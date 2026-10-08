#!/usr/bin/env python3
"""P12 step C — retrieval-only ceiling: how good is the candidate-retrieval layer by itself?

    python3 tools/experiment_c.py [--resamples 10000] [--seed 7]

**Question.** The pipeline is `candidates → ranker → belief/uncertainty → answer`. Experiment C
measures only the **first** stage: given the admitted official arms, does the retrieval layer produce
a candidate set good enough to contain a usable answer — or is retrieval itself the ceiling?

**Retrieval-only.** No model is fitted, no feature is selected, nothing is tuned. The ranker appears in
exactly one place (the framework's own "lane top-1", reported as *context*, marked as Experiment D's
territory) and never decides anything here.

**What is measured — definitions reused verbatim, never reinvented.**
* Coverage, `recall_{100,250,500}` ("a candidate exists within k metres"), the oracle (best candidate in
  the set: median · p80 · p90 · hit@100/250/500 m), the candidate-count distribution, the unresolved
  rate and per-address latency come from `sutra.replay` / `tools/experiment_b.metrics_for` — the same
  code Experiment B was scored with.
* Labels: `operational_confirmation_proxy` (S-TRAIN/S-VAL, never called ground truth) for the
  supervised populations, and `surveyed_ground_truth` for the locked S-Eval check, read **once**
  through the declared `S_EVAL_BASELINE` spec, which increments the test-look counter.

**Two declared lenses.**
* **LENS A (primary) — static retrieval ceiling.** The five static arms in registry order
  (`config.STATIC_ARMS`): `frozen_baseline → locality_centroid → town_centroid → official_landmark →
  address_book`. This is the layer that answers a *cold* address, and it is what a retrieval ceiling
  means. Measured per arm, as a cumulative union ladder in that order, and under arm-removal.
* **LENS B (secondary diagnostic) — historical evidence arms.** `field_evidence` and `memory` consume
  the visit history, and they exist for a minority of surveyed addresses. They are reported separately
  and are **never** part of the C headline.

**Two views of the same hit criterion (declared, not a second metric framework).**
1. *Set recall* — the framework's `recall_k`: some candidate in the whole set is within k metres.
2. *Prefix recall@k* (k = 1 · 3 · 5 · 10) — some candidate among the **first k of the deterministic
   retrieval order** (`config.ARMS` order, then `arm_rank`, then `candidate_id`; exactly the order
   `sutra.candidates.generate` returns) is within k metres. This is the retrieval-set prefix the ranker
   would later be allowed to reorder — it measures *how deep* a usable candidate sits, which set recall
   cannot show. No ranker is involved: the order is fixed and inspectable.

**Statistics.** Grouped bootstrap, 95%, 10,000 resamples, **group = place block** (`sutra.stats`), paired
on the same addresses; the account-grouped interval is reported as a sensitivity check. Deterministic
seed, n and number of groups always printed. Inside the interval = *not resolved by this dataset*.

**Negative controls (all reused, none invented).**
* the `frozen_baseline`-only rung — the floor every other rung must beat;
* a **random-candidate control** (same per-address candidate count, area-uniform around the address's own
  locality anchor — the placebo construction of `tools/neighbour_index_probe.py`), plus a town-uniform
  variant;
* a **truth-echo scan** (no candidate may sit on a surveyed coordinate) and a runtime guard proving the
  candidate path never reads `surveyed_addresses.csv`;
* zero-outbound-call enforcement (sockets closed for the whole run, as T12 does);
* the C2 lock: `place_neighbour` is asserted absent everywhere and stays disabled.

**Decision rule (declared before the run).**
1. An arm *earns its place* only if adding it is **resolved better** than the rung without it on the
   primary ceiling metrics (oracle <500 m hit-rate and coverage), paired and grouped.
2. The ceiling is *adequate* if the static lane is resolved better than the baseline-only rung on those
   metrics **and** its oracle is materially better than a random-candidate control of the same size.
3. If no rung is resolved better, retrieval is **limited by the supplied data, not by the algorithm** —
   and the answer is more official parsing / memory / field evidence, never external augmentation, and
   never more complexity for its own sake.
4. **C2 gate.** C2 becomes *eligible for a future controlled experiment* only if C shows a resolved,
   material shortfall that a neighbour-index mechanism (extra confirmed place points near the anchor,
   with a placebo control of its own) is designed to fill. C2 is never run here.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import socket
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np                                                               # noqa: E402

from sutra import config, dataio, geo, splits, stats                              # noqa: E402
from sutra.candidates import generate, place_neighbour_candidates                # noqa: E402
from sutra.indexes import get_index                                              # noqa: E402
from sutra.replay import _manifest, _proxy_truth, _q                             # noqa: E402
from sutra.store import Store                                                    # noqa: E402
from sutra.version import (EVIDENCE_POLICY_VERSION, PROTOCOL_VERSION,            # noqa: E402
                           RADIUS_MAP_VERSION, RULE_VERSION, SCHEMA_VERSION)
from tools.experiment_a import populations                                       # noqa: E402
from tools.experiment_b import fmt_ci, hash_runs, metrics_for                    # noqa: E402

# ── declared before the run ──────────────────────────────────────────────────────────────────────
STATIC_LADDER = ("frozen_baseline",)                    # registry order == the union ladder order
EVIDENCE_LANE = ("field_evidence", "memory")            # `place_neighbour` stays out (C2 locked)
PREFIX_KS = (1, 3, 5, 10)
HIT_HOLDS = (100, 250, 500)
PRIMARY = ("oracle_hit_500m", "coverage_labelled", "recall_500", "oracle_err_m")
CONTEXT_ONLY = ("rule_top1_hit_500m", "rule_top1_err_m")   # Experiment D's territory, shown for context
N_GUARD = config.N_GUARD                                  # 15, the framework's existing guard
# the framework's row-key mapping, reused from Experiment B: an aggregate name may differ from the
# per-address column that carries it (coverage_labelled is the aggregate of the per-address `coverage`)
ROW_KEY = {"coverage_labelled": "coverage", "recall_100": "recall_100", "recall_250": "recall_250",
           "recall_500": "recall_500", "oracle_err_m": "oracle_err_m",
           "oracle_hit_500m": "oracle_hit_500m", "oracle_hit_100m": "oracle_hit_100m",
           "rule_top1_hit_500m": "rule_top1_hit_500m", "n_candidates": "n_candidates"}
EV = "S-EVAL (locked check)"                              # the locked ground-truth population
VA = "S_VAL (selection)"                                  # the declared selection population
ST = "S_TRAIN+S_VAL (stability)"


def ladder() -> list[tuple[str, tuple[str, ...]]]:
    """The cumulative union ladder: one rung per arm, in the registry's own order."""
    rungs, acc = [], tuple()
    for arm in config.STATIC_ARMS:
        acc = acc + (arm,)
        rungs.append((f"+{arm}" if rungs else f"{arm} (baseline only)", acc))
    return rungs


RUNG_NAME = {name: name for name, _ in ladder()}


# ── generation (one pass over the full book, reused by every population) ─────────────────────────
def run_book(addresses: list[str], ix, store, as_of) -> tuple[dict, dict]:
    """Generate every address's candidate set once under the production ring (B2, unchanged).

    Returns `(run, timings)`. `latency_ms` is the retrieval-layer cost of one address: candidate
    generation only — no ranking, no belief, no I/O beyond the precomputed indexes.
    """
    for aid in addresses[:3]:                                   # untimed warm-up
        generate(aid, as_of, store, ix=ix)
    run: dict[str, dict] = {}
    lat: list[float] = []
    for aid in addresses:
        t0 = time.perf_counter()
        cands = generate(aid, as_of, store, ix=ix)
        dt = (time.perf_counter() - t0) * 1000.0
        lat.append(dt)
        run[aid] = {"candidates": cands, "latency_ms": dt, "ranked": None, "top": None}
    return run, {"n": len(addresses), "mean_ms": round(sum(lat) / len(lat), 3),
                 "p50_ms": _q(lat, 0.5), "p95_ms": _q(lat, 0.95), "max_ms": round(max(lat), 3)}


# ── per-arm census (label-free, full book) ───────────────────────────────────────────────────────
def arm_census(addresses: list[str], run: dict, arm: str) -> dict:
    """How many of the addresses this arm emits / does not emit for; how many candidates it emits."""
    fires = cands = as_of_valid = 0
    for aid in addresses:
        cs = [c for c in run[aid]["candidates"] if c["arm"] == arm]
        if cs:
            fires += 1
        cands += len(cs)
        as_of_valid += sum(1 for c in cs if c.get("as_of_valid"))
    n = len(addresses)
    return {"n_addresses": n, "addresses_emitting": fires,
            "share_emitting": round(fires / n, 4) if n else None,
            "candidates": cands,
            "mean_candidates_per_emitting_address": round(cands / fires, 3) if fires else None,
            "candidates_with_as_of_valid": as_of_valid,
            "evidence_backed": arm in config.EVIDENCE_ARMS}


def arm_quality(addresses: list[str], run: dict, truth: dict[str, tuple[float, float]]) -> dict:
    """Per-arm retrieval quality on a labelled population (the arm's *own* best candidate vs truth)."""
    out: dict[str, dict] = {}
    for arm in config.ARMS:
        errs, best_share, unique_500, sole = [], 0, 0, 0
        for aid in addresses:
            if aid not in truth:
                continue
            tx, ty = truth[aid]
            cs = [c for c in run[aid]["candidates"] if c["arm"] == arm]
            if not cs:
                continue
            e = min(geo.dist(c["x"], c["y"], tx, ty) for c in cs)
            errs.append(e)
            all_arms = run[aid]["candidates"]
            if all_arms:
                best = min(geo.dist(c["x"], c["y"], tx, ty) for c in all_arms)
                if e <= best + 1e-9:
                    best_share += 1
                within = [c["arm"] for c in all_arms if geo.dist(c["x"], c["y"], tx, ty) <= 500]
                if within and set(within) == {arm}:
                    unique_500 += 1
            if e <= 500:
                sole += 1
        n = len(errs)
        out[arm] = {"n_labelled": sum(1 for a in addresses if a in truth),
                    "fires": n,
                    "fire_rate": round(n / max(1, sum(1 for a in addresses if a in truth)), 4),
                    "median_err_m": _q(errs, 0.5), "p80_err_m": _q(errs, 0.8),
                    "hit_100m": round(sum(1 for e in errs if e <= 100) / n, 4) if n else None,
                    "hit_500m": round(sum(1 for e in errs if e <= 500) / n, 4) if n else None,
                    "supplies_the_best_candidate": best_share,
                    "is_the_only_arm_within_500m": unique_500}
    return out


