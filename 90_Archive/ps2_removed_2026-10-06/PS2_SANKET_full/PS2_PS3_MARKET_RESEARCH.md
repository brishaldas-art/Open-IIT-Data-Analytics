# PS2 / PS3 — MARKET RESEARCH

*Consultant's view of who already solves this, what they claim, what they cannot do, and what is left.*
All claims labelled `[PUB]` (published/claimed by the vendor or press) or `[EXT]`/`[INFER]`. Vendor marketing is directional, not evidence.

---

## 1. The map

### 1.1 CreditNirvana itself — the most important competitor is the host
| | |
|---|---|
| What it is | **Agentic-AI-native collections platform for Indian BFSI**, a **Perfios company** (acquired March 2025) `[PUB]` |
| Scale claimed | 1,000+ institutions behind Perfios, **62M+ accounts under management**, $21B+ (~$11B at Maestro launch), 9 portfolio types, 400M+ data points `[PUB]` |
| Product | **Maestro** (launched 26 Nov 2025): 150+ GenAI collection agents, **20 modules**, digital + voice + **field operations** + settlement + legal + repossessions `[PUB]` |
| Claims | −60–70% human intervention, **+40% collection efficiency**, up to **95% fewer language-compliance errors**, allocation cut **24h → 30 min**, **+32% field efficiency**, 80+ dashboards `[PUB]` |
| Compliance posture | RBI-compliant, SOC 2 Type II, "timestamped consent", "immutable audit trails with policy decision logs", "RBI contact hours enforced at the dialer and AI layer" `[PUB]` |
| Client outcomes shown | bounce rates down 15–30% in 3–6 months (up to 66% in Bucket 0); a Top-5 ARC: 1.5M+ accounts, 2× portfolio capacity `[PUB]` |
| Weakness we can exploit | Everything above is **claimed at the platform level**. There is **no published mechanism** for: contact-point-level health, calibrated address confidence, or gating a recoverable action on modelled identity. "Compliant" is asserted through logs, not *proved by blocked actions*. |

### 1.2 Adjacent / direct competitors
| Player | Focus | Claims / capabilities `[PUB]` | The gap we can name |
|---|---|---|---|
| **Credgenics** | Full-stack collections SaaS (India leader) | 98M+ loan accounts, $250B+, 1.7B communications; **CG Collect** field app (geo-tag, offline, 22+ languages); DialNext predictive dialer; Swara GenAI voicebot; legal + ODR; 400+ behavioural signals; FY25 revenue ₹220 Cr, PBT ₹25 Cr; claims 20% better resolution, 40% lower cost | Field app is *recording* geo-tagging, not *address intelligence*; no modelled address confidence; no identity-gated disclosure |
| **Spocto X (Yubi)** | E2E agentic collections | **Spocto Score** (behavioural), **Connect** (contactability), Recommendation Guru (allocation), YuVoice/YuVin/YuCI; claims 9 Cr accounts prevented from NPA, ₹50,000 Cr+ ECL saved; PSB RFP wins; 20-day go-live `[PUB]` | "Contactability" is marketed as a score, not as a per-contact-point decision with a compliance gate |
| **Mobicule mCollect** | Phygital field collections | **Offline-first field app, mandatory GPS geo-tagging + geo-fencing, liveness face-verified login, OTP verification, digital receipts, AI/ML beat plans** "to prevent location spoofing" `[PUB]` | Ships the *telemetry*; does not convert it into a **learned address belief**, and does not gate notices/visits on confidence |
| **DPDzero** | AI-led full-stack, outcome-based pricing | ₹8,000 Cr recovered, 70% conversion claims `[PUB]` | Similar to Credgenics |
| **Skit.ai** | Voice AI for collections | 1B+ conversations, $47.6M raised; claims **+24% RPC**, 50–70% liquidation uplift, 17% fewer escalations; per-minute and per-outcome pricing `[PUB]` | Voice layer only; no address/field intelligence |
| **Gnani.ai / Rezo.ai** | Multilingual voice agents | Gnani: 150+ lenders, 30,000-seat equivalent; claims AI beat human teams by ~4% at an NBFC and ₹40,000 Cr collections in 6 months; 85–89% of borrowers thought it was human `[PUB]` | Interaction layer |
| **SkipTracer.in** | India borrower-reachability / tracing | "2–3 hours → minutes" per hard-to-trace borrower `[PUB]` | Tracing is a **service**; it does not price itself per account via EVSI, nor does it feed a decision engine |
| **TransUnion (TruLookup / PBI / TruContact)** | Global RPC + contact intelligence | TLOxp across **10,000+ sources / 100B+ records**; ranked phones; **Phone Behavior Intelligence claims +33% RPC**; Contact Compliance Risk; Caller Name Optimization claims 90–100% reduction in erroneous blocking `[PUB]` | Proves the *category is mature* — and that our PS2 core is not novel |
| **SkipTrace AI (US)** | Self-serve skip tracing | Confidence score 0–100 from recency + source diversity + line status; pay-only-for-results; ~$500M market `[PUB]` | US real-estate-oriented; the *confidence-scoring* idea is already productised |
| **Shiprocket Address Intelligence** | India address resolution | **Learns from delivery outcomes; 72.69% within 100 m, 90.57% within 500 m**, sub-200 ms CPU `[PUB]` | Delivery evidence ≠ recovery-visit evidence; no compliance coupling |
| **Delhivery Maps / GeoNaksha** | India geocoding LLM | **Returns an error radius**, validates against **4B+ deliveries**, offers **address-visit verification** over a 1–24 month window `[PUB]` | Logistics-first; no notion of *permissible* action |
| **Google Address Validation (India) / Mappls eLoc** | Geocoding | Google: ML parsing, component confidence, **residential vs commercial**; Mappls: **eLoc ~3 m**, India-first, INR pricing `[PUB]` | ToS restrict caching commercial output; neither is tied to a recovery workflow |

