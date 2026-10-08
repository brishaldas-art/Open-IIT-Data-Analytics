# PS2 — ARCHITECTURE OPTIONS

**Phase 4, File 4 of 13.** Seven options that differ in *kind*, not in tuning. Each is complete enough to be built, scored against the brief's criteria, and rejected or carried forward on the record.

**Scoring key (1–5, same for all options):** `Align` = fit to the official PS2 statement and requirement IDs R1–R13 · `Value` = business value in the real collection workflow · `Depth` = technical depth · `Diff` = differentiation from a standard submission · `Data` = support from the audited dataset · `Prod` = production realism · `Feas` = 48-hour feasibility · `Expl` = explainability/auditability.
**Weights (from the brief):** 20 / 15 / 15 / 15 / 10 / 10 / 10 / 5.

---

## O1 — Honest baseline control *(the thing to beat, not the answer)*

**What it is.** Rules for eligibility, one GBM for P(right party), rank by probability, call top-N. No economics, no state, no refusal logic.

**Components.** Feature builder over `dial_attempts` pre-dial fields → LightGBM → isotonic → rank.

**Why it is listed.** The brief says every advanced component must beat a simpler baseline. This *is* that baseline, and it must exist as a running artifact so that every later claim is comparative. Measured: honest pre-dial test AUC **0.604** (logistic) / **0.670** (GBM); the leaked variant reaches 0.933 and is never quoted `[DATA]`.

**What it proves.** Nothing about collections practice. Its job is to occupy the "before" column.

**Scoring.** Align 3 · Value 2 · Depth 1 · Diff 1 · Data 5 · Prod 3 · Feas 5 · Expl 3 → **2.75**

**Fate.** Kept as `baseline/` in the repo, reported in the demo as the control.

---

## O2 — Propensity + identity, gate-shaped *(vendor-shaped production design)*

