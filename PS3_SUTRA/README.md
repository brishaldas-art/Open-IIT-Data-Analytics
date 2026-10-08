# SUTRA — Address Geocoder That Learns from Field Visits

**Official Problem Statement 3. This workspace contains one project and nothing else.**

SUTRA resolves a written address into a coordinate **plus a granularity, a calibrated radius, a reason and an auditable
memory** — and it improves where nobody else does: from what field visits actually reveal, weighted by how much each visit
deserves to be believed.

> **Status: research, data audit, data discovery, cleaning, architecture and preprocessing are complete.**
> **No model has been trained, and none may be trained until this set is frozen** — enforced by
> `python3 tools/check_workspace.py`.

---

## Start here (in this order)

| # | Read | Why |
|---|---|---|
| 1 | `PS3_FINAL_REPORT.md` | the consolidated answer, sections **A–R** (the headline deliverable) |
| 2 | `PS3_MASTER_ARCHITECTURE.md` | the binding architecture: 27 answered questions, the pruned pipeline, the two loops |
| 3 | `PS3_DATA_AUDIT.md` | what the official data actually is, and the twelve traps it sets |
| 4 | `PS3_CANONICAL_SCHEMA.md` | the entity/field contract every artefact obeys |
| 5 | `PS3_SOURCE_REGISTER.md` | every external claim, with URL, licence class and what it proves |

## The three findings that shaped the design

1. **Field visits are evidence, not truth.** Failure check-ins (`address_not_traceable`) sit a median **1,603 m** from
   surveyed truth at a **1.3-minute** dwell and land nearer the vendor pin **84.9%** of the time, while met-someone visits
   sit **29 m** from truth. So negative evidence may *never* move a coordinate — it raises suspicion and queues
   re-verification.
2. **The dataset's integrity problem is not GPS.** One agent has **156 duplicate photo hashes (25.6%)** while its GPS is
   pristine. Integrity must be cross-signal and weight-based: *weight, don't accuse*.
3. **Candidate arms alone are worth ~19%.** The oracle over the current arms is **306 m** median vs the vendor's **376 m**,
   so the value is in memory and evidence — not in a bigger model. (n = 100 surveyed records; every claim in this package
   carries its n.)

## Repository map

