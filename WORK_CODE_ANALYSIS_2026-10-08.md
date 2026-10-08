# CODE ANALYSIS — Google Drive folder `work` (the Battle-Model frontend source)

**Analysed:** 2026-10-08 · **Method:** downloaded via the Drive folder API, hashed, read line-by-line.
**Nothing in the source was executed or modified.** Markers: `[VERIFIED]` = observed in the code or
re-measured here · `[INFERENCE]` = follows from the code · `[UNKNOWN]` = not determinable from this folder.

---

## 0 · Provenance — what this folder is, and what it is not

| Fact | Evidence |
|---|---|
| The link is a Drive **folder**, id `1dIyX8LkpH4J30QmC_jXuSB-KqbC1i_Rw`, name `work` | folder listing |
| It contains one subfolder `work` (`1s-Ur7ZeJltoAF5Ue_reXTDzcNOKc1NSj`) with **22 files**, 260,823 B | recursive listing |
| All 22 files are **byte-identical** to the Battle-Model zip already retrieved and integrated (§7) | sha256 comparison, 22/22 match |
| The folder export **omits `vite.config.ts`** (present in the zip, absent here) | file-set diff |

`[INFERENCE]` The omission is a copy artefact, not a different revision — every file that is present
matches the zip exactly. Practical consequence: **this folder cannot be built as it stands.** The
project's own `tsconfig.json` line 30 includes `vite.config.ts`, and the `@/*` import alias used by
every component needs Vite's `resolve.alias` (plus the Tailwind plugin and the single-file build).
Without that file, `npm run build` fails on the aliases. `[VERIFIED]` in the deployed copy, where the
config exists, the build succeeds.

---

## 1 · What the code is

A single-page **field-operations workbench** for address resolution: React 19.2.6 + TypeScript 5.9.3
(strict) + Vite 7.3.2 + Tailwind 4.1.17, six screens, an SVG local-metric-plane map, and a
hash-routed-free single-view shell. It is designed as a **fixture-backed prototype**: it looks like a
working system, and it is labelled as a replay in two places (§3.4), but it talks to nothing.

```
src/main.tsx → App.tsx → Shell (chrome, nav, clock)
   ├── views/Resolver.tsx       502 lines   intake → candidate ranking → gate → decision → task
   ├── views/Overview.tsx       255         KPIs, warm/cold, series, service health
   ├── views/Places.tsx         218         memory graph, confidence, contradictions
   ├── views/FieldEvidence.tsx  213         visit feed
   ├── views/VerifyQueue.tsx    230         case queue, SLA, assign, close
   ├── views/Method.tsx         176         pipeline, gates, weights, audit table
   ├── components/LocalPlaneMap 447         SVG plane: roads, landmarks, candidates, rings, trails
   ├── components/u.tsx         197         Panel / Sec / KV / Meter / Pill primitives
   ├── lib/fixtures.ts          548         ← every operational value in the app
   ├── lib/api.ts                77         the data seam (all six fetchers)
   ├── lib/session.tsx          111         in-browser "audit ledger" + queue mutations
   └── lib/{types,utils}.ts     349         domain model · formatting · plane maths
```

---

## 2 · The data seam — the one genuinely good architectural decision

`src/lib/api.ts` is written as a swappable interface: six async fetchers with **documented intended
endpoints**, all returning fixtures after a simulated delay.

```ts
/** @backend GET /v1/overview */        export async function fetchOverview(): Promise<SystemOverview>
/** @backend GET /v1/scene */           /** @backend GET /v1/resolver/scenarios — POST /v1/resolve in production */
/** @backend GET /v1/places */          /** @backend GET /v1/evidence?window=14d */
/** @backend GET /v1/verify/cases?state=open */
```

`[VERIFIED]` This is why the integration later cost days, not weeks: views never import fixtures
directly (only `App.tsx`, for a case count), and no view touches `fetch`/`XHR` — `[VERIFIED]` there is
**no HTTP call anywhere in the tree**.

`[VERIFIED]` Three of the six documented routes do **not** exist in the service and never did:
`/v1/scene`, `/v1/resolver/scenarios`, `/v1/verify/cases`. The service's real equivalents are
`GET /v1/plane/{town_id}` + `GET /v1/geometry/{address_id}`, `POST /resolve`, and
`GET /v1/tasks?state=open`. The seam had the right *shape* and the wrong *addresses*.

---

