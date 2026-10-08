# SUTRA — IMPLEMENTATION CONTRACTS (2026-10-07)

*Status: normative. This is the document implementation is built against. The architecture is LOCKED
(`PS3_ARCHITECTURE_LOCK_CANDIDATE_2026-10-07.md`); the data policy is binding
(`PS3_FINAL_DATA_AND_ARCHITECTURE_FREEZE.md`, `[S95]`). Where any earlier document disagrees with a schema, interface or
rule below, **this document wins** and the earlier text is to be read as history. No training happens in this phase.*

Conventions: field names are `snake_case`; lengths in metres; coordinates are in the **declared local metric plane**
(`PS3_CANONICAL_SCHEMA.md` §4 — no reprojection, no CRS juggling); all timestamps ISO-8601 UTC with the offset recorded;
all identifiers opaque strings; every artefact carries its versions (§12). 🟩 = GREEN (build now) · 🟨 = YELLOW
(build if time) · 🟥 = RED (production-only, not built in the 48 h).

---

## 1. Vocabulary (frozen names)

| Name | Meaning | Never |
|---|---|---|
| `request_purpose` | the **caller's declared** purpose — an access-control input (why the coordinate is being requested) | an inference; a model output |
| `address_purpose` | what the place **is**: `HOME_LIKE` · `WORK_LIKE` · `OTHER` · `UNKNOWN` | a permission |
| `eligibility` | the permitted action: `SERVE` · `VERIFY_FIRST` · `REFUSE` | a purpose |
| `official frozen baseline geocode arm` | the candidate arm fed by the supplied `baseline_geocodes.csv`; arm id `frozen_baseline` | a live vendor call (there are none) |
| arm id aliases | `frozen_baseline` ≡ the value `vendor_pin` found in pre-2026-10-07 derived CSVs — **display-name change only, no data change** | — |
| S-Eval · S-Train · S-Val | the evaluation/supervision sets defined in §2 | any other split |

**Terminology note.** The word *vendor* in older artefacts refers to the provider whose output is already embedded in
the supplied baseline file. **No Google/Mapbox/HERE/Mappls (or any) service is called in the benchmark or the demo**;
the provider adapter exists only as a named production extension.

## 2. TRAIN/EVAL PROTOCOL (immutable — no experiment may invent its own split)

| Set | Membership (exact) | Rules |
|---|---|---|
| **S-Eval** | all **100** surveyed addresses (`surveyed_addresses.csv`), fixed forever | never trained · never tuned · never used to pick features, thresholds, early stopping or prompt-like settings; every query increments the **test-look counter**, reported per experiment |
| **S-Train / S-Val** | **operational supervision only**: candidate–place pairs for addresses carrying promotion-grade confirmations (independence per F2.2) | nested grouped CV: **outer folds = place blocks** (`ps3_place_blocks.csv`), **inner folds = accounts**; S-Val = inner held-out; loop experiments use time-ordered cut-points |
| **S-Eval firewall** | excluded from every supervision/feature-fit/tuning set: the 100 surveyed addresses · their **100 accounts → 128 addresses** · every **place block containing a surveyed address → 99 blocks** (union **145 addresses = 4.7% of 3,117**) `[S96]` | computed in code with a receipt; remaining supervision pool **2,972 addresses (841 with ≥1 met visit)** |

**Hard rules.** (1) A result that cannot state its set membership, fold construction and firewall count is invalid.
(2) Warm/cold/lane reporting keeps the three populations of Amendment A1 (all 100 · validation+test · leave-block-out).
(3) If the F2.2-rated supervision pool proves too thin, **no learned ranker ships** — the rule baseline is the product,
and that outcome is pre-registered and reportable.

## 3. Interfaces (code-level, frozen signatures)

```python
# resolution  (deterministic, no model, < 250 ms p95)
def resolve(address_text: str, town_hint: str | None,
            as_of: datetime, request_purpose: PurposeCode) -> ResolveResponse

# evidence    (append-only; the ONLY write path into the store)
def submit_observation(obs: Observation, idempotency_key: str) -> ObservationReceipt

# memory      (read-only views; projections are never feature sources)
def place_state(place_id: str, as_of: datetime) -> PlaceState
def verify_first_tasks(town_id: str, limit: int = 100) -> list[Task]

# packs       (offline; versioned; no polygons)
def build_pack(town_id: str, valid_days: int = 7) -> PackManifest

# learning    (governed; never on the request path)
def replay(cutpoints: list[datetime]) -> ReplayReport          # SIMULATION
def candidate_metrics(split: SplitSpec) -> MetricsReport       # split must reference §2
```

