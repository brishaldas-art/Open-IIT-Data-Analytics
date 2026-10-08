# PS3 — ADVANCED ARCHITECTURE RESEARCH

**Phase 4, File 3 of 13.** Fifteen genuinely different architectures for PS3, compared before any is chosen.

**Read with:** `PS2_PS3_DATASET_REVIEW.md` §2 (the official PS3 statement and why our framing is location-intelligence for field collections, not "build a geocoder"), §4 (PS3 evidence) and §5 (traps). Numbers tagged `[DATA]` come from the audited synthetic dataset via `dataset_audit.py p3`. Vendors/papers are tagged `[S-nn]` (mapped in `ARCHITECTURE_RESEARCH_BIBLIOGRAPHY.md`).

**The three facts that decide everything below.**

1. **The baseline is not broken, it is uncalibrated.** Vendor baseline error on 100 surveyed addresses: mean **532.7 m**, median **376.4 m**, p90 **839 m**; only 9% land within 100 m `[DATA]`. But the vendor also tells us its own `precision` per address, and that field is *good*: median error by labelled precision — rooftop **37.7 m**, street **134.9 m**, locality **367.4 m**, pincode **1,336.5 m** (independently reproduced on the surveyed sample: 25.6 / 108.6 / 385.9 / 1,375.8) `[DATA]`. The vendor's label carries the stratum; the system does not use it. That is the whole opportunity in one line.
2. **Free data cannot beat 370 m.** Candidate/landmark scoring from public free-text sources lands at **383 m** median; the *oracle over the candidate set* is **370 m** with 2% under 100 m; naive landmark snapping is **4,093 m** (worse than baseline in 90% of cases) `[DATA]`. No re-ranking architecture over free text crosses the gap. **The remaining error is field evidence.**
3. **Field evidence does beat it — by an order of magnitude, where it exists.** On visits where the agent met someone, the point can be placed at a **median 29 m** of the surveyed truth vs the vendor's 385 m on the same addresses; 87% of those cases improve and 82% land under 100 m `[DATA]`. So the architecture is not "geocode better"; it is **choose where to spend field evidence and merge it correctly**.

---

## The fifteen architectures

| ID | Architecture | Thesis |
|---|---|---|
| **G1** | Vendor wrapper | Call the API, store the pin |
| **G2** | Multi-vendor consensus | Cross-check providers; agreement = confidence |
| **G3** | Parse-then-geocode | Normalise/parse the Indian address first, then geocode |
| **G4** | Retrieval + ranking | Treat geocoding as search: retrieve candidates, rank them |
| **G5** | Learned candidate ranker | Train LambdaMART/GBM to rank candidates against observed truth |
| **G6** | Hierarchical cell prediction | Predict the administrative cell (H3/ward/local street), then resolve locally |
| **G7** | Landmark/POI anchoring | Use landmarks as anchors and infer offsets |
| **G8** | Field-evidence fusion | Bayesian fusion of GPS trail, dwell, photo, and outcome sign |
| **G9** | Map matching (HMM) | Snap the trail to a road graph to infer where the agent actually went |
| **G10** | Conformal uncertainty | Distribution-free honest radius per address |
| **G11** | Probabilistic geocoding | A posterior *distribution* over coordinates, not a point |
| **G12** | Feedback / active learning | Auto-promote confirmed coordinates; learn which strategy wins per stratum |
| **G13** | Compliance-grade provider layer | Pluggable providers, cache/permanence rules enforced in the data model |
| **G14** | Place identity graph | Resolve addresses↔buildings↔units as entities across the portfolio |
| **G15** | **Hybrid**: parse → retrieve → rank → posterior + conformal radius → field fusion → feedback | The recommended end-to-end shape |

---

## G1. Vendor wrapper

```
address_text ─► Google/Mappls API ─► {lat, lng, precision, place_id} ─► store as point
```

