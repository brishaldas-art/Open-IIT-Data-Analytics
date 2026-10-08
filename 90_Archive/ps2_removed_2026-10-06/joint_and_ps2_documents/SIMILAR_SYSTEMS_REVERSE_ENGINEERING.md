# SIMILAR SYSTEMS — REVERSE ENGINEERING

**Phase 4, File 1 of 13.** Reverse-engineering of serious systems that solve problems adjacent to PS2 and PS3, done *before* designing anything.

**Method.** For every system: what is publicly establishable about its architecture (not its marketing), what it proves, what we can borrow, what we must not copy. Sources are numbered `[S-nn]` and listed in `ARCHITECTURE_RESEARCH_BIBLIOGRAPHY.md`. Claims are tagged `[VERIFIED]` (stated by the operator/author), `[INFERENCE]` (we deduced it from published detail), `[VENDOR CLAIM]` (a number the vendor publishes about itself), `[UNKNOWN]` (not publicly establishable).

**The single most useful finding.** Three of the most serious systems in this space — Experian Optimize, FICO's decision platform, and the NYS Department of Taxation & Finance deployment — converge on the **same five-layer shape**: *state → prediction → rules/constraints → constrained optimization → rules out*. None of them is "features → model → threshold". The competition-grade version of PS2 is not a better classifier; it is that shape, built small and honestly. `[VERIFIED]` for each of the three; the convergence is our `[INFERENCE]`.

---

## Part A — How to read this file

Each system gets a **row** in the library table (§1) and, for the twelve most instructive, a **tear-down** (§2–§13) using the fields demanded by the brief: *System · Problem · Inputs · State representation · Models · Retrieval · Ranking · Rules · Optimization · Feedback · Storage · Serving · Monitoring · Failure handling · Human override*.

Systems are classified as:
- **[P]** production commercial system — architecture partly public, behaviour observable
- **[O]** open-source system — inspectable
- **[A]** academic prototype with a real deployment
- **[R]** research architecture — not deployed, but the design is published in detail

---

## 1. The library — 24 systems at a glance

