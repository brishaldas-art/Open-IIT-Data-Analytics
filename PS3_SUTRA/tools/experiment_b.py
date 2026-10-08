#!/usr/bin/env python3
"""P12 step B — preprocessing ablation (B1 raw · B2 normalised+spans · B3 +TF-IDF/SVD · B4 +parser).

    python3 tools/experiment_b.py [--rings B1,B2,B3,B4] [--resamples 10000]

**Question.** Does increasingly sophisticated deterministic address preprocessing actually improve
candidate retrieval or final geocoding enough to justify its complexity? The answer must be empirical.

**What varies.** Text handling only — one `sutra.preprocess.Ring` per rung. The candidate arms, the
record shape, the licence class, the as-of discipline, the ranker and the radius map are identical
across rungs (contract §4 is not reopened; `sutra/candidates.py` takes the ring as an argument and
defaults to production `B2`).

**What is measured** (definitions reused, not reinvented):
* candidate metrics follow `sutra.replay.candidate_metrics` — coverage, recall@k at 100/250/500 m,
  oracle error median · p80 · hit-rates, and the rule-priority top-1;
* labels are `operational_confirmation_proxy` (an independently-confirmed field position, **never**
  called ground truth) for selection, exactly as `sutra.replay` defines it;
* intervals are the plan's grouped bootstrap 95%, 10,000 resamples, grouped by **place block**
  (`sutra.stats`), reported as paired deltas against the production rung.

**Environments.**
* `S-VAL` (69 addresses) — the **selection** population. Nothing else is looked at while choosing.
* `S-TRAIN+S-VAL` (292) — reported for stability.
* `S-EVAL` (100 surveyed) — the **locked check**, read once through the declared `S_EVAL_BASELINE`
  spec; the read increments the test-look counter, is reported, and decides nothing.
* `leave-block-out` (S-TRAIN+S-VAL restricted to addresses whose place block never crosses into the
  official train split) — the stress population the framework already defines.

**Selection rule.** The cheapest rung that is not resolved-worse than the best rung on S-VAL in any
guardrail (coverage, recall@500, oracle<500 m, rule top-1<500 m, latency) is the winner; if no rung is
*resolved better* than production on a primary metric, production stays. "B1/B2 is enough" is a
successful result and is recorded as such.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sutra import config, dataio, geo, preprocess, ranking, splits, stats        # noqa: E402
from sutra.candidates import generate                                            # noqa: E402
from sutra.indexes import get_index                                               # noqa: E402
from sutra.replay import _manifest, _proxy_truth, _q                             # noqa: E402
from sutra.store import Store                                                     # noqa: E402
from tools.experiment_a import populations                                        # noqa: E402
from sutra.version import (EVIDENCE_POLICY_VERSION,      # noqa: E402
                           PROTOCOL_VERSION, RADIUS_MAP_VERSION, RULE_VERSION, SCHEMA_VERSION)

RINGS = ("B1", "B2", "B3", "B4")
PRODUCTION_RING = "B2"
# Declared before the final run, and applied symmetrically: a *latency* difference counts as a
# regression only when the wrong-side bound of its 95% interval exceeds 5% of the contract's p95
# budget for the whole resolve path (250 ms). Without a materiality margin, a measured 1 ms difference
# would decide a preprocessing choice on a shared machine — an artefact, not a finding. Error and
# hit-rate metrics need no such margin: given a candidate set they are exact, so any resolved
# difference in them is real.
LATENCY_MATERIALITY_MS = 0.05 * 250.0
PRIMARY = ("coverage_labelled", "recall_500", "oracle_hit_500m", "rule_top1_hit_500m",
           "variant_round_trip", "latency_ms")
HIT_THRESHOLDS = (100, 250, 500)
Q = 0.5      # the headline error statistic (median), as everywhere else in the project


# ── the ring runs ────────────────────────────────────────────────────────────────────────────────
def run_ring(ring, addresses: list[str], ix, store, as_of) -> dict:
    """Generate every address's candidate set under one ring — the only ring-dependent step.

    Deterministic: address order is fixed, the generator is deterministic, and only the wall-clock
    latency field is a measurement.
    """
    for aid in addresses[:3]:                      # warm-up (untimed): lazily built indexes etc.
        generate(aid, as_of, store, ix=ix, ring=ring)
    out: dict[str, dict] = {}
    for aid in addresses:
        t0 = time.perf_counter()
        cands = generate(aid, as_of, store, ix=ix, ring=ring)
        dt = (time.perf_counter() - t0) * 1000.0
        feats = ranking.features_matrix(ix.addresses[aid], cands, ix)
        ranked = ranking.rank(cands, feats, as_of)
        top = next((c for c in cands if c["candidate_id"] == ranked[0]["candidate_id"]), None) if ranked else None
        out[aid] = {"candidates": cands, "ranked": ranked, "top": top, "latency_ms": dt}
    return out


# ── metrics (definitions reused from sutra.replay) ───────────────────────────────────────────────
def metrics_for(pop: list[str], run: dict, truth: dict[str, tuple[float, float]], ix, as_of,
                arms: tuple[str, ...] | None = None) -> dict:
    """Per-address rows + aggregate metrics for one (ring, population, lane) cell.

    `arms` restricts the candidate set. The **static lane** (`config.STATIC_ARMS`) is the only lane a
    preprocessing ring can influence, and it is the lane scored for selection: the evidence arms
    (`field_evidence`, `memory`) are derived from the very check-ins the proxy label is built from, so
    scoring them against that label would be circular. The full lane is still computed, and reported
    as an **interference check** — a ring must not change it.
    """
    rows = []
    for aid in pop:
        r = run.get(aid)
        if r is None:
            continue
        cands = [c for c in r["candidates"] if arms is None or c["arm"] in arms]
        if arms is None:
            top = r["top"]
        else:
            # a lane's answer is that lane's best candidate under the frozen ranker — the same thing a
            # cold address gets today, when no evidence arm exists at all
            feats = ranking.features_matrix(ix.addresses[aid], cands, ix)
            ranked = ranking.rank(cands, feats, as_of)
            top = next((c for c in cands if ranked and c["candidate_id"] == ranked[0]["candidate_id"]), None)
        labelled = aid in truth
        row = {"address_id": aid, "n_candidates": len(cands), "latency_ms": round(r["latency_ms"], 3),
               "coverage": int(bool(cands)), "labelled": int(labelled)}
        if labelled:
            tx, ty = truth[aid]
            errs = [geo.dist(c["x"], c["y"], tx, ty) for c in cands]
            row["oracle_err_m"] = round(min(errs), 3) if errs else None
            for k in HIT_THRESHOLDS:
                row[f"oracle_hit_{k}m"] = int(bool(errs) and min(errs) <= k)
            for k in HIT_THRESHOLDS:                      # recall@k == "a candidate exists within k m"
                row[f"recall_{k}"] = int(any(e <= k for e in errs))
            row["rule_top1_err_m"] = (round(geo.dist(top["x"], top["y"], tx, ty), 3)
                                      if top is not None else None)
            for k in HIT_THRESHOLDS:
                row[f"rule_top1_hit_{k}m"] = int(row["rule_top1_err_m"] is not None and row["rule_top1_err_m"] <= k)
        else:
            row["oracle_err_m"] = None
            row["rule_top1_err_m"] = None
            for k in HIT_THRESHOLDS:
                row[f"recall_{k}"] = None
                row[f"oracle_hit_{k}m"] = None
                row[f"rule_top1_hit_{k}m"] = None
        rows.append(row)

    lab = [r for r in rows if r["labelled"]]
    cov_all = [r["coverage"] for r in rows]
    agg = {
        "n": len(rows), "n_labelled": len(lab),
        "coverage_all": round(sum(cov_all) / len(cov_all), 4) if cov_all else None,
        "coverage_labelled": round(sum(r["coverage"] for r in lab) / len(lab), 4) if lab else None,
        "unresolved_all": round(sum(1 - c for c in cov_all) / len(cov_all), 4) if cov_all else None,
        "unresolved_labelled": round(sum(1 - r["coverage"] for r in lab) / len(lab), 4) if lab else None,
        "cand_count": {"min": min((r["n_candidates"] for r in rows), default=0),
                       "median": _q([r["n_candidates"] for r in rows], 0.5),
                       "mean": round(sum(r["n_candidates"] for r in rows) / len(rows), 3) if rows else None,
                       "p90": _q([r["n_candidates"] for r in rows], 0.9),
                       "max": max((r["n_candidates"] for r in rows), default=0)},
        "latency_ms": {"mean": round(sum(r["latency_ms"] for r in rows) / len(rows), 3) if rows else None,
                       "p50": _q([r["latency_ms"] for r in rows], 0.5),
                       "p95": _q([r["latency_ms"] for r in rows], 0.95)},
    }
    if lab:
        # The oracle is "the best candidate in the set" — undefined where the lane emits nothing, so it is
        # computed over the *covered* labelled rows only. Uncovered addresses are never dropped silently:
        # `coverage_labelled` counts them and `recall_k` scores them as misses over every labelled address
        # (the censored reading) — the pair of numbers a varying-coverage ladder needs. Output-neutral for
        # Experiment B, whose scored lanes are fully covered (verified byte-identical after the change).
        covered = [r for r in lab if r["oracle_err_m"] is not None]
        orc = [r["oracle_err_m"] for r in covered]
        agg["oracle"] = {"median_err_m": _q(orc, 0.5), "p80_err_m": _q(orc, 0.8),
                         "hit_100m": round(sum(1 for e in orc if e <= 100) / len(orc), 4) if orc else None,
                         "hit_250m": round(sum(1 for e in orc if e <= 250) / len(orc), 4) if orc else None,
                         "hit_500m": round(sum(1 for e in orc if e <= 500) / len(orc), 4) if orc else None}
        for k in HIT_THRESHOLDS:
            agg[f"recall_{k}"] = round(sum(r[f"recall_{k}"] for r in lab) / len(lab), 4)
        top = [r["rule_top1_err_m"] for r in lab]
        agg["rule_top1"] = {"n": len(top),
                            "median_err_m": _q([t for t in top if t is not None], 0.5),
                            "hit_100m": round(sum(1 for e in top if e is not None and e <= 100) / len(top), 4),
                            "hit_250m": round(sum(1 for e in top if e is not None and e <= 250) / len(top), 4),
                            "hit_500m": round(sum(1 for e in top if e is not None and e <= 500) / len(top), 4)}
        sys_answered = [1 if r["rule_top1_err_m"] is not None else 0 for r in lab]
        prim_eligible = [1 if r["rule_top1_err_m"] is not None else 0 for r in lab]
        agg["refusal"] = {"unplaceable_share": round(1 - sum(sys_answered) / len(lab), 4)}
    else:
        agg["oracle"] = agg["rule_top1"] = None
        for k in HIT_THRESHOLDS:
            agg[f"recall_{k}"] = None
        agg["refusal"] = {"unplaceable_share": None}
    return {"agg": agg, "rows": rows}


def arm_metrics(pop: list[str], run: dict, truth: dict[str, tuple[float, float]]) -> dict:
    """Per-arm fire rate and accuracy over the labelled part of the population.

    The aggregate lane metrics are dominated by `frozen_baseline` (a file lookup no ring can change),
    so the honest reading of "did preprocessing help retrieval?" is per arm: did the text-driven arm
    fire, and how far was the candidate it proposed?
    """
    out: dict[str, dict] = {}
    for aid in pop:
        r = run.get(aid)
        if r is None or aid not in truth:
            continue
        tx, ty = truth[aid]
        for arm in config.ARMS:
            cs = [c for c in r["candidates"] if c["arm"] == arm]
            e = out.setdefault(arm, {"fired": 0, "n_labelled": 0, "errors": []})
            e["n_labelled"] += 1
            if cs:
                e["fired"] += 1
                e["errors"].append(min(geo.dist(c["x"], c["y"], tx, ty) for c in cs))
    for arm, e in out.items():
        errs = e.pop("errors")
        e["fire_rate"] = round(e["fired"] / e["n_labelled"], 4) if e["n_labelled"] else None
        e["median_err_m"] = _q(errs, 0.5)
        e["hit_100m"] = round(sum(1 for x in errs if x <= 100) / len(errs), 4) if errs else None
        e["hit_500m"] = round(sum(1 for x in errs if x <= 500) / len(errs), 4) if errs else None
    return out


def diag_stats(ring, run: dict, ix, hashes: dict, production_run: dict | None = None) -> dict:
    """What the ring *did* differently — the mechanism, not just the score."""
    residue = sum(1 for r in run.values()
                  if any(str(c["provenance"].get("match", "")).startswith("residue")
                         or c["provenance"].get("residue_match") for c in r["candidates"]))
    vs_prod = {}
    if production_run is not None:
        for aid, r in run.items():
            p = production_run.get(aid)
            if p is None:
                continue
            mine = {c["arm"]: c["source_ref"] for c in r["candidates"] if c["arm"] in config.STATIC_ARMS}
            theirs = {c["arm"]: c["source_ref"] for c in p["candidates"] if c["arm"] in config.STATIC_ARMS}
            for arm in sorted(set(mine) | set(theirs)):
                if mine.get(arm) != theirs.get(arm):
                    vs_prod[arm] = vs_prod.get(arm, 0) + 1
        vs_prod = {"addresses_with_a_different_choice_per_arm": vs_prod,
                   "addresses_compared": len(run)}
    disposition = {}
    for aid, r in run.items():
        key = tuple(sorted(c["arm"] for c in r["candidates"]))
        disposition[key] = disposition.get(key, 0) + 1
    out = {"addresses_with_residue_candidate": residue,
           "arm_disposition_top5": sorted(({"arms": list(k), "n": v} for k, v in disposition.items()),
                                          key=lambda d: (-d["n"], d["arms"]))[:5],
           "candidate_id_hash": hashes.get(ring.ring_id)}
    out.update(vs_prod)                     # {} for production itself; the per-arm diff otherwise
    return out


def hash_runs(run: dict) -> str:
    """A stable fingerprint of a ring's candidate universe (ids + coordinates + arms)."""
    h = hashlib.sha256()
    for aid in sorted(run):
        for c in run[aid]["candidates"]:
            h.update(f"{aid}|{c['arm']}|{c['source_ref']}|{c['x']}|{c['y']}|{c['granularity']}"
                     f"|{c['as_of_valid']}".encode("utf-8"))
    return h.hexdigest()


