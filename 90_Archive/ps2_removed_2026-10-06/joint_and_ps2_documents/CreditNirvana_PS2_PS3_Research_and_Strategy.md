# CreditNirvana — PS2 + PS3
## Deep Research & Solution Strategy
### Right-Party Contact Prediction & Skip-Trace Prioritisation (PS2) · Self-Learning Address Geocoder (PS3)

**Prepared for:** CreditNirvana hackathon team
**Date:** 5 October 2026
**Status:** Research-backed strategy, pre-implementation (no code written)

**How to read this document.** Section 1–5 is what exists today and where it fails. Sections 6–12 are our design. Sections 13–16 are execution. Every non-obvious claim carries a source URL. Where a source is a **vendor blog or marketing page**, it is labelled *[vendor claim]* — treat those as directional industry signal, not evidence. Where a source is **peer-reviewed or a working paper**, it is labelled *[paper]*.

---

# 1. EXECUTIVE SUMMARY

## 1.1 What PS2 actually is

**Stated problem:** predict, for each phone number/address, P(Right-Party Contact), then choose the next best action (retry / switch contact point / switch channel / skip-trace / field visit), with skip-trace triggered by *expected economic value*, not attempt count.

**What it actually is, once you read the challenges carefully:** PS2 is **not a classification problem**. It is a *partially observable, sequential, resource-constrained decision problem where the state (is this contact point live and owned by our borrower?) is never directly observed, the actions themselves change the future data, and some state distinctions (avoiding vs invalid vs recycled) are only separable through the *lawfulness of the response function to deliberate probes*.*

Three concrete sub-problems hide inside PS2:

| Sub-problem | Nature | Why it breaks naive ML |
|---|---|---|
| **S1. Latent contact-health inference** | Unsupervised/latent-state inference with action-conditional observations | "Borrower avoiding" and "number dead" both look like "no answer". A classifier trained on "did we contact?" learns the *dialer policy*, not the contact point. |
| **S2. Next-best-action decision policy** | Constrained expected-value optimisation (a decision engine, not a model) | Highest-probability dial ≠ highest-value dial. Cost, compliance, fatigue and information value all differ per action. |
| **S3. Learning under feedback loops** | Off-policy / exploration problem | Only high-scored contacts get called, so low-scored contacts never generate labels → the model cannot learn it was wrong. |

The literature has solved pieces of S1 and S2 (Sánchez et al. 2022 for contact prediction; van de Geer et al. 2018 for marginal-value call scheduling), but **essentially nobody has published S1 at the contact-point level with an explicit right-party-identity head**, and nobody treats **skip-trace as a value-of-information purchase**.

## 1.2 What PS3 actually is

**Stated problem:** geocode descriptive Indian addresses, learn from field visits, output lat/lon + confidence radius + landmark directions, keep learning.

**What it actually is:** a **multi-source evidence fusion and ranking problem with a label-integrity problem on top**.

