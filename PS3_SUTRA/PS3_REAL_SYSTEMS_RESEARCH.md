# SUTRA — REAL SYSTEMS RESEARCH

Reverse-engineering the systems that already solve parts of this problem, with the commission's 13 questions applied
to each: **problem · data · architecture · assumptions · failure modes · incomplete-address behaviour · uncertainty ·
learning from observations · poisoning prevention · compute · operating cost · buildability · the honest simplification.**

Sources are cited as `[S-nn]` against `PS3_SOURCE_REGISTER.md`. Claims labelled `[V]` verified from a source, `[I]` inference,
`[A]` assumption, `[?]` unknown. `[VENDOR CLAIM]` means the number comes from the vendor and is never treated as a measured
result of ours.

---

## 1. The commercial geocoders (Google, Mapbox, HERE, TomTom, Mappls)

**Problem solved.** Resolve a written address (or a coordinate) to a point, with some statement of how good that point is.
Google splits the job into two products: *Geocoding* returns a location with a `location_type`
(`ROOFTOP` / `RANGE_INTERPOLATED` / `GEOMETRIC_CENTER` / `APPROXIMATE`) while *Address Validation* returns
`validationGranularity`, `addressComplete`, `hasInferredComponents` and a verdict [S1][S2]. Mapbox returns per-component
`match_code` (exact/high/medium/low/plausible) with `plausible` meaning *interpolated or extrapolated* — and sells
"permanent geocoding" as a distinct, cacheable product [S3][S4]. HERE and TomTom use the same shape: a confidence value
plus a match-level indicator, batch endpoints for bulk [S5]. Mappls (MapIndia) returns a 6-character **eLoc** — a
stable, shareable India-wide code for a location [S6].

**Data required.** A large authoritative address/road/POI reference base per country, plus interpolation ranges along
street segments. Mapbox states rooftop accuracy as *"greater than 70% in key metro areas"* [S4] — i.e. quality is a
coverage-dependent promise, not a global property.

**Architecture (inferred from the response contract).** Parse → normalise → match against a reference index at several
granularities → interpolate within a street range when the exact point is unknown → attach a confidence vocabulary. The
contract is the tell: when a system can return `RANGE_INTERPOLATED`, its internal state is not "a point", it is
"a point plus the reason it is that point" [I].

**Assumptions.** That the reference base is authoritative; that house-number ranges are ordered along a segment; that a
road graph exists and is correct.

**Failure modes.** Ambiguous locality names across regions; missing house numbers; addresses whose anchor is a landmark
("opposite the water tank"); text in a script the index does not carry; and — the one that matters most to us — a
confident wrong answer, because a coarse match presented at the wrong granularity is indistinguishable from a good one
unless the caller reads the granularity field. Google's own product split exists because of this [I].

**Incomplete-address behaviour (`[V]` on the contract).** They do not refuse; they degrade *explicitly*: partial match,
`addressComplete=false`, `hasInferredComponents=true`, `APPROXIMATE`, `plausible`. **This is the single most transferable
design decision in the whole survey:** the industry's answer to incompleteness is a *granularity vocabulary*, not an error.

**Uncertainty representation.** A discrete vocabulary (level) plus, in Address Validation, an inferred-components flag.
No calibrated numeric radius is exposed. Our audit shows why a numeric radius matters: the pincode stratum here has a
1,375.8 m median error while the street stratum has 108.6 m — one "accuracy" number cannot describe both
(`PS3_DATA_AUDIT.md` §2.6). SUTRA adds a *measured* radius per stratum and per evidence tier [S90][S91].

**Learning from observations.** Not observable from the contract; commercial geocoders largely update through reference-
base refreshes and (for logistics-facing products) customer corrections. There is no public evidence that a consumer
geocoder updates its own index from an individual field visit [I]. **This is the gap SUTRA fills** — not "better
geocoding", but *learning from visits with an auditable memory*.

**Poisoning prevention.** Invisible to a caller; the relevant lesson is that a vendor's answer must not become our truth
merely because it is consistent [S8 forbids us from storing it beyond a cache window].

