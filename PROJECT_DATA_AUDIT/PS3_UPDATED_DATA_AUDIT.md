# PS3 UPDATED DATA AUDIT (v2)

**Scope:** DATASET A = 6 PS3-specific + 6 officially PS3-assigned shared tables · **12 tables · 177,196 rows · 83 columns** · hash-verified against the Drive (12/12).
**Change from v1:** adds the structural audit of **all eight** shared tables (including the two excluded), agent/language integrity tests, town-consistency and multi-address tests, candidate-anchor measurement, per-stratum radius transfer, value/exposure profile, the corrected warm/cold decomposition and the sharpened entity-leakage counts. **Four published figures change (see §14).**
**Artefacts:** `data/derived/updated_*.csv` (16 files), `data/cleaned/*` (3 files).

---

## 1. Inventory (in scope)

| Table | Rows | Cols | Key | Key dups | Full-row dups | Date range |
|---|---|---|---|---|---|---|
| `towns` | 3 | 4 | `town_id` | 0 | 0 | static |
| `localities` | 36 | 6 | `locality_id` | 0 | 0 | static |
| `landmarks_poi` | 240 | 6 | `poi_id` | 0 | 0 | static |
| `baseline_geocodes` | 2,880 | 4 | `address_id` | 0 | 0 | static |
| `visit_gps_points` | 160,406 | 6 | (`visit_id`,`seq`) | n/a | 0 | 2026-04-01 → 06-29 |
| `surveyed_addresses` | 100 | 3 | `address_id` | 0 | 0 | undated |
| `accounts` | 2,400 | 20 | `account_id` | 0 | 0 | `dpd_start` 0–720 d |
| `addresses` | 3,117 | 7 | `address_id` | 0 | 0 | added 2026-04-01 → 06-29 |
| `agents` | 30 | 6 | `agent_id` | 0 | 0 | static |
| `field_visits` | 5,578 | 15 | `visit_id` | 0 | 0 | 2026-04-01 → 06-29 |
| `lenders` | 6 | 4 | `lender_id` | 0 | 0 | static |
| `splits` | 2,400 | 2 | `account_id` | 0 | 0 | static |

**No duplicate keys, no identical rows anywhere in scope.**

## 2. Structural audit — all eight shared tables

| Table | Rows | Key | Join path to a place | Temporal character | Leakage | Verdict |
|---|---|---|---|---|---|---|
| `addresses` | 3,117 | `address_id` ✔ | direct (it *is* the place record) | T0 snapshot + `added_date` | none | IN |
| `field_visits` | 5,578 | `visit_id` ✔ | `address_id` | T3 (post-visit) | central | IN — evidence lanes only |
| `accounts` | 2,400 | `account_id` ✔ | **none** (only via addresses; no coordinate field) | T0 book snapshot | if used as feature | IN — exposure/context |
| `agents` | 30 | `agent_id` ✔ | none (identifies collectors) | static | if used to rank places | IN — monitoring/weights |
| `splits` | 2,400 | `account_id` ✔ | n/a | time-blind | none | IN — evaluation only |
| `lenders` | 6 | `lender_id` ✔ | none | static | none | IN — context only (no signal) |
| `dial_attempts` | 51,105 | `attempt_id` ✔ | **none** (account/phone only) | call-campaign timeline | cross-domain | **OUT** — PS1+PS2 assignment |
| `payments` | 2,162 | `payment_id` ✔ | none | post-outcome (to 2026-07-24) | future leak | **OUT** — PS1+PS2 assignment |

## 3. Missingness (in scope)

`accounts.salary_credit_day` 68.2% (not applicable) · `accounts.ability_to_pay_estimate` 30.3% (genuinely unknown) · `agents.town_id` 70.0% (not applicable — tele/bot) · `agents.tenure_months` 3.3% · `field_visits.ptp_id` 89.2% (structural; excluded field). Everything else 0%. **No imputation anywhere.**

