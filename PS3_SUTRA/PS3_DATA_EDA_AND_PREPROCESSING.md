# PS3 DATA EDA AND PREPROCESSING

**SUTRA — Address Geocoder That Learns from Field Visits.**
**Scope of this document: the official PS3 dataset supplied for the problem statement, and nothing else.**
Prepared before any model training. Every number here is measured directly from the official files by
`tools/eda_official.py` (transcript: `data/derived/eda_report.txt`, 608 lines) and `tools/eda_charts.py`
(charts: `data/derived/eda_charts/`, dashboard: `data/derived/eda_charts.html`). Nothing in this document is estimated,
borrowed, or inferred from any other source.

---

> **SUPERSESSION NOTE — 2026-10-07 (official-scope re-audit).**
> Two figures in this document are **definition-dependent** and are now published with their definitions in
> §3 of the official-scope re-audit's *Updated Data Audit*, in the sibling re-audit set outside this workspace:
> * duplicate address text — **5 groups / 10 rows** under the *identity* key (trailing token kept); **70 groups / 203 rows** under the *render* key (trailing token stripped; 193 rows differ only in that token, 184 of them `permanent_native` — template families, **not** duplicates);
> * near-duplicate pairs — **238** under the char-3-gram measure; **161** under the token-set measure (all 161 cross-account, 73 cross-split).
> Two results are **strengthened** by the same re-audit: two accounts at one place is not an edge case — **191 addresses form 81 co-located clusters** (met check-ins ≤30 m, all cross-account); and the memory premise holds outside the training split (**val+test subset: 21.1 m vs 383.7 m pin, memory better in 80%**). No number in §A–§I, and no architectural conclusion, changes.

> **Scope note (2026-10-07, official-scope re-audit).** This document's corpus statements ("11 tables · 177,190 rows",
> SHA-256 snapshot table) describe the working copy at authoring time. The **scope of record is now 12 tables ·
> 177,196 rows**: the officially assigned shared table `lenders` (6 rows × 4 columns) joined the frozen tree and the
> hash set was re-baselined. `lenders` is context-only (measured to carry no address-style signal) and **no statistic,
> chart or conclusion in this document changes**. The evaluation amendments (place-blocked folds, radius n-floor,
> prequential replay) are recorded in the architecture documents' Amendment sections.


---

## 1. Scope

This document answers five questions about the **official dataset only**:

1. What does the official PS3 dataset look like — every table, field, key, distribution and defect?
2. What did detailed EDA find that matters for modelling?
3. How was the data cleaned and preprocessed, and what exactly was produced?
4. Why was each decision made — including the decisions *not* to act?
5. What does the EDA tell us about the model stage that follows?

**Boundaries observed throughout:**

* Only the 11 official CSV tables in `data/official_ps3/` are analysed. **No other data source of any kind is used,
  cleaned, joined, referenced or proposed in this document.**
* The official files are opened **read-only** and are byte-verified by hash in §2. All cleaning output goes to
  `data/cleaned/`; all derived artefacts go to `data/derived/`.
* **No model is trained here.** This document ends at EDA + cleaning + preprocessing + feature design + leakage
  verification + modelling implications.
* Findings that **weaken** the intended architecture are reported with the same prominence as findings that support it
  (§24.2 lists five such findings explicitly).
* All numbers are dataset-specific. Nothing in this document is a claim about real-world Indian addresses, real
  collections operations, or national accuracy. The dataset's own README states it is synthetic; where that synthetic
  character changes how a number may be used, the document says so in the text.

**Reproduction:**

```bash
bash tools/reproduce.sh              # everything below, in order, ~40 s
python3 tools/eda_official.py        # 608-line EDA transcript + machine-readable tables + 8 charts
python3 tools/eda_charts.py          # 14 charts + self-contained HTML dashboard
```

---

## 2. Official Dataset Overview

**11 tables · 177,190 rows · 8.97 MB of CSV · one synthetic collections book across three towns.**

Snapshot analysed (SHA-256, first 12 hex) — this is the exact data every number in this document comes from:

| Table | Rows | Cols | Bytes | SHA-256[:12] |
|---|---|---|---|---|
| `accounts.csv` | 2,400 | 20 | 320,356 | `df65051e6f70` |
| `addresses.csv` | 3,117 | 7 | 405,168 | `7e0eed682a64` |
| `agents.csv` | 30 | 6 | 969 | `1a1d8722e4db` |
| `baseline_geocodes.csv` | 2,880 | 4 | 91,795 | `e7dde99db504` |
| `field_visits.csv` | 5,578 | 15 | 960,718 | `b4099e532581` |
| `landmarks_poi.csv` | 240 | 6 | 11,278 | `d565be9d3fca` |
| `localities.csv` | 36 | 6 | 1,701 | `b18ea44e58f0` |
| `splits.csv` | 2,400 | 2 | 37,457 | `005342b60c45` |
| `surveyed_addresses.csv` | 100 | 3 | 2,356 | `2d26aa6c6c23` |
| `towns.csv` | 3 | 4 | 135 | `e0167d3efe2d` |
| `visit_gps_points.csv` | 160,406 | 6 | 7,136,303 | `1afd7b9f7c0d` |
| **Total** | **177,190** | **79** | **8,968,236 B (8.97 MB)** | — |

**Shape of the book.** 2,400 accounts (6 lenders, 6 portfolios) hold 3,117 addresses across three modelled towns plus
237 addresses flagged outside every modelled town. A vendor geocoder has placed 2,880 of those addresses. 9 field
agents have made 5,578 visits to 1,477 addresses, each visit carrying a GPS trail (160,406 points), a dwell time, a
photo hash and a two-part outcome. 100 addresses carry surveyed ground truth. An official account-level
train/validation/test assignment covers all 2,400 accounts.

**MODELLING IMPLICATION.** The learnable surface is *small and sharply asymmetric*: 3,117 addresses, of which only
**47.4% were ever visited**, only **28.9% ever produced a met-someone visit**, and only **3.2% carry true coordinates**.
Any model that needs dense per-address supervision cannot be fitted here; any model that consumes *evidence events*
(visits) has 5,578 observations with rich structure. This asymmetry — many addresses, few truths, moderate visit
volume — is the single fact that shapes every subsequent decision.

---

## 3. Table-by-Table Schema

Dtypes, null %, cardinality, duplicates and ranges are as measured. "Unique" marks a verified candidate key.
Exact duplicate rows are **zero in every table**.

### 3.1 `towns.csv` — 3 rows × 4 cols (reference)
| Field | Type | Null % | Distinct | Notes |
|---|---|---|---|---|
| `town_id` | object | 0 | 3 | **key**: T1, T2, T3 |
| `town_name` | object | 0 | 3 | Kaveripura · Devgarh Nagar · Navanagara East |
| `address_style` | object | 0 | 3 | `karnataka` · `hindi` · `metro` — one per town |
| `approx_radius_m` | int | 0 | 3 | 4,200 · 3,800 · 4,800 |

**MODELLING IMPLICATION.** `address_style` is a *labelling convention*, not data: it correlates perfectly with
`town_id` and would let a model memorise towns through a proxy. `approx_radius_m` is an author parameter, not a
measurement — it must never be published as an error bound. Both are context, not features.

### 3.2 `localities.csv` — 36 rows × 6 cols (reference)
| Field | Type | Null % | Distinct | Notes |
|---|---|---|---|---|
| `locality_id` | object | 0 | 36 | **key** |
| `town_id` | object | 0 | 3 | FK → towns; 12 localities per town |
| `locality_name` | object | 0 | **35** | `Nehru Colony` appears in T1 **and** T2 |
| `pincode` | int | 0 | 12 | 4 per town; **no pincode crosses a town** |
| `centroid_x`, `centroid_y` | float | 0 | 36 each | 1-decimal values (rounded artefacts) |

**MODELLING IMPLICATION.** Locality identity must be keyed `(town_id, locality_name)`; a name-only lookup silently
merges two different places 3.5 km apart. Centroids are rounded to 0.1 m precision but sit inside a multi-km town —
they are *coarse* anchors, and their precision of representation must not be mistaken for spatial precision.

### 3.3 `landmarks_poi.csv` — 240 rows × 6 cols (reference)
| Field | Type | Null % | Distinct | Notes |
|---|---|---|---|---|
| `poi_id` | object | 0 | 240 | **key** |
| `town_id` | object | 0 | 3 | 82 / 77 / 81 per town |
| `landmark_type` | object | 0 | 14 | ration_shop 26, bus_stop 22, govt_school 22, … petrol_bunk 8 |
| `name` | object | 0 | **14** | exactly mirrors the type count — e.g. every ration shop is named "Ration Shop" |
| `x`, `y` | float | 0 | 238 / 239 | coordinates near-unique |

**MODELLING IMPLICATION.** With 14 distinct names over 240 rows (42 `(town, name)` groups; 198 rows are repeats beyond
the first of their group), a landmark name is **not an identifier**. Landmarks can contribute a *type + town-scoped*
language prior and a plausibility feature; they cannot be snapped to as a coordinate target.

### 3.4 `accounts.csv` — 2,400 rows × 20 cols (context)
| Field | Type | Null % | Distinct | Notes |
|---|---|---|---|---|
| `account_id` | object | 0 | 2,400 | **key** |
| `lender_id` | object | 0 | 6 | L01 646, L06 567, L03 499, … |
| `portfolio` | object | 0 | 6 | pl_salaried 682 · two_wheeler 502 · mfi_jlg 358 · credit_card 319 · consumer_durable 296 · msme 243 |
| `income_type` | object | 0 | 3 | salaried 1,283 · self_employed 792 · daily_wage 325 |
| `town_id` | object | 0 | 3 | T3 826 · T1 787 · T2 787 |
| `preferred_language` | object | 0 | 3 | hinglish 1,217 · kanglish 640 · english 543 |
| `bucket_start` | object | 0 | 5 | 1-30 (664) · 31-60 (528) · 90+ (470) · … |
| `dpd_start` | int | 0 | 323 | 0–720, mean 66.4 |
| `emi_amount` | float | 0 | 473 | 700–39,950, mean 7,500 |
| `overdue_start` | float | 0 | 790 | 700–460,200, mean 20,490 |
| `outstanding` | float | 0 | 1,665 | 6,300–2,117,000, mean 217,000 |
| `salary_credit_day` | float | **68.2** | 8 | 1–30 — only meaningful for salaried accounts |
| `bureau_score_band` | object | 0 | 5 | 300-549 (1,508) · 550-649 (609) · … |
| `other_active_loans` | int | 0 | 9 | 0–8, mean 1.9 |
| `paid_other_lenders_30d` | bool | 0 | 2 | true for 25.2% |
| `last_bounce_reason` | object | 0 | 4 | insufficient_funds 2,019 · technical 158 · stop_payment 118 |
| `ability_to_pay_estimate` | float | **30.3** | 101 | 0–1, mean 0.53 |
| `prev_ptp_count` / `prev_ptp_broken` | int | 0 | 10 / 8 | 0–10 / 0–7 |
| `dialling_arm` | object | 0 | 2 | rule_based 2,277 · random_contact_point 123 |

**MODELLING IMPLICATION.** Account fields describe *why a visit happens* (risk, value, language), not *where a place
is*. They are legitimate inputs to a **visit-pricing or exposure model** and are **forbidden** as location features:
they correlate with the collections policy, and using them to place a coordinate would teach the model the policy
instead of the geography (§22).

### 3.5 `addresses.csv` — 3,117 rows × 7 cols (the book)
| Field | Type | Null % | Distinct | Notes |
|---|---|---|---|---|
| `address_id` | object | 0 | 3,117 | **key** |
| `account_id` | object | 0 | 2,400 | FK → accounts; 1 address for 1,694 accounts, 2 for 695, 3 for 11 |
| `address_type` | object | 0 | 3 | residence 2,427 · office 464 · permanent_native 226 |
| `source` | object | 0 | 2 | kyc_origination 3,090 · skip_trace 27 |
| `added_date` | object | 0 | **24** | 2026-04-01 … 2026-06-29; **3,093 (99.2%) on one weekday — 3,090 on 2026-04-01 alone** |
| `town_id` | object | 0 | **4** | T3 986 · T2 952 · T1 942 · **OUT 237** |
| `address_text` | object | 0 | 3,114 | 3 exact duplicates; median 67 characters |

**MODELLING IMPLICATION.** `town_id` contains a value (`OUT`) that does not exist in `towns.csv` — the dataset ships
with a built-in refusal case, and a pipeline that assumes a closed hierarchy will crash or silently mis-file 237
records. `added_date` has only 24 distinct values, 99.2% of them on a single weekday: it is a generation timestamp, not
a business event, and must not be used as a temporal feature (§12).

### 3.6 `baseline_geocodes.csv` — 2,880 rows × 4 cols (the vendor pin)
| Field | Type | Null % | Distinct | Notes |
|---|---|---|---|---|
| `address_id` | object | 0 | 2,880 | **key** (one row per geocoded address) |
| `geocoder_x`, `geocoder_y` | float | 0 | 2,806 / 2,814 | x ∈ [−4,061.5, 4,327.2], y ∈ [−4,088.6, 3,403.4]; 1 decimal |
| `precision` | object | 0 | 4 | **locality 2,052 (71.2%)** · street 504 (17.5%) · pincode 274 (9.5%) · rooftop 50 (1.7%) |

**MODELLING IMPLICATION.** The vendor's own vocabulary is a *granularity claim*, and it is heavily skewed to the
coarsest useful level. Coverage is 92.4% — the missing 7.6% are exactly the `OUT` records. Coordinate precision
(1 decimal) far exceeds spatial precision (hundreds of metres): the pin looks precise and is not.

### 3.7 `surveyed_addresses.csv` — 100 rows × 3 cols (the only ground truth)
| Field | Type | Null % | Distinct | Notes |
|---|---|---|---|---|
| `address_id` | object | 0 | 100 | **key**; all are `residence`, 98 `kyc_origination` |
| `surveyed_x`, `surveyed_y` | float | 0 | 100 / 100 | x ∈ [−4,039, 4,177.6], y ∈ [−4,013.1, 3,429.9] |

**MODELLING IMPLICATION.** 100 rows, 3.2% coverage, **zero** `OUT` records, zero offices, zero native addresses, one
rooftop-stratum record, and 66 of the 100 accounts sit in the official *train* split (§13). Every headline metric in
this project is computed on this sample, with its n attached, or not at all.

### 3.8 `field_visits.csv` — 5,578 rows × 15 cols (the evidence)
| Field | Type | Null % | Distinct | Notes |
|---|---|---|---|---|
| `visit_id` | object | 0 | 5,578 | **key** |
| `account_id` / `address_id` | object | 0 | 1,339 / 1,477 | FKs |
| `agent_id` | object | 0 | **9** | of 30 agents, only 9 ever visit |
| `visit_date` | object | 0 | 77 | 2026-04-01 … 2026-06-29 |
| `start_ts`, `checkin_ts` | object | 0 | 5,564 / 5,569 | no nulls, no negative travel |
| `checkin_x`, `checkin_y` | float | 0 | 5,263 / 5,253 | **5,578 distinct (x,y) pairs — no two visits share a coordinate** |
| `gps_accuracy_m` | float | 0 | 324 | 4–72.8, mean 11.3 |
| `dwell_s` | int | 0 | 1,129 | **30–1,495 (≈25 min cap)**, median 207 s |
| `outcome` | object | 0 | 7 | see §9 |
| `ptp_id` | object | **89.2** | 605 | belongs to a different workflow → dropped in cleaning |
| `remark` | object | 0 | 762 | free text, multilingual (Hindi/Kannada/English transliteration) |
| `photo_hash` | object | 0 | 5,417 | 161 repeat-hash visits beyond the first (see §11) |

**MODELLING IMPLICATION.** The visit table is the only place where the field's judgement about a place is recorded, and
it is *dense but biased*: 100% of visits come from 9 agents, 47.4% of addresses are never visited, and the outcome
vocabulary mixes place-information and person-information (§9). `ptp_id` is an accidental dependency and is removed.
`dwell_s` has a hard 1,495 s ceiling — a fabricated-looking upper bound that tells us the dwell distribution is
generated, not observed (see §24.2, finding W3).

