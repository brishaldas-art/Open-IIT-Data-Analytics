"""Candidate generation — the contract's arm set, and nothing else (P2, contract §4).

Eight arms, all `licence_class = "official"`, no truth column anywhere, no vendor call anywhere:

    frozen_baseline    the supplied `baseline_geocodes.csv` — THE frozen arm (D44)
    locality_centroid  official locality centroid, matched by name span or in-text pincode
    town_centroid      mean of the town's locality centroids (last-resort coarse anchor)
    official_landmark  official POI named by a relation phrase in the address text
    address_book       the same normalised address text, already known elsewhere in the town
    field_evidence     check-in positions from the append-only store (as-of filtered)
    memory             this address's own prior belief (as-of filtered)
    place_neighbour    experiment-gated (C2) — DISABLED, emits nothing until C2 admits it

`as_of_valid` is present **iff** the arm is evidence-backed: a candidate enters the answer only after
the evidence that justifies it existed (`asof.candidates_upto`).
"""
from __future__ import annotations

import hashlib

from . import asof, config, dataio, geo
from .preprocess import get as get_ring          # text primitives live in the ring (Experiment B)
from .version import RULE_VERSION

RING_B2 = "B2"        # production ring: normalised text + spans (see sutra/preprocess.py)

ARM_GRANULARITY = {
    "frozen_baseline": None,       # taken from the arm's own `precision`
    "locality_centroid": "locality",
    "town_centroid": "town",
    "official_landmark": "locality",   # a landmark anchors a neighbourhood, not a doorway
    "address_book": None,              # inherits the matched record's own arm
    "field_evidence": "street",
    "memory": None,
    "place_neighbour": "rooftop",
}
PRECISION_TO_GRANULARITY = {"rooftop": "rooftop", "street": "street", "locality": "locality",
                            "pincode": "locality", "town": "town"}


def make_candidate(address_id: str, arm: str, source_ref: str, x, y, granularity: str,
                   provenance: dict, valid_from=None, arm_rank: int = 1) -> dict:
    """A contract §4 candidate record.

    `as_of_valid` is present **iff** the arm is evidence-backed, and it is the instant of the evidence
    that justifies the candidate (never the query instant). `built_at` is the arm's own instant too:
    the canonical artefact instant for static arms, the contributing observation for evidence arms. The
    record is therefore stable across queries — the coordinate cannot move because someone asked later.
    """
    cid = "c-" + hashlib.sha1(f"{arm}|{address_id}|{source_ref}".encode("utf-8")).hexdigest()[:12]
    evidence_backed = arm in config.EVIDENCE_ARMS
    stamp = asof.to_utc_str(valid_from) if valid_from else config.MOMENT
    return {
        "candidate_id": cid, "address_id": address_id, "arm": arm, "source_ref": source_ref,
        "x": round(float(x), 3), "y": round(float(y), 3), "granularity": granularity,
        "arm_rank": int(arm_rank), "licence_class": config.LICENCE_CLASS,
        "as_of_valid": stamp if evidence_backed else None,
        "provenance": {"rule_version": RULE_VERSION, "built_at": stamp, **provenance},
    }


# ── static arms ─────────────────────────────────────────────────────────────────────────────────
def _frozen_baseline(address_id: str, banch: dict, as_of) -> list[dict]:
    b = banch.get(address_id)
    if not b:
        return []
    precision = (b.get("precision") or "").strip() or "locality"
    gran = PRECISION_TO_GRANULARITY.get(precision, "locality")
    return [make_candidate(address_id, "frozen_baseline", f"baseline:{precision}", b["geocoder_x"],
                           b["geocoder_y"], gran, {"built_from": "baseline_geocodes.csv",
                                                   "stratum": precision,
                                                   "baseline_precision": precision}, None)]


