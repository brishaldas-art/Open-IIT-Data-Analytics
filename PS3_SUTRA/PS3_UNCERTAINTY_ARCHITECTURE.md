# SUTRA — UNCERTAINTY ARCHITECTURE

Every coordinate leaves the system with: a **granularity**, a **tier**, a **measured radius with its nominal level and its
measured coverage**, and **reason codes**. A number without those four things is not an answer; it is a guess wearing a
decimal point.

---

## 1. The vocabulary (deliberately borrowed from the systems that ship)

| Our field | Values | Industry counterpart that shaped it |
|---|---|---|
| `granularity` | `town` · `locality` · `street` · `rooftop` | Google's `location_type`, Mapbox's per-component `match_code` (with `plausible` = interpolated/extrapolated), Mappls' eLoc [S1][S3][S6] |
| `tier` | `CONFIRMED` · `PROBABLE` · `APPROXIMATE` · `UNPLACEABLE` (plus the orthogonal `OUT` for outside-town) | geocoding status vocabularies in logistics ("approximately geocoded → flag") [S48] |
| `radius_m`, `nominal`, `measured_coverage` | numbers, always together | GeoConformal/GeoXCP: a radius must carry a coverage claim that is *measured*, not declared [S24][S25] |
| `reason_codes[]` | e.g. `vendor_only`, `locality_match`, `field_confirmed_x2`, `dwell_short`, `pin_agreement_banned`, `outside_town`, `calibration_fallback`, `pack_stale` | the reason is what makes a score auditable [S1][S3] |
| `stage` | `T1` (pre-visit) · `T2` (in-visit) | our leakage contract (`PS3_LEAKAGE_AND_VALIDATION.md` §1) |

`granularity` is **never silently upgraded**: a locality match cannot be rendered as `street`; an interpolated position
cannot be rendered as `rooftop`. If the user needs the distinction, the vocabulary carries it.

---

## 2. How the radius is produced (calibrated, coverage-reported)

**Method: geographically weighted split conformal prediction** [S24][S25].
1. Split the calibration set (grouped, entity-aware) into a proper training part and a calibration part.
2. Fit the model on the training part; compute nonconformity scores (absolute error) on the calibration part.
3. Weight the calibration residuals **spatially** (nearer residuals count more, with a fixed bandwidth per town).
4. For a nominal level α, take the weighted (1−α) quantile → `radius_m` for that (stratum × evidence class × tier).
5. Report `nominal = 1 − α` **and** `measured_coverage` from an independent set — and when they diverge, the divergence is
   published, not hidden.

**Why not a plain bootstrap:** published results show bootstrap under-covering materially (81% observed against a 90%
nominal claim) where geographically weighted conformal reaches ~93.7% [S24]. On our data the practical consequences are
concrete: the vendor's own stratum labels would otherwise be reused as if they were error bounds — and the audit shows a
`pincode` stratum at a **1,375.8 m median with a 4,808 m maximum** (`PS3_DATA_AUDIT.md` §2.6), which no single global
radius can describe.

**What we can honestly calibrate on this dataset (and what we cannot):**

| Stratum | n (surveyed) | Status |
|---|---|---|
| `locality` | 73 | calibratable |
| `street` | 16 | calibratable with a guard; report the interval |
| `pincode` | 10 | **below the n ≥ 15 guard** → parent-stratum fallback, widened, labelled `calibration_fallback` |
| `rooftop` | 1 | not calibratable → declared `insufficient n`, fallback + wide radius |
| `OUT` / unplaceable | 0 (0% geocoded) | no calibration possible; the state is published as unplaceable with its reason |

This is the honest version of "we ship a radius": we ship it where it can be measured, and we widen and label it where it
cannot.

---

## 3. Tier assignment (rule-based, model-informed, auditable)

| Tier | Required evidence | Radius behaviour |
|---|---|---|
| `CONFIRMED` | ≥ 2 independent confirmations, integrity ≥ threshold, position stable within the tier radius | calibrated radius for the evidence class |
| `PROBABLE` | 1 strong confirmation, or 2 weak (e.g. `locked_premises`) | calibrated radius × widening factor (policy) |
| `APPROXIMATE` | coarse candidate only (locality/town arm), or stale `CONFIRMED` | stratum radius, widening with staleness/pack age |
| `UNPLACEABLE` | no candidate, or explicit contradiction unresolved, or `outside_town` | no coordinate returned; reason code required |

