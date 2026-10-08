# SUTRA — DATA AUDIT (official PS3 dataset)

**Scope.** Every table the PS3 problem can touch, profiled field by field, *before* any cleaning. Produced by
`tools/ps3_audit.py`; the raw run is saved verbatim at `data/derived/ps3_audit_full.txt` (466 lines) and the two machine
readable profiles at `data/derived/ps3_table_profile.csv` and `data/derived/ps3_column_profile.csv`.

**Everything here is SYNTHETIC.** The dataset README says so in its own words. This audit can show that a mechanism
exists and that a failure mode is real; it can never be quoted as accuracy, coverage, or market fact. Where a number
would be tempting to quote, the audit says so explicitly.

---

## 0. The headline findings (read these before the tables)

1. **The only true coordinates in the package are 100 surveyed addresses.** 3,117 addresses exist; 100 have ground truth
   (3.2%). Every accuracy claim in this project is measured on that sample, and the sample is 38/33/29 across the three
   towns — small enough that per-stratum conclusions need the minimum-n guard in `PS3_UNCERTAINTY_ARCHITECTURE.md`.
2. **237 addresses are `town_id = OUT`** — outside any modelled town — and **every one of them is missing a vendor
   geocode** (0% geocoded vs 100% for the rest). "Cannot be placed" is a state that already exists in the data.
3. **Field evidence is not a random sample of addresses.** Visit rate rises monotonically with delinquency:
   19.9% of DPD 0–30 accounts visited versus 84.8% of 180+ accounts. Any accuracy number computed on visited addresses
   is a *conditional* number, and the loop must be built and evaluated accordingly (§7).
4. **The planted integrity anomaly is duplicate photos, not GPS spoofing.** One field agent has 156 reused photo hashes
   in 610 visits (25.6%); every other agent is ≤0.3%. GPS trails in this dataset are *clean* — no teleports, no
   off-trail check-ins (median check-in-to-trail distance 7.6 m, max 90.8 m). The integrity layer must therefore be
   *designed* for real-world spoofing and *tested* against injected faults, because the dataset cannot supply them.
5. **Failure visits converge on the vendor pin; success visits converge on the truth.** On the surveyed 100:
   met-someone check-ins sit a median 29.3 m from truth and 396.9 m from the pin (closer to the pin only **3.2%** of the
   time); `address_not_traceable` check-ins sit 1,603.2 m from truth and 253.4 m from the pin — closer to the pin **84.9%**
   of the time, at a 1.3-minute dwell. So "the agent's GPS agrees with our pin" is a **failure** signal, not a
   confirmation, and a single `address_not_traceable` can never relocate a coordinate by itself (accumulated independent negatives only demote/widen/mark/re-verify — F2.1/D36). Full table:
   `data/derived/ps3_evidence_diagnostics.csv` (`tools/evidence_diagnostics.py`).
6. **A licence-clean retriever already matches the commercial geocoder on coarse records.** Matching a locality name
   *from the address text* against the gazetteer covers 61.1% of addresses and lands at a **median 348 m** on the
   surveyed subset, versus the vendor's **376 m** — at zero marginal cost and with no licence clock. It is not a
   replacement (39% have no match at all, and it cannot resolve street level), but it is a real baseline.
7. **Landmarks cannot be snapped to.** 240 landmarks carry only 14 distinct names and 198 duplicate `(town, name)`
   pairs; name→point is not a function. Prior measurement: naive snapping = 4,093 m median.

---

## 1. Method

`tools/ps3_audit.py` runs eleven sections (`q keys coord txt geo visits gps agents acc leak xtra`) over
`data/official_ps3/`, read-only. For every table it reports shape, key uniqueness, full-row duplicates, null cells and
per-column: dtype, null %, distinct count, min/max/mean (numeric) or top-3 values (categorical). Then it performs
targeted checks: FK reachability in both directions, coordinate ranges and decimal precision, pin-pile sizes, town
containment of check-ins, address-text shape, pincode/locality consistency, stratum-conditional error, outcome-conditional
dwell and distance, duplicate evidence, trail geometry and implied speeds, collector behaviour, and the selection-bias
table. Reproduce with `bash tools/reproduce.sh` (≈15 s).

