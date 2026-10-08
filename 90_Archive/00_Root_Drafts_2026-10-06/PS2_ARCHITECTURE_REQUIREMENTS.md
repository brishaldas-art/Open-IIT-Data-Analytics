# PS2 — ARCHITECTURE REQUIREMENTS

**This is not the architecture.** It is the set of requirements the eventual `PS2_SANKET_SOLUTION_ARCHITECTURE.md` must satisfy, each one traceable to evidence in `PS2_DEEP_INTERNET_RESEARCH.md` (cited as §n) and each one answering: **what does this change in the actual collections workflow?**

Requirement IDs are stable; the architecture must address every one of them, and may only drop a "MUST" by recording the data or evidence reason.

---

## 0. Scope statement the architecture must open with

> PS2 governs **which action a collections platform is permitted to take, and which is worth taking**, on a contact point. It is not a contactability score, not a propensity ranker, and not a dialer. Its measurable outputs are (a) refusals with reasons and (b) expected net recovery per action for the actions that survive.

Evidence: §1.2, §7.2 of the PS2 research.

---

## 1. Inputs

| ID | Requirement | Evidence | Workflow change |
|---|---|---|---|
| **R1.1** | MUST ingest a **contact slate per account** (points with type, source, first-seen, last-verified, status). Slate, not "the number" | §2.2 — "no answer" conflates states; slate is the operational unit | Agent/engine chooses among points instead of redialling one |
| **R1.2** | MUST ingest **point-level call outcomes** (point dialled, timestamp in IST, channel, window, result disposition) | §2.4; §4.2 | Turns dialer logs into training labels |
| **R1.3** | MUST ingest the **incumbent policy's attempt metadata** sufficient to reconstruct a propensity (which queue/rule/allocator chose this action) | §4.1, §4.2 | Enables later off-policy evaluation; a one-line log change today |
| **R1.4** | SHOULD ingest **identity-verified events** (OTP / DOB / last-4 outcomes) | §2.2 | Separates "a human answered" from "the right human answered" |
| **R1.5** | MUST ingest **payment and roll-back outcomes** with a defined attribution window | §4.3 | Enables net-recovery framing; defines the label horizon |
| **R1.6** | MUST ingest **suppression state** (hardship, grievance open, bereavement, DNC/preference, legal hold) | §6.1, §6.2 | These are hard barriers, not features |
| **R1.7** | MUST ingest **complaint/conduct events** attributable to an account and action, when available | §6.1 | Gives the conduct exposure a measurable denominator |
| **R1.8** | MAY use **runtime telephony intelligence** (line type/status, reassigned lookups) as a paid call — never stored as a feature beyond the licence terms | §2.1 | Cheap pre-dial validation before expensive actions |

## 2. Outputs

| ID | Requirement | Evidence | Workflow change |
|---|---|---|---|
| **R2.1** | MUST output a **ranked, eligible action set** per account with, for each action: `estimate`, `cost`, `expected_net_value`, `eligibility` (permitted / refused + rule code) | §3.3, §5.3 | The allocator receives decisions, not scores |
| **R2.2** | MUST include an explicit **`wait` / no-action** option with its own expected value | §3.1 (E); PS2 §1.2 | Makes "leave the borrower alone this week" a legitimate, defensible output |
| **R2.3** | MUST output, for every refusal, a **machine-readable rule code and human sentence** | §6.3 | The refusal itself becomes the compliance artefact |
| **R2.4** | MUST NOT output any disclosure-capable action without an identity confidence above the configured threshold | §6.2 | Third-party disclosure becomes structurally impossible, not policed |
| **R2.5** | MUST output a **calibrated probability** (not a rank) wherever a probability is displayed | §23 (evaluation) | Prevents threshold decisions from being made on miscalibrated scores |
| **R2.6** | SHOULD output an **information-purchase recommendation** (trace / verification) with its price and expected information value | §5.3 | Replaces "trace after N attempts" rules |

## 3. Deterministic components (the rules floor)

| ID | Requirement | Evidence | Workflow change |
|---|---|---|---|
| **R3.1** | MUST implement, as configuration with versioning: contact-hour window, frequency ceilings, suppression list, permitted party definition, notice-before-visit precondition, recording/retention flags | §6.1, §6.2 | Compliance becomes a deployment of config, not a code change |
| **R3.2** | MUST construct the **candidate set** by rule *before* any model scores anything | §6.2 (Abe et al.: constraints supplied by a rules engine) | The model can never propose an unlawful action |
| **R3.3** | MUST make rule changes **auditable and dated**, and MUST be able to freeze disclosure actions on a config change pending review | §6.1 (effective 1 Jan 2027) | Handles the regulatory-change window without an outage |
| **R3.4** | MUST assign each refused action a **reason from a closed vocabulary** | §6.3 | Enables a compliance dashboard that aggregates refusals by rule |

## 4. ML components (and the limits on them)

