# SUTRA — field evidence / memory decision policy
**FINAL_EVIDENCE_MEMORY_POLICY · emp-v1 · sha256 `a110f08962993e3c…`** · frozen /home/user/PS3_SUTRA/data/derived/final_evidence_memory_policy.json
_as-of 2026-06-01T00:00:00Z · pool 292 (S-TRAIN+S-VAL) · S-VAL 69 · temporal cuts ['2026-05-01', '2026-05-15'] · tool run 312.3s · outbound socket attempts 0._
This is the last precision task before the UI/UX phase. No new model, no new arm, no new feature: one question — **when may a prior observation become a candidate at all?** Everything below is measured on the official dataset. The S-Eval truth was read only after the policy was frozen and hashed, and every increment of that counter is disclosed in §7.
## 1 · Baseline (the shipped policy)
The shipped rule selects `field_evidence` on 263 and `memory` on 29 of 292 pool rows. When the memory arm is chosen it is weak (`<100 0.1724`, median 337.9 m) while the field-evidence arm is strong (`<100 0.9582`).
| population | n | <100 m | <250 m | <500 m | median |
|---|---|---|---|---|---|
| pool (proxy label, circular) | 292 | 0.8801 | 0.9349 | 0.9658 | 0.0 |
| S-VAL (proxy label) | 69 | 0.8696 | 0.942 | 0.9565 | 0.0 |
| temporal 2026-05-15 | 237 | 0.8903 | 0.9451 | 0.9873 | 8.2 |
| temporal 2026-05-01 | 271 | 0.8339 | 0.9262 | 1.0 | 8.4 |
## 2 · Warm failure taxonomy (the 292-row pool)
10 rows > 500 m under the shipped policy.
| class | n | what the failure actually is |
|---|---|---|
| **memory re-wraps the pin** | 7 | the emitted memory candidate is within 5 m of the vendor pin, i.e. it carries the pin's own error while presenting itself as learned place memory — and it outranks the field evidence because `primary_eligible` adds +0.08 |
| single check-in, no consolidation | 3 | only one usable check-in, taken at the wrong place / weak accuracy; prior status CONTESTED |
| address | selected arm | selected err | memory err | memory evidence-derived | best single err | status | tier | obs | collectors |
|---|---|---|---|---|---|---|---|---|---|
| AD000037 | memory | 1302.4 m | 1302.4 m | False | 152.9 m | STABLE | CONFIRMED | 4 | 2 |
| AD000526 | memory | 852.1 m | 852.1 m | False | 588.2 m | STABLE | CONFIRMED | 4 | 2 |
| AD000624 | memory | 1392.8 m | 1392.8 m | False | 148.7 m | STABLE | CONFIRMED | 2 | 1 |
| AD000779 | memory | 1270.5 m | 1270.5 m | False | 1159.3 m | STABLE | CONFIRMED | 5 | 2 |
| AD001880 | memory | 826.7 m | 826.7 m | False | 736.4 m | STABLE | CONFIRMED | 3 | 1 |
| AD002070 | field_evidence | 2011.3 m | 1838.6 m | False | 2011.3 m | CONTESTED | APPROXIMATE | 2 | 2 |
| AD002415 | field_evidence | 2540.8 m | 2668.1 m | False | 2534.7 m | CONTESTED | APPROXIMATE | 3 | 2 |
| AD002416 | field_evidence | 1970.5 m | 1613.9 m | False | 1970.5 m | CONTESTED | APPROXIMATE | 2 | 2 |
| AD002696 | memory | 624.4 m | 624.4 m | False | 156.0 m | STABLE | CONFIRMED | 5 | 2 |
| AD002711 | memory | 794.8 m | 794.8 m | False | 0.0 m | STABLE | CONFIRMED | 4 | 3 |
**What the frozen policy does to these ten.** It removes the memory class entirely: four of the seven memory rows become correct (AD000037 1302.4 -> 152.9 m, AD000624 1392.8 -> 148.7 m, AD002696 624.4 -> 156.0 m, AD002711 794.8 -> 0.0 m). The other three fall back to field evidence that is itself wrong (AD000526 588.2 m, AD000779 1159.3 m, AD001880 736.4 m) — a single-check-in quality problem, not a memory problem — and the three field_evidence rows (AD002070, AD002415, AD002416, all CONTESTED) are untouched by design. No row in this table changes from correct to incorrect.
**Root cause.** `memory_candidates()` read the previous belief's *candidate coordinate*: when the previous winner was the pin, the pin came back as memory, now marked `primary_eligible` (prior tier CONFIRMED) and therefore ahead of the real check-in. Memory was not remembering evidence; it was remembering a pin and calling it memory.
## 3 · Policy challengers (S-TRAIN/S-VAL, temporal holdout, LBO)
| policy | pool <500 | pool <100 | S-VAL <500 | S-VAL <100 | T0=05-15 <500 | T0=05-15 <100 | paired vs P0 (pool) |
|---|---|---|---|---|---|---|---|
| `P0 shipped` | 0.9658 | 0.8801 | 0.9565 | 0.8696 | 0.9873 | 0.8903 | baseline |
| `P1a memory not eligible when pin-derived` | 0.9795 | 0.9212 | 0.9855 | 0.8986 | 0.9873 | 0.8945 | +0.0137 [+0.0034, +0.0280] challenger better |
| `P1b memory not emitted when pin-derived` | 0.9795 | 0.9212 | 0.9855 | 0.8986 | 0.9873 | 0.8945 | +0.0137 [+0.0034, +0.0280] challenger better |
| `P2 single quality tiering` | 0.9658 | 0.8801 | 0.9565 | 0.8696 | 0.9873 | 0.8776 | +0.0000 [+0.0000, +0.0000] identical |
| `P2b tiering + at most 2 singles` | 0.9384 | 0.8185 | 0.913 | 0.7681 | 0.9831 | 0.865 | -0.0274 [-0.0478, -0.0102] P0 better |
| `P2c tiering + at most 1 single` | 0.9349 | 0.7945 | 0.9275 | 0.7391 | 0.9789 | 0.8439 | -0.0308 [-0.0521, -0.0135] P0 better |
| `P3a drop singles with GPS > 50 m` | 0.9658 | 0.8801 | 0.9565 | 0.8696 | 0.9873 | 0.8903 | +0.0000 [+0.0000, +0.0000] identical |
| `P3b drop singles with GPS > 100 m` | 0.9658 | 0.8801 | 0.9565 | 0.8696 | 0.9873 | 0.8903 | +0.0000 [+0.0000, +0.0000] identical |
| `P4 tiering + memory evidence-derived` | 0.9795 | 0.9212 | 0.9855 | 0.8986 | 0.9873 | 0.8819 | +0.0137 [+0.0034, +0.0280] challenger better |
| `P5 on-demand prior (projection fix only)` | 0.9658 | 0.8801 | 0.9565 | 0.8696 | 0.9662 | 0.6498 | +0.0000 [+0.0000, +0.0000] identical |
| `P6 on-demand prior + memory evidence-derived` | 0.9795 | 0.9212 | 0.9855 | 0.8986 | 0.9873 | 0.8945 | +0.0137 [+0.0034, +0.0280] challenger better |
| `P7 on-demand + evidence-derived + tiering` | 0.9795 | 0.9212 | 0.9855 | 0.8986 | 0.9873 | 0.8819 | +0.0137 [+0.0034, +0.0280] challenger better |
| `P8 quality tie-break only` | 0.9658 | 0.8733 | 0.9565 | 0.8696 | 0.9831 | 0.8692 | +0.0000 [+0.0000, +0.0000] identical |
| `P9 evidence-derived memory + quality tie-break` | 0.9795 | 0.9144 | 0.9855 | 0.8986 | 0.9831 | 0.8734 | +0.0137 [+0.0034, +0.0280] challenger better |
| `P_FINAL (frozen policy)` | 0.9795 | 0.9212 | 0.9855 | 0.8986 | 0.9873 | 0.8945 | +0.0137 [+0.0034, +0.0280] challenger better |
Intervals are paired grouped bootstraps over place blocks. Readings that do not clear the interval are reported as *not resolved by this dataset* — never as an improvement.
**What each challenger taught us.**
- *Quality tiering of singles*: no effect — the competing singles carry **equal weight**, so relabelling their granularity cannot separate them.
- *Fewer singles (<=2 / <=1)*: regression. The third check-in sometimes is the right one.
- *GPS-accuracy gates (50 / 100 m)*: no effect; no single in the pool exceeds them.
- *Quality-ordered tie-break* (order equal scores by the generator's quality order instead of the id hash): **regression** on S-VAL and both temporal cuts. The shipped arbitrary tie-break is no worse than the weight order — the 22-row ordering defect is real, but weight is not a usable proxy for correctness.
- *On-demand prior alone* (materialise memory at every as-of instant, without the emit rule): temporal `<100` collapses 0.8903 -> 0.6498. This is the cleanest evidence that pin-derived memory is *harmful* rather than merely useless.
## 4 · The frozen policy
```json
{
 "version": "emp-v1",
 "memory": {
  "eligibility_rule": "prior tier in (CONFIRMED, PROBABLE) AND the prior is evidence-derived",
  "emit_rule": "evidence-derived priors only (MEMORY_EMIT=evidence_derived_only)",
  "evidence_derived_definition": "the prior belief's candidate coordinate comes from accumulated field evidence (armed `field_evidence`, provenance built_from='store observations'); a prior that merely re-wraps a static arm (pin/locality/town/landmark/address-book) is NOT memory and is not emitted",
  "place_keying": "unchanged: ix.place_blocks; account identity never maps to a coordinate",
  "prior_source": "belief recomputed at the query instant when no belief row was materialised there (MEMORY_ON_DEMAND_BELIEF) \u2014 belief is a pure function of the store, the stored row is a projection"
 },
 "field_evidence": {
  "consolidated_median": "unchanged: emitted when >=2 promoting independent observations agree within CONSISTENCY_BAND_M=30",
  "quality_gates": null,
  "singles_emitted": 3,
  "singles_primary_eligible": false,
  "tie_break": "candidate_id (shipped; the quality-ordered tie-break lost on S-VAL and temporal)"
 },
 "contradiction_behavior": "unchanged: CONTESTED when strong observations separate by more than 2x radius; memory never overrides a contradiction, it is only ever demoted or withheld",
 "staleness_behavior": "unchanged: STALE when the newest positive is older than 365 days; no invented decay, no age-based reweighting",
 "negative_evidence_safety": "unchanged: a negative observation can never relocate a coordinate (demote / widen / VERIFY_FIRST only); graded negatives accumulate at NEG_ACCUMULATION_MIN=2"
}
```
### Promotion-gate verdict (recorded before the S-Eval read)
- **(1) S-VAL** — NOT RESOLVED on S-VAL alone: +0.0290 [+0.0000, +0.0725] — the interval touches zero at n=69 (2 rows of 69)
- **(1) supervision pool (S-TRAIN+S-VAL)** — resolved: +0.0137 [+0.0034, +0.0280] over n=292
- **(2) no regression** — cleared on the product lane and on every measured population (product coverage 100/100 unchanged, no new coordinates, no negative-evidence relocation, contradiction census unchanged, candidate set smaller so latency cannot increase), with ONE deliberate exception stated plainly: the warm lane's memory licence narrows (S-Eval warm answers 45 -> 31). All 14 withheld answers were pin-derived, and those addresses still receive the pin answer with its pin radius and VERIFY_FIRST semantics — the product lane is bit-identical.
- **(3) leave-block-out / temporal** — cleared: LBO blocks improved 4 / worse 0; both temporal cuts identical (0 rows changed)
- **(4) no S-Eval tuning** — cleared: the freeze and its hash precede the first S-Eval read; no parameter was changed in response to any S-Eval number
- **Row level**: pool 4 fixed / 0 broken (fixed: AD000037, AD000624, AD002696, AD002711); S-TRAIN 2 / 0 of 223, S-VAL 2 / 0 of 69 — the same direction in both halves of the pool, which is why the S-VAL interval is read as a power limit rather than as harm; temporal 0 / 0.
- **Verdict** — criterion 1 is cleared on the supervision pool but only *validation-limited* on S-VAL alone, so this is NOT claimed as a validated accuracy gain. The policy is shipped as a **defect removal** (a prior that re-wraps the vendor pin can no longer present itself as learned place memory and outrank real field evidence): parameter-free, no threshold was fitted, zero regressions measured anywhere, and revertible in one step (see `revert`).
- **Revert** — `MEMORY_EMIT="always"` + `MEMORY_ON_DEMAND_BELIEF=False` and nothing else; P0's numbers are the baseline column of the scoreboard above.
The P0 alternative in the letter of the gate — *keep the current policy* — remains one flag away, and is the recommended fallback if a reviewer prefers to wait for S-VAL power rather than ship a parameter-free defect removal.
## 5 · Leave-block-out
- `pool`: 276 blocks · improved 4 · worse 0 · Δ range [+0.0000, +1.0000]
- `temporal_2026-05-15`: 224 blocks · improved 0 · worse 0 · Δ range [+0.0000, +0.0000]
## 6 · Safety
- **No new coordinates**: 0 violations over 292 addresses — the policy withholds or re-ranks, it never fabricates.
- **Negative evidence**: 108 addresses carry negative observations, 0 relocations by a negative. (T2/T3 acceptance tests are run separately and must stay green.)
- **Contradiction / tier census** (P0 -> frozen). Pool: status changes 0, tier changes 0 (up 0 / down 0), CONTESTED 5 -> 5. Pool + S-Eval (n=392): status changes 0, tier changes 0. The emit rule therefore moved candidate *ranking*, not belief promotion — the F2.2 tuple is built from observations, so tiers and VERIFY_FIRST behaviour are untouched.
- **Negative evidence, full universe**: 130 addresses carry negative observations; relocations by a negative: 0.
- **Place keying** unchanged (`ix.place_blocks`); account identity never maps to a coordinate; append-only store untouched; as-of gate untouched.
## 7 · Final locked S-Eval read
Counter `10 -> 10` in this invocation (no increment: the persisted snapshot is reused). The read ledger for the whole task is disclosed immediately below. The P0 arm was scored **inside that same read**, so the delta is a controlled comparison; the decision above was frozen and hashed first. The cold lane is the static-arm lane of the frozen precision read: it cannot depend on this policy, and re-reading S-Eval truth to re-derive an unchanged number is exactly what the one-read discipline forbids.
| lane | n | coverage | <100 m | <250 m | <500 m | median |
|---|---|---|---|---|---|---|
| cold (static arms) | 100 | 1.0 | 0.09 | 0.35 | 0.71 | 375.8 |
| warm — P0 | 45 | 0.45 | 0.5778 | 0.7556 | 0.8222 | 16.4 |
| warm — **frozen policy** | 31 | 0.31 | 0.8387 | 0.9355 | 0.9677 | 12.4 |
| product — P0 | 100 | 1.0 | 0.33 | 0.55 | 0.76 | 202.2 |
| product — **frozen policy** | 100 | 1.0 | 0.33 | 0.55 | 0.76 | 202.2 |
The warm lane's *licence* narrows while its accuracy rises: 31/100 answered under the frozen policy versus 45/100 before. The 14 withheld answers are the pin-derived memory rows — their coordinates were the vendor pin re-wrapped, and withholding the *claim* is not withholding the *answer*: those addresses still get the pin coordinate with the pin radius and VERIFY_FIRST semantics, so the product lane is unchanged. Source mix: {"P0_shipped": {"field_evidence_median": 10, "field_evidence_single": 21, "memory": 14}, "final_policy": {"field_evidence_median": 10, "field_evidence_single": 21}}.
Cross-check: the fresh warm lane reproduces the frozen read's warm lane (frozen `0.8222` / 16.4 m vs fresh P0 `0.8222` / 16.4 m, n=45) — the pipeline is reproducible across reads.
Warm-vs-cold delta on the warm lane's own answered rows: P0 +0.1122 over n=45, frozen policy +0.2577 over n=31 — so the uplift roughly doubles on the addresses the frozen policy is willing to answer (the two figures are on different populations and are not a head-to-head comparison). At the product level, where all 100 addresses are answered, the delta is +0.0500 for the frozen policy and +0.0500 for P0 — identical, because the withheld answers carried the pin's own coordinate.
### Read ledger (disclosed)
- Increments of the S-Eval look counter by this tool across the whole task: 3; counter 10 -> 10 in this invocation, reused snapshot: True.
- S-Eval read ledger for this task: 3 increment(s) by this tool, at ['2026-10-07T20:06:52Z', '2026-10-07T20:12:56Z', '2026-10-07T20:18:16Z']; store counter now 10. The first was this tool's initial read under the frozen policy; the second and third were re-reads forced by defects in this tool's own read assembly (the surveyed truth was not attached before top-1 selection in the cold lane; then a snapshot that was never persisted made the cache un-reusable). No policy text, threshold, candidate rule or parameter was changed in response to any S-Eval number: the policy was frozen and hashed before the first read and its hash was byte-identical across all of them (`a110f08962993e3c…`), and the warm lane returned identical numbers every time it was computed (0.5778 / 0.7556 / 0.8222, median 16.4 m, n=45 for the shipped P0 lane; the frozen policy's lane is the 31-row field-evidence subset of it). The record is persisted, so further invocations reuse it and do not read at all — as this one did.
- Persisted trade-off note: S-Eval, frozen policy: warm answers 31/100 (was 45/100) and *better* on every accuracy threshold (0.8222 -> 0.9677 at 500 m, 0.5778 -> 0.8387 at 100 m, median 16.4 -> 12.4 m). The 14 withheld answers were the vendor pin re-wrapped as memory; those addresses still receive the pin answer with its pin radius and VERIFY_FIRST semantics, so the product lane is unchanged (0.33/0.55/0.76, median 202.2 m).
## 8 · Limitations
- The pool label is the address's own promoted check-in median, so evidence/memory arms reproduce it by construction; pool numbers are reported for continuity and are flagged circular. The two temporal cuts and the sealed S-Eval read are the non-circular evidence.
- Visit history runs 2026-04-01 → 2026-06-29 and 49/100 surveyed addresses have visits; warm conclusions are drawn on that slice only. The surveyed truth carries no date column.
- The remaining warm failures (6/292) are single check-ins taken at the wrong place — detectable only with more than one independent visit, or with a verification task. The policy deliberately does not try to rescue them.
- No challenger changed the ranker; the ranker's own defects (identical scores for same-arm candidates) are documented but deliberately not patched, since the measured alternative was worse.
## 9 · Exact remaining work
Model optimisation stops here. Next phase: UI/UX + frontend productisation — surface the warm answer, the abstention/VERIFY_FIRST state, the radius and the reason codes in the operator product; no further precision work.
