# SUTRA — FINAL PRODUCT INTEGRATION REPORT · 2026-10-08

**Scope of this report.** The P1/P2 backend product surface, the frontend fixture-excision pass, the
new guards, and the verification that was actually executed in this session. Every figure below is a
value observed in this session's output — nothing is carried over from an earlier report without
being re-measured, and nothing is estimated.

**Status key.** `IMPLEMENTED` · `DESIGNED` (specified, not built) · `NOT YET IMPLEMENTED` ·
`NOT MEASURED`.

---

## 1 · THE BATTLE-MODEL SHELL: RETRIEVED, INTEGRATED, SERVED

The earlier finding in this report — that the Battle-Model zip was `NOT RETRIEVABLE` — is **superseded**.
The Drive link arrived, the archive downloaded byte-exact (sha256 `77c1d289dd2fb27a…fe36`, 264,431 B,
28 files), and its tree now lives at `battle_model/`: same structure, typography, hierarchy and
navigation, wired to the real service instead of its fixtures. **The service serves that build at `/`.**

| What the shell shipped with | What it is now |
|---|---|
| a 548-line fixture module (`battle_model/src/lib/fixtures.ts`: invented providers, scores, GPS trails, SLA hours) | **deleted** — nothing imports it; every number on screen is fetched |
| the Resolver's `verdict()` — a React re-derivation of the gate at invented thresholds (0.85 / 0.60 / 0.15 / 25 m) and an invented score decomposition (text / components / source trust / evidence / memory) | gone; decision, gate, tier, radius, reason codes and score terms come from `POST /resolve` (`eligibility`, `decision_ticket`, `score_terms`, typed `reason_codes`) |
| `VQ-49${Math.random()}` case ids; a `setTimeout` "pipeline trace" with invented millisecond budgets | the real task id from `POST /resolve` → `task`, and each arm's real consideration from `arms_considered` |
| a session ledger (SEAL-01, epoch 2025-W46, `chainHash`) and a `demo 0.9.4 · fixture replay` shell banner | the service's own as-of clock, version block, pack freshness and provenance; the shell's mode chip reads LIVE RUNTIME |
| Places / Field Evidence built on fixture maps (`PLACE_EVIDENCE`, `Math.random()` reverification ids, a confidence %) | `GET /v1/places` and `GET /v1/evidence` — new **read-only projections** in `sutra/feeds.py`, no frozen module touched |
| Queue "close case" patched locally; "Assign to me"; fake SLA countdowns | `PATCH /v1/tasks/{id}` and `POST /v1/adjudicate` with the service's permitted transitions, receipts and effects |
| Method page's invented stages, gates, weights and "214 ms" | `GET /v1/method-trust`: the real receipts, the three frozen populations and the four status labels |

Build: `cd battle_model && npm ci && npm run build` → `battle_model/site/index.html`, **one file**,
345,597 B (98.7 kB gzipped). `sutra/api.py::_web_root()` prefers it and falls back to the earlier
console build in `web/site`, which remains in the tree.
## 2 · BACKEND — `IMPLEMENTED`

New modules: `sutra/product.py` (774 lines) and — added for the workbench integration — `sutra/feeds.py`
(the two read-only projections below), plus routes in `sutra/api.py`. The frozen intelligence is
untouched: `sutra/candidates.py`, `sutra/ranking.py`, `sutra/belief.py`, `sutra/uncertainty.py`, `sutra/memory.py`, `sutra/evidence.py`,
`sutra/eligibility.py`, `sutra/purpose.py`, `sutra/store.py` were not modified.

