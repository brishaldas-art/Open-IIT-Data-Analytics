# SUTRA — MODEL ARCHITECTURE

Which models exist, why each is justified by evidence rather than taste, how they are trained on **100 surveyed labels
plus weighted field evidence**, how they fail, and what is deliberately *not* built. Companion: `PS3_MODEL_SELECTION.md`
(the comparison that picks the specific algorithm per component) and `PS3_UNCERTAINTY_ARCHITECTURE.md` (calibration).

---

## 1. The two prediction problems (restated precisely)

| | Problem 1 — *ranking* | Problem 2 — *evidence weighting* |
|---|---|---|
| Asked when | at query time (T0/T1), and again in-visit (T2) | after a visit (T3) |
| Input | the record + ≤25 candidates + as-of memory | the visit: outcome dimensions, dwell, trail geometry, media integrity, agent baseline |
| Output | a score per candidate + reason codes | a weight `w_i ∈ [0,1]` per visit, splitting into *place* and *person* dimensions |
| Labels | `1[err_m < τ]` on the 100 surveyed records (+ grouped entity splits) | no direct labels here; validated **indirectly** by whether weighted beliefs improve calibration and whether injected faults are caught |
| Loss | grouped ranking (`rank:ndcg`, pairwise for the small-data regime) | log-loss on adjudicated outcomes where available; otherwise a likelihood-ratio table |
| Failure mode | confidently ranking a coarse arm above the true street | over-weighting a fake visit; the more dangerous of the two |

**Why not one model.** A single regressor `address → (x, y)` cannot express "two plausible places", cannot say "this visit
matters more than that one", and has no vocabulary for refusal. The audit quantifies the cost of that limitation: the
oracle over the current arms is 306 m median versus the vendor's 376 m, i.e. **ranking alone buys ~19%**; the rest of the
value must come from evidence and memory. Neither can be expressed in a point regressor.

---

## 2. Model inventory (six, each with a job and a kill criterion)

| # | Component | Model | Why this model | Data it needs | Kill criterion (when we drop it) |
|---|---|---|---|---|---|
| M1 | entity resolution / matching | **rule + gazetteer first**, then probabilistic record linkage (Fellegi–Sunter style, per-field weights) [S22] | explainable, no labels needed, audit line per match | gazetteer + address text | if the rule match already covers ≥ the linkage model on a hand-checked sample, drop the model |
| M2 | candidate ranker | **gradient-boosted LambdaMART** with monotone constraints on `granularity`/`arm`, shallow trees (depth ≤ 4), strong regularisation, pairwise loss for the small-data regime [S20] | the task is listwise over a few dozen candidates with categorical structure; trees handle the mixed feature types and are transparent | features from `PS3_DATA_PREPROCESSING.md` §5; grouped CV | if it does not beat the rule-priority baseline on S-Val by more than the bootstrap interval → ship the rule baseline |
| M3 | point fallback | **ridge / small GBM** on coarse features (town, locality centroid, text similarity, stratum) | used only when no candidate exists; a simple model with an honest radius is enough | T0 features | if the town/locality prior matches it, keep the prior |
| M4 | evidence weighting | **likelihood-ratio table first** (stratum × outcome dimension × dwell band × trail agreement), logistic/GBM version as challenger | the signal is 1-D and interpretable; a table can be explained in a review, and the code path is auditable | visit evidence + adjudicated labels when available | if the table and the model disagree materially on S-Val, the table wins until the model is understood |
| M5 | integrity scorer | **rules** (mock flag, speed plausibility, duplicate media hashes, coordinate reuse, stationarity, agent baselines) producing a weight + reason codes [S26][S27]; a learned scorer only when labelled faults exist | the dataset contains **one** anomaly type and no spoof (`PS3_RED_TEAM.md` F1/F2); learning from injected faults alone would encode the injection, not reality | rules need nothing; a learned version needs adjudications | no labelled faults → the learned version is BUILD IF TIME at best, and is *not* used to zero anyone's evidence |
| M6 | radius calibration | **geographically weighted split conformal** [S24][S25]; bootstrap as documented fallback (known to under-cover) | gives a *measured* coverage at a nominal level, which is the contract we publish | candidate errors per stratum, spatially weighted held-out set | if measured coverage cannot be achieved at the declared nominal level for a stratum, the stratum's radius is widened and the shortfall is published |
| M7 | purpose classifier (consumer of the coordinate) | logistic/GBM with measured precision/recall | the eligibility gate needs a purpose signal; the *gate itself* stays a rule | adjudicated purpose labels | if measured precision is worse than a keyword rule, ship the rule |

**Explicitly absent:** deep sequence models for parsing (tier-2 only, BUILD IF TIME), embeddings (RESEARCH ONLY), LLMs
(RESEARCH ONLY), RL/bandits (RESEARCH ONLY, needs logs), HMM map matching (needs a road graph) [S30], any model whose
feature set touches T3/T4 information at T0/T1.

---

## 3. Learning protocol (IMMUTABLE) — operational supervision, untouched S-Eval

