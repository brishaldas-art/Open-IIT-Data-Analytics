# SUTRA — ARCHITECTURE CHANGE SET (official-scope re-audit) · 2026-10-07

*One page, one purpose: state exactly what the official-scope re-audit changed in the architecture, what evidence
forced each change, what was deliberately **not** changed, and what remains excluded. Every claim is cited to the source
register — register group N `[S67]`–`[S73]` (external research) and `[S94]` (our own measurements on DATASET A).*

**Status: implemented and checked.** `build_manifest.py` → 113 catalogued files / 31.70 MB · `check_workspace.py` →
ALL PASSED (incl. the 12-table assertion) · `check_links.py` → ALL RESOLVE · `check_leakage.py` → ALL PASSED
(incl. "official dataset unmodified", hash match). Nothing was trained.

---

## 1. Why this change set exists

The re-audit produced four findings that the architecture could not ignore:

1. **The scope of record was one table short.** The officially assigned shared table `lenders` was missing from the
   frozen tree, so our own count strings ("11 tables / 177,190 rows") were stale `[S94]`.
2. **The official split separates accounts, not places.** **66 of the 100** surveyed truths sit on train-split accounts;
   **124 of the 344 (36.0%)** test addresses with a met-someone visit have a train-split met check-in within 30 m;
   39 of 3,007 place blocks (99 addresses) cross the split `[S94]`. Block cross-validation is the standard remedy
   wherever dependence structures exist [S67][S68].
3. **Several published numbers were weaker or wrong than stated** — the warm/cold replay was mislabelled
   (warm **56.0%**, n=1,383 vs cold **24.5%**, n=1,343 — not "vs 40.5%"), and the "645 check-ins >500 m" integrity
   claim is **not reproducible** (max **90.8 m** to the nearest own-trail point) `[S94]`.
4. **Three design devices needed grounding**: an evidence-keyed place-identity rule, a radius publication contract, and
   a way to keep this task's claims honest given that field visits are targeted but the official data contains
   **no propensity column** (the shipped `dial_attempts.selection_propensity` belongs to another problem statement and
   is out of scope here).

## 2. The changes (all additive; recorded in-place, never silently overwritten)

| ID | Change | Where | Evidence |
|---|---|---|---|
| **A0** | **Scope of record = 12 tables · 177,196 rows** — imported the assigned shared `lenders.csv` byte-identical to the official Drive pack; re-baselined the frozen-tree hash set; `check_workspace.py` now asserts 12 tables; stale count strings carry dated corrections | `PS3_WORKSPACE_MANIFEST.md`, `README.md`, `PS3_DATA_LINEAGE.md`, `PS3_DATA_AUDIT.md`, `PS3_CANONICAL_SCHEMA.md`, `PS3_BUSINESS_AND_OPERATIONAL_RETHINK.md`, `PS3_DATA_EDA_AND_PREPROCESSING.md`, `tools/check_workspace.py` | Drive hash record; `lenders` measured to carry **no** address signal (portfolio differences ≤1.4 pts) → context-only `[S94]` |
| **A1** | **Evaluation protocol v2** — every claim on three populations (all 100 surveyed · validation+test · leave-block-out); new place-block ledger `data/derived/ps3_place_blocks.csv` built by `tools/place_block_folds.py` (3,007 blocks, 5 spatially ordered folds); memory/warm features additionally validated leave-block-out; prequential loop evaluation; T0–T4 stage labels harmonised | `PS3_LEAKAGE_AND_VALIDATION.md` §Amendment A1 | **36.0%** cross-split proximity; **66/19/15** truths by split `[S94]`; [S67][S68][S70] |
| **U1** | **Radius contract** — publish `radius_m` + `nominal` + `measured_coverage` + `n_calibration` + `source_stratum`; strata below n=15 fall back to the parent stratum, labelled; the **pincode radius is withheld as a measured transfer failure**; `UNPLACEABLE` stays first-class | `PS3_UNCERTAINTY_ARCHITECTURE.md` §Amendment U1 | locality **79.2%** coverage at p80 (n=24 eval) vs pincode **0% (n=4)** `[S94]`; [S69][S73] |
| **M1** | **Place identity by evidence** — `CONFIRMED_MERGE` / **`POSSIBLE_MATCH` review queue** / `DISTINCT`; identity text key **keeps** the trailing token (render key strips it); **never merge by account**; contradictions stay visible | `PS3_ADDRESS_MEMORY_ARCHITECTURE.md` §Amendment M1 | **81 co-location clusters / 191 addresses**, all cross-account; one account's addresses median **3,011.6 m** apart (0% <100 m); agreement 77.7 m same-agent vs 75.8 m different-agent `[S94]`; [S72] |
| **F1** | **Integrity basis corrected** — the "645 check-ins >500 m" sentence is **retracted**; integrity rests on **media duplication** (162/610 on one collector) and timing plausibility, with per-collector windowed baselines; collector traits **rejected as features** (tenure −0.16; language match nil); the remark lane becomes a designed capture channel (208 landmark-bearing remarks, 0 naming a locality) | `PS3_FIELD_EVIDENCE_ARCHITECTURE.md` §Amendment F1 | `[S94]` measured, as above |
| **L1** | **Dynamic loop** — corrected replay (warm 56.0% vs cold 24.5%; val+test 56.7/25.1); **prequential** test-then-train protocol with rolling metrics beside the fixed historical replay; **propensity logging** required from the first live window (evaluation-only, never a feature); targeting claims report weighted **and** unweighted numbers | `PS3_DYNAMIC_LEARNING_ARCHITECTURE.md` §Amendment L1 | `[S94]`; [S70][S71] |
| **E1** | **Experiment grid** — seven row-level changes (three-population rule · radius n-floor · replay correction · exposure-matched triage audit · propensity logging · prequential baselines · remark experiment) | `PS3_EXPERIMENT_PLAN.md` §Amendment E1 | as above |
| **A2** | **Final data policy** — external data permanently rejected; experiment I cancelled (grid A–O, no I); S4 arms official-only; register S39–S47 marked rejected; the external-research document archived; workspace guard forbids any dataset outside `official_ps3/cleaned/derived` | final project decision, 2026-10-07 | `PS3_FINAL_DATA_AND_ARCHITECTURE_FREEZE.md` |
| — | **Master register + provenance** — master architecture §8 lists A0–E1; decisions **D25–D31** locked with evidence and reversibility; register **group N `[S67]`–`[S73]`** added (URLs + type); internal measurement row **`[S94]`** | `PS3_MASTER_ARCHITECTURE.md`, `PS3_DECISION_LOG.md`, `PS3_SOURCE_REGISTER.md` | register rule: no decision rests on a source without a recorded URL |