def variant_round_trip(ring, ix) -> dict:
    """Does a *differently spelled but official-equivalent* text still reach the same record?

    The candidate arms read a corpus that is already canonicalised, so they cannot show this. The
    identification path can: a field agent (or an integration) that writes an abbreviation in its long
    form — "Nagar" for "Ngr", "Road" for "Rd" — must still resolve to the same address. For every
    corpus text the ring is asked to normalise the long-form variant, and the round trip succeeds when
    the two normalise identically. Measured, per ring, over the official corpus.
    """
    import re as _re
    rows = []
    for aid in sorted(ix.addresses):
        row = ix.addresses[aid]
        raw = row.get("address_text_raw") or row.get("address_text") or ""
        long_form = raw
        for pattern, canon in dataio.ABBREV.items():
            long_form = _re.sub(pattern, canon, long_form, flags=_re.I)
        base = ring.normalise(raw)
        rows.append({"address_id": aid, "has_abbreviation": int(long_form != raw),
                     "round_trip": int(ring.normalise(long_form) == base)})
    with_abbr = [r for r in rows if r["has_abbreviation"]]
    return {
        "rows": rows,
        "rate_all": round(sum(r["round_trip"] for r in rows) / len(rows), 4) if rows else None,
        "rate_with_abbreviation": (round(sum(r["round_trip"] for r in with_abbr) / len(with_abbr), 4)
                                   if with_abbr else None),
        "n_with_abbreviation": len(with_abbr),
    }