| Attribute | Assessment |
|---|---|
| **Accuracy** | Median 376 m; 9% <100 m `[DATA]` |
| **Uncertainty** | Only the vendor's categorical `precision`; no radius, no coverage guarantee |
| **Multilingual / Indian-address handling** | As good as the provider; Google's India coverage is the reference point `[S-49]`, Mappls is India-native with an address standard (eLoc) `[S-50]` |
| **Data needs** | None |
| **Robustness** | Single point of failure; quota and outage visible to the agent |
| **Online/offline** | Online only (and licence-bound: Google lat/lng cache ≤30 days, no permanent storage of other content `[S-48]`) |
| **Learning** | None |
| **Explainability** | Low (`partial_match`, `location_type` are weak signals `[S-47]`) |
| **Complexity / feasibility** | Trivial / trivial |
| **Role** | **The floor.** The brief forbids "call an API and return the pin" as a solution — correctly, because it is what is already happening |

**Failure modes.** Silent wrong pin (the 1,336 m pincode stratum is returned as confidently as a rooftop one); the agent cannot tell 30 m from 1.3 km; permanent-storage licence breach if cached naively.

---

## G2. Multi-vendor consensus

```
address ──► provider A ─┐
        ──► provider B ─┼──► agreement clustering ──► consensus + confidence
        ──► provider C ─┘
```

| Attribute | Assessment |
|---|---|
| **Accuracy** | Improves the *median* only if providers make independent errors. Evidence does not support that assumption strongly `[INFERENCE]`; free-form candidate sets in our sample could not beat 370 m even with an oracle `[DATA]` |
| **Uncertainty** | Real signal: cross-provider distance is a usable disagreement score |
| **Data needs** | 2–3 provider contracts, per-request cost, licence review per provider `[S-48][S-51]` |
| **Robustness** | Best-in-class against single-vendor outage |
| **Online/offline** | Online |
| **Learning** | None beyond recalibrating thresholds |
| **Explainability** | Good — "two providers agree within 50 m; the third is 1.2 km away" |
| **Complexity / feasibility** | Low / easy — but cost and terms are the blocker |
| **Differentiation** | Low: it is a purchasing decision, not an architecture |

**Failure modes.** Providers sharing a common base dataset produce false agreement; three bills; a consensus point can still be systematically wrong along the same street.

---

## G3. Parse-then-geocode

```
raw address ─► normalise script/abbreviations ─► NER (unit, building, street, locality, city, PIN) ─► structured fields
             ─► geocode each field level independently ─► compose
```

| Attribute | Assessment |
|---|---|
| **Accuracy** | The dominant error source in Indian addresses is *parsing*, not geocoding `[S-45][S-46]`. Public tooling exists: `addressparser` (IndicBERTv2-SS + CRF, <30 ms) `[S-46]`, Shiprocket's open IndicBERT address NER `[S-13bis]` |
| **Uncertainty** | Per-field: unknown PIN ≠ unknown street |
| **Multilingual** | **The strong point.** Handles Devanagari/Bengali/transliteration, which the vendor alone often does not |
| **Data needs** | The address corpus we have (3,117 addresses) plus a gazetteer |
| **Robustness** | Degrades gracefully: unparsed → fall back to whole-string geocode |
| **Online/offline** | Fully offline-capable (a real advantage: privacy and cost) |
| **Learning** | NER model is pretrained; a small amount of fine-tuning is possible, but the dataset has no parse-level labels `[DATA: GAP]` |
| **Explainability** | **High** — the parse *is* the explanation |
| **Complexity / feasibility** | Medium / feasible (open weights) |
| **Differentiation** | Medium — most teams will dump the raw string into an API |

**Failure modes.** Mis-parse silently attaches the right street to the wrong locality; the CRF is only as good as its training distribution (Indian postal corpora, not collections-specific).

---

## G4. Retrieval + ranking

```
query (parsed address) ─► BM25/embedding retrieval over gazetteer+POI+past-verified pins ─► top-k candidates
                       ─► rank ─► return best, or "no confident candidate" ─► field task
```

