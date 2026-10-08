# PS3 WORKSPACE RECONCILIATION — stale claims, their locations, and what replaces them

**Purpose (Task 9):** identify and report stale assumptions in the existing workspace, name the exact file and line where each lives, state what the official data actually says, and record the correction — **without silently overwriting history**. Corrections are appended with dates; source documents inside the hash-frozen folder are never edited.

**Method:** claims were verified by reading the files (grep + direct inspection), and every replacement number was recomputed from the official Drive copy in this pass.

---

## 1. The three claims this re-audit was asked to check — verdicts

| Asked | Verdict | Exact location | What is actually true |
|---|---|---|---|
| "The previous claim that only accounts/addresses/field_visits were shared with PS3" | **CONFIRMED — and it is the root defect.** One document states PS3's shared set is exactly those three tables | `PS3_SUTRA/data/official_ps3/README_DATA_PS3.md`: *"including byte-identical copies of the **three** tables PS2 also uses"* and §2, which lists `splits.csv`, `agents.csv`, `lenders.csv` as "PS2-owned" and therefore "deliberately not here" | The official assignment makes **six** shared tables PS3-relevant: `addresses`, `field_visits` (PS2+PS3) plus `accounts`, `agents`, `splits`, `lenders` (PS1+PS2+PS3). All six are now in DATASET A |
| "agents/splits classified as PS2-only" | **CONFIRMED, in two places** | (1) the same §2 of `README_DATA_PS3.md` ("PS2-owned contact and case data" covering `splits`, `agents`, `lenders`); (2) `90_Archive/.../PS2_SANKET_full/data/README_DATA_PS2.md` lines 18–25, which label agents/splits/lenders/payments "**PS2 only**" | `agents.csv` and `splits.csv` are assigned to **all three** problem statements in the official README; `splits.csv` even carries the line "All three also use splits.csv", and `agents.csv` appears in the PS3 file list verbatim |
| "Outdated dataset README statements" | **CONFIRMED — five items** | all inside `data/official_ps3/README_DATA_PS3.md` (our authored file, inside the frozen folder) | see §2 below |

No other active document contains these claims: the six PS3-side architecture/EDA documents either never discuss scope or (since v1 of this re-audit) state the six-table position.

## 2. `README_DATA_PS3.md` — every stale item, with its replacement

| # | Stale statement in that file | Correct position (recomputed 2026-10-07) |
|---|---|---|
| 1 | §2: shared tables beyond three are "PS2-owned" → `splits`, `agents`, `lenders` excluded | All six PS3-relevant shared tables are in DATASET A; roles per `PS3_SHARED_DATA_USAGE.md` |
| 2 | "integrity findings (645 check-ins >500 m from their own trail)" | **Retracted.** Check-in → nearest own-trail point: median 7.6 m, max 90.8 m, 0 visits >100 m (the 645 figure measured to the trail *centroid*) |
| 3 | "rooftop 37.7 m → pincode 1,336.5 m" radius chain | Superseded by the per-stratum fit on the official truths: locality p50 400.3 m / p80 539.9 m (n=49 train); street p50 116.1 m (n=11); pincode p50 925.5 m with **n=6 — no publishable radius** (transfer fails) |
| 4 | "the locality ceiling (379 m)" | Superseded: with the current arms the locality arm measures **356.7 m** (65.9% coverage); the free-data oracle over the three arms is **306.2 m** (earlier "370 m" figure retired) |
| 5 | Drive ID `18iqIR8TjXDqf9-hgEY34uJr_DraIl_3P`; `../PS2_SANKET/` paths; `tools/check_section.sh` | The live authoritative folder is `11J0vOHyjHH0y4Vjw8_5HZxsBWyVgH48t`; the retired-project paths and the retired tool reference no longer resolve and are not used by anything active |

**Disposition:** the file sits inside the hash-frozen official folder, so it was **not edited**. Corrections live here and in the v2 documents. The standing recommendation (logged as O-5 in the workspace decision record) is to **move it out of the frozen folder, rewrite it against the v2 scope, and re-baseline the hash set** — to be executed deliberately, not silently.

## 3. Stale figures elsewhere — corrections of record (this pass)

| # | Figure | Where published | Correct now |
|---|---|---|---|
| C-1 | "56.0% vs **40.5% for all other post-cut visits**" | workspace business document (7 occurrences: §E, §G, §L, P3, X2) and v1 audit docs | 40.5% is the **overall** post-cut rate. Correct: **warm 56.0% (n=1,383) vs cold 24.5% (n=1,343)**; val+test: **56.7% vs 25.1%**. The finding is stronger than published |
| C-2 | "FA009: 83% of check-ins 10:00–13:00 — missed-slot anomaly" | probe-level claim, not in an active document | **Retracted** — every agent is 79.5–88.7% in that window (schedule artefact). FA009's only confirmed anomaly: media duplication, 162/610 visits |
| C-3 | "same-agent 90.0 m vs different-agent 98.0 m" | workspace business document | Re-measured with stated definition (median of per-address medians, 563 addresses): **77.7 m vs 75.8 m** — same conclusion (agent-independent), definitions now printed |
| C-4 | "5 duplicate-text groups / 10 rows" as the place-sharing measure | workspace EDA + cleaning report | Identity key 5 groups / 10 rows **plus** render-key 70 groups / 203 rows (template families), and the direct measure: **81 co-located clusters / 191 addresses**; same-account addresses are **not** co-located (median 3,011.6 m) |
| C-5 | Archived arrival review states "**20 CSVs, 21 MB**" | `90_Archive/00_Root_Drafts_2026-10-06/PS2_PS3_DATASET_REVIEW.md` | The Drive holds **21 CSVs** (288,754 rows). Which file the earlier count omitted cannot be determined from the record; logged as an unresolved discrepancy rather than guessed |

## 4. Experiment assumptions that must not be reused

| Assumption | Status |
|---|---|
| "645 check-ins >500 m" as an integrity rationale | **Retracted** (C-2-analogue; see §2 item 2). Integrity rests on media duplication + timing |
| "free-data oracle ceiling 370 m" | Superseded: **306.2 m** over the current three arms |
| "385 m → 29 m" visit-learning claim | Superseded: met-someone check-ins median **29.3 m**; first met-visit anchor **24.0 m** overall, **21.1 m** on val+test, vs pin 380.3 m/383.7 m |
| "the 100 surveyed are one evaluation set" | Now split-aware: **66 train / 19 val / 15 test** |
| "visits can be replayed without stating definitions" | Replay must state the cut (2026-05-15), the warm definition, and the subset |
| "agents/splits/lenders are not PS3 data" | **Wrong** — all three are PS3-assigned and in DATASET A |

## 5. Reconciliation actions taken (and not taken)

**Taken:** v2 of the seven re-audit documents supersedes v1 (same filenames, revision history in each); a dated correction note will be appended to the workspace business document (history preserved, nothing rewritten silently); `data/derived/updated_shared_column_map.csv` now carries the authoritative 75-column classification; this reconciliation document records every stale claim with its location.

**Deliberately not taken:** editing or deleting `README_DATA_PS3.md` (inside the frozen folder); rewriting the archived PS2 README (archive is never cited); deleting v1 artefacts (v1 remains as history inside the workspace audit folder).

**Open item for the project owner:** approve the O-5 move-and-rewrite of `README_DATA_PS3.md` out of the frozen folder, after which the frozen hash set is re-baselined and the file's §2 becomes a pointer to this reconciliation.