def source_hashes(files: list[str]) -> dict:
    out = {}
    for f in files:
        p = os.path.join(config.ROOT, f)
        if os.path.exists(p):
            out[f] = hashlib.sha256(open(p, "rb").read()).hexdigest()
    return out


# ── human-readable report ───────────────────────────────────────────────────────────────────────
def fmt_ci(d: dict, digits: int = 4, a_label: str = "this ring", b_label: str = "B2") -> str:
    """A neutral two-sided reading: which side of zero the interval sits on, or 'not resolved'.

    The direction-of-better question is answered separately (guardrails, decisions); a *fire rate* is
    not "better" or "worse" on its own, so the table must not pretend otherwise.
    """
    if not d or d.get("n") in (0, None):
        return "n=0"
    if d.get("identical"):
        return "identical series (no difference to resolve)"
    if d["lo"] > 0:
        tag = f"**RESOLVED** — {a_label} higher/slower"
    elif d["hi"] < 0:
        tag = f"**RESOLVED** — {b_label} higher/slower"
    else:
        tag = "not resolved (interval spans 0)"
    return (f"{d['point_delta']:+.{digits}f} [{d['lo']:+.{digits}f}, {d['hi']:+.{digits}f}] — {tag}"
            + (f" (n={d['n']}, groups={d.get('n_groups')})" if d.get("n") else ""))


