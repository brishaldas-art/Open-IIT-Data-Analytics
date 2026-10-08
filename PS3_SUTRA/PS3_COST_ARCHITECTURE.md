# SUTRA — COST ARCHITECTURE

Written **after** the correct architecture, on the commission's rule: build the scientifically defensible design first,
then find the cheap way to run it — never the other way round, and never by degrading the evidence or uncertainty layers.

Two cost questions, kept apart:
1. **What does the designed system cost to run?** (§2–§4)
2. **What may be substituted, and in what order, if the budget does not allow it?** (§5) — with the measured consequence
   of each substitution, and a hard floor below which the product should not be shipped because it would emit overconfident
   coordinates.

---

## 1. Cost drivers, and which ones are actually material here

| Driver | Material? | Why |
|---|---|---|
| Vendor geocoding calls | **Yes, if used per query** | per-call or per-1,000 pricing, plus licence limits on storage (Google 30-day cache [S8]); Mapbox separately sells permanent geocoding [S4] — i.e. even *caching* is a purchased product |
| Compute for models | **No** | every model here is tabular, small, CPU-only; retrain < 10 min |
| Storage | **No** | 3,117 records / 160,406 GPS points ≈ 30 MB; a 1 M-record book ≈ 10 GB with trails, ≈ 400 MB without `[I]` — an estimate, not a measurement |
| Engineering/ops time | **Yes** | the real cost is operating two loops and a belief store correctly |
| Field visits | **Dominant, but not ours to decide** | a visit already happens for collections; SUTRA's value is to *use* it, not to add one — the only new field cost is the small exploration slice |

**Design consequence:** cost control is not about shaving milliseconds; it is about (a) not making a vendor call the
critical path, (b) keeping the loop cheap enough to run conservatively, and (c) never paying twice for the same evidence.

---

## 2. Designed cost per 1,000 resolves (shapes and orders of magnitude, not invented prices)

| Component | Unit cost shape | Designed usage | Notes |
|---|---|---|---|
| Local resolve (rules + memory + ranker) | ~free (CPU only) | 100% of queries | measured: preprocessing 23 s for 3,117 records; a resolve is milliseconds |
| Vendor pin | per-1,000 calls, plus caching licence | **cold records only, cached** | warm records use memory; the cache clock is enforced |
| External index (Overture/OSM…) | — | **REJECTED (final data policy, 2026-10-07):** no external index exists in this architecture | not in the cost model |
| Reranker (GBDT) | ~free | always (tiny candidate sets) | if a neural reranker were ever added, cost rises 100–1000× [S19] — hence RESEARCH ONLY |
| Evidence ingest | ~free | per visit | milliseconds |
| Slow loop | minutes of CPU per retrain | ≤ monthly + gated | the cheapness is what lets it be conservative |
| Storage/retention | negligible | trails 90 days, scores permanent | retention is a policy choice, not a capacity constraint |

**We publish no rupee/dollar figures we cannot source.** Prices for commercial geocoding are vendor- and volume-specific
and change; quoting a number would violate the standard this package holds (no invented statistics). What we publish is the
*structure* of the cost and the substitutions available when a budget is imposed.

---

## 3. The cost-control mechanisms (each tied to a design decision)

| Mechanism | What it saves | Design cost of using it |
|---|---|---|
| **Memory before vendor** | vendor calls on every already-verified address | memory must be trustworthy — hence the integrity layer (this is the architectural justification for what looks like an "extra" component) |
| **Cache with a licence clock** | repeat calls for the same text/pin | cannot store Google content beyond 30 days [S8]; our own belief is stored instead — the cache is a *convenience*, the belief is the *asset* |
| **Candidate cap ≤ 25** | reranker cost, index scan cost | negligible accuracy risk at this arm count |
| **Conditional reranking** | reranker invocations (skip when the top-2 margin is wide) | a margin threshold must be calibrated (experiment D reports the effect) |
| **Local official-gazetteer index** | per-query vendor calls | one-time build from the official tables already in the pack; no external index exists (final data policy) |
| **Batch, not interactive, for bulk** | vendor price tier | results are less fresh — acceptable for the seasonal re-verify sweep |
| **Cheap features** | no GPU, no embedding service | limits the parser/model tier (accepted: see §4) |
| **Town packs** | central compute in field use; network | staleness must be *shown* (pack age widens the radius) |
| **Two-loop split** | avoids per-visit training entirely | governance overhead (worth it: it is the reason the system is auditable) |

