# SUTRA — PS3 SOLUTION ARCHITECTURE (FINAL)

**Phase 4, File 10 of 13.** 30 sections, as mandated. Replaces the Phase-2 hypothesis in `PS3_SUTRA_SOLUTION_ARCHITECTURE.md`.

**Companions:** `PS3_ADVANCED_ARCHITECTURE_RESEARCH.md` (15 architectures compared) · `PS3_ARCHITECTURE_OPTIONS.md` (7 options scored) · `PS3_ARCHITECTURE_SELECTION.md` (the decision) · `PS2_PS3_DATASET_REVIEW.md` (§2 reconciliation, §4 evidence, §5 traps) · `SANKET_SUTRA_SYSTEM_ARCHITECTURE_FINAL.md` (integration) · `ARCHITECTURE_RESEARCH_BIBLIOGRAPHY.md` (sources).

**Component labelling convention:** `①real system` · `②problem solved` · `③fed by` · `④if wrong` · `⑤why a simpler component cannot replace it`.

---

## 1. Problem, and the official statement it must satisfy

PS3's official statement is about **address/location intelligence for the field-recovery workflow** — the reconciliation with our framing is on the record in `PS2_PS3_DATASET_REVIEW.md` §2 and is not re-litigated here. The operational questions are: *can this borrower be found at this address; how far might we be wrong; is this visit worth a field slot tonight; and what did we learn about this address from the last visit?*

The three measured facts that define the problem `[DATA]`:

1. **The current point estimate is not good enough to walk to.** Median error 376.4 m, p90 839 m, only 9% under 100 m against 100 surveyed addresses.
2. **Public data cannot fix it.** Our own oracle over candidate sets built from free text: 370 m median, 2% under 100 m. Naive landmark snapping: 4,093 m, worse than baseline in 90% of cases.
3. **Field evidence can — by an order of magnitude.** On visits where the agent met someone: 385 m → **29 m** median on the same addresses, 82% under 100 m.

So the problem is not "geocode the address". It is: **state an honest belief about location, spend field evidence where it changes that belief, refuse to learn from evidence that is contaminated, and hand a probability — not a pin — to the decision that spends a field slot.**

## 2. What this system is, in one paragraph

**SUTRA** maintains an **`ADDRESS_STATE`** for every address: a location belief (point + radius + stratum), an evidence history, an integrity status, and a confirmation count. It parses and normalises Indian address text, retrieves candidates from a gazetteer and from our own confirmed-pin index, keeps the commercial geocoder's point as a *prior* (never as truth), fuses field evidence — GPS trails, dwell, outcome sign, media sanity — into a posterior, expresses uncertainty as per-stratum conformal radii validated on two independent samples, and publishes exactly two things outward: `P(truth within r)` for the PS2 allocator, and promotion events when a coordinate is confirmed twice. It is offline-first, licence-clean (the canonical coordinate is ours, not a vendor's), and it refuses to move a pin on the strength of a negative visit outcome.

## 3. Users and consumers

| Consumer | What they see | Why they care |
|---|---|---|
| Field officer (mobile app) | Search radius, not a pin: "search within 1.3 km" vs "within 40 m"; landmark hint; confirmation capture flow | Arrives at the right building; knows when to stop looking |
| Field supervisor | Visit queue ranked by *value of confirmation*; integrity flags on returned visits | Utilises slots on cases where certainty is worth money |
| PS2 allocator (machine) | `P(truth within 200 m)` + stratum radius + integrity status | Prices a field slot in expected rupees |
| Master-data steward | Low-confidence / high-value address queue | Fixes addresses before slots are spent |
| Data-engineering / legal | Provider audit log, cache policy compliance, licence register | Approves the data flow |
| Model risk | Coverage report per town and stratum; promotion audit | Validates the uncertainty claims |

## 4. Business objective (explicit)

```text
Maximise  Σ_visits [ P(met | address belief) · Value(met) − VisitCost ]
        + Σ_addresses [ Value_of_certainty · Δuncertainty ]         [the compounding term]
subject to: field-slot capacity (PS2-owned)  (hard)
            no coordinate may be promoted without 2 independent integrity-passing confirmations (hard)
            vendor licence constraints honoured: no permanent storage of vendor content (hard)
            a negative-outcome visit may never move a coordinate (hard — anti-poison rule)

Objective is expressed in rupees only where a rupee value exists; where it does not,
the term is reported as a ranked preference, not a currency amount.
```

**Primary KPI:** median location error on addresses with field evidence (target: the measured 29 m, not a made-up figure).
**Secondary KPIs:** % addresses under 100 m (baseline 9%); field-slot hit rate (`met_*` per slot); wasted-visit rate; confirmation coverage (% of addresses with ≥1 confirmation); time-to-confirmation.
**Honesty KPI:** published interval coverage vs nominal — the metric most systems refuse to publish.

## 5. Non-goals and explicit refusals