## 3 · The central finding: every operational value is fabricated

`src/lib/fixtures.ts` (548 lines) is the entire database of this application.

| Fabricated set | Count | Where it surfaces |
|---|---|---|
| Resolver scenarios (raw text, parse tokens, anchors, candidates) | 4 scenarios, 15 candidates | Resolver — 8 arms, scores to 3 dp, `sigmaM`, co-location distances |
| Places (memory records) | 10 | Places list, contradiction panels |
| Field visits (`EV-23xx`) | 12 | Evidence feed, visit timeline |
| Verify cases (`VQ-49xx`) | 10 | Queue, with age and SLA clocks |
| Roads + landmarks (base map) | 12 roads, 8 landmarks | The plane, every screen |
| "Service health" rows (parse-svc, cand-idx, memory-graph, verify-orch…) | 6 | Overview telemetry strip |
| Daily series (resolutions + warm/cold "accuracy") | 14 days | Overview chart |
| KPI block | 6 | Overview header |

Specific inventions, with the line that carries them:

* **Coordinates** for every candidate, place, visit, road and landmark — e.g.
  `fixtures.ts:66` `anchor: { x: 820, y: 620 }`, `fixtures.ts:75` `at: { x: 700, y: 580 }`.
  `[VERIFIED]` They are internally consistent metres, but they are *nowhere's* metres.
* **Scores** to three decimal places with a **six-part decomposition** —
  `parts: { text: 0.91, component: 0.93, source: 0.72, evidence: 0.95, memory: 0.97, freshness: 0.94 }`
  (`fixtures.ts:76`) — invented weights, rendered as if they were the engine's.
* **Invented providers** — `"Gazette Registry"`, `"Municipal Parcel DB"`, `"Postal PIN Directory"`,
  `"Field Memory"` (`types.ts:45–49`). None corresponds to an official table in this project.
* **A survey origin and epoch presented as fact** — `SEAL-01 · 2025-W46 retrace`
  (`fixtures.ts:18`, shown on 13 lines incl. the shell banner `Shell.tsx:70`).
* **Real geography, invented** — a road named `Pune–Nashik Hwy · SH-27`, a rail line named
  `Daund–Manmad line`, and localities `Ambegaon BK` placed on an invented coordinate grid. `[INFERENCE]`
  This is the most dangerous class of fixture here: plausible real-world names attached to coordinates
  no source ever produced.
* **Fabricated ops telemetry** — `p50ms`, `errPct`, `queueDepth`, `status: "DEGRADED"`
  (`fixtures.ts:527–534`), including a service whose p50 is 480 ms and error rate 1.8 %.
* **Fabricated accuracy** — a per-day warm/cold "accuracy" series (`SERIES`, `fixtures.ts:510`) and
  headline `warm 0.914 / cold 0.628` (`fixtures.ts:543`) with sample sizes `warmN 2310 / coldN 1464`
  that belong to no measurement.
* **Fabricated SLAs** — `slaHoursLeft: 48, slaHoursTotal: 48` on every created case
  (`Resolver.tsx:191`, `:206`), then rendered as a burning-down meter (`VerifyQueue.tsx:101–126`).
* **Fabricated people and devices** — officers `S. Jadhav`, `R. Pawar`, `M. Kale`, `A. Shaikh`;
  the signed-in actor `OPR K. Deshmukh` (`session.tsx:41`); devices `GS-07 · u-blox M10`,
  `GS-19 · phone A-GPS`.
* **Fabricated case ids** — `` `VQ-49${…Math.random()…}` `` (`Resolver.tsx:190`, `:205`,
  `Places.tsx:53`).

### 3.1 The gate is re-derived in the browser, on invented thresholds

`Resolver.tsx:23–37` implements its own decision policy:

```ts
if (t1.score < 0.6)            return "UNPLACEABLE — BELOW 0.60 FLOOR"
if (margin < 0.15 && sep > 25) return "CONTESTED — HOLD FOR FIELD"
if (margin < 0.15)             return "COMMIT PERMITTED · SPATIAL CLUSTER"
if (t1.score >= 0.85)          return "AUTO-CONFIRM ELIGIBLE"
return "VERIFY-FIRST RECOMMENDED"
```

