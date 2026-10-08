"""Preprocessing rings (Experiment B) — the text primitives the retrieval arms read.

Experiment B asks a narrow, empirical question: **does more sophisticated deterministic text
preprocessing buy better candidate retrieval?** To answer it without touching the architecture, the
text primitives are factored out of the arms and into a *ring*: the arm logic (which locality, which
landmark, which address-book record) is unchanged, and only the text handling differs.

    B1  raw text          — the naive floor: lowercase alphanumeric tokens, a 6-digit pin regex, the
                            same relation vocabulary. No NFKC, no abbreviation table, no spans.
    B2  normalised+spans  — **production**. `sutra/dataio.norm_text` (NFKC + the corpus abbreviation
                            table + a Latin/Devanagari/Kannada-preserving strip), `text_norm`, the
                            deterministic spans produced by the cleaning stage, the relation windows.
    B3  + TF-IDF/SVD      — B2, plus a residue matcher: where B2 finds no locality (or no landmark),
                            score the in-town gazetteer by cosine in a character-ngram TF-IDF space
                            and in its truncated-SVD projection. Official corpus only, no labels.
    B4  + parser/statistics on the residue — B3, plus deterministic parser features: IDF-weighted
                            token evidence, edit-tolerant token matching, and **numeric-slot
                            consistency** against the candidate locality's own member addresses.

Rules honoured here (contract §4/§13, experiment plan §1):

* **No label is read.** Everything is computed from the official corpus: address texts, locality
  names, landmark names. No surveyed truth, no visit, no outcome, no account/agent attribute.
* **No external data, no network, no LLM, no embedding API.** B3/B4 are linear algebra over strings
  that are already in `data/cleaned/`.
* **Deterministic.** Fixed vocabulary, fixed IDF, fixed SVD sign convention, integer-quantised
  projections, no random sampling anywhere (see `facts()` for what each ring records).
* **B2 is production and must stay bit-identical** — `RingB2` calls exactly the functions the arms
  called before; `tools/experiment_b.py` proves it by rebuilding the candidate artefact and diffing.
"""
from __future__ import annotations

import math
import re
import time

from . import config, dataio

RING_IDS = ("B1", "B2", "B3", "B4")

# ── B3/B4 constants — fixed BEFORE the run, and never tuned on any population ────────────────────
SVD_DIM = 16                     # low-rank dimension of the character-ngram projection
SVD_TOP_TERMS = 1200             # densest terms kept for the SVD (determinism + cost)
NGRAM_N = 4                      # character n-gram size for the TF-IDF space
B3_MIN_SCORE = 0.35              # residue acceptance: best score
B3_MIN_MARGIN = 1.25             # ... and its ratio over the runner-up
B4_MIN_SCORE = 0.30              # B4 accepts slightly looser text evidence
B4_MIN_MARGIN = 1.15             # ... because the slot constraint is an independent requirement

# generic address words: they may never be the only reason a locality matches
GENERIC = {"nagar", "nagara", "layout", "layt", "colony", "badavane", "extension", "extn", "block",
           "sector", "stage", "phase", "road", "street", "cross", "main", "lane", "gali", "east",
           "west", "north", "south", "new", "old", "town", "village"}
# The relation vocabulary belongs to the ARM and is frozen (`config.RELATION_WORDS`): every ring uses
# exactly it. A ring may change how the text is read, never what counts as a relation phrase — an
# earlier draft of B1 quietly added "pass"/"nr"/"hattira" and would have flattered the naive ring.
RELATION_WORDS = config.RELATION_WORDS
NUM_SLOT = re.compile(r"\b(\d{1,4})\s*(?:st|nd|rd|th)?\s*(cross|main|block|gali|lane|ward|sector)\b", re.I)
HOUSE_SLOT = re.compile(r"\b(?:no\.?|number|h\.?\s?no\.?|house|plot|door|d\.?no|flat)\s*\.?\s*(\d{1,4})", re.I)


