# PS3 — ARCHITECTURE OPTIONS

**Phase 4, File 5 of 13.** Seven options that differ in *kind*. Scored with the same weights as PS2 (20/15/15/15/10/10/10/5).

**The measurement that frames all of them** `[DATA]`:
- Vendor baseline vs survey: mean 532.7 m · median **376.4 m** · p90 839 m · 9% under 100 m.
- Free-data candidate ceiling (oracle over candidate sets): **370 m**, 2% under 100 m. Naive landmark snapping: 4,093 m (worse in 90%).
- Field-evidence fusion on met-someone visits: **385 m → 29 m**, 87% improve, 82% under 100 m.
- Vendor `precision` strata medians: rooftop 37.7 · street 134.9 · locality 367.4 · pincode **1,336.5** m (two independent samples agree).

**Therefore:** point accuracy is *already* what the market sells; what is missing is (1) honesty about the error, (2) a mechanism to spend field evidence, (3) protection against poisoned evidence.

---

## P1 — Calibrated truth only *(radius honesty, no point change)*

**What it is.** Accept the vendor's point; replace the *silent* error with a **published per-stratum radius** derived from the 100 surveyed addresses, plus a coverage check.

**Components.** `precision` stratum × town lookup → radius (p50/p90) → downstream decisions consume `P(truth within r)`; coverage monitor; retrained when labels arrive.

**Data.** 100 surveyed addresses `[DATA]`; `derived_ps3_radius_calibration.csv`.

**Proves.** That the current system is confidently wrong in 1.3 km increments. **Cheapest high-value change in the whole submission** — it flips a hidden failure mode into a visible one with no model at all.

**Cannot prove.** Any improvement in point accuracy; it is a *disclosure* architecture.

**Scoring.** Align 5 · Value 5 · Depth 3 · Diff 4 · Data 5 · Prod 5 · Feas 5 · Expl 5 → **4.60**

---

## P2 — Evidence-fusion-first

**What it is.** Make the field visit the sensor. A visit produces a GPS trail with per-point `accuracy` (median 9.8 m, median 26 points/visit), a dwell pattern, an outcome code, and media. Fuse those into a posterior for the address, weighted by outcome sign and dwell.

**Components.** (1) integrity gate — mock-location flag, teleport check, duplicate-media hash, cross-check against the check-in (645 check-ins are >500 m from their own trail, 11.6% `[DATA]`); (2) stationary-cluster stop detection; (3) likelihood weighting by dwell — a 2-minute check-in that says `address_not_traceable` sits **1,603 m** from truth and 195 m from the pin, i.e. negative outcomes manufacture false locations `[DATA]`; (4) posterior update against the vendor prior; (5) one-line explanation per shift.

**Proves.** 385 m → **29 m** where evidence exists `[DATA]`. **Cannot prove.** Anything for the ~64% of addresses never visited at mobile-verified precision.

**Scoring.** Align 5 · Value 5 · Depth 4 · Diff 5 · Data 5 · Prod 4 · Feas 5 · Expl 5 → **4.70**

---

## P3 — Parse → retrieve → rank pipeline *(data-quality-first)*

**What it is.** Fix the input before touching the output: normalise script/abbreviation, split the address into administrative levels with an open Indic NER model, retrieve candidates from a gazetteer index, rank them, and return "no confident candidate → field task" when the evidence is thin.

**Components.** `addressparser` (IndicBERTv2-SS + CRF, <30 ms) `[S-46]`; gazetteer from towns/localities/POIs present in the dataset plus open address data `[S-52]`; BM25/embedding retrieval; rule-first ranking (PIN match > locality match > token overlap); abstention.

**Proves.** A cleaner input, a candidate list instead of a single pin, and — importantly — a **cheap, defensible** build. **Cannot prove.** Accuracy beyond the 370 m ceiling: our own oracle experiment caps it `[DATA]`. The brief's prohibition on fake sophistication means this option must be sold as *hygiene + abstention*, never as an accuracy story.

**Scoring.** Align 5 · Value 4 · Depth 3 · Diff 3 · Data 5 · Prod 4 · Feas 4 · Expl 5 → **4.20**

---

## P4 — Probabilistic posterior engine *(distribution-first)*

**What it is.** The deliverable is not a point but a **distribution over coordinates**: vendor stratum kernel (prior) ⊗ field-evidence likelihood ⊗ landmark likelihood, reported with mode, mean and a high-density region. Downstream, everything is a probability query (`P(within 200 m) = ?`).

**Proves.** That decisions, not maps, are the product. **Cannot prove.** Sub-100 m precision where no evidence exists — the posterior will simply be honest and wide, which is the correct answer and a harder thing to demo.

