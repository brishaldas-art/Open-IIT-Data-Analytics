# ANALYSIS REPORT — INDEX & CONTENT PLAN (40 PAGES)

**Purpose.** This file is the authoritative table of contents and page-budget plan for the analysis
report to be written from this repository (`Open-IIT-Data-Analytics`). For every topic it lists the
subtopics, what each subtopic must cover, the repository files/numbers it draws from, and the number
of pages allocated. The total is **exactly 40 pages — the hard cap**.

**How to use it.**
- Write one report chapter per topic below, in this order; the *Pages* column is the page budget
  (fractions = half-page blocks; two 0.5-page subtopics may share a page).
- The *Location* column gives the report page range for each topic (what a printed TOC would show).
- Every factual claim in the report must cite the repo source listed here; keep the repo's own
  discipline — every number carries its **n**, and the markers `[VERIFIED]` / `[INFERENCE]` /
  `[UNKNOWN]` (used in `WORK_CODE_ANALYSIS_2026-10-08.md`) should be reused in the report.
- Annexure A is the traceability check: after drafting, verify every subtopic's sources were used.

---

## 0 · PAGE BUDGET SUMMARY (verifies to 40/40)

| # | Topic | Pages | Location |
|---|---|---:|---|
| FM | Front matter (title, TOC, executive summary) | 4 | pp. 1–4 |
| 1 | Repository Overview & Provenance | 3 | pp. 5–7 |
| 2 | Problem Statement & Product Purpose | 2 | pp. 8–9 |
| 3 | Data Analysis (the official PS3 dataset) | 6 | pp. 10–15 |
| 4 | Architecture & System Design | 5 | pp. 16–20 |
| 5 | Implementation & Code Analysis | 6 | pp. 21–26 |
| 6 | Experiments, Evaluation & Results | 4 | pp. 27–30 |
| 7 | Product, UX & Integration | 3 | pp. 31–33 |
| 8 | Governance, Risk & Red Team | 3 | pp. 34–36 |
| 9 | Consolidated Findings & Recommendations | 2 | pp. 37–38 |
| AX | Annexures (traceability, metrics register, glossary) | 2 | pp. 39–40 |
| | **TOTAL** | **40** | |

---

## FM · FRONT MATTER — 4 pages (pp. 1–4)

| ID | Subtopic | What it includes (content · repo sources) | Pages |
|---|---|---|---:|
| FM.1 | Title page & document control | Report title ("Analysis of the Open-IIT-Data-Analytics repository / SUTRA PS3 workspace"); date 2026-10-09; repo snapshot reference (`main` @ `c64f3a1`, branch `arena/e4484973-open-iit-data-analytics`); author/version/status table; one-line repo self-description from `README.md`. | 1.0 |
| FM.2 | Table of contents | This index rendered as the report TOC (topics + page locations). | 1.0 |
| FM.3 | Executive summary | 1 page max: what the repo is (a single-project PS3 workspace for **SUTRA**, an address geocoder that learns from field visits); the repo's own three headline findings (visits are evidence-not-truth · integrity is cross-signal, "weight, don't accuse" · candidate arms oracle ≈ **306 m** vs vendor **376 m**, n=100); what has been completed (research→audit→cleaning→architecture→implementation→integration) vs not (no model trained); the report's verdict in three bullets. Sources: `PS3_SUTRA/README.md`, `PS3_SUTRA/PS3_FINAL_REPORT.md`. | 2.0 |

---

## 1 · REPOSITORY OVERVIEW & PROVENANCE — 3 pages (pp. 5–7)