def _l2(vec: dict) -> float:
    return math.sqrt(sum(v * v for v in vec.values())) or 1.0


def _cos(a: dict, b: dict) -> float:
    if not a or not b:
        return 0.0
    small, large = (a, b) if len(a) <= len(b) else (b, a)
    dot = sum(v * large.get(k, 0.0) for k, v in small.items())
    return dot / (_l2(a) * _l2(b))


def _ngrams(s: str, n: int = NGRAM_N) -> list[str]:
    s = "^" + s.replace(" ", "_") + "$"
    return [s[i:i + n] for i in range(max(0, len(s) - n + 1))]


# ══ the ring interface ═══════════════════════════════════════════════════════════════════════════
class Ring:
    """Text primitives + a residue matcher. Subclasses override; the arms never branch on ring id."""

    ring_id = "?"
    description = ""
    uses = ()

    # ── primitives ──────────────────────────────────────────────────────────────────────────────
    def normalise(self, text: str) -> str:
        raise NotImplementedError

    def tokens(self, text: str) -> list[str]:
        return dataio.tokens(self.normalise(text))

    def pin(self, text: str) -> str | None:
        return dataio.pin_in_text(text)

    def relation_windows(self, text: str):
        return dataio.relation_windows(text)

    def match_text(self, addr: dict) -> str:
        """The text the normaliser treats as the address (what the arms read)."""
        return addr.get("address_text") or ""

    def locality_text(self, addr: dict) -> str:
        """The canonical text the locality arm tokenises."""
        return self.normalise(addr.get("address_text", ""))

    def address_book_key(self, addr: dict) -> str:
        return addr.get("text_norm") or self.normalise(addr.get("address_text", ""))

    def address_book_index(self, ix) -> dict:
        """The ring's own key space for the address-book arm (B2 reads the production `text_index`).

        Built once per ring and cached: rebuilding a 3,117-row key space on every request would be an
        implementation defect masquerading as a cost of the approach (it was one, until it was found
        while profiling — see the Experiment B report).
        """
        cached = getattr(self, "_book_cache", None)
        if cached is not None:
            return cached
        book: dict[tuple[str, str], list[str]] = {}
        for aid in sorted(ix.addresses):
            row = ix.addresses[aid]
            book.setdefault((row["town_id"], self.address_book_key(row)), []).append(aid)
        self._book_cache = {k: sorted(v) for k, v in book.items()}
        return self._book_cache

    # ── index-time work (B3/B4) ─────────────────────────────────────────────────────────────────
    def build(self, ix) -> dict:
        return {}

    # ── residue proposals ───────────────────────────────────────────────────────────────────────
    def locality_residue(self, addr: dict, localities: list[dict], ix) -> list[dict]:
        return []

    def landmark_residue(self, addr: dict, landmarks: list[dict], ix) -> list[dict]:
        return []

    def facts(self) -> dict:
        return {"ring_id": self.ring_id, "description": self.description, "uses": list(self.uses)}


# ══ B1 — raw text ════════════════════════════════════════════════════════════════════════════════
_RAW_TOKEN = re.compile(r"[0-9a-z\u0c80-\u0cff]+")
_RAW_PIN = re.compile(r"\b(\d{6})\b")


