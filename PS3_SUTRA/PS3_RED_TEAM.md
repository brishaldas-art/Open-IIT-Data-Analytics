# SUTRA — RED TEAM

**Method.** SUTRA is attacked from the position of someone who wants it to be wrong: a field agent with an incentive to
fake, a borrower with a reason to redirect the address, a dataset that drifts, a vendor that is confidently wrong, and a
clock that keeps moving. Every failure class below is answered with the same five questions, in the same order —
**detect · quantify · mitigate · rule-based or learned · monitor** — plus the residual risk and the honest failure
response. Nothing here is aspirational: each detection has a named signal, a named threshold source, and a named owner
(channel/rule), and where we cannot measure, the document says `[UNKNOWN]` instead of inventing a rate.

Two commissions drive the priorities: (1) never let a fabricated or leaked signal produce an impressive number —
"a mediocre honest number is better than a fake impressive number"; (2) assume the field is neither random nor honest.

---

## 0. The adversarial picture (who attacks what)

| Actor | Motivation | Primary lever | Our first defence |
|---|---|---|---|
| Field agent (lazy) | close visits fast | reuse photos, check in from the street/at the pin, short dwell | integrity weights + duplicate-media detection + trail agreement |
| Field agent (dishonest) | fabricated visit, inflated numbers | mock location, teleport, pre-visit photo set, coordinated "confirmations" | cross-signal inconsistency, agent baselines, two-independent-confirmation rule, mock flag |
| Borrower / household | hide, redirect, avoid contact | give a false address, deny identity, ask a neighbour to misdirect | negative evidence is never a coordinate label; contradiction store; re-verification queue |
| Dataset drift | reality changes | houses renumbered, localities renamed, town expands (the 237 `OUT` records are the visible edge of this) | staleness → radius widening; re-verification; drift detectors |
| Vendor geocoder | its own commercial objective | confident coarse answer with a "plausible" flag | never scored as confirmation (audit §2.7b); radius is ours and measured |
| Our own pipeline | silent leakage | post-visit, exposure-driven, entity-duplicate information | T0–T4 gates, receipts, `check_leakage.py`, exploration slice |
| Insider | manipulate the memory | hand-edit a belief row | append-only belief store, reason codes, no UPDATE path |

---

## 1. Failure classes, answered in full

### F1 — GPS spoofing (mock location, teleport, replay)
* **Detect:** platform mock flag (`isMock()`, [S26]); implied-speed implausibility between consecutive trail points (our
  audit's clean max is 32 km/h, so any step far above the fleet's p99 is suspect); coordinate reuse across agents/days;
  GPS that disagrees with IP/Wi-Fi-derived coarse location [S27]; a trail that does not pass through any plausible access
  geometry; stationary "walk" with zero displacement.
* **Quantify:** per-visit integrity multiplier `w_i ∈ [0,1]` with the *reason codes* attached; the audit measured this
  dataset to be spoof-free (`max speed 32.2 km/h`, zero teleports), so **we publish no detection rate** — we publish the
  fault-injection recall/precision from §2 instead.
* **Mitigate:** spoofed or suspect evidence **moves nothing**; it may only *reduce* confidence and *increase* the value of a
  re-visit. Two independent confirmations are required before any belief promotes to `CONFIRMED` [S49].
* **Rule vs learned:** rules ship (cheap, explainable, auditable); a learned integrity scorer is BUILD IF TIME and only
  when adjudicated labels exist.
* **Monitor:** flag rate per agent/day, rate of flags that were later adjudicated true, and the fraction of beliefs whose
  only support is low-integrity evidence (target 0).
* **Residual:** a sophisticated spoofer with device-level control is `[UNKNOWN]` and is documented as such — we may not
  claim detection we cannot measure.

### F2 — Duplicate / reused media ("evidence laundering")
* **Detect:** photo hash collisions per agent, per day, per address; near-duplicate perceptual hashes; timestamp/EXIF
  sanity; photo-of-a-photo indicators [S27].