| # | System | Class | Domain | Core problem | Architecture in one line | Important idea | Borrow | Do NOT copy |
|---|---|---|---|---|---|---|---|---|
| 1 | **Experian Optimize** (ex-Marketswitch) | P | Lending/collections strategy | Choose the best combination of actions under constraints | Strategy-tree + constraint-based mathematical solver, evaluated over scenario simulations `[S-3][S-4]` | Optimization is over **combinations** of decisions, not per-row argmax | Constraint-based allocation with scenario simulation as the acceptance test | Its scale (trillions of strategy evaluations) — we need one day's plan, not a portfolio repricing engine |
| 2 | **Ascend Intelligence Services Collect** | P | Collections | Next best action + contact channel per customer | "Optimized collections decision strategy" riding on 2,100+ attributes and 20+ years of file data `[S-1]` | NBA is delivered as a **decision strategy service**, not a model endpoint | Decision strategy as the deliverable artefact, with the model inside it | The assumption that a deep credit-attribute library is available to us |
| 3 | **PriorityScore / Collection Advantage** | P | Collections prioritisation | Who to work first, at what dollar value | Suite of catch-up scores + segmentation feeding a work queue `[S-5]` | Prioritisation ≠ prediction: the same score is used differently by bucket | Rank by *dollars-weighted* propensity, not raw propensity | Treating score bands as decisions (they are inputs to a decision layer) |
| 4 | **FICO Decision Management / Platform** | P | Enterprise decisioning | One decisioning layer for many decision types | Business rules + optimization + simulation + analytics, orchestrated by DMN decision models `[S-14][S-15][S-16]` | **Simulation and champion/challenger are first-class platform features**, not add-ons | Copyback simulation, challenger slots, DMN-style decision description | Enterprise governance overhead (decision service catalogues, DecisionOps tooling) |
| 5 | **FICO TRIAD / Strategy Director** | P | Account management | Segment, score, test, report on account strategies | Strategy management with champion/challenger, segmentation, streaming decisioning `[S-18]` | Strategies are **versioned business artefacts** a business user edits; models are components inside them | Strategy version on every decision record | The premise of a large analyst team maintaining strategies |
| 6 | **TransUnion TruLookup** | P | Skip trace / investigations | Locate people, assets, relationships | 10,000+ public/proprietary sources fused by TLOxp; "powered by data fusion and advanced linking" `[S-10][S-11]` | Contact intelligence is an **identity-and-relationship graph**, queried as a product | Model our internal contact slate as a graph (borrower–phone–address–shared-with) | Buying/building a 100B-record data pool; we have no such data |
| 7 | **TransUnion Phone Behavior Intelligence** | P | Outbound contact | Which number, what time, will it be answered and by whom | "Contactability" score per contact + phone type + in-service indicators + TCPA risk; 15-minute refresh of call-transaction data `[S-13]` | Distinguishes **reachable** from **correct-party** — two different fields | Separate `reachable` and `right_party` in our state, never one score | Relying on network-observed behaviour we cannot see from inside the lender |
| 8 | **TransUnion Contact Compliance Risk** | P | Compliance | Don't dial a number now tied to someone else | Identifies "verified telephone numbers currently tied to the correct consumer prior to engagement" `[S-12]` | Compliance is a **pre-contact gate with its own data product** | Gate-before-dial, with the gate's evidence recorded | Its claim to verify correctness — we must produce our own evidence trail |
| 9 | **Pega Customer Decision Hub** | P | Cross-industry NBA | One action per customer per moment, under policy | Engagement policy (eligibility/applicability/suitability) → arbitration `P×C×V×L` → constraints → adaptive models learn from every outcome `[S-19][S-20][S-21][S-22]` | **"Do nothing" and contact limits are configured as first-class constraints** (e.g. 1 outbound/week) `[S-20]` | The exact layering, and the discipline of a policy layer *before* scoring | Adaptive-model opacity at scale; its action counts (50–2,500) and customer volumes are not our setting |
| 10 | **Credgenics (Indian collections SaaS)** | P | Retail collections in India | Run digital + calling + field + legal as one system | Six modules on a shared platform: digital comms, DialNext dialer, CG Collect field app, litigation, payments, analytics `[S-24][S-25][S-26]` | **The infrastructure around the decision already exists** — allocation, dialers, field app, payments | Integrate at the allocation boundary; do not rebuild dialer/field-app/CRM | Being a platform. We are a decision layer inside theirs |
| 11 | **Spocto X (Yubi)** | P | Collections journeys | Decide and execute next best action across channels with guardrails | Agentic orchestration of outreach, prioritisation, treatment recommendation, routing, with compliance controls and audit logs `[S-28]` | Executive framing: *"collections can't be treated as a set of static rules anymore… closed-loop execution where outcome signals refine strategies"* `[S-28]` | Closed-loop wording and the visible audit trail | Agentic autonomy without a rules floor; the £/₹ claims in its press releases `[S-30]` |
| 12 | **Mobicule mCollect** | P | Phygital collections | Field + digital + legal in one workflow | Six modules, offline-first field app with mandatory GPS geo-tagging, liveness face-verified logins, AI/ML beat plans `[S-29]` | **Field integrity is a product feature**, not a nice-to-have | The integrity checklist: geo-tag, liveness, offline sync, geo-fenced check-in | Assuming app-side integrity is sufficient — it is evidence, not truth |
| 13 | **NYS DTF tax collections optimization** | A | Government collections | Sequence actions under legal+resource constraints | Constrained MDP; ~300 business/legal rules enter as binary *action-constraint* features; LP relaxation; rules engine inside and outside `[S-32][S-33][S-34]` | Rules are **input to** optimization, and the output policy re-enters the rules engine for execution `[S-33]` | The "action constraints as features" pattern — cheap to implement, huge in effect | The full C-MDP; our horizon and data do not support value-function estimation |
| 14 | **Collection optimization patent (US7519553B2)** | P/R | Collections policy | Optimise action sequences over time | Constrained MDP + constrained RL, event store of historical actions/payments, debtor-state value function `[S-35]` | The **event data model** claimed: dated action and transaction events per debtor | The event model (dated action/outcome per account) — we need it regardless | The RL machinery (see `FRONTIER_*`) |
| 15 | **"Smart debt collection system" (Design Science, 2025)** | A | Consumer collections | End-to-end NB A with compliance | Offline deep Q-learning on a factorised MDP + **formal temporal-logic constraint enforcement** producing provably compliant policies `[S-36]` | Compliance expressed as a logic specification over trajectories, not a checklist | The idea that constraint violations are *provable properties of a policy*, testable offline | Requiring a full RL stack to get there |
| 16 | **MCDA decision-support framework (2026)** | A | Debt collection strategy | Jointly segment, predict, optimise | Three layers: rule extraction (unsupervised segments) → prediction (behaviour, best day/time/channel, PTP likelihood) → optimization with fuzzy logic + MCDA + mTSP routing `[S-31]` | The **three-layer vocabulary** matches our system exactly, and it names field routing as an optimization problem | The layer names and the explicit multi-criteria framing | Fuzzy inference for legal gates — hard rules must stay hard |
| 17 | **Contact-center + financial data fusion (Sánchez et al. 2022)** | A | Collections prediction | Do contact-center signals improve collection models? | Data-integration framework over 1,023,418 call records + 26,466 PTPs + 54,349 payments; three tasks: contact, PTP|contact, payment; separate models for first-touch vs follow-up `[S-38]` | Contact-center data adds **real** predictive value; first contact and follow-up are different problems `[S-38]` | Own the `first_contact` vs `follow_up` model split; treat disposition history as a first-class feature block | Claiming their lift numbers (Chilean bank, not ours) |
| 18 | **Counterfactual Risk Minimization (Swaminathan & Joachims)** | R | Learning from logs | Learn a policy from biased, incomplete logs | Propensity-scored IPS + variance regularisation → POEM `[S-39]` | The logged distribution is **both biased and incomplete**; unregularised IPS can *degrade* the system `[S-39]` | Snapshot/log propensity from day one (R1.3) even if unusable today | Running IPS on propensities that are 1.0 for 94.6% of rows (our dataset's reality) |
| 19 | **Splink** | O | Identity resolution | Link/dedupe records without a key | Fellegi-Sunter + EM, blocking rules, term-frequency adjustment, SQL backends, 100M+ records `[S-44]` | **Transparent, explainable match weights** — each pair's score decomposes into per-field contributions | Use it to surface cross-account contact conflicts (one number, many borrowers) | Graph-first ER; clustering everything before you know what a "match" means in the business |
| 20 | **Google Geocoding API** | P | Geocoding | Address ⇄ coordinate | Query → normalisation → candidate matching → ranked `results[]` with `location_type` (ROOFTOP / RANGE_INTERPOLATED / GEOMETRIC_CENTER), `partial_match`, `viewport`, `bounds`, `place_id`, `plus_code` `[S-47]` | The **response is a candidate set with machine-readable resolution class** — a vendor's own uncertainty vocabulary | Treat vendor `location_type` as our stratum key; never collapse to one coordinate | Treating the returned point as truth; caching beyond licence terms |
| 21 | **MapmyIndia / Mappls Address Standardization** | P | Indian addressing | Clean → parse → validate → standardise Indian addresses | Pipeline: cleansing → validation & normalisation (tokenise + resolve) → standardisation against an address directory, populating missing admin values `[S-50]` | **Explicitly multi-stage and modular** — you can use one stage without the others `[S-50]` | The stage split, and "populate missing admin levels during validation" as a confidence signal | Assuming eLoc/±3 m coverage for our messy residential addresses |
| 22 | **GeoIndia (Meesho) — v1 EMNLP 2024, v2 CIKM 2025** | R→P | Indian geocoding | Predict fine-grained location from messy Indian addresses | Seq2Seq predicts **hierarchical H3 cells**; ~29 state-specific models; v2 fuses Graphormer + language model by cross-attention with generative H3 decoding `[S-47bis][S-47bis]` | Spatial prediction can be **hierarchical classification over cells** instead of coordinate regression | The H3-hierarchy framing and the cell-candidate output | Building it: needs 67M addresses + millions of delivery traces `[S-47bis-prod]` |
| 23 | **GeoConformal / conformal spatial prediction** | R | Uncertainty | Get a radius that actually covers | Split conformal prediction with geographically weighted quantiles → local coverage theorem; 93.67% empirical coverage at 90% nominal vs 68.33% for bootstrap `[S-53]` | There is a **principled way to produce honest radii** that is model-agnostic | Validate our radius by coverage on held-out visits; report measured coverage | Headlining a coverage guarantee our sample can't support (the paper's own reviewer flags the unreported bandwidth `[S-53]`) |
| 24 | **Field-visit integrity stacks (fleet/field-sales/collections)** | P | Field force | Is the observation real? | Layered checks: mock-location flag (`isFromMockProvider`), rooted/emulator attestation, GPS-vs-IP consistency, teleport/movement plausibility, duplicate-photo and geofence checks `[S-63]` | Spoofing is caught by **cross-signal inconsistency**, not by trusting one flag | Weight, don't accuse: convert signals into an evidence weight | Claiming a spoof-detection rate (`FRONTIER_*`: RESEARCH ONLY) |
| 25 | **Delivery-data geocoding feedback (Descartes / LogiNext / q-commerce)** | P | Last-mile | Improve coordinates from operations | Auto-update the geocode after repeated driver confirmations; four explicit geocoding status indicators incl. "approximately geocoded → confirm before routing"; self-supervised detection of bad GPS from address text `[S-56][S-55][S-56]` | **Operational feedback as the accuracy engine** — exactly PS3's title, already productised in logistics | The status vocabulary and the "confirm before dispatch" pattern | Their confidence in auto-updates; our legal action needs a recorded gate |