## 4. Duplicates / entity structure (definition-aware)

| Definition | Result | Reading |
|---|---|---|
| Identity key (trailing `- <6 digits>` kept) | **5 groups / 10 rows** | true text collisions, 5 account pairs |
| Render key (token stripped) | **70 groups / 203 rows** (193 differ only by the trailing token; 184 `permanent_native`) | template families — **never merged** |
| Near-duplicate pairs (token-set J ≥ 0.80) | 161, all cross-account, all different trailing tokens (char-3-gram measure: 238) | same template, different house |

## 5. Foreign keys & coverage

0 orphans everywhere; the single exception is the deliberate marker `addresses.town_id='OUT'` (237). Coverage: accounts→≥1 address 2,400/2,400 · addresses→≥1 visit 1,477/3,117 (47.4%) · addresses→vendor pin 2,880/3,117 (92.4%) · addresses→survey truth 100 (3.2%) · visits→GPS trail 5,578/5,578.

## 6. Temporal

Window 2026-04-01 → 06-29; 77 visit dates; `added_date`→first visit median 14 d (p90 66). Repeats: 1,071 addresses visited >1×; **73.5% of visits are repeats**; 577 addresses never confirm, absorbing 1,650 visits (29.6%).

## 7. Coordinates & geometry

Local planar metres (±~4 km per town; not lat/lon). Check-in accuracy median 9.8 m. Check-in ↔ nearest own-trail point: median 7.6 m, max 90.8 m, **0 visits >100 m** (the retracted "645 >500 m" figure measured to the trail centroid). 160,406 trail points; 3.13% non-positive Δt.

## 8. Agent diagnostics — `agents.csv` as integrity/exposure material (new)

| Agent | Team | Tenure | Visits | met | not-traceable | Median dwell | Repeat-hash visits | Share of check-ins 10:00–12:59 |
|---|---|---|---|---|---|---|---|---|
| FA008 | hinglish | 38 m | 611 | 38.0% | **29.1%** | 187 s | 4 | 83.8% |
| FA007 | kanglish | 37 m | 626 | 41.7% | 28.0% | 212.5 s | 0 | 79.7% |
| FA002 | kanglish | 52 m | 633 | 39.5% | 27.5% | 197 s | 4 | 80.6% |
| FA001 | english | 29 m | 628 | 40.6% | 26.3% | 206 s | 0 | 81.2% |
| **FA009** | english | 6 m | 610 | 36.2% | 25.9% | 184 s | **162** | 84.9% |
| FA006 | hinglish | 64 m | 583 | 41.2% | 24.4% | 220 s | 0 | 88.7% |
| FA003 | kanglish | 4 m | 645 | 45.9% | 22.9% | 223 s | 0 | 79.5% |
| FA004 | hinglish | 3 m | 636 | 41.0% | 22.3% | 221 s | 0 | 86.0% |
| FA005 | hinglish | 16 m | 606 | 41.6% | **19.5%** | 220.5 s | 2 | 84.2% |

**Readings:** (i) outcome spread across agents is modest (met 36.2–45.9%; not-traceable 19.5–29.1%) but real → evidence weighting by collector is justified; (ii) **media duplication is the only confirmed anomaly** (FA009 162/610; next highest 4); (iii) tenure↔met correlation **−0.16 (nil)**; (iv) `shift` is single-valued (`day`) → zero information; (v) the 10:00–12:59 concentration (79.5–88.7%) is a **schedule artefact affecting every agent**, not an FA009 anomaly (published claim retracted); (vi) agent↔borrower language match does not help: matched 38.7% met vs unmatched 40.8% (n=331).

## 9. Town consistency & the `OUT` class (new)

`address.town_id` vs `account.town_id`: **0 mismatches** across 3,117 rows (excluding `OUT`). **But the account town cannot rescue `OUT` addresses:** all 237 `OUT` rows carry real account towns (T1 75, T2 77, T3 85) yet 226 of them are `permanent_native` **native-village** records — the account's town is the operating town, not the address location. And all 237 have **no vendor pin and no visit** (0/237). They are a structurally unserved class, not a data error.

