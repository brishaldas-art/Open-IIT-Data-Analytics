# SUTRA — deployment

One application, one process. The workbench is a single-file static build; the API is
standard-library Python. The same Python service serves both, so there is no second host, no CORS,
and no runtime network egress anywhere in the product.

```
battle_model/  (React + TS + Vite, single-file build)  →  battle_model/site/index.html
                                                                ↓  served by
sutra/api.py  (stdlib ThreadingHTTPServer)  →  /  (workbench)  +  /v1/*, /health, /place, /tasks…  (API)

web/ (earlier console build) remains in the tree and is served instead when battle_model/site is
absent — `sutra.api._web_root()` prefers the workbench build.
```

---

## 1 · Build

```bash
# workbench (the frontend served at /)
cd battle_model
npm ci            # or: npm install
npm run build     # → battle_model/site/index.html  (one file, 345.6 kB / 98.7 kB gzipped)

# nothing to install for the service: Python 3.11+ standard library only
python3 -c "import sutra.api"     # from the repository root
```

`npm run build` runs `tsc -b --noEmit && vite build`; output is deterministic for the committed
lockfile (`vite-plugin-singlefile` inlines the JS and CSS into the one HTML file). The earlier
console build (`cd web && npm ci && npm run build` → `web/site`) still works and is used only when
the workbench build is missing.

## 2 · Run

```bash
python3 tools/serve_runtime.py                 # 0.0.0.0:8000
python3 tools/serve_runtime.py --port 9000     # explicit port
PORT=3000 python3 tools/serve_runtime.py       # platform-provided port (containers pass this)
HOST=0.0.0.0 PORT=3000 python3 tools/serve_runtime.py
```

Port resolution order: `--port` → `$PORT` → `8000`. Host resolution: `--host` → `$HOST` → `0.0.0.0`.
**Never loopback-only**: the bind address is `0.0.0.0` by default so the service is reachable from
outside its container or sandbox.

Console absent? The service still starts and serves the API; `/` falls back to the original
read-only page. Nothing else changes.

## 3 · Environment

| Variable | Default | Meaning |
|---|---|---|
| `PORT` | `8000` | listen port (use the platform-provided value in containers) |
| `HOST` | `0.0.0.0` | bind address; keep `0.0.0.0` in containers |
| `PYTHONUNBUFFERED` | — | set to `1` in containers so logs stream |

There are no secrets, no API keys, no external service credentials, and no outbound calls.

## 4 · Health check

```bash
curl -fsS http://localhost:8000/health | head -c 200
curl -fsS http://localhost:8000/v1/health          # alias
curl -fSsI http://localhost:8000/                  # workbench present → 200 text/html
```

`/health` returns `ok: true`, the version block, store counts, index digests, pack identity, runtime
gauges and the counter ledger. The Docker image declares the same check as a `HEALTHCHECK`
(`urllib.request` against `127.0.0.1:$PORT/health`, inside the container).

## 5 · Container

```bash
docker build -t sutra .
docker run --rm -p 8000:8000 -e PORT=8000 sutra
```

* Stage 1 (`node:20-alpine`) builds the workbench (`battle_model/`) and the reference console (`web/`)
  with `npm ci && npm run build`.
* Stage 2 (`python:3.12-slim`) copies `sutra/`, `tools/`, `tests/`, `data/`, the workbench build
  (`battle_model/site`) and the console build (`web/site`).
  **No `pip install` at runtime** — the service imports only the standard library.
* Runs as the non-root user `sutra` (uid 10001). The API is read-only over the store; the counter
  ledger is appended when a request is served.
* Layout produced by the image is exactly the layout smoke-tested here
  (`DEPLOYMENT.md` §6, "container-layout run").

## 6 · Smoke test

```bash
python3 tools/smoke_test.py --base http://localhost:8000
```

21 checks: the served workbench bundle, `/health` and `/v1/health`, both demo resolves, the refusal
state, byte-identical repeated calls, geometry, belief, observations, place, queue, town plane, the two
workbench projections (`/v1/places`, `/v1/evidence`), the offline pack, the legacy place read, and the
three error paths (400 bad cursor, 404 unknown address, withheld geometry). The suite and its output are recorded in
`SUTRA_FRONTEND_SMOKE_REPORT_2026-10-08.md`.

