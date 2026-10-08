# PS2 — ASSUMPTION REGISTER & PROBLEM RE-READ

**Problem statement 2:** *Right-Party Contact (RPC) prediction & skip-trace prioritisation — predict P(RPC) per phone/address, then choose the next action (continue trying / switch contact point / switch channel / trigger skip-trace / prioritise field visit). Skip-trace must not fire on a fixed attempt count; it must be driven by expected recovery from finding a valid contact point vs. the cost of tracing.*

**Classification tags used throughout**
- `[PS]` — stated in the CreditNirvana problem statement
- `[EXT]` — supported by external research, with source
- `[INFER]` — our inference, not stated anywhere
- `[UNVERIFIED]` — plausible but unconfirmed; must be confirmed with CN before it can carry weight

---

## 1. The eleven questions

### 1.1 What is the exact user/customer?
| Layer | Who | Tag |
|---|---|---|
| Paying customer | The lender: bank / NBFC / fintech / ARC that buys collections software | `[PS]` |
| Primary operational user of the *output* | The **allocation & strategy analyst / collections manager** who decides tonight's working list | `[INFER]` |
| Secondary consumer | **Dialer / campaign orchestrator** (machine consumer, no UI) | `[INFER]` |
| Exception consumer | **Floor supervisor** handling accounts the system refuses to auto-touch | `[INFER]` |
| Downstream affected | Tele-caller, field agent, and — most importantly — **the borrower**, who is the subject, not the user | `[PS]` implies |

**Assumption to challenge:** we previously designed for an "agent console". The evidence says the primary buyer-visible artefact is a **strategy/allocation output plus an exception queue**, not an agent-facing dashboard. Agents act through CN's existing app/console.

### 1.2 Who actually uses the output?
`[INFER]` Nightly batch allocation to (a) automated voice/WhatsApp/SMS, (b) human tele-calling queues, (c) field visit lists, (d) trace vendor requests. A human looks at the *exceptions*, not the whole book.

### 1.3 What decision are they making?
`[PS]` For each contact point: continue trying / switch contact point / switch channel / trigger skip-trace / prioritise field visit.
`[INFER]` The decision has **three layers** the problem statement compresses into one:
1. **Eligibility** — may we contact this person at all, on this channel, now? (regulatory)
2. **Targeting** — which point/channel/time?
3. **Intensity** — how many attempts, and when do we stop?

### 1.4 What does "success" mean operationally?
`[INFER]` Ranked by what an Indian collections head is actually measured on:
1. **Cure/roll-back rate** in early buckets (bucket-1 resolution is the P&L lever — TransUnion CIBIL reports only **7–22%** of 31–60 DPD accounts cured in a quarter `[EXT]`)
2. **Cost per rupee recovered** and cost per RPC
3. **Field-slot yield** (successful visits / slots spent)
4. **Zero conduct events** (complaints, penalties, agency blacklisting)
5. Not "AUC". Not "RPC rate in isolation".

### 1.5 What does CN actually gain?
`[INFER]` Three things, in order of defensibility:
1. **Avoided waste** on the only actions with material unit cost (human call ₹33–44/RPC, field visit ₹220–370, trace ₹60–150 `[EXT]`/`[MODEL]`)
2. **Avoided conduct exposure** — FY24 RBI Ombudsman logged **85,281** loan/recovery complaints, **+42.7% YoY**, ≈29% of all complaints; RB-IOS 2026 raised the harassment compensation cap to **₹3 lakh**; Bajaj Finance was fined **₹2.5 crore** for agent conduct `[EXT]`
3. A **control layer** that makes CN's existing Maestro claims (`RBI compliant`, `immutable audit trails`) *verifiable per decision* rather than asserted `[EXT]`

### 1.6 What could go wrong?
| Failure | Mechanism | Tag |
|---|---|---|
| Wrong-party disclosure | Model says 0.91 right-party; it is the borrower's neighbour | `[PS]` |
| Harassment-by-optimisation | "Excessive calls" is a named prohibited practice; a model maximising contact can produce it | `[EXT]` |
| Feedback loop | We only learn from what we dial; the policy creates its own labels | `[INFER]` |
| Recycling cascade | Number reassigned; every subsequent call is a third-party contact | `[PS]` |
| Exploration harm | Randomised actions hit real people | `[INFER]` |
| Silent segment failure | Model good on average, worse in tier-3 / vernacular / thin-file | `[INFER]` |
| Address–identity leakage | Contacting a *guarantor* or relative is prohibited for non-borrower relatives `[EXT]` | `[EXT]` |

