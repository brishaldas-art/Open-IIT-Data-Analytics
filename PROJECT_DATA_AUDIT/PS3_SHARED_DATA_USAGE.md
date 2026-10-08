# PS3 SHARED DATA USAGE (v2)

**Question this document answers:** for each of the eight tables in the Drive's `shared/` folder — why is it (or isn't it) relevant to PS3, how would it join, what is its cardinality and temporal character, what leakage does it carry, may it be used at training time, at inference time, for evaluation — and does it change candidate generation, ranking, uncertainty, integrity weighting, field-visit learning or business/value analysis?

**Eight role classes** (one per column, no column gets two): **model feature · candidate-generation input · field-evidence input · integrity feature · exposure-propensity variable · evaluation-only · business-value context · excluded** (plus an explicit `key (not a feature)` tag for identifiers).
**Availability stages:** **T0** when the address/query first arrives · **T1** during candidate generation/resolution · **T2** before a field visit · **T3** during/after a visit · **T4** future/post-outcome.
The complete 75-column classification is in §8; the machine-readable version is `data/derived/updated_shared_column_map.csv`.

---

## 1. Headline: 75 shared columns, 9 usable facts

| Role class | Columns | Which ones |
|---|---|---|
| Model feature | **1** | `addresses.address_text` |
| Candidate-generation input | **1** | `addresses.town_id` |
| Field-evidence input | **7** | `field_visits.{checkin_ts, checkin_x, checkin_y, gps_accuracy_m, dwell_s, outcome, remark}` |
| Integrity feature | **7** | `agents.{agent_id, channel, town_id, tenure_months}` + `field_visits.{agent_id, start_ts, photo_hash}` |
| Exposure-propensity variable | **7** | `accounts.{portfolio, income_type, preferred_language, bucket_start, dpd_start}` + `addresses.address_type` + `agents.language_team` |
| Evaluation-only | **3** | `addresses.added_date`, `field_visits.visit_date`, `splits.split` |
| Business-value context | **10** | `accounts.{lender_id, town_id, emi_amount, overdue_start, outstanding}` + `addresses.source` + all 4 `lenders.*` |
| Excluded | **32** | 9 volatile/sensitive `accounts.*` (incl. the three cross-domain `prev_ptp_*`/`dialling_arm`) · `agents.shift` · `field_visits.ptp_id` · all 16 `dial_attempts.*` · all 5 `payments.*` |
| Keys (not features) | 7 | account/address/visit/split identifiers |

**The compliance statement the brief asks for: of 75 shared columns, exactly 1 is a model feature, and 32 are excluded.** Nothing was turned into a feature because it existed.

---

## 2. Per-table audit — all eight shared tables, ten dimensions each

### 2.1 `addresses.csv` — class **A (REQUIRED)**
- **Why PS3-relevant:** named in the PS3 file list; it *is* the query.
- **Join keys:** `address_id` (unique) → `field_visits`, `baseline_geocodes`, `surveyed_addresses`; `account_id` → `accounts`, `splits`; `town_id` → `towns`.
- **Cardinality:** 3,117 rows; 2,400 accounts → 1,694 accounts have 1 address, 695 have 2, 11 have 3.
- **Temporal:** `added_date` 2026-04-01 → 06-29; median 14 d to first visit (p90 66).
- **Leakage:** none by itself (T0). Roles `address_type`/`source` are exposure/context; using them as location features would import targeting.
- **Inference:** yes (text, town). **Training:** yes (text features). **Evaluation:** n/a.
- **Changes:** candidate generation (town), address/entity resolution (via text keys + place clusters), normalisation (input), business analysis (visit coverage by type).

### 2.2 `field_visits.csv` — class **A (REQUIRED)**
- **Why:** the statement's "learns from field visits" has no other source.
- **Join keys:** `visit_id` (unique) → `visit_gps_points`; `address_id` → `addresses`; `account_id` → `accounts`, `splits`; `agent_id` → `agents`.
- **Cardinality:** 5,578 visits over 1,477 addresses and 1,339 accounts; 9 field agents, 583–645 visits each.
- **Temporal:** visit dates 2026-04-01 → 06-29; every row is post-visit.
- **Leakage:** the central one — check-in coordinates, outcome and remark are **T3**. Usable for *later* decisions only; a visit may never inform its own prediction, and `address_not_traceable` may never become a negative location label.
- **Inference:** at T2 the app carries only earlier-visit memory; at T3 the visit appends evidence. **Training:** yes, eligibility-gated (dwell ≥180 s etc.). **Evaluation:** yes — the outcome is the learning loop's own metric.
- **Changes:** field-visit learning (core), evidence weighting (accuracy/dwell/media), integrity (photo hash; per-agent `not_traceable` spread 19.5–29.1%), uncertainty (check-in dispersion), business analysis (yield, repeats, warm/cold).

