# SUTRA — SYSTEM DESIGN

How the blocks of `PS3_MASTER_ARCHITECTURE.md` become a running system: components, interfaces, sequence flows, state
ownership, failure paths, latency and cost budgets, deployment topology, and the deliberate decision *against*
microservices-for-their-own-sake.

---

## 1. Component inventory (nine components, no more)

| # | Component | Responsibility | State it owns | Must never do |
|---|---|---|---|---|
| C1 | `ingest` | take a record (batch/CSV/API), assign ids, declare CRS and provenance class | record identity | interpret text, geocode |
| C2 | `resolver` | normalise, parse spans, match gazetteers, emit typed fields + unresolved reasons | none (pure) | guess across towns; infer pincodes |
| C3 | `candidates` | build the arm set (vendor pin, locality, town, external, memory-as-of) with licence class | none (pure) | hide an arm's absence; use future evidence |
| C4 | `ranker` | score and order ≤25 candidates; produce score + reason codes | model version only | invent candidates; read T2 as T0 |
| C5 | `belief` | fuse candidate score + memory + visit evidence into a versioned belief | belief store (append-only) | delete or overwrite a version |
| C6 | `uncertainty` | tier, empirically calibrated radius, coverage bookkeeping, reason codes | calibration map | report nominal coverage as measured |
| C7 | `evidence` | turn a visit into structured, integrity-weighted evidence | none (pure, writes to belief) | move a coordinate on negative evidence |
| C8 | `memory` | append-only store of observations, beliefs, contradictions, evidence scores, aliases | the memory | allow UPDATE/DELETE of a version; serve a "latest" value to an as-of query |
| C9 | `slowloop` | quality-gated buffer, drift detection, retrain, calibration refresh, champion/challenger, rollback | model registry + promotion log | promote without the gate; retrain per visit |

Plus the **serving API** (`PS3_API_AND_COMPONENT_DESIGN.md`) and the **evaluation harness** (offline; reads the split
ledger and prints negative controls).

**Why not more components.** Each seam above is a real *policy* boundary (purity, state, or a licence). Anything else —
a separate "parser service", a "similarity microservice", a message bus per stage — would add operational surface with no
decision attached. The design is one deployable process with clear module boundaries until a measured need (scale, or a
licence-isolated store) forces a split. Microservice count is not a quality metric.

---

## 2. Interfaces (the contracts that matter)

```
C1 ingest   : ingest(records, source_meta) -> {accepted, rejected, crs, provenance_class}
C2 resolver : resolve(record)              -> {spans, typed_fields, matched_ids, unresolved_reasons}   (pure)
C3 cands    : candidates(address_id, as_of) -> [{candidate_id, arm, x, y, granularity, licence_class, source_ref}]
C4 ranker   : rank(features[T0|T1], model_version) -> [{candidate_id, score, reason_codes}]           (pure)
C5 belief   : get_belief(address_id, as_of) -> version | null
              update_belief(address_id, evidence, policy_version) -> new_version                 (append-only)
C6 uncert   : calibrate(stratum, evidence_class, model_version) -> radius_map_version
              radius(belief, radius_map_version) -> {radius_m, nominal, measured_coverage, fallback_reason}
C7 evidence : score_visit(visit, trail, media, agent_baseline) -> {w_i, reason_codes, dimensions}
C8 memory   : observations(address_id, as_of) · belief_at(as_of) · contradictions(address_id) · aliases(town_id)
C9 slowloop : buffer_add(record) · drift_check() · retrain(window) · promote(challenger_id) · rollback(version)
```

Invariants enforced at these seams (unit-tested, not documented-only):
1. `C3` may not read anything with `observed_at >= as_of`.
2. `C5` has no mutation path; a belief is corrected by appending.
3. `C6` returns `measured_coverage`; a caller cannot obtain a radius without it.
4. `C7` cannot emit a negative-evidence instruction that changes coordinates — the instruction type does not exist.
5. `C4` features are keyed by stage; a T2 feature in a T0 call is a hard error.
6. `C9.promote` requires a challenger comparison record and a rollback pointer.

---

## 3. Sequence flows

