# SUTRA — frontend + deployment smoke report (2026-10-08)

Everything below was executed against the delivered build on this date. Nothing in this report is
projected, estimated or re-stated from an earlier document; each row names the command that produced
it. **This revision follows the Battle-Model integration**: the frontend served at `/` is now the
workbench build (`battle_model/site/index.html`), and every number here was re-measured against it.

## 1 · Build

| Step | Command | Result |
|---|---|---|
| Clean install from the lockfile (workbench) | `cd battle_model && npm ci` | 98 packages, 0 audit issues |
| Type-check + production build | `npm run build` | `tsc -b --noEmit` clean · `battle_model/site/index.html` = **345,597 B single file** (98,439 B gzipped) |
| Reproducibility | `npm ci && npm run build` again (incl. from `tools/reproduce.sh`) | same single-file output |
| Console build (fallback, retained) | `cd web && npm ci && npm run build` | `web/site` = 622 B html + 19,513 B css (5.2 kB gz) + 304,634 B js (90,444 B gz) |
| Container layout | the image's exact filesystem (`sutra/ tools/ tests/ data/ battle_model/site web/site`) started as a service from a scratch directory | 75 MB tree, service starts, **21/21** HTTP checks pass, `/` serves the workbench single file |

## 2 · Test suites

| Suite | Command | Result |
|---|---|---|
| Acceptance (T1–T16 + as-of/ring invariants) | `python3 -m pytest tests/test_acceptance.py -q` | **26 passed** (17.26 s) |
| Frontend contract v1 | `python3 -m pytest tests/test_contract_v1.py -q` | **51 passed** (2.42 s) |
| Product surface v1 | `python3 -m pytest tests/test_product_v1.py -q` | **39 passed** (6.12 s) |
| No-fake-data guard (console **and** workbench) | `python3 -m pytest tests/test_no_fake_data.py -q` | **9 passed** (0.08 s) |
| Whole test directory | `python3 -m pytest tests/ -q` | **125 passed** (26.8 s) |
| Guards | `check_leakage.py` · `check_workspace.py` · `check_links.py` | ALL PASSED · ALL CHECKS PASSED · ALL RESOLVE (1,158 refs) |
| Manifest | `tools/build_manifest.py` | 342 files / 84.21 MB (`node_modules` and build output excluded) |
| End-to-end chain | `bash tools/reproduce.sh full` | green through every numbered step, including the added workbench build |

The no-fake-data guard now scans the workbench sources and the shipped bundle
(`battle_model/src`, `battle_model/site/index.html`) in addition to `web/src` and `web/site`. It
asserts: no banned provider/score/delay/GPS tokens, no `Math.random` outside vendor code, and that
every route the workbench's API layer calls is a real route.

## 3 · HTTP smoke — `python3 tools/smoke_test.py --base http://localhost:8000`

**21/21 passed.** Grouped:

* **Frontend** — `GET /` returns the workbench single-file build (345,597 B).
* **Runtime** — `GET /health` and `GET /v1/health`: `ok: true`, 4 packs, 5,578 observations, and the S-Eval locked-read ledger disclosed as an integer that reading does not advance (the historical ten-read ledger lives in `data/derived/evidence_memory_policy_receipt.json`; the counter itself was restarted by the deterministic store rebuild — see §5).
* **Resolve** — AD003067 → CONFIRMED/STABLE, `SERVE`, r = 566.9 m, space `sutra_local_metric_plane:T2`; AD002936 → MOVED_SUSPECTED, `VERIFY_FIRST`, r = 1202.6 m, task `VF-AD002936-MOVED_SUSPECTED`; AD000002 (work-like) → `REFUSE`, coordinate withheld; all contract blocks present; **repeated call byte-identical**.
* **Workbench projections** — `/v1/places` (952 places in T2, identity rule `colocation<=30m|adjudicated` from the service) and `/v1/evidence` (1,141 negatives in the filter, `negatives_move_coordinate: false`, no negative row claiming a coordinate).
* **Read surface** — geometry (7 candidates, 6 visit markers, 1 ring r 1202.6), belief (v7, 6 refs), observations (6 rows, both negatives non-claims, `negatives_move_coordinate: false`), place (MOVED_SUSPECTED, 1 stored version, contradiction `coordinate_unchanged: true`), tasks (5 of 84, facets `{MOVED_SUSPECTED: 84}`, cursor present), town plane (89 reference points), offline pack `pack-T2-7247f0bd3d96`, legacy `/place/{id}`.
* **Error paths** — bad cursor → 400 `INVALID_REQUEST`; unknown address → 404 `unknown_address`; unplaceable geometry → 200 with `withheld: gate_refuse` and zero points.

## 4 · Browser smoke — `node battle_model/tools/browser_smoke.mjs` (headless Chromium)

**22/22 checks passed against `http://127.0.0.1:8001` (a copied store), zero console errors, zero
failed requests, zero responses ≥ 400.** The checks cover: Overview's real operational counts and the
three frozen populations stated separately; the Resolver answering AD003067 (`SERVE`) and AD002936
(`VERIFY_FIRST`, radius 1202.6 m); the decision ticket's typed reason codes and score terms;
candidate→map cross-highlighting; the typed free-text intake resolving through the live pipeline
(no fixture replay); the refusal case rendering **no coordinate anywhere** (panel + withheld plane);
Places and the place detail (stored point, radius, real belief versions); the evidence feed with the
policy's verdict; a negative visit stating it carries no coordinate claim; the queue with real task
ids, causes and lifecycle; the case panel's ticket, radius, history and `clears_when`; a **real**
`PATCH /v1/tasks/{id}` transition recorded as a lifecycle event; a **real** adjudication that closes
the case and recomputes the belief; the read-only audit chain with its payload hash; Method & Trust's
frozen evaluation and four status labels; a 900 px viewport with no horizontal overflow; and a
network gate asserting every one of the 66 API calls was a real route.

