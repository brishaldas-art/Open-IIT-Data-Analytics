# ARCHITECTURE DECISION LOG (FINAL)

**Phase 4, File 13 of 13.** Every architecture decision taken in Phase 4, with its reason, its evidence, its label, and — critically — **the condition that would reverse it**. Rejections are recorded as decisions.

**Labels:** `BUILD NOW` (48-hour deliverable) · `BUILD IF TIME` (stretch) · `PRODUCTION` (correct at bank scale, out of scope) · `RESEARCH ONLY` (do not build; precondition stated).
**Evidence classes:** `[DATA]` (audited synthetic dataset, regenerate with `dataset_audit.py`) · `[S-nn]` (bibliography) · `[VERIFIED]` (public/official source) · `[INFERENCE]` · `[ASSUMPTION]` · `[GAP]` (data absent).

---

## Part 1 — System-shaping decisions

### ADR-01 · PS2 is a decision system, not a model · `BUILD NOW`
**Context.** The brief rejects `database → preprocessing → LightGBM → API → dashboard`; the reverse-engineering pass found that every serious system (Experian, FICO, Pega, NYS DTF) separates prediction from policy, constraints and allocation `[S-1][S-3][S-16][S-19][S-32]`.
**Decision.** Build SANKET as state → evidence fusion → prediction → gate → economics → allocation → feedback.
**Why not the classifier.** Measured ceiling: honest pre-dial AUC 0.670, logistic 0.604, leaked 0.933 `[DATA]`. A single model cannot express permission, cost, capacity or sequence.
**Reversal condition.** None foreseen; a better model changes one layer, not the shape.

### ADR-02 · Six layers, each independently refusable · `BUILD NOW`
**Context.** Scope risk is the dominant failure mode in a 48-hour build.
**Decision.** L0 event log · L1 state · L2 identity fusion · L3 prediction · L4 gate · L5 economics · L6 allocation · L7 execution/feedback — with a stated cut-line so each layer can ship alone.
**Evidence.** The three top-scoring options in File 7 score highest on *different criteria* (alignment vs value/depth vs differentiation), which is the signature of layers rather than rivals.
**Reversal condition.** If a layer cannot be shown to change a decision, cut it (test applied in ADR-05, ADR-18).

### ADR-03 · Compliance gate constructs the candidate set; it never filters results · `BUILD NOW`
**Context.** Pega: eligibility → applicability → suitability precedes scoring `[S-19]`; TransUnion sells the same as a pre-engagement gate `[S-12]`; RBI Directions make several actions prohibited from 1 Jan 2027 `[VERIFIED]`.
**Decision.** The gate runs **before** the optimiser; prohibited actions never enter the action set.
**Why it matters.** Post-hoc filtering spends capacity on ineligible work and makes the refusal reason approximate; construction makes prohibited actions structurally impossible and the reason exact.
**Reversal condition.** A rule that can only be evaluated after scoring would have to be split into a pre-scoring proxy plus a post-scoring confirmation — document it if it happens.

### ADR-04 · Refusal ledger as a primary product artefact · `BUILD NOW`
**Context.** No reviewed system publishes *why it declined to act*; the brief demands every action have a failure path and every choice a reason.
**Decision.** Every non-action is an event with rule code, inputs, policy version and a **counterfactual value with a range**.
**Reversal condition.** Never — this is the submission's differentiating claim.

### ADR-05 · No contextual bandit · `RESEARCH ONLY`
**Context.** Propensity ≡ 1.0 on 48,339 of 51,105 attempts; the random arm is 2,766 attempts / 123 accounts / 5.1%, skewed by DPD and outstanding, and *worse* than the incumbent (RPC 0.134 vs 0.166) `[DATA]`; logged feedback is biased and incomplete `[S-39]`; every exploration contacts a real borrower.
**Decision.** Do not build policy learning. Log propensity from day one.
**Reversal condition.** A legal pilot with a genuine control arm and campaign-level reward attribution, plus an ESS budget computed *before* the experiment starts.