| ID | Subtopic | What it includes (content · repo sources) | Pages |
|---|---|---|---:|
| 1.1 | Repository identity & provenance | What the repo contains and where it came from: Open IIT Data Analytics course workspace; single squashed commit snapshot; what was retrieved from Google Drive (Battle-Model zip) and how (`fetch_battle_model_zip.sh`, sha256-verified 264,431 B / 28 files). Sources: `git log`, `fetch_battle_model_zip.sh`, `WORK_CODE_ANALYSIS_2026-10-08.md` §0, `uploads/SUTRA_FINAL_ARENA_HANDOFF_GOOGLE_DRIVE.md`. | 0.5 |
| 1.2 | Top-level map & folder inventory | Annotated tree of the five top-level areas and their roles: `PS3_SUTRA/` (the one active workspace — 54 design/decision docs, `sutra/` engine, `tools/`, `web/` + `battle_model/` frontends, `data/`, `tests/`, `screenshots/`, `research/precision/`); `PROJECT_DATA_AUDIT/` (official-scope re-audit record v2 + its own data copy); `90_Archive/` (superseded PS1/PS2/draft material); `uploads/` (Drive-retrieved frontend copies: `battle_model_zip/`, `drive_work/`); root artefacts (`WORK_CODE_ANALYSIS_2026-10-08.md`, `fetch_battle_model_zip.sh`, `README.md`). | 1.0 |
| 1.3 | Lifecycle discipline: active / audit / archive | The repo's own hygiene rules and what they prove about working method: `90_Archive/00_Root_Drafts_2026-10-06` (41 files), `ps2_removed_2026-10-06` (137 files), `ps1_fake_ptp_not_used` (4), `ps3_rejected_2026-10-07` (external-data research, **rejected**), `unrelated_non_ps3_artefacts_2026-10-07` (5); "one project and nothing else" rule enforced by `PS3_SUTRA/tools/check_workspace.py`. Sources: `90_Archive/**`, `PS3_SUTRA/README.md` header. | 1.0 |
| 1.4 | Quantitative profile of the repo | Counts that size the work: ~7,759 LOC backend (`sutra/`, 30 modules), ~10,241 LOC tooling (`tools/`, 28 scripts), ~3,384 LOC frontend TS (`web/src`), ~2,121 LOC tests (4 suites), 54 top-level MD documents in `PS3_SUTRA/`, 26 screenshots, 12 hash-frozen data tables. Sources: `wc -l` over components, `ls PS3_SUTRA/*.md \| wc -l`. | 0.5 |

---

## 2 · PROBLEM STATEMENT & PRODUCT PURPOSE — 2 pages (pp. 8–9)

| ID | Subtopic | What it includes (content · repo sources) | Pages |
|---|---|---|---:|
| 2.1 | PS3 stated exactly | The problem the workspace answers: resolve a written address into a coordinate **plus** granularity, calibrated radius, reason and auditable memory; improve from field-visit outcomes; the synthetic-data caveat (dataset is synthetic; mechanisms provable, accuracy claims bounded). Sources: `PS3_SUTRA/PS3_FINAL_REPORT.md` §A, `PS3_SUTRA/PS3_DATA_AUDIT.md` header. | 0.5 |
| 2.2 | Product thesis & non-negotiables | SUTRA as an "address-resolution and field-operations control room"; three product consequences: (1) the answer is a decision object, not a dot; (2) abstention (`REFUSE`/`VERIFY_FIRST`) is a first-class outcome; (3) learning is visible and deliberately slow. Sources: `PS3_SUTRA/SUTRA_PRODUCT_UX_SPEC_2026-10-08.md` §1, `PS3_SUTRA/PS3_PURPOSE_AND_DIRECTION_MODULES.md`. | 0.75 |
| 2.3 | The three findings that shaped the design | (1) Field visits are evidence, not truth — `address_not_traceable` sits median **1,603 m** from truth at **1.3-min** dwell, nearer the vendor pin **84.9%** of the time, vs met-someone at **29 m**; negatives may never move a coordinate. (2) Integrity is not GPS — one agent has **156 duplicate photo hashes (25.6%)** with pristine GPS → weight, don't accuse. (3) Arms alone are worth ~19% — oracle **306 m** vs vendor **376 m** (n=100). Sources: `PS3_SUTRA/README.md`, `PS3_SUTRA/PS3_DATA_AUDIT.md` §0, `PS3_SUTRA/PS3_FINAL_REPORT.md` §C. | 0.75 |

---

## 3 · DATA ANALYSIS — 6 pages (pp. 10–15)

