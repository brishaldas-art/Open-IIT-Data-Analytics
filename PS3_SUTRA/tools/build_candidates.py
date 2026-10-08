#!/usr/bin/env python3
"""P2 — candidate generation, the contract way (rewrites the pre-contract builder).

    python3 tools/build_candidates.py

Arms (exactly these; `place_neighbour` stays disabled until C2 admits it):

    frozen_baseline · locality_centroid · town_centroid · official_landmark · address_book ·
    field_evidence · memory · place_neighbour

Every candidate carries `licence_class = "official"`, a stable `candidate_id`, a `source_ref`, a
granularity, its provenance, and `as_of_valid` **iff** it is evidence-backed. No candidate carries a
truth column; truth lives only in `labels_eval_v2.csv`, which is evaluation-only and S-Eval-only.

Outputs (data/derived/):
  candidates_v2.csv + candidates_v2.receipt.json
  features_coldstart_v2.csv + receipt    (static arms; nothing visit-derived, as_of_valid all null)
  features_warm_v2.csv + receipt         (all arms as of the canonical instant, via the frozen as-of gate)
  labels_eval_v2.csv                     (S-Eval only: err_m and hits; never joined into a feature set)
"""
from __future__ import annotations

import csv
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sutra import asof, config, geo, ranking                      # noqa: E402
from sutra.candidates import generate                             # noqa: E402
from sutra.indexes import get_index                               # noqa: E402
from sutra.store import Store                                     # noqa: E402
from sutra.version import (EVIDENCE_POLICY_VERSION, RULE_VERSION,  # noqa: E402
                           SCHEMA_VERSION)

CAND_COLS = ["candidate_id", "address_id", "account_id", "town_id", "arm", "source_ref", "x", "y",
             "granularity", "arm_rank", "licence_class", "as_of_valid", "stratum", "primary_eligible",
             "agreement_arms", "rule_version", "built_at"]
FEAT_COLS = ["candidate_id", "address_id", "arm", "granularity", "arm_rank", "as_of_valid"] + list(ranking.FEATURES)
LABEL_COLS = ["candidate_id", "address_id", "arm", "granularity", "x", "y", "err_m", "label_within_100m",
              "label_within_250m", "is_best_of_set", "label_source", "split"]


def cand_row(c: dict, addr: dict) -> dict:
    prov = c.get("provenance", {})
    return {
        "candidate_id": c["candidate_id"], "address_id": c["address_id"],
        "account_id": addr.get("account_id"), "town_id": addr.get("town_id"), "arm": c["arm"],
        "source_ref": c["source_ref"], "x": c["x"], "y": c["y"], "granularity": c["granularity"],
        "arm_rank": c["arm_rank"], "licence_class": c["licence_class"],
        "as_of_valid": c["as_of_valid"], "stratum": prov.get("stratum", c["granularity"]),
        "primary_eligible": bool(prov.get("primary_eligible", True)),
        "agreement_arms": prov.get("agreement_arms"), "rule_version": prov.get("rule_version"),
        "built_at": prov.get("built_at"),
    }