**The 100 surveyed records are NEVER used for learning, tuning, feature selection, thresholding or early stopping.**
They are **S-Eval**, the immutable benchmark. This section is the one authoritative protocol; it is restated as normative
schemas in `PS3_IMPLEMENTATION_CONTRACTS_2026-10-07.md` §2, and **no experiment may invent its own split**.

| Set | Membership (exact) | Leakage rules |
|---|---|---|
| **S-Eval** | all **100** surveyed addresses (`surveyed_addresses.csv`), fixed forever | never trained on · never tuned on · never used to choose features or thresholds · every query counted in the test-look counter and reported |
| **S-Train / S-Val** | candidate–place supervision built from **operational field evidence only**: candidate lists for addresses carrying promotion-grade confirmations (independence per F2.2), never the surveyed rows | nested grouped CV: outer folds = **place blocks** (`ps3_place_blocks.csv`), inner folds = **accounts**; S-Val = the inner held-out fold; time-ordered cut-points for loop experiments |
| **S-Eval firewall** | excluded from **every** supervision, feature-fitting and tuning set: the 100 surveyed addresses · their **100 accounts (128 addresses)** · every **place block containing a surveyed address (99 blocks)** → **union = 145 addresses, 4.7% of 3,117** `[S96]` | computed deterministically in code with a receipt; the remaining supervision pool is **2,972 addresses (841 with ≥1 met visit)** |

Consequences, stated plainly:

1. **Grouped nested CV** on the supervision pool with `group_key` = account + place block + town: the same building never
   straddles a fold, and no supervision group sits within co-location distance of an S-Eval place (the firewall).
2. **Feature budget** ≤ 15 for M2, ≤ 6 for M4 — unchanged.
3. **Monotone constraints** where the direction is known — unchanged.
4. **No calibration on S-Eval.** Radius and tier thresholds are fitted on S-Val and reported on S-Eval with the counter.
5. **Negative controls always printed** — unchanged (shuffled labels ≈ chance; agent-ID-only must under-perform).
6. **Complexity ladder, not a leap:** rules → table → shallow GBM; every rung must beat the previous on S-Val before
   adoption; the rule baseline remains the default that ships.
7. **If operational supervision is too thin** — the 439 "≥2 met confirmations" figure predates F2.2's stricter
   independence tuple, and the honest F2.2 count will be lower — then **no learned ranker ships**, the rule baseline is
   the product, and the experiment reports exactly that. (This is a legitimate, pre-registered outcome.)

---

## 4. What the ranker actually sees (the justification per feature)

| Feature | Why it is there | What would break without it |
|---|---|---|
| `arm`, `granularity`, `arm_rank` | different arms have different reliability (measured per stratum) | the model would treat a town-centroid arm like a rooftop pin |
| text↔locality similarity (jaccard, char-3-gram, ratio) | the only *licence-clean* evidence that the record belongs to a locality; measured to reach 356.7 m median at 65.9% coverage | losing it removes the only arm that competes with the vendor pin |
| `pin_in_text`, `pin_unknown`, `no_digit`, `no_separator`, `outside_town` | record-quality signals; `outside_town` is the strongest T0 predictor of an unplaceable record | the system would confidently place `OUT` records (237 of them, 0% vendor-geocoded) |
| `f_dist_to_town_centroid_m` | bounds an implausible candidate | a "rooftop" pin 4 km outside its town would look acceptable |
| as-of memory features (warm only) | the only features that carry what the field has learned | warm scoring would ignore history; the loop would be decorative |
| **banned:** pin-agreement distance | measured to be a *failure* signal (84.9% of failures land nearer the pin) | it would actively teach the model to prefer wrong places |

---

## 5. The evidence model in detail (M4)

Per visit the model produces two weights and a reason list:

```
w_place  = f(outcome_place_dim, dwell_band, trail_agreement, media_integrity, agent_baseline, stratum)
w_person = g(outcome_person_dim, dwell_band, media_integrity, agent_baseline)
```
* `met_borrower` / `cash_collected` → high `w_place` **only if** dwell ≥ the stratum's realistic band and the trail agrees
  with the check-in (the dataset's own medians: met_borrower 16.6 min vs `address_not_traceable` 1.3 min).
* `locked_premises` / `neighbour_says_shifted` / `no_such_person` → moderate `w_place`, and the *person* dimension may go
  negative (a real, useful signal: "the address is right, the person may have moved").
* `address_not_traceable` → `w_place = 0` **by construction**; it instead sets `record_suspect` and a re-verification
  priority, with a rule (never a model) deciding how far that goes.
* Media integrity (duplicate hashes: FA009's 25.6%) multiplies the weight down; it never zeroes it, and never labels a
  person.
* Agent baseline is applied as a *scoped* multiplier: the agent's own recent behaviour, in a rolling window, so an agent
  who improved is not permanently punished.

Whichever form the weight takes, the **policy version** is stored on every `evidence_score` row, so beliefs can be
re-derived after a policy change without reprocessing trails (`PS3_DATA_ARCHITECTURE.md` §2.3).

---

## 6. How each model fails, and what catches it

| Model | Failure | Detector | Response |
|---|---|---|---|
| M1 matching | matches a locality in the wrong town | town-scoping rule + cross-town block counter | block the match, log it |
| M2 ranker | over-fits the synthetic generator's regularities | nested grouped CV on S-Val; S-Eval firewall; negative controls; small feature budget | hold the model, ship the rule baseline |
| M2 ranker | drifts as address vocabulary changes | PSI on features, ADWIN on error stream [S31][S32] | challenger retrain through the slow loop |
| M3 point fallback | fabricates precision | tier is capped at APPROXIMATE by rule; radius is wide | refusal instead of a point when the prior is weak |
| M4 evidence | over-trusts a coordinated fake | concentration caps; two-confirmation gate; fault injection | block promotion, mark the belief contested |
| M5 integrity | false-positives a legitimate agent | weight (not accusation) + reversible windowed baselines + published clean-visit false-positive rate | unblock automatically as the window rolls |
| M6 calibration | under-covering a stratum | coverage monitor per stratum with n-guard | widen, publish the gap, fall back to parent stratum |
| Any | silent feature drift | receipts + hash-pinned tensor versions | build fails; no reportable number |

---

## 7. Compute and cost shape of the models

* M1/M5 are pure functions: microseconds, no GPU, no external call.
* M2 scores ≤ 25 rows per query with a tree model: sub-millisecond. Training on the full matrix: seconds to a couple of
  minutes on one CPU at this scale.
* M4/M6 are table lookups: microseconds.
* **No model in this architecture requires a GPU.** That is a deliberate cost decision with a correctness justification:
  every problem here is small, tabular and evidence-bound, and the literature's Indian-geocoding results [S9][S11][S13]
  were achieved with hierarchy/graph models over *millions* of traces — a scale at which our data does not exist here.

---

## 8. What would change this architecture (the conditions to revisit)

1. **Real (non-synthetic) data at ≥10⁵ records** with genuine linguistic variety → tier-2 parser and a neural matcher become
   justified; re-run experiment B/I to prove it.
2. **Adjudicated integrity labels** at scale → M5 becomes a learned scorer (never a judge: weights only).
3. **A road graph and a real CRS** → street-level snapping and (then) map matching leave RESEARCH ONLY [S30].
4. **Millions of visits with stable tracking** → bandit-style visit allocation becomes meaningful (currently RESEARCH ONLY,
   because exposure instrumentation is the prerequisite).
5. **A measured failure of the fast loop** (e.g. contradictions resolving badly) → the belief update becomes a review-first
   workflow, i.e. *less* automation, not more.



## 9. Amendment M2 — final data policy (2026-10-07): official-only models and the role contract

1. **Official arms only.** Candidate generation (M1) draws exclusively on the official dataset: the official frozen baseline geocode arm,
   official towns/localities, official landmark/POI anchors, official address-book anchors, official historical field
   evidence, and address memory. No external gazetteer, address database, building raster, map or geocoder may appear as
   an arm, a feature, a tie-breaker, a proof-of-life record on disk, or a cached index
   (`PS3_FINAL_DATA_AND_ARCHITECTURE_FREEZE.md` §DATA `[S95]`).
2. **Shared-column roles bind the feature schema** (`PS3_DATA_ARCHITECTURE.md` §9): `accounts` = exposure/business context
   only (never a coordinate feature); `agents` = integrity/monitoring only (never a location prior); `splits` = evaluation
   only (never labels or features); `lenders` = context only (never a geocoder feature). The feature matrix keeps exactly
   one shared column as a model feature (`address_text`), as audited.
3. **Every future model card states the data policy.** One line, verbatim: *"Trained on the official CreditNirvana PS3
   dataset and its officially assigned shared tables only; no external, scraped or third-party geographic data was used."*
4. **The ranker/fallback hierarchy is unchanged** — shallow LambdaMART (small-data variant) with a logistic-regression
   challenger and a rule baseline; deterministic prior / ridge with a small GBM challenger for the point fallback;
   likelihood-ratio rules first for evidence. This amendment removes a data source, not a model.

---


## Amendment M3b — point-fallback semantics and the ranker interface (2026-10-07)

1. **M3 fallback may not fabricate an address coordinate.** Outputs are limited to: (a) a labelled area anchor
   (`AREA_CONTEXT`), tier capped below address level, radius = the stratum's empirical radius, or (b) no coordinate
   at all with `UNPLACEABLE` + verify-first. The ridge/GBM fallback therefore predicts **only within a candidate's
   support** (e.g. interpolating between two street anchors); where support does not exist, it abstains. Kill
   criterion unchanged: a fallback point that ever ends up in an address-level tier fails the build.
2. **The ranker interface is frozen; the ranker is not.** Every implementation must expose: candidate set in,
   **inspectable per-candidate score**, **reason codes**, deterministic order out. Three implementations compete
   under experiment D: transparent weighted rule (ships by default), logistic challenger, shallow
   LambdaMART/pairwise challenger. Cheapest winner ships; the rule baseline remains a valid production fallback
   forever (no model is ever on the critical path of correctness).
