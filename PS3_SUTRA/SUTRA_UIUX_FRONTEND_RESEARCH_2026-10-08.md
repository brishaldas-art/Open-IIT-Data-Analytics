# SUTRA — product / UI / UX / frontend research (2026-10-08)

**Scope.** Research for the interface layer only. Sources are product documentation, technical
documentation, design-system references and peer-reviewed user studies — no generic "AI dashboard
inspiration", no external data, no external geography. Every external fact used here is filed as
`[U1]`–`[U22]` in `SUTRA_UIUX_RESEARCH_SOURCES_2026-10-08.md`; the *dataset and system* sources stay
in `PS3_SOURCE_REGISTER.md` (`[S1]`–`[S96]`), which remains the only register that governs the data
policy. Nothing in this document changes a frozen precision decision `[S95]`.

**What the interface must never be** (carried from the frozen architecture, not from taste): not an
AI-chat surface, not a hero-and-chatbot page, no decorative map, no "AI confidence score", no
latitude/longitude anywhere. The coordinate system is the dataset's local metric plane, and the
product's honesty about uncertainty is the product `[S73]`.

---

## 1. What the repository already implies about the interface

Audited before any research (see `SUTRA_BACKEND_GAP_AUDIT_2026-10-08.md`): the runtime is a working
HTTP service with six live routes, a 26-test acceptance suite, an append-only store with 5,578
observations, 2,757 belief versions, 278 task events, a per-town offline pack and an offline device
outbox. So the interface has a real backend to stand on; the research question is not "what could we
build" but **what the existing decision objects should look like when a human has to trust them**.

Three structural facts from the audit shape every pattern below:

1. A resolve response today is a *flat decision object* (`candidate`, `tier`, `status`, `radius_m`,
   `reasons`, `eligibility`, `belief_version`, `support`) — already rich, but with no candidate list,
   no alternatives, no decision ticket.
2. Uncertainty is **empirical**: radius = published p80 for the stratum, × tier/negative factors,
   with `n_calibration` and `measured_coverage` travelling with it (`radius-map-v1`). The UI must
   show the calibration basis, never a bare number.
3. The learning loop is real and replayable: an address's belief moves cold → `PROBABLE` →
   `CONFIRMED` → `MOVED_SUSPECTED` across actual visits, and two independent negatives demote and
   widen the radius **without moving the coordinate**. That is the demo.

---

## 2. Research area 1 — field-service / field-operations interfaces

**Sources.** Salesforce Field Service dispatcher console and the newer Scheduling Console `[U1]`
`[U2]`; Field Service mobile (offline-capable) `[U2]`.

**Pattern.** The dispatch console is *not* a dashboard: it is a workbench with a persistent list on
one side, a time/space canvas on the other (Gantt and Map tabs), saved views and filters at the top,
and bulk actions on the selection. The Scheduling Console adds an explicit **keyboard-shortcut
surface** for dispatchers — the product documents shortcuts as a first-class feature because the
users are high-frequency operators `[U2]`.

**Why it matters to SUTRA.** SUTRA's primary user is a field-force operator doing many addresses per
day, and the second user is a reviewer adjudicating a queue. Both are frequency users. The frozen
runtime already emits per-address decisions; the missing piece is a workbench that keeps the
*queue* and the *decision surface* on one screen.

**Adopt.** Queue-left / decision-right workbench; saved views (by town, by tier, by queue cause);
documented keyboard map; bulk selection semantics that operate on *decisions* (resolve, export,
verify) — never silent coordinate edits.

**Do NOT copy.** The Gantt metaphor (SUTRA has no scheduling optimiser and inventing one would be
decoration); drag-to-dispatch (there is no dispatcher role in the frozen architecture); territory
polygons (no polygons exist in the official package — `place_neighbour` is locked off).

**Backend implication.** A queue surface needs a server-side filtered, ordered, paginated task list
with facets and counts (`GET /tasks` with `cause`, `town`, `state`, `min_negatives`, sorting by
`priority`), plus stable task ids. Structure exists (`verify_first_tasks`); filtering/facets do not.

---

## 3. Research area 2 — professional geospatial operations

