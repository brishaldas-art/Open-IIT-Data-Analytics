# PS2 — ADVANCED ARCHITECTURE RESEARCH

**Phase 4, File 2 of 13.** Twelve genuinely different architectures for PS2, compared before any is chosen.

**Inputs to this comparison:** `PS2_ARCHITECTURE_REQUIREMENTS.md` (R1.1–R13.2), `PS2_PS3_DATASET_REVIEW.md` (every number below tagged `[DATA]` is from the audited synthetic dataset), `SIMILAR_SYSTEMS_REVERSE_ENGINEERING.md` (patterns `[S-nn]`), and the Phase-1 research.

**Ground rules used throughout.**
- A "probability" without a calibration and evaluation strategy is not an architecture, it is a wish. Every option below states its calibration plan.
- Every option must survive the dataset traps: leakage, the non-unique `phone_id`, the degenerate propensity (1.0 on 94.6% of attempts `[DATA]`), the 5.4% confounded random arm `[DATA]`, and the absent cost table.
- Feasibility is judged for a **48-hour hackathon build** and for **production**, separately, because they are different questions.

---

## 0. The ten architectures we could actually build, and one we must stop calling an architecture

| ID | Architecture | One-line thesis | Verdict class |
|---|---|---|---|
| **A1** | Classifier | Score each attempt/point, threshold it, rank | Baseline to beat — not an architecture |
| **A2** | Two-stage contactability | Stage 1 "will anyone answer", stage 2 "is it the borrower" | Useful simplification of A1 |
| **A3** | Identity graph | Represent borrower⇄phone⇄address⇄shared-with as a graph; score nodes/edges | Strong for *refusal*, weak for *uplift* |
| **A4** | State machine | Model each point as explicit states (fresh / reachable / verified-borrower / wrong-party / stale-dead) with transitions | Strong, cheap, explainable |
| **A5** | Next-best-action | Score and rank all actions per account, take argmax | Good framing, incomplete economics |
| **A6** | Constraint + optimizer | Rules floor + per-account EV, then allocate a *day's capacity* under constraints | The serious option |
| **A7** | Contextual bandit | Learn the policy online from realised rewards | Not supportable here (no exploration, no reward attribution) |
| **A8** | Constrained MDP | Optimise long-run return over sequences of actions under constraints | Research-only at our scale |
| **A9** | EVSI / information acquisition | Treat traces and verifications as *purchases of information* with a price and a value | The missing primitive — high value, low cost |
| **A10** | Portfolio-level optimizer | Solve the day as one MILP/LP: maximise expected net recovery subject to capacity, frequency, compliance | The production end-state |
| **A11** | Risk-sensitive optimizer | Same as A10, but with a downside penalty (CVaR-style) on conduct/uncertainty tails | A *modifier* that becomes a differentiator for irreversible actions |
| **A12** | Hybrid belief-state + optimization | Per-point belief state (event-sourced) → policy gate → EV/EVSI → constrained allocator → feedback | **Recommended** (see `PS2_ARCHITECTURE_SELECTION.md`) |

---

## A1. Classifier architecture

```
accounts + phones + attempt history ──► feature builder ──► GBM ──► P(RPC) ──► threshold ──► call list
```

| Attribute | Assessment |
|---|---|
| **Data requirements** | Account row + point row + attempt history. Everything in `accounts.csv`, `phones.csv`, `dial_attempts.csv` |
| **Complexity** | Low |
| **Training requirements** | ~51k labelled attempts `[DATA]`; supplied split; hours |
| **Cold start** | Trains fine on day one; a new *portfolio* has no history, but account features transfer |
| **Interpretability** | Medium (SHAP-style attributions; not a decision rule) |
| **Production realism** | This is what most deployed models are `[INFERENCE]`. It is not what the serious platforms sell `[S-3][S-16]` |
| **Hackathon feasibility** | Trivial |
| **Differentiation** | **Zero.** Every team will ship this |
| **Calibration plan** | Isotonic per segment; ECE monitored |
| **Failure modes** | (1) Leakage: adding `talk_duration_s` lifts test AUC 0.670 → **0.933** `[DATA]` — a beautiful number that means nothing. (2) Optimising RPC raises third-party contact (random arm: RPC 0.134 but third-party 0.121 vs 0.066 `[DATA]`). (3) No cost model, so "top decile" ≠ "best decile". (4) Threshold chosen once and never revisited |
| **What real systems use this?** | Only as a *component* inside a strategy `[S-16]` |

