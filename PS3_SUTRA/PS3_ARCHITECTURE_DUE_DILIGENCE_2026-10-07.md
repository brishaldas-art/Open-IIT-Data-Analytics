# SUTRA — ARCHITECTURE DUE-DILIGENCE (2026-10-07)

**Purpose.** One final pass before lock: does the current SUTRA architecture actually solve PS3, build inside 48 hours
on the supplied data, survive red-teaming, and tell the truth about what is novel? This document records the pass:
what was read, what was found wrong, what was resolved, what was cut, and what remains uncertain. It is deliberately
critical. **External systems were researched for architecture comparison only; no external dataset or model enters the
build** `[S95]`.

**Pass status.** All 18 lock-gate items completed → `ARCHITECTURE LOCKED` is recorded in
`PS3_ARCHITECTURE_LOCK_CANDIDATE_2026-10-07.md` §Lock gate. This document is the audit trail of *how* it qualified.

---

## 1. What was read, and what "FINAL" actually meant

All 23 architecture/planning documents were re-read together (master, system design, API, data/model/memory/evidence/
uncertainty/dynamic/MLOps/cost architectures, requirements, red team, experiment plan, business rethink, real-systems
research, novelty, freeze, plus the options/selection/advanced/change-set quartet). Findings about the documents
themselves:

| Document | Status found | Action taken |
|---|---|---|
| `PS3_ARCHITECTURE_REQUIREMENTS.md` | **Out of date**: R4.1/R4.3/R4.5 and PIN-polygon requirements assume a live vendor and OSM — impossible under the final data policy | Reconciled row-by-row in `PS3_ARCHITECTURE_REQUIREMENTS_RECONCILED.md` (this pass's section 3) |
| `PS3_FINAL_REPORT.md`, `PS3_DATA_AUDIT.md` | "FINAL" labels predate the data policy; external-data sentences survived | Corrected in the freeze pass; verified again here (zero planning-language remains) |
| `PS3_MASTER_ARCHITECTURE.md` | S6 "coarse prior" fallback contradicted the no-fabricated-coordinate rule | §2/§5 amended; §8 row A3 added |
| `PS3_FIELD_EVIDENCE_ARCHITECTURE.md` | Negative-evidence rule absolute; promotion independence unstated | Amendments F2.1 / F2.2 |
| `PS3_UNCERTAINTY_ARCHITECTURE.md` | "nominal 90%", "conformal", "p80" blended | Amendment U2 (vocabulary + publication rule) |
| `PS3_ADDRESS_MEMORY_ARCHITECTURE.md` | Belief/memory ownership blurred | Amendment M3 |
| `PS3_MLOPS_ARCHITECTURE.md` | Offline sync described behaviourally ("highest weight wins") | Sync contract specified |
| `PS3_MODEL_ARCHITECTURE.md` | Fallback could fabricate; ranker implicitly fixed | Amendment M3b |
| `PS3_EXPERIMENT_PLAN.md` | No triage replay; no neighbour-index control | Amendment E3 (C2, P) |
| Others (options, selection, advanced, change-set) | Historical; several superseded claims | Left as history; owned by the change-set and this pass |

**Method note.** Every number quoted in this document is either computed on DATASET A (`[S90][S94][S96]`), a published
external claim with its source tag, or absent. No number was invented to make the lock look better.

## 2. Existing-systems comparison (fresh research; comparison only)

Research sources: register group O `[S74]`–`[S83]`. All ten systems were read against fifteen questions (problem,
inputs, parsing, candidate generation, ranking, geographic representation, uncertainty, learning from operations,
memory, integrity, offline, sync, latency, topology, open source) — compressed here to what changes decisions.

| System | What it is | What SUTRA borrows | What SUTRA must NOT copy | Weakness it exposes in us |
|---|---|---|---|---|
| **Pelias** [S74] | Modular ES geocoder; query "layouts"; wrappers score returned features | Explicit retrieval arms with per-candidate metadata; inspectable query construction | Its open-data corpus (prohibited) and its confidence-via-wrapper scoring | Our S4 has **fewer independent arms** than theirs; the official ceiling (306 m) is the honest consequence |
| **Photon** [S75] | komoot's Java+ES geocoder; search-as-you-type; thousands of req/min in production | The latency envelope (a small local service can meet 250 ms p95) | Nothing operational; it has no uncertainty or learning layer | Reminds us our API budget assumes an index we must actually build |
| **libpostal** [S76] | CRF address parser, ~20 tags, trained on ~1B addresses | Confidence that rules-first parsing is a legitimate start | The model and its training data (external) | Our parser must be measurably good on **our** strings (23.6 s full EDA proves we can afford the test) |
| **Delhivery Maps / GeoNaksha** [S77] | Commercial suite; **Address Verification = visited within a window**, from 4B+ deliveries; returns error radius | The mechanism's validation: operational visit history **is** a product | The proprietary data/model; LLM-centric pipeline | We have 5,578 visits, not 4B — our claims must stay at our scale |
| **Shiprocket** [S78] | Open TinyBERT/IndicBERT address NER (23 labels), 66M params, ~19 ms | Proof that cheap address understanding is possible | The weights and augmented training data (external) | If our rules lose badly to a 66M model, that is a finding — but we cannot import it |
| **GeoIndia V1** [S79] | Seq2Seq H3-cell prediction, per-state models, claims >50% mean-distance reduction vs commercial | Grid/tier vocabulary thinking | 29 state models on proprietary corpora | Their advantage is data volume; ours must be evidence, not scale |
| **GeoIndia V2** [S80] | Graphormer + PTLM fused on graphs built from delivery traces | **The idea** that operational traces create geographic structure (→ our neighbour index, experiment-gated) | Graphormer/GNN compute; proprietary graphs; generative decoding | The placebo result (section 4) shows structure without scale is thin — our index is a lookup, not a brain |
| **ODK Collect/Central** [S81] | Offline-first capture; submission queue; **holds out-of-order updates up to 5 days**; conflict labels | Hold-then-mark-conflict; ordering by local sequence; server cursors | Nothing — it is the reference implementation | Our earlier sync phrasing ("highest weight wins") was weaker than a 15-year-old open-source tool |
| **Offline-first practice** [S82] | Outbox + idempotency keys + version checks; LWW unsafe for audited data | The whole sync contract | LWW for evidence | Sync is named the most failure-prone component; we now specify it rather than describe it |
| **FieldSync / field-service apps** [S82] | Offline PWAs with local DB + queue + audit trail | The audit-trail-as-product pattern our integrity layer feeds | Their cloud topology assumptions | Our app must work with evidence classes, not just photos |

**Net finding.** Every mechanism SUTRA proposes exists somewhere in production **at a different scale and with data
SUTRA cannot have**. That is exactly why the differentiator cannot be "we combine sources" (section 8) and why each
component earns its place by experiment.

## 3. Contradictions found and resolved (A–J of the brief)

| # | Contradiction | Where it lived | Resolution | Recorded in |
|---|---|---|---|---|
| A | Official-only policy vs live-vendor/OSM requirements | requirements doc vs freeze | Vendor calls = none; `baseline_geocodes.csv` is the frozen arm; adapter = production-only concept; OSM rejected | Reconciliation doc; D44 |
| B | Point fallback could return a coarse coordinate as an address answer | master S6, model M3 | **NO CANDIDATE → NO LOCATION COORDINATE → AREA CONTEXT ONLY (`AREA_CONTEXT`, labelled) → `UNPLACEABLE` / VERIFY-FIRST** | master §2/§5, M3b; D35 |
| C | Negative evidence absolute ("can never move a coordinate") | ~18 documents | Graded rule: one negative never relocates; accumulated independent negatives demote/widen/mark/trigger re-verification; only positive evidence or adjudication relocates | F2.1; D36 |
| D | Confirmation independence unstated ("two visits") | memory/promotion rules | Scored independence: visit · collector · period · media · source · space; ≥2 collectors-or-periods **plus** media independence | F2.2; D37 |
| E | Nominal 90% vs measured p80 vs conformal wording | uncertainty doc, requirements R8.2 | Empirical quantiles are the shipped basis (`radius_basis`), nominal only when measured, conformal = experiment E only; "90%" never headlined | U2; D38 |
| F | Belief vs memory ownership | memory doc, MLOps | Belief = pure calculation; store = authoritative append-only persistence; projections = query optimisation | M3; D39 |
| G | Offline sync semantics vague | MLOps, API | Full contract: local store + append-only event + outbox + idempotency + local_seq + cursor + replay-safe push + pull-since-cursor + deterministic recompute; hold-then-conflict | Sync contract; D40 |
| H | Purpose classification present but not placed | requirements §11 vs architecture | First-class decision module: belief+uncertainty → purpose → eligibility; rule-based + abstention; no model training | Purpose/direction doc; D41 |
| I | Landmark directions promised, undefined | requirements R15.1, business doc | Deterministic cue generator from official POIs + parsed relation spans; advisory only; no road navigation | Purpose/direction doc; D41 |
| J | PIN polygon requirement vs no polygons in data | requirements R5.2/R15.1 | Centroid-based candidate kept; polygons never invented; boundary routing = production extension | Reconciliation doc |

Two further inconsistencies found by this pass were also fixed: the API's "invariant" test line still asserted the
absolute negative-evidence rule (now F2.1), and the experiment grid's M row tested a strawman (now tests the graded rule
against the old one).