The tier is decided by **rules over evidence counts and weights** — not by the ranker's score, and not by a threshold the
ranker could learn its way across. A model may *inform* (e.g. an integrity weight), but the promotion of a tier is a rule
with an audit line.

---

## 4. Negative evidence and refusal (the invariant)

* `address_not_traceable`, `no_such_person`, and other negatives **never relocate a coordinate by themselves** — the
  only code path they have is the graded one of F2.1/D36: accumulation demotes, widens, marks
  `MOVED_SUSPECTED`/`CONTESTED` and creates a verify-first task, and only positive evidence or adjudication can establish
  a new primary coordinate (`PS3_FIELD_EVIDENCE_ARCHITECTURE.md` §F2.1). Measured justification: those check-ins sit
  **1,603.2 m** from truth at a **1.3-minute** dwell, closer to the frozen baseline pin 84.9% of the time [S90].
* Refusal is explicit: `UNPLACEABLE` with a reason, a coverage contribution, and a re-verification path.
  Refusal is *counted* — a model that improves its accuracy by refusing more records must do so visibly, and the
  trade-off is reported (`PS3_EXPERIMENT_PLAN.md` metric set).
* **`OUT` is a state, not an error.** 237 records in the official data are outside every modelled town and 0% geocoded;
  they are handled by a dedicated state so that no downstream consumer mistakes "we don't cover this" for "we failed".

---

## 5. Deciding with uncertainty (how the number is actually used)

| Decision | Rule (published, versioned) |
|---|---|
| Send an agent to this address | requires `tier ∈ {CONFIRMED, PROBABLE}` **or** `APPROXIMATE` with radius ≤ the visit's acceptable travel slack; requires also the notice-eligibility gate ([S48] pattern) |
| Choose which of two addresses to visit first | expected value = f(stake, tier, radius, suspicion, age) — a rule, not a model output |
| Auto-promote a belief to the primary coordinate | two independent confirmations [S49] |
| Emit a shareable code (e.g. DIGIPIN-style) for a confirmed place | only at `CONFIRMED`, and the code is a pure function of the coordinate [S41] — this dataset's local metric plane means the capability is *implemented and switched off* until a real CRS exists |
| Act on a coarse pin for routing/dispatch | blocked by rule; requires `CONFIRMED` or human confirmation |

**Consistency check:** the radius a consumer receives is the radius the *decision rules* use. There is no separate
"marketing radius".

---

## 6. Coverage bookkeeping (the contract we hold ourselves to)

* **Measured coverage** is computed on held-out adjudications/surveyed records per stratum, trended over time, and
  reported with its **n** and a grouped bootstrap interval.
* **Alarms:** coverage below nominal by more than the interval for two consecutive windows ⇒ widen the stratum's radius
  immediately (fast, safe) and rebuild the calibration map in the slow loop.
* **Per-stratum publication:** the radius table (`data/derived/derived_ps3_radius_calibration.csv`) publishes, per stratum,
  the sample it came from and the *evidence class* — including the two lines that exist to prevent misreading:
  the field-visit row is labelled **"agent-generated, not ground truth"**, and the `address_not_traceable` row is labelled
  **"not a location label"**.
* **Never** quote a nominal level as if it were measured; never quote a radius without the stratum; never average radii
  across strata into one "typical accuracy".

---

## 7. Interaction with the loops

| Loop stage | Uncertainty effect |
|---|---|
| fast loop (belief update) | new evidence may widen/narrow the radius, step the tier by one level, or set `CONTESTED`; it never rewrites history |
| staleness / offline pack | radius widens with `pack_age_days` and with belief age; the reason code says which |
| slow loop (retrain) | recalibration is a **gate**: a challenger that improves ranking but worsens measured coverage is rejected (`PS3_DYNAMIC_LEARNING_ARCHITECTURE.md` §3 [5]–[6]) |
| drift | coverage alarms are themselves the drift signal (a stream in the ADWIN detector) |
| cold start | tier caps at `APPROXIMATE`, radius from the parent stratum, reasons `cold_start` + `calibration_fallback` |