| Attribute | Assessment |
|---|---|
| **Accuracy** | Ceiling measured: oracle over our candidate sets = 370 m median, 2% <100 m `[DATA]`. Retrieval is necessary but **not sufficient** |
| **Uncertainty** | Margin between top-1 and top-2 is a usable confidence feature |
| **Data needs** | A gazetteer: PIN↔locality↔town (present: 3 towns, 36 localities, 240 POIs `[DATA]`), Overture/open addresses `[S-52]`, India Post directory (non-commercial NDSAP terms `[S-65]`) |
| **Robustness** | Good: an empty candidate set is a legitimate, informative output |
| **Online/offline** | Offline; can be precomputed per PIN |
| **Retrieval vs ranking** | This is the correct *mental model* for the problem `[S-46bis, BM25/retrieve-rerank]` — but see G5 |
| **Explainability** | High — candidates with scores |
| **Complexity / feasibility** | Medium / feasible |
| **Differentiation** | Medium-high as a *framing*: geocoding is search, and search outputs candidates, not answers |

**Failure modes.** A confident top-1 from a degenerate candidate set (all 14 POI names repeat in `landmarks_poi.csv` `[DATA]`); BM25 on transliterated text matching the wrong script variant.

---

## G5. Learned candidate ranker

```
candidates ─► features (token overlap, PIN match, locality distance, POI proximity, vendor precision, past confirmations)
           ─► LambdaMART / GBM ─► ranked list
```

| Attribute | Assessment |
|---|---|
| **Accuracy** | The honest ceiling is again 370 m `[DATA]` — **a ranker can only recover what retrieval offered**. This is the single most important negative result of Phase 4 for PS3 |
| **Uncertainty** | Rank margin; not a calibrated error radius |
| **Data needs** | Pairs (candidate, truth). We have 100 surveyed addresses `[DATA]` — enough to *demonstrate*, not to train a generalisable ranker |
| **Robustness** | Overfits fast at n=100 |
| **Online/offline** | Offline |
| **Learning** | Yes, but label-poor |
| **Explainability** | Medium |
| **Complexity / feasibility** | Medium / feasible as a demo, **not defensible as a claim** |
| **Differentiation** | Medium |

**Failure modes.** Reporting an improvement measured on the same 100 surveyed points it was tuned on; a ranker trained on locality-level candidates learning "prefer the town centre".

---

## G6. Hierarchical cell prediction *(GeoIndia-style)*

```
address ─► predict hierarchy: PIN ─► ward/zone ─► H3 cell (res 8–10) ─► local street ─► building
        ─► point = cell centroid, radius = cell size
```

| Attribute | Assessment |
|---|---|
| **Accuracy** | GeoIndia reports >50% mean and >85% p99 error reduction vs Google on 67 M addresses `[S-47bis]`, with production gains self-reported by Meesho; an earlier ACL Industry paper predicts H3 cells and was the origin of the approach `[S-47]`. **Not reproducible here**: the corpus is proprietary |
| **Uncertainty** | **Excellent** — a cell *is* a radius; error is bounded by construction |
| **Multilingual** | Strong (built for Indian addresses) |
| **Data needs** | Large labelled corpus + hierarchy gazetteer — the blocker |
| **Robustness** | High: hierarchical fallback (street fails → locality still returned) |
| **Online/offline** | Offline, fast (cell classification) |
| **Learning** | Yes, supervised, data-hungry |
| **Explainability** | High — "we are confident of the street, not the building" |
| **Complexity / feasibility** | High / **research-only at our scale** |
| **Differentiation** | Very high if it could be built — which is why we steal the *output contract* (hierarchy + bound) and not the model |

**Failure modes.** With 3,117 addresses the hierarchy is learnable to locality level only — which is exactly the 367 m stratum the baseline already produces.

---

## G7. Landmark / POI anchoring

```
address mentions landmark ─► find POI ─► apply relational offset ("behind", "opposite") ─► pin
```

| Attribute | Assessment |
|---|---|
| **Accuracy** | **Measured failure: 4,093 m median, worse than baseline in 90% of cases `[DATA]`** — because the POI table is sparse (240 rows, 14 repeated names, incomplete per the README) and the relational offsets are mostly absent from the text |
| **Uncertainty** | High, and not quantifiable from the data |
| **Data needs** | A real POI/GIS layer with attributes; we have a demo table |
| **Robustness** | Poor |
| **Online/offline** | Offline if the POI table is licensed |
| **Explainability** | High but wrong |
| **Complexity / feasibility** | Low / **do not build as an accuracy play** |
| **Differentiation** | None |
| **Correct use** | Landmarks as **candidates and priors for the field task** ("the agent's search radius shrinks around the named landmark"), never as automatic coordinate correction `[DATA]` |

