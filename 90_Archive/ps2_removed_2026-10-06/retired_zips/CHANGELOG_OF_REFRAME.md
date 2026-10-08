# CHANGELOG — workspace reframe, 6 October 2026

What moved, what changed, why, and how it was verified. Read with `WORKSPACE.md`.

---

## 1. Why the reframe was necessary

The workspace had grown by accretion. Every editing pass had left two copies of each document: a **working copy** at the root and the **shipped copy** inside `CreditNirvana_Submission/`. By 6 Oct 2026 the root held **41 loose files, 37 of them byte-identical duplicates** of package files and **3 superseded**. Two consequences, both real:

- **Ambiguity about truth.** A teammate reading `PS2_SANKET_SOLUTION_ARCHITECTURE.md` from the root would find the *hypothesis* version, while the package held the *final* version under a different name — with no marker at the root saying which was current.
- **Risk of divergence.** Two masters existed for two documents (`CreditNirvana_PS2_PS3_MASTER.md`, the reader's guide) and for the audit script. Editing the wrong copy would silently ship a stale deliverable.

A reframe was also the right moment to make the workspace **self-verifying**, since the whole submission rests on claims about numbers.

---

## 2. What changed

### 2.1 Structure — four tiers, one home per file

| Before | After |
|---|---|
| 41 loose files in the root, plus `dataset/`, plus the package, plus the zip | `CreditNirvana_Submission/` (deliverable) · `10_Inputs/` (raw inputs) · `20_Tools/` (machinery) · `90_Archive/` (history) · zip at root · `WORKSPACE.md` + this file |
| `dataset/` at root | `10_Inputs/dataset/` — inputs are read-only and visibly separated from deliverables |
| No machine-readable index | `20_Tools/workspace_manifest.csv` — 112 entries with tier, path, size, SHA-256 (12) and status |
| No way to rebuild or check anything | `reproduce.sh`, `build_package.sh`, `build_manifest.py`, `check_workspace.sh` |

### 2.2 Files archived (not deleted) — `90_Archive/00_Root_Drafts_2026-10-06/` (40 files)

- **37 byte-identical duplicates** of package files (verified by MD5 before moving: e.g. `PS2_ARCHITECTURE_SELECTION.md`, `SIMILAR_SYSTEMS_REVERSE_ENGINEERING.md`, `CN_QUESTIONS.md`, `financial_model.py`, both Phase-1 files, the demo HTML).
- **3 superseded versions**, kept because their filenames are what a teammate may search for:
  - `CreditNirvana_PS2_PS3_MASTER.md` (395 KB, pre-dataset-review and pre-Phase-4) → canonical is now the 768 KB master carrying Parts 0, I–XV.
  - `HOW_TO_USE_AND_UNDERSTAND_THIS_PACKAGE.md` (pre-Act-6) → canonical has the six-act structure.
  - `dataset_audit.py` (hard-coded `/home/user/dataset`) → canonical is path-portable.

Nothing was discarded: history is recoverable, and the archive is labelled *do not build from here*.

### 2.3 Content changes made during the reframe

| Change | File(s) | Reason |
|---|---|---|
| Path portability | `06_Dataset_Review/dataset_audit.py`, `build_derived_tables.py` | Were hard-coded to `/home/user/dataset`; now `$CN_DATASET` / `$CN_OUT` with new defaults |
| All stale paths rewritten (`/home/user/dataset` → `/home/user/10_Inputs/dataset`) | 8 documents incl. the master, the dataset review, the SANKET design and the bibliography | So every documented command still runs after the move; verified zero residual matches |
| Reproduce command simplified | `START_HERE_TEAM_HANDOFF.md` §6, master Part 0 | Now points at `./20_Tools/reproduce.sh` instead of four hand-typed invocations |
| Workspace map added | `WORKSPACE.md` (new) | Front door: tiers, rules, commands, health check |
| Reframe recorded | `CHANGELOG_OF_REFRAME.md` (this file) | Why the layout is what it is — so it is not "reorganised" back into ambiguity |

### 2.4 New machinery — `20_Tools/`

| Script | Does | Notes |
|---|---|---|
| `reproduce.sh` | Runs the four audit sections + regenerates both acceptance CSVs into `20_Tools/out/` | Exits with a clear message and the `gdown` command if the dataset is absent |
| `build_package.sh` | Deletes, rebuilds and verifies the zip; refreshes the manifest | The canonical release step — one command |
| `build_manifest.py` | Walks the workspace → `workspace_manifest.csv` (tier, path, bytes, sha256, role, status) | Excludes caches, `out/` and itself so it is drift-free |
| `check_workspace.sh` | 11 invariant checks, non-zero exit on failure | The regression test for the workspace |

---

## 3. Invariant checks now enforced

```
PASS  four top-level tiers exist (10_Inputs, 20_Tools, 90_Archive, package)
PASS  package has all 8 numbered folders
PASS  package root has README + reader's guide + team handoff
PASS  master document carries Parts 0, I, XIV, XV
PASS  no stale /home/user/dataset paths anywhere in the package
PASS  dataset present with 21 CSVs
PASS  scripts parse (no bytecode written)
PASS  acceptance-number tables present
PASS  manifest is current (regenerating produces no drift, excluding the rebuilt zip)
PASS  all [S-nn] citations resolve to the bibliography
PASS  zip exists and verifies
ALL CHECKS PASSED
```

Two of these caught real defects during the reframe and are worth remembering:

1. The manifest's first version hashed **itself**, guaranteeing drift on every regeneration; and `py_compile` had written `__pycache__` into the package (the zip had silently grown 856 KB → 892 KB with `.pyc` files). Both fixed: caches are excluded, the manifest skips itself, and the syntax check now parses with `ast` instead of writing bytecode.
2. The stale-path check would have failed on four documents after the move; they were rewritten and re-verified at zero residual matches — the bibliography, the dataset review, the SANKET design and the master.

---

## 4. Verification performed

- **Byte-level duplicate detection** (MD5) before archiving: 37 identical, 3 differing, 1 zip.
- **End-to-end reproduction:** `./20_Tools/reproduce.sh q` re-derived the acceptance numbers live — survey strata medians (rooftop 25.6 m / street 108.6 m / locality 385.9 m / pincode 1,375.8 m, n=100) and the policy baselines (incumbent all-calls RPC/call **0.1762**; dead-streak rule **0.1872**; first-ever-only 0.1333).
- **Package rebuild:** zip re-created and `unzip -t` clean — **54 files, 856 KB** (back to the correct content after removing the accidental `.pyc` entries).
- **All 11 invariants pass** on the reframed workspace.

---

## 5. What did *not* change

- **Every deliverable's content.** No claim, number, table or conclusion was altered by the reframe — only locations, paths and the tooling around them. The Phase-4 architecture files are byte-identical to what was delivered in the previous turn.
- **The naming of the deliverable folder.** `CreditNirvana_Submission/` keeps its name because that is the name in the instructions, the README and the zip — renaming it would break the reader's mental map for no structural gain.
- **The evidence discipline.** `[DATA]` / `[S-nn]` / `[VERIFIED]` / `[INFERENCE]` / `[ASSUMPTION]` / `[UNKNOWN]` tagging, the refusal ledger, and the "no claim we cannot defend" rule are untouched.

---

## 6. How to keep it reframed

1. **Write in the package, never at the root.** New documents go into the correct numbered folder; the root holds only the zip, `WORKSPACE.md` and this changelog.
2. **Ship with one command:** `./20_Tools/build_package.sh` (rebuilds zip → verifies → refreshes manifest).
3. **Before any hand-off:** `./20_Tools/check_workspace.sh` — if it prints anything other than `ALL CHECKS PASSED`, fix that first.
4. **If a document is superseded, move it to `90_Archive/` with the date**, and say in the new version what it replaced (the pattern used for `03_Architecture_Hypotheses/` and for the pre-Phase-4 files).

---

# CHANGELOG — PS2 / PS3 / SHARED division, 6 October 2026 (second entry)

## 1. What was asked

*"Make separate 2 sections of folders for PS2 and PS3, divide everything."*

## 2. What was done

The deliverable is now three sections. **Every one of the 45 files has been assigned to exactly one home**, by a written rule rather than by topic-similarity:

| Section | Content | Count |
|---|---|---|
| **`PS2_SANKET/`** | Assumptions · deep research · requirements · 12 architectures compared · 7 options scored · the selection · the final 30-section design · the superseded hypothesis · `data/derived_ps2_policy_baselines.csv` · its own brief (`README_PS2_SANKET.md`) | 16 files |
| **`PS3_SUTRA/`** | The same nine artefacts for PS3, incl. `data/derived_ps3_radius_calibration.csv` and `README_PS3_SUTRA.md` | 16 files |
| **`SHARED/`** | `00_MASTER_DOCUMENT` · `01_Phase1_Baseline_Research` · `02_Phase2_Strategy` · `03_Integrated_Architecture` · `04_Cross_PS_Research` · `05_Model_and_Demo` · `06_Dataset_Review` · `README_SHARED.md` | 16 files |

**The rule (stated in `WORKSPACE.md` and enforced by `20_Tools/build_ps_sections.py`):** a document with one owner lives in that owner's section; a document serving both problem statements lives in `SHARED/` — never duplicated, because two copies of a claim is how a submission starts disagreeing with itself.

**Why some things are in `SHARED/` deliberately:** the dataset is one dataset; the competitor landscape is one landscape; the integrated architecture exists precisely to join the halves; the master document is a concatenation of both. Assigning those to PS2 *or* PS3 would have been false. `SHARED/README_SHARED.md` states the reason per folder so the section is not read as a dumping ground.

## 3. Consequences carried through

- **Every internal reference rewritten.** 100+ path references across 8 documents (including the 768 KB master, which inlines them all) were remapped to the new sections — file-specific rules first, then folder-level rules — and one class of artefact was caught and cleaned: double-prefixing (`SHARED/SHARED/…`) in 5 files.
- **The acceptance tables moved to their owners.** `derived_ps2_policy_baselines.csv` → `PS2_SANKET/data/`, `derived_ps3_radius_calibration.csv` → `PS3_SUTRA/data/`, and `build_derived_tables.py` now writes each into its own section (`$CN_PS2_OUT` / `$CN_PS3_OUT`). A leftover reference to the removed `out` variable was found by actually running the script and fixed.
- **Three section briefs written** (not stubs): each has its purpose, reading order with status per file, its own measured numbers, frozen build scope, and the list of shared files it depends on with the reason.
- **Front-door documents updated:** `README.md` rewritten around the three sections; `START_HERE_TEAM_HANDOFF.md` §2 replaced with the section map and §4 workstreams tagged to their sections; the reader's guide's six acts and all reading paths re-pointed.
- **Tooling extended:** new `build_ps_sections.py` (idempotent division) and `check_index_links.py` (resolves 88 path references in the front-door docs); `check_workspace.sh` grew from 11 to **18 invariants**, now including *the pre-division folders are gone*, *each section holds its exact document set*, *the acceptance tables are not left in SHARED*, *the division is reproducible*, and *index links resolve*.

## 4. Verification

```
ALL CHECKS PASSED   (18 invariants)
  three sections + their briefs · pre-division folders gone · SHARED has 7 subfolders
  PS2 section: 9 documents + acceptance table · PS3 section: 9 documents + acceptance table
  tables not left in SHARED · master Parts 0 / I / XIV / XV · division reproducible (idempotent)
  no stale paths · 21 input CSVs · scripts parse · citations resolve
  index links resolve (88 checked) · manifest drift-free · zip verifies (48 files)
```

`./20_Tools/reproduce.sh` was re-run end-to-end after the division and still reproduces the acceptance numbers from the moved scripts, writing the two CSVs into the two PS sections.

## 5. What did not change

No claim, number, table, conclusion or recommendation was altered. Every file's **content** is byte-identical to the pre-division version apart from the path references listed in §3 — the division is structural.

## 6. Note on shell permissions

The workspace tools are marked executable (`chmod +x 20_Tools/*.sh`), but a snapshot restore can drop the mode bit. If `./20_Tools/check_workspace.sh` reports *Permission denied*, run it as `bash 20_Tools/check_workspace.sh`.

---

## 7. Second reframe, later the same day — strict two sections (supersedes the SHARED design)

### 7.1 What changed and why

The first reframe divided the package into `PS2_SANKET/` · `PS3_SUTRA/` · `SHARED/`, on the principle *one document,
one home*. That principle was correct for documents and wrong for a hand-over: a section could not be zipped and given
to one owner, because part of what that owner needs (the master document, the dataset review, the integrated
architecture, and three of the tables) lived in a third folder. The instruction was to make the workspace **strictly
two sections**, data included. So:

| Before (three sections) | After (two sections, this tree) |
|---|---|
| `CreditNirvana_Submission/{PS2_SANKET, PS3_SUTRA, SHARED}` | `CreditNirvana_Submission/{PS2_SANKET, PS3_SUTRA}` |
| 7 numbered folders under `SHARED/` (master, Phase 1, strategy, integration, cross-PS research, model/demo, dataset review) | The same 22 documents **duplicated inside each section**, same words, section-relative links |
| Tables split `shared/` · `ps2_…/` · `ps3_…/` under `10_Inputs/dataset/data` | `PS2_SANKET/data/raw/` (11 tables) and `PS3_SUTRA/data/raw/` (9); the three tables both designs read exist in **both**, byte-identical |
| `20_Tools/` at the root: reproduce · build_package · build_ps_sections · build_manifest · check_index_links · check_workspace | `tools/` **inside each section**: `dataset_audit.py` · `build_derived_table.py` · `reproduce.sh` · `check_section.sh` · `check_links.py` · `build_manifest.py` · `build_package.sh` · `financial_model.py` (+ output). The root-level machinery and `build_ps_sections.py` are retired |
| One zip of the package | `PS2_SANKET_Package.zip` · `PS3_SUTRA_Package.zip` · combined `CreditNirvana_PS2_PS3_Deliverables.zip` |
| 18-check `check_workspace.sh` | 14-check `check_section.sh` per section (includes "no old shared-bucket references anywhere", "no stale paths", "every link resolves", "reproduces its numbers", "sibling exists") |

### 7.2 The duplication rule, stated once

- **A document needed by both sections** exists twice — one copy per section — identical except for paths that point
  at the sibling (`../OTHER/…`). **Edit one, edit the other.** Nothing is silently shared.
- **A table read by one design** lives in that section only. **A table read by both** lives in both, proven
  byte-identical (`cmp`), because a section must be able to reproduce its own numbers alone.
- That leaves exactly three shared copies: `accounts.csv`, `addresses.csv`, `field_visits.csv`.

### 7.3 The one placement that is outside both sections

The Drive folder also contained **PS1** data — `ptps.csv`, `call_transcripts.csv`, `post_call_events.csv`,
`annotated_ptp_sample.csv` (4.0 MB, the sample partly mislabelled). PS1 is a *third* problem statement
(promise-to-pay) that neither the PS2 nor the PS3 design consumes. It is preserved at
`90_Archive/ps1_fake_ptp_not_used/` with a README explaining the exclusion, rather than forced into a section where it
would be a false placement. Flagged in both section briefs and in `data/README_DATA_PS2.md` / `README_DATA_PS3.md`.

### 7.4 Prose and path repairs made during the split

- Every reference to the retired third bucket and the numbered folders was rewritten in **both copies** of every
  front-door document: `README.md`, `HOW_TO_USE_AND_UNDERSTAND_THIS_PACKAGE.md`, `START_HERE_TEAM_HANDOFF.md`,
  `README_PS2_SANKET.md` / `README_PS3_SUTRA.md`, and `CreditNirvana_PS2_PS3_MASTER.md` (§2 map, command blocks, the
  Part XV note).
- Table references were re-pointed: `shared/x.csv` → `data/raw/x.csv`, `ps2/…` and `ps3/…` → the owning section's
  `data/raw/`, with cross-section references given the explicit `../OTHER/data/raw/…` form.
- Command blocks now name the section-relative tools (`bash tools/reproduce.sh`, `bash tools/check_section.sh`,
  `bash tools/build_package.sh`, `python3 tools/build_manifest.py`) and the Drive re-fetch writes to `/tmp` before the
  tables are flattened into `data/raw/`.
- Added `data/README_DATA_PS2.md` and `data/README_DATA_PS3.md`: per table — what it is, why *this* section needs it,
  which tables were left to the sibling and why, and the traps each table carries.
- `tools/dataset_audit.py` (one file, duplicated) now **audits whichever section it lives in**: the inventory lists the
  tables actually present and names the ones the sibling holds, and a requested audit section whose tables belong to
  the sibling is skipped with a pointer instead of crashing. `tools/reproduce.sh` defaults to `q p2 eco` (PS2) and
  `q p3 eco` (PS3).
- Both sections' `build_manifest.py` and `check_section.sh` labels were corrected (the PS3 copies had inherited the
  PS2 strings).

