# PS3 — DEEP INTERNET RESEARCH

**Phase 1 of the evidence pass. Research only — no architecture is fixed here.**
Companion files: `PS3_ARCHITECTURE_REQUIREMENTS.md`, `PS3_REAL_SYSTEMS_RESEARCH.md`, `PS3_SOURCE_REGISTER.md`, `PS3_DATA_AUDIT.md`.

Evidence tags: **[VERIFIED]** directly supported · **[INFERENCE]** conclusion from ≥2 sources · **[ASSUMPTION]** still assumed · **[UNKNOWN]** insufficient evidence.

---

# 9. What the PS3 address problem actually is (§9 of the brief)

## 9.1 Candidate decompositions, and which one the evidence supports

| Framing | Evidence | Verdict |
|---|---|---|
| Parsing / normalisation | Open-source Indian parsers exist and run in <30 ms (IndicBERTv2-SS + CRF, 600+ annotated Delhi addresses; a spaCy/regex parser with PIN-anchoring; fine-tuned LLM parsers) — [VERIFIED: addressparser.kushagragolash.dev; GitHub priyanshi0609/Indian-Address-Parser; dev.to LoRA pipeline with 4.3M raw + 4,834 gold labels] | **Solved enough; not the bottleneck** |
| Geocoding accuracy | Google's India fine-grained performance is weak: in peer-reviewed comparisons, Google achieved **23.8% of addresses within 100 m** vs **64.3% for a production Indian system** (COLING 2025 industry paper) — [VERIFIED] | **The dominant error source** |
| Candidate generation / ranking | GeoIndia learns H3-cell prediction ("hierarchical H3-cell prediction within a Seq2Seq framework") — [VERIFIED: EMNLP 2024 Industry] | **Promising but data-hungry** |
| Confidence / radius | Vendors already return error radii (Delhivery GeoNaksha) and Google returns component-level accuracy for Address Validation — [VERIFIED for Delhivery; Google AVI per Phase-1 research] | **Partly commoditised; the *use* of it is not** |
| Landmark extraction | Landmarks are a named output class in published Indian address NER models ("landmarks" is one of 23 entity labels in Shiprocket's released IndicBERT NER model) — [VERIFIED: huggingface.co/shiprocket-ai/open-indicbert-indian-address-ner] | **Component, not headline** |
| Residence / purpose classification | Home/work inference from mobility is a mature literature (dwell-time + night-window rules; 65–70% within 100 m in one cited study) — [VERIFIED as reported in arXiv 2410.22386; PLOS ONE 2014; Wiley 2021] | **Real, and cheap to approximate** |
| Field verification | Field apps already geo-tag visits (Credgenics CG Collect, Mobicule) — [VERIFIED: vendor pages] | **The input exists commercially; the *integrity* question does not have an off-the-shelf answer** |
| Field-force optimisation | Solved and sold (OR-Tools VRP supports capacity/time-window/dropped visits; vendors sell beat plans) — [VERIFIED: developers.google.com/optimization/routing] | **Do not build; consume** |

**[INFERENCE] Conclusion:** PS3 is **not** a geocoder-building problem and **not** a parsing problem. It is a **representation + evidence + permission** problem: what to output (a distribution with uncertainty, not a point), what evidence to trust (field observations, weighted), and what the output is *allowed to authorise* (a legally-required notice or a doorstep visit).

## 9.2 Real Indian address pathologies — evidenced

| Pathology | Evidence |
|---|---|
| Landmark-based addressing, missing house numbers | Shiprocket's released NER model carries `landmarks`, `house_details`, `sub_locality`, `locality` as first-class labels, and lists as limitations "highly regional or colloquial formats", "very recent developments", "highly unstructured text" — [VERIFIED] |
| Spelling variation and informal text | Delhivery's GeoNaksha LLM is marketed explicitly for "informal, incomplete, or misspelled address text" — [VERIFIED: delhivery.com/maps/developer] |
| Multi-script / multilingual | IndicBERT-based models and multilingual address NER exist; STHAL (ICON 2020) shows Indian-styled location mentions (e.g., "Gali No. 5") break generic NER, with best F1 72.49% — [VERIFIED: ACL Anthology] |
| PIN-code weakness | Google's own address-validation component-confidence signal is sold precisely because components are unreliable; India Post's own pincode directory has latitude/longitude for only a small fraction of post offices historically (142 of ~154,797 as of a 2015 data.gov.in note) — [VERIFIED as a historical data-quality observation] |
| Outdated / multiple addresses | Not directly evidenced in public sources — **[UNKNOWN]** whether the *bow* (self-reported) address, the KYC address and the notice address diverge systematically. Must be asked of CN |

---

# 10. Indian address parsing: approaches compared (§10)

| Approach | Accuracy evidence | Latency | Explainability | Data requirement | Hackathon feasibility |
|---|---|---|---|---|---|
| Regex + PIN gazetteer + dictionary | PIN-anchored parsers claim ~100% accurate PIN→city/state enrichment using a ~155k-row lookup — [VERIFIED as vendor/dev claim] | ms | **High** | PIN directory | **High** |
| CRF / probabilistic sequence labelling | Classic, works with modest supervision | ms | High | annotated spans | Medium |
| BERT-family NER (IndicBERT / multilingual BERT + CRF) | Delhi parser: IndicBERTv2-SS + CRF, 600+ annotated addresses, **<30 ms**; Shiprocket's IndicBERT NER (23 labels) is **publicly downloadable** with stated limitations | tens of ms | Medium | 500–5,000 labelled spans | **High** (open weights) |
| Seq2Seq / LLM end-to-end (address → H3 cell or coordinate) | GeoIndia: 29 state models, ">50% reduction in mean distance error and >85% reduction in 99th-percentile distance error compared to Google Maps" in multiple states — [VERIFIED]; GeoIndia-V2 adds a Graphormer + language model trained on **proprietary** Indian address data and e-commerce delivery graphs — [VERIFIED] | high (LLM) | Low | **large proprietary corpora** | **Low** |
| LLM + tools (GeoAgent, ACL Findings 2024) | Standardising non-standard addresses reduced average distance error; AD ≈ 53 m reported (Chinese address context) — [VERIFIED] | high | Medium | moderate | Medium (cost) |

**[INFERENCE] Verdict:** parsing is a *solved-enough preprocessing step*; buy/open-weight it, do not invent it. The evidence does **not** support making parsing the centrepiece of PS3.

---

# 11. Commercial geocoding systems (§11)

| Provider | India capability | Confidence/uncertainty signals | Pricing | Licensing constraints that matter to us |
|---|---|---|---|---|
| **Google Maps Platform** | Global; Address Validation returns component-level results (Phase-1 research) | Component confidence; not a doorstep guarantee | Per-request; 3,000 QPM noted in practitioner write-ups | **Decisive:** lat/lng from the Geocoding API may be cached **only up to 30 consecutive days**, after which it must be deleted; indefinite caching of lat/lng/formatted/structured address is allowed **only** to support direct end-user-facing functionality of the requesting app, and the cache must not replace a service call; outside lat/lng and place_id, content may not be used "with any Map"; no pre-fetching/indexing/storing/scraping — [VERIFIED: Google Maps Platform Service Specific Terms §6] |
| **Mappls / MapmyIndia** | India-native; **eLoc** described as a "doorstep digital address system in just 6 characters"; Address Standardisation API; data hosted in India; positioned as compliant with Government of India regulations — [VERIFIED: mapmyindia.com; mappls REST API GitHub] | eLoc + standardisation outputs | **Not published** — sales contact required (2026 comparisons state this explicitly) — [VERIFIED] | Terms require attribution; commercial terms per contract — [INFERENCE] |
| **Delhivery Maps (GeoNaksha LLM)** | Geocoding, reverse geocoding, **Address Validation** (finds missing/wrong components), **Address Verification** (has this address been visited within a window), Address Standardisation; backed by 4B+ deliveries, 3M+/day — [VERIFIED: delhivery.com/maps/developer] | Returns validation/verification outcomes and (per our Phase-2 research) an error radius | Not public | The visit-history verification is the closest commercial analogue to what we proposed — **and it exists** |
| **HERE** | Global coverage; India coverage quality not verified in this pass — **[UNKNOWN]** | — | Published tiers | — |
| ~~**OSM / Nominatim**~~ **— REJECTED (final data policy, 2026-10-07: no external data)** | Coverage in India is uneven but the POI/road base is usable; self-hosting permitted | none natively | Free (self-host) / public API with limits | Public instance: **max 1 req/s**, no heavy use, bulk geocoding discouraged (single-threaded, 4 req/min for long-running scripts), **results must be cached**, ODbL **share-alike** attribution — [VERIFIED: OSMF Nominatim Usage Policy]. **Self-hosting removes the storage restriction** (you may store and reuse results) — [VERIFIED via practitioner write-up] |

## 11.1 Build vs buy — the evidence-based answer

- **Do not build a geocoder.** The two best Indian geocoders in the literature (GeoIndia, GeoIndia-V2, and the COLING-2025 production system) are built on **proprietary corpora** (state-labelled address data, e-commerce delivery graphs). A hackathon team cannot reproduce that, and a released open model of that class does not exist — [VERIFIED].
- **Do buy at runtime, but do not store vendor coordinates as your product.** Google's terms expressly forbid indefinite caching except for end-user-facing display, and forbid using content with non-Google maps — so a *stored belief state* built from Google coordinates is a licensing problem, not merely a design choice — [VERIFIED].
- **Therefore the differentiated layer must be built from evidence you own** (field observations, agent attestations, notice outcomes) plus the official gazetteer already in the pack, with the vendor API used as a *candidate generator at request time* — [INFERENCE]. External open data is **rejected** by the final project decision `[S95]`.
- **Licensing escape hatches:** a commercial India-native licence (Mappls/Delhivery) if stored coordinates are required. Self-hosted/open geocoders are **rejected** — no external data may be stored or queried `[S95]`.

---

# 12. Advanced Indian geocoding research — is "address → one coordinate" the wrong representation? (§12)

**Evidence that it is:**

1. **Peer-reviewed Indian benchmarks** show a single top-1 coordinate is where the error lives: Google 23.8% within 100 m; the best production system 64.3%; a multi-head model 77.2% — [VERIFIED: COLING 2025 industry paper comparison table].
2. **Vendors already ship uncertainty** (Delhivery's validation/verification; Google's component confidence) — [VERIFIED].
3. **The uncertainty literature has spawned a geospatial branch:** *GeoConformal Prediction* introduces geographic weighting into conformal prediction, reporting **93.67% coverage** vs **≤81%** for bootstrap in a spatial regression case, and explicitly argues uncertainty should vary by location — [VERIFIED: arXiv 2412.08661; Annals of the AAG 2025]. Follow-on work (GeoSIMCP, 2026) adds feature-space similarity for non-stationary processes — [VERIFIED].
4. **Methodologically, prediction regions for 2-D targets are a solved family** (adaptive geodesic conformal, 2026) — [VERIFIED: arXiv 2602.16015].

**Evidence that a distribution is operationally awkward:** none found — but note that a *candidate set* is what field operations already use implicitly (agent asked to go "near Hanuman Mandir, behind the shop") — [INFERENCE].

**[INFERENCE] Conclusion:** output **top-k candidates with weights + a calibrated radius + an explicit "unknown" tier**, and validate coverage empirically. Conformal methods are the right *validation* tool; a global coverage claim is not defensible at small n.

---

# 13. GPS / field verification evidence (§13)

| Question | Evidence | Consequence |
|---|---|---|
| What does a reported GPS accuracy mean? | Android `Location.getAccuracy()`: "estimated horizontal accuracy radius in meters … at the **68th percentile** confidence level" — [VERIFIED: developer.android.com] | A "10 m" reading is a 68% radius, not truth. Any 90% radius must be derived empirically, not by assuming 1.5× |
| Can a mock location be detected? | `Location.isMock()` (API 31+) and the deprecated `isFromMockProvider()`; Google also offers device/app integrity APIs (Play Integrity) | Cheap first-line signal, **not** a guarantee — rooted devices and injected APIs can evade it — [VERIFIED for the API; [INFERENCE] on evadability] |
| What makes a field observation trustworthy? | Mobility literature: home/work inference uses **dwell time** (stay-point methods with 10–50 minute dwell thresholds), **time windows** (night vs day), and spatial clustering radii (e.g., 250 m) — [VERIFIED: PLOS ONE 2014; Wiley 2021; GHOST 2026; arXiv 2410.22386] | Use dwell + time-of-day + repeat agreement; single pings are weak evidence |
| Sequence plausibility | Speed/route feasibility checks are standard in map-matching literature — [INFERENCE] | Cheap, strong detector of fabricated check-ins |
| Repetition / agreement | Multiple independent visits agreeing is the classic robust-estimation setup | Agreement should raise confidence; disagreement should widen the radius |
| Photo/attestation | Not evidenced in collections; used in logistics (proof of delivery) | Treat as a supporting signal only — [ASSUMPTION] |
| Spoof-detection rates in the field | No public benchmark found | **[UNKNOWN]** — never claim a detection rate |

**Address Evidence Score — supported ingredients:** accuracy radius, dwell duration, time-of-day fit for the claimed purpose, distance to current belief, agreement with prior observations, device-integrity flags, movement plausibility between consecutive check-ins.
**Not to be trusted on its own:** a coordinate without an accuracy value, an agent-entered remark without dwell, a "visit marked complete" flag, a single observation, and any coordinate that arrives faster than physically possible.

---

# 14. Address confidence and uncertainty representation (§14)

| Representation | Evidence for | Evidence against | Recommendation |
|---|---|---|---|
| Single lat/lon | What vendors return | India fine-grained error is large (23.8% <100 m for Google) | **No** |
| lat/lon + radius | Delhivery returns an error radius; Android reports a 68% radius; GeoConformal supplies spatially varying coverage | A radius without a purpose/threshold is not actionable | **Yes — as one field** |
| Top-k candidates + probabilities | GeoIndia predicts H3 cells (a discrete distribution); multi-candidate generation is the standard IR approach | Requires scoring candidates; vendors disagree | **Yes — as the primary object** |
| Full belief distribution | Theoretically clean; supports Bayesian fusion (as in our SUTRA hypothesis) | Hard to explain to a field agent; calibration needs data volume | **Yes, internally** (belief state) rendered as top-k + radius externally |
| Hybrid | — | — | **Recommended** |

**Calibration options:** empirical quantiles of held-out error **per stratum** (cheap, honest); quantile regression (needs volume); conformal, with geographic weighting where the calibration set is spatially clustered (GeoCP); vendor-supplied uncertainty as a *feature*, never as the final answer.
**Honest limit:** with CN's data volume per locality likely small, the correct output is often "**unknown — verify first**", and the product must make that a first-class state. [INFERENCE]

---

# 15. Residence / purpose classification (§15)

| Signal | Evidence | Weight |
|---|---|---|
| Dwell time | Stay-point literature: 10–50 min thresholds; GHOST uses total stay-time per grid cell as the primary home signal, outperforming visit-count methods — [VERIFIED] | High |
| Time-of-day / night window | Standard: night-time dwell → home; day window → work (e.g., night 8pm–5am; day 8am–6pm) — [VERIFIED] | High |
| Day-of-week pattern | Weekend vs weekday occupancy distinguishes home from workplace — [VERIFIED as a standard feature in the literature; GHOST uses a weekend fallback when night data are sparse] | Medium |
| POI type at location | OSM/place classes (shop, office, worship) | Medium |
| Repeat visits over months | Sign of residence | Medium |
| Agent remark ("met at shop") | Direct but manipulable | Medium, with integrity weight |
| Account records (employer address, KYC) | Strong when present | Medium |

**Reported accuracy:** one widely cited result is **70% home / 65% workplace within 100 m** from mobile data (as reported in arXiv 2410.22386); the GHOST paper reports stay-time methods beating clustering approaches across datasets. **No Indian, address-text-anchored benchmark was found — [UNKNOWN].**

**[INFERENCE] Consequence for PS3:** a three-way purpose classification (home-like / work-or-business / other-or-unknown) with an explicit confidence and an abstain class is defensible and buildable. A 7-way taxonomy is not evidenced and should not be claimed.

**Why purpose matters at all (compliance, not curiosity):** RBI's framework prohibits contacting relatives/friends/colleagues and disclosing debt to third parties. Serving a notice or making a debt-disclosing visit at a **workplace or shop** creates exactly that exposure. So purpose classification is a *permission input*, not a nice-to-have — [INFERENCE from the Directions' prohibited-practices list].

