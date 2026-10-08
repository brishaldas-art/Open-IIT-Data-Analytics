# SUTRA --- FINAL ARENA HANDOFF

## Google Drive Battle-Model Frontend Integration + Real Backend Completion

**Status:** STOP the current Arena run before implementation continues.

**Critical change:** The Battle-Model frontend ZIP could not be uploaded
directly into the Arena workspace. The ZIP has now been placed in Google
Drive, and a Google Drive connector will be available to Arena.

The file to locate is:

`sutra-geospatial-operations-workbench.zip`

Do **not** guess its contents and do **not** rebuild the UI from the
current console.

------------------------------------------------------------------------

# 1. FIRST ACTION --- FIND THE ZIP IN CONNECTED GOOGLE DRIVE

After the Google Drive connector is available:

1.  Search connected Google Drive for:
    -   `sutra-geospatial-operations-workbench.zip`
    -   `sutra-geospatial-operations-workbench`
2.  Open/read the file metadata.
3.  Download/materialize the ZIP into the workspace.
4.  Verify its contents before modifying anything.

Expected Battle-Model frontend structure includes files such as:

``` text
src/App.tsx
src/components/LocalPlaneMap.tsx
src/components/Shell.tsx
src/components/u.tsx
src/lib/api.ts
src/lib/fixtures.ts
src/lib/session.tsx
src/lib/types.ts
src/lib/utils.ts
src/views/FieldEvidence.tsx
src/views/Method.tsx
src/views/Overview.tsx
src/views/Places.tsx
src/views/Resolver.tsx
src/views/VerifyQueue.tsx
src/index.css
package.json
vite.config.*
```

These names are a verification clue, not permission to fabricate files.

### HARD STOP RULE

If the ZIP cannot be found in Google Drive:

-   do NOT redesign the current console
-   do NOT claim that the Battle-Model UI has been preserved
-   do NOT fabricate its source code
-   report exactly what was searched and stop at the
    frontend-integration step

------------------------------------------------------------------------

# 2. PRIMARY OBJECTIVE

Turn the existing Battle-Model frontend from a visually strong fixture
prototype into the **real SUTRA product**.

The target is:

``` text
Battle-Model UI/UX
        ↓
real SUTRA API
        ↓
real PS3 data + frozen intelligence
        ↓
real decision / uncertainty / evidence / task
```

The Battle-Model UI is the **visual shell**.

The existing SUTRA backend is the **source of truth**.

Do NOT redesign the Battle-Model UI.

Do NOT replace its layout with the current console.

Do NOT create a new aesthetic.

Preserve its:

-   information architecture
-   visual hierarchy
-   navigation
-   typography
-   spacing
-   map interaction
-   resolver workbench layout
-   candidate ↔ map ↔ decision interaction
-   evidence timeline
-   verification queue
-   Places view
-   Method & Trust view
-   responsive behavior

Correct only the parts that are technically fake, misleading, or
inconsistent with the SUTRA contract.

------------------------------------------------------------------------

# 3. ABSOLUTE ARCHITECTURE RULES

These are frozen.

## DO NOT CHANGE

Do not modify:

-   candidate arms
-   candidate generation
-   ranker weights
-   ranker tie-breaks
-   gate-v2 rules
-   radius thresholds
-   evidence weighting
-   memory policy
-   place-keying
-   append-only observation semantics
-   as-of semantics
-   S-Eval firewall
-   official raw dataset
-   precision configuration
-   frozen evaluation artifacts
-   local metric coordinate model

Do not introduce:

-   new ML ranking models
-   local ML models
-   LLMs
-   embeddings as production dependencies
-   autonomous agents
-   external geocoders
-   OSM/Overture/OpenAddresses
-   live map providers
-   external POI data
-   WGS84/lat-lon conversion
-   Web Mercator
-   EPSG reprojection

This task is **productisation and integration**, not precision
optimisation.

------------------------------------------------------------------------

# 4. COORDINATE RULE

SUTRA uses:

``` text
sutra_local_metric_plane:<town>
```

Coordinates are local metric:

``` text
x = metres
y = metres
```

Never use:

``` text
latitude
longitude
lat
lng
WGS84
EPSG
Mercator
Web Mercator
```

Do not invent geographic coordinates.

The map must render the SUTRA local metric plane.

For refusal states, coordinates must not leak into the response or UI.

------------------------------------------------------------------------

# 5. INSPECT BOTH SIDES BEFORE CODING