## 4. Feasibility audit — every component, one class each (recounted 2026-10-07)

`GREEN` = build now · `YELLOW` = build if time (or experiment-gated) · `RED` = production-only / research-only.
**Counting rule:** every component row carries **exactly one** class; the summary counts rows, so the numbers below are
recomputed mechanically from the table (previously some rows carried mixed classes, which is why the earlier summary did
not reconcile).

| # | Component | Data available? | Label / ground truth? | Algorithm | Complexity | 48 h | Runtime | Failure fallback | Class |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Parser (S1–S2) | yes (3,117 texts) | 100 surveyed (indirect) | regex/lexicon spans + typed fields | low | ✓ | ms | flat-token + `low_structure` flag | **GREEN** |
| 2 | Candidate retrieval (S3–S4) | yes (12 tables) | oracle (no labels needed) | rule + gazetteer exact/token match + linkage | low-med | ✓ | ms | empty arm recorded; `arms_available[]` | **GREEN** |
| 3 | Ranker: frozen interface + **rule baseline** (S5) | features yes | S-Val supervision (ops evidence) | transparent weighted rule | low | ✓ | <10 ms | this *is* the fallback | **GREEN** |
| 4 | Ranker challengers (logistic, shallow LambdaMART) | same features | S-Val supervision; S-Eval never touched | nested grouped CV | med | if time | <10 ms | rule baseline keeps serving | **YELLOW** |
| 5 | Belief fusion (S7) | observations yes | — | deterministic scoring over candidates + memory | low | ✓ | µs | last snapshot read-only | **GREEN** |
| 6 | Uncertainty (S8) | yes (`derived_ps3_radius_calibration.csv`) | S-Val errors per stratum | empirical quantiles + n-guard + parent fallback | low | ✓ | µs | parent stratum, widened, labelled | **GREEN** |
| 7 | `address_purpose` + eligibility (M7) | visit features yes | **no purpose labels** | rules P1–P5 + abstention | low | ✓ | µs | abstain → VERIFY_FIRST | **GREEN** |
| 8 | Direction cue generator | official POIs + parsed spans | n/a (deterministic) | town-scoped nearest + bearing + template | low | ✓ | µs | `null` when unresolvable | **GREEN** |
| 9 | Evidence scoring (S9) | 5,578 visits + trails + media | outcomes are evidence, not labels | structured feature extraction | med | ✓ | ms/visit | reduced weight + reason | **GREEN** |
| 10 | Integrity weighting (S10) | media hashes, dwell, GPS, agent baselines | FA009-style cases measured | reason-coded weights (never GPS-only) | med | ✓ | ms/visit | weight 1.0 + `insufficient_evidence` | **GREEN** |
| 11 | Place memory (S11–S12) | 900 confirmed places + clusters | visited outcomes | append-only store + place states + promotion per F2.2 | med-high | ✓ core | ms | memory miss → cold lane | **GREEN** |
| 12 | Neighbour index | 900 confirmed places | none needed (retrieval) | inverted index + as-of lookup | low | shadow only | ms | index off | **YELLOW** (C2-gated) |
| 13 | Historical replay J | historical visits + as-of model | outcomes + 100 truths | time-aware replay, **SIMULATION** label | med | ✓ | minutes CPU | cut rows, keep label | **GREEN** |
| 14 | Triage replay P | historical visits | outcomes (proxy), S-Eval for the summary | as-of policy replay + confusion tables | med | if time | minutes CPU | report as future work | **YELLOW** |
| 15 | **Offline field MVP** (pack → network OFF → local capture → durable outbox → replay on reconnect) | packs + observations | n/a | local store + outbox + capture screen + replay path | med | ✓ (demo slice) | — | queue locally; replay later | **GREEN** |
| 16 | Full offline app (multi-day autonomy, device lifecycle, encryption ops) | packs + observations | n/a | full mobile client | high | no | — | ship online-only first | **RED** |
| 17 | Distributed sync (server cursor feed, hold-then-mark-conflict, multi-device) | contract defined | n/a | push/pull + idempotency + conflict engine | high | no | — | capture locally, replay via file/API | **RED** |
| 18 | Slow loop S13 (challenger/promotion/recalibration execution) | simulated windows | gated promotion | prequential monitoring + gates | high | no | minutes/run | challenger never promotes | **RED** |

