# SUTRA — ARCHITECTURE LOCK CANDIDATE (2026-10-07)

**Status: ARCHITECTURE LOCKED (2026-10-07)** — all 18 lock-gate items completed (checklist below); verified with `build_manifest.py`, `check_workspace.py`, `check_links.py`, `check_leakage.py`, `reproduce.sh` — all green.
**Implementation is built against `PS3_IMPLEMENTATION_CONTRACTS_2026-10-07.md`** (normative schemas, interfaces, API,
invariants, failure states, acceptance tests). Where this document and the contracts disagree on a schema or interface,
the contracts win. This document is the single
statement of what will be built, on what data, under what rules. It supersedes earlier architecture text wherever they
differ; the data policy is unchanged from `PS3_FINAL_DATA_AND_ARCHITECTURE_FREEZE.md` `[S95]`.
**After this document: architecture research stops. Implementation begins.**

Runtime is presented in **four layers** for clarity; internal stage codes S0–S13 are kept for traceability. Ownership is
unambiguous (M3): the **store** remembers, the **belief engine** calculates, **projections** serve.

---

## A. Architecture diagram

```
┌──────────────────────────── LAYER 1 — RESOLUTION ────────────────────────────┐
│  S0 ingest ▸ S1 normalise/script ▸ S2 parse (typed) ▸ S3 resolve entities    │
│  S4 candidate generation — OFFICIAL ARMS ONLY:                               │
│     official frozen baseline arm · towns/localities · landmark/POI anchors · │
│     address-book anchors · historical field evidence · address memory        │
│     [C2 place-neighbour index — SHADOW, admitted only by experiment]         │
│  S5 rank — FROZEN INTERFACE: candidates in → inspectable score + reason      │
│     codes + deterministic order out   (rule ▸ logistic ▸ shallow LTR)        │
│  S6 point fallback — NEVER constructs an address coordinate (D35)            │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   ▼
┌──────────────────────────── LAYER 2 — DECISION ──────────────────────────────┐
│  S7 belief fusion (candidates + memory + visits, reason-coded)               │
│  S8 uncertainty (tier + EMPIRICAL radius + measured coverage + n-guard)      │
│  M7 address_purpose (HOME_LIKE | WORK_LIKE | OTHER | UNKNOWN + abstention)   │
│  request_purpose (caller-declared; access-control input)                     │
│  DIRECTION CUES (official POIs + parsed relation spans; advisory)            │
│  ELIGIBILITY GATE  →  SERVE | VERIFY_FIRST | REFUSE                          │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   ▼
┌────────────────────────── LAYER 3 — FIELD LEARNING ──────────────────────────┐
│  S9 evidence capture (outcome · dwell · trail · media · remark lane, offline)│
│  S10 integrity weights (media · timing · GPS/trail · per-agent baselines)    │
│  observations (append-only) ▸ S11 belief update ▸ S12 place memory           │
│  contradiction / reverification (CONTESTED · MOVED_SUSPECTED)                │
│  [place-neighbour index — maintained here, queried by S4]                    │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   ▼
┌────────────────── LAYER 4 — GOVERNED LEARNING / PLATFORM ────────────────────┐
│  as-of replay · calibration · drift monitoring · challenger/promotion gate   │
│  offline pack generation · sync (contract, production-only) · audit/versioning│
│  S13 slow loop — PRODUCTION-DESIGNED (champion/challenger, cooldown, rollback)│
└──────────────────────────────────────────────────────────────────────────────┘
```

**S0–S13 ⇒ layers:** L1 = S0–S6 · L2 = S7–S8 + M7 + directions + gate · L3 = S9–S12 + index maintenance ·
L4 = S13 + platform services. No stage exists outside a layer; no layer has a stage that contradicts the other map.

## B. Component table