---

# 16. Field-force optimisation (§16)

- **Route optimisation is a solved, commoditised layer:** Google OR-Tools ships TSP/VRP with capacity, time windows, resource constraints and a "dropping visits" mechanism — [VERIFIED: developers.google.com/optimization/routing and /vrp].
- **Public routing data exists for benchmarking heuristics** (Amazon Last Mile Routing Research Challenge: 6,112 training routes across 5 US metros, anonymised, no PII; AWS Open Data) — [VERIFIED: INFORMS *Transportation Science* 2022].
- **Vendors already sell the beat-plan layer** in Indian collections (Mobicule "AI beat plans", Credgenics CG Collect allocation) — [VERIFIED as vendor claims].
- **H3 is a real, well-motivated indexing tool** (hexagons, 16 resolutions, ~1/7 area steps, neighbour/edge operations, used by Uber for marketplace analysis) — [VERIFIED: Uber engineering blog; h3geo].

**[INFERENCE] Answer to the brief's question:** **PS3 should not optimise routes.** It should emit a **location-and-confidence object** (candidates, weights, radius, purpose, landmark directions, evidence count) that an existing field-optimisation system consumes. Building routing adds effort, duplicates a commodity, and adds no compliance value. H3 is useful **only** as a cheap spatial key for strata and for matching landmark phrases to localities; it is not a deliverable.

