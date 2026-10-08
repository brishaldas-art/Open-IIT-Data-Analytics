# PS3 ⇄ SHARED DATA ALIGNMENT

**Purpose:** map every PS3 requirement (from the verbatim statement, `docs/PS3_DATA_REQUIREMENTS.md` §1) to the actual field that would serve it, state whether it is available, what transformation is needed, whether it is usable, what is missing, and how confident we are. **No gap is filled with an invented value.**

Legend: `[PS]` statement text · `[PACK]` pack structure · `[DATA]` measured · `[INFER]` our reading · Confidence = that availability/semantics are as stated, not that the field is fit for production.

---

## 1. Alignment table

| # | PS3 requirement | Source file → field | Available? | Transformation required | Usable for the PS3 task? | Usable for Adjacent? | Missing information | Confidence |
|---|---|---|---|---|---|---|---|---|
| 1 | Address as written (clauses 1–2) | `addresses.address_text` | **Yes** (3,117) | Normalise script/whitespace; parse trailing ` - <6 digits>` tail (93.3%) | **Yes — the core input** | N/A — no cinema entity | Nothing for the task; the texture *is* the task | High |
| 2 | Address context | `addresses.{address_type, source, added_date, town_id, account_id}` | Yes | None | Yes (stratifiers) | N/A | — | High |
| 3 | Baseline to beat (clause 3) | `baseline_geocodes.{geocoder_x, geocoder_y, precision}` | **Yes** (2,880 = 92.4%) | None; stratify by `precision` | **Yes — the comparator** | N/A | 237 addresses have no pin; vendor method unknown | High |
| 4 | Ground truth for evaluation | `surveyed_addresses.{surveyed_x, surveyed_y}` | **Yes but tiny** (100 · 3.2%) | Join on `address_id`; check split overlap | Yes, with **explicit small-n caveats** | N/A | 2nd survey; surveyed accuracy figure; `OUT` coverage | High |
| 5 | Output point (clause 4) | (produced by the model; check-in/trail data below) | Target derivable | — | Yes | N/A | — | — |
| 6 | **Confidence radius** (clause 4) | No radius field exists anywhere | **No** | Must be **produced and calibrated**: use check-in dispersion + `gps_accuracy_m` + baseline stratum, validated on the 100 | Yes, but it is *our* construct | N/A | Radius definition (1σ? 90%?); acceptance method | High that it is absent |
| 7 | Landmark-based directions (clause 4) | `landmarks_poi.{landmark_type, name, x, y}`; `localities`; landmark spans in the text | **Partial** (240 pts, 14 names, 198 duplicate (town,name) pairs; README: *"incomplete and slightly off"*) | Extract landmark mentions from text; match to POI by name within town; treat as hint, not target | **Partially — directions only, never as coordinates** | N/A | Complete landmark inventory; naming variants | High |
| 8 | "Learns from **successful** visits" (clause 5) | `field_visits.{outcome, dwell_s, checkin_x, checkin_y, gps_accuracy_m, photo_hash}` | **Yes** (5,578 visits over 1,477 addresses) | Convert outcomes into evidence weights; **`address_not_traceable` must never become a negative location** | **Yes — the learning signal** | N/A | A rule from the brief on which outcomes may teach | High |
| 9 | GPS trails | `visit_gps_points` (160,406 pts; accuracy median 10 m) | Yes | Per-visit geometry; dwell/cluster detection | Yes (process evidence) | N/A | — | High |
| 10 | Visit ↔ address ↔ account linkage | `field_visits.{address_id, account_id}` (0 orphans) | Yes | None | Yes | N/A | — | High |
| 11 | Offline app constraint (clause 6) | — nothing in the data defines the app | **No (not data)** | — | Deployment constraint only | N/A | The app itself | High |
| 12 | Hierarchy assistance | `towns` (3), `localities` (36, centroid + pincode) | Yes | Match locality names/pincodes found in the text to the gazetteer | Yes (candidate generation) | N/A | `OUT` addresses (237) have no town → unroutable | High |
| 13 | Evaluation protocol | `splits.{account_id, split}` 1,680/360/360 | Yes, **account-level & time-blind** | Decide how an account split maps to an address/visit task; or add an entity/time-aware split | Yes, with caution | N/A | Split protocol for geocoding; leakage position of the 100 surveyed | High |
| 14 | Radius / error targets | — | **No** | — | Cannot be scored without our own definition | N/A | The brief defines no metric | High |
| 15 | "Continuously" (cadence) | — single 90-day snapshot, no versioning | **No** | — | Must be argued, not measured | N/A | Any second wave of data | High |
| 16 | Demand context (design extension, not in the brief) | `accounts.{dpd_start, outstanding, portfolio…}` | Yes | Aggregate per address/account | Yes as *context*, never as a location feature | N/A | — | High |
| 17 | Integrity / monitoring | `agents.{channel, tenure, shift}`; `field_visits.photo_hash` | Yes | Flag repeat-hash media; timing anomalies | Yes (gate) | N/A | — | High |
| 18 | Call/contact data | `dial_attempts`, `payments` | Present in the pack but **marked PS1+PS2 by the pack README** | — | **Out of PS3's assigned scope** (in scope only if our standing "PS3-only" rule is lifted) | N/A | Ownership decision | High |

