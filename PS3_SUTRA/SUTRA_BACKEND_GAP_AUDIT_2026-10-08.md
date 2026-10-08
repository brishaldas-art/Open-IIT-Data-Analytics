# SUTRA — backend gap audit (2026-10-08)

Phase 0 of the product/UI task: what actually exists in the repository, what is documented but not
built, and exactly what the interface needs. **Nothing here is inferred from an architecture
document**: every "IMPLEMENTED" row was verified by running the module, calling the endpoint or
querying the store on 2026-10-08. Companion: `SUTRA_FRONTEND_BACKEND_CONTRACT_V1_2026-10-08.md`.

Method: repository walk; module reads (`sutra/`); live calls (`resolve`, `place_state`,
`verify_first_tasks`, `build_pack`, `Store` queries) against the real store; comparison against
`PS3_API_AND_COMPONENT_DESIGN.md` §2 and `PS3_IMPLEMENTATION_CONTRACTS_2026-10-07.md` (normative).
Frozen precision untouched `[S95]`.

---

## 1. Item status table

| ITEM | STATUS | FILES | Evidence |
|---|---|---|---|
| Runtime engine (candidates, ranking, belief, evidence, uncertainty, gate, purpose, directions) | **IMPLEMENTED** | `sutra/candidates.py`, `sutra/ranking.py`, `sutra/belief.py`, `sutra/evidence.py`, `sutra/uncertainty.py`, `sutra/eligibility.py`, `sutra/purpose.py`, `sutra/directions.py` | live calls return full decision objects |
| HTTP API surface | **IMPLEMENTED (6 routes)** | `sutra/api.py`, `tools/serve_runtime.py` | stdlib `ThreadingHTTPServer`, `serve("0.0.0.0", 8000)`, routes below |
| Candidate generation + rule ranker | **IMPLEMENTED** | `sutra/candidates.py`, `sutra/ranking.py` | 8 arms defined; `arm_prior` + additive reasons |
| Belief computation (pure function of the store at `as_of`) | **IMPLEMENTED** | `sutra/belief.py` | recomputed at any instant; `computed_from` echoed |
| Evidence scoring (weights, reason codes, independence tuple, negatives) | **IMPLEMENTED** | `sutra/evidence.py` | 5,578 scored observations in store |
| Uncertainty / radius map | **IMPLEMENTED** | `sutra/uncertainty.py`, `sutra/config.py` | `radius-map-v1`: locality 539.9 m p80, n=24, coverage 0.792, publishable; street/pincode/rooftop withheld (n<15) → fallback |
| Eligibility gate | **IMPLEMENTED** | `sutra/eligibility.py` | `SERVE`/`VERIFY_FIRST`/`REFUSE` + 11 reason strings |
| Purpose classifier | **IMPLEMENTED** | `sutra/purpose.py` | `HOME_LIKE`/`WORK_LIKE`/`OTHER`/`UNKNOWN` + basis codes |
| Directions / landmark cues | **IMPLEMENTED** | `sutra/directions.py` | advisory only; `ambiguous` flag present |
| Place memory read model | **IMPLEMENTED** | `sutra/memory.py` | `place_state()` returns projection with `identity_rule`, members, history |
| Verification tasks | **IMPLEMENTED (read-only)** | `sutra/memory.py` | 278 `task_events`; `verify_first_tasks(town, limit)`; causes `MOVED_SUSPECTED`/`CONTESTED` |
| Append-only store | **IMPLEMENTED** | `sutra/store.py` | tables: observations 5,578 · evidence_scores 5,578 · belief_versions 2,757 (7 global recompute versions) · task_events 278 · ingest_log 1 · counter_events 26; **empty**: receipts, held_observations, place_events, place_members |
| Offline device (outbox, pack, replay) | **IMPLEMENTED** | `sutra/offline.py` | `capture`, `outbox`, `download_pack`, `replay`; T9 proves idempotent replay |
| Pack builder | **IMPLEMENTED** | `sutra/packs.py` | `pack-T2-7247f0bd3d96`: 952 addresses w/ cold-lane candidates + radius map, `contains_truth/evidence/polygons false` |
| Replay / as-of capability | **IMPLEMENTED** | `sutra/replay.py`, `sutra/asof.py` | `_manifest`, `_proxy_truth`, `replay`, `candidate_metrics`; strict `observed_at < as_of` |
| Acceptance tests | **IMPLEMENTED (26/26)** | `tests/test_acceptance.py` | T1–T16 + invariants; T2/T3 encode negative-evidence safety |
| Leakage / workspace / link / manifest checks | **IMPLEMENTED** | `tools/check_leakage.py`, `tools/check_workspace.py`, `tools/check_links.py`, `tools/build_manifest.py` | all green at audit time |
| Reproduce chain | **IMPLEMENTED (15 steps)** | `tools/reproduce.sh` | does not yet include the evidence/memory policy tool |
| Demo transcript generator | **IMPLEMENTED** | `tools/demo_walkthrough.py` | scene-based transcript on a fresh demo store; `data/derived/demo_transcript.md` |
| **Frontend application (any)** | **NOT PRESENT** | — | only the inline read-only HTML page in `sutra/api.py` (a form + JSON dump) |
| Documented `/v1/...` API surfaces | **DESIGN ONLY** | `PS3_API_AND_COMPONENT_DESIGN.md` §2 | 10 conceptual endpoints; 4 have partial implementations with different names/shapes |
| `alternatives[]` in a resolve response | **NOT PRESENT** | — | the flat response has no candidate list |
| `coordinate` object with `coordinate_space` | **NOT PRESENT** | — | coordinate is flat `candidate.x/.y`; the design doc's `crs` field is not implemented |
| Decision ticket (single render unit) | **NOT PRESENT** | — | fields exist scattered across the response |
| Task lifecycle states / history / recommended action | **PARTIAL** | `sutra/memory.py` | `state: open` only; transitions exist as `task_events` rows, not as an API surface |
| Idempotency receipts table | **NOT PRESENT (empty)** | `sutra/store.py` | `receipts` 0 rows; idempotent behaviour proven by tests, not persisted as receipts |
| `POST /v1/score_visit` (pre-visit/live advisory) | **DESIGN ONLY** | `PS3_API_AND_COMPONENT_DESIGN.md` §2.2 | no implementation |
| `POST /v1/adjudicate` (human decision) | **NOT PRESENT** | — | no route, no storage path |
| `GET /v1/audit/{belief_id}` | **NOT PRESENT** | — | the three source tables exist; no query surface |
| `POST /v1/batch_resolve` | **NOT PRESENT** | — | — |
| Overview / operations metrics endpoint | **NOT PRESENT** | — | counts computable from the store |
| Plane/map geometry endpoint | **NOT PRESENT** | — | pack ships coordinates; no address-scoped geometry read |
| Lat/lon, WGS84, Mercator, EPSG anywhere in runtime | **NOT PRESENT (correct)** | — | audit §3 below |
| Model artefacts on disk | **NONE (by policy)** | — | `check_leakage.py` enforces |
| Design system / component library | **NOT PRESENT (deliberate)** | — | out of scope for this phase |