### 3.9 `agents.csv` — 30 rows × 6 cols (collectors)
| Field | Type | Null % | Distinct | Notes |
|---|---|---|---|---|
| `agent_id` | object | 0 | 30 | **key** |
| `channel` | object | 0 | 3 | tele 20 · field 9 · voice_bot 1 |
| `language_team` | object | 0 | 4 | hinglish 14 · kanglish 8 · english 7 · all 1 |
| `town_id` | object | **70.0** | 3 | null for all 21 non-field agents — **not applicable**, not missing |
| `tenure_months` | float | 3.3 (1 cell) | 25 | 1–64, mean 30.5 |
| `shift` | object | 0 | 2 | day 29 · all 1 |

**MODELLING IMPLICATION.** The roster is tiny (9 producing agents). Agent identity is therefore high-risk as a model
feature — 9 categories over 5,578 visits allows trivial memorisation — and high-value as an **integrity and monitoring
signal** (§11). It must never be a production feature, because a 10th agent must not break scoring.

### 3.10 `visit_gps_points.csv` — 160,406 rows × 6 cols (trails)
| Field | Type | Null % | Distinct | Notes |
|---|---|---|---|---|
| `visit_id` | object | 0 | 5,578 | FK; composite key with `seq` |
| `seq` | int | 0 | **80** | 0–79, monotone in time |
| `point_ts` | object | 0 | 146,732 | 2026-04-01 09:39:07 → 2026-06-29 13:43:44 |
| `x`, `y` | **int** | 0 | 8,200 / 7,407 | whole metres — 1 m quantisation, coarser than the vendor pin's decimals |
| `accuracy_m` | **int** | 0 | 98 | 3–111, median 10 |

**MODELLING IMPLICATION.** Trails are integer-quantised and capped at 80 points per visit — fine for geometry and
evidence weighting, insufficient for sub-metre claims. The `(visit_id, seq)` pair is the real key; `visit_id` alone
repeats 154,828 times, so naive joins on `visit_id` alone will multiply rows.

### 3.11 `splits.csv` — 2,400 rows × 2 cols (evaluation protocol)
| Field | Type | Null % | Distinct | Notes |
|---|---|---|---|---|
| `account_id` | object | 0 | 2,400 | **key**; covers every account exactly once |
| `split` | object | 0 | 3 | train 1,680 · validation 360 · test 360 |

**MODELLING IMPLICATION.** The protocol is account-level and time-blind; see §13 for what it does and does not
guarantee.

---

## 4. Dataset Relationships

### 4.1 Foreign keys (verified in both directions)

```
towns(T1,T2,T3) ──< localities ──< (name → address text, NOT a stored FK)
      │                 └── pincode (4 per town, never shared)
      ├──< landmarks_poi (240)
      ├──< addresses (3,117; 237 carry town_id='OUT' — NOT in towns)
                ▲
                │ address_id
      accounts ─┴──< baseline_geocodes (2,880)
           │  └──< field_visits (5,578) ──< visit_gps_points (160,406 on (visit_id, seq))
           │            └── agent_id ──< agents (9 of 30 ever visit)
           └──< splits (2,400, all accounts)
                 surveyed_addresses (100) ──▶ addresses  [ground truth, evaluation only]
```

| Relationship | Integrity result |
|---|---|
| `addresses.account_id → accounts` | 0 orphans (2,400 accounts used) |
| `addresses.town_id → towns` | **1 orphan value: `OUT`, 237 rows** |
| `field_visits.address_id → addresses` | 0 orphans; 1,477 distinct addresses |
| `field_visits.account_id → accounts` | 0 orphans; 1,339 distinct accounts |
| `field_visits.agent_id → agents` | 0 orphans; only 9 agents appear |
| `baseline_geocodes.address_id → addresses` | 0 orphans; 237 addresses uncovered |
| `surveyed_addresses.address_id → addresses` | 0 orphans; 100 of 3,117 |
| `splits.account_id → accounts` | exact coverage, no duplicates |
| `visit_gps_points.(visit_id, seq)` | 0 violations; every visit has ≥1 trail point |

### 4.2 The missing link that matters most

**There is no stored address → locality foreign key.** Locality can only be *inferred from the address text*. Measured:
an exact, town-scoped substring match succeeds for **1,904 of 3,117 addresses (61.1%)**, fails for **1,213 (38.9%)**,
and ambiguously matches two or more localities for **0** — because 61.1% of texts name their locality explicitly, and
those that do name exactly one. Of the addresses that do match a locality, **150 (7.9%) carry a trailing 6-digit
pincode token that contradicts the matched locality's pincode** (a further 260 records carry a 6-digit token that
matches no pincode in the gazetteer at all).

**MODELLING IMPLICATION.** The geographic hierarchy is a *hypothesis to be scored*, not a lookup to be executed.
Candidate generation must therefore output *evidence* (which gazetteer token matched, with what strength, at what
granularity) rather than a resolved chain — and it must be able to run with no locality at all, because 38.9% of
records offer none.

---

## 5. Address Text EDA

### 5.1 Shape of the strings

| Metric | Measured (n = 3,117) |
|---|---|
| Characters | min 11 · p25 55 · **median 67** · p75 78 · p90 84 · max 113 · mean 66.8 |
| Tokens | min 2 · **median 12** · p90 15 · max 20 · mean 11.88 |
| Digits | mean 8.86 · median 9 · **0 digits in 9 rows (0.29%)** |
| Letters | mean 41.1 · 0 rows with fewer than 5 letters |
| Commas | **0 commas: 777 (24.9%)** · 1: 26 · 2: 427 · 3+: 1,887 |
| Slashes | present in 426 (13.7%), max 2 |
| Hyphens | present in **2,967 (95.2%)**, max 2 |
| Dots | present in 1,302 (41.8%) — abbreviation artefacts like `H.No.` |
| No separator at all (no comma, slash, hyphen) | 24 (0.8%) |
| Trailing `- <6 digits>` pattern | **2,907 (93.3%)** |
| Non-ASCII characters | **262 rows (8.41%)**: Devanagari 154, Kannada 108 |

Histogram of length (bars = count of records): 0–10: 0 · 10–20: 2 · 20–30: 8 · 30–40: 63 · 40–50: 246 · 50–60: 676 ·
60–70: **739** · 70–80: **752** · 80–90: 496 · 90–100: 111 · 100–110: 21 · 110–120: 3.

**Examples (verbatim, including the two scripts and the numeric tails):**

```
6th Cross, 5th Main, ಚರ್ಚ್ ಹತ್ತಿರ, Kuvempu Layt, Kaveripura - 960102
गली नं. 3, राशन की दुकान के बगल में, Tilak Ngr, Devgarh Nagar - 970204
house 52 gali no. 5 ward 9 मस्जिद के पास shastri nagar devgarh nagar - 970201
#160, 5th Cross, 1st Main, ಕಲ್ಯಾಣ ಮಂಟಪ ಹತ್ತಿರ, Kalyana Ngr, Kaveripura - 960104
414/3, DEVGARH NAGAR - 970203
railway colony navanagara east - 980304
```

**MODELLING IMPLICATION.** These are **short, semi-structured, delimited strings**, not free prose and not clean
fields. Median 67 characters and 12 tokens mean word-level rules and character n-grams are affordable and sufficient;
the 95.2% hyphen presence shows the records carry an almost fixed `… - <pincode>` tail, which is a *structural
separator*, not punctuation noise. A heavy learned parser would be solving a problem this data does not pose.

### 5.2 Component presence — what can be relied on

| Component | Present | Reading |
|---|---|---|
| Town name | 2,922 (93.7%) | the town is almost always written — strong T0 evidence |
| Trailing 6-digit token | 2,907 (93.3%) | almost always present structurally |
| **…of which matches a known pincode** | **2,647 (91.1% of tokens / 84.9% of all records)** | pincode evidence usually true, sometimes false |
| Locality name token (any known locality word) | 2,572 (82.5%) | strong but not universal |
| Locality name of the *correct town* (exact substring) | 1,904 (61.1%) | the usable resolution rate |
| House number, **marker-anchored** (a dwelling marker + digit, or a `12/3`-style token) | **2,111 (67.7%)** | most records identify a dwelling — with a definition attached |
| House number, **any numeric token** (upper bound) | 3,099 (99.4%) | includes pincode tails and road numbers — the two definitions differ by 31.7 points (§24.1 row 11) |
| Known landmark phrase | 785 (25.2%) | landmark evidence is a minority signal |
| **At least one of {locality, known pincode, landmark}** | **2,855 (91.6%)** | resolvable in principle |
| **None of the three** | **262 (8.4%)** | falls back to town-level prior |
| House number **and** known locality | 1,898 (60.9%) | the records that can support street-level placement |
| Neither house number nor locality | 332 (10.7%) | coarse-only records |

**MODELLING IMPLICATION.** Candidate generation has three usable evidence channels (town, pincode, locality) covering
91.6% of records, one scarce channel (landmark, 25.2%), and a hard floor: **332 records (10.7%) cannot be placed
better than town level by text alone**, and 8.4% have no sub-town evidence at all. Any architecture must therefore
treat "coarse" and "unplaceable" as normal operating states, not exceptions.

### 5.3 The 6-digit tokens are hypotheses, not facts

2,907 records contain a 6-digit token; **260 of them (8.9%) match no pincode in the gazetteer**, and where a record
matches a locality by name, **7.9% of those matches are contradicted by the record's own pincode token**. Since only
12 pincodes exist in the whole dataset, a 6-digit token that matches nothing is very likely a plot number, a phone
fragment, or a house number — and a token that matches a *different* area's pincode is a data-entry error or a genuine
mobility signal (a work address).

**MODELLING IMPLICATION.** Pincode agreement is **soft evidence with an explicit contradiction feature**, never a hard
constraint. A pipeline that filters on pincode equality would silently discard 410 records — 260 whose 6-digit token
matches nothing plus 150 whose token contradicts the locality they match — 13.2% of the book, including precisely the
records the field reports as hardest.

### 5.4 Vocabulary, structure and repetition

**Top content words** (share of records): nagar 39.4% · east 32.6% · navanagara 30.5% · devgarh 29.8% · kaveripura
29.6% · gali 22.5% · main 20.5% · blk 19.0% · cross 16.7% · colony 15.5% · house 12.0% · ngr 9.1% · nehru 8.7% ·
nagr 8.7% · road 8.6% · block 8.1% · ward 7.7% · village 7.6% · district 7.6% · close 7.5% · temple 7.0% ·
near 6.6% · layout 5.8% · bus 5.3% · gandhi 5.3% · **hattira 5.3%** (Kannada "near") · enclave 4.7% · patel 4.7% ·
school 4.6% · colny 4.4%.

**Structural vocabulary present**: `no.` 31.2% · `nagar/nager` 32.9% · `rd` 22.8% · `gali` 22.5% · `main` 20.5% ·
`cross` 16.7% · `colony` 15.5% · `h.no` 12.9% · `block` 8.1% · `near` 6.6% · `layout` 5.8% · `opp` 3.8% · `phase` 3.2%
· `opposite` 1.8% · `behind` 1.6%.
**Structurally absent**: `st` 0% · `sector` 0% · `extension` 0% · `circle` 0% · `stage` 0%.

**Top 2-grams**: `navanagara east` ×927 · `devgarh nagar` ×649 · `gali no` ×471 · `th main` ×404 · `h no` ×399 ·
`th cross` ×377 · `cross th` ×336 · `nagar devgarh` ×279 · `nagar kaveripura` ×244 · `close to` ×233 ·
`colony navanagara` ×215 · `no gali` ×196.

**Templates**: 2,586 distinct digit-masked/word-masked templates across 3,117 records; the eight most common cover
only **2.5%** of rows.

**Unusual tokens (frequency 1, length > 8)**: `navanagora`, `navvanagara`, `apatments`, `naavanagara`, `kavripura`,
`apartment`, `navnagara`, `sidddeshwara`, `naanagara`, `kaveipura`, `anjjaneya`, `communitty`.

**MODELLING IMPLICATION.** The vocabulary is *local and misspelled* (three spellings of the same locality in one
record set, plus transliteration variants). Normalisation plus character n-grams is the right tool; aggressive
language modelling is not: there are only ~2,600 distinct templates and the tail is dominated by *misspellings of
gazetteer names*, which is exactly what a fuzzy gazetteer matcher with town scoping handles cheaply. The presence of
Kannada/Hindi relational words (`hattira`, `गली`, `मस्जिद`, `ಬಗಲು`) means the resolver must carry multi-script
relation markers, not just Latin abbreviations.

### 5.5 Duplicates and near-duplicates in the text

| Measure | Value |
|---|---|
| Exact duplicate texts | 3 |
| Duplicate after normalisation | 5 groups, **10 rows**, spanning 5 pairs of **different accounts**, all within one town |
| Near-duplicate pairs (char-3-gram Jaccard ≥ 0.80, blocked by leading tokens) | **238 pairs, all within one town** |
| …of those, identical once digits are masked (**same template, different numbers**) | **228** |
| …of those, differing in wording as well | 10 |

Examples of the 228 same-template pairs (these are *different places written the same way*):

```
'Village Rampura Kalan, Tehsil D, District South - 996281'  vs  '… District South - 999621'   J = 0.923
'Village Rampura Kalan, Tehsil D, District North - 992673'  vs  '… District North - 999495'   J = 0.852
```

and the 10 genuinely similar-wording pairs (the only true near-duplicate risk), e.g. region-type records such as
`railway colony navanagara east - 980304` appearing under two accounts.

**MODELLING IMPLICATION.** **Text similarity is not place identity.** A high-Jaccard pair is *usually* two different
addresses sharing a village template, and only *occasionally* the same building written twice. Therefore: (a) a
string-similarity feature must never alone decide that two records are the same place; (b) entity grouping for
train/test integrity must use `(account_id, normalised text, town)` — not fuzzy similarity, which would over-merge
238 pairs; and (c) the 10 rows in 5 duplicate groups are exactly the rows that could leak across a split.

### 5.6 Where the non-ASCII records are

| Town | Share non-ASCII |
|---|---|
| T2 | 16.2% |
| T1 | 8.6% |
| T3 | 2.7% |
| OUT | 0.0% |

**MODELLING IMPLICATION.** Script usage is town-correlated, so a model could learn "non-ASCII ⇒ T2" — a proxy for the
town the record already declares. Script features are legitimate (they describe the text) but must be paired with the
declared town in a way that cannot substitute for it.

### 5.7 Degenerate records

9 records (0.29%) contain **no digit at all**; 2 are under 20 characters; 2 have fewer than 4 tokens; **none** are
empty or letter-free. The shortest records are `Kaveripura - 960102`, `shastri ngr devgrah nagar`,
`gandhi basti devgarh nagar` — town/neighbourhood-level statements with no dwelling identifier.

**MODELLING IMPLICATION.** There is no empty-address problem to solve, but there is a **structural-information
ceiling**: for these records the correct answer is a neighbourhood-scale coordinate, and a system that returns a
street-level tier for them is lying. The tier vocabulary must be driven by *text evidence*, not by ambition.

---

## 6. Geographic Hierarchy EDA

### 6.1 Town → locality → pincode

| Town | Localities | Pincodes | Landmarks | Addresses | Style | `approx_radius_m` | Max locality-centroid spread from town centre |
|---|---|---|---|---|---|---|---|
| T1 | 12 | 4 | 82 | 942 | karnataka | 4,200 | 3,469 m |
| T2 | 12 | 4 | 77 | 952 | hindi | 3,800 | 3,809 m |
| T3 | 12 | 4 | 81 | 986 | metro | 4,800 | 3,935 m |
| OUT | — | — | — | 237 | — | — | — |

* **Pincodes never cross towns** (0 of 12 appear in more than one town) — a useful, rare property.
* **A pincode is not a locality**: 2–5 localities share each `(town, pincode)` pair
  (2 localities ×5 pairs, 3 ×3, 4 ×3, 5 ×1); 24 `(town, pincode)` pairs have more than one locality row.
* **One locality name repeats across towns**: `Nehru Colony` in T1 (pincode 960102, centroid 2735.1, −2128.6) and in T2
  (pincode 970203, centroid 3029.6, 575.7) — 2.7 km apart in the coordinate plane, in different towns entirely.
* Locality centroids carry **1 decimal** (rounded artefacts).

**MODELLING IMPLICATION.** The hierarchy is real but *many-to-one in the wrong direction* for lookup: locality→pincode
is not a function, so a pincode can only narrow to 2–5 candidate localities, never to one. Pincode is therefore **soft
evidence that constrains a candidate set**, and locality is the coarsest unit safe to use as an anchor point.

### 6.2 Landmarks

