# SUTRA — DYNAMIC LEARNING ARCHITECTURE

How SUTRA changes when reality changes — without retraining after every visit, without thrashing, and without a single
visit being able to poison what the system believes.

Two speeds, one rule: **the fast loop moves beliefs; the slow loop moves models. Nothing else moves anything.**

---

## 1. Why two loops (the commission's question, answered with evidence)

| Option | Verdict | Evidence |
|---|---|---|
| Retrain per visit | **rejected** | ungovernable on small data, unreproducible behaviour, and the cost is absurd: 5,578 visits × a training run; also catastrophic-forgetting risk on incremental updates [S35] |
| Online learning continuously updating parameters | **rejected** for this stage | label lag (a visit's reliability is only known when evidence exists), no rollback story, and tabular models gain little versus a scheduled fit [S33][S35] |
| **Immediate belief update + gated periodic retraining** | **chosen** | beliefs are cheap, local and reversible; models are expensive and must be governed [S31][S33][S34] |
| Retrain on a fixed schedule only | **partial** | used as a floor (monthly), with drift triggers to react sooner |

The published comparison that shaped the trigger design: an uncertainty-based drift trigger produced **16 retrains where a
naive trigger produced 345** [S32] — i.e. the *trigger* is where the cost and the risk live.

---

## 2. The fast loop (milliseconds; no training, no gradient, no parameter change)

```
visit closes
   │
   ├─▶ E1 evidence extraction (S9)         outcome dimensions · dwell · trail geometry · media integrity
   ├─▶ E2 integrity weighting (S10)        w_place, w_person ∈ [0,1] + reason codes (never zero by a single signal)
   ├─▶ E3 belief update (S11)              append-only version: position(s), tier, radius, support, contradictions
   ├─▶ E4 memory write (S12)               observation + evidence_score + alias evidence (if any)
   ├─▶ E5 side effects                     re-verification task (if suspected drift), review flag (if contested)
   └─▶ E6 counter                          buffer_add(record)   ← the ONLY thing the slow loop consumes
```

Guarantees:

* **Idempotent** by `visit_id` (a replayed sync cannot double-count).
* **Append-only**: nothing is edited; corrections are new versions with reason codes (`PS3_ADDRESS_MEMORY_ARCHITECTURE.md`).
* **Bounded influence**: per-visit caps (a single visit can move belief by at most one tier step, and cannot promote to
  `CONFIRMED` alone); promotion requires **two independent confirmations** [S49].
* **Latency budget**: ≤ 120 ms p95 end-to-end, in-process (`PS3_SYSTEM_DESIGN.md` §4).
* **Reversible**: any belief version can be superseded by appending a version that cites the rollback reason; the auditor
  sees both.

**What "instant" means concretely:** the next query that reads that address sees the new belief *and* the new radius, and
the response says which belief version it read. No restart, no cache invalidation dance, no model deployment.

---

## 3. The slow loop (buffered, gated, weekly-to-monthly)

```
                                   ┌───────────────────────────── quality gate
buffer_add(record) ─► EVIDENCE BUFFER ─► [1] quality filter ─► [2] window assembly ─┐
                                   └──────────────────────────────────────────────┘
                                                                                    ▼
        [3] DRIFT CHECK  ── no drift & schedule not due ──► HOLD (log)  ──► back to buffer
                 │ drift ∨ schedule ∧ cooldown elapsed
                 ▼
        [4] RETRAIN (warm start from champion)  ─►  [5] RECALIBRATE radius map
                 │
                 ▼
        [6] CHALLENGER EVALUATION on S-Val (grouped, weighted, with negative controls)
                 │
        ┌────────┴─────────┐
        ▼                  ▼
   PASS → PROMOTE      FAIL → HOLD (champion stays; challenger archived with the reason)
        │
        ▼
   [7] POST-PROMOTION MONITOR → regression detected → ROLLBACK to previous alias
```

### [1] Quality gate on the buffer
A record enters the training window only if all hold: `evidence_score.w_i ≥ w_min`; the visit is not flagged as suspected
(duplicate media / speed implausibility); the outcome is usable for the dimension being learned (a place label needs a
place dimension ≥ weak-positive); the record is not part of a `CONTESTED` unresolved contradiction; `agent_baseline`
window is complete for the visit date; and it is not `address_not_traceable` **for a place label** (it is eligible for the
*record-suspicion* target only). Gate drops are counted and reported — a shrinking buffer is an early warning about
either fraud or drift.

### [2] Window assembly (label lag is excluded by construction)
* Window = `[t − W, t)` where `W` = 90 days (configurable), *and* only records whose adjudication/evidence arrived before
  `t` — the standard mistake (training on labels that did not exist yet) is impossible because the buffer is keyed on
  `observed_at` and the window closes before assembly [S33].
* Warm features are rebuilt **as of the window end**, never with current memory.

### [3] Drift checks (four streams, cheap, independent)

| Stream | Detector | Signal | Typical action |
|---|---|---|---|
| Error / radius stream (labelled subset) | **ADWIN** [S31][S32] | change in median/p90 error and coverage | trigger |
| Model uncertainty (unlabelled, daily) | ADWIN on predictive-entropy proxy | rising uncertainty without labels | investigate; trigger if paired with feature drift |
| Feature stream | PSI/KS nightly per feature, per town | vocabulary/distribution shift | warn; trigger if ≥ k features shift |
| Outcome-mix stream | DDM-style on accuracy *and* on outcome distribution | e.g. a jump in `locked_premises` — could be seasonality, could be a process change | investigate before retrain |

Guard-rails: **cooldown** (no trigger within C days of the last promotion), **hysteresis** (a drift must persist across
two consecutive windows), **minimum buffer** (n ≥ N new quality-gated records — otherwise a "drift" is just noise), and
**seasonality blackout** (expected calendar effects are annotated and excluded, e.g. quarter-end collection pushes).

### [4] Retrain
Full retrain with **warm start** from the champion's parameters [S33][S35]; same feature schema and monotone constraints;
seeds fixed; the training run records the tensor hash, the window, the split version, the buffer composition and the
negative-control results.

### [5] Recalibrate
The radius map is refit (geographically weighted split conformal [S24][S25]) on the validation window and compared to the
champion's map: **a promotion that improves ranking but worsens measured coverage is rejected** — coverage is a
first-class gate, not a diagnostic.

### [6] Challenger evaluation (the gate)
Promotion requires *all* of:
1. primary metric (pre-registered) improves beyond the bootstrap interval on S-Val **and** does not regress on S-Eval beyond
   its interval when the final test is run;
2. **coverage** ≥ nominal on S-Val with the n-guard;
3. **no stratum regresses** beyond its interval (with n ≥ 15 strata only — thin strata are reported as "insufficient n");
4. **negative controls still behave** (shuffled ≈ chance; agent-ID-only under-performs);
5. **cost and latency within budget** (`PS3_COST_ARCHITECTURE.md`);
6. refusal behaviour unchanged or better (the model may not buy accuracy by refusing more records *silently* — refusals are
   visible and counted);
7. the challenger's evidence policy passes the invariant tests (no negative-evidence movement; no pin-agreement feature).

### [7] Post-promotion monitoring and rollback
Alias-based registry promotion (`champion` / `challenger`) [S34]; rollback is a single alias flip and takes effect without
a deploy. A regression alarm is defined *before* promotion (e.g. median error +15% on a rolling week, or coverage below
nominal for two consecutive days) so that rollback is a decision rule, not a debate.

---

## 4. What updates instantly vs what waits (the operational contract)

| Thing | Updates | Latency | Reversible by |
|---|---|---|---|
| belief position(s), tier, radius, reason codes | on evidence | ms | appending a version |
| contradiction state | on contradiction | ms | resolution or adjudication |
| re-verification priority | on suspicion | ms | completing the task |
| agent integrity baseline | rolling window | minutes | window roll-forward |
| alias tables | reviewed additions only | days | review reversal (versioned) |
| **ranker model** | slow loop only | weeks | alias rollback |
| **calibration map** | slow loop only | weeks | alias rollback |
| **evidence policy (`policy_version`)** | change-controlled | on approval | re-derive beliefs from observations (cheap, because observations are immutable) |

**Never:** a visit triggering a model update; a belief being edited; a policy change applied silently to history.

---

## 5. Learning from *what the system chose to visit* (the part most systems get wrong)

The audit measured exposure to be demand-driven (visit rate 19.9% → 84.8% across DPD bands). Therefore:

* **Training weights** `≈ 1/P(visit | T0 covariates)` (clipped 1/99, logged) so the model does not learn the collections
  policy instead of geography [S38].
* **An exploration slice** (5–10% of assignments) chosen by uncertainty + spatial coverage + a random component [S36][S37],
  giving a later, honest comparison for "did the loop improve things?".
* **Evaluation reports both weighted and unweighted metrics**, always side by side.
* **The loop's effect on itself is measured, not assumed:** the slow loop's gate includes a check that accuracy on the
  exploration slice has not fallen while accuracy on the demand-driven slice rose — the classic sign of a self-confirming
  loop.

---

## 6. Simulation on this dataset (honest design under a 90-day window)

The commission forbids pretending this dataset supports a real drift experiment: visits span **2026-04-01 → 2026-06-29**,
a 90-day window with no known regime change [S90]. So dynamic learning is evaluated by **replay simulation**, and labelled
as such:

| Simulation | Mechanism | What it tests | Reported as |
|---|---|---|---|
| **Cold vs warm** (experiment N) | order visits chronologically; score each address as of its first visit, then re-score after k visits | does field evidence improve the answer? | measured on the surveyed subset with as-of discipline |
| **Retrain replay** (experiment J) | weekly cut-points: train on everything before t, evaluate on `[t, t+7d)` | stability of the slow loop under a moving window | mean/variance of the primary metric; number of "promotions" in simulation |
| **Injected drift** (fault bed) | shift a locality's true centre by 300 m after t | does ADWIN fire, and how many periods late? | detection delay (periods), retrains triggered (target ≪ per-visit) |
| **Injected poisoning** | coordinated fake confirmations | does the gate block promotion? | block rate, false-block rate |
| **Label-lag test** | delay evidence arrival by 3/7/14 days | does the quality gate + window assembly stay correct? | metric impact; any leak fails the pipeline |

Every simulated result is reported with the word **simulation** in the same sentence, and none of it is presented as a
production drift measurement.

---

## 7. Governance and audit

* Every promotion writes a **model card** carrying the binding policy line ("trained on the official PS3 dataset and its
  officially assigned shared tables only; no external data") plus: window, buffer composition, feature schema, metrics with intervals, coverage,
  strata regression table, negative-control output, cost delta, and the rollback pointer.
* The **promotion log** is append-only: who/what/when/why, and the outcome (promote/hold/rollback).
* **Cooldown and hysteresis settings are configuration**, versioned with the policy, so behaviour is reproducible.
* **Data quality incidents** (buffer shrinkage, sudden flag-rate change, vendor outage) gate the loop: a retraining run in
  a data incident is blocked, not nannied.
* The **test-look counter** is logged per experiment so that repeated peeking at S-Eval is visible in the record.

---

## 8. Cost of the loop (the reason it is affordable)

| Activity | Frequency | Cost on this data | Scaling note |
|---|---|---|---|
| fast loop | per visit | milliseconds of CPU | linear in visits; evidence store grows, compute does not |
| drift check | daily | seconds | 4 scalar streams + feature PSI |
| retrain | weekly–monthly, gated | < 10 min CPU, no GPU | tabular models on ≤ 10⁵ rows |
| recalibration | with retrain | seconds | conformal on a validation window |
| featurisation for a retrain | with retrain | minutes (measured: cleaning 9 s, candidates+features 23 s for 3,117 records) | the reason preprocessing must stay cheap |

**Design consequence:** because the slow loop is cheap, it can afford to be *conservative* (rare, gated, reversible) — and
being conservative is what keeps a learning system from damaging a working one.


## Amendment L1 — replay corrected; the loop is evaluated prequentially; propensities are logged · 2026-10-07

**Corrected numbers.** The 2026-05-15 cut test: 2,726 post-cut visits; warm (confirmed before the cut) **56.0% met
over 1,383 visits** vs cold **24.5% over 1,343**; overall 40.5%. On non-training entities **56.7% vs 25.1%** `[S94]`.
Earlier text printed "56.0% vs 40.5% (all other post-cut visits)" — 40.5% was the *overall* rate. The true contrast is
larger than published; the finding is stronger, not weaker.

**Prequential protocol** [S70]. For every new visit the system (1) emits and stores its as-of prediction — candidates,
radius, direction — **before** the visit; (2) ingests the evidence; (3) updates memory; (4) scores the prediction
against the outcome. Metrics roll over a fixed window (default: last 500 eligible visits) and are reported alongside
the fixed historical replay. A frozen hold-out is not used to judge the loop.

**Propensity logging** [S71]. From the first live window every allocation decision records its **propensity** — the
probability that this address was chosen for this slot under the then-current policy. Without it no later comparison
of targeting policies is identifiable; with it, IPS/SNIPS-style reweighting becomes possible. The propensity is
evaluation metadata: never a feature, and every targeting claim reports weighted **and** unweighted numbers.

**Exposure discipline (rule unchanged, wording sharpened).** Visits are targeted and yield is flat, so no yield or
triage claim is made without conditioning on the exposure variables (delinquency band, portfolio, address type), and
the exploration slice (D15) exists to make future comparisons honest — now with its propensities logged.