---

## 2. Tear-down 1 — Experian: prediction + optimization as two engines

**[P]** `[S-1][S-3][S-4][S-8][S-9]`

| Field | Finding |
|---|---|
| **Problem** | Assign the best treatment/channel per delinquent account subject to operational and business constraints |
| **Inputs** | Deep-file credit attributes (2,100+), trended data (24 months), alternative data, contact-channel preference, plus the client's own history `[S-1][S-8]` |
| **State** | Segmentation state (risk/recovery segments) plus "what happened last" — collections optimisation is described as assigning "appropriate collection treatments by assessing the level of risk… while considering a customer's responsiveness to particular treatment options" `[S-4]` |
| **Models** | Propensity-to-pay, recovery, channel-preference, self-cure, and stress models; "patent-pending ML explainability" generating adverse-action codes from the model `[S-8]` |
| **Rules / Retrieval** | Not publicly described; the sellable unit is the decision strategy tree |
| **Ranking / Optimization** | **Constraint-based mathematical optimization** that "evaluates competing business goals, operational constraints, contact protocols and individual customer needs" and "calculates the impact of every possible decision" `[S-3]`. Marketed as evaluating "trillions of strategy options in seconds" `[S-3]` `[VENDOR CLAIM]` |
| **Feedback** | Simulation → monitor → rebuild/retrain on a regular cadence `[S-3]`; strategy trees are evaluated before deployment |
| **Serving** | Cloud; "customer-level action assignment and/or strategy tree creation"; can be embedded in a real-time call-centre flow `[S-3][S-5]` |
| **Failure handling / override** | Not public. Strategy simulation exists precisely to make failures cheap and pre-production `[S-3]` |
| **What it proves** | Optimization is a separate engine from prediction, and *constraints are configured in the optimisation problem*, not in a dashboard `[VERIFIED]` |
| **Borrow** | (a) two engines, one artefact — the strategy; (b) simulation as the safety case; (c) the idea of scoring *combinations* of decisions against portfolio goals |
| **Reject** | Their data advantages; their scale of solver; treating "trillions of options" as an aspiration |