def _locality_centroid(addr: dict, locs: list[dict], as_of, ring=None, ix=None) -> list[dict]:
    """Which locality the address text names. The *rule* is the arm's; the *text handling* is the
    ring's (Experiment B): identical for `B2`, blind to every locality the ring cannot read."""

    def emit(locality_id: str, why: str, extra: dict | None = None) -> list[dict]:
        L = next(x for x in locs if x["locality_id"] == locality_id)
        prov = {"built_from": "localities.csv", "match": why, "stratum": "locality",
                "retrieval_version": getattr(config, "RETRIEVAL_VERSION", "v1")}
        if extra:
            prov.update(extra)
        return [make_candidate(addr["address_id"], "locality_centroid", f"locality:{L['locality_id']}",
                               L["centroid_x"], L["centroid_y"], "locality", prov, None)]

    ring = ring or get_ring(RING_B2)
    town = addr["town_id"]
    toks = set(ring.tokens(ring.locality_text(addr)))
    pin = ring.pin(addr.get("address_text", ""))
    version = getattr(config, "RETRIEVAL_VERSION", "v1")
    best = None
    idf = getattr(ix, "idf", None) if ix is not None else None
    for L in locs:
        if L["town_id"] != town:
            continue
        ntoks = set(ring.tokens(ring.normalise(L["locality_name"])))
        pin_hit = pin is not None and L.get("pincode") == pin
        if version == "v2":
            # every distinctive token of the name must be present, and the rarest token always: a bare
            # "nagar"/"colony" match is not evidence that *this* locality is named.
            if not ntoks:
                continue
            present = ntoks & toks
            coverage = len(present) / len(ntoks)
            rarest = min(ntoks, key=lambda t: ((idf and ix.token_rarity(t)) or 0, t))
            if coverage < config.LOCALITY_MIN_COVERAGE or rarest not in toks or not present:
                continue
            weight = round(sum((idf(t) if idf else 1.0) for t in present), 6)
            key = (-round(coverage, 6), -weight, -len(ntoks), L["locality_id"])
            cand = (key, L, "idf_token_match", {"coverage": round(coverage, 4),
                                                "idf_sum": weight, "matched_tokens": sorted(present)})
        else:
            hit = bool(ntoks & toks) and len(ntoks) > 0
            if not (hit or pin_hit):
                continue
            score = (2 if hit else 0) + (1 if pin_hit else 0)
            key = (-score, L["locality_id"])
            cand = (key, L, "locality_name_match" if hit else "pincode_match", None)
        if best is None or cand[0] < best[0]:
            best = cand
    if best:
        _, L, why, extra = best
        return emit(L["locality_id"], why, extra)
    if version == "v2":
        # no name match at all: the pincode is the only postal signal left, and it maps to *several*
        # localities — emit them all (deterministic order) instead of silently picking the first.
        if pin is not None:
            hits = [L for L in locs if L["town_id"] == town and L.get("pincode") == pin]
            if hits:
                return [c for L in sorted(hits, key=lambda L: L["locality_id"])
                        for c in emit(L["locality_id"], "pincode_match", {"ambiguous_pincode": True})]
    # the residue: no name token and no pin could be read. A ring with a residue matcher (B3/B4) may
    # still propose a locality — the arm is the same arm, only the text evidence is richer.
    for r in ring.locality_residue(addr, locs, ix):
        return emit(r["locality_id"], r["how"], {"residue": {k: v for k, v in r.items()
                                                             if k not in ("locality_id", "how")}})
    return []


def town_centroids(locs: list[dict] | None = None) -> dict[str, tuple[float, float]]:
    """Mean of the town's official locality centroids (deterministic, official-only)."""
    locs = locs or dataio.localities()
    acc: dict[str, list[tuple[float, float]]] = {}
    for L in locs:
        acc.setdefault(L["town_id"], []).append((float(L["centroid_x"]), float(L["centroid_y"])))
    return {t: (sum(x for x, _ in v) / len(v), sum(y for _, y in v) / len(v)) for t, v in acc.items()}


def _town_centroid(addr: dict, cents: dict, as_of) -> list[dict]:
    c = cents.get(addr["town_id"])
    if not c:
        return []
    return [make_candidate(addr["address_id"], "town_centroid", f"town:{addr['town_id']}", c[0], c[1],
                           "town", {"built_from": "localities.csv (town mean)", "stratum": "town"}, None)]