### ADR-06 · No constrained MDP · `RESEARCH ONLY` (idea absorbed)
**Context.** NYS DTF's deployment drew on ≈$5 M research + ≈$4 M engagement `[S-33]`; our horizon is 3 months of a single policy with no cost data.
**Decision.** Adopt the C-MDP's *representational* ideas only: legal prerequisites as **states** (L1) and per-action availability flags (L4) `[S-32][S-33]`.
**Reversal condition.** Multi-year longitudinal data with cost and capacity, plus a research budget.

### ADR-07 · No uplift / incremental-effect claims · `RESEARCH ONLY`
**Decision.** No ranking by incremental effect; no numeric uplift claim; the preconditions are documented publicly in the submission.
**Evidence.** The randomisation is not clean (5.4%, skewed, propensity degenerate) and payments carry no campaign id (60% within 7 days of an RPC is correlation) `[DATA]`.
**Reversal condition.** Clean randomisation with logged propensities **including control**, and campaign-level attribution.

### ADR-08 · No LLM or agent inside the decision loop · `RESEARCH ONLY`
**Decision.** Deterministic components only. No generation, no agentic autonomy, no fuzzy logic inside legal gates `[S-31]`.
**Reason.** Auditability, latency, cost, and the brief's explicit prohibition of "LLM/agents everywhere".
**Reversal condition.** A document/letter-understanding task with a deterministic fallback and a measured accuracy requirement.

### ADR-09 · Cost table exposed as parameters with published ranges · `BUILD NOW`
**Context.** No cost, notice or campaign column exists anywhere in the dataset `[GAP]`; the only measured price is the trace (₹104 mean, ₹79,650 total) `[DATA]`.
**Decision.** Ship `costs.yaml` with central values, ranges, owners and sources; every EV displays a range; a single-point rupee figure is structurally unstorable (schema in File 9 §22).
**Reversal condition.** The client supplies their cost/capacity tables.

---

## Part 2 — PS2 component decisions

### ADR-10 · Explicit finite-state machine over 16 dispositions · `BUILD NOW`
**Evidence.** RPC/attempt by consecutive dead calls: 0.180 / 0.177 / 0.160 / **0.067** for 0/1/2/3+; points with ≥1 prior dead call are 42.7% of calls and 37.4% of RPCs `[DATA]`. The naive "never call a dead point" rule is *wrong*.
**Decision.** Refuse dialing only at `dead_streak ≥ 3`; pooled RPC/call improves 0.1762 → **0.1872** with −12.5% calls.
**Reversal condition.** A hidden-state or sequence model demonstrably beating the counter on the same split — then it replaces the *derivation*, not the state object.

### ADR-11 · Identity posterior with an interval, provenance-led · `BUILD NOW`
**Evidence.** P(borrower) by provenance: skip_trace 1.00 · kyc 0.73 · borrower_update 0.67 · bureau 0.30 · reference 0.16 · employer 0.07; CV AUC 0.899 (with behaviour) / 0.813 (provenance alone) / 0.508 (majority) `[DATA]`. Reference+employer points are 14% of calls, answer at 0.44–0.46, but are 81–93% third-party.
**Decision.** Separate, calibrated, interval-valued; disclosure unlock requires a threshold *and* coverage support.
**Reversal condition.** A validated identity model on real data with measured coverage per segment.

### ADR-12 · Shared-number edge detection instead of a GNN · `BUILD NOW`
**Evidence.** 43.2% of attempts sit on shared numbers; third-party rate 0.080 (shared) vs 0.061 (unique) `[DATA]`; 74 duplicate `phone_id`s across accounts make naive joins wrong (52,367 inflated rows).
**Decision.** Deterministic graph edges + Fellegi-Sunter weights `[S-44]`; no embeddings.
**Reversal condition.** A graph model whose increment is measurable against the edge flag on real data.

### ADR-13 · Single multi-class prediction model; no per-action models · `BUILD NOW`
**Evidence.** One target (16 dispositions); no channel arms exist in the log; per-action models would triple the calibration burden for presentation value.
**Reversal condition.** A multi-channel log with per-arm outcomes.

