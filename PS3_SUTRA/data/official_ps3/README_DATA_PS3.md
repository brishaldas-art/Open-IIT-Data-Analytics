# DATA — the tables in the PS3 section

**Source:** the official CreditNirvana PS2/PS3 dataset, delivered as a Google Drive folder
(`18iqIR8TjXDqf9-hgEY34uJr_DraIl_3P`). **Everything in it is synthetic** — the dataset README says so
(`DATASET_README.md`, a copy of the original, sits next to this file). It validates *mechanism*, never magnitude.

**This section is self-contained:** every table PS3 needs is here, including byte-identical copies of the three
tables PS2 also uses. Nothing is read from `../PS2_SANKET/`.

---

## 1. What is here, and why PS3 needs it

| File | Rows | Why PS3 needs it | Owner |
|---|---|---|---|
| `visit_gps_points.csv` | 160,406 | The field evidence: lat/lng with **per-point accuracy** (median 9.8 m ≈ a 68% radial confidence), ~26 points per visit. Source of the integrity findings (645 check-ins >500 m from their own trail) | PS3 only |
| `baseline_geocodes.csv` | 2,880 | The vendor point **and its precision stratum** — PS3's prior and the key to the radius table (rooftop 37.7 m → pincode 1,336.5 m). ⚠ 237 addresses have no geocode: a first-class state, not a skip | PS3 only |
| `surveyed_addresses.csv` | 100 | **The only ground truth in the package.** Every accuracy claim and every radius states whether it is inside or outside this sample | PS3 only |
| `landmarks_poi.csv` | 240 | Landmarks. ⚠ Incomplete and 14/14 names repeat — usable as **priors/telephone-aid only**; naive snapping measured 4,093 m median (worse than baseline in 90% of cases) | PS3 only |
| `localities.csv` | 36 | The gazetteer level for candidate retrieval and the locality ceiling (379 m) | PS3 only |
| `towns.csv` | 3 | Towns with address style and approximate radius — the unit of per-town calibration | PS3 only |
| `field_visits.csv` | 5,578 (1,477 addresses) | Visit outcomes + dwell: the positive evidence PS3 learns from **and** the poison (`address_not_traceable` check-ins sit 1,603 m from truth) | **copy** (also in PS2) |
| `addresses.csv` | 3,117 | Address text, town and locality — what the parser and the retrieval index consume | **copy** (also in PS2) |
| `accounts.csv` | 2,400 | The value side of a field slot (DPD band, outstanding) — how PS3 prices a confirmation | **copy** (also in PS2) |

**Copies are byte-identical to the same table in `../PS2_SANKET/data/raw/`.** Verify with
`sha256sum data/raw/field_visits.csv ../PS2_SANKET/data/raw/field_visits.csv`; `tools/check_section.sh` fails on drift.

## 2. What is deliberately **not** here

| Table | Why not |
|---|---|
| `dial_attempts.csv` (51,105), `phones.csv`, `skip_traces.csv`, `verified_contact_points.csv`, `payments.csv`, `splits.csv`, `agents.csv`, `lenders.csv` | PS2-owned contact and case data. PS3 receives their *result* — verified identity on a met visit — through `visit.completed`, never the raw rows |
| `ps1_fake_ptp/` (4 files, 4 MB) | A **third problem statement** (promise-to-pay) used by neither design. Preserved once at `90_Archive/ps1_fake_ptp_not_used/` |

## 3. Traps these tables carry

1. **No road graph / no polygons** — coordinates are a local metric plane, so HMM map matching is impossible here (documented as RESEARCH ONLY, not quietly attempted).
2. **Negative outcomes manufacture false locations** — `address_not_traceable` check-ins are 1,603 m from truth with 2-minute dwell. Rule: a negative outcome may never move a coordinate.
3. **A planted bad actor** — one agent has 162/172 duplicate photo hashes (26.6% vs ≤1% elsewhere); the integrity gate is what makes the learning loop safe.
4. **Vendor content has a licence clock** — Google permits a lat/lng cache of ≤30 days only, so the canonical coordinate must be field-confirmed (Google Maps Platform Service Terms §6).
5. **`accuracy` is a 68% radius**, not a hard bound (Android `Location.getAccuracy()`).

## 4. Reproduce the numbers from these tables

```bash
./tools/reproduce.sh          # audit sections q + p3, then rebuilds the radius calibration table
./tools/reproduce.sh p3       # PS3 evidence only
```
Outputs the baseline error by stratum, the free-data ceiling (370 m oracle), the visit-learning gain
(385 m → 29 m), the integrity findings and the address structure — then rewrites
`data/derived/derived_ps3_radius_calibration.csv`.
