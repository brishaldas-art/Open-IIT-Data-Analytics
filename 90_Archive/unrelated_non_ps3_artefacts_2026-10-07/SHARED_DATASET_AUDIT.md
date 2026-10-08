# SHARED DATASET AUDIT

**Scope:** the 8 files in the Drive folder `shared` — `accounts`, `addresses`, `agents`, `dial_attempts`, `field_visits`, `lenders`, `payments`, `splits`.
**Totals:** 66,798 rows · 75 columns · all CSV · all byte-identical to the Drive copies (see `docs/DRIVE_DATA_INVENTORY.md` §8).
**Method:** every figure below is computed from the files themselves; referential integrity was checked against the other 13 files in the pack.

---

## 1. The entity model

```
lenders (6) ──< accounts (2,400) ──< addresses (3,117) ──< field_visits (5,578) ──< visit_gps_points (160,406)
                   │  ├──< phones (5,719) ──< dial_attempts (51,105)
                   │  ├──< payments (2,162)
                   │  ├──< ptps (3,696) ──< post_call_events (8,466)
                   │  └──   splits (1:1, train/val/test)
agents (30) ──< field_visits, dial_attempts
towns (3) ──< accounts, addresses, agents(field only), localities (36) ── landmarks (240)
```

**What each row is:** `accounts` — one loan account. `addresses` — one address on file for an account, as written. `agents` — one collections agent (20 tele, 9 field, 1 voice bot). `dial_attempts` — one outbound call attempt. `field_visits` — one field visit to one address. `lenders` — one lender. `payments` — one payment received. `splits` — the split assignment of one account.

## 2. Referential integrity — checked, not assumed

Every foreign key resolves with **zero orphans** except one expected case: `addresses.town_id` contains the literal value `OUT` for 237 rows, which is not a town (it means "outside the three modelled towns").
`addresses→accounts` 0 orphans · `field_visits→addresses` 0 · `field_visits→agents` 0 · `visit_gps_points→field_visits` 0 · `dial_attempts→{accounts,phones,agents}` 0 · `ptps→{accounts,visits,attempts}` 0 · `payments→accounts` 0 · `skip_traces→accounts` 0 · `verified_contact_points→{accounts,phones}` 0 · `post_call_events→ptps` 0 · `splits→accounts` exactly 2,400. `[DATA]`

**Coverage:** all 2,400 accounts have ≥1 address; 1,339 have ≥1 visit; 1,667 have ≥1 payment; 2,368 have ≥1 dial attempt. 1,477 of 3,117 addresses (47.4%) have ≥1 visit; 2,880 (92.4%) have a vendor pin. `[DATA]`

## 3. The cinema checklist — the critical question (§7 of the brief)

| Asked | Answer from the actual data |
|---|---|
| Real cinema venues | **No.** No venue table, no venue field, no venue ID. Place entities are towns, localities and 14 types of landmark — none is a cinema. |
| Modern programming | **No.** No programme, screening, showtime or run field anywhere. |
| Historical/current programme records | **No.** The only dated records are calls, visits, promises, payments and traces. |
| Audience signals | **No.** No audience, attendee, viewer or household-preference field. |
| Attendance | **No.** No attendance or footfall column. |
| Demand proxies | **Only non-cinema demand:** loan delinquency, PTP amounts, payments received, dial answering. None measures entertainment demand. |
| Ticketing | **No** ticketing, booking, seat, price or capacity field. |
| Availability | **No** schedule or availability field. |
| Geographic context | **Yes — but credit geography:** 3 synthetic towns, 36 localities with pincodes, 240 landmarks, visit coordinates. No cinema-relevant geography. |
| Programme outcomes | **No.** The only "outcomes" are visit outcomes (7 classes) and call dispositions (16 classes). |

Evidence: keyword census over all 149 columns = **0 matches**; free-text scan over all text columns = **0 matches** (inventory §7).

## 4. Dates and temporal coverage

| File | Column | Range |
|---|---|---|
| `addresses` | `added_date` | 2026-04-01 → 2026-06-29 |
| `phones` | `added_date` | 2026-04-01 → 2026-06-29 |
| `dial_attempts` | `attempt_ts` | 2026-04-01 08:01 → 2026-06-29 18:54 |
| `field_visits` | `visit_date` | 2026-04-01 → 2026-06-29 |
| `payments` | `payment_ts` | 2026-04-01 → **2026-07-24** |
| `ptps` | `captured_ts` / `promised_date` | 2026-04-01 → 06-29 / promises to **07-24** |

**Historical or current?** A single **synthetic 90-day snapshot** (plus a payment tail to 24 July). There is no multi-year history, no version field, no update log: the pack *is* one frozen window. `[DATA]`

## 5. Outcomes present (and absent)