| ID | Subtopic | What it includes (content · repo sources) | Pages |
|---|---|---|---:|
| 3.1 | Dataset inventory & structural audit | DATASET A: **12 tables · 177,196 rows · 83 columns**, hash-verified 12/12 against Drive; per-table row/col/key table (towns 3, localities 36, landmarks_poi 240, baseline_geocodes 2,880, visit_gps_points 160,406, surveyed_addresses 100, accounts 2,400, addresses 3,117, agents 30, field_visits 5,578, lenders 6, splits 2,400); zero duplicate keys, zero full-row duplicates, zero FK orphans; excluded tables (`dial_attempts` 51,105, `payments` 2,162) and why. Sources: `PROJECT_DATA_AUDIT/PS3_UPDATED_DATA_AUDIT.md` §1–2, `PS3_SUTRA/data/official_ps3/`, `PROJECT_DATA_AUDIT/data/drive_verification.csv`. | 1.0 |
| 3.2 | Scope & shared-table governance | The official-scope re-audit: A–G classification of all 8 shared tables; T0–T4 temporal staging; all **75 shared columns** classified by stage and role; the forbidden-input register (no PS1/PS2 data, no external data — permanently rejected). Sources: `PROJECT_DATA_AUDIT/PS3_OFFICIAL_DATA_SCOPE_REAUDIT.md`, `PS3_SHARED_DATA_USAGE.md`, `PS3_UPDATED_DATA_LINEAGE.md`, `90_Archive/ps3_rejected_2026-10-07/PS3_EXTERNAL_DATA_RESEARCH.md`. | 1.0 |
| 3.3 | Data quality: missingness, duplicates, ground truth | Missingness profile (salary_credit_day 68.2%, ability_to_pay 30.3%, agents.town_id 70%, ptp_id 89.2% — structural; **no imputation anywhere**); definition-aware duplicates (identity-key 5 groups/10 rows vs render-key 70 groups/203 rows — template families never merged); only **100/3,117 addresses (3.2%)** have ground truth, split 38/33/29 across towns; 237 `town_id=OUT` addresses all missing vendor geocodes; visit-rate bias by delinquency (19.9% at DPD 0–30 → 84.8% at 180+). Sources: `PS3_UPDATED_DATA_AUDIT.md` §3–4, `PS3_SUTRA/PS3_DATA_AUDIT.md` §0, `data/derived/updated_table_profile.csv`. | 1.0 |
| 3.4 | Field-visit evidence geometry | Visit-outcome analysis: met-someone 29.3 m from truth vs `address_not_traceable` 1,603.2 m (84.9% nearer vendor pin); check-in-to-trail median 7.6 m / max 90.8 m (GPS clean); implications for negative evidence handling. Sources: `PS3_SUTRA/PS3_DATA_AUDIT.md` §0, `data/derived/eda_visit_outcome_geometry.csv`, `eda_visit_outcomes.csv`. | 1.0 |
| 3.5 | Agent & integrity diagnostics | Cross-signal integrity: the planted anomaly is photo duplication (agent with 156 reused hashes in 610 visits = 25.6%; all others ≤0.3%; 172 duplicate-hash visits overall); FA009 time-window "anomaly" **retracted** (79.5–88.7% for every agent in 10:00–12:59 — schedule artefact); memory-consistency re-measurement (77.7 m same-agent vs 75.8 m different-agent). Sources: `PROJECT_DATA_AUDIT/PS3_UPDATED_DATA_AUDIT.md` (corrections 1–4), `data/derived/updated_agent_diagnostics.csv`. | 1.0 |
| 3.6 | EDA outputs & visual evidence | The EDA programme: `eda_report.txt`, `eda_chart_index.json`, **22 SVG charts** (`data/derived/eda_charts/`, `eda_charts.html`); key profiles (baseline error by stratum, ground-truth composition, hierarchy, landmark types, near-duplicates); what EDA invalidated ("nine EDA-invalidates-this-assumption findings"). Sources: `PROJECT_DATA_AUDIT/PS3_UPDATED_EDA.md`, `PS3_SUTRA/data/derived/eda_*`, `tools/eda_official.py`, `tools/eda_charts.py`. | 0.5 |
| 3.7 | Lineage, chain of custody & reproducibility | Chain of custody and verification discipline: Drive downloaded & hashed twice, **21/21 byte-identical**; cleaning guarantees (**0 rows dropped, 0 coordinates moved, 0 labels invented**, rules A1–A9 logged in `cleaning_log.csv`); the four published-figure corrections this pass issued. Sources: `PROJECT_DATA_AUDIT/README.md`, `PS3_UPDATED_DATA_LINEAGE.md`, `PS3_SUTRA/data/cleaned/cleaning_log.csv`, `tools/clean_official.py`. | 0.5 |

