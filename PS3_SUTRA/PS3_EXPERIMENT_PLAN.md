# SUTRA — EXPERIMENT PLAN (A–O)

Pre-registered. Fifteen experiments, each with a hypothesis, a baseline, a fixed metric set, leakage guards, and the
decision it informs. Written **before** any training so that results cannot be cherry-picked afterwards, and so that a
negative result is a *finding*, not a failure to be hidden.

**Nothing has been trained yet.** This plan is the contract for when training is permitted — after the architecture and
preprocessing stages are frozen (the commission's order).

---

## 1. Fixed measurement rules (identical in every experiment)

| Rule | Detail |
|---|---|
| **Primary ground truth** | the 100 surveyed records (`surveyed_addresses.csv`), S-Eval, never trained on, never used for tuning |
| **Secondary signal** | adjudications and high-integrity visits, evaluated **as-of** and labelled as proxy evidence, never as truth |
| **Splits** | the **immutable protocol** (`PS3_IMPLEMENTATION_CONTRACTS_2026-10-07.md` §2): S-Eval = the 100 surveyed, untouched; S-Train/S-Val = operational supervision with the S-Eval firewall (145 addresses excluded); nested grouped CV (place blocks × accounts); time-ordered cut-points for loop experiments. **No experiment may invent its own split** |
| **Metric set (never one metric)** | median / p75 / p90 error · hit-rate curve <50/<100/<250/<500 m · precision@1 · nDCG@5 · tier mix · refusal rate (+ its correctness) · **measured coverage of the published radius** · calibration error (ECE) · per-stratum with the n ≥ 15 guard · cost per 1,000 resolves · p95 latency · integrity precision/recall on the fault bed |
| **Intervals** | grouped bootstrap 95% (10,000 resamples). A difference inside the interval is reported as **"not resolved by this dataset"** |
| **Weights** | every visit-based metric reported both **unweighted and exposure-weighted** (propensity from T0 covariates, clipped 1/99) |
| **Negative controls (always printed)** | shuffled-label model (≈ chance) · agent-ID-only model (must under-perform) · vendor-pin-only row · random-candidate arm · tensor-hash registration check |
| **Receipts** | each run records tensor hash, split-ledger version, candidate receipt, belief-store version (for memory experiments), buffer composition (for loop experiments) |
| **Test-look counter** | the number of times S-Eval has been queried is logged per experiment and reported |
| **Simulation label** | any result from replay (J, N, O and the drift rows) carries the word **simulation** in the same sentence |

---

## 2. The grid

### A — Official frozen baseline geocode arm (the floor)
* **Question:** what does the vendor pin alone achieve on our ground truth?
* **Method:** rule-priority top-1 = vendor pin where present; town centroid otherwise.
* **Known result (measured):** median **376.4 m**, <100 m **9.0%**, <500 m 71.0%, coverage 92.4% [S91].
* **Decision:** this is the number everything else must beat; it is printed in every other experiment.

### B — Preprocessing ablations
* **Question:** does normalisation/parsing earn its place?
* **Arms:** (B1) raw text features · (B2) normalised + spans · (B3) + tier-2 TF-IDF/SVD features · (B4) + statistical parser features on the unresolved residue.
* **Primary:** candidate recall (does the locality arm fire?) and final hit-rate@100 m.
* **Decision:** adopt the cheapest rung that matches the best beyond the interval. If B3/B4 add nothing, they are dropped **and the decision is recorded** (this is how "no LLMs everywhere" is made an empirical claim rather than a preference).

### C — Retrieval only
* **Question:** how good are the candidate arms by themselves?
* **Method:** measure recall@k and the oracle (best candidate in set) on S-Eval; report coverage per arm over the full book.
* **Known result:** oracle median **306.2 m**, <100 m 11.0% — i.e. **ranking these arms alone is worth ~19% relative** [S91].
* **Decision:** if the **official** candidate oracle remains near the observed ceiling (306.2 m), retrieval is data-limited **within the supplied dataset**. The next investment is official-data parsing, memory and field evidence — **not** external augmentation, which the final data policy forbids.

### D — Retrieval + ranking
* **Question:** does a learned ranker beat the rule priority? Which loss, which features?
* **Arms:** rule priority · logistic regression · GBDT LambdaMART (listwise) · pairwise variant · (−) memory features.
* **Decision rule:** adopt only beyond the interval on S-Val, with no coverage/stratum/cost regression. If no model wins, **the rule baseline ships** (explicitly a legitimate outcome).

### E — Uncertainty / calibration
* **Question:** can we publish a radius whose coverage we have measured?
* **Arms:** fixed per-stratum radius · bootstrap quantiles · split conformal · **geographically weighted conformal**.
* **Primary:** measured coverage vs nominal (90%) per stratum, and coverage under the time split.
* **Known evidence:** bootstrap 81% vs conformal 93.67% at 90% nominal [S24]; >75% under noise [S25].
* **Decision:** the published radius comes from the winning calibrator; strata with n < 15 stay on parent fallback and are labelled.

### F — Vendor + field learning (the core hypothesis)
* **Question:** does learned evidence improve answers beyond any static geocoder?
* **Method:** warm resolves (memory + prior evidence) versus cold resolves (no memory), scored as-of, on addresses with ≥1 usable visit; report separately for addresses with ≥2 confirmations.
* **Primary:** hit-rate@100 m and median error on the warm-eligible subset; **secondary:** tier mix, coverage, refusal.
* **Decision:** if warm does not beat cold beyond the interval, the fast loop's value is limited to *triage* (queue prioritisation), and the architecture must say so — the memory would remain for auditability, not for accuracy.

### G — Full SUTRA
* **Question:** what does the whole pipeline do, honestly?
* **Method:** cold-start and warm modes, full candidate set, ranker, belief, calibrated radius; reported per stratum with n and per tier.
* **Decision:** this is the headline table of the deliverable, and it must include the refusal rate and coverage next to every accuracy figure.

### H — Official-only (frozen floor)
* **Method:** the complete pipeline using only Domain A. This is the **only** configuration that may be called the official benchmark.
* **Decision:** all headline claims come from here.

### I — CANCELLED: external data augmentation rejected by final project policy
* **Status:** **CANCELLED (2026-10-07).** External-data augmentation was considered during research but rejected by final
  project decision. The final PS3 system uses **only** the official CreditNirvana dataset and the legitimately
  PS3-relevant shared data — no scraped, downloaded, third-party or external geographic source enters candidate
  generation, training or any headline metric.
* **Retained in the grid** (rather than renumbering) so that every downstream reference to experiments J–O stays stable,
  and so the reason for the gap is explicit and auditable.
* **Binding statement:** `PS3_FINAL_DATA_AND_ARCHITECTURE_FREEZE.md` §DATA.

### J — Dynamic retrain simulation
* **Question:** does the slow loop stay stable, and does it react without thrashing?
* **Method — labelled SIMULATION:** historical field visits only, time-aware replay, **official data only** (no external data, no physical fieldwork by the team); weekly cut-points (fit on everything before `t`, evaluate on `[t, t+7d)`); injected drift (shift a locality's centre by 300 m); injected poisoning (coordinated fake confirmations); label lag 3/7/14 days. Every number this experiment produces is reported as a simulation, never as a measured field result.
* **Primary:** metric stability (mean ± spread across cut-points), number of simulated promotions, detection delay, and the **retrain count** (target: orders of magnitude below per-visit retraining; the published comparison is 16 vs 345 retrains for a good vs naive trigger [S32]).
* **Decision:** the trigger, cooldown and hysteresis settings ship from what this shows.

### K — Integrity ablation
* **Question:** what breaks without integrity weighting?
* **Arms:** integrity on · integrity off · integrity as a binary accept/reject.
* **Primary:** belief error under injected poisoning (a coordinated fake must not move the primary), plus **false-positive rate on clean visits** as the fairness cost.
* **Known anchor:** FA009's 25.6% duplicate-photo rate with pristine GPS [S90] — an integrity layer that only watches GPS would score zero damage here, which is exactly what the ablation will show.

### L — Memory ablation
* **Question:** is the memory (as opposed to the moments' evidence) doing work?
* **Arms:** no memory · memory without decay · memory with decay · memory without the two-confirmation gate.
* **Primary:** warm hit-rate; contradicted-belief rate; time-to-correct after an injected address shift.
* **Decision:** sets the decay horizon and validates or kills the promotion gate. (The gate is expected to survive: it is what stops a single visit from promoting anything.)

### M — Negative-evidence ablation (the safety experiment)
* **Question:** what happens if negative evidence is allowed to move coordinates?
* **Arms:** quarantine (our invariant) · allow `address_not_traceable` to pull the coordinate.
* **Primary:** error on the surveyed records, restricted to addresses with ≥1 negative visit.
* **Known result:** those check-ins sit 1,603.2 m from truth at 1.3 min dwell, nearer the pin 84.9% of the time [S90] — the ablation is expected to show a large, unambiguous degradation. Reporting it converts an architectural rule into a measured fact.

### N — Static vs dynamic
* **Question:** is anything gained by updating at all?
* **Arms:** static model trained once · scheduled retrain · drift-triggered retrain.
* **Primary:** accuracy over time-split windows; stability; retrain count; recovery time after injected drift.
* **Honest limitation:** the 90-day window (2026-04-01 → 06-29) contains no known regime change [S90] — so this is a **simulation** and its conclusion is about *design behaviour*, not about a measured real-world drift.

### O — Cold vs warm
* **Question:** how does the system behave for addresses with no history?
* **Method:** hold out the never-visited tail (84.6% of addresses at the extreme; 52.6% of addresses beyond the 1,477 ever-visited) and evaluate the cold path separately: tier mix, radius widening, coverage, refusal reasons.
* **Decision:** defines the cold-start contract and the messaging to operators about what "no history" means.

---

## 3. Pre-registered primary metric and honest thresholds

* **Primary:** `<100 m` hit-rate on S-Eval (with the median as the co-primary, because a hit-rate alone can hide a heavy tail).
* **Resolved-improvement threshold:** the improvement must exceed the grouped-bootstrap interval, **and** at least one of {median, p90, coverage} must move in the right direction without another moving materially the wrong way.
* **Reported always:** every figure with its `n`, its stratum, its interval, and the word `simulation` where applicable.

## 4. Reporting template (one page per experiment)

```
Experiment: <letter + name>            Date: <…>   Stage: T0/T1 | T2 | T3   Mode: cold | warm
Data: official dataset only (hash <…>)   No external/augmented data exists in this build (final data policy)
Splits: rule_version <…>   groups: <…>  time cut: <…>   test-look count: <…>
Tensor hash: <…>   Candidate receipt: <…>   Belief store version: <…>   Buffer n: <…>
RESULTS  (unweighted | exposure-weighted)
  median / p75 / p90:  …      hit-rate <50/<100/<250/<500:  …
  precision@1: …   nDCG@5: …   refusal: … (% of which correct: …)
  radius nominal/measured coverage: … / …   ECE: …
  per stratum (n ≥ 15): …
NEGATIVE CONTROLS  shuffled: …  agent-ID-only: …  vendor-only: …  random-arm: …
COST/LATENCY  cost per 1,000: …  p95: …
WHAT THIS CHANGES IN THE DESIGN: <the decision: adopt / hold / drop, and which document is updated>
HONEST CAVEATS  <n, simulation, proxy labels, unresolved strata>
```

## 5. What we expect to find (stated in advance, so surprises are visible)

| # | Prediction | If wrong, what it means |
|---|---|---|
| A/G | the vendor pin remains a hard floor to beat on coarse records; gains come from memory and evidence, not from better ranking of the same arms | our central architectural claim would need rewriting |
| C | official oracle ≈ 306.2 m is the observed ceiling **within the supplied dataset** | prioritise official-data parsing, memory and field evidence over retrieval tuning |
| D | a shallow ranker beats the rule baseline by a small margin; the pairwise variant wins at this n | if not, ship rules and say so |
| E | geographically weighted conformal meets or exceeds nominal coverage where n allows | if not, publish empirical hit-rates instead of nominal radii |
| F | warm beats cold meaningfully **on addresses with ≥2 confirmations**, marginally with one | determines whether triage-only value is the honest claim |
| K | integrity weighting changes little on clean data and a lot under injection | the fairness/utility trade is quantified, not asserted |
| M | allowing negative evidence to move coordinates performs badly | converts an invariant into a measured result |
| J/N | drift-triggered retraining ≈ scheduled retraining on this window; both ≪ per-visit | confirms the two-loop design and its cost story |


## Amendment E1 — experiment grid after the official-scope re-audit · 2026-10-07

| # | Change | Supersedes / extends | Evidence | If it fails |
|---|---|---|---|---|
| E1.1 | Every accuracy and memory experiment gains three-population reporting and leave-block-out folds | single-population reporting in the grid below | **36.0%** cross-split place proximity; 39 split-crossing blocks `[S94]`; [S67][S68] | the claim is withdrawn, not softened |
| E1.2 | Radius-by-stratum is published only with `n_calibration`; strata below n=15 fall back to the parent stratum, labelled | extends experiment E | measured transfer: locality **79.2%** coverage at p80 (n=24 eval); pincode **0% (n=4)** `[S94]`; [S69][S73] | empirical hit-rates replace nominal radii for that stratum |
| E1.3 | The warm/cold replay reports the corrected decomposition | the older "56.0% vs 40.5% (others)" phrasing | warm **56.0%** (n=1,383) vs cold **24.5%** (n=1,343); val+test **56.7% vs 25.1%** `[S94]` | triage value is stated as auditability, not yield |
| E1.4 | Triage claims become exposure-matched audits | the raw warm/cold contrast as a triage argument | exposure targeted, yield flat (37.5–42.9% by DPD band; 43.1→41.8% by outstanding quintile) `[S94]`; [S71] | "confirmability" stays a hypothesis |
| E1.5 | A **propensity-logging** requirement enters the data contract for all future windows | the exploration slice of D15 | logged propensities are the precondition for any unbiased later comparison [S71] | evaluation of targeting stays descriptive |
| E1.6 | Prequential baselines are recorded from the first live window | the frozen-hold-out habit | [S70] | — |
| E1.7 | The remark lane becomes a designed capture + extraction experiment | — | **208/5,578** remarks carry corrective landmarks; **0** name a locality `[S94]` | remarks stay free text and are never trained on |

**Unchanged by this amendment:** the four arms (cold rules, cold ranker, warm memory, oracle), the plural acceptance
metrics of D21, and the refusal to invent a benchmark.


---

## Amendment E2 — final data policy (2026-10-07): external experiments removed

The grid is **A–O with no I**: A — official frozen baseline geocode arm · B preprocessing ablation · C official candidate retrieval/oracle ·
D retrieval+ranking · E uncertainty/radius calibration · F vendor + field learning · G full SUTRA · H official frozen
benchmark · ~~I~~ **CANCELLED** · J dynamic replay / slow-loop simulation (**SIMULATION**) · K integrity ablation ·
L memory ablation · M negative-evidence ablation · N static vs dynamic · O cold vs warm.

Rules that follow from the freeze and apply to every experiment `[S95]`:
1. **Official data only** — no scraped, downloaded, third-party or external geographic source, and no own-experiment
   artefact as data.
2. **Dynamic experiments are historical, time-aware replays, always labelled SIMULATION**; the team conducts no physical
   fieldwork, and no model-derived value ever becomes truth.
3. **The 100 surveyed addresses remain the primary ground truth**; the official benchmark stays frozen; all warm/cold
   results are as-of and time-aware (warm 56.0% / cold 24.5%; val+test 56.7% / 25.1%).
4. **Three populations per claim** (Amendment E1) and radius results carry their calibration n (Amendment U1).

---


## Amendment E3 — two experiments added by the due-diligence pass (2026-10-07)

### C2 — Operational place-neighbour index ablation (**experiment-gated**; not in S4 until it wins)

*Arms:* official candidate arms alone · + place-neighbour candidates (confirmed places within 1 km of the locality
anchor) · + neighbour candidates **with ranker features** · placebo (random points, same count — the control that
separates candidate-density from place knowledge).
*Pre-registered reading (from the capacity probe):* oracle median **306.2 m → 72.2 m**, but the **placebo reaches
93.6 m (55.0% ≤100 m)** at the same candidate count, and the naive nearest-neighbour anchor is **397.2 m** — so the
index is expected to be worth little **unless the ranker selects well** `[S96]`. Admission test: the ranked result
must beat the official-arms-only pipeline beyond the interval on the three populations (A1). Otherwise the index is
dropped, not kept "for completeness" (`PS3_OPERATIONAL_NEIGHBOUR_INDEX_RESEARCH.md`).

### P — Visit-triage / decision-quality replay (**SIMULATION**, official data only)

For every historical visit: reconstruct the state **as-of before that visit**, resolve the address, and derive the
decision the SUTRA policy would have taken — `VISIT` · `VERIFY-FIRST` · `REFUSE/RECHECK` — then compare with the
actually recorded outcome. Primary metrics: bad-visit capture (share of negative-outcome visits flagged),
negative-outcome capture, false verify-first rate, coverage retained, candidate/uncertainty quality per band.
Pre-registered policy thresholds (tier ≥ PROBABLE and radius within the address-level band ⇒ VISIT; APPROXIMATE or
n_neg ≥ 2 ⇒ VERIFY-FIRST; UNPLACEABLE ⇒ REFUSE). No rupee claim: the experiment demonstrates *triage quality*,
never savings. Reference points already measured: post-cut met warm **56.0%** vs cold **24.5%** `[S94]`.
