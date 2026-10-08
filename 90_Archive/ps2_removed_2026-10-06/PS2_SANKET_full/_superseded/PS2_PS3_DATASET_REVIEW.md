# PS2 / PS3 — DETAILED DATASET REVIEW

**What this is.** A complete review of the official CreditNirvana synthetic collections dataset (Google Drive folder `18iqIR8TjXDqf9-hgEY34uJr_DraIl_3P`, 20 CSVs, 21 MB) reviewed specifically against **PS2 — Right-Party Contact Prediction and Skip-Trace Prioritisation** and **PS3 — Address Geocoder That Learns from Field Visits**, and against the requirement files `PS2_ARCHITECTURE_REQUIREMENTS.md` (R1.1–R13.2) and `PS3_ARCHITECTURE_REQUIREMENTS.md` (R1.1–R15.3).

**Status of the numbers.** Every figure below was computed from the downloaded CSVs by `dataset_audit.py` (reproducible with one command; see §11). They are tagged:

| Tag | Meaning |
|---|---|
| `[DATA]` | computed directly from the dataset — reproducible, but **synthetic** |
| `[DATA→READ]` | computed from the dataset, then interpreted (the interpretation is ours) |
| `[GAP]` | the requirement needs a field, table or label that **does not exist** in the dataset |
| `[ASSUMPTION]` | outside the data; must be a named parameter, never a presented fact |

**The one rule that governs everything below.** The README states plainly: *"Everything in it is invented."* So this dataset can prove **mechanism** — that a pipeline runs, that a signal exists, that a failure mode is real and detectable. It can never prove **magnitude** — not an accuracy, not an ROI, not a market claim. Any number in a demo must be labelled `SYNTHETIC`.

---

## 0. Headline: the five things this review changes

| # | Finding | Consequence for the build |
|---|---|---|
| **1** | The randomised holdout in PS2 is **5.4%** of attempts and is *confounded*; the "random contact point" arm performs **worse** than the incumbent (13.4% vs 16.6% RPC). `[DATA]` | No uplift claim is possible. The benchmark is **the incumbent**, not a random baseline. R10.4 stops being a policy preference and becomes a data fact. |
| **2** | The learnable PS2 signal is **contactability memory** (what happened on *this point* before), not account financials. Permutation importance: prior-RPC **0.089**, self-relation **0.028**, hour-of-day **0.027**, everything else ≤0.009. `[DATA]` | SANKET's centre of gravity moves to the point-level state table + rules floor; the financial feature set is decoration. |
| **3** | **Skip-trace prioritisation cannot be an ML success model here**: predicting trace success from pre-trace features gives CV AUC **0.574** against a 0.772 majority-class baseline. `[DATA]` | Replace "trace after N failures" with an **EVSI-style rule** whose cost is a named parameter, and report the hit rate honestly: **77% of trace spend produced nothing**. |
| **4** | **PS3 cannot beat the commercial geocoder on accuracy with free data.** Locality centroid = **376–379 m** median vs baseline **376 m**; the oracle over all 12 candidate localities = **370 m**, with only 2% <100 m. `[DATA]` | "Beat the geocoder" is dead. The winnable target — and the one the official PS3 title actually names — is **learning from field visits**: median error **385 m → 29 m** on visits that met someone. `[DATA]` |
| **5** | The dataset **plants the failure modes** the architecture must survive: a leakage trap that doubles AUC (0.93 vs 0.67), a many-to-many join that silently inflates 51,105 attempts to 52,367, one collector supplying 162 of 172 duplicated photos, and negative visit outcomes that are *closer* to the pin than successful ones. `[DATA]` | Each becomes an explicit, testable component: point-in-time features, the ACP key, tripwire monitoring, integrity weights. |

---

## 1. What arrived — inventory and key integrity

`[DATA]` All 20 CSVs downloaded, read, and profiled. Row counts and key status:

| File | Rows | Cols | First key | Unique? | Note |
|---|---:|---:|---|---|---|
| `data/raw/accounts.csv` | 2,400 | 20 | `account_id` | ✅ | 6 lenders, 6 portfolios, 3 towns, buckets 1-30…X |
| `data/raw/splits.csv` | 2,400 | 2 | `account_id` | ✅ | train 1,680 / validation 360 / test 360 |
| `data/raw/lenders.csv` | 6 | 4 | `lender_id` | ✅ | |
| `data/raw/agents.csv` | 30 | 6 | `agent_id` | ✅ | 20 tele, 9 field, 1 voice bot |
| `data/raw/dial_attempts.csv` | 51,105 | 16 | `attempt_id` | ✅ | 2026-04-01 → 2026-06-29 |
| `data/raw/payments.csv` | 2,162 | 5 | `payment_id` | ✅ | |
| `data/raw/addresses.csv` | 3,117 | 7 | `address_id` | ✅ | 2,400 accounts; residence 2,427 / office 464 / permanent_native 226 |
| `data/raw/field_visits.csv` | 5,578 | 15 | `visit_id` | ✅ | 1,477 distinct addresses |
| `data/raw/phones.csv` | 5,719 | 7 | `phone_id` | ❌ | **5,618 unique phone_ids; 74 repeat across accounts** |
| `data/raw/skip_traces.csv` | 766 | 7 | `trace_id` | ✅ | **one** trigger rule value |
| `data/raw/verified_contact_points.csv` | 250 | 4 | `phone_id` | ✅ | all labelled 2026-07-02 |
| `../PS3_SUTRA/data/raw/towns.csv` | 3 | 4 | `town_id` | ✅ | T1/T2/T3, radius 4.2 / 3.8 / 4.8 km |
| `../PS3_SUTRA/data/raw/localities.csv` | 36 | 6 | `locality_id` | ✅ | 12 per town; 12 pincodes shared by >1 locality |
| `../PS3_SUTRA/data/raw/landmarks_poi.csv` | 240 | 6 | `poi_id` | ✅ | 14 types; **14 of 14 distinct names repeat across towns** |
| `../PS3_SUTRA/data/raw/baseline_geocodes.csv` | 2,880 | 4 | `address_id` | ✅ | 237 addresses (7.6%) have **no** geocode |
| `../PS3_SUTRA/data/raw/visit_gps_points.csv` | 160,406 | 6 | — | — | 26 points/visit median, p90 57 |
| `../PS3_SUTRA/data/raw/surveyed_addresses.csv` | 100 | 3 | `address_id` | ✅ | **the only surveyed ground truth in the package** |
| `ps1/*` (4 files) | 3,696 / 39,194 / 8,466 / 200 | — | — | — | out of scope for PS2/PS3 |

