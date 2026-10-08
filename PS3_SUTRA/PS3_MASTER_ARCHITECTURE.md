# SUTRA — MASTER ARCHITECTURE

**SUTRA = Semantic Utility for Traceable Resolution of Addresses.** One sentence: *a per-town address intelligence that
learns from field visits — resolving a written address into a coordinate, a granularity, a **measured radius**, a reason,
and an append-only memory that is corrected by evidence and never overwritten by opinion.*

This document is the binding architecture. It supersedes the earlier selection drafts and answers the commission's
question set (§1), the block-by-block pruning (§3), and the standing quality bar: for every block, *what does it change
in the real workflow* and *why can't something simpler replace it*.

---

## 1. The commission's question set, answered (27 questions)

| # | Question | Answer (one line; the full argument lives in the named document) |
|---|---|---|
| 1 | What is the actual prediction problem? | Two decisions, not one: **"which of these candidate places is the record?"** (ranking, at query time) and **"how much does this visit change what we believe about this place?"** (evidence weighting, after a visit). `PS3_MODEL_ARCHITECTURE.md` §1 |
| 2 | What do the labels really mean? | `surveyed_*` = truth (100 rows). A met-someone visit = strong *place* evidence. A negative outcome = evidence about the *record/agent*, never about a coordinate (measured: 1,603 m off truth at 1.3 min dwell). `PS3_DATA_AUDIT.md` §2.7b, `PS3_CANONICAL_SCHEMA.md` §3 |
| 3 | How good is the ground truth? | 100 surveyed records, 3.2% of the book, skewed to geocodable addresses (0 `OUT`, 1 rooftop). Every headline number is calibrated to that limitation. `PS3_DATA_AUDIT.md` §2.6 |
| 4 | Which evidence is trustworthy? | Weighted, not trusted: integrity multipliers from media, trail, dwell, coordinate reuse and per-agent baselines; two independent confirmations before a promotion. `PS3_FIELD_EVIDENCE_ARCHITECTURE.md` |
| 5 | Which features are valid? | T0/T1 only for the resolver; T2 only for the in-visit stage; as-of joins for memory. 12 banned patterns enforced in code. `PS3_LEAKAGE_AND_VALIDATION.md` §2 |
| 6 | When is each field available? | T0–T4 map over the audited tables: `data/derived/ps3_leakage_map.csv` (the assigned `lenders` table adds four context-only T0 columns; scope of record = 12 tables) |
| 7 | Where can leakage occur? | Ranked list of 8 realistic traps, each with a mechanical guard. `PS3_LEAKAGE_AND_VALIDATION.md` §8 |
| 8 | What are the deployment constraints? | Offline-capable field app; no vendor dependency for correctness; per-query cost and p95 latency budgets; licence constraints on every stored artefact. `PS3_COST_ARCHITECTURE.md`, `PS3_API_AND_COMPONENT_DESIGN.md` §7 |
| 9 | How do field visits change the system? | Fast loop: visit → integrity weight → immediate belief update in memory (no training). Slow loop: quality-gated buffer → drift check → retrain → calibrate → challenger → promote/rollback. `PS3_DYNAMIC_LEARNING_ARCHITECTURE.md` |
| 10 | What updates instantly vs triggers retraining? | Belief, radius, tier, reason codes, re-verification priority: instant. Model parameters: only through the gated slow loop. **Never retrain per visit.** |
| 11 | Which models are justified? | A small LambdaMART-style ranker over ≤25 candidates; a one-dimensional evidence weight table (rule-first, GBM as challenger); a geographically weighted conformal calibrator; a purpose classifier. Nothing else. `PS3_MODEL_SELECTION.md` |
| 12 | What is memory (store/expire/decay/never overwrite)? | Append-only versions of belief; decay by tier; raw trails expire at 90 days, derived evidence persists; a position is never deleted, only demoted and disputed. `PS3_ADDRESS_MEMORY_ARCHITECTURE.md` |
| 13 | How are contradictions resolved? | Contradiction mass comparison → `CONTESTED` state + widened radius + review; resolution by a high-integrity visit or adjudication, never by an automatic overwrite. |
| 14 | How does the integrity layer avoid accusing? | Every signal produces a **weight and a reason code**; no single signal can zero a visit; agent-level effects are scoped and reversible. `PS3_FIELD_EVIDENCE_ARCHITECTURE.md` §4 |
| 15 | What happens to negative evidence? | **Graded rule:** one negative observation can never relocate a coordinate by itself; accumulated independent negative evidence demotes confidence, widens the radius, marks `MOVED_SUSPECTED`/`CONTESTED` and triggers re-verification; only positive evidence or adjudication can establish a new primary coordinate (F2.1/D36). `PS3_FIELD_EVIDENCE_ARCHITECTURE.md` F2.1 |
| 16 | What happens at cold start? | Explicit cold-start mode: coarse tier, wide radius, honest reason, no fabricated precision; the vendor/town prior is an arm, not a crutch. `PS3_API_AND_COMPONENT_DESIGN.md` §6 |
| 17 | How is uncertainty represented? | `tier` ∈ CONFIRMED / PROBABLE / APPROXIMATE / UNPLACEABLE (+ `OUT`) with an empirically calibrated radius and reason codes; measured coverage always reported next to any nominal coverage. `PS3_UNCERTAINTY_ARCHITECTURE.md` |
| 18 | How is the radius obtained? | Geographically weighted split conformal over candidate errors; bootstrap as a documented fallback with its known under-coverage. |
| 19 | What is the cost architecture? | Correctness first, then substitutes: local index, candidate cap, conditional reranking, cached vendor pins with licence clocks. Numbers and substitution ladder in `PS3_COST_ARCHITECTURE.md`. |
| 20 | What is the failure path of every action? | §5 below: each block names its failure response; the system prefers an honest refusal to a fabricated point. |
| 21 | Who owns each state and how does it change? | Ownership map: `PS3_SYSTEM_DESIGN.md` §6 (state → owner → update mechanism → audit trail). |
| 22 | How is drift detected? | ADWIN on the radius/coverage stream, PSI/KS on feature distributions nightly, DDM-style on accuracy when labels land, with cooldown and hysteresis. `PS3_DYNAMIC_LEARNING_ARCHITECTURE.md` §7 |
| 23 | How is the loop evaluated? | Entity- and time-aware splits, exposure-weighted metrics, an exploration slice, and negative controls in every run. `PS3_LEAKAGE_AND_VALIDATION.md` §5–§6 |
| 24 | What if the vendor geocoder is wrong? | It is a measured baseline (median 376.4 m, 9% <100 m) and one arm among several; the ranker learns when to overrule it. |
| 25 | What if the field is offline / the API is down? | Local index + memory resolve without the vendor; responses declare missing inputs; offline queue with sync reconciliation. |
| 26 | What is deliberately NOT built? | Global geocoding, LLM-in-the-loop, RL, microservices, map matching (no road graph), a point-prediction model over landmarks, a single-number accuracy claim. `PS3_DECISION_LOG.md` |
| 27 | Why is this better than `address → ML → coordinates`? | Because that pipeline has nowhere to put *evidence*, *doubt*, *history*, or *correction* — it dies at the first wrong visit. Measured reason: candidate arms alone buy 376 → 306 m (oracle); only evidence changes the answer. |