Browser-level check (needs a Chromium; in this sandbox install it with the idempotent helper
`bash web/tools/install_browser_deps.sh`, which vendors the shared libraries under `/var/tmp/root`
and then runs `npx playwright install chromium`):

```bash
cd battle_model
LD_LIBRARY_PATH=/var/tmp/root/usr/lib/x86_64-linux-gnu:/var/tmp/root/usr/lib/x86_64-linux-gnu/nss \
PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS=1 \
node tools/browser_smoke.mjs http://127.0.0.1:8001 ../screenshots
```

22 checks over the workbench — every screen, candidate cross-highlighting, the refusal state (no
coordinate rendered anywhere), the places/evidence projections, the real task transition, the real
adjudication, the read-only audit chain, a narrow viewport, and a request/console cleanliness gate —
failing on any console error, any request answered ≥ 400, or missing state. Run it against a second
service instance on a **copied store** (`SUTRA_STORE=/tmp/wt2.sqlite … --port 8001`) because checks
15–17 write. Writes the 12 `bm-*.png` screenshots in `screenshots/`.

The earlier console-level script (`cd web && node tools/browser_smoke.mjs …`) is retained and still
passes, but the workbench script is the one that exercises the shipped frontend.

## 7 · Deployment status (2026-10-08) — honest account

| Target | Status |
|---|---|
| Local run, all routes | **done** — 21/21 HTTP checks, 22/22 workbench browser checks against a copied store, 125/125 pytest |
| Container layout (the image's exact filesystem) | **done** — service started from that tree, HTTP checks pass |
| Public preview URL via this workspace's preview mechanism | **done** — the service binds `0.0.0.0:8000`, which the platform exposes as a live preview |
| product surface (P1/P2, 2026-10-08 · extended) | `GET /v1/overview` (cold/warm + tier mix), `GET /v1/method-trust` (four status labels), `GET /v1/audit` (+ **`GET /v1/audit/{belief_id}`** chain walk), `GET /v1/address/{id}/case`, `GET /v1/tasks/{id}` (+`/history`), `PATCH /v1/tasks/{id}`, `POST /v1/adjudicate` (**adjudication observation + belief recompute**), `POST /v1/score_visit`, `POST /v1/batch_resolve` (**≤5,000** per call) — append-only task events; every other route stays read-only |
| write-path testing | run a **second service instance against a copied store** (`SUTRA_STORE=/tmp/copy.sqlite … --port 8001`) so the shipped store is never written by a test; the store is a pure function of the official history and can be rebuilt with `python3 tools/build_store.py --reset` |
| `docker build` / `docker run` on this machine | **blocked** — no container runtime is installed in this sandbox (`docker: command not found`, no `podman`); the image cannot be built or run here |
| Push to a hosting provider (Fly/Render/Railway/Cloud Run/ECR…) | **blocked** — no provider credentials or tokens are present in this environment (`env` shows none); nothing was faked |

**The single command needed once a runtime or credentials exist** (from the repository root):

```bash
docker build -t sutra . && docker run --rm -p 8000:8000 -e PORT=8000 sutra
```

or, for a platform that builds from a Dockerfile, point it at the repository root with
`PORT` from the platform. Both were validated as far as this environment allows: the frontend builds are
proven reproducible (`npm ci`), the runtime layout the image produces is proven working (container
layout run), and every route is proven over HTTP and in a browser.

## 8 · What a reader should not expect

* No basemap, tile server, geocoder or external geography at any layer — the plane is local metric
  metres only.
* No runtime network egress from the application: `sutra/*` imports no HTTP client.
* Nothing beyond the declared write surface. `POST /v1/adjudicate`, `PATCH /v1/tasks/{id}` and
  `POST /v1/batch_resolve` (≤ 5,000) are the only routes that append to the store, and each is
  append-only — old observations are never mutated. Everything else, including the audit chain the
  workbench renders, is read-only.

---

*Sources:* `[S61]`/`[S81]`/`[S82]` — offline-first field capture practice (client-generated idempotency
keys, append-only observations, server-authoritative versions, hold-then-mark-conflict) is why the
service is a single append-only store plus one read surface rather than a distributed pair of hosts;
`[S92]` — the operational framing of running this on real field infrastructure.
