# SUTRA — Frontend ⇄ Backend Contract v1 (2026-10-08)

**Status:** proposed, for the P0 implementation task. **Version:** `fe-be-v1` (interface), on top of
runtime `sutra-1.0` / `candidate-rules-v2` / `evidence-policy-v3` / `radius-map-v1` / `gate-v2`
`[S95]`. **Scope:** the read and write surfaces the interface needs, in the shape the interface needs
them. This document does not change any decision rule; it specifies what the already-computed
decisions look like on the wire.

Companions: `SUTRA_PRODUCT_UX_SPEC_2026-10-08.md` (screens), `SUTRA_BACKEND_GAP_AUDIT_2026-10-08.md`
(what exists today), `SUTRA_FRONTEND_DEMO_FLOW_2026-10-08.md` (the journey).

---

## 1. Principles the contract enforces

1. **The backend is authoritative for every derived quantity.** Tier, status, radius, `radius_basis`,
   evidence weights, eligibility action/reason, contradiction state, task priority and the winning
   reason codes are **never** recomputed in the frontend. If the UI needs a derived value, it is a
   field here.
2. **Every read is explicit about `as_of`.** Requests carry it; responses echo it (`as_of` +
   `computed_at` + `belief_version`). A response without them is invalid.
3. **A refusal is a 200 with a decision.** `candidate: null` is a complete answer. Errors (4xx/5xx)
   mean *no decision was produced* and carry no decision fields.
4. **Local metric plane only.** Coordinates are `x`, `y` in metres inside a named
   `coordinate_space`. No latitude, no longitude, no WGS84, no Web Mercator, no EPSG. The frontend
   must not introduce a projection layer.
5. **Provenance travels with the claim.** Every candidate carries where it came from; every belief
   carries the rule versions and the observation ids that produced it.
6. **Additive evolution.** v1 responses are supersets of today's response objects: existing flat
   fields remain (they are asserted by the acceptance suite), new structure is added in named blocks.
7. **Writes are append-only events.** No endpoint mutates a coordinate. The only writes are
   observation ingest and adjudication; both return receipts with idempotency keys.
8. **Determinism.** Same store + same `as_of` + same request → byte-identical decision fields
   (ordering of arrays is specified; no timestamps of *response* time inside decision fields).

**Notation for the field tables.** `req` ∈ {●required, ○optional, ∅never}. `as_of` describes how the
field behaves under a time cut. `pre-visit` = safe to show before any field visit. `deriv` = derived
server-side. `edit` = user-editable through this API.

---

## 2. `Coordinate`

| field | type | req | enum / notes | source (module · table) | as_of | pre-visit | deriv | edit |
|---|---|---|---|---|---|---|---|---|
| `x` | number (m) | ● | local plane metres | `sutra/candidates.py` · `observations` / `baseline_geocodes` | fixed per candidate | yes | yes | ∅ |
| `y` | number (m) | ● | local plane metres | same | fixed per candidate | yes | yes | ∅ |
| `coordinate_space` | string | ● | `sutra_local_metric_plane:<town_id>` (e.g. `sutra_local_metric_plane:T2`) | `sutra/config.py` + index manifest | invariant | yes | no | ∅ |
| `granularity` | enum | ● | `town·locality·street·rooftop` | `sutra/candidates.py` | fixed per candidate | yes | yes | ∅ |
| `radius_m` | number \| null | ● | null **only** when there is no candidate | `sutra/uncertainty.py` | recomputed at `as_of` | yes | yes | ∅ |

Rules: `x`/`y` are never rendered without `granularity` and `radius_m` (or an explicit
"radius withheld — n<15" note). The `coordinate_space` value is the *only* legal spatial identifier;
a UI that needs a "map" reads §10.

---

## 3. `Candidate`

