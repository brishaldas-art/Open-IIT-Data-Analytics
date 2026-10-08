"""Offline packs (P11, contract §3/§11): versioned, deterministic, **no polygons**, no truth.

A pack is what the field app downloads before losing network: the town's addresses with their static
candidates, the town's localities and landmarks, the radius map, and the rule versions. Evidence is
*never* in the pack — evidence is appended on the device and replayed later.
"""
from __future__ import annotations

import hashlib
import json
import os

from . import asof, candidates as cand_mod, config
from .version import (EVIDENCE_POLICY_VERSION, GATE_RULE_VERSION, RADIUS_MAP_VERSION, RULE_VERSION,
                      SCHEMA_VERSION)

PACK_DIR = os.path.join(config.DERIVED, "packs")


def _canon(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _plus_days(ts, days: int) -> str:
    from datetime import timedelta
    return asof.to_utc_str(asof.parse_ts(ts) + timedelta(days=int(days)))


def build_pack(town_id: str, valid_days: int = config.PACK_VALID_DAYS_DEFAULT, *, store=None,
               ix=None, as_of=None, out_dir: str | None = None) -> dict:
    """Build (and persist) the pack for one town. Deterministic: same inputs → same pack bytes."""
    from .indexes import get_index
    ix = ix or get_index()
    as_of = as_of or config.MOMENT
    out = out_dir or PACK_DIR
    os.makedirs(out, exist_ok=True)

    if town_id not in ix.towns:
        raise KeyError(f"unknown town_id: {town_id}")

    addrs = []
    for aid in sorted(ix.addresses):
        row = ix.addresses[aid]
        if row["town_id"] != town_id:
            continue
        cands = cand_mod.generate(aid, as_of, store=None, ix=ix)      # static arms only: no evidence in a pack
        addrs.append({"address_id": aid, "address_text": row.get("address_text"),
                      "text_norm": row.get("text_norm") or "", "account_id": row.get("account_id"),
                      "address_type": row.get("address_type"),
                      "place_block_id": ix.block_of(aid), "candidates": cands})

    landmarks = [{"poi_id": p["poi_id"], "name": p["name"], "landmark_type": p["landmark_type"],
                  "x": float(p["x"]), "y": float(p["y"])} for p in ix.landmarks if p["town_id"] == town_id]
    localities = [{"locality_id": L["locality_id"], "locality_name": L["locality_name"],
                   "pincode": L["pincode"], "x": float(L["centroid_x"]), "y": float(L["centroid_y"])}
                  for L in ix.localities if L["town_id"] == town_id]

    body = {
        "town_id": town_id, "town_name": ix.towns[town_id]["town_name"],
        "built_for_as_of": asof.to_utc_str(as_of),
        "valid_days": int(valid_days), "valid_until": _plus_days(as_of, valid_days),
        "n_addresses": len(addrs), "addresses": addrs, "localities": localities, "landmarks": landmarks,
        "radius_map": {s: {"radius_m": v["radius_m"], "n_calibration": v["n_calibration"],
                           "measured_coverage": v["measured_coverage"], "publishable": v["publishable"]}
                       for s, v in config.RADIUS_TABLE.items()},
        "fallback_stratum": config.FALLBACK_STRATUM,
        "versions": {"schema_version": SCHEMA_VERSION, "rule_version": RULE_VERSION,
                     "radius_map_version": RADIUS_MAP_VERSION,
                     "evidence_policy_version": EVIDENCE_POLICY_VERSION,
                     "gate_rule_version": GATE_RULE_VERSION},
        "contains_polygons": False,
        "contains_evidence": False,
        "contains_truth": False,
    }
    pack_sha = hashlib.sha256(_canon(body).encode("utf-8")).hexdigest()
    pack_version = f"pack-{town_id}-{pack_sha[:12]}"
    body["pack_version"] = pack_version
    body["pack_sha256"] = pack_sha          # both self-referential fields are excluded from the hash
    path = os.path.join(out, f"{pack_version}.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(body, fh, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    manifest = {
        "pack_version": pack_version, "pack_sha256": pack_sha, "town_id": town_id,
        "valid_until": body["valid_until"], "valid_days": body["valid_days"],
        "n_addresses": len(addrs), "n_landmarks": len(landmarks), "n_localities": len(localities),
        "path": os.path.relpath(path, config.ROOT), "bytes": os.path.getsize(path),
        "contains_polygons": False, "contains_evidence": False, "contains_truth": False,
        "versions": body["versions"],
    }
    return manifest


def load_pack(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def verify_pack(pack: dict) -> dict:
    """Client-side verification: recompute the hash over the body (excluding the version fields)."""
    body = {k: v for k, v in pack.items() if k not in ("pack_version", "pack_sha256")}
    sha = hashlib.sha256(_canon(body).encode("utf-8")).hexdigest()
    return {"ok": sha == pack.get("pack_sha256"), "pack_sha256": sha,
            "declared": pack.get("pack_sha256"), "town_id": pack.get("town_id"),
            "valid_until": pack.get("valid_until")}


def pack_is_stale(pack: dict, as_of=None) -> bool:
    as_of = as_of or asof.now_utc()
    return asof.parse_ts(as_of) > asof.parse_ts(pack["valid_until"])