**Sources.** ArcGIS Data Reviewer error management and the error life-cycle (Review → Correction →
Verification), the Error Inspector table schema, and "mark as exception" state `[U3]` `[U4]` `[U5]`.

**Pattern.** A spatial data-quality workflow is modelled as **error results with a life cycle and an
inspector table**, where each error carries: rule name, error message, severity, source layer, the id
of the feature that created it, and an *exception* flag; correcting the feature does not delete the
error — the error is re-evaluated and cleared `[U3]` `[U4]`.

**Why it matters to SUTRA.** This is the closest professional analogue to SUTRA's verification queue,
and it validates the frozen design: SUTRA's `verify_first_tasks` already carry `task_id`, `kind`,
`cause`, `reason`, `negatives_independent`, `priority`, `town_id`, `state` and the rule version —
i.e. the same shape as a Reviewer error result, including the rule version, which most products
forget.

**Adopt.** Error-row anatomy verbatim: *cause + rule version + evidence counts + severity/priority +
source ids*; a three-phase life cycle (detected → actioned → verified) for tasks; the "exception"
concept maps to SUTRA's adjudication (`confirmed` / `not_true` / `inconclusive`); clearing a task
requires re-evaluation, not a delete.

**Do NOT copy.** The blanket "geodatabase" framing (SUTRA is not a GIS editor and does not edit
geometry); pixel-granular editing tools; the assumption that a human can draw the right answer (in
SUTRA a human *observation* is evidence like any other, weighted and independent-scored).

**Backend implication.** `POST /v1/adjudicate` must record an **observation**, not a coordinate edit,
and the task must transition through explicit states with an audit row each time. The UI needs
`task.state`, `task.history[]`, `task.rule_version`, `task.clears_when`.

---

## 4. Research area 3 — uncertainty visualisation

**Sources.** Hegarty et al., *Where Are You? The effect of uncertainty and its visual representation
on location judgments in GPS-like displays* `[U6]`; a systematic review of geospatial uncertainty
user studies `[U7]`; a 2024 study on communicating spatial uncertainty of landmarks by circle/size/
transparency `[U8]`.

**Findings that matter.**
- The familiar translucent "blue circle" is read by non-experts as a *confidence region* and — in a
  single-symbol task — users assume they are at the **centre** `[U6]`. The circle does not induce
  neglect, but it does not explain itself either.
- Circle-style uncertainty areas measurably improve map↔reality matching when the underlying data is
  inaccurate, and the effect grows with inaccuracy `[U8]`.
- The review reports that *coincident* uncertainty symbols outperform uncertainty in a legend, and
  that point-based positional-uncertainty symbols produced higher accuracy **and higher confidence**
  `[U7]` — i.e. showing uncertainty next to the object raises trust rather than lowering it.

**Why it matters to SUTRA.** SUTRA's whole claim is that a radius is an empirically measured p80 with
an n, not a decoration. The research says: put the uncertainty *on the object* (the candidate), keep
it coincident, and pair it with a numeric statement. It also warns about the centre assumption, which
is exactly the failure mode we must avoid — a user reading "±1203 m" and driving to the centre point.

**Adopt.** A radius ring drawn around the candidate with the numeric `radius_m` label attached to the
same glyph; the `basis` (`empirical_p80` / `fallback`), `n_calibration` and `measured_coverage` in the
adjacent detail pane with plain-language phrasing ("radius is the measured 80th-percentile error over
24 calibration addresses; it is not a guarantee"). Widen triggers (`negative_accumulation`,
`calibration_fallback`) rendered as annotations on the ring, not hidden in a tooltip.

**Do NOT copy.** Continuous probability shading (implies a density model SUTRA does not have);
"95% confidence" phrasing (the published statistic is p80); ellipses (no covariance is estimated).

**Backend implication.** The radius object must always travel with `basis`, `n_calibration`,
`measured_coverage`, `source_stratum`, `widened`, `widen_reason`, `radius_map_version` — today it
does, and the UI contract must forbid rendering `radius_m` without them.

---

## 5. Research area 4 — offline-first field capture