---

## 2. Endpoint audit (documented vs implemented)

| Endpoint (documented) | Documented? | Implemented? | Actual request | Actual response | Missing for the UI | Priority |
|---|---|---|---|---|---|---|
| `POST /v1/resolve` | §2.1 | **yes, as `POST /resolve`** | `{address_text, town_hint?, as_of?, request_purpose?}` | flat decision object (30 fields; §16A of the contract for a real body) | `coordinate{}`, `uncertainty{}`, `alternatives[]`, `decision_ticket{}`, `as_of` echo, `task` link | **P0** |
| `POST /v1/score_visit` | §2.2 | no | — | — | everything (advisory only; must not write) | P1 |
| `POST /v1/ingest_evidence` | §2.3 | **yes, as `POST /evidence`** | `{observation{…}, idempotency_key}` | 202 + receipt | `belief_before/after` summary, task delta, validation echo | **P0** |
| `POST /v1/adjudicate` | §2.4 | no | — | — | the whole write path (observation of kind `adjudication`) | P1 |
| `GET /v1/belief/{address_id}` | §2.5 | **partial** (belief embedded in resolve) | — | — | standalone read with `as_of` and version list | **P0** |
| `GET /v1/place/{place_key}/history` | §2.5 | **partial** (`GET /place/{id}`) | `?as_of=` | `place_state` (members, history pairs, projection) | version list, contradictions, pagination | **P0** |
| `GET /v1/tasks` | §2.5 | **partial** (`GET /tasks/verify-first`) | `?town_id=&limit=` | `{town_id, tasks[]}` | `cause`/`state`/`as_of` filters, cursor, facets, `recommended_action`, `clears_when` | **P0** |
| `POST /v1/batch_resolve` | §2.6 | no | — | — | the whole path (≤5,000; per-row tickets + aggregate; never bulk accuracy) | P2 |
| `GET /v1/health` | §2.6 | **partial** (`GET /health`) | — | `{ok, versions, store.meta()}` | pack versions/age, gauges, index digests, S-Eval firewall counters | **P0** |
| `GET /v1/audit/{belief_id}` | §2.6 | no | — | — | the whole chain read (data exists in 3 tables) | P1 |
| `POST /evidence` (actual) | — | **yes** | as above | 202 + receipt | see above | **P0** |
| `POST /explain` (actual) | — | **yes** | `{address_text, town_hint?, request_purpose?}` | `{explain: "…", response: {…}}` | keep as a convenience; the `explain` string is already UI-grade copy | P2 |
| `GET /packs/{town_id}` (actual) | — | **yes** | — | pack metadata | device-side age echo | P2 |
| `GET /` (actual) | — | **yes** | — | inline read-only page | replaced by the real frontend | P2 |

**Naming trap, recorded so nobody repeats it:** in a resolve response `stage: "T1"` means **visit
stage 1 = pre-visit**, while `T1`/`T2`/`T3` as town ids are three different towns (942 / 952 / 986
addresses). The two namespaces must not be conflated in the interface.

**`arms_considered` already exists** in the live response: an ordered list of `{arm, candidate_id,
score, primary_eligible, reasons[]}` for every arm that produced a candidate. It is not yet a
candidate list (no coordinate, granularity, provenance or "why it lost" vocabulary), but it is real
material — `alternatives[]` (P0-2) is a projection of it, not a new ranking path.

