# PS2 — ARCHITECTURE SELECTION

**Phase 4, File 7 of 13.** The decision, the arithmetic behind it, and the record of what was rejected.

---

## 1. Criteria and weights (as specified in the brief — not re-tuned)

| # | Criterion | Weight | What it means at scoring time |
|---|---|---|---|
| C1 | Official PS alignment | **20%** | Does it satisfy the stated PS2 requirement IDs (R1–R13) directly, not tangentially? |
| C2 | Business value | **15%** | Does it change the real collections workflow (calls, visits, rupees, conduct)? |
| C3 | Technical depth | **15%** | Is there substance a senior engineer would respect — without impersonating research? |
| C4 | Differentiation | **15%** | Would a judge who has seen 40 submissions see this for the first time? |
| C5 | Dataset support | **10%** | Can the audited dataset actually train/validate it, with no invented fields? |
| C6 | Production realism | **10%** | Could this sit inside a BFSI platform without an asterisk? |
| C7 | Hackathon feasibility | **10%** | Buildable and demonstrable in 48 hours, including the failure path? |
| C8 | Explainability | **5%** | Can a decision, a refusal and a probability be defended to an auditor? |

Scores 1–5. Weighted score = Σ (score × weight).

---

## 2. Candidate scores

Architectures from `PS2_ADVANCED_ARCHITECTURE_RESEARCH.md` (A1–A12) and options from `PS2_ARCHITECTURE_OPTIONS.md` (O1–O7) map as: A1/O1 baseline · A2/O2 two-stage · A3 identity graph · A4/O3 state machine · A5 NBA · A6/O2 gate+EV · A7 bandit · A8 C-MDP · A9/O5 EVSI · A10/O4 allocator · A11/O6 risk-sensitive · **A12 hybrid** · O7 causal.

| Candidate | C1 20 | C2 15 | C3 15 | C4 15 | C5 10 | C6 10 | C7 10 | C8 5 | **Weighted** |
|---|---|---|---|---|---|---|---|---|---|
| **A12 Hybrid belief-state + optimization** | 5 | 5 | 5 | 5 | 4 | 5 | 3 | 5 | **4.60** |
| A10 / O4 Portfolio allocator alone | 4 | 5 | 5 | 5 | 3 | 5 | 4 | 4 | 4.35 |
| A6 Constraint + EV alone | 5 | 4 | 3 | 4 | 4 | 5 | 5 | 5 | 4.30 |
| A9 / O5 EVSI alone | 4 | 4 | 4 | 5 | 4 | 4 | 5 | 5 | 4.30 |
| A4 / O3 State machine alone | 5 | 4 | 3 | 4 | 5 | 5 | 5 | 5 | **4.40** |
| A3 Identity graph alone | 4 | 3 | 3 | 4 | 5 | 4 | 3 | 3 | 3.60 |
| A11 / O6 Risk-sensitive alone | 4 | 4 | 4 | 5 | 2 | 4 | 4 | 5 | 3.90 |
| O2 Two-stage propensity + gate | 4 | 3 | 3 | 2 | 5 | 5 | 5 | 4 | 3.75 |
| A2 Two-stage contactability | 4 | 3 | 2 | 2 | 5 | 4 | 5 | 4 | 3.50 |
| O7 Causal / uplift | 3 | 4 | 5 | 4 | 1 | 3 | 3 | 2 | 3.20 |
| A5 NBA argmax | 4 | 3 | 2 | 2 | 2 | 3 | 4 | 3 | 2.85 |
| A8 Constrained MDP | 3 | 4 | 5 | 3 | 1 | 3 | 1 | 1 | 2.90 |
| A1 / O1 Classifier baseline | 3 | 2 | 1 | 1 | 5 | 3 | 5 | 3 | 2.75 |
| A7 Contextual bandit | 3 | 3 | 4 | 3 | 1 | 2 | 1 | 1 | 2.45 |

**Worked example (A12).** `0.20(5) + 0.15(5) + 0.15(5) + 0.15(5) + 0.10(4) + 0.10(5) + 0.10(3) + 0.05(5) = 1.00 + 0.75 + 0.75 + 0.75 + 0.40 + 0.50 + 0.30 + 0.25 = 4.60`.