---

## 2. The pipeline, block by block (the §12 hypothesis, challenged and pruned)

```
RAW ADDRESS ─► S0 INGEST ─► S1 NORMALISE/PARSE ─► S2 RESOLVE ENTITIES ─► S3 GAZETTEER INDEX
                    │                                                                  │
                    └──────────────► S4 CANDIDATE GENERATION ◄──────────────────────────┘
                                              │
                    ┌─────────────────────────┼───────────────────────────┐
                    ▼                         ▼                           ▼
             S5 RANKER (Λ)            S6 POINT FALLBACK            memory arm (as-of)
                    │                         │                           │
                    └────────────► S7 FUSION / BELIEF ◄────────────────────┘
                                              │
                                              ▼
                                   S8 UNCERTAINTY (tier + measured radius + reasons)
                                              │
              ┌───────────────────────────────┴──────────────────────────────┐
              ▼                                                              ▼
      SERVE (resolve / score)                              FIELD VISIT EVIDENCE
              ▲                                                              │
              │                                                              ▼
      S12 ADDRESS MEMORY ◄── S11 BELIEF UPDATE ◄── S10 INTEGRITY ── S9 EVIDENCE FEATURES
              ▲                                                              │
              │                                                              ▼
      S13 SLOW LOOP (buffer → drift → retrain → calibrate → challenger)  ◄────┘
```