| ID | Requirement | Evidence | Workflow change |
|---|---|---|---|
| **R4.1** | MAY contain **one** learned outcome model, predicting a multi-class outcome (no answer / wrong party / right party / other) and deriving P(connect) and P(right party) from it; two separate binary heads are permitted only with a documented reason | §19 (too many models); §23 | One model card, one calibration artefact, one drift monitor |
| **R4.2** | MUST calibrate the model (isotonic or Platt) **per segment** and monitor **ECE per segment** | §23 | Threshold decisions remain stable as the portfolio shifts |
| **R4.3** | MUST train with **selection-bias handling**: full-population features, and propensity weighting where the attempt log permits it, with clipping and effective-sample-size monitoring | §4.1, §4.2 | Model quality stops depending on the old policy's choices |
| **R4.4** | MUST NOT include a survival/hazard model in the MVP; retest timing uses **cohort-level priors**. A hazard model may be added only after a pre-registered lift test beats the baseline | §19 (attack 6) | Avoids modelling complexity that changes no decision today |
| **R4.5** | MUST NOT include graph/sequence/deep models in the MVP | §23 | Keeps the system explainable and buildable |
| **R4.6** | SHOULD include entity resolution of the platform's **own** records (Fellegi-Sunter / Splink) to surface cross-account contact conflicts (one number, many borrowers) | §2.3 | Detects shared/recycled points using internal evidence, without new data purchases |
| **R4.7** | MUST report, for every model, **PR-AUC, Brier, ECE per segment and precision at the operating budget**; ROC-AUC alone is not an acceptable model card | §23 | Evaluation matches the threshold decision being made |

## 5. Optimisation component

| ID | Requirement | Evidence | Workflow change |
|---|---|---|---|
| **R5.1** | MUST rank eligible actions by **expected net value = P(success) × value_of_success − cost − expected_conduct_cost**, using a **versioned cost table** | §5.3 | Field slots and human hours get allocated by value, not by list position |
| **R5.2** | MUST expose the **cost table and the incrementality assumption** as named parameters with ranges; the UI must never show a single point estimate | §5.1, §4.3 | Prevents invented ROI; a CFO can change one number and watch decisions move |
| **R5.3** | MUST price information purchases with an **EVSI-style rule** (threshold + sensitivity), not a count-trigger | §5.3 | Traces stop being fired by rule and start being bought by value |
| **R5.4** | MUST respect **capacity constraints** for scarce resources (human minutes, field slots) — optimisation is under constraints, not unconstrained ranking | §5.3 | Matches how collections operations actually allocate |
| **R5.5** | MUST NOT use live exploration; any exploration is limited to reallocating attempts already planned | §4.3, §19 (attack 10) | No extra borrower contacts are created by the model |

## 6. Compliance component

| ID | Requirement | Evidence | Workflow change |
|---|---|---|---|
| **R6.1** | MUST implement the eligibility filter inside the decision engine, not as a UI warning | §6.2 | Removes the "agent discretion" failure mode |
| **R6.2** | MUST treat the following as hard, model-independent controls: contact window, third-party disclosure prohibition, borrower/guarantor-only contact, suppression on hardship/grievance/death, notice-before-visit, agent identification, recording/retention | §6.1, §6.2 | Directly implements the RBI Directions due 1 Jan 2027 |
| **R6.3** | MUST NOT rely on consent or logs as the compliance claim; the claim is the *permitted set* | §6.3 | Changes the pitch from "we audit" to "we prevent" |
| **R6.4** | MUST support **purpose-limited data flows** consistent with DPDP (features derived for recovery, minimised, retained per policy) | §6.1 | Keeps the product deployable after May 2027 |
| **R6.5** | MUST NOT contact non-borrower parties, and MUST use graph/relationship data only as *features*, never as contact targets | §2.2, §6.1 | A feature set that stays lawful after the framework lands |

## 7. Data storage

| ID | Requirement | Evidence | Workflow change |
|---|---|---|---|
| **R7.1** | MUST store the decision record separately from operational tables, append-only, with the config, cost-table and model versions | §6.3 | One artefact answers "why was this contact made?" |
| **R7.2** | MUST define retention per data class (recordings ≥6 months per the Directions; DPDP retention/erasure policy documented) | §6.1 | Removes the retention conflict before it is found in an audit |
| **R7.3** | MUST NOT persist paid telephony/lookup attributes beyond licence terms; store derived flags instead | §2.1 | Keeps third-party licence risk off the balance sheet |
| **R7.4** | SHOULD store contact-point features in a point-level table with point-in-time correctness | §2.3 | Prevents leakage in training and in audit replay |

## 8. Training pipeline

