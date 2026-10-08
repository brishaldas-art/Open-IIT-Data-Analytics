# PS3 UPDATED BUSINESS DATA FLOW — how CreditNirvana actually operates, read from the official data

**Question this document answers** (the brief's §12): not "which extra columns can feed a model" but **what the shared data reveals about how the company works, where effort is wasted, what knowledge is lost, and how every future field interaction can become durable, reusable knowledge** — with PS3 as the layer that makes that happen.
Every figure below is official, in-scope data, and reproducible from `data/derived/`.

---

## 1. How an address enters the company

| Path | Count | What it means |
|---|---|---|
| KYC origination | 3,090 (99.1%) | The address arrives as lender paperwork, written in whatever the branch captured |
| Skip trace | 27 (0.9%) | The address arrives because an earlier process couldn't find the borrower |

The written text is then **never structurally repaired**: 24.9% carry no comma at all, 8.4% are mixed-script, and 93.3% end in a trailing 6-digit token — 260 of which match no known pincode. The company's memory of a place begins as prose.

## 2. How it is processed — and where the first failure occurs

The incumbent step is the vendor geocoder: **2,880 of 3,117 addresses (92.4%) get a pin; 237 get nothing.** The pins are coarse — on the 100 survey-grade addresses the median error is **376.4 m** and only **9.0%** land within 100 m. Two-thirds are locality-level (`precision` = locality: 2,052 of 2,880). So the very first automated decision — *which door* — is made at street-block resolution, and 237 addresses are made with no pin at all.

## 3. When a visit happens, and who pays for it

Median **14 days** between an address entering and its first visit (p90: 66 days). Visits are allocated on the collections book: exposure rises steeply with delinquency (440 visits in the 0–30 DPD band vs 276 in 361+ per band-population, concentrated by policy), while **yield stays near-flat** (37.5%–42.9% met across bands). Effort is targeted; outcomes are not very sensitive to that targeting.

The effort profile of the book (official data):
- 1,477 of 3,117 addresses ever visited (47.4%) — in **5,578 visits**;
- **73.5% of those visits (4,101) go to an address already visited at least once**;
- **577 addresses never produce a contact in any visit, absorbing 1,650 visits (29.6%)**;
- first-visit yield 37.8% met; repeat-visit yield 41.7%;
- addresses that were ever confirmed still attract 6.2 visits on average.

## 4. What gets recorded — and what survives

| Recorded | Survives as | Evidence |
|---|---|---|
| Check-in coordinates | usable location evidence of the visit | median 9.8 m accuracy; all check-ins lie on the agent's own walked path (max 90.8 m from the nearest trail point) |
| GPS trail | process evidence (footpath, stop detection) | 160,406 points across 100% of visits |
| Dwell | weak quality weight | median 207 s; its link to outcome is a synthetic artefact — weight, do not trust |
| Outcome enum | the learning signal | 7 classes; `address_not_traceable` 25.1% |
| Photo hash | integrity control | 172 visits share a hash with another visit by the same agent (FA009: 162/610) |
| Free-text remark | **the only channel that ever corrects a location** | 208 visits (3.7%) name a landmark — *"actual house behind Park, 2 lanes ahead"*; **0 name a locality**; 762 distinct remark strings for 5,578 visits |

**What is lost today:** the corrective content of those 208 remarks is written as prose, attached to one visit, and — in any workflow that stores only the outcome enum — never becomes a property of the *place*. Meanwhile the outcome enum itself is systematically over-read: `address_not_traceable` check-ins sit a median **1,603 m** from the true location and are *closer to the wrong pin* 84.9% of the time. The most common sentence in the field data is not "the house is here" — it is "I could not find it".

## 5. How the same address appears again

Three distinct ways, all officially measured:

1. **Repeat visits to one `address_id`** — 1,071 addresses revisited; 73.5% of all visits.
2. **Two accounts at one place** — 191 addresses form **81 co-located clusters** (met check-ins within 30 m, every pair a *different* account, 58 of 127 pairs across the official splits). The same building is worked for different borrowers, with no shared identity.
3. **The same written template** — 70 render-key families (203 rows, 184 of them `permanent_native` villages differing only in the trailing token); identity-key collisions are 5 groups / 10 rows.

## 6. Can historical knowledge prevent unnecessary work?

The data says yes, twice:

- **Memory beats the pin by an order of magnitude.** Where a met-someone visit exists, its check-in sits **24.0 m** (median) from the survey truth versus **380.3 m** for the vendor pin — and on the honest (non-training) subset, 21.1 m vs 383.7 m, memory better in 80% of cases.
- **Confirmed knowledge raises later yield.** Addresses confirmed before the 2026-05-15 cut and re-visited after it succeed **56.0% met** (1,383 post-cut visits) versus **24.5%** for addresses never previously confirmed (1,343) — and on val+test accounts only, **56.7% vs 25.1%**. (Corrected 2026-10-07: the earlier *40.5%* was the overall post-cut rate, not the cold rate.)

Both are statements about *reusing knowledge that already exists* — not about spending more effort. They are the evidence base for the workflow change: **a confirmed place should never be re-derived from scratch, and an unconfirmed address should not keep consuming visits without a structured conclusion.**

## 7. The structured form every future interaction should take

One capture template, ~20 seconds of taps (offline-capable), designed so that today's visit becomes tomorrow's knowledge:

| Captured | Why it exists |
|---|---|
| Outcome (fixed vocabulary incl. "not traceable", "locked", "met") | the evidence class |
| **If met**: confirm/adjust the place — one tap on a candidate or a nudge on the map | converts a successful visit into a durable location fact |
| **If not met**: *why*, and *what is nearby* (landmark pick-list, not prose) | turns today's failures into tomorrow's directions; today 208 agents wrote this by hand |
| Dwell + GPS trace | quality and integrity weight |
| Photo (hash-checked) | integrity and evidence of the door |
| Linked place identity (cluster candidate) | so two accounts at 21 m become one place |

The instrument to measure whether this works already exists in the official data: the 2026-05-15 cut test (56.0% warm vs 24.5% cold; 56.7% vs 25.1% on val+test) and the memory-vs-pin comparison (24.0 m vs 380.3 m). Both are re-runnable every window.

## 8. How this reduces wasted operational effort (without proposing fewer visits)

| Waste pool (official figures) | Mechanism PS3 changes |
|---|---|
| 4,101 repeat visits with no memory of the last one | confirmed places become reusable facts, so repeat visits start warm instead of from the vendor pin |
| 1,650 visits to 577 addresses that never confirm (29.6%) | place-level conclusions + honest abstention → those addresses get screened/documentary handling before consuming slots |
| 237 addresses with no pin at all | the no-pin path becomes a first-class worklist with candidate sets instead of a guess |
| 376.4 m median pin error → wrong-door risk on a compliance-sensitive visit | memory + radius + directions; the notice goes to the right door |
| 208 corrective remarks dying in prose | landmark knowledge becomes structured place evidence |
| Two borrowers at one building worked twice | place identity shared across accounts (81 clusters visible today) |

Nothing in this list removes a visit; every line makes a visit that is already happening cheaper to target and richer in return.

## 9. What the re-audit changed about this story — and what it did not

**Changed:** the case now rests on official in-scope data alone (`accounts`, `addresses`, `agents`, `field_visits`, `lenders`, `splits` + the six PS3 tables). The excluded tables (`payments`, `dial_attempts`) are exactly the ones that would have let the story drift from "we find places" to "we collect money". The place-sharing evidence is now a number (81 clusters / 191 addresses), the remark channel is a number (208 / 3.7%), and the memory premise has been re-verified outside the training split.

**Not changed:** the workflow diagnosis, the waste pools, and the product position — an address/location-intelligence layer that makes each existing visit worth more, fed by every visit already happening.