### 3.1 Cold resolution (query time, T0/T1)
```
client ─► API.resolve(text, town_id?, purpose)
        ─► C2 resolve ─► C3 candidates(vendor, locality, town, external?, memory as_of=now)
        ─► C4 rank (or rule-priority fallback if no model)
        ─► C5 belief.get (may be null → cold start)
        ─► C6 radius (stratum × evidence class)
        ─► response {coordinate, granularity, tier, radius_m, nominal, measured_coverage, reasons[], stage="T1", arms_available[]}
```
Budget: ≤ 250 ms p95 on official arms only (no external index is ever queried); the vendor call is
**never** on the critical path when a cache hit exists (and the cache obeys the licence clock).

### 3.2 During a visit (T2 — the in-visit score)
```
field app ─► API.score_visit(visit_id, live_trail, dwell_so_far, candidate_id)
           ─► C7 evidence.partial (integrity signals so far)
           ─► response {agreement: high|medium|low|insufficient, hint, reasons[]}
```
Purpose: tell the agent "you are 400 m from the pin and the pin is locality-grade" *before* they give up — an operational
change that is only possible because the radius is real.

### 3.3 After a visit (T3 → fast loop)
```
app/file ─► API.ingest_evidence(visit, outcome, trail, media_hashes, agent_id)
          ─► C7 evidence.score → {w_i, reason_codes, dimensions}
          ─► C5 belief.update (append-only version: position(s), tier, radius, evidence, contradictions)
          ─► memory: observation row + evidence_score row + (if needed) re-verification queue entry
          ─► response {belief_version, tier_after, radius_after, changed: true|false, why[]}
```
Guarantee in the response: **`changed:false` is a legitimate, common outcome** — most visits confirm and widen nothing.

### 3.4 Slow loop (T4 → model change)
```
nightly    : C9.drift_check()  → ADWIN on error/coverage stream, PSI on features, label-lag-aware window
threshold  : buffer(quality_gated, n ≥ N) ∧ (drift ∧ schedule) ∧ cooldown elapsed
action     : retrain (warm start) → recalibrate radius map → challenger evaluated on S-Val → promote | hold | rollback
```
Full detail and governance: `PS3_DYNAMIC_LEARNING_ARCHITECTURE.md` §5–§9.

---

## 4. Latency and cost budgets (design targets, measured in experiments)

| Path | p50 | p95 | Notes |
|---|---|---|---|
| Cold resolve, local only | 20 ms | 250 ms | index in-process; no network |
| Cold resolve, vendor cache miss | +150 ms | +800 ms | licence clock enforced; failure → local-only |
| Warm resolve (memory hit) | 5 ms | 60 ms | no arm rebuild needed |
| `score_visit` (T2) | 10 ms | 80 ms | trail geometry only |
| `ingest_evidence` (T3) | 15 ms | 120 ms | includes belief append |
| Nightly drift check | minutes | minutes | offline |
| Retrain (slow loop) | < 10 min on this data | — | one CPU, no GPU |

Cost: see `PS3_COST_ARCHITECTURE.md`; the design constraint is that a **batch re-resolve of the whole book (3,117 records)
must complete in minutes on one CPU** so the slow loop can re-derive features cheaply.

---

## 5. Deployment topology

| Context | Topology | Rationale |
|---|---|---|
| This project (48 h demo + evaluation) | one process, local files (`data/`), a SQLite/Postgres belief store, CLI + HTTP API | nothing to operate; the demonstration is the *behaviour*, not the infrastructure |
| Field deployment (production shape) | API service + Postgres + object store for media/trails + model registry + offline-first mobile client | the required state is relational and append-only; object storage holds the heavy evidence |
| District pack mode | a per-town artefact (index + calibration map + alias table) bundled for offline installation | the field is offline-first [S50]; the pack is the unit of sync |

No Kubernetes, no service mesh, no streaming platform is required by any design decision here. A message queue appears
only if the evidence volume forces it — and the design keeps evidence ingestion idempotent by `visit_id`, so that change
would be local.

---

## 6. State ownership (every state has one owner and one update mechanism)

