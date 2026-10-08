# SUTRA — product UX specification (2026-10-08)

The interface contract that the frontend and the next backend task are built against. Screens,
interactions, states and the judge journey. Data contract in
`SUTRA_FRONTEND_BACKEND_CONTRACT_V1_2026-10-08.md`; research basis in
`SUTRA_UIUX_FRONTEND_RESEARCH_2026-10-08.md`; what exists today in
`SUTRA_BACKEND_GAP_AUDIT_2026-10-08.md`.

---

## 1. Product thesis

SUTRA is an **address-resolution and field-operations control room**. One sentence a judge should
believe after 30 seconds: *this system answers with a place, says how far off that answer is
empirically known to be, shows the field evidence it learned it from, and refuses when it cannot
justify a point.*

Three product consequences, chosen deliberately:

1. **The answer is a decision object, not a dot.** Candidate + granularity + tier + radius (with its
   calibration basis) + reason codes + gate action travel together, always.
2. **Abstention is a first-class outcome.** `no candidate → no coordinate` is rendered as a designed
   state with a reason, never as an error toast `[S73]` `[U18]`.
3. **Learning is visible, and it is slow on purpose.** A visit moves a belief; two independent
   negatives widen it and mark it `MOVED_SUSPECTED` **without moving the coordinate** — the UI must
   make that asymmetry obvious.

What it is not: not a chatbot, not a KPI dashboard, not a map product, not "AI magic" `[U18]`.

---

## 2. Users and jobs

| Actor | Job | Screen it lives in |
|---|---|---|
| **Field agent** (mobile, intermittent connectivity) | "Where exactly do I go, and what do I record when I get there?" | Resolver (read-only card) + Field capture |
| **Ops reviewer / verifier** | "Which addresses need attention this week, and what is the safest action?" | Verification queue → Resolver → Place history |
| **Auditor / compliance** | "Why did the system answer this, on what evidence, under which rule versions?" | Audit / Evidence timeline |
| **Judge** | "Does this thing do something real, honestly?" | The 2–3 minute demo journey (`SUTRA_FRONTEND_DEMO_FLOW_2026-10-08.md`) |

---

## 3. Shell

**Primary navigation — six destinations, and no more.** The five mandated destinations keep their
exact names and jobs; `Operations` is added as the landing surface the other five funnel into (it is
the only page that shows town-level counts, and the demo opens there). Each destination is one page,
one responsibility, one primary endpoint:

| Destination | Screen | Responsibility (the one question it answers) | Primary endpoint |
|---|---|---|---|
| `Resolve` | B | "What do we do with *this* address, and why?" — the three-zone workbench | `POST /v1/resolve` |
| `Places` | C | "What do we durably know about this place, and where did it come from?" | `GET /v1/place/{id}?as_of=` |
| `Evidence` | D | "What did the field actually observe, and what did each observation do?" | `GET /v1/address/{id}/observations` |
| `Verify Queue` | E | "Which places need a human decision next, and what is the action?" | `GET /v1/tasks` |
| `Method & Trust` | F | "What is the system allowed to do, and what has it actually measured?" | `GET /v1/health` + static |
| `Operations` | A | "What is the state of the operation right now?" (landing) | `GET /v1/overview` (P1) |

No dashboard grid of twelve widgets, no settings page, no user-management page, no billing, no
"insights" tab. Cross-navigation is by id: every place, address, belief version, task and observation
is a link, and the command palette reaches all of them from anywhere.

**Persistent context bar** (top): town selector (`T1|T2|T3`), purpose selector
(`FIELD_NAVIGATION` / `NOTICE_SERVICE` / `VISIT_PLANNING` / `PORTFOLIO_REVIEW` / `AUDIT`), **`as_of`
control** (a real timestamp input, defaulting to the current cut; every read response echoes it), and
the **runtime-status chip**.