| Component | What it does | Data (official only) | Class |
|---|---|---|---|
| Ingest/normalise/parse | typed fields from free text, script-safe | `addresses` text (3,117) | GREEN · MVP |
| Entity resolution | locality/pincode/town tokens → known entities | `towns` 3 · `localities` 36 · keys | GREEN · MVP |
| Candidate generation | official arms, per-candidate provenance | `baseline_geocodes` 2,880 · gazetteer · landmarks 240 · address book · `field_visits` 5,578 · memory | GREEN · MVP |
| Ranker | freeze the interface, not the model | features + 100 truths (eval only) | GREEN (rule) · YELLOW (models) |
| Point fallback | abstain or area-context; never invent | — | GREEN · MVP |
| Belief fusion | deterministic, replayable | observations + memory | GREEN · MVP |
| Uncertainty | empirical radius + n + coverage, parent fallback | calibration table | GREEN · MVP |
| address_purpose + eligibility (M7) | the second decision | visit features | GREEN · MVP (rules) |
| Direction cues | landmark-relative text, no road nav | `landmarks_poi` + parsed spans | GREEN · MVP |
| Evidence scoring | visit → structured evidence | `field_visits` + `visit_gps_points` | GREEN · MVP |
| Integrity | reason-coded weights, never GPS-only | media hashes · dwell · accuracy · agent baselines | GREEN · MVP |
| Memory | place-keyed, append-only, decaying, contradiction-aware | confirmed places (900) | GREEN · MVP (core) |
| Neighbour index | candidate mass from confirmed places | same, as-of filtered | YELLOW · C2-gated |
| Offline app | pack + capture + outbox (demo slice) | packs + observations | YELLOW |
| Sync | contract locked; production-only build | observations | RED → production |
| Replay/triage | as-of historical evaluation (SIMULATION) | historical visits | GREEN (J) · YELLOW (P) |
| Slow loop | gated retraining/recalibration | windows | RED → production-designed |

## C. Data flow (text in → decision out)

```
raw address ─► parse ─► resolve ─► candidates (official arms) ─► rank ─► fuse with as-of memory
      └─ tier + radius(basis) + reasons + request_purpose + address_purpose
         + directions + eligibility ─► response / pack
as-of filters at every read (T0–T4); no T2+ value reaches a T1 output; no external data anywhere.
```

## D. Request flow (`/resolve`)

```
API → auth → purpose-of-request → parse/resolve/candidates (≤25) → rank → fuse → uncertainty → purpose → cues
    → eligibility gate → response {candidate, tier, radius_m, radius_basis, nominal|null, measured_coverage,
      n_calibration, reasons[], request_purpose, address_purpose{class,...}, directions[...], eligibility{action, reason}}
Latency budget: p95 ≤ 250 ms local (official arms only; no vendor calls). Refusals are 200s with an action, not errors.
```

## E. Field-visit flow

```
assignment (or historical visit) → offline pack (candidates, radii, cues, VERIFY_FIRST tasks)
→ capture: outcome class · dwell · GPS trail · media · remark (structured lane)
→ integrity weighting (media duplication · timing · trail agreement · per-agent baseline)
→ append-only observation [UUID · local_seq · captured_at_device · server_received_at]
→ belief update (instant, deterministic) → place memory (promote per F2.2 independence; contradict per F2.1)
```

## F. Offline sync flow (contract; production build)

```
DEVICE: local store (projection) + durable OUTBOX   |   SERVER: authoritative store + cursor feed
push: batches ordered by local_seq, idempotent by observation_id (client UUID)
pull: changes since server cursor (tombstones included)
MVP scope (GREEN): pack download · network OFF · local capture · durable outbox · replay-on-reconnect — the full engine is RED (production-only)
conflict: base version unseen ⇒ HOLD ≤7 days, apply in order when base arrives, else mark CONFLICT for review
duplicate visit from a second device ⇒ linked duplicate claim, never a second confirmation (F2.2)
recompute: server re-derives beliefs deterministically; device adopts on next pull. Device clock never orders evidence.
```

## G. Belief / memory flow (ownership M3)

```
observation (append-only) ──► evidence_score (versioned policy) ──► belief recomputation (pure function)
place clusters (identity per M1) ◄── observations                 └──► projections: address_current, packs, per-place views
Contradictions live in the STORE's status field: CONTESTED · MOVED_SUSPECTED · STALE. Projections are never features.
```

## H. Slow-learning flow (production-designed; simulated in J)

