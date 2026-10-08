# PS3 — BUSINESS AND OPERATIONAL RETHINK

**SUTRA: *Address Geocoder That Learns from Field Visits.***
A deliberate challenge to our own architecture, written from the company's side of the table: what PS3 actually requires,
where the operational pain and money sit, what field visits genuinely contribute, what knowledge the company loses
today, and what — if anything — our current design gets wrong.

---

> **SUPERSESSION NOTE — 2026-10-07 (official-scope re-audit).**
> The §L row "two accounts at one building — 5 duplicate-text groups / 10 rows at minimum" understates the measured
> position. Re-audited on the corrected official scope: **191 addresses form 81 co-located clusters** (met check-ins
> ≤30 m apart, every pair a different account, 58 of 127 pairs across the official splits), alongside 5 identity-key
> text groups. The memory premise is re-verified outside the training split (val+test: 21.1 m vs 383.7 m pin, better in
> 80%). Detail: §4 and §11 of the official-scope re-audit's *Updated EDA* (sibling re-audit set, outside this workspace). The §L conclusion is unchanged — place identity
> keyed on evidence, not on `address_id` — and is now better evidenced.



> **CORRECTION LOG — 2026-10-07 (v2, official-scope re-audit).**
> Two figures in this document are corrected. (1) Every occurrence of *"56.0% vs 40.5% for all other post-cut visits"*
> mislabels the second number: **40.5% is the overall post-cut met rate**. The correct decomposition of the
> 2026-05-15 cut is **warm (confirmed before the cut) 56.0% met over 1,383 post-cut visits vs cold 24.5% over 1,343**
> — and on the honest, non-training subset (val+test accounts only) **56.7% vs 25.1%**. The finding is stronger than
> previously written; the tables above and below are unchanged because no architectural statement depended on the
> mislabelled number. (2) Where this document says same-agent vs different-agent re-visits land 90.0 m / 98.0 m apart,
> the re-measurement with a stated definition (median of per-address medians, 563 addresses) is **77.7 m / 75.8 m** —
> the same conclusion (memory consistency is agent-independent). Detail: the v2 *Updated EDA* and *Reconciliation* in
> the sibling re-audit set outside this workspace.

**Ground rules used throughout**

| Rule | How it is applied here |
|---|---|
| PS3 only | No other problem statement is referenced or depended on |
| Official dataset only as *data* | Every measured number is from `data/official_ps3/` (11 tables, 177,190 rows when this document was written; **12 tables · 177,196 rows as of 2026-10-07**, when the assigned `lenders` table joined the frozen tree). External research is cited as **published practice**, `[S##]`, and **never enters the data, the training set or the headline metric** |
| No invented economics | No ROI figure, no per-visit cost for CreditNirvana, no savings percentage. Where external prices are quoted they are labelled as third-party list benchmarks and are **not** multiplied into any claim |
| Claims tagged | `[DATA]` measured from the official dataset · `[V]` verified external · `[VENDOR CLAIM]` published by a vendor about itself · `[I]` our inference · `[A]` assumption · `[UNKNOWN]` not knowable from what we hold |
| Current design is a hypothesis | Sections N/O/S exist to attack it; anything that survives is stated with the evidence that lets it survive |

**The single most important new measurement in this document** (official data only, reproducible):

> On the 38 surveyed addresses that ever produced a met-someone visit, the *check-in coordinate of that visit* sits
> **24.0 m** (median) from the surveyed truth — **87% within 100 m** — while the vendor pin on the same 38 addresses sits
> **380.3 m** away with **5% within 100 m**. The field evidence is better in **89%** of cases. `[DATA]`

That is PS3's premise, measured. Everything else in this document is about the operational machinery required to turn
that single fact into something the company can run, audit and keep.

---

## A. EXACT PS3 PROBLEM

### A.1 The problem statement, as given

> *"An address geocoder that learns from field visits. Indian addresses are descriptive and landmark-based,
> mixed-language, transliterated, misspelt. Commercial geocoders land at locality/pincode centroids. Output must be
> lat/lon + confidence radius + landmark-based directions, continuously learning from new successful visits. The field
> app must work offline."*

### A.2 What the PS actually requires — five clauses, nothing more

| # | Requirement (verbatim trigger) | What it demands operationally | Does the official data support it? |
|---|---|---|---|
| R1 | *"address geocoder that learns from field visits"* | a system whose *location output changes* as a result of what field agents observe | **Yes** — 5,578 visits, 2,268 met-someone, and the 24.0 vs 380.3 m result above `[DATA]` |
| R2 | *"Indian addresses are descriptive and landmark-based, mixed-language, transliterated, misspelt"* | tolerate landmark phrasing, 3 scripts, misspellings | **Partly** — 25.2% of records name a landmark, 8.41% are non-ASCII (Devanagari 154, Kannada 108), and the rare-token tail is dominated by misspellings of gazetteer names `[DATA]` |
| R3 | *"Output must be lat/lon + confidence radius + landmark-based directions"* | **three** outputs, one of which is an *uncertainty*, one of which is *human-readable guidance* | **Yes for the radius** (vendor label ⇒ 13× error spread across strata); **weak for directions** — the landmark table is 240 rows with 14 distinct names `[DATA]` |
| R4 | *"continuously learning from new successful visits"* | an eligibility rule (what counts as *successful*), an update path, and a way to be wrong safely | **Yes in principle** — 2,224 visits (39.9%) pass a conservative "successful" test today; 439 addresses carry ≥2 independent confirmations `[DATA]` |
| R5 | *"The field app must work offline"* | offline is a **product requirement**, not an infrastructure detail: what the agent carries, what they can capture, what happens when they return | **Not testable on this dataset** — no device, sync or session data exists here `[UNKNOWN]` |

### A.3 Separating four things people constantly conflate

| | |
|---|---|
| **A · What the PS requires** | R1–R5 above. Nothing about memory stores, integrity scoring, drift detection, calibration regimes, H3 cells, digital address codes, ranking models, LLM parsing, or dashboards |
| **B · What the data supports** | 3,117 addresses; 2,880 vendor pins with a **granularity label**; 5,578 visits with outcomes, dwell, trails, media; 100 surveyed truths; 3 towns / 36 localities / 240 landmarks; an account-level official split. Testable: retrieval quality, ranking value, evidence behaviour, radius behaviour, reuse behaviour, eligibility rules |
| **C · What our current SUTRA design proposes** | parse → resolve → candidates → rank → belief → uncertainty → evidence → integrity → memory → slow loop, with a place-identity layer, decay, contradiction handling, drift detection, conformal-style radii, an exposure-weighted learner, and a rule table for evidence |
| **D · What is merely our assumption** | that the company will run a memory store; that agents can capture structured evidence without friction; that a *learned* evidence model is needed at all; that decay curves are fittable; that drift exists in 89 days; that "two confirmations" is the right promotion threshold; that CN's field cost is material relative to its digital channels; that a wrong pin translates into a wasted visit rather than a compliance event |

### A.4 The problem in operational language

Forget "geocoder". The operational statement is:

> **The company holds 3,117 addresses it cannot trust, sends people to them, and throws away what those people learn.**
> It cannot say how far off any address is, it cannot tell an agent where to look beyond a dropped pin, it cannot stop
> the same address being worked repeatedly, and it cannot prove to anyone what happened at the door.

Four measured facts make that concrete:

| Fact | Number | Source |
|---|---|---|
| The vendor's answer is coarse and unlabelled in practice: **71.2% of pins are locality-level**; median error **376.4 m**; only **9.0%** within 100 m | 2,880 pins / n=100 truths | `[DATA]` |
| Field effort is dominated by **repeat** work: **73.5% of all visits (4,101 of 5,578) are visits to an address that had already been visited** | 5,578 visits | `[DATA]` |
| A large block of effort produces **no knowledge at all**: **577 addresses (39.1% of visited) never produced a confirmation**, absorbing **1,650 visits (29.6%)** | 5,578 visits | `[DATA]` |
| Coarse pins are concentrated in failure: `pincode`-stratum addresses fail **51.8%** of visits and only **55.8%** are ever confirmed (vs 72.5% for locality) | 581 visits / 150 addresses | `[DATA]` |

### A.5 The ten questions, answered with evidence

| Question | Answer | Tag |
|---|---|---|
| What is CN trying to solve operationally? | Recover money across many channels where **field is the most expensive, least scalable, most compliance-exposed channel** — and the one whose outcome depends on a piece of data (an address) that no system owns today | `[I]`, anchored on `[S51]`–`[S54]` |
| What is slow / repetitive / error-prone today? | Repeat visits (73.5% of visits), re-discovery of already-known places, manual address interpretation, and evidence that exists only as free text in one agent's app | `[DATA]` + `[I]` |
| What happens when an address is poorly written? | 38.9% of addresses cannot be matched exactly to a locality; 8.4% carry no sub-town evidence at all; 42.7% of the book is unplaceable or coarse-only under a strict rule | `[DATA]` |
| What happens when the geocoder is coarse? | Structurally worse field outcomes: 51.8% not-traceable on `pincode` stratum, 6.4% on `rooftop`; and no signal is emitted saying which is which beyond the vendor's own label | `[DATA]` |
| What happens when a field visit fails? | A 1.3-minute median dwell, a check-in **1,603 m from the truth** (median, on the 53 surveyed failure visits), and **84.9%** of the time sitting *closer to the wrong vendor pin than to the real address* — i.e. failure manufactures false agreement | `[DATA]` |
| What happens when a visit succeeds? | A coordinate **24.0 m** from truth (median, n=38) — 15× better than the pin — plus dwell, media, a remark, and a trail nobody currently reads | `[DATA]` |
| What happens to that knowledge afterwards? | Nothing systematic. It lives as a row in a visit table; it is not a place, it has no confidence, and no future address query consults it | `[DATA]`/`[I]` |
| What happens when the same or similar address appears again? | The duplicate is worked from scratch: median check-in-to-check-in distance between repeat visits is **194.8 m**, and only **9.3%** of multiply-visited addresses have *all* visits within 50 m of each other — i.e. the field does not converge on the same spot by itself | `[DATA]` |
| What information is lost after a visit? | The failure inference, the remark's content, the neighbouring-address relationship, the effort spent, the integrity doubt, and the fact that two accounts share one building | `[DATA]` + §E |
| What would make the workflow cheaper / faster / more systematic? | (a) turning a confirmed visit into a reusable place record; (b) refusing to send effort at places where evidence says effort cannot help; (c) making every visit's capture structured enough to be usable tomorrow without a human preparing a dataset | §G, §F, §R |

---

## B. CURRENT OPERATIONAL WORKFLOW

Reconstructed from the official dataset plus CN's public product description `[S51]`,`[S52]`. Where a stage cannot be
observed in our data, it is marked `[UNKNOWN]` — those marks are the instrumentation list in §M.

```
LENDER DATA ─► ADDRESS RECEIVED ─► ADDRESS UNDERSTOOD ─► LOCATION ESTIMATED ─► FIELD DECISION
     ─► FIELD VISIT ─► OBSERVATION ─► SYNC ─► QUALITY CHECK ─► KNOWLEDGE UPDATE ─► FUTURE RESOLUTION
```

