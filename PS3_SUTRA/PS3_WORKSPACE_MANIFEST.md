# SUTRA — WORKSPACE MANIFEST

*Required deliverable. What is kept, what was removed, what is shared and why, which datasets exist, which are
temporary/private, and what is generated.*

Project: **SUTRA — Address Geocoder That Learns from Field Visits** (official Problem Statement 3).
Rule of this manifest: after this point, every artefact in the active tree answers one question —
**"How do we build the best Address Geocoder That Learns from Field Visits?"** Nothing else lives here.

---

## 1. Active tree (the whole workspace)

```
/home/user/
├── PS3_SUTRA/          ← the active workspace (52 files at first freeze; 120 catalogued / 31.85 MB after the consistency + contracts pass, 2026-10-07)
└── 90_Archive/         ← inactive, retained for provenance (182 files, 35 MB). Never cited by active documents.
```

| Area | Contents | Status |
|---|---|---|
| `PS3_SUTRA/*.md` | the document set (§2) | ACTIVE — the deliverable |
| `PS3_SUTRA/data/official_ps3/` | **DATASET A** — 12 CSV tables + 2 dataset READMEs | ACTIVE — read-only, hash-frozen |
| `PS3_SUTRA/data/external_research/` | reserved path only — **external data prohibited** (final data policy) | ACTIVE — **permanently empty**; the guard fails the build if anything is placed here |
| `PS3_SUTRA/data/cleaned/` | cleaned Domain-A tables + row-level cleaning log | ACTIVE — derived from A only |
| `PS3_SUTRA/data/derived/` | audit profiles, leakage map, candidates, features, labels, diagnostics, radius calibration | ACTIVE — reproducible |
| `PS3_SUTRA/tools/` | 13 tools + `section_manifest.csv` (hashes) | ACTIVE |

Verify at any time: `python3 tools/check_workspace.py` (invariants), `python3 tools/build_manifest.py` (hashes),
`bash tools/reproduce.sh` (every number in the document set).

**Dated note (2026-10-07, consistency + implementation-contract pass).** The architecture is LOCKED and normative
schemas now live in `PS3_IMPLEMENTATION_CONTRACTS_2026-10-07.md`: immutable train/eval protocol (S-Eval firewall =
145 addresses), synchronised graded-negative-evidence rule, append-only sync semantics, single-class feasibility counts
(12 GREEN · 3 YELLOW · 3 RED of 18), frozen vocabulary (official frozen baseline geocode arm; `request_purpose` ≠
`address_purpose` ≠ `eligibility`), and the offline field MVP (GREEN) versus distributed sync (RED).

**Dated note (2026-10-07, official-scope re-audit change set).** The assigned shared table `lenders.csv` was imported
into DATASET A byte-identical to the official Drive pack (hash recorded in the audit folder), taking the frozen tree to
**12 tables · 177,196 rows**; `tools/place_block_folds.py` and `data/derived/ps3_place_blocks.csv` were added
(Amendment A1); the manifest hash set was re-baselined; `check_workspace.py` now asserts 12 tables. No document was
silently rewritten — superseded figures carry their dates.

---

## 2. Documents retained (with the reason each one is here)

**Authored for this deliverable**

| File | Role |
|---|---|
| `PS3_SOURCE_REGISTER.md` | 50 external sources (S1–S50) + internal evidence (S90–S92): URL, what it proves, how used, licence class, claim labels. Any factual claim in this package resolves here. |
| `PS3_CANONICAL_SCHEMA.md` | the entity/field contract: 11 canonical tables, the two-dimension outcome vocabulary, CRS assumption, external→canonical mapping rule, versioning. |
| `PS3_DATA_AUDIT.md` | field-by-field audit of Domain A before cleaning, with the twelve traps and the evidence diagnostic. |
| `PS3_DATA_LINEAGE.md` | provenance of every byte: source, version, licence, transformation, consumer, retention. |
| *(+ the rest of the set in §6 — authored in this same pass)* | data cleaning, preprocessing, leakage, external research, real systems, red team, the nine architecture documents, model selection, experiment plan, cost, MLOps, API, novelty, decision log. |

**Retained PS3 reference documents (inputs, re-derived rather than trusted as conclusions)**

| File | Why retained | Why not deleted |
|---|---|---|
| `PS3_DEEP_INTERNET_RESEARCH.md` | the original problem analysis behind the requirements | still the richest statement of *what the problem is*; sources inside it are now catalogued in the register |
| `PS3_ASSUMPTIONS.md` | explicit assumption list — the thing red-teaming consumes | assumptions must be visible, not remembered |
| `PS3_ARCHITECTURE_REQUIREMENTS.md` | the requirement set the architecture must satisfy | the acceptance checklist for §23 of this package |
| `PS3_ADVANCED_ARCHITECTURE_RESEARCH.md` | deeper research on advanced blocks | evidence for the "advanced" options |
| `PS3_ARCHITECTURE_OPTIONS.md` | the option space (P1–P7) and the construction rule | the option space is the record of what was *not* chosen, and why |
| `PS3_ARCHITECTURE_SELECTION.md` | the prior selection decision (S0–S9) | kept as **input to be re-derived**, never as the answer; `PS3_MASTER_ARCHITECTURE.md` supersedes it as the binding design |