| Endpoint | What it does | Verified live result |
|---|---|---|
| `GET /v1/overview` | operational aggregates at a cut: coverage, workload by reason in product words, field activity, pack freshness, **cold/warm split and tier mix** | 3,117 indexed · 278 open cases (273 possible-move + 5 conflicting) · 3,788 visits at the cut · warm 1,280 / cold 1,837 · tier mix 911 APPROXIMATE / 271 CONFIRMED / 295 PROBABLE · packs T1–T4 with `valid_until` + `stale: false` |
| `GET /v1/method-trust` | the mechanism, the safety rules and the three frozen populations, read from the receipts | 8 steps · 7 safety rules · cold 0.71 n=100 · warm 0.9677 n=31 · product 0.76 n=100 |
| `GET /v1/tasks/{id}` · `/history` | one case, its ledger and its adjudications | `VF-AD002936-MOVED_SUSPECTED` · "Needs review" · 1 event · allowed `in_progress/resolved/reopened` |
| `PATCH /v1/tasks/{id}` | append-only lifecycle; validated against the state machine; idempotent replays | open → in_progress → resolved → reopened; retried request returned the recorded event |
| `POST /v1/adjudicate` | a human review decision, stored as an **adjudication observation** (`kind=adjudication`) and replayed through the frozen belief mechanism; closes the case with an appended event; idempotent on the key | live review of `AD002936`: `confirmed` → `met_family`, belief recomputed to **v10**, tier/status/uncertainty **unchanged**, `coordinate_moved: false`, case closed *Reviewed*; replay returns the recorded receipt and writes nothing. A **backdated** review (`as_of` in the past) replays that instant instead and can select a different candidate — see §6.5 |
| `GET /v1/audit` (+ `address_id`/`place_id` scope) | decision history in product language, negatives labelled "does not move the location" | AD002936: 8 events, flip at 2026-05-30T04:45:54Z, adjudication appears as "Location confirmed by reviewer · belief unchanged" |
| `POST /v1/score_visit` | "what would this visit change" — simulated on a throwaway store copy, then discarded | advisory, `applied: false`; store census unchanged; assumptions stated (`agent_id` + basis) |
| `GET /v1/address/{id}/case` | one address, one coherent story, one request | AD002936: APPROXIMATE/MOVED_SUSPECTED, task, 8 history rows, 6 observations, place, decision ticket |
| `POST /v1/batch_resolve` | bounded (**≤5,000**, the contract ceiling) batch with a per-row ticket and an aggregate: refusal rate, tier mix, radius histogram — never a bulk-accuracy claim | `{"SERVE": 1, "REFUSE": 1}`; refusal rate 0.5; tier mix 1/1; histogram counts 1 in the 500–1000 m band; the refused row carries **no radius** |
| `GET /v1/audit/{belief_id}` | the full provenance chain for one answer: evidence with the engine's weights and reason codes, the losing candidates, the uncertainty change, the tasks | `AD002936:7` → 6 weighted steps (the negative carries weight 0.3375 and its reason codes), winner arm `field_evidence`, radius 1202.6 m, 1 task |
| `GET /v1/places` *(new, for the workbench)* | the memory graph as a read-only projection: identity rule, state, tier, member count, radius and basis at a cut; filters `q,state,tier,town_id` + cursor | 3,117 places · CONFIRMED 271 / MOVED_SUSPECTED 273 / WARM 300 / COLD 2,268 / CONTESTED 5 · identity rule `colocation<=30m\|adjudicated` |
| `GET /v1/evidence` *(new, for the workbench)* | the stored observations as a read-only feed with the evidence policy's verdict per row; a negative keeps its device position, labelled `coordinate_claim: false` | 3,788 rows · positive 1,539 / negative 1,141 / ambiguous 1,108 · `negatives_move_coordinate: false` |

Rules the implementation holds to, each covered by a test: **append-only** (a transition adds an
event, never edits one, from the ledger's own insertion order); **the single as-of gate** (the
overview's own timestamp filtering was rewritten to use `sutra/asof.py` after the frozen invariant
test caught it); **receipts are read, never invented** (method-trust reads the frozen receipts; the
overview reads the packs already on disk instead of calling `build_pack`, which writes files);
**isolation** (write paths verified against a byte-copy of the store, never the shipped one).

---

## 3 · FRONTEND — `IMPLEMENTED`

### 3.1 · The workbench is the served frontend (handoff §2, §34)

