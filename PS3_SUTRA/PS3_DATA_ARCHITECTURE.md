# SUTRA — DATA ARCHITECTURE

The physical home of every entity in `PS3_CANONICAL_SCHEMA.md`: tables, keys, indexes, the append-only belief store, the
as-of join that makes leakage structurally impossible, partitioning and retention, and the explicit decision *against*
exotic stores.

---

## 1. Store choices (and why they are boring on purpose)

| Store | Used for | Why this and not something else |
|---|---|---|
| **Relational (Postgres in production; SQLite/files in this project)** | addresses, observations, beliefs, evidence scores, accounts, splits, aliases | Every access pattern here is a keyed lookup, a time-range join, or an append. That is a relational workload; the as-of join is a `WHERE observed_at < :as_of` on an indexed column |
| **Local spatial index (R-tree / SQLite R*Tree / a numpy KD-tree in this project)** | gazetteer points, candidate pruning by distance, town containment | the index is *small* (three towns; ~300 points here, ~10⁵ in a real city) and rebuildable in seconds. No need for a geo-database cluster |
| **Object/file store** | media hashes, trail files, model artefacts, town packs, receipts | large, immutable, versioned by content hash |
| **Files in `data/` (this project)** | Domain A, cleaned, derived | the deliverable must be inspectable without a server; the same layouts map 1:1 onto the tables below |
| **Not used: vector DB** | — | no embedding-based retrieval is justified (`PS3_DATA_PREPROCESSING.md` §2); a vector store without a semantic matcher is decoration |
| **Not used: graph DB** | — | the entity graph is 5 node types and 4 relation types, resolved by keys; a graph engine adds operational cost with no query it would serve better |
| **Not used: streaming platform** | — | evidence is per-visit and idempotent by `visit_id`; a queue is a later, local change if volume demands it |

---

## 2. Physical schema (maps 1:1 to the canonical entities)

### 2.1 Reference data (slowly changing, versioned)
```
town(town_id PK, town_name, address_style, approx_radius_m, version, valid_from, valid_to)
locality(locality_id PK, town_id FK, locality_name, pincode, centroid_x, centroid_y,
         source, licence_class, version)
landmark(landmark_id PK, town_id FK, name, type, x, y, aliases[], source, licence_class, version)
                                       INDEX (town_id, lower(name))   -- alias lookup, town-scoped
idx_town_point(town_id, kind, object_id, x, y)   -- R*Tree / KD-tree backing table for distance pruning
```
`locality_name` is **not** unique (`Nehru Colony` exists in two towns) — every lookup is `(town_id, name)`.

### 2.2 Address records (immutable text, mutable interpretation)
```
address_record(address_id PK, account_id FK, town_id FK NULL, address_type, source, added_date,
               address_text, address_text_raw, text_norm, text_sha1,
               group_key,                      -- hash(account_id, norm_text, town_id) for split integrity
               rule_version, created_at)
                                       INDEX (town_id), INDEX (group_key), INDEX (text_sha1)
address_version(address_id FK, version, text_norm, spans_json, resolved_ids_json, rule_version, created_at)
                                       PK (address_id, version)
```
Text is never overwritten: a correction creates a new `address_version` so the history of what was known when remains
queryable — this is the same discipline the belief store uses.

### 2.3 Observation and belief (append-only; the heart of the system)
```
observation(observation_id PK, address_id FK, kind,          -- visit | adjudication | ingest | external
            observed_at TIMESTAMP, actor_id NULL, source_ref,
            x, y, granularity, accuracy_m NULL, dwell_s NULL, outcome NULL,
            evidence_score_id FK NULL, provenance, licence_class, ingested_at)
                                       INDEX (address_id, observed_at)
trail_point(visit_id FK, seq, point_ts, x, y, accuracy_m)
                                       PK (visit_id, seq)   -- partitioned by month; 90-day retention
evidence_score(evidence_score_id PK, visit_id FK, w_i REAL, reason_codes JSONB,
               dims_json JSONB, policy_version, created_at)
location_belief(belief_id PK, address_id FK, version INT, as_of TIMESTAMP,
               x, y, granularity, tier, radius_m, nominal_coverage, measured_coverage,
               support_json JSONB, contradiction_state, reason_codes JSONB,
               policy_version, snake_case_created_by)
                                       PK (address_id, version); INDEX (address_id, as_of DESC)
verification_task(task_id PK, address_id FK, priority, reason_code, created_at, state, outcome)
```
Three structural properties, each a deliberate answer to a red-team failure:
1. **No UPDATE/DELETE anywhere in `location_belief`.** A correction is a new row. Therefore any past answer can be
   reconstructed, and any poisoned belief can be traced and superseded (`PS3_RED_TEAM.md` F6).
