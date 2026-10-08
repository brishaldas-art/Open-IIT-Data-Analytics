# PS3 — SUTRA · address belief, field evidence and the honest radius

**Section owner's brief.** Everything that defines, researches, scores or specifies PS3 lives in this folder. If it is not here, it is in `../` — §5 names the shared files PS3 depends on.

---

## 1. What PS3 is, in one paragraph

CreditNirvana asks for address intelligence for the field-recovery workflow: **can this borrower be found at this address, how far might we be wrong, is this visit worth a slot tonight, and what did the last visit teach us about this address?** Our answer (**SUTRA**) is not a geocoder. It keeps an `ADDRESS_STATE` per address: parse and normalise the Indian address text, retrieve candidates, keep the commercial geocoder's point as a *prior* (never as truth), run an **integrity gate** before learning from any visit, fuse field evidence — GPS trail, dwell, outcome sign, media sanity — into a posterior, express uncertainty as a **per-stratum conformal radius validated on two independent samples**, and publish exactly two things outward: `P(truth within r)` for PS2's field-slot decision, and promotion events when a coordinate is confirmed twice.

**The three artefacts that carry PS3:** the **calibrated radius table** (the geocoder already tells us its error band and nobody uses it), the **field-evidence fusion** (385 m → 29 m where evidence exists), and the **integrity gate** (so the learning loop cannot poison itself).

---

## 2. Reading order

| # | File | What it is | Status |
|---|---|---|---|
| 1 | `PS3_DEEP_INTERNET_RESEARCH.md` | The real address problem: Indian parsing approaches compared, commercial geocoders and their licence terms, advanced Indian geocoding research, GPS/field-evidence integrity, confidence representation, field-force optimisation, datasets and licences | CURRENT |
| 2 | `PS3_ASSUMPTIONS.md` | PS3 re-read from scratch + register B1–B6 + the three findings that invalidated part of the original PS3 story + the four-part defensible residue | CURRENT |
| 3 | `PS3_ARCHITECTURE_REQUIREMENTS.md` | MUST / SHOULD / MAY checklist for PS3, each tied to evidence and workflow impact | CURRENT |
| 4 | `PS3_ADVANCED_ARCHITECTURE_RESEARCH.md` | Fifteen architectures compared (vendor wrapper → multi-vendor consensus → parse-then-geocode → retrieval+ranking → learned ranker → hierarchical cells → landmark anchoring → field fusion → map matching → conformal → probabilistic → feedback → compliance layer → place graph → hybrid) | **BINDING input** |
| 5 | `PS3_ARCHITECTURE_OPTIONS.md` | Seven buildable options scored, with the evidence table that decides them | **BINDING input** |
| 6 | `PS3_ARCHITECTURE_SELECTION.md` | The weighted decision, worked arithmetic, the rejected alternatives (HMM map matching, cell prediction, landmark snapping, learned ranker), the risk register and the cut-line | **BINDING decision** |
| 7 | `PS3_SUTRA_SOLUTION_ARCHITECTURE_FINAL.md` | **The architecture we build — 30 sections.** Parse → retrieve → rank → prior → integrity gate → fusion → conformal radius → PS2 contract → promotion, with the two-sample calibration table, the licence envelope, failure paths and the build plan | **BINDING** |
| 8 | `data/derived/derived_ps3_radius_calibration.csv` | The radius table PS3 must output — nine strata, from two independent samples, with hit rates at 100 m / 250 m / 500 m | **BINDING baseline** |
| 9 | `PS3_SUTRA_SOLUTION_ARCHITECTURE.md` | The Phase-2 hypothesis (26 sections) | **SUPERSEDED** — kept as the reasoning record; file 7 replaces it |

---

## 3. The numbers PS3 stands on (all reproducible)

Run `tools/reproduce.sh p3` — every figure below comes back.