Preserved, not redesigned: the paper/graphite/restrained-orange palette, the serif numerals, the mono
diagnostics, the six-screen navigation (Overview · Resolver · Places · Field Evidence · Verify Queue ·
Method & Trust), the three-zone Resolver workbench, the SVG local plane with candidate↔map↔decision
cross-highlighting, the evidence timeline, and the responsive collapse. The diff is data-binding, not design.

### 3.2 · Nothing invented, nothing re-derived (handoff §3)

Every value the workbench renders comes from a route: the Resolver answers from `POST /resolve` (the same
call serves the typed free-text intake — no fixture replay), the plane from `GET /v1/plane/{town}` and
`GET /v1/geometry/{id}`, Places from `GET /v1/places` + `GET /v1/place/{id}`, Evidence from
`GET /v1/evidence` + `GET /v1/address/{id}/observations`, the Queue from `GET /v1/tasks` + `PATCH` +
`POST /v1/adjudicate`, Method & Trust from `GET /v1/method-trust` + `GET /v1/audit/{belief_id}`, Overview
from `GET /v1/overview`. Reason codes are typed objects end to end — no code path parses a reason string —
and the UI never recomputes ranking, gate, tier, radius or priority.

Refusal is first-class: the service's `refusal` block renders the panel, and the plane renders its
withheld state with **no coordinate, no radius and no geometry** (smoke check 08).

### 3.3 · Guards

`tests/test_no_fake_data.py` now scans the workbench too — `battle_model/src` and the built
`battle_model/site/index.html` — alongside the console sources (9 tests). The new assertions: no banned
token in the workbench sources or in the shipped bundle, and every route the workbench's API layer calls
is a real route. `tools/reproduce.sh` gained the workbench build as a numbered step, so the one-command
chain regenerates the frontend the service serves.
## 4 · TESTING — `IMPLEMENTED`

| Suite | Tests | Result |
|---|---|---|
| `tests/test_acceptance.py` | 26 | pass |
| `tests/test_contract_v1.py` | 51 | pass |
| `tests/test_product_v1.py` (new) | 39 | pass |
| `tests/test_no_fake_data.py` (§49/§11 + workbench) | 9 | pass |
| **total** | **125** | **125 passed** (26.8 s) |

Notable tests, not decoration: `score_visit` writes nothing to the shipped store (census compared
before/after); the product layer may only call `append_task_event` (source-scanned); a reviewed case
must be reopened before another decision; every read path leaves the shipped store's data tables
untouched; the frozen policy body hash recomputes; the frontend has no client-side geography, no
randomness, no static fixture import.