## 3. Tear-down 2 — FICO: rules, models, optimization, simulation in one platform

**[P]** `[S-14][S-15][S-16][S-17][S-18]`

| Field | Finding |
|---|---|
| **Problem** | Operationalise analytics at scale with business-user control |
| **State** | Customer/account context assembled per decision from streaming and batch data; "stateful models … agnostic of the data source" executed with low latency `[S-18]` |
| **Models** | Predictive analytics; adaptive control ("test-and-learn … champion/challenger") `[S-17]` |
| **Rules** | Business rules are the *strategy*; models are components that "drive the actions and treatments — including product entitlement, cut-offs, pricing" `[S-16]` |
| **Optimization** | A solver under constraints and maximum-risk limits, used by business users to "find the optimal business strategy" `[S-16]` |
| **Feedback / Evaluation** | Champions vs challengers executed in production, plus **full-scenario simulation over hundreds of millions of transactions** `[S-14]`; the platform advertises an "integrated Digital Twins & Simulation Capability" `[S-15]` |
| **Serving** | Both: batch portfolio runs and in-stream low-latency decisions `[S-18]` |
| **Human override** | Business users edit strategies; "human-in-the-loop AI" is an explicit design goal `[S-15]` |
| **What it proves** | Mature decision platforms treat **simulation, challenger slots, and business-editable strategy** as core architecture `[VERIFIED]` |
| **Borrow** | (a) the four-layer split rules/models/optimization/simulation; (b) champion/challenger as a *slot in the record*, not an experiment run offline; (c) "digital twin" language for a replayable state |
| **Reject** | DMN tooling and DecisionOps governance for a 48-hour build; **also reject the "digital twin" label unless we actually replay state** |

## 4. Tear-down 3 — TransUnion: identity + contact + compliance as one contactability stack

**[P]** `[S-10][S-11][S-12][S-13]`

