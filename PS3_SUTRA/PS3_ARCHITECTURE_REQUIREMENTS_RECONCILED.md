# SUTRA — ARCHITECTURE REQUIREMENTS RECONCILED

**What this document is.** `PS3_ARCHITECTURE_REQUIREMENTS.md` was written before the final data policy and still
contains requirements that assume a live commercial geocoder, an OSM fallback and vendor budgeting. Under the
official-only decision those requirements cannot both stand. This document resolves every conflict explicitly — one
row per requirement, with the **original requirement**, the **current interpretation**, the **final decision**, the
**reason**, and its **status** (`MVP` · `PRODUCTION-ONLY` · `REJECTED`). The old file remains as history; wherever it
conflicts, this reconciliation governs `[S95]`.

**Reading rule.** `MVP` = part of the 48-hour build. `PRODUCTION-ONLY` = designed and named, not built now, never a
dependency of correctness. `REJECTED` = not built, not planned, kept only as recorded history.

---

## 1. Geocoder integration and candidate sources (R4.x, R5.x)

| Original requirement | Current interpretation | Final decision | Reason | Status |
|---|---|---|---|---|
| **R4.1** MUST consume a commercial/India-native geocoder **at request time** | The supply already contains that geocoder's output: `baseline_geocodes.csv` is a **frozen candidate arm**, not a live service | **`baseline_geocodes.csv` is THE baseline arm.** No Google/Mapbox/HERE/Mappls (or any vendor) is called during the benchmark or the demo. A provider-adapter interface is *reserved by name* for production | The official pack is the only data; live calls would make results irreproducible, licence-bound and unmeasurable here `[S95]` | **MVP** (as the frozen arm) |
| **R4.2** MUST declare per vendor what may be stored and enforce it in code | No vendor content enters the build at all, so the obligation is vacuous today | Keep the `licence_class` column and the "no non-shippable row is served" test; the vendor-cache-clock logic moves to the adapter spec | Same licence-cleanliness intent, now enforced by construction | **PRODUCTION-ONLY** |
| **R4.3** MUST support an **OSM/self-hosted fallback** | External data is prohibited outright — there is no OSM fallback | **REJECTED.** The fallback ladder is internal: cached official arms → memory → `AREA_CONTEXT` → `UNPLACEABLE` | Final data policy; external open data is out of the build `[S95]` | **REJECTED** |
| **R4.4** MAY request multiple candidates from the vendor and keep them | Kept as a *principle*: the system always works on a set, never a single point | Official arms deliver multiple candidates today (vendor pin, town/locality centroid, landmark anchors, address-book anchors, memory) | Preserves option value when sources disagree — now with official sources `[S94]` | **MVP** |
| **R4.5** MUST cap vendor spend with a budget and log lookups | Vendor spend is **zero** in this build | Log every *arm* used per query (already in the response); budget logic belongs to the adapter spec | Removes a cost line rather than managing it | **PRODUCTION-ONLY** |
| **R5.1** MUST produce a top-k candidate set with a source label per candidate | Unchanged in substance | Implemented: `arm`, `source_ref`, `granularity`, `licence_class` on every candidate `[S90]` | The auditability requirement the whole design rests on | **MVP** |
| **R5.2** MUST include a **PIN/locality polygon** candidate on low confidence | The dataset contains **no true PIN polygons**; inventing them is prohibited | Use town / locality / **pincode candidate + centroid** (already measured: locality arm 65.9% coverage, 356.7 m median). Polygon-boundary routing is a production extension for whoever supplies official polygons | Triangles drawn by us would be fabricated geography | **MVP** (centroid) · polygon **PRODUCTION-ONLY** |

## 2. Confidence and uncertainty (R7.x, R8.x)

| Original requirement | Current interpretation | Final decision | Reason | Status |
|---|---|---|---|---|
| **R8.2** radius as an **empirical quantile (e.g., 90th), by stratum** | The measured calibration supports **p80** (and p50) with small n; the "90th" was an example, never a measurement | Ship **empirical p80** per stratum, labelled `radius_basis: empirical_p80` with `n_calibration`; a 90th percentile is used only where n supports it; pincode stratum withheld (transfer failure) | p80 transfer: locality 79.2% (n=24) vs pincode 0% (n=4) `[S94]`; U2 sets the vocabulary | **MVP** |
| **R8.3** widen to a parent stratum when observations are few | Unchanged | n-guard n < 15 → parent stratum, labelled `calibration_fallback` (Amendment U1) | Honest degradation | **MVP** |
| **R8.4** MAY use conformal for validation, MUST NOT headline a coverage guarantee | Now stated mechanically | `nominal` is published **only when measured**; otherwise `null` + `radius_basis`; conformal lives in experiment E | GeoConformal's 93.67% is its dataset's number, not ours `[S69]` | **MVP** |
| **R7.1–R7.4** tier from evidence; `unknown` first-class; calibrate tiers on held-out outcomes | Unchanged; tiers cap the action vocabulary | Implemented as stated; tiers feed the eligibility gate (R11.3) | — | **MVP** |