**Geometry.** Coordinates are a local metric plane in **metres from a town origin** (max \|x\| ≈ 7,900), not lat/lng. Distances are directly computable — and also mean there are **no real PIN polygons, no administrative boundaries, and no lat/lng to hand to a map SDK**. `[GAP]` for R5.2 and R12.2.

**The join key is not what it looks like.** `[DATA→READ]` `phone_id` is **not** unique in `phones.csv`; the true contact-point key is the pair **`(account_id, phone_id)`** (5,719 rows, 5,719 unique). A naive `dial_attempts × phones` join inflates 51,105 rows to 52,367 and every rate computed afterwards is quietly wrong. In this review, all PS2 rates use the ACP key. This is R7.4 and R4.6 arriving as a concrete defect rather than a principle.

---

## 2. The official framing vs our research framing

The dataset README names PS2 and PS3 in one line each. That wording is the strongest evidence in the whole package about what CreditNirvana will actually score:

| | Official name (from the dataset README) | Our research framing (requirement files) | Reconciliation |
|---|---|---|---|
| **PS2** | *Right-Party Contact Prediction and Skip-Trace Prioritisation* | "Which action a platform is **permitted** to take, and which is **worth** taking, on a contact point" | Both centre on the same two objects: a **point-level right-party signal** and a **paid-information decision**. Our framing adds the permission layer; the PS title adds the explicit money question. The data supports the first directly and the second only as a rule with parameters (§5). |
| **PS3** | *Address Geocoder That Learns from Field Visits* | "Runtime geocode + top-k candidate set + honest uncertainty + purpose classification + a visit-evidence loop" | The PS title **is** the loop. Our earlier "do not build a geocoder" verdict survives only in its original form: do not build a *coordinate producer* — build the **learner**. §4 shows the learner is where 100% of the winnable gain lives. |

**This resolves the one open scope tension in the package.** The PS3 architecture was always going to be tested against "did you build a geocoder?". The answer is now evidence-based: a from-scratch coordinate producer is **provably not competitive** on this data (376 m vs 379 m, oracle 370 m), while the visit-learning loop is **provably effective** (385 m → 29 m). Build the loop; consume a vendor for the cold start; say exactly that out loud.

---

## 3. PS2 — what the data actually supports

### 3.1 The funnel and the target vocabulary

`[DATA]` 51,105 attempts → 13,303 answered (**26.0%**) → **8,400 RPC (16.4%)**; RPC|answered = **63.0%**. 7,778 attempts (15.2%) hit a dead network response and produced **zero** RPCs.

The disposition vocabulary has **16 values**, and 7 of them are right-party outcomes:

```
no_answer 24591 | call_rejected 5409 | not_reachable 4354 | third_party_contact 3537 | switched_off 3336
rpc_ptp 2937 | rpc_hung_up 2229 | rpc_call_back 1674 | wrong_number 1192 | rpc_refused 1049
rpc_hardship 237 | third_party_ptp 154 | rpc_dispute 139 | rpc_claims_paid 135 | invalid_number 88 | language_barrier 44
```

`[DATA→READ]` This is a ready-made **multi-class label** for R4.1, and it is richer than the four macro-classes we specified: it separates *why* the right party engaged (PTP vs hung-up vs callback vs refused vs hardship vs dispute vs claims-paid) and it separates two third-party states (`third_party_contact`, `third_party_ptp` — a third party who *promises* is a distinct and dangerous object). R4.1's "one model" requirement is satisfiable **without** inventing a taxonomy; the taxonomy is in the data.

### 3.2 The logged propensity — present, but barely usable

`[DATA]` `selection_propensity` exists on every attempt. But: rule-based rows are degenerate at **exactly 1.0** for all 48,339 attempts, and the randomised arm covers **123 of 2,400 accounts (5.1%)** / 2,766 attempts. Real propensities (0.25, 0.333, 0.5, 0.75, 1.0) appear only inside that arm.

