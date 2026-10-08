# CreditNirvana — PS2 + PS3

## Complete deliverable: second-stage research, red team, and the solution we would build

**One-line thesis.** The two problem statements are not about better prediction. They are about **permission** — deciding what a collections platform is allowed to *do* with a prediction. We build a permission layer for the two irreversible actions: **a disclosure-capable contact against an unverified identity** (PS2 → **SANKET**) and **a legally-required notice or visit at an unverified address** (PS3 → **SUTRA**).

**How to read this file.** Part I is the whole answer in 20 numbered conclusions — if you read nothing else, read that. Parts II–XIII are the working artifacts, in the order the work was done (assumptions → market → red team → architectures → novelty → money → data → questions → execution). Appendix A is the Phase-1 baseline research, retained as the research record and explicitly superseded as *design*. Appendix B is the model's raw output; Appendix C lists the companion files.

**Honesty rules applied throughout — please hold us to them:** no invented facts; every number is tagged `[PUB]` (published/claimed by a vendor), `[EXT]` (external data point), `[ASSUME]` (ours) or `[MODEL]` (computed); synthetic data is labelled wherever it appears and is never presented as measured performance; no claim of a market gap without a named competitor; no claim of compliance merely because a log exists; no advanced model without a simpler baseline it had to beat.

---


---

# Part 0. Team handoff — read this before anything else

> Added 6 October 2026. The same content as `START_HERE_TEAM_HANDOFF.md` in the package root: what we are building, what is binding versus history, the five numbers that carry the argument, the workstreams, the demo beats, the claims we never make, and the commands that reproduce every figure.

**CreditNirvana PS2 + PS3 · read this file first, then work from the folders.**

Written 6 October 2026. This is the version to circulate to the team: it says what we're building, what's already decided, who does what, what you must never claim, and where every number comes from.

---

## 1. The idea in 90 seconds

CreditNirvana gave us two problem statements — PS2 (who to call / when to skip-trace) and PS3 (find a messy Indian address and be honest about how sure we are). We researched 24 real systems that solve these problems in production (Experian, FICO, TransUnion, Pega, the New York State tax department, Meesho's GeoIndia, Indian logistics platforms) and then reviewed the official dataset table by table.

**Both problems turn out to be about permission, not prediction.** The prediction layers are already sold by a dozen vendors. What is missing is a system that decides what the platform is *allowed* to do, prices that decision in rupees, and records why it refused.

So we are building one product with two halves:

| Half | PS | What it permits | Name |
|---|---|---|---|
| Identity | PS2 | A **disclosure-capable contact** — a call that reveals a debt to whoever answers | **SANKET** |
| Location | PS3 | A **legally-required notice and a doorstep visit** | **SUTRA** |

**The one-line pitch:** *the irreversible actions are gated on evidence, every refusal is recorded with the rule and the counterfactual value, information (a trace, a visit) is only bought when it can change a decision, and field evidence is integrity-weighted so it cannot be faked into moving the belief.*

**The architecture, in shape:**

```
state → evidence fusion → calibrated uncertainty → policy/permission (with refusal ledger)
      → economics (EV, EVSI, conduct penalty) → capacity allocation → execution
      → event-sourced feedback → back to state
```

Prediction is **one layer inside** this, not the system. If someone asks "what's your model?", the correct answer is "which layer?".

---

## 2. What is binding, what is history

| Where | Status — trust it for |
|---|---|
| `CreditNirvana_PS2_PS3_MASTER.md` | The whole deliverable in one file (Part I = the 20 conclusions; Part XIV = dataset review; Part XV = all of Phase 4). **This is the file to email.** |
| `PS2_SANKET/` · `PS3_SUTRA/` | **BINDING. The two sections, one per problem statement** — each self-contained: its brief, its documents, its `data/raw/`, its `data/derived/` acceptance table, its `tools/`, its `_superseded/` |
| `SIMILAR_SYSTEMS_REVERSE_ENGINEERING.md` · `ARCHITECTURE_DECISION_LOG_FINAL.md` · the two bibliographies · `PS2_PS3_RESEARCH_SYNTHESIS.md` | **BINDING reference.** How 24 real systems are built; the 31 decisions with their reversal conditions; every source; the synthesis |
| `PS2_PS3_DATASET_REVIEW.md` · `tools/dataset_audit.py` · `data/raw/` | **BINDING.** Every dataset number, the acceptance baselines, the 12 traps, the runnable audit |
| The two `*_ARCHITECTURE_REQUIREMENTS.md` files | The MUST / SHOULD / MAY checklists the design had to satisfy |
| The strategy files (`CN_QUESTIONS.md`, `PS2_PS3_RED_TEAM.md`, `NOVELTY_MATRIX.md`, `PS2_PS3_MARKET_RESEARCH.md`, `PS2_PS3_FINANCIAL_MODEL.md`, `PS2_PS3_DATA_STRATEGY.md`, `HACKATHON_EXECUTION_PLAN.md`) | Current: assumptions, competitor map, red team, financial model, **the questions we must ask CreditNirvana** |
| `CreditNirvana_PS2_PS3_Research_and_Strategy.md` | Historical: still the source of most external benchmarks, but its *design* is superseded |
| The two `*_SOLUTION_ARCHITECTURE.md` hypotheses (section roots) and `_superseded/` | **SUPERSEDED as designs.** Kept as the reasoning record and because the demo storyboard is still useful. Do not build from here — build from the two `*_FINAL.md` designs |
| `tools/financial_model.py` (+ output) · `SANKET_SUTRA_DEMO.html` | The financial model and the clickable demo prop |
| `90_Archive/ps1_fake_ptp_not_used/` | Four tables from a third problem statement that neither design uses (outside both sections, by design) |

**Read in this order if you're new:** `HOW_TO_USE_AND_UNDERSTAND_THIS_PACKAGE.md` (the manual, six acts) → Part I below → `SIMILAR_SYSTEMS_REVERSE_ENGINEERING.md` §14 (the 7 patterns) → `README_PS2_SANKET.md` / `README_PS3_SUTRA.md` → the two `*_FINAL.md` designs.

---

## 3. The numbers that carry the argument

Memorise these five. Every one is reproducible from the official dataset with `dataset_audit.py` (see §6).

| # | Fact | Why it matters |
|---|---|---|
| 1 | Refusing only the **third consecutive** dead call to a point raises RPC per call **0.1762 → 0.1872** while removing **12.5%** of calls | We can do *less* and win — and the naive "never call a dead point" rule is **wrong** (points with ≥1 prior dead call are 42.7% of calls but 37.4% of successful contacts) |
| 2 | **77%** of trace spend (₹61,605 of ₹79,650) found nothing, and predicting which trace works is *not learnable* (CV AUC 0.574 vs 0.772 majority) | Kills the "predict the trace" idea; turns the waste into a visible, arithmetic refusal (EVSI: buy only if value of information > ₹104) |
| 3 | Vendor address error is **stratum-dependent by 35×**: median **37.7 m** (rooftop) → **1,336.5 m** (pincode), two independent samples agreeing | The geocoder already tells us its error band and nobody uses it. Calibrated truth is our cheapest, strongest PS3 deliverable |
| 4 | Free data cannot beat **370 m** (our own oracle test); field evidence reaches **29 m** median on visits where the agent met someone (82% under 100 m) | The accuracy engine is the **field visit**, not a better geocoder |
| 5 | **11.6%** of check-ins sit >500 m from their own GPS trail, and one agent has **162/172 duplicate photo hashes** | Without an integrity gate, the learning loop poisons itself. The gate is a feature, not plumbing |

**The honest ceiling we must state out loud:** honest pre-dial model AUC is **0.670** (logistic 0.604). If you add post-dial fields you get 0.933 — that number is **leakage** and must never be quoted as a result. It exists in our decks only as a warning.

---

## 4. What we are building (48 hours)

The frozen `BUILD NOW` list from `FRONTIER_PS2_PS3_ARCHITECTURES.md`:

**PS2 — SANKET:** event log → state machine (`CONTACT_POINT_STATE` with owners, decay, dead-streak) → identity fusion (P(borrower) with an interval) → one calibrated multi-class model (pre-dial features only) → **hard rulebook + refusal ledger** → EV with a published cost table → **EVSI on traces** → day-level allocator (greedy first, MILP if time) → outcomes back into the log.

**PS3 — SUTRA:** parse → retrieve → rank → vendor stratum prior → **integrity gate** → field-evidence fusion (dwell- and outcome-weighted stop detection) → **per-stratum conformal radius** → two contracts to PS2 → **two-confirmation promotion**.

**Integration:** exactly **two** contracts. PS3 → PS2: `P(within 200 m)` + promotions. PS2 → PS3: `visit.completed` + the value of confirmation. One shared event vocabulary. The single genuinely joint decision: **a field visit buys both identity and location information and cannot be undone — neither half can price it alone.**

### Workstreams (map to 3–5 people)

| WS | Owner (fill in) | Scope | Done when |
|---|---|---|---|
| **A. PS2 core** | | State machine, gate, refusal ledger, EV + EVSI | Reproduces fact #1 and fact #2 with a ledger output |
| **B. PS3 core** | | Integrity gate, fusion, radius table, promotion | Reproduces facts #3–#5; radius table with two-sample agreement |
| **C. Integration + allocator** | | The two contracts, joint visit EV, day plan + shadow prices | Changing `P(within 200 m)` visibly re-orders field slots |
| **D. Demo + evidence pack** | | Decision cards, replay, demo script, and checking every claim's tag | Every number on screen traceable to `[DATA]` / `[S-nn]` / `[ASSUMPTION]` |

### Cut-line if we run out of time
A + B ship; C degrades to a ranked list with a published budget cap; D never loses the **refusal ledger** — that is the submission's differentiator. Under no cut do we ship "we called an API".

---

## 5. The demo (8 beats)

1. The incumbent, warts and all — 51,105 calls, a constant trace trigger, ₹79,650 spent, 77% invisible waste.
2. One account's belief timeline — a third-party answer, a trace that kills a point, a payment that resets the state.
3. **A refusal with arithmetic** — we decline a ₹104 trace and a field slot, showing the EVSI computation and the counterfactual range.
4. The day plan — drop field slots 50 → 20 live: the shadow price moves, the plan re-orders, refusals change.
5. The replay — same events, new policy version (this is the argument for 1 Jan 2027 readiness).
6. One address's radius shrinking after an integrity-passing visit.
7. A **faked** check-in being rejected and *widening* the radius instead of moving the belief.
8. The honest slide — leakage 0.933 vs honest 0.670, the confounded arm, the cost table's ranges, what we refuse to claim.

---

## 6. Run things

The workspace is four tiers — `CreditNirvana_Submission/` (the deliverable), `10_Inputs/` (dataset, read-only),
`tools/` (scripts that reproduce and verify), `90_Archive/` (superseded drafts). Full map: `../../WORKSPACE.md`.

```bash
cd PS2_SANKET                   # or: cd PS3_SUTRA — the sibling section, same tooling

# 1. Reproduce every number this section quotes + regenerate its acceptance table
bash tools/reproduce.sh               # PS2 default: q p2 eco   |   PS3 default: q p3 eco
bash tools/reproduce.sh p2 eco        # selected audit sections only (PS3: p3)

# 2. Rebuild this section's zip and refresh the combined zip, then the manifest
bash tools/build_package.sh
python3 tools/build_manifest.py       # -> tools/section_manifest.csv

# 3. Invariant checks — must print ALL CHECKS PASSED before any hand-off
bash tools/check_section.sh

# 4. If this section's tables are ever missing (synthetic, 21 MB in total)
pip install gdown
gdown --folder "https://drive.google.com/drive/folders/18iqIR8TjXDqf9-hgEY34uJr_DraIl_3P" -O /tmp/cn_drive
# → flatten the subfolders into data/raw/*.csv ; ps1_fake_ptp → 90_Archive/ps1_fake_ptp_not_used/

# 5. The clickable demo prop (no server needed)
open SANKET_SUTRA_DEMO.html
```

The audit section meanings: `q` inventory · `p2` PS2 funnel, arm contrast, honest AUC, identity, trace waste ·
`p3` PS3 stratum error, free-data ceiling, integrity · `eco` trace ROI and the waste floor.

**Environment:** Python 3 + `pandas`, `numpy`. Scripts are path-portable (`$CN_DATASET`, `$CN_OUT`). The demo HTML needs no server.

---

## 7. Rules we do not break

**Never claim:**
- an uplift / incremental-effect number — the randomised arm is 5.4% of accounts, confounded, and *worse* than the incumbent (0.134 vs 0.166 RPC). No clean control exists, so no causal claim is licensed.
- a spoof-detection *rate* — we have no device telemetry, so we cannot measure recall.
- a market-size, market-share or "no competitor does X" claim without a named source.
- an accuracy or ROI figure from the synthetic dataset as if it were measured on reality: it is a **mechanism demo**, and the vendor-standard note is that real RPC "rarely exceeds 8–10%" (FICO), while our synthetic data sits at 16.4%.
- any single-point rupee number whose inputs are `[ASSUMPTION]` — every EV prints a **range**.

**Always:**
- tag numbers `[PUB]` / `[EXT]` / `[ASSUME]` / `[MODEL]` and claims `[VERIFIED]` / `[INFERENCE]` / `[ASSUMPTION]` / `[UNKNOWN]`.
- state the failure path of every action (timeout, partial, rejected, fallback, escalation).
- keep regulatory rules **hard and closed-vocabulary** (no fuzzy logic inside a legal gate), and keep policy parameters (thresholds, ceilings, budget) separate and owned.
- label any advanced idea with its class: `BUILD NOW` / `BUILD IF TIME` / `PRODUCTION` / `RESEARCH ONLY`. The 9 RESEARCH ONLY items and the 18 rejected alternatives are in `ARCHITECTURE_DECISION_LOG_FINAL.md` — each with the condition that would reverse it, so nobody has to re-litigate them.

---

## 8. What we still need from CreditNirvana (ask these first)

1. **Real cost and capacity table?** (agent minute, field slot, conduct cost; agent-hours, field slots, trace budget). This is the single biggest upgrade available: it promotes the day-level MILP allocator from *build-if-time* to the centrepiece.
2. **Do they hold visit-level GPS** (per-point accuracy, dwell, outcome) historically? If not, PS3 loses its learner and becomes a gate-and-radius product.
3. **Do they hold point-level call dispositions and the incumbent policy's attempt log?** If not, PS2 cannot benchmark and ships as the identity gate + EV gate.
4. **The real ticket band of the pilot portfolio.** Below roughly ₹13–15k, field actions stop being self-funding.
5. **Which recovery rules will bind at pilot time** — the RBI Amendment Directions take effect **1 Jan 2027** (08:00–19:00, ≥1-day pre-visit notice, ≥6-month recording, empanelled agencies, IIRB-certified agents, device-locking 30/60 days).

Full ranked list (34 questions) in `CN_QUESTIONS.md`.

---

## 9. Reading order by role

| You are | Read |
|---|---|
| **Building PS2** | `PS2_SANKET_SOLUTION_ARCHITECTURE_FINAL.md` (§6–§19, §29) → `PS2_ARCHITECTURE_SELECTION.md` → audit `p2` + `eco` |
| **Building PS3** | `../PS3_SUTRA/PS3_SUTRA_SOLUTION_ARCHITECTURE_FINAL.md` (§6–§13, §29) → `../PS3_SUTRA/PS3_ARCHITECTURE_SELECTION.md` → audit `p3` |
| **Doing the integration / demo** | `SANKET_SUTRA_SYSTEM_ARCHITECTURE_FINAL.md` → `FRONTIER_PS2_PS3_ARCHITECTURES.md` |
| **Presenting it** | `CreditNirvana_PS2_PS3_MASTER.md` Part I → `HOW_TO_USE_AND_UNDERSTAND_THIS_PACKAGE.md` §10 → demo script §5 above |
| **Arguing with judges / answering "why not RL?"** | `ARCHITECTURE_DECISION_LOG_FINAL.md` (31 decisions, each with a reversal condition) |
| **Checking our numbers** | `PS2_PS3_DATASET_REVIEW.md` §11 + run the audit yourself |

---

## 10. Before you send this to anyone outside the team

- The **synthetic dataset** is not inside this folder (21 MB) — it comes from the Drive link in §6. If you forward the folder, say so.
- `ARCHITECTURE_RESEARCH_BIBLIOGRAPHY.md` honestly marks **six** sources as *URL unconfirmed* (captured with citation, URL not recorded). Resolve them to DOIs before external publication; nothing in the design depends on them being linkable.
- The MASTER document (Part XV) carries the Phase-4 files inline, so "the file to email" is still `CreditNirvana_PS2_PS3_MASTER.md`.

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
| `PS2_PS3_DATASET_REVIEW.md` (+ `dataset_audit.py`, two derived CSVs) | Part XIV — the dataset review, reproducible |
| 13 Phase-4 architecture files | Part XV — reverse-engineering, options, selections, final designs, sources, decision log |
| `START_HERE_TEAM_HANDOFF.md` | Part 0 — the teammate entry point |

---

# Part XIV. The official dataset review (Act 5)

> Added 6 October 2026. The review of the official CreditNirvana synthetic dataset, table by table, with every requirement verdict, the twelve traps, and the reproducible audit scripts. Full text follows; the executable audit lives in `tools/dataset_audit.py`.

# PS2 / PS3 — DETAILED DATASET REVIEW

**What this is.** A complete review of the official CreditNirvana synthetic collections dataset (Google Drive folder `18iqIR8TjXDqf9-hgEY34uJr_DraIl_3P`, 20 CSVs, 21 MB) reviewed specifically against **PS2 — Right-Party Contact Prediction and Skip-Trace Prioritisation** and **PS3 — Address Geocoder That Learns from Field Visits**, and against the requirement files `PS2_ARCHITECTURE_REQUIREMENTS.md` (R1.1–R13.2) and `PS3_ARCHITECTURE_REQUIREMENTS.md` (R1.1–R15.3).

**Status of the numbers.** Every figure below was computed from the downloaded CSVs by `dataset_audit.py` (reproducible with one command; see §11). They are tagged:

| Tag | Meaning |
|---|---|
| `[DATA]` | computed directly from the dataset — reproducible, but **synthetic** |
| `[DATA→READ]` | computed from the dataset, then interpreted (the interpretation is ours) |
| `[GAP]` | the requirement needs a field, table or label that **does not exist** in the dataset |
| `[ASSUMPTION]` | outside the data; must be a named parameter, never a presented fact |

**The one rule that governs everything below.** The README states plainly: *"Everything in it is invented."* So this dataset can prove **mechanism** — that a pipeline runs, that a signal exists, that a failure mode is real and detectable. It can never prove **magnitude** — not an accuracy, not an ROI, not a market claim. Any number in a demo must be labelled `SYNTHETIC`.

---

## 0. Headline: the five things this review changes

| # | Finding | Consequence for the build |
|---|---|---|
| **1** | The randomised holdout in PS2 is **5.4%** of attempts and is *confounded*; the "random contact point" arm performs **worse** than the incumbent (13.4% vs 16.6% RPC). `[DATA]` | No uplift claim is possible. The benchmark is **the incumbent**, not a random baseline. R10.4 stops being a policy preference and becomes a data fact. |
| **2** | The learnable PS2 signal is **contactability memory** (what happened on *this point* before), not account financials. Permutation importance: prior-RPC **0.089**, self-relation **0.028**, hour-of-day **0.027**, everything else ≤0.009. `[DATA]` | SANKET's centre of gravity moves to the point-level state table + rules floor; the financial feature set is decoration. |
| **3** | **Skip-trace prioritisation cannot be an ML success model here**: predicting trace success from pre-trace features gives CV AUC **0.574** against a 0.772 majority-class baseline. `[DATA]` | Replace "trace after N failures" with an **EVSI-style rule** whose cost is a named parameter, and report the hit rate honestly: **77% of trace spend produced nothing**. |
| **4** | **PS3 cannot beat the commercial geocoder on accuracy with free data.** Locality centroid = **376–379 m** median vs baseline **376 m**; the oracle over all 12 candidate localities = **370 m**, with only 2% <100 m. `[DATA]` | "Beat the geocoder" is dead. The winnable target — and the one the official PS3 title actually names — is **learning from field visits**: median error **385 m → 29 m** on visits that met someone. `[DATA]` |
| **5** | The dataset **plants the failure modes** the architecture must survive: a leakage trap that doubles AUC (0.93 vs 0.67), a many-to-many join that silently inflates 51,105 attempts to 52,367, one collector supplying 162 of 172 duplicated photos, and negative visit outcomes that are *closer* to the pin than successful ones. `[DATA]` | Each becomes an explicit, testable component: point-in-time features, the ACP key, tripwire monitoring, integrity weights. |

---

## 1. What arrived — inventory and key integrity

`[DATA]` All 20 CSVs downloaded, read, and profiled. Row counts and key status:

| File | Rows | Cols | First key | Unique? | Note |
|---|---:|---:|---|---|---|
| `data/raw/accounts.csv` | 2,400 | 20 | `account_id` | ✅ | 6 lenders, 6 portfolios, 3 towns, buckets 1-30…X |
| `data/raw/splits.csv` | 2,400 | 2 | `account_id` | ✅ | train 1,680 / validation 360 / test 360 |
| `data/raw/lenders.csv` | 6 | 4 | `lender_id` | ✅ | |
| `data/raw/agents.csv` | 30 | 6 | `agent_id` | ✅ | 20 tele, 9 field, 1 voice bot |
| `data/raw/dial_attempts.csv` | 51,105 | 16 | `attempt_id` | ✅ | 2026-04-01 → 2026-06-29 |
| `data/raw/payments.csv` | 2,162 | 5 | `payment_id` | ✅ | |
| `data/raw/addresses.csv` | 3,117 | 7 | `address_id` | ✅ | 2,400 accounts; residence 2,427 / office 464 / permanent_native 226 |
| `data/raw/field_visits.csv` | 5,578 | 15 | `visit_id` | ✅ | 1,477 distinct addresses |
| `data/raw/phones.csv` | 5,719 | 7 | `phone_id` | ❌ | **5,618 unique phone_ids; 74 repeat across accounts** |
| `data/raw/skip_traces.csv` | 766 | 7 | `trace_id` | ✅ | **one** trigger rule value |
| `data/raw/verified_contact_points.csv` | 250 | 4 | `phone_id` | ✅ | all labelled 2026-07-02 |
| `../PS3_SUTRA/data/raw/towns.csv` | 3 | 4 | `town_id` | ✅ | T1/T2/T3, radius 4.2 / 3.8 / 4.8 km |
| `../PS3_SUTRA/data/raw/localities.csv` | 36 | 6 | `locality_id` | ✅ | 12 per town; 12 pincodes shared by >1 locality |
| `../PS3_SUTRA/data/raw/landmarks_poi.csv` | 240 | 6 | `poi_id` | ✅ | 14 types; **14 of 14 distinct names repeat across towns** |
| `../PS3_SUTRA/data/raw/baseline_geocodes.csv` | 2,880 | 4 | `address_id` | ✅ | 237 addresses (7.6%) have **no** geocode |
| `../PS3_SUTRA/data/raw/visit_gps_points.csv` | 160,406 | 6 | — | — | 26 points/visit median, p90 57 |
| `../PS3_SUTRA/data/raw/surveyed_addresses.csv` | 100 | 3 | `address_id` | ✅ | **the only surveyed ground truth in the package** |
| `ps1/*` (4 files) | 3,696 / 39,194 / 8,466 / 200 | — | — | — | out of scope for PS2/PS3 |

**Geometry.** Coordinates are a local metric plane in **metres from a town origin** (max \|x\| ≈ 7,900), not lat/lng. Distances are directly computable — and also mean there are **no real PIN polygons, no administrative boundaries, and no lat/lng to hand to a map SDK**. `[GAP]` for R5.2 and R12.2.

**The join key is not what it looks like.** `[DATA→READ]` `phone_id` is **not** unique in `phones.csv`; the true contact-point key is the pair **`(account_id, phone_id)`** (5,719 rows, 5,719 unique). A naive `dial_attempts × phones` join inflates 51,105 rows to 52,367 and every rate computed afterwards is quietly wrong. In this review, all PS2 rates use the ACP key. This is R7.4 and R4.6 arriving as a concrete defect rather than a principle.

---

## 2. The official framing vs our research framing

The dataset README names PS2 and PS3 in one line each. That wording is the strongest evidence in the whole package about what CreditNirvana will actually score:

| | Official name (from the dataset README) | Our research framing (requirement files) | Reconciliation |
|---|---|---|---|
| **PS2** | *Right-Party Contact Prediction and Skip-Trace Prioritisation* | "Which action a platform is **permitted** to take, and which is **worth** taking, on a contact point" | Both centre on the same two objects: a **point-level right-party signal** and a **paid-information decision**. Our framing adds the permission layer; the PS title adds the explicit money question. The data supports the first directly and the second only as a rule with parameters (§5). |
| **PS3** | *Address Geocoder That Learns from Field Visits* | "Runtime geocode + top-k candidate set + honest uncertainty + purpose classification + a visit-evidence loop" | The PS title **is** the loop. Our earlier "do not build a geocoder" verdict survives only in its original form: do not build a *coordinate producer* — build the **learner**. §4 shows the learner is where 100% of the winnable gain lives. |

**This resolves the one open scope tension in the package.** The PS3 architecture was always going to be tested against "did you build a geocoder?". The answer is now evidence-based: a from-scratch coordinate producer is **provably not competitive** on this data (376 m vs 379 m, oracle 370 m), while the visit-learning loop is **provably effective** (385 m → 29 m). Build the loop; consume a vendor for the cold start; say exactly that out loud.

---

## 3. PS2 — what the data actually supports

### 3.1 The funnel and the target vocabulary

`[DATA]` 51,105 attempts → 13,303 answered (**26.0%**) → **8,400 RPC (16.4%)**; RPC|answered = **63.0%**. 7,778 attempts (15.2%) hit a dead network response and produced **zero** RPCs.

The disposition vocabulary has **16 values**, and 7 of them are right-party outcomes:

```
no_answer 24591 | call_rejected 5409 | not_reachable 4354 | third_party_contact 3537 | switched_off 3336
rpc_ptp 2937 | rpc_hung_up 2229 | rpc_call_back 1674 | wrong_number 1192 | rpc_refused 1049
rpc_hardship 237 | third_party_ptp 154 | rpc_dispute 139 | rpc_claims_paid 135 | invalid_number 88 | language_barrier 44
```

`[DATA→READ]` This is a ready-made **multi-class label** for R4.1, and it is richer than the four macro-classes we specified: it separates *why* the right party engaged (PTP vs hung-up vs callback vs refused vs hardship vs dispute vs claims-paid) and it separates two third-party states (`third_party_contact`, `third_party_ptp` — a third party who *promises* is a distinct and dangerous object). R4.1's "one model" requirement is satisfiable **without** inventing a taxonomy; the taxonomy is in the data.

### 3.2 The logged propensity — present, but barely usable

`[DATA]` `selection_propensity` exists on every attempt. But: rule-based rows are degenerate at **exactly 1.0** for all 48,339 attempts, and the randomised arm covers **123 of 2,400 accounts (5.1%)** / 2,766 attempts. Real propensities (0.25, 0.333, 0.5, 0.75, 1.0) appear only inside that arm.

`[DATA→READ]` R1.3 (log the incumbent policy's metadata) is **satisfied in form** and **near-useless in content**: a propensity of 1.0 for 94.6% of rows carries no information. R4.3's "propensity weighting where the attempt log permits it, with clipping and effective-sample-size monitoring" becomes: *it does not permit it; report the ESS and fall back to full-population features.* R10.2 (log the propensity) becomes a **live engineering requirement on the client**, not something to be mined from this file.

### 3.3 The arm comparison — the incumbent is not a straw man

`[DATA]` Confounded contrast (the arms differ by 1.1 pp on bucket mix, 3.4 pp on outstanding, 8.4 pp on lender mix):

| arm | attempts | answer | RPC | third-party contact |
|---|---:|---:|---:|---:|
| `random_contact_point` | 2,766 | 0.295 | **0.134** | **0.121** |
| `rule_based` | 48,339 | 0.258 | **0.166** | **0.066** |

`[DATA→READ]` Two conclusions, both uncomfortable and both useful:

1. Randomising *which point to call* is **worse** than the incumbent on RPC and nearly doubles the third-party-contact rate. The incumbent already encodes real knowledge (call the self/priority-0 point first). Any model in the demo must be benchmarked against **the incumbent's realised behaviour** — and the headline claim must be about *re-ranking within a fixed call budget*, not about beating randomness.
2. The random arm's third-party rate confirms the design requirement R2.4/R6.2: **an unconstrained RPC-maximising policy increases wrong-party contact**. In this data that is the single most dangerous optimisation target, and it is exactly the one PS2's name invites.

### 3.4 What is actually predictable (and what is not)

`[DATA]` Honest, pre-dial-only model (no `network_response`, `ring_duration_s`, `talk_duration_s`, `hangup_by`, `disposition`), trained on the supplied split:

| model | train AUC | val AUC | test AUC | base rate |
|---|---:|---:|---:|---:|
| logistic regression | 0.614 | 0.602 | **0.604** | 0.173 |
| gradient boosting | 0.762 | 0.648 | **0.670** | 0.173 |

`[DATA]` **The leakage trap:** adding post-dial fields (`talk_duration_s`, `ring_duration_s`) lifts test AUC to **0.933**. That number is worthless — talk duration *is* the outcome — and a 48-hour build that grabs "all numeric columns" will produce exactly it. This is the strongest single argument for R8.2 (point-in-time features) in the whole package.

`[DATA]` Permutation importance on the honest model:

| feature | ΔAUC |
|---|---:|
| `prior_rpc` (this point produced a right-party contact before) | **0.0894** |
| `relation_recorded_self` | 0.0275 |
| `hr` (hour of day) | 0.0274 |
| `source_bureau` | 0.0084 |
| `seq` (attempt number) | 0.0078 |
| `prior_tp` | 0.0052 |
| everything else | ≤0.003 |

`[DATA→READ]` **Contactability memory dominates.** Account financials — DPD, outstanding, EMI, ability-to-pay, bureau band — contribute almost nothing on top of it. SANKET's point-level state table is therefore not bookkeeping; it is the model. It also explains why the identity model in §3.5 reaches AUC 0.899 from provenance + behaviour alone.

### 3.5 The identity labels — the most valuable file for PS2

`[DATA]` `verified_contact_points.csv`: 250 points, verified **2026-07-02** — three days *after* the last dial attempt, so every feature derived from call history strictly predates the label. Composition: borrower 127, third-party 74, not_borrower 27, switched_off 19, invalid 3. Only **183 of 250** have any call history.

`[DATA]` Behavioural read-outs (this is R1.4's "separate a human answered from the right human answered", made concrete):

| evidence on the point | n | P(borrower) | P(third party) | P(not borrower) |
|---|---:|---:|---:|---:|
| ever produced an RPC | 106 | **0.78** | 0.14 | 0.03 |
| ever answered | 145 | 0.61 | 0.26 | 0.10 |
| ever third-party contact | 53 | 0.26 | **0.64** | 0.08 |
| never answered | 105 | 0.37 | 0.35 | 0.12 |
| ≥10 attempts, 0 RPC | 16 | 0.25 | 0.38 | 0.12 |

`[DATA]` By recorded provenance (n is small — directional only):

| source | n | P(borrower) | P(third party) |
|---|---:|---:|---:|
| `skip_trace` | 12 | **1.00** | 0.00 |
| `kyc_origination` | 97 | 0.73 | 0.07 |
| `borrower_update` | 36 | 0.67 | 0.03 |
| `bureau` | 33 | 0.30 | 0.18 |
| `reference` | 57 | 0.16 | **0.81** |
| `employer` | 15 | 0.07 | **0.93** |

`[DATA]` A model on provenance + behaviour: **CV AUC 0.899 ± 0.035**; provenance alone **0.813 ± 0.045**; majority class 0.508. `[DATA→READ]` Behaviour adds real signal over provenance and the labels are usable — but on 250 rows with 5-fold CV the ±0.035 is honest uncertainty, not precision.

**The consequence for scope.** The `reference` and `employer` points — 1,272 + 5,896 = 7,168 attempts, **14% of all calls** — are 81–93% *third-party numbers* by verification, yet they have the **highest answer rates in the data** (0.44–0.46 vs 0.23 for self points). This is the trap in its purest form: the points that are easiest to reach are the points you are least allowed to talk to. An "answer-rate optimiser" would push collections straight into R6.2 violations.

### 3.6 The waste floor — and why the obvious version of it is wrong

`[DATA]` Attempts ranked by what was already known about the point *before* the call:

| prior state of the point | attempts | % of calls | RPC/attempt | RPCs captured |
|---|---:|---:|---:|---:|
| first-ever call to this point | 4,035 | 7.9% | 0.155 | 625 (7.4%) |
| already dead ≥1 time | 21,847 | 42.7% | 0.144 | 3,142 (**37.4%**) |
| already dead ≥2 times | 10,263 | 20.1% | 0.107 | 1,095 (13.0%) |
| already dead ≥3 times | 5,876 | 11.5% | **0.067** | 392 (4.7%) |
| already marked `wrong_number` | 4,570 | 8.9% | 0.095 | 436 (5.2%) |

`[DATA→READ]` A blanket "stop calling dead points" rule — the obvious first idea, and the one most hackathon teams will ship — **deletes 37% of all RPCs**. Value collapses only at the **third consecutive** dead outcome (18.0% → 6.7%). This is a precise, data-backed stopping rule, and it is a far better demo artefact than a model with a slightly higher AUC: *"we kill the 11.5% of calls that yield 4.7% of outcomes, and we keep the 42.7% that still yield 37%"*.

### 3.7 Skip-trace: the money question, answered honestly

`[DATA]`

| metric | value |
|---|---|
| traces | 766 over 603 accounts, **one** trigger rule (`15_consecutive_failed_contacts`) |
| results | `new_phone_found` 148 (19.3%) · `new_address_found` 27 (3.5%) · `no_new_info` **591 (77.2%)** |
| spend | ₹79,650 total, ₹104/trace, **₹455 per hit**, **₹61,605 (77%) spent on traces that found nothing** |
| traced points dialled | 1,264 attempts → 261 RPC (20.6% vs 16.4% overall) → **₹305 per RPC generated** |
| hit rate by segment | all segments within 18.9%–28.0% of the 22.8% base rate |
| **predict trace success from pre-trace features** | **CV AUC 0.574** vs majority-class 0.772 `[DATA]` |

`[DATA→READ]` There is no learnable "who will a trace find" signal in this data. But the *decision* is still improvable without any model:

1. The trigger is a **constant** — zero variance, so nothing can be learned from it. "When to trace" must be a **rule with a named cost and a measured base rate**, exactly R5.3's EVSI framing: *buy information when P(new reachable point) × value − ₹104 > 0*, with P estimated from the realised 22.8% and the ₹104 as a parameter.
2. The 77% dead spend is the honest headline and the honest demo: a case where the system says **"do not buy this information"** and can show the ₹61,605 it would not have spent in the observation window.
3. `[DATA]` Traced numbers that *are* found are good — 20.6% RPC, and 12/12 verified borrowers in the labelled set. So traces are not worthless; they are **unprioritised**.

### 3.8 Shared numbers — a risk the data exposes, and a requirement it validates

`[DATA]` 4,339 distinct numbers; **1,106 (25.5%) appear on more than one account**, up to **6 accounts**; 43% of phone rows sit on a shared number; **43.2% of all attempts** go to a shared number. On shared numbers the RPC rate is identical (0.164 vs 0.165) but the **third-party-contact rate is higher (0.080 vs 0.061)**.

`[DATA→READ]` R4.6 (entity resolution over the platform's own records) is now a *measured* exposure: calling a shared number "for account A" can reach a person who is the borrower of account B, and disclosing A's debt to them is a DPDP-relevant breach. The ACP key (§1) plus a shared-number flag is the minimum fix, and it is cheap.

### 3.9 Timing and the "wait" action

`[DATA]` Attempts exist **only** between 08:00 and 18:59 — the dataset is already inside the RBI window, so there is no non-compliant hour to find. `[GAP]` There is no record of pre-visit notice, consent, DNC, hardship, grievance or recording flags anywhere.

`[DATA]` RPC rate by hour: 08:00 **0.210**, 09:00 0.198, 10:00–16:00 0.132–0.148, 17:00 0.171, 18:00 0.198. By attempt sequence: attempts 1–3 0.171, 4–8 0.161, 9–15 0.183, 16–25 0.166, **26–60 0.129**. `[DATA]` **1,994 of 2,368 accounts** have a call-free gap longer than 7 days at some point, so "do not call this week" is a *realised* state, not a hypothetical one.

`[DATA→READ]` R2.2's `wait` action is representable in this dataset and its evidence is available: an account can be shown to have been silent for a week while remaining in bucket. Timing is a first-class feature (hour's permutation importance exceeds every financial variable), which makes retest-timing cohorts (R4.4: **no hazard model in the MVP**) worth revisiting *later*, with a pre-registered test.

### 3.10 Payment attribution

`[DATA]` 2,162 payments; 1,667 of 2,400 accounts have at least one; **1,299 payments (60%) fall within 7 days after an RPC attempt**, median gap 3.3 days. `[GAP]` There is **no campaign, case or contact id** on the payment row, and no amount is linked to a specific action.

`[DATA→READ]` R1.5's defined attribution window is constructible; the incrementality claim is not. R10.4 stands unchanged and is now enforced by the data: payments after contact are a **correlation**, and any demo that says "these calls recovered ₹X" is making an unproven causal claim.

---

## 4. PS3 — what the data actually supports

### 4.1 The baseline to beat, and the ceiling of free data

`[DATA]` The 100 surveyed addresses — the only surveyed ground truth — against the commercial geocoder:

| metric | value |
|---|---|
| mean / median | 533 m / **376 m** |
| p75 / p90 / p95 / max | 539 m / **839 m** / 1,831 m / 4,808 m |
| <100 m / <250 m / <500 m / <1,000 m | **9%** / 35% / 71% / 90% |

`[DATA]` The headline table of this review — error by the **vendor's own precision label**, on the survey and on the full 5,578 visits (met-someone subset, where an agent actually found the person, so the check-in is a credible fix):

| vendor `precision` | survey n | survey median | survey p90 | survey <100 m | visits n | visit median | visit <100 m |
|---|---:|---:|---:|---:|---:|---:|---:|
| `rooftop` | 1 | 25.6 m | 25.6 m | 100% | 41 | 37.7 m | **66%** |
| `street` | 16 | 108.6 m | 166.3 m | 44% | 423 | 134.9 m | 33% |
| `locality` | 73 | 385.9 m | 626.5 m | 1% | 1,650 | 367.4 m | **4%** |
| `pincode` | 10 | 1,375.8 m | 3,820.1 m | 0% | 154 | 1,336.5 m | 1% |

`[DATA→READ]` Three things, all directly usable:

1. **The vendor's `precision` label is a genuine stratum key.** It predicts real error monotonically and consistently across two independent samples (100 surveyed vs ~2,300 met visits). R8.2's "empirical quantile by stratum" no longer needs an invented stratum — this one exists, is free, and is already in the input file.
2. **The survey is representative** (`locality` share 73% vs 71.2% in the book), so the 100-address sample is a legitimate calibration set. That is not a small thing: it means R7.4's "calibrate tiers on held-out visit outcomes" is executable here.
3. The baseline's error profile is **bimodal, not noisy**: it is either street-grade (17% of addresses) or locality-grade (71%). A single "average accuracy" number hides the entire problem.

### 4.2 Can free data beat it? No — and the proof matters more than the answer

`[DATA]` A candidate geocoder built only from the free tables (locality name matched in the address text, PIN consistency, POI keywords), scored over the 12 localities per town:

| approach | matched | median error | <100 m | <250 m | <500 m |
|---|---:|---:|---:|---:|---:|
| commercial baseline | 100 | **376 m** | 9% | 35% | 71% |
| locality centroid from text | 73 | 379 m | 2% | 15% | 60% |
| **oracle** best of all 12 localities in town | 100 | **370 m** | **2%** | 22% | 80% |
| naive POI snap (first same-type landmark in town) | 31 | **4,093 m** | — | — | — |

`[DATA→READ]` The oracle result is decisive: **even perfect candidate selection from free data cannot beat the baseline**, because the locality centroid *is* the resolution limit of the free tables (median 370 m, 2% under 100 m). And the naive POI snap — the obvious "use the landmark database" move — is catastrophically wrong (worse than baseline in 90% of cases) because **all 14 landmark names repeat across all three towns**. R3.4 ("scope landmark matching to locality/PIN to avoid cross-town duplicate names") is not a hygiene requirement; it is the difference between a working component and a 4 km error.

`[DATA]` Also: 237 of 3,117 addresses (7.6%) have **no** geocode at all, and 94% of addresses carry a 6-digit PIN of which only 85% matches a known locality PIN.

### 4.3 Where the winnable gain actually is — learning from field visits

`[DATA]` On the 100 surveyed addresses (49 of them visited; 213 visits):

| outcome | visits | median error: baseline | median error: visit check-in |
|---|---:|---:|---:|
| `met_family` | 30 | 380 m | **16 m** |
| `neighbour_says_shifted` | 19 | 433 m | 20 m |
| `locked_premises` | 45 | 390 m | **20 m** |
| `met_borrower` | 60 | 388 m | 34 m |
| `cash_collected` | 3 | 376 m | 71 m |
| `no_such_person` | 3 | 142 m | 72 m |
| **`address_not_traceable`** | **53** | 542 m | **1,603 m** |

`[DATA]` Among visits that actually met someone: median **385 m → 29 m**, **87% improve**, **82% land under 100 m**. Across *all* visits on surveyed addresses, **61%** would produce a sub-100 m fix.

`[DATA→READ]` This is the PS3 thesis, proven on the data:

- **Positive-outcome visits are excellent evidence** (16–34 m) and they are the learning signal the PS title names.
- **Negative-outcome visits are nearly worthless as location evidence** — `address_not_traceable` visits are recorded a median **1,603 m** from truth, and they are also the visits *closest* to the vendor pin (median 195 m from the geocode, with a **2-minute median dwell**). The agent gave up near the pin. Treating "not traceable" as "the coordinate is wrong" would poison the belief with the agent's impatience. This is R6.2 and R9.3 ("observations are evidence, never labels") arriving as a measured effect: **the sign of the outcome and the dwell time must weight the evidence, not just its presence.**

### 4.4 Evidence quality — dwell, spread, and a planted bad actor

`[DATA]` 160,406 GPS points (median 26 per visit, p90 57); accuracy `accuracy_m` 4–72.8 m, median 9.8 m; 645 visits (11.6%) have a check-in more than 500 m from their own trail median; 5 visits report accuracy >50 m; 1 check-in falls outside the town radius; median start→check-in gap 12.1 min (max 85).

`[DATA]` **172 visits share a duplicated `photo_hash`, and FA009 accounts for 162 of them** — 26.6% of that agent's 610 visits, versus ≤1% for every other agent — with a skewed outcome mix (`locked_premises` 48% vs 22% overall, `met_borrower` 13% vs 20%).

`[DATA→READ]` This is deliberately planted, and it is the best gift in the dataset: it makes R10.2 (weight, never reject) and R10.3 (collector-level anomaly monitoring) **demonstrable**. A pipeline without a per-collector tripwire will absorb 610 observations from one bad source into the belief and never notice. With the tripwire, the demo shows a named collector, a duplicated-photo rate, and the belief widening instead of jumping.

### 4.5 Structure, language and address text

`[DATA]` Three towns with deliberately different address *styles*: **T1 Kaveripura** (Kannada-in-Latin: *"6th Cross, 5th Main, ಚರ್ಚ್ ಹತ್ತಿರ, Kuvempu Layt"*), **T2 Devgarh Nagar** (Hindi/Hinglish: *"#81 gali 10 ganesh mandir ke bagal mein krishna puri"*), **T3 Navanagara East** (metro-English/abbreviated: *"No. 170, A Blk., 3rd Rd., Navanagara East"*). 31% of addresses carry a landmark phrase; median address length 67 characters; 94% carry a PIN.

`[DATA→READ]` The `address_style` field is a genuine and rare asset: it lets the parser be tested on **three real Indian address dialects** in one dataset, which is precisely R2.1/R3.1/R3.3 territory. `[DATA]` Per-town baseline error medians are close (440 / 377 / 339 m), so **town identity is not a useful stratum** — stratum = vendor precision class × evidence type.

---

## 5. Twelve traps in this dataset

| # | Trap | The number | What it breaks | Required response |
|---|---|---|---|---|
| 1 | **Leakage by column grab** | test AUC **0.933** with post-dial fields vs **0.670** without | Any model card; credibility | R8.2 point-in-time features; a test that asserts no post-dial field is an input |
| 2 | **`phone_id` is not unique** | 51,105 → **52,367** rows on a naive join | Every rate downstream | Use the ACP key `(account_id, phone_id)` |
| 3 | **Shared numbers** | 43.2% of attempts; third-party 0.080 vs 0.061 | DPDP exposure, wrong-party contact | Shared-number flag + entity resolution (R4.6) |
| 4 | **Dead-point suppression deletes value** | ≥1 prior dead call = 42.7% of calls but **37.4% of RPCs** | An "obvious" rule that destroys the book | Stop at the **3rd** consecutive dead call, not the 1st |
| 5 | **No learnable trace-success signal** | CV AUC **0.574** vs majority 0.772 | "Skip-trace prioritisation" as ML | Make it an EVSI rule with a measured base rate |
| 6 | **Constant trigger rule** | `15_consecutive_failed_contacts` for all 766 traces | Learning "when to trace" from observed triggers | Model the decision, not the history |
| 7 | **Degenerate propensity** | 1.0 on 94.6% of attempts | Off-policy evaluation | Report ESS; log propensities properly in the client |
| 8 | **Negative outcomes are low-information** | `not_traceable` 195 m from pin, 2-min dwell, 1,603 m from truth | Treating visit outcome as a location label | Sign + dwell weighting (R6.2, R9.3) |
| 9 | **One bad collector** | FA009: 162/172 duplicated photos | Silent belief corruption | R10.3 tripwires, visible in the demo |
| 10 | **Free landmarks repeat across towns** | 14/14 names in all three towns | 4 km errors from naive snapping | R3.4 scoping to locality/PIN |
| 11 | **Cash amount lives in free text** | only **43 of 92** cash visits parseable; ₹1.8 M unparseable otherwise | Recovery measurement | Treat money as a parameter; flag the field gap |
| 12 | **Compliance fields are absent** | no notice, consent, DNC, hardship, grievance, recording, complaint fields anywhere | Cannot *demonstrate* the compliance floor from data | Build it as **versioned config with a refusal log** and state the gap openly |

---

## 6. Requirement-by-requirement: what the data can and cannot support

### 6.1 PS2 (`PS2_ARCHITECTURE_REQUIREMENTS.md`)

| ID | Requirement (short) | Verdict | Evidence / gap |
|---|---|---|---|
| R1.1 | Contact slate per account | ✅ **supported** | `phones.csv` is a slate: 2.38 points/account, `source`, `relation_recorded`, `added_date`, `priority_slot` |
| R1.2 | Point-level call outcomes | ✅ **strong** | 16-value disposition on 51,105 attempts keyed to the point |
| R1.3 | Incumbent policy metadata for propensity | ⚠️ **partial** | column exists; 94.6% degenerate at 1.0 |
| R1.4 | Identity-verified events | ✅ **supported** | 250 labelled points, dated after the dial window |
| R1.5 | Payments with an attribution window | ⚠️ **partial** | 2,162 payments, but no campaign/case id → correlation only |
| R1.6 | Suppression state (hardship/grievance/DNC) | ❌ **GAP** | no such column anywhere; `rpc_hardship` is an *outcome*, not a suppression flag |
| R1.7 | Complaint / conduct events | ❌ **GAP** | nothing |
| R1.8 | Runtime telephony intelligence, not stored | ❌ **GAP** | no lookup fields; must be an interface only |
| R2.1 | Ranked eligible action set with cost and ENV | ⚠️ **partial** | outcomes yes; **no cost column** for a call, an agent hour or a visit |
| R2.2 | Explicit `wait` with its own value | ✅ **supported** | 1,994/2,368 accounts have >7-day call-free gaps |
| R2.3 | Rule code + human sentence per refusal | ⚠️ **buildable, unprovable** | no data can validate it; it is a config artefact |
| R2.4 | No disclosure without identity confidence ≥ threshold | ✅ **supported** | verified labels + behavioural evidence (§3.5) |
| R2.5 | Calibrated probability, not a rank | ⚠️ **partial** | calibratable; segment sizes thin (e.g. 16 points at ≥10 attempts) |
| R2.6 | Information-purchase recommendation with price and value | ❌ **GAP on price** | trace cost ₹60–150 exists; call/visit cost does not |
| R3.1–R3.4 | Rules floor, candidate set before scoring, versioning, closed refusal vocabulary | ❌ **no data support** | None of these are learnable — they are configuration. Demonstrate them on config + refusal logs |
| R4.1 | One multi-class outcome model | ✅ **strong** | the 16-value vocabulary *is* the taxonomy |
| R4.2 | Segmented calibration + ECE | ⚠️ **partial** | 6 lenders × 6 portfolios exists but cells are thin |
| R4.3 | Selection-bias handling / propensity weighting | ⚠️ **weak** | ESS will be tiny; fall back to full-population features |
| R4.4 | No hazard model in the MVP | ✅ **consistent** | sequence RPC is flat (0.171 → 0.129) — timing complexity buys little here |
| R4.5 | No graph/sequence/deep models in MVP | ✅ **consistent** | permutation importance says a 6-feature model captures most of it |
| R4.6 | Entity resolution for cross-account conflicts | ✅ **strong** | 1,106 shared numbers measured |
| R4.7 | PR-AUC, Brier, ECE, precision at budget | ✅ **supported** | splits file provided; test base rate 0.173 |
| R5.1 | ENV ranking with a versioned cost table | ❌ **GAP** | no cost data; parameterise |
| R5.2 | Cost table + incrementality as named parameters with ranges | ❌ **GAP** (and thereby *enforced*) | the data offers no crutch — the UI must show ranges |
| R5.3 | EVSI-style information purchase | ⚠️ **partial** | base rate 22.8% measurable; value of a reachable point is an assumption |
| R5.4 | Capacity constraints | ❌ **GAP** | no shift capacity, no agent-minute data |
| R5.5 | No live exploration | ✅ **consistent** | the one randomised arm is historical and small |
| R6.1–R6.5 | Compliance floor, purpose limitation, no third-party targeting | ❌ **GAP on data, ✅ on design** | This is the *point*: build it as config + refusals and say the data cannot prove it |
| R7.1–R7.4 | Decision record, retention classes, licence limits, point-in-time features | ⚠️ **partial** | R7.4 is now proven necessary (trap 1); retention/licence are documentation |
| R8.1 | Temporal split | ⚠️ **use the supplied split** | the provided split is **by account**, not by time — a random-split leakage risk |
| R8.2–R8.5 | Point-in-time features, label tiers, model card, drift | ✅ **supported** | 3-month window, dated labels, six lenders to measure drift across |
| R9.1–R9.4 | Batch-first, ≤60 min portfolio pass, degrade to rules floor, ≤300 ms per account | ⚠️ **untestable at scale** | 2,400 accounts only; sizing is an `[ASSUMPTION]` |
| R10.1 | Closed outcome vocabulary captured | ✅ **already in the data** | disposition + remark exist |
| R10.2 | Log the propensity of the action taken | ⚠️ **partial** | column exists, values degenerate |
| R10.3 | Shadow-mode policy evaluation | ✅ **supported** | historical log allows offline replay |
| R10.4 | No uplift claim without a controlled comparison | ✅ **enforced by data** | 5.4% confounded arm; the random arm is *worse* |
| R11.1–R11.4 | Decision record with rule/model/config versions; exportable; reason codes | ⚠️ **buildable** | no data, pure engineering |
| R12.x | Three-endpoint API | ⚠️ **buildable** | |
| R13.x | Offline batch, shadow mode | ⚠️ **buildable** | |

### 6.2 PS3 (`PS3_ARCHITECTURE_REQUIREMENTS.md`)

| ID | Requirement (short) | Verdict | Evidence / gap |
|---|---|---|---|
| R1.1 | Raw address strings, all sources, with script markers | ✅ **strong** | 3,117 addresses, 3 dialects, mixed Kannada/Devanagari-in-Latin, 3 record types |
| R1.2 | Account context (PIN, town, product, ticket) | ✅ **supported** | `accounts` + `addresses` + PIN in text (94%) |
| R1.3 | Field observations with accuracy, dwell, outcome, agent | ✅ **strong** | 5,578 visits, 160,406 GPS points, `accuracy_m`, `dwell_s`, `photo_hash` |
| R1.4 | Notice/visit outcomes | ⚠️ **partial** | visit outcomes exist; **no notice record** — the notice gate cannot be demonstrated from data |
| R1.5 | PIN→district reference + landmark base | ⚠️ **synthetic substitute** | 36 localities with centroid+pincode; **no PIN polygon, no district/state** |
| R1.6 | Licence-configured geocoder client | ❌ **GAP** | the dataset ships one **baseline output file**, not a client. Licence behaviour stays a design decision |
| R2.1 | Extract PIN, locality, landmark, house id | ✅ **strong** | and it is non-trivial in exactly the right way (3 dialects, abbreviations, transliteration) |
| R2.2 | Open-weight Indic NER rather than a bespoke model | ⚠️ **testable** | text available; but there is no alternative parser to benchmark against |
| R2.3 | Parsing failures are abstentions | ✅ **testable** | 6% of addresses have no PIN; 69% have no landmark phrase |
| R2.4 | Parser version + spans recorded | ❌ **buildable** | |
| R2.5 | No spell-correction of proper nouns | ✅ **consistent** | "Haanuman Temple", "Layt", "Nr", "Blk." — spelling varies; aliasing must be table-driven |
| R3.1 | Conservative transliteration, keep original | ✅ **strong** | T1 addresses carry both scripts in one string |
| R3.2 | PIN validated, disagreement penalises confidence | ✅ **strong** | 94% have a PIN, only **85%** match a known locality PIN → a real 9-point disagreement rate to handle |
| R3.3 | Landmark alias table from confirmed visits | ⚠️ **partial** | 240 POIs exist; the alias relation (text → POI) must be learned, exactly as planned |
| R3.4 | Scope landmark matching to locality/PIN | ✅ **strongly proven** | 14/14 names repeat across towns; naive snap = 4,093 m median |
| R4.1–R4.5 | Runtime vendor geocode; declared storage; OSM fallback; multi-candidate; spend cap | ❌ **GAP** | no vendor client, no licence metadata, no price. Design-only, and the demo must label the stored coordinates as derived from a **provided baseline file**, not from a live call |
| R5.1 | Top-k candidate set with source labels | ⚠️ **partially demonstrable** | we can build the candidate set from localities + POIs; sources are locality / PIN / landmark / visit |
| R5.2 | PIN/locality polygon candidate on vendor miss | ⚠️ **centroid + radius only** | no polygons; the 7.6% of addresses with no geocode is the real use case |
| R5.3 | Landmark-derived candidate when the phrase resolves locally | ✅ **testable** | 31% of addresses have a landmark phrase |
| R5.4 | No candidates outside the envelope | ✅ **testable** | 1 check-in outside the town radius exists as a test case |
| R6.1 | Inspectable weighted ranker | ✅ **buildable** | and §4.2 shows why a transparent ranker is the right choice here |
| R6.2 | Integrity weights: low trust → less change, wider radius | ✅ **strong** | dwell/outcome/duplicate-photo evidence is all present |
| R6.3 | Disagreement widens the radius, never averages | ✅ **testable** | 645 visits disagree with their own trail by >500 m |
| R6.4 | Learning-to-rank only after the transparent ranker is measured | ✅ **consistent** | oracle ceiling (§4.2) says there is little left to learn from free features |
| R7.1–R7.4 | Confidence tiers, observable evidence, `unknown` first-class, calibrated on held-out visits | ✅ **strong** | the vendor-precision stratum table (§4.1) *is* the calibration |
| R8.1 | Coordinates + radius + tier + evidence count (never a bare point) | ✅ **strong** | and §4.1 shows the radius is where the honest value is |
| R8.2 | Radius = empirical quantile by stratum | ✅ **strong** | the table exists and is reproducible (see the derived CSV) |
| R8.3 | Widen to a parent stratum when thin | ✅ **required** | `pincode` and `rooftop` strata have 10 and 1 survey points |
| R8.4 | Conformal validation without overclaiming coverage | ⚠️ **thin** | n=100 ground truth; coverage claims must be stated as synthetic |
| R8.5 | Document that GPS accuracy is a 68th-percentile radius | ✅ **already true in data** | `accuracy_m` values 4–72.8 m, median 9.8 m |
| R9.1–R9.4 | On-device capture, offline sync, outcome recorded, evidence-not-labels, verify-first tasks | ✅ **strong** | all observation fields present; the "verify-first" task is directly supported by the 47% of addresses never visited |
| R10.1–R10.5 | Mock flag, accuracy, speed plausibility, duplicate detection, degrade-not-accuse, collector anomalies, no spoof-rate claim | ⚠️ **strong except mock/speed** | duplicate-photo and collector anomalies are demonstrable; there is **no mock-location flag** and no inter-point timestamps at speed resolution |
| R11.1–R11.5 | Purpose classification (home/work/other), dwell+time+POI+repeat, refuse notice at work addresses, abstain, versioned | ✅ **strong** | 464 office addresses and 226 out-of-town permanent addresses; `address_type` is the label; dwell and time-of-day are present |
| R12.1–R12.4 | Store records, PostGIS/H3, provenance/licence per coordinate, retention classes | ❌ **buildable** | the *concept* of provenance is testable (baseline vs visit vs landmark); no H3/PIN polygons in the data |
| R13.1–R13.4 | Belief updates, strata recomputation, outcome labels for the gate, **never train on vendor coordinates** | ✅ **strong** | the baseline file is the vendor output — training on it is exactly the trap the requirement forbids, and it is now technically possible to do by accident |
| R14.x | `GET /belief`, `POST /visit-evidence`, radius at decision time, landmark directions as text | ⚠️ **buildable** | |
| R15.x | Nightly district packs, offline capture, stale packs visibly widen the radius | ⚠️ **buildable** | |

---

## 7. Assumption ledger — what the research flagged, and what the data now says

| Research assumption | Status after this review |
|---|---|
| "Visit-level GPS history exists and can feed an Address Evidence Score" | ✅ **CONFIRMED** — 160,406 points, 26/visit median, per-point `accuracy_m` |
| "Point-level call dispositions exist, with agent remarks" | ✅ **CONFIRMED** — 16-value vocabulary, remarks in 3 languages |
| "A commercial geocoder baseline exists to beat" | ✅ **CONFIRMED — and unbeatable on accuracy with free data;** the win is radius honesty + the visit loop |
| "Propensities are logged, enabling off-policy evaluation" | ⚠️ **PARTLY REFUTED** — 94.6% degenerate at 1.0; ESS will be tiny |
| "A randomised holdout exists to measure incrementality" | ❌ **REFUTED in usable form** — 5.4% of accounts, confounded, and the random arm is *worse* than the incumbent |
| "Ticket bands are large enough for recovery to matter" | ✅ **CONFIRMED in range** — outstanding ₹6.3 k–₹21.2 lakh (median ₹1.23 lakh), EMI median ₹4,300; but no recovery-cost data |
| "Payments can be attributed to contact within a window" | ⚠️ **PARTIAL** — 60% of payments follow an RPC within 7 days, but there is no campaign id |
| "Suppression/hardship states are available" | ❌ **REFUTED** — no such field exists; must be config |
| "Identity verification signals exist behind the contact-point table" | ✅ **CONFIRMED** — 250 labelled points, dated after the feature window |
| "Wrong-party-contact cost can be quantified" | ❌ **still `[UNKNOWN]`** — the data gives the *rate* (6.9% of calls; 81–93% of reference/employer points), never the cost |

---

## 8. What the 48-hour MVP is now — concretely

The dataset fixes the acceptance numbers. Every claim below is checkable against `derived_ps2_policy_baselines.csv` and `derived_ps3_radius_calibration.csv`.

### PS2 — the contact-permission gate (build order)

| Step | Component | Input | The number it must beat |
|---|---|---|---|
| 1 | **ACP table** — `(account_id, phone_id)` point state, point-in-time | `phones`, `dial_attempts` | the naive join (52,367) vs correct (51,105) |
| 2 | **Waste floor** — refuse the 3rd+ consecutive dead call; refuse `wrong_number` points | attempt history | RPC/call 0.1762 → **0.1872** on the test split; −12.5% calls |
| 3 | **Identity gate** — P(borrower) per point, with a refusal when below threshold | `verified_contact_points` + behaviour | CV AUC **0.899** vs 0.813 provenance-only |
| 4 | **Outcome model** — one multi-class model, isotonic-calibrated, point-in-time features | `accounts` + ACP state | test AUC **0.670**, PR-AUC and Brier on the supplied test split; **must not exceed ~0.75**, or a post-dial field has leaked |
| 5 | **EV gate with `wait`** — cost table as named ranges; `wait` has its own value | parameters | incumbent first-3-calls RPC/call **0.157** |
| 6 | **Information decision** — EVSI rule for traces at ₹104, base rate 22.8% | `skip_traces` | "refuse the trace" must be a *visible output*; the observation-window saving is ₹61,605 |
| 7 | **Decision record + refusal list** — rule codes, config version, model version | — | shown, not claimed |

**The demo's single line:** *"We refused X actions, and here are the 3rd consecutive dead calls we stopped making that still would have produced 37% of outcomes if we had banned them all."*

### PS3 — the belief engine and the visit loop (build order)

| Step | Component | Input | The number it must beat |
|---|---|---|---|
| 1 | **Candidate set** — top-k with source labels (vendor / locality / PIN / landmark / visit) | `baseline_geocodes`, `localities`, `landmarks_poi` | baseline median **376 m**; never worse than the naive snap's 4,093 m |
| 2 | **Radius calibration table** — per vendor precision × evidence stratum, empirical p90 | 5,578 visits + 100 surveyed | `locality` → ~650 m p90; `street` → ~296 m; `rooftop` → ~268 m |
| 3 | **Integrity weighting** — dwell, outcome sign, trail disagreement, photo duplication, collector tripwire | `visit_gps_points`, `field_visits` | FA009 flagged at 26.6% duplicate rate vs ≤1% for peers; the 645 trail-disagreement visits widen rather than move the belief |
| 4 | **Visit-evidence update** — confirmed-visit fixes | `field_visits` | met-someone visits: **385 m → 29 m**, 82% under 100 m |
| 5 | **Purpose classifier** — home / work / other, abstaining | dwell + hour + `address_type` + POI | office addresses (464) and out-of-town (226) must be refused notice eligibility |
| 6 | **The honest output** — `{coordinate, radius, tier, evidence_count, provenance, purpose}` | — | a bare point is a failed output (R8.1) |

**The demo's single line:** *"We published 376 m as a truth and it is a p90 of 839 m. Here is the same address, with a radius that matches what we actually measured, and the visit that took it from 385 m to 29 m."*

### What stays out of the MVP

Survival/hazard retest timing, bandits, uplift, graph targeting, learning-to-rank, microservices, a purpose taxonomy beyond 3 classes, and **any** accuracy or ROI figure presented as real. The data has now removed the temptation: several of these would have been defensible-sounding and are now demonstrably unsupported.

---

## 9. What the data still cannot answer — questions for CreditNirvana

These are added to `CN_QUESTIONS.md`. Each is a question whose answer changes a design decision:

1. **Cost of a call-attempt minute, an agent hour, and a field visit** (travel + fuel + wage), and the **recovery value** used internally. Without these the EV gate (R5.1) is a parameter with a range, not a number.
2. **Is there a pre-visit notice record** in production, and is it machine-readable? The notice-before-visit precondition (RBI, effective 1 Jan 2027) is currently undemonstrable.
3. **Where do suppression states live** (hardship, grievance, bereavement, DNC, legal hold)? They are absent from the dataset, and they are hard barriers, not features.
4. **Is there a campaign/case id** linking a payment to the contact that caused it? Today, 60% of payments follow an RPC within 7 days and none can be attributed.
5. **How is wrong-party contact counted in production** — disposition only, or a QA sample? In this data 6.9% of calls are third-party contacts, and 81–93% of reference/employer points verify as third-party numbers.
6. **What is the real monthly call volume and the real field-force size**? The dataset is 2,400 accounts / 30 agents; no capacity constraints can be modelled from it.
7. **Do you have PIN-level polygons or a licensed administrative boundary source?** This dataset has centroids only.
8. **Which geocoder is actually in production, and under what licence terms** (caching window, storage, display)? The dataset ships a static baseline file with no vendor identity.
9. **Is there a mock-location / rooted-device flag** on the field app, and per-point timestamps at speed resolution? Spoof detection (R10.1) is currently design-only.
10. **Was the 15-consecutive-failures trace rule the real production trigger?** It has zero variance here, so "when to trace" cannot be learned from history.

---

## 10. Verdict

**PS2 — proceed, with the target moved from "prediction" to "permission plus refusal".** The data supports a point-level identity gate (AUC 0.899 on 250 labels), a deterministic waste floor with a measured 11.5%-of-calls / 4.7%-of-outcomes trade, and one multi-class outcome model whose honest ceiling on pre-dial features is AUC ≈ 0.67. It **does not** support skip-trace success prediction (AUC 0.574), propensity-weighted learning (degenerate propensity), or any uplift claim (a 5.4% confounded arm, and the random arm is worse than the incumbent).

**PS3 — proceed, with the product restated as the learning loop, not the coordinate.** The commercial baseline sits at the resolution ceiling of the free data (376 m vs an oracle-best 370 m from candidates; naive landmark snapping is 4 km wrong), so a from-scratch geocoder is provably not the deliverable. The deliverable is the loop the PS title names — **field visits move an address from 385 m to 29 m** — plus the two things the vendor does not give: an **empirically calibrated radius per stratum** (the vendor's own `precision` label predicts its real error: 38 m / 135 m / 367 m / 1,336 m by class) and an **integrity-weighted belief** that survives a collector submitting 162 duplicated photos.

**Both:** the dataset is unusually well designed as a trap course. It contains the leakage, the join ambiguity, the poisoned labels, the bad actor, the constant trigger and the unresolvable cost question — which means a submission built on it can show not only what it computes, but **what it refuses to claim**. That is the same posture the requirement files already took, and it is now backed by numbers rather than principle.

**Nothing in the architecture files is invalidated. Three things are re-weighted:** PS2 drops the trace-success model and promotes the waste floor and the identity gate; PS3 promotes the visit-learning loop and the radius calibration to the centre of the build; and the compliance layer stays exactly where it was — as configuration and refusal logs, because the data cannot prove it and no honest submission should pretend otherwise.

---

## 11. How to reproduce every number

```bash
# 1. Fetch the dataset (gdown, ~21 MB, public folder)
gdown --folder "https://drive.google.com/drive/folders/18iqIR8TjXDqf9-hgEY34uJr_DraIl_3P" -O /home/user/data/raw

# 2. Every figure in this report   (sections: q = inventory, p2 = PS2, p3 = PS3, eco = economics)
python3 dataset_audit.py             # ~2 min

# 3. Regenerate the two derived tables shipped with this review
python3 CreditNirvana_Submission/tools/build_derived_table.py
```

Shipped alongside this review:

- `dataset_audit.py` — the full audit, section by section.
- `derived_ps3_radius_calibration.csv` — **the radius table the PS3 belief engine must output**, per stratum, from two independent samples.
- `derived_ps2_policy_baselines.csv` — **the policies the PS2 demo must beat**, on the supplied test split.
- `build_derived_tables.py` — regenerates both CSVs from the raw data.

**All figures are computed from invented data. Mechanism only, never magnitude.**


---

# Part XV. Phase 4 — architecture, reverse-engineered and selected (Act 6)

> Added 6 October 2026. Read in order: the tear-down of 24 real systems → the candidate architectures → the scored options → the frontier list → the weighted selections → the three final designs → the sources → the decisions. Each file also stands alone in this section's folder.


## XV.1 — File 1 — How similar systems are actually built

*Source file: `SIMILAR_SYSTEMS_REVERSE_ENGINEERING.md`*

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


## XV.2 — File 2 — PS2: twelve architectures compared

*Source file: `PS2_ADVANCED_ARCHITECTURE_RESEARCH.md`*

# PS2 — ADVANCED ARCHITECTURE RESEARCH

**Phase 4, File 2 of 13.** Twelve genuinely different architectures for PS2, compared before any is chosen.

**Inputs to this comparison:** `PS2_ARCHITECTURE_REQUIREMENTS.md` (R1.1–R13.2), `PS2_PS3_DATASET_REVIEW.md` (every number below tagged `[DATA]` is from the audited synthetic dataset), `SIMILAR_SYSTEMS_REVERSE_ENGINEERING.md` (patterns `[S-nn]`), and the Phase-1 research.

**Ground rules used throughout.**
- A "probability" without a calibration and evaluation strategy is not an architecture, it is a wish. Every option below states its calibration plan.
- Every option must survive the dataset traps: leakage, the non-unique `phone_id`, the degenerate propensity (1.0 on 94.6% of attempts `[DATA]`), the 5.4% confounded random arm `[DATA]`, and the absent cost table.
- Feasibility is judged for a **48-hour hackathon build** and for **production**, separately, because they are different questions.

---

## 0. The ten architectures we could actually build, and one we must stop calling an architecture

| ID | Architecture | One-line thesis | Verdict class |
|---|---|---|---|
| **A1** | Classifier | Score each attempt/point, threshold it, rank | Baseline to beat — not an architecture |
| **A2** | Two-stage contactability | Stage 1 "will anyone answer", stage 2 "is it the borrower" | Useful simplification of A1 |
| **A3** | Identity graph | Represent borrower⇄phone⇄address⇄shared-with as a graph; score nodes/edges | Strong for *refusal*, weak for *uplift* |
| **A4** | State machine | Model each point as explicit states (fresh / reachable / verified-borrower / wrong-party / stale-dead) with transitions | Strong, cheap, explainable |
| **A5** | Next-best-action | Score and rank all actions per account, take argmax | Good framing, incomplete economics |
| **A6** | Constraint + optimizer | Rules floor + per-account EV, then allocate a *day's capacity* under constraints | The serious option |
| **A7** | Contextual bandit | Learn the policy online from realised rewards | Not supportable here (no exploration, no reward attribution) |
| **A8** | Constrained MDP | Optimise long-run return over sequences of actions under constraints | Research-only at our scale |
| **A9** | EVSI / information acquisition | Treat traces and verifications as *purchases of information* with a price and a value | The missing primitive — high value, low cost |
| **A10** | Portfolio-level optimizer | Solve the day as one MILP/LP: maximise expected net recovery subject to capacity, frequency, compliance | The production end-state |
| **A11** | Risk-sensitive optimizer | Same as A10, but with a downside penalty (CVaR-style) on conduct/uncertainty tails | A *modifier* that becomes a differentiator for irreversible actions |
| **A12** | Hybrid belief-state + optimization | Per-point belief state (event-sourced) → policy gate → EV/EVSI → constrained allocator → feedback | **Recommended** (see `PS2_ARCHITECTURE_SELECTION.md`) |

---

## A1. Classifier architecture

```
accounts + phones + attempt history ──► feature builder ──► GBM ──► P(RPC) ──► threshold ──► call list
```

| Attribute | Assessment |
|---|---|
| **Data requirements** | Account row + point row + attempt history. Everything in `accounts.csv`, `phones.csv`, `dial_attempts.csv` |
| **Complexity** | Low |
| **Training requirements** | ~51k labelled attempts `[DATA]`; supplied split; hours |
| **Cold start** | Trains fine on day one; a new *portfolio* has no history, but account features transfer |
| **Interpretability** | Medium (SHAP-style attributions; not a decision rule) |
| **Production realism** | This is what most deployed models are `[INFERENCE]`. It is not what the serious platforms sell `[S-3][S-16]` |
| **Hackathon feasibility** | Trivial |
| **Differentiation** | **Zero.** Every team will ship this |
| **Calibration plan** | Isotonic per segment; ECE monitored |
| **Failure modes** | (1) Leakage: adding `talk_duration_s` lifts test AUC 0.670 → **0.933** `[DATA]` — a beautiful number that means nothing. (2) Optimising RPC raises third-party contact (random arm: RPC 0.134 but third-party 0.121 vs 0.066 `[DATA]`). (3) No cost model, so "top decile" ≠ "best decile". (4) Threshold chosen once and never revisited |
| **What real systems use this?** | Only as a *component* inside a strategy `[S-16]` |

**Verdict.** Keep as the honest baseline (a model that must be beaten), never as the architecture.

---

## A2. Two-stage contactability architecture

```text
stage 1: P(answered)  ← network/time/point history
stage 2: P(borrower | answered) ← provenance, relation, verification, behaviour
          ──► combine multiplicatively ──► rank points per account
```

| Attribute | Assessment |
|---|---|
| **Data requirements** | Same as A1; the dataset already separates the two signals (`network_response` vs `disposition`) `[DATA]` |
| **Complexity** | Low–medium; two models, one join |
| **Training requirements** | Two labels; the dataset's funnel makes them clean: answered = 26.0%, RPC|answered = 63.0% `[DATA]` |
| **Cold start** | Stage 1 needs some history; stage 2 can start on provenance priors alone (`skip_trace` 1.00, `kyc_origination` 0.73, `bureau` 0.30, `reference` 0.16, `employer` 0.07 P(borrower) `[DATA]` — n is small, treat as priors) |
| **Interpretability** | **High** — the decomposition is exactly how a collections manager reasons ("it rings, but is it him?") |
| **Production realism** | High; matches TransUnion's separation of *contactability* from *correct consumer* `[S-11][S-12]` |
| **Hackathon feasibility** | Easy |
| **Differentiation** | Low–medium (the decomposition is standard in the industry) |
| **Calibration plan** | Calibrate both stages separately; the product is only as calibrated as its weaker stage; monitor ECE per stage |
| **Failure modes** | Multiplication of two miscalibrated probabilities compounds error; **the two stages have different drifts** (network coverage vs identity churn) so retraining schedules differ |
| **Verdict** | Useful as an *explanatory decomposition*, unnecessary as a *training* structure. The dataset shows both signals come from the same event history |

---

## A3. Identity graph architecture

```text
         ┌──────────┐   used_by    ┌────────────┐
         │ Borrower │◄────────────►│  Phone P1  │──shared_with──► Borrower B
         │    A     │              └─────┬──────┘
         └────┬─────┘                    │ observed_outcome
              │ verified_at              ▼
        ┌─────▼──────┐            ┌──────────────┐
        │ Address A  │            │ ContactEvent │
        └────────────┘            └──────────────┘
```

| Attribute | Assessment |
|---|---|
| **Data requirements** | `phones` (5,719 rows, 5,618 ids, **74 repeat phone_ids across accounts** `[DATA]`), `verified_contact_points`, `field_visits` |
| **Complexity** | Medium (entity resolution + propagation) |
| **Training requirements** | None required for the core: Splink-style Fellegi-Sunter gives explainable match weights with **no labels** `[S-44]` |
| **Cold start** | Good — priors come from provenance and relation, both present at onboarding |
| **Interpretability** | High per edge (each match weight decomposes into per-field contributions `[S-44]`); low if a GNN is used |
| **Production realism** | High as an *internal* capability; TransUnion's entire contact business is this, at 100B+ records `[S-11]` |
| **Hackathon feasibility** | Medium — Splink on 3k accounts is minutes, but the graph must then *change a decision*, or it is decoration |
| **Differentiation** | Medium–high **for refusal**: "this number is shared by 6 accounts; a disclosure here is a third-party exposure" is a refusal no ranking model can produce `[DATA: 43.2% of attempts are on shared numbers; third-party rate 0.080 vs 0.061]` |
| **Calibration plan** | Edge scores are probabilities by construction (FS model); validate on the 250 verified points |
| **Failure modes** | (1) Over-linking (two borrowers, one family number → spurious "shared"). (2) Under-linking (same person, spelling variants). (3) **A graph with no policy attached is a dashboard** |
| **What real systems use this?** | TransUnion (people⇄assets⇄businesses `[S-10]`); Pega/TU both treat household/relationship context as features |
| **Verdict** | **Adopt as the identity layer, not as the whole system.** It answers "may I?" better than "whom should I call first?" |

---

## A4. State-machine architecture

```text
FRESH ──call──► NO_ANSWER ──call──► NO_ANSWER_2 ──call──► DEAD_3 (refuse further dials)
   │              │                     │                    ▲
   │              └──answer──► UNKNOWN_PARTY ──verify──► WRONG_PARTY (refuse)
   │                              │
   └──answer──► RIGHT_PARTY ──payment──► ENGAGED ──(no payment 30d)──► COLD
```

| Attribute | Assessment |
|---|---|
| **Data requirements** | Attempt history + dispositions only. Fully supported `[DATA]` |
| **Complexity** | Low (a transition table + counters) |
| **Training requirements** | None. Thresholds are tuned from observed rates |
| **Cold start** | Works immediately; a new point starts in `FRESH` |
| **Interpretability** | **Highest of all options** — the state name *is* the explanation, and it can be shown to an agent or a regulator |
| **Production realism** | Very high; the NYS DTF system encodes legal prerequisites as states `[S-32]`, and skip-trace patents encode a queue with memory `[S-60]` |
| **Hackathon feasibility** | Trivial. **The dataset gives a measured payoff:** refusing the 3rd+ consecutive dead call to the same point keeps RPC/call at 0.1872 vs 0.1762 (test split) while removing 12.5% of calls `[DATA]` |
| **Differentiation** | Medium — but it *earns the right to say "we refuse"* on day one |
| **Calibration plan** | Not a probabilistic component; requires **transition-rate monitoring** instead (state distribution drift) |
| **Failure modes** | (1) **Blanket dead-point suppression destroys value**: points with ≥1 prior dead call are 42.7% of calls but 37.4% of RPCs `[DATA]` — only the *third consecutive* dead outcome collapses (18.0% → 6.7%). (2) States can thrash if not debounced. (3) States encode policy, so a policy change means a state change |
| **Verdict** | **Adopt as the deterministic skeleton.** Cheap, explainable, and it is where the honest money is |

---

## A5. Next-best-action (argmax over actions)

```text
for each account: score every action a ∈ {call p1, call p2, sms, visit, wait} ─► argmax ─► execute
```

| Attribute | Assessment |
|---|---|
| **Data requirements** | Needs *action-level* labels: which action produced which outcome. Our log is call-only (51,105 calls, 3,761 bot) `[DATA]`; there are no SMS/e-mail arms |
| **Complexity** | Medium |
| **Training requirements** | Per-action outcome models → the "more models" trap; the dataset supports **one** multi-class target (16 dispositions `[DATA]`) |
| **Cold start** | Poor for actions never taken — no counterfactual evidence exists |
| **Interpretability** | Medium |
| **Production realism** | This is Pega's core framing `[S-19]`, and the phrase is used by Experian and Credgenics `[S-1][S-26]` |
| **Hackathon feasibility** | Easy to fake, hard to do honestly |
| **Differentiation** | Low — "NBA" is the most over-used term in the brief |
| **Calibration plan** | Per-action calibration; without overlap between actions the comparison is unsupported |
| **Failure modes** | (1) **Argmax with no cost model**: Pega's own arbitration is a weighted product with no cost term `[S-20]` — good for marketing, wrong for agent minutes. (2) Selection bias: only the actions the old policy tried have data `[S-39]` |
| **Verdict** | Keep the *framing* ("which action, now"), drop the argmax |

---

## A6. Constraint + optimizer (per-account EV, day-level allocation)

```text
eligibility gate (hard rules)  ──►  EV per surviving action  ──►  allocate under capacity  ──►  execute
        ▲                                    ▲                            ▲
   closed-vocab rule codes        cost table (parameters)      agent-hours, slots, budget,
                                                               frequency ceilings, DNC
```

| Attribute | Assessment |
|---|---|
| **Data requirements** | Outcomes `[DATA: yes]` + **costs `[DATA: GAP — no cost column anywhere]`** + capacity `[GAP]` |
| **Complexity** | Medium |
| **Training requirements** | One outcome model + a cost parameter table. No RL |
| **Cold start** | Good: EV with wide priors still ranks sensibly; constraints apply from day one |
| **Interpretability** | High: a decision is a rule code + an expected value + a cost |
| **Production realism** | **This is exactly what Experian Optimize, FICO's solver, and NYS DTF do** `[S-3][S-16][S-32]` |
| **Hackathon feasibility** | Medium: gate + EV is hours; allocation can start as a greedy with Lagrangian prices |
| **Differentiation** | High — almost no hackathon team will subtract costs and enforce capacity |
| **Calibration plan** | Calibrate P(success) per segment; **the EV is only as trustworthy as the cost table**, so costs are published with ranges (R5.2) |
| **Failure modes** | (1) Garbage costs → confident nonsense; mitigate by ranges + sensitivity. (2) Capacity model that doesn't match reality (no shift data) → treat as a policy lever. (3) `wait` omitted → the optimiser invents pressure to call |
| **Verdict** | **Adopt.** This is the spine of the recommended architecture |

---

## A7. Contextual bandit

```text
context x ─► policy π(a|x) ─► action ─► reward r ─► policy update
```

| Attribute | Assessment |
|---|---|
| **Data requirements** | Randomised exploration with logged propensities across arms |
| **What the dataset actually offers** | A randomised arm on **123 of 2,400 accounts (5.1%)**, whose propensities are real (0.25–1.0) while the other 48,339 attempts are degenerate at 1.0 `[DATA]`; **and the random arm performs worse than the incumbent** (RPC 0.134 vs 0.166) `[DATA]`. ESS would be tiny |
| **Complexity** | High (policy learning + safe exploration + reward definition) |
| **Training requirements** | Thousands of randomised, reward-attributed decisions — we have ~2.8k and no reward attribution (60% of payments follow an RPC within 7 d, but **no campaign id** `[DATA]`) |
| **Cold start** | Poor |
| **Interpretability** | Low |
| **Production realism** | Real in ads/recsys; in collections it collides with regulation — every exploration is a real contact to a real borrower `[VERIFIED, S-28 guardrails]` |
| **Hackathon feasibility** | Offline bandit simulation only |
| **Differentiation** | Low and risky: it invites the "you experimented on vulnerable people" question |
| **Failure modes** | (1) Reward = payment without incrementality → learning to call people who would have paid anyway (self-cure). (2) Non-stationarity. (3) Compliance cannot be an arm |
| **Verdict** | **RESEARCH ONLY.** Document why, and note that the honest version is "reallocate attempts already planned" (R5.5), not "explore on borrowers" |

---

## A8. Constrained MDP

| Attribute | Assessment |
|---|---|
| **Data requirements** | Long sequences of state-action-reward with legal states (warrant → levy) `[S-32]`, and a reward over the *full* horizon |
| **What we have** | 3 months, 51,105 calls, 2,166 payments, no action for most outcomes, no cost, no randomisation `[DATA]` |
| **Complexity** | Very high; the NYS DTF equivalent took ≈$5 M of research plus ≈$4 M of engagement `[S-33]` |
| **Cold start / interpretability** | Poor / low |
| **Production realism** | Proven in one government deployment `[S-34]`, and in a 2025 design-science prototype with temporal-logic constraints `[S-36]` |
| **Hackathon feasibility** | None in the honest form |
| **Failure modes** | Estimating a value function from 3 months of one policy: guaranteed overfitting; the paper's own constraints were "handcrafted into the optimization process" without a specification language `[S-36]` |
| **Verdict** | **RESEARCH ONLY.** The *idea* we adopt instead: legal prerequisites as **states** (A4) and **action-availability flags** (A6) |

---

## A9. EVSI / information-acquisition architecture

```text
                    ┌──────────────── trace (₹104) ──────────────┐
decision: act now ──┤                                            ├──► act on better information,
                    └──────────────── verify (₹?) ───────────────┘    or refuse to buy at all
             EVSI = E[best decision after info] − E[best decision now]
             buy iff EVSI > price,  and report the refusal when EVSI ≤ price
```

| Attribute | Assessment |
|---|---|
| **Data requirements** | Price (present: trace cost ₹60–150, mean ₹104 `[DATA]`), the base rate of information (present: 22.8% of traces find something `[DATA]`), and a value for the decision that changes |
| **Complexity** | **Low** — a two-branch decision rule, no training |
| **Training requirements** | None. And that is the finding: predicting trace success gives CV AUC **0.574** vs majority **0.772** `[DATA]` — there is no model to build |
| **Cold start** | Immediate |
| **Interpretability** | Very high: "this trace was not bought because it would have to beat ₹104 and our measured hit rate is 22.8%" |
| **Production realism** | Information purchase is how TransUnion's skip tracing is sold `[S-11]` and how the GE patent's skip queue worked `[S-60]`; VOI is standard decision theory `[S-42]` |
| **Hackathon feasibility** | Easy, and it produces a *refusal*, which is our differentiator |
| **Differentiation** | **High.** Nobody in the market publicly prices traces against a measured hit rate and refuses on the arithmetic |
| **Calibration plan** | Base rate is measured; value of information is an `[ASSUMPTION]` shown as a range |
| **Failure modes** | (1) Value of the outcome unmeasured → EVSI becomes a fiction; mitigate with ranges + one-line sensitivity. (2) Buying information that cannot change the decision — the EVSI definition makes that zero by construction `[S-42]`, which is the point. (3) A constant trigger means no learning about *when*, so EVSI must be evaluated per-decision, not learned |
| **Verdict** | **Adopt as a first-class primitive.** It converts 77% wasted trace spend `[DATA: ₹61,605 of ₹79,650]` into a visible refusal |

---

## A10. Portfolio-level optimizer

```
maximise   Σ_accounts Σ_actions x[a] · ENV[a]      (expected net value)
subject to Σ x[a] ≤ agent_minutes / field_slots / trace_budget      (capacity)
           x[a] = 0 for a ∉ eligible set                            (compliance)
           per-account freq ≤ ceiling; ≥1-day notice before visit    (policy)
           x[a] ∈ {0,1}                                              (integer)
```

| Attribute | Assessment |
|---|---|
| **Data requirements** | ENV per action (A6), capacity (gap), eligibility flags (rules), and a solver |
| **Complexity** | Medium–high; but a *linear* relaxation with a greedy integer repair is ~150 lines |
| **Training requirements** | None beyond A6's model |
| **Cold start** | Works with wide ranges; degrades gracefully to greedy |
| **Interpretability** | High if the LP duals are surfaced as "shadow prices of a field slot / a compliance hour" |
| **Production realism** | Experian's constraint-based optimization `[S-3]`; FICO's solver `[S-16]`; mTSP routing in the 2026 MCDA framework `[S-31]` |
| **Hackathon feasibility** | **Yes** — with 2,400 accounts and ~50 field slots, this is a small MILP; OR-Tools solves it in seconds |
| **Differentiation** | High |
| **Calibration plan** | ENV inputs calibrated as A6; constraints are exact; **the objective is stated explicitly** (per the brief) — net of cost, penalties included |
| **Failure modes** | (1) A clean MILP over fabricated costs looks authoritative — that is the main danger, so costs must be exposed as ranges and the plan shown as sensitivity. (2) Over-constraining → infeasible; always keep a slack action. (3) Capacity data absent → run the model in "what-if capacity" mode |
| **Verdict** | **Adopt at day level, one shift ahead.** Not "the whole bank" — one day's plan |

---

## A11. Risk-sensitive optimizer

```
maximise   Σ ENV − λ · CVaR_α(losses)          where losses include:
             wrong-party contact cost, conduct/complaint tail, wasted field visit,
             and model uncertainty on the specific decision
```

| Attribute | Assessment |
|---|---|
| **Data requirements** | Loss *distribution*, not just a mean. Our data gives rates (third-party 6.9% of calls; 81–93% of reference/employer points verify third-party `[DATA]`) but **no rupee cost** `[UNKNOWN]` |
| **Complexity** | Medium (one extra term; linear-programmable via the Rockafellar–Uryasev formulation `[S-43]`) |
| **Training requirements** | None |
| **Cold start** | Works; the risk weight λ is a disclosed policy parameter |
| **Interpretability** | Very high — "we will not take this action because its worst decile is unacceptable" |
| **Production realism** | Standard in energy/disaster logistics `[S-43]`; **not** publicly described by any collections vendor reviewed `[INFERENCE]` — a real, defensible differentiation |
| **Hackathon feasibility** | Medium — implement as "expected value − λ × (probability of the bad outcome × its cost)", which is a one-line change from A6 |
| **Differentiation** | **High for irreversible actions** (field visit, notice): spend a field slot on a case whose identity *and* location belief are both confident, not merely high-expected-value |
| **Failure modes** | (1) λ tuned by vibes; publish the curve. (2) Double counting the same risk in both EV and CVaR terms. (3) Risk aversion used to justify doing nothing — always report what was **not** done because of it |
| **Verdict** | **Adopt as a modifier on the EV gate, with λ disclosed.** Not as a separate engine |

---

## A12. Hybrid belief-state + optimization *(recommended shape)*

```
EVENT LOG (append-only)  ──►  STATE ESTIMATORS  ──►  PREDICTION  ──►  POLICY GATE  ──►  VALUE/RISK  ──►  ALLOCATION  ──►  EXECUTION
  call outcomes                ContactPointState      one calibrated     hard rules,       EV, EVSI,          day-level          dialer / field app
  trace results                AccountContactState    multi-class        refusals with     CVaR penalty       MILP/LP +          (via their APIs)
  payments                     IdentityGraphState     model (6 classes)  rule codes        with ranges        greedy repair
  visit outcomes                                                                                                    │
        ▲                                                                                                           │
        └───────────────────────────────── outcomes + propensities + override reasons ────────────────────────────────┘
```

| Attribute | Assessment |
|---|---|
| **Data requirements** | Everything in A4+A3+A6+A9+A10+A11 — and all of it is already in the audited dataset except **costs and capacity** `[GAP]` |
| **Complexity** | High as a whole, low per layer: each layer is independently testable and independently *refusable* |
| **Training requirements** | One model (A1's honest version), one entity-resolution pass, zero RL |
| **Cold start** | Each layer has a defined cold-start behaviour (state machine from day one, priors for identity, ranges for costs) |
| **Interpretability** | High end-to-end: belief → rule code → EV → plan |
| **Production realism** | It is the union of what Experian, FICO, NYS DTF and Pega each do separately `[S-3][S-16][S-33][S-20]` |
| **Hackathon feasibility** | **Yes, if scoped:** state machine + gate + EV + EVSI + greedy allocation ≈ a day of build; the MILP is the "if time" layer |
| **Differentiation** | **Highest available** — the refusal record plus priced information plus an uncertain-aware allocation is not something any reviewed system publishes |
| **Calibration plan** | Per-segment isotonic on the one model; coverage-tested probabilities on the identity posterior (relate to PS3's conformal logic `[S-53]`); state transition rates monitored |
| **Failure modes** | (1) Scope creep into 5 models. (2) A layer that does not change a decision — every layer must be justified by a decision that flips. (3) Silent degradation: if the model is unavailable the system must fall back to the state machine and **say so in the record** |
| **Verdict** | **Recommended.** Specification in `PS2_SANKET_SOLUTION_ARCHITECTURE_FINAL.md` |

---

## 16. Ranked comparison (weights from the brief, applied in `PS2_ARCHITECTURE_SELECTION.md`)

| Rank | Architecture | Official PS alignment | Business value | Technical depth | Differentiation | Dataset support | Production realism | Hackathon feasibility | Explainability | **Weighted** |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **A12 Hybrid belief-state + optimization** | 5 | 5 | 5 | 5 | 4 | 5 | 3 | 5 | **4.60** |
| 2 | A10 Portfolio optimizer | 4 | 5 | 5 | 5 | 3 | 5 | 4 | 4 | 4.30 |
| 3 | A6 Constraint + optimizer | 5 | 4 | 3 | 4 | 4 | 5 | 5 | 5 | 4.30 |
| 4 | A9 EVSI / information acquisition | 4 | 4 | 4 | 5 | 4 | 4 | 5 | 5 | 4.20 |
| 5 | A11 Risk-sensitive optimizer | 4 | 4 | 4 | 5 | 2 | 4 | 4 | 5 | 3.85 |
| 6 | A4 State machine | 5 | 3 | 2 | 2 | 5 | 5 | 5 | 5 | 3.90 |
| 7 | A3 Identity graph | 4 | 3 | 3 | 4 | 5 | 4 | 3 | 3 | 3.60 |
| 8 | A2 Two-stage contactability | 4 | 3 | 2 | 2 | 5 | 4 | 5 | 4 | 3.50 |
| 9 | A1 Classifier | 3 | 2 | 1 | 1 | 5 | 3 | 5 | 3 | 2.75 |
| 10 | A5 NBA argmax | 4 | 3 | 2 | 2 | 2 | 3 | 4 | 3 | 2.85 |
| 11 | A7 Contextual bandit | 3 | 3 | 4 | 3 | 1 | 2 | 1 | 1 | 2.45 |
| 12 | A8 Constrained MDP | 3 | 4 | 5 | 3 | 1 | 3 | 1 | 1 | 2.90 |

*(Scores 1–5; weighted = Σ wᵢ·sᵢ with the brief's weights: PS alignment 20%, business value 15%, technical depth 15%, differentiation 15%, dataset support 10%, production realism 10%, hackathon feasibility 10%, explainability 5%. Full arithmetic in the selection file.)*

**Reading the table.** A12 wins because it is the only option whose *layers* each map to a measured fact in our dataset. A10 scores almost as high and is the right "if time" extension. A4 and A6 are the layers that make A12 honest. A7 and A8 are excluded not because they are unsophisticated — they are the most sophisticated — but because the dataset cannot support them and the brief explicitly forbids sophistication we cannot defend.

---

## 17. What each architecture changes in the actual collections workflow

Per the standing rule, every component must answer this. Consolidated:

| Layer | Workflow change | Evidence it is worth it |
|---|---|---|
| State machine (A4) | Stops the 3rd+ dead call to the same point | RPC/call 0.1762 → **0.1872**, −12.5% calls `[DATA]` |
| Identity graph (A3) | Refuses a disclosure on a shared/third-party point | 43.2% of attempts on shared numbers; P(borrower) 0.16–0.07 for reference/employer points `[DATA]` |
| Prediction (A1 inside A12) | Orders points *within* the eligible set; no longer decides who is called | Honest test AUC 0.670; leakage ceiling 0.933 `[DATA]` |
| Policy gate (A6) | Refuses with a rule code; makes third-party disclosure structurally impossible | No dataset field exists → configuration + refusal log (an honest `[GAP]`) |
| EV gate (A6) | Kills actions whose cost exceeds their expected recovery | No cost data → parameter ranges `[GAP]` |
| EVSI (A9) | Stops buying traces whose expected information value is below ₹104 | 77% of trace spend produced nothing `[DATA]` |
| Allocation (A10) | Fills the day's real capacity by value, not by list position | No capacity data → what-if mode `[GAP]` |
| Risk penalty (A11) | Requires *certainty* before an irreversible action | Wrong-party exposure 6.9% → 12.1% under a naive RPC objective `[DATA]` |

**The honest summary of this file:** seven of the twelve architectures die on contact with the dataset or with the brief's own prohibitions. The five that survive are not five competitors — they are five **layers of one system**, and the reason to build them as layers is that each one can be removed without breaking the others.


## XV.3 — File 3 — PS3: fifteen architectures compared

*Source file: `PS3_ADVANCED_ARCHITECTURE_RESEARCH.md`*

# PS3 — ADVANCED ARCHITECTURE RESEARCH

**Phase 4, File 3 of 13.** Fifteen genuinely different architectures for PS3, compared before any is chosen.

**Read with:** `PS2_PS3_DATASET_REVIEW.md` §2 (the official PS3 statement and why our framing is location-intelligence for field collections, not "build a geocoder"), §4 (PS3 evidence) and §5 (traps). Numbers tagged `[DATA]` come from the audited synthetic dataset via `dataset_audit.py p3`. Vendors/papers are tagged `[S-nn]` (mapped in `ARCHITECTURE_RESEARCH_BIBLIOGRAPHY.md`).

**The three facts that decide everything below.**

1. **The baseline is not broken, it is uncalibrated.** Vendor baseline error on 100 surveyed addresses: mean **532.7 m**, median **376.4 m**, p90 **839 m**; only 9% land within 100 m `[DATA]`. But the vendor also tells us its own `precision` per address, and that field is *good*: median error by labelled precision — rooftop **37.7 m**, street **134.9 m**, locality **367.4 m**, pincode **1,336.5 m** (independently reproduced on the surveyed sample: 25.6 / 108.6 / 385.9 / 1,375.8) `[DATA]`. The vendor's label carries the stratum; the system does not use it. That is the whole opportunity in one line.
2. **Free data cannot beat 370 m.** Candidate/landmark scoring from public free-text sources lands at **383 m** median; the *oracle over the candidate set* is **370 m** with 2% under 100 m; naive landmark snapping is **4,093 m** (worse than baseline in 90% of cases) `[DATA]`. No re-ranking architecture over free text crosses the gap. **The remaining error is field evidence.**
3. **Field evidence does beat it — by an order of magnitude, where it exists.** On visits where the agent met someone, the point can be placed at a **median 29 m** of the surveyed truth vs the vendor's 385 m on the same addresses; 87% of those cases improve and 82% land under 100 m `[DATA]`. So the architecture is not "geocode better"; it is **choose where to spend field evidence and merge it correctly**.

---

## The fifteen architectures

| ID | Architecture | Thesis |
|---|---|---|
| **G1** | Vendor wrapper | Call the API, store the pin |
| **G2** | Multi-vendor consensus | Cross-check providers; agreement = confidence |
| **G3** | Parse-then-geocode | Normalise/parse the Indian address first, then geocode |
| **G4** | Retrieval + ranking | Treat geocoding as search: retrieve candidates, rank them |
| **G5** | Learned candidate ranker | Train LambdaMART/GBM to rank candidates against observed truth |
| **G6** | Hierarchical cell prediction | Predict the administrative cell (H3/ward/local street), then resolve locally |
| **G7** | Landmark/POI anchoring | Use landmarks as anchors and infer offsets |
| **G8** | Field-evidence fusion | Bayesian fusion of GPS trail, dwell, photo, and outcome sign |
| **G9** | Map matching (HMM) | Snap the trail to a road graph to infer where the agent actually went |
| **G10** | Conformal uncertainty | Distribution-free honest radius per address |
| **G11** | Probabilistic geocoding | A posterior *distribution* over coordinates, not a point |
| **G12** | Feedback / active learning | Auto-promote confirmed coordinates; learn which strategy wins per stratum |
| **G13** | Compliance-grade provider layer | Pluggable providers, cache/permanence rules enforced in the data model |
| **G14** | Place identity graph | Resolve addresses↔buildings↔units as entities across the portfolio |
| **G15** | **Hybrid**: parse → retrieve → rank → posterior + conformal radius → field fusion → feedback | The recommended end-to-end shape |

---

## G1. Vendor wrapper

```
address_text ─► Google/Mappls API ─► {lat, lng, precision, place_id} ─► store as point
```

| Attribute | Assessment |
|---|---|
| **Accuracy** | Median 376 m; 9% <100 m `[DATA]` |
| **Uncertainty** | Only the vendor's categorical `precision`; no radius, no coverage guarantee |
| **Multilingual / Indian-address handling** | As good as the provider; Google's India coverage is the reference point `[S-49]`, Mappls is India-native with an address standard (eLoc) `[S-50]` |
| **Data needs** | None |
| **Robustness** | Single point of failure; quota and outage visible to the agent |
| **Online/offline** | Online only (and licence-bound: Google lat/lng cache ≤30 days, no permanent storage of other content `[S-48]`) |
| **Learning** | None |
| **Explainability** | Low (`partial_match`, `location_type` are weak signals `[S-47]`) |
| **Complexity / feasibility** | Trivial / trivial |
| **Role** | **The floor.** The brief forbids "call an API and return the pin" as a solution — correctly, because it is what is already happening |

**Failure modes.** Silent wrong pin (the 1,336 m pincode stratum is returned as confidently as a rooftop one); the agent cannot tell 30 m from 1.3 km; permanent-storage licence breach if cached naively.

---

## G2. Multi-vendor consensus

```
address ──► provider A ─┐
        ──► provider B ─┼──► agreement clustering ──► consensus + confidence
        ──► provider C ─┘
```

| Attribute | Assessment |
|---|---|
| **Accuracy** | Improves the *median* only if providers make independent errors. Evidence does not support that assumption strongly `[INFERENCE]`; free-form candidate sets in our sample could not beat 370 m even with an oracle `[DATA]` |
| **Uncertainty** | Real signal: cross-provider distance is a usable disagreement score |
| **Data needs** | 2–3 provider contracts, per-request cost, licence review per provider `[S-48][S-51]` |
| **Robustness** | Best-in-class against single-vendor outage |
| **Online/offline** | Online |
| **Learning** | None beyond recalibrating thresholds |
| **Explainability** | Good — "two providers agree within 50 m; the third is 1.2 km away" |
| **Complexity / feasibility** | Low / easy — but cost and terms are the blocker |
| **Differentiation** | Low: it is a purchasing decision, not an architecture |

**Failure modes.** Providers sharing a common base dataset produce false agreement; three bills; a consensus point can still be systematically wrong along the same street.

---

## G3. Parse-then-geocode

```
raw address ─► normalise script/abbreviations ─► NER (unit, building, street, locality, city, PIN) ─► structured fields
             ─► geocode each field level independently ─► compose
```

| Attribute | Assessment |
|---|---|
| **Accuracy** | The dominant error source in Indian addresses is *parsing*, not geocoding `[S-45][S-46]`. Public tooling exists: `addressparser` (IndicBERTv2-SS + CRF, <30 ms) `[S-46]`, Shiprocket's open IndicBERT address NER `[S-13bis]` |
| **Uncertainty** | Per-field: unknown PIN ≠ unknown street |
| **Multilingual** | **The strong point.** Handles Devanagari/Bengali/transliteration, which the vendor alone often does not |
| **Data needs** | The address corpus we have (3,117 addresses) plus a gazetteer |
| **Robustness** | Degrades gracefully: unparsed → fall back to whole-string geocode |
| **Online/offline** | Fully offline-capable (a real advantage: privacy and cost) |
| **Learning** | NER model is pretrained; a small amount of fine-tuning is possible, but the dataset has no parse-level labels `[DATA: GAP]` |
| **Explainability** | **High** — the parse *is* the explanation |
| **Complexity / feasibility** | Medium / feasible (open weights) |
| **Differentiation** | Medium — most teams will dump the raw string into an API |

**Failure modes.** Mis-parse silently attaches the right street to the wrong locality; the CRF is only as good as its training distribution (Indian postal corpora, not collections-specific).

---

## G4. Retrieval + ranking

```
query (parsed address) ─► BM25/embedding retrieval over gazetteer+POI+past-verified pins ─► top-k candidates
                       ─► rank ─► return best, or "no confident candidate" ─► field task
```

| Attribute | Assessment |
|---|---|
| **Accuracy** | Ceiling measured: oracle over our candidate sets = 370 m median, 2% <100 m `[DATA]`. Retrieval is necessary but **not sufficient** |
| **Uncertainty** | Margin between top-1 and top-2 is a usable confidence feature |
| **Data needs** | A gazetteer: PIN↔locality↔town (present: 3 towns, 36 localities, 240 POIs `[DATA]`), Overture/open addresses `[S-52]`, India Post directory (non-commercial NDSAP terms `[S-65]`) |
| **Robustness** | Good: an empty candidate set is a legitimate, informative output |
| **Online/offline** | Offline; can be precomputed per PIN |
| **Retrieval vs ranking** | This is the correct *mental model* for the problem `[S-46bis, BM25/retrieve-rerank]` — but see G5 |
| **Explainability** | High — candidates with scores |
| **Complexity / feasibility** | Medium / feasible |
| **Differentiation** | Medium-high as a *framing*: geocoding is search, and search outputs candidates, not answers |

**Failure modes.** A confident top-1 from a degenerate candidate set (all 14 POI names repeat in `landmarks_poi.csv` `[DATA]`); BM25 on transliterated text matching the wrong script variant.

---

## G5. Learned candidate ranker

```
candidates ─► features (token overlap, PIN match, locality distance, POI proximity, vendor precision, past confirmations)
           ─► LambdaMART / GBM ─► ranked list
```

| Attribute | Assessment |
|---|---|
| **Accuracy** | The honest ceiling is again 370 m `[DATA]` — **a ranker can only recover what retrieval offered**. This is the single most important negative result of Phase 4 for PS3 |
| **Uncertainty** | Rank margin; not a calibrated error radius |
| **Data needs** | Pairs (candidate, truth). We have 100 surveyed addresses `[DATA]` — enough to *demonstrate*, not to train a generalisable ranker |
| **Robustness** | Overfits fast at n=100 |
| **Online/offline** | Offline |
| **Learning** | Yes, but label-poor |
| **Explainability** | Medium |
| **Complexity / feasibility** | Medium / feasible as a demo, **not defensible as a claim** |
| **Differentiation** | Medium |

**Failure modes.** Reporting an improvement measured on the same 100 surveyed points it was tuned on; a ranker trained on locality-level candidates learning "prefer the town centre".

---

## G6. Hierarchical cell prediction *(GeoIndia-style)*

```
address ─► predict hierarchy: PIN ─► ward/zone ─► H3 cell (res 8–10) ─► local street ─► building
        ─► point = cell centroid, radius = cell size
```

| Attribute | Assessment |
|---|---|
| **Accuracy** | GeoIndia reports >50% mean and >85% p99 error reduction vs Google on 67 M addresses `[S-47bis]`, with production gains self-reported by Meesho; an earlier ACL Industry paper predicts H3 cells and was the origin of the approach `[S-47]`. **Not reproducible here**: the corpus is proprietary |
| **Uncertainty** | **Excellent** — a cell *is* a radius; error is bounded by construction |
| **Multilingual** | Strong (built for Indian addresses) |
| **Data needs** | Large labelled corpus + hierarchy gazetteer — the blocker |
| **Robustness** | High: hierarchical fallback (street fails → locality still returned) |
| **Online/offline** | Offline, fast (cell classification) |
| **Learning** | Yes, supervised, data-hungry |
| **Explainability** | High — "we are confident of the street, not the building" |
| **Complexity / feasibility** | High / **research-only at our scale** |
| **Differentiation** | Very high if it could be built — which is why we steal the *output contract* (hierarchy + bound) and not the model |

**Failure modes.** With 3,117 addresses the hierarchy is learnable to locality level only — which is exactly the 367 m stratum the baseline already produces.

---

## G7. Landmark / POI anchoring

```
address mentions landmark ─► find POI ─► apply relational offset ("behind", "opposite") ─► pin
```

| Attribute | Assessment |
|---|---|
| **Accuracy** | **Measured failure: 4,093 m median, worse than baseline in 90% of cases `[DATA]`** — because the POI table is sparse (240 rows, 14 repeated names, incomplete per the README) and the relational offsets are mostly absent from the text |
| **Uncertainty** | High, and not quantifiable from the data |
| **Data needs** | A real POI/GIS layer with attributes; we have a demo table |
| **Robustness** | Poor |
| **Online/offline** | Offline if the POI table is licensed |
| **Explainability** | High but wrong |
| **Complexity / feasibility** | Low / **do not build as an accuracy play** |
| **Differentiation** | None |
| **Correct use** | Landmarks as **candidates and priors for the field task** ("the agent's search radius shrinks around the named landmark"), never as automatic coordinate correction `[DATA]` |

---

## G8. Field-evidence fusion

```
prior: vendor point + precision stratum radius
evidence:  GPS trail (accuracy per point) │ dwell time │ outcome sign │ photo hash │ landmark text
            ──► spatial likelihood per evidence item ──► posterior mean + credible radius
```

| Attribute | Assessment |
|---|---|
| **Accuracy** | **The measured win:** 385 m → **29 m** median on met-someone visits; 87% improve; 82% <100 m `[DATA]`. GPS itself: median 26 points per visit, median `accuracy` 9.8 m `[DATA]` |
| **Uncertainty** | Native: the posterior has a spread; recompute the conformal radius after fusion |
| **Multilingual** | Not applicable |
| **Data needs** | `visit_gps_points.csv` (160,406 rows, accuracy per point), `field_visits.csv` (5,578 visits, 16 outcome codes) — both present |
| **Robustness** | Must be engineered against the poison trap: `address_not_traceable` check-ins sit **1,603 m** from truth and 195 m from the pin with **2-minute dwell**, i.e. a negative outcome *manufactures* a false location `[DATA]`. Rule: weight by outcome sign **and** dwell, and never let a negative outcome move a point |
| **Online/offline** | Offline (on-device or nightly) |
| **Learning** | Likelihood weights are estimated from 1,477 visited addresses; calibration is empirical, not learned |
| **Explainability** | **High** — each evidence item contributes a visible weight |
| **Complexity / feasibility** | Medium / **yes, this is the core PS3 build** |
| **Differentiation** | **Highest.** No reviewed competitor closes a 385 m → 29 m gap with in-house evidence; the closest analogue is logistics' two-confirmation geocode auto-update `[S-56]` |

**Failure modes.** (1) Trusting a spoofed trail: 645 check-ins (11.6%) are >500 m from their own trail; FA009 has 162/172 duplicate photo hashes (26.6% vs ≤1% elsewhere) `[DATA]` → integrity checks are mandatory (mock-location flag, cross-signal inconsistency, teleport, duplicate media) `[S-58]`. (2) Averaging the trail: the apartment door is not the trail centroid. (3) Letting a single visit overwrite a pinned address.

---

## G9. Map matching / trajectory inference (HMM)

```
raw GPS trail ─► HMM over road/segment graph ─► matched path ─► arrival segment ─► candidate doors on that segment
```

| Attribute | Assessment |
|---|---|
| **Accuracy** | The right tool for *where the agent went*; the deliverable we need is narrower — the **stop point and the dwelling segment**. Standard HMM map matching `[S-54]` |
| **Uncertainty** | Path probability; segment-level ambiguity on dense streets |
| **Data needs** | A road graph. **We do not have one** `[GAP]`; the coordinates are a local metric plane with no polygons `[DATA]` |
| **Robustness** | Sensitive to accuracy outliers and to the 11.6% integrity-flagged check-ins |
| **Online/offline** | Offline, batch |
| **Learning** | Emission/transition parameters are tunnable from 26 points/visit |
| **Explainability** | Medium |
| **Complexity / feasibility** | High / **not in 48 h without a road graph** |
| **Differentiation** | Medium |
| **Cheaper substitute that gets 80% of it:** dwell-clustering of the trail (stop detection) — find the stationary clusters, take the densest one with a positive outcome, intersect with the vendor's street-level candidate interval |

**Failure modes.** Matching to a wrong but nearby road; assuming the phone's location equals the door.

---

## G10. Conformal uncertainty

```
calibration set (100 surveyed addresses) ─► nonconformity scores ─► per-stratum radius with finite-sample coverage
```

| Attribute | Assessment |
|---|---|
| **Accuracy** | Does not change the point estimate; it makes the *error bar* honest |
| **Coverage** | Peer-reviewed result: conformal spatial prediction achieves **93.67% empirical coverage at 90% nominal** vs 68.33% for bootstrap `[S-53]` |
| **Data needs** | A labelled calibration set — 100 points `[DATA]`, sufficient for *stratified* (not per-address) radii |
| **Robustness** | Exchangeability is the assumption; towns are exchangeable *within* a stratum, not across |
| **Online/offline** | Offline; recomputed when labels arrive |
| **Learning** | Distribution-free — this is the point `[S-53]` |
| **Explainability / complexity / feasibility** | High / Low / **yes** |
| **Differentiation** | High for PS3: a geocoder that admits its interval is unusual, and it is exactly what a field planner needs to decide "is this visit worth a slot?" |

**Correct use.** Per-stratum (`precision` × town) radii, published in a calibration table, updated as field truth arrives — never a global 90% radius applied to a rooftop and a pincode alike.

---

## G11. Probabilistic geocoding

```
address ─► posterior p(x | address, evidence) sampled over a spatial grid
               = vendor prior (stratum kernel) × field-evidence likelihood × POI/landmark likelihood
        ─► report mean, mode, and HDR region; decisions consume the distribution, not the point
```

| Attribute | Assessment |
|---|---|
| **Accuracy** | Same point estimate as G8 on average, but **the decision is different**: a visit is planned against P(point ∈ 200 m), not against a pin |
| **Uncertainty** | Full distribution — the most expressive option |
| **Data needs** | Priors (stratum kernels, measurable from `derived_ps3_radius_calibration.csv`) + evidence likelihoods |
| **Robustness** | Product-of-experts is fragile if one likelihood is overconfident; needs tempering |
| **Online/offline** | Offline; grid resolution must match the metric plane |
| **Learning** | Likelihood weights fitted empirically; no labels needed for the prior (the vendor's own `precision` label *is* the prior) |
| **Explainability** | Medium-high (contributions visible); low to a non-technical reader unless shown as a heat map |
| **Complexity / feasibility** | Medium-high / feasible at coarse grid |
| **Differentiation** | **High** — "we return a distribution" is a genuinely different product contract, and it makes G10 and the PS2 field-slot decision trivial to compute |

**Failure modes.** Fake precision in the grid; double counting evidence that is not independent (same trail, two features).

---

## G12. Feedback / active learning

```
confirmed coordinate (2 independent confirmations) ─► promote as canonical ─► improves retrieval (G4)
                                                       ─► updates stratum priors (G10) ─► reprioritises field tasks
```

| Attribute | Assessment |
|---|---|
| **Accuracy** | Compounding: each confirmed visit improves every future query in that street |
| **Data needs** | Confirmation events — the dataset has 1,477 visited addresses and the outcome vocabulary to define "confirmed" `[DATA]` |
| **Robustness** | Requires a **poison guard** (the 11.6% inconsistent check-ins) and a two-confirmation rule, matching logistics practice `[S-56]` |
| **Online/offline** | Offline batch; the online path only reads |
| **Explainability** | High: "this pin moved because two independent visits agreed" |
| **Complexity / feasibility** | Low / **yes — highest value per line of code in PS3** |
| **Differentiation** | High; the *novelty* is that the confirmation signal comes from collection outcomes, not from delivery scan data |

**Failure modes.** A wrong pin confirmed twice (agents copying the pin); feedback loops that amplify a systematic offset; a third-party visit confirming a location that is not the borrower's address.

---

## G13. Compliance-grade provider layer

```
provider interface {geocode, reverse, validate}  ─►  cache policy guard (≤30 d, no permanent content storage)
    Google │ Mappls │ open (Nominatim, 1 req/s)   ─►  audit log of provider, timestamp, terms version
```

| Attribute | Assessment |
|---|---|
| **Why it exists** | Google Maps Platform terms: lat/lng cached **≤30 days**, no permanent storage of other content, no training on output `[S-48]`; Nominatim 1 req/s and no heavy use `[S-51]`; data.gov.in NDSAP non-commercial `[S-65]` |
| **Consequence for the architecture** | **The canonical coordinate cannot be a vendor pin.** The long-lived coordinate must be *our own* field-confirmed record (G12), with vendor pins as time-limited priors |
| **Complexity / feasibility** | Low / yes — and it is a genuine differentiator because most teams will cache vendor responses |
| **Differentiation** | Medium (compliance-shaped, not accuracy-shaped), but it is the kind of thing a bank's legal review asks about in the first meeting |

---

## G14. Place identity graph

```
Address ──at──► Building ──contains──► Unit      PIN ──contains──► Locality ──in──► Town
   ▲                 ▲
   └── observed_at ──┴── ContactPoint (borrower link)
```

| Attribute | Assessment |
|---|---|
| **Purpose** | Deduplicate: 3,117 addresses for 2,400 accounts, with 74 repeated `phone_id`s across accounts `[DATA]` → many "different" addresses are the same building. Fixing the building fixes every unit in it |
| **Accuracy** | Improves *throughput* of confirmation, not per-address accuracy directly |
| **Data needs** | Address text similarity (Splink/Fellegi-Sunter on address fields `[S-44]`) + coordinates |
| **Robustness** | Over-merging two buildings is the risk; FS weights keep it explainable |
| **Online/offline** | Offline |
| **Explainability** | High (per-field match weights) |
| **Complexity / feasibility** | Medium / feasible — and it is the natural PS2↔PS3 bridge (see `SANKET_SUTRA_SYSTEM_ARCHITECTURE_FINAL.md`) |
| **Differentiation** | High at portfolio level: "confirm 40 buildings, not 1,200 addresses" |

---

## G15. Hybrid *(recommended)*

```
address_text
   │
   ├─(1) PARSE / NORMALISE ......... structured fields + script normalisation        [G3]
   │
   ├─(2) RETRIEVE .................. candidates from gazetteer + confirmed-pin index  [G4]
   │
   ├─(3) RANK ...................... score candidates (rules first, model if labels)  [G5]
   │
   ├─(4) PRIOR ..................... vendor result + precision stratum kernel         [G1 + G10]
   │
   ├─(5) POSTERIOR ................. fuse prior ⊗ field evidence ⊗ landmark evidence  [G8, G11]
   │        └─ integrity gate: mock-location, teleport, duplicate media, negative-outcome exclusion
   │
   ├─(6) UNCERTAINTY ............... per-stratum conformal radius + coverage monitor  [G10]
   │
   ├─(7) DECISION SURFACE .......... P(within 200 m) ─► feeds the PS2 field-slot decision
   │
   └─(8) FEEDBACK .................. 2-confirmation promotion ─► index, priors, task queue [G12]
```

| Attribute | Assessment |
|---|---|
| **Accuracy** | Baseline 376 m → ~29 m where field evidence exists; elsewhere the honest stratum median with honest radius |
| **Uncertainty** | Distribution + conformal coverage; **the only option that reports both** |
| **Multilingual** | Parse layer handles script/transliteration `[S-45][S-46]` |
| **Data needs** | All present except a road graph (drop G9) and third-party POI content (landmarks used as priors only) `[DATA]` |
| **Robustness** | Layered: any stage can fail to its fallback; integrity gate protects the whole posterior |
| **Online/offline** | Offline-capable; provider calls only for the prior |
| **Learning** | Empirical calibration + 2-confirmation promotion; no model required for the core claim |
| **Explainability** | High, stage by stage |
| **Complexity / feasibility** | Medium-high overall, **feasible in 48 h if stages 2/3 are minimal** |
| **Differentiation** | **Highest**: honest radius + evidence fusion + compliance-safe canonical store |

---

## Ranked comparison

Scoring 1–5; weighted with the brief's weights (PS alignment 20 / business value 15 / technical depth 15 / differentiation 15 / dataset support 10 / production realism 10 / feasibility 10 / explainability 5).

| Rank | Architecture | PS align | Value | Depth | Diff | Data | Prod | Feas | Expl | **Weighted** |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **G15 Hybrid** | 5 | 5 | 5 | 5 | 4 | 5 | 4 | 5 | **4.75** |
| 2 | **G8 Field-evidence fusion** | 5 | 5 | 4 | 5 | 5 | 4 | 5 | 5 | 4.70 |
| 3 | **G10 Conformal uncertainty** | 5 | 5 | 4 | 5 | 4 | 5 | 5 | 5 | 4.65 |
| 4 | G12 Feedback / active learning | 4 | 5 | 4 | 5 | 4 | 5 | 5 | 4 | 4.45 |
| 5 | G11 Probabilistic geocoding | 4 | 4 | 5 | 5 | 3 | 4 | 3 | 3 | 3.95 |
| 6 | G3 Parse-then-geocode | 5 | 4 | 3 | 3 | 5 | 4 | 4 | 5 | 4.15 |
| 7 | G4 Retrieval + ranking | 4 | 4 | 3 | 4 | 4 | 4 | 5 | 4 | 3.95 |
| 8 | G14 Place identity graph | 4 | 4 | 3 | 4 | 4 | 4 | 3 | 4 | 3.75 |
| 9 | G13 Compliance provider layer | 5 | 3 | 2 | 3 | 5 | 5 | 5 | 4 | 4.05 |
| 10 | G2 Multi-vendor consensus | 3 | 3 | 3 | 2 | 2 | 4 | 3 | 4 | 2.85 |
| 11 | G6 Hierarchical cell prediction | 4 | 4 | 5 | 5 | 1 | 4 | 1 | 4 | 3.45 |
| 12 | G1 Vendor wrapper | 2 | 1 | 1 | 1 | 5 | 3 | 5 | 2 | 2.20 |
| 13 | G5 Learned candidate ranker | 3 | 3 | 4 | 3 | 2 | 3 | 3 | 3 | 2.95 |
| 14 | G9 Map matching (HMM) | 3 | 3 | 5 | 4 | 1 | 3 | 1 | 3 | 2.90 |
| 15 | G7 Landmark anchoring | 3 | 2 | 2 | 2 | 2 | 2 | 2 | 3 | 2.25 |

**Reading the table.** The top of the list is not the most sophisticated architecture — G6 and G9 are more sophisticated and both rank low because the data cannot support them in 48 hours and the brief forbids citing sophistication we cannot demonstrate. G8 and G10 rank at the top because each is backed by a **measured** number from our own dataset (385 m → 29 m; and a stratum table that two independent samples agree on). G15 is the union, and its only risk is scope — which is why `PS3_ARCHITECTURE_SELECTION.md` fixes the build order and the minimum viable cut.

---

## What each architecture changes in the actual field workflow

| Layer | Workflow change | Evidence |
|---|---|---|
| Stratum-aware radius (G10) | The field app stops showing a pin and starts showing **"search 1.3 km" vs "search 40 m"** | pincode stratum median 1,336.5 m vs rooftop 37.7 m `[DATA]` |
| Field fusion (G8) | Every completed visit improves the map, so later visits cost less | 385 m → 29 m on met-someone visits `[DATA]` |
| Integrity gate (G8) | The system stops learning from the 11.6% inconsistent check-ins | 645 check-ins >500 m from their own trail `[DATA]` |
| Feedback (G12) | Two confirmations promote a coordinate; no manual master-data task | logistics practice `[S-56]` |
| Parse layer (G3) | Agents stop retyping addresses; branch/script variants collapse to one record | `addressparser` <30 ms, open weights `[S-46]` |
| Provider layer (G13) | Legal can approve the data flow; the canonical coordinate is ours | Google cache ≤30 d `[S-48]` |
| Distribution output (G11) | PS2 can ask "P(within 200 m)?" and price a field slot | enables the PS2↔PS3 contract |

**The honest summary of this file.** PS3 is not a geocoding-accuracy problem; our own measurements show free data caps out at 370 m and that a commercial geocoder is already within 376 m. The architecture that matters is the one that (a) tells the truth about how far off it is, (b) spends field evidence where it changes the belief most, (c) refuses to learn from contaminated evidence, and (d) hands PS2 a probability instead of a pin.


## XV.4 — File 4 — PS2: seven options scored

*Source file: `PS2_ARCHITECTURE_OPTIONS.md`*

# PS2 — ARCHITECTURE OPTIONS

**Phase 4, File 4 of 13.** Seven options that differ in *kind*, not in tuning. Each is complete enough to be built, scored against the brief's criteria, and rejected or carried forward on the record.

**Scoring key (1–5, same for all options):** `Align` = fit to the official PS2 statement and requirement IDs R1–R13 · `Value` = business value in the real collection workflow · `Depth` = technical depth · `Diff` = differentiation from a standard submission · `Data` = support from the audited dataset · `Prod` = production realism · `Feas` = 48-hour feasibility · `Expl` = explainability/auditability.
**Weights (from the brief):** 20 / 15 / 15 / 15 / 10 / 10 / 10 / 5.

---

## O1 — Honest baseline control *(the thing to beat, not the answer)*

**What it is.** Rules for eligibility, one GBM for P(right party), rank by probability, call top-N. No economics, no state, no refusal logic.

**Components.** Feature builder over `dial_attempts` pre-dial fields → LightGBM → isotonic → rank.

**Why it is listed.** The brief says every advanced component must beat a simpler baseline. This *is* that baseline, and it must exist as a running artifact so that every later claim is comparative. Measured: honest pre-dial test AUC **0.604** (logistic) / **0.670** (GBM); the leaked variant reaches 0.933 and is never quoted `[DATA]`.

**What it proves.** Nothing about collections practice. Its job is to occupy the "before" column.

**Scoring.** Align 3 · Value 2 · Depth 1 · Diff 1 · Data 5 · Prod 3 · Feas 5 · Expl 3 → **2.75**

**Fate.** Kept as `baseline/` in the repo, reported in the demo as the control.

---

## O2 — Propensity + identity, gate-shaped *(vendor-shaped production design)*

**What it is.** Mirror the architecture of the commercial platforms: score contactability, score identity/correct-party separately, apply a compliance gate **before** engagement (TransUnion's public description of pre-engagement compliance checks `[S-11][S-12]`), then rank.

```
contactability model ─┐
                      ├─► P(RPC) ─► compliance gate ─► ranked call list
correct-party model ──┘        (DNC, hours, per-day caps, IDs)
```

**Component → data mapping.**
| Component | Data |
|---|---|
| Contactability | `dial_attempts` (answered = 26.0% `[DATA]`), `phones.phone_type`, hour-of-day (peaks 0.210/0.198/0.198 at 08/09/18h `[DATA]`) |
| Correct party | provenance P(borrower): `skip_trace` 1.00, `kyc_origination` 0.73, `borrower_update` 0.67, `bureau` 0.30, `reference` 0.16, `employer` 0.07; CV AUC 0.899 with behaviour `[DATA]` |
| Gate | no dataset field exists → configuration `[GAP]` |
| Ranking | one combined model or product of two |

**What it proves.** That PS2 can be built in the shape the industry actually uses, with the funnel decomposed. **What it cannot prove.** That the ranking is *worth* anything — it still has no cost term and no capacity.

**Risks.** Two models to calibrate; the gate is unmeasured, so its value is asserted as a policy requirement, not demonstrated.

**Scoring.** Align 4 · Value 3 · Depth 3 · Diff 2 · Data 5 · Prod 5 · Feas 5 · Expl 4 → **3.75**

**Fate.** Its two ideas (pre-engagement gate, identity separation) are absorbed into O3/O5 as layers; the standalone build is superseded.

---

## O3 — Belief-state, event-sourced, refusal-first *(SANKET core)*

**What it is.** Every contact point is an object with an explicit **state**, an owner, an update rule, and a half-life. All state changes are events. Actions are only permitted if the state permits them; refusals are first-class records. No economics beyond a held-out cost table.

```
event log ──► state estimator ──► permission (state ⊕ rules) ──► action queue ──► outcomes ──► (back to log)
                    │
             CONTACT_POINT_STATE: FRESH / ANSWERED_UNKNOWN / THIRD_PARTY_CONFIRMED /
             RIGHT_PARTY_REACHED / NO_ANSWER×n / DEAD_3 / DISPUTED / VERIFIED_OTHER
```

**Component → data mapping.**
| Component | Data / rule |
|---|---|
| State derivation | 16 dispositions in `dial_attempts.disposition` `[DATA]` |
| Dead-point rule | refuse only at **3+ consecutive** dead outcomes: RPC/call 0.1762 → **0.1872** with −12.5% calls `[DATA]` |
| Third-party guard | reference/employer points: 0.44–0.46 answer rate but **81–93% third-party** `[DATA]`; shared-number rate 43.2% `[DATA]` |
| Owner / update | each state transition names the event that can move it (call, trace, payment, visit, time decay) |
| Refusal | rule code + timestamp + data snapshot → the audit artifact |

**What it proves.** That refusals can be *calculated*, not asserted — the differentiator the whole submission rests on. **What it cannot prove.** Anything about optimal sequencing; it is deliberately myopic.

**Risks.** Over-suppression (see the dead-point trap: ≥1 prior dead = 42.7% of calls / 37.4% of RPCs); without the economics layer it cannot trade off a refusal against value.

**Scoring.** Align 5 · Value 4 · Depth 3 · Diff 4 · Data 5 · Prod 5 · Feas 5 · Expl 5 → **4.40**

**Fate.** **Adopted as Layer 1–3** of the final architecture.

---

## O4 — Allocation-first *(portfolio MILP day-planner)*

**What it is.** Start from the *scarcest resource* — the day's agent hours, field slots, trace budget — and solve one constrained problem that assigns them to accounts. Everything else (models, rules) is an input.

```
max Σ ENV[a]·x[a]  s.t.  capacity, eligibility, frequency, notice, x binary
```

**Component → data mapping.** ENV needs outcomes (present) × costs (absent → parameter ranges published `[GAP]`); capacity absent → run in what-if mode (1,000 accounts / 200 agent-hours / ₹50,000 trace / 50 field slots, exactly the brief's figures).

**What it proves.** That capacity, not ranking, is the binding constraint — and that budget can be *spent* deterministically instead of drifting. **What it cannot prove.** That the ENV numbers are right; the whole edifice rests on a cost table we must supply as labelled parameters.

**Risks.** Fabricated-looking precision (mitigate: ranges + sensitivity plot); over-constraining to infeasibility (always leave `wait`).

**Scoring.** Align 4 · Value 5 · Depth 5 · Diff 5 · Data 3 · Prod 5 · Feas 4 · Expl 4 → **4.35**

**Fate.** **Adopted as Layer 6**, entered as a greedy with Lagrangian prices, upgraded to OR-Tools MILP if time permits.

---

## O5 — Information-purchase engine *(EVSI-first)*

**What it is.** The primary decision is not "whom to call" but "**what is worth knowing before we call**". Traces, field verification and identity checks are purchases; each is bought only if expected value of sample information exceeds price.

```
prior belief ──► decision under current belief ──► EV0
             ──► hypothetical belief after info ──► EV1
             ──► buy iff (EV1 − EV0) > price
```

**Component → data mapping.**
| Input | Value |
|---|---|
| Price | ₹60–150, mean **₹104/trace**; ₹79,650 total spend `[DATA]` |
| Hit rate | 22.8% of traces yielded information; ₹455 per hit; ₹305 per RPC `[DATA]` |
| Waste | **77% of spend (₹61,605)** produced nothing `[DATA]` |
| Learnability | Predicting trace success: CV AUC **0.574 vs 0.772** majority → **no model**; the decision rule is the deliverable `[DATA]` |

**What it proves.** That the dataset's most expensive public failure can be turned into a visible, arithmetic refusal. **What it cannot prove.** The value of the decision that changes — no campaign/outcome links, so the value side is an `[ASSUMPTION]` with a sensitivity range.

**Risks.** Value fiction; a constant trace trigger means no *when* to learn, so EVSI is evaluated per-decision, never trained.

**Scoring.** Align 4 · Value 4 · Depth 4 · Diff 5 · Data 4 · Prod 4 · Feas 5 · Expl 5 → **4.30**

**Fate.** **Adopted as Layer 5.** The single highest ratio of differentiation to lines of code in PS2.

---

## O6 — Risk-sensitive policy *(CVaR-style conduct tail)*

**What it is.** Optimise expected value **minus a penalty on the bad tail**, where the tail is measured on things the bank actually fears: a third-party disclosure, a wrong-party field visit, a complaint-generating call pattern, and model uncertainty on this specific decision.

```
score = ENV − λ·(P(bad outcome)·cost(bad) + κ·σ_uncertainty)
```

**Why it is a *different* architecture, not a tweak.** It changes *which* actions are admissible: an irreversible action (field visit, notice) is approved only when the belief is *confident*, not merely high-expected-value. On the random arm data this is not academic — optimising RPC naively raised third-party contact from 0.066 to 0.121 `[DATA]`.

**Data.** Rates are measured (third-party 6.9% of attempts overall; 81–93% on reference/employer points `[DATA]`); **rupee costs are `[UNKNOWN]`** — so λ is published and the curve shown. No cited competitor in the reviewed set prices this tail `[INFERENCE]`.

**Risks.** λ by vibes; double counting; using risk aversion to justify doing nothing (mandate: always report what was *not* done and why).

**Scoring.** Align 4 · Value 4 · Depth 4 · Diff 5 · Data 2 · Prod 4 · Feas 4 · Expl 5 → **3.90**

**Fate.** **Adopted as a modifier inside Layer 5/6**, not as a standalone engine.

---

## O7 — Causal / incremental-value design *(uplift on the clean subset)*

**What it is.** Instead of P(RPC), model the **incremental** effect of a contact: who would pay *because* we called, versus who would pay anyway (self-cure). The only defensible instrument is randomised variation.

**Honest data verdict.** The randomisation exists but is unusable in the form available: 2,766 of 51,105 attempts (5.4%) sit on the random arm, 123 of 2,400 accounts, skewed by DPD/outstanding, propensity ≡ 1.0 on the rule arm, and the random arm performs **worse** (RPC 0.134 vs 0.166) `[DATA]`. Effective sample size would be far below what a policy claim needs, and payments have no campaign id (60% within 7 days of an RPC, median 3.3 days, **correlation only** `[DATA]`).

**What a correct build looks like.** Estimate the effect *within* the comparably-randomised subset only, report a confidence interval wide enough to be honest, and state that it cannot license a policy change. Complement: an agent-level propensity check to detect the confounding that is already visible.

**Risks.** Presenting a 5.4% non-random subset as a holdout; the phrase "uplift model" appearing anywhere near a headline number.

**Scoring.** Align 3 · Value 4 · Depth 5 · Diff 4 · Data 1 · Prod 3 · Feas 3 · Expl 2 → **3.20**

**Fate.** **Not built as an engine.** Its constraint becomes a design rule: no claim of incremental effect from this data, and a documented "what a clean experiment would need" appendix (the brief allows an explicit refusal).

---

## Comparison

| | O1 Baseline | O2 Propensity+identity | **O3 Belief-state** | **O4 Allocation-first** | **O5 EVSI** | O6 Risk-sensitive | O7 Causal |
|---|---|---|---|---|---|---|---|
| Align (20) | 3 | 4 | **5** | 4 | 4 | 4 | 3 |
| Value (15) | 2 | 3 | 4 | **5** | 4 | 4 | 4 |
| Depth (15) | 1 | 3 | 3 | **5** | 4 | 4 | 5 |
| Diff (15) | 1 | 2 | 4 | **5** | **5** | **5** | 4 |
| Data (10) | 5 | 5 | **5** | 3 | 4 | 2 | 1 |
| Prod (10) | 3 | 5 | **5** | **5** | 4 | 4 | 3 |
| Feas (10) | 5 | 5 | **5** | 4 | **5** | 4 | 3 |
| Expl (5) | 3 | 4 | **5** | 4 | **5** | **5** | 2 |
| **Weighted** | **2.75** | **3.75** | **4.40** | **4.35** | **4.30** | **3.90** | **3.20** |

**Construction rule for the final architecture.** O3 + O4 + O5 are near-tied at the top and are *not alternatives* — each is the strongest at a different layer (permission, allocation, information). O6 is a modifier on both. O2 supplies the gate shape and the identity decomposition. O1 is the control. O7 is excluded with reasons on the record. This composition, and why combining is legitimate rather than indecisive, is argued in `PS2_ARCHITECTURE_SELECTION.md`; the specification is `PS2_SANKET_SOLUTION_ARCHITECTURE_FINAL.md`.


## XV.5 — File 5 — PS3: seven options scored

*Source file: `PS3_ARCHITECTURE_OPTIONS.md`*

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


## XV.6 — File 6 — the frontier list, every idea labelled

*Source file: `FRONTIER_PS2_PS3_ARCHITECTURES.md`*

# FRONTIER ARCHITECTURES — PS2 & PS3

**Phase 4, File 6 of 13.** Every ambitious idea surfaced in the reverse-engineering pass, each classified **BUILD NOW** (48-hour deliverable), **BUILD IF TIME** (hours 24–48 stretch), **PRODUCTION** (correct answer at bank scale, out of scope here), **RESEARCH ONLY** (do not build; here is what would have to be true).

**Rule applied to every entry.** If it cannot be built, it must still be *stated* — with the reason and the precondition — because the brief treats a justified refusal as a first-class deliverable. Nothing here is included for impressiveness; each entry names the decision it changes.

---

## A. PS2 frontier ideas

### A1 — ContactPointState as a first-class belief object · **BUILD NOW**
A `CONTACT_POINT_STATE` entity: identity posterior, reachability history, last outcome, refusal flags, decay half-life. **Owner:** the contact-point record (in production, the customer-communication system). **Update:** call outcome, trace result, payment, field outcome, time decay. **Decision it changes:** whether an action is permitted at all, and which points are eligible for the day. **Evidence:** the dead-point arithmetic — refusing only the 3rd+ consecutive dead call raises RPC/call 0.1762 → 0.1872 with 12.5% fewer calls `[DATA]`.

### A2 — Refusal ledger with rule codes · **BUILD NOW**
Every non-action (no call, no trace, no visit) recorded with code, reason, inputs, timestamp. **Evidence:** Nyckel/Experian/FICO systems all gate actions explicitly `[S-1][S-3][S-16]`; NYS DTF encodes ~300 legal rules as binary action constraints `[S-33]`. **Decision it changes:** turns compliance from a claim into an auditable artifact, and makes the demo's strongest slide.

### A3 — EVSI trace purchase · **BUILD NOW**
Buy a trace iff expected value of information > ₹104. **Evidence:** 77% of ₹79,650 trace spend produced nothing; predicting trace success is not learnable (CV AUC 0.574 vs 0.772 majority) `[DATA]`. **Decision it changes:** stops spending on information that cannot change any decision.

### A4 — Cost table as configuration with ranges · **BUILD NOW**
A single published parameter file: call minute, dial attempt, field slot, trace, SMS, plus ranges and sources. **Why now:** every downstream economic claim depends on it, and the brief forbids fake precision. **Decision it changes:** makes "expected value" auditable and lets a judge vary it.

### A5 — Day-level capacity allocator (greedy → MILP) · **BUILD IF TIME**
Greedy Lagrangian first, OR-Tools MILP if hours remain: 1,000 accounts / 200 agent-hours / ₹50,000 trace / 50 field slots. **Evidence:** Experian constraint-based optimization `[S-3]`; FICO solver `[S-16]`; mTSP routing in the 2026 MCDA framework `[S-31]`. **Decision it changes:** *which* eligible account gets the scarce minute.

### A6 — Conduct-tail penalty on irreversible actions · **BUILD NOW (simple form)**
`score = ENV − λ·P(bad)·cost(bad)`, with λ published and a sensitivity curve. **Evidence:** optimising RPC naively doubled third-party contact on the randomised subset (0.066 → 0.121) `[DATA]`; CVaR is standard in energy/disaster optimisation `[S-43]`; no reviewed collections vendor prices this publicly `[INFERENCE]`. **Decision it changes:** an irreversible action requires *confidence*, not just high expected value.

### A7 — Event-sourced log + policy replay · **BUILD NOW**
Append-only events; any past decision can be replayed under a new policy. **Evidence:** event sourcing is the industry pattern for auditable decisions `[S-59]`; LIME/xAI dashboards in collections `[S-30]`. **Decision it changes:** makes policy change *safe* — you can show what the new policy would have done.

### A8 — Counterfactual "fewer calls" replay · **BUILD NOW**
Cheap and decisive: replay the incumbent's first-3-calls-only policy and report the outcome at the same resource level using train/test-derived rates `[DATA: derived_ps2_policy_baselines.csv]`. **Decision it changes:** legitimises doing less, which is the hardest political sell in collections.

### A9 — Off-policy evaluation with honest ESS · **BUILD IF TIME**
Use only the clean-propensity subset (123 accounts / 5.1%) and report effective sample size and an interval; state plainly that it cannot license a policy change. **Evidence:** logged bandit feedback is biased and incomplete `[S-39]`. **Decision it changes:** none directly — its value is *not* over-claiming.

### A10 — Portfolio digital twin (week simulation) · **BUILD IF TIME**
Simulate 7 days of dialer/field outcomes under a candidate policy, so capacity and cashflow effects are visible before deployment. **Evidence:** FICO Simulation `[S-16]`; the belief-state model is what makes simulation tractable. **Decision it changes:** capacity planning and policy choice, not individual actions.

### A11 — Adaptive contact-frequency controller · **RESEARCH ONLY**
Learning optimal contact frequency online. **Blocked by:** no randomised arms at usable scale, regulatory exposure on every exploration `[S-28]`, and non-stationary self-cure. **Precondition to revisit:** a legal, consented, propensity-logged pilot.

### A12 — Uplift / incremental-value ranking · **RESEARCH ONLY**
See `PS2_ARCHITECTURE_OPTIONS.md` O7 for the full data verdict. **Precondition:** proper randomisation with logged propensities *including* the control, plus campaign-level payment attribution.

### A13 — Temporal knowledge graph of contact points · **PRODUCTION**
The correct long-run identity substrate: persons, phones, addresses, employers, references as entities with valid-time intervals, queried at decision time. **Evidence:** TransUnion's contact graph `[S-10][S-11]`; Splink/Fellegi-Sunter for edge weights `[S-44]`. **Mid-size version buildable now:** the identity graph layer.

### A14 — Multi-objective Pareto surface · **BUILD NOW**
Instead of one tuned λ, publish the frontier: recovery vs third-party contact vs cost. **Evidence:** multi-criteria decision frameworks are standard in the 2026 academic line `[S-31]`, and the brief demands explicit objectives. **Decision it changes:** the choice of operating point becomes the bank's, not the modeller's.

### A15 — Voice/bot disposition as evidence · **BUILD IF TIME**
3,761 bot attempts exist in the log `[DATA]`; treat bot disposition as a distinct evidence source with its own reliability. **Evidence:** TransUnion voice intelligence `[S-12]`; AI-voice economics are 2–4× headline rates `[S-8bis]`. **Decision it changes:** routing — a bot-confirmed third party should remove the point without an agent minute.

### A16 — Segment-level conformal calibration of P(RPC) · **BUILD NOW**
Distribution-free intervals on the model's own probabilities by segment (town, DPD band, point provenance). **Evidence:** conformal methods give honest coverage where bootstrap does not `[S-53]`. **Decision it changes:** the allocator can refuse to act where the model itself is not calibrated.

### A17 — Complaint/conduct risk predictor · **RESEARCH ONLY**
Predicting which cases generate RBI-ombudsman complaints. **Blocked by:** 85,281 recovery complaints FY24 is a *national* aggregate `[VERIFIED]`, with no labelled case-level complaint data in our dataset. **Precondition:** internal complaint records joined to outreach history.

### A18 — Fairness-constrained allocation across towns · **RESEARCH ONLY**
Equalising service or outcomes across geographies. **Blocked by:** no policy definition of fairness from the client, and our synthetic towns are not real strata. **Precondition:** an agreed fairness metric and a real portfolio.

### A19 — Agent-capacity learning from real logs · **PRODUCTION**
Learn per-agent throughput and skill-based routing. **Blocked here by:** `agents.csv` gives only 30 synthetic agents with no shift log. **Decision it changes:** in production, minutes per call.

---

## B. PS3 frontier ideas

### B1 — Per-stratum conformal radius table · **BUILD NOW**
Publish `P(truth within r)` by vendor `precision` × town, two-sample validated `[DATA]`. **Decision it changes:** the field app's search radius and the PS2 field-slot decision. **Why now:** it is the cheapest defensible artifact in PS3 and it is already computed.

### B2 — Field-evidence posterior fusion · **BUILD NOW**
GPS trail + dwell + outcome sign + media sanity → posterior; 385 m → 29 m on met-someone visits `[DATA]`. **Decision it changes:** every future visit in that street starts from a better pin.

### B3 — Evidence integrity gate · **BUILD NOW**
Mock-location flag, teleport check, duplicate-media hash, trail-vs-check-in distance; 645 check-ins (11.6%) are >500 m from their own trail and FA009 has 162/172 duplicate photo hashes `[DATA]`. **Evidence:** spoofing is caught by cross-signal inconsistency `[S-58]`. **Decision it changes:** whether this visit is allowed to teach the system anything.

### B4 — Two-confirmation promotion · **BUILD NOW**
Two independent, integrity-passing confirmations promote a coordinate to canonical; everything else stays a prior. **Evidence:** logistics auto-update after two confirmations `[S-56]`. **Decision it changes:** the canonical coordinate store, and therefore licence exposure (B13).

### B5 — Address parse + canonicalisation · **BUILD IF TIME**
Open Indic NER + rule normalisation `[S-46][S-13bis]`. **Decision it changes:** duplicate detection and retrieval quality.

### B6 — Confirmed-pin retrieval index · **BUILD IF TIME**
The compounding asset: every confirmed coordinate improves every future query in that building/street `[S-52]`. **Decision it changes:** how often an address needs a field visit at all.

### B7 — Building-level identity graph · **BUILD IF TIME**
3,117 addresses for 2,400 accounts; 74 repeated phone ids across accounts `[DATA]` → fix the building, fix every unit. **Evidence:** Fellegi-Sunter/Splink explainable match weights `[S-44]`. **Decision it changes:** "confirm 40 buildings, not 1,200 addresses".

### B8 — Distribution-valued output (`P(within 200 m)`) · **BUILD NOW (discrete)** / PRODUCTION (continuous)
The PS2↔PS3 contract. Even a 3-bucket version (high/medium/low confidence + radius) is enough to make the field-slot decision rational. **Decision it changes:** the allocator can price a visit against its expected location gain.

### B9 — Active-learning task selection · **BUILD IF TIME**
Choose the next address to verify by uncertainty reduction × account value / visit cost. **Decision it changes:** turns a visit queue into an acquisition strategy.

### B10 — HMM map matching · **RESEARCH ONLY**
Blocked by **no road graph**; coordinates are a local metric plane with no polygons `[DATA]` and the paper standard requires a segment graph `[S-54]`. **Precondition:** an OSM/road-network extract for the three towns. **Cheaper substitute shipped:** stationary-cluster stop detection.

### B11 — Hierarchical cell prediction (GeoIndia-style H3 model) · **RESEARCH ONLY**
Blocked by a proprietary 67 M-address corpus `[S-47bis]`; with 3,117 addresses the hierarchy is learnable only to locality level — the stratum the vendor already gives us. **What we steal:** the *output contract* (hierarchy + bound), not the model.

### B12 — Cross-signal GPS spoof fingerprinting · **PRODUCTION**
Mock-location detection, root/emulator, GPS-vs-IP mismatch, teleport, duplicate media `[S-58]`. Our dataset supports the *rule* version (B3); a learned fingerprint needs device telemetry we do not have.

### B13 — Provider cache/compliance layer · **PRODUCTION**
Pluggable providers, ≤30-day vendor cache, no permanent vendor-content storage, audit log `[S-48][S-51][S-65]`. **Decision it changes:** legal approval and the definition of "our address record".

### B14 — Geocode confidence calibration across towns · **BUILD NOW**
Stratum × town coverage monitoring; the two independent samples already agree `[DATA]`, which is the calibration evidence. **Decision it changes:** whether the radius table can be trusted in a new town.

### B15 — Human-in-the-loop address steward queue · **PRODUCTION**
Low-confidence, high-value addresses routed to a data steward before a field slot is spent. **Decision it changes:** cost per confirmed address; prevents the most expensive mistakes from reaching the field.

---

## C. Cross-cutting frontier ideas

### C1 — The belief-handoff protocol (PS2 ⇄ PS3) · **BUILD NOW**
Two contracts only: PS3 publishes `P(location within r)` per address; PS2 publishes `field-slot value of certainty` and returns confirmed-visit events. Everything else stays decoupled. **Decision it changes:** makes integration real without merging two systems.

### C2 — Single event vocabulary across both PS · **BUILD NOW**
`CALL_COMPLETED`, `TRACE_RETURNED`, `PAYMENT_RECEIVED`, `VISIT_COMPLETED`, `VISIT_REJECTED_INTEGRITY`, `COORDINATE_PROMOTED`, `REFUSAL_RECORDED`. **Decision it changes:** one log, two views — the mechanism that keeps the integrated file from being two boxes joined `[S-59]`.

### C3 — Simulation-in-the-loop demo · **BUILD IF TIME**
Feed the twin with a week of synthetic days so judges see the policy adapt rather than a static chart.

### C4 — Full reinforcement learning of the contact policy · **RESEARCH ONLY**
Blocked by: no exploration data, no reward attribution, no cost model, regulatory exposure on every experiment, and the brief's explicit prohibition on RL for show. **Precondition:** a legal pilot with logged propensities and campaign-level attribution, then a constrained-MDP formulation with the legal rules as action-availability features `[S-32][S-33]`.

---

## D. Classification summary

| Class | Count | Entries |
|---|---|---|
| **BUILD NOW** | 20 | A1 A2 A3 A4 A6 A7 A8 A14 A16 · B1 B2 B3 B4 B8 B14 · C1 C2 · (plus A13-mid as the identity layer) |
| **BUILD IF TIME** | 9 | A5 A9 A10 A15 · B5 B6 B7 B9 · C3 |
| **PRODUCTION** | 6 | A13 A19 · B12 B13 B15 · (B8-continuous) |
| **RESEARCH ONLY** | 9 | A11 A12 A17 A18 · B10 B11 · C4 · (plus the two rejected in File 2/3: contextual bandit and full C-MDP) |

**How this table is used.** The `BUILD NOW` set is the demo script and the scope of `PS2_SANKET_SOLUTION_ARCHITECTURE_FINAL.md` / `PS3_SUTRA_SOLUTION_ARCHITECTURE_FINAL.md`. `BUILD IF TIME` is the stretch list in the execution plan. `PRODUCTION` and `RESEARCH ONLY` entries each appear in the final documents as an explicit *out-of-scope with reasons* section — which is what a serious BFSI platform document contains and what a hackathon deck usually omits.


## XV.7 — File 7 — PS2 selection and its arithmetic

*Source file: `PS2_ARCHITECTURE_SELECTION.md`*

# PS2 — ARCHITECTURE SELECTION

**Phase 4, File 7 of 13.** The decision, the arithmetic behind it, and the record of what was rejected.

---

## 1. Criteria and weights (as specified in the brief — not re-tuned)

| # | Criterion | Weight | What it means at scoring time |
|---|---|---|---|
| C1 | Official PS alignment | **20%** | Does it satisfy the stated PS2 requirement IDs (R1–R13) directly, not tangentially? |
| C2 | Business value | **15%** | Does it change the real collections workflow (calls, visits, rupees, conduct)? |
| C3 | Technical depth | **15%** | Is there substance a senior engineer would respect — without impersonating research? |
| C4 | Differentiation | **15%** | Would a judge who has seen 40 submissions see this for the first time? |
| C5 | Dataset support | **10%** | Can the audited dataset actually train/validate it, with no invented fields? |
| C6 | Production realism | **10%** | Could this sit inside a BFSI platform without an asterisk? |
| C7 | Hackathon feasibility | **10%** | Buildable and demonstrable in 48 hours, including the failure path? |
| C8 | Explainability | **5%** | Can a decision, a refusal and a probability be defended to an auditor? |

Scores 1–5. Weighted score = Σ (score × weight).

---

## 2. Candidate scores

Architectures from `PS2_ADVANCED_ARCHITECTURE_RESEARCH.md` (A1–A12) and options from `PS2_ARCHITECTURE_OPTIONS.md` (O1–O7) map as: A1/O1 baseline · A2/O2 two-stage · A3 identity graph · A4/O3 state machine · A5 NBA · A6/O2 gate+EV · A7 bandit · A8 C-MDP · A9/O5 EVSI · A10/O4 allocator · A11/O6 risk-sensitive · **A12 hybrid** · O7 causal.

| Candidate | C1 20 | C2 15 | C3 15 | C4 15 | C5 10 | C6 10 | C7 10 | C8 5 | **Weighted** |
|---|---|---|---|---|---|---|---|---|---|
| **A12 Hybrid belief-state + optimization** | 5 | 5 | 5 | 5 | 4 | 5 | 3 | 5 | **4.60** |
| A10 / O4 Portfolio allocator alone | 4 | 5 | 5 | 5 | 3 | 5 | 4 | 4 | 4.35 |
| A6 Constraint + EV alone | 5 | 4 | 3 | 4 | 4 | 5 | 5 | 5 | 4.30 |
| A9 / O5 EVSI alone | 4 | 4 | 4 | 5 | 4 | 4 | 5 | 5 | 4.30 |
| A4 / O3 State machine alone | 5 | 4 | 3 | 4 | 5 | 5 | 5 | 5 | **4.40** |
| A3 Identity graph alone | 4 | 3 | 3 | 4 | 5 | 4 | 3 | 3 | 3.60 |
| A11 / O6 Risk-sensitive alone | 4 | 4 | 4 | 5 | 2 | 4 | 4 | 5 | 3.90 |
| O2 Two-stage propensity + gate | 4 | 3 | 3 | 2 | 5 | 5 | 5 | 4 | 3.75 |
| A2 Two-stage contactability | 4 | 3 | 2 | 2 | 5 | 4 | 5 | 4 | 3.50 |
| O7 Causal / uplift | 3 | 4 | 5 | 4 | 1 | 3 | 3 | 2 | 3.20 |
| A5 NBA argmax | 4 | 3 | 2 | 2 | 2 | 3 | 4 | 3 | 2.85 |
| A8 Constrained MDP | 3 | 4 | 5 | 3 | 1 | 3 | 1 | 1 | 2.90 |
| A1 / O1 Classifier baseline | 3 | 2 | 1 | 1 | 5 | 3 | 5 | 3 | 2.75 |
| A7 Contextual bandit | 3 | 3 | 4 | 3 | 1 | 2 | 1 | 1 | 2.45 |

**Worked example (A12).** `0.20(5) + 0.15(5) + 0.15(5) + 0.15(5) + 0.10(4) + 0.10(5) + 0.10(3) + 0.05(5) = 1.00 + 0.75 + 0.75 + 0.75 + 0.40 + 0.50 + 0.30 + 0.25 = 4.60`.

---

## 3. Decision

### 3.1 The architecture

**A12 — Hybrid belief-state + optimization**, built as **six layers in a fixed order**, with the composition justified below the scores (the top three candidates are within 0.30 and are layers, not rivals).

```text
L0  EVENT LOG (append-only)                     owner: platform        source: dial_attempts, skip_traces, payments, field_visits
L1  STATE ESTIMATION  ContactPointState        owner: point record    update: outcome events + time decay
L2  IDENTITY / EVIDENCE FUSION  P(borrower)    owner: identity service source: provenance, verification, behaviour, graph
L3  PREDICTION  calibrated multi-class          owner: model service   label: disposition (pre-dial features only)
L4  POLICY GATE  rules → permission + refusals  owner: compliance rulebook  output: rule-coded refusals
L5  ECONOMICS  EV → EVSI (trace/verify) → CVaR penalty → cap/claim
L6  ALLOCATION  day-level greedy → MILP under capacity, frequency, notice
L7  EXECUTION + FEEDBACK  dialer/field APIs → outcomes + overrides → back to L0
```

### 3.2 Why layers rather than the single best-scoring option

- The three top candidates (**A12** 4.60, **A4/O3** 4.40, **A10/O4** 4.35) score high on *different criteria*: O3 owns alignment, realism and explainability; O4 owns value, depth and differentiation; A9/O5 owns differentiation at the lowest cost. Selecting any one of them alone loses a criterion where another is strongest, and the brief explicitly asks for a system, not a model.
- The layers are **independently refusable**: if L5's cost table is deemed unapproved, the system runs L0–L4 and still beats the baseline and still produces refusals. That property — graceful degradation to a *smaller honest system* — is why composition is safe here and would not be in a system where the layers are entangled by design.
- Every layer is justified by a measured number from the audited dataset (see §5).

### 3.3 Why the alternatives were rejected (record)

| Rejected | Reason |
|---|---|
| **A7 Contextual bandit** | Propensities are degenerate (≡1.0 on 94.6% of attempts); the random arm is 5.1% of attempts, skewed by DPD/outstanding, and *worse* (RPC 0.134 vs 0.166); reward is not attributable (no campaign id). ESS would be unusable. Learning online by contacting real borrowers is a regulatory exposure. `[DATA]` |
| **A8 Constrained MDP** | The reference deployment consumed ≈$5 M research + ≈$4 M engagement `[S-33]`; our horizon is 3 months of one policy. Retained conceptually: legal rules become states (L1) and action-availability flags (L4) `[S-32]` |
| **O7 Causal / uplift** | The randomisation is not clean enough to license a policy claim; no clean control arm. Retained as a design rule: no incremental-effect claims, plus a documented precondition appendix |
| **A5 NBA argmax** | Argmax without costs and without a `wait` option manufactures pressure to act; Pega's own arbitration weights (P×C×V×L) contain no cost term `[S-20]` |
| **A2 Two-stage contactability** | Subsumed: the dataset supports one multi-class model whose decomposition is reported afterwards. Two models would double the calibration burden for presentation value only |
| **A1 classifier baseline** | Retained as the running control, not as the answer |

### 3.4 The single biggest architectural bet

**That a measured refusal is worth more than a measured prediction.** The evidence: the dead-point rule alone gives +6.2% RPC per call with −12.5% calls `[DATA]`; the EVSI rule touches 77% wasted trace spend `[DATA]`; and no reviewed competitor publishes a refusal ledger. If this bet is wrong, the system still ships L0–L3 and is a competent baseline-plus-state-machine — which is the point of the layering.

---

## 4. Component-level selection (what was chosen for each layer, and what was not)

| Layer | Chosen | Considered and rejected | Why |
|---|---|---|---|
| L1 state | Explicit finite-state machine over 16 dispositions `[DATA]` | Learned hidden state (HMM/RL) | 3 months, one policy, no reward attribution; an auditor can read a state table |
| L2 identity | Provenance priors + behavioural evidence + shared-number edge detection; CV AUC 0.899 / 0.813 / 0.508 baseline `[DATA]` | GNN over the contact graph | The graph's only claim to value is a *refusal* on shared numbers (43.2% of attempts `[DATA]`), which needs edges, not embeddings |
| L3 prediction | Single calibrated GBM, multi-class over dispositions, pre-dial features only | Per-action models; deep sequence model | Test AUC 0.670 honest vs 0.933 leaked `[DATA]`; a sequence model on 51k rows with this label noise is a liability |
| L4 gate | Closed-vocabulary rule codes, refusals logged | Fuzzy/soft compliance scoring | The brief: never put fuzzy logic inside a legal gate. Discipline: rules are binary and auditable |
| L5 economics | EV + EVSI + one-λ CVaR term, all with published ranges | Full CVaR optimisation; dynamic programming | Ranges + sensitivity is honest; a precise CVaR over unmeasured rupee costs is fictional precision |
| L6 allocation | Greedy Lagrangian, upgrade to OR-Tools MILP | RL scheduler | MILP is provably optimal for the stated LP relaxation; RL scheduler would need the data we do not have |
| L7 feedback | Event log + override reasons + refusal ledger | A/B experimentation platform | No experimentation licence; event sourcing gives replay, which is what an auditor actually wants |

---

## 5. Evidence table — every layer against a measured fact

| Layer | Measured fact it exploits | Source |
|---|---|---|
| L1 | 3rd+ consecutive dead: RPC/attempt 0.180 → **0.067**; refusal at 3+ raises pooled RPC/call 0.1762 → 0.1872, −12.5% calls | `[DATA]` |
| L2 | P(borrower) by provenance 1.00 / 0.73 / 0.67 / 0.30 / 0.16 / 0.07; reference+employer = 14% of calls, 81–93% third-party | `[DATA]` |
| L3 | Honest pre-dial AUC 0.670 (GBM) / 0.604 (LR); leakage 0.933; ΔAUC prior_rpc 0.0894 > self-relation 0.0275 > hour 0.0274 | `[DATA]` |
| L4 | No compliance field exists in the data → configuration + refusal log `[GAP]`; requirement R6 is regulatory `[VERIFIED]` | `[DATA]`, Phase-1 |
| L5 | ₹104/trace, 22.8% hit, ₹455/hit, ₹305/RPC, 77% wasted; trace-success model AUC 0.574 vs 0.772 majority | `[DATA]` |
| L6 | Capacity/trace-budget absent → what-if parameters (1,000 / 200 h / ₹50,000 / 50 slots) | `[GAP]` + brief |
| L7 | No campaign id; 60% of payments within 7 days of an RPC (median 3.3 d) → correlation only | `[DATA]` |

---

## 6. Risk register for the selected architecture

| Risk | Severity | Mitigation built into the design |
|---|---|---|
| Cost table challenged as invented | High | Publish as labelled parameters with ranges + one-line sensitivity; every EV shows the range |
| Model AUC modest (0.670) and over-claimed | High | Report honestly, compare to 0.604 LR and to the leaked 0.933 as an explicit anti-pattern |
| State machine too conservative → over-suppression | Medium | Refuse only at 3+ consecutive dead; report the counterfactual "what suppression cost us" |
| Scope creep into seven components | High | BUILD NOW list frozen in `FRONTIER_PS2_PS3_ARCHITECTURES.md`; everything else labelled |
| Judges read "belief state" as jargon | Medium | Demo shows one account's state timeline changing after a call, a trace and a payment |
| Integration with PS3 becomes cosmetic | Medium | Two hard contracts (C1/C2 in File 6) with a named field and a named event |

## 7. What would change this decision

1. A client-supplied **cost and capacity table** → promote L6 to a full MILP as the centrepiece.
2. A **clean randomised pilot with campaign-level attribution** → reopen A7/O7 (bandit/uplift) with a real ESS budget.
3. **Internal complaint-labelled case data** → the conduct predictor (A17) becomes buildable and moves from RESEARCH ONLY.
4. A **target operating point** (e.g. "no more than X% third-party contact") from the client → λ becomes a constraint rather than a penalty.

**Cut-line if the build slips:** L0 L1 L2 L4 L5(EV) sharpen and ship; L3 shrinks to a logistic baseline; L6 degrades to a ranked list with a published budget cap; EVSI ships as a decision rule even if the allocator does not. Under no cut does the submission lose the refusal ledger.


## XV.8 — File 8 — PS3 selection and its arithmetic

*Source file: `PS3_ARCHITECTURE_SELECTION.md`*

# PS3 — ARCHITECTURE SELECTION

**Phase 4, File 8 of 13.** The decision, the arithmetic, and what was rejected.

---

## 1. Criteria and weights (identical to PS2, per the brief)

Official PS alignment **20%** · Business value **15%** · Technical depth **15%** · Differentiation **15%** · Dataset support **10%** · Production realism **10%** · Feasibility **10%** · Explainability **5%**. Scores 1–5.

---

## 2. Candidate scores

From `PS3_ADVANCED_ARCHITECTURE_RESEARCH.md` (G1–G15) and `PS3_ARCHITECTURE_OPTIONS.md` (P1–P7).

| Candidate | C1 20 | C2 15 | C3 15 | C4 15 | C5 10 | C6 10 | C7 10 | C8 5 | **Weighted** |
|---|---|---|---|---|---|---|---|---|---|
| **G15 Hybrid (parse→retrieve→rank→posterior→feedback)** | 5 | 5 | 5 | 5 | 4 | 5 | 4 | 5 | **4.75** |
| **G8 / P2 Field-evidence fusion** | 5 | 5 | 4 | 5 | 5 | 4 | 5 | 5 | **4.70** |
| **G10 / P1 Conformal, stratum-calibrated radius** | 5 | 5 | 4 | 5 | 4 | 5 | 5 | 5 | **4.65** |
| **G12 / P5 Compounding confirmed-pin map** | 4 | 5 | 4 | 5 | 4 | 5 | 5 | 4 | **4.55** |
| G/ P6 Decision-coupled routing | 5 | 5 | 4 | 5 | 4 | 4 | 3 | 4 | 4.45 |
| G3 / P3 Parse-then-geocode / retrieve+rank | 5 | 4 | 3 | 3 | 5 | 4 | 4 | 5 | 4.20 |
| G13 / P7 Provider + compliance layer | 5 | 3 | 2 | 3 | 5 | 5 | 5 | 4 | 4.05 |
| G11 / P4 Probabilistic posterior engine | 4 | 4 | 5 | 5 | 3 | 4 | 3 | 3 | 3.95 |
| G4 Retrieval + ranking | 4 | 4 | 3 | 4 | 4 | 4 | 5 | 4 | 3.95 |
| G14 Place identity graph | 4 | 4 | 3 | 4 | 4 | 4 | 3 | 4 | 3.75 |
| G6 Hierarchical cell prediction | 4 | 4 | 5 | 5 | 1 | 4 | 1 | 4 | 3.45 |
| G5 Learned candidate ranker | 3 | 3 | 4 | 3 | 2 | 3 | 3 | 3 | 2.95 |
| G9 Map matching (HMM) | 3 | 3 | 5 | 4 | 1 | 3 | 1 | 3 | 2.90 |
| G2 Multi-vendor consensus | 3 | 3 | 3 | 2 | 2 | 4 | 3 | 4 | 2.85 |
| G7 Landmark anchoring | 3 | 2 | 2 | 2 | 2 | 2 | 2 | 3 | 2.25 |
| G1 Vendor wrapper | 2 | 1 | 1 | 1 | 5 | 3 | 5 | 2 | 2.20 |

**Worked example (G15).** `0.20(5)+0.15(5)+0.15(5)+0.15(5)+0.10(4)+0.10(5)+0.10(4)+0.05(5) = 1.00+0.75+0.75+0.75+0.40+0.50+0.40+0.25 = 4.80` — capped to **4.75** in the table after the feasibility deduction recorded in §6 (the rank-retrain step is cut).

---

## 3. Decision

### 3.1 The architecture

**G15 — SUTRA: parse → retrieve → rank → posterior → conformal radius → field fusion → feedback**, with **P1 (calibrated truth) shipped unconditionally** because it is the one layer that is already computed and cannot fail.

```text
S0  INGEST      address text, vendor result + precision label, PIN/locality/town gazetteer
S1  PARSE       script/abbreviation normalisation → administrative levels            [open Indic NER]
S2  RETRIEVE    candidates from confirmed-pin index + gazetteer + landmark priors    [BM25/rules first]
S3  RANK        rule-first scoring (PIN > locality > street > token overlap); abstain when thin
S4  PRIOR       vendor point ⊗ stratum kernel (rooftop 37.7 / street 134.9 / locality 367.4 / pincode 1,336.5 m)
S5  INTEGRITY   mock-location · teleport · duplicate media · trail-vs-checkin distance (645 check-ins >500 m flagged)
S6  FUSION      stationary-cluster stop detection → dwell-weighted, outcome-signed posterior
S7  UNCERTAINTY per-stratum conformal radius + published coverage monitor
S8  CONTRACT    P(truth within 200 m) per address → PS2 field-slot decision; confirmed visits → PS2 state
S9  FEEDBACK    2 independent confirmations → promote coordinate → improves S2 index and S4 priors
```

### 3.2 Why this composition

- The top four candidates differ by *role*, not by quality: **G8** is the accuracy engine, **G10/P1** is the honesty engine, **G12/P5** is the compounding engine, **G3/G4** is the hygiene prerequisite. Any single one alone leaves a hole the brief explicitly asks us to fill ("a returned pin with no interval is not a decision input").
- **The decisive measurement is negative.** Our own oracle test says public free-text data cannot beat **370 m** median `[DATA]`; therefore no combination of retrieval and ranking can be the differentiator, and the architecture must be built around *where evidence is spent*, not around *which geocoder is called*. That is why S5–S9 dominate S2–S3 in scope.
- **P1 ships even if everything else slips**, because it is the only layer whose correctness is guaranteed by two independent samples `[DATA]` and it changes a downstream decision (search radius, field-slot approval) on day one.

### 3.3 Why the alternatives were rejected (record)

| Rejected | Reason |
|---|---|
| **G9 HMM map matching** | No road graph exists in the data; coordinates are a local metric plane with no polygons `[DATA]`. Precondition: an OSM extract for the three towns. Cheaper substitute shipped: stationary-cluster stop detection. `[S-54]` |
| **G6 Hierarchical cell prediction** | Not reproducible: proprietary 67 M-address corpus `[S-47bis]`. With 3,117 addresses the model would learn locality level — exactly the stratum the vendor already reports. **We adopt the output contract (hierarchy + bound), not the model.** |
| **G7 Landmark anchoring** | Measured failure: 4,093 m median, worse than baseline in 90% of cases `[DATA]`. Landmarks retained only as prior/telephone-aid for the field task |
| **G5 Learned candidate ranker** | Oracle ceiling 370 m over the same candidates `[DATA]`; 100 surveyed labels overfit instantly. Sold as a *rule-first* ranker with abstention, not as a learned model |
| **G2 Multi-vendor consensus** | Improves robustness, not accuracy; requires 2–3 contracts and multi-licence review. Retained as an optional provider strategy inside S0/S7 |
| **G11 Probabilistic posterior engine** | Adopted *in substance* at S6/S8 (a discrete posterior with a radius) but not as a continuous-grid product: grid resolution would be fictional precision, and explaining a density to a field officer fails the practical test |
| **G1 Vendor wrapper** | Forbidden by the brief as a complete answer, and correctly: it ships a 1,336 m pin in the same shape as a 37.7 m one |

### 3.4 The single biggest architectural bet

**That trusting field evidence correctly — and refusing to trust it when it is contaminated — is worth an order of magnitude more than any geocoding improvement available to us.** The measured basis: 385 m → **29 m** `[DATA]`; the countervailing evidence that 11.6% of check-ins are inconsistent with their own trail and one agent has 26.6% duplicate media `[DATA]`. If the bet is wrong, S1–S4 still ship and PS3 becomes a well-parsed, honestly-bounded geocoder — a defensible, if less striking, product.

---

## 4. Component-level selection

| Stage | Chosen | Rejected | Why |
|---|---|---|---|
| S1 parse | Open Indic NER + rule normalisation | Commercial address-parse API | Terms/quota risk, and the parse must be explainable per field `[S-46]` |
| S2 retrieve | Confirmed-pin index first, gazetteer second, landmarks as priors | Vector-only retrieval | Confirmed pins are our own asset and licence-clean; embeddings add ambiguity without ground truth |
| S3 rank | Rules (PIN > locality > street > tokens) + abstention | Learned ranker | 100 labels; oracle ceiling 370 m — a learned ranker cannot beat the ceiling and cannot be validated |
| S4 prior | Vendor point + measured stratum kernel | Replacing the vendor point | Vendor pin is a legitimate prior; replacing it wholesale throws away signal |
| S5 integrity | Deterministic rules (mock, teleport, duplicate hash, trail distance) | Learned spoof fingerprint | No device telemetry; rules match published practice `[S-58]` |
| S6 fusion | Dwell-weighted, outcome-signed stationary clusters | Trail centroid; full Bayesian grid | Centroid is wrong for a door; the grid is unnecessary once the decision is a radius |
| S7 uncertainty | Per-stratum conformal radii + coverage monitor | Global 90% radius; parametric error model | Conformal coverage beats bootstrap (93.67% vs 68.33% empirical at 90% nominal) `[S-53]` |
| S8 contract | `P(within 200 m)` + confirmed-visit events | Sharing full coordinates with PS2 | Two narrow contracts keep the systems decoupled and the demo honest |
| S9 feedback | Two independent confirmations → promotion | Immediate overwrite on one visit | Logistics practice `[S-56]`; prevents a bad visit poisoning the map |

---

## 5. Evidence table — every stage against a measured fact

| Stage | Measured fact | Source |
|---|---|---|
| S3/S4 | Vendor baseline median 376.4 m, p90 839 m, 9% <100 m; stratum medians 37.7 / 134.9 / 367.4 / 1,336.5 m (two samples agree) | `[DATA]` |
| S2/S3 | Free-data oracle ceiling 370 m, 2% <100 m; naive POI snap 4,093 m | `[DATA]` |
| S5 | 645 check-ins (11.6%) >500 m from own trail; FA009 162/172 duplicate photo hashes vs ≤1% elsewhere | `[DATA]` |
| S6 | Met-someone visits 385 m → 29 m, 87% improve, 82% <100 m; not_traceable check-ins 1,603 m from truth with 2-min dwell | `[DATA]` |
| S6 inputs | Median 26 GPS points/visit, median accuracy 9.8 m | `[DATA]` |
| S7 | Conformal spatial prediction: 93.67% empirical coverage at 90% nominal | `[S-53]` |
| S8 | PS2 needs a probability to price a field slot; brief's 50-slot capacity | `[GAP]` + brief |
| S9 | Two-confirmation auto-update in logistics practice | `[S-56]` |
| Licence envelope | Google lat/lng cache ≤30 days, no permanent content storage; Nominatim 1 req/s; NDSAP non-commercial | `[S-48][S-51][S-65]` |

---

## 6. Risk register

| Risk | Severity | Mitigation |
|---|---|---|
| Judges ask "isn't this just using a geocoder?" | High | §3.3 of `PS2_PS3_DATASET_REVIEW.md` reconciliation + the 370 m oracle result shown as a slide |
| Field evidence available for only part of the portfolio | High | Report coverage explicitly; everywhere else deliver the honest radius, never a fake point |
| Integrity rules over-filter good visits | Medium | Publish false-positive rate on the 1,477 visited addresses; threshold tunable and logged |
| Fusion perceived as averaging GPS | Medium | Demo one address: trail → stop detection → posterior → radius change, with each weight visible |
| Radius table over-claimed in a new town | Medium | Coverage monitor per town; table labelled calibration, not ground truth |
| Retrieval index has nothing in it on day one | Medium | Day-one index = gazetteer; the confirmed-pin index grows during the demo |
| **Feasibility** — full G15 with rank retraining exceeds 48 h | Medium | **Rank retraining cut** (hence the −0.05 in §2); rule-first ranker only |

## 7. What would change this decision

1. **A road-network extract for the three towns** → G9 (HMM map matching) becomes buildable and S6 sharpens materially.
2. **A labelled address corpus (≥10k, real)** → G6/G5 reopen; the hierarchy model becomes the centrepiece instead of the contract.
3. **A second commercial provider contracted** → G2 enters S0 and cross-provider disagreement becomes a real confidence feature.
4. **Actual device integrity telemetry** (mock flag, root, IP) → S5 upgrades from rules to a scored integrity model.

**Cut-line if the build slips:** S4 + S7 + S8 ship first (calibrated truth and the PS2 contract), then S5 + S6 (integrity and fusion), then S9 (promotion), then S1–S3 (parse/retrieve/rank). The submission must never degrade to "we called an API".


## XV.9 — File 9 — SANKET final architecture (30 sections)

*Source file: `PS2_SANKET_SOLUTION_ARCHITECTURE_FINAL.md`*

# SANKET — PS2 SOLUTION ARCHITECTURE (FINAL)

**Phase 4, File 9 of 13.** 30 sections, as mandated. This is the deliverable architecture, replacing the Phase-2 hypothesis in `PS2_SANKET_SOLUTION_ARCHITECTURE.md`.

**Companion files:** `PS2_ADVANCED_ARCHITECTURE_RESEARCH.md` (12 architectures compared) · `PS2_ARCHITECTURE_OPTIONS.md` (7 options scored) · `PS2_ARCHITECTURE_SELECTION.md` (the decision and its arithmetic) · `FRONTIER_PS2_PS3_ARCHITECTURES.md` (every idea labelled BUILD NOW / BUILD IF TIME / PRODUCTION / RESEARCH ONLY) · `SIMILAR_SYSTEMS_REVERSE_ENGINEERING.md` (the systems this borrows from) · `PS2_PS3_DATASET_REVIEW.md` (the data verdict).

**Component labelling convention used throughout** *(the brief's Part M test — every component answers five questions)*:
`①what real system uses it` · `②what problem it solves` · `③what feeds it` · `④what if it is wrong` · `⑤why a simpler component cannot replace it`.

---

## 1. Problem, and the official statement it must satisfy

CreditNirvana's PS2 asks, in the client's own words, for the system that decides **which contact point to use, whether it is reachable, whether it is the right party, and what the next action should be** — with the trace/visit decision governed by economics rather than by an attempt counter. The official statement and our framing are reconciled line by line in `PS2_PS3_DATASET_REVIEW.md` §2; nothing below assumes a requirement the statement does not contain.

Three properties of the problem make it hard, and each one is a component later in this document:

1. **The state is latent.** Whether a phone belongs to the borrower, a relative, or a stranger is not observed — it is inferred from provenance, behaviour and outcomes, and it changes over time (recycled numbers, changed hands).
2. **The action space is priced but unpriced.** Calling, tracing, field-visiting and waiting have different costs and different irreversibility, and the client's system has no cost model in it.
3. **Conduct is a hard constraint, not a term in an objective.** From 1 Jan 2027 the amended RBI Directions impose calling windows, pre-visit notice, empanelment, certification and record-keeping on the recovery process `[VERIFIED]`. A debt-disclosing action against an unverified identity is not "a low-value action"; it is a prohibited one.

## 2. What this system is, in one paragraph

**SANKET** is a *decision system*, not a model. It maintains a belief state for every contact point and every account, fuses identity and behavioural evidence into calibrated probabilities, gates every action through a hard compliance rulebook, prices the remaining actions in expected rupees (including the price of *information* — traces and verifications are purchases), applies a conduct-tail penalty to irreversible actions, and then allocates the day's scarce capacity — agent minutes, trace budget, field slots — against that value. Every outcome, every refusal and every override is written to an append-only event log, which is both the audit artifact and the input to the next belief update.

## 3. Users and consumers

| Consumer | What they see | Why they care | Interaction |
|---|---|---|---|
| Allocation analyst | Tomorrow's plan: N calls by hour bucket, M field slots, ₹X trace budget, plus the refusal summary | Cure rate, cost per rupee recovered | Reviews exceptions, adjusts capacity |
| Collections supervisor | The exception queue: accounts the system refused to auto-touch, with the rule code | Defensibility, team utilisation | Approves or escalates |
| Compliance officer | Decision records, refusal ledger, conduct counters, hours-of-contact distribution | Regulatory inspection (effective 1 Jan 2027) `[VERIFIED]` | Audits; can freeze rule codes |
| Field officer | Address confidence band + visit priority (fed by PS3) | Whether the visit is worth the trip | Returns outcome + evidence |
| Dialer / orchestrator (machine) | Per-point action + permitted window + attempt ceiling | Execution | Emits outcomes back |
| Model risk / audit | Calibration reports, coverage by segment, event-sourced replay of any decision | Model governance | Queries, replays |
| **Not the borrower** — the borrower is the subject of the decision and the party this system exists to protect |

## 4. Business objective, stated as an optimisation problem

```text
Maximise   Σ_t  [ recovered_t − λ_conduct · ConductTail_t − OperatingCost_t ]
subject to: 0 regulatory breaches (hard) · capacity limits (hard, per skill/hour)
            · attempt/frequency ceilings (hard) · one action per point per window (hard)

ConductTail = CVaR_α over the loss distribution of {wrong-party contact, disclosure event,
              out-of-window contact, un-notified visit}   — α and λ published
```

**Primary KPI:** rupees recovered per rupee spent (all-in: agent minute, dial attempt, trace, field slot).
**Secondary KPIs:** right-party-contact rate per attempt; third-party contact rate (**must not rise** — the naive-RPC-maximising policy raises it from 0.066 to 0.121 `[DATA]`); trace spend per successful trace (today ₹455 `[DATA]`); wasted-visit rate; complaints per 10,000 contacts.
**Anti-KPI, reported alongside:** attempts per account and contacts per week — recovering the same money with *fewer* contacts is a win, not a draw.

## 5. Non-goals and explicit refusals

| Not building | Why | What would change it |
|---|---|---|
| Contextual bandit / online policy learning | Propensities degenerate (≡1.0 on 94.6% of attempts), random arm 5.1% and worse (0.134 vs 0.166), no reward attribution (no campaign id) `[DATA]` | A legal pilot with logged propensities + campaign-level payment attribution |
| Constrained MDP over the full collection journey | 3 months of one policy; the reference deployment consumed ≈$5 M research + ≈$4 M engagement `[S-33]` | Multi-year longitudinal data + a research budget |
| Uplift / incremental-value claims | The randomisation is confounded (skewed DPD/outstanding, 123 accounts) `[DATA]` | Clean randomisation with a real control arm |
| LLM-driven agents inside the decision loop | Latency, cost, non-determinism, auditability; nothing in the requirements needs generation | A specific document-understanding task with a deterministic fallback |
| A voice bot re-build | Out of PS2 scope; 3,761 bot attempts already exist in the log and are consumed as evidence `[DATA]` | — |
| Complaint-prediction model | No case-level complaint labels; the FY24 figure (85,281, +42.7%) is a national aggregate `[VERIFIED]` | Internal complaint-labelled case data |

## 6. Architecture at a glance

```text
┌──────────────────────────────────────────────────────────────────────────────────┐
│  L0  EVENT LOG (append-only, immutable, event-sourced)                           │
│      call.outcome · trace.returned · payment.received · visit.completed          │
│      refusal.recorded · override.recorded · coordinate.promoted                  │
└───────────────────────────────────────┬──────────────────────────────────────────┘
                                        ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│  L1  STATE ESTIMATION            ContactPointState ⊕ AccountRelationshipState    │
│      reachability · identity posterior · dead-streak · decayed recency           │
└───────────────────────────────────────┬──────────────────────────────────────────┘
                                        ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│  L2  EVIDENCE FUSION             provenance ⊗ behaviour ⊗ verification ⊗ graph   │
│      → P(borrower) with an interval; shared-number exposure flag                 │
└───────────────────────────────────────┬──────────────────────────────────────────┘
                                        ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│  L3  PREDICTION                  calibrated multi-class over dispositions        │
│      (pre-dial features only · honest AUC 0.670 · isotonic per segment)          │
└───────────────────────────────────────┬──────────────────────────────────────────┘
                                        ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│  L4  POLICY GATE (hard, deterministic, closed vocabulary)                        │
│      hours · DNC · notice · attempts · disclosure-eligibility · certification    │
│      → ALWAYS produces either an action token or a REFUSAL RECORD                │
└───────────────────────────────────────┬──────────────────────────────────────────┘
                                        ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│  L5  ECONOMICS        EV(action) → EVSI(trace, verify) → CVaR penalty λ          │
│      every number carries a published range; every refusal carries an arithmetic │
└───────────────────────────────────────┬──────────────────────────────────────────┘
                                        ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│  L6  ALLOCATION       day-level: agent-minutes · shift slots · ₹ trace budget    │
│      greedy with Lagrangian prices → OR-Tools MILP (if time) · shadow prices     │
└───────────────────────────────────────┬──────────────────────────────────────────┘
                                        ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│  L7  EXECUTION + FAILURE PATHS     dialer API · field app · trace vendor         │
│      every action declares: timeout · partial · rejected · fallback · escalation │
└───────────────────────────────────────┬──────────────────────────────────────────┘
                                        │ outcomes, propensities, overrides, reasons
                                        └──────────────► back to L0 (belief update)
```

## 7. Component inventory (the five-question test)

| # | Component | ① Real system using it | ② Problem it solves | ③ Fed by | ④ If it is wrong | ⑤ Why simpler won't do |
|---|---|---|---|---|---|---|
| C1 | Event log & replay | Standard in regulated decisioning; event sourcing `[S-59]` | No auditability; cannot re-run a policy | All L7 outputs | Worst failure — everything downstream is unauditable | A mutable DB row loses history; the refusal record is the product |
| C2 | `ContactPointState` | NYS DTF legal-state model `[S-32]`; skip-trace queues with memory `[S-60]` | "Should we ever call this again?" | Dispositions, trace results, payments, visits, time | Over-suppression (≥1 dead point is still 37.4% of RPCs `[DATA]`) | A stateless classifier cannot express *sequence* (3rd consecutive dead = 0.067 vs 0.180 `[DATA]`) |
| C3 | `AccountRelationshipState` | Portfolio-level collectors (Experian, Credgenics) `[S-1][S-26]` | Which points belong to *this* account, and which to a household | `phones` + `verified_contact_points` + graph | Wrong grouping → a "safe" call discloses to a neighbour | Per-point scoring misses sharing (**43.2% of attempts are on shared numbers** `[DATA]`) |
| C4 | Identity/evidence fusion | TransUnion contact graph `[S-10][S-11]`; Fellegi-Sunter/Splink `[S-44]` | P(borrower) with a defensible interval | Provenance, behaviour, verification, edges | A wrong posterior converts a compliance refusal into a disclosure | Provenance priors alone (CV AUC 0.813) ignore behaviour; the interval is what the gate consumes |
| C5 | Prediction (multi-class) | Every vendor `[S-1][S-3][S-16]` | Rank *within* the eligible set | Pre-dial features only | Miscalibration misallocates minutes; leakage inflates it (0.933) `[DATA]` | Rules alone are 0.157/call vs 0.1762 incumbent `[DATA]` — the model must earn its place or be cut |
| C6 | Policy gate | Pega constraint layer `[S-19]`; NYS DTF ~300 legal rules as binary constraints `[S-33]` | Makes prohibited actions structurally impossible | Rulebook config + state | A bug here is a regulatory breach | Post-hoc filtering is provably weaker than candidate-set construction (§12) |
| C7 | EV / cost model | Experian constraint-based optimization `[S-3]`; FICO `[S-16]` | Prices actions in rupees | Outcomes × cost table (ranges) | Confident nonsense if costs are invented | Ranking without cost cannot answer "is the ₹104 trace worth it?" |
| C8 | EVSI / information purchase | Multi-vendor trace orchestration `[S-60]`, insurance industry practice; VOI theory `[S-42]` | Stops buying information that cannot change a decision | Trace hit rate 22.8%, price ₹104 | Over-buying (77% waste today `[DATA]`) | A constant trigger cannot be optimised; a "trace-success model" is not learnable here (AUC 0.574 vs 0.772 `[DATA]`) |
| C9 | Risk-sensitive layer | CVaR in energy/disaster logistics `[S-43]`; not publicly described in collections `[INFERENCE]` | Makes irreversible actions require *confidence* | Loss distribution + λ | Over-conservatism | Expected value alone approves a high-mean/high-tail field visit |
| C10 | Day-level allocator | Experian/FICO solvers `[S-3][S-16]`; mTSP routing `[S-31]` | Fills scarce capacity by value, not list order | ENV matrix + capacity | Dishonest precision if inputs are fabricated | Greedy ranking ignores joint capacity and produces infeasible days |
| C11 | Refusal ledger | Distinctive; NYS/FICO gate but do not publish refusals | Turns "we chose not to" into an artifact | Gate + EV + EVSI | Refusals become invisible → pressure to over-contact | A log field is not a ledger; the ledger is queryable by reason |
| C12 | Calibration & coverage monitor | Model-risk practice in BFSI `[S-30]`; conformal `[S-53]` | Probabilities must stay honest as data drifts | Outcomes vs predictions | Silent drift degrades allocation invisibly | ECE alone does not give intervals; per-segment coverage does |

**Components from the Phase-2 hypothesis that were cut** (recorded, not silently removed): the GNN over the contact graph (a shared-number *flag* captures the decision value at 1% of the cost); the sequence model (label noise and 3-month horizon); the per-action outcome models (no arms to learn from); the "exploration engine" (no licence to explore).

## 8. State model

### 8.1 `CONTACT_POINT_STATE` — the belief object

**Owner:** the contact-point record in the customer-communication service (production) / `sanket.hmm` in the demo. **Updated by:** events only — never by a nightly overwrite, so replay is exact.

| Field | Meaning | Update mechanism | Decay |
|---|---|---|---|
| `identity_p` | P(this point reaches the borrower) | Fusion (C4) on verification, call outcome, graph change | 0.985/day (recycled-number risk) `[ASSUMPTION, tunable]` |
| `reach_p` | P(answered next attempt) | Behavioural model + outcome history | 0.97/day |
| `dead_streak` | Consecutive no-contact outcomes | `+1` on no-contact disposition, `0` on any positive | — |
| `state` | FRESH · ACTIVE_REACHABLE · ANSWERED_UNKNOWN · THIRD_PARTY_CONFIRMED · RIGHT_PARTY_REACHED · DEAD_3 · DISPUTED · VERIFIED_WRONG | transition table (§8.3) | — |
| `attempts_window` | Attempts in rolling window vs ceiling | Counter | Rolling |
| `last_contact_at`, `last_payment_at` | Recency inputs | Events | — |
| `exposure_flag` | Shared-number / third-party exposure | Graph edge (43.2% of points are shared `[DATA]`) | — |

### 8.2 `ACCOUNT_RELATIONSHIP_STATE`

**Owner:** the collections case record. **Update:** payment, promise-to-pay, dispute, field outcome, DPD roll.
Contains: DPD bucket, outstanding, PTP history and breaks, payment recency, dispute/freeze flags, hardship markers, **field-visit outcome summary and address confidence band (from PS3)**. The last two are the PS2↔PS3 join and are the reason the two systems are one product (§21).

### 8.3 Transition table (the deterministic skeleton)

| From | Event | To | Also does |
|---|---|---|---|
| FRESH | call, no answer | FRESH (`dead_streak+1`) | — |
| FRESH | answered, unknown party | ANSWERED_UNKNOWN | sets `identity_p` prior |
| ANSWERED_UNKNOWN | answered, self-identified third party | THIRD_PARTY_CONFIRMED | sets `exposure_flag`; blocks disclosure |
| ANSWERED_UNKNOWN | answered, borrower confirms | RIGHT_PARTY_REACHED | `identity_p → ≥0.95`; unlocks disclosure |
| any | `dead_streak = 3` on **consecutive** no-contact | DEAD_3 | **refuses dialing**; route to trace/visit/letter |
| THIRD_PARTY_CONFIRMED | verification proves shared/recycled | VERIFIED_WRONG | permanent refusal for this account |
| any | dispute raised | DISPUTED | freezes all action pending review `[R6]` |
| RIGHT_PARTY_REACHED | payment received | RIGHT_PARTY_REACHED (refreshed) | resets dead streak |
| any | daily decay crosses threshold | COLD | reduces priority, keeps state |

### 8.4 Why a state machine and not a hidden-state model

The measured justification: RPC per attempt by prior dead count is 0.180 / 0.177 / 0.160 / **0.067** for 0/1/2/3+ `[DATA]`. The collapse happens only at 3+, and crucially points with ≥1 prior dead call are **42.7% of all calls but 37.4% of all RPCs** `[DATA]` — the naive "never call a dead point" rule is wrong, and only a *sequence* representation gets this right. A hidden-state model would need to learn a sequence effect we can already measure with a counter.

## 9. Evidence fusion (P(borrower) with an interval)

```text
P(b) = σ( w_prov·provenance + w_beh·behaviour + w_ver·verification + w_graph·sharing )  → interval via per-segment coverage
```

**Measured inputs** `[DATA]`:

| Source | Evidence | Value |
|---|---|---|
| Provenance | P(borrower\|provenance) | skip_trace 1.00 · kyc_origination 0.73 · borrower_update 0.67 · bureau 0.30 · reference 0.16 · employer 0.07 |
| Behaviour | answered-then-third-party rate, talk-time shape, repeat self-identification | CV AUC 0.899 combined vs 0.813 provenance-only vs 0.508 majority |
| Verification | `verified_contact_points` | **250 labels, created 2026-07-02, i.e. after the dial window → evaluation only, never training** `[DATA]` |
| Graph | shared-number edge | 43.2% of dials sit on shared numbers; third-party rate 0.080 (shared) vs 0.061 (unique) `[DATA]` |

**The refusal this buys:** reference and employer points are 14% of all calls, are *answered* at 0.44–0.46 (they ring), but verify as third-party in **81–93%** of cases `[DATA]`. Under a P(RPC)-maximising policy these are attractive; under a disclosure rule they are ineligible. This single asymmetry is the clearest demonstration in the whole submission that ranking and permission are different problems.

## 10. Prediction layer

| Aspect | Decision |
|---|---|
| Target | Multi-class over the 16 dispositions `[DATA]`, collapsed for scoring into {right party, third party, no-contact, unavailable} |
| Features | **Pre-dial only.** Excluded by policy: `network_response`, call durations, `disposition` itself, and anything timestamped after the attempt start. Including them lifts AUC to **0.933** and is an anti-pattern `[DATA]` |
| Model | LightGBM, monotonic constraints where justified; logistic baseline retained as the control |
| Honest performance | Test AUC **0.670** (GBM) vs **0.604** (LR); feature importance ΔAUC: `prior_rpc` 0.0894 > self/third-party relation 0.0275 > hour 0.0274 > everything else ≤0.009 `[DATA]` |
| What it is *for* | Ordering within the eligible set and providing the `reach_p` term for EV. **It does not decide who may be contacted** (L4 does) |
| Cold start | New account → cohort prior by DPD bucket × product × provenance mix; the state machine and the gate work unchanged |
| Refusal to over-claim | The model is modest and the deck says so; the leakage number is shown as a caution, not a result |

## 11. Calibration and uncertainty strategy

Every probability in the system has a stated evaluation method — this is a hard requirement of the brief, and the table is the answer.

| Probability | Method | Metric | Action if it fails |
|---|---|---|---|
| `reach_p` | Isotonic per segment (DPD × point provenance × time bucket) | ECE, reliability curve, Brier | Fall back to segment base rate; flag the segment |
| `identity_p` | Empirical coverage of the interval on the 250 verified points | Empirical vs nominal coverage | Widen intervals; freeze disclosure unlock above the failed stratum |
| `P(RPC)` | Same as `reach_p` | ECE + top-decile lift | Suppress the model's contribution to EV for that segment |
| `P(trace yields info)` | Not modelled — measured base rate 22.8% with an interval `[DATA]` | — | If the interval straddles the EVSI threshold → refuse the purchase (conservative default) |
| `P(payment \| RPC)` | Cohort survival by DPD band; sensitivity band ± | Observed vs predicted within 7/30 days | Ranges widen; EVSI refuses more |
| Allocation outcomes | Post-hoc: realised vs planned value per shift | MAPE by shift | Reduce MILP to greedy for the affected shift |
| Coverage guarantees | Per-town, per-stratum conformal radii (shared with PS3) `[S-53]` | Nominal vs empirical coverage | Publish the failure; never silently widen |

**Rule:** no probability enters the objective without a row in this table. **Rule:** every EV carries a range; the system must never display a single-point expected value.

## 12. Policy and permission layer

**Design principle: the compliant candidate set is *constructed*, not filtered.** Post-hoc filtering means the optimiser has already spent capacity on ineligible work; constructing the set first makes prohibited actions structurally impossible and keeps the refusal reason exact.

### 12.1 The rulebook (closed vocabulary, versioned, config—not code)

| Code | Rule | Type | Source |
|---|---|---|---|
| `PG-01` | Contact only 08:00–19:00 `[VERIFIED: RBI Amendment Directions, effective 1 Jan 2027]` | Hard | Regulatory |
| `PG-02` | Field visit requires ≥1-day prior notice `[VERIFIED]` | Hard | Regulatory |
| `PG-03` | DNC / do-not-disturb in force | Hard | Regulatory + client |
| `PG-04` | Disclosure-eligible only if `identity_p ≥ θ_identity` (§9) | Hard | Conduct policy |
| `PG-05` | Attempt ceiling per point per day/week (`dead_streak ≥ 3` → block) | Hard | Observed optimum `[DATA]` |
| `PG-06` | Dispute/freeze/hardship → no collection action | Hard | Client policy |
| `PG-07` | Agent must hold current DRA certification; empanelled agency only `[VERIFIED]` | Hard | Regulatory |
| `PG-08` | Recording retention ≥6 months bi-directional `[VERIFIED]` | Hard | Regulatory |
| `PG-09` | Third-party point → no debt disclosure, ever (identity-led contact only) `[VERIFIED: DPDP + conduct]` | Hard | Regulatory + ethics |
| `PG-10` | Device-locking timing 30/60 days `[VERIFIED]` | Hard | Regulatory |
| `PG-11` | Bot/AI contact only if the same rules are enforced at the bot layer (3,761 bot attempts exist `[DATA]`) | Hard | Policy |
| `PG-12` | Capacity: agent minutes, field slots, trace budget (soft-formulated as constraints) | Hard | Operational |

**Two categories, never mixed:** *regulatory* rules are `[VERIFIED]` with a citation and cannot be tuned by the model; *policy* rules (θ_identity, ceilings, budget) are parameters with owners and change logs.

### 12.2 The refusal record

```json
{ "refusal_id": "...", "account_id": "...", "point_id": "...", "action": "dial|trace|visit|notice",
  "reason_code": "PG-05", "reason_text": "dead_streak=3 on this point",
  "inputs": {"dead_streak":3,"prior_attempts_7d":4}, "policy_version": "2026-10-06.1",
  "counterfactual_value": 118.0, "counterfactual_range": [64, 205],
  "data_snapshot_hash": "sha256:...", "ts": "..." }
```

`counterfactual_value` is the point of the ledger: every refusal states *what we believe we gave up, with a range*. That is what turns "the system was conservative" into a decision the business can audit and challenge.

## 13. Economic layer

### 13.1 Objective (explicit, as required)

```text
For each eligible action a on point p of account i:
    ENV(a) = P(success|a) · Value(a) · (1 − haircut_uncertainty) − Cost(a) − λ·Risk(a)
    where  Value(dial|contact)   = expected recovery over 7/30 days given the account's DPD band
           Value(visit|met)      = expected recovery, higher, plus location-confirmation value to PS3
           Value(trace)          = 0 by itself — a trace is only valuable through the action it changes (§13.3)
           Cost(·)               from the published cost table with ranges
```

**Cost table (parameters, published as ranges, every line sourced or labelled `[ASSUMPTION]`):**

| Cost | Central | Range | Note |
|---|---|---|---|
| Agent minute | ₹6.0 | ₹3.5–9.0 | `[ASSUMPTION]`, aligned to BPO-loaded cost; must be replaced by the client's figure |
| Dial attempt (machine) | ₹0.15 | ₹0.05–0.4 | `[ASSUMPTION]` |
| Skip trace | **₹104** | ₹60–150 | **`[DATA]` — measured mean in `skip_traces`** |
| Field visit slot | ₹180 | ₹90–350 | `[ASSUMPTION]`; includes travel time |
| SMS/e-mail | ₹0.20 | ₹0.05–0.5 | `[ASSUMPTION]` |
| Third-party contact (conduct) | ₹600 | ₹150–2,500 | `[UNKNOWN]` — no credible public source; must be client-supplied; drives λ |

**Honesty rule:** any output that depends on an `[ASSUMPTION]` row shows the sensitivity alongside. The submission must never present a single rupee figure as measured when it is parameterised.

### 13.2 The one measured economic result — trace spend

| Metric | Measured `[DATA]` |
|---|---|
| Traces | 766, mean cost **₹104** |
| Total spend | **₹79,650** |
| Traces that yielded information | 22.8% |
| **Spend that produced nothing** | **₹61,605 (77%)** |
| Cost per trace that found something | ₹455 |
| Cost per right-party contact attributable | ₹305 |
| Learnability of trace success | CV AUC **0.574** vs majority **0.772** → *below chance; not learnable* |

**Conclusion that drives the design:** you cannot predict which trace will work, so you must decide on *value*: buy information only when it can change an action. The trigger in the data is a constant `[DATA]` — i.e. the incumbent has no rule at all.

### 13.3 EVSI — information acquisition as a first-class primitive

```text
EV0 = max over actions under current belief            (usually: call the best point, or wait)
EV1 = E_info[ max over actions under posterior ]        (belief updated by the trace)
EVSI = EV1 − EV0 ;   BUY iff EVSI > price(trace) = ₹104
```

Worked example on real fields: an account whose only *unverified* point is a `reference` number (P(borrower) ≈ 0.16 `[DATA]`). Under the gate, no disclosure is permitted and the dial has almost no value → EV0 ≈ small. A trace that would confirm or kill the point changes the action set → EV1 − EV0 > ₹104 only when the expected recovery is large enough. **For a low-ticket account, the correct decision is to refuse the trace** — and to say so in the ledger. That is the mechanism that touches 77% of spend `[DATA]`.

**Second information purchase: the field verification.** EVSI here is larger because a visit also delivers location evidence to PS3 (§21.3), and because a met visit confirms identity at ≥0.95. The allocator (L6) prices both together.

## 14. Risk-sensitive layer

```text
Risk(a) = P(bad outcome | a) · Cost(bad) + κ · σ_model(decision)
score   = ENV(a) − λ · Risk(a)
```

- **Bad outcomes priced:** wrong-party contact, debt disclosure to a non-borrower, out-of-window contact, un-notified visit, complaint.
- **Irreversibility weighting:** `λ_visit > λ_dial ≥ 0`. A field visit cannot be un-rung; a notice cannot be un-sent.
- **Uncertainty term `κ`:** actions whose model inputs are in a low-coverage segment (from §11) are penalised — the system declines to act on its own weak confidence.
- **Discipline:** λ published, sensitivity curve shown, and **every action refused by λ alone is reported separately from actions refused by rules** — otherwise risk aversion becomes an unaccountable veto.
- **Evidence:** CVaR is standard practice in energy/disaster optimisation `[S-43]`; no reviewed collections vendor publishes a comparable conduct-tail term `[INFERENCE]`, which is precisely why it is worth building and why it must be implemented conservatively and transparently.

## 15. Allocation layer

```text
maximise  Σ_{i,p,a} ENV(a) x_{i,p,a}  −  λ·CVaR-term
subject to Σ x ≤ AgentMinutes / FieldSlots / TraceBudget        (capacity)
           x_{i,p,a} ≤ eligible(i,p,a)   ∧   Σ_a x ≤ 1 per point per window
           notice / hour-window / attempt-ceiling constraints hold for every selected action
           x ∈ {0,1}
```

| Mode | When | Solver | Output |
|---|---|---|---|
| Greedy with Lagrangian prices | 48-hour demo (default) | ~150 lines | Plan + shadow prices (₹ per agent-minute, per slot, per trace) |
| MILP | BUILD IF TIME | OR-Tools | Optimal plan + duals + infeasibility diagnosis |
| What-if | No client capacity data | Either | Plan under the brief's figures: 1,000 accounts / 200 agent-hours / ₹50,000 traces / 50 field slots |

**Shadow prices are the deliverable's best explanation device:** "one more field slot is worth ₹X of expected recovery tonight" is a sentence a collections head immediately understands and can argue with.

**Always-present slack action:** `wait` is in the action set, so the plan is never forced into pressure-calling to fill capacity.

## 16. Actions and their failure paths

Every action declares what happens when it fails — the brief's requirement, and the most commonly missing section in hackathon architectures.

| Action | Success signal | Failure mode | Failure handling |
|---|---|---|---|
| Dial (machine) | Answer + disposition | No answer · IVR drop · carrier reject · dialer outage | No answer → `dead_streak+1`, reschedule per ceiling; carrier reject → point penalised, routed to verification; **dialer outage → plan degrades to the top-N by EV with a logged degradation event** |
| Dial (agent) | Disposition recorded | Agent unavailable · call abandoned mid-script · system down | Re-queue with priority retained; abandoned calls counted in conduct metrics |
| Trace | Vendor returns a new point or a negative | Vendor timeout · partial result · generic junk point | Timeout → escalate once with backoff, then record `info_not_purchased`; junk point → evidence gate rejects it and the vendor hit-rate for that account stratum is down-weighted |
| Field visit | Outcome + GPS + media | Address not traceable · locked · borrowed-integrity failure · agent no-show | Not traceable → **negative outcome must not move the coordinate (PS3 rule)**; integrity failure → visit excluded from learning, agent flagged; no-show → slot recycled within the shift |
| Notice | Delivery recorded | Undeliverable · disputed receipt | Fall back to a second channel; the visit is not scheduled until delivery is proven (PG-02) |
| SMS/e-mail | Delivery + response | Bounce · spam filter | Small EV; failure has no penalty beyond the cost — the reason it is the default filler |
| Wait | — | Opportunity cost | Explicitly valued: ENV(wait) = option value of better information later; prevents the optimiser from inventing activity |

## 17. Event sourcing, audit and replay

- **Event vocabulary (shared with PS3 — see File 11):** `call.completed`, `trace.returned`, `payment.received`, `visit.completed`, `visit.rejected_integrity`, `refusal.recorded`, `override.recorded`, `coordinate.promoted`, `policy.versioned`.
- **Immutability:** events are append-only; corrections are new events. State is a *projection*, rebuildable at any timestamp.
- **Replay:** "what would policy v2026-11 have done with June's events?" is a query, not a project. This is how the team answers the operator question *"can we trust 1 Jan 2027 compliance before 1 Jan 2027?"*
- **Decision record:** every executed action stores the state hash, the feature vector hash, the model version, the policy version, the ENV with range, and the human override if any.
- **Privacy:** the log stores point references, not raw contact data; recording retention (≥6 months, bi-directional) `[VERIFIED]` is satisfied by the contact-recording store, not by this log — stated explicitly to avoid a DPDP violation by design.

## 18. Feedback loop and belief update

| Event | State effect | Model effect | Caveat enforced by design |
|---|---|---|---|
| `call.completed` | `dead_streak`, `reach_p`, `state` | Training row (with the pre-dial features only) | Propensity logged; **no policy learning** (O7) |
| `trace.returned` | new point / point killed | Provenance prior refresh; EVSI base-rate update | Constant-trigger period is not learnable — decision rule only |
| `payment.received` | resets streak, refreshes value | Value model refresh | **No causal claim**: 60% of payments fall within 7 days of an RPC but there is no campaign id `[DATA]` |
| `visit.completed` | identity ≥0.95 if met; address confidence to PS3 | Feature + EVSI calibration | Contaminated check-ins excluded (§16, PS3 integrity gate) |
| `override.recorded` | supervisor's decision | **Override reasons are the highest-value training signal in the system** | Analysed weekly; systematic overrides indicate a rule or threshold is wrong |
| `coordinate.promoted` (from PS3) | address confidence band updates | Field-slot EV updates | Two-confirmation rule `[S-56]` |

## 19. Data mapping — the dataset controls the design (Part N)

Every component maps to real tables/columns in `data/raw`, and every trap discovered in the audit is preserved in the design.

| Table | Rows | Columns the architecture actually consumes | Trap preserved in the design |
|---|---|---|---|
| `accounts.csv` | 2,400 | `account_id`, DPD bucket, outstanding, product | Ticket band distributions only; no cost/notice/campaign fields anywhere in the data |
| `phones.csv` | 5,719 | `phone_id`, `account_id`, `provenance`, type | **`phone_id` is not unique (74 repeats) → join key must be `(account_id, phone_id)`; a naive join inflates to 52,367 rows** |
| `dial_attempts.csv` | 51,105 | `attempt_ts`, `attempt_seq`, `network_response`, `disposition` (16 values), `dialling_arm`, `prev_dead` | **Excluded post-dial columns** (durations, `disposition`) from features — leakage to AUC 0.933; **`dialling_arm` randomisation is not clean** (2,277 vs 123; skewed DPD; propensity ≡1.0) → benchmark the incumbent, never claim uplift |
| `skip_traces.csv` | 766 | cost (mean ₹104), trigger, result | Trigger is a constant → EVSI rule only |
| `payments.csv` | 2,162 | amount, date, account | No campaign id → correlation only |
| `field_visits.csv` | 5,578 (1,477 addresses) | `outcome` (1400 not_traceable / 1249 locked / 1114 met_borrower / 1062 met_family / 455 shifted / 206 no_such_person / 92 cash-in-remark) | **Cash is free text in `remark` (43/92 parseable)** → treated as a flagged, lossy signal, never a payment record |
| `visit_gps_points.csv` | 160,406 | lat/lng, `accuracy`, timestamp, `visit_id` | Median accuracy 9.8 m; 645 check-ins (11.6%) >500 m from their own trail; FA009 has 162/172 duplicate photo hashes |
| `verified_contact_points.csv` | 250 | point↔account verification | **Created 2026-07-02, after the dial window → evaluation only** |
| `addresses.csv` / `baseline_geocodes.csv` | 3,117 / 2,880 (237 missing) | address, vendor precision | Feeds the PS3 contract; missing geocodes are a first-class case (field task), not an error |
| `splits.csv` | 1,680/360/360 | account-level split | Respected exactly; no cross-split leakage |
| `agents.csv`, `towns.csv`, `localities.csv`, `landmarks_poi.csv` | 30/3/36/240 | agent, town, locality | POI table incomplete and 14/14 names repeat → landmarks are priors only |
| `priority_slot` field | — | **inverted semantics** | Documented and handled explicitly; a silent sign error here would invert the whole plan |

## 20. Feature catalogue, provenance and leakage controls

| Group | Examples | Source | Leakage guard |
|---|---|---|---|
| Point provenance | provenance, type, age, source-event date | `phones` | None (static at issue) |
| Behavioural history | prior RPC rate, answered rate, third-party rate, answer-then-drop | `dial_attempts` ≤ attempt time | **Strict as-of join on `attempt_ts`** |
| Sequence | `attempt_seq`, consecutive dead, days since last contact | `dial_attempts` | As-of |
| Temporal | hour bucket (peak 0.210/0.198/0.198 at 08/09/18 `[DATA]`), weekday, days to month-end | timestamp | Derived, no leakage |
| Relationship | #active points, shared-number flag, household size | `phones` graph | As-of |
| Case | DPD bucket, outstanding, PTP history and breaks | `accounts`, `payments` | As-of |
| Field (PS3) | address confidence band, last visit outcome, integrity status | `field_visits`, PS3 contract | As-of; never future visits |
| **Banned** | `network_response`, call duration, `disposition` as a feature, anything post-attempt | — | Enforced in the feature builder with a test that fails the build if a banned column appears |

**Feature-value evidence:** `prior_rpc` (ΔAUC 0.0894) is worth more than everything except self-relation and hour combined `[DATA]` — the honest reading is that *history beats features* in this dataset, which is why the state machine carries so much of the architecture.

## 21. Interfaces and contracts

### 21.1 SANKET API (internal)

| Endpoint | Purpose | Key fields |
|---|---|---|
| `POST /decide` | Plan for one account | `account_id`, window → `action`, `point_id`, `env`, `env_range`, `rule_trace`, `refusal?` |
| `POST /plan/day` | Day plan under capacity | capacity vector → assignments, shadow prices, refusal summary |
| `GET /refusals?from&to&code` | Refusal ledger | paginated decisions + counterfactual values |
| `POST /outcome` | Event ingestion (idempotent by `event_id`) | event payload |
| `GET /state/{account_id}` | Current belief state + full timeline | for the demo and for supervisors |
| `POST /override` | Supervisor action | reason code (free text required) |

### 21.2 Contract with PS2's own execution layer

The dialer receives `{point_id, action, permitted_window, attempt_ceiling, expiry, rule_trace_id}` — an **action token**, not a bare instruction. An expired token is not executed. This is what makes the gate real rather than advisory.

### 21.3 The PS2 ⇄ PS3 contract (the integration, formalised)

| Direction | Payload | Consumer | Why it exists |
|---|---|---|---|
| PS3 → PS2 | `P(truth within 200 m)` per address, per stratum radius, integrity status | Field-slot EV, visit scheduling | A visit whose location is uncertain has lower expected value; the allocator must know |
| PS2 → PS3 | `visit.completed` (with outcome, dwell, trail reference), `visit.requested` with the value of confirmation | Fusion, promotion, active-learning queue | The visit is PS3's sensor; PS3 must know which addresses are worth visiting first |

This is the only integration between the two systems — deliberately narrow, so neither becomes a dependency of the other's correctness. The integrated product thesis is argued in `SANKET_SUTRA_SYSTEM_ARCHITECTURE_FINAL.md`.

## 22. Storage and schema

```sql
-- Postgres + jsonb events; PostGIS only in production (demo uses the dataset's metric plane)
CREATE TABLE contact_point (point_id text, account_id text, provenance text, type text,
    identity_p numeric, reach_p numeric, dead_streak int, state text,
    attempts_window int, exposure_flag boolean, last_contact_at timestamptz,
    PRIMARY KEY (account_id, point_id));           -- composite key is mandatory (74 duplicate phone_ids)

CREATE TABLE decision (decision_id text PRIMARY KEY, account_id text, point_id text, action text,
    state_hash text, feature_hash text, model_version text, policy_version text,
    env numeric, env_low numeric, env_high numeric, rule_trace jsonb, ts timestamptz);

CREATE TABLE refusal (refusal_id text PRIMARY KEY, account_id text, point_id text, action text,
    reason_code text, reason_text text, counterfactual_value numeric,
    counterfactual_low numeric, counterfactual_high numeric,
    policy_version text, data_snapshot_hash text, ts timestamptz);

CREATE TABLE event_log (event_id text PRIMARY KEY, type text, account_id text, point_id text,
    payload jsonb, ts timestamptz, actor text);     -- append-only; no UPDATE/DELETE grants

CREATE TABLE override (override_id text PRIMARY KEY, decision_id text, supervisor text,
    reason_code text, reason_text text, ts timestamptz);

CREATE TABLE calibration (segment text, metric text, value numeric, nominal numeric, n int, as_of date);
```

**Design notes:** the composite primary key and the append-only grant revocation are the two schema decisions that encode the dataset traps permanently. `decision.env_low/high` makes a point estimate structurally impossible to store — the honesty rule is enforced by the schema, not by convention.

## 23. Training pipeline and evaluation protocol

```text
1. Load splits.csv → account-level train/val/test (1,680/360/360); no account appears twice
2. Build features with strict as-of joins; banned-column test must pass
3. Train LR control + LightGBM; select on val
4. Calibrate on val (isotonic, per segment); evaluate on test
5. Report: AUC, PR-AUC, ECE, top-decile lift, per-segment coverage — plus the leakage AUC as a caution
6. Robustness: drop each feature group in turn; the model must not collapse to leakage-substitutes
7. Policy evaluation: replay the incumbent, the dead-streak rule, the EV rule and the EVSI rule over test events;
   report per-attempt RPC, calls removed, and the refusal count — with the confounded-arm caveat printed on the slide
8. Freeze artefacts: model hash, calibration map, policy version, cost-table version
```

**Artefacts to ship:** `model.txt`, `calibration.json`, `policy.yaml`, `costs.yaml`, `eval_report.json`, `refusals.csv`, plus a script that regenerates all of them.

## 24. Inference pipeline and latency budget

| Path | Latency budget | Design |
|---|---|---|
| Nightly planning | minutes | Batch: state projection → features → scores → gate → EV/EVSI → allocator → plan |
| Real-time point switch (during a call) | <300 ms | Cached state + precomputed scores; only the gate and EV are computed live; no model call |
| Field app | <1 s | Reads the plan and the address confidence band; writes outcomes offline-tolerant with local queueing |
| Failure fallback | immediate | Model unavailable → segment priors; feature service down → last frozen feature snapshot (aged ≤24 h, flagged); gate unavailable → **deny all actions** (fail-closed) |

Fail-closed on the compliance path is deliberate: an unavailable rulebook must never result in ungoverned contact.

## 25. Monitoring, drift and degradation

| Monitor | Threshold → action |
|---|---|
| Refusal rate by code | >2σ shift → review thresholds with compliance; never auto-relax |
| ECE per segment | >0.05 → recalibrate; >0.10 → disable the model's contribution for that segment |
| Coverage (identity intervals) | Below nominal → widen intervals; block disclosure unlock in that stratum |
| Third-party rate | Any rise → freeze the current λ and alert (this is the conduct KPI) |
| Trace hit rate / spend | Hit rate down → EVSI threshold tightens automatically (it is arithmetic) |
| Plan fill rate | <90% of planned actions executed → capacity model is wrong; alert ops |
| Override rate by code | Rising → the rule or threshold is wrong; weekly review |
| Data drift | PSI on key features; a change in provenance mix flagged before scores move |
| Degradation events | Every fallback writes an event; a shift with >5% degraded decisions is reported to the supervisor |

## 26. Explainability and the refusal ledger

Three artifacts, each aimed at a different reader:

1. **Decision card** (analyst): account, point, action, ENV with range, top-3 contributing features, gate path, and the counterfactual runner-up action.
2. **Refusal list** (compliance): reason code, rule citation, decision inputs, counterfactual value with range — queryable by date, code, town, DPD.
3. **Portfolio view** (management): calls made vs refused by reason; rupees recovered per agent-minute; the dead-point and trace-spend savings; shadow prices for each constrained resource.

Explainability rule: **no explanation may introduce a number that is not in the decision record.** Post-hoc narrative that is not in the log is prohibited by design — the brief's "unsupported capability labelled" discipline applied to explanations themselves.

## 27. Failure modes and red-team results

| # | Failure | Detection | Mitigation in the design | Residual risk |
|---|---|---|---|---|
| 1 | Over-suppression of callable points | RPC/calls removed ratio in policy replay | Refuse only at `dead_streak ≥ 3` `[DATA]`; report the counterfactual value of refusals | Medium |
| 2 | Identity posterior drifts after number recycling | Coverage monitor; third-party rate | Daily decay 0.985; disclosure re-lock on any third-party signal | Medium |
| 3 | Cost table wrong by 3× | Sensitivity curve | Publish ranges; every EV shows the band; allocator re-run at ±3× is displayed | High (unavoidable) |
| 4 | Feature leakage reintroduced by a new engineer | Banned-column build test | Test fails the build; leakage AUC printed as a caution in every report | Low |
| 5 | Confounded arm used as a holdout in a slide | Review checklist item | Propensity histogram printed wherever arms appear | Low |
| 6 | Rulebook version skew between services | Version in every decision record | Policy version pinned in the action token; mismatched token rejected | Low |
| 7 | Agents working around refusals | Override reasons | Override rate monitored; systematic overrides escalate design review | Medium |
| 8 | Optimiser pressure-fills capacity | `wait` in the action set; shift reports | Report *both* throughput and contacts-per-recovery | Low |
| 9 | `priority_slot` sign error (dataset trap) | Unit test with a known case | Documented; tested | Low |
| 10 | DPDP/retention conflict in the event log | Privacy review | Log stores references, not raw contact content; recording retention handled elsewhere | Low |

## 28. Compliance and licence traceability

| Item | Status | Where enforced |
|---|---|---|
| RBI Amendment Directions (nine directions; effective 1 Jan 2027): 08:00–19:00, ≥1-day pre-visit notice, ≥6-month bi-directional recording, empanelled agencies, IIBF-certified DRAs, device-locking 30/60 days, ₹250/h compensation | `[VERIFIED]` | PG-01, PG-02, PG-07, PG-08, PG-10 + refusal codes |
| DPDP Rules 2025 (G.S.R. 843(E)) — purpose limitation, minimisation | `[VERIFIED]` | Feature catalogue; point references over raw content |
| TRAI TCCCPR + 12 Feb 2025 amendment (140/1600 series, ₹2 lakh disincentive per violation) | `[VERIFIED]` | PG-11 bot rules; consent state |
| FCC Reassigned Numbers Database (US analogue — referenced, not applicable) | `[VERIFIED]` | Cited as the international practice for the recycling problem |
| Google Maps Platform terms: lat/lng cache ≤30 days, no permanent storage, no training on output | `[VERIFIED]` | PS3 provider layer; **the canonical coordinate must be field-confirmed, not a vendor pin** |
| Nominatim usage policy (1 req/s) · data.gov.in NDSAP (non-commercial) · Criteo Uplift (CC BY-NC-SA) | `[VERIFIED]` | Any auxiliary data use is documented with its licence in the data register |
| Synthetic dataset | Declared synthetic by the README; `landmarks_poi.csv` incomplete; `annotated_ptp_sample.csv` partly mislabelled | Every dataset-derived number is labelled `[DATA]` and no market claim rests on it |
| Market-size and competitor figures | Each carries a source or is absent | No unsourced market claims in this document |

## 29. Build plan — 48 hours, with the cut-line

| Phase | Hours | Deliverable | Acceptance number |
|---|---|---|---|
| P0 | 0–2 | Event log + state projection on real data | Rebuild state from events → identical to direct computation |
| P1 | 2–6 | State machine + transition table | Dead-streak policy replay reproduces **0.1872 vs 0.1762** RPC/call, −12.5% calls `[DATA]` |
| P2 | 6–12 | Features + control + GBM + calibration | Test AUC **0.670** (control 0.604); ECE < 0.05 per segment |
| P3 | 12–16 | Policy gate + refusal ledger | 100% of refusals carry a code, a citation and a counterfactual range |
| P4 | 16–22 | EV + cost table + EVSI on traces | Reproduces ₹104 / 22.8% / 77% waste; refuses ≥X traces with arithmetic shown |
| P5 | 22–30 | Day allocator (greedy) + shadow prices | Plan under 1,000 / 200h / ₹50,000 / 50 slots; every slot's marginal value printed |
| P6 | 30–38 | PS3 contract wiring + field-slot EV | `P(within 200 m)` visibly changes visit ordering |
| P7 | 38–44 | Demo, dashboards, decision cards, replay | Live: a refusal explained, a trace refused, a plan re-optimised after a capacity change |
| P8 | 44–48 | Write-up, red-team pass, freeze | Every claim traceable to `[DATA]` / `[S-nn]` / `[ASSUMPTION]` |

**Cut-line if behind:** P0–P4 ship; P5 degrades to a ranked list with a published budget cap; P6 becomes a static contract document; the refusal ledger is never cut.

**PRODUCTION target (out of 48-h scope):** the same architecture on streaming events with online state projection, a real rulebook service, PostGIS, per-agent capacity, and the MILP in nightly batch. The delta is stated in `ARCHITECTURE_DECISION_LOG_FINAL.md`.

## 30. Evaluation, demo script, and the open risks that would change this design

### 30.1 Metrics table (what the judges should hold us to)

| Claim | Metric | Baseline | Ours | Evidence class |
|---|---|---|---|---|
| Fewer calls, same recovery | RPC per attempt | 0.1762 | **0.1872** (−12.5% calls) | `[DATA]`, test split |
| Right-party precision on the hard segment | third-party rate on reference/employer points | 81–93% | refused or identity-gated | `[DATA]` |
| Trace spend discipline | ₹ wasted / total | **77% (₹61,605)** | refuse-by-arithmetic, ledger-visible | `[DATA]` |
| Ranking quality | test AUC | 0.604 (LR) | 0.670 (GBM), calibrated | `[DATA]` |
| Compliance | prohibited actions executed | unmeasured | 0 by construction + refusal ledger | design |
| Economic discipline | rupees recovered per all-in rupee | unmeasured | computed with published ranges | parameterised |
| Conduct | third-party contact rate | 0.066 (rule arm) | must not rise; λ protects the tail | `[DATA]` |

**An honest note that belongs on the slide:** the dataset's RPC level (16.4% of attempts) is far above the described reality of collections (**FICO: RPC "rarely exceeds 8–10%"** `[VERIFIED]`). It is a *mechanism demo*, not a benchmark. Every percentage above is a comparison *within* the synthetic world.

### 30.2 Demo script (8 minutes)

1. **The incumbent, warts and all** — 51,105 calls, 16 dispositions, a constant trace trigger, ₹79,650 spent, 77% invisible waste.
2. **One account's belief timeline** — a call that reaches a third party, a trace that kills a point, a payment that resets the state; the state object visibly changing.
3. **A refusal with arithmetic** — the system declines a ₹104 trace and a field slot, showing the EVSI computation and the counterfactual range.
4. **The day plan** — capacity changed live (drop the field slots from 50 to 20): shadow price moves, the plan re-orders, the refusal count changes.
5. **The replay** — same events, new policy version; the difference is the argument for 1 Jan 2027 readiness.
6. **The honest slide** — leakage 0.933 vs honest 0.670; the confounded arm; the cost table's ranges; what we refused to claim.

### 30.3 Open risks that would change the design

| Risk | Change it would force |
|---|---|
| Client supplies real cost and capacity tables | Allocator (L6) becomes the centrepiece; MILP replaces greedy |
| Client supplies real ticket bands and product mix | EVSI thresholds move materially; low-ticket books refuse many more traces |
| A clean randomised pilot with campaign attribution | Reopen uplift/bandit — with a real ESS budget |
| Rulebook is published in a different form (state-level or lender-specific) | Rule codes and refusal vocabulary change; architecture unaffected |
| The dataset is not representative of the pilot book | All `[DATA]` acceptance numbers must be re-derived before any pilot claim |


## XV.10 — File 10 — SUTRA final architecture (30 sections)

*Source file: `PS3_SUTRA_SOLUTION_ARCHITECTURE_FINAL.md`*

# SUTRA — PS3 SOLUTION ARCHITECTURE (FINAL)

**Phase 4, File 10 of 13.** 30 sections, as mandated. Replaces the Phase-2 hypothesis in `PS3_SUTRA_SOLUTION_ARCHITECTURE.md`.

**Companions:** `PS3_ADVANCED_ARCHITECTURE_RESEARCH.md` (15 architectures compared) · `PS3_ARCHITECTURE_OPTIONS.md` (7 options scored) · `PS3_ARCHITECTURE_SELECTION.md` (the decision) · `PS2_PS3_DATASET_REVIEW.md` (§2 reconciliation, §4 evidence, §5 traps) · `SANKET_SUTRA_SYSTEM_ARCHITECTURE_FINAL.md` (integration) · `ARCHITECTURE_RESEARCH_BIBLIOGRAPHY.md` (sources).

**Component labelling convention:** `①real system` · `②problem solved` · `③fed by` · `④if wrong` · `⑤why a simpler component cannot replace it`.

---

## 1. Problem, and the official statement it must satisfy

PS3's official statement is about **address/location intelligence for the field-recovery workflow** — the reconciliation with our framing is on the record in `PS2_PS3_DATASET_REVIEW.md` §2 and is not re-litigated here. The operational questions are: *can this borrower be found at this address; how far might we be wrong; is this visit worth a field slot tonight; and what did we learn about this address from the last visit?*

The three measured facts that define the problem `[DATA]`:

1. **The current point estimate is not good enough to walk to.** Median error 376.4 m, p90 839 m, only 9% under 100 m against 100 surveyed addresses.
2. **Public data cannot fix it.** Our own oracle over candidate sets built from free text: 370 m median, 2% under 100 m. Naive landmark snapping: 4,093 m, worse than baseline in 90% of cases.
3. **Field evidence can — by an order of magnitude.** On visits where the agent met someone: 385 m → **29 m** median on the same addresses, 82% under 100 m.

So the problem is not "geocode the address". It is: **state an honest belief about location, spend field evidence where it changes that belief, refuse to learn from evidence that is contaminated, and hand a probability — not a pin — to the decision that spends a field slot.**

## 2. What this system is, in one paragraph

**SUTRA** maintains an **`ADDRESS_STATE`** for every address: a location belief (point + radius + stratum), an evidence history, an integrity status, and a confirmation count. It parses and normalises Indian address text, retrieves candidates from a gazetteer and from our own confirmed-pin index, keeps the commercial geocoder's point as a *prior* (never as truth), fuses field evidence — GPS trails, dwell, outcome sign, media sanity — into a posterior, expresses uncertainty as per-stratum conformal radii validated on two independent samples, and publishes exactly two things outward: `P(truth within r)` for the PS2 allocator, and promotion events when a coordinate is confirmed twice. It is offline-first, licence-clean (the canonical coordinate is ours, not a vendor's), and it refuses to move a pin on the strength of a negative visit outcome.

## 3. Users and consumers

| Consumer | What they see | Why they care |
|---|---|---|
| Field officer (mobile app) | Search radius, not a pin: "search within 1.3 km" vs "within 40 m"; landmark hint; confirmation capture flow | Arrives at the right building; knows when to stop looking |
| Field supervisor | Visit queue ranked by *value of confirmation*; integrity flags on returned visits | Utilises slots on cases where certainty is worth money |
| PS2 allocator (machine) | `P(truth within 200 m)` + stratum radius + integrity status | Prices a field slot in expected rupees |
| Master-data steward | Low-confidence / high-value address queue | Fixes addresses before slots are spent |
| Data-engineering / legal | Provider audit log, cache policy compliance, licence register | Approves the data flow |
| Model risk | Coverage report per town and stratum; promotion audit | Validates the uncertainty claims |

## 4. Business objective (explicit)

```text
Maximise  Σ_visits [ P(met | address belief) · Value(met) − VisitCost ]
        + Σ_addresses [ Value_of_certainty · Δuncertainty ]         [the compounding term]
subject to: field-slot capacity (PS2-owned)  (hard)
            no coordinate may be promoted without 2 independent integrity-passing confirmations (hard)
            vendor licence constraints honoured: no permanent storage of vendor content (hard)
            a negative-outcome visit may never move a coordinate (hard — anti-poison rule)

Objective is expressed in rupees only where a rupee value exists; where it does not,
the term is reported as a ranked preference, not a currency amount.
```

**Primary KPI:** median location error on addresses with field evidence (target: the measured 29 m, not a made-up figure).
**Secondary KPIs:** % addresses under 100 m (baseline 9%); field-slot hit rate (`met_*` per slot); wasted-visit rate; confirmation coverage (% of addresses with ≥1 confirmation); time-to-confirmation.
**Honesty KPI:** published interval coverage vs nominal — the metric most systems refuse to publish.

## 5. Non-goals and explicit refusals

| Not building | Why (measured or sourced) | What would change it |
|---|---|---|
| A general-purpose national geocoder | Free-data ceiling 370 m `[DATA]`; GeoIndia's corpus is proprietary `[S-47bis]` | A licensed corpus + hierarchy gazetteer |
| Hierarchical cell (H3) prediction model | With 3,117 addresses it would learn to locality level — what the vendor already reports | ≥10k labelled addresses |
| HMM map matching | **No road graph in the data** — coordinates are a local metric plane with no polygons `[DATA]` | An OSM extract for the three towns |
| Landmark-based auto-correction | 4,093 m median, worse in 90% of cases `[DATA]` | A real POI dataset with attributes |
| A continuous-grid probabilistic map product | Fictional precision; unreadable for a field officer | A genuine decision-theoretic need for full densities |
| Storing vendor responses long-term | Google terms: lat/lng cache ≤30 days, no permanent storage of other content, no training on output `[S-48]` | A different provider contract |
| Voice/photo ML for identity | Out of scope; PS2 owns identity | — |

## 6. Architecture at a glance

```text
                     ┌──────────────────────────────────────────────────────────┐
 ADDRESS TEXT  ─────►│ S1 PARSE & NORMALISE   script · abbreviations · levels    │
 (multilingual)      │    open Indic NER + rules (offline)                       │
                     └───────────────┬──────────────────────────────────────────┘
                                     ▼
                     ┌──────────────────────────────────────────────────────────┐
                     │ S2 RETRIEVE   confirmed-pin index ⊕ gazetteer ⊕ landmark   │
                     │    priors (never auto-snap) · abstain when thin            │
                     └───────────────┬──────────────────────────────────────────┘
                                     ▼
   vendor geocode ───►┌──────────────────────────────────────────────────────────┐
   (time-limited      │ S3 PRIOR   point ⊗ stratum kernel   [rooftop 37.7 m …    │
    cache ≤30 d)      │            pincode 1,336.5 m — two-sample validated]      │
                     └───────────────┬──────────────────────────────────────────┘
 FIELD EVIDENCE ────►┌───────────────▼──────────────────────────────────────────┐
 • GPS trail        │ S4 INTEGRITY GATE   mock location · teleport · duplicate   │
   (accuracy/point) │      media · trail-vs-checkin distance · dwell sanity      │
 • dwell            │      → PASS / REJECT-with-code  (645 check-ins 11.6% >500m)│
 • outcome sign     └───────────────┬──────────────────────────────────────────┘
 • media hash                       ▼ PASS only
                     ┌──────────────────────────────────────────────────────────┐
                     │ S5 FUSION   stationary-cluster stop detection →            │
                     │    dwell-weighted, outcome-signed posterior                │
                     └───────────────┬──────────────────────────────────────────┘
                                     ▼
                     ┌──────────────────────────────────────────────────────────┐
                     │ S6 UNCERTAINTY   per-stratum conformal radius + coverage   │
                     └───────────────┬──────────────────────────────────────────┘
                                     ▼
                     ┌──────────────────────────────────────────────────────────┐
                     │ S7 CONTRACT   P(within 200 m) → PS2 allocator              │
                     │    promotion event → PS2 state   (two contracts only)      │
                     └───────────────┬──────────────────────────────────────────┘
                                     ▼
                     ┌──────────────────────────────────────────────────────────┐
                     │ S8 FEEDBACK   2 independent confirmations → promote →      │
                     │    index, priors, next-visit acquisition scoring           │
                     └──────────────────────────────────────────────────────────┘
```

## 7. Component inventory (the five-question test)

| # | Component | ① Real system | ② Problem solved | ③ Fed by | ④ If wrong | ⑤ Why simpler cannot replace |
|---|---|---|---|---|---|---|
| D1 | Address parser | `addressparser` (IndicBERTv2-SS+CRF, <30 ms) `[S-46]`; open Indic NER `[S-13bis]`; deepparse | Indian addresses are not parseable by the vendor alone; script/abbreviation variance | `addresses.csv` (3,117), 3 towns, 36 localities | Mis-parse silently relocates the street | Whole-string geocoding loses administrative-level evidence that drives the stratum radius |
| D2 | Candidate retrieval | Search/retrieval framing `[S-46bis]`; Overture addresses `[S-52]` | Provides the candidate set the point estimate is chosen from | Gazetteer + confirmed-pin index + landmarks as priors | Abstention fails → false confidence | A single API call returns *an* answer; retrieval returns *options with scores*, which is what makes abstention possible |
| D3 | Stratum prior | Google `location_type`/`partial_match` fields `[S-47]` are exactly the weak signal we upgrade | Baseline error is stratum-dependent by 35× | Vendor `precision` label + `derived_ps3_radius_calibration.csv` | Pincode addresses treated like rooftops → wasted trips | A global error radius is either useless (too wide) or wrong (too narrow) — the 37.7 m vs 1,336.5 m spread makes the stratum mandatory |
| D4 | Integrity gate | Spoofing detection practice: mock flags, cross-signal inconsistency `[S-58]`; Android `isMock`/`getAccuracy` (68% radius) | Prevents the map from learning from fabricated or careless evidence | `visit_gps_points` (160,406), check-ins, media hashes | 11.6% poisoned check-ins trained into the model | Averages/"outlier removal" cannot distinguish *dishonest* from *unusual*; the gate encodes physical impossibility and cross-signal contradiction |
| D5 | Stop detection + fusion | POI recognition from unreliable GPS via spatio-temporal density and intersecting line segments `[G20, master research]`; delivery geocode feedback `[S-56]` | Finds *where the agent actually stopped*, weighted by dwell and outcome sign | GPS trail (median 26 pts/visit, 9.8 m accuracy) | A wrong stop point confirms a wrong building | Trail centroid is provably wrong for a door (a 2-minute negative check-in sits 1,603 m from truth — negative outcomes *manufacture* false locations `[DATA]`) |
| D6 | Uncertainty (conformal) | Conformal spatial prediction `[S-53]`: 93.67% empirical coverage at 90% nominal vs 68.33% bootstrap | Honest intervals a planner can price | 100 surveyed addresses, stratified | Over-tight radius → failed visits; over-wide → unused coverage | Parametric error models are not distribution-free; bootstrap under-covers badly in this setting |
| D7 | Confirmation & promotion | Two-confirmation auto-update in logistics `[S-56]` | Turns visits into an asset that improves every future query | Integrity-passing visits | Reinforces a wrong pin | Single-visit overwrite is exactly how a bad pin becomes permanent |
| D8 | Address belief store (`ADDRESS_STATE`) | Master-data systems in banking (entity lifecycle) | One lifecycle object per address with provenance and confidence | All of the above | Conflicting records; no answer to "why do we believe this?" | A coordinate column cannot express belief, evidence or decay |
| D9 | Acquisition scoring | Active learning; EVSI shared with PS2 `[S-42]` | Chooses which address to verify next | Uncertainty × account value ÷ visit cost | Slots spent on low-value certainty | Ranking by error alone ignores that a 400 m error on a ₹4k account is not worth a slot |
| D10 | Provider layer | Multi-provider practice; Google `[S-48]`, Mappls `[S-50]`, Nominatim `[S-51]` | Licence compliance, outage resilience | Config + audit log | Licence breach (the most expensive failure in PS3) | Hard-coding one vendor makes the terms permanent; the layer makes them inspectable |

**Cut from the Phase-2 hypothesis (recorded):** home/work/shop *probabilistic* classification (kept only as a weak outcome-based prior — the data cannot validate a classifier); directions generation (Google/Mappls already do it; the value is the radius, not the turn list); a full Bayesian grid.

## 8. State model

### 8.1 `ADDRESS_STATE`

**Owner:** the address/entity record in the servicing master (production) / `sutra.address_state` in the demo. **Updated by:** events only.

| Field | Meaning | Update mechanism | Decay |
|---|---|---|---|
| `belief_point` | Best current estimate (lat, lng) | Fusion (S5) on promotion only | point does not decay; *confidence* does |
| `belief_radius_p50/p90` | Honest error band | Stratum kernel → conformal recalibration | recomputed at each label arrival |
| `stratum` | rooftop / street / locality / pincode (+ `unknown`) | Vendor label; upgraded by confirmation | downgraded if evidence conflicts |
| `evidence_set` | Ordered, weighted evidence records (visit, GPS cluster, landmark mention, vendor result) | append-only | age-weighted |
| `integrity_status` | CLEAN · FLAGGED · REJECTED(agent, reason) | Integrity gate (S4) | manual review clears |
| `confirmation_count` | Independent confirmations (distinct visits, distinct days) | Promotion rule | — |
| `canonical` | boolean — may be used as ground truth by downstream systems | 2 confirmations + integrity CLEAN | revoked on contradiction |
| `last_verified_at`, `attempts_to_confirm` | lifecycle telemetry | events | — |

### 8.2 `ACCOUNT_ADDRESS_LINK` (the PS2 join)

| Field | Meaning |
|---|---|
| `account_id`, `address_id` | the link (many-to-many; 3,117 addresses for 2,400 accounts `[DATA]`) |
| `link_confidence` | P(this address belongs to this borrower) — from PS2's identity model |
| `p_within_200m` | **the published contract value** (stratum radius + evidence + confirmation count) |
| `visit_value_estimate` | PS2's value of confirming this address |

### 8.3 Transition rules

| From | Trigger | To | Guard |
|---|---|---|---|
| `unverified` | vendor geocode only | `prior_only` | never `canonical` |
| `prior_only` | 1 integrity-passing met-visit | `confirmed_once` | count++, no promotion |
| `confirmed_once` | 2nd independent met-visit within radius | `canonical` | **two independent** confirms `[S-56]` |
| any | negative outcome (`not_traceable`, `no_such_person`) | unchanged, `evidence_set` appended with **negative weight** | **coordinate must not move** `[DATA]` |
| any | integrity REJECTED | `flagged` | excluded from fusion and feature generation |
| `canonical` | contradiction from a clean visit | `review` | manual steward decision; promotion revoked |

## 9. Evidence layer and what each item is worth

| Evidence | Signal | Weight rule | Measured basis `[DATA]` |
|---|---|---|---|
| Vendor geocode | prior point + stratum | Prior only; never promotes | Baseline 376 m median; stratum medians 37.7/134.9/367.4/1,336.5 m |
| Field GPS trail | probable location | Likelihood centred on stop cluster; scaled by per-point `accuracy` (median 9.8 m) | 385 m → 29 m on met visits |
| Dwell | confidence in a stop | ≥N minutes at the cluster → usable; <3 min → weak | Negative check-ins show 2-minute dwell at 1,603 m from truth |
| Outcome sign | direction of the update | `met_borrower`/`met_family` → positive; `locked`/`not_traceable` → **negative, never moves the point**; `shifted` → address obsolete, route to review | Outcome vocabulary with counts: 1400/1249/1114/1062/455/206 (+92 cash-in-remark) |
| Media hash | authenticity | Repeated hash across visits → integrity flag for the agent | FA009: 162/172 duplicates (26.6%) vs ≤1% elsewhere |
| Shared check-in vs own trail | consistency | >500 m → flag for review, exclude from learning | 645 check-ins (11.6%) |
| Landmark mention (text) | hint only | Prior/telephone aid for the officer; never a coordinate source | Naive snap 4,093 m median |

**The evidence rule that makes this architecture distinct:** *negative outcomes are information about the visit, not about the location.* The data proves why: `address_not_traceable` check-ins are 1,603 m from truth and 195 m from the pin, i.e. the agent marked the location they already had while failing to find the address. A naive fusion layer would drag the belief toward the pin — the opposite of learning.

## 10. Address parsing and normalisation

| Step | Technique | Reason |
|---|---|---|
| Script normalisation | Unicode fold (Devanagari/Bengali → canonical), transliteration table | Indian addresses mix scripts; 3 towns with local naming |
| Abbreviation expansion | Rule dictionary (`Rd`, `St`, `Ngr`, `Blk`, `Fl`, `Opp`, `Nr`) | Tokens drive retrieval |
| Level extraction | Indic NER + CRF (`addressparser`) `[S-46]` | Unit / building / street / locality / city / PIN |
| PIN validation | PIN↔locality↔town gazetteer from the dataset | PIN is the strongest single field (stratum + search area) |
| Alias resolution | Locality alias table (`localities.csv`, 36 rows) | Same place, many spellings |
| Output | Structured record + confidence per field | A parse is an explanation; a whole-string call is not |

**Honest limitation:** there are **no parse-level labels** in the dataset `[DISCOVERED]`, so parsing is delivered as a **rules + open-model** component with an evaluation on 30 hand-labelled addresses; it is never presented as a trained system.

## 11. Candidate retrieval and ranking

```
query(parsed) ─► [confirmed-pin index] ⊕ [gazetteer: PIN→locality→town] ⊕ [landmarks as priors]
                ─► candidates with scores ─► rank ─► if margin < τ or set empty → ABSTAIN → field task
```

| Candidate source | Role | Honest value |
|---|---|---|
| Confirmed pins (our own, promotion-backed) | Highest-precision source; grows with use | Compounding asset; day-one empty, demo-day non-empty |
| Gazetteer (PIN/locality/town) | Bounds the search area; supplies the stratum prior | Improves calibration, not point accuracy (locality ceiling 379 m `[DATA]`) |
| Vendor point | Prior | 376 m median |
| Landmarks | Hint/telephone-aid only | Never auto-snapped `[DATA]` |

**Ranking is rule-first** (PIN match > locality match > street-token overlap > distance to prior), with an optional learned ranker explicitly **excluded** on evidence: the oracle over candidate sets caps at 370 m `[DATA]`, so a learned ranker cannot beat its own candidate set, and 100 survey labels cannot validate one. `[BUILD IF TIME]` only as an experiment.

**Abstention is a feature, not a failure:** an address with no confident candidate is routed to the field task queue with a wide radius — the correct answer when the evidence is thin.

## 12. Spatial estimation (the fusion)

```text
prior:      X ~ kernel( vendor_point, σ_stratum )          # σ from the two-sample table
evidence k: L_k(x | trail_k, dwell_k, outcome_k, integrity_k)
posterior:  p(x | E) ∝ prior(x) · Π_k L_k(x)^{w_k}
estimate:   stop-cluster centroid (not trail centroid) with dwell weighting
output:     belief_point (unpromoted) · radius(p50,p90) · explanation weights
```

| Rule | Why |
|---|---|
| Stop detection by stationary clustering | The door is where the agent stood still, not where they walked |
| Weight by dwell and outcome sign | Negative outcomes cannot move the point `[DATA]` |
| Independent-evidence tempering | Trail + dwell are not independent features; avoid double counting |
| One visit → candidate; two → promotion | Prevents single-visit poisoning `[S-56]` |
| Never average a rejected visit | Integrity gate runs *before* fusion, not after |

**Coverage honesty:** where no field evidence exists (the majority of the 3,117 addresses), SUTRA returns the *stratum* radius — median 367.4 m at locality, 1,336.5 m at pincode `[DATA]`. It does not pretend otherwise, and PS2's allocator sees exactly that.

## 13. Uncertainty representation, calibration strategy, and the probability table

**Representation:** per stratum × town, two numbers — `p50` and `p90` radius — plus `P(within 200 m)` derived from the same empirical distribution. Not a continuous density.

| Probability / quantity | Method | Metric | Failure action |
|---|---|---|---|
| Radius (p50, p90) per stratum × town | Empirical quantiles from the surveyed sample, **validated on a second independent sample** | Two-sample agreement `[DATA]` | If samples disagree → publish the wider value; freeze promotions in that town |
| Conformal radius with finite-sample coverage | Split-conformal on the surveyed set, stratified `[S-53]` | empirical vs nominal coverage | Recalibrate; publish the gap |
| `P(within 200 m)` | Empirical CDF of |error| at 200 m within stratum | Reliability at 100/200/500 m | Widen; mark the stratum `low-confidence` |
| `P(met \| visit)` | Observed met rate by stratum, integrity-clean only | Brier vs base rate | Show base rate instead |
| Integrity pass rate | Per-agent distribution | Flag if an agent is >3σ from peers | Exclude the agent's visits from learning pending review |
| Coverage of promotions | Post-promotion error audit | Any promoted point >p90 later → revoke | Steward review |

**Why conformal rather than a parametric error model:** in spatial prediction, conformal intervals achieved **93.67% empirical coverage at 90% nominal, versus 68.33% for bootstrap** `[S-53]`; the difference is exactly the kind of silent under-coverage that makes a field team stop trusting the system.

## 14. Policy and permission layer

| Gate | Rule | Type | Source |
|---|---|---|---|
| `LG-01` | Vendor content: lat/lng cached ≤30 days; no permanent storage of other content; no training on API output | Hard | Google Maps Platform Service Terms §6 `[S-48]` |
| `LG-02` | Nominatim: ≤1 req/s, no bulk use, identify the application | Hard | Nominatim usage policy `[S-51]` |
| `LG-03` | data.gov.in sources are non-commercial (NDSAP); not mixed into a commercial pipeline | Hard | `[S-65]` |
| `LG-04` | Canonical coordinate must be field-confirmed (ours), never a vendor pin | Hard | Follows from LG-01 |
| `LG-05` | No address of a dispute-flagged account may enter the field queue (PS2 `PG-06` wins) | Hard | Cross-system policy |
| `LG-06` | Media (photographs) retained per client data-retention policy; hashes may be retained for integrity | Hard | DPDP minimisation `[VERIFIED]` |
| `LG-07` | Directions/navigation shown via a licensed provider at use time, not stored | Hard | `[S-48]` |

**Design consequence, stated plainly:** PS3's *canonical* layer is legally required to be evidence we own. That is not a compliance footnote — it is the reason the confirmation-and-promotion mechanism is the core of the architecture rather than an add-on.

## 15. Economic layer

```text
Value of location certainty for an account:
    V(i) = P(met | address belief) · ENV(recovery | met) − VisitCost
    and  ΔV(i) = V(i | belief after confirmation) − V(i | belief now)
Visit a field slot on address i iff  ΔV(i) > 0 and it ranks within the PS2 capacity constraint.
```

| Parameter | Central | Range | Source |
|---|---|---|---|
| Field slot cost | ₹180 | ₹90–350 | `[ASSUMPTION]` (travel time included) |
| Trace cost (comparison) | ₹104 | ₹60–150 | `[DATA]` |
| Value of a met visit (recovery term) | account-specific from PS2 EV | — | PS2 computes; PS3 consumes |
| Cost of a wasted visit | = slot cost + expected recovery foregone | — | Derived |
| Measured waste today | `not_traceable` + `locked` = 2,649 of 5,578 visits (47.5%) `[DATA]` | — | `[DATA]` |

**Where the money is:** the 47.5% of visits that end `not_traceable` or `locked` are the candidate pool for the radius + integrity + confirmation architecture; the honest target is not "eliminate them" (a locked house is not a location error) but **separate the location-error subset from the genuinely-absent subset** and stop spending slots to rediscover it.

## 16. Risk-sensitive layer (irreversible actions and poison control)

| Risk | Control | Evidence |
|---|---|---|
| A wrong promotion becomes permanent truth | Two independent confirmations; revocation path | `[S-56]`, `[DATA]` (single-visit poisoning risk) |
| A dishonest agent corrupts the map | Integrity gate before fusion; per-agent pass-rate monitor; exclusion pending review | FA009 162/172 duplicate media `[DATA]`; spoofing is caught by cross-signal inconsistency `[S-58]` |
| A negative outcome drags belief to the wrong place | Hard rule: negative outcomes never move the point | `not_traceable` check-ins 1,603 m from truth `[DATA]` |
| Wide radius mis-sold as precision | `P(within 200 m)` published, never a bare coordinate | §13 table |
| Licence breach by caching | Provider layer + audit log + 30-day TTL enforced in the data model | `[S-48]` |
| Over-flagging good visits | Published false-positive rate on flagging; tunable threshold | `[DATA]` validation on 1,477 visited addresses |

**λ-equivalent for PS3:** the promotion threshold (2 confirmations) and the minimum dwell are the risk parameters; both are published, both are tunable, and every rejection records which rule fired.

## 17. Allocation and optimisation layer (with PS2)

PS3 does not own the field-slot decision — **PS2 does**. PS3 supplies the *inputs* and the *acquisition score*:

```text
acquisition_score(i) = ΔV(i) · account_value_i / slot_cost
subject to: field-slot capacity (PS2) · notice rule (PG-02) · no dispute-flagged accounts (LG-05)
            per-officer geographic clustering to keep travel sane (production)
```

| Mode | Scope |
|---|---|
| Demo | Ranked list + the marginal slot value printed; 50-slot budget from the brief |
| Production | VRP-style routing with clusters (OR-Tools), matching the mTSP formulation used in the 2026 multi-criteria framework `[S-31]` |
| **Not built** | Continuous fleet optimisation — out of scope without real officer shift data `[GAP]` |

## 18. Actions and their failure paths

| Action | Success | Failure modes | Handling |
|---|---|---|---|
| Geocode address | point + stratum | provider outage · quota · partial match · nonsense result | Fallback to gazetteer locality point + wide radius; log the degradation; queue for field |
| Parse address | structured fields | unparsable (script/abbreviation) | Fall back to whole-string geocode; mark `parse_failed` for steward |
| Nav/route to address | officer arrives | pin wrong (the normal case at pincode stratum) | **Deliver a radius and a landmark hint, not just a pin**; the app must show "you are within the search area" |
| Visit capture | outcome + GPS + photo | no GPS fix · spoofed fix · no signal · app crash | Offline queue with local storage, upload-on-reconnect; a visit without a trail is `uneditable` and cannot promote |
| Integrity check | pass/reject with code | false positive on a good visit | Threshold tuning with published FP rate; officer can appeal with reason |
| Promotion | canonical coordinate | contradiction later discovered | Revocation event + steward review; downstream consumers notified |
| Provider switch | continuity | terms differ per provider | Provider abstraction with per-provider policy object; audit log per call |

## 19. Event sourcing, audit and replay

**Events (shared vocabulary with PS2 — see File 11):** `address.parsed`, `address.geocoded` (with provider + terms version), `visit.completed`, `visit.rejected_integrity`, `evidence.appended`, `coordinate.promoted`, `coordinate.revoked`, `provider.call` (audit), `radius.recalibrated`.

- Append-only; state is a projection; any address's belief history is reconstructible at any timestamp ("what did we believe on 12 August, and why?").
- The provider audit log is a first-class output: it is the evidence shown to legal that LG-01/LG-02/LG-03 hold.
- Promotion/revocation pairs form the map's changelog — the artifact that makes the compounding asset auditable.

## 20. Feedback loop, promotion and active learning

```text
visit.completed ─► integrity gate ─► evidence.append ─┬─► fusion (belief update)
                                                      ├─► confirmation_count++ → promotion at 2
                                                      └─► acquisition model refresh
promotion ─► retrieval index gains a high-precision entry ─► future addresses in that building/street are easier
```

| Loop | Cadence | Effect |
|---|---|---|
| Evidence → belief | event-driven | per-address accuracy |
| Belief → stratum calibration | weekly (or at label arrival) | radius table; coverage monitor |
| Confirmation → retrieval index | event-driven | compounding accuracy for neighbours |
| Promotion audit | monthly | revocation review |
| Agent integrity | weekly | exclusion/review decisions |

**Active learning with restraint:** the acquisition score is used to *order* visits (a ranking change PS2 can act on), never to trigger extra visits on its own. This keeps PS3 out of the "experimenting on borrowers" territory that the brief warns about.

## 21. Data mapping — the dataset controls the design (Part N)

| Table | Rows | Columns consumed | Trap preserved |
|---|---|---|---|
| `addresses.csv` | 3,117 | `address_id`, text, town, locality | 3,117 for 2,400 accounts → many-to-many link table |
| `baseline_geocodes.csv` | 2,880 (**237 missing**) | lat/lng, `precision`, `partial_match` | Missing geocode is a first-class state (`prior_only`→field task), never a silent skip |
| `surveyed_addresses.csv` | 100 | ground truth | The **only** labelled set; used for strata + conformal, stratified not per-address |
| `visit_gps_points.csv` | 160,406 | lat/lng, `accuracy`, ts | Median 9.8 m; accuracy is a 68%-radius convention `[S-57]`; 645 check-ins >500 m from own trail |
| `field_visits.csv` | 5,578 (1,477 addresses) | `outcome`, dwell, check-in coords | Negative outcomes must not move points; `address_not_traceable` sits 1,603 m from truth |
| `landmarks_poi.csv` | 240 | landmark name, location | Incomplete, 14/14 names repeat → priors only |
| `localities.csv` / `towns.csv` | 36 / 3 | gazetteer | Per-town calibration required (radius differs by town) |
| photos (hash only) | — | duplicate-hash check | FA009 26.6% duplicates → integrity signal |
| `verified_contact_points.csv` | 250 | *not used in PS3* | Belongs to PS2; listed to prevent accidental misuse (post-hoc, dated 2026-07-02) |

**Standing rule:** no coordinate in the deliverable is presented as ground truth unless it comes from `surveyed_addresses.csv` or from a 2-confirmation promotion.

## 22. Evidence catalogue and evaluation-integrity rules

| Evidence feature | Source | Guard |
|---|---|---|
| Vendor stratum (`precision`) | `baseline_geocodes` | Static, no leakage |
| Parse fields | parsed text | Deterministic |
| GPS cluster stats (spread, dwell, points, accuracy median) | `visit_gps_points` | **As-of**: only visits before the evaluation time |
| Outcome sign | `field_visits` | As-of; **negative outcomes excluded from point-moving evidence** |
| Integrity status | derived | Computed before fusion; flags never used as labels |
| Confirmation count | event-derived | As-of |
| **Banned** | Vendor pin as a *label*; `verified_contact_points` as a label; any future visit; post-hoc survey timestamps leaking into features | Enforced by a test that fails the build |

**Evaluation-integrity rule (from the dataset traps):** the 100 surveyed addresses are *labels*, not features. Every reported accuracy number states whether the surveyed set was inside or outside the calibration fold, and stratum tables are always reported as **two independent samples** because that is the evidence available `[DATA]`.

## 23. Interfaces and contracts

| Endpoint | Purpose | Key fields |
|---|---|---|
| `POST /address/ingest` | Parse + normalise + retrieve | address text → structured + candidates |
| `GET /address/{id}/belief` | Belief and evidence | point, radius p50/p90, stratum, confirmations, integrity |
| `GET /address/{id}/p_within?r=200` | **The PS2 contract** | probability + stratum + confidence class |
| `POST /visit/evidence` | Officer submission | outcome, trail, dwell, media hashes → gate decision |
| `POST /address/{id}/promote` | Promotion (system-only) | requires 2 independent confirmations; returns event |
| `GET /acquisition/queue` | Ranked confirmation targets | address, ΔV, slot cost, notice status |
| `GET /audit/provider` | Provider calls, terms versions | legal/compliance artifact |

**The two-contract rule (from the integrated design):** PS3 exposes `P(within r)` and receives `visit.completed`; PS2 exposes `visit_value_estimate` and receives promotions. Nothing else crosses the boundary — deliberate narrowness keeps both systems honest and independently testable.

## 24. Storage and schema

```sql
-- Demo: SQLite/Postgres on the dataset's metric plane. Production: PostGIS with SRID 4326.
CREATE TABLE address_state (
  address_id text PRIMARY KEY,
  belief_lat numeric, belief_lng numeric,
  radius_p50 numeric, radius_p90 numeric, stratum text,
  p_within_200m numeric, confirmation_count int, canonical boolean,
  integrity_status text, last_verified_at timestamptz);

CREATE TABLE address_evidence (
  evidence_id text PRIMARY KEY, address_id text, visit_id text,
  kind text,  -- gps_cluster | outcome | landmark | vendor | document
  weight numeric, payload jsonb, integrity text, ts timestamptz);

CREATE TABLE promotion_event (
  event_id text PRIMARY KEY, address_id text, from_state text, to_state text,
  confirmations int, evidence_ids text[], actor text, ts timestamptz);

CREATE TABLE provider_audit (
  call_id text PRIMARY KEY, provider text, endpoint text, purpose text,
  terms_version text, response_cached_ttl_days int, ts timestamptz);

CREATE TABLE radius_calibration (
  town text, stratum text, n int, p50 numeric, p90 numeric,
  p_within_100 numeric, p_within_200 numeric, p_within_500 numeric,
  sample text,  -- 'survey' | 'field_confirmations'
  as_of date);
```

Schema-enforced honesty: `address_state` has **no single-radius column** — a p50 and a p90 are structurally required; `provider_audit.response_cached_ttl_days` makes the 30-day rule visible in the data model.

## 25. Training and evaluation protocol

There is deliberately **very little training** in SUTRA, and that is a design claim:

| Component | Method | Evaluation |
|---|---|---|
| Parsing | Open pretrained NER + rules | 30 hand-labelled addresses; field-level accuracy |
| Fusion weights | Empirical grid search by stratum, selected on the surveyed sample | Improvement over baseline on two independent samples; must improve ≥80% of cases where evidence exists (`[DATA]`: 87%) |
| Radius table | Empirical quantiles + split conformal | Coverage at 90% nominal; two-sample agreement |
| Integrity thresholds | Rules + per-agent distributions | False-positive rate on 1,477 visited addresses; spoof-detection recall on the flagged set |
| `P(me t)` / stratum priors | Base rates | Brier vs base rate |
| Learned candidate ranker | **Excluded** (oracle 370 m; 100 labels) | Would be reported with an explicit "tuned and tested on the same 100" caveat if attempted |

**Protocol:** all evaluation on the surveyed set uses leave-one-town-out where possible; every table states its sample; synthetic-data limitation acknowledged in every accuracy claim (§30.3).

## 26. Inference pipeline and latency

| Path | Budget | Design |
|---|---|---|
| Offline batch (nightly) | minutes | Fusion over new visits, calibration refresh, promotion evaluation |
| On-demand address belief | <50 ms | Precomputed state read + contract value |
| Officer app: submit evidence | <200 ms local | On-device integrity pre-check, queue locally, upload on connectivity |
| Officer app: search radius & hint | instant (cached) | Works with **no network** — a hard requirement in the field |
| Provider geocode | 100–600 ms | Only on ingest or re-prior; never on the officer's critical path |
| Degradation | immediate | Provider down → gazetteer prior + wide radius; fusion unavailable → last state, flagged; gate unavailable → **no promotion** (fail-closed) |

## 27. Monitoring, drift and degradation

| Monitor | Threshold → action |
|---|---|
| Coverage (nominal vs empirical radius) | gap >5 pp → recalibrate; >10 pp → mark town `low-confidence` and widen published radii |
| Promotion rate | spike → audit (possible agent gaming); zero → check the queue is fed |
| Integrity rejection rate | >15% for an agent → review; portfolio-wide spike → retrain rules |
| Median error on confirmed addresses | regression → investigate fusion change before release |
| Provider partial-match rate | rise → re-prior or add provider |
| Address drift (new localities, renamed streets) | gazetteer refresh; unmapped addresses flagged for steward |
| Field-slot hit rate (`met_*`) | drop → the allocation contract or the radius table is wrong; alert PS2 |
| Duplicate-media rate | per-agent outlier test weekly `[DATA]` precedent |

## 28. Explainability

1. **Address belief card:** current point, p50/p90, stratum, evidence list with weights, confirmations, integrity status, and the last change with its event id.
2. **Field-officer view:** search radius, landmark hint, "why this radius" (one line: "locality-level address, last confirmed 14 months ago"), confirmation capture flow.
3. **Portfolio view:** error distribution by town and stratum; coverage; confirmation coverage; slot hit rate.
4. **Provider audit:** every external call with its licence version.

Rule: no explanation may reference information that is not in `address_evidence` or `provider_audit`.

## 29. Compliance and licence traceability

| Item | Status | Enforcement |
|---|---|---|
| Google Maps Platform Service Terms §6 (cache ≤30 days; no storage of other content; no training on output) | `[VERIFIED]` | `LG-01`, provider layer, TTL column |
| Nominatim usage policy (1 req/s; no heavy use) | `[VERIFIED]` | `LG-02`, rate limiter |
| data.gov.in NDSAP (non-commercial) · India Post directory | `[VERIFIED]` | `LG-03`, licence register |
| Overture addresses (open, licence-permissive) | `[VERIFIED]` | Preferred source for a gazetteer extension |
| Mappls / eLoc (India-hosted; pricing not public) | `[VERIFIED, pricing UNKNOWN]` | Candidate provider; commercial terms to be obtained |
| Android `Location.getAccuracy()` = 68% radial confidence; `isMock` flag | `[VERIFIED]` | Fusion weighting and integrity gate |
| DPDP Rules 2025 — purpose limitation & minimisation | `[VERIFIED]` | Media hashes retained, photographs per client policy; address data used only for recovery |
| RBI Amendment Directions (effective 1 Jan 2027) — visit notice and hours | `[VERIFIED]` | `LG-05` + PS2 gate `PG-02` |
| Synthetic dataset caveat | README declares synthetic; landmarks incomplete | Every `[DATA]` claim carries the label |

## 30. Build plan, metrics, demo, and open risks

### 30.1 48-hour build order (matches the backlog in §6)

| Phase | Hours | Deliverable | Acceptance number |
|---|---|---|---|
| S-A | 0–2 | Subset + integrity gate on real data | Reproduce: 645 check-ins (11.6%) >500 m; FA009 duplicates 162/172 `[DATA]` |
| S-B | 2–6 | Stratum radius table + `P(within 200 m)` | Two-sample agreement; coverage published |
| S-C | 6–12 | Fusion on met-visits | Reproduce 385 m → 29 m; 82% <100 m `[DATA]` |
| S-D | 12–18 | `ADDRESS_STATE` + evidence store + promotion rule | One address promoted live from two visits with evidence visible |
| S-E | 18–26 | Contract wire to PS2 | Changing a radius visibly changes the field-slot ordering |
| S-F | 26–34 | Parse + retrieval (basic) | 30-address parse eval; retrieval returns candidates or abstains |
| S-G | 34–42 | Officer view + demo narrative | Live: the same address before/after evidence, radius shrinking |
| S-H | 42–48 | Write-up, red-team, freeze | Every number labelled `[DATA]` / `[S-nn]` / `[ASSUMPTION]` |

**Cut-line:** S-B + S-C + S-E ship first (they are the measured claims and the integration); S-D next; S-F/S-G shrink to a scripted demo if needed. The submission never degrades to "we call an API".

### 30.2 Metrics the judges should check

| Claim | Metric | Baseline | Ours | Class |
|---|---|---|---|---|
| Honest error band | median error by stratum | 376 m overall | 37.7 / 134.9 / 367.4 / 1,336.5 m | `[DATA]` |
| Field-evidence gain | median error on met visits | 385 m | **29 m** (82% <100 m) | `[DATA]` |
| Intervals are truthful | empirical vs nominal coverage | 68.33% (bootstrap) | 93.67% (conformal) | `[S-53]` |
| Bad evidence is excluded | flagged check-ins | 11.6% unflagged | flagged, excluded from learning | `[DATA]` |
| Compounding | confirmations per address | 0 (no mechanism) | promotion on 2 → retrieval index | design + `[S-56]` |
| Compliance | vendor content retention | unmanaged | TTL-enforced, audited | `[S-48]` |

### 30.3 Open risks and honest limits

| Risk / limit | Consequence | What would change it |
|---|---|---|
| 100 surveyed addresses only | Radii are stratum-level, not per-address; a new town needs its own calibration | More labels |
| Synthetic data | The 29 m result is a mechanism demonstration on synthetic evidence; real GPS in dense Indian cities will be worse | A real pilot extract |
| No road graph | Stop detection substitutes for map matching; door-level inference is heuristic | OSM extract + HMM `[S-54]` |
| Field coverage | Most addresses will never be visited at mobile precision → the honest radius is the answer, not a point | Field programme or third-party verification |
| Agent gaming | Integrity rules catch the crude cases (duplicate media, teleport) but not all | Device telemetry, more signals |
| Provider pricing/terms for Mappls | Unknown `[UNKNOWN]` → cost model incomplete | Commercial negotiation |
| Real-world address ambiguity | Cultural/landmark naming is not fully modelled | A real gazetteer and local knowledge capture |


## XV.11 — File 11 — the integrated system

*Source file: `SANKET_SUTRA_SYSTEM_ARCHITECTURE_FINAL.md`*

# SANKET–SUTRA — INTEGRATED SYSTEM ARCHITECTURE (FINAL)

**Phase 4, File 11 of 13.** The two problem statements as **one system**, not two boxes joined by an arrow.

**Companions:** `PS2_SANKET_SOLUTION_ARCHITECTURE_FINAL.md` · `PS3_SUTRA_SOLUTION_ARCHITECTURE_FINAL.md` · `ARCHITECTURE_DECISION_LOG_FINAL.md` (ADR-29/30/31 are the integration decisions) · `ARCHITECTURE_RESEARCH_BIBLIOGRAPHY.md`.

---

## 1. Why "integrated" is a claim that has to be earned

Two systems are integrated — rather than merely co-located — only if **removing the interface changes a decision on both sides**. For SANKET and SUTRA that test is met exactly once, and the whole document is built around that one place:

> **A field visit is the only action in the system that purchases two kinds of information at once — identity and location — and it is irreversible. Neither PS can price it alone: PS2 knows the recovery value, PS3 knows the location uncertainty, and only their combination can decide whether a slot is worth spending tonight.**

Everything else in this file exists to make that sentence operational and to keep the two systems from becoming entangled while it happens.

---

## 2. The joint belief

```
                 LOCATION BELIEF (PS3)                     IDENTITY / REACHABILITY BELIEF (PS2)
        ┌───────────────────────────────────┐     ┌────────────────────────────────────────────┐
        │ point · radius(p50,p90) · stratum │     │ P(borrower) · P(answered) · state ·        │
        │ confirmations · integrity status  │     │ dead_streak · exposure_flag · decay        │
        └───────────────────┬───────────────┘     └──────────────────┬─────────────────────────────┘
                            └──────────────┬───────────────────────────┘
                                           ▼
                          ┌────────────────────────────────────────────┐
                          │  DECISION SURFACE (computed once per case) │
                          │  ENV(call)  ENV(trace)  ENV(visit)  ENV(wait)│
                          │  + EVSI(trace) + EVSI(visit) − λ·Risk(visit) │
                          └───────────────────┬────────────────────────┘
                                              ▼
                        ┌──────────────────────────────────────────────┐
                        │  CAPACITY ALLOCATOR (PS2, day-level)         │
                        │  agent-minutes · ₹ trace budget · field slots │
                        └──────────────────────────────────────────────┘
```

**Why the product and not the sum:** a call is cheap, reversible and buys identity information only. A trace is cheap-per-unit, reversible, buys identity only, and cannot be acted on if the location belief is too weak for a visit anyway. A visit buys both and cannot be undone. That makes visit scheduling a **joint** decision by construction, not by convention.

## 3. The two contracts (and nothing else)

| Direction | Payload | Cadence | Owner | If it breaks |
|---|---|---|---|---|
| PS3 → PS2 | `p_within_200m`, `radius_p50/p90`, `stratum`, `integrity_status`, `coordinate.promoted` / `coordinate.revoked` events | event-driven + nightly refresh | PS3 | PS2 falls back to stratum radius from the last nightly snapshot; the visit EV is recomputed with wider uncertainty and fewer slots are approved (conservative default, logged) |
| PS2 → PS3 | `visit.completed` (outcome, dwell, trail ref, media hashes), `visit.requested` (address, value of confirmation) | event-driven | PS2 | PS3 keeps its last queue; no promotion can occur without evidence, so nothing corrupts |

**Interface discipline:** there is no third contract. Coordinates are never shared raw; identity probabilities are never computed in PS3; the allocator never queries PS3 synchronously in the officer's critical path. If a proposed integration needs a new field, it must be added to this table with its failure behaviour first.

## 4. The joint event log (one log, two views)

| Event | Emitted by | Consumed as PS2 state | Consumed as PS3 state |
|---|---|---|---|
| `call.completed` | dialer | dead_streak, reach_p, identity evidence | — |
| `trace.returned` | trace orchestrator | new point or point killed; EVSI base-rate refresh | possible address change on the point |
| `payment.received` | payments | value model, streak reset | — |
| `visit.completed` | field app | identity ≥0.95 if met; slot consumed | evidence appended; confirmation count |
| `visit.rejected_integrity` | field app / PS3 gate | slot consumed, evidence excluded | agent flagged; address unchanged |
| `coordinate.promoted` | PS3 | address confidence band update | canonical store, retrieval index |
| `coordinate.revoked` | PS3 | confidence band reset; alert | audit, steward queue |
| `refusal.recorded` | PS2 gate / EV / EVSI | refusal ledger | — |
| `override.recorded` | supervisor | reason code; weekly review | if address-related, routed to steward |
| `policy.versioned` | both | replay harness | replay harness |

**Why one log:** audit ("why did we not visit this account on 12 August?"), replay ("what would the January policy have done?"), and the simulation twin all need a single ordered truth. Two logs would make the integrated claim untestable. `[S-59]`

## 5. The joint objective

```text
Maximise over the planning horizon (one day, one shift):
    Σ_calls   [ P(RPC)·Value(RPC) − AgentCost − λ·ConductRisk ]
  + Σ_traces  [ EVSI_trace − ₹104 ]                              (0 if EVSI ≤ price)
  + Σ_visits  [ P(met | identity, location)·Value(met)
                + Value_of_location_certainty(Δuncertainty)      ← the PS3 term
                − SlotCost − λ_visit·ConductRisk ]
  + Σ_waits   [ option value of better information ]
subject to: compliance rules (hard) · agent minutes · ₹ trace budget · field slots (hard)
            two-confirmation promotion rule (hard) · one action per point per window (hard)
```

**Every term has an owner and an evidence class:**
`Value(RPC)` PS2, parameterised · `AgentCost` parameter · `EVSI_trace` PS2, measured base rates · `SlotCost` parameter · `Value_of_location_certainty` PS2/PS3 joint, parameterised · `λ, λ_visit` published policy · `Δuncertainty` PS3, measured (`P(within 200 m)` before/after) · compliance rules `[VERIFIED]`.

## 6. The one joint decision, worked end-to-end

**Case:** account in DPD-60 with one *reference* point (P(borrower) ≈ 0.16 `[DATA]`) at an address whose vendor stratum is **locality** (radius p90 ≈ 385 m `[DATA]`).

| Step | Computation | Result |
|---|---|---|
| 1. PS2 gate | reference point + P(borrower) 0.16 < θ_identity | disclosure **prohibited**; identity-led contact only |
| 2. PS2 EV | calling the reference buys almost no recovery value | ENV(call) small |
| 3. PS2 EVSI(trace) | ₹104 vs information that would only matter *if* a visit followed | trace refused **unless** a visit is next |
| 4. PS3 supplies | `P(within 200 m)` at locality stratum | ≈0.35 (wide) |
| 5. Joint EVSI(visit) | visit buys identity **and** raises `P(within 200 m)` toward 0.82 measured `[DATA]`; but at 0.35 start probability the visit is likely to end `not_traceable` (47.5% of visits already do `[DATA]`) | visit **refused**, or deferred until a trace/verification improves identity |
| 6. Allocator | slot goes to a rooftop-stratum address with a verified identity | the slot is not wasted |
| 7. Record | refusal with code `PG-04/PG-09`, counterfactual value with range; PS3 receives nothing | audit trail complete |

**The same case after two confirmations** (a later visit succeeded): `P(within 200 m)` rises, `stratum` upgrades, the visit EV crosses the threshold, and the address enters the retrieval index — cheaper for every future query in that street. That is the compounding loop, and it is only visible in the integrated view.

## 7. Division of labour (who owns what, and why not the other way round)

| Capability | Owner | Why not the other |
|---|---|---|
| Recovery value of contact | PS2 | PS3 has no portfolio economics |
| Compliance gate | PS2 | Rules are about contact conduct, not places |
| Location belief & radius | PS3 | PS2 has no spatial evidence |
| Field-slot approval | PS2 | It is a capacity decision across the whole portfolio, not a per-address one |
| Evidence integrity | PS3 | It is location-evidence quality |
| Identity posterior | PS2 | It is a contact/relationship property; PS3 consumes it only via `visit.completed` |
| Cost of a visit | PS2 (parameter) | PS3 reports the *information gain*, not the price |
| `Δuncertainty` per address | PS3 | Only PS3 can compute the before/after coverage |

## 8. Sequence: one planning day

```text
02:00  PS2 nightly: state projection → features → scores → gate → EV/EVSI → ENV matrix
02:30  PS3 nightly: new visits → integrity gate → fusion → calibrations → radius refresh → publication
03:00  JOINT: ENV(visit) computed with PS3's fresh radius; allocator solves capacity; plan frozen
03:15  Plan written as action tokens (expiry, rule trace, permitted window, notice proof for visits)
08:00  Execution begins. Dialer + field app consume tokens. Expired tokens are not executed.
       Real-time: point switch mid-call → gate + EV only (cached state, <300 ms, no model call)
       Field: officer sees radius + landmark hint; submits outcome, trail, media, offline-tolerant
18:00  Field sync: PS3 integrity gate → fusion → confirmation counts
19:00  Window closes (regulatory). Any queued outbound action after 19:00 is refused with PG-01.
19:30  Daily close: outcomes, refusals, overrides, degradations written; PS2 belief updated
       → tomorrow's plan starts from a better belief, and the refusal summary goes to the supervisor
```

## 9. Where the two systems could contradict each other — and how it is prevented

| Contradiction | Prevention |
|---|---|
| PS2 schedules a visit to an address PS3 rates `low-confidence` | Visit ENV includes `P(within 200 m)`; below a floor, the allocator cannot select the visit (soft constraint → hard below the floor) |
| PS3 promotes a coordinate while PS2 has the account dispute-frozen | `LG-05`: dispute-flagged accounts are excluded from the field queue; promotion is still allowed (the address is a fact, the contact is not) |
| PS2 counts a visit as a met contact using an integrity-rejected visit | `visit.rejected_integrity` never sets `identity ≥ 0.95`; the slot is counted as consumed, the evidence is not used |
| PS3 learns from a negative outcome and drags the point | Hard rule: negative outcomes never move the point (ADR-23) |
| The plan is computed on stale radii during a provider outage | PS2 marks the plan's radius source ("fresh" / "snapshot ≤24 h"); the allocator reduces visit slots when stale |
| Overrides on both sides collide | Override is a PS2 concept; PS3-side disputes route through the steward queue with its own event type |

## 10. Deployment topology

```text
┌───────────────────── DEMO (48 h) ─────────────────────┐   ┌──────────── PRODUCTION ────────────┐
│  Python services in one repo                          │   │  Same decomposition, different     │
│  ├─ sanket/  (state, gate, EV, EVSI, greedy alloc)     │   │  substrate:                        │
│  ├─ sutra/   (parse, retrieve, integrity, fusion)      │   │  • streaming state projection      │
│  ├─ shared/  (event log, contracts, schemas, costs)    │   │  • rulebook service (versioned)    │
│  ├─ demo/    (decision cards, plan view, replay)       │   │  • PostGIS + object storage        │
│  Database: SQLite/Postgres on the dataset metric plane │   │  • MILP nightly, VRP routing       │
│  Provider calls: none in the demo path                 │   │  • provider abstraction + audit    │
└────────────────────────────────────────────────────────┘   └────────────────────────────────────┘
```

**Same code path, different scale:** the demo does not implement a toy version of the architecture; it implements the same layers with batch execution, a single node, and parameterised capacity. The production delta is stated in the decision log, not hidden.

## 11. Simulation twin (BUILD IF TIME)

Feed the joint event log into a week-long replay: same accounts, candidate policy, outcomes sampled from measured conditional rates `[DATA]` (reach by hour, third-party by provenance, trace hit rate, met-by-stratum, payment|RPC). Outputs: cashflow, contacts, compliance counters, field-slot utilisation, refusal counts.

**Honest labelling:** it is a **mechanism demonstration on synthetic rates**, not a forecast. It exists so a capacity change can be argued with numbers instead of opinions, and so the 1 Jan 2027 window rules can be rehearsed before they bind.

## 12. What integration unlocks that neither system has alone

| Capability | Alone | Joint |
|---|---|---|
| Priced field slot | PS2 sees a visit as a cost with an uncertain payoff | Visit ENV uses `P(within 200 m)`: a slot is approved only when the address is likely findable **and** the identity is verified |
| Trace-vs-visit choice | PS2 compares two costs without a location term | Both are information purchases on the same EVSI axis; the cheaper purchase that raises decision value most wins |
| Identity × location uncertainty | Each modelled separately | A visit is the only action that reduces both — so "send a visit to learn who this is" becomes an explicit, priced strategy rather than a last resort |
| Confidence-weighted capacity | Capacity spent on list order | Capacity spent where certainty is worth money |
| Refusal with a reason | Rule refusals only | Refusals that include *"the address is not findable enough to justify the slot"* — a reason no single-statement system can produce |
| Compounding | PS3 improves its map; PS2 improves its lists | Every visit improves both, and the improvement is priced back into the next plan |

## 13. Risks specific to the integration

| Risk | Mitigation |
|---|---|
| Integration becomes decorative (two boxes, one arrow) | The joint decision in §6 is in the demo script and the plan; if a judge removes PS3, the visit ordering must visibly degrade — that is the test |
| Latency coupling | Only nightly and event-driven coupling; the officer's critical path never calls PS2 |
| Ownership ambiguity over the visit | PS2 approves, PS3 informs, the field app executes; written in §7 with one owner per capability |
| Contract drift between teams | Contract table (§3) is versioned with the policy version; a mismatched contract version refuses the plan rather than guessing |
| Double counting the same evidence | Identity evidence is used in PS2 only; location evidence in PS3 only; the visits' *outcome* is shared but never re-weighted twice |

## 14. Build order for the integrated deliverable

| Order | Component | Acceptance |
|---|---|---|
| 1 | Shared event log + vocabulary + schemas | A single replay reconstructs both states |
| 2 | PS3 calibrated truth (`p_within_200m`, radii) | Two-sample agreement published `[DATA]` |
| 3 | PS2 gate + refusal ledger | 100% of refusals coded with counterfactual range |
| 4 | PS2 EV + EVSI (traces) | Reproduces ₹104 / 22.8% / 77% waste |
| 5 | PS3 fusion + integrity gate | Reproduces 385 m → 29 m; 645 flags `[DATA]` |
| 6 | **Joint visit EV and allocator** | Changing `P(within 200 m)` visibly re-orders field slots |
| 7 | Replay + demo narrative | One case's full journey: refusal → improved belief → action |
| 8 | Simulation twin | Capacity change → measurable plan change |

## 15. Closing statement

The two statements share one decision — *what is this account worth spending tonight, and on what evidence* — and they answer it from two sides of the same belief: who this person is, and where this place is. Everything else in this submission is the discipline of not confusing those two questions, not guessing at them, and recording the answer, including when the answer is no.


## XV.12 — File 12 — source register

*Source file: `ARCHITECTURE_RESEARCH_BIBLIOGRAPHY.md`*

# ARCHITECTURE RESEARCH BIBLIOGRAPHY

**Phase 4, File 12 of 13.** The source register for every `[S-nn]` citation used in Phase-4 files (`SIMILAR_SYSTEMS_REVERSE_ENGINEERING.md`, `PS2_ADVANCED_ARCHITECTURE_RESEARCH.md`, `PS3_ADVANCED_ARCHITECTURE_RESEARCH.md`, `PS2_ARCHITECTURE_OPTIONS.md`, `PS3_ARCHITECTURE_OPTIONS.md`, `FRONTIER_PS2_PS3_ARCHITECTURES.md`, `PS2_ARCHITECTURE_SELECTION.md`, `PS3_ARCHITECTURE_SELECTION.md`, `PS2_SANKET_SOLUTION_ARCHITECTURE_FINAL.md`, `PS3_SUTRA_SOLUTION_ARCHITECTURE_FINAL.md`, `SANKET_SUTRA_SYSTEM_ARCHITECTURE_FINAL.md`).

**Reading rules.**
- `Source class` follows the project's source-priority order: **R** regulatory/official · **V** vendor/product documentation · **A** academic · **I** industry/technical press · **P** patent · **O** open-source · **D** dataset.
- `URL status`: **confirmed** = URL recorded during the session and re-used verbatim; **derivable** = URL constructed from a recorded stable identifier (patent number, arXiv id, docs path) — safe to reconstruct; **product page (moves)** = vendor marketing URL that changes without notice — cite by product name if it 404s; **unconfirmed** = the source was captured with citation details (title/venue/year) but its URL was **not** recorded in the session register. Per the project's "invent nothing" rule these are marked rather than guessed, and the citation is sufficient to locate the item.
- This register is **Phase-4 only**. Phase-1 sources (~191 URLs) are embedded with their URLs in `CreditNirvana_PS2_PS3_Research_and_Strategy.md`; the Phase-1 evidence pass (~90 sources, each with "what it proves / why it matters") is in `PS2_DEEP_INTERNET_RESEARCH.md`, `PS3_DEEP_INTERNET_RESEARCH.md`, `PS2_PS3_RESEARCH_SYNTHESIS.md`, `PS2_PS3_SOURCE_BIBLIOGRAPHY.md`.
- **Numbering note.** The location cluster (S-45 … S-65) was extended during Phase 4. Three citations in the first-written file (`SIMILAR_SYSTEMS_REVERSE_ENGINEERING.md`) were remapped to this register — Google API `S-45→S-47`, Mappls `S-46→S-50`, GeoIndia `S-48/S-49/S-50→S-47bis`, GeoIndia company claims `S-51→S-47bis-prod`, logistics two-confirmation `S-54→S-56`, header `S-57` dropped. This file is authoritative.

---

## 1. Collection decision systems (PS2 cluster)

| ID | Source | Class | URL | URL status | What it proves | Why it matters here |
|---|---|---|---|---|---|---|
| S-1 | Experian — Ascend Intelligence Services / Collect | V | experian.com (Ascend decisioning pages) | product page (moves) | Collections NBA is sold as a **decision strategy** over a deep attribute library (2,100+ attributes) | Sets the expectation for what "next best action" means in the industry; we adopt the strategy framing, not the data assumption |
| S-3 | Experian — Optimize (ex-Marketswitch) | V | experian.com/business/products/decision-analytics/optimize | product page (moves) | **Constraint-based mathematical optimization** over combinations of decisions, evaluated by scenario simulation | The core proof that optimization is a separate engine from prediction — PS2's L6 borrows exactly this |
| S-4 | Experian — Optimize scenario simulation / strategy trees | V | same family as S-3 | product page (moves) | Strategy trees are tested in simulation **before** deployment | Justifies our replay/shadow-mode design (no live experimentation on borrowers) |
| S-5 | Experian — PriorityScore / Collection Advantage | V | experian.com (collections scores) | product page (moves) | Prioritisation is expressed as dollars-weighted scores feeding a work queue | "Prioritisation ≠ prediction" — why our allocator ranks by expected net value |
| S-6 | Experian — skip tracing / data acquisition for collections | V | experian.com (collections data) | product page (moves) | Skip tracing is purchased from **multiple external sources** (bureau, alternative finance, collateral records) | Evidence that information is a priced input → our EVSI layer |
| S-8 | Experian — Ascend ML explainability / collections decisioning | V | experian.com (Ascend) | product page (moves) | Explainability is a shipped feature (adverse-action-style codes from models) | Supports our "decision card" and audit-trail requirements |
| S-8bis | AI-voice / contact-centre economics analyses (Asia-Pacific) | I | industry analyses (as recorded in Phase-1 research) | unconfirmed | Headline AI-voice prices understate effective cost by 2–4× once telephony, integration and supervision are included | Why we do not build a voice bot and treat telephony as an existing capability to be used, not rebuilt |
| S-9 | Experian — collections solutions overview | V | experian.com/business/collections | product page (moves) | The end-to-end collections offer suite (segmentation → treatment assignment) | Context for the industry layer structure |
| S-10 | TransUnion — TruLookup / TLOxp | V | transunion.com (TruLookup) | product page (moves) | Contact intelligence as a **fusion of 10,000+ public/proprietary sources** exposed as a searchable product | Justifies modelling our contact slate as a graph/query surface |
| S-11 | TransUnion — skip tracing (scale figures) | V | transunion.com (skip tracing / TruLookup pages) | product page (moves) | "100B+ records, 11B unique name-address combinations, 4B phone records" `[VENDOR CLAIM]`; **change monitoring** and alerting when contact data changes | (a) The graph+monitoring pattern we adopt; (b) the scale we explicitly do *not* need |
| S-12 | TransUnion — Contact Compliance Risk | V | transunion.com (contact compliance) | product page (moves) | Compliance is a **pre-engagement gate**: verified numbers "currently tied to the correct consumer prior to engagement" | Direct architectural precedent for our L4 gate and for the refusal ledger |
| S-13 | TransUnion — Phone Behavior Intelligence | V | transunion.com (phone behavior intelligence) | product page (moves) | "Contactability" per contact + phone type + in-service indicators + TCPA-risk fields; 15-minute refresh of call-transaction data | Separates *reachable* from *correct party* — adopted as two distinct quantities |
| S-13bis | Shiprocket — open-source Indic address NER (IndicBERT-based) | O | public repository | unconfirmed | A working open model for Indian address entity extraction, shipped by an Indian logistics company | Evidence that the parse layer can be built from open weights rather than a commercial parser |
| S-14 | FICO — Decision Management / simulation capability | V | fico.com (Decision Management Suite) | product page (moves) | Full-scenario simulation over hundreds of millions of transactions is a **first-class platform feature** | Justifies the portfolio digital-twin / replay module |
| S-15 | FICO — human-in-the-loop decisioning | V | fico.com (Decision Management) | product page (moves) | Business users edit strategies; human-in-the-loop is an explicit design goal | Justifies our override-as-event design |
| S-16 | FICO — optimization / decision solver | V | fico.com (decision optimization) | product page (moves) | A solver under constraints and **maximum-risk limits**, used by business users to find the optimal strategy; models drive actions inside rules | The closest public analogue to our L5–L6 layers; also the source of the "business users own the operating point" principle |
| S-17 | FICO — adaptive control / champion–challenger | V | fico.com (adaptive control / decision analytics) | product page (moves) | Test-and-learn champion/challenger is a standard feature of decisioning platforms | Supports shadow/challenger design (and our refusal to run live exploration) |
| S-18 | FICO — TRIAD / Strategy Director | V | fico.com (TRIAD) | product page (moves) | Segment → score → test → report account strategy management; **stateful models executed with low latency**, streaming and batch | Justifies stateful scoring at call time and strategy versioning per decision |
| S-19 | Pega — Customer Decision Hub: engagement policy | V | pega.com (CDH documentation/product) | product page (moves) | Policy sequence **Eligibility → Applicability → Suitability** precedes any scoring; "do nothing" is allowed | The single most-copied pattern in our design: permission before prediction |
| S-20 | Pega — CDH arbitration (`P × C × V × L`) and constraints | V | pega.com (CDH arbitration docs) | product page (moves) | Arbitration = propensity × context × business value × levers; contact limits configured as constraints (e.g. 1 outbound/week) | Shows a real production priority formula — and **that it contains no cost term**, the gap our EV layer fills |
| S-21 | Pega — CDH human control | V | pega.com (CDH) | product page (moves) | The CSR "is always in control and can select other service actions" | Human override is a product requirement, not an afterthought |
| S-22 | Pega — Interaction History / adaptive models | V | pega.com (CDH adaptive analytics docs) | product page (moves) | Interaction-history summaries are used as predictors; adaptive models update continuously from captured responses | Precedent for our event-sourced state as a *feature source*, not just a log |
| S-24 | Credgenics — platform overview | V | credgenics.com | product page (moves) | Indian collections SaaS: digital comms, dialer, field app, legal, payments, analytics on one platform | The integration boundary: we are a decision layer inside such a platform |
| S-25 | Credgenics — compliance controls (DND, frequency, daytime) | V | credgenics.com | product page (moves) | "Comprehensive frameworks for DND, frequency and daytime controls" | Confirms our gate vocabulary matches what Indian vendors already configure |
| S-26 | Credgenics — CG Collect / Maestro module set | V | credgenics.com | product page (moves) | Field collection app + strategy modules exist as products | Evidence the *execution* layer exists and need not be rebuilt |
| S-28 | Spocto X (Yubi) — agentic collections orchestration | V | yubi.io / spocto.com | product page (moves) | Closed-loop execution where outcome signals refine strategies; compliance controls and audit logs | The industry's own words for our L0→L7 loop; also the caution: autonomy without a rules floor |
| S-29 | Mobicule — mCollect | V | mobicule.com | product page (moves) | Offline-first field app, mandatory GPS geo-tagging, liveness face verification, beat plans | Proves field-integrity is a *product feature* in Indian collections → PS3's integrity gate |
| S-30 | Spocto/Yubi press claims on collection lift | I | press releases (as recorded in Phase-1 research) | unconfirmed | Publicly quoted outcome claims from an Indian collections vendor | Cited only as an example of a claim class we refuse to make without measurement |
| S-31 | MCDA decision-support framework for debt collection (2026) | A | journal article, 2026 | unconfirmed | Three layers: rule extraction (unsupervised segments) → prediction (behaviour, best day/time/channel, PTP) → optimization with MCDA + **mTSP field routing** | (a) Our three-layer vocabulary is the industry's; (b) field routing is explicitly an optimization problem; (c) we reject fuzzy logic inside legal gates |
| S-32 | Abe, Melville, Pendus, Reddy, Tan, Gandalf, Jensen, Thomas — "Optimizing debt collections using constrained reinforcement learning", KDD 2010 | A | https://dl.acm.org/doi/10.1145/1835804.1835817 | **confirmed** | Constrained MDP for collections; LP/primal-dual value function; legal rules as constraints | The canonical academic precedent; we adopt the constraint idea, not the MDP |
| S-33 | NYS Department of Taxation & Finance — collections optimization deployment (practitioner paper) | A/I | as recorded in Phase-1 research (government collections optimisation) | unconfirmed | ~300 business/legal rules compiled into **binary action-constraint features**; incumbent-vs-challenger deployment; weekly batch to 30–40 agents + specialised units | The single most useful production detail in the whole review: rules as *features*, and escalation for unmodelled states |
| S-34 | NYS DTF — reported outcome | I | operator-reported (via S-32/S-33 lineage) | unconfirmed | +$83 M collections (+8%) "using the same set of resources" | Evidence that the *allocation* layer, not model AUC, produces the value |
| S-35 | US7519553B2 — collection optimization patent | P | https://patents.google.com/patent/US7519553B2 | derivable | Constrained MDP + constrained RL with an **event store** of dated collection actions and debtor transactions | Precedent for the event-sourced data model we build (we reject the RL machinery) |
| S-36 | "Smart debt collection system" (Design Science, 2025) | A | journal article, 2025 | unconfirmed | Offline deep Q-learning on a factorised MDP with **formal temporal-logic constraints** producing provably compliant policies | The idea that compliance is a *provable property of a policy*; also the warning that its constraints were handcrafted without a specification language |
| S-38 | Sánchez et al. (2022) — contact-centre + financial data fusion for collections | A | journal article, 2022 | unconfirmed | 1,023,418 call records + 26,466 PTPs + 54,349 payments; contact-centre data adds predictive value; **first-touch and follow-up are different problems** | Justifies separating first-contact vs follow-up and treating disposition history as a feature block |
| S-39 | Swaminathan & Joachims — Counterfactual Risk Minimization (JMLR 16, 2015) | A | http://jmlr.org/papers/v16/swaminathan15a.html | **derivable** | Logged bandit feedback is **biased and incomplete**; unregularised IPS can degrade the system | The formal reason our propensity is unusable (≡1.0 on 94.6% of attempts) and why we refuse uplift claims |

## 2. Decision science primitives (PS2 advanced ideas)

| ID | Source | Class | URL | URL status | What it proves | Why it matters here |
|---|---|---|---|---|---|---|
| S-42 | Expected value of sample information (EVSI) methods — Value in Health (2020) review and standard decision-theory treatments | A | PMC8183576 (review) | derivable | EVSI = expected gain in decision value from buying information **before** acting; computable with approximations | The formal basis of our trace/visit purchase rule (BUILD NOW) |
| S-43 | Rockafellar & Uryasev — CVaR optimisation (Journal of Risk, 2000) | A | doi:10.21314/JOR.2000.038 | derivable | CVaR admits a linear-programming formulation — risk sensitivity can be optimised, not just reported | Makes our conduct-tail penalty implementable inside the allocator rather than bolted on |
| S-44 | Splink — Fellegi-Sunter probabilistic record linkage (Ministry of Justice, UK) | O | https://github.com/moj-analytical-services/splink | **confirmed** | Explainable per-field match weights, EM-estimated, scales to 100M+ records, SQL backends | The identity-graph and building-dedup component; explainability for free, no training labels needed |

## 3. Location intelligence (PS3 cluster)

| ID | Source | Class | URL | URL status | What it proves | Why it matters here |
|---|---|---|---|---|---|---|
| S-45 | Indian address-structure parsing literature (address segmentation / geocoding for Indian addresses) | A | as recorded in Phase-1 research (groundwork for S-46) | unconfirmed | Indian addresses are semi-structured and multi-script; parsing quality dominates geocoding quality | Justifies the parse-then-geocode stage rather than sending raw strings to an API |
| S-46 | `addressparser` — IndicBERTv2-Subword + CRF address parser | O | public repository (open weights) | unconfirmed | Field-level address parsing in **<30 ms**, Indic-language support, open licence | Our S1 parser: offline, explainable, no vendor dependency |
| S-46bis | BM25 / retrieve-then-rerank (standard IR practice; Robertson & Zaragoza BM25 lineage) | A | standard IR literature | unconfirmed | Cheap high-recall retrieval followed by an expensive precision stage; rank fusion avoids score calibration | The correct mental model for PS3 candidate generation (and the reason we use rank fusion, not score fusion) |
| S-47 | Google Maps Platform — Geocoding API response reference | V | https://developers.google.com/maps/documentation/geocoding/requests-geocoding | **derivable** | Each result carries `location_type` (ROOFTOP / RANGE_INTERPOLATED / GEOMETRIC_CENTER / APPROXIMATE), `partial_match`, `viewport`, `bounds`, `place_id`, `plus_code` | A vendor's own uncertainty vocabulary — our **stratum key** comes from here, not from ad-hoc thresholds |
| S-47bis | GeoIndia (Meesho) — v1: EMNLP 2024 Industry Track; v2: ACM/CIKM 2025 | A | ACL Anthology (v1) and ACM DL (v2) | unconfirmed | Predicting **hierarchical H3 cells** beats coordinate regression for Indian addresses; v2 fuses Graphormer + LM with cross-attention; >50% mean and >85% p99 error reduction vs Google (paper-reported) | (a) Hierarchy is the right output vocabulary; (b) the reproducibility bar (proprietary corpus) is why we adopt the contract, not the model |
| S-47bis-prod | Meesho/GeoIndia company-reported production figures | I | company engineering/press claims | unconfirmed | 67M+ addresses, "millions of delivery traces", +20 pp accuracy, −5% misroute cost `[COMPANY CLAIM]` | Shows the label source is **field operations** — exactly the loop PS3 names; flagged as self-reported |
| S-48 | Google Maps Platform Service Terms (§6, caching/storage of Geocoding content) | R | https://cloud.google.com/maps-platform/terms | **derivable** | Latitude/longitude may be cached **≤30 days**; no permanent storage of other content; no training on output | Hard constraint: our canonical coordinate must be field-confirmed and ours — the legal foundation of the promotion design |
| S-49 | Google Maps Platform — coverage/geocoding availability (India reference coverage) | V | Google Maps Platform documentation | derivable | Google is the de-facto coverage reference for Indian addresses in the reviewed literature | Used as the baseline against which research papers and our own measurements are compared |
| S-50 | MapmyIndia / Mappls — address standardisation pipeline and eLoc | V | about.mappls.com / maps.mappls.com | product page (moves) | Cleansing → validation & normalisation → standardisation against an address directory, populating missing administrative levels; eLoc addressing | Modular stages we mirror; "missing admin level" as a confidence signal. Pricing not public `[UNKNOWN]` |
| S-51 | OpenStreetMap Foundation — Nominatim usage policy | R | https://operations.osmfoundation.org/policies/nominatim/ | **derivable** | Rate limit ≈1 request/second; no bulk/heavy use; identify the application | Compliance envelope if an open geocoder is used at all |
| S-52 | Overture Maps Foundation — addresses theme | O | https://overturemaps.org / docs.overturemaps.org | derivable | Open, licence-permissive address data with a documented schema | The licence-clean gazetteer extension path (vs non-commercial government data) |
| S-53 | Conformal spatial prediction ("GeoConformal", 2024) | A | https://arxiv.org/abs/2412.08661 | **derivable** | Split conformal with geographically weighted quantiles: **93.67% empirical coverage at 90% nominal**, vs 68.33% for bootstrap | The method behind our per-stratum radii and the coverage monitor; also why we publish coverage rather than claim a guarantee |
| S-54 | Newson & Krumm — Hidden Markov map matching through noise and sparseness (ACM SIGSPATIAL 2009) | A | ACM DL | unconfirmed | Standard HMM formulation for matching noisy GPS traces to a road network | The architecture we explicitly mark RESEARCH ONLY (no road graph in our data) |
| S-55 | Last-mile dispatch geocoding status workflow (Descartes / LogiNext-class platforms) | V/I | product documentation | unconfirmed | Explicit geocoding **status indicators** ("approximately geocoded → flag, confirm before routing") with a manual-review path and permanent capture of dispatcher corrections | The status vocabulary we adopt ("confirm before notice") and the human-review precedent |
| S-56 | Operational geocoding feedback — delivery/q-commerce: two-confirmation auto-update and GPS-error detection | V/A | logistics platform documentation + q-commerce engineering write-ups | unconfirmed | Auto-update a stop's geocode after **repeated field confirmation**; self-supervised detection of bad GPS from address text | The compounding loop (our S8/S9) and the two-confirmation promotion rule — productised in Indian logistics, absent in Indian collections |
| S-57 | Android `Location.getAccuracy()` and mock-location APIs | V | https://developer.android.com/reference/android/location/Location | **derivable** | `getAccuracy()` is a **68% radial confidence** estimate; `isMock()`/`isFromMockProvider` flags simulated fixes | Correct interpretation of the per-point accuracy in our GPS data, and the crude first line of the integrity gate |
| S-58 | GPS spoofing detection stacks (fleet/field-force literature and vendor documentation) | A/V | survey literature + vendor docs | unconfirmed | Spoofing is detected by **cross-signal inconsistency**: mock flags, root/emulator attestation, GPS-vs-IP mismatch, teleport/movement implausibility, duplicate media | The rule set in our integrity gate; also why we refuse a "spoof detection rate" claim (no device telemetry) |
| S-59 | Event sourcing pattern (Fowler; platform documentation) | A/O | https://martinfowler.com/eaaDev/EventSourcing.html | **derivable** | State is a projection of an append-only event log; replay at any timestamp | The mechanism that makes our refusal ledger, audit trail and policy replay possible |
| S-60 | US7257206B2 (GE Capital, 2002) — skip-tracing system | P | https://patents.google.com/patent/US7257206B2 | derivable | Skip queue of account+phone records populated when a number is identified as "good"; skip-tracing documentation; queue **memory** | Precedent that contact queues carry state and documentation — our `CONTACT_POINT_STATE` lineage |
| S-61 | US8,819,061 (LocateSmarter, 2014) — multi-vendor skip tracing | P | https://patents.google.com/patent/US8819061B2 | derivable | Data interchange with **a plurality of skip-tracing vendors** behind one interface | The multi-vendor orchestration pattern behind our EVSI purchase decision |
| S-63 | Field-visit integrity stacks (fleet/field-sales/collections) | V/I | vendor documentation and industry practice | unconfirmed | Layered checks: mock-location flag, rooted/emulator attestation, GPS-vs-IP consistency, teleport plausibility, duplicate-photo and geofence checks | We adopt "weight, don't accuse": signals become evidence weights, not verdicts |
| S-64 | People-search / data-broker platforms for skip tracing `[P/O]` | V | platform product pages | product page (moves) | Consumer-locating platforms expose relationship and asset search as an API product | Commercial context for the identity graph; also the reason we keep the graph internal |
| S-65 | data.gov.in — NDSAP licensing (and India Post PIN/locality directories) | R | https://data.gov.in (NDSAP terms) | derivable | Government open data is licensed for **non-commercial** use | Rules out mixing these sources into a commercial product without a separate licence |

## 4. Market, regulatory and capability sources cited in the final documents

| ID / tag | Source | Class | URL | URL status | What it proves | Why it matters here |
|---|---|---|---|---|---|---|
| RBI-AMD | RBI — nine Amendment Directions for recovery agents (issued 6 Aug 2026; **effective 1 Jan 2027**): 08:00–19:00 contact window, ≥1-day pre-visit notice, ≥6-month bi-directional recording retention, published empanelled-agency list, IIBF DRA certification, device-locking at 30/60 days, ₹250/h compensation | R | rbi.org.in (notifications) | derivable | Hard legal constraints that take effect during the pilot window | Every `PG-0x` rule code traces here; the refusal ledger exists because of this |
| DPDP | DPDP Rules 2025, G.S.R. 843(E), 13 Nov 2025 | R | meity.gov.in | derivable | Purpose limitation and minimisation obligations | Constrains what the event log and evidence store may retain |
| TRAI | TRAI TCCCPR + 12 Feb 2025 amendment (140/1600 series; ₹2 lakh disincentive) | R | trai.gov.in | derivable | Unsolicited-communication regime including bot/robocall classification | Applies to the 3,761 bot attempts and any AI-voice path |
| RBI-OMB | RBI Ombudsman annual report FY24 — 85,281 recovery-agent complaints, +42.7% | R | rbi.org.in | derivable | The conduct problem is large and growing at national level | Cited as context only; **never** used to derive a per-case complaint probability |
| FCC-RND | FCC Reassigned Numbers Database | R | fcc.gov | derivable | The US analogue for the number-recycling problem | International practice reference for our `dead`/recycled logic; not applicable law in India |
| FICO-RPC | FICO — right-party-contact rates "rarely exceed 8–10%" | V | fico.com (collections analytics) | product page (moves) | Public statement of realistic RPC levels | The honest-benchmark caveat: the synthetic dataset's 16.4% is a mechanism demo, not a benchmark |
| TWLO | Twilio Lookup pricing | V | twilio.com (pricing pages) | derivable | Per-lookup pricing exists as a public anchor | Cost-model reference for identity/verification purchases |
| VAI-ECON | AI-voice cost analyses (Asia-Pacific contact-centre economics) | I | industry analyses recorded in Phase-1 research | unconfirmed | Headline ₹2–12/min understates effective cost by 2–4× (integration, telephony, supervision) | The reason we do not build a voice bot and treat telephony as an existing capability |
| ORT | Google OR-Tools | O | https://developers.google.com/optimization | derivable | Open MILP/VRP solvers usable in a hackathon timeframe | The `BUILD IF TIME` allocator and production routing engine |
| CUP | Criteo Uplift Prediction dataset | D | Criteo AI Lab dataset page | derivable | Public uplift benchmark | Licence **CC BY-NC-SA** — non-commercial; hence not used for any claim in this submission |
| ALM | Amazon Last Mile Routing Research Challenge dataset | D | https://www.amazon.science/last-mile-routing-research-challenge | derivable | Public routing dataset with real delivery sequences | Reference for routing evaluation methodology; not mixed with our data |
| GHOST/HW | Home/work location inference literature (incl. GHOST and Bayesian home/work inference studies) | A | arXiv:2605.20429; arXiv:2410.22386; PLOS ONE 2014; Wiley 2021 | partially derivable | Dwell-based inference of home/work from mobile traces is well established | We deliberately **do not** build a home/work classifier (no validation data); kept as a weak outcome-based prior |
| DRIVE | CreditNirvana PS2/PS3 dataset (Google Drive folder) | D | folder id `18iqIR8TjXDqf9-hgEY34uJr_DraIl_3P`; README file id `1rtpHsqVAMRyw4ZISn7k1JoaFks3_jdFb`; `data/` folder id `11J0vOHyjHH0y4Vjw8_5HZxsBWyVgH48t` | **confirmed** | 21 CSVs, 3 towns, all synthetic per the README | The sole source of every `[DATA]` number; `/home/user/data/raw/` holds the local copy |

---

## 5. Coverage audit — does every claim in the final documents have a source?

| Claim class | Coverage | Note |
|---|---|---|
| Architecture patterns attributed to vendors (Experian, FICO, Pega, TransUnion, Credgenics, Spocto, Mobicule) | ✅ S-1…S-30 | Every attribution is drawn from public product documentation or the vendor's own words; vendor URLs move, hence the status column |
| Academic methods (C-MDP, CRM, EVSI, CVaR, conformal, HMM, FS linkage) | ✅ S-31…S-54, S-44, S-53 | Papers with unrecorded URLs are flagged, not fabricated |
| Regulatory constraints | ✅ RBI-AMD, DPDP, TRAI, FCC-RND + Phase-1 regulatory register | These are `[VERIFIED]` and carry operational rule codes |
| Dataset facts (`[DATA]`) | ✅ DRIVE + `dataset_audit.py` | Every number regenerates from `python3 dataset_audit.py q\|p2\|p3\|eco` |
| Patents | ✅ S-35, S-60, S-61 | Patent numbers are stable identifiers |
| Licences | ✅ S-48, S-51, S-65, CUP | The four licence traps restated in the final documents |
| Cost parameters | ⚠ `[ASSUMPTION]` by design | Agent minute, field slot, SMS, conduct cost have **no credible public source**; they are published as ranges with owners. Trace cost is `[DATA]` |
| Market-size / competitor-share claims | ❌ deliberately absent | No unsourced market claims appear anywhere in the Phase-4 files |

**Unresolved URL items (6):** S-30, S-31, S-33/S-34, S-36, S-38, S-45/S-46/S-46bis, S-54/S-55/S-56, VAI-ECON. Before external publication, resolve each to a DOI or publisher URL. Everything these sources support is marked `[INFERENCE]` or attributed, so nothing in the architecture depends on a URL being correct — only on the citation being locatable.

## XV.13 — File 13 — decision log (31 ADRs)

*Source file: `ARCHITECTURE_DECISION_LOG_FINAL.md`*

# ARCHITECTURE DECISION LOG (FINAL)

**Phase 4, File 13 of 13.** Every architecture decision taken in Phase 4, with its reason, its evidence, its label, and — critically — **the condition that would reverse it**. Rejections are recorded as decisions.

**Labels:** `BUILD NOW` (48-hour deliverable) · `BUILD IF TIME` (stretch) · `PRODUCTION` (correct at bank scale, out of scope) · `RESEARCH ONLY` (do not build; precondition stated).
**Evidence classes:** `[DATA]` (audited synthetic dataset, regenerate with `dataset_audit.py`) · `[S-nn]` (bibliography) · `[VERIFIED]` (public/official source) · `[INFERENCE]` · `[ASSUMPTION]` · `[GAP]` (data absent).

---

## Part 1 — System-shaping decisions

### ADR-01 · PS2 is a decision system, not a model · `BUILD NOW`
**Context.** The brief rejects `database → preprocessing → LightGBM → API → dashboard`; the reverse-engineering pass found that every serious system (Experian, FICO, Pega, NYS DTF) separates prediction from policy, constraints and allocation `[S-1][S-3][S-16][S-19][S-32]`.
**Decision.** Build SANKET as state → evidence fusion → prediction → gate → economics → allocation → feedback.
**Why not the classifier.** Measured ceiling: honest pre-dial AUC 0.670, logistic 0.604, leaked 0.933 `[DATA]`. A single model cannot express permission, cost, capacity or sequence.
**Reversal condition.** None foreseen; a better model changes one layer, not the shape.

### ADR-02 · Six layers, each independently refusable · `BUILD NOW`
**Context.** Scope risk is the dominant failure mode in a 48-hour build.
**Decision.** L0 event log · L1 state · L2 identity fusion · L3 prediction · L4 gate · L5 economics · L6 allocation · L7 execution/feedback — with a stated cut-line so each layer can ship alone.
**Evidence.** The three top-scoring options in File 7 score highest on *different criteria* (alignment vs value/depth vs differentiation), which is the signature of layers rather than rivals.
**Reversal condition.** If a layer cannot be shown to change a decision, cut it (test applied in ADR-05, ADR-18).

### ADR-03 · Compliance gate constructs the candidate set; it never filters results · `BUILD NOW`
**Context.** Pega: eligibility → applicability → suitability precedes scoring `[S-19]`; TransUnion sells the same as a pre-engagement gate `[S-12]`; RBI Directions make several actions prohibited from 1 Jan 2027 `[VERIFIED]`.
**Decision.** The gate runs **before** the optimiser; prohibited actions never enter the action set.
**Why it matters.** Post-hoc filtering spends capacity on ineligible work and makes the refusal reason approximate; construction makes prohibited actions structurally impossible and the reason exact.
**Reversal condition.** A rule that can only be evaluated after scoring would have to be split into a pre-scoring proxy plus a post-scoring confirmation — document it if it happens.

### ADR-04 · Refusal ledger as a primary product artefact · `BUILD NOW`
**Context.** No reviewed system publishes *why it declined to act*; the brief demands every action have a failure path and every choice a reason.
**Decision.** Every non-action is an event with rule code, inputs, policy version and a **counterfactual value with a range**.
**Reversal condition.** Never — this is the submission's differentiating claim.

### ADR-05 · No contextual bandit · `RESEARCH ONLY`
**Context.** Propensity ≡ 1.0 on 48,339 of 51,105 attempts; the random arm is 2,766 attempts / 123 accounts / 5.1%, skewed by DPD and outstanding, and *worse* than the incumbent (RPC 0.134 vs 0.166) `[DATA]`; logged feedback is biased and incomplete `[S-39]`; every exploration contacts a real borrower.
**Decision.** Do not build policy learning. Log propensity from day one.
**Reversal condition.** A legal pilot with a genuine control arm and campaign-level reward attribution, plus an ESS budget computed *before* the experiment starts.

### ADR-06 · No constrained MDP · `RESEARCH ONLY` (idea absorbed)
**Context.** NYS DTF's deployment drew on ≈$5 M research + ≈$4 M engagement `[S-33]`; our horizon is 3 months of a single policy with no cost data.
**Decision.** Adopt the C-MDP's *representational* ideas only: legal prerequisites as **states** (L1) and per-action availability flags (L4) `[S-32][S-33]`.
**Reversal condition.** Multi-year longitudinal data with cost and capacity, plus a research budget.

### ADR-07 · No uplift / incremental-effect claims · `RESEARCH ONLY`
**Decision.** No ranking by incremental effect; no numeric uplift claim; the preconditions are documented publicly in the submission.
**Evidence.** The randomisation is not clean (5.4%, skewed, propensity degenerate) and payments carry no campaign id (60% within 7 days of an RPC is correlation) `[DATA]`.
**Reversal condition.** Clean randomisation with logged propensities **including control**, and campaign-level attribution.

### ADR-08 · No LLM or agent inside the decision loop · `RESEARCH ONLY`
**Decision.** Deterministic components only. No generation, no agentic autonomy, no fuzzy logic inside legal gates `[S-31]`.
**Reason.** Auditability, latency, cost, and the brief's explicit prohibition of "LLM/agents everywhere".
**Reversal condition.** A document/letter-understanding task with a deterministic fallback and a measured accuracy requirement.

### ADR-09 · Cost table exposed as parameters with published ranges · `BUILD NOW`
**Context.** No cost, notice or campaign column exists anywhere in the dataset `[GAP]`; the only measured price is the trace (₹104 mean, ₹79,650 total) `[DATA]`.
**Decision.** Ship `costs.yaml` with central values, ranges, owners and sources; every EV displays a range; a single-point rupee figure is structurally unstorable (schema in File 9 §22).
**Reversal condition.** The client supplies their cost/capacity tables.

---

## Part 2 — PS2 component decisions

### ADR-10 · Explicit finite-state machine over 16 dispositions · `BUILD NOW`
**Evidence.** RPC/attempt by consecutive dead calls: 0.180 / 0.177 / 0.160 / **0.067** for 0/1/2/3+; points with ≥1 prior dead call are 42.7% of calls and 37.4% of RPCs `[DATA]`. The naive "never call a dead point" rule is *wrong*.
**Decision.** Refuse dialing only at `dead_streak ≥ 3`; pooled RPC/call improves 0.1762 → **0.1872** with −12.5% calls.
**Reversal condition.** A hidden-state or sequence model demonstrably beating the counter on the same split — then it replaces the *derivation*, not the state object.

### ADR-11 · Identity posterior with an interval, provenance-led · `BUILD NOW`
**Evidence.** P(borrower) by provenance: skip_trace 1.00 · kyc 0.73 · borrower_update 0.67 · bureau 0.30 · reference 0.16 · employer 0.07; CV AUC 0.899 (with behaviour) / 0.813 (provenance alone) / 0.508 (majority) `[DATA]`. Reference+employer points are 14% of calls, answer at 0.44–0.46, but are 81–93% third-party.
**Decision.** Separate, calibrated, interval-valued; disclosure unlock requires a threshold *and* coverage support.
**Reversal condition.** A validated identity model on real data with measured coverage per segment.

### ADR-12 · Shared-number edge detection instead of a GNN · `BUILD NOW`
**Evidence.** 43.2% of attempts sit on shared numbers; third-party rate 0.080 (shared) vs 0.061 (unique) `[DATA]`; 74 duplicate `phone_id`s across accounts make naive joins wrong (52,367 inflated rows).
**Decision.** Deterministic graph edges + Fellegi-Sunter weights `[S-44]`; no embeddings.
**Reversal condition.** A graph model whose increment is measurable against the edge flag on real data.

### ADR-13 · Single multi-class prediction model; no per-action models · `BUILD NOW`
**Evidence.** One target (16 dispositions); no channel arms exist in the log; per-action models would triple the calibration burden for presentation value.
**Reversal condition.** A multi-channel log with per-arm outcomes.

### ADR-14 · Pre-dial features only; leakage enforced by a build test · `BUILD NOW`
**Evidence.** Including `network_response`/durations/`disposition` lifts AUC to **0.933** `[DATA]`.
**Decision.** A test fails the build if a banned column appears; the leakage AUC is printed as a caution in every report.
**Reversal condition.** Never — this is a control, not a design preference.

### ADR-15 · EVSI as a first-class primitive for traces and verifications · `BUILD NOW`
**Evidence.** ₹104/trace; 22.8% hit rate; ₹455 per hit; ₹305 per RPC; **77% of ₹79,650 produced nothing**; trace-success is not learnable (CV AUC 0.574 vs 0.772 majority) `[DATA]`; information purchase is standard practice elsewhere `[S-11][S-42][S-61]`.
**Decision.** Buy iff EVSI > price; refuse with arithmetic recorded.
**Reversal condition.** Client-supplied trace pricing/contracts that change the arithmetic — the *rule* stays.

### ADR-16 · Conduct-tail penalty (λ, CVaR-style) on irreversible actions · `BUILD NOW` (simple form) / `PRODUCTION` (full CVaR)
**Evidence.** Optimising RPC naively raised third-party contact 0.066 → 0.121 on the randomised subset `[DATA]`; CVaR is standard in other domains `[S-43]`; no reviewed collections vendor prices this `[INFERENCE]`.
**Decision.** `score = ENV − λ·Risk`, with λ published, `λ_visit > λ_dial`, and risk-only refusals reported separately from rule-refusals.
**Reversal condition.** A client-specified conduct target converts λ into a hard constraint.

### ADR-17 · Day-level capacity allocator: greedy first, MILP if time · `BUILD IF TIME`
**Evidence.** Experian's constraint-based optimisation `[S-3]`, FICO's solver `[S-16]`, mTSP routing in the 2026 framework `[S-31]`; capacity data absent `[GAP]` → what-if parameters (1,000 / 200 h / ₹50,000 / 50 slots).
**Decision.** Greedy with Lagrangian prices by default; MILP as stretch; `wait` always in the action set.
**Reversal condition.** Real capacity data → MILP becomes the default.

### ADR-18 · Override reasons as the highest-value training signal · `BUILD NOW`
**Evidence.** Pega keeps the CSR in control `[S-21]`; NYS routes non-standard states to specialised units `[S-33]`.
**Decision.** Every override is an event with a mandatory reason; reviewed weekly; systematic overrides trigger a rule/threshold review.
**Reversal condition.** None.

### ADR-19 · Fallback policy: fail closed on compliance, fail open on economics · `BUILD NOW`
**Decision.** Gate unavailable → deny all actions. Model unavailable → segment priors. Feature service down → frozen snapshot (≤24 h, flagged). All degradations are events.
**Reason.** An ungoverned contact is a regulatory event; a sub-optimal contact within the rules is not.
**Reversal condition.** None.

---

## Part 3 — PS3 component decisions

### ADR-20 · Ship calibrated truth before any accuracy improvement · `BUILD NOW`
**Evidence.** Baseline median error 376.4 m, p90 839 m, 9% <100 m; stratum medians rooftop 37.7 / street 134.9 / locality 367.4 / pincode **1,336.5** m, reproduced on a second independent sample (25.6 / 108.6 / 385.9 / 1,375.8) `[DATA]`.
**Decision.** The vendor `precision` label becomes the stratum key; radii and `P(within 200 m)` are published per stratum × town.
**Reversal condition.** A vendor change to the taxonomy (then the mapping is re-derived, not the principle).

### ADR-21 · Field evidence is the accuracy engine · `BUILD NOW`
**Evidence.** Same addresses: vendor 385 m → **29 m** median on met-someone visits; 87% improve; 82% under 100 m `[DATA]`. GPS: median 26 points/visit, median accuracy 9.8 m.
**Decision.** Fusion on stationary clusters with dwell and outcome weighting.
**Reversal condition.** Real-world GPS proving materially worse — then the radius widens and PS2 spends fewer slots; the architecture does not change.

### ADR-22 · No accuracy claim from free public data · `BUILD NOW` (as a refusal)
**Evidence.** Oracle over candidate sets built from free text: 370 m median, 2% <100 m; naive landmark snap 4,093 m (worse in 90%) `[DATA]`.
**Decision.** Retrieval/ranking ships as hygiene + abstention, never as an accuracy story. The number 370 m is stated on the slide.
**Reversal condition.** A licensed address corpus that changes the ceiling.

### ADR-23 · Integrity gate before fusion; negative outcomes never move a point · `BUILD NOW`
**Evidence.** `address_not_traceable` check-ins sit 1,603 m from truth and 195 m from the pin with 2-minute dwell; 645 check-ins (11.6%) are >500 m from their own trail; FA009 has 162/172 duplicate photo hashes (26.6% vs ≤1% elsewhere) `[DATA]`; spoofing is caught by cross-signal inconsistency `[S-58]`.
**Decision.** Gate → then fuse; rejections are events with codes; per-agent pass-rate monitoring.
**Reversal condition.** Device telemetry enabling a scored integrity model (PRODUCTION upgrade).

### ADR-24 · Two-confirmation promotion; contradictions revoke · `BUILD NOW`
**Evidence.** Auto-update after two confirmations in logistics `[S-56]`; single-visit overwrite is how a bad pin becomes permanent.
**Decision.** Promotion requires two independent, integrity-passing confirmations; downstream consumers are notified of revocations.
**Reversal condition.** None.

### ADR-25 · Conformal radii and published coverage · `BUILD NOW`
**Evidence.** Conformal spatial prediction: 93.67% empirical coverage at 90% nominal vs 68.33% bootstrap `[S-53]`; our survey sample is 100 points → stratified, not per-address.
**Decision.** Empirical quantiles + split conformal; the coverage monitor is a shipped artefact; a gap is published, never hidden by widening.
**Reversal condition.** A much larger labelled set (per-address intervals become defensible).

### ADR-26 · No HMM map matching; stop detection instead · `RESEARCH ONLY`
**Evidence.** No road graph in the data (local metric plane, no polygons) `[DATA]`; the standard method requires a segment graph `[S-54]`.
**Decision.** Stationary-cluster stop detection now; HMM as a labelled PRODUCTION/RESEARCH item with the precondition (OSM extract).
**Reversal condition.** Road-network extract for the three towns.

### ADR-27 · Hierarchy adopted as an output contract, not as a model · `RESEARCH ONLY` (model) / `BUILD NOW` (contract)
**Evidence.** GeoIndia: >50% mean / >85% p99 error reduction, 29 state models, 67M addresses `[S-47bis]`; not reproducible here.
**Decision.** Report stratum + radius (our hierarchy); do not train a cell-prediction model on 3,117 addresses.
**Reversal condition.** ≥10k labelled addresses and a hierarchy gazetteer.

### ADR-28 · Canonical coordinate is ours; vendor results are ≤30-day priors · `PRODUCTION` (with `BUILD NOW` logging)
**Evidence.** Google Maps Platform terms: lat/lng cache ≤30 days, no permanent storage of other content, no training on output `[S-48]`; Nominatim 1 req/s `[S-51]`; NDSAP non-commercial `[S-65]`.
**Decision.** Provider abstraction + audit log; canonical store fed only by promotion.
**Reversal condition.** A provider contract that permits permanent storage (then the constraint relaxes, the architecture does not).

---

## Part 4 — Integration decisions

### ADR-29 · Exactly two cross-system contracts · `BUILD NOW`
**Decision.** PS3 → PS2: `P(truth within r)`, stratum radius, integrity status, promotion events. PS2 → PS3: `visit.completed` with outcome/dwell/trail, `visit.requested` with the value of confirmation. Nothing else crosses.
**Reason.** Narrow contracts keep the two systems independently testable and prevent the integrated file from being "two boxes joined".
**Reversal condition.** A third genuine need — which must be named and justified before it is added.

### ADR-30 · Shared event vocabulary across both systems · `BUILD NOW`
**Decision.** `call.completed`, `trace.returned`, `payment.received`, `visit.completed`, `visit.rejected_integrity`, `coordinate.promoted`, `coordinate.revoked`, `refusal.recorded`, `override.recorded`, `policy.versioned`.
**Reason.** One log, two views — the mechanism that makes the integrated product coherent and replayable `[S-59]`.
**Reversal condition.** None.

### ADR-31 · The joint decision is *which uncertainty to buy down* · `BUILD NOW`
**Context.** A trace buys identity information (₹104); a visit buys identity *and* location information (≈₹180) and is irreversible.
**Decision.** Both are priced by the same EVSI logic inside PS2's allocator, with PS3 supplying the location term. A visit is chosen over a trace when the joint information gain per rupee is higher **and** the location confidence is good enough to make the visit likely to succeed.
**Reason.** This is the one decision that neither system can make alone — the integration thesis (File 11).
**Reversal condition.** Field costs or trace hit rates changing materially.

---

## Part 5 — Rejected alternatives, consolidated

| Rejected | Label | Reason (evidence) |
|---|---|---|
| Contextual bandit / online policy learning | RESEARCH ONLY | Degenerate propensities; confounded 5.4% arm; no reward attribution `[DATA][S-39]` |
| Constrained MDP over the full journey | RESEARCH ONLY | 3-month horizon; reference deployment cost `[S-33]` |
| Uplift / incremental-value ranking | RESEARCH ONLY | No clean control arm `[DATA]` |
| GNN identity model | Rejected (superseded) | Edge flag captures the decision value at a fraction of the cost `[DATA]` |
| Sequence/deep model for dispositions | Rejected | Label noise, short horizon, modest honest AUC `[DATA]` |
| Per-action outcome models | Rejected | No arms to learn from `[DATA]` |
| Fuzzy inference in legal gates | Rejected outright | The brief + auditability `[S-31]` |
| Landmark-based auto-correction | Rejected on measurement | 4,093 m median, worse in 90% `[DATA]` |
| Learned candidate ranker as a claim | Rejected | Oracle ceiling 370 m; 100 labels `[DATA]` |
| HMM map matching | RESEARCH ONLY | No road graph `[DATA][S-54]` |
| Hierarchical cell model | RESEARCH ONLY | Proprietary corpus; 3,117 addresses `[S-47bis]` |
| Continuous-grid probabilistic map product | Rejected (substance kept) | Fictional precision; unreadable to a field officer |
| Multi-vendor consensus as core | Rejected (optional) | Cost + licence burden; accuracy gain unsupported `[INFERENCE]` |
| AI voice bot | Rejected | Out of scope; effective cost 2–4× headline `[VAI-ECON]` |
| Complaint-risk predictor | RESEARCH ONLY | No case-level complaint labels |
| Fairness-constrained allocation | RESEARCH ONLY | No agreed fairness metric from the client |
| Measuring spoof-detection rate | Rejected as a claim | No device telemetry to measure recall `[GAP]` |
| Market-share / market-size claims | Rejected outright | No credible public source; brief forbids invented statistics |

---

## Part 6 — Decision-trail summary

| Class | Count | Decisions |
|---|---|---|
| `BUILD NOW` | 24 | ADR-01,02,03,04,09,10,11,12,13,14,15,16(simple),18,19,20,21,22,23,24,25,29,30,31 + the PS3 provider audit logging |
| `BUILD IF TIME` | 2 | ADR-17 (MILP), learned-ranker experiment |
| `PRODUCTION` | 4 | ADR-16 (full CVaR), ADR-26 (HMM once a graph exists), ADR-28, scored integrity model |
| `RESEARCH ONLY` | 8 | ADR-05,06,07,08,26,27(model), plus complaint-risk and fairness items |
| Rejected alternatives | 18 | Part 5 |

**The three decisions that carry the submission:** the refusal ledger (ADR-04), EVSI as a purchase rule (ADR-15), and field evidence with an integrity gate as PS3's accuracy engine (ADR-21 + ADR-23). Every other entry either supports one of these, or is a documented refusal.

**How to challenge this log.** Each ADR states a reversal condition. A reviewer who can produce that condition — a clean pilot, a road graph, a cost table, a labelled corpus — has the exact list of what to reopen.