---

## 2. Table-by-table profile

> **Scope of record (2026-10-07, official-scope re-audit):** DATASET A is **12 tables · 177,196 rows** —
> the 11 profiled below plus the officially assigned shared table `lenders` (§2.12). The assigned shared tables
> `dial_attempts` and `payments` belong to other problem statements and are excluded; this task has no financial
> outcome variable. Nothing in §2.1–§2.11 changes.

### 2.1 `towns.csv` — 3 rows × 4 cols
`town_id` PK unique. Fields: `town_name`, `address_style` (`karnataka` / `hindi` / `metro`), `approx_radius_m`
(4,200 / 3,800 / 4,800). **Usable at inference: yes.** Verdict: coarse prior only — and note `approval_radius_m` is an
*author's* parameter, not a measurement; it must never be published as an error bound.

### 2.2 `localities.csv` — 36 rows × 6 cols
12 localities per town, 4 pincodes per town, **no pincode shared across towns**. `locality_name` has **35 distinct
values for 36 rows** — "Nehru Colony" exists in both T1 and T2. So `locality_name` alone is ambiguous, while
`(town_id, locality_name)` is unique: locality identity must be keyed by town. Centroids have 1-decimal precision
(36 distinct x, 36 distinct y) — i.e. rounded, which is consistent with their role as coarse artefacts.

### 2.3 `landmarks_poi.csv` — 240 rows × 6 cols
14 landmark types (ration shop 26, bus stop 22, govt school 22, masjid 21, Hanuman temple 21, medical store 19,
Ganesha temple 18, water tank 18, milk dairy 16, community hall 14, park 13, church 12, post office 10, petrol bunk 8).
**226 duplicate names; 14 distinct names total; 198 duplicate `(town_id, name)` pairs.** Coordinates look sane
(x ∈ [−4,072, 3,788]) and are near-unique (238 distinct x for 240 rows). 25.2% of address texts mention a landmark of
their own town — so landmarks are *useful as a language prior* and *useless as a coordinate target*.

### 2.4 `addresses.csv` — 3,117 rows × 7 cols; PK unique; zero nulls
| Dimension | Measurement |
|---|---|
| Text length | median 67 chars (max 113); 11.9 tokens median |
| Digits | median 9 per address; **9 addresses (0.3%) contain no digit at all** |
| House number detectable | 76.8% match a house-number-like token |
| Comma-separated | 75.1%; **24.9% are a single unpunctuated blob** |
| Contains a 6-digit number | 93.3% — **and only 91.1% of those match a known pincode** |
| Non-ASCII (Devanagari/Kannada) | 262 rows (8.4%) — e.g. `6th Cross, 5th Main, ಚರ್ಚ್ ಹತ್ತಿರ, Kuvempu Layt, Kaveripura - 960102` |
| Exact duplicate text | 3 rows; 9 after aggressive normalisation; **0 across different accounts** |
| `town_id` | T3 986 · T2 952 · T1 942 · **OUT 237** (not present in `towns.csv`) |
| `address_type` | residence 2,427 · office 464 · permanent_native 226 |
| `source` | kyc_origination 3,090 · skip_trace 27 |
| `added_date` | 2026-04-01 → 2026-06-29 (90-day window) |

Verdict: text is *semi-structured and highly regular* (synthetic), with three real traps worth designing for:
`OUT` addresses, missing pincodes that do not correspond to any locality, and a quarter of records with no punctuation.

### 2.5 `baseline_geocodes.csv` — 2,880 rows × 4 cols
| Stratum | Rows | Implication |
|---|---|---|
| `locality` | 2,052 (71%) | the modal case is a coarse pin |
| `street` | 504 (17.5%) | the only stratum where street-level work is possible |
| `pincode` | 274 (9.5%) | the stratum with the largest error and the fewest survey rows |
| `rooftop` | 50 (1.7%) | too rare to calibrate (1 survey row) |