## 2. Gap register

| # | Gap | Impact on PS3 | What would close it | Obtainable from the provided pack? | Confidence |
|---|---|---|---|---|---|
| G-1 | Only 100 surveyed truths (3.2%), 0 from `OUT` | Any accuracy claim is small-n; strata for pincode pins have n=10 | More surveyed addresses | **No** | High |
| G-2 | Coordinates are local planar metres, not lat/lon; no frame origin | The statement's "lat/lon" output cannot be produced as true geographic coordinates from this pack | A documented frame/origin for each town | **No** | High |
| G-3 | No confidence-radius definition or measured radii | Radius must be invented + calibrated by us; comparability to the brief's intent unknown | A stated radius convention | **No** | High |
| G-4 | Landmarks incomplete + "slightly off"; 14 names / 240 points | Directions can only be produced for addresses whose landmark is in the table | A complete POI inventory | **No** | High |
| G-5 | No verifiable "success" rule for *which* visits may teach | Learning loop's eligibility is our design choice | A brief-level rule | **No** | High |
| G-6 | Visits are operationally selected, non-random | Learning from them risks selection bias; must be handled, cannot be eliminated | Randomised visit sampling | **No** | High |
| G-7 | Vendor method unknown | Cannot attribute *why* we beat the baseline | Vendor documentation | **No** | Med |
| G-8 | 237 `OUT` addresses with no town | Unroutable in the 3-town frame; excluded from geography features | Their town assignment | **No** | High |
| G-9 | No second survey / no re-visit audit of known-truth addresses | "Continuous learning" cannot be *measured*, only argued | A post-window survey | **No** | High |
| G-10 | Check-in ≠ door coordinate | Evidence must be weighted, not treated as truth | Door-level capture protocol | **No** | Med |
| G-11 | No `locality`/`pincode` columns on `addresses` | Hierarchy joins must go through free text | Structured locality field | **No** | High |
| G-12 | No address version history | Cannot measure address drift over time | Versioned address records | **No** | High |

## 3. How PS3 and the shared dataset fit together — one paragraph

PS3 **consumes** from shared: `addresses` (input text), `field_visits` (evidence), and the context tables `accounts`/`agents`; it **owns** the geocoding artefacts in `ps3_geocoder` (towns, localities, landmarks, vendor baseline, GPS trails, surveyed truth); and it **uses** `splits.csv` though the split is account-level and time-blind. Two shared files that sit in the same Drive folder — `dial_attempts` and `payments` — are marked **PS1+PS2 only** by the pack README and are therefore out of the PS3 mandate unless the project's standing scope rule changes.

**For the Adjacent/cinema framing:** none of the 18 rows above has a cinema counterpart. The fields a cinema programme-analysis would need — venue identity, programme title, screen, date/time, ticket/attendance, audience — **do not exist in this pack** (`docs/SHARED_DATASET_AUDIT.md` §3). This alignment table therefore doubles as the proof that the pack cannot be re-labelled into an entertainment dataset.

**Provenance note.** Nothing in this table invents a value: every "Usable" verdict is bounded by what the files contain, and every gap is listed rather than filled.