**Verdict.** Keep as the honest baseline (a model that must be beaten), never as the architecture.

---

## A2. Two-stage contactability architecture

```text
stage 1: P(answered)  ← network/time/point history
stage 2: P(borrower | answered) ← provenance, relation, verification, behaviour
          ──► combine multiplicatively ──► rank points per account
```

| Attribute | Assessment |
|---|---|
| **Data requirements** | Same as A1; the dataset already separates the two signals (`network_response` vs `disposition`) `[DATA]` |
| **Complexity** | Low–medium; two models, one join |
| **Training requirements** | Two labels; the dataset's funnel makes them clean: answered = 26.0%, RPC|answered = 63.0% `[DATA]` |
| **Cold start** | Stage 1 needs some history; stage 2 can start on provenance priors alone (`skip_trace` 1.00, `kyc_origination` 0.73, `bureau` 0.30, `reference` 0.16, `employer` 0.07 P(borrower) `[DATA]` — n is small, treat as priors) |
| **Interpretability** | **High** — the decomposition is exactly how a collections manager reasons ("it rings, but is it him?") |
| **Production realism** | High; matches TransUnion's separation of *contactability* from *correct consumer* `[S-11][S-12]` |
| **Hackathon feasibility** | Easy |
| **Differentiation** | Low–medium (the decomposition is standard in the industry) |
| **Calibration plan** | Calibrate both stages separately; the product is only as calibrated as its weaker stage; monitor ECE per stage |
| **Failure modes** | Multiplication of two miscalibrated probabilities compounds error; **the two stages have different drifts** (network coverage vs identity churn) so retraining schedules differ |
| **Verdict** | Useful as an *explanatory decomposition*, unnecessary as a *training* structure. The dataset shows both signals come from the same event history |

---

## A3. Identity graph architecture

```text
         ┌──────────┐   used_by    ┌────────────┐
         │ Borrower │◄────────────►│  Phone P1  │──shared_with──► Borrower B
         │    A     │              └─────┬──────┘
         └────┬─────┘                    │ observed_outcome
              │ verified_at              ▼
        ┌─────▼──────┐            ┌──────────────┐
        │ Address A  │            │ ContactEvent │
        └────────────┘            └──────────────┘
```

| Attribute | Assessment |
|---|---|
| **Data requirements** | `phones` (5,719 rows, 5,618 ids, **74 repeat phone_ids across accounts** `[DATA]`), `verified_contact_points`, `field_visits` |
| **Complexity** | Medium (entity resolution + propagation) |
| **Training requirements** | None required for the core: Splink-style Fellegi-Sunter gives explainable match weights with **no labels** `[S-44]` |
| **Cold start** | Good — priors come from provenance and relation, both present at onboarding |
| **Interpretability** | High per edge (each match weight decomposes into per-field contributions `[S-44]`); low if a GNN is used |
| **Production realism** | High as an *internal* capability; TransUnion's entire contact business is this, at 100B+ records `[S-11]` |
| **Hackathon feasibility** | Medium — Splink on 3k accounts is minutes, but the graph must then *change a decision*, or it is decoration |
| **Differentiation** | Medium–high **for refusal**: "this number is shared by 6 accounts; a disclosure here is a third-party exposure" is a refusal no ranking model can produce `[DATA: 43.2% of attempts are on shared numbers; third-party rate 0.080 vs 0.061]` |
| **Calibration plan** | Edge scores are probabilities by construction (FS model); validate on the 250 verified points |
| **Failure modes** | (1) Over-linking (two borrowers, one family number → spurious "shared"). (2) Under-linking (same person, spelling variants). (3) **A graph with no policy attached is a dashboard** |
| **What real systems use this?** | TransUnion (people⇄assets⇄businesses `[S-10]`); Pega/TU both treat household/relationship context as features |
| **Verdict** | **Adopt as the identity layer, not as the whole system.** It answers "may I?" better than "whom should I call first?" |