| Field | Finding |
|---|---|
| **Problem** | Find the right person, on a number that is theirs, legally, now |
| **Inputs** | 10,000+ public and proprietary sources; "100B+ records, 11B unique name-address combinations, 4B phone records" `[S-11]` `[VENDOR CLAIM]` |
| **State** | Person-level profile with relationship links (people ⇄ assets ⇄ businesses), plus **change monitoring**: "automatically monitor data for changes… send alerts when contact information is updated" `[S-11]` |
| **Models** | Contactability scoring (Phone Behavior Intelligence) with phone type, in-service indicators, and TCPA-risk fields `[S-13]` |
| **Retrieval** | Multi-key search from partial inputs ("inputting partial or full information to enhance skip tracing efforts and prioritisation" `[S-11]`) |
| **Ranking** | Ranks candidate numbers/addresses/emails/employers; "improve right-party contact rates with phone, address, email and place of employment" `[S-11]` |
| **Rules** | Contact Compliance Risk acts as a **pre-engagement gate**: identify verified numbers "currently tied to the correct consumer **prior to engagement**" `[S-12]` |
| **Feedback / refresh** | 15-minute refresh cycle on contact-transaction data 🗓 `[S-13]` |
| **Serving** | Online, API **and** batch; bulk appends `[S-10][S-11]` |
| **What it proves** | The industry's own architecture separates **known number / reachable number / correct consumer / outdated** into distinct fields and products, and puts compliance in front `[VERIFIED]` |
| **Borrow** | The four-field separation; change-alerts as an event stream; a gate whose evidence is itself recorded |
| **Reject** | Any dependence on external data we cannot lawfully obtain in India; the ~25%/33% RPC claims as anything other than vendor claims |

## 5. Tear-down 4 — Pega CDH: the cleanest public expression of a policy-before-model NBA engine

**[P]** `[S-19][S-20][S-21][S-22]`

| Field | Finding |
|---|---|
| **Problem** | One next-best-action per customer per moment across every channel |
| **State** | Customer profile + **Interaction History** with real-time summarisation; "Interaction History Summaries … used as predictors in Adaptive models and contact policies" `[S-22]` |
| **Models** | Predictive models (propensity, risk, churn) plus self-learning **adaptive models** updated continuously from captured responses `[S-20][S-22]` |
| **Rules (the decisive layer)** | **Engagement policy**: Eligibility (may we?) → Applicability (relevant now?) → Suitability (appropriate/ethical?) `[S-19]`; **Constraints**: outbound channel and action limits, "no more than one outbound message each week and three per month" as documented examples `[S-20]` |
| **Ranking** | **Arbitration**: `Priority = P × C × V × L` — propensity × context weighting × business value × levers `[S-19][S-20]` |
| **Feedback** | `CaptureResponse` on every triggered action; outcomes (impression/click/acceptance) feed adaptive models `[S-19][S-22]` |
| **Human override** | Business users configure taxonomy, policy, arbitration; "the CSR is always in control and can select other service actions" `[S-21]` |
| **Failure handling** | Not public; the design implies over-suppression under uncertainty is preferred to over-contact ("do nothing" is an allowed outcome) `[S-19]` |
| **What it proves** | A production NBA engine orders the layers **policy → ranking → limits**, and treats "do nothing" as an action `[VERIFIED]` |
| **Borrow** | Exactly that ordering; the three-question policy screen; contact limits as constraints; response capture as a first-class API |
| **Reject** | `P×C×V×L` as a *formula* — it is a ranking heuristic with no cost model and no risk term; our version must subtract costs and penalise conduct risk |

## 6. Tear-down 5 — the NYS DTF deployment: what constrained optimization actually bought

**[A]** `[S-32][S-33][S-34][S-35]`

| Field | Finding |
|---|---|
| **Problem** | Collect delinquent tax with limited agents, respecting law and equity |
| **Inputs** | Event data ("historical dated records of events including collection actions taken against each debtor and transactions from each debtor including payment") `[S-35]`; feature blocks named in the paper: liability, transactional (payments since last action, payments to date), collections (open warrants, days since last warrant) `[S-33]` |
| **State** | A case state that includes **legal-stage states** — e.g. a *warranted* state where levy becomes possible; the paper notes the legal requirement that "a warrant precedes levy" is modelled naturally as a state `[S-32]` |
| **Rules** | ~300 business and legal rules compiled into **binary action-constraint features** — "for each action considered, whether the action is currently allowed on the case" `[S-33]` |
| **Optimization** | Constrained MDP → primal-dual / LP relaxation with a resource-constrained value function `[S-32]` |
| **Feedback / evaluation** | Incumbent-vs-challenger model deployment "until such time as there is sufficient statistical significance to call a winner" `[S-33]` |
| **Deployment** | Weekly batch scoring for accounts with events or due review; recommendations delivered to 30–40 call-centre agents on screen and to specialised units via allocations `[S-33]` |
| **Outcome** | Delinquent revenue collections +$83 M (+8%) from 2009 to 2010 "using the same set of resources" `[S-34]` `[VERIFIED — operator-reported]` |
| **Failure handling** | Cases are routed to specialised units/district offices — i.e. **an escalation path exists for non-standard states** `[S-33]` |
| **What it proves** | (a) legal constraints can be represented as per-action availability flags and still be optimised over; (b) the value of the system shows up as *resource efficiency* (+8% with the same resources), not as a better score; (c) it cost ≈$5 M of research + ≈$4 M of engagement `[S-33]` |
| **Borrow** | Action-constraint flags; legal states as states; weekly batch as the primary path; challenger slots; escalation for the unmodelled |
| **Reject** | The five-year, nine-figure build; RL; anything needing a value function we cannot estimate from 51,105 calls |

