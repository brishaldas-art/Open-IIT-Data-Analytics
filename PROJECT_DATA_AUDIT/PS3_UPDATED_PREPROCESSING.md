# PS3 UPDATED PREPROCESSING (v2)

**Separation that governs this document:** *cleaning* removes or flags defects in the official data (non-destructive, rule-logged); *preprocessing* turns cleaned official data into model-ready inputs by lane. Raw stays read-only; outputs land in `data/cleaned/` and `data/derived/`. **Nothing invents rows, coordinates or labels.**

---

## 1. Cleaning rules (updated: A1–A9)

| Rule | Input | Condition | Transformation | Rows | Why | Risk if wrong | Information preserved / lost |
|---|---|---|---|---|---|---|---|
| A1 | `address_text` | all | **Identity key** — lowercase, unicode-safe punctuation strip, **trailing token kept** | 3,117 | two accounts at one place must be linkable; two villages differing only in the trailing token must not merge | over-merging distinct places | none lost |
| A2 | `address_text` | all | **Render key** — same, trailing token stripped | 3,117 | parse/template lane only | if used as identity: 193 rows collapse into 70 false places | trailing token kept as `pin_tail` |
| A3 | `address_text` | trailing 6-digit present (2,907) | extract `pin_tail` + `pin_known` | 2,907 | pincode is an address component; unknown tails flagged, never imputed | misreading a house number as pincode | none lost |
| A4 | `field_visits.remark` | all (5,578) | keep raw; flag landmark-named (208) and digit-bearing (451) | 5,578 | the only free text that can correct a location | training on text as a label | none lost |
| A5 | `address_type` | `permanent_native` (226) | flag; exclude from place merging; never a visit target | 226 | native-village templates collide across accounts; 0/226 ever visited | losing `OUT` context | none lost (flag) |
| A6 | `photo_hash` | repeats within agent | `same_hash_hits` count | 5,578 (172 flagged) | media duplication is the measured integrity signal | accusing instead of weighting | none lost |
| A7 | `baseline_geocodes` | 237 absent | left join; missing-pin flag | 237 | coverage must stay visible | imputing a pin | none lost |
| **A8 (new)** | `agents`, `field_visits` | all visits | **integrity weight** ∈ {1, w_media} from repeat-hash + timing plausibility; per-agent not-traceable rate kept as a diagnostic, **not** a per-visit penalty by default | 5,578 | separates evidence quality from evidence content; avoids modelling the collector | over-penalising an agent's addresses | nothing lost (weights reversible) |
| **A9 (new)** | `accounts` exposure fields | all | **excluded from feature matrices**; retained only in the analysis tables as exposure/value context | 2,400 | flat-yield measurements show they describe targeting, not place success | silent leakage of exposure into geography | none lost (analysis intact) |

**Positions moved: 0 · rows deleted: 0 · labels invented: 0** (the 34 placeholder GPS rows deleted in the earlier pass remain the only deletions anywhere, 0.021%).

## 2. Preprocessing lanes

### TEXT (T0)
Unicode NFC; case-fold for matching (original retained); script segments separated (Latin / Devanagari 154 / Kannada 108); tokenisation; trailing `- <6 digits>` split into a component; house-marker and separator spans; gazetteer lookups; small documented abbreviation table. **No stemming, no machine transliteration, no LLM, no external dictionary.**

### GEOGRAPHIC (T0–T1)
Candidate sources: matched locality centroid · pincode-mates · street/rooftop pins of other addresses as **finer anchors (available within 300 m for 96.7% of coarse cases; median 96 m)** · landmark mentions (directions only — 240 points / 14 names, README says "incomplete and slightly off") · the vendor pin. Distances in the local metric plane.

### FIELD-VISIT (T3→T4)
Evidence classes: **positive** (`met_borrower`, `met_family`, `cash_collected`) · **ambiguous** (`neighbour_says_shifted` — movement, not location) · **process, never place** (`address_not_traceable`, `locked_premises`, `no_such_person`). Weights: `gps_accuracy_m` (median 9.8 m), dwell (median 207 s; synthetic artefact link to outcome), media-integrity (A8), phase (pre/post 2026-05-15 cut). Place clusters from met check-ins ≤30 m across addresses (81 clusters / 191 addresses), fit on train evidence only; **never merge on `account_id`** (an account's addresses are median 3,011.6 m apart).

### CATEGORICAL (T0/T4)
`town_id` (3 + `OUT`), baseline `precision` (4), outcome class, address type, source. Encodings fit on training data only. `OUT` and `permanent_native` are honest categories.

### NUMERIC (T0/T2/T3)
Distances (candidate-to-pin, candidate-to-candidate; check-in-to-truth in evaluation only), token/length/digit counts, GPS accuracy, dwell. Scaling fit on training data only. **No imputation** (68.2%/30.3% nulls stay null).

## 3. Evaluation protocol (preprocessing's contract with honesty)

- Ground truth for accuracy: the **100 surveyed addresses only**, reported **split-aware** (train 66 / val 19 / test 15), with the val+test subset always shown separately.
- Radius: fit per stratum on **train** truths; report coverage on val+test **with n** (locality 79.2% at p80; pincode fails — published as a failure).
- Warm/cold claims: computed on val+test (56.7% vs 25.1%) alongside the full-population number.
- An **additional entity/time-aware split ledger** (documentation only, official benchmark untouched) records for each address: first-evidence date, split, nearest cross-split evidence distance — so no claim can accidentally rely on a neighbour in training data.

## 4. Outputs

| Output | Contents | Shape |
|---|---|---|
| `data/cleaned/addresses_scope_clean.csv` | official fields + identity/render keys, `pin_tail`, `pin_known`, `non_ascii`, `house_marker`, `permanent_native` | 3,117 × 15 |
| `data/cleaned/visits_scope_clean.csv` | official fields + `met_someone`, `phase`, `same_hash_hits`, pin stratum | 5,578 × 21 |
| `data/cleaned/cleaning_log_updated.csv` | rules A1–A9 with rows, why, risk, information preserved/lost | 9 × 8 |
| `data/derived/updated_shared_column_map.csv` | all 75 shared columns: stage, role class, note | 75 × 5 |
| `data/derived/updated_*.csv` | the 16 analysis artefacts (diagnostics, radius, anchors, leakage, exposure…) | — |

## 5. Performance (CPU-first, no GPU, no network)

Full re-audit 1.7 s / 226 MB peak · cleaning 0.15 s · analysis battery <1 s · the entire pipeline is reproducible from the official files in seconds.

## 6. Why this is defensible

Every rule answers to the official documentation (scope), the files themselves (definitions and counts), or a leakage boundary (stage). The two rules that matter most — **one shared column is a feature, and no T3/T4 value may inform its own visit's prediction** — are enforced by construction, not by discipline.
