# SUTRA — judge demo script (3 minutes)

As built on 2026-10-08 against the running service, **on the Battle-Model workbench** (the frontend the
service serves at `/`). Every value quoted below is a real response from the runtime at
`as_of = 2026-06-01T00:00:00Z`; the screenshots in `screenshots/` (`bm-*.png`) are captures of these
exact states, taken by `battle_model/tools/browser_smoke.mjs`.

**Pre-flight (30 seconds before you start)**

```bash
cd PS3_SUTRA && python3 tools/serve_runtime.py --port 8000    # prints the frontend it will serve
curl -fsS localhost:8000/health | head -c 120                 # ok:true → go
```

Open `http://localhost:8000/`. The header shows the as-of cut, the plane declaration
(`local metric plane · no lat/lng`) and a **LIVE RUNTIME** chip. The `#/` routes are deep-linkable:
`#/overview`, `#/resolver`, `#/places`, `#/evidence`, `#/queue`, `#/method`.

---

## 00:00 · Overview — "this is a real runtime" (`screenshots/bm-01-overview.png`)

Say: *"Nothing on this screen is mocked. 3,117 addresses indexed, 5,578 observations, 2,757 stored
beliefs, 278 open verification tasks — read live from the service one second ago. The three evaluation
populations are stated separately, never merged; the tier chips are counted, not modelled."*

## 00:15 · Resolve — a messy address (`screenshots/bm-02-resolver-serve.png`)

Click **AD003067** in the demo strip. The address text is the real captured text:
`H.NO. 221, GALI 12, NR COMMUNITY HALL, PATEL NAGAR, DEVGARH NGR`.

Say: *"One address out, one decision in. Ranked arms on the left — eight considered, each with its arm,
its score and its granularity. The plane in the middle is a local metric plane in metres: no latitude,
no longitude, no basemap. The right-hand column is the decision."*

## 00:35 · Candidate selection — cross-highlight (`screenshots/bm-04-cross-highlight.png`)

Click the second row (`memory · 0.917`).

Say: *"The list, the plane and the ticket are one selection — the ring is drawn on the selected arm.
And here is why the alternative lost: not a sentence we wrote, the engine's own typed reason codes —
`lower_arm_prior +0.550 vs +0.620`, `score_margin +0.070000`."*

## 00:50 · Decision ticket (`screenshots/bm-02-resolver-serve.png`, right column)

Say: *"The answer: `field_evidence` at street granularity, tier CONFIRMED, status STABLE. Radius
566.9 metres — and the number underneath is what earns trust: measured coverage 79.2 % at p80 over 24
calibrated addresses, stratum locality. Score 0.987106. The reason rows are typed codes with their
score effects, and they sum to the score. Nothing here is re-derived by the frontend."*

## 01:10 · The stable case, end to end

Scroll the centre column: the **visit timeline** — six real visits with dwell, device note, photo
hashes and reason codes.

Say: *"Three independent confirmations, one independent negative that only caps. This is what good
looks like."*

## 01:30 · Places — history, contradictions (`screenshots/bm-06-places.png`)

Click **Places** → search `AD002936` → open the row.

Say: *"The durable object behind the address. Stored belief versions — the store holds one here and
the panel says so rather than inventing history — the identity rule that gates memory
(`colocation<=30m|adjudicated`), and the contradiction record: two independent negatives, separation
versus threshold, and the line that matters, **coordinate unchanged: true**. Memory is keyed by
colocation, never by account."*

## 01:50 · Verify Queue — a real transition (`screenshots/bm-08-queue.png`)

Click **Verify Queue**.

Say: *"Open verification demand: 84 tasks in T2, all MOVED_SUSPECTED. Facets, filters and cursor
pagination — all server-side."*

Open the `VF-AD002936-MOVED_SUSPECTED` row: recommended action *"Re-visit with a fresh independent
collector"*, clears when *"two clean independent positives"*, and the case history from the service's
own ledger. Click the offered **in progress** transition (`screenshots/bm-09-transition.png`).

Say: *"That was a real `PATCH /v1/tasks/{id}` — an appended lifecycle event, never an edit. The
allowed transitions come from the service, not from the page."*

Then the part that makes it a workbench rather than a dashboard — **record the reviewer's decision**
(`screenshots/bm-10-adjudication.png`): choose `confirmed` / `not true` / `inconclusive`, type a note,
press **Record decision & close case**. The service stores it as an *adjudication observation* — a
reviewer's word, not a visit — and the frozen engine recomputes the belief. The receipt shows the
effect: belief before → after, whether the coordinate moved, the new belief version, and the line
**"never enters S-Eval"**.

Say: *"Nothing here is done in the browser. The decision is an append on the server, the belief is
recomputed by the same engine that answers every other request, and the receipt is returned before
anything is reconsidered — a retried request replays instead of duplicating. On this sandbox the writes
go to a copy of the store; the shipped store is untouched."*

## 02:00 · Resolve AD002936 — contradictory evidence (`screenshots/bm-03-resolver-verify-first.png`)

