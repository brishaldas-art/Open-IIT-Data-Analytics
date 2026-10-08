# Battle-Model → SUTRA integration plan

Source of truth for this pass: the retrieved zip (sha256 `77c1d289dd2fb27a2e749f0413fcd36a9a87f0dad15087c36b0ba37cdf9fee36`,
28 files, all 15 handoff clue files present), unpacked at `uploads/battle_model_zip/`, and the live service
on `0.0.0.0:8000`.

## What the Battle-Model shell is (inspection result)

React 19 · Vite 7 · Tailwind 4 · lucide-react · `vite-plugin-singlefile` (build = one self-contained
`index.html`). Six views (`overview · resolver · places · evidence · queue · method`), an instrument-grade
SVG map (`LocalPlaneMap`, drag-pan/wheel-zoom/candidate-select, pure metres), a UI primitive kit (`u.tsx`),
and **one data seam: `src/lib/api.ts`** (six fetchers + a `useQuery` hook) — the file whose own header says
*"to go live, replace each body with the documented HTTP call and keep the return types"*.

Design system (`index.css`): warm paper, hairlines, IBM Plex Sans/Mono/Serif, surveyor orange. Preserved
verbatim — no visual changes anywhere in this port.

## What must die (Phase 3 + §27 of the handoff)

| Where | Fake behaviour | Real replacement |
|---|---|---|
| `lib/fixtures.ts` | 548 lines of invented cases/places/visits/overview | **deleted** |
| `lib/api.ts` | `setTimeout` "network", fixture returns | real `fetch` to the SUTRA service |
| `lib/session.tsx` | client hash-chained audit ledger, invented hashes, client case patches | backend is the ledger; session keeps only notices + as-of |
| `lib/utils.ts` | `chainHash` (fake hashes), `mulberry32` (fixture jitter) | removed |
| `Resolver.verdict()` | re-derives the gate in React with invented thresholds `0.85 / 0.60 / 0.15 / 25 m` | `eligibility.action` + `decision_ticket` from the backend |
| `Resolver` task ids | ``VQ-49${Math.random()}`` | real `task_id` from the response |
| `Resolver` pipeline | `setTimeout` staged "trace" with invented ms | real `arms_considered[]` — what each arm scored and why it lost |
| `Resolver` score parts | invented 6-part decomposition (`text/component/source/evidence/memory/freshness`) | real typed `reason_codes[]` / `score_terms[]` with their real effect values |
| `Overview` | 14-day accuracy series, fake latency, fake SLA, 5 invented microservices with p50/err% | real frozen populations (n-stated), measured accepted latency, real components/packs |
| `Places` | confidence %, `Math.random()` reverification ids | tier + measured coverage; real `place_id`; reverification via the real task list |
| `FieldEvidence` | mock-provider / clock-skew / sats-HDOP diagnostics | real integrity: duplicate claims, media hashes, dwell, accuracy, `coordinate_claim`, evidence class |
| `VerifyQueue` | close = local state patch; fake SLA hours; "assign to me" (no such backend concept) | `POST /v1/adjudicate` + `PATCH /v1/tasks/{id}`; real `priority`, `recommended_action`, `clears_when` |
| `Method` | invented stages/gates/weights/"EV-2303 rejected"/214 ms | real `how_it_works`, real gate vocabulary, frozen populations, four capability labels, real audit chain |
| `Shell` | "Plane SEAL-01 · Epoch 2025-W46", "fixture replay", "demo 0.9.4" | real `coordinate_space` + town name, real runtime/offline mode, pack version |
| `types.ts` | `CandidateSource = "Gazette Registry" \| "Municipal Parcel DB" \| "Postal PIN Directory"`, SLA, P1/P2/P3, confidence | the real vocabularies the service emits |

## What is preserved (Phase 2)

Every layout, hierarchy, spacing, typography token, navigation item, the map's interaction model
(pan/zoom/select/cross-highlight/legend/scale bar/north arrow), the candidate card, the decision ticket,
the evidence timeline, the places table + detail, the queue table + case panel, responsive grids
(`grid-cols-12` with `col-span` breakpoints). No redesign, no new views, no renamed navigation.

## Where each view's data comes from (all verified live)

| View | Endpoints |
|---|---|
| Overview | `GET /v1/overview`, `GET /v1/method-trust`, `GET /v1/evidence` (new, read-only) |
| Resolver | `POST /resolve` (free text **or** `address_id` — free text is real, not fixture replay), `GET /v1/plane/{town}` |
| Places | `GET /v1/places` (new, read-only list), `GET /v1/place/{place_id}`, `GET /v1/plane/{town}` |
| Field evidence | `GET /v1/evidence` (new, read-only), `GET /v1/address/{id}/observations`, `GET /v1/geometry/{id}` |
| Verify queue | `GET /v1/tasks`, `GET /v1/tasks/{id}` (+history), `POST /v1/adjudicate`, `PATCH /v1/tasks/{id}` |
| Method | `GET /v1/method-trust`, `GET /v1/audit/{belief_id}`, `GET /v1/health` |

New backend routes are **additive and read-only** (`/v1/places`, `/v1/evidence`) — allowed by the handoff
("only existing routes or contract-conformant additions"). No frozen module is touched.

## Serving

`battle_model/` builds to `battle_model/site/index.html` (single file). The Python service serves it at `/`;
the previous console stays available at `/console/` for reference. One origin, no CORS, no second host.

## Rules held throughout

Backend decides; the frontend renders. No ranking, tier, radius, gate, priority, weight or eligibility is
computed in React. No lat/lon, no basemap, no external geography. Demo values are read from the service.
Refusal renders no coordinate. Frozen intelligence untouched.

## Files changed after the copy

`src/lib/{types,api,session,utils}.ts(x)`, `src/components/{Shell,LocalPlaneMap,u}.tsx`, `src/App.tsx`,
`src/views/{Overview,Resolver,Places,FieldEvidence,VerifyQueue,Method}.tsx`, `index.html` (title/meta only),
`vite.config.ts` (build outDir + dev proxy), `package.json` (build script), and `src/lib/fixtures.ts` deleted.