def main() -> int:
    t0 = time.time()
    out = config.DERIVED
    ix = get_index()
    st = Store()
    moment = config.MOMENT

    # ── candidates + features ───────────────────────────────────────────────────────────────────
    cand_rows, cold_rows, warm_rows = [], [], []
    for i, aid in enumerate(sorted(ix.addresses), start=1):
        addr = ix.addresses[aid]
        cold = generate(aid, moment, store=None, ix=ix)          # static arms only
        warm = generate(aid, moment, store=st, ix=ix)            # + field_evidence + memory
        for c in warm:
            cand_rows.append(cand_row(c, addr))
        all_feats = ranking.features_matrix(addr, warm, ix)
        for c in cold:
            cold_rows.append({**{k: cand_row(c, addr)[k] for k in FEAT_COLS[:6]}, **all_feats[c["candidate_id"]]})
        for c in warm:
            warm_rows.append({**{k: cand_row(c, addr)[k] for k in FEAT_COLS[:6]}, **all_feats[c["candidate_id"]]})
        if i % 1000 == 0:
            print(f"  {i}/{len(ix.addresses)} addresses")

    _write(os.path.join(out, "candidates_v2.csv"), CAND_COLS, cand_rows)
    _write(os.path.join(out, "features_coldstart_v2.csv"), FEAT_COLS, cold_rows)
    _write(os.path.join(out, "features_warm_v2.csv"), FEAT_COLS, warm_rows)

    # ── evaluation-only labels for S-Eval (the 100 surveyed addresses) ──────────────────────────
    st.bump_counter("s_eval_looks", detail="build_candidates:labels_eval_v2")
    lab_rows = []
    by_addr: dict[str, list[dict]] = {}
    for r in cand_rows:
        by_addr.setdefault(r["address_id"], []).append(r)
    for aid, sv in sorted(ix_surveyed().items()):
        tx, ty = sv
        rows = by_addr.get(aid, [])
        errs = [(geo.dist(r["x"], r["y"], tx, ty), r) for r in rows]
        best = min((e for e, _ in errs), default=None)
        for e, r in errs:
            lab_rows.append({"candidate_id": r["candidate_id"], "address_id": aid, "arm": r["arm"],
                             "granularity": r["granularity"], "x": r["x"], "y": r["y"],
                             "err_m": round(e, 3), "label_within_100m": int(e <= 100),
                             "label_within_250m": int(e <= 250),
                             "is_best_of_set": int(best is not None and abs(e - best) < 1e-9),
                             "label_source": "surveyed_ground_truth", "split": "S-EVAL"})
    _write(os.path.join(out, "labels_eval_v2.csv"), LABEL_COLS, lab_rows)

    # ── receipts ────────────────────────────────────────────────────────────────────────────────
    arms_used = sorted({r["arm"] for r in cand_rows})
    licences = sorted({r["licence_class"] for r in cand_rows})
    cold_arms = sorted({r["arm"] for r in cold_rows})
    warm_only = sorted(set(arms_used) - set(cold_arms))
    recv_common = {
        "schema_version": SCHEMA_VERSION, "rule_version": RULE_VERSION,
        "evidence_policy_version": EVIDENCE_POLICY_VERSION, "built_for_as_of": moment,
        "arms": arms_used, "licence_classes": licences, "contains_truth_column": False,
        "contains_vendor_call": False, "external_data": False,
        "notes": ["every candidate is generated by sutra/candidates.py (contract §4)",
                  "as_of_valid is present iff the arm is evidence-backed",
                  "no candidate file carries a truth label; labels live in labels_eval_v2.csv"],
    }
    _write_receipt(os.path.join(out, "candidates_v2.receipt.json"),
                   {**recv_common, "statement": "candidate universe built to the implementation contract",
                    "n_rows": len(cand_rows), "n_addresses": len({r["address_id"] for r in cand_rows}),
                    "arms_cold_start": cold_arms, "arms_warm_only": warm_only})
    _write_receipt(os.path.join(out, "features_coldstart_v2.receipt.json"),
                   {**recv_common, "arms": cold_arms,
                    "statement": ("cold-start feature matrix: static arms only, no evidence-backed "
                                  "arm, no visit-derived value; every as_of_valid is null"),
                    "n_rows": len(cold_rows), "n_addresses": len({r["address_id"] for r in cold_rows}),
                    "features": list(ranking.FEATURES), "n_features": len(ranking.FEATURES),
                    "forbidden_prefix_flag": _forbidden(cold_rows)})
    _write_receipt(os.path.join(out, "features_warm_v2.receipt.json"),
                   {**recv_common, "statement": ("warm feature matrix: all arms as of the canonical instant; "
                                                 "evidence arms carry as_of_valid and are read through the frozen "
                                                 "as-of gate (never 'latest visit')"),
                    "n_rows": len(warm_rows), "n_addresses": len({r["address_id"] for r in warm_rows}),
                    "features": list(ranking.FEATURES), "n_features": len(ranking.FEATURES),
                    "forbidden_prefix_flag": _forbidden(warm_rows)})

    print(f"candidates      : {len(cand_rows)} rows / {len({r['address_id'] for r in cand_rows})} addresses"
          f"  arms={arms_used}")
    print(f"features cold/warm: {len(cold_rows)} / {len(warm_rows)} rows · {len(ranking.FEATURES)} features")
    print(f"labels (S-Eval) : {len(lab_rows)} rows over {len(ix_surveyed())} surveyed addresses")
    print(f"licence classes : {licences}")
    print(f"seconds         : {time.time() - t0:.1f}")
    return 0


def ix_surveyed() -> dict[str, tuple[float, float]]:
    import csv as _csv
    p = os.path.join(config.OFFICIAL, "surveyed_addresses.csv")
    with open(p, encoding="utf-8", newline="") as fh:
        return {r["address_id"]: (float(r["surveyed_x"]), float(r["surveyed_y"])) for r in _csv.DictReader(fh)}


def _forbidden(rows: list[dict]) -> list[str]:
    bad = ("checkin", "gps_", "dwell", "outcome", "photo", "remark", "trail", "surveyed", "label_", "err_m")
    cols = set(rows[0]) if rows else set()
    return sorted(c for c in cols if any(t in c.lower() for t in bad))


def _write(path: str, cols: list[str], rows: list[dict]) -> None:
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def _write_receipt(path: str, obj: dict) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, sort_keys=True, ensure_ascii=False)


if __name__ == "__main__":
    raise SystemExit(main())
