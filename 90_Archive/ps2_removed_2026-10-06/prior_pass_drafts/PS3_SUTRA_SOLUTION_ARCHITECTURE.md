# SUTRA — PS3 SOLUTION ARCHITECTURE
### Address confidence for the recovery decision

*26 sections as specified. SUTRA is deliberately **not** a geocoder: it consumes a commercial geocoder and adds the four things a collections operation needs and the market does not sell (recovery-visit evidence, integrity weighting, purpose classification, and a confidence gate on the irreversible action).*

---

## 1. Problem
Indian addresses are landmark-based, multilingual, transliterated and misspelt, so geocoders land at a locality centroid. CN needs lat/lon **plus a confidence radius** plus landmark directions, learning from field visits — and now, under RBI's 2026 framework, **an advance notice precedes the first in-person visit**, which makes a wrong-door address a *disclosure event*, not just an inefficiency.

## 2. User
Field agent (pin + radius + landmark route + no-disclosure script, offline) · field-ops manager (is this slot worth spending?) · compliance officer (was the notice legally sendable?) · address-data steward (which addresses need re-verification?).

## 3. Business objective
Raise the **right-door rate** and **eliminate notice-to-wrong-address events**, while reducing wasted field slots (₹220 marginal / ₹370 standalone `[MODEL]`). Distance error is a means, not the objective: a 90 m error in a dense colony can be one building wrong.

## 4. Address ingestion
Accept what CN actually holds: raw free text (one blob), optional PIN, city, landmark phrase, source, age, and any previously returned vendor coordinate. Reject nothing; classify confidence-of-input instead. Existing vendor output is stored as an **observation with provenance**, never as ground truth.

## 5. Multilingual normalisation
Deterministic-first (this is the honest lesson from the one Indian build we found `[EXT]`): abbreviation expansion (gali/lane, opp/opposite, nr/near), PIN extraction by regex anywhere in the string, comma/title normalisation, script detection, and transliteration variants for landmark matching. **No spell-correction layer**, because a wrong correction is worse than none. `[CUT]` libpostal/deepparse as a centrepiece — they are optional helpers, not the product (parsing is not the bottleneck: Shiprocket/Delhivery already resolve unstructured landmark addresses at national scale `[EXT]`).

## 6. Landmark / entity extraction
Extract (a) the landmark phrase, (b) its relation word (behind/near/opposite/next to/ke saamne), (c) ordinal or lane tokens ("2nd cross", "gali no 5"), (d) building/colony/complex names, (e) an optional PIN. Store all of them; the **landmark phrase is the validation key** for the later visit — if the returned GPS is near a POI whose name matches the phrase in the address, that is strong corroboration `[INFER]`.

## 7. Candidate generation
Consume a commercial geocoder (Delhivery Maps / Google Address Validation / Mappls eLoc) **at runtime, never cached as training data** `[EXT]`-ToS. Add OSM/POI context and a PIN-polygon check. Keep a small multi-hypothesis set (usually 1–5) rather than a single point. `[CUT]` a bespoke mulit-head H3 classifier — it duplicates what vendors already return.

