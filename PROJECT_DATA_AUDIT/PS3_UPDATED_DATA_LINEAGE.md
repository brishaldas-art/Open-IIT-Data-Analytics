# PS3 UPDATED DATA LINEAGE (v2)

**Principle:** the official Drive is read-only and authoritative; everything PS3 produces is downstream of a copy whose bytes are provably identical to it; **no other data source exists anywhere on the chain** — no PS1 file, no PS2-only file, no PS1/PS2-derived field, no external, scraped or augmented data, and no artefact of our own earlier experiments.

---

## 1. The chain

```
[1] DRIVE (authoritative, read-only, never modified)
    data/  →  ps1_fake_ptp/ (4)   ps2_right_party_contact/ (3)   ps3_geocoder/ (6)   shared/ (8)
    21 files · 288,754 rows · 149 columns
        │  download + SHA-256  (2026-10-07, twice: morning and this pass)
        ▼
[2] VERIFICATION   data/drive_verification.csv
    21/21 byte-identical BOTH times (same file IDs, same timestamps) → the Drive has not changed
        │  scope decision = official assignment (pack README) + verified FK structure
        ▼
[3] DATASET A      data/official_ps3/   12 files · 177,196 rows · 83 columns
    PS3-specific: towns · localities · landmarks_poi · baseline_geocodes · visit_gps_points · surveyed_addresses
    Shared (PS3): accounts · addresses · agents · field_visits · lenders · splits
    receipts: data/derived/updated_scope_receipts.csv  →  12/12 hashes match the Drive
        │  cleaning (non-destructive; raw never overwritten)
        ▼
[4] CLEANED        data/cleaned/
    addresses_scope_clean.csv (3,117×15) · visits_scope_clean.csv (5,578×21) · cleaning_log_updated.csv (rules A1–A9)
        │  derived analysis
        ▼
[5] DERIVED        data/derived/   (17 files)
    profile · fk_checks · address_split_chain · place_duplicate_groups · near_duplicate_pairs ·
    cross_address_proximity · agent_coverage · agent_diagnostics · selection_bias · remark_by_outcome ·
    lender_style · same_account_address_pairs · coarse_pin_nearest_fine · radius_by_stratum ·
    value_exposure · shared_column_map · scope_receipts
```

## 2. What may enter PS3, and what can never enter it

| Category | Status | Items |
|---|---|---|
| Official, in scope | **allowed** | the 12 tables of DATASET A, each under its role class (`PS3_SHARED_DATA_USAGE.md`) |
| Official, out of scope | **forbidden** | `dial_attempts`, `payments` (PS1+PS2); `phones`, `skip_traces`, `verified_contact_points` (PS2); the four PS1 files |
| Derived from out-of-scope tables | **forbidden** | any statistic, feature, label, weight, filter or split built on the nine excluded tables |
| Our own earlier artefacts (v1 candidate sets, benchmark-style files, labels, diagnostics) | **forbidden as data** | usable only as *reference documents*; they may inform rules, never inputs or labels |
| External / scraped / augmented | **forbidden in this pass** | not read, not counted, not substituted; a separate, controlled decision later |
| Ground truth | **evaluation only** | `surveyed_addresses` — never a feature, never a training label, never a prior |
| Field evidence | **T3/T4 lanes only** | earlier visits may inform later decisions; never the visit that produced them |

## 3. Binding rules

1. **Raw is read-only**; every transformation writes a new file.
2. **Every derived file is reproducible** from `tools_updated/ps3_scope_audit.py` on DATASET A alone.
3. **Row-count invariants:** 3,117 addresses · 5,578 visits · 160,406 GPS points · 2,880 pins · 100 surveyed truths. This pass moved **0** coordinates, dropped **0** rows, invented **0** labels.
4. **Every number traces to a file**; anything not recomputable is not a claim.
5. **Exclusions are listed, not implied** — the defect that triggered this re-audit.
6. **No silent overwrite:** corrections are appended with dates (see `PS3_WORKSPACE_RECONCILIATION.md`).

## 4. Provenance of the scope decision

| Link | Evidence |
|---|---|
| Which files the Drive holds | folder listings (four folders, CSVs only, Oct-4 timestamps) |
| Which problem statements each file serves | the pack README, held in two mutually independent copies whose assignment rows agree (differing only in re-pathed path strings) |
| Arrival corroboration | `90_Archive/.../PS2_PS3_DATASET_REVIEW.md` (same four folders, same per-PS lists) |
| Structural corroboration | all FKs resolve inside DATASET A (0 orphans; 1 deliberate `OUT` marker) |
| Explicitly rejected evidence | the archived **PS2-era README** ("PS2 only" labels on agents/splits/lenders/payments) — PS2's own consumption list, contradicted by the official README; never cited by active documents |
| Honest limitation | the Drive carries no documentation of its own; if the organisers publish a different assignment, §7 of the re-audit states the exact revision path |

## 5. Two-layer custody of the found defect

Our own in-folder `data/official_ps3/README_DATA_PS3.md` (authored by us, sitting inside the frozen folder) contains a §2 that labels `splits.csv`, `agents.csv`, `lenders.csv` as "PS2-owned case data" and claims only **three** shared tables belong to PS3. **That is the stale scope claim this re-audit corrects.** The file is inside the hash-frozen folder, so it was **not edited**; the correction lives in the v2 documents and in the reconciliation record, and moving the file out of the frozen folder (the already-logged O-5 recommendation) remains the clean fix. Nothing was silently rewritten.