**Runtime-status chip** shows, from live state: connection (`online|offline`), outbox depth
(`n pending`), last successful sync, pack version and pack age for the selected town. It is the one
element that never hides on small screens `[U9]` `[U11]`.

**Command palette** (`⌘K` / `Ctrl-K`): resolve an address, jump to an address id, open a queue by
cause, switch `as_of` to a named cut, open the method page. Every command runs a real backend call
`[U1]` `[U2]`.

**Keyboard map** (documented in-product, because the primary user is a frequency user `[U2]`):
`⌘K` palette · `/` focus address input · `j`/`k` next/previous row · `Enter` open decision ·
`o` open on plane · `a` alternatives · `e` evidence chain · `[`/`]` previous/next belief version ·
`Esc` back. All list + detail navigation is operable without a mouse.

**Layout grammar.** Workbench screens are three panes on wide viewports (list · decision · plane),
collapsing to list → detail on narrow ones. Detail is a **pane**, not a modal, so a reviewer can keep
the queue in view `[U12]`. Two disclosure levels maximum: decision summary, then evidence/audit
detail `[U13]` `[U14]`.

**Visual semantics (fixed vocabulary).**
- Tier: `CONFIRMED` (strong), `PROBABLE` (medium), `APPROXIMATE` (weak), `UNPLACEABLE` (none).
- Status: `STABLE`, `CONTESTED`, `MOVED_SUSPECTED`, `STALE` — always shown beside tier, never merged
  into one badge.
- Evidence polarity: **positive** (learned the place), **ambiguous** (partial), **negative**
  (process/location complaint that can demote but never relocate). Polarities use different symbols,
  not only different colours.
- Numbers: distances in whole metres with the unit in the label, radii always with their `basis`.
- No colour is the sole carrier of meaning (accessibility) and no gauge/percentage represents
  anything except a directly measured quantity.

---

## 4. Screen A — Overview / Operations

**Goal.** Answer "what is the state of this town's address intelligence right now?" in one glance,
then get out of the way.

**Primary information.** Addresses covered by town; **cold vs warm split** (an address with ≥1
observed visit vs none); tier mix among evidence-bearing addresses; open verification count by
cause; pack version/age; the `as_of` the numbers were computed at. All are counts derived from the
store at `as_of` — no estimates, no percentages without a denominator on screen.

**Secondary.** Recent belief changes (newest first, address + old→new tier/status); queue ageing.

**Actions.** Jump into the workbench with a filter ("open all `MOVED_SUSPECTED` in T2"); open a queue
by cause; download the town pack (existing `GET /packs/{town_id}`).

**States.** *Empty*: "no evidence-bearing addresses in this town yet — cold-start numbers only."
*Loading*: skeleton rows with the count placeholders distinctly styled (never fake numbers).
*Refusal/stale-offline*: last-known snapshot with an explicit "as of <time>, offline" stamp.

**Live vs derived.** Live: counts, queue depth, pack metadata. Derived: tier mix (recomputed per
`as_of`), cold/warm split. Nothing is sampled or projected.

**Endpoint.** `GET /v1/overview?town_id=&as_of=` (new; P1 — the underlying counts exist via store
queries and `verify_first_tasks`).

---

## 5. Screen B — Resolver workbench (the core screen)

**Goal.** Resolve one address and justify the answer completely.

**Layout (three panes + one strip).**

*Left — context and input.* Address text input (single field, one real example as placeholder
`[U24]`), optional `town_id`, purpose selector, `as_of` chip, and the resolution method returned by
the backend (`exact_text_match`, `fuzzy_token`, `area_context:<locality>`, `address_id_given`) shown
as provenance, not decoration. Below: the identity block — `address_id`, `place_id`, town, address
type, account link status ("exposure link only — never a coordinate source" `[S95]`).

