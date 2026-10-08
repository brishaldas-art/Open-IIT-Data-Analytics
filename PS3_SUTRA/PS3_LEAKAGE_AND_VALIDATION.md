# SUTRA — LEAKAGE AND VALIDATION

The commission's rule: *a mediocre honest number is better than a fake impressive number.* This document defines what
information exists at each moment, what may never see what, and how every claim is measured. It is enforced in code
(`tools/check_leakage.py`) and in the split ledger (`PS3_CANONICAL_SCHEMA.md` §2.11).

---

## 1. The five time stages

| Stage | Name | What exists | What a decision may use |
|---|---|---|---|
| **T0** | pre-geocoding | the record as written, the gazetteers, the vendor's pin **and its stratum**, account *context* (for visit pricing by a consumer, never for location) | T0 only |
| **T1** | candidate generation | our candidate set: arms, positions, granularity, similarity scores, licence class | T0 + T1 |
| **T2** | in-visit | check-in point, GPS accuracy, dwell, trail geometry, photo hash — created *during* the visit | T0 + T1 + T2 **only for that visit's own scoring moment** |
| **T3** | post-visit | the outcome, the remark, any adjudication | may inform belief; may **not** be used to place the visit it came from |
| **T4** | later outcomes | surveyed truth, later visits, re-verification, belief versions | evaluation and slow-loop learning only |

**The anchor rule:** the number delivered *during* a visit may use T2 information; the number delivered *before* a visit
may not. A single model that mixes them is a leak. SUTRA therefore scores at explicit stages (`PS3_API_AND_COMPONENT_DESIGN.md`
§2 exposes `stage` in every response) and every logged prediction records its stage.

---

## 2. The banned list (hard, not advisory)

| # | Banned | Why it is leakage | Enforced by |
|---|---|---|---|
| 1 | `surveyed_*` in any training feature | it is the label | column prefix check |
| 2 | the outcome of the visit being scored | tells the model the answer it is being asked to predict | prefix check + stage gate |
| 3 | any *other* visit's outcome used to place *this* visit's decision when it is later in time | future information | as-of join on `observed_at < as_of` |
| 4 | `distance(check-in, frozen_baseline)` as a correctness feature | audit §2.7b: failure visits land *nearer* the pin (84.9%) than success visits (3.2%) — it encodes the wrong thing | banned-by-name; replaced by trail-agreement and deviation features |
| 5 | `agent_id` as a production feature | unseen agent at inference; also trivially memorises who was careless | evidence model may use it *with* an unseen bucket; location model never |
| 6 | account fields (DPD, outstanding, EMI, lender, product) in a location model | correlates with demand, not with geography; would leak the *visit-selection* mechanism into the coordinate | prefix check on `accounts.*` |
| 7 | `ptp_id` | belongs to a different problem statement; 89.2% null | dropped at cleaning |
| 8 | statistics fitted on train+test (scalers, IDF, vocab, thresholds) | transductive leak | fit-on-train-only rule, receipt per artefact |
| 9 | "latest belief" lookups in a historical join | current-state leak | range join on the belief version stream |
| 10 | selecting the radius from the same rows used to fit the model | optimistic radius | radius fitted on validation, reported on test, with the min-n guard |
| 11 | entity leakage across splits (two accounts, one building) | near-duplicate rows across folds | `group_key` grouping (10 flagged duplicate texts) |
| 12 | publishing a number produced on a `shippable = false` dataset | licence and benchmark confusion | licence class on every candidate + reporting rule |

---

## 3. Label definition (what "correct" means)

| Label | Definition | Available for | Never used for |
|---|---|---|---|
| `err_m` | distance from a candidate to `surveyed_*` | the 100 surveyed addresses | — |
| `label_within_τ` | `1[err_m < τ]`, τ ∈ {50, 100, 250, 500} m | ″ | presenting one τ as "accuracy" |
| `place_positive` | a met-someone / cash-collected visit | 900 addresses (28.9%) | ground truth — an agent can be at the wrong door |
| `record_suspect` | derived from `address_not_traceable` + dwell + agent baseline | 1,400 visits | **any coordinate movement** |
| `radius_claim` | a calibrated radius with measured coverage | all scored addresses | a nominal coverage quoted as measured |