---

# 17. Datasets (§17)

> **REJECTED (final data policy, 2026-10-07).** Every external dataset catalogued in this section — OSM/Geofabrik, Overture,
> India Post/data.gov.in, open address corpora, open geocoding services — was considered during research and **rejected by final
> project decision**. The PS3 system uses only the official CreditNirvana dataset and its officially assigned shared tables.
> The rows below are retained as historical research for provenance, never as plans; the binding statement is
> `PS3_FINAL_DATA_AND_ARCHITECTURE_FREEZE.md` §DATA `[S95]`.

## 17.1 PS3

| Dataset | URL | Domain / size | Geography | Labels | Licence / commercial use | Relevance | Limitations |
|---|---|---|---|---|---|---|---|
| ~~**OpenStreetMap** (via Geofabrik extracts / Overpass)~~ **REJECTED** | openstreetmap.org; download.geofabrik.de | Global map: roads, POIs, some addresses/buildings | India: uneven but widespread | n/a (features) | **ODbL** — share-alike, attribution; commercial use permitted with obligations | Landmark gazetteer, POI purpose typing, road network, geofence polygons | Rural address/POI sparsity; no house numbers in most of India |
| ~~**Overture Maps — addresses theme**~~ **REJECTED** | docs.overturemaps.org/guides/addresses | **474,186,531 addresses** (Sept 2026 release), monthly, alpha | **41 countries**; India presence **not confirmed in this pass — [UNKNOWN]** | street/number/postcode/levels | Overture licence (permissive, attribution) — verify per-source provenance | Would be the best open address base if India is covered | Alpha; partial coverage in several large countries; must verify India before relying on it |
| ~~**India Post / data.gov.in PIN directory**~~ **REJECTED** | data.gov.in catalog "All India Pincode Directory"; Kaggle mirrors | ~122,000–155,000 rows | All India | post office name, district, state, taluk, some lat/long (mostly missing) | NDSAP — free; **an open-data review found the licence "not open" for commercial reuse** — [VERIFIED]; confirm with CN's legal before production use | PIN → district/state anchor; classic first step in Indian parsers | Lat/long largely absent; licence must be checked |
| ~~**Shiprocket IndicBERT address NER (open weights)**~~ **REJECTED (external model/data)** | huggingface.co/shiprocket-ai/open-indicbert-indian-address-ner | NER model, 23 labels incl. `landmarks`, `locality`, `pincode` | India (English-oriented) | pretrained, ready to infer | Model card terms on HF (check) | Instant parsing baseline — no training needed | "Primarily optimized for English Indian addresses"; struggles with colloquial formats |
| ~~**Indian address corpora (community)**~~ **REJECTED (external address DB)** | HF datasets `indian-addresses-raw` (≈4.37M records) and `indian-addresses-gold` (4,834 span-labelled) per a published pipeline write-up | Combined MCA + bank/BC address records | India | Silver (rules) + gold (human) spans | Check HF dataset cards | The closest thing to a trainable Indian address corpus | Silver labels derived from rules → circular for evaluating parsing; gold set is small |
| **Amazon Last Mile Routing Research Challenge** | registry.opendata.aws/amazon-last-mile-challenges | 6,112 training routes (2018) | 5 US metros | Route sequences, travel times | Open Data (anonymised, no PII) | Routing/sequence benchmarking only | **US, not addresses**; irrelevant to Indian address accuracy |
| **Google Address Validation API (as a service, not a dataset)** | mapsplatform.google.com | — | India supported | component-level results | per-call licence, caching limits | Candidate generation + component agreement checks | Cannot be stored as training data |