## 3. Purpose classification and action eligibility (R11.x)

| Original requirement | Current interpretation | Final decision | Reason | Status |
|---|---|---|---|---|
| **R11.1–R11.2** classify home-like / work-like / unknown using dwell, time, POI class, repeats; single observations must not decide | Elevate from a section to a **first-class decision module** | Rule-based classifier with **abstention as the default**; explicit basis codes per decision; no trained purpose model (no labels exist) | R11 was buried in the old document; the due-diligence pass makes purpose → action eligibility the second decision the product makes `[S96]` | **MVP** |
| **R11.3** refuse notice/visit eligibility for work/business or third-party-likely locations unless the borrower confirmed residence | Unchanged, now enforced through the eligibility field of the API | `eligibility.action ∈ {serve, verify_first, refuse}` with a reason; `refuse` blocks the notice decision, not the record | RBI framework: the irreversible act is the notice/visit decision `[S55]` | **MVP** |
| **R11.4** abstain rather than guess | Unchanged | Abstention is a *successful* outcome; counted and reported (D21) | — | **MVP** |
| **R11.5** versioned provenance behind every published coordinate | Unchanged, strengthened | Ownership fixed: store = truth, belief = recomputation, projection = cache (M3) | Audit provision R6.3 | **MVP** |

## 4. Offline, field evidence and the loop (R9.x, R12.x, R13.x, R15.x)

| Original requirement | Current interpretation | Final decision | Reason | Status |
|---|---|---|---|---|
| **R15.1** nightly per-district packs including **PIN polygons** | Packs carry candidates, radii, tiers, purpose priors, direction cues, verify-first tasks — **no polygons** | Drop polygons from the pack schema (they do not exist); packs are versioned and carry their validity window | See R5.2 | **MVP** (pack) |
| **R15.2** offline capture with monotonic local timestamp + device attestation, reconciled on sync | The requirement is executed as the **sync contract** | Client UUID idempotency keys · monotonic `local_seq` · outbox states · server cursor pull · **hold-then-mark-conflict (≤7 days)** · deterministic recomputation `[S81][S82]` | "Highest weight wins" was not a reconciliation rule; ODK's shipped behaviour is the precedent | **MVP** |
| **R15.3** visibly widen radius when a pack is stale | Unchanged | Kept verbatim; staleness is a reason code and a radius widening | — | **MVP** |
| **R9.4** verify-first tasks from low confidence | Now also generated by the *graded negative-evidence rule* (F2.1) | `verify_first` tasks appear for APPROXIMATE tiers, `n_neg ≥ 2`, and `UNPLACEABLE` | Two mechanisms, one cheap action | **MVP** |
| **R13.x** feedback loop | Kept, with the D27/D28 protocol | Prequential replay; propensities logged from the first live window; no per-visit retraining | — | **MVP** (fast loop) / **PRODUCTION-ONLY** (slow loop) |

## 5. What the 48-hour MVP now is (replacing §16 of the old document)

> Resolve an address from **official arms only** → rank with the frozen interface → tier + **empirical** radius + reason
> codes → **`address_purpose`** → **eligibility gate** (`SERVE` / `VERIFY_FIRST` / `REFUSE`) → deterministic
> **landmark direction cues** when a landmark reference exists → one screen showing an address that fails the gate and
> *why* → one scripted historical-style visit that flips a decision → one injected low-integrity observation that
> **widens without moving** (F2.1). All synthetic inputs labelled `SYNTHETIC`. **Zero vendor calls, zero external data.**

## 6. Requirements that were already aligned (no change)

R1.x inputs · R2.x parsing (rules-first) · R3.x normalisation · R6.x ranking (interface `[S96]`) · R7.x (above) ·
R8.1/R8.5 · R9.1–R9.3 · R10.x integrity (media duplication + timing basis, Amendment F1) · R12.1 storage (contract in
the lock candidate §L) · R14.x API (amended with purpose/directions/eligibility) · §18 non-requirements (unchanged; it
now also excludes *any* external geographic source explicitly).

---

*Sources: `PS3_SOURCE_REGISTER.md` — `[S55]` RBI framework · `[S69]` conformal practice · `[S81][S82]` offline-sync
precedent · `[S90][S94]` official-data measurements · `[S95]` final data policy · `[S96]` due-diligence pass. Binding
data policy: `PS3_FINAL_DATA_AND_ARCHITECTURE_FREEZE.md`. Locked architecture: `PS3_ARCHITECTURE_LOCK_CANDIDATE_2026-10-07.md`.*