The 12 screenshots written by the run are `screenshots/bm-01…bm-12*.png`. The earlier console-level
script (`web/tools/browser_smoke.mjs`, 14 steps) is retained and still passes, but it exercises the
fallback build, not the product surface.

## 5 · Frozen-architecture integrity

| Check | Result |
|---|---|
| `FINAL_PRECISION_CONFIG` | **reported, not resolved** — the regenerated file carries `frozen_configuration_sha256 = 9abebb8f…` while the published value is `ac61cf2e…1989`; the behavioural knobs are unchanged and every frozen lane reproduces exactly (main report §5.3). No "unchanged" claim is made for this hash. |
| `FINAL_EVIDENCE_MEMORY_POLICY` (emp-v1) | **unchanged** — `policy_hash()` over the policy body (file minus the tool-written `policy_sha256` / `scoring_code`) → `a110f08962993e3ca6b7151edbc01002029019faa4e583625eb599f8379b2775`, equal to the file's own field and the receipt's `frozen_policy.sha256`; `s_eval_used_for_selection: false` |
| S-Eval locked reads | the store-state counter was restarted by the deterministic rebuild (`GET /health` → 7); the historical ledger of **10 reads with full timestamps** is preserved in `data/derived/evidence_memory_policy_receipt.json` (`s_eval.read.timeline`). Reading it never advances it. |
| Official dataset | **12/12 tables byte-identical** to the independent Drive record (leakage checker) |
| Store rows | observations 5,578 · evidence_scores 5,578 · belief_versions 2,757 · task_events 278 · receipts 0 — the documented baseline, verified before and after the smoke runs; every write-path check ran against a copied store (`SUTRA_STORE=/tmp/wt2.sqlite … --port 8001`) |
| Candidate arms / ranking / radius / gate / memory / purpose / evidence policy | untouched — `sutra/candidates.py`, `sutra/ranking.py`, `sutra/evidence.py`, `sutra/uncertainty.py`, `sutra/eligibility.py`, `sutra/purpose.py`, `sutra/directions.py`, `sutra/config.py`, `sutra/belief.py` were not modified |
| Runtime `sutra/` source | contains no `requests.` / `urllib.request` / `http.client` / `socket.socket(` / `urlopen` — and the workbench makes no outbound call either; all fetches are same-origin relative paths |
| External data | none added; the external-research holding area remains permanently empty |

**Backend changes in this task, complete list:** static serving extended with `_web_root()` preferring
the workbench build (SPA fallback, traversal-safe paths, immutable `/assets/`) in `sutra/api.py`; the
new read-only projections `GET /v1/places` and `GET /v1/evidence` in `sutra/feeds.py`; and the
Dockerfile's stage 1 now builds the workbench. No product logic: the frozen modules were not touched,
and every legacy endpoint behaves as before (the HTTP smoke exercises them).

## 6 · Deployment status

| Target | Status |
|---|---|
| Local service, all routes | **done** (21/21 HTTP, 22/22 workbench browser checks) |
| Container layout | **done** (service started from the image's exact tree, 21/21, serving the workbench) |
| Workspace preview URL (`0.0.0.0:8000`) | **done** — the service binds all interfaces, which this platform exposes as a live preview |
| `docker build` / `docker run` here | **blocked** — no container runtime in this environment |
| Hosted provider push | **blocked** — no provider credentials present; nothing was faked |

The one command that finishes it, once a runtime or credentials exist:

```bash
docker build -t sutra . && docker run --rm -p 8000:8000 -e PORT=8000 sutra
```

`DEPLOYMENT.md` carries the build, run, environment, health-check and smoke-test instructions, and
`SUTRA_JUDGE_DEMO_SCRIPT_2026-10-08.md` carries the demo with the screenshot set in `screenshots/`.

## 7 · What this build does not claim

* No metric is served by the API; the three frozen evaluation populations are rendered from
  `/v1/method-trust` and kept separate: cold 71 % < 500 m (n = 100, median 375.8 m) · warm independent
  96.77 % (n = 31 answered, median 12.4 m) · product lane 76 % (median 202.2 m). No single accuracy
  figure, and no rupee or visit-reduction claim, appears anywhere.
* The workbench renders capability status from `/v1/method-trust`: 15 IMPLEMENTED · 1 DESIGNED ·
  4 NOT YET IMPLEMENTED · 4 NOT MEASURED — including, in product words, that a reviewer closes a case
  but does not move a location.
* Coordinates are local metric metres only. No latitude, longitude, CRS, basemap or external
  geography exists at any layer of this build — the plane is drawn from the service's own geometry
  payloads.

---

*Sources:* `[S61]`/`[S81]`/`[S82]` (offline-first field capture: append-only observations, idempotency
keys, server-authoritative versioning, hold-then-mark-conflict) frame the service's read/write
discipline; `[S69]` (n-guards) and `[S73]` (heavy-tailed geocoder error) frame the radius and coverage
claims the workbench is allowed to show; `[S95]` is the binding data policy the guards enforce.