## 8. GPS evidence model
For each returned visit, compute an **observation tuple**: (coordinate, timestamp, dwell seconds, distance to the address's current belief, arrival/departure context, outcome text, purpose classification, integrity weight). Observations are *evidence*, never labels.

## 9. GPS integrity model  ← the component that makes the learning safe
A per-observation credibility weight `w ∈ [0.2, 1.0]`, built from deterministic checks, not a black box:
| Check | Signal |
|---|---|
| Device attestation | mock-location flag, provider, reported accuracy — captured **at the moment of the visit** |
| Spatial plausibility | implied speed vs previous fix; inside the stated PIN/city at all? |
| Temporal plausibility | dwell vs reported visit duration; fix density during the claimed meeting |
| Cross-account duplication | same coordinate returned as "successful visit" for many unrelated accounts |
| Text–GPS agreement | does the remark's landmark resolve within X m of the coordinate? |
| Outcome economics | payment collected + receipt + OTP ⇒ high trust |
| Agent-level shrinkage | rolling duplicate/implausibility rate, shrunk to the population mean |
Fraud **degrades gracefully**: a poisoned observation is down-weighted and the radius **widens**; it never silently moves the belief. This is deliberately **not** a fraud-accusation system — output is a weight, not a verdict, because agents who fear grading will game harder `[INFER]`.

## 10. Home / work / shop classification
Purpose from: dwell distribution (home visits have long dwell, shop visits short and frequent), time-of-day profile (workday-hours at a workplace), POI context, outcome text ("met at shop", "house locked, neighbour said…"), and whether the coordinate is a *stop* on a multi-stop beat. Purpose changes the action: **a workplace or a shop is not a place to deliver a debt notice.**

## 11. Candidate ranking
`[CUT]` a LightGBM LambdaMART ranker in the MVP (candidates usually agree; ranking adds complexity without a decision change). Replaced by a transparent score: vendor confidence × PIN agreement × landmark-POI match × visit-evidence agreement. `[v2]` LTR returns only if candidate disagreement is shown to be frequent on CN's data.

## 12. Location estimation
Credibility-weighted **robust** estimate (weighted geometric median; Huber-style trimming). Explicitly **not** the mean: field GPS error is biased, not zero-mean `[EXT]` (Amazon's last-mile finding). Where the evidence is non-home, the estimate is produced for that purpose-tagged point, and the *residential* belief is left unchanged.

## 13. Confidence radius
Empirical quantiles of held-out error, computed per **stratum** (urban/rural, POI density, evidence count, purpose, whether the PIN agrees) rather than a global conformal claim. Output: `radius_90` (the width within which 90% of observed errors fell in that stratum) plus the evidence count. If the stratum has <30 observations, the radius is **widened to the parent stratum** and the output says so. `[CUT]` conformal coverage as a headline claim — unfalsifiable at small n and unnecessary for the decision.

## 14. Directions
Template-based, local-language landmark directions generated **on-device** ("Hanuman Mandir ke peeche, Sharma ration shop ke paas"), using the *original address text* plus the confirmed landmark set. No LLM call, no network. Directions are also the agent's **validation script**: "if you do not see a ration shop next to the temple, you are at the wrong place."

## 15. Offline architecture
Bundled per-district pack: the day's target list, each with pin + radius + landmark directions + the no-disclosure script + PIN/village polygons + a small local landmark list for fuzzy matching; SQLite + R-tree for spatial queries; write-ahead capture of GPS/dwell/outcome/attestation at visit time; delta sync on reconnect. Pack target <100 MB/district. Graceful degradation: a stale pack **widens** the radius visibly.

## 16. Feedback loop
Visit evidence → integrity weight → purpose classification → belief update → radius update → **tomorrow's notice/visit eligibility**. Alias learning: when a visit confirms a landmark phrase, the phrase↔coordinate pair enters the locality's landmark table, improving matching for **other accounts at the same landmark** (the compounding asset).

## 17. API design
```
POST /v1/address-confidence {address_text|address_id, purpose} ->
     {lat, lon, radius_90, confidence_tier, purpose_belief[], evidence_count, landmarks[], pack_id}
POST /v1/visit-evidence     {visit payload} -> {accepted, integrity_weight, belief_delta, new_radius}
POST /v1/notice-eligibility {account, address_id} -> {sendable: bool, reason, radius_at_decision, rule_version}
GET  /v1/directions/{address_id}?lang=hi&offline=1 -> {text, landmarks[]}
```

## 18. Database / PostGIS schema
```
address_raw(address_id, account_id, raw_text, pin_stated, city_stated, landmark_phrase, source, created_ts)
address_belief(address_id, purpose, lat, lon, radius_90, confidence_tier, evidence_count, updated_ts, model_version)
observation(obs_id, address_id, visit_id, agent_id, lat, lon, accuracy_m, provider, dwell_s,
            purpose, outcome_code, remark_text, integrity_w, ts)
landmark(locality_id, name_norm, phonetic_key, lat, lon, source  /*OSM | visit-confirmed*/, confirmations)
notice_gate_log(address_id, decision_ts, radius_at_decision, sendable, rule_version, decision_id)
```
PostGIS for point-in-polygon and distance queries; a `locality_id` (H3 or admin) keys the landmark table and the error strata.

## 19. Training pipeline
Weekly: recompute error strata and `radius_90` from held-out visits; re-fit the purpose classifier; refresh the landmark table; re-weight agent credibility. All on CN-held data. No vendor coordinate is ever a training label.

## 20. Inference pipeline
Fast path (online, <200 ms): cached belief + rule-based confidence tier — no model call needed for most addresses. Slow path (async): new/ambiguous addresses go to vendor geocoding + POI match, then the belief is cached. Nightly: rebuild the day's field lists and re-evaluate notice eligibility.

## 21. Monitoring
Abstention rate (tier=unknown) by locality · median and p90 radius by stratum · **notice-gate block rate and its reasons** · wrong-door reports from the field · integrity-weight distribution (a rise in low weights = an incentive problem, not a data problem) · stale-pack rate · drift in purpose classification.

## 22. Failure modes
| Failure | Detection | Fallback |
|---|---|---|
| No visits in a segment | evidence_count = 0 across the book | system returns vendor confidence only and **withholds the field/notice actions** |
| Landmark ambiguity (same name in two towns) | PIN disagreement, two clusters | require PIN agreement; otherwise tier = unknown |
| Borrower moved | repeated failed visits, "shifted" remarks | mark address stale → feeds PS2 as a contactability signal, not a geocode error |
| Vendor output unavailable | API error / ToS change | degrade to PIN centroid with tier = low and radius = locality width |
| Agents stop submitting evidence | observation volume drops | product problem, not model problem — surfaced to field ops with the agent-facing benefit |
| Gaming of check-ins | duplicate/implausible patterns | weight down and widen radius (never shift) |

## 23. MVP architecture (48 h)
Consume one vendor geocoder (or OSM fallback) → PIN-polygon check → landmark-POI match → empirical radius → **notice-eligibility gate** → offline pack (static file) → on-device directions template. `[CUT]` purpose classifier `[v2]`, `[CUT]` full integrity model (ship the three cheapest checks: mock-location flag, speed plausibility, duplicate coordinate), `[CUT]` LTR.

## 24. Production architecture
Polygon/POI store in PostGIS · district packs generated nightly and versioned · observation ingestion from CN's field app with attestation captured client-side · credibility service · landmark table governance with a human review queue for new aliases · notice-gate log feeding the compliance dashboard.

## 25. Demo architecture
One landmark-anchored address; a vendor pin with a 1.4 km radius that **blocks** the notice; a verification visit that returns a trail + dwell + remark; belief and radius update; the notice becomes sendable and the directions render **with the device offline**.

## 26. Evaluation metrics
**Address:** median/p90 error where ground truth exists (field-confirmed home visits only) · **abstention rate with tier** (the honest metric) · wrong-door rate from the field · notice-gate block rate.
**Learning:** does the radius actually shrink after visits, and does it *widen* when a poisoned observation is injected? (a test, not a claim)
**Business:** field-slot yield · avoided standalone trips · notices sent per verified address.
**Guardrails:** zero notices sent below the confidence threshold · zero visits to a purpose-tagged non-home point without an explicit rule.

*(Explicit limitation to state on every slide: all accuracy figures from synthetic or OSM-derived data are labelled synthetic and are **not** presented as real-world performance.)*