* **Quantify:** **the audit found it**: agent FA009 has **156 duplicate photo hashes in 610 visits (25.6%)** versus
  <0.3% for every other agent (S90). That is a directly computable, per-agent statistic.
* **Mitigate:** hash reuse is a *weight reduction* for the affected visits, never an automatic rejection of the visit's
  outcome (weight, don't accuse); the agent's evidence baseline is recomputed; affected confirmations do not count toward
  the two-confirmation promotion.
* **Rule vs learned:** rule (hash identity + perceptual distance). Learned media forensics is out of scope.
* **Monitor:** per-agent duplicate rate with a control band; alert when a rate exceeds the fleet's p99 for two consecutive
  weeks; report the effect on beliefs attributed to that agent's evidence.

### F3 — Check-in at the wrong place, honestly
* **Detect:** the decisive finding of this audit (S90, `ps3_evidence_diagnostics.csv`): failure visits land closer to the
  **vendor pin** (84.9%) than to truth, with a 1.3-minute median dwell; success visits land 29.3 m from truth and beat the
  pin 96.8% of the time. Signals: dwell × distance-to-nearest-candidate × outcome dimension × trail deviation from the
  approach path.
* **Quantify:** per-visit likelihood ratios for each outcome dimension, computed per stratum and reported with n.
* **Mitigate:** only positive place outcomes may *move* belief; failures may only raise `record_suspect` and re-verification
  priority. **Pin-agreement is a banned feature** (`PS3_LEAKAGE_AND_VALIDATION.md` §2, row 4).
* **Rule vs learned:** rule-based likelihood table ships; a calibrated logistic/GBM version is the challenger.
* **Monitor:** distribution of `distance(check-in, chosen candidate)` by outcome; share of promotions driven by
  single-visit evidence (target 0); "wrong-door" rate on re-verified records.

### F4 — Contradictory evidence (two visits, two places)
* **Detect:** two or more high-integrity positive outcomes whose evidence coordinates differ by more than the tier radius.
* **Quantify:** contradiction mass (sum of weights on each side), plus intra-class agreement distance.
* **Mitigate:** the belief keeps **both** versions, marks the record `CONTESTED`, widens the radius, and routes to review;
  resolution requires either a tie-breaking high-integrity visit or human adjudication. Negative evidence never *deletes* a
  position — it demotes it and shortens its validity.
* **Rule vs learned:** rule (mass comparison); the learned layer may only *propose* an ordering, never a deletion.
* **Monitor:** contested-record count and age; adjudication queue length; share of contested records resolved by evidence
  (vs. by timeout).

### F5 — Address reality changes (shifting, renumbering, renaming, demolition)
* **Detect:** repeated `neighbour_says_shifted`; new positive evidence at a different coordinate; a locality rename in the
  gazetteer; staleness beyond the validity horizon; `OUT` growth.
* **Quantify:** validity horizon per tier; age distribution of confirmations; the audit's 90-day window is **too short** to
  observe real drift, so this is explicitly `[UNKNOWN]` in magnitude and simulated (experiments J/N/O).
* **Mitigate:** time decay in belief weight; radius widening with age (never silent staleness); re-verification priority
  rises with age × value; a "moved" outcome requires two independent confirmations to change the primary coordinate.
* **Rule vs learned:** decay and horizons are **rules** (auditable policy); the drift detector is statistical (ADWIN on the
  radius/coverage stream) [S31][S32].
* **Monitor:** share of beliefs past their horizon; median age at score time; radius widening events per week.

### F6 — Feedback poisoning through the loop
* **Detect:** a belief whose support traces to a single visit; sudden belief movement attributable to one agent; evidence
  arriving in bursts (batch-entered after a shift); promotions whose supporting visits share a device/time cluster.
* **Quantify:** "evidence concentration" (Herfindahl over contributing visits/agents); share of beliefs with ≥2 independent
  sources (target: the promotion rule makes this 100% by construction).
* **Mitigate:** two independent confirmations for promotion [S49]; caps on how much weight one visit may contribute; agent
  ineligibility (F2) propagating to all beliefs that depend on them; append-only log so any poisoned belief can be traced
  and rolled back.
* **Rule vs learned:** rule-based caps and promotion gate; the anomaly detection over concentration is statistical.
* **Monitor:** independent-support share; number of beliefs requiring rollback per month; time from poisoning to rollback.

### F7 — Selection bias / the loop flatters itself
* **Detect:** the audit measured visit exposure to be demand-driven (19.9% → 84.8% across DPD bands, S90); the loop only
  ever confirms addresses it chose to visit.
* **Quantify:** unweighted vs propensity-weighted metrics printed side by side; their divergence is the bias estimate.
* **Mitigate:** exposure weights in training and evaluation [S38]; a 5–10% **exploration slice** assigned by policy, not by
  demand [S36][S37]; cold-start/coverage metrics reported separately for the unvisited tail.
* **Rule vs learned:** weights are estimated by a propensity model (learned, audited), applied as a rule.
* **Monitor:** weighted-vs-unweighted gap; exploration-slice coverage; performance on low-exposure strata.

### F8 — Leakage into the model (our own pipeline as adversary)
* **Detect:** the 12 banned patterns (T0–T4 gates, banned prefixes, "latest-belief" joins, fit-on-train-only, entity
  duplication, radius chosen on test) enforced by `tools/check_leakage.py`.
* **Quantify:** negative controls printed in every experiment — shuffled-label model must be ~chance; agent-ID-only model
  must underperform; any violation is a build failure, not a footnote.
* **Mitigate:** receipts per artefact, split ledger with entity+time grouping, test-look counter, registered tensor hashes.
* **Rule vs learned:** entirely rule-based and mechanical. This is the one error class where "learned defence" is nonsense.
* **Monitor:** count of test-set queries per experiment; receipt coverage 100%; any number published without a receipt is
  retracted.

### F9 — Entity duplication across splits ("the same building twice")
* **Detect:** normalised text duplicates (10 rows today), near-identical coordinates across accounts, shared phone/landmark
  patterns.
* **Quantify:** duplicate-adjusted metrics; count of `group_key` groups spanning splits (target 0).
* **Mitigate:** `group_key = hash(account_id, normalised_text, town_id)` grouping; S-Eval (the surveyed 100) is disjoint by
  construction.
* **Rule vs learned:** rule (probabilistic record linkage, Fellegi–Sunter style, auditable) [S22].
* **Monitor:** groups spanning splits; metric delta between row-split and group-split evaluation (reported always).

### F10 — Overconfident radius
* **Detect:** measured coverage of the reported radius versus nominal (target ≥ nominal, e.g. 90% claims must cover ≥90% on
  S-Eval); coverage by stratum; coverage under time split.
* **Quantify:** empirical coverage with a grouped bootstrap interval; coverage gap per stratum (with the n ≥ 15 guard).
* **Mitigate:** geographically weighted conformal radius [S24][S25] rather than bootstrap (which under-covered 81% vs the
  claimed 90%); widen when the stratum is thin or the evidence is old; **never** quote a nominal level as measured.
* **Rule vs learned:** conformal calibration is a procedure (fitted on validation, reported on test).
* **Monitor:** rolling coverage on new adjudicated records; drift of the calibration map; share of scores produced with
  fallback (parent-stratum) calibration.

### F11 — Cold start / unseen everything
* **Detect:** new town, new agent, new locality, never-visited record, unfamiliar address grammar.
* **Quantify:** coverage of the T0 arms (measured: vendor pin 92.4%, matched locality 65.9%, town 92.4%); `UNPLACEABLE`
  rate (the 237 `OUT` records are 0% geocoded by the vendor — a real cold-start population).
* **Mitigate:** explicit cold-start mode that returns a coarse tier with a wide radius and an honest reason, never a
  fabricated precise point; the two-dimension outcome vocabulary means an unseen agent still gets a usable likelihood.
* **Rule vs learned:** rules + the vendor/town prior; the learned ranker is bypassed when no candidate exceeds the minimum
  evidence.
* **Monitor:** cold-start share; accuracy of cold-start answers separately from warm answers (never blended).

### F12 — Vendor geocoder is wrong (and confidently so)
* **Detect:** vendor pin far from any gazetteer-consistent locality; pincode-in-text disagreement; stratum inconsistency
  (a "rooftop" pin whose stratum-mates are all locality-level); the audit's own numbers (pincode stratum median 1,375.8 m,
  up to 4,808 m).