| State | Owner | Written by | Update mechanism | Audit trail |
|---|---|---|---|---|
| address record | C1 | ingest | new record version on change (text never overwritten) | row versions |
| parsed fields / spans | C2 (derived) | resolver | recomputed per rule_version | rule_version per row |
| candidate set | C3 (derived) | candidates | recomputed per request, cached with as_of | receipt |
| belief (position(s), tier, radius) | C5/C8 | belief.update | **append-only versions** + reason codes | full history |
| contradiction state | C5 | belief.update | set/cleared by rule | history |
| evidence score per visit | C7/C8 | evidence.score | inserted once, immutable | reason codes |
| agent integrity baseline | C7 | evidence.score | rolling window recomputation | window params |
| radius calibration map | C6 | slow loop | replacement per version | version log |
| ranker model | C9 | slow loop | champion/challenger promotion only | registry alias history |
| alias tables (locality/landmark) | review process | human + ingest | versioned additions, never silent edits | review log |
| split ledger | evaluation | harness | new `rule_version`, never edited | ledger history |

---

## 7. Offline behaviour (the field is the first-class citizen)

* The mobile client holds a **town pack**: gazetteer index, alias table, calibration map, and the subset of memory for its
  beat. It can resolve, score a visit and update *local* belief with no network.
* Sync is **append-only and idempotent**: every capture is an event carrying a client UUID (idempotency key). An offline
  device never overwrites server belief — it submits observations; the server applies each event **once** and
  **recomputes beliefs deterministically** (M3). Conflicts are ordering problems, resolved by hold-then-mark-conflict,
  never by "whoever is heavier wins" (sync contract, `PS3_MLOPS_ARCHITECTURE.md`; D40).
* Media hashes are computed on-device (so duplicate detection works offline even before upload).
* A response generated offline is marked `offline=true, pack_age_days=N, radius_widened=true` — staleness is *visible*,
  never invisible.
* Vendor calls never block a field action; the pack is the fallback, and its age directly widens the radius.

---

## 8. Security, privacy and purpose control

| Concern | Control |
|---|---|
| Purpose limitation | every API call declares `purpose`; the belief/coordinate is returned with an eligibility flag, and the gate (a rule) is a separate component ([S48] pattern: status + review before acting) |
| Personal data in address text | addresses can contain names/phone numbers; the resolver strips obvious phone/ID patterns into a quarantined field used for nothing |
| Raw GPS trails | 90-day retention, then only the derived evidence score survives (`PS3_DATA_LINEAGE.md` §6) |
| Media | only hashes + verification verdicts are retained long-term; the image itself is not part of the model asset |
| Insider risk | no UPDATE/DELETE on belief versions; every write carries `actor`; anomalous read patterns are monitored |
| Licence compliance | each stored candidate carries `licence_class`; the serving layer refuses to emit a non-shippable row; caches obey vendor clocks (Google 30-day [S8]); the tree holds official data only (machine-guarded — no external dataset can exist) |
| Abuse of memory | a belief whose support is only one visit cannot be promoted; concentration caps (`PS3_RED_TEAM.md` F6) |

---

## 9. Failure paths and degradation ladder

| Failure | Immediate behaviour | Recovery |
|---|---|---|
| vendor API down/slow | local arms + cache; response says `vendor_unavailable` | retry off the critical path; cache refresh later |
| memory store unavailable | serve from the last read-only snapshot; block promotions (never accept evidence that cannot be logged) | restore, replay the queued evidence by idempotent id |
| ranker missing/corrupt | rule priority list (vendor > locality > town) — the measured baseline | restore model version; investigate |
| calibration map missing for a stratum | parent-stratum map, radius widened, reason code | nightly recalibration |
| evidence burst (a week of offline syncs) | buffer accepts; integrity weighting applies as usual; belief updates are ordered by `observed_at` | drift check runs after the burst, not during |
| model regression detected post-promotion | rollback to previous alias | incident: challenger gate reviewed |
| index/licence expiry | arm disabled, `arms_available` updated, radius widened | rebuild/refresh index under licence |

**The rule behind the ladder:** the system degrades by *admitting* uncertainty, never by inventing precision.

---

## 10. Acceptance of this design (what "done" means for the build)

1. Every flow above leaves an auditable trace (version numbers, reason codes, receipts).
2. Every invariant in §2 has a test that fails if violated.
3. Every response can be read by a non-ML reviewer: coordinate, granularity, tier, radius, reasons.
4. Every failure in §9 has been *exercised* in the fault-injection bed (`PS3_RED_TEAM.md` §2).
5. No component exists whose removal would not be noticed by a downstream decision — the pruning test from the commission.