### 1.3 Answering the question we were told not to ignore
> **"If CreditNirvana already has an agentic collections platform, why would they care about our solution?"**

Because Maestro answers *"what should we do next?"* and **cannot currently prove three things**:

1. **Is this contact point actually reachable by the *right person*, or are we about to talk to a stranger?** Maestro has 150+ agents but no published, contact-point-level identity model. Every disclosure-control claim rests on scripts and logs, which RBI's 2026 framework explicitly says is not enough ("compliance will be assessed on whether your systems permitted a violation" `[EXT]`).
2. **Is this address good enough to send a legally-required advance notice to?** Under the new framework, the notice precedes the visit and is itself an irreversible artefact. A wrong-door notice is a disclosure event. Nothing in the market gates the *notice* on address confidence.
3. **What did we learn from the visit, and was it true?** Field GPS is captured (Mobicule-style) and used for beat plans; it is **not converted into a learned, integrity-weighted address belief** that changes tomorrow's decision.

So the honest positioning is not "another platform". It is:
> **A control layer for the two irreversible actions in collections — taking a compliance-bearing action against an unverified identity, and sending a recovery notice to an unverified address.**

That is a module inside Maestro, it is bought by the compliance + CFO + field-ops trio, and it makes CN's existing marketing claims *demonstrable*.

---

## 2. What users complain about (borrower side and operational side)
| Complaint | Evidence |
|---|---|
| Harassment, night calls, shaming | FY24: **85,281** loan/recovery complaints to the RBI Ombudsman, **+42.7% YoY**, ≈29% of all complaints `[EXT]`; experts estimate <5% of harassment cases are ever reported `[EXT]` |
| Lenders pay for agent behaviour | Bajaj Finance fined **₹2.5 Cr** for recovery-agent harassment `[EXT]` |
| Compensation is rising | RB-IOS 2026: up to **₹3 lakh** for harassment/mental anguish (was ₹1 lakh), **90-day** filing window `[EXT]` |
| Address-driven failure is normal | ~**30%** of last-mile shipments required a phone call to the customer to find them `[EXT]`; PIN codes frequently missing/wrong and too coarse for a doorstep `[EXT]` |
| Dashboards nobody uses | Multiple `[INFER]` — CN itself advertises "80+ dashboards out of the box", which is a warning sign, not proof |
| Tracing latency | Indian tracing sold on "hours → minutes" per case `[EXT]` — i.e. it is still a manual bottleneck |