### 2.3 `accounts.csv` — class **E (EXPOSURE / SAMPLING VARIABLE)**
- **Why PS3-relevant:** assigned to all three PS; explains *who is visited* — necessary to keep any PS3 claim honest — and carries the value side for prioritisation.
- **Join keys:** `account_id` → `addresses`, `field_visits`, `splits`; `lender_id` → `lenders`; `town_id` → `towns` (consistency only).
- **Cardinality:** 2,400 × 20; 6 lenders, 6 portfolios, 3 towns; `dpd_start` 0–720.
- **Temporal:** T0 book snapshot plus evolving dues fields; no versioning.
- **Leakage:** high if used as features — delinquency predicts visits, not places.
- **Inference:** only as prioritisation context at the decision layer. **Training:** **no**. **Evaluation:** no.
- **Changes:** none to location machinery; **exposure modelling is mandatory**, and two measurements reshape the value story: yield is flat across DPD bands (37.5–42.9%) and across outstanding quintiles (Q1 43.1% → Q5 41.8%; met/not-met median ratio 0.99).

### 2.4 `agents.csv` — class **B (USEFUL)**
- **Why:** assigned to all three PS; identifies the collector whose observations carry the evidence.
- **Join keys:** `agent_id` → `field_visits`.
- **Cardinality:** 30 rows (20 tele, 9 field, 1 voice_bot); only the 9 field agents appear in visits; `town_id` N/A for 70%, 100% present for field agents.
- **Temporal:** static attributes (tenure months, shift).
- **Leakage:** agent attributes must never rank locations (that models the collector); use only as weights/monitoring.
- **Inference:** as weight metadata. **Training:** as sample weights (media-integrity, monitoring). **Evaluation:** diagnostics.
- **Changes:** integrity weighting (media duplication — FA009 162/610, every other agent ≤4), monitoring. Measured nulls: `tenure_months`↔met r=−0.16; `shift` single value; `language_team` match gives no benefit (38.7% vs 40.8%).

### 2.5 `splits.csv` — class **C (EVALUATION-ONLY)**
- **Why:** "All three also use splits.csv"; it is the official evaluation protocol.
- **Join keys:** `account_id` → `accounts`.
- **Cardinality:** 2,400 → train 1,680 / validation 360 / test 360; 1:1 with accounts.
- **Temporal:** time-blind (no date logic).
- **Leakage:** not a leak itself, but **account-level only**: 1 test address shares identical identity text with train, and **124/344 (36.0%) test addresses with a met visit sit within 30 m of a train met check-in**.
- **Inference:** no. **Training:** no. **Evaluation:** the partition itself.
- **Changes:** addresses the evaluation protocol; **add** (do not replace) an entity/time-aware split ledger for address-level claims.

### 2.6 `lenders.csv` — class **D (CONTEXT ONLY)**
- **Why:** assigned to PS3 in the pack README; `kyc_address_format` was a plausible style prior.
- **Join keys:** `lender_id` → `accounts`.
- **Cardinality:** 6 rows.
- **Temporal:** static.
- **Leakage:** none. **Inference:** no. **Training:** no. **Evaluation:** no.
- **Changes:** **none — measured**: address style by format varies ≤1.4 points on every statistic (non-ASCII 8.0/9.3/7.9%; trailing pincode 93.5/92.7/93.8%; house marker 46.8/46.8/46.3%). Retained for provenance only. *Documented exclusion-by-measurement, as the brief requires.*

### 2.7 `dial_attempts.csv` — class **G (SHOULD NOT BE USED)**
- **Why not:** officially assigned **PS1+PS2**; 15 of 16 columns are telephony/contact semantics; carries a PS2 experiment artefact (`selection_propensity`).
- **Join keys:** `account_id`, `phone_id`, `agent_id`, `attempt_id` — none reaches an address directly.
- **Cardinality:** 51,105 rows; 2,368 accounts.
- **Temporal:** call-campaign timeline (2026-04-01 → 06-29), independent of visit ordering.
- **Leakage:** yes — contact outcomes are not location information and would cross-contaminate the target.
- **Inference / training / evaluation:** none. **Changes:** none. **No PS3 artefact reads it.**