---

## 4 · ARCHITECTURE & SYSTEM DESIGN — 5 pages (pp. 16–20)

| ID | Subtopic | What it includes (content · repo sources) | Pages |
|---|---|---|---:|
| 4.1 | The locked architecture | The binding architecture: **4 layers**, the **27-question** commission set answered (A–T), the pruned pipeline (from `address → ML → coordinates` to deterministic candidates + memory + evidence), cross-cutting rules, failure paths, self-falsification criteria; the lock process (options → selection → due diligence → lock candidate → freeze; external data rejected). Sources: `PS3_MASTER_ARCHITECTURE.md`, `PS3_ARCHITECTURE_LOCK_CANDIDATE_2026-10-07.md`, `PS3_FINAL_DATA_AND_ARCHITECTURE_FREEZE.md`, `PS3_ARCHITECTURE_{OPTIONS,SELECTION,REQUIREMENTS_RECONCILED}.md`. | 1.0 |
| 4.2 | Candidate generation & ranking | The **8 candidate arms** (baseline, landmarks, hierarchy, etc.), additive reason scoring, `arm_prior`; the deterministic candidate build with receipts (`candidates_v2.csv` + receipt). Sources: `sutra/candidates.py`, `sutra/ranking.py`, `tools/build_candidates.py`, `data/derived/candidates_v2.*`. | 0.75 |
| 4.3 | Evidence, belief & address memory | The evidence model: weighted, reason-coded visit evidence, independence tuple, negative-evidence policy (never moves a coordinate; raises suspicion → `MOVED_SUSPECTED`, queues re-verification); belief as a pure function of the store at `as_of`; memory lifecycle (identity, decay, contradiction resolution, states). Sources: `sutra/evidence.py`, `sutra/belief.py`, `sutra/memory.py`, `PS3_FIELD_EVIDENCE_ARCHITECTURE.md`, `PS3_ADDRESS_MEMORY_ARCHITECTURE.md`, `data/derived/evidence_memory_policy_report.md`. | 1.0 |
| 4.4 | Uncertainty & calibrated radius | The published uncertainty contract: tier + calibrated radius with its empirical basis; `radius-map-v1` (locality **539.9 m p80, n=24, coverage 0.792** → publishable; street/pincode/rooftop withheld n<15 → fallback); per-stratum radius transfer. Sources: `sutra/uncertainty.py`, `PS3_UNCERTAINTY_ARCHITECTURE.md`, `data/derived/derived_ps3_radius_calibration.csv`, `updated_radius_by_stratum.csv`. | 0.75 |
| 4.5 | Dynamic learning: fast loop / slow loop | Two-speed learning with gates, drift detection, rollback; the order of operations imposed by the leakage map; why the loop is deliberately slow. Sources: `PS3_DYNAMIC_LEARNING_ARCHITECTURE.md`, `sutra/learning.py`, `PS3_UPDATED_LEAKAGE_MAP.md`. | 0.75 |
| 4.6 | Eligibility gate, refusal & purpose | The gate: `SERVE` / `VERIFY_FIRST` / `REFUSE` with **11 reason codes**; eligibility purpose-module (what may be served at all); landmark direction cues; cold-start handling. Sources: `sutra/eligibility.py`, `sutra/purpose.py`, `sutra/directions.py`, `PS3_PURPOSE_AND_DIRECTION_MODULES.md`, `PS3_FINAL_REPORT.md` §K. | 0.75 |

---

## 5 · IMPLEMENTATION & CODE ANALYSIS — 6 pages (pp. 21–26)