---

## G8. Field-evidence fusion

```
prior: vendor point + precision stratum radius
evidence:  GPS trail (accuracy per point) │ dwell time │ outcome sign │ photo hash │ landmark text
            ──► spatial likelihood per evidence item ──► posterior mean + credible radius
```

| Attribute | Assessment |
|---|---|
| **Accuracy** | **The measured win:** 385 m → **29 m** median on met-someone visits; 87% improve; 82% <100 m `[DATA]`. GPS itself: median 26 points per visit, median `accuracy` 9.8 m `[DATA]` |
| **Uncertainty** | Native: the posterior has a spread; recompute the conformal radius after fusion |
| **Multilingual** | Not applicable |
| **Data needs** | `visit_gps_points.csv` (160,406 rows, accuracy per point), `field_visits.csv` (5,578 visits, 16 outcome codes) — both present |
| **Robustness** | Must be engineered against the poison trap: `address_not_traceable` check-ins sit **1,603 m** from truth and 195 m from the pin with **2-minute dwell**, i.e. a negative outcome *manufactures* a false location `[DATA]`. Rule: weight by outcome sign **and** dwell, and never let a negative outcome move a point |
| **Online/offline** | Offline (on-device or nightly) |
| **Learning** | Likelihood weights are estimated from 1,477 visited addresses; calibration is empirical, not learned |
| **Explainability** | **High** — each evidence item contributes a visible weight |
| **Complexity / feasibility** | Medium / **yes, this is the core PS3 build** |
| **Differentiation** | **Highest.** No reviewed competitor closes a 385 m → 29 m gap with in-house evidence; the closest analogue is logistics' two-confirmation geocode auto-update `[S-56]` |

**Failure modes.** (1) Trusting a spoofed trail: 645 check-ins (11.6%) are >500 m from their own trail; FA009 has 162/172 duplicate photo hashes (26.6% vs ≤1% elsewhere) `[DATA]` → integrity checks are mandatory (mock-location flag, cross-signal inconsistency, teleport, duplicate media) `[S-58]`. (2) Averaging the trail: the apartment door is not the trail centroid. (3) Letting a single visit overwrite a pinned address.

---

## G9. Map matching / trajectory inference (HMM)

```
raw GPS trail ─► HMM over road/segment graph ─► matched path ─► arrival segment ─► candidate doors on that segment
```

| Attribute | Assessment |
|---|---|
| **Accuracy** | The right tool for *where the agent went*; the deliverable we need is narrower — the **stop point and the dwelling segment**. Standard HMM map matching `[S-54]` |
| **Uncertainty** | Path probability; segment-level ambiguity on dense streets |
| **Data needs** | A road graph. **We do not have one** `[GAP]`; the coordinates are a local metric plane with no polygons `[DATA]` |
| **Robustness** | Sensitive to accuracy outliers and to the 11.6% integrity-flagged check-ins |
| **Online/offline** | Offline, batch |
| **Learning** | Emission/transition parameters are tunnable from 26 points/visit |
| **Explainability** | Medium |
| **Complexity / feasibility** | High / **not in 48 h without a road graph** |
| **Differentiation** | Medium |
| **Cheaper substitute that gets 80% of it:** dwell-clustering of the trail (stop detection) — find the stationary clusters, take the densest one with a positive outcome, intersect with the vendor's street-level candidate interval |

**Failure modes.** Matching to a wrong but nearby road; assuming the phone's location equals the door.

---

## G10. Conformal uncertainty

```
calibration set (100 surveyed addresses) ─► nonconformity scores ─► per-stratum radius with finite-sample coverage
```