### 1.7 What constraints are mandatory?
| Constraint | Source | Status |
|---|---|---|
| Contact only **08:00–19:00** unless the borrower expressly authorises otherwise | RBI recovery-conduct framework (final, effective **1 Jan 2027**; drafts proposed 1 Jul / 1 Oct 2026) | `[EXT]` — **changed from the 2022 circular we previously cited** |
| Interact only with **borrower or guarantor**; no relatives/contacts | RBI framework | `[EXT]` |
| Calls **recorded and retained ≥6 months** (longer if litigated); borrower informed | RBI framework | `[EXT]` |
| No contact during bereavement / medical emergency / communicated hardship; suppression + cooling-off required | RBI framework | `[EXT]` |
| **Grievance pending ⇒ no recovery action/assignment** | RBI framework | `[EXT]` |
| Only **minimum-necessary** data to agents (employer/workplace explicitly not shareable) | RBI framework | `[EXT]` |
| No harassment, intimidation, social-media shaming, excessive or anonymous calls | RBI framework | `[EXT]` |
| Recovery agents **IIBF-certified**; agency list publicly disclosed and updated within 7 days | RBI framework | `[EXT]` |
| **≥1 day advance SMS/email notice** before first in-person visit (3 days by letter if no digital contact) | RBI framework | `[EXT]` |
| A2P/robocall **pre-declaration**; 140xx/1600xx series protected from spam-tagging; 3-complaint threshold; ≤5 paise/min charge on undeclared calls | TRAI TCCCPR Third Amendment, 18 Sep 2026 | `[EXT]` |
| Consent + purpose limitation + accuracy + erasure; full obligations ~**13–14 May 2027** | DPDP Rules 2025 (G.S.R. 846(E), 13/14 Nov 2025) | `[EXT]` |

> **This table is the single biggest correction to our first deliverable.** We built the compliance design on the August-2022 RBI circular. The regime that matters now is the 2026 framework — and two of its provisions (advance notice before a visit; borrower/guarantor-only interaction) change the *architecture*, not just the copy.

### 1.8 What data is required?
`[PS]`-listed signals: attempts, timestamps, time of day, ring duration, answer/hangup, network responses, prior RPC events, time since last RPC, agent dispositions/remarks, voice-bot transcripts, shared contact points across accounts, source & age of contact info, prior field-visit outcomes, GPS/dwell, account & recovery characteristics.
`[UNVERIFIED]` Whether CN's sandbox actually exposes: **(a)** per-attempt telephony telemetry (ring duration, cause codes), **(b)** propensity/logged policy of the incumbent, **(c)** inbound-call events (the highest-quality contact label), **(d)** per-action unit costs. Without (a) and (d), half this design degrades to rules.
`[EXT]` Purchasable augmentation: HLR/carrier/ported status at **$0.0015–$0.04 per lookup** (Telnyx / Neutrino / Twilio) — cheap enough to run on a whole book, but subject to DPDP purpose limits.

### 1.9 Explicitly required vs merely suggested
| Element | Status |
|---|---|
| Score **each phone/address** (contact-point level) | **Required** `[PS]` |
| Recommend the **best next action** | **Required** `[PS]` |
| Skip-trace driven by **expected recovery vs cost** | **Required** `[PS]` |
| **Explainable and auditable** decisions | **Required** `[PS]` |
| Prevent **third-party debt disclosure** | **Required** `[PS]` |
| Three-factor decomposition (Answer × RightParty × Productive) | Our inference `[INFER]` |
| Survival/hazard modelling, graphs, calibration layers, conformal radii, bandit exploration | Our inference `[INFER]` |
| Specific architectures (LightGBM, H3, LambdaMART) | Our inference `[INFER]` |