### ADR-14 · Pre-dial features only; leakage enforced by a build test · `BUILD NOW`
**Evidence.** Including `network_response`/durations/`disposition` lifts AUC to **0.933** `[DATA]`.
**Decision.** A test fails the build if a banned column appears; the leakage AUC is printed as a caution in every report.
**Reversal condition.** Never — this is a control, not a design preference.

### ADR-15 · EVSI as a first-class primitive for traces and verifications · `BUILD NOW`
**Evidence.** ₹104/trace; 22.8% hit rate; ₹455 per hit; ₹305 per RPC; **77% of ₹79,650 produced nothing**; trace-success is not learnable (CV AUC 0.574 vs 0.772 majority) `[DATA]`; information purchase is standard practice elsewhere `[S-11][S-42][S-61]`.
**Decision.** Buy iff EVSI > price; refuse with arithmetic recorded.
**Reversal condition.** Client-supplied trace pricing/contracts that change the arithmetic — the *rule* stays.

### ADR-16 · Conduct-tail penalty (λ, CVaR-style) on irreversible actions · `BUILD NOW` (simple form) / `PRODUCTION` (full CVaR)
**Evidence.** Optimising RPC naively raised third-party contact 0.066 → 0.121 on the randomised subset `[DATA]`; CVaR is standard in other domains `[S-43]`; no reviewed collections vendor prices this `[INFERENCE]`.
**Decision.** `score = ENV − λ·Risk`, with λ published, `λ_visit > λ_dial`, and risk-only refusals reported separately from rule-refusals.
**Reversal condition.** A client-specified conduct target converts λ into a hard constraint.

### ADR-17 · Day-level capacity allocator: greedy first, MILP if time · `BUILD IF TIME`
**Evidence.** Experian's constraint-based optimisation `[S-3]`, FICO's solver `[S-16]`, mTSP routing in the 2026 framework `[S-31]`; capacity data absent `[GAP]` → what-if parameters (1,000 / 200 h / ₹50,000 / 50 slots).
**Decision.** Greedy with Lagrangian prices by default; MILP as stretch; `wait` always in the action set.
**Reversal condition.** Real capacity data → MILP becomes the default.

### ADR-18 · Override reasons as the highest-value training signal · `BUILD NOW`
**Evidence.** Pega keeps the CSR in control `[S-21]`; NYS routes non-standard states to specialised units `[S-33]`.
**Decision.** Every override is an event with a mandatory reason; reviewed weekly; systematic overrides trigger a rule/threshold review.
**Reversal condition.** None.

### ADR-19 · Fallback policy: fail closed on compliance, fail open on economics · `BUILD NOW`
**Decision.** Gate unavailable → deny all actions. Model unavailable → segment priors. Feature service down → frozen snapshot (≤24 h, flagged). All degradations are events.
**Reason.** An ungoverned contact is a regulatory event; a sub-optimal contact within the rules is not.
**Reversal condition.** None.

---

## Part 3 — PS3 component decisions

### ADR-20 · Ship calibrated truth before any accuracy improvement · `BUILD NOW`
**Evidence.** Baseline median error 376.4 m, p90 839 m, 9% <100 m; stratum medians rooftop 37.7 / street 134.9 / locality 367.4 / pincode **1,336.5** m, reproduced on a second independent sample (25.6 / 108.6 / 385.9 / 1,375.8) `[DATA]`.
**Decision.** The vendor `precision` label becomes the stratum key; radii and `P(within 200 m)` are published per stratum × town.
**Reversal condition.** A vendor change to the taxonomy (then the mapping is re-derived, not the principle).

### ADR-21 · Field evidence is the accuracy engine · `BUILD NOW`
**Evidence.** Same addresses: vendor 385 m → **29 m** median on met-someone visits; 87% improve; 82% under 100 m `[DATA]`. GPS: median 26 points/visit, median accuracy 9.8 m.
**Decision.** Fusion on stationary clusters with dwell and outcome weighting.
**Reversal condition.** Real-world GPS proving materially worse — then the radius widens and PS2 spends fewer slots; the architecture does not change.