240 rows, 14 types, **14 distinct names**, 42 `(town, name)` groups covering all 240 rows (198 rows are repeats beyond
the first of their group), per-town counts 82 / 77 / 81, coordinates near-unique (238 distinct x, 239 distinct y).

**MODELLING IMPLICATION.** "Near the Ration Shop" is a statement every 26th record can make; it identifies nothing by
itself. Landmarks enter the design as (a) a town-scoped language prior, and (b) a *plausibility* feature for a
candidate ("does this candidate sit near a landmark of a type the text names?"). They are never a target.

### 6.3 Where ambiguity originates (and how much)

| Ambiguity source | Measured |
|---|---|
| Locality name repeated across towns | 1 name, 2 localities |
| Pincode shared by several localities | all 12 pincodes (2–5 localities each) |
| Landmark name shared within a town | every landmark name; 42 groups over 240 rows |
| Address text matching two locality names | **0** (exact town-scoped matching is unambiguous here) |
| Address text matching a locality that contradicts its own pincode token | **150 records (7.9% of matched)** |
| Address text with no sub-town evidence | **262 records (8.4%)** |
| Addresses per matched locality | mean 54.4 · min 12 · max 179 (35 of the 36 localities are named by at least one address) |

**MODELLING IMPLICATION.** Ambiguity here is *not* the classic "same name, two places" problem (which is present but
tiny); it is **evidence conflict** (pincode vs locality name) and **evidence absence** (8.4% with nothing). That is a
strong argument for a resolver that scores evidence and reports conflicts, rather than a resolver that returns a
single resolved chain and hides its doubts. The 12–179 spread of addresses per locality also makes *per-locality
calibration statistically impossible* (median ~53 addresses, no ground truth per locality) — calibration must be
per stratum and per evidence class.

---

## 7. Baseline Geocoder EDA

### 7.1 Coverage

| Measure | Value |
|---|---|
| Addresses with a vendor pin | 2,880 of 3,117 = **92.4%** |
| Addresses without a pin | **237 (7.6%) — all of them `town_id = 'OUT'`** |
| Coverage by town | T1 100% · T2 100% · T3 100% · OUT **0%** |

### 7.2 Granularity of the answer

| Stratum | Rows | Share |
|---|---|---|
| `locality` | 2,052 | **71.2%** |
| `street` | 504 | 17.5% |
| `pincode` | 274 | 9.5% |
| `rooftop` | 50 | 1.7% |

By town: locality 659/684/709 (T1/T2/T3) · street 152/171/181 · pincode 115/80/79 · rooftop 16/17/17.

**Spatial behaviour of the pins:** 2,880 geocoded addresses produce **2,880 distinct coordinates** — zero duplicate
pins, largest pin pile = 1 — so the baseline never collapses many addresses onto one point. Coordinates carry 1 decimal
place.

**MODELLING IMPLICATION.** The vendor answers confidently at exactly the granularity where this problem is hardest. It
also gives us no "pile-up" degradation signal to exploit (no pin is shared), which removes a tempting shortcut: we
cannot detect bad pins by looking for clusters, we can only detect them by comparing against other evidence.

### 7.3 Error against the only ground truth (n = 100)

| Threshold | Share within |
|---|---|
| ≤ 50 m | **5.0%** |
| ≤ 100 m | **9.0%** |
| ≤ 250 m | 35.0% |
| ≤ 500 m | 71.0% |
| ≤ 1,000 m | 90.0% |

| Statistic | Value |
|---|---|
| Median | **376.4 m** |
| Mean | 532.7 m |
| p25 / p75 / p90 | 170.8 / 539.4 / 839.2 m |
| Max | **4,807.7 m** |

**By stratum** — and this is the table that decides how error may be reported:

| Stratum | n | Median | p75 | p90 | <100 m | <500 m |
|---|---|---|---|---|---|---|
| `rooftop` | 1 | 25.6 m | 25.6 | 25.6 | 100% | 100% |
| `street` | 16 | 108.6 m | 129.6 | 166.3 | 43.8% | 100% |
| `locality` | 73 | **385.9 m** | 504.5 | 626.5 | 1.4% | 74.0% |
| `pincode` | 10 | **1,375.8 m** | 2,658.5 | 3,820.1 | 0% | 0% |

**By town**: T1 n=33 median 440.1 m (<100 m 9.1%) · T2 n=29 median 377.0 m (10.3%) · T3 n=38 median 339.3 m (7.9%).
**By address type**: every surveyed record is a residence, so no type comparison is possible.

**MODELLING IMPLICATION.** Three facts must be kept separate in every future report: (a) the vendor's *own* precision
label is informative — a `street` pin is 3.5× better than a `locality` pin, and a `pincode` pin is effectively a
neighbourhood — but (b) the labels are not error bars, since a `pincode` pin has a p90 of 3.8 km, and (c) strata with
n = 10 and n = 1 cannot be calibrated on this data at all. The baseline is therefore both the thing to beat and the
source of the granularity feature, and any model that cannot beat a 376 m median is not adding value.

---

## 8. Ground-Truth EDA

| Dimension | Measured |
|---|---|
| Records | **100** = 3.2% of addresses |
| By town | T3 38 · T1 33 · T2 29 |
| By address type | **residence 100** (no office, no permanent_native) |
| By source | kyc_origination 98 · skip_trace 2 |
| By vendor stratum | locality 73 · street 16 · pincode 10 · rooftop 1 |
| By official split | **train 66 · validation 19 · test 15** |
| Accounts represented | 100 distinct accounts, 1 address each |
| Ever visited | 49 of 100 |
| Ever met-someone | 38 of 100 |
| Confirmed by ≥2 distinct agents (met-someone visit) | 18 of 100 (35 of 100 were visited by ≥2 agents) |
| Distance from the declared town's mean locality centroid | median 2,740 m · max 4,430 m |
| Error of the vendor pin on this sample | median 376.4 m |

**Representativeness, honestly stated.** Stratum mix is close to the population (73/16/10/1% surveyed vs 71.2/17.5/9.5/
1.7% population). But the sample contains **zero `OUT` records** (population 237, all ungeocoded and all outside the
modelled towns), **zero office addresses** (population 464, and offices are the worst-performing type in the field —
31.0% not-traceable) and **zero permanent_native addresses** (population 226). The surveyed sample is therefore
*optimistic about the part of the book that is easiest and silent about the part that is hardest*.

**Unsafe conclusions from n = 100 (explicit list):** per-stratum accuracy for `pincode` (n=10) and `rooftop` (n=1);
per-town differences (33/29/38); comparisons smaller than the bootstrap interval; any statement about `OUT`, office or
native addresses; any absolute claim about real-world error. **All conclusions in this document are dataset-specific.**

**MODELLING IMPLICATION.** The ground truth is a *calibration and evaluation* asset, not a training asset: it is small,
skewed towards easy records, and — critically — **66 of its 100 accounts belong to the official train split**, so
training on that split and evaluating on all 100 would contaminate the measurement. The 100 records must be held out
en bloc, grouped by account, and used only with the sample size and interval quoted every time.

---

## 9. Field Visit EDA

### 9.1 Volume and allocation

| Measure | Value |
|---|---|
| Visits | **5,578** |
| Distinct addresses visited | **1,477 of 3,117 (47.4%)** |
| Distinct accounts visited | 1,339 of 2,400 |
| Visits per visited address | mean 3.78 · median 3 · p90 8 · max 9 |
| Distribution | 1: 406 · 2: 248 · 3: 154 · 4: 134 · 5: 118 · 6: 111 · 7: 107 · 8: 118 · 9: 81 |
| Visits per visited account | mean 4.17 · median 4 · max 9 |
| Addresses visited more than once | 1,071 |
| Addresses visited ≥3 times | 823 |
| Addresses confirmed by more than one agent | 957 |
| Addresses ever producing a met-someone visit | **900 (28.9% of the book)** |

### 9.2 Outcomes — two different things are mixed in one column

| Outcome | n | Share | Median dwell | Median travel start→check-in |
|---|---|---|---|---|
| `address_not_traceable` | 1,400 | **25.1%** | **1.3 min** | 18.6 min |
| `locked_premises` | 1,249 | 22.4% | 2.5 min | 9.1 min |
| `met_borrower` | 1,114 | 20.0% | 14.8 min | 10.6 min |
| `met_family` | 1,062 | 19.0% | 6.6 min | 9.5 min |
| `neighbour_says_shifted` | 455 | 8.2% | 4.3 min | 8.8 min |
| `no_such_person` | 206 | 3.7% | 3.2 min | 11.1 min |
| `cash_collected` | 92 | 1.6% | 14.5 min | 8.6 min |

Met-someone (borrower + family + cash) = **40.6%**.

**MODELLING IMPLICATION.** The column mixes **place evidence** ("the dwelling is here": `met_*`, `cash_collected`,
`locked_premises`) with **person evidence** ("who lives here": `met_*`, `no_such_person`) and one class that is neither
(`address_not_traceable`, an admission of failure). Treating them as one ordered label would both destroy information
(`locked_premises` says the door exists but nobody confirmed the household) and create the worst possible error: a
failed search becoming a label that the place is elsewhere. The vocabulary must be split into two orthogonal
dimensions before any model sees it (§21).

### 9.3 Who gets visited — and who does not

| Account dimension | Visit exposure |
|---|---|
| DPD 0–30 (n=1,025) | **25.1%** |
| DPD 31–60 (n=528) | 61.7% |
| DPD 61–90 (n=377) | 83.0% |
| DPD 91–180 (n=254) | 92.1% |
| DPD 180+ (n=216) | **96.8%** |
| Outstanding quartile | Q1 55.2% · Q2 51.7% · Q3 59.8% · Q4 56.5% |
| Portfolio | 51.4% (msme) – 60.1% (consumer_durable) |
| Address type | residence 54.5% · office 33.4% · **permanent_native 0.0%** |
| Vendor stratum | street 49.0% · locality 51.3% · rooftop 54.0% · pincode 54.7% |

Visited accounts have a **median `dpd_start` of 68 vs 15** for never-visited accounts; median outstanding ₹1,29,000 vs
₹1,17,500.

**MODELLING IMPLICATION — the most consequential EDA finding for the learning loop.** Visits are allocated by
**delinquency, not by geocoding uncertainty**: exposure varies 3.9× across risk bands while varying only 1.1× across
vendor strata. Therefore (a) any accuracy measured on visited addresses is a *conditional* number, (b) models trained
on visits learn the collections policy unless exposure weights correct for it, and (c) nothing in this dataset tells us
how the system would perform on the 52.6% of addresses nobody ever visited. This is a structural selection bias, not a
sampling nuisance.

### 9.4 Outcome correlates — where the field struggles

By vendor stratum (the cleanest signal in the data):

| Vendor stratum | Visits | Met-someone | `address_not_traceable` | Median dwell |
|---|---|---|---|---|
| `rooftop` | 94 | 43.6% | **6.4%** | 4.2 min |
| `street` | 907 | 46.6% | 13.5% | 4.0 min |
| `locality` | 3,996 | 41.3% | 24.3% | 3.5 min |
| `pincode` | 581 | 26.5% | **51.8%** | 1.9 min |

By town: T1 25.6% · T2 22.0% · T3 27.7% not-traceable. By address type: **office 32.5% met-someone / 31.0%
not-traceable** vs residence 41.0% / 24.8%.

**MODELLING IMPLICATION.** Pin quality *predicts field failure* — a `pincode`-stratum address fails more than half the
time and is abandoned in under two minutes. This is direct evidence that improving the coordinate is not a cosmetic
win: it changes what the visit can achieve.

### 9.5 Dwell and outcome — a finding that weakens the architecture

| Dwell band | Met-someone | `address_not_traceable` |
|---|---|---|
| < 1 min | **0.0%** | **97.3%** |
| 1–3 min | 2.3% | 46.1% |
| 3–10 min | 59.7% | 1.3% |
| 10–25 min | **100.0%** | 0.0% |

**MODELLING IMPLICATION (a warning).** In this dataset, dwell almost *determines* the outcome. That is a
synthetic-generator artefact, and it has three consequences: (1) any evidence-weighting model fitted here will look
near-perfect for the wrong reason; (2) therefore evidence weighting must be shipped as an **explicit rule/likelihood
table** and its learned version treated as a challenger that requires genuinely independent confirmation; (3) EDA
**invalidates the assumption** that this data can validate an evidence model's accuracy — it can only demonstrate that
the mechanism is implementable. §24.2 records this formally.

### 9.6 Free text the field writes

`remark` is populated in **100%** of visits, with **762 distinct values**, and it is multilingual:

| Remark (top values) | Visits | Language |
|---|---|---|
| `address sikkilla, tumba hudukide` | 256 | Kannada/transliterated ("wrong address, searched a lot") |
| `address nahi mila` / `address sikkilla` | 240 / 240 | Hindi / transliterated |
| `mane lock agide` / `lock laga hai` | 216 / 215 | Kannada / Hindi ("house is locked") |

**MODELLING IMPLICATION.** The remarks corroborate the outcome column and can be used to *audit* outcome coding, but
they are T3 information (written after the visit) and must never enter a location feature set. Their existence also
means an outcome is never the only textual evidence a visit carries.

`ptp_id` is populated in only 10.8% of visits and belongs to a different workflow; it was removed in cleaning (§18).

---

## 10. GPS / Trajectory EDA

### 10.1 Trail shape and quality

| Measure | Value |
|---|---|
| Points | **160,406** across 5,578 visits |
| Points per visit | median **26** · p10 7 · p90 57 · **max 80 (hard cap)** |
| Visits with < 5 points | 68 |
| Visits with ≥ 20 points | 3,525 |
| `accuracy_m` | median **10** · p75 15 · p90 21 · p99 40 · max 111 |
| Points above 100 m accuracy | 10 (0.006%) |
| Axis artefacts (x = 0 or y = 0) | **34 (0.021%)** |
| Consecutive-point distance | median 40.8 m · p90 179.5 m · max 544.9 m |
| Implied speed | median 4.84 · p95 21.09 · p99 23.06 · p99.9 25.70 · **max 32.21 km/h** |
| Steps faster than 40 km/h | **0** |
| Steps with non-positive dt | 4,842 of 154,828 steps (**3.13%** → speed undefined) |
| Trail duration (last − first point) | median 14.5 min |
| Coordinate quantisation | whole metres (integers) while check-ins and pins carry decimals |

### 10.2 Are the trails "clean"? Yes — and that limits what can be learned from them

Max implied speed is 32.2 km/h with **zero** teleports, zero check-ins off their own trail, and no repeated
coordinates across visits (5,578 unique check-ins). This dataset therefore contains **no spoofing, no GPS fraud and no
teleportation** to detect.

**MODELLING IMPLICATION.** Integrity signals can be *defined* on this data (accuracy class, point count, speed
plausibility, axis artefacts, media duplication) but **cannot be validated** here. Every integrity claim must be
measured by fault injection, and no detection rate may ever be quoted from this dataset.

### 10.3 Trail geometry: what it does and does not tell us

| Measure | Value |
|---|---|
| Check-in → **nearest trail point** | median **7.6 m** · p90 19.5 m |
| Check-in → trail **centroid** | median 108.0 m · p90 578.9 m · max 3,455 m |
| Trail bounding-box span | median 525 m · p90 3,563 m |
| Trail path length | median 1,150 m · p90 4,641 m |

| Outcome | n | Dwell | Dist. to vendor pin | Within 100 m of pin | Min dist. to trail | Trail span | Points |
|---|---|---|---|---|---|---|---|
| `address_not_traceable` | 1,400 | **1.3 min** | **195 m** | **17.6%** | 7.7 m | 616 m | 38 |
| `no_such_person` | 206 | 3.2 min | 233 m | 12.1% | 7.8 m | 490 m | 24 |
| `cash_collected` | 92 | 14.5 min | 275 m | 9.8% | 5.7 m | 540 m | 24 |
| `neighbour_says_shifted` | 455 | 4.3 min | 298 m | 14.3% | 7.6 m | 551 m | 20 |
| `met_family` | 1,062 | 6.6 min | 323 m | 11.6% | 7.6 m | 506 m | 22 |
| `locked_premises` | 1,249 | 2.5 min | 329 m | 11.0% | 8.3 m | 475 m | 15 |
| `met_borrower` | 1,114 | **14.8 min** | **346 m** | **9.2%** | 6.8 m | 538 m | 26 |

Three facts, reported separately rather than blended:

1. **Distance to the pin is failure-correlated.** The failure outcome has the *lowest* median distance to the vendor
   pin (195 m) and the *highest* share of visits within 100 m of that pin (17.6%) — while successful visits sit 323–346 m
   away (9.2–11.6% within 100 m). Anchored on the 100 surveyed records, the same test is decisive: met-someone check-ins
   are closer to the pin than to the truth only **3.2%** of the time, while `address_not_traceable` check-ins are closer
   to the pin **84.9%** of the time (median 1,603.2 m from truth, median 253.4 m from the pin).
2. **Dwell is strongly discriminative** (1.3 min on failure vs 6.6–14.8 min on success) — with the synthetic warning of
   §9.5 attached.
3. **Trail shape is not discriminative here.** The minimum check-in→trail distance is 5.7–8.3 m for *every* outcome
   (the check-in is by construction a point on the agent's own path), and trail span is slightly *larger* for failures
   (616 m) than for confirmations (475–551 m), because the trail includes the entire approach walk.

**MODELLING IMPLICATION — the distinction this project turns on.** A trail provides two completely different kinds of
information:

* **Evidence about the location**: where the agent converged, the spatial extent they searched, how far the check-in is
  from a candidate. This is legitimate place evidence when combined with a positive outcome and adequate dwell.
* **Evidence about the collection process**: accuracy class, point count, timestamps, quantisation, speed plausibility,
  axis artefacts, media reuse. This says something about the *visit*, not the *address*.

Because "agreement with the vendor pin" is failure-correlated (§10.3 fact 1), a feature of the form
*distance(check-in, pin)* is banned from the feature set: it is not a correctness signal, it is a give-up signal.

---

## 11. Agent / Collector EDA

| Attribute | Distribution |
|---|---|
| Agents | 30: tele 20 · **field 9** · voice_bot 1 |
| Language teams | hinglish 14 · kanglish 8 · english 7 · all 1 |
| Shift | day 29 · all 1 |
| Town assignment | null 21 (non-field) · T1 3 · T2 3 · T3 3 |
| Tenure (months) | min 1 · median 33 · max 64 · 1 null |
| Visits per field agent | median 626, range 583–645 — deliberately balanced |

| Agent | Visits | Addresses | Met-someone | Not-traceable | Median dwell | **Duplicate-photo rate** | Town |
|---|---|---|---|---|---|---|---|
| FA003 | 645 | 340 | 45.9% | 22.9% | 3.7 min | 0.0% | T1 |
| FA004 | 636 | 310 | 41.0% | 22.3% | 3.7 min | 0.0% | T2 |
| FA002 | 633 | 330 | 39.5% | 27.5% | 3.3 min | 0.3% | T1 |
| FA001 | 628 | 360 | 40.6% | 26.3% | 3.4 min | 0.0% | T1 |
| FA007 | 626 | 329 | 41.7% | 28.0% | 3.5 min | 0.0% | T3 |
| FA008 | 611 | 321 | 38.0% | 29.1% | 3.1 min | 0.3% | T3 |
| **FA009** | **610** | 325 | 36.2% | 25.9% | 3.1 min | **25.6%** | T3 |
| FA005 | 606 | 332 | 41.6% | 19.5% | 3.7 min | 0.2% | T2 |
| FA006 | 583 | 299 | 41.2% | 24.4% | 3.7 min | 0.0% | T2 |

Photo hashes: 5,417 distinct across 5,578 visits; the largest single hash group is 32 visits. **One agent (FA009)
carries 156 repeated photo hashes in 610 visits (25.6%); every other agent is ≤ 0.3%.** FA009's GPS is flawless:
610 distinct check-in coordinates, no implausible speed, no off-trail check-in — **a GPS-only integrity layer would
have caught nothing.**

**MODELLING IMPLICATION — three different roles, deliberately separated:**

1. **Integrity signal (yes).** Duplicate media, dwell behaviour and coordinate uniqueness give a per-collector quality
   baseline. It produces a *weight* on evidence and a monitoring alert — never an accusation, and never a zeroing of a
   visit on one signal.
2. **Monitoring / fairness signal (yes).** Per-agent flag rates must be published with their false-positive cost, since
   a wrong flag penalises an honest collector; the control band is computed from the fleet's own distribution.
3. **Model feature (no).** With 9 producing agents and 30 categories, an agent-ID feature would memorise who walked
   where, would not exist for a new agent, and would let a model learn the collections policy instead of the geography.
   Agent identity is allowed in the *evidence* model only in rolling, windowed form with an explicit unseen-agent
   bucket — and never in the location model.

---

## 12. Temporal EDA

### 12.1 The address timeline is a generation artefact

| Measure | Value |
|---|---|
| `added_date` range | 2026-04-01 → 2026-06-29 (89 days) |
| Distinct dates | **24** |
| Weekday distribution | **3,093 of 3,117 (99.2%) on a Wednesday**; the remaining 24 spread over other weekdays |
| Addresses created before the visit window | 0 |

**MODELLING IMPLICATION — EDA invalidates an assumption.** Address creation time cannot be used as a business-events
timeline: it is effectively one timestamp. Any "address age" feature derived from it is a constant, and any temporal
split based on it would be meaningless. Only visit timestamps carry real temporal structure in this dataset.

### 12.2 The visit timeline is real but shallow

| Measure | Value |
|---|---|
| Range | 2026-04-01 → 2026-06-29 (**89 days**) |
| Weekday mix (0 = Mon) | 949 · 866 · 942 · 968 · 928 · 925 · **0 (no Sunday visits)** |
| Check-in hour mix | 09: 165 · 10: 1,613 · 11: 1,729 · 12: 1,306 · 13: 588 · 14: 162 · 15: 15 |
| Visits per week | 293 · 430 · 444 · 443 · 432 · 444 · 438 · 434 · 430 · 436 · 426 · 416 · 440 · 72 (partial weeks at each end) |
| Gaps between active visit days | median 1 day · max 2 days · 13 of 90 days have no visit |
| Lead time, address creation → **first** visit | median **14 days** · p10 2 · p90 66 · negative: 0 |
| Longest observation history for one address | **9 visits** |
| First-visit month | April 989 · May 291 · June 197 |

**MODELLING IMPLICATION.** Three consequences. (a) ~83% of check-ins fall between 10:00 and 13:00 — a visit-window
feature is legitimate and stable. (b) The window is **too short and too uniform to contain real drift**, so any
dynamic-learning experiment here is necessarily a **replay simulation**, labelled as such. (c) The history depth is
≤ 9 observations per address, which is enough to test warm-vs-cold behaviour on a small subset but not to learn
long-horizon decay curves.

### 12.3 Information availability, mapped to the data (T0–T4)

| Stage | What exists | Where it lives in the official data |
|---|---|---|
| **T0 — before geocoding** | the written address, its declared town and type, the vendor pin *and its stated stratum*, the gazetteers, account context | `addresses`, `towns`, `localities`, `landmarks_poi`, `baseline_geocodes`, `accounts` |
| **T1 — during candidate generation** | our own candidate set: any derived positions, granularities, similarity scores | derived only (no official table) |
| **T2 — during the visit** | check-in coordinate, per-point accuracy, dwell so far, live trail, media at capture | `field_visits` (check-in, `gps_accuracy_m`, `dwell_s`), `visit_gps_points` |
| **T3 — after the visit** | the outcome, the free-text remark, the photo hash as filed | `field_visits.outcome`, `.remark`, `.photo_hash` |
| **T4 — later knowledge** | surveyed coordinates, later visits, later belief state | `surveyed_addresses`, subsequent rows of `field_visits` |

**MODELLING IMPLICATION.** The dataset supplies a clean four-stage separation, which is exactly what a leakage-safe
pipeline needs. The trap is that `field_visits` holds T2 and T3 columns side by side in one table: a naive feature
build that reads the table will pick up T3 columns for a T2 decision. Stage tags must be attached **per column**, not
per table (§22).

---

## 13. Train/Validation/Test EDA

| Measure | train | validation | test |
|---|---|---|---|
| Accounts (official) | 1,680 | 360 | 360 |
| Addresses | 2,175 | 483 | 459 |
| Visits | 3,896 | 894 | 788 |
| **Surveyed ground truth** | **66** | **19** | **15** |
| Town mix (T1/T2/T3/OUT) | 664/639/707/165 | 139/163/141/40 | 139/150/138/32 |
| Address type (residence/office/native) | 1,699/320/156 | 364/81/38 | 364/63/32 |
| Vendor stratum (locality/street/pincode/rooftop) | 1,416/357/203/34 | 318/89/29/7 | 318/58/42/9 |

**Checks performed:**
* Exact duplicate rows in `splits.csv`: none. Every account appears exactly once.
* Normalised-duplicate address groups spanning more than one split: **3 groups covering 6 rows** — i.e. the same
  building written twice can straddle train and test.
* Normalised text appearing in more than one town: **0 groups** (text cannot leak across towns here).
* Same-account leakage: impossible by construction (splits are account-level).
* **Temporal leakage: the official split is time-blind.** Addresses and visits span the same 89 days in all three
  splits; there is no time cut at all.
* **Ground-truth membership: 66 of the 100 surveyed records are in the *train* accounts.** Evaluating the headline
  metric on all 100 while training on the official train split would score partly on training entities.

**MODELLING IMPLICATION — and an explicit correction to the protocol.** The official split is *necessary but not
sufficient*. Three additions are required, none of which modifies the official file:

1. **A group key** `hash(account_id, normalised_address_text, town_id)` so that the 3 duplicate-text groups (and any
   near-identical siblings) cannot straddle a split.
2. **A time-aware ledger** for any experiment that involves visits: each record carries an `as_of`, and training rows
   must have `observed_at < as_of`.
3. **A reserved evaluation set** consisting of the 100 surveyed addresses, used **only** as an independent evaluation
   set and never trained on — including that none of their 100 accounts may be used to fit the model whose performance
   they measure. Any experiment that trains on the official train split and reports on the surveyed sample must state
   that 66 of the accounts are shared and therefore treat the number as *indicative*, not held out.

---

## 14. Missing Values

### 14.1 Classification (not just counting)

| Field | Missing | Classification | Decision |
|---|---|---|---|
| `addresses.*` | 0% | complete | use as-is |
| `accounts.salary_credit_day` | **68.2%** | **not applicable** (only salaried accounts have a salary credit day) | leave null; never impute |
| `accounts.ability_to_pay_estimate` | **30.3%** | **genuinely unknown** (the estimate was never produced) | leave null + add `has_apt_estimate` if ever used |
| `agents.town_id` | **70.0%** | **not applicable** (tele/voice channels have no town) | keep null; do not back-fill from behaviour |
| `agents.tenure_months` | 3.3% (1 cell) | genuinely unknown (new joiner) | leave null; listwise drop in the tiny roster if needed |
| `baseline_geocodes.*` | **237 addresses absent (7.6%)** | **structurally missing** — the vendor declines to place out-of-town records | keep absent; encode as a *state* (no pin), never impute |
| `field_visits.ptp_id` | **89.2%** | **not applicable** to this problem statement | column removed in cleaning |
| `field_visits.photo_hash` | 0% | — (if it were missing: process failure) | keep; a non-zero rate would be an integrity signal |
| `field_visits.remark` | 0% | — | T3 text; used for audit only |
| `visit_gps_points.*` | 0% | — | if accuracy were missing: potentially corrupted → weight reduction |
| `surveyed_addresses` (as coverage of the book) | 96.8% of addresses | **structurally missing by design** — a survey samples, it does not cover | never impute; treat as an evaluation sample |

### 14.2 Policy applied (five-way rule)

| Action | When | Applied to |
|---|---|---|
| **Leave null** | absence carries meaning | no vendor pin (out-of-town), `agents.town_id` for non-field channels |
| **Add an indicator** | absence changes the decision | `pin_unknown`, `no_digit`, `no_separator`, `no_locality_match`, `trail_missing` |
| **Impute** | only for numeric model inputs where absence is noise, and only with a statistic fitted on training rows | `gps_accuracy_m` (median-of-visit only if a point is missing), and nothing else in this dataset |
| **Derive** | the fact lives in another table | visit outcome → place/person dimensions; trail → agreement and extent |
| **Exclude** | the column belongs to another workflow or leaks | `ptp_id`; account fields from location features; outcome from T0 features |

**MODELLING IMPLICATION.** There is no "fill the nulls" step in this pipeline, because every null here is informative:
7.6% of addresses are ungeocodable *by the vendor's own choice*, 68.2% of accounts structurally lack a salary credit
day, and 70% of agents structurally lack a town. Imputing any of them would invent data and destroy a state the design
depends on.

---

## 15. Duplicates and Entity Resolution

### 15.1 What was found

| Check | Result |
|---|---|
| Exact duplicate rows, any table | **0** (all 11 tables) |
| Duplicate key values (all `*_id` columns) | **0** — every claimed key is unique |
| Duplicate address text (exact) | 3 |
| Duplicate address text (normalised) | **5 groups / 10 rows / 5 different account pairs** |
| Near-duplicate text pairs (J ≥ 0.80) | **238** (228 = same template, different numbers; 10 = similar wording) |
| Same text, different accounts | 5 groups — legitimate repeat buildings |
| Normalised text in more than one town | 0 groups |
| Duplicate `(town, pincode)` pairs | 24 (2–5 localities share a pincode) |
| Duplicate `(town, landmark name)` pairs | 42 groups covering all 240 rows |
| Duplicate vendor pin coordinates | **0** |
| Duplicate check-in coordinates | **0** (5,578 unique) |
| Duplicate landmark coordinates | 0 |
| Duplicate `(visit_id, seq)` | 0 |

### 15.2 Interpretation — three different things that all look like "duplicates"

1. **Multiple accounts at one building** (the 5 normalised groups, 10 rows): *legitimate repeated entity*. Two
   borrowers listed at `Shivaji Nagar, Devgarh Nagar - 970202`, etc. These must be **grouped for split integrity** and
   **linked (not merged) in memory**, so that a visit to one account's record informs the shared place.
2. **Same template, different numbers** (228 of the 238 near-duplicate pairs): *not duplicates at all* — different
   villages/houses written with identical phrasing. Any de-duplication based on similarity would delete real addresses.
3. **Repeated landmark names** (42 groups): *data limitation*, not error. A name is not an identity; matching must be
   town- and type-scoped and coordinate-aware.

**MODELLING IMPLICATION.** The leakage risk in this dataset is small but real (3 duplicate groups straddling splits,
6 rows) and the false-merge risk is large (238 near-duplicate pairs that are different places). Grouping therefore uses
an *exact, normalised* key — never a similarity threshold — and memory linking uses evidence (resolved locality +
house number + coordinate proximity), with an explicit `AMBIGUOUS_GROUP` state rather than a guess.

---

## 16. Outliers and Anomalies

Every anomaly below is identified, explained, given a disposition, and **kept in the raw file**.

| # | Anomaly | n | Explanation | Disposition |
|---|---|---|---|---|
| 1 | GPS points with x = 0 or y = 0 | **34 (0.021%)** | device wrote a placeholder when it had no fix | **exclude from evidence**; kept in raw |
| 2 | Visits with < 5 trail points | 68 | very short or interrupted tracking | keep; lower evidence weight (low point count) |
| 3 | GPS accuracy > 100 m | 10 (0.006%) | urban canyon / weak fix | keep; reduce weight, never drop silently |
| 4 | Implied speed > 40 km/h | **0** | — (max observed 32.2 km/h) | no action; the check stays as a feature |
| 5 | Steps with non-positive Δt | 4,842 of 154,828 (3.13%) | repeated device timestamps | speed undefined there; excluded from speed statistics only |
| 6 | Dwell < 60 s | **443 (7.9%)** | check-in and immediate departure | keep; weak evidence for any place claim |
| 7 | Dwell > 2 h | 0 | — (hard ceiling at 1,495 s) | no action |
| 8 | Negative travel time (check-in before start) | **0** | — | check retained as a validity test |
| 9 | Check-ins outside a 6 km town envelope | **0** (max 4,544 m) | — | town containment holds here |
| 10 | Vendor pins > 6 km from their town centre | **0** (max 4,608 m) | — | check retained |
| 11 | Addresses with no digit | 9 (0.29%) | no dwelling identifier can exist | flag `no_digit`; tier capped at locality/street |
| 12 | Addresses with no separator at all | 24 (0.8%) | single unpunctuated blob | flag `no_separator`; still resolvable by tokens |
| 13 | 6-digit tokens matching no known pincode | **260 (8.9% of tokens)** | plot number, phone fragment, or out-of-area pincode | flag `pin_unknown`; never parsed as fact |
| 14 | Locality match contradicted by the record's own pincode token | **150 (7.9% of matched)** | data entry error or genuine mobility | flag `pin_conflict`; pincode stays soft evidence |
| 15 | `address.town_id` ≠ `account.town_id` (the 237 `OUT` records) | **237** | borrower lives/works outside the serviced towns | flag `outside_town`; first-class refusal state |
| 16 | Duplicate photo hashes by one agent | **156 visits (25.6% of FA009's visits)** | reused media | integrity weight reduction + monitoring; never an automatic rejection of the visit's outcome |
| 17 | Dwell↔outcome near-determinism (§9.5) | 5,578 | synthetic generator artefact | **structural warning**: do not read evidence-model performance from this data |
| 18 | `added_date` collapsed onto one weekday (§12.1) | 3,093 | generation artefact | exclude as a temporal feature |

**MODELLING IMPLICATION.** Nothing is deleted except the 34 axis artefacts from evidence use; everything else is
flagged. This matters because an outlier here is usually a *fact about the process* (a weak fix, a hurried visit, an
outside-town borrower) and the process is exactly what the evidence layer must model. The two genuinely structural
anomalies (17, 18) are not data problems at all but **limits on what may be concluded from this dataset** — they are
carried into §24.2 and into the leakage rules.

---

## 17. Data Quality Findings

| Table | Rows | Mean null % | Exact dup rows | Key integrity | Verdict |
|---|---|---|---|---|---|
| accounts | 2,400 | 4.93 | 0 | ok | high quality; nulls are structural |
| addresses | 3,117 | 0.00 | 0 | ok (4th town value `OUT` is intentional) | high quality; text is the challenge |
| agents | 30 | 12.22 | 0 | ok | tiny; nulls structural |
| baseline_geocodes | 2,880 | 0.00 | 0 | ok | complete for what it covers; 237 uncovered |
| field_visits | 5,578 | 5.94 | 0 | ok | rich; one irrelevant column, mixed T2/T3 |
| landmarks_poi | 240 | 0.00 | 0 | ok | complete but semantically impoverished (14 names) |
| localities | 36 | 0.00 | 0 | ok | complete; 1 name repeated across towns |
| splits | 2,400 | 0.00 | 0 | ok | complete; time-blind |
| surveyed_addresses | 100 | 0.00 | 0 | ok | complete but very small and skewed |
| towns | 3 | 0.00 | 0 | ok | complete; `address_style` is redundant with `town_id` |
| visit_gps_points | 160,406 | 0.00 | 0 | ok on `(visit_id, seq)` | complete; integer-quantised; 0.02% placeholders |

**Strengths.** No orphaned foreign keys anywhere; no duplicated keys; no duplicated rows; no negative travel times; no
teleporting trails; complete coverage of the fields the design depends on; a documented, consistent outcome vocabulary.

**Weaknesses (ranked in the final section):** one very small ground-truth sample that excludes the hardest records;
structural selection bias in visit allocation; an outcome column that mixes place and person information; a landmark
table that cannot identify anything by name; a duplication pattern in text that punishes similarity-based de-duplication;
and two synthetic artefacts (dwell↔outcome, collapsed `added_date`) that cap what may be concluded.

---

## 18. Cleaning Strategy

**Principles:** (1) raw official data is read-only, always; (2) every transformation is reversible — the raw value is
preserved in a `*_raw` column; (3) nothing spatial is ever "corrected" — suspicious geometry is flagged; (4) no label is
ever invented or re-typed; (5) every rule is logged with input, condition, effect, row counts and risk; (6) outputs go
to `data/cleaned/`.

| Rule | Input | Condition | Transformation | Rows affected | Why | Risk | Preserved / lost |
|---|---|---|---|---|---|---|---|
| **C01** text normalisation | `addresses.address_text` | always | NFKC; lowercase; punctuation collapsed to single spaces; keep Latin + Devanagari + Kannada; 13 abbreviation expansions (`rd→road`, `h.no→house`, `nr→near`, `nagar` variants…) | 3,117 | matching needs a stable form | over-normalising could merge distinct tokens | preserved: `address_text_raw`; lost: punctuation layout (also kept as flags) |
| **C02** `flag_no_digit` | address text | no digit present | boolean | 9 | a dwelling identifier cannot exist | none | nothing lost |
| **C03** `flag_no_separator` | address text | no comma, slash or hyphen | boolean | 24 (also: 777 (24.9%) have no comma — recorded, not flagged) | marks records where the structural tail is absent | none | nothing lost |
| **C04** `flag_pin_in_text` | address text | 6-digit token present | boolean + extracted token | 2,907 | pincode-shaped evidence is common and useful | none | token kept as *string*, never as an integer key |
| **C05** `flag_pin_unknown` | address text + gazetteer | token matches no known pincode | boolean | 260 | prevents a plot number from being read as a pincode | none | nothing lost |
| **C06** `flag_outside_town` | `town_id` | value not in `towns.csv` | boolean | 237 | makes the refusal state explicit | none | nothing lost |
| **C07** `flag_dup_text` | normalised text | duplicated elsewhere | boolean | 10 | protects split integrity | none | rows kept — deletion would hide the leak |
| **C08** span extraction | normalised text | marker present | 6 boolean spans: lane/block/cross/house/relation + gazetteer-token | 3,117 | gives the ranker interpretable text features | rules can under-fire on odd phrasings (measured: the marker-anchored and any-numeric-token definitions of a house number differ by 31.7 points) | nothing lost; `house_no` kept as string |
| **C09** outcome split into two dimensions | `field_visits.outcome` | always | `outcome_place_flag` ∈ {place_positive, place_weak_positive, place_indeterminate}; `outcome_person_flag` ∈ {positive, negative, indeterminate} | 5,578 | one column carries two different facts (§9.2) | mis-assignment would mis-weight evidence — the mapping is documented and fixed by rule | original `outcome` preserved |
| **C10** `flag_short_dwell` | `dwell_s` | < 60 s | boolean | 443 | weak place evidence | none | kept and used as a weight |
| **C11** `flag_implausible_dwell` | `dwell_s` | > 12 h | boolean | 0 | guards against app-left-open records | none | kept as a check |
| **C12** `flag_negative_travel` | start/check-in timestamps | negative | boolean | 0 | clock-skew guard | none | check retained |
| **C13** `flag_negative_outcome` | outcome | = `address_not_traceable` | boolean | 1,400 | marks evidence that can never relocate a coordinate by itself (F2.1/D36) | none | kept; used for suspicion and re-verification |
| **C14** drop `ptp_id` | `field_visits` | always | column removed | 5,578 (col) | belongs to a different workflow; 89.2% null | loses a link that this problem statement never uses | raw file retains it |
| **C15** GPS placeholder removal | `visit_gps_points` | x = 0 or y = 0 | row excluded from **evidence use** | **34 dropped (0.021%)** | placeholders carry no location | if a legitimate point ever sat on an axis it would be dropped — impossible in a local metric plane with multi-km extent, and the count is logged | raw file retains the rows |
| **C16** trail geometry derivation | `visit_gps_points` | per visit | n_points, accuracy median/p90, span, path length, endpoints, two check-in agreement measures | 5,578 visits | converts a trail into features | geometry is evidence, **not a truth test** (§10.3) | raw points retained |
| **C17** (deliberately **not** executed) transliteration of Devanagari/Kannada | address text | — | — | 262 | transliteration loses the evidence that the record is multi-script and would create a second, silently different string | a transliterated variant may be *added* as a parallel column later and tested as an ablation | script markers retained |
| **C18** (deliberately **not** executed) fuzzy de-duplication of near-identical texts | address text | J ≥ 0.80 | — | 238 pairs | 228 of the 238 pairs are *different places with the same template*; merging them would delete real addresses | handled instead by an exact normalised group key + evidence-based linking | all rows retained |
| **C19** (deliberately **not** executed) outlier deletion (dwell, accuracy, speed) | visits, GPS | any | — | 443 + 10 + 0 | these are facts about the collection process, which the evidence layer models | deleting them would hide exactly the signal the system needs | retained as flags/weights |

**MODELLING IMPLICATION.** Cleaning deliberately stops before interpretation. It produces a **flat, faithful, flagged**
representation plus spans; turning text into structured entities is a *preprocessing* concern (§20) with its own
scoring and its own fallbacks, so that the parser can be swapped or removed without re-cleaning the data.

---

## 19. Cleaning Results

Executed by `python3 tools/clean_official.py`; every rule writes a row to `data/cleaned/cleaning_log.csv`
(15 rules; `rows_in → rows_out`, drop count and a note). Verbatim log:

| Table | Rule | rows_in | rows_out | dropped | Note |
|---|---|---|---|---|---|
| addresses | normalise text (NFKC, case, punct, abbrev) | 3,117 | 3,117 | 0 | raw preserved in `address_text_raw` |
| addresses | `flag_no_digit` | 3,117 | 3,117 | 0 | 9 rows flagged — no digit at all |
| addresses | `flag_no_separator` | 3,117 | 3,117 | 0 | 24 rows flagged (777 have no comma) |
| addresses | `flag_pin_unknown` | 3,117 | 3,117 | 0 | 260 rows flagged |
| addresses | `flag_outside_town` | 3,117 | 3,117 | 0 | 237 rows flagged |
| addresses | `flag_dup_text` | 3,117 | 3,117 | 0 | 10 rows flagged |
| addresses | rule-based span extraction | 3,117 | 3,117 | 0 | 5 markers + gazetteer token |
| visits | derive place/person evidence flags | 5,578 | 5,578 | 0 | outcome split into two dimensions |
| visits | `flag_negative_travel` | 5,578 | 5,578 | 0 | 0 rows flagged |
| visits | `flag_short_dwell` | 5,578 | 5,578 | 0 | 443 rows flagged |
| visits | `flag_implausible_dwell` | 5,578 | 5,578 | 0 | 0 rows flagged |
| visits | `flag_negative_outcome` | 5,578 | 5,578 | 0 | 1,400 rows flagged |
| visits | drop `ptp_id` column | 5,578 | 5,578 | 0 | 89.2% null; different workflow |
| gps_points | drop axis artefacts (x=0 or y=0) | 160,406 | **160,372** | **34** | placeholders; raw file untouched |
| trail_features | per-visit trail geometry | 5,578 | 5,578 | 0 | median 26 points/visit |

**Artefacts produced**

| File | Rows | Contents |
|---|---|---|
| `data/cleaned/addresses_clean.csv` | 3,117 | raw text + normalised text + 7 flags + 5 spans + `text_norm` |
| `data/cleaned/visits_clean.csv` | 5,578 | visits with two-dimension outcome flags, travel time, 4 validity flags, `ptp_id` removed |
| `data/cleaned/gps_points_clean.csv` | 160,372 | trail points minus axis artefacts, with `step_m` and `speed_kmh` |
| `data/cleaned/trail_features.csv` | 5,578 | per-visit geometry (points, accuracy, span, path, endpoints, two agreement measures) |
| `data/cleaned/cleaning_log.csv` | 15 | the log above |

**Totals:** 15 rules applied; **34 rows excluded from evidence use (0.021% of GPS points)**; 0 rows dropped anywhere
else; **0 coordinates moved; 0 labels invented; 0 text values overwritten.**

**MODELLING IMPLICATION.** The cleaning stage is intentionally almost lossless: 99.979% of all rows survive, and the
handful that do not are sensor placeholders. This is possible because the dataset's defects are *semantic*, not
mechanical — the work is in interpretation (preprocessing) and in evidence weighting, not in scrubbing.

---

## 20. Preprocessing Pipeline

**The three stages, kept strictly apart:**

| Stage | Question it answers | Output | Nature |
|---|---|---|---|
| **Cleaning** (§18–19) | "Is this value well-formed and faithful?" | flat, flagged, reversible columns | deterministic, no interpretation |
| **Preprocessing** (§20) | "What does this record *mean* in canonical entities?" | typed fields, resolved entities, candidates, features | deterministic rules + documented fallbacks, versioned by `rule_version` |
| **Feature engineering** (§21) | "Which of those facts may a model consume, at which stage?" | feature matrices with a leakage receipt | stage-tagged, fit-on-train-only |

**Order of operations (fixed; changing it is a new `rule_version`):**

```
text_norm ─► span extraction ─► entity resolution (rule → pattern → optional statistical) ─► gazetteer match
          ─► candidate generation (T0/T1) ─► candidate features ─► [as-of join for warm mode]
          ─► sample weighting (exposure) ─► training tensor / scoring request
```

**Two hard boundaries inside that order:**

1. **Nothing is fitted on validation or test.** Normalisation vocabulary, similarity thresholds, scaling statistics and
   calibration parameters are computed on training rows only and applied outward.
2. **The as-of join is a point-in-time join.** Warm features may read only observations with `observed_at < as_of`; a
   lookup of a "current" state is forbidden (it is the classic leak that makes a memory look prescient).

### 20.1 Text

| Step | Decision | Justification from the data |
|---|---|---|
| Unicode normalisation | NFKC; collapse whitespace/punctuation; preserve Devanagari (154 rows) and Kannada (108) as distinct scripts | 8.41% of records are multi-script; destroying the script destroys a real signal |
| Tokenisation | whitespace + punctuation split on the normalised form; digits kept as tokens | median 12 tokens, 95.2% carry a structural hyphen tail |
| Digit handling | digits preserved verbatim; a 6-digit token is extracted *as a string* and tested against the gazetteer | 8.9% of such tokens match nothing; treating them as keys would create false joins |
| Abbreviation normalisation | 13 fixed expansions (`rd`, `h.no`, `ngr`, `nr`, `opp`, …) | 31.2% of records use `no.`, 22.8% `rd`, 19.0% `blk` |
| Character n-grams | char-3-grams over the normalised string | misspellings dominate the tail (`navanagora`, `kavripura`, `communitty`) |
| Lexical features | token counts, digit counts, separator counts, script flags | cheap and stable (see §21) |
| Span extraction | 5 rule spans + gazetteer-token span | house number 67.7% (marker-anchored) / 99.4% (any numeric token), cross 16.7%, gali 22.5%, main 20.5% |
| Landmark features | town-scoped phrase presence + landmark **type** | names are not unique (14 names / 240 rows), types are |

### 20.2 Geographic

| Step | Decision | Justification |
|---|---|---|
| Coordinate handling | coordinates stay in the dataset's **local metric plane**; no lat/lon, no projection is assumed | every table is in the same plane (multi-km extents, axis-aligned); inventing geographic coordinates would be a fabrication |
| Distances | Euclidean metres in the plane; `log1p` before scaling | all coordinate ranges are within ±4.5 km |
| Town/locality relationships | town-scoped matching; `(town_id, locality_name)` keys | `Nehru Colony` exists in two towns |
| Candidate distances | distance to town centre, distance between candidates, distance to matched locality centroid | the discriminating structure is *relative* position |
| Spatial indexing | a plain in-memory KD-tree/R-tree over ≤ 300 points per town | the index is tiny; a spatial database would be infrastructure without a purpose |

### 20.3 Field visit

| Group | Features | Stage | Rule |
|---|---|---|---|
| Dwell | dwell seconds, dwell band, `is_short_dwell` | T2/T3 | banded, because the raw distribution is generator-shaped |
| GPS quality | accuracy median/p90 per visit, point count, `low_accuracy` rate | T2 | weight inputs, never truth |
| Trajectory | span, path length, endpoint-to-check-in distance, min check-in→trail distance | T2 | describes the *process* (see §10.3) |
| Travel | start→check-in travel seconds, travel band | T2 | 0 negative values; median 12.1 min |
| Integrity | media-duplicate rate, coordinate reuse, speed plausibility, axis artefacts | T2 | weight inputs with reason codes |
| Evidence weights | `w_place`, `w_person` | T3 | two dimensions, never summed |

### 20.4 Categorical

One-hot for low-cardinality categories (`arm`, `granularity`, `town_id`, `address_type`, `language_team` where used);
ordinal for ordered granularity (town < locality < street < rooftop); **unknown bucket for every categorical** so an
unseen value cannot break scoring; **no target encoding anywhere** (with 100 ground-truth records, target encoding
leaks through folds).

### 20.5 Numeric

`log1p` on distances and durations; robust scaling fitted on training rows only; clipping at training-set percentiles
with the clip recorded; **no imputation of structurally missing values**; explicit missing indicators where absence
changes a decision (§14.2).

**MODELLING IMPLICATION.** The preprocessing pipeline is deliberately *small and checkable*: about 40 features, all of
which can be traced to a measured property of this dataset. Where the data offers no evidence (landmark identity, deep
history, real drift), the pipeline does not manufacture a substitute.

---

## 21. Feature Engineering

Every feature below is computable from the official tables alone. "Stage" uses the T0–T4 map of §12.3.

| # | Feature | Source | Stage | Type | Missing policy | Notes |
|---|---|---|---|---|---|---|
| 1 | `text_len`, `token_count` | addresses | T0 | numeric | n/a | median 67 / 12 |
| 2 | `digit_count`, `has_digit` | addresses | T0 | numeric/bool | n/a | 9 records have none |
| 3 | `comma_count`, `slash_count`, `hyphen_count`, `has_separator` | addresses | T0 | numeric/bool | n/a | 24.9% have no comma |
| 4 | `script_devanagari`, `script_kannada`, `script_latin` | addresses | T0 | bool | n/a | 154 / 108 / all |
| 5 | `span_lane`, `span_block`, `span_cross`, `span_house`, `span_relation` | addresses | T0 | bool | n/a | rule-based, auditable |
| 6 | `house_number_present` (marker-anchored **and** any-numeric-token variants) | addresses | T0 | bool | n/a | definitions differ by 31.7 points (67.7% vs 99.4%) → keep both |
| 7 | `pin_in_text`, `pin_unknown`, `pin_conflict_with_locality` | addresses + localities | T0 | bool | indicator | 2,907 / 260 / 150 |
| 8 | `locality_match_id`, `locality_match_score`, `n_locality_matches` | addresses + localities | T0 | categorical+numeric | unmatched → its own bucket | 61.1% exact-match; 0 ambiguous on exact match |
| 9 | `landmark_type_in_text`, `landmark_phrase_present` | addresses + landmarks | T0 | bool | indicator | 25.2% mention a landmark |
| 10 | `town_declared`, `is_outside_town` | addresses | T0 | categorical/bool | n/a | 237 records outside |
| 11 | `char3_jaccard(text, locality_name)`, `token_jaccard`, `edit_ratio` | addresses + localities | T0 | numeric | 0 when unmatched | three similarity views keep different failure modes visible |
| 12 | `vendor_stratum` (rooftop/street/locality/pincode/none) | baseline_geocodes | T0 | ordinal | `none` for the 237 | the vendor's own claim — context, not truth |
| 13 | `vendor_present` | baseline_geocodes | T0 | bool | n/a | 92.4% |
| 14 | `candidate_arm`, `candidate_granularity`, `candidate_rank` | derived | T1 | categorical/ordinal | n/a | monotone constraints apply |
| 15 | `dist_to_town_centre`, `dist_between_candidates` | derived | T1 | numeric | n/a | plausibility |
| 16 | `n_candidates` | derived | T1 | numeric | n/a | 1–4 with the current arms |
| 17 | **T2 only:** `dwell_s`, `dwell_band`, `is_short_dwell` | field_visits | T2 | numeric/bool | n/a | 443 below 60 s |
| 18 | **T2 only:** `checkin_x/y`, `gps_accuracy_m`, `accuracy_class` | field_visits | T2 | numeric/ordinal | n/a | 68%-confidence semantics |
| 19 | **T2 only:** `trail_points`, `trail_span_m`, `trail_path_m`, `checkin_to_trail_min_m` | visit_gps_points | T2 | numeric | `trail_missing` indicator | 68 visits with < 5 points |
| 20 | **T2 only:** `travel_s`, `travel_band` | field_visits | T2 | numeric | n/a | median 12.1 min |
| 21 | **T2/T3:** `outcome_place_flag`, `outcome_person_flag` | field_visits | T3 | ordinal | n/a | the two dimensions of §9.2 |
| 22 | **T3 only:** `w_place`, `w_person`, `integrity_reasons[]` | derived | T3 | numeric/list | n/a | policy version recorded |
| 23 | as-of memory: `prior_confirmations`, `prior_attempts`, `belief_age_days`, `support_spread_m` | derived from field_visits < as_of | T1 (warm) | numeric | 0 for cold | strictly point-in-time |
| 24 | exposure weight `1/P(visit)` | accounts (T0 covariates only) | training only | numeric | n/a | never a scoring feature |

**Explicitly excluded from every model:** `surveyed_x/y` (labels), `remark` (T3 prose), `ptp_id` (other workflow),
`agent_id` in production location scoring, all `accounts.*` fields from location features, `photo_hash` value itself
(only its duplicate *rate* is used, as an integrity input), and any feature computed with `observed_at ≥ as_of`.

**MODELLING IMPLICATION.** The feature set is small on purpose: 24 families, of which the last six are visit-derived
and therefore unavailable at T0/T1. With 100 ground-truth records and ~25 candidates per address, a 50-feature model
would fit the generator's quirks perfectly and generalise nowhere. The features that remain are those the EDA showed to
be *structural*: text spans, gazetteer match strength, vendor stratum, candidate geometry, and (only after a visit)
dwell/outcome/integrity.

---

## 22. Leakage Analysis

### 22.1 The five stages, restated as an allowance table

| Stage | May use | May **not** use |
|---|---|---|
| **T0** pre-geocoding | address text, declared town/type, gazetteers, vendor pin + stratum, account context for visit pricing only | any candidate we generated, any visit data, any ground truth |
| **T1** candidate generation | T0 + our candidate set and its geometry | any T2/T3/T4 information |
| **T2** in-visit | T0+T1 + this visit's check-in, live trail, dwell-so-far, live accuracy | this visit's outcome, any later visit, any belief derived from this visit |
| **T3** post-visit | everything above + this visit's outcome and integrity weight | other visits' outcomes when placing *this* visit earlier in time |
| **T4** later knowledge | surveyed coordinates, later visits, belief history | — (evaluation and slow-loop learning only) |

### 22.2 Candidate feature × allowance matrix (the audit the commission asked for)

| Feature family | Source | Stage | Cold start | Warm start | Evidence model | Retraining | Potential leakage? | Why / why not |
|---|---|---|---|---|---|---|---|---|
| Text length, tokens, digits, separators, script flags | addresses | T0 | ✔ | ✔ | — | ✔ | **No** | intrinsic to the query string |
| Rule spans, house-number presence | addresses | T0 | ✔ | ✔ | — | ✔ | **No** | computed from the query text |
| Pincode token, `pin_unknown`, `pin_conflict` | addresses + localities | T0 | ✔ | ✔ | — | ✔ | **No** | text evidence; contradiction is a recorded fact |
| Locality match id/score, similarity trio | addresses + localities | T0 | ✔ | ✔ | — | ✔ | **No** | gazetteer is static reference data |
| Landmark type/phase presence | addresses + landmarks | T0 | ✔ | ✔ | — | ✔ | **No** | static reference |
| `town_declared`, `is_outside_town` | addresses | T0 | ✔ | ✔ | — | ✔ | **No** | declared at ingest |
| Vendor pin coordinates + stratum | baseline_geocodes | T0 | ✔ | ✔ | — | ✔ | **No** for training (it is an input, not an outcome) — but **yes** if used as a *label* | the pin is a vendor *claim*; using it as the training target would teach the model to reproduce the vendor |
| Candidate geometry (`arm`, granularity, distances) | derived | T1 | ✔ | ✔ | — | ✔ | **No** | generated at scoring time from T0 inputs |
| `dist(check-in, vendor pin)` | visits | T2 | ✘ | ✘ | **prohibited** | ✘ | **Yes — subtle and fatal** | measured failure-correlated (§10.3): failures land 195 m from the pin; it would teach the model to prefer wrong places |
| Dwell, dwell bands | field_visits | T2 | ✘ | ✘ | ✔ | ✔ | **No** for evidence; **contaminated** as a *validation* signal (§9.5) | post-hoc discriminative power here is a generator artefact |
| Trail geometry features | visit_gps_points | T2 | ✘ | ✘ | ✔ | ✔ | **No** | process description |
| Check-in coordinate | field_visits | T2 | ✘ | ✘ | ✔ | ✔ | **No if staged**; **yes if** used to place the same visit's pre-visit decision | must carry `observed_at` |
| `outcome`, `outcome_place_flag`, `outcome_person_flag` | field_visits | T3 | ✘ | ✘ | as *label/weight*, never as input to the same visit's placement | ✔ with lag | **Yes if mis-staged** | the classic leak: an outcome that arrived after the decision |
| `remark`, `photo_hash` value | field_visits | T3 | ✘ | ✘ | integrity only (duplicate rate) | ✘ | **Yes** if used as a feature | prose and media are post-visit |
| Integrity weights `w_place`, `w_person` | derived | T3 | ✘ | ✘ | ✔ | ✔ | **No** if policy-versioned | re-derivable from immutable observations |
| As-of memory features | visits before `as_of` | T1 (warm) | ✘ | ✔ | ✔ | ✔ | **Yes** unless the join is strictly `observed_at < as_of` | "current state" lookups are the canonical leak |
| Exposure weights | accounts | training only | ✘ | ✘ | ✘ | ✔ | **No** if computed from T0 covariates of training rows only | using outcome-correlated covariates would re-import the bias |
| `surveyed_x/y` | surveyed_addresses | T4 | ✘ | ✘ | ✘ | **never** | **Yes** — it *is* the label | held out en bloc, all 100 accounts |
| `ptp_id` | field_visits | — | ✘ | ✘ | ✘ | ✘ | n/a | different workflow; removed |
| `accounts.*` fields | accounts | T0 | pricing only | pricing only | ✘ | ✘ | **Yes** for location models | they encode *why* a visit occurred, i.e. the selection mechanism |
| `agent_id` | agents | T0 | ✘ | ✘ | windowed only | limited | **Yes** | memorises the collector; absent for new agents |
| `added_date` | addresses | T0 | ✘ | ✘ | ✘ | ✘ | **Yes** (proxy for split membership) | collapsed to one weekday (§12.1) |

### 22.3 Strictly prohibited (and how each is prevented)

| Prohibition | Prevention |
|---|---|
| Surveyed coordinates as features | column-prefix rule; the 100 rows are excluded from every training frame |
| Post-visit outcome used for the same prediction | stage tag per column; per-visit `observed_at`; a decision's `as_of` precedes the visit |
| Future observations in a feature | as-of range join (`observed_at < as_of`), enforced in the candidate builder |
| Future belief state | beliefs are versioned with `as_of`; "latest value" lookups are forbidden in historical joins |
| Target-derived features | no target encoding; labels live in a separate file (`labels_eval_v2.csv`) never joined into training |
| Future geocoder results | vendor pins are cached inputs with the stage recorded; they are never re-fetched retroactively to "improve" a past decision |
| Normalisation statistics fitted on validation/test | scalers, thresholds and vocabularies are fitted on training rows only, versioned |
| Statistics fitted on train+test (similarity thresholds, IDF, quantiles) | same rule; the derived-table builder recomputes per split when it needs one |
| Duplicate entity leakage | group key `(account_id, normalised text, town)`; 3 groups/6 rows identified in the official split |
| Sample selection leaking into validation | the 66/100 surveyed accounts inside the official train split are recorded, and the ground-truth set is documented as *indicative* unless the model is fitted without those accounts |
| Ground truth used as *both* training data and evaluation | either/or, decided per experiment and stated in its report |
| Exposure-based sample bias unrecorded | weighted and unweighted metrics both reported, with the weight definition |
| Agent-specific behaviour learned as geography | `agent_id` barred from location features; windowed only in the evidence model with an unseen bucket |
| Synthetic-generator artefacts learned as skill | findings W1–W5 of §24.2 attached to every interpretation; the evidence model ships as a rule table, learned version is a challenger |
| A model's validation score reported as production accuracy | every number carries its sample, split membership and interval |

**MODELLING IMPLICATION.** This dataset can be made leakage-safe because its own structure supplies the stage
boundaries. The dangers are not exotic: they are (a) the pin-agreement feature that *looks* like a correctness signal
and is a give-up signal, (b) the outcome column sitting in the same table as T2 fields, and (c) the 66 surveyed accounts
inside the training split. Each has a mechanical guard, and each guard is testable in code.

---

## 23. Preprocessing Runtime

Measured on the official dataset, single CPU core, no GPU, Python 3.13 with pandas:

| Stage | Command | Runtime | Peak memory | Rows processed | Throughput |
|---|---|---|---|---|---|
| Full EDA (this document) | `tools/eda_official.py` | **23.6 s** | 160 MB | 177,190 (incl. 160,406 GPS points) | ~7,500 rows/s overall; ~6,800 GPS points/s including the per-visit trail-geometry step |
| Charts + dashboard | `tools/eda_charts.py` | 0.8 s | 120 MB | 11 tables aggregated | — |
| Cleaning | `tools/clean_official.py` | 8.9 s | 150 MB | 3,117 addresses + 5,578 visits + 160,406 points | ~19,000 rows/s |
| Candidate generation + features | `tools/build_candidates.py` | 23 s | 210 MB | 3,117 addresses → 7,813 candidates → 7,813 feature rows | ~135 addresses/s |
| Radius/calibration table | `tools/build_derived_table.py` | 0.7 s | 90 MB | 5,578 visits + 100 ground-truth rows | — |
| Leakage + link + workspace checks | `tools/check_*.py` | 1.8 s | 80 MB | all derived artefacts | — |
| **Full reproduction** | `bash tools/reproduce.sh` | **~40 s** | < 250 MB | everything above | — |

**Storage:** official CSVs 8,968,236 B (8.6 MB on disk) · cleaned outputs 18 MB (`gps_points_clean.csv` dominates at
160,372 rows × 10 cols) · derived artefacts 3.6 MB (including 14 SVG charts in `eda_charts/` plus the 8-chart set, and
the EDA transcript).

**Scaling note (marked as an estimate, not a measurement):** the pipeline is linear in rows with no GPU and no
external service. Nothing in the design requires a GPU, an LLM or a distributed system at this data scale; the only
sub-second component that could grow is the per-visit trail geometry loop, which would be vectorised before it needed
more machines.

**MODELLING IMPLICATION.** Preprocessing must stay cheap enough to be re-run on every model refresh and on every
belief reconstruction. At ~40 s for the whole pipeline, the slow loop can afford to be conservative (rare, gated,
reversible) precisely because re-deriving everything is cheap. Any future addition that costs minutes-to-hours per run
(the kind of thing a GPU imposes) should be rejected unless it can be shown to change a decision.

---

## 24. EDA → Model Design Insights

### 24.1 Observation → why it matters → model consequence

| # | Observation (measured) | Why it matters | Model consequence |
|---|---|---|---|
| 1 | Vendor pins are 71.2% locality-level, 9.5% pincode-level, 1.7% rooftop | the pin is a neighbourhood, not a dwelling | do not regress to a coordinate from text alone; generate **candidates with granularity** and rank them |
| 2 | Vendor median error 376.4 m; only 9% within 100 m; p90 839 m | the baseline is both weak and *variable* | report a hit-rate curve, never one number; per-stratum reporting with n |
| 3 | Error varies 13× between strata (pincode 1,375.8 m vs street 108.6 m) | a single accuracy figure would hide the failure mode | strata-aware calibration; thin strata fall back to a parent and are labelled |
| 4 | 237 addresses (7.6%) are outside every town and 0% geocoded | a real, permanent "cannot place" population | a first-class `UNPLACEABLE/outside_town` state with a reason code, counted in coverage |
| 5 | Pin piles do not exist (0 duplicate pin coordinates) | no cluster-based degradation signal is available | distrust verdicts must come from *evidence comparison*, not from geometry alone |
| 6 | Locality match succeeds for 61.1% of texts; 0% ambiguous on exact match; 38.9% have no locality | a licence-free, cheap anchor exists for most records | candidate generation should include a gazetteer-derived arm, with the unmatched third falling back to town level |
| 7 | 7.9% of locality matches are contradicted by the record's own pincode token (plus 8.9% of 6-digit tokens matching no pincode) | text evidence conflicts with itself often | pincode is **soft evidence with a conflict feature**, never a filter |
| 8 | Landmark names: 14 distinct over 240 rows; 198 rows repeat a `(town, name)` | name matching cannot identify a place | landmarks become a type-level language prior and a plausibility feature, never a target |
| 9 | `Nehru Colony` exists in two towns; every pincode maps to 2–5 localities | hierarchy is many-to-many | scope all resolution by town; never let a pincode imply a single locality |
| 10 | 8.4% of addresses carry no locality, pincode or landmark evidence; 10.7% have neither house number nor locality | a floor exists on what text alone can achieve | tier must be driven by evidence; "APPROXIMATE" is the honest output for these records |
| 11 | House-number detection is definition-dependent: 67.7% marker-anchored vs 99.4% any-numeric-token (31.7 pts apart) | house-number parsing is genuinely uncertain | keep **both** pattern features; never treat house-number extraction as a fact |
| 12 | 93.3% carry a `- <6 digits>` tail, but 8.9% of those tokens match no pincode | the most reliable-looking structure has an 8.9% false rate | parse it, test it, flag the failures, and never key on it |
| 13 | 24.9% of records have no comma; 0.8% have no separator at all | "messy text" here means *unpunctuated*, not unstructured | rule and token features, not language modelling |
| 14 | Misspellings dominate the rare-token tail; 3 spellings of one locality in one file | exact matching will miss real records | character n-grams + town-scoped fuzzy matching |
| 15 | 8.41% non-ASCII, 16.2% of T2 vs 2.7% of T3 | script usage is town-correlated | keep script features, but never let them substitute for the declared town |
| 16 | Visits: 5,578 over 1,477 addresses; 47.4% of addresses never visited; max 9 visits per address | evidence exists for a minority of the book and is shallow | memory must work from *one* observation and degrade honestly; cold start is the common case |
| 17 | 25.1% of visits are `address_not_traceable`, with a 1.3-minute median dwell | the failure class is large and shallow | separate place evidence from person evidence; failures must not move coordinates |
| 18 | Failure visits land closest to the vendor pin (195 m; 17.6% within 100 m) and successful visits 323–346 m away (3.2% pin-closer on the surveyed subset) | "the agent agrees with our pin" is a *failure* signal | ban pin-agreement features; use dwell, media and coordinate evidence instead |
| 19 | Trail shape does not separate outcomes (min distance 5.7–8.3 m for all; span larger for failures) | trails describe the process, not the truth | trail features are weighting inputs and evidence coordinates, never correctness labels |
| 20 | Dwell separates outcomes almost perfectly (<1 min → 0% met-someone; 10–25 min → 100%) | a synthetic artefact that would inflate any evidence model | ship evidence weighting as a rule/likelihood table; a learned version must be justified on independent data |
| 21 | Visit exposure 25.1% → 96.8% across delinquency bands (visited accounts median DPD 68 vs 15) | visits are allocated by risk, not by uncertainty | exposure-weighted training and evaluation; record the weighting whenever a visit-based metric is reported |
| 22 | Exposure varies only 1.1× across vendor strata but 3.9× across risk bands | nobody visits *because* the pin is bad | the improvement claim cannot come from "we visited the bad ones"; it must come from using the visits that happen |
| 23 | `pincode`-stratum addresses fail 51.8% of visits vs 6.4% for rooftop | pin quality changes what a visit can achieve | accuracy improvement is an operational outcome, not a cosmetic one — worth the design effort |
| 24 | 957 addresses were confirmed by more than one agent; 1,071 visited more than once; 823 visited ≥3× | repeat and independent confirmation exists | a promotion rule requiring two independent confirmations is supported by the data, not just by caution |
| 25 | One agent has a 25.6% duplicate-photo rate with pristine GPS; all others ≤0.3% | integrity cannot be GPS-only | cross-signal integrity (media, coordinates, dwell) with weights; fault-injection testing |
| 26 | 5,578 unique check-in coordinates, 0 duplicate pins, max speed 32.2 km/h | this dataset contains no spoofing to learn from | no spoof-detection rate may ever be quoted from this data |
| 27 | `added_date` is effectively one weekday (99.2%) | the address timeline is a generation artefact | exclude `added_date` from features; only visit time carries temporal structure |
| 28 | Visits span 89 days, ~430/week, Sundays empty, 83% of check-ins between 10:00 and 13:00 | temporal depth is shallow but the daily rhythm is stable | drift experiments must be replay simulations; visit-hour features are legitimate |
| 29 | Surveyed ground truth: 100 rows, all residences, 0 `OUT`, 0 offices, 1 rooftop; 66 accounts in the train split | the benchmark is small, optimistic and partly shared with training | hold the 100 rows out en bloc; report every number with n and interval; never train on their accounts when they are the test |
| 30 | 3 duplicate-text groups (6 rows) straddle the official split | a small but real entity leak | group key on `(account, normalised text, town)`; verify zero groups spanning splits |
| 31 | 5 duplicate groups across 10 rows represent *different accounts at one building* | the same physical place appears twice in the book | memory must link places across accounts (append-only link events), not key on `address_id` alone |
| 32 | 228 near-duplicate pairs are *different places with the same template* | similarity-based entity merging would delete real addresses | group only on exact normalised keys; similarity stays a *feature*, not an identity |
| 33 | GPS: 26 median points/visit, 10 m median accuracy, 34 axis artefacts, 3.13% of steps with zero Δt | trails are usable geometry of modest quality | weight evidence by accuracy class and point count; drop placeholders from evidence use |
| 34 | Every visit has a remark (762 distinct, multilingual) | outcomes are corroborated in free text | use for auditing outcome coding; keep out of location features (T3 text) |
| 35 | No empty addresses; no missing outcomes; no orphan keys anywhere | the data is mechanically clean | cleaning effort belongs in flags and interpretation, not in scrubbing |
| 36 | Locality address counts range 12–179 (median ~54) | per-locality calibration is statistically impossible | calibrate per stratum × evidence class, not per locality |

### 24.2 Where the EDA weakens or invalidates earlier assumptions

**W1 — EDA invalidates this assumption: "trail geometry can serve as a truth test."** Measured: the minimum check-in→trail
distance is 5.7–8.3 m for *every* outcome, and trail span is *larger* for failed visits (616 m) than for confirmations
(475–551 m). Trail geometry is a description of the collection process. **Architectural change:** trail features move
from "agreement/verification" to "process weight + evidence coordinate"; the integrity layer no longer relies on trail
shape, and its discriminative power must come from media, coordinates and timing.

**W2 — EDA invalidates this assumption: "`added_date` gives a usable temporal axis for addresses."** Measured: 3,093/3,117
addresses share one weekday; 24 distinct dates. **Architectural change:** address-age features are removed; the temporal
axis is visit time only, and any drift reasoning about *address* changes stays a simulation.

**W3 — EDA weakens this assumption: "evidence weighting can be validated on this dataset."** Measured: dwell alone
separates outcomes almost perfectly (< 1 min → 0% met-someone; 10–25 min → 100%), a generator artefact.
**Architectural change:** evidence weighting ships as an explicit rule/likelihood table with documented bands; a learned
evidence model is a challenger that requires confirmation beyond this dataset, and no accuracy claim about evidence
weighting may be derived from these visits.

**W4 — EDA weakens this assumption: "the official split is sufficient for evaluation."** Measured: 66 of the 100
ground-truth accounts fall in the train split; 3 duplicate-text groups straddle splits; the split is time-blind.
**Architectural change:** a group-and-time-aware ledger on top of (not replacing) the official split, and an explicit
rule that the 100 surveyed records are held out en bloc and reported with their shared-account caveat.

**W5 — EDA weakens this assumption: "landmark evidence will substantially improve accuracy."** Measured: landmark phrases
appear in only 25.2% of records, and only 14 distinct names exist, with 198 repeated rows. **Architectural change:**
landmarks stay a minor language/plausibility feature; effort is redirected to locality and evidence, which the data
shows to be the load-bearing channels.

---

### 24.3 Visual EDA register — every chart answers a modelling question

Charts live in `data/derived/eda_charts/` as standalone SVG (no external assets, no network, safe to view offline) and
are collected — inlined, so the file works anywhere — in the self-contained dashboard `data/derived/eda_charts.html`. Regenerate with `python3 tools/eda_charts.py`. Eight of them
are also re-rendered by `tools/eda_official.py`, so the transcript and the figure set never drift apart.

| Chart file | Modelling question it answers | What it shows (measured) |
|---|---|---|
| `addr_len.svg` | Is the address a long free-text field needing heavy NLP? | No — median 67 characters, max 113 |
| `addr_tokens.svg` | Can token-level features carry signal? | Yes — mean 11.9 tokens per record |
| `addr_components.svg` | Which structural components are present, and which are scarce? | Locality/town/pincode usually present; landmark 25.2%; house-number definition-dependent (67.7% vs 99.4%) |
| `baseline_strata.svg` | Is the vendor pin precise enough to be the answer? | No — 71.2% locality-level, only 1.7% rooftop |
| `baseline_error_curve.svg` | How often is the vendor pin good enough to act on? | 5% ≤50 m, 9% ≤100 m, 71% ≤500 m (n=100) |
| `baseline_error_stratum.svg` | Does error depend on the vendor's own precision claim? | Yes — median 108.6 m (street) → 1,375.8 m (pincode) |
| `outcome_by_stratum.svg` | Does a worse pin cause more failed visits? | Yes, monotonically: 6.4% → 51.8% not-traceable |
| `visit_outcomes.svg` | What is the field reporting, and how big is the failure class? | 25.1% `address_not_traceable`; met-someone 40.6% |
| `dwell_outcome.svg` | How strongly does dwell separate success from failure? | Almost deterministically — a synthetic-data warning, not a skill |
| `exposure_dpd.svg` | Are visits a random sample of the book? | No — exposure 25.1% → 96.8% across delinquency bands |
| `gps_accuracy.svg` | How reliable is a single GPS fix? | Median 10 m; 10 points above 100 m; accuracy is a ~68% confidence, not a bound |
| `visits_time.svg` | Is there enough temporal depth for a drift experiment? | No — 13 weeks, ~430/week, Sundays empty, no regime change |
| `agent_photo_dup.svg` | Can an integrity layer be built on GPS alone? | No — one agent at 25.6% duplicate photos with flawless GPS |
| `candidate_arms.svg` | With the official data alone, what does candidate generation deliver? | Vendor pin 92.4% coverage / 376.4 m; matched locality 65.9% / 356.7 m; town centroid 92.4% / 2,740 m; **oracle over the three arms 306.2 m** (n=100 surveyed) — evidence and memory, not a bigger model, is where the remaining value sits |

Every chart's question is printed under the figure in the HTML dashboard, so a reviewer can check that no figure exists
for decoration — each one either changes a feature, a weight, a threshold, or a claim we are allowed to make.

## 25. Final Modelling Implications

**What the data can support (with confidence):**

1. **A candidate-and-rank formulation.** Text evidence resolves 91.6% of records to at least one of {locality, pincode,
   landmark}, and the vendor supplies 92.4% coverage with a stratum label. A model that scores a small candidate set is
   the correct shape; a coordinate regressor would have to invent precision the evidence does not carry.
2. **A granularity-aware output vocabulary.** 71.2% of vendor pins are locality-level, 10.7% of records cannot support
   street-level placement, and 8.4% have no sub-town evidence at all — so the system's output must be a *tier*, not a
   point.
3. **A memory keyed on places, not rows.** 5 duplicate groups across 10 rows show two accounts listing one building, and
   957 addresses already carry independent multi-agent confirmation.
4. **A promotion rule requiring two independent confirmations.** 823 addresses visited ≥3×, 957 with >1 agent: the data
   contains the redundancy this rule needs.
5. **Integrity weighting that is not GPS-based.** One agent carries 25.6% duplicate media with pristine GPS; every
   other agent is ≤0.3%.
6. **Exposure weighting in training and evaluation.** 25.1% → 96.8% exposure across risk bands is a measured, structural
   bias.

**What the data cannot support (and therefore must not be claimed):**

1. **Absolute accuracy for `pincode` (n=10) and `rooftop` (n=1) strata** — insufficient n; parent-stratum fallback and
   visible labelling instead.
2. **Any statement about `OUT`, office or native addresses** — zero ground truth for them, despite 237 + 464 + 226
   records existing.
3. **Real drift behaviour** — 89 days, no regime change; every dynamic-learning result is a replay simulation.
4. **Spoof detection performance** — no spoofing in the data; fault injection only, with injection-based labels.
5. **Evidence-model accuracy** — dwell↔outcome near-determinism makes any fitted number a generator artefact.
6. **A confident statement about the 52.6% of addresses never visited** — no evidence exists for them.

**Immediate implications for the next stage (no training yet):** the first modelling work should be the *cheapest
diagnostic* available — establishing the floor (vendor pin), the ceiling of the current evidence (best achievable
candidate), and whether any learned component beats a rule baseline on so thin a truth set. Only after those three
numbers exist does a model earn the right to be built, and its report must carry the sample, the split membership and
the interval.

---

## 26. What We Should Test Next

Ordered, pre-registered, all computable from the official dataset alone. Each states its estimator, its split, and the
condition under which it may be reported.

| # | Test | Estimator | Split / guard | Pass condition | Report if it fails |
|---|---|---|---|---|---|
| N1 | Floor: vendor pin, rule priority | median error, hit-rate <50/100/250/500 m | the 100 surveyed rows; 66-account caveat stated | establishes the floor (already 376.4 m median / 9.0% <100 m) | — |
| N2 | Ceiling: best candidate in the generated set | same curve, plus per-arm coverage over all 3,117 | surveyed rows; grouped by account | the ceiling bounds what ranking can ever achieve | if the ceiling is near the floor, ranking is not the lever — evidence and memory are |
| N3 | Text-feature ablation | candidate recall and hit-rate curve | grouped CV over accounts | adopt the smallest feature set that matches the best beyond the interval | drop features, record the decision |
| N4 | Ranking vs rules | precision@1, nDCG@5, hit-rate curve | grouped CV; the 100 rows never trained on | a model must beat the rule baseline beyond the interval, with no coverage/stratum/cost regression | ship the rule baseline |
| N5 | Cold vs warm | hit-rate curve on addresses with ≥1 and ≥2 confirmations | as-of joins; time-ordered cut-points | warm must beat cold beyond the interval on ≥2-confirmation addresses | if not, memory is justified by auditability and triage only — and the document says so |
| N6 | Negative-evidence safety check | median error on surveyed addresses that also have ≥1 `address_not_traceable` visit | surveyed rows | the invariant (no coordinate movement from negative evidence) must hold exactly | any violation is a build failure, not a metric |
| N7 | Integrity weighting ablation | error under injected duplicate-media and implausible-movement faults | fault injection; clean-visit false-positive rate reported | detections improve without penalising clean visits | no detection rate may be claimed until this passes |
| N8 | Exposure weighting | weighted vs unweighted metrics side by side | the full visit set | the gap is quantified and reported | if the gap is large, visit-based metrics must always be reported weighted |
| N9 | Radius calibration feasibility | measured coverage at nominal 90% | strata with n ≥ 15 only (locality 73, street 16) | measured coverage ≥ nominal | else widen and label `calibration_fallback`, and publish empirical hit-rates instead of nominal radii |
| N10 | Duplicate-entity leak check | number of group keys spanning splits | full book | must be 0 | fix the group key definition |
| N11 | Cold-start behaviour | tier mix, refusal reasons, coverage | the 237 `OUT` records and all never-visited addresses | every record gets either a coarse coordinate with a wide radius or `UNPLACEABLE` with a reason | any fabricated point fails the test |
| N12 | Outcome-vocabulary audit | agreement between `outcome` and `remark` text | all 5,578 visits | the two-dimension mapping must be mechanically consistent | fix the mapping, not the data |

**What must not be done next:** training a ranking model before N1–N4 have produced their numbers; reporting any
evidence-model accuracy from this dataset; quoting a radius for strata with n < 15; treating the 100 surveyed rows as a
held-out set while training on the 66 shared accounts; or producing a single-number accuracy claim without its sample,
split and interval.

---

### Dataset in numbers

*Official PS3 dataset only.*

| Quantity | Value |
|---|---|
| Tables | **11** |
| Rows (all tables) | **177,190** |
| CSV size | 8.97 MB |
| Towns modelled | 3 (+237 addresses outside all of them) |
| Accounts | 2,400 |
| Addresses | **3,117** |
| Addresses with a vendor geocode | 2,880 (92.4%) |
| Addresses never geocoded | 237 (7.6%) — all `OUT` |
| Localities / pincodes | 36 / 12 |
| Landmarks | 240 (14 distinct names, 14 types) |
| Agents | 30, of which **9** ever visit |
| Field visits | **5,578** |
| Addresses ever visited | **1,477 (47.4%)** |
| Addresses ever met-someone | **900 (28.9%)** |
| Addresses visited ≥3 times / by >1 agent | 823 / 957 |
| GPS points | **160,406** |
| Surveyed ground-truth addresses | **100 (3.2%)** |
| Median vendor error (surveyed 100) | 376.4 m |
| Vendor error ≤100 m | 9.0% |
| Median address length / tokens | 67 characters / 12 tokens |
| Visits ending `address_not_traceable` | 1,400 (25.1%) |
| Median dwell on failure / success | 1.3 min / 6.6–14.8 min |
| Visit window | 2026-04-01 → 2026-06-29 (89 days) |
| Rows dropped in cleaning | **34 (0.021%, GPS placeholders)** |
| Coordinates moved by cleaning | **0** |
| Labels invented | **0** |

### Top 20 EDA findings (ranked by importance for modelling)

| # | Finding | Rank rationale |
|---|---|---|
| 1 | **Pin quality drives field failure:** `address_not_traceable` runs 6.4% (rooftop) → 13.5% (street) → 24.3% (locality) → **51.8% (pincode)** | establishes the whole problem's value |
| 2 | **Failure visits converge on the vendor pin** (median 195 m; 17.6% within 100 m), success visits 323–346 m away — and on the surveyed subset failures are pin-closer 84.9% of the time while successes are 3.2% | bans a plausible-looking feature and reorders the evidence design |
| 3 | Visit exposure is **25.1% → 96.8% across delinquency bands**, and nearly flat across vendor strata | forces exposure-weighted training/evaluation; visits are not a sample |
| 4 | The vendor is **71.2% locality-level**, median error 376.4 m, only 9.0% within 100 m | the baseline, and the reason a point-regression framing fails |
| 5 | Ground truth is **100 rows, 3.2%, all residences, 0 `OUT`, 1 rooftop, 66 accounts inside the train split** | bounds every claim that can be made |
| 6 | **Dwell↔outcome is near-deterministic** (<1 min → 0% met-someone; 10–25 min → 100%) — a generator artefact | caps what evidence modelling may claim here |
| 7 | Outcome column **mixes place and person evidence** (`locked_premises`, `no_such_person`, `address_not_traceable`) | the vocabulary must be split before any model sees it |
| 8 | **91.6%** of records carry at least one of {locality, known pincode, landmark}; **8.4%** carry none; **38.9%** have no localisable locality name on exact match | sets the resolution ceiling and the refusal floor |
| 9 | **7.9% of locality matches are contradicted by the record's own pincode token**; 260 6-digit tokens match no pincode | pincode must be soft evidence with a conflict feature |
| 10 | **Trail shape does not separate outcomes** (min distance 5.7–8.3 m for all; span larger for failures) | redirects integrity away from trajectory agreement |
| 11 | One agent carries **25.6% duplicate photo hashes** with pristine GPS; all others ≤0.3% | the dataset's only planted integrity anomaly, and it is not spatial |
| 12 | **228 near-duplicate pairs are different places** sharing a template; only 10 pairs are genuinely similar wording | similarity-based de-duplication would destroy real addresses |
| 13 | **5 duplicate groups / 10 rows** are two accounts at one building; 3 groups straddle the official split | place-level memory and group-aware splits |
| 14 | Landmarks: **14 distinct names for 240 rows** (198 repeated) | landmark names cannot identify anything |
| 15 | **237 addresses outside all towns, 0% geocoded** | refusal is a first-class state, not an error |
| 16 | **`added_date` collapsed to one weekday** (99.2%) | removes a whole category of temporal features |
| 17 | 5,578 visits, **max 9 observations per address**, 47.4% of addresses never visited | memory must work from one observation; cold start is the norm |
| 18 | **957 addresses confirmed by >1 agent**, 1,071 visited more than once | the two-confirmation promotion rule is supportable |
| 19 | Addresses per matched locality vary **12–179**; pincodes map to 2–5 localities; `Nehru Colony` spans two towns | per-locality calibration is impossible; matching must be town-scoped |
| 20 | Registry is mechanically clean: **0 orphan FKs, 0 duplicate rows, 0 duplicate keys, no negative travel, no teleports** | cleaning is an interpretation task, not a repair task |

### Top 15 data-quality problems (ranked by severity)

| # | Problem | Severity | Evidence | Mitigation carried into the design |
|---|---|---|---|---|
| 1 | Ground truth covers 3.2% of addresses and excludes the hardest records | **critical** | 100 rows; 0 `OUT`, 0 office, 0 native; 1 rooftop | hold out en bloc; report n + interval; parent-stratum calibration |
| 2 | 66 of the 100 ground-truth accounts sit in the official train split | **critical** | measured directly | never train on those accounts when they are the test; state the caveat |
| 3 | Visit allocation is demand-driven | **critical** | 25.1% → 96.8% by delinquency band | exposure weighting; weighted and unweighted metrics both reported |
| 4 | Outcome column mixes place and person evidence | **high** | `locked_premises`, `no_such_person`, `address_not_traceable` semantics | two-dimension vocabulary; a single failure never relocates a coordinate — accumulated independent negatives only demote/widen/mark/re-verify (graded rule, F2.1/D36) |
| 5 | Dwell↔outcome near-determinism (synthetic) | **high** | 0% met-someone below 1 min vs 100% above 10 min | evidence model ships as a rule table; no accuracy claim from this data |
| 6 | `address_not_traceable` correlates with abandonment, not with the true place | **high** | median 1,603 m from truth at 1.3 min dwell; pin-closer 84.9% | negative evidence quarantined from coordinates |
| 7 | Landmark table cannot identify places | **high** | 14 names / 240 rows / 198 repeats | landmarks demoted to type-level evidence |
| 8 | Text similarity conflates templates with duplicates | **high** | 228 of 238 near-duplicate pairs are different places | exact normalised group keys; similarity only as a feature |
| 9 | Pincode evidence contradicts locality evidence in 7.9% of matched records | **medium-high** | measured | soft evidence + `pin_conflict` flag |
| 10 | 7.6% of addresses are outside every modelled town and ungeocoded | **medium-high** | 237 records, 0% coverage | first-class `UNPLACEABLE/outside_town` state |
| 11 | No stored address→locality key | **medium** | 61.1% exact-match rate; 38.9% unmatched | text-based resolution with scored evidence and explicit failures |
| 12 | Trail geometry is not discriminative | **medium** | 5.7–8.3 m min distance for every outcome | trail features used as process weights only |
| 13 | GPS is quantised to whole metres and capped at 80 points | **medium** | integer x/y; max seq 79 | no sub-metre claims; accuracy-class weighting |
| 14 | 34 GPS placeholder points and 3.13% of steps with zero Δt | **low-medium** | measured | placeholders excluded from evidence; Δt-gated speed |
| 15 | `added_date` is a generation artefact | **low** | 99.2% on one weekday | excluded from features |

### Top 15 preprocessing decisions (and why)

| # | Decision | Why |
|---|---|---|
| 1 | Keep the raw text in `address_text_raw` and add `text_norm` beside it | reversibility; every later rule can be re-derived or undone |
| 2 | Preserve Devanagari and Kannada ranges instead of transliterating | 262 multi-script records; script is real signal and transliteration is lossy |
| 3 | Expand 13 abbreviations mechanically | `no.` 31.2%, `rd` 22.8%, `blk` 19.0% — the vocabulary is stable enough for a fixed map |
| 4 | Extract 6-digit tokens **as strings** and test them against the gazetteer | 8.9% match nothing; integer keys would create false joins |
| 5 | Add `pin_conflict_with_locality` | 7.9% of matches conflict with the record's own pincode |
| 6 | Split the outcome into place and person dimensions | one column, two meanings; the split changes what evidence may do |
| 7 | Keep `address_not_traceable` as a **suspicion** signal only | 1,603 m from truth at 1.3 min dwell |
| 8 | Keep every near-duplicate row; group with an exact normalised key | 228 of 238 similar pairs are different places |
| 9 | Flag instead of delete outliers (dwell, accuracy, speed) | these describe the collection process, which the evidence layer models |
| 10 | Exclude only the 34 GPS placeholders from evidence use | they carry no location, and the count is logged |
| 11 | Remove `ptp_id` | 89.2% null and belongs to a different workflow — an accidental dependency |
| 12 | Do not impute structural nulls (`salary_credit_day`, `agents.town_id`, missing pins) | each null is a state the design depends on |
| 13 | Keep both house-number definitions as separate flags | they disagree by 31.7 points; certainty is not available |
| 14 | Derive per-visit trail geometry as *features*, not as a truth test | trail shape does not separate outcomes |
| 15 | Version every rule (`rule_version`) and log each rule's row counts | reproducible cleaning; a change of rule is a new version, not a silent edit |

### Top 15 leakage risks (and prevention)

| # | Risk | Prevention |
|---|---|---|
| 1 | `surveyed_x/y` used as a feature | column-prefix rule; the 100 rows are excluded from every training frame |
| 2 | Training on the 66 ground-truth accounts that sit in the official train split | the caveat is recorded and the ground-truth set is used as an independent sample or explicitly labelled indicative |
| 3 | A visit's outcome used to place the decision that preceded it | stage tags per column; per-visit `observed_at`; decisions carry `as_of` |
| 4 | **Distance to the vendor pin treated as a correctness feature** | banned by name — it is failure-correlated (§10.3) |
| 5 | Future observations in warm features | as-of range join (`observed_at < as_of`) in the candidate builder |
| 6 | "Latest belief" lookups in historical joins | beliefs are versioned; only versions with `as_of < t` are readable |
| 7 | Account fields used as location features | they encode the visit-selection policy; excluded by prefix rule |
| 8 | `agent_id` memorising the collector | barred from location features; windowed only in the evidence model, with an unseen bucket |
| 9 | Duplicate entities straddling splits | `group_key = (account_id, normalised text, town)`; verified 0 groups span splits after grouping |
| 10 | Normalisation/scaling statistics fitted on validation or test | fitted on training rows only, versioned in the artefact receipt |
| 11 | `remark` or `photo_hash` values entering features | T3 prose/media; only the duplicate *rate* is used, as an integrity input |
| 12 | `added_date` acting as a split proxy | excluded from features |
| 13 | Dwell's synthetic discriminative power read as evidence-model skill | interpretation rule in §24.2; rule-table-first evidence policy |
| 14 | Exposure-biased metrics quoted as population performance | weighted and unweighted metrics reported together, with the weight definition |
| 15 | Radius quoted from the fitting sample, or for strata too thin to calibrate | calibration fitted on validation, reported on held-out rows; strata with n < 15 use parent fallback and are labelled |

### Top 15 modelling implications (data behaviour → SUTRA architecture)

| # | Data behaviour (measured) | Architectural element it requires |
|---|---|---|
| 1 | 71.2% locality-level pins; error varies 13× by vendor stratum | candidate generation + ranking with a **granularity** vocabulary, not coordinate regression |
| 2 | Failures cluster at the pin (195 m, 17.6% within 100 m) | a ban on pin-agreement features; evidence must come from dwell, media and coordinates |
| 3 | Outcome column mixes place and person facts | the two-dimension evidence vocabulary, and graded negative evidence (never relocates a coordinate by itself; F2.1/D36) |
| 4 | 957 addresses confirmed by >1 agent; 823 visited ≥3× | a promotion rule requiring **two independent confirmations** |
| 5 | One agent's media anomaly with flawless GPS | **cross-signal integrity weighting** ("weight, don't accuse"), not a GPS check |
| 6 | Exposure 25.1% → 96.8% by risk band | **exposure-weighted** training and evaluation; weighted metrics reported every time |
| 7 | 47.4% of addresses visited, max 9 observations, 52.6% never visited | memory that works from a **single** observation and an explicit **cold-start** mode |
| 8 | 8.4% of records have no sub-town evidence; 10.7% have neither house number nor locality | **tiered output** with an honest APPROXIMATE floor |
| 9 | 237 addresses outside all towns and ungeocoded | **`UNPLACEABLE` as a first-class state** with a reason code |
| 10 | 7.9% pincode/locality conflicts; 260 unmatched 6-digit tokens | **soft evidence with an explicit conflict feature**, no hard filters |
| 11 | 14 landmark names / 240 rows; `Nehru Colony` in two towns; pincodes map to 2–5 localities | **town-scoped** resolution; landmarks as type-level evidence only |
| 12 | 228 near-duplicate pairs are different places; 5 groups are the same building twice | **exact-key grouping** for splits; **evidence-based place linking** for memory |
| 13 | 89-day window, no drift; `added_date` collapsed | dynamic learning evaluated as **replay simulation**, labelled as such |
| 14 | Ground truth n = 100, 3.2%, skewed away from the hard cases | **strata-aware reporting with n and intervals**; parent-stratum fallback for thin strata |
| 15 | Mechanically clean data (0 orphan keys, 0 duplicate rows, 0 teleports) | cleaning stays **flat and lossless**; the work moves to interpretation, evidence weighting and uncertainty |

### Final recommendation

**Given what this dataset actually looks like, what should we build next?**

The EDA changes the order of work, not just the details. Three findings dominate:

1. **The data cannot validate an evidence model.** Dwell alone separates success from failure almost perfectly
   (§9.5) — a synthetic-generator artefact. Any evidence-weighting model fitted here would report a flattering number
   that means nothing. Therefore the evidence layer ships as an **explicit, auditable rule/likelihood table** with
   documented bands, and a learned version is treated as a *challenger* that needs genuinely independent confirmation.
2. **The benchmark is thin, optimistic and partly shared with training.** 100 surveyed rows, all residences, no `OUT`,
   no offices, one rooftop — and 66 of their accounts sit in the official train split. Therefore the 100 rows are held
   out **en bloc**, every headline number carries its n and interval, and strata below n = 15 are declared
   uncalibratable rather than reported with a confident-looking figure.
3. **The lever is evidence and memory, not a bigger model.** The vendor's pin is coarse (71.2% locality-level, 376 m
   median) and the text evidence is structurally limited (8.4% with no sub-town evidence, 10.7% with neither house
   number nor locality). Meanwhile 5,578 visits exist, 957 addresses carry independent multi-agent confirmation, and
   visit failure tracks pin quality almost linearly. The largest honest gains available in this dataset come from using
   visits well — and from refusing to overstate what the evidence says.

**Build next, in this order:**

1. **The frozen floor and ceiling first** (N1–N2): vendor-pin baseline and the best achievable candidate from the
   official evidence. Without these two numbers, no model's improvement can be judged.
2. **The evidence rule table and the belief update** (N5–N7): two-dimension weights, the no-negative-movement
   invariant, the two-confirmation promotion rule, and the fault-injection bed that measures integrity behaviour —
   because these are the parts of the architecture the data can actually exercise.
3. **The group- and time-aware split ledger** (N10) plus the cold-start contract (N11): the two smallest pieces of
   infrastructure that prevent a wrong headline number and a fabricated coordinate.
4. **Then, and only then**, the ranker (N3–N4) — announced in advance as likely to win by a small margin, with the rule
   baseline shipping if it does not, and with the pincode/rooftop strata excluded from any calibration claim.
5. **Uncertainty as a first-class output** (N9): a measured radius where n allows, a labelled fallback where it does
   not, and empirical hit-rates instead of nominal radii whenever measurement fails.

**What we will not do:** train a ranking model before the floor, ceiling and integrity behaviour are known; report an
evidence-model accuracy from these visits; quote a radius for a stratum with fewer than 15 ground-truth records; treat
the surveyed rows as held out while training on their 66 shared accounts; or publish any accuracy figure without its
sample, its split membership and its interval.

**In one sentence:** the official dataset is mechanically clean but statistically thin, its visits are informative but
biased and its failures point at *our own pin*, and its ground truth is too small to forgive a single unexamined
assumption — so the next stage must build the smallest, most auditable version of SUTRA first (candidates, evidence
rules, memory, refusal), and earn every additional model with a measured improvement on a properly guarded split.

---

**Sources.** External claims resolve in `PS3_SOURCE_REGISTER.md` (`[S1]`–`[S50]`); internal measurements are
`[S90]` (audit log `data/derived/ps3_audit_full.txt`), `[S91]` (radius calibration
`data/derived/derived_ps3_radius_calibration.csv`) and `[S92]` (prior-pass measurements). Statements that cite no
external source rest on internal evidence and are labelled `[DATA]`/`[INFERENCE]` where they appear.
