# PS3 — ARCHITECTURE REQUIREMENTS

**This is not the architecture.** It is the requirement set the eventual `PS3_SUTRA_SOLUTION_ARCHITECTURE.md` must satisfy, each item traceable to `PS3_DEEP_INTERNET_RESEARCH.md` (cited as §n), and each answering: **what does this change in the collections workflow?**

---

## 0. Scope statement the architecture must open with

> PS3 does not build a geocoder. It **produces a location belief with calibrated uncertainty for a recovery address, from evidence that a geocoder cannot have**, and it uses that belief to decide whether a legally-required notice or a doorstep visit may be issued. Its outputs are: a candidate set, a radius, a purpose judgement, directions, and a **permission**.

Evidence: §9.1, §11.1, §12, §15.

---

## 1. Inputs

| ID | Requirement | Evidence | Workflow change |
|---|---|---|---|
| **R1.1** | MUST accept the **raw address string(s)** as recorded (origination/KYC/application/prior notice), plus language/script markers where known | §9.2 | Keeps provenance; prevents silent normalisation loss |
| **R1.2** | MUST accept **account context**: PIN if present, city/district/state, borrower-declared employer/landmarks, product and ticket size | §15 | Feeds purpose classification and the value test for spending a visit |
| **R1.3** | MUST accept **field observations**: coordinate, **accuracy value**, timestamp, dwell, visit outcome, purpose remark, agent/device identifiers, attestation flags | §13 | The evidence stream that no vendor has |
| **R1.4** | MUST accept **notice/visit outcomes** (served, refused, wrong door, no one present, returned) | §15 | Closes the loop on the action the system permits |
| **R1.5** | MUST accept **PIN→district/state reference data** and a **landmark/POI base** | §17.1 | Anchors parsing and purpose typing without a licence risk |
| **R1.6** | MUST accept a **licence-configured geocoder client** as a runtime dependency (which vendor, what may be stored) | §11.1, Google ToS §6 | Makes the legal position explicit in configuration, not in a wiki |

## 2. Parsing

| ID | Requirement | Evidence | Workflow change |
|---|---|---|---|
| **R2.1** | MUST extract, at minimum: PIN, state, district, city/locality, sub-locality, landmark phrases, house/building identifiers, floor/block where present | §10 | Produces the fields the downstream checks and directions need |
| **R2.2** | SHOULD use an **open-weight Indic address NER** (e.g., IndicBERT-based) plus deterministic **PIN-anchoring** rather than a bespoke model | §10 (open weights; <30 ms class performance) | Ships in the MVP; no training corpus required |
| **R2.3** | MUST treat parsing failures as **abstentions**, not as guesses | §10, §14 | Forces "verify first" instead of a wrong-door action |
| **R2.4** | SHOULD record the parser version and the extracted spans with every decision | §6.3 (PS2 R11.1) | Replayable decisions |
| **R2.5** | MUST NOT spell-correct proper nouns before the landmark match (aliasing is handled by the landmark table) | §9.2, §15 | Avoids silently corrupting a landmark into a different real place |

## 3. Normalisation

| ID | Requirement | Evidence | Workflow change |
|---|---|---|---|
| **R3.1** | MUST normalise scripts/transliteration conservatively: transliterate for matching, retain the original string in storage | §9.2 | Field agents still see the address the way it was written |
| **R3.2** | MUST validate the PIN against the PIN→district/state reference and flag disagreements as a **confidence penalty**, not a silent correction | §17.1 | Catches one of the most common Indian address errors early |
| **R3.3** | SHOULD build a per-locality **landmark alias table** from confirmed visits (e.g., "behind Hanuman mandir" → coordinate) with human review for new entries | §15, §16 | The compounding asset: matching improves for *other* accounts at the same landmark |
| **R3.4** | MUST scope landmark matching to locality/PIN/H3 cell to avoid cross-town duplicate names | §16 (H3 as key) | Prevents the classic "same temple name, different town" failure |

