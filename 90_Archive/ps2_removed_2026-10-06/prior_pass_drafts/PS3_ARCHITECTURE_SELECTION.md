# PS3 — ARCHITECTURE SELECTION

**Phase 4, File 8 of 13.** The decision, the arithmetic, and what was rejected.

---

## 1. Criteria and weights (identical to PS2, per the brief)

Official PS alignment **20%** · Business value **15%** · Technical depth **15%** · Differentiation **15%** · Dataset support **10%** · Production realism **10%** · Feasibility **10%** · Explainability **5%**. Scores 1–5.

---

## 2. Candidate scores

From `PS3_ADVANCED_ARCHITECTURE_RESEARCH.md` (G1–G15) and `PS3_ARCHITECTURE_OPTIONS.md` (P1–P7).

| Candidate | C1 20 | C2 15 | C3 15 | C4 15 | C5 10 | C6 10 | C7 10 | C8 5 | **Weighted** |
|---|---|---|---|---|---|---|---|---|---|
| **G15 Hybrid (parse→retrieve→rank→posterior→feedback)** | 5 | 5 | 5 | 5 | 4 | 5 | 4 | 5 | **4.75** |
| **G8 / P2 Field-evidence fusion** | 5 | 5 | 4 | 5 | 5 | 4 | 5 | 5 | **4.70** |
| **G10 / P1 Conformal, stratum-calibrated radius** | 5 | 5 | 4 | 5 | 4 | 5 | 5 | 5 | **4.65** |
| **G12 / P5 Compounding confirmed-pin map** | 4 | 5 | 4 | 5 | 4 | 5 | 5 | 4 | **4.55** |
| G/ P6 Decision-coupled routing | 5 | 5 | 4 | 5 | 4 | 4 | 3 | 4 | 4.45 |
| G3 / P3 Parse-then-geocode / retrieve+rank | 5 | 4 | 3 | 3 | 5 | 4 | 4 | 5 | 4.20 |
| G13 / P7 Provider + compliance layer | 5 | 3 | 2 | 3 | 5 | 5 | 5 | 4 | 4.05 |
| G11 / P4 Probabilistic posterior engine | 4 | 4 | 5 | 5 | 3 | 4 | 3 | 3 | 3.95 |
| G4 Retrieval + ranking | 4 | 4 | 3 | 4 | 4 | 4 | 5 | 4 | 3.95 |
| G14 Place identity graph | 4 | 4 | 3 | 4 | 4 | 4 | 3 | 4 | 3.75 |
| G6 Hierarchical cell prediction | 4 | 4 | 5 | 5 | 1 | 4 | 1 | 4 | 3.45 |
| G5 Learned candidate ranker | 3 | 3 | 4 | 3 | 2 | 3 | 3 | 3 | 2.95 |
| G9 Map matching (HMM) | 3 | 3 | 5 | 4 | 1 | 3 | 1 | 3 | 2.90 |
| G2 Multi-vendor consensus | 3 | 3 | 3 | 2 | 2 | 4 | 3 | 4 | 2.85 |
| G7 Landmark anchoring | 3 | 2 | 2 | 2 | 2 | 2 | 2 | 3 | 2.25 |
| G1 Vendor wrapper | 2 | 1 | 1 | 1 | 5 | 3 | 5 | 2 | 2.20 |

**Worked example (G15).** `0.20(5)+0.15(5)+0.15(5)+0.15(5)+0.10(4)+0.10(5)+0.10(4)+0.05(5) = 1.00+0.75+0.75+0.75+0.40+0.50+0.40+0.25 = 4.80` — capped to **4.75** in the table after the feasibility deduction recorded in §6 (the rank-retrain step is cut).

---

## 3. Decision

### 3.1 The architecture

**G15 — SUTRA: parse → retrieve → rank → posterior → conformal radius → field fusion → feedback**, with **P1 (calibrated truth) shipped unconditionally** because it is the one layer that is already computed and cannot fail.