| Stage | Who acts | Artefact produced today | What our data shows | What is lost at this stage |
|---|---|---|---|---|
| 1. Lender data arrives | client ops | `addresses.csv`-shaped row: free text + town + type | 3,117 addresses, 30.2% offices/native, 99.2% created on one weekday — the address does not change often once loaded | provenance of the *text* (KYC vs skip-trace: 3,090 / 27) `[DATA]` |
| 2. Address understood | nobody, or a human | nothing durable; consumption is per-case | 38.9% have no exact locality match; 91.6% carry at least one usable evidence channel | the parse itself, and the fact that a human resolved it once |
| 3. Location estimated | vendor geocoder | one row: x, y, precision | 2,880 pins, 71.2% locality-level, no pin shared by two addresses | which evidence produced the pin; the pin's real error (median 376 m) |
| 4. Field decision | allocator / policy | a visit list; risk-weighted | exposure rises 25.1% → 96.8% across DPD bands; permanent_native addresses are **never** visited (0.0%) | *why* an address was skipped, and any record that skipping was a decision |
| 5. Field visit | field agent (9 in data; 4,000+ in a real book `[S58]`) | check-in, dwell, outcome, remark, photo, GPS trail | median 3.78 visits per visited address; 83% of check-ins between 10:00–13:00 | the notice that preceded it (RBI requires ≥1 day) `[S55]`; the search effort; what was *seen* beyond the outcome |
| 6. Observation | field agent | 7-value outcome + free text | 762 distinct remarks, 100% populated, multilingual | the discriminating facts: which door, which floor, what the neighbour said, whether a shop now occupies the house |
| 7. Sync | app → server | rows appear | no sync metadata exists in the dataset | lag, retries, duplicates, device clock skew — the failure modes with published 60% incident share `[S61]` |
| 8. Quality check | supervisor, ad hoc | nothing systematic | one agent carries **162 of 610 visits with a repeated photo hash (26.6%)** while its GPS is flawless | any durable quality state per visit |
| 9. Knowledge update | — | — | **the step does not exist in the data** | the entire learning loop the PS asks for |
| 10. Future resolution | next case | starts from the same vendor pin | 473 of 665 previously-confirmed addresses were visited again after a mid-window cut, and their post-cut success rate is **56.0%** vs 40.5% for all other post-cut visits | that those addresses were already known to be confirmable |

**The one-line diagnosis of the current workflow:** *stages 1–5 spend money; stage 6 produces information; stages 7–10
throw most of it away.* The PS is, in effect, a request to build stages 7–10.

---

## C. WHERE VALUE / COST / WASTE EXISTS

### C.1 The waste map — what is measurable today

| # | Waste | Measured here | Why it happens | Who feels it |
|---|---|---|---|---|
| W1 | **Repeat visits** | 4,101 of 5,578 visits (73.5%) went to an address already visited; 1,071 addresses visited >1×; 823 visited ≥3× | no durable place record, so each case starts fresh | field ops, finance |
| W2 | **Visits that produce no knowledge** | 577 addresses never confirmed (39.1% of visited), absorbing 1,650 visits (29.6%) | mixture of bad pins, bad addresses, and "person genuinely not there" — currently indistinguishable | field ops, ML |
| W3 | **Coarse-pin penalty** | `pincode` stratum: 51.8% failure, 55.8% confirmation rate, **257 visits spent on 85 never-confirmed addresses** | the pin's granularity is not used to set expectations or to plan a search | field ops |
| W4 | **Effort re-discovery** | 6.2 visits per finally-confirmed address; 2.46 visits per met-someone visit | nothing remembers which addresses are cheap or expensive to confirm | allocation, finance |
| W5 | **Non-convergence** | repeat-visit check-ins differ by a **median 194.8 m**; only **9.3%** of repeat-visited addresses have all visits within 50 m | agents are not told where the previous agent stood, or why | field ops |
| W6 | **Notice served on the wrong door** | 237 addresses sit outside every modelled town and 0% are geocoded; 9.0% of pins are within 100 m | an address that cannot be placed still triggers a legal notice | **compliance/risk** `[S55]` |
| W7 | **Unused evidence** | 762 distinct remarks; 160,406 GPS points; dwell; media — none of it durable knowledge | capture is designed for case closure, not for learning | data/ML, ops |
| W8 | **Unknown-integrity evidence** | 172 visits (3.1%) carry a repeated photo hash; 443 visits (7.9%) under 60 s dwell | quality check is manual and unrecorded | risk, audit |
| W9 | **Travel time inside the window** | median 12.1 min from start to check-in, p99 53.8 min — but the `pincode`-stratum failure visits burned the *longest* median travel (18.6 min) before failing | effort is spent arriving at a place that cannot be found | field ops |
| W10 | **Vendor dependency** | 92.4% of the book depends on a vendor pin; only 28.9% of the book ever gets a field-confirmed coordinate | no owned coordinate exists as an asset | finance, product |
| W11 | **Manual address investigation** | not observable in this dataset `[UNKNOWN]` | — | ops (instrumented in §M) |
| W12 | **Improvement blindness** | there is no measurement of *avoided* work, because skipping a visit is never recorded | the operating loop is open at both ends | everyone |

### C.2 Where the money actually sits

| Cost pool | Evidence of magnitude | Tag |
|---|---|---|
| **Field slots** (travel + dwell + supervision) | Dominant by construction: every visit costs a person-hour plus travel; the digitised-channel alternative is priced an order of magnitude cheaper per resolution in published Indian benchmarks (₹480–850 field-first vs ₹85–120 AI-led per account) | `[VENDOR CLAIM]` `[S56]` — benchmark only, **not** CN's cost |
| **Independent address verification** (the market price of knowing where a place is) | Physical field verification ₹800–1,500 per address, 3–7 day TAT; $2–10 per completed visit internationally | `[VENDOR CLAIM]` `[S59]` — order-of-magnitude anchor |
| **Vendor geocoding spend** | not public, not visible to us `[UNKNOWN]` | — |
| **Compute / storage / model training** | **the small pool**: our entire pipeline — EDA, cleaning, candidates, features, charts, checks — runs in **~24 s on one CPU core, 160 MB peak** | `[DATA]` |
| **Compliance and rework cost of a wrong address** | Framework effective 1 Oct 2026: advance notice naming the agency, contact windows, agent certification, 6-month call retention, and a grievance pause — a wrong-door notice is a reportable event, not a wasted trip | `[V]` `[S55]` |

**Read this correctly:** the money is in **which addresses get worked, and what happens when they are worked**. It is
not in compute, not in storage, and not in model sophistication. Any design decision in this package that spends
engineering effort on compute while leaving W1–W6 untouched is spending on the wrong pool.

### C.3 Value drivers present in the data — and the ones that are not

| Value driver | Measurable now? | Denominator available today |
|---|---|---|
| Fewer repeat visits | **Partially** — the repeat volume is measurable (4,101 visits); the *avoidance* requires a counterfactual we do not have | §L |
| Higher first-visit success | **Yes** — first-visit met 37.8%, not-traceable 33.0%, and a memory-eligible cohort already shows 56.0% vs 40.5% | §L |
| Fewer wrong-door attempts | **Proxy only** — not-traceable share, pin-distance of failures | §M |
| Fewer vendor lookups | **Yes** — 28.9% of the book could already carry a field-confirmed coordinate; 47.4% has some visit evidence | §L |
| Faster field preparation | **No** — no pre-visit session data `[UNKNOWN]` | §M |
| Less manual investigation | **No** `[UNKNOWN]` | §M |
| Better reuse of verified locations | **Yes** — the 24.0 m recovery result and the 90 m repeat-check-in spread | §G/§L |
| Faster resolution for recurring addresses | **Proxy** — pre-cut-confirmed addresses succeed more often | §L |
| Institutional memory (person → company) | **Structurally yes** — 9 agents hold the knowledge today; nothing in the data survives an agent leaving | §N |
| Auditability | **Partly** — evidence exists (trail, media, dwell) but no quality state is attached | §R |
| Offline effectiveness | **No** `[UNKNOWN]` | §H |

---

## D. WHAT FIELD VISITS ACTUALLY CONTRIBUTE

### D.1 The evidence taxonomy

A single visit row carries seven distinct kinds of information. They have **different reliability, different lifetimes,
and different permissions**.

| # | Evidence | What it is evidence *of* | What it may legitimately do | What it must never do |
|---|---|---|---|---|
| E1 | Check-in coordinate | *where the agent stood at the moment of contact* | anchor a place record when contact happened (turn out, or person met) | be treated as the doorstep; be averaged with the vendor pin |
| E2 | Outcome (7 values) | **two different things** — place evidence (`met_*`, `cash`, `locked`) and person evidence (`no_such_person`, `neighbour_says_shifted`) | weight belief; drive re-verification; classify refusal | become one ordinal label; place a coordinate on failure |
| E3 | Dwell | *how long the agent stayed* — a proxy for whether a search actually happened | weight: <1 min → 0% met-someone, 10–25 min → 100% | be used as truth: this separation is a generator artefact `[DATA]` |
| E4 | Photo / media | *something was photographed* — and by arrangement, a duplicate rate | integrity weighting, plus a durable visual record | be read as proof of the person or the door |
| E5 | Free-text remark | *what the agent wanted a colleague to know* | audit outcomes, mine recurring obstruction patterns | be a feature input at prediction time (T3) |
| E6 | GPS trail (26 points median) | *the path taken* — process evidence | place-side: where the agent converged; process-side: accuracy, coverage | be a truth test: **trail shape does not separate outcomes** `[DATA]` |
| E7 | Effort context (travel time, slot) | *what the attempt cost* | allocation and triage | be used to justify a coordinate (sunk-cost reasoning) |

### D.2 The four hard truths about visit evidence in this dataset

| # | Truth | Measurement |
|---|---|---|
| D-1 | **A failed visit manufactures a false location.** | On the surveyed subset, `address_not_traceable` check-ins sit **1,603.2 m** from truth (median) with 1.3-minute dwell, and are closer to the *vendor pin* than to the truth **84.9%** of the time `[DATA]` |
| D-2 | **A successful visit is genuinely accurate.** | Met-someone check-ins: **29.3 m** median from truth; 24.0 m if we anchor on the *first* met-someone visit per address (n=38 surveyed) — 87% within 100 m `[DATA]` |
| D-3 | **A trail is not a truth test.** | Check-in→nearest own-trail-point: median **7.6 m**, max **90.8 m**, **zero** visits >100 m. Every check-in is on the agent's own walked path `[DATA]` |
| D-4 | **A failed visit still carries real information.** | "Not traceable at the pin's location after 1.3 minutes" is a *search-failure* signal that should raise suspicion about the pin — and today it is discarded `[DATA]`/`[I]` |

### D.3 What a visit does *not* tell us