**Pseudo-label policy (explicit):** a field visit may *never* be promoted to ground truth. It may be used as (a) a
training signal with an evidence weight, (b) a validation signal under an explicit assumption, and (c) a trigger for
re-verification. The 100 surveyed records are the only ground truth, and they are held back from all training.

---

## 4. Splits (entity- and time-aware)

| Split | Rule | Size | Purpose |
|---|---|---|---|
| **S-Eval (primary)** | the 100 surveyed addresses; never trained on; stratified by town and vendor stratum | 100 | every headline accuracy number |
| **S-Train / S-Val** | `splits.csv` (account-level 1,680/360/360) **intersected** with `group_key` grouping (account + normalised text + town) so one building cannot straddle | 2,400 accounts | model fitting and tuning |
| **S-Time (for the loop)** | visit-ordered: fit on visits before `t`, evaluate on visits in `[t, t+Δ]`; Δ = 14 / 30 days | 5,578 visits | cold/warm and dynamic-learning experiments (J, N, O) |
| **S-OUThold** | the 237 `OUT` records | 237 | the refusal/`UNPLACEABLE` behaviour — measured, not assumed |
| **S-Explore** | a 5–10% slice of future visits assigned by policy, not by demand | designed | unbiased evaluation of the loop (see §6) |

`splits.csv` is authoritative for accounts; the ledger adds `group_key` and `as_of` so both can be audited. Any change of
rule is a new `rule_version`; experiments must name theirs.

---

## 5. Validation protocol

1. **Nested selection.** Hyper-parameters chosen on S-Val; the radius and the belief weights chosen on S-Val; the final
   number reported once on S-Eval. Repeated looks at S-Eval are logged in the experiment ledger (a running count of how
   many times each test set has been queried).
2. **Fit-on-train-only** for every statistic; the pipeline refuses to fit a scaler on a frame containing test rows.
3. **Metric set (never one metric):** median and p75/p90 error · hit-rate curve (<50/100/250/500 m) · refusal rate and its
   correctness · **coverage of the reported radius** (measured vs nominal) · calibration error (ECE) · per-stratum results
   with `n ≥ 15` guard (below that: reported as "insufficient n", never as a number) · precision@1 and nDCG@5 for the
   ranker · `UNPLACEABLE` precision/recall · integrity flags precision on the injected-fault bed · cost per 1,000
   geocodes · p95 latency.
4. **Negative controls (must fail, and are printed in every experiment):**
   * shuffled-label model — if it scores above chance on S-Eval, the pipeline leaks;
   * "agent-ID-only" model — if it matches the full model, the task is not being learned;
   * vendor-pin-only arm — the honest floor;
   * a random-candidate arm — a null anchor for the ranker;
   * a *post-hoc* check that no reported number comes from a run whose tensor hash is unregistered.
5. **Statistical honesty on n = 100.** No bare point estimates: every headline carries a bootstrap 95% interval (10,000
   resamples, grouped by `group_key`), and the doc says which interval it is. A difference smaller than the interval is
   reported as "not resolved by this dataset", not as an improvement.

---

## 6. Selection bias and the feedback loop (the PS3-specific leakage)

The audit measured the exposure gradient: visit rate rises 19.9% → 84.8% with delinquency. Therefore:

* **Training weights.** Every visit carries `w = 1/P(visit | observed covariates)` estimated by a propensity model over
  T0 covariates (town, stratum, account band). Weights are clipped at the 1st/99th percentile to keep variance sane and
  the clip is reported.
* **Evaluation weights.** Metrics on visited data are computed both unweighted and weighted; the two are printed side by
  side, and any divergence larger than the bootstrap interval is treated as evidence of selection bias, not as noise.
* **Exploration slice.** A small, deliberate, policy-assigned slice of visits (5–10%) is held out from the *decision*
  process, so that later comparisons have an unbiased reference. Without it, "the system improved" is unfalsifiable,
  because the system chose which visits happened (Swaminathan & Joachims logged-bandit bias, source S50-series).
* **The loop's own leak.** A belief updated by a visit must never be read by the decision that produced that visit.
  Enforced by versioning every belief row with `observed_at` and by the "prediction → visit → belief" ordering asserted
  in tests (`PS3_DYNAMIC_LEARNING_ARCHITECTURE.md` §6).

---