Before changing anything, inspect:

## A. Battle-Model ZIP

Understand:

``` text
App
Shell
Resolver
Places
FieldEvidence
VerifyQueue
Overview
Method
LocalPlaneMap
api
fixtures
session
types
styles
```

Record:

-   what is visual-only
-   what is fixture-only
-   what is already reusable
-   what frontend code derives incorrectly
-   what API contracts it expects

## B. Current SUTRA repository

Inspect:

``` text
sutra/
tests/
tools/
data/official_ps3/
data/derived/
research/
docs/
```

Especially inspect:

``` text
sutra/api.py
sutra/resolve.py
sutra/candidates.py
sutra/memory.py
sutra/store.py
sutra/evidence.py
sutra/packs.py
sutra/offline.py
```

Also inspect the latest backend contract and gap audit already present
in the repository.

Do not assume the old gap list is still current.

------------------------------------------------------------------------

# 6. REAL CURRENT BACKEND STATUS

The SUTRA backend has already completed the major P0 contract layer.

Known validated state before this task:

``` text
26/26 existing acceptance tests
51/51 contract tests
77/77 total tests
21/21 HTTP smoke
13/13 browser smoke
leakage guards passed
workspace checks passed
official data unchanged
S-Eval reads unchanged
precision configuration unchanged
```

Therefore:

## DO NOT REIMPLEMENT P0

First run the existing tests and inspect the actual repository.

Only implement genuinely missing functionality.

------------------------------------------------------------------------

# 7. FRONTEND FIXTURE REPLACEMENT

The Battle-Model frontend currently contains fixture-oriented code.

Typical problematic patterns include:

``` ts
import { CASES, OVERVIEW, PLACES, SCENARIOS, SCENE, VISITS } from "./fixtures";
```

simulated network delays:

``` ts
setTimeout(...)
```

random task identifiers:

``` ts
Math.random()
```

hard-coded fake providers:

``` text
Municipal Parcel DB
Gazette Registry
Postal PIN Directory
```

fake metrics:

``` text
fake latency
fake SLA
fake score
fake dates
fake GPS
fake provider
```

These must not survive in production UI.

### Replace them with real API calls.

The frontend must never invent:

-   candidates
-   scores
-   coordinates
-   uncertainty
-   task IDs
-   evidence
-   timestamps
-   provenance
-   workflow state
-   metrics

The backend owns those values.

------------------------------------------------------------------------

# 8. FRONTEND MUST NOT RE-DERIVE SUTRA INTELLIGENCE

The UI must NOT calculate:

``` text
candidate ranking
tier
radius
winning candidate
eligibility
priority
evidence weight
memory confidence
gate decision
task priority
```

The frontend renders backend decisions.

For example, do NOT do this in React:

``` ts
const gate = score > 0.8 ? "SERVE" : "VERIFY_FIRST";
```

Instead:

``` ts
const decision = response.decision_ticket;
```

and render the server result.

------------------------------------------------------------------------

# 9. REAL API CONTRACT

Use the repository's existing contracts as authoritative.

The core endpoints are:

``` http
POST /resolve
POST /evidence
POST /explain
GET /health
GET /place/{id}
GET /tasks/verify-first
GET /packs/{town_id}
```

The v1/read surfaces include:

``` http
POST /v1/resolve
GET /v1/belief/{address_id}
GET /v1/address/{address_id}/observations
GET /v1/place/{place_id}
GET /v1/tasks
GET /v1/health
GET /v1/plane/{town_id}
GET /v1/plane/address/{address_id}
```

Only use routes that actually exist or implement them according to the
repository's contract.

------------------------------------------------------------------------

# 10. REMAINING P1 BACKEND WORK

Inspect first, then implement only missing pieces.

## P1-1 --- score_visit

``` http
POST /v1/score_visit
```

Purpose:

Pre-visit advisory scoring.

Input should contain the live check-in / candidate context defined by
the repository contract.

Output should expose things such as:

``` text
distance_to_candidate_m
within_radius
hint
reason_codes
```

CRITICAL:

``` text
score_visit MUST NOT write observations.
```

It is advisory only.

------------------------------------------------------------------------

# 11. P1-2 --- HUMAN ADJUDICATION

Implement:

``` http
POST /v1/adjudicate
```

Conceptual input:

``` json
{
  "address_id": "AD002936",
  "decision": "confirmed",
  "actor": "human",
  "note": "Verified during field review",
  "idempotency_key": "..."
}
```

Allowed decisions:

``` text
confirmed
not_true
inconclusive
```

The operation must:

1.  validate input
2.  enforce idempotency
3.  append an observation of kind `adjudication`
4.  update the derived belief through the existing frozen mechanism
5.  return receipt + resulting effect
6.  never mutate old observations

Do not invent a second truth store.

------------------------------------------------------------------------

# 12. P1-3 --- TASK LIFECYCLE

Implement the task transition surface according to the existing
contract.

Expected conceptual endpoint:

``` http
PATCH /v1/tasks/{task_id}
```

Transitions must be append-only.

Example:

``` text
open
→ in_progress
→ resolved
```

and where permitted:

``` text
resolved
→ reopened
```

Store task events rather than rewriting history.

Expose:

``` text
current state
history
actor
timestamp
note
recommended action
```

The frontend must display the real workflow state.

------------------------------------------------------------------------

# 13. P1-4 --- AUDIT CHAIN

Implement:

``` http
GET /v1/audit/{belief_id}
```

This is a read-only reconstruction over existing
evidence/observation/belief records.

The audit should explain:

``` text
what happened
when it happened
what evidence arrived
how evidence was weighted
what belief version resulted
what uncertainty changed
what task was created/changed
```

Do not create fake audit events just to populate the UI.

------------------------------------------------------------------------

# 14. P1-5 --- OVERVIEW

Implement:

``` http
GET /v1/overview
```

Use real store/runtime data.

The Overview should show operational state such as:

``` text
address population
cold/warm operating population
tier mix
verification queue depth
town counts
pack freshness
```

Do NOT show fabricated:

``` text
fake latency
fake accuracy
fake throughput
fake SLA
```

Do not turn Overview into a generic analytics dashboard.

------------------------------------------------------------------------

# 15. P1-6 --- PACK FRESHNESS

Expose real pack metadata.

Where appropriate return:

``` text
pack_version
downloaded_at
age_days
valid_until
stale
```

Never pretend an offline pack is fresh.

------------------------------------------------------------------------

# 16. P1-7 --- METHOD & TRUST

Build the Method/Trust response from actual backend/runtime metadata.

It may explain:

``` text
fast loop
slow loop
candidate generation
evidence
memory
uncertainty
as-of behavior
official data boundary
offline packs
```

Use explicit product status labels:

``` text
IMPLEMENTED
DESIGNED
NOT YET IMPLEMENTED
NOT MEASURED
```

Do not expose internal API capability matrices as the main product
experience.

------------------------------------------------------------------------

# 17. P1 PROVENANCE

Ensure the real candidate provenance survives the API boundary.

The UI should be able to answer:

``` text
Where did this candidate come from?
Why did it win?
Why did alternatives lose?
What evidence supports it?
```

Use server-generated:

``` text
candidate arm
source
lost_reason
reason codes
```

Do not reconstruct explanations from strings in React.

------------------------------------------------------------------------

# 18. P2 --- BATCH RESOLVE

Implement only after P1 is stable:

``` http
POST /v1/batch_resolve
```

Limit:

``` text
≤ 5,000 rows
```

Return:

``` text
per-row decision ticket summary
refusal rate
tier mix
radius histogram
```

Never call this a bulk accuracy benchmark.

------------------------------------------------------------------------

# 19. CASE SNAPSHOT

If the repository contract contains a case snapshot route, implement it
as a **read-only composition** of existing backend truth.

It should make it possible for all screens to show the same case
consistently:

``` text
Resolve
Places
Evidence
Verify Queue
Audit
```

No duplicated frontend truth.

------------------------------------------------------------------------

# 20. REAL DEMO RECORDS

Use real PS3 records.

Important demo addresses include:

``` text
AD003067
AD002936
```

AD002936 is particularly important because the real evidence replay
demonstrates:

``` text
radius:
566.9 m → 1202.6 m

tier:
CONFIRMED → APPROXIMATE

status:
MOVED_SUSPECTED

task:
VERIFY_FIRST

coordinate:
UNCHANGED
```

The demo must show that:

> uncertainty and workflow can change without blindly moving the
> physical place.

Do not hand-type these values into the frontend.

Retrieve them from the backend.

------------------------------------------------------------------------

# 21. PRODUCT LANGUAGE

The Battle-Model UI currently exposes too much backend jargon.

Keep the visual design but make the product understandable.

Prefer:

``` text
Recommended
Close alternative
Needs verification
Evidence quality: strong
Evidence quality: needs review
Why this decision?
What changed?
```

