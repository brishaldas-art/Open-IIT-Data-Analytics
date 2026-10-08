"""Historical replay and candidate metrics (contract §3, §15 T15).

* `replay(cutpoints)` is a **simulation**: forward-only, prequential, no peeking. It answers "what did
  the system know at each cut-point, and what changed between them" — the machinery experiment J uses.
* `candidate_metrics(split)` is the only place metrics are produced, and it refuses to run without a
  declared `SplitSpec` (T15). Reading surveyed truth is allowed **only** through the S_EVAL_BASELINE
  spec, and every such read increments the test-look counter.

Labels come from exactly one of two sources, and the report always names which:
* `surveyed_ground_truth` — the 100 surveyed addresses (S-Eval);
* `operational_confirmation_proxy` — the independently-confirmed field position (a *proxy* label, never
  called ground truth).
"""
from __future__ import annotations

import csv
import os

from . import asof, config, dataio, geo, splits
from .belief import compute_belief
from .candidates import generate
from .indexes import get_index
from .ranking import features_matrix, rank
from .version import PROTOCOL_VERSION, RULE_VERSION

MANIFEST = "supervision_manifest.csv"


def _manifest(ix) -> dict[str, dict]:
    path = os.path.join(config.DERIVED, MANIFEST)
    if not os.path.exists(path):
        raise FileNotFoundError("run tools/build_supervision.py first (supervision_manifest.csv missing)")
    with open(path, encoding="utf-8", newline="") as fh:
        return {r["address_id"]: r for r in csv.DictReader(fh)}


def _proxy_truth(store, address_id: str, as_of) -> tuple[float, float] | None:
    """The independently-confirmed field position — a proxy label, never ground truth."""
    obs = asof.observations_upto(store, as_of, address_id=address_id)
    if not obs:
        return None
    ev = store.evidence_for([o["observation_id"] for o in obs])
    xs, ys = [], []
    for o in obs:
        e = ev.get(o["observation_id"])
        if not e or e["polarity"] != "positive" or float(e["weight"]) < config.W_PROMOTE:
            continue
        if o.get("x") is None or o.get("duplicate_claim_of"):
            continue
        xs.append(o["x"]); ys.append(o["y"])
    if len(xs) < 2:
        return None
    return geo.median(xs), geo.median(ys)


def _q(values: list[float], p: float) -> float | None:
    """Linear-interpolated quantile — the pandas/numpy convention used by every quoted figure."""
    import math
    if not values:
        return None
    vs = sorted(values)
    if len(vs) == 1:
        return round(vs[0], 1)
    pos = p * (len(vs) - 1)
    lo, hi = math.floor(pos), math.ceil(pos)
    return round(vs[lo] + (vs[hi] - vs[lo]) * (pos - lo), 1)


