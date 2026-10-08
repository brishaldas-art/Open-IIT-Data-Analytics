# SUTRA — IMPLEMENTATION PHASE REPORT (2026-10-07)

**Scope.** P0–P13 of the implementation brief, built strictly against
`PS3_IMPLEMENTATION_CONTRACTS_2026-10-07.md` (normative on any conflict). The architecture was not
reopened and no architecture document was added. Four learned ranking challengers were **fitted in
memory** under the declared SplitSpec against the 292-address promotion pool of Experiment D — and all
four were rejected by the pre-registered gate, so **the rule ranker remains the product** and **no model
artefact exists anywhere in the workspace** (`tools/check_workspace.py` asserts it). That is a
pre-registered outcome (contract §2 rule 3), not a failure.

**Reproduce everything with one command:**

```bash
cd PS3_SUTRA && bash tools/reproduce.sh full      # 15 steps: manifest → audit → cleaning → store → indexes →
                                                  # firewall → candidates → T1–T16 → A → B → C → D → precision → demo
```

**Executed end-to-end on 2026-10-07: 15/15 steps, exit 0, 7 m 4 s.** The fifteenth step is the
precision-optimisation pass (§3.8). Every number in this report comes
from that run. The chain **fails closed**: the three guards at its end (`check_leakage` · `check_links` ·
`check_workspace`) are no longer wrapped in `|| true`, and all three report green.

---

## 1. What was built

| Step | Deliverable | Status |
|---|---|---|
| P0 | pre-contract artefacts marked `SUPERSEDED_PRE_CONTRACT` and moved to `data/derived/superseded_pre_contract_2026-10-07/` | ✅ |
| P1 | supervision firewall + manifest + split receipt (145 excluded addresses, 4.7%) | ✅ |
| P2 | candidate generation rewritten to the eight contract arms, `licence_class = "official"` throughout | ✅ |
| P3 | precomputed runtime indexes (9 JSON + hash manifest, deterministic rebuild) | ✅ |
| P4 | one as-of query gate (`sutra/asof.py`), enforced by a code-level invariant test | ✅ |
| P5 | the runtime package `sutra/` (26 modules) + `sutra/learning.py` (the D challenger library, off the request path) + the contract's 7 frozen entry points | ✅ |
| P6 | Observation → Evidence → Belief → Place state → Projection, byte-deterministic | ✅ |
| P7 | rule-based evidence engine: weight + reason codes, no binary trust flag | ✅ |
| P8 | radius payload with stratum fallback + n-guard; pincode withheld; `nominal` never faked | ✅ |
| P9 | `request_purpose` / `address_purpose` / `eligibility` separated; deterministic landmark cues | ✅ |
| P10 | contract tests T1–T16 + 10 invariant tests (**26 in one suite**), green | ✅ |
| P11 | offline MVP: pack → airplane mode → capture → durable outbox → replay | ✅ |
| P12 | ladder: **A complete** (the floor reproduced exactly) · **B complete** (preprocessing ablation, verdict: keep production) · **C complete** (retrieval-only ceiling) · **D complete** (retrieval + ranking, verdict: **rule priority retained**) | ✅ |
| P13 | six-scene demonstrator (`data/derived/demo_transcript.md`) | ✅ |

### 1.1 Files created (workspace-relative)

**Runtime (26 modules + the D-only challenger library, importable offline):** `sutra/__init__.py` · `sutra/version.py` · `sutra/config.py` ·
`sutra/geo.py` · `sutra/asof.py` · `sutra/store.py` · `sutra/dataio.py` · `sutra/indexes.py` · `sutra/evidence.py` ·
`sutra/candidates.py` · `sutra/preprocess.py` · `sutra/stats.py` · `sutra/ranking.py` · `sutra/belief.py` ·
`sutra/memory.py` · `sutra/uncertainty.py` · `sutra/purpose.py` · `sutra/directions.py` ·
`sutra/eligibility.py` · `sutra/resolve.py` · `sutra/splits.py` · `sutra/packs.py` · `sutra/offline.py` ·
`sutra/replay.py` · `sutra/seed.py` · `sutra/api.py` · **`sutra/learning.py`** (learned-ranking challengers; imported by `tools/experiment_d.py` only, never by a request-path module — a standing leakage guard asserts it)

**Tools:** `tools/build_store.py` · `build_runtime_indexes.py` · `build_supervision.py` ·
`build_candidates.py` (rewritten) · `run_acceptance_tests.py` · `experiment_a.py` · `experiment_b.py` ·
`experiment_c.py` · `experiment_d.py` · `precision_opt.py` · `demo_walkthrough.py` · `serve_runtime.py` · `reproduce.sh` (rewritten: 15 steps, fails closed) ·
`check_leakage.py` · `check_workspace.py` · `check_links.py`.

**Tests:** `tests/test_acceptance.py` (T1–T16 + 10 invariants).

**Artefacts (`data/derived/`):** `supervision_firewall.csv` · `supervision_manifest.csv` ·
`split_receipt.json` · `candidates_v2.csv` + receipt · `features_coldstart_v2.csv` + receipt ·
`features_warm_v2.csv` + receipt · `labels_eval_v2.csv` · `runtime_indexes/` (9 JSON + `data/derived/runtime_indexes/manifest.json`) ·
`runtime/sutra_store.sqlite` · `packs/` · `acceptance_report.json` · `experiment_A_report.json` ·
`experiment_b_results.csv` · `experiment_b_receipt.json` · **`experiment_b_report.md`** ·
`experiment_c_results.csv` · `experiment_c_receipt.json` · **`experiment_c_report.md`** ·
`experiment_d_results.csv` · `experiment_d_receipt.json` · **`experiment_d_report.md`** ·
`demo_transcript.md`.

### 1.2 Files superseded (kept, never deleted)

`data/derived/superseded_pre_contract_2026-10-07/` holds
`data/derived/superseded_pre_contract_2026-10-07/candidates_coldstart.csv` ·
`data/derived/superseded_pre_contract_2026-10-07/candidates_warm.csv` ·
`data/derived/superseded_pre_contract_2026-10-07/features_coldstart.csv` (+receipt) ·
`data/derived/superseded_pre_contract_2026-10-07/features_warm.csv` (+receipt) ·
`data/derived/superseded_pre_contract_2026-10-07/labels_eval.csv`, with a README
stating the three defects (non-contract arm names, prohibited licence classes, no as-of semantics) and
what replaced each. **Nothing was deleted and the official raw data was never touched** (hash-verified
by `tools/check_workspace.py` and the manifest step of the chain). No active module reads the
superseded directory, and a leakage check asserts it.

---

## 2. Runtime modules (what each one owns)