| ID | Subtopic | What it includes (content · repo sources) | Pages |
|---|---|---|---:|
| 5.1 | Backend runtime engine (`sutra/`) | Module map and responsibilities of the 30-module / ~7,759-LOC Python package (api, asof, belief, candidates, evidence, geo, indexes, memory, ranking, resolve, splits, store, uncertainty, views…); as-of discipline; the store (`Store`), runtime indexes and packs; `version.py` schema tags (`sutra-1.0`, `candidate-rules-v2`, `protocol-v1-immutable`). Sources: `PS3_SUTRA/sutra/*.py`, `SUTRA_BACKEND_GAP_AUDIT_2026-10-08.md`. | 1.0 |
| 5.2 | Pipeline tooling & reproducibility (`tools/`) | The 28 tools (~10,241 LOC): audit → clean → candidates/features → supervision firewall → runtime indexes → experiments → acceptance; machine guards (`check_workspace.py`, `check_leakage.py`, `check_links.py`); receipts attached to every derived artefact; one-command reproduction (`tools/reproduce.sh`). Sources: `PS3_SUTRA/tools/*.py`, `data/derived/*.receipt.json`. | 1.0 |
| 5.3 | HTTP API surface | The 6 implemented routes on a stdlib `ThreadingHTTPServer` (`serve_runtime.py`, port 8000): `/health`, `POST /resolve`, place state, verify-first tasks, packs, plane/geometry; error vocabulary; what the design specified vs what ships (gap-audit method: every "IMPLEMENTED" verified by live call). Sources: `sutra/api.py`, `tools/serve_runtime.py`, `SUTRA_BACKEND_GAP_AUDIT_2026-10-08.md`, `PS3_API_AND_COMPONENT_DESIGN.md`. | 0.75 |
| 5.4 | Frontends (`web/` product UI + `battle_model/` workbench) | Two React/TS frontends: `web/` (6 pages — Resolve, Places, Evidence, Queue, Method, Operations; API client layer with validation; ~3,384 LOC) and `battle_model/` (the Drive-retrieved workbench now wired to the live service, fixtures deleted, 6 views + 447-line SVG `LocalPlaneMap`); build/serve model (service serves the workbench at `/`). Sources: `PS3_SUTRA/web/src/**`, `PS3_SUTRA/battle_model/src/**`, `SUTRA_FINAL_INTEGRATION_REPORT_2026-10-08.md`. | 1.0 |
| 5.5 | Battle-Model forensic code analysis | The line-by-line audit of the retrieved frontend: provenance (22/22 files byte-identical to zip; Drive folder export omits `vite.config.ts` → unbuildable as-is); the data seam (`lib/api.ts`, 6 fetchers — right shape, wrong addresses: 3 of 6 documented routes never existed); the central finding — **every operational value fabricated** in `fixtures.ts` (548 lines: invented coordinates, 3-dp score decompositions, invented providers, fake audit ledger SEAL-01); what it admits (a replay, labelled twice); engineering quality and verdict. Sources: `WORK_CODE_ANALYSIS_2026-10-08.md` §§0–6, `uploads/battle_model_zip/src/lib/fixtures.ts`. | 1.0 |
| 5.6 | Tests & machine guards | The 4 test suites (~2,121 LOC): `test_acceptance.py`, `test_contract_v1.py`, `test_no_fake_data.py` (the fixture-excision guarantee), `test_product_v1.py`; acceptance report (`data/derived/acceptance_report.json`); workspace guard semantics (no training until freeze). Sources: `PS3_SUTRA/tests/*.py`, `tools/run_acceptance_tests.py`, `tools/check_workspace.py`. | 1.25 |

---

## 6 · EXPERIMENTS, EVALUATION & RESULTS — 4 pages (pp. 27–30)