### 7.5 Verification on this exact tree

```
PS2_SANKET: ALL CHECKS PASSED     PS3_SUTRA: ALL CHECKS PASSED      (14 invariants each)
reproduce.sh  PS2 (q p2 eco) exit 0   ->  data/derived/derived_ps2_policy_baselines.csv  (0.1762 -> 0.1872, -12.5% calls)
reproduce.sh  PS3 (q p3 eco) exit 0   ->  data/derived/derived_ps3_radius_calibration.csv (baseline median 376 m; pincode 1336 m)
document links: PS2 50 checked / 0 broken · PS3 45 checked / 0 broken
cmp: accounts.csv · addresses.csv · field_visits.csv byte-identical across the two sections
manifest: 87 (PS2) + 73 (PS3) files hashed with role and status
prose scan: no reference to the retired shared bucket or the numbered folders anywhere in the live tree
zips: PS2_SANKET_Package.zip 88 files / 3.0 MB · PS3_SUTRA_Package.zip 74 files / 3.2 MB
      CreditNirvana_PS2_PS3_Deliverables.zip 209 files / 7.8 MB (+ 90_Archive, WORKSPACE.md, this changelog)
cold test: each section zip unzipped on its own -> ALL CHECKS PASSED (14/14, links inside the section resolve,
           cross-section links reported as unverified rather than broken); the combined zip -> both sections PASS
```

`tools/dataset_audit.py` is byte-identical in both sections by design (it is section-aware); every other duplicated
document is identical except for section-relative links.

### 7.6 What did not change

No number, table, conclusion or recommendation was altered. The dataset is the same 21 CSVs; the two acceptance tables
reproduce their published values; the Phase-4 architecture, the decision log, the reverse-engineering study and the
front-door documents' substance are untouched. This reframe is structural plus the prose repairs listed in §7.4.