def _official_landmark(addr: dict, lms: list[dict], as_of, ring=None, ix=None) -> list[dict]:
    """The landmark named by the address text, town-scoped, scored on the landmark's own name tokens."""
    ring = ring or get_ring(RING_B2)
    text = ring.match_text(addr)
    rel, before, after = ring.relation_windows(text)
    if rel is None or not (before or after):
        return []
    scored = []
    for L in lms:
        if L["town_id"] != addr["town_id"]:
            continue
        name_toks = set(ring.tokens(ring.normalise(L["name"])))
        score = 2 * len(name_toks & set(after)) + len(name_toks & set(before))
        if score > 0:
            scored.append((score, L))
    if not scored:
        return _landmark_candidates_from_residue(addr, ring, ix, rel, before, after)
    return _landmark_candidates_from_scores(addr, scored, rel, before, after)


def _landmark_candidates_from_residue(addr, ring, ix, rel, before, after) -> list[dict]:
    """A residue landmark: the ring recognised the name even though no token matched exactly."""
    out = []
    for i, r in enumerate(ring.landmark_residue(addr, ix.landmarks if ix else [], ix)[:2], start=1):
        L = ix.poi(r["poi_id"]) if ix else None
        if L is None:
            continue
        out.append(make_candidate(addr["address_id"], "official_landmark", f"landmark:{L['poi_id']}",
                                  L["x"], L["y"], "locality",
                                  {"built_from": "landmarks_poi.csv", "parsed_relation": rel,
                                   "parsed_window_after": list(after), "parsed_window_before": list(before),
                                   "name_token_overlap": 0, "landmark_type": L["landmark_type"],
                                   "ambiguous": bool(r.get("ambiguous", False)), "stratum": "locality",
                                   "residue_match": r["how"],
                                   "residue_score": r.get("score"),
                                   "residue_detail": r.get("detail")}, None, i))
    return out


def _landmark_candidates_from_scores(addr, scored, rel, before, after) -> list[dict]:
    best = max(s for s, _ in scored)
    hits = sorted((L for s, L in scored if s == best), key=lambda L: L["poi_id"])
    out = []
    for i, L in enumerate(hits[:2], start=1):
        out.append(make_candidate(addr["address_id"], "official_landmark", f"landmark:{L['poi_id']}",
                                  L["x"], L["y"], "locality",
                                  {"built_from": "landmarks_poi.csv", "parsed_relation": rel,
                                   "parsed_window_after": after, "parsed_window_before": before,
                                   "name_token_overlap": best, "landmark_type": L["landmark_type"],
                                   "ambiguous": len(hits) > 1, "stratum": "locality"}, None, i))
    return out


def _address_book(addr: dict, index: dict, banch: dict, as_of, ring=None) -> list[dict]:
    """Same normalised text, another record, same town — the address book as a data asset.

    The key space is the ring's: `B2` reads the production `text_index` directly (no rebuild), every
    other ring compares records under its own normalisation.
    """
    ring = ring or get_ring(RING_B2)
    book_key = ring.address_book_key(addr)
    others = [a for a in index.get((addr["town_id"], book_key), []) if a != addr["address_id"]]
    if not others or not book_key:
        return []
    for other in sorted(others):
        b = banch.get(other)
        if not b:
            continue
        precision = (b.get("precision") or "").strip() or "locality"
        return [make_candidate(addr["address_id"], "address_book", f"address:{other}", b["geocoder_x"],
                               b["geocoder_y"], PRECISION_TO_GRANULARITY.get(precision, "locality"),
                               {"built_from": "addresses.csv (identical text_norm)",
                                "matched_address_id": other, "stratum": precision}, None)]
    return []


