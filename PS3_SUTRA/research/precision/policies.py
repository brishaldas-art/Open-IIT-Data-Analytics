"""Evidence/memory policy challengers — measured, not asserted.

Protocol
--------
* **Temporal holdout (the honest metric).** Candidates are built with `as_of = T0`, so only
  observations strictly before T0 exist; the label is the median of promoted visits *at or after* T0
  (trace-tail coordinates). Two cuts (2026-05-01, 2026-05-15) so a policy cannot be selected by one
  lucky split. No future observation reaches a candidate.
* **Supervision pool (continuity, flagged circular).** as-of = MOMENT with the operational proxy
  label; reported because every earlier experiment used it, and flagged because the label is built
  from the same visits that feed the warm arms.
* Every sample that produces no label is dropped, and the *same* samples are used for every policy,
  so policies are compared pairwise on identical populations.

Policy challengers are config knobs; the ranker is never touched.
"""
import collections
import statistics as st
import sys
import os

sys.path.insert(0, "/home/user/PS3_SUTRA")
os.chdir("/home/user/PS3_SUTRA")

from sutra import config, geo, splits, ranking, stats                      # noqa: E402
from sutra.candidates import generate                                      # noqa: E402
from sutra.indexes import get_index                                        # noqa: E402
from sutra.replay import _manifest, _proxy_truth                          # noqa: E402
from sutra.store import Store                                              # noqa: E402
from sutra.dataio import visits, visit_gps_traces                          # noqa: E402

PROMOTED = ("met_borrower", "met_family", "cash_collected")

# The pre-policy behaviour, expressed as an explicit restore patch. It is written out in full so that
# `P0 shipped` keeps meaning the same thing after the frozen policy becomes the shipped default —
# otherwise every scoreboard row would silently shift when the defaults change.
P0_PATCH = {"MEMORY_EMIT": "always", "MEMORY_REQUIRES_EVIDENCE_DERIVED": False,
            "MEMORY_ON_DEMAND_BELIEF": False, "SINGLE_TIEBREAK_QUALITY": False,
            "SINGLE_QUALITY_TIERING": False, "SINGLE_GATE_GPS_M": None,
            "SINGLE_GATE_MIN_WEIGHT": None, "SINGLE_MAX_EMITTED": 3}
POLICIES = {
    "P0 shipped": dict(P0_PATCH),
    "P1a memory not eligible when pin-derived": {"MEMORY_REQUIRES_EVIDENCE_DERIVED": True},
    "P1b memory not emitted when pin-derived": {"MEMORY_EMIT": "evidence_derived_only"},
    "P2 single quality tiering": {"SINGLE_QUALITY_TIERING": True},
    "P2b tiering + at most 2 singles": {"SINGLE_QUALITY_TIERING": True, "SINGLE_MAX_EMITTED": 2},
    "P2c tiering + at most 1 single": {"SINGLE_QUALITY_TIERING": True, "SINGLE_MAX_EMITTED": 1},
    "P3a drop singles with GPS > 50 m": {"SINGLE_GATE_GPS_M": 50.0},
    "P3b drop singles with GPS > 100 m": {"SINGLE_GATE_GPS_M": 100.0},
    "P4 tiering + memory evidence-derived": {"SINGLE_QUALITY_TIERING": True,
                                             "MEMORY_REQUIRES_EVIDENCE_DERIVED": True},
    "P5 on-demand prior (projection fix only)": {"MEMORY_ON_DEMAND_BELIEF": True},
    "P6 on-demand prior + memory evidence-derived": {"MEMORY_ON_DEMAND_BELIEF": True,
                                                     "MEMORY_EMIT": "evidence_derived_only"},
    "P7 on-demand + evidence-derived + tiering": {"MEMORY_ON_DEMAND_BELIEF": True,
                                                  "MEMORY_EMIT": "evidence_derived_only",
                                                  "SINGLE_QUALITY_TIERING": True},
    "P8 quality tie-break only": {"SINGLE_TIEBREAK_QUALITY": True},
    "P9 evidence-derived memory + quality tie-break": {"MEMORY_EMIT": "evidence_derived_only",
                                                       "MEMORY_ON_DEMAND_BELIEF": True,
                                                       "SINGLE_TIEBREAK_QUALITY": True},
    "P_FINAL (frozen policy)": {"MEMORY_EMIT": "evidence_derived_only",
                                "MEMORY_ON_DEMAND_BELIEF": True},
}
KNOBS = ("SINGLE_QUALITY_TIERING", "SINGLE_GATE_GPS_M", "SINGLE_GATE_MIN_WEIGHT", "SINGLE_MAX_EMITTED",
         "MEMORY_REQUIRES_EVIDENCE_DERIVED", "MEMORY_EMIT", "MEMORY_ON_DEMAND_BELIEF",
         "SINGLE_TIEBREAK_QUALITY")