**Semantics verified against the brief's checklist.** `as_of`: supported on resolve/place, *not* on
tasks or health (P0 gap). Stage separation: `stage` is present and hard-coded to the
pre-visit stage; the post-visit write paths exist only as ingest (P1 for `score_visit`). Uncertainty:
complete and always accompanied by basis/n/coverage. Provenance: present on candidates and beliefs.
Alternatives: **missing** (the biggest single contract gap). Refusal: correct and coordinate-free.
Evidence provenance: complete per observation. Contradiction: derivable (`status`, `support`,
`radius.widen_reason`) but not exposed as an object. Memory history: pairs `{at, observation_id}`
only. Verification tasks: implemented read-only. Audit trail: absent as a surface. Idempotency:
enforced, not persisted. Deterministic responses: yes for decision fields (`computed_at` excluded).

---

## 3. Coordinate representation audit (every place a coordinate exists)

| Where | Representation | Space | Units | Notes |
|---|---|---|---|---|
| `observations.x/y` (store) | integer pair | local metric plane | metres | stored exactly as received on ingest; verified integer-valued across a 4,000-row sample (no coordinate transform exists anywhere in the ingest path) |
| `candidate.x/y` (`sutra/candidates.py`) | number pair | same | metres | rounded to 3 dp |
| resolve response `candidate`, `area_context` | flat numbers | same | metres | `area_context` carries locality context, never an address coordinate |
| `belief.candidate` | same record | same | metres | — |
| `place_state.coordinate` | `{x, y, radius_m, basis, n_calibration}` | same | metres | projection |
| `verify_first_tasks[].radius_m` | number | — | metres | — |
| `directions[]` | `{distance_m, bearing_deg}` | relative cue | metres/degrees | bearing is computed in-plane; **not** a bearing to geographic north — the UI must not draw a compass `[U21]` |
| pack `addresses[].candidates[]` | candidate records | same | metres | pack also ships `radius_map` → the device can render uncertainty offline |
| `config.RADIUS_TABLE`, `sutra/uncertainty.py` | radii | — | metres | published p80 values |
| EDA / derived CSVs | coordinates | same | metres | analysis artefacts, not runtime |

**Latitude/longitude audit.** No runtime module, no API response and no store column contains
lat/lon, a projection identifier such as WGS84/Mercator/EPSG, or a tile reference. Three documents
mention lat/lon, and **none of them is a UI or API contract**:

- `PS3_CANONICAL_SCHEMA.md` §171–175 — an explicit *forward note*: a real deployment would carry
  `lat`/`lon` plus a `crs` field; the package has no projection and no road graph.
- `PS3_DATA_AUDIT.md` §296 — an open question to the data owner ("is there a CRS…?"), unresolved.
- `PS3_ASSUMPTIONS.md` — the original problem statement's wording, not a design decision.

