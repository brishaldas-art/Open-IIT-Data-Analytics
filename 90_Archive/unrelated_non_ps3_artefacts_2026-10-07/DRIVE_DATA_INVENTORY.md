# DRIVE DATA INVENTORY

**Drive folder audited:** `data` — <https://drive.google.com/drive/folders/11J0vOHyjHH0y4Vjw8_5HZxsBWyVgH48t>
**Audit date:** 2026-10-07 · **Mode:** read-only (nothing in the Drive was modified; no file was uploaded, renamed or moved)
**Method:** the folder listing was read from the Drive embed view; **every one of the 21 files was then downloaded from the Drive and SHA-256 compared with the copy already held in this workspace** → **21/21 byte-identical** (`data/drive_verification.csv` carries the full hashes). Every row count, column count and distribution below is computed from those exact bytes.

**Headline:** the folder is the **CreditNirvana synthetic collections pack** for three problem statements (PS1, PS2, PS3) plus the shared tables. **It contains no film, cinema, venue, programme, audience, ticketing or cultural-affinity data of any kind** (§5 — census over all 149 columns and all free text: zero matches). The four subfolders are `ps1_fake_ptp`, `ps2_right_party_contact`, `ps3_geocoder`, `shared`.

---

## 1. What is in the folder — totals

| Folder | Files | Rows | Columns | What it is |
|---|---|---|---|---|
| `ps1_fake_ptp` | 4 | 51,556 | 27 | Promise-to-pay (PTP) records, call transcripts, post-call events, 200 hand labels |
| `ps2_right_party_contact` | 3 | 6,735 | 18 | Phone inventory, skip-trace requests, 250 verified contact points |
| `ps3_geocoder` | 6 | 163,665 | 29 | Gazetteer, vendor baseline geocodes, field-visit GPS trails, 100 surveyed addresses |
| `shared` | 8 | 66,798 | 75 | Accounts, addresses, agents, dial attempts, field visits, lenders, payments, splits |
| **Total** | **21** | **288,754** | **149** | One synthetic 90-day collections operation, three anonymised towns |