`[DATA→READ]` R1.3 (log the incumbent policy's metadata) is **satisfied in form** and **near-useless in content**: a propensity of 1.0 for 94.6% of rows carries no information. R4.3's "propensity weighting where the attempt log permits it, with clipping and effective-sample-size monitoring" becomes: *it does not permit it; report the ESS and fall back to full-population features.* R10.2 (log the propensity) becomes a **live engineering requirement on the client**, not something to be mined from this file.

### 3.3 The arm comparison — the incumbent is not a straw man

`[DATA]` Confounded contrast (the arms differ by 1.1 pp on bucket mix, 3.4 pp on outstanding, 8.4 pp on lender mix):

| arm | attempts | answer | RPC | third-party contact |
|---|---:|---:|---:|---:|
| `random_contact_point` | 2,766 | 0.295 | **0.134** | **0.121** |
| `rule_based` | 48,339 | 0.258 | **0.166** | **0.066** |

`[DATA→READ]` Two conclusions, both uncomfortable and both useful:

1. Randomising *which point to call* is **worse** than the incumbent on RPC and nearly doubles the third-party-contact rate. The incumbent already encodes real knowledge (call the self/priority-0 point first). Any model in the demo must be benchmarked against **the incumbent's realised behaviour** — and the headline claim must be about *re-ranking within a fixed call budget*, not about beating randomness.
2. The random arm's third-party rate confirms the design requirement R2.4/R6.2: **an unconstrained RPC-maximising policy increases wrong-party contact**. In this data that is the single most dangerous optimisation target, and it is exactly the one PS2's name invites.

### 3.4 What is actually predictable (and what is not)

`[DATA]` Honest, pre-dial-only model (no `network_response`, `ring_duration_s`, `talk_duration_s`, `hangup_by`, `disposition`), trained on the supplied split:

| model | train AUC | val AUC | test AUC | base rate |
|---|---:|---:|---:|---:|
| logistic regression | 0.614 | 0.602 | **0.604** | 0.173 |
| gradient boosting | 0.762 | 0.648 | **0.670** | 0.173 |

`[DATA]` **The leakage trap:** adding post-dial fields (`talk_duration_s`, `ring_duration_s`) lifts test AUC to **0.933**. That number is worthless — talk duration *is* the outcome — and a 48-hour build that grabs "all numeric columns" will produce exactly it. This is the strongest single argument for R8.2 (point-in-time features) in the whole package.

`[DATA]` Permutation importance on the honest model:

| feature | ΔAUC |
|---|---:|
| `prior_rpc` (this point produced a right-party contact before) | **0.0894** |
| `relation_recorded_self` | 0.0275 |
| `hr` (hour of day) | 0.0274 |
| `source_bureau` | 0.0084 |
| `seq` (attempt number) | 0.0078 |
| `prior_tp` | 0.0052 |
| everything else | ≤0.003 |

`[DATA→READ]` **Contactability memory dominates.** Account financials — DPD, outstanding, EMI, ability-to-pay, bureau band — contribute almost nothing on top of it. SANKET's point-level state table is therefore not bookkeeping; it is the model. It also explains why the identity model in §3.5 reaches AUC 0.899 from provenance + behaviour alone.

### 3.5 The identity labels — the most valuable file for PS2

`[DATA]` `verified_contact_points.csv`: 250 points, verified **2026-07-02** — three days *after* the last dial attempt, so every feature derived from call history strictly predates the label. Composition: borrower 127, third-party 74, not_borrower 27, switched_off 19, invalid 3. Only **183 of 250** have any call history.

`[DATA]` Behavioural read-outs (this is R1.4's "separate a human answered from the right human answered", made concrete):

| evidence on the point | n | P(borrower) | P(third party) | P(not borrower) |
|---|---:|---:|---:|---:|
| ever produced an RPC | 106 | **0.78** | 0.14 | 0.03 |
| ever answered | 145 | 0.61 | 0.26 | 0.10 |
| ever third-party contact | 53 | 0.26 | **0.64** | 0.08 |
| never answered | 105 | 0.37 | 0.35 | 0.12 |
| ≥10 attempts, 0 RPC | 16 | 0.25 | 0.38 | 0.12 |

`[DATA]` By recorded provenance (n is small — directional only):

| source | n | P(borrower) | P(third party) |
|---|---:|---:|---:|
| `skip_trace` | 12 | **1.00** | 0.00 |
| `kyc_origination` | 97 | 0.73 | 0.07 |
| `borrower_update` | 36 | 0.67 | 0.03 |
| `bureau` | 33 | 0.30 | 0.18 |
| `reference` | 57 | 0.16 | **0.81** |
| `employer` | 15 | 0.07 | **0.93** |

`[DATA]` A model on provenance + behaviour: **CV AUC 0.899 ± 0.035**; provenance alone **0.813 ± 0.045**; majority class 0.508. `[DATA→READ]` Behaviour adds real signal over provenance and the labels are usable — but on 250 rows with 5-fold CV the ±0.035 is honest uncertainty, not precision.

**The consequence for scope.** The `reference` and `employer` points — 1,272 + 5,896 = 7,168 attempts, **14% of all calls** — are 81–93% *third-party numbers* by verification, yet they have the **highest answer rates in the data** (0.44–0.46 vs 0.23 for self points). This is the trap in its purest form: the points that are easiest to reach are the points you are least allowed to talk to. An "answer-rate optimiser" would push collections straight into R6.2 violations.

### 3.6 The waste floor — and why the obvious version of it is wrong

`[DATA]` Attempts ranked by what was already known about the point *before* the call:

| prior state of the point | attempts | % of calls | RPC/attempt | RPCs captured |
|---|---:|---:|---:|---:|
| first-ever call to this point | 4,035 | 7.9% | 0.155 | 625 (7.4%) |
| already dead ≥1 time | 21,847 | 42.7% | 0.144 | 3,142 (**37.4%**) |
| already dead ≥2 times | 10,263 | 20.1% | 0.107 | 1,095 (13.0%) |
| already dead ≥3 times | 5,876 | 11.5% | **0.067** | 392 (4.7%) |
| already marked `wrong_number` | 4,570 | 8.9% | 0.095 | 436 (5.2%) |

`[DATA→READ]` A blanket "stop calling dead points" rule — the obvious first idea, and the one most hackathon teams will ship — **deletes 37% of all RPCs**. Value collapses only at the **third consecutive** dead outcome (18.0% → 6.7%). This is a precise, data-backed stopping rule, and it is a far better demo artefact than a model with a slightly higher AUC: *"we kill the 11.5% of calls that yield 4.7% of outcomes, and we keep the 42.7% that still yield 37%"*.

### 3.7 Skip-trace: the money question, answered honestly

`[DATA]`

| metric | value |
|---|---|
| traces | 766 over 603 accounts, **one** trigger rule (`15_consecutive_failed_contacts`) |
| results | `new_phone_found` 148 (19.3%) · `new_address_found` 27 (3.5%) · `no_new_info` **591 (77.2%)** |
| spend | ₹79,650 total, ₹104/trace, **₹455 per hit**, **₹61,605 (77%) spent on traces that found nothing** |
| traced points dialled | 1,264 attempts → 261 RPC (20.6% vs 16.4% overall) → **₹305 per RPC generated** |
| hit rate by segment | all segments within 18.9%–28.0% of the 22.8% base rate |
| **predict trace success from pre-trace features** | **CV AUC 0.574** vs majority-class 0.772 `[DATA]` |

`[DATA→READ]` There is no learnable "who will a trace find" signal in this data. But the *decision* is still improvable without any model:

1. The trigger is a **constant** — zero variance, so nothing can be learned from it. "When to trace" must be a **rule with a named cost and a measured base rate**, exactly R5.3's EVSI framing: *buy information when P(new reachable point) × value − ₹104 > 0*, with P estimated from the realised 22.8% and the ₹104 as a parameter.
2. The 77% dead spend is the honest headline and the honest demo: a case where the system says **"do not buy this information"** and can show the ₹61,605 it would not have spent in the observation window.
3. `[DATA]` Traced numbers that *are* found are good — 20.6% RPC, and 12/12 verified borrowers in the labelled set. So traces are not worthless; they are **unprioritised**.

### 3.8 Shared numbers — a risk the data exposes, and a requirement it validates

`[DATA]` 4,339 distinct numbers; **1,106 (25.5%) appear on more than one account**, up to **6 accounts**; 43% of phone rows sit on a shared number; **43.2% of all attempts** go to a shared number. On shared numbers the RPC rate is identical (0.164 vs 0.165) but the **third-party-contact rate is higher (0.080 vs 0.061)**.

`[DATA→READ]` R4.6 (entity resolution over the platform's own records) is now a *measured* exposure: calling a shared number "for account A" can reach a person who is the borrower of account B, and disclosing A's debt to them is a DPDP-relevant breach. The ACP key (§1) plus a shared-number flag is the minimum fix, and it is cheap.

### 3.9 Timing and the "wait" action

`[DATA]` Attempts exist **only** between 08:00 and 18:59 — the dataset is already inside the RBI window, so there is no non-compliant hour to find. `[GAP]` There is no record of pre-visit notice, consent, DNC, hardship, grievance or recording flags anywhere.

`[DATA]` RPC rate by hour: 08:00 **0.210**, 09:00 0.198, 10:00–16:00 0.132–0.148, 17:00 0.171, 18:00 0.198. By attempt sequence: attempts 1–3 0.171, 4–8 0.161, 9–15 0.183, 16–25 0.166, **26–60 0.129**. `[DATA]` **1,994 of 2,368 accounts** have a call-free gap longer than 7 days at some point, so "do not call this week" is a *realised* state, not a hypothetical one.

`[DATA→READ]` R2.2's `wait` action is representable in this dataset and its evidence is available: an account can be shown to have been silent for a week while remaining in bucket. Timing is a first-class feature (hour's permutation importance exceeds every financial variable), which makes retest-timing cohorts (R4.4: **no hazard model in the MVP**) worth revisiting *later*, with a pre-registered test.

### 3.10 Payment attribution

`[DATA]` 2,162 payments; 1,667 of 2,400 accounts have at least one; **1,299 payments (60%) fall within 7 days after an RPC attempt**, median gap 3.3 days. `[GAP]` There is **no campaign, case or contact id** on the payment row, and no amount is linked to a specific action.

`[DATA→READ]` R1.5's defined attribution window is constructible; the incrementality claim is not. R10.4 stands unchanged and is now enforced by the data: payments after contact are a **correlation**, and any demo that says "these calls recovered ₹X" is making an unproven causal claim.

---

## 4. PS3 — what the data actually supports

### 4.1 The baseline to beat, and the ceiling of free data

`[DATA]` The 100 surveyed addresses — the only surveyed ground truth — against the commercial geocoder:

| metric | value |
|---|---|
| mean / median | 533 m / **376 m** |
| p75 / p90 / p95 / max | 539 m / **839 m** / 1,831 m / 4,808 m |
| <100 m / <250 m / <500 m / <1,000 m | **9%** / 35% / 71% / 90% |

`[DATA]` The headline table of this review — error by the **vendor's own precision label**, on the survey and on the full 5,578 visits (met-someone subset, where an agent actually found the person, so the check-in is a credible fix):

| vendor `precision` | survey n | survey median | survey p90 | survey <100 m | visits n | visit median | visit <100 m |
|---|---:|---:|---:|---:|---:|---:|---:|
| `rooftop` | 1 | 25.6 m | 25.6 m | 100% | 41 | 37.7 m | **66%** |
| `street` | 16 | 108.6 m | 166.3 m | 44% | 423 | 134.9 m | 33% |
| `locality` | 73 | 385.9 m | 626.5 m | 1% | 1,650 | 367.4 m | **4%** |
| `pincode` | 10 | 1,375.8 m | 3,820.1 m | 0% | 154 | 1,336.5 m | 1% |

`[DATA→READ]` Three things, all directly usable:

1. **The vendor's `precision` label is a genuine stratum key.** It predicts real error monotonically and consistently across two independent samples (100 surveyed vs ~2,300 met visits). R8.2's "empirical quantile by stratum" no longer needs an invented stratum — this one exists, is free, and is already in the input file.
2. **The survey is representative** (`locality` share 73% vs 71.2% in the book), so the 100-address sample is a legitimate calibration set. That is not a small thing: it means R7.4's "calibrate tiers on held-out visit outcomes" is executable here.
3. The baseline's error profile is **bimodal, not noisy**: it is either street-grade (17% of addresses) or locality-grade (71%). A single "average accuracy" number hides the entire problem.

### 4.2 Can free data beat it? No — and the proof matters more than the answer

`[DATA]` A candidate geocoder built only from the free tables (locality name matched in the address text, PIN consistency, POI keywords), scored over the 12 localities per town:

| approach | matched | median error | <100 m | <250 m | <500 m |
|---|---:|---:|---:|---:|---:|
| commercial baseline | 100 | **376 m** | 9% | 35% | 71% |
| locality centroid from text | 73 | 379 m | 2% | 15% | 60% |
| **oracle** best of all 12 localities in town | 100 | **370 m** | **2%** | 22% | 80% |
| naive POI snap (first same-type landmark in town) | 31 | **4,093 m** | — | — | — |

`[DATA→READ]` The oracle result is decisive: **even perfect candidate selection from free data cannot beat the baseline**, because the locality centroid *is* the resolution limit of the free tables (median 370 m, 2% under 100 m). And the naive POI snap — the obvious "use the landmark database" move — is catastrophically wrong (worse than baseline in 90% of cases) because **all 14 landmark names repeat across all three towns**. R3.4 ("scope landmark matching to locality/PIN to avoid cross-town duplicate names") is not a hygiene requirement; it is the difference between a working component and a 4 km error.

`[DATA]` Also: 237 of 3,117 addresses (7.6%) have **no** geocode at all, and 94% of addresses carry a 6-digit PIN of which only 85% matches a known locality PIN.

### 4.3 Where the winnable gain actually is — learning from field visits

`[DATA]` On the 100 surveyed addresses (49 of them visited; 213 visits):

| outcome | visits | median error: baseline | median error: visit check-in |
|---|---:|---:|---:|
| `met_family` | 30 | 380 m | **16 m** |
| `neighbour_says_shifted` | 19 | 433 m | 20 m |
| `locked_premises` | 45 | 390 m | **20 m** |
| `met_borrower` | 60 | 388 m | 34 m |
| `cash_collected` | 3 | 376 m | 71 m |
| `no_such_person` | 3 | 142 m | 72 m |
| **`address_not_traceable`** | **53** | 542 m | **1,603 m** |

`[DATA]` Among visits that actually met someone: median **385 m → 29 m**, **87% improve**, **82% land under 100 m**. Across *all* visits on surveyed addresses, **61%** would produce a sub-100 m fix.

`[DATA→READ]` This is the PS3 thesis, proven on the data:

- **Positive-outcome visits are excellent evidence** (16–34 m) and they are the learning signal the PS title names.
- **Negative-outcome visits are nearly worthless as location evidence** — `address_not_traceable` visits are recorded a median **1,603 m** from truth, and they are also the visits *closest* to the vendor pin (median 195 m from the geocode, with a **2-minute median dwell**). The agent gave up near the pin. Treating "not traceable" as "the coordinate is wrong" would poison the belief with the agent's impatience. This is R6.2 and R9.3 ("observations are evidence, never labels") arriving as a measured effect: **the sign of the outcome and the dwell time must weight the evidence, not just its presence.**

### 4.4 Evidence quality — dwell, spread, and a planted bad actor

`[DATA]` 160,406 GPS points (median 26 per visit, p90 57); accuracy `accuracy_m` 4–72.8 m, median 9.8 m; 645 visits (11.6%) have a check-in more than 500 m from their own trail median; 5 visits report accuracy >50 m; 1 check-in falls outside the town radius; median start→check-in gap 12.1 min (max 85).

`[DATA]` **172 visits share a duplicated `photo_hash`, and FA009 accounts for 162 of them** — 26.6% of that agent's 610 visits, versus ≤1% for every other agent — with a skewed outcome mix (`locked_premises` 48% vs 22% overall, `met_borrower` 13% vs 20%).

`[DATA→READ]` This is deliberately planted, and it is the best gift in the dataset: it makes R10.2 (weight, never reject) and R10.3 (collector-level anomaly monitoring) **demonstrable**. A pipeline without a per-collector tripwire will absorb 610 observations from one bad source into the belief and never notice. With the tripwire, the demo shows a named collector, a duplicated-photo rate, and the belief widening instead of jumping.

### 4.5 Structure, language and address text

`[DATA]` Three towns with deliberately different address *styles*: **T1 Kaveripura** (Kannada-in-Latin: *"6th Cross, 5th Main, ಚರ್ಚ್ ಹತ್ತಿರ, Kuvempu Layt"*), **T2 Devgarh Nagar** (Hindi/Hinglish: *"#81 gali 10 ganesh mandir ke bagal mein krishna puri"*), **T3 Navanagara East** (metro-English/abbreviated: *"No. 170, A Blk., 3rd Rd., Navanagara East"*). 31% of addresses carry a landmark phrase; median address length 67 characters; 94% carry a PIN.

`[DATA→READ]` The `address_style` field is a genuine and rare asset: it lets the parser be tested on **three real Indian address dialects** in one dataset, which is precisely R2.1/R3.1/R3.3 territory. `[DATA]` Per-town baseline error medians are close (440 / 377 / 339 m), so **town identity is not a useful stratum** — stratum = vendor precision class × evidence type.

---

## 5. Twelve traps in this dataset

| # | Trap | The number | What it breaks | Required response |
|---|---|---|---|---|
| 1 | **Leakage by column grab** | test AUC **0.933** with post-dial fields vs **0.670** without | Any model card; credibility | R8.2 point-in-time features; a test that asserts no post-dial field is an input |
| 2 | **`phone_id` is not unique** | 51,105 → **52,367** rows on a naive join | Every rate downstream | Use the ACP key `(account_id, phone_id)` |
| 3 | **Shared numbers** | 43.2% of attempts; third-party 0.080 vs 0.061 | DPDP exposure, wrong-party contact | Shared-number flag + entity resolution (R4.6) |
| 4 | **Dead-point suppression deletes value** | ≥1 prior dead call = 42.7% of calls but **37.4% of RPCs** | An "obvious" rule that destroys the book | Stop at the **3rd** consecutive dead call, not the 1st |
| 5 | **No learnable trace-success signal** | CV AUC **0.574** vs majority 0.772 | "Skip-trace prioritisation" as ML | Make it an EVSI rule with a measured base rate |
| 6 | **Constant trigger rule** | `15_consecutive_failed_contacts` for all 766 traces | Learning "when to trace" from observed triggers | Model the decision, not the history |
| 7 | **Degenerate propensity** | 1.0 on 94.6% of attempts | Off-policy evaluation | Report ESS; log propensities properly in the client |
| 8 | **Negative outcomes are low-information** | `not_traceable` 195 m from pin, 2-min dwell, 1,603 m from truth | Treating visit outcome as a location label | Sign + dwell weighting (R6.2, R9.3) |
| 9 | **One bad collector** | FA009: 162/172 duplicated photos | Silent belief corruption | R10.3 tripwires, visible in the demo |
| 10 | **Free landmarks repeat across towns** | 14/14 names in all three towns | 4 km errors from naive snapping | R3.4 scoping to locality/PIN |
| 11 | **Cash amount lives in free text** | only **43 of 92** cash visits parseable; ₹1.8 M unparseable otherwise | Recovery measurement | Treat money as a parameter; flag the field gap |
| 12 | **Compliance fields are absent** | no notice, consent, DNC, hardship, grievance, recording, complaint fields anywhere | Cannot *demonstrate* the compliance floor from data | Build it as **versioned config with a refusal log** and state the gap openly |

---

## 6. Requirement-by-requirement: what the data can and cannot support

### 6.1 PS2 (`PS2_ARCHITECTURE_REQUIREMENTS.md`)

| ID | Requirement (short) | Verdict | Evidence / gap |
|---|---|---|---|
| R1.1 | Contact slate per account | ✅ **supported** | `phones.csv` is a slate: 2.38 points/account, `source`, `relation_recorded`, `added_date`, `priority_slot` |
| R1.2 | Point-level call outcomes | ✅ **strong** | 16-value disposition on 51,105 attempts keyed to the point |
| R1.3 | Incumbent policy metadata for propensity | ⚠️ **partial** | column exists; 94.6% degenerate at 1.0 |
| R1.4 | Identity-verified events | ✅ **supported** | 250 labelled points, dated after the dial window |
| R1.5 | Payments with an attribution window | ⚠️ **partial** | 2,162 payments, but no campaign/case id → correlation only |
| R1.6 | Suppression state (hardship/grievance/DNC) | ❌ **GAP** | no such column anywhere; `rpc_hardship` is an *outcome*, not a suppression flag |
| R1.7 | Complaint / conduct events | ❌ **GAP** | nothing |
| R1.8 | Runtime telephony intelligence, not stored | ❌ **GAP** | no lookup fields; must be an interface only |
| R2.1 | Ranked eligible action set with cost and ENV | ⚠️ **partial** | outcomes yes; **no cost column** for a call, an agent hour or a visit |
| R2.2 | Explicit `wait` with its own value | ✅ **supported** | 1,994/2,368 accounts have >7-day call-free gaps |
| R2.3 | Rule code + human sentence per refusal | ⚠️ **buildable, unprovable** | no data can validate it; it is a config artefact |
| R2.4 | No disclosure without identity confidence ≥ threshold | ✅ **supported** | verified labels + behavioural evidence (§3.5) |
| R2.5 | Calibrated probability, not a rank | ⚠️ **partial** | calibratable; segment sizes thin (e.g. 16 points at ≥10 attempts) |
| R2.6 | Information-purchase recommendation with price and value | ❌ **GAP on price** | trace cost ₹60–150 exists; call/visit cost does not |
| R3.1–R3.4 | Rules floor, candidate set before scoring, versioning, closed refusal vocabulary | ❌ **no data support** | None of these are learnable — they are configuration. Demonstrate them on config + refusal logs |
| R4.1 | One multi-class outcome model | ✅ **strong** | the 16-value vocabulary *is* the taxonomy |
| R4.2 | Segmented calibration + ECE | ⚠️ **partial** | 6 lenders × 6 portfolios exists but cells are thin |
| R4.3 | Selection-bias handling / propensity weighting | ⚠️ **weak** | ESS will be tiny; fall back to full-population features |
| R4.4 | No hazard model in the MVP | ✅ **consistent** | sequence RPC is flat (0.171 → 0.129) — timing complexity buys little here |
| R4.5 | No graph/sequence/deep models in MVP | ✅ **consistent** | permutation importance says a 6-feature model captures most of it |
| R4.6 | Entity resolution for cross-account conflicts | ✅ **strong** | 1,106 shared numbers measured |
| R4.7 | PR-AUC, Brier, ECE, precision at budget | ✅ **supported** | splits file provided; test base rate 0.173 |
| R5.1 | ENV ranking with a versioned cost table | ❌ **GAP** | no cost data; parameterise |
| R5.2 | Cost table + incrementality as named parameters with ranges | ❌ **GAP** (and thereby *enforced*) | the data offers no crutch — the UI must show ranges |
| R5.3 | EVSI-style information purchase | ⚠️ **partial** | base rate 22.8% measurable; value of a reachable point is an assumption |
| R5.4 | Capacity constraints | ❌ **GAP** | no shift capacity, no agent-minute data |
| R5.5 | No live exploration | ✅ **consistent** | the one randomised arm is historical and small |
| R6.1–R6.5 | Compliance floor, purpose limitation, no third-party targeting | ❌ **GAP on data, ✅ on design** | This is the *point*: build it as config + refusals and say the data cannot prove it |
| R7.1–R7.4 | Decision record, retention classes, licence limits, point-in-time features | ⚠️ **partial** | R7.4 is now proven necessary (trap 1); retention/licence are documentation |
| R8.1 | Temporal split | ⚠️ **use the supplied split** | the provided split is **by account**, not by time — a random-split leakage risk |
| R8.2–R8.5 | Point-in-time features, label tiers, model card, drift | ✅ **supported** | 3-month window, dated labels, six lenders to measure drift across |
| R9.1–R9.4 | Batch-first, ≤60 min portfolio pass, degrade to rules floor, ≤300 ms per account | ⚠️ **untestable at scale** | 2,400 accounts only; sizing is an `[ASSUMPTION]` |
| R10.1 | Closed outcome vocabulary captured | ✅ **already in the data** | disposition + remark exist |
| R10.2 | Log the propensity of the action taken | ⚠️ **partial** | column exists, values degenerate |
| R10.3 | Shadow-mode policy evaluation | ✅ **supported** | historical log allows offline replay |
| R10.4 | No uplift claim without a controlled comparison | ✅ **enforced by data** | 5.4% confounded arm; the random arm is *worse* |
| R11.1–R11.4 | Decision record with rule/model/config versions; exportable; reason codes | ⚠️ **buildable** | no data, pure engineering |
| R12.x | Three-endpoint API | ⚠️ **buildable** | |
| R13.x | Offline batch, shadow mode | ⚠️ **buildable** | |

### 6.2 PS3 (`PS3_ARCHITECTURE_REQUIREMENTS.md`)

| ID | Requirement (short) | Verdict | Evidence / gap |
|---|---|---|---|
| R1.1 | Raw address strings, all sources, with script markers | ✅ **strong** | 3,117 addresses, 3 dialects, mixed Kannada/Devanagari-in-Latin, 3 record types |
| R1.2 | Account context (PIN, town, product, ticket) | ✅ **supported** | `accounts` + `addresses` + PIN in text (94%) |
| R1.3 | Field observations with accuracy, dwell, outcome, agent | ✅ **strong** | 5,578 visits, 160,406 GPS points, `accuracy_m`, `dwell_s`, `photo_hash` |
| R1.4 | Notice/visit outcomes | ⚠️ **partial** | visit outcomes exist; **no notice record** — the notice gate cannot be demonstrated from data |
| R1.5 | PIN→district reference + landmark base | ⚠️ **synthetic substitute** | 36 localities with centroid+pincode; **no PIN polygon, no district/state** |
| R1.6 | Licence-configured geocoder client | ❌ **GAP** | the dataset ships one **baseline output file**, not a client. Licence behaviour stays a design decision |
| R2.1 | Extract PIN, locality, landmark, house id | ✅ **strong** | and it is non-trivial in exactly the right way (3 dialects, abbreviations, transliteration) |
| R2.2 | Open-weight Indic NER rather than a bespoke model | ⚠️ **testable** | text available; but there is no alternative parser to benchmark against |
| R2.3 | Parsing failures are abstentions | ✅ **testable** | 6% of addresses have no PIN; 69% have no landmark phrase |
| R2.4 | Parser version + spans recorded | ❌ **buildable** | |
| R2.5 | No spell-correction of proper nouns | ✅ **consistent** | "Haanuman Temple", "Layt", "Nr", "Blk." — spelling varies; aliasing must be table-driven |
| R3.1 | Conservative transliteration, keep original | ✅ **strong** | T1 addresses carry both scripts in one string |
| R3.2 | PIN validated, disagreement penalises confidence | ✅ **strong** | 94% have a PIN, only **85%** match a known locality PIN → a real 9-point disagreement rate to handle |
| R3.3 | Landmark alias table from confirmed visits | ⚠️ **partial** | 240 POIs exist; the alias relation (text → POI) must be learned, exactly as planned |
| R3.4 | Scope landmark matching to locality/PIN | ✅ **strongly proven** | 14/14 names repeat across towns; naive snap = 4,093 m median |
| R4.1–R4.5 | Runtime vendor geocode; declared storage; OSM fallback; multi-candidate; spend cap | ❌ **GAP** | no vendor client, no licence metadata, no price. Design-only, and the demo must label the stored coordinates as derived from a **provided baseline file**, not from a live call |
| R5.1 | Top-k candidate set with source labels | ⚠️ **partially demonstrable** | we can build the candidate set from localities + POIs; sources are locality / PIN / landmark / visit |
| R5.2 | PIN/locality polygon candidate on vendor miss | ⚠️ **centroid + radius only** | no polygons; the 7.6% of addresses with no geocode is the real use case |
| R5.3 | Landmark-derived candidate when the phrase resolves locally | ✅ **testable** | 31% of addresses have a landmark phrase |
| R5.4 | No candidates outside the envelope | ✅ **testable** | 1 check-in outside the town radius exists as a test case |
| R6.1 | Inspectable weighted ranker | ✅ **buildable** | and §4.2 shows why a transparent ranker is the right choice here |
| R6.2 | Integrity weights: low trust → less change, wider radius | ✅ **strong** | dwell/outcome/duplicate-photo evidence is all present |
| R6.3 | Disagreement widens the radius, never averages | ✅ **testable** | 645 visits disagree with their own trail by >500 m |
| R6.4 | Learning-to-rank only after the transparent ranker is measured | ✅ **consistent** | oracle ceiling (§4.2) says there is little left to learn from free features |
| R7.1–R7.4 | Confidence tiers, observable evidence, `unknown` first-class, calibrated on held-out visits | ✅ **strong** | the vendor-precision stratum table (§4.1) *is* the calibration |
| R8.1 | Coordinates + radius + tier + evidence count (never a bare point) | ✅ **strong** | and §4.1 shows the radius is where the honest value is |
| R8.2 | Radius = empirical quantile by stratum | ✅ **strong** | the table exists and is reproducible (see the derived CSV) |
| R8.3 | Widen to a parent stratum when thin | ✅ **required** | `pincode` and `rooftop` strata have 10 and 1 survey points |
| R8.4 | Conformal validation without overclaiming coverage | ⚠️ **thin** | n=100 ground truth; coverage claims must be stated as synthetic |
| R8.5 | Document that GPS accuracy is a 68th-percentile radius | ✅ **already true in data** | `accuracy_m` values 4–72.8 m, median 9.8 m |
| R9.1–R9.4 | On-device capture, offline sync, outcome recorded, evidence-not-labels, verify-first tasks | ✅ **strong** | all observation fields present; the "verify-first" task is directly supported by the 47% of addresses never visited |
| R10.1–R10.5 | Mock flag, accuracy, speed plausibility, duplicate detection, degrade-not-accuse, collector anomalies, no spoof-rate claim | ⚠️ **strong except mock/speed** | duplicate-photo and collector anomalies are demonstrable; there is **no mock-location flag** and no inter-point timestamps at speed resolution |
| R11.1–R11.5 | Purpose classification (home/work/other), dwell+time+POI+repeat, refuse notice at work addresses, abstain, versioned | ✅ **strong** | 464 office addresses and 226 out-of-town permanent addresses; `address_type` is the label; dwell and time-of-day are present |
| R12.1–R12.4 | Store records, PostGIS/H3, provenance/licence per coordinate, retention classes | ❌ **buildable** | the *concept* of provenance is testable (baseline vs visit vs landmark); no H3/PIN polygons in the data |
| R13.1–R13.4 | Belief updates, strata recomputation, outcome labels for the gate, **never train on vendor coordinates** | ✅ **strong** | the baseline file is the vendor output — training on it is exactly the trap the requirement forbids, and it is now technically possible to do by accident |
| R14.x | `GET /belief`, `POST /visit-evidence`, radius at decision time, landmark directions as text | ⚠️ **buildable** | |
| R15.x | Nightly district packs, offline capture, stale packs visibly widen the radius | ⚠️ **buildable** | |

---

## 7. Assumption ledger — what the research flagged, and what the data now says

| Research assumption | Status after this review |
|---|---|
| "Visit-level GPS history exists and can feed an Address Evidence Score" | ✅ **CONFIRMED** — 160,406 points, 26/visit median, per-point `accuracy_m` |
| "Point-level call dispositions exist, with agent remarks" | ✅ **CONFIRMED** — 16-value vocabulary, remarks in 3 languages |
| "A commercial geocoder baseline exists to beat" | ✅ **CONFIRMED — and unbeatable on accuracy with free data;** the win is radius honesty + the visit loop |
| "Propensities are logged, enabling off-policy evaluation" | ⚠️ **PARTLY REFUTED** — 94.6% degenerate at 1.0; ESS will be tiny |
| "A randomised holdout exists to measure incrementality" | ❌ **REFUTED in usable form** — 5.4% of accounts, confounded, and the random arm is *worse* than the incumbent |
| "Ticket bands are large enough for recovery to matter" | ✅ **CONFIRMED in range** — outstanding ₹6.3 k–₹21.2 lakh (median ₹1.23 lakh), EMI median ₹4,300; but no recovery-cost data |
| "Payments can be attributed to contact within a window" | ⚠️ **PARTIAL** — 60% of payments follow an RPC within 7 days, but there is no campaign id |
| "Suppression/hardship states are available" | ❌ **REFUTED** — no such field exists; must be config |
| "Identity verification signals exist behind the contact-point table" | ✅ **CONFIRMED** — 250 labelled points, dated after the feature window |
| "Wrong-party-contact cost can be quantified" | ❌ **still `[UNKNOWN]`** — the data gives the *rate* (6.9% of calls; 81–93% of reference/employer points), never the cost |

---

## 8. What the 48-hour MVP is now — concretely

The dataset fixes the acceptance numbers. Every claim below is checkable against `derived_ps2_policy_baselines.csv` and `derived_ps3_radius_calibration.csv`.

### PS2 — the contact-permission gate (build order)

| Step | Component | Input | The number it must beat |
|---|---|---|---|
| 1 | **ACP table** — `(account_id, phone_id)` point state, point-in-time | `phones`, `dial_attempts` | the naive join (52,367) vs correct (51,105) |
| 2 | **Waste floor** — refuse the 3rd+ consecutive dead call; refuse `wrong_number` points | attempt history | RPC/call 0.1762 → **0.1872** on the test split; −12.5% calls |
| 3 | **Identity gate** — P(borrower) per point, with a refusal when below threshold | `verified_contact_points` + behaviour | CV AUC **0.899** vs 0.813 provenance-only |
| 4 | **Outcome model** — one multi-class model, isotonic-calibrated, point-in-time features | `accounts` + ACP state | test AUC **0.670**, PR-AUC and Brier on the supplied test split; **must not exceed ~0.75**, or a post-dial field has leaked |
| 5 | **EV gate with `wait`** — cost table as named ranges; `wait` has its own value | parameters | incumbent first-3-calls RPC/call **0.157** |
| 6 | **Information decision** — EVSI rule for traces at ₹104, base rate 22.8% | `skip_traces` | "refuse the trace" must be a *visible output*; the observation-window saving is ₹61,605 |
| 7 | **Decision record + refusal list** — rule codes, config version, model version | — | shown, not claimed |

**The demo's single line:** *"We refused X actions, and here are the 3rd consecutive dead calls we stopped making that still would have produced 37% of outcomes if we had banned them all."*

### PS3 — the belief engine and the visit loop (build order)

| Step | Component | Input | The number it must beat |
|---|---|---|---|
| 1 | **Candidate set** — top-k with source labels (vendor / locality / PIN / landmark / visit) | `baseline_geocodes`, `localities`, `landmarks_poi` | baseline median **376 m**; never worse than the naive snap's 4,093 m |
| 2 | **Radius calibration table** — per vendor precision × evidence stratum, empirical p90 | 5,578 visits + 100 surveyed | `locality` → ~650 m p90; `street` → ~296 m; `rooftop` → ~268 m |
| 3 | **Integrity weighting** — dwell, outcome sign, trail disagreement, photo duplication, collector tripwire | `visit_gps_points`, `field_visits` | FA009 flagged at 26.6% duplicate rate vs ≤1% for peers; the 645 trail-disagreement visits widen rather than move the belief |
| 4 | **Visit-evidence update** — confirmed-visit fixes | `field_visits` | met-someone visits: **385 m → 29 m**, 82% under 100 m |
| 5 | **Purpose classifier** — home / work / other, abstaining | dwell + hour + `address_type` + POI | office addresses (464) and out-of-town (226) must be refused notice eligibility |
| 6 | **The honest output** — `{coordinate, radius, tier, evidence_count, provenance, purpose}` | — | a bare point is a failed output (R8.1) |

**The demo's single line:** *"We published 376 m as a truth and it is a p90 of 839 m. Here is the same address, with a radius that matches what we actually measured, and the visit that took it from 385 m to 29 m."*

### What stays out of the MVP

Survival/hazard retest timing, bandits, uplift, graph targeting, learning-to-rank, microservices, a purpose taxonomy beyond 3 classes, and **any** accuracy or ROI figure presented as real. The data has now removed the temptation: several of these would have been defensible-sounding and are now demonstrably unsupported.

---

## 9. What the data still cannot answer — questions for CreditNirvana

These are added to `CN_QUESTIONS.md`. Each is a question whose answer changes a design decision:

1. **Cost of a call-attempt minute, an agent hour, and a field visit** (travel + fuel + wage), and the **recovery value** used internally. Without these the EV gate (R5.1) is a parameter with a range, not a number.
2. **Is there a pre-visit notice record** in production, and is it machine-readable? The notice-before-visit precondition (RBI, effective 1 Jan 2027) is currently undemonstrable.
3. **Where do suppression states live** (hardship, grievance, bereavement, DNC, legal hold)? They are absent from the dataset, and they are hard barriers, not features.
4. **Is there a campaign/case id** linking a payment to the contact that caused it? Today, 60% of payments follow an RPC within 7 days and none can be attributed.
5. **How is wrong-party contact counted in production** — disposition only, or a QA sample? In this data 6.9% of calls are third-party contacts, and 81–93% of reference/employer points verify as third-party numbers.
6. **What is the real monthly call volume and the real field-force size**? The dataset is 2,400 accounts / 30 agents; no capacity constraints can be modelled from it.
7. **Do you have PIN-level polygons or a licensed administrative boundary source?** This dataset has centroids only.
8. **Which geocoder is actually in production, and under what licence terms** (caching window, storage, display)? The dataset ships a static baseline file with no vendor identity.
9. **Is there a mock-location / rooted-device flag** on the field app, and per-point timestamps at speed resolution? Spoof detection (R10.1) is currently design-only.
10. **Was the 15-consecutive-failures trace rule the real production trigger?** It has zero variance here, so "when to trace" cannot be learned from history.

---

## 10. Verdict

**PS2 — proceed, with the target moved from "prediction" to "permission plus refusal".** The data supports a point-level identity gate (AUC 0.899 on 250 labels), a deterministic waste floor with a measured 11.5%-of-calls / 4.7%-of-outcomes trade, and one multi-class outcome model whose honest ceiling on pre-dial features is AUC ≈ 0.67. It **does not** support skip-trace success prediction (AUC 0.574), propensity-weighted learning (degenerate propensity), or any uplift claim (a 5.4% confounded arm, and the random arm is worse than the incumbent).

**PS3 — proceed, with the product restated as the learning loop, not the coordinate.** The commercial baseline sits at the resolution ceiling of the free data (376 m vs an oracle-best 370 m from candidates; naive landmark snapping is 4 km wrong), so a from-scratch geocoder is provably not the deliverable. The deliverable is the loop the PS title names — **field visits move an address from 385 m to 29 m** — plus the two things the vendor does not give: an **empirically calibrated radius per stratum** (the vendor's own `precision` label predicts its real error: 38 m / 135 m / 367 m / 1,336 m by class) and an **integrity-weighted belief** that survives a collector submitting 162 duplicated photos.

**Both:** the dataset is unusually well designed as a trap course. It contains the leakage, the join ambiguity, the poisoned labels, the bad actor, the constant trigger and the unresolvable cost question — which means a submission built on it can show not only what it computes, but **what it refuses to claim**. That is the same posture the requirement files already took, and it is now backed by numbers rather than principle.

**Nothing in the architecture files is invalidated. Three things are re-weighted:** PS2 drops the trace-success model and promotes the waste floor and the identity gate; PS3 promotes the visit-learning loop and the radius calibration to the centre of the build; and the compliance layer stays exactly where it was — as configuration and refusal logs, because the data cannot prove it and no honest submission should pretend otherwise.

---

## 11. How to reproduce every number

```bash
# 1. Fetch the dataset (gdown, ~21 MB, public folder)
gdown --folder "https://drive.google.com/drive/folders/18iqIR8TjXDqf9-hgEY34uJr_DraIl_3P" -O /home/user/dataset

# 2. Every figure in this report   (sections: q = inventory, p2 = PS2, p3 = PS3, eco = economics)
python3 dataset_audit.py             # ~2 min

# 3. Regenerate the two derived tables shipped with this review
python3 CreditNirvana_Submission/06_Dataset_Review/build_derived_tables.py
```

Shipped alongside this review:

- `dataset_audit.py` — the full audit, section by section.
- `derived_ps3_radius_calibration.csv` — **the radius table the PS3 belief engine must output**, per stratum, from two independent samples.
- `derived_ps2_policy_baselines.csv` — **the policies the PS2 demo must beat**, on the supplied test split.
- `build_derived_tables.py` — regenerates both CSVs from the raw data.

**All figures are computed from invented data. Mechanism only, never magnitude.**