**Sources.** Offline-first architecture/UX guidance (visible network state, banner + pending-count,
queued submissions explained) `[U9]`; an app-architecture write-up with the same conclusions
`[U10]`; the field-data-collection tool landscape (ODK/Kobo/CommCare/SurveyCTO: offline capture with
server-side conflict handling) `[U11]`. The *contract* precedent (outbox, client-generated
idempotency keys, server cursors, hold-then-conflict) is already filed internally as `[S81]` `[S82]`.

**Pattern.** Offline-first interfaces make three things visible at all times: *you are offline*,
*how many items are pending*, and *what will happen to them*. Nothing is lost, nothing is blocked, and
the queue is inspectable. Conflicts are resolved by explicit review, not last-write-wins `[U9]` `[U10]`.

**Why it matters to SUTRA.** The runtime already has the hard part: `sutra/offline.py` with an outbox
table (observation id, local seq, capture time, payload + sha256), pack download, attempt log and
replay; T9 in the acceptance suite proves an offline capture replays idempotently. The UI merely has
to expose what exists.

**Adopt.** A persistent runtime-status chip in the shell: connection state, outbox depth, last sync
time, pack version and pack age. A "pending evidence" list showing each queued observation with its
idempotency key and last attempt result. Human-readable explanation on submit: "queued locally; it
will sync and score when a connection returns".

**Do NOT copy.** Optimistic full-state editing (SUTRA writes are append-only observations); a
sync-conflict UI for coordinates (there is nothing to conflict: observations never overwrite).

**Backend implication.** The pack needs to expose `pack_version`, `valid_until` and a staleness flag
(today `build_pack` returns those fields for the *pack builder*, not for a device already holding an
older pack). `Health` must report pack age and outbox-relevant counters.

---

## 6. Research area 5 — data-dense B2B workbenches

**Sources.** NN/g *Data Tables: Four Major User Tasks* `[U12]`; NN/g *Progressive Disclosure* `[U13]`;
the collated application-design guidance (predictable placement, clear hierarchy, two-level disclosure
maximum) `[U14]`.

**Findings that matter.** Tables exist for four tasks: find by criteria, compare, inspect one row,
act on rows. The first column should be a **human-readable record identifier**, not an opaque id, and
column order should follow the user's priority `[U12]`. Progressive disclosure defers secondary
features; more than ~two levels is where users get lost; labels must be concrete `[U13]` `[U14]`.

**Why it matters to SUTRA.** SUTRA's natural identifiers are `address_id` (opaque: `AD002936`) and
`address_text` (a real, messy, mixed-script string). The first column must be the address text with
the id as a secondary monospace token. Every derived quantity the UI shows — tier, radius, queue
cause, eligibility action — is already computed server-side, so disclosure is a *layout* problem, not
a computation problem.

**Adopt.** Address text first, id second, tier/status/radius as right-aligned scannable columns; a
detail pane rather than a modal; two levels: (1) decision summary, (2) evidence/audit detail.

**Do NOT copy.** KPI-tile dashboards as a landing experience (the landing screen must be the work,
not four numbers); infinite scroll with no position memory (queue work needs "resume where I was").

**Backend implication.** List endpoints must return the human fields the table needs (`address_text`,
`town_id`, `candidate.arm`, `granularity`, `tier`, `status`, `radius_m`, `eligibility.action`,
`queue.cause`) so the table never issues N+1 lookups.

---

## 7. Research area 6 — audit, provenance, version history

**Sources.** Event-sourcing-for-audit literature and append-only/hash-chain practice `[U15]`;
audit-trail UI pattern description (searchable log of decisions, data used, versions, timestamps,
actors, exportable) `[U16]`; "audit by default" engineering guidance (middleware capture, separation
of audit stream from operational data, append-only storage) `[U17]`.

**Pattern.** The audit trail is a *product surface*, not a debug log: it answers who/what/when/why,
it is immutable, it separates the event stream from current state (state is a *projection* that can be
rebuilt), and it is read-only for humans `[U15]` `[U16]` `[U17]`.

**Why it matters to SUTRA.** This is SUTRA's architecture already: `observations` → `evidence_scores`
→ `belief_versions` are append-only, belief is a pure function recomputed from the store, and
`place_state` is explicitly named a **projection** in its own payload. The frozen system can therefore
show a *real* audit chain — and the UI's job is to make "state is derived" legible, including the
"recompute at a different `as_of`" affordance that no ordinary product can offer.