**Excluded by policy:** Bhuvan/ISRO (terms), scraped vendor content.

**Not found, and therefore not listed:** any public Indian geocoded ground-truth dataset with sub-100 m household accuracy; any public field-visit GPS dataset for collections; any public benchmark for landmark resolution in India. **[UNKNOWN]**

## 17.3 Synthetic data — when and how (permitted only with labels)
Synthetic data is acceptable for: demo flows, unit tests, calibration plumbing, failure-mode tests, and architecture demonstration. It is **not** acceptable as evidence of accuracy, lift, or ROI. Every synthetic artefact must carry a visible `SYNTHETIC` marker; any number derived from it must be labelled as illustrative.

---

# 18. What this changes for PS3 (hand-off to the requirements file)

1. **Do not build a geocoder; do not store vendor coordinates as the product.** Licensing (Google §6) and the proprietary-data moat of Indian geocoding research both point to consuming a geocoder at runtime. [evidence: §11, §12]
2. **Parsing is preprocessing; use open weights + a PIN anchor.** [evidence: §10]
3. **The output object is a candidate set + radius + purpose + evidence count**, not a point. [evidence: §12, §14]
4. **Integrity weighting is the only defensible way to learn from field data** — and it has a real, documented evidential basis (dwell, time window, accuracy radius, sequence plausibility). [evidence: §13]
5. **A visit reveals a debt at an address**, so the coordinate that authorises a doorstep action is a compliance artefact, not a convenience: it must be evidence-backed, versioned and reviewable. [evidence: §15; licence envelope §14]
6. **No routing.** Emit the object; let the field system consume it. [evidence: §16]
7. **State uncertainty, claim coverage only where measured, and keep "unknown" as a first-class output.** [evidence: §14]


---

**Sources.** This reference document predates the register; its external sources are catalogued in
`PS3_SOURCE_REGISTER.md`, its measurements on the official dataset are reproduced by `tools/ps3_audit.py` (`[S90]`), and
the binding design it fed into is `PS3_MASTER_ARCHITECTURE.md`.