| Attribute | Assessment |
|---|---|
| **Accuracy** | Does not change the point estimate; it makes the *error bar* honest |
| **Coverage** | Peer-reviewed result: conformal spatial prediction achieves **93.67% empirical coverage at 90% nominal** vs 68.33% for bootstrap `[S-53]` |
| **Data needs** | A labelled calibration set — 100 points `[DATA]`, sufficient for *stratified* (not per-address) radii |
| **Robustness** | Exchangeability is the assumption; towns are exchangeable *within* a stratum, not across |
| **Online/offline** | Offline; recomputed when labels arrive |
| **Learning** | Distribution-free — this is the point `[S-53]` |
| **Explainability / complexity / feasibility** | High / Low / **yes** |
| **Differentiation** | High for PS3: a geocoder that admits its interval is unusual, and it is exactly what a field planner needs to decide "is this visit worth a slot?" |

**Correct use.** Per-stratum (`precision` × town) radii, published in a calibration table, updated as field truth arrives — never a global 90% radius applied to a rooftop and a pincode alike.

---

## G11. Probabilistic geocoding

```
address ─► posterior p(x | address, evidence) sampled over a spatial grid
               = vendor prior (stratum kernel) × field-evidence likelihood × POI/landmark likelihood
        ─► report mean, mode, and HDR region; decisions consume the distribution, not the point
```