| Gap | Consequence | Currently unobservable |
|---|---|---|
| Which door / floor / unit | a 24 m error is the right building or the wrong flat | yes |
| Whether the named person still lives there | the location can be right and the person gone | yes — `no_such_person` (3.7%) hints but does not establish |
| Whether the address has *moved* (new construction, renumbering) | the place is stale while the evidence looks fresh | yes |
| Whether a skipped address would have succeeded | the counterfactual that would price triage | yes — never recorded |
| Whether the notice reached the right household | the compliance event the RBI framework cares about | yes |
| What the agent actually saw (shop, locked house, demolished) | richer place state | only via free text |

**Design consequence.** The product of a visit is not "a coordinate" but a **place observation with a scope**: *at this
coordinate, at this time, with this stop-effort, contact was or was not established.* The scope is what makes the
observation reusable; the coordinate alone is not.

---

## E. WHAT KNOWLEDGE IS CURRENTLY LOST

Ten losses, each with what it costs, what a minimal capture would look like, and whether it is measurable today.

| # | Lost knowledge | What it costs operationally | Minimal capture that would keep it | Measurable today? |
|---|---|---|---|---|
| L1 | **Search-failure as a signal about the pin** — 1,400 `address_not_traceable` visits | the same bad pin is sent again; 51.8% of `pincode`-stratum visits fail and nobody is told | a `search_failed_at` event with the coordinate and the dwell | **Yes** — 1,400 rows already exist |
| L2 | **Agent-local knowledge** — 762 distinct remarks, 100% populated | "lock laga hai", "mane lock agide", "address nahi mila" are never aggregated into a place state | a controlled vocabulary of obstruction reasons, plus optional free text | **Yes** — remarks are there; only the vocabulary is missing |
| L3 | **The neighbouring-place relationship** — a confirmed address 60 m away | every address is resolved as if it were the first in the world | a spatial index over confirmed places, consulted before any vendor lookup | **Yes** — 900 confirmed places exist to link against |
| L4 | **Two accounts at one building** — 5 duplicate-text groups / 10 rows at minimum | the same building is verified twice for two borrowers, and never linked | a place identity keyed on evidence, not on `address_id` | **Yes** |
| L5 | **Negative space** — "not at this location" | today it is a discarded row; tomorrow it should be a *suspicion weight* on the pin, never a location | separation of place-evidence from search-failure evidence (already designed) | **Yes** |
| L6 | **Time** — the age of a confirmation | an address confirmed 8 months ago is treated exactly like one confirmed yesterday | confirmation recency on the place record, plus re-verification triggers | **Partly** — the dataset spans only 89 days `[UNKNOWN]` for real decay |
| L7 | **Effort cost per place** | nothing learns that some addresses cost 6 visits and others cost 1 | attempts-to-confirm kept per place; slot cost attached upstream | **Yes** for attempts; `[UNKNOWN]` for money |
| L8 | **Integrity doubt** | 172 visits with repeated media and 443 sub-minute visits still count as evidence | a per-visit integrity state, versioned and visible | **Yes** |
| L9 | **The pre-visit plan** | what the agent was told, and what they were looking for, is not recorded — so the next agent gets the same thin brief | pack version + plan id on each visit | **No** `[UNKNOWN]` |
| L10 | **Cross-agency / cross-town knowledge** | large books run through many agencies `[S58]`; a confirmation obtained by agency A does not exist for agency B | a company-owned place record, agency-neutral | **Structurally yes** |

**Why this matters more than accuracy.** Improving median error from 376 m to 200 m changes how close the pin is.
Keeping L1–L10 changes *whether the work is done twice*. The second is where the repeat-visit volume (73.5%) lives.

---

## F. HOW DATA SHOULD FLOW: OPERATION → KNOWLEDGE → TRAINING

### F.1 The lifecycle, with an eligibility ladder rather than a pipeline

```
RAW OPERATIONAL EVENT  (visit, notice, correction, address change)
   ↓ gate 1  VALIDITY        — is this record mechanically sound?        [deterministic]
CLEANED OBSERVATION
   ↓ gate 2  TRUST           — does this observation claim to prove a location? [rule-based]
TRUSTED OBSERVATION  (place-positive, adequate dwell, integrity pass, coordinate present)
   ↓ gate 3  INDEPENDENCE    — has a *different* source said the same thing?  [episode rule]
ADJUDICATED OBSERVATION (≥2 independent confirmations, or 1 with high dwell + no contradiction)
   ↓ gate 4  DERIVATION      — what may be *inferred* from it? (multi-source fusion, never a raw copy)
DERIVED EVIDENCE  → ADDRESS / PLACE KNOWLEDGE  (queryable, auditable, agency-neutral)
   ↓ gate 5  ELIGIBILITY     — may this be learned from? (delayed labels resolved, group-safe, no held-out entity)
TRAINING-ELIGIBLE EVIDENCE
   ↓ gate 6  GATING          — has enough *new* eligible evidence accumulated? (pre-registered thresholds)
MODEL UPDATE → VALIDATION → PROMOTION → OFFLINE PACK REFRESH → FUTURE RESOLUTION
```

**Six rules that make the ladder safe**

| Rule | Why | Evidence from our own data |
|---|---|---|
| G1 — **Belief is never a label** | a model trained on its own output drifts into confidence about nothing | — (design rule) |
| G2 — **A negative outcome is never a location** | failures sit 1,603 m from truth and point at the pin | `[DATA]` |
| G3 — **One observation is a hypothesis; two independent ones are knowledge** | repeat check-ins differ by 194.8 m median, so a single visit is not a place | `[DATA]` |
| G4 — **Independence is about source, not repetition** | one agent visiting 3× is not 3 confirmations; 9 agents exist today, 4,000+ across agencies in real books | `[DATA]` + `[S58]` |
| G5 — **A correction is a new row, never an edit** | offline devices will deliver out-of-order, duplicated and replayed events | `[S61]`,`[S62]` |
| G6 — **Nothing becomes training-eligible until its label is final** | the outcome of *this* visit is not the label for placing *this* visit | house rule; feature-store analogue `[S64]` |

### F.2 Eligibility, in numbers, on today's data

| Gate | Rule (conservative) | Survives | Share |
|---|---|---|---|
| All visits | — | 5,578 | 100% |
| Validity | coordinate present, dwell > 0, trail present | 5,578 | 100% |
| Trust — place-positive | outcome ∈ {met_borrower, met_family, cash_collected} | **2,268** | 40.6% |
| Trust — adequate effort | + dwell ≥ 180 s | **2,224** | **39.9%** |
| Integrity | remove visits carrying globally-repeated media (172) | ≈ 2,060 | ≈ 37% |
| Independence — address level | addresses with ≥2 *independent* met-someone confirmations | **439 addresses** | 14.1% of the book |
| Training-eligible cohort (for the cold lens) | group-safe (account-level), label final, not in the evaluation block | **all of the above, minus held-out entities** | ~— |

Two numbers from this table deserve to be on a wall:

* **2,224 eligible visits (39.9%)** — that is the entire supervised surface a learned model could ever see from this
  dataset, and it is *why* the architecture must be honest about small-data behaviour.
* **439 addresses with ≥2 independent confirmations** — note this is far smaller than the 957 addresses that were
  merely visited by more than one agent; the earlier "957" figure counted *any* visit, which would promote places on
  the strength of someone walking past them `[DATA]`.

### F.3 The learning contract — eleven events, each with a *consumer*

The test for adding an event is not "is it modern", it is: **what breaks downstream if this event is missing?**

| Event | Business meaning | Producer | Consumer that breaks without it | Minimum payload |
|---|---|---|---|---|
| `address.created` | a new address enters the book | client ingestion | retrieval index (no arity), allocation | id, text, town, type, source, provenance, `event_time` |
| `address.updated` | the lender changed the address text | client ingestion | memory (stale text), audit (which text was used when) | id, previous text hash, new text, source, `event_time` |
| `resolution.created` | a location was published | geocoder | field app, compliance record, downstream accuracy | query id, candidate set, chosen tier, radius, model/pack version, `as_of` |
| `visit.planned` | an address was selected for a visit | allocator | triage learning, notice compliance (**RBI requires notice before the visit**) | plan id, address id, notice sent at, pack version `[S55]` |
| `visit.started` | an agent began travelling | field app (offline) | travel/dwell analytics, effort cost | visit id (client UUID), agent id, start ts, device clock + offset |
| `visit.completed` | the observation exists | field app (offline) | the entire knowledge loop | outcome, dwell, coordinate, accuracy, media hash, remark, plan id |
| `evidence.validated` | an observation passed/failed gates | server | trust scoring, training buffer, review queue | visit id, gate results, reasons, validator version |
| `belief.updated` | a place's state changed | belief engine | field app's next brief, uncertainty output | place id, previous/new state, supporting evidence ids, `as_of` |
| `address.confirmed` | the place is now usable as knowledge | belief engine | memory-backed resolution, vendor independence | place id, coordinate, radius, confirmations, eligible-from date |
| `address.contested` | two trusted sources disagree | belief engine | review queue, abstention behaviour | place id, the two positions, evidence ids, magnitude |
| `address.stale` | a confirmation has aged or a trigger fired | policy job | re-visit planning, radius widening | place id, reason, last confirmation, policy version |
| `training_eligible` | this evidence may be learned from | eligibility service | retraining, audit of what each model saw | evidence ids, label definition, group key, gate versions |
| `model_retrained` / `model_promoted` | a new version exists / is live | slow loop | offline packs, rollback, explanation of a changed answer | version, data window, metrics, decision, approver |

**The question this contract must answer — and does:** *"If a company starts using this system tomorrow, will the data
produced by daily operations automatically become useful for the next version of the system?"* Under this contract,
yes — because (a) the capture is structured at the moment of the visit, (b) eligibility is computed by machine against
published gates rather than by a human preparing a dataset, (c) labels are attached to *places and events*, not to a
one-off training file, and (d) `training_eligible` records the exact rule version that admitted each row, so a future
auditor can reconstruct why the model learned what it learned.

### F.4 Schema discipline (the three clocks)

| Clock | Meaning | Where it lives | Why it cannot be collapsed |
|---|---|---|---|
| `event_time` | when it happened in the field | on every event | a device offline for two days must still produce correctly ordered history `[S61]` |
| `ingest_time` | when the server learned it | on every event | late arrivals and corrections are normal; "as now known" ≠ "as known then" `[S64]` |
| `valid_from` | when a belief was true *for serving purposes* | on belief states only | beliefs have a lifetime independent of their supporting events |

Training rows are built **known-then** by default: for a row with decision time *t*, only evidence with
`ingest_time < t` may be read. This is the single most common production-ML failure named in the literature `[S64]`, and
in a field system it is the difference between a model that learned geography and one that learned the future.

---

## G. HOW REPEATED WORK COULD BE REDUCED

### G.1 The measured case

| Measure | Value | Reading |
|---|---|---|
| Repeat visits (to an already-visited address) | **4,101 of 5,578 = 73.5%** | the field is mostly re-walking known ground `[DATA]` |
| Addresses visited more than once / ≥3 times | 1,071 / 823 | repetition is the norm, not the exception `[DATA]` |
| Addresses never confirmed despite ≥3 visits | **212** | some places resist effort; today nothing learns that `[DATA]` |
| Visits per finally-confirmed address | **6.2** | the cost of knowledge is paid several times over `[DATA]` |
| Repeat-visit check-in spread | median **194.8 m**; only **9.3%** of repeat-visited places have all visits within 50 m | the field does **not** self-converge — memory must be built, not assumed `[DATA]` |