```
window of new visits ─► prequential scores (as-of, test-then-train) ─► drift monitor ─► challenger train (gated)
─► evaluation on frozen protocol + three populations ─► promotion gate (intervals, coverage, refusal quality, cost)
─► model card + registry alias flip ─► cooldown ─► (rollback path). No per-visit retraining, ever.
```

## I. Model inventory

| # | Model | Form | Status |
|---|---|---|---|
| M1 | retrieval/linkage | rules + Fellegi–Sunter-style weights | ships |
| M2 | ranker | **interface frozen**; weighted rule → logistic → shallow LambdaMART | experiment D picks; rule ships by default |
| M3 | point fallback | ridge/small GBM **within candidate support only**; else abstain | ships (rarely used) |
| M4 | evidence | likelihood-ratio rules first; learned model only with adjudicated labels | rules ship |
| M5 | integrity | reason-coded weights | ships |
| M6 | radius | empirical quantiles + n-guard (conformal = validation) | ships |
| M7 | address_purpose | rules P1–P5 + abstention | ships (rules) |

## J. Failure / degradation ladder

`full` (candidates+memory) → `no memory` (cold lane) → `no locality match` (AREA_CONTEXT, action = VERIFY_FIRST) →
`no candidate` (**no coordinate**, UNPLACEABLE, action = VERIFY_FIRST) → `store down` (read last snapshot; queue observations) →
`pack stale` (radius widening + reason) → `calibration missing` (parent stratum, labelled). At no rung does the system
invent a coordinate or hide its doubt.

## K. API contract (summary)

`/resolve` (above) · `/evidence` (append observation; idempotent; offline-replay-safe) · `/place/{id}` (state,
support, contradictions) · `/tasks/verify-first` (generated from low tiers, `n_neg ≥ 2`, UNPLACEABLE) · `/packs/{district}`
(versioned pack; no polygons). Every response carries versions (`rule_version`, `radius_map_version`, `evidence_policy_version`).

## L. Storage contract (summary)

`observation` (append-only) · `evidence_score` (versioned) · `belief_version` (snapshots) · `place` + `place_link`
(identity, review queue) · `candidate_log` · `gate_log` (eligibility decisions + rule version) · `pack` (versioned
exports). No model artefact is stored as evidence; no projection is a feature source (M3).

## M. Security / privacy

Purpose-bound access (a coordinate is served for locating a visited address, nothing else) · no third-party disclosure
paths (R11.3 gate) · device stores encrypted, remote wipe, media retention rules · observations carry actor + device
attestation · audit trails immutable · contact-time constraints per the visit framework `[S55]`.

## N. Feasibility matrix

Full matrix in `PS3_ARCHITECTURE_DUE_DILIGENCE_2026-10-07.md` §4 (18 rows, one class each, mechanically recounted):
**12 GREEN · 3 YELLOW · 3 RED**. RED = the three production-only rows — full offline app (16), distributed sync (17),
slow-loop execution (18) — none on the correctness path. The **offline field MVP** (pack → network OFF → local capture
→ durable outbox → replay on reconnect) is **GREEN** and ships in the 48-hour build.

## O. Competitor / system comparison (summary)

Full table in the due-diligence §2 `[S74]`–`[S83]`. The one-line: every mechanism we use exists in production
somewhere at greater scale with data we cannot have; our advantage is the *combination* (section P) executed honestly
on official data, not any single technique.

## P. Novelty positioning

**Cannot claim:** geocoding, parsing, learning from visits, historical-delivery evidence [S77][S80], uncertainty
calibration, offline capture. **COMBINATION:** place-keyed auditable memory for collections-verification addresses;
address_purpose → eligibility gate under the visit framework; as-of evidence discipline end-to-end. **NOVEL (as specified):**
graded negative-evidence semantics with `MOVED_SUSPECTED`/reverification and scored confirmation independence.
**STANDARD ENGINEERING (honestly labelled):** landmark cues, empirical radii, the ranker. **RESEARCH-ONLY:** neighbour
index (until C2), any neural purpose/evidence model, bandit allocation.

## Q. Experiment-to-decision map