| field | type | req | enum / notes | source | as_of | pre-visit | deriv | edit |
|---|---|---|---|---|---|---|---|---|
| `candidate_id` | string | ● | `c-<sha1[:12]>` | `sutra/candidates.py` | stable | yes | yes | ∅ |
| `address_id` | string | ● | e.g. `AD002936` | `sutra/indexes.py` · `addresses` | stable | yes | no | ∅ |
| `arm` | enum | ● | `frozen_baseline·locality_centroid·town_centroid·official_landmark·address_book·field_evidence·memory` — the frozen **vocabulary** also contains `place_neighbour`, which production never emits (`ENABLE_PLACE_NEIGHBOUR=False`, C2 locked; contract §4 of the normative contracts) | `sutra/candidates.py` | varies (evidence arms are time-gated) | yes | yes | ∅ |
| `source_ref` | string | ● | e.g. `visit:obs-VS002307`, `baseline:locality` | `sutra/candidates.py` | stable | yes | yes | ∅ |
| `x`, `y` | number (m) | ● | — | see §2 | — | yes | yes | ∅ |
| `granularity` | enum | ● | as §2 (candidate's own claim) | `sutra/candidates.py` | fixed | yes | yes | ∅ |
| `arm_rank` | int | ○ | deterministic intra-arm order | `sutra/candidates.py` | fixed | yes | yes | ∅ |
| `as_of_valid` | string \| null | ● | observation instant; null for static arms | `sutra/candidates.py` | time-gated | yes | yes | ∅ |
| `licence_class` | string | ● | always `official` | `sutra/config.py` | invariant | yes | no | ∅ |
| `provenance.built_from` | string | ● | e.g. `store observations (median of agreeing independent check-ins)`, `baseline_geocodes.csv` | `sutra/candidates.py` | stable | yes | yes | ∅ |
| `provenance.built_at` | string | ● | arm's own instant | same | — | yes | yes | ∅ |
| `provenance.n_observations` | int | ○ | evidence arms only | same | counts ≤ `as_of` | yes | yes | ∅ |
| `provenance.observation_ids` | string[] | ○ | the observations behind the coordinate | same | ids available ≤ `as_of` | yes | yes | ∅ |
| `provenance.spread_m` | number | ○ | agreement spread of the contributing check-ins | same | — | yes | yes | ∅ |
| `provenance.primary_eligible` | bool | ● | whether this candidate may be primary (single check-ins are **false** by rule) | `sutra/candidates.py` | — | yes | yes | ∅ |
| `provenance.agreement_arms` | int | ○ | how many arms agree | same | — | yes | yes | ∅ |
| `provenance.memory_evidence_derived` | bool | ○ | memory arm only — true iff the prior is evidence-derived (policy `emp-v1`) | same | — | yes | yes | ∅ |
| `provenance.stratum`, `baseline_precision` | string | ○ | arm-specific | same | — | yes | yes | ∅ |
| `score` | number | ● | the frozen rule score, 6 dp | `sutra/ranking.py` | — | yes | yes | ∅ |
| `score_reasons` | string[] | ● | e.g. `arm_prior:field_evidence=+0.620` | `sutra/ranking.py` | — | yes | yes | ∅ |
| `lost_reason` | string[] | ○ | **new**: why this candidate is not the winner (see §11) | `sutra/resolve.py` (to add) | — | yes | yes | ∅ |

---

## 4. `Uncertainty`

| field | type | req | enum / notes | source | as_of | pre-visit | deriv | edit |
|---|---|---|---|---|---|---|---|---|
| `radius_m` | number | ● | published radius for the candidate's stratum × tier/negative factors | `sutra/uncertainty.py` | recomputed | yes | yes | ∅ |
| `basis` | enum | ● | `empirical_p80` (only value today) | same | — | yes | yes | ∅ |
| `nominal` | number \| null | ● | declared nominal coverage; **null** when not calibrated | same | — | yes | yes | ∅ |
| `measured_coverage` | number \| null | ● | hit-rate of this radius on the calibration set | same | — | yes | yes | ∅ |
| `n_calibration` | int \| null | ● | calibration n behind the radius | same | — | yes | yes | ∅ |
| `source_stratum` | enum | ● | the stratum actually used after the n≥15 guard (`locality` today for all published cases) | same | — | yes | yes | ∅ |
| `fallback_applied` | bool | ● | true when the candidate's stratum was withheld and `locality` used instead | same | — | yes | yes | ∅ |
| `widened` | bool | ● | whether tier/negative/freshness factors applied | same | — | yes | yes | ∅ |
| `widen_reason` | enum \| null | ● | `negative_accumulation·calibration_fallback·stale·contested` | same | — | yes | yes | ∅ |
| `radius_map_version` | string | ● | `radius-map-v1` | `sutra/version.py` | invariant | yes | no | ∅ |

UI rule (research-driven `[U6]` `[U7]`): `radius_m` is never displayed without `basis`,
`n_calibration` and `measured_coverage`, and never phrased as a guarantee or as "95%".

---

## 5. `EvidenceSummary` and `EvidenceObservation`

**`EvidenceSummary`** (attached to every resolve/belief response)

| field | type | req | enum / notes | source | as_of | pre-visit | deriv | edit |
|---|---|---|---|---|---|---|---|---|
| `n_observations` | int | ● | observations for the address | `sutra/belief.py` · `observations` | ≤ `as_of` | yes | yes | ∅ |
| `n_positives` | int | ● | positive polarity | same | same | yes | yes | ∅ |
| `n_ambiguous` | int | ● | ambiguous polarity | same | same | yes | yes | ∅ |
| `n_negatives` | int | ● | negative polarity (total) | same | same | yes | yes | ∅ |
| `negatives_independent` | int | ● | independent negatives (drives demotion) | `sutra/evidence.py` | same | yes | yes | ∅ |
| `independent_confirmations` | int | ● | observations satisfying the F2.2 independence tuple | same | same | yes | yes | ∅ |
| `positive_weight_sum` | number | ● | Σ evidence weights | same | same | yes | yes | ∅ |
| `duplicate_claims` | int | ● | duplicate-media observations | same | same | yes | yes | ∅ |
| `newest_observation_at` | string \| null | ● | freshness | same | ≤ `as_of` | yes | yes | ∅ |
| `age_days` | number \| null | ● | age of the newest positive at `as_of` | `sutra/asof.py` | computed at `as_of` | yes | yes | ∅ |

**`EvidenceObservation`** (one visit; the timeline's atom)

| field | type | req | enum / notes | source | as_of | pre-visit | deriv | edit |
|---|---|---|---|---|---|---|---|---|
| `observation_id` | string | ● | `obs-<visit_id>` | `sutra/store.py` | — | yes | no | ∅ |
| `address_id` | string | ● | — | same | — | yes | no | ∅ |
| `observed_at` / `captured_at_device` / `server_received_at` | string | ●/○/● | UTC ISO-8601; device vs server clock are separate fields (audit) | same | ordering uses `observed_at` | yes | no | ∅ |
| `outcome` | enum | ● | `met_borrower·met_family·cash_collected·address_not_traceable·locked_premises·…` | official `field_visits` | — | yes | no | ∅ |
| `polarity` | enum | ● | `positive·ambiguous·negative` | `sutra/evidence.py` | — | yes | yes | ∅ |
| `evidence_class` | enum | ● | `positive·ambiguous·process·…` | same | — | yes | yes | ∅ |
| `weight` | number | ● | 0.0–1.0 evidence weight | same | — | yes | yes | ∅ |
| `weight_reasons` | string[] | ● | e.g. `gps_fine`, `dwell_short`, `outcome:met_family`, `trail_agrees` | same | — | yes | yes | ∅ |
| `independence` | object | ● | `{collector, day, media, period, source, space, visit}` | same | — | yes | yes | ∅ |
| `x`, `y` | number \| null | ● | observation position (null for negatives that carry no coordinate claim) | `observations` | — | **no** (post-visit) | no | ∅ |
| `gps_accuracy_m` | number | ○ | device-reported accuracy | official `visit_gps_points` | — | no | no | ∅ |
| `dwell_s` | number | ○ | time on site | official `field_visits` | — | no | no | ∅ |
| `media` | object[] | ○ | `{sha256, kind}` | official + store | — | no | no | ∅ |
| `agent_id` | string | ● | collector identity (integrity only) | official `agents` | — | yes | no | ∅ |
| `trail_agreement` | enum | ○ | `agrees·disagreement·loose` (derived from the trace) | `sutra/evidence.py` | — | no | yes | ∅ |
| `duplicate_claim_of` | string \| null | ● | set when media/phash repeats | same | — | yes | yes | ∅ |
| `policy_version` | string | ● | `evidence-policy-v3` | `sutra/version.py` | invariant | yes | no | ∅ |

Rule: **negatives carry no coordinate claim** — the UI must render `x`/`y` as absent for them, not as
`(0,0)` and not as the pin's position.

---

## 6. `BeliefVersion`

| field | type | req | enum / notes | source | as_of | pre-visit | deriv | edit |
|---|---|---|---|---|---|---|---|---|
| `address_id` | string | ● | — | `sutra/belief.py` | — | yes | no | ∅ |
| `belief_version` | int | ● | monotone per address | `sutra/store.py` · `belief_versions` | — | yes | yes | ∅ |
| `as_of` | string | ● | the instant the belief is *about* | `sutra/belief.py` | the argument | yes | no | ∅ |
| `computed_from` | object | ● | `{observations_upto, policy, rule_version, radius_map_version}` | same | — | yes | yes | ∅ |
| `candidate` | object \| null | ● | §3 or null | `sutra/candidates.py` | ≤ `as_of` | yes | yes | ∅ |
| `candidate_id` | string \| null | ● | — | same | — | yes | yes | ∅ |
| `tier` | enum | ● | `CONFIRMED·PROBABLE·APPROXIMATE·UNPLACEABLE` | `sutra/belief.py` | — | yes | yes | ∅ |
| `status` | enum | ● | `STABLE·CONTESTED·MOVED_SUSPECTED·STALE·UNPLACEABLE` | same | — | yes | yes | ∅ |
| `radius` | object | ● | §4 (`null` fields when unplaceable) | `sutra/uncertainty.py` | — | yes | yes | ∅ |
| `support` | object | ● | §5 EvidenceSummary | `sutra/belief.py` | — | yes | yes | ∅ |
| `reasons` | string[] | ● | e.g. `field_confirmed_x3`, `negatives_independent=2`, `negative_accumulation_cap`, `promotion:ok` | same | — | yes | yes | ∅ |
| `promotion_detail` | object | ● | the F2.2 tuple outcome (why promotion did/didn't happen) | `sutra/evidence.py` | — | yes | yes | ∅ |
| `score`, `score_reasons` | number/string[] | ● | winning candidate's score | `sutra/ranking.py` | — | yes | yes | ∅ |
| `place_id` | string | ● | `PL-<anchor>` | `sutra/memory.py` | — | yes | yes | ∅ |
| `arms_available`, `arms_considered` | string[] | ● | candidate arms produced / scored | `sutra/candidates.py` | — | yes | yes | ∅ |
| `eligibility` | object | ● | `{action, reason, rule_version, request_purpose, address_purpose, tier, status}` | `sutra/eligibility.py` | — | yes | yes | ∅ |

---

## 7. `PlaceHistory`, `Contradiction`, `VerificationTask`

**`PlaceHistory`** (`GET /v1/place/{place_key}/history`): `place_id`; `identity_rule`
(`colocation<=30m|adjudicated`); `member_address_ids[]` with per-member `{belief_version, candidate_id,
tier, status}`; `versions[]` — one entry per belief version `{belief_version, as_of, candidate_id,
tier, status, radius_m, trigger_observation_id}` for the anchor address; `observations[]` — the place's
observations in time order (id, at, polarity, weight, agent); `contradictions[]` — §7b;
`projection: true`; `as_of`. *Source:* `sutra/memory.py` (`place_state`) + `belief_versions` +
`observations`. *Gap:* version list and contradictions are P0 additions (the data exists; the read
model does not expose it).

**`Contradiction`**: `contradiction_id`; `kind` ∈ `CONTESTED·MOVED_SUSPECTED`; `detected_at`;
`separation_m` (max distance of strong observations from their median);
`threshold_m` (`CONTEST_SEPARATION_MULT × radius` = 2×); `strong_observation_ids[]` with their
positions; `negative_observation_ids[]` with independence; `effect` — the derived consequences
(`tier_cap`, `radius_widen_m`, `gate_action`, `task_id`); `coordinate_unchanged: true` (an explicit
field, because the UI must state it). *Source:* `sutra/belief.py` + `sutra/uncertainty.py` +
`verify_first_tasks`. *Gap:* P0 composition of existing facts.

**`VerificationTask`**: `task_id` (`VF-<address>-<cause>`); `address_id`; `place_id`; `town_id`;
`kind` (`verify_first·reverification·adjudication`); `cause` (§8 of the UX spec, five values);
`state` (`open·in_progress·resolved·superseded`); `priority` (0–1, rule-based); `created_at`;
`at` (event instant); `rule_version`; `tier`; `status`; `negatives_independent`; `radius_m`;
`evidence_refs[]` (the observations that caused it); `recommended_action` (string, rule-derived);
`clears_when` (the condition that closes it, in words — e.g. "a new independent confirmation within
the radius"); `history[]` (`{at, from, to, actor, note}`). *Source:* `sutra/memory.py` +
`task_events`. *Gap:* `recommended_action`, `clears_when`, `evidence_refs`, `history` are P0/P1.

---

## 8. `DecisionTicket` (the UI's single render unit)

One object that answers "what is the answer, how good is it, why, and what may be done with it".
Composed entirely from fields defined above; **no new semantics**.

| field | type | req | source |
|---|---|---|---|
| `address_id`, `place_id` | string | ● | resolve |
| `as_of`, `computed_at`, `belief_version` | string/string/int | ● | belief |
| `selected_candidate_id` | string \| null | ● | belief |
| `coordinate` | object \| null | ● | §2 |
| `uncertainty` | object | ● | §4 |
| `tier`, `status`, `granularity` | enum | ● | belief |
| `evidence` | object | ● | §5 summary |
| `gate` | object | ● | `{action, reason, rule_version, request_purpose, address_purpose}` |
| `why[]` | string[] | ● | ordered human-readable reasons: winning arm prior, granularity, promotion eligibility, locality match, agreement, negatives |
| `provenance.versions` | object | ● | the version block |
| `provenance.resolution_method` | string | ● | how the address was identified (`exact_text_match`, `fuzzy_token`, `address_context…`) |
| `alternatives_summary` | object | ● | `{n_alternatives, best_alternative_id, margin}` |
| `refusal` | object \| null | ● | `{reasons[], attempted[], area_context}` when `selected_candidate_id` is null |
| `task` | object \| null | ● | the open task, if any (links the decision to the queue) |

**Why:** `[U19]` N-best + uncertainty display; `[U18]` stakes-aware explanation. The frontend renders
the ticket verbatim; it re-derives nothing.

---

## 9. Model `ResolveResponse` (the composed read)

```
POST /v1/resolve
{ "address_text": "<free text>", "town_id": "T2" | null, "address_id": null | "AD002936",
  "request_purpose": "FIELD_NAVIGATION", "as_of": "2026-06-01T00:00:00Z", "include": ["alternatives","evidence","task","ticket"] }
```

Response = **today's flat object, unchanged** (all fields the acceptance suite asserts:
`candidate, candidate_id, score, score_reasons, granularity, tier, status, radius_m, radius_basis,
nominal, measured_coverage, n_calibration, source_stratum, widened, widen_reason, reasons,
request_purpose, address_id, address_purpose, directions, is_area_context, area_context, eligibility,
stage, arms_available, arms_considered, support, place_id, belief_version, resolution, versions`)
**plus** these additive blocks:

| block | type | req | notes |
|---|---|---|---|
| `coordinate` | §2 \| null | ● | null iff no candidate |
| `uncertainty` | §4 | ● | mirrors the flat radius fields, same values |
| `alternatives[]` | §3[] | ● | all generated candidates except the winner, ordered by score desc, then `candidate_id` asc; each with `lost_reason[]` |
| `decision_ticket` | §8 | ● | the single render unit |
| `evidence_summary` | §5 | ● | same values as `support`, named for the UI |
| `task` | §7 \| null | ● | open verification task for the address, if any |
| `as_of` | string | ● | echoed instant actually used |
| `computed_at` | string | ● | server response instant (audit; excluded from determinism comparisons) |

**Validation rules.** `as_of` must parse as UTC ISO-8601; `request_purpose` ∈ the five defined
purposes; `include` is a whitelist. Refusal responses set `coordinate = null`, `uncertainty` with all
null metrics, `alternatives: []`, `decision_ticket.refusal` populated, and **no coordinate-shaped
field anywhere** (D35 invariant — asserted by `tests/test_acceptance.py::test_T1_no_candidate_no_coordinate`).

**Determinism requirement.** Two calls with the same `(store state, as_of, request)` produce identical
values for everything except `computed_at`.

---

## 10. Map contract (local plane)

**Backend provides data only** (geometry + semantics), never styling or projection.

```
GET /v1/plane/{town_id}?as_of=&x0=&y0=&x1=&y1=        # optional clustered context
{ "coordinate_space": "sutra_local_metric_plane:T2",
  "extent": {"x_min": -2281.4, "y_min": -3418.3, "x_max": 2993.9, "y_max": 3246.8},   # town envelope, metres
  "grid_hint_m": 250,
  "addresses": [{"address_id":"AD002936","x":1130.5,"y":2970.0,"granularity":"rooftop","tier":"APPROXIMATE","status":"MOVED_SUSPECTED","radius_m":1202.6}],
  "localities": [{"locality_id":"L-12","name":"<official locality name>","x":…,"y":…,"radius_m":539.9}],
  "landmarks":  [{"landmark_id":"LM-77","name":"Community Hall","type":"community_hall","x":…,"y":…}] }

GET /v1/plane/address/{address_id}?as_of=             # the resolver's plane view
{ "coordinate_space": "…:T2", "extent": {...},
  "selected": {candidate §3 + "is_selected": true},
  "alternatives": [{candidate §3, "lost_reason": [...]}],
  "observations": [{observation_id, x, y, polarity, weight, observed_at}],
  "locality_ring": {"x":…, "y":…, "radius_m":539.9},
  "contradiction_markers": [{kind, x, y, separation_m}],
  "radius": {"x":…, "y":…, "radius_m":1202.6, "basis":"empirical_p80", "widen_reason":"negative_accumulation"} }
```

**Frontend owns:** viewBox mapping (`data-space → screen-space` linear transform, equal x/y scale so
the radius ring stays circular), symbolisation, hit-testing, keyboard focus, tooltips, the scale bar
("1 grid = 250 m"), and the "schematic local plane — not a geographic map" caption.

**Renderer decision: SVG**, not Canvas `[U23]`. Rationale: the plane view is bounded by the query
(one address's candidates + its observations + a locality ring: tens of objects, not thousands), each
object needs an accessible label, focus and hover state, and CSS theming keeps the design coherent
with the rest of the app. Canvas/WebGL is reserved for a future *town-wide* view if a cluster layer
exceeds a few thousand nodes; the contract already allows it because the backend returns data, not
drawing instructions.

**Forbidden in the frontend:** basemap tiles, roads, satellite imagery, north arrows or compass
roses, any lat/lon conversion, any EPSG/WGS84/Mercator code, any claim that the plane is geographic.

**Two scopes, deliberately separate.**

| Endpoint | Scope | Contains |
|---|---|---|
| `GET /v1/geometry/{address_id}?as_of=&town_id=&request_purpose=` (alias `/v1/plane/address/{address_id}`) | one address | candidate markers, the **authoritative** radius ring, observation markers, optional traces, extent |
| `GET /v1/plane/{town_id}?as_of=` | one town | **reference geometry only**: locality centroids, landmark points, town centroid, extent, counts |

The town plane never contains an address-level candidate — that is the address-scoped payload, and
keeping the two apart is what stops a town request from becoming a bulk coordinate dump no gate
approved. Both reply with `coordinate_space = sutra_local_metric_plane:<town>`, `units: metres`, a
padded bbox (`basis: bbox_of_returned_points_padded`) sufficient for a frontend `viewBox`, and a
`renderer_hint` (`preferred: svg`, graticule 10 m minor / 100 m major).
The plane is `sutra_local_metric_plane:<town>` and nothing else `[U21]` `[S95]`.

---

## 11. `lost_reason` vocabulary (why a candidate did not win)

Deterministic, produced server-side by comparing the winner to each alternative:
`lower_arm_prior`, `coarser_granularity`, `no_promotion_credit`, `single_observation_not_primary_eligible`,
`memory_not_evidence_derived`, `locality_name_mismatch`, `pin_unknown_penalty`,
`outside_town_penalty`, `landmark_ambiguous`, `coarse_precision_penalty`, `score_margin`.
Each entry may carry a value (`"score_margin +0.212"`). This is the N-best explanation surface
`[U19]`, and it is the reason `alternatives[]` is required rather than optional.

---

## 12. Endpoint contracts

| # | Endpoint | Today | v1 contract (target) | Priority |
|---|---|---|---|---|
| 1 | `POST /resolve` | implemented, flat object | §9 (flat + 8 additive blocks); `as_of` optional, defaults to now; echoes `as_of` | **P0** |
| 2 | `GET /place/{place_id}` | implemented (`place_state`) | + `versions[]`, `contradictions[]`, `unplaced` flag; keep existing keys | **P0** |
| 3 | `GET /tasks/verify-first` | implemented (town + limit) | `GET /tasks` with `cause`, `state`, `as_of`, `cursor`, facets; row = §7 task with `recommended_action` | **P0** |
| 4 | `GET /health` | implemented (versions + store meta) | §13 runtime status: pack version/age, counters, outbox-relevant stats, index digests | **P0** |
| 5 | `POST /evidence` | implemented (idempotent submit) | + validation echo, + `belief_before/after` summary, + task delta; unchanged semantics | **P0** |
| 6 | `GET /v1/address/{address_id}/observations` | not present | §5 rows in time order, `as_of`-gated | **P0** |
| 7 | `POST /v1/score_visit` | design only | pre-visit advisory scoring for live capture: agreement of a check-in with the current belief (`distance_to_candidate_m`, `within_radius`, hint text, reason codes). **Cannot write anything.** | **P1** |
| 8 | `POST /v1/adjudicate` | not present | the only human ground-truth write; stores an observation with `kind=adjudication`; returns receipt + `effect` | **P1** |
| 9 | `GET /v1/audit/{belief_id}` | not present | §14 chain walk | **P1** |
| 10 | `POST /v1/batch_resolve` | not present | ≤5,000 rows, per-row ticket summary + aggregate (refusal rate, tier mix, radius histogram). **Never** a bulk-accuracy claim. | **P2** |
| 11 | `GET /v1/overview` | not present | town counts (§4 of the UX spec) | **P2** |
| 12 | `GET /packs/{town_id}` | implemented | + `downloaded_at`/`age_days` echo when a device reports its pack version | **P2** |

**Idempotency.** `POST /evidence` and `POST /v1/adjudicate` require `idempotency_key`; a repeated key
returns the original receipt with `duplicate: true` and writes nothing (the receipt table exists but is
empty today — the replay path already proves idempotency in `tests/test_acceptance.py::test_T8_duplicate_observation_idempotent`).

---

## 13. Health / runtime status contract

```
GET /health
{ "ok": true, "versions": { …9 version strings… },
  "store": {"store_schema_version":"store-2","n_observations":5578,"n_belief_versions":2757,"n_tasks":278},
  "packs": [{"town_id":"T2","pack_version":"pack-T2-7247f0bd3d96","valid_days":7,"valid_until":"2026-06-08T00:00:00Z","bytes":1774492,"contains_truth":false,"contains_evidence":false,"contains_polygons":false}],
  "gauges": {"cold_addresses_by_town": {"T1":486,"T2":560,"T3":554}, "open_tasks_by_cause": {…}},
  "indexes": {"addresses":"7ab95ecf…","localities":"3fad5ac0…","landmarks":"a33054f9…"},
  "s_eval_firewall": {"reads_by_tools_total": 10, "tuning_uses": 0} }
```
`packs[].contains_truth = false` is itself a product statement (the pack deliberately ships no
answer key) and must be visible on the Method screen.

---

## 14. Audit contract

```
GET /v1/audit/{belief_id}
{ "belief": {belief_version, as_of, candidate_id, tier, status, radius…, score_reasons…},
  "chain": [
    {"kind":"observation","observation_id":"obs-VS002307","at":"2026-05-07T05:14:44Z",
     "actor":"FA006","payload":{"outcome":"met_family","gps_accuracy_m":5.9,"dwell_s":358,"media":[…]}},
    {"kind":"evidence","of":"obs-VS002307","weight":0.8,"polarity":"positive",
     "reason_codes":["business_hours","gps_fine","media_present","outcome:met_family","trail_agrees"],
     "independence":{…},"counted_as_confirmation":true},
    {"kind":"belief","belief_version":6,"as_of":"…","candidate_id":"c-28f5aface67c",
     "tier":"CONFIRMED","status":"STABLE","radius_m":566.9,"reasons":[…]},
    {"kind":"task","task_id":"VF-AD002936-MOVED_SUSPECTED","cause":"MOVED_SUSPECTED","state":"open"}
  ],
  "rule_versions": {…}, "immutable": true, "exportable": true }
```
Every node is read-only. The chain is assembled from `observations`, `evidence_scores`,
`belief_versions`, `task_events` — no new storage. *Gap:* the query surface is P1; the data exists.

---

## 15. Error / refusal contract

| HTTP | shape | meaning | UI |
|---|---|---|---|
| 200 | decision object (may contain `candidate: null`) | a decision was produced, including refusal | render the decision |
| 400 | `{error:"INVALID_REQUEST", detail, field}` | malformed request; **no** decision produced | inline field error |
| 404 | `{error:"unknown_place"|"unknown_address"|"not_found", detail}` | the id does not exist | "not found" state, no partial data |
| 409 | `{error:"IDEMPOTENCY_CONFLICT", detail}` | same key, different payload | surface the original receipt |
| 422 | `{error:"AS_OF_INVALID", detail}` | unparseable instant | fix the control |
| 503 | `{error:"RUNTIME_UNAVAILABLE", request_id}` | no answer | "nothing was written", retry |

Refusal vocabulary (200-with-decision) is fixed and reused by the UI verbatim: `no_candidate`,
`no_match_in_address_book`, `area_context_locality_only`, `tier_approximate`, `negatives_accumulated`,
`status_contested`, `radius_beyond_band`, `purpose_work_like`, `purpose_other`,
`purpose_unknown_low_confidence`, `unplaceable`.

---

## 16. Real fixture appendix (frozen examples, from the store at `as_of = 2026-06-01T00:00:00Z`)

These are **not invented** — they are copies of live responses collected during the audit and are the
demos' canonical records. Regenerate with the tool in `SUTRA_FRONTEND_DEMO_FLOW_2026-10-08.md`.

**A · Warm, confirmed, gate `SERVE` — `AD003067`** (text `H.NO. 221, GALI 12, NR COMMUNITY HALL,
PATEL NAGAR, DEVGARH NGR`, town T2, residence, 6 observations incl. 1 negative):
`candidate_id c-28f5aface67c` · `arm field_evidence` · `granularity street` · `x 1390.0 y -1818.0` ·
`score 0.987106` · `tier CONFIRMED` · `status STABLE` · `radius_m 566.9` (`empirical_p80`, n=24,
coverage 0.792, `widened true`, `negative_accumulation`) · `support {independent_confirmations 3,
negatives_independent 1, n_positives 4, n_observations 6, positive_weight_sum 2.798487}` ·
`belief_version 7` · `place_id PL-AD003067` · `eligibility {SERVE, purpose_home_like}` ·
`directions [{Community Hall, 1170 m, 209.3°, ambiguous true}]`.

**B · Warm, demoted by negatives, gate `VERIFY_FIRST` — `AD002936`** (text `Gali no-11, Azad Mohalla,
Devgarh Nagar - 970203`, town T2, residence, 6 observations: 2 positive, 2 ambiguous, 2 negative):
`candidate_id c-a7fcc592cd99` · `field_evidence @ rooftop` · `x 1130.5 y 2970.0` · `score 1.050441` ·
`tier APPROXIMATE` · `status MOVED_SUSPECTED` · `radius_m 1202.6` (`widened true`,
`negative_accumulation`) · `support {independent_confirmations 2, negatives_independent 2,
n_positives 2}` · `belief_version 7` · `eligibility {VERIFY_FIRST, negatives_accumulated}`.
Its real belief trajectory at visit instants: `APPROXIMATE/STABLE 809.8 m` (cold) → `PROBABLE/STABLE
708.6 m` → `CONFIRMED/STABLE 566.9 m @rooftop` → `APPROXIMATE/MOVED_SUSPECTED 1202.6 m` — **the
coordinate never moved; only the confidence and the radius did.**

**C · Cold — `AD000004`** (text `#81 gali 10 ganesh mandir ke bagal mein krishna puri devgarh nagar -
970202`, town T2, no observations): `candidate_id c-bb1142e5551f` · `frozen_baseline @ locality` ·
`tier APPROXIMATE` · `status STABLE` · `radius_m 809.8` (`calibration_fallback` widening,
`n_calibration 24`) · `belief_version 1` · `eligibility {VERIFY_FIRST, tier_approximate}` ·
`address_purpose {UNKNOWN, low, insufficient_evidence}`.

**D · Refusal** (text with no match): `candidate null`, `tier/status UNPLACEABLE`,
`reasons [no_candidate, no_match_in_address_book]`, `eligibility {VERIFY_FIRST, unplaceable}`,
`area_context null` — **no coordinate field anywhere in the body.**

**E · Task row** — `VF-AD000105-MOVED_SUSPECTED`: `{cause MOVED_SUSPECTED, tier APPROXIMATE,
negatives_independent 2, radius_m 1202.6, priority 0.8, state open, town_id T2,
rule_version candidate-rules-v2, at 2026-05-29T05:44:55Z}`.

**F · Pack** — `T2`: `pack_version pack-T2-7247f0bd3d96`, 1,774,492 bytes, 952 addresses, 77
landmarks, 12 localities, `valid_days 7`, `valid_until 2026-06-08T00:00:00Z`,
`contains_truth/evidence/polygons false`.

## 17. `ReasonCode` (typed expansion of the strings the backend already emits)

Today the runtime returns codes as bare strings in four places: `score_reasons[]` (arithmetic terms),
`reasons[]` (support/state facts), `widen_reason`, and `eligibility.reason`. The brief requires the
workbench step "expand reason codes"; the **frontend must not parse those strings** — the backend
composes typed entries so the arithmetic never has to be re-derived client-side.

| field | type | req | meaning | source | fixture_only |
|---|---|---|---|---|---|
| `code` | string | ● | the literal token (`arm_prior:field_evidence=+0.620`, `negatives_independent=1`, `negative_accumulation_cap`, `cold_start_no_field_evidence`, `promotion:not_ok`, `resolution:exact_text_match`, `purpose_home_like`) | verbatim from the response, never reworded | no |
| `kind` | enum | ● | `score_term` \| `support` \| `widen` \| `resolution` \| `gate` \| `refusal` | derived from which array the string came from | no |
| `subject` | string \| null | ● | the left-hand side of a score term (`arm_prior`, `granularity:street`, `arm_agreement_x4`), else null | split of the literal, done server-side | no |
| `effect` | number \| null | ● | the signed value of a score term (`+0.620`, `−0.060`), else null | split of the literal, done server-side | no |
| `direction` | enum | ● | `positive` \| `negative` \| `neutral` | sign of `effect`, or the support/state semantics | no |
| `label` | string | ● | one short human sentence for the evidence drawer (e.g. "arm prior: field evidence") | generated server-side from a fixed phrase table | no |
| `weight` | number \| null | ● | for `support` codes that carry one (e.g. an evidence weight) | evidence module, when present | no |

`ReasonCode[]` is **presentation of existing values**, not new logic: no threshold, weight or
candidate rule changes, and the ordered terms must reproduce `score` exactly when summed with the
arm prior — the contract test asserts that identity (P0-10).

---

## 18. `Overview` (operations landing; P1-5)

| field | type | req | meaning | source |
|---|---|---|---|---|
| `as_of` | string | ● | the cut every count is computed at | request |
| `towns[]` | object[] | ● | `{town_id, n_addresses, n_cold, n_warm, tier_mix{tier→n}, status_mix{status→n}}` | `runtime_indexes/addresses.json`, `belief_versions` |
| `queue` | object | ● | `{open_total, by_cause{cause→n}, oldest_at}` | `task_events` |
| `field` | object | ● | `{n_observations, n_evidence, last_observation_at, n_addresses_with_evidence}` | `observations` |
| `packs[]` | object[] | ● | `{town_id, pack_version, valid_days, valid_until, bytes, stale}` | `packs.build_pack` |
| `firewall` | object | ● | `{s_eval_looks_total, tuning_uses}` — the locked-read ledger, read-only | `counter_events` |

Counts only. **No accuracy percentage, no trend arrow, no sparkline, no "insights"** — the Overview
answers "what is the state of the operation", not "how good are we" (that is Method & Trust, §19).

---

## 19. `MethodTrust` (the one page allowed to state accuracy; P0 content, static + `/health`)

| field | type | req | meaning |
|---|---|---|---|
| `versions` | object | ● | the nine version strings (schema, rules, evidence, radius map, gate, purpose, directions, store, protocol) |
| `gate_table[]` | object[] | ● | `{address_purpose, tier, request_purpose, action, reason}` — the live gate reasons |
| `radius_map[]` | object[] | ● | `{stratum, p80_m, n, measured_coverage, publishable, fallback_to}` — `locality` publishable, others withheld under the n≥15 guard |
| `invariants[]` | string[] | ● | "no candidate → no coordinate", "one negative never relocates", "identity is place-keyed, never account-keyed", "append-only; corrections are new versions" |
| `loops` | object | ● | `{fast: {steps[], status}, slow: {steps[], status}}` — Fast = implemented; Slow = step-by-step labels, with the challenger labelled `evaluated_and_rejected` and model promotion `not_yet_implemented` |
| `claimed_numbers[]` | object[] | ● | `{metric_id, population, n, value, unit, median_m, as_of, config_hash, required_caption, s_eval_note}` — **exactly three entries**: cold independent `<500 m 71 %` (n 100, median 375.8), warm subset `96.77 %` (**n 31**, median 12.4), product lane `76 %` (median 202.2); hash `ac61cf2e71f77454…` |
| `pack_truth_flags` | object | ● | `{contains_truth:false, contains_evidence:false, contains_polygons:false}` — a product statement, shown verbatim |
| `fallback_statement` | string | ● | one sentence: what happens to an address the field never reaches |

**Hard display rule (frontend-enforced, backend-supplied).** Any `claimed_numbers` entry rendered
without its `population`, `n` and `required_caption` on the same line is a contract violation. No
other screen may render `claimed_numbers`.

---

## 20. `AsOfMetadata` (present on every read; the anti-ambiguity block)

| field | type | req | meaning | notes |
|---|---|---|---|---|
| `as_of` | string (ISO-8601 Z) | ● | the instant the answer is computed for | echoed, never re-derived by the UI |
| `computed_at` | string (ISO-8601 Z) | ● | when the answer was computed | excluded from any byte-comparison |
| `stage` | string | ● | `T1` = pre-visit (the only stage the read API serves) | never conflated with town ids `T1`/`T2`/`T3` |
| `request_purpose` | enum | ● | the caller's declared purpose | required on every resolve |
| `versions` | object | ● | the seven code-map versions on the decision | same block as the ticket |

Rule: **determinism is defined over `as_of` only** — two identical reads at the same `as_of` must
return byte-identical decision fields; `computed_at` is the only field allowed to differ, and the UI
must never display a decision without its `as_of` on screen.

---

## 21. As built — P0 implementation status (2026-10-08)

Everything below shipped in the **P0 backend productisation** pass. Nothing in the frozen intelligence
layer changed: no candidate arm, no ranking weight, no radius rule, no evidence policy, no gate rule,
no coordinate, and no new S-Eval read (ledger `s_eval_looks` 10 → 10).

### 21.1 Endpoints, as they now behave

| Endpoint | Status | Response highlights |
|---|---|---|
| `POST /resolve` | extended, **flat fields unchanged** | + `coordinate`, `uncertainty`, `alternatives[]`, `reason_codes[]`, `decision_ticket`, `evidence_summary`, `task`, `as_of`, `computed_at`, `town_id` |
| `GET /v1/belief/{address_id}?as_of=` | **new** | `belief` (verbatim `compute_belief` payload), `observation_refs[]`, `uncertainty`, `evidence_summary`, `reason_codes`, `coordinate_space`, `versions` |
| `GET /v1/address/{id}/observations?as_of=` | **new** | `observations[]` in storage order with `visit_id`, `coordinate_claim`, `captured{}`, `evidence{}`, `contributes` |
| `GET /v1/tasks?town_id=&cause=&state=&as_of=&limit=&cursor=` | **new** | `items[]` (+ `recommended_action`, `clears_when`, `evidence_refs[]`), `facets{by_cause,by_state,by_town}`, `next_cursor`, `total_matching` |
| `GET /v1/geometry/{address_id}?as_of=&town_id=&request_purpose=` | **new** | `coordinate_space`, `units: metres`, `points[]`, `rings[]`, `traces[]`, `extent`, `withheld`, `renderer_hint` |
| `GET /place/{place_id}?as_of=` | extended | + `versions[]`, `contradictions_detail[]`, `unplaced` (legacy `contradictions` id list untouched) |
| `GET /v1/place/{place_id}`, `GET /v1/health` | **new aliases** | same payloads as the legacy paths |
| `GET /health` | extended | + `packs[]`, `gauges{}`, `indexes{}` (index digests), `counters{}`, `offline{}`, `s_eval_firewall{}`, `store.counts{}`/`attestation{}` |
| `POST /evidence` | extended receipt | + `belief_before`, `belief_after`, `changed{fields}`, `task_delta{added}` — **semantics and idempotency unchanged** |
| `POST /explain`, `GET /tasks/verify-first`, `GET /packs/{town}`, `GET /` | unchanged | legacy behaviour preserved; verified in the contract suite |

### 21.2 Implementation decisions taken (each one is a deviation you should know about)

1. **`uncertainty` is `null` whenever `coordinate` is `null`.** A radius is a statement *about a
   position*; publishing "no coordinate, but here is its radius" is incoherent and leaks the shape of
   the withheld answer. The legacy flat `radius_m` stays (backward compatibility).
2. **Refusals publish no geometry at all.** `GET /v1/geometry` returns `points: []`, `rings: []`,
   `extent: null` and `withheld.suppressed{candidate_points, observation_points, rings}`. Evidence
   markers are withheld too: a marker's x/y is readable as a position, and the gate just refused one.
3. **`contradictions` keeps its legacy meaning** (address ids) on both place paths; the v1 objects are
   `contradictions_detail[]`. Renaming a shipped key would have broken existing readers.
4. **`evidence_refs` are reconstructed** as *the observations that raised the task* (negatives for
   `MOVED_SUSPECTED`, positives for `CONTESTED`) read at the task's own `at` instant, capped at 10,
   with `evidence_refs_basis` naming the rule. The stored task payload carries no observation ids.
5. **`reason_codes[]` is additive, never a replacement.** The raw strings stay verbatim in
   `score_reasons[]`/`reasons[]`; the typed entries carry `kind/subject/effect/direction/label`.
6. **`memory_not_evidence_derived` is in the vocabulary but is not emitted today.** The provenance key
   it needs (`provenance.memory_evidence_derived`) is on the candidate object, which the response does
   not carry. Emitting a guess would be worse than the gap → tracked as **P1 provenance passthrough**.
7. **`next_action` and `lost_reason` are presentation tables** over facts already in the response
   (gate action + reason; the score terms). The gate decision itself remains authoritative and no
   threshold is recomputed.
8. **`as_of` is echoed and `computed_at` added.** Determinism is defined over `as_of`: two reads at the
   same `as_of` are byte-identical apart from `computed_at`.

### 21.3 Where the code lives

| Layer | File |
|---|---|
| every v1 block, endpoint payload and presentation table | new module `sutra/views.py` |
| eight additive blocks on the frozen response | `sutra/resolve.py` (`_v1_blocks`) |
| receipt enrichment (before/after/changed/task delta) | `sutra/store.py` (`submit_observation`) |
| HTTP routes | `sutra/api.py` |
| the suite that pins all of it | new module `tests/test_contract_v1.py` (39 tests) |

### 21.4 Review deltas (second review pass, 2026-10-08)

| Delta | Where | Note |
|---|---|---|
| `alternatives[].rank` (+ `granularity`) | `sutra/views.py::alternatives_block` | rank = position in **one** deterministic ordering (score desc, `candidate_id` asc) over the whole ranked set; winner is rank 1. Granularity is read off the candidate's own `granularity:<value>` term — nothing new is scored |
| `GET /v1/plane/{town_id}` + `/v1/plane/address/{address_id}` alias | `sutra/views.py::plane_payload`, `sutra/api.py` | town reference geometry (localities, landmarks, centroid, extent); no address-level candidate |
| `capabilities` + `capabilities_note` on `GET /health` | `sutra/views.py::CAPABILITIES` | 20 capabilities over a closed status vocabulary; `metrics_api: not_implemented` records that no measured figure is served by the API |
| pack age | `GET /health.packs[]` | `built_for_as_of` + `age_days_at_cut` (computed at the frozen cut, not from the wall clock) |

### 21.5 Contract test coverage (51 tests, hermetic)

Normal/warm resolve · cold resolve · `VERIFY_FIRST` · refusal by purpose · refusal without candidate ·
unmatched text · alternatives + `lost_reason` vocabulary + determinism · typed reason codes ·
belief read (verbatim, as-of, unknown address) · observations (order, negative non-claim, future
exclusion) · place history (versions, contradictions, additivity) · queue parity with the legacy
reader, filters, facets, cursor pagination, cursor rejection · health (counts, gauges, digests,
firewall, no accuracy claim) · evidence before/after/changed/task-delta, replay idempotency · geometry
(local metric, refusal withholding, negative non-claims, traces) · determinism · byte-identical belief
recompute · as-of correctness · the negative-cannot-move-the-place invariant on the real transition
second · legacy flat-field survival · `explain`.

The suite reads a **sqlite backup copy** of the shipped store and uses throwaway stores for writes, so
a full test run leaves the shipped store byte-identical (verified: 0 delta on every table and counter).

---

---

## 22. As built — the console (2026-10-08)

The v1 read surface now has a client: a React + TypeScript + Vite console served **by the same Python
process that owns the API** (one origin, no CORS, no second host). Built assets land in `web/site`;
`GET /` serves them, and every API route is untouched.

| Screen | Binds to | Notes |
|---|---|---|
| Operations | `GET /v1/health` | runtime vs frozen evaluation separated; capability labels straight from the payload |
| Resolve | `POST /resolve` → `/v1/geometry` · `/v1/belief` · `/v1/address/{id}/observations` · `/v1/place/{id}` · `/v1/plane/{town}` | 3-zone workbench; candidates ↔ plane ↔ ticket cross-highlighting; belief replay at real observation instants |
| Places | `/v1/place/{id}` (+ belief, observations) | stored versions only; contradictions with `coordinate_unchanged` |
| Evidence | `/v1/address/{id}/observations` | address-scoped by necessity — there is no global evidence endpoint, so none is invented |
| Verify Queue | `/v1/tasks` | server-side filters, facets, cursor; read-only, with no control the runtime cannot perform |
| Method & Trust | `/v1/health` + published documents | two loops, capability labels, the three frozen evaluation populations kept separate |

**What the console is forbidden to do, and does not do:** re-derive tier, status, radius, gate action,
eligibility, priority or the winning reason; parse a reason string (it renders typed `ReasonCode`
objects only); draw a coordinate when the gate refused (`/v1/geometry` returns empty points and the
console shows a suppression panel instead); present a captured fixture as live data (a fixture is
labelled *captured* everywhere it can appear).

**Backend surface added for serving, complete list:** static asset serving + SPA fallback + `HEAD`
probes (`sutra/api.py`), `WEB_ROOT`, `tools/serve_runtime.py` honouring `$PORT`/`$HOST`, and an opt-in
`address_id` field on `POST /resolve` (absent ⇒ the legacy request is byte-for-byte unchanged; used by
"Open in Resolve"). Deployment files: `Dockerfile`, `.dockerignore`, `DEPLOYMENT.md`.

**Evidence:** `SUTRA_FRONTEND_SMOKE_REPORT_2026-10-08.md` (21/21 HTTP, 13/13 browser, 77/77 tests,
12 screenshots), `SUTRA_JUDGE_DEMO_SCRIPT_2026-10-08.md` (3-minute flow), `web/tools/browser_smoke.mjs`
(re-runnable), `tools/smoke_test.py` (re-runnable).

*Sources: `[U6]`–`[U8]` (uncertainty display), `[U12]`–`[U14]` (tables/disclosure), `[U15]`–`[U20]`
(audit + trust), `[U21]`–`[U23]` (schematic plane, SVG) per
`SUTRA_UIUX_RESEARCH_SOURCES_2026-10-08.md`; data-policy invariants `[S73]` `[S81]` `[S95]` per
`PS3_SOURCE_REGISTER.md`. Field-level semantics are reproduced from the frozen contract
`PS3_IMPLEMENTATION_CONTRACTS_2026-10-07.md`, which remains normative where this document is silent.*