**237 addresses have no geocode at all** — exactly the `OUT` set. Coordinates are rounded to 1 decimal (median decimals
= 1), 2,806 distinct x for 2,880 rows, and **no pin piles** (largest pile = 1 address): this synthetic vendor never
degrades by collapsing many addresses onto one point, which real vendors do — so our design must not *rely* on piles as
a degradation signal.

### 2.6 `surveyed_addresses.csv` — 100 rows × 3 cols (the only ground truth)
T1 33 · T2 29 · T3 38; all 100 have a vendor geocode (so the surveyed sample excludes the hard `OUT` case entirely —
another reason it is an optimistic sample). Error vs the vendor geocode:

| Strata | n | median | p75 | p90 | <100 m |
|---|---|---|---|---|---|
| all | 100 | **376.4 m** | 539.4 m | 839.2 m | **9%** |
| `rooftop` | 1 | 25.6 m | — | — | 100% |
| `street` | 16 | 108.6 m | 129.6 m | 166.3 m | 43.8% |
| `locality` | 73 | 385.9 m | 504.5 m | 626.5 m | 1.4% |
| `pincode` | 10 | **1,375.8 m** | 2,658.5 m | 3,820.1 m | 0% |

Hit rates overall: <50 m 5% · <100 m 9% · <250 m 35% · <500 m 71%. **Ground-truth quality verdict:** these are the only
coordinates in the package that can serve as labels, they are 100 rows, and they over-represent geocodable addresses.
Every claim in this package is calibrated to that limitation.

### 2.7 `field_visits.csv` — 5,578 rows × 15 cols; PK unique; 89.2% nulls are in `ptp_id` alone
| Outcome | n | % | median dwell | median dist. to surveyed truth (subset) |
|---|---|---|---|---|
| met_borrower | 1,114 | 20.0 | 14.8 min | 34.3 m (n=60) |
| met_family | 1,062 | 19.0 | 6.6 min | 15.9 m (n=30) |
| cash_collected | 92 | 1.6 | 14.5 min | 71.2 m (n=3) |
| locked_premises | 1,249 | 22.4 | 2.5 min | 20.2 m (n=45) |
| neighbour_says_shifted | 455 | 8.2 | 4.3 min | 20.1 m (n=19) |
| no_such_person | 206 | 3.7 | 3.2 min | 72.3 m (n=3) |
| address_not_traceable | 1,400 | **25.1** | **1.3 min** | **1,603.2 m (n=53)** |

Met-someone 29 m vs negative 493 m on the same 100-address sample: **the outcome field is informative about the *place*
in one direction only, and catastrophic in the other.** 1,477 addresses ever visited (47.4% of the book); 900 (28.9%)
have at least one met-someone visit — that is the entire positive learning signal. Median 3 visits per visited address
(p90 8, max 9). Travel (start→check-in) median 12.1 min, never negative. Check-ins cluster 10:00–14:00.

### 2.7b What a check-in is actually evidence *of* — the decisive diagnostic
`tools/evidence_diagnostics.py` → `data/derived/ps3_evidence_diagnostics.csv` (surveyed subset, where truth exists):

| Outcome | n | med. to truth | med. to vendor pin | closer to pin | med. dwell | reading |
|---|---|---|---|---|---|---|
| met_borrower | 60 | 34.3 m | 412.0 m | 3.3% | 16.6 min | converges on **truth** |
| met_family | 30 | 15.9 m | 381.2 m | 3.3% | 5.7 min | converges on **truth** |
| cash_collected | 3 | 71.2 m | 420.2 m | 0.0% | 14.7 min | converges on **truth** |
| locked_premises | 45 | 20.2 m | 400.8 m | 11.1% | 2.8 min | converges on **truth** |
| neighbour_says_shifted | 19 | 20.1 m | 427.5 m | 10.5% | 4.5 min | converges on **truth** |
| no_such_person | 3 | 72.3 m | 140.4 m | 0.0% | 1.8 min | converges on **truth** |
| **address_not_traceable** | **53** | **1,603.2 m** | **253.4 m** | **84.9%** | **1.3 min** | converges on the **PIN** |
| ALL met-someone | 93 | 29.3 m | 396.9 m | 3.2% | 9.7 min | accuracy signal |
| ALL address_not_traceable | 53 | 1,603.2 m | 253.4 m | 84.9% | 1.3 min | **record/agent signal** |