---

## A4. State-machine architecture

```text
FRESH ──call──► NO_ANSWER ──call──► NO_ANSWER_2 ──call──► DEAD_3 (refuse further dials)
   │              │                     │                    ▲
   │              └──answer──► UNKNOWN_PARTY ──verify──► WRONG_PARTY (refuse)
   │                              │
   └──answer──► RIGHT_PARTY ──payment──► ENGAGED ──(no payment 30d)──► COLD
```

| Attribute | Assessment |
|---|---|
| **Data requirements** | Attempt history + dispositions only. Fully supported `[DATA]` |
| **Complexity** | Low (a transition table + counters) |
| **Training requirements** | None. Thresholds are tuned from observed rates |
| **Cold start** | Works immediately; a new point starts in `FRESH` |
| **Interpretability** | **Highest of all options** — the state name *is* the explanation, and it can be shown to an agent or a regulator |
| **Production realism** | Very high; the NYS DTF system encodes legal prerequisites as states `[S-32]`, and skip-trace patents encode a queue with memory `[S-60]` |
| **Hackathon feasibility** | Trivial. **The dataset gives a measured payoff:** refusing the 3rd+ consecutive dead call to the same point keeps RPC/call at 0.1872 vs 0.1762 (test split) while removing 12.5% of calls `[DATA]` |
| **Differentiation** | Medium — but it *earns the right to say "we refuse"* on day one |
| **Calibration plan** | Not a probabilistic component; requires **transition-rate monitoring** instead (state distribution drift) |
| **Failure modes** | (1) **Blanket dead-point suppression destroys value**: points with ≥1 prior dead call are 42.7% of calls but 37.4% of RPCs `[DATA]` — only the *third consecutive* dead outcome collapses (18.0% → 6.7%). (2) States can thrash if not debounced. (3) States encode policy, so a policy change means a state change |
| **Verdict** | **Adopt as the deterministic skeleton.** Cheap, explainable, and it is where the honest money is |

---

## A5. Next-best-action (argmax over actions)

```text
for each account: score every action a ∈ {call p1, call p2, sms, visit, wait} ─► argmax ─► execute
```

| Attribute | Assessment |
|---|---|
| **Data requirements** | Needs *action-level* labels: which action produced which outcome. Our log is call-only (51,105 calls, 3,761 bot) `[DATA]`; there are no SMS/e-mail arms |
| **Complexity** | Medium |
| **Training requirements** | Per-action outcome models → the "more models" trap; the dataset supports **one** multi-class target (16 dispositions `[DATA]`) |
| **Cold start** | Poor for actions never taken — no counterfactual evidence exists |
| **Interpretability** | Medium |
| **Production realism** | This is Pega's core framing `[S-19]`, and the phrase is used by Experian and Credgenics `[S-1][S-26]` |
| **Hackathon feasibility** | Easy to fake, hard to do honestly |
| **Differentiation** | Low — "NBA" is the most over-used term in the brief |
| **Calibration plan** | Per-action calibration; without overlap between actions the comparison is unsupported |
| **Failure modes** | (1) **Argmax with no cost model**: Pega's own arbitration is a weighted product with no cost term `[S-20]` — good for marketing, wrong for agent minutes. (2) Selection bias: only the actions the old policy tried have data `[S-39]` |
| **Verdict** | Keep the *framing* ("which action, now"), drop the argmax |

---

## A6. Constraint + optimizer (per-account EV, day-level allocation)

```text
eligibility gate (hard rules)  ──►  EV per surviving action  ──►  allocate under capacity  ──►  execute
        ▲                                    ▲                            ▲
   closed-vocab rule codes        cost table (parameters)      agent-hours, slots, budget,
                                                               frequency ceilings, DNC
```

