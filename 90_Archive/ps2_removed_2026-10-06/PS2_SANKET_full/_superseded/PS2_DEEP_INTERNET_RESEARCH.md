# PS2 — DEEP INTERNET RESEARCH

**Phase 1 of the evidence pass. Research only — no architecture is fixed here.**
Companion files: `PS3_DEEP_INTERNET_RESEARCH.md`, `PS2_PS3_RESEARCH_SYNTHESIS.md`, `PS2_ARCHITECTURE_REQUIREMENTS.md`, `PS3_ARCHITECTURE_REQUIREMENTS.md`, `PS2_PS3_SOURCE_BIBLIOGRAPHY.md`.

## 0. Evidence rules used in this file

| Tag | Meaning |
|---|---|
| **[VERIFIED]** | Directly supported by the source cited next to the claim |
| **[INFERENCE]** | Reasonable conclusion drawn from two or more sources |
| **[ASSUMPTION]** | We still have to assume this; stated as such wherever used |
| **[UNKNOWN]** | Insufficient evidence; treated as an open question, never as a fact |

Source hierarchy applied (highest first): regulator/statute → official product/API documentation → peer-reviewed paper → conference/industry paper (ACL/EMNLP/COLING/KDD/INFORMS) → vendor documentation → vendor marketing (labelled *[vendor claim]*) → engineering blog. SEO/AI-generated blog content was excluded from every load-bearing conclusion.

> **Correction carried into this file.** Our Phase-2 brief cited TransUnion Phone Behavior Intelligence as claiming "+33% RPC". The vendor's own current pages state **"increase right-party contacts by about 25% on average"**. The **+33% figure is withdrawn**; the 25% figure is used here and is tagged *[vendor claim]*. [VERIFIED: transunion.com solution page and TransUnion blog]

---

# 1. What PS2 is actually asking (§2 of the brief)

## 1.1 The stated problem, as recorded in our Phase-1 reading

> Predict, for each contact point (phone number, address), the probability of a **right-party contact**; then choose the next best action (retry / switch contact point / change channel / skip-trace / field visit), with skip-trace triggered by **expected economic value**, not by attempt count.

## 1.2 Candidate framings, tested against the literature

| Framing | Where it comes from | Evidence it is *the* problem |
|---|---|---|
| Contactability prediction | Vendor category (TransUnion PBI scores "the likelihood of a number being answered") | Real and commoditised — [VERIFIED: transunion.com TruContact PBI] |
| Right-party-contact prediction | PS2's own wording; collections operator KPI | FICO states RPC rates in collections "rarely exceed 8–10%" and treats best channel/time as the lever — [VERIFIED: fico.com blog "Using AI to Improve Debt Collection"] |
| Identity confidence | Regulatory need (no debt disclosure to third parties) | US analogue exists as a product category: TransUnion *Contact Compliance Risk* "identifies whether a phone number is currently associated with the correct consumer **before outreach occurs**" — [VERIFIED: transunion.com] |
| Contact-point health (live / dead / recycled / shared) | Law + network reality | Number recycling is systemic: FCC Reassigned Numbers Database; ~35M US numbers disconnected/reassigned per year with a 45-day aging period — [VERIFIED: fcc.gov RND FAQ; FCC 18-177 order] |
| Next-best-action (NBA) | Operations practice; vendors | FICO: "real-time prescriptive decisioning — driving best next action" — [VERIFIED: fico.com] |
| Sequential / resource-constrained optimisation | Academic collections literature | Deployed systems exist: constrained MDP at New York State Dept. of Taxation & Finance (Abe et al., KDD 2010) — [VERIFIED: ACM DL abstract] |
| Expected-value / net-recovery optimisation | PS2's explicit "skip-trace triggered by expected economic value" | Matches the decision-theoretic formulation; EVSI machinery for "is it worth buying information" is standard in decision analysis — [VERIFIED: EVSI method review, *Value in Health* 2020] |
| Causal / uplift | Marketing literature, transplanted | Requires treatment variation; **no public randomised debt-collection experiment was found** in this pass — [UNKNOWN] |

**Conclusion [INFERENCE].** PS2 is best framed as: **a constrained sequential decision problem over a partially observable state, where the deliverable is an auditable permission + action decision, and where the two genuine technical difficulties are (a) label validity under policy-induced selection and (b) eligibility as a first-class constraint.** Contactability prediction is one *input* to that; it is not the problem.

