# SUTRA — frontend demo flow, 2–3 minutes, deterministic (2026-10-08)

One canonical judge journey over **real, replayable records from the frozen store**. Nothing here is
invented: every value in this document was captured on 2026-10-08 by calling the runtime, and every
scene names the exact input and the exact expected output. Where the current API cannot yet produce
what the screen needs, the scene is marked **BLOCKED** with the honest substitute and the P0 item
(from `SUTRA_BACKEND_GAP_AUDIT_2026-10-08.md` §4) that unblocks it. Precision is frozen; the demo
exercises it, never re-tunes it `[S95]`.

---

## 1. Rules of the demo

| Rule | Why |
|---|---|
| Fixed canonical instant: **`as_of = 2026-06-01T00:00:00Z`** (the frozen moment) for every resolve | Deterministic, replayable, and the same cut the product was measured at |
| Fixed request purpose: **`FIELD_NAVIGATION`** for scenes 1–5; `NOTICE_SERVICE` only in scene 7 | Purpose is an input, never inferred; `FIELD_NAVIGATION` does not trigger the work-like refusal |
| Only these 5 addresses are used: `AD003067`, `AD002936`, `AD000004`, `AD000006`, `AD000105`, plus `AD000002` for the purpose refusal | All are real records; none is hand-authored |
| Read-only: no writes, no adjudication, no `/evidence` call during the demo (except the optional offline scene, which writes to a throwaway store) | The demo must not mutate the store or the belief chain |
| Coordinates are **local metric x/y in metres**; no basemap, no lat/lon, no north arrow, no "95 %" | The package has no projection and no road graph; the plane is schematic `[U21]` `[U22]` |
| A refusal is a **designed success state**, shown as a decision, never as an error dialog | The irreversible act is the notice/visit decision `[S55]` |