*Centre — decision and alternatives.* The selected candidate card: arm (`field_evidence` /
`frozen_baseline` / `locality_centroid` / …), granularity, score with its additive
`score_reasons[]`, `belief_version`, `as_of`, and the **eligibility action as the headline**. Then
the **alternatives list**: every other candidate that was generated, with its own arm, granularity,
score and the reasons it lost. Alternatives are the interface form of "we are not certain"
`[U19]` — this is why `alternatives[]` is a contract requirement.

*Right — the plane* (see §9 of the contract): the selected candidate at its true metric position,
alternatives as hollow points, field-evidence observations as small glyphs coloured by polarity, the
radius ring at true scale, locality context ring, and — when present — contradiction markers. Zoom and
pan are in metres; the scale bar reads "1 grid = 250 m".

*Bottom strip — decision ticket.* A single dense row the UI can render without deriving anything:
`tier · status · granularity · radius_m (+basis, n_calibration, measured_coverage) · evidence count ·
independent confirmations · negatives · belief_version · as_of · gate action + reason · rule
versions`. Clicking it expands to the full ticket (two-level disclosure).

**States.**
- *Empty (no text)*: the input keeps focus; the panes show the last resolved address or a neutral
  "resolve an address to begin".
- *Loading*: candidate skeleton with `as_of` already shown; controls disabled, not hidden.
- *Refusal*: `candidate: null` → the centre pane shows **"No candidate → no coordinate"** with
  `reasons[]` (`no_candidate`, `no_match_in_address_book`, `area_context_locality_only`), the gate
  action (`VERIFY_FIRST|REFUSE`), and the area-context payload if one exists (a locality is offered
  as *context*, clearly not as an address coordinate). The plane shows the town/locality context
  rings only. This state must look deliberate — it is a success `[U18]`.
- *Area context*: `is_area_context: true` → the candidate is labelled "locality-level context",
  granularity `locality`, and the headline action is typically `VERIFY_FIRST`.
- *Stale/offline*: banner "resolved from pack `pack-T2-…`, downloaded <time>; evidence after that
  date is not included" — the offline device's own truth.
- *Error*: transport/500 → "the runtime did not answer; nothing was written" + a copyable request id.
  No partial decision is ever rendered.

**Live vs derived.** Candidate set, belief, radius, gate: all derived server-side at `as_of`. Nothing
on this screen is computed by the frontend except layout.

**Endpoint.** `POST /v1/resolve` (implemented, must be extended — see the gap audit).

---

## 6. Screen C — Place intelligence / memory

**Goal.** Show what the system *knows* about one place, and what it has learned over time.

**Primary.** The current belief card (tier/status/radius/gate), the **belief-version timeline** (each
version with its `as_of`, candidate, tier, status, radius and the visit that moved it), the evidence
that produced each change, and the place's member addresses + the identity rule
(`colocation<=30m|adjudicated`).

**Secondary.** Contradictions (`CONTESTED`, `MOVED_SUSPECTED`) with the separating observations;
`merge_review` state; the "state is a projection" banner — the panel states plainly that the belief
is recomputed from the append-only observations, and offers a re-read at any `as_of` `[U15]`.

**Actions.** Step through belief versions (`[`/`]`); open the observation that caused a change; open
the audit chain; raise a verification task (P1).

**States.** *Empty (no evidence)*: cold-start card showing the static answer with `APPROXIMATE` and
the pin/locality provenance. *Loading*: timeline skeleton. *Refusal*: n/a. *Stale/offline*: timeline
truncated at pack time with an explicit stamp.

**Live vs derived.** The place read model is a **projection** (explicitly named as such by the
runtime) — the UI must not present it as a stored fact.

**Endpoint.** `GET /v1/place/{place_key}?as_of=` (also served at `/place/{id}`; since 2026-10-08 both
carry `versions[]`, `contradictions_detail[]` and `unplaced`) and
`GET /v1/place/{place_key}/history?as_of=` (design only; the store already holds belief versions).

---