| Not building | Why (measured or sourced) | What would change it |
|---|---|---|
| A general-purpose national geocoder | Free-data ceiling 370 m `[DATA]`; GeoIndia's corpus is proprietary `[S-47bis]` | A licensed corpus + hierarchy gazetteer |
| Hierarchical cell (H3) prediction model | With 3,117 addresses it would learn to locality level — what the vendor already reports | ≥10k labelled addresses |
| HMM map matching | **No road graph in the data** — coordinates are a local metric plane with no polygons `[DATA]` | An OSM extract for the three towns |
| Landmark-based auto-correction | 4,093 m median, worse in 90% of cases `[DATA]` | A real POI dataset with attributes |
| A continuous-grid probabilistic map product | Fictional precision; unreadable for a field officer | A genuine decision-theoretic need for full densities |
| Storing vendor responses long-term | Google terms: lat/lng cache ≤30 days, no permanent storage of other content, no training on output `[S-48]` | A different provider contract |
| Voice/photo ML for identity | Out of scope; PS2 owns identity | — |

## 6. Architecture at a glance

```text
                     ┌──────────────────────────────────────────────────────────┐
 ADDRESS TEXT  ─────►│ S1 PARSE & NORMALISE   script · abbreviations · levels    │
 (multilingual)      │    open Indic NER + rules (offline)                       │
                     └───────────────┬──────────────────────────────────────────┘
                                     ▼
                     ┌──────────────────────────────────────────────────────────┐
                     │ S2 RETRIEVE   confirmed-pin index ⊕ gazetteer ⊕ landmark   │
                     │    priors (never auto-snap) · abstain when thin            │
                     └───────────────┬──────────────────────────────────────────┘
                                     ▼
   vendor geocode ───►┌──────────────────────────────────────────────────────────┐
   (time-limited      │ S3 PRIOR   point ⊗ stratum kernel   [rooftop 37.7 m …    │
    cache ≤30 d)      │            pincode 1,336.5 m — two-sample validated]      │
                     └───────────────┬──────────────────────────────────────────┘
 FIELD EVIDENCE ────►┌───────────────▼──────────────────────────────────────────┐
 • GPS trail        │ S4 INTEGRITY GATE   mock location · teleport · duplicate   │
   (accuracy/point) │      media · trail-vs-checkin distance · dwell sanity      │
 • dwell            │      → PASS / REJECT-with-code  (645 check-ins 11.6% >500m)│
 • outcome sign     └───────────────┬──────────────────────────────────────────┘
 • media hash                       ▼ PASS only
                     ┌──────────────────────────────────────────────────────────┐
                     │ S5 FUSION   stationary-cluster stop detection →            │
                     │    dwell-weighted, outcome-signed posterior                │
                     └───────────────┬──────────────────────────────────────────┘
                                     ▼
                     ┌──────────────────────────────────────────────────────────┐
                     │ S6 UNCERTAINTY   per-stratum conformal radius + coverage   │
                     └───────────────┬──────────────────────────────────────────┘
                                     ▼
                     ┌──────────────────────────────────────────────────────────┐
                     │ S7 CONTRACT   P(within 200 m) → PS2 allocator              │
                     │    promotion event → PS2 state   (two contracts only)      │
                     └───────────────┬──────────────────────────────────────────┘
                                     ▼
                     ┌──────────────────────────────────────────────────────────┐
                     │ S8 FEEDBACK   2 independent confirmations → promote →      │
                     │    index, priors, next-visit acquisition scoring           │
                     └──────────────────────────────────────────────────────────┘
```

## 7. Component inventory (the five-question test)

| # | Component | ① Real system | ② Problem solved | ③ Fed by | ④ If wrong | ⑤ Why simpler cannot replace |
|---|---|---|---|---|---|---|
| D1 | Address parser | `addressparser` (IndicBERTv2-SS+CRF, <30 ms) `[S-46]`; open Indic NER `[S-13bis]`; deepparse | Indian addresses are not parseable by the vendor alone; script/abbreviation variance | `addresses.csv` (3,117), 3 towns, 36 localities | Mis-parse silently relocates the street | Whole-string geocoding loses administrative-level evidence that drives the stratum radius |
| D2 | Candidate retrieval | Search/retrieval framing `[S-46bis]`; Overture addresses `[S-52]` | Provides the candidate set the point estimate is chosen from | Gazetteer + confirmed-pin index + landmarks as priors | Abstention fails → false confidence | A single API call returns *an* answer; retrieval returns *options with scores*, which is what makes abstention possible |
| D3 | Stratum prior | Google `location_type`/`partial_match` fields `[S-47]` are exactly the weak signal we upgrade | Baseline error is stratum-dependent by 35× | Vendor `precision` label + `derived_ps3_radius_calibration.csv` | Pincode addresses treated like rooftops → wasted trips | A global error radius is either useless (too wide) or wrong (too narrow) — the 37.7 m vs 1,336.5 m spread makes the stratum mandatory |
| D4 | Integrity gate | Spoofing detection practice: mock flags, cross-signal inconsistency `[S-58]`; Android `isMock`/`getAccuracy` (68% radius) | Prevents the map from learning from fabricated or careless evidence | `visit_gps_points` (160,406), check-ins, media hashes | 11.6% poisoned check-ins trained into the model | Averages/"outlier removal" cannot distinguish *dishonest* from *unusual*; the gate encodes physical impossibility and cross-signal contradiction |
| D5 | Stop detection + fusion | POI recognition from unreliable GPS via spatio-temporal density and intersecting line segments `[G20, master research]`; delivery geocode feedback `[S-56]` | Finds *where the agent actually stopped*, weighted by dwell and outcome sign | GPS trail (median 26 pts/visit, 9.8 m accuracy) | A wrong stop point confirms a wrong building | Trail centroid is provably wrong for a door (a 2-minute negative check-in sits 1,603 m from truth — negative outcomes *manufacture* false locations `[DATA]`) |
| D6 | Uncertainty (conformal) | Conformal spatial prediction `[S-53]`: 93.67% empirical coverage at 90% nominal vs 68.33% bootstrap | Honest intervals a planner can price | 100 surveyed addresses, stratified | Over-tight radius → failed visits; over-wide → unused coverage | Parametric error models are not distribution-free; bootstrap under-covers badly in this setting |
| D7 | Confirmation & promotion | Two-confirmation auto-update in logistics `[S-56]` | Turns visits into an asset that improves every future query | Integrity-passing visits | Reinforces a wrong pin | Single-visit overwrite is exactly how a bad pin becomes permanent |
| D8 | Address belief store (`ADDRESS_STATE`) | Master-data systems in banking (entity lifecycle) | One lifecycle object per address with provenance and confidence | All of the above | Conflicting records; no answer to "why do we believe this?" | A coordinate column cannot express belief, evidence or decay |
| D9 | Acquisition scoring | Active learning; EVSI shared with PS2 `[S-42]` | Chooses which address to verify next | Uncertainty × account value ÷ visit cost | Slots spent on low-value certainty | Ranking by error alone ignores that a 400 m error on a ₹4k account is not worth a slot |
| D10 | Provider layer | Multi-provider practice; Google `[S-48]`, Mappls `[S-50]`, Nominatim `[S-51]` | Licence compliance, outage resilience | Config + audit log | Licence breach (the most expensive failure in PS3) | Hard-coding one vendor makes the terms permanent; the layer makes them inspectable |