**External grounding (group N, one line each):** block CV over random CV where dependence exists [S67][S68] ·
conformal validity needs its calibration set, n included [S69] · prequential test-then-train for non-stationary streams
[S70] · IPS/SNIPS needs **logged** propensities [S71] · two-threshold linkage with a clerical-review band [S72] ·
geocoding error is biased, heavy-tailed and sometimes kilometre-scale [S73].

## 3. What was deliberately **not** changed

- **The official benchmark split is untouched.** The place-block ledger is an evaluation lens; the competition protocol
  remains the account split. Editing it would make our numbers incomparable and the data unfaithful.
- **The architecture itself** — resolver → evidence → memory → uncertainty → loop → API — is unchanged. Every amendment
  is additive; **D05, D07, D12, D19, D21 stand exactly as written** (abstention, append-only evidence, no forced
  merges, `UNPLACEABLE` as a first-class answer, plural acceptance metrics).
- **No dataset substitution, no augmentation, no external rows.** No data from other problem statements, no columns
  owned by them (`dial_attempts`, `payments`), no scraped maps. The 100 surveyed addresses remain the only ground truth; no labels
  were manufactured.
- **Nothing trained**, no model artefact, no `tools/train*.py` (machine-checked).
- **No new claims.** Every amendment *tightens* what may be claimed: three populations instead of one, a withheld
  radius, logged propensities, a retracted integrity figure. Total effect: **harder to claim, easier to defend.**

## 4. Exclusions, restated with the round that made them

| Excluded | Classification (re-audit verdict) | Why, in one line | Where recorded |
|---|---|---|---|
| `dial_attempts` (87,066 rows) | **G — should not be used** (owned by another problem statement) | dialer activity describes that task's workflow; using it would import a foreign selection model | `PS3_DATA_LINEAGE.md` §4 (classification carried from the official-scope re-audit) |
| `payments` (24,486 rows) | **G — should not be used** (owned by another problem statement) | this task has **no financial outcome variable**; its presence would tempt a fabricated ROI | `PS3_DATA_LINEAGE.md` §4 |
| four tables from other problem statements + two retired dataset READMEs | out of problem statement | only this problem statement's data and its assigned shared tables are used; staged in `90_Archive/`, never cited by active documents | `PS3_WORKSPACE_MANIFEST.md` §4 |
| External / scraped / OSM / commercial augmentation | **REJECTED permanently — final data policy (2026-10-07)** | no external, scraped, downloaded or third-party geographic source may enter the build; the reserved path stays empty and is machine-guarded | `PS3_FINAL_DATA_AND_ARCHITECTURE_FREEZE.md` §DATA, `tools/check_workspace.py` external-data guard |
| Own-experiment artefacts as data | forbidden input | an augmented set may exist separately with lineage, but may never enter DATASET A, training or any headline metric | `PS3_DATA_LINEAGE.md` §4 |

## 5. What this changes in the real workflow (the only justification that counts)

- An **allocator** now receives a radius with its evidence count — and no radius at all where we cannot stand behind one
  (pincode, `UNPLACEABLE`) — so the expensive irreversible act (issuing a visit notice) is spent on places we can
  actually reach.
- **Two collectors at one building** share one verified place across borrowers, through a review queue rather than a
  silent merge — and a borrower's two addresses are never averaged into one.
- The **field app becomes the measurement instrument**: propensities, timings, media integrity and the remark lane are
  logged as first-class evidence, which is what makes every future accuracy and targeting claim auditable.
- **Evaluation integrity is now visible to the operator**: any accuracy figure can be re-read as "on places the model
  has never seen", which is what the business will actually face on day one of a new town.

*Sources: register group N `[S67]`–`[S73]`; internal measurement row `[S94]`; decision log D25–D31; master architecture
§8. Prepared 2026-10-07; no training performed.*
