# SUTRA — CANONICAL SCHEMA

One schema, defined **before** any cleaning, so that the official dataset and every external dataset are mapped onto the
same meaning rather than force-fitted into the official file layout. Nothing is dropped silently; nothing is promoted to
"ground truth" without being labelled.

Conventions below: **required** = the pipeline cannot run without it · **optional** = enhances · **derived** = computed
by us and always versioned.

---

## 1. The five entities

```
TOWN ─┬─ LOCALITY ──── ADDRESS_RECORD ──┬── CANDIDATE (0..n)
      └─ LANDMARK                        └── OBSERVATION (0..n) ── EVIDENCE_SCORE (1)
                                                               └── TRAIL (0..1 per observation)
```
An `ADDRESS_RECORD` is the unit of work (one `address_id`). A `CANDIDATE` is a possible location for it. An
`OBSERVATION` is what an agent reported (check-in, outcome, photos). A `TRAIL` is the GPS trace of a visit.

---

## 2. Canonical tables

### 2.1 `town`
| Field | Type | Req | Notes |
|---|---|---|---|
| town_id | str | ✔ | canonical id |
| town_name | str | ✔ | as stored |
| address_style | enum | ○ | e.g. `karnataka`, `hindi`, `metro` — a hint for normalisation, never a model feature |
| approx_radius_m | int | ○ | coarse prior for the town's spread |
| centroid_x, centroid_y | float | ○ | **local metric plane** in this dataset (see §4) |

### 2.2 `locality`
| Field | Type | Req | Notes |
|---|---|---|---|
| locality_id | str | ✔ | unique |
| town_id | str | ✔ | parent |
| locality_name | str | ✔ | **not unique alone** — duplicates across towns exist (e.g. "Nehru Colony" in two towns) |
| pincode | str(6) | ○ | string, not int — preserves leading zeros |
| centroid_x, centroid_y | float | ○ | approximate centre; the honest *coarse* artefact |

### 2.3 `landmark`
| Field | Type | Req | Notes |
|---|---|---|---|
| poi_id | str | ✔ | unique |
| town_id | str | ✔ | parent |
| landmark_type | enum | ✔ | in the official data: 14 types (temple, masjid, school, water tank, dairy…) |
| name | str | ✔ | **globally non-unique**; `(town_id, name)` also repeats → a name is *not* an identity |
| x, y | float | ✔ | point |

### 2.4 `address_record`
| Field | Type | Req | Notes |
|---|---|---|---|
| address_id | str | ✔ | PK |
| account_id | str | ✔ | FK → account (the household/borrower link) |
| address_type | enum | ○ | `residence` / `office` / `permanent_native` |
| source | enum | ○ | how the address entered the system (`kyc_origination`, `skip_trace`, …) — provenance, useful for priors |
| added_date | date | ○ | record age; also a **time anchor for leakage control** |
| town_id | str | ✔ | may be `OUT` = outside any modelled town → a first-class state, not an error |
| address_text | str | ✔ | the query, verbatim, never overwritten |
| text_norm | str | derived | NFKC + case + punctuation-normalised + abbreviation-expanded (versioned) |
| parse_json | json | derived | token spans: house/plot, lane/`gali`, block/sector, locality, town, pincode, landmark phrase, relation words (near/opposite/behind) |
| script_mix | str | derived | detected scripts present (Latin / Devanagari / Kannada / …) |
| flags | bitmask | derived | e.g. `NO_HOUSE_NUMBER`, `NO_PINCODE`, `PINCODE_UNKNOWN`, `SINGLE_BLOB`, `DUP_TEXT` |

### 2.5 `candidate`
| Field | Type | Req | Notes |
|---|---|---|---|
| candidate_id | str | ✔ | deterministic hash of (address_id, arm, source_ref) |
| address_id | str | ✔ | FK |
| arm | enum | ✔ | **official arms only** (final data policy), frozen by `PS3_IMPLEMENTATION_CONTRACTS_2026-10-07.md` §4: `frozen_baseline` · `locality_centroid` · `town_centroid` · `official_landmark` · `address_book` · `field_evidence` · `memory` · `place_neighbour` (C2-gated, off) |
| source_ref | str | ✔ | the id in the arm's source table (or `NULL` for computed candidates) |
| x, y | float | ✔ | position |
| granularity | enum | ✔ | `rooftop` / `street` / `locality` / `pincode` / `town` / `unknown` — never silently upgraded |
| arm_rank | int | ✔ | rank inside its arm, before fusion |
| fused_rank | int | derived | after rank fusion |
| licence_class | enum | ✔ | `ours` / `open_attribution` / `open_sharealike` / `vendor_tos` / `noncommercial_research` — drives shippability |