Total run time: **3 min 15 s** (scenes 0–8; scene 7 and scene 2's alternatives drawer are the two
things to cut if a judge's clock is short — the wow moment and Method & Trust are not). Every scene has a
30-second-delay fallback if the live call is slow — the numbers are constant, so a cached screenshot
is legitimate *provided the caption states the as-of instant*.

---

## 2. The fixtures (all captured, all real)

| # | Address | Text (as in the index) | Town | Canonical outcome at the frozen instant |
|---|---|---|---|---|
| A | `AD003067` | `H.NO. 221, GALI 12, NR COMMUNITY HALL, PATEL NAGAR, DEVGARH NGR` | T2 | `CONFIRMED/STABLE` → gate **SERVE** (`purpose_home_like`) |
| B | `AD002936` | `Gali no-11, Azad Mohalla, Devgarh Nagar - 970203` | T2 | `APPROXIMATE/MOVED_SUSPECTED` → gate **VERIFY_FIRST** (`negatives_accumulated`) |
| C | `AD000004` | `#81 gali 10 ganesh mandir ke bagal mein krishna puri devgarh nagar - 970202` | T2 | `APPROXIMATE/STABLE` → gate **VERIFY_FIRST** (`tier_approximate`), cold |
| D | `AD000006` | `Village Rampura Kalan, Tehsil D, District South - 996281` | OUT | `UNPLACEABLE` → gate **REFUSE** (`purpose_other`), **no candidate at all** |
| E | `AD000002` | `no. 173 12th cross 3rd main shanthi nagar kaveripura - 960101` | T1 | `APPROXIMATE/STABLE`, gate **REFUSE** (`purpose_work_like`) under `NOTICE_SERVICE` |
| F | `AD000105` | — | T2 | queue row `VF-AD000105-MOVED_SUSPECTED`, priority 0.8, `negatives_independent=2` |
| G | `AD002936` (again) | — | T2 | queue row `VF-AD002936-MOVED_SUSPECTED`, priority 0.8, `at 2026-05-30T04:45:54Z` |
| H | town `T2` | — | — | offline pack `pack-T2-7247f0bd3d96`, 952 addresses, 77 landmarks, 12 localities, valid until `2026-06-08T00:00:00Z` |

Belief trajectories used in scene 4 were recomputed at each real visit instant (before the visit,
strict `observed_at < as_of`): `AD003067` 8 observations, `AD002936` 9 observations.

---

## 3. The script

### Scene 0 — cold open: the workbench, not a dashboard (0:00–0:15)

**On screen:** the two-pane workbench; top bar shows runtime status: `online`, `as_of
2026-06-01T00:00:00Z`, store `sutra-1.0`, engine versions `candidate-rules-v2` ·
`evidence-policy-v3` · `radius-map-v1` · `gate-v2`, and the pack chip `pack-T2-7247f0bd3d96`
(valid until 2026-06-08).

**Endpoint today:** `GET /health` returns `{ok, versions, store.meta()}` — versions are real, the
pack chip and the offline gauge are not there yet → **P0-7**.
**Say:** "Every number on this screen is versioned. If the radius map changes, this bar changes."

### Scene 1 — the serving ticket (0:15–0:45)

**Input:** `POST /resolve {address_id: AD003067, request_purpose: FIELD_NAVIGATION, as_of: 2026-06-01T00:00:00Z}`

**Exact values on the ticket (all real):**

| Field | Value |
|---|---|
| gate | `SERVE` · reason `purpose_home_like` |
| tier / status | `CONFIRMED` / `STABLE` |
| coordinate | `x 1390.0  y −1818.0` · `granularity: street` · `coordinate_space: sutra_local_metric_plane:T2` |
| candidate | `c-28f5aface67c` · arm `field_evidence` · `source_ref visits:median(3)` · `as_of_valid 2026-05-15T05:35:37Z` · `licence_class official` |
| radius | **566.9 m** · basis `empirical_p80` · n = 24 · measured coverage **0.792** · stratum `locality` · `widened: true` (`negative_accumulation`) |
| support | 6 observations · 4 positive · 1 independent negative · 3 independent confirmations · positive weight 2.798487 |
| reason codes | `cross_arm_agreement`, `field_confirmed_x3`, `negatives_independent=1`, `promotion:ok`, `resolution:exact_text_match` |
| score | 0.987106 — shown only in the "why" drawer, never as a headline |
| direction cue | `Community Hall ~1170 m, bearing SW, near it` — **flagged `ambiguous: true`** |
| belief version | 7 |

**Say:** "Radius is not a promise; it is the p80 of measured error for 24 addresses in this stratum,
and we show the n and the coverage with it. It is already widened because one independent visit
failed to trace the address — and the coordinate did not move because of it."

**Backend part: shipped.** The ring payload is `rings[0]` of `GET /v1/geometry/AD003067?as_of=…`
(centre, `radius_m 566.9`, basis, n, coverage, `authoritative: true`). Drawing it is frontend work.

### Scene 2 — why not the others (0:45–1:05) — **BLOCKED (partial)**

**What the judge should see:** the 2nd–4th candidates with their scores and one phrase each for why
they lost (`coarser_granularity`, `no_promotion_credit`, `memory_not_evidence_derived`, …).

**What exists today:** `arms_considered[]` — **8** entries for `AD003067`, **7** for `AD002936`,
**3** for the cold `AD000004`, each `{arm, candidate_id, score, primary_eligible, reasons[]}`. Real
runner-up on screen for A: the **memory** arm at 0.917106 with `primary_eligible: true`, i.e. a
second servable-grade candidate that is not the winner. That is real material, but the rows carry no
coordinate, no granularity and no "lost" vocabulary → **P0-2**.
**Backend part: shipped.** `resolve.alternatives[]` returns the ranked losers with `lost_reason`
(for `AD003067` the runner-up is the `memory` arm at 0.917106, losing on `lower_arm_prior` and
`score_margin +0.070000`).
**Never do:** re-rank in the browser, invent a percentage, or display a losing candidate as if it
were servable.

### Scene 3 — a cold address is not a guess (1:05–1:25)

**Input:** `POST /resolve {address_id: AD000004, FIELD_NAVIGATION, as_of 2026-06-01T00:00:00Z}`

`APPROXIMATE / STABLE` · gate **VERIFY_FIRST** (`tier_approximate`) · candidate `c-bb1142e5551f`
arm `frozen_baseline` · granularity **`locality`** · `x 2775.9  y −1262.8` · radius 809.8 m
(basis `empirical_p80`, n 24, coverage 0.792) · `support: 0 observations` · reason codes
`cold_start_no_field_evidence`, `promotion:not_ok` · `resolution: exact_text_match`.

**Say:** "Zero field evidence. The system returns the frozen baseline at locality granularity and
refuses to dress it up: no field count, no promotion, and the gate says verify before you act."

### Scene 4 — the negative that must not move a place (1:25–2:00) — the centrepiece

**Input:** stub the belief rail with `as_of` stepping over the real visit instants of `AD002936`
(all values recaptured on 2026-10-08):

| as_of (state *before* that visit) | visit | evidence | tier / status | radius | candidate |
|---|---|---|---|---|---|
| 2026-04-04T05:39:09Z | `obs-VS000244` | `address_not_traceable` (negative) | APPROXIMATE / STABLE | 809.8 | `c-503cfcf760dd` locality |
| 2026-04-16T04:32:58Z | `obs-VS000969` | `locked_premises` (ambiguous) | APPROXIMATE / STABLE | 850.3 | `c-503cfcf760dd` |
| 2026-04-27T05:33:42Z | `obs-VS001649` | `met_borrower` (positive) | APPROXIMATE / STABLE | 850.3 | `c-503cfcf760dd` |
| 2026-05-07T05:14:44Z | `obs-VS002307` | `met_family` (positive) | **PROBABLE** / STABLE | 708.6 | `c-503cfcf760dd` |
| 2026-05-20T05:53:45Z | `obs-VS003098` | `address_not_traceable` | **CONFIRMED** / STABLE | 566.9 | `c-a7fcc592cd99` rooftop |
| 2026-05-30T04:45:53Z | `obs-VS003745` | `locked_premises` | **APPROXIMATE / MOVED_SUSPECTED** | **1202.6** | `c-a7fcc592cd99` |
| 2026-06-09T06:58:55Z | `obs-VS004322` | `locked_premises` | APPROXIMATE / MOVED_SUSPECTED | 1202.6 | `c-a7fcc592cd99` |
| 2026-06-19T05:59:04Z | `obs-VS004962` | `address_not_traceable` | APPROXIMATE / MOVED_SUSPECTED | 1202.6 | `c-a7fcc592cd99` |
| 2026-06-29T06:20:31Z | `obs-VS005535` | `met_family` (positive) | APPROXIMATE / MOVED_SUSPECTED | 1257.3 | `c-a7fcc592cd99` |

At the canonical instant: `APPROXIMATE / MOVED_SUSPECTED`, gate `VERIFY_FIRST`
(`negatives_accumulated`), radius 1202.6 m, `c-a7fcc592cd99`, rooftop, `x 1130.5  y 2970.0`,
support 2 positive / 2 independent negative, reason codes `negative_accumulation_cap`,
`negatives_independent=2`.

**Say (the line that must be said exactly):** "Two independent visits said *not traceable*. The
place was **not** moved and the coordinate was **not** replaced — the radius widened from 566.9 m to
1202.6 m, the tier dropped from CONFIRMED to APPROXIMATE, and the address entered the verification
queue. A negative observation has zero evidence weight and carries no coordinate of its own; it can
raise doubt, never author a location."

**Why this is the centrepiece:** it is the frozen rule ("one negative never relocates a place")
made visible in nine real rows, and it is the exact behaviour a judge can try to falsify.

**Backend part: shipped.** `GET /v1/belief/AD002936?as_of=…` returns the authoritative object for any
instant, so the rail can step through the nine real visit points; the same values can still be obtained
from repeated `resolve(..., as_of=…)` calls.

### Scene 5 — the queue is the product (2:00–2:20)

**Input today:** `GET /tasks/verify-first?town_id=T2&limit=…` → **84** rows in T2 (**96** in T1,
**98** in T3: 93 `MOVED_SUSPECTED` + 5 `CONTESTED`).

**Row anatomy (all fields real):** `task_id` `cause` `state` `priority` `negatives_independent`
`tier` `status` `radius_m` `rule_version` `at` `place_id` `town_id`.
Show row G: `VF-AD002936-MOVED_SUSPECTED`, `at 2026-05-30T04:45:54Z`, priority 0.8,
`negatives_independent 2`, radius 1202.6, `state: open`; then row F:
`VF-AD000105-MOVED_SUSPECTED`, priority 0.8, radius 1202.6, town T2.

**Say:** "A place does not get quietly edited. It gets a task with a cause, a priority, the evidence
that raised it, and a rule version — and the correction, when it comes, is a new version, never an
overwrite."

**Backend part: shipped.** `GET /v1/tasks?town_id=T2&cause=&state=&limit=&cursor=` returns rows with
`recommended_action`, `clears_when` and `evidence_refs`, plus `facets.by_cause`. What is still P1 is
*acting* on a row: `state` is `open` for every task today (P1-3 transitions, P1-2 adjudication).

### Scene 6 — refusal, twice, as design (2:20–2:40)

**(a) No candidate.** `AD000006` → `tier: UNPLACEABLE`, candidate `null`, gate `REFUSE`
(`purpose_other`), support all zeros, `status STABLE`, and **no coordinate field anywhere in the
body**. Say: "We do not have a place here. You get a decision, not a dot."

**(b) Wrong purpose.** `AD000002` under `NOTICE_SERVICE` → `REFUSE` (`purpose_work_like`) with
`APPROXIMATE/STABLE` and a frozen-baseline street candidate. **Contract hygiene note:** the current
payload still carries `candidate.x/y` here. The v1 envelope must emit `coordinate` only when the
gate is `SERVE`/`VERIFY_FIRST`, and the UI must never render or export a coordinate from a refusal
(**P0-1**). Say: "The notice decision needs a SERVE-grade place. This address is not one, so the
system refuses the action rather than shipping a plausible dot."

### Scene 7 — offline and auditability (2:40–2:45, optional if time is tight)

Pack chip H: `pack-T2-7247f0bd3d96`, 952 addresses, 77 landmarks, 12 localities, 1,774,492 bytes,
valid until `2026-06-08`, `contains_truth: false`, `contains_evidence: false`,
`contains_polygons: false`. Device outbox and idempotent replay are already implemented
(`sutra/offline.py`; acceptance T9). If the judge asks "what happens with no signal?", the answer is
a working outbox and a pending counter, not a spinner → `GET /health.offline{}` +
`gauges{}` ship today; device-reported pack age is **P1-6**.

### Scene 8 — Method & Trust, and the 30-second wow (3:05–3:15)

**On screen:** the Method & Trust page (Screen F). Show, top to bottom: the nine version strings; the
gate table with live reason strings; the radius map (`locality` p80 539.9 m, n 24, coverage 0.792,
publishable — `street`/`pincode` withheld under the n≥15 guard); the **five invariants**; the **two
loops** with their honest status labels (Fast loop **IMPLEMENTED**; Slow loop step-by-step, with the
learned challenger labelled **EVALUATED, REJECTED — not in the request path** and model promotion
**NOT YET IMPLEMENTED**); `contains_truth: false` on the shipped pack; and the **three measured
figures with their captions**: cold independent `<500 m 71 %` (n 100, median 375.8 m), warm subset
**`96.77 %` with "31 answered"** (median 12.4 m), product lane `76 %` (median 202.2 m), all with the
frozen config hash `ac61cf2e71f77454…`.

**Say (exact):** "Three numbers, three populations, and they are never interchangeable: the cold
independent evaluation is 71 % under 500 m; the warm field-confirmed subset — **31 answered** — is
96.77 %; the product lane, cold and warm together, is 76 %. S-Eval was never trained or tuned on, and
the learned ranker we evaluated did not clear the bar, so the rule ranker is what you just watched."

**Blocked part:** none of the *content* is blocked — it is static text plus `GET /health`. The page
that renders it needs the `MethodTrust` DTO (contract §19); until then a static appendix page is an
honest substitute.

---

### The 30-second wow moment (rehearse this as a standalone clip)

Start a stopwatch and run **scene 4 alone**, cut to its essence:

> **0:00** Open `AD002936` at `as_of 2026-06-01`. Ticket reads `APPROXIMATE / MOVED_SUSPECTED`,
> `VERIFY_FIRST`, radius **1202.6 m**, candidate `c-a7fcc592cd99` at `x 1130.5 y 2970.0`.
> **0:08** Step the belief rail backwards through the nine real visit instants: `809.8 → 708.6
> (PROBABLE) → 566.9 (CONFIRMED) → 1202.6 (MOVED_SUSPECTED)`.
> **0:18** Point at the coordinate: **it never changes across any of those steps.**
> **0:24** Read the two negatives: `address_not_traceable`, zero evidence weight, no coordinate claim.
> **0:30** Stop. "Doubt moved the radius, the tier and the queue — not the place."

That is the differentiator in one sentence and it is 100 % real behaviour, replayable from the store.

---

## 4. BLOCKED board — **updated after P0 shipped (2026-10-08)**

The backend blocks listed here in the first edition are implemented. This table says what is *still*
blocked. Frontend rendering is not a backend gap: the payloads exist.

| Scene | Still blocked | Why | Unblocked by |
|---|---|---|---|
| 1, 3, 4 | drawing the ring/plane in the browser | the payload ships (`GET /v1/geometry/{id}`); the renderer does not exist | frontend build (SVG) — no backend work |
| 4 | belief-version stepping as a control | `GET /v1/belief/{id}?as_of=` ships; the rail is a frontend control | frontend build |
| 5 | acting on a queue row (accept / reverify / mark unresolved) | transitions are P1 | P1-2, P1-3 |
| 5, 6 | recording a review decision | no adjudication write path | P1-2 |
| 7 | offline status chip with pack age | `/health` ships the metadata; the chip is frontend | frontend build (+ P1-6 for device-reported age) |
| any | single-call audit chain | reconstructable from four endpoints, but no `GET /v1/audit/{belief_id}` | P1-4 |
| 2 | `memory_not_evidence_derived` losing reason | in the vocabulary; needs candidate provenance on the wire | P1 provenance passthrough |

**No longer blocked:** alternatives with losing reasons · typed reason codes · the radius ring payload ·
per-visit evidence with weights and reason codes · place versions and contradictions · queue filters,
facets and cursor · refusal envelopes with no coordinate · health/runtime status.

### 4.1 First-edition board (closed, kept for the record)

| Scene | Formerly blocked element | Shipped | Pinned by |
|---|---|---|---|
| 1, 3, 4 | radius ring on the plane | `GET /v1/geometry/{id}` — ring, points, extent, metres | `test_contract_geometry_is_local_metric` |
| 2 | `alternatives[]` with `lost_reason` | `resolve.alternatives[]`, ranked, vocabulary-checked | `test_contract_alternatives_are_the_ranked_losers` |
| 4 | belief-version read | `GET /v1/belief/{id}?as_of=` | `test_contract_belief_read_is_the_authoritative_object` |
| 4 | per-visit evidence rows | `GET /v1/address/{id}/observations` | `test_contract_observations_are_ordered_and_typed` |
| 5 | filters, facets, `recommended_action` | `GET /v1/tasks` (+ cursor, + `evidence_refs`) | `test_contract_task_filters_and_facets` |
| 6 | refusal envelope with no coordinate | `coordinate: null`, no `uncertainty`, no geometry | `test_contract_refusal_*` (three tests) |
| 7 | health / runtime status | `GET /health` + packs, gauges, digests, counters | `test_contract_health_is_operational_metadata_only` |
| 1, 2, 4, 6 | typed reason codes | `resolve.reason_codes[]` (`kind/subject/effect`) | `test_contract_reason_codes_typed_and_additive_to_score` |


## 5. Rehearsal (all read-only, ~2 minutes)

```bash
# versions and runtime
python3 -c "import json,sys; sys.path.insert(0,'.'); import tools.serve_runtime" 2>/dev/null || true
python3 tools/serve_runtime.py &            # binds 0.0.0.0:8000
curl -s localhost:8000/health | head -c 400
# the three canonical resolves
curl -s -X POST localhost:8000/resolve -H 'content-type: application/json' \
  -d '{"address_text":"H.NO. 221, GALI 12, NR COMMUNITY HALL, PATEL NAGAR, DEVGARH NGR","town_hint":"T2","request_purpose":"FIELD_NAVIGATION","as_of":"2026-06-01T00:00:00Z"}' | head -c 600
# the queue
curl -s 'localhost:8000/tasks/verify-first?town_id=T2&limit=5'
# the plane-ready pack
curl -s localhost:8000/packs/T2
# the v1 read surface (P0, shipped)
curl -s 'localhost:8000/v1/belief/AD003067?as_of=2026-06-01T00:00:00Z' | head -c 400
curl -s 'localhost:8000/v1/address/AD002936/observations?as_of=2026-06-01T00:00:00Z' | head -c 400
curl -s 'localhost:8000/v1/tasks?town_id=T2&limit=5'
curl -s 'localhost:8000/v1/geometry/AD003067?as_of=2026-06-01T00:00:00Z' | head -c 400
curl -s 'localhost:8000/v1/plane/T2' | head -c 300        # town reference geometry (backdrop)
curl -s 'localhost:8000/v1/plane/address/AD003067?as_of=2026-06-01T00:00:00Z' | head -c 200
```

Expected: `AD003067` → `SERVE` / `purpose_home_like` / radius `566.9`; `AD002936` → `VERIFY_FIRST` /
`negatives_accumulated` / radius `1202.6`; `AD000004` → `VERIFY_FIRST` / `tier_approximate` /
`809.8`; `AD000006` → `REFUSE` / `purpose_other` / candidate `null`. If any of these differ, **stop
and re-audit** — the store or a version changed, and the demo script must be re-derived, never
adjusted by hand.

---

## 6. Judge Q&A (answer length: two sentences)

1. **"Is the coordinate a real GPS point?"** No — it is x/y in a local metric plane in metres,
   medians of captured visit coordinates, and the UI never shows a basemap because the package has
   no projection.
2. **"Why should I believe 566.9 m?"** It is the p80 of measured error for 24 addresses in the
   `locality` stratum with coverage 0.792; where n < 15 the stratum is withheld and the answer falls
   back `[S69]`.
3. **"What happens if a visit says the address doesn't exist?"** The radius widens, the tier drops,
   a task is raised — and the coordinate stays exactly where it was.
4. **"Can a bad visit wreck a good place?"** One negative cannot relocate anything; two independent
   negatives trigger the widening cap and the queue, never a new coordinate.
5. **"How do you avoid circularity?"** Evidence and memory arms are kept out of the cold lane, and
   the surveyed truth is firewalled from every training and tuning path (`split_receipt.json`).
6. **"Is the machine learning doing this?"** No model is trained in this runtime: candidates come
   from eight declared official arms with a rule ranker; the frozen policy experiment is a separate,
   versioned artefact.
7. **"What if the staff never return?"** Then the radius never shrinks for that address; the answer
   stays at the frozen baseline locality granularity and the gate keeps saying verify first.
8. **"Where does the truth live?"** In the field visits, append-only; belief is a pure function of
   the store at an instant, so any past answer can be recomputed byte-identically.
9. **"What stops the system from editing the map silently?"** There is no coordinate-edit control in
   the interface at all; corrections are new versions plus an audit event.
10. **"What is the single most important screen?"** The verification queue — it is where a fragile
    belief becomes an action instead of a wrong visit.

**Do not say:** lat/lon, GPS accuracy guarantees, "95 % confidence", any accuracy percentage inside
the workbench, ticket or queue, rupee savings, "eliminates field visits", "the AI learns",
"production-ready", "90 % guaranteed", "100 % accurate", or any number that is not in this
document. The **only** three figures that may ever be spoken are the labelled ones in scene 8 —
and only with their populations and the "31 answered" qualifier.

**The one sentence that must never be mangled:** "96.77 % is 31 warm field-confirmed addresses in
the independent evaluation, not the product's general accuracy."


---

## 6. As built — the console exists (2026-10-08)

The blocked board in §4 is now fully closed for this edition: every scene in this flow is executable
against the shipped console. The screen-by-screen script with exact clicks, quoted values and
screenshots is `SUTRA_JUDGE_DEMO_SCRIPT_2026-10-08.md`; the captures live in `screenshots/`.

What changed in the runtime of the demo: the console is served by the same process as the API, so the
rehearsal is one command —

```bash
python3 tools/serve_runtime.py --port 8000     # then open http://localhost:8000/
```

Two additions landed since this flow was written and are worth rehearsing: the **belief replay strip**
on Resolve (each column is one real `GET /v1/belief/<address>?as_of=…`, so the as-of transition can be
driven from the UI rather than by editing the field), and the **refusal state** as a first-class screen
including the suppressed-plane notice for a work-like place.
*Sources: interface research `[U1]`–`[U24]` in `SUTRA_UIUX_RESEARCH_SOURCES_2026-10-08.md`
(especially `[U6]` centre-of-circle reading, `[U7]` coincident symbols over legends, `[U20]` N-best
alternatives, `[U21]` "not to scale" as a property, `[U23]` SVG threshold); package register rows
`[S55]` `[S69]` `[S81]` `[S82]` `[S95]`. Contracts: `SUTRA_FRONTEND_BACKEND_CONTRACT_V1_2026-10-08.md`.*
