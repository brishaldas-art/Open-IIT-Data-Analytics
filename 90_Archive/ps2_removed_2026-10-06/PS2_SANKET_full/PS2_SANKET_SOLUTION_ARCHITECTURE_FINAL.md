# SANKET — PS2 SOLUTION ARCHITECTURE (FINAL)

**Phase 4, File 9 of 13.** 30 sections, as mandated. This is the deliverable architecture, replacing the Phase-2 hypothesis in `PS2_SANKET_SOLUTION_ARCHITECTURE.md`.

**Companion files:** `PS2_ADVANCED_ARCHITECTURE_RESEARCH.md` (12 architectures compared) · `PS2_ARCHITECTURE_OPTIONS.md` (7 options scored) · `PS2_ARCHITECTURE_SELECTION.md` (the decision and its arithmetic) · `FRONTIER_PS2_PS3_ARCHITECTURES.md` (every idea labelled BUILD NOW / BUILD IF TIME / PRODUCTION / RESEARCH ONLY) · `SIMILAR_SYSTEMS_REVERSE_ENGINEERING.md` (the systems this borrows from) · `PS2_PS3_DATASET_REVIEW.md` (the data verdict).

**Component labelling convention used throughout** *(the brief's Part M test — every component answers five questions)*:
`①what real system uses it` · `②what problem it solves` · `③what feeds it` · `④what if it is wrong` · `⑤why a simpler component cannot replace it`.

---

## 1. Problem, and the official statement it must satisfy

CreditNirvana's PS2 asks, in the client's own words, for the system that decides **which contact point to use, whether it is reachable, whether it is the right party, and what the next action should be** — with the trace/visit decision governed by economics rather than by an attempt counter. The official statement and our framing are reconciled line by line in `PS2_PS3_DATASET_REVIEW.md` §2; nothing below assumes a requirement the statement does not contain.

Three properties of the problem make it hard, and each one is a component later in this document:

1. **The state is latent.** Whether a phone belongs to the borrower, a relative, or a stranger is not observed — it is inferred from provenance, behaviour and outcomes, and it changes over time (recycled numbers, changed hands).
2. **The action space is priced but unpriced.** Calling, tracing, field-visiting and waiting have different costs and different irreversibility, and the client's system has no cost model in it.
3. **Conduct is a hard constraint, not a term in an objective.** From 1 Jan 2027 the amended RBI Directions impose calling windows, pre-visit notice, empanelment, certification and record-keeping on the recovery process `[VERIFIED]`. A debt-disclosing action against an unverified identity is not "a low-value action"; it is a prohibited one.

## 2. What this system is, in one paragraph

**SANKET** is a *decision system*, not a model. It maintains a belief state for every contact point and every account, fuses identity and behavioural evidence into calibrated probabilities, gates every action through a hard compliance rulebook, prices the remaining actions in expected rupees (including the price of *information* — traces and verifications are purchases), applies a conduct-tail penalty to irreversible actions, and then allocates the day's scarce capacity — agent minutes, trace budget, field slots — against that value. Every outcome, every refusal and every override is written to an append-only event log, which is both the audit artifact and the input to the next belief update.

## 3. Users and consumers

| Consumer | What they see | Why they care | Interaction |
|---|---|---|---|
| Allocation analyst | Tomorrow's plan: N calls by hour bucket, M field slots, ₹X trace budget, plus the refusal summary | Cure rate, cost per rupee recovered | Reviews exceptions, adjusts capacity |
| Collections supervisor | The exception queue: accounts the system refused to auto-touch, with the rule code | Defensibility, team utilisation | Approves or escalates |
| Compliance officer | Decision records, refusal ledger, conduct counters, hours-of-contact distribution | Regulatory inspection (effective 1 Jan 2027) `[VERIFIED]` | Audits; can freeze rule codes |
| Field officer | Address confidence band + visit priority (fed by PS3) | Whether the visit is worth the trip | Returns outcome + evidence |
| Dialer / orchestrator (machine) | Per-point action + permitted window + attempt ceiling | Execution | Emits outcomes back |
| Model risk / audit | Calibration reports, coverage by segment, event-sourced replay of any decision | Model governance | Queries, replays |
| **Not the borrower** — the borrower is the subject of the decision and the party this system exists to protect |

## 4. Business objective, stated as an optimisation problem

```text
Maximise   Σ_t  [ recovered_t − λ_conduct · ConductTail_t − OperatingCost_t ]
subject to: 0 regulatory breaches (hard) · capacity limits (hard, per skill/hour)
            · attempt/frequency ceilings (hard) · one action per point per window (hard)

ConductTail = CVaR_α over the loss distribution of {wrong-party contact, disclosure event,
              out-of-window contact, un-notified visit}   — α and λ published
```

**Primary KPI:** rupees recovered per rupee spent (all-in: agent minute, dial attempt, trace, field slot).
**Secondary KPIs:** right-party-contact rate per attempt; third-party contact rate (**must not rise** — the naive-RPC-maximising policy raises it from 0.066 to 0.121 `[DATA]`); trace spend per successful trace (today ₹455 `[DATA]`); wasted-visit rate; complaints per 10,000 contacts.
**Anti-KPI, reported alongside:** attempts per account and contacts per week — recovering the same money with *fewer* contacts is a win, not a draw.

## 5. Non-goals and explicit refusals

| Not building | Why | What would change it |
|---|---|---|
| Contextual bandit / online policy learning | Propensities degenerate (≡1.0 on 94.6% of attempts), random arm 5.1% and worse (0.134 vs 0.166), no reward attribution (no campaign id) `[DATA]` | A legal pilot with logged propensities + campaign-level payment attribution |
| Constrained MDP over the full collection journey | 3 months of one policy; the reference deployment consumed ≈$5 M research + ≈$4 M engagement `[S-33]` | Multi-year longitudinal data + a research budget |
| Uplift / incremental-value claims | The randomisation is confounded (skewed DPD/outstanding, 123 accounts) `[DATA]` | Clean randomisation with a real control arm |
| LLM-driven agents inside the decision loop | Latency, cost, non-determinism, auditability; nothing in the requirements needs generation | A specific document-understanding task with a deterministic fallback |
| A voice bot re-build | Out of PS2 scope; 3,761 bot attempts already exist in the log and are consumed as evidence `[DATA]` | — |
| Complaint-prediction model | No case-level complaint labels; the FY24 figure (85,281, +42.7%) is a national aggregate `[VERIFIED]` | Internal complaint-labelled case data |

## 6. Architecture at a glance

```text
┌──────────────────────────────────────────────────────────────────────────────────┐
│  L0  EVENT LOG (append-only, immutable, event-sourced)                           │
│      call.outcome · trace.returned · payment.received · visit.completed          │
│      refusal.recorded · override.recorded · coordinate.promoted                  │
└───────────────────────────────────────┬──────────────────────────────────────────┘
                                        ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│  L1  STATE ESTIMATION            ContactPointState ⊕ AccountRelationshipState    │
│      reachability · identity posterior · dead-streak · decayed recency           │
└───────────────────────────────────────┬──────────────────────────────────────────┘
                                        ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│  L2  EVIDENCE FUSION             provenance ⊗ behaviour ⊗ verification ⊗ graph   │
│      → P(borrower) with an interval; shared-number exposure flag                 │
└───────────────────────────────────────┬──────────────────────────────────────────┘
                                        ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│  L3  PREDICTION                  calibrated multi-class over dispositions        │
│      (pre-dial features only · honest AUC 0.670 · isotonic per segment)          │
└───────────────────────────────────────┬──────────────────────────────────────────┘
                                        ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│  L4  POLICY GATE (hard, deterministic, closed vocabulary)                        │
│      hours · DNC · notice · attempts · disclosure-eligibility · certification    │
│      → ALWAYS produces either an action token or a REFUSAL RECORD                │
└───────────────────────────────────────┬──────────────────────────────────────────┘
                                        ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│  L5  ECONOMICS        EV(action) → EVSI(trace, verify) → CVaR penalty λ          │
│      every number carries a published range; every refusal carries an arithmetic │
└───────────────────────────────────────┬──────────────────────────────────────────┘
                                        ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│  L6  ALLOCATION       day-level: agent-minutes · shift slots · ₹ trace budget    │
│      greedy with Lagrangian prices → OR-Tools MILP (if time) · shadow prices     │
└───────────────────────────────────────┬──────────────────────────────────────────┘
                                        ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│  L7  EXECUTION + FAILURE PATHS     dialer API · field app · trace vendor         │
│      every action declares: timeout · partial · rejected · fallback · escalation │
└───────────────────────────────────────┬──────────────────────────────────────────┘
                                        │ outcomes, propensities, overrides, reasons
                                        └──────────────► back to L0 (belief update)
```

## 7. Component inventory (the five-question test)

| # | Component | ① Real system using it | ② Problem it solves | ③ Fed by | ④ If it is wrong | ⑤ Why simpler won't do |
|---|---|---|---|---|---|---|
| C1 | Event log & replay | Standard in regulated decisioning; event sourcing `[S-59]` | No auditability; cannot re-run a policy | All L7 outputs | Worst failure — everything downstream is unauditable | A mutable DB row loses history; the refusal record is the product |
| C2 | `ContactPointState` | NYS DTF legal-state model `[S-32]`; skip-trace queues with memory `[S-60]` | "Should we ever call this again?" | Dispositions, trace results, payments, visits, time | Over-suppression (≥1 dead point is still 37.4% of RPCs `[DATA]`) | A stateless classifier cannot express *sequence* (3rd consecutive dead = 0.067 vs 0.180 `[DATA]`) |
| C3 | `AccountRelationshipState` | Portfolio-level collectors (Experian, Credgenics) `[S-1][S-26]` | Which points belong to *this* account, and which to a household | `phones` + `verified_contact_points` + graph | Wrong grouping → a "safe" call discloses to a neighbour | Per-point scoring misses sharing (**43.2% of attempts are on shared numbers** `[DATA]`) |
| C4 | Identity/evidence fusion | TransUnion contact graph `[S-10][S-11]`; Fellegi-Sunter/Splink `[S-44]` | P(borrower) with a defensible interval | Provenance, behaviour, verification, edges | A wrong posterior converts a compliance refusal into a disclosure | Provenance priors alone (CV AUC 0.813) ignore behaviour; the interval is what the gate consumes |
| C5 | Prediction (multi-class) | Every vendor `[S-1][S-3][S-16]` | Rank *within* the eligible set | Pre-dial features only | Miscalibration misallocates minutes; leakage inflates it (0.933) `[DATA]` | Rules alone are 0.157/call vs 0.1762 incumbent `[DATA]` — the model must earn its place or be cut |
| C6 | Policy gate | Pega constraint layer `[S-19]`; NYS DTF ~300 legal rules as binary constraints `[S-33]` | Makes prohibited actions structurally impossible | Rulebook config + state | A bug here is a regulatory breach | Post-hoc filtering is provably weaker than candidate-set construction (§12) |
| C7 | EV / cost model | Experian constraint-based optimization `[S-3]`; FICO `[S-16]` | Prices actions in rupees | Outcomes × cost table (ranges) | Confident nonsense if costs are invented | Ranking without cost cannot answer "is the ₹104 trace worth it?" |
| C8 | EVSI / information purchase | Multi-vendor trace orchestration `[S-60]`, insurance industry practice; VOI theory `[S-42]` | Stops buying information that cannot change a decision | Trace hit rate 22.8%, price ₹104 | Over-buying (77% waste today `[DATA]`) | A constant trigger cannot be optimised; a "trace-success model" is not learnable here (AUC 0.574 vs 0.772 `[DATA]`) |
| C9 | Risk-sensitive layer | CVaR in energy/disaster logistics `[S-43]`; not publicly described in collections `[INFERENCE]` | Makes irreversible actions require *confidence* | Loss distribution + λ | Over-conservatism | Expected value alone approves a high-mean/high-tail field visit |
| C10 | Day-level allocator | Experian/FICO solvers `[S-3][S-16]`; mTSP routing `[S-31]` | Fills scarce capacity by value, not list order | ENV matrix + capacity | Dishonest precision if inputs are fabricated | Greedy ranking ignores joint capacity and produces infeasible days |
| C11 | Refusal ledger | Distinctive; NYS/FICO gate but do not publish refusals | Turns "we chose not to" into an artifact | Gate + EV + EVSI | Refusals become invisible → pressure to over-contact | A log field is not a ledger; the ledger is queryable by reason |
| C12 | Calibration & coverage monitor | Model-risk practice in BFSI `[S-30]`; conformal `[S-53]` | Probabilities must stay honest as data drifts | Outcomes vs predictions | Silent drift degrades allocation invisibly | ECE alone does not give intervals; per-segment coverage does |

**Components from the Phase-2 hypothesis that were cut** (recorded, not silently removed): the GNN over the contact graph (a shared-number *flag* captures the decision value at 1% of the cost); the sequence model (label noise and 3-month horizon); the per-action outcome models (no arms to learn from); the "exploration engine" (no licence to explore).

## 8. State model

### 8.1 `CONTACT_POINT_STATE` — the belief object

**Owner:** the contact-point record in the customer-communication service (production) / `sanket.hmm` in the demo. **Updated by:** events only — never by a nightly overwrite, so replay is exact.

| Field | Meaning | Update mechanism | Decay |
|---|---|---|---|
| `identity_p` | P(this point reaches the borrower) | Fusion (C4) on verification, call outcome, graph change | 0.985/day (recycled-number risk) `[ASSUMPTION, tunable]` |
| `reach_p` | P(answered next attempt) | Behavioural model + outcome history | 0.97/day |
| `dead_streak` | Consecutive no-contact outcomes | `+1` on no-contact disposition, `0` on any positive | — |
| `state` | FRESH · ACTIVE_REACHABLE · ANSWERED_UNKNOWN · THIRD_PARTY_CONFIRMED · RIGHT_PARTY_REACHED · DEAD_3 · DISPUTED · VERIFIED_WRONG | transition table (§8.3) | — |
| `attempts_window` | Attempts in rolling window vs ceiling | Counter | Rolling |
| `last_contact_at`, `last_payment_at` | Recency inputs | Events | — |
| `exposure_flag` | Shared-number / third-party exposure | Graph edge (43.2% of points are shared `[DATA]`) | — |

### 8.2 `ACCOUNT_RELATIONSHIP_STATE`

**Owner:** the collections case record. **Update:** payment, promise-to-pay, dispute, field outcome, DPD roll.
Contains: DPD bucket, outstanding, PTP history and breaks, payment recency, dispute/freeze flags, hardship markers, **field-visit outcome summary and address confidence band (from PS3)**. The last two are the PS2↔PS3 join and are the reason the two systems are one product (§21).

### 8.3 Transition table (the deterministic skeleton)

| From | Event | To | Also does |
|---|---|---|---|
| FRESH | call, no answer | FRESH (`dead_streak+1`) | — |
| FRESH | answered, unknown party | ANSWERED_UNKNOWN | sets `identity_p` prior |
| ANSWERED_UNKNOWN | answered, self-identified third party | THIRD_PARTY_CONFIRMED | sets `exposure_flag`; blocks disclosure |
| ANSWERED_UNKNOWN | answered, borrower confirms | RIGHT_PARTY_REACHED | `identity_p → ≥0.95`; unlocks disclosure |
| any | `dead_streak = 3` on **consecutive** no-contact | DEAD_3 | **refuses dialing**; route to trace/visit/letter |
| THIRD_PARTY_CONFIRMED | verification proves shared/recycled | VERIFIED_WRONG | permanent refusal for this account |
| any | dispute raised | DISPUTED | freezes all action pending review `[R6]` |
| RIGHT_PARTY_REACHED | payment received | RIGHT_PARTY_REACHED (refreshed) | resets dead streak |
| any | daily decay crosses threshold | COLD | reduces priority, keeps state |

### 8.4 Why a state machine and not a hidden-state model

The measured justification: RPC per attempt by prior dead count is 0.180 / 0.177 / 0.160 / **0.067** for 0/1/2/3+ `[DATA]`. The collapse happens only at 3+, and crucially points with ≥1 prior dead call are **42.7% of all calls but 37.4% of all RPCs** `[DATA]` — the naive "never call a dead point" rule is wrong, and only a *sequence* representation gets this right. A hidden-state model would need to learn a sequence effect we can already measure with a counter.

## 9. Evidence fusion (P(borrower) with an interval)

```text
P(b) = σ( w_prov·provenance + w_beh·behaviour + w_ver·verification + w_graph·sharing )  → interval via per-segment coverage
```

**Measured inputs** `[DATA]`:

| Source | Evidence | Value |
|---|---|---|
| Provenance | P(borrower\|provenance) | skip_trace 1.00 · kyc_origination 0.73 · borrower_update 0.67 · bureau 0.30 · reference 0.16 · employer 0.07 |
| Behaviour | answered-then-third-party rate, talk-time shape, repeat self-identification | CV AUC 0.899 combined vs 0.813 provenance-only vs 0.508 majority |
| Verification | `verified_contact_points` | **250 labels, created 2026-07-02, i.e. after the dial window → evaluation only, never training** `[DATA]` |
| Graph | shared-number edge | 43.2% of dials sit on shared numbers; third-party rate 0.080 (shared) vs 0.061 (unique) `[DATA]` |

**The refusal this buys:** reference and employer points are 14% of all calls, are *answered* at 0.44–0.46 (they ring), but verify as third-party in **81–93%** of cases `[DATA]`. Under a P(RPC)-maximising policy these are attractive; under a disclosure rule they are ineligible. This single asymmetry is the clearest demonstration in the whole submission that ranking and permission are different problems.

## 10. Prediction layer

| Aspect | Decision |
|---|---|
| Target | Multi-class over the 16 dispositions `[DATA]`, collapsed for scoring into {right party, third party, no-contact, unavailable} |
| Features | **Pre-dial only.** Excluded by policy: `network_response`, call durations, `disposition` itself, and anything timestamped after the attempt start. Including them lifts AUC to **0.933** and is an anti-pattern `[DATA]` |
| Model | LightGBM, monotonic constraints where justified; logistic baseline retained as the control |
| Honest performance | Test AUC **0.670** (GBM) vs **0.604** (LR); feature importance ΔAUC: `prior_rpc` 0.0894 > self/third-party relation 0.0275 > hour 0.0274 > everything else ≤0.009 `[DATA]` |
| What it is *for* | Ordering within the eligible set and providing the `reach_p` term for EV. **It does not decide who may be contacted** (L4 does) |
| Cold start | New account → cohort prior by DPD bucket × product × provenance mix; the state machine and the gate work unchanged |
| Refusal to over-claim | The model is modest and the deck says so; the leakage number is shown as a caution, not a result |

## 11. Calibration and uncertainty strategy

Every probability in the system has a stated evaluation method — this is a hard requirement of the brief, and the table is the answer.

| Probability | Method | Metric | Action if it fails |
|---|---|---|---|
| `reach_p` | Isotonic per segment (DPD × point provenance × time bucket) | ECE, reliability curve, Brier | Fall back to segment base rate; flag the segment |
| `identity_p` | Empirical coverage of the interval on the 250 verified points | Empirical vs nominal coverage | Widen intervals; freeze disclosure unlock above the failed stratum |
| `P(RPC)` | Same as `reach_p` | ECE + top-decile lift | Suppress the model's contribution to EV for that segment |
| `P(trace yields info)` | Not modelled — measured base rate 22.8% with an interval `[DATA]` | — | If the interval straddles the EVSI threshold → refuse the purchase (conservative default) |
| `P(payment \| RPC)` | Cohort survival by DPD band; sensitivity band ± | Observed vs predicted within 7/30 days | Ranges widen; EVSI refuses more |
| Allocation outcomes | Post-hoc: realised vs planned value per shift | MAPE by shift | Reduce MILP to greedy for the affected shift |
| Coverage guarantees | Per-town, per-stratum conformal radii (shared with PS3) `[S-53]` | Nominal vs empirical coverage | Publish the failure; never silently widen |

**Rule:** no probability enters the objective without a row in this table. **Rule:** every EV carries a range; the system must never display a single-point expected value.

## 12. Policy and permission layer

**Design principle: the compliant candidate set is *constructed*, not filtered.** Post-hoc filtering means the optimiser has already spent capacity on ineligible work; constructing the set first makes prohibited actions structurally impossible and keeps the refusal reason exact.

### 12.1 The rulebook (closed vocabulary, versioned, config—not code)

| Code | Rule | Type | Source |
|---|---|---|---|
| `PG-01` | Contact only 08:00–19:00 `[VERIFIED: RBI Amendment Directions, effective 1 Jan 2027]` | Hard | Regulatory |
| `PG-02` | Field visit requires ≥1-day prior notice `[VERIFIED]` | Hard | Regulatory |
| `PG-03` | DNC / do-not-disturb in force | Hard | Regulatory + client |
| `PG-04` | Disclosure-eligible only if `identity_p ≥ θ_identity` (§9) | Hard | Conduct policy |
| `PG-05` | Attempt ceiling per point per day/week (`dead_streak ≥ 3` → block) | Hard | Observed optimum `[DATA]` |
| `PG-06` | Dispute/freeze/hardship → no collection action | Hard | Client policy |
| `PG-07` | Agent must hold current DRA certification; empanelled agency only `[VERIFIED]` | Hard | Regulatory |
| `PG-08` | Recording retention ≥6 months bi-directional `[VERIFIED]` | Hard | Regulatory |
| `PG-09` | Third-party point → no debt disclosure, ever (identity-led contact only) `[VERIFIED: DPDP + conduct]` | Hard | Regulatory + ethics |
| `PG-10` | Device-locking timing 30/60 days `[VERIFIED]` | Hard | Regulatory |
| `PG-11` | Bot/AI contact only if the same rules are enforced at the bot layer (3,761 bot attempts exist `[DATA]`) | Hard | Policy |
| `PG-12` | Capacity: agent minutes, field slots, trace budget (soft-formulated as constraints) | Hard | Operational |

**Two categories, never mixed:** *regulatory* rules are `[VERIFIED]` with a citation and cannot be tuned by the model; *policy* rules (θ_identity, ceilings, budget) are parameters with owners and change logs.

### 12.2 The refusal record

```json
{ "refusal_id": "...", "account_id": "...", "point_id": "...", "action": "dial|trace|visit|notice",
  "reason_code": "PG-05", "reason_text": "dead_streak=3 on this point",
  "inputs": {"dead_streak":3,"prior_attempts_7d":4}, "policy_version": "2026-10-06.1",
  "counterfactual_value": 118.0, "counterfactual_range": [64, 205],
  "data_snapshot_hash": "sha256:...", "ts": "..." }
```

`counterfactual_value` is the point of the ledger: every refusal states *what we believe we gave up, with a range*. That is what turns "the system was conservative" into a decision the business can audit and challenge.

## 13. Economic layer

### 13.1 Objective (explicit, as required)

```text
For each eligible action a on point p of account i:
    ENV(a) = P(success|a) · Value(a) · (1 − haircut_uncertainty) − Cost(a) − λ·Risk(a)
    where  Value(dial|contact)   = expected recovery over 7/30 days given the account's DPD band
           Value(visit|met)      = expected recovery, higher, plus location-confirmation value to PS3
           Value(trace)          = 0 by itself — a trace is only valuable through the action it changes (§13.3)
           Cost(·)               from the published cost table with ranges
```

**Cost table (parameters, published as ranges, every line sourced or labelled `[ASSUMPTION]`):**

| Cost | Central | Range | Note |
|---|---|---|---|
| Agent minute | ₹6.0 | ₹3.5–9.0 | `[ASSUMPTION]`, aligned to BPO-loaded cost; must be replaced by the client's figure |
| Dial attempt (machine) | ₹0.15 | ₹0.05–0.4 | `[ASSUMPTION]` |
| Skip trace | **₹104** | ₹60–150 | **`[DATA]` — measured mean in `skip_traces`** |
| Field visit slot | ₹180 | ₹90–350 | `[ASSUMPTION]`; includes travel time |
| SMS/e-mail | ₹0.20 | ₹0.05–0.5 | `[ASSUMPTION]` |
| Third-party contact (conduct) | ₹600 | ₹150–2,500 | `[UNKNOWN]` — no credible public source; must be client-supplied; drives λ |

**Honesty rule:** any output that depends on an `[ASSUMPTION]` row shows the sensitivity alongside. The submission must never present a single rupee figure as measured when it is parameterised.

### 13.2 The one measured economic result — trace spend

| Metric | Measured `[DATA]` |
|---|---|
| Traces | 766, mean cost **₹104** |
| Total spend | **₹79,650** |
| Traces that yielded information | 22.8% |
| **Spend that produced nothing** | **₹61,605 (77%)** |
| Cost per trace that found something | ₹455 |
| Cost per right-party contact attributable | ₹305 |
| Learnability of trace success | CV AUC **0.574** vs majority **0.772** → *below chance; not learnable* |

**Conclusion that drives the design:** you cannot predict which trace will work, so you must decide on *value*: buy information only when it can change an action. The trigger in the data is a constant `[DATA]` — i.e. the incumbent has no rule at all.

### 13.3 EVSI — information acquisition as a first-class primitive

```text
EV0 = max over actions under current belief            (usually: call the best point, or wait)
EV1 = E_info[ max over actions under posterior ]        (belief updated by the trace)
EVSI = EV1 − EV0 ;   BUY iff EVSI > price(trace) = ₹104
```

Worked example on real fields: an account whose only *unverified* point is a `reference` number (P(borrower) ≈ 0.16 `[DATA]`). Under the gate, no disclosure is permitted and the dial has almost no value → EV0 ≈ small. A trace that would confirm or kill the point changes the action set → EV1 − EV0 > ₹104 only when the expected recovery is large enough. **For a low-ticket account, the correct decision is to refuse the trace** — and to say so in the ledger. That is the mechanism that touches 77% of spend `[DATA]`.

**Second information purchase: the field verification.** EVSI here is larger because a visit also delivers location evidence to PS3 (§21.3), and because a met visit confirms identity at ≥0.95. The allocator (L6) prices both together.

## 14. Risk-sensitive layer

```text
Risk(a) = P(bad outcome | a) · Cost(bad) + κ · σ_model(decision)
score   = ENV(a) − λ · Risk(a)
```

- **Bad outcomes priced:** wrong-party contact, debt disclosure to a non-borrower, out-of-window contact, un-notified visit, complaint.
- **Irreversibility weighting:** `λ_visit > λ_dial ≥ 0`. A field visit cannot be un-rung; a notice cannot be un-sent.
- **Uncertainty term `κ`:** actions whose model inputs are in a low-coverage segment (from §11) are penalised — the system declines to act on its own weak confidence.
- **Discipline:** λ published, sensitivity curve shown, and **every action refused by λ alone is reported separately from actions refused by rules** — otherwise risk aversion becomes an unaccountable veto.
- **Evidence:** CVaR is standard practice in energy/disaster optimisation `[S-43]`; no reviewed collections vendor publishes a comparable conduct-tail term `[INFERENCE]`, which is precisely why it is worth building and why it must be implemented conservatively and transparently.

## 15. Allocation layer

```text
maximise  Σ_{i,p,a} ENV(a) x_{i,p,a}  −  λ·CVaR-term
subject to Σ x ≤ AgentMinutes / FieldSlots / TraceBudget        (capacity)
           x_{i,p,a} ≤ eligible(i,p,a)   ∧   Σ_a x ≤ 1 per point per window
           notice / hour-window / attempt-ceiling constraints hold for every selected action
           x ∈ {0,1}
```

| Mode | When | Solver | Output |
|---|---|---|---|
| Greedy with Lagrangian prices | 48-hour demo (default) | ~150 lines | Plan + shadow prices (₹ per agent-minute, per slot, per trace) |
| MILP | BUILD IF TIME | OR-Tools | Optimal plan + duals + infeasibility diagnosis |
| What-if | No client capacity data | Either | Plan under the brief's figures: 1,000 accounts / 200 agent-hours / ₹50,000 traces / 50 field slots |

**Shadow prices are the deliverable's best explanation device:** "one more field slot is worth ₹X of expected recovery tonight" is a sentence a collections head immediately understands and can argue with.

**Always-present slack action:** `wait` is in the action set, so the plan is never forced into pressure-calling to fill capacity.

## 16. Actions and their failure paths

Every action declares what happens when it fails — the brief's requirement, and the most commonly missing section in hackathon architectures.

| Action | Success signal | Failure mode | Failure handling |
|---|---|---|---|
| Dial (machine) | Answer + disposition | No answer · IVR drop · carrier reject · dialer outage | No answer → `dead_streak+1`, reschedule per ceiling; carrier reject → point penalised, routed to verification; **dialer outage → plan degrades to the top-N by EV with a logged degradation event** |
| Dial (agent) | Disposition recorded | Agent unavailable · call abandoned mid-script · system down | Re-queue with priority retained; abandoned calls counted in conduct metrics |
| Trace | Vendor returns a new point or a negative | Vendor timeout · partial result · generic junk point | Timeout → escalate once with backoff, then record `info_not_purchased`; junk point → evidence gate rejects it and the vendor hit-rate for that account stratum is down-weighted |
| Field visit | Outcome + GPS + media | Address not traceable · locked · borrowed-integrity failure · agent no-show | Not traceable → **negative outcome must not move the coordinate (PS3 rule)**; integrity failure → visit excluded from learning, agent flagged; no-show → slot recycled within the shift |
| Notice | Delivery recorded | Undeliverable · disputed receipt | Fall back to a second channel; the visit is not scheduled until delivery is proven (PG-02) |
| SMS/e-mail | Delivery + response | Bounce · spam filter | Small EV; failure has no penalty beyond the cost — the reason it is the default filler |
| Wait | — | Opportunity cost | Explicitly valued: ENV(wait) = option value of better information later; prevents the optimiser from inventing activity |

## 17. Event sourcing, audit and replay

- **Event vocabulary (shared with PS3 — see File 11):** `call.completed`, `trace.returned`, `payment.received`, `visit.completed`, `visit.rejected_integrity`, `refusal.recorded`, `override.recorded`, `coordinate.promoted`, `policy.versioned`.
- **Immutability:** events are append-only; corrections are new events. State is a *projection*, rebuildable at any timestamp.
- **Replay:** "what would policy v2026-11 have done with June's events?" is a query, not a project. This is how the team answers the operator question *"can we trust 1 Jan 2027 compliance before 1 Jan 2027?"*
- **Decision record:** every executed action stores the state hash, the feature vector hash, the model version, the policy version, the ENV with range, and the human override if any.
- **Privacy:** the log stores point references, not raw contact data; recording retention (≥6 months, bi-directional) `[VERIFIED]` is satisfied by the contact-recording store, not by this log — stated explicitly to avoid a DPDP violation by design.

## 18. Feedback loop and belief update

| Event | State effect | Model effect | Caveat enforced by design |
|---|---|---|---|
| `call.completed` | `dead_streak`, `reach_p`, `state` | Training row (with the pre-dial features only) | Propensity logged; **no policy learning** (O7) |
| `trace.returned` | new point / point killed | Provenance prior refresh; EVSI base-rate update | Constant-trigger period is not learnable — decision rule only |
| `payment.received` | resets streak, refreshes value | Value model refresh | **No causal claim**: 60% of payments fall within 7 days of an RPC but there is no campaign id `[DATA]` |
| `visit.completed` | identity ≥0.95 if met; address confidence to PS3 | Feature + EVSI calibration | Contaminated check-ins excluded (§16, PS3 integrity gate) |
| `override.recorded` | supervisor's decision | **Override reasons are the highest-value training signal in the system** | Analysed weekly; systematic overrides indicate a rule or threshold is wrong |
| `coordinate.promoted` (from PS3) | address confidence band updates | Field-slot EV updates | Two-confirmation rule `[S-56]` |

## 19. Data mapping — the dataset controls the design (Part N)

Every component maps to real tables/columns in `data/raw`, and every trap discovered in the audit is preserved in the design.

| Table | Rows | Columns the architecture actually consumes | Trap preserved in the design |
|---|---|---|---|
| `accounts.csv` | 2,400 | `account_id`, DPD bucket, outstanding, product | Ticket band distributions only; no cost/notice/campaign fields anywhere in the data |
| `phones.csv` | 5,719 | `phone_id`, `account_id`, `provenance`, type | **`phone_id` is not unique (74 repeats) → join key must be `(account_id, phone_id)`; a naive join inflates to 52,367 rows** |
| `dial_attempts.csv` | 51,105 | `attempt_ts`, `attempt_seq`, `network_response`, `disposition` (16 values), `dialling_arm`, `prev_dead` | **Excluded post-dial columns** (durations, `disposition`) from features — leakage to AUC 0.933; **`dialling_arm` randomisation is not clean** (2,277 vs 123; skewed DPD; propensity ≡1.0) → benchmark the incumbent, never claim uplift |
| `skip_traces.csv` | 766 | cost (mean ₹104), trigger, result | Trigger is a constant → EVSI rule only |
| `payments.csv` | 2,162 | amount, date, account | No campaign id → correlation only |
| `field_visits.csv` | 5,578 (1,477 addresses) | `outcome` (1400 not_traceable / 1249 locked / 1114 met_borrower / 1062 met_family / 455 shifted / 206 no_such_person / 92 cash-in-remark) | **Cash is free text in `remark` (43/92 parseable)** → treated as a flagged, lossy signal, never a payment record |
| `visit_gps_points.csv` | 160,406 | lat/lng, `accuracy`, timestamp, `visit_id` | Median accuracy 9.8 m; 645 check-ins (11.6%) >500 m from their own trail; FA009 has 162/172 duplicate photo hashes |
| `verified_contact_points.csv` | 250 | point↔account verification | **Created 2026-07-02, after the dial window → evaluation only** |
| `addresses.csv` / `baseline_geocodes.csv` | 3,117 / 2,880 (237 missing) | address, vendor precision | Feeds the PS3 contract; missing geocodes are a first-class case (field task), not an error |
| `splits.csv` | 1,680/360/360 | account-level split | Respected exactly; no cross-split leakage |
| `agents.csv`, `towns.csv`, `localities.csv`, `landmarks_poi.csv` | 30/3/36/240 | agent, town, locality | POI table incomplete and 14/14 names repeat → landmarks are priors only |
| `priority_slot` field | — | **inverted semantics** | Documented and handled explicitly; a silent sign error here would invert the whole plan |

## 20. Feature catalogue, provenance and leakage controls

| Group | Examples | Source | Leakage guard |
|---|---|---|---|
| Point provenance | provenance, type, age, source-event date | `phones` | None (static at issue) |
| Behavioural history | prior RPC rate, answered rate, third-party rate, answer-then-drop | `dial_attempts` ≤ attempt time | **Strict as-of join on `attempt_ts`** |
| Sequence | `attempt_seq`, consecutive dead, days since last contact | `dial_attempts` | As-of |
| Temporal | hour bucket (peak 0.210/0.198/0.198 at 08/09/18 `[DATA]`), weekday, days to month-end | timestamp | Derived, no leakage |
| Relationship | #active points, shared-number flag, household size | `phones` graph | As-of |
| Case | DPD bucket, outstanding, PTP history and breaks | `accounts`, `payments` | As-of |
| Field (PS3) | address confidence band, last visit outcome, integrity status | `field_visits`, PS3 contract | As-of; never future visits |
| **Banned** | `network_response`, call duration, `disposition` as a feature, anything post-attempt | — | Enforced in the feature builder with a test that fails the build if a banned column appears |

**Feature-value evidence:** `prior_rpc` (ΔAUC 0.0894) is worth more than everything except self-relation and hour combined `[DATA]` — the honest reading is that *history beats features* in this dataset, which is why the state machine carries so much of the architecture.

## 21. Interfaces and contracts

### 21.1 SANKET API (internal)

| Endpoint | Purpose | Key fields |
|---|---|---|
| `POST /decide` | Plan for one account | `account_id`, window → `action`, `point_id`, `env`, `env_range`, `rule_trace`, `refusal?` |
| `POST /plan/day` | Day plan under capacity | capacity vector → assignments, shadow prices, refusal summary |
| `GET /refusals?from&to&code` | Refusal ledger | paginated decisions + counterfactual values |
| `POST /outcome` | Event ingestion (idempotent by `event_id`) | event payload |
| `GET /state/{account_id}` | Current belief state + full timeline | for the demo and for supervisors |
| `POST /override` | Supervisor action | reason code (free text required) |

### 21.2 Contract with PS2's own execution layer

The dialer receives `{point_id, action, permitted_window, attempt_ceiling, expiry, rule_trace_id}` — an **action token**, not a bare instruction. An expired token is not executed. This is what makes the gate real rather than advisory.

### 21.3 The PS2 ⇄ PS3 contract (the integration, formalised)

| Direction | Payload | Consumer | Why it exists |
|---|---|---|---|
| PS3 → PS2 | `P(truth within 200 m)` per address, per stratum radius, integrity status | Field-slot EV, visit scheduling | A visit whose location is uncertain has lower expected value; the allocator must know |
| PS2 → PS3 | `visit.completed` (with outcome, dwell, trail reference), `visit.requested` with the value of confirmation | Fusion, promotion, active-learning queue | The visit is PS3's sensor; PS3 must know which addresses are worth visiting first |

This is the only integration between the two systems — deliberately narrow, so neither becomes a dependency of the other's correctness. The integrated product thesis is argued in `SANKET_SUTRA_SYSTEM_ARCHITECTURE_FINAL.md`.

## 22. Storage and schema

```sql
-- Postgres + jsonb events; PostGIS only in production (demo uses the dataset's metric plane)
CREATE TABLE contact_point (point_id text, account_id text, provenance text, type text,
    identity_p numeric, reach_p numeric, dead_streak int, state text,
    attempts_window int, exposure_flag boolean, last_contact_at timestamptz,
    PRIMARY KEY (account_id, point_id));           -- composite key is mandatory (74 duplicate phone_ids)

CREATE TABLE decision (decision_id text PRIMARY KEY, account_id text, point_id text, action text,
    state_hash text, feature_hash text, model_version text, policy_version text,
    env numeric, env_low numeric, env_high numeric, rule_trace jsonb, ts timestamptz);

CREATE TABLE refusal (refusal_id text PRIMARY KEY, account_id text, point_id text, action text,
    reason_code text, reason_text text, counterfactual_value numeric,
    counterfactual_low numeric, counterfactual_high numeric,
    policy_version text, data_snapshot_hash text, ts timestamptz);

CREATE TABLE event_log (event_id text PRIMARY KEY, type text, account_id text, point_id text,
    payload jsonb, ts timestamptz, actor text);     -- append-only; no UPDATE/DELETE grants

CREATE TABLE override (override_id text PRIMARY KEY, decision_id text, supervisor text,
    reason_code text, reason_text text, ts timestamptz);

CREATE TABLE calibration (segment text, metric text, value numeric, nominal numeric, n int, as_of date);
```

**Design notes:** the composite primary key and the append-only grant revocation are the two schema decisions that encode the dataset traps permanently. `decision.env_low/high` makes a point estimate structurally impossible to store — the honesty rule is enforced by the schema, not by convention.

## 23. Training pipeline and evaluation protocol

```text
1. Load splits.csv → account-level train/val/test (1,680/360/360); no account appears twice
2. Build features with strict as-of joins; banned-column test must pass
3. Train LR control + LightGBM; select on val
4. Calibrate on val (isotonic, per segment); evaluate on test
5. Report: AUC, PR-AUC, ECE, top-decile lift, per-segment coverage — plus the leakage AUC as a caution
6. Robustness: drop each feature group in turn; the model must not collapse to leakage-substitutes
7. Policy evaluation: replay the incumbent, the dead-streak rule, the EV rule and the EVSI rule over test events;
   report per-attempt RPC, calls removed, and the refusal count — with the confounded-arm caveat printed on the slide
8. Freeze artefacts: model hash, calibration map, policy version, cost-table version
```

**Artefacts to ship:** `model.txt`, `calibration.json`, `policy.yaml`, `costs.yaml`, `eval_report.json`, `refusals.csv`, plus a script that regenerates all of them.

## 24. Inference pipeline and latency budget

| Path | Latency budget | Design |
|---|---|---|
| Nightly planning | minutes | Batch: state projection → features → scores → gate → EV/EVSI → allocator → plan |
| Real-time point switch (during a call) | <300 ms | Cached state + precomputed scores; only the gate and EV are computed live; no model call |
| Field app | <1 s | Reads the plan and the address confidence band; writes outcomes offline-tolerant with local queueing |
| Failure fallback | immediate | Model unavailable → segment priors; feature service down → last frozen feature snapshot (aged ≤24 h, flagged); gate unavailable → **deny all actions** (fail-closed) |

Fail-closed on the compliance path is deliberate: an unavailable rulebook must never result in ungoverned contact.

## 25. Monitoring, drift and degradation

| Monitor | Threshold → action |
|---|---|
| Refusal rate by code | >2σ shift → review thresholds with compliance; never auto-relax |
| ECE per segment | >0.05 → recalibrate; >0.10 → disable the model's contribution for that segment |
| Coverage (identity intervals) | Below nominal → widen intervals; block disclosure unlock in that stratum |
| Third-party rate | Any rise → freeze the current λ and alert (this is the conduct KPI) |
| Trace hit rate / spend | Hit rate down → EVSI threshold tightens automatically (it is arithmetic) |
| Plan fill rate | <90% of planned actions executed → capacity model is wrong; alert ops |
| Override rate by code | Rising → the rule or threshold is wrong; weekly review |
| Data drift | PSI on key features; a change in provenance mix flagged before scores move |
| Degradation events | Every fallback writes an event; a shift with >5% degraded decisions is reported to the supervisor |

## 26. Explainability and the refusal ledger

Three artifacts, each aimed at a different reader:

1. **Decision card** (analyst): account, point, action, ENV with range, top-3 contributing features, gate path, and the counterfactual runner-up action.
2. **Refusal list** (compliance): reason code, rule citation, decision inputs, counterfactual value with range — queryable by date, code, town, DPD.
3. **Portfolio view** (management): calls made vs refused by reason; rupees recovered per agent-minute; the dead-point and trace-spend savings; shadow prices for each constrained resource.

Explainability rule: **no explanation may introduce a number that is not in the decision record.** Post-hoc narrative that is not in the log is prohibited by design — the brief's "unsupported capability labelled" discipline applied to explanations themselves.

## 27. Failure modes and red-team results

| # | Failure | Detection | Mitigation in the design | Residual risk |
|---|---|---|---|---|
| 1 | Over-suppression of callable points | RPC/calls removed ratio in policy replay | Refuse only at `dead_streak ≥ 3` `[DATA]`; report the counterfactual value of refusals | Medium |
| 2 | Identity posterior drifts after number recycling | Coverage monitor; third-party rate | Daily decay 0.985; disclosure re-lock on any third-party signal | Medium |
| 3 | Cost table wrong by 3× | Sensitivity curve | Publish ranges; every EV shows the band; allocator re-run at ±3× is displayed | High (unavoidable) |
| 4 | Feature leakage reintroduced by a new engineer | Banned-column build test | Test fails the build; leakage AUC printed as a caution in every report | Low |
| 5 | Confounded arm used as a holdout in a slide | Review checklist item | Propensity histogram printed wherever arms appear | Low |
| 6 | Rulebook version skew between services | Version in every decision record | Policy version pinned in the action token; mismatched token rejected | Low |
| 7 | Agents working around refusals | Override reasons | Override rate monitored; systematic overrides escalate design review | Medium |
| 8 | Optimiser pressure-fills capacity | `wait` in the action set; shift reports | Report *both* throughput and contacts-per-recovery | Low |
| 9 | `priority_slot` sign error (dataset trap) | Unit test with a known case | Documented; tested | Low |
| 10 | DPDP/retention conflict in the event log | Privacy review | Log stores references, not raw contact content; recording retention handled elsewhere | Low |

## 28. Compliance and licence traceability

| Item | Status | Where enforced |
|---|---|---|
| RBI Amendment Directions (nine directions; effective 1 Jan 2027): 08:00–19:00, ≥1-day pre-visit notice, ≥6-month bi-directional recording, empanelled agencies, IIBF-certified DRAs, device-locking 30/60 days, ₹250/h compensation | `[VERIFIED]` | PG-01, PG-02, PG-07, PG-08, PG-10 + refusal codes |
| DPDP Rules 2025 (G.S.R. 843(E)) — purpose limitation, minimisation | `[VERIFIED]` | Feature catalogue; point references over raw content |
| TRAI TCCCPR + 12 Feb 2025 amendment (140/1600 series, ₹2 lakh disincentive per violation) | `[VERIFIED]` | PG-11 bot rules; consent state |
| FCC Reassigned Numbers Database (US analogue — referenced, not applicable) | `[VERIFIED]` | Cited as the international practice for the recycling problem |
| Google Maps Platform terms: lat/lng cache ≤30 days, no permanent storage, no training on output | `[VERIFIED]` | PS3 provider layer; **the canonical coordinate must be field-confirmed, not a vendor pin** |
| Nominatim usage policy (1 req/s) · data.gov.in NDSAP (non-commercial) · Criteo Uplift (CC BY-NC-SA) | `[VERIFIED]` | Any auxiliary data use is documented with its licence in the data register |
| Synthetic dataset | Declared synthetic by the README; `landmarks_poi.csv` incomplete; `annotated_ptp_sample.csv` partly mislabelled | Every dataset-derived number is labelled `[DATA]` and no market claim rests on it |
| Market-size and competitor figures | Each carries a source or is absent | No unsourced market claims in this document |

## 29. Build plan — 48 hours, with the cut-line

| Phase | Hours | Deliverable | Acceptance number |
|---|---|---|---|
| P0 | 0–2 | Event log + state projection on real data | Rebuild state from events → identical to direct computation |
| P1 | 2–6 | State machine + transition table | Dead-streak policy replay reproduces **0.1872 vs 0.1762** RPC/call, −12.5% calls `[DATA]` |
| P2 | 6–12 | Features + control + GBM + calibration | Test AUC **0.670** (control 0.604); ECE < 0.05 per segment |
| P3 | 12–16 | Policy gate + refusal ledger | 100% of refusals carry a code, a citation and a counterfactual range |
| P4 | 16–22 | EV + cost table + EVSI on traces | Reproduces ₹104 / 22.8% / 77% waste; refuses ≥X traces with arithmetic shown |
| P5 | 22–30 | Day allocator (greedy) + shadow prices | Plan under 1,000 / 200h / ₹50,000 / 50 slots; every slot's marginal value printed |
| P6 | 30–38 | PS3 contract wiring + field-slot EV | `P(within 200 m)` visibly changes visit ordering |
| P7 | 38–44 | Demo, dashboards, decision cards, replay | Live: a refusal explained, a trace refused, a plan re-optimised after a capacity change |
| P8 | 44–48 | Write-up, red-team pass, freeze | Every claim traceable to `[DATA]` / `[S-nn]` / `[ASSUMPTION]` |

**Cut-line if behind:** P0–P4 ship; P5 degrades to a ranked list with a published budget cap; P6 becomes a static contract document; the refusal ledger is never cut.

**PRODUCTION target (out of 48-h scope):** the same architecture on streaming events with online state projection, a real rulebook service, PostGIS, per-agent capacity, and the MILP in nightly batch. The delta is stated in `ARCHITECTURE_DECISION_LOG_FINAL.md`.

## 30. Evaluation, demo script, and the open risks that would change this design

### 30.1 Metrics table (what the judges should hold us to)

| Claim | Metric | Baseline | Ours | Evidence class |
|---|---|---|---|---|
| Fewer calls, same recovery | RPC per attempt | 0.1762 | **0.1872** (−12.5% calls) | `[DATA]`, test split |
| Right-party precision on the hard segment | third-party rate on reference/employer points | 81–93% | refused or identity-gated | `[DATA]` |
| Trace spend discipline | ₹ wasted / total | **77% (₹61,605)** | refuse-by-arithmetic, ledger-visible | `[DATA]` |
| Ranking quality | test AUC | 0.604 (LR) | 0.670 (GBM), calibrated | `[DATA]` |
| Compliance | prohibited actions executed | unmeasured | 0 by construction + refusal ledger | design |
| Economic discipline | rupees recovered per all-in rupee | unmeasured | computed with published ranges | parameterised |
| Conduct | third-party contact rate | 0.066 (rule arm) | must not rise; λ protects the tail | `[DATA]` |

**An honest note that belongs on the slide:** the dataset's RPC level (16.4% of attempts) is far above the described reality of collections (**FICO: RPC "rarely exceeds 8–10%"** `[VERIFIED]`). It is a *mechanism demo*, not a benchmark. Every percentage above is a comparison *within* the synthetic world.

### 30.2 Demo script (8 minutes)

1. **The incumbent, warts and all** — 51,105 calls, 16 dispositions, a constant trace trigger, ₹79,650 spent, 77% invisible waste.
2. **One account's belief timeline** — a call that reaches a third party, a trace that kills a point, a payment that resets the state; the state object visibly changing.
3. **A refusal with arithmetic** — the system declines a ₹104 trace and a field slot, showing the EVSI computation and the counterfactual range.
4. **The day plan** — capacity changed live (drop the field slots from 50 to 20): shadow price moves, the plan re-orders, the refusal count changes.
5. **The replay** — same events, new policy version; the difference is the argument for 1 Jan 2027 readiness.
6. **The honest slide** — leakage 0.933 vs honest 0.670; the confounded arm; the cost table's ranges; what we refused to claim.

### 30.3 Open risks that would change the design

| Risk | Change it would force |
|---|---|
| Client supplies real cost and capacity tables | Allocator (L6) becomes the centrepiece; MILP replaces greedy |
| Client supplies real ticket bands and product mix | EVSI thresholds move materially; low-ticket books refuse many more traces |
| A clean randomised pilot with campaign attribution | Reopen uplift/bandit — with a real ESS budget |
| Rulebook is published in a different form (state-level or lender-specific) | Rule codes and refusal vocabulary change; architecture unaffected |
| The dataset is not representative of the pilot book | All `[DATA]` acceptance numbers must be re-derived before any pilot claim |