**Cut from the Phase-2 hypothesis (recorded):** home/work/shop *probabilistic* classification (kept only as a weak outcome-based prior — the data cannot validate a classifier); directions generation (Google/Mappls already do it; the value is the radius, not the turn list); a full Bayesian grid.

## 8. State model

### 8.1 `ADDRESS_STATE`

**Owner:** the address/entity record in the servicing master (production) / `sutra.address_state` in the demo. **Updated by:** events only.

| Field | Meaning | Update mechanism | Decay |
|---|---|---|---|
| `belief_point` | Best current estimate (lat, lng) | Fusion (S5) on promotion only | point does not decay; *confidence* does |
| `belief_radius_p50/p90` | Honest error band | Stratum kernel → conformal recalibration | recomputed at each label arrival |
| `stratum` | rooftop / street / locality / pincode (+ `unknown`) | Vendor label; upgraded by confirmation | downgraded if evidence conflicts |
| `evidence_set` | Ordered, weighted evidence records (visit, GPS cluster, landmark mention, vendor result) | append-only | age-weighted |
| `integrity_status` | CLEAN · FLAGGED · REJECTED(agent, reason) | Integrity gate (S4) | manual review clears |
| `confirmation_count` | Independent confirmations (distinct visits, distinct days) | Promotion rule | — |
| `canonical` | boolean — may be used as ground truth by downstream systems | 2 confirmations + integrity CLEAN | revoked on contradiction |
| `last_verified_at`, `attempts_to_confirm` | lifecycle telemetry | events | — |

### 8.2 `ACCOUNT_ADDRESS_LINK` (the PS2 join)

| Field | Meaning |
|---|---|
| `account_id`, `address_id` | the link (many-to-many; 3,117 addresses for 2,400 accounts `[DATA]`) |
| `link_confidence` | P(this address belongs to this borrower) — from PS2's identity model |
| `p_within_200m` | **the published contract value** (stratum radius + evidence + confirmation count) |
| `visit_value_estimate` | PS2's value of confirming this address |

### 8.3 Transition rules

| From | Trigger | To | Guard |
|---|---|---|---|
| `unverified` | vendor geocode only | `prior_only` | never `canonical` |
| `prior_only` | 1 integrity-passing met-visit | `confirmed_once` | count++, no promotion |
| `confirmed_once` | 2nd independent met-visit within radius | `canonical` | **two independent** confirms `[S-56]` |
| any | negative outcome (`not_traceable`, `no_such_person`) | unchanged, `evidence_set` appended with **negative weight** | **coordinate must not move** `[DATA]` |
| any | integrity REJECTED | `flagged` | excluded from fusion and feature generation |
| `canonical` | contradiction from a clean visit | `review` | manual steward decision; promotion revoked |

## 9. Evidence layer and what each item is worth

| Evidence | Signal | Weight rule | Measured basis `[DATA]` |
|---|---|---|---|
| Vendor geocode | prior point + stratum | Prior only; never promotes | Baseline 376 m median; stratum medians 37.7/134.9/367.4/1,336.5 m |
| Field GPS trail | probable location | Likelihood centred on stop cluster; scaled by per-point `accuracy` (median 9.8 m) | 385 m → 29 m on met visits |
| Dwell | confidence in a stop | ≥N minutes at the cluster → usable; <3 min → weak | Negative check-ins show 2-minute dwell at 1,603 m from truth |
| Outcome sign | direction of the update | `met_borrower`/`met_family` → positive; `locked`/`not_traceable` → **negative, never moves the point**; `shifted` → address obsolete, route to review | Outcome vocabulary with counts: 1400/1249/1114/1062/455/206 (+92 cash-in-remark) |
| Media hash | authenticity | Repeated hash across visits → integrity flag for the agent | FA009: 162/172 duplicates (26.6%) vs ≤1% elsewhere |
| Shared check-in vs own trail | consistency | >500 m → flag for review, exclude from learning | 645 check-ins (11.6%) |
| Landmark mention (text) | hint only | Prior/telephone aid for the officer; never a coordinate source | Naive snap 4,093 m median |