`visit_gps_points.csv` alone is 160,406 rows = **55.6%** of all rows. All 21 files are CSV, UTF-8, RFC-4180 quoting; no archives, no documentation files, **no licence file, no README and no version manifest inside the Drive folders** (the pack's README is held in this workspace at `PS3_SUTRA/data/official_ps3/DATASET_README.md` and is quoted in §6).

**Drive last-modified (as listed):** files — 4 Oct 2026; the four subfolders — 5 Oct 2026. No file carries an internal version field.

**Temporal scope (whole pack):** operationally **2026-04-01 → 2026-06-29** (a 90-day window; use-level detail in each row below). Payment and promise records extend to **2026-07-24**; the contact-verification snapshot is dated **2026-07-02**.

**Geographic scope (whole pack):** three anonymised Indian towns — `T1 Kaveripura` (Karnataka address style), `T2 Devgarh Nagar` (Hindi), `T3 Navanagara East` (metro) — approximate radii 3.8–4.8 km, 36 localities, synthetic 6-digit pincodes (960101–980304), plus 237 addresses tagged `OUT` (outside the three towns). **Coordinates are local planar metres (roughly ±4,000 m about each town), not lat/lon.**

---

## 2. `ps1_fake_ptp` — 4 files

| File | Rows × Cols | What a row is | Temporal | Identifiers | Class | Licence/usage | Relevance to Adjacent | Recommended use |
|---|---|---|---|---|---|---|---|---|
| `ptps.csv` | 3,696 × 13 | One promise-to-pay, from a call or a visit | captured 2026-04-01 → 2026-06-29; promises to 2026-07-24 | `ptp_id` (PK), `account_id`, `attempt_id`, `visit_id`, `agent_id` | Raw | Pack README: used by PS1 | **None** — collections data | PS1-owned; not part of the PS3 mandate |
| `call_transcripts.csv` | 39,194 × 8 | One transcript **turn** (agent/customer/bot) | same window | `call_id` (3,367 calls) | Raw | Pack README: used by PS1 | **None** | PS1-owned |
| `post_call_events.csv` | 8,466 × 3 | One post-PTP event (link sent/opened, WhatsApp reply, inbound call) | 2026-04-01 → 2026-07-20 | `ptp_id` | Raw | Pack README: used by PS1 | **None** | PS1-owned |
| `annotated_ptp_sample.csv` | 200 × 3 | One **hand-labelled** PTP (6 types, 3 confidence levels); "some labels are wrong" per README | n/a | `ptp_id` | **Labelled sample** (200 of 3,696 PTPs) | Pack README: used by PS1 | **None** | PS1-owned; the only human labels in the pack |

## 3. `ps2_right_party_contact` — 3 files

| File | Rows × Cols | What a row is | Temporal | Identifiers | Class | Licence/usage | Relevance to Adjacent | Recommended use |
|---|---|---|---|---|---|---|---|---|
| `phones.csv` | 5,719 × 7 | One phone number linked to one account, with source and relation | added 2026-04-01 → 2026-06-29 | `phone_id`, `account_id` | Raw | Pack README: used by PS2 | **None** | PS2-owned. **74 `phone_id`s appear across 2–3 accounts** (all `kyc_origination`) — shared-number pattern, not row errors (see shared audit §9) |
| `skip_traces.csv` | 766 × 7 | One skip-trace request and its result (148 found a phone, 27 an address) | 2026-04-13 → 2026-06-29 | `trace_id`, `account_id`, `new_contact_point_id` | Raw | Pack README: used by PS2 | **None** | PS2-owned; `cost_inr` ₹60–150 per trace is a logged cost signal |
| `verified_contact_points.csv` | 250 × 4 | One contact point checked by a verification campaign | single snapshot 2026-07-02 | `phone_id`, `account_id` | Raw (verified sample) | Pack README: used by PS2 | **None** | PS2-owned; 4-way status incl. `third_party_number` 74/250 |

## 4. `ps3_geocoder` — 6 files *(this is the PS3 pack)*

| File | Rows × Cols | What a row is | Temporal | Identifiers | Class | Licence/usage | Relevance to Adjacent | Recommended use |
|---|---|---|---|---|---|---|---|---|
| `towns.csv` | 3 × 4 | One town: name, address style, approx radius (3,800–4,800 m) | static | `town_id` | Raw reference | Pack README: used by PS3 | **None** | PS3 scope; anchors all coordinates |
| `localities.csv` | 36 × 6 | One locality: name, town, pincode, approximate centre | static | `locality_id` (T?-L??), `town_id` | Raw reference | Pack README: used by PS3 | **None** | PS3 scope; 12 per town; **pincodes are synthetic (9xxxxx) and do not resolve to real India** |
| `landmarks_poi.csv` | 240 × 6 | One landmark point: 14 name types (ration shop, bus stop, temple, masjid, church…), town, x, y | static | `poi_id`, `town_id` | Raw reference | Pack README: used by PS3; **the README itself warns it is "incomplete and slightly off"** | **None** | PS3 scope; 198 duplicate (town, name) pairs — usable as weak hints only |
| `baseline_geocodes.csv` | 2,880 × 4 | The **commercial geocoder's** answer per address + its claimed precision | static snapshot | `address_id` | Raw — vendor baseline output | Pack README: used by PS3 ("the baseline to beat") | **None** | PS3 scope; strata: locality 2,052 / street 504 / pincode 274 / rooftop 50; 237 addresses ungeocoded |
| `visit_gps_points.csv` | 160,406 × 6 | One GPS sample inside one field visit's trail (median 26 points/visit; accuracy median 10 m) | 2026-04-01 → 2026-06-29 | `visit_id` (+ `seq`) | Raw — collection telemetry | Pack README: used by PS3 | **None** | PS3 scope; the physical evidence of each visit |
| `surveyed_addresses.csv` | 100 × 3 | One **survey-grade** ground-truth coordinate (the only truth in the pack) | undated | `address_id` | Raw — survey ground truth | Pack README: used by PS3 | **None** | PS3 scope; 100 of 3,117 addresses (3.2%), 0 from `OUT` |

## 5. `shared` — 8 files

| File | Rows × Cols | What a row is | Temporal | Identifiers | Class | Licence/usage | Relevance to Adjacent | Recommended use |
|---|---|---|---|---|---|---|---|---|
| `accounts.csv` | 2,400 × 20 | One loan account: lender, product, DPD band, dues, what the lender knows | `dpd_start` 0–720 days | `account_id`, `lender_id`, `town_id` | Raw | Pack README: all three PS | **None** | Context for PS2/PS3; **never a location feature** |
| `addresses.csv` | 3,117 × 7 | One address on file, as written (mixed script, landmark-based) | added 2026-04-01 → 2026-06-29 | `address_id`, `account_id`, `town_id` | Raw | Pack README: PS2 + PS3 | **None** | The PS3 input text; 2,427 residence / 464 office / 226 permanent_native; 237 `OUT` |
| `agents.csv` | 30 × 6 | One agent: channel, language team, town, tenure, shift | static | `agent_id`, `town_id` | Raw | Pack README: all three PS | **None** | PS3 integrity/monitoring context; `town_id` is N/A for 70% (tele/bot) |
| `dial_attempts.csv` | 51,105 × 16 | One outbound call attempt with outcome, disposition, remark | 2026-04-01 → 2026-06-29 | `attempt_id`, `account_id`, `phone_id`, `agent_id` | Raw | Pack README: **PS1 + PS2 only** | **None** | Owned by PS1/PS2 — not part of PS3 even though it sits in `shared`. Carries `selection_propensity` (1.0/0.5/0.33/0.25) — the pack's only logged randomisation |
| `field_visits.csv` | 5,578 × 15 | One field visit: check-in x/y, dwell, outcome, photo hash | 2026-04-01 → 2026-06-29 | `visit_id`, `account_id`, `address_id`, `agent_id` | Raw | Pack README: PS2 + PS3 | **None** | PS3 evidence layer (and PS2's); 7 outcomes; 1,477 addresses covered (47.4%) |
| `lenders.csv` | 6 × 4 | One lender: name, type, KYC address format | static | `lender_id` | Raw reference | Pack README: all three PS | **None** | Context only |
| `payments.csv` | 2,162 × 5 | One payment received (amount, channel, timestamp) | 2026-04-01 → 2026-07-24 | `payment_id`, `account_id` | Raw | Pack README: **PS1 + PS2 only** | **None** | Not in PS3's file list; usable only as generic outcome context |
| `splits.csv` | 2,400 × 2 | The pack's train/validation/test assignment | static | `account_id` | Raw — **protocol artefact** | Pack README: all three PS | **None** | 1,680 / 360 / 360 accounts; account-level, time-blind |

---

## 6. What the pack says about itself (provenance and usage)

- Pack README, line 1–3: **"CN Synthetic Collections Data — collections data for three problem statements. Everything in it is invented."** → synthetic data; no real persons; safe for internal analysis. `[VERIFIED]`
- The README maps each file to the problem statements. PS3's list, verbatim: `addresses.csv`, `baseline_geocodes.csv`, `field_visits.csv`, `visit_gps_points.csv`, `surveyed_addresses.csv`, `localities.csv`, `landmarks_poi.csv`, `towns.csv`, `accounts.csv`, `agents.csv` — plus `splits.csv` ("All three also use splits.csv"). `[VERIFIED]`
- **No licence, terms of use, DOI or citation file exists in the Drive.** Standing rule we apply: treat as internal competition material, read-only, no redistribution, no external dataset substitution.
- The Drive contains **no PS1/PS2/PS3 problem-statement documents**. The PS statements we hold came through the brief (recorded in our archive); the PS3 statement text is quoted verbatim in `docs/PS3_DATA_REQUIREMENTS.md`.

## 7. Premise check — "Adjacent", Qloo, cinema, Picturehouses

Checks performed on the actual bytes (not on names):

| Check | Result |
|---|---|
| Keyword census over **all 149 column names** (`film, movie, cinema, venue, screen, show, program, audience, ticket, attend, artist, brand, title, imdb, tmdb, wikidata, qloo, genre, release, director, actor`) | **0 matches** |
| Regex scan of **all free-text columns** across the pack for `film|cinema|movie|theatre|song|music|album|actor|hero|qloo` | **0 matches** |
| Any IMDb / TMDB / Wikidata / MusicBrainz / Qloo identifier anywhere | **None** — the only identifiers are internal loan/collections IDs |
| Any venue, theatre or screen entity | **None** — the only place-like entities are towns, localities, landmarks (bus stops, ration shops, temples) |
| Cinema Context / Picturehouses files | **Not present** in the Drive and not present in this workspace |

**Consequence:** an "Adjacent / Qloo" empirical programme **cannot be anchored on this Drive pack**. It holds operational lending/collections data, and its place data is credit-relevant geography, not entertainment geography. This is a finding, not a data-quality complaint: the pack is exactly what it claims to be.

## 8. Verification artefact

`data/drive_verification.csv` — one row per file: drive folder, filename, Drive file ID, bytes, **full SHA-256**, rows, columns, `byte_identical_to_local`, and the local path of the audited copy (11 files in `PS3_SUTRA/data/official_ps3/` — active PS3 workspace; 10 files in `90_Archive/` — the retired sibling workstream, read-only). Full-pack totals: **288,754 rows · 149 columns · 21 files.**

**Provenance note.** This audit was commissioned for a workstream described as "Adjacent/Qloo". The Drive contains no such data (§7). The inventory above records what is actually there and is filed outside `PS3_SUTRA/` so that the PS3-only workspace and its integrity checkers remain untouched.
