# SUTRA — FINAL CONSOLIDATED REPORT (A–R)

**Project:** SUTRA — *Address Geocoder That Learns from Field Visits* (official Problem Statement 3).
**Status:** research, data audit, data discovery, cleaning, architecture design and preprocessing design are **complete**;
**no model has been trained, and none may be trained until this document set is frozen.**
**Every number is either measured on the official synthetic dataset (labelled SYNTHETIC — mechanism, never magnitude),
sourced in `PS3_SOURCE_REGISTER.md`, or explicitly marked as simulation/injection-based.**

Section index: **A** the problem · **B** the data · **C** labels and trust · **D** cleaning, preprocessing, leakage ·
**E** what the world does · **F** architecture · **G** field evidence and integrity · **H** address memory ·
**I** uncertainty · **J** dynamic learning · **K** API and components · **L** validation and experiments ·
**M** model selection · **N** cost · **O** MLOps and governance · **P** red team · **Q** novelty and claims ·
**R** roadmap and falsification.

---

## A — The problem, stated exactly

Collections operations send agents to addresses that are written badly and geocoded worse. Three facts from the official
data define the task:

1. The vendor geocoder leaves **237 records (7.6%) ungeocoded** and, where it does answer, it is **coarse**: on 100
   surveyed addresses the median error is **376.4 m**, and only **9.0%** are within 100 m. The modal stratum is
   *locality-level* (2,052 of 2,880 pins; 71%).
2. **Field visits already happen** — 5,578 of them, covering 1,477 addresses (47.4%) — and they carry GPS trails, dwell
   times, photos and outcomes. This is a signal nobody else is using in this book.
3. **The visits are not truth.** They are evidence of differing quality, and some of them are actively misleading (§C).

So the prediction problem is **not** "address → coordinates". It is: *given a badly written address and a poor vendor pin,
which of a small set of plausible places is the record — and how much should what the field has observed change what we
believe about that place?* The answer must be delivered with a granularity, a **measured radius**, a reason, and a memory
that can be audited.

**What we are explicitly not solving:** global geocoding, routing, beat optimisation, or any claim of India-scale coverage.
SUTRA is per-town, per-book, and built to get better with every visit.

---

## B — The data (audit in brief; full detail in `PS3_DATA_AUDIT.md`)

| Table | Rows | Key facts that shaped the design |
|---|---|---|
| `addresses` | 3,117 | median 67 chars; **24.9% have no comma**; 9 have no digits; 8.4% carry Devanagari/Kannada; **237 are `town_id='OUT'`**; 10 share a normalised text |
| `baseline_geocodes` | 2,880 | strata locality 2,052 / street 504 / pincode 274 / rooftop 50; **no pin piles** (largest = 1) |
| `surveyed_addresses` | **100** | the only ground truth: T1 33 / T2 29 / T3 38; 0 `OUT`; 1 rooftop |
| `field_visits` | 5,578 | outcomes: met_borrower 20.0% · met_family 19.0% · locked_premises 22.4% · **address_not_traceable 25.1%**; 443 visits < 60 s |
| `visit_gps_points` | 160,406 | median 26 points/visit; accuracy median 10 m; **max implied speed 32.2 km/h, no teleports**; 34 axis artefacts |
| `localities` | 36 | 35 names for 36 rows — `Nehru Colony` exists in two towns with different pincodes |
| `landmarks_poi` | 240 | only **14 distinct names**, 198 duplicate `(town, name)` pairs → unusable as a coordinate target |
| `towns`, `agents`, `accounts`, `splits` | 3 / 30 / 2,400 / 2,400 | splits are account-level only; accounts are demand context, never location features |

Measured error vs the vendor pin on the surveyed 100: overall median **376.4 m** (p90 839.2 m); by stratum —
rooftop 25.6 (n=1) · street 108.6 (n=16) · locality **385.9** (n=73) · pincode **1,375.8** (n=10, max 4,808).

---

## C — Labels and trust: what a visit really means

The single most consequential measurement in this project:

| Outcome (on the surveyed subset) | n | median dist. to **truth** | median dist. to **vendor pin** | closer to pin | median dwell |
|---|---|---|---|---|---|
| met_borrower / met_family / cash_collected | 93 | **29.3 m** | 396.9 m | 3.2% | 9.7 min |
| `address_not_traceable` | 53 | **1,603.2 m** | 253.4 m | **84.9%** | **1.3 min** |

**Reading:** success visits converge on the truth; **failure visits converge on the pin** — the agent walked to where our
bad geocode pointed, failed, and left. Therefore:

* **A single `address_not_traceable` can never relocate a coordinate by itself.** It is evidence about the *record* and
  the *agent*: one negative observation can never relocate a coordinate by itself; accumulated independent negative evidence demotes confidence, widens the radius, marks `MOVED_SUSPECTED`/`CONTESTED` and triggers re-verification; only positive evidence or adjudication can establish a new primary coordinate (F2.1/D36). (`PS3_RED_TEAM.md` F15)
* **"The field GPS agrees with our pin" is a failure signal, not a confirmation** — the feature is banned by name
  (`PS3_LEAKAGE_AND_VALIDATION.md` §2, row 4).
* Outcomes are split into **two dimensions**: *place* evidence and *person* evidence. `locked_premises` is weak
  place-positive, person-indeterminate; `no_such_person` is place-positive, person-negative ("the house is right, the
  household may have moved").
* **A visit is never promoted to ground truth.** Only the 100 surveyed records and human adjudications are truth.

Other trust facts: the integrity anomaly in this data is **not GPS** — agent FA009 carries **156 duplicate photo hashes out
of 610 visits (25.6%)** while every other agent is <0.3% and its trails are clean. And exposure is demand-driven: visit
rate rises **19.9% → 84.8%** from the lowest to the highest delinquency band, so any improvement claim needs weighting and
an exploration slice (`PS3_LEAKAGE_AND_VALIDATION.md` §6).

---

## D — Cleaning, preprocessing and leakage safety

* **Domain A stays byte-identical**; cleaning writes to `data/cleaned/` with a **row-level log** (15 rules): text
  normalisation preserving the raw, six descriptive flags (including `pin_unknown` for 260 records whose 6-digit token
  matches no pincode, and `flag_outside_town` for 237), rule-based span extraction, the outcome split, and the removal of
  `ptp_id` (89.2% null, different problem). **No coordinate is moved; no label invented**; 34 axis-artefact GPS points
  (0.021%) are flagged and excluded from evidence — that is the only drop.
* **Preprocessing is deterministic and cheap** (cleaning 9 s, candidates+features 23 s for 3,117 records, one CPU). Three
  text tiers: tokens+spans+char-3-grams ship; TF-IDF/SVD is BUILD IF TIME; embeddings/LLM are RESEARCH ONLY.
* **Leakage is structural, not stylistic.** Five stages (T0 pre-geocode, T1 candidates, T2 in-visit, T3 post-visit, T4
  later outcomes) with a per-field map (`data/derived/ps3_leakage_map.csv`), and **12 banned patterns enforced in code**
  (`tools/check_leakage.py`): no `surveyed_*`, no visit outcome of the scored visit, no future observations (as-of joins
  only), no pin-agreement, no account fields, no entity duplication across splits, no fitting statistics on test.
* **Splits are entity- and time-aware**: `splits.csv` (1,680/360/360 accounts) extended by a `split_ledger` grouping on
  `group_key = hash(account, normalised text, town)`; the 100 surveyed records form S-Eval and are never trained on.

---

## E — What the world does (and what we take from it)

Reverse-engineered with the 13-question template (`PS3_REAL_SYSTEMS_RESEARCH.md`):

* **Google** separates *geocoding* (with `location_type`) from *address validation* (`validationGranularity`,
  `addressComplete`, inferred components); **Mapbox** returns per-component match codes and sells permanent geocoding;
  **HERE/TomTom** echo the same shape; **Mappls** returns a 6-character eLoc. The industry's answer to incomplete addresses
  is a **granularity vocabulary**, not an error — SUTRA copies that and adds a **calibrated radius**, which none of them
  publish.
* **India:** GeoIndia predicts H3 cells (hierarchy beats coordinate regression) with **delivery traces as labels**; SAGEL
  reports 64.3% <100 m vs Google's 23.8% on its own benchmark; Shiprocket publishes 72.69%/90.57% at 100 m/500 m; Delhivery
  verifies addresses against **visit history**. Lesson: the field is the label factory — nobody surveyed publishes what
  SUTRA publishes (weighted memory + measured radius + negative-evidence semantics).
* **Parsing:** libpostal 98.9% full-parse; deepparse slower, similar; an Indic parser at <30 ms; practitioner evidence of
  **~240× latency** for comparable field accuracy → rules first.
* **Uncertainty:** geographically weighted conformal reaches **93.67% coverage at 90% nominal** where bootstrap under-covers
  at 81%; Android's `getAccuracy()` is a **68% radial confidence** and exposes `isMock()`.
* **External data: REJECTED by the final project decision (2026-10-07).** External-data augmentation was considered during
  research but rejected; the final PS3 system uses only the official CreditNirvana dataset and the legitimately
  PS3-relevant shared data. No external, scraped, downloaded or third-party geographic source enters candidate generation,
  training or any metric. The rejected evaluation is archived; the binding statement is
  `PS3_FINAL_DATA_AND_ARCHITECTURE_FREEZE.md` §DATA.

---

## F — The architecture (and what changed from `address → ML → coordinates`)

The full block diagram, the §12 pruning and the 27 answered questions are in `PS3_MASTER_ARCHITECTURE.md`. In brief:

```
RAW ADDRESS → S0 ingest → S1 normalise/parse → S2 resolve → S3 gazetteer index
            → S4 candidate generation (vendor · locality · town · external · memory-as-of)
            → S5 ranker → S6 point fallback → S7 belief fusion ← memory(prior)
            → S8 uncertainty (tier + measured radius + reasons) → SERVE
FIELD VISIT → S9 evidence features → S10 integrity (weights) → S11 belief update (append-only)
            → S12 address memory → (buffer) → S13 slow loop → champion/challenger
```

**What the naive pipeline cannot express, and this one can:** two plausible places; a reason per candidate; a doubt that is
quantified; evidence that is weighted rather than trusted; history that contradicts itself safely; refusal as a legitimate
answer. Measured justification: the **oracle over the current arms is 306.2 m vs the vendor's 376.4 m** — ranking those arms
buys ~19%, so the architecture invests in memory, evidence and external anchors rather than in a bigger ranker.

**Classification (BUILD NOW / IF TIME / PRODUCTION / RESEARCH ONLY):** S0–S12 BUILD NOW · S13 BUILD IF TIME (designed as
PRODUCTION) · S14/S15 BUILD IF TIME · S16 embeddings/LLM, S17 map matching (no road graph), S18 RL/bandits RESEARCH ONLY.

---

## G — Field evidence and integrity: *weight, don't accuse*

Per visit, SUTRA stores an **evidence score** with two dimensions and reason codes:
`w_place` and `w_person`, composed multiplicatively from outcome dimension × dwell band × trail agreement × media
integrity × accuracy class × a **rolling agent baseline** × recency.

* No single signal can zero a visit; **absence of usable evidence** is a recorded state (`insufficient_evidence`), not a
  suspicion.
* Integrity rules: mock flag, speed plausibility, coordinate reuse, duplicate/perceptual-hash media, trail↔check-in
  disagreement, dwell realism, agent-deviation z-scores — each producing a **weight and a reason**, never an accusation
  (`PS3_FIELD_EVIDENCE_ARCHITECTURE.md` §4).
* **Promotion requires two independent confirmations** (different visit, different day, sufficient weight, not traceable to
  the same media hash or agent-day cluster).
* The fault-injection bed measures recall, false-positive rate on clean visits, and detection delay — and every figure is
  labelled *injection-based*, because this dataset contains no spoofing to measure.

---

## H — Address memory: the asset

A **place-keyed, append-only** memory: belief versions with positions, tier, radius, support and reasons; observations as
the only clock; evidence scores with policy versions; merge/split events; alias evidence; verification tasks.

* **Never overwritten.** Corrections are new versions citing a reason; nothing is edited or deleted (compaction keeps
  summaries while preserving decision-bearing versions).
* **Never averaged.** Positions are candidate-backed (address point, locality centroid, building anchor, evidence cluster).
  Averaging produces coordinates that correspond to no real place.
* **Contradictions are a state** (`CONTESTED`): both supports are kept, the radius widens, a task is queued; resolution needs
  a high-integrity third visit or adjudication — and a *moved* address needs two independent confirmations before the
  primary changes.
* **States:** `UNSEEN → COLD → WARM → CONFIRMED → STALE`, plus `CONTESTED` and `UNPLACEABLE` (with `OUT` as a first-class
  reason). The 237 `OUT` records are a state the system holds honestly, indefinitely.
* **Why a cache cannot replace it:** a cache has no credibility, no decay, no provenance, no reasons — and it serves
  whichever value was written last, including a poisoned one.

---

## I — Uncertainty: the contract we publish

Every answer carries `granularity` (town/locality/street/rooftop), `tier` (CONFIRMED/PROBABLE/APPROXIMATE/UNPLACEABLE),
`radius_m` with `nominal` **and measured coverage**, and reason codes.

* The radius comes from **geographically weighted split conformal** [GeoConformal/GeoXCP], not bootstrap (81% observed
  against a 90% claim) and not from the vendor's vocabulary.
* **Honest about thin data:** locality (n=73) and street (n=16) are calibratable; pincode (n=10) and rooftop (n=1) are
  **below the n ≥ 15 guard** → parent-stratum fallback, widened radius, reason `calibration_fallback`.
* **Negative evidence and refusal are explicit**: refusals are counted, and the correctness of refusals is reported.
* Radius widens with staleness and offline **pack age** — staleness is visible, never silent.

---

## J — Dynamic learning: two speeds, one rule

**Fast loop (milliseconds, no training):** visit → evidence features → integrity weights → append belief version → update
memory → side effects (re-verification task, review flag) → add to the slow loop's buffer. Idempotent by `visit_id`;
bounded (one visit can move belief by at most one tier step and can never promote alone); fully reversible by appending.

**Slow loop (gated, weekly–monthly):** quality-gated buffer → window assembly that excludes label lag → four drift streams
(ADWIN on error/coverage, uncertainty, feature PSI, outcome mix) with cooldown, hysteresis, minimum-buffer and seasonality
rules → full retrain with **warm start** → recalibration → **challenger evaluation** (7 gates, coverage is a gate, not a
diagnostic) → promote by registry alias, with a **pre-declared rollback alarm**.

**What updates instantly vs what waits:** beliefs, tiers, radii, reasons, priorities — instantly. Model parameters and the
calibration map — only through the slow loop. **Never retrain after a visit** (the published comparison that justifies the
trigger design: 16 retrains with a good trigger vs 345 with a naive one).

**Honest limitation:** visits span 2026-04-01 → 06-29 (90 days, no known regime change), so drift behaviour is evaluated by
**replay simulation** (cold/warm, weekly cut-points, injected drift, injected poisoning, varied label lag) and every such
result is labelled simulation.

---

## K — API and components (how it is actually used)

Nine components — `ingest · resolver · candidates · ranker · belief · uncertainty · evidence · memory · slowloop` — and a
small API (`PS3_API_AND_COMPONENT_DESIGN.md`):

* `POST /v1/resolve` — pre-visit answer (T1): coordinate **with** granularity, tier, radius, coverage, reasons,
  `alternatives[]`, `arms_available[]`, and an eligibility flag.
* `POST /v1/score_visit` — in-visit answer (T2): "you are 210 m from a locality-level pin with a 210 m radius; check the
  cross street". It **cannot** move a coordinate (`coordinate_moved: false` by construction).
* `POST /v1/ingest_evidence` — post-visit write (T3): returns the evidence weight, reason codes, the new belief version, and
  often `changed: false` (a confirmation should not be dramatic).
* `POST /v1/adjudicate`, `GET /v1/belief?as_of=…`, `GET /v1/place/…/history`, `GET /v1/tasks`, `POST /v1/batch_resolve`,
  `GET /v1/health`, `GET /v1/audit/{belief_id}`.

Deliberately absent: a bare `geocode(text)→lat,lon` endpoint; a single "confidence" number; any external write path into
memory; any admin edit of a belief. Refusals and fallbacks return as 200-level states with reasons — errors are for
malfunction, not for a hard world.

---

## L — Validation and the pre-registered experiment grid (A–O)

Fixed metric set (never one metric): median/p75/p90 error · hit-rate <50/<100/<250/<500 m · precision@1 · nDCG@5 · tier mix ·
refusal rate **and its correctness** · measured coverage vs nominal · ECE · per-stratum with the n ≥ 15 guard · cost per
1,000 resolves · p95 latency · integrity precision/recall on the injection bed. Every visit-based metric is reported
**unweighted and exposure-weighted**, with grouped bootstrap intervals, and every run prints the **negative controls**
(shuffled labels ≈ chance, agent-ID-only, vendor-only, random arm).

The grid: **A** official frozen baseline geocode arm · **B** preprocessing ablations · **C** retrieval only · **D** retrieval+ranking ·
**E** uncertainty/calibration · **F** vendor+field learning (the core hypothesis) · **G** full SUTRA · **H** official-only
floor · **I** official+external ablation · **J** dynamic-retrain simulation · **K** integrity ablation · **L** memory
ablation · **M** negative-evidence ablation (the safety experiment) · **N** static vs dynamic · **O** cold vs warm.
`PS3_EXPERIMENT_PLAN.md` also states, in advance, **what we expect each one to find**, so that surprises are visible
rather than quietly absorbed.

---

## M — Model selection (what ships, what does not)

| Component | Ships | Challenger | Rejected / research |
|---|---|---|---|
| Retrieval | rules + gazetteer + probabilistic linkage (Fellegi–Sunter) | BM25 (if time) | embeddings, LLM, cross-encoder |
| Ranker | shallow GBDT LambdaMART with monotone constraints (pairwise variant for small n); **rule priority is the fallback** | logistic regression | deep listwise, bandits |
| Point fallback | ridge or the prior, tier-capped at APPROXIMATE | small GBM | any narrow-radius model |
| Evidence | **likelihood table** (rule-first) | logistic → GBM with adjudications | deep trail models |
| Integrity | **rules** with weights | supervised scorer (weights only) | GPS-only detector, unsupervised outlier |
| Radius | geographically weighted conformal | quantile GBM | bootstrap, fixed radius |
| Purpose gate | rules | logistic/GBM to *inform* | LLM |

Small-data protocol (2026-10-07, contracts §2): S-Eval = the 100 surveyed, never trained/tuned; nested grouped CV on operational S-Val supervision with the S-Eval firewall; ≤15 features (≤6 for evidence), monotone
constraints, no calibration on training rows, complexity ladder (rules → table → shallow GBM) where each rung must beat the
previous beyond the interval. **Nothing here needs a GPU.**

---

## N — Cost architecture

Correctness first, then substitutes. Vendor calls are kept off the critical path (memory before vendor; cache with a
licence clock — Google's 30-day limit applies); candidate generation is capped at 25; reranking is conditional; external
indices are local; the slow loop costs < 10 minutes of CPU. We publish **no invented prices** — commercial geocoding is
volume- and licence-negotiated, so what is published is the *structure* and the **substitution ladder** (drop the ranker →
reduce parsing tiers → fewer vendor calls → quarterly retraining; external arms are not in the ladder because they are
prohibited), with a stated **floor**: the
integrity weighting and the calibrated radius are never traded away, because without them the product returns confident
coordinates instead of honest ones.

---

## O — MLOps and governance

Versioning everywhere (`source_snapshot`, `rule_version`, `schema_version`, `policy_version`, `radius_map_version`, model
alias, pack version, split-ledger version), and **every response records the versions it used**, so any coordinate ever
served can be reconstructed. Four monitoring layers (data, model/drift, belief/loop, serving/cost) plus a **fairness
monitor** that publishes the clean-visit false-positive rate alongside every integrity flag. Promotion needs all seven
gates and a human approval; rollback is a single alias flip. Incident playbooks cover vendor outage, memory outage,
poisoning, drift-during-data-incident, calibration regression, licence expiry and CRS surprises. Five ownership roles, no
more; every alarm maps to one of them.

---

## P — Red team (22 failure classes, answered in full)

Each of `PS3_RED_TEAM.md`'s classes is answered with **detect · quantify · mitigate · rule-vs-learned · monitor** plus the
residual risk. The load-bearing ones:

* **Spoofing (F1)** — cross-signal detection; measured *only* on injected faults; we publish no detection rate.
* **Duplicate media (F2)** — the dataset's own anomaly (FA009, 25.6%) is detectable by hash, and its GPS is pristine.
* **Wrong-place check-ins (F3)** — solved by §C's measurement: a single failure never relocates a coordinate; only accumulated independent negatives demote/widen/re-verify (F2.1/D36).
* **Feedback poisoning (F6)** — concentration caps, two confirmations, agent scoping, append-only traceability.
* **Loop flattery (F7)** — exposure weights + exploration slice; weighted vs unweighted printed side by side.
* **Leakage (F8)** and **entity duplication (F9)** — mechanical guards and negative controls.
* **Overconfident radius (F10)** — coverage monitor with automatic widening.
* **Negative evidence (F15)** — a hard invariant, unit-tested, alarmed on any violation.
* **Metric myopia (F21)** — fixed plural metric set with a pre-registered primary.
* Plus cold start, vendor error, parsing failure, landmark ambiguity, memory growth, cost/latency, offline/outage,
  privacy/eligibility, data-subject manipulation, and CRS/schema drift.

The document ends with **claims we are forbidden to make** (no spoof-detection rate, no production drift latency, no
accuracy computed on check-ins or pins, no radius without measured coverage, no improvement claim without an exploration
slice) and a fault-injection bed that converts every detector claim into a measured one.

---

## Q — Novelty and what we refuse to claim

Not novel, and not claimed: geocoding, parsing, learning from traces, active learning, conformal prediction, drift-triggered
retraining, status vocabularies, propensity weighting.

The six defensible claims (each with support and an explicit limit): **C1** an address *memory* as the system of record
(append-only, place-keyed, decaying) rather than a geocoder cache; **C2** integrity-weighted evidence — *weight, don't
accuse*; **C3** graded negative evidence — never relocates by itself, demote/widen/re-verify only, relocation by positive evidence or adjudication (F2.1/D36); **C4** a calibrated radius published
with measured coverage, with labelled fallbacks for thin strata; **C5** a two-speed loop where the fast path is a product
feature (in-visit doubt) and the slow path is gated; **C6** exposure-aware learning with an exploration slice.

Publication-safe wording is fixed in `PS3_NOVELTY_AND_DIFFERENTIATION.md` §6: we may say "a field-visit-learned address
memory with measured uncertainty and integrity weighting"; we may **never** say "we built a geocoder", "we detect spoofing",
or "India-scale".

---

## R — Roadmap, and what would prove this wrong

**Order of work from here (the commission's sequence, respected):**

1. **Freeze this document set** and the toolchain (`tools/check_workspace.py`, `tools/check_leakage.py` both green;
   Domain A hash-verified).
2. **Then** the first training runs — experiments **A → B → C → D → E**, each with the fixed metric set and negative
   controls, at the 100-surveyed-record scale with grouped CV. Models only where §M says a model is justified.
3. **Memory and loop experiments** (F, K, L, M, N, O) with as-of discipline and simulation labels.
4. **No external-data ablation exists** (experiment I cancelled by the final data policy); J still runs as a labelled
   simulation on official historical visits. The official numbers are the only numbers.
5. **Demo-ready slice** (after correctness): the 48-hour demo surface implied by the requirements — a resolve, an
   in-visit hint, a scripted visit that flips a decision, and an injected low-integrity observation that **widens without
   moving** — all on synthetic data, all labelled.

**Self-falsification criteria (stated so the design can lose):**

* If the oracle over real arms stays near the vendor pin even after external anchors are added, retrieval is data-capped
  and the architecture must collapse toward memory + evidence only.
* If warm resolving (after ≥2 confirmations) does not beat cold beyond the interval, the memory's *accuracy* claim fails
  and it survives only as auditability and triage — and `PS3_NOVELTY_AND_DIFFERENTIATION.md` gets rewritten to say so.
* If measured coverage cannot be achieved at the nominal level for a stratum, we stop publishing nominal radii there and
  publish empirical hit-rates instead.
* If the integrity layer cannot separate injected faults without punishing clean visits, promotion returns to human
  adjudication only — less automation, not more.

**The one-sentence version of this report:** *SUTRA treats every field visit as weighted, reason-coded evidence; keeps
what it believes about a place in an append-only memory that decays and can hold contradictions; answers with a
granularity, a calibrated radius and a reason; refuses rather than fabricates; and changes its models only through a gated,
reversible loop — which is what makes it a geocoder that learns from field visits, and not another geocoder.*




## Addendum — official-scope re-audit (2026-10-07)

Six changes, none of which redraws the architecture; two corrections, both toward more conservative statements.

1. **Scope of record.** The official data scope is now complete: **12 tables** — the 6 task-specific tables plus the 6
   officially assigned shared tables (`accounts`, `addresses`, `agents`, `field_visits`, `lenders`, `splits`). The
   assigned `lenders` table was imported into the frozen tree and the hash set re-baselined. The two large shared
   tables assigned to *other* problem statements (`dial_attempts`, `payments`) are excluded — so this task provably has
   **no financial outcome variable**, and no claim here depends on one.
2. **Evaluation protocol v2** (Amendment A1): three populations per claim (all 100 surveyed · validation+test ·
   leave-block-out), with a place-block ledger built by `tools/place_block_folds.py`; the official account split is
   untouched. Why: **66 of the 100 surveyed truths are on train-split accounts** and **124 of 344 (36.0%)** met test
   addresses sit within 30 m of a train met check-in `[S94]`; block validation is the standard remedy where places, not
   rows, carry the signal [S67][S68].
3. **Radius rule** (Amendment U1): radii publish with `n_calibration`; below n=15 a stratum falls back to its parent,
   labelled; the pincode radius is **withheld** (79.2% vs 0% transfer at p80) [S69][S73].
4. **Place identity** (Amendment M1): evidence-keyed clusters with a `POSSIBLE_MATCH` review queue; never merged by
   account; the identity text key keeps the trailing token [S72]. Why: 81 clusters / 191 addresses across accounts, and
   a borrower's two addresses sit a median 3,011.6 m apart `[S94]`.
5. **Integrity and the loop** (Amendments F1, L1): integrity rests on media duplication and timing; the
   "645 check-ins >500 m" figure is **retracted** (max 90.8 m from the nearest own-trail point); **warm 56.0% vs cold
   24.5%** (val+test 56.7/25.1) replaces the mislabelled replay; the loop is evaluated **prequentially** and allocation
   **propensities are logged** from the first live window [S70][S71].
6. **Nothing is trained.** The amendment pass adds one deterministic tool, one derived ledger and documentation only.

**Source:** register group N `[S67]`–`[S73]`; re-audit measurements `[S94]`; decision-log entries D25–D31.

---

**Sources.** External claims resolve in `PS3_SOURCE_REGISTER.md` (`[S1]`–`[S73]`); internal measurements are
`[S90]` (audit log `data/derived/ps3_audit_full.txt`), `[S91]` (radius calibration
`data/derived/derived_ps3_radius_calibration.csv`) and `[S92]` (prior-pass measurements). Statements that cite no
external source rest on internal evidence and are labelled `[DATA]`/`[INFERENCE]` where they appear.