**The evidence rule that makes this architecture distinct:** *negative outcomes are information about the visit, not about the location.* The data proves why: `address_not_traceable` check-ins are 1,603 m from truth and 195 m from the pin, i.e. the agent marked the location they already had while failing to find the address. A naive fusion layer would drag the belief toward the pin — the opposite of learning.

## 10. Address parsing and normalisation

| Step | Technique | Reason |
|---|---|---|
| Script normalisation | Unicode fold (Devanagari/Bengali → canonical), transliteration table | Indian addresses mix scripts; 3 towns with local naming |
| Abbreviation expansion | Rule dictionary (`Rd`, `St`, `Ngr`, `Blk`, `Fl`, `Opp`, `Nr`) | Tokens drive retrieval |
| Level extraction | Indic NER + CRF (`addressparser`) `[S-46]` | Unit / building / street / locality / city / PIN |
| PIN validation | PIN↔locality↔town gazetteer from the dataset | PIN is the strongest single field (stratum + search area) |
| Alias resolution | Locality alias table (`localities.csv`, 36 rows) | Same place, many spellings |
| Output | Structured record + confidence per field | A parse is an explanation; a whole-string call is not |

**Honest limitation:** there are **no parse-level labels** in the dataset `[DISCOVERED]`, so parsing is delivered as a **rules + open-model** component with an evaluation on 30 hand-labelled addresses; it is never presented as a trained system.

## 11. Candidate retrieval and ranking

```
query(parsed) ─► [confirmed-pin index] ⊕ [gazetteer: PIN→locality→town] ⊕ [landmarks as priors]
                ─► candidates with scores ─► rank ─► if margin < τ or set empty → ABSTAIN → field task
```

| Candidate source | Role | Honest value |
|---|---|---|
| Confirmed pins (our own, promotion-backed) | Highest-precision source; grows with use | Compounding asset; day-one empty, demo-day non-empty |
| Gazetteer (PIN/locality/town) | Bounds the search area; supplies the stratum prior | Improves calibration, not point accuracy (locality ceiling 379 m `[DATA]`) |
| Vendor point | Prior | 376 m median |
| Landmarks | Hint/telephone-aid only | Never auto-snapped `[DATA]` |

**Ranking is rule-first** (PIN match > locality match > street-token overlap > distance to prior), with an optional learned ranker explicitly **excluded** on evidence: the oracle over candidate sets caps at 370 m `[DATA]`, so a learned ranker cannot beat its own candidate set, and 100 survey labels cannot validate one. `[BUILD IF TIME]` only as an experiment.

**Abstention is a feature, not a failure:** an address with no confident candidate is routed to the field task queue with a wide radius — the correct answer when the evidence is thin.

## 12. Spatial estimation (the fusion)

```text
prior:      X ~ kernel( vendor_point, σ_stratum )          # σ from the two-sample table
evidence k: L_k(x | trail_k, dwell_k, outcome_k, integrity_k)
posterior:  p(x | E) ∝ prior(x) · Π_k L_k(x)^{w_k}
estimate:   stop-cluster centroid (not trail centroid) with dwell weighting
output:     belief_point (unpromoted) · radius(p50,p90) · explanation weights
```

| Rule | Why |
|---|---|
| Stop detection by stationary clustering | The door is where the agent stood still, not where they walked |
| Weight by dwell and outcome sign | Negative outcomes cannot move the point `[DATA]` |
| Independent-evidence tempering | Trail + dwell are not independent features; avoid double counting |
| One visit → candidate; two → promotion | Prevents single-visit poisoning `[S-56]` |
| Never average a rejected visit | Integrity gate runs *before* fusion, not after |

**Coverage honesty:** where no field evidence exists (the majority of the 3,117 addresses), SUTRA returns the *stratum* radius — median 367.4 m at locality, 1,336.5 m at pincode `[DATA]`. It does not pretend otherwise, and PS2's allocator sees exactly that.

## 13. Uncertainty representation, calibration strategy, and the probability table

**Representation:** per stratum × town, two numbers — `p50` and `p90` radius — plus `P(within 200 m)` derived from the same empirical distribution. Not a continuous density.

| Probability / quantity | Method | Metric | Failure action |
|---|---|---|---|
| Radius (p50, p90) per stratum × town | Empirical quantiles from the surveyed sample, **validated on a second independent sample** | Two-sample agreement `[DATA]` | If samples disagree → publish the wider value; freeze promotions in that town |
| Conformal radius with finite-sample coverage | Split-conformal on the surveyed set, stratified `[S-53]` | empirical vs nominal coverage | Recalibrate; publish the gap |
| `P(within 200 m)` | Empirical CDF of |error| at 200 m within stratum | Reliability at 100/200/500 m | Widen; mark the stratum `low-confidence` |
| `P(met \| visit)` | Observed met rate by stratum, integrity-clean only | Brier vs base rate | Show base rate instead |
| Integrity pass rate | Per-agent distribution | Flag if an agent is >3σ from peers | Exclude the agent's visits from learning pending review |
| Coverage of promotions | Post-promotion error audit | Any promoted point >p90 later → revoke | Steward review |

