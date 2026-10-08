# PS3 DATA REQUIREMENTS — as stated, not inferred

**Rule applied throughout:** anything not present in the problem statement or the pack is marked `[UNKNOWN — not stated]` rather than filled in. `[PS]` = text of the problem statement; `[PACK]` = the dataset README / observed pack structure; `[INFER]` = our reading; `[DATA]` = measured from the 21 files.

---

## 1. The problem statement, verbatim

> **Problem statement 3:** *An address geocoder that learns from field visits. Indian addresses are descriptive and landmark-based, mixed-language, transliterated, misspelt. Commercial geocoders land at locality/pincode centroids. Output must be lat/lon + confidence radius + landmark-based directions, continuously learning from new successful visits. The field app must work offline.* `[PS]`

(Text as recorded in our archive from the brief; the Drive itself contains no statement document.)

## 2. Exact problem definition — six clauses

| # | Clause (`[PS]`) | What it demands, precisely |
|---|---|---|
| 1 | "address geocoder" | Input = the address as written on file; output = a location for **that address** |
| 2 | "Indian addresses are descriptive and landmark-based, mixed-language, transliterated, misspelt" | Must survive real address texture: two scripts mixed in one string, landmarks as the primary reference frame, no house-number discipline, spelling variation |
| 3 | "Commercial geocoders land at locality/pincode centroids" | The **baseline to beat** is defined by the pack's own vendor output (`baseline_geocodes.csv`), not by a generic API |
| 4 | "Output must be lat/lon + confidence radius + landmark-based directions" | Three outputs: a point, a **calibrated uncertainty radius**, and human-usable directions in landmark terms |
| 5 | "continuously learning from new successful visits" | The system consumes field-visit outcomes and improves over time; "successful" qualifies which visits may teach |
| 6 | "The field app must work offline" | A deployment constraint on the consumer of the output — no network at the doorstep |

## 3. What the statement expects of the data

| Clause | Data it implies | Provided by the pack | Where |
|---|---|---|---|
| 1 | Addresses as written | 3,117 addresses, mixed script, 93.3% carrying a trailing ` - <6 digits>` tail | `shared/addresses.csv` |
| 2 | Language/transliteration reality | 8.41% non-ASCII (Devanagari 154, Kannada 108); 3 address styles across towns | `addresses.csv` + `towns.address_style` |
| 3 | A baseline geocoder's output | 2,880 pins with a claimed precision stratum; 237 ungeocoded | `ps3_geocoder/baseline_geocodes.csv` |
| 4a | A point to be evaluated | **100 surveyed coordinates** — the only ground truth in the pack | `ps3_geocoder/surveyed_addresses.csv` |
| 4b | Uncertainty radius | No radius is given anywhere; must be **produced and calibrated by us** | (derived) |
| 4c | Landmark vocabulary + positions | 240 landmark points across 14 types; the README itself warns this table is *"incomplete and slightly off"* | `ps3_geocoder/landmarks_poi.csv` |
| 5 | Field-visit evidence | 5,578 visits (7 outcomes, dwell, photo hash, check-in) + 160,406 GPS trail points | `shared/field_visits.csv`, `ps3_geocoder/visit_gps_points.csv` |
| 6 | Offline app | Nothing in the data defines the app; the GPS trails and `gps_accuracy_m` describe the collection environment only | (deployment constraint, not data) |
| — | Geography frame | 3 towns, 36 localities with pincodes + approximate centres | `towns.csv`, `localities.csv` |
| — | Context | Accounts (2,400) for demand; agents (30) for integrity/context | `shared/accounts.csv`, `shared/agents.csv` |
| — | Evaluation protocol | 1,680 / 360 / 360 **account-level** split | `shared/splits.csv` |

## 4. Required fields (the pack's PS3 file list, per table)

The README's PS3 list is verbatim: `addresses.csv`, `baseline_geocodes.csv`, `field_visits.csv`, `visit_gps_points.csv`, `surveyed_addresses.csv`, `localities.csv`, `landmarks_poi.csv`, `towns.csv`, `accounts.csv`, `agents.csv`, plus `splits.csv`. `[PACK]`

Minimum viable field set actually consumed by a PS3 solution:

| Need | Fields | File |
|---|---|---|
| Address text + its written context | `address_text`, `address_type`, `source`, `added_date`, `town_id`, `account_id` | `addresses` |
| Baseline + its claimed granularity | `geocoder_x`, `geocoder_y`, `precision` | `baseline_geocodes` |
| Truth for evaluation | `surveyed_x`, `surveyed_y` | `surveyed_addresses` |
| Hierarchy | town name/style/radius; locality name/pincode/centroid | `towns`, `localities` |
| Landmarks | `landmark_type`, `name`, `x`, `y` | `landmarks_poi` |
| Visit evidence | `outcome`, `dwell_s`, `checkin_x`, `checkin_y`, `gps_accuracy_m`, `visit_date`, `photo_hash`, `agent_id`, `address_id` | `field_visits` |
| Trails | `seq`, `point_ts`, `x`, `y`, `accuracy_m` | `visit_gps_points` |
| Context / integrity | account DPD & dues; agent channel/team/tenure | `accounts`, `agents` |
| Split | `account_id`, `split` | `splits` |