## 7. Screen D — Field evidence / visit timeline

**Goal.** Make one visit legible: what was observed, how much it was trusted, what changed.

**The learning pattern (the five beats, 10–20 s to comprehend).**

```
BEFORE                OBSERVED                 EVIDENCE QUALITY            BELIEF AFTER            WHY
belief card at        observation card:        weight w + reason codes     belief card at the      the diff, in words
t-1: tier/status/     outcome, observed_at,    with positive/ambiguous/    observation instant:    ("2nd independent
radius/candidate     agent, GPS ±m, dwell,    negative polarity, and      tier/status/radius/     confirmation →
                      media hash, trail         whether it counted as an    candidate               PROBABLE"),
                      agreement                 independent confirmation                           plus what did NOT move
```

Each beat is one card in a horizontal strip, connected by the observation id — clicking any card
opens its raw JSON. The strip is generated from two beliefs computed at real `as_of` instants, so it
cannot be faked: the numbers come from the same function the product uses.

**Negative evidence design (mandatory).** A negative observation renders with a distinct glyph,
carries `w = 0.0` and the reason `negative_no_coordinate_claim`, and its card states: *"this
observation cannot move the coordinate; it can only demote and widen."* When the second independent
negative lands, the "after" card shows tier `CONFIRMED → APPROXIMATE`, status `STABLE →
MOVED_SUSPECTED`, radius `566.9 → 1202.6 m` and the candidate **unchanged** — with the widen reason
`negative_accumulation` on the ring `[S73]` `[U6]`.

**Actions.** Replay the visit at real time; open the agent's other observations; open the verification
task it created.

**States.** *Empty*: "no field visits recorded for this address — cold." *Loading*: cards in
sequence-skeleton. *Refusal*: n/a. *Offline*: local-only visits appear with a "queued" badge and a
local sequence number until synced `[U9]`.

**Endpoints.** `GET /v1/address/{address_id}/observations?as_of=` and
`GET /v1/evidence/{observation_id}` (both new; data fully exists in `observations` +
`evidence_scores`).

---

## 8. Screen E — Verification queue

**Goal.** Work a queue of addresses that need a human decision, without ever editing a coordinate.

**Queue row anatomy** (professional precedent `[U3]` `[U4]`): address text (first column, human
readable), `address_id`, town, cause, tier/status, radius, independent negatives, **rule version**,
age, priority. Sorted by priority, filterable by `cause`/`town`/`state`.

**Causes and their meaning** (all five are real states in the runtime):

| Cause | Why the task exists | Evidence shown | Recommended action | What the reviewer can record |
|---|---|---|---|---|
| `VERIFY_FIRST` | gate action for an `APPROXIMATE`/unknown place | belief + radius + why the gate abstained | visit and confirm, or accept the locality-level answer | a normal observation (or decline) |
| `REVERIFICATION` | a prior negative accumulation resolved ambiguously | positives vs negatives with independence | re-visit with a fresh independent collector | observation |
| `CONTESTED` | strong observations separated by > 2× radius | the separating observations and their coordinates | adjudicate; the place may be two places | adjudication (`confirmed` / `not_true` / `inconclusive`) |
| `MOVED_SUSPECTED` | ≥2 independent negatives accumulated | the negatives + the unchanged positive coordinate | send a verification visit; keep serving the pin meanwhile | observation; adjudication only if the visit is conclusive |
| `UNPLACEABLE` | no candidate exists | the resolution attempt and its reasons | field capture to establish evidence, or leave unplaced | observation |

**Interaction rules (hard).** No control on this screen edits a coordinate. The only writes are
`POST /v1/evidence` (a new observation) and `POST /v1/adjudicate` (a review decision, stored as an
observation). Every action appends; the queue row then shows the resulting belief version and the
task's new state. Undo is not "delete" — it is another event `[U15]` `[U16]` `[U17]`.