| Experiment | Decision it locks |
|---|---|
| A | the floor (published baseline) |
| B | which preprocessing survives |
| C / C2 | whether retrieval — and the neighbour index — earn their place |
| D | which ranker ships (rule by default) |
| E | radius basis per stratum; pincode stays withheld |
| F | whether field learning adds value over the vendor arm |
| G / H | the full-pipeline and frozen-benchmark numbers |
| J / N / O | loop stability, static-vs-dynamic, warm-vs-cold claims |
| K / L / M | integrity, memory, and the graded negative-evidence rule |
| P | the triage/eligibility thresholds and the decision-quality story |

## R. Explicit cut list (this pass)

External arm · vendor adapter (from build) · PIN polygons · full offline app · distributed sync · slow-loop execution ·
purpose/evidence neural models · graph/GNN anything · landmark-snapping point model · neighbour index default-on ·
any claim of savings.

## S. Remaining risks (accepted, visible)

100-label constraint on all learned components · purpose/triage thresholds unvalidated until P runs · index may be cut
by its control · sync is contract-only · 36.0% place proximity makes leave-block-out reporting mandatory · the graded
negative rule needs real review-queue use to earn operator trust.

## T. Build order (48 h)

| Block | Hours | Deliverable |
|---|---|---|
| 1 | 0–6 | parse/resolve/candidates on official data; rule ranker; receipts |
| 2 | 6–12 | belief + uncertainty (empirical, n-guard) + reasons; `/resolve` |
| 3 | 12–18 | address_purpose + eligibility gate + direction cues; `/tasks/verify-first` |
| 4 | 18–26 | evidence ingestion + integrity weights + memory (store, promote, contradict) |
| 5 | 26–34 | replay J + triage P on historical visits (SIMULATION); frozen-benchmark numbers |
| 6 | 34–44 | demo surface: failing gate, scripted visit flips decision, low-integrity widens-not-moves, **offline field MVP** (pack → network OFF → capture → durable outbox → replay on reconnect) |
| 7 | 44–48 | docs + checks green (`build_manifest`, `check_workspace`, `check_leakage`, `reproduce.sh`); no training on stage |

---

## Lock gate — all items completed

- [x] unrelated-project artefacts removed from the active workspaces (4 files archived with provenance; keyword guard added)
- [x] official-only data policy consistent across every active document (re-swept this pass)
- [x] old vendor/OSM/PIN requirements reconciled (`PS3_ARCHITECTURE_REQUIREMENTS_RECONCILED.md`)
- [x] purpose classification explicitly placed (first-class module; D41)
- [x] landmark direction output explicitly designed (cue generator; D41)
- [x] negative-evidence rule corrected (F2.1; D36)
- [x] confirmation independence strengthened (F2.2; D37)
- [x] radius semantics corrected (U2; D38)
- [x] offline sync contract specified (D40)
- [x] belief/memory ownership clarified (M3; D39)
- [x] operational neighbour index evaluated (probe + placebo; C2-gated; D43)
- [x] point-fallback semantics corrected (D35)
- [x] feasibility matrix completed (due-diligence §4)
- [x] existing-systems comparison completed (due-diligence §2; register group O)
- [x] red-team pass completed (24 attacks; due-diligence §6)
- [x] business decision-quality replay designed (experiment P)
- [x] 48-hour implementation plan completed (section T)
- [x] acceptance tests defined (below)

**Acceptance tests (implementation gate):** no coordinate without a candidate (S6/D35) · a single negative observation
cannot change any coordinate (F2.1) · every published radius carries basis + n; pincode withheld · promotion requires
the F2.2 independence tuple · deterministic re-derivation of any belief from the store (M3) · purpose gate refuses
work-like notices and records why · direction cues return `null` rather than guessing · no dataset outside
`official_ps3/cleaned/derived` (guard) · no vendor call in benchmark or demo path · no model-derived value ever enters
the store as evidence.

**ARCHITECTURE LOCKED — 2026-10-07.** Architecture research stops here.

---

*Sources: register group O `[S74]`–`[S83]`, `[S90][S94][S96]`, `[S95]`; decisions D32–D44. Data policy:
`PS3_FINAL_DATA_AND_ARCHITECTURE_FREEZE.md`. Full due-diligence record:
`PS3_ARCHITECTURE_DUE_DILIGENCE_2026-10-07.md`.*
