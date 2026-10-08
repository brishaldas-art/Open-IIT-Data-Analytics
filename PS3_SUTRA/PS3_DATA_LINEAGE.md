# SUTRA — DATA LINEAGE

Provenance for every byte the system reads or writes: source, version, acquisition date, licence, transformation, and
which stage consumed it. The rule this file enforces: **the official dataset is the canonical benchmark and is never
overwritten; and no third-party or external data exists anywhere in the tree to contaminate it.**

---

## 1. The two domains

```
data/
├── official_ps3/        DOMAIN A — the official dataset. READ-ONLY. The benchmark. Never edited, never merged.
│                        Scope of record (2026-10-07): 12 tables. The assigned shared `lenders.csv` (6×4,
│                        context only) joined the tree byte-identical to the official Drive pack
│                        (hash recorded in the audit folder's data/drive_verification.csv); the frozen-tree
│                        hash set was re-baselined and `check_workspace.py` now asserts 12 tables.
│                        The assigned shared tables `dial_attempts` and `payments` belong to other problem
│                        statements and are excluded — this task has no financial outcome variable.
├── external_research/   REMOVED 2026-10-07 — external data is prohibited by the final data policy (see §4).
│                        The directory remains only as a reserved, permanently-empty path; the workspace guard fails
│                        if anything is placed in it or if any dataset appears outside the three sanctioned folders.
├── cleaned/             derived from A only: cleaned tables + the transformation log
└── derived/             everything computed: audit profiles, radius table, candidate sets, features, manifests
```

Rules:
1. Nothing writes into `official_ps3/`. `tools/ps3_audit.py` and `tools/clean_official.py` open it read-only; a test
   (`check_workspace.py`) fails the build if a file's hash changes.
2. `cleaned/` is a *transformation* of A with a row-level log — never a silent fix-up.
3. `derived/` may contain both, but every row carries `source` and `licence_class`, so a mixed artefact is impossible to
   mistake for an official benchmark.
4. *(Superseded — no external rows may exist at all; the guard enforces emptiness.)* Historical rule, kept for the record:
   external rows were to be marked `provenance=external` and `shippable=true|false|unknown`; a `false` row may not enter a
   shipped index, and the loader refuses it.

---

## 2. Domain A — official PS3 data (12 files)

| File | Rows | Capture | Licence / note | Consumed by |
|---|---|---|---|---|
| `accounts.csv` | 2,400 | Drive folder `18iqIR8TjXDqf9-hgEY34uJr_DraIl_3P`, 6 Oct 2026 | synthetic, provided by CreditNirvana; **no licence for redistribution granted to us** → internal use | context only (visit pricing by a consumer) |
| `addresses.csv` | 3,117 | ″ | ″ | S0 ingest, S2 parse, S4 resolution, S5 candidates |
| `agents.csv` | 30 | ″ | ″ | integrity baselines (S9), not a model feature |
| `baseline_geocodes.csv` | 2,880 | ″ | ″ — vendor stratum vocabulary; **if this were real Google content, caching rules apply (S8/S48)** | S5 candidate arm A, stratum key |
| `field_visits.csv` | 5,578 | ″ | ″ | S9 integrity, S10 fusion, S12 promotion |
| `landmarks_poi.csv` | 240 | ″ | ″ (dataset README flags it as incomplete and imperfect) | S4/S5 language prior only |
| `localities.csv` | 36 | ″ | ″ | S4 resolution, S5 candidate arm B, uncertainty strata |
| `splits.csv` | 2,400 | ″ | ″ | evaluation protocol (extended, see §5) |
| `surveyed_addresses.csv` | 100 | ″ | ″ | **ground truth for evaluation only** |
| `towns.csv` | 3 | ″ | ″ | coarse prior, strata |
| `visit_gps_points.csv` | 160,406 | ″ | ″ | S9 trail geometry only |
| `DATASET_README.md`, `README_DATA_PS3.md` | — | ″ | dataset's own words | provenance of record |

**Source integrity:** SHA-256 of every file is recorded in `tools/section_manifest.csv`. A change in Domain A is a
pipeline-breaking event (it invalidates the audit, the radius table and every experiment), and is treated as a new
`source_snapshot` version rather than a silent update.

---

## 3. Transformations of Domain A (each one logged, reversible)