def apply_policy(patch: dict) -> None:
    """Every row is evaluated from the same, explicitly written baseline — never from whatever the
    shipped default happens to be."""
    base = dict(P0_PATCH)
    base.update(patch)
    for k, v in base.items():
        setattr(config, k, v)


def q(v, p):
    v = sorted(v)
    return round(float(v[int(p * (len(v) - 1))]), 1) if v else None


def fr(v, t):
    return round(sum(1 for x in v if x <= t) / len(v), 4) if v else None


def tail3(v, traces):
    t = traces.get(v["visit_id"])
    if not t:
        return None
    tail = t[-3:]
    return (geo.median([float(p[1]) for p in tail]), geo.median([float(p[2]) for p in tail]))


def labels_after(t0, addresses, traces):
    by = collections.defaultdict(list)
    for v in visits():
        if v.get("outcome") in PROMOTED and v["address_id"] in addresses and v["visit_date"][:10] >= t0:
            p = tail3(v, traces)
            if p:
                by[v["address_id"]].append(p)
    return {a: (geo.median([p[0] for p in pts]), geo.median([p[1] for p in pts]))
            for a, pts in by.items() if pts}


def production_pick(ix, store, aid, as_of):
    """Exactly what the runtime would answer: the frozen rule over every arm, at `as_of`."""
    cands = generate(aid, as_of, store, ix=ix)
    if not cands:
        return None
    feats = ranking.features_matrix(ix.addresses[aid], cands, ix)
    ranked = ranking.rank(cands, feats, as_of)
    by = {c["candidate_id"]: c for c in cands}
    return by[ranked[0]["candidate_id"]]


def arm_of(ix, store, aid, as_of):
    c = production_pick(ix, store, aid, as_of)
    return (c["arm"] if c else None), c


def run(ix, store, ids, as_of, label, traces, label_name):
    """One policy, one population: the production rule's top-1 error + arm mix."""
    errs, arms, picks = [], collections.Counter(), {}
    for a in ids:
        c = production_pick(ix, store, a, as_of)
        if c is None:
            continue
        e = geo.dist(c["x"], c["y"], *label[a])
        picks[a] = {"err": e, "arm": c["arm"]}
        errs.append(e)
        arms[c["arm"]] += 1
    return {"n": len(errs), "hit_100m": fr(errs, 100), "hit_250m": fr(errs, 250),
            "hit_500m": fr(errs, 500), "median_err_m": q(errs, 0.5), "p75_err_m": q(errs, 0.75),
            "mean_err_m": round(sum(errs) / len(errs), 1) if errs else None,
            "arm_mix": dict(arms.most_common()), "picks": picks, "errs": errs}