2. **`observation.observed_at` is the only clock that matters.** Every read is `observed_at < :as_of`, so the "latest
   value" leak cannot be expressed as a query — it would have to be written deliberately.
3. **`evidence_score` is separate from `observation`.** The weight is a *policy* artefact (`policy_version`); re-weighting
   evidence after a policy change does not require touching the observation.

### 2.4 Accounts, agents, splits (context and governance)
```
account(account_id PK, lender, portfolio, dpd_start, outstanding, emi_amount, ... )   -- never a location feature
agent(agent_id PK, kind, town_id NULL, tenure_months, shift)
agent_baseline(agent_id FK, window_end, dup_media_rate, median_dwell_s, trail_agree_med, n_visits)
split_ledger(account_id, address_id, group_key, split, basis, rule_version, as_of)
```
`account` exists here for record-keeping and visit pricing by a consumer; `check_leakage.py` refuses any artefact whose
feature columns derive from it.

---

## 3. The as-of join (implementation)

```sql
-- belief as it was known at the moment of a decision
SELECT * FROM location_belief
 WHERE address_id = :aid AND as_of < :as_of
 ORDER BY as_of DESC, version DESC
 LIMIT 1;
```
* Index `(address_id, as_of DESC)` makes this a range scan.
* The candidate builder uses the **same** predicate; a unit test asserts that a belief created *after* `as_of` can never
  appear in a warm feature row (the guard is in `tools/build_candidates.py`, checks in `tools/check_leakage.py`).
* Every response records the `belief_version` it read, so "what did the system know at that moment?" is always answerable.

---

## 4. Indexes, partitions, retention, and their measurements

| Table | Growth (real deployment, per 1,000 records) | Partition | Retention | Why |
|---|---|---|---|---|
| `address_record` | 1,000 rows | by town | permanent | the book |
| `observation` | ~2,000 (visits + adjudications) | by month | permanent | evidence is the asset |
| `trail_point` | ~26,000 | by month | **90 days** | heavy, and the derived score survives; privacy minimisation |
| `evidence_score` | ~2,000 | by month | permanent (small) | re-derive beliefs without re-processing trails |
| `location_belief` | ~2,000 versions | by town | permanent | auditability; compaction keeps only *superseded* versions summarised, never the current ones |
| `idx_town_point` | ~10⁵–10⁶ points per city | by town | rebuilt | rebuildable in seconds; a derived artefact, not a source |

**Measured on this dataset:** 3,117 records, 5,578 visits, 160,406 GPS points ≈ **30 MB** total on disk. Extrapolated
linearly (marked `[I]` — an estimate, not a measurement): a 1 M-record book ≈ 10 GB with trails, ≈ 400 MB without.
Storage is not a constraint; **trail retention is a policy choice, not a capacity one.**

**Compaction rule (F16):** superseded belief versions collapse into a summary row keeping `(first_version, last_version,
n_versions, first_seen, last_seen, min_radius, max_radius, reason_histogram)`; the current version and every version that
ever supported a *decision* are kept verbatim. Compaction is verified by a rebuild test.

---

## 5. Index artefacts (what ships to the field)

| Artefact | Contents | Size (per town, this dataset) | Rebuild |
|---|---|---|---|
| `town_pack` | gazetteer (localities, landmarks, aliases), calibration map, policy version, memory subset for the beat | ~1 MB here; ~50–200 MB realistic | minutes, deterministic |
| `calibration_map` | radius per (stratum × evidence class × tier) + measured coverage + n | KB | nightly |
| `alias_table` | vetted locality/landmark variants (reviewed) | KB | on review |
| `model_artefact` | ranker + evidence policy (versioned, hashed) | KB–few MB | slow loop |