| Step | Tool | What it produces | What it must never do |
|---|---|---|---|
| T1 profile | `tools/ps3_audit.py` | `derived/ps3_table_profile.csv`, `ps3_column_profile.csv`, `ps3_leakage_map.csv`, `ps3_audit_full.txt` | write anything | 
| T2 clean | `tools/clean_official.py` | `cleaned/addresses_clean.csv`, `visits_clean.csv`, `gps_points_clean.csv`, `cleaning_log.csv` | drop a row without a logged reason; "fix" a coordinate; invent a label |
| T3 candidates + features | `tools/build_candidates.py` | `derived/candidates_<scope>.csv`, `derived/features_<scope>.csv` (+ a leakage receipt per artefact) | use any T2+ field; read `surveyed_*` |
| T4 calibration | `tools/build_derived_table.py` | `derived/derived_ps3_radius_calibration.csv` | include an address that was ever used for training |
| T5 experiments (later) | `experiments/` (planned) | metrics, model cards | claim a number not reproducible from the ledger |

Every artefact carries: `source_snapshot` (hash of Domain A), `schema_version`, `rule_version`, `created_at`, `rows_in`,
`rows_out`, `dropped_by_reason`.

---

## 4. External data — **REJECTED** (final data policy, 2026-10-07)

**External-data augmentation was considered during research but rejected by final project decision. The final PS3 system
uses only the official CreditNirvana dataset and the legitimately PS3-relevant shared data.**

Recorded history (for provenance only — none of this is an active plan):

| Considered | Fate |
|---|---|
| Overture Maps, OSM/Geofabrik, Google Open Buildings, Microsoft ML Building Footprints, OpenAddresses | **Rejected** — no external geographic source may enter candidate generation, features, training or metrics |
| Nominatim / any external geocoder | **Rejected** — not queried, not cached, not a model input |
| India Post PIN directory (data.gov.in, NDSAP non-commercial), Amazon LMRRC (CC BY-NC) | **Rejected** — licence-restricted and unnecessary |
| The detailed evaluation of each | `90_Archive/ps3_rejected_2026-10-07/PS3_EXTERNAL_DATA_RESEARCH.md` (marked REJECTED); register entries S39–S47 carry the rejected marker |

**What replaces them:** the official arms already in the data — the official frozen baseline geocode arm, official towns/localities, official
landmark/POI anchors, official address-book anchors, official historical field evidence, and address memory. Where those
are exhausted, the sanctioned investments are **official-data parsing, memory quality, field-evidence capture and
calibration** (`PS3_FINAL_DATA_AND_ARCHITECTURE_FREEZE.md` §DATA).

**Forbidden-input register (unchanged in force, now absolute):** no scraped dataset · no own-experiment artefact as data ·
material from other problem statements · no model-derived value promoted to ground truth. Bound by the guard in
`tools/check_workspace.py`.

## 5. Split protocol and its lineage

`splits.csv` (account-level, 1,680/360/360) is the dataset's protocol and is preserved. Because it is account-level
only, the pipeline additionally assigns every address a `group_key = hash(account_id, normalized_address_text,
town_id)` so that the same building written twice cannot straddle a split. The ledger (`split_ledger`, canonical schema
§2.11) records which rule produced which assignment; a change of rule is a new `rule_version`, and any experiment must
state the `rule_version` it used. For the learning-loop simulations the ledger is extended with a *time* dimension
(visit-based, not address-based), so that "what did the system know before this visit?" is always answerable.

---

## 6. Retention and destruction

| Artefact | Retention | Why |
|---|---|---|
| Domain A tables | life of the project | benchmark integrity |
| *(no external snapshots exist)* | — | the guard fails the build if any non-official dataset appears |
| Raw GPS trails | 90 days rolling in the design (the aggregation and the derived evidence score persist) | evidence need vs storage/privacy minimisation |
| `location_belief` versions | permanent, append-only | auditability of any action taken on a coordinate |
| `evidence_score` rows | permanent (small) | re-deriving a belief must be possible |
| Model artefacts | every promoted version kept; challengers kept 90 days | rollback and comparison |

---

## 7. What would invalidate this lineage

1. A change to `official_ps3/*` (hash mismatch) — the audit, radius table and all experiments must be re-run.
2. A dataset file appearing anywhere outside `data/official_ps3/`, `data/cleaned/`, `data/derived/`.
3. A feature set carrying a T2+ column (caught by `tools/check_leakage.py`).
4. A belief whose `rule_version`/`schema_version` no longer exists in the repo (caught in the manifest).
5. A "ground truth" label that is not `surveyed_*` or an adjudicated confirmation — the single most dangerous form of
   drift in this project, and the reason the promotion rule is rule-based and auditable rather than model-based.


---

**Sources.** External claims resolve in `PS3_SOURCE_REGISTER.md` (`[S1]`–`[S50]`); internal measurements are
`[S90]` (audit log `data/derived/ps3_audit_full.txt`), `[S91]` (radius calibration
`data/derived/derived_ps3_radius_calibration.csv`) and `[S92]` (prior-pass measurements). Statements that cite no
external source rest on internal evidence and are labelled `[DATA]`/`[INFERENCE]` where they appear.