| ID | Subtopic | What it includes (content · repo sources) | Pages |
|---|---|---|---:|
| 6.1 | Evaluation discipline & leakage firewall | T0–T4 feature staging vs lanes; the banned-feature list; entity-leakage register (place proximity **36.0%**); place-block group folds — **3,007 blocks / 5 spatially ordered folds**, 39 blocks crossing the official split; transform-fit discipline; supervision firewall/manifest. Sources: `PS3_LEAKAGE_AND_VALIDATION.md`, `PS3_UPDATED_LEAKAGE_MAP.md`, `tools/place_block_folds.py`, `data/derived/ps3_place_blocks.csv`, `supervision_firewall.csv`. | 1.0 |
| 6.2 | Pre-registered experiments A–D | The pre-registered grid A–O and the four executed experiments with receipts: **A** (candidate arms / ranking), **B** (preprocessing ablation B1–B4 — does text sophistication pay?), **C**, **D**; reporting template, metric set, kill criteria; what each concluded. Sources: `PS3_EXPERIMENT_PLAN.md`, `PS3_MODEL_SELECTION.md`, `tools/experiment_{a,b,c,d}.py`, `data/derived/experiment_*_report.{md,json}`, `experiment_*_results.csv`. | 1.0 |
| 6.3 | Warm/cold replay & evaluation populations | The corrected headline numbers: warm **56.0%** vs cold **24.5%** (val+test 56.7% vs 25.1%); the three evaluation populations kept separate (surveyed n=100 / warm replay / cold start); what this says about where the value is (memory + evidence, not a bigger model); candidate-anchor measurement. Sources: `PROJECT_DATA_AUDIT/README.md` (correction 1), `sutra/replay.py`, `data/derived/labels_eval_v2.csv`, `PS3_FINAL_REPORT.md` §L. | 1.0 |
| 6.4 | Precision optimization research | The `research/precision` programme (20 modules: rank2, sib/sib2, temporal, lexicon, lm, sim, bound…), the precision-optimization experiment and its bottleneck table, final frozen config (`final_precision_config.json`) and why frozen precision must not be retuned ad hoc `[S95]`. Sources: `PS3_SUTRA/research/precision/**`, `tools/precision_opt.py`, `data/derived/precision_optimization_report.md`, `final_precision_config.json`. | 1.0 |

---

## 7 · PRODUCT, UX & INTEGRATION — 3 pages (pp. 31–33)

| ID | Subtopic | What it includes (content · repo sources) | Pages |
|---|---|---|---:|
| 7.1 | From backend gap audit to product surface | Phase-0 method (nothing inferred from docs; every status verified by live call); the item status table (IMPLEMENTED / DESIGNED / NOT YET IMPLEMENTED / NOT MEASURED); what this exposed about docs-vs-code drift. Sources: `SUTRA_BACKEND_GAP_AUDIT_2026-10-08.md`. | 0.75 |
| 7.2 | Contract v1 & the UX specification | `SUTRA_FRONTEND_BACKEND_CONTRACT_V1` (typed responses, reason codes, decision ticket); the UX spec (screens, states, judge journey, abstention as a designed state, live as-of clock); UI/UX research basis and its sources register. Sources: `SUTRA_FRONTEND_BACKEND_CONTRACT_V1_2026-10-08.md`, `SUTRA_PRODUCT_UX_SPEC_2026-10-08.md`, `SUTRA_UIUX_FRONTEND_RESEARCH_2026-10-08.md`, `SUTRA_UIUX_RESEARCH_SOURCES_2026-10-08.md`. | 1.0 |
| 7.3 | Integration verification, smoke tests & demo | The fixture-excision pass and new guards; what was actually executed (browser smoke `tools/browser_smoke.mjs`, `SUTRA_FRONTEND_SMOKE_REPORT`, 26 screenshots `bm-*` + `01–13`); the 3-minute judge demo script with real runtime values (3,117 addresses indexed, 5,578 observations, 2,757 stored beliefs, 278 open tasks at as-of 2026-06-01). Sources: `SUTRA_FINAL_INTEGRATION_REPORT_2026-10-08.md`, `SUTRA_JUDGE_DEMO_SCRIPT_2026-10-08.md`, `SUTRA_FRONTEND_SMOKE_REPORT_2026-10-08.md`, `screenshots/`. | 1.25 |

---

## 8 · GOVERNANCE, RISK & RED TEAM — 3 pages (pp. 34–36)

