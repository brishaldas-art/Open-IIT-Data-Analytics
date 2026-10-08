# SUTRA — MLOps ARCHITECTURE

How SUTRA is run, monitored, promoted, rolled back and audited — with the same governing idea as the rest of the
architecture: **automate the cheap, reversible things; gate the expensive, hard-to-reverse ones.**

---

## 1. Environments and artefact flow

```
                 ┌───────────── DEV ─────────────┐
Domain A (frozen)│ notebooks? NO — tools only    │  data/cleaned, data/derived, receipts
                 │ tools/*.py (deterministic)    │
                 └───────────────┬───────────────┘
                                 │ manifest + receipts + tensor hashes
                 ┌───────────────▼───────────────┐
                 │        STAGING / EVAL         │  experiments A–O, negative controls, model cards
                 └───────────────┬───────────────┘
                                 │ promotion gate (§4)
                 ┌───────────────▼───────────────┐
                 │          PRODUCTION           │  champion model + calibration map + town packs
                 │  registry aliases: champion    │  belief store (append-only)
                 └───────────────┬───────────────┘
                                 │ every response cites versions
                          audit / review tooling
```

**Rule:** the dataset never moves between environments. Only *artefacts* (models, calibration maps, packs) move, each
with its manifest and receipts. Domain A stays hash-frozen wherever it is read (the toolchain asserts it).

---

## 2. What is versioned (and what the version is attached to)

| Artefact | Version identity | Attached to |
|---|---|---|
| Official data (DATASET A) | `source_snapshot` (SHA-256 manifest) | every derived artefact and every experiment; no external data exists in the tree (machine-guarded) |
| Cleaning / resolving / candidate rules | `rule_version` | rows and receipts |
| Feature sets | `schema_version` + `rule_version` + tensor hash | the model card |
| Belief store | per-address `version`, plus a store snapshot id | every response and every memory experiment |
| Evidence policy | `policy_version` | every `evidence_score` row (beliefs re-derivable from observations) |
| Calibration map | `radius_map_version` | every response (`nominal` + `measured_coverage`) |
| Models | registry version + alias (`champion`, `challenger`) | every score |
| Town packs | pack version + `pack_age_days` | every offline response |
| Split ledger | `rule_version` | every metric |

**The 1:1 property that makes auditing possible:** any coordinate a consumer ever received can be reproduced from
(belief version, calibration map version, model version, policy version) — all of which are recorded in the response and
the log.

---

## 3. Monitoring (four layers, each with a named owner and an alarm)

| Layer | Signals | Alarm | Who acts |
|---|---|---|---|
| **Data** | ingest volume, null-rate per field, unresolved-rate, `OUT` share, pincode-token match rate, duplicate-text count, buffer shrinkage after the quality gate | deviation beyond the trailing distribution → **block retrains**, investigate | data owner |
| **Model / drift** | ADWIN on the error and coverage streams, PSI/KS per feature per town, uncertainty proxy, outcome-mix shift [S31][S32] | drift persisting two windows ⇒ trigger (cooldown + hysteresis) | ML owner |
| **Belief / loop** | version counts, contradiction rate and age, promotion-block rate, share of beliefs with ≥2 independent confirmations, evidence concentration (Herfindahl), share of promotions driven by one agent-day cluster | any belief whose support is a single low-integrity visit; contradiction backlog growth | loop owner |
| **Serving / cost** | p50/p95 latency, vendor call share, cache hit rate + licence-clock compliance, refusal rate and its correctness, tier mix | latency or cost beyond budget; refusal-rate jump (a silent accuracy strategy) | platform owner |

Plus the **fairness monitor** (a first-class one, not a footnote): per-agent integrity flag rates with the **clean-visit
false-positive rate** published alongside, and a review path for an agent to have a flag examined.

---

## 4. Promotion gate (the same seven conditions as the slow loop, restated as ops)

1. Primary metric improves beyond the grouped-bootstrap interval on S-Val (and no regression on S-Eval beyond its interval).
2. Measured **coverage ≥ nominal** with the n-guard.
3. No stratum with n ≥ 15 regresses beyond its interval.
4. Negative controls behave (shuffled ≈ chance; agent-ID-only under-performs).
5. Cost and latency within budget.
6. Refusal behaviour unchanged or better, and **visible**.
7. Invariant tests pass: no negative-evidence movement, no pin-agreement feature, no T2 feature at T1, ids/CRS declared.

A promotion writes a **model card** (`PS3_DYNAMIC_LEARNING_ARCHITECTURE.md` §7) and flips the registry alias. Rollback is
one alias flip, with a pre-declared regression alarm so it is a rule rather than a debate [S34].

---

## 5. Incident playbooks

| Incident | First action | Recovery | Prevention |
|---|---|---|---|
| Vendor outage | serve local arms; response says `vendor_unavailable`; stop calling for N minutes | resume off the critical path | circuit breaker + cache-first |
| Memory store unavailable | read-only snapshot; **refuse writes** (never accept evidence that cannot be logged) | restore, replay queued evidence by idempotent id | replication + snapshot drills |
| Poisoning detected (F6) | trace belief → supporting observations → evidence scores; supersede with a version citing the rollback | re-derive affected beliefs from observations minus the flagged evidence | promotion gate, concentration caps, agent scoping |
| Drift alarm during a data incident | do **not** retrain; retraining on broken data is worse than waiting | retrain once data quality is restored | quality gate blocks the loop |
| Calibration regression in production | widen radii immediately (safe direction), rebuild the map in the slow loop | — | coverage monitor |
| Licence expiry / policy change on an external source | disable that arm; `arms_available` reflects it; rebuild without it | rebuild pack | licence register checked in CI (`check_workspace.py`) |
| Schema/CRS surprise | stop ingest for that feed; the CRS declaration is mandatory | fix at the boundary | envelope + impossible-coordinate checks |