---

## 4. What we deliberately do not spend on (and why it is not a compromise)

| Not bought/built | Cost avoided | Why it is not needed |
|---|---|---|
| GPUs / embedding infrastructure | large, recurring | the signals here are structural and tabular; embeddings are RESEARCH ONLY with no licence-cleared model and no real-text benchmark (`PS3_DATA_PREPROCESSING.md` §2) |
| LLM inference per address | large, per-call | parsing here is a bounded task; the practitioner evidence shows a small model at 19 ms versus 4.6 s for a comparable-accuracy alternative [S17] |
| A global geocoder of our own | enormous | the vendor pin is one arm; the differentiator is field-learned memory, not global coverage |
| Microservices/K8s/message bus | ops overhead | one process with clear modules; a queue is a local later change if volume demands (`PS3_DATA_ARCHITECTURE.md` §1) |
| A data warehouse | ETL + ops | 30 MB of tables, queried by keys and time ranges |
| Real-time streaming analytics | ops + complexity | the fast loop is per-visit and idempotent; batch drift checks are enough |

---

## 5. Substitution ladder (only if budget forces it — application order is fixed)

| Step | Substitution | Measured/expected consequence | Acceptable? |
|---|---|---|---|
| 1 | **Drop the reranker** (ship rule priority) | measured: rule priority ≡ the official frozen baseline geocode arm (376.4 m / 9.0%) [S91]; the reranker's contribution is whatever experiment D shows | Acceptable **only if** D shows a small gain; the honest baseline is already the plan |
| 2 | **Trim parsing tiers** | rules already cover the bulk; the residue is small | Acceptable |
| 3 | **Reduce tier-2 parser** to rules only | affects the unresolved residue; measured by experiment B | Acceptable |
| 4 | **Fewer vendor calls** (cold-only + cache) | more `APPROXIMATE` tiers for cold records, wider radii — visible, not hidden | Acceptable |
| 5 | **Less frequent slow loop** (quarterly instead of monthly) | slower reaction to drift; the detector still alarms | Acceptable with monitoring |
| FLOOR | **Remove integrity weighting or the calibrated radius** | fakes move coordinates; radii become nominal claims with no coverage; the product starts lying | **NOT acceptable — do not ship this configuration** |

**The floor is the point of this document.** Cheaper versions of SUTRA are legitimate only while they still return
*uncertain coordinates with reasons* instead of *confident coordinates without evidence*.

---

## 6. Cost of the two loops (why the design is affordable at all)

| Activity | Frequency | Cost | Scaling |
|---|---|---|---|
| Fast loop per visit | every visit | ms of CPU, one small append each to `observation`, `evidence_score`, `location_belief` | linear in visits |
| Nightly drift check | daily | seconds (4 scalar streams + feature PSI) | linear in features |
| Retrain | gated, weekly–monthly | < 10 min CPU, no GPU | ~linear in rows ≤ 10⁵ |
| Recalibration | with retrain | seconds | small |
| Town pack rebuild | on gazetteer change | minutes | per town |
| Full-book re-resolve | seasonal sweep | minutes on one CPU (measured: 23 s featurisation for 3,117 records) | linear |

**If a budget forces one choice:** keep the fast loop, keep the integrity layer, keep the calibrated radius, and cut the
slow loop's frequency. A system that never retrains but never lies is worth more than one that retrains nightly and moves
coordinates on a fake visit.

---

## 7. What we cannot cost honestly (stated, not guessed)

1. **Vendor pricing** — commercial geocoder prices are volume-negotiated and licence-dependent; no reliable public number
   applies to a deployment of this shape. The design therefore minimises *dependence*, not a specific price.
2. **Field-visit cost** — the dominant real-world cost, but it belongs to the collections operation, not to SUTRA; SUTRA's
   contribution is to make existing visits more informative. Any claim that SUTRA reduces field cost must come from a
   measured reduction in *repeat* visits, which is an operational experiment we have not run.
3. **The cost of a wrong coordinate** — the reason the whole architecture exists; a decision that reaches a person carries
   a cost that is not ours to quantify, which is exactly why the eligibility gate is a separate component and not an
   optimisation (`PS3_API_AND_COMPONENT_DESIGN.md` §5).