class RingB1(Ring):
    ring_id = "B1"
    description = ("raw address text: lowercase alphanumeric tokens, 6-digit pin regex, the arm's "
                   "relation vocabulary — no NFKC, no abbreviation table, no cleaning spans")
    uses = ("raw_text",)

    def normalise(self, text: str) -> str:
        return (text or "").lower()

    def tokens(self, text: str) -> list[str]:
        return _RAW_TOKEN.findall(self.normalise(text))

    def pin(self, text: str) -> str | None:
        m = _RAW_PIN.search(text or "")
        return m.group(1) if m else None

    def relation_windows(self, text: str):
        """Same relation vocabulary as production (it belongs to the arm, not to the normaliser),
        applied to the raw text without normalisation."""
        t = self.normalise(text)                    # B1's only transform: lower-casing
        for rel in RELATION_WORDS:
            i = t.find(rel)
            if i >= 0:
                before = _RAW_TOKEN.findall(t[:i])[-3:]
                after = _RAW_TOKEN.findall(t[i + len(rel):])[:3]
                return rel, before, after
        return None, [], []

    def match_text(self, addr: dict) -> str:
        return addr.get("address_text_raw") or addr.get("address_text") or ""

    def locality_text(self, addr: dict) -> str:
        return self.normalise(addr.get("address_text") or "")

    def address_book_key(self, addr: dict) -> str:
        return self.normalise(addr.get("address_text_raw") or addr.get("address_text") or "")


# ══ B2 — production (normalised text + spans) ════════════════════════════════════════════════════
class RingB2(Ring):
    ring_id = "B2"
    description = ("production: NFKC + the corpus abbreviation table + script-preserving strip, the "
                   "cleaned `text_norm`, the deterministic span flags, relation windows")
    uses = ("normalisation", "abbreviations", "spans")

    def normalise(self, text: str) -> str:
        return dataio.norm_text(text)

    def match_text(self, addr: dict) -> str:
        return addr.get("address_text_raw") or addr.get("address_text") or ""

    def locality_text(self, addr: dict) -> str:
        return addr.get("text_norm") or dataio.norm_text(addr.get("address_text", ""))

    def spans(self, addr: dict) -> dict:
        """The deterministic spans the cleaning stage produced (lane/block/cross/house/relation/
        locality-token) — available to B2's arms and features exactly as they are in production."""
        return {k: addr.get(k) for k in ("span_lane", "span_block", "span_cross", "span_house",
                                         "span_relation", "span_locality_token")}