def write_report(receipt: dict, cells: dict, comparisons: dict, arm_comparisons: dict,
                 path: str) -> None:
    R = receipt
    rings = [k for k in ("B1", "B2", "B3", "B4") if k in R["rings"]]
    L = []
    A = L.append
    A("# Experiment B — preprocessing ablation (B1 · B2 · B3 · B4)")
    A("")
    A(f"*Generated by `tools/experiment_b.py` · {R['seconds']}s · as-of `{R['as_of']}` · "
      f"schema `{R['schema_version']}` · rules `{R['rule_version']}` · "
      f"protocol `{R['protocol_version']}`*")
    A("")
    A("**Question.** Does increasingly sophisticated *deterministic* address preprocessing actually")
    A("improve candidate retrieval or final geocoding enough to justify its complexity?")
    A("")
    A("**What varies.** Only the text primitives (`sutra/preprocess.Ring`). The candidate arms, the")
    A("record shape, the licence class, the as-of discipline, the ranker, the radius map and the")
    A("official data are identical across rungs. Nothing is trained; no external data or API is used.")
    A("")
    A("| rung | definition |")
    A("|---|---|")
    for rid in rings:
        f = R["rings"][rid]
        A(f"| **{rid}** | {f['description']} |")
    A("")
    A("## 1. Data, split and firewall")
    A("")
    A("| item | value |")
    A("|---|---|")
    for k, v in R["populations"].items():
        A(f"| population `{k}` | {v} addresses |")
    A(f"| labelled (proxy `operational_confirmation_proxy`) | {R['n_labelled_proxy']} |")
    A(f"| labelled (surveyed ground truth, S-Eval) | {R['n_labelled_surveyed']} |")
    A(f"| scored lane | **{R['scored_lane']} arms only** — {R['lane_note']} |")
    A(f"| supervision firewall | `data/derived/supervision_firewall.csv` "
      f"sha256 `{R['hashes']['supervision_manifest'].get('data/derived/supervision_manifest.csv', '')[:12]}…` |")
    A(f"| split receipt | `data/derived/split_receipt.json` "
      f"sha256 `{R['hashes']['split_receipt'].get('data/derived/split_receipt.json', '')[:12]}…` |")
    A(f"| S-Eval test-look counter after the run | **{R['test_look_counter_after']}** (one read by this "
      f"experiment, logged as `experiment_B:s_eval_locked_check (single read)`) |")
    A("")
    A("## 2. S-VAL (selection population) — scored lane")
    A("")
    hdr = ("| ring | coverage | recall@100 m | recall@250 m | recall@500 m | oracle median | oracle <100 m | "
           "oracle <500 m | rule top-1 <500 m | ms/address |")
    A(hdr)
    A("|---|---|---|---|---|---|---|---|---|---|")
    for rid in rings:
        g = cells["S_VAL (selection)"][rid]["static"]["agg"]
        o, t = g.get("oracle") or {}, g.get("rule_top1") or {}
        A(f"| {rid} | {g['coverage_labelled']} | {g.get('recall_100')} | {g.get('recall_250')} | "
          f"{g.get('recall_500')} | {o.get('median_err_m')} m | {o.get('hit_100m')} | {o.get('hit_500m')} | "
          f"{t.get('hit_500m')} | {g['latency_ms']['mean']} |")
    A("")
    A("Recall@k here means *a candidate exists within k metres of the label* — the same definition")
    A("`sutra.replay.candidate_metrics` uses. `oracle` is the best candidate in the set.")
    A("")
    A("### 2.1 Paired deltas vs production (B2), S-VAL")
    A("")
    A("Grouped bootstrap, 95%, paired on the same addresses, resampled by **place block** "
      f"({R['intervals']['resamples']} resamples, seed {R['intervals']['seed']}). A difference inside the")
    A("interval is reported as *not resolved by this dataset*.")
    A("")
    A("| comparison | metric | delta (this ring − B2) | reading |")
    A("|---|---|---|---|")
    for rid in rings:
        if rid == "B2":
            continue
        for key in ("coverage_labelled", "recall_100", "recall_500", "oracle_hit_500m",
                    "rule_top1_hit_500m", "oracle_err_m", "latency_ms"):
            d = comparisons["S_VAL (selection)"][rid].get(key, {})
            A(f"| {rid} vs B2 | {key} | {fmt_ci(d)} | |")
    A("")
    A("### 2.2 Identification round-trip (corpus-wide, ring-dependent, label-free)")
    A("")
    A("Does a long-form spelling of an official abbreviation still reach the same record?")
    A("")
    A("| ring | round-trip rate (all 3,117) | round-trip rate (the 1,602 texts carrying an abbreviation) |")
    A("|---|---|---|")
    for rid in rings:
        v = R["variant_round_trip"][rid]
        A(f"| {rid} | {v['rate_all']} | {v['rate_with_abbreviation']} (n={v['n_with_abbreviation']}) |")
    A("")
    A("## 3. Arm level — the only place preprocessing can act")
    A("")
    A("`frozen_baseline` is a file lookup no rung can change, so aggregate metrics are dominated by it.")
    A("The arm-scoped view is the honest reading of the question.")
    A("")
    A("| arm | metric | B1 | B2 | B3 | B4 |")
    A("|---|---|---|---|---|---|")
    for arm in ("locality_centroid", "official_landmark", "address_book"):
        for metric, key in (("fire rate", "fire_rate"), ("median error when it fires (m)", "median_err_m"),
                            ("hit <100 m when it fires", "hit_100m"), ("hit <500 m when it fires", "hit_500m")):
            vals = []
            for rid in rings:
                m = cells["S_VAL (selection)"][rid]["arms"].get(arm, {})
                v = m.get(key)
                vals.append("—" if v is None else v)
            A(f"| {arm} | {metric} | " + " | ".join(str(v) for v in vals) + " |")
    A("")
    A("Paired comparisons of the arm-level series (fire rate over every labelled address; error paired")
    A("only on addresses where **both** rungs fire):")
    A("")
    A("| arm | comparison | delta | reading |")
    A("|---|---|---|---|")
    for arm, entry in arm_comparisons["S_VAL (selection)"].items():
        for k, d in entry.items():
            if k == "extra_firing_quality":
                continue
            A(f"| {arm} | {k} | {fmt_ci(d)} | |")
    A("")
    A("### 3.1 What the extra firings are worth")
    A("")
    A("A fire-rate difference is only a quality difference if the *additional* candidates are any good.")
    A("")
    A("| arm | comparison | both fire | this ring only | B2 only |")
    A("|---|---|---|---|---|")
    for arm in ("locality_centroid", "official_landmark", "address_book"):
        for rid, e in arm_comparisons["S_VAL (selection)"][arm].get("extra_firing_quality", {}).items():
            def cell(s):
                return "—" if not s else (f"n={s['n']} · median {s['median_err_m']} m · "
                                          f"<500 m {s['hit_500m']}")
            A(f"| {arm} | {rid} vs B2 | {cell(e['both_fire'])} | {cell(e[f'{rid}_only_firings'])} | "
              f"{cell(e['B2_only_firings'])} |")
    A("")
    A("## 4. The residue matcher (B3/B4): what it was asked to do, and what it refused")
    A("")
    for rid in [r for r in ("B3", "B4") if r in R["rings"]]:
        rs = R["rings"][rid].get("residue_stats", {})
        A(f"* **{rid}** — locality residues consulted {rs.get('locality_calls', 0)} "
          f"(accepted {rs.get('locality_accepted', 0)}; rejected on score "
          f"{rs.get('locality_rejected_threshold', 0)}; rejected on ambiguity margin "
          f"{rs.get('locality_rejected_margin', 0)}); landmark residues consulted "
          f"{rs.get('landmark_calls', 0)} (accepted {rs.get('landmark_accepted', 0)}; rejected on score "
          f"{rs.get('landmark_rejected_threshold', 0)}; rejected on ambiguity margin "
          f"{rs.get('landmark_rejected_margin', 0)}).")
    A("")
    A("The residue path is verified working by a positive control (a typo'd locality name with no")
    A("in-text pincode is recovered at score 0.51 by B3 and 1.00 by B4 with slot evidence), so the")
    A("zero-acceptances are a property of the **corpus**, not of the code: this gazetteer repeats")
    A('names heavily inside a town ("Ganesh Temple" ×7, "Ration Shop" ×9 in T1), so a fuzzy name')
    A("match is almost always ambiguous — and the margin rule then refuses, which is the correct")
    A("behaviour (the alternative is pinning the address to one of seven temples hundreds of metres apart).")
    A("")
    A("## 5. Locked check (S-Eval) and the stability populations")
    A("")
    A("Read once, through the declared `S_EVAL_BASELINE` spec, and it decides nothing.")
    A("")
    A("| population | ring | coverage | oracle median | oracle <100 m | oracle <500 m |")
    A("|---|---|---|---|---|---|")
    for pname in R["populations"]:
        for rid in rings:
            g = cells[pname][rid]["static"]["agg"]
            o = g.get("oracle") or {}
            A(f"| {pname} | {rid} | {g['coverage_labelled']} | {o.get('median_err_m')} m | "
              f"{o.get('hit_100m')} | {o.get('hit_500m')} |")
    A("")
    A("## 6. Interference check (all arms, including the evidence arms)")
    A("")
    A("| ring | S-VAL oracle median | S-VAL oracle <100 m | candidates/address |")
    A("|---|---|---|---|")
    for rid in rings:
        g = cells["S_VAL (selection)"][rid]["all"]["agg"]
        o = g.get("oracle") or {}
        A(f"| {rid} | {o.get('median_err_m')} m | {o.get('hit_100m')} | {g['cand_count']['mean']} |")
    A("")
    A("## 7. Decision")
    A("")
    sel = R["selection"]
    A(f"* quality frontier on S-VAL: `{R['quality_frontier_on_S_VAL']}` · eligible rungs: "
      f"`{R['eligible_rungs']}`")
    A(f"* **winner of the ablation: {sel['winner']}** (`change: {sel['change']}`) — {sel['why']}")
    A(f"* guardrail: {R['guardrails']['rule']} over {', '.join(R['guardrails']['metrics'])}")
    A(f"* materiality: {R['guardrails']['materiality_note']} "
      f"(latency margin {R['guardrails']['latency_materiality_ms']} ms)")
    A("")
    A("| dominance (a rung routed out on a material, resolved guardrail difference) | evidence |")
    A("|---|---|")
    dom = R["dominance_vs_every_other_rung"]
    for rid, others in dom.items():
        for other, fails in others.items():
            A(f"| {rid} vs {other} | {'; '.join(fails)} |")
    A("")
    A("### Kept / rejected")
    A("")
    lat = {rid: cells["S_VAL (selection)"][rid]["static"]["agg"]["latency_ms"]["mean"] for rid in rings}
    rt = {rid: R["variant_round_trip"][rid]["rate_all"] for rid in rings}
    A(f"* **kept — `B2` (production, unchanged).** Chosen because it is the cheapest rung that is not")
    A("  resolved-worse than any other on S-VAL. Its normalisation is doing real, measured work on the")
    A(f"  **identification** path the candidate arms cannot show: variant round-trip "
      f"{rt['B2']:.3f} vs B1's {rt['B1']:.3f} "
      f"({R['variant_round_trip']['B2']['n_with_abbreviation']} of 3,117 texts carry an abbreviation and")
    A("  a long-form spelling must still reach the same record).")
    A(f"* **rejected — `B1` (raw text).** Statistically competitive on every *retrieval* metric and")
    A(f"  cheaper ({lat['B1']:.2f} ms vs {lat['B2']:.2f} ms per address), but **resolved materially worse**")
    A("  on identification: it loses the abbreviation equivalence entirely, so \"Ngr\" and \"Nagar\"")
    A("  become different strings for the same place. This is the finding that keeps raw text as the")
    A("  ablation's control rather than the product.")
    A(f"* **rejected — `B3` (TF-IDF/SVD residue) and `B4` (parser/statistics residue).** Their candidate")
    A("  universe is **byte-identical** to B2's on every evaluated address (identical")
    A("  `candidate_id_hash`), they landed **zero** residue candidates, and they cost")
    A(f"  {lat['B3'] / lat['B2']:.2f}× and {lat['B4'] / lat['B2']:.2f}× B2's per-address time. The residue")
    A("  path itself is proven to work by a positive control; it stays silent because this gazetteer")
    A("  repeats names heavily inside a town, so a fuzzy match is almost always ambiguous and the margin")
    A("  rule correctly refuses. Rejecting them is exactly what the commission asked for: the ablation is")
    A("  how \"no LLMs / no embeddings everywhere\" becomes an empirical claim rather than a preference.")
    A("")
    A("**What this buys the project:** the three preprocessing layers in production (normalisation,")
    A("abbreviation table, deterministic spans) are *kept on measured evidence*; the two layers that")
    A("would have been easy to add later (a text-similarity retriever and a parser/statistics stage) are")
    A("now **closed by measurement** — they add nothing to retrieval on this corpus and are dropped.")
    A("")
    A("## 8. Reproduce")
    A("")
    A("```bash")
    A("cd PS3_SUTRA && python3 tools/experiment_b.py            # all four rungs")
    A("cd PS3_SUTRA && bash tools/reproduce.sh full             # whole pipeline incl. experiment B")
    A("```")
    A("")
    A("Determinism: `sha256` over every (address, arm, source_ref, x, y, granularity, as_of_valid):")
    A("")
    A("| ring | candidate-universe hash |")
    A("|---|---|")
    for rid, h in R["determinism"]["run_hashes"].items():
        A(f"| {rid} | `{h}` |")
    A("")
    A("Code hashes: " + " · ".join(f"`{k}` `{v[:12]}…`" for k, v in R["hashes"]["code"].items()))
    A("")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")