* **Quantify:** vendor error is our **measured baseline** on S-Eval (median 376.4 m; <100 m 9.0%) — the floor we must beat
  — not an assumption.
* **Mitigate:** the vendor pin is one arm among several; our canonical coordinate is ours; caching rules respected (Google
  30-day limit [S8]); licence class recorded per candidate.
* **Rule vs learned:** the arm set is a rule; the ranker learns when to distrust it (stratum + text evidence).
* **Monitor:** per-stratum vendor error on newly adjudicated records; share of decisions that *overrule* the vendor pin and
  their outcomes.

### F13 — Parsing / resolution failure
* **Detect:** unresolved spans; no locality match; pincode-shaped token that matches nothing (260 rows = 8.9% of those
  tokens); addresses with no digits (9) or no separators (24).
* **Quantify:** unresolved rate per stratum; effect on the final radius; hand-checked agreement for the optional parser.
* **Mitigate:** tiered resolver with explicit `unresolved` reasons; town prior as last resort; the record still gets a
  candidate + a wide radius, and the reason is visible to the user.
* **Rule vs learned:** rule + gazetteer first [S15][S16][S17]; statistical parser BUILD IF TIME; LLM RESEARCH ONLY.
* **Monitor:** unresolved rate trend; radius inflation attributable to unresolved fields.