**Compute / operating cost.** Centralised index serving; the cost is in the reference base and its refresh, not in the
query. For us the cost orientation is inverted: our index is small (three towns), our *evidence* is the expensive part.

**Buildability for us.** Replacing them is not the goal. We consume a vendor pin as one arm, and we must be able to work
without it (the audit's 237 `OUT` records have no pin at all).

**Honest simplification.** *Do not build a global geocoder.* Build the layer they do not have: a per-town, per-record,
field-verified, uncertainty-carrying memory.

---

## 2. Indian production geocoding: GeoIndia (Meesho), SAGEL, Shiprocket, Delhivery

**GeoIndia v1/v2** [S9][S10]: predicts **hierarchical H3 cells** rather than raw coordinates for Indian addresses —
a hierarchy beats regression on the same task, and v2 fuses a graph model with a language model. Company material states
the label source at scale is **delivery traces** from their own operations. That is exactly the structure SUTRA assumes:
the labels come from the field, not from a survey.
`[V]` this validates two of our choices: (a) output should be a *granularity-aware* object, not a bare point; (b) the
field is the label factory. `[I]` it also warns: a delivery trace is a *proxy* label, and their published precision
reflects that — no Indian paper claims survey-grade truth.

**SAGEL** [S11] reports 64.3% of addresses within 100 m versus Google's 23.8% on its benchmark. Two readings, both kept:
`[V]` a specialist system can beat a general one by a wide margin; `[A]` the comparison's ground truth is not ours and
the address population is not ours, so **we may not import that number as our target**. Our own floor is the vendor pin
on our own 100 surveyed records: median 376 m, 9% within 100 m.

**Shiprocket** [S13]: published claims of 72.69% within 100 m and 90.57% within 500 m `[VENDOR CLAIM]`. What we take from
it is the **reporting unit**: a hit-rate curve, not a single average error. Every SUTRA experiment reports <50/<100/<250/<500 m
plus a calibrated radius.

**Delhivery (GeoNaksha / Maps)** [S14]: address validation and verification for logistics, with visit-history based
verification and a developer-facing API `[VENDOR CLAIM]` on "4 billion+ deliveries". Two mechanisms are visible: an
address *verification* product, and a *visit history* that can corroborate a point. That is our fast loop described from
the outside, without the integrity weighting or the uncertainty contract.

**Transferable lesson.** The Indian market's consensus is: parse with local vocabulary (gali, colony, block, sector,
"opposite the temple"), anchor on landmarks ([S7] describes exactly this), and accept that the field is the best label
source available. SUTRA's differentiation is not in parsing; it is in **what is remembered afterwards and how much it is
trusted** (§6, §7).

---

## 3. Address parsing and normalisation systems

| System | Approach | Reported quality | Lesson for us |
|---|---|---|---|
| **libpostal** [S15] | averaged perceptron, multilingual, C | 98.9% full-parse accuracy on its benchmark | parsing is a solved-enough problem; it is also an *optional* dependency, not the core |
| **deepparse** [S16] | neural, fine-tunable | ~99% on trained countries, slower | the accuracy/latency trade is real; fine-tuning per country is a maintenance cost |
| **IndicBERTv2-Subword + CRF** (`addressparser`) [S12] | small transformer + CRF, <30 ms | field-level Indian parsing | the Indian case is offline-solvable and cheap |
| Practitioner comparison [S17] | IndicBERTv2-CRF vs 6-layer classifier | 4.6 s vs 19 ms for similar field accuracy | **~240× latency for the same job** — the reason our tier-1 parser is rules + gazetteer |

**Design decision (locking the §12 pruning).** Tier 1 rules + gazetteer ship; a statistical parser is BUILD IF TIME and is
scored, not assumed; an LLM parser is RESEARCH ONLY. The dataset's addresses are semi-structured (median 67 characters,
76.8% carry a house-number-like token, only 24.9% lack a comma), so a rule engine plus a closed gazetteer of 36 localities,
3 towns and 240 landmarks covers the bulk of the signal at microsecond cost. The audit's counters are the argument:
a parser's value must be demonstrated on *unresolved* records, and there are few of them here.