| Block | What it changes in the real workflow | Why not simpler | Class |
|---|---|---|---|
| **S0 ingest** | a record can exist with no geocode at all (237 `OUT` today) — the system must accept that state instead of erroring | without an explicit unknown-state, every downstream stage invents one | **BUILD NOW** |
| **S1 normalise/parse** | sends *typed* fields (house no, relation, locality token) instead of one blob; 24.9% of records have no comma, so this is not cosmetic | a single "clean the string" step loses span evidence the ranker needs | **BUILD NOW** (rules) |
| **S2 resolve entities** | decides *whether* the text contains a locality/pincode we know (260 records carry a 6-digit token that matches nothing) | skipping resolution means the ranker compares strings without knowing what matched — no auditability | **BUILD NOW** |
| **S3 gazetteer index** | makes matching local, offline and licence-auditable | a remote lookup per record is slow, costly, and licence-encumbered | **BUILD NOW** |
| **S4 candidate generation** (official arms only) | exposes *why* each option exists (arm + source + granularity + licence): the **official frozen baseline geocode arm**, **official towns/localities**, **official landmark/POI anchors**, **official address-book anchors**, **official historical field evidence**, **address memory** | a single point prediction cannot express "the vendor says locality-level, the official gazetteer says another locality, my memory says the house is behind the temple" — and no external source may enter this stage (final data policy) | **BUILD NOW** |
| **S5 ranker (Λ)** | picks between arms using text + stratum + memory features | a priority list is measurably as good as the vendor alone (audit §2.7c) — i.e. a ranker is *necessary* once arms compete, and honest when it cannot beat the floor | **BUILD NOW** (small model) |
| **S6 point fallback** | **never invents a coordinate**: with no candidate the system returns NO COORDINATE — area context only (town/locality extent, labelled `AREA_CONTEXT`), `UNPLACEABLE`, and a verify-first task; a coarse anchor can never carry an address-level tier | a town centroid served as an address coordinate is the false-precision failure this design exists to prevent (audit trap 12) | **BUILD NOW** |
| **S7 fusion/belief** | combines candidate score, memory, and visits into a belief with reasons | without fusion there is no place to put evidence — this is the difference from `address → ML → coords` | **BUILD NOW** |
| **S8 uncertainty** | the radius is a *number the field can act on* and one the compliance side can audit | a level without a radius cannot answer "is this good enough to act on?" | **BUILD NOW** |
| **S9 evidence features** | converts a visit into structured evidence (dwell, trail agreement, media, baseline) | raw GPS as a label is the trap the audit measured | **BUILD NOW** |
| **S10 integrity** | "weight, don't accuse" — one bad actor cannot poison the memory | binary accept/reject loses good visits and still lets coordinated fakes through once | **BUILD NOW** (rules) |
| **S11 belief update** | instant, append-only, reason-coded | a batch retrain per visit is economically absurd and would make behaviour unreproducible | **BUILD NOW** |
| **S12 address memory** | the actual asset: what this street/house is, learned from the field | a cache of the last answer cannot hold contradiction, decay or provenance | **BUILD NOW** |
| **S13 slow loop** | improves the model when reality moves, without thrash: gates, cooldown, rollback | continuous online learning is ungovernable here (label lag, small data) [S33][S35] | **BUILD IF TIME** (simulated on this dataset; PRODUCTION as designed) |
| **S14 external gazetteers** | — | **REJECTED (final data policy, 2026-10-07):** official data only — no external, scraped, downloaded or third-party geographic source may enter S4 or any metric | **REJECTED** |
| **S15 statistical parser** | helps only the unresolved residue | rules already cover the bulk; the residue is small here | **BUILD IF TIME** |
| **S16 embeddings / LLM parse** | nothing measurable on this data | no licence-cleared model + no real-text benchmark + 240× latency evidence | **RESEARCH ONLY** |
| **S17 HMM map matching / road graph** | would refine street-level points in deployment | no road graph and no CRS in this dataset | **RESEARCH ONLY** |
| **S18 RL / bandit for visit allocation** | could allocate visits optimally *later*, once exposure is instrumented | needs logs we do not yet have; the exploration slice is the honest precursor | **RESEARCH ONLY** |