---

## 8. What would falsify this design

1. If measured coverage persistently fell below nominal even after spatial weighting and widening, then the honest response
   is to **stop publishing radii at a nominal level** and publish empirical hit-rates per stratum instead. (The audit
   already gives us those: median/p75/p90 by stratum.)
2. If adjudicated labels turned out to be systematically biased toward easy records, the calibration set would need
   re-weighting by exposure — and the report must say so.
3. If the field behaved in a way that makes `distance(check-in, candidate)` uninformative (e.g. agents check in from the
   road for every visit), the evidence classes would need to move to trail-shape-based signals — which is exactly why the
   trail agreement features exist rather than being assumed.


## Amendment U1 — the radius table is published with its calibration n · 2026-10-07

**Measured (official data; fit on train-split truths, evaluated on validation+test):**

| Stratum | n (train / eval) | train p50 | train p80 | eval coverage at p80 | publishable? |
|---|---|---|---|---|---|
| locality | 73 (49 / 24) | 400.3 m | 539.9 m | **79.2%** | yes (n ≥ 15) |
| street | 16 (11 / 5) | 116.1 m | 162.1 m | 100% (n=5) | not independently — parent stratum, labelled |
| pincode | 10 (6 / 4) | 925.5 m | 1,204.2 m | **0% (n=4)** | **no — measured to fail transfer; withheld** |
| rooftop | 1 (0 / 1) | — | — | — | no |

**Why this rule, from the research.** Conformal confidence sets are valid with finitely many datapoints — but only on
the calibration set that produced them [S69]; a nominal radius quoted on n=6 is a coincidence, not a radius. The
geocoding-accuracy literature shows positional error is non-normal, directionally biased, and reaches kilometres on
mis-matches — exactly the pincode stratum here [S73].

**What changes:** (i) the radius payload keeps `radius_m`, `nominal`, `measured_coverage`, `n_calibration` and gains
`source_stratum`, so a fallback is always visible; (ii) strata below the n floor are never published independently;
(iii) the pincode failure is published as a failure in every report that discusses strata; (iv) `UNPLACEABLE`
(including the 237 outside-town records) remains a first-class output (D19) because no radius is honest for them.

**What this changes in the real workflow:** an allocator sees "street-level guess, n=5 behind it" instead of a number
that looks like knowledge.

---


## Amendment U2 — radius semantics reconciled: empirical quantiles first, nominal only when measured (2026-10-07)

**The contradiction.** The requirements (R8.2) say "empirical quantile (e.g., 90th) of held-out error"; the
architecture text drifted into "nominal 90%" and "conformal" interchangeably; the measurement table reports
**p80** radii; and the literature we cite (GeoConformal/GeoXCP `[S24]`) is 90%-nominal with 93.67% measured coverage.
Three different claims were being blended. This amendment fixes the vocabulary:

| Level | What it is | May be published? |
|---|---|---|
| **Empirical quantile radius** | the p80 (or any quantile) of held-out error for the stratum, with its n — **the hackathon default** | **Yes**, labelled as *empirical p80, n = …*, never as a coverage guarantee |
| **Measured coverage** | the observed hit-rate of a radius on an independent set: locality **79.2%** at p80 (n=24 eval); pincode **0% (n=4)** `[S94]` | **Yes**, always beside the radius |
| **Nominal level (conformal)** | a guarantee *only* with its calibration set and exchangeability; our n's are tiny | **Validation/research only** (R8.4) — may be reported in experiment E, never headlined |

**Rules now in force.** (i) The API field `nominal` stays, but a stratrum whose nominal was never *measured* is
published with `nominal = null` and `radius_basis = "empirical_p80"`; (ii) the pincode stratum stays withheld
(transfer failure) with the parent-stratum fallback; (iii) no document may say "90% coverage" where only p80 was
measured — the phrase "90%" appears only next to a measured coverage number; (iv) the n-guard (n < 15 → parent
stratum, labelled) is unchanged from Amendment U1.

**What this changes in the workflow:** the field app shows "≈540 m (empirical, 24 matches)" instead of borrowing
the authority of a 90% guarantee the sample cannot support — the same number, honestly labelled.
