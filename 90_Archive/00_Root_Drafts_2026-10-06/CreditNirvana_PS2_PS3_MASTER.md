# CreditNirvana — PS2 + PS3

## Complete deliverable: second-stage research, red team, and the solution we would build

**One-line thesis.** The two problem statements are not about better prediction. They are about **permission** — deciding what a collections platform is allowed to *do* with a prediction. We build a permission layer for the two irreversible actions: **a disclosure-capable contact against an unverified identity** (PS2 → **SANKET**) and **a legally-required notice or visit at an unverified address** (PS3 → **SUTRA**).

**How to read this file.** Part I is the whole answer in 20 numbered conclusions — if you read nothing else, read that. Parts II–XIII are the working artifacts, in the order the work was done (assumptions → market → red team → architectures → novelty → money → data → questions → execution). Appendix A is the Phase-1 baseline research, retained as the research record and explicitly superseded as *design*. Appendix B is the model's raw output; Appendix C lists the companion files.

**Honesty rules applied throughout — please hold us to them:** no invented facts; every number is tagged `[PUB]` (published/claimed by a vendor), `[EXT]` (external data point), `[ASSUME]` (ours) or `[MODEL]` (computed); synthetic data is labelled wherever it appears and is never presented as measured performance; no claim of a market gap without a named competitor; no claim of compliance merely because a log exists; no advanced model without a simpler baseline it had to beat.

---

# Part I. Final conclusions — the 20 items

## 1. What was wrong with the previous solution

The Phase-1 design was **twelve models, three dashboards, and a compliance story resting on logging**. Attacked as a collections head, a CFO and a regulator, five flaws survived:

1. **It optimised the wrong cost.** Dial volume sits at the cheap end of a **185× cost spread** (₹1.35–2.60 automated dial → ₹220–370 field visit `[MODEL]`). A perfect dial model is worth ₹2,700–25,900/month. A mediocre field/identity gate is worth lakhs.
2. **Survival modelling was oversold** — worth ~₹94,000/month per pp of field-slot success: a *timing sub-component*, not an architecture.
3. **Novelty was claimed where vendors already ship** — contactability (TransUnion PBI claims +33% RPC), geo-tagged field apps (Mobicule, Credgenics), outcome-learning addresses (Shiprocket: 72.69% <100 m), error radii (Delhivery GeoNaksha) `[PUB]`.
4. **It would have fought CreditNirvana's own Maestro layer** for the single most valuable lever in the model — P(pay | RPC) at ₹7.37 lakh/month per pp `[MODEL]` — a fight we lose and should not start.
5. **The PS2+PS3 combination was asserted, not proven.** Two products in one demo with no causal reason to fuse them.

## 2. Research that changed our thinking

- **CreditNirvana is not an agency with software; it is agentic-AI-native** — 20 modules, 150+ GenAI agents, 62M+ accounts, Maestro (field + legal lifecycle) since Nov 2025, 32% field-efficiency claim `[PUB]`. Anything we build must sit **inside** Maestro's decision, not beside it.
- **Perfios owns CN and the adjacent rails** (Karza KYC, Clari5 fraud, IHX) — identity plumbing is an internal capability, not a gap to sell into.
- **Address intelligence is commoditised** — Shiprocket learns from delivery outcomes; Delhivery returns error radii over 4B+ deliveries; Google classifies residential vs commercial in India `[PUB]`. "We learn addresses from field visits" is no longer novel by itself.
- **Contactability is commoditised** — TransUnion PBI, Spocto YuCI, every dialer vendor's timing claim `[PUB]`.
- **The white space is permission, and a rule created it.** The RBI recovery framework — **final, effective 1 January 2027** — requires **≥1 day advance notice before the first visit** (3 days by letter), contact only with borrower/guarantor, 08:00–19:00, suppression on hardship or open grievance, ≥6-month recordings, board-approved policy `[EXT]`. RBI judges whether the **system permitted** the violation, so logging is not compliance. Add the ₹3,00,000 harassment-compensation cap and the ₹2.5 crore lender penalty precedent `[PUB]`.
- **The economics are ticket-conditional** — field-visit ROI is 0.65× at a ₹5,000 ticket, 2.43× at ₹18,802, 104× at ₹8 lakh `[MODEL]` — which forces a segment-conditional product instead of one global policy.

## 3. Assumptions kept, rejected, and still unverified

**Kept:** the two problem statements are worth combining *only* through the notice/visit loop; every advanced component must beat a simpler baseline; no synthetic result presented as measured.
**Rejected:** PS2 as the spine (the expensive action is the spine, not the prediction); survival as an architecture; graph features on the critical path; bandits before a randomised holdout; uplift/causal claims without randomisation; conformal coverage as a headline; building our own geocoder; an LLM in the decision path.
**Unverified and labelled as such everywhere:** whether any vendor learns a geocoded **location distribution** from its own field-visit outcomes (phrased *unproven*, never *non-existent*); whether CN captures visit-level GPS historically; exactly what sandbox tables and API docs a hackathon team receives.

## 4. The best PS2 formulation

| Formulation | Data need | Complexity | Explainability | Value | Hackathon fit | Production fit | Novelty | Failure mode | **Total /40** |
|---|---|---|---|---|---|---|---|---|---|
| A. Contact-point ranking (slate LTR) | Med | Med | Med | Med | 5 | 4 | 3 | ranks a point that must never be contacted | 25 |
| B. Latent-state / HMM | High | High | Low | Med | 2 | 3 | 4 | unidentifiable states | 21 |
| C. Hazard / survival | Med | Med | Med | Med | 4 | 5 | 3 | censoring sensitivity; no identity | 25 |
| D. Contextual bandit | High | High | Low | High? | 2 | 3 | 4 | exploration harms real people | 16 |
| E. Decision-centric EV + abstention | Low | Low | **5** | **5** | **5** | 5 | 4 | costs must be defended | **34** |
| F. Causal / uplift | Very high | High | Med | High? | 1 | 3 | 5 | unidentifiable without randomisation | 15 |
| G. Graph identity | High | High | Low | Med | 2 | 4 | 4 | regulatory limits on non-borrower contact | 20 |
| **H. Hybrid: rules floor + one calibrated contact-point scorer + EV gate** | Med | Low | **5** | **5** | **5** | **5** | 3 | rule drift; needs governance | **34** |

**Winner: H ⊕ E (34/40).** A deterministic compliance floor that can veto; **one** calibrated contact-point model (never account-level); an EV gate with an explicit **`wait`** action; tiered labels with inverse-propensity weighting, because we only ever observe what the incumbent policy chose to attempt. Everything else is v2, gated on a measured lift test.

## 5. The best PS3 architecture

| Architecture | Data need | Complexity | Explainability | Value | Hackathon fit | Production fit | Novelty | Failure mode | **Total /40** |
|---|---|---|---|---|---|---|---|---|---|
| A. Commercial geocoder + post-processing | Low | Very low | High | Low | 4 | 5 | 1 | commodity | 22 |
| B. Parse → normalise → geocode | Med | Med | High | Low–Med | 4 | 4 | 2 | parsing is *not* the bottleneck | 22 |
| C. Multi-candidate + LTR ranker | Med | Med–High | Med | Med | 3 | 4 | 3 | candidates usually agree | 24 |
| D. Belief model + Bayesian fusion of visit evidence | Med | Med | Med–High | High | 4 | 4 | **5** | weak priors | 32 |
| E. D + robust estimator + empirical radius | Med | Med | High | High | **5** | 4 | 4 | radius quality at small n | 30 |
| F. End-to-end LLM / geospatial foundation model | Very high | Very high | Low | Uncertain | 1 | 2 | 3 | no calibration, cost, licensing | 12 |
| G. Visit evidence only (no geocoder) | High | Med | High | Med | 2 | 2 | 4 | cold start | 18 |
| **H. Runtime commercial geocoder + recovery-visit evidence fusion + integrity weight + purpose classification + empirical radius + notice gate** | Med | Med | **5** | **5** | **5** | 5 | 4 | requires visits to exist in the segment | **34** |

**Winner: H (34/40).** Parsing is not the bottleneck. Candidate generation is not the bottleneck. **GPS integrity and the permission decision are.** The integrity weight `w ∈ [0.2, 1.0]` is what makes field evidence trustworthy: a low-`w` observation moves the belief *less* and widens the radius *more*. Commercial geocoder output is consumed **at runtime and never cached as training data**.

## 6. Combine, or not

| Option | Judging clarity | Impl. risk | Demo strength | Novelty | Business value | Data need | Effort | **Total /35** |
|---|---|---|---|---|---|---|---|---|
| 1. PS2 alone | 4 | **5** | 3 | 2 | 4 | Med | Low | 23 |
| 2. PS3 alone | 4 | 3 | **5** | 4 | 3 | High | Med | 24 |
| **3. PS2 + PS3 tightly integrated — one loop, one decision** | **5** | 3 | **5** | **5** | **5** | High | Med–High | **31** |
| 4. Loose integration (two demos, shared UI) | 3 | 4 | 3 | 3 | 4 | High | Med | 24 |
| 5. PS2 core + PS3 as an uncertainty module | 4 | 4 | 4 | 4 | 4 | Med | Med | 27 |
| 6. PS3 core + PS2 as the decision layer | **5** | 3 | 4 | **5** | 4 | Med–High | Med | 29 |

**Combine — but only through one causal chain, and only for the expensive action.** A legally-required notice or visit costs money and is irreversible, so it needs both an identity judgement (whose phone, whose door) and a location judgement — and the field visit is the only thing that improves the location judgement. Everything else stays separate. At an ₹18,802 ticket the address component is thin (2.43× marginal ROI); the identity gate applies to **every** portfolio, including pure automated digital.

## 7. The exact product

**SANKET (PS2) = permission to contact. SUTRA (PS3) = permission to serve.** Together: the layer between prediction and action.

- **User:** the collections/field allocation owner and the compliance officer — not the tele-caller, not a new analyst.
- **Painful decision:** *do I spend ₹220–370 and an irreversible legal step on this account, at this address, with this number?*
- **Input:** contact slate + dispositions + incumbent-policy logs; address record + runtime geocode candidates + field check-in evidence.
- **Intelligence:** calibrated P(right party) and P(connect) per contact point; `conf_address` with `radius_90` by stratum; integrity weight per observation; purpose class (home/work/shop); EVSI for traces.
- **Decision:** `ALLOW` / `BLOCK` / `WAIT`, with the rule that fired. Disclosure-capable actions are **removed from the candidate set**, not merely down-ranked.
- **Action:** allocation deltas, suppression list, notice release/hold, trace order, verification task.
- **Feedback:** visit outcome, notice outcome, contact outcome, complaint → address evidence and recalibration.
- **Economics:** avoided waste on expensive actions + avoided conduct exposure. Never gross recovery uplift.
- **Compliance:** the constraint that permitted or blocked the action sits in the same immutable record as the action.
- **Workflow:** one loop — allocate → gate → act → record → learn.

## 8. Why it wins — the board's verdict and the changes it forced

| Persona | Verdict |
|---|---|
| **Collections Head** | "Useful only as allocation deltas + an exception queue, inside my workflow." → accepted: no new dashboard |
| **Field Ops Head** | "Reduces failed visits and wasted travel." → beat plans consume `conf_address` |
| **CFO** | "The money is avoided waste and avoided exposure; the offer layer is bigger and it isn't yours." → accepted, and said out loud |
| **CRO / Risk** | "Does recovery fall when you suppress?" → suppression is segment-conditional; measured in the pilot |
| **Compliance Officer** | "Can it disclose debt to a third party?" → the identity gate makes it structurally impossible |
| **Data Science Head** | "Are the labels valid; can you evaluate it?" → tiered labels, propensity weighting, abstention, and an explicit list of what cannot be concluded |
| **CTO** | "Integrate or replace?" → two services, three endpoints, one schema; runs inside Maestro |
| **PM** | "Why this rather than more of the platform?" → because the regulator now judges the *system*, not the agent |
| **Bank / NBFC customer** | "Why pay?" → ₹1–3 per account needs only +0.2–1.0 pp of connect, or 455–2,273 avoided visits |
| **Judge** | "Why not the other 50 AI-collections projects?" → because ours refuses to act, and can prove why |
| **DPO** (added) | "Lawful basis for enrichment and profiling?" → separate purposes, minimum-necessary, no cached geocoder data, aggregate-only artefacts |
| **Field Agent** (added) | "What's in it for me?" → fewer wasted trips and a defensible record; without a benefit the evidence quality collapses |

**Modifications forced by the board:** drop two of three planned UIs; make the visit gate a **hard block** but the notice gate advisory-with-alternative (to avoid breaching notice SLAs); expose an override with a reason code from day one; add the DPO and field-agent personas, both of which changed the design.

## 9. Competitor threats

| Threat | Reality | Our answer |
|---|---|---|
| **CN / Maestro already does this** | Maestro owns offer, negotiation, routing and the legal workflow `[PUB]` | We are not another predictor; we are the permission decision Maestro consumes. Complementary, not competitive |
| TransUnion PBI, Spocto, Credgenics, Mobicule, Skit, Gnani | Better data, more signals, existing integrations | Compete on *what the output is allowed to authorise*, and on field-outcome evidence |
| Shiprocket / Delhivery address AI | Better at delivery distances, far more volume | Different object: **recovery-visit** evidence under an integrity constraint, coupled to a legal gate they have no reason to build |
| Skip-trace vendors | Cheap, fast, India-ready | We don't sell tracing; we price it (EVSI) |
| **CN builds it in-house** (the most likely real competitor) | They have the data and the platform | The moat is the **field-outcome evidence loop + the permission record inside the collections workflow** — not the model |

## 10. Differentiation — the honest novelty statement

> We are not claiming a better geocoder or a better RPC model — both are mature markets with strong incumbents. We claim the **first permission layer between prediction and action in Indian collections**: a debt-disclosing action is not in the candidate set unless identity is verified to a modelled threshold, and a notice or visit is not generated unless address confidence clears a threshold — and both refusals are recorded, with the rule that caused them, in the same record that proves the action was allowed. The field evidence that lifts those refusals is integrity-weighted, so a fake check-in cannot teach the system the wrong door.

Ranked novelty (weighted for compliance, data moat and demonstrability): **N1 confidence-gated notice/visit (4.6/5) · N2 identity-gated eligibility (4.4) · N3 integrity-weighted evidence that widens instead of shifting (3.8) · N4 contact-point slates with censoring (3.2) · N5 priced trace (3.0 — real, required, and easiest to copy)**.

**Rejected novelty claims** (research killed them): "an address engine that learns from field outcomes" (Shiprocket); "calibrated uncertainty from a geocoder" (Delhivery error radius); "residential vs commercial" (Google Address Validation India); "predicting which number is right, and when to call" (TransUnion PBI, Spocto); "GPS for routing" (Mobicule, Credgenics).

## 11. The ROI story — ranges with mechanisms, never point facts

| Pool | Monthly, 100k accounts at an ₹18,802 ticket | Tag |
|---|---|---|
| Field-slot success (+10–45 pp) | **₹9.4–42.4 lakh** | `[MODEL]` |
| Human-agent conversations (+5–12 pp RPC) | ₹3.4–14.7 lakh | `[MODEL]` |
| Wasted field slots (10–35% of slots) | ₹1.5–8.6 lakh | `[MODEL]` |
| Conduct exposure avoided | ₹3–75 lakh expected, plus a lumpy penalty class (₹2.5 Cr precedent) | `[MODEL]` / `[PUB]` |
| *Dial-volume optimisation* — listed **to be ignored** | *₹2,700–25,900* | `[MODEL]` |

Incremental recovery per RPC ≈ **₹205** (gross ₹1,183 × 0.20–0.35 incrementality) — gross is quoted nowhere, because citing it overstates value ~3.6×. **Break-even:** at ₹1/account/month the product needs **+0.20 pp of connect or ~455 avoided visits**; at ₹3, +0.60 pp or ~1,364 visits; at ₹5, +1.00 pp or ~2,273 visits. **Single biggest assumption:** incremental versus gross recovery (Q3 for CN). **Biggest lever overall:** P(pay | RPC) at ₹7.37 lakh/pp — **owned by Maestro; we do not claim it.**

## 12. The compliance story

Not "we have an audit log". The claim is architectural and demonstrable: **disclosure-capable actions are structurally absent from the candidate set without identity confidence, and notices and visits are structurally absent without address confidence** — shown live, with the blocking rule visible on screen. Anchored to the RBI recovery framework (effective **1 Jan 2027**: 08:00–19:00, borrower/guarantor only, ≥1-day advance notice before the first visit and 3 days by letter, hardship and open-grievance suppression, ≥6-month recordings, board policy, IIBF-certified agents) `[EXT]`; DPDP Rules 2025 with fiduciary duties commencing ~May 2027 — **phased, not in force** `[EXT]`; TRAI A2P rules `[EXT]`. Plus purpose classification that prevents serving a notice at a workplace, overrides that require a reason code, and a versioned ledger exportable for a regulator. **What we do not claim:** compliance from logs alone, or consent coverage we have not verified.

## 13. The 2–3 minute demo

- **0:00–0:40 — Refusal.** A ₹42,300 / 46-DPD account, address confidence **0.41**, radius **1,400 m**. The notice does not exist. Two rules fire: `ADDR_CONF_LOW`, `NOTICE_PRECHECK`.
- **0:40–1:35 — Release.** A field check-in: landmark matched, dwell 6 minutes, door photo matched, `w = 0.95` → confidence **0.78**, radius **90 m** → notice and visit released. The ledger shows evidence, weight and rule.
- **1:35–2:05 — Identity gate.** Two accounts with **identical connect probability (0.31)** and different P(right party) (0.36 vs 0.88): one may receive a debt-disclosing call, the other only a challenge script.
- **2:05–2:40 — Poisoning.** A fake check-in 6.1 km away is neither rejected nor believed: `w = 0.20`, belief **0.79 unchanged**, radius **90 m → 520 m**, visit refused. *Fraud can cost us precision; it cannot teach us the wrong door.*
- **Close (20 s).** The counterfactual: three wasted visits and one mis-served notice avoided — labelled **synthetic**.

The clickable prop is `SANKET_SUTRA_DEMO.html` (synthetic data, marked on screen).

## 14. The 48-hour MVP — and the data strategy

**In:** address-confidence gate · integrity weight · empirical radius by stratum · notices/visits API with `ALLOW`/`BLOCK`/`WIDEN` · field evidence ingest · identity gate · permission ledger · trace EV gate · one console · rules-based timing. **Out:** graph identity, bandits, uplift, own geocoder, LTR ranker, sequence models, routing solver, extra dashboards. The hour-by-hour build plan is in Part XIII, including the rule that **if a demo beat cannot be produced, it is cut rather than narrated**.

**Data strategy A/B/C/D** (per-feature table in Part XI). **A — CN-provided:** point-level dispositions, identity-verified events, payment/cure labels, incumbent-policy attempt logs, visit GPS, notice outcomes. **B — public/licensable:** runtime geocoder, HLR dips, OSM for landmark typing, RBI/CIBIL aggregates for sanity checks only (never Bhuvan/ISRO). **C — synthetic:** the demo book, labelled `SYNTHETIC` in the UI, the payload and the deck. **D — must-not-fabricate:** visit GPS history, incumbent-policy propensity, radius containment, trace outcomes, wrong-party rates — **without these we abstain or re-scope; we do not simulate a result.** The minimal ask is exactly two datasets: **visit-level GPS + outcome**, and **point-level dispositions with policy attempts**.

## 15. Competition-final scope

1. Shadow-mode counterfactual over 2–4 weeks of real cases. 2. Timing model — *only if* it beats the hour-of-day baseline on a held-out window. 3. Radius recalibrated on real field outcomes. 4. Integrity v2 (device, route plausibility, door-plate OCR). 5. Regulator-exportable ledger. 6. **One** end-to-end integration (notice generation → gate), logged with its counterfactual.

## 16. Production roadmap, with kill criteria

P0 shadow (months 0–1; gate: ≥70% of visits carry GPS, geocoder licence permits runtime use) → P1 notice/visit gate live in one bucket (2–3; gate: zero unlogged suppressions, override rate <15%) → P2 identity gate and point-level modelling (3–6) → P3 learning loop recalibrated on real field outcomes (6–9) → P4 second portfolio with ticket-conditional policies (9–12).
**Kill criteria, pre-registered:** if measured wrong-party contacts do not fall, or wasted visits do not fall by ≥5 pp, or overrides exceed 25% — stop and re-scope rather than iterate.

## 17. Top risks and failure scenarios

**Top 10 of 20 risks:** (1) CN has no historical visit-level GPS → SUTRA loses its learner; (2) no point-level dispositions → SANKET cannot claim lift; (3) incremental recovery unknown → ROI unfalsifiable; (4) geocoder licence forbids even runtime retention of coordinates; (5) judges read the gate as "just a threshold"; (6) "why not build it in-house?"; (7) a blocked notice breaches an internal notice SLA; (8) agents are incentivised to fake check-ins; (9) suppression harms genuine recovery in a good account; (10) field visits too rare in the target segment to calibrate radii.

**Sixteen failure scenarios across seven columns** (scenario / naive system / ours / detection / fallback / business impact / compliance impact) — full table in Part VIII §10. Headlines: recycled phone → disclosure avoided · **shared family phone → identity gate forces a challenge script** · borrower moved → address marked stale and fed back to contactability · wrong address → **notice blocked** · agent fakes a check-in → radius widens, belief does not move · workplace encounter → purpose class forbids delivery there · landmark ambiguity and duplicate names across towns → abstain and verify · 12 unanswered attempts → hazard backoff · deliberately avoiding borrower → window/CLI probe inside the planned attempt · third party answers → not in the candidate set · two-year-old successful contact → age-decayed · **model confident and wrong → asymmetry plus reversible-first ordering** · expensive-but-informative visit → priced as an option · low-value account with high trace cost → suppressed · regulation lands mid-month → config version bump freezes disclosure actions.

## 18. Top questions for CreditNirvana

Ranked in Part XII (23 questions across DATA / BUSINESS / COMPLIANCE). The five that decide the architecture: **Q1** portfolio and true ticket band · **Q7** is visit-level GPS (accuracy, dwell, photo) captured historically · **Q3** incremental vs gross recovery · **Q15** how the ≥1-day advance notice is generated today, and from which address field · **Q17** what the audit trail records per action. These five decide which product leads, whether PS3 has a learning loop at all, and whether our ROI claim is credible.

## 19. Final recommendation

**Build SANKET + SUTRA as one permission loop governing only the expensive and irreversible actions.** The MVP is the address-confidence gate + integrity weight + identity gate + permission ledger + one console, running on data labelled synthetic, with shadow-mode counters pre-registered. Lead the pitch with **refusals**, not predictions. Do not touch the offer layer. Do not build a geocoder. Do not ship a bandit. Lead with the segment where the loop pays (larger tickets, field-bearing books) and say plainly where it does not (₹18,802 tickets, thin address value).

## 20. "How would I beat this team?"

| If I were the rival | Why it works | Our answer |
|---|---|---|
| Reduce us to "a threshold with an audit log" | It is one line, and partly true | Concede, then show the widening behaviour and the identity gate — thresholds cannot be poisoned and cannot express *who* an action is permitted for |
| Bring **one real dataset from a real collections floor** | Beats any architecture | The only genuine threat. Counter: ask for exactly that dataset in the room (Q7, Q15) and have shadow mode ready to run |
| "TransUnion / Spocto already do this" | True at the model level | We compete at the permission level, with field-outcome evidence and a regulator-facing record |
| "Shiprocket / Delhivery do addresses" | True | Different object — recovery-visit evidence under an integrity constraint — and a legal gate they have no reason to build |
| "Where is the AI?" | There is no LLM | Answer with what the models actually do, and with the deliberate refusal to put a model where a rule belongs |
| "Too small to matter" | Small tickets, few visits | That is exactly why ROI is computed by ticket band — and why we say out loud that the bigger lever (₹7.37 lakh/pp) is Maestro's, not ours |

**What would beat us is measurement, not cleverness.** So the first action after the pitch is a 30-day shadow pilot with pre-registered counters: cost per RPC · cost per productive RPC · field-slot yield · notices blocked below confidence · traces ordered versus productive · wrong-party contacts · complaints · cure in bucket. If the mechanism demoed here does not move those counters on CN's real data, the honest answer is to stop — not to add another model.


---

# Part II. PS2 — assumption register & problem re-read

*Source file: `PS2_ASSUMPTIONS.md`*

## PS2 — ASSUMPTION REGISTER & PROBLEM RE-READ

**Problem statement 2:** *Right-Party Contact (RPC) prediction & skip-trace prioritisation — predict P(RPC) per phone/address, then choose the next action (continue trying / switch contact point / switch channel / trigger skip-trace / prioritise field visit). Skip-trace must not fire on a fixed attempt count; it must be driven by expected recovery from finding a valid contact point vs. the cost of tracing.*

**Classification tags used throughout**
- `[PS]` — stated in the CreditNirvana problem statement
- `[EXT]` — supported by external research, with source
- `[INFER]` — our inference, not stated anywhere
- `[UNVERIFIED]` — plausible but unconfirmed; must be confirmed with CN before it can carry weight

---

### 1. The eleven questions

#### 1.1 What is the exact user/customer?
| Layer | Who | Tag |
|---|---|---|
| Paying customer | The lender: bank / NBFC / fintech / ARC that buys collections software | `[PS]` |
| Primary operational user of the *output* | The **allocation & strategy analyst / collections manager** who decides tonight's working list | `[INFER]` |
| Secondary consumer | **Dialer / campaign orchestrator** (machine consumer, no UI) | `[INFER]` |
| Exception consumer | **Floor supervisor** handling accounts the system refuses to auto-touch | `[INFER]` |
| Downstream affected | Tele-caller, field agent, and — most importantly — **the borrower**, who is the subject, not the user | `[PS]` implies |

**Assumption to challenge:** we previously designed for an "agent console". The evidence says the primary buyer-visible artefact is a **strategy/allocation output plus an exception queue**, not an agent-facing dashboard. Agents act through CN's existing app/console.

#### 1.2 Who actually uses the output?
`[INFER]` Nightly batch allocation to (a) automated voice/WhatsApp/SMS, (b) human tele-calling queues, (c) field visit lists, (d) trace vendor requests. A human looks at the *exceptions*, not the whole book.

#### 1.3 What decision are they making?
`[PS]` For each contact point: continue trying / switch contact point / switch channel / trigger skip-trace / prioritise field visit.
`[INFER]` The decision has **three layers** the problem statement compresses into one:
1. **Eligibility** — may we contact this person at all, on this channel, now? (regulatory)
2. **Targeting** — which point/channel/time?
3. **Intensity** — how many attempts, and when do we stop?

#### 1.4 What does "success" mean operationally?
`[INFER]` Ranked by what an Indian collections head is actually measured on:
1. **Cure/roll-back rate** in early buckets (bucket-1 resolution is the P&L lever — TransUnion CIBIL reports only **7–22%** of 31–60 DPD accounts cured in a quarter `[EXT]`)
2. **Cost per rupee recovered** and cost per RPC
3. **Field-slot yield** (successful visits / slots spent)
4. **Zero conduct events** (complaints, penalties, agency blacklisting)
5. Not "AUC". Not "RPC rate in isolation".

#### 1.5 What does CN actually gain?
`[INFER]` Three things, in order of defensibility:
1. **Avoided waste** on the only actions with material unit cost (human call ₹33–44/RPC, field visit ₹220–370, trace ₹60–150 `[EXT]`/`[MODEL]`)
2. **Avoided conduct exposure** — FY24 RBI Ombudsman logged **85,281** loan/recovery complaints, **+42.7% YoY**, ≈29% of all complaints; RB-IOS 2026 raised the harassment compensation cap to **₹3 lakh**; Bajaj Finance was fined **₹2.5 crore** for agent conduct `[EXT]`
3. A **control layer** that makes CN's existing Maestro claims (`RBI compliant`, `immutable audit trails`) *verifiable per decision* rather than asserted `[EXT]`

#### 1.6 What could go wrong?
| Failure | Mechanism | Tag |
|---|---|---|
| Wrong-party disclosure | Model says 0.91 right-party; it is the borrower's neighbour | `[PS]` |
| Harassment-by-optimisation | "Excessive calls" is a named prohibited practice; a model maximising contact can produce it | `[EXT]` |
| Feedback loop | We only learn from what we dial; the policy creates its own labels | `[INFER]` |
| Recycling cascade | Number reassigned; every subsequent call is a third-party contact | `[PS]` |
| Exploration harm | Randomised actions hit real people | `[INFER]` |
| Silent segment failure | Model good on average, worse in tier-3 / vernacular / thin-file | `[INFER]` |
| Address–identity leakage | Contacting a *guarantor* or relative is prohibited for non-borrower relatives `[EXT]` | `[EXT]` |

#### 1.7 What constraints are mandatory?
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

#### 1.8 What data is required?
`[PS]`-listed signals: attempts, timestamps, time of day, ring duration, answer/hangup, network responses, prior RPC events, time since last RPC, agent dispositions/remarks, voice-bot transcripts, shared contact points across accounts, source & age of contact info, prior field-visit outcomes, GPS/dwell, account & recovery characteristics.
`[UNVERIFIED]` Whether CN's sandbox actually exposes: **(a)** per-attempt telephony telemetry (ring duration, cause codes), **(b)** propensity/logged policy of the incumbent, **(c)** inbound-call events (the highest-quality contact label), **(d)** per-action unit costs. Without (a) and (d), half this design degrades to rules.
`[EXT]` Purchasable augmentation: HLR/carrier/ported status at **$0.0015–$0.04 per lookup** (Telnyx / Neutrino / Twilio) — cheap enough to run on a whole book, but subject to DPDP purpose limits.

#### 1.9 Explicitly required vs merely suggested
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

#### 1.10 What is our own assumption?
Everything in the two `[INFER]` rows above, plus: that CN wants a *new module* (they may want a *reference design*), that their field data is usable for training (PS3), that the sandbox has labels, and that judges reward technical breadth (evidence says they reward a single undeniable demonstration).

#### 1.11 Does this contradict something we previously claimed?
Yes — four things, documented as rejected assumptions in `PS2_PS3_RED_TEAM.md`: (i) that *exploration* can be bought with extra attempts; (ii) that *graph/reference contacts* can be contacted; (iii) that *dial-volume optimisation* is a value pool; (iv) that **PS2** is where the differentiation is.

---

### 2. Assumption register

#### Product & user
| # | Assumption | Tag |
|---|---|---|
| A1 | Output is consumed by an allocation/strategy function and machine orchestration, not primarily by agents | `[INFER]` |
| A2 | The buyer cares more about avoided conduct exposure than about a marginal RPC gain | `[INFER]` — **test in persona review** |
| A3 | CN wants a module inside Maestro rather than a competing platform | `[INFER]` |
| A4 | "Do nothing / wait" is an acceptable recommendation to a collections manager | `[UNVERIFIED]` — behavioural, must be tested |
| A5 | A refusal (blocked action) is as valuable to demo as a recommendation | `[INFER]` |

#### Economics
| # | Assumption | Tag |
|---|---|---|
| A6 | Field visit unit cost ₹220 marginal / ₹370 standalone | `[MODEL]` from `[EXT]` salary data + assumptions |
| A7 | Trace ₹60–150 per case in India | `[EXT]`-anchored (global bulk $5–25; US one-off $50–175) |
| A8 | Human call ₹33–44 per RPC; automated dial ₹1.35–2.6 | `[MODEL]` from `[EXT]` |
| A9 | Incremental recovery per extra RPC ≈ ₹205 at an ₹18.8k ticket | `[ASSUME]` — **the most consequential assumption in the model** |
| A10 | 15–25% of 1–30 DPD accounts self-cure | `[EXT]` vendor-published `[vendor]` |
| A11 | Field visits matter little at <₹50k unsecured tickets unless marginal to a beat | `[MODEL]` |

#### ML / data
| # | Assumption | Tag |
|---|---|---|
| A12 | Attempt-level telephony telemetry exists in the sandbox | `[UNVERIFIED]` |
| A13 | RPC labels can be verified at ≥3 confidence tiers (payment / agent-confirmed / inferred) | `[INFER]` |
| A14 | Never-tested contact points are a large share of the book | `[UNVERIFIED]` |
| A15 | Recycled-number detection is feasible from ≥90-day silence + discontinuity | `[EXT]` — TRAI mandates a ≥90-day gap before reallocation `[EXT]` |
| A16 | Graph features add lift beyond hand-built shared-contact counts | `[UNVERIFIED]` — must be measured, not assumed |
| A17 | Sequence/GNN models are not needed for the MVP | `[INFER]` |

#### Compliance
| # | Assumption | Tag |
|---|---|---|
| A18 | A modelled P(right party) is the correct gate for debt-disclosing actions | `[PS]` implies |
| A19 | Logging alone does not constitute compliance | `[EXT]` — RBI framework judges whether **systems permitted** a violation |
| A20 | The 1-day pre-visit notice must be gated by **address confidence**, not just scheduled | `[INFER]` — **this is our sharpest novel compliance insight** |
| A21 | Non-borrower contact points may be used as *features* but not as *contact targets* | `[EXT]` |
| A22 | DPDP erasure/purpose duties interact with 6-month call-recording retention | `[EXT]` — unresolved tension; needs legal input |

#### Competition
| # | Assumption | Tag |
|---|---|---|
| A23 | Contact intelligence (who to call, which number, when) is a mature market | `[EXT]` — TransUnion PBI claims +33% RPC; Spocto contactability; SkipTracer.in |
| A24 | CN's own platform already performs allocation and outreach | `[EXT]` — CN Maestro: allocation 24h→30 min, 150+ agents, 20 modules |
| A25 | Our differentiation must therefore be narrower than "RPC prediction" | `[INFER]` — **central conclusion** |

---

# Part III. PS3 — assumption register & problem re-read

*Source file: `PS3_ASSUMPTIONS.md`*

## PS3 — ASSUMPTION REGISTER & PROBLEM RE-READ

**Problem statement 3:** *An address geocoder that learns from field visits. Indian addresses are descriptive and landmark-based, mixed-language, transliterated, misspelt. Commercial geocoders land at locality/pincode centroids. Output must be lat/lon + confidence radius + landmark-based directions, continuously learning from new successful visits. The field app must work offline.*

Tags: `[PS]` problem statement · `[EXT]` external research · `[INFER]` our inference · `[UNVERIFIED]` unconfirmed.

---

### 1. The eleven questions

#### 1.1 What is the exact user/customer?
| Layer | Who | Tag |
|---|---|---|
| Paying customer | The lender / ARC | `[PS]` |
| **Primary user of the output** | The **field agent** standing on a street at 4pm with a phone | `[PS]` implies ("field app", "offline") |
| Operational owner | Field operations manager allocating beats and slots | `[INFER]` |
| Silent beneficiary | **Household members, neighbours and shopkeepers** who must not learn about the debt | `[INFER]` — from the RBI third-party rule `[EXT]` |
| Data owner | CN's address/contact-data steward | `[INFER]` |

#### 1.2 Who actually uses the output?
`[PS]` The field agent (pin + radius + directions), offline. `[INFER]` The allocator (is this address visit-worthy at all?) is the *higher-value* consumer, because that decision costs ₹220–370 per slot `[EXT]`/`[MODEL]`.

#### 1.3 What decision are they making?
1. **Do we send a recovery notice / visit to this address at all?** (RBI now requires ≥1 day advance notice before the first visit `[EXT]` — so sending the notice is itself the irreversible act)
2. **Where exactly do we send the agent**, and what do we tell them to look for?
3. **Do we trust what came back?** (integrity)
4. **Has this borrower moved?** (a contactability signal that belongs to PS2)

#### 1.4 What does "success" mean operationally?
`[INFER]`, ranked:
1. **Right-door rate** — visits that reach the intended household
2. **Zero notice-to-wrong-party events** — a notice delivered to the wrong home is a disclosure event
3. **Field-slot yield** (borrower met / slots spent), and slot cost
4. **Calibrated abstention** — the system says "I don't know" instead of guessing
5. Distance error (median and p90) — necessary but **not** the headline, because a 90 m error in a dense colony can be one building wrong

#### 1.5 What does CN gain?
`[EXT]` CN already advertises **32% higher field efficiency** and RBI-compliant audit trails. So the gain is not "field efficiency" in general — it is:
1. **A number they cannot currently produce**: the confidence of each address, and the notice/visit decisions that confidence blocks
2. **A defensible answer to an RBI inspection** on exactly the control that is hardest to prove (advance notice delivered to the right door; borrower/guarantor-only contact)
3. **An asset that compounds**: every successful visit improves the address for the *next* account at that landmark `[PS]` requires continuous learning

#### 1.6 What could go wrong?
| Failure | Mechanism | Tag |
|---|---|---|
| Notice disclosure | Advance notice sent to an address 1.3 km off in a dense colony | `[INFER]` ← new, highest severity |
| False confidence | Radius says 90 m; the actual home is 900 m away in a different lane | `[PS]` |
| Label poisoning | Agent fabricates a check-in; geocoder learns the wrong place | `[PS]` implies |
| Purpose confusion | Agent meets the borrower at his shop and the system treats *the shop* as home | `[PS]` |
| Staleness | Borrower moved 2 years ago; address is "correct" and useless | `[PS]` |
| Offline divergence | Two agents in the same locality hold different frozen packs | `[INFER]` |
| Commercial-ToS breach | Caching a commercial geocoder's coordinates as training data | `[EXT]` — Google/MapmyIndia terms restrict caching |

#### 1.7 What constraints are mandatory?
| Constraint | Tag |
|---|---|
| Offline-capable field app | `[PS]` |
| Confidence radius output, not just a point | `[PS]` |
| Landmark-based, local-language directions | `[PS]` |
| Continuous learning from new successful visits | `[PS]` |
| No third-party debt disclosure (RBI) | `[EXT]` |
| ≥1 day advance notice before first visit (RBI) | `[EXT]` |
| Minimum-necessary data to agents; no employer/workplace details shared | `[EXT]` |
| Geotagged visit evidence already expected by buyers (Mobicule/Credgenics ship it) | `[EXT]` |

#### 1.8 What data is required?
`[PS]` successful-visit GPS (which may be home, shop, workplace or a road), failed-visit GPS, GPS trails, dwell time, visit outcomes, agent remarks, nearby confirmed locations.
`[UNVERIFIED]` Whether CN's sandbox has **trails** (not just final points), **dwell**, **attestation/mock-location flags**, **failed-visit coordinates**, and **multilingual remarks**. These four determine whether the integrity model and the purpose classifier are buildable or just aspirational.

#### 1.9 Explicitly required vs merely suggested
| Element | Status |
|---|---|
| Geocode with confidence radius | **Required** `[PS]` |
| Landmark-based directions | **Required** `[PS]` |
| Learn continuously from visits | **Required** `[PS]` |
| Offline operation | **Required** `[PS]` |
| Parse → normalise → candidates → rank → robust estimator → conformal radius → directions | Our pipeline `[INFER]` |
| libpostal / deepparse / IndicXlit / LambdaMART / GeoConformal / H3 | Our tool choices `[INFER]`, **all replaceable** |
| Integrity/anti-fabrication model | Our addition — `[INFER]`, but strongly implied by "fake check-ins" being a named challenge `[PS]` |

#### 1.10 Our own assumptions (the ones we must not smuggle into the pitch as facts)
| # | Assumption | Tag |
|---|---|---|
| B1 | Field-visit volume is sufficient to train a geocoder in CN's portfolios | `[UNVERIFIED]` — **at ₹18.8k average digital-PL ticket, visits are rare; this may be false for the highest-volume portfolio** |
| B2 | Successful-visit GPS is a good label for *home* | `[UNVERIFIED]` — `[PS]` explicitly says it may be shop/workplace/road |
| B3 | Third-party geocoders can be used at runtime but not cached as training data | `[EXT]` |
| B4 | An outcome-learning Indian address engine does not already exist | **FALSE** — see §1.11 |
| B5 | Calibrated radii are not commercially available for India | **MOSTLY FALSE** — Delhivery GeoNaksha returns an *error radius* `[EXT]` |
| B6 | Agents can be trusted to self-report | **FALSE by design** — hence the integrity model |

#### 1.11 The three findings that invalidate part of our previous PS3 story
1. **Shiprocket Address Intelligence** `[EXT]`: NLP + spatial reasoning, **learns from every successful delivery and every delivery-partner correction**, claims **72.69% of addresses within 100 m** and **90.57% within 500 m**, sub-200 ms on CPU. → *"Nobody learns from field outcomes"* is false. It exists, at national scale, in India.
2. **Delhivery GeoNaksha / Maps** `[EXT]`: LLM geocoding that returns **structured coordinates with an error radius for positional confidence**, validates against **4 billion+ deliveries / 3M+ daily**, and offers **Address Verification ("has this address been visited in the last N months?")**. → *"Geocoders return a point with no uncertainty"* is false, and *"visit-history verification"* already ships — in logistics.
3. **Google Address Validation API for India** `[EXT]`: ML parsing that returns **component-level accuracy**, and explicitly **distinguishes residential from commercial** addresses. → Part of our "place-purpose classification" novelty is also productised.

**Consequence for the pitch.** PS3 cannot be sold as "a better geocoder", "an outcome-learning geocoder", or "the first to give uncertainty". The defensible residue is narrower and — fortunately — sharper:
- **(i)** these systems learn from **deliveries**; collections needs evidence from **recovery visits**, whose failure modes differ (refusal, borrower not at home, hostile household, agent incentive to fake);
- **(ii)** nobody maps address confidence to a **compliance decision** — *whether the RBI-mandated advance notice may be sent and whether a recovery action may be taken at that door*;
- **(iii)** nobody treats a returned visit as **weighted evidence with an integrity discount** rather than a fact;
- **(iv)** nobody separates **home / workplace / shop / a family member's address** for the specific purpose of *not exposing a debt to the wrong person*.

That residue is the PS3 product. It is narrower, more credible, and much harder for a logistics company to copy.

#### 1.12 What we should NOT claim
- Not "we beat Google on Indian addresses" (Shiprocket/Delhivery already claim better, and we cannot verify either).
- Not "calibrated coverage guarantees" as a headline (conformal on a handful of synthetic visits is unfalsifiable).
- Not "we replace the geocoder" (we consume one).
- Not "our model found the home" without stating the **integrity weight** and the **abstention rate** alongside it.

---

# Part IV. Market research, competitor map & the 12-persona advisory board

*Source file: `PS2_PS3_MARKET_RESEARCH.md`*

## PS2 / PS3 — MARKET RESEARCH

*Consultant's view of who already solves this, what they claim, what they cannot do, and what is left.*
All claims labelled `[PUB]` (published/claimed by the vendor or press) or `[EXT]`/`[INFER]`. Vendor marketing is directional, not evidence.

---

### 1. The map

#### 1.1 CreditNirvana itself — the most important competitor is the host
| | |
|---|---|
| What it is | **Agentic-AI-native collections platform for Indian BFSI**, a **Perfios company** (acquired March 2025) `[PUB]` |
| Scale claimed | 1,000+ institutions behind Perfios, **62M+ accounts under management**, $21B+ (~$11B at Maestro launch), 9 portfolio types, 400M+ data points `[PUB]` |
| Product | **Maestro** (launched 26 Nov 2025): 150+ GenAI collection agents, **20 modules**, digital + voice + **field operations** + settlement + legal + repossessions `[PUB]` |
| Claims | −60–70% human intervention, **+40% collection efficiency**, up to **95% fewer language-compliance errors**, allocation cut **24h → 30 min**, **+32% field efficiency**, 80+ dashboards `[PUB]` |
| Compliance posture | RBI-compliant, SOC 2 Type II, "timestamped consent", "immutable audit trails with policy decision logs", "RBI contact hours enforced at the dialer and AI layer" `[PUB]` |
| Client outcomes shown | bounce rates down 15–30% in 3–6 months (up to 66% in Bucket 0); a Top-5 ARC: 1.5M+ accounts, 2× portfolio capacity `[PUB]` |
| Weakness we can exploit | Everything above is **claimed at the platform level**. There is **no published mechanism** for: contact-point-level health, calibrated address confidence, or gating a recoverable action on modelled identity. "Compliant" is asserted through logs, not *proved by blocked actions*. |

#### 1.2 Adjacent / direct competitors
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

#### 1.3 Answering the question we were told not to ignore
> **"If CreditNirvana already has an agentic collections platform, why would they care about our solution?"**

Because Maestro answers *"what should we do next?"* and **cannot currently prove three things**:

1. **Is this contact point actually reachable by the *right person*, or are we about to talk to a stranger?** Maestro has 150+ agents but no published, contact-point-level identity model. Every disclosure-control claim rests on scripts and logs, which RBI's 2026 framework explicitly says is not enough ("compliance will be assessed on whether your systems permitted a violation" `[EXT]`).
2. **Is this address good enough to send a legally-required advance notice to?** Under the new framework, the notice precedes the visit and is itself an irreversible artefact. A wrong-door notice is a disclosure event. Nothing in the market gates the *notice* on address confidence.
3. **What did we learn from the visit, and was it true?** Field GPS is captured (Mobicule-style) and used for beat plans; it is **not converted into a learned, integrity-weighted address belief** that changes tomorrow's decision.

So the honest positioning is not "another platform". It is:
> **A control layer for the two irreversible actions in collections — taking a compliance-bearing action against an unverified identity, and sending a recovery notice to an unverified address.**

That is a module inside Maestro, it is bought by the compliance + CFO + field-ops trio, and it makes CN's existing marketing claims *demonstrable*.

---

### 2. What users complain about (borrower side and operational side)
| Complaint | Evidence |
|---|---|
| Harassment, night calls, shaming | FY24: **85,281** loan/recovery complaints to the RBI Ombudsman, **+42.7% YoY**, ≈29% of all complaints `[EXT]`; experts estimate <5% of harassment cases are ever reported `[EXT]` |
| Lenders pay for agent behaviour | Bajaj Finance fined **₹2.5 Cr** for recovery-agent harassment `[EXT]` |
| Compensation is rising | RB-IOS 2026: up to **₹3 lakh** for harassment/mental anguish (was ₹1 lakh), **90-day** filing window `[EXT]` |
| Address-driven failure is normal | ~**30%** of last-mile shipments required a phone call to the customer to find them `[EXT]`; PIN codes frequently missing/wrong and too coarse for a doorstep `[EXT]` |
| Dashboards nobody uses | Multiple `[INFER]` — CN itself advertises "80+ dashboards out of the box", which is a warning sign, not proof |
| Tracing latency | Indian tracing sold on "hours → minutes" per case `[EXT]` — i.e. it is still a manual bottleneck |

---

### 3. Virtual advisory board (12 reviewers)

Format: **objection → answer → unresolved → what we changed**.

#### 3.1 Collections Head — *"Will this improve collector productivity?"*
- **Objection:** "My problem isn't prediction, it's that my team works the same list every day. Another score doesn't help."
- **Answer:** the output is an ordered work list plus a **refusal list** (accounts not worth contacting) and a **street-level field list**. It removes work rather than adding a screen.
- **Unresolved:** whether a manager will accept "do not contact this account this week" as a recommendation from a model.
- **Changed:** made **"do nothing / wait"** a first-class output and put the refusal count on the main screen, not in a log.

#### 3.2 Field Operations Head — *"Will this reduce failed visits?"*
- **Objection:** "My agents already have routes and geo-tagged check-ins."
- **Answer:** the beat plan optimises *travel*; this optimises *target quality*. The value is in the slots you don't spend, and in the notices you don't mis-deliver.
- **Unresolved:** whether address-confidence gating reduces the visit *count* by enough to notice (at ₹18.8k tickets it may not).
- **Changed:** scoped the field story to portfolios with material visit volume; made route integration optional.

#### 3.3 CFO — *"Where exactly does the money come from?"*
- **Objection:** "Show me the rupee."
- **Answer (post-model):** not from dial savings — our own model shows dial-volume optimisation is worth ₹0.3–7 lakh/month on a 100k book. It comes from four places: avoided expensive actions (₹220–370 per wasted slot, ₹60–150 per wasted trace), conduct exposure (₹3–75 lakh/month band at 0.2–1% escalation), reclaimed human/field capacity, and basis-point RPC gains. See `PS2_PS3_FINANCIAL_MODEL.md`.
- **Unresolved:** the incremental-recovery-per-RPC figure (₹205 in our model) is an assumption, not a measurement.
- **Changed:** **deleted the recovery-uplift claim** from the value proposition. The pitch is now *avoided waste + avoided exposure*, both countable on real accounts.

#### 3.4 CRO / Risk Head — *"Can this increase recovery without increasing customer risk?"*
- **Objection:** "Every extra contact is a complaint waiting to happen."
- **Answer:** the system *reduces* contact volume on low-yield accounts and hard-blocks disclosure-capable actions below an identity threshold.
- **Unresolved:** borrower-experience metrics (NPS, complaint rate) aren't in the sandbox.
- **Changed:** made complaint-risk a **guardrail metric** with a hard ceiling, not a soft target.

#### 3.5 Compliance Officer — *"Can this accidentally disclose debt to a wrong party?"*
- **Objection:** "You will be judged on what your system prevented."
- **Answer:** debt-disclosing actions are **not in the candidate set** unless P(right party) ≥ τ; non-verifiable points can only receive a no-disclosure script; notices are gated on address confidence; grievance-hold and sensitive-occasion suppression are hard filters; every refusal is logged with the rule that fired.
- **Unresolved:** DPDP erasure vs the mandated 6-month recording retention.
- **Changed:** added the **notice-confidence gate** and the **grievance/bereavement suppression state** to the architecture; added DPDP-aware retention rules.

#### 3.6 Data Science Head — *"Can I trust the labels and evaluate the model?"*
- **Objection:** "You are learning your own dialer's behaviour."
- **Answer:** labels are tiered (payment > agent-confirmed > inferred), never-tested contacts are censored not negative, propensities are logged, and field-visit outcomes are policy-independent-ish evidence.
- **Unresolved:** no randomised holdout in the sandbox → no honest uplift estimate.
- **Changed:** removed uplift/Qini from the MVP claims; evaluation is temporal-split, calibration + decision-regret, with explicit limitations.

#### 3.7 CTO — *"Can this integrate into our existing systems?"*
- **Objection:** "We have 20 modules and an API-first stack. Don't hand me a new platform."
- **Answer:** two endpoints (`/eligibility`, `/address-confidence`), a decision-record table, and a config service — it is designed to sit *behind* Maestro.
- **Unresolved:** whether the sandbox exposes the telephony/label fields we need.
- **Changed:** every interface is specified as a contract in the two architecture files.

#### 3.8 Product Manager — *"Why ship this instead of improving the existing platform?"*
- **Objection:** "Which of our 20 modules does this replace?"
- **Answer:** none — it upgrades three of them (allocation, field ops, compliance) from *claimed* to *provable*, and it is the only one addressing the Oct-2026 RBI conduct provisions.
- **Unresolved:** internal build-vs-buy; CN could build it.
- **Changed:** positioned explicitly as a **reference implementation + specification** they could absorb.

#### 3.9 Bank/NBFC Customer — *"Why should I pay for this?"*
- **Objection:** "I already pay for a collections platform and for agencies."
- **Answer:** it reduces the two things they are personally exposed to: regulator/ombudsman complaints and wasted field/trace spend — and it makes their own RBI inspection cheaper.
- **Unresolved:** proven savings without a pilot.
- **Changed:** added an explicit **30-day pilot design** with pre-agreed counters.

#### 3.10 Hackathon Judge — *"Why is this better than 50 other AI collection projects?"*
- **Objection:** "Everyone will build a churn-style risk model and a dashboard."
- **Answer:** we do not claim a better model. We show a **refusal**: the system blocks a legally-required notice because the address is not good enough, then unblocks it after verifying evidence arrives. Almost nobody will build the negative path.
- **Unresolved:** judges may prefer a flashier accuracy number.
- **Changed:** the demo's centre of gravity is the blocked action + the evidence that unblocks it, in under 3 minutes, offline-capable.

#### 3.11 Data Protection Officer (added) — *"What is the lawful basis for enrichment and profiling?"*
- **Objection:** purchased contact data + automated profiling + retention is a DPDP problem, not just a technical one.
- **Answer:** purpose-limited processing under the recovery legal basis, no unnecessary data to agents, DPIA-style documentation, erasure workflow that respects statutory retention, and no *new* data purchase in the MVP.
- **Unresolved:** whether the sandbox data is consent-clean for a demo.
- **Changed:** MVP uses only data types CN already holds; every enrichment step is optional and switchable.

#### 3.12 The Field Agent (added) — *"What's in it for me?"*
- **Objection:** "If my check-in is used to grade me, I'll game it."
- **Answer:** the integrity model is deliberately **soft-weighted, not punitive**, and the app gives the agent landmark directions, a radius instead of a false-precision pin, and a no-disclosure script that protects *them* personally from a complaint.
- **Unresolved:** any integrity model creates a gaming incentive; must be paired with field-ops policy, not just code.
- **Changed:** integrity output ships as a **credibility weight + widening radius**, explicitly not as an agent-fraud accusation.

---

### 4. The gaps that survive all of this

| Gap | Why it survives the market scan |
|---|---|
| **A notice/visit gated on address confidence** | Every competitor discloses and geotags *after* the decision; nobody gates the decision on confidence |
| **An identity gate that removes the disclosure-capable action from the candidate set** | Competitors assert compliance via scripts and logs; RBI 2026 explicitly rejects "we trained them" as evidence |
| **Integrity-weighted field evidence** | Field apps capture geo-tagged "proof" (`[PUB]` Mobicule), which is exactly the wrong frame if the proof can be manufactured |
| **Contact-point-level, censoring-aware scoring with a rules floor** | TransUnion/Spocto productise account-level contactability; contact-point slates remain unmodelled |
| **A priced trace decision** | SkipTracer.in and TruLookup sell tracing; nobody publishes per-account EVSI gating |
| **Decision-level auditability** | CN claims immutable audit trails; a *decision record with the constraint that blocked the action* is a different artefact |

---

# Part V. Red team — 36 questions and every scored alternative

*Source file: `PS2_PS3_RED_TEAM.md`*

## RED TEAM — attacking our own solution before a judge does

*Nothing in this file defends the previous design. Where a previous choice survives, it is because the attack failed, not because it was ours.*

---

## PART A — THE 36 QUESTIONS

### A1. Product (6)

| # | Question | Honest answer | Verdict |
|---|---|---|---|
| P1 | Would a collections manager actually use this? | Only if it lands in their **existing allocation workflow** and includes a *refusal* list they trust. A separate dashboard would not be used — CN already ships 80+ of them `[PUB]`. | **Design change:** output = allocation deltas + exception queue, not a dashboard |
| P2 | Does it reduce an important operational bottleneck? | The bottleneck is not "which number to dial" (cheap, automated). It is **deciding which expensive action to spend** and **not triggering a conduct event**. | **Reframe:** the product governs expensive + irreversible actions |
| P3 | Does it fit an existing collector workflow? | Tele-calling: partly (allocation). Field: poorly, unless beat plans consume our confidence output. Compliance: well — it becomes their evidence. | **Design change:** three consumers, three contracts |
| P4 | Does it create another dashboard nobody wants? | Yes, as previously specified. Our own first deliverable had 3 UIs for a 48-hour build. | **Cut:** one screen per persona, or none |
| P5 | What decision changes because of our product? | (a) a visit slot is withheld, (b) a notice is withheld, (c) a debt-disclosing script is replaced by an identity check, (d) a trace is not ordered, (e) an account is left alone this week. All five are *negative* decisions. | **This is the product.** Name it that way |
| P6 | Who pays, and why would a bank/NBFC/ARC buy it? | The lender pays as part of the CN subscription; it buys **reduced regulatory exposure and reduced waste in field/trace budgets**, not "AI". | Moved to CFO narrative |

### A2. Economics (9)

| # | Question | Answer |
|---|---|---|
| E1 | Value of one additional RPC? | **₹6–11 (automated) / ₹33–44 (human) cost per RPC**, and ~₹205 **incremental** recovery per RPC at an ₹18.8k ticket under stated assumptions `[MODEL]`. The ratio is what matters, and it is thin — which is why the pitch is avoided waste, not uplift |
| E2 | Cost of a failed call? | ₹1.35–2.60 automated, ₹8.48 human-dialled. **Trivial.** Do not build a business case on it `[MODEL]` |
| E3 | Cost of a field visit? | ₹220 marginal / ₹370 standalone `[MODEL]`. Material |
| E4 | Cost of skip-tracing? | ₹60–150/case `[EXT]`-anchored. Material |
| E5 | Cost of a wrong-party contact? | ~₹0 directly; **₹3,000–75,000 in expectation** after applying a 0.2–1% escalation probability `[MODEL]`, plus lumpy RBI penalties (Bajaj ₹2.5 Cr) |
| E6 | Value of information from an exploratory action? | Unmeasurable in this sandbox. So exploration must cost **zero extra contacts** (reallocate an attempt we were already going to make) |
| E7 | At what balance/DPD does field tracing become justified? | Our model: **visit ROI < 1× standalone below ~₹13k ticket**; >2× marginal at ₹18.8k; 19× at ₹1.5L; 104× at ₹8L. Trace EV spans **30×** across accounts — a rule cannot capture it `[MODEL]` |
| E8 | When is "do nothing / wait" better? | When (a) the account is likely to self-cure (15–25% at 1–30 DPD `[EXT]`), (b) all contact points are identity-ambiguous, (c) a grievance or hardship state is open, (d) the hazard is near zero right after a rejection | 
| E9 | How does economics change 30 DPD vs NPA? | Early bucket: cheap channels, self-cure dominates, **the crime is over-contact**. NPA/secured: expensive channels, asset at stake, **the crime is under-contact and route inefficiency**. Same engine, opposite default |

### A3. ML (8)

| # | Question | Answer |
|---|---|---|
| M1 | Are the labels valid? | Tiered: payment-made > inbound call > agent-confirmed identity > inferred from disposition. Payment is the only near-gold label |
| M2 | Are we learning collector behaviour rather than contact health? | Yes, unless we log the incumbent policy's propensity and weight by it. **This is a first-class requirement, not a refinement** |
| M3 | How do we distinguish "no answer" from "wrong party"? | Different heads + different evidence (network layer vs identity layer). Requires disposition discipline CN may not have `[UNVERIFIED]` |
| M4 | Censored/unobserved contacts? | Survival framing (never-tested = censored) — but see M6 |
| M5 | Can the model create feedback loops? | Yes. Mitigations: propensity weighting, field-visit evidence (policy-independent-ish), and *not* adding a randomised-audit stream that costs money on small tickets |
| M6 | **Does survival modelling materially improve the MVP?** | **No, not as a headline.** It improves *retest timing*, worth ₹94k/month per pp of slot success in our model. Keep it as a **timing sub-component**, not an architecture |
| M7 | Do graph features add measurable lift? | Unknown `[UNVERIFIED]`. And RBI now restricts contacting non-borrower parties, so graph edges are **features, not targets**. Demote to v2, gated on a measured lift test |
| M8 | Does model sophistication improve business decisions enough to justify complexity? | No. Per-pp value ranking: connect-rate, identity-gate, field-slot, trace-yield `[MODEL]`. The cheapest large lever (P(pay\|RPC)) belongs to **CN's existing agent layer** — so we should *not* compete there |

### A4. Compliance / responsible collections (8)

| # | Question | Answer |
|---|---|---|
| C1 | Could our recommendation expose a borrower's debt to a third party? | Yes — via (a) a call to a recycled number, (b) a **notice sent to a wrong address**, (c) a visit to a shared/landmark address. All three must be gated |
| C2 | Can the system recommend a call that is profitable but unacceptable? | Only if disclosure-capable actions are *scored* rather than *excluded*. They must be excluded from the candidate set |
| C3 | What happens when address confidence is low? | **Nothing is sent** — no notice, no visit; the account moves to verification actions only. This is the centrepiece |
| C4 | What if a phone is shared by multiple borrowers? | Identity head + cross-account identity conflict features; without identity confirmation, no-disclosure script only |
| C5 | How do we prove why a contact was selected? | Decision record: config version, rule evaluations, probabilities, candidate set with per-candidate blocking reasons, chosen action, propensity |
| C6 | Can a compliance officer audit one decision months later? | Only if the record is immutable, versioned, and includes the *constraint that fired*. Retention interacts with DPDP erasure `[EXT]` |
| C7 | What happens when the model is wrong? | Bounded harm by design: the expensive/irreversible actions require higher confidence than cheap reversible ones. Wrong ⇒ lost opportunity, not a disclosure |
| C8 | Do we claim compliance because we have an audit log? | **No.** RBI 2026 judges whether the *system permitted* the violation. So the claim must be "the action was not in the candidate set", demonstrated live |

### A5. Competition (5)

| # | Question | Answer |
|---|---|---|
| K1 | Has somebody already built this? | The **components** yes: contact intelligence (TransUnion PBI +33% RPC), contactability (Spocto), tracing (SkipTracer.in), geo-tagging (Mobicule), outcome-learning addresses (Shiprocket 72.69% <100 m) |
| K2 | Is the novelty real? | Only in the **integration point**: identity-gated eligibility + confidence-gated notices + integrity-weighted field evidence. See `NOVELTY_MATRIX.md` |
| K3 | Is this merely "XGBoost + dashboard"? | As previously specified, closer to "12 models + 3 dashboards". Now: rules floor + 2 models + a gate + an evidence ledger |
| K4 | Is PS2 substantially different from existing contact-intelligence products? | **No, not at the model level.** Different at the *permission* level (what the output is allowed to authorise) |
| K5 | Is PS3 merely a wrapper around Google/OSM? | **Partly yes.** It becomes non-wrapper only via recovery-visit evidence, integrity weight, purpose classification and the notice gate |

---

## PART B — FIVE ALTERNATIVE PS2 FORMULATIONS, SCORED

Scoring 1–5 (5 = best), with the honest reason.

| Formulation | Data need | Complexity | Explainability | Expected business value | Hackathon fit | Production fit | Novelty | Failure modes | **Total** |
|---|---|---|---|---|---|---|---|---|---|
| **A. Contact-point ranking (slate LTR)** | Med | Med | Med | Med | **5** | 4 | 3 | Can rank a point that should never be contacted | 25 |
| **B. Latent-state model (HMM/state machine)** | High | High | Low | Med | 2 | 3 | 4 | Unidentifiable states; audit is hard | 21 |
| **C. Hazard / survival (retest timing)** | Med | Med | Med | Med | 4 | 5 | 3 | Sensitive to censoring assumptions; no identity | 25 |
| **D. Contextual bandit** | High (needs randomisation) | High | Low | Potentially High | 2 | 3 | 4 | Exploration harms real people; compliance-hostile | 16 |
| **E. Decision-centric EV + abstention** | Low–Med | Low | **5** | **5** | **5** | 5 | 4 | Needs defensible costs; garbage-in → garbage decisions | **34** |
| **F. Causal / uplift** | Very high (holdout) | High | Med | High *if* identifiable | 1 | 3 | 5 | Cannot be validated without randomisation | 15 |
| **G. Graph identity/contact** | High | High | Low | Med | 2 | 4 | 4 | Regulatory limits on non-borrower contact | 20 |
| **H. Hybrid: rules floor + calibrated scoring + EV gate** | Med | **Low–Med** | **5** | **5** | **5** | **5** | 3 | Rule drift; needs governance | **34** |

**Chosen: H ⊕ E** — a **rules floor** (legal + conduct constraints and recycling heuristics, deterministic and auditable), **one calibrated contact-point scorer**, and an **expected-value gate with an explicit abstain/"wait" action**.

Why this beats the previous design: it removes survival, graphs, bandits and uplift *from the critical path* while keeping their outputs as optional inputs; it is explainable by construction; and it is buildable to a demo in 48 hours. Survival returns in the competition-final version strictly as **retest timing**; bandits only after a real randomised holdout exists; graph features only after a measured lift test — i.e. all three must **earn** their way back.

---

## PART C — SIX PS3 ARCHITECTURES, SCORED

| Architecture | Data need | Complexity | Explainability | Business value | Hackathon fit | Production fit | Novelty | Failure modes | **Total** |
|---|---|---|---|---|---|---|---|---|---|
| **A. Commercial geocoder + post-processing** | Low | Very low | High | Low (commodity) | 4 | 5 | 1 | No learning; ToS caching limits | 22 |
| **B. Parse → normalise → geocode pipeline** | Med | Med | High | Low–Med | 4 | 4 | 2 | Parsing is not the bottleneck (Shiprocket/Delhivery solved it) | 22 |
| **C. Multi-candidate generation + LTR ranker** | Med | Med–High | Med | Med | 3 | 4 | 3 | Needs labelled candidates; candidates usually agree | 24 |
| **D. Belief/distribution model + Bayesian fusion of visit evidence** | Med | Med | Med–High | High | 4 | 4 | **5** | Weak priors; needs honesty about uncertainty | **32** |
| **E. D + robust estimator + empirical radius** | Med | Med | High | High | **5** | 4 | 4 | Radius quality unverifiable at small n | 30 |
| **F. End-to-end LLM / geospatial foundation model** | Very high | Very high | Low | Uncertain | 1 | 2 | 3 | Compute, cost, licensing, no calibration | 12 |
| **G. Visit-evidence only (no geocoder)** | High | Med | High | Med | 2 | 2 | 4 | Cold start; rural sparsity | 18 |
| **H. Hybrid: consume a commercial geocoder + fuse recovery-visit evidence + purpose classification + integrity weight + confidence gate** | Med | Med | **5** | **5** | **5** | 5 | 4 | Requires visits to exist for the segment | **34** |

**Chosen: H** (which internally uses D's belief representation and E's empirical radius).

**The attack we accept:** *"Is candidate generation the bottleneck?"* — No. Two national-scale Indian systems already resolve unstructured landmark addresses to <500 m for the majority of inputs `[EXT]`. **Parsing and candidate generation are solved-enough. The bottleneck is deciding whether the result may be acted upon, and learning from the visits that only a recovery operation makes.**

**Consequently rejected:** building our own geocoder; a multi-head H3 classifier; libpostal/deepparse as a centrepiece; conformal coverage as a headline claim.
**Consequently kept:** belief + radius (empirical quantiles, honest and cheap), integrity weighting, home/work/shop purpose classification, landmark directions, the **notice/visit gate**, and the feedback from evidence → belief.

---

## PART D — SHOULD PS2 AND PS3 BE COMBINED? (6 options scored)

| Option | Judging clarity | Impl. risk | Demo strength | Novelty | Business value | Data need | Effort | **Total** |
|---|---|---|---|---|---|---|---|---|
| 1. PS2 alone | 4 | **5** | 3 | 2 | 4 | Med | Low | 23 |
| 2. PS3 alone | 4 | 3 | **5** | 4 | 3 | High | Med | 24 |
| 3. **PS2 + PS3 tightly integrated (one loop, one decision)** | **5** | 3 | **5** | **5** | **5** | High | Med–High | **31** |
| 4. PS2 + PS3 loosely integrated (two demos, shared UI) | 3 | 4 | 3 | 3 | 4 | High | Med | 24 |
| 5. PS2 core + PS3 as an uncertainty module | 4 | 4 | 4 | 4 | 4 | Med | Med | 27 |
| 6. PS3 core + PS2 as the decision layer | **5** | 3 | 4 | **5** | 4 | Med–High | Med | **29** |

**Verdict: combine — but only through one causal mechanism, and only where the economics support it.**

The combination is justified *not* by "they are related" but by a hard causal chain that only exists jointly:

> A recovery action has a **cost** (₹220–370 per slot, ₹60–150 per trace) and an **irreversibility** (the RBI-mandated advance notice precedes the visit). Therefore the decision to act requires (i) an **identity** judgement (PS2) and (ii) a **location** judgement (PS3). Neither alone can authorise the action. And the visit itself is the only source that improves (ii) — which then changes (i)'s economics.

**The condition we attach:** the coupling is worth building where **both** are true — (a) the portfolio has material field/trace spend, and (b) the ticket is large enough for a visit to matter. For a pure ₹18.8k-ticket automated-digital portfolio, PS3's loop is thin and PS2's value is mostly conduct-control. We therefore:
- build the **integrated loop** as the hero (options 3/6 fused),
- but declare **segment-conditional deployment**, and
- make PS2's conduct gate the part that always applies.

**Reversal recorded:** the first deliverable said "PS2 more feasible, PS3 more differentiation, build PS2+PS3 with PS2 as the spine". After market research, the differentiation has moved decisively to **PS3's confidence gate + PS2's identity gate as one permission layer**. PS2's *model* is commoditised; PS2's *permission* role is not.

---

# Part VI. SANKET — solution architecture (PS2)

*Source file: `PS2_SANKET_SOLUTION_ARCHITECTURE.md`*

## SANKET — PS2 SOLUTION ARCHITECTURE
#### Contact-point eligibility, right-party confidence and the priced next action

*25 sections as specified. Every component must justify itself against a simpler baseline; components that fail that test are marked **[CUT]** or **[v2]**, not quietly retained.*

---

### 1. Problem
CreditNirvana must predict P(right-party contact) **per contact point** and choose the next action — continue, switch point, switch channel, trace, visit — where **skip-trace is triggered by expected recovery versus cost, never by an attempt counter**. Three sub-problems: latent contact health is unobserved; most points are untested; and "borrower avoiding" vs "invalid" vs "recycled" look alike but need opposite actions. Add the 2026 regulatory frame: every contact is a *conduct* event, and debt-disclosing actions against unverified identities are prohibited.

### 2. User
| Consumer | What they see | Why they care |
|---|---|---|
| Allocation/strategy analyst | Nightly action list + exception queue | Cure rate, cost per rupee |
| Supervisor | Accounts the system refused to auto-touch | Is the refusal defensible? |
| Compliance officer | Decision records + conduct counters | Regulatory inspection |
| Dialer / orchestrator (machine) | Per-contact-point action with window | Execution |
| **Not the borrower** — the borrower is the subject of the decision, and the party the system protects | | |

### 3. Business objective
Primary: **reduce avoided waste and avoided conduct exposure** on the four expensive/irreversible actions (human call, field visit, trace, notice/legal), while holding or improving recovery. Deliberately *not*: maximising RPC, minimising dials, or maximising model AUC.

### 4. Data flow
```
contact_points (source, age, verification history)
   + attempt log (ring duration, cause code, disposition, timestamp, channel, CLI)
   + payment/PTP ledger           + agent attributes          + suppression state
   + optional HLR/carrier lookup  + cost table (versioned)    + constraint config (versioned)
        │
   [FEATURE VIEW] as-of point-in-time ──► [RULES FLOOR] ──► [SCORER] ──► [EV GATE] ──► ACTION
                                                                              │
                                                        [DECISION RECORD] ◄───┘
```

### 5. Feature architecture
**Tier 1 — deterministic (no model needed, and these do most of the work)**
- attempts in window; attempts this week; days since last contact; days since last RPC
- supplier of record and its age (application / KYC / bureau / self-update / trace)
- HLR state: reachable / absent / invalid / ported / line type `[EXT]`-purchasable at ₹0.13–0.60
- suppression state: grievance open, bereavement/hardship, dispute, DND, consent scope
- **recycling heuristic**: ≥90 days of silence followed by any answer with a stranger signature (TRAI mandates a ≥90-day gap before reallocation `[EXT]`)

**Tier 2 — modelled**
- reachability: answer rate by (weekday × window) for this point and its cohort; ring-duration distribution and trend; explicit call-reject rate (an avoidance signal); busy/off/out-of-service cause-code mix
- identity: ever-confirmed-right-party (and when); share of answers that were third-party; cross-account identity conflict (same number, different names/DOB/locality); discontinuity across a silence gap; transcript-derived stranger phrases
- productivity: PTP history and kept/broken ratio at this point; best channel for this account

**Tier 3 — deliberately excluded from the MVP**
`[CUT]` graph embeddings, `[CUT]` sequence encoders, `[v2]` shared-contact graph features (gate on a measured lift test), `[v2]` number-portability history beyond the HLR flag.

### 6. Model architecture
**Two models, not five.**
- **S1** `P(contact succeeds at this point, in this window | features)` — LightGBM, monotone constraints where sensible, isotonic-calibrated per channel × window bucket
- **S2** `P(right party | answer)` — LightGBM + isotonic, **trained only on answered calls** with tiered labels
- **S3 (timing sub-component)** hazard of "next successful contact", used **only** to rank retest times, not to produce probabilities shown to users
- **Rules floor** runs before both, and can veto their output.

`[CUT]` separate productive/PTP head in the MVP (it belongs to CN's offer layer, where our model adds nothing `[MODEL]`).

### 7. Label strategy
| Label | Source | Tier |
|---|---|---|
| Payment/PTP within N days of an RPC | ledger | 1 (near-gold) |
| Inbound call from the number | telephony | 1 |
| Agent-confirmed identity (doc/DOB challenge passed) | disposition | 2 |
| RPC inferred from disposition text | NLP | 3 |
| "Answered" | ring/talk duration + cause code | 1 (objective) |
| Recycled | agent marking, cross-account conflicts, ≥90-day disruption | 2–3 |
Never train on "which point was dialled" — train on "what happened when it was dialled", weighted by the propensity with which the policy chose it.

### 8. Bias / selection correction
- log `p(action chosen | context)` for every decision (a **requirement**, not a nicety)
- inverse-propensity weighting for training; report weighted *and* unweighted metrics
- **no randomised exploration stream** on small-ticket portfolios — at ₹205 incremental recovery per RPC, random contact has no ROI and creates conduct risk. Exploration is instead **within-envelope**: choose a different window/CLI among attempts we were already going to make.
- field-visit outcomes are treated as *policy-partially-independent* evidence and used to sanity-check calibration

### 9. Calibration
Isotonic on a held-out temporal fold for both models; **segmented** by channel × window × supplier-age; Platt where the segment has <1,000 points. Monitor ECE per segment weekly. Reason: a mid-range miscalibration changes which action wins the EV comparison.

### 10. Decision engine
For each account·contact-point·window, enumerate candidates:
`call_human`, `call_auto`, `message(WhatsApp/SMS)`, `switch_point`, `field_visit`, `trace`, `identity_check`, `wait(Δ)`, `suppress/close`.

Score each by **ENRC**:
```
ENRC(a) = P_rpc(a) · [P_pay|rpc · E[recovery] ]            ← incremental, not gross
        − cost(a)
        − λ_conduct · P(conduct event | a) · E[cost of conduct event]
```
Then pick `argmax` over the **eligible** set (§11). `wait` is a real candidate with its own value (cure risk vs contact risk). Skip-trace competes as an **information purchase**:
```
ENRC(trace) = π · k · ΔRPC · E[incremental recovery per RPC] − cost(trace)
```

### 11. Compliance gate (candidate-set construction, not post-hoc filtering)
```
Eligible(account, point, t) = { a :
    in_window(t)                              // 08:00–19:00 unless borrower expressly authorised
  ∧ interacts_only_with(borrower, guarantor)  // no relatives/co-workers
  ∧ ¬grievance_open ∧ ¬suppression(reason)    // bereavement / medical / hardship / dispute
  ∧ attempts_this_week + 1 ≤ cap              // "excessive calls" is prohibited
  ∧ ¬on_dnd(point) ∨ consent exists
  ∧ purpose_permitted(a)                      // DPDP
  ∧ ( discloses_debt(a) → P_right_party ≥ τ )  // IDENTITY GATE
  ∧ ( sends_notice(a) → address_confidence ≥ ρ )  // NOTICE GATE — from PS3
  ∧ channel_authorised(a)
}
```
Illegal actions are not scored; they do not exist for the optimiser. The decision record states which constraint removed each candidate.

### 12. Exploration strategy
- **No additional contacts** for exploration.
- VoI-directed **within-envelope** exploration: for ambiguous points, choose the window/CLI/channel that maximises information gain per attempt we already planned.
- **Retest scheduling** from the hazard sub-model (cheap, reversible, high-yield).
- `[v2]` Thompson/LinUCB **only** if a real randomised holdout becomes possible and the portfolio has the ticket size to fund it.

### 13. Expected-value / financial model
Inputs from `PS2_PS3_FINANCIAL_MODEL.md`: human call ₹33–44 per RPC; field visit ₹220 marginal / ₹370 standalone; trace ₹60–150; incremental recovery per RPC ≈ ₹205 at an ₹18.8k ticket `[MODEL]`. The engine's job is to **refuse** actions whose ENRC is negative — and to show that count.

### 14. API design
```
POST /v1/eligibility      {account, point, t} -> {eligible_actions[], blocked[{action, rule, config_version}]}
POST /v1/score            {account, points[]} -> {p_contact[], p_right_party[], hazard_band, drivers[]}
POST /v1/next-action      {account}          -> {action, window, channel, ENRC_breakdown, alternatives[], decision_id}
POST /v1/decision/{id}    -> full decision record (audit)
POST /v1/feedback         {decision_id, outcome}  -> ack + propensity stored
GET  /v1/health           -> model versions, ECE per segment, drift, refuse-rate
```

### 15. Database schema (PostgreSQL)
```
contact_point(point_id, account_id, type, value_norm, source, source_age_days,
              first_seen, last_verified, verified_by, hlr_state, status)
attempt(attempt_id, point_id, agent_id, ts, channel, cli, ring_s, talk_s, cause_code,
        amd, disposition_code, transcript_id, propensity)
rpc_event(account_id, point_id, ts, verified_how, tier)
payment(account_id, ts, amount, mode, ptp_flag, ptp_date, ptp_kept)
suppression(account_id, reason, opened_ts, closed_ts, evidence)
cost_table(action_type, unit_cost, effective_from, effective_to)
rule_config(config_version, effective_from, params_json)
decision(decision_id, ts, account_id, point_id, models_json, probs_json,
         candidates_json, chosen, propensity, blocked_json, config_version, shap_top5)
```

### 16. Training pipeline
Temporal split (train <T, validate T..T+14d, test T+14d..T+28d) → point-in-time feature build → IPW-weighted training → isotonic calibration on the validation fold → model card → registry. Nightly recalibration, weekly retrain, drift alarms on feature PSI and per-segment ECE.

### 17. Inference pipeline
Batch overnight for allocation (the primary path) + synchronous `/next-action` for interactive use. p95 target < 150 ms. Refusals and their reasons are recomputed at decision time from the *current* rule-config version, never cached.

### 18. Monitoring
Feature drift (PSI/KS) · per-segment ECE and Brier · refuse-rate by reason (a sudden rise = a rule misfiring) · conduct counters (out-of-window contacts, wrong-party contacts, grievance-state contacts — target zero) · decision-regret proxy on logged data · rule-config change log.

### 19. Explainability
Two layers only: (a) **reason codes** — human sentences ("identity unconfirmed at this point; disclosure actions blocked", "hazard peaks 19:00–20:00", "supplier age 11 days"); (b) SHAP top-5 attached to the record, never shown first. The reason codes are generated from the gate and the feature thresholds, so they cannot drift from the actual logic.

### 20. Audit trail
Every decision writes an immutable, versioned record containing: rule-config version, cost-table version, model versions, per-candidate ENRC, blocked candidates with the rule that blocked them, chosen action, propensity, and the timestamp in IST. Retention aligned to the mandated ≥6-month recording window, with a DPDP-compatible purge policy.

### 21. Failure modes
| Failure | Detection | Fallback |
|---|---|---|
| Labels are just dialer behaviour | calibration drifts off; field evidence disagrees | down-weight model, widen to rules floor |
| Disposition quality poor | high share of "other/unknown" | identity head disabled; all actions become no-disclosure |
| Rule-config stale vs a regulatory change | config-review SLA breach | freeze disclosure-capable actions until reviewed |
| Over-refusal (system blocks too much) | refuse-rate alarm + supervisor sampling | τ tuning with compliance sign-off, logged |
| Cost table wrong | ENRC decisions look absurd to ops | ops override with reason; override is logged and fed back |
| Recycling false positives | complaints from "answered-by-other" points | lower threshold sensitivity, keep challenge-only path |

### 22. MVP architecture (48 h)
Rules floor + S1 (contact) + S2 (right party) + EV gate with `wait` + identity gate + decision record + synthetic CN simulator + one screen showing **the refused action and why**. `[CUT]` hazard model, `[CUT]` IPW, `[CUT]` SHAP UI, `[CUT]` any exploration.

### 23. Production architecture
Feature store with point-in-time semantics · MLflow registry · nightly recalibration jobs · segment-level calibration monitors · rule-config service with change control and four-eyes approval · integration to Maestro's allocation and dialer layers · conduct dashboards for compliance.

### 24. Demo architecture
A single account, three contact points, one refused action, one unblocked action after evidence arrives (the PS2↔PS3 handshake), and an audit record opened live. Runs against the synthetic simulator **or** the sandbox, whichever is available, behind one switch.

### 25. Evaluation metrics
**Model:** PR-AUC (not ROC-AUC), Brier, ECE per segment, Precision@operating budget, and **precision of the recycled flag at the operating threshold** (a false positive costs an identity check; a false negative costs a disclosure).
**Decision:** refuse-rate by reason, % of disclosure-capable actions blocked below τ (must be 100%), avoided field slots, avoided traces, decision-regret proxy.
**Business:** cost per RPC, cost per productive RPC, ₹ recovered per human-agent hour, field-slot yield, trace ROI, cure/roll-back rate in bucket.
**Guardrails (all must be zero-or-alert):** out-of-window contacts, wrong-party contacts, contact while grievance open, contacts to non-borrower/non-guarantor, decisions without a complete record.

---

# Part VII. SUTRA — solution architecture (PS3)

*Source file: `PS3_SUTRA_SOLUTION_ARCHITECTURE.md`*

## SUTRA — PS3 SOLUTION ARCHITECTURE
#### Address confidence for the recovery decision

*26 sections as specified. SUTRA is deliberately **not** a geocoder: it consumes a commercial geocoder and adds the four things a collections operation needs and the market does not sell (recovery-visit evidence, integrity weighting, purpose classification, and a confidence gate on the irreversible action).*

---

### 1. Problem
Indian addresses are landmark-based, multilingual, transliterated and misspelt, so geocoders land at a locality centroid. CN needs lat/lon **plus a confidence radius** plus landmark directions, learning from field visits — and now, under RBI's 2026 framework, **an advance notice precedes the first in-person visit**, which makes a wrong-door address a *disclosure event*, not just an inefficiency.

### 2. User
Field agent (pin + radius + landmark route + no-disclosure script, offline) · field-ops manager (is this slot worth spending?) · compliance officer (was the notice legally sendable?) · address-data steward (which addresses need re-verification?).

### 3. Business objective
Raise the **right-door rate** and **eliminate notice-to-wrong-address events**, while reducing wasted field slots (₹220 marginal / ₹370 standalone `[MODEL]`). Distance error is a means, not the objective: a 90 m error in a dense colony can be one building wrong.

### 4. Address ingestion
Accept what CN actually holds: raw free text (one blob), optional PIN, city, landmark phrase, source, age, and any previously returned vendor coordinate. Reject nothing; classify confidence-of-input instead. Existing vendor output is stored as an **observation with provenance**, never as ground truth.

### 5. Multilingual normalisation
Deterministic-first (this is the honest lesson from the one Indian build we found `[EXT]`): abbreviation expansion (gali/lane, opp/opposite, nr/near), PIN extraction by regex anywhere in the string, comma/title normalisation, script detection, and transliteration variants for landmark matching. **No spell-correction layer**, because a wrong correction is worse than none. `[CUT]` libpostal/deepparse as a centrepiece — they are optional helpers, not the product (parsing is not the bottleneck: Shiprocket/Delhivery already resolve unstructured landmark addresses at national scale `[EXT]`).

### 6. Landmark / entity extraction
Extract (a) the landmark phrase, (b) its relation word (behind/near/opposite/next to/ke saamne), (c) ordinal or lane tokens ("2nd cross", "gali no 5"), (d) building/colony/complex names, (e) an optional PIN. Store all of them; the **landmark phrase is the validation key** for the later visit — if the returned GPS is near a POI whose name matches the phrase in the address, that is strong corroboration `[INFER]`.

### 7. Candidate generation
Consume a commercial geocoder (Delhivery Maps / Google Address Validation / Mappls eLoc) **at runtime, never cached as training data** `[EXT]`-ToS. Add OSM/POI context and a PIN-polygon check. Keep a small multi-hypothesis set (usually 1–5) rather than a single point. `[CUT]` a bespoke mulit-head H3 classifier — it duplicates what vendors already return.

### 8. GPS evidence model
For each returned visit, compute an **observation tuple**: (coordinate, timestamp, dwell seconds, distance to the address's current belief, arrival/departure context, outcome text, purpose classification, integrity weight). Observations are *evidence*, never labels.

### 9. GPS integrity model  ← the component that makes the learning safe
A per-observation credibility weight `w ∈ [0.2, 1.0]`, built from deterministic checks, not a black box:
| Check | Signal |
|---|---|
| Device attestation | mock-location flag, provider, reported accuracy — captured **at the moment of the visit** |
| Spatial plausibility | implied speed vs previous fix; inside the stated PIN/city at all? |
| Temporal plausibility | dwell vs reported visit duration; fix density during the claimed meeting |
| Cross-account duplication | same coordinate returned as "successful visit" for many unrelated accounts |
| Text–GPS agreement | does the remark's landmark resolve within X m of the coordinate? |
| Outcome economics | payment collected + receipt + OTP ⇒ high trust |
| Agent-level shrinkage | rolling duplicate/implausibility rate, shrunk to the population mean |
Fraud **degrades gracefully**: a poisoned observation is down-weighted and the radius **widens**; it never silently moves the belief. This is deliberately **not** a fraud-accusation system — output is a weight, not a verdict, because agents who fear grading will game harder `[INFER]`.

### 10. Home / work / shop classification
Purpose from: dwell distribution (home visits have long dwell, shop visits short and frequent), time-of-day profile (workday-hours at a workplace), POI context, outcome text ("met at shop", "house locked, neighbour said…"), and whether the coordinate is a *stop* on a multi-stop beat. Purpose changes the action: **a workplace or a shop is not a place to deliver a debt notice.**

### 11. Candidate ranking
`[CUT]` a LightGBM LambdaMART ranker in the MVP (candidates usually agree; ranking adds complexity without a decision change). Replaced by a transparent score: vendor confidence × PIN agreement × landmark-POI match × visit-evidence agreement. `[v2]` LTR returns only if candidate disagreement is shown to be frequent on CN's data.

### 12. Location estimation
Credibility-weighted **robust** estimate (weighted geometric median; Huber-style trimming). Explicitly **not** the mean: field GPS error is biased, not zero-mean `[EXT]` (Amazon's last-mile finding). Where the evidence is non-home, the estimate is produced for that purpose-tagged point, and the *residential* belief is left unchanged.

### 13. Confidence radius
Empirical quantiles of held-out error, computed per **stratum** (urban/rural, POI density, evidence count, purpose, whether the PIN agrees) rather than a global conformal claim. Output: `radius_90` (the width within which 90% of observed errors fell in that stratum) plus the evidence count. If the stratum has <30 observations, the radius is **widened to the parent stratum** and the output says so. `[CUT]` conformal coverage as a headline claim — unfalsifiable at small n and unnecessary for the decision.

### 14. Directions
Template-based, local-language landmark directions generated **on-device** ("Hanuman Mandir ke peeche, Sharma ration shop ke paas"), using the *original address text* plus the confirmed landmark set. No LLM call, no network. Directions are also the agent's **validation script**: "if you do not see a ration shop next to the temple, you are at the wrong place."

### 15. Offline architecture
Bundled per-district pack: the day's target list, each with pin + radius + landmark directions + the no-disclosure script + PIN/village polygons + a small local landmark list for fuzzy matching; SQLite + R-tree for spatial queries; write-ahead capture of GPS/dwell/outcome/attestation at visit time; delta sync on reconnect. Pack target <100 MB/district. Graceful degradation: a stale pack **widens** the radius visibly.

### 16. Feedback loop
Visit evidence → integrity weight → purpose classification → belief update → radius update → **tomorrow's notice/visit eligibility**. Alias learning: when a visit confirms a landmark phrase, the phrase↔coordinate pair enters the locality's landmark table, improving matching for **other accounts at the same landmark** (the compounding asset).

### 17. API design
```
POST /v1/address-confidence {address_text|address_id, purpose} ->
     {lat, lon, radius_90, confidence_tier, purpose_belief[], evidence_count, landmarks[], pack_id}
POST /v1/visit-evidence     {visit payload} -> {accepted, integrity_weight, belief_delta, new_radius}
POST /v1/notice-eligibility {account, address_id} -> {sendable: bool, reason, radius_at_decision, rule_version}
GET  /v1/directions/{address_id}?lang=hi&offline=1 -> {text, landmarks[]}
```

### 18. Database / PostGIS schema
```
address_raw(address_id, account_id, raw_text, pin_stated, city_stated, landmark_phrase, source, created_ts)
address_belief(address_id, purpose, lat, lon, radius_90, confidence_tier, evidence_count, updated_ts, model_version)
observation(obs_id, address_id, visit_id, agent_id, lat, lon, accuracy_m, provider, dwell_s,
            purpose, outcome_code, remark_text, integrity_w, ts)
landmark(locality_id, name_norm, phonetic_key, lat, lon, source  /*OSM | visit-confirmed*/, confirmations)
notice_gate_log(address_id, decision_ts, radius_at_decision, sendable, rule_version, decision_id)
```
PostGIS for point-in-polygon and distance queries; a `locality_id` (H3 or admin) keys the landmark table and the error strata.

### 19. Training pipeline
Weekly: recompute error strata and `radius_90` from held-out visits; re-fit the purpose classifier; refresh the landmark table; re-weight agent credibility. All on CN-held data. No vendor coordinate is ever a training label.

### 20. Inference pipeline
Fast path (online, <200 ms): cached belief + rule-based confidence tier — no model call needed for most addresses. Slow path (async): new/ambiguous addresses go to vendor geocoding + POI match, then the belief is cached. Nightly: rebuild the day's field lists and re-evaluate notice eligibility.

### 21. Monitoring
Abstention rate (tier=unknown) by locality · median and p90 radius by stratum · **notice-gate block rate and its reasons** · wrong-door reports from the field · integrity-weight distribution (a rise in low weights = an incentive problem, not a data problem) · stale-pack rate · drift in purpose classification.

### 22. Failure modes
| Failure | Detection | Fallback |
|---|---|---|
| No visits in a segment | evidence_count = 0 across the book | system returns vendor confidence only and **withholds the field/notice actions** |
| Landmark ambiguity (same name in two towns) | PIN disagreement, two clusters | require PIN agreement; otherwise tier = unknown |
| Borrower moved | repeated failed visits, "shifted" remarks | mark address stale → feeds PS2 as a contactability signal, not a geocode error |
| Vendor output unavailable | API error / ToS change | degrade to PIN centroid with tier = low and radius = locality width |
| Agents stop submitting evidence | observation volume drops | product problem, not model problem — surfaced to field ops with the agent-facing benefit |
| Gaming of check-ins | duplicate/implausible patterns | weight down and widen radius (never shift) |

### 23. MVP architecture (48 h)
Consume one vendor geocoder (or OSM fallback) → PIN-polygon check → landmark-POI match → empirical radius → **notice-eligibility gate** → offline pack (static file) → on-device directions template. `[CUT]` purpose classifier `[v2]`, `[CUT]` full integrity model (ship the three cheapest checks: mock-location flag, speed plausibility, duplicate coordinate), `[CUT]` LTR.

### 24. Production architecture
Polygon/POI store in PostGIS · district packs generated nightly and versioned · observation ingestion from CN's field app with attestation captured client-side · credibility service · landmark table governance with a human review queue for new aliases · notice-gate log feeding the compliance dashboard.

### 25. Demo architecture
One landmark-anchored address; a vendor pin with a 1.4 km radius that **blocks** the notice; a verification visit that returns a trail + dwell + remark; belief and radius update; the notice becomes sendable and the directions render **with the device offline**.

### 26. Evaluation metrics
**Address:** median/p90 error where ground truth exists (field-confirmed home visits only) · **abstention rate with tier** (the honest metric) · wrong-door rate from the field · notice-gate block rate.
**Learning:** does the radius actually shrink after visits, and does it *widen* when a poisoned observation is injected? (a test, not a claim)
**Business:** field-slot yield · avoided standalone trips · notices sent per verified address.
**Guardrails:** zero notices sent below the confidence threshold · zero visits to a purpose-tagged non-home point without an explicit rule.

*(Explicit limitation to state on every slide: all accuracy figures from synthetic or OSM-derived data are labelled synthetic and are **not** presented as real-world performance.)*

---

# Part VIII. The integrated product — workflow, demo, moat, 16 failure scenarios

*Source file: `PS2_PS3_INTEGRATED_PRODUCT.md`*

## THE INTEGRATED PRODUCT
#### A permission layer for the two irreversible actions in collections

---

## 1. The product in one paragraph

**SANKET/SUTRA is not a better dialer and not a better geocoder.** It is the layer that decides **whether a recovery action is permissible right now** — because the action is against an *unverified identity* (PS2) or at an *unverified location* (PS3) — and then proves that decision. Everything else in collections optimises *what to do*. This optimises *whether we are allowed to do it, and whether it is worth its cost* — and it learns from every visit that comes back.

**Positioning inside CreditNirvana:** a module behind Maestro. It makes Maestro's existing claims (*RBI compliant, audit trails, field efficiency*) **provable per decision** under the RBI framework effective 1 Jan 2027 and the TRAI rules notified 18 Sep 2026.

---

## 2. The product definition (Part-10 format)

| Dimension | Answer |
|---|---|
| **User** | Allocation/strategy analyst (nightly), supervisor (exception queue), compliance officer (evidence), field-ops manager (slot decisions), field agent (directions + script, offline) |
| **Problem** | "We are about to spend ₹220–370 on a visit, ₹60–150 on a trace, or send a legally-required notice — to an identity and an address we have not verified." |
| **Input** | Contact points with source/age · attempt telemetry · dispositions · payment history · field visit trails + dwell + remarks · address text + vendor geocode · cost table · rule config |
| **Intelligence** | P(contact) per point and window · P(right party \| answer) · an empirical confidence radius per address · purpose classification (home/work/shop) · integrity weight per observation · a hazard band for retest timing |
| **Decision** | An **eligible action set** (illegal actions removed, not penalised), scored by expected net recovery contribution, with `wait` and `suppress` as first-class options |
| **Action** | Auto/human call at a specified window · WhatsApp/SMS · identity-challenge call (no disclosure) · field verification task · field recovery visit · skip-trace purchase · notice dispatch (only if confidence ≥ ρ) · do nothing |
| **Feedback** | Outcome + telephony metadata + GPS trail + attestation + remark → observation with credibility weight → belief, radius, identity evidence and calibration all update |
| **Economic outcome** | Fewer wasted expensive actions; slot yield up; trace spend moved to accounts where EVSI is positive; human-agent hours pointed at accounts that move |
| **Compliance outcome** | Zero disclosure-capable actions below τ; zero notices below ρ; grievance/hardship suppression enforced; every decision reproducible from one record |

---

## 3. The workflow

```
        ┌──────────────────────────── NIGHTLY ────────────────────────────┐
        │ 1. Ingest outcomes (calls, payments, visits, complaints)         │
        │ 2. Rebuild features point-in-time; update beliefs & radii        │
        │ 3. Score: P(contact) · P(right party) · hazard band              │
        │ 4. Build the ELIGIBLE set per account (rules floor + gates)      │
        │ 5. Score candidates by ENRC (incl. wait, trace-as-information)   │
        │ 6. Emit: allocation deltas · field list · notice list · refusals │
        └──────────────────────────────────────────────────────────────────┘
                    │                    │                     │
        ┌───────────▼─────────┐ ┌────────▼─────────┐ ┌─────────▼──────────┐
        │ DIALER / MESSAGING  │ │ FIELD APP (PWA)  │ │ COMPLIANCE VIEW    │
        │ action + window     │ │ pin+radius+route │ │ decisions, blocks, │
        │ + script class      │ │ + script, offline │ │ conduct counters   │
        └───────────┬─────────┘ └────────┬─────────┘ └─────────┬──────────┘
                    │                    │                     │
                    └──────────┬─────────┘                     │
                               ▼                               │
        ┌────────────────── OUTCOME + EVIDENCE ─────────────┐  │
        │ ring/talk/cause/disposition/payment               │  │
        │ GPS trail + dwell + attestation + remark          │  │
        │ integrity weight → belief/radius → tomorrow's gate│──┘
        └───────────────────────────────────────────────────┘
```

## 4. The one causal loop we will actually demonstrate

```
 address text ─► vendor geocode ─► belief(lat,lon,radius=1,400m, tier=LOW)
                                          │
                        ┌─────────────────┴──────────────────┐
                        ▼                                    ▼
        NOTICE GATE: radius > ρ → notice BLOCKED    FIELD: is a verification
        VISIT: marginal ROI collapses at this       stop worth a slot? (₹220
        radius (p_wrongdoor high)                   marginal, information value)
                        │                                    │
                        └──────────────► VERIFICATION VISIT ◄┘
                                              │
                             GPS trail + dwell + "met borrower at home,
                             house 90 m from the temple, behind the ration shop"
                                              │
                                    integrity weight w = 0.94
                                              │
                    ┌─────────────────────────┴─────────────────────────┐
                    ▼                                                   ▼
        SUTRA: belief radius 1,400 m → 90 m; landmark phrase        SANKET: staleness flag cleared;
        CONFIRMED (poi match); tier LOW → HIGH                      identity evidence up; hazard re-estimated
                    │                                                   │
                    └───────────────────────┬───────────────────────────┘
                                            ▼
                    NOTICE now SENDABLE · VISIT now EV-positive and
                    route-marginal · tomorrow's action changes from
                    "call again (low value)" to "visit + notice"
                                            │
                                     DECISION RECORD
                    (why it was blocked before, what changed, which rule version)
```

**Why this is the demo and not the ROI slide:** the first half is a *refusal*, which almost no competing team will build, and the second half is an *evidence-driven reversal*, which requires both halves of the system to be real. It also happens to be exactly what RBI's 2026 framework forces lenders to be able to prove.

---

## 5. The 2–3 minute demo

| t | Beat | On screen | Line |
|---|---|---|---|
| 0:00–0:20 | **The trap** | `"Plot 14, behind Hanuman Mandir, near Sharma ration shop, 2nd cross, Gudgaon"`; vendor pin lands at the locality centroid; radius **1,400 m**; a **notice is scheduled** for tomorrow | "Under RBI's new conduct rules, the first visit needs a one-day advance notice. So this pin is about to send a recovery notice to a 1,400-metre circle in a dense colony." |
| 0:20–0:40 | **The harm** | A shop 1.3 km away receives it. Panel shows: FY24 **85,281** recovery complaints (+42.7%), harassment compensation cap now **₹3 lakh**, a lender fined **₹2.5 crore** for agent conduct | "If the notice lands at the wrong door, a third party learns about the debt before we ever visit. That is not an inefficiency. That is the exposure." |
| 0:40–1:05 | **The refusal** | The system **blocks the notice and the visit** for the same account — while two other accounts in the queue are approved. Show the blocking record: `NOTICE_GATE: radius 1,400 m > 400 m (ρ, config v7)`; `IDENTITY_GATE: p_right_party 0.42 < 0.90` | "It refuses. It will not send the notice, and it will not spend a ₹220 slot. Most systems will happily do both." |
| 1:05–1:35 | **The evidence arrives** | A verification stop on the agent's existing beat — the agent is already 900 m away. The app was **offline**; directions rendered from the pack. Return: trail, 34-minute dwell, remark *"met borrower at home, house 90 m from the temple, behind the ration shop"*, one payment receipt for ₹2,000 | "It didn't cost a special trip. It cost a stop on a beat the agent was already running." |
| 1:35–2:05 | **The reversal** | Radius **1,400 m → 90 m**; landmark phrase **confirmed** against a POI; tier LOW → HIGH; integrity weight 0.94. The gate **reopens**: notice now sendable, visit EV-positive, route-marginal | "One verified visit. The address the geocoder never resolved is now the best-resolved address in the district — and it will help every other borrower at that same landmark." |
| 2:05–2:25 | **The proof** | Open the decision record: rule versions, probabilities, the blocked candidates and the exact rule that blocked each, chosen action, propensity. Counter: **"0 notices sent below confidence this month."** | "Every decision is one row. A compliance officer can audit any of them, months later, and see what the system prevented." |
| 2:25–2:40 | **The anti-hype beat** | Inject a faked check-in: implausible speed + a coordinate already returned for six unrelated accounts → the estimate **does not move**; the radius **widens**; the observation is flagged for review, not accused | "Field data is not truth. We weight it — so a fake check-in widens our uncertainty instead of poisoning the map." |
| 2:40–3:00 | **Close** | "Never disclosed to a stranger. Never sent a notice to a wrong door. Never spent a slot on an address we can't defend." | "PS2 decides who we may speak to. PS3 decides where we may go. Together they decide what we are allowed to do — and they get better every time an agent walks to a door." |

**Fallback if the venue network dies:** the entire field half runs offline from the bundled pack; the notice-gate record and the belief update are on-device.

---

## 6. Level 1 — 48-hour hackathon MVP (only what increases win probability)

| # | Component | Why it stays |
|---|---|---|
| 1 | Synthetic CN simulator (accounts, contact points, attempts, visits, remarks, fakes) with the exact schema | Nothing else is demonstrable without labels; doubles as the rehearsal environment |
| 2 | Rules floor (08:00–19:00, borrower/guarantor, grievance/hardship suppression, caps, DND, ≥90-day recycling heuristic) | It is the compliance story and it is deterministic — no training needed |
| 3 | Two calibrated models: P(contact) and P(right party) | Just enough to make the identity gate non-arbitrary |
| 4 | EV gate with `wait` and a priced trace | The problem statement's explicit requirement |
| 5 | Address belief + empirical radius + **notice gate** | The hero of the demo |
| 6 | Integrity weight from **three** deterministic checks only (mock-location, speed plausibility, duplicate coordinate) | Makes the "fake visit" beat real without building a model |
| 7 | Offline pack + on-device directions template | One static file; the visual proof of "works with no network" |
| 8 | Decision record + one audit screen | The compliance claim becomes checkable |
| 9 | One screen, three states (blocked → evidence → unblocked) | The demo |

**Explicitly cut:** hazard/survival model, graph features, LTR ranker, purpose classifier, purpose-of-address model, route optimisation, multi-page dashboards, SHAP UI, any user accounts, any cloud dependency.

---

## 7. Level 2 — competition-final version

Adds: hazard model for retest timing · purpose classification (home/work/shop) with the derived rule *"never deliver a notice to a non-home purpose"* · full integrity model with agent-level shrinkage · per-stratum radius with sample-size guards · IPW-corrected training metrics · field route with time windows (OR-Tools) computing **marginal** visit cost · an off-policy evaluation vs the synthetic legacy policy · a monitoring panel (ECE per segment, abstention rate, notice-gate block rate, refuse reasons) · 30-day pilot design with pre-registered counters.

---

## 8. Level 3 — production roadmap inside CN

Phase 0 (weeks 1–2): data contracts + rule-config service + decision-record table in CN's environment.
Phase 1 (weeks 3–8): real telephony/label ingestion, calibration on CN's book, notice gate live for one region, field packs for two districts.
Phase 2 (months 3–6): purpose classifier, integrity model, radius strata per district, Landmark table governance with a review queue, DPDP documentation (DPIA, retention, erasure workflow), model cards.
Phase 3 (months 6–12): graph features and LTR **only if they clear a measured-lift gate**; route optimisation coupled to the confidence output; conduct dashboard as a client-facing artefact; extension of the same evidence loop to repossession/legal workflows where the notice problem is identical.

---

## 9. Competitor-defensible story — "why can't CreditNirvana just build this?"

It can. So the honest answer is **what makes it hard**, ranked by durability:

| # | Moat | Strength | Why |
|---|---|---|---|
| 1 | **Field-outcome address evidence** | **Strongest** | Requires a live field force producing *recovery* visits, with the integrity problem solved. Shiprocket/Delhivery cannot substitute: delivery evidence is a different process with different failures. Competitors without a field force cannot buy this |
| 2 | **Permission ledger (decisions + blocks)** | Strong | Its value comes from being *the* record in a regulatory inspection. Whoever holds it first in a lender's stack is the reference implementation |
| 3 | **Rule-config ↔ decision coupling** | Medium-strong | Regulatory change lands as config, not code. Vendors who hard-code conduct rules will lag each amendment cycle |
| 4 | **Landmark gazetteer per locality** | Medium | Compounds with coverage; but reachable by anyone with visits (and partially by OSM) |
| 5 | **Calibrated radius logic** | Weak-medium | Reproducible; the hard part is the evidence stream, not the maths |
| 6 | Contact models / geocoding | **Weak** | Commoditised (TransUnion PBI; vendor geocoders) |
| 7 | Dashboards, workflows, UI | None | CN already ships 80+ |

**Conclusion for the pitch:** the moat is **the evidence loop plus the audit position**, not the models. Say that out loud — it is more credible than claiming algorithmic secrecy, and it explains why the *first* field-verified portfolio wins.

---

## 10. Failure scenarios (16)

| # | Scenario | What a naive system does | What ours must do | Detection | Fallback | Business impact | Compliance impact |
|---|---|---|---|---|---|---|---|
| 1 | Recycled phone | Keeps dialling; reaches a stranger | Challenge-only path; no disclosure; flag for correction | ≥90-day silence + discontinuity + cross-account conflict | Suppress disclosure actions; queue a trace | Wasted attempts, no recovery | **Disclosure event avoided** |
| 2 | Shared family phone | Treats any answer as RPC | Identity head; no-disclosure script if unconfirmed | Answer profile + transcript + identity conflict | Message-only | Attempts spent | Third-party exposure avoided |
| 3 | Borrower moved | Visits a stale address repeatedly | Mark address **stale** → contactability signal to PS2 | Repeated failed visits + "shifted" remarks | Re-verify, do not visit | Field slots saved | Wrong-door notice avoided |
| 4 | Wrong address in the file | Sends notice; visits | Notice **blocked** below ρ | PIN/landmark disagreement, wide radius | Verification stop | ₹220–370 per slot + officer time | **Notice disclosure avoided** |
| 5 | Agent fakes a check-in | Learns the faked coordinate | Weight down; radius **widens**; estimate does not move | Speed implausibility, duplicate coordinate, dwell vs duration | Observation quarantined | Map integrity preserved | — |
| 6 | Agent meets borrower at his workplace | Marks workplace as home | Purpose = work; never deliver a notice there; ask for the home landmark | Purpose classifier + POI + time-of-day | Ask for a home landmark | Better next visit | Home address not exposed at workplace |
| 7 | Landmark ambiguity ("Hanuman Mandir") | Resolves to the nearest temple | Require PIN/landmark agreement; else tier = unknown | Two clusters, PIN disagreement | Abstain, verify | Avoided wasted slot | Avoided wrong-door |
| 8 | Same landmark, different town | Single global name match | Locality-scoped landmark table | PIN/city mismatch | Abstain | Avoided mis-travel | — |
| 9 | No answer, 12 attempts | Keeps dialling (or traces on count) | Hazard-based backoff; priced trace decision | Hazard near zero, attempts climbing | Wait; retest at hazard peak | Cost per recovery down | "Excessive calls" avoided |
| 10 | Deliberate avoider | Codes as dead | Different window/CLI probe **within the planned attempt** | Call-reject rate, window selectivity | Switch channel | Recovers a recoverable account | — |
| 11 | Third party answers | Discusses the debt | Never in the candidate set | Identity gate | Challenge script | — | **The core control** |
| 12 | Old successful contact (2 years) | Treats as valid | Age-decayed, re-verification required | Supplier age + failure since | Re-verify | — | — |
| 13 | **Model confident but wrong** | Acts on 0.93 and discloses | Asymmetry: expensive/irreversible actions need higher confidence; cheap reversible ones recover the truth | Calibration monitors per segment; supervisor sampling | Reversible-first ordering | Small recovery loss | Bounded harm |
| 14 | Field visit expensive but highly informative | Skips it on cost alone | Price the information: allow the stop when it is marginal to a beat and the account value supports the option | VoI term in ENRC | Alternative: cheap verification channel | Option value captured | — |
| 15 | Low-value account, high trace cost | Traces anyway (rule) | EVSI says no; close or drip | π·k·ΔRPC·value < fee | Suppress | ₹60–150 saved per account | — |
| 16 | Regulatory amendment lands mid-month | Code change backlog | Config version bump; disclosure actions freeze until reviewed | Config-review SLA monitor | Freeze disclosure actions | Brief throughput dip | Compliance preserved |

---

## 11. What we will **not** do (so the scope stays honest)
Not building a dialer · not building a geocoder · not competing on offer/negotiation (CN's layer) · not claiming accuracy on synthetic data · not shipping GNN/sequence/bandit/lift models in the MVP · not building a customer-facing UI · not purchasing new personal data for the demo · not asserting compliance from logs alone.

---

# Part IX. Novelty matrix — what is actually new

*Source file: `NOVELTY_MATRIX.md`*

## NOVELTY MATRIX

**Rule applied:** novelty is not claimed because our architecture has many components. It is claimed only where **a specific existing system does the adjacent thing and still cannot produce our outcome**. Five candidate novelty directions were enumerated, scored, and ranked. Two were rejected outright because the research showed they already exist commercially.

---

### 1. The five directions, with the evidence that ranks them

| # | Novelty direction | Existing industry solution that does the adjacent thing | What it does | Our approach | **Why existing systems don't already do it** | Technical moat | Data moat | Workflow moat | Economic moat | Compliance moat | Demonstrability | Difficulty to copy |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **N1** | **Notice/visit gated on modelled *address confidence*** | Delhivery GeoNaksha returns an **error radius**; Mobicule/Credgenics geo-tag visits | Returns a coordinate + radius; records where the agent went | The radius is a **gate**: below a threshold, the RBI-mandated advance notice and the visit are **not generated at all** | Geocoding vendors have no stake in *whether an action is lawful*; collections platforms treat geo-tagging as proof-of-visit, i.e. the decision is already made before geo data is consulted | Low (arithmetic) | **High** — needs field-visit evidence per address | **High** — must sit inside the allocation/notice workflow | **High** — converts geo uncertainty into avoided notices/visits | **Very high** — directly implements the 2026 advance-notice rule | **Very high** — the blocked notice is a 20-second visual | Hard for a geocoder (no workflow); easy for a collections platform *once it thinks of it* |
| **N2** | **Identity gate: disclosure-capable actions removed from the candidate set** | TransUnion **Contact Compliance Risk**; Skit.ai RPC verification in-call; script-level guards | Verifies identity **during or before** the call; flags compliance risk | Modelled P(right party) **structurally excludes** the action; the audit shows the constraint that removed it | Vendors verify *after* the call connects; law firms and DBs see compliance as a property of the *call*, not of the *decision* | Low | Medium | High | High (avoided conduct cost) | **Very high** | **High** — two accounts, same connect probability, opposite allowed actions | Medium |
| **N3** | **Integrity-weighted field evidence (anti-poisoning by widening, not rejecting)** | Mobicule: geo-fencing, liveness, "prevent location spoofing" | Detects/penalises fraudulent check-ins | Fraud **degrades gracefully**: the observation is down-weighted and the confidence radius **widens** instead of the belief shifting | Fraud systems are punitive and binary; geographic systems assume observations are true or junk — nobody formalises *credibility as a weight on belief* | Medium | High | Medium | Medium | Low–Medium | **Very high** — inject a fake check-in live and show the estimate not moving | Medium |
| **N4** | **Priced skip-trace (EVSI) instead of attempt-count triggering** | SkipTracer.in; TruLookup; every dialer vendor's "smart trace" | Finds updated contacts faster; traces at a configured cadence | Trace fires only when **expected information value > fee**, computed per account | Trace vendors monetise volume; platforms configure a cadence. Neither has an incentive to *suppress* trace volume | Low | Medium (needs our own trace-yield history) | Medium | **High** | None | High — move the price slider and watch decisions flip | **Low — easiest to copy** |
| **N5** | **Contact-point-level, censoring-aware health with a rules floor** | Account-level propensity models everywhere; contactability scores (Spocto, TransUnion PBI) | Scores accounts or phone numbers | Scores **each point on a slate**, never-tested points **censored not failed**, with a deterministic floor that can veto | Contactability scoring is account/identity-centric; slates are an operations concept, not a data-product concept | Medium | Medium | High | Medium | Low | Medium | Medium |

#### Rejected novelty claims (research killed them)
| Claim we nearly made | Why it is dead |
|---|---|
| "An address engine that learns from field outcomes" | **Shiprocket Address Intelligence**: learns from every successful delivery and correction; claims 72.69% <100 m, 90.57% <500 m `[PUB]` |
| "Calibrated uncertainty from a geocoder" | **Delhivery GeoNaksha returns an error radius**; Google returns component-level accuracy `[PUB]` |
| "Distinguishing residential from commercial addresses" | **Google Address Validation for India already does this** `[PUB]` |
| "Predicting which number is right, and when to call" | TransUnion **Phone Behavior Intelligence claims +33% RPC**; Spocto markets contactability; every dialer vendor claims timing uplift `[PUB]` |
| "Using field GPS to improve routing" | Mobicule and Credgenics sell AI beat plans and geo-tagged visits today `[PUB]` |

---

### 2. Ranking (weighted: compliance 25%, data moat 20%, demonstrability 20%, workflow 15%, technical 10%, economic 10%)

| Rank | Direction | Score | Verdict |
|---|---|---|---|
| **1** | **N1 — confidence-gated notice/visit** | **4.6 / 5** | The hero. Maps to a brand-new legal obligation, is visually undeniable, and requires the field-evidence stream that a geocoder cannot have |
| **2** | **N2 — identity-gated eligibility** | **4.4 / 5** | The co-star. Makes the compliance claim structural rather than aspirational, and it is the only part that applies to **every** portfolio, including pure automated digital |
| **3** | **N3 — integrity-weighted evidence** | **3.8 / 5** | The credibility move. Turns "we built a learning geocoder" into "we built one that cannot be fooled" — and it is the piece a judge remembers |
| **4** | **N5 — contact-point slates with censoring** | **3.2 / 5** | Real but explainable in one sentence; a supporting argument, not a headline |
| **5** | **N4 — priced trace** | **3.0 / 5** | Genuinely required by the problem statement and impressive in a slider, but trivially copyable |

---

### 3. The honest novelty statement (use this verbatim)

> We are not claiming a better geocoder or a better RPC model — both are mature markets with strong incumbents. We are claiming the **first implementation of a permission layer that sits between prediction and action in Indian collections**: an action that would disclose a debt is not in the candidate set unless the identity is verified to a modelled threshold, and a recovery notice or visit is not generated unless the address confidence clears a threshold — and both refusals are recorded, with the rule that caused them, in the same record that proves the action was allowed. The field evidence that unlocks those refusals is weighted by an integrity model, so the system cannot be taught the wrong address by a fake check-in.

**Why it is credible:** every element of that sentence maps to a system that exists (geocoder, dialer, identity check, geo-tagged visit) but none of which connects them to *permission*. And every element maps to a rule that is now enforceable: 08:00–19:00, borrower/guarantor only, one-day advance notice, no contact during hardship `[EXT]`.

**Why it is not "AI-powered" fluff:** the claim is falsifiable in one click — block the notice, show the rule, unblock it after evidence, show the record.

---

# Part X. Financial model

*Source file: `PS2_PS3_FINANCIAL_MODEL.md`*

## PS2 / PS3 — FINANCIAL MODEL

*Illustrative model, deliberately conservative, sensitivity-tested. Companion script: `financial_model.py` (run it: `python3 financial_model.py`); raw output: `financial_model_output.txt`.*

**Labelling used everywhere:** `[PUB]` published/claimed · `[EXT]` external data point · `[ASSUME]` our assumption · `[MODEL]` computed. **No number here measures CreditNirvana's actual portfolio.**

---

### 1. The three findings that changed our product scope

1. **Dial volume is not where the money is.** An automated dial costs **₹1.35–2.60**; a field visit costs **₹220–370**; a trace **₹60–150** `[MODEL]`. That is a **185× spread**. Any effort spent optimising dial volume is worth **₹0.3–7 lakh/month** on a 100,000-account book — i.e. nothing. *We deleted dial optimisation from the value story.*
2. **The economics are ticket-conditional.** Field-visit ROI: **0.65× marginal / 0.38× standalone at a ₹5,000 ticket**; **2.43× / 1.45× at ₹18,802**; **19× / 12× at ₹1.5 lakh**; **104× / 62× at ₹8 lakh** `[MODEL]`. A single story cannot cover a digital-PL book and a vehicle-finance book. *Deployment becomes segment-conditional.*
3. **Trace is a 30× uncertainty business.** Trace EV at the average ticket spans **₹7–204 per case** against a **₹60–150 fee** `[MODEL]`, driven by yield (35–60%) and RPC uplift of a new point (6–14 pp). *A rule cannot fire this correctly — which is exactly the problem statement's point, and it is also why our own trace claim must be modest.*

---

### 2. Cost structure of each action

| Action | Cost | Basis |
|---|---|---|
| Automated dial (voice-AI 60–75 s, connect ~28%) | **₹1.35–2.60** | `[PUB]` India voice-AI ₹4–7/min + ₹0.55/min telephony; `[MODEL]` blend for non-connects |
| Human-agent dial | **₹8.48** | `[PUB]` agent salary ₹15,788/mo median (Indeed) + ~75% loading; `[ASSUME]` 3,300 dials/mo |
| HLR / number intelligence | **₹0.13–0.60** | `[PUB]` Telnyx $0.0015/dip; Neutrino $0.007; Twilio $0.005–0.04 |
| SMS / WhatsApp utility | **₹0.15–0.25** | `[PUB]` WhatsApp utility pricing |
| Skip-trace (data purchase) | **₹60–150** | `[EXT]`-anchored: global bulk $5–25/record; US one-off $50–175 |
| Field visit — **marginal** (on an existing beat) | **₹220** | `[MODEL]` ₹130 labour + ₹90 travel |
| Field visit — **standalone trip** | **₹370** | `[MODEL]` ₹130 labour + ₹240 travel |
| Voice-AI per resolved outcome | ₹8–25 | `[PUB]` India outcome-based pricing |

**Cost per RPC:** ₹5–14 automated (₹9–24 per *productive* RPC at 60% paying) · **₹32–47 per RPC on a human call** `[MODEL]`. A human call is **4–8× the cost of an automated connect** — which is why human minutes, not dials, are the scarce resource worth optimising.

---

### 3. Value pools (monthly, 100k accounts / ₹188 Cr book at ₹18,802 ticket `[PUB]` FACE, 1–30 DPD)

| Pool | Monthly value | Note |
|---|---|---|
| **VP-1 Dial-volume optimisation** | **₹2,700–25,900** | Listed first *so that nobody funds it*. 1–5 pp of dials avoided |
| **VP-2 Scarce-capacity arbitrage** — field slots | **₹9.4–42.4 lakh** | 6,600 slots/mo `[ASSUME]`; +10–45 pp slot-level success from better address confidence + timing |
| **VP-2b** — human-agent conversations | **₹3.4–14.7 lakh** | 33,000 conversations/mo `[ASSUME]`; +5–12 pp RPC × ₹205 incremental recovery per RPC |
| **VP-3 Wasted expensive actions** | **₹1.5–8.6 lakh** | 10–35% of field slots spent on wrong-door / low-confidence addresses |
| **VP-4 Conduct exposure** | see §5 | Bounded, probabilistic, and the pool a CFO funds without an ROI debate |
| *(reference)* 1 pp of connect rate | **₹5.01 lakh** | `[MODEL]` at ₹205 incremental recovery per RPC |

---

### 4. Incremental recovery per RPC — the assumption that decides everything

```
E[gross recovery | RPC] = P(pay | RPC)     0.20–0.30   [ASSUME]
                        × payment fraction 0.20–0.30   [ASSUME]
                        × ticket           ₹18,802     [PUB]
                        = ₹752 – ₹1,692  (mid ₹1,183)
E[INCREMENTAL recovery | RPC] = gross × incrementality 0.20–0.35  [ASSUME]
                             ≈ ₹205 at the midpoint
```
**Why we use the incremental figure:** most 1–30 DPD accounts that pay would have paid anyway (15–25% self-cure `[EXT]` vendor-published). Using gross recovery inflates every benefit by ~4×. **If CN has better numbers, this single assumption changes the model more than any other** — it is question B1 in `CN_QUESTIONS.md`.

---

### 5. Conduct exposure (the part a lender funds without argument)

| Element | Value | Source |
|---|---|---|
| FY24 RBI Ombudsman complaints (loans/recovery) | **85,281**, +42.7% YoY, ≈29% of all complaints | `[PUB]` |
| Harassment/mental-anguish compensation cap (RB-IOS 2026) | **₹3,00,000** (was ₹1,00,000); 90-day filing window | `[PUB]` |
| Lender penalty precedent | **₹2.5 crore** against Bajaj Finance for agent conduct — the **lender** pays | `[PUB]` |
| Our model | 5% of dials reach a wrong party; 0.2–1.0% of those escalate at ₹15k–75k expected cost → **₹3–75 lakh/month** on a 100k book | `[MODEL]` |

**Framing rule:** call this *avoided exposure*, never "savings". The lumpy ₹2.5 crore penalty class dwarfs the compensated amounts, which is why the budget is defensible even though the expected value is bounded.

---

### 6. Trace and visit ROI by ticket size

| Ticket | Visit ROI (marginal) | Visit ROI (standalone) | Trace EV (vs ₹60–150 fee) |
|---|---|---|---|
| ₹5,000 | 0.65× | 0.38× | ₹2–54 → **negative** |
| **₹18,802 (digital-PL average)** | **2.43×** | 1.45× | ₹7–204 → **indeterminate** |
| ₹50,000 | 6.47× | 3.85× | ₹18–541 → positive if yield is good |
| ₹1,50,000 | 19.4× | 11.6× | ₹54–1,624 → positive |
| ₹8,00,000 | 103.6× | 61.6× | ₹289–8,663 → clearly positive |

**Decision consequence:** in small-ticket books, both visits and traces must be priced per account and, for visits, evaluated **marginally to an existing beat**. In large-ticket books, the discipline is route efficiency, not go/no-go.

---

### 7. Break-even at a price

One percentage point of connect rate is worth **₹5.01 lakh/month** on this book `[MODEL]`.

| Price | Monthly cost | Improvement needed |
|---|---|---|
| ₹1 / account / month | ₹1.0 lakh | **+0.20 pp connect**, or ~**455 avoided field visits/month** |
| ₹3 / account / month | ₹3.0 lakh | +0.60 pp connect, or ~1,364 avoided visits/month |
| ₹5 / account / month | ₹5.0 lakh | +1.00 pp connect, or ~2,273 avoided visits/month |

**This is the most important number in the deck.** The product does not need a heroic claim — it needs a **demonstrable** one. If we cannot show avoided expensive actions and avoided exposure on real accounts, no model quality will save the ROI story.

---

### 8. Which decision produces the largest financial impact?

| Rank | Decision | Value per pp | Why it ranks here |
|---|---|---|---|
| 1 | **P(pay \| RPC)** — offer/agent/script | ₹7.4 L/month per pp | Largest, cheapest lever — **and it belongs to CN's existing Maestro layer. We must not claim it** |
| 2 | **Connect rate** via timing/contact point | ₹5.0 L/month per pp | Ours, but shared with every dialer vendor's claim |
| 3 | **Identity gate** (right-party share + avoided conduct) | ₹2.0 L/month per pp *plus* avoided exposure | Ours, defensible, compliance-anchored |
| 4 | **Field-slot success** | ₹0.94 L/month per pp | Ours via PS3; small per pp but directly controllable |
| 5 | **Trace yield** | ₹0.01 L/month per pp | Small per pp; the win is *avoided negative-EV traces*, not yield |

**Answer to "which decision moves the most money":** *the offer layer does — which is why we do not touch it.* Within what is defensibly ours, the biggest movers are **connect timing, the identity gate and field-slot quality**, and all three are best expressed as **avoided waste and avoided exposure on expensive actions**.

---

### 9. What the model cannot tell us (stated plainly)
- Whether CN's portfolio looks like this book (ticket, DPD mix, field intensity) — **unknown**.
- Whether field visits are frequent enough to train an address learner in the target segment — **unknown, and material to PS3**.
- Whether the trace fee in India is ₹60–150 (**our estimate**), and whether vendors charge per hit or per query.
- The true incremental-recovery-per-RPC — the single biggest swing factor.
- Anything about borrower-experience cost (complaints, NPS, attrition), which we have deliberately left out of the ROI rather than invent.

**Pilot counters we would pre-register (30 days, one region):** field-slot yield · standalone-trip share · notices blocked below confidence · traces ordered and their realised yield · wrong-party contacts · complaints · cost per RPC · cost per productive RPC · cure/roll-back rate in bucket.

---

# Part XI. Data strategy — A / B / C / D

*Source file: `PS2_PS3_DATA_STRATEGY.md`*

## DATA STRATEGY — A / B / C / D, per feature

**A = CN-provided** · **B = public / open / licensable** · **C = synthetic** · **D = must-not-fabricate**

Universal rules applied throughout:
1. **Never present C as measurement.** Every synthetic-derived output carries a `SYNTHETIC` marker in the API payload, the console and the deck.
2. **D is a hard line.** We would rather abstain than invent. Where a label or an input is unavailable, the product abstains (blocks the action) rather than guessing — abstention is the compliant default, not a failure.
3. **No new personal data purchased for the demo.** Enrichment in the demo is limited to what CN already holds.
4. **Immutable exclusions:** Bhuvan/ISRO (ToS); commercial geocoder output may be used **at runtime** but **must not be stored or cached as training data** (licence + DPDP minimisation).
5. **Minimum-necessary data** for every feature, with retention tied to the recovery record's life, and a documented lawful basis per processing purpose.

---

### 1. SANKET (PS2) features

| Feature | A — CN-provided | B — public / licensable | C — synthetic | D — must-not-fabricate | What cannot be concluded from C |
|---|---|---|---|---|---|
| Contact slate (points + type) | Telephony/CRM number records per account | — | Generated slate with realistic type mix | Which number actually belongs to the borrower today | Any claim of contactability improvement |
| Outcome label per point (answered / RPC / paid) | Dispositions at **point level** — *exists only if CN logs it; Q5 in `CN_QUESTIONS.md`* | — | Plausible outcome mixes | Never infer a "contact" that did not occur | RPC lift, calibration, AUC — all meaningless on synthetic labels |
| P(connect) features | Time-of-day history, attempt history, operator/HLR class | HLR/dip lookup at runtime (paid, no storage) | Simulated | Carrier-level facts we did not look up | Operator-level effects |
| P(right party) labels | Agent-verified identity events (OTP / DOB / last-4 result) | — | 3-class synthetic outcome | Identity of any real person | True wrong-party rate |
| Payment / cure labels | LMS payment postings, roll-back | RBI/CIBIL **aggregate** cure rates for sanity checks only | Simulated payment timing | Individual payment behaviour | Incremental value of contact |
| **Incumbent policy propensity** (what the old system did) | Prior allocation/attempt logs with timestamps | — | n/a | This one **cannot be synthesised** — without it, the model learns collector behaviour instead of contact health | Any causal claim about our own model |
| Trace outcomes (ordered → hit → productive) | Vendor invoices + post-trace contact results | — | Simulated yield | Whether a trace would have been productive | Trace EVSI, ROI |
| Complaints / conduct events | Grievance log per account | RBI ombudsman **aggregates** (`[PUB]` 85,281 in FY24) | n/a | Attribution of a complaint to an action | Financial value of avoided conduct (we can only cite the mechanism and the penalty precedent) |
| Attempt-suppression state (hardship, grievance open, bereavement) | Collections CRM flags | — | Scripted states for the demo | Whether a borrower is in hardship | — |

**Decision rule:** if A is missing for labels, SANKET ships as **shadow mode first** (recommendations logged, humans decide) and no accuracy number is published.

---

### 2. SUTRA (PS3) features

| Feature | A — CN-provided | B — public / licensable | C — synthetic | D — must-not-fabricate | What cannot be concluded from C |
|---|---|---|---|---|---|
| Raw address record | Origination KYC address + application address + prior notices | — | Fuzzed addresses in real formats | That the recorded address is where the borrower lives | — |
| Geocode candidates + error radius | — | **Commercial geocoder at runtime** (Google / Mappls); radius/confidence per provider | Cached-at-runtime-in-memory only, never persisted as training data | A "validated doorstep" | True containment rates |
| Field check-in evidence (GPS, accuracy, dwell, photo hash) | Field app DB — *exists only if CN captures it; Q7* | — | Scripted check-ins incl. one spoof | That an agent actually stood at the door | Learning-loop value: **if CN has no historical visit GPS, SUTRA has no learner and must be re-scoped to gate-only. We will not simulate a learning curve and call it a result.** |
| Purpose label (home / work / shop) | Agent remarks, visit outcomes | Open POI data for landmark typing | Weak-labelled synthetic set | A person's home | Purpose-classification accuracy |
| Landmark table | Agent-captured landmark text ("behind Hanuman Mandir") | OpenStreetMap POIs (ODbL attribution; no Bhuvan) | Synthetic names in real dialects | — | Landmark resolution quality |
| Integrity signals | Device ID, app version, timestamp, prior-stop sequence | — | Scripted flags | Device-level assertions about a real collector | Anti-spoof effectiveness |
| Radius calibration (`radius_90` by stratum) | **Visit outcomes against geocoded positions — the only real source** | — | Cannot be validated synthetically | Containment that we have not measured | The whole uncertainty claim |
| Notice / visit outcome (served / refused / wrong-door) | Field app + notice register | — | Scripted | — | Avoided-waste ₹ |

---

### 3. Minimum viable data ask (the honest version)

**If CN gives us only two things, these are them:**
1. **Field-visit GPS + outcome at visit level** (SUTRA's learning loop),
2. **Point-level contact dispositions with the incumbent policy's attempts** (SANKET's labels and the propensity correction).

Without (1) SUTRA becomes a geocode + notice-gate product (still valuable, still novel in the permission sense, but no learner). Without (2) SANKET cannot claim any improvement over a rules floor and should ship as the identity gate + EV gate only — which is still the part that maps to the RBI framework.

---

### 4. Data-protection posture (short form)
- Lawful basis per purpose documented; geospatial inference and profiling are separate purposes from servicing.
- Field-agent location is **employee/work-device** data: purpose limitation, no continuous tracking outside the visit window.
- No training on commercial geocoder responses; no re-identification attempts on third parties; no contact data for non-borrowers as a *target*.
- Erasure vs retention conflict: the recovery record (audit) and the address evidence (product) must have documented, different retention clocks.
- Every pilot artefact that leaves CN's environment is aggregate-only.

**One sentence for the deck:** *our data strategy is to abstain where we cannot measure, and to measure only from evidence CN actually owns.*

---

# Part XII. Questions for CreditNirvana

*Source file: `CN_QUESTIONS.md`*

## CN_QUESTIONS.md — ranked questions for CreditNirvana

**Rule for this list:** every question is here because **the answer changes our architecture, our scope, or our ROI claim**. Questions we can answer ourselves from public sources are omitted. Nothing here is a sales question.

---

### Table A — Questions that can kill or reshape the design

| # | Q | Cat | Why it changes architecture |
|---|---|---|---|
| **1** | Which portfolio would this pilot run on — product, ticket band, DPD bucket, field-bearing or not — and what is the **actual average outstanding**? | DATA | Everything in §6 of the financial model is ticket-conditional. A digital-PL book (₹18.8k) and a used-car book (₹3–8 L) need different products; below ~₹15k, visits and traces stop being self-funding |
| **2** | **How many field visits per month, per collector-day, and what fraction are "standalone" trips** vs stops on an existing beat? | DATA | Determines whether per-visit ROI is marginal (₹220) or standalone (₹370) and whether the field learner has enough monthly volume to learn anything |
| **3** | What is **incremental** recovery per RPC (i.e. what would these accounts have paid anyway)? What is the current measured self-cure in the target bucket? | DATA | The single biggest swing factor in the model (§4). Without it every ROI number we publish is a guess |
| **4** | Of an identity-verified contact, what is the **right-party verification method today** (OTP, DOB, last-4, agent judgement), and what is the measured **wrong-party rate**? | DATA | The identity gate's threshold and the audit record both depend on it |
| **5** | Does CN already receive **call dispositions at contact-point level** (which number answered, at what time), and can that be modelled without changing the agent desktop? | DATA | PS2's core label needs point-level dispositions; if dispositions are account-level only, PS2 loses its best feature set |
| **6** | What **geocoder licence** does CN hold today (Google / Mappls / Ola / none), and what are the terms on **storing** returned coordinates? | DATA | Governs whether our runtime-only geocoding design is implementable, and whether we may persist coordinates at all |
| **7** | Does CN capture **GPS at the moment of the field visit**, with accuracy radius, dwell time, and a photo of the door/address? Can we read historical visit claims? | DATA | This is the *only* proprietary input that a commercial geocoder cannot have. If it does not exist, PS3 must be re-scoped to "geocode + notice gate", with no learning component |
| **8** | Which **field-workforce model** applies to the accounts we would pilot — own agents, empanelled agencies, or both? Who controls the mobile app the agent uses? | DATA | Determines whether an agent can be asked to confirm an address, and whether we can trust their claim (it is also the answer to "who is incentivised to fake a check-in") |

---

### Table B — Business questions

| # | Q | Cat | Why it changes the design |
|---|---|---|---|
| **9** | Is the commercial model **per account / per seat / per visit / outcome-based**? What has CN previously charged for a data product? | BUS | Sets the break-even target (§7). At ₹1–3/account the product must earn its keep on avoided visits alone |
| **10** | In the pilot region, what is the **cost per field visit** all-in, and is the marginal travel cost treated as free because agents already move through the beat? | BUS | Decides whether we optimise visits as go/no-go or as routing |
| **11** | Who signs off on **suppressing** a legal notice on modelled grounds? Does a credit officer or legal team have to approve a "do not serve notice" state? | BUS | Determines whether the notice gate is a hard block or an advisory flag — a compliance-driven product decision, not an ML one |
| **12** | Is there an existing SLA on notice delivery (e.g. within N days of bucket entry) that a blocked notice would **breach**? | BUS | If yes, the gate must propose an alternative (call/letter/e-mail) rather than simply refusing |
| **13** | What is CN's appetite for a **shadow-mode pilot** (recommendations logged, humans decide, no workflow change) for 2–4 weeks before anything is auto-suppressed? | BUS | Shadow mode is our lowest-risk proof and our fallback if CN's data is thinner than expected |
| **14** | Which single metric must improve for the pilot to be declared a success by CN's leadership — cost per productive contact, field-slot yield, complaint rate, or recovery in bucket? | BUS | Determines which of our two products leads the deck |

---

### Table C — Compliance questions

| # | Q | Cat | Why it changes the design |
|---|---|---|---|
| **15** | How is the **advance notice before the first field visit** (≥1 day by SMS/e-mail; 3 days by letter when applicable) currently generated, and from which address record? | COMP | That address record is precisely what PS3 must score; if it is the same field that the geocoder feeds, the gate is a small change with a large effect |
| **16** | For DPDP, are we acting as **Data Fiduciary or Data Processor** for the pilot data, and is consent collected at origination broad enough to cover geospatial inference and profiling? | COMP | Decides what we may store at all, and whether the "no cached commercial geocoder data" rule is about licence or about personal data |
| **17** | What does CN's **audit trail** currently record per action — the recommendation, the rule, the data snapshot, or only the human's decision? | COMP | Our whole compliance claim is "the constraint that permitted or blocked the action is recorded". If CN's log is decision-only, we must add a recommendation log, and that is a real engineering change |
| **18** | Has CN already had to defend an agent-conduct complaint where the system "permitted" a contact (e.g. hours, wrong party, repeat contact after a request to stop)? | COMP | If yes, the identity gate and the suppression gate become the product's spine rather than a feature |
| **19** | Are there **state-level** recovery-conduct or e-notice requirements (or a licence condition) beyond the central framework that apply to the pilot states? | COMP | May force state-conditional rules in the gate — cheap to add now, expensive to retrofit |
| **20** | What is CN's position on **recording and retention** under the new framework (≥6 months) — and would the geospatial evidence and integrity weights be considered part of the recovery record? | COMP | Determines retention design and whether the integrity weight must itself be auditable |

---

### Table D — Competition / positioning questions

| # | Q | Cat | Why it changes the design |
|---|---|---|---|
| **21** | Which of TransUnion / Spocto / Credgenics / Mobicule capabilities does CN **already resell or integrate**, and where does ours overlap? | COMP | We must position as a layer *between* predictors, not a replacement for any of them |
| **22** | Is Maestro's field module already geo-tagging visits and using that data for anything beyond proof-of-visit? | COMP | If yes, our PS3 learning loop is a fast follower, and we should lead with the **notice gate** instead |
| **23** | Would CN accept a design where the geocoder is called **at runtime and nothing is cached** — and does that pass their own security/procurement review? | COMP | It is our legal position for PS3; if rejected, the product must fall back to open data + field evidence, which is weaker |

---

### The five questions we would ask in the first 15 minutes of a hackathon mentor session
**Q1** (portfolio + ticket band) · **Q7** (is visit GPS captured historically) · **Q3** (incremental vs gross recovery) · **Q15** (how the advance notice is generated today) · **Q17** (what the audit trail records).

Those five answers decide (a) which product leads, (b) whether PS3 has a learning loop at all, (c) whether our ROI is credible, and (d) whether the compliance story is a small change or a rebuild.

---

# Part XIII. Hackathon execution plan

*Source file: `HACKATHON_EXECUTION_PLAN.md`*

## HACKATHON EXECUTION PLAN — SANKET + SUTRA

**Objective:** win, not submit. Translation: a judge must be able to say, in one sentence, *what changed and why it matters* — and see it happen on screen.

---

### 1. The win condition, read backwards

Hackathon judging in BFSI essentially reduces to four questions: **Is the problem real? Is the solution novel *for us*? Can it be built? Did you show it working?** Long architecture documents lose to a crisp story plus a working screen.

Therefore the plan is built so that the *minimum viable story* is also the *minimum viable build*:

> A recovery notice is about to be served at an address the system is only 41% sure is valid. The system refuses to serve it and says which rule drove the refusal. Evidence arrives — a field visit at a landmark near the address. The confidence clears the threshold and the notice is released, with the evidence and the rule recorded. Then someone submits a fake check-in from six kilometres away; the system does not move its belief — it **widens** and keeps the notice blocked on a second condition.

Everything else in the design exists only if it strengthens that loop or a number next to it.

---

### 2. 48-hour MVP — build exactly this, nothing else

**Frozen scope (L1).** Two services, one console, one recorded demo path.

| # | Component | In | Notes |
|---|---|---|---|
| 1 | **Address confidence gate** (M1) | ✅ | Stratified base rate × agreement-style evidence fusion → `conf_address` → threshold `τ_notice` |
| 2 | **Notices & visits API** | ✅ | `POST /v1/notices/eligibility` returns `ALLOW×3 / BLOCK×5 / WIDEN`; the block reasons are the product |
| 3 | **Field evidence ingest** | ✅ | Check-in with GPS, accuracy, dwell, photo hash, purpose tag, `device_trust` |
| 4 | **Integrity weight** (M3) | ✅ | `w ∈ [0.2, 1.0]`; low `w` ⇒ the observation is down-weighted and the **radius widens**, belief does not shift |
| 5 | **Radius output** (`radius_90`, per stratum) | ✅ | Empirical, stratum-conditional (metro / tier-2 dense / tier-2 sparse / rural), never a single global number |
| 6 | **Contact-point identity gate** (M4) | ✅ | P(right party) below threshold ⇒ the *disclosure-capable* action is not in the candidate set |
| 7 | **Decision record / permission ledger** | ✅ | Recommendation, rule fired, data snapshot, human decision, action, outcome — hash-chained, exportable |
| 8 | **Skip-trace EV gate** | ✅ | Fires only when expected information value > fee; slider in the console |
| 9 | **Console (demo prop)** | ✅ | Three screens: queue, decision, evidence |
| 10 | Contact timing model (S3) | ⚠️ rules only | Cohort-level hour-of-day priors; no learned survival model in the MVP |

**Explicitly out of the MVP:** graph identity, bandits, uplift modelling, our own geocoder, LTR ranker, multi-head H3 classifier, sequence models, beat-plan routing solver, notification-bot integrations, speak-vernacular templates, dashboards for anything other than the four pilot counters.

**Build plan (2 people × 48 h, or 4 people × 24 h):**

| Hours | Workstream A (ML/data) | Workstream B (product/demo) |
|---|---|---|
| 0–4 | Freeze schema; generate the synthetic book; write the strata base rates | Console shell; wire the API contract; ledger format |
| 4–12 | M1 + M3 + radius; unit tests on hand-built cases | Decision panel; blocked-notice UI with the rule name visible |
| 12–20 | M4 identity gate + trace EV gate; seeded replay of 200 accounts | Evidence panel with radius/W visualisation; timer for the demo beats |
| 20–30 | Calibrate thresholds on the synthetic book; produce the counterfactual table (naive vs gated) | Polish: the 1,400 m → 90 m loop; the widening animation; ledger JSON view |
| 30–40 | Failure-case pass (all 16 scenarios) against the running system | Demo script rehearsal ×5; 2–3 min recording; fallback video |
| 40–48 | Numbers freeze; README; architecture one-pager; pitch deck | Dry run in front of a non-technical colleague; cut whatever confuses them |

**Honesty rule inside the build:** every synthetic input is labelled `SYNTHETIC` in the UI (a corner ribbon), and the console prints, in one line, *what would change if the input were real*. We never present synthetic performance as measured performance — a judge who catches that ends the pitch.

---

### 3. What each demo beat needs from the build (contract)

| Beat | Screen | Machine requirement |
|---|---|---|
| Refusal | Decision | `conf_address = 0.41 < 0.70`; reason code `ADDR_CONF_LOW` + `NOTICE_PRECHECK` |
| Evidence | Evidence | One check-in: landmark match, dwell 6 min, `device_trust` high, `w = 0.95` |
| Reversal | Decision | `0.78 ≥ 0.70` → `ALLOW`; ledger row written with both reasons |
| Poisoning | Evidence | Spoofed check-in 6.1 km away; `w = 0.20`; `conf 0.79`, **`radius_90` 90 m → 520 m** |
| Identity gate | Queue | Two accounts with identical connect probability, opposite `P(right party)` → different permitted actions |

If **any** of these five cannot be produced, the demo must be re-cut to the four that can. Never narrate a screen that is not on screen.

---

### 4. Competition-final scope (4–8 weeks, if we advance)

Ordered by winning value, not by technical interest:

1. **Shadow-mode pilot evidence**: run against 2–4 weeks of historical cases; publish the counterfactual (how many notices/visits would have been blocked, how many traces avoided, at what claimed risk).
2. **Timing model (S3)** with the censoring fix, if and only if it beats the hour-of-day baseline on a held-out window.
3. **Address calibration by stratum** with real field outcomes; replace synthetic radii with empirical ones.
4. **Integrity model M3 v2**: device fingerprint, route plausibility between consecutive check-ins, photo-OCR of the door plate, collector-level anomaly detection.
5. **Permission ledger export** in a format a compliance officer can hand to a regulator (CSV + signed JSON).
6. **One integration** end-to-end: notice generation → gate → suppression or release, with the counterfactual logged — not a dashboard.

---

### 5. Production roadmap (12 months, with gates)

| Phase | Months | Deliverable | Gate to proceed |
|---|---|---|---|
| P0 Pilot | 0–1 | Shadow mode on one region; counters pre-registered | Field GPS captured on ≥70% of visits; geocoder licence permits runtime use |
| P1 Gate live | 2–3 | Notice/visit gate in production for one bucket; humans override with reason codes | Zero unlogged suppressions; override rate <15% |
| P2 Identity gate | 3–6 | Disclosure-capable actions restricted by modelled P(right party); point-level dispositions modelled | Measured wrong-party rate down; no drop in cure in bucket beyond tolerance |
| P3 Learning loop | 6–9 | Address confidence recalibrated on real field outcomes; radius replaced by empirical strata | Coverage of `radius_90` verified; drift monitor live |
| P4 Scale | 9–12 | Multi-portfolio (ticket-conditional policies), trace EV, field route integration | ROI holds in a **second** book (the real test) |

**Kill criteria (pre-registered):** if the identity gate does not reduce measured wrong-party contacts, or the address gate does not reduce wasted visits by ≥5 pp, or override rate exceeds 25%, **stop and re-scope** rather than iterate.

---

### 6. Anti-patterns we will not ship
Building our own geocoder · an LLM in the decision path · a GNN/sequence model · bandits before a real randomised holdout · a map UI nobody in collections asked for · a dashboard with no action attached · a compliance claim resting on "we log everything" · presenting synthetic results as measured · reusing the 1,400 m→90 m example as if it were real.

---

### 7. "How would I beat this team?" — adversarial pass

*If I were a rival team, here is how I would attack this entry, and our pre-planned response:*

| Attack | Why it would work | Our response (in the pitch) |
|---|---|---|
| **"This is a threshold with an audit log."** | It is, partly. A judge can reduce our architecture in one line | Concede immediately, then show the widening behaviour and the identity gate: *thresholds cannot be poisoned and cannot express "which action is permitted for whom"*. The reduction is the point — we built the smallest thing that changes the decision |
| **"TransUnion/Spocto already rank contactability."** | True, and they have more data | Agree. We position as the layer that decides **what the platform is permitted to do** with a prediction, and we compete on **field-outcome evidence and the permission record**, not on contact scores |
| **"Shiprocket/Delhivery already learn addresses."** | True, and better resourced | Agree. Difference is the object: they learn *delivery* distances; we learn *recovery-visit* evidence under an integrity constraint, and we couple it to a legal gate they have no reason to build |
| **"You have no data."** | Our demo runs on synthetic cases | Say it before they do, and point at the pre-registered pilot counters and the shadow-mode design. The demo proves the **mechanism**, the plan proves the **measurement** |
| **"Compliance is the compliance team's job, not a product."** | A common view inside BFSI | Reframe with the RBI language: the regulator judges whether the **system permitted** the violation. That makes permission a product requirement, not a policy |
| **"Where is the AI?"** | There is no LLM and no deep net | Answer with the actual AI content: a calibrated identity model, an integrity-weighted evidence model, a stratified uncertainty model, an EV decision rule — and a deliberate refusal to put a model where a rule belongs |
| **"Too small to matter."** | Small ticket book, few visits | That is exactly why we computed ROI **by ticket band** and why we lead with avoided waste and avoided exposure — and why we said out loud that the offer layer (₹7.4 L/pp) is bigger and not ours to claim |

**What would actually beat us:** a team that arrives with **one real dataset from a real collections floor** and shows a measured 5 pp reduction in wasted visits with a compliance record the regulator would accept. Our counter is to make that the *first* thing we ask CN for (see `CN_QUESTIONS.md`, Q7 and Q15) and to have the shadow-mode design ready to execute in the room.

---

# Appendix A. Phase-1 baseline research (research record)

*Source file: `CreditNirvana_PS2_PS3_Research_and_Strategy.md` (+ `.docx`). **Status:** the research, benchmarks, rules and URLs here remain valid and are cited throughout Parts I–XIII. The **design** it recommends (three calibrated heads + competing-risks survival + graph features; parse → normalise → LTR → conformal radius) is **superseded** by Parts VI–VIII — see Part V for why.*

## CreditNirvana — PS2 + PS3
### Deep Research & Solution Strategy
#### Right-Party Contact Prediction & Skip-Trace Prioritisation (PS2) · Self-Learning Address Geocoder (PS3)

**Prepared for:** CreditNirvana hackathon team
**Date:** 5 October 2026
**Status:** Research-backed strategy, pre-implementation (no code written)

**How to read this document.** Section 1–5 is what exists today and where it fails. Sections 6–12 are our design. Sections 13–16 are execution. Every non-obvious claim carries a source URL. Where a source is a **vendor blog or marketing page**, it is labelled *[vendor claim]* — treat those as directional industry signal, not evidence. Where a source is **peer-reviewed or a working paper**, it is labelled *[paper]*.

---

## 1. EXECUTIVE SUMMARY

### 1.1 What PS2 actually is

**Stated problem:** predict, for each phone number/address, P(Right-Party Contact), then choose the next best action (retry / switch contact point / switch channel / skip-trace / field visit), with skip-trace triggered by *expected economic value*, not attempt count.

**What it actually is, once you read the challenges carefully:** PS2 is **not a classification problem**. It is a *partially observable, sequential, resource-constrained decision problem where the state (is this contact point live and owned by our borrower?) is never directly observed, the actions themselves change the future data, and some state distinctions (avoiding vs invalid vs recycled) are only separable through the *lawfulness of the response function to deliberate probes*.*

Three concrete sub-problems hide inside PS2:

| Sub-problem | Nature | Why it breaks naive ML |
|---|---|---|
| **S1. Latent contact-health inference** | Unsupervised/latent-state inference with action-conditional observations | "Borrower avoiding" and "number dead" both look like "no answer". A classifier trained on "did we contact?" learns the *dialer policy*, not the contact point. |
| **S2. Next-best-action decision policy** | Constrained expected-value optimisation (a decision engine, not a model) | Highest-probability dial ≠ highest-value dial. Cost, compliance, fatigue and information value all differ per action. |
| **S3. Learning under feedback loops** | Off-policy / exploration problem | Only high-scored contacts get called, so low-scored contacts never generate labels → the model cannot learn it was wrong. |

The literature has solved pieces of S1 and S2 (Sánchez et al. 2022 for contact prediction; van de Geer et al. 2018 for marginal-value call scheduling), but **essentially nobody has published S1 at the contact-point level with an explicit right-party-identity head**, and nobody treats **skip-trace as a value-of-information purchase**.

### 1.2 What PS3 actually is

**Stated problem:** geocode descriptive Indian addresses, learn from field visits, output lat/lon + confidence radius + landmark directions, keep learning.

**What it actually is:** a **multi-source evidence fusion and ranking problem with a label-integrity problem on top**.

- The text is low-information ("behind Hanuman temple", "2nd cross"). The *evidence* is in the GPS of past visits — but that GPS is **biased, not just noisy** (Amazon Last Mile states plainly that "centroids and other center-finding methods do not serve well, because the noise is consistently biased" — see [Forman, ECML PKDD 2021](https://mlanthology.org/ecmlpkdd/2021/forman2021ecmlpkdd-getting/) *[paper]*).
- The GPS may be the *right* GPS for the *wrong* reason: borrower met at a shop, workplace, road junction, or a neighbour's gate.
- And the GPS can be **fabricated** (fake check-ins), which poisons labels — a problem the e-commerce geocoding literature does not face in the same way, because a delivery is validated by a parcel.

So PS3 = (a) parse & normalise messy multilingual addresses, (b) generate location candidates, (c) **rank candidates using field evidence with reliability weighting**, (d) classify *what kind of place the GPS is* (home/work/shop/road), (e) produce a **calibrated radius**, not a fake-precise point, and (f) run the whole thing **offline**.

### 1.3 Which is more feasible?

| Dimension | PS2 | PS3 |
|---|---|---|
| Are labels naturally available in CN's data? | **Yes** — RPC events, dispositions, answer/hangup, ring duration. Dense, numeric, high-volume. | **Partially** — field-visit GPS exists but is sparse per address, biased, and sometimes unverifiable. |
| Can a public dataset bootstrap a hackathon prototype? | **Weakly** — no public RPC dataset exists. Requires synthetic + proxy datasets. | **Yes** — OSM POIs, pincode polygons, building footprints, transliteration corpora, public GPS trajectories all exist and are usable. See §8. |
| Model risk | Medium (selection bias, calibration) | High (label poisoning, biased GPS, "is this a home?") |
| Time to a credible MVP | **3–5 days** | **5–9 days** |
| Demo-ability without sandbox data | Medium (needs a simulator) | **High** (maps are visually compelling; public data alone can demo a geocoder) |
| Business value per unit of effort | **High** — every avoided wasted dial and every correctly-timed trace is money | Medium-high — compounds through the visit and trace channels |
| Novelty headroom | Medium (crowded field: dialers, propensity models) | **High** (nobody has published "learn a geocoder from *contact* outcomes") |

**Verdict:** PS2 is more *feasible*; PS3 has more *differentiation headroom*; and **PS3's labels are generated by PS2's actions** — which is the entire reason to build them together (§6).

### 1.4 Which has greater hackathon potential?

**PS2 alone** demos as a dashboard of numbers — hard to make a judge *feel* it.
**PS3 alone** demos as a map — instantly legible, but risks looking like "an open-source geocoder with extra steps".
**PS2 + PS3 combined** gives the one demo nobody else will have: *click "send this address to field verification" → the field agent's GPS comes back → the address's confidence radius shrinks from 1,400 m to 90 m → the account's field-visit expected value flips positive → the decision engine changes tomorrow's action from "call again" to "visit with these landmark directions".*

That single loop is the pitch. It is also the only part of the design that is genuinely defensible as original.

---

## 2. PS2 — EXISTING RESEARCH

### 2.1 Important papers

| # | Paper | Venue / Year | What it does | Why it matters to us | URL |
|---|---|---|---|---|---|
| P1 | **Sánchez, Maldonado, Vairetti — "Improving debt collection via contact center information: A predictive analytics framework"** | *Decision Support Systems* 159, 2022 | Fuses contact-center variables with financial data; defines **five prediction tasks**, notably (1) probability of *successfully contacting* a late payer, (2) contact **that results in a promise to pay**, (3) late-payment — each trained (a) on all debtors and (b) **only on contacted debtors**. | The single most directly relevant paper to PS2. Proves (i) contact-center features add lift, (ii) *contact* and *commitment* must be separate heads, (iii) training "promise to pay" only on contacted customers introduces a **selection-bias variant** the authors benchmark explicitly. | [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0167923622000835) *[paper]* |
| P2 | **van de Geer, Wang, Bhulai — "Data-Driven Consumer Debt Collection via Machine Learning and Approximate Dynamic Programming"** | SSRN 3250755, 2018 | Formulates call scheduling as an **MDP**; approximates the value function with ML; computes the **marginal value of making a call** per debtor; validated in a **controlled field experiment** with real debtors. | The canonical proof that *ranking by marginal value beats ranking by probability*, and that it survives contact with reality. Winner: "collects more debt in less time, using substantially fewer resources." | [Semantic Scholar](https://www.semanticscholar.org/paper/7f05af04d948ea9578477b926187378e45f4dd5d) · [Oracle summary](https://blogs.oracle.com/ai-and-datascience/post/data-driven-debt-collection-using-machine-learning-and-predictive-analytics) *[paper]* |
| P3 | **Lappas & Xanthopoulos — "Intelligent decision support for debt collection using predictive learning and multi-criteria optimization"** | *Finance Research Open* 2(2), 2026 | Three layers: **Rule Extraction** (unsupervised behavioural segments — self-cured / lazy payer / delinquent / defaulter), **Prediction** (best day, best time, best channel, likelihood of payment/PTP), **Optimization** (fuzzy logic + MCDA over cost and recovery). Data from a debt collection agency. | Gives us the **auditability architecture**: ML outputs → fuzzy risk profiles → multi-criteria decision. This is the pattern for "explainable and auditable decisions" the problem statement demands. Also its literature table is a free map of the field. | [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S3050700626000381) *[paper]* |
| P4 | **Witzany & Kozina** — survival analysis for soft collection | Cited in P3 | Applies **survival analysis** to soft-collection actions (calls, mails, visits, legal steps); compares phone calls to medical treatment and repayment to recovery. | Direct evidence that **time-to-event models outperform logistic regression** for collection action optimisation. The blueprint for our "contact decay" model. | [via P3](https://www.sciencedirect.com/science/article/pii/S3050700626000381) *[paper]* |
| P5 | **Kim & Kang — "Late payment prediction models for fair allocation of customer contact lists to call center agents"** | *Decision Support Systems*, 2017 | Five ML late-payment models + **ten customer scoring rules** to allocate contact lists **fairly** across agents. | Two lessons: (i) allocation/fairness is a first-class constraint (drives agent behaviour and complaints); (ii) scoring rules differ from models — the *decision layer* is where value is created. | [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0167923616300264) *[paper]* |
| P6 | **Przybyłek et al. — "Towards a smart debt collection system: a Design Science Research approach"** | *Journal of Big Data* 12:193, 2025 | Design-science build of a Smart Debt Collection System with a major financial institution; includes **PAD: a persona extractor that filters irrelevant utterances and summarises debtor personas from call transcripts**, plus a strategy/response suggestion generator for novice collectors. | Anthropic evidence that **transcripts → structured persona features** is feasible and useful in production collections. That is our route for using voice-bot transcripts without over-engineering. | [SpringerOpen](https://journalofbigdata.springeropen.com/articles/10.1186/s40537-025-01252-0) *[paper]* |
| P7 | **FRS-DRL — "Flexible recommendation for optimizing the debt collection process based on customer risk using deep reinforcement learning"** | *Expert Systems with Applications*, 2024 | Deep-RL recommender producing flexible per-risk-category collection actions; **tested in a real environment for three months**. | Reported: reward rate 73.22% (with transfer learning) / 62.44% (without); **collection % +20.34%; field-agent visits −16.30%**. The visit reduction is the number to remember: RL reallocated *away from* field visits. | [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0957417424018189) *[paper]* |
| P8 | **Agent Matching Model (AMM)** — ML + Operations Research for recovery | 2025 working paper | Predicts repayment probability per debtor **incorporating caller-level data**, then solves an assignment ILP maximising Σ P(d,c)·x·R(d,c) subject to exclusive assignment, workload balance, and legal/ethical compliance. | Shows the **two-stage architecture** (predict → optimise with constraints) that we reuse, and that *caller identity is a feature*, not a constant. | [ResearchGate](https://www.researchgate.net/publication/391171731_Optimizing_Recovery_Debt_Collection_Process_by_Using_Machine_Learning_and_Operation_Research) *[paper]* |
| P9 | **Ye & Bellotti** — two-stage beta-mixture model for recovery rates; **Kriebel & Yam** — collector data in third-party collections | 2019/2020, both summarised in P3 | P9 models **multimodal recovery distributions**; Kriebel & Yam show process/collector data materially improves prediction. | Recovery is multimodal (partial payers, burst payers) — a single mean is misleading. And process data (who called, how) is predictive. | [via P3](https://www.sciencedirect.com/science/article/pii/S3050700626000381) *[paper]* |
| P10 | **Sánchez et al. — TreeSHAP feature importance in collections** | Cited in P3 | Uses TreeSHAP to explain which contact-centre variables drive predictions. | Confirms SHAP-based explainability is standard practice in this domain → our audit layer is expected, not exotic. | [via P3](https://www.sciencedirect.com/science/article/pii/S3050700626000381) *[paper]* |
| P11 | **Niculescu-Mizil & Caruana — "Obtaining Calibrated Probabilities from Boosting"** | UAI 2005 / arXiv:1207.1403 | Demonstrates *why* boosted trees produce distorted probabilities, and that **Platt scaling and isotonic regression** each reduce cross-entropy by ~21%. | Critical: **our primary model (GBM) is miscalibrated by construction.** Since every downstream EV calculation multiplies probabilities by money, miscalibration is a direct financial error. | [arXiv](https://arxiv.org/abs/1207.1403) · [PDF](https://www.cs.cornell.edu/~caruana/niculescu.scldbst.crc.rev4.pdf) *[paper]* |
| P12 | **"Calibration Meets Reality"** | arXiv:2509.23665, 2025 | Quantitative post-hoc calibration study: XGBoost ECE **0.185 → 0.044** with Platt scaling (76% improvement); isotonic also strong; behaviour is dataset-dependent. | Gives us the concrete numbers to quote in the pitch for *why* we ship a calibration layer. | [arXiv](https://arxiv.org/html/2509.23665v1) *[paper]* |
| P13 | **Vovk-style conformal prediction** (modern surveys: Angelopoulos & Bates; geo-variant below) | ongoing | Distribution-free, model-agnostic **prediction sets/intervals with finite-sample coverage guarantees**. | The right way to answer "how confident are you that this action is the best one?" — and, in PS3, to produce **confidence radii with a stated coverage**. | [Survey ref via CP applications](https://www.sciencedirect.com/science/article/pii/S0168169925006659) · [GeoConformal](https://arxiv.org/html/2412.08661v1) *[paper]* |
| P14 | **Uplift modelling: meta-learners & Qini** (T/S/X/R-learners; Zhao & Harinen Qini curves; multiple-treatment uplift **with cost optimisation**) | arXiv:1908.05372 + standard literature | Estimates **CATE** — the *incremental* effect of an action, not the baseline propensity. Multiple-treatment uplift explicitly models **per-treatment cost** and picks the best treatment per individual. | Exactly our problem shape: several candidate actions, different costs, need the *incremental* effect. Provides AUUC/Qini as the evaluation metric when we have randomisation. | [arXiv:1908.05372](https://arxiv.org/pdf/1908.05372) · [Qini/multiple-treatment background](https://link.springer.com/article/10.1007/s10796-022-10283-4) *[paper]* |
| P15 | **"Next Best Action" decisioning: propensity → uplift → constrained argmax, including the null action** | Industry synthesis, 2026 | Formalises NBA as a **stack**: candidate action set (including "do nothing"), per-action expected value `uplift × margin − cost`, hard-constraint pre-filter, soft-constraint arbitration, log-with-reason-codes. | This *is* the architecture of our PS2 decision layer. It also tells us what most implementations get wrong: they rank by propensity and forget the null action. | [CDP.com glossary](https://cdp.com/glossary/next-best-action/) · [Grid Dynamics: NBA via RL](https://blog.griddynamics.com/building-a-next-best-action-model-using-reinforcement-learning/) *[industry]* |
| P16 | **Lee & Narayanan — "Security and Privacy Risks of Number Recycling at Mobile Carriers in the US"** | 2021 (PETS-style measurement study) | Sampled 259 numbers available to new subscribers at two major carriers: **83% were recycled**; **66% were linked to PII or existing online accounts**; 39% linked to breached passwords; a honeypot of 200 recycled numbers received sensitive calls/texts within a week. | The hardest evidence that recycled numbers are a *privacy incident generator*, not a nuisance. Directly underwrites "recycled number = compliance risk". | [summary + related TSF model](https://www.researchgate.net/publication/359427393_Security_and_Privacy_Risks_of_Number_Recycling_at_Mobile_Carriers_in_the_United_States) *[paper]* |
| P17 | **TSF — Temporal pattern and Statistical feature Fusion model for reassigned-number account compromise** | Meituan dataset, 2021+ | Detects accounts compromised because a phone number was **reassigned**, using a temporal-pattern encoder + statistical features. | Shows a *learnable detector* for number reassignment exists; we adapt the temporal-discontinuity idea to borrower contact history. | [researchgate summary](https://www.researchgate.net/publication/359427393_Security_and_Privacy_Risks_of_Number_Recycling_at_Mobile_Carriers_in_the_United_States) *[paper]* |
| P18 | **Uber — contextual bandits in production: XGBoost + SquareCB** | Uber Engineering blog, 2025 | Uses an XGBoost reward model plus **SquareCB post-processing to inject deliberate exploration** because "the XGBoost model lacks an exploration component"; also runs LinUCB for a linear-assumption variant. | The production blueprint for "GBM scorer + explicit exploration layer" — exactly the two-part design we need so the model doesn't starve untested contacts. | [Uber blog](https://www.uber.com/us/en/blog/enhancing-personalized-crm/) *[industry / engineering]* |
| P19 | **Optimizely contextual bandits — exploration floors** | Vendor docs, 2026 | Documents that exploration must be **≥5%** for the model to keep learning, and that automated schemes ramp exploration from ~100% down to ~5%. | A concrete, citable operating parameter for the exploration budget. | [Optimizely docs](https://support.optimizely.com/hc/en-us/articles/29328842964109-Contextual-bandits) *[vendor claim]* |
| P20 | **FPBoost / SurvivalBoost / scikit-survival / lifelines** | arXiv:2409.13363; SODA-INRIA; JMLR 21(212) | Open, sklearn-compatible implementations of gradient-boosted survival models, competing-risks models, and proper scoring rules. | Tells us the survival-model engineering path is *off-the-shelf*, not from scratch. | [FPBoost](https://arxiv.org/html/2409.13363v2) · [Hazardous/SurvivalBoost](https://soda-inria.github.io/hazardous/) · [scikit-survival](https://datascience.oneoffcoder.com/survival-mva.html) *[code + paper]* |
| P21 | **Vicencio et al. — "Getting Your Package to the Right Place" analysis: Learning-to-rank for geolocation** | ECML PKDD 2021 | See §3 — included here because LTR is one of the PS2 candidate ranking approaches too. | Cross-pollination: LTR over *candidate contact points within an account* is the mirror of LTR over *candidate coordinates within an address*. | [mlanthology](https://mlanthology.org/ecmlpkdd/2021/forman2021ecmlpkdd-getting/) *[paper]* |
| P22 | **Gradient boosting vs. logistic regression vs. MLP in a real debt collection agency** | IEOM 2022 (Ecuadorian DCA, 7.4M records) | CRISP-DM build over 7,447,856 records with class-undersampling; GBM best (sensitivity 0.97, specificity 0.93, AUC 0.98); LR balanced; RF overfit. | Practical confirmation: **GBM > RF > LR > MLP** on tabular collections data, and that undersampling + specificity/sensitivity framing is the norm. | [IEOM PDF](https://ieomsociety.org/proceedings/2022paraguay/112.pdf) *[paper]* |

### 2.2 Industry approaches

| System / vendor | What it is | Technique | Reported outcome |
|---|---|---|---|
| **TrueAccord HeartBeat** | Patented ML decision engine, digital-first collections; 24M+ consumer journeys of engagement data; dynamic personalisation of channel/message/plan in real time. | ML personalisation + "HumAIn" hybrid; constant A/B optimisation; RPA for downstream state changes. | Snap Finance side-by-side vs traditional agencies: **25–35% better performance**; Retain vs three call-and-collect agencies: **24% roll-rate improvement, 28% early-stage / 40% late-stage gross flow-through improvement**. [*vendor claim*] [TrueAccord](https://blog.trueaccord.com/tag/machine-learning/) · [Retain PR](https://www.wfmz.com/news/pr_newswire/pr_newswire_technology/trueaccord-announces-results-confirming-effectiveness-of-digital-first-retain-product-for-early-stage-delinquencies/article_c348f980-670a-5f88-8c29-cc2b1e073505.html) |
| **Experian — PriorityScore for Collections / Collection Triggers** | 60+ industry-specific debt recovery scores; monitors accounts and re-queues when borrower circumstances change (new job). | Scores selectable by *likelihood to pay* **or** *expected recovery amount*. | Defines the industry standard that "priority = probability × value", and that **trigger-based re-scoring beats static buckets**. [*vendor claim*] [Experian](https://www.experian.com/blogs/insights/four-collections-best-practices/) |
| **Predictive dialers** (Revring, Sprinklr, RingCentral, NICE-class) | Pacing algorithms that dial multiple lines per agent; "AI call scoring" and adaptive pacing layers on top. | Real-time statistical pacing on AHT/answer-rate; Sprinklr documents **RL-based pacing** tuned to abandon-rate constraints. | Dialing modes: predictive ≈60–150 dials/agent-hour; RPC benchmark **8–15% cold B2C**, 35–50% preview B2B. `[vendor claim]` [Revring](https://www.revring.com/blog/predictive-dialing-guide?from=blg) · [Plura](https://www.plura.ai/articles/reduce-cost-contact-predictive-dialer) · [Sprinklr](https://www.sprinklr.com/help/articles/dialers/predictive-dialers/641180977517d84a3ab00839) |
| **AI contact-optimisation for collections** (e.g. ainora.lt write-up) | Per-debtor best time, best channel, frequency-cap management, portfolio segmentation by data freshness. | Time-series + individual-level timing models; sequence models on channel engagement. | Claims 2–4× more RPC per attempt; example segmentation: "high balance + stale data → **skip-trace first, then targeted contact**". `[vendor claim]` [ainora](https://ainora.lt/blog/ai-predictive-dialing-debt-collection-contact-optimization) |
| **Indian voice-AI collections** — Skit.ai (ex-Vernacular.ai), Gnani.ai, Rezo.ai | Indic-language voice agents for EMI reminders/KYC callbacks; Rezo markets "agentic AI" for collections. | Multilingual ASR/TTS, code-mixing, call-flow orchestration, CRM connectors (Salesforce), telephony integrations (Exotel/Jio/Tata Tele). | Rezo: leading Indian NBFC saw **10% jump in collection efficiency**, go-live in 20 days. `[vendor claim]` [DialNexa comparison](https://dialnexa.com/blogs/best-voice-ai-platform-in-india/) · [awaaz.ai](https://www.awaaz.ai/blog/indian-call-center-ai-voice-solutions) · [Rezo](https://www.rezo.ai/ai-voice-agents) |
| **Speech analytics for collections** — CallMiner, Sedric, Vasvox | Scores **100% of calls** for Mini-Miranda, *Right-Party-Contact language*, FDCPA-style violations, abusive language; redaction; real-time agent prompts. | ASR + phrase/pattern detection + sentiment; real-time flagging. | Provides the *supervision signal* for right-party detection from conversation content. `[vendor claim]` [CallMiner](https://callminer.com/blog/speech-analytics-collections-important) · [Sedric](https://www.sedric.ai/arm-resources/speech-analytics-in-debt-recovery-challenges-opportunities-and-the-ai-advantage) |
| **Skip-trace platforms** — Thomson Reuters CLEAR, LexisNexis, TLO-class | Locate people from fragmented data; "enhanced skip tracing" measured by Profit Per Account (PPA) and Collector Effective Index rather than contact rate. | ML-assisted entity linking; claim: can locate an individual from an **outdated phone number alone**. | Reinforces the KPI discipline: skip-trace success must be measured in **money per account**, not in "found/not found". `[vendor claim]` [Thomson Reuters](https://legal.thomsonreuters.com/blog/benefits-of-enhanced-skip-tracing/) · [ACS](https://wp.acs-cam.com/blog/from-skip-tracing-to-smart-tracing-how-technology-is-changing-asset-tracing/) |
| **Phone number intelligence** — Telesign, Twilio/Telnyx Lookup, ClearoutPhone, AbstractAPI | Carrier lookup, line type (mobile/landline/VoIP), HLR live-reachability, LRN/ported status, CNAM, spam scoring, "recycled number risk". | Carrier/HLR queries + ML anomaly detection on location/SIM/usage change. | Telesign explicitly markets **predictive analytics on number-churn and regional reassignment trends** to anticipate recycling. `[vendor claim]` [Telesign](https://www.telesign.com/blog/number-deactivation-and-the-recycled-phone-number-dilemma) · [Telnyx](https://telnyx.com/products/number-lookup) · [ClearoutPhone](https://clearoutphone.io/) |
| **Collections decisioning platforms** | Finvi, Sapiens, FICO Debt Manager-class, digiqt-class AI agents | Predictive scoring + next-best-action + omnichannel automation + "compliance guardrails" as a declared feature. | digiqt markets: recovery probability, expected recovery value, treatment, channel, best contact time, compliance constraints — *per account, with explanation codes*. `[vendor claim]` [digiqt](https://digiqt.com/ai-agent/financial-services/debt-collections/collections-prioritization-ai-agent-for-debt-collections-in-financial-services/) · [CR Software buyer's guide](https://blog.crsoftware.com/ai-powered-debt-collection-software) |
| **McKinsey (collections economics)** | Advisory benchmark | Gen-AI/augmentation in customer assistance & collections. | **Up to ~40% reduction in operational expenses and ~10% recovery improvement; up to 30% CSAT increase.** [McKinsey](https://www.mckinsey.com/capabilities/risk-and-resilience/our-insights/the-promise-of-generative-ai-for-credit-customer-assistance) · [secondary summary](https://sbs-software.com/insights/artificial-intelligence-data/ai-automation-collections/) *[paper/consultancy]* |
| **Contact-rate benchmarking by data recency** | Contact-centre KPI guides | Empirical contact rate vs. data age. | Fresh 0–7 days **25%**, warm 7–30 days **16%**, aged 30–90 days **11%**, cold purchased **7%**. `[vendor claim]` [Plura citing ViciStack/Voiso](https://www.plura.ai/articles/reduce-cost-contact-predictive-dialer) |
| **Call-window effects** | Outbound benchmark guides | Time-of-day/day-of-week contact modelling. | Tue–Thu 10–11 AM and 4–5 PM local highest-converting; *changing the call window alone* claimed to lift connect rates **30–70%**. `[vendor claim]` [Plura](https://www.plura.ai/articles/reduce-cost-contact-predictive-dialer) |

### 2.3 Open-source projects for PS2

| Project | What it gives us | URL |
|---|---|---|
| **scikit-survival** (Pölsterl, JMLR 21(212)) | Cox, Random Survival Forest, **GradientBoostingSurvivalAnalysis**, concordance index, cumulative/dynamic AUC, IPCW metrics. sklearn-compatible. | https://github.com/sebp/scikit-survival |
| **lifelines** | CoxPH, Cox time-varying, Weibull/LogLogistic/LogNormal AFT, Kaplan-Meier, piecewise-exponential; good for the *interpretable* decay model and hazard plots. | https://lifelines.readthedocs.io/ |
| **hazardous / SurvivalBoost** (SODA-INRIA) | Scalable gradient boosting for survival **and competing risks** with proper scoring rules — directly usable for "contact-event vs. three competing failure modes". | https://soda-inria.github.io/hazardous/ |
| **PySurvival** | Alternative parametric survival zoo. | https://square.github.io/pysurvival/ |
| **CausalML, EconML, DoWhy** | T/S/X/R-learners, causal forests, doubly-robust CATE, refutation tests. | https://github.com/uber/causalml · https://github.com/py-why/EconML · https://github.com/py-why/dowhy |
| **scikit-uplift** | Uplift trees/forests, Qini/AUUC curves, uplift-at-k. | https://github.com/maks-sh/scikit-uplift |
| **Open Bandit Pipeline / Vowpal Wabbit / River** | Off-policy evaluation (IPS, DR, DM), contextual bandit algorithms (LinUCB, SquareCB-friendly), online learning. | https://github.com/st-tech/zr-obp · https://vowpalwabbit.org/ · https://riverml.xyz/ |
| **Splink** (UK MoJ) | Probabilistic record linkage at scale (Fellegi–Sunter), EM-trained match weights — the reliable, auditable ER engine. | https://github.com/moj-analytical-services/splink |
| **LightGBM / XGBoost / CatBoost** | Workhorse tabular models; CatBoost has native categorical + text features. | https://github.com/microsoft/LightGBM |
| **SHAP** | TreeSHAP explanations for the audit trail. | https://github.com/shap/shap |
| **MLflow** | Model registry, experiment tracking, `pyfunc` serving — matches the team's stack. | https://mlflow.org/ |
| **Prefect / Airflow / Dagster** | Retraining + feedback-loop orchestration. | https://dagster.io/ |

### 2.4 Relevant datasets for PS2

An honest, important finding: **there is no public dataset of collections call outcomes with RPC labels.** Every credible study in §2.1 is on a private bank/agency dataset. Our dataset strategy must therefore be *synthetic-first with proxy pre-training* (§8).

| Dataset | Size | Features | Target | Licence / access | PS2 relevance | Hackathon-usable? |
|---|---|---|---|---|---|---|
| **Home Credit Default Risk** | ~307k applications, 7 related tables | Demographics, bureau, prior applications, instalments, POS/cash balances, credit card balances | `TARGET` = default | Kaggle competition rules (open for research/hackathon) | Proxy for *account/recovery characteristics* and the "who responds to intervention" signal; the multi-table structure mimics our account↔contact-point joins. | **Yes** — but for pre-training/plumbing, not RPC. [URL](https://www.kaggle.com/c/home-credit-default-risk/data) |
| **Lending Club (public loan files)** | ~2.9M loans, 150+ columns | Loan terms, grade, income, employment, delinq history, payment history, `last_pymnt_d`, `recoveries`, `collections_12_mths_ex_med` | `loan_status`, recoveries | LendingClub public data (permissive-ish; check current terms) | Best available proxy for **recovery amount** targets and *time-to-payment* (survival). The `recoveries` field lets us prototype the EV formula. | **Yes** — strong for EV/survival prototyping. [URL](https://www.lendingclub.com/info/download-data.action) · [mirror](https://www.kaggle.com/datasets/wordsforthewise/lending-club) |
| **UCI "Default of Credit Card Clients" (Taiwan, 30k)** | 30,000 × 23 | Credit limit, sex/education/marriage/age, 6 months of bill/repayment statuses | default next month | CC BY 4.0, UCI | Small, clean, fast — perfect for the **baseline model + calibration + NB** pipeline sanity check. | **Yes** [UCI](https://archive.ics.uci.edu/ml/datasets/default+of+credit+card+clients) |
| **KDD Cup 2009 (churn/appetency/up-selling)** | 50k train / 100k test, 230+ features, missing-heavy | Customer/CRM features | churn, appetency, upselling | Public, academic | The **canonical dataset for "missing-not-at-random customer-contact features with a rare positive"** — our exact modelling pathology. | **Yes** [overview](https://link.springer.com/article/10.1007/s42979-024-02722-7) |
| **UCI Bank Marketing (telco/telemarketing campaigns)** | 41,188 × 21 (bank-additional variant) | age, job, marital, education, `contact` (cellular/telephone), `month`, `day_of_week`, `duration`, `campaign` (attempts), `pdays`, `previous` | `y` = term-deposit subscription | CC BY 4.0 | **The closest public analogue to a call-attempt dataset**: it literally contains number-of-attempts-this-campaign, days-since-previous-contact, contact channel, month/day, and *call duration* — i.e. our ring-duration/attempt-count/recency features. Used widely for best-time-to-call work. | **Yes — highest practical value.** [UCI](https://archive.ics.uci.edu/ml/datasets/bank+marketing) · [best-time-to-call discussion](https://datascience.stackexchange.com/questions/14124/predict-the-best-time-of-call) |
| **Telco Customer Churn (IBM/Kaggle)** | 7,043 × 21 | tenure, contract, services, payment method, monthly/total charges | `Churn` | Public, widely permissive | Proxy for "contact disappears over time" — useful for **decay/hazard** model development. | **Yes** [survey context](https://link.springer.com/article/10.1007/s42979-024-02722-7) |
| **Telco/Telecom Fraud Detection Dataset (synthetic)** | 10,000 call records × 14 features | historical caller behaviour, network reputation indicators, fraud signals; explicitly **overlapping distributions**, ~70/30 split | `fraud_label` | Vendor-distributed, synthetic | Skeleton for **suspicious/recycled contact-point detection features** (reputation, behaviour change, anomaly flags). | **Yes** — but synthetic. [gts.ai](https://gts.ai/dataset-download/telecom-fraud-detection-dataset/) |
| **Automated Fraudulent Phone Call Recognition datasets** (Xing et al.) | SC_1…SC_200 + RC_1–RC_6 (up to 1.5M normal calls / 400–600 fraud calls per month, 6 months) | CDR-derived call features | fraudulent-call label | Academic (paper) | Demonstrates **temporal drift in fraud detection** — the model degrades on later months. Direct warning for our contact-health model. | Partially [Wiley](https://onlinelibrary.wiley.com/doi/10.1155/2020/8853468) |
| **PAKDD 2009 / credit-scoring collection** (via JLZml repo) | Aggregated list | Various | default | Public mirrors | Fast source of multiple credit datasets for baseline benchmarking. | **Yes** [GitHub](https://github.com/JLZml/Credit-Scoring-Data-Sets) |
| **Give Me Some Credit** | 150k | revolving utilisation, DTI, delinquency counts | serious delinquency | Kaggle | Tabular baseline. | Yes |
| **IEEE-CIS Fraud Detection** | 590k transactions | identity + transaction + device | `isFraud` | Kaggle | Used by the TSF-style reassigned-number papers as a benchmark — useful for **recycled/compromise** head prototyping. | Yes [via TSF summary](https://www.researchgate.net/publication/359427393_Security_and_Privacy_Risks_of_Number_Recycling_at_Mobile_Carriers_in_the_United_States) |
| **Hillstrom MineThatData e-mail** | 64,000 customers, 3 arms (Mens / Womens / No e-mail) | recency, history, channel, zip, newbie | visit, conversion, spend | Public | **The standard multi-treatment uplift benchmark** — lets us prototype T-learner / X-learner and Qini *before* CN has randomized treatment logs. | **Yes — critical for uplift prototyping.** [via time-sensitive uplift paper](https://www.researchgate.net/publication/401286138_Modeling_Time-Sensitive_Causal_Uplift_in_Marketing_Campaigns) |

### 2.5 Best modelling approaches — the honest comparison (PS2)

| Family | Fit to PS2 | Hackathon MVP? | Production? | Verdict |
|---|---|---|---|---|
| **1. Logistic regression** | Interpretation, auditability, sign of effects. But underfits the interactions (time-of-day × channel × number-age). | ✔ baseline only | ✔ as the **auditable challenger / reason-code generator** | Keep as baseline + audit. Every regulator-facing explanation should be legible in a linear model. [P22 shows LR is *balanced* and generalises] |
| **2. XGBoost / LightGBM / CatBoost** | The right default: mixed categorical/numeric, missing values, monotone constraints, fast, SHAP-friendly. All published collections benchmarks land on GBM. | ✔✔ **PRIMARY** | ✔✔ **PRIMARY** | LightGBM for speed + monotone constraints; CatBoost if categorical cardinality (locality, agent, pincode) explodes. |
| **3. Random Forest** | Slightly worse than GBM on tabular, better calibrated natively (ensemble averaging), slower to serve. | △ | △ as ensemble member | Useful only as a calibration-friendlier ensemble member. |
| **4. Neural networks (MLP)** | Needs more data, worse calibration out of the box, no SHAP-native story. [P22] found MLP worst. | ✘ | △ only if we later learn embeddings (agent, locality) jointly | Not now. |
| **5. Survival analysis** | **Strong fit** — "how long until this contact point answers again?" is literally a time-to-event question with heavy right-censoring (never tested / not yet answered). [P4] shows it beats LR in soft collection. | ✔ (add as a 2nd model in MVP-days 5–7) | ✔✔ | Ship it. Use it for **contact decay** and for **untested contact points** (censoring is the correct treatment for "we never tried"). |
| **6. Time-to-event / hazard with competing risks** | Best fit for the *state* problem: from "last observed state", hazards of {answers, stays silent, number dies, wrong party answers}. SurvivalBoost implements competing risks directly. | △ | ✔✔ | This is the cleanest mathematical home for avoiding-vs-invalid-vs-recycled. See §9. |
| **7. Sequence models (LSTM/GRU/Transformer over the attempt sequence)** | Attractive: attempt sequences *are* sequences (ring duration, cause code, time-of-day over k attempts). But: needs long per-contact sequences, expensive, poorly calibrated, hard to explain, and cold-start contacts have no sequence. | ✘ for MVP | △ **only after** ≥6 months of dense per-number attempt logs, and only as an auxiliary embedding generator feeding the GBM | Defer. The FP7 lit review explicitly notes LSTM gains are real but come with data-hunger. |
| **8. Graph-based models** | **Underrated and high-value here.** Shared contact points across accounts (the same number appearing on 4 loans), associate/co-borrower links, agent↔borrower history. A contact point's RPC probability depends on *who else* it is connected to. GNNs are the published state of the art in entity resolution (GraphER, AAAI-20; xEM, 2025). | △ (graph *features* yes; GNN no) | ✔✔ | **Compute graph features in the MVP** (degree, shared-account count, neighbour RPC rate, PageRank). Upgrade to a GNN encoder in production. |
| **9. Learning-to-rank** | Correct framing when the real question is "which contact point on this account next?" — pairwise/listwise objectives (LambdaMART) directly optimise the ordering the agent sees. Proven in a near-identical ranking problem in geolocation (Forman 2021). | △ | ✔✔ | Add once we can define a slate (per-account candidate contact points). Strong differentiator: nobody ranks *contact points*. |
| **10. Contextual bandits** | Mandatory for the *exploration* requirement. Uber's published design (XGBoost + SquareCB) is the closest engineering analogue; Optimizely documents a ≥5% exploration floor. | ✘ (MVP = ε-greedy + VoI, not full bandit) | ✔✔ | Ship LinUCB/Thompson as the **allocation layer over actions**, not as the RPC model. |
| **11. Uplift / causal** | The only way to answer "does calling this number *cause* payment, or would they have paid anyway?" Highly relevant for frequency decisions and channel choice. | △ (needs randomisation or strong assumptions) | ✔✔ | MVP: proxy via Hillstrom + T-learner prototype. Production: causal forest / X-learner on top of a **deliberate randomised holdout**. |
| **12. Expected-value decision engine** | **Not a model — the product.** This is where money is made ([P2] marginal value per call; [P15] NBA stack). | ✔✔ **MUST** | ✔✔ | This is our core differentiator vs. "a churn model" team. |

#### Recommended combination (the short answer)

> **Contact-health factorisation on GBMs + a hazard/competing-risks head for decay + graph features + calibration + a constrained EV decision engine + a bandit exploration layer. Sequence models only as a later auxiliary embedding. Uplift only once randomised logs exist.**

That is: **GBM (workhorse) × survival (state & decay) × graph (relationship) × EV engine (decision) × bandit (exploration)**. Not "pick one".

### 2.6 Important technical insights from the PS2 research

1. **Separate the heads.** Contact ≠ commitment ≠ payment ([P1]). Any model that collapses these three into one label will be wrong in ways that cost money: a number that answers but never pays needs a *different* action from a number that never answers.
2. **Rank by marginal value, not probability** ([P2]). A 12% answer-probability number with a ₹40k balance beats a 40% answer-probability number with a ₹2k balance whenever cost-per-attempt is equal.
3. **Your model is miscalibrated before you fix it** ([P11], [P12]). EV decisions multiply probabilities by money; a 5-point ECE is a 5% systematic pricing error on every action.
4. **Boosting's distortion is fixable and cheap** — Platt/isotonic are one-liners via `CalibratedClassifierCV`. There is no excuse for shipping uncalibrated probabilities.
5. **Selection bias is structural, not incidental.** The policy (which numbers we chose to dial) determines which outcomes we observe. [P1]'s "contacted-only" variants and [P2]'s MDP framing are the two published ways of handling it. We handle it with **propensity logging + off-policy evaluation + a small randomised audit stream**.
6. **Temporal drift is real and measured.** The phone-fraud CDR study found models trained on earlier months degrade on later re-collections. Our contact-health model must be retrained on a rolling window with drift monitoring, not trained once.
7. **"Wrong-party contact" is measurable from transcripts** — speech analytics vendors literally score for "Right Party Contact language". That means we can *label* right-party status from conversation content instead of relying on agent dispositions alone.
8. **Phone recycling is a first-class privacy event with measured base rates** ([P16]: 83% of numbers offered to new subscribers were recycled; 66% still linked to PII).
9. **In India, recycling is regulation-shaped:** TRAI/DoT require at least a **90-day** gap before reallocation of a deactivated number, plus a quarantine period ([LiveLaw](https://www.livelaw.in/top-stories/once-a-mobile-number-is-deactivated-it-is-not-assigned-to-a-new-user-for-90-days-trai-to-supreme-court-241506), [Times of India](https://timesofindia.indiatimes.com/india/cant-bar-telecom-companies-from-reissuing-deactivated-numbers-says-supreme-court/articleshow/104993401.cms)). **This gives us a hard, defensible prior: any number silent for ≳90 days and then suddenly answering is a recycling suspect.** That is a rule you can code on day 1 and defend in an audit.
10. **Compliance is not a post-filter you bolt on — it is an action-space restriction.** RBI's outsourcing/recovery-agent framework (circular RBI/2022-23/108, 12 Aug 2022) bans calls before 8 AM / after 7 PM, bans third-party disclosure and public shaming, and holds the lender vicariously liable ([YuVerse summary](https://www.yuverse.ai/resources/posts/what-rbis-guidelines-on-recovery-agents-mean-for-your-collections-team)). Under **DPDP Act 2023 §8(3)** the fiduciary must keep personal data accurate — meaning *"this number is now someone else's"* is not merely an efficiency signal, it is a **compliance obligation to correct** ([DPDP overview](https://www.matters.ai/compliance/dpdp/dpdp-act-2023), [Beacon summary](https://beaconfiling.com/glossary/dpdp-act)).
11. **The null action must compete.** [P15]: if you don't model "do nothing", you systematically over-contact, burn attempts, and increase complaint risk.
12. **Attempts are a scarce, regulated resource.** Under Reg-F-style caps (7 calls / 7 days / per debt) each attempt has option value; "if an account has used six of seven weekly attempts with no contact, reserve the seventh for the statistically optimal window" `[vendor claim]` ([ainora](https://ainora.lt/blog/ai-predictive-dialing-debt-collection-contact-optimization)). Even under Indian rules, the principle holds: **some attempts should be banked, not spent.**

---

## 3. PS3 — EXISTING RESEARCH

### 3.1 Important papers

| # | Paper | Venue / Year | What it does | Why it matters to us | URL |
|---|---|---|---|---|---|
| G1 | **Rustogi — "What is the right Addressing scheme for India?"** | arXiv:1801.06540, 2018 (Delhivery) | Quantifies the Indian addressing problem: **~80% of Indian addresses are written w.r.t. a landmark typically 50–1500 m away**; only ~30% of addresses are in a structured format; **70% of sites have no street names**; landmarks rarely improve resolution to the doorstep; ~10M POIs in the top 200 cities make landmark cataloguing hard; **poor addresses cost India an estimated $10–14B/yr (~0.5% of GDP)**. | This is our **problem-definition citation**. It also warns us: don't assume "landmark ⇒ precise". Landmarks usually give a *neighbourhood-scale* answer, which is why **confidence radius** is the honest output, not the point. | [arXiv PDF](https://arxiv.org/pdf/1801.06540) *[paper / industry]* |
| G2 | **Rustogi — "Learning to Decode Unstructured Indian Addresses"** (AddFix, Delhivery) | Medium, 2018 | Describes AddFix: a **generative/graphical model** learns names of cities/localities/sub-localities/buildings/POIs and their **hierarchical relations and alternative spellings** from millions of e-commerce addresses + delivery-boy GPS, producing a **directed acyclic graph** of locality features; node boundaries learned from GPS; prediction by phonetic-distance fuzzy search tuned to Indian languages; outputs the full hierarchy + polygon boundaries. | The single most useful *system description* of Indian address intelligence. Notably: (i) v1 rules → 80–85% locality accuracy, **500 m** median geocode precision; (ii) v3 → **>90% locality accuracy, 200 m median**; (iii) it *discarded pincode-based sorting* in favour of **locality-based** sorting. Phonetic matching must be **India-specific** (standard engines miss Gurgaon↔Gudgaon). | [Medium](https://medium.com/@kabirrustogi/learning-to-decode-unstructured-indian-addresses-c80ffcda2e84) *[industry / practitioner]* |
| G3 | **Forman — "Getting Your Package to the Right Place: Supervised Machine Learning for Geolocation"** | ECML PKDD 2021 (Amazon Last Mile) | Learns an accurate delivery point per address from **noisy GPS of past deliveries**. States explicitly: *"Centroids and other center-finding methods do not serve well, because the noise is consistently biased."* Solution: a **novel adaptation of learning-to-rank** from IR, **enabling information fusion from map layers**. Offline: outstanding reduction in error distance. Online: **estimated millions in annualised savings**. Third-party geocodes are **not** used in the computation. | **The closest published system to PS3.** Three takeaways we adopt directly: (1) GPS bias ≠ noise → don't average; (2) **LTR over candidate points** with map-layer features is the winning formulation; (3) bootstrap with approximate geocoding but compute your own answer. | [mlanthology](https://mlanthology.org/ecmlpkdd/2021/forman2021ecmlpkdd-getting/) · [Springer](https://link.springer.com/chapter/10.1007/978-3-030-86514-6_25) *[paper]* |
| G4 | **"Geo-Spatially Informed Models for Geocoding Unstructured Addresses"** | COLING 2025 Industry Track | Rebuilds the India geocoding stack on an **address-specific RoBERTa** and compares: weakly-supervised triplet contrastive learning (Kothari & Sohoney) vs. **fully supervised multi-head H3-grid classification**. Reports drift accuracy vs. baselines: | Method | <100 m | <500 m | <1 km | |---|---|---|---| | Production system | 64.3% | 88.4% | 92.4% | | Google Maps API | 23.8% | 59.1% | 73.1% | | RoBERTa-triplet (original) | 56.7% | 73.4% | 75.6% | | RoBERTa-triplet (modified) | 65.7% | 83.1% | 85.1% | | **Multi-head classification** | **77.2%** | **91.2%** | **93.3%** | Claims **+20% drift-accuracy within 100 m vs. prior SOTA** and **+54% vs. the commercial system**; also an **8% reduction in incorrect delivery-hub assignments**. | Gives us *numbers to beat* and a decisive architectural lesson: **explicitly modelling hierarchical spatial resolution (H3 levels) beats implicit spatial learning.** Also: a plain commercial geocoder gets only **23.8% within 100 m on Indian addresses** — a devastating baseline for the pitch. | [ACL Anthology PDF](https://aclanthology.org/2025.coling-industry.19.pdf) *[paper]* |
| G5 | **Kothari & Sohoney — "Learning Geolocations for Cold-Start and Hard-to-Resolve Addresses via Deep Metric Learning"** | EMNLP 2022 Industry Track (Amazon) | Weakly-supervised **deep metric learning** encoding geospatial distance semantics into address embeddings; resolves cold-start "hard-to-resolve" addresses to **neighbourhood** granularity. Results: **22% (India) and 55% (UAE) reduction in delivery defects**; **43% (IN) / 90% (UAE) reduction in p50 distance** vs. the existing production system. | The canonical "we have no labels for new addresses, but we have *proximity* as weak supervision" method. **This is our cold-start strategy for addresses that have never had a field visit.** | [ACL Anthology](https://aclanthology.org/2022.emnlp-industry.33/) · [PDF](https://aclanthology.org/2022.emnlp-industry.33.pdf) *[paper]* |
| G6 | **GeoIndia / GeoIndia-V2** | EMNLP 2024 Industry / ACM 2025 | **GeoIndia**: Seq2Seq geocoding for Indian addresses. **GeoIndia-V2**: unifies a **Graphormer** (over a fine-grained neighbourhood-connectivity graph built from last-mile delivery data) with a transformer LM trained from scratch on proprietary Indian address data, fused via **Key Modulated Cross-Attention (KMCA)** to handle colloquial usage, inconsistent formatting and multilinguality. | The state of the art in *architecture design* for Indian geocoding: **graph topology + language model, cross-attended**. We will not build this in 2 weeks, but it tells us the direction of travel and gives us a "vision slide". | [ACM DL](https://dl.acm.org/doi/10.1145/3746252.3761512) *[paper]* |
| G7 | **Chatterjee et al. — "SAGEL: Smart Address Geocoding Engine for Supply-Chain Logistics"** | ACM SIGSPATIAL 2016 | Pre-processes the address query, retrieves matching address documents from a **high-quality structured corpus (from a commercial map data provider)**, and **ranks candidates using graph techniques**. Motivation: "fuzzy region boundaries, dynamic topography and lack of convention in spellings of toponyms". | Historic but instructive: (i) candidate-generation + ranking beats single-shot matching; (ii) the approach is **bounded by corpus quality** — which is exactly why CN's own field data is a strategic asset, not a nice-to-have. Its benchmark performance in G4 (17.7% <100 m) shows how far corpus-bound methods fall short. | [SIGSPATIAL accepted papers](https://sigspatial2016.sigspatial.org/accepted-papers/) · [ACM ref via G4](https://aclanthology.org/2025.coling-industry.19.pdf) *[paper]* |
| G8 | **Srivastava et al. — "GeoCloud"** | KDD 2020 | Parses the address corpus and creates a **geo-polygon for each address chunk using historical delivered data**; uses heavy domain-knowledge heuristics for parsing into chunks. | The polygon idea is useful for *area* reasoning; the critique in G4 (not scalable, heuristics limit retraining) is the reason we prefer learned embeddings + LTR over hand-built chunk rules. | [via G4](https://aclanthology.org/2025.coling-industry.19.pdf) *[paper]* |
| G9 | **Matci & Avdan — "Address standardization using NLP for improving geocoding results"** | *Computers, Environment & Urban Systems* 70, 2018 | NLP-based parsing + **misspelling correction (Levenshtein / Match Rating) + abbreviation expansion + reformatting**; reports a **50% improvement in capturing coordinates** on test sets. | Quantitative proof that **normalisation alone is worth ~50% geocoding capture improvement** — i.e. a cheap, high-ROI first module. | [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0198971517300455) *[paper]* |
| G10 | **"Improving a Street-Based Geocoding Algorithm Using Machine Learning"** | Applied Sciences | Three modules — **address parsing → address matching (ML over combined similarity metrics) → address locating**; argues that combining multiple fuzzy similarity metrics through a learner beats any single metric. | Directly supports our "similarity-ensemble → learned matcher" design rather than picking one fuzzy metric. | [PDF](https://pdfs.semanticscholar.org/bdf5/05865133fa76289f1998d7e832e0bf0ceccf.pdf) *[paper]* |
| G11 | **DeepParse** (Abid et al., IEEE 2018) and **deepparse** (GRAAL-Research) | IEEE 2018 / arXiv:2006.16152 | Neural address parsers. DeepParse: character + trigram + word granularity into BLSTM, robust to OCR noise, **90.44% on CoNLL-2003**. deepparse: **subword (BPEmb/fastText) embeddings + Seq2Seq**, a **single model for multiple countries**, ~**99% accuracy** on trained countries, and **zero-shot transfer to 80% of 41 countries**; MIT-licensed Python package. | Gives us a *second, neural* parser to ensemble with libpostal, and an explicitly **multinational + multilingual** design. | [IEEE](https://ieeexplore.ieee.org/document/8615844/) · [arXiv](https://arxiv.org/pdf/2006.16152) · [code](https://github.com/GRAAL-Research/deepparse) *[paper + code]* |
| G12 | **libpostal** (Barrentine / Mapzen; retrained by Senzing) | Mapzen, 2016 → present | Multilingual address parsing + normalisation: **CRF parser** trained on ~1B addresses (Senzing model: 1.2B records, 230+ countries, 100+ languages), **language classification** (FTRL logistic regression on OSM), **60+ languages of normalisation**, numeric-expression parsing (30+ languages), CLDR transliteration, script detection. MIT. | The default first module. Crucially it gives **language classification and transliteration** — the two things Indian addresses need most. Its own README example is literally an Indian address. | [GitHub](https://github.com/openvenues/libpostal) · [Mapzen engineering post](https://www.mapzen.com/blog/inside-libpostal/) · [Senzing](https://senzing.com/what-is-libpostal/) *[code + paper]* |
| G13 | **Newson & Krumm — "Hidden Markov Map Matching Through Noise and Sparseness"** | ACM SIGSPATIAL 2009 | HMM over road network states; accounts for measurement noise and road layout; **test-set released publicly**; works down to 30 s sampling with ~30 m noise; 4.07 m std dev / ≤47 m worst error on clean data; three insights: correct matches are nearby, successive matches are linked by simple routes, **some points are junk and should be ignored**. | The standard for snapping noisy GPS to the network. The "**some points are junk — ignore them**" insight is exactly our field-integrity problem, formalised. Also: we can use the **public HMM test set** to validate our map-matching code. | [ACM DL](https://dl.acm.org/doi/10.1145/1653771.1653818) · [slides](https://www.slideshare.net/slideshow/hiddenmarkovmapmatchingthroughnoiseandsparsenessacmsigspatial2009finalpptx/257638619) *[paper]* |
| G14 | **Fast Map Matching (FMM)** | 2020+ | HMM + precomputation, open-source implementation; handles large-scale GPS data efficiently. | Production-grade map matching without writing it ourselves. | [via map-matching survey](https://www.researchgate.net/publication/348162025_Hidden_Markov_map_matching_based_on_trajectory_segmentation_with_heading_homogeneity) *[paper + code]* |
| G15 | **Zandbergen — geocoding positional error studies** | 2009 + replications | Street-geocoding positional error typically **~40–75 m**; rural addresses dramatically worse — in one study **95% of rural addresses geocoded within 2,872 m**, suburban within 421 m, urban within 152 m. Error is **spatially clustered and systematically biased** (e.g. displaced north in parts of Queens, south in northern Manhattan). | Two things: (a) the *magnitude* of the problem we are fixing, and (b) **error is spatially structured** → uncertainty should be modelled spatially, not globally. | [ResearchGate summary](https://www.researchgate.net/publication/343622122_Geocoding_Error_Spatial_Uncertainty_and_Implications_for_Exposure_Assessment_and_Environmental_Epidemiology) *[paper]* |
| G16 | **GeoConformal Prediction (GeoCP)** | *Annals of the AAG* 115(8), 2025 / arXiv:2412.08661 | Extends conformal prediction with **geographic weighting** (kernel by distance from test point to calibration points), giving **location-varying prediction intervals with coverage guarantees**. Housing-price regression: GeoCP coverage **93.67%** vs bootstrap max **81–68%**; in spatial interpolation its uncertainty **aligns with Kriging variance**. | **This is how we produce the confidence radius.** Global isotonic-style calibration gives one width everywhere; GeoCP gives *this address in this locality* a radius with a stated coverage — which is exactly what a field agent needs ("90% chance the borrower's home is within 240 m of this pin"). | [arXiv](https://arxiv.org/html/2412.08661v1) · [journal](https://ideas.repec.org/a/taf/raagxx/v115y2025i8p1971-1998.html) *[paper]* |
| G17 | **Google Address Descriptors** | Google Maps Platform, 2023 | Reverse-geocoding feature that returns the **most relevant landmarks and area names relative to an address**, using ML signals on **proximity, prominence and visibility**, informed by **on-the-ground research in Indian cities**. Launched explicitly because Indian users express addresses through landmarks. | (a) Validates that "landmark-based direction" is a *product requirement*, not a hack; (b) gives us a commercial API to call in the MVP; (c) the *signals* (proximity, prominence, visibility) are exactly the features our own landmark ranker should use. | [Google Maps Platform blog](https://mapsplatform.google.com/resources/blog/launching-address-descriptors-make-it-easier-find-addresses-using-landmarks-indian-cities/) *[industry]* |
| G18 | **GHOST: Grid-based Home detection via Stay-Time** | arXiv:2605.20429, 2026 | Infers **home location** from mobile GPS by ranking grid cells by **total stay-time** (max timestamp − min timestamp within the cell), filtered to nighttime (default 22:00–06:00) with a weekend-daytime fallback; ties broken by unique nights then point count; then sub-divides the winning cell into 2–3 m bins and takes the densest bin centroid. **Validated against self-reported home labels** (MIT BostonWalks, 377 users; GeoTracker, 10 volunteers) against five baselines (all-time mean-shift clustering, stay-point method, DBSCAN, K-Means++, scikit-mobility). | **The direct answer to "is this GPS the borrower's home?"** It outperforms clustering methods, is robust to GPS noise, is linear-time (scales), and has an open-source implementation. We adopt the stay-time criterion and extend it with outcome-conditioning. | [arXiv](https://arxiv.org/html/2605.20429) · [plain-language audit](https://pith.science/paper/2605.20429) *[paper]* |
| G19 | **Trip-purpose inference from GPS via POI semantic zones + Pareto calibration** | arXiv:2605.01257, 2026 | Three-stage pipeline: (1) extract **staypoints**; (2) build **semantic zones from POIs**; (3) infer activity type. Mandatory activities (home/work/school) use **weighted Bayesian bidding** across repeated observations (cross-day persistence × POI semantic prior); non-mandatory activities use a unified probabilistic score over time-of-day and duration distributions. Confidence is **calibrated via multi-phase Pareto optimisation** against household-survey reference distributions. | **The direct answer to "is this a home, a workplace, a shop or a road?"** It provides the *architecture* (staypoints → POI zones → Bayesian activity inference → calibrated confidence) and the key empirical finding that **home is the most robust inference (99.72%) because it relies on spatial recurrence rather than POI context**, whereas work (93.29%) and school (86.18%) degrade with POI incompleteness. | [arXiv](https://arxiv.org/html/2605.01257) *[paper]* |
| G20 | **POI-ID: recognising places of interest from unreliable GPS via spatio-temporal density + line intersections** | *Pervasive & Mobile Computing* / ScienceDirect | Ranks candidate POIs at **building-level accuracy** from highly inaccurate GPS, using **intersecting GPS line-segment counts** to distinguish "inside building A" from "moving around it". Explicitly addresses urban-canyon and indoor error where the *nearest building to the centroid is the wrong building*. | Solves the exact failure mode we care about: borrower met *inside* a shop next to their house. The line-intersection trick is a cheap, clever feature we can compute from GPS trails. | [ScienceDirect](https://sciencedirect.com/science/article/abs/pii/S1574119214001357) *[paper]* |
| G21 | **Detecting stop episodes from GPS trajectories with gaps** | Springer, 2017 | DBSCAN-based stay-point detection that **explicitly handles gaps** (linear interpolation), requiring both spatial density and time duration; validated on 9 weeks of trajectories. Shows **gap treatment materially improves detection**. | Field visits have gaps (app killed, tunnel, phone locked). Handling gaps explicitly is required, not optional. | [Springer](https://link.springer.com/chapter/10.1007/978-3-319-40902-3_23) *[paper]* |
| G22 | **Clustering-based location/address resolution for Q-commerce (India)** | ACM, 2022 | Trains models on two synthetically constructed sets — **Gaussian location perturbation** and **address-pair swapping** — from accurate address–location pairs; ensemble gives **84.5% precision / 49% recall** at detecting *incorrect* stored GPS coordinates for Indian addresses. | Two gifts: (i) a **synthetic data generation recipe** for location-correction models; (ii) evidence that a *correction/detection* framing (is this stored location wrong?) is practical — relevant to our GPS-integrity model. | [ACM DOI](https://doi.org/10.1145/3564121.3564800) *[paper]* |
| G23 | **Geospatial foundation models & location embeddings** | Esri GDFM; PlaceFM (arXiv:2507.02921); PDFM | Esri's **Geodemographic Foundation Model**: multi-view autoencoder over 5,000+ socio-demographic/environmental variables → **256-dim embedding per H3 cell**. **Global Location Encoder (Sentinel-2)**: embeddings from satellite imagery. **PlaceFM**: training-free POI-graph place embeddings, multigranular, >10× faster than baselines. **PDFM**: heterogeneous graph over counties/postal codes → GNN embeddings; benchmarked as improving subnational population estimation (median **20.1%** unexplained-variance reduction) though **unevenly across space and scale**. | Where this *helps us now*: using H3-cell embeddings as **features** (deprivation/urbanity) in both PS2 and PS3 — e.g. contact health and field-visit success differ systematically by locality. Where it *doesn't*: none of these give sub-100 m address resolution. Nice-to-have, not MVP. | [Esri GDFM](https://www.esri.com/arcgis-blog/products/arcgis-pro/geoai/every-place-has-a-fingerprint-how-foundation-models-are-learning-locations) · [PlaceFM](https://arxiv.org/html/2507.02921v2) · [PDFM benchmark](https://arxiv.org/abs/2605.01650) *[paper + industry]* |
| G24 | **Toponym resolution / geoparsing survey** | JOIV; Wikipedia; Remote Sensing 12(3):41 | Survey of extracting and disambiguating place names: **map-based, knowledge-based (gazetteer: GeoNames, OSM), and ML methods**; clustering-based spatial-density disambiguation; context-hierarchy fusion; geoparsing goes beyond geocoding because references are ambiguous ("Al Hamra" is several places). Tools: CLAVIN, GeoTxt, Edinburgh Geoparser, geoparsepy. | Our landmark tokens ("Hanuman temple") are *toponyms with many referents*. The survey tells us we need **candidate sets + contextual disambiguation by proximity to the locality/pincode**, not a single dictionary lookup. | [JOIV survey](https://joiv.org/index.php/joiv/article/download/2763/1236) · [Wikipedia](https://en.wikipedia.org/wiki/Toponym_resolution) *[paper]* |
| G25 | **H3 (Uber) — hexagonal hierarchical spatial index** | Open source | Earth divided into hierarchical hexagons at **16 resolutions**; each cell has a 64-bit index; parent/child traversal, `k-ring`, `polyfill`; integrated into BigQuery/Snowflake/ClickHouse; bindings in Python/JS/Java/Go. | Our **spatial key for everything**: hex-index features for PS2 (locality-level contact health), grid classes for PS3 (multi-head classification targets per G4), and cheap map aggregation in the dashboard. | [H3 docs](https://h3geo.org/docs/) · [overview](https://mapular.com/glossary/h3) *[code]* |

### 3.2 Industry approaches to Indian / unstructured geocoding

| System | Technique | Notable claim | Source |
|---|---|---|---|
| **Google Maps Platform / Address Descriptors** | Proprietary POI + ML landmark ranking (proximity, prominence, visibility) | Landmark-aware reverse geocoding built specifically for Indian address culture; free with Reverse Geocoding. | [blog](https://mapsplatform.google.com/resources/blog/launching-address-descriptors-make-it-easier-find-addresses-using-landmarks-indian-cities/) *[industry]* |
| **Delhivery AddFix** | Unsupervised generative model → locality DAG → GPS-derived polygons → phonetic fuzzy search | Rules v1: 80–85% locality accuracy, **500 m** median precision. Learned v3: **>90% locality accuracy, 200 m median**. Enabled **abandoning pincode-based sorting**. | [Medium](https://medium.com/@kabirrustogi/learning-to-decode-unstructured-indian-addresses-c80ffcda2e84) *[industry]* |
| **Amazon Last Mile (geolocation)** | Learning-to-rank over candidate points fusing map layers; explicitly rejects centroids due to **biased** noise | "Outstanding reduction in error distance"; online experiments estimated **millions in annualised savings**. | [ECML PKDD 2021](https://mlanthology.org/ecmlpkdd/2021/forman2021ecmlpkdd-getting/) *[paper]* |
| **Amazon India (hard-to-resolve addresses)** | Weakly-supervised deep metric learning on address embeddings | **22% fewer delivery defects (IN)**, **43% lower p50 distance** vs. production. | [EMNLP 2022](https://aclanthology.org/2022.emnlp-industry.33/) *[paper]* |
| **Mappls / MapmyIndia** | 30 years of India-first map data, ISRO/NavIC partnership, eLoc addresses, village-level coverage; **offline maps via NaviMaps** | Deepest India + South Asia coverage; **API pricing sales-only**; logo cannot be removed per terms. | [NextBillion comparison](https://nextbillion.ai/feeds/blog/indian-alternative-google-maps) · [swadeshiapps](https://swadeshiapps.com/development/mapmyindia-maps) *[industry]* |
| **Ola Maps** | India-only maps built on Ola ride data; Directions/Autocomplete/Geocoding/Reverse Geocoding/Tiles; Indian data residency | **500,000 free API requests/month** (current); launch offer was 5M; paid tiers claimed ~50% of Google's India rates; SOC2 + ISO 27001. | [maps.guru comparison](https://maps.guru/blog/google-maps-alternatives-indian-startups) · [NextBillion](https://nextbillion.ai/feeds/blog/indian-alternative-google-maps) *[industry]* |
| **Google Maps Geocoding API** | Global geocoder | **$5 / 1,000 requests**; $200/mo free credit ≈ 40k requests; 500k requests/month ≈ **$2,300/mo**. And on Indian addresses: only **23.8% within 100 m** (per G4). | [csv2geo pricing comparison](https://csv2geo.com/blog/geocoding-api-pricing-compared-real-cost-2026) · [G4](https://aclanthology.org/2025.coling-industry.19.pdf) *[industry + paper]* |
| **Nominatim (OSM)** | Open-source geocoder over OSM data; public instance limited to 1 req/s and **bulk geocoding prohibited**; self-hosting needs ~64 GB RAM, ~1 TB SSD, ~**$200–500/mo** hosting | The realistic **offline/self-hosted** backbone; the only option with no per-request cost and no vendor lock. | [comparison](https://continuuiti.com/blog/best-geocoding-api/) · [csv2geo](https://csv2geo.com/blog/geocoding-api-pricing-compared-real-cost-2026) *[industry]* |
| **Pelias / Photon** | OSM-based open geocoding stacks with ranking layers | Alternative self-hosted stacks if Nominatim's ranking is insufficient. | [Senzing on libpostal/Pelias lineage](https://senzing.com/what-is-libpostal/) |
| **Geocoding consensus / accuracy practice** | Multi-vendor agreement: if Google and Mapbox agree within 100 m, use it; if they disagree by >500 m, flag for manual review | Claimed **94–98% effective** catch rate for bad geocodes; SafeGraph reports **2.17 m** average deviation in tested areas vs. OSM/Google 15 m errors. | [theneuralbase](https://theneuralbase.com/ai-for-logistics/learn/intermediate/address-quality-geocoding/) · [SafeGraph guide](https://www.safegraph.com/guides/the-ultimate-guide-to-safegraphs-geocode-data/) *[vendor claim]* |
| **Matching-type discipline** | Geocoders return `match_type` ∈ {exact, interpolated, fallback} + confidence 0–1; the `accuracy` field means point-vs-centroid and is **not** a quality signal | "Downstream users often accept any non-null result without checking match type, which is exactly how low-confidence geocodes end up causing operational problems." | [Stadia Maps](https://stadiamaps.com/learn/geocoding/) · [SafeGraph](https://www.safegraph.com/guides/the-ultimate-guide-to-safegraphs-geocode-data/) *[industry]* |

### 3.3 Open-source projects for PS3

| Project | Role in our stack | URL |
|---|---|---|
| **libpostal** | Address parsing (CRF), language ID, normalisation (60+ languages), transliteration. MIT. | https://github.com/openvenues/libpostal |
| **deepparse** (GRAAL) | Neural multinational address parser (subword + Seq2Seq), 99% on trained countries, zero-shot to 80% of 41 countries. MIT. Python package. | https://github.com/GRAAL-Research/deepparse |
| **IndicXlit / IndicLID / IndicBERT / IndicNER / IndicTrans2** (AI4Bharat, IIT-M) | Roman↔native transliteration (Aksharantar: **26M pairs, 21 languages, 12 scripts**), language ID for romanised Indic text (**47 classes**, Bhasha-Abhijnaanam test set), multilingual ALBERT (12 languages), Indic NER (11 languages), translation (22 languages). | https://models.ai4bharat.org/ · https://github.com/AI4Bharat/indicnlp_catalog · https://ai4bharat.iitm.ac.in/areas/xlit/ |
| **Indic NLP Library / iNLTK / BNLP** | Tokenisation, normalisation, script conversion for Indic text. | https://github.com/AI4Bharat/indicnlp_catalog |
| **Dakshina dataset** | Latin + native script for 12 South Asian languages, ~300k word pairs, 120k sentence pairs — for training/evaluating transliteration and romanisation normalisation. | https://github.com/google-research-datasets/dakshina |
| **RapidFuzz** | Fast fuzzy string matching (Levenshtein, Jaro-Winkler, token-ratio) — the base layer under our Indian-language phonetic matcher. | https://github.com/rapidfuzz/RapidFuzz |
| **jellyfish / metaphone / Double Metaphone ports; Indic phonetic variants** | Phonetic keys. Add India-specific rules (Gurgaon↔Gudgaon, V↔B/W, bh↔b, aspirates, vowel-length collapse) on top — AddFix's explicit lesson. | https://github.com/jamesturk/jellyfish |
| **Nominatim** (PostgreSQL + PostGIS) | Self-hosted geocoding for offline/bulk use; also the base for custom ranking. | https://github.com/osm-search/Nominatim |
| **Pelias / Photon** | Alternative OSM geocoding stacks. | https://github.com/pelias/pelias · https://github.com/komoot/photon |
| **H3** | Hexagonal hierarchical indexing for grid-class targets, aggregation, and the offline app. | https://github.com/uber/h3 |
| **OSMnx / GeoPandas / Shapely / pyproj / Rasterio** | OSM download & analysis, geometry ops, projection maths. | https://github.com/gboeing/osmnx · https://geopandas.org/ |
| **MovingPandas / scikit-mobility** | Trajectory objects, stop detection, mobility measures (scikit-mobility is one of GHOST's baselines). | https://github.com/anitagraser/movingpandas · https://github.com/scikit-mobility/scikit-mobility |
| **Fast Map Matching (FMM) / OSRM** | HMM map matching at scale; routing for travel-cost and dwell/travel-time features. | https://github.com/cyang-kth/fmm · http://project-osrm.org/ |
| **GeoConformal implementation / MAPIE** | Model-agnostic conformal prediction; MAPIE for the standard case, custom kernel weighting for the geo-variant. | https://github.com/scikit-learn-contrib/MAPIE |
| **Splink** | Entity resolution for addresses and contact points (Fellegi–Sunter with EM). | https://github.com/moj-analytical-services/splink |
| **Sentence-Transformers / fastText / BPEmb** | Address embeddings; fastText is what the supervised-geocoding baseline used (grid-ID classification). | https://github.com/facebookresearch/fastText |
| **Bhashini / ULCA (Govt. of India)** | Indic ASR/TTS/translation APIs — for voice remarks in regional languages and for normalising regional-language address tokens. | https://bhashini.gov.in/ · https://github.com/AI4Bharat/indicnlp_catalog |

### 3.4 Datasets for PS3

| Dataset | Size | Features | Target / use | Licence | PS3 relevance | Hackathon-usable? |
|---|---|---|---|---|---|---|
| **OpenStreetMap India (via Overpass API)** | India has millions of POIs, named shops, temples, schools, roads; coverage varies sharply by city tier | Lat/lon, name (often native script + transliteration), `amenity`/`shop`/`place` tags, road network, building polygons | **Landmark gazetteer + POI semantic zones + road network for map matching** | ODbL (attribution + share-alike) | The backbone of landmark resolution — and the *same* source `libpostal` and AddFix-style systems use. | **YES — primary** [Overpass](https://overpass-turbo.eu/) |
| **Google Address Descriptors (reverse geocoding)** | Per-coordinate landmark list | Ranked landmarks + area names relative to a coordinate | Landmark directions + validation of our own landmark ranker | Google Maps Platform ToS (paid/attribution) | Directly solves "landmark-based directions" for the MVP | Yes (free tier) [blog](https://mapsplatform.google.com/resources/blog/launching-address-descriptors-make-it-easier-find-addresses-using-landmarks-indian-cities/) |
| **India Post PIN code directories + pincode polygons** | ~**19,312 pincode polygons** (data.gov.in 2025 layer); DataMeet ~155k-row pincode→city/district/state lookup used by an Indian address parser | Pincode ↔ district/state/city; polygon boundaries | Anchor + constraint: predicted location must fall inside (or within a tolerance of) the stated pincode | **GODL-India** (data.gov.in), CC0/CC-BY for DataMeet | The single cheapest **precision gain**: it eliminates whole classes of geocoding error | **YES — primary** [bharatlas pincode layer](https://bharatlas.com/) · [india-geodata](https://github.com/yashveeeeeeer/india-geodata) · [Indian Address Parser using 155k pincode lookup](https://github.com/priyanshi0609/Indian-Address-Parser) |
| **DataMeet India maps** | India, state, district, constituency boundaries; municipal ward boundaries for 28 cities; pincode boundaries | Polygons | Spatial joins, admin normalisation | CC BY 4.0 / CC0 | Standard reference geometry | **YES** [india-geodata](https://github.com/yashveeeeeeer/india-geodata) |
| **bharatlas** | Catalog: LGD boundaries state→village, 6,393 blocks, city wards, **63k pincode polygons**, electoral, plus REST API (`/locate`, `/nearby`) and MCP server | Boundaries + point-in-polygon API | Offline/online reverse-geocoding to admin hierarchy | Mixed CC0/CC-BY/GODL | Ready-made **offline reverse geocoder** and API for the demo | **YES** [bharatlas.com](https://bharatlas.com/) · [GitHub](https://github.com/sarathsomana/geodata) |
| **india-geodata (55+ datasets)** | Admin (state→habitation), electoral, census, roads (PMGSY/GeoSadak, NH), buildings (AMRUT/GSDL/VEDAS urban footprints), healthcare, education, urban wards/slums/localities, nightlights, population density, rivers, and more — in Parquet/GeoJSON/Shapefile/PMTiles/GeoTIFF | Multi-layer | Feature enrichment + map basemaps + building footprints for "is this a house or a shop?" | **CC BY 4.0** | Probably the single highest-value one-stop download for a hackathon | **YES — primary** [site](https://yashveeeeeeer.github.io/india-geodata/) · [GitHub](https://github.com/yashveeeeeeer/india-geodata) |
| **Microsoft / Google Open Buildings (India)** | Hundreds of millions of building footprints | Building polygons | Snap predictions to *a building*; distinguish dwelling vs. commercial via size/shape + POI context | Open licences (check per-release terms) | Turns a 200 m radius into "this building" | Yes [india-geodata buildings layer](https://yashveeeeeeer.github.io/india-geodata/) |
| **SHRUG (Development Data Lab)** | **~600,000 villages and ~8,000 towns**, dozens of datasets over 25 years, all linked by shared geographic IDs; ~90% georeferenced with polygons | Demographics, non-farm employment, public goods, night lights, forest cover, constituency outcomes | Rural/town **context features**; village/town polygon joins; village-level denominators | Open access (Harvard Dataverse DOI:10.7910/DVN/DPESAK) | For rural and small-town borrower addresses, SHRUG's village polygons give us a *prior footprint* when text evidence is only "village + landmark" | **Yes** (4.0 GB zip if using the Dataverse mirror; the DDL site offers modular downloads) [devdatalab.org/shrug](https://www.devdatalab.org/shrug) · [Dataverse](https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi%3A10.7910%2FDVN%2FDPESAK) |
| **GeoLite / GeoLite2 city** | Global | Lat/lon per location | Cheap *coarse* prior for "which city is this number/address in" | Proprietary but free tier | Sanity checks on pincode↔coordinate consistency | Yes |
| **Geolife GPS Trajectories** | **182 users, 17,621 trajectories, ~1.2M km, ~48,000 hours**, 2007–2012, Beijing + other Chinese cities; transportation-mode labels | Timestamped lat/lon | **Develop and test our field-visit pipeline end-to-end**: staypoint detection, GPS cleaning, home/work classification, map matching, robustness to noise | Free for research (MSRA) | Small but *ground-truth-rich* and has been the standard benchmark for >15 years. Perfect for a hackathon: small enough to load, rich enough to prove the pipeline. | **YES — primary for GPS** [user guide](https://www.microsoft.com/en-us/research/publication/geolife-gps-trajectory-dataset-user-guide/) · [processed version](https://github.com/taspinar/GPSMachineLearning) |
| **T-Drive** | **10,357 taxis, 1 week**, Beijing, ~15M points | Timestamped lat/lon | Large-scale map matching / road network validation (Mumbai-Pune style tests exist) | Free for research (MSRA) | Stress-test map matching | Yes [via survey](https://www.osti.gov/servlets/purl/2267639) |
| **Porto Taxi Trajectories** | ~1.7M trips | Polyline GPS + timestamps | Trajectory ML benchmarks | Public (Kaggle/Figshare) | Optional | Yes [via WorldTrace paper](https://kdd.org/kdd2025/wp-content/uploads/2025/07/paper_9.pdf) |
| **WorldTrace** | Millions of trajectories, billions of points, global, **1 Hz** sampling, includes **India**, with trip metadata | GPS + metadata | Fine-grained trajectory modelling and route/road inference | Open (check terms) | Modern, large, and includes India — better than Geolife for distribution realism | Yes [KDD 2025 paper](https://kdd.org/kdd2025/wp-content/uploads/2025/07/paper_9.pdf) |
| **MIT BostonWalks / GeoTracker** | 377 users with **self-reported home labels**; 10 volunteers with self-reported coordinates | GPS + ground-truth home | **Validate our home-detection code against ground truth** (used by GHOST) | Public / paper-associated | The cleanest validation set for the "is this the home?" question | **YES** [GHOST paper](https://arxiv.org/html/2605.20429) |
| **Aksharantar / Dakshina** | **26M transliteration pairs, 21 languages, 12 scripts**; Dakshina: ~300k word pairs, 120k sentence pairs, 12 languages | Roman ↔ native script word pairs | Train/fine-tune/fuse transliteration for address tokens; phonetic normalisation | Open (AI4Bharat / Google Research) | Directly attacks "same landmark, 12 spellings" | **YES** [AI4Bharat Xlit](https://ai4bharat.iitm.ac.in/areas/xlit/) |
| **CLDR / ICU transliteration data** | Global per-script transliteration rules | Rules | Fallback transliteration, numeric-expression parsing (as libpostal does) | Unicode licence | Low effort fallback | Yes |
| **Bhuvan (ISRO)** | Satellite/terrain/admin layers | Imagery, boundaries | Visual verification in demo | ⚠ **Restrictive: Bhuvan's ToS forbid use outside viewing without written authorisation** | **Do not build on it.** Use OSM + open government data instead. | **NO — licensing trap** [OSM Help thread quoting Bhuvan ToS](https://help.openstreetmap.org/questions/77050/indian-government-mapping-system-bhuvan) |
| **GeoNames** | Global gazetteer (~25M names) | Names + coords + population + admin hierarchy | Candidate generation and disambiguation (used by libpostal) | CC BY 4.0 | Standard gazetteer component | Yes [libpostal docs](https://www.mapzen.com/blog/inside-libpostal/) |

### 3.5 Best modelling approaches (PS3)

| # | Approach | Fit | MVP? | Production? | Notes |
|---|---|---|---|---|---|
| 1 | **Standard geocoding APIs** (Google/Mappls/Ola/Nominatim) | Necessary but insufficient: only ~23.8% within 100 m on Indian addresses (G4); Ola Maps free tier is generous. | ✔ for **candidate generation** | ✔ as one candidate source | Never trust a single geocoder. Use match_type + confidence, and treat "fallback" matches as locality-only. |
| 2 | **Address parsing + normalisation** | 50% coordinate-capture improvement from standardisation alone (G9). libpostal (CRF) + deepparse (neural) ensemble. | ✔✔ | ✔✔ | Cheapest, highest-ROI first module. Also produces language ID needed downstream. |
| 3 | **Multilingual NLP / NER** | IndicNER/IndicBERT for entity tagging; IndicLID for language ID; IndicXlit for transliteration. | ✔ (targeted: only for landmark/entity spans) | ✔✔ | Don't build a general NLU; extract *location mentions*. |
| 4 | **Landmark extraction & normalisation** | The core of Indian addressing. Build a **learned landmark gazetteer** (AddFix-style) from CN's own field data + OSM, with alias graph + phonetic keys. | ✔✔ | ✔✔ | Our moat. Google's Address Descriptors validates the requirement. |
| 5 | **Entity resolution** | Same landmark, many spellings; same address, many formats; same phone, many accounts. Splink (probabilistic) → GNN (GraphER/xEM) later. | ✔ (Splink + rules) | ✔✔ | Feeds both PS2 (contact-point graph) and PS3 (alias graph). |
| 6 | **GPS clustering** | Needed for visit clusters, but **plain clustering underperforms** (GHOST beat mean-shift, DBSCAN, K-Means++, scikit-mobility). | △ | △ | Use clustering as a *feature*, not the estimator. |
| 7 | **Bayesian location estimation** | Weighted Bayesian bidding for mandatory activities (home/work) across repeated observations (G19) + robust weighted location estimation from G3/G20. | ✔ | ✔✔ | This is how we combine prior (text/POI) with likelihood (GPS evidence). |
| 8 | **Spatial statistics** | Weighted geometric median / Huber M-estimators for biased GPS; Kernel density for visit hotspots; spatial autocorrelation checks. | ✔✔ | ✔✔ | Direct answer to "noise is consistently biased" (G3). |
| 9 | **Graph-based location inference** | GeoIndia-V2's neighbourhood-connectivity Graphormer; landmark co-occurrence graphs; address↔GPS bipartite graphs. | ✘ | ✔✔ | Direction of travel; not a 2-week build. |
| 10 | **Map matching** | HMM (G13) / FMM: snap GPS trails to walkable/road network; distinguish "on the road" from "inside a building"; compute travel paths, dwell, and whether the agent actually reached the address. | ✔ (FMM/Nominatim-routing or OSRM) | ✔✔ | Essential for the "met at the road/shop vs. at home" question. |
| 11 | **Learning from historical visits** | **Learning-to-rank over candidate locations** with information fusion from map layers (G3) — the strongest published formulation. | ✔✔ | ✔✔ | Our core learner. |
| 12 | **Confidence-radius estimation** | GeoConformal (G16) for spatially varying, coverage-guaranteed radii; plus empirical distance quantiles conditioned on evidence class (visit count, cluster tightness, text-match strength). | ✔ | ✔✔ | The honest output. Also the input to the decision engine's visit-vs-call economics. |
| 13 | **Weak supervision** | Triplet/metric learning on GPS proximity (G5) for cold-start; use field visits as labels where integrity is high; perturbed/swapped address pairs as synthetic labels (G22). | ✔ | ✔✔ | Solves "most addresses have zero visits". |
| 14 | **Active learning** | Choose *which address to field-verify next* by maximising information gain × account value; conformal deferral (route uncertain cases to humans). | ✔ (as a selection rule) | ✔✔ | **This is the bridge to PS2.** |
| 15 | **Geospatial foundation/embedding models** | H3-cell embeddings (Esri GDFM, PlaceFM) as *context features*; satellite embeddings (Sentinel-2 location encoder) where imagery exists. | ✘ | △ (nice-to-have) | Gains are real but uneven across space and scale (PDFM benchmark) — do not bet the MVP on it. |

#### Recommended combination (the short answer)

> **Parse (libpostal + deepparse + IndicXlit) → Normalise & alias (learned landmark gazetteer + India-tuned phonetic matching) → Generate candidates (commercial geocoder + OSM POIs + H3 classifier + embedding kNN) → Classify place-purpose (stay-time + POI semantic zones) → Rank with learning-to-rank over text+GPS+map-layer features → Estimate a robust location (weighted M-estimator, not a mean) → Emit a GeoConformal radius + landmark directions → Feed successful visits back as labels (with integrity weighting).**

### 3.6 Important technical insights from the PS3 research

1. **Do not use the mean.** Amazon's finding that GPS noise is *biased* invalidates every centroid/median approach as a primary estimator (G3). Use a **ranking** formulation with features, or a robust M-estimator with asymmetric weights.
2. **Landmarks give neighbourhoods, not doorsteps.** 80% of Indian addresses reference a landmark 50–1500 m away (G1). So the deliverable must be **"point + radius + landmark route"**, exactly as CreditNirvana's problem statement demands. That requirement is a *consequence of physics*, not a design preference.
3. **Explicit spatial hierarchy beats implicit spatial learning.** Multi-head H3-grid classification at multiple resolutions beat triplet-loss metric learning (77.2% vs 56.7% <100 m) (G4). Model space explicitly.
4. **A plain commercial geocoder is a weak baseline on Indian addresses** (23.8% <100 m) (G4) — which is exactly the gap CreditNirvana is asking us to close, and a great slide.
5. **Weak supervision is the cold-start answer** (G5): you don't need labels for new addresses, you need *relative proximity*. Triplets from neighbouring grids.
6. **Normalisation is worth ~50%** (G9). Do it first, do it well, and it pays across everything downstream.
7. **Home detection is the most reliable inference** (99.72% stable under POI loss) because it rests on **spatial recurrence over time**, not on noisy POI context (G19). Work/shop inference is *far* more fragile to missing POIs — so we should be correspondingly more conservative about non-home conclusions and reflect that in the confidence radius.
8. **Stay-time beats visit-count** for home detection (GHOST); grid-based methods incorporating stay-time consistently achieved the lowest errors and most stable performance vs. clustering (G18).
9. **Gaps in GPS trails matter and must be handled** (G21).
10. **"Some GPS points are junk — ignore them"** (G13) is the correct prior for field telemetry; build a junk detector rather than trying to clean everything.
11. **Building-level ambiguity is real**: the nearest building to a staypoint centroid can be the wrong building (G20). Line-intersection counts and POI ranking solve it. This matters enormously for us: visiting the *neighbour's* house to discuss a loan is both useless *and* a DPDP/privacy incident.
12. **Synthetic perturbation is a legitimate training-data strategy** for Indian geo models (G22): Gaussian location perturbation + address-pair swapping gave 84.5% precision at detecting wrong stored coordinates.
13. **Offline is a first-class constraint, not a feature flag.** Nominatim self-hosting (~64 GB RAM, 1 TB SSD), Mappls' NaviMaps, and offline pincode polygons all exist — so plan the field app around a *bundled index* and delta syncs.
14. **Licensing is a real trap.** Bhuvan's terms forbid re-use without written authorisation; Google's ToS restrict caching coordinates. Build on **OSM + government open data (GODL-India) + CN's own data**, and treat commercial geocoders as *runtime* services, not sources of stored training data.

---

## 4. COMPETITOR / EXISTING SOLUTION ANALYSIS

| # | Existing solution | What it does | Technique | Strength | Weakness (for CreditNirvana's problem) | What we learn / take |
|---|---|---|---|---|---|---|
| 1 | **TrueAccord HeartBeat** | Personalises channel, message, timing, plan per consumer, in real time; digital-first | Patented ML decision engine on 24M+ engagement journeys; constant A/B optimisation | Real, measured, at scale: 25–35% better vs traditional agencies; 24% roll-rate / 28–40% gross-flow improvements | Digital-first bias (assumes email/SMS reachability); US regulatory frame (FDCPA/Reg-F), not RBI/DPDP; no address geocoding or field-visit layer; contact *identity* risk not publicly addressed | Timing + channel must be **per-contact-point actions in the same action space** as calls; decision engine ≥ model |
| 2 | **Experian PriorityScore / Collection Triggers** | 60+ recovery scores; re-queues accounts on life events | Propensity + expected-recovery scoring; monitoring triggers | Industry-standard vocabulary ("likelihood to pay *or* expected recovery amount"); trigger-based re-prioritisation | Account-level, bureau-driven, US-centric, closed; no per-number RPC model; no geo; no exploration mechanism | Score on **expected value**, and **re-score on events** rather than on a nightly batch |
| 3 | **Predictive dialers (Revring/Sprinklr/RingCentral/NICE-class)** | Pacing, dial ratios, abandonment control, adaptive pacing, time-zone awareness, local-presence caller ID | Real-time statistical pacing; **RL-based pacing** (Sprinklr) | Excellent at *agent occupancy*; cheap; mature telephony integration | Optimises **agent idle time**, not **recovery per contact**; treats all leads alike; abandon-rate compliance is US-shaped; no contact-identity model | Two published facts we reuse: contact rate decays sharply with data age (25%→11%→7%) and call-window choice alone can move connect rate 30–70% `[vendor claim]` |
| 4 | **Skip-trace platforms (CLEAR, LexisNexis, TLO-class)** | Locate people from fragmented data; enhanced tracing | ML-assisted entity linking across data sources | Can be effective with only an outdated phone number; mature data supply chain | Black-box data vendors; per-lookup cost with no ROI model; no link to *your* recovery economics; third-party-data compliance risk under DPDP | Skip-trace must be a **priced action with an ROI threshold**, benchmarked by **Profit Per Account** |
| 5 | **Phone number intelligence (Telesign, Telnyx/Twilio Lookup, ClearoutPhone, AbstractAPI)** | Carrier, line type, HLR live-reachability, LRN/ported, CNAM, spambot scoring, "recycled number risk" | Carrier/HLR queries + ML anomaly detection on location/SIM/usage patterns | Cheap, fast, API-shaped; explicit recycling-risk signals | Snapshot, not history; no borrower context; India specifics vary (LRN/CNAM are US-centric; India has MNP + DND); accuracy for *recycled* specifically is not published | Buy **line-type + ported-status** as features day 1; build the *behavioural* recycling detector ourselves from our own attempt history — that's the part nobody sells you |
| 6 | **Speech analytics (CallMiner, Sedric, Vasvox, Gnani/Mihup)** | Scores 100% of calls for RPC language, Mini-Miranda, violations, sentiment; real-time agent prompts | ASR + phrase patterns + sentiment | Gives a **supervision signal for right-party status** beyond agent dispositions; directly reduces compliance risk | Costly; per-language quality varies; post-hoc unless real-time; doesn't decide next action | **Use transcripts to label P(right party)** and to detect forbidden disclosure — this is a *model input and a compliance control*, from one asset |
| 7 | **Indian voice-AI collections (Skit.ai, Gnani.ai, Rezo.ai)** | Multilingual voice agents for EMI reminders/KYC; code-mixing; telephony + CRM integration | Indic ASR/TTS + orchestration | Real NBFC deployments; fast go-live (20 days); **10% collection-efficiency uplift** reported `[vendor claim]` | Agent/execution layer, not a contact-health intelligence layer; no geocoding/field layer; no adaptive *policy* (which number, when, or trace?) | Strong candidate as the **execution channel** for our action engine (bot → agent → field), and a partner-shaped product, not a competitor to what we're building |
| 8 | **Collections decisioning suites (Finvi, Sapiens, FICO DM-class, digiqt)** | Score + treatment + channel + timing + compliance guardrails, with explanation codes | Propensity + rules + NBA | Complete operational surface; audit-friendly; "compliance guardrails" as a shipped feature | Account-level; geography absent; strategy logic usually rule-based rather than learned-EV; third-party risk not modelled as a first-class output | Steal the **explanation-code + audit-log** pattern (matches our REVIO experience) |
| 9 | **Google Maps Geocoding + Address Descriptors** | Global geocoding; landmark ranking for Indian addresses | Proprietary; ML on proximity/prominence/visibility | Best-in-class landmark intuition; free with Reverse Geocoding | **23.8% within 100 m on Indian unstructured addresses** (G4); no memory of *our* field visits; ToS restrict caching; no radius/coverage guarantee; no home-vs-shop distinction | Use for **candidate generation + landmark naming**, never as the final answer |
| 10 | **Mappls / MapmyIndia** | India-first maps, geocoding, eLoc, village coverage, offline maps | Proprietary India dataset, ISRO partnership | Deepest Indian coverage; offline navigation exists | Sales-only pricing; attribution mandatory; no field-visit learning; no confidence radius semantics | Best **commercial candidate source** for a serious pilot; check offline SDK for the field app |
| 11 | **Ola Maps** | India-only maps/geocoding built on ride data; 500k free requests/month; Indian data residency | Proprietary | Best free tier for India-only MVPs; SOC2/ISO | Newer ecosystem; vendor-risk (MapMyIndia litigation); no field learning | Default MVP candidate source on cost grounds |
| 12 | **Nominatim / Pelias / Photon (self-hosted)** | OSM geocoding; unlimited requests when self-hosted | OSM + ranking layer | Zero per-request cost; **fully offline-capable**; no lock-in | ~64 GB RAM / 1 TB SSD; import & maintenance burden; weaker Indian POI ranking | The **offline backbone**; we add our learned gazetteer on top |
| 13 | **Delhivery AddFix** | Learns Indian locality hierarchy + spellings from e-commerce addresses + delivery GPS | Unsupervised generative/graphical model over locality names; GPS-derived polygons; India-tuned phonetic fuzzy search | >90% locality accuracy, **200 m** median precision; replaced pincode sorting; improves without extra dev effort | E-commerce delivery context (parcel validates the trip); no home-vs-work distinction; no uncertainty radius; no *contact* objective; proprietary | **Closest analogue to PS3's ambition.** Our differentiation: use *visit outcomes* as validation and emit a radius |
| 14 | **Amazon Last Mile geolocation + hard-to-resolve addresses (IN)** | Candidate ranking over map layers; weak-supervision embeddings for cold-start | **Learning-to-rank**; deep metric learning | Explicitly handles **biased** GPS; 22% fewer defects (IN); millions in annual savings | Delivery-specific (a delivered parcel is ground truth); no borrower-contact objective; no compliance constraint; not offline-first for our use case | **The methodological blueprint for PS3.** Adopt LTR + candidate generation; add integrity weighting and radius calibration |
| 15 | **SAGEL / GeoCloud / GeoIndia-V2 (research)** | Corpus retrieval + graph ranking; address chunks → geo-polygons; Graphormer+LM fusion | Graph ranking; heuristics; multimodal transformer | Pushes the frontier on architecture | SAGEL 17.7% <100 m; GeoCloud's heuristics limit retraining; GeoIndia-V2 needs proprietary corpora | Direction of travel for a **12-month** roadmap, not the MVP |
| 16 | **Collections research systems (P1, P2, P3, P7, P8)** | Contact prediction, MDP call scheduling, MCDA decision support, deep-RL recommendations, agent matching | GBM + MDP/MCDA/RL/ILP | Rigorous, validated (P2 and P7 have real-world field tests) | **Account-level only**; no contact-point identity; no geo; no skip-trace EV; feedback loops mostly unaddressed | Adopt their **architecture patterns** (predict → optimise → constrain → log) and go one level deeper (to the contact point) |
| 17 | **Geospatial platforms (Esri GeoAI, H3, SafeGraph)** | Location embeddings, spatial indexing, POI accuracy | Multi-view autoencoders; H3 hierarchy; ML validation | Enormous leverage for context features and indexing | Not address-resolution engines for India; embeddings gains are uneven across space/scale | Use **H3 as the spatial key** and geodemographic embeddings as **optional context features**, later |

---

## 5. RESEARCH GAP — what existing approaches fail to solve well

**G-1. Everything is account-level; the actual decision is contact-point-level.**
All published collections models (P1–P8) score *accounts*. But CreditNirvana's problem is to score *each phone number and each address* and then pick among them. No published system ranks **contact points within an account** as a slate. Forman's LTR-over-candidates (G3) is the right *shape* but was applied to delivery coordinates, never to contact points.

**G-2. "Avoiding", "invalid", "recycled", "third-party" and "temporarily unreachable" are collapsed into one negative label.**
This is the deepest failure. A model trained on "did the call connect?" produces a *reachability* score, and then the business applies *reachability-level* actions to *identity-level* problems. Calling a recycled number more often is not just wasteful — it is a privacy incident. **No paper in our corpus separates reachability from right-party identity as two modelled heads.** The closest things are: speech analytics vendors detecting "RPC language" post-hoc `[vendor claim]`, and the TSF model detecting number reassignment from behavioural discontinuity (P17) — but not integrated into a contact-scoring system.

**G-3. Skip-trace is triggered by rules, not by value of information.**
Every industry system we found triggers tracing on attempt counts, data staleness buckets, or "high balance + stale data → trace first" heuristics `[vendor claim]`. **None frames tracing as a purchase of information with an expected value.** Decision-analysis has a mature apparatus for exactly this (EVSI/value-of-information), and applying it here is nearly unexplored territory.

**G-4. Feedback loops and selection bias are acknowledged in theory and ignored in practice.**
Only P1 (benchmarking contacted-only training variants) and P2 (a deliberate field experiment) take the problem seriously. Most industry systems retrain on their own policy's output and quietly become self-confirming. Off-policy evaluation (IPS/DR), propensity logging, and randomised audit streams are standard in recommender systems (Open Bandit Pipeline, Uber's bandit work) but essentially absent from published collections practice.

**G-5. Compliance is a guardrail *outside* the model, not a modelled risk *inside* it.**
Vendors advertise "compliance guardrails" as filters `[vendor claim]`. But the highest-frequency compliance failure in third-party collections is **disclosing a debt to the wrong person** — which is a *prediction error*, not a rule violation. If your model cannot estimate P(right party | answered), your guardrail has nothing to guard on. CreditNirvana's own problem statement calls this out ("Third-party debt disclosure must be prevented"); the literature has not answered it.

**G-6. Contact intelligence and location intelligence are two separate industries, and nobody has joined them.**
Collections/telecom vendors own contactability; geocoding vendors and e-commerce players own addresses. There is *no published system* that conditions the decision to call/visit/trace on the **precision of the known location**, and none that conditions **geocoding updates on field-visit outcomes** in a closed loop. This gap is CreditNirvana's structural advantage: **they own both datasets.**

**G-7. Geocoders return points, not calibrated uncertainty.**
Commercial geocoders return a coordinate, a `match_type`, and a 0–1 confidence that is not a coverage guarantee (Stadia/SafeGraph both warn that the `accuracy` field is meaningless for quality). Research models (G4, G5) report aggregate accuracy percentages, not per-address radii. **A field agent needs "90% chance the home is within 240 m of this pin".** GeoConformal (G16) exists and is not applied to address geocoding anywhere in our corpus.

**G-8. "The GPS from a successful visit" is treated as ground truth, and it isn't.**
The e-commerce geocoding literature's label is a *delivered parcel*. CreditNirvana's label is a human meeting — which may occur at a shop, a workplace, the road, a neighbour's gate, or a fake check-in. **No paper in our corpus models check-in integrity or meeting-location purpose** as a label-quality problem. Papers G18–G20 solve *parts* of the purpose question (home detection, trip purpose, POI ranking) but none connect it to label trustworthiness.

**G-9. Offline field operation is an afterthought in research and a licensing trap in industry.**
Research assumes connectivity. Commercial offline options (Mappls NaviMaps) are bundled with closed systems. And the most tempting "India geodata" source (Bhuvan) has terms that forbid industrial re-use without written authorisation. A practical offline architecture — bundled index + delta sync + on-device direction generation — is not documented anywhere we found.

**G-10. Multilingual *address* semantics remain under-served.**
libpostal handles 60+ languages of normalisation; IndicXlit handles transliteration; IndicNER handles entities. But **Indian locality aliasing** ("Gurgaon" / "Gudgaon" / "Gurugram", "2nd cross" vs "2nd cross road" vs "doosri gali") is a *data* problem, solved only by owning the data (AddFix). Open tools give us 60% of the way; CN's field data gets us the rest — provided we build the alias-learning loop.

**G-11. Nobody evaluates contact models on *decision* metrics.**
Published work reports AUC / sensitivity / specificity / concordance. The business cares about **rupees recovered per agent-hour**, **cost per RPC**, **wrong-party contact rate**, and **trace ROI**. Our evaluation section (§12) is designed to close this gap and is itself a differentiator in a hackathon.

**G-12. Exploration is absent from every collections system we found.**
Not one published collections paper we reviewed has an explicit exploration mechanism. Meanwhile Uber's CRM bandit work (P18) and Optimizely's docs (P19) treat exploration floors as basic hygiene. Low-scored contact points are permanently starved, and their "score" is therefore never corrected.

---

## 6. OUR PROPOSED SOLUTION

### 6.1 Name and one-line thesis

**SANKET + SUTRA** *(working names — SANKET = "signal", for the contact-health & decision engine; SUTRA = "thread", for the address-to-place resolver)*

> **Thesis:** CreditNirvana's unifying asset is not phone numbers and not addresses — it is the **field-visit event**, which is simultaneously *a recovery action, a ground-truth location label, and a contact-health probe*. We build the first system that treats it as all three at once, closing a loop nobody closes: **better geocoding → higher visit success → more trusted labels → better geocoding**, while the same loop **feeds contact health back into the call/trace decision**.

### 6.2 The three-layer conceptual model

#### Layer A — Contact-Point Health as a three-factor decomposition (our core idea)

For contact point *j* (a phone number, an address, an email, a WhatsApp handle) on account *i* at time *t*, decompose:

```
P(RPC | j, i, t) = P(Answer | j, t, channel, caller_id, context)
                 × P(RightParty | Answer, j, i)
                 × P(Productive | RightParty, i, agent, offer)
```

Three heads, three failure modes, three different actions:

| Factor | Low value means | Correct action | Never do |
|---|---|---|---|
| **A = P(Answer)** low | Dead / switched-off / invalid / temporarily unreachable | Retest at a different window; test an alternate contact point; consider trace | Keep dialing on the same schedule |
| **R = P(RightParty \| Answer)** low | **Recycled** (new owner) or **third-party** (family/neighbour/shopkeeper) | Identity-challenge only (no debt disclosure); invalidate & trace if recycled | Disclose debt, negotiate, offer settlement |
| **P = P(Productive)** low | Avoiding-but-reachable; wrong offer; wrong agent; wrong channel | Switch channel (SMS/voice-bot), change offer, change agent, change script | Escalate to field visit on a low-value account |

**Why this decomposition is the single most important design decision:** it is the only formulation in which "borrower avoiding" and "invalid contact" *cannot* be confused, because they live in different heads (A is high/low respectively), and it makes the compliance requirement **structurally enforced**: the decision engine literally cannot route a contact point to a disclosure-enabled action unless R exceeds a threshold.

#### Layer B — Location truth as calibrated evidence, not a coordinate (SUTRA)

For each address *a*, produce a **location belief**, not a point:

```
Belief(a) = ( centroid_μ(a), radius_r(a) at coverage 1−α, purpose_distribution, evidence_ledger )
```

where the evidence ledger records, per observation, *who* observed it, *how* (attested GPS / agent-entered / geocoder), *what kind of place* it was (home / work / shop / road / gate / other), *what happened* (met borrower / met family / no one / refused), and a **credibility weight**. The centroid is a **credibility-weighted robust estimator**, and the radius is a **geographically-weighted conformal quantile** (GeoConformal, G16) so that it carries an actual coverage guarantee.

#### Layer C — The decision engine: constrained expected value over an action lattice

Actions are not "call / don't call". They are a structured lattice:

```
A = { call(channel=c, contact=j, window=w, agent_type=g, script=s)
    , message(channel=c, content=k, contact=j)
    , switch_contact_point(from=j, to=j')
    , field_visit(address=a, route=R, script=s)
    , skip_trace(tier=τ)
    , escalate(legal / agency / restructuring)
    , wait(Δ)                              ← the null action, with option value
    , suppress(reason) }
```

Each candidate is scored by **expected net recovery contribution (ENRC)**, filtered by hard constraints, and the argmax is executed and logged. Details and formulas in §10.

### 6.3 End-to-end architecture (the pipeline, sharpened)

```
                    ┌──────────────────────────────────────────────────────────┐
                    │  LAYER 0 · DATA & FEATURE STORE (point-in-time correct)   │
                    │  Postgres+PostGIS · Parquet/S3 · MLflow · dbt/GE tests   │
                    └──────────────────────────────────────────────────────────┘
   CDR/call telemetry │ agent dispositions & remarks │ voice-bot transcripts │
   field-visit GPS + dwell + outcome + attestation │ address records + source + age │
   payment / PTP / settlement events │ shared-contact graph │ OSM/POI + pincode + boundaries
                    ┌──────────────────────────────────────────────────────────┐
                    │  LAYER 1 · IDENTITY & CONTACT-POINT GRAPH                 │
                    │  E.164 normalise → Splink blocking → contact-point nodes   │
                    │  + address nodes + agent nodes + associate edges          │
                    │  Graph features: degree, shared accounts, neighbour RPC   │
                    └──────────────────────────────────────────────────────────┘
        ┌──────────────────────────────────┬───────────────────────────────────┐
        │  LAYER 2 · PS2 — SANKET           │  LAYER 3 · PS3 — SUTRA            │
        │  H1 P(Answer)                     │  N1 libpostal+deepparse+IndicXlit │
        │  H2 P(RightParty|Answer)          │  N2 learnt landmark gazetteer +   │
        │     ↳ recycled-risk sub-head      │     India phonetic alias keys     │
        │  H3 P(Productive|RightParty)      │  N3 candidate generation          │
        │  H4 hazard/decay (survival,       │  N4 purpose classifier (home/work │
        │     competing risks, censoring)   │     /shop/road) from dwell+POI+   │
        │  H5 uplift CATE per action        │     outcome+remark                │
        │  CAL calibration (isotonic/Platt, │  N5 integrity model (check-in     │
        │     segmented by channel × TOD)   │     credibility, agent reliability│
        │  XAI SHAP + reason codes          │  N6 LTR over candidates           │
        │                                   │  N7 robust location estimator     │
        │                                   │  N8 GeoConformal radius           │
        │                                   │  N9 landmark direction generator  │
        └──────────────────────────────────┴───────────────────────────────────┘
                                  │                        │
                                  ▼                        ▼
                    ┌──────────────────────────────────────────────────────────┐
                    │  LAYER 4 · DECISION ENGINE (REVIO pattern, extended)      │
                    │  1. candidate enumeration                                 │
                    │  2. HARD filters: RBI 8am–7pm · DND · freq caps · DPDP    │
                    │     purpose · identity gate · do-not-disclose flags       │
                    │  3. ENRC scoring per candidate (incl. WAIT)               │
                    │  4. soft constraints: budget, agent capacity, route VRP    │
                    │  5. exploration layer: VoI-directed ε-floor + Thompson    │
                    │  6. argmax → execute → SIGNED AUDIT RECORD (reason codes) │
                    └──────────────────────────────────────────────────────────┘
                                  │
              ┌───────────────────┼────────────────────┐
              ▼                   ▼                    ▼
   ┌────────────────┐  ┌──────────────────┐  ┌──────────────────────┐
   │ AGENT CONSOLE  │  │ FIELD APP (PWA,  │  │ MANAGER DASHBOARD    │
   │ React/TS       │  │ OFFLINE-FIRST)   │  │ H3 heatmaps · ROI of │
   │ health heatmap │  │ lat/lon + radius │  │ trace · compliance   │
   │ NBA card + why │  │ + landmark route │  │ panel · model health │
   │ identity gate  │  │ + no-disclosure  │  │ (ECE, drift, coverage│
   │ (no-debt mode) │  │   script, local  │  │  of radii)           │
   └────────────────┘  │   language, sync │  └──────────────────────┘
                       └──────────────────┘
                                  │
                    ┌──────────────────────────────────────────────────────────┐
                    │  LAYER 5 · CONTACT-TRUTH LOOP (the differentiator)        │
                    │  every outcome logged WITH PROPENSITY and with GPS/       │
                    │  integrity → nightly: retrain · recalibrate · update      │
                    │  gazetteer · update radii · off-policy eval before promote│
                    └──────────────────────────────────────────────────────────┘
```

### 6.4 The Contact-Truth Loop (the part that makes this ours)

```
        ┌────────────────────────────────────────────────────────────┐
        │                                                            │
        ▼                                                            │
  SUTRA: address a has radius r(a) = 1,400 m  ──►  PS2 decision:     │
  P(visit success) = 0.11, ENRC(visit) = −₹40  ──►  action = "call"  │
        │                                                            │
        │  (uncertainty is HIGH ⇒ information value is HIGH,        │
        │   but the account is LOW value ⇒ not worth a visit)       │
        │                                                            │
        ▼                                                            │
  For HIGH-VALUE accounts with HIGH geo-uncertainty:                 │
  the visit is chosen partly BECAUSE it is a label purchase.         │
        │                                                            │
        ▼                                                            │
  FIELD VISIT happens ──► GPS trail + dwell + outcome + remark       │
        │                                                            │
        ├─► SUTRA: integrity check → purpose classify → new evidence │
        │          → radius r(a) drops to 90 m at 90% coverage       │
        │                                                            │
        └─► PS2: visit outcome is ALSO a policy-independent label:  │
                   • met borrower at home   → P(Answer) prior up     │
                   • nobody home 3× night   → address-poor signal    │
                   • met at shop, lives 4km away → NEW address node  │
                                                     + recycled-phone │
                                                     suspicion up     │
```

**Three properties of this loop that no existing system has:**

1. **The visit is a "policy-independent" measurement.** Unlike dials (whose occurrence is caused by our own score), visits on high-uncertainty accounts are partly information-motivated — giving us a *quasi-random* label stream that counteracts the feedback loop in PS2. (We formalise this in §10.5 with an explicit VoI term, and we supplement it with a tiny randomised audit stream.)
2. **The ladder is monotone: geo-uncertainty is a lagging indicator of wasted effort.** Every rupee of field budget currently spent on a 1,400 m radius pin is partly wasted. Quantifying that waste is the business case for PS3 funding.
3. **Compliance improves as a side effect.** A tighter radius means fewer visits to the *wrong door* — which under RBI/DPDP is not merely inefficiency, it is unauthorised third-party exposure.

### 6.5 A detail that turns out to matter enormously: the "mover" latent factor

The same underlying event — *the borrower moved* — produces **both** PS2 symptoms and PS3 symptoms:

| Observable | PS2 reading | PS3 reading |
|---|---|---|
| Phone answers a stranger | recycled / wrong party | address likely stale |
| Address never has anyone home | contact strategy failing | geocode may be *correct* but the resident is wrong |
| Long silence on all contact points, then activity in a new locality | "recoverable with new contact points" | "address has changed" |
| Field visit: "person shifted 2 years ago" | disposition | **hard negative** for that address |

**Design consequence:** we learn a **shared latent "record staleness / mobility" factor** for account *i*, estimated jointly from contact-point behaviour **and** location evidence, and we expose it as a feature to *both* heads. Concretely: a joint embedding table keyed by account, trained with a small multi-task encoder whose tasks are (a) predict next-attempt answer, (b) predict visit outcome, (c) predict "address changed" from remark text. In the MVP this is approximated with **3 engineered features** (contact-point failure breadth, geo-residual, remark-NLP staleness score) — cheap, explainable, and it captures most of the value. In production it becomes a learned multi-task embedding.

This is genuinely novel framing and it directly answers the problem statement line *"Borrower avoiding and invalid contact can look similar but require different actions"* — extended to *"stale contact and stale address are two faces of one variable."*

---

## 7. WHY OUR SOLUTION IS DIFFERENT

| # | Our differentiation | What exists today | Why ours is better | How a judge/grader can verify it |
|---|---|---|---|---|
| **D1** | **Three-factor RPC decomposition with a dedicated right-party-identity head** | Published collections work predicts "contact" (P1) or "payment" (P2,P3); speech analytics detects RPC *after* the call `[vendor claim]` | Separates *avoiding* from *invalid* (different heads) and *recycled* from *third-party* (identity head + temporal-discontinuity features per P17) → yields **different, safer actions per failure mode** | Show two accounts with identical P(connect)=0.05; our system says "retest at 7 pm" for one and "identity-challenge only + trace" for the other, and shows the *feature evidence* for each |
| **D2** | **Skip-trace as a value-of-information purchase (EVSI)** | Industry triggers trace on attempt counts / stale-data buckets `[vendor claim]` | Trace is priced: we compute the *expected improvement in recovery* from the new contact points a trace is expected to yield, against its cost. If the uplift doesn't beat the fee, we don't trace | Demo a slider: change trace price → see which accounts cross the threshold, live |
| **D3** | **Contact decay as a censored survival process, not a label** | Collections models treat "no answer" as a negative label; [P4] uses survival but for repayment, not contactability | Never-tested contact points are **censored**, not negative — so we can score the part of the portfolio that has never been dialled without pretending it failed | Show the survival curve for a cohort and the calibration of "P(contact within 5 attempts)" |
| **D4** | **Joint staleness factor across contact and location** | Nobody couples them (§5, G-6) | One latent variable explains both symptom families; gives the decision engine a single "this record is stale — go find them" trigger that is *evidence-weighted* rather than rule-based | Show an account where phone and address symptoms agree, and one where they disagree, with the differing recommendation |
| **D5** | **Closed-loop active learning driven by the decision engine** | Geocoding systems learn from deliveries (G3,G5); collection systems run visits operationally but not as label acquisition | We *choose which visits to make partly for their information value*, and we propagate the resulting label into a calibrated radius within 24 h | The 60-second demo act: visit → radius shrinks → tomorrow's action changes |
| **D6** | **Field check-in integrity model (anti-label-poisoning)** | No published system models fake check-ins; HMM literature only says "some points are junk" (G13) | Agent-credibility + spatial-plausibility + attestation + cross-account duplicate detectors weight every observation, so fraud *degrades gracefully* instead of corrupting the geocoder | Deliberately inject a faked check-in in the demo and show the estimate not moving |
| **D7** | **Calibrated radius with coverage guarantee, surfaced to humans** | Geocoders return a point + non-guaranteed confidence; research reports aggregate drift accuracy (G4) | GeoConformal (G16) gives "90% of the time the true home is within X m of this pin" per address; the field agent sees the circle, and the decision engine uses the radius in the visit economics | Show a coverage test: across N held-out visits, empirical coverage ≈ nominal |
| **D8** | **Compliance as structural impossibility, not a filter** | "Guardrails" are post-hoc filters `[vendor claim]` | An action that would disclose a debt requires R > τ; if R is unknown the action is not in the candidate set. Plus the 8 AM–7 PM window and DND are applied as *candidate-set construction*, so illegal actions have no score to be chosen by | Show the audit record: every decision lists the constraints evaluated and the reason the chosen action was legal |
| **D9** | **Exploration that is directed, budgeted and audited** | No exploration in any collections paper we found (§5, G-12) | VoI-directed exploration with a hard budget, propensity logging, Thompson sampling over actions, and off-policy evaluation before any policy promotion — engineering practice imported from Uber's bandit stack (P18) and Optimizely's floor (P19) | Show the "starvation report": count of contact points with 0 attempts; show it decreasing while cost/contact falls |
| **D10** | **Offline-first field application with local-language landmark directions** | Research ignores offline; commercial offline is closed | Bundled H3 index + pincode polygons + template-based direction generator (EN/HI/BN/TA/…) with no network requirement; delta sync on reconnect | Turn off wifi in the demo and the field app still routes to the borrower |
| **D11** | **Decision metrics as first-class evaluation** | Literature reports AUC/concordance | We report **₹ recovered per agent-hour, cost per RPC, wrong-party contact rate, trace ROI, visit-success lift** alongside Brier/ECE/NDCG | The dashboard's default view is money, not ROC |

---

## 8. DATA STRATEGY

### 8.1 CN data we need — the minimum viable schema

**Tier 1 — absolutely required for PS2 (derivable from existing CN systems)**

| Entity | Fields | Why |
|---|---|---|
| `contact_point` | point_id, account_id, type {mobile, landline, alt_mobile, whatsapp, email, address_id}, value_e164 / normalised address, source {application, KYC, bureau, trace, self-update, referral}, first_seen_ts, last_verified_ts, verified_by {agent, field, bot, none}, status | The unit of prediction. **Source and age are core features** (problem statement explicitly lists them). |
| `call_attempt` | attempt_id, point_id, agent_id, campaign_id, ts_start, channel, caller_id_used, ring_duration_s, talk_duration_s, network_cause_code, amd_result {human, machine, unknown}, disposition_code, disposition_text, transcript_id | The observation. Ring duration + cause code + timestamp is where the reachability signal lives. |
| `rpc_event` | account_id, point_id, ts, verified_how {agent_confirmed_identity, bot_challenge_passed, doc_seen, payment_made}, confidence | The label. Multiple confidence tiers matter — a payment is stronger evidence of right-party than an agent's word. |
| `payment_event` | account_id, ts, amount, mode, point_of_contact, promise_to_pay_flag, ptp_date, ptp_kept | The money. Needed for EV and the productivity head. |
| `account_static` | balance, DPD bucket, product, segment, state, pincode, language_pref, original_address_id, bureau_score_band | The value side of EV. |
| `agent` | agent_id, type {inhouse, agency, bot}, language_skills, tenure, historical RPC rate, complaint flags | Agent is a feature, not a constant ([P8]). |

**Tier 2 — required for PS3**

| Entity | Fields | Why |
|---|---|---|
| `address_record` | address_id, account_id, raw_text, language_mix, source, geo_from_source_lat/lon, pincode_stated, city_stated, landmark_tokens, created_ts, superseded_by | The input. |
| `field_visit` | visit_id, account_id, address_id, agent_id, ts_start/end, **gps_trail** (ts, lat, lon, accuracy, provider, mock_flag), max_dwell_s, dwell_geohash, outcome_code, outcome_text (multilingual), met_person {borrower, family, neighbour, shopkeeper, guard, none}, place_type {home, work, shop, road, gate, other}, payment_collected, photo_attested, device_id, app_version | **The crown jewel.** This single table powers PS3's learning *and* PS2's policy-independent labels. |
| `visit_remark` | visit_id, raw_remark_any_language, translated_en (Bhashini/IndicTrans), extracted_entities {landmark, relation_to_borrower, moved_flag, new_address_hint} | Where "person shifted", "met at shop", "house locked, neighbour says…" live. TubeSignal's NLP stack maps directly here. |

**Tier 3 — required for the decision engine**

| Entity | Fields | Why |
|---|---|---|
| `cost_table` | action_type, unit_cost, currency, effective_from | Without costs there is no EV. **Include: cost per dial, per SMS, per bot-minute, per agent-minute, per field visit (by locality), per trace tier, per legal step.** |
| `constraint_config` | contact_window (08:00–19:00), max_attempts_per_week_per_debt, dnd_flag_source, cooling_off_after_conversation_days, identity_gate_threshold τ | Hard filters. Must be **versioned**, because the audit record must show which config version applied. |
| `outcome_ledger` | decision_id, ts, account, candidate set, features hash, chosen action, propensity, ENRC decomposition, constraint evaluations, reason codes, model versions | The audit trail. REVIO lineage. |

**Tier 4 — nice to have:** device fingerprint / app signals, WhatsApp delivery status, **inbound-call events** (an inbound call proves the number is live *and* owned by the borrower — the highest-quality contact signal in the entire system; hunt for it in the data), IVR/bot session logs, SMS delivery DLRs.

### 8.2 Public datasets — the concrete prototype stack

**Recommended hackathon stack (all obtainable in hours):**

```
PS2 prototype:   UCI Bank Marketing (attempt/recency/channel/duration proxy)
                 + KDD Cup 2009 (missing-not-at-random customer features)
                 + Lending Club (recoveries → EV & survival targets)
                 + Hillstrom (multi-treatment uplift & Qini)
                 + Synthetic CN-like attempt log (see §8.4)

PS3 prototype:   OSM India via Overpass      (POI/landmark + roads)
                 + pincode polygons (data.gov.in / DataMeet / bharatlas)
                 + OSM / Microsoft building footprints
                 + Geolife (field-trail pipeline: staypoints, cleaning, home detection)
                 + MIT BostonWalks / GeoTracker (home-detection ground truth)
                 + Aksharantar / Dakshina (transliteration & phonetic normalisation)
                 + SHRUG village/town polygons (rural addressing prior)
                 + Nominatim or Ola Maps free tier (candidate generation)

Combined:        H3 everywhere as the spatial key
```

**Licensing summary (this is a real risk — read it):**

| Source | Licence | Constraint we must respect |
|---|---|---|
| OpenStreetMap | ODbL 1.0 | Attribution + share-alike on derived *databases*. |
| data.gov.in pincode layer | GODL-India | Free with attribution. |
| DataMeet maps | CC BY 4.0 / CC0 | Attribution for CC-BY layers. |
| india-geodata / bharatlas | CC BY 4.0 / mixed CC0-CC-BY-GODL | Check per layer; code MIT. |
| SHRUG | Open access, published DOI | Citation required. |
| Aksharantar / Dakshina | Open (AI4Bharat / Google Research) | Citation. |
| Geolife / T-Drive | Research use | Fine for a hackathon; re-check for production. |
| Hillstrom | Public dataset | Fine. |
| Home Credit / Lending Club | Competition terms | Do **not** ship production decisions on weights trained purely on these. |
| Google Maps / Mappls / Ola Maps | Commercial ToS | **Do not store/cache coordinates** beyond ToS; treat as runtime candidate suppliers. |
| **Bhuvan (ISRO)** | ⚠ Restrictive | **Avoid.** ToS forbid re-use without written authorisation. |

### 8.3 Labels — and how to get them honestly

| Label | Source | Quality | Notes |
|---|---|---|---|
| **Answered** | telephony (ring/talk duration + cause code) | ★★★★ | Objective, machine-generated. Our best label. |
| **Right party** | (a) agent disposition + identity-confirmation step, (b) speech-analytics RPC language detection, (c) payment made during/after the call, (d) inbound call from that number | ★★★★ for (c)/(d), ★★★ for (a)/(b) | **Build a label-confidence hierarchy; train on the high-confidence subset, then distil to the rest.** Payments and inbound calls are the gold standard. |
| **Productive (PTP / settlement)** | payment/PTP ledger | ★★★★★ | Direct business label. |
| **Third party answered** | disposition + transcript phrases ("he's not here", "{relationship}") | ★★★ | Needed to train the identity head. |
| **Recycled** | (i) agent marking "number belongs to someone else", (ii) payment/credit from a *different* identity, (iii) behaviour discontinuity ([P17]), (iv) hard rule: silence ≥ 90 days then answering with a stranger | ★★ → ★★★★ | Rule-based pseudo-labels from (iv) are defensible and auditable, because the 90-day gap is a regulatory construct. |
| **Address visit outcome** | field app | ★★★★ if attested, ★ if not | Must be integrity-weighted (§9.4). |
| **Location truth** | successful visit GPS **with**: met borrower ∧ place_type=home ∧ attested ∧ agent credible | ★★★★ | Our geocoding label. Everything else is weaker evidence. |
| **"Address moved/changed"** | remark NLP ("shifted", "वहाँ नहीं रहता") + repeated no-contact at that address | ★★★ | Feeds the staleness factor. |

> **A rule we will state explicitly in the pitch:** *we never train the RPC model on "which contact points got dialled". We train on "what happened when this contact point was dialled", weighted by the propensity with which the policy chose it.* This one sentence is the difference between a demo and a system.

### 8.4 Synthetic fallback — because CN sandbox data may not arrive in time

**Generate a CN-shaped simulator.** This is not a throwaway: it doubles as the *rehearsal environment* for the decision engine and as the only way to demonstrate off-policy evaluation with a known ground-truth policy.

**Simulation design (latent types + explicit ground truth):**

1. **Borrower-type generator** per account: `{willing-capable, willing-cash-constrained, avoider, genuine-hardship, moved-away, fraud-declared}`, each with a behaviour model:
   - `avoider`: real device, declines/rejects calls, answers only in one narrow window, short talk time when caught.
   - `temporarily_unreachable`: answer probability varies by hour/week with device/travel events.
   - `invalid`: network cause codes only, never a ring to a human.
   - `recycled`: silent for **≥ 90 days** after `t_last_good`, then answers with a **stranger signature** — mirroring the TRAI/DoT 90-day reallocation shape.
2. **Contact-point generator**: N points per account (mobile 1–3, landline, alt contact, address, WhatsApp) with source + age metadata; recycling rate parameterised by source and age.
3. **Action-conditional observation model** with realistic noise:
   - Answer probability = f(window, channel, caller_id, number health, attempt fatigue)
   - Ring-duration distribution (short ring = network rejection; long ring then no answer = avoidance; answer after 2 rings = engaged)
   - Cause codes sampled from an Indian-style taxonomy.
4. **Field-visit model**: success probability = f(geo_radius, time-of-day, visit history, locality type); GPS generated as `true_location + biased_offset(locality) + gaussian_noise + occasional junk`; **5% of check-ins generated fraudulently** (wrong place / spoofed) to exercise the integrity model; remarks generated from multilingual templates.
5. **A legacy policy** (fixed 3 attempts → visit → trace) so we can show **off-policy improvement**, mirroring the [P2] field-experiment structure.

Deliverable: `synthetic_cn_generator.py` producing `contact_points.parquet`, `call_attempts.parquet`, `field_visits.parquet`, `accounts.parquet`, `ground_truth_latent.parquet` (hidden from the model), plus a **data dictionary matching the CN schema exactly**, so swapping in real data is a config change. *This is the highest-leverage engineering artifact of the whole hackathon: it de-risks both problems and makes the demo reproducible.*

**Also generate synthetic addresses:** take ~5,000 real OSM POI + locality names per city, apply realistic corruption (`Gurgaon→Gudgaon`, dropped tokens, Hindi-transliteration variance, landmark-relative phrasing templates: "behind X", "near Y", "opposite Z", "2nd cross", "X ke peeche"), and retain ground-truth coordinates. This becomes an **address-corruption benchmark** with known ground truth and Indian-specific corruption — more useful than any public dataset for our purposes.

### 8.5 Feature engineering — the concrete lists

#### PS2 features (per candidate contact point, as-of decision time)

**A · Reachability**
- Attempts: total; last 7/30/90 d; since last answer; since last RPC; distinct days attempted; distinct windows attempted.
- Timing: hour-of-day histogram, day-of-week, days since first attempt; **answer rate by (weekday × window)** for this point and for its locality/cohort.
- Telephony response: ring-duration mean/median/max/trend; share of attempts with zero ring; share busy; share switched-off cause; share out-of-service cause; AMD human/machine rate; **call-rejected rate (a strong avoidance signal)**; voicemail share.
- Recency/decay: days since last successful answer; days since last RPC; slope of rolling RPC rate.
- Number intelligence: line type, carrier, ported flag, MCC/MNC change, number-age proxy (first-seen), source and age of the record, DND status.
- Cohorts: same-locality RPC rate, same-carrier answer rate, same-source answer rate, numeral-prefix answer rate.
- Graph: shared with k other accounts; those accounts' RPC rates; whether any linked account had recent RPC.
- Survival: `P(answer by attempt k)`, median attempts-to-answer, censoring indicator.

**R · Right-party identity**
- Number-level: ever previously confirmed as right party (and when); share of answers that were third-party; count of distinct *claimed identities* in transcripts at this number.
- Temporal-discontinuity features ([P17]-flavoured): **silence gap before last answer**; divergence in answer-hour profile (KS / Jensen–Shannon between pre-gap and post-gap); divergence in average talk duration; sudden change in AMD behaviour; **≥ 90-day gap flag**.
- Content: transcript features (name-confirmation attempts, "who is this", refusal-to-identify rate, language-switch rate, third-party mention patterns); dispositions like wrong-number / belongs-to-someone-else.
- Cross-account: this number on accounts with **different** borrower names / DOBs / localities (a strong recycling indicator); number↔address geo-consistency (does the number's circle match the loan's address locality?).
- Associate structure: is this number in the graph as relative / employer / reference?

**P · Productivity (given right party)**
- Payment history at this point; PTP kept/broken ratio; average paid amount; days-to-pay after contact; settlement behaviour; dispute/refusal flags.
- Agent/offer: agent's PTP rate in this segment; language match; last offer type; the account's best-performing channel.
- Timing: payday proximity, month-end, salary-cycle inference from past payments.

**Account/value features** (for EV): balance, DPD, product, interest/fees at stake, legal recoverability, settlement propensity, cost-to-collect, and an **expected recovery distribution** (quantiles, not a mean — [P9] shows recovery is multimodal).

#### PS3 features

**Text side**
- Parsed components (house number, building, road, sub-locality, locality, city, district, state, pincode) from libpostal **and** deepparse, plus their agreement.
- Language mix (IndicLID), script mix, transliteration-normalised form, romanisation variants expanded via IndicXlit/Aksharantar.
- Landmark tokens with relation word (`behind`, `near`, `opposite`, `next to`, `ke peeche`, `saamne`) and ordinal/direction tokens (`2nd cross`, `gali no. 5`).
- Gazetteer match: exact score, India-tuned phonetic key match, alias-graph distance, token Jaccard/Levenshtein/Jaro-Winkler combined through a learned matcher ([G10]), embedding cosine to candidate localities, **candidate-set size (an ambiguity indicator)**.
- Boundary consistency: is the candidate inside the stated pincode polygon? Distance to the polygon boundary.
- Building/campus/colony match; apartment-complex alias handling ("Raheja Atlantis" ↔ "rahja etlantice").

**GPS / visit side (aggregated per candidate location)**
- Visit count at this cluster; distinct agents; distinct days; time span; recency of the last successful visit.
- **Dwell statistics** (median, max, share of visits with dwell > 20 min) — the home signature ([G18]).
- **Night-share and weekend-share** of visits ([G18]'s nighttime filter).
- Outcome-conditioned counts: met-borrower-here, met-family, nobody-home, payment-collected-here.
- Travel context: arrival by vehicle vs walk; presence of a preceding stop (shop visit); GPS line-intersection counts ([G20]).
- POI context: count and category mix within 50/150/300 m; residential vs commercial share; **is the landmark named in the address text within X m of this candidate?** — one of the strongest single features available.
- Building footprint: does the candidate snap to a building polygon? Its area/shape (dwelling vs shop)?
- Cross-visit geometry: spread of visit points; distance from the median of all visits for this address; whether this candidate is the trip's final stop.
- Integrity-adjusted evidence weight (§9.4).
- Uncertainty: GeoConformal radius at 90% for this candidate; stability of the radius across the last 3 updates.

**Cohort / global**
- **Learned locality-level geocoder bias offset** (error is spatially structured, [G15]).
- **H3-cell historical geocode error surface** built from past visits — a cheap, powerful bias-correction layer almost nobody builds. (UrbanFlow's home turf for our team.)
- Locality urbanity/deprivation embedding from an H3-cell encoder (optional, later).

---

## 9. MODEL STRATEGY

### 9.1 Baseline → Strong MVP → Advanced

**Baseline (Day 1–2) — "prove the plumbing"**
- Models: logistic regression (interpretable) + LightGBM (performance); one classifier for `P(answered)`, one for `P(RPC | attempt)`.
- Calibration: `CalibratedClassifierCV(method='isotonic')` on a held-out fold.
- Decision: fixed thresholds + a spreadsheet EV with hard-coded costs.
- Metrics: PR-AUC, Brier, ECE, lift@decile.
- Purpose: baseline numbers for the before/after story, plus an audit-friendly linear challenger.

**Strong MVP (Day 3–7) — "the system"**
- **H1** `LightGBM → P(Answer | point, window, channel, history)`, monotone constraints where sensible.
- **H2** `LightGBM → P(RightParty | Answer)` + a small **recycled-risk head** on the ≥90-day-gap subpopulation.
- **H3** `LightGBM → P(PTP | RPC)`.
- **H4** **Survival model** (`sksurv.GradientBoostingSurvivalAnalysis`, or CoxPH via lifelines for interpretability) for attempts-to-contact with right-censoring; emits `P(contact within k)`.
- **H5** **Prototype uplift** via a T-learner on simulated data (and on Hillstrom to validate the methodology).
- Calibration: segmented isotonic by `channel × time-window × source-age`; per-segment reliability curves in the dashboard.
- Decision engine: full ENRC with hard constraints, WAIT as a candidate, VoI-directed exploration (ε ≈ 3–5%), propensity logging, audit records.
- Geo layer: libpostal + pincode constraints + learned gazetteer + OSM POI landmark scoring + staypoint/dwell home-signature + weighted robust estimator + **empirical/GeoConformal radii** + landmark direction templates.
- Graph features: degree, shared-account count, neighbour RPC rate (no GNN yet).

**Advanced / production (4–12 weeks)**
- **Graph:** GNN (GraphSAGE/GAT) or node2vec over the contact-point graph; weekly retrain. (Precedent: GraphER, AAAI-20; xEM, 2025.)
- **Sequence:** a small GRU/transformer encoder over attempt sequences → 8–16 embedding features. Gated on ≥6 months of dense history and a measurable PR-AUC gain.
- **Causal:** X-learner / causal forest per action with a **permanent 2–5% randomised holdout**; doubly-robust off-policy evaluation before any policy promotion (Open Bandit Pipeline).
- **Bandits:** Thompson sampling / LinUCB over actions with cost-aware regret; SquareCB-style exploration on top of GBM scores (Uber's pattern, [P18]).
- **PS3 advanced:** address RoBERTa pre-trained on CN's own address corpus + **multi-head H3 classification** ([G4]'s winning architecture); neighbourhood-connectivity graph with cross-attention towards [G6]'s shape; automated landmark-alias discovery from successful visits; satellite/geodemographic H3 embeddings as context.
- **Multi-task staleness encoder** for the D4 joint factor.
- **Serving:** point-in-time feature store; model registry + shadow deployment; drift monitors (PSI/KS per feature, ECE, conformal coverage); automatic rollback.
- **Human-in-the-loop:** **conformal deferral** — decisions with wide prediction sets go to a supervisor queue.

### 9.2 How to handle missing / unobserved contact outcomes

This is the most under-discussed problem in the field, and the one most likely to be probed in Q&A. Five parts:

1. **Never treat "untested" as "failed".** Encode it as **censoring**. A survival model trained with `(T = time since last activity or ∞, E = 1 if answered else 0)` handles "we never tried" correctly — letting us score the never-dialled tail of the portfolio.
2. **Train on attempt-level, not account-level, rows.** Each dial is a row; the label is what that dial produced. A "failed" contact point becomes a *sequence of censored observations*, not a permanent negative.
3. **Correct policy-induced selection with propensity weighting.** Log `p(action chosen | context)` at decision time and weight training rows by `1/p` (or use doubly-robust estimation) so under-sampled regions of the action space are not invisible. This is standard off-policy machinery from the bandit literature (Open Bandit Pipeline, Vowpal Wabbit) that collections practice ignores.
4. **Keep a small randomised audit stream.** 1–3% of decisions are replaced with a uniformly random **permissible** action for measurement only — never legal escalation, never a disclosure-capable action on an unverified number. This is the only way to obtain unbiased Qini/uplift estimates and unbiased calibration in the low-score region.
5. **Exploit structurally policy-independent labels.** Field-visit outcomes, **inbound calls**, self-cures (payment with no contact), and voluntary callbacks are *not caused by our dialing policy*. They are gold for evaluating and correcting the model. Hunting for inbound-call events is a day-1 task with very high payoff.

### 9.3 How to distinguish avoiding vs invalid vs recycled vs temporarily unreachable

**The mechanism: model the *response function*, not the last outcome.** Each state has a distinct signature across four layers: network, temporal, identity, continuity.

| Evidence | **Reachable & willing** | **Avoiding** | **Temporarily unreachable** | **Switched off / long-dead** | **Invalid from start** | **Recycled** | **Third party** |
|---|---|---|---|---|---|---|---|
| Rings, no answer | rare | **frequent** | occasional | no / immediate "switched off" | **never rings** ("does not exist" / "out of service") | rings, answers | rings, answers |
| Explicit call-reject | rare | **diagnostic** | rare | n/a | n/a | n/a | n/a |
| Answer behaviour | steady across windows | **window-selective** (only 7–9 pm), short talk, early hang-up | erratic, event-driven (travel/theft) | none | none | answers quickly, unusual hours | answers, then hands over |
| Temporal continuity | stable answer-hour profile | stable | bursty | **long plateau (≥90 d silent)** | never any activity | **discontinuity after a long gap** ([P17] signature; TRAI 90-day shape) | continuity with a *different person* |
| Transcript identity signals | confirms name/details | refuses confirmation but no stranger markers | follows pattern when reached | n/a | n/a | "who are you?", wrong name, wrong language, denies knowing borrower | states relationship ("his brother"), no debt acknowledgement |
| Cross-account evidence | consistent | consistent | consistent | consistent | number on multiple unrelated accounts | **number with conflicting identities/DOBs** | number flagged as reference/associate in the original file |
| Payment behaviour | pays | refuses / token payments | pays late when reached | none | none | none | none (may relay a message) |
| **Action** | Ask for payment | Change window/offer/agent; do **not** code as dead | Retest with backoff; SMS/WhatsApp may still land | Test an **alternate** contact point; candidate for trace | **Invalidate**; stop dialing; stop paying for it | **Identity-challenge only**, no disclosure; invalidate if confirmed; **trace** | **No-disclosure script**; obtain a location/contact hint; never discuss the debt |

**Three concrete model mechanisms behind that table:**

1. **A competing-risks hazard model.** From the latent state "silent", the competing events are {answers-as-right-party, answers-as-wrong-party, network-death signal, continues-silent}. `hazardous`/`SurvivalBoost` implements competing-risks gradient boosting with proper scoring rules. This is the cleanest mathematical home for the distinction, and its output is directly a per-action probability.
2. **A dedicated recycled-risk head**, trained on: ≥90-day-gap flags; answer-hour-profile divergence (Jensen–Shannon between pre-gap and post-gap distributions); cross-account identity conflicts; agent-confirmed wrong-number labels; stranger-language transcript features. The **TRAI/DoT 90-day rule** gives a regulator-shaped, auditable prior for this head — rare, and very persuasive in a pitch.
3. **A deliberate probe policy.** Distinguishing "avoiding" from "dead" needs *contrastive* evidence, which the ordinary policy never generates (it always calls at the same times). So the engine schedules **information-seeking probes**: a different window, a different caller-ID, or a different low-cost channel whose failure modes differ from voice. This is *action as measurement* — and it is precisely why the decision engine and the model must be co-designed, not stacked.

> **Presentation-ready one-liner:** *"We don't ask the model whether the phone answered. We ask whether this number, called at 7 pm from an unknown caller ID, behaves like a person who can see the missed calls and is choosing not to pick up — or like a SIM that was reassigned eleven weeks ago."*

### 9.4 Detecting suspicious / recycled contact points (PS2) and suspicious GPS visits (PS3)

#### PS2 — suspicious & recycled contact points

| Detector | Signal | Implementation |
|---|---|---|
| **Regulatory-shape detector** | silence ≥ 90 days, then answering | binary + days-since-last-activity; grounded in the TRAI/DoT 90-day reallocation floor |
| **Behavioural discontinuity** | answer-hour profile shift; talk-duration shift; AMD-profile shift | Jensen–Shannon / KS divergence between pre-gap and post-gap windows; [P17]-style temporal-pattern encoder in production |
| **Identity conflict** | same number on accounts with different borrower names / DOBs / localities; agent "wrong number" marks; "who is this" phrasing | cross-account join + transcript NER; confidence-weighted vote |
| **Geographic inconsistency** | number's registered circle / observed region vs. the address locality | telecom-circle join (or coarse GeoLite); mismatch raises both recycling and "moved" suspicion |
| **Velocity / abuse patterns** | one number answering many different accounts (shop phone, gatekeeper, callback farm) | per-number outcome entropy; distinct-account answer count; answer-rate anomaly vs. carrier/prefix baseline |
| **Port / HLR signals** | ported flag, MCC/MNC change, line-type change | purchased lookup (Telnyx/Twilio/ClearoutPhone) as features |
| **Honeypot / decoy logic** | ≥90-day rule + discontinuity + identity conflict jointly triggered | **Identity Gate**: if recycled-risk > τ, only a no-debt identity challenge is legal, and the contact point is queued for correction (**DPDP §8(3) accuracy duty**) |

#### PS3 — suspicious GPS check-ins (the anti-label-poisoning layer)

This is **a model in its own right**, producing a scalar credibility weight `w ∈ [0,1]` per observation that scales its influence on the location estimate.

| Check | Feature | Rationale |
|---|---|---|
| **Attestation** | device mock-location flag; provider ∈ {gps, network, fused, cached}; app-integrity / Play-Integrity result; reported `accuracy` in metres; sensor availability | A spoofed or cached fix is cheap to flag — and impossible to fake if you verify attestation *at capture time* |
| **Spatial plausibility** | implied speed between consecutive fixes (teleport detector); Mahalanobis distance from the day's trajectory; whether the fix is even inside the stated pincode/city | HMM-style junk-point rejection ([G13]) |
| **Temporal plausibility** | dwell seconds vs. agent-reported duration; fix density during the claimed meeting; app foregrounded? | 40-minute meeting with 2 GPS points is suspicious; 200 points with no dwell is also suspicious |
| **Agent-day consistency** | was the agent actually in this locality that day (median of the day's fixes)? Is the previous visit reachable given travel time (routing-based)? | Prevents impossible visit sequences |
| **Cross-account duplication** | the same coordinate reported as a successful visit for many unrelated accounts | The classic lazy/fake check-in signature; a duplicate-rate penalty is brutally effective |
| **Text–GPS agreement** | does the remark/landmark mention a place within X m of the reported coordinate? | "Met at the temple by the ration shop" should be near a temple and a ration shop |
| **Outcome consistency** | payment collected + photo attested + borrower-side confirmation | Money is hard to fake |
| **Agent-level credibility** | rolling distribution of this agent's implied speeds, duplicate rate, GPS accuracy, outcome mix | Bayesian shrinkage toward the population mean when data is thin |
| **Peer disagreement** | other agents' observations of the same address | An outlier against 12 corroborating visits is likely fake |

**How the weight is used:** not as a hard filter, but as a **soft weight** in a robust estimator (Huber / trimmed weighted geometric median) and as a **sample weight** in the LTR ranker. Fraud therefore *degrades gracefully*: a poisoned observation is down-weighted rather than silently accepted, and the address's confidence radius **widens** rather than shifting.

### 9.5 How to model contact decay over time

Three layers, cheap → principled:

1. **Empirical decay curve (day 1).** Compute `P(answer | days_since_last_contact)` and `P(RPC | days_since_last_RPC)`, segmented by source-age bucket. Reproduce the published shape — fresh (0–7 d) ≈ 25%, warm (7–30 d) ≈ 16%, aged (30–90 d) ≈ 11%, cold ≈ 7% `[vendor claim]` ([Plura](https://www.plura.ai/articles/reduce-cost-contact-predictive-dialing-debt-collection-optimization)). This alone justifies re-ordering the dialing queue.
2. **Survival / hazard model (MVP).** Let `T` = time from last observed activity to the next successful right-party contact, right-censored when not yet observed. Covariates = contact-point features + time-varying features (attempts since, channel mix since, seasonality). Outputs `S(t)` (probability of no RPC by *t*) and hazard `h(t)`. This gives:
   - **Retest scheduling:** pick `t*` maximising `h(t) · V − c`. Never spend an attempt where the hazard is near zero (e.g. immediately after a rejection).
   - **Backoff policies:** a *rising* hazard after a gap implies that for some states (avoiders) **strategic silence beats persistence** — counterintuitive, and a great demo moment.
3. **Competing risks + time-varying covariates (production).** Extend to `{RPC, wrong-party answer, network death, continued silence}` with monotone constraints (attempts → hazard up; days-silent → network-death hazard up).

**Cadence:** nightly recalibration, weekly full retrain, with drift monitoring on the hazard baseline (the CDR fraud study's temporal-degradation warning applies directly).

### 9.6 How to calculate expected economic value of call / switch / visit / trace

Full treatment in §10. Summary of the four formulas:

- **Call:** `ENRC_call = A · R · [ P_ptp · P_keep · V · β + (1−P_ptp) · E[V_soft] ] − c_call − λ_f · fatigue − λ_c · q · C_compliance`
- **Switch contact point:** `ENRC_switch = ENRC_call(j') − ENRC_call(j) − c_switch − λ_d · Δ(quality)`
- **Field visit:** `ENRC_visit = p_home(a,τ) · [P_ptp|visit · P_keep · V · β + E[V_soft_visit]] − c_visit − c_travel_marginal − p_wrongdoor · C_compliance + VoI_geo · η`
- **Skip-trace (EVSI):** `ENRC_trace ≈ π_t · k_t · ΔRPC_per_point · p_recovery · V · β − c_trace(t)`

**Two subtleties that make ours better than a naive EV:**
- **Visit economics are route-level, not account-level.** The marginal cost of a visit depends on whether the agent is already going to that locality. So we solve a **VRP with time windows** and report the *marginal* ENRC of adding this stop. This is UrbanFlow-style geospatial optimisation — and it explains why **FRS-DRL cut field visits by 16.3% while improving collections by 20.34%** ([P7]): the visits were being spent badly, not too seldomly.
- **`C_compliance` is real money.** A wrong-door visit is an RBI/DPDP exposure. So a low-confidence geocode reduces visit EV through both the success term and a risk term — which is why PS3 creates value for PS2 *even before* it improves recovery.

### 9.7 How to prevent the model from starving low-scored contacts of exploration

Seven mechanisms (the first four ship in the MVP):

| # | Mechanism | Implementation | Guardrail |
|---|---|---|---|
| 1 | **Untested-first policy** | Any contact point with `< k` observations carries an explicitly wide posterior → its ENRC includes an **information bonus** | Bonus capped per account and per day |
| 2 | **VoI-directed exploration** | `VoI(j) = (E[max_a ENRC] − max_a E[ENRC]) × account_value`; explore where VoI × value is highest, **not at random** | Exploration ≤ 3–5% of attempts |
| 3 | **ε-floor + Thompson sampling** | ε ≈ 3–5% chance of a non-argmax **permissible** action, plus Thompson sampling over action posteriors (Optimizely documents ≥5% as the floor for continued learning, [P19]) | Randomisation restricted to legal, low-risk actions |
| 4 | **Propensity logging** | Log `p(a|context)` for every decision | Without it, exploration is unmeasurable |
| 5 | **Decay-triggered retest** | Any contact point untested for `T` days is forced into the queue regardless of score, because health *changes* | `T` from the survival model's median, not a guess |
| 6 | **Audit stream** | 1–3% of permissible decisions replaced by uniform-random legal actions, held out from learning | Excluded from harmful action classes |
| 7 | **Starvation dashboard** | Live count of contact points with zero attempts, split by score decile, plus marginal cost/contact by decile. **If the lowest decile's cost/contact is not dramatically worse than the next, we are under-exploring.** | Reviewed weekly |

> **The one-liner:** *"Exploration is not a random tax; it is a targeted purchase of information where the expected value of knowing exceeds the cost of finding out."*

### 9.8 How to calibrate the probability

| Level | Method | When / why |
|---|---|---|
| **Base** | `CalibratedClassifierCV(method='isotonic', cv='prefit')` on a held-out fold for H1/H2/H3 | Always. Boosting is miscalibrated by construction ([P11]); isotonic wins on large data ([P12]) |
| **Small-sample segments** | Platt scaling instead of isotonic | Segments with < ~1,000 calibration points (isotonic overfits) |
| **Segmented recalibration** | Separate calibrators per `channel × time-window × source-age × language` | Answer rates differ structurally by channel/window; one global map mis-prices actions |
| **Survival outputs** | Proper scoring rules — IPCW Brier, cumulative/dynamic AUC, concordance | Standard survival evaluation (`sksurv`) |
| **Decision-aware** | Fit the calibration map to minimise **expected ENRC error**, not just probability error | A small mid-range miscalibration changes the argmax |
| **Uncertainty for deferral** | **Conformal prediction sets** over the action set (which action is plausibly optimal?) | Route wide-set decisions to humans (conformal deferral) |
| **Monitoring** | Reliability diagrams + ECE per segment + **coverage checks** weekly; alert if ECE > threshold or coverage drifts > 2 pp | Model decay is a *financial* risk, not just an ML one |

**Worked illustration for the pitch:** with ECE = 0.05, 1,000,000 attempts/month, and a ₹12 blended cost per attempt, an uncalibrated model mis-prices the equivalent of roughly 50,000 attempts/month of decision error. Calibration is not housekeeping — it is money.

### 9.9 Which metrics to use

Full tables in §12. Headline set:

**Model:** PR-AUC (not ROC-AUC — low base rates), Brier, ECE + reliability diagrams **per segment**, Recall@k / Precision@k at the operational budget, NDCG@k for contact-point ranking within an account, C-index + IPCW Brier for the survival head, **Qini / AUUC / uplift@k** where randomisation exists, and **decision regret** (how far the chosen action's ENRC is from the best achievable).

**Business:** ₹ recovered per agent-hour, cost per RPC, RPC rate, PTP rate, PTP-kept rate, attempts per resolution, skip-trace ROI, field-visit success rate, visits per recovery, % of portfolio with a valid contact point, days-to-first-RPC.

**Guardrails:** wrong-party contact rate, third-party disclosure incidents (**0**), contacts outside 08:00–19:00 (**0**), DND violations (**0**), complaints per 10k contacts, attempt-cap breaches, recycling-detection precision.

---

## 10. DECISION ENGINE

### 10.1 The principle

> The model does not decide. The model produces **probability distributions over outcomes for each candidate action**; the decision engine converts them into **money**, filters by **law**, prices **uncertainty** and **information**, and picks the argmax — then writes a signed record explaining exactly why.

This is the REVIO pattern the team already owns, extended three ways: (i) actions are multi-dimensional (not call/no-call), (ii) the **null action has option value**, (iii) **information is a costed good** (probes and traces are purchases, not reflexes).

### 10.2 Notation

For account `i`, contact point `j`, address `a`, decision time `t`:

| Symbol | Meaning |
|---|---|
| `A` | P(Answer \| j, t, channel, caller_id) — head H1 (calibrated) |
| `R` | P(RightParty \| Answer, j, i) — head H2 (calibrated) |
| `P_ptp` | P(PromiseToPay \| RPC, i, offer, agent) — head H3 |
| `P_keep` | P(PTP kept \| PTP) |
| `V` | Amount at stake (balance + accrued interest/fees), or `E[V_recovered]` from a quantile model |
| `c_a` | Unit cost of action `a` (₹) |
| `τ` | Identity-gate threshold for disclosure |
| `N_week`, `N_max` | Attempts used this week / the cap |
| `u` | Model uncertainty on `A·R` (e.g. conformal interval half-width) |
| `λ_f` | Fatigue penalty per attempt (complaint risk + diminishing returns) |
| `q` | Recycling-risk score |

### 10.3 The core formula: Expected Net Recovery Contribution (ENRC)

For a voice call at contact point `j`, window `w`, channel `c`:

```
ENRC_call(j, w, c)
   = A(j,w,c) · R(j) · [ P_ptp · P_keep · V·β  +  (1 − P_ptp) · E[V_soft] ]
     − c_call(c)                                  ← direct cost
     − λ_f · fatigue(N_week, N_max)                ← regulatory + goodwill cost
     − λ_c · q(j) · C_compliance                   ← expected cost of a wrong-party exposure
```

| Term | Meaning |
|---|---|
| `β` | Expected fraction of `V` collected upon a PTP — from the payment-amount model, never assumed |
| `E[V_soft]` | Expected value of *partial* outcomes (a PTP without immediate payment, a warming contact, an address hint, an agreement to call back). **Never set to zero** — it is why many contacts are worth making even when no money moves |
| `C_compliance` | Expected regulatory/legal/relationship cost of an unauthorised disclosure (get one rough number from legal/ops — it transforms decision quality) |
| `fatigue(·)` | Increasing in `N_week / N_max`; at `N_week ≥ N_max` the action becomes **infeasible**, not expensive (see hard filters) |

**What this does that a propensity model cannot:** it correctly prefers a 12% answer-rate / 40% right-party / high-balance contact over a 45% answer-rate / 20% right-party / low-balance one, *and* prices the compliance risk of chasing a possibly-recycled number.

### 10.4 The other three actions

**Switch contact point** `j → j'`:

```
ENRC_switch(j→j') = ENRC_call(j') − ENRC_call(j) − c_switch − λ_d · Δ(quality)
```

`Δ(quality)` penalises moving to a lower-quality data source (e.g. from a KYC-verified number to a purchased one), because that raises long-run recycling risk.

**Field visit to address `a`** in window `τ`:

```
ENRC_visit(i, a, τ)
   = p_home(a, τ) · [ P_ptp|visit · P_keep · V·β + E[V_visit_soft] ]
   − c_visit − c_travel_marginal(a, R)        ← marginal cost given the day's route R
   − p_wrongdoor(a) · C_compliance            ← wrong-door exposure from geo uncertainty
   + VoI_geo(a) · η                           ← information value: this visit is also a label
```

- `p_home(a, τ) = p_place_is_home(a) × p_person_present(τ | home, income_proxy, locality_type)`. The **first factor is a PS3 output**; the second is a temporal-presence model.
- `p_wrongdoor(a) ≈ f(radius r(a), coverage level, locality density)` — derived **directly from the PS3 confidence radius**. This is the cleanest single line connecting PS3 to money.
- `VoI_geo(a) = η · u_geo(a) · (expected reduction in future decision error)` — the information bonus (§10.5).

**Route-level note:** `c_travel_marginal` is only computable after solving the day's route, so the engine runs two passes — (1) rank candidate visits by standalone ENRC; (2) solve a **VRP with time windows** over the top-N to get true marginal costs; (3) re-rank and finalise. It is ~30 lines of OR-Tools, and it is the difference between "we recommend visits" and "we schedule visits that pay for themselves."

**Skip-trace (tier `t`)** — framed as **Expected Value of Sample Information (EVSI)**:

```
ENRC_trace(i, t)
   = E_{J' ~ TraceYield(i,t)} [ Σ_{j' ∈ J'} (A·R·P_ptp·P_keep·V·β | j') − (best incumbent term) ]
   − c_trace(t)

ENRC_trace(i,t) ≈ π_t(i) · k_t · ΔRPC_per_point(i) · p_recovery(i) · V · β  −  c_trace(t)
```

| Term | Meaning | Where it comes from |
|---|---|---|
| `π_t(i)` | P(tier `t` yields ≥1 *new* usable contact point) | A yield model learned from **our own** historical trace outcomes — never the vendor's marketing numbers |
| `k_t` | Expected number of new contact points returned | Same |
| `ΔRPC_per_point(i)` | Expected RPC-rate **uplift per new point relative to the incumbent best point** | The RPC model. This term is what makes trace economics honest |
| `p_recovery(i)` | P(recovery eventually happens given RPC) | Payment model |
| `V·β` | Money at stake | Ledger |
| `c_trace(t)` | Tiered trace cost | Cost table |

**Why this is the killer feature.** Today, trace fires on an attempt count. Ours fires when `EVSI > c_trace(t)` **and** no cheaper action has higher ENRC — which correctly produces **four behaviours the industry does not distinguish**:

1. **High balance + high geo-uncertainty + high π_t** → trace **early**, before burning 5 attempts (because the attempts have option value).
2. **Low balance** → never trace; write off or route to a low-cost digital journey.
3. **High balance + low π_t (dense, well-known address, valid other numbers)** → don't trace; **visit** instead.
4. **Live number but unverified address** → trace/verify the **address**, not the phone — a different product, cost and yield model.

Case 4 is invisible to any attempt-count rule. It exists **only** if you model contact points and location separately — which is the entire justification for building PS2 and PS3 together.

### 10.5 Uncertainty, information and the option value of waiting

**VoI-annotated scoring.** Every candidate carries both a point estimate and:

```
VoI(i, j) = ( E_a[ max_a′ ENRC(a′) ] − max_a′ E_a′[ ENRC(a) ] ) × v_i
```

i.e. how much expected value is lost by acting under uncertainty, scaled by account value. Two consequences:

- A contact point with a wide `u` (big conformal interval) is **not** automatically deprioritised — it becomes a candidate for a cheap **probe**.
- **Waiting becomes a positive-EV action:**

```
ENRC_wait(Δ) = [ max_a ENRC(a, t+Δ) − max_a ENRC(a, t) ] − c_holdover(Δ)
```

This implements, as an optimisation rather than a heuristic, the industry observation that "each attempt is a scarce resource that should be deployed at the optimal time rather than burning the weekly allocation with poorly timed calls" `[vendor claim]`.

**Deliberate probing as measurement.** A probe is an action whose primary purpose is information, not collection:

| Ambiguity | Probe | What we learn |
|---|---|---|
| "Avoiding or dead?" | Call at a *different* window with a *different* caller-ID | Rejection at a new window ⇒ device-level avoidance; silence across all windows ⇒ dead/shifted |
| "Answered by whom?" | Identity-challenge call from a neutral caller-ID, **no debt mention** | Right-party identity → feeds `R`; legal when done without disclosure |
| "Is the address right?" | Low-cost channel (SMS/WhatsApp/IVR) + a field-visit candidate | Delivery success + dwell + outcome → PS3 evidence |
| "Is the number recycled?" | Compare the answer signature against the stored profile (name, gender, language, consent) | Recycled-head label |

Probes carry a costed ENRC with a positive information term, so they **compete** with collection actions on one scale. That is the mechanism that prevents starvation without random waste.

### 10.6 Hard constraints — implemented as candidate-set construction

Compliance is applied **before** scoring, so illegal actions literally have no score to be chosen by:

```
Candidates(i, t) = { a ∈ A :
      in_contact_window(t)                       // RBI: 08:00–19:00, all channels
   ∧  N_week(i, debt) + 1 ≤ N_max                  // attempt caps
   ∧  ¬on_dnd(j) OR has_consent(j)                 // DND/TRAI + consent
   ∧  purpose_permitted(action, purpose)           // DPDP purpose limitation
   ∧  (discloses_debt(action) → R(j) ≥ τ)          // IDENTITY GATE
   ∧  ¬suppressed(i, j, reason)                    // disputes, legal holds, hardship flags
   ∧  channel_consent(channel)                     // channel-specific consent
}
```

**The Identity Gate is the crown jewel of the compliance design.** Any action that discloses the debt (asking for payment, mentioning the loan, negotiating settlement) is available **only** on contact points where `R ≥ τ` (e.g. 0.90) or where a verified identity challenge has just succeeded. Every other contact point can still be contacted — but only with a **no-disclosure script** ("I'm calling from &lt;company&gt;; may I confirm I'm speaking with &lt;name&gt;?"), which is exactly what the regulation requires (RBI bans third-party disclosure; DPDP demands accuracy).

Because the gate is a *filter*, not a *weight*, the audit record can state: *"Action `request_payment` was not in the candidate set for contact point `p_4471` because P(right party) = 0.42 < τ = 0.90."* That is an auditable, defensible sentence — and it is only producible if you built head H2.

### 10.7 Exploration layer

```
policy     = argmax over Candidates of [ ENRC + ε_explore · VoI ]   // exploitation + targeted exploration
with prob ε_rand:  choose uniformly from Candidates ∩ SAFE           // budgeted randomness
propensity = P(chosen action | context)                              // LOGGED, always
```

| Parameter | MVP value | Rationale |
|---|---|---|
| `ε_explore` (VoI weight) | 0.20–0.30 of the VoI term | Exploration competes on value, not on noise |
| `ε_rand` (uniform floor) | 3% of attempts, restricted to `SAFE` (never legal escalation; never disclosure-capable on unverified numbers) | Optimizely's ≥5% figure is the anchor ([P19]); we start lower and tune against measured regret |
| `SAFE` action set | retiming, caller-ID change, channel switch to SMS/IVR, contact-point switch to a lower-priority point | Information-rich, low-risk |
| Audit stream | 1–3%, held out from training, for unbiased evaluation | Required for honest Qini/calibration in the low-score region |
| Kill switch | If cost-per-RPC in the exploration stream exceeds 2× the exploitation stream for 7 consecutive days, halve the exploration budget | Protects the P&L |

### 10.8 The audit record (REVIO lineage, extended)

Every decision writes an immutable row:

```json
{
  "decision_id": "dec_20261005_000177",
  "ts": "2026-10-05T19:42:11+05:30",
  "account_id": "A_88231", "contact_point_id": "P_4471", "address_id": "AD_1109",
  "model_versions": {"H1":"lgbm_h1_v3.2","H2":"lgbm_h2_v3.2","H3":"lgbm_h3_v3.1",
                     "hazard":"sksurv_gb_v2.0","sutra":"ltr_v1.4","calibrator":"iso_seg_v3"},
  "probabilities": {"A":0.34,"R":0.91,"P_ptp":0.22,"P_keep":0.78,"q_recycled":0.03},
  "value": {"V": 41250, "E_recovery": 6210, "beta": 0.61},
  "candidates": [
    {"action":"call","window":"19:00-20:00","channel":"voice","ENRC": 412.6},
    {"action":"sms","channel":"sms","ENRC": 118.4},
    {"action":"field_visit","ENRC": -38.2,
     "blocked_by": "p_wrongdoor=0.19 > 0.15 (radius=1400 m at 90% coverage)"},
    {"action":"skip_trace","tier":"T2","ENRC": -210.0,
     "blocked_by": "EVSI(210) < c_trace(850)"},
    {"action":"wait","delta_h":18,"ENRC": 96.3},
    {"action":"request_payment","hard_filters_passed": false,
     "blocked_by": "IDENTITY_GATE: disclosure requires a verified identity challenge first"}
  ],
  "chosen": "call", "propensity": 0.61,
  "reason_codes": ["HAZARD_PEAK_19H","SRC_AGE_11D","R_HIGH_VERIFIED_4D_AGO",
                   "BALANCE_HIGH","GEO_RADIUS_1400M_BLOCKS_VISIT","TRACE_EVSI_NEGATIVE"],
  "constraints_evaluated": {"config_version":"cc_v7","window_ok":true,
                            "attempts_this_week":2,"n_max":7,"dnd":false,"consent":"voice_yes"},
  "exploration_flag": false,
  "shap_top5": [["days_since_last_rpc",-0.19],["pincode_answer_rate",0.11]]
}
```

**Why this matters for CreditNirvana specifically:** the problem statement demands "explainable and auditable decisions" — this schema *is* that answer. It is also the training data for the next generation of the model (propensity + counterfactual logging), so the audit trail pays for itself twice.

---

## 11. SYSTEM ARCHITECTURE

### 11.1 Component map

| Layer | Component | Technology | Responsibility |
|---|---|---|---|
| **L0 Data** | Ingestion | Python + HTTP/Kafka/CDC from Postgres | CDR telephony, dispositions, transcripts, field telemetry, payments |
| | Lake | Parquet on S3/MinIO | Append-only, immutable event history |
| | Operational DB | **PostgreSQL + PostGIS** | Accounts, contact points, addresses, decisions, constraints |
| | **Feature store** | Postgres tables with `as_of` semantics (MVP) → Feast later | Point-in-time correctness; prevents post-decision leakage |
| | Geodata | PostGIS + H3 + OSM extract + pincode polygons + building footprints | Spatial joins, candidate generation, tiles |
| | Data quality | Great Expectations / dbt tests | Freshness, nulls, referential integrity, schema drift |
| **L1 Identity** | Entity resolution | **Splink** (MVP) → GNN/GraphER later | Contact-point graph, shared-number detection, landmark alias graph |
| **L2 PS2** | Training | LightGBM, scikit-survival / lifelines, scikit-uplift / CausalML | Heads H1–H5 + calibrators |
| | Explainability | SHAP → reason codes | Audit + agent UX |
| | Tracking | **MLflow** | Versions, metrics, artefacts, registry |
| **L3 PS3** | Parsing | libpostal + deepparse + IndicXlit/IndicLID (containerised) | Normalise, transliterate, language-ID |
| | Candidate generation | Self-hosted Nominatim/Photon + Google/Ola/Mappls APIs + OSM POI index | Candidate **set** (never a single answer) |
| | Gazetteer service | Postgres + pg_trgm + phonetic keys + alias graph | Landmark matching and alias learning |
| | Integrity model | Gradient boosting (§9.4 features) | Credibility weight per observation |
| | Ranker | LightGBM LambdaMART | Candidate ranking + explanation features |
| | Location estimator | Weighted geometric median / Huber | Robust centroid |
| | Radius estimator | GeoConformal (kernel-weighted split CP) | Radius at stated coverage |
| | Directions | Template engine + i18n (EN/HI/BN/TA/…) | Landmark directions that work offline |
| **L4 Decision** | Candidate builder | Python service, versioned config | Hard filters |
| | ENRC scorer | Python | §10 formulas |
| | Route optimiser | **Google OR-Tools** (VRP + time windows) | Visit scheduling, marginal travel cost |
| | Exploration | NumPy / bandit libs | VoI exploration, ε-floor, propensity logging |
| | Audit writer | Postgres append-only + hash chain | Immutable decision records |
| **L5 Backend** | API | **FastAPI** (`/score`, `/decide`, `/geocode`, `/visit-plan`, `/feedback`, `/audit`, `/health`) | Low-latency serving; uvicorn workers |
| | Cache / queue | Redis + Celery/RQ | Batch scoring, retraining, notifications |
| | Packaging | **Docker Compose** (MVP) → k8s later | Reproducible demo environment |
| **L6 Frontend** | Agent console | **React + TypeScript** + MapLibre/Leaflet | Contact-health heatmap, NBA card with reason codes, identity-gate state, no-disclosure script |
| | Field app | React PWA + **IndexedDB + bundled H3/pincode pack + Service Worker** | Offline-first: pin + radius + landmark route + local-language script; delta sync |
| | Manager dashboard | React + deck.gl | H3 heatmaps, trace ROI, compliance panel, model-health panel (ECE, coverage, drift, starvation) |
| **L7 Loop** | Orchestrator | Dagster/Prefect + MLflow | Nightly recalibrate, weekly retrain, monthly re-embed |
| | Off-policy evaluator | Open Bandit Pipeline (IPS/DR) | Promotion gate for any policy change |
| | Monitoring | Evidently/custom + alerts | PSI/KS drift, ECE, conformal coverage, decision regret |

### 11.2 Data → ML → decision → app → feedback

```
[1] Event lands (call ended, visit synced, payment posted)
        │
[2] Normalisation & enrichment
      phone → E.164; address → libpostal / deepparse / transliteration; GPS → map-match + integrity weight
        │
[3] Point-in-time feature assembly  (as-of the decision timestamp — enforced by the feature store)
        │
[4] Scoring: H1..H5 + graph features + SUTRA geo belief → calibrated probabilities + radius
        │
[5] Decision: candidates → hard filters → ENRC (+VoI) → route solve → argmax → audit row
        │
[6] Execution: dialer / bot / SMS / WhatsApp APIs · field-app task queue · trace-vendor API
        │
[7] Capture: outcome + telephony metadata + GPS trail + transcripts + remarks → back to [1]
        │
[8] Learning: nightly recalibrate · weekly retrain · gazetteer & alias updates · radius refresh
              → shadow deploy → off-policy evaluation → promote or roll back
```

### 11.3 Offline strategy for the field application (the part most teams get wrong)

Field agents in Indian tier-2/3 towns lose connectivity. Design:

1. **Bundle the index, not the service.** Ship a compact H3-indexed pack per operating district: predicted lat/lon + radius + landmark directions + pincode/village polygons + a small locality↔landmark gazetteer for fuzzy on-device search. Target < 100 MB per district.
2. **On-device search:** SQLite + R*Tree for spatial queries; a precomputed phonetic-key table so a misspelt landmark still resolves offline.
3. **Offline direction generation:** templates + the bundled landmark list. No LLM call, no network.
4. **Write-ahead capture:** GPS trail, dwell and outcome queued locally *with device attestation at the moment of the visit* — this is what makes the integrity model possible at all.
5. **Delta sync:** on reconnect, upload new observations and download only the updated packs for addresses the agent will visit.
6. **Graceful degradation:** if a pack is stale, the app marks the radius as *stale* and widens it explicitly rather than showing an over-confident pin. Trust is a feature.

---

## 12. EVALUATION

### 12.1 Model metrics

| Task | Primary | Secondary | Why these |
|---|---|---|---|
| **H1 P(Answer)** | PR-AUC | Brier, ECE, reliability curve, calibration by segment | Low base rates — ROC-AUC flatters. Brier/ECE because the output is multiplied by money |
| **H2 P(RightParty)** | PR-AUC on the answered subpopulation; **wrong-party recall at fixed precision** | ECE; recycled vs third-party confusion | The compliance-relevant error is a false "right party" — measure it directly |
| **H3 P(PTP)** | PR-AUC | **₹-weighted error** (not probability error) | A 0.05 error on a ₹5L account ≠ a ₹5k account |
| **Recycled head** | **Precision at the operating threshold** | Recall@fixed-precision, PR-AUC | Asymmetric cost: a false positive costs an identity challenge, a false negative costs a disclosure |
| **Hazard / survival** | C-index, **IPCW Brier**, cumulative/dynamic AUC | Calibration of `P(contact within k)` | Standard survival evaluation |
| **Uplift (H5)** | **Qini / AUUC / uplift@k** on randomised data | DR/IPS loss, policy gain | Only valid with randomisation ([P14]) |
| **Contact-point ranking** | **NDCG@k**, Recall@k at the day's call budget | MRR | Matches the operational question |
| **PS3 candidate ranking** | **Drift accuracy < 100 m / 500 m / 1 km** | median & p90 error, MRR of the correct candidate | Directly comparable to published numbers ([G4]) — comparability is how we prove we aren't fooling ourselves |
| **PS3 radius** | **Empirical vs nominal coverage**; **median radius at nominal coverage** | Coverage by strata (urban/rural) | The honest measure of a confidence radius |
| **PS3 purpose** | Balanced accuracy; home/work/shop/road confusion | Coverage of non-home conclusions | Non-home inference is fragile under POI incompleteness ([G19]) |
| **Integrity model** | ROC-AUC on injected fake check-ins; **does a faked visit move the estimate?** | Agent-level rank correlation with manual audit | The real test is robustness, not classification |
| **Whole system (offline)** | **Decision regret** = mean(chosen ENRC − best-achievable ENRC) | — | The single best "our decision layer works" metric |

### 12.2 Business metrics

| Metric | Definition | Direction | Anchor |
|---|---|---|---|
| **₹ recovered per agent-hour** | rupees collected / paid agent hours | ↑ | The north-star of [P2]: "more debt in less time, using substantially fewer resources" |
| **Cost per RPC** | total contact cost / RPCs | ↓ | The classic dialer denominator |
| **RPC rate** | RPCs / dials | ↑ | 8–15% cold B2C `[vendor claim]` as the "before" row |
| **PTP rate / PTP-kept rate** | PTPs per RPC; kept per PTP | ↑ | Kept-rate is the honest one |
| **Attempts per resolution** | dials + visits + messages until resolution | ↓ | Van de Geer's "fewer resources" result |
| **Skip-trace ROI** | (attributable recovery − trace fees) / trace fees | ↑ | Trace as a purchase, measured like one |
| **Field-visit success rate** | visits meeting the borrower / visits | ↑ | Anchored to FRS-DRL's −16.3% visits, +20.34% collections |
| **Visits per recovery** | visits / recoveries | ↓ | The efficiency reading of the same data |
| **% portfolio with a valid contact point** | accounts with ≥1 point at `A·R > threshold` | ↑ | Contactability-book coverage |
| **Days to first RPC** | from allocation | ↓ | Speed matters most in early buckets |
| **Roll rate / recovery rate** | standard collections KPIs | ↓ / ↑ | What clients actually judge |
| **Cost-to-collect ratio** | collection cost / amount collected | ↓ | McKinsey's ~40% opex framing |
| **Stage-transition lift (30→60→90 DPD)** | roll-rate reduction | ↓ | The clearest leading indicator that early outreach changed outcomes |

### 12.3 Compliance / guardrail metrics (reported on the same dashboard — non-negotiable)

| Metric | Target |
|---|---|
| Contacts outside 08:00–19:00 IST | **0** |
| Third-party debt-disclosure incidents | **0** |
| Wrong-party contact rate | ↓, with a hard ceiling |
| Attempts beyond `N_max` per debt per week | **0** |
| DND / consent violations | **0** |
| Complaints per 10,000 contacts | ↓ |
| Recycling-detection precision | ≥ 0.95 |
| Decisions with a complete audit record | **100%** |
| Disclosure-capable actions taken where `R < τ` | **0** — verifiable structurally in the audit log |
| Conformal coverage deviation (empirical vs nominal) | ≤ 2 pp |

### 12.4 The evaluation protocol (how we avoid fooling ourselves)

1. **Strict temporal split.** Train on `t < T`; validate `T … T+14d`; test `T+14d … T+28d`. **Never random-split** — the problem is temporal, and random splits leak the future into the past.
2. **Point-in-time features only**, enforced by the feature store's `as_of` semantics. Any feature knowable only after the decision is banned. (This is the #1 way hackathon models "win" and real models die.)
3. **Propensity-weighted metrics** wherever data is policy-selected; report both weighted and unweighted so the bias is visible.
4. **Segment reporting, always:** metro vs tier-2/3, language, channel, source-age band, account-value band. A model that wins on average and loses in tier-3 is a liability for CreditNirvana.
5. **Policy-level offline evaluation** via IPS/DR over logged decisions, plus a **counterfactual simulation** on the synthetic generator whose ground truth we hold. This is how we claim an improvement number before deployment — honestly.
6. **Shadow-mode deployment:** run the new policy alongside the incumbent for a week, logging would-be decisions only, then compare.
7. **A one-page model card per model:** intended use, prohibited use, calibration, segment performance, retraining cadence, owner.

---

## 13. DEMO STRATEGY (2–3 MINUTES)

### 13.1 The single sentence the judges must remember

> **"We made the field visit do two jobs at once: it collects money *and* it teaches the geocoder — so every rupee of field budget buys a better map, and every better map makes the next rupee of field budget buy more money."**

### 13.2 Storyboard (timed)

| t | Beat | What is on screen | What we say |
|---|---|---|---|
| **0:00–0:15** | **The wound** | A real Indian address: *"Plot 14, behind Hanuman Mandir, near Sharma ration shop, 2nd cross, Gudgaon"*. Google pin drops at the **locality centroid**. Map shows the pin 1.4 km from the true house, and a **circle** of radius 1,400 m. | "India's addresses are sentences, not coordinates. Today's geocoder gives a locality centroid — and no honest measure of how wrong it is. This is why field agents knock on the wrong door." |
| **0:15–0:35** | **What everyone else does** | Split-screen: (a) attempt-count rule — *"3 attempts failed → trigger skip-trace"*; (b) our dashboard. | "Every system we found triggers skip-trace on an attempt counter, and treats field-visit GPS as ground truth. Both are wrong: a counter knows nothing about expected value, and GPS includes fakes." |
| **0:35–1:05** | **PS2: the decision changes because the *right party* is uncertain** | Two accounts with **identical P(answer) = 0.05**. Left: *avoiding* → recommendation "retest 19:00–20:00 with caller-ID B; do not code as dead". Right: *recycled suspect* (silent 94 days, then a stranger answered) → recommendation "**identity challenge only — no debt disclosure**; queue for correction; trace EVSI = −₹210 so **do not trace**". Show the reason codes and the SHAP bars. | "Same probability, opposite actions — because we model answer, identity and productivity separately. And we don't trace on a counter: we trace when the *expected value of the information* beats its price." |
| **1:05–1:35** | **PS3: uncertainty is priced, and it blocks a bad visit** | The visit card is **blocked**: *"p_wrongdoor = 0.19 > 0.15, radius 1,400 m at 90% coverage."* Toggle "geocode improved" → radius **1,400 m → 90 m** → the same card turns **green** (ENRC −₹40 → +₹115). | "Geo-uncertainty isn't a cosmetic issue. It blocks field visits through the *success* term **and** the compliance-risk term. This is PS3 creating money for PS2 before it recovers a single rupee." |
| **1:35–2:05** | **The loop closes — live** | Click **"send address to field verification"**. Simulated agent GPS returns: a trail, a 34-minute dwell, *"met borrower at home"*, photo attested. Watch: (i) radius shrink and the pin snap to the building; (ii) contact-health card update — the phone that was "recycled suspect" now reads *"address confirmed; borrower present"*; (iii) **tomorrow's recommended action flips from "call again" to "visit with these landmark directions"**. | "One visit. It collected nothing today — and it was worth making anyway, because it just bought us a trustworthy label. That's the loop nobody else closes." |
| **2:05–2:25** | **The anti-hype proof** | Inject a **fake check-in**: an implausible GPS jump + a duplicate coordinate already reported for 6 unrelated accounts. The estimate **does not move**; the radius **widens**; the agent's credibility score drops; the fraud row appears in the ops panel. | "Field data is not ground truth. We weight every observation by an integrity model — so fraud degrades accuracy gracefully instead of poisoning the map." |
| **2:25–2:45** | **Money + compliance, side by side** | Dashboard: ₹ recovered per agent-hour ↑; cost per RPC ↓; visits per recovery ↓; skip-trace ROI on traced accounts; and a compliance panel reading **0 disclosures, 0 out-of-window contacts, 100% audit records**. | "The default view is money and compliance — not ROC curves. Every decision here is a signed, auditable record with the constraints it evaluated." |
| **2:45–3:00** | **Offline + close** | Turn off wifi in the field app — the pin, the radius, the landmark directions and the local-language script still render. | "And it works with no network, because our agents are in places with no network. PS2 decides *who* and *when*; PS3 decides *where*; one engine turns both into the best next action." |

### 13.3 Design rules for the demo

- **One account, one screen, one decision at a time.** No scrolling dashboards in the first 90 seconds.
- **Every claim on screen has a number next to it** (radius in metres, ENRC in ₹, EVSI vs. trace cost, p_wrongdoor). Judges reward specificity; vague AI-talk loses.
- **Show a refusal.** The blocked visit and the rejected trace are more persuasive than any positive recommendation, because they prove the engine computes economics rather than producing enthusiasm.
- **Never fake the hard parts.** The synthetic generator, the integrity model and the conformal coverage test are all real code with real outputs; the demo is a rehearsal environment, not a mock.
- **Keep a pre-recorded 3-minute fallback** in case the venue's network dies.

### 13.4 The 5 questions we must be able to answer instantly (rehearse these)

1. **"How do you know the label is right?"** → Three-factor decomposition; payment/inbound calls are the gold-standard label; refunded attempt-level censoring; propensity weighting.
2. **"What if CN has no field data yet?"** → The synthetic CN generator with the identical schema, plus the OSM/pincode/Geolife prototype stack; swap-in is a config change.
3. **"Isn't this just geocoding + a call model?"** → No — the coupling *is* the contribution (D4/D5), plus the calibration guarantee (D7) and the compliance-by-construction design (D8).
4. **"Why will agents trust it?"** → Reason codes, the identity gate, offline operation, a visible radius instead of a false-precision pin, and no-disclosure scripts that protect them personally.
5. **"What's the ROI?"** → Fewer wasted visits (radius-driven), trace only when EVSI is positive, and better attempt timing — anchored to published results (fewer resources, more recovery) and stated as *our* measurable targets, not promises.

---

## 14. HACKATHON MVP — MUST / SHOULD / NICE

### 14.1 MUST (if we only ship this, we still win)

| # | Deliverable | Why it is non-negotiable | Definition of done |
|---|---|---|---|
| M1 | **Synthetic CN generator** with the exact schema (accounts, contact points, attempts, visits, GPS, remarks, ground truth) + legacy policy | Everything else depends on it; it is the swap-in contract with real data | `make data` produces all parquet files + a data dictionary in < 2 min; a notebook validates the 25/16/11/7% decay shape emerges |
| M2 | **H1 P(Answer) + H2 P(RightParty) LightGBM heads, calibrated** (isotonic, segmented) | The core prediction; H2 is the compliance engine's fuel | PR-AUC beats the logistic baseline; ECE < 0.03 on test; reliability plots saved to MLflow |
| M3 | **Three-factor decomposition visible in the UI** ("why" card with reason codes + top-5 SHAP) | This is D1, the headline novelty | Two same-probability accounts get different recommendations with visible evidence |
| M4 | **ENRC decision engine** with the four actions + WAIT, hard-constraint filter (window, caps, DND, **identity gate**), propensity logging | D2/D8; the "decision" in the decision engine | Every decision returns a candidate list with per-candidate ENRC and blocked_by reasons |
| M5 | **Skip-trace EVSI gate** | D2 — the single most quotable feature | Changing the trace price on a slider flips decisions live |
| M6 | **PS3 pipeline end-to-end on synthetic + OSM**: parse → gazetteer → candidate gen → **integrity-weighted estimate → conformal radius → landmark directions** | D6/D7; the radius is the money link to PS2 | Radius shrinks after new visits; coverage test on held-out visits within 2 pp of nominal |
| M7 | **The demo loop** (visit → label → radius ↓ → tomorrow's action flips) working as a single click sequence | D5 — the story | Runs 3 times in a row without manual data fixing |
| M8 | **Audit record** written for every decision, queryable in the UI | D8 + the problem statement's "auditable" requirement | A decision can be replayed showing config version, probabilities, candidate ENRCs, constraints |
| M9 | **FastAPI backend + Docker Compose** one-command startup | Judging is time-boxed; a broken start is fatal | `docker compose up` → working demo in < 3 min on a clean machine |

### 14.2 SHOULD (the difference between "good" and "wins")

| # | Deliverable | Payoff |
|---|---|---|
| S1 | **H4 survival/hazard head** (`sksurv`) with censoring | D3; enables retest scheduling and the "avoiders get *more* contact by being called less" insight |
| S2 | **Recycled-risk head** on the ≥90-day-gap population | Makes the identity gate sharp and demo-able |
| S3 | **Integrity model with a live fake-check-in demo** | D6 — the anti-poisoning story lands hard |
| S4 | **Exploration layer** (VoI bonus + 3% ε-floor) + **starvation dashboard** | D9; answers the problem statement's exploration requirement concretely |
| S5 | **Route-aware visit economics** (OR-Tools VRP, marginal ENRC) | Shows visits are scheduled on marginal cost, not standalone EV |
| S6 | **Offline field PWA** (service worker + bundled pack) with airplane-mode demo | D10; visually unforgettable |
| S7 | **Manager dashboard**: H3 heatmaps, trace ROI, compliance panel, model-health panel (ECE, coverage, drift, starvation) | Default view = money; proves §12 is implemented, not aspirational |
| S8 | **Address-corruption benchmark** (OSM-derived, 5k addresses, known ground truth) plus drift-accuracy numbers <100 m/<500 m/1 km | Lets us compare honestly with published SOTA ([G4]) |
| S9 | **Off-policy evaluation** (IPS/DR) vs. the legacy synthetic policy | "Fewer resources, more recovery" claimed with a method, not a vibe |
| S10 | **MLflow tracking + model cards** | Signals engineering maturity to technical judges |

### 14.3 NICE (production roadmap, described in the pitch — not built at the event)

| # | Deliverable | When |
|---|---|---|
| N1 | GNN over the contact-point graph (GraphSAGE/GAT) | Production, month 2 |
| N2 | Sequence encoder (GRU/transformer) over attempt sequences | Production, gated on data volume |
| N3 | Uplift/CATE per action + permanent randomised holdout | Production, with volume |
| N4 | Multi-head H3 address model + address RoBERTa fine-tuned on CN corpus | Production, month 2–3 |
| N5 | Multi-task staleness encoder (the D4 joint factor, learned) | Production, month 3 |
| N6 | Ops Console for agency-side recording compliance + QA sampling | Production |
| N7 | Bhashini/BHASH-A integration for multilingual transcripts at scale | Production |
| N8 | Sentinel/geodemographic H3 embeddings as geocoder context | Production, exploratory |

### 14.4 Team split (4 people, 48 hours)

| Person | Owns | Interface contract |
|---|---|---|
| **A — Data & sim** | M1 generator, feature pipelines, feature store `as_of` logic, MLflow | Emits frozen parquet + feature views |
| **B — PS2 models** | M2 heads, S1 hazard, S2 recycled head, S4 exploration, calibration | Emits `/score` JSON: `{A, R, P_ptp, q, hazard}` per contact point |
| **C — PS3 models** | M6 parsing/gazetteer/candidates, S3 integrity, conformal radius, directions | Emits `/geocode` JSON: `{lat, lon, radius@90, purpose, directions, evidence[]}` |
| **D — Decision + app** | M4 engine, M5 EVSI, M8 audit, M9 API/Compose, S6 offline PWA, S7 dashboard | Consumes `/score` + `/geocode`; owns the demo script |

**Hard rules for the 48 hours:** freeze the two API contracts by hour 4; every component must run against the *synthetic* data by hour 24; no model retraining after hour 40 (only parameter tuning); the demo runs from a **clean checkout** at hour 47.

---

## 15. EXECUTION PLAN

### 15.1 The compressed hackathon plan (48–72 hours, the recommended option)

**Day 0 (2 h, before the clock starts)**
- Lock the two API contracts (`/score`, `/geocode`) and the JSON schemas.
- Confirm dataset downloads: OSM India extract (target cities), pincode polygons, Geolife, Hillstrom, Bank Marketing.
- Create the repo skeleton: `data/`, `models/`, `decision/`, `api/`, `web/`, `field/`, `notebooks/`, `docker-compose.yml`, `Makefile`.

**Day 1 — data + baseline (the boring day that decides everything)**
| Slot | Work |
|---|---|
| Morning | M1 synthetic generator v1 (accounts, contact points, attempts, latent types, legacy policy). Validate the decay curve and RPC base rate. |
| Midday | Baseline models (logistic + LightGBM on P(answer)) → first PR-AUC/Brier/ECE. Freeze the temporal split. |
| Afternoon | PS3 sanitisation: OSM extract for 2 cities → POI/landmark table; pincode polygons; address corruption generator (5k synthetic addresses with ground truth). |
| Evening | `pgvector`/PostGIS schema; feature assembly with `as_of`; **first end-to-end smoke test**: score one contact point, produce one decision. |

**Day 2 — the system**
| Slot | Work |
|---|---|
| Morning | H2 right-party head + recycled head; segmented isotonic calibration; SHAP→reason codes. |
| Midday | PS3: libpostal parsing, gazetteer + phonetic keys, candidate generation, LTR ranker v1, weighted robust estimator, **conformal radius**. |
| Afternoon | Decision engine: candidates, hard filters (identity gate!), ENRC, WAIT, propensity logging, audit record; OR-Tools VRP. |
| Evening | FastAPI endpoints + Docker Compose; agent-console UI with the "why" card. **Demo acts 1–3 must run.** |

**Day 3 — the show**
| Slot | Work |
|---|---|
| Morning | Integrity model + fake-check-in demo; offline PWA with bundled pack; the loop act (visit → radius ↓ → action flips). |
| Midday | Manager dashboard (money + compliance + model health); starvation panel; trace-price slider. |
| Afternoon | Freeze code; rehearse the 3-minute script 5×; record the fallback video; write the model cards and the one-slide architecture. |
| Evening | Buffer. Ship. |

### 15.2 The full 14-day plan (if this is being built for real, with real CN data)

| Day | Focus | Deliverable | Gate to pass |
|---|---|---|---|
| **1** | Data audit & schema mapping | CN tables mapped to §8.1 tiers; identify gaps; find **inbound-call events** | Written data-readiness notes; Tier-1 completeness ≥ 80% |
| **2** | Synthetic generator v1 + evaluation harness | `synthetic_cn_generator.py`; temporal split; metric harness | Published decay shape reproduced; harness runs end-to-end |
| **3** | Baseline models | Logistic + LightGBM for P(answer), P(RPC) | PR-AUC, Brier, ECE logged in MLflow |
| **4** | Feature store + point-in-time correctness | `as_of` feature views; leakage tests | A deliberately leaky feature is caught by the test |
| **5** | H2 right-party + recycled head | Calibrated H2; recycled-head prototype | Wrong-party recall at fixed precision reported |
| **6** | Survival/decay head | `sksurv` hazard model; `P(contact within k)` | C-index + IPCW Brier beats a constant-hazard baseline |
| **7** | Decision engine v1 | Candidates, hard filters, ENRC, audit records | Every decision replayable from the audit row |
| **8** | Trace-EVSI + exploration | EVSI gate; VoI bonus; ε-floor; propensity logs | Trace decisions change with price; starvation metric tracked |
| **9** | PS3 parsing + gazetteer | libpostal/deepparse + learned landmark aliases + phonetic keys | ≥ 80% landmark-match recall on a labelled sample |
| **10** | PS3 candidates + ranker + radius | LTR ranker; weighted estimator; conformal radius | Coverage within 2 pp; drift accuracy reported vs. G4 baseline |
| **11** | Integrity model | Credibility weights; fraud-injection tests | An injected fake visit does not move the estimate |
| **12** | Field app + offline packs | PWA with district packs; delta sync | Full workflow in airplane mode |
| **13** | Dashboards + API hardening | Money/compliance/model-health views; load test | p95 latency < 150 ms for `/decide`; 100% audit coverage |
| **14** | Shadow-mode setup + pitch | Shadow logging, off-policy evaluation harness, model cards, deck | Off-policy estimate of policy gain vs. incumbent, with CIs |

**Sequencing rule:** PS3 work (days 9–12) must not block PS2 (days 3–8). The interface between them is the geo-belief JSON. If PS3 slips, PS2 still ships with a wide, honest radius — and the demo still works, because the *coupling* is demonstrated through the radius parameter, not through PS3's internal sophistication.

---

## 16. FINAL RECOMMENDATION

### 16.1 The verdict, stated plainly

| Question | Answer |
|---|---|
| Which is more **feasible**? | **PS2.** Labels (RPC events, dispositions, telemetry) already exist; a competent MVP is 3–5 days; the decision-engine pattern is one the team has already built (REVIO). |
| Which has more **differentiation headroom**? | **PS3.** Commercial geocoders are all locality-centroid-grade on Indian addresses; nobody ships calibrated radii or learns from field GPS with integrity weighting; the visuals are superior. But it carries higher model risk and a heavier data dependency. |
| Which has more **hackathon potential**? | **PS3 for the "wow", PS2 for the "so what". Build both — but sequence them so PS2 is never at risk.** |
| **What do we build?** | **PS2 + PS3 as one system**, because PS3's **labels are produced by PS2's actions** and PS2's **best action depends on PS3's uncertainty**. Building one is building half a system; building both is building a flywheel. |

### 16.2 Why the combination is not just additive

1. **Label dependency (mechanical):** field visits are one of PS2's actions and PS3's only high-quality label source. Separately, PS2 never learns to value visits for information, and PS3 never receives the visits it needs.
2. **Decision dependency (economic):** the PS3 confidence radius enters the PS2 visit-EV formula twice — through `p_home` and through `p_wrongdoor · C_compliance`. Without PS3, visit decisions are systematically over-confident.
3. **Compliance dependency (legal):** fewer wrong-door visits means fewer third-party exposures. PS3 is a compliance instrument, not just a mapping utility.
4. **Shared latent variable (statistical):** "the borrower moved" drives both phone-recycling symptoms and address staleness (§6.5). The joint factor is more predictive than either head alone.
5. **Novelty (competitive):** every competitor we surveyed solves one half. G-6 (contact intelligence ∥ location intelligence) is the gap, and the combination is the moat.

### 16.3 The exact approach to build (one paragraph)

Build **SANKET** (PS2) as three calibrated LightGBM heads — `P(Answer)`, `P(RightParty | Answer)`, `P(Productive | RPC)` — plus a **competing-risks survival head** for contact decay, plus a hand-built **contact-point graph feature block** (shared numbers, neighbour RPC rate), all calibrated per segment with isotonic regression under a strict temporal split with point-in-time features and propensity logging. Build **SUTRA** (PS3) as a **parse → normalise/alias → generate candidates → rank (LightGBM LTR over text + GPS + OSM/POI + boundary features) → robust weighted estimate → conformal radius → landmark directions** pipeline, with an **integrity model** weighting every field observation. Join them with a **constrained expected-value decision engine** that enumerates actions (call / message / switch contact point / field visit / skip-trace / wait / suppress), filters them by law (08:00–19:00, attempt caps, DND, DPDP purpose, and an **identity gate requiring `P(RightParty) ≥ τ` before any debt-disclosing action**), prices each candidate by **ENRC** — with skip-trace as **EVSI** and the visit's geo-uncertainty as both a success penalty and an information bonus — solves the day's **visit route** with OR-Tools for true marginal costs, adds a **budgeted, VoI-directed exploration layer** with 3% ε-floor and propensity logging, then writes an immutable **audit record** with reason codes and SHAP evidence. Everything runs on a **CN-shaped synthetic generator** (schema-identical, so real data is a config change), served by **FastAPI**, visualised in a **React/TypeScript** agent console, field PWA (offline-first with bundled H3/pincode packs) and manager dashboard, tracked in **MLflow**, instrumented with model, business and compliance metrics, and evaluated with **strict temporal splits, conformal coverage checks, decision regret, and off-policy evaluation** before any policy is promoted.

### 16.4 What we explicitly do **not** do (and why)

| Not doing | Why |
|---|---|
| Sequence models (LSTM/GRU) in the MVP | Data-hungry, poorly calibrated, cold-start-hostile — and we cannot yet prove they beat GBM features |
| GNNs in the MVP | Only after there is enough graph density; hand-built graph features capture most of the lift now |
| Geospatial foundation models | Compute-heavy, licensing-heavy, no evidence of superiority over a good LTR ranker on Indian addresses today |
| Median-of-GPS as the location estimate | Amazon's finding: field GPS error is **biased**, not zero-mean; a naive mean/median inherits the bias |
| Fixed-attempt-count skip-trace | Contradicts the problem statement and destroys value on low-balance and low-yield cases |
| Ranking by propensity rather than incremental value | The field experiment in [P2] shows propensity ranking misallocates effort |
| Storing commercial geocoder outputs as training data | Google/MapmyIndia ToS restrict caching; runtime use only |
| Using Bhuvan (ISRO) | ToS forbids re-use without written authorisation — a licensing trap |
| Training on contacted-only populations without correction | Guarantees a feedback-loop model that looks calibrated and isn't |
| Treating "no answer" as a negative label | It is censored data, and the difference is measurable in PR-AUC and in field spend |

### 16.5 Success criteria for the build (how we will know it worked)

**Hackathon:** the 3-minute demo runs clean twice; the loop act works live; a judge can ask "why this action?" and get an audit record; the blocked visit and the rejected trace are shown as evidence of economics, not enthusiasm.

**Pilot (30 days, one portfolio, one city):** radius median at 90% coverage < 300 m in urban areas and shrinking week over week; coverage within ±2 pp; visit-success lift ≥ 15% relative; cost per RPC down ≥ 10%; zero compliance breaches; skip-trace spend reallocated with measurable ROI; decision regret decreasing; the exploration stream's cost-per-RPC within 2× of exploitation (i.e. starvation is being cured cheaply).

**Production (2 quarters):** contactability coverage of the book up; ₹ recovered per agent-hour up with the same headcount; trace spend down while recovery holds; field-visit count down while collections hold or improve — the FRS-DRL shape (fewer visits, more recovery), reproduced on CN's own data.

---

## RECOMMENDED SOLUTION TO BUILD

### Architecture in one picture

```
  ADDRESS (Hindi/English/regional, landmark-based, misspelt)
        │
        ▼
  ┌──────────────────────────── SUTRA (PS3) ────────────────────────────┐
  │ parse (libpostal + deepparse + IndicXlit)                            │
  │ → alias/phonetic normalise (learned landmark gazetteer + OSM)        │
  │ → candidate set (geocoder + OSM POI + H3 heads + embedding kNN)      │
  │ → rank (LightGBM LTR: text + GPS + POI + boundary + visit history)   │
  │ → purpose (home / work / shop / road) from dwell + POI + outcome     │
  │ → integrity weight per observation (anti-fake-check-in model)        │
  │ → robust weighted estimate + GeoConformal radius @ 90%               │
  │ → landmark-based directions (EN/HI/BN/TA…, offline)                  │
  └──────────────────────────────────┬───────────────────────────────────┘
                                     │  {lat, lon, radius@90, purpose, evidence}
                                     ▼
  ┌──────────────────── SANKET (PS2) ────────────────────────────────────┐
  │ H1 P(Answer | point, window, channel, caller-ID, history)            │
  │ H2 P(RightParty | Answer)  +  recycled-risk head (TRAI 90-day shape) │
  │ H3 P(Productive | RightParty, offer, agent)                          │
  │ H4 competing-risks hazard for contact decay (censored, not negative)  │
  │ CAL segmented isotonic calibration · SHAP reason codes               │
  │ GRAPH shared numbers · degree · neighbour RPC · cross-account identity│
  └──────────────────────────────────┬───────────────────────────────────┘
                                     ▼
  ┌─────────────────── DECISION ENGINE (constrained EV, REVIO++) ────────┐
  │ candidates: call / message / switch point / field visit / trace /    │
  │             escalate / WAIT / suppress                               │
  │ HARD filters: 08:00–19:00 · attempt caps · DND · DPDP purpose ·      │
  │               IDENTITY GATE (disclose ⇒ P(RightParty) ≥ τ)           │
  │ ENRC = A·R·[P_ptp·P_keep·V·β + (1−P_ptp)·E[V_soft]] − cost − fatigue │
  │        − compliance risk    ·   visit adds − p_wrongdoor·C + VoI_geo  │
  │ skip-trace = EVSI purchase vs its fee (4 distinct behaviours)        │
  │ route: OR-Tools VRP with time windows → marginal travel cost          │
  │ exploration: VoI bonus + 3% ε-floor (permissible actions only)        │
  │ → argmax → execute → IMMUTABLE AUDIT RECORD (reason codes, SHAP,      │
  │                                        constraints, propensity)       │
  └──────────────────────────────────┬───────────────────────────────────┘
                                     ▼
   AGENT CONSOLE · FIELD PWA (offline, local language, radius) · DASHBOARD
                                     │
                                     ▼
  ┌────────────────── CONTACT-TRUTH LOOP (the differentiator) ───────────┐
  │ visit GPS + dwell + outcome (attested, integrity-weighted)            │
  │   → SUTRA: radius 1,400 m → 90 m, gazetteer + aliases updated         │
  │   → SANKET: policy-independent label, staleness factor updated        │
  │   → decision engine: tomorrow's action flips from "call" to "visit"   │
  │ nightly recalibrate · weekly retrain · off-policy eval before promote │
  └──────────────────────────────────────────────────────────────────────┘
```

### Why this is the best thing for this team to build

1. **It is the only design that uses CreditNirvana's actual differentiator.** CN's field visits are a proprietary, hard-to-copy data asset. Every competitor's geocoder gets better by *buying* data; CN's gets better by *working*. This design converts an operating cost into a compounding data asset — and it is defensible precisely because it cannot be copied without the field force.
2. **It answers every line of the problem statements, not just the headline.** Decay → survival head. Avoiding vs. invalid → three-factor decomposition + competing risks. Recycling → regulator-shaped detector + identity gate + DPDP correction loop. Unobserved contacts → censoring + propensity weighting + audit stream. Exploration/starvation → VoI bonus + ε-floor + starvation dashboard. Explainability/audit → the audit record schema. Confidence radius → GeoConformal. Offline → bundled packs. Third-party disclosure → structural candidate filtering.
3. **It reuses the team's proven muscles instead of gambling on new ones.** REVIO → the decision engine + audit trail. UrbanFlow AI → H3 spatiotemporal features, geospatial optimisation, large-scale pipelines. Gurgaon real-estate ML → address/geo feature engineering and geocoding failure modes. TubeSignal NLP → multilingual remark/transcript understanding.
4. **It is honestly staged.** A 3-day path exists (generator + two calibrated heads + ENRC engine + radius + demo loop); a 14-day path exists (with real data, hazard head, integrity model, offline app, shadow deployment); and a production path exists (GNN, uplift with holdouts, bandits, learned staleness encoder, address RoBERTa). Each stage is useful on its own — nothing here is a demo-only artefact.
5. **The economics are legible to a non-ML decision-maker.** Field visits that pay for themselves, trace spend that is priced like a purchase, dials deployed when their hazard peaks, zero third-party disclosures, and an audit trail for every rupee-relevant decision. That is a business case, not a model card.
6. **It is differentiated in a way that is checkable.** Every claim in §7 (D1–D11) can be demonstrated live against a system that does the naive thing. Judges do not have to take our word for it — and neither does CreditNirvana.

> **Final line for the pitch:** *Build PS2 + PS3 as one closed loop. PS2 tells CreditNirvana who to reach and when — priced by expected value and gated by identity. PS3 tells it where the borrower actually is — with a radius it can defend. And every field visit makes both of them better, automatically, forever.*

---

# Appendix B. Financial model — full run output

*Source: `financial_model_output.txt`, regenerated by `python3 financial_model.py`. Every input is tagged `[PUB]` / `[EXT]` / `[ASSUME]` / `[MODEL]`. Illustrative, not a measurement of any portfolio.*

```text
[MODEL] gross recovery per RPC  = Rs 1,175;  INCREMENTAL = Rs 323.16  <-- used everywhere below
====================================================================================================
S1 — WHAT ACTUALLY COSTS MONEY  (the scope decision)
====================================================================================================
action                                               low      high   source
Automated dial (voice-AI, 60-75s)                Rs 1.35   Rs 2.59   [PUB] India voice-AI Rs4-7/min + Rs0.55/min telephony
Automated dial (human agent)                     Rs 8.48   Rs 8.48   [PUB] Rs15,788/mo agent salary + loading / [ASSUME] 3,300 dials/mo
HLR / number-intelligence lookup                 Rs 0.13   Rs 0.60   [PUB] Telnyx $0.0015/dip; Neutrino $0.007; Twilio $0.005-0.04
SMS / WhatsApp (utility)                         Rs 0.15   Rs 0.25   [PUB] WhatsApp utility per-conversation price
Skip-trace (data purchase)                      Rs 60.00 Rs 150.00   [PUB-anchored] global bulk $5-25/record; India per-case higher
Field visit, marginal (on an existing beat)    Rs 220.00 Rs 220.00   [MODEL] Rs130 labour + Rs90 travel
Field visit, standalone trip                   Rs 370.00 Rs 370.00   [MODEL] Rs130 labour + Rs240 travel
Voice-AI, per resolved outcome                   Rs 8.00  Rs 25.00   [PUB] per-outcome India pricing

INSIGHT [MODEL-1]: the spread between a Rs 2 dial and a Rs 370 visit is 185x. Any optimisation
effort spent on automated dial VOLUME is economically trivial; the money is in the four actions
that carry material unit cost AND compliance exposure: HUMAN call, FIELD VISIT, TRACE, LEGAL/NOTICE.
=> PRODUCT SCOPE DECISION: SANKET/SUTRA govern the expensive, reviewable actions. We do NOT compete
   with a dialer on dial volume.

====================================================================================================
S2 — UNIT METRICS: cost per RPC and per productive RPC
====================================================================================================
  automated low    connect=26% rightparty=70% -> cost/RPC Rs 7.42 | cost/productive-RPC @60% pay Rs 12.36
  automated low    connect=31% rightparty=85% -> cost/RPC Rs 5.12 | cost/productive-RPC @60% pay Rs 8.54
  automated high   connect=26% rightparty=70% -> cost/RPC Rs 14.23 | cost/productive-RPC @60% pay Rs 23.72
  automated high   connect=31% rightparty=85% -> cost/RPC Rs 9.83 | cost/productive-RPC @60% pay Rs 16.38
  human call       connect=26% rightparty=70% -> cost/RPC Rs 46.59 | cost/productive-RPC @60% pay Rs 77.66
  human call       connect=31% rightparty=85% -> cost/RPC Rs 32.18 | cost/productive-RPC @60% pay Rs 53.64
  => Range: Rs 6-11 per RPC automated, Rs 33-44 per RPC on a human call [MODEL]

====================================================================================================
S3 — VALUE POOLS (monthly, 100k-account / Rs188 Cr book, 1-30 DPD)
====================================================================================================

VP-1 · DIAL-VOLUME OPTIMISATION  ->  negligible. Deliberately listed first so nobody funds it.

    1 pp of dials avoided =   2,000 dials/mo =   Rs 2,700 -  Rs 5,180 / month [MODEL]
    2 pp of dials avoided =   4,000 dials/mo =   Rs 5,400 - Rs 10,360 / month [MODEL]
    5 pp of dials avoided =  10,000 dials/mo =  Rs 13,500 - Rs 25,900 / month [MODEL]

VP-2 · SCARCE-CAPACITY ARBITRAGE  ->  the largest legitimate pool. Human agent minutes and field
       slots are the real constraint. Reallocating ONE field slot from a low-yield stop to a
       high-yield stop is worth the difference in expected recovery, not the travel cost.
    6,600 field slots/mo; +10-25 pp slot-level success (better address confidence + timing) ->  Rs 9.43 L - Rs 23.57 L / month
    6,600 field slots/mo; +25-45 pp slot-level success (better address confidence + timing) -> Rs 23.57 L - Rs 42.42 L / month
    33,000 human conversations/mo (60 agents x 25/day x 22d [ASSUME]); +5-12 pp RPC on these ->  Rs 5.33 L - Rs 12.80 L / month incremental recovery
    (human calls are reserved for high-value accounts; this is the pool that pays for better targeting)

VP-3 · WASTED EXPENSIVE ACTIONS  ->  real but bounded. Every field visit or trace fired on a wrong
       address / a recycled number is a ~100% loss, not a partial one.
    10% of field slots wasted on wrong-door/low-confidence addresses ->  Rs 1.45 L -  Rs 2.44 L / month
    20% of field slots wasted on wrong-door/low-confidence addresses ->  Rs 2.90 L -  Rs 4.88 L / month
    35% of field slots wasted on wrong-door/low-confidence addresses ->  Rs 5.08 L -  Rs 8.55 L / month
    NOTE: field slots assume a field-bearing portfolio (vehicle/MFI/consumer-durable/ARC).

VP-4 · CONDUCT / COMPLAINT EXPOSURE  ->  the pool a CFO funds without an ROI debate.
    5% of 200,000 dials reach a wrong party; 0.2-1.0% escalate:
      wrong-party exposure = Rs 3.00 L - Rs 75.00 L / month  [MODEL]
    [PUB] FY24 RBI Ombudsman: 85,281 loan/recovery complaints (+42.7% YoY, ~29% of all complaints)
    [PUB] Bajaj Finance fined Rs 2.5 Cr for recovery-agent conduct — the LENDER pays, not the agent

====================================================================================================
S4 — FIELD VISIT & TRACE ROI BY TICKET (the segment-conditional finding)
====================================================================================================
    ticket | visit ROI (marginal) | visit ROI (standalone) |            trace EV (Rs)
------------------------------------------------------------------------------------------
  Rs 5,000 |                0.65x |                  0.38x |    Rs 1.80 -   Rs 54.14 vs fee Rs60-150
 Rs 18,802 |                2.43x |                  1.45x |    Rs 6.79 -  Rs 203.59 vs fee Rs60-150
 Rs 50,000 |                6.47x |                  3.85x |   Rs 18.05 -  Rs 541.41 vs fee Rs60-150
 Rs 1.50 L |               19.42x |                 11.55x |   Rs 54.14 -   Rs 1,624 vs fee Rs60-150
 Rs 8.00 L |              103.59x |                 61.60x |  Rs 288.75 -   Rs 8,663 vs fee Rs60-150

FINDING [MODEL-2]: at the DIGITAL-PL average ticket (Rs 18.8k) a field visit only pays when it is
MARGINAL to an existing beat (2.4x) — as a standalone trip it barely clears 1x. Trace EV spans
Rs 7-204 per case at the average ticket depending on yield and uplift: a ~30x spread. Therefore BOTH actions must be
priced per account, not triggered by a rule or a bucket. Above Rs 1.5 L tickets, visit ROI is 10-100x
and the discipline that matters is ROUTE EFFICIENCY, not whether to visit at all.
=> PRODUCT SCOPE DECISION: SUTRA's confidence gate matters most in the Rs 5k-50k band (where a bad
   visit destroys the ROI) and matters least in vehicle/secured/ARC portfolios (where route
   optimisation dominates). Segment the deployment, do not oversell one story for all portfolios.

====================================================================================================
S5 — SENSITIVITY: which lever buys the most recovery per 1 pp of its own probability
====================================================================================================
  +1 pp connect rate (timing/window/contact point)          Rs 5.01 L / month per pp   (new RPCs x incremental recovery per RPC)
  +1 pp right-party share (identity gate)                   Rs 1.97 L / month per pp   (recovered RPCs + avoided conduct exposure)
  +1 pp P(pay | RPC) (offer/agent/script)                   Rs 7.37 L / month per pp   (Maestro already owns this layer)
  +1 pp field-slot success                                  Rs 94,272 / month per pp   (6,600 slots/mo [ASSUME])
  +1 pp trace yield (new usable point found)                 Rs 1,131 / month per pp   (2,000 traces/mo [ASSUME])

FINDING [MODEL-3]: per percentage point, identity/conduct corrections and field-slot success move
the most money — but they are also the two hardest to move. The CHEAPEST large lever is
P(pay | RPC), which belongs to the OFFER/agent layer (CN's Maestro already owns it).
We should therefore NOT claim that layer. Our defensible claim is the two control levers:
(a) never spend a Rs 220-370 slot or a Rs 60-150 trace on an unverified target, and
(b) never take a compliance-bearing action on an unverified identity. Both are measurable as
    AVOIDED WASTE and AVOIDED EXPOSURE — not as invented recovery uplift.

====================================================================================================
S6 — BREAK-EVEN AT A PRICE (what has to be true for CN to buy this)
====================================================================================================
  [MODEL] one percentage point of connect rate on this book = Rs 5.01 L/month of incremental recovery
  Rs 1/account/month = Rs 1.00 L/mo -> requires +0.20 pp connect (baseline connect 28.5% -> 28.70%); or ~455 avoided field visits/month
  Rs 3/account/month = Rs 3.00 L/mo -> requires +0.60 pp connect (baseline connect 28.5% -> 29.10%); or ~1,364 avoided field visits/month
  Rs 5/account/month = Rs 5.00 L/mo -> requires +1.00 pp connect (baseline connect 28.5% -> 29.50%); or ~2,273 avoided field visits/month

FINDING [MODEL-4]: at Rs 1-5 per account per month the required lift is TINY (a few basis points of
connect rate, or one avoided field visit per ~60 accounts). The product does not need a heroic
claim. It needs a DEMONSTRABLE one: show avoided expensive actions and avoided exposure on real
accounts. That is the single most important design constraint in this whole document.
If we cannot show avoided waste + avoided exposure, the ROI story collapses — no matter how good
the model is.

====================================================================================================
S7 — EXECUTIVE SUMMARY OF THE ECONOMICS
====================================================================================================

  1. The expensive actions are human call (Rs33-44/RPC), field visit (Rs220-370), trace (Rs60-150),
     notice/legal. Those four are the product's scope.
  2. Automated dial-volume optimisation is worth Rs 0.3-7 L/month on a 100k book. Do not pitch it.
  3. Field-visit ROI is ticket-conditional: 0.4x standalone at Rs5k, 2.4x marginal at Rs18.8k,
     60-100x at Rs8L. One story cannot cover all portfolios.
  4. Trace EV spans 30x by account. The only honest way to fire it is per-account EVSI.
  5. Conduct exposure is bounded but real and is the pool a lender funds without argument: see S3
     VP-4 for the band, plus lumpy RBI penalties (Rs 2.5 Cr against Bajaj Finance) that dwarf the
     compensated amounts.
  6. Break-even needs only basis points of improvement. So the deliverable is EVIDENCE OF AVOIDED
     WASTE AND AVOIDED EXPOSURE, not a recovery-uplift claim.

[MODEL END] every figure depends on [ASSUME] inputs that CN must replace with actuals.
```

---

# Appendix C. Companion files

| File | What it is |
|---|---|
| `SANKET_SUTRA_DEMO.html` | Clickable three-beat demo prop (synthetic data, labelled on screen): refusal → release → widening |
| `financial_model.py` | The model script behind Appendix B — editable assumptions, sensitivity sections S1–S7 |
| `CreditNirvana_PS2_PS3_MASTER.md` | This file — the complete deliverable |
| `CreditNirvana_PS2_PS3_Research_and_Strategy.md` / `.docx` | Phase-1 baseline (Appendix A) |
| Individual Phase-2 artifacts | Parts II–XIII, each also readable on its own |