---

## 3. Virtual advisory board (12 reviewers)

Format: **objection → answer → unresolved → what we changed**.

### 3.1 Collections Head — *"Will this improve collector productivity?"*
- **Objection:** "My problem isn't prediction, it's that my team works the same list every day. Another score doesn't help."
- **Answer:** the output is an ordered work list plus a **refusal list** (accounts not worth contacting) and a **street-level field list**. It removes work rather than adding a screen.
- **Unresolved:** whether a manager will accept "do not contact this account this week" as a recommendation from a model.
- **Changed:** made **"do nothing / wait"** a first-class output and put the refusal count on the main screen, not in a log.

### 3.2 Field Operations Head — *"Will this reduce failed visits?"*
- **Objection:** "My agents already have routes and geo-tagged check-ins."
- **Answer:** the beat plan optimises *travel*; this optimises *target quality*. The value is in the slots you don't spend, and in the notices you don't mis-deliver.
- **Unresolved:** whether address-confidence gating reduces the visit *count* by enough to notice (at ₹18.8k tickets it may not).
- **Changed:** scoped the field story to portfolios with material visit volume; made route integration optional.

### 3.3 CFO — *"Where exactly does the money come from?"*
- **Objection:** "Show me the rupee."
- **Answer (post-model):** not from dial savings — our own model shows dial-volume optimisation is worth ₹0.3–7 lakh/month on a 100k book. It comes from four places: avoided expensive actions (₹220–370 per wasted slot, ₹60–150 per wasted trace), conduct exposure (₹3–75 lakh/month band at 0.2–1% escalation), reclaimed human/field capacity, and basis-point RPC gains. See `PS2_PS3_FINANCIAL_MODEL.md`.
- **Unresolved:** the incremental-recovery-per-RPC figure (₹205 in our model) is an assumption, not a measurement.
- **Changed:** **deleted the recovery-uplift claim** from the value proposition. The pitch is now *avoided waste + avoided exposure*, both countable on real accounts.

### 3.4 CRO / Risk Head — *"Can this increase recovery without increasing customer risk?"*
- **Objection:** "Every extra contact is a complaint waiting to happen."
- **Answer:** the system *reduces* contact volume on low-yield accounts and hard-blocks disclosure-capable actions below an identity threshold.
- **Unresolved:** borrower-experience metrics (NPS, complaint rate) aren't in the sandbox.
- **Changed:** made complaint-risk a **guardrail metric** with a hard ceiling, not a soft target.

### 3.5 Compliance Officer — *"Can this accidentally disclose debt to a wrong party?"*
- **Objection:** "You will be judged on what your system prevented."
- **Answer:** debt-disclosing actions are **not in the candidate set** unless P(right party) ≥ τ; non-verifiable points can only receive a no-disclosure script; notices are gated on address confidence; grievance-hold and sensitive-occasion suppression are hard filters; every refusal is logged with the rule that fired.
- **Unresolved:** DPDP erasure vs the mandated 6-month recording retention.
- **Changed:** added the **notice-confidence gate** and the **grievance/bereavement suppression state** to the architecture; added DPDP-aware retention rules.

### 3.6 Data Science Head — *"Can I trust the labels and evaluate the model?"*
- **Objection:** "You are learning your own dialer's behaviour."
- **Answer:** labels are tiered (payment > agent-confirmed > inferred), never-tested contacts are censored not negative, propensities are logged, and field-visit outcomes are policy-independent-ish evidence.
- **Unresolved:** no randomised holdout in the sandbox → no honest uplift estimate.
- **Changed:** removed uplift/Qini from the MVP claims; evaluation is temporal-split, calibration + decision-regret, with explicit limitations.