Every implementation must expose the frozen **ranker interface** (§6.3) and must be importable without network access.

## 4. Candidate record

```json
{
  "candidate_id": "c-7f3a…",            // stable within a response
  "address_id": "AD000527",
  "arm": "frozen_baseline | locality_centroid | town_centroid | official_landmark | address_book | field_evidence | memory | place_neighbour",
  "source_ref": "baseline:locality|locality:L-0148|landmark:P-0022|address:AD000123|visit:V-…",
  "x": 940.8, "y": 2638.2,
  "granularity": "rooftop | street | locality | pincode | town",
  "arm_rank": 1,
  "licence_class": "official",
  "as_of_valid": "2026-05-15T00:00:00Z",   // evidence-backed arms only; null otherwise
  "provenance": {"rule_version": "…", "built_at": "…"}
}
```
Invariants: `licence_class == "official"` always; `place_neighbour` appears **only** if experiment C2 admitted the index;
`as_of_valid` present ⇔ arm ∈ {field_evidence, memory, place_neighbour}; no candidate carries a truth column.

## 5. Evidence record (Observation) — append-only

```json
{
  "observation_id": "UUID (client-generated — the idempotency key)",
  "kind": "visit | adjudication | ingest",
  "address_id": "AD000527", "account_id": "AC000123", "agent_id": "AG004",
  "outcome": "met_borrower | met_family | cash_collected | neighbour_says_shifted | locked_premises | no_such_person | address_not_traceable",
  "evidence_class": "positive | ambiguous | process",
  "checkin": {"x": 941.2, "y": 2637.9, "gps_accuracy_m": 9.8},
  "dwell_s": 207,
  "captured_at_device": "…", "server_received_at": "…",
  "local_seq": 41,                         // monotonic per device
  "media": [{"sha256": "…", "kind": "photo"}],
  "remark": "…raw…",
  "integrity": {"weight": 0.62, "reasons": ["duplicate_media_cluster", "dwell_short"],
                "independence_tuple": {"visit":"V-…","collector":"AG004","period":"2026-05","media":"m1","source":"field","space":"ok"}},
  "policy_version": "evidence_policy-v3"
}
```
Rules: never updated in place (corrections arrive as **new** observations); a second device submitting the same visit is
stored as a linked **duplicate claim**, never as a second confirmation (F2.2); `address_not_traceable` may never carry a
coordinate claim; media hashes computed on-device.

## 6. Belief, ranking and memory

### 6.1 Belief version
```json
{"address_id":"AD000527","belief_version":14,"computed_from":{"observations_upto":"2026-06-01T00:00:00Z","policy":"evidence-policy-v3"},
 "candidate_id":"c-7f3a…","tier":"CONFIRMED|PROBABLE|APPROXIMATE|UNPLACEABLE","status":"STABLE|CONTESTED|MOVED_SUSPECTED|STALE",
 "support":{"independent_confirmations":2,"negatives_independent":0},"reasons":["field_confirmed_x2","locality_match"]}
```
The belief is a **pure function** of the store (M3): re-deriving it must reproduce the exact JSON (deterministic test).

### 6.2 Place memory record
```json
{"place_id":"PL-…","member_address_ids":["AD000527","AD001988"],"identity_rule":"colocation<=30m|adjudicated",
 "state":"WARM|CONFIRMED|CONTESTED|STALE","coordinate":{"x":…,"y":…,"radius_m":…,"basis":"empirical_p80","n_calibration":24},
 "history":[{"observation_id":"…","at":"…"}],"merge_review":"none|POSSIBLE_MATCH(PL-…)"}
```
Never keyed by account; merges/splits are reversible events; contradictions live here, not in a client cache.

### 6.3 Ranker interface (frozen; implementation chosen by experiment D)
```python
def rank(candidates: list[Candidate], features: dict, as_of: datetime) -> list[RankedCandidate]
# RankedCandidate = {candidate_id, score: float, reasons: [str]}  — inspectable, deterministic, ≤15 features (M2)
```
Rule baseline ships by default; logistic/LambdaMART are challengers; **the interface never changes**, so swapping the
implementation is a configuration change.

## 7. Radius result

```json
{"radius_m": 539.9, "basis": "empirical_p80", "nominal": null, "measured_coverage": 0.792, "n_calibration": 24,
 "source_stratum": "locality", "widened": false, "widen_reason": null}
```
Rules: `nominal` non-null **only** where a nominal level was measured; pincode stratum is **withheld** (transfer failure)
and falls back to its parent with `source_stratum` naming the parent; n < 15 → fallback, labelled; `widened=true` when a
stale pack or accumulation of negatives forced a widening (always with a reason).