Three design consequences, all binding:
1. **Positive outcomes are location evidence; negative outcomes are not.** The two dimensions must never be summed into
   one score, and `address_not_traceable` must not be allowed to move a coordinate (canonical schema §3).
2. **"Agreement with the pin" is not corroboration.** Any feature of the form *distance(check-in, pin)* is contaminated:
   a failed visit *reduces* it. SUTRA therefore forbids pin-agreement features and instead conditions on
   *distance to the pin at the moment the agent deviates from the trail*, plus dwell and outcome.
3. **A failure is evidence about the record, not about the place** — it raises the prior probability that the record is
   wrong/moved, which raises the value of re-verification, and (only after independent corroboration elsewhere) can
   *demote* the old position. Demotion is a slow-loop decision with a rule, never a point move.

### 2.7c Candidate arms measured on the same 100 (from `tools/build_candidates.py`)

| Arm (all licence-clean except the vendor pin) | coverage over 3,117 | n on survey | median | <100 m | <500 m |
|---|---|---|---|---|---|
| vendor pin (baseline) | 92.4% | 100 | 376.4 m | 9.0% | 71.0% |
| matched-locality centroid | 65.9% | 75 | 356.7 m | 2.7% | 84.0% |
| town centroid | 92.4% | 100 | 2,740.0 m | 0.0% | 1.0% |
| **oracle over the candidate set** | — | 100 | **306.2 m** | **11.0%** | **79.0%** |
| naive priority top-1 (vendor > locality > town) | — | 100 | 376.4 m | 9.0% | 71.0% |

Read this honestly: **candidate generation from these three arms alone can only buy 376 → 306 m** (a ~19% relative
improvement) because the arms are coarse and correlated — and the naive rule is *identical* to the official frozen baseline geocode arm because
the vendor pin wins the priority list every time. That is the empirical case for (a) semantic addressing memory, (b) real
retrieval from the official anchors (landmarks, address book) we do have, and (c) field evidence as the arm that actually
changes the answer — external gazetteers are **rejected** by the final data policy and were never the missing piece. It is also the
argument against pretending that a ranker over three coarse arms is "the model".

### 2.8 `visit_gps_points.csv` — 160,406 rows × 6 cols (100% of visits instrumented)
Median 26 points/visit (p90 57); median accuracy 10.0 m (p90 21 m) — a **68% radial confidence**, so the honest "where
was the agent, really" radius is roughly the accuracy value, not a hard bound. 68 visits have <5 points.
`seq` is time-monotone in all 5,578 visits. Implied speeds between consecutive points: p50 4.84 km/h, p99 23.06 km/h,
**max 32.2 km/h** — no teleports whatsoever. Zero-distance repeated points: 0.1%. Half the visits have the check-in
within 7.6 m of its own trail and no visit is >500 m off trail. **34 points sit on the x=0 or y=0 axis** (0.021%) —
sensor artefacts to filter, not learn from. *Design consequence:* the dataset cannot validate a spoof detector, so the
integrity layer ships with rule-based weights, an explicit "insufficient evidence" class, and a fault-injection test bed.

### 2.9 `agents.csv` — 30 rows × 6 cols
20 tele, 9 field, 1 voice bot; 4 language teams; 3 towns (3 agents each); `town_id` null for 21 (all non-field);
`tenure_months` 1–64 (one null); shifts day/all. **Verdict:** kept because the integrity layer needs *behavioural
baselines per collector*, not because collection capacity is a modelling input.