- The text is low-information ("behind Hanuman temple", "2nd cross"). The *evidence* is in the GPS of past visits — but that GPS is **biased, not just noisy** (Amazon Last Mile states plainly that "centroids and other center-finding methods do not serve well, because the noise is consistently biased" — see [Forman, ECML PKDD 2021](https://mlanthology.org/ecmlpkdd/2021/forman2021ecmlpkdd-getting/) *[paper]*).
- The GPS may be the *right* GPS for the *wrong* reason: borrower met at a shop, workplace, road junction, or a neighbour's gate.
- And the GPS can be **fabricated** (fake check-ins), which poisons labels — a problem the e-commerce geocoding literature does not face in the same way, because a delivery is validated by a parcel.

So PS3 = (a) parse & normalise messy multilingual addresses, (b) generate location candidates, (c) **rank candidates using field evidence with reliability weighting**, (d) classify *what kind of place the GPS is* (home/work/shop/road), (e) produce a **calibrated radius**, not a fake-precise point, and (f) run the whole thing **offline**.

## 1.3 Which is more feasible?

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

## 1.4 Which has greater hackathon potential?

**PS2 alone** demos as a dashboard of numbers — hard to make a judge *feel* it.
**PS3 alone** demos as a map — instantly legible, but risks looking like "an open-source geocoder with extra steps".
**PS2 + PS3 combined** gives the one demo nobody else will have: *click "send this address to field verification" → the field agent's GPS comes back → the address's confidence radius shrinks from 1,400 m to 90 m → the account's field-visit expected value flips positive → the decision engine changes tomorrow's action from "call again" to "visit with these landmark directions".*

That single loop is the pitch. It is also the only part of the design that is genuinely defensible as original.

---

# 2. PS2 — EXISTING RESEARCH

## 2.1 Important papers

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

## 2.2 Industry approaches

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

## 2.3 Open-source projects for PS2

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

## 2.4 Relevant datasets for PS2

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

## 2.5 Best modelling approaches — the honest comparison (PS2)

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

### Recommended combination (the short answer)

> **Contact-health factorisation on GBMs + a hazard/competing-risks head for decay + graph features + calibration + a constrained EV decision engine + a bandit exploration layer. Sequence models only as a later auxiliary embedding. Uplift only once randomised logs exist.**

That is: **GBM (workhorse) × survival (state & decay) × graph (relationship) × EV engine (decision) × bandit (exploration)**. Not "pick one".

## 2.6 Important technical insights from the PS2 research

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

# 3. PS3 — EXISTING RESEARCH

## 3.1 Important papers

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

## 3.2 Industry approaches to Indian / unstructured geocoding

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

## 3.3 Open-source projects for PS3

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

## 3.4 Datasets for PS3

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

## 3.5 Best modelling approaches (PS3)

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

### Recommended combination (the short answer)

> **Parse (libpostal + deepparse + IndicXlit) → Normalise & alias (learned landmark gazetteer + India-tuned phonetic matching) → Generate candidates (commercial geocoder + OSM POIs + H3 classifier + embedding kNN) → Classify place-purpose (stay-time + POI semantic zones) → Rank with learning-to-rank over text+GPS+map-layer features → Estimate a robust location (weighted M-estimator, not a mean) → Emit a GeoConformal radius + landmark directions → Feed successful visits back as labels (with integrity weighting).**

## 3.6 Important technical insights from the PS3 research

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

# 4. COMPETITOR / EXISTING SOLUTION ANALYSIS

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

# 5. RESEARCH GAP — what existing approaches fail to solve well

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

# 6. OUR PROPOSED SOLUTION

## 6.1 Name and one-line thesis

**SANKET + SUTRA** *(working names — SANKET = "signal", for the contact-health & decision engine; SUTRA = "thread", for the address-to-place resolver)*

> **Thesis:** CreditNirvana's unifying asset is not phone numbers and not addresses — it is the **field-visit event**, which is simultaneously *a recovery action, a ground-truth location label, and a contact-health probe*. We build the first system that treats it as all three at once, closing a loop nobody closes: **better geocoding → higher visit success → more trusted labels → better geocoding**, while the same loop **feeds contact health back into the call/trace decision**.

## 6.2 The three-layer conceptual model

### Layer A — Contact-Point Health as a three-factor decomposition (our core idea)

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

### Layer B — Location truth as calibrated evidence, not a coordinate (SUTRA)

For each address *a*, produce a **location belief**, not a point:

```
Belief(a) = ( centroid_μ(a), radius_r(a) at coverage 1−α, purpose_distribution, evidence_ledger )
```

where the evidence ledger records, per observation, *who* observed it, *how* (attested GPS / agent-entered / geocoder), *what kind of place* it was (home / work / shop / road / gate / other), *what happened* (met borrower / met family / no one / refused), and a **credibility weight**. The centroid is a **credibility-weighted robust estimator**, and the radius is a **geographically-weighted conformal quantile** (GeoConformal, G16) so that it carries an actual coverage guarantee.

### Layer C — The decision engine: constrained expected value over an action lattice

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

## 6.3 End-to-end architecture (the pipeline, sharpened)

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

## 6.4 The Contact-Truth Loop (the part that makes this ours)

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

## 6.5 A detail that turns out to matter enormously: the "mover" latent factor

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

# 7. WHY OUR SOLUTION IS DIFFERENT

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

# 8. DATA STRATEGY

## 8.1 CN data we need — the minimum viable schema

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

## 8.2 Public datasets — the concrete prototype stack

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

## 8.3 Labels — and how to get them honestly

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

## 8.4 Synthetic fallback — because CN sandbox data may not arrive in time

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

## 8.5 Feature engineering — the concrete lists

### PS2 features (per candidate contact point, as-of decision time)

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

### PS3 features

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

# 9. MODEL STRATEGY

## 9.1 Baseline → Strong MVP → Advanced

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

## 9.2 How to handle missing / unobserved contact outcomes

This is the most under-discussed problem in the field, and the one most likely to be probed in Q&A. Five parts:

1. **Never treat "untested" as "failed".** Encode it as **censoring**. A survival model trained with `(T = time since last activity or ∞, E = 1 if answered else 0)` handles "we never tried" correctly — letting us score the never-dialled tail of the portfolio.
2. **Train on attempt-level, not account-level, rows.** Each dial is a row; the label is what that dial produced. A "failed" contact point becomes a *sequence of censored observations*, not a permanent negative.
3. **Correct policy-induced selection with propensity weighting.** Log `p(action chosen | context)` at decision time and weight training rows by `1/p` (or use doubly-robust estimation) so under-sampled regions of the action space are not invisible. This is standard off-policy machinery from the bandit literature (Open Bandit Pipeline, Vowpal Wabbit) that collections practice ignores.
4. **Keep a small randomised audit stream.** 1–3% of decisions are replaced with a uniformly random **permissible** action for measurement only — never legal escalation, never a disclosure-capable action on an unverified number. This is the only way to obtain unbiased Qini/uplift estimates and unbiased calibration in the low-score region.
5. **Exploit structurally policy-independent labels.** Field-visit outcomes, **inbound calls**, self-cures (payment with no contact), and voluntary callbacks are *not caused by our dialing policy*. They are gold for evaluating and correcting the model. Hunting for inbound-call events is a day-1 task with very high payoff.

## 9.3 How to distinguish avoiding vs invalid vs recycled vs temporarily unreachable

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

## 9.4 Detecting suspicious / recycled contact points (PS2) and suspicious GPS visits (PS3)

### PS2 — suspicious & recycled contact points

| Detector | Signal | Implementation |
|---|---|---|
| **Regulatory-shape detector** | silence ≥ 90 days, then answering | binary + days-since-last-activity; grounded in the TRAI/DoT 90-day reallocation floor |
| **Behavioural discontinuity** | answer-hour profile shift; talk-duration shift; AMD-profile shift | Jensen–Shannon / KS divergence between pre-gap and post-gap windows; [P17]-style temporal-pattern encoder in production |
| **Identity conflict** | same number on accounts with different borrower names / DOBs / localities; agent "wrong number" marks; "who is this" phrasing | cross-account join + transcript NER; confidence-weighted vote |
| **Geographic inconsistency** | number's registered circle / observed region vs. the address locality | telecom-circle join (or coarse GeoLite); mismatch raises both recycling and "moved" suspicion |
| **Velocity / abuse patterns** | one number answering many different accounts (shop phone, gatekeeper, callback farm) | per-number outcome entropy; distinct-account answer count; answer-rate anomaly vs. carrier/prefix baseline |
| **Port / HLR signals** | ported flag, MCC/MNC change, line-type change | purchased lookup (Telnyx/Twilio/ClearoutPhone) as features |
| **Honeypot / decoy logic** | ≥90-day rule + discontinuity + identity conflict jointly triggered | **Identity Gate**: if recycled-risk > τ, only a no-debt identity challenge is legal, and the contact point is queued for correction (**DPDP §8(3) accuracy duty**) |

### PS3 — suspicious GPS check-ins (the anti-label-poisoning layer)

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

## 9.5 How to model contact decay over time

Three layers, cheap → principled:

1. **Empirical decay curve (day 1).** Compute `P(answer | days_since_last_contact)` and `P(RPC | days_since_last_RPC)`, segmented by source-age bucket. Reproduce the published shape — fresh (0–7 d) ≈ 25%, warm (7–30 d) ≈ 16%, aged (30–90 d) ≈ 11%, cold ≈ 7% `[vendor claim]` ([Plura](https://www.plura.ai/articles/reduce-cost-contact-predictive-dialing-debt-collection-optimization)). This alone justifies re-ordering the dialing queue.
2. **Survival / hazard model (MVP).** Let `T` = time from last observed activity to the next successful right-party contact, right-censored when not yet observed. Covariates = contact-point features + time-varying features (attempts since, channel mix since, seasonality). Outputs `S(t)` (probability of no RPC by *t*) and hazard `h(t)`. This gives:
   - **Retest scheduling:** pick `t*` maximising `h(t) · V − c`. Never spend an attempt where the hazard is near zero (e.g. immediately after a rejection).
   - **Backoff policies:** a *rising* hazard after a gap implies that for some states (avoiders) **strategic silence beats persistence** — counterintuitive, and a great demo moment.
3. **Competing risks + time-varying covariates (production).** Extend to `{RPC, wrong-party answer, network death, continued silence}` with monotone constraints (attempts → hazard up; days-silent → network-death hazard up).

**Cadence:** nightly recalibration, weekly full retrain, with drift monitoring on the hazard baseline (the CDR fraud study's temporal-degradation warning applies directly).

## 9.6 How to calculate expected economic value of call / switch / visit / trace

Full treatment in §10. Summary of the four formulas:

- **Call:** `ENRC_call = A · R · [ P_ptp · P_keep · V · β + (1−P_ptp) · E[V_soft] ] − c_call − λ_f · fatigue − λ_c · q · C_compliance`
- **Switch contact point:** `ENRC_switch = ENRC_call(j') − ENRC_call(j) − c_switch − λ_d · Δ(quality)`
- **Field visit:** `ENRC_visit = p_home(a,τ) · [P_ptp|visit · P_keep · V · β + E[V_soft_visit]] − c_visit − c_travel_marginal − p_wrongdoor · C_compliance + VoI_geo · η`
- **Skip-trace (EVSI):** `ENRC_trace ≈ π_t · k_t · ΔRPC_per_point · p_recovery · V · β − c_trace(t)`

**Two subtleties that make ours better than a naive EV:**
- **Visit economics are route-level, not account-level.** The marginal cost of a visit depends on whether the agent is already going to that locality. So we solve a **VRP with time windows** and report the *marginal* ENRC of adding this stop. This is UrbanFlow-style geospatial optimisation — and it explains why **FRS-DRL cut field visits by 16.3% while improving collections by 20.34%** ([P7]): the visits were being spent badly, not too seldomly.
- **`C_compliance` is real money.** A wrong-door visit is an RBI/DPDP exposure. So a low-confidence geocode reduces visit EV through both the success term and a risk term — which is why PS3 creates value for PS2 *even before* it improves recovery.

## 9.7 How to prevent the model from starving low-scored contacts of exploration

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

## 9.8 How to calibrate the probability

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

## 9.9 Which metrics to use

Full tables in §12. Headline set:

**Model:** PR-AUC (not ROC-AUC — low base rates), Brier, ECE + reliability diagrams **per segment**, Recall@k / Precision@k at the operational budget, NDCG@k for contact-point ranking within an account, C-index + IPCW Brier for the survival head, **Qini / AUUC / uplift@k** where randomisation exists, and **decision regret** (how far the chosen action's ENRC is from the best achievable).

**Business:** ₹ recovered per agent-hour, cost per RPC, RPC rate, PTP rate, PTP-kept rate, attempts per resolution, skip-trace ROI, field-visit success rate, visits per recovery, % of portfolio with a valid contact point, days-to-first-RPC.

**Guardrails:** wrong-party contact rate, third-party disclosure incidents (**0**), contacts outside 08:00–19:00 (**0**), DND violations (**0**), complaints per 10k contacts, attempt-cap breaches, recycling-detection precision.

---

# 10. DECISION ENGINE

## 10.1 The principle

> The model does not decide. The model produces **probability distributions over outcomes for each candidate action**; the decision engine converts them into **money**, filters by **law**, prices **uncertainty** and **information**, and picks the argmax — then writes a signed record explaining exactly why.

This is the REVIO pattern the team already owns, extended three ways: (i) actions are multi-dimensional (not call/no-call), (ii) the **null action has option value**, (iii) **information is a costed good** (probes and traces are purchases, not reflexes).

## 10.2 Notation

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

## 10.3 The core formula: Expected Net Recovery Contribution (ENRC)

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

## 10.4 The other three actions

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

## 10.5 Uncertainty, information and the option value of waiting

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

## 10.6 Hard constraints — implemented as candidate-set construction

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

## 10.7 Exploration layer

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

## 10.8 The audit record (REVIO lineage, extended)

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

# 11. SYSTEM ARCHITECTURE

## 11.1 Component map

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

## 11.2 Data → ML → decision → app → feedback

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

## 11.3 Offline strategy for the field application (the part most teams get wrong)

Field agents in Indian tier-2/3 towns lose connectivity. Design:

1. **Bundle the index, not the service.** Ship a compact H3-indexed pack per operating district: predicted lat/lon + radius + landmark directions + pincode/village polygons + a small locality↔landmark gazetteer for fuzzy on-device search. Target < 100 MB per district.
2. **On-device search:** SQLite + R*Tree for spatial queries; a precomputed phonetic-key table so a misspelt landmark still resolves offline.
3. **Offline direction generation:** templates + the bundled landmark list. No LLM call, no network.
4. **Write-ahead capture:** GPS trail, dwell and outcome queued locally *with device attestation at the moment of the visit* — this is what makes the integrity model possible at all.
5. **Delta sync:** on reconnect, upload new observations and download only the updated packs for addresses the agent will visit.
6. **Graceful degradation:** if a pack is stale, the app marks the radius as *stale* and widens it explicitly rather than showing an over-confident pin. Trust is a feature.

---

# 12. EVALUATION

## 12.1 Model metrics

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

## 12.2 Business metrics

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

## 12.3 Compliance / guardrail metrics (reported on the same dashboard — non-negotiable)

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

## 12.4 The evaluation protocol (how we avoid fooling ourselves)

1. **Strict temporal split.** Train on `t < T`; validate `T … T+14d`; test `T+14d … T+28d`. **Never random-split** — the problem is temporal, and random splits leak the future into the past.
2. **Point-in-time features only**, enforced by the feature store's `as_of` semantics. Any feature knowable only after the decision is banned. (This is the #1 way hackathon models "win" and real models die.)
3. **Propensity-weighted metrics** wherever data is policy-selected; report both weighted and unweighted so the bias is visible.
4. **Segment reporting, always:** metro vs tier-2/3, language, channel, source-age band, account-value band. A model that wins on average and loses in tier-3 is a liability for CreditNirvana.
5. **Policy-level offline evaluation** via IPS/DR over logged decisions, plus a **counterfactual simulation** on the synthetic generator whose ground truth we hold. This is how we claim an improvement number before deployment — honestly.
6. **Shadow-mode deployment:** run the new policy alongside the incumbent for a week, logging would-be decisions only, then compare.
7. **A one-page model card per model:** intended use, prohibited use, calibration, segment performance, retraining cadence, owner.

---

# 13. DEMO STRATEGY (2–3 MINUTES)

## 13.1 The single sentence the judges must remember

> **"We made the field visit do two jobs at once: it collects money *and* it teaches the geocoder — so every rupee of field budget buys a better map, and every better map makes the next rupee of field budget buy more money."**

## 13.2 Storyboard (timed)

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

## 13.3 Design rules for the demo

- **One account, one screen, one decision at a time.** No scrolling dashboards in the first 90 seconds.
- **Every claim on screen has a number next to it** (radius in metres, ENRC in ₹, EVSI vs. trace cost, p_wrongdoor). Judges reward specificity; vague AI-talk loses.
- **Show a refusal.** The blocked visit and the rejected trace are more persuasive than any positive recommendation, because they prove the engine computes economics rather than producing enthusiasm.
- **Never fake the hard parts.** The synthetic generator, the integrity model and the conformal coverage test are all real code with real outputs; the demo is a rehearsal environment, not a mock.
- **Keep a pre-recorded 3-minute fallback** in case the venue's network dies.

## 13.4 The 5 questions we must be able to answer instantly (rehearse these)

1. **"How do you know the label is right?"** → Three-factor decomposition; payment/inbound calls are the gold-standard label; refunded attempt-level censoring; propensity weighting.
2. **"What if CN has no field data yet?"** → The synthetic CN generator with the identical schema, plus the OSM/pincode/Geolife prototype stack; swap-in is a config change.
3. **"Isn't this just geocoding + a call model?"** → No — the coupling *is* the contribution (D4/D5), plus the calibration guarantee (D7) and the compliance-by-construction design (D8).
4. **"Why will agents trust it?"** → Reason codes, the identity gate, offline operation, a visible radius instead of a false-precision pin, and no-disclosure scripts that protect them personally.
5. **"What's the ROI?"** → Fewer wasted visits (radius-driven), trace only when EVSI is positive, and better attempt timing — anchored to published results (fewer resources, more recovery) and stated as *our* measurable targets, not promises.

---

# 14. HACKATHON MVP — MUST / SHOULD / NICE

## 14.1 MUST (if we only ship this, we still win)

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

## 14.2 SHOULD (the difference between "good" and "wins")

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

## 14.3 NICE (production roadmap, described in the pitch — not built at the event)

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

## 14.4 Team split (4 people, 48 hours)

| Person | Owns | Interface contract |
|---|---|---|
| **A — Data & sim** | M1 generator, feature pipelines, feature store `as_of` logic, MLflow | Emits frozen parquet + feature views |
| **B — PS2 models** | M2 heads, S1 hazard, S2 recycled head, S4 exploration, calibration | Emits `/score` JSON: `{A, R, P_ptp, q, hazard}` per contact point |
| **C — PS3 models** | M6 parsing/gazetteer/candidates, S3 integrity, conformal radius, directions | Emits `/geocode` JSON: `{lat, lon, radius@90, purpose, directions, evidence[]}` |
| **D — Decision + app** | M4 engine, M5 EVSI, M8 audit, M9 API/Compose, S6 offline PWA, S7 dashboard | Consumes `/score` + `/geocode`; owns the demo script |

**Hard rules for the 48 hours:** freeze the two API contracts by hour 4; every component must run against the *synthetic* data by hour 24; no model retraining after hour 40 (only parameter tuning); the demo runs from a **clean checkout** at hour 47.

---

# 15. EXECUTION PLAN

## 15.1 The compressed hackathon plan (48–72 hours, the recommended option)

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

## 15.2 The full 14-day plan (if this is being built for real, with real CN data)

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

# 16. FINAL RECOMMENDATION

## 16.1 The verdict, stated plainly

| Question | Answer |
|---|---|
| Which is more **feasible**? | **PS2.** Labels (RPC events, dispositions, telemetry) already exist; a competent MVP is 3–5 days; the decision-engine pattern is one the team has already built (REVIO). |
| Which has more **differentiation headroom**? | **PS3.** Commercial geocoders are all locality-centroid-grade on Indian addresses; nobody ships calibrated radii or learns from field GPS with integrity weighting; the visuals are superior. But it carries higher model risk and a heavier data dependency. |
| Which has more **hackathon potential**? | **PS3 for the "wow", PS2 for the "so what". Build both — but sequence them so PS2 is never at risk.** |
| **What do we build?** | **PS2 + PS3 as one system**, because PS3's **labels are produced by PS2's actions** and PS2's **best action depends on PS3's uncertainty**. Building one is building half a system; building both is building a flywheel. |

## 16.2 Why the combination is not just additive

1. **Label dependency (mechanical):** field visits are one of PS2's actions and PS3's only high-quality label source. Separately, PS2 never learns to value visits for information, and PS3 never receives the visits it needs.
2. **Decision dependency (economic):** the PS3 confidence radius enters the PS2 visit-EV formula twice — through `p_home` and through `p_wrongdoor · C_compliance`. Without PS3, visit decisions are systematically over-confident.
3. **Compliance dependency (legal):** fewer wrong-door visits means fewer third-party exposures. PS3 is a compliance instrument, not just a mapping utility.
4. **Shared latent variable (statistical):** "the borrower moved" drives both phone-recycling symptoms and address staleness (§6.5). The joint factor is more predictive than either head alone.
5. **Novelty (competitive):** every competitor we surveyed solves one half. G-6 (contact intelligence ∥ location intelligence) is the gap, and the combination is the moat.

## 16.3 The exact approach to build (one paragraph)

Build **SANKET** (PS2) as three calibrated LightGBM heads — `P(Answer)`, `P(RightParty | Answer)`, `P(Productive | RPC)` — plus a **competing-risks survival head** for contact decay, plus a hand-built **contact-point graph feature block** (shared numbers, neighbour RPC rate), all calibrated per segment with isotonic regression under a strict temporal split with point-in-time features and propensity logging. Build **SUTRA** (PS3) as a **parse → normalise/alias → generate candidates → rank (LightGBM LTR over text + GPS + OSM/POI + boundary features) → robust weighted estimate → conformal radius → landmark directions** pipeline, with an **integrity model** weighting every field observation. Join them with a **constrained expected-value decision engine** that enumerates actions (call / message / switch contact point / field visit / skip-trace / wait / suppress), filters them by law (08:00–19:00, attempt caps, DND, DPDP purpose, and an **identity gate requiring `P(RightParty) ≥ τ` before any debt-disclosing action**), prices each candidate by **ENRC** — with skip-trace as **EVSI** and the visit's geo-uncertainty as both a success penalty and an information bonus — solves the day's **visit route** with OR-Tools for true marginal costs, adds a **budgeted, VoI-directed exploration layer** with 3% ε-floor and propensity logging, then writes an immutable **audit record** with reason codes and SHAP evidence. Everything runs on a **CN-shaped synthetic generator** (schema-identical, so real data is a config change), served by **FastAPI**, visualised in a **React/TypeScript** agent console, field PWA (offline-first with bundled H3/pincode packs) and manager dashboard, tracked in **MLflow**, instrumented with model, business and compliance metrics, and evaluated with **strict temporal splits, conformal coverage checks, decision regret, and off-policy evaluation** before any policy is promoted.

## 16.4 What we explicitly do **not** do (and why)

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

## 16.5 Success criteria for the build (how we will know it worked)

**Hackathon:** the 3-minute demo runs clean twice; the loop act works live; a judge can ask "why this action?" and get an audit record; the blocked visit and the rejected trace are shown as evidence of economics, not enthusiasm.

**Pilot (30 days, one portfolio, one city):** radius median at 90% coverage < 300 m in urban areas and shrinking week over week; coverage within ±2 pp; visit-success lift ≥ 15% relative; cost per RPC down ≥ 10%; zero compliance breaches; skip-trace spend reallocated with measurable ROI; decision regret decreasing; the exploration stream's cost-per-RPC within 2× of exploitation (i.e. starvation is being cured cheaply).

**Production (2 quarters):** contactability coverage of the book up; ₹ recovered per agent-hour up with the same headcount; trace spend down while recovery holds; field-visit count down while collections hold or improve — the FRS-DRL shape (fewer visits, more recovery), reproduced on CN's own data.

---

# RECOMMENDED SOLUTION TO BUILD

## Architecture in one picture

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

## Why this is the best thing for this team to build

1. **It is the only design that uses CreditNirvana's actual differentiator.** CN's field visits are a proprietary, hard-to-copy data asset. Every competitor's geocoder gets better by *buying* data; CN's gets better by *working*. This design converts an operating cost into a compounding data asset — and it is defensible precisely because it cannot be copied without the field force.
2. **It answers every line of the problem statements, not just the headline.** Decay → survival head. Avoiding vs. invalid → three-factor decomposition + competing risks. Recycling → regulator-shaped detector + identity gate + DPDP correction loop. Unobserved contacts → censoring + propensity weighting + audit stream. Exploration/starvation → VoI bonus + ε-floor + starvation dashboard. Explainability/audit → the audit record schema. Confidence radius → GeoConformal. Offline → bundled packs. Third-party disclosure → structural candidate filtering.
3. **It reuses the team's proven muscles instead of gambling on new ones.** REVIO → the decision engine + audit trail. UrbanFlow AI → H3 spatiotemporal features, geospatial optimisation, large-scale pipelines. Gurgaon real-estate ML → address/geo feature engineering and geocoding failure modes. TubeSignal NLP → multilingual remark/transcript understanding.
4. **It is honestly staged.** A 3-day path exists (generator + two calibrated heads + ENRC engine + radius + demo loop); a 14-day path exists (with real data, hazard head, integrity model, offline app, shadow deployment); and a production path exists (GNN, uplift with holdouts, bandits, learned staleness encoder, address RoBERTa). Each stage is useful on its own — nothing here is a demo-only artefact.
5. **The economics are legible to a non-ML decision-maker.** Field visits that pay for themselves, trace spend that is priced like a purchase, dials deployed when their hazard peaks, zero third-party disclosures, and an audit trail for every rupee-relevant decision. That is a business case, not a model card.
6. **It is differentiated in a way that is checkable.** Every claim in §7 (D1–D11) can be demonstrated live against a system that does the naive thing. Judges do not have to take our word for it — and neither does CreditNirvana.

> **Final line for the pitch:** *Build PS2 + PS3 as one closed loop. PS2 tells CreditNirvana who to reach and when — priced by expected value and gated by identity. PS3 tells it where the borrower actually is — with a radius it can defend. And every field visit makes both of them better, automatically, forever.*
