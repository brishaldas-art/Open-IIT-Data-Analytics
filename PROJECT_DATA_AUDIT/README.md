# PROJECT DATA AUDIT — official PS3 scope re-audit (v2, 2026-10-07)

> **STATUS NOTE — superseded by the final data policy (2026-10-07).** This folder is the *audit record* (outside the
> active PS3 workspace) and is retained for provenance. References here to a "Domain B", an "external candidate arm" or an
> augmentation experiment describe what was **evaluated during the re-audit**; the final project decision **rejected all
> external data permanently**. The binding statement is `PS3_SUTRA/PS3_FINAL_DATA_AND_ARCHITECTURE_FREEZE.md`: the PS3
> system uses only the official dataset and its officially assigned shared tables.



**What this folder is.** The official Drive folder (`data`: `ps1_fake_ptp` · `ps2_right_party_contact` · `ps3_geocoder` · `shared`) was re-audited from the files themselves. PS3's canonical scope is defined, every shared table is classified (A–G), every shared column is staged (T0–T4) and assigned a role, the canonical dataset is rebuilt hash-verified, and all audit/EDA numbers are recomputed on that scope. **No PS1 data, no PS2-only data, no PS1/PS2-derived field, no external data, and no artefact of earlier experiments is used in any PS3 artefact.**

## Verification (performed twice today)
Drive files downloaded and hashed: **21/21 byte-identical both times** (same file IDs, same timestamps → the Drive is unchanged). In-scope files re-copied: **12/12 hashes match the Drive**. FK orphans inside DATASET A: **0** (one deliberate `OUT` marker). Cleaning: **0 rows dropped, 0 coordinates moved, 0 labels invented**.

## The eight documents

| # | File | Answers |
|---|---|---|
| 1 | `PS3_OFFICIAL_DATA_SCOPE_REAUDIT.md` | Full 21-file classification table (required columns), A–G classification of all 8 shared tables with justification, structural audit of the excluded tables, DATASET A definition + relationship diagram, Task-6 twelve-question table, architecture-impact verdicts, revision path, corrections register |
| 2 | `PS3_SHARED_DATA_USAGE.md` | Per-table ten-dimension audit; the eight role classes; what actually changed (6 things) and did not (3); join-key reference; **appendix: all 75 shared columns classified by stage and role** |
| 3 | `PS3_UPDATED_DATA_AUDIT.md` | Recomputed audit: inventory, structural audit of all 8 shared tables, missingness, duplicates (definition-aware), FKs, coverage, temporal, geometry, **agent diagnostics**, town consistency, multi-address finding, candidate anchors, radius transfer, value/exposure, corrected replay, sharpened entity leakage, changed-numbers register |
| 4 | `PS3_UPDATED_EDA.md` | EDA re-answered on the corrected scope with the T0–T4 frame (as defined by this brief) and nine "EDA invalidates this assumption" findings |
| 5 | `PS3_UPDATED_DATA_LINEAGE.md` | Chain of custody, the forbidden-input register (including our own earlier artefacts), binding rules, provenance of the scope decision, custody note for the stale in-folder README |
| 6 | `PS3_UPDATED_LEAKAGE_MAP.md` | Feature × T0–T4 × lane map, the cold-start invariant, the dynamic-learning order of operations, entity-leakage register (36.0% place proximity), transform-fit discipline |
| 7 | `PS3_UPDATED_PREPROCESSING.md` | Cleaning rules A1–A9 and the five preprocessing lanes, evaluation contract, outputs, performance |
| 8 | `PS3_WORKSPACE_RECONCILIATION.md` | Task 9: every stale claim with its exact location, the corrected position, corrections C-1…C-5, experiment assumptions that may not be reused, actions taken and not taken |

Supporting: `PS3_UPDATED_BUSINESS_DATA_FLOW.md` (workflow/value read of the official data) · `data/official_ps3/` (DATASET A, 12 hash-verified tables) · `data/cleaned/` · `data/derived/` (17 artefacts incl. `updated_shared_column_map.csv`) · `data/drive_verification.csv` · `tools_updated/ps3_scope_audit.py` · `docs/PS3_DATA_REQUIREMENTS.md` (PS3-only) · v1 files remain in place as history; the seven named documents above are v2. Earlier non-PS3 artefacts were archived out of this folder on 2026-10-07 (`90_Archive/unrelated_non_ps3_artefacts_2026-10-07/`).

## The four corrections this pass issues (all toward better-evidenced statements)
1. **Warm/cold replay:** 56.0% warm vs **24.5% cold** (not "40.5% other post-cut" — that was the overall rate); val+test 56.7% vs 25.1%.
2. **FA009 time-window "anomaly" retracted** — every agent is 79.5–88.7% in 10:00–12:59 (schedule artefact); media duplication remains its only confirmed anomaly.
3. **Memory consistency** re-measured with a stated definition: 77.7 m (same agent) vs 75.8 m (different agent).
4. **Place sharing** measured directly: 81 co-located clusters / 191 addresses; same-account addresses are median 3,011.6 m apart (never merge by account).

## Boundaries observed
Drive read-only, nothing modified. No scraping, no external datasets, no augmentation, no synthetic rows, no manufactured labels, no training, no performance claims.

## Change set derived from this re-audit (2026-10-07)

The architecture amendments this re-audit mandates are implemented in `PS3_SUTRA` and recorded there, not here:
master architecture §8 (A0–A1, U1, M1, F1, L1, E1), source register group N `[S67]`–`[S73]`, decision log D25–D31, and
the deterministic tool `tools/place_block_folds.py` with its ledger `data/derived/ps3_place_blocks.csv`
(3,007 blocks / 5 spatially ordered folds; 39 blocks cross the official split).

Housekeeping closed in the same pass: `data/cleaned/cleaning_log_updated.csv` (rules A1–A9, 9×8) now exists and the two
flags are stated with their audited definitions (landmark-bearing remarks 208; duplicate-hash visits 172).