---

## 3. The two loops (the heart of the design)

```
FAST LOOP (seconds, no training)                     SLOW LOOP (weekly/monthly, gated)
visit evidence ─► integrity weight w_i               quality-gated buffer ─► drift detectors
      │                    │                                    │
      └─► evidence score ──┴─► belief update ─► memory          ├─► retrain (warm start)
                    (append-only, reason-coded)                 ├─► recalibrate radius map
                                                                ├─► challenger vs champion
                                                                └─► promote | hold | rollback
```

| Property | Fast loop | Slow loop |
|---|---|---|
| Latency | milliseconds | hours–days (buffer-driven) |
| Artefact changed | belief versions + radius + tier + queue | model parameters + calibration map |
| Trigger | a visit, an adjudication, a correction | ≥ N new labelled visits, drift alarm, schedule |
| Guard | integrity weight, two-confirmation gate, caps | quality gate, drift evidence, cooldown, challenger comparison, rollback |
| Leakage rule | as-of join only | label-lag exclusion from the training window |
| Why this split | evidence is cheap and local; parameters are neither | |

---

## 4. Cross-cutting rules (apply to every block)

0. **Vocabulary (frozen).** The candidate arm fed by `baseline_geocodes.csv` is the **official frozen baseline geocode
   arm** (arm id `frozen_baseline`; older text says "vendor pin" — same arm, no live vendor call exists anywhere in the
   benchmark or demo). `request_purpose` (caller-declared, access control) ≠ `address_purpose` (HOME_LIKE · WORK_LIKE ·
   OTHER · UNKNOWN) ≠ `eligibility` (SERVE · VERIFY_FIRST · REFUSE). Normative schemas:
   `PS3_IMPLEMENTATION_CONTRACTS_2026-10-07.md`.
1. **Provenance first.** Every coordinate carries where it came from, its licence class, and its stage.
2. **Granularity is never silently upgraded.** A locality match may not be rendered as a rooftop claim.
3. **Negative evidence is graded (F2.1).** One negative observation can never relocate a coordinate by itself;
   accumulated independent negatives demote, widen, mark `MOVED_SUSPECTED`/`CONTESTED` and trigger re-verification;
   only positive evidence or adjudication establishes a new primary coordinate. Hard invariant, alarmed, tested.
4. **Weight, don't accuse.** Integrity produces multipliers and reason codes.
5. **Append-only memory.** Updates are new versions; corrections are new versions with a reason.
6. **One metric is never enough.** Strata, n, hit-rate curve, coverage, refusal, cost.
7. **The vendor is an arm, not an authority.**
8. **Degrade honestly.** No candidate → coarse tier + wide radius + reason; no data → `UNPLACEABLE`, not a guess.
9. **Cost follows correctness.** Cheaper substitutes only after the correct design exists.
10. **Everything reproducible.** Artefact receipts, tensor hashes, split versions, belief versions.

---

## 5. Failure paths (every action has one)