**States.** *Empty*: "queue clear at <as_of>" — a good outcome. *Loading*: row skeletons with the
count. *Stale/offline*: queue frozen at pack time, marked. *Error*: no state change anywhere.

**Endpoint.** `GET /v1/tasks?town_id=&cause=&state=&as_of=&limit=&cursor=` — **shipped** (2026-10-08),
returning `items[]`, `facets{}`, `next_cursor` and `total_matching`; rows carry `recommended_action`,
`clears_when` and `evidence_refs[]`. The legacy `/tasks/verify-first` reader is unchanged.

---

## 9. Screen F — Method / trust / system explanation

**Goal.** Let an auditor (or a sceptical judge) see exactly what the system is allowed to do.

**Content.** The gate table (address purpose × tier × request purpose → action) with the live reason
strings; the radius map (`locality` p80 539.9 m, n=24, coverage 0.792, publishable; `street`/`pincode`
below the n≥15 guard → withheld and falling back to `locality`; `rooftop` insufficient n); the
invariants ("one negative never relocates"; "no candidate → no coordinate"; "identity is place-keyed,
never account-keyed"); the version block (schema/rules/evidence/radius/gate/purpose/directions);
the frozen precision decision and its measured results; and the **S-Eval firewall** statement — what
the system is *not allowed* to learn from.

**Backdrop.** The workbench plane draws against the town's **reference geometry** (`GET /v1/plane/{town_id}`:
locality centroids, landmark points, town centroid, extent, graticule 10 m / 100 m) and overlays the
address-scoped payload (`GET /v1/geometry/{address_id}`, alias `/v1/plane/address/{address_id}`) on
top. The town payload carries no address-level candidate, so the backdrop can never be mistaken for a
served answer.

**Actions.** Copy the version block; open the accuracy/method appendix; open the research register.

**The two loops this page must show (explicitly labelled, never blurred).**

```
FAST LOOP   — per place, per visit, runs today
FIELD VISIT → EVIDENCE → BELIEF UPDATE → PLACE MEMORY

SLOW LOOP   — across the corpus, runs offline under a declared split
EVIDENCE BUFFER → QUALITY GATE → TEMPORAL WINDOW → GLOBAL MODEL / CHALLENGER
                → CALIBRATION → VALIDATION → PROMOTION
```

| Loop step | What it is in this repository | Honest status label |
|---|---|---|
| Field visit → evidence | `sutra/evidence.py`, policy `evidence-policy-v3`: weight + reason codes + independence + polarity | **IMPLEMENTED** |
| Evidence → belief update | `sutra/belief.py`: pure function of the store at `as_of`, byte-identical recompute | **IMPLEMENTED** |
| Belief → place memory | `sutra/memory.py`: place-keyed projection with identity rule and contradictions | **IMPLEMENTED** |
| Evidence buffer | the append-only store (`observations`, `evidence_scores`, `task_events`) | **IMPLEMENTED** (as storage; no queue daemon) |
| Quality gate | duplicate/independence checks + the promotion gate (`gate-v2`, frozen F2.2 tuple) | **IMPLEMENTED as rules** — *not* a learned quality classifier |
| Temporal window | strict `observed_at < as_of`, replay and pack `valid_until` | **IMPLEMENTED** |
| Global model / challenger | `sutra/learning.py` challengers exist and were evaluated once under Experiment D; **no learned challenger cleared the declared bar, so the rule baseline remains the product** | **EVALUATED, REJECTED — not in the request path** |
| Calibration | conformal / validation research only; the shipped radii are empirical p80 strata | **RESEARCH ONLY** — the production radius map is not learned |
| Validation | split protocol (`split_receipt.json`), S-Eval firewall, grouped bootstrap | **IMPLEMENTED** |
| Promotion | evidence *promotion* is implemented; an automated **model** promotion pipeline | **NOT YET IMPLEMENTED / DESIGNED** |