**Why conformal rather than a parametric error model:** in spatial prediction, conformal intervals achieved **93.67% empirical coverage at 90% nominal, versus 68.33% for bootstrap** `[S-53]`; the difference is exactly the kind of silent under-coverage that makes a field team stop trusting the system.

## 14. Policy and permission layer

| Gate | Rule | Type | Source |
|---|---|---|---|
| `LG-01` | Vendor content: lat/lng cached ≤30 days; no permanent storage of other content; no training on API output | Hard | Google Maps Platform Service Terms §6 `[S-48]` |
| `LG-02` | Nominatim: ≤1 req/s, no bulk use, identify the application | Hard | Nominatim usage policy `[S-51]` |
| `LG-03` | data.gov.in sources are non-commercial (NDSAP); not mixed into a commercial pipeline | Hard | `[S-65]` |
| `LG-04` | Canonical coordinate must be field-confirmed (ours), never a vendor pin | Hard | Follows from LG-01 |
| `LG-05` | No address of a dispute-flagged account may enter the field queue (PS2 `PG-06` wins) | Hard | Cross-system policy |
| `LG-06` | Media (photographs) retained per client data-retention policy; hashes may be retained for integrity | Hard | DPDP minimisation `[VERIFIED]` |
| `LG-07` | Directions/navigation shown via a licensed provider at use time, not stored | Hard | `[S-48]` |

**Design consequence, stated plainly:** PS3's *canonical* layer is legally required to be evidence we own. That is not a compliance footnote — it is the reason the confirmation-and-promotion mechanism is the core of the architecture rather than an add-on.

## 15. Economic layer

```text
Value of location certainty for an account:
    V(i) = P(met | address belief) · ENV(recovery | met) − VisitCost
    and  ΔV(i) = V(i | belief after confirmation) − V(i | belief now)
Visit a field slot on address i iff  ΔV(i) > 0 and it ranks within the PS2 capacity constraint.
```

| Parameter | Central | Range | Source |
|---|---|---|---|
| Field slot cost | ₹180 | ₹90–350 | `[ASSUMPTION]` (travel time included) |
| Trace cost (comparison) | ₹104 | ₹60–150 | `[DATA]` |
| Value of a met visit (recovery term) | account-specific from PS2 EV | — | PS2 computes; PS3 consumes |
| Cost of a wasted visit | = slot cost + expected recovery foregone | — | Derived |
| Measured waste today | `not_traceable` + `locked` = 2,649 of 5,578 visits (47.5%) `[DATA]` | — | `[DATA]` |

**Where the money is:** the 47.5% of visits that end `not_traceable` or `locked` are the candidate pool for the radius + integrity + confirmation architecture; the honest target is not "eliminate them" (a locked house is not a location error) but **separate the location-error subset from the genuinely-absent subset** and stop spending slots to rediscover it.

## 16. Risk-sensitive layer (irreversible actions and poison control)

| Risk | Control | Evidence |
|---|---|---|
| A wrong promotion becomes permanent truth | Two independent confirmations; revocation path | `[S-56]`, `[DATA]` (single-visit poisoning risk) |
| A dishonest agent corrupts the map | Integrity gate before fusion; per-agent pass-rate monitor; exclusion pending review | FA009 162/172 duplicate media `[DATA]`; spoofing is caught by cross-signal inconsistency `[S-58]` |
| A negative outcome drags belief to the wrong place | Hard rule: negative outcomes never move the point | `not_traceable` check-ins 1,603 m from truth `[DATA]` |
| Wide radius mis-sold as precision | `P(within 200 m)` published, never a bare coordinate | §13 table |
| Licence breach by caching | Provider layer + audit log + 30-day TTL enforced in the data model | `[S-48]` |
| Over-flagging good visits | Published false-positive rate on flagging; tunable threshold | `[DATA]` validation on 1,477 visited addresses |

**λ-equivalent for PS3:** the promotion threshold (2 confirmations) and the minimum dwell are the risk parameters; both are published, both are tunable, and every rejection records which rule fired.

## 17. Allocation and optimisation layer (with PS2)

PS3 does not own the field-slot decision — **PS2 does**. PS3 supplies the *inputs* and the *acquisition score*:

```text
acquisition_score(i) = ΔV(i) · account_value_i / slot_cost
subject to: field-slot capacity (PS2) · notice rule (PG-02) · no dispute-flagged accounts (LG-05)
            per-officer geographic clustering to keep travel sane (production)
```

| Mode | Scope |
|---|---|
| Demo | Ranked list + the marginal slot value printed; 50-slot budget from the brief |
| Production | VRP-style routing with clusters (OR-Tools), matching the mTSP formulation used in the 2026 multi-criteria framework `[S-31]` |
| **Not built** | Continuous fleet optimisation — out of scope without real officer shift data `[GAP]` |

## 18. Actions and their failure paths