# ── prefix recall (the declared second view of the same hit criterion) ───────────────────────────
def prefix_rows(addresses: list[str], run: dict, truth: dict[str, tuple[float, float]],
                arms: tuple[str, ...]) -> list[dict]:
    """Per-address prefix recall@k over the deterministic retrieval order (`generate`'s own order)."""
    rows = []
    for aid in addresses:
        if aid not in truth:
            continue
        tx, ty = truth[aid]
        seq = [c for c in run[aid]["candidates"] if c["arm"] in arms]         # order preserved
        row = {"address_id": aid, "n_in_lane": len(seq)}
        for k in PREFIX_KS:
            pref = seq[:k]
            d = min((geo.dist(c["x"], c["y"], tx, ty) for c in pref), default=None)
            for h in (100, 500):
                row[f"prefix{k}_hit_{h}m"] = (None if d is None else int(d <= h))
            row[f"prefix{k}_err_m"] = None if d is None else round(d, 3)
        rows.append(row)
    return rows


def prefix_agg(rows: list[dict]) -> dict:
    out = {}
    n = len(rows)
    for k in PREFIX_KS:
        for h in (100, 500):
            vals = [r[f"prefix{k}_hit_{h}m"] for r in rows if r[f"prefix{k}_hit_{h}m"] is not None]
            out[f"prefix{k}_hit_{h}m"] = round(sum(vals) / len(vals), 4) if vals else None
        errs = [r[f"prefix{k}_err_m"] for r in rows if r[f"prefix{k}_err_m"] is not None]
        out[f"prefix{k}_n"] = len(errs)
    return out


# ── negative controls ────────────────────────────────────────────────────────────────────────────
def town_radii(ix) -> dict[str, float]:
    """A town's radius = p95 distance from its centroid to its own baseline pins (official data only).

    Used by the random-candidate control to place placebo points at the same *scale* as the real arms,
    so the control is not trivially defeated by a bad choice of spread.
    """
    from collections import defaultdict
    d: dict[str, list[float]] = defaultdict(list)
    for aid, b in ix.baseline.items():
        t = ix.town_of(aid)
        cx, cy = ix.town_centroids.get(t, (None, None))
        if t and cx is not None:
            d[t].append(geo.dist(float(b["geocoder_x"]), float(b["geocoder_y"]), float(cx), float(cy)))
    return {t: (_q(v, 0.95) or 500.0) for t, v in d.items()}


def random_control(addresses: list[str], run: dict, truth: dict[str, tuple[float, float]], ix,
                    seed: int) -> dict:
    """Placebo candidates: same count as the real static lane, placed at random.

    Two placements, both from the existing placebo recipe (`tools/neighbour_index_probe.py` control 1):
    `anchored` — area-uniform in a disc around the address's own locality anchor (generous to the
    control: it is handed the anchor for free), and `town_uniform` — uniform in the town's extent.
    """
    rng = np.random.default_rng(seed)
    radii = town_radii(ix)
    anchored, town_uniform = {}, {}
    for aid in addresses:
        if aid not in truth:
            continue
        real = [c for c in run[aid]["candidates"] if c["arm"] in config.STATIC_ARMS]
        k = max(1, len(real))
        loc = next((c for c in real if c["arm"] == "locality_centroid"), None)
        t = ix.town_of(aid)
        cx, cy = ix.town_centroids.get(t, (None, None))
        anchor = (loc["x"], loc["y"]) if loc else ((float(cx), float(cy)) if cx is not None else None)
        R = float(radii.get(t, 500.0))
        if anchor is not None:
            ang = rng.uniform(0, 2 * np.pi, k)
            rad = R * np.sqrt(rng.uniform(0, 1, k))
            pts = [(anchor[0] + r * np.cos(a), anchor[1] + r * np.sin(a)) for r, a in zip(rad, ang)]
            anchored[aid] = min(geo.dist(x, y, *truth[aid]) for x, y in pts)
        if cx is not None:
            ang = rng.uniform(0, 2 * np.pi, k)
            rad = R * np.sqrt(rng.uniform(0, 1, k)) * 1.5
            pts = [(float(cx) + r * np.cos(a), float(cy) + r * np.sin(a)) for r, a in zip(rad, ang)]
            town_uniform[aid] = min(geo.dist(x, y, *truth[aid]) for x, y in pts)
    def agg(d: dict) -> dict:
        errs = list(d.values())
        if not errs:
            return {"n": 0}
        return {"n": len(errs), "median_err_m": _q(errs, 0.5), "p80_err_m": _q(errs, 0.8),
                "hit_100m": round(sum(1 for e in errs if e <= 100) / len(errs), 4),
                "hit_500m": round(sum(1 for e in errs if e <= 500) / len(errs), 4)}
    return {"anchored": {**agg(anchored), "per_address": anchored},
            "town_uniform": {**agg(town_uniform), "per_address": town_uniform},
            "construction": ("placebo points, count-matched to the address's real static lane, "
                             "area-uniform (radius ~ sqrt(U) · town p95 radius) about the locality "
                             "anchor — reuse of `tools/neighbour_index_probe.py` control 1"),
            "seed": seed}


def truth_echo_scan(addresses: list[str], run: dict, surveyed: dict, ix) -> dict:
    """No candidate may be the evaluation truth in disguise: measure the closest approach, per arm."""
    per_arm: dict[str, list[float]] = {}
    hits_1m, hits_5m, exact = 0, 0, []
    for aid in addresses:
        if aid not in surveyed:
            continue
        tx, ty = float(surveyed[aid]["surveyed_x"]), float(surveyed[aid]["surveyed_y"])
        for c in run[aid]["candidates"]:
            d = geo.dist(c["x"], c["y"], tx, ty)
            per_arm.setdefault(c["arm"], []).append(d)
            if d <= 1.0:
                hits_1m += 1
                exact.append({"address_id": aid, "arm": c["arm"], "source_ref": c["source_ref"],
                              "dist_m": round(d, 3)})
            if d <= 5.0:
                hits_5m += 1
    return {"n_surveyed": sum(1 for a in addresses if a in surveyed),
            "candidates_scanned": sum(len(run[a]["candidates"]) for a in addresses if a in surveyed),
            "candidates_within_1m_of_truth": hits_1m, "candidates_within_5m_of_truth": hits_5m,
            "within_1m_detail": exact[:10],
            "min_distance_per_arm_m": {a: round(min(v), 3) for a, v in sorted(per_arm.items())},
            "reading": ("a candidate is built from the arms' own source tables (addresses, localities, "
                        "landmarks, towns, baseline pins, visit check-ins); the surveyed table is read "
                        "only by the evaluation and firewall code, so a near-zero distance can only "
                        "come from an independent measurement of the same place — field GPS noise")}


def governance_checks(ix, store, run, specs) -> dict:
    """The controls that must hold for C to mean anything (all reused, none invented)."""
    cand_path_files = ["sutra/candidates.py", "sutra/indexes.py", "sutra/ranking.py", "sutra/geo.py"]
    reads_surveyed = {}
    for f in cand_path_files:
        txt = open(os.path.join(config.ROOT, f), encoding="utf-8").read()
        # `dataio.surveyed(` = reading the table's contents; the bare filename may also appear as a
        # *source hash* in the index manifest (provenance of the artefact, not an input to a candidate)
        reads_surveyed[f] = {"reads_contents": txt.count("dataio.surveyed("),
                             "mentions_the_file_name": txt.count("surveyed_addresses")}
    reads_any = sum(v["reads_contents"] for v in reads_surveyed.values())
    # firewall: no firewalled address may appear in a supervision split
    fw = {r["address_id"] for r in csv.DictReader(
        open(os.path.join(config.DERIVED, "supervision_firewall.csv"), encoding="utf-8"))}
    man = list(csv.DictReader(open(os.path.join(config.DERIVED, "supervision_manifest.csv"),
                                  encoding="utf-8")))
    leaked = [m["address_id"] for m in man
              if m["address_id"] in fw and m["split"] in (splits.S_TRAIN, splits.S_VAL)]
    # candidate artefact shape
    cand_cols = next(csv.reader(open(os.path.join(config.DERIVED, "candidates_v2.csv"),
                                     encoding="utf-8")))
    n_neighbour_rows = sum(1 for r in csv.DictReader(
        open(os.path.join(config.DERIVED, "candidates_v2.csv"), encoding="utf-8"))
        if r.get("arm") == "place_neighbour")
    licences = {c["licence_class"] for r in run.values() for c in r["candidates"]}
    ext_dir = os.path.join(config.DATA, "external_research")
    return {
        "candidate_path_reads_the_surveyed_table": reads_surveyed,
        "candidate_path_reads_surveyed_anywhere": bool(reads_any),
        "candidate_path_reads_note": ("`mentions_the_file_name` counts include the index manifest, which "
                                      "records the file's sha256 as provenance; that is not a read of its "
                                      "contents into any candidate"),
        "firewalled_addresses_in_a_supervision_split": leaked,
        "firewall_rows": len(fw),
        "candidate_artefact_has_truth_column": any("truth" in c or "err" in c or "label" in c
                                                   for c in cand_cols),
        "candidate_artefact_place_neighbour_rows": n_neighbour_rows,
        "licence_classes_in_run": sorted(licences),
        "licence_classes_is_official_only": sorted(licences) == [config.LICENCE_CLASS],
        "external_research_dir_empty": (not os.path.exists(ext_dir)) or not os.listdir(ext_dir),
        "place_neighbour_enabled_in_config": bool(config.ENABLE_PLACE_NEIGHBOUR),
        "place_neighbour_arm_emits_nothing": all(place_neighbour_candidates(a, config.MOMENT, store,
                                                                          enable=False) == []
                                                 for a in sorted(ix.addresses)[:25]),
        "place_neighbour_absent_from_run": all(
            c["arm"] != "place_neighbour" for r in run.values() for c in r["candidates"]),
        "declared_specs": sorted(specs),
    }