def candidate_metrics(spec, *, store=None, ix=None, path: str | None = None) -> dict:
    """Per-arm metrics under a declared split. `spec` may be a SplitSpec or its dict form."""
    spec = splits.require_declared(spec, path=path)
    ix = ix or get_index()
    if store is None:
        from .store import Store
        store = Store()
    manifest = _manifest(ix)

    as_of = spec.as_of
    surveyed = dataio.surveyed()
    label_source = spec.label_source
    if label_source == "surveyed_ground_truth":
        store.bump_counter("s_eval_looks", detail=f"{spec.spec_id}|n={sum(1 for m in manifest.values() if m['split'] == splits.S_EVAL)}")

    rows = []
    for aid, m in sorted(manifest.items()):
        if m["split"] not in spec.populations:
            continue
        if spec.outer_fold is not None and int(m["outer_fold"]) != spec.outer_fold:
            continue
        addr = ix.addresses.get(aid)
        if not addr:
            continue
        truth = None
        if label_source == "surveyed_ground_truth":
            s = surveyed.get(aid)
            truth = (float(s["surveyed_x"]), float(s["surveyed_y"])) if s else None
        else:
            truth = _proxy_truth(store, aid, as_of)
        if truth is None:
            continue
        cands = generate(aid, as_of, store, ix=ix)
        feats = features_matrix(addr, cands, ix)
        ranked = rank(cands, feats, as_of)
        top = next((c for c in cands if c["candidate_id"] == ranked[0]["candidate_id"]), None) if ranked else None
        rows.append({"address_id": aid, "candidates": cands, "ranked": ranked, "top": top, "truth": truth})

    metrics = {}
    for arm in config.ARMS:
        errs, hits = [], {100: 0, 250: 0, 500: 0}
        n = 0
        for r in rows:
            for c in r["candidates"]:
                if c["arm"] != arm:
                    continue
                if c.get("as_of_valid") and not asof.is_before(c["as_of_valid"], as_of):
                    continue
                d = geo.dist(c["x"], c["y"], *r["truth"])
                errs.append(d)
                n += 1
                for k in hits:
                    if d <= k:
                        hits[k] += 1
        if n:
            metrics[arm] = {"n": n, "median_err_m": _q(errs, 0.5), "p80_err_m": _q(errs, 0.8),
                            "p90_err_m": _q(errs, 0.9), "max_err_m": round(max(errs), 1),
                            "hit_100m": round(hits[100] / n, 4), "hit_250m": round(hits[250] / n, 4),
                            "hit_500m": round(hits[500] / n, 4)}

    top_errs = [geo.dist(r["top"]["x"], r["top"]["y"], *r["truth"]) for r in rows if r["top"]]
    report = {
        "spec": spec.to_json(),
        "protocol_version": PROTOCOL_VERSION,
        "rule_version": RULE_VERSION,
        "label_source": label_source,
        "n_addresses_evaluated": len(rows),
        "arms": metrics,
        "system_top_ranked": {"n": len(top_errs), "median_err_m": _q(top_errs, 0.5),
                              "p80_err_m": _q(top_errs, 0.8),
                              "hit_100m": round(sum(1 for e in top_errs if e <= 100) / len(top_errs), 4)
                              if top_errs else None,
                              "hit_250m": round(sum(1 for e in top_errs if e <= 250) / len(top_errs), 4)
                              if top_errs else None},
        "test_look_counter": store.counters("s_eval_looks"),
        "notes": ["labels come from the split's declared label_source only",
                  "no model was fitted; the rule priority is the shipped ranker (D42)",
                  "the test-look counter increments on every S-Eval read and is reported per experiment"],
    }
    return report


def replay(cutpoints: list, *, spec, store=None, ix=None) -> dict:
    """Forward-only simulation over cut-points (experiment J machinery). Requires a declared split."""
    spec = splits.require_declared(spec)
    ix = ix or get_index()
    if store is None:
        from .store import Store
        store = Store()
    manifest = _manifest(ix)
    population = [a for a, m in sorted(manifest.items()) if m["split"] in spec.populations]

    steps = []
    prev_state: dict[str, tuple] = {}
    for t in cutpoints:
        tiers, statuses, radii = {}, {}, []
        changed = []
        for aid in population:
            try:
                b = compute_belief(aid, t, store, ix=ix)
            except KeyError:
                continue
            tiers[b["tier"]] = tiers.get(b["tier"], 0) + 1
            statuses[b["status"]] = statuses.get(b["status"], 0) + 1
            if b["radius"]["radius_m"]:
                radii.append(b["radius"]["radius_m"])
            cur = (b["tier"], b["status"], b["candidate_id"])
            if aid in prev_state and prev_state[aid] != cur:
                changed.append({"address_id": aid, "from": prev_state[aid], "to": cur})
            prev_state[aid] = cur
        steps.append({"cutpoint": asof.to_utc_str(t), "n_addresses": len(population),
                      "tier_histogram": tiers, "status_histogram": statuses,
                      "median_radius_m": _q(radii, 0.5), "n_changed_since_previous": len(changed),
                      "changes_sample": changed[:5]})
    return {"spec": spec.to_json(), "steps": steps, "n_steps": len(steps),
            "simulation": True,
            "notes": ["forward-only: each step reads the store strictly before its cut-point",
                      "no tuning, no fitting, no S-Eval truth read"]}