```
PS3_SUTRA/
├── PS3_FINAL_REPORT.md                  consolidated A–R answer
├── PS3_MASTER_ARCHITECTURE.md           binding architecture (question set + pruning + loops)
├── PS3_SYSTEM_DESIGN.md                 components, interfaces, flows, budgets, failure paths
├── PS3_DATA_ARCHITECTURE.md             stores, schema, as-of joins, retention, compaction
├── PS3_MODEL_ARCHITECTURE.md            the six models, small-data protocol, kill criteria
├── PS3_DYNAMIC_LEARNING_ARCHITECTURE.md fast loop / slow loop, gates, drift, rollback
├── PS3_FIELD_EVIDENCE_ARCHITECTURE.md   visit → weighted, reason-coded evidence
├── PS3_ADDRESS_MEMORY_ARCHITECTURE.md   place identity, decay, contradiction resolution, states
├── PS3_UNCERTAINTY_ARCHITECTURE.md      tier + calibrated radius + measured coverage
├── PS3_API_AND_COMPONENT_DESIGN.md      endpoints, error vocabulary, cold start, offline
├── PS3_DATA_AUDIT.md · PS3_DATA_LINEAGE.md · PS3_DATA_CLEANING_REPORT.md · PS3_DATA_PREPROCESSING.md
├── PS3_DATA_EDA_AND_PREPROCESSING.md    the dataset in full: EDA · cleaning · preprocessing · leakage audit
├── PS3_BUSINESS_AND_OPERATIONAL_RETHINK.md  A–T: PS3 as a business problem — workflow, waste, knowledge loop,
│                                        offline design, economics, and what in SUTRA is wrong
├── PS3_LEAKAGE_AND_VALIDATION.md        T0–T4 stages, banned list, splits, negative controls
├── PS3_FINAL_DATA_AND_ARCHITECTURE_FREEZE.md   binding data policy + frozen architecture (external data rejected)
├── PS3_ARCHITECTURE_LOCK_CANDIDATE_2026-10-07.md   LOCKED architecture (4 layers, A–T, acceptance tests)
├── PS3_ARCHITECTURE_DUE_DILIGENCE_2026-10-07.md    the pre-lock pass: systems, contradictions, feasibility, red team, novelty
├── PS3_IMPLEMENTATION_CONTRACTS_2026-10-07.md     normative schemas · interfaces · API · invariants · acceptance tests
├── PS3_ARCHITECTURE_REQUIREMENTS_RECONCILED.md     old requirements vs the official-only decision, row by row
├── PS3_OPERATIONAL_NEIGHBOUR_INDEX_RESEARCH.md     probe + placebo control; experiment-gated verdict
├── PS3_PURPOSE_AND_DIRECTION_MODULES.md            purpose → eligibility gate · landmark direction cues
├── PS3_REAL_SYSTEMS_RESEARCH.md         13-question reverse-engineering of real systems
├── PS3_RED_TEAM.md                      22 failure classes: detect · quantify · mitigate · monitor
├── PS3_MODEL_SELECTION.md               choices, evidence, kill criteria
├── PS3_EXPERIMENT_PLAN.md               pre-registered grid A–O, metric set, reporting template
├── PS3_COST_ARCHITECTURE.md             designed cost, substitution ladder, the do-not-ship floor
├── PS3_MLOPS_ARCHITECTURE.md            environments, versioning, monitoring, incidents
├── PS3_NOVELTY_AND_DIFFERENTIATION.md   six defensible claims, and what we refuse to claim
├── PS3_DECISION_LOG.md                  every decision with its evidence and reversibility
├── PS3_ARCHITECTURE_CHANGE_SET_2026-10-07.md   what the official-scope re-audit changed, and why (A0–E1)
├── PS3_CANONICAL_SCHEMA.md · PS3_SOURCE_REGISTER.md · PS3_WORKSPACE_MANIFEST.md
├── PS3_DEEP_INTERNET_RESEARCH.md · PS3_ASSUMPTIONS.md · PS3_ARCHITECTURE_REQUIREMENTS.md
├── PS3_ADVANCED_ARCHITECTURE_RESEARCH.md · PS3_ARCHITECTURE_OPTIONS.md · PS3_ARCHITECTURE_SELECTION.md
├── data/
│   ├── official_ps3/        DATASET A — official, synthetic, read-only, hash-frozen (12 tables incl. the assigned `lenders`)
│   ├── external_research/   reserved path — permanently empty (external data prohibited; machine-guarded)
│   ├── cleaned/             cleaned tables + cleaning_log.csv (one row per rule)
│   └── derived/             audit profiles, leakage map, candidates, features + receipts, diagnostics, calibration,
│                            EDA transcript + eda_* tables + 22 SVG charts
└── tools/                   audit · clean · candidates · evidence diagnostics · place-block folds · calibration · EDA
                             (eda_official.py, eda_charts.py) · leakage/links/workspace checks · manifest · reproduce.sh
```

## Run it

```bash
bash tools/reproduce.sh          # manifest → audit → clean → candidates → calibration → all invariant checks
python3 tools/check_workspace.py # PS3-only invariants, no-training-yet, citations, links, licences
python3 tools/check_leakage.py   # leakage guard + hash proof that Domain A never changed
python3 tools/evidence_diagnostics.py   # the check-in-vs-truth diagnostic that drives the evidence design
python3 tools/place_block_folds.py      # place-blocked evaluation folds (Amendment A1; account split untouched)
python3 tools/eda_official.py     # full dataset EDA → transcript, 13 tables, 8 charts (read-only on Domain A)
python3 tools/eda_charts.py       # 14 modelling-question charts → self-contained HTML dashboard
```

Requires Python 3 with `pandas` and `numpy`. Runtime on the official dataset: well under a minute.

## Reading the evidence tags

* `[V]` verified from a source · `[I]` inference · `[A]` assumption · `[?]` unknown.
* `[VENDOR CLAIM]` — a vendor's published number; never used as a measured result of ours.
* Licence classes: `[OPEN]` · `[NC]` non-commercial (research only) · `[NC-REQ]` request required · `[PAID]` · `[TOS]`.
* Data labels: **SYNTHETIC** (the official dataset is synthetic — mechanism only, never magnitude) · **SIMULATION**
  (replay-based dynamic-learning results) · **injection-based** (integrity detector metrics).

## The rules this package holds itself to

1. Never present private augmentation as official data; never mix the two domains silently.
2. Never erase provenance; every coordinate names its evidence and its licence.
3. A mediocre honest number beats a fake impressive one — every figure carries its stratum, its n and its interval.
4. Never trust field GPS, a vendor geocoder, an outcome field or a retrain by default.
5. Weight, don't accuse; widen, don't invent; refuse rather than fabricate.

*Sources: `PS3_SOURCE_REGISTER.md` (`[S1]`–`[S50]` external, `[S90]`–`[S92]` internal).*