| Fact | Value | Why it matters |
|---|---|---|
| Vendor baseline vs 100 surveyed addresses | mean 532.7 m · median **376.4 m** · p90 839 m · only **9%** under 100 m | The current pin is not walkable-to, and nothing in the workflow says so |
| **Stratum spread (the opportunity)** | median distance-to-truth by vendor `precision`: rooftop **37.7 m** · street **134.9 m** · locality **367.4 m** · pincode **1,336.5 m** | A 35× spread hidden inside one "geocoded" flag — the vendor's own label is the stratum key. Two independent samples agree (survey medians 25.6 / 108.6 / 385.9 / 1,375.8 m) |
| Free-data ceiling (our oracle test) | best achievable from candidate sets built on free text: **370 m** median, 2% under 100 m; naive landmark snapping **4,093 m**, worse than baseline in 90% of cases | No retrieval/ranking architecture crosses the gap — we state 370 m on the slide instead of pretending |
| **Field evidence** | on visits where the agent met someone: **385 m → 29 m** median, 87% improve, **82% under 100 m** | The accuracy engine is the visit, not a better geocoder |
| GPS quality | median 26 points/visit · median `accuracy` 9.8 m | Enough signal for stop detection; `accuracy` is a 68% radial convention |
| **The poison trap** | `address_not_traceable` check-ins sit **1,603 m** from truth and 195 m from the pin with 2-minute dwell; **645 check-ins (11.6%)** are >500 m from their own trail; one agent has **162/172 duplicate photo hashes** (26.6% vs ≤1% elsewhere) | Negative outcomes *manufacture* false locations — the gate must run **before** fusion, and negative outcomes may never move a point |
| Honest intervals | conformal spatial prediction: **93.67%** empirical coverage at 90% nominal vs **68.33%** for bootstrap | We publish coverage and a coverage monitor rather than claiming a guarantee |
| Field waste today | 2,649 of 5,578 visits (47.5%) end `not_traceable` or `locked` | The pool where calibrated radii + integrity + confirmation pay for themselves |

**Verdict of the selection arithmetic:** the hybrid (parse → retrieve → rank → posterior → conformal → fusion → feedback) scores 4.75, with field-evidence fusion (4.70) and calibrated truth (4.65) close behind — again *layers of one system*, shipped in the cut-line order: radius + PS2 contract first, then gate + fusion, then promotion, then parse/retrieve.

---

## 4. Build scope (frozen)

`BUILD NOW` — per-stratum radius table + `P(within 200 m)` · integrity gate · dwell- and outcome-weighted fusion (stationary-cluster stop detection) · two-confirmation promotion with revocation · discrete distribution output as the PS2 contract · per-town coverage calibration.

`BUILD IF TIME` — Indic address parsing and canonicalisation · confirmed-pin retrieval index · building-level identity graph (dedup across 3,117 addresses / 2,400 accounts) · active-learning task selection · officer view.

`RESEARCH ONLY, with the precondition recorded` — HMM map matching (**no road graph in the data**) · hierarchical H3 cell prediction (proprietary corpus; 3,117 addresses would only learn locality level) · learned candidate ranker (oracle ceiling 370 m; 100 labels) · continuous-grid probabilistic map · learned GPS-spoof fingerprinting (no device telemetry).

---

## 5. What else in this section PS3 leans on (and why)

| File in this section | Why PS3 needs it |
|---|---|
| `PS2_PS3_DATASET_REVIEW.md` §2, §4, §5, §8 | The PS3 evidence, the official-vs-our framing reconciliation, the twelve traps (landmark table incomplete, no road graph, metric plane with no polygons) and the requirement verdicts |
| `tools/dataset_audit.py` | Regenerates every `[DATA]` number above (`p3` section), including the planted bad actor |
| `tools/build_derived_table.py` | Rebuilds `data/derived/derived_ps3_radius_calibration.csv` from the two samples |
| `SANKET_SUTRA_SYSTEM_ARCHITECTURE_FINAL.md` | The two contracts and the joint trace-vs-visit decision PS3 prices |
| `SIMILAR_SYSTEMS_REVERSE_ENGINEERING.md` | GeoIndia, Mappls, logistics geocode-feedback and field-integrity tear-downs — where the loan of these patterns comes from |
| `ARCHITECTURE_RESEARCH_BIBLIOGRAPHY.md` | Every `[S-nn]` citation PS3 uses, with the licence entries (Google ≤30-day cache, Nominatim 1 req/s, NDSAP non-commercial) |
| `ARCHITECTURE_DECISION_LOG_FINAL.md` | ADR-20…ADR-28: what PS3 decided, and what would reverse each decision |
| `CN_QUESTIONS.md` | Does CN hold visit-level GPS with accuracy and dwell? That single answer decides whether PS3 has a learner or is a gate-and-radius product |

---

## 6. Run it

```bash
cd PS3_SUTRA                      # this section; the sibling is the same shape
bash tools/reproduce.sh q p3 eco  # every number below, and rebuilds data/derived/derived_ps3_radius_calibration.csv
bash tools/check_section.sh        # the section's invariants; must print ALL CHECKS PASSED
bash tools/build_package.sh        # this section's zip + the combined zip
```

**Honesty rules that bind this section:** never present a vendor pin as ground truth (canonical coordinates must be field-confirmed — Google's terms permit only a ≤30-day lat/lng cache); never let a negative visit outcome move a coordinate; never report an accuracy figure without stating which sample it came from; `unknown` is a first-class output; and the 29 m result is a *mechanism demonstration on synthetic evidence*, not a promise about real Indian GPS.
