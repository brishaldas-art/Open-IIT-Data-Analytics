# PS3 UPDATED LEAKAGE MAP (v2)

**Stage definitions (this pass adopts these; v1 used a different T2/T3 split):**
**T0** available when the address/query first arrives · **T1** during candidate generation/resolution · **T2** available before a field visit · **T3** generated during/after a field visit · **T4** future / post-outcome information.

**Cold-start rule (the invariant):** *a field may not be used for a cold-start prediction if it only exists after the outcome.* Translated to this task: **no T3/T4 field of an address may inform the prediction for that same visit**; warm lanes may use the **earlier-visit** values of that address only.

**Lanes:** COLD (no prior evidence) · WARM (prior evidence from *earlier* visits) · FIELD-EVIDENCE (offline aid at T2) · RETRAIN (later corpora, eligibility-gated).
**Transform-fit discipline:** vocabularies, weights, radius tables and place clusters are fit on **train-split data only** and validated on val/test.

---

## 1. Feature × stage × lane × verdict

| Feature | Stage | Source | COLD | WARM | FIELD-EVIDENCE | RETRAIN | Leakage verdict |
|---|---|---|---|---|---|---|---|
| `address_text` + its T0 derivatives | T0 | `addresses` | ✔ | ✔ | ✔ | ✔ | none |
| Gazetteer hits (locality/pincode/landmark) | T0 | `localities`, `landmarks_poi` | ✔ | ✔ | ✔ | ✔ | none (static reference) |
| `town_id` (+ account-town consistency check) | T0 | `addresses` (+`accounts`) | ✔ | ✔ | ✔ | ✔ | none; account town does **not** locate `OUT` addresses |
| Vendor pin + `precision` stratum | T0 | `baseline_geocodes` | ✔ | ✔ | ✔ | ✔ | none — legitimate incumbent answer; publish a no-pin arm too (237) |
| Co-location / finer-pin anchors (96.7% of coarse cases) | T1 | derived from T0 | ✔ | ✔ | ✔ | ✔ | none |
| Account exposure fields (`dpd_start`, `bucket_start`, `portfolio`, `income_type`, `preferred_language`) | T0 | `accounts` | ✘ | ✘ | ✘ | ✘ | **yes if used** — wrong variable class (targeting, not place). EXPOSURE ONLY |
| Account value fields (`outstanding`, `emi_amount`, `overdue_start`) | T0 | `accounts` | ✘ | ✘ | ✘ | ✘ | yes if used — business context only |
| `address_type`, `source`, `added_date` | T0 | `addresses` | ✘ | ✘ | ✘ | ✘ | no leak, but off-target (exposure / context / time axis) |
| Agent attributes (`agent_id`, `channel`, `town_id`, `tenure_months`, `language_team`, `shift`) | T2 | `agents` | ✘ | ✘ | ✘ | ✘ | **yes if used as features** — models the collector. INTEGRITY/EXPOSURE only |
| `checkin_x/y`, `checkin_ts`, `gps_accuracy_m`, `dwell_s` | **T3** | `field_visits` | ✘ same visit | ✔ earlier visits | ✔ display | ✔ eligible | **yes for the same visit** — post-visit by construction |
| `outcome` | **T3** | `field_visits` | ✘ same visit | ✔ earlier visits | ✔ display | ✔ eligible | as above; `address_not_traceable` never a negative location |
| `remark` | **T3** | `field_visits` | ✘ same visit | ✔ extraction lane | ✔ display | ✔ research lane | yes if trained as a label — extract, never target |
| `photo_hash`, `start_ts` | T3 | `field_visits` | — | — | — | — | INTEGRITY/MONITORING only |
| `ptp_id` | T3 | `field_visits` | ✘ | ✘ | ✘ | ✘ | cross-domain; EXCLUDED |
| `surveyed_addresses.x/y` | — | ground truth | ✘ | ✘ | ✘ | ✘ | **catastrophic if used** — EVALUATION ONLY |
| `splits.split` | T0 protocol | `splits` | — | — | — | — | protocol, not a feature |
| `dial_attempts.*`, `payments.*` | T2/T4 | excluded tables | ✘ | ✘ | ✘ | ✘ | cross-domain / post-outcome; **out of official scope** |

The full 75-column stage + role classification is printed as an appendix to `PS3_SHARED_DATA_USAGE.md` and stored at `data/derived/updated_shared_column_map.csv` (stages: T0 35 · T2 8 · T3 11 · T4 3 · out-of-scope 18).

## 2. The dynamic-learning order of operations (T0→T4, enforced)

1. **T0** the address arrives → candidates built from text + gazetteer + vendor pin only.
2. **T1** candidates scored; no outcome-conditioned term may appear.
3. **T2** the offline pack (candidates, radius, directions, **earlier-visit memory only**) is dispatched.
4. **T3** the visit appends evidence (check-in, trail, dwell, photo hash, outcome, remark). Append-only; server-authoritative.
5. **T4** evidence enters place memory, radius calibration and retraining corpora **after** the visit, and may only inform **future** decisions.
**Replay rule:** for every scored visit, reconstruct exactly what was known *before* it — the 2026-05-15 cut test is the template.
**Prohibition list (all verified absent from every artefact):** future field-visit outcomes · surveyed truth · post-visit coordinates · model-derived labels · future-memory state · post-outcome fields.

## 3. Entity-leakage register (v2, sharpened)

| Channel | Measured | Mitigation |
|---|---|---|
| Surveyed truths on train accounts | **66 / 100** (val 19, test 15) | report split-aware; treat the 66 as development data |
| Identity-key text overlap test→train | **1 of 459** test addresses | small in text terms — do not overstate text leakage |
| Near-duplicate pairs crossing splits | 73 / 161 | publish split-aware |
| **Place proximity: met test addresses within 30 m of a train met check-in** | **124 / 344 = 36.0%** (279 within 100 m) | the official split cannot be fixed; memory features must be validated **without crossing splits**, and place-level claims must state this |
| Co-located clusters crossing splits | 58 / 127 | same |
| Memory premise on train entities | 38 met-surveyed → 23/15 | **re-verified**: val+test 21.1 m vs pin 383.7 m, better in 80% |

## 4. Cold / warm boundary

- **Cold** (no prior evidence): 1,640 of 3,117 addresses. T0 features + candidates + vendor arm + no-pin arm only.
- **Warm** (≥1 earlier visit): 1,477 addresses, 900 with positive evidence. May add place memory (median re-visit consistency 77.7 m), radius calibration, cluster priors — **from earlier visits only**.
- **Boundary is per visit, not per address**; negative outcomes lower candidate confidence, never create or confirm a location.

## 5. Verdict

The corrected scope adds **no new leakage surface** relative to v1: exactly one shared column is a model feature (`address_text`), seven are field-evidence inputs used strictly after the fact, and the two largest shared tables are out of scope entirely. What v2 adds is precision: **36.0%** place-proximity overlap between test and train evidence, the corrected warm/cold magnitudes, and the explicit T0–T4 classification of all 75 shared columns.
