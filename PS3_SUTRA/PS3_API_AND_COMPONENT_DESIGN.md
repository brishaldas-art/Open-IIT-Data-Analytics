# SUTRA — API AND COMPONENT DESIGN

The interface is where SUTRA's honesty is enforced: if the response cannot express doubt, memory, provenance and refusal,
then none of the architecture documents matter. This document specifies the endpoints, the payloads, the error vocabulary,
the latency budgets, and the components behind them.

---

## 1. Design rules for the API

1. **Every response names its stage** (`T1` pre-visit, `T2` in-visit). A consumer cannot accidentally use a post-visit
   answer as a pre-visit one.
2. **Every response carries uncertainty**: `tier`, `radius_m`, `nominal`, `measured_coverage`, `reason_codes[]`.
3. **Every response carries provenance**: `arms_available[]`, `belief_version`, `pack_age_days` (when offline), `purpose`.
4. **No endpoint returns a coordinate without a granularity.** A bare point is not a valid payload.
5. **Refusal is a first-class 200-level answer** (`UNPLACEABLE` with reasons), not a 4xx/5xx error. Errors are for
   *malfunction*, not for *the world being hard*.
6. **Idempotency** by `visit_id` / `record_id` on all write paths.
7. **Backwards-compatible evolution only**: additive fields; a breaking change is a new `/v2` and a documented migration.

---

## 2. Endpoints

### 2.1 `POST /v1/resolve` — the pre-visit answer (T1)
```json
{ "address_text": "6th Cross, 5th Main, Church hattira, Kuvempu Layt, Kaveripura - 960102",
  "town_id": "T2", "account_id": "A-00231", "purpose": "visit_allocation", "as_of": "2026-05-04T09:00:00Z" }
```
```json
{ "stage": "T1",
  "coordinate": { "x": 1543.2, "y": -820.6, "coordinate_space": "sutra_local_metric_plane:T2" },
  "granularity": "street", "tier": "PROBABLE",
  "radius_m": 210.0, "nominal": 0.90, "measured_coverage": 0.93, "n_calibration": 16,
  "reason_codes": ["field_confirmed_x1", "locality_match", "vendor_stratum=locality"],
  "belief_version": 7, "belief_as_of": "2026-05-03T17:12:00Z",
  "arms_available": ["frozen_baseline", "locality_centroid", "town_centroid", "official_landmark", "memory"],
  "alternatives": [ { "x": 1498.0, "y": -788.3, "granularity": "locality", "score": 0.41, "reason_codes": ["vendor_only"] } ],
  "eligibility": { "actionable_for_visit": true, "notice_gate": "pass" },
  "cost": { "vendor_calls": 0, "cache_hit": true } }
```
Notes: `alternatives` exposes the second-best option so a human can see when the top-2 margin is thin (the interface-level
version of "we are not certain"). `eligibility` is the separate purpose gate ([S48] pattern).

### 2.2 `POST /v1/score_visit` — the in-visit answer (T2)
```json
{ "visit_id": "V-000123", "candidate_id": "c_8f3a...", "checkin": {"x":1500.1,"y":-790.4,"accuracy_m":12.0},
  "trail_so_far": [{"ts":"...","x":1490.0,"y":-800.0,"accuracy_m":9.0}, "..."], "dwell_s": 90 }
```
```json
{ "stage": "T2", "agreement": "low", "distance_to_candidate_m": 210.0,
  "hint": "you are ~210 m from the locality-level pin; the belief is PROBABLE with a 210 m radius — check the cross street",
  "reason_codes": ["distance_exceeds_radius", "vendor_stratum=locality"], "coordinate_moved": false }
```
This endpoint exists to change field behaviour *while it is still useful*. It cannot relocate a coordinate by itself:
one negative observation can never relocate a coordinate by itself; accumulated independent negative evidence demotes confidence, widens the radius, marks `MOVED_SUSPECTED`/`CONTESTED` and triggers re-verification; only positive evidence or adjudication can establish a new primary coordinate (F2.1/D36). `coordinate_moved=true` is only ever written by an adjudication record.

