# SUTRA — DATA CLEANING REPORT

**Domain cleaned: DATASET A only** (`data/official_ps3/`, hash-frozen). DATASET B is empty and is cleaned separately,
under its own licence rules, if and when it lands (`PS3_DATA_LINEAGE.md` §4). There is no merged dirty dataset anywhere
in this workspace.

---

> **SUPERSESSION NOTE — 2026-10-07 (official-scope re-audit).**
> The duplicate-text rule below is stated with **one** definition ("10 rows share a normalised text"). The
> authoritative, definition-aware pair — identity key **5 groups / 10 rows** vs render key **70 groups / 203 rows**
> (template families, mostly `permanent_native`) — is in §3 of the official-scope re-audit's *Updated Data Audit* (sibling re-audit set, outside this workspace), together with
> the updated cleaning-log rules A1–A7 (the updated cleaning-log rules A1–A7 in that re-audit's cleaned-data folder). The cleaning
> **policy** here is unchanged; only the count is now published with its definition.


Run: `python3 tools/clean_official.py` → `data/cleaned/` + `data/cleaned/cleaning_log.csv` (15 rules, one row each with
counts). Every rule is reversible: raw values are preserved in `<col>_raw`, and the log records `rows_in/rows_out`.

---

## 1. Principles the cleaning obeys

1. **Preserve before transforming.** `address_text_raw` keeps the original; `text_norm` adds the normalised form.
2. **Flag, do not fix, anything spatial.** No coordinate is moved, snapped, averaged or "corrected". Suspicious geometry
   becomes a flag, and the flag is a feature/audit fact.
3. **Never invent a label.** No outcome is re-typed; no pseudo-label is created. `address_not_traceable` becomes a
   *record-quality* signal, never a negative coordinate label.
4. **Every drop is logged with a reason and a count.** Drops today: 34 GPS points (0.021%).
5. **Deterministic.** Same input → same output; no random sampling, no seed-dependent choices.
6. **Domain A stays byte-identical** — verified by hash in `tools/check_leakage.py`.

---

## 2. Address cleaning (3,117 rows → 3,117 rows, no drops)

| Step | What was done | Count / effect |
|---|---|---|
| Unicode normalisation | NFKC; Devanagari and Kannada ranges kept (8.4% of rows carry them), punctuation collapsed | 3,117 rows |
| Case + abbreviation expansion | `rd→road`, `st→street`, `ngr→nagar`, `h.no→house`, `nr→near`, `opp→opposite`, `soc→society`, … | deterministic map, 13 patterns |
| Token whitespace | collapse runs, strip | — |
| **Descriptive flags (kept, never "fixed")** | `flag_no_digit` (9) · `flag_no_separator` (24 without comma/slash/hyphen; **777 = 24.9% without any comma**) · `flag_pin_in_text` (2,910) · `flag_pin_unknown` (260 = 8.9% of those tokens match no known pincode) · `flag_outside_town` (237, `town_id = OUT`) · `flag_dup_text` (10 rows share a normalised text) | 6 flags |
| Rule-based span extraction | `span_lane` (`gali/galli/lane`), `span_block` (`block/sector/ward`), `span_cross` (`cross/main/marg`), `span_house` (`house/plot/door/flat`), `span_relation` (`near/opposite/behind/beside/adjacent/next to`), `span_locality_token` (gazetteer hit) | 6 spans |

**Deliberately NOT done:** transliteration of Devanagari/Kannada (would destroy the evidence that the record is
multilingual and that the field agent wrote it; a transliteration variant can be *added* as a parallel column later and
tested as an ablation, never substituted); stemming/lemmatisation (loses "cross"-type address grammar signals);
de-duplication of near-identical texts (10 rows — these must stay visible, because two accounts at the same building are
a *grouping* problem for evaluation, and deleting one would corrupt the account↔address accounting).

### 2.1 The duplicate-text decision
10 rows share a normalised text. They are **kept** and flagged. Reason: the risk is not the duplicate itself, it is that
the same physical building lands in both train and test. Deleting the row would hide the problem; instead the pipeline
computes a `group_key` over `(account_id, normalized_text, town_id)` and the split ledger groups on it
(`PS3_DATA_LINEAGE.md` §5).

---

## 3. Visit cleaning (5,578 rows → 5,578 rows, 2 derived columns added, 1 column dropped)

| Step | What was done | Count / effect |
|---|---|---|
| Outcome split into **two dimensions** | `outcome_place_flag` ∈ {place_positive (`met_borrower`,`met_family`,`cash_collected`), place_weak_positive (`locked_premises`,`neighbour_says_shifted`,`no_such_person`), place_indeterminate (`address_not_traceable`)}; `outcome_person_flag` ∈ {person_positive, person_negative, person_indeterminate} | 5,578 rows; the split is the single most important cleaning decision in this project (audit §2.7b) |
| Timestamps | `start_ts`, `checkin_ts` parsed to datetime; `travel_s` derived | 0 negative travel values |
| Flags | `flag_short_dwell` (443 visits < 60 s) · `flag_implausible_dwell` (0) · `flag_negative_travel` (0) · `flag_negative_outcome` (1,400) | 4 flags |
| Column dropped | `ptp_id` (89.2% null) | belongs to a different problem statement; keeping it would be an accidental dependency |
| **Not done** | No visit was deleted for being "bad", no outcome was re-typed, no `address_not_traceable` visit was removed | 0 drops — a short or failed visit is *evidence*, not noise |

`locked_premises` is deliberately **weak positive for place, indeterminate for person**: the location is right enough to
stand at a door, but nobody confirmed who lives there.

---

## 4. GPS cleaning (160,406 points → 160,372 points)

| Step | What was done | Count |
|---|---|---|
| Axis artefacts | drop points with `x == 0` or `y == 0` (sensor placeholder, not a place in the local metric plane) | **34 dropped (0.021%)** |
| Ordering | sort by `(visit_id, seq)`; verified `seq` is monotone in time for all 5,578 visits | — |
| Derived per-step geometry | `step_m`, `dt`, `speed_kmh` | 160,372 rows |
| **Deliberately NOT done** | No smoothing, no Kalman filter, no outlier removal, no map matching (a road graph is unavailable; the dataset is a local metric plane), no dwell re-estimation | 0 additional drops |

Reason for the "hands off" stance: the audit found **no implausible trail** — max implied speed 32.2 km/h, p99 23.1 km/h,
0 teleports, 0 visits checking in more than 500 m off their own trail. Applying a filter to clean data would only
manufacture confidence. The integrity layer instead *measures* trail agreement (see §6) and gets its thresholds from the
fault-injection test bed (`PS3_FIELD_EVIDENCE_ARCHITECTURE.md` §7), because this dataset cannot demonstrate a spoof.

---

## 5. Cleaning units into canonical form (what the cleaning stage does *not* do)

Address text is **not** parsed into a nested canonical object here. Cleaning produces a **flat, faithful, flagged**
representation plus spans; turning text into the canonical `TOWN / LOCALITY / LANDMARK / ADDRESS_RECORD` structure is the
preprocessing job, with a documented fallback (rule → pattern grammar → optional statistical parser → unresolved), and
every mapping decision is scored, not assumed (`PS3_DATA_PREPROCESSING.md`). This separation is what lets the parser be
swapped or removed without re-cleaning the data.

---

## 6. Per-visit trail features produced (5,578 rows)

`data/cleaned/trail_features.csv`: `n_points`, `acc_med`, `acc_p90`, `span_s`, `path_m`, `speed_max`, `speed_p90`,
centroid and endpoints, and two agreement measures — `dist_checkin_to_median_m`, `dist_start_to_checkin_m`.

**Warning carried with the artefact:** these are *evidence geometry*, not labels. In particular
`dist_checkin_to_median_m` is small for both a successful visit and a failed one, so it must never be read alone; the
combination that matters is (outcome dimension × dwell × trail agreement × agent baseline), as specified in
`PS3_FIELD_EVIDENCE_ARCHITECTURE.md`.

---

## 7. What cleaning changed in the design (the honest summary)

| Finding | Design consequence |
|---|---|
| 237 records outside every modelled town, 0% geocoded | `UNPLACEABLE` is a first-class output state with a reason code, not an error |
| 8.9% of 6-digit tokens are not known pincodes; 2.4% of addresses have no separator | the resolver must test evidence, not pattern-match: a "pincode-looking" string is a *hypothesis* |
| 443 visits under a minute | dwell is an evidence weight, and a sub-minute visit can never carry a place claim |
| 1,400 negative outcomes whose check-in sits near the pin | a single negative can never relocate a coordinate by itself; negatives are quarantined from coordinates (audit §2.7b; F2.1/D36) |
| 34 axis artefacts | a geometry sanity rule exists, and its effect on any metric will be measured, not asserted |
| 10 duplicate texts straddling accounts | evaluation groups on `group_key`, not on address id |

---

## 8. Reproduction

```
python3 tools/clean_official.py                 # 15 logged rules
cat data/cleaned/cleaning_log.csv               # every rule, rows_in/rows_out, note
python3 tools/check_leakage.py                  # proves Domain A is unmodified by the cleaning
```


---

**Sources.** External claims resolve in `PS3_SOURCE_REGISTER.md` (`[S1]`–`[S50]`); internal measurements are
`[S90]` (audit log `data/derived/ps3_audit_full.txt`), `[S91]` (radius calibration
`data/derived/derived_ps3_radius_calibration.csv`) and `[S92]` (prior-pass measurements). Statements that cite no
external source rest on internal evidence and are labelled `[DATA]`/`[INFERENCE]` where they appear.