## 1.3 Sector evidence — where these systems actually run

| Sector | Real system | What it proves |
|---|---|---|
| Government receivables (tax) | Abe, Melville, Pendus, Reddy et al., **"Optimizing debt collections using constrained reinforcement learning" (KDD 2010)**, deployed at NYS DTF; constraints come from a **rules engine** | The literature's canonical pattern is *optimisation wrapped in hard rules* — exactly the shape PS2 needs — [VERIFIED: ACM DL] |
| Consumer credit (bank) | De Almeida Filho, Mues & Thomas, *Production & Operations Management* 19(6), 2010 — dynamic-programming model of which collection action to use and for how long, with a European bank case study | Action *sequencing* and duration are core, not per-dial accuracy — [VERIFIED: journal abstract] |
| Consumer credit (theory) | Chehrazi, Glynn & Weber, "Dynamic Credit-Collections Optimization", *Management Science* 67(6), 2021 | The field's reference model for dynamic collections — [VERIFIED: INFORMS/repec listing] |
| Debt-collection agency (deployed ML) | van de Geer / Wang / Bhulai (VU Amsterdam): MDP over "which debtor to call", value function approximated with **LightGBM on tabular data**, deployed at an agency. Reported: **4–6% higher collection rate with ~40% fewer calls** (author's own talk abstract); a later peer-reviewed paper cites **21.5% fewer calls** | The single most relevant published deployment for PS2's economics — discipline on expensive actions beats more actions — [VERIFIED: PyData Amsterdam talk abstract; Springer *J. Big Data* 2025 review citing the same work] |
| Microlending (China) | Yang, Lu, Li & Lu, "When Less Is More? Deep RL-Based Optimization of Debt Collection" (SSRN 4488673, 2023): loan-level optimisation uses **fewer** "harsh" actions and yields higher recovery than the incumbent sequence | Supports the "less contact, better targeted" thesis — [VERIFIED: SSRN abstract] |
| Collections decision support | Lappas & Xanthopoulos, *Finance Research Open* 2(2), 2026: rules → prediction (best day/time/channel) → multi-criteria optimisation | The published pattern for **auditable** decision support — [VERIFIED: journal] |
| US collections practice | FICO: treatment optimisation framed as *whom to treat / how to treat / how to balance workload*, with explicit notes on over-contacting and 90-second verification calls costing money | Practitioner confirmation that the cost of the *wrong* action, not model AUC, is the operating issue — [VERIFIED: fico.com blog] |
| Telecom / insurance / government (other than tax) | Not found in this pass | [UNKNOWN] — do not claim sector coverage we have not evidenced |

---

# 2. Existing approaches to contact intelligence (§3 of the brief)

## 2.1 What is already commoditised

| Capability | Who sells it | Evidence |
|---|---|---|
| Number-level "will it be answered" scoring | **TransUnion TruContact Phone Behavior Intelligence** | "scores the quality of each number according to the likelihood of it being answered"; claims ~25% RPC improvement on average; sources include carrier relationships; refreshed data — [VERIFIED: transunion.com, vendor claim on the effect size] |
| Pre-outreach identity / reassignment checking | **TransUnion Contact Compliance Risk** | "identifying whether a phone number is currently associated with the correct consumer before outreach occurs"; monitors reassigned/disconnected/invalid numbers — [VERIFIED: transunion.com] |
| Carrier/line intelligence via API | **Twilio Lookup** (and equivalents) | Line Type Intelligence **$0.008/request**, Line Status **$0.007**, Identity Match **$0.10**, SMS-pumping risk $0.025; formatting/validation free — [VERIFIED: twilio.com pricing + docs] |
| Best time / channel selection | FICO, CR Software, Spocto, Credgenics, dialer vendors | FICO: "AI can help … finding the best channel and time to contact each customer" — [VERIFIED, vendor claim] |
| Contactability + agentic next-best-action in India | **Spocto X (Yubi)** | Company states it is building AI agents that "decide the next best action and execute it across tools and channels … with clear logs for review" — [VERIFIED: ETBFSI 19 Jan 2026 interview] |
| Voice AI at scale in Indian collections | **Skit.ai**, Gnani, Rezo | Skit India page reports portfolio-level outcomes (₹600 Cr collections; 82% liquidation rate; 86% resolution) — [VERIFIED as *vendor claim*] |
| Geo-tagged field collection with offline app | **Credgenics CG Collect**, **Mobicule** | Credgenics: "real-time geo-tracking and geo-fencing of agent locations", "offline functionality" — [VERIFIED: credgenics.com blog + G2 profile] |

## 2.2 What is genuinely difficult

1. **Identity confidence in India has no authoritative linkage rail.** The US has an FCC-mandated Reassigned Numbers Database (300M+ numbers) with a statutory safe harbour. **No equivalent Indian database was found** — [UNKNOWN / likely absent]. Consequence: an identity gate in India must be built from *behavioural* evidence (who answered, what was said, what verified) rather than from an authoritative reassignment lookup.
2. **Policy-induced selection makes the training sample a record of the old policy, not of contact health.** Only points the old system chose get called; low-scored points never generate labels. Formal treatment: *batch learning from logged bandit feedback* — the logged data is "both biased … and incomplete" (Swaminathan & Joachims, JMLR 16, 2015) — [VERIFIED].
3. **"No answer" is not a label.** Avoiding / dead / recycled / shared are observationally similar; separating them requires either probes (RBI-constrained) or cross-account evidence.
4. **Incremental value of an action is unidentifiable without variation.** Uplift/CATE methods (CausalML — arXiv 2002.11631; EconML) assume treatment variation; collections CRM data typically has none for the actions of interest.
5. **Eligibility is a product-level problem, not a model-level one.** Nothing in the contact-intelligence market sells "this action is *permitted* for this contact point"; compliance is implemented as *during-call* checks (US TCPA-style) rather than as candidate-set construction — [INFERENCE from TransUnion/Spocto material].

## 2.3 What a hackathon team can realistically implement

| Component | Feasibility | Why |
|---|---|---|
| Deterministic rules floor (hours, DNC, suppression, identity preconditions) | **High** | Pure config + tests; no data needed |
| Point-level feature + gradient-boosted model with isotonic calibration | **High** | Tabular, small data volumes per portfolio; the deployed literature uses LightGBM for exactly this (van de Geer) |
| Propensity/censoring correction (IPW with clipping) | **Medium** | Needs the incumbent policy's attempt logs; implementable but only if CN logs them |
| EV / net-recovery decision engine with an explicit `wait` | **High** | Arithmetic over a cost table + calibrated probabilities; the decision layer of the published systems |
| Identity linkage of *own* records (dedupe/link) | **Medium–High** | Splink (Fellegi-Sunter, MIT-licensed, unsupervised, DuckDB/Spark backends, documented to link ~1M records per minute on a laptop) — [VERIFIED: splink docs] |
| Caller-side number intelligence at runtime | **High** (paid API) | Twilio-class lookups at $0.007–0.008 per attribute |
| Off-policy evaluation of a new policy | **Medium** | Requires propensities; standard estimators exist (IPS/DR) |
| Live contextual bandit | **Low for this setting** | Exploration costs real borrower contacts and creates conduct risk |

## 2.4 What requires proprietary data that a hackathon team cannot obtain

- **Point-level call outcomes with the incumbent policy's attempt log** (which point, which channel, which window, chosen by what rule).
- **Verified identity events** (OTP/match results), which are usually held by the lender, not the platform.
- **Repayment and roll-back outcomes** for the accounts in question.
- **Complaint/conduct events attributable to specific actions.**
These are exactly the items to request in a sandbox (see `CN_QUESTIONS.md`, items 3–5, 17).

---

# 3. Next-best-action for collections (§4 of the brief)

## 3.1 The six approaches, scored

| Approach | What it needs | Technical strength | Defensibility | Ease | Safety with hackathon data | Explainability | Evidence verdict |
|---|---|---|---|---|---|---|---|
| **A. Predict P(payment \| action)** | Action-level outcome labels, action variation | Medium | Medium — it is a response model, not a policy | Medium | Low (needs variation) | Medium | Industry standard; FICO framing — [VERIFIED as practice] |
| **B. Predict P(success \| customer)** | Account-level features | Low–Medium | High (simple, stable) | **High** | **High** | **High** | Does not answer "which action"; useful as an input, not a decision |
| **C. Incremental effect / uplift** | Randomised or strongly ignorable treatment | **High** (when identifiable) | High *if* a trial exists | High (CausalML/EconML) | **Very low** without randomisation | Low–Medium | No public collections RCT found — [UNKNOWN] |
| **D. Direct policy learning / ranker on logged feedback** | Propensities from the logging policy | Medium–High | Medium (needs OPE) | Medium | Low (propensities usually missing) | Medium | Counterfactual Risk Minimisation / POEM (Swaminathan & Joachims 2015) is the reference; applies directly to logged dialer data — [VERIFIED] |
| **E. Expected-value optimisation with an explicit `wait`/abstain** | Calibrated probabilities + cost table | Medium | **High** — every term is inspectable | **High** | **High** | **High** | Matches the PS wording ("skip-trace by expected economic value") and the EVSI machinery for buying information — [VERIFIED] |
| **F. Contextual bandit / sequential policy (MDP/RL)** | Exploration, propensities, simulation | High | Medium | Low | **Very low** (exploration on real borrowers) | Low | Deployed in the literature *inside a rules engine* (Abe et al. KDD 2010) and in offline/agency settings (van de Geer) — [VERIFIED] |

## 3.2 How the published systems handle the hard parts

| Concern | Published treatment | Source |
|---|---|---|
| Previous actions / state | MDP state includes debtor history; action sequences modelled explicitly | De Almeida Filho et al. 2010; Abe et al. 2010 — [VERIFIED] |
| Action cost | Objective is net benefit, not contact count; agency deployment reports 40% fewer calls for equal/better collection | van de Geer talk abstract — [VERIFIED] |
| Compliance restrictions | Encoded as **constraints** on the optimisation, supplied by a rules engine (e.g., a warrant must precede a levy as a *state* condition) | Abe et al. 2010 — [VERIFIED: "legal requirement … addressed naturally by introduction of states"] |
| Delayed rewards | Standard MDP discounting; some work models settlement probability over time | Chehrazi et al. 2021 — [VERIFIED] |
| Action sequencing / timing | Dynamic programming over "which action and for how long" | De Almeida Filho et al. 2010 — [VERIFIED] |
| Customer state | Latent/behavioural segmentation (e.g., self-cured / lazy payer / delinquent) | Lappas & Xanthopoulos 2026 — [VERIFIED] |

## 3.3 Recommendation from the evidence

**Decision layer = E (expected net recovery with explicit abstain).** Probabilities feed it from **B/A** (point-level connection and identity), calibrated. **C** stays out until a randomised holdout exists. **D** becomes viable only if propensities are logged from now on. **F** is used *offline* (policy evaluation, simulation), never as live exploration over compliant borrowers.

This is not a compromise position: it is the position the deployed literature arrived at, with a rules engine supplying constraints and a learned value function supplying ranking.

---

# 4. Selection bias and feedback loops (§5 of the brief)

## 4.1 The core problem, stated with sources

> "Log data … is both **biased** (predictions favored by the historical algorithm will be over-represented) and **incomplete** (feedback for other predictions will not be available)."
> — Swaminathan & Joachims, *Batch Learning from Logged Bandit Feedback through Counterfactual Risk Minimization*, JMLR 16 (2015) — **[VERIFIED]**

The credit analogue is well documented in a different setting: models trained on accepted applicants only ("reject inference") produce biased scorecards; correction requires explicit bias handling — *Fighting Sampling Bias: A Framework for Training and Evaluating Credit Scoring Models* (arXiv 2407.13009, 2024) — **[VERIFIED]**.

Practitioner confirmation for collections specifically: a propensity model trained only on contacted accounts "reflects existing contact strategy rather than true customer behavior" — *[vendor/practitioner source, treated as corroboration only, not as evidence]*.

## 4.2 Practical remedies, ranked by feasibility for this project

| Remedy | What it fixes | Feasibility | Cost | Notes |
|---|---|---|---|---|
| **1. Log propensities from day one** (the probability the incumbent policy assigned to the action actually taken) | Enables OPE and IPW later; costs nothing at inference | **High** | ~zero | This one line is the highest-value data decision in the whole product |
| **2. Inverse-propensity weighting with clipping** on the training loss | Selection into the labelled set | Medium | Low | Standard; must monitor effective sample size |
| **3. Include the full account population in features, label only the treated** | Partial observability | Medium | Low | Prevents the model learning "only contacted accounts exist" |
| **4. Exploit natural variation in routing thresholds** (queues that switch rules by date/region/team) | A quasi-experiment without touching borrowers | Medium | Low | Must be documented as an assumption; not a true RCT |
| **5. Shadow-mode counterfactual evaluation** (new policy scored on historical data; decisions logged but not executed) | Safest way to demonstrate value to a bank | **High** | Low | Recommended deliverable for the competition |
| **6. Deliberate randomisation** (hold out a small % of contacts) | Real causal identification | Low | High — real borrower harm risk + conduct exposure | Do **not** do this in the MVP; it is a lender decision with legal sign-off |
| **7. Drift monitoring per segment** (PSI, calibration, policy-change log) | Model decay after policy change | High | Low | Required in production |

## 4.3 What we may and may not claim

- **May claim:** "the model is trained with propensity weighting and evaluated by shadow-mode counterfactual simulation."
- **May not claim:** "our model increases recovery by X%" — that requires an experiment we will not have.
- **Must state:** exploration that costs extra contacts is out of scope; any exploration must be *within* attempts already planned.

---

# 5. Economics of collections actions (§6 of the brief)

## 5.1 Cost inputs with sources

| Action | Cost | Source / status |
|---|---|---|
| Number intelligence lookup (line type / line status) | **$0.007–0.008 per attribute** (~₹0.6–0.7) | Twilio Lookup pricing — [VERIFIED] |
| Identity Match lookup | **$0.10 per request** (~₹8.8) | Twilio Lookup pricing — [VERIFIED] |
| Outsourced voice agent hour, India | **$5–14 per agent hour** across several 2026 pricing guides | — [VERIFIED as market listings; treat range as *[INFERENCE]* for India] |
| Voice AI minute (India) | ₹2–12/min headline, effective 2–4× due to connected-minute billing | Phase-2 research, vendor pricing pages — *[vendor claim]* |
| Skip-trace (US market) | **$0.02–0.15 per successful record** (Tracerfy normal $0.02 / advanced $0.04, hits only) | trac erfy.com pricing — [VERIFIED for US; India pricing [UNKNOWN]] |
| Field visit | ₹220 marginal / ₹370 standalone | Our model — **[ASSUMPTION]** |
| Cost of a wrong-party contact | No credible ₹ figure found | **[UNKNOWN] — must not be invented.** Treat as a compliance/reputational exposure plus a compensation-precedent class (RBI ombudsman) |

## 5.2 Metric definitions to use (and to avoid)

**Use:** cost per RPC · cost per *productive* RPC · recovery per agent-hour · recovery per visit · recovery per ₹ spent · **expected net recovery** · **expected value of sample information (EVSI)** for trace purchases.

**Avoid:** "gross recovery per dial" (overstates, since most payers would have paid), "accuracy" as a business metric, "dials saved" (dials are cheap — see §5.3).

## 5.3 Which objective function the evidence supports

1. **Maximise expected net recovery per unit of the scarce resource** (field slots, human hours) — because the cost spread between channels is enormous and dials are effectively free at the margin [INFERENCE from the cost table above].
2. **Subject to hard constraints** — eligibility, hours, suppression, notice-before-visit — i.e., a constrained optimisation, matching Abe et al.'s rules-engine-plus-MDP pattern [VERIFIED].
3. **Where information is purchased, price it:** trace and verification are information purchases; the decision-theoretic tool is EVSI, and it is computable in practice with standard approximations (regression-based / importance-sampling / Gaussian-approximation / moment-matching; implementations published) — [VERIFIED: *Value in Health* 2020 review + ConVOI GitHub].
4. **Do not optimise P(success) alone** — it ignores cost asymmetry and the value of the information the action produces.

---

# 6. Regulatory and compliance constraints (§7 of the brief)

## 6.1 The binding Indian rules (as of this research pass)

| Rule | Detail | Status |
|---|---|---|
| **RBI recovery framework** | Issued **6 August 2026** as nine Amendment Directions (Commercial Banks, SFBs, LABs, RRBs, UCBs, RCBs, AIFIs, NBFCs, HFCs); **effective 1 January 2027**; Press Release 2026-2027/827. Content: contact hours **08:00–19:00** (or as the borrower authorises); **at least one day's prior intimation** before the recovery agent's first visit, with the agency's details; agent must carry ID card, authorisation letter and the notice; lender must publish an up-to-date **list of empanelled recovery agencies** (updated within 7 days); **IIBF Debt Recovery Agent certification** mandatory (transition for existing agents); **bi-directional call recording retained ≥6 months**; board-approved collection/recovery policy; enumerated **harsh practices** (abusive/minatory language, inappropriate messages/social media, excessive or out-of-hours calling, anonymous/threatening calls, contacting relatives/friends/colleagues, disclosure to third parties); device-locking protocol (no locking before 30 DPD, full restriction only after 60 DPD, ₹250/hour compensation for wrongful delay) | [VERIFIED] via RBI-linked summaries and the draft/notification trail (draft 20 May 2026 → final 6 Aug 2026) |
| **RBI Digital Lending Guidelines** | Press release 10 Aug 2022; guidelines 2 Sep 2022. Require disclosure of recovery-mechanism terms and the LSP responsible for recovery in the Key Fact Statement; prohibit access to phone contact lists/call logs; on-device data storage in India; grievance-redressal officer for digital lending | [VERIFIED] |
| **DPDP Act 2023 + DPDP Rules 2025** | Rules notified **13 November 2025** in the Gazette (G.S.R. 843(E) commencement notification). Phased: some provisions immediate, Consent Manager regime at ~12 months (**~Nov 2026**), the substantive data-fiduciary obligations at ~18 months (**~May 2027**) — including security safeguards, breach reporting (72h to the Board), retention and erasure. **Significant Data Fiduciaries** must appoint a DPO, do an annual DPIA, and **ensure algorithmic systems do not violate data principals' rights** | [VERIFIED] |
| **TRAI TCCCPR 2018 + amendment 12 Feb 2025** | DLT registration; **140-series for promotional**, **1600-series for transactional/service** voice; no 10-digit numbers for telemarketing; disclosure of auto-dialer/robocall use; financial disincentive of **₹2 lakh** for first instance of a CLI-based violation; blacklisting and disconnection of telecom resources | [VERIFIED: TRAI Press Release 11/2025; PIB] |
| **RBI Ombudsman exposure** | FY24: **85,281** loan/recovery-related complaints, **+42.7% YoY**, ≈29% of all complaints; RB-IOS compensation for harassment up to ₹3,00,000 (2026 scheme) | [VERIFIED via RBI Annual Report on the Ombudsman Scheme as cited by multiple secondary sources; treat the sub-totals as [VERIFIED] and the scheme caps as [VERIFIED]] |

**Phase discipline:** the RBI Directions are **not yet in force** (they apply from 1 Jan 2027) and the DPDP fiduciary obligations are **not yet in force** (~May 2027). Every deck and document must say "effective 1 January 2027", never "current law".

## 6.2 Hard rules vs probabilistic outputs — the line that must hold

| Decision element | Nature | Why |
|---|---|---|
| Contact window, contact frequency ceilings, DNC/preferences, suppression on hardship/grievance/death, third-party disclosure prohibition, notice-before-visit, agent identity/certification, recording and retention, device-locking thresholds | **Hard deterministic controls** | These are externally specified, auditable, and must not depend on a model score. The regulator asks whether the *system permitted* the conduct |
| P(connect), P(right party), timing, channel preference, expected value, best contact point, information value of a trace | **Probabilistic model outputs** | These are estimates under uncertainty; they inform, they do not authorise |
| The join between the two | **Eligibility filter first, then model ranking** — the model may only rank within the set of actions the rules allow | This is the architecture the literature already uses for constrained collections (Abe et al. 2010) — [VERIFIED] |

## 6.3 Two compliance facts that shape PS2's design

1. **Recording + 6-month retention** means the platform already has a corpus of verified/mismatched identity moments; that is a lawful feature source for an identity model [INFERENCE].
2. **DPDP's algorithmic-rights clause for SDFs** (Rule 13) is the strongest argument that an eligibility gate — not a post-hoc audit — is the right compliance architecture [INFERENCE from the rule text].

---

# 7. Competitors and what CN would value (§8 of the brief)

## 7.1 Competitor capability map (public materials only)

| Player | What they publicly claim | Contact strategy | Field | Identity / contact intelligence | Geospatial | Agentic | Compliance features |
|---|---|---|---|---|---|---|---|
| **CreditNirvana (Perfios)** | "Agentic AI platform that runs collections end to end"; **20 modules**; **80+ dashboards out of the box**; API-first with 50+ pre-built integrations; "Governance & Access: who did what, and who is allowed to"; Maestro embedded | AI-orchestrated outreach across voice/WhatsApp/SMS | Field ops inside Maestro; 32% field-efficiency claim | Predictive analytics (from Perfios press materials) | — (not evidenced publicly) | **Yes** — Maestro, 120+ planned agentic capabilities, 50+ languages | Governance/access control, audit |
| **Perfios (parent)** | FY25 revenue ₹669.5 Cr, PAT ₹104.3 Cr; 1,000+ FIs; owns Karza (KYC), Clari5 (financial crime), IHX | — | — | Identity/KYC rails in-group | — | — | — |
| **Spocto X (Yubi)** | "End-to-end debt collections platform"; agentic AI orchestration; "9 Cr+ accounts prevented from becoming NPA"; "₹50,000 Cr+ ECL saved"; 57% cost reduction claim | Explicit multi-channel NBA agents | Field routing referenced ("route cases across digital, tele-calling and field operations") | Contactability/behavioural scores (Spocto Score, YuCI historically) | — | **Yes**, explicitly | "clear logs for review"; auditability claims |
| **Credgenics** | 400+ behavioural signals (prior claims); CG Collect field app | Multi-channel + dialer | Geo-tracking, geo-fencing, offline, digital receipts, case-study claims (25% agent productivity, 20% fewer field allocations, 5× daily visits) | AI predictor models | Geo-tagging of visits | Partially | Audit trails |
| **Mobicule** | Field collection platform; offline-first; anti-spoof claims | Field-centric | Beat plans, AI planning | — | Geo-fencing | Partially | Geo-tagged proof of visit |
| **Skit.ai / Gnani / Rezo** | Voice AI for collections; India portfolios | Voice-first | — | — | — | Yes (voice agents) | Recording/monitoring |
| **TransUnion** | TruContact suite: PBI (~25% RPC claim), Contact Compliance Risk, Address Behavior Intelligence | Contact ranking | — | **Strongest** | Address BI | No | TCPA-oriented compliance products |
| **Delhivery Maps / Shiprocket** | Geocoding, address standardisation/validation/verification over 4B+ deliveries (Delhivery); delivery-outcome learning (Shiprocket) | — | Delivery | — | **Strongest in India** | LLM-based (GeoNaksha) | — |
| **FICO / Pega-style decisioning** | Treatment optimisation, prescriptive decisioning | Enterprise NBA | — | — | — | Yes | Constraint frameworks |

## 7.2 "CN already has Maestro — why would they care?"

Answering this honestly, from the public evidence, four things are **not** evidenced in CN's public materials and are the only defensible asks:

1. **Action-level permission as a product surface.** CN's published governance claim is about *access* ("who is allowed to" — RBAC/user governance). Nothing public shows **eligibility computed per action from identity/address confidence** — [INFERENCE from absence plus the wording on creditnirvana.ai].
2. **Address confidence as a decision input.** CN publicly markets field operations and legal/notice workflows, but no public material shows an address-confidence object gating the pre-visit notice that the RBI framework requires from 1 Jan 2027 — [INFERENCE].
3. **Measured discipline on expensive actions.** The published evidence that this is worth doing (40% fewer calls at equal/better collection) exists in the literature but no CN material claims it — [INFERENCE].
4. **A regulator-facing decision record.** "Who did what" is not the same as "which rule permitted this action on this account, with which probabilities and which data snapshot" — [INFERENCE].

**We must not claim a market gap.** CN, Spocto, Credgenics and Mobicule all ship overlapping pieces. The defensible position is that **the permission layer is an integration point none of them markets**, and that CN's own regulatory deadline creates the demand.

---

# 8. What this changes for PS2 (hand-off to the requirements file)

1. The **decision layer** is expected-value with constraints, not a classifier. [evidence: §3]
2. The **model inventory should be small** — the deployed literature uses one learned value function plus a rules engine. [evidence: §1.3, §3.2]
3. **Propensity logging is the single most valuable data requirement.** [evidence: §4]
4. **Information purchases (trace/verification) must be priced with EVSI**, not triggered by counts. [evidence: §5.3]
5. **Eligibility must be deterministic and auditable**; models propose, rules permit. [evidence: §6.2]
6. **Do not claim uplift, recovery lift, or sector coverage we cannot evidence.** [evidence: §1.3, §4.3]