## 4. Geocoder integration

| ID | Requirement | Evidence | Workflow change |
|---|---|---|---|
| **R4.1** | MUST consume a commercial/India-native geocoder **at request time**; the stored belief must not be a cache of vendor coordinates | §11.1; Google Service Terms §6.3 | Keeps the legal position clean; the belief is built from our evidence |
| **R4.2** | MUST declare, per vendor, **what may be stored** (e.g., permitted caching window; permitted display contexts) and enforce it in code | §11.1 | Prevents an accidental licence breach at scale |
| **R4.3** | MUST support an **OSM/self-hosted fallback** with ODbL attribution obligations | §11 | Keeps the product running if a vendor contract lapses |
| **R4.4** | MAY request multiple candidate locations from the vendor and MUST keep them as candidates rather than collapsing to one | §12 | Preserves the option value when vendors disagree |
| **R4.5** | MUST cap vendor spend with a per-portfolio budget and log every lookup | §5.1 (PS2 research: lookups are cheap but not free at scale) | Lookups become a controllable cost line |

## 5. Candidate generation

| ID | Requirement | Evidence | Workflow change |
|---|---|---|---|
| **R5.1** | MUST produce a **top-k candidate set** (k small, typically 1–5) with a source label per candidate (vendor, PIN polygon, landmark, prior visit) | §12 | Gives field and compliance users alternatives, not a false precision |
| **R5.2** | MUST include a **PIN/locality polygon candidate** whenever the vendor returns low-confidence or misses | §14 (fallback) | Guarantees a bounded, honest answer instead of nothing |
| **R5.3** | MUST include a **landmark-derived candidate** when a landmark phrase resolves inside the locality | §3.3, §15 | Matches how Indian addresses are actually given |
| **R5.4** | MUST NOT include candidates outside the PIN/district envelope unless evidence explicitly places them there, and must record the exception | §9.2 | Blocks the most damaging geocoding error for a doorstep action |

## 6. Candidate ranking

| ID | Requirement | Evidence | Workflow change |
|---|---|---|---|
| **R6.1** | MUST rank candidates with an **inspectable weighted combination** (source agreement, PIN consistency, landmark match, visit evidence with integrity weight), not an opaque ranker, in the MVP | §12, §23 | A compliance officer can read the ranking rationale |
| **R6.2** | MUST apply observation **integrity weights** so that a low-trust observation changes the belief less and widens the uncertainty more | §13 | Fraud costs precision, but cannot relocate the belief |
| **R6.3** | MUST allow **disagreement to widen** the radius rather than average the candidates into a midpoint | §13, §14 | Prevents the "centroid of two different places" failure |
| **R6.4** | MAY graduate to a learning-to-rank model only after the transparent ranker is measured against it | §23 | Complexity must earn its place |

## 7. Confidence estimation

| ID | Requirement | Evidence | Workflow change |
|---|---|---|---|
| **R7.1** | MUST output a **confidence tier** (e.g., confirmed / probable / weak / unknown) derived from evidence counts, agreement and integrity weights | §14 | Becomes the input to the notice gate |
| **R7.2** | MUST derive confidence from **observable evidence**, not from a vendor's numeric score alone | §11.1, §12 | The claim is defensible in an audit |
| **R7.3** | MUST make **`unknown` a first-class output**, not an error state | §14 | The default action becomes verification, not action |
| **R7.4** | SHOULD calibrate tiers on held-out visit outcomes and report the observed hit rate per tier | §14 (marginal vs conditional coverage) | Confidence means something measurable |

## 8. Uncertainty representation