| Attribute | Assessment |
|---|---|
| **Data requirements** | Outcomes `[DATA: yes]` + **costs `[DATA: GAP — no cost column anywhere]`** + capacity `[GAP]` |
| **Complexity** | Medium |
| **Training requirements** | One outcome model + a cost parameter table. No RL |
| **Cold start** | Good: EV with wide priors still ranks sensibly; constraints apply from day one |
| **Interpretability** | High: a decision is a rule code + an expected value + a cost |
| **Production realism** | **This is exactly what Experian Optimize, FICO's solver, and NYS DTF do** `[S-3][S-16][S-32]` |
| **Hackathon feasibility** | Medium: gate + EV is hours; allocation can start as a greedy with Lagrangian prices |
| **Differentiation** | High — almost no hackathon team will subtract costs and enforce capacity |
| **Calibration plan** | Calibrate P(success) per segment; **the EV is only as trustworthy as the cost table**, so costs are published with ranges (R5.2) |
| **Failure modes** | (1) Garbage costs → confident nonsense; mitigate by ranges + sensitivity. (2) Capacity model that doesn't match reality (no shift data) → treat as a policy lever. (3) `wait` omitted → the optimiser invents pressure to call |
| **Verdict** | **Adopt.** This is the spine of the recommended architecture |

---

## A7. Contextual bandit

```text
context x ─► policy π(a|x) ─► action ─► reward r ─► policy update
```

| Attribute | Assessment |
|---|---|
| **Data requirements** | Randomised exploration with logged propensities across arms |
| **What the dataset actually offers** | A randomised arm on **123 of 2,400 accounts (5.1%)**, whose propensities are real (0.25–1.0) while the other 48,339 attempts are degenerate at 1.0 `[DATA]`; **and the random arm performs worse than the incumbent** (RPC 0.134 vs 0.166) `[DATA]`. ESS would be tiny |
| **Complexity** | High (policy learning + safe exploration + reward definition) |
| **Training requirements** | Thousands of randomised, reward-attributed decisions — we have ~2.8k and no reward attribution (60% of payments follow an RPC within 7 d, but **no campaign id** `[DATA]`) |
| **Cold start** | Poor |
| **Interpretability** | Low |
| **Production realism** | Real in ads/recsys; in collections it collides with regulation — every exploration is a real contact to a real borrower `[VERIFIED, S-28 guardrails]` |
| **Hackathon feasibility** | Offline bandit simulation only |
| **Differentiation** | Low and risky: it invites the "you experimented on vulnerable people" question |
| **Failure modes** | (1) Reward = payment without incrementality → learning to call people who would have paid anyway (self-cure). (2) Non-stationarity. (3) Compliance cannot be an arm |
| **Verdict** | **RESEARCH ONLY.** Document why, and note that the honest version is "reallocate attempts already planned" (R5.5), not "explore on borrowers" |

---

## A8. Constrained MDP

| Attribute | Assessment |
|---|---|
| **Data requirements** | Long sequences of state-action-reward with legal states (warrant → levy) `[S-32]`, and a reward over the *full* horizon |
| **What we have** | 3 months, 51,105 calls, 2,166 payments, no action for most outcomes, no cost, no randomisation `[DATA]` |
| **Complexity** | Very high; the NYS DTF equivalent took ≈$5 M of research plus ≈$4 M of engagement `[S-33]` |
| **Cold start / interpretability** | Poor / low |
| **Production realism** | Proven in one government deployment `[S-34]`, and in a 2025 design-science prototype with temporal-logic constraints `[S-36]` |
| **Hackathon feasibility** | None in the honest form |
| **Failure modes** | Estimating a value function from 3 months of one policy: guaranteed overfitting; the paper's own constraints were "handcrafted into the optimization process" without a specification language `[S-36]` |
| **Verdict** | **RESEARCH ONLY.** The *idea* we adopt instead: legal prerequisites as **states** (A4) and **action-availability flags** (A6) |

---

## A9. EVSI / information-acquisition architecture