| Action | Success | Failure modes | Handling |
|---|---|---|---|
| Geocode address | point + stratum | provider outage · quota · partial match · nonsense result | Fallback to gazetteer locality point + wide radius; log the degradation; queue for field |
| Parse address | structured fields | unparsable (script/abbreviation) | Fall back to whole-string geocode; mark `parse_failed` for steward |
| Nav/route to address | officer arrives | pin wrong (the normal case at pincode stratum) | **Deliver a radius and a landmark hint, not just a pin**; the app must show "you are within the search area" |
| Visit capture | outcome + GPS + photo | no GPS fix · spoofed fix · no signal · app crash | Offline queue with local storage, upload-on-reconnect; a visit without a trail is `uneditable` and cannot promote |
| Integrity check | pass/reject with code | false positive on a good visit | Threshold tuning with published FP rate; officer can appeal with reason |
| Promotion | canonical coordinate | contradiction later discovered | Revocation event + steward review; downstream consumers notified |
| Provider switch | continuity | terms differ per provider | Provider abstraction with per-provider policy object; audit log per call |

## 19. Event sourcing, audit and replay

**Events (shared vocabulary with PS2 — see File 11):** `address.parsed`, `address.geocoded` (with provider + terms version), `visit.completed`, `visit.rejected_integrity`, `evidence.appended`, `coordinate.promoted`, `coordinate.revoked`, `provider.call` (audit), `radius.recalibrated`.

- Append-only; state is a projection; any address's belief history is reconstructible at any timestamp ("what did we believe on 12 August, and why?").
- The provider audit log is a first-class output: it is the evidence shown to legal that LG-01/LG-02/LG-03 hold.
- Promotion/revocation pairs form the map's changelog — the artifact that makes the compounding asset auditable.

## 20. Feedback loop, promotion and active learning

```text
visit.completed ─► integrity gate ─► evidence.append ─┬─► fusion (belief update)
                                                      ├─► confirmation_count++ → promotion at 2
                                                      └─► acquisition model refresh
promotion ─► retrieval index gains a high-precision entry ─► future addresses in that building/street are easier
```

| Loop | Cadence | Effect |
|---|---|---|
| Evidence → belief | event-driven | per-address accuracy |
| Belief → stratum calibration | weekly (or at label arrival) | radius table; coverage monitor |
| Confirmation → retrieval index | event-driven | compounding accuracy for neighbours |
| Promotion audit | monthly | revocation review |
| Agent integrity | weekly | exclusion/review decisions |

**Active learning with restraint:** the acquisition score is used to *order* visits (a ranking change PS2 can act on), never to trigger extra visits on its own. This keeps PS3 out of the "experimenting on borrowers" territory that the brief warns about.

## 21. Data mapping — the dataset controls the design (Part N)

| Table | Rows | Columns consumed | Trap preserved |
|---|---|---|---|
| `addresses.csv` | 3,117 | `address_id`, text, town, locality | 3,117 for 2,400 accounts → many-to-many link table |
| `baseline_geocodes.csv` | 2,880 (**237 missing**) | lat/lng, `precision`, `partial_match` | Missing geocode is a first-class state (`prior_only`→field task), never a silent skip |
| `surveyed_addresses.csv` | 100 | ground truth | The **only** labelled set; used for strata + conformal, stratified not per-address |
| `visit_gps_points.csv` | 160,406 | lat/lng, `accuracy`, ts | Median 9.8 m; accuracy is a 68%-radius convention `[S-57]`; 645 check-ins >500 m from own trail |
| `field_visits.csv` | 5,578 (1,477 addresses) | `outcome`, dwell, check-in coords | Negative outcomes must not move points; `address_not_traceable` sits 1,603 m from truth |
| `landmarks_poi.csv` | 240 | landmark name, location | Incomplete, 14/14 names repeat → priors only |
| `localities.csv` / `towns.csv` | 36 / 3 | gazetteer | Per-town calibration required (radius differs by town) |
| photos (hash only) | — | duplicate-hash check | FA009 26.6% duplicates → integrity signal |
| `verified_contact_points.csv` | 250 | *not used in PS3* | Belongs to PS2; listed to prevent accidental misuse (post-hoc, dated 2026-07-02) |

**Standing rule:** no coordinate in the deliverable is presented as ground truth unless it comes from `surveyed_addresses.csv` or from a 2-confirmation promotion.

## 22. Evidence catalogue and evaluation-integrity rules

| Evidence feature | Source | Guard |
|---|---|---|
| Vendor stratum (`precision`) | `baseline_geocodes` | Static, no leakage |
| Parse fields | parsed text | Deterministic |
| GPS cluster stats (spread, dwell, points, accuracy median) | `visit_gps_points` | **As-of**: only visits before the evaluation time |
| Outcome sign | `field_visits` | As-of; **negative outcomes excluded from point-moving evidence** |
| Integrity status | derived | Computed before fusion; flags never used as labels |
| Confirmation count | event-derived | As-of |
| **Banned** | Vendor pin as a *label*; `verified_contact_points` as a label; any future visit; post-hoc survey timestamps leaking into features | Enforced by a test that fails the build |

**Evaluation-integrity rule (from the dataset traps):** the 100 surveyed addresses are *labels*, not features. Every reported accuracy number states whether the surveyed set was inside or outside the calibration fold, and stratum tables are always reported as **two independent samples** because that is the evidence available `[DATA]`.