# ── evidence-backed arms (as-of filtered, never from "latest visit") ────────────────────────────
def field_evidence_candidates(address_id: str, as_of, store) -> list[dict]:
    """Check-in positions that passed the evidence policy, as known at `as_of`.

    A consolidated candidate is emitted when >= 2 independent positives agree within the consistency
    band: its position is the **median** of the agreeing check-ins (order-independent, deterministic).
    Medians of agreeing, independently-collected check-ins are a defined aggregation — never an
    average of arbitrary coordinates (M3).
    """
    obs = asof.observations_upto(store, as_of, address_id=address_id)
    if not obs:
        return []
    ev = store.evidence_for([o["observation_id"] for o in obs])
    rows = []
    for o in obs:
        e = ev.get(o["observation_id"])
        if not e or e["polarity"] != "positive" or float(e["weight"]) < config.W_MIN or o.get("x") is None:
            continue
        rows.append({"obs": o, "w": float(e["weight"]), "ind": e["independence"]})
    if not rows:
        return []
    # ── policy: how a single check-in enters the candidate set ───────────────────────────────────
    # Its *granularity* is the precision that check-in actually claims, so a well-measured visit
    # outranks a poorly-measured one instead of losing a candidate_id tie-break. Both knobs default
    # to the shipped behaviour (all singles equal at "street"), so P0 is byte-identical.
    kept = []
    for r in rows:
        o = r["obs"]
        if config.SINGLE_GATE_MIN_WEIGHT is not None and r["w"] < config.SINGLE_GATE_MIN_WEIGHT:
            continue
        acc = o.get("gps_accuracy_m")
        if config.SINGLE_GATE_GPS_M is not None and acc is not None and float(acc) > config.SINGLE_GATE_GPS_M:
            continue
        kept.append((r, o, acc))
    singles = kept
    if config.SINGLE_QUALITY_TIERING:
        # deterministic order: confident+well-measured first, then by id — never by chance
        singles = sorted(kept, key=lambda t: (0 if t[0]["w"] >= config.W_PROMOTE else 1,
                                              0 if (t[2] is not None and float(t[2]) <= config.GPS_OK_M) else 1,
                                              -t[0]["w"], t[1]["observed_at"], t[1]["observation_id"]))
    else:
        singles = sorted(kept, key=lambda t: (-t[0]["w"], t[1]["observation_id"]))
    out: list[dict] = []
    for r, o, acc in singles[:max(0, int(config.SINGLE_MAX_EMITTED))]:
        gran = "street"
        if config.SINGLE_QUALITY_TIERING:
            well_measured = acc is not None and float(acc) <= config.GPS_OK_M
            gran = "street" if (r["w"] >= config.W_PROMOTE and well_measured) else "locality"
        out.append(make_candidate(
            address_id, "field_evidence", f"visit:{o['observation_id']}", o["x"], o["y"], gran,
            {"built_from": "store observations", "observation_id": o["observation_id"],
             "evidence_weight": r["w"], "gps_accuracy_m": acc, "collected_at": o["observed_at"],
             "stratum": gran, "single_quality_tier": config.SINGLE_QUALITY_TIERING,
             "primary_eligible": False},          # a single check-in supports; it never relocates
            valid_from=o["observed_at"], arm_rank=len(out) + 1))
    strong = [r for r in rows if r["w"] >= config.W_PROMOTE]
    if len(strong) >= 2:
        mx, my = geo.median([r["obs"]["x"] for r in strong]), geo.median([r["obs"]["y"] for r in strong])
        spread = max(geo.dist(r["obs"]["x"], r["obs"]["y"], mx, my) for r in strong)
        if spread <= config.CONSISTENCY_BAND_M:
            accs = [r["obs"].get("gps_accuracy_m") for r in strong if r["obs"].get("gps_accuracy_m") is not None]
            gran = "rooftop" if (accs and geo.median(accs) <= config.GPS_FINE_M and spread <= 30.0) else "street"
            out.insert(0, make_candidate(
                address_id, "field_evidence", f"visits:median({len(strong)})", mx, my, gran,
                {"built_from": "store observations (median of agreeing independent check-ins)",
                 "n_observations": len(strong), "spread_m": round(spread, 1),
                 "observation_ids": sorted(r["obs"]["observation_id"] for r in strong),
                 "stratum": gran, "primary_eligible": True},
                valid_from=max(r["obs"]["observed_at"] for r in strong), arm_rank=1))
    return out