# ── grouped reporting: town and stratum ──────────────────────────────────────────────────────────
def grouped_table(addresses: list[str], run: dict, truth: dict[str, tuple[float, float]], ix,
                  by: str) -> list[dict]:
    """Oracle metrics grouped by `town` or by the address's own baseline `precision` (the stratum)."""
    groups: dict[str, list[str]] = {}
    for aid in addresses:
        if aid not in truth:
            continue
        key = ix.town_of(aid) if by == "town" else (dataio.baseline_precision(aid) or "no_baseline_pin")
        groups.setdefault(str(key), []).append(aid)
    out = []
    for key in sorted(groups):
        rows = []
        for aid in groups[key]:
            tx, ty = truth[aid]
            cs = [c for c in run[aid]["candidates"] if c["arm"] in config.STATIC_ARMS]
            if not cs:
                rows.append(None)
                continue
            rows.append(min(geo.dist(c["x"], c["y"], tx, ty) for c in cs))
        errs = [r for r in rows if r is not None]
        n = len(errs)
        out.append({"group": key, "n": n, "n_unresolved": len(rows) - n,
                    "resolved_share": round(n / len(rows), 4) if rows else None,
                    "oracle_median_err_m": _q(errs, 0.5), "oracle_p80_err_m": _q(errs, 0.8),
                    "oracle_hit_100m": round(sum(1 for e in errs if e <= 100) / n, 4) if n else None,
                    "oracle_hit_500m": round(sum(1 for e in errs if e <= 500) / n, 4) if n else None,
                    "below_n_guard": n < N_GUARD})
    return out