### 3.7 CTO — *"Can this integrate into our existing systems?"*
- **Objection:** "We have 20 modules and an API-first stack. Don't hand me a new platform."
- **Answer:** two endpoints (`/eligibility`, `/address-confidence`), a decision-record table, and a config service — it is designed to sit *behind* Maestro.
- **Unresolved:** whether the sandbox exposes the telephony/label fields we need.
- **Changed:** every interface is specified as a contract in the two architecture files.

### 3.8 Product Manager — *"Why ship this instead of improving the existing platform?"*
- **Objection:** "Which of our 20 modules does this replace?"
- **Answer:** none — it upgrades three of them (allocation, field ops, compliance) from *claimed* to *provable*, and it is the only one addressing the Oct-2026 RBI conduct provisions.
- **Unresolved:** internal build-vs-buy; CN could build it.
- **Changed:** positioned explicitly as a **reference implementation + specification** they could absorb.

### 3.9 Bank/NBFC Customer — *"Why should I pay for this?"*
- **Objection:** "I already pay for a collections platform and for agencies."
- **Answer:** it reduces the two things they are personally exposed to: regulator/ombudsman complaints and wasted field/trace spend — and it makes their own RBI inspection cheaper.
- **Unresolved:** proven savings without a pilot.
- **Changed:** added an explicit **30-day pilot design** with pre-agreed counters.

### 3.10 Hackathon Judge — *"Why is this better than 50 other AI collection projects?"*
- **Objection:** "Everyone will build a churn-style risk model and a dashboard."
- **Answer:** we do not claim a better model. We show a **refusal**: the system blocks a legally-required notice because the address is not good enough, then unblocks it after verifying evidence arrives. Almost nobody will build the negative path.
- **Unresolved:** judges may prefer a flashier accuracy number.
- **Changed:** the demo's centre of gravity is the blocked action + the evidence that unblocks it, in under 3 minutes, offline-capable.

### 3.11 Data Protection Officer (added) — *"What is the lawful basis for enrichment and profiling?"*
- **Objection:** purchased contact data + automated profiling + retention is a DPDP problem, not just a technical one.
- **Answer:** purpose-limited processing under the recovery legal basis, no unnecessary data to agents, DPIA-style documentation, erasure workflow that respects statutory retention, and no *new* data purchase in the MVP.
- **Unresolved:** whether the sandbox data is consent-clean for a demo.
- **Changed:** MVP uses only data types CN already holds; every enrichment step is optional and switchable.

### 3.12 The Field Agent (added) — *"What's in it for me?"*
- **Objection:** "If my check-in is used to grade me, I'll game it."
- **Answer:** the integrity model is deliberately **soft-weighted, not punitive**, and the app gives the agent landmark directions, a radius instead of a false-precision pin, and a no-disclosure script that protects *them* personally from a complaint.
- **Unresolved:** any integrity model creates a gaming incentive; must be paired with field-ops policy, not just code.
- **Changed:** integrity output ships as a **credibility weight + widening radius**, explicitly not as an agent-fraud accusation.

---

## 4. The gaps that survive all of this

| Gap | Why it survives the market scan |
|---|---|
| **A notice/visit gated on address confidence** | Every competitor discloses and geotags *after* the decision; nobody gates the decision on confidence |
| **An identity gate that removes the disclosure-capable action from the candidate set** | Competitors assert compliance via scripts and logs; RBI 2026 explicitly rejects "we trained them" as evidence |
| **Integrity-weighted field evidence** | Field apps capture geo-tagged "proof" (`[PUB]` Mobicule), which is exactly the wrong frame if the proof can be manufactured |
| **Contact-point-level, censoring-aware scoring with a rules floor** | TransUnion/Spocto productise account-level contactability; contact-point slates remain unmodelled |
| **A priced trace decision** | SkipTracer.in and TruLookup sell tracing; nobody publishes per-account EVSI gating |
| **Decision-level auditability** | CN claims immutable audit trails; a *decision record with the constraint that blocked the action* is a different artefact |