### F14 — Landmark and locality ambiguity
* **Detect:** 14 distinct landmark names over 240 rows with 198 duplicate `(town, name)` pairs; `Nehru Colony` present in
  two towns with different pincodes (S90).
* **Quantify:** naive landmark snapping measured at 4,093 m median — the quantified reason landmarks are *evidence*, not
  targets.
* **Mitigate:** all name matching scoped to the delivered town; per-town alias tables with review; landmarks contribute a
  language prior and a plausibility feature only.
* **Rule vs learned:** scoping is a rule; alias expansion is a small auditable lookup built with review.
* **Monitor:** cross-town match attempts blocked; alias table changes (each one reviewed, versioned).

### F15 — Negative evidence becomes a catastrophic false label
* **Detect:** the audit's own trap — `address_not_traceable` check-ins sit 1,603.2 m from truth at a 1.3-minute dwell,
  standing near the pin 84.9% of the time.
* **Quantify:** measured per-outcome distance/dwell table (`ps3_evidence_diagnostics.csv`); design invariant: **negative
  outcome can never relocate a coordinate by itself; accumulated independent negatives only demote/widen/mark and re-verify — relocation requires positive evidence or adjudication (F2.1/D36)** — asserted by the belief-update rule and testable.
* **Mitigate:** negatives only (a) lower confidence, (b) raise `record_suspect`, (c) increase re-verification priority.
  `UNPLACEABLE` is a *state*, not a coordinate.
* **Rule vs learned:** rule, hard-coded in the belief update; a learned model may not override it (checked at promotion).
* **Monitor:** count of coordinate changes attributable to negative evidence (target 0, alarm on any).

### F16 — Memory grows without bound / staleness accumulates
* **Detect:** store size, average belief age, share of records never re-verified, duplicate belief versions, orphaned
  evidence.
* **Quantify:** bytes per record; re-verification rate; age histogram.
* **Mitigate:** append-only versions with compaction of *superseded* versions into a summarised form (never deleting the
  audit trail: the summary keeps counts and extremes); decay; expiry of raw GPS trails at 90 days while keeping derived
  evidence scores (`PS3_DATA_LINEAGE.md` §6).