ACCUMULATED_EVIDENCE_ARMS = ("field_evidence",)   # arms whose coordinate IS accumulated field evidence


def memory_candidates(address_id: str, as_of, store) -> list[dict]:
    """This address's own prior belief, as known at `as_of` — a prior, never a truth.

    **What the prior actually carries matters.** A belief's coordinate can be accumulated field
    evidence (the prior candidate came from `field_evidence`) or it can be a static arm that nothing
    has moved yet. Only the first is memory worth trusting as memory: the second merely re-wraps the
    vendor pin under a stronger-looking arm, and the policy experiment measured that class as adding
    exactly nothing over the pin it copies. The provenance records which one this is, and
    `config.MEMORY_EMIT` / `config.MEMORY_REQUIRES_EVIDENCE_DERIVED` decide what may enter the set.
    """
    prev = store.latest_belief_before(address_id, as_of)
    if (not prev or not prev.get("candidate_id")) and config.MEMORY_ON_DEMAND_BELIEF:
        # Belief is a *pure function* of the store at `as_of` (contract §6); the stored rows are a
        # projection, not the authority. A stored row can be absent at an arbitrary as-of instant
        # simply because nothing materialised it there — which used to make the memory arm silently
        # vanish at any cut that is not a visit instant. Recompute instead of guessing.
        from .belief import compute_belief
        try:
            # the prior is computed over the evidence-and-static set, never re-entering this function
            bare = _static_candidates(address_id, as_of, store, ix=None) + field_evidence_candidates(
                address_id, as_of, store)
            b = compute_belief(address_id, as_of, store, candidates=bare)
        except KeyError:
            return []
        if not b.get("candidate_id"):
            return []
        prev = {"belief_version": b["belief_version"], "as_of": as_of, "candidate_id": b["candidate_id"],
                "payload": b}
    if not prev or not prev.get("candidate_id"):
        return []
    payload = prev["payload"]
    cand = payload.get("candidate")
    if not cand or cand.get("x") is None:
        return []
    prov = cand.get("provenance") or {}
    derived_from = prov.get("built_from", "")
    evidence_derived = str(derived_from).startswith("store observations")
    if not evidence_derived:
        # the prior candidate's own arm is the marker when `built_from` is absent (older beliefs)
        evidence_derived = cand.get("arm") in ACCUMULATED_EVIDENCE_ARMS
    if config.MEMORY_EMIT == "evidence_derived_only" and not evidence_derived:
        return []
    eligible = payload.get("tier") in ("CONFIRMED", "PROBABLE")
    if config.MEMORY_REQUIRES_EVIDENCE_DERIVED and not evidence_derived:
        eligible = False
    return [make_candidate(address_id, "memory", f"memory:{address_id}@v{prev['belief_version']}",
                           cand["x"], cand["y"], cand.get("granularity") or "street",
                           {"built_from": "belief_versions", "prior_tier": payload.get("tier"),
                            "prior_status": payload.get("status"), "prior_as_of": prev["as_of"],
                            "prior_candidate_arm": cand.get("arm"),
                            "memory_evidence_derived": bool(evidence_derived),
                            "stratum": prov.get("stratum", "street"),
                            "primary_eligible": eligible},
                           valid_from=prev["as_of"])]


def place_neighbour_candidates(address_id: str, as_of, store, enable: bool | None = None) -> list[dict]:
    """C2-gated (D43). Emits nothing unless the experiment explicitly admitted the index."""
    enable = config.ENABLE_PLACE_NEIGHBOUR if enable is None else enable
    if not enable:
        return []
    raise RuntimeError("place_neighbour requires an admitted C2 index artefact; not built in this phase")