### 2.10 `accounts.csv` — 2,400 rows × 20 cols
6 lenders; portfolios: pl_salaried 682, two_wheeler 502, mfi_jlg 358, credit_card 319, consumer_durable 296, msme 243.
`dpd_start` 0–720 (median 41, p90 171); `outstanding` median ₹1.23 L, p90 ₹5.11 L; `emi_amount` median ₹4,300.
Nulls concentrated in `salary_credit_day` (68.3%) and `ability_to_pay_estimate` (30.3%). **No account field is a
feature of the location model** (see `PS3_LEAKAGE_AND_VALIDATION.md` §2) — accounts exist in the PS3 section because a
consumer prices a visit, not because they locate a house.

### 2.11 `splits.csv` — 2,400 rows × 2 cols
train 1,680 / validation 360 / test 360, account-level, covering every account with no overlap. **But it is
account-level only**: 3,117 addresses map onto 2,400 accounts, and the same *building* can appear under different
accounts with near-identical text, so the file is necessary but **not sufficient** — the audit's normalised-duplicate
check found 9 duplicate texts, and the split must additionally group by normalized address hash.

---

### 2.12 `lenders.csv` — 6 rows × 4 cols (assigned shared; context only)
`lender_id` (PK), `lender_name`, `lender_code`, `lender_style`. Joined 0 orphans from `accounts.lender_id`.
Imported into the frozen tree 2026-10-07, byte-identical to the official Drive pack. **Contributes no address
signal** (portfolio-style differences ≤1.4 pts) `[S94]`: it exists so that reports can name the counterparty, and
so that no consumer invents a lender linkage. Never a model feature.

## 3. Cross-table integrity (both directions)

| Relationship | Result |
|---|---|
| `addresses.account_id → accounts` | 0 orphans (2,400/2,400) |
| `addresses.town_id → towns` | **1 orphan value: `OUT` (237 rows)** |
| `field_visits.address_id → addresses` | 0 orphans; 1,477 addresses touched |
| `field_visits.account_id → accounts` | 0 orphans |
| `field_visits.agent_id → agents` | 0 orphans; **9 of 30 agents ever visit** |
| `baseline_geocodes.address_id → addresses` | 0 orphans; **237 addresses uncovered** |
| `surveyed_addresses.address_id → addresses` | 0 orphans; 100 of 3,117 |
| `visit_gps_points.visit_id → field_visits` | 0 orphans; 5,578/5,578 visits have a trail |
| `(visit_id, seq)` uniqueness | 0 violations |
| `splits.account_id → accounts` | exact coverage, no duplicates |

**Town containment:** every check-in lies inside its town's envelope (T1 max 3.9 km, T2 4.4 km, T3 4.5 km from the town
centroid) — so "coordinate outside its declared town" is a usable integrity signal in a real dataset, and is dormant in
this one.

---

## 4. The twelve traps this dataset sets (carried into the design, not worked around)

1. `OUT` town (237 addresses) — no geocode, no locality, no field visit history. Must be a first-class output state.
2. Surveyed ground truth covers **zero** `OUT` addresses and only 1 rooftop row — the benchmark is optimistic.
3. `precision` is a *vendor* vocabulary; treating it as an error bound is wrong (pincode stratum: 1,376 m median, up to
   4,808 m).
4. Landmark names are not identities (14 distinct names, 198 duplicate town-name pairs).
5. Locality names repeat across towns (35 names / 36 rows).
6. 6-digit numbers in text are **not** necessarily pincodes (8.9% of them match nothing).
7. 24.9% of addresses have no punctuation and 0.3% have no digits at all.
8. Negative outcomes correlate with *agent giving up*, not with the true location (1,603 m, 1.3 min).
9. Duplicate photo hashes identify a bad actor **without any GPS anomaly** — integrity cannot be GPS-only.
10. GPS is clean in this dataset; a spoof detector cannot be validated here (fault injection required).
11. `ptp_id` (89.2% null) belongs to a different problem statement — it must be excluded from every feature set.
12. Visit exposure is demand-driven (19.9% → 84.8% by DPD band): any "the system improved" claim needs an exploration
    design, not an observational comparison.