## 7. Guard-rails in code (run in CI and before every report)

```
python3 tools/check_leakage.py     # 12 checks: receipts, forbidden prefixes, cold/warm separation,
                                   # labels isolated, Domain A hash-unchanged
python3 tools/check_workspace.py   # structure, no-training-yet, citations, links, licence presence
```

Any experiment's output must contain: tensor hash, split ledger version, candidate receipt, the run's stage, and the
negative controls. A result missing any of those is not reportable, regardless of how good it looks.

---

## 8. The leakage traps this project is most likely to fall into (ranked)

1. **Using check-ins as pseudo-ground-truth.** It flatters the system enormously and is measurably wrong here (audit
   §2.7b). Mitigation: check-ins never enter S-Eval.
2. **"Agreement with the vendor pin" scored as confirmation.** Banned by name.
3. **Exposure-driven optimism** (evaluating on the visited, high-delinquency slice only). Mitigation: weighted metrics +
   exploration slice.
4. **Entity leakage** in the 10 duplicate-text buildings. Mitigation: `group_key`.
5. **Radius quoted from the fitting sample.** Mitigation: nested protocol + min-n guard.
6. **Domain-B result presented as an official benchmark.** Mitigation: fixed three-line reporting shape
   (`PS3_DATA_LINEAGE.md` §4).
7. **A parser whose silver labels are counted as gold.** Mitigation: parser output is a feature; hand-checked agreement
   reported separately with the sample size.
8. **Snapshot drift**: the belief store is a moving target, so an experiment re-run next week may differ. Mitigation:
   belief-store snapshots are versioned and every experiment cites the version it read.




## Amendment A1 — evaluation protocol v2 (place-blocked, split-aware, prequential) · 2026-10-07

**Trigger (measured).** The official split is account-level and time-blind. On the official data: **66 of the 100
surveyed truths sit on train-split accounts** (validation 19, test 15); **124 of the 344 test addresses with a
met-someone visit (36.0%) have a train-split met check-in within 30 m**; 39 of the 3,007 place blocks (99 addresses)
cross the official split `[S94]`. The split separates *accounts*; it does not separate *places*.

**External grounding.** Block cross-validation is *"nearly universally more appropriate than random cross-validation"*
wherever dependence structures exist [S67], and spatially separated folds are its standard implementation [S68].
For a non-stationary stream, the standard protocol is **test-then-train (prequential)**, not a frozen hold-out [S70].

**What changes.**
1. **Every claim is reported on three populations** — all 100 surveyed truths · validation+test only · leave-block-out
   (folds from `data/derived/ps3_place_blocks.csv`, built by `tools/place_block_folds.py`). A single-number result is
   now a schema violation, not a style choice.
2. **The official benchmark is never edited.** The place-block ledger is an evaluation lens and a documentation
   artefact; the account split remains the competition protocol.
3. **Memory and warm-lane features are additionally validated leave-block-out**, so no claim can rest on a
   neighbouring place that sat in training.
4. **The dynamic loop is evaluated prequentially** [S70]: each visit is scored as-of before it enters memory. The
   2026-05-15 cut remains the fixed historical replay; its corrected baseline is warm **56.0%** met (n=1,383) vs cold
   **24.5%** (n=1,343), and **56.7% vs 25.1%** on non-training entities `[S94]`.
5. **Stage labels harmonised to T0–T4** — T0 arrival · T1 candidate generation · T2 pre-visit · T3 during/after visit ·
   T4 future/post-outcome — as defined in the companion re-audit. Where §2 of this document says T2/T3, read the
   harmonised labels.
6. **Radius and coverage carry their calibration n** (Amendment U1).

**What this changes in the real workflow:** evaluation stops crediting the model with knowledge of the neighbours, and
the field operation's own logging (next) becomes an evaluation asset instead of an untracked side effect.

---

**Sources.** External claims resolve in `PS3_SOURCE_REGISTER.md` (`[S1]`–`[S73]`); internal measurements are
`[S90]` (audit log `data/derived/ps3_audit_full.txt`), `[S91]` (radius calibration
`data/derived/derived_ps3_radius_calibration.csv`) and `[S92]` (prior-pass measurements). Statements that cite no
external source rest on internal evidence and are labelled `[DATA]`/`[INFERENCE]` where they appear.