### G.2 Does reuse actually work? A backtest we can run today

This is the strongest official-data test of the PS's premise, and it is deliberately simple:

| Test | Design | Result |
|---|---|---|
| **Memory accuracy** | For the 38 surveyed addresses that ever had a met-someone visit, use that visit's check-in as the estimate of the place, and compare against the surveyed truth | memory median **24.0 m**, 87% within 100 m, 68% within 50 m vs vendor pin median **380.3 m**, 5% within 100 m; memory better in **89%** of cases `[DATA]` |
| **Forward reuse** | Cut the visit history at 2026-05-15; find addresses with a met-someone confirmation before the cut (665); then look at every visit after the cut | 473 of those addresses were visited again (**1,383 post-cut visits**); those visits land a median **90.0 m** from the pre-cut confirmed check-in (p75 251.7 m; 36.3% ≤50 m, 51.9% ≤100 m), and **56.0%** of them met someone vs **40.5%** of all other post-cut visits `[DATA]` |
| **Independence** | Same-agent replays vs different-agent replays | same-agent replay lands nearer the previous confirmation (median 82.0 m) than a different agent (98.0 m) — real but modest `[DATA]` |

Three conclusions, each with an operational consequence:

1. **A confirmed visit is a better location than anything the vendor produced** (24 m vs 380 m on the same 38
   addresses). → *The company already owns a better answer than it is using; it simply does not store it as one.*
2. **Reuse is not free**: the second visit's check-in differs from the first by ~90 m median. → *A memory-backed
   answer must ship with a radius that covers agent standing variation (≈250 m at p75), not just coordinate error.*
3. **Already-confirmed addresses are materially more productive** (56.0% vs 40.5% met-someone). → *Confirmability is
   itself a property of the place that can be learned and allocated against.*

### G.3 What "one good visit → reusable knowledge" should mean

| State | Definition (conservative) | Today's volume | What it unlocks |
|---|---|---|---|
| **Unvisited** | no visit | 1,640 addresses (52.6%) | nothing yet; the honest unknown |
| **Attempted** | ≥1 visit, no confirmation | 577 addresses | a **negative prior** on the pin: raise suspicion, widen the search, do not trust the vendor pin here |
| **Confirmed** | ≥1 met-someone visit, adequate dwell, integrity pass | 900 addresses (28.9% of the book) | a usable coordinate + radius for the *next* case at this place |
| **Corroborated** | ≥2 **independent** met-someone confirmations | **439 addresses** | promotion to durable knowledge; usable without re-verification until a trigger fires |
| **Contested** | two trusted sources disagree beyond tolerance | 0 observed in 89 days; the mechanism must still exist `[I]` | abstain, review, do not silently average |
| **Stale** | a trigger fired (age, failure run, lender address change) | not measurable in 89 days `[UNKNOWN]` | re-verification, radius widening, or explicit downgrade |

**Re-verification triggers — when a revisit is genuinely necessary** (each is a *rule*, not a decay curve):

| Trigger | Fires when | Why a revisit is justified |
|---|---|---|
| Contradiction | a trusted visit lands outside the published radius | knowledge is wrong, not merely old |
| Repeated search failure | ≥2 attempts with dwell < 60 s and no contact | the pin may be wrong; do not spend a third slot blind |
| Address text change | `address.updated` alters the text materially (house number, locality) | the *place* may have changed, not just the record |
| Age | beyond a policy horizon with no confirmation | the only lever available until real address-change data exists |
| New construction / landmark movement | gazetteer or media shows change | the world moved |
| Second account at the same building | a new case maps to a corroborated place | reuse without a visit (no confirmation needed) |
| **Never** | for a corroborated place with none of the above | the whole point of the loop |

### G.4 The honest ceiling

We cannot claim avoided visits from this dataset: skipping is never recorded, so there is no counterfactual `[UNKNOWN]`.
What we *can* state is the **size of the addressable waste**: 4,101 repeat visits, 1,650 visits on never-confirmed
addresses, and 473 already-confirmed addresses that were visited again inside the window. Any future claim of avoided
visits must be measured by logging the decision to *not* visit — which is §M's first instrumentation item.

---

## H. HOW OFFLINE OPERATION CHANGES THE PRODUCT

Offline is not "cache some coordinates". It is the reason the field app can be the *sensor* of this system — and the
reason the server must assume that everything it receives is a late, possibly duplicated, possibly re-ordered echo of
what really happened.

### H.1 The four moments

| Moment | What the agent needs | What the app must hold | What breaks if designed badly |
|---|---|---|---|
| **Before leaving** | the plan: which address, *how uncertain*, what to look for, who was there last time | a **pack**: place records + radii + landmark chain + last-attempt history + pack version | an agent with a bare pin repeats another agent's wasted hour |
| **During the visit** | capture with zero connectivity, fast, one-handed | local SQLite store, structured capture (outcome + 2–3 taps + photo + auto GPS + optional remark) | an 8-field form in the sun produces garbage or no data |
| **After the visit** | confidence the work is recorded | queued submission with client-generated idempotency key and a local "synced / pending" state | silent loss; users re-enter or abandon |
| **On reconnect** | nothing — it should just work | delta sync, resumable, idempotent, server-authoritative versioning | duplicates, lost observations, "I thought it synced" `[S61]` |

### H.2 The failure modes, and the mechanism for each

| Failure mode | Mechanism (published practice, adapted) | Concretely in PS3 |
|---|---|---|
| **Duplicate submission** (retry after a lost acknowledgement) | client UUID → server id map; every write idempotent | a visit has a client-generated `visit_id`; the server returns the existing record on retry. Reported field reality: 47 observations became 141; duplicates + clock skew were **60% of a team's data issues** `[S61]` |
| **Conflicting timestamps** | never trust the device clock; server-assigned monotonic versions; device time stored as user-facing metadata only | dwell and travel are recomputed server-side from ingest-ordered events |
| **Out-of-order offline revisions** | hold-then-mark, not last-write-wins | an offline correction that arrives before its original is **held up to 5 days**, then force-processed and the place marked `CONTESTED` — the ODK Central policy, adopted deliberately `[S62]` |
| **Evidence vs status conflict** | different rules per data kind: status = server decides; *findings and evidence = keep both* | two agents' visit observations are never merged; a place's **status** is decided server-side `[S63]` |
| **Stale packs** | pack version + TTL on every record; the app refuses to present an expired certainty as current | an agent who has been offline for 10 days sees "last confirmed 9 days ago; search radius widened" |
| **Partial sync** | delta sync with resume checkpoints; per-visit atomicity | a visit uploads whole or not at all; a photo may follow separately and the visit is marked `media_pending` |
| **Device failure / loss** | local queue durable across restarts; the app treats unsynced work as precious and *says so prominently* | "3 observations not yet synced — data will be lost if this device is wiped" |
| **Corrupted evidence** | content hashes on media; plausibility checks server-side | a truncated photo fails its hash and is flagged, not silently attached |
| **Model / pack version mismatch** | every event carries the pack version that produced the plan; the server never mixes versions silently | a visit captured against pack v7 is evaluated as a *v7* observation, even if v9 is live |
| **Repeated visits to the same place** | idempotent at the *place* level too: the second observation appends, it does not overwrite | corroboration counting depends on this `[S63]` |

### H.3 What makes the app *more effective*, not merely functional

The offline design changes what a visit can *be*:

1. **The brief replaces the pin.** A confirmed place is shown as *"last confirmed 2026-06-02 by FA007: this gate, 90 %
   within 100 m"* plus the landmark chain. That is the PS's own output requirement (lat/lon **+ radius + landmark
   directions**), and offline it is the difference between a search and a guess.
2. **The questions become discriminating.** Instead of "did you meet them?", the capture asks what actually resolves
   *this* address: is the number visible? is the shop still in front? did the neighbour name them? Each answer is a
   candidate feature; today all of it collapses into one of seven labels.
3. **The app collects for the next agent.** Because the observation is structured at capture time, the very next
   offline pack is better — no human prepares a dataset, which is precisely the PS's "continuously learning" clause.
4. **Refusal becomes cheap.** "I could not find it" with a coordinate and 90 seconds of dwell is *useful* evidence when
   the system treats it as suspicion of the pin. Today it is just a failed visit.

### H.4 Product consequences

| Consequence | Implication |
|---|---|
| Packs are the unit of update | model/knowledge change must be pack-deliverable, not a live-API-only capability |
| The server is the arbiter | belief state, contradiction and promotion are server-side; the device is an observer |
| Capture must be *fast* | every added required field costs data quality; the design budget is ~20 seconds of taps |
| Storage is cheap, conflicts are not | append-only revisions accepted even at 11 rows for one observation `[S61]` |
| Support surface grows | offline sync failures become an operational support category (observability from day one) |

---

## I. HOW THE SYSTEM COULD BECOME DYNAMIC

### I.1 Two clocks (and the honest reason they are two)

| Clock | What changes | Latency | Mechanism | Reversible? |
|---|---|---|---|---|
| **Immediate (per event)** | place belief, confidence, tier, contest/stale status, attempt count, suspicion on the pin | seconds after sync | deterministic rules + weights, versioned | yes, by policy version |
| **Controlled (per cycle)** | parser vocabulary additions, candidate-set composition, ranker weights, radius calibration, tie-breaks | weeks, gated | retraining + validation + promotion | yes, by rollback |

**There is no third clock.** "Retrain after every visit" is not a design; on this dataset it would be fitting
339 new rows a day against a generator's quirks.

### I.2 What the immediate clock is allowed to do with one new visit

| Condition on the incoming observation | Immediate action | Why safe |
|---|---|---|
| place-positive, dwell ≥180 s, integrity pass, no contradiction | append evidence; if a second **independent** confirmation exists → promote to `CONFIRMED` with a published radius | corroboration rule `[DATA]`: 439 addresses already qualify |
| place-positive but first confirmation | hold at `PROVISIONAL`; radius stays wide; feeds the next pack as "probable" | one observation is a hypothesis (repeat-check-in spread 194.8 m) `[DATA]` |
| `address_not_traceable` with short dwell | raise suspicion on the *pin*; increment attempt count; never touch coordinates | failures sit 1,603 m from truth `[DATA]` |
| `locked_premises`, `neighbour_says_shifted`, `no_such_person` | person-side evidence only: status/re-verification, no coordinate movement | two-dimension vocabulary |
| low integrity (repeated media, sub-minute dwell, accuracy outlier) | flag, quarantine from coordinate learning, keep the row | FA009: 162/610 visits with repeated media `[DATA]` |
| contradicts current belief beyond the radius | mark `CONTESTED`, freeze promotion, queue review | conflict-as-evidence, not as error `[S63]` |

### I.3 What the controlled clock is allowed to change — and when