**Town packs make offline first-class** (`PS3_SYSTEM_DESIGN.md` §7) and make staleness *visible*: `pack_age_days` is in
every offline response and feeds the radius widening.

---

## 6. Migrations and versioning

* Schema changes are additive: `schema_version` is carried **on every artefact** and on every derived file; a loader
  refuses a mismatch rather than guessing.
* `rule_version` covers cleaning, resolving, candidate building and belief policy separately. Changing a rule that
  touches beliefs (e.g. decay horizon) is a **policy change** that must state its migration: either beliefs are re-derived
  from observations (preferred, since observations are immutable) or the change applies only to new beliefs (recorded).
* Domain A (official) carries its own snapshot hash; a change there invalidates the audit, the calibration and every
  experiment (`PS3_DATA_LINEAGE.md` §7).
* **There is no external-data domain (final data policy, 2026-10-07):** external data is prohibited, not merely separable. The pipeline
  loads `data/official_ps3/` only, and the workspace guard fails if any dataset appears outside
  `official_ps3/`/`cleaned/`/`derived/`.

---

## 7. Backup, restore, and the failure that matters

| Scenario | Design |
|---|---|
| Belief store loss | restore from snapshot + replay `observation`/`evidence_score` (both immutable) → beliefs are *derivable*; that is the whole point of separating observations from beliefs |
| Corrupted model artefact | registry alias rollback to the previous version; the rule-priority fallback keeps serving in the meantime |
| Lost trails but intact scores | acceptable by design (scores are the retained artefact; trails are the raw material) |
| Lost calibration map | serve with parent-stratum radii + `calibration_fallback` reason (wider, honest) until rebuilt |
| Domain A changed by accident | detected by hash check; the pipeline stops, the manifest says exactly which file changed |

---

## 8. What this architecture refuses to do

1. **Store vendor content as our record of truth** — vendor pins are cached inputs with a licence clock (Google 30 days
   [S8]); the coordinate we serve is ours.
2. **Use any data that is not the official dataset** — the pipeline loads `data/official_ps3/` only; a machine guard fails
   the build if any other dataset file appears anywhere in the tree (`PS3_FINAL_DATA_AND_ARCHITECTURE_FREEZE.md` §DATA).
3. **Keep a "current state" shortcut table** — a denormalised `address_current` view exists for serving speed but is
   marked *derived*, carries the belief version it was built from, and is never a source for a model feature.
4. **Hide deletion.** Retention rules are explicit; when a trail expires, the fact is recorded.
5. **Use the location store for anything else.** Coordinates are for locating a visited address; the purpose gate lives in
   the API, and no downstream consumer reads this store without declaring a purpose.

---

## 9. Shared-table role contract (final data policy, 2026-10-07)

The six officially assigned shared tables are used, each **only in its role** — the distinction that must stay consistent
across the data architecture, preprocessing, leakage map, feature schema, experiments, model cards and the final report:

| Table | Role | May be used for | May **never** be used for |
|---|---|---|---|
| `addresses` | **REQUIRED** | core model input: text, keys, town, type, added date | — |
| `field_visits` | **REQUIRED** | core learning/evidence input: outcomes, timing, dwell, media, trails | — |
| `accounts` | **EXPOSURE / BUSINESS CONTEXT ONLY** | visit-selection analysis, exposure-matched reporting, business-value context | any coordinate feature; any place inference |
| `agents` | **INTEGRITY / MONITORING ONLY** | evidence-integrity weighting, per-collector windowed baselines, collector grouping | any location prior; any ranking feature |
| `splits` | **EVALUATION ONLY** | evaluation protocol (official account split + place-block lens) | training labels; any feature |
| `lenders` | **CONTEXT ONLY** | reporting context (who the counterparty is) | any geocoder feature |

**Excluded by the same policy:** the two shared tables assigned to other problem statements (`dial_attempts`, `payments`)
and everything outside this problem statement. This task therefore has **no financial outcome variable**, by design.

**No external data.** The pipeline loads `data/official_ps3/` only. `tools/check_workspace.py` fails the build if any
dataset file appears anywhere outside `data/official_ps3/`, `data/cleaned/` and `data/derived/`, and fails if
`data/external_research/` is non-empty. Binding statement: `PS3_FINAL_DATA_AND_ARCHITECTURE_FREEZE.md`.