```text
                    ┌──────────────── trace (₹104) ──────────────┐
decision: act now ──┤                                            ├──► act on better information,
                    └──────────────── verify (₹?) ───────────────┘    or refuse to buy at all
             EVSI = E[best decision after info] − E[best decision now]
             buy iff EVSI > price,  and report the refusal when EVSI ≤ price
```

| Attribute | Assessment |
|---|---|
| **Data requirements** | Price (present: trace cost ₹60–150, mean ₹104 `[DATA]`), the base rate of information (present: 22.8% of traces find something `[DATA]`), and a value for the decision that changes |
| **Complexity** | **Low** — a two-branch decision rule, no training |
| **Training requirements** | None. And that is the finding: predicting trace success gives CV AUC **0.574** vs majority **0.772** `[DATA]` — there is no model to build |
| **Cold start** | Immediate |
| **Interpretability** | Very high: "this trace was not bought because it would have to beat ₹104 and our measured hit rate is 22.8%" |
| **Production realism** | Information purchase is how TransUnion's skip tracing is sold `[S-11]` and how the GE patent's skip queue worked `[S-60]`; VOI is standard decision theory `[S-42]` |
| **Hackathon feasibility** | Easy, and it produces a *refusal*, which is our differentiator |
| **Differentiation** | **High.** Nobody in the market publicly prices traces against a measured hit rate and refuses on the arithmetic |
| **Calibration plan** | Base rate is measured; value of information is an `[ASSUMPTION]` shown as a range |
| **Failure modes** | (1) Value of the outcome unmeasured → EVSI becomes a fiction; mitigate with ranges + one-line sensitivity. (2) Buying information that cannot change the decision — the EVSI definition makes that zero by construction `[S-42]`, which is the point. (3) A constant trigger means no learning about *when*, so EVSI must be evaluated per-decision, not learned |
| **Verdict** | **Adopt as a first-class primitive.** It converts 77% wasted trace spend `[DATA: ₹61,605 of ₹79,650]` into a visible refusal |

---

## A10. Portfolio-level optimizer

```
maximise   Σ_accounts Σ_actions x[a] · ENV[a]      (expected net value)
subject to Σ x[a] ≤ agent_minutes / field_slots / trace_budget      (capacity)
           x[a] = 0 for a ∉ eligible set                            (compliance)
           per-account freq ≤ ceiling; ≥1-day notice before visit    (policy)
           x[a] ∈ {0,1}                                              (integer)
```

| Attribute | Assessment |
|---|---|
| **Data requirements** | ENV per action (A6), capacity (gap), eligibility flags (rules), and a solver |
| **Complexity** | Medium–high; but a *linear* relaxation with a greedy integer repair is ~150 lines |
| **Training requirements** | None beyond A6's model |
| **Cold start** | Works with wide ranges; degrades gracefully to greedy |
| **Interpretability** | High if the LP duals are surfaced as "shadow prices of a field slot / a compliance hour" |
| **Production realism** | Experian's constraint-based optimization `[S-3]`; FICO's solver `[S-16]`; mTSP routing in the 2026 MCDA framework `[S-31]` |
| **Hackathon feasibility** | **Yes** — with 2,400 accounts and ~50 field slots, this is a small MILP; OR-Tools solves it in seconds |
| **Differentiation** | High |
| **Calibration plan** | ENV inputs calibrated as A6; constraints are exact; **the objective is stated explicitly** (per the brief) — net of cost, penalties included |
| **Failure modes** | (1) A clean MILP over fabricated costs looks authoritative — that is the main danger, so costs must be exposed as ranges and the plan shown as sensitivity. (2) Over-constraining → infeasible; always keep a slack action. (3) Capacity data absent → run the model in "what-if capacity" mode |
| **Verdict** | **Adopt at day level, one shift ahead.** Not "the whole bank" — one day's plan |

---

## A11. Risk-sensitive optimizer

```
maximise   Σ ENV − λ · CVaR_α(losses)          where losses include:
             wrong-party contact cost, conduct/complaint tail, wasted field visit,
             and model uncertainty on the specific decision
```