### 2.3 `POST /v1/ingest_evidence` — the post-visit write (T3 → fast loop)
```json
{ "visit_id": "V-000123", "address_id": "AD-00088", "outcome": "met_family",
  "checkin": {"x":1500.1,"y":-790.4,"accuracy_m":12.0,"mock_flag":false},
  "trail": [["2026-05-04T10:02:00Z",1490.0,-800.0,9.0], "..."],
  "media": [{"hash":"9f2c...","phash":"ab12..."}], "agent_id": "AG-007", "observed_at": "2026-05-04T10:41:00Z" }
```
```json
{ "evidence_score_id": "E-9a1c", "w_place": 0.86, "w_person": 0.71,
  "reason_codes": ["met_family", "dwell_ok", "trail_agree", "photo_unique"],
  "belief": { "version": 8, "tier_after": "CONFIRMED", "radius_after_m": 95.0, "changed": true },
  "contradiction": null,
  "next": { "verification_task": null } }
```
When nothing changes, the response says `"changed": false` with reasons — a confirmation is not supposed to be dramatic.

### 2.4 `POST /v1/adjudicate` — human confirmation (the only new ground truth)
`{ "visit_id": ..., "decision": "confirm|deny|inconclusive", "actor": "...", "note": "..." }` →
`{ "observation_id": ..., "belief_version": ..., "effect": {...} }`. Adjudications are stored as observations with
`kind='adjudication'` and never enter S-Eval (`PS3_ADDRESS_MEMORY_ARCHITECTURE.md` §7).

### 2.5 Memory reads (governed)
* `GET /v1/belief/{address_id}?as_of=…` → belief version (with `support[]`, reasons). `as_of` is **required** for any
  machine consumer; omitting it is only allowed with `purpose=review`.
* `GET /v1/place/{place_key}/history` → versions, observations, contradictions (review UI, paginated).
* `GET /v1/tasks?state=open&town=T2` → the re-verification queue ordered by rule-based priority.

### 2.6 Batch and operations
* `POST /v1/batch_resolve` (≤ 5,000 per call) → streamed results with a per-row `reason_codes` and an aggregate summary
  (refusal rate, tier mix, radius histogram). **Batch never returns a "bulk accuracy" claim** — accuracy is measured on
  adjudicated/surveyed ground truth only.
* `GET /v1/health` → component status (`memory`, `index`, `vendor`, `registry`), current champion model version,
  calibration map version, pack age.
* `GET /v1/audit/{belief_id}` → the full provenance chain for an answer (this is what a reviewer or a regulator asks for).

---

## 3. Error vocabulary (stable, meaningful, non-blaming)

| Code | When | Body |
|---|---|---|
| `ok` | resolved | full payload |
| `unplaceable_outside_town` | `town_id = OUT` / no gazetteer scope | no coordinate; reason + coverage contribution |
| `unplaceable_no_evidence` | no candidate and no usable prior | no coordinate; `arms_available: []` |
| `calibration_fallback_applied` | stratum below the n-guard | coordinate returned, radius widened, `n_calibration` shown |
| `pack_stale` (offline) | `pack_age_days > horizon` | coordinate + widened radius + `pack_age_days` |
| `vendor_unavailable` | vendor arm failed/slow | local arms only, `cost.vendor_calls = 0` |
| `memory_unavailable` | belief store down | serve snapshot; **writes refused** (never accept evidence that cannot be logged) |
| `contested` | contradictory supports | coordinate = primary + `alternatives[]` + `contradiction` block |
| `schema_mismatch` | caller's schema version unsupported | 4xx with the supported versions |

Refusals and fallbacks are **counted as product metrics**, not as incidents (`PS3_EXPERIMENT_PLAN.md` §4).

---

## 4. Components behind the API (already defined in `PS3_SYSTEM_DESIGN.md` §1)

| Endpoint | Components touched | p95 budget |
|---|---|---|
| `/resolve` | C2 → C3 → C4 → C5(read) → C6 | 250 ms local (official arms only; no external calls) |
| `/score_visit` | C7 (partial) | 80 ms |
| `/ingest_evidence` | C7 → C5(write) → C8 → C9.buffer | 120 ms |
| `/belief`, `/place`, `/tasks` | C5/C8 read | 60 ms |
| `/batch_resolve` | as `/resolve`, streaming | 5,000 rows ≪ 5 min on one CPU |
| `/health`, `/audit` | ops/read models | 50 ms |

