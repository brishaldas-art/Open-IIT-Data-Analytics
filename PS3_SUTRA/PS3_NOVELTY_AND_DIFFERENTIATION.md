# SUTRA — NOVELTY AND DIFFERENTIATION

The discipline of this document: **claim novelty only where the research supports it, and never claim "we built a
geocoder"** — geocoding is a mature industry [S1]–[S6]. What follows is what is genuinely different, what is merely a good
engineering practice, and what we explicitly do *not* claim.

---

## 1. First, what is not novel (so that the claim list is honest)

| Not a novelty | Why |
|---|---|
| Geocoding an address | Google, Mapbox, HERE, TomTom, Mappls all do it, at a scale we cannot approach [S1]–[S6] |
| Address parsing/normalisation | libpostal, deepparse, Indic parsers solve this [S12][S15][S16] |
| Learning from delivery/visit traces | GeoIndia, Delhivery, Shiprocket all state field-derived labels as their mechanism [S9][S10][S13][S14] |
| Active learning to choose which visits matter | Settles/Aggarwal and deployed hybrid strategies [S36][S37] |
| Conformal prediction for spatial data | GeoConformal / GeoXCP already published [S24][S25] |
| Drift-triggered retraining with champion/challenger | standard MLOps practice [S31]–[S35] |
| Status vocabulary + manual review for geocoding | shipped in logistics tooling [S48] |
| Weighting logged, biased feedback | Swaminathan & Joachims; Unbiased LambdaMART [S21][S38] |

Anyone claiming those as novelty would be describing the field rather than contributing to it. SUTRA's differentiation is
narrower and, we argue, real.

---

## 2. The six claims (each with the evidence that supports it, and its limit)

### C1 — An **address memory** as the system of record, not a geocoder cache
**Claim:** beliefs are append-only, place-keyed (shared across accounts that mean the same building), versioned with reason
codes, and *decayed* — so "what is known about this place" is an auditable object, not the last answer returned.
**Support:** vendor terms forbid storing their content beyond a short cache window (Google 30 days) and make permanent
caching a *purchased product* ([S8], Mapbox [S4]); no surveyed commercial geocoder exposes its own memory as an artefact.
Logistics tooling captures dispatcher corrections permanently [S48], but as a correction log, not as a versioned belief with
contradictions and decay.
**Limit:** the *components* (versions, decay, provenance) are standard data-engineering; the claim is that they are applied
to address truth as the product's core asset. `[I]` (inference from the survey), not a first-in-the-world claim.

### C2 — **Integrity-weighted evidence** ("weight, don't accuse")
**Claim:** every visit contributes a weight with reason codes, multiplicatively composed from media integrity, trail
agreement, dwell realism, coordinate reuse, accuracy class and a *rolling per-agent baseline*; no single signal can zero a
visit, and no coordinate is ever moved by a signal.
**Support:** spoofing practice is cross-signal inconsistency detection [S27][S26]; our own data shows why: the one planted
integrity anomaly (one agent, 156 duplicate photo hashes = 25.6%) has **pristine GPS** [S90] — a GPS-only detector would
have found nothing. No surveyed system publishes a weight-based, non-accusatory integrity layer for address evidence.
**Limit:** we have no labelled real-world spoofing, so detector performance is measured on injected faults only
(`PS3_RED_TEAM.md` §2) — the claim is about *design and fairness*, not about detection rates.

### C3 — **Negative evidence routed to re-verification, never to coordinates**
**Claim:** outcomes like `address_not_traceable` and `no_such_person` may raise suspicion, table a task, or widen a radius —
but the only code path they have is the graded one of F2.1/D36 — a single negative never relocates a coordinate; accumulated independent negatives demote, widen, mark MOVED_SUSPECTED/CONTESTED and create a verify-first task, and only positive evidence or adjudication can establish a new primary coordinate.
**Support:** the measurement that makes this non-optional: those check-ins sit **1,603.2 m** from surveyed truth at a
**1.3-minute** dwell, and are nearer the vendor pin **84.9%** of the time (vs 3.2% for met-someone visits) [S90].
**Limit:** the taxonomy itself is our design; the *justification* is measured.

### C4 — **A measured radius, published with its coverage**
**Claim:** every answer carries `radius_m` at a nominal level with measured coverage and the calibration stratum, produced
by geographically weighted split conformal; strata too thin to calibrate are widened and labelled
(`calibration_fallback`) rather than given a fake number.
**Support:** no surveyed commercial geocoder exposes a calibrated numeric radius with measured coverage — they expose
discrete levels/match codes [S1][S3][S6]; conformal spatial methods reach 93.67% coverage at 90% nominal where bootstrap
under-covers at 81% [S24][S25].
**Limit:** the method is published work; the novelty is its use as the *shipped contract* of a field-learned geocoder, plus
the explicit refusal to publish numbers for uncalibratable strata.