### 1.10 What is our own assumption?
Everything in the two `[INFER]` rows above, plus: that CN wants a *new module* (they may want a *reference design*), that their field data is usable for training (PS3), that the sandbox has labels, and that judges reward technical breadth (evidence says they reward a single undeniable demonstration).

### 1.11 Does this contradict something we previously claimed?
Yes — four things, documented as rejected assumptions in `PS2_PS3_RED_TEAM.md`: (i) that *exploration* can be bought with extra attempts; (ii) that *graph/reference contacts* can be contacted; (iii) that *dial-volume optimisation* is a value pool; (iv) that **PS2** is where the differentiation is.

---

## 2. Assumption register

### Product & user
| # | Assumption | Tag |
|---|---|---|
| A1 | Output is consumed by an allocation/strategy function and machine orchestration, not primarily by agents | `[INFER]` |
| A2 | The buyer cares more about avoided conduct exposure than about a marginal RPC gain | `[INFER]` — **test in persona review** |
| A3 | CN wants a module inside Maestro rather than a competing platform | `[INFER]` |
| A4 | "Do nothing / wait" is an acceptable recommendation to a collections manager | `[UNVERIFIED]` — behavioural, must be tested |
| A5 | A refusal (blocked action) is as valuable to demo as a recommendation | `[INFER]` |

### Economics
| # | Assumption | Tag |
|---|---|---|
| A6 | Field visit unit cost ₹220 marginal / ₹370 standalone | `[MODEL]` from `[EXT]` salary data + assumptions |
| A7 | Trace ₹60–150 per case in India | `[EXT]`-anchored (global bulk $5–25; US one-off $50–175) |
| A8 | Human call ₹33–44 per RPC; automated dial ₹1.35–2.6 | `[MODEL]` from `[EXT]` |
| A9 | Incremental recovery per extra RPC ≈ ₹205 at an ₹18.8k ticket | `[ASSUME]` — **the most consequential assumption in the model** |
| A10 | 15–25% of 1–30 DPD accounts self-cure | `[EXT]` vendor-published `[vendor]` |
| A11 | Field visits matter little at <₹50k unsecured tickets unless marginal to a beat | `[MODEL]` |

### ML / data
| # | Assumption | Tag |
|---|---|---|
| A12 | Attempt-level telephony telemetry exists in the sandbox | `[UNVERIFIED]` |
| A13 | RPC labels can be verified at ≥3 confidence tiers (payment / agent-confirmed / inferred) | `[INFER]` |
| A14 | Never-tested contact points are a large share of the book | `[UNVERIFIED]` |
| A15 | Recycled-number detection is feasible from ≥90-day silence + discontinuity | `[EXT]` — TRAI mandates a ≥90-day gap before reallocation `[EXT]` |
| A16 | Graph features add lift beyond hand-built shared-contact counts | `[UNVERIFIED]` — must be measured, not assumed |
| A17 | Sequence/GNN models are not needed for the MVP | `[INFER]` |

### Compliance
| # | Assumption | Tag |
|---|---|---|
| A18 | A modelled P(right party) is the correct gate for debt-disclosing actions | `[PS]` implies |
| A19 | Logging alone does not constitute compliance | `[EXT]` — RBI framework judges whether **systems permitted** a violation |
| A20 | The 1-day pre-visit notice must be gated by **address confidence**, not just scheduled | `[INFER]` — **this is our sharpest novel compliance insight** |
| A21 | Non-borrower contact points may be used as *features* but not as *contact targets* | `[EXT]` |
| A22 | DPDP erasure/purpose duties interact with 6-month call-recording retention | `[EXT]` — unresolved tension; needs legal input |

### Competition
| # | Assumption | Tag |
|---|---|---|
| A23 | Contact intelligence (who to call, which number, when) is a mature market | `[EXT]` — TransUnion PBI claims +33% RPC; Spocto contactability; SkipTracer.in |
| A24 | CN's own platform already performs allocation and outreach | `[EXT]` — CN Maestro: allocation 24h→30 min, 150+ agents, 20 modules |
| A25 | Our differentiation must therefore be narrower than "RPC prediction" | `[INFER]` — **central conclusion** |