### 2.8 `payments.csv` — class **G (SHOULD NOT BE USED)**
- **Why not:** officially assigned **PS1+PS2**; every row is a post-outcome financial event (payments run to 2026-07-24, past the visit window).
- **Join keys:** `account_id` only.
- **Cardinality:** 2,162 rows; 1,667 accounts.
- **Temporal:** T4 by construction.
- **Leakage:** classifying — a future outcome that would leak into any earlier prediction.
- **Inference / training / evaluation:** none. **Changes:** none. **No PS3 artefact reads it.**

---

## 3. What exclusion costs — stated, not hidden

Excluding `dial_attempts` and `payments` means PS3 has **no financial outcome variable** and **no contact-attempt history**. Both were checked against the PS3 statement: it asks for a location, a radius and landmark directions, learned from successful visits. Neither table contributes to that object; both would dilute it. The cost is recorded here so the trade-off is a decision, not an oversight.

## 4. The six things shared data actually changed (and three it did not)

| Changed | Evidence |
|---|---|
| Exposure discipline | DPD/portfolio targeting vs flat yield |
| Integrity weighting | media duplication (FA009 162/610); per-agent `not_traceable` 19.5–29.1% |
| Entity resolution | 81 place clusters across accounts; **same account ≠ same place** (median 3,011.6 m between an account's two met addresses) |
| Address memory | split-aware warm/cold: 56.7% vs 25.1% (val+test) |
| Evaluation honesty | split composition 66/19/15; 36.0% place-proximity leakage |
| Prioritisation framing | value × confirmability, no cost claims |

| Not changed (measured, documented) | Why |
|---|---|
| Lender/format features | no signal |
| Agent-trait features (tenure/language/shift) | no signal / no variance |
| Book fields as location features | wrong variable class + leakage |

## 5. Join-key reference

| From | To | Key | Cardinality | Guard |
|---|---|---|---|---|
| addresses | accounts | `account_id` | N:1 | 0 orphans |
| addresses | towns | `town_id` | N:1 | 237 `OUT` |
| field_visits | addresses / accounts / agents | `address_id` / `account_id` / `agent_id` | N:1 | 0 orphans |
| visit_gps_points | field_visits | `visit_id` | N:1 | 0 orphans |
| baseline_geocodes / surveyed_addresses | addresses | `address_id` | 1:1 / 1:1 | 2,880 / 100 |
| splits | accounts | `account_id` | 1:1 | 2,400 exact |
| lenders | accounts | `lender_id` | 1:N | 0 orphans |

## 6. Field-level classification — the important columns (summary)

| Column | Stage | Role | One-line reason |
|---|---|---|---|
| `addresses.address_text` | T0 | model feature | the input |
| `addresses.town_id` | T0 | candidate-generation input | constrains the candidate set |
| `addresses.address_type` | T0 | exposure variable | residence 54.5% visited vs office 33.4% vs native 0% |
| `addresses.source` | T0 | business-value context | provenance label only |
| `addresses.added_date` | T0 | evaluation-only | time axis |
| `accounts.dpd_start`, `bucket_start`, `portfolio`, `income_type`, `preferred_language` | T0 | exposure variables | explain targeting; never features |
| `accounts.outstanding`, `emi_amount`, `overdue_start`, `lender_id`, `town_id` | T0 | business-value context | value side + consistency check |
| `agents.agent_id`, `channel`, `town_id`, `tenure_months` | T2 | integrity features | monitoring / weights |
| `agents.language_team` | T2 | exposure variable | no benefit measured |
| `agents.shift` | T2 | excluded | single value |
| `field_visits.checkin_*`, `gps_accuracy_m`, `dwell_s`, `outcome`, `remark` | T3 | field-evidence input | future decisions only |
| `field_visits.agent_id`, `start_ts`, `photo_hash` | T2/T3 | integrity features | who/when/media |
| `splits.split` | T0 | evaluation-only | official partition |

## 7. Compliance

- **No shared column is a feature unless it is T0 and location-bearing** — exactly one qualifies (`address_text`).
- **No post-outcome column (T3/T4) is used for cold-start prediction**; warm lanes use *earlier* visits only.
- **No PS1 file, no PS2-only file and no PS1/PS2-derived field** appears in any PS3 artefact.
- The eight role classes and the T0–T4 stages are the *only* vocabularies used to justify inclusion.

---

## 8. Appendix — full 75-column classification of the shared folder

| Table | Column | Stage | Role | Note |
|---|---|---|---|---|
| `accounts` | `account_id` | T0 | key (not a feature) | grouping key |
| `accounts` | `lender_id` | T0 | business-value context | registry link; no address information |
| `accounts` | `portfolio` | T0 | exposure-propensity variable | which books get visited (met 38.2–47.6%) |
| `accounts` | `income_type` | T0 | exposure-propensity variable | targeting segment |
| `accounts` | `town_id` | T0 | business-value context | consistency check only: 0 mismatches vs addresses.town_id; does NOT locate OUT addresses (account town = operating town; 226/237 OUT rows are native-village records) |
| `accounts` | `preferred_language` | T0 | exposure-propensity variable | language-match test: matched 38.7% met vs unmatched 40.8% (n=331) → no usable signal |
| `accounts` | `bucket_start` | T0 | exposure-propensity variable | delinquency bucket |
| `accounts` | `dpd_start` | T0 | exposure-propensity variable | exposure rises with DPD; yield flat (37.5–42.9%) |
| `accounts` | `emi_amount` | T0 | business-value context | value side; not a location feature |
| `accounts` | `overdue_start` | T0 | business-value context | value side |
| `accounts` | `outstanding` | T0 | business-value context | value side; met/not-met median ratio 0.99 |
| `accounts` | `salary_credit_day` | T0 | excluded | 68.2% N/A; retention-sensitive |
| `accounts` | `bureau_score_band` | T0 | excluded | not location; fairness-sensitive |
| `accounts` | `other_active_loans` | T0 | excluded | not location |
| `accounts` | `paid_other_lenders_30d` | T0 | excluded | not location |
| `accounts` | `last_bounce_reason` | T0 | excluded | not location |
| `accounts` | `ability_to_pay_estimate` | T0 | excluded | 30.3% missing; not location |
| `accounts` | `prev_ptp_count` | T0 | excluded | cross-domain (PS1/PS2 promise history) |
| `accounts` | `prev_ptp_broken` | T0 | excluded | cross-domain (PS1/PS2 promise history) |
| `accounts` | `dialling_arm` | T0 | excluded | PS2 experiment artefact |
| `addresses` | `address_id` | T0 | key (not a feature) | record key, not a place identity (191 addresses share 81 places) |
| `addresses` | `account_id` | T0 | key (not a feature) | grouping key; splits run on it |
| `addresses` | `address_text` | T0 | model feature | the only feature the geocoder consumes |
| `addresses` | `address_type` | T0 | exposure-propensity variable | residence 54.5% visited · office 33.4% · permanent_native 0% |
| `addresses` | `source` | T0 | business-value context | provenance (kyc_origination 3,090 / skip_trace 27); 27 rows name a PS2 process — label only, no PS2 payload |
| `addresses` | `added_date` | T0 | evaluation-only | time axis (lag to first visit, median 14 d) |
| `addresses` | `town_id` | T0 | candidate-generation input | constrains candidates; 237 OUT → no candidates |
| `agents` | `agent_id` | T2 | integrity feature | collector grouping; evidence weights by agent |
| `agents` | `channel` | T2 | integrity feature | only 'field' appears in visits (9 agents) |
| `agents` | `language_team` | T2 | exposure-propensity variable | no benefit measured (matched 38.7% vs 40.8%); monitoring only |
| `agents` | `town_id` | T2 | integrity feature | 100% present for field agents; beat sanity checks |
| `agents` | `tenure_months` | T2 | integrity feature | tenure↔met r=−0.16 (nil); monitoring only |
| `agents` | `shift` | T2 | excluded | single value 'day' → zero variance |
| `dial_attempts` | `attempt_id` | — | excluded | PS1+PS2-assigned; call timeline, not visit timeline; no PS3 artefact reads it |
| `dial_attempts` | `account_id` | — | excluded | PS1+PS2-assigned; call timeline, not visit timeline; no PS3 artefact reads it |
| `dial_attempts` | `phone_id` | — | excluded | PS1+PS2-assigned; call timeline, not visit timeline; no PS3 artefact reads it |
| `dial_attempts` | `attempt_ts` | — | excluded | PS1+PS2-assigned; call timeline, not visit timeline; no PS3 artefact reads it |
| `dial_attempts` | `channel` | — | excluded | PS1+PS2-assigned; call timeline, not visit timeline; no PS3 artefact reads it |
| `dial_attempts` | `agent_id` | — | excluded | PS1+PS2-assigned; call timeline, not visit timeline; no PS3 artefact reads it |
| `dial_attempts` | `dialling_arm` | — | excluded | PS1+PS2-assigned; call timeline, not visit timeline; no PS3 artefact reads it |
| `dial_attempts` | `selection_propensity` | — | excluded | PS1+PS2-assigned; call timeline, not visit timeline; no PS3 artefact reads it |
| `dial_attempts` | `network_response` | — | excluded | PS1+PS2-assigned; call timeline, not visit timeline; no PS3 artefact reads it |
| `dial_attempts` | `ring_duration_s` | — | excluded | PS1+PS2-assigned; call timeline, not visit timeline; no PS3 artefact reads it |
| `dial_attempts` | `talk_duration_s` | — | excluded | PS1+PS2-assigned; call timeline, not visit timeline; no PS3 artefact reads it |
| `dial_attempts` | `hangup_by` | — | excluded | PS1+PS2-assigned; call timeline, not visit timeline; no PS3 artefact reads it |
| `dial_attempts` | `disposition` | — | excluded | PS1+PS2-assigned; call timeline, not visit timeline; no PS3 artefact reads it |
| `dial_attempts` | `remark` | — | excluded | PS1+PS2-assigned; call timeline, not visit timeline; no PS3 artefact reads it |
| `dial_attempts` | `ptp_id` | — | excluded | PS1+PS2-assigned; call timeline, not visit timeline; no PS3 artefact reads it |
| `dial_attempts` | `has_transcript` | — | excluded | PS1+PS2-assigned; call timeline, not visit timeline; no PS3 artefact reads it |
| `field_visits` | `visit_id` | T3 | key (not a feature) | evidence record key |
| `field_visits` | `account_id` | T0 | key (not a feature) | grouping key |
| `field_visits` | `address_id` | T0 | key (not a feature) | evidence-to-place binding |
| `field_visits` | `agent_id` | T2 | integrity feature | who collected; used for weights & diagnostics |
| `field_visits` | `visit_date` | T2 | evaluation-only | scheduling/time axis; split-aware replay |
| `field_visits` | `start_ts` | T3 | integrity feature | timing plausibility (all agents 79.5–88.7% of check-ins 10:00–12:59 — schedule artefact) |
| `field_visits` | `checkin_ts` | T3 | field-evidence input | evidence timestamp |
| `field_visits` | `checkin_x` | T3 | field-evidence input | location evidence for FUTURE decisions only |
| `field_visits` | `checkin_y` | T3 | field-evidence input | location evidence for FUTURE decisions only |
| `field_visits` | `gps_accuracy_m` | T3 | field-evidence input | quality weight (median 9.8 m) |
| `field_visits` | `dwell_s` | T3 | field-evidence input | weight (median 207 s); dwell↔outcome link is a synthetic artefact |
| `field_visits` | `outcome` | T3 | field-evidence input | the learning signal; address_not_traceable never a negative label |
| `field_visits` | `ptp_id` | T3 | excluded | 89.2% null; cross-domain (PS1) |
| `field_visits` | `remark` | T3 | field-evidence input | research lane: 208 landmark-bearing (3.7%); never train on text as label |
| `field_visits` | `photo_hash` | T3 | integrity feature | media duplication (FA009 162/610) |
| `lenders` | `lender_id` | T0 | business-value context | assigned to PS3; measured no signal (style varies ≤1.4 pts) |
| `lenders` | `lender_name` | T0 | business-value context | assigned to PS3; measured no signal (style varies ≤1.4 pts) |
| `lenders` | `lender_type` | T0 | business-value context | assigned to PS3; measured no signal (style varies ≤1.4 pts) |
| `lenders` | `kyc_address_format` | T0 | business-value context | assigned to PS3; measured no signal (style varies ≤1.4 pts) |
| `payments` | `payment_id` | — | excluded | PS1+PS2-assigned; post-outcome by construction; no PS3 artefact reads it |
| `payments` | `account_id` | — | excluded | PS1+PS2-assigned; post-outcome by construction; no PS3 artefact reads it |
| `payments` | `payment_ts` | T4 | excluded | PS1+PS2-assigned; post-outcome by construction; no PS3 artefact reads it |
| `payments` | `amount` | T4 | excluded | PS1+PS2-assigned; post-outcome by construction; no PS3 artefact reads it |
| `payments` | `channel` | T4 | excluded | PS1+PS2-assigned; post-outcome by construction; no PS3 artefact reads it |
| `splits` | `account_id` | T0 | key (not a feature) | protocol key |
| `splits` | `split` | T0 | evaluation-only | official partition; account-level, time-blind |
