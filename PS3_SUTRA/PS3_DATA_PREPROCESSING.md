# SUTRA — DATA PREPROCESSING

Deterministic, versioned, leakage-checked transformation from cleaned tables (`data/cleaned/`) to the two artefacts a
model may consume: a **candidate table** and a **feature matrix**, each with a receipt. Nothing else is fed to a model.
Implemented in `tools/build_candidates.py`; guarded by `tools/check_leakage.py`.

---

## 1. Order of operations (fixed; changing the order is a new `rule_version`)

```
text_norm ─► span extraction ─► entity resolution (rule → pattern → optional statistical) ─► gazetteer match
   ─► candidate generation (T0/T1) ─► candidate feature vector ─► (memory arm only) as-of belief join
   ─► sample weighting (exposure) ─► per-arm normalisation ─► training tensor / scoring request
```

Two hard boundaries inside that order:
1. **No statistic is computed over the concatenation of train and test.** Normalisation, vocabulary, IDF, gazetteer
   frequency and any encoder are fitted on the training window only and applied to validation/test (`PS3_LEAKAGE_AND_VALIDATION.md` §5).
2. **The as-of join is a point-in-time join.** A feature that uses memory or field evidence may only read observations
   with `observed_at < as_of`; the join is implemented as a range query on an append-only store, not as a lookup on the
   latest value (the classic "current state" leak).

---

## 2. Text representation — three tiers, each justified by cost

| Tier | Representation | Use | Cost | Justification |
|---|---|---|---|---|
| **T1 (ships)** | normalised tokens + spans + character 3-grams + matched-gazetteer tokens | candidate features, similarity, resolver | microseconds | the audit shows the discriminative signal is *structural* (locality token, house number, relation word), not semantic |
| **T2 (BUILD IF TIME)** | char n-gram TF-IDF + SVD(64) over the *record-vs-candidate-name* pair | strength feature for street-level candidates | milliseconds, fit-once | helps when a locality name is misspelled; measured in experiment B |
| **T3 (RESEARCH ONLY)** | multilingual sentence embeddings (Indic-capable) | only for locality/landmark semantic matching in a *deployment with real, noisy text* | GPU + licence review per model | the dataset's text is synthetic and regular; an embedding model would learn its own generator's quirks. Without a licence-cleared model and a real-text benchmark it cannot be defended |

**No LLM anywhere in the preprocessing path.** Address parsing here is a *bounded, checkable* task with ~40 markers and
a closed gazetteer; an LLM would add latency, licence exposure and unverifiability for a problem a 40-line rule engine
plus a small tagger already solves (this is the §12 pruning decision, recorded in `PS3_DECISION_LOG.md`).

---

## 3. Entity resolution (text → canonical entities)

| Stage | Rule | Output | Failure behaviour |
|---|---|---|---|
| 1. rule | exact token match against locality names, town names, known pincodes, landmark names of the declared town | `matched_locality_id`, `matched_landmark_id` (with offsets) | fall through |
| 2. pattern | house-number patterns (`h.no`, `no.`, `plot`, `#`, leading digit token), relation phrases, cross/main grammar | spans, `parsed_house_no` as *string*, never as an integer | fall through |
| 3. gazetteer fuzzy | token-set similarity + char-3-gram over candidate localities **of the declared town only** | best match + score | below threshold → no match |
| 4. statistical parser (BUILD IF TIME) | sequence tagger over spans, trained on rule-derived silver labels, validated by hand-checked agreement, never allowed to override a confident rule match | span labels | its output is a *feature*, never a fact |
| **unresolved** | nothing matched | explicit `unresolved` with the reason | the record still gets a candidate set (town prior) and a wide radius |

**Never done:** inferring a pincode; guessing a locality across towns (35 names for 36 localities — `Nehru Colony`
exists in two towns); merging localities by text similarity; treating a landmark name as an identity (14 distinct names,
198 duplicate `(town, name)` pairs).

---

## 4. Candidate generation (T0/T1 — what the ranker will score)

Arms (each row carries `arm`, `source_ref`, position, granularity, `licence_class = "official"`), exactly as
the implementation contract freezes them (`PS3_IMPLEMENTATION_CONTRACTS_2026-10-07.md` §4):
`frozen_baseline` · `locality_centroid` · `town_centroid` · `official_landmark` · `address_book` ·
`field_evidence` · `memory` · `place_neighbour` (**C2-gated, default off**).

Measured — the pre-contract arm set (four arms, archived under
`data/derived/superseded_pre_contract_2026-10-07/`): coverage 92.4% · oracle ≤100 m 11.0% · **oracle median
306.2 m vs the frozen baseline 376.4 m**. That remains the honest ceiling of the *old* arm set; the post-contract
arm set (eight arms, `data/derived/candidates_v2.csv`) is measured by experiment A, and its numbers are reported
there rather than restated here. Either way the architecture invests in memory, official anchors and field evidence
rather than in a bigger ranker — external gazetteers are rejected by the final data policy.