* **Rule vs learned:** rule.
* **Monitor:** growth rate vs visit rate; compaction integrity checks (rebuilt summaries equal the originals).

### F17 — Cost and latency blow-up
* **Detect:** cost per 1,000 geocodes, vendor call share, reranker invocation rate, candidate count inflation, p95 latency.
* **Quantify:** measured in experiment P/cost runs; the design's budget is in `PS3_COST_ARCHITECTURE.md`.
* **Mitigate:** candidate cap (≤25), cheap arms first, reranker only when the top-2 margin is small, cache with the
  licence clock, offline-first demo path.
* **Rule vs learned:** policy rules (a learned router is RESEARCH ONLY).
* **Monitor:** cost per resolution, vendor dependency ratio, latency percentile alarms.

### F18 — Vendor/API outage, network loss, offline field use
* **Detect:** vendor error rate, timeout rate, offline flag on records.
* **Quantify:** resolution success rate with the vendor arm removed (a required ablation, experiment C).
* **Mitigate:** local index + memory must resolve without the vendor; the field app queues offline and syncs; every
  response declares what was unavailable.
* **Rule vs learned:** rule (degradation ladder).
* **Monitor:** offline resolution share; queued-record latency; reconciliations after sync.

### F19 — Regulatory / privacy / notice-eligibility abuse
* **Detect:** a coordinate used for a purpose other than the visited one; memory read by a process with no legitimate
  purpose; retention beyond policy; personal data in address text (it can contain names/phones).
* **Quantify:** purpose-classification error rates (measured, not assumed); access-log anomalies.
* **Mitigate:** every read declares a purpose; the eligibility gate is a separate component ([S48] shows the shipped
  pattern: status + review before acting); raw trails expire; DIGIPIN-style shareable codes ([S41]) can be emitted instead
  of raw coordinates where a code suffices; never store vendor content beyond licence ([S8]).
* **Rule vs learned:** purpose classification may be learned (with measured error) but the *gate* is a rule.
* **Monitor:** purpose-mismatch attempts; retention compliance; gate block rate by reason (a first-class metric, not noise).

### F20 — Manipulation by the data subject (address given deliberately to mislead)
* **Detect:** contradictions between deliveries/communications and the claimed address; repeated "no such person";
  an address that never yields a positive outcome despite multiple high-integrity visits.
* **Quantify:** per-record positive-evidence deficit; agent-verified physical description mismatch (a new field, flagged
  as a product gap, not built here).
* **Mitigate:** such records land in `record_suspect` with a reason, not in a coordinate; no penalty is inferred from
  absence alone (absence of contact ≠ absence of dwelling).
* **Rule vs learned:** rule + review queue.
* **Monitor:** records with ≥3 high-integrity negative outcomes and no positive; review outcomes.

### F21 — The system is good at the wrong thing (metric myopia)
* **Detect:** improving median error while p90/refusal/coverage stay flat (the audit's strata make this likely: the
  locality stratum dominates → easy wins hide pincode failures).
* **Quantify:** per-stratum reporting with n-guard; precision@1; refusal correctness; coverage; cost per success.
* **Mitigate:** fixed metric set (`PS3_LEAKAGE_AND_VALIDATION.md` §5); pre-registered experiment grid; the *pre-registered*
  primary metric, with secondary metrics reported — and no post-hoc selection of the flattering one.
* **Rule vs learned:** process rule.
* **Monitor:** metric dashboard with the six fixed families; any single-number claim must name its stratum and n.

### F22 — Silent schema/CRS change (the deployment risk hidden in the dataset)
* **Detect:** the dataset is a **local metric plane** with no lat/lon; a real deployment delivers lat/lng. A CRS mismatch
  would corrupt every distance silently.