Click **AD002936** in the demo strip (or resolve the free-text address
`Gali no-11, Azad Mohalla, Devgarh Nagar - 970203` through the intake box — the same live pipeline).

Say: *"Same address, now the hard case. Seven arms considered, and the gate says **VERIFY FIRST** —
negative evidence accumulated past its cap. Radius 1202.6 metres, and it is a **widened** radius —
widening reason `negative_accumulation`. Best-known location, not a confirmed one."*

## 02:30 · The wow — the coordinate never moved

Point at the readout and the plane together.

Say: *"Between the two instants one second apart in field time — `2026-05-30 05:53:45Z` and `:46` —
the radius moved from 566.9 to 1202.6 metres, the tier fell from CONFIRMED to APPROXIMATE, the status
became MOVED_SUSPECTED, a verification task appeared — and the coordinate did not move at all:
1130.5, 2970.0 before and after. **A negative observation can never relocate a coordinate; it widens
and caps, and it has to accumulate.** That is a safety property, and you are watching it hold under a
real transition."*

## 02:45 · Evidence — captured position ≠ location claim (`screenshots/bm-07-evidence.png`)

Click **Field Evidence**, filter to `negative`.

Say: *"Every negative here is kept with the position the collector stood at — `coordinate_claim:
false`, no evidence weight, 'device position only'. The product keeps the testimony and refuses the
claim. The device note says it plainly: 'address nahi mila'."*

## 02:55 · Method & Trust — the honest close (`screenshots/bm-11-method.png`)

Click **Method & Trust**.

Say: *"Three evaluation populations, three numbers, never merged: cold independent 71 % under 500
metres over 100 addresses, median 376; the 31 warm addresses that answered, 96.77 %, median 12.4
metres; product lane 76 %, median 202. There is no 90 % cold-start claim in this project. Every
capability carries one of four labels — implemented, designed, not yet implemented, not measured —
and the learned challenger is evaluated and not adopted."*

Scroll to the **audit chain** on the same screen: the read-only reconstruction for a belief — the
payload hash, the evidence rows with the engine's own weights, the losing alternatives, the tasks.

## 03:00 · Close

Say: *"Messy address in, decision out — with a radius you can defend, reasons you can read, evidence
you can audit, and a refusal that is a first-class answer rather than an error. This is the
Battle-Model workbench: its own design, running entirely on this service's data."*

---

## If something goes wrong on the day

| Symptom | Cause | Move |
|---|---|---|
| The workbench shows an error panel instead of data | the service is not reachable from the page | the frontend has **no fixture fallback** — start the service on the same port; nothing is ever rendered from invented data |
| Plane shows a "not served" panel with no coordinate | you are on AD000002 (the work-life refusal case) | that is the intended state (`screenshots/bm-05-refusal.png`) — the panel names the gate and the reason; pick another demo case |
| A panel reads "loading" for a moment | the fetch is in flight (~1 s) | wait a beat; the workbench never shows another address's data while loading (deliberate) |
| Anything else | — | reload; every screen is deep-linkable: `#/overview`, `#/resolver`, `#/places`, `#/evidence`, `#/queue`, `#/method` |

## Numbers quoted in this script (for verification)

| Value | Where it comes from |
|---|---|
| 3,117 addresses · 5,578 observations · 2,757 beliefs · 278 tasks | `GET /health`, `GET /v1/overview` |
| S-Eval locked reads | `GET /health` discloses the counter (a store value restarted by the deterministic rebuild); the historical ledger of 10 reads with timestamps is in `data/derived/evidence_memory_policy_receipt.json` — reading it never advances it |
| AD003067: CONFIRMED/STABLE, r 566.9 m, coverage 79.2 %, n 24, score 0.987106, 8 arms considered, 3 independent confirmations | `POST /resolve`, `GET /v1/belief/AD003067` |
| alternative lost reasons for `memory` (`lower_arm_prior`, `score_margin`) | `alternatives[0].lost_reason` on the same response |
| AD002936: APPROXIMATE/MOVED_SUSPECTED, r 1202.6 m widened (`negative_accumulation`), 7 arms, task `VF-AD002936-MOVED_SUSPECTED`, belief v7, coordinate 1130.5 / 2970.0 unchanged | `POST /resolve`, `/v1/belief`, `/v1/place/PL-AD002936` |
| flip instants `2026-05-30T05:53:45Z` and `:46Z` | the address's own observation timestamps; the boundary is in the store |
| queue: 84 of 84 T2 MOVED_SUSPECTED | `GET /v1/tasks?town_id=T2&limit=5` |
| frozen evaluation 71 % n=100 median 375.8 · 96.77 % n=31 median 12.4 · 76 % median 202.2 | `GET /v1/method-trust` (read from the receipts) |

---

*Sources:* `[S69]` — the minimum-sample guard behind the radius strata quoted in the ticket (n = 24
locality calibration is why the coverage figure is shown with its stratum); `[S73]` — geocoder error
is heavy-tailed, which is why every answer carries an empirical radius instead of a point; `[S61]` —
append-only, idempotent evidence is why the timeline can be replayed at any instant without the store
changing.