---

## 4. Retrieval and ranking (candidate generation → reranking)

* **RRF** [S18]: fusing ranked lists by rank preserves complementarity without score calibration — used here for *candidate
  ordering only*, never as a final score (rank fusion cannot express "40 m vs 4,000 m").
* **Two-stage practice** [S19]: recall stage is cheap, the reranker is 100–1000× costlier — so the expensive model must
  see few candidates. Our budget: ≤25 candidates per address.
* **LambdaMART / `rank:ndcg`** [S20]: listwise ranking with gradient-boosted trees; for small data, pairwise losses with careful
  grouping are more stable — directly relevant because our labelled set is 100 surveyed records plus field evidence.
* **Unbiased LambdaMART** [S21]: propensity-weighted exposure correction. Our exposure is *field-visit* exposure, and the
  audit measured it to be demand-driven (19.9% → 84.8% by DPD band), so this is not a theoretical concern.
* **Probabilistic record linkage** [S22]: Fellegi–Sunter with per-field weights, no labels needed, fully explainable —
  the right tool for matching an address text to a gazetteer entry and for deciding when two records are the same place.
  It also gives us *auditability*, which a neural matcher does not.

**Transfer.** Candidate generation is a small, auditable, deterministic set of arms; ranking is a learned scorer over a
few dozen candidates; the fusion is explainable. This is the shape our design takes (`PS3_MODEL_ARCHITECTURE.md`).

---

## 5. Probabilistic geocoding and uncertainty

* **GeoConformal prediction** [S24]: geographically weighted split conformal attains 93.67% empirical coverage at a 90%
  nominal level, versus 81% for a plain bootstrap; **GeoXCP** [S25] adds local approximate exchangeability and holds >75%
  coverage under model-induced noise. Two consequences: (a) a radius must be produced with a *measured* coverage and a
  spatial-weights scheme, (b) plain bootstrap under-covers — which is exactly how a system ends up claiming "90% within
  500 m" without it being true.
* **Android `getAccuracy()`** [S26] is a **68% radial confidence**, and the platform exposes `isMock()` — so a GPS
  "accuracy" value is a weak claim, and spoofing leaves *some* checkable trace.

**The consensus pattern across commercial and academic systems:** report uncertainty as a *discrete level plus a
granularity*, and never as a single accuracy figure. SUTRA does that, then adds a measured radius with reported coverage,
which none of the surveyed products expose.

---

## 6. Systems that learn from field observations

| System class | Mechanism | What it proves | What it does not do |
|---|---|---|---|
| Delivery platforms (Delhivery, Shiprocket, Meesho delivery traces) [S10][S13][S14] | visits/deliveries generate labels; addresses get corrected over time | the field is the label factory, and closed loops exist in production | no published evidence of *integrity-weighted* updates, no memory contract, no calibrated radius |
| Active-learning deployments [S36][S37] | hybrid entropy + diversity + random sampling reached target with ~2/3 of the pool | *choosing which visits matter* is a validated practice | none of them handle spoofed/duplicated evidence |
| Logged-bandit evaluation [S38] | propensity weighting repairs biased exposure | a policy's effect is not measurable from a naively logged sample | rarely applied in field operations |
| Field-force apps [S50] | offline-first capture, mandatory geotagging, liveness/photo verification, beat plans | Indian field ops already *collect* geo-tagged, photo-backed evidence | collection ≠ learning: no weighting, no contradiction handling |
| Geocoding status + manual review [S48] | "approximately geocoded → flag → confirm before dispatch"; dispatcher corrections captured permanently | status vocabulary + human review + permanent correction capture is shipped practice | no probabilistic belief, no decay, no negative-evidence semantics |
| Two-confirmation auto-update [S49] | auto-updating a geocode after two independent confirmations | matches our fast-loop promotion rule | vendor/practitioner claim, not a measured study |