### 2.6 `observation` (a field visit, as evidence)
| Field | Type | Req | Notes |
|---|---|---|---|
| visit_id | str | ✔ | PK |
| address_id, account_id, agent_id | str | ✔ | FKs |
| visit_date, start_ts, checkin_ts | ts | ✔ | event time |
| checkin_x, checkin_y | float | ✔ | the agent's reported position |
| gps_accuracy_m | float | ○ | Android convention: **~68% radial confidence** |
| dwell_s | int | ○ | time on site |
| outcome | enum | ✔ | see §3 — carries two dimensions (place vs person) |
| photo_hash | str | ○ | duplicate detection only; never a feature keyed to agent identity |
| remark | text | ○ | free text; landmark phrases may be extracted, amount-like numbers are not trusted |

### 2.7 `trail_point`
| Field | Type | Req | Notes |
|---|---|---|---|
| visit_id | str | ✔ | FK |
| seq | int | ✔ | ordering key; `(visit_id, seq)` unique |
| point_ts | ts | ✔ | |
| x, y | float | ✔ | |
| accuracy_m | float | ○ | per-point 68% radius |

### 2.8 `evidence_score` (per observation, derived, versioned)
| Field | Type | Req | Notes |
|---|---|---|---|
| visit_id | str | ✔ | FK, one row per observation |
| weight | float ∈ [0,1] | ✔ | the contribution this observation may make to a coordinate |
| class | enum | ✔ | `strong` / `medium` / `weak` / `quarantine` |
| flags | list | ✔ | e.g. `MOCK_SUSPECT`, `DUPLICATE_PHOTO`, `TRAIL_DISAGREES`, `CHECKIN_OFF_TRAIL`, `DWELL_TOO_SHORT`, `COORD_REUSE`, `AGENT_OUTLIER` |
| rule_version | str | ✔ | which scoring rules produced it |
| rationale | json | ✔ | per-signal contributions (explainability requirement) |

### 2.9 `location_belief` (per address, versioned, append-only)
| Field | Type | Req | Notes |
|---|---|---|---|
| address_id | str | ✔ | FK |
| version | int | ✔ | monotonically increasing; **old versions never destroyed** |
| x, y | float | ○ | null only if `UNPLACEABLE` |
| radius_m | float | ○ | the published radius for the nominal coverage level |
| coverage_nominal | float | ✔ | e.g. 0.9 |
| coverage_measured | float | ○ | from the calibration sample; `null` when n is too small to claim |
| tier | enum | ✔ | `CONFIRMED` / `PROBABLE` / `APPROXIMATE` / `UNPLACEABLE` |
| reason_codes | list | ✔ | closed vocabulary, e.g. `NO_GAZETTEER_MATCH`, `OUTSIDE_TOWN`, `CONFLICTING_EVIDENCE`, `LICENCE_BLOCKED` |
| n_observations, n_strong, n_agents | int | ✔ | counts behind the belief |
| model_version, rule_version, schema_version | str | ✔ | reproducibility |
| as_of | ts | ✔ | belief time |

### 2.10 `account` (context only)
`account_id`, `lender_id`, `portfolio`, `town_id`, `dpd_start`, `outstanding`, plus whatever a consumer needs to price a
visit. **No account field may be a feature of the location model** — it is context for routing/reporting only, so a
change in collections policy cannot silently move coordinates.

