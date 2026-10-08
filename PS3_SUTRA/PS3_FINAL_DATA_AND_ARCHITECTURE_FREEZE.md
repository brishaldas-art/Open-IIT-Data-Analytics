# SUTRA — FINAL DATA & ARCHITECTURE FREEZE

**CreditNirvana · Problem Statement 3 — *Address Geocoder That Learns from Field Visits*** · frozen **2026-10-07** · status: **BINDING**

This document is the authoritative statement of what data may be used, what the architecture is, how it learns, how it is
evaluated, and what is forever excluded. Every active document, experiment, feature and metric answers to it. It supersedes
all earlier planning on external data `[S95]`.

> **One sentence:** *CreditNirvana's own field operations become a continuously improving address intelligence asset —
> built on the official dataset alone.*

---

## 1. DATA — the only permitted inputs

**Authoritative policy: official PS3-specific data from the supplied CreditNirvana pack, plus the official shared data
that the PS3 scope audit proved legitimately relevant. Nothing else.**

**PS3-specific (6 files):** `baseline_geocodes.csv` · `landmarks_poi.csv` · `localities.csv` ·
`surveyed_addresses.csv` · `towns.csv` · `visit_gps_points.csv`

**PS3-relevant shared (6 files):** `addresses.csv` · `accounts.csv` · `agents.csv` · `field_visits.csv` ·
`splits.csv` · `lenders.csv`