### ADR-22 · No accuracy claim from free public data · `BUILD NOW` (as a refusal)
**Evidence.** Oracle over candidate sets built from free text: 370 m median, 2% <100 m; naive landmark snap 4,093 m (worse in 90%) `[DATA]`.
**Decision.** Retrieval/ranking ships as hygiene + abstention, never as an accuracy story. The number 370 m is stated on the slide.
**Reversal condition.** A licensed address corpus that changes the ceiling.

### ADR-23 · Integrity gate before fusion; negative outcomes never move a point · `BUILD NOW`
**Evidence.** `address_not_traceable` check-ins sit 1,603 m from truth and 195 m from the pin with 2-minute dwell; 645 check-ins (11.6%) are >500 m from their own trail; FA009 has 162/172 duplicate photo hashes (26.6% vs ≤1% elsewhere) `[DATA]`; spoofing is caught by cross-signal inconsistency `[S-58]`.
**Decision.** Gate → then fuse; rejections are events with codes; per-agent pass-rate monitoring.
**Reversal condition.** Device telemetry enabling a scored integrity model (PRODUCTION upgrade).

### ADR-24 · Two-confirmation promotion; contradictions revoke · `BUILD NOW`
**Evidence.** Auto-update after two confirmations in logistics `[S-56]`; single-visit overwrite is how a bad pin becomes permanent.
**Decision.** Promotion requires two independent, integrity-passing confirmations; downstream consumers are notified of revocations.
**Reversal condition.** None.

### ADR-25 · Conformal radii and published coverage · `BUILD NOW`
**Evidence.** Conformal spatial prediction: 93.67% empirical coverage at 90% nominal vs 68.33% bootstrap `[S-53]`; our survey sample is 100 points → stratified, not per-address.
**Decision.** Empirical quantiles + split conformal; the coverage monitor is a shipped artefact; a gap is published, never hidden by widening.
**Reversal condition.** A much larger labelled set (per-address intervals become defensible).

### ADR-26 · No HMM map matching; stop detection instead · `RESEARCH ONLY`
**Evidence.** No road graph in the data (local metric plane, no polygons) `[DATA]`; the standard method requires a segment graph `[S-54]`.
**Decision.** Stationary-cluster stop detection now; HMM as a labelled PRODUCTION/RESEARCH item with the precondition (OSM extract).
**Reversal condition.** Road-network extract for the three towns.

### ADR-27 · Hierarchy adopted as an output contract, not as a model · `RESEARCH ONLY` (model) / `BUILD NOW` (contract)
**Evidence.** GeoIndia: >50% mean / >85% p99 error reduction, 29 state models, 67M addresses `[S-47bis]`; not reproducible here.
**Decision.** Report stratum + radius (our hierarchy); do not train a cell-prediction model on 3,117 addresses.
**Reversal condition.** ≥10k labelled addresses and a hierarchy gazetteer.

### ADR-28 · Canonical coordinate is ours; vendor results are ≤30-day priors · `PRODUCTION` (with `BUILD NOW` logging)
**Evidence.** Google Maps Platform terms: lat/lng cache ≤30 days, no permanent storage of other content, no training on output `[S-48]`; Nominatim 1 req/s `[S-51]`; NDSAP non-commercial `[S-65]`.
**Decision.** Provider abstraction + audit log; canonical store fed only by promotion.
**Reversal condition.** A provider contract that permits permanent storage (then the constraint relaxes, the architecture does not).

---

## Part 4 — Integration decisions

### ADR-29 · Exactly two cross-system contracts · `BUILD NOW`
**Decision.** PS3 → PS2: `P(truth within r)`, stratum radius, integrity status, promotion events. PS2 → PS3: `visit.completed` with outcome/dwell/trail, `visit.requested` with the value of confirmation. Nothing else crosses.
**Reason.** Narrow contracts keep the two systems independently testable and prevent the integrated file from being "two boxes joined".
**Reversal condition.** A third genuine need — which must be named and justified before it is added.

### ADR-30 · Shared event vocabulary across both systems · `BUILD NOW`
**Decision.** `call.completed`, `trace.returned`, `payment.received`, `visit.completed`, `visit.rejected_integrity`, `coordinate.promoted`, `coordinate.revoked`, `refusal.recorded`, `override.recorded`, `policy.versioned`.
**Reason.** One log, two views — the mechanism that makes the integrated product coherent and replayable `[S-59]`.
**Reversal condition.** None.

