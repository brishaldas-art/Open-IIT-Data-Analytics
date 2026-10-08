#!/usr/bin/env python3
"""P12 step A — the official frozen baseline arm against ground truth, on the three A1 populations.

    python3 tools/experiment_a.py

Question (experiment plan §2 A): *what does the frozen baseline arm alone achieve on our ground truth?*
Method: top-1 by rule priority — `frozen_baseline` where present, `town_centroid` otherwise — reported
on (1) all 100 surveyed addresses, (2) the validation+test accounts, (3) leave-block-out.

This is the floor every other experiment must beat, and it doubles as a **regression check on the
implementation**: the pre-contract pipeline measured median 376.4 m / <100 m 9.0% / coverage 92.4% on
population 1 `[S91]`. The post-contract runtime must reproduce that number through a completely
different code path, or the difference must be explained.

Lawful reads only: the run declares the `S_EVAL_BASELINE` SplitSpec (contract §2/§15 T15) and every
population read increments the test-look counter, which is reported here.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sutra import asof, config, dataio, geo, splits                     # noqa: E402
from sutra.candidates import generate                                   # noqa: E402
from sutra.indexes import get_index                                     # noqa: E402
from sutra.store import Store                                           # noqa: E402

CUT = config.MOMENT
# the three A1 populations, as membership rules (no hidden list)
POPULATIONS = ("all_100", "validation_plus_test", "leave_block_out")


def populations(ix) -> dict[str, list[str]]:
    surveyed = sorted(dataio.surveyed())
    sp = dataio.splits_table()
    blocks = {}
    for aid, b in ix.place_blocks.items():
        blocks.setdefault(b["block_id"], set()).add(b["split"])
    val_test = [a for a in surveyed
                if sp.get(ix.addresses[a]["account_id"], {}).get("split") in ("validation", "test")]
    leave_block_out = [a for a in surveyed if "train" not in blocks.get(ix.block_of(a), set())]
    return {"all_100": surveyed, "validation_plus_test": val_test, "leave_block_out": leave_block_out}


def q(values, p):
    """Linear-interpolated quantile (the pandas/numpy convention), so medians reproduce the
    historical measurements exactly rather than to the nearest order statistic."""
    import math
    if not values:
        return None
    vs = sorted(values)
    if len(vs) == 1:
        return round(vs[0], 1)
    pos = p * (len(vs) - 1)
    lo, hi = math.floor(pos), math.ceil(pos)
    return round(vs[lo] + (vs[hi] - vs[lo]) * (pos - lo), 1)


def block(rows: list[dict]) -> dict:
    errs = [r["err_m"] for r in rows]
    n = len(errs)
    return {"n": n, "median_err_m": q(errs, 0.5), "p80_err_m": q(errs, 0.8), "max_err_m": round(max(errs), 1) if errs else None,
            "hit_100m": round(sum(1 for e in errs if e <= 100) / n, 4) if n else None,
            "hit_250m": round(sum(1 for e in errs if e <= 250) / n, 4) if n else None,
            "hit_500m": round(sum(1 for e in errs if e <= 500) / n, 4) if n else None}


def main() -> int:
    # the gate first: no metrics without a declared split (T15)
    spec = splits.require_declared(splits.declared_specs()[0])          # S_EVAL_BASELINE
    ix = get_index()
    st = Store()
    surveyed = dataio.surveyed()
    pops = populations(ix)

    out: dict = {"spec": spec.to_json(), "label_source": "surveyed_ground_truth", "as_of": CUT,
                 "label_basis": "surveyed ground truth (the only ground truth this project has, n=100)",
                 "populations": {k: len(v) for k, v in pops.items()},
                 "reports": {}, "test_look_reads": []}

    for name in POPULATIONS:
        st.bump_counter("s_eval_looks", detail=f"experiment_A:{name}")
        rows_priority, rows_arm = [], []
        for aid in pops[name]:
            tx, ty = float(surveyed[aid]["surveyed_x"]), float(surveyed[aid]["surveyed_y"])
            cands = generate(aid, CUT, st, ix=ix)
            static = [c for c in cands if c["arm"] in config.STATIC_ARMS]
            pin = next((c for c in static if c["arm"] == "frozen_baseline"), None)
            town = next((c for c in static if c["arm"] == "town_centroid"), None)
            top = pin or town
            if pin:
                rows_arm.append({"address_id": aid, "arm": "frozen_baseline",
                                 "err_m": geo.dist(pin["x"], pin["y"], tx, ty)})
            if top:
                rows_priority.append({"address_id": aid, "arm": top["arm"],
                                      "err_m": geo.dist(top["x"], top["y"], tx, ty)})
        cold = {a: block([r for r in rows_arm if r["arm"] == a]) for a in ("frozen_baseline",)}
        out["reports"][name] = {
            "n_surveyed": len(pops[name]),
            "coverage": round(len(rows_priority) / max(1, len(pops[name])), 4),
            "frozen_baseline_only": cold["frozen_baseline"],
            "rule_priority_top1 (frozen_baseline else town_centroid)": block(rows_priority),
        }
        out["test_look_reads"].append({"population": name, "n": len(pops[name])})

    n_book = len(ix.addresses)
    n_pin = sum(1 for a in ix.addresses if a in ix.baseline)
    out["corpus_coverage"] = {"n_addresses": n_book, "n_with_frozen_baseline": n_pin,
                              "share": round(n_pin / n_book, 4),
                              "note": "the pre-contract 'coverage 92.4%' figure [S91] is this share"}
    out["test_look_counter"] = st.counters("s_eval_looks")
    out["regression_check"] = {
        "pre_contract_reference": {"population": "all_100", "median_err_m": 376.4, "hit_100m": 0.09,
                                   "hit_500m": 0.71, "coverage": 0.924, "source": "[S91]"},
        "post_contract": out["reports"]["all_100"]["rule_priority_top1 (frozen_baseline else town_centroid)"],
    }
    ref = out["regression_check"]["pre_contract_reference"]
    got = out["regression_check"]["post_contract"]
    out["regression_check"]["median_delta_m"] = (round(got["median_err_m"] - ref["median_err_m"], 1)
                                                 if got["median_err_m"] is not None else None)
    out["regression_check"]["matches"] = bool(got["median_err_m"] is not None
                                              and abs(got["median_err_m"] - ref["median_err_m"]) < 0.5)

    p = os.path.join(config.DERIVED, "experiment_A_report.json")
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, sort_keys=True, ensure_ascii=False)

    print(f"experiment A — the floor (split {spec.spec_id}, label source {spec.label_source})")
    for name in POPULATIONS:
        r = out["reports"][name]
        t = r["rule_priority_top1 (frozen_baseline else town_centroid)"]
        a = r["frozen_baseline_only"]
        print(f"  {name:22s} n={r['n_surveyed']:3d} cov={r['coverage']:.3f} | "
              f"top1 median={t['median_err_m']} m  <100 m={t['hit_100m']}  <500 m={t['hit_500m']} | "
              f"pin-only median={a['median_err_m']} m (n={a['n']})")
    rc = out["regression_check"]
    print(f"  regression vs pre-contract [S91]: median {rc['post_contract']['median_err_m']} m vs "
          f"{rc['pre_contract_reference']['median_err_m']} m -> matches={rc['matches']}")
    print(f"  corpus coverage     : {out['corpus_coverage']['n_with_frozen_baseline']}/"
          f"{out['corpus_coverage']['n_addresses']} = {out['corpus_coverage']['share']:.3f} "
          f"(the historical 92.4%)")
    print(f"  test-look counter   : {out['test_look_counter']}")
    print(f"wrote {os.path.relpath(p, config.ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