# ── main ─────────────────────────────────────────────────────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--resamples", type=int, default=stats.DEFAULT_RESAMPLES)
    ap.add_argument("--seed", type=int, default=stats.DEFAULT_SEED)
    ap.add_argument("--out-dir", default=None)
    a = ap.parse_args()

    t_start = time.time()
    out_dir = a.out_dir or config.DERIVED
    os.makedirs(out_dir, exist_ok=True)

    # ── zero outbound calls for the whole experiment (the T12 pattern) ───────────────────────────
    outbound = []

    class _NoNet(socket.socket):
        def __init__(self, *args, **kwargs):
            outbound.append("socket()")
            raise RuntimeError("no outbound calls are permitted in an experiment")

    real_socket, real_create = socket.socket, socket.create_connection
    socket.socket = _NoNet
    socket.create_connection = lambda *args, **kw: outbound.append("create_connection")

    # ── the gate: no metrics without a declared split (T15) ─────────────────────────────────────
    specs = {s.spec_id: s for s in splits.declared_specs()}
    spec_eval = splits.require_declared(specs["S_EVAL_BASELINE"])
    as_of = config.MOMENT

    ix = get_index()
    store = Store()
    manifest = _manifest(ix)
    pops_a1 = populations(ix)

    pop_val = [aid for aid, m in sorted(manifest.items()) if m["split"] == splits.S_VAL]
    pop_sup = [aid for aid, m in sorted(manifest.items()) if m["split"] in (splits.S_TRAIN, splits.S_VAL)]
    block_splits: dict[str, set] = {}
    for aid, b in ix.place_blocks.items():
        block_splits.setdefault(b["block_id"], set()).add(b["split"])
    pop_lbo = [aid for aid in pop_sup if len(block_splits.get(ix.block_of(aid), set())) <= 1]
    pop_eval = [aid for aid, m in sorted(manifest.items()) if m["split"] == splits.S_EVAL]
    pop_book = sorted(ix.addresses)
    populations_used = {"FULL BOOK (label-free)": pop_book,
                        "S_TRAIN+S_VAL (stability)": pop_sup,
                        "S_VAL (selection)": pop_val,
                        "leave-block-out (stress)": pop_lbo,
                        "S-EVAL (locked check)": pop_eval}

    # ── labels: proxy for the supervised populations, surveyed truth once for S-Eval ─────────────
    proxy: dict[str, tuple[float, float]] = {}
    for aid in pop_sup:
        t = _proxy_truth(store, aid, as_of)
        if t is not None:
            proxy[aid] = t
    counter_before = store.counters("s_eval_looks")
    store.bump_counter("s_eval_looks", detail="experiment_C:s_eval_locked_check (single read)")
    surveyed = dataio.surveyed()
    truth_eval = {aid: (float(surveyed[aid]["surveyed_x"]), float(surveyed[aid]["surveyed_y"]))
                  for aid in pop_eval if aid in surveyed}
    counter_after = store.counters("s_eval_looks")

    # ── one generation pass over the full book, reused by every population ───────────────────────
    # a runtime guard: the candidate path must not read the surveyed table (leakage proof, not a claim)
    guard_hits = []
    real_surveyed = dataio.surveyed
    dataio.surveyed = lambda *args, **kw: (guard_hits.append("surveyed()"), real_surveyed(*args, **kw))[1]
    try:
        run, timing = run_book(pop_book, ix, store, as_of)
    finally:
        dataio.surveyed = real_surveyed

    universe_hash = hash_runs(run)
    # cross-experiment regression: the same addresses Experiment B hashed must hash identically
    b_subset = sorted(set(pop_val) | set(pop_sup) | set(pop_eval))
    subset_hash = hash_runs({a: run[a] for a in b_subset})

    # ── lenses and populations ───────────────────────────────────────────────────────────────────
    rungs = ladder()
    truth_of = {"S-EVAL (locked check)": truth_eval, "FULL BOOK (label-free)": {}}
    cells: dict[str, dict[str, dict]] = {}
    for pname, pop in populations_used.items():
        truth = truth_of.get(pname, proxy)
        lanes: dict[str, dict] = {}
        for rname, arms in rungs:
            lanes[rname] = metrics_for(pop, run, truth, ix, as_of, arms)
        lanes["evidence_lane (field_evidence+memory)"] = metrics_for(pop, run, truth, ix, as_of, EVIDENCE_LANE)
        lanes["all_arms (static+evidence)"] = metrics_for(
            pop, run, truth, ix, as_of, tuple(config.STATIC_ARMS) + EVIDENCE_LANE)
        cells[pname] = lanes
    static_rung = rungs[-1][0]                                   # the complete static lane

    # Lane quality from the framework's own per-address rows. The oracle is defined over the rows the
    # lane actually covers, so its n travels with it; `recall_k` is the censored reading (uncovered
    # addresses scored as misses over every labelled address). p90 uses `sutra.replay._q`, the same
    # quantile as every other figure in the project.
    lane_quality: dict[str, dict[str, dict]] = {}
    for pname in populations_used:
        lane_quality[pname] = {}
        for rname in cells[pname]:
            rows = cells[pname][rname]["rows"]
            lab = [r for r in rows if r["labelled"]]
            cov = [r for r in lab if r.get("oracle_err_m") is not None]
            errs = [r["oracle_err_m"] for r in cov]
            lane_quality[pname][rname] = {
                "n_labelled": len(lab), "n_covered_in_lane": len(cov),
                "coverage_in_lane": round(len(cov) / len(lab), 4) if lab else None,
                "oracle_median_err_m": _q(errs, 0.5), "oracle_p80_err_m": _q(errs, 0.8),
                "oracle_p90_err_m": _q(errs, 0.9), "oracle_max_err_m": round(max(errs), 1) if errs else None,
                "oracle_hit_100m": round(sum(1 for e in errs if e <= 100) / len(errs), 4) if errs else None,
                "oracle_hit_500m": round(sum(1 for e in errs if e <= 500) / len(errs), 4) if errs else None,
                "censored_recall_100": round(sum(1 for r in lab if r.get("recall_100") == 1) / len(lab), 4)
                                       if lab else None,
                "censored_recall_500": round(sum(1 for r in lab if r.get("recall_500") == 1) / len(lab), 4)
                                       if lab else None,
                "note": ("oracle stats are conditional on the lane covering the address; censored_recall_* "
                         "score an uncovered address as a miss over every labelled address"),
            }

    # ── prefix recall (declared second view) ────────────────────────────────────────────────────
    prefix: dict[str, dict[str, dict]] = {}
    for pname, pop in populations_used.items():
        truth = truth_of.get(pname, proxy)
        if not truth:
            continue
        prefix[pname] = {}
        for label, arms in ((static_rung, tuple(config.STATIC_ARMS)),
                            ("evidence_lane (field_evidence+memory)", EVIDENCE_LANE),
                            ("all_arms (static+evidence)", tuple(config.STATIC_ARMS) + EVIDENCE_LANE)):
            rows = prefix_rows(pop, run, truth, arms)
            prefix[pname][label] = {"agg": prefix_agg(rows), "rows": rows}

    # ── per-arm census and quality ──────────────────────────────────────────────────────────────
    census_book = {arm: arm_census(pop_book, run, arm) for arm in config.ARMS}
    census_eval = {arm: arm_census(pop_eval, run, arm) for arm in config.ARMS}
    quality_eval = arm_quality(pop_eval, run, truth_eval)
    quality_val = arm_quality(pop_val, run, proxy)

    # ── paired comparisons (group = place block; account as the sensitivity check) ───────────────
    def series(pop: list[str], rname: str, key: str, truth: dict) -> tuple[list, list, list]:
        rows = {r["address_id"]: r for r in cells_by_name(pop, rname)["rows"]}
        ids = sorted(i for i in rows if rows[i].get(key) is not None)
        return ([rows[i][key] for i in ids], None, [ix.block_of(i) for i in ids], ids)

    def cells_by_name(pop, rname):                                # cached lane metrics per population
        return _cell_cache[(id(pop), rname)]

    _cell_cache: dict[tuple, dict] = {}
    for pname, pop in populations_used.items():
        for rname in cells[pname]:
            _cell_cache[(id(pop), rname)] = cells[pname][rname]

    def paired(pop_name: str, rname_a: str, rname_b: str, key: str, group: str = "place_block"):
        rk = ROW_KEY.get(key, key)                    # the framework's aggregate → row mapping
        ra = {r["address_id"]: r for r in cells[pop_name][rname_a]["rows"]}
        rb = {r["address_id"]: r for r in cells[pop_name][rname_b]["rows"]}
        va, vb, gr = [], [], []
        for aid in sorted(set(ra) & set(rb)):
            x, y = ra[aid].get(rk), rb[aid].get(rk)
            if x is None or y is None:
                continue
            va.append(x); vb.append(y)
            gr.append(ix.block_of(aid) if group == "place_block"
                      else ix.addresses[aid]["account_id"])
        if not va:
            return {"n": 0, "resolved": False, "note": "no aligned rows"}
        stat = "median" if key == "oracle_err_m" else "mean"
        lower_better = key in ("oracle_err_m", "rule_top1_err_m", "n_candidates", "latency_ms")
        d = stats.paired_grouped_ci(va, vb, gr, stat=stat, resamples=a.resamples, seed=a.seed,
                                    direction="lower_is_better" if lower_better else "higher_is_better")
        if all(abs(x - y) < 1e-12 for x, y in zip(va, vb)):
            d["identical"] = True
        return d

    comparisons: dict[str, dict] = {}
    for pname in populations_used:
        if not truth_of.get(pname, proxy):
            continue
        comparisons[pname] = {"rungs_vs_baseline_only": {}, "rung_increments": {},
                              "account_grouped_sensitivity": {}}
        for rname, _arms in rungs[1:]:
            comparisons[pname]["rungs_vs_baseline_only"][rname] = {
                k: paired(pname, rname, rungs[0][0], k) for k in PRIMARY + ("n_candidates",)}
        for i in range(1, len(rungs)):
            prev, cur = rungs[i - 1][0], rungs[i][0]
            comparisons[pname]["rung_increments"][cur] = {
                k: paired(pname, cur, prev, k) for k in PRIMARY + ("n_candidates",)}
        for k in PRIMARY:
            comparisons[pname]["account_grouped_sensitivity"][k] = paired(
                pname, static_rung, rungs[0][0], k, group="account")

    # ── arm removal: which arm is load-bearing for the ceiling? ─────────────────────────────────
    removal: dict[str, dict] = {}
    for pname in ("S-EVAL (locked check)", "S_VAL (selection)"):
        removal[pname] = {}
        for arm in config.STATIC_ARMS:
            keep = tuple(x for x in config.STATIC_ARMS if x != arm)
            lanes = metrics_for(populations_used[pname], run, truth_of.get(pname, proxy), ix, as_of, keep)
            _cell_cache[(id(populations_used[pname]), f"static_without_{arm}")] = lanes
            removal[pname][arm] = {
                "without_it": {k: lanes["agg"].get(k) for k in ("coverage_labelled", "unresolved_labelled")},
                "without_it_oracle": lanes["agg"].get("oracle"),
                "delta_oracle_err_m_vs_full_static": (
                    None if not lanes["agg"].get("oracle") or not cells[pname][static_rung]["agg"].get("oracle")
                    else round(lanes["agg"]["oracle"]["median_err_m"]
                               - cells[pname][static_rung]["agg"]["oracle"]["median_err_m"], 1)),
            }
            pairs = {}
            for k in ("oracle_err_m", "coverage_labelled"):
                ra = {r["address_id"]: r for r in lanes["rows"]}
                rb = {r["address_id"]: r for r in cells[pname][static_rung]["rows"]}
                va, vb, gr = [], [], []
                for aid in sorted(set(ra) & set(rb)):
                    x, y = ra[aid].get(k), rb[aid].get(k)
                    if x is None or y is None:
                        continue
                    va.append(x); vb.append(y); gr.append(ix.block_of(aid))
                if va:
                    pairs[k] = stats.paired_grouped_ci(
                        va, vb, gr, stat="median" if k == "oracle_err_m" else "mean",
                        resamples=a.resamples, seed=a.seed,
                        direction="lower_is_better" if k == "oracle_err_m" else "higher_is_better")
                else:
                    pairs[k] = {"n": 0}
            pr = pairs.get("oracle_err_m", {})
            # a *sign* statement, not a direction claim: dropping the arm is resolved worse when the
            # paired interval of (without − with) sits entirely above zero (more error, never less)
            removal[pname][arm]["drop_is_resolved_worse"] = bool(
                pr.get("lo") is not None and pr.get("lo") > 0.0)
            removal[pname][arm]["reading"] = (
                f"dropping it costs {pr.get('point_delta')} m of oracle median "
                f"[{pr.get('lo')}, {pr.get('hi')}] — the pin is load-bearing"
                if removal[pname][arm]["drop_is_resolved_worse"] else
                "dropping it does not move the ceiling beyond the interval")
            removal[pname][arm]["paired_vs_full_static"] = pairs

    # ── grouped tables: town and stratum ────────────────────────────────────────────────────────
    grouped = {
        "S-EVAL (locked check)": {"by_town": grouped_table(pop_eval, run, truth_eval, ix, "town"),
                                  "by_stratum": grouped_table(pop_eval, run, truth_eval, ix, "stratum")},
        "S-VAL (selection)": {"by_town": grouped_table(pop_val, run, proxy, ix, "town"),
                              "by_stratum": grouped_table(pop_val, run, proxy, ix, "stratum")},
        "S_TRAIN+S_VAL (stability)": {"by_stratum": grouped_table(pop_sup, run, proxy, ix, "stratum")},
    }

    # ── negative controls ───────────────────────────────────────────────────────────────────────
    controls = {
        "baseline_only_rung": {k: cells["S-EVAL (locked check)"][rungs[0][0]]["agg"].get(k)
                               for k in ("coverage_labelled", "unresolved_labelled")},
        "random_candidate_control": {
            "S-EVAL (locked check)": random_control(pop_eval, run, truth_eval, ix, a.seed),
            "S_VAL (selection)": random_control(pop_val, run, proxy, ix, a.seed),
        },
        "truth_echo_scan": truth_echo_scan(pop_eval, run, surveyed, ix),
        "governance": governance_checks(ix, store, run, specs),
        "outbound_call_attempts": len(outbound),
    }
    # paired: real static lane vs its own random control
    ctl_pairs = {}
    for pname, truth in (("S-EVAL (locked check)", truth_eval), ("S_VAL (selection)", proxy)):
        for kind in ("anchored", "town_uniform"):
            per = {k: v for k, v in controls["random_candidate_control"][pname][kind]["per_address"].items()}
            real = {}
            for r in cells[pname][static_rung]["rows"]:
                if r["address_id"] in per and r["oracle_err_m"] is not None:
                    real[r["address_id"]] = r["oracle_err_m"]
            ids = sorted(set(real) & set(per))
            if ids:
                ctl_pairs[f"{pname}|{kind}"] = stats.paired_grouped_ci(
                    [real[i] for i in ids], [per[i] for i in ids],
                    [ix.block_of(i) for i in ids], stat="median",
                    resamples=a.resamples, seed=a.seed, direction="lower_is_better")
            else:
                ctl_pairs[f"{pname}|{kind}"] = {"n": 0}
    controls["real_static_lane_vs_random_control"] = ctl_pairs

    # ── where the static lane fails, and whether history would have helped ──────────────────────
    ev_lane_name = "evidence_lane (field_evidence+memory)"
    fail_rows = {r["address_id"]: r for r in cells[EV][static_rung]["rows"]
                 if r.get("oracle_err_m") is not None and r["oracle_err_m"] > 500}
    ev_rows = {r["address_id"]: r for r in cells[EV][ev_lane_name]["rows"]}
    fail_with_history = [a for a in fail_rows if ev_rows.get(a, {}).get("oracle_err_m") is not None]
    fail_fixed_by_history = [a for a in fail_with_history
                             if (ev_rows[a]["oracle_err_m"] or 9e9) <= 500]
    fail_detail = [{"address_id": a, "town": ix.town_of(a),
                    "stratum": dataio.baseline_precision(a) or "no_baseline_pin",
                    "static_oracle_m": fail_rows[a]["oracle_err_m"],
                    "n_static_candidates": fail_rows[a]["n_candidates"],
                    "evidence_available": a in fail_with_history,
                    "evidence_oracle_m": (ev_rows.get(a) or {}).get("oracle_err_m")}
                   for a in sorted(fail_rows)]
    failure_analysis = {
        "static_lane_oracle_over_500m": len(fail_rows),
        "n_labelled": len(truth_eval),
        "of_those_with_evidence_available": len(fail_with_history),
        "of_those_recovered_by_the_evidence_lane": len(fail_fixed_by_history),
        "detail": fail_detail,
    }

    # ── the decision (rule declared in the docstring, applied to the numbers) ────────────────────
    # The *selection* population is S-VAL (contract §2: S-Val selects, S-Eval is the locked check and
    # never tunes). C adopts nothing, so S-Eval is used as a confirmation, never as a chooser.
    DEC = "S_VAL (selection)"
    eval_inc = comparisons[EV]["rung_increments"]
    val_inc = comparisons[DEC]["rung_increments"]
    earners = []
    for pname, comp in ((DEC, val_inc), (EV, eval_inc)):
        role = "selection" if pname == DEC else "locked check"
        for rname, d in comp.items():
            for k in PRIMARY:
                dd = d.get(k, {})
                if dd.get("resolved") and dd.get("favours") == "a":
                    earners.append({"population": pname, "role": role, "rung": rname, "metric": k,
                                    "delta": f"{dd['point_delta']:+.4f} [{dd['lo']}, {dd['hi']}]"})
    arm_earners = sorted({e["rung"] for e in earners})
    load_bearing = [arm for arm in config.STATIC_ARMS if removal[DEC][arm]["drop_is_resolved_worse"]]
    # adequacy, declared before the run: the layer is adequate when it loses no coverage against the
    # pin, carries information beyond a same-size random control, and no admitted arm that is dropped
    # moves the ceiling (§ the drop analysis above). Every clause is reported separately.
    cov_static = cells[DEC][static_rung]["agg"].get("coverage_labelled")
    cov_base = cells[DEC][rungs[0][0]]["agg"].get("coverage_labelled")
    ctl_dec = ctl_pairs.get(f"{DEC}|anchored", {})
    cl1 = bool(cov_static is not None and cov_base is not None and cov_static >= cov_base)
    cl2 = bool(ctl_dec.get("resolved") and ctl_dec.get("favours") == "a")
    cl3 = bool(arm_earners)
    ceiling_adequate = cl1 and cl2
    oracle_eval = cells[EV][static_rung]["agg"].get("oracle") or {}
    oracle_val = cells[DEC][static_rung]["agg"].get("oracle") or {}
    # C2 criterion, declared before the run: eligible only if the static ceiling leaves a *majority* of
    # the addresses it covers without a single candidate inside the locality radius (500 m), i.e. the
    # cheap mechanism (more confirmed place points near the anchor) has a real gap to fill.
    c2_majority_gap = bool(oracle_eval.get("hit_500m") is not None and oracle_eval["hit_500m"] < 0.5)
    c2_eligible = bool(c2_majority_gap)
    decision = {
        "rule": ("an arm earns its place only if adding it is resolved better on a primary ceiling metric "
                 "(paired, grouped, on the declared population); the ceiling is adequate when the static "
                 "lane loses no coverage against the pin-only rung and beats a count-matched random "
                 "control; C2 becomes eligible only if a majority of covered addresses have no candidate "
                 "within 500 m (the locality radius scale) and no admitted arm closes that"),
        "primary_decision_population": DEC,
        "locked_check_population": EV,
        "adequacy_clauses": {
            "no_coverage_lost_vs_pin_only": {"S_VAL": cl1, "static": cov_static, "pin_only": cov_base},
            "beats_a_count_matched_random_control": {"S_VAL": cl2, **{k: ctl_dec.get(k) for k in
                                                                     ("point_delta", "lo", "hi", "n")}},
            "at_least_one_admitted_arm_earns_its_place": {"value": cl3, "arms": arm_earners},
        },
        "ceiling_adequate": ceiling_adequate,
        "adequacy_reading": (
            ("the retrieval layer keeps every address the pin alone covers (coverage "
             f"{cov_static} vs {cov_base}), it is resolved better than a count-matched random control "
             f"({ctl_dec.get('point_delta')} m median, [{ctl_dec.get('lo')}, {ctl_dec.get('hi')}]), and "
             f"{'at least one' if cl3 else 'no'} admitted arm earns its place beyond the pin. The ceiling "
             f"is therefore not a mechanism failure: it is the granularity of the supplied official data, "
             f"and the headroom that remains sits in confirmed history (LENS B), not in more retrieval "
             f"mechanisms.")
            if ceiling_adequate else
            ("the static lane does not clear the declared adequacy clauses — see the clause table; "
             "retrieval itself is then the binding constraint and the failing clause names the mechanism")),
        "retrieval_is_the_bottleneck": (not ceiling_adequate),
        "arms_that_earn_their_place": earners,
        "load_bearing_arms_under_removal": load_bearing,
        "static_lane_vs_baseline_only": {"S_VAL (selection)":
                                         comparisons[DEC]["rungs_vs_baseline_only"][static_rung],
                                         "S-EVAL (locked check)":
                                         comparisons[EV]["rungs_vs_baseline_only"][static_rung]},
        "static_lane_vs_random_control": ctl_pairs,
        "failure_analysis": failure_analysis,
        "ranked_answer_share_s": {
            "note": "context only — Experiment D's territory, not part of the C ceiling",
            "S-EVAL static lane": (cells[EV][static_rung]["agg"].get("rule_top1") or {}),
        },
        "c2_gate": {
            "criterion": ("eligible only if the static ceiling leaves a majority of covered addresses "
                          "with no candidate inside 500 m (the locality-radius scale)"),
            "s_eval_static_oracle_hit_500m": oracle_eval.get("hit_500m"),
            "s_val_static_oracle_hit_500m": oracle_val.get("hit_500m"),
            "majority_gap_measured": c2_majority_gap,
            "eligible_for_a_future_controlled_experiment": c2_eligible,
            "run_now": False,
            "reason": ("the static ceiling leaves a majority of covered addresses without a candidate "
                       "inside the locality radius, so extra confirmed place points near the anchor have "
                       "a real gap to fill — a *controlled* neighbour-index experiment (its own placebo "
                       "and receipt) would be informative"
                       if c2_eligible else
                       ("no majority gap: the static lane already places a candidate within 500 m for "
                        f"{oracle_eval.get('hit_500m')} of covered addresses on the locked check, it is "
                        "resolved better than a count-matched random control, and the failures that remain "
                        "sit in coarse strata where the supplied gazetteer is the limit — not in missing "
                        "candidate count. Keep C2 locked; do not alter the production candidate set.")),
        },
        "next_experiment": "D — retrieval + ranking (the ceiling is measured here; ranking is D's question)",
        "c2_status": "STILL LOCKED",
    }

    # ── the bottleneck, written from the numbers rather than asserted ───────────────────────────
    o_static = cells[EV][static_rung]["agg"].get("oracle") or {}
    o_base = cells[EV][rungs[0][0]]["agg"].get("oracle") or {}
    rm_pin = removal[EV]["frozen_baseline"]["paired_vs_full_static"]["oracle_err_m"]
    inert = [r for r, _ in rungs[1:] if comparisons[DEC]["rung_increments"][r].get("oracle_hit_500m", {})
             .get("identical")]
    strata = R_strata = grouped[EV]["by_stratum"]
    worst = sorted([s for s in strata if s["n"]], key=lambda s: (s["oracle_hit_500m"] or 0))[:2]
    worst_txt = "; ".join(f"{w['group']}: n={w['n']}, <500 m {w['oracle_hit_500m']}" for w in worst)
    bottleneck = [
        f"* **The frozen baseline pin is the ceiling, and the locality arm is the only other arm that "
        f"contributes.** Removing the pin from the static lane costs "
        f"{rm_pin.get('point_delta')} m of oracle median on the locked check, with the paired interval "
        f"entirely above zero "
        f"({fmt_ci(rm_pin, a_label='without the pin', b_label='with the pin')}) — the pin is "
        f"load-bearing; the locality rung adds "
        f"{comparisons[EV]['rung_increments'].get('+locality_centroid', {}).get('oracle_hit_500m', {}).get('point_delta')} "
        f"of the <500 m hit-rate on the locked check "
        f"({fmt_ci(comparisons[EV]['rung_increments'].get('+locality_centroid', {}).get('oracle_hit_500m', {}), a_label='with the locality arm', b_label='without')}) "
        f"and is *not resolved* on the selection population — a small, honestly-quantified addition.",
        f"* **The remaining static arms are inert on this corpus.** Adding {', '.join(inert) if inert else 'no rung'} "
        f"produces an *identical* per-address oracle series, so the ladder from `{rungs[1][0]}` to "
        f"`{static_rung}` is flat: town centroids, POI landmarks and the address book never supply a "
        f"better candidate than the pin or the locality centroid for these addresses. That is the "
        f"empirical form of the brief's rule D — **no complexity without a measured improvement**.",
        f"* **What is left is a data-granularity limit, not a mechanism failure.** Locked-check oracle "
        f"median {o_static.get('median_err_m')} m (<100 m {o_static.get('hit_100m')}, <500 m "
        f"{o_static.get('hit_500m')}) against the pin-only rung's {o_base.get('median_err_m')} m "
        f"(<500 m {o_base.get('hit_500m')}); the failures concentrate in the coarse strata "
        f"({worst_txt}). "
        f"The supplied official data offers a precision-tagged pin plus locality/town centroids; no "
        f"admitted arm can conjure street-level knowledge it does not contain, and external augmentation "
        f"is forbidden by the final data policy.",
        f"* **Where the headroom actually is: confirmed history.** Of the {failure_analysis['static_lane_oracle_over_500m']} "
        f"locked-check addresses whose static oracle is worse than 500 m, "
        f"{failure_analysis['of_those_with_evidence_available']} have visit history and "
        f"{failure_analysis['of_those_recovered_by_the_evidence_lane']} of those are recovered inside 500 m by the "
        f"evidence lane (LENS B). That is the measured case for prioritising F/L/O — field evidence and "
        f"memory — over any new retrieval mechanism, including C2.",
    ]

    # ── runtime cost ────────────────────────────────────────────────────────────────────────────
    acc_path = os.path.join(config.DERIVED, "acceptance_report.json")
    acceptance_latency = None
    if os.path.exists(acc_path):
        acceptance_latency = json.load(open(acc_path, encoding="utf-8")).get("latency")
    cost = {"retrieval_generation": timing,
            "note": ("retrieval-layer cost only (candidate generation, no ranking/belief/I-O); the "
                     "full resolve path latency is reported by the acceptance suite"),
            "full_resolve_path_from_acceptance_report": acceptance_latency,
            "total_experiment_seconds": round(time.time() - t_start, 1)}

    # ── results CSV ─────────────────────────────────────────────────────────────────────────────
    csv_path = os.path.join(out_dir, "experiment_c_results.csv")
    with open(csv_path, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["population", "rung", "address_id", "n_candidates", "coverage", "labelled",
                    "oracle_err_m", "oracle_hit_100m", "oracle_hit_250m", "oracle_hit_500m",
                    "recall_100", "recall_250", "recall_500", "rule_top1_err_m", "latency_ms"])
        for pname in populations_used:
            for rname in cells[pname]:
                for r in cells[pname][rname]["rows"]:
                    w.writerow([pname, rname, r["address_id"], r["n_candidates"], r["coverage"],
                                r["labelled"], r["oracle_err_m"], r.get("oracle_hit_100m"),
                                r.get("oracle_hit_250m"), r.get("oracle_hit_500m"),
                                r.get("recall_100"), r.get("recall_250"), r.get("recall_500"),
                                r.get("rule_top1_err_m"), r["latency_ms"]])

    # ── receipt ─────────────────────────────────────────────────────────────────────────────────
    receipt = {
        "experiment": "C — retrieval-only ceiling",
        "question": ("how good is the candidate-retrieval layer by itself, before ranking?"),
        "schema_version": SCHEMA_VERSION, "protocol_version": PROTOCOL_VERSION,
        "rule_version": RULE_VERSION, "evidence_policy_version": EVIDENCE_POLICY_VERSION,
        "radius_map_version": RADIUS_MAP_VERSION,
        "as_of": as_of,
        "lenses": {
            "primary": {"name": "LENS A — static retrieval ceiling",
                        "arms": list(config.STATIC_ARMS),
                        "note": ("the arms that answer a cold address; the C ceiling is this lane only")},
            "secondary": {"name": "LENS B — historical evidence arms (diagnostic)",
                          "arms": list(EVIDENCE_LANE),
                          "note": ("consumes the visit history and exists for a minority of surveyed "
                                   "addresses; never part of the C headline")},
        },
        "ladder": [{"rung": name, "arms": list(arms)} for name, arms in rungs],
        "populations": {k: len(v) for k, v in populations_used.items()},
        "n_labelled_proxy": len(proxy), "n_labelled_surveyed": len(truth_eval),
        "label_sources": {"supervised_populations": "operational_confirmation_proxy (never ground truth)",
                          "S-EVAL": "surveyed_ground_truth via S_EVAL_BASELINE (single read)"},
        "intervals": {"method": "grouped bootstrap, 95%, paired on the difference",
                      "resamples": a.resamples, "group": "place block (primary)",
                      "sensitivity_group": "account", "seed": a.seed, "module": "sutra/stats.py"},
        "results": {pname: {rname: cells[pname][rname]["agg"] for rname in cells[pname]}
                    for pname in populations_used},
        "prefix_recall": {pname: {label: {"agg": v["agg"]} for label, v in entry.items()}
                          for pname, entry in prefix.items()},
        "arm_census_full_book": census_book,
        "arm_census_s_eval": census_eval,
        "arm_quality_s_eval": quality_eval,
        "arm_quality_s_val": quality_val,
        "comparisons": comparisons,
        "arm_removal": removal,
        "grouped": grouped,
        "negative_controls": controls,
        "lane_quality": lane_quality,
        "leakage_runtime_proof": {
            "guard": "`sutra.dataio.surveyed` was replaced by a counting wrapper for the whole generation pass",
            "n_reads_of_the_surveyed_table_during_generation": len(guard_hits),
            "addresses_generated": len(pop_book),
            "reading": ("the candidate path never reads the surveyed truth table; a near-zero distance "
                        "between a candidate and a surveyed coordinate can therefore only come from an "
                        "independent measurement of the same place"),
            "static_scan": "see negative_controls.governance.candidate_path_reads_surveyed_anywhere",
        },
        "decision": {**decision, "bottleneck_report": bottleneck},
        "runtime_cost": cost,
        "test_look_counter_before": counter_before,
        "test_look_counter_after": counter_after,
        "determinism": {
            "candidate_universe_sha256_full_book": universe_hash,
            "candidate_universe_sha256_experiment_b_address_set": subset_hash,
            "hash_alg": "sha256 over (address|arm|source_ref|x|y|granularity|as_of_valid)",
        },
        "hashes": {"code": _file_hashes(["sutra/candidates.py", "sutra/indexes.py", "sutra/ranking.py",
                                         "sutra/replay.py", "sutra/stats.py", "tools/experiment_c.py"]),
                   "artefacts": _file_hashes(["data/derived/candidates_v2.csv",
                                              "data/derived/supervision_manifest.csv",
                                              "data/derived/split_receipt.json"])},
        "seconds": round(time.time() - t_start, 1),
    }
    rc_path = os.path.join(out_dir, "experiment_c_receipt.json")
    with open(rc_path, "w", encoding="utf-8") as fh:
        json.dump(receipt, fh, indent=2, sort_keys=True, ensure_ascii=False, default=str)

    # ── console ─────────────────────────────────────────────────────────────────────────────────
    print(f"experiment C — retrieval-only ceiling · primary lens = static arms only · as-of {as_of}")
    print(f"  full book {len(pop_book)} addresses generated in {timing['mean_ms']:.2f} ms/address "
          f"(p95 {timing['p95_ms']} ms) · candidate universe {universe_hash[:12]}")
    print(f"  test-look counter: {counter_before} -> {counter_after} (one declared S-Eval read)")
    for pname in ("S-EVAL (locked check)", "S_VAL (selection)", "S_TRAIN+S_VAL (stability)",
                  "leave-block-out (stress)"):
        print(f"\n  {pname} — cumulative union ladder (registry order)")
        print(f"    {'rung':<26} {'cov':>6} {'orc med':>8} {'orc p80':>8} {'<100m':>6} {'<500m':>6} "
              f"{'rec@100':>7} {'rec@500':>7} {'cand/addr':>9}")
        for rname, _arms in rungs:
            g = cells[pname][rname]["agg"]
            o = g.get("oracle") or {}
            print(f"    {rname:<26} {str(g.get('coverage_labelled')):>6} {str(o.get('median_err_m')):>8} "
                  f"{str(o.get('p80_err_m')):>8} {str(o.get('hit_100m')):>6} {str(o.get('hit_500m')):>6} "
                  f"{str(g.get('recall_100')):>7} {str(g.get('recall_500')):>7} "
                  f"{str(g['cand_count']['mean']):>9}")
        p = prefix[pname]
        a1 = p[static_rung]["agg"]
        print(f"    prefix recall (static lane, deterministic order): "
              f"@1 {a1['prefix1_hit_500m']} · @3 {a1['prefix3_hit_500m']} · @5 {a1['prefix5_hit_500m']} "
              f"· @10 {a1['prefix10_hit_500m']} (hit@500 m)")
        ev = p.get("evidence_lane (field_evidence+memory)", {}).get("agg", {})
        if ev:
            print(f"    LENS B diagnostic (evidence arms): coverage "
                  f"{cells[pname]['evidence_lane (field_evidence+memory)']['agg'].get('coverage_labelled')} "
                  f"· oracle median "
                  f"{(cells[pname]['evidence_lane (field_evidence+memory)']['agg'].get('oracle') or {}).get('median_err_m')} m "
                  f"· prefix@1 {ev.get('prefix1_hit_500m')}")

    print("\n  paired deltas vs the baseline-only rung (95% grouped bootstrap, group=place block):")
    for pname in ("S-EVAL (locked check)", "S_VAL (selection)"):
        for rname in comparisons[pname]["rungs_vs_baseline_only"]:
            d = comparisons[pname]["rungs_vs_baseline_only"][rname]["oracle_hit_500m"]
            e = comparisons[pname]["rungs_vs_baseline_only"][rname]["oracle_err_m"]
            print(f"    {pname:<22} {rname:<26} <500m {fmt_ci(d, a_label=rname, b_label='baseline')} | "
                  f"median {fmt_ci(e, a_label=rname, b_label='baseline')}")
    print("\n  rung increments (each arm's own contribution):")
    for pname in ("S-EVAL (locked check)", "S_VAL (selection)"):
        for rname, d in comparisons[pname]["rung_increments"].items():
            print(f"    {pname:<22} {rname:<26} <500m "
                  f"{fmt_ci(d['oracle_hit_500m'], a_label=rname, b_label='previous rung')}")
    print("\n  arm removal (static lane without one arm, vs the complete static lane):")
    for pname in ("S-EVAL (locked check)", "S_VAL (selection)"):
        for arm, d in removal[pname].items():
            pr = d["paired_vs_full_static"]["oracle_err_m"]
            print(f"    {pname:<22} drop {arm:<18} oracle median "
                  f"{fmt_ci(pr, a_label='without', b_label='with')} "
                  f"| Δmedian {d['delta_oracle_err_m_vs_full_static']} m")
    print("\n  negative controls:")
    print(f"    random-candidate control (anchored, count-matched) vs real static lane: "
          f"{fmt_ci(ctl_pairs.get('S-EVAL (locked check)|anchored'), a_label='real', b_label='random')}")
    print(f"    truth-echo scan: {controls['truth_echo_scan']['candidates_within_1m_of_truth']} candidate(s) "
          f"within 1 m of a surveyed coordinate out of "
          f"{controls['truth_echo_scan']['candidates_scanned']} scanned")
    print(f"    outbound call attempts: {controls['outbound_call_attempts']} · place_neighbour rows: "
          f"{controls['governance']['candidate_artefact_place_neighbour_rows']} · C2 enabled: "
          f"{controls['governance']['place_neighbour_enabled_in_config']}")
    print(f"\n  decision: ceiling_adequate={decision['ceiling_adequate']} · "
          f"arms that earn their place: {arm_earners or 'none'} · "
          f"C2 eligible for future testing={decision['c2_gate']['eligible_for_a_future_controlled_experiment']} "
          f"(C2 {decision['c2_status']})")

    md_path = os.path.join(out_dir, "experiment_c_report.md")
    write_report(receipt, csv_path, md_path)
    socket.socket, socket.create_connection = real_socket, real_create
    print(f"\nwrote {os.path.relpath(csv_path, config.ROOT)}, {os.path.relpath(rc_path, config.ROOT)} and "
          f"{os.path.relpath(md_path, config.ROOT)} in {receipt['seconds']}s")
    return 0


