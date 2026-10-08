# PS2 — SANKET · right-party contact, identity permission and the priced next action

**Section owner's brief.** Everything that defines, researches, scores or specifies PS2 lives in this folder. If it is not here, it is in `../` — and §5 of this page tells you exactly which shared files matter to PS2 and why.

---

## 1. What PS2 is, in one paragraph

CreditNirvana asks for a system that decides **which contact point to use, whether it is reachable, whether it is the right party, and what the next action should be** — with traces and visits governed by economics rather than by an attempt counter. Our answer (**SANKET**) is a decision system, not a model: a belief state per contact point, identity evidence fused into a calibrated probability, a hard rulebook that produces refusals instead of filtering results, expected value and **EVSI** (buy information only if it can change a decision), a conduct-tail penalty on irreversible actions, and a day-level allocator that spends agent-minutes, trace budget and field slots by value. Prediction is one layer inside it.

**The three artefacts that carry PS2:** the **refusal ledger** (why we declined, with a counterfactual range), the **information-purchase rule** (EVSI against the measured ₹104 trace price), and the **dead-streak discipline** (we call *less* and hit *more*).

---

## 2. Reading order

| # | File | What it is | Status |
|---|---|---|---|
| 1 | `PS2_DEEP_INTERNET_RESEARCH.md` | What PS2 actually is once you check the literature: contact-intelligence landscape, six next-best-action approaches, selection bias, the economics of each action, Indian regulation, competitor capabilities | CURRENT |
| 2 | `PS2_ASSUMPTIONS.md` | PS2 re-read from scratch: the 11 questions (user, consumer, decision, success, CN's gain, risks, constraints, data) + assumption register A1–A25 with compliance citations | CURRENT |
| 3 | `PS2_ARCHITECTURE_REQUIREMENTS.md` | MUST / SHOULD / MAY checklist, each item tied to evidence and to "what it changes in the collection workflow" | CURRENT |
| 4 | `PS2_ADVANCED_ARCHITECTURE_RESEARCH.md` | Twelve genuinely different architectures compared (classifier → two-stage → identity graph → state machine → NBA → constraint optimizer → bandit → constrained MDP → EVSI → portfolio optimizer → risk-sensitive → hybrid), each with data needs, cold start, interpretability, failure modes | **BINDING input** |
| 5 | `PS2_ARCHITECTURE_OPTIONS.md` | Seven buildable options scored, with the evidence table that decides them | **BINDING input** |
| 6 | `PS2_ARCHITECTURE_SELECTION.md` | The weighted decision (PS alignment 20 · business value 15 · technical depth 15 · differentiation 15 · dataset support 10 · production realism 10 · feasibility 10 · explainability 5), the worked arithmetic, the rejected alternatives, the risk register and the cut-line | **BINDING decision** |
| 7 | `PS2_SANKET_SOLUTION_ARCHITECTURE_FINAL.md` | **The architecture we build — 30 sections.** State model with owners/decay/transition table, evidence fusion with intervals, the prediction layer and its leakage guard, calibration table for every probability, closed-vocabulary rulebook, EV + EVSI + CVaR, day allocator with shadow prices, failure path per action, event sourcing, storage schema, monitoring, build plan with acceptance numbers | **BINDING** |
| 8 | `data/derived/derived_ps2_policy_baselines.csv` | The acceptance table: what the incumbent does, what the dead-streak rule does, what a cold-start policy would do | **BINDING baseline** |
| 9 | `PS2_SANKET_SOLUTION_ARCHITECTURE.md` | The Phase-2 hypothesis (25 sections) | **SUPERSEDED** — kept as the reasoning record; file 7 replaces it |

---

## 3. The numbers PS2 stands on (all reproducible)

Run `tools/reproduce.sh p2 eco` — every figure below comes back.

| Fact | Value | Why it matters |
|---|---|---|
| Right-party contact rate | 16.4% of attempts / 63% of answered | The funnel we are ordering |
| **Dead-streak collapse** | RPC/attempt 0.180 → 0.177 → 0.160 → **0.067** for 0/1/2/3+ consecutive dead | Only the *third* consecutive dead call is worth refusing |
| **The waste floor** | Refusing 3rd+ dead: **0.1762 → 0.1872** RPC/call, **−12.5% calls** | Doing less, winning more — the strongest single result in the submission |
| The trap in the same table | 1–2 prior dead calls = **42.7% of all calls and 37.4% of all RPCs** | "Never call a dead point" is **wrong**; only a sequence representation gets this right |
| Honest model ceiling | pre-dial AUC **0.670** (GBM) / 0.604 (LR); feature ΔAUC `prior_rpc` 0.0894 > self-relation 0.0275 > hour 0.0274 | History beats features in this data — which is why the state machine carries the architecture |
| The number never to quote | 0.933 | That is leakage (post-dial fields). It appears only as a caution |
| Provenance → identity | P(borrower): skip_trace 1.00 · kyc 0.73 · borrower_update 0.67 · bureau 0.30 · reference 0.16 · employer 0.07 | Reference/employer points ring (0.44–0.46) and are 81–93% third-party |
| Shared numbers | 43.2% of attempts; third-party 0.080 vs 0.061 | The disclosure risk is measurable, not hypothetical |
| Trace economics | ₹104 mean · 22.8% hit · ₹455 per hit · ₹305 per RPC · **77% of ₹79,650 produced nothing**; trace success CV AUC **0.574** vs 0.772 majority | Not learnable → the deliverable is a *decision rule*, not a model |
| Why the conduct penalty exists | a naive RPC-maximising policy raises third-party contact 0.066 → 0.121 | Optimising the wrong objective is a compliance event |

**Verdict of the selection arithmetic:** the hybrid belief-state + optimization architecture scores 4.60, ahead of the portfolio allocator (4.35) and the state machine (4.40) — but the top three are *layers*, not rivals, so all three ship.

---

## 4. Build scope (frozen)

`BUILD NOW` — event log · state machine with owners and decay · identity fusion with intervals · one calibrated multi-class model (pre-dial features only) · rulebook + refusal ledger · EV with a published cost table · EVSI on traces · greedy day allocator with Lagrangian shadow prices · override-as-event · calibration/coverage monitor.

`BUILD IF TIME` — OR-Tools MILP allocator · off-policy evaluation on the clean 5.4% subset (reported with an ESS caveat) · portfolio digital twin · bot-disposition as an evidence source.

`RESEARCH ONLY, with the precondition recorded` — contextual bandit · full constrained MDP · uplift ranking · sequence/deep models · per-action outcome models · complaint-risk prediction.

---

## 5. What else in this section PS2 leans on (and why)

| File in this section | Why PS2 needs it |
|---|---|
| `PS2_PS3_DATASET_REVIEW.md` §3, §5, §6, §8 | The PS2 evidence, the twelve traps (leakage, the confounded arm, the non-unique `phone_id`, the inverted `priority_slot`, cash in free text) and the requirement-by-requirement verdict |
| `tools/dataset_audit.py` | Regenerates every `[DATA]` number above (`p2`, `eco` sections) |
| `SANKET_SUTRA_SYSTEM_ARCHITECTURE_FINAL.md` | The two contracts with PS3 and the one genuinely joint decision (trace vs visit) |
| `SIMILAR_SYSTEMS_REVERSE_ENGINEERING.md` | Where the patterns came from — Experian/FICO/Pega/TransUnion/NYS tear-downs |
| `ARCHITECTURE_DECISION_LOG_FINAL.md` | The 31 ADRs relevant to PS2 (ADR-01…ADR-19) and their reversal conditions |
| `CN_QUESTIONS.md` | The questions PS2 must ask before any number is trusted (cost table, capacity, ticket band) |
| `PS2_PS3_RED_TEAM.md` | The 36 adversarial questions — PS2's half is the checklist before anyone presents this |

---

## 6. Run it

```bash
cd PS2_SANKET                      # this section; the sibling is the same shape
bash tools/reproduce.sh q p2 eco     # every number below, and rebuilds data/derived/derived_ps2_policy_baselines.csv
bash tools/check_section.sh        # the section's invariants; must print ALL CHECKS PASSED
bash tools/build_package.sh        # this section's zip + the combined zip
```

**Honesty rules that bind this section:** no uplift or incremental-effect claim (the randomised arm is 5.4%, confounded, and *worse* than the incumbent); no single-point rupee figure where the cost inputs are `[ASSUMPTION]`; regulatory rules stay hard, closed-vocabulary and cited; every refusal carries a rule code and a counterfactual range.
