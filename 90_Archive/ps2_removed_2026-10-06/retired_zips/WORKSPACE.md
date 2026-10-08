# WORKSPACE — CreditNirvana PS2 + PS3

**Restructured 6 October 2026 (second reframe).** The workspace is now **strictly two sections**, one per problem
statement — `PS2_SANKET/` and `PS3_SUTRA/` — each self-contained down to its own data, tools and history. There is no
shared bucket. The only thing that lives outside the two sections is the PS1 tables, deliberately archived and flagged.

---

## The map

```
/home/user
├── CreditNirvana_Submission/
│   ├── PS2_SANKET/          ← SECTION 1 · SANKET — PS2 (88 files, 13 MB)
│   │   ├── README_PS2_SANKET.md · README.md · HOW_TO_USE_AND_UNDERSTAND_THIS_PACKAGE.md · START_HERE_TEAM_HANDOFF.md
│   │   ├── 9 PS2 documents (assumptions → deep research → requirements → 12 architectures → 7 options → selection → FINAL)
│   │   ├── 22 joint documents, duplicated here (master, Phase-1 research, strategy, integrated architecture, cross-PS research, dataset review, demo)
│   │   ├── data/raw/        11 tables + DATASET_README.md + README_DATA_PS2.md        (read-only, synthetic)
│   │   ├── data/derived/    derived_ps2_policy_baselines.csv                          (the acceptance table)
│   │   ├── tools/           dataset_audit.py · build_derived_table.py · reproduce.sh · check_section.sh
│   │   │                    check_links.py · build_manifest.py · build_package.sh · financial_model.py (+ output)
│   │   └── _superseded/     32 earlier drafts, kept as the reasoning record
│   └── PS3_SUTRA/           ← SECTION 2 · SUTRA — PS3 (74 files, 12 MB) — same shape
│       ├── data/raw/        9 tables (shares accounts · addresses · field_visits, byte-identical)
│       └── data/derived/    derived_ps3_radius_calibration.csv
├── 90_Archive/
│   ├── ps1_fake_ptp_not_used/      ← the 4 PS1 tables: a third problem statement, used by NEITHER design
│   └── 00_Root_Drafts_2026-10-06/  ← pre-division root drafts, history only
├── PS2_SANKET_Package.zip · PS3_SUTRA_Package.zip · CreditNirvana_PS2_PS3_Deliverables.zip   (built by tools/build_package.sh)
└── WORKSPACE.md · CHANGELOG_OF_REFRAME.md
```

### The division rule (and the only exception)

| Where | What goes there | Rule |
|---|---|---|
| **`PS2_SANKET/`** | Everything that defines, researches, scores or specifies PS2 — own documents, own brief, own tables, acceptance table, tools, history | One owner per file. Nothing PS2 needs may live outside this folder |
| **`PS3_SUTRA/`** | The same for PS3 | Same rule |
| **Both sections** | The master document, Phase-1 research, strategy/competitor/finance/red-team, the integrated architecture, cross-PS research, the dataset review, the demo, the three front-door files | Needed by both ⇒ **duplicated inside both**, same words, section-relative links. Cross-section references are relative (`../OTHER/…`) |
| **`data/raw/`** | A table with one consumer ⇒ that section only. A table both designs read ⇒ **both**, as a byte-identical copy | `accounts.csv`, `addresses.csv`, `field_visits.csv` are the three copies; `cmp` proves them |
| **`_superseded/`** | Anything replaced: earlier Phase-2 material, intermediate files, the pre-division audit script | Labelled, never deleted — the reasoning trail is part of the deliverable |
| **`90_Archive/ps1_fake_ptp_not_used/`** | PS1 (promise-to-pay) tables that came in the same Drive folder | **Outside both sections by design.** Neither design consumes them; placing them in a section would be a false placement. Flagged in every front-door document |

**Consequence to remember:** the duplicated documents are two physical copies. Fix prose in one, fix it in the other —
or regenerate both. The check script enforces the parts that must not drift.

---

## Entry points

| You are | Start here |
|---|---|
| **A teammate about to build** | `CreditNirvana_Submission/START_HERE_TEAM_HANDOFF.md` (identical in both sections) → then your section's brief: `PS2_SANKET/README_PS2_SANKET.md` or `PS3_SUTRA/README_PS3_SUTRA.md` |
| **A judge, mentor or reviewer** | `CreditNirvana_Submission/PS2_SANKET/README.md` (or the PS3 copy) → `CreditNirvana_PS2_PS3_MASTER.md` **Part I** — the 20 conclusions. The master file also carries Part 0 (handoff), Parts II–XIII, **Part XIV** (dataset review) and **Part XV** (all 13 architecture files) |
| **Someone auditing our numbers** | `PS2_PS3_DATASET_REVIEW.md` §11, then run the section's `tools/reproduce.sh` yourself |
| **Someone asking "why did you use these tables?"** | `data/README_DATA_PS2.md` / `data/README_DATA_PS3.md` — every table, why the section needs it, and what was deliberately left to the sibling |