**Adopt.** A timeline that is a list of *events* (observation → evidence weight/reason codes → belief
version), each event clickable to reveal its inputs and rule versions; a "state is a projection"
banner on the place screen; export-the-chain action; read-only enforcement.

**Do NOT copy.** Editable audit rows; "history" that shows only the last N changes without versions;
diff views that imply the coordinate was edited in place (it never is).

**Backend implication.** `GET /v1/audit/{belief_id}` must return the full chain with rule versions and
the *inputs* (observation ids, weights, reason codes), and `GET /v1/belief` must accept any `as_of`,
not only "now".

---

## 8. Research area 7 — explainability and calibrated trust

**Sources.** Google PAIR *People + AI Guidebook* — explainability/trust chapter and worksheet `[U18]`
`[U19]`; a summary of its chapters `[U20]`.

**Patterns.** Calibrated trust is the goal, not maximal trust: the product should be trusted in some
situations and double-checked in others `[U18]`. Two concrete instruments: the "N-best" display
(show alternatives, not only the top choice) and explicit uncertainty display; and a 2×2 of user
impact × model confidence to decide *when* an explanation is owed `[U19]`. "Tie explanations to user
actions" and "account for situational stakes" are named factors `[U18]`.

**Why it matters to SUTRA.** SUTRA's gate (`SERVE` / `VERIFY_FIRST` / `REFUSE`) *is* the 2×2 made
executable: high-stakes purposes (notice, visit planning) require a `SERVE`-grade place, and the
system abstains otherwise. The interface should present the gate as the explanation, and use N-best
(alternatives + why the runner-up lost) rather than a confidence score.

**Adopt.** Alternatives list with the losing reason codes and score deltas; the eligibility action as
the headline of every decision; abstention styled as a *successful* outcome with the reason
("no candidate → no coordinate"), never as an error state.

**Do NOT copy.** A single "confidence %" (SUTRA has a tier + a measured radius; a percentage would be
an invented statistic); disclaimers as a substitute for explanation; anthropomorphised assistant copy.

**Backend implication.** `ResolveResponse` must carry `alternatives[]` (≥ the runner-up with its own
reason codes) and a `decision_ticket` the UI can render without re-deriving anything.

---

## 9. Research area 8 — maps when the coordinates are not geographic

**Sources.** Schematic/topological map principles — deliberate metric distortion, topology and
adjacency retained, "not to scale" as an explicit property `[U21]` `[U22]`; SVG vs Canvas rendering
thresholds (SVG DOM, CSS, accessibility, comfortable to a few thousand nodes; Canvas for tens of
thousands) `[U23]`.

**Why it matters to SUTRA.** The dataset is a **local metric plane** with no projection, no
lat/lon and no polygons; the town extents are multi-kilometre axis-aligned boxes. Admitting "this is
a schematic plane, drawn to scale within a town but not a real-world map" is more honest than any
pseudo-geographic rendering, and the research legitimises it: schematic maps trade geographic
fidelity for comprehension and say so `[U21]`.