| ID | Subtopic | What it includes (content · repo sources) | Pages |
|---|---|---|---:|
| 8.1 | Decision log & change sets | How decisions are recorded (every decision with evidence + reversibility): decision log D-numbers (through D25–D31 from the re-audit), amendment register A0–E1, implementation contracts as normative schemas; workspace manifest & source register (`PS3_SOURCE_REGISTER.md` — every external claim with URL/licence class). Sources: `PS3_DECISION_LOG.md`, `PS3_ARCHITECTURE_CHANGE_SET_2026-10-07.md`, `PS3_IMPLEMENTATION_CONTRACTS_2026-10-07.md`, `PS3_SOURCE_REGISTER.md`, `PS3_WORKSPACE_MANIFEST.md`. | 0.75 |
| 8.2 | Red team: 22 failure classes | The 22 failure classes each answered with detect / quantify / mitigate / monitor; which are covered by data vs designed-for-but-untestable-on-synthetic-data (e.g., GPS spoofing); assumptions register. Sources: `PS3_RED_TEAM.md`, `PS3_ASSUMPTIONS.md`, `PS3_FINAL_REPORT.md` §P. | 1.0 |
| 8.3 | Novelty, cost & MLOps guardrails | The six defensible claims and what the project **refuses** to claim; the business/operational rethink (A–T: workflow, waste, knowledge loop, offline design, economics, "what in SUTRA is wrong"); cost architecture (substitution ladder, do-not-ship floor); MLOps (environments, versioning, monitoring, incidents). Sources: `PS3_NOVELTY_AND_DIFFERENTIATION.md`, `PS3_BUSINESS_AND_OPERATIONAL_RETHINK.md`, `PS3_COST_ARCHITECTURE.md`, `PS3_MLOPS_ARCHITECTURE.md`, `PS3_FINAL_REPORT.md` §§N–Q. | 1.25 |

---

## 9 · CONSOLIDATED FINDINGS & RECOMMENDATIONS — 2 pages (pp. 37–38)

| ID | Subtopic | What it includes (content · repo sources) | Pages |
|---|---|---|---:|
| 9.1 | Strengths / weaknesses / gaps matrix | The report's own assessment, evidenced by earlier sections: strengths (verification culture, receipts, leakage discipline, abstention-first design, honest correction of its own numbers); weaknesses/gaps (n=100 ground truth ceiling; synthetic-data limits; no model trained yet; three designed-not-built surfaces; single squashed commit history). Sources: cross-references to §§1–8; `PS3_FINAL_REPORT.md` §R. | 1.0 |
| 9.2 | Recommendations & roadmap | The project's own roadmap plus the report's recommendations: what would prove it wrong (self-falsification criteria), next implementable steps (slow-loop activation, precision unfreeze protocol, real-data pilot design), and documentation/process suggestions (e.g., restore granular git history). Sources: `PS3_FINAL_REPORT.md` §R, `PS3_MASTER_ARCHITECTURE.md` §6, `PS3_ARCHITECTURE_DUE_DILIGENCE_2026-10-07.md`. | 1.0 |

---

## AX · ANNEXURES — 2 pages (pp. 39–40)

| ID | Subtopic | What it includes (content · repo sources) | Pages |
|---|---|---|---:|
| AX.A | Source-to-section traceability map | One table: every subtopic above ↔ the repo files it cited — proving full coverage and nothing fabricated. Sources: this index. | 0.75 |
| AX.B | Metrics register | Every quantitative claim used in the report, each with its n, its source file and its `[VERIFIED]/[INFERENCE]` status (e.g., 1,603 m · n=100 surveyed · `PS3_DATA_AUDIT.md` §0). | 0.75 |
| AX.C | Glossary & archive inventory | Terms (arm, as-of, belief, block fold, cold/warm, DPD, gate, p80, T0–T4, tier) + one paragraph on what each archive folder holds and why it is out of scope. | 0.5 |

---

## WRITING CONVENTIONS (apply throughout)

1. **Evidence discipline:** every number carries its n and its file source; reuse `[VERIFIED]` / `[INFERENCE]` / `[UNKNOWN]`.
2. **Figures to include (budgeted inside their sections):** repo tree diagram (§1.2), dataset relationship diagram (§3.1), T0–T4 lane diagram (§3.2/§6.1), pipeline block diagram (§4.1), radius-map table (§4.4), before/after Battle-Model integration table (§5.4–5.5), warm/cold bar comparison (§6.3), 2–4 screenshots (§7.3).
3. **Honesty rules inherited from the repo:** state that the dataset is synthetic; no accuracy claims beyond the n=100 sample; report what is *not* built (DESIGNED / NOT YET IMPLEMENTED) as plainly as what is.
4. **Hard cap:** if any section overruns, cut from §3.6, §7.1, §8.3 first — never from FM.3, §5.5, §6.3 or §9 (the sections that carry the report's argument).