---

## 6. Reproducibility contract (what "reproducible" means in practice)

* Every number in the document set is produced by a script in `tools/` (`bash tools/reproduce.sh`).
* Every derived artefact carries: source snapshot, rule/schema/policy version, row counts in/out, and the reason codes for
  drops (cleaning log).
* Every experiment records tensor hash, split version, receipts, belief-store version, and negative controls.
* **Determinism:** fixed seeds, no random sampling in cleaning, stable sort orders, golden-file tests on the JSON output.
* **Hash proof:** `tools/check_leakage.py` re-checks Domain A's hashes against `tools/section_manifest.csv` on every run.

---

## 7. Team surface (what a small team actually has to operate)

| Role | Owns | Cadence |
|---|---|---|
| Data owner | Domain A integrity, cleaning rules, licence register | per release |
| ML owner | ranker + evidence policy + drift detectors | per retrain |
| Loop owner | belief store, promotion/rollback log, contradiction queue, fairness monitor | weekly |
| Platform owner | serving, latency, cost, offline packs | continuous |
| Reviewer (compliance/ops) | eligibility gate, adjudications, review queue | per shift |

Five responsibilities, no more. Every alarm in §3 maps to exactly one of them, and every state in the system has one owner
(`PS3_SYSTEM_DESIGN.md` §6).

---

## 8. What we do NOT operate (and why it is not a gap)

* **No feature store**: the features are derived deterministically in minutes from a 30 MB dataset; a store would add a
  moving part whose only benefit is speed we do not need.
* **No streaming platform**: evidence is per-visit and idempotent; batch drift checks suffice.
* **No auto-rollback on a single metric**: rollback is triggered by pre-declared alarms, not by noise-level fluctuations
  (cooldown and hysteresis exist for a reason).
* **No unattended promotion.** The gate is automated; a human approves the promotion, because the consequence of a bad
  coordinate reaches the field.
* **No synthetic data in production paths.** Synthetic data is used only where labelled as such, never to train a shipped
  model (`PS3_ASSUMPTIONS.md`; the official dataset is itself synthetic, and every document says so).

---


## Sync contract (final, 2026-10-07)

The offline path is specified as a contract, not a slogan. It replaces the earlier vague "highest weight wins"
phrasing, which would have made two devices converge by accident rather than by rule.

```
DEVICE (offline)                                   SERVER
──────────────                                     ──────
provisional:  local store = projection + decisions
observation:  append-only record, signed, with:
              · observation_id (UUID, client-generated → idempotency key)
              · local_seq (monotonic per device)
              · captured_at_device + server_received_at (both kept)
              · media hash + integrity fields
outbox:       durable queue; states PENDING → IN_FLIGHT → SYNCED | FAILED | CONFLICT
push:         replay-safe batch push, ordered by local_seq, each item idempotent by observation_id
pull:         changes since server cursor (incremental, tombstones included)
conflict:     server hold-then-mark-conflict per ODK precedent [S81]: an update whose base version the
              server has not seen is HELD (≤ 7 days, configurable) and applied in order once the base
              arrives; after the window it is marked CONFLICT for human review — never silently dropped
recompute:    the server re-derives the belief deterministically from stored observations [M3];
              the device accepts the recomputed belief on next pull
duplicates:   same observation_id ⇒ single application (retry-safe) [S82]
two devices, one visit: first accepted observation_id wins as the evidence; the second is linked as a
              duplicate claim, not counted as an independent confirmation [F2.2]
```

Rules stated once: device clocks are evidence, never ordering authority (server cursor + local_seq order the
stream); LWW is explicitly rejected for evidence; deletions require tombstones; every sync state is visible to
the collector (saved locally / syncing / synced / conflict / failed). Pack staleness beyond validity **widens
the radius and says so** (R15.3, unchanged).

**Scope split (2026-10-07).** The **full distributed sync is RED — production-only**, but a **minimal offline field
MVP is GREEN** and ships in the 48-hour build:

```
offline MVP (GREEN)                     full sync (RED — production-only)
────────────────────                    ────────────────────────────────
download pack (file)                    server cursor feed
network OFF (airplane mode demo)        multi-device concurrency + hold-then-conflict engine
capture evidence locally (SQLite)       device lifecycle, encryption ops, remote wipe
durable outbox (PENDING items, UUIDs)   background scheduling, battery/backoff policies
replay on reconnect: push the outbox    partial-batch recovery, tombstones, retention compaction
to the local API (idempotent) and
watch the belief recompute
```

The MVP exercises every rule of the contract that matters for correctness (append-only capture · idempotency ·
deterministic recompute); it omits only the operational engineering. Nothing in the MVP contradicts the contract, so the
production build is an extension, not a rewrite.