Instead of making raw internals the main visual:

``` text
score 0.917106
belief_version
place_id
gps_accuracy_m
policy_version
raw enum
```

Exact technical values can remain under:

``` text
Decision details
Evidence details
Audit
Method
```

Do not remove useful technical information from the product entirely.

Move it to the appropriate detail layer.

------------------------------------------------------------------------

# 22. MAP / LOCAL PLANE

Preserve the Battle-Model map interaction.

But ensure:

``` text
local metric x/y
equal scale
authoritative uncertainty radius
candidate points
evidence points
cross-highlighting
```

Never:

``` text
lat/lng
basemap
roads
satellite imagery
geographic conversion
```

Refusal:

``` text
no coordinate
no radius
no hidden candidate geometry
```

------------------------------------------------------------------------

# 23. PLACES SCREEN

Keep the Battle-Model Places UI.

Show:

``` text
place identity
current belief
history
contradictions
members
evidence-derived memory
verification state
```

Hide low-level fields behind a Details/Technical section:

``` text
belief_version
place_id
raw status enums
internal IDs
```

------------------------------------------------------------------------

# 24. EVIDENCE SCREEN

Keep the evidence timeline.

The main UI should communicate:

``` text
Evidence quality: strong
Evidence quality: needs review
Positive evidence
Negative evidence
Non-claim
Independence
Integrity
What changed
```

Technical fields such as:

``` text
gps_accuracy_m
device
policy version
HDOP
constellation
```

may be available under expandable technical detail, but must not
dominate the main product surface.

------------------------------------------------------------------------

# 25. VERIFY QUEUE

Use the real backend task queue.

The queue must not be fixture-driven.

Each task should be linked to:

``` text
real address
real reason
real decision
real uncertainty
real recommended action
real history
```

A human action should call the adjudication/task APIs rather than mutate
React state only.

------------------------------------------------------------------------

# 26. OPERATIONS / OVERVIEW

The Operations screen must become a real operational view.

Do not make it a generic KPI dashboard.

It should answer:

``` text
What needs attention?
Where is SUTRA uncertain?
How fresh is the runtime?
How many verification tasks exist?
Which towns are cold/warm?
```

------------------------------------------------------------------------

# 27. NO-FAKE-DATA GUARD

Add an automated test/guard that fails if production UI code contains
known fake/demo providers or fixture-only production data.

Search for at least:

``` text
Municipal Parcel DB
Gazette Registry
Postal PIN Directory
fixture replay
demo 0.9.4
Math.random
setTimeout
fake provider
mock provider
fake GPS
```

Also inspect imports so production components do not use demo fixtures
as authoritative data.

A tiny labelled fallback may exist only if the existing runtime contract
explicitly permits it, and it must be visibly labelled as
captured/offline data.

------------------------------------------------------------------------

# 28. DO NOT REMOVE THE REAL OFFLINE FALLBACK BLINDLY

SUTRA intentionally has offline/pack behavior.

Do not confuse:

``` text
real captured/offline data
```

with:

``` text
fake fixture data
```

The UI must clearly distinguish:

``` text
LIVE RUNTIME
CAPTURED DATA
OFFLINE PACK
```

Never silently present captured data as live.

------------------------------------------------------------------------

# 29. TESTING REQUIREMENTS

After implementation:

## Backend

Run:

``` bash
bash tools/reproduce.sh full
```

and the repository's current test suite.

Expected existing baseline must remain green.

Do not accept:

``` text
77/77 → lower
```

because of this integration.

------------------------------------------------------------------------

# 30. API SMOKE

Verify at minimum:

``` text
/health
/v1/health
/resolve
/v1/resolve
/v1/belief/{id}
/v1/address/{id}/observations
/v1/place/{id}
/v1/tasks
/v1/plane/{town}
/v1/plane/address/{id}
/v1/overview
/v1/audit/{id}
```

plus write paths:

``` text
/evidence
/v1/score_visit
/v1/adjudicate
/v1/tasks/{id}
```

where implemented.

------------------------------------------------------------------------

# 31. BROWSER TEST

Run the Battle-Model frontend in headless Chromium.

Verify:

1.  Operations loads
2.  Resolve loads
3.  real address resolves
4.  candidate selection cross-highlights map
5.  decision ticket matches backend
6.  uncertainty ring matches backend
7.  Places loads real place
8.  Evidence loads real evidence
9.  Verify Queue loads real tasks
10. adjudication changes the backend state
11. Method & Trust loads
12. refusal hides coordinates
13. narrow viewport works