→ **DATASET A = 12 tables · 177,196 rows · 83 columns** `[S94]`, hash-frozen at `data/official_ps3/`, byte-identical to
the official Drive pack (the audit folder's Drive-verification register records every file id and SHA-256). The official Drive remains
authoritative: <https://drive.google.com/drive/folders/11J0vOHyjHH0y4Vjw8_5HZxsBWyVgH48t>

**Explicitly excluded:** the two shared tables that belong to other problem statements — `dial_attempts` and `payments`
(both live in the supplied pack's shared bucket; neither is used here) — plus everything under the other problem
statements (their tables, their derived fields, their models) and all external data (below).

**Shared-table role contract — binding in every artefact** (data architecture, preprocessing, leakage map, feature schema,
experiments, model cards, final report):

| Table | Role | Never |
|---|---|---|
| `addresses` | **REQUIRED** — core model input | — |
| `field_visits` | **REQUIRED** — core learning/evidence input | — |
| `accounts` | **EXPOSURE / BUSINESS CONTEXT ONLY** | a coordinate feature |
| `agents` | **INTEGRITY / MONITORING ONLY** | a location prior |
| `splits` | **EVALUATION ONLY** | training labels or features |
| `lenders` | **CONTEXT ONLY** | a geocoder feature |

**No external data — permanent.** Not scraped, not Overture, OSM/Geofabrik, Open Buildings, Microsoft Building Footprints,
OpenAddresses, Nominatim, India Post or data.gov.in, no third-party address database, no downloaded POIs, no external
geocoder as a model input, no geographic augmentation of any kind. Enforced mechanically: `tools/check_workspace.py`
fails the build if any dataset file appears anywhere outside `data/official_ps3/`, `data/cleaned/`, `data/derived/`, and
fails if `data/external_research/` is non-empty (it is reserved and permanently empty).

*Recorded decision:* **"External-data augmentation was considered during research but rejected by final project decision.
The final PS3 system uses only the official CreditNirvana dataset and legitimately PS3-relevant shared data."** The
rejected evaluation is archived at `90_Archive/ps3_rejected_2026-10-07/PS3_EXTERNAL_DATA_RESEARCH.md`; register entries
S39–S47 are marked REJECTED.

---

## 2. ARCHITECTURE — S0–S13, frozen

> **Status update (2026-10-07, due-diligence pass).** The **DATA** policy below remains binding and unchanged. The
> architecture content is the working blueprint until the due-diligence checklist completes, at which point
> `PS3_ARCHITECTURE_LOCK_CANDIDATE_2026-10-07.md` becomes the single locked statement (it carries the corrected
> point-fallback semantics, graded negative evidence, scored confirmation independence, radius vocabulary, ownership
> rules and the sync contract).

| # | Block | Class |
|---|---|---|
| S0 | Ingest (accept "no geocode yet"; 237 out-of-town records exercise this) | **CORE** |
| S1 | Normalisation / script / language | **CORE** |
| S2 | Parsing (typed: house, relation, locality token; 24.9% of records have no comma) | **CORE** |
| S3 | Entity / place resolution | **CORE** |
| S4 | Candidate generation — **official arms only** (below) | **CORE** |
| S5 | Ranking (shallow LambdaMART small-data variant; logistic-regression challenger; rule baseline ships if no model wins) | **CORE** |
| S6 | Point fallback (deterministic prior / ridge; small GBM challenger) | **CORE** |
| S7 | Belief fusion (candidate score + memory + visits, reason-coded) | **CORE** |
| S8 | Uncertainty (empirical / conformal calibration; n-guard; parent-stratum fallback; measured coverage) | **CORE** |
| S9 | Visit evidence (dwell, trail agreement, media, timing, outcome semantics) | **CORE** |
| S10 | Integrity weighting (reason-coded: duplicate media, dwell, GPS/trail consistency, accuracy, rolling per-agent baselines — **never GPS-only**) | **CORE** |
| S11 | Belief update (fast, append-only, instant) | **CORE** |
| S12 | Address / place memory (place-keyed, append-only, provenance-aware, decaying, contradiction-aware, reversible merge/split; **no model-derived evidence is ever ground truth**) | **CORE** |
| S13 | Slow learning loop (gated retraining / recalibration; no per-visit model retraining) | **PRODUCTION-DESIGNED / BUILD-IF-TIME** |

*(In `PS3_MASTER_ARCHITECTURE.md` §2 the same sequence appears with S1–S3 as normalise/parse · resolve-entities ·
gazetteer-index; the mapping is one-to-one and no block was added or removed.)*

**S4 — the official candidate arms, and nothing else:**

```
official frozen baseline geocode arm
+ official towns / localities          (towns 3 · localities 36)
+ official landmark / POI anchors      (landmarks_poi 240)
+ official address-book anchors        (addresses: known house markers, locality tokens, pincode tails)
+ official historical field evidence   (field_visits + visit_gps_points, as-of)
+ official address memory              (place-keyed, built from the above)
```

**No external candidate arm. No outside geographic source may enter S4.** Where the official arms are exhausted
(the measured oracle is 306.2 m median), the sanctioned investments are **official-data parsing, memory quality,
field-evidence capture and calibration** — not acquisition.

**Forbidden dependencies, stated plainly:** no LLM dependency (parsing is rules; LLM tier stays research-only), no
embedding dependency, no external map dependency, no external geocoder dependency for correctness. The vendor geocoder
remains a *candidate input under licence clocks*, never our record of truth.

---

## 3. LEARNING — historical, time-aware, simulated

* **Dynamic learning uses historical field visits replayed with time-aware cut-points** (fit on everything before `t`,
  evaluate on `[t, t+7d)`). Every replay result is labelled **SIMULATION**.
* **No physical fieldwork by the team.** No new visits are commissioned; the existing 5,578 visits are the raw material.
* **No model-derived truth.** A prediction, a fused belief, a ranker preference or an imputed coordinate can never become
  evidence or a label. Only observed field outcomes and the 100 surveyed truths are truth.
* **No future leakage.** As-of discipline (T0–T4) applies to every feature, every join and every belief read; treatment
  effects are measured on the exploration slice with the logged-propensity protocol (D28, [S71]).
* **Fast loop:** belief update per observation. **Slow loop:** gated retraining/recalibration on accumulated trustworthy
  evidence only (D13/D27).

## 4. EVALUATION — what counts as evidence of quality

* **The 100 surveyed addresses remain the primary ground truth.** No labels are manufactured; negative outcomes never
  become location labels; the surveyed set is never used as training data.
* **The official benchmark stays frozen** (hash-verified; account split untouched; the place-block fold ledger is an
  evaluation lens, never an edit).
* **All warm/cold results are as-of and time-aware**, reported as: overall post-cut **40.5%**; warm **56.0%** (n=1,383);
  cold **24.5%** (n=1,343); validation+test warm **56.7%** / cold **25.1%** `[S94]`. 40.5% is the *overall* rate — it is
  never called the cold rate.
* **Three populations per claim:** all 100 surveyed · validation+test · leave-block-out (Amendment A1, [S67][S68]).
* **Radii publish with `n_calibration`**; strata below n=15 fall back to the parent stratum, labelled; the pincode radius
  is withheld (measured transfer failure: 79.2% locality at p80 vs 0% pincode, n=4) [S69][S73].
* Plural acceptance metrics (D21): accuracy **and** coverage **and** refusal quality **and** cost shape — no single
  number is "the result".

## 5. EXPERIMENTS — the frozen grid

**A** official frozen baseline geocode arm · **B** preprocessing ablation · **C** official candidate retrieval / oracle · **C2** place-neighbour index ablation (added 2026-10-07, gated) · **D** retrieval +
ranking · **E** uncertainty / radius calibration · **F** vendor + field learning · **G** full SUTRA · **H** official
frozen benchmark · **I — CANCELLED** (external data rejected by final project policy; kept as a marked gap, never
renumbered away) · **J** dynamic replay / slow-loop simulation (**SIMULATION**) · **K** integrity ablation ·
**L** memory ablation · **M** negative-evidence ablation (now testing the graded rule of F2.1) · **N** static vs dynamic · **O** cold vs warm · **P** visit-triage / decision-quality replay (**SIMULATION**, added 2026-10-07).

## 6. Corrections preserved from the re-audit (binding wording)

| # | Item | Frozen statement |
|---|---|---|
| 1 | Warm/cold | overall post-cut **≈ 40.5%** · warm **≈ 56.0%** · cold **≈ 24.5%** · val+test warm **≈ 56.7%** · val+test cold **≈ 25.1%**. **40.5% is not the cold rate.** |
| 2 | FA009 | keep the **duplicate-media anomaly** (162 repeat photo hashes of 610 visits); the old "83% in the 10–13 slot / missed-slot anomaly" is **retracted** — all agents show similar daytime concentration (schedule artefact) |
| 3 | Memory consistency | same-agent ≈ **77.7 m** · different-agent ≈ **75.8 m** → interpreted as **essentially agent-independent under this definition** |
| 4 | Multi-address | **same account does NOT imply same place**; visited multi-address pairs are far apart (median **3,011.6 m**; 0% within 100 m) → **never merge solely because `account_id` matches** |
| 5 | Radius | locality transfer is useful · **pincode transfer fails at tiny n** · rooftop has insufficient n → **n-guards and parent-stratum fallback stay** |

## 7. BUSINESS STORY — the frozen framing

**Sell this:** *"CreditNirvana's own field operations become a continuously improving address intelligence asset."*
**Never sell** "we combine many geographic data sources" — there is exactly one data source: CreditNirvana's own.

```
address arrives
  → resolve from official data            (S0–S4, official arms only)
  → return candidate / uncertainty / directions   (S5–S8)
  → field visit occurs                    (historical visits; future visits as they happen)
  → capture structured evidence           (S9: outcome, dwell, media, trail, remark lane)
  → assess evidence integrity             (S10: weight, don't accuse)
  → update belief                         (S11)
  → update place memory                   (S12)
  → reuse knowledge on future resolutions (S4/S7, warm lane)
  → gated retraining when enough trustworthy evidence accumulates   (S13)
```

**Business value:** less repeat investigation · fewer wasted visits caused by poor prior resolution · better
prioritisation of uncertain addresses · reusable field knowledge · auditable corrections · calibrated uncertainty
instead of false precision · improvement from the company's own operational evidence.

**Claim discipline:** no measured reduction in field cost is claimed unless a completed experiment demonstrates it; no
external price is ever multiplied into a claim; the goal is fewer *unnecessary* visits and higher value per *necessary*
visit — visits themselves are never eliminated.

## 8. Verification (re-run any time)

```bash
cd PS3_SUTRA && bash tools/reproduce.sh full
python3 tools/check_workspace.py   # incl. the 12-table assertion AND the external-data guard
python3 tools/check_leakage.py     # incl. the Domain-A hash proof (official data unmodified)
```

Normative implementation schemas: `PS3_IMPLEMENTATION_CONTRACTS_2026-10-07.md`.

Frozen-state evidence on the day of this freeze: workflow **ALL CHECKS PASSED** · links **ALL RESOLVE** · leakage
**ALL PASSED** · official-hash proof **PASS** · no training artefacts · no training script · no external dataset
anywhere in the tree. Register: group N `[S67]`–`[S73]`, project-policy row `[S95]`, measurements `[S94]`; decisions
D25–D34.

*Freeze prepared 2026-10-07. Nothing is trained until the operator lifts the hold; the next step after this freeze is the
official-only experiment sequence A → E.*