## 7. Tear-down 6 — Credgenics / Spocto / Mobicule: what infrastructure already exists in India

**[P]** `[S-24]…[S-30]`

| Field | Finding |
|---|---|
| **Modules that exist** | Digital communications (SMS/WhatsApp/e-mail/IVR/voice-bot), predictive dialers with auto-allocation and agent dashboards, field-collection apps with GPS geo-tracking, offline support, route plans, digital receipts, payments, litigation/legal notices, skip tracing, settlement workflow `[S-24][S-25][S-29]` |
| **Decisioning that exists** | Borrower risk segmentation, channel prediction ("best channel, day, time"), intent-to-pay from outreach attempts, "strategy optimisation by tracking borrower response in real time" `[S-26]`; Spocto X positions **agentic** orchestration of who/when/channel with "clear logs for review" and "outcome signals such as contactability, promises-to-pay and repayments" refining strategy `[S-28]` |
| **Compliance that exists** | "Comprehensive frameworks for DND, frequency and daytime controls" `[S-25]`; Mobicule: DRA-certified telecalling, compliance guardrails, mandatory GPS geo-tagging, liveness face-verified logins `[S-29]` |
| **Gaps that remain (our read)** | `[INFERENCE]` What is *described* is (i) segmentation + channel/timing prediction, (ii) workflow automation, (iii) tracking and logs. What is **not** described publicly by any of them: a per-contact-point **belief state** with identity probability, an **information-purchase decision** with a dollar value, a **constrained allocation** of a day's capacity with explicit refusal reasons, or an **empirical error radius** on an address |
| **What it proves** | The pipeline (allocate → dial → visit → pay) is commoditised in India `[VERIFIED]`; the decision layer inside it is the contested space `[INFERENCE]` |
| **Borrow** | Integration at the allocation boundary; their compliance-config vocabulary (DND, daytime, frequency); field-app integrity features as a standard to meet |
| **Reject** | Rebuilding dialers, CG-Collect-style field apps, or payment rails |

## 8. Tear-down 7 — MCDA decision-support framework (2026): the closest academic match to our shape

**[A]** `[S-31]`

| Field | Finding |
|---|---|
| **Shape** | Layer 1 **Rule Extraction** (unsupervised segments: self-cured / lazy payers / delinquents / defaulters) → Layer 2 **Prediction** (behaviour, best day & time, best channel, payment likelihood, PTP likelihood) → Layer 3 **Optimization** (constrained problems: minimising communication cost, maximising recovery; TOPSIS ranking; **mTSP** for field-collector routing) |
| **Why it matters** | It is the only paper we found that names *our* three layers in the same order and then solves **field allocation as a routing problem**, validated on a real agency's mortgage portfolio `[VERIFIED]` |
| **Borrow** | The layer names as our architecture vocabulary; segmentation as a cheap, explainable prior; routing as part of the allocation problem, not a separate product |
| **Reject** | Fuzzy logic in the *legal* gate (fuzzy compliance is non-compliance). Use hard rules for prohibitions, fuzzy/MCDA only for ranking |
| **Also noted** | The same paper's literature table shows voice analytics (pitch, speed, loudness) affecting repayment `[S-31]` — evidence that contact-centre signal is real, but our dataset has no audio |

## 9. Tear-down 8 — Sánchez et al. (2022): what contact-centre data actually adds

**[A]** `[S-38]`

| Field | Finding |
|---|---|
| **Problem set** | Three tasks: (1) successful contact, (2) contact **resulting in a promise to pay**, (3) eventual repayment — each also in full-population and contacted-only variants (five models) |
| **Data** | 1,023,418 call records; 26,466 PTPs; 54,349 payments (Chilean bank) |
| **Findings** | Combining contact-centre + financial features improves prediction over either alone; **first contacts and follow-ups need separate models** `[VERIFIED]` |
| **Implication for us** | Our disposition vocabulary contains exactly this structure (`third_party_contact` vs `rpc_ptp`); our model should have separate first-contact and repeat-contact behaviour, and PTP is a distinct target from payment |
| **Borrow** | The task decomposition: contact → RPC → PTP → payment (a chain, not one label) |
| **Reject** | Their feature set (call-level audio/social features we do not have) |