| Attribute | Assessment |
|---|---|
| **Accuracy** | Same point estimate as G8 on average, but **the decision is different**: a visit is planned against P(point ∈ 200 m), not against a pin |
| **Uncertainty** | Full distribution — the most expressive option |
| **Data needs** | Priors (stratum kernels, measurable from `derived_ps3_radius_calibration.csv`) + evidence likelihoods |
| **Robustness** | Product-of-experts is fragile if one likelihood is overconfident; needs tempering |
| **Online/offline** | Offline; grid resolution must match the metric plane |
| **Learning** | Likelihood weights fitted empirically; no labels needed for the prior (the vendor's own `precision` label *is* the prior) |
| **Explainability** | Medium-high (contributions visible); low to a non-technical reader unless shown as a heat map |
| **Complexity / feasibility** | Medium-high / feasible at coarse grid |
| **Differentiation** | **High** — "we return a distribution" is a genuinely different product contract, and it makes G10 and the PS2 field-slot decision trivial to compute |

**Failure modes.** Fake precision in the grid; double counting evidence that is not independent (same trail, two features).

---

## G12. Feedback / active learning

```
confirmed coordinate (2 independent confirmations) ─► promote as canonical ─► improves retrieval (G4)
                                                       ─► updates stratum priors (G10) ─► reprioritises field tasks
```

| Attribute | Assessment |
|---|---|
| **Accuracy** | Compounding: each confirmed visit improves every future query in that street |
| **Data needs** | Confirmation events — the dataset has 1,477 visited addresses and the outcome vocabulary to define "confirmed" `[DATA]` |
| **Robustness** | Requires a **poison guard** (the 11.6% inconsistent check-ins) and a two-confirmation rule, matching logistics practice `[S-56]` |
| **Online/offline** | Offline batch; the online path only reads |
| **Explainability** | High: "this pin moved because two independent visits agreed" |
| **Complexity / feasibility** | Low / **yes — highest value per line of code in PS3** |
| **Differentiation** | High; the *novelty* is that the confirmation signal comes from collection outcomes, not from delivery scan data |

**Failure modes.** A wrong pin confirmed twice (agents copying the pin); feedback loops that amplify a systematic offset; a third-party visit confirming a location that is not the borrower's address.

---

## G13. Compliance-grade provider layer

```
provider interface {geocode, reverse, validate}  ─►  cache policy guard (≤30 d, no permanent content storage)
    Google │ Mappls │ open (Nominatim, 1 req/s)   ─►  audit log of provider, timestamp, terms version
```

| Attribute | Assessment |
|---|---|
| **Why it exists** | Google Maps Platform terms: lat/lng cached **≤30 days**, no permanent storage of other content, no training on output `[S-48]`; Nominatim 1 req/s and no heavy use `[S-51]`; data.gov.in NDSAP non-commercial `[S-65]` |
| **Consequence for the architecture** | **The canonical coordinate cannot be a vendor pin.** The long-lived coordinate must be *our own* field-confirmed record (G12), with vendor pins as time-limited priors |
| **Complexity / feasibility** | Low / yes — and it is a genuine differentiator because most teams will cache vendor responses |
| **Differentiation** | Medium (compliance-shaped, not accuracy-shaped), but it is the kind of thing a bank's legal review asks about in the first meeting |

---

## G14. Place identity graph

```
Address ──at──► Building ──contains──► Unit      PIN ──contains──► Locality ──in──► Town
   ▲                 ▲
   └── observed_at ──┴── ContactPoint (borrower link)
```

| Attribute | Assessment |
|---|---|
| **Purpose** | Deduplicate: 3,117 addresses for 2,400 accounts, with 74 repeated `phone_id`s across accounts `[DATA]` → many "different" addresses are the same building. Fixing the building fixes every unit in it |
| **Accuracy** | Improves *throughput* of confirmation, not per-address accuracy directly |
| **Data needs** | Address text similarity (Splink/Fellegi-Sunter on address fields `[S-44]`) + coordinates |
| **Robustness** | Over-merging two buildings is the risk; FS weights keep it explainable |
| **Online/offline** | Offline |
| **Explainability** | High (per-field match weights) |
| **Complexity / feasibility** | Medium / feasible — and it is the natural PS2↔PS3 bridge (see `SANKET_SUTRA_SYSTEM_ARCHITECTURE_FINAL.md`) |
| **Differentiation** | High at portfolio level: "confirm 40 buildings, not 1,200 addresses" |

---

## G15. Hybrid *(recommended)*

```
address_text
   │
   ├─(1) PARSE / NORMALISE ......... structured fields + script normalisation        [G3]
   │
   ├─(2) RETRIEVE .................. candidates from gazetteer + confirmed-pin index  [G4]
   │
   ├─(3) RANK ...................... score candidates (rules first, model if labels)  [G5]
   │
   ├─(4) PRIOR ..................... vendor result + precision stratum kernel         [G1 + G10]
   │
   ├─(5) POSTERIOR ................. fuse prior ⊗ field evidence ⊗ landmark evidence  [G8, G11]
   │        └─ integrity gate: mock-location, teleport, duplicate media, negative-outcome exclusion
   │
   ├─(6) UNCERTAINTY ............... per-stratum conformal radius + coverage monitor  [G10]
   │
   ├─(7) DECISION SURFACE .......... P(within 200 m) ─► feeds the PS2 field-slot decision
   │
   └─(8) FEEDBACK .................. 2-confirmation promotion ─► index, priors, task queue [G12]
```

| Attribute | Assessment |
|---|---|
| **Accuracy** | Baseline 376 m → ~29 m where field evidence exists; elsewhere the honest stratum median with honest radius |
| **Uncertainty** | Distribution + conformal coverage; **the only option that reports both** |
| **Multilingual** | Parse layer handles script/transliteration `[S-45][S-46]` |
| **Data needs** | All present except a road graph (drop G9) and third-party POI content (landmarks used as priors only) `[DATA]` |
| **Robustness** | Layered: any stage can fail to its fallback; integrity gate protects the whole posterior |
| **Online/offline** | Offline-capable; provider calls only for the prior |
| **Learning** | Empirical calibration + 2-confirmation promotion; no model required for the core claim |
| **Explainability** | High, stage by stage |
| **Complexity / feasibility** | Medium-high overall, **feasible in 48 h if stages 2/3 are minimal** |
| **Differentiation** | **Highest**: honest radius + evidence fusion + compliance-safe canonical store |

---

## Ranked comparison

Scoring 1–5; weighted with the brief's weights (PS alignment 20 / business value 15 / technical depth 15 / differentiation 15 / dataset support 10 / production realism 10 / feasibility 10 / explainability 5).

| Rank | Architecture | PS align | Value | Depth | Diff | Data | Prod | Feas | Expl | **Weighted** |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **G15 Hybrid** | 5 | 5 | 5 | 5 | 4 | 5 | 4 | 5 | **4.75** |
| 2 | **G8 Field-evidence fusion** | 5 | 5 | 4 | 5 | 5 | 4 | 5 | 5 | 4.70 |
| 3 | **G10 Conformal uncertainty** | 5 | 5 | 4 | 5 | 4 | 5 | 5 | 5 | 4.65 |
| 4 | G12 Feedback / active learning | 4 | 5 | 4 | 5 | 4 | 5 | 5 | 4 | 4.45 |
| 5 | G11 Probabilistic geocoding | 4 | 4 | 5 | 5 | 3 | 4 | 3 | 3 | 3.95 |
| 6 | G3 Parse-then-geocode | 5 | 4 | 3 | 3 | 5 | 4 | 4 | 5 | 4.15 |
| 7 | G4 Retrieval + ranking | 4 | 4 | 3 | 4 | 4 | 4 | 5 | 4 | 3.95 |
| 8 | G14 Place identity graph | 4 | 4 | 3 | 4 | 4 | 4 | 3 | 4 | 3.75 |
| 9 | G13 Compliance provider layer | 5 | 3 | 2 | 3 | 5 | 5 | 5 | 4 | 4.05 |
| 10 | G2 Multi-vendor consensus | 3 | 3 | 3 | 2 | 2 | 4 | 3 | 4 | 2.85 |
| 11 | G6 Hierarchical cell prediction | 4 | 4 | 5 | 5 | 1 | 4 | 1 | 4 | 3.45 |
| 12 | G1 Vendor wrapper | 2 | 1 | 1 | 1 | 5 | 3 | 5 | 2 | 2.20 |
| 13 | G5 Learned candidate ranker | 3 | 3 | 4 | 3 | 2 | 3 | 3 | 3 | 2.95 |
| 14 | G9 Map matching (HMM) | 3 | 3 | 5 | 4 | 1 | 3 | 1 | 3 | 2.90 |
| 15 | G7 Landmark anchoring | 3 | 2 | 2 | 2 | 2 | 2 | 2 | 3 | 2.25 |

**Reading the table.** The top of the list is not the most sophisticated architecture — G6 and G9 are more sophisticated and both rank low because the data cannot support them in 48 hours and the brief forbids citing sophistication we cannot demonstrate. G8 and G10 rank at the top because each is backed by a **measured** number from our own dataset (385 m → 29 m; and a stratum table that two independent samples agree on). G15 is the union, and its only risk is scope — which is why `PS3_ARCHITECTURE_SELECTION.md` fixes the build order and the minimum viable cut.

---

## What each architecture changes in the actual field workflow

| Layer | Workflow change | Evidence |
|---|---|---|
| Stratum-aware radius (G10) | The field app stops showing a pin and starts showing **"search 1.3 km" vs "search 40 m"** | pincode stratum median 1,336.5 m vs rooftop 37.7 m `[DATA]` |
| Field fusion (G8) | Every completed visit improves the map, so later visits cost less | 385 m → 29 m on met-someone visits `[DATA]` |
| Integrity gate (G8) | The system stops learning from the 11.6% inconsistent check-ins | 645 check-ins >500 m from their own trail `[DATA]` |
| Feedback (G12) | Two confirmations promote a coordinate; no manual master-data task | logistics practice `[S-56]` |
| Parse layer (G3) | Agents stop retyping addresses; branch/script variants collapse to one record | `addressparser` <30 ms, open weights `[S-46]` |
| Provider layer (G13) | Legal can approve the data flow; the canonical coordinate is ours | Google cache ≤30 d `[S-48]` |
| Distribution output (G11) | PS2 can ask "P(within 200 m)?" and price a field slot | enables the PS2↔PS3 contract |

**The honest summary of this file.** PS3 is not a geocoding-accuracy problem; our own measurements show free data caps out at 370 m and that a commercial geocoder is already within 376 m. The architecture that matters is the one that (a) tells the truth about how far off it is, (b) spends field evidence where it changes the belief most, (c) refuses to learn from contaminated evidence, and (d) hands PS2 a probability instead of a pin.