| Module | Owns | Notable rules |
|---|---|---|
| `sutra/asof.py` | the **only** temporal predicate (`observed_at < as_of`) | `is_before`, `rows_upto`, `candidates_upto`; a code-scanning test fails the build on any other comparison |
| `sutra/store.py` | the append-only store; **no UPDATE/DELETE** in the module | idempotent `submit_observation` under one writer lock; canonical JSON + sha256 per payload; beliefs refuse to persist if a re-derivation differs; belief rows are scoped by rule set, so a rule change is a migration, never a violation; **one connection per thread** (WAL) so the threaded API is served off one store |
| `sutra/dataio.py` | **one** text normaliser for the whole system | `norm_text`/`tokens`/`edit_ratio`; imported by the cleaner *and* the ranker — a second copy is a defect, and a test asserts the cleaned table's md5 is unchanged by the move |
| `sutra/evidence.py` | weight + reason codes + the independence tuple | dwell · GPS · trail agreement · duplicate media · timing · collector baseline · recency; negatives are 0.00 with `polarity=negative` and no coordinate path |
| `sutra/candidates.py` | the eight arms | `as_of_valid` iff evidence-backed; landmark plausibility filter; agreement annotation; C2-gated neighbour arm that refuses to run; `ring=` selects text primitives (Experiment B) and nothing else |
| `sutra/preprocess.py` | the four preprocessing rungs B1–B4 | B2 **is** production; B1/B2 are stateless, B3/B4 fit a text model at index time; the arm set, record shape, licence class and as-of rules are identical under every ring (asserted by an invariant test) |
| `sutra/stats.py` | grouped/paired grouped bootstrap intervals | the interval machinery behind Experiment B's selection rule; validated by T16 (bracketing, group-inflation, seed determinism, zero-width on identical series) |
| `sutra/ranking.py` | frozen `rank(...)` interface, rule baseline | ≤15 features, additive inspectable score, every contribution a reason code; **byte-unchanged by Experiment D** |
| `sutra/learning.py` | the four D challengers (logistic · LambdaMart · pairwise · shuffled control) | fits **in memory only**, writes no artefact, imports numpy/sklearn only; monotone-constrained with a per-tree structural check; **no request-path module may import it** (leakage guard), so the production ranker cannot depend on research code |
| `sutra/belief.py` | tier/status/support, the primary coordinate | promotion needs F2.2; negatives cap the tier; contested keeps both supports; version = 1 + observations |
| `sutra/memory.py` | place identity + tasks | members from the place-block ledger; merges/splits are events; verify-first tasks idempotent |
| `sutra/uncertainty.py` | the radius payload | n<15 → parent fallback; `nominal` null; three widening triggers named |
| `sutra/purpose.py` / `sutra/eligibility.py` / `sutra/directions.py` | P1–P5 purpose rules; the SERVE/VERIFY_FIRST/REFUSE gate; landmark cues | single observation never decides; `UNKNOWN` is a success state; no cue rather than a guessed cue |
| `sutra/replay.py` | `candidate_metrics` + `replay` | refuses to run without a declared `SplitSpec` (T15); the only metrics producer |
| `sutra/packs.py` / `sutra/offline.py` | versioned pack + device outbox | no evidence, no truth, no polygons in a pack; the outbox is append-only too |
| `sutra/api.py` | the §11 HTTP surface (stdlib, `ThreadingHTTPServer`) | `/resolve`, `/evidence`, `/place/{id}`, `/tasks/verify-first`, `/packs/{town_id}`, `/health`; backlog raised for device bursts; keep-alive with explicit `Content-Length` |

---

## 3. Acceptance results — item 4 (tests implemented) and item 5 (all results)

`python3 tools/run_acceptance_tests.py` → **26 passed · 0 failed · 0 skipped** (12.1 s).
Tests T1–T15 are the contract's; T16 and the ten invariants are the ones this build added on top.

| # | Test | Result | Evidence |
|---|---|---|---|
| T1 | no candidate → no coordinate | ✅ | unmatched text and the 237 `OUT` records both return `candidate=null`, no x/y anywhere, VERIFY_FIRST/REFUSE |
| T2 | one negative → coordinate unchanged | ✅ | candidate bytes identical; radius 539.9 → 566.9 m; counter 0 → 1 |
| T3 | ≥2 independent negatives → doubt out loud | ✅ | status `MOVED_SUSPECTED`, tier capped APPROXIMATE, verify-first task raised, coordinate unchanged |
| T4 | fake independence rejected | ✅ | one collector, one day, one photo hash → stays WARM, `media_ok=false` |
| T5 | valid confirmations promote | ✅ | two collectors, distinct media, 9 days apart → CONFIRMED, primary = field median (spread 2.2 m) |
| T6 | pincode radius withheld | ✅ | `source_stratum=locality`, `nominal=null`, `basis=empirical_p80`, `n_calibration=24` |
| T7 | deterministic belief | ✅ | re-derivation byte-identical; the store raises `DeterminismViolation` on a tampered payload |
| T8 | duplicate observation idempotent | ✅ | one stored row, one evidence row, original receipt returned |
| T9 | offline capture → outbox → replay | ✅ | 2 captured offline, server untouched, drained in `local_seq` order, belief recomputed server-side |
| T10 | WORK_LIKE refused for a notice | ✅ | `REFUSE / purpose_work_like`, decision logged with its rule version |
| T11 | no resolvable landmark → `null` | ✅ | address still resolves; `directions=null` |
| T12 | no external data, zero outbound calls | ✅ | sockets monkeypatched for the whole benchmark/demo path; tree scan clean |
| T13 | feature-matrix audit | ✅ | 15 features, no shared-table column, only `address_text`-derived text inputs |
| T14 | S-Eval firewall | ✅ | 145 excluded, none in any supervision set, test-look counter reported |
| T15 | undeclared split aborts | ✅ | `None`, a made-up spec and a wrong protocol version all raise `UndeclaredSplit` |
| **T16** | **residue matcher is live (positive control)** | ✅ | a typo'd locality with no in-text pincode (`kuvempu layot`) is recovered as `T1-L03` "Kuvempu Layout" by B3 (score 0.5061, margin 37.5) and B4 (0.375, idf 1.0) with an inspectable reason; B2 carries no residue matcher at all |
| I1 | as-of is the single gate | ✅ | code-level scan: no timestamp comparison outside `sutra/asof.py` (+ the marked SQL backend) |
| I2 | store append-only | ✅ | no `UPDATE`/`DELETE` anywhere in `sutra/store.py` |
| I3 | candidate vocabulary, no truth | ✅ | arms ⊆ contract arms, `licence_class=official`, no pre-contract vocabulary |
| I4 | labels evaluation-only | ✅ | `labels_eval_v2.csv` is S-EVAL only, no label column in a feature file |
| I5 | pack has no truth/evidence/polygons | ✅ | verified on the built pack |
| I6 | no unmeasured nominal radius | ✅ | every stratum reports `empirical_p80`, `nominal=null` |
| I7 | no vendor call in the runtime | ✅ | no `requests`/`urllib`/`http.client`/raw socket in the package |
| I8 | supervision manifest shape | ✅ | every required column present on every row |
| I9 | a typed address reaches the index | ✅ | the runtime's normaliser reproduces `text_norm` row-for-row; an exact paste resolves to its own record; a near miss returns a labelled area context with **no** coordinate |
| **I10** | **a ring may change only how text is read** | ✅ | B2/B3/B4 return byte-identical candidate universes to the production default on a sampled set (the residue matcher declines everywhere on this corpus) while B1 differs on the same sample — so the check is not vacuous |