**Risks.** Fake grid precision; product-of-experts overconfidence (needs tempering); explaining a density to a field officer (mitigate: render as a heat map + one search radius).

**Scoring.** Align 4 · Value 4 · Depth 5 · Diff 5 · Data 3 · Prod 4 · Feas 3 · Expl 3 → **3.95**

---

## P5 — Compounding map *(feedback / active learning first)*

**What it is.** The system's asset is a growing set of **field-confirmed coordinates**: two independent confirmations promote a pin to canonical; promoted pins improve retrieval for every future address in that building/street; and an acquisition function chooses *which* address to verify next to reduce portfolio-wide uncertainty fastest.

**Components.** confirmation rule (2 independent, integrity-passing visits) `[S-56]`; promotion event with provenance; retrieval index over confirmed pins; acquisition scoring (uncertainty × account value × visit cost).

**Proves.** Compounding returns — the only PS3 mechanism whose value *grows* with usage. **Cannot prove.** Day-one accuracy gains; it needs visits, and it must be guarded against reinforcing a wrong pin.

**Scoring.** Align 4 · Value 5 · Depth 4 · Diff 5 · Data 4 · Prod 5 · Feas 5 · Expl 4 → **4.55**

---

## P6 — Decision-coupled routing *(PS2-into-PS3)*

**What it is.** Spend field slots where location uncertainty is *expensive*: rank addresses by `P(within 200 m)` × outstanding balance × visit cost, not by error magnitude alone. The geocoder's uncertainty becomes an input to the PS2 allocator, and confirmed visits become evidence back in PS2's belief state.

**Proves.** That PS3 without PS2 is a map, and PS2 without PS3 is blind — the integrated thesis (File 11). **Cannot prove.** Benefits without the cost table; and it needs both systems built.

**Scoring.** Align 5 · Value 5 · Depth 4 · Diff 5 · Data 4 · Prod 4 · Feas 3 · Expl 4 → **4.45**

---

## P7 — Provider orchestration & compliance layer

**What it is.** Treat geocoding as a *vendor risk* problem: a pluggable provider interface (Google, Mappls, open), a cache-policy guard (Google: lat/lng ≤30 days, no permanent storage of other content, no training on output `[S-48]`; Nominatim 1 req/s `[S-51]`; NDSAP non-commercial `[S-65]`), and an audit log.

**Proves.** That the long-lived canonical coordinate must be ours (field-confirmed), with vendor results as time-limited priors. **Cannot prove.** Accuracy; it is a licence/latency/outage architecture.

**Scoring.** Align 5 · Value 3 · Depth 2 · Diff 3 · Data 5 · Prod 5 · Feas 5 · Expl 4 → **4.05**

---

## Comparison

| | P1 Calibrated truth | **P2 Evidence fusion** | P3 Parse→retrieve→rank | P4 Posterior engine | **P5 Compounding map** | **P6 Decision-coupled** | P7 Provider layer |
|---|---|---|---|---|---|---|---|
| Align (20) | **5** | **5** | **5** | 4 | 4 | **5** | **5** |
| Value (15) | 5 | 5 | 4 | 4 | 5 | 5 | 3 |
| Depth (15) | 3 | 4 | 3 | **5** | 4 | 4 | 2 |
| Diff (15) | 4 | **5** | 3 | **5** | **5** | **5** | 3 |
| Data (10) | 5 | **5** | 5 | 3 | 4 | 4 | 5 |
| Prod (10) | **5** | 4 | 4 | 4 | **5** | 4 | **5** |
| Feas (10) | **5** | **5** | 4 | 3 | **5** | 3 | **5** |
| Expl (5) | **5** | **5** | **5** | 3 | 4 | 4 | 4 |
| **Weighted** | **4.60** | **4.70** | **4.20** | **3.95** | **4.55** | **4.45** | **4.05** |

**Construction rule.** P2 (fusion) is the accuracy engine; P5 (compounding) is what makes it an asset; P1 (calibrated truth) is the honesty layer that must ship even if P2 slips; P6 is the integration thesis; P3 is the hygiene prerequisite that makes P2/P5 work on messy text; P7 is the compliance envelope; P4 is the elegant-but-optional expression of the same idea as P1+P2 (it is *how* the posterior is represented, not a competing product). Chosen composition and the cut-line logic: `PS3_ARCHITECTURE_SELECTION.md`; specification: `PS3_SUTRA_SOLUTION_ARCHITECTURE_FINAL.md`.

**One sentence to remember.** The only two PS3 numbers that matter are **370 m** (what public data can reach — our own oracle test) and **29 m** (what field evidence reaches when it is trusted correctly). Every architecture above is an argument about which of those two numbers the product should promise.