**Recounted summary: 12 GREEN · 3 YELLOW · 3 RED (of 18 rows).**
- **RED** = the three production-only rows (16 full app, 17 distributed sync, 18 slow-loop execution). None sits on the
  correctness path.
- Fixes applied by this recount (per the consistency pass): the offline MVP was split out of the old mixed "Offline app"
  row and is now **GREEN** (row 15); the ranker was split into rule baseline (GREEN) and challengers (YELLOW); replay was
  split into J (GREEN) and P (YELLOW). Section 7 of this pass's brief required exactly this: full sync stays RED while a
  minimal offline field demo is buildable now.

**Cuts this table forces (section 8 of the brief, "be brutal"):** full offline app, real sync, real slow loop, any
purpose/evidence neural model, Graphormer-class anything, vendor adapter, PIN polygons, and the neighbour index unless
C2 admits it. What remains is a complete end-to-end story on official data that runs in seconds.

## 5. Business test — the visit-triage / decision-quality replay (designed, not yet run)

Full pre-registration in `PS3_EXPERIMENT_PLAN.md` (experiment P). In one line: **for every historical visit,
reconstruct the pre-visit state as-of, let the policy decide `VISIT` / `VERIFY-FIRST` / `REFUSE`, and compare with what
actually happened.**

* **Measures:** bad-visit capture (share of negative-outcome visits the policy would have triaged away), negative-
  outcome capture, false verify-first rate, coverage retained, candidate/uncertainty quality per band.
* **Pre-registered thresholds:** tier ≥ PROBABLE ∧ radius within address band ⇒ VISIT; APPROXIMATE ∨ `n_neg ≥ 2` ⇒
  VERIFY-FIRST; UNPLACEABLE ⇒ REFUSE.
* **What it demonstrates:** *"SUTRA would have triaged historically weak field actions"* — a **decision-quality**
  claim, never a savings claim. Anchors already measured: warm 56.0% vs cold 24.5% met, post-cut `[S94]`.
