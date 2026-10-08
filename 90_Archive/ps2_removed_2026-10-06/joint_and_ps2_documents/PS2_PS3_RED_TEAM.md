# RED TEAM — attacking our own solution before a judge does

*Nothing in this file defends the previous design. Where a previous choice survives, it is because the attack failed, not because it was ours.*

---

# PART A — THE 36 QUESTIONS

## A1. Product (6)

| # | Question | Honest answer | Verdict |
|---|---|---|---|
| P1 | Would a collections manager actually use this? | Only if it lands in their **existing allocation workflow** and includes a *refusal* list they trust. A separate dashboard would not be used — CN already ships 80+ of them `[PUB]`. | **Design change:** output = allocation deltas + exception queue, not a dashboard |
| P2 | Does it reduce an important operational bottleneck? | The bottleneck is not "which number to dial" (cheap, automated). It is **deciding which expensive action to spend** and **not triggering a conduct event**. | **Reframe:** the product governs expensive + irreversible actions |
| P3 | Does it fit an existing collector workflow? | Tele-calling: partly (allocation). Field: poorly, unless beat plans consume our confidence output. Compliance: well — it becomes their evidence. | **Design change:** three consumers, three contracts |
| P4 | Does it create another dashboard nobody wants? | Yes, as previously specified. Our own first deliverable had 3 UIs for a 48-hour build. | **Cut:** one screen per persona, or none |
| P5 | What decision changes because of our product? | (a) a visit slot is withheld, (b) a notice is withheld, (c) a debt-disclosing script is replaced by an identity check, (d) a trace is not ordered, (e) an account is left alone this week. All five are *negative* decisions. | **This is the product.** Name it that way |
| P6 | Who pays, and why would a bank/NBFC/ARC buy it? | The lender pays as part of the CN subscription; it buys **reduced regulatory exposure and reduced waste in field/trace budgets**, not "AI". | Moved to CFO narrative |

## A2. Economics (9)

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

## A3. ML (8)

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

## A4. Compliance / responsible collections (8)

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

## A5. Competition (5)

| # | Question | Answer |
|---|---|---|
| K1 | Has somebody already built this? | The **components** yes: contact intelligence (TransUnion PBI +33% RPC), contactability (Spocto), tracing (SkipTracer.in), geo-tagging (Mobicule), outcome-learning addresses (Shiprocket 72.69% <100 m) |
| K2 | Is the novelty real? | Only in the **integration point**: identity-gated eligibility + confidence-gated notices + integrity-weighted field evidence. See `NOVELTY_MATRIX.md` |
| K3 | Is this merely "XGBoost + dashboard"? | As previously specified, closer to "12 models + 3 dashboards". Now: rules floor + 2 models + a gate + an evidence ledger |
| K4 | Is PS2 substantially different from existing contact-intelligence products? | **No, not at the model level.** Different at the *permission* level (what the output is allowed to authorise) |
| K5 | Is PS3 merely a wrapper around Google/OSM? | **Partly yes.** It becomes non-wrapper only via recovery-visit evidence, integrity weight, purpose classification and the notice gate |

---

# PART B — FIVE ALTERNATIVE PS2 FORMULATIONS, SCORED

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

# PART C — SIX PS3 ARCHITECTURES, SCORED

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

# PART D — SHOULD PS2 AND PS3 BE COMBINED? (6 options scored)

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