**Adopt.** A **SUTRA plane** view: local metric axes in metres, per-town extent, grid at a declared
interval, and objects drawn at their real metric positions *within* the plane (so distances and the
radius ring are true). SVG with viewBox and data-space → screen-space transform; the count of objects
per view is bounded by design (one address's candidates, its observations, its neighbours), so SVG's
DOM ceiling is far away `[U23]`.

**Do NOT copy.** Basemap tiles, road networks, satellite imagery, compass roses, north arrows (there
is no geographic north), or any claim that the plane is a real map. No Web Mercator, no EPSG, no
lat/lng — the plane is the coordinate system `[S73]`.

**Backend implication.** The backend returns geometry and local-plane metadata only
(`coordinate_space`, `x`, `y`, `radius_m`, plus optional extent and context rings). All projection,
symbolisation and interaction stay in the frontend (see the map contract in
`SUTRA_FRONTEND_BACKEND_CONTRACT_V1_2026-10-08.md`).

---

## 10. Pattern ledger — adopt / reject, with the backend consequence

| # | Source | Pattern | Adopt in SUTRA | Backend consequence |
|---|---|---|---|---|
| 1 | `[U1]` `[U2]` | List + canvas workbench with saved views | Resolver workbench: queue left, decision middle, plane right | server-side filtering/facets on list endpoints |
| 2 | `[U2]` | Documented keyboard map for high-frequency operators | Command palette + shortcuts in the workbench | none (client-only) |
| 3 | `[U3]` `[U4]` | Error result with rule version, severity, source ids | Task/queue row anatomy | `task.rule_version`, `task.source_ids[]` (partial today) |
| 4 | `[U5]` | Detected → corrected → verified life cycle; exception flag | Task states incl. adjudication outcomes | task transitions + audit rows (P0) |
| 5 | `[U6]` `[U7]` `[U8]` | Coincident circle uncertainty, numeric pairing, centre-assumption risk | Radius ring anchored on the candidate with numeric label | radius must always carry basis/n/coverage |
| 6 | `[U9]` `[U10]` `[U11]` | Visible offline state, pending count, explained queueing | Runtime-status chip + pending-evidence list | pack age/staleness + outbox counters (P0) |
| 7 | `[U12]` | Human-readable first column; task-driven column order | Address text first, id second in every queue | lists return display fields |
| 8 | `[U13]` `[U14]` | Two-level progressive disclosure | Summary → evidence/audit detail | nested payloads (`decision_ticket`, `chain`) |
| 9 | `[U15]` `[U16]` `[U17]` | Append-only audit chain as a product surface | Evidence & belief timeline, exportable | `GET /audit/{belief_id}` (design-only today) |
| 10 | `[U18]` `[U19]` | N-best alternatives; uncertainty over confidence-score | Alternatives pane with losing reasons | `alternatives[]` in the resolve contract (missing) |
| 11 | `[U19]` | Stakes × confidence decides when to explain | Gate action headlines every decision | gate already implemented; expose as headline |
| 12 | `[U21]` `[U22]` | Schematic plane, "not to scale" honesty | SUTRA plane with explicit plane id and metre grid | `coordinate_space` + extent in the map contract |
| 13 | `[U23]` | SVG until tens of thousands of nodes | SVG renderer, viewBox transform | none |

**Rejected outright** (with reasons): Gantt/dispatch semantics `[U1]` (no scheduler exists);
polygon/territory selection `[U2]` (no polygons in the official package); GIS editing tools `[U3]`
(SUTRA never edits geometry); probability-density shading `[U7]` (no density model); LWW conflict
resolution `[U9]` (SUTRA is append-only); KPI-tile landing pages `[U12]`; chat/assistant framing and
confidence percentages `[U18]`; basemaps and any geographic projection `[U21]`.

---

## 11. What this research changes in the plan (and what it does not)

**Changes.** (a) The landing screen becomes the *workbench*, not a dashboard; (b) alternatives and
losing reasons become a **contract requirement** (`alternatives[]`) rather than a nice-to-have;
(c) the queue row anatomy is fixed by a professional precedent, so `verify_first_tasks` gains
`rule_version`/`source_ids`-style fields instead of a bespoke shape; (d) offline state becomes a
first-class shell element fed by pack age + outbox depth; (e) the map is declared a schematic plane
in the contract itself, with `coordinate_space` as a required field; (f) alternatives+radius replace
any "confidence" display.

**Does not change.** The precision backbone, the arm set, the belief/uncertainty mathematics, the
gate rules, the store, the packs, the S-Eval discipline. Every item above is presentation-layer or a
read-only projection of state that already exists; the two write paths that do exist (`/evidence`,
adjudication) are unchanged in semantics and gain only validation and audit obligations.

*Sources for this document: `[U1]`–`[U23]` in `SUTRA_UIUX_RESEARCH_SOURCES_2026-10-08.md`; internal
data-policy and system sources `[S69]` (grouped resampling practice, unaffected), `[S73]`
(heavy-tailed geocoding error — the reason radius is a measured p80 and never a bare number), `[S81]`
`[S82]` (offline sync precedent already implemented), `[S95]` (final data policy, unchanged).*