* **What it cannot show:** that any visit was actually prevented, or any rupee saved — that requires a live slice.

## 6. Red team — 24 attacks (detect · mitigate · what we have · what is missing · change)

| # | Attack | Detect | Mitigate | Current status | Change made |
|---|---|---|---|---|---|
| 1 | Wrong frozen-baseline arm | stratum + surveyed sample checks | arm weight by stratum; memory overrides | covered (V1 baseline measured) | — |
| 2 | Wrong locality | locality-vs-pincode conflict flag (150 records) | candidate set + conflict reason | covered | — |
| 3 | Repeated landmark name across towns | ambiguity counter | town-scoped resolution; `ambiguous` flag | **was missing** | direction module §2.3 step 2 |
| 4 | Duplicate media | photo-hash clustering (FA009 162/610) | media weight + independence rule | covered | F2.2 |
| 5 | Coordinated fake visits | per-agent windowed baselines; spatial concentration | weight-not-verdict; cluster caps | covered (D11) | — |
| 6 | Same wrong candidate confirmed by multiple agents | independence dimensions | source/spatial independence required | partly | F2.2 (collector ≠ independence) |
| 7 | Address moved | negative accumulation across collectors/periods | `MOVED_SUSPECTED` + verify-first | **was forbidden** | F2.1 |
| 8 | Address renamed | text-key drift monitoring | identity vs render keys; no silent merge | covered (M1) | — |
| 9 | Multiple accounts at one place | co-location clusters (81) | place-keyed memory; never account-keyed | covered | — |
| 10 | One account at multiple places | same-account distance (median 3,011.6 m) | never merge by account | covered | — |
| 11 | Future memory leakage | as-of guard | `observed_at` reads only | covered (T0–T4) | index as-of rule added |
| 12 | Place-level split leakage | block ledger (36.0% proximity) | leave-block-out reporting | covered (A1) | — |
| 13 | Tiny-radius overconfidence | n-guard, coverage alarms | parent fallback + measured coverage | covered (U1) | U2 vocabulary |
| 14 | Cold start | cold lane is default-measured | `WARM`/`COLD` explicit states | covered | — |
| 15 | Offline pack stale | pack validity window | radius widening + reason | covered (R15.3) | — |
| 16 | Two devices, one visit | idempotency keys; duplicate claims | single evidence application | **was vague** | sync contract + F2.2 |
| 17 | Schema mismatch | `schema_version` on artefacts; loader refuses | additive-only schema; refuse-not-guess | covered | — |
| 18 | CRS mismatch | local-plane declaration | one declared frame; no reprojection | covered (canonical schema §4) | — |
| 19 | Ranker overfit | nested grouped CV on S-Val supervision (place blocks × accounts); S-Eval never touched | rule baseline; kill criterion | covered | M3b interface + immutable protocol §2 of the contracts |
| 20 | Purpose misclassification | abstention rate + gate audit | prefer abstain; borrower-confirmed exception | **was scattered** | purpose module |
| 21 | Landmark direction wrong | relation word only repeated, never invented | `null` over wrong cue; advisory only | **was missing** | direction module |
| 22 | Stale place memory | decay horizon + staleness state | `STALE` state widens radius | covered | — |
| 23 | Model belief becomes pseudo-truth | provenance marks; store vs projection | model-derived values can never be evidence | covered (M3) | ownership made explicit |
| 24 | Business metric improves by refusing more | refusal counters + coverage metric (D21) | plural acceptance metrics; report refusal quality | covered | triage replay reports it explicitly |

Three attacks (7, 18-adjacent ownership, 16) required real rule changes rather than documentation; two required new
modules (3, 20–21). The rest were already mitigated — the table above is the proof they were checked, not assumed.

## 7. Novelty reassessment — what we may and may not claim

**Cannot claim (prior art exists, per register group O):** geocoding itself · address parsing · learning from field
visits · using historical delivery/visit evidence (Delhivery sells it) [S77] · graph/language fusion of operational
traces (Meesho V2) [S80] · uncertainty/conformal calibration · offline field capture [S81].