| Component | Change trigger (pre-registered) | Gate | Rollback |
|---|---|---|---|
| Evidence weights / rule table | measurable error reduction on the surveyed block, or a documented operational failure | review + shadow run | policy version pinned per query |
| Ranker | ≥X% growth in **eligible** evidence (e.g. eligible rows +25%) *and* an interval-clean improvement over the rule baseline | grouped, account-safe validation | keep-the-previous champion `[S64]` |
| Radius calibration | refreshed only when the eligible cohort grows; strata with n<15 stay on parent fallback | measured coverage on held-out rows | table is versioned and reversible |
| Parser vocabulary | new gazetteer/alias confirmed by ≥2 independent observations | deterministic test suite | vocabulary version pinned per query |
| Drift detection | **not “detect drift continuously”** — the dataset shows no drift in 89 days; the mechanism is monitoring + pre-registered triggers, exercised by replay simulation | — | — |

### I.4 The gates that make dynamism safe

| Gate | Question | Mechanical test |
|---|---|---|
| Label finality | is the outcome we are learning from final? | the visit's own outcome cannot be a feature of placing that visit; later corrections create new rows |
| Independence | is this corroboration or repetition? | source identity (agent/agency) must differ, and the episode must be different |
| Group safety | are we training on an entity we will evaluate on? | group key = `(account_id, normalised_text, town)`; the 3 duplicate-text groups spanning splits stay grouped `[DATA]` |
| Distribution | did the *inputs* shift, not just the volume? | pack-version and cohort drift checks before promotion |
| Coverage | did the change help the segments we care about? | stratum-level reporting with n; no claim for n<15 |
| Cost | does it stay CPU-cheap? | retrain budget: minutes, not hours `[DATA]`: the whole pipeline is ~24 s |

**End state to aim at:** the system gets *easier* to operate over time — more places are known, fewer cases need a
human, and each new month of operations produces its own training material. A system that needs progressively more
human maintenance is a failure of this design, not a phase of it.

---

## J. HOW THE COMPANY COULD BENEFIT ECONOMICALLY

**No ROI number appears anywhere in this section.** What follows is the structure that a profitability story must
respect, with honest labels on what we can and cannot measure.

### J.1 The value table — VALUE DRIVER → MECHANISM → DATA NEEDED → EXPECTED DIRECTION → EXPERIMENT

| # | Value driver | Mechanism (how money is actually affected) | Data needed to measure it | Expected direction | Experiment required |
|---|---|---|---|---|---|
| 1 | Fewer repeat visits to confirmed places | a corroborated place answers the next query without a visit | decision-to-skip log + visit plans | fewer slots for the same confirmed coverage | log skipped decisions; compare slot spend per confirmed case, before/after |
| 2 | Higher first-visit success | the brief carries the last confirmation + radius + landmark chain | pre-visit pack contents + first-visit outcome | first-visit met-someone rises from the 37.8% baseline | A/B on pack content, same towns, matched risk bands |
| 3 | Fewer wrong-door notices | the notice is only sent when a place is confirmable, or the notice goes to a *range* | notice record + place tier at notice time | fewer notices served where a place is `UNPLACEABLE` | measure notice-to-tier mix before/after; pair with disclosure incidents |
| 4 | Less wasted effort on unpinnable addresses | `pincode`-stratum/contested places route to a wider search or to another channel instead of a blind slot | evidence class on the plan | fewer visits ending in 90-second not-traceable | compare success on triaged vs untriaged pincode-stratum cohorts |
| 5 | Reduced vendor lookup dependency | confirmed places answer future queries locally | resolved-from-memory rate | memory share rises with coverage (28.9% of the book is confirmed today) | shadow resolution: what would memory have answered, per query |
| 6 | Faster case resolution for recurring addresses | the second employee at a known building starts from a confirmed place | time-to-first-contact per case | shorter first-contact time for memory-hit cases | cohort comparison by memory hit/miss |
| 7 | Lower manual address investigation | mechanical resolution + refusal state replaces eyeballing | analyst minutes per case (not logged today) | falls | instrument the manual queue for 4 weeks |
| 8 | Higher field productivity (slots per day) | less dead travel to unfindable places; better beat order using known coordinates | visits/day, travel per visit | up, *without* raising failure rate | measure travel time on triaged vs untriaged cohorts |
| 9 | Reusable geographic intelligence across portfolios/towns | one place record serves every lender/agency touching that building | places shared across portfolios | more reuse per confirmation | count second-use events per confirmed place |
| 10 | Lower onboarding effort for new towns/teams | vocabulary + aliases + landmark chains carry over, not the person | time-to-first-confirmation per new town | shorter | timed onboarding before/after a structured pack |
| 11 | Better data quality with less rework | every observation is validated on entry, with reasons | validation pass rate, correction rate | corrections fall, eligible share rises | track eligible-share over months (39.9% today) |
| 12 | Better auditability / lower compliance risk | visit, notice, evidence and confidence are one queryable record | audit queries answered without manual reconstruction | fewer unanswerable inspections | dry-run an RBI-style audit question today |
| 13 | Reduced re-verification cost for known places | triggers replace calendar-based re-checks | reverify events per place | fewer unnecessary re-checks | count triggers fired vs re-checks performed |
| 14 | Better scalability across the book | marginal cost of the 3,118th address is one candidate set, not a new workflow | cost per 1,000 resolutions | flat | replay at 10× address volume on synthetic scale-up |
| 15 | Institutional memory (person → company) | the 9 agents' local knowledge becomes structured place state | share of confirmations held in the company store | 100% by construction | audit: what is known only in an agent's head today |

**Guardrail pairing (mandatory):** every efficiency driver above must be reported next to a quality guardrail —
`repeat-visit reduction` next to `not-traceable rate`; `memory-backed answers` next to `memory false-positive rate`;
`fewer visits` next to `confirmed-coverage`. Without pairing, "fewer visits" can be achieved by simply giving up.

### J.2 The five cost pools, and which we can see

| Pool | Visible to us? | What we can say honestly |
|---|---|---|
| Field slots (people, travel, supervision) | structure only | the largest pool; the repeat-visit and never-confirmed volumes (73.5%, 29.6%) are the addressable waste `[DATA]` |
| Vendor geocoding | no `[UNKNOWN]` | 92.4% of the book depends on it; 28.9% could be answered from field-confirmed knowledge `[DATA]` |
| Manual investigation | no `[UNKNOWN]` | §M instrument item #1 |
| Compliance / rework | qualitatively | wrong-door notice is the highest-severity failure, per RBI framework `[S55]` |
| Compute / storage / training | yes | negligible: **~24 s, 160 MB, one CPU** for the entire current pipeline `[DATA]` — so any "cost" argument for a simpler model is irrelevant here; simplicity must be argued on *correctness and operability* grounds instead |

### J.3 The commercially interesting asymmetry

Published Indian market pricing puts a *digitally* resolved account an order of magnitude below a field-first one
(₹85–120 vs ₹480–850 per resolution) `[VENDOR CLAIM]` `[S56]`. Two conclusions follow, and only one of them is ours:

1. **[VENDOR CLAIM]** Field effort is the expensive channel — which is why *allocating* it well is worth more than
   *increasing* it. This is the same logic as the field-service benchmark spread: avoidable dispatches run 3 % for top
   performers and 24 % for the bottom quintile `[S61a]`.
2. **[I]** For CN, the defensible commercial claim is not "we cut field cost" (the company already publishes efficiency
   numbers `[S51]`). It is **"we can prove where every address is, how sure we are, and what happened at the door"** —
   a claim that compounds across portfolios, survives agency turnover, and answers an RBI inspection without manual
   reconstruction.

---

## K. WHAT SHOULD BE MEASURED

### K.1 The metric contract

Every metric below states its definition, its denominator, its owner and — critically — its **guardrail pair**.

| # | Metric | Definition | Measurable today | Owner | Guardrail pair |
|---|---|---|---|---|---|
| M1 | Median error / p75 / p90 | distance to surveyed truth, per stratum, with n | **Yes** (n=100; strata with n≥15 only) | data/ML | coverage (unanswered) |
| M2 | Hit-rate curve | % within 50/100/250/500/1,000 m | **Yes** | data/ML | sample size disclosed every time |
| M3 | Coverage / refusal rate | % of addresses answered at each tier; % `UNPLACEABLE` | **Yes** (42.7% coarse-only/unplaceable today) | product | tier mix |
| M4 | **Repeat-visit rate** | visits to an address already visited ÷ all visits | **Yes — 73.5%** | field ops | not-traceable rate |
| M5 | First-visit success | % of first visits ending in a met-someone outcome | **Yes — 37.8%** | field ops | end-state confirmation (43.6%) |
| M6 | Never-confirmed consumption | visits spent on addresses that never confirm | **Yes — 1,650 visits, 29.6%** | field ops | confirmed coverage |
| M7 | Visits per confirmed place | total visits ÷ places confirmed | **Yes — 6.2** | finance/ops | confirmation quality |
| M8 | Resolved from memory | share of queries answered by a corroborated place, no vendor call | **No** `[UNKNOWN]` — needs logging | product | memory false-positive rate |
| M9 | Time to knowledge | field event → usable place record | **No** `[UNKNOWN]` — sync lag not in data | data/ML | — |
| M10 | Evidence ingestion completeness | % of visits with outcome, coordinate, trail, media, remark | **Yes — ~100% for the core fields** | engineering | — |
| M11 | **Training-eligible share** | eligible evidence ÷ all evidence, by gate version | **Yes — 39.9% under today's conservative rule** | data/ML | eligibility audit |
| M12 | Corroborated-place count | places with ≥2 independent confirmations | **Yes — 439** | knowledge owner | contradiction count |
| M13 | Stale-memory rate | places past the age policy without re-verification | **No** `[UNKNOWN]` — needs time and a policy | knowledge owner | re-verification backlog |
| M14 | Review / adjudication rate | evidence routed to a human ÷ all evidence | **Partly** (integrity-flagged share) | ops | review turnaround |
| M15 | Notice-to-tier mix | notices sent per place tier | **No** — notice events not in data | compliance | disclosure incidents |
| M16 | Unresolved address rate | % of the book with no coordinate and no refusal state | **Partly** (237 OUT today) | ops | refusal correctness |

### K.2 The five numbers to put on a wall

1. **24.0 m vs 380.3 m** — what a confirmed visit is worth against what the vendor supplies (n=38) `[DATA]`.
2. **73.5%** — the share of field visits that are repeats `[DATA]`.
3. **39.9%** — the share of visits that a conservative rule would accept as learning material `[DATA]`.
4. **56.0% vs 40.5%** — met-someone rate on already-confirmed vs other addresses (a triage signal hiding in plain
   sight) `[DATA]`.
5. **42.7%** — the share of the book that is coarse-only or unplaceable today, i.e. where the honest answer is "we
   don't know" `[DATA]`.

### K.3 What must **not** be measured or published