- `field_visits.outcome` — 7 classes: `address_not_traceable` 1,400 · `locked_premises` 1,249 · `met_borrower` 1,114 · `met_family` 1,062 · `neighbour_says_shifted` 455 · `no_such_person` 206 · `cash_collected` 92. Plus `dwell_s` and `photo_hash`.
- `dial_attempts.disposition` — 16 classes (top: `no_answer` 24,591 · `call_rejected` 5,409 · `not_reachable` 4,354 · `third_party_contact` 3,537 · `rpc_ptp` 2,937) and `network_response` 6 classes.
- `payments` — 2,162 events, ₹50–₹438,000 across 7 channels. `ptps` — 3,696 promises. `skip_traces.result` — 3 classes. `verified_contact_points.verified_status` — 5 classes.
- **Absent:** attendance, ticket sales, box office, programme outcomes, satisfaction, or any non-collections outcome.

## 6. Geographic fields

`town_id` (T1/T2/T3/`OUT`); locality and pincode exist **only as text inside `address_text`** — there is no locality or pincode column on `addresses`; visit check-in coordinates (5,578 distinct points); trail coordinates (160,406). Reference geometry: town centres/radii, locality centroids, landmark points. **Coordinate system: local planar metres, roughly ±4 km about each town — not lat/lon.** `[DATA]`

## 7. Identifiers (all of them)

`account_id` · `address_id` · `agent_id` · `visit_id` · `attempt_id` · `phone_id` · `ptp_id` · `payment_id` · `trace_id` · `lender_id` · `town_id` · `locality_id` · `poi_id` · `call_id`. All are **internal loan/collections identifiers**. `phone_masked` (e.g. masked 10-digit strings) is the only quasi-external key, and it is masked. **No external identifier of any kind (IMDb / TMDB / Wikidata / MusicBrainz / Qloo) exists anywhere in the pack.** `[DATA]`

## 8. Missingness profile (shared tables only; classify, then decide)

| Field | Null % | Class | Decision |
|---|---|---|---|
| `accounts.salary_credit_day` | 68.2% | **Not applicable** (only salaried products have a credit day) | Leave null; add indicator if used; never impute |
| `accounts.ability_to_pay_estimate` | 30.3% | **Genuinely unknown** (lender didn't record) | Leave null; missingness itself is a signal |
| `agents.town_id` | 70.0% | **Not applicable** (tele/bot agents are not town-bound) | Leave null; exclude those agents from town-level analyses rather than assigning a town |
| `agents.tenure_months` | 3.3% | Genuinely unknown | Leave null |
| `dial_attempts.ptp_id` | 94.0% | **Structurally missing** (set only when a PTP was created) | Leave null; `disposition` already says what happened |
| `field_visits.ptp_id` | 89.2% | Structurally missing | Leave null |
| `ptps.attempt_id` / `ptps.visit_id` | 16.4% / 83.6% | **Structural pair** (a PTP comes from exactly one of call/visit) | Leave both; use `source` |
| `skip_traces.new_contact_point_id` | 77.2% | Structurally missing (only when something was found) | Leave null |
| everything else in the 8 files | 0% | — | — |

**Rule applied:** never fill every null. No field in the shared dataset should be imputed for modelling without a stated reason; three of the nine are *not applicable*, not missing.

## 9. Duplicate structure (classify each kind)

| Kind | Found | Classification |
|---|---|---|
| Duplicate primary keys | **0** in all 8 files | None |
| Identical full rows | **0** in all 8 files | None |
| Multiple observations per entity | `visit_gps_points` 26/visit median; `call_transcripts` 11.6 turns/call; `post_call_events` 2.6/PTP; `field_visits` 3.78/address; `dial_attempts` 21.6/account; `payments` 1.3/account; `addresses` 1.30/account | **Legitimate repeated entity / multiple observations** — not errors |
| Repeated visits to one address | 1,071 addresses visited >1×; 4,101 of 5,578 visits are repeats (73.5%) | Legitimate observation; a *targeting* signal |
| `phones.phone_id` appearing under >1 account | 74 ids · 175 rows · 2–3 accounts each · all `kyc_origination` · no identical attribute rows | **Shared contact point** (one number, several borrowers) — legitimate pattern, needs an ownership rule; not a data error |
| Same address text near-duplicates | 238 pairs with Jaccard ≥0.80 — but 228 of them are *different houses with the same template* | **Legitimate repeated entity** (template reuse), not duplication |
| The one media anomaly | FA009 carries a repeated photo hash on 162 of 610 visits (26.6%) vs ≤0.3% for every other agent | **Integrity anomaly** (process evidence), owned by the visit-evidence layer — not a duplicate row |

## 10. Suitability verdict

- **Programme-level analysis: NOT suitable.** There are no programmes. This is definitional, not a quality judgement.
- Suitable for: collections-outcome modelling; contactability and skip-trace; address-location evidence and hierarchy work (PS3); targeting/prioritisation; cost and effort analysis.
- **Venue coverage: zero venues. Audience coverage: zero audience fields.** The word "venue" does not appear in any column name or in any text column.

**Provenance note.** This audit was commissioned under an "Adjacent/Qloo" framing; §3 answers that framing directly and negatively. The table is recorded as-is so that no downstream document can quietly treat this pack as entertainment data.