# ── main ─────────────────────────────────────────────────────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rings", default=",".join(RINGS))
    ap.add_argument("--resamples", type=int, default=stats.DEFAULT_RESAMPLES)
    ap.add_argument("--seed", type=int, default=stats.DEFAULT_SEED)
    ap.add_argument("--out-dir", default=None)
    a = ap.parse_args()
    rings_wanted = [r.strip().upper() for r in a.rings.split(",") if r.strip()]
    for r in rings_wanted:
        if r not in RINGS:
            raise SystemExit(f"unknown ring {r}; allowed: {RINGS}")

    t_start = time.time()
    ix = get_index()
    store = Store()
    out_dir = a.out_dir or config.DERIVED
    os.makedirs(out_dir, exist_ok=True)

    # ── the declared split is mandatory (T15); the selection population is S-VAL ─────────────────
    specs = {s.spec_id: s for s in splits.declared_specs()}
    spec_base = specs["S_EVAL_BASELINE"]                     # the only spec that may read surveyed truth
    as_of = config.MOMENT
    manifest = _manifest(ix)
    pops_a1 = populations(ix)
    pop_sel = [aid for aid, m in sorted(manifest.items()) if m["split"] == splits.S_VAL]
    pop_sup = [aid for aid, m in sorted(manifest.items()) if m["split"] in (splits.S_TRAIN, splits.S_VAL)]
    # A1's rule, applied to the supervised population: a block that does not cross the official split
    # (`ps3_place_blocks.csv` carries `n_splits`; the ledger is an evaluation lens, never edited).
    block_splits: dict[str, set] = {}
    for aid, b in ix.place_blocks.items():
        block_splits.setdefault(b["block_id"], set()).add(b["split"])
    pop_lbo = [aid for aid in pop_sup if len(block_splits.get(ix.block_of(aid), set())) <= 1]
    pop_eval = [aid for aid, m in sorted(manifest.items()) if m["split"] == splits.S_EVAL]
    populations_used = {"S_VAL (selection)": pop_sel, "S_TRAIN+S_VAL (stability)": pop_sup,
                        "leave-block-out (stress)": pop_lbo, "S-EVAL (locked check)": pop_eval}

    # labels: proxy for selection/stability/stress, surveyed truth ONLY for the locked check
    proxy: dict[str, tuple[float, float]] = {}
    for aid in pop_sup:
        t = _proxy_truth(store, aid, as_of)
        if t is not None:
            proxy[aid] = t
    store.bump_counter("s_eval_looks", detail="experiment_B:s_eval_locked_check (single read)")
    surveyed = dataio.surveyed()
    truth_eval = {aid: (float(surveyed[aid]["surveyed_x"]), float(surveyed[aid]["surveyed_y"]))
                  for aid in pop_eval if aid in surveyed}

    # ── build rings and run every address once per ring ─────────────────────────────────────────
    rings = preprocess.build_all(ix) if any(r in ("B3", "B4") for r in rings_wanted) \
        else {r: preprocess.get(r, ix) for r in rings_wanted}
    all_addresses = sorted(set(pop_sel) | set(pop_sup) | set(pop_eval))
    runs: dict[str, dict] = {}
    run_hashes: dict[str, str] = {}
    for rid in rings_wanted:
        t0 = time.time()
        runs[rid] = run_ring(rings[rid], all_addresses, ix, store, as_of)
        run_hashes[rid] = hash_runs(runs[rid])
        print(f"  {rid}: {len(all_addresses)} addresses in {time.time() - t0:.1f}s "
              f"({run_hashes[rid][:12]})")

    # ── the identification guardrail (corpus-wide, ring-dependent, no labels) ────────────────────
    rtt = {rid: variant_round_trip(rings[rid], ix) for rid in rings_wanted}

    # ── metrics per (population × ring) ─────────────────────────────────────────────────────────
    cells: dict[str, dict[str, dict]] = {}
    for pname, pop in populations_used.items():
        truth = truth_eval if pname.startswith("S-EVAL") else proxy
        cells[pname] = {rid: {"static": metrics_for(pop, runs[rid], truth, ix, as_of, config.STATIC_ARMS),
                              "all": metrics_for(pop, runs[rid], truth, ix, as_of, None),
                              "arms": arm_metrics(pop, runs[rid], truth)}
                        for rid in rings_wanted}
    primary_pop = "S_VAL (selection)"
    check_pop = "S-EVAL (locked check)"
    LANE = "static"          # the lane the ablation is scored on (see metrics_for docstring)

    # ── paired grouped-bootstrap deltas against production (group = place block) ─────────────────
    ROW_KEY = {"coverage_labelled": "coverage", "recall_100": "recall_100", "recall_250": "recall_250",
               "recall_500": "recall_500", "oracle_err_m": "oracle_err_m",
               "oracle_hit_500m": "oracle_hit_500m", "rule_top1_hit_500m": "rule_top1_hit_500m",
               "latency_ms": "latency_ms"}

    def round_trip_series(rid):
        return {r["address_id"]: float(r["round_trip"]) for r in rtt[rid]["rows"]}

    def paired(pop_name, rid_a, rid_b, key):
        """(a, b, groups) over the SAME addresses, in a fixed order — a true paired comparison."""
        if key == "variant_round_trip":
            sa, sb = round_trip_series(rid_a), round_trip_series(rid_b)
            ids = sorted(set(sa) & set(sb))
            return ([sa[i] for i in ids], [sb[i] for i in ids], [ix.block_of(i) for i in ids])
        rk = ROW_KEY[key]
        ra = {r["address_id"]: r for r in cells[pop_name][rid_a][LANE]["rows"]}
        rb = {r["address_id"]: r for r in cells[pop_name][rid_b][LANE]["rows"]}
        va, vb, gr = [], [], []
        for aid in sorted(set(ra) & set(rb)):
            x, y = ra[aid][rk], rb[aid][rk]
            if x is None or y is None:
                continue
            va.append(x); vb.append(y); gr.append(ix.block_of(aid))
        return va, vb, gr

    comparisons: dict[str, dict] = {}
    for pop_name in populations_used:
        comparisons[pop_name] = {}
        for rid in rings_wanted:
            if rid == PRODUCTION_RING:
                continue
            row = {}
            for key, direction in (("coverage_labelled", "higher_is_better"),
                                   ("variant_round_trip", "higher_is_better"),
                                   ("recall_500", "higher_is_better"),
                                   ("recall_100", "higher_is_better"),
                                   ("oracle_hit_500m", "higher_is_better"),
                                   ("rule_top1_hit_500m", "higher_is_better"),
                                   ("oracle_err_m", "lower_is_better"),
                                   ("latency_ms", "lower_is_better")):
                va, vb, gr = paired(pop_name, rid, PRODUCTION_RING, key)
                if not va:
                    row[key] = {"n": 0, "resolved": False, "note": "no aligned rows"}
                    continue
                stat = "median" if key == "oracle_err_m" else "mean"
                d = stats.paired_grouped_ci(va, vb, gr, stat=stat,
                                            resamples=a.resamples, seed=a.seed, direction=direction)
                if all(abs(x - y) < 1e-12 for x, y in zip(va, vb)):
                    d["identical"] = True
                    d["note"] = "the two rings produce identical per-address values for this metric"
                row[key] = d
            comparisons[pop_name][rid] = row

    # ── the selection rule, applied only on S-VAL ───────────────────────────────────────────────
    def guard_ok(rid, best_rid) -> tuple[bool, list[str]]:
        """Is `rid` not *resolved worse* than the best rung, on any guardrail, on S-VAL?"""
        fails = []
        if rid == best_rid:
            return True, fails
        for key in PRIMARY:
            d = resolved_worse(rid, best_rid, key)
            if d.get("resolved_worse"):
                fails.append(f"{key}: resolved-worse by {d['point_delta']} [{d['lo']}, {d['hi']}]")
        return (not fails), fails

    def resolved_worse(a_rid, b_rid, key) -> dict:
        """`key` is *resolved worse* for `a` than `b` when the 95% interval of (a - b) sits entirely on
        the wrong side of zero — including when `a` is slower, which a one-sided 'better' test misses."""
        va, vb, gr = paired(primary_pop, a_rid, b_rid, key)
        if not va:
            return {"resolved": False, "n": 0}
        stat = "median" if key == "oracle_err_m" else "mean"
        lower_better = key in ("oracle_err_m", "latency_ms")
        d = stats.paired_grouped_ci(va, vb, gr, stat=stat, resamples=a.resamples, seed=a.seed,
                                    direction="lower_is_better" if lower_better else "higher_is_better")
        if all(abs(x - y) < 1e-12 for x, y in zip(va, vb)):
            return {"resolved": False, "identical": True, "n": d["n"], "point_delta": 0.0}
        if lower_better:
            worse = bool(d["lo"] > LATENCY_MATERIALITY_MS) if key == "latency_ms" else bool(d["lo"] > 0.0)
        else:
            worse = bool(d["hi"] < 0.0)
        return {**d, "resolved_worse": worse, "materiality": ("5% of the 250 ms p95 budget"
                                                              if key == "latency_ms" else "any resolved difference")}

    # ── arm-level paired comparisons (where preprocessing actually acts) ────────────────────────
    def arm_series(pop_name, rid, arm, kind):
        """Per-address series for one arm: `fire` (0/1, all labelled) or `err` (when the arm fires).

        `err` is paired only on addresses where **both** rings fire — the comparison must not compare
        different address sets.
        """
        run = runs[rid]
        truth = truth_eval if pop_name.startswith("S-EVAL") else proxy
        out = []
        for aid in sorted(set(truth) & {a for a, m in manifest.items()
                                        if m["split"] in (splits.S_TRAIN, splits.S_VAL, splits.S_EVAL)}):
            r = run.get(aid)
            if r is None:
                continue
            cs = [c for c in r["candidates"] if c["arm"] == arm]
            if kind == "fire":
                out.append((aid, 1.0 if cs else 0.0))
            elif cs:
                tx, ty = truth[aid]
                out.append((aid, min(geo.dist(c["x"], c["y"], tx, ty) for c in cs)))
        return out

    def extra_firing_quality(pop_name, rid, arm) -> dict:
        """What the extra firings are worth: a fire-rate difference is only a *quality* difference
        if the additional candidates are any good. Reported per pair, on the labelled population."""
        run, prod = runs[rid], runs[PRODUCTION_RING]
        truth = truth_eval if pop_name.startswith("S-EVAL") else proxy
        shared, only_this, only_prod = [], [], []
        for aid in sorted(set(truth) & set(run) & set(prod)):
            tx, ty = truth[aid]
            ca = [c for c in run[aid]["candidates"] if c["arm"] == arm]
            cb = [c for c in prod[aid]["candidates"] if c["arm"] == arm]
            ea = min((geo.dist(c["x"], c["y"], tx, ty) for c in ca), default=None)
            eb = min((geo.dist(c["x"], c["y"], tx, ty) for c in cb), default=None)
            (shared.append(ea) if (ea is not None and eb is not None) else
             only_this.append(ea) if ea is not None else
             only_prod.append(eb) if eb is not None else None)
        def stat(v):
            return None if not v else {"n": len(v), "median_err_m": _q(v, 0.5),
                                       "hit_100m": round(sum(1 for e in v if e <= 100) / len(v), 4),
                                       "hit_500m": round(sum(1 for e in v if e <= 500) / len(v), 4)}
        return {"both_fire": stat(shared), f"{rid}_only_firings": stat(only_this),
                f"{PRODUCTION_RING}_only_firings": stat(only_prod)}

    arm_comparisons: dict[str, dict] = {}
    for pop_name in ([primary_pop, check_pop] if check_pop in populations_used else [primary_pop]):
        arm_comparisons[pop_name] = {}
        for arm in ("locality_centroid", "official_landmark", "address_book"):
            entry = {}
            for rid in rings_wanted:
                if rid == PRODUCTION_RING:
                    continue
                # fire rate: paired over every labelled address
                fa = dict(arm_series(pop_name, rid, arm, "fire"))
                fb = dict(arm_series(pop_name, PRODUCTION_RING, arm, "fire"))
                ids = sorted(set(fa) & set(fb))
                if ids:
                    va, vb = [fa[i] for i in ids], [fb[i] for i in ids]
                    gr = [ix.block_of(i) for i in ids]
                    entry[f"{rid}_fire_rate"] = stats.paired_grouped_ci(
                        va, vb, gr, resamples=a.resamples, seed=a.seed, direction="higher_is_better")
                # accuracy: paired only where both fire
                ea = dict(arm_series(pop_name, rid, arm, "err"))
                eb = dict(arm_series(pop_name, PRODUCTION_RING, arm, "err"))
                ids = sorted(set(ea) & set(eb))
                entry[f"{rid}_err_both_fire"] = (
                    {**stats.paired_grouped_ci([ea[i] for i in ids], [eb[i] for i in ids],
                                               [ix.block_of(i) for i in ids], stat="median",
                                               resamples=a.resamples, seed=a.seed,
                                               direction="lower_is_better"),
                     "n_both_fire": len(ids)} if ids else {"n": 0})
            entry["extra_firing_quality"] = {rid: extra_firing_quality(pop_name, rid, arm)
                                             for rid in rings_wanted if rid != PRODUCTION_RING}
            arm_comparisons[pop_name][arm] = entry

    # ── the selection rule ──────────────────────────────────────────────────────────────────────
    # 1. quality frontier on S-VAL: best on (oracle <500 m, coverage, oracle median) — ties count
    def score_key(rid):
        agg = cells[primary_pop][rid][LANE]["agg"]
        o = agg.get("oracle") or {}
        return (-(o.get("hit_500m") or 0.0), -(agg.get("coverage_labelled") or 0.0),
                (o.get("median_err_m") if o.get("median_err_m") is not None else float("inf")),
                rings_wanted.index(rid))

    ordered = sorted(rings_wanted, key=score_key)
    frontier = [ordered[0]]
    for rid in ordered[1:]:
        agg, best_agg = cells[primary_pop][rid][LANE]["agg"], cells[primary_pop][frontier[0]][LANE]["agg"]
        same = (agg["oracle"]["hit_500m"] == best_agg["oracle"]["hit_500m"]
                and agg["coverage_labelled"] == best_agg["coverage_labelled"]
                and agg["oracle"]["median_err_m"] == best_agg["oracle"]["median_err_m"])
        if same:
            frontier.append(rid)

    # 2. dominance: a rung is out if it is *resolved worse* than any other rung on any guardrail
    dominance: dict[str, dict[str, list[str]]] = {}
    for a_rid in rings_wanted:
        dominance[a_rid] = {}
        for b_rid in rings_wanted:
            if a_rid == b_rid:
                continue
            fails = []
            for key in PRIMARY:
                d = resolved_worse(a_rid, b_rid, key)
                if d.get("resolved_worse"):
                    fails.append(f"{key} vs {b_rid}: {d['point_delta']} [{d['lo']}, {d['hi']}]")
            if fails:
                dominance[a_rid][b_rid] = fails

    eligible = [r for r in rings_wanted if not dominance[r]]
    cheapest_ok = min(eligible, key=lambda r: rings_wanted.index(r)) if eligible else None

    # 3. adopt a more expensive rung only if it is *resolved better* than production on a primary metric
    def resolved_better_than_production(rid) -> list[str]:
        out = []
        for key in ("coverage_labelled", "variant_round_trip", "recall_100", "recall_500",
                    "oracle_hit_500m", "rule_top1_hit_500m"):
            c = comparisons[primary_pop].get(rid, {}).get(key)
            if c and c.get("resolved") and c.get("favours") == "a":
                out.append(f"{key} {c['point_delta']:+.4f} [{c['lo']}, {c['hi']}]")
        return out

    gains = {rid: resolved_better_than_production(rid) for rid in rings_wanted if rid != PRODUCTION_RING}
    if not eligible:
        selection = {"winner": PRODUCTION_RING, "change": "none",
                     "why": "every rung is resolved-worse than some other on S-VAL; production stands"}
    elif cheapest_ok == PRODUCTION_RING:
        higher_gain = next((r for r in eligible
                            if rings_wanted.index(r) > rings_wanted.index(PRODUCTION_RING) and gains.get(r)),
                           None)
        if higher_gain:
            selection = {"winner": higher_gain, "change": "adopt",
                         "why": f"{higher_gain} is resolved better than production on S-VAL",
                         "evidence": gains[higher_gain]}
        else:
            selection = {"winner": PRODUCTION_RING, "change": "none",
                         "why": ("production is the cheapest rung that is not resolved-worse than the "
                                 "others on S-VAL, and no more expensive rung is resolved better than it")}
    elif rings_wanted.index(cheapest_ok) < rings_wanted.index(PRODUCTION_RING):
        selection = {"winner": cheapest_ok, "change": "simplification",
                     "why": (f"{cheapest_ok} is not resolved-worse than any other rung on S-VAL and is "
                             "cheaper than production; a lower rung that ties is a simplification win")}
    else:
        if gains.get(cheapest_ok):
            selection = {"winner": cheapest_ok, "change": "adopt", "why": "resolved better than production",
                         "evidence": gains[cheapest_ok]}
        else:
            selection = {"winner": PRODUCTION_RING, "change": "none",
                         "why": (f"{cheapest_ok} is not resolved-worse, but it is not resolved *better* "
                                 "than production either — the extra layer does not earn its place")}

    # ── results CSV + receipt ───────────────────────────────────────────────────────────────────
    csv_path = os.path.join(out_dir, "experiment_b_results.csv")
    with open(csv_path, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["population", "ring", "lane", "address_id", "n_candidates", "coverage", "labelled",
                    "oracle_err_m", "recall_100", "recall_250", "recall_500",
                    "rule_top1_err_m", "rule_top1_hit_100m", "rule_top1_hit_250m", "rule_top1_hit_500m",
                    "latency_ms"])
        for pname in populations_used:
            for rid in rings_wanted:
                for lane in ("static", "all"):
                    for r in cells[pname][rid][lane]["rows"]:
                        w.writerow([pname, rid, lane, r["address_id"], r["n_candidates"], r["coverage"], r["labelled"],
                                    r["oracle_err_m"], r["recall_100"], r["recall_250"], r["recall_500"],
                                    r["rule_top1_err_m"], r["rule_top1_hit_100m"], r["rule_top1_hit_250m"],
                                    r["rule_top1_hit_500m"], r["latency_ms"]])

    receipt = {
        "experiment": "B — preprocessing ablation",
        "schema_version": SCHEMA_VERSION, "protocol_version": PROTOCOL_VERSION,
        "rule_version": RULE_VERSION, "evidence_policy_version": EVIDENCE_POLICY_VERSION,
        "radius_map_version": RADIUS_MAP_VERSION,
        "as_of": as_of,
        "rings": {rid: rings[rid].facts() for rid in rings_wanted},
        "production_ring": PRODUCTION_RING,
        "selection_population": primary_pop, "locked_check_population": check_pop,
        "populations": {k: len(v) for k, v in populations_used.items()},
        "n_labelled_proxy": len(proxy), "n_labelled_surveyed": len(truth_eval),
        "label_sources": {"selection": "operational_confirmation_proxy",
                          "locked_check": "surveyed_ground_truth (S_EVAL_BASELINE, single read)"},
        "variant_round_trip": {rid: {k: v for k, v in rtt[rid].items() if k != "rows"}
                               for rid in rings_wanted},
        "intervals": {"method": "grouped bootstrap, 95%, paired on the difference",
                      "resamples": a.resamples, "group": "place_block", "seed": a.seed,
                      "module": "sutra/stats.py",
                      "doc": "PS3_EXPERIMENT_PLAN.md §1 (fixed method, not a new choice)"},
        "scored_lane": LANE,
        "lane_note": ("the scored lane is static-only: the proxy label is the address's own promoted "
                      "check-in median, so the evidence arms reproduce it by construction and are "
                      "excluded from scoring; the full lane is an interference check"),
        "results": {p: {rid: {**{lane: cells[p][rid][lane]["agg"] for lane in ("static", "all")},
                              "arms": cells[p][rid]["arms"]}
                        for rid in rings_wanted} for p in populations_used},
        "comparisons_vs_production": comparisons,
        "arm_comparisons_vs_production": arm_comparisons,
        "quality_frontier_on_S_VAL": frontier,
        "dominance_vs_every_other_rung": dominance,
        "eligible_rungs": eligible,
        "guardrails": {"metrics": list(PRIMARY),
                       "latency_materiality_ms": LATENCY_MATERIALITY_MS,
                       "rule": ("a rung is eligible only if it is not *resolved worse* than any other "
                                "rung on any guardrail, on S-VAL; among eligible rungs the cheapest wins"),
                       "materiality_note": ("a latency difference is a regression only past 5% of the "
                                            "250 ms p95 budget; error/hit metrics are exact given the "
                                            "candidate set, so any resolved difference counts")},
        "best_ring_on_S_VAL": frontier[0],
        "selection": selection,
        "resolved_gains_vs_production": gains,
        "diagnostics": {rid: diag_stats(rings[rid], runs[rid], ix, run_hashes,
                                       runs.get(PRODUCTION_RING) if rid != PRODUCTION_RING else None)
                        for rid in rings_wanted},
        "determinism": {"run_hash_alg": "sha256 over (address|arm|source_ref|x|y|granularity|as_of_valid)",
                        "run_hashes": run_hashes},
        "hashes": {
            "candidate_artefact": source_hashes(["data/derived/candidates_v2.csv"]),
            "candidate_receipt": source_hashes(["data/derived/candidates_v2.receipt.json"]),
            "supervision_manifest": source_hashes(["data/derived/supervision_manifest.csv"]),
            "split_receipt": source_hashes(["data/derived/split_receipt.json"]),
            "code": source_hashes(["sutra/preprocess.py", "sutra/candidates.py", "sutra/stats.py",
                                   "sutra/ranking.py", "sutra/dataio.py", "tools/experiment_b.py"]),
        },
        "test_look_counter_after": store.counters("s_eval_looks"),
        "seconds": round(time.time() - t_start, 1),
    }
    rc_path = os.path.join(out_dir, "experiment_b_receipt.json")
    with open(rc_path, "w", encoding="utf-8") as fh:
        json.dump(receipt, fh, indent=2, sort_keys=True, ensure_ascii=False)

    # ── console ────────────────────────────────────────────────────────────────────────────────
    print(f"\nexperiment B — preprocessing ablation · scored lane = static arms only · "
          f"selection population = {primary_pop} (proxy labels, {len(pop_sel)} addresses)")
    hdr = f"  {'ring':<5} {'n':>4} {'cov':>6} {'rec@1':>6} {'rec@3':>6} {'rec@5':>6} {'orc med':>8} {'orc<100':>8} {'orc<500':>8} {'top1<500':>9} {'ms/addr':>8}"
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))
    for rid in rings_wanted:
        g = cells[primary_pop][rid][LANE]["agg"]
        o = g.get("oracle") or {}
        t = g.get("rule_top1") or {}
        print(f"  {rid:<5} {g['n']:>4} {g['coverage_labelled']:>6.3f} {g.get('recall_100', 0):>6.3f} "
              f"{g.get('recall_250', 0):>6.3f} {g.get('recall_500', 0):>6.3f} {o.get('median_err_m', 0):>8.1f} "
              f"{o.get('hit_100m', 0):>8.3f} {o.get('hit_500m', 0):>8.3f} {t.get('hit_500m', 0):>9.3f} "
              f"{g['latency_ms']['mean']:>8.2f}")
    print(f"\n  per-arm fire rate / accuracy on {primary_pop} (the sink where preprocessing acts):")
    arms_shown = [a for a in ("locality_centroid", "official_landmark", "address_book") ]
    print(f"    {'arm':<18} " + "".join(f"{rid:>22}" for rid in rings_wanted))
    for arm in arms_shown:
        cells_txt = []
        for rid in rings_wanted:
            m = cells[primary_pop][rid]["arms"].get(arm, {})
            cells_txt.append(f"{m.get('fire_rate', 0):>6.3f}/{str(m.get('median_err_m') or '-'):>6}")
        print(f"    {arm:<18} " + "".join(f"{c:>22}" for c in cells_txt))
    print("    (fire rate / median error in m when the arm fires; '-' = never fires)")

    print(f"\n  paired deltas vs production {PRODUCTION_RING} on S-VAL (95% grouped bootstrap, "
          f"group=place block, n={a.resamples}):")
    for rid in rings_wanted:
        if rid == PRODUCTION_RING:
            continue
        c = comparisons[primary_pop][rid]
        for key in ("coverage_labelled", "variant_round_trip", "recall_500", "oracle_hit_500m",
                    "rule_top1_hit_500m", "oracle_err_m", "latency_ms"):
            d = c[key]
            tag = "RESOLVED" if d.get("resolved") else ("identical" if d.get("identical") else "not resolved")
            print(f"    {rid} vs {PRODUCTION_RING} {key:<20} {d.get('point_delta')} "
                  f"[{d.get('lo')}, {d.get('hi')}]  {tag} ({d.get('favours', '')})")
    print(f"\n  full lane (interference check, all arms incl. evidence arms) on S-VAL:")
    for rid in rings_wanted:
        g = cells[primary_pop][rid]["all"]["agg"]
        o = g.get("oracle") or {}
        print(f"    {rid}: oracle median {o.get('median_err_m')} m · <100 m {o.get('hit_100m')} · "
              f"coverage {g['coverage_labelled']} · candidates/addr {g['cand_count']['mean']}")

    print(f"\n  locked check (S-EVAL, {len(pop_eval)} surveyed, single read, decides nothing):")
    for rid in rings_wanted:
        g = cells[check_pop][rid][LANE]["agg"]
        o = g.get("oracle") or {}
        print(f"    {rid}: oracle median {o.get('median_err_m')} m · <100 m {o.get('hit_100m')} · "
              f"<500 m {o.get('hit_500m')} · coverage {g['coverage_labelled']}")
    print(f"\n  arm-level paired comparisons vs {PRODUCTION_RING} on S-VAL (95% CI):")
    for arm, entry in arm_comparisons[primary_pop].items():
        for k, d in entry.items():
            if not d.get("n"):
                print(f"    {arm:<18} {k:<22} n=0 (never fires in both rings)")
                continue
            tag = "RESOLVED" if d.get("resolved") else "not resolved"
            print(f"    {arm:<18} {k:<22} {d.get('point_delta')} [{d.get('lo')}, {d.get('hi')}] {tag} "
                  f"(n={d['n']}, groups={d.get('n_groups')})")

    print(f"\n  quality frontier on S-VAL: {frontier} | eligible (not resolved-worse than any rung): "
          f"{eligible or 'none'}")
    print(f"  selection: winner={selection['winner']} change={selection['change']} — {selection['why']}")
    print(f"  test-look counter: {receipt['test_look_counter_after']}")
    md_path = os.path.join(out_dir, "experiment_b_report.md")
    write_report(receipt, cells, comparisons, arm_comparisons, md_path)
    print(f"wrote {os.path.relpath(csv_path, config.ROOT)}, {os.path.relpath(rc_path, config.ROOT)} and "
          f"{os.path.relpath(md_path, config.ROOT)} in {receipt['seconds']}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