---

## Commands

```bash
cd /home/user/CreditNirvana_Submission/PS2_SANKET        # or PS3_SUTRA — identical tooling

# 1. Reproduce every number this section quotes + rebuild its acceptance table
bash tools/reproduce.sh             # PS2 default: q p2 eco  |  PS3 default: q p3 eco
bash tools/reproduce.sh p2 eco      # selected audit sections only (PS3: p3)

# 2. Rebuild this section's zip and refresh the combined zip; then the manifest
bash tools/build_package.sh         # -> ../PS2_SANKET_Package.zip and ../CreditNirvana_PS2_PS3_Deliverables.zip
python3 tools/build_manifest.py     # -> tools/section_manifest.csv

# 3. Invariant checks — 14 rules; must print ALL CHECKS PASSED before any hand-off
bash tools/check_section.sh

# 4. If a section's tables are ever missing (synthetic, 21 MB in total)
pip install gdown
gdown --folder "https://drive.google.com/drive/folders/18iqIR8TjXDqf9-hgEY34uJr_DraIl_3P" -O /tmp/cn_drive
# → flatten the subfolders into data/raw/*.csv ; ps1_fake_ptp → 90_Archive/ps1_fake_ptp_not_used/
```

**Environment:** Python 3 with `pandas` + `numpy`. Every script is section-relative and path-portable —
`dataset_audit.py` and `build_derived_table.py` read this section's `data/raw` (override with `$CN_DATASET`) and write
to `data/derived` (override with `$CN_OUT`). `dataset_audit.py` audits whichever section it lives in; asked for a
section whose tables belong to the sibling, it skips with a pointer instead of faking a result.

---

## Health check (last run: 6 Oct 2026, on this exact tree)

```
PS2_SANKET: ALL CHECKS PASSED     PS3_SUTRA: ALL CHECKS PASSED          (14 invariants each)
  brief present · 9 own documents · cross-cutting documents · master Parts 0/I/XIV/XV
  own tables present (11 / 9) · acceptance table present · no sibling-only table leaked in
  tools parse · no old shared-bucket or pre-division folder reference anywhere in the live tree
  no stale dataset paths · scripts parse · hand-off ready · the section reproduces its numbers
  links: PS2 50 inside-section + 41 cross-boundary, 0 broken · PS3 45 + 48, 0 broken
reproduce.sh(PS2) q p2 eco -> exit 0   data/derived/derived_ps2_policy_baselines.csv  (0.1762 → 0.1872, −12.5% calls)
reproduce.sh(PS3) q p3 eco -> exit 0   data/derived/derived_ps3_radius_calibration.csv (baseline median 376 m; pincode 1336 m)
cmp: accounts.csv · addresses.csv · field_visits.csv byte-identical across the two sections
manifest: 87 (PS2) + 73 (PS3) files hashed with role and status
zip: PS2_SANKET_Package.zip 88 files / 3.0 MB · PS3_SUTRA_Package.zip 74 files / 3.2 MB
     CreditNirvana_PS2_PS3_Deliverables.zip 209 files / 7.8 MB (both sections + 90_Archive + WORKSPACE.md + CHANGELOG)
cold test: each section zip extracted alone -> ALL CHECKS PASSED (14/14)
           combined zip extracted -> both sections ALL CHECKS PASSED
```

**Current state:** 162 deliverable files (88 PS2 + 74 PS3 — 22 documents exist twice by design), 20 raw tables
(11 + 9, three of them shared copies), 2 acceptance tables, 9 tools per section, 52 superseded drafts, 45 archived
files, 3 verified zips.

---

## The discipline this layout enforces

1. **Self-containment is the point.** Each section can be handed to one owner, zipped, and read end to end without
   reaching outside itself — including its data. A section that needs a file from its sibling is a bug.
2. **Duplication is explicit and checkable.** Where a document serves both PSes it exists twice, and the three shared
   tables are proven byte-identical by `cmp`; there is no invisible third folder that can silently drift.
3. **Inputs are immutable.** `data/raw/` is read-only; conclusions flow one way, into `data/derived/`.
4. **Claims are reproducible.** `tools/reproduce.sh` re-derives every dataset figure; `tools/check_section.sh` fails
   loudly if a document link breaks, a stale path returns, or the acceptance number stops reproducing.
5. **Superseded work is labelled, not deleted** — `_superseded/`, the two SUPERSEDED hypotheses, and `90_Archive/`.
6. **The PS1 exception is stated, not hidden.** Four tables from a third problem statement sit outside both sections,
   and every front-door document says so and why.
