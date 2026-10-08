"""Precomputed runtime indexes (P3).

`/resolve` must not scan CSVs with pandas. Everything the request path needs is built once into
`data/derived/runtime_indexes/` as canonical JSON with a hash manifest, loaded lazily, and rebuildable
deterministically: rebuild → same bytes (the build tool asserts the manifest hash).

Indexes: addresses · text book (normalised text -> records) · locality · locality-by-pincode ·
landmark · landmark-name · town centroid · place blocks · memory (address -> place + belief refs).
"""
from __future__ import annotations

import json
import os

from . import config, dataio
from .version import RULE_VERSION

INDEX_FILES = ("addresses", "text_book", "localities", "localities_by_pin", "landmarks",
               "landmark_names", "town_centroids", "place_blocks", "memory", "token_idf")


def _canon(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _write_json(path: str, obj) -> str:
    import hashlib
    txt = _canon(obj)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(txt)
    return hashlib.sha256(txt.encode("utf-8")).hexdigest()


def build(out_dir: str | None = None, store=None) -> dict:
    """Build every index from official/cleaned/derived inputs. Deterministic; returns the manifest."""
    from .candidates import town_centroids
    out = out_dir or config.INDEX_DIR
    os.makedirs(out, exist_ok=True)
    hashes: dict[str, str] = {}

    A = dataio.addresses()
    addresses = {aid: {k: v for k, v in row.items()} for aid, row in sorted(A.items())}
    hashes["addresses"] = _write_json(os.path.join(out, "addresses.json"), addresses)

    text_book: dict[str, list[str]] = {}
    for aid, row in sorted(A.items()):
        key = f"{row['town_id']}|{row.get('text_norm') or dataio.norm_text(row.get('address_text',''))}"
        text_book.setdefault(key, []).append(aid)
    hashes["text_book"] = _write_json(os.path.join(out, "text_book.json"),
                                      {k: sorted(v) for k, v in sorted(text_book.items())})

    L = sorted(dataio.localities(), key=lambda r: r["locality_id"])
    hashes["localities"] = _write_json(os.path.join(out, "localities.json"), L)
    by_pin: dict[str, list[str]] = {}
    for r in L:
        by_pin.setdefault(f"{r['town_id']}|{r['pincode']}", []).append(r["locality_id"])
    hashes["localities_by_pin"] = _write_json(os.path.join(out, "localities_by_pin.json"),
                                              {k: sorted(v) for k, v in sorted(by_pin.items())})

    LM = sorted(dataio.landmarks(), key=lambda r: r["poi_id"])
    hashes["landmarks"] = _write_json(os.path.join(out, "landmarks.json"), LM)
    name_ix: dict[str, list[str]] = {}
    for r in LM:
        for tok in sorted(set(dataio.tokens(r["name"]))):
            name_ix.setdefault(f"{r['town_id']}|{tok}", []).append(r["poi_id"])
    hashes["landmark_names"] = _write_json(os.path.join(out, "landmark_names.json"),
                                           {k: sorted(v) for k, v in sorted(name_ix.items())})

    hashes["town_centroids"] = _write_json(os.path.join(out, "town_centroids.json"),
                                           {t: [round(x, 3), round(y, 3)]
                                            for t, (x, y) in sorted(town_centroids(L).items())})

    # retrieval-v2: token document frequencies over official address text added before the cut.
    # Unsupervised, official-only, as-of clean — the weight behind "a rare token match is evidence".
    from .preprocess import get as _ring_for
    _cut = config.MOMENT.isoformat() if hasattr(config.MOMENT, "isoformat") else str(config.MOMENT)
    _r = _ring_for(config.RETRIEVAL_RING)
    _df: dict[str, int] = {}
    _docs = 0
    for _aid, _row in sorted(A.items()):
        if str(_row.get("added_date", "")) >= _cut[:10]:
            continue                      # a record added after the cut cannot inform retrieval at the cut
        _docs += 1
        for _t in sorted(set(_r.tokens(_row.get("text_norm") or _row.get("address_text", "")))):
            _df[_t] = _df.get(_t, 0) + 1
    hashes["token_idf"] = _write_json(os.path.join(out, "token_idf.json"),
                                      {"docs": _docs, "df": dict(sorted(_df.items())),
                                       "ring": _r.ring_id, "cut": _cut[:10]})

    blocks = dataio.place_blocks()
    hashes["place_blocks"] = _write_json(os.path.join(out, "place_blocks.json"),
                                         {aid: {"block_id": r["block_id"], "fold": int(r["fold"]),
                                                "split": r["split"], "size": int(r["size"])}
                                          for aid, r in sorted(blocks.items())})

    memory_ix = _memory_index(store)
    hashes["memory"] = _write_json(os.path.join(out, "memory.json"), memory_ix)

    manifest = {"rule_version": RULE_VERSION, "files": hashes,
                "source_hashes": {name: _hash_file(os.path.join(config.OFFICIAL, name))
                                  for name in ("addresses.csv", "localities.csv", "landmarks_poi.csv",
                                               "towns.csv", "baseline_geocodes.csv", "surveyed_addresses.csv")}}
    _write_json(os.path.join(out, "manifest.json"), manifest)
    return {"dir": out, "manifest": manifest}


def _hash_file(path: str) -> str:
    import hashlib
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def _memory_index(store) -> dict:
    """address -> {place_id, belief: {version, tier, status, as_of}} — the memory arm's fast path."""
    if store is None:
        return {}
    out: dict[str, dict] = {}
    for r in store.conn.execute("SELECT address_id, place_id FROM place_members ORDER BY address_id"):
        out.setdefault(r["address_id"], {})["place_id"] = r["place_id"]
    for r in store.conn.execute(
            "SELECT address_id, belief_version, as_of, tier, status FROM belief_versions"
            " ORDER BY address_id, as_of"):
        out.setdefault(r["address_id"], {})["belief"] = {
            "version": int(r["belief_version"]), "as_of": r["as_of"], "tier": r["tier"], "status": r["status"]}
    return {k: v for k, v in sorted(out.items())}


# ── lazy loader ─────────────────────────────────────────────────────────────────────────────────
class RuntimeIndex:
    def __init__(self, path: str | None = None, autobuild: bool = True):
        self.path = path or config.INDEX_DIR
        if not os.path.exists(os.path.join(self.path, "manifest.json")) and autobuild:
            build(self.path)
        self.manifest = json.load(open(os.path.join(self.path, "manifest.json"), encoding="utf-8"))
        self.addresses = json.load(open(os.path.join(self.path, "addresses.json"), encoding="utf-8"))
        self.text_book = json.load(open(os.path.join(self.path, "text_book.json"), encoding="utf-8"))
        self.localities = json.load(open(os.path.join(self.path, "localities.json"), encoding="utf-8"))
        self.localities_by_pin = json.load(open(os.path.join(self.path, "localities_by_pin.json"), encoding="utf-8"))
        self.landmarks = json.load(open(os.path.join(self.path, "landmarks.json"), encoding="utf-8"))
        self.landmark_names = json.load(open(os.path.join(self.path, "landmark_names.json"), encoding="utf-8"))
        self.town_centroids = {t: (v[0], v[1]) for t, v in
                               json.load(open(os.path.join(self.path, "town_centroids.json"), encoding="utf-8")).items()}
        self.place_blocks = json.load(open(os.path.join(self.path, "place_blocks.json"), encoding="utf-8"))
        self.memory = json.load(open(os.path.join(self.path, "memory.json"), encoding="utf-8"))
        _idf = json.load(open(os.path.join(self.path, "token_idf.json"), encoding="utf-8"))
        self.token_docs = int(_idf["docs"])
        self.token_df = _idf["df"]
        self.baseline = dataio.baseline_geocodes()
        self.towns = dataio.towns()
        # text_book keys are "town|text"; candidates.py wants (town, text) -> [address_id]
        self.text_index = {tuple(k.split("|", 1)): v for k, v in self.text_book.items()}
        self.landmark_index: dict[tuple[str, str], list[str]] = {}
        for k, v in self.landmark_names.items():
            town, tok = k.split("|", 1)
            self.landmark_index[(town, tok)] = v
        self._poi_by_id = {p["poi_id"]: p for p in self.landmarks}

    def idf(self, token: str) -> float:
        """Smoothed inverse document frequency from the official corpus (retrieval-v2)."""
        import math
        return math.log((self.token_docs + 1) / (self.token_df.get(token, 0) + 1)) + 1.0

    def token_rarity(self, token: str) -> int:
        """Document frequency of a token: 0 means it never appears in the official corpus."""
        return self.token_df.get(token, 0)

    def poi(self, poi_id: str) -> dict | None:
        return self._poi_by_id.get(poi_id)

    def block_of(self, address_id: str) -> str | None:
        b = self.place_blocks.get(address_id)
        return b["block_id"] if b else None

    def town_of(self, address_id: str) -> str | None:
        a = self.addresses.get(address_id)
        return a["town_id"] if a else None

    def verify(self) -> dict:
        """Recompute every index hash and compare with the manifest (determinism check)."""
        bad = []
        for name, h in self.manifest["files"].items():
            p = os.path.join(self.path, f"{name}.json")
            if not os.path.exists(p) or _hash_file(p) != h:
                bad.append(name)
        return {"ok": not bad, "mismatched": bad}


_SINGLETON: RuntimeIndex | None = None


def get_index(path: str | None = None) -> RuntimeIndex:
    global _SINGLETON
    if _SINGLETON is None or (path and path != _SINGLETON.path):
        _SINGLETON = RuntimeIndex(path)
    return _SINGLETON