| ID | Requirement | Evidence | Workflow change |
|---|---|---|---|
| **R8.1** | MUST output **coordinates + radius + tier + evidence count**; a bare point is non-compliant with this requirement | §12, §14 | Field agents get a search area and a route, not a false pin |
| **R8.2** | MUST compute the radius as an **empirical quantile (e.g., 90th) of held-out error, by stratum** (urban/rural, POI density, evidence type), with the stratum named in the output | §14; GeoConformal evidence base | A small-city address and a metro address get different tolerances |
| **R8.3** | MUST widen to a parent stratum and say so when a stratum has too few observations | §14, §23 | Honest degradation instead of fake precision |
| **R8.4** | MAY use conformal methods for validation and reporting, but MUST NOT headline a coverage guarantee that the sample cannot support | §14 | Prevents an unfalsifiable claim |
| **R8.5** | MUST document that platform GPS accuracy values are 68th-percentile radii and MUST NOT be treated as ground truth | §13 (Android docs) | Stops a systematic overconfidence bug at the source |

## 9. Field evidence

| ID | Requirement | Evidence | Workflow change |
|---|---|---|---|
| **R9.1** | MUST capture evidence at visit time on-device (including when offline) and sync later, with the accuracy value and dwell | §16 (offline field apps exist); §13 | Evidence quality stops depending on connectivity |
| **R9.2** | MUST record the visit **outcome** and whether the person met was the borrower, a household member, or someone else | §15; RBI third-party rules | Connects the visit to the compliance question |
| **R9.3** | MUST treat observations as **evidence, never as labels** | §13 | Keeps a single bad visit from redefining an address |
| **R9.4** | MUST support **verify-first tasks** generated from low confidence (a cheap task: ask for a landmark, confirm the door) | §14, §15 | Replaces the wasted visit with a small interaction |

## 10. Integrity checks

| ID | Requirement | Evidence | Workflow change |
|---|---|---|---|
| **R10.1** | MUST implement, at minimum: mock-location flag, reported accuracy radius, speed plausibility between consecutive observations, duplicate-coordinate detection, and dwell realism | §13 | Catches the cheap and common spoofing patterns |
| **R10.2** | MUST convert integrity signals into a **weight** (degrade), not a rejection or an accusation | §13 | Agents do not learn to game a binary check |
| **R10.3** | MUST detect **collector-level anomalies** (one agent producing atypical weights/outcomes) as a monitoring metric | §13 | Surfaces incentive problems as a data-quality signal |
| **R10.4** | MUST NOT claim a spoof-detection rate, and MUST document residual risk of undetected spoofing | §13 ([UNKNOWN] on evasion rates) | Prevents an overclaim in front of a bank |
| **R10.5** | SHOULD capture an independent attestation where available (photo of the door/plate, NFC/QR at the premises) as supporting evidence, with privacy handling | [ASSUMPTION] — pattern is standard in logistics, not evidenced in collections | Adds a second, independent signal |

## 11. Purpose classification

| ID | Requirement | Evidence | Workflow change |
|---|---|---|---|
| **R11.1** | MUST classify a location as **home-like / work-or-business-like / other-or-unknown** with a confidence; a 7-way taxonomy is not required | §15 | Directly answers "may I serve a notice here?" |
| **R11.2** | MUST use **dwell + time-of-day + day-of-week + POI class + repeat visits**; single observations must not determine purpose | §15 | Prevents a shop visit from being learned as a home |
| **R11.3** | MUST **refuse notice/visit eligibility when the location is classified as work/business or third-party-likely**, unless the borrower has independently confirmed that address as their residence | §15; RBI prohibited practices (contacting colleagues/third parties) | Prevents the disclosure event that the law is designed to prevent |
| **R11.4** | SHOULD abstain rather than guess when the purpose signal is mixed | §15 | Verification instead of risk |
| **R11.5** | MUST keep the purpose belief **versioned and reviewable**, since it changes whether an action is lawful | §6.3 (PS2) | A reviewer can see why a notice was permitted last week and not today |

## 12. Storage