## 10. Tear-down 9 — Skiptrace architecture, as patented

**[P]** `[S-60][S-61]`

| Field | Finding |
|---|---|
| **US7257206B2 (GE Capital, 2002)** | A skip-tracing system with: a **skip queue** of account+phone records populated when a number is identified as "good"; a **skip-tracing documentation database** whose recorded activities "are taken into account when performing subsequent skip tracing of the accounts"; and an operator UI to mark numbers good/bad `[S-60]` |
| **US8,819,061 (LocateSmarter, 2014)** | Cloud platform that performs "data interchange with a plurality of vendors providing skip tracing services" — multi-vendor orchestration behind one interface `[S-61]` |
| **What it proves** | The core loop of skip tracing — *attempt → record → re-prioritise the queue* — has been a patented architecture since 2002. **Our differentiation cannot be "we remember prior skip-trace results"; it must be what the queue is optimised for** `[INFERENCE]` |
| **Borrow** | (a) the queue-with-memory pattern; (b) vendor pluralism behind one interface (so tracing can be priced per purchase); (c) writing the outcome of every trace back to the account state |

## 11. Tear-down 10 — Retrieval architecture: how serious systems turn text into a ranked shortlist

**[P/O]** `[S-64]`

| Field | Finding |
|---|---|
| **Pattern** | Two-stage retrieve-then-rerank: cheap high-recall first stage (BM25 over an inverted index, and/or ANN over dense vectors) → fusion (e.g. reciprocal rank fusion, which avoids cross-channel score calibration) → expensive precision stage (cross-encoder reranker) `[S-64]` |
| **Why we need it** | PS3's candidate generation is a retrieval problem. The vendor API is one retriever; our locality/landmark/prior-visit candidates are others; the integrity-weighted ranker is the reranker. **Fusion by rank, not by calibrated score, is the safe default** `[INFERENCE]` |
| **Borrow** | Candidate generation and ranking as *separate, independently testable* components; rank fusion; recall-then-precision budgeting |
| **Reject** | Dense retrieval for its own sake: with 36 localities and 240 POIs our corpus is tiny; lexical + structural matching dominates (this is also what our dataset audit showed) |

## 12. Tear-down 11 — GeoIndia: the state of the art for *this* address problem

**[R→P]** `[S-47bis]`

| Field | Finding |
|---|---|
| **Architecture v1** | Seq2Seq over Flan-T5-base and QLF-Llama-3-8b; **target = hierarchical H3 cell**, not coordinates; ~29 models, one per state; a data-correction strategy over the address corpus `[S-47bis]` |
| **Architecture v2** | Graphormer (graph) + transformer LM (text) fused by **Key-Modulated Cross-Attention**, with **generative decoding of hierarchical H3 cells** `[S-47bis]` |
| **Published results** | >50% reduction in mean distance error and >85% reduction in p99 error vs Google Maps in multiple states `[S-47bis]` |
| **Company-reported production figures** | GeoIndia LLM trained on 67M+ Indian addresses and "millions of delivery traces"; +20 percentage points geocoding accuracy; −5% misroute-related cost; >50% reduction in last-mile misroutes when combined with their network system `[S-47bis-prod]` `[VENDOR/COMPANY CLAIM — self-reported, not audited]` |
| **What it proves** | (a) hierarchy beats raw coordinate regression for Indian addresses `[VERIFIED]`; (b) **the labels come from delivery traces** — i.e. from field operations, which is exactly the loop PS3 names `[VERIFIED]`; (c) the reproducibility bar is brutal: proprietary corpus, 29 state models `[S-47bis]` |
| **Borrow** | H3-cell candidates as our output vocabulary; the "hierarchy = the prediction" framing; traces/delivery outcomes as the label source |
| **Reject** | Training it ourselves. Our dataset has 3 towns and 100 surveyed addresses; the honest move is to *consume* hierarchy (H3/PIN) and put our learning where the data is (the visit loop) |

## 13. Tear-down 12 — Operational geocoding feedback in logistics

**[P]** `[S-55][S-56]`