---

## 3. Decision

### 3.1 The architecture

**A12 — Hybrid belief-state + optimization**, built as **six layers in a fixed order**, with the composition justified below the scores (the top three candidates are within 0.30 and are layers, not rivals).

```text
L0  EVENT LOG (append-only)                     owner: platform        source: dial_attempts, skip_traces, payments, field_visits
L1  STATE ESTIMATION  ContactPointState        owner: point record    update: outcome events + time decay
L2  IDENTITY / EVIDENCE FUSION  P(borrower)    owner: identity service source: provenance, verification, behaviour, graph
L3  PREDICTION  calibrated multi-class          owner: model service   label: disposition (pre-dial features only)
L4  POLICY GATE  rules → permission + refusals  owner: compliance rulebook  output: rule-coded refusals
L5  ECONOMICS  EV → EVSI (trace/verify) → CVaR penalty → cap/claim
L6  ALLOCATION  day-level greedy → MILP under capacity, frequency, notice
L7  EXECUTION + FEEDBACK  dialer/field APIs → outcomes + overrides → back to L0
```

### 3.2 Why layers rather than the single best-scoring option

- The three top candidates (**A12** 4.60, **A4/O3** 4.40, **A10/O4** 4.35) score high on *different criteria*: O3 owns alignment, realism and explainability; O4 owns value, depth and differentiation; A9/O5 owns differentiation at the lowest cost. Selecting any one of them alone loses a criterion where another is strongest, and the brief explicitly asks for a system, not a model.
- The layers are **independently refusable**: if L5's cost table is deemed unapproved, the system runs L0–L4 and still beats the baseline and still produces refusals. That property — graceful degradation to a *smaller honest system* — is why composition is safe here and would not be in a system where the layers are entangled by design.
- Every layer is justified by a measured number from the audited dataset (see §5).

### 3.3 Why the alternatives were rejected (record)

| Rejected | Reason |
|---|---|
| **A7 Contextual bandit** | Propensities are degenerate (≡1.0 on 94.6% of attempts); the random arm is 5.1% of attempts, skewed by DPD/outstanding, and *worse* (RPC 0.134 vs 0.166); reward is not attributable (no campaign id). ESS would be unusable. Learning online by contacting real borrowers is a regulatory exposure. `[DATA]` |
| **A8 Constrained MDP** | The reference deployment consumed ≈$5 M research + ≈$4 M engagement `[S-33]`; our horizon is 3 months of one policy. Retained conceptually: legal rules become states (L1) and action-availability flags (L4) `[S-32]` |
| **O7 Causal / uplift** | The randomisation is not clean enough to license a policy claim; no clean control arm. Retained as a design rule: no incremental-effect claims, plus a documented precondition appendix |
| **A5 NBA argmax** | Argmax without costs and without a `wait` option manufactures pressure to act; Pega's own arbitration weights (P×C×V×L) contain no cost term `[S-20]` |
| **A2 Two-stage contactability** | Subsumed: the dataset supports one multi-class model whose decomposition is reported afterwards. Two models would double the calibration burden for presentation value only |
| **A1 classifier baseline** | Retained as the running control, not as the answer |

### 3.4 The single biggest architectural bet

**That a measured refusal is worth more than a measured prediction.** The evidence: the dead-point rule alone gives +6.2% RPC per call with −12.5% calls `[DATA]`; the EVSI rule touches 77% wasted trace spend `[DATA]`; and no reviewed competitor publishes a refusal ledger. If this bet is wrong, the system still ships L0–L3 and is a competent baseline-plus-state-machine — which is the point of the layering.

---

## 4. Component-level selection (what was chosen for each layer, and what was not)