## 8. Purpose result

```json
{"address_purpose": {"class": "HOME_LIKE", "confidence": "medium", "basis": ["met_x2", "weekday_daytime_visits", "not_office_type"]},
 "request_purpose": "NOTICE_SERVICE",     // caller-declared, access-control input
 "model_version": "purpose_rules-v1"}
```
`class ∈ {HOME_LIKE, WORK_LIKE, OTHER, UNKNOWN}`; single observations never decide; `UNKNOWN` is a success state.

## 9. Direction cue

```json
{"directions": [{"landmark": "water tank", "landmark_type": "water_tank", "distance_m": 120, "bearing_deg": 34,
                 "cue_text": "water tank ~120 m, bearing NE, behind it", "ambiguous": false,
                 "source_ref": "landmark:P-0022", "parsed_relation": "behind"}]}
```
Deterministic; **`null` when nothing resolvable** — never a guessed cue; advisory only (never changes tier, radius or
eligibility); ambiguity is surfaced, not hidden.

## 10. Eligibility decision

```json
{"action": "SERVE | VERIFY_FIRST | REFUSE", "reason": "purpose_work_like | tier_approximate | negatives_accumulated | unplaceable | radius_beyond_band | request_purpose_incompatible", "rule_version": "gate-v2"}
```
Mapping: HOME_LIKE + (CONFIRMED|PROBABLE) → SERVE · HOME_LIKE + weak → VERIFY_FIRST · WORK_LIKE → REFUSE (unless
`borrower_confirmed_residence`) · OTHER/UNKNOWN → VERIFY_FIRST/REFUSE. Every decision is logged with its rule version.

## 11. API (request / response)

```http
POST /resolve        {address_text, town_hint?, as_of?, request_purpose}
POST /evidence       {observation…, idempotency_key}            → 202 + receipt (replay-safe)
GET  /place/{id}     ?as_of=                                    → belief + state + history refs
GET  /tasks/verify-first?town_id=                               → generated tasks
GET  /packs/{town_id}                                           → versioned pack (no polygons)
```

```json
// 200 for /resolve — refusal is a successful decision, not an error
{"candidate": {...§4}, "granularity": "locality", "tier": "PROBABLE",
 "radius_m": 539.9, "radius_basis": "empirical_p80", "nominal": null, "measured_coverage": 0.792, "n_calibration": 24,
 "reasons": ["locality_match", "field_confirmed_x1"],
 "request_purpose": "NOTICE_SERVICE",
 "address_purpose": {"class": "HOME_LIKE", "confidence": "medium", "basis": ["met_x2", "weekday_daytime_visits"]},
 "directions": [{"landmark": "water tank", "distance_m": 120, "bearing_deg": 34, "cue_text": "…", "ambiguous": false}],
 "eligibility": {"action": "VERIFY_FIRST", "reason": "tier_approximate", "rule_version": "gate-v2"},
 "stage": "T1", "arms_available": ["frozen_baseline", "locality_centroid", "field_evidence", "memory"],
 "versions": {"rule_version": "…", "radius_map_version": "…", "evidence_policy_version": "…", "schema_version": "sutra-1.0"}}
```
Errors (§14) never leak partial beliefs; `candidate` is `null` exactly when the system returned no coordinate.

## 12. Versioning

| Object | Version field | Bumped when | Migration |
|---|---|---|---|
| schemas/artefacts | `schema_version` (`sutra-1.0`) | any field added/removed | additive-only; loaders refuse unknown-major rather than guess |
| rules | `rule_version` | cleaning/resolving/candidate/gate rules change | receipts pin the version; re-derivation reproduces old outputs |
| evidence policy | `evidence_policy_version` | weights/thresholds change | beliefs re-derived from the immutable store (never patched) |
| radius map | `radius_map_version` | calibration window or stratum set changes | responses name the map |
| packs | `pack_version` + `valid_until` | rebuild or expiry | staleness widens the radius, visibly |

## 13. Invariants (each has a test in §15)