| Temptation | Why it is refused |
|---|---|
| A single accuracy percentage with no n and no split | the truth set is 100 rows, 66 of whose accounts are inside the official *train* split `[DATA]` |
| Any radius for `pincode` (n=10) or `rooftop` (n=1) strata | statistically meaningless |
| "Visits saved" claims without a skip log | no counterfactual exists `[UNKNOWN]` |
| Spoof-detection rates | there is no spoofing in this data `[DATA]` |
| Uplift percentages borrowed from vendor pages (`[S57]`, `[S58]`) | they are claims about other books, on other definitions |

---

## L. WHAT IS MEASURABLE FROM THE OFFICIAL DATA TODAY

Everything in this table is computed from `data/official_ps3/` alone and is reproducible from this package. Definitions
are given so the numbers can be re-derived rather than believed.

### L.1 The operational denominators (new in this re-think)

| # | Quantity | Definition | Value |
|---|---|---|---|
| L-1 | Repeat-visit share | visits − distinct visited addresses ÷ visits | **4,101 / 5,578 = 73.5%** |
| L-2 | Addresses visited >1× / ≥3× | per-address visit counts | 1,071 (72.5% of visited) / 823 |
| L-3 | Never-confirmed addresses | visited, no met-someone visit ever | **577 = 39.1% of visited** |
| L-4 | Visits consumed by never-confirmed addresses | visits on those addresses | **1,650 = 29.6% of visits** |
| L-5 | Never confirmed despite ≥3 visits | per-address | **212** |
| L-6 | Visits per confirmed address | 5,578 ÷ 900 | **6.2** |
| L-7 | Visits per met-someone visit | 5,578 ÷ 2,268 | 2.46 |
| L-8 | First-visit met-someone / not-traceable | first visit per address | **37.8% / 33.0%** |
| L-9 | Last-visit met-someone | last visit per address | 43.6% |
| L-10 | Confirmation rate by vendor stratum | addresses ever confirmed ÷ addresses in stratum | locality **72.5%** · street 70.8% · rooftop 68.1% · **pincode 55.8%** |
| L-11 | Pincode-stratum never-confirmed | 85 of 150 addresses; 257 visits spent | **257 visits** |
| L-12 | Coarse-only / unplaceable book | OUT ∨ no sub-town evidence ∨ no house-number marker | **1,331 = 42.7%** |
| L-13 | Repeat-visit convergence | median pairwise check-in distance among multi-visit addresses | **194.8 m** (met-subset 173.1 m; never-met 249.3 m) |
| L-14 | Tight convergence share | multi-visit addresses with all visits ≤50 m | **9.3%** (≤100 m: 17.1%) |
| L-15 | Training-eligible visits | met-someone ∧ dwell ≥180 s | **2,224 = 39.9%** |
| L-16 | ≥2 independent confirmations | distinct agents with met-someone visits | **439 addresses** (vs 957 addresses visited by >1 agent under the loose definition) |
| L-17 | Repeated-media visits | visits whose photo hash appears elsewhere | **172 = 3.1%** (largest hash group 32) |
| L-18 | One agent's media anomaly | FA009 | 610 visits, **162 with a repeated hash (26.6%)**, 156 within-agent duplicates (25.6% duplication rate); every other agent ≤0.3% |

### L.2 The accuracy and evidence facts (from the EDA pass, re-stated for this argument)

| # | Quantity | Value |
|---|---|---|
| L-19 | Vendor pin coverage / granularity | 2,880 of 3,117 (92.4%); locality 71.2%, street 17.5%, pincode 9.5%, rooftop 1.7% |
| L-20 | Vendor error vs surveyed truth (n=100) | median 376.4 m; p75 539.4; p90 839.2; <50 m 5.0%, <100 m 9.0%, <250 m 35.0%, <500 m 71.0% |
| L-21 | Candidate-arm ceiling (n=100) | vendor pin 92.4% coverage / 376.4 m · matched locality 65.9% / 356.7 m · town centroid 92.4% / 2,740 m · **oracle 306.2 m** |
| L-22 | Memory anchor accuracy (surveyed, met-someone) | **24.0 m** median, 87% <100 m, n=38; better than the pin in **89%** of cases |
| L-23 | Failure-visit geometry | `address_not_traceable` check-ins: median **1,603.2 m** from truth, closer to the pin **84.9%** of the time (n=53) |
| L-24 | Trail truth test | check-in → nearest own-trail point: median 7.6 m, **max 90.8 m**, 0 visits >100 m |
| L-25 | Dwell vs outcome | met-someone 0.0% (<1 min) → 2.3% (1–3) → 59.7% (3–10) → 100% (10–25 min) — a generator artefact, usable as a *mechanism* only |
| L-26 | Selection bias | exposure 25.1% (DPD 0–30) → 96.8% (180+); visited accounts' median DPD 68 vs 15 |
| L-27 | Cost of our own compute | whole pipeline ≈ **24 s**, 160 MB, one CPU; storage < 30 MB |

### L.3 What is *not* measurable, stated plainly

`[UNKNOWN]`: per-visit rupee cost; time-to-first-contact; sync lag; device/offline behaviour; the manual investigation
queue; skipped-visit outcomes; real address-change (staleness) events; notice delivery; disputed-address volume;
cross-agency reuse. Each of these becomes measurable the moment §M's instrumentation exists — and **no estimate of
them appears anywhere in this package.**

---

## M. WHAT REQUIRES FUTURE OPERATIONAL DATA

| # | What to log | Why it matters | Minimum schema | Unlocks |
|---|---|---|---|---|
| I1 | **Decision-to-skip / decision-to-visit** per address, with the reason and the confidence at decision time | without it, "fewer visits" is unprovable and triage cannot be learned | `address_id, decided_at, decision, reason_code, tier, evidence_class, pack_version` | M8, avoided-visit claims, triage model |
| I2 | **Notice event** (sent at, channel, which address text, agency named) | RBI requires advance notice and inspection readiness `[S55]` | `address_id, notice_id, sent_at, channel, agency, address_text_hash` | M15, disclosure-incident analysis |
| I3 | **Slot economics** (agent day, visits planned/attempted, travel) | turns visits into money | `agent_id, date, planned, attempted, travel_min, distance_km` | cost per confirmed place, J1 |
| I4 | **Manual investigation queue** (case, minutes, what was looked up) | the hidden labour pool | `case_id, opened_at, minutes, action, outcome` | J1 #7 |
| I5 | **Sync telemetry** (queue depth, retries, conflicts, clock offset) | the offline failure modes are invisible today | `device_id, event_id, attempted_at, result, retry_n, clock_offset_s` | M9, data-quality assurance |
| I6 | **Pre-visit pack contents** | to prove the brief changes outcomes | `visit_id, pack_version, radius_shown, landmarks_shown, last_confirmation_age` | J1 #2/#4 |
| I7 | **Human adjudication decisions** on contested evidence | the label for the contradiction policy | `place_id, both_positions, reviewer, verdict, decided_at` | contested-state tuning |
| I8 | **Address-change events from lenders** | the only honest route to a decay rate | `address_id, changed_at, field_changed, old_hash, new_hash` | staleness policy |
| I9 | **Place-use events** (a place answered a query for another case/portfolio) | measures reuse, the core compounding claim | `place_id, query_id, source_event, portfolio` | M8, J1 #9 |
| I10 | **Reviewer-verified outcomes** (spot audits of outcomes) | the only way to know outcome labels are honest in a real book | `visit_id, audited_at, auditor, agrees, note` | label trustworthiness |

**Design rule for all instrumentation:** each item must be *captured as a by-product of work already being done*. Any
instrumentation that adds a separate reporting step for field staff will not survive contact with a live book — the
same lesson the offline literature reports about capture design `[S61]`.

---

## N. WHAT IN OUR CURRENT SUTRA ARCHITECTURE IS STRONG