**Interval machinery, validated rather than assumed** (T16 also exercises `sutra/stats.py` directly,
because Experiment B's selection rule rests on it): a grouped CI brackets the mean and is close to the
analytic i.i.d. interval when groups are independent; under strong intra-group correlation the grouped
interval is ~3× wider than the naive ungrouped one (which is the point of resampling by place block);
the same seed reproduces the same interval exactly; a paired comparison of an identical series has
zero width and is reported *not resolved*.

### 3.1 Candidate-schema validation (`data/derived/candidates_v2.csv`) — item 6

12,021 candidates · 2,880 addresses · `sha256 4d06c7da9f2c83feb247ce40f747bafd72016d8520de169892e249f1611e50a5`
(unchanged across every rebuild in this phase, including the two Experiment B reruns) · licence classes
= `{official}` · no truth column · `as_of_valid` present iff arm ∈ {field_evidence, memory,
place_neighbour}.

| arm | candidates | as_of_valid |
|---|---|---|
| frozen_baseline | 2,880 | none (static) |
| town_centroid | 2,880 | none |
| locality_centroid | 2,863 | none |
| official_landmark | 604 | none (after the nuisance-name and 1,000 m plausibility filters) |
| address_book | 10 | none |
| field_evidence | 1,504 | all (the contributing observation's own instant) |
| memory | 1,280 | all (the prior belief's instant) |
| place_neighbour | 0 | **disabled until C2** |

Feature matrices: `features_coldstart_v2.csv` 9,234 rows (static arms only — every `as_of_valid` is
empty), `features_warm_v2.csv` 12,021 rows, `labels_eval_v2.csv` 424 rows over the 100 surveyed
addresses, `label_source = surveyed_ground_truth`, `split = S-EVAL` only.

### 3.2 S-Eval firewall validation — item 7

`S-Eval = 100` surveyed addresses · firewall `= 145` addresses `= 100 ∪ 100 accounts (128 addrs) ∪
99 blocks (117 addrs) = 4.7% of 3,117` · supervision pool 2,972, of which **292 carry
promotion-grade confirmations** → `S-TRAIN 223 · S-VAL 69` (nested grouped CV: outer = place block,
inner = account) · 2,680 pool addresses with no promotion-grade confirmation yet · **zero** firewalled
addresses in any supervision set. `tools/build_supervision.py` writes `supervision_firewall.csv`,
`supervision_manifest.csv` (3,117 rows, one per address, with split, as-of, source observation ids and
the exclusion reason) and `split_receipt.json` (sha `228680109f0c…`). The thin pool is why **no
learned ranker ships** (contract §2 rule 3).

**S-Eval reads are counted, not assumed.** Every read appends to `counter_events` in the store with its
caller. In the clean chain of 2026-10-07 the counter ends at **6**, and the six rows name themselves:
`build_candidates:labels_eval_v2` (constructing the evaluation-only label file), `experiment_A` ×3
populations, `experiment_B:s_eval_locked_check (single read)` and
`experiment_C:s_eval_locked_check (single read)`. Earlier in the phase the counter reached 18–20 because
incremental reruns share one store without a reset; the reproducible number is the chain's **6**, and it
is the one quoted in the artefacts.

### 3.3 Runtime latency (`resolve`, full path incl. gate logging) — item 8

p50 **11.6 ms** · p95 **24.9 ms** · p99 **33.8 ms** · max 45.3 ms over 400 addresses, n=400, on a copy
of the runtime store — target **p95 < 250 ms → MET**, ~10× margin. Through the live HTTP server:
96 concurrent `/resolve` requests, all HTTP 200, ~4.8 ms mean per request, zero errors, one distinct
answer (determinism holds under concurrency).

### 3.4 Experiment A — the floor (ladder step 1)

| population | n | top-1 median | <100 m | <500 m |
|---|---|---|---|---|
| all 100 surveyed | 100 | **376.4 m** | 9.0% | 71.0% |
| validation+test | 34 | 326.1 m | 8.8% | 70.6% |
| leave-block-out | 31 | 329.9 m | 9.7% | 67.7% |

The pre-contract pipeline measured 376.4 m / 9.0% / 71.0% / coverage 92.4% `[S91]`; the new runtime
**reproduces the median, the hit-rates and the 92.4% corpus coverage exactly** through an independent
code path (`regression_check.matches = True`). The report records its own `S_EVAL_BASELINE` SplitSpec,
which is the only lawful path to these rows.

### 3.5 Experiment B — preprocessing ablation (ladder step 2; full report in `data/derived/experiment_b_report.md`)

**Question.** Do increasingly sophisticated *deterministic* text primitives and a residue matcher
improve candidate retrieval enough to justify their complexity? Four rungs: **B1** raw text · **B2**
production (NFKC + abbreviation table + deterministic spans) · **B3** = B2 + TF-IDF/SVD residue ·
**B4** = B3 + parser/statistics residue. Nothing is trained; no external data or API is used; only the
ring varies — the arms, the record shape, the as-of discipline and the radius map are held fixed.

Scored lane = **static arms only**: the proxy label is the address's own promoted check-in median, so
the `field_evidence` / `memory` arms would reproduce it by construction (oracle median 0.0 m, 88.4%
< 100 m — the signature of circularity, reported as an interference check instead).

| finding | result |
|---|---|
| static-lane quality on S-VAL | **identical across all four rungs** — coverage 1.000, recall@1/3/5 = 0.203 / 0.551 / 0.870, oracle median 238.0 m; every paired delta exactly 0 |
| candidate universes | B2 = B3 = B4 **byte-identical** (`eeba49f8672c…`); B1 differs (`e154312bba1d…`) |
| residue matcher | 31 landmark + 1 locality call per ring, **zero acceptances** — every near-match is ambiguous in a gazetteer that repeats names inside a town ("Ganesh Temple" ×7, "Ration Shop" ×9), so the margin rule refuses; proven live by the T16 positive control |
| latency (ms/address) | B1 **0.84** · B2 **2.89** · B3 **3.62** · B4 **13.82** |
| identification guardrail (corpus-wide, label-free) | long-form spelling of an official abbreviation must reach the same record: **B1 0.486** overall and **0.000** on the 1,602 texts carrying an abbreviation, vs **B2 = B3 = B4 = 1.000** |
| arm level (the only place preprocessing can act) | `official_landmark` fires on 15.9% of labelled addresses under B1 vs 24.6% under B2 (delta −0.0856 [−0.1191, −0.0550], resolved) — and B2's extra firings are **coarse** (B2-only n=25, median 1,202 m, 28% within 500 m); `locality_centroid` fires everywhere under both |
| S-Eval read | once, through the declared spec; it decides nothing |

**Verdict: keep B2, change nothing.** Eligible rungs `['B2','B3','B4']`; B1 is the only rung routed out,
on the identification guardrail alone (−0.514 [−0.532, −0.4963]) — it is statistically competitive on
every *retrieval* metric and cheaper, but it loses the abbreviation equivalence entirely ("Ngr" and
"Nagar" become different strings for the same place), so it stays the ablation's control rather than the
product. B3/B4 are rejected because they buy nothing measurable on this corpus at 1.25× / 4.78× the
per-address cost — *which is the empirical form of "no LLMs and no embeddings everywhere"*. The
selection rule is declared in advance and applied symmetrically: a rung is eligible only if it is not
resolved worse than any other rung on any guardrail; among eligible rungs the cheapest wins; latency
needs a materiality margin (5% of the 250 ms budget = 12.5 ms) because two rungs sharing one machine
will always differ by microseconds, while error/hit metrics are exact given a candidate set.

---

## 3.6 Experiment C — the retrieval-only ceiling (ladder step 3; full report in `data/derived/experiment_c_report.md`)

**Question.** How good is the candidate-retrieval layer **by itself, before ranking**? C scores only the
candidate sets (`tools/experiment_c.py`, 165 s, exit 0; the chain re-runs it as step 13) and lets no ranker decide anything: the four
things a single accuracy number usually conflates are reported separately — *retrieval coverage*,
*retrieval recall*, the *oracle ceiling* (what a perfect ranker could reach) and the *ranked answer*
(the rule top-1, printed as Experiment D's territory only).

**Primary lens (LENS A): the five static arms, in the registry's own order**, cumulatively
(`frozen_baseline → locality_centroid → town_centroid → official_landmark → address_book`), over the
full book, S-TRAIN+S-VAL, S-VAL, leave-block-out and the locked S-Eval check. The evidence arms
(`field_evidence`, `memory`) are **LENS B**, reported as a diagnostic only, because they consume the
visit history and exist for a minority of surveyed addresses.

| | baseline pin only | + locality | + town | + landmark | + address book (static lane) |
|---|---|---|---|---|---|
| S-Eval oracle median | 376.4 m | 332.7 m | 332.7 m | **306.2 m** | 306.2 m |
| S-Eval oracle <100 m / <500 m | 0.09 / 0.71 | 0.10 / 0.79 | 0.10 / 0.79 | 0.13 / 0.79 | 0.13 / 0.79 |
| S-Val oracle median | 249.0 m | 238.0 m | 238.0 m | 238.0 m | 238.0 m |
| S-Val oracle <500 m | 0.8406 | 0.8696 | 0.8696 | 0.8696 | 0.8696 |
| candidates / address | 1.00 | 1.99 | 2.99 | 3.21 | 3.21 |

* **The ladder is flat above the locality arm.** Adding the town centroid, the landmark arm and the
  address book produces an **identical per-address oracle series** on the locked check — no complexity
  without a measured improvement (rule D applied to C's own result).
* **The frozen pin is load-bearing.** Removing it costs **+156.967 m** of oracle median on S-Eval
  (paired interval [+48.007, +306.484], entirely above zero) and +165.0 m on S-VAL.
* **The locality arm earns a small, honestly-bounded place.** It adds **+0.0800** of the <500 m hit-rate
  on the locked check ([+0.0298, +0.1393], resolved) but is **not resolved** on the selection population
  (+0.0290 [0.0000, 0.0725]) — both are reported, and C adopts nothing.
* **Prefix recall** (a declared second view of the same hit criterion, over the deterministic retrieval
  order `generate` returns): S-Eval **@1 0.71 · @3 0.79 · @5 0.79 · @10 0.79** (hit@500 m; at 100 m
  @1 0.09 → @10 0.13). S-VAL @1 0.8406 → @3 0.8696. The entire gain of the later arms is a *depth*
  effect, not a set effect.
* **Coverage, whole book (3,117, label-free):** static lane **0.924**, unresolved **0.076** (the 237
  `OUT` addresses), candidates/address min 0 · median 3 · mean 2.963 · p90 4 · max 5. Per arm:
  pin 2,880 (92.4%) · locality 2,863 (91.9%) · town 2,880 · landmark 528 addresses/604 candidates ·
  address book 10 · field_evidence 751/1,504 · memory 1,280 · **place_neighbour 0**.
* **Where it fails:** 21 of 100 locked-check addresses have no candidate within 500 m; they concentrate
  in the coarse strata (pincode n=10, <500 m 0.20, below the n-guard) while street (n=16) is 1.00.
  Of those 21, **11 have visit history and 6 are pulled inside 500 m by the evidence lane** — the
  measured case for prioritising F/L/O, not a new retrieval mechanism.
* **Negative controls, all reused:** a count-matched **random-candidate control** (the placebo recipe of
  `tools/neighbour_index_probe.py`) scores 1,777.6 m median against the static lane's 306.2 m — paired
  Δ **−1261.1 m [−1591.2, −1138.9]**, resolved, i.e. the arms carry real information rather than "more
  points near the anchor"; the **truth-echo scan** finds **0 of 424** candidates within 1 m of a surveyed
  coordinate; a runtime guard proves **0 reads** of `surveyed_addresses.csv` while generating all 3,117
  addresses (static scan: the only mention is the index manifest recording its hash as provenance);
  0 S-Eval firewall violations out of 145 firewalled addresses; 0 socket attempts; licence classes
  `[official]`; the external-data holding area stays empty.
* **Cost:** **1.85 ms/address** for retrieval alone (p50 1.0 · p95 4.0 · max 7.8); the full `resolve`
  path from the acceptance suite is p50 10.4 / p95 21.0 ms against the 250 ms budget.
* **Cross-experiment determinism:** C's candidate universe restricted to Experiment B's address set
  hashes to `eeba49f8672c…` — **the same hash Experiment B recorded for the production ring** — and the
  full-book universe hashes to `41e5de3c71db…`, so C provably generated the same candidates through the
  same path.

**Verdict (declared rule, applied to the numbers):** the ceiling is **adequate** — the static lane loses
no coverage against the pin, beats a count-matched random control by 1,293.9 m (resolved, selection
population) and at least one admitted arm earns its place — so **retrieval is not the dominant
bottleneck**; what remains is the *granularity of the supplied official data* plus the *absence of
history* on 55% of surveyed addresses, which is F/L/O territory. **C2 stays locked**: the declared gate
required a majority of covered addresses to have no candidate inside the locality-radius scale
(500 m); the measured figure is 0.79 within it, so there is no majority gap for a neighbour mechanism to
fill, and the production candidate set is untouched. **Next experiment: D** (retrieval + ranking) — now run,
see §3.7.

**One shared-function repair, proven inert.** Scoring a lane whose coverage varies required
`tools/experiment_b.metrics_for`'s oracle block to skip rows the lane does not cover (it assumed full
coverage and would divide by zero otherwise). The fix was verified numerically inert for Experiment B by
running B with and without it: the per-address CSV is **identical** once the wall-clock latency column is
removed, and the receipt is **identical** once its wall-clock fields are masked — same verdict
(`winner=B2 · change none`), same eligibility, same every number.

---

## 3.7 Experiment D — retrieval + ranking (ladder step 4; full report in `data/derived/experiment_d_report.md`)

**Question, exactly.** *Given the existing official candidate set, can an inspectable learned ranker order
the candidates better than the current deterministic rule-priority ranker?* Candidate generation is frozen
(C measured its ceiling), so D may only **reorder**. The two numbers are kept apart on purpose: `oracle` is
C's ceiling and is never used as a ranker metric here; top-1 and nDCG@5 are D's.

**Arms compared (exactly four, as briefed).** `RULE` (production `sutra.ranking.rank`, in every table) ·
`LOGISTIC` (L2 logistic on binary relevance ≤500 m) · `LAMBDAMART` (gradient-boosted trees, listwise
NDCG-weighted LambdaRank gradients) · `PAIRWISE` (same trees, RankNet pairwise-logistic gradients).
lightgbm/xgboost are absent from this environment and **no external package was fetched** (zero outbound
calls, asserted): the GBDT is implemented in-repo in `sutra/learning.py`, monotone-constrained on the
pre-registered similarities/granularity/distance trio and verified per tree by a structural check. Fits
happen in memory only; no model file is written, and no request-path module imports the library.

**Primary lane = static/cold** (the five arms that read no visit). The evidence/memory arms are the
**warm lane**, reported as a *circular diagnostic* only: the proxy label is the address's own promoted
check-in median, so a model on those arms reproduces its own label (S-VAL P@1 0.9855, median 24.8 m). The
frozen 15-feature matrix contains no memory-specific feature, and the report says so instead of presenting
a "memory ablation" that does not exist.

**Data (disclosed, not fought).** 292 labelled addresses / 944 candidate rows / 680 differing-grade pairs
/ 409 positives; 3.23 candidates per address; 276 place blocks / 290 accounts; grade mix 54 at ≤100 m ·
153 at ≤250 m · 202 at ≤500 m · 535 beyond. Outer grouping = place block, inner = account; every pool
block sits wholly inside one fold. Hyperparameters are exactly the pre-registered set (n_estimators ≤300 —
the models stop after 1–11 trees on the grouped S-VAL early-stopping signal — max_depth ≤4, lr 0.05,
subsample 0.8, L2 leaf 1.0, min_data_in_leaf 10).

| model | S-VAL P@1 | <100 m | <250 m | <500 m | median err | nDCG@5 | S-EVAL P@1 | S-EVAL median | verdict |
|---|---|---|---|---|---|---|---|---|---|
| **RULE (shipped)** | **0.8406** | 0.1594 | 0.5072 | 0.8406 | **249.0 m** | **0.9670** | **0.71** | **376.4 m** | **retained** |
| PIN_ONLY | 0.8406 | 0.1594 | 0.5072 | 0.8406 | 249.0 m | 0.9622 | 0.71 | 376.4 m | control |
| LOGISTIC | 0.8116 | 0.1739 | 0.4928 | 0.8116 | 258.0 m | 0.9516 | 0.73 | 371.6 m | rejected |
| LAMBDAMART | 0.8406 | 0.1594 | 0.5072 | 0.8406 | 249.0 m | 0.9640 | 0.72 | 371.6 m | rejected |
| PAIRWISE | 0.8406 | 0.1594 | 0.5072 | 0.8406 | 249.0 m | 0.9653 | 0.72 | 371.6 m | rejected |
| LAMBDAMART_SHUFFLED | 0.5652 | 0.1014 | 0.3188 | 0.5652 | 398.3 m | 0.8090 | — | — | leakage control |

**Paired, grouped-bootstrap, 95%, 10,000 resamples, block groups, seed 7 — both directions tested.** On
S-VAL no challenger beats RULE on the primary metric: LAMBDAMART and PAIRWISE produce **identical top-1
series** (delta exactly 0.0000 at every k), LOGISTIC is a point *worse* on <500 m (−0.0290
[−0.0725, 0.0000], not resolved) and fails the monotone structural check. In the other direction the rule
is **resolved better** than LAMBDAMART and than PIN_ONLY on nDCG@5 (−0.0029 [−0.0057, −0.0008] and
−0.0048 [−0.0090, −0.0015]); that verdict was invisible until a one-sided-test labelling defect was fixed
(see below). Out-of-fold — the unbiased lens, 5 spatial folds, inner account-grouped early stopping —
LAMBDAMART and PAIRWISE each gain **+0.0103 [+0.0000, +0.0238] <500 m (not resolved)** at *identical*
median error (257.5 / 258.2 m). Leave-block-out agrees with S-VAL in direction and is not resolved.

**Why the models do not generalise — measured, not asserted.** They fit: in-sample the trees reach P@1
0.8475 with the early-stopping signal already optimal at **tree 1**, and on S-TRAIN the learned models
*are* marginally better than RULE (0.8475 vs 0.8386). Out-of-fold that advantage evaporates. The headroom
decomposition explains it: on S-VAL the rule's top-1 **is already the best candidate available on 75.4%**
of addresses (52/69); a strictly better candidate exists for 17 addresses, and the median gain waiting
there is 138 m. A *perfect* ranker, which does not exist, could reach 0.2029 at <100 m and 0.8696 at
<500 m — the entire reordering headroom is **+0.04 / +0.03**. D's honest answer to its own question is
therefore: **no**, and the reason is that ranking is not where the remaining error lives; the static
candidate set is (Experiment C), and the warm lane's 24.8 m median shows where warmth would take it.

**Locked S-Eval read (one read per run, after the freeze).** Frozen before the read: features (the frozen
15), arms, ring B2, training population, hyperparameters, monotone set, label definition
(`frozen_configuration_sha256 3f71a437…`). In-chain test-look counter **6 → 7**. RULE 0.71 P@1 /
376.4 m / nDCG@5 0.9417; LOGISTIC 0.73 / 371.6 m (one address), LAMBDAMART 0.72 / 371.6 m, PAIRWISE
0.72 / 371.6 m — every paired interval spans zero on 100 addresses. The winner was frozen before the look
and the decision would not have changed if it had gone the other way.

**Controls.** Shuffled-label LambdaMart collapses (S-VAL <500 m 0.5652 vs RULE 0.8406, resolved worse)
→ no label leakage; pin-only reproduces RULE's top-1 exactly (the rule's value is its tie-breaking, not
its geometry); the frozen feature key set is exactly the 15, with no forbidden key present and no
agent/account field in the matrix (so an "agent-ID-only" control **cannot exist without inventing a
feature** — the audit replaces it, said out loud rather than faked); 0 firewall violations; 0 outbound
socket attempts; `place_neighbour` still disabled and absent from every lane. Cost: fits 0.6–0.8 s; scoring
p95 ≤0.2 ms/address (LOGISTIC) vs 0.03 ms for the rule — material but not the deciding factor.

**Repairs made while building D.** (1) A `KeyError` in `sutra/learning.py`'s prediction path was removed
before any number was quoted. (2) A row-truncation bug: D passed a stripped candidate dict to the frozen
rule interface, which needs `granularity` — rows now carry the full candidate record, so the rule is scored
with the same object the product uses. (3) Per-town/per-stratum tables were built for every learned model
rather than one (the decision loop inspects all of them). (4) **A one-sided-test labelling defect** — the
same class as Experiment C's removal flag: `paired_grouped_ci` tests only "does A beat B?", so a *resolved
rule advantage* was being printed as "not resolved". Both directions are now computed and reported;
`reading ∈ {challenger_resolved_better, rule_resolved_better, not_resolved, identical}`. The adoption
gate still only ever asks whether a challenger beats RULE. (5) `tools/check_leakage.py` gained two standing
guards: the challenger library is included in the "never reads the surveyed truth table" scan, and no
request-path module may import it. (6) `LOGISTIC`'s monotone failure is **resolved by documented rejection** rather than a constrained
refit, and the exact violations are recorded in the receipt: `f_sim_jaccard` fitted negative (required
≥0) and `f_dist_to_town_centroid_m` fitted positive (required ≤0). Rejection was chosen because LOGISTIC
already fails the adoption gate on its own metrics and because a constraint would erase the diagnostic —
the trees stay constrained and are verified per tree. (7) The three D artefacts plus the four code files
are registered in the manifest step of the chain.

**Outcome: rule priority retained — a successful experiment.** The gate required a challenger to beat RULE
on the pre-registered primary S-VAL metric beyond the paired interval, regress nothing, and stay
directionally consistent out of block; none did, and `sutra/ranking.py` is byte-unchanged. The production
ranker was never a candidate for change on this evidence, and the machinery that would have promoted a
challenger is now built, tested, and idle — which is the point of a gate.

---


## 3.8 Precision optimisation — pushing the official data to its ceiling (`data/derived/precision_optimization_report.md`)

**Question.** *Can end-to-end precision be pushed to ≥0.90 within 500 m using official data only, and if
not, what is the honest ceiling?* Beyond D in scope: candidate generation, ranking, uncertainty and the
temporal use of field evidence were all in play, S-Eval stayed firewalled until the freeze.

**What changed in production.** Exactly one thing: the **locality matching rule** (`sutra/candidates.py`,
`config.RETRIEVAL_VERSION = "v2"`). v1 counted a locality as matched when the address and the locality name
shared *any single token* and let a stale pincode outvote the text — measured wrong on 118/292 supervision
rows. v2 requires every token of the name (coverage ≥ 0.5), always including the name's **rarest** token
(IDF over the official corpus, as-of clean), with a deterministic tie-break, and emits *all* localities of
an ambiguous pincode instead of the first. The same arm, the same source table, a better rule.

**Measured effect (pool):** candidate recall/oracle rises **0.8801 → 0.9144 within 500 m** (median 229.9 →
215.5 m; S-VAL 0.8696 → 0.8986); the ranked answer does not move (top-1 <500 m 0.839, pin 292/292) — the
rule is not the bottleneck and was never going to be.

**Selection, re-tested on the better candidate set.** RULE 0.8386/0.8406 (S-TRAIN/S-VAL) vs medoid 0.8341/
0.8406, coarse-pin demotion 0.8296/0.8116, medoid-on-v1 0.7444/0.7826; fitted challengers LOGISTIC
−0.029 [−0.101, +0.044] nR, LAMBDAMART and PAIRWISE **resolved worse** (−0.246). The pin remains the
cold-lane optimum, and the taxonomy explains why: of 292 rows, 245 resolve within 500 m, **22 have a
candidate that would have been better** but every trade that fixes them breaks more, 19 have nothing within
500 m (best is a centroid), 6 are pincode-coarse retrieval failures.

**The ceiling, proved.** A perfect chooser over the candidates the arms can build reaches **0.88 within
500 m on S-EVAL and 0.8986 on S-VAL** — so **the 0.90 cold-start target is not reachable from the official
data**, and that is a bound, not an opinion. The absolute "best of every official point" bound (pin, any
locality centroid, any POI, any other address's pin) is 1.00 at 38.8 m median, reached only by a selector
that already knows the answer.

**Where ≥0.90 *is* reached — the warm regime.** A non-circular temporal holdout (candidates from evidence
strictly before T0 = 2026-05-15, label = promoted check-ins at or after it, 229 labels) gives **0.9867 within
500 m and 0.7733 within 100 m, median 45.6 m**, against cold 0.8472 on exactly those rows; where two
independent confirmations exist it is 1.000 within 500 m at a 24.0 m median. Paired vs cold, grouped by
place block: **+0.1397 [+0.0938, +0.1888] resolved better**, median −176.3 m [−227.3, −149.5] resolved
better. The mechanism is simple and worth stating: `gps_accuracy_m` in the official visits has a 9.8 m
median, so the check-ins are the precise signal and the vendor pin is the noisy one (promoted check-ins
disagree with each other by 39–43 m across a mid-quarter cut, 97–99% within 500 m).

**The locked S-Eval read (one read, after the freeze; snapshot now persisted and reused).** Cold
0.71 <500 m / median 375.8 m · warm (45/100 had evidence at the cut) 0.8222 <500 m / 0.5778 <100 m / median
58.0 m · product (warm→cold fallback) 0.76 <500 m / 0.33 <100 m / median 206.7 m · static-lane oracle 0.88.
The product-vs-cold delta on S-Eval (+0.05 <500 m [0.00, +0.101]) is **not resolved**. Full read history,
including the debugging executions, is disclosed in the report.

**Integrity.** Official data only, zero outbound attempts (asserted in-process), no model artefact, S-Eval
untouched until the freeze, every interval a paired grouped bootstrap over place blocks, and every
rejected idea kept as a negative control in `research/precision/` with its measurement.

**Follow-on pass (same task, after the first freeze): the coordinate policy.** The official
`visit_gps_points` table (160,406 rows — the agent's approach track, median 26 fixes per visit) had never
been used for coordinates; a visit's coordinate was one check-in sample. The **last three fixes** are taken
at the address, so their median averages out the single-sample error: `sutra/seed.py` now ingests that
estimate (`coord-v2-trace-tail`, ingest id `…-v3`, raw check-in retained as provenance). Measured
non-circularly — estimator from pre-T0 visits, judged against post-T0 visits — the holdout moves from
**28.7 m to 7.6 m median** and from 0.7639 to **0.8627 within 100 m**; the cold lane is unchanged under
either label (0.8459 at 500 m on both), which is what makes the gain attributable to the estimator rather
than to a moved goalpost. The product line follows: warm-within-100 m 0.7733 → **0.8578**, warm median
45.6 → **7.5 m**, and on the locked S-EVAL read the warm lane's median falls 58.0 → **16.4 m** while the
cold lane is untouched (0.71 / 375.8 m — the same numbers as the previous freeze, as it must be).

**Three more brief items, each measured and closed.** *Extra generators*: an address-book near-duplicate
retriever (town + retrieval-v2 locality + char-4-gram Jaccard ≥ 0.5, place-collapsed) covers 42.8% of rows
but rescues **one** frozen miss while losing on 66 — rejected; a pincode-consistency generator beats the
frozen best on **0** rows — rejected. *Archetype routing* fitted on S-TRAIN (six archetypes) collapses to
`frozen_baseline` in **every** archetype, so the router is the rule (delta 0.0, identical series): the pin
is not merely the global best arm, it is the best arm per address shape. *`place_neighbour`*: the
construction is now properly defined (other addresses in the same official place block, promoted evidence
strictly before as-of, provenance recorded, independence = neighbour addresses) and it is **genuinely
informative** — 61.9 m median against a 2162.1 m placebo at identical candidate counts — but it can change
**zero** product answers, because every address that has a same-place neighbour with evidence also has its
own. The arm therefore stays disabled, now for a stronger reason than the pre-registered placebo doubt:
redundancy, not weakness.

**Also delivered:** the mandatory per-address bottleneck audit as `data/derived/precision_bottleneck_table.csv`
(47 failure rows: text, normalised text, town, resolved locality, pincode, arms present, n candidates,
selected/oracle arm and error, why the oracle was not selected, why it does or does not exist), with the
full 292-row classification in the receipt.

## 3b. What *running* it found that testing it could not

The acceptance suite passed while the shipped server was broken in four separate ways. All four were
found by starting the process and using it, which is why the brief ends by requiring the runtime to be
run for real rather than only unit-tested:

| # | Symptom | Cause | Fix |
|---|---|---|---|
| 1 | every request through the HTTP server died: `SQLite objects created in a thread can only be used in that same thread` | one `sqlite3` connection created on the main thread, handed to `ThreadingHTTPServer` workers | `Store` now keeps **one connection per thread** (WAL + busy timeout, schema idempotent) and `submit_observation` takes a single writer lock |
| 2 | half of a 48-request burst reset the connection | `socketserver`'s default listen backlog of 5 — exactly the shape of a field team syncing at once | `Server.request_queue_size = 128`, keep-alive with explicit `Content-Length` |
| 3 | two consecutive rebuilds of the same official history produced **different store digests** | the backfill stamped `server_received_at` from the wall clock; a settled archive has no "now" | backfill takes the receipt time from the source record (live capture keeps a real receipt time); ingest id → `v2`; digest now stable at `26232e3a…` across rebuilds |
| 4 | pasting a corpus address into `/resolve` returned UNPLACEABLE | the runtime's text normaliser had drifted from the cleaner's, so a record could not match itself; the fallback then picked an arbitrary address in a matched locality | one canonical normaliser in `sutra/dataio.py`, imported by `tools/clean_official.py` (the cleaned table's md5 is **unchanged**, proving the move was behaviour-preserving); `find_address` now requires an unambiguous token match and otherwise returns a labelled **area context with no coordinate** |

A fifth defect was found while reconciling this report against the artefacts rather than against the
tests: **the `memory` arm had silently disappeared** from `candidates_v2.csv` (10,741 rows, no memory
row). Cause: beliefs were being materialised only *at* the canonical cut-point, and a belief may not
read itself — `latest_belief_before` correctly found nothing strictly earlier, so the warm lane was
quietly weaker than the report claimed. Fixed by materialising each address's **prequential** belief
(last observation before the cut-point, +1 s) alongside the canonical one — 2,757 belief rows now — and
by adding a guard to `tools/check_leakage.py` that fails the build whenever the memory index holds
entries but the candidate artefact holds no memory row. Effect on the canonical state at
`2026-06-01`: CONFIRMED 271 · PROBABLE 361 · APPROXIMATE 845 (70 addresses move APPROXIMATE → PROBABLE
because a remembered prior belief is strictly better than a cold default).

### 3c. The Experiment B hardening pass (defects found by running the ablation)

| # | Symptom | Cause | Fix |
|---|---|---|---|
| 1 | B1 looked *cheaper* than production | `Ring.address_book_index` rebuilt the 3,117-row key space **on every call** — our defect masquerading as a property of the approach | cached per ring (`_book_cache`); fair timing is B1 0.82 ms vs B2 2.80 ms per address. The earlier "+1.42 ms/addr" claim is **retracted** and the retraction is stated in the report |
| 2 | a naive ring could have won a "simplification" while being worse | a one-sided "resolved better" test let a ring be its own benchmark | selection rewritten as a quality frontier + **symmetric** dominance + eligibility (cheapest rung not resolved-worse than any other) |
| 3 | a run produced **no eligible rung at all** | raw CIs let a ~1–2 ms shared-machine latency delta "dominate" production | declared a materiality margin (12.5 ms = 5% of the 250 ms budget) *before* the final run, applied symmetrically; error/hit metrics need none because they are exact given a candidate set |
| 4 | an ablation that compares normalisations could have been rigged | B1 briefly carried its own richer relation vocabulary | `preprocess.RELATION_WORDS = config.RELATION_WORDS` — a ring may change *how* text is read, never *what* counts as a relation phrase (now invariant I10) |
| 5 | a rejected component with no positive control is indistinguishable from dead code | the residue matcher accepts nothing on this corpus | added the **T16 positive control** (typo'd locality recovered at 0.5061 / 0.375) and the instrumented funnel counters reported in the receipt |
| 6 | the report could claim a guardrail the chain never reproduced | `tools/reproduce.sh` did not run Experiment B, and two guards were wrapped in `|| true` | Experiment B is now step 12/12 of the chain and the guards **fail closed**; the report's reproduce section quotes the real chain |

Two smaller repairs in the same phase: `Store.reset()` removes the `-wal`/`-shm` sidecars (rebuilding a
store used to fail with a bare `disk I/O error`, which reads like corruption and is only a stale
journal), and the demo's scratch databases no longer accumulate inside `data/derived/runtime/`.
Invariant test **I9** was added so the text path cannot silently rot again.

---

## 4. Two live documents that contradicted the contract (found and fixed)

An implementation cannot obey two rules at once, so these were corrected in place (the decision log's
history rows are untouched):

1. `PS3_UNCERTAINTY_ARCHITECTURE.md` §4 and `PS3_NOVELTY_AND_DIFFERENTIATION.md` still said negatives
   **cannot** change a coordinate and that "there is no code path that expresses it" — the exact
   absolute the graded rule (F2.1/D36) replaced, and the code path the contract requires. Both now
   state the graded rule verbatim.
2. The landmark parser assumed the noun precedes the relation ("church near"). The corpus is the other
   way round in English (`close to Hanuman Temple`, 233; `near`, 207; `opp`, 173) and the other way
   round in Kannada (`ಚರ್ಚ್ ಹತ್ತಿರ`, 76). The parser now reads both windows and only fires on a real
   landmark-name token match; a plausibility filter drops a wrong-but-named POI that is far from every
   other arm. Known limitation, honestly reported: Kannada relation phrases resolve only when the
   landmark noun is Latin-script, so those addresses get `directions=null` rather than a guess.

---

## 5. What remains before Experiment A — item 9

**Nothing, and A has run.** The brief's stop condition was *"STOP before Experiment A if any acceptance
test fails"*; the suite is green (26/26), the firewall is verified, the candidate schema validates, and
p95 latency meets the contract with a 10× margin — so the gate opened and A was executed as ladder step
1, reproducing the pre-contract floor exactly (§3.4). Experiment B then ran as step 2 (§3.5).

What remains before the **next** experiment (F, per the gated order A → C → E → D → F → …):

* nothing blocking; C ran and answered its retrieval question (§3.6) and D ran and answered its ranking
  question (§3.7) — a learned ranker does **not** beat rule priority on this pool, and the reason is
  measured, not asserted: the rule's top-1 is already the best available candidate on 75% of S-VAL
  addresses, and the whole reordering headroom is +0.04 on <100 m;
* **C2 (neighbour index) stays locked** until the official baseline pipeline is stable and the placebo
  control passes: the arm exists in code, refuses to emit, and is asserted absent in the artefacts;
* **still RED by design (production-only, not built):** distributed multi-device sync, the slow loop
  (retraining with drift alarms), and the full mobile app. The offline MVP that *is* built covers
  pack → airplane → capture → outbox → replay;
* **open limitations, stated rather than hidden:** the promotion pool is thin (292 addresses, so the
  learned ranker is not built); the pincode stratum has no publishable radius; the 8-arm retrieval
  ceiling is measured by C, not assumed here; DIGIPIN remains unmarked in the post-contract docs;
  `AD000005`'s landmark candidate scores 0.874 but is not primary-eligible, so the ranker falls through
  to memory — correct behaviour (a landmark is an anchor, not an address), left as the worked example;
  `sutra/api.py` has no explicit per-operation timing budget (the socket block in T12 still passes).

---

## 6. The ten requested items, and where each one is answered — item 10

| # | Item | Where |
|---|---|---|
| 1 | files created | §1.1 |
| 2 | files superseded | §1.2 |
| 3 | runtime modules | §2 |
| 4 | tests implemented | §3 (T1–T16 + I1–I10) |
| 5 | all test results | §3 (26 passed · 0 failed · 0 skipped) |
| 6 | candidate-schema validation | §3.1 |
| 7 | S-Eval firewall validation | §3.2 |
| 8 | runtime latency | §3.3 (p95 24.9 ms, target 250 ms → MET) |
| 9 | what remains before the next experiment | §5 (nothing blocking — A, B, C and D have run; the gate order continues at F) |
| 10 | exact reproduce command | below |

```bash
cd PS3_SUTRA && bash tools/reproduce.sh full
```

Determinism of the chain: `sutra_store.sqlite` ingest digest `26232e3a…`, `candidates_v2.csv`
`4d06c7da…`, firewall receipt `228680109f0c…`, Experiment A `regression_check.matches = True`,
Experiment B candidate-universe hashes `eeba49f8…` (B2/B3/B4) and `e154312b…` (B1), Experiment C
universes `41e5de3c…` / `eeba49f8…`, Experiment D frozen configuration `3f71a437…` — all unchanged
across repeated runs. D is deterministic given the seed (every fit seeds the same generator; tree building
depends only on the seed and the manifest's sorted row order), so a re-run reproduces the same scoreboards;
its receipt carries the code hashes of `sutra/learning.py`, `sutra/ranking.py`, `sutra/replay.py`,
`sutra/splits.py` and `sutra/stats.py` that produced the numbers.

---

*Sources: `[S69]` n-guard practice · `[S68]` blockCV/grouped resampling (the reason intervals are
resampled by place block) · `[S81][S82]` offline-sync precedent (outbox, idempotency keys,
hold-then-conflict) · `[S91]` pre-contract baseline measurement reproduced here · `[S95]` final data
policy (official data only, enforced by `tools/check_workspace.py`) · `[S96]` firewall and
due-diligence counts. Contracts: `PS3_IMPLEMENTATION_CONTRACTS_2026-10-07.md`. Locked architecture:
`PS3_ARCHITECTURE_LOCK_CANDIDATE_2026-10-07.md`.*

## Evidence / memory decision policy — `FINAL_EVIDENCE_MEMORY_POLICY` (`emp-v1`), 2026-10-08

The last precision task. `memory_candidates()` used to emit the previous belief's *candidate
coordinate*, so an address whose prior winner was the vendor pin came back as "place memory" —
identical to the pin within 5 m, marked `primary_eligible` (prior tier CONFIRMED) and therefore ahead
of a real check-in. Measured on the 292-row supervision pool: 73/292 emitted memory candidates were
pin-derived, and 7 of the 10 warm >500 m failures were that class.

The frozen policy emits memory only when the prior's coordinate is **accumulated field evidence**
(armed `field_evidence`), and recomputes the prior at the query instant when no belief row was
materialised there (belief is a pure function; the stored row is a projection). Result: 4 pool rows
fixed, 0 broken, supervision-pool paired grouped bootstrap +0.0137 [+0.0034, +0.0280]; both temporal
cuts and the tier/status census byte-identical; no new coordinates; no negative-evidence relocation.
On S-Eval the product lane is unchanged (0.33 / 0.55 / 0.76, median 202.2 m = the frozen read) and
the warm lane narrows to the 31 answers that are actually evidence-backed, at higher accuracy
(<500 0.8222 → 0.9677, median 16.4 → 12.4 m). Gate status is recorded in full — criterion (1) is
resolved on the supervision pool but only *validation-limited* on S-VAL alone.

Rejected after measurement: single quality tiering (no effect — competing singles carry equal
weight), fewer singles (regression), GPS-accuracy gates (no effect), a quality-ordered tie-break
(regression on S-VAL and both temporal cuts), and materialising memory everywhere *without* the emit
rule (temporal <100 m collapses 0.8903 → 0.6498 — the cleanest proof that pin-derived memory is
harmful rather than merely useless).

Artefacts: `data/derived/evidence_memory_policy_{report.md,results.csv,receipt.json}`,
`evidence_memory_error_table.csv`, `final_evidence_memory_policy.json`, snapshot
`evidence_memory_policy_snapshot.json`; tool `tools/evidence_memory_policy.py`. Revert is one flag
pair (`MEMORY_EMIT="always"`, `MEMORY_ON_DEMAND_BELIEF=False`). Model optimisation stops here; the
next phase is UI/UX.