All six were checked line by line: no reference to the retired problem statement, no reference to retired files, no
dangling paths (`tools/check_links.py` → ALL RESOLVE).

---

## 3. Documents removed / archived (and why)

Everything below sits in `90_Archive/`, outside the active tree, hash-indexed in the archive's own `WORKSPACE.md`.

| Archive folder | Files | What it was | Why it is out |
|---|---|---|---|
| `ps2_removed_2026-10-06/PS2_SANKET_full/` | 88 | the entire retired problem statement's package (its data, audits, architectures, tools, documents) | **PS3-only instruction.** This is a different problem (voice collections), not a component of SUTRA |
| `ps2_removed_2026-10-06/joint_and_ps2_documents/` | 24 | documents that discussed both problems together, and the integration/"shared decision engine" thesis | a merged product is explicitly forbidden; keeping it would keep the old dependency alive |
| `ps2_removed_2026-10-06/prior_pass_drafts/` | 22 | earlier hypothesis drafts of the geocoder architecture (`_superseded/`), the solution-architecture drafts, the bibliography | superseded by this pass; the surviving ideas were re-derived in `PS3_MASTER_ARCHITECTURE.md` |
| `ps2_removed_2026-10-06/retired_tools/` | — | `divide_strict.py`, `fix_two_section_prose.py`, PS2 tooling | describe a workspace structure that no longer exists |
| `ps2_removed_2026-10-06/retired_zips/` | 3 + 2 | the frozen submission zips, the old `WORKSPACE.md`, `CHANGELOG_OF_REFRAME.md` | snapshots of a two-section workspace; retained for provenance, never rebuilt |
| `ps1_fake_ptp_not_used/` | 4 | a third problem statement's fake data | irrelevant to SUTRA; data must not sit next to a shippable dataset |
| `00_Root_Drafts_2026-10-06/` | 41 | loose root-level drafts from earlier passes | not part of the PS3 deliverable |

**Not one byte was deleted from a dataset.** Archive moves were made deliberate and reversible; the official dataset is
hash-frozen and its hashes are checked by `tools/check_leakage.py` on every run.

---

## 4. Shared files: what was kept, and the reason

| Shared item | Kept? | Reason |
|---|---|---|
| `agents.csv` (field-force roster) | **kept in Domain A** | the evidence-integrity layer needs per-collector behavioural baselines (the audit found one agent with 25.6% duplicate photos). It is a *quality* input, never a location feature |
| `accounts.csv` | **kept in Domain A** | a consumer prices a visit (DPD, outstanding, EMI) — the *why* of a field visit. No account field is a location feature |
| `splits.csv` | **kept in Domain A** | the official evaluation protocol; extended by `split_ledger` (entity- and time-aware) rather than replaced |
| `landmarks_poi.csv` | **kept in Domain A** | address-language prior only (14 distinct names — unusable as a coordinate target) |
| GPS trails | **kept in Domain A** | evidence geometry for the visit (agreement, dwell, deviation) — not a label |
| The old "shared" utilities bucket | **removed** | it existed to serve two problems from one code path; that is exactly the hidden dependency the instruction forbids |
| The old "shared decision engine" concept | **removed** | no merged product; SUTRA's decision layer is defined in `PS3_FIELD_EVIDENCE_ARCHITECTURE.md` and depends on nothing outside this tree |

---

## 5. Datasets

**DATASET A — `data/official_ps3/` (official, synthetic, canonical benchmark).**
12 tables (2026-10-07 official-scope re-audit): `accounts, addresses, agents, baseline_geocodes, field_visits,
landmarks_poi, lenders, localities, splits, surveyed_addresses, towns, visit_gps_points`. Read-only. Hashed. Audited at `PS3_DATA_AUDIT.md`. The dataset's own README
states the data is synthetic and that some tables are deliberately incomplete; that README is itself part of Domain A and
is hash-frozen (it mentions tables from the other problem statement — it is input, not authored prose, and we neither
edit nor rely on those mentions).

**Temporary / private data: none exists in the active tree.** The only private material is the *archive* (`90_Archive/`),
which is provenance for this workspace, not a data source, and is never read by any tool.