## 23. Interfaces and contracts

| Endpoint | Purpose | Key fields |
|---|---|---|
| `POST /address/ingest` | Parse + normalise + retrieve | address text → structured + candidates |
| `GET /address/{id}/belief` | Belief and evidence | point, radius p50/p90, stratum, confirmations, integrity |
| `GET /address/{id}/p_within?r=200` | **The PS2 contract** | probability + stratum + confidence class |
| `POST /visit/evidence` | Officer submission | outcome, trail, dwell, media hashes → gate decision |
| `POST /address/{id}/promote` | Promotion (system-only) | requires 2 independent confirmations; returns event |
| `GET /acquisition/queue` | Ranked confirmation targets | address, ΔV, slot cost, notice status |
| `GET /audit/provider` | Provider calls, terms versions | legal/compliance artifact |

**The two-contract rule (from the integrated design):** PS3 exposes `P(within r)` and receives `visit.completed`; PS2 exposes `visit_value_estimate` and receives promotions. Nothing else crosses the boundary — deliberate narrowness keeps both systems honest and independently testable.

## 24. Storage and schema

```sql
-- Demo: SQLite/Postgres on the dataset's metric plane. Production: PostGIS with SRID 4326.
CREATE TABLE address_state (
  address_id text PRIMARY KEY,
  belief_lat numeric, belief_lng numeric,
  radius_p50 numeric, radius_p90 numeric, stratum text,
  p_within_200m numeric, confirmation_count int, canonical boolean,
  integrity_status text, last_verified_at timestamptz);

CREATE TABLE address_evidence (
  evidence_id text PRIMARY KEY, address_id text, visit_id text,
  kind text,  -- gps_cluster | outcome | landmark | vendor | document
  weight numeric, payload jsonb, integrity text, ts timestamptz);

CREATE TABLE promotion_event (
  event_id text PRIMARY KEY, address_id text, from_state text, to_state text,
  confirmations int, evidence_ids text[], actor text, ts timestamptz);

CREATE TABLE provider_audit (
  call_id text PRIMARY KEY, provider text, endpoint text, purpose text,
  terms_version text, response_cached_ttl_days int, ts timestamptz);

CREATE TABLE radius_calibration (
  town text, stratum text, n int, p50 numeric, p90 numeric,
  p_within_100 numeric, p_within_200 numeric, p_within_500 numeric,
  sample text,  -- 'survey' | 'field_confirmations'
  as_of date);
```

Schema-enforced honesty: `address_state` has **no single-radius column** — a p50 and a p90 are structurally required; `provider_audit.response_cached_ttl_days` makes the 30-day rule visible in the data model.

## 25. Training and evaluation protocol

There is deliberately **very little training** in SUTRA, and that is a design claim:

| Component | Method | Evaluation |
|---|---|---|
| Parsing | Open pretrained NER + rules | 30 hand-labelled addresses; field-level accuracy |
| Fusion weights | Empirical grid search by stratum, selected on the surveyed sample | Improvement over baseline on two independent samples; must improve ≥80% of cases where evidence exists (`[DATA]`: 87%) |
| Radius table | Empirical quantiles + split conformal | Coverage at 90% nominal; two-sample agreement |
| Integrity thresholds | Rules + per-agent distributions | False-positive rate on 1,477 visited addresses; spoof-detection recall on the flagged set |
| `P(me t)` / stratum priors | Base rates | Brier vs base rate |
| Learned candidate ranker | **Excluded** (oracle 370 m; 100 labels) | Would be reported with an explicit "tuned and tested on the same 100" caveat if attempted |

**Protocol:** all evaluation on the surveyed set uses leave-one-town-out where possible; every table states its sample; synthetic-data limitation acknowledged in every accuracy claim (§30.3).

## 26. Inference pipeline and latency

| Path | Budget | Design |
|---|---|---|
| Offline batch (nightly) | minutes | Fusion over new visits, calibration refresh, promotion evaluation |
| On-demand address belief | <50 ms | Precomputed state read + contract value |
| Officer app: submit evidence | <200 ms local | On-device integrity pre-check, queue locally, upload on connectivity |
| Officer app: search radius & hint | instant (cached) | Works with **no network** — a hard requirement in the field |
| Provider geocode | 100–600 ms | Only on ingest or re-prior; never on the officer's critical path |
| Degradation | immediate | Provider down → gazetteer prior + wide radius; fusion unavailable → last state, flagged; gate unavailable → **no promotion** (fail-closed) |

## 27. Monitoring, drift and degradation

| Monitor | Threshold → action |
|---|---|
| Coverage (nominal vs empirical radius) | gap >5 pp → recalibrate; >10 pp → mark town `low-confidence` and widen published radii |
| Promotion rate | spike → audit (possible agent gaming); zero → check the queue is fed |
| Integrity rejection rate | >15% for an agent → review; portfolio-wide spike → retrain rules |
| Median error on confirmed addresses | regression → investigate fusion change before release |
| Provider partial-match rate | rise → re-prior or add provider |
| Address drift (new localities, renamed streets) | gazetteer refresh; unmapped addresses flagged for steward |
| Field-slot hit rate (`met_*`) | drop → the allocation contract or the radius table is wrong; alert PS2 |
| Duplicate-media rate | per-agent outlier test weekly `[DATA]` precedent |