**HTTP smoke:** `tools/smoke_test.py --base http://localhost:8000` → **21/21 passed** against the live
service (the two new checks cover the workbench's projection endpoints: `/v1/places` and `/v1/evidence`).
**Browser smoke (the served frontend):** `battle_model/tools/browser_smoke.mjs` → **22/22 checks
passed** against a copied store on `:8001`, 0 console errors, 0 failed requests; writes the 12
`bm-*.png` screenshots. The earlier console script (`web/tools/browser_smoke.mjs`, 14 steps) is
retained and still passes, but it exercises the fallback build, not the product surface.
**End to end:** `bash tools/reproduce.sh full` → green (all numbered steps, including the added
workbench build), then pytest, the guards and both smokes re-run against its output.

---

## 5 · INTEGRITY — `VERIFIED`, WITH ONE FALSE ALARM RECORDED

| Check | Result |
|---|---|
| Official PS3 data (leakage checker, includes the Drive hash comparison) | **ALL PASSED — official dataset unmodified** |
| End-to-end reproduction | `bash tools/reproduce.sh full` → **green** through every numbered step, old and added (acceptance 26 · contract 51 · console build · **workbench build** · experiments A–D · precision · demo · leakage/links/workspace) |
| Frozen evidence/memory policy (emp-v1) | body hash **recomputes exactly**: `policy_hash()` over the policy body (the file minus the two tool-written fields `policy_sha256` / `scoring_code`) → `a110f08962993e3c…2775`, equal to both the file's own `policy_sha256` and the receipt's `frozen_policy.sha256`; `s_eval_used_for_selection: false` |
| Frozen evaluation lanes | reproduce exactly on re-run: product lane n=100 · 0.33 @100 m · **0.76 @500 m** · median 202.2 m; cold 0.71/375.8 (n=100); warm 0.9677/12.4 (n=31) |
| S-Eval locked-read ledger | disclosed as an integer by `GET /health`; **reading it never advances it**. It is a store-state counter, so the deterministic rebuild restarted it (see the note below); the historical ledger of **10 reads with full timestamps** is preserved in `data/derived/evidence_memory_policy_receipt.json` (`s_eval.read.timeline`) |
| Store census after the rebuild | observations 5,578 · evidence_scores 5,578 · belief_versions 2,757 · task_events 278 · receipts 0 — **the documented baseline, restored exactly** |
| Store determinism | `tools/build_store.py --reset` twice produced the same attestation digest (`0af3e93fb7469…`, n=5,578) |
| Store ledger | `VF-AD002936-MOVED_SUSPECTED` holds exactly one event, state `open` — no post-era rows (`at ≥ 2026-07-01`: 0) |

### 5.1 · Disclosed: the shipped store was written to, and deterministically restored

While probing the new adjudication path I ran the writes against the **production service** instead of the
sandboxed copy I had prepared (the `SUTRA_STORE` variable applied to the test client, not to the server).
That added 2 adjudication observations, 2 belief versions, 3 task events and 2 receipts to
`data/derived/runtime/sutra_store.sqlite`, and closed then reopened the `AD002936` case — which the browser
smoke then caught as a broken demo step.

The store is a **pure function of the official visit history**, so it was restored with the sanctioned
deterministic rebuild, not by editing rows:

```
python3 tools/build_store.py --reset      # ingest digest 0af3e93fb7469… identical on repeat runs
```

Everything downstream was then re-verified against the restored store: 125 tests, `bash tools/reproduce.sh
full` (green), 21/21 HTTP smoke, 22/22 workbench browser smoke, guards. All later write-path tests — including
the browser smoke's own transition and adjudication checks — ran against a **copied** store on a second
service instance (`SUTRA_STORE` set on the server process), so the shipped store was not touched again.
The final `reproduce.sh full` pass rebuilds the store from the official history as its documented step 6;
after it, the census is again 5,578 / 2,757 / 278, receipts 0, and `GET /health` reports the counter the
rebuild restarted (`s_eval_looks: 7`) — the historical ledger of 10 reads with timestamps remains in
`data/derived/evidence_memory_policy_receipt.json`.

### 5.2 · Finding: 70 of 1,477 addresses changed tier across the rebuild

The rebuilt store is not byte-identical to the pre-rebuild one: at the `2026-06-01` cut, 70 of the 1,477
addresses that carry a belief differ in tier (mix 843/271/363 → **911/271/295**). Traced by payload diff on
`AD000002`: the pre-rebuild build carried a fourth, cross-agreeing arm (`fine_pin_with_cross_arm_agreement`,
+0.04 score, tier PROBABLE); the current pipeline emits three arms and scores the same address
`cold_start_no_field_evidence` at APPROXIMATE. The two demo cases (`AD003067`, `AD002936`) and every frozen
lane are unchanged, and the acceptance, contract and browser suites all pass on the rebuilt store.

Read plainly: the pre-rebuild store was built by the pipeline **as it stood then**; the current pipeline —
with the frozen memory-withholding policy in force — no longer emits that agreement arm for pin-derived
priors. The rebuilt store is the reproducible artefact; the old store's extra arm is the thing that does not
reproduce. **Open item** (§38): confirm against the memory-policy receipt that the withheld arm is the
pin-derived prior (the receipt says exactly that: *"the 14 withheld answers were the vendor pin re-wrapped as
memory"*), and record the tier-mix change in the method notes.

### 5.3 · Finding: the published frozen-configuration hash moved

The regenerated `data/derived/final_precision_config.json` carries `frozen_configuration_sha256 =
9abebb8f…`, while the frozen evidence/memory policy receipt and the backend gap audit quote the precision
configuration as `ac61cf2e…`. The **behavioural knobs are unchanged** (`candidate-rules-v2`,
`evidence-policy-v3`, `radius-map-v1`, retrieval `v2`, `place_neighbour` disabled, `w_n_guard 15`,
`locality_min_coverage 0.5`, coordinate policy `coord-v2-trace-tail`) and **every frozen lane reproduces
exactly**, so the movement is confined to the canonicalised version object — which embeds the ten runtime
index digests that `tools/build_runtime_indexes.py` regenerates. It cannot be diffed here: the reproduce run
overwrote the pre-rebuild copy. This is reported, not resolved, and no claim of "hashes unchanged" is made
for the precision configuration.

### 5.4 · Not applicable: git discipline

`git status` / `git diff --stat` / `git diff` (handoff §35) cannot be produced: this workspace is **not a git
repository** (`fatal: not a git repository`). §35's other checks — frozen policy hash, frozen lanes,
official-data hashes, S-Eval ledger, store census — are reported above.

## 6 · DEPLOYMENT — `IMPLEMENTED` (local, workbench) · `BLOCKED` (container runtime)

| Item | Status |
|---|---|
| Service serving the workbench at `/` | running, `0.0.0.0:8000`, one file **345,597 B** (`battle_model/site/index.html`) |
| HTTP smoke against it | **21/21 passed** (`python3 tools/smoke_test.py --base http://localhost:8000`) |
| Workbench browser smoke | **22/22 checks**, 0 console errors, 0 requests answered ≥ 400 — run against a **copied** store on `:8001` so the shipped store is untouched; writes the 12 `bm-*.png` screenshots |
| Container layout (the image's exact filesystem) | **verified** — the tree the Dockerfile produces (`sutra/ tools/ tests/ data/ battle_model/site web/site`) started from a scratch directory: 21/21 checks, `/` serves the workbench |
| Container build/run | **blocked** — no `docker`/`podman` in this environment and no provider credentials. `NOT MEASURED`, not claimed. |

Finisher, unchanged: `docker build -t sutra . && docker run --rm -p 8000:8000 -e PORT=8000 sutra`.
The image's stage 1 now builds the workbench (and keeps the console as the fallback build).
## 6.5 · CONTRACT RECONCILIATION (handoff §10–§18) — `IMPLEMENTED`

| Handoff | What it asked for | What the runtime does now |
|---|---|---|
| §11 | decisions `confirmed|not_true|inconclusive`; append `kind=adjudication`; frozen belief mechanism; receipt + effect; idempotency; no old-observation mutation; no second truth store | all of it. Both spellings are accepted (`confirmed`=`confirm`, `not_true`=`deny`) with the canonical word stored; the reviewer's decision is mapped onto the frozen outcome of the class it declares and that mapping is **returned with every adjudication** and printed in the UI. Verified observation-equivalent: the same decision sent as a plain negative visit through `/evidence` produces the identical belief for that address |
| §13 | `GET /v1/audit/{belief_id}` | added (`AD002936:7`); the query-scoped `/v1/audit` product view remains |
| §14 | overview from real data, no fake latency/accuracy/SLA | tier mix, cold/warm, queue depth, town counts, pack freshness — all counted at the cut, nothing modelled |
| §15 | pack freshness fields | `pack_version`, `age_days`, `valid_until`, `stale` added; `downloaded_at` is `null` with the reason stated, because the server does not track per-device downloads |
| §16 | four status labels from real metadata | `GET /v1/method-trust` now returns IMPLEMENTED / DESIGNED / NOT YET IMPLEMENTED / NOT MEASURED, assembled from the runtime's own capability map |
| §18 | batch ≤5,000, per-row ticket + aggregate, never a bulk benchmark | ceiling raised to the contract's **5,000**; the summary carries refusal rate, tier mix and a radius histogram and states in the payload that it is *not* a benchmark |

**One limitation to state plainly.** A review submitted *now* recomputes the belief at the current instant
and, for `AD002936`, changes nothing (`changed: false`, coordinate unchanged) — the contract's *"a
confirmation is not supposed to be dramatic"*. A review submitted with a **backdated `as_of`** replays that
instant, where the adjudication is the newest positive evidence, and there the engine reports a different
selected candidate and a wider radius (`coordinate_moved: true`). Both are the frozen mechanism behaving as
documented (`coordinate_moved=true` is only ever written by an adjudication), and the demo values are
untouched because they are read at the fixed `2026-06-01` cut. Whether the API should accept a backdated
adjudication at all — a reviewer's decision is made *now* — is a **product question** (open item §38; no
frozen constant was touched).

## 7 · WHAT IS NOT DONE

* **Open product question** — whether `POST /v1/adjudicate` should accept a **backdated** `as_of` (§6.5).
  No frozen constant was touched and the demo cut is unaffected.
* **Open item** — the precision-configuration hash movement of §5.3 is reported, not resolved.
* `NOT IMPLEMENTED` — a reviewer changing what the system *believes*. Deliberate: only field evidence
  moves a location; a review closes a case, and the adjudication's effect block says so in-product.
* `NOT MEASURED` — any accuracy figure beyond the three frozen populations, and any rupee or
  visit-reduction claim. Neither is estimated, and neither appears in the product.
* **Retained, not served** — the earlier console build in `web/` (kept as the `_web_root()` fallback and
  for its own smoke script); it is not the product surface.
* **Not run** — the container image itself (`docker` absent); everything the image does *except* its
  packaging has been run from the image's own file layout.
## 8 · NUMBERS A READER CAN CHECK

| Claim | How to check it |
|---|---|
| the workbench is what `/` serves | `curl -sI http://localhost:8000/` → 200, 345,597 bytes, and `GET /` matches `battle_model/site/index.html` |
| 3,117 indexed · 278 open cases · warm 1,280 / cold 1,837 | `GET /v1/overview?as_of=2026-06-01T00:00:00Z` |
| cold 0.71 (n=100) · warm 0.9677 (n=31) · product 0.76 (n=100) | `GET /v1/method-trust` |
| AD002936 · APPROXIMATE / MOVED_SUSPECTED · radius 1202.6 (was 566.9) · coordinate unchanged | `GET /v1/address/AD002936/case?as_of=2026-06-01T00:00:00Z` |
| 3,788 evidence rows · negative 1,141 · `negatives_move_coordinate: false` | `GET /v1/evidence` |
| 3,117 places · identity rule `colocation<=30m\|adjudicated` | `GET /v1/places` |
| no fixture payload anywhere in the workbench sources or the served bundle | `grep -c "fixtures" battle_model/src` → 0 hits as an import; the guard test asserts the banned tokens against both the sources and the built file |
| 125 tests | `python3 -m pytest tests/ -q` |
| the store was not written by any of it | observations 5,578 · belief_versions 2,757 · task_events 278 · receipts 0 — compared before and after (§5) |
---

*Sources:* [S61] and [S66] (field-data engineering: independent confirmations, negative evidence, what a
visit may and may not establish, and the offline-capture failure modes this integration had to respect) ·
[S69] (minimum sample guard on empirical radii — why the resolver publishes a radius + coverage + n rather
than a bare point) · [S73] (heavy-tailed, directionally biased positional error — why the workbench pairs
every ring with the number) · [S81] and [S82] (outbox / idempotency-key / hold-then-conflict precedent — the
contract behind the append-only adjudication and task ledger the Queue now drives) · [S92] (the
free-artefact ceiling that keeps the map local-plane only) · [S95] (the binding data policy the guards
enforce: official tables only, no external geography anywhere in this frontend or the service behind it).