---

## 5. When is each field known? (T0–T4, compressed; full map at `data/derived/ps3_leakage_map.csv`)

| Stage | Meaning | Fields |
|---|---|---|
| **T0** — before geocoding | known when the query is made | `address_text`, `address_type`, `source`, `added_date`, `town_id`, locality/landmark/town gazetteers, `vendor pin + precision`, `accounts.*` (context only) |
| **T1** — generated by candidate retrieval | our own artefacts | `candidate.*` (positions, granularity, ranks, licences) |
| **T2** — during the visit | exists only after the visit starts | `checkin_x/y`, `gps_accuracy_m`, `dwell_s`, `photo_hash`, all `trail_point.*` |
| **T3** — after the visit | outcome-side | `outcome`, `remark`, `ptp_id` (excluded) |
| **T4** — later outcomes | evaluation only | `surveyed_x/y`, future visits, future belief versions |

Hard rules enforced in code (`tools/check_leakage.py`): no T2+ field in any T0 feature set; `surveyed_*` never in
training; a visit's own outcome never used to place the coordinate used at that visit; every field-visit-derived feature
carries an explicit `as_of`; vendor coordinates cached at most as long as the licence permits, with the canonical point
ours.

---

## 6. What this audit changes in the design (the reason to do it first)

1. **Radius, not accuracy, is the headline output** — and it must be per stratum with an `n` guard, because the
   interesting strata (pincode, rooftop) cannot be calibrated on this sample.
2. **`UNPLACEABLE` is a product state**, driven by `OUT`/no-gazetteer-match/conflicting evidence — not an exception path.
3. **The integrity layer is rule-first** (duplicate media, trail agreement, dwell, coordinate reuse, agent baselines)
   with a learned scorer only when labelled faults exist; the dataset proves the *need* and supplies one labelled
   anomaly, nothing more.
4. **Negative evidence never relocates a coordinate by itself.** It updates record-quality and agent-quality dimensions; one negative observation can never relocate a coordinate by itself; accumulated independent negative evidence demotes confidence, widens the radius, marks `MOVED_SUSPECTED`/`CONTESTED` and triggers re-verification; only positive evidence or adjudication can establish a new primary coordinate (F2.1/D36).
5. **The retriever is worth building** (locality match ≈ vendor at 348 m vs 376 m on coarse records) and the ranker must
   therefore be benchmarked *against the vendor pin*, not against a straw man.
6. **Evaluation is entity- and time-aware** (account + normalized-address grouping; held-out surveyed set; exposure
   weights) because the data's duplicates, `OUT` block and demand-driven visits would otherwise inflate every number.

---

## 7. What the audit cannot answer (questions for the data owner, not assumptions)

1. Are `OUT` addresses simply *not covered*, or is `OUT` an "unknown town" bucket? (Changes the reason code and the
   roadmap, not the state machine.)
2. Is there a CRS for the metric plane, and can real deployments deliver `lat/lon`? (Needed before any map interaction.)
3. Do visits carry mock-location flags, device attestation, or IP in production? (Determines whether the integrity layer
   can ever claim spoof detection rather than anomaly weighting.)
4. Is the field force assigned by town/beat in production, or can an agent appear anywhere? (Changes agent-baseline
   logic.)
5. Are visit outcomes adjudicated later (e.g. a supervisor confirms `met_borrower`)? (Would supply labels for the
   integrity scorer.)
6. What is the real address-change cadence (shifting, renumbering)? (Sets memory decay and re-verification intervals.)


---

**Sources.** External claims resolve in `PS3_SOURCE_REGISTER.md` (`[S1]`–`[S50]`); internal measurements are
`[S90]` (audit log `data/derived/ps3_audit_full.txt`), `[S91]` (radius calibration
`data/derived/derived_ps3_radius_calibration.csv`) and `[S92]` (prior-pass measurements). Statements that cite no
external source rest on internal evidence and are labelled `[DATA]`/`[INFERENCE]` where they appear.