| Block | Fails when | Response |
|---|---|---|
| S0 | record has no town, no text | `UNPLACEABLE` with `missing_town` + review queue; still counted in coverage |
| S1 | text is unparsable | flat-token fallback; flag `low_structure`; wide radius |
| S2 | no locality/pincode match | town prior arm only; reason `no_local_evidence` |
| S3 | index stale | serve with `index_age_days` in the response; widen radius |
| S4 | ≥1 arm empty | continue with the remaining arms; record `arms_available` (the 237 `OUT` records exercise this today) |
| S5 | model version missing | fall back to the rule priority list (the honest baseline) |
| S6 | no candidate at all | **NO COORDINATE**: area context (town/locality extent, labelled `AREA_CONTEXT`), `UNPLACEABLE` + verify-first task; never a fabricated point |
| S7 | contradiction | `CONTESTED` + widened radius + review |
| S8 | calibration missing for the stratum | parent-stratum map + `calibration_fallback` reason, radius widened |
| S9 | trail missing | evidence from outcome/dwell only, weight reduced |
| S10 | integrity signal absent (the honest default) | weight unchanged, `insufficient_evidence` recorded |
| S11 | belief store unavailable | read the last snapshot (read-only degradation); queue the update |
| S12 | memory miss | cold-start path |
| S13 | challenger worse | hold; champion stays; incident logged |
| S14 | *(component rejected — no external arm exists)* | not applicable; `arms_available` lists official arms only |
| Serving | vendor API timeout | local-only resolution; latency budget preserved behind the cache |

---

## 6. What would make this architecture wrong (self-falsification criteria)

1. If the **official** candidate oracle remains near the observed ceiling (306.2 vs 376.4 m vendor pin, as it is today),
   retrieval is **data-limited within the supplied dataset**. The next investment is official-data parsing, memory and field
   evidence — **not** external augmentation, which the final data policy forbids.
2. If field evidence proved uncorrelated with truth — it does not (met-someone 29.3 m vs 1,603.2 m) — the loops would be
   pointless.
3. If the integrity layer could not distinguish injected faults (measured on the bed in `PS3_RED_TEAM.md` §2), promotion
   would have to return to human adjudication only.
4. If exposure weighting did not move the metrics at all, the selection-bias concern would be empirically void on this
   dataset — reported as a finding, not hidden.

---

## 7. Document map

| Question | Document |
|---|---|
| What the data is, field by field | `PS3_DATA_AUDIT.md`, `PS3_CANONICAL_SCHEMA.md`, `PS3_DATA_LINEAGE.md` |
| How data is cleaned, preprocessed, kept leaking-free | `PS3_DATA_CLEANING_REPORT.md`, `PS3_DATA_PREPROCESSING.md`, `PS3_LEAKAGE_AND_VALIDATION.md` |
| What the world already does | `PS3_REAL_SYSTEMS_RESEARCH.md` |
| What is frozen and binding | `PS3_FINAL_DATA_AND_ARCHITECTURE_FREEZE.md` |
| How it is built | `PS3_SYSTEM_DESIGN.md`, `PS3_DATA_ARCHITECTURE.md`, `PS3_MODEL_ARCHITECTURE.md`, `PS3_API_AND_COMPONENT_DESIGN.md` |
| How it learns | `PS3_DYNAMIC_LEARNING_ARCHITECTURE.md`, `PS3_FIELD_EVIDENCE_ARCHITECTURE.md`, `PS3_ADDRESS_MEMORY_ARCHITECTURE.md` |
| How it admits doubt | `PS3_UNCERTAINTY_ARCHITECTURE.md` |
| How it is proven, priced, run, defended | `PS3_EXPERIMENT_PLAN.md`, `PS3_MODEL_SELECTION.md`, `PS3_COST_ARCHITECTURE.md`, `PS3_MLOPS_ARCHITECTURE.md`, `PS3_RED_TEAM.md` |
| Why it is different, and what was decided when | `PS3_NOVELTY_AND_DIFFERENTIATION.md`, `PS3_DECISION_LOG.md` |

## 8. Amendment register — official-scope re-audit (2026-10-07)

An architecture that cannot show what changed, on what evidence, is a preference. Every amendment below is **additive**:
no block was removed and no invariant was relaxed. Each one is grounded in the new register group N `[S67]`–`[S73]`
and the re-audit measurements `[S94]`.