The page must say this in plain words: *"SUTRA learns from field evidence per place. It does not
currently retrain a model, and the learned ranker that was evaluated was not adopted."* No training
platform, no scheduler, no model registry is claimed — because none exists.

**States.** Static by design — this screen renders constants and published numbers, and says when each
was frozen.

**Endpoint.** `GET /v1/health` (implemented, extended) + static content shipped with the frontend.

---

## 10. The learning loop, as a designed object

The differentiation is not one screen: it is that **BEFORE → OBSERVED → QUALITY → AFTER → WHY** is a
reusable component that appears (a) in the Field-evidence timeline, (b) in the Resolver after an
adjudication, (c) in the demo. Its non-negotiable properties:

- both "before" and "after" are computed by the same belief function at real instants;
- the evidence weight and its reason codes are shown verbatim, never summarised into a score;
- a change that did *not* happen is stated ("no promotion: the second confirmation lacked
  independence") — silence is indistinguishable from failure to a judge `[U18]`;
- negative evidence is visually distinct in all five beats.

---

## 11. Refusal, error and abstention copy (fixed)

| State | Headline | Body |
|---|---|---|
| No candidate | **No candidate → no coordinate** | reason codes + what was attempted (`exact_text_match`, `fuzzy_token`) + the locality context if any + "a town centroid is never served as an address" |
| `VERIFY_FIRST` (tier) | **Answer, but verify first** | tier + radius + why the gate abstained + what would change it (a field confirmation) |
| `REFUSE` (purpose) | **Not served for this purpose** | gate reason (`purpose_work_like`, `purpose_unknown_low_confidence`) + which purpose *could* be served |
| Contradiction | **This place is contested** | the separating observations, distance, threshold (2× radius) + "the coordinate has not been changed" |
| Offline | **Working offline** | pack version, age, evidence cutoff, outbox depth, "your captures are queued" |
| Transport error | **No answer recorded** | request id, retry; explicit statement that nothing was written |

---

## 12. Out of scope for this product phase

Route optimisation, dispatch/Gantt, polygon territories, basemaps, lat/lon display, chat, any
"confidence %", drag-to-edit geometry, dark patterns, a component-library rewrite, a design system
build. Each of these is either impossible under the frozen data policy `[S95]` or a distraction from
the one thing the product must prove.

## 13. Visual system — "survey office that learned to code"

The reference object is a **survey office**: ruled paper, instrument dials, ink corrections, a
register that is initialled and dated. Serious, warm, legible at arm's length under office light.
Nothing on screen is decorative; every rule, glyph and accent carries a meaning.

**Tokens (fixed; no theme switching in v1)**

| Token | Value | Use |
|---|---|---|
| `paper` | `#F6F2EA` | app background (warm off-white, not white, not grey) |
| `panel` | `#FDFBF6` | work surfaces, one step lighter than paper |
| `ink` | `#22201D` | primary text (graphite, never pure black) |
| `ink-2` | `#5A544B` | secondary text, labels, captions |
| `hairline` | `#D8D1C4` | 1 px borders and every table rule; separation comes from rules, not shadows |
| `survey` | `#C4521E` | restrained surveyor-orange: one accent per screen — the selected row/marker, the gate action, the active `as_of` cut |
| `field-pos` | `#2F6B45` | positive field evidence (always paired with a glyph) |
| `field-neg` | `#9B2C2C` | negative evidence (always paired with a glyph and a strike) |
| `warn` | `#8A5A00` | fallback radius, widened stratum, stale pack |
| `grid` | `#E7E1D6` | plane graticule dots, 10 m minor / 100 m major |

**Type**

- **Display numerals: serif** — coordinates, radii, distances, dates, counts and the ticket headline.
  This is the surveyor's hand: `x 1390.0 · y −1818.0`, `r 566.9 m`, `n 24`, `2026-06-01`.
- **UI text: sans** — labels, table cells, buttons. One family, three weights.
- **Diagnostics: monospace** — reason codes, version strings, hashes, payload snippets, the audit
  chain. Never used for prose.
- **Tabular figures everywhere**; no proportional numerals in tables. Radii and distances carry the
  unit in the label, never only in a legend.

**Line and space.** 1 px hairlines; 8-pt spacing scale; square corners with at most a 2 px radius.
Panels are separated by rules, not by shadow or float. Density is a feature: 36–44 px table rows,
full-height panes, no hero strips, no decorative empty space.

**The plane's own grammar.** Graticule dots; candidate markers as small circles, **filled** when
`primary_eligible` and **hollow** otherwise; the chosen candidate double-ringed in `survey`; the
uncertainty ring drawn as a hatched annulus at 1 px with its radius printed on the ring's own leader
line; negative observations as hollow crosses with a strike; the field-evidence trace as a thin
polyline through visit points ordered by time (arrowhead at the latest). **Static vs field-derived
provenance is carried by stroke and glyph** (dashed = `frozen_baseline`/static arms, solid =
evidence/memory arms), never by colour alone `[U21]` `[U22]`.

**Explicitly refused (the Phase-18 anti-list, treated as a hard style test).** Glassmorphism, neon
gradients, "AI glow", generic blue-SaaS palettes, stock hero illustrations, pill-shaped rounded
cards, drop shadows, parallax, animation that is not state change, decorative charts, 3-D anything,
fake geographic maps, and any compass rose or north arrow on the local plane.

**Accessibility.** Every state is legible without colour (glyph + stroke + text label); focus ring
uses `survey` at 2 px; the plane exposes an accessible list of the same points in the same order; all
table rows are operable by keyboard (`j`/`k`/`Enter`).

---

## 14. Evaluation honesty — the only numbers the product may show

The product may surface **exactly three** measured figures, each with its population, n, median, the
frozen `as_of`, and the frozen configuration hash. They are **not interchangeable**, and the
interface must never let them be read as one number.

| # | Figure | Population | n | < 500 m | Median error | Where it may appear |
|---|---|---|---|---|---|---|
| 1 | Cold independent evaluation | the 100 surveyed addresses, cold lane, `as_of 2026-06-01` | 100 | **71 %** | 375.8 m | Method & Trust only |
| 2 | Warm subset under the frozen evidence/memory policy | warm addresses with a field-confirmed answer, independent evaluation | **31** | **96.77 %** | 12.4 m | Method & Trust only, always with "31 answered" on the same line |
| 3 | Product lane (mixed traffic as served) | product lane, same frozen split | 100 | **76 %** | 202.2 m | Method & Trust only |

**Mandatory captions.** Figure 2 always carries *"31 answered"* and *"warm field-confirmed subset"*;
figure 1 always carries *"independent cold-start evaluation"*; figure 3 always carries *"product lane
— cold and warm together"*. Every figure carries the config hash `ac61cf2e71f77454…` and the note
*"measured on the frozen split; S-Eval was never trained or tuned on"* `[S95]`.

**Never in the product:** "90 % guaranteed", "100 % accurate", "production-ready", any accuracy
percentage inside the workbench, ticket or queue, any percentage attached to a single address, any
conversion of the 96.77 % warm subset into a general claim, any number shown without its population
and n, and any comparison against a vendor or competitor.

**Workbench rule.** Resolve, Places, Evidence and Verify Queue show **no accuracy percentage at
all** — they show tier, status, radius with basis/n/coverage, and reason codes. Accuracy lives on
exactly one page, with its labels, or it does not appear.

---

*Sources: `[U6]`–`[U14]` `[U15]`–`[U20]` `[U24]` per `SUTRA_UIUX_RESEARCH_SOURCES_2026-10-08.md`;
system and data policy `[S73]` `[S81]` `[S95]` per `PS3_SOURCE_REGISTER.md`.*