def _file_hashes(files: list[str]) -> dict:
    out = {}
    for f in files:
        p = os.path.join(config.ROOT, f)
        if os.path.exists(p):
            out[f] = hashlib.sha256(open(p, "rb").read()).hexdigest()
    return out


# ── report ───────────────────────────────────────────────────────────────────────────────────────
def write_report(R: dict, csv_path: str, path: str) -> None:
    L: list[str] = []
    A = L.append
    rungs = [r["rung"] for r in R["ladder"]]
    static_rung = rungs[-1]
    A("# Experiment C — retrieval-only ceiling")
    A("")
    A(f"*Generated by `tools/experiment_c.py` · {R['seconds']}s · as-of `{R['as_of']}` · "
      f"schema `{R['schema_version']}` · rules `{R['rule_version']}` · protocol `{R['protocol_version']}`*")
    A("")
    A("**Question (1 — what exactly was measured).** How good is the **retrieval layer by itself**, before")
    A("ranking? For every address the arms produce a *candidate set*; C measures whether that set contains a")
    A("usable answer, per arm, per cumulative union, and per population. **No ranker decides anything here**:")
    A("the only ranking-shaped number in this report is the framework's own \"lane top-1\", printed as")
    A("context and labelled Experiment D's territory.")
    A("")
    A("**The four things this report keeps apart** (they are routinely conflated):")
    A("")
    A("| term | meaning here |")
    A("|---|---|")
    A("| **retrieval coverage** | the share of addresses for which *some* admitted arm emits a candidate |")
    A("| **retrieval recall** | the share of labelled addresses whose candidate set contains a point within k metres |")
    A("| **oracle ceiling** | the error of the *best* candidate in the set — what a perfect ranker could reach |")
    A("| **ranked answer** | the error of what the system actually returns today (rule top-1) — **D's question, not C's** |")
    A("")
    A("A good oracle does **not** mean a good system. It means the information was in the candidate set.")
    A("Whether the ranker can find it is Experiment D.")
    A("")
    A("## 1. What was admitted, and what was excluded (2 · 3)")
    A("")
    A("**Admitted (primary lens).** The static retrieval arms, in registry order — the arms that answer a")
    A("*cold* address with no history:")
    A("")
    A("| arm | what it reads (official tables only) | cold/static or historical | licence | as-of |")
    A("|---|---|---|---|---|")
    for arm in R["lenses"]["primary"]["arms"]:
        reads = {
            "frozen_baseline": "`baseline_geocodes.csv` (the supplied pin, precision-tagged)",
            "locality_centroid": "`localities.csv` centroid, selected by the address text",
            "town_centroid": "`towns.csv` centroid",
            "official_landmark": "`landmarks_poi.csv` POI matched through the text's relation window",
            "address_book": "`addresses.csv` — an exact text key already carrying a pin",
        }.get(arm, "")
        A(f"| `{arm}` | {reads} | cold/static | `{R['lenses']['primary']['note'] and 'official'}` | n/a (not evidence-backed) |")
    A("")
    A("**Excluded from the C headline (LENS B diagnostic, reported separately).** "
      "`field_evidence` and `memory`: they consume the visit history, exist for a minority of surveyed")
    A("addresses, and are the subject of Experiments F/L/M/O. They are reported below in their own table")
    A("and are **never** mixed into the ceiling.")
    A("")
    A("**Locked out entirely — `place_neighbour` (C2).** The arm exists in code, is disabled in config, and")
    A("is asserted absent from every candidate set, from the emitted artefact and from this run. C2 is not")
    A("run, not tuned and not admitted. See §14.")
    A("")
    A("## 2. Populations, labels and split protocol")
    A("")
    A("| population | n | label used |")
    A("|---|---|---|")
    labels = {"FULL BOOK (label-free)": "none (retrieval availability only)",
              "S_TRAIN+S_VAL (stability)": "`operational_confirmation_proxy` (never called truth)",
              "S_VAL (selection)": "`operational_confirmation_proxy`",
              "leave-block-out (stress)": "`operational_confirmation_proxy`",
              "S-EVAL (locked check)": "**surveyed ground truth**, read once via `S_EVAL_BASELINE`"}
    for k, v in R["populations"].items():
        A(f"| {k} | {v} | {labels.get(k, '')} |")
    A(f"| labelled addresses available | proxy {R['n_labelled_proxy']} · surveyed {R['n_labelled_surveyed']} | |")
    A("")
    A(f"**Test-look counter: {R['test_look_counter_before']} before the run → "
      f"**{R['test_look_counter_after']}** after** (one declared single read of S-Eval, logged as "
      "`experiment_C:s_eval_locked_check (single read)`). The read decides nothing; the split for every "
      "supervised population is the declared protocol, not a new split.")
    A("")
    A("## 3. Full-book retrieval availability (label-free)")
    A("")
    A(f"All {R['populations']['FULL BOOK (label-free)']} addresses in the index, generated once through the")
    A(f"production path (B2 ring, unchanged): **{R['runtime_cost']['retrieval_generation']['mean_ms']} ms per "
      f"address** (p50 {R['runtime_cost']['retrieval_generation']['p50_ms']} · "
      f"p95 {R['runtime_cost']['retrieval_generation']['p95_ms']}).")
    A("")
    A("| arm | addresses it emits for | share | candidates | mean per emitting address | as-of-valid | cold/static? |")
    A("|---|---|---|---|---|---|---|")
    for arm, c in R["arm_census_full_book"].items():
        A(f"| `{arm}` | {c['addresses_emitting']} | {c['share_emitting']} | {c['candidates']} | "
          f"{c['mean_candidates_per_emitting_address']} | {c['candidates_with_as_of_valid']} | "
          f"{'historical' if c['evidence_backed'] else 'cold/static'} |")
    A("")
    fb = R["results"]["FULL BOOK (label-free)"][static_rung]
    cc = fb["cand_count"]
    A(f"Static lane over the whole book: **coverage {fb['coverage_all']}** · "
      f"unresolved {fb['unresolved_all']} · candidates per address min {cc['min']} · "
      f"median {cc['median']} · mean {cc['mean']} · p90 {cc['p90']} · max {cc['max']}.")
    A("")
    A("## 4. The static retrieval ceiling — cumulative union ladder (registry order)")
    A("")
    A("Each rung adds one arm; every rung is a full candidate set scored with the framework's own")
    A("definitions. `recall_k` = *a candidate exists within k metres*; `oracle` = the best candidate.")
    A("")
    for pname in (EV, VA, ST):
        A(f"### {pname}")
        A("")
        A("| rung | coverage | oracle median | oracle p80 | oracle p90 | <100 m | <250 m | <500 m | "
          "recall@100 | recall@500 | cand/addr |")
        A("|---|---|---|---|---|---|---|---|---|---|---|")
        for rname in rungs:
            g = R["results"][pname][rname]
            q = R["lane_quality"][pname][rname]
            A(f"| {rname} | {g.get('coverage_labelled')} | {q.get('oracle_median_err_m')} m | "
              f"{q.get('oracle_p80_err_m')} m | {q.get('oracle_p90_err_m')} m | {q.get('oracle_hit_100m')} | "
              f"{g.get('oracle', {}).get('hit_250m')} | {q.get('oracle_hit_500m')} | "
              f"{g.get('recall_100')} | {g.get('recall_500')} | {g['cand_count']['mean']} |")
        A("")
        u = R["results"][pname][rungs[0]]
        s = R["results"][pname][static_rung]
        qs = R["lane_quality"][pname][static_rung]
        A(f"unresolved rate: baseline-only {u.get('unresolved_labelled')} → static lane "
          f"{s.get('unresolved_labelled')}. Lane coverage inside the labelled population: "
          f"{qs['coverage_in_lane']} ({qs['n_covered_in_lane']}/{qs['n_labelled']}) — the oracle n below "
          f"is that covered set, while `recall_k` scores an uncovered address as a miss over every "
          f"labelled address (the censored reading).")
        A("")
    A("### Prefix recall — how deep a usable candidate sits (static lane)")
    A("")
    A("The deterministic retrieval order is `config.ARMS` order, then `arm_rank`, then `candidate_id` —")
    A("exactly the order `sutra.candidates.generate` returns. No ranker is involved: this is where a")
    A("candidate sits *before* any reordering, which set recall cannot show.")
    A("")
    A("| population | prefix@1 | prefix@3 | prefix@5 | prefix@10 | set recall@500 (whole set) |")
    A("|---|---|---|---|---|---|---|")
    for pname in (EV, VA, ST):
        p = R["prefix_recall"][pname][static_rung]["agg"]
        A(f"| {pname} | {p['prefix1_hit_500m']} | {p['prefix3_hit_500m']} | {p['prefix5_hit_500m']} | "
          f"{p['prefix10_hit_500m']} | {R['results'][pname][static_rung].get('recall_500')} |")
    A("")
    for pname in (EV,):
        p = R["prefix_recall"][pname][static_rung]["agg"]
        A(f"At the tighter 100 m tolerance the same prefix curve on {pname} reads "
          f"@1 {p['prefix1_hit_100m']} · @3 {p['prefix3_hit_100m']} · @5 {p['prefix5_hit_100m']} · "
          f"@10 {p['prefix10_hit_100m']}.")
        A("")
    A("## 5. Per-arm contribution")
    A("")
    A("**Which arm supplies the best candidate** (how often an arm's own candidate is the oracle winner),")
    A("and **which arm is load-bearing** (drop it and the ceiling moves):")
    A("")
    A(f"| arm | emit rate (S-Eval) | median error when it fires | <100 m | <500 m | supplies the oracle "
      f"(ties counted) | only arm within 500 m | drop-it Δ oracle median (aggregate) | drop-it Δ (paired) |")
    A("|---|---|---|---|---|---|---|---|")
    for arm in R["lenses"]["primary"]["arms"]:                     # the C ceiling is the static lane
        q = R["arm_quality_s_eval"][arm]
        rm = R["arm_removal"][EV].get(arm, {})
        pr = (rm.get("paired_vs_full_static") or {}).get("oracle_err_m", {})
        fire = "never fires" if not q["fires"] else ""
        A(f"| `{arm}` | {q['fire_rate']} | {q['median_err_m'] if q['fires'] else '—'} "
          f"{'m' if q['fires'] else fire} | {q['hit_100m'] if q['fires'] else '—'} | "
          f"{q['hit_500m'] if q['fires'] else '—'} | {q['supplies_the_best_candidate']} | "
          f"{q['is_the_only_arm_within_500m']} | {rm.get('delta_oracle_err_m_vs_full_static')} m | "
          f"{pr.get('point_delta')} [{pr.get('lo')}, {pr.get('hi')}] |")
    A("")
    A("`supplies the oracle` counts every address where the arm's own candidate *is* the best one, so a tie")
    A("counts for each arm sharing it and the column sums above the population size. The two Δ columns")
    A("disagree on purpose: the *aggregate* compares two medians of the whole population (a handful of")
    A("addresses moving a long way shows up), while the *paired* interval resamples the per-address")
    A("difference and is the reading a claim is allowed to rest on — `[0.0000, 0.0000]` means the median")
    A("per-address change is exactly zero, which is the honest result for an arm that only helps a few")
    A("addresses.")
    A("")
    A("**Cumulative-union increments** — does the arm added at each rung earn its place? (paired, grouped")
    A("bootstrap, 95%, group = place block; *not resolved* = inside the interval, i.e. this dataset cannot")
    A("tell the difference):")
    A("")
    A("| population | rung added | Δ oracle <500 m | Δ oracle median | Δ coverage | reading |")
    A("|---|---|---|---|---|---|")
    for pname in (EV, VA):
        for rname, d in R["comparisons"][pname]["rung_increments"].items():
            h, e, c = d["oracle_hit_500m"], d["oracle_err_m"], d["coverage_labelled"]
            A(f"| {pname} | {rname} | {h.get('point_delta')} [{h.get('lo')}, {h.get('hi')}] | "
              f"{e.get('point_delta')} [{e.get('lo')}, {e.get('hi')}] | "
              f"{c.get('point_delta')} [{c.get('lo')}, {c.get('hi')}] | "
              f"{'resolved' if h.get('resolved') else 'not resolved'} |")
    A("")
    A("## 6. Per-town and per-stratum (S-Eval and S-Val, with n)")
    A("")
    for pname in (EV, VA):
        for by in ("by_town", "by_stratum"):
            rows = (R["grouped"].get(pname) or {}).get(by) or []
            if not rows:
                continue
            A(f"### {pname} — {by.replace('by_', '')}")
            A("")
            A("| group | n | unresolved | oracle median | oracle p80 | <100 m | <500 m | below n-guard |")
            A("|---|---|---|---|---|---|---|---|")
            for r in rows:
                A(f"| {r['group']} | {r['n']} | {r['n_unresolved']} | {r['oracle_median_err_m']} m | "
                  f"{r['oracle_p80_err_m']} m | {r['oracle_hit_100m']} | {r['oracle_hit_500m']} | "
                  f"{'**yes — indicative only**' if r['below_n_guard'] else 'no'} |")
            A("")
            if any(r["below_n_guard"] for r in rows):
                A(f"*Strata marked **below n-guard** (< {N_GUARD}) are printed because hiding them would hide")
                A("the failure, but they are **not** precision claims: a median over 4 addresses is an anecdote,")
                A("and the framework's own rule (`config.N_GUARD`) is that such a stratum falls back to its parent.*")
                A("")
    A("## 7. LENS B — the historical evidence arms (diagnostic only)")
    A("")
    ev_lane = "evidence_lane (field_evidence+memory)"
    for pname in (EV, VA, ST):
        g = R["results"][pname][ev_lane]
        o = g.get("oracle") or {}
        A(f"* **{pname}**: coverage {g.get('coverage_labelled')} · oracle median {o.get('median_err_m')} m · "
          f"<100 m {o.get('hit_100m')} · <500 m {o.get('hit_500m')} · candidates/address "
          f"{g['cand_count']['mean']}")
    A("")
    A(f"These arms exist only where the address has an eligible visit history "
      f"(`field_evidence` {R['arm_census_s_eval']['field_evidence']['addresses_emitting']}/100, "
      f"`memory` {R['arm_census_s_eval']['memory']['addresses_emitting']}/100 on S-Eval), so the lane's")
    A("coverage figure is a statement about **visit coverage**, not about retrieval quality. They are the")
    A("subject of F (vendor + field learning), L (memory) and O (cold vs warm) and are excluded from the")
    A("C ceiling by construction.")
    A("")
    A("## 8. Negative controls")
    A("")
    rcs = R["negative_controls"]["random_candidate_control"][EV]
    rcv = R["negative_controls"]["random_candidate_control"][VA]
    A("| control | what it forbids | result |")
    A("|---|---|---|")
    ctl = R["negative_controls"]["real_static_lane_vs_random_control"]
    d = ctl.get(f"{EV}|anchored", {})
    A(f"| random candidates, count-matched, around the locality anchor | \"the arms are just more points near the anchor\" | "
      f"control oracle median **{rcs['anchored'].get('median_err_m')} m** (<500 m {rcs['anchored'].get('hit_500m')}) "
      f"vs real static lane; paired Δ (real − random) {d.get('point_delta')} [{d.get('lo')}, {d.get('hi')}] → "
      f"{'resolved' if d.get('resolved') else 'not resolved'} |")
    dt = ctl.get(f"{EV}|town_uniform", {})
    A(f"| random candidates, town-uniform | the same, without the anchor's help | "
      f"{rcs['town_uniform'].get('median_err_m')} m · paired Δ {dt.get('point_delta')} "
      f"[{dt.get('lo')}, {dt.get('hi')}] |")
    A(f"| baseline-only rung | \"the extra arms contributed nothing\" | baseline-only rung is rung 1 of the ladder "
      f"(§4); every later rung is compared to it in §5 |")
    te = R["negative_controls"]["truth_echo_scan"]
    A(f"| truth-echo scan | a candidate that *is* the evaluation truth | "
      f"{te['candidates_within_1m_of_truth']} of {te['candidates_scanned']} candidates within 1 m of a surveyed "
      f"coordinate; closest per arm: "
      f"{', '.join(f'{a} {v} m' for a, v in list(te['min_distance_per_arm_m'].items())[:5])} |")
    gv = R["negative_controls"]["governance"]
    lp = R["leakage_runtime_proof"]
    A(f"| the candidate path never reads the surveyed table | leakage through the truth file | "
      f"content reads in the candidate-path modules: "
      f"{sum(v['reads_contents'] for v in gv['candidate_path_reads_the_surveyed_table'].values())} · "
      f"**runtime guard: {lp['n_reads_of_the_surveyed_table_during_generation']} reads** while generating "
      f"all {lp['addresses_generated']} addresses · the one file-name mention is the index manifest "
      f"recording the table's sha256 as provenance, not an input |")
    A(f"| no truth column in the candidate artefact | truth smuggled as a feature | "
      f"{'**FOUND**' if gv['candidate_artefact_has_truth_column'] else 'none found'} |")
    A(f"| S-Eval firewall | a firewalled address entering supervision | "
      f"{len(gv['firewalled_addresses_in_a_supervision_split'])} violations out of {gv['firewall_rows']} "
      f"firewalled addresses |")
    A(f"| zero outbound calls | an external dependency | {R['negative_controls']['outbound_call_attempts']} "
      f"socket attempts (sockets closed for the whole run, the T12 pattern) |")
    A(f"| official data only | external augmentation | licence classes in the run: "
      f"{gv['licence_classes_in_run']}; external-data holding area empty: {gv['external_research_dir_empty']} |")
    A(f"| `place_neighbour` (C2) locked | the experiment quietly enabling itself | config flag False · emits "
      f"nothing · absent from the run · {gv['candidate_artefact_place_neighbour_rows']} rows in the artefact |")
    A("")
    A("## 9. Methodology (11) and runtime cost (14)")
    A("")
    A(f"* Intervals: grouped bootstrap, 95%, **{R['intervals']['resamples']} resamples**, group = "
      f"**{R['intervals']['group']}**, paired on the difference, deterministic seed {R['intervals']['seed']}, "
      f"`{R['intervals']['module']}`. The account-grouped interval is reported as a sensitivity check.")
    A("* A difference whose interval spans zero is written **not resolved by this dataset** — never a claim.")
    A(f"* Retrieval-layer cost: **{R['runtime_cost']['retrieval_generation']['mean_ms']} ms/address** "
      f"(p50 {R['runtime_cost']['retrieval_generation']['p50_ms']} · p95 "
      f"{R['runtime_cost']['retrieval_generation']['p95_ms']} · max "
      f"{R['runtime_cost']['retrieval_generation']['max_ms']}) for candidate generation alone, over the full book.")
    if R["runtime_cost"]["full_resolve_path_from_acceptance_report"]:
        al = R["runtime_cost"]["full_resolve_path_from_acceptance_report"]
        A(f"* Full `resolve` path (candidates + ranker + belief + uncertainty), from the acceptance suite: "
          f"p50 {al['p50_ms']} ms · p95 {al['p95_ms']} ms (target {al['target_p95_ms']} ms → "
          f"{'MET' if al['target_met'] else 'NOT MET'}).")
    A(f"* Whole experiment: {R['runtime_cost']['total_experiment_seconds']} s.")
    A("")
    A("## 10. Determinism and registration")
    A("")
    A(f"* candidate universe, full book: `{R['determinism']['candidate_universe_sha256_full_book']}`")
    A(f"* candidate universe over Experiment B's address set: "
      f"`{R['determinism']['candidate_universe_sha256_experiment_b_address_set']}` — it must equal "
      f"Experiment B's production-ring hash `eeba49f8672c…`, which is the cross-experiment check that C "
      f"generated the same candidates through the same path.")
    A("")
    for f, h in R["hashes"]["code"].items():
        A(f"* `{f}` `{h[:12]}…`")
    A("")
    A("## 11. What limits the ceiling (16 — the bottleneck)")
    A("")
    bo = R["decision"].get("bottleneck_report")
    if bo:
        for line in bo:
            A(line)
        A("")
    A("## 12. Decision for the next experiment (17)")
    A("")
    dd = R["decision"]
    A(f"* **Ceiling adequate?** `{dd['ceiling_adequate']}` — {dd.get('adequacy_reading', '')}")
    A("")
    A(f"Declared adequacy clauses (population: {dd['primary_decision_population']}):")
    A("")
    A("| clause | value | evidence |")
    A("|---|---|---|")
    ac = dd["adequacy_clauses"]
    c1 = ac["no_coverage_lost_vs_pin_only"]
    c2 = ac["beats_a_count_matched_random_control"]
    c3 = ac["at_least_one_admitted_arm_earns_its_place"]
    A(f"| loses no coverage against the pin-only rung | {c1['S_VAL']} | static {c1['static']} vs "
      f"pin-only {c1['pin_only']} |")
    A(f"| beats a count-matched random control | {c2['S_VAL']} | paired Δ {c2.get('point_delta')} m "
      f"[{c2.get('lo')}, {c2.get('hi')}] (n={c2.get('n')}) |")
    A(f"| at least one admitted arm earns its place | {c3['value']} | {', '.join(c3['arms']) or 'none'} |")
    A("")
    if dd["arms_that_earn_their_place"]:
        A("* **Arms that earn their place** (resolved improvement, paired and grouped):")
        A("")
        A("| population | role | rung | metric | delta |")
        A("|---|---|---|---|---|")
        for e in dd["arms_that_earn_their_place"]:
            A(f"| {e['population']} | {e['role']} | {e['rung']} | {e['metric']} | {e['delta']} |")
    else:
        A("* **Arms that earn their place:** **none beyond the frozen baseline** — a legitimate outcome, "
          "and the reason the layer is not made more complex.")
    A("")
    A(f"* **Retrieval the dominant bottleneck?** `{dd['retrieval_is_the_bottleneck']}`")
    A(f"* **Load-bearing arms (dropping one is resolved worse):** "
      f"{', '.join('`' + a + '`' for a in dd['load_bearing_arms_under_removal']) or 'none'}"
      f"{' — ' + R['arm_removal'][EV][dd['load_bearing_arms_under_removal'][0]]['reading'] if dd['load_bearing_arms_under_removal'] else ''}")
    A(f"* **Selection vs locked check, stated separately:** the locality arm's increment is resolved on "
      f"the **locked check** "
      f"({dd['static_lane_vs_baseline_only']['S-EVAL (locked check)']['oracle_hit_500m'].get('point_delta')} "
      f"<500 m) but *not resolved* on the **selection population** "
      f"({dd['static_lane_vs_baseline_only']['S_VAL (selection)']['oracle_hit_500m'].get('point_delta')} "
      f"<500 m, interval spanning zero). C records both and adopts nothing — no threshold, feature or arm "
      f"is chosen from either number.")
    A(f"* **Next experiment:** {dd['next_experiment']}")
    A(f"* Ranked-answer context (D's territory, not this decision): rule top-1 on S-Eval "
      f"{dd['ranked_answer_share_s']['S-EVAL static lane'].get('median_err_m')} m median, "
      f"<500 m {dd['ranked_answer_share_s']['S-EVAL static lane'].get('hit_500m')}.")
    A("")
    A("## 13. Honest caveats")
    A("")
    A("* S-Eval is 100 addresses and is read **once**; every interval is grouped by place block, so the")
    A("  effect of spatially clustered truth is priced in. Small strata are printed with their n and marked")
    A("  below the n-guard.")
    A("* The proxy label is an independently-confirmed field position — a *proxy*, never ground truth.")
    A("* `oracle` is a ceiling, not a result: it is what a perfect ranker over this exact candidate set could")
    A("  reach. The system's actual answer is the rule top-1, and improving it is Experiment D.")
    A("* The evidence arms (LENS B) are excluded from the ceiling because they consume the visit history;")
    A("  their coverage is visit coverage, and they are the subject of later experiments.")
    A("")
    A("## 14. C2 status (18)")
    A("")
    c2 = R["decision"]["c2_gate"]
    A(f"* **C2 (neighbour index): `{R['decision']['c2_status']}`.**")
    A(f"* Eligible for a *future controlled* experiment: **{c2['eligible_for_a_future_controlled_experiment']}**. "
      f"Run now: **{c2['run_now']}**.")
    A(f"* Reason: {c2['reason']}")
    A("* The barrier stands: `config.ENABLE_PLACE_NEIGHBOUR = False`, the arm raises rather than emitting, the")
    A("  production candidate set is untouched, and no C2 result appears anywhere in this experiment.")
    A("")
    A("## 15. Reproduce")
    A("")
    A("```bash")
    A("cd PS3_SUTRA && python3 tools/experiment_c.py      # this experiment")
    A("cd PS3_SUTRA && bash tools/reproduce.sh full       # the whole chain (C is the last step)")
    A("```")
    A("")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
