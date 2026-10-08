# SUTRA — MODEL SELECTION

Every model choice, compared against alternatives, with the evidence that decided it, the starting configuration, the
protocol that will judge it, and the condition under which the choice is reversed. **No model has been trained yet** —
this document pre-registers the choices so that later results cannot be read as retrofitted justifications
(`PS3_EXPERIMENT_PLAN.md` fixes the comparison grid).

---

## 0. Selection protocol (what makes a choice legitimate here)

1. **Task first.** Each model answers one question (`PS3_MODEL_ARCHITECTURE.md` §1); a model is never added "because it
   might help".
2. **Baseline always included.** Rule-priority top-1 and the vendor pin are baseline rows in every comparison. On the
   surveyed 100 the vendor pin is median 376.4 m / 9.0% <100 m, and the oracle over current arms is 306.2 m / 11.0%
   [S91] — a candidate model must beat those, not a straw man.
3. **Small-data discipline.** S-Eval = the 100 surveyed rows (measured, never trained); supervision = operational field
   evidence with the S-Eval firewall; nested grouped CV by place block × account; leave-town-out kept only as a stress
   test; ≤ 15 features.
4. **Decision rule.** Adopt only if it improves the pre-registered primary metric beyond the grouped-bootstrap interval
   **and** does not regress measured coverage, any stratum with n ≥ 15, cost, or refusal behaviour.
5. **Recorded either way.** Rejected models go in `PS3_DECISION_LOG.md` with the number that rejected them.

---

## 1. Candidate generation (M1) — retrieval arms

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| **Rule + gazetteer exact/token match** (town-scoped) | deterministic, explainable, sub-ms, no licence issue; measured 65.9% coverage at 356.7 m median [S91] | misses misspellings | **CHOSEN — primary** |
| Probabilistic record linkage (Fellegi–Sunter per-field weights) [S22] | no labels needed, auditable weights, handles partial agreement | needs tuned field weights and a blocking strategy | **CHOSEN — secondary matcher** for unmatched records |
| Fuzzy string (Jaccard / char-3-gram / ratio) | cheap, already implemented as candidate features | alone it matches garbage confidently | **CHOSEN — as features, never as a decision** |
| BM25 over gazetteer strings [S23] | strong on short noisy strings | adds an index; gains unproven here | **BUILD IF TIME** (experiment B) |
| Neural/embedding retrieval | handles paraphrase | licence-cleared Indic model + real-text benchmark absent; cost [S17] | **RESEARCH ONLY** |
| LLM as resolver/parser | flexible | unverifiable, costly, latency; nothing in the survey shows it winning at this scale [S12][S17] | **RESEARCH ONLY** |
| External gazetteers / address databases (OSM, Overture, Open Buildings, OpenAddresses, third-party POIs…) | — | forbidden by the **final data policy**: official data only; licence duties and provenance cannot be justified against the measured oracle ceiling | **REJECTED (2026-10-07)** |
| Cross-encoder reranker over candidates [S19] | accuracy on hard pairs | 100–1000× cost; our candidate sets are tiny and structural | **RESEARCH ONLY** |

## 2. Ranker (M2) — ordering the candidate set

| Option | Evidence | Decision |
|---|---|---|
| Rule priority (vendor > locality > town) | measured: identical to the vendor alone (376.4 m, 9.0%) because the vendor pin wins every row [S91] | **BASELINE — always reported** |
| Logistic regression on candidate features | interpretable, stable at n = 100; cannot express interactions (stratum × text) | **RUN in experiment D** as the honest simple model |
| **Gradient-boosted LambdaMART (`rank:ndcg`), shallow, monotone constraints** | the standard for listwise ranking with mixed features [S20]; monotone constraints inject domain knowledge without parameter inflation; handles ≤ 25 candidates/group trivially | **CHOSEN** |
| Pairwise (RankNet-style) loss | often more stable than listwise at tiny group sizes [S20] | **CHOSEN as the small-data variant** — the experiment compares pairwise vs listwise and picks by S-Val |
| Deep listwise ranker (e.g. transformer over candidates) | needs far more data | **RESEARCH ONLY** |
| Multi-armed bandit over arms | needs exposure logs | **RESEARCH ONLY** (needs the exploration slice to exist first) |

Starting configuration: `n_estimators ≤ 300`, `max_depth ≤ 4`, `learning_rate 0.05`, `subsample 0.8`, `lambda` regularisation
on, monotone constraints on `similarity↑`, `granularity↑`, `distance_to_town_centroid↓`; early stopping on grouped S-Val.

**Kill criterion:** if the ranker does not beat the rule baseline beyond the interval on S-Val, **ship the rule baseline**
and record that the retrieval arms — not the ranking — are the bottleneck. (The audit already suggests this is the likely
outcome with the current arms. The grid re-tests it on **official arms only**: external augmentation was rejected by
final project decision (`PS3_FINAL_DATA_AND_ARCHITECTURE_FREEZE.md` §DATA), so the honest next moves are parsing,
memory and field evidence.)

## 3. Point fallback (M3)

| Option | Evidence | Decision |
|---|---|---|
| Town/locality centroid as the answer with a wide radius | honest, zero cost | **BASELINE** |
| Ridge regression on coarse T0 features | stable, interpretable | **CHOSEN for a coordinate when a prior exists** |
| Small GBM | marginally better | **CHALLENGER** — accepted only if it beats ridge beyond the interval |
| Any model with a narrow radius | fabricates precision | **FORBIDDEN by policy** (tier caps at APPROXIMATE) |