| Attribute | Assessment |
|---|---|
| **Data requirements** | Loss *distribution*, not just a mean. Our data gives rates (third-party 6.9% of calls; 81–93% of reference/employer points verify third-party `[DATA]`) but **no rupee cost** `[UNKNOWN]` |
| **Complexity** | Medium (one extra term; linear-programmable via the Rockafellar–Uryasev formulation `[S-43]`) |
| **Training requirements** | None |
| **Cold start** | Works; the risk weight λ is a disclosed policy parameter |
| **Interpretability** | Very high — "we will not take this action because its worst decile is unacceptable" |
| **Production realism** | Standard in energy/disaster logistics `[S-43]`; **not** publicly described by any collections vendor reviewed `[INFERENCE]` — a real, defensible differentiation |
| **Hackathon feasibility** | Medium — implement as "expected value − λ × (probability of the bad outcome × its cost)", which is a one-line change from A6 |
| **Differentiation** | **High for irreversible actions** (field visit, notice): spend a field slot on a case whose identity *and* location belief are both confident, not merely high-expected-value |
| **Failure modes** | (1) λ tuned by vibes; publish the curve. (2) Double counting the same risk in both EV and CVaR terms. (3) Risk aversion used to justify doing nothing — always report what was **not** done because of it |
| **Verdict** | **Adopt as a modifier on the EV gate, with λ disclosed.** Not as a separate engine |

---

## A12. Hybrid belief-state + optimization *(recommended shape)*

```
EVENT LOG (append-only)  ──►  STATE ESTIMATORS  ──►  PREDICTION  ──►  POLICY GATE  ──►  VALUE/RISK  ──►  ALLOCATION  ──►  EXECUTION
  call outcomes                ContactPointState      one calibrated     hard rules,       EV, EVSI,          day-level          dialer / field app
  trace results                AccountContactState    multi-class        refusals with     CVaR penalty       MILP/LP +          (via their APIs)
  payments                     IdentityGraphState     model (6 classes)  rule codes        with ranges        greedy repair
  visit outcomes                                                                                                    │
        ▲                                                                                                           │
        └───────────────────────────────── outcomes + propensities + override reasons ────────────────────────────────┘
```