### 2.11 `split_ledger`
`address_id`, `account_id`, `split` (`train`/`validation`/`test`), `group_key` (account or normalized-address hash),
`assigned_at`, `rule_version`. Entity- and time-aware: no address or account may appear in two splits.
**Place note (2026-10-07):** account-level grouping does **not** separate places — 124 of the 344 test addresses with a
met-someone visit (36.0%) sit within 30 m of train-split met evidence `[S94]`. The ledger therefore also references the
place-block fold (`data/derived/ps3_place_blocks.csv`, Amendment A1) for evaluation; the official split itself is never
edited.

### 2.12 `lender` (assigned shared; context only)
`lender_id`, `lender_name`, `lender_code`, `lender_style`. The sixth assigned shared table, imported into the frozen tree
2026-10-07 (byte-identical to the official Drive pack). **Context only:** it names the counterparty behind an account;
measured to carry no address-style signal (portfolio differences ≤1.4 pts), so it is never a feature. A schema row
exists so that no downstream consumer silently invents one.

---

## 3. Outcome vocabulary (the two dimensions)

| Outcome | Place evidence | Person evidence | Notes |
|---|---|---|---|
| `met_borrower` | **strong positive** | positive | a human at the place confirmed identity |
| `met_family` | **strong positive** | weak positive | place confirmed, borrower not met |
| `cash_collected` | **strong positive** | positive | strongest possible real-world confirmation |
| `locked_premises` | weak positive | none | the door exists; nothing about the person |
| `neighbour_says_shifted` | weak positive | **negative** | place resolved, person moved |
| `no_such_person` | weak positive | **negative** | as above |
| `address_not_traceable` | **negative about the record, not the place** | none | agent could not find it — this is evidence about the *address text*, the *agent*, or the *time of day*, and can never relocate a coordinate by itself: accumulated independent negatives only demote/widen/mark `MOVED_SUSPECTED`/`CONTESTED` and trigger re-verification (F2.1/D36) |

> This decomposition is a design decision, and it is the reason the intelligence layer cannot be a single
> classifier over `outcome`. Measured consequence in our data: on the 100 surveyed addresses, met-someone check-ins sit a
> median **29 m** from truth while `address_not_traceable` check-ins sit **1,603 m** away with a **1.3-minute** median
> dwell. Treating the latter as a location label would teach the system to move pins to the wrong street.

---

## 4. Coordinate frame — an explicit assumption we must not paper over

The official dataset's coordinates are a **local metric plane** (`x`, `y` in metres, values roughly −4,400…+4,400), not
latitude/longitude. There is **no projection, no road graph, no administrative polygon** in the package.

Consequences, stated as design constraints:
1. Every distance, radius and cluster operation in this package is in the dataset's own metric plane.
2. For a real deployment the same schema carries `lat`/`lon` (WGS84) plus an explicit `crs` field; the swap is a
   conversion at the ingest boundary, not a redesign.
3. Map matching (HMM) and any polygon-based validation are **out of scope for this dataset** and are marked RESEARCH
   ONLY — they are not quietly attempted.
4. A `DIGIPIN`/geohash rendering of a confirmed coordinate (S40) is the shipping form of the same point once a real CRS
   exists; until then it stays a roadmap item.

---

## 5. Mapping rule — vendor schema → canonical *(retained; no external dataset is loaded)*

The procedure below was written for mapping any incoming dataset into the canonical schema. Under the **final data policy
(2026-10-07)** no external dataset exists, so today it applies to exactly one input: the **vendor API response** (candidate
ingest, never our record of truth) and the official tables themselves `[S95]`.

## 6. Versioning

Every derived artefact carries `schema_version`, `rule_version` and `source_snapshot` (dataset hash). A belief cannot be
reproduced without those three strings, and `PS3_MLOPS_ARCHITECTURE.md` makes them mandatory on every write. The
canonical schema is versioned in this file; a breaking change requires a new `schema_version` and a migration note here
— not an in-place edit.


---

**Sources.** External claims resolve in `PS3_SOURCE_REGISTER.md` (`[S1]`–`[S50]`); internal measurements are
`[S90]` (audit log `data/derived/ps3_audit_full.txt`), `[S91]` (radius calibration
`data/derived/derived_ps3_radius_calibration.csv`) and `[S92]` (prior-pass measurements). Statements that cite no
external source rest on internal evidence and are labelled `[DATA]`/`[INFERENCE]` where they appear.