**Action:** flagged as *deployment-forward notes, not UI contracts*. The interface contract uses
`coordinate_space: "sutra_local_metric_plane:<town>"` and the design doc's `"crs":
"local_metric_plane:T2"` is superseded by that field name. **No UI/API example anywhere contains a
fabricated lat/lon value**, so nothing requires correction beyond this note.

---

## 4. What the frontend needs that the backend must provide (P0/P1/P2)

Every task lists the exact module, interface, dependency, complexity, tests, and its effect on the
frozen precision layer. **Rule: no task may reopen frozen precision; none does.** Complexity is
S (≤1 h), M (half day), L (a day+).

### P0 — required for the frontend to function at all

| # | Task | Module / file | Interface | Depends on | Cx | Tests | Precision impact | S-Eval read |
|---|---|---|---|---|---|---|---|---|
| P0-1 | Additive resolve blocks | `sutra/resolve.py` | `_resolve_response()` gains `coordinate`, `uncertainty`, `alternatives[]`, `decision_ticket`, `evidence_summary`, `task`, `as_of`, `computed_at`; all flat fields retained | — | M | extend `tests/test_acceptance.py` (new `test_T17_resolve_contract_blocks`), full suite green | **none** — presentation of existing values | none |
| P0-2 | Alternatives + `lost_reason` | `sutra/ranking.py`, `sutra/resolve.py` | `rank(..., explain=True)`-style helper returning per-candidate reason deltas; deterministic ordering (score desc, `candidate_id` asc) | P0-1 | M | a new test module (tests/test_contract_alternatives.py, to be created); `test_T16` unaffected | none | none |
| P0-3 | Belief read endpoint | `sutra/api.py` | `GET /v1/belief/<address_id>?as_of=` → §6 belief object | — | S | API-level test | none | none |
| P0-4 | Observations read endpoint | `sutra/api.py`, `sutra/store.py` | `GET /v1/address/<id>/observations?as_of=` → §5 rows | — | S | test incl. a negative observation (no coordinate claim) | none | none |
| P0-5 | Place history completion | `sutra/memory.py` | `place_state` gains `versions[]` (from `belief_versions`) and `contradictions[]` (composed from support + radius widen reason) | — | M | a new test module (tests/test_contract_place.py, to be created) | none | none |
| P0-6 | Task list filters + facets | `sutra/memory.py`, `sutra/api.py` | `GET /v1/tasks?town_id=&cause=&state=&as_of=&limit=&cursor=` returning `{items[], facets{}}`; rows gain `recommended_action`, `clears_when`, `evidence_refs[]` | — | M | test: queue counts match `verify_first_tasks` today | none | none |
| P0-7 | Health extension | `sutra/api.py` | §13 shape: packs, gauges, index digests; `s_eval_firewall.reads_by_tools_total` read from the receipt counter source | store counters | S | test: refuses to invent a gauge it cannot compute | none | **none** (read the counter, never the truth) |
| P0-8 | Ingest receipt enrichment | `sutra/store.py`, `sutra/api.py` | `/evidence` returns `belief_before`/`belief_after` (tier/status/radius/candidate), `changed`, `task_delta` | — | S | extend T8/T9 | none | none |
| P0-9 | Plane geometry endpoint | `sutra/api.py` (new read-only view; may live in a new module, sutra/views.py, to be created) | §10 contract | — | M | test: extent contains all returned points; no coordinate invented | none | none |
| P0-10 | Contract test suite | a new test module (tests/test_contract_v1.py, to be created) | schema-level assertions for all 15 models + refusal + determinism (two identical calls) | P0-1…P0-9 | M | itself | none | none |
| P0-11 | Typed `ReasonCode[]` expansion | `sutra/resolve.py` (compose from the four string sources) | contract §17: `{code, kind, subject, effect, direction, label}`; the strings stay verbatim in `score_reasons[]`/`reasons[]` | P0-1 | S | contract test asserts Σ`effect` over `score_term` codes reproduces `score` exactly | **none** — presentation of existing arithmetic | none |

### P1 — supports the UX, not blocking

| # | Task | Module | Interface | Cx | Notes | S-Eval read |
|---|---|---|---|---|---|---|
| P1-1 | `POST /v1/score_visit` | `sutra/api.py` (+ small pure helper) | agreement of a check-in with the current belief: `distance_to_candidate_m`, `within_radius`, hint copy, reason codes; **writes nothing** | M | the T2 in-visit answer; blocked on a product decision about which device sends it | none |
| P1-2 | `POST /v1/adjudicate` | `sutra/store.py`, `sutra/api.py` | `{address_id, decision: confirmed|not_true|inconclusive, actor, note, idempotency_key}` → observation of kind `adjudication` + belief delta + task transition | M | the only human ground-truth write; must not enter S-Eval | none |
| P1-3 | Task transitions + history | `sutra/memory.py`, `sutra/store.py` | `PATCH /v1/tasks/{id}` → append `task_events` row (state, actor, note); `task.history[]` served from those rows | M | no deletes | none |
| P1-4 | Audit chain endpoint | `sutra/api.py` (+ view helper) | §14 | M | pure read over 3 tables | none |
| P1-5 | Overview endpoint | `sutra/api.py` | town counts, cold/warm, tier mix, queue depth, pack age at `as_of` | S | counts only | none |

*Why Overview is P1 and not P0:* the judge flow opens in the workbench and never depends on
town-level counts; the operations landing must exist for a credible product, but no demo beat breaks
without it.
| P1-6 | Pack age on the wire | `sutra/packs.py`, `sutra/offline.py` | device reports `pack_version`; `GET /health` and the sync response report `stale` | S | offline UX depends on it | none |
| P1-7 | `MethodTrust` assembly | static appendix + `GET /health` | contract §19: versions, gate table, radius map, invariants, two loops with honest status labels, `claimed_numbers[]` (exactly three, each with population/n/caption) | S | static content; the only live dependency is `/health` | none |

### P2 — polish / optional

| # | Task | Module | Notes |
|---|---|---|---|
| P2-1 | `POST /v1/batch_resolve` | `sutra/api.py` | ≤5,000 rows; per-row ticket summary + aggregate (refusal rate, tier mix, radius histogram). Never a bulk-accuracy claim |
| P2-2 | Export endpoints | `sutra/viewsexport` helper | CSV/JSON of a queue or an audit chain, with versions stamped |
| P2-3 | `explain` string as a first-class field | `sutra/resolve.py` | already exists; expose in the ticket |
| P2-4 | Receipt persistence for idempotency | `sutra/store.py` | currently proven but not stored |
| P2-5 | Command-palette deep links | frontend | client-only |

**Not tasks (rejected).** Any change to ranking weights, candidate generation, the memory emit rule,
the radius map, the gate, the store schema's semantics, or the S-Eval discipline. The interface is a
*reader* of the frozen system plus two append-only writers that already exist
(`/evidence`, and adjudication when added) `[S95]`.

---

## 5. Blocked demo steps (honest list)

| Demo step | Status | Unblocked by |
|---|---|---|
| Candidate list with losing reasons | **BLOCKED** | P0-2 |
| Radius ring on a plane | **BLOCKED** | P0-9 (or a client-side transform of `candidate.x/y` — possible today with no backend work, using the pack's `radius_map`) |
| Evidence timeline per visit | **BLOCKED** | P0-4 |
| Belief-version stepping (`[`/`]`) | **BLOCKED** (standalone) | P0-3; **partially available today** by calling resolve with different `as_of` values — the demo flow uses that |
| Verification queue with causes/filters | **PARTIAL** | `GET /tasks/verify-first` works today (town + limit); filters/cursor are P0-6 |
| Adjudicate button | **BLOCKED** | P1-2 |
| Audit chain view | **BLOCKED** | P1-4 |
| Offline capture with pending count | **PARTIAL** | `sutra/offline.py` works; UI chip needs P0-7 |

---

## 6. Verification performed at audit time (non-destructive)

- live `resolve()` on a warm, a demoted-negative, a cold and an unmatched address; all bodies
  reproduced in §16 of the contract;
- `place_state`, `verify_first_tasks` (T1 96 tasks, all `MOVED_SUSPECTED` / T2 84 tasks, all
  `MOVED_SUSPECTED` / T3 98 tasks: 93 `MOVED_SUSPECTED` + 5 `CONTESTED`), `build_pack("T2")`;
- store census (5,578 / 5,578 / 2,757 / 278 / 1) and empty-table list, measured 2026-10-08;
- visit coverage: 3,788 observations precede the frozen cut (2026-06-01) across 1,280 addresses;
  5,578 observations in total across 1,477 addresses, spanning 2026-04-01 → 2026-06-29 — the
  post-cut visits are the T2/T3 material and are never in the frozen evaluation;
- town coverage at the frozen cut (towns `T1`/`T2`/`T3` — not the resolve `stage` field): T1 942
  addresses (456 warm / 486 cold), T2 952 (392 / 560), T3 986 (432 / 554) of the 3,117 indexed
  addresses;
- latest stored belief per address over the 1,477 belief-bearing addresses:
  `APPROXIMATE/STABLE` 623 · `PROBABLE/STABLE` 305 · `APPROXIMATE/MOVED_SUSPECTED` 273 ·
  `CONFIRMED/STABLE` 271 · `APPROXIMATE/CONTESTED` 5;
- belief progressions at real visit instants for `AD003067` and `AD002936`;
- coordinate audit: every sampled observation coordinate is an integer pair in the local metric
  plane; every store column name was scanned for `lat`/`lon`/`crs`/`epsg`/`proj` → none, and a
  text scan of `sutra/`, `tools/serve_runtime.py` and `tests/` for latitude/longitude/projection
  vocabulary returns only `sutra/geo.py`'s own statement that the plane is local ("no
  reprojection, no CRS juggling") plus compass words inside address text;
- 26/26 acceptance tests, leakage/workspace/links green, frozen precision hash unchanged.

---

## 7. State discipline — what this audit touched, disclosed in full

| Artefact | Before | After | Verdict |
|---|---|---|---|
| `observations` / `evidence_scores` | 5,578 / 5,578 | 5,578 / 5,578 | unchanged |
| `belief_versions` / `task_events` | 2,757 / 278 | 2,757 / 278 | unchanged |
| `place_events` / `place_members` / `held_observations` / `receipts` | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 | unchanged |
| `counter_events` | 26 | 80 | **appended by the runtime itself** when answering read-only `resolve` calls (`gate_decisions` 58; `evidence_memory_policy_runs` 12; `s_eval_looks` **10 → 10**, unchanged) |
| `s_eval_looks` (the locked-read ledger) | 10 | **10** | **no new S-Eval read was spent in this task** |
| `data/official_ps3/*` | — | mtimes 2026-10-07 21:25, `check_leakage` hash match | unmodified |
| the T2 offline pack | existed | re-written with **identical content** (same content-derived `pack_version`, `verify_pack` → `ok: true`, sha `7247f0bd3d96…`, not stale at the canonical instant) | no functional change |
| Frozen precision | `ac61cf2e71f77454…` | same | untouched |
| Frozen evidence/memory policy | `a110f08962993e3c…`, `s_eval_used_for_selection: false`, runtime knobs `MEMORY_EMIT: evidence_derived_only` + `MEMORY_ON_DEMAND_BELIEF: true` (the document's own `knobs` map is its *revert* set — see §11) | same | untouched |

No coordinate, no candidate, no score, no threshold, no policy knob and no model behaviour was
changed by this audit. The only writes are the runtime's own append-only counters.

---

## 8. P0 — CLOSED (2026-10-08)

Every P0 row below is implemented, tested and reproducible. All of them are **readers or
projections** of the frozen runtime: no ranking weight, candidate arm, radius rule, evidence policy,
gate rule, coordinate or policy knob was touched, and no S-Eval read was spent (`s_eval_looks`
10 → 10).

| # | Task | State | Where it landed | Proof |
|---|---|---|---|---|
| P0-1 | Additive resolve blocks | **DONE** | `sutra/views.py::resolve_blocks` + `sutra/resolve.py::_v1_blocks` (served **and** refusal paths) | contract tests: warm/cold/verify-first/refusal; flat legacy fields asserted intact |
| P0-2 | `alternatives[]` + `lost_reason` | **DONE** (projection of `arms_considered`; no new ranking) | `sutra/views.py::alternatives_block`, `_lost_reasons` | vocabulary check + determinism + margin arithmetic; runner-up on `AD003067` is the memory arm losing on `lower_arm_prior` |
| P0-3 | Belief read `GET /v1/belief/{id}` | **DONE** | `sutra/views.py::belief_payload` (verbatim `compute_belief`) | test asserts `payload["belief"] == compute_belief(...)` |
| P0-4 | Observations read | **DONE** | `sutra/views.py::observations_payload` | order, `visit_id`, negative non-claim, captured position, as-of exclusion |
| P0-5 | Place history `versions[]`, `contradictions[]` | **DONE** | `sutra/views.py::place_history_v1` | stored belief rows only; legacy keys proven unchanged; `unplaced` flag |
| P0-6 | `GET /v1/tasks` filters + facets + cursor | **DONE** | `sutra/views.py::tasks_list` | 278 rows, `{MOVED_SUSPECTED: 273, CONTESTED: 5}`; parity with the legacy reader; cursor paging without gaps |
| P0-7 | Health / runtime status | **DONE** | `sutra/views.py::health_payload` | packs, gauges, index digests, counters, firewall; no accuracy claim anywhere |
| P0-8 | Evidence receipt enrichment | **DONE** (semantics and idempotency unchanged) | `sutra/store.py::submit_observation` + `_belief_summary`/`_changed` | before/after/changed/task-delta; replay still `DUPLICATE_OBSERVATION` |
| P0-9 | Local metric plane geometry | **DONE** | `sutra/views.py::geometry_payload` | `sutra_local_metric_plane:<town>`, metres, SVG hint; refusals publish nothing |
| P0-10 | Contract test suite | **DONE** | `tests/test_contract_v1.py` (39 tests) + `tools/reproduce.sh` step 10b | 39 passed, 0 writes to the shipped store |
| P0-11 | Typed `ReasonCode[]` | **DONE** | `sutra/views.py::reason_codes` | typed terms are the emitted score terms, verbatim and complete |

**Backward compatibility, verified:** `POST /resolve`, `POST /evidence`, `POST /explain`,
`GET /health`, `GET /place/{id}`, `GET /tasks/verify-first`, `GET /packs/{town_id}` all still answer
with their previous keys; the 26 acceptance tests are untouched and green; `/v1/tasks` and
`/tasks/verify-first` return the same task ids in the same order.

### 8.1 P0 residue (honest, not hidden)

| Residue | Why it is still open | Tracked as |
|---|---|---|
| `memory_not_evidence_derived` is never emitted | the provenance key it needs is not on the wire (`arms_considered` carries no provenance) | P1 provenance passthrough |
| Task `state` is always `open` | transitions are P1 by the brief | P1-3 |
| `computed_at` is the one non-deterministic field | it is the computation clock, excluded by contract §20 | by design |
| `gate_decisions` counter grows on every read of `/resolve` | the runtime's own append-only telemetry, by design | by design |

### 8.2 What this changed in the shipped store (measured, disclosed)

| Artefact | Delta over the P0 run |
|---|---|
| observations · evidence_scores · belief_versions · task_events · place_events · place_members · held_observations · receipts · ingest_log | **0 rows** |
| `counter_events` | **+11** `gate_decisions` rows, all appended by the runtime itself while the new endpoints were exercised over HTTP (`/resolve` ×2, `/explain` ×1, and the P0 verification pass) |
| `s_eval_looks` | **10 → 10 — no new locked read** |
| `tests/` runs (65 tests) | **0 delta** on every table and counter (the contract suite works on a sqlite backup copy) |
| the T2 offline pack | rewritten **content-identical** (`verify_pack` ok, same content-derived version) by the `/packs/T2` call |
| frozen precision `ac61cf2e71f77454…`, policy `a110f08962993e3c…` | unchanged |
| official dataset | **11/11 recorded tables byte-identical** to their pre-existing Drive record (the audit folder's drive-verification record), verified independently of the manifest this repo regenerates |

### 8.3 P1/P2 remain exactly as scoped

P1: `score_visit` (advisory, writes nothing) · `adjudicate` (append-only human truth) · task
transitions + history · audit chain · Overview · pack age on the wire · MethodTrust assembly ·
provenance passthrough for `alternatives[]`.
P2: batch resolve · exports · `explain` as a ticket field · receipt persistence · palette deep links.
**None of them was started in this run.**

### 8.4 Independent immutability check (not circular)

`check_leakage.py` compares the official tables against `tools/section_manifest.csv`, which this repo
regenerates — so on its own it could not prove immutability. The P0 run therefore also verified the 11
official/shared tables against the **pre-existing hash record captured from the Drive listing**
(`/home/user/PROJECT_DATA_AUDIT/data/drive_verification.csv`): **11 match, 0 changed**. The file mtimes
of every pre-existing file are one bulk timestamp (06:29:52, the workspace materialisation), and only
the files this task authored carry later times — no official, cleaned or derived input was rewritten.

---

---

## 9. Privacy / retention / purpose control — as-built audit (documentation only)

Every row was verified in code on 2026-10-08. **No code changed for this section and no policy claim is
made that the runtime does not already implement.** No legal claim is made anywhere.

| Concern | What the runtime actually does | Where it is enforced | Label |
|---|---|---|---|
| Purpose control | `request_purpose` is **required** and validated against the frozen vocabulary (`NOTICE_SERVICE · VISIT_PLANNING · FIELD_NAVIGATION · PORTFOLIO_REVIEW · AUDIT · DEMO`); `NOTICE_SERVICE`/`VISIT_PLANNING` refuse a `WORK_LIKE` place; every decision records `eligibility {action, reason, rule_version, request_purpose}` and appends a `gate_decisions` counter row with the rule version | `sutra/purpose.py::validate_request_purpose`, `sutra/eligibility.py`, `sutra/resolve.py` | **[VERIFIED]** |
| Raw GPS retention | the raw check-in (`x`, `y`, `gps_accuracy_m`) is retained on the observation row **and** in the immutable `payload_json` (with `coord_method`, `coord_fixes`, `checkin_sample`); the published coordinate is the derived trace-tail estimate. Raw is never overwritten or discarded | `sutra/store.py::append_observation`, `sutra/evidence.py` | **[VERIFIED]** |
| Negative evidence | the captured position is preserved for provenance but is **not a coordinate claim**: ingest raises on a negative that claims one, the API returns `x`/`y` as `null` with the captured position under `captured{}`, and the plane payload publishes no point for it | `sutra/evidence.py` (invariant 8), `sutra/views.py::observations_payload` | **[VERIFIED]** |
| Media handling | only `{sha256, kind}` metadata is stored (`media_json`); **no image bytes exist anywhere in the runtime**; duplicate hashes feed duplicate-claim and independence accounting, never a per-agent identity feature | `sutra/store.py`, `sutra/evidence.py` | **[VERIFIED]** |
| Auditability | all tables are append-only; belief rows carry `payload_sha256`; task events and counters are appended with timestamps and rule versions; ingest is idempotent via receipts | `sutra/store.py`, `tools/check_leakage.py` (no UPDATE/DELETE) | **[VERIFIED]** |
| Retention **policy** (deletion window, encryption at rest, PII scrubbing, consent registry, regulator export) | **not implemented and not claimed.** The store is append-only by design; the workspace holds no deletion path. A retention regime is a future decision, not a capability of this build | — | **[OPEN] — labelled, not pretended** |

**Not changed by this audit:** no retention rule, no scrubbing, no field removed, no schema edit.

---

## 10. `place_neighbour` — consistency audit (no drift found)

| Source | Statement | Consistent? |
|---|---|---|
| `sutra/config.py` | `ENABLE_PLACE_NEIGHBOUR = False` | ✔ |
| `data/derived/final_precision_config.json` → `frozen_configuration.place_neighbour` | `{"c2_gate": "locked", "enabled": false}` | ✔ |
| `sutra/candidates.py::place_neighbour_candidates` | returns `[]` when disabled; **raises** if enabled without an admitted index artefact | ✔ |
| `PS3_ARCHITECTURE_LOCK_CANDIDATE_2026-10-07.md` | "C2 place-neighbour index — SHADOW, admitted only by experiment"; decision-table row "YELLOW · C2-gated" | ✔ |
| `PS3_IMPLEMENTATION_CONTRACTS_2026-10-07.md` §4 | "`place_neighbour` appears **only** if experiment C2 admitted the index" | ✔ |
| `data/derived/candidates_v2.csv` | arm absent (asserted by the acceptance suite) | ✔ |
| `SUTRA_FRONTEND_BACKEND_CONTRACT_V1_2026-10-08.md` §3 | lists `place_neighbour` in the **arm vocabulary** — correct, and now annotated as vocabulary-only | ✔ (clarified) |

**Verdict: consistent; zero drift; zero behaviour change.** The arm exists in the frozen *vocabulary* and
never in production output; that distinction was clarified in the contract document (documentation only)
and is now pinned by `test_contract_place_neighbour_stays_disabled` (frozen config block, config flag,
15 real addresses emitting no such candidate, and the guard that enabling it without an admitted index
raises).

---

## 11. Memory policy — the one wording defect (found, fixed, now guarded)

**What the runtime does** (config + behaviour, verified): `MEMORY_EMIT = "evidence_derived_only"`,
`MEMORY_REQUIRES_EVIDENCE_DERIVED = True`, `MEMORY_ON_DEMAND_BELIEF = True`. A prior that merely
re-wraps a static arm (pin / locality / town / landmark / address-book) is **not emitted** as memory.

**What the frozen document declares** (`final_evidence_memory_policy.json`, sha
`a110f08962993e3c…`): `memory.emit_rule` = "evidence-derived priors only (`MEMORY_EMIT=evidence_derived_only`)",
`memory.evidence_derived_definition` = "a prior that merely re-wraps a static arm … is NOT memory and is
not emitted", `memory.prior_source` = the on-demand recomputation. Report §Verdict/§Revert says the same.

**The defect.** The same document carries a `knobs` map reading `EMIT=always`, `ON_DEMAND=false`,
`REQUIRES=false` — which is the **revert set**, exactly as the document's own `revert` section and
`research/precision/policies.py::P0_PATCH` define it. The previous handoff quoted that map as the shipped value —
`MEMORY_EMIT: always` — which was **wrong**; the review caught it and it is corrected here. The sentence was corrected in
`SUTRA_BACKEND_GAP_AUDIT_2026-10-08.md` §7, the hazard is now written down where a reader will meet it,
and a guard fails the suite if any productisation document repeats the mistake.

**One genuine divergence, inert, now pinned.** The frozen arm tuple has
`MEMORY_REQUIRES_EVIDENCE_DERIVED = false` (it is carried over from `P0_PATCH`), while the runtime ships
`true`. Under the adopt emit gate a candidate can only reach the eligibility check if it already *is*
evidence-derived, so the flag cannot change any decision — the frozen evaluation numbers describe this
build. Flipping it would be a config edit with zero behavioural effect, so it was **not touched**.

**Regression assertions added** (the "cannot silently diverge again" requirement):

| Test | What it pins |
|---|---|
| `test_contract_memory_policy_runtime_matches_frozen_document` | the document's sha256, `s_eval_used_for_selection: false`, the declared emit rule, the runtime knobs, **and the behaviour in both directions** — a static-pin prior yields `memory_candidates(...) == []`, an evidence-derived prior yields exactly one row with `memory_evidence_derived: True` — plus the inert third knob, recorded rather than changed |
| `test_contract_memory_policy_wording_cannot_drift_in_our_docs` | no `SUTRA_*.md` may present the revert set as the shipped configuration (the guard that caught the stale sentence above) |

**No S-Eval read; frozen hashes unchanged; memory implementation untouched.**

---

## 12. Review-feedback items folded in (A, B) — no new metrics, no new capability claims

**A · Evaluation honesty (preserved, not merged).** The three populations stay separated exactly as
frozen: cold independent **71 % < 500 m, n = 100, median 375.8 m**; independent warm subset
**96.77 %, n = 31 answered, median 12.4 m**; product lane **76 % < 500 m, median 202.2 m** — documented
in the UX spec §14 with mandatory captions and in the contract §19 as `claimed_numbers[]`, and
`/health.capabilities.metrics_api = "not_implemented"` records that the API serves **none** of them
(they are static Method & Trust content). No metric was created, recomputed or merged.

**B · Implementation labels.** `GET /health` now carries `capabilities` — a closed status vocabulary
(`implemented · designed · not_implemented · evaluated_not_adopted · research_only`) over 20
capabilities, plus `capabilities_note`. The frontend can therefore distinguish what is running from
what is designed: `resolve`, `belief_read`, `observations_read`, `place_read`,
`verification_queue_read`, `plane_geometry`, `alternatives_explanation`, `typed_reason_codes`,
`evidence_ingest`, `offline_pack_capture_replay` = `implemented`; `task_state_transitions`,
`adjudication_write`, `audit_chain_read`, `batch_resolve`, `overview`, `metrics_api`,
`model_training`, `place_neighbour_arm` = `not_implemented`; `learned_ranker` =
`evaluated_not_adopted`; `calibration_learning` = `research_only`. A test asserts the block contains no
digits, so a status can never smuggle a number past the honesty guard.

**Also delivered from the P0 review deltas:** `alternatives[].rank` (+`granularity`) and the town plane
endpoint `GET /v1/plane/{town_id}` (plus the `/v1/plane/address/{address_id}` alias) — both pure
projections of existing runtime/official data, both pinned by tests.

---

---

## 13. Validation ledger — second pass (2026-10-08, review deltas)

| Check | Result |
|---|---|
| Existing acceptance suite | **26 / 26 passed**, 0 failed, 0 skipped |
| P0 contract suite | **51 / 51 passed** (12 added in this pass) |
| Whole test directory | **77 / 77 passed** |
| Deterministic repeated API calls | **8 endpoints byte-identical** on repeat (resolve, belief, observations, tasks, geometry, plane, plane/address, health). `/health` is deterministic because pack age is computed at the frozen cut, not the wall clock |
| Acceptance receipt (`tools/run_acceptance_tests.py`) | regenerated: 26 passed · latency over 400 real resolutions **p50 20.3 ms · p95 37.4 ms · p99 44.1 ms** (target p95 < 250 ms → MET), measured on a **copy** of the store in `/tmp` |
| Index digests | `verify()` → `ok: true`, no mismatched file, 3,117 addresses |
| Leakage · workspace · links · manifest | ALL PASSED · ALL CHECKS PASSED · ALL RESOLVE (1,089 refs) · 244 files / 78.38 MB |
| Model artefacts / outbound calls / external data | none · none · none |
| Official data (independent Drive record) | **12 / 12 tables byte-identical**, 0 changed |
| `FINAL_PRECISION_CONFIG` | `ac61cf2e71f77454d91c854c0738b81f…` unchanged (file sha `f7bb53813ecf57f7…`) |
| `FINAL_EVIDENCE_MEMORY_POLICY` (emp-v1) | `a110f08962993e3ca6b7151edbc01002…` unchanged, 3,754 bytes, `s_eval_used_for_selection: false` |
| S-Eval locked reads | **10 → 10 — no new read in either P0 pass** |
| Store rows | observations · evidence_scores · belief_versions · task_events · receipts · held_observations · place_events · place_members — **0 delta** |
| Store counters | `counter_events` +8 during the HTTP verification pass (all `gate_decisions`, appended by the runtime itself; `s_eval_looks` and `evidence_memory_policy_runs` untouched) |

**The full 15-step `tools/reproduce.sh` chain was deliberately NOT run, and this is a considered
decision, not an omission.** Step 6 rebuilds the store and step 15 is the precision tool: running them
under the freeze would either reset the append-only counter ledger the freeze is meant to preserve, or
require a fresh locked read. A validation that can only be performed by breaking the rules it is
validating is not a validation. The chain's *acceptance* layer was run instead (the tool above), which
re-derives the receipt, the latency distribution and the index digests from the current runtime without
touching frozen state.

*Sources: `[U1]`–`[U24]` per `SUTRA_UIUX_RESEARCH_SOURCES_2026-10-08.md`; `[S69]` `[S73]` `[S81]`
`[S82]` `[S95]` per `PS3_SOURCE_REGISTER.md`. Normative runtime contracts remain
`PS3_IMPLEMENTATION_CONTRACTS_2026-10-07.md`.*