**Deduplication:** candidates within 25 m *and* the same granularity collapse to the first by arm priority, keeping the
higher-evidence provenance. RRF (k = 60) is used only to order candidate lists for retrieval experiments, never as a
final score ([S-sources in the register: hybrid retrieval/RRF]).

---

## 5. Feature set (cold-start), by origin

| Group | Features | Availability | Notes |
|---|---|---|---|
| Query-side | `f_pin_in_text`, `f_pin_unknown`, `f_no_digit`, `f_no_separator`, `f_outside_town`, token count, digit count | T0 | `f_outside_town` is the strongest single T0 signal for `UNPLACEABLE` |
| Text–gazetteer | `f_sim_jaccard`, `f_sim_char3`, `f_sim_ratio` (record vs matched locality), `f_locality_name_matched` | T0 | all three kept because they fail differently on misspellings |
| Candidate-side | `arm`, `granularity`, `arm_rank`, `f_n_candidates`, `f_dist_to_town_centroid_m` | T1 | `arm`/`granularity` enter as **categorical** and are monotone-constrained in the ranker |
| Vendor metadata | `f_vendor_stratum` (rooftop/street/locality/pincode/none) | T0 | the vendor's own vocabulary; kept as *context*, never as a truth claim |
| **Warm-only (separate file)** | prior field observations count, as-of belief mean/σ, age of last confirmation, contradiction count | T1 as-of | requires `observed_at < as_of`; cold-start scoring is forbidden |
| **Excluded forever** | every account field; `agent_id` at inference; `ptp_id`; `surveyed_*`; anything derived from the outcome of the visit being scored | — | enforced by prefix in `check_leakage.py` |

`agent_id` deserves a note: it is a *training-time* feature only in the evidence model (with an explicit
"unseen agent" fallback bucket), because in production an unseen agent must not break scoring.

---

## 6. Missing values, scaling, encoding

* **Missingness is information here.** `frozen_baseline` absent ⇒ `OUT` or ungeocoded: the record simply has one arm fewer, and the absence is never imputed.
  Missing `gps_accuracy_m` ⇒ unknown reliability, weight reduced, not filled with the median.
* Numeric features: `log1p` on distances, then robust scaling fitted **on train only**.
* Categoricals: ordinal for `granularity` (town < locality < street < rooftop) and one-hot for `arm`; unknown category →
  its own bucket. No target encoding anywhere (it leaks through folds on small data).
* No SMOTE / synthetic oversampling. Labels are scarce and spatially clustered; synthetic candidates would be
  indistinguishable from real coarse candidates and would corrupt radius calibration. Class imbalance is handled by
  **loss weighting and grouped ranking**, not by inventing rows.
* Weights: each candidate carries `w_exposure = 1/P(exposure)` computed from the observed visit-demand distribution
  (audit: visit rate 19.9% → 84.8% across DPD bands) so the training distribution reports what a *deployment* sees
  (`PS3_LEAKAGE_AND_VALIDATION.md` §6).

---

## 7. Building the training tensor

1. For each labelled address (surveyed truth, training window only): candidate list from the cold-start or warm builder.
2. Label per candidate: `y = 1[candidate within τ of truth]`, τ ∈ {50, 100, 250, 500} m — **reported as a curve, never
   one number**; plus the regression target `log1p(error_m)` for the fallback point model.
3. Group = `address_id`; ranking loss computed within the group (`rank:ndcg` / pairwise), so an arm that is merely coarse
   cannot be rewarded for being present.
4. Group split by `group_key`+`account_id`+time (never a random row split).
5. Persist: tensor hash, `schema_version`, `rule_version`, the split ledger version, and the exact candidate builder
   invocation — a model that cannot name its tensor provenance may not be promoted.

---

## 8. Cost of preprocessing (why it is not the bottleneck)

Full pipeline on the official 3,117-address set: cleaning ≈ 9 s, candidates+features ≈ 23 s, all in Python/pandas on one
core, no GPU. The design point: **preprocessing must stay cheap enough to re-run on every retrain and every belief
rebuild**, because the fast loop re-derives features for a single record (milliseconds) and the slow loop re-derives the
whole matrix nightly. Anything that costs a GPU pass over the corpus is excluded by cost, not by taste
(`PS3_COST_ARCHITECTURE.md`).

---

## 9. Reproduce

```
python3 tools/clean_official.py         # cleaned tables + log
python3 tools/build_candidates.py       # candidates, features, receipts, labels, per-arm report
python3 tools/check_leakage.py          # all feature rules enforced
```


---

**Sources.** External claims resolve in `PS3_SOURCE_REGISTER.md` (`[S1]`–`[S50]`); internal measurements are
`[S90]` (audit log `data/derived/ps3_audit_full.txt`), `[S91]` (radius calibration
`data/derived/derived_ps3_radius_calibration.csv`) and `[S92]` (prior-pass measurements). Statements that cite no
external source rest on internal evidence and are labelled `[DATA]`/`[INFERENCE]` where they appear.