Four thresholds (0.60 / 0.15 / 25 m / 0.85) that exist nowhere except this function, and a decision
vocabulary (`AUTO-CONFIRM`, `HUMAN-COMMIT`, `UNPLACEABLE`) that is not the engine's
(`SERVE` / `VERIFY_FIRST` / `REFUSE`). The screen teaches an operator a policy the backend does not
implement. `[VERIFIED]` in the live service these are one gate at `gate-v2`, returned as
`eligibility.{action,reason,rule_version}` — never recomputed client-side.

### 3.2 The uncertainty model is a different model

The prototype publishes **±σ standard error** (`candidate.sigmaM`, `place.sigmaM`, `visit.fix.cepM`)
and a **percentage confidence** (`place.confidence`, rendered with a colour-coded meter at
`Places.tsx:111–153`). The service publishes **a radius with its basis, measured coverage and
calibration n** (e.g. AD002936: 1202.6 m, `empirical_p80`, coverage 79.2 %, n 24) and deliberately
publishes **no confidence percentage**. `[INFERENCE]` Two uncertainty frameworks in one product is
exactly the "second metric framework" failure mode; a σ and a percentile radius are not convertible
without a distributional assumption this project explicitly refuses to make.

### 3.3 The audit ledger is not an audit trail

`session.tsx` maintains an in-memory event list whose "hash" is computed by
`utils.ts:93–107 chainHash(prev, action + detail + Date.now())` — a 16-hex-char, non-cryptographic
mix that **cannot be recomputed** (it hashes the wall clock), seeded with fabricated history
(`session.tsx:51–52`: `"session mounted · fixtures replay window 12–15 Feb 2026"`,
`"EPOCH_PIN · plane SEAL-01 · epoch 2025-W46 retrace"`), stamped with the **browser's local clock**
(`stamp()`, `session.tsx:43–47`) and attributed to a hardcoded actor. It is labelled a
"hash-chained event log" on screen (`fixtures.ts:532`). Nothing here would survive the question
"recompute this chain".

`[INFERENCE]` This is the pattern the project's own rules were written against: the audit surface must
be a **read-only reconstruction computed from stored state**, not a decoration that always agrees with
whatever the UI just did.

### 3.4 To its credit: it does admit, twice, that it is a replay

* The shell carries `demo 0.9.4 · fixture replay` (`Shell.tsx:116`, `:135`).
* Typing anything that is not one of the four pre-baked strings produces
  `FREE-TEXT RESOLUTION NEEDS THE LIVE PIPELINE — THIS DEMO REPLAYS 4 CAPTURED INTAKES.`
  (`Resolver.tsx:250`, `:256`, banner at `:267`).

`[VERIFIED]` That is the honest part, and it is real: the intake **only** matches strings exactly —
it never resolves. The dishonest part is everything around it: the SLA meters, the accuracy series,
the service-health strip and the confidence percentages carry no such label, and they are presented
with the same visual authority as the two admissions.

---

## 4 · Engineering quality

**Good, and worth saying plainly**

* **The seam** (§2) — the single most valuable decision in the codebase.
* **Type discipline**: strict TS, `noUnusedLocals`, `noUnusedParameters`, `noFallthroughCasesInSwitch`,
  a real domain model in `types.ts` (241 lines), discriminated unions for outcomes and codes.
* **No latitude/longitude anywhere** — the model is metres from a declared origin throughout
  (`types.ts:7–10`), which is the right shape and matched the project's constraint.
* **Deterministic jitter**: `mulberry32` (`utils.ts:57`) instead of `Math.random()` for spread — good
  instinct (the only `Math.random()` uses are invented case ids).
* **Cancellation-aware hook**: `useQuery` guards stale responses with a sequence ref (`api.ts:64–73`).
* **Design system**: one palette mirrored for SVG (`utils.ts:9–29`) with a stated reason, real
  primitives (`u.tsx`), consistent spacing/typography, tabular figures for numbers.

**Defects and risks**