## 4. Evidence weighting (M4)

| Option | Evidence | Decision |
|---|---|---|
| **Likelihood-ratio table** (outcome dimension × dwell band × trail agreement × stratum) | the signal is 1-D and well-measured (met_borrower 16.6 min vs `address_not_traceable` 1.3 min; pin-following signature 84.9% vs 3.2%) [S90] | **CHOSEN — ships first** |
| Logistic regression on the same evidence dims | slightly smoother; needs adjudicated labels to fit honestly | **CHALLENGER** |
| GBM | can learn interactions (e.g. dwell × stratum) | **CHALLENGER, later**, only with adjudications |
| Deep model over raw trails | no labels, no need; trails are geometry | **REJECTED** |
| Treating `address_not_traceable` as negative evidence | measured to be wrong (1,603.2 m from truth) | **FORBIDDEN by invariant** |

Starting bands (pre-registered, to be re-fit only on adjudicated data): met-someone base 0.9, `locked_premises` 0.5,
`no_such_person` 0.4 (place) / negative (person), `neighbour_says_shifted` 0.4, `address_not_traceable` 0.0 (place) with
record-suspicion only; sub-minute dwell multiplier ≤ 0.35; duplicate-media ≤ 0.4.

## 5. Integrity scorer (M5)

| Option | Evidence | Decision |
|---|---|---|
| **Rule set** (mock flag, speed, coordinate reuse, duplicate media, dwell, trail agreement, agent baseline) [S26][S27] | the dataset contains one anomaly type (FA009 duplicate photos: 156/610 = 25.6%) and no spoofing [S90] | **CHOSEN — ships** |
| Supervised anomaly classifier | needs labelled faults; training on injected faults encodes the injection | **BUILD IF TIME**, and only weights, never verdicts |
| Unsupervised outlier detection on features | no ground truth to validate; high false-positive risk against honest agents | **RESEARCH ONLY** |
| GPS-only spoof detector | proven insufficient here: FA009's GPS is pristine [S90] | **REJECTED** |

## 6. Radius calibration (M6)

| Option | Evidence | Decision |
|---|---|---|
| Fixed radius per vendor stratum | ignores our own evidence classes; the audit's own strata range 108.6–1,375.8 m | **REJECTED as the product, kept as a diagnostic** |
| Plain split conformal | distribution-free but spatially naive | **FALLBACK**, documented under-coverage |
| Bootstrap quantiles | published under-coverage (81% vs 90% nominal) [S24] | **REJECTED as the primary** |
| **Geographically weighted split conformal** | 93.67% coverage at 90% nominal; local approximate exchangeability > 75% under noise [S24][S25] | **CHOSEN** |
| Quantile regression / GBM quantiles | needs more labels per stratum; conflates model error with calibration | **CHALLENGER for the fast loop**, calibrator still decides the published radius |

n-guard: a stratum with n < 15 is calibrated by its parent and labelled `calibration_fallback` (our `pincode` n=10 and
`rooftop` n=1 fall here) — the honest response to thin data.

## 7. Purpose / eligibility classifier (M7)

| Option | Decision |
|---|---|
| Keyword/rule gate | **CHOSEN as the gate** (must be explainable to a compliance reviewer) |
| Logistic/GBM purpose classifier | **CHALLENGER** to *inform* the gate; adopted only with measured precision/recall above the rule |
| LLM-based classification | **RESEARCH ONLY** (unverifiable for a consequential action; [S48] shows the shipped pattern is status + human review) |

## 8. The selection table (one screen)

| Component | Ships | Challenger | Rejected / Research |
|---|---|---|---|
| Retrieval | rules + gazetteer + probabilistic linkage | BM25 (if time) | embeddings, LLM, cross-encoder, deep reranker |
| Ranker | GBDT LambdaMART (pairwise small-data variant), monotone | logistic regression | deep listwise, bandits |
| Point fallback | ridge (or prior) | small GBM | any narrow-radius model |
| Evidence | likelihood table | logistic → GBM (with adjudications) | deep trail models |
| Integrity | rules | supervised scorer (weights only) | GPS-only detector, unsupervised outlier |
| Radius | geographically weighted conformal | quantile GBM (fast loop) | bootstrap, fixed radius |
| Purpose gate | rules | logistic/GBM | LLM |

## 9. What would change a choice (pre-registered reversal conditions)

1. Ranker fails to beat the rule baseline ⇒ retrieval arms are the bottleneck ⇒ invest in arms (I/J), not in models.
2. Logistic evidence model beats the table beyond the interval on S-Val ⇒ adopt the model, keep the table as the audit view.
3. Adjudicated integrity labels appear (≥ 300) ⇒ M5 becomes learned (still weights-only).
4. Real, non-synthetic text arrives with ≥ 10⁴ labels ⇒ re-open M1/M2 to neural options, with a fresh benchmark.
5. Coverage cannot be met after spatial weighting and widening ⇒ **stop publishing nominal levels**, publish empirical
   hit-rates per stratum (`PS3_UNCERTAINTY_ARCHITECTURE.md` §8).
6. Cost pressure (a cheaper substitute is demanded) ⇒ the substitution ladder in `PS3_COST_ARCHITECTURE.md`, applied only
   to components whose removal path has been measured — never by damaging the evidence or uncertainty layers.