Zero console errors.

------------------------------------------------------------------------

# 32. IMPORTANT DEMO FLOW

Use this exact conceptual sequence:

``` text
OPEN OPERATIONS
      ↓
OPEN RESOLVE
      ↓
RESOLVE AD003067
      ↓
show real SERVE decision
      ↓
open AD002936
      ↓
open contradictory evidence replay
      ↓
show radius widening
      ↓
show tier downgrade
      ↓
show MOVED_SUSPECTED
      ↓
show VERIFY_FIRST task
      ↓
show coordinate did NOT move
      ↓
open Evidence
      ↓
open Places
      ↓
open Verify Queue
      ↓
show Method & Trust
```

The story is:

> SUTRA does not merely guess a point. It maintains a belief about a
> place, learns from field evidence, represents uncertainty explicitly,
> and routes unresolved cases to verification.

------------------------------------------------------------------------

# 33. ACCEPTANCE RULES

Do not report success merely because the page loads.

The final product must satisfy:

``` text
REAL DATA
REAL BACKEND
REAL DECISIONS
REAL EVIDENCE
REAL TASKS
REAL AUDIT
NO FAKE OUTPUT
NO EXTERNAL GEOGRAPHY
NO LAT/LON
NO PRECISION REGRESSION
NO S-EVAL LEAKAGE
NO FRONTEND RE-DERIVATION
```

------------------------------------------------------------------------

# 34. FILES TO CREATE / UPDATE

Use the existing repository structure.

Likely backend changes:

``` text
sutra/api.py
sutra/store.py
sutra/memory.py
sutra/packs.py
```

Add helpers only where necessary.

Frontend should live in the Battle-Model structure from the ZIP.

Do not copy the old current-console UI over it.

------------------------------------------------------------------------

# 35. GIT / CHANGE DISCIPLINE

Before editing:

``` bash
git status
```

Create a baseline record.

After implementation:

``` bash
git diff --stat
git diff
```

Verify frozen modules have not changed.

Verify:

``` text
precision config hash unchanged
evidence/memory policy hash unchanged
official dataset hashes unchanged
S-Eval read count unchanged
```

------------------------------------------------------------------------

# 36. DEPLOYMENT

If Docker is available:

``` bash
docker build -t sutra .
docker run --rm -p 8000:8000 -e PORT=8000 sutra
```

Then verify:

``` bash
curl http://localhost:8000/health
curl http://localhost:8000/v1/health
```

If Docker is unavailable:

-   do NOT claim Docker was tested
-   document the blocker
-   still validate the exact runtime filesystem as far as possible

------------------------------------------------------------------------

# 37. FINAL REPORT

Create:

``` text
SUTRA_FINAL_INTEGRATION_REPORT_2026-10-08.md
```

Include:

## Implementation

-   frontend integration
-   backend endpoints
-   task workflow
-   adjudication
-   audit
-   overview
-   score_visit
-   batch
-   case snapshot

## Validation

``` text
existing tests
new tests
HTTP smoke
browser smoke
leakage guard
workspace guard
official data hash
precision hash
S-Eval read count
```

## Honest limitations

Explicitly separate:

``` text
IMPLEMENTED
DESIGNED
NOT YET IMPLEMENTED
NOT MEASURED
```

Never exaggerate benchmark performance.

------------------------------------------------------------------------

# 38. FINAL STOP CONDITIONS

Stop and report instead of improvising if:

-   Google Drive ZIP cannot be accessed
-   ZIP is corrupt
-   expected Battle-Model files are absent
-   API contract conflicts with repository implementation
-   a change would modify frozen intelligence
-   a test requires S-Eval
-   external data would be needed
-   lat/lon would be required
-   Docker is unavailable

Do not silently solve these by inventing behavior.

------------------------------------------------------------------------

# 39. FINAL DELIVERABLE

The final state should be:

``` text
Battle-Model UI
      +
real SUTRA backend
      +
real PS3 data
      +
real task/evidence/audit workflow
      +
real local-metric map
      +
real uncertainty
      +
real verification
      +
77+ regression-safe tests
      +
browser smoke
      +
deployment instructions
      +
judge demo script
```

The central principle:

> **Do not redesign. Do not fake. Do not reopen the intelligence.
> Integrate the existing SUTRA brain into the Battle-Model shell and
> make the entire product truthful end-to-end.**