| Attribute | Assessment |
|---|---|
| **Data requirements** | Everything in A4+A3+A6+A9+A10+A11 — and all of it is already in the audited dataset except **costs and capacity** `[GAP]` |
| **Complexity** | High as a whole, low per layer: each layer is independently testable and independently *refusable* |
| **Training requirements** | One model (A1's honest version), one entity-resolution pass, zero RL |
| **Cold start** | Each layer has a defined cold-start behaviour (state machine from day one, priors for identity, ranges for costs) |
| **Interpretability** | High end-to-end: belief → rule code → EV → plan |
| **Production realism** | It is the union of what Experian, FICO, NYS DTF and Pega each do separately `[S-3][S-16][S-33][S-20]` |
| **Hackathon feasibility** | **Yes, if scoped:** state machine + gate + EV + EVSI + greedy allocation ≈ a day of build; the MILP is the "if time" layer |
| **Differentiation** | **Highest available** — the refusal record plus priced information plus an uncertain-aware allocation is not something any reviewed system publishes |
| **Calibration plan** | Per-segment isotonic on the one model; coverage-tested probabilities on the identity posterior (relate to PS3's conformal logic `[S-53]`); state transition rates monitored |
| **Failure modes** | (1) Scope creep into 5 models. (2) A layer that does not change a decision — every layer must be justified by a decision that flips. (3) Silent degradation: if the model is unavailable the system must fall back to the state machine and **say so in the record** |
| **Verdict** | **Recommended.** Specification in `PS2_SANKET_SOLUTION_ARCHITECTURE_FINAL.md` |

---

## 16. Ranked comparison (weights from the brief, applied in `PS2_ARCHITECTURE_SELECTION.md`)

| Rank | Architecture | Official PS alignment | Business value | Technical depth | Differentiation | Dataset support | Production realism | Hackathon feasibility | Explainability | **Weighted** |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **A12 Hybrid belief-state + optimization** | 5 | 5 | 5 | 5 | 4 | 5 | 3 | 5 | **4.60** |
| 2 | A10 Portfolio optimizer | 4 | 5 | 5 | 5 | 3 | 5 | 4 | 4 | 4.30 |
| 3 | A6 Constraint + optimizer | 5 | 4 | 3 | 4 | 4 | 5 | 5 | 5 | 4.30 |
| 4 | A9 EVSI / information acquisition | 4 | 4 | 4 | 5 | 4 | 4 | 5 | 5 | 4.20 |
| 5 | A11 Risk-sensitive optimizer | 4 | 4 | 4 | 5 | 2 | 4 | 4 | 5 | 3.85 |
| 6 | A4 State machine | 5 | 3 | 2 | 2 | 5 | 5 | 5 | 5 | 3.90 |
| 7 | A3 Identity graph | 4 | 3 | 3 | 4 | 5 | 4 | 3 | 3 | 3.60 |
| 8 | A2 Two-stage contactability | 4 | 3 | 2 | 2 | 5 | 4 | 5 | 4 | 3.50 |
| 9 | A1 Classifier | 3 | 2 | 1 | 1 | 5 | 3 | 5 | 3 | 2.75 |
| 10 | A5 NBA argmax | 4 | 3 | 2 | 2 | 2 | 3 | 4 | 3 | 2.85 |
| 11 | A7 Contextual bandit | 3 | 3 | 4 | 3 | 1 | 2 | 1 | 1 | 2.45 |
| 12 | A8 Constrained MDP | 3 | 4 | 5 | 3 | 1 | 3 | 1 | 1 | 2.90 |

*(Scores 1–5; weighted = Σ wᵢ·sᵢ with the brief's weights: PS alignment 20%, business value 15%, technical depth 15%, differentiation 15%, dataset support 10%, production realism 10%, hackathon feasibility 10%, explainability 5%. Full arithmetic in the selection file.)*

**Reading the table.** A12 wins because it is the only option whose *layers* each map to a measured fact in our dataset. A10 scores almost as high and is the right "if time" extension. A4 and A6 are the layers that make A12 honest. A7 and A8 are excluded not because they are unsophisticated — they are the most sophisticated — but because the dataset cannot support them and the brief explicitly forbids sophistication we cannot defend.

---

## 17. What each architecture changes in the actual collections workflow

Per the standing rule, every component must answer this. Consolidated:

| Layer | Workflow change | Evidence it is worth it |
|---|---|---|
| State machine (A4) | Stops the 3rd+ dead call to the same point | RPC/call 0.1762 → **0.1872**, −12.5% calls `[DATA]` |
| Identity graph (A3) | Refuses a disclosure on a shared/third-party point | 43.2% of attempts on shared numbers; P(borrower) 0.16–0.07 for reference/employer points `[DATA]` |
| Prediction (A1 inside A12) | Orders points *within* the eligible set; no longer decides who is called | Honest test AUC 0.670; leakage ceiling 0.933 `[DATA]` |
| Policy gate (A6) | Refuses with a rule code; makes third-party disclosure structurally impossible | No dataset field exists → configuration + refusal log (an honest `[GAP]`) |
| EV gate (A6) | Kills actions whose cost exceeds their expected recovery | No cost data → parameter ranges `[GAP]` |
| EVSI (A9) | Stops buying traces whose expected information value is below ₹104 | 77% of trace spend produced nothing `[DATA]` |
| Allocation (A10) | Fills the day's real capacity by value, not by list position | No capacity data → what-if mode `[GAP]` |
| Risk penalty (A11) | Requires *certainty* before an irreversible action | Wrong-party exposure 6.9% → 12.1% under a naive RPC objective `[DATA]` |

**The honest summary of this file:** seven of the twelve architectures die on contact with the dataset or with the brief's own prohibitions. The five that survive are not five competitors — they are five **layers of one system**, and the reason to build them as layers is that each one can be removed without breaking the others.