def _static_candidates(address_id: str, as_of, store=None, *, ix=None, ring=None, book=None) -> list[dict]:
    """The arms that need no store: pin, locality, town, landmark, address book."""
    if ix is None:
        from .indexes import get_index
        ix = get_index()
    ring = ring or get_ring(RING_B2)
    if book is None:
        book = ix.text_index if getattr(ring, "ring_id", None) == RING_B2 else ring.address_book_index(ix)
    A, L, LM, BG = ix.addresses, ix.localities, ix.landmarks, ix.baseline
    addr = A.get(address_id)
    if not addr:
        return []
    out: list[dict] = []
    out += _frozen_baseline(address_id, BG, as_of)
    out += _locality_centroid(addr, L, as_of, ring, ix)
    out += _town_centroid(addr, ix.town_centroids, as_of)
    out += _official_landmark(addr, LM, as_of, ring, ix)
    out += _address_book(addr, book, BG, as_of)
    return out


# ── the generator ───────────────────────────────────────────────────────────────────────────────
def generate(address_id: str, as_of, store=None, *, ix=None, enable_neighbour: bool | None = None,
             ring=None) -> list[dict]:
    """All candidates for one address as of `as_of`, deduplicated by (arm, source_ref).

    `ring` selects the text primitives (Experiment B). Default `None` = `B2`, production. The arm set,
    the record shape, the licence class and the as-of rules are identical under every ring.
    """
    from .indexes import get_index
    ix = ix or get_index()
    ring = ring or get_ring(RING_B2)
    book = ix.text_index if getattr(ring, "ring_id", None) == RING_B2 else ring.address_book_index(ix)
    A, L, LM, BG, TI = ix.addresses, ix.localities, ix.landmarks, ix.baseline, ix.text_index
    addr = A.get(address_id)
    if not addr:
        return []
    out: list[dict] = []
    out += _static_candidates(address_id, as_of, store, ix=ix, ring=ring, book=book)
    if store is not None:
        out += field_evidence_candidates(address_id, as_of, store)
        out += memory_candidates(address_id, as_of, store)
    out += place_neighbour_candidates(address_id, as_of, store, enable_neighbour)
    out = _apply_landmark_plausibility(out)

    seen, uniq = set(), []
    for c in sorted(out, key=lambda c: (config.ARMS.index(c["arm"]) if c["arm"] in config.ARMS else 99,
                                        c["arm_rank"], c["candidate_id"])):
        k = (c["arm"], c["source_ref"])
        if k in seen:
            continue
        seen.add(k)
        uniq.append(c)
    return annotate_agreement(uniq)


def _apply_landmark_plausibility(cands: list[dict]) -> list[dict]:
    """A landmark named *in the address text* is by construction near the address.

    When other arms exist, any landmark hit further than `LANDMARK_PLAUSIBILITY_M` from **every**
    other-arm candidate is dropped (deterministic, recorded on the survivors). This is the one place a
    bad landmark match is filtered rather than merely down-ranked: 240 generic POIs ("Bus Stop",
    "Masjid") repeat across a town, and a wrong one must not be able to win the ranking.
    """
    lm = [c for c in cands if c["arm"] == "official_landmark"]
    if not lm:
        return cands
    others = [c for c in cands if c["arm"] != "official_landmark"]
    if not others:
        return cands
    keep, dropped = [], 0
    for c in lm:
        d = min(geo.dist(c["x"], c["y"], o["x"], o["y"]) for o in others)
        if d <= config.LANDMARK_PLAUSIBILITY_M:
            c["provenance"] = dict(c["provenance"], plausibility_m=round(d, 1))
            keep.append(c)
        else:
            dropped += 1
    if dropped:
        for c in keep:
            c["provenance"] = dict(c["provenance"], landmark_implausible_dropped=dropped)
    return [c for c in cands if c["arm"] != "official_landmark"] + keep


def annotate_agreement(cands: list[dict]) -> list[dict]:
    """Cross-arm agreement: how many *other* arms land within the consistency band of this one.

    Computed from the candidate set alone (official data + this address's own evidence), so it stays
    a pure function of the as-of state and travels inside `provenance` (hence inside the belief bytes).
    """
    for c in cands:
        others = {o["arm"] for o in cands if o["candidate_id"] != c["candidate_id"]
                  and geo.dist(o["x"], o["y"], c["x"], c["y"]) <= config.SPACE_BAND_M}
        c["provenance"] = dict(c["provenance"], agreement_arms=len(others),
                               agreement_list=sorted(others))
    return cands