* **Quantify:** impossible-coordinate checks (34 axis artefacts found), envelope containment per town (all check-ins
  contained here), plus a mandatory CRS declaration field.
* **Mitigate:** CRS declared at the ingest boundary (`PS3_CANONICAL_SCHEMA.md` §4); no implicit conversions; any transform
  recorded; the map-matching/HMM path stays RESEARCH ONLY until a real graph and CRS exist [S30].
* **Rule vs learned:** rule.
* **Monitor:** CRS declaration coverage 100%; coordinate range monitors per feed.

---

## 2. The fault-injection test bed (how we measure detections we cannot observe)

The audit proved the dataset contains **one** integrity anomaly (duplicate photos) and **no** spoofing. Therefore every
detector's performance is measured on injected faults, and reported as such:

| Injected fault | Injection rule | Expected detector behaviour | Reported metric |
|---|---|---|---|
| Mock-location visit | set the mock flag / offset trail by 300–2,000 m while keeping dwell | integrity multiplier drops; belief does not move | recall, false-positive rate on clean visits |
| Teleport | insert an impossible step (>80 km/h) | speed-plausibility rule fires | same |
| Photo reuse | copy a photo hash from another visit | duplicate-media rule fires; weight reduced | same, per agent share |
| Coordinated fake confirmations | three visits by one agent, same coordinate, same day | concentration cap blocks promotion | promotion-block rate |
| Stale belief | age a belief past its horizon without new evidence | radius widens; re-verification priority rises | widening behaviour |
| Contradictory confirmations | two positive visits 800 m apart | record marked `CONTESTED`; radius widened | contest recall |
| Drift | shift a locality's true centre by 300 m after t | ADWIN on the error stream fires; challenger retrains | detection delay, retrain count (target: ≪ per-visit retraining) |

Rules of the bed: the injected labels are never used for training (only for measuring detectors), fault rates are reported
as *injection* rates not as real-world rates, and the clean-visit false-positive rate is published alongside every recall
figure.

---

## 3. Claims we are forbidden to make (red-team output, binding)

1. A spoof-detection rate — we have no measured evasion data.
2. A drift-detection latency in production — our window is 90 days and synthetic.
3. Any accuracy figure computed on check-ins or on vendor pins.
4. A "90% coverage" without the measured coverage printed next to it.
5. An improvement claim whose comparison set was chosen by the system's own decisions (no exploration slice → no claim).
6. A benchmark number that includes any non-official data (impossible by guard: the tree holds official data only).
7. A "field-verified" claim for a belief whose only support is one visit or a low-integrity visit.
8. Any single-number accuracy figure that hides the stratum and the n.

---

## 4. Owner map (every defence has a name and a trigger)

| Defence | Type | Trigger | Owner (component) | Where enforced |
|---|---|---|---|---|
| Integrity weighting | rule | per visit | S9 evidence scorer | `PS3_FIELD_EVIDENCE_ARCHITECTURE.md` |
| Promotion gate (2 independent confirmations) | rule | per belief promotion | S10 fusion | `PS3_DYNAMIC_LEARNING_ARCHITECTURE.md` §5 |
| Negative-evidence quarantine | rule | per outcome | belief update | `PS3_UNCERTAINTY_ARCHITECTURE.md` §4 |
| Leakage gate | rule | per artefact | pipeline | `tools/check_leakage.py` |
| Radius calibration + coverage monitor | statistical | per stratum, weekly | S11 uncertainty | `PS3_UNCERTAINTY_ARCHITECTURE.md` |
| Drift detectors + retrain gate | statistical | daily stream | S13 slow loop | `PS3_DYNAMIC_LEARNING_ARCHITECTURE.md` §7 |
| Exposure weighting + exploration slice | mixed | per evaluation / per assignment | evaluation harness | `PS3_LEAKAGE_AND_VALIDATION.md` §6 |
| Cost/latency alarms | rule | hourly | serving layer | `PS3_COST_ARCHITECTURE.md` |
| Fault-injection bed | test | per release | QA harness | this document §2 |