## 5. Evaluation expectations

- The statement names **no metric, no threshold and no protocol**. `[UNKNOWN — not stated]`
- What is *given*: 100 surveyed addresses `[PACK]`, a vendor baseline `[PACK]`, and an account-level split `[PACK]`.
- What our delivered design (SUTRA) uses and which must be labelled as **our choice, not the brief's**: median/p75/p90 error and %<50/100/250/500 m against the surveyed 100; radius calibration (coverage vs radius); directional usefulness for the field app; abstention rate. `[INFER]`
- The statement's own success phrase — "continuously learning" — is unscored: no improvement floor, cadence or back-test protocol is specified. `[UNKNOWN — not stated]`

## 6. Intended output

`lat/lon` **(note: the pack stores local planar metres, ±4 km about each town, not geographic coordinates — the frame's origin is not given anywhere, so true lat/lon cannot be produced from the pack alone)** · a confidence radius · landmark-based directions. `[PS]` vs `[DATA]` — the mismatch is a real gap, carried in `docs/PS3_SHARED_DATA_ALIGNMENT.md` as gap **G-2**.

## 7. Constraints

- Offline field app `[PS]`.
- Only 100 surveyed truths, all inside T1–T3, none `OUT` `[DATA]`.
- 237 addresses (7.6%) are `town_id='OUT'` — outside the modelled towns `[DATA]`.
- Visits cover 1,477 of 3,117 addresses (47.4%) and are **operationally selected, not random** `[DATA]`.
- Synthetic, invented data (pack README); 90-day window (2026-04-01 → 2026-06-29) `[PACK]`.
- Standing project rule: no external/augmented/web-scraped data may enter the dataset or the metric.

## 8. Hidden assumptions (each testable, none stated in the brief)

| # | Assumption | Status |
|---|---|---|
| H-1 | A visit check-in approximates the household | Usually yes at ~metres scale (median 7.6 m to nearest own-trail point) but it is a **street-side observation**, not a door coordinate `[DATA]` |
| H-2 | The 100 surveyed coordinates are accurate | Pack calls them "accurately surveyed" `[PACK]`; no accuracy figure given `[UNKNOWN]` |
| H-3 | Visits are representative of the book | **False** — allocation follows delinquency and past outcomes `[DATA]` |
| H-4 | Visit outcomes are honest evidence | Mostly, but one agent carries a repeated photo hash on 162/610 visits (26.6%) `[DATA]` |
| H-5 | The vendor baseline is a fair comparator | It is the pack's designated baseline `[PACK]`; its method is unknown `[UNKNOWN]` |
| H-6 | `address_not_traceable` means "no such place" | **False** — those check-ins sit a median 1,603 m from truth and 84.9% of them are closer to the pin: process failure, not place evidence `[DATA]` |
| H-7 | One address = one household | Not guaranteed; offices and `permanent_native` addresses are in the same table `[DATA]` |
| H-8 | Landmarks can be a coordinate target | **Contradicted by the pack's own README** ("incomplete and slightly off"); 14 names for 240 points `[PACK]` |
| H-9 | Addresses are stable over the window | Only `added_date` exists; no versioned address history `[DATA]` |
| H-10 | "Continuous learning" can be validated | No post-survey update, no second survey, no versioned model log in the pack `[DATA]` |
| H-11 | Town names are real places | **False** — T1/T2/T3 and the localities/pincodes are synthetic `[PACK]` |
| H-12 | Coordinates are lat/lon | **False** — local planar metres `[DATA]` |

## 9. What PS3 says should be done with the shared dataset

The pack README assigns **file ownership**, not a procedure: PS3 uses the 10 files §4 lists plus `splits.csv`; `dial_attempts.csv` and `payments.csv` are marked **PS1 + PS2 only**; `addresses.csv` and `field_visits.csv` are marked **PS2 + PS3** (shared). Beyond that mapping, the brief says nothing about *how* PS3 should consume shared tables. `[PACK]`

## 10. Open questions — not stated anywhere we hold

Do **not** fill these by inference; each is an escalation item:

1. What cadence must "continuously learning" achieve, and what improvement counts? `[UNKNOWN]`
2. Is the confidence radius defined at 1σ, 90%, or "one building"? `[UNKNOWN]`
3. Is the deliverable per address, or per (address, visit) decision? `[UNKNOWN]`
4. Should the vendor pin remain in the loop as a prior, or be replaced? `[UNKNOWN]`
5. How should the account-level split be honoured for an address-level task? `[UNKNOWN]`
6. Are the 237 `OUT` addresses in scope for delivery? `[UNKNOWN]`
7. Is true lat/lon required, or is the local frame acceptable? `[UNKNOWN]`
8. What is the acceptance threshold for "wins" vs the baseline? `[UNKNOWN]`