### C5 — A **two-speed loop with an evidence-shaped fast path**
**Claim:** beliefs update in milliseconds from weighted evidence with no training; models change only through a gated,
buffered, drift-triggered, warm-started, challenger-compared, rollback-capable slow loop — and the fast path is a *product
feature* (in-visit scoring tells the agent where the doubt is while they are standing there).
**Support:** the industry evidence that per-visit retraining is ungovernable and that uncertainty-based triggers cut
retraining from 345 to 16 [S32][S33][S35]; vendor practice shows two-confirmation auto-update exists [S49] and that
collectors already capture geotagged, photo-backed visits [S50].
**Limit:** the loop architecture is standard MLOps applied with unusual discipline; the differentiator is the *split* of
what may change instantly (belief) versus what must be gated (parameters).

### C6 — **Exposure-aware learning and evaluation baked into the loop design**
**Claim:** since visit exposure is demand-driven (measured: 19.9% → 84.8% across delinquency bands [S90]), training uses
propensity weights, evaluation reports weighted and unweighted side by side, and a deliberate 5–10% exploration slice gives
later comparisons an unbiased reference.
**Support:** logged-bandit bias [S38], unbiased ranking [S21], hybrid active learning validated in deployment [S36][S37].
**Limit:** the *techniques* are published; the contribution is their integration into a field-visit loop that would
otherwise grade its own homework.

---

## 3. The composite claim (what we would defend in front of a critical reviewer)

> SUTRA treats field visits as **weighted, reason-coded evidence** feeding an **append-only, decaying, contradiction-aware
> address memory**, publishes **calibrated radii with measured coverage**, and changes its **models only through a gated,
> rollback-capable slow loop** — while never letting negative evidence, a vendor pin, an unweighted agent's report, or a
> single visit decide a coordinate.

Each phrase maps to C1–C6, and each is either measured here or sourced in `PS3_SOURCE_REGISTER.md`. Notably, the composite
does not require the individual pieces to be novel; it requires them to *coexist* with the invariants that make them safe.

---

## 4. Differentiators against the three realistic alternatives

| Alternative | Their strength | Where SUTRA differs (and why it matters in the field) |
|---|---|---|
| **Buy the vendor geocoder** | coverage, freshness, brand trust | vendor content cannot be our system of record (30-day cache [S8]); their error is frozen and their confidence vocabulary is qualitative; SUTRA keeps a per-place memory that improves exactly where the field visits, and reports a measurable radius |
| **Build a better address ML model** (GeoIndia-style, H3 hierarchy) | strong published gains from large trace datasets [S9] | needs millions of traces; our book is 3,117 records with 100 surveyed truths. A model-centric plan would overfit a synthetic generator. SUTRA's accuracy lever is *evidence*, and its memory is useful from the very first visit |
| **Logistics status + manual review** [S14][S48] | ships today, human in the loop | review without weighting, decay or contradictions becomes a queue that rots; SUTRA automates what is safe (belief, radius, priority) and reserves humans for adjudication |

---

## 5. What would falsify the novelty claims (and how we would publish it)

1. If a commercial geocoder began exposing a calibrated radius **with measured coverage**, C4's differentiation weakens to
   an implementation detail.
2. If a survey showed an existing system publishing integrity-weighted, non-accusatory evidence for geocoding, C2 becomes
   "applied practice".
3. If the warm-vs-cold experiment (F) shows no improvement on addresses with ≥ 2 confirmations, C1's *accuracy* value
   collapses to *auditability and triage* — and this document must be rewritten to say exactly that.
4. If the exploration slice never changes any conclusion in experiments J/N/O, C6 becomes prudent bookkeeping rather than a
   differentiator — reported as such.

## 6. Publication-safe statements (the wording we will use)

* "A field-visit-learned address memory with measured uncertainty and integrity weighting" — defensible.
* "We improve on the official frozen baseline geocode arm by X on the surveyed subset (n = 100, interval …)" — only after experiment G runs,
  with the interval and the n attached.
* "We detect spoofed visits" — **never**, without labelled real-world data.
* "India-scale geocoding" — **never**; our claim is per-town, per-book.
* "We built a geocoder" — **never** as a novelty claim; the novelty is what happens *after* the first visit.