| Layer | Chosen | Considered and rejected | Why |
|---|---|---|---|
| L1 state | Explicit finite-state machine over 16 dispositions `[DATA]` | Learned hidden state (HMM/RL) | 3 months, one policy, no reward attribution; an auditor can read a state table |
| L2 identity | Provenance priors + behavioural evidence + shared-number edge detection; CV AUC 0.899 / 0.813 / 0.508 baseline `[DATA]` | GNN over the contact graph | The graph's only claim to value is a *refusal* on shared numbers (43.2% of attempts `[DATA]`), which needs edges, not embeddings |
| L3 prediction | Single calibrated GBM, multi-class over dispositions, pre-dial features only | Per-action models; deep sequence model | Test AUC 0.670 honest vs 0.933 leaked `[DATA]`; a sequence model on 51k rows with this label noise is a liability |
| L4 gate | Closed-vocabulary rule codes, refusals logged | Fuzzy/soft compliance scoring | The brief: never put fuzzy logic inside a legal gate. Discipline: rules are binary and auditable |
| L5 economics | EV + EVSI + one-λ CVaR term, all with published ranges | Full CVaR optimisation; dynamic programming | Ranges + sensitivity is honest; a precise CVaR over unmeasured rupee costs is fictional precision |
| L6 allocation | Greedy Lagrangian, upgrade to OR-Tools MILP | RL scheduler | MILP is provably optimal for the stated LP relaxation; RL scheduler would need the data we do not have |
| L7 feedback | Event log + override reasons + refusal ledger | A/B experimentation platform | No experimentation licence; event sourcing gives replay, which is what an auditor actually wants |

---

## 5. Evidence table — every layer against a measured fact

| Layer | Measured fact it exploits | Source |
|---|---|---|
| L1 | 3rd+ consecutive dead: RPC/attempt 0.180 → **0.067**; refusal at 3+ raises pooled RPC/call 0.1762 → 0.1872, −12.5% calls | `[DATA]` |
| L2 | P(borrower) by provenance 1.00 / 0.73 / 0.67 / 0.30 / 0.16 / 0.07; reference+employer = 14% of calls, 81–93% third-party | `[DATA]` |
| L3 | Honest pre-dial AUC 0.670 (GBM) / 0.604 (LR); leakage 0.933; ΔAUC prior_rpc 0.0894 > self-relation 0.0275 > hour 0.0274 | `[DATA]` |
| L4 | No compliance field exists in the data → configuration + refusal log `[GAP]`; requirement R6 is regulatory `[VERIFIED]` | `[DATA]`, Phase-1 |
| L5 | ₹104/trace, 22.8% hit, ₹455/hit, ₹305/RPC, 77% wasted; trace-success model AUC 0.574 vs 0.772 majority | `[DATA]` |
| L6 | Capacity/trace-budget absent → what-if parameters (1,000 / 200 h / ₹50,000 / 50 slots) | `[GAP]` + brief |
| L7 | No campaign id; 60% of payments within 7 days of an RPC (median 3.3 d) → correlation only | `[DATA]` |

---

## 6. Risk register for the selected architecture

| Risk | Severity | Mitigation built into the design |
|---|---|---|
| Cost table challenged as invented | High | Publish as labelled parameters with ranges + one-line sensitivity; every EV shows the range |
| Model AUC modest (0.670) and over-claimed | High | Report honestly, compare to 0.604 LR and to the leaked 0.933 as an explicit anti-pattern |
| State machine too conservative → over-suppression | Medium | Refuse only at 3+ consecutive dead; report the counterfactual "what suppression cost us" |
| Scope creep into seven components | High | BUILD NOW list frozen in `FRONTIER_PS2_PS3_ARCHITECTURES.md`; everything else labelled |
| Judges read "belief state" as jargon | Medium | Demo shows one account's state timeline changing after a call, a trace and a payment |
| Integration with PS3 becomes cosmetic | Medium | Two hard contracts (C1/C2 in File 6) with a named field and a named event |

## 7. What would change this decision

1. A client-supplied **cost and capacity table** → promote L6 to a full MILP as the centrepiece.
2. A **clean randomised pilot with campaign-level attribution** → reopen A7/O7 (bandit/uplift) with a real ESS budget.
3. **Internal complaint-labelled case data** → the conduct predictor (A17) becomes buildable and moves from RESEARCH ONLY.
4. A **target operating point** (e.g. "no more than X% third-party contact") from the client → λ becomes a constraint rather than a penalty.

**Cut-line if the build slips:** L0 L1 L2 L4 L5(EV) sharpen and ship; L3 shrinks to a logistic baseline; L6 degrades to a ranked list with a published budget cap; EVSI ships as a decision rule even if the allocator does not. Under no cut does the submission lose the refusal ledger.