**Where SUTRA is genuinely differentiated** (see `PS3_NOVELTY_AND_DIFFERENTIATION.md`): the combination of
(i) an append-only *address memory* with decay and contradiction rules, (ii) integrity-weighted evidence where the
weight is explicit and auditable rather than binary, (iii) negative evidence that raises *re-verification value* instead of
moving a point, (iv) a measured radius with reported coverage, and (v) a slow loop with drift gates, cooldown and rollback.
Each piece exists somewhere in the literature or in practice; the packaged, auditable combination does not appear in the
systems surveyed.

---

## 7. Data quality, fraud and poisoning prevention

* Spoofing is detected by **cross-signal inconsistency**, not by GPS alone: mock-location flags, MDM app scans, GPS-vs-IP/
  Wi-Fi mismatch, teleport/implausibility, reused photos, impossible stationarity [S27], with `isMock()` available at the
  platform level [S26].
* The audit of our own dataset shows the same lesson from the other side: the planted integrity anomaly is **156 reused
  photo hashes (25.6%) for one agent** while its GPS looks perfect (max implied speed 32 km/h, no off-trail check-in)
  [S90]. **A GPS-only integrity layer would have caught nothing.**
* Consequence: "weight, don't accuse" ([S27]'s own framing is detection, ours is weighting) — evidence carries a
  multiplier, a flag is raised, and no coordinate is moved or rejected on one signal.

---

## 8. Dynamic learning / MLOps patterns

* Drift detectors (ADWIN, DDM/EDDM, Page-Hinkley) work on any scalar stream; **uncertainty-based triggers cut retrains
  from 345 to 16** in a published comparison [S31][S32] — the design lesson is that *the trigger* is the costly decision.
* Scheduled **full retrain with warm start** is safer and more governable than continuous online updates for tabular
  models; label lag must be excluded from the window; champion/challenger gates with cooldown and rollback are the norm
  [S33][S34][S35].
* Registry-level alias promotion (`champion`, `challenger`) gives promotion and rollback without code deploys [S34].

**Applied to SUTRA:** the fast loop is *not* a model update — it is a belief update over an append-only store
(milliseconds, no training). The slow loop is the only place a model changes, and it is gated (§8 of
`PS3_DYNAMIC_LEARNING_ARCHITECTURE.md`). This directly answers the commission's warning: **never retrain after every visit.**

---

## 9. Cross-system synthesis — the ten transferable decisions

1. Express completeness as a **granularity vocabulary**, never as an error code (Google, Mapbox, HERE, TomTom, Mappls).
2. Attach **the reason** to every coordinate (match code / location type / eLoc), not only the coordinate.
3. Treat rooftop quality as **coverage-dependent**, not as a property of the engine (Mapbox's own wording).
4. Report accuracy as a **hit-rate curve** (Shiprocket, SAGEL) — never one average.
5. Use **hierarchical labels** where the input is coarse (GeoIndia's H3 cells).
6. Let the **field generate labels**, but treat a trace as a proxy, not as truth (GeoIndia's delivery traces; our audit's
   1,603 m failure signature).
7. Predict **uncertainty with a spatially aware method**, because bootstrap under-covers (GeoConformal, GeoXCP).
8. Detect integrity problems by **inconsistency across signals**, not from GPS alone (spoofing practice + our own FA009).
9. **Weight** evidence instead of accusing (our policy) and don't auto-update a geocode on one signal (two-confirmation
   practice [S49]).
10. Keep the loop **two-speed**: instant belief, gated retraining (drift/registry practice [S31]–[S35]).

## 10. What this research forbids us from claiming

* We may not claim "we built a geocoder" as novelty — the world is full of them [S1]–[S6].
* We may not claim a measured India-wide accuracy from SAGEL/Shiprocket/GeoIndia numbers — they are different datasets and,
  in two cases, vendor claims [S11][S13].
* We may not claim that field GPS is truth: within this dataset it follows the pin on failed visits 84.9% of the time [S90].
* We may not claim hidden spoof detection: our dataset contains one detectable anomaly type and no spoof at all [S90].
* We may not claim LLM-based geocoding as a plan: nothing in the survey shows it beating a retrieval + ranking system on
  this task, and the cost/latency evidence [S17] points the other way.