| Issue | Where | Consequence |
|---|---|---|
| `useQuery` has no error path — `fn().then(...)` with no `.catch` | `api.ts:65–75` | On a real API, any failure leaves the spinner up **forever**; there is no error state in the whole app |
| Client trusts the browser clock (`new Date()` for ledger stamps) | `session.tsx:43` | Violates the "never trust the device clock" rule any offline-capable field tool must hold |
| Two competing `cn` helpers — one `join`, one `clsx+twMerge` | `lib/utils.ts:3` vs `utils/cn.ts` | `utils/cn.ts` is **dead code** (zero imports); the live one silently drops Tailwind conflict resolution |
| Missing `vite.config.ts` | folder root | Project cannot be built from this folder as-is (§0) |
| No tests, no lint config, no CI | whole tree | Fixture values have no guard; regressions in the gate logic have no net |
| Version ranges | `package.json` | `lucide-react ^1.52.0` and caret ranges resolve differently over time; the committed lock pins them (v1.52.0 / react 19.2.6) but only if `npm ci` is used |
| 447-line map component doing layout, hit-testing, drag, zoom and animation | `LocalPlaneMap.tsx` | `[INFERENCE]` fine at this scale; the SVG-vs-canvas threshold discussion in the UI research register applies if the point count grows |

---

## 5 · What the deployed workbench does with this code

`[VERIFIED]` The integrated application (served at `/` by the Python service) is this codebase, file
by file:

| Files | Fate |
|---|---|
| `index.html`, `src/index.css`, `src/main.tsx`, `src/utils/cn.ts`, `tsconfig.json` | **byte-identical** — the visual identity is untouched |
| `src/lib/fixtures.ts` | **deleted** |
| `api.ts` | rewritten: same function names, real `fetch` to `/resolve`, `/v1/overview`, `/v1/places`, `/v1/evidence`, `/v1/tasks`, `/v1/plane/{town}`, `/v1/geometry/{id}`, `/v1/place/{id}`, `/v1/method-trust`, `/v1/audit/{belief_id}` |
| `Resolver.tsx` | `verdict()` deleted; every decision now read from `POST /resolve` (`eligibility`, `decision_ticket`, typed `reason_codes`, `score_terms`); free-text intake calls the live pipeline |
| `Places.tsx` | confidence % and σ removed; state/tier/radius from `/v1/places` + `/v1/place/{id}`; identity rule shown as the service declares it |
| `VerifyQueue.tsx` | local "close case" replaced by `PATCH /v1/tasks/{id}` and `POST /v1/adjudicate`, with the service's permitted transitions and its receipt |
| `Method.tsx` | invented stages/weights/214 ms replaced by `/v1/method-trust` (real receipts) plus a read-only `/v1/audit/{belief_id}` chain |
| `Overview.tsx` | KPIs from `/v1/overview`; the fake service-health strip and accuracy series removed |
| `session.tsx` | fabricated ledger + fake hash chain removed; a real session as-of clock against the service |
| `LocalPlaneMap.tsx`, `Shell.tsx`, `u.tsx` | **kept, re-fed** — the drawing code is largely the same; its inputs now come from `/v1/plane/{town_id}` and `/v1/geometry/{address_id}` (the maps that used to draw `fixtures.SCENE`) |

Verification of that deployment, re-run today: `reproduce.sh full` exit 0 · 125 pytest · 21/21 HTTP
smoke · **22/22 browser checks** on the workbench · zero console errors, zero 4xx/5xx · the store
unwritten. The no-fake-data guard now scans `battle_model/src` **and** the built bundle, so the
classes of invention catalogued in §3 cannot reappear without failing a test.

---

## 6 · Verdict

**As a design artefact: keep it.** The information architecture, the plane, the candidate↔ticket
relationship and the typographic system are the strongest part of this project's surface, and they
survived integration unchanged.

**As a system: it was a demo, and it says so in exactly two places.** The gap is not the fixtures —
it is that ~20 fabricated operational classes (KPIs, telemetry, accuracy, SLA, confidence, gate
thresholds, providers, provenance) were rendered without the label the other two carried. In a
product whose whole claim is "a mediocre honest number is better than a fake impressive number",
those are the values that had to go first, because they are the ones an operator would act on.

**Nothing in this analysis is a request to change the folder.** It is the source of the deployed
workbench; the deployed copy is the one that matters, and it is already bound to the real service.
If this folder is meant to become the canonical source again — e.g. for a source-of-truth in a
repository — the work is: add `vite.config.ts`, delete `lib/fixtures.ts` and `utils/cn.ts`, and copy
the ported `src/` from the deployment. `[UNKNOWN]` Whether the Drive folder is under version control
elsewhere — the export carries no `.git`.

---

*Evidence for every claim: file and line numbers as cited; hashes and counts re-measured in this
session; commands used — recursive folder listing via the Drive folder endpoint, sha256 comparison
against `uploads/battle_model_zip/`, and line-by-line reads of all 22 files. No file in the folder
was modified; nothing was executed from it.*
