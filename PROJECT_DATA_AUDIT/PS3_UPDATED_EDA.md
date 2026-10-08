# PS3 UPDATED EDA (v2)

**Scope:** DATASET A (12 official tables). **Frames:** **T0** address/query arrival · **T1** candidate generation · **T2** before a field visit · **T3** during/after a visit · **T4** future/post-outcome. (v1 used a different T2/T3 split; all v2 documents use these definitions.)
**Purpose:** re-answer the EDA questions on the corrected official scope, state every finding that **weakens** an assumption as such, and register the four number corrections v2 issues.

---

## 1. Address structure (T0)

Median 67 chars · trailing `- <6 digits>` on 2,907 (93.3%) — 2,647 known pincodes, 260 unknown · non-ASCII 262 (8.4%; Devanagari 154, Kannada 108) · comma-free 777 (24.9%) · house marker 2,111 (67.7%) · towns T3 986 / T2 952 / T1 942 / `OUT` 237 · types residence 2,427 / office 464 / permanent_native 226.
**Confirms** the statement's premise; no assumption is invalidated here.

## 2. Account ↔ address ↔ place (T0)

| Finding | Value |
|---|---|
| Addresses per account | 1 → 1,694 · 2 → 695 · 3 → 11 |
| Visited share by type | residence 54.5% · office 33.4% · **permanent_native 0%** |
| `OUT` class | 237 rows, **226 native-village records**, 0 pins, 0 visits; account towns exist but describe the operating town, not the location |
| An account's two met-visited addresses | median **3,011.6 m** apart; **0% within 100 m** (38 pairs) |

**EDA invalidates:** *"an account's addresses are near each other"* and *"two accounts at one building is an edge case"*. Places are shared **across accounts** (81 clusters / 191 addresses) and separated **within** accounts. Identity must come from evidence, never from `account_id` or `address_id`.

## 3. Address reuse (T0/T3)

1,477 of 3,117 addresses visited (47.4%); 1,071 revisited; **73.5% of visits are repeats**; first-visit met 37.8% vs repeat 41.7%; 577 addresses never confirm across 1,650 visits (29.6%).

## 4. Field-visit coverage & agents (T2/T3)

All 5,578 visits belong to the 9 field agents (583–645 each; load deliberately flat). Outcome mix: `address_not_traceable` 25.1% · `locked_premises` 22.4% · `met_borrower` 20.0% · `met_family` 19.0% · `neighbour_says_shifted` 8.2% · `no_such_person` 3.7% · `cash_collected` 1.6%.
**Agent diagnostics (new):** met spread 36.2–45.9%; not-traceable spread **19.5–29.1%**; **media duplication is the only confirmed anomaly** (FA009 162/610; all others ≤4); tenure↔met r=−0.16; `shift` single-valued; time-of-day concentration 79.5–88.7% for **every** agent (schedule artefact).
**EDA invalidates:** *"collector quality is a strong driver of outcomes worth modelling as a feature"* — the spread is real but modest, and the only sharp signal is media integrity. Use weights, not models.

## 5. Visit selection bias (T0)

Exposure is strongly targeted (DPD band, portfolio) while **yield is flat**: by DPD 37.5–42.9%; by outstanding quintile 43.1 / 38.5 / 41.6 / 38.2 / 41.8%; met/not-met median outstanding ratio 0.99.
**EDA invalidates:** *"harder or more valuable cases are visited later and teach less"* and *"value predicts visit success"*. Neither holds: bias lives in **where effort goes**, not in what a visit yields. Consequence: model exposure; do not use value as a success proxy.

## 6. Temporal (T0→T4)

Window 2026-04-01 → 06-29 (77 visit dates, no Sundays); `added_date`→first visit median 14 d (p90 66). No second wave exists — "continuous learning" must be designed and replayed, not measured from a held-out wave.

## 7. Splits & entity leakage (T0 protocol)

Accounts 1,680/360/360 → addresses 2,175/483/459 → visits 3,896/894/788; surveyed truths **train 66 · val 19 · test 15**.
**Sharpened leakage (new):** test addresses sharing **identical identity text** with train: **1 of 459**. But **124 of 344 (36.0%) test addresses with a met visit lie within 30 m of a train met check-in** (279 within 100 m).
**EDA invalidates:** *"the account-level split separates addresses."* It separates *accounts*; places still touch. Address-level claims must be split-aware, and memory features must be validated without crossing splits.