---

## 5. Deliberately absent from the API

* **No `geocode(text) → lat,lon` endpoint.** A bare point is the thing this system refuses to be. Every coordinate arrives
  with granularity, tier, radius and reasons.
* **No "confidence" single number.** Confidence is a vector (tier, radius, coverage, reasons); collapsing it invites misuse.
* **No auto-write endpoint for external callers.** Memory changes only through evidence with integrity context.
* **No admin edit of a belief.** Corrections are new versions with a reason and an actor.
* **No visitor/notification side effects.** The eligibility gate informs; the action belongs to the workflow that owns it
  (a bank's notice process), so SUTRA cannot accidentally become a decision-maker.

---

## 6. Cold-start and offline behaviour (contract level)

| Situation | Behaviour |
|---|---|
| New town, empty memory | `tier=APPROXIMATE`, radius from parent stratum, reasons `cold_start`, `calibration_fallback`; `arms_available` shows what exists |
| No vendor pin (the 237 `OUT` records) | `unplaceable_outside_town`; the record is still counted and surfaced for coverage planning |
| Offline field app | local pack serves resolve + score_visit + **local belief updates**; response marked `offline=true`, `pack_age_days=N`, radius widened; sync reconciles by rule (higher-weight evidence wins; ties → `CONTESTED`) |
| Vendor outage | local arms; `vendor_unavailable`; latency budget honoured; cache serves until its licence clock expires |
| Memory outage | read-only snapshot; evidence queued with idempotent ids; no promotion while writes are blocked |

---

## 7. Non-functional requirements (measured, not asserted)

| Requirement | Target | How verified |
|---|---|---|
| Latency | p50/p95 per §4 | load test in the demo harness; reported in `PS3_COST_ARCHITECTURE.md` |
| Throughput | ≥ 100 resolves/s single node (cached) | batch replay of the 3,117-record book |
| Idempotency | replaying all 5,578 visits twice changes no belief | automated test |
| Auditability | every belief reconstructible from observations | rebuild test on a sample of places |
| Determinism | same inputs + same versions ⇒ identical outputs (bit-for-bit on the JSON number fields) | golden-file test |
| Licence safety | no non-shippable row served | negative test with a `shippable=false` fixture |
| Invariant safety | single negative observation cannot relocate a coordinate; accumulated independent negatives only demote/widen (`F2.1`); no pin-agreement feature; no T2 feature at T1 | unit tests wired into CI |

**What this design changes in the real workflow:** a collections operator gets an answer they can *act on and defend* —
"PROBABLE, 210 m, confirmed once by a field visit on 3 May, locality-grade vendor pin, contested alternative 400 m away" —
instead of a coordinate that silently mixes a guess, a rental and a memory.

---


## Amendment (2026-10-07) — the response and the two decision modules

`/resolve` keeps its contract and gains the decision payload the requirements always implied:

```
{ candidate, granularity, tier, radius_m, radius_basis, nominal | null, measured_coverage, n_calibration,
  reasons[], stage="T1", arms_available[],
  request_purpose: "<declared by the caller — access-control input>",
  address_purpose: {class: "HOME_LIKE" | "WORK_LIKE" | "OTHER" | "UNKNOWN", confidence, basis[]},
  directions: [ {landmark, distance_m, bearing_deg, cue_text, ambiguous} ] | null,
  eligibility: {action: "SERVE" | "VERIFY_FIRST" | "REFUSE", reason} }
```

* `purpose` and `eligibility` are computed by the rule-based decision modules (`PS3_PURPOSE_AND_DIRECTION_MODULES.md`);
  `directions` is deterministic landmark cueing, never road navigation.
* **VERIFY_FIRST** is a first-class action: the API can say *"cheap task before expensive visit"* with its reason.
* No endpoint accepts a model-derived belief as evidence; evidence enters only through the observation path (M3).