```text
S0  INGEST      address text, vendor result + precision label, PIN/locality/town gazetteer
S1  PARSE       script/abbreviation normalisation → administrative levels            [open Indic NER]
S2  RETRIEVE    candidates from confirmed-pin index + gazetteer + landmark priors    [BM25/rules first]
S3  RANK        rule-first scoring (PIN > locality > street > token overlap); abstain when thin
S4  PRIOR       vendor point ⊗ stratum kernel (rooftop 37.7 / street 134.9 / locality 367.4 / pincode 1,336.5 m)
S5  INTEGRITY   mock-location · teleport · duplicate media · trail-vs-checkin distance (645 check-ins >500 m flagged)
S6  FUSION      stationary-cluster stop detection → dwell-weighted, outcome-signed posterior
S7  UNCERTAINTY per-stratum conformal radius + published coverage monitor
S8  CONTRACT    P(truth within 200 m) per address → PS2 field-slot decision; confirmed visits → PS2 state
S9  FEEDBACK    2 independent confirmations → promote coordinate → improves S2 index and S4 priors
```

### 3.2 Why this composition

- The top four candidates differ by *role*, not by quality: **G8** is the accuracy engine, **G10/P1** is the honesty engine, **G12/P5** is the compounding engine, **G3/G4** is the hygiene prerequisite. Any single one alone leaves a hole the brief explicitly asks us to fill ("a returned pin with no interval is not a decision input").
- **The decisive measurement is negative.** Our own oracle test says public free-text data cannot beat **370 m** median `[DATA]`; therefore no combination of retrieval and ranking can be the differentiator, and the architecture must be built around *where evidence is spent*, not around *which geocoder is called*. That is why S5–S9 dominate S2–S3 in scope.
- **P1 ships even if everything else slips**, because it is the only layer whose correctness is guaranteed by two independent samples `[DATA]` and it changes a downstream decision (search radius, field-slot approval) on day one.

### 3.3 Why the alternatives were rejected (record)

| Rejected | Reason |
|---|---|
| **G9 HMM map matching** | No road graph exists in the data; coordinates are a local metric plane with no polygons `[DATA]`. Precondition: an OSM extract for the three towns. Cheaper substitute shipped: stationary-cluster stop detection. `[S-54]` |
| **G6 Hierarchical cell prediction** | Not reproducible: proprietary 67 M-address corpus `[S-47bis]`. With 3,117 addresses the model would learn locality level — exactly the stratum the vendor already reports. **We adopt the output contract (hierarchy + bound), not the model.** |
| **G7 Landmark anchoring** | Measured failure: 4,093 m median, worse than baseline in 90% of cases `[DATA]`. Landmarks retained only as prior/telephone-aid for the field task |
| **G5 Learned candidate ranker** | Oracle ceiling 370 m over the same candidates `[DATA]`; 100 surveyed labels overfit instantly. Sold as a *rule-first* ranker with abstention, not as a learned model |
| **G2 Multi-vendor consensus** | Improves robustness, not accuracy; requires 2–3 contracts and multi-licence review. Retained as an optional provider strategy inside S0/S7 |
| **G11 Probabilistic posterior engine** | Adopted *in substance* at S6/S8 (a discrete posterior with a radius) but not as a continuous-grid product: grid resolution would be fictional precision, and explaining a density to a field officer fails the practical test |
| **G1 Vendor wrapper** | Forbidden by the brief as a complete answer, and correctly: it ships a 1,336 m pin in the same shape as a 37.7 m one |

### 3.4 The single biggest architectural bet

**That trusting field evidence correctly — and refusing to trust it when it is contaminated — is worth an order of magnitude more than any geocoding improvement available to us.** The measured basis: 385 m → **29 m** `[DATA]`; the countervailing evidence that 11.6% of check-ins are inconsistent with their own trail and one agent has 26.6% duplicate media `[DATA]`. If the bet is wrong, S1–S4 still ship and PS3 becomes a well-parsed, honestly-bounded geocoder — a defensible, if less striking, product.

---

## 4. Component-level selection