### ADR-31 · The joint decision is *which uncertainty to buy down* · `BUILD NOW`
**Context.** A trace buys identity information (₹104); a visit buys identity *and* location information (≈₹180) and is irreversible.
**Decision.** Both are priced by the same EVSI logic inside PS2's allocator, with PS3 supplying the location term. A visit is chosen over a trace when the joint information gain per rupee is higher **and** the location confidence is good enough to make the visit likely to succeed.
**Reason.** This is the one decision that neither system can make alone — the integration thesis (File 11).
**Reversal condition.** Field costs or trace hit rates changing materially.

---

## Part 5 — Rejected alternatives, consolidated

| Rejected | Label | Reason (evidence) |
|---|---|---|
| Contextual bandit / online policy learning | RESEARCH ONLY | Degenerate propensities; confounded 5.4% arm; no reward attribution `[DATA][S-39]` |
| Constrained MDP over the full journey | RESEARCH ONLY | 3-month horizon; reference deployment cost `[S-33]` |
| Uplift / incremental-value ranking | RESEARCH ONLY | No clean control arm `[DATA]` |
| GNN identity model | Rejected (superseded) | Edge flag captures the decision value at a fraction of the cost `[DATA]` |
| Sequence/deep model for dispositions | Rejected | Label noise, short horizon, modest honest AUC `[DATA]` |
| Per-action outcome models | Rejected | No arms to learn from `[DATA]` |
| Fuzzy inference in legal gates | Rejected outright | The brief + auditability `[S-31]` |
| Landmark-based auto-correction | Rejected on measurement | 4,093 m median, worse in 90% `[DATA]` |
| Learned candidate ranker as a claim | Rejected | Oracle ceiling 370 m; 100 labels `[DATA]` |
| HMM map matching | RESEARCH ONLY | No road graph `[DATA][S-54]` |
| Hierarchical cell model | RESEARCH ONLY | Proprietary corpus; 3,117 addresses `[S-47bis]` |
| Continuous-grid probabilistic map product | Rejected (substance kept) | Fictional precision; unreadable to a field officer |
| Multi-vendor consensus as core | Rejected (optional) | Cost + licence burden; accuracy gain unsupported `[INFERENCE]` |
| AI voice bot | Rejected | Out of scope; effective cost 2–4× headline `[VAI-ECON]` |
| Complaint-risk predictor | RESEARCH ONLY | No case-level complaint labels |
| Fairness-constrained allocation | RESEARCH ONLY | No agreed fairness metric from the client |
| Measuring spoof-detection rate | Rejected as a claim | No device telemetry to measure recall `[GAP]` |
| Market-share / market-size claims | Rejected outright | No credible public source; brief forbids invented statistics |

---

## Part 6 — Decision-trail summary

| Class | Count | Decisions |
|---|---|---|
| `BUILD NOW` | 24 | ADR-01,02,03,04,09,10,11,12,13,14,15,16(simple),18,19,20,21,22,23,24,25,29,30,31 + the PS3 provider audit logging |
| `BUILD IF TIME` | 2 | ADR-17 (MILP), learned-ranker experiment |
| `PRODUCTION` | 4 | ADR-16 (full CVaR), ADR-26 (HMM once a graph exists), ADR-28, scored integrity model |
| `RESEARCH ONLY` | 8 | ADR-05,06,07,08,26,27(model), plus complaint-risk and fairness items |
| Rejected alternatives | 18 | Part 5 |

**The three decisions that carry the submission:** the refusal ledger (ADR-04), EVSI as a purchase rule (ADR-15), and field evidence with an integrity gate as PS3's accuracy engine (ADR-21 + ADR-23). Every other entry either supports one of these, or is a documented refusal.

**How to challenge this log.** Each ADR states a reversal condition. A reviewer who can produce that condition — a clean pilot, a road graph, a cost table, a labelled corpus — has the exact list of what to reopen.