def main():
    ix = get_index()
    store = Store()
    man = _manifest(ix)
    pool = sorted(a for a, m in man.items() if m["split"] in (splits.S_TRAIN, splits.S_VAL))
    val = sorted(a for a, m in man.items() if m["split"] == splits.S_VAL)
    traces = visit_gps_traces()
    proxy = {a: _proxy_truth(store, a, config.MOMENT) for a in pool}
    cuts = {}
    for t0 in ("2026-05-01", "2026-05-15"):
        lab = labels_after(t0, set(pool), traces)
        cuts[t0] = {"ids": sorted(lab), "label": lab}
    print(f"pool {len(pool)} (S-VAL {len(val)}) · temporal cuts: "
          + " · ".join(f"{t0}: {len(c['ids'])} labels" for t0, c in cuts.items()))
    out = {}
    for name, patch in POLICIES.items():
        apply_policy(patch)
        rec = {"patch": patch}
        rec["pool_proxy (circular)"] = run(ix, store, pool, config.MOMENT, proxy, traces, "pool")
        rec["S-VAL proxy (circular)"] = run(ix, store, val, config.MOMENT, proxy, traces, "val")
        for t0, c in cuts.items():
            rec[f"temporal {t0}"] = run(ix, store, c["ids"], t0, c["label"], traces, t0)
        out[name] = rec
        m = rec["pool_proxy (circular)"]; t = rec["temporal 2026-05-15"]; v = rec["S-VAL proxy (circular)"]
        print(f"\n{name}")
        print(f"   pool  n={m['n']} <100={m['hit_100m']} <250={m['hit_250m']} <500={m['hit_500m']} med={m['median_err_m']} m "
              f"| arms {m['arm_mix']}")
        print(f"   S-VAL n={v['n']} <100={v['hit_100m']} <250={v['hit_250m']} <500={v['hit_500m']} med={v['median_err_m']} m")
        print(f"   T0=05-15 n={t['n']} <100={t['hit_100m']} <250={t['hit_250m']} <500={t['hit_500m']} med={t['median_err_m']} m "
              f"| arms {t['arm_mix']}")
    # ── paired grouped bootstrap, every challenger vs P0, on the temporal cut ────────────────────
    print("\npaired vs P0 (grouped by place block, 10,000 resamples):")
    base = out["P0 shipped"]
    for name, rec in out.items():
        if name == "P0 shipped":
            continue
        for pop in ("pool_proxy (circular)", "temporal 2026-05-15", "temporal 2026-05-01"):
            a = rec[pop]["picks"]; b = base[pop]["picks"]
            common = sorted(set(a) & set(b))
            va = [1.0 if a[i]["err"] <= 500 else 0.0 for i in common]
            vb = [1.0 if b[i]["err"] <= 500 else 0.0 for i in common]
            gr = [ix.block_of(i) for i in common]
            d = stats.paired_grouped_ci(va, vb, gr, stat="mean", resamples=10000, seed=7,
                                        direction="higher_is_better")
            rev = stats.paired_grouped_ci(vb, va, gr, stat="mean", resamples=10000, seed=7,
                                          direction="higher_is_better")
            reading = ("identical" if all(abs(x - y) < 1e-12 for x, y in zip(va, vb))
                       else ("P0 better" if rev.get("resolved") else
                             ("challenger better" if d.get("resolved") else "not resolved")))
            rec.setdefault("paired", {})[pop] = {**{k: d.get(k) for k in ("point_delta", "lo", "hi", "n", "n_groups")},
                                                 "reading": reading}
            print(f"  {name[:42]:44s} {pop:26s} {d.get('point_delta'):+.4f} "
                  f"[{d.get('lo'):+.4f}, {d.get('hi'):+.4f}] {reading}")
    return out


if __name__ == "__main__":
    import json
    res = main()
    with open("/tmp/po/policy_raw.json", "w") as fh:
        json.dump({k: {kk: {kkk: vvv for kkk, vvv in vv.items() if kkk != "picks"}
                       for kk, vv in v.items() if kk != "picks"} if False else
                   {kk: (vv if kk != "picks" else "omitted") for kk, vv in v.items()}
                   for k, v in res.items()}, fh, indent=1, default=str)
    print("\nraw -> /tmp/po/policy_raw.json")