Ten components that survive the challenge, each with the evidence that lets it survive. (Nothing is retained "because
it sounds impressive"; the kill list is §O.)

| # | Component | Why it survives | Evidence |
|---|---|---|---|
| N1 | **Granularity + radius as the primary output** | the PS demands it, and the vendor's own label shows the error spread is 13× across strata | rooftop 25.6 m → pincode 1,375.8 m (surveyed); the label is usable, the pin is not `[DATA]` |
| N2 | **Evidence separated from truth** | failure check-ins would poison any naive learner | failures 1,603 m from truth, closer to the pin 84.9% of the time `[DATA]` |
| N3 | **Two-dimension outcome vocabulary** | one column carries place and person facts; conflating them destroys the refusal decision | `locked_premises` (22.4%) and `no_such_person` (3.7%) mean opposite things `[DATA]` |
| N4 | **Candidates + ranking, not coordinate regression** | a regressor would invent precision the text does not carry; the oracle over three arms shows the recoverable headroom | oracle 306.2 m vs pin 376.4 m; 8.4% of records have no sub-town evidence `[DATA]` |
| N5 | **Append-only, place-anchored memory** | corroboration, contradiction and audit all require immutability; repeat visits do **not** self-converge, so memory must be explicit | 194.8 m repeat spread; 439 corroborated places `[DATA]`; `[S61]`,`[S63]` |
| N6 | **Exposure-weighted learning and reporting** | visits are allocated by risk, not by need; unweighted metrics describe the vendor's policy | exposure 25.1% → 96.8% `[DATA]` |
| N7 | **Offline pack design with versioning** | the PS requires offline, and packs are the only way knowledge reaches the field | `[S61]`,`[S62]` |
| N8 | **A first-class refusal state** | 237 addresses (7.6%) are outside every town and 0% geocoded; a system that refuses is more useful than one that guesses | `[DATA]`; industry practice `[S48]` |
| N9 | **Stage-tagged features and leakage discipline** | the outcome sits in the same table as the check-in; only staging prevents the classic leak | T0–T4 map; `[S64]` |
| N10 | **CPU-cheap, reproducible pipeline** | because re-deriving everything costs ~24 s, the loop can afford to be conservative and reversible | `[DATA]` |

**The strongest asset is not a component — it is the measured premise**: a confirmed visit is 15× better than the
vendor pin, and 73.5% of visits re-walk known ground. That combination is why the loop is worth building at all.

---

## O. WHAT IN OUR CURRENT SUTRA ARCHITECTURE IS OVERENGINEERED OR WRONG

### O.1 Errors that need correcting (in order of severity)

| # | Problem | What we claimed | What is true today | Action |
|---|---|---|---|---|
| **O-1** | **The integrity gate rests on an unreproducible number** | "645 check-ins (11.6%) are >500 m from their own trail" — repeated in `README_DATA_PS3.md`, `PS3_ADVANCED_ARCHITECTURE_RESEARCH.md`, `PS3_ARCHITECTURE_OPTIONS.md` | measured now: **0 visits** have a check-in >100 m from their nearest own-trail point (max **90.8 m**, median 7.6 m). >500 m to the trail *centroid* = 1,016 visits (18.2%); to the trail *start* = 2,353 (42.2%). The "645" matches none of the three definitions and appears to be an orphan from an earlier pass | rewrite the justification: integrity is justified by **media duplication** (FA009, 162/610) and timing anomalies, and its scope is narrowed to media/timing — not "check-in vs trail" |
| **O-2** | **A learned evidence-weight model is unjustified** | a learned layer weighting visit evidence | dwell→outcome separation is near-deterministic in this generator (0% → 100%); eligible volume is 2,224 visits | ship the **rule/weight table**; keep a learned version as an explicit challenger with an independent-data requirement |
| **O-3** | **"Slow loop / drift detection" is over-scoped** | continuous learning, drift detection, retraining cadence | 89-day window, no regime change, ~430 visits/week, no seasonality | reframe as **monitoring + pre-registered triggers + replay simulation**; drop any implication of online learning |
| **O-4** | **Decay curves cannot be fitted** | memory decay, half-lives, freshness scoring | no address-change events, no multi-year history `[UNKNOWN]` | replace fitted decay with a **policy TTL + re-verification triggers** (§G.3); reconsider when I8 exists |
| **O-5** | **Our own document sits inside the frozen official folder** | `data/official_ps3/` is "official, read-only, hash-frozen" | it contains `README_DATA_PS3.md` — authored by us, carrying paths into a retired sibling workstream and into retired tooling (`tools/check_section.sh`), plus the stale O-1 claim, and it sits inside the hash set | move it out to a neutral location; the immutable folder keeps only the 11 CSVs and the dataset's own README; re-baseline the hash set |
| **O-6** | **Stale numbers propagated across documents** | "free-data ceiling 370 m"; "385 m → 29 m" framing | today's measurement on the same 100 truths: **oracle 306.2 m** over the current three arms; pin 376.4 m; **memory anchor 24.0 m**. "385 → 29" came from a different, earlier candidate set and a different subset — it is directionally right, numerically stale | one consistency pass; every number in §L replaces its ancestor |
| **O-7** | **"Six models" is more than the data can support** | a six-model architecture | 100 truths, 439 corroborated places, 2,224 eligible visits | two earned components (candidate/ranking scorer, evidence-to-belief rules) + rules elsewhere; the rest stay RESEARCH ONLY |
| **O-8** | **The landmark sub-system was argued for the wrong reason** | landmarks as a candidate/coordinate source (then rejected at 4,093 m naive snapping) | the PS requires **landmark-based directions** — human guidance, not coordinates. Landmarks are a *product requirement*, not a location feature | keep landmarks for what the PS asks (directions + plausibility), stop evaluating them as a coordinate source |
| **O-9** | **"957 multi-agent confirmed" was too loose** | two-agent confirmation as the promotion signal | 957 counts *any* visit by a second agent; **439** is the number with ≥2 *met-someone* confirmations | promotion rule keyed on quality-gated independent confirmations |
| **O-10** | **Calibration language where calibration is impossible** | conformal-style radii for all strata | `pincode` n=10, `rooftop` n=1 in the surveyed sample | publish empirical hit-rates for measured strata; parent-fallback + visible labels elsewhere |

### O.2 Components that are legitimate but should shrink

| Component | Keep | Shrink to |
|---|---|---|
| Candidate generation | yes | three arms (vendor, matched locality, town centroid) + a memory arm; no exotic retrieval without evidence |
| Ranker | yes | GBDT over ~40 stage-tagged features; monotone constraints; no neural ranker |
| Uncertainty | yes | tier + empirical hit-rate + radius; no nominal-confidence claims without measurement |
| Integrity | yes | media duplication, dwell plausibility, coordinate reuse, accuracy class — no trail-shape test |
| Memory | yes | append-only place records with corroboration, contest and stale states |
| Agent features | yes | integrity and monitoring only; never a location feature |
| H3 / digital address codes | possible later | not a differentiator; the PS asks for lat/lon + radius + directions |
| LLM parsing | no | rules + gazetteer + char n-grams; a parser is BUILD-IF-TIME |

### O.3 What we were right to refuse (and should keep refusing)

| Refusal | Why it stays right |
|---|---|
| Treating surveyed coordinates as features | they are the only truth we have |
| Treating a check-in as ground truth | failures sit 1,603 m from truth |
| Counting a negative outcome as a location | it would erase exactly the suspicion the system needs |
| Adding external geographic data as training rows | **prohibited outright** (final data policy, 2026-10-07): the official dataset is the only data; the frozen benchmark and every feature come from it |
| Retraining on every visit | 339 rows/day against a generator |
| Publishing a single accuracy number | the truth set is 100 rows and partly inside the training split |

---

## P. ALTERNATIVE PRODUCT / SYSTEM CONCEPTS

Five concepts that could rise out of this problem. They are described as *what they would be for the company*, not as
build orders; §R selects.

| # | Concept | Who uses it | What it needs that we have | What it needs that we do not | Complexity |
|---|---|---|---|---|---|
| **P1** | **Uncertainty-first address service** (the PS, literally): every address answered with coordinate + radius + landmark directions + refusal | field agent, allocator, downstream systems | 3,117 addresses, vendor strata, gazetteers, 100 truths | acceptance tests in a live book | low |
| **P2** | **Evidence-to-knowledge loop**: confirmed visits become place records; corroboration; contestation; as-of belief; every capture structured for reuse | field ops, data/ML | 5,578 visits, 439 corroborated places, the eligibility ladder | instrumented notice/plan/skip events | medium |
| **P3** | **Field-effort triage**: visit-worthiness and search strategy per address from evidence class, attempt history and confirmability | field ops, allocation, finance | attempt counts, stratum failure rates (51.8% pincode), the 56.0% vs 40.5% signal | slot economics (I1, I3) | medium |
| **P4** | **Offline evidence-capture kit** (turnkey capture contract: structured outcome, media, GPS, plan id, idempotent sync) | engineering, any field team, CN's own app | the contract in §F.3, §H | device/app ownership | medium |
| **P5** | **Compliance-grade visit ledger**: notice → visit → evidence → confidence, one queryable record | compliance/risk, auditors, clients | visit, dwell, media, trail, outcome, timestamps | notice events (I2), adjudication records (I7) | medium-high |

**Reading the table.** P1 is required by the PS today. P2 is the compounding asset — and it is the only concept that
makes P1 better every month without a human preparing data. P3 is where a finance conversation becomes possible, but it
needs instrumentation we cannot fake. P5 is where willingness-to-pay is likely highest in 2026 — because the RBI
framework makes notice and contact provable obligations `[S55]`, and CN already sells compliance posture `[S51]`.
P4 is an enabler, not a product.

**Cross-cutting observation (the pbKey lesson).** Geospatial MDM has solved the "same place, many systems" problem by
issuing a **persistent place identifier with a stated accuracy** and by getting departments to agree on *one* geocoding
methodology `[S66]`. That is exactly the artefact PS3 should produce — a company-owned place record with an ID and a
precision — which means we are not inventing a category; we are buying into a known one at a small scale.

---

## Q. RED-TEAM OF THOSE CONCEPTS

| # | Concept | How it fails | The embarrassing version | Kill criterion |
|---|---|---|---|---|
| P1 | Uncertainty-first service | agents ignore radius; allocators use it as a filter and starve coverage | a "90 % radius" that misses in the field because it ignored agent standing variation (repeat spread p75 = 251.7 m) | if agents cannot act on the radius after two field trials |
| P2 | Evidence-to-knowledge loop | corroboration is scarce → few promotions; or promotions are wrong because two agents followed the same bad assumption | a "confirmed" place built from one agent's three visits | if ≥2-independent-confirmation count stops growing after 3 months |
| P3 | Field-effort triage | triage is learned from a biased sample and starts skipping the addresses where a good agent *would* have succeeded | "we reduced visits by 20 %" while not-traceable rose | any cohort where a skip is followed by a confirmed visit by a different route |
| P4 | Offline capture kit | capture friction or sync failures poison the data at the source | duplicates tripling observations (a documented real failure `[S61]`) | sync conflict rate above a pre-set threshold in a 4-week pilot |
| P5 | Compliance ledger | legal exposure increases if the ledger is incomplete — a partial audit trail is worse than none | a notice recorded with no address version, indefensible in an inspection | any audit question the ledger cannot answer |

### Q.2 Red-teaming the *premise* itself

| Threat to our own thesis | Why it could be right | What we would do about it |
|---|---|---|
| **Field visits shrink** (digital channels improve, UPI autopay, regulation makes contact expensive) | the PS premise "learns from visits" weakens if visits become rare | the loop still pays off on the visits that happen, and the place records serve *all* channels; but the value case weakens — this is the biggest external risk to the plan |
| **The synthetic benchmark misleads us** | dwell→outcome near-determinism proves the generator encodes outcome through effort | never quote a model's *magnitude* from this data; keep the rule table primary and instrument a real pilot |
| **Lenders will not share clean address text** | our parse quality depends on text quality | the architecture degrades to tier + refusal, which is why refusal is first-class |
| **Agents will not capture structured evidence** | field friction is real | capture must be ≤20 s of taps and useful *to the agent first* (the brief, the map, the history) |
| **The 100-record truth set overfits our choices** | 66 of its accounts are in the train split | pre-register the split usage; treat every headline number as indicative, and publish n always |
| **The company already has this** | CN sells a field app with GPS and dashboards `[S51]`,`[S52]` | possible — which is why the honest differentiation is *place knowledge + eligibility + audit*, not another dashboard |
| **Nobody owns the loop** | a knowledge asset with no owner rots | name the owner at design time (knowledge owner, §K owners column) |

---

## R. RECOMMENDED DIRECTION

### R.1 The operational loop we actually want

Not the diagram from the brief, and not our own first draft. The loop that matches the evidence is:

```
address arrives ─► evidence-scored resolution (candidates + tier + radius + landmark chain)
      │                                   │
      │                                   └─► memory consulted FIRST (corroborated place? answer, no vendor call)
      ▼
field decision ─► visit-worthiness from evidence class + attempt history + confirmability
      ▼
offline visit ─► plan + last confirmation + radius carried in the pack
      ▼
structured observation ─► outcome (place/person split) + dwell + coordinate + media + remark + plan id
      ▼
gates ─► valid ─► trusted ─► independent ─► derived
      ▼
place knowledge ─► PROVISIONAL → CONFIRMED → (CONTESTED | STALE)   ← append-only, as-of queryable
      ▼
reuse ─► next case at this address, next portfolio at this building, next agency at this landmark
      ▼
training eligibility ─► buffer ─► gated retrain ─► promotion ─► pack refresh ─► the field again
```

**What is different from our earlier architecture:** the loop starts at *memory first* (not vendor first); the field
decision is a first-class step with its own evidence; the capture is designed for reuse; and there is exactly one
knowledge object (the place) with explicit states and an owner.

### R.2 The three things worth doing — in priority order

| Priority | What | Why it is first | The claim it must earn | Not doing |
|---|---|---|---|---|
| **1** | **Evidence-scored resolution with refusal** (P1) — tier, radius, landmark chain, memory-first lookup | it is the PS's literal requirement, it is buildable from what we hold, and it immediately improves *what the next visit can achieve* | confidence intervals published per stratum with n, and a refusal state that is honest | no learned re-ranker until the rule baseline is measured |
| **2** | **The knowledge loop with the eligibility ladder** (P2) — corroborated places, contestation, as-of belief, structured capture contract | it converts the 73.5 % repeat volume into a compounding asset, and it is what makes everything else improve without human data preparation | 439 corroborated places growing month over month, with the eligibility rule published | no decay curves, no drift detection theatre, no LLM in the ingestion path |
| **3** | **Effort triage + compliance ledger** (P3/P5) — visit-worthiness and the notice→visit→evidence record | this is where finance and compliance value becomes *legible*, and it is where the RBI framework bites in 2026 `[S55]` | "we skip only where evidence says effort cannot help", with the guardrail metrics reporting alongside | no triage model before the skip log exists |

### R.3 What we deliberately do **not** recommend

| Not recommended | Why |
|---|---|
| Any claim of cost reduction expressed in money | we cannot see a single rupee of CN's field or vendor spend `[UNKNOWN]` |
| More models | two components earn their place; the rest is rules and policy |
| External geographic data folded into training | it may enter as *knowledge or candidates* only if it passes the seven tests in the brief, and never as the headline number |
| Eliminating field visits | the PS says "learns from visits"; the target is *fewer unnecessary, repeated or poorly targeted visits, with more information from each necessary one* |
| A demo-led design | the demo comes after the loop produces a better next visit, measurably |

### R.4 The first three experiments (all official-data-only, no training)

| # | Experiment | What it settles | Measurement |
|---|---|---|---|
| X1 | **Memory-first backtest** (the §G.2 test, formalised) | whether a corroborated place is a better answer than the vendor — and the radius it needs | median error + hit-rate curve for memory vs pin on the surveyed block; 90 m repeat spread as the radius floor |
| X2 | **Triage counterfactual audit** | whether "already-confirmed addresses succeed more often" holds under risk-matched cohorts | 56.0 % vs 40.5 % re-measured within DPD bands and towns |
| X3 | **Eligibility and yield per stratum** | how much of the book a conservative rule would actually learn from, per vendor stratum | 39.9 % eligible overall; breakdown by locality/street/pincode |

---

## S. WHAT SHOULD CHANGE IN OUR CURRENT ARCHITECTURE

| # | Change | Rationale | Effort | What it replaces |
|---|---|---|---|---|
| S-1 | Rewrite the integrity justification; narrow its scope to media/timing/coordinate-reuse | O-1: the trail-based claim does not reproduce | small | "check-in vs own trail" test |
| S-2 | Demote the learned evidence model to a challenger; ship the rule/weight table | O-2 | medium | "evidence model" as a primary component |
| S-3 | Replace fitted decay with policy TTL + the seven re-verification triggers | O-4 | medium | decay curves/half-lives |
| S-4 | Tighten corroboration to ≥2 **independent met-someone** confirmations; publish the count (439 today) | O-9 | small | "visited by >1 agent" (957) |
| S-5 | Move our own README out of `data/official_ps3/`; re-baseline the immutable hash set | O-5 provenance discipline | small | the current arrangement |
| S-6 | Make the **eligibility ladder + event contract** first-class artefacts (gates are code, not prose) | §F; makes "training-eligible" auditable | medium | implicit eligibility |
| S-7 | Add **offline soak + chaos tests** (kill mid-sync, duplicate, clock skew, partial upload, stale pack) to the test plan | §H; published failure modes `[S61]` | medium | functional-only offline testing |
| S-8 | Demote H3/digital-address codes to "possible later"; keep lat/lon + radius + directions | O-8, PS text | small | the "address-as-code" flourish |
| S-9 | Add **"known then"** as-of semantics to the memory/belief layer, with `ingest_time` on every event | §F.4; `[S64]` | medium | "current state" reads |
| S-10 | Publish metrics only with definition + denominator + guardrail pair; retire any number without an n | §K | small | the standing headline-metric habits |
| S-11 | Add the effort-allocation/triage component **only after** the skip log (I1) exists | P3 needs a counterfactual | deferred | any pre-emptive triage model |
| S-12 | One consistency pass across all prior documents for O-1/O-6 stale numbers | the package must not argue with itself | small | duplicated stale claims |

**Net effect:** the architecture loses two components (fitted decay, learned evidence weighting), gains one
(eligibility/gates as a first-class artefact), and becomes *more* defensible while getting smaller.

---

## T. WHAT SHOULD REMAIN UNCHANGED

| # | Invariant | Why it is not negotiable |
|---|---|---|
| T1 | **Evidence is never truth**; one negative observation can never relocate a coordinate by itself; accumulated independent negative evidence demotes confidence, widens the radius, marks `MOVED_SUSPECTED`/`CONTESTED` and triggers re-verification; only positive evidence or adjudication can establish a new primary coordinate (F2.1/D36) | failures sit 1,603 m from truth and point at our own pin |
| T2 | **Answer with granularity + radius + directions, or refuse** | the PS requires it; the vendor's own label shows why |
| T3 | **Two-dimension outcome vocabulary** (place / person) | one column carries two meanings; refusal depends on the split |
| T4 | **Append-only, place-anchored memory with explicit states** | corroboration, contestation and audit all require it; repeat visits do not self-converge |
| T5 | **Exposure-weighted learning and reporting** | visits are allocated by risk, not by need |
| T6 | **Refusal / explicit unknown as a product state** | 42.7 % of the book is coarse-only or unplaceable; a guess is worse than a refusal |
| T7 | **Stage-tagged features, leak-free by construction** | the outcome shares a table with the check-in |
| T8 | **Field evidence is the company's asset, not the agency's or the vendor's** | agency turnover is normal `[S58]`; knowledge must survive it |
| T9 | **No training until the floor and ceiling are measured** | the discipline that produced this document's honest numbers |
| T10 | **Official dataset is the only data — external knowledge rejected** | the headline number, every feature and every experiment come from the supplied data; external augmentation was considered and rejected (freeze §DATA) |
| T11 | **CPU-cheap, reproducible, reversible** | ~24 s for the whole pipeline; reversibility is what allows conservatism |
| T12 | **The goal is fewer *unnecessary* visits with more information per *necessary* one** | the framing the PS actually permits |

---

## FINAL JUDGEMENT: WHAT WOULD MAKE CREDITNIRVANA ACTUALLY WANT THIS SYSTEM?

Answered from seven seats at the table. Each answer names **what they would pay attention to**, **what would make them
say yes**, and **what would make them reject it**.

| Seat | What they care about | What makes them want it | What makes them reject it |
|---|---|---|---|
| **Collections operations** | slots that land, fewer wasted mornings, cases that close | a brief that says *where* to look and *how sure* we are; addresses that stop being re-attempted from scratch; the 73.5 % repeat volume visibly shrinking | anything that adds work to the agent's day, or that tells them less than the vendor pin |
| **Product** | a capability that shows up in the platform story and wins deals | "address intelligence with published confidence and refusal" plugs into the existing field app and modules `[S52]`; it is a *feature*, not a parallel product | a research artefact with no UI, no SLAs, no API |
| **Finance** | where the money leaks; unit economics | the repeat-visit and never-confirmed volumes (73.5 %, 29.6 %, 6.2 visits per confirmed place) are *quantified* rather than asserted `[DATA]`; and every future claim is measured, not modelled | any ROI number that cannot be traced to a logged event — which is exactly why §J has none |
| **Field operations** | agent productivity, travel, disputes with agencies | confirmed places cut dead travel; the pack replaces phone-a-friend; evidence is defensible when a client disputes a visit | a system that criticises agents on one signal (the "25.6 % duplicate media" trap) without context or appeal |
| **Data / ML** | honest data, reproducible numbers, a loop that improves | the eligibility ladder (39.9 % eligible today), the event contract, "known then" discipline, and a benchmark that cannot be quietly replaced | a model that must be retrained weekly on 339 rows, or metrics without denominators |
| **Compliance / risk** | RBI framework from 1 Oct 2026, DPDP, auditability | notice → visit → evidence → confidence as one queryable record; refusal instead of a wrong-door notice; immutable history with policy versions `[S55]` | a partial audit trail; a system that cannot say which address text the notice was based on |
| **Engineering** | operability, blast radius, cost | offline-first with idempotency and server-authoritative state; ~24 s CPU pipelines; few moving parts; rollback by version | distributed complexity, feature-store platforms for 3,117 rows, or a knowledge store with no owner |

### The intersection — where the winning idea sits

```
PS3 REQUIREMENT (lat/lon + radius + landmark directions, learned from visits, offline)
  + REAL OPERATIONAL PAIN (73.5% repeat visits; 29.6% of visits produce no knowledge; coarse pins fail half the time)
  + MEASURABLE ECONOMIC VALUE (slots are the dominant cost; memory answers are 15× better than the vendor's)
  + REUSABLE COMPANY KNOWLEDGE (place records survive agents, agencies and portfolios)
  + DYNAMIC LEARNING (immediate: belief/confidence; controlled: models, on gates)
  + OFFLINE PRACTICALITY (the pack is where knowledge becomes field behaviour)
  + LOW OPERATIONAL COMPLEXITY (rules first, two earned models, one CPU)
```

**The direct answer, in four sentences.**

1. **They would want it because it converts an expense they already pay — field visits — into a company-owned asset**:
   right now 73.5 % of visits re-walk known ground and 29.6 % produce nothing durable, while a single confirmed visit
   is worth **24 m versus the vendor's 380 m**.
2. **They would want it because it lets them say something they cannot say today** — *"here is where this address is,
   here is how sure we are, here is when we last confirmed it, and here is what we will do if we are not sure"* — which
   is simultaneously the PS's output requirement, the allocator's decision input, and the auditor's evidence.
3. **They would keep it because it gets better without anyone preparing a dataset**: every visit is captured in a form
   the system can validate, corroborate and learn from, and the eligibility rule that decides what may be learned is
   itself published and auditable.
4. **They would reject it if it pretended.** If we quoted an ROI we cannot measure, a drift detector that has no drift
   to detect, a decay curve fitted on 89 days, or an accuracy claim built on 100 addresses that are partly inside the
   training split — the whole thing becomes a liability in an inspection.

**The one-line answer.** Build the address-truth loop the PS actually asks for — *resolution with radius and directions,
memory-first, offline-delivered, evidence-gated* — and sell it on the three things the company can prove: **where the
place is, how sure we are, and what happened at the door**; everything else is either instrumentation we still owe
ourselves (§M) or a claim we have no right to make yet (§O, §Q).

---

**Sources.** External claims resolve in `PS3_SOURCE_REGISTER.md` — new groups **L** (the company, the market and the
money: `[S51]`–`[S60]`) and **M** (field-data engineering, offline sync, ML data contracts: `[S61]`–`[S66]`), plus
internal evidence `[S90]`–`[S93]`. Every dataset number in §A–§T is `[DATA]` from `data/official_ps3/` only
(12 tables · 177,196 rows after the 2026-10-07 scope import; 11 tables · 177,190 rows at authoring time), with the repeat-work, convergence, eligibility and memory-backtest figures first measured in
this pass and recorded as `[S93]`. No external dataset, augmentation, scraped source or third-party model has been used
as data anywhere in this package, and no financial figure in §J is presented as CreditNirvana's.