## 28. Explainability

1. **Address belief card:** current point, p50/p90, stratum, evidence list with weights, confirmations, integrity status, and the last change with its event id.
2. **Field-officer view:** search radius, landmark hint, "why this radius" (one line: "locality-level address, last confirmed 14 months ago"), confirmation capture flow.
3. **Portfolio view:** error distribution by town and stratum; coverage; confirmation coverage; slot hit rate.
4. **Provider audit:** every external call with its licence version.

Rule: no explanation may reference information that is not in `address_evidence` or `provider_audit`.

## 29. Compliance and licence traceability

| Item | Status | Enforcement |
|---|---|---|
| Google Maps Platform Service Terms §6 (cache ≤30 days; no storage of other content; no training on output) | `[VERIFIED]` | `LG-01`, provider layer, TTL column |
| Nominatim usage policy (1 req/s; no heavy use) | `[VERIFIED]` | `LG-02`, rate limiter |
| data.gov.in NDSAP (non-commercial) · India Post directory | `[VERIFIED]` | `LG-03`, licence register |
| Overture addresses (open, licence-permissive) | `[VERIFIED]` | Preferred source for a gazetteer extension |
| Mappls / eLoc (India-hosted; pricing not public) | `[VERIFIED, pricing UNKNOWN]` | Candidate provider; commercial terms to be obtained |
| Android `Location.getAccuracy()` = 68% radial confidence; `isMock` flag | `[VERIFIED]` | Fusion weighting and integrity gate |
| DPDP Rules 2025 — purpose limitation & minimisation | `[VERIFIED]` | Media hashes retained, photographs per client policy; address data used only for recovery |
| RBI Amendment Directions (effective 1 Jan 2027) — visit notice and hours | `[VERIFIED]` | `LG-05` + PS2 gate `PG-02` |
| Synthetic dataset caveat | README declares synthetic; landmarks incomplete | Every `[DATA]` claim carries the label |

## 30. Build plan, metrics, demo, and open risks

### 30.1 48-hour build order (matches the backlog in §6)

| Phase | Hours | Deliverable | Acceptance number |
|---|---|---|---|
| S-A | 0–2 | Subset + integrity gate on real data | Reproduce: 645 check-ins (11.6%) >500 m; FA009 duplicates 162/172 `[DATA]` |
| S-B | 2–6 | Stratum radius table + `P(within 200 m)` | Two-sample agreement; coverage published |
| S-C | 6–12 | Fusion on met-visits | Reproduce 385 m → 29 m; 82% <100 m `[DATA]` |
| S-D | 12–18 | `ADDRESS_STATE` + evidence store + promotion rule | One address promoted live from two visits with evidence visible |
| S-E | 18–26 | Contract wire to PS2 | Changing a radius visibly changes the field-slot ordering |
| S-F | 26–34 | Parse + retrieval (basic) | 30-address parse eval; retrieval returns candidates or abstains |
| S-G | 34–42 | Officer view + demo narrative | Live: the same address before/after evidence, radius shrinking |
| S-H | 42–48 | Write-up, red-team, freeze | Every number labelled `[DATA]` / `[S-nn]` / `[ASSUMPTION]` |

**Cut-line:** S-B + S-C + S-E ship first (they are the measured claims and the integration); S-D next; S-F/S-G shrink to a scripted demo if needed. The submission never degrades to "we call an API".

### 30.2 Metrics the judges should check

| Claim | Metric | Baseline | Ours | Class |
|---|---|---|---|---|
| Honest error band | median error by stratum | 376 m overall | 37.7 / 134.9 / 367.4 / 1,336.5 m | `[DATA]` |
| Field-evidence gain | median error on met visits | 385 m | **29 m** (82% <100 m) | `[DATA]` |
| Intervals are truthful | empirical vs nominal coverage | 68.33% (bootstrap) | 93.67% (conformal) | `[S-53]` |
| Bad evidence is excluded | flagged check-ins | 11.6% unflagged | flagged, excluded from learning | `[DATA]` |
| Compounding | confirmations per address | 0 (no mechanism) | promotion on 2 → retrieval index | design + `[S-56]` |
| Compliance | vendor content retention | unmanaged | TTL-enforced, audited | `[S-48]` |

### 30.3 Open risks and honest limits

| Risk / limit | Consequence | What would change it |
|---|---|---|
| 100 surveyed addresses only | Radii are stratum-level, not per-address; a new town needs its own calibration | More labels |
| Synthetic data | The 29 m result is a mechanism demonstration on synthetic evidence; real GPS in dense Indian cities will be worse | A real pilot extract |
| No road graph | Stop detection substitutes for map matching; door-level inference is heuristic | OSM extract + HMM `[S-54]` |
| Field coverage | Most addresses will never be visited at mobile precision → the honest radius is the answer, not a point | Field programme or third-party verification |
| Agent gaming | Integrity rules catch the crude cases (duplicate media, teleport) but not all | Device telemetry, more signals |
| Provider pricing/terms for Mappls | Unknown `[UNKNOWN]` → cost model incomplete | Commercial negotiation |
| Real-world address ambiguity | Cultural/landmark naming is not fully modelled | A real gazetteer and local knowledge capture |