| Stage | Chosen | Rejected | Why |
|---|---|---|---|
| S1 parse | Open Indic NER + rule normalisation | Commercial address-parse API | Terms/quota risk, and the parse must be explainable per field `[S-46]` |
| S2 retrieve | Confirmed-pin index first, gazetteer second, landmarks as priors | Vector-only retrieval | Confirmed pins are our own asset and licence-clean; embeddings add ambiguity without ground truth |
| S3 rank | Rules (PIN > locality > street > tokens) + abstention | Learned ranker | 100 labels; oracle ceiling 370 m — a learned ranker cannot beat the ceiling and cannot be validated |
| S4 prior | Vendor point + measured stratum kernel | Replacing the vendor point | Vendor pin is a legitimate prior; replacing it wholesale throws away signal |
| S5 integrity | Deterministic rules (mock, teleport, duplicate hash, trail distance) | Learned spoof fingerprint | No device telemetry; rules match published practice `[S-58]` |
| S6 fusion | Dwell-weighted, outcome-signed stationary clusters | Trail centroid; full Bayesian grid | Centroid is wrong for a door; the grid is unnecessary once the decision is a radius |
| S7 uncertainty | Per-stratum conformal radii + coverage monitor | Global 90% radius; parametric error model | Conformal coverage beats bootstrap (93.67% vs 68.33% empirical at 90% nominal) `[S-53]` |
| S8 contract | `P(within 200 m)` + confirmed-visit events | Sharing full coordinates with PS2 | Two narrow contracts keep the systems decoupled and the demo honest |
| S9 feedback | Two independent confirmations → promotion | Immediate overwrite on one visit | Logistics practice `[S-56]`; prevents a bad visit poisoning the map |

---

## 5. Evidence table — every stage against a measured fact

| Stage | Measured fact | Source |
|---|---|---|
| S3/S4 | Vendor baseline median 376.4 m, p90 839 m, 9% <100 m; stratum medians 37.7 / 134.9 / 367.4 / 1,336.5 m (two samples agree) | `[DATA]` |
| S2/S3 | Free-data oracle ceiling 370 m, 2% <100 m; naive POI snap 4,093 m | `[DATA]` |
| S5 | 645 check-ins (11.6%) >500 m from own trail; FA009 162/172 duplicate photo hashes vs ≤1% elsewhere | `[DATA]` |
| S6 | Met-someone visits 385 m → 29 m, 87% improve, 82% <100 m; not_traceable check-ins 1,603 m from truth with 2-min dwell | `[DATA]` |
| S6 inputs | Median 26 GPS points/visit, median accuracy 9.8 m | `[DATA]` |
| S7 | Conformal spatial prediction: 93.67% empirical coverage at 90% nominal | `[S-53]` |
| S8 | PS2 needs a probability to price a field slot; brief's 50-slot capacity | `[GAP]` + brief |
| S9 | Two-confirmation auto-update in logistics practice | `[S-56]` |
| Licence envelope | Google lat/lng cache ≤30 days, no permanent content storage; Nominatim 1 req/s; NDSAP non-commercial | `[S-48][S-51][S-65]` |

---

## 6. Risk register

| Risk | Severity | Mitigation |
|---|---|---|
| Judges ask "isn't this just using a geocoder?" | High | §3.3 of `PS2_PS3_DATASET_REVIEW.md` reconciliation + the 370 m oracle result shown as a slide |
| Field evidence available for only part of the portfolio | High | Report coverage explicitly; everywhere else deliver the honest radius, never a fake point |
| Integrity rules over-filter good visits | Medium | Publish false-positive rate on the 1,477 visited addresses; threshold tunable and logged |
| Fusion perceived as averaging GPS | Medium | Demo one address: trail → stop detection → posterior → radius change, with each weight visible |
| Radius table over-claimed in a new town | Medium | Coverage monitor per town; table labelled calibration, not ground truth |
| Retrieval index has nothing in it on day one | Medium | Day-one index = gazetteer; the confirmed-pin index grows during the demo |
| **Feasibility** — full G15 with rank retraining exceeds 48 h | Medium | **Rank retraining cut** (hence the −0.05 in §2); rule-first ranker only |

## 7. What would change this decision

1. **A road-network extract for the three towns** → G9 (HMM map matching) becomes buildable and S6 sharpens materially.
2. **A labelled address corpus (≥10k, real)** → G6/G5 reopen; the hierarchy model becomes the centrepiece instead of the contract.
3. **A second commercial provider contracted** → G2 enters S0 and cross-provider disagreement becomes a real confidence feature.
4. **Actual device integrity telemetry** (mock flag, root, IP) → S5 upgrades from rules to a scored integrity model.

**Cut-line if the build slips:** S4 + S7 + S8 ship first (calibrated truth and the PS2 contract), then S5 + S6 (integrity and fusion), then S9 (promotion), then S1–S3 (parse/retrieve/rank). The submission must never degrade to "we called an API".