| Claim | Label | Why |
|---|---|---|
| Place-keyed, provenance-aware, auditable **memory** used for collections-and-verification addresses (borrower × place × visit notice) | **COMBINATION** (novel context) | the parts exist (MDM, logistics memory); the collections-compliance context, evidence classes and reversal semantics are ours |
| Evidence **weighting instead of binary trust** with explicit contradiction states and graded negative semantics | **NOVEL** (as specified) | Delhivery verifies visits; nobody publishes graded negative-evidence semantics with `MOVED_SUSPECTED`/reverification in this domain |
| Purpose → action-eligibility gate tied to an RBI-shaped visit framework [S55] | **COMBINATION** | purpose classification exists; the gate mapping to the notice decision is the differentiator |
| Landmark direction cues from **official POI coordinates + parsed relation spans** | **STANDARD ENGINEERING** (honestly labelled) | simple geodesy; the value is workflow placement, not novelty |
| Empirical quantile radii with n-labelling and parent fallback | **STANDARD ENGINEERING** applied honestly | calibration is a solved practice; our contribution is refusing to overclaim |
| As-of (T0–T4) evidence discipline in a field loop | **COMBINATION** | point-in-time joins are known; applying them end-to-end to visits→belief is the contribution |
| Neighbour index from operational traces | **prior art** [S80]; our version **RESEARCH-ONLY unless C2 admits it** | the placebo (93.6 m) is the honest floor |

## 8. Simplification — what this pass cut, and why

**Cut now:** external-data arm (policy) · vendor adapter from the build (production-only) · PIN polygons (do not exist)
· full offline app and real sync (red; contract locked, demo simulates) · slow loop execution (red; design kept) ·
purpose/evidence neural models (no labels; external models prohibited) · landmark-snapping point model (already
rejected) · neighbour index default-on (placebo-controlled gate). **Kept, with discipline:** the four-layer
presentation (resolution / decision / field learning / governed learning) over S0–S13; the frozen ranker *interface*;
the two-population honesty of every number. **Result:** the end-to-end story — resolve → decide → visit → learn →
reuse — survives intact using nothing but the official dataset.

## 9. Demo feasibility (48h)

The lock candidate's §T build order fits one weekend: day 1 = parse + candidates + rule ranker + belief + uncertainty +
purpose/gate + direction cues on official data with the API surface; day 2 = evidence ingestion + integrity weights +
memory + the scripted demo (a failing-gate address, a visit that flips a decision, an injected low-integrity
observation that **widens without moving**, and the triage replay reading on historical visits). All inputs on stage
are official or explicitly labelled `SYNTHETIC`.

## 10. Remaining risks (carried into the lock, not hidden)

1. **Supervision is thin**: S-Eval (100 rows) measures but never trains, so learned components depend on the operational
   F2.2 confirmation pool, which may be too small — the rule baselines are therefore not a fallback but a likely *final*
   choice. Acceptable, and honestly reported (contracts §2).
2. **Purpose and triage thresholds** are pre-registered, not validated; experiment P may invalidate them.
3. **The neighbour index** may be cut by its own control (expected outcome, per the probe).
4. **Sync is designed, not built** — the riskiest real-world surface rests entirely on a written contract until
   implementation.
5. **The 36.0% place proximity** means any future "generalisation" claim without leave-block-out reporting is invalid
   by construction; the guard is procedural (A1), not automated.
6. **Recruitment of trust**: the graded negative-evidence rule (F2.1) is a behaviour change for operators; it needs
   the review queue exercised by real users, or it becomes theory.

---

*Sources: register group O `[S74]`–`[S83]`; measurements `[S90][S94][S96]`; policy `[S95]`; decisions D32–D44. Locked
architecture: `PS3_ARCHITECTURE_LOCK_CANDIDATE_2026-10-07.md`. Verification: `tools/check_workspace.py`,
`tools/check_leakage.py`, `tools/reproduce.sh`.*