## 10. Multi-address accounts (new)

Of the accounts with ≥2 addresses that each produced a met-someone visit (38 pairs): median separation **3,011.6 m**, p90 5,325.4 m, **0% within 100 m**. Reading: an account's addresses are *different places* (home/office; or home vs native village). **Rule: never merge addresses on account identity.**

## 11. Candidate-generation anchors (new)

Of 2,326 coarse-pinned addresses (locality or pincode strata): **2,249 (96.7%)** have a street/rooftop pin of *another* address within 300 m; median distance to the nearest such anchor **96 m**. → Finer local anchors exist for almost every coarse case (a legitimate candidate-generation input).

## 12. Radius calibration & transfer (new; fit on train truths, reported on val+test)

| Stratum | n (train / eval) | train p50 | train p80 | train p90 | eval coverage at train-p80 |
|---|---|---|---|---|---|
| locality | 73 (49 / 24) | 400.3 m | 539.9 m | 630.6 m | **79.2%** |
| street | 16 (11 / 5) | 116.1 m | 162.1 m | 170.5 m | 100% (n=5) |
| pincode | 10 (6 / 4) | 925.5 m | 1,204.2 m | 1,703.0 m | **0% (n=4)** |
| rooftop | 1 (0 / 1) | — | — | — | — |

**Reading:** the locality-stratum radius transfers (≈80% empirical coverage at nominal p80); the pincode radius does **not** transfer — and with n=10 total the honest statement is "no pincode radius can be published yet". Street/rooftop have too few truths to fit. **The radius table must be published with per-stratum n and its failures.**

## 13. Value / exposure & replay (new)

- **Value is orthogonal to visit success:** met rate by outstanding quintile 43.1 / 38.5 / 41.6 / 38.2 / 41.8%; median outstanding met vs not-met ratio **0.99**.
- **Corrected warm/cold decomposition** (2026-05-15 cut): post-cut visits 2,726 → warm (address confirmed pre-cut) **56.0% met (n=1,383)** vs cold **24.5% (n=1,343)**; overall 40.5%. Val+test only: **56.7% vs 25.1%**. (v1 published "56.0% vs 40.5% for all other post-cut visits" — 40.5% was the overall rate.)
- **Memory consistency:** 563 addresses with ≥2 met visits; median pairwise distance **77.7 m same-agent vs 75.8 m different-agent** → agent-independent.

## 14. Changed numbers register (v1 → v2)

| Figure | v1 | v2 | Cause |
|---|---|---|---|
| Warm/cold post-cut | "56.0% vs 40.5% (other post-cut)" | **56.0% warm vs 24.5% cold**; overall 40.5% | mislabel in v1; finding strengthened |
| Memory consistency | 90.0 / 98.0 m | **77.7 / 75.8 m** (median of per-address medians) | definition stated |
| FA009 time-window anomaly | "83% of check-ins 10:00–13:00" | **retracted** — every agent 79.5–88.7% | schedule artefact |
| Multi-account places | "5 text groups, at minimum" | **81 co-located clusters / 191 addresses** + same-account addresses far apart (3,011.6 m) | new measurements |
| Entity leakage | not quantified | 1/459 identity-text overlap; **124/344 (36.0%) met test addresses within 30 m of train evidence** | new measurement |
| Everything else (counts, keys, nulls, duplicates, FK, coverage, geometry, outcomes, selection) | — | re-derived, unchanged | re-verification |

## 15. Runtime & provenance

Re-audit pass: **1.7 s / 226 MB peak**; cleaning 0.15 s; this pass's additional battery <1 s. Drives re-verified **21/21** at the start of this pass. Raw Drive unmodified; nothing outside the official pack was read for any number in this document.