| ID | Requirement | Evidence | Workflow change |
|---|---|---|---|
| **R12.1** | MUST store: address record and parsed components; candidate set with source labels; belief (candidate, tier, radius, evidence count); observation log with integrity weights; notice/visit outcome log; gate decision log with rule version | §12, §14, §15 | The complete chain from text to permission |
| **R12.2** | SHOULD use PostGIS (or equivalent) with a **locality key (H3 or administrative)** for strata, landmark scoping and pack partitioning | §16 | Makes per-locality statistics and offline packs tractable |
| **R12.3** | MUST store the **provenance and licence status** of every coordinate that enters the system | §11.1 | Answers "where did this pin come from?" in any audit |
| **R12.4** | MUST apply retention classes: recovery record vs address evidence vs device telemetry | §6.1 (PS2 research: DPDP) | Prevents a retention conflict between the audit and the model |

## 13. Feedback loop

| ID | Requirement | Evidence | Workflow change |
|---|---|---|---|
| **R13.1** | MUST update the belief from weighted observations and recompute the tier and radius | §13 | The system improves where it acts, and only there |
| **R13.2** | MUST recompute error strata and radius quantiles on a stated cadence from held-out visits | §14 | Uncertainty stays calibrated as coverage shifts |
| **R13.3** | MUST feed notice/visit outcomes back as *outcome labels for the gate*, and as evidence only with an integrity weight | §15 | Distinguishes "the address was wrong" from "the borrower was out" |
| **R13.4** | MUST NOT train on vendor-returned coordinates | §11.1 (licence), §12 (circularity) | Keeps the model from learning the vendor's errors |

## 14. API design

| ID | Requirement | Evidence | Workflow change |
|---|---|---|---|
| **R14.1** | Minimal surface: `GET /address/{id}/belief` (candidates, tier, radius, purpose, evidence count, provenance) · `POST /visit-evidence` (observation → weight, belief delta, new radius) · `POST /notice-eligibility` (account, address → `sendable: bool`, reason, rule version, radius at decision) | §14, §15 | One object for the field app, one endpoint for the notice workflow |
| **R14.2** | MUST return the **rule version and the radius at decision time** with every eligibility answer | §6.3 (PS2) | The decision is reproducible months later |
| **R14.3** | SHOULD return **landmark directions** as text (on-device templating, no vendor map tile required) | §11.1 (map-use restrictions) | Directions work offline and stay licence-safe |

## 15. Offline capability

| ID | Requirement | Evidence | Workflow change |
|---|---|---|---|
| **R15.1** | MUST generate **per-district packs** (targets, candidates, radii, directions, landmark hints, PIN polygons) on a nightly cadence with versioning | §16 | Field work continues without connectivity |
| **R15.2** | MUST capture observations offline with a **monotonic local timestamp** plus a device attestation, and reconcile on sync | §13 (timestamps are integrity evidence) | Prevents back-dated forged evidence on sync |
| **R15.3** | MUST visibly **widen the radius** when a pack is stale beyond its validity | §14 | Staleness becomes an explicit loss of confidence, not an invisible error |

## 16. Minimum viable implementation (48 h)

Runtime geocode → PIN-polygon check → landmark match → top-3 candidates with an inspectable ranking → tier + empirical radius by stratum → **notice-eligibility gate** → one screen showing an address that **fails** the gate, the reason, and what evidence would change the answer → one synthetic scripted visit that flips the decision → one injected low-integrity observation that **widens without moving**. All synthetic inputs labelled `SYNTHETIC`.

## 17. Production-grade extension

Purpose classifier with measured performance → integrity model v2 (device integrity APIs, sequence plausibility, door-plate evidence) → landmark alias governance with human review → per-locality radius calibration at scale → district pack service with delta sync → gate analytics (block rate by reason, override rate, wrong-door rate) as the compliance dashboard → support for multi-address borrowers (home/work/relative) with per-address purpose beliefs.

---

## 18. Non-requirements (explicitly out of scope)

Building a geocoder · on-device geocoding · route/beat optimisation · full belief-distribution APIs exposed to users · LLM-in-the-loop for eligibility · conformal coverage as a headline · any accuracy claim not measured on held-out field outcomes · Bhuvan/ISRO data (terms) · storing commercial geocoder coordinates as training data.