**No DATASET B exists — external data is prohibited (final data policy, 2026-10-07).**
External-data augmentation was considered during research but **rejected by final project decision**. The final PS3 system
uses only the official CreditNirvana dataset and the legitimately PS3-relevant shared data. The former candidate catalogue
is archived as REJECTED (`90_Archive/ps3_rejected_2026-10-07/PS3_EXTERNAL_DATA_RESEARCH.md`); register entries S39–S47 are
marked rejected. `tools/check_workspace.py` fails the build if any dataset file appears anywhere outside
`data/official_ps3/`, `data/cleaned/` and `data/derived/`, and fails if a file appears in `data/external_research/`.
Binding statement: `PS3_FINAL_DATA_AND_ARCHITECTURE_FREEZE.md`.

---

## 6. Generated artefacts (all reproducible, all hashed)

| Path | What it is | Produced by |
|---|---|---|
| `data/derived/ps3_audit_full.txt` | the full audit transcript (the evidence behind `PS3_DATA_AUDIT.md`) | `tools/ps3_audit.py` |
| `data/derived/ps3_table_profile.csv`, `ps3_column_profile.csv` | row/schema/dtype/null/uniqueness/cardinality profile | ″ |
| `data/derived/ps3_leakage_map.csv` | every field → T0/T1/T2/T3/T4 availability + leakage verdict | ″ |
| `data/derived/ps3_evidence_diagnostics.csv` | what a check-in is evidence of (truth vs pin convergence) | `tools/evidence_diagnostics.py` |
| `data/cleaned/*.csv` + `cleaning_log.csv` | cleaned tables from Domain A, one row per cleaning rule | `tools/clean_official.py` |
| `data/derived/candidates_{coldstart,warm}.csv` | candidate sets, each with arm, position, granularity, licence class | `tools/build_candidates.py` |
| `data/derived/features_{coldstart,warm}.csv` (+ `.receipt.json`) | feature matrices with a leakage receipt each | ″ |
| `data/derived/labels_eval_v2.csv` | labels for evaluation only (`label_within_100m`, `err_m`); S-Eval rows only | ″ |
| `data/derived/derived_ps3_radius_calibration.csv` | the radius table SUTRA must output, by stratum and by evidence type | `tools/build_derived_table.py` |
| `tools/section_manifest.csv` | every file: bytes, sha256, role, status, domain | `tools/build_manifest.py` |

**No model artefact exists, and none may be created until the document set is complete.** `tools/check_workspace.py`
enforces this (any `*.pkl/.joblib/.onnx/.pt` or `models/` directory fails the build).

---

## 7. Tooling map (PS3-only)

| Tool | Purpose | Reads | Writes |
|---|---|---|---|
| `ps3_audit.py` | 11-section audit of Domain A | Domain A (ro) | `derived/ps3_*` |
| `clean_official.py` | clean Domain A with a row-level log | Domain A (ro) | `cleaned/*` |
| `build_candidates.py` | candidate arms + T0 features + leakage receipts | A + cleaned | `derived/candidates_*`, `features_*`, `labels_eval` |
| `evidence_diagnostics.py` | what a check-in proves about a coordinate | Domain A (ro) | `derived/ps3_evidence_diagnostics.csv` |
| `build_derived_table.py` | the radius calibration table | Domain A (ro) | `derived/derived_ps3_radius_calibration.csv` |
| `check_leakage.py` | fails the build on leakage; proves Domain A unmodified | Domain A + derived | — |
| `check_workspace.py` | PS3-only invariants, no-premature-training, citations, structure | whole tree | — |
| `check_links.py` | every path reference in our prose resolves | whole tree | — |
| `build_manifest.py` | hash manifest of everything | whole tree | `tools/section_manifest.csv` |
| `reproduce.sh` | runs all of the above in order | — | — |

Retired and deleted in this pass (they targeted paths that no longer exist): `dataset_audit.py`, `check_section.sh`,
`build_package.sh`. Retired scripts that survive only in the archive: `divide_strict.py`, `fix_two_section_prose.py`.

---

## 8. Front door

`README.md` (rewritten PS3-only) is the entry point. The old front-door documents
(`README_PS3_SUTRA.md`, `HOW_TO_USE_AND_UNDERSTAND_THIS_PACKAGE.md`, `START_HERE_TEAM_HANDOFF.md`) were written for a
two-section workspace that no longer exists and are **archived**; their useful content (how to run the tools, how to
read the evidence tags) is folded into `README.md`. The final consolidated report (sections A–R) is delivered as the
headline document of this set.


---

**Sources.** External claims resolve in `PS3_SOURCE_REGISTER.md` (`[S1]`–`[S50]`); internal measurements are
`[S90]` (audit log `data/derived/ps3_audit_full.txt`), `[S91]` (radius calibration
`data/derived/derived_ps3_radius_calibration.csv`) and `[S92]` (prior-pass measurements). Statements that cite no
external source rest on internal evidence and are labelled `[DATA]`/`[INFERENCE]` where they appear.