| # | Amendment | What changed | Evidence | Detail |
|---|---|---|---|---|
| A3 | **Point-fallback semantics, negative evidence, independence, radius vocabulary, ownership, sync** | S6 returns no coordinate without a candidate (area context only); negative evidence graded (F2.1); promotion independence scored (F2.2); empirical quantiles first, nominal only when measured (U2); belief/memory/projection ownership fixed (M3); sync contract specified | due-diligence pass, 2026-10-07 `[S96]` | `PS3_ARCHITECTURE_LOCK_CANDIDATE_2026-10-07.md`; amendment sections in the owning documents |
| A2 | **Final data policy — external data rejected** | Experiment I cancelled; S4 arms are official-only; the external-research document archived; register entries S39–S47 marked rejected; the absolute guard in `check_workspace.py` fails if any dataset appears outside `official_ps3/cleaned/derived` | final project decision, 2026-10-07 | `PS3_FINAL_DATA_AND_ARCHITECTURE_FREEZE.md` |
| A0 | **Dataset scope of record** | DATASET A = the 6 task-specific tables + the 6 officially assigned shared tables (`accounts, addresses, agents, field_visits, lenders, splits`) = **12 tables · 177,196 rows**; the assigned `lenders` table was imported into the frozen tree and the hash set re-baselined; the two shared tables assigned to other problem statements (`dial_attempts`, `payments`) are excluded — this task has **no financial outcome variable, by design** | official pack assignment + verified FK structure; `lenders` measured to carry no signal (≤1.4 pts) → context-only | `PS3_DATA_LINEAGE.md`, `PS3_CANONICAL_SCHEMA.md`, `PS3_DATA_AUDIT.md`, `PS3_WORKSPACE_MANIFEST.md`, `README.md` |
| A1 | **Evaluation protocol v2** | three-population reporting (all 100 surveyed · validation+test · leave-block-out); place-block ledger `data/derived/ps3_place_blocks.csv` via `tools/place_block_folds.py`; prequential loop evaluation | 66/19/15 truths by split; **124/344 (36.0%)** test addresses with a train met check-in within 30 m; 39 split-crossing blocks [S67][S68][S70] | `PS3_LEAKAGE_AND_VALIDATION.md` Amendment A1 |
| U1 | **Radius publication rule** | publish with `n_calibration`; strata below n=15 fall back to the parent stratum, labelled; the pincode radius is withheld (measured transfer failure) | locality **79.2%** coverage at p80 (n=24 eval); pincode **0% (n=4)** [S69][S73] | `PS3_UNCERTAINTY_ARCHITECTURE.md` Amendment U1 |
| M1 | **Place identity** | evidence-keyed clusters; `CONFIRMED_MERGE` / `POSSIBLE_MATCH` / `DISTINCT`; the identity key keeps the trailing token; **never merge by account** | **81 co-location clusters / 191 addresses** (all cross-account); account-separated addresses median **3,011.6 m**; repeat-visit agreement 77.7 m / 75.8 m [S72] | `PS3_ADDRESS_MEMORY_ARCHITECTURE.md` Amendment M1 |
| F1 | **Integrity basis** | media duplication + timing plausibility; per-collector windowed baselines; collector traits rejected as features; remark lane becomes a designed capture channel | 162/610 media repeats (one collector); not-traceable spread 19.5–29.1%; tenure **−0.16**; language match nil — and the "645 check-ins >500 m" figure is **retracted** (max 90.8 m) | `PS3_FIELD_EVIDENCE_ARCHITECTURE.md` Amendment F1 |
| L1 | **Dynamic loop** | corrected replay; prequential protocol; **propensity logging** from the first live window; exposure conditioning sharpened | warm **56.0%** vs cold **24.5%** (val+test 56.7/25.1); yield flat by value quintile (43.1→41.8%) [S70][S71] | `PS3_DYNAMIC_LEARNING_ARCHITECTURE.md` Amendment L1 |
| E1 | **Experiment grid** | seven row-level changes: three-population rule · radius n-floor · replay correction · exposure-matched triage · propensity logging · prequential baselines · remark experiment | as above | `PS3_EXPERIMENT_PLAN.md` Amendment E1 |

**Direction of change.** A1, U1, F1 and L1 make the system's claims *harder to make* — fewer populations, smaller n's,
narrower integrity grounds, logged propensities. No amendment trades an invariant away; D05, D07, D12, D19 and D21
stand exactly as written.

**Decision-log entries:** D25–D34.