**What it is.** Mirror the architecture of the commercial platforms: score contactability, score identity/correct-party separately, apply a compliance gate **before** engagement (TransUnion's public description of pre-engagement compliance checks `[S-11][S-12]`), then rank.

```
contactability model ─┐
                      ├─► P(RPC) ─► compliance gate ─► ranked call list
correct-party model ──┘        (DNC, hours, per-day caps, IDs)
```

**Component → data mapping.**
| Component | Data |
|---|---|
| Contactability | `dial_attempts` (answered = 26.0% `[DATA]`), `phones.phone_type`, hour-of-day (peaks 0.210/0.198/0.198 at 08/09/18h `[DATA]`) |
| Correct party | provenance P(borrower): `skip_trace` 1.00, `kyc_origination` 0.73, `borrower_update` 0.67, `bureau` 0.30, `reference` 0.16, `employer` 0.07; CV AUC 0.899 with behaviour `[DATA]` |
| Gate | no dataset field exists → configuration `[GAP]` |
| Ranking | one combined model or product of two |

**What it proves.** That PS2 can be built in the shape the industry actually uses, with the funnel decomposed. **What it cannot prove.** That the ranking is *worth* anything — it still has no cost term and no capacity.

**Risks.** Two models to calibrate; the gate is unmeasured, so its value is asserted as a policy requirement, not demonstrated.

**Scoring.** Align 4 · Value 3 · Depth 3 · Diff 2 · Data 5 · Prod 5 · Feas 5 · Expl 4 → **3.75**

**Fate.** Its two ideas (pre-engagement gate, identity separation) are absorbed into O3/O5 as layers; the standalone build is superseded.

---

## O3 — Belief-state, event-sourced, refusal-first *(SANKET core)*

**What it is.** Every contact point is an object with an explicit **state**, an owner, an update rule, and a half-life. All state changes are events. Actions are only permitted if the state permits them; refusals are first-class records. No economics beyond a held-out cost table.

```
event log ──► state estimator ──► permission (state ⊕ rules) ──► action queue ──► outcomes ──► (back to log)
                    │
             CONTACT_POINT_STATE: FRESH / ANSWERED_UNKNOWN / THIRD_PARTY_CONFIRMED /
             RIGHT_PARTY_REACHED / NO_ANSWER×n / DEAD_3 / DISPUTED / VERIFIED_OTHER
```

**Component → data mapping.**
| Component | Data / rule |
|---|---|
| State derivation | 16 dispositions in `dial_attempts.disposition` `[DATA]` |
| Dead-point rule | refuse only at **3+ consecutive** dead outcomes: RPC/call 0.1762 → **0.1872** with −12.5% calls `[DATA]` |
| Third-party guard | reference/employer points: 0.44–0.46 answer rate but **81–93% third-party** `[DATA]`; shared-number rate 43.2% `[DATA]` |
| Owner / update | each state transition names the event that can move it (call, trace, payment, visit, time decay) |
| Refusal | rule code + timestamp + data snapshot → the audit artifact |

**What it proves.** That refusals can be *calculated*, not asserted — the differentiator the whole submission rests on. **What it cannot prove.** Anything about optimal sequencing; it is deliberately myopic.

**Risks.** Over-suppression (see the dead-point trap: ≥1 prior dead = 42.7% of calls / 37.4% of RPCs); without the economics layer it cannot trade off a refusal against value.

**Scoring.** Align 5 · Value 4 · Depth 3 · Diff 4 · Data 5 · Prod 5 · Feas 5 · Expl 5 → **4.40**

**Fate.** **Adopted as Layer 1–3** of the final architecture.

---

## O4 — Allocation-first *(portfolio MILP day-planner)*

**What it is.** Start from the *scarcest resource* — the day's agent hours, field slots, trace budget — and solve one constrained problem that assigns them to accounts. Everything else (models, rules) is an input.

```
max Σ ENV[a]·x[a]  s.t.  capacity, eligibility, frequency, notice, x binary
```

**Component → data mapping.** ENV needs outcomes (present) × costs (absent → parameter ranges published `[GAP]`); capacity absent → run in what-if mode (1,000 accounts / 200 agent-hours / ₹50,000 trace / 50 field slots, exactly the brief's figures).

**What it proves.** That capacity, not ranking, is the binding constraint — and that budget can be *spent* deterministically instead of drifting. **What it cannot prove.** That the ENV numbers are right; the whole edifice rests on a cost table we must supply as labelled parameters.

**Risks.** Fabricated-looking precision (mitigate: ranges + sensitivity plot); over-constraining to infeasibility (always leave `wait`).

**Scoring.** Align 4 · Value 5 · Depth 5 · Diff 5 · Data 3 · Prod 5 · Feas 4 · Expl 4 → **4.35**

**Fate.** **Adopted as Layer 6**, entered as a greedy with Lagrangian prices, upgraded to OR-Tools MILP if time permits.

---

## O5 — Information-purchase engine *(EVSI-first)*

**What it is.** The primary decision is not "whom to call" but "**what is worth knowing before we call**". Traces, field verification and identity checks are purchases; each is bought only if expected value of sample information exceeds price.

```
prior belief ──► decision under current belief ──► EV0
             ──► hypothetical belief after info ──► EV1
             ──► buy iff (EV1 − EV0) > price
```

**Component → data mapping.**
| Input | Value |
|---|---|
| Price | ₹60–150, mean **₹104/trace**; ₹79,650 total spend `[DATA]` |
| Hit rate | 22.8% of traces yielded information; ₹455 per hit; ₹305 per RPC `[DATA]` |
| Waste | **77% of spend (₹61,605)** produced nothing `[DATA]` |
| Learnability | Predicting trace success: CV AUC **0.574 vs 0.772** majority → **no model**; the decision rule is the deliverable `[DATA]` |

**What it proves.** That the dataset's most expensive public failure can be turned into a visible, arithmetic refusal. **What it cannot prove.** The value of the decision that changes — no campaign/outcome links, so the value side is an `[ASSUMPTION]` with a sensitivity range.

**Risks.** Value fiction; a constant trace trigger means no *when* to learn, so EVSI is evaluated per-decision, never trained.

**Scoring.** Align 4 · Value 4 · Depth 4 · Diff 5 · Data 4 · Prod 4 · Feas 5 · Expl 5 → **4.30**

**Fate.** **Adopted as Layer 5.** The single highest ratio of differentiation to lines of code in PS2.

---

## O6 — Risk-sensitive policy *(CVaR-style conduct tail)*

**What it is.** Optimise expected value **minus a penalty on the bad tail**, where the tail is measured on things the bank actually fears: a third-party disclosure, a wrong-party field visit, a complaint-generating call pattern, and model uncertainty on this specific decision.

```
score = ENV − λ·(P(bad outcome)·cost(bad) + κ·σ_uncertainty)
```

**Why it is a *different* architecture, not a tweak.** It changes *which* actions are admissible: an irreversible action (field visit, notice) is approved only when the belief is *confident*, not merely high-expected-value. On the random arm data this is not academic — optimising RPC naively raised third-party contact from 0.066 to 0.121 `[DATA]`.

**Data.** Rates are measured (third-party 6.9% of attempts overall; 81–93% on reference/employer points `[DATA]`); **rupee costs are `[UNKNOWN]`** — so λ is published and the curve shown. No cited competitor in the reviewed set prices this tail `[INFERENCE]`.

**Risks.** λ by vibes; double counting; using risk aversion to justify doing nothing (mandate: always report what was *not* done and why).

**Scoring.** Align 4 · Value 4 · Depth 4 · Diff 5 · Data 2 · Prod 4 · Feas 4 · Expl 5 → **3.90**

**Fate.** **Adopted as a modifier inside Layer 5/6**, not as a standalone engine.

---

## O7 — Causal / incremental-value design *(uplift on the clean subset)*

**What it is.** Instead of P(RPC), model the **incremental** effect of a contact: who would pay *because* we called, versus who would pay anyway (self-cure). The only defensible instrument is randomised variation.

**Honest data verdict.** The randomisation exists but is unusable in the form available: 2,766 of 51,105 attempts (5.4%) sit on the random arm, 123 of 2,400 accounts, skewed by DPD/outstanding, propensity ≡ 1.0 on the rule arm, and the random arm performs **worse** (RPC 0.134 vs 0.166) `[DATA]`. Effective sample size would be far below what a policy claim needs, and payments have no campaign id (60% within 7 days of an RPC, median 3.3 days, **correlation only** `[DATA]`).

**What a correct build looks like.** Estimate the effect *within* the comparably-randomised subset only, report a confidence interval wide enough to be honest, and state that it cannot license a policy change. Complement: an agent-level propensity check to detect the confounding that is already visible.

**Risks.** Presenting a 5.4% non-random subset as a holdout; the phrase "uplift model" appearing anywhere near a headline number.

**Scoring.** Align 3 · Value 4 · Depth 5 · Diff 4 · Data 1 · Prod 3 · Feas 3 · Expl 2 → **3.20**

**Fate.** **Not built as an engine.** Its constraint becomes a design rule: no claim of incremental effect from this data, and a documented "what a clean experiment would need" appendix (the brief allows an explicit refusal).

---

## Comparison

| | O1 Baseline | O2 Propensity+identity | **O3 Belief-state** | **O4 Allocation-first** | **O5 EVSI** | O6 Risk-sensitive | O7 Causal |
|---|---|---|---|---|---|---|---|
| Align (20) | 3 | 4 | **5** | 4 | 4 | 4 | 3 |
| Value (15) | 2 | 3 | 4 | **5** | 4 | 4 | 4 |
| Depth (15) | 1 | 3 | 3 | **5** | 4 | 4 | 5 |
| Diff (15) | 1 | 2 | 4 | **5** | **5** | **5** | 4 |
| Data (10) | 5 | 5 | **5** | 3 | 4 | 2 | 1 |
| Prod (10) | 3 | 5 | **5** | **5** | 4 | 4 | 3 |
| Feas (10) | 5 | 5 | **5** | 4 | **5** | 4 | 3 |
| Expl (5) | 3 | 4 | **5** | 4 | **5** | **5** | 2 |
| **Weighted** | **2.75** | **3.75** | **4.40** | **4.35** | **4.30** | **3.90** | **3.20** |

**Construction rule for the final architecture.** O3 + O4 + O5 are near-tied at the top and are *not alternatives* — each is the strongest at a different layer (permission, allocation, information). O6 is a modifier on both. O2 supplies the gate shape and the identity decomposition. O1 is the control. O7 is excluded with reasons on the record. This composition, and why combining is legitimate rather than indecisive, is argued in `PS2_ARCHITECTURE_SELECTION.md`; the specification is `PS2_SANKET_SOLUTION_ARCHITECTURE_FINAL.md`.