| Field | Finding |
|---|---|
| **Patterns** | (a) Auto-update a stop's geocode after repeated field confirmation ("automatically updates geocodes after two visits") `[S-56]`; (b) explicit **geocoding status indicators** with a manual-review path ("approximately geocoded → flag, confirm with the customer, pause auto-assignment") and permanent capture of dispatcher corrections `[S-55]`; (c) self-supervised detection of wrong GPS using the text address (Gaussian perturbation + address-swap training sets) reaching 84.5% precision / 49% recall on a large Indian city `[S-56]` |
| **What it proves** | The field-feedback address loop is **productised and in production** in Indian logistics `[VERIFIED]`. Our PS3 is not a novel idea in the world; it is a novel *application* (legal-notice eligibility) of a proven pattern `[INFERENCE]` |
| **Borrow** | (a) two-confirmation rule before a fix becomes authoritative; (b) status vocabulary that drives *workflow* (confirm-before-dispatch → confirm-before-notice); (c) text-based sanity checks on GPS |
| **Reject** | Auto-correction without evidence weighting — a fraudster's ghost visit would then permanently poison an address (our dataset's FA009 exists precisely to test this) |

---

## 14. Cross-system synthesis: the seven patterns that recur

| # | Pattern | Where it appears | Our verdict |
|---|---|---|---|
| **1** | **Policy/eligibility precedes scoring** | Pega Engagement Policy `[S-20]`; TU Contact Compliance Risk `[S-12]`; NYS action-constraint features `[S-33]`; RBI-driven Indian compliance configs `[S-25]` | **Adopt unconditionally.** The model must never see an ineligible action |
| **2** | **Optimization is a distinct engine from prediction** | Experian Optimize `[S-3]`; FICO solver `[S-16]`; MCDA layer 3 `[S-31]`; C-MDP `[S-32]` | **Adopt at day level** (one day's calls/visits/traces under capacity), not per-account argmax |
| **3** | **State is explicit and accumulates** | TU change monitoring `[S-11]`; Pega Interaction History `[S-22]`; patent event model `[S-35]`; skip-queue memory `[S-60]` | **Adopt: a per-contact-point and per-address belief state, event-sourced** |
| **4** | **Information is purchased** | TransUnion skip tracing as a paid product `[S-11]`; multi-vendor trace orchestration `[S-61]`; Experian collecting "additional data from credit bureaus, alternative financial services, collateral records" for skip tracing `[S-6]` | **Adopt: an explicit price per information purchase and a value rule for buying it** |
| **5** | **Champion/challenger + simulation is how policies change** | FICO adaptive control & simulation `[S-14][S-17]`; NYS incumbent/challenger `[S-33]`; Swaminathan/Joachims OPE `[S-39]` | **Adopt: shadow mode + propensity logging + challenger slots** |
| **6** | **Human override and escalation for the unmodelled** | Pega CSR always in control `[S-21]`; NYS specialised units `[S-33]`; dispatcher manual review `[S-55]` | **Adopt: an override that is itself logged as an event** |
| **7** | **Evidence quality is weighted, not assumed** | field-integrity stacks `[S-63]`; q-commerce GPS-error detection `[S-56]`; conformal coverage testing `[S-53]` | **Adopt: every observation carries an integrity weight; every radius is coverage-tested** |

**And the four things that recur that we will NOT copy:** RL/agentic policy learning without propsensity-logged exploration data (`[S-36]`, `[S-28]`); fuzziness inside legal gates (`[S-31]`); auto-correction of coordinates without evidence weighting (`[S-56]`); and claiming a detection or uplift rate the deployment cannot measure (`[S-30]`, `[S-47bis-prod]`).

---

## 15. What this means for PS2 and PS3 — the three sentences this file exists to produce

1. **PS2 is not a classifier problem and never was.** Every serious system in this space — Experian, FICO, Pega, NYS DTF — is *state + prediction + rules + constrained optimization + feedback*, and the publicly reported value (+8% collections on the same resources `[S-34]`) came from the allocation and constraint layers, not from model AUC.
2. **PS3's loop is proven in logistics and absent in Indian collections.** Descartes updates geocodes from driver confirmations `[S-56]`; Meesho trained on delivery traces `[S-47bis-prod]`; Swiggy-style work detects bad GPS from address text `[S-56]`. Nobody publicly applies that loop to **legal-notice eligibility in collections** — and that application is where the permission question lives.
3. **The differentiation available to us is the refusal layer, not the prediction layer.** TransUnion sells a compliance *gate* `[S-12]`; Pega sells engagement *policy* `[S-20]`; India's RBI requires the *permitted set* from 1 Jan 2027. A system whose primary artefact is a **decision record containing why an action was refused, on evidence, with an honest uncertainty radius** has no direct comparable in any of the 24 systems reviewed — and every component of it is borrowed from one of them.