1. No coordinate without a candidate (point fallback never fabricates) — D35.
2. **One negative observation can never relocate a coordinate by itself. Accumulated independent negative evidence can demote, widen, mark MOVED_SUSPECTED/CONTESTED and trigger re-verification. Only positive evidence or adjudication can establish a new primary coordinate.** — F2.1.
3. Promotion requires the F2.2 independence tuple (≥2 collectors-or-periods + media independence).
4. Every published radius carries `basis`, `n_calibration`; pincode is withheld (parent fallback labelled).
5. Belief = pure function of the store; projections are never feature sources — M3.
6. No T2+ value reaches a T1 output; every read is as-of — T0–T4.
7. Official data only: no dataset outside `official_ps3/cleaned/derived`; no vendor call in benchmark or demo — `[S95]`.
8. Negatives never carry coordinates; `address_not_traceable` is record/agent evidence, never a place label.
9. Every response is attributable to versions (rules, policy, radius map, schema).
10. `request_purpose` is required and logged; `address_purpose` never grants permission by itself.

## 14. Error / failure states

| State | Trigger | Response | Never |
|---|---|---|---|
| `UNPLACEABLE` | no candidate at all | 200, `candidate=null`, area context labelled, action VERIFY_FIRST/REFUSE | a fabricated coordinate |
| `AREA_CONTEXT` | coarse anchor only | 200, tier capped, radius widened, `is_area_context=true` | an address-level tier |
| `CALIBRATION_FALLBACK` | stratum n < 15 | 200, parent stratum named | a nominal claim |
| `PACK_STALE` | pack past `valid_until` | 200, radius widened + reason | silent staleness |
| `CONTESTED` / `MOVED_SUSPECTED` | conflicting independent evidence | 200 with status + VERIFY_FIRST | overwriting either version |
| `DUPLICATE_OBSERVATION` | same `observation_id` replayed | 200 with the original receipt | double-application |
| `HELD_OUT_OF_ORDER` | base version unseen (sync) | 202 held ≤7 days, then CONFLICT queue | silent drop |
| `STORE_UNAVAILABLE` | store down | read last snapshot (labelled old), queue observations | writing through the cache |
| `INVALID_REQUEST` | missing/unknown `request_purpose`, bad input | 400, no partial belief | inference from a missing field |

## 15. Exact acceptance tests (implementation gate)

| # | Test | Pass condition |
|---|---|---|
| T1 | resolve on an address with no candidate | `candidate=null`, no coordinates anywhere in the response, action ∈ {VERIFY_FIRST, REFUSE} |
| T2 | submit 1 negative observation to a CONFIRMED place | coordinate unchanged **bit-for-bit**; radius ≥ previous; status unchanged or downgraded; counter incremented |
| T3 | submit 3 independent negatives (2 collectors, 2 periods) | status `MOVED_SUSPECTED`/`CONTESTED`; VERIFY_FIRST task created; coordinate unchanged |
| T4 | two confirmations from one collector, same day, same photo hash | place stays `WARM` (independence tuple fails) |
| T5 | two confirmations, two collectors, distinct media, 9 days apart, within consistency band | place promotes to `CONFIRMED` |
| T6 | response radius for the pincode stratum | `source_stratum` = parent; `nominal` null; `basis=empirical_p80`; `n_calibration` present |
| T7 | re-derive a belief from the store | byte-identical JSON to the stored version (determinism) |
| T8 | replay the same `observation_id` twice | one stored observation; second returns the original receipt |
| T9 | offline MVP: airplane mode → capture → outbox → reconnect | evidence captured locally; outbox drains on reconnect; belief recomputed server-side; ordering by `local_seq` |
| T10 | `/resolve` at a WORK_LIKE place for `NOTICE_SERVICE` | `eligibility=REFUSE`, reason `purpose_work_like`, decision logged |
| T11 | direction cue with no resolvable landmark | `directions=null` (never a guessed cue) |
| T12 | grep the tree + monkeypatch sockets | no external dataset file; zero outbound calls during benchmark/demo |
| T13 | feature matrix audit | exactly one shared column (`address_text`) is a model feature; no `accounts/agents/splits/lenders` column present |
| T14 | S-Eval firewall | the 145 excluded addresses appear in **no** supervision/feature-fit set; the counter shows the S-Eval query count |
| T15 | split declaration | every metrics report names its `SplitSpec` referencing §2; an undeclared split aborts the run |

---

*Sources: `PS3_SOURCE_REGISTER.md` — `[S55]` visit framework · `[S69]` conformal practice · `[S81][S82]` offline-sync
precedent · `[S90][S94][S96]` official-data measurements · `[S95]` final data policy. Architecture:
`PS3_ARCHITECTURE_LOCK_CANDIDATE_2026-10-07.md`. Data policy: `PS3_FINAL_DATA_AND_ARCHITECTURE_FREEZE.md`.*