## 8. The T0–T4 knowledge timeline (what is known, when)

| Stage | Available | Never usable here |
|---|---|---|
| **T0** | address text/type/source/added_date/town; account exposure + value context; gazetteer; **vendor pin**; split label (protocol) | any field evidence for this address |
| **T1** | candidate set from locality/pincode/landmark/co-location anchors; baseline stratum; **finer-pin anchors exist for 96.7% of coarse cases (median 96 m)** | outcome-conditioned anything |
| **T2** (before the visit) | the offline pack: candidates, radius, directions, **earlier-visit memory of this place** | this visit's own outcome; other agents' concurrent work |
| **T3** (during/after) | check-in, trail, accuracy, dwell, photo hash, outcome, remark — appended, not overwritten | treating any of it as truth; negative outcomes as locations |
| **T4** | place memory, radius table, co-location clusters, retraining corpora (eligibility-gated) | the surveyed 100 (evaluation only, forever) |

## 9. Dynamic replay, split-aware (new headline)

2026-05-15 cut, warm = confirmed before the cut:
**post-cut: warm 56.0% met (n=1,383) vs cold 24.5% (n=1,343); overall 40.5%.**
**val+test only: warm 56.7% (n=441) vs cold 25.1% (n=410).**
**Correction C-1:** v1 published "56.0% vs 40.5% for all other post-cut visits"; 40.5% was the *overall* rate. The true contrast is more than double, and it holds outside training data.
**Memory consistency:** 563 addresses with ≥2 met visits → median pairwise distance 77.7 m (same agent) vs 75.8 m (different agent) → **agent-independent** (correction C-3: v1 printed 90.0/98.0 m without a stated definition).

## 10. Uncertainty: radius transfer (new)

Fit on train truths, evaluated on val+test: locality stratum p80 = 539.9 m → **79.2% eval coverage** (n=24); street 162.1 m → 100% (n=5); **pincode 1,204.2 m → 0% (n=4)**; rooftop n=1.
**Reading:** a per-stratum radius table is publishable **only with n attached**; the pincode stratum's radius fails transfer and must be published as a failure, not a number.

## 11. Memory premise (re-verified, split-aware)

First met-someone check-in vs survey truth vs the vendor pin on the same addresses: all 38 → **24.0 m vs 380.3 m**, memory better in 89.5%; **val+test only (n=15) → 21.1 m vs 383.7 m, better in 80%**. The premise survives outside training entities.

## 12. What the EDA does **not** change

Baseline coarseness (376.4 m median, 9.0% <100 m) · negative evidence is not location (1,603 m, closer to the wrong pin 84.9%) · geometry of check-ins is clean (≤90.8 m from own trail) · the hierarchy alone cannot beat the baseline. No architectural conclusion moves (see the re-audit §6).

## 13. Findings register — "EDA invalidates this assumption"

| # | Assumption that fails | Evidence | Change |
|---|---|---|---|
| E-1 | One address per borrower | 706 accounts hold 2–3; 226 native-village rows never visited | State the address role; exclude `permanent_native` from merging |
| E-2 | Two accounts at a building is an edge case | 81 clusters / 191 addresses; all cross-account | Place identity from evidence |
| E-3 | An account's addresses are the same place | median 3,011.6 m apart; 0% within 100 m | Never merge by account |
| E-4 | Duplicate text ⇒ duplicate place | Render key: 70 template families (184/203 native), 3 ever visited | Keep identity vs render keys separate |
| E-5 | The account split separates addresses | 36.0% of met test addresses within 30 m of train evidence | Split-aware reporting; guarded memory validation |
| E-6 | Value predicts visit success | Quintile met rates 38.2–43.1%; median ratio 0.99 | Value shapes priority, not accuracy claims |
| E-7 | Agent traits drive outcomes | tenure r=−0.16; shift null; language match unhelpful | Weights only: media integrity + per-agent variance |
| E-8 | Collector time-of-day anomaly | every agent 79.5–88.7% in 10:00–12:59 | Retract; schedule artefact |
| E-9 | Visit outcomes capture what the field learned | 208 remarks (3.7%) carry corrective landmarks; 0 name a locality | Remarks become a structured evidence lane |