# ══ the shared text model for B3/B4 ══════════════════════════════════════════════════════════════
class _TextModel:
    """Character-ngram TF-IDF + its truncated-SVD projection, built from the official corpus only.

    Documents = every official address text + every locality name + every landmark name (3,393
    strings). Terms = padded character n-grams. The projection is the top `SVD_DIM` right singular
    vectors of the (restricted, densest-terms) document matrix, sign-canonicalised so that the
    largest-magnitude loading of each component is positive, and quantised to 6 decimals so the
    artefact is stable to hash. No label, no visit, no external text is involved.
    """

    def __init__(self, docs: list[str]):
        import numpy as np
        self.np = np
        self.docs = docs
        df: dict[str, int] = {}
        for d in docs:
            for g in set(_ngrams(d)):
                df[g] = df.get(g, 0) + 1
        n = len(docs)
        self.idf = {g: math.log((1 + n) / (1 + c)) + 1.0 for g, c in df.items()}
        # a term no corpus document contains gets the unseen-term IDF (smoothed upper bound)
        self.idf_unseen = math.log(1 + n) + 1.0
        t0 = time.time()
        top = sorted(df.items(), key=lambda kv: (-kv[1], kv[0]))[:SVD_TOP_TERMS]
        vocab = sorted(g for g, _ in top)
        self.top_terms = vocab
        index = {g: i for i, g in enumerate(vocab)}
        M = np.zeros((n, len(vocab)), dtype=np.float64)
        for r, d in enumerate(docs):
            tf: dict[str, int] = {}
            for g in _ngrams(d):
                if g in index:
                    tf[g] = tf.get(g, 0) + 1
            for g, c in tf.items():
                M[r, index[g]] = (1.0 + math.log(c)) * self.idf[g]
        norms = np.linalg.norm(M, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        M = M / norms
        U, S, Vt = np.linalg.svd(M, full_matrices=False)
        k = min(SVD_DIM, Vt.shape[0])
        V = Vt[:k].T.copy()
        for j in range(V.shape[1]):                     # sign convention: largest |loading| positive
            col = V[:, j]
            if col[np.argmax(np.abs(col))] < 0:
                V[:, j] = -col
        self.V = np.round(V, 6)
        self.singular = np.round(S[:k], 6)
        self.docs_meta = {"n_docs": n, "vocab_full": len(df), "vocab_used": len(vocab), "svd_dim": int(k),
                          "build_s": round(time.time() - t0, 3)}

    def vec(self, s: str) -> dict:
        tf: dict[str, int] = {}
        for g in _ngrams(s):
            tf[g] = tf.get(g, 0) + 1
        return {g: (1.0 + math.log(c)) * self.idf.get(g, self.idf_unseen) for g, c in tf.items()}

    def vec_restricted(self, s: str):
        np = self.np
        v = np.zeros(len(self.top_terms), dtype=np.float64)
        idx = {g: i for i, g in enumerate(self.top_terms)}
        tf: dict[str, int] = {}
        for g in _ngrams(s):
            if g in idx:
                tf[g] = tf.get(g, 0) + 1
        for g, c in tf.items():
            v[idx[g]] = (1.0 + math.log(c)) * self.idf.get(g, self.idf_unseen)
        nrm = np.linalg.norm(v)
        return v / nrm if nrm else v

    def sim(self, a: str, b: str) -> dict:
        """(TF-IDF cosine, SVD cosine) for two strings — the two channels B3 reports separately."""
        va, vb = self.vec(a), self.vec(b)
        tfidf = _cos(va, vb)
        ra, rb = self.vec_restricted(a), self.vec_restricted(b)
        denom = (self.np.linalg.norm(ra) * self.np.linalg.norm(rb)) or 1.0
        svd = float(ra @ self.V @ self.V.T @ rb / denom) if denom else 0.0
        return {"tfidf": round(float(tfidf), 4), "svd": round(float(svd), 4),
                "score": round(0.5 * float(tfidf) + 0.5 * float(svd), 4)}


# ══ B3 — B2 + TF-IDF/SVD residue matcher ═════════════════════════════════════════════════════════
class RingB3(RingB2):
    ring_id = "B3"
    description = ("B2 + a residue matcher: where B2 finds no locality or landmark, score the in-town "
                   "gazetteer by character-ngram TF-IDF cosine and by its truncated-SVD projection")
    uses = ("normalisation", "abbreviations", "spans", "tfidf", "svd")

    def __init__(self, ix=None):
        self.model: _TextModel | None = None
        self.stats: dict = {}
        self._simcache: dict[tuple[str, str], dict] = {}
        # why the residue did or did not produce a candidate — counted, never guessed
        self.residue_stats: dict[str, int] = {"locality_calls": 0, "locality_accepted": 0,
                                              "locality_rejected_threshold": 0,
                                              "locality_rejected_margin": 0,
                                              "landmark_calls": 0, "landmark_accepted": 0,
                                              "landmark_rejected_threshold": 0,
                                              "landmark_rejected_margin": 0,
                                              "landmark_no_relation": 0}

    def build(self, ix) -> dict:
        docs = []
        for aid in sorted(ix.addresses):
            a = ix.addresses[aid]
            docs.append(a.get("text_norm") or self.normalise(a.get("address_text", "")))
        docs += [self.normalise(L["locality_name"]) for L in ix.localities]
        docs += [self.normalise(p["name"]) for p in ix.landmarks]
        self.model = _TextModel(docs)
        self.stats = dict(self.model.docs_meta)
        return self.facts()

    # ── residue: names that B2's token/pin rules could not see ──────────────────────────────────
    def _distinctive(self, name: str) -> list[str]:
        return [t for t in self.tokens(name) if t not in GENERIC]

    def _score_names(self, query: str, names: list[tuple[str, str]]) -> list[dict]:
        """query vs [(id, name)] → scored, sorted proposals (deterministic: score, then id)."""
        if self.model is None:
            return []
        out = []
        for ident, name in names:
            dist = self._distinctive(name)
            if not dist:
                continue
            qt = set(self.tokens(query))
            if not qt:
                continue
            per_token = []
            for t in dist:
                best = 0.0
                for q in sorted(qt):
                    key = (t, q)
                    s = self._simcache.get(key)
                    if s is None:
                        s = self.model.sim(t, q)["score"]
                        self._simcache[key] = s
                    best = max(best, s)
                per_token.append(best)
            score = round(sum(per_token) / len(per_token), 4)
            if score > 0:
                out.append({"id": ident, "name": name, "score": score,
                            "per_token": [round(p, 4) for p in per_token],
                            "matched_tokens": dist})
        out.sort(key=lambda d: (-d["score"], d["id"]))
        return out

    def locality_residue(self, addr: dict, localities: list[dict], ix) -> list[dict]:
        self.residue_stats["locality_calls"] += 1
        query = addr.get("text_norm") or self.normalise(addr.get("address_text", ""))
        cands = [(L["locality_id"], L["locality_name"]) for L in localities
                 if L["town_id"] == addr["town_id"]]
        scored = self._score_names(query, cands)
        if not scored:
            self.residue_stats["locality_rejected_threshold"] += 1
            return []
        best, second = scored[0], (scored[1] if len(scored) > 1 else None)
        if best["score"] < B3_MIN_SCORE:
            self.residue_stats["locality_rejected_threshold"] += 1
            return []
        if second and best["score"] < B3_MIN_MARGIN * second["score"]:
            self.residue_stats["locality_rejected_margin"] += 1
            return []
        self.residue_stats["locality_accepted"] += 1
        return [{"locality_id": best["id"], "how": "residue_tfidf_svd", "score": best["score"],
                 "margin_over_second": round(best["score"] / second["score"], 3) if second else None,
                 "detail": {"per_token": best["per_token"], "name": best["name"],
                            "threshold": B3_MIN_SCORE, "min_margin": B3_MIN_MARGIN}}]

    def landmark_residue(self, addr: dict, landmarks: list[dict], ix) -> list[dict]:
        text = self.match_text(addr)
        rel, before, after = self.relation_windows(text)
        if rel is None or not (before or after):
            self.residue_stats["landmark_no_relation"] += 1
            return []                                   # the arm's own precondition still holds
        self.residue_stats["landmark_calls"] += 1
        query = " ".join(list(before) + list(after))
        scored = self._score_names(query, [(p["poi_id"], p["name"]) for p in landmarks
                                           if p["town_id"] == addr["town_id"]])
        if not scored or scored[0]["score"] < B3_MIN_SCORE:
            self.residue_stats["landmark_rejected_threshold"] += 1
            return []
        top = scored[0]
        second = scored[1] if len(scored) > 1 else None
        if second and top["score"] < B3_MIN_MARGIN * second["score"]:
            self.residue_stats["landmark_rejected_margin"] += 1
            return []
        self.residue_stats["landmark_accepted"] += 1
        return [{"poi_id": top["id"], "score": top["score"], "parsed_relation": rel,
                 "window_before": list(before), "window_after": list(after), "ambiguous": False,
                 "detail": {"per_token": top["per_token"], "name": top["name"],
                            "threshold": B3_MIN_SCORE}}]

    def facts(self) -> dict:
        f = super().facts()
        f.update({"threshold": B3_MIN_SCORE, "min_margin": B3_MIN_MARGIN, "ngram_n": NGRAM_N,
                  "text_model": self.stats, "residue_stats": dict(self.residue_stats)})
        return f


# ══ B4 — B3 + parser/statistical evidence on the residue ════════════════════════════════════════
class RingB4(RingB3):
    ring_id = "B4"
    description = ("B3 + deterministic parser/statistical features on the residue: IDF-weighted "
                   "edit-tolerant token evidence and numeric-slot consistency against the candidate "
                   "locality's own member addresses")
    uses = ("normalisation", "abbreviations", "spans", "tfidf", "svd", "parser_slots",
            "idf_weighted_tokens", "slot_consistency")

    def __init__(self, ix=None):
        super().__init__(ix)
        self.loc_members: dict[str, list[str]] = {}
        self.loc_slots: dict[str, set] = {}
        self._localities: list[dict] = []

    def build(self, ix) -> dict:
        super().build(ix)
        self._localities = ix.localities
        for aid in sorted(ix.addresses):
            a = ix.addresses[aid]
            L = self._locality_of_text(a)
            if L is None:
                continue
            text = a.get("text_norm") or self.normalise(a.get("address_text", ""))
            self.loc_members.setdefault(L, []).append(aid)
            self.loc_slots.setdefault(L, set()).update(self._slots(text))
        self.stats = dict(self.stats, n_localities_with_slots=len(self.loc_slots),
                          median_member_slots=int(sorted(len(v) for v in self.loc_slots.values())[
                              len(self.loc_slots) // 2]) if self.loc_slots else 0)
        return self.facts()

    # a locality's own member texts are official data; they are used as a *parser statistic*
    # (which numeric slots co-occur with this name), never as a label
    def _locality_of_text(self, addr: dict) -> str | None:
        text = addr.get("text_norm") or self.normalise(addr.get("address_text", ""))
        toks = set(self.tokens(text))
        hits = [L["locality_id"] for L in self._localities
                if L["town_id"] == addr["town_id"]
                and set(self.tokens(self.normalise(L["locality_name"]))) & toks]
        return sorted(hits)[0] if hits else None

    @staticmethod
    def _slots(text: str) -> list[str]:
        out = [f"{m.group(2).lower()}{m.group(1)}" for m in NUM_SLOT.finditer(text or "")]
        out += [f"house{m.group(1)}" for m in HOUSE_SLOT.finditer(text or "")]
        return out

    def _idf_weighted(self, query: str, name: str) -> float:
        """IDF-weighted, edit-tolerant token evidence: every distinctive name token must be loosely
        present in the query (edit ratio or character-ngram cosine), weighted by how rare it is."""
        dist = self._distinctive(name)
        qt = self.tokens(query)
        if not dist or not qt:
            return 0.0
        num = den = 0.0
        for t in dist:
            w = self.model.idf.get(t, 1.0) if self.model else 1.0
            best = 0.0
            for q in qt:
                ngram = _cos({g: 1.0 for g in _ngrams(t)}, {g: 1.0 for g in _ngrams(q)})
                edit = dataio.edit_ratio(t, q)
                best = max(best, ngram, edit)
            num += w * best
            den += w
        return round(num / den, 4) if den else 0.0

    def locality_residue(self, addr: dict, localities: list[dict], ix) -> list[dict]:
        self.residue_stats["locality_calls"] += 1
        query = addr.get("text_norm") or self.normalise(addr.get("address_text", ""))
        text_score = {d["id"]: d for d in super()._score_names(
            query, [(L["locality_id"], L["locality_name"]) for L in localities
                    if L["town_id"] == addr["town_id"]])}
        qslots = set(self._slots(query))
        scored = []
        for lid, name in [(L["locality_id"], L["locality_name"]) for L in localities
                          if L["town_id"] == addr["town_id"]]:
            if not self._distinctive(name):
                continue
            s_text = text_score.get(lid, {}).get("score", 0.0)
            s_idf = self._idf_weighted(query, name)
            member_slots = self.loc_slots.get(lid, set())
            slot_hit = 1.0 if (qslots and qslots & member_slots) else 0.0
            # the parser channel is an independent requirement, not a tie-breaker: a residue match
            # with no slot evidence needs stronger text evidence to be accepted
            combined = round(0.5 * max(s_text, s_idf) + 0.5 * (0.5 * s_idf + 0.5 * slot_hit), 4)
            if qslots and not slot_hit:
                combined = round(combined * 0.5, 4)
            scored.append({"locality_id": lid, "name": name, "score": combined, "text_score": s_text,
                           "idf_score": s_idf, "slot_hit": slot_hit,
                           "query_slots": sorted(qslots), "member_slots_sample": sorted(member_slots)[:8]})
        scored.sort(key=lambda d: (-d["score"], d["locality_id"]))
        if not scored or scored[0]["score"] < B4_MIN_SCORE:
            self.residue_stats["locality_rejected_threshold"] += 1
            return []
        best = scored[0]
        second = scored[1] if len(scored) > 1 else None
        if second and best["score"] < B4_MIN_MARGIN * second["score"]:
            self.residue_stats["locality_rejected_margin"] += 1
            return []
        if qslots and not best["slot_hit"] and not second:
            self.residue_stats["locality_rejected_margin"] += 1
            return []                                   # nothing to disambiguate against: stay silent
        self.residue_stats["locality_accepted"] += 1
        return [{**best, "how": "residue_parser_tfidf_svd",
                 "detail": {"threshold": B4_MIN_SCORE, "min_margin": B4_MIN_MARGIN}}]

    def landmark_residue(self, addr: dict, landmarks: list[dict], ix) -> list[dict]:
        text = self.match_text(addr)
        rel, before, after = self.relation_windows(text)
        if rel is None or not (before or after):
            self.residue_stats["landmark_no_relation"] += 1
            return []
        self.residue_stats["landmark_calls"] += 1
        query = " ".join(list(before) + list(after))
        scored = []
        for p in landmarks:
            if p["town_id"] != addr["town_id"]:
                continue
            if not self._distinctive(p["name"]):
                continue
            s_tf = 0.0
            if self.model is not None:
                s_tf = max((self.model.sim(t, q)["score"] for t in self._distinctive(p["name"])
                            for q in self.tokens(query)), default=0.0)
            s_idf = self._idf_weighted(query, p["name"])
            combined = round(0.5 * max(s_tf, s_idf) + 0.5 * s_idf, 4)
            scored.append({"poi_id": p["poi_id"], "score": combined, "text_score": round(s_tf, 4),
                           "idf_score": s_idf, "name": p["name"]})
        scored.sort(key=lambda d: (-d["score"], d["poi_id"]))
        if not scored or scored[0]["score"] < B4_MIN_SCORE:
            self.residue_stats["landmark_rejected_threshold"] += 1
            return []
        best = scored[0]
        second = scored[1] if len(scored) > 1 else None
        if second and best["score"] < B4_MIN_MARGIN * second["score"]:
            self.residue_stats["landmark_rejected_margin"] += 1
            return []
        self.residue_stats["landmark_accepted"] += 1
        return [{"poi_id": best["poi_id"], "score": best["score"], "parsed_relation": rel,
                 "window_before": list(before), "window_after": list(after), "ambiguous": False,
                 "detail": {"threshold": B4_MIN_SCORE, "name": best["name"],
                            "idf_score": best["idf_score"]}}]

    def facts(self) -> dict:
        f = super().facts()
        f.update({"threshold": B4_MIN_SCORE, "min_margin": B4_MIN_MARGIN,
                  "locality_slot_profiles": len(self.loc_slots),
                  "residue_stats": dict(self.residue_stats)})
        return f


def build_all(ix) -> dict[str, Ring]:
    """Instantiate and build every ring. B1/B2 are stateless; B3/B4 build their text model here."""
    rings: dict[str, Ring] = {"B1": RingB1(), "B2": RingB2(), "B3": RingB3(), "B4": RingB4()}
    for r in rings.values():
        if r.ring_id in ("B3", "B4"):
            r.build(ix)
    return rings


def get(ring_id: str, ix=None) -> Ring:
    """One ring by id; `B2` is production and is always available."""
    if ring_id == "B2":
        return RingB2()
    if ring_id == "B1":
        return RingB1()
    if ix is None:
        from .indexes import get_index
        ix = get_index()
    return build_all(ix)[ring_id]