| ID | Requirement | Evidence | Workflow change |
|---|---|---|---|
| **R8.1** | MUST use a **temporal split** (train / validate / test by time, not random) | §23 | Matches deployment reality (policy and portfolio drift) |
| **R8.2** | MUST build features **point-in-time**, derived from the decision timestamp | §4.2 | Prevents the model from seeing the future |
| **R8.3** | MUST document the **label taxonomy and its tiers** with validity notes (payment > identity-verified > disposition-inferred) | §2.2 | A reviewer can see what the model is actually learning |
| **R8.4** | MUST run a **model card + registry** step, including what the model cannot conclude | §23 | Sets honest expectations internally |
| **R8.5** | MUST retrain/recalibrate on a stated cadence with drift alarms (PSI, ECE) | §4.2 (drift) | Limits decay after policy changes |

## 9. Inference

| ID | Requirement | Evidence | Workflow change |
|---|---|---|---|
| **R9.1** | MUST support **batch allocation** (daily/nightly) as the primary path, with a synchronous path for on-demand checks | §23 | Fits how collections allocation works |
| **R9.2** | MUST complete a full portfolio pass (≈100k accounts, a handful of points each) in a batch window of ≤60 minutes on commodity infrastructure | [ASSUMPTION — sizing to be confirmed with CN] | Fits the nightly cycle |
| **R9.3** | MUST degrade to the rules floor if models or vendor lookups are unavailable, and must record that degradation | §6.2 | The operation never stops, and the audit says why |
| **R9.4** | MUST be callable per account with a latency target for interactive use (≤300 ms excluding external lookups) | [ASSUMPTION] | Lets a supervisor re-decide a case in the UI |

## 10. Feedback loop

| ID | Requirement | Evidence | Workflow change |
|---|---|---|---|
| **R10.1** | MUST capture action outcome (reached / not reached / wrong party / paid / promised) in a closed vocabulary | §2.2 | The loop closes on the same field the decision used |
| **R10.2** | MUST log the propensity of the action taken | §4.2 | Makes the next generation of the model evaluable |
| **R10.3** | MUST evaluate any policy change in **shadow mode** against historical data before activation | §4.2 | A bank can approve a change on evidence, not on faith |
| **R10.4** | MUST NOT present measured uplift unless a controlled comparison exists; otherwise label as simulated | §4.3 | Protects the project's credibility |

## 11. Auditability and explainability

| ID | Requirement | Evidence | Workflow change |
|---|---|---|---|
| **R11.1** | MUST write, per decision: timestamp (IST), account, slate, per-action estimates, cost-table version, model versions, rules evaluated, rule that blocked or permitted, chosen action, propensity, config version | §6.3 | One record answers a regulator, an auditor and an engineer |
| **R11.2** | MUST make the record **exportable** in a human-readable form (CSV/JSON) for a compliance officer | §6.3 | Removes the "engineering ticket" from the audit path |
| **R11.3** | MUST generate **reason codes from the gate and feature thresholds**, not from a post-hoc explanation model shown first | §6.3 | Explanations cannot drift from the logic |
| **R11.4** | SHOULD attach model attributions (top features) as a secondary artefact, never as the primary explanation | §6.3 | Keeps the audit line deterministic |

## 12. APIs

| ID | Requirement | Evidence | Workflow change |
|---|---|---|---|
| **R12.1** | Minimal surface: `POST /decisions` (account slate → ranked eligible actions), `GET /decision/{id}` (record + reasons), `POST /outcomes` (outcome feedback), `GET /health` (versions, ECE, drift, refusal rate) | §23 | Three endpoints integrate into an existing allocator |
| **R12.2** | MUST accept and return a **rule-config version** on every call | §6.3 | Prevents silent behaviour changes |
| **R12.3** | MUST return refusals with codes as a first-class part of the response | §6.3 | The refusal list is consumable by compliance directly |

## 13. Offline / batch requirements

| ID | Requirement | Evidence | Workflow change |
|---|---|---|---|
| **R13.1** | Batch path must run without internet access to third-party services beyond the licensed lookups it is configured to use | [ASSUMPTION] | Fits bank network constraints |
| **R13.2** | MUST support a **shadow mode** where decisions are produced, logged and not executed | §4.2 | Enables a zero-risk pilot |

## 14. Minimum viable implementation (48 h)

Rules floor with closed-vocabulary reason codes → one multi-class outcome model on synthetic or sandbox data → isotonic calibration → EV ranking with `wait` and a versioned cost table (ranges) → decision record → one screen that shows **a refused action, its rule code, and the action that replaced it**. Synthetic data must be marked as such in the UI and in the payload.

## 15. Production-grade extension

Propensity-weighted training and OPE on real logs → segmented calibration at scale → hazard-based retest timing (gated on measured lift) → entity-resolution-driven identity conflicts → EVSI for trace/verification at scale → multi-portfolio, segment-conditional policies (early bucket vs NPA: opposite defaults) → complaint-attribution analytics feeding the conduct-exposure estimate.

---

## 16. Non-requirements (explicitly out of scope)

Offer/negotiation modelling · dialer/telephony stack · CRM UI · route planning · graph-based contact targeting of third parties · live bandits · uplift claims without randomisation · any accuracy or ROI number the sandbox cannot support.
