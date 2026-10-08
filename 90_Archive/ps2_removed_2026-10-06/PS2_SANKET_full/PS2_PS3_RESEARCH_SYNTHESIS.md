# PS2 + PS3 — RESEARCH SYNTHESIS

**Red-team of the current designs, the integration question researched independently, component choices, and the final research conclusion.**
Reads with: `PS2_DEEP_INTERNET_RESEARCH.md`, `PS3_DEEP_INTERNET_RESEARCH.md`, `PS2_ARCHITECTURE_REQUIREMENTS.md`, `PS3_ARCHITECTURE_REQUIREMENTS.md`, `PS2_PS3_SOURCE_BIBLIOGRAPHY.md`.

Tags: **[VERIFIED]** · **[INFERENCE]** · **[ASSUMPTION]** · **[UNKNOWN]**

---

# PART C — CHALLENGING THE CURRENT DESIGNS

## 19. Red-team: `PS2_SANKET_SOLUTION_ARCHITECTURE.md`

The hypothesis under attack: *rules floor + one calibrated contact-point model + a right-party model + a survival/timing sub-component + an EV gate + a candidate-set compliance gate + a decision record.*

| # | Attack | Verdict | Evidence |
|---|---|---|---|
| 1 | **Are we solving the actual problem?** | **Partly.** We solve "which action is permitted and worth spending", which matches the PS's economics clause. But the SANKET design leans on point-level labels CN may not hold — that is a data assumption, not a design fact | §1.2, §2.4 of PS2 research |
| 2 | **Are we using too many models?** | **Yes — cut to two, then to one if possible.** S1 (contact), S2 (right party) and S3 (timing) is three artefacts plus a gate. The deployed literature uses **one learned value function + a rules engine** | van de Geer (LightGBM value function); Abe et al. (rules engine + optimisation) |
| 3 | **Is contact-health prediction useful?** | **Yes, but keep it coarse.** Point-level with rich features will overfit sparse per-point histories; a *channel × window × point-type × age* feature set is where the signal actually is | [INFERENCE] from feature availability, not from a published ablation |
| 4 | **Is P(RPC) necessary?** | **Yes.** It is both the PS's metric and the input to the compliance gate (an identity-verified contact is what authorises disclosure) | PS2 §1.2; TransUnion Contact Compliance Risk as the commercial analogue |
| 5 | **Is P(productive) necessary?** | **No — cut.** The offer/negotiation layer is CN's (Maestro). Modelling it duplicates the platform and would not change our decision | PS2 §7.2 |
| 6 | **Is survival modelling justified?** | **Not in the MVP.** Published value came from full MDP scheduling with volume and logged propensities; our design has neither. Replace with cohort-level hour/day priors and earn the survival model back with a measured lift test | PS2 §3.2; §4.2 |
| 7 | **Is expected net recovery measurable?** | **Only as a range.** Incremental recovery per contact needs an incrementality assumption; the honest artefact is a sensitivity table with a named assumption, not a number | Phase-2 model; PS2 §4.3 |
| 8 | **Can we obtain the training data?** | **Only from a CN sandbox: point-level dispositions + the incumbent policy's attempt log.** If absent: rules floor + identity gate + EV with assumed parameters, and **no accuracy claims** | PS2 §2.4, §4.2 |
| 9 | **Are we duplicating CN capabilities?** | **Risky in two places:** (a) any "who to call" propensity model competes with Maestro; (b) dashboards compete with 80+ existing. Differentiate on the **eligibility decision + record**, not on ranking dashboards | creditnirvana.ai (20 modules, 80+ dashboards) |
| 10 | **Is a contextual bandit practical?** | **No.** No propensities, no safe exploration, conduct exposure. The literature itself wraps optimisation in **constraints**; live exploration in collections is a compliance problem before it is a statistical one | Abe et al.; PS2 §4.2 |
| 11 | **Is VoI genuinely useful?** | **Yes for purchases** (trace, verification, a second check): the tool exists (EVSI approximations) and the decision is naturally an information purchase. Implement as a **threshold with sensitivity**, not full nested Monte Carlo | *Value in Health* 2020 EVSI review |
| 12 | **Are hard compliance gates realistic?** | **Yes, and they are the point.** Encode hours, suppression, third-party prohibition, notice-before-visit as candidate-set constraints, not as post-hoc filters | PS2 §6.2; RBI Directions |
| 13 | **Can this be explained to a bank/NBFC?** | **Yes if** reason codes are generated from the gate and feature thresholds (not SHAP-first). The decision record must show *which rule permitted the action* | PS2 §6.3 |
| 14 | **Can it be built in the hackathon?** | **Yes, if cut to:** rules floor + one outcome model + calibration + EV gate with `wait` + decision record + one screen. Survivor: the refusal path | [INFERENCE] |

### 19.1 Simpler alternatives proposed

| Simpler design | What it drops | What it keeps | When it is enough |
|---|---|---|---|
| **S-A. Rules + EV only (no ML)** | All models | Eligibility gate, cost table, EV ranking with priors from cohort rates | When there are no point-level labels, or for the first pilot week |
| **S-B. One multi-class outcome model** | Two separate binaries | A single model predicting {no answer, wrong party, RPC, refusal/other} → derived P(RPC) and P(right party); one calibration artefact, one monitoring surface | **Recommended default** — one pipeline, one model card, one drift monitor |
| **S-C. Two binary heads** (current SANKET) | — | Slightly better calibration per head; supports different label sources | If the outcome taxonomy is genuinely different per head |

**Recommendation:** ship **S-A as the fallback path** and **S-B as the modelled path**; treat S-C as a refinement, not the plan.

## 20. Red-team: `PS3_SUTRA_SOLUTION_ARCHITECTURE.md`

The hypothesis under attack: *consume a commercial geocoder at runtime + fuse recovery-visit evidence with an integrity weight + purpose classification + empirical radius + the notice gate.*

| # | Attack | Verdict | Evidence |
|---|---|---|---|
| 1 | **Are we rebuilding a geocoder?** | **No — and we must keep it that way.** Any drift toward "better than Google" fails: the Indian systems that beat Google use proprietary corpora and delivery graphs | GeoIndia (EMNLP 2024); GeoIndia-V2; COLING 2025 |
| 2 | **Can commercial geocoders already solve most of this?** | **Most of the address→coordinate step, yes.** The unsolved part is what the output may *authorise* and whether field evidence is trustworthy | Delhivery Maps; Google ToS |
| 3 | **What exactly is the differentiated layer?** | **(a)** integrity-weighted evidence from *recovery* visits; **(b)** purpose classification as a third-party-disclosure control; **(c)** a confidence gate on the irreversible notice/visit; **(d)** stratified empirical radius reported honestly | PS3 §12–15 |
| 4 | **Is address confidence useful enough?** | **Yes where field/legal actions exist; thin at small tickets.** Value is ticket-conditional — must be scoped to field-bearing portfolios | Phase-2 financial model |
| 5 | **Is the uncertainty radius actionable?** | **Only if a threshold consumes it.** Android's own semantics (68th-percentile radius) prove a radius without a decision is meaningless | developer.android.com |
| 6 | **Can field GPS reliably improve the belief?** | **Yes with dwell + time window + repeats + accuracy; weakly with single pings.** Documented stay-point methodologies support this | PLOS ONE 2014; Wiley 2021; GHOST 2026 |
| 7 | **Is purpose classification worth building?** | **Yes — for compliance.** Serving a notice at a workplace/shop is a third-party-disclosure risk. Start with a small rule + POI classifier with an abstain class | RBI prohibited practices; PS3 §15 |
| 8 | **How do we detect bad/spoofed evidence?** | Cheap checks first: mock-location flag, accuracy radius, speed plausibility between check-ins, duplicate coordinates, dwell realism. **Never claim a detection rate** | Android `isMock`; [UNKNOWN] on real-world evasion |
| 9 | **Best fallback when geocoding fails?** | PIN/locality polygon centroid **with a wide radius and tier = unknown**, plus a verification task. The failure mode must be "verify", never "guess" | PS3 §14 |
| 10 | **Is H3 useful or decorative?** | **Useful as a spatial key** for strata, landmark locality and pack partitioning; **decorative** as a product claim. It is not the reason a notice is right or wrong | Uber H3 docs |
| 11 | **Can this work offline?** | **Yes** — packs per district, capture at visit time, sync later; field apps already do this | credgenics CG Collect (offline) |
| 12 | **What data can actually train it?** | Only **own-outcome** data (visit outcomes with integrity), never vendor coordinates as labels. Licence: Google forbids indefinite storage of its coordinates except for end-user display | Google Maps Platform Service Specific Terms §6 |

### 20.1 Simpler alternatives proposed

| Simpler design | What it drops | What it keeps | When it is enough |
|---|---|---|---|
| **G-A. Geocode + PIN polygon + verify-first** | All learning | Candidate generation, PIN checks, "unknown" tier, the notice gate | When CN has no visit evidence |
| **G-B. G-A + integrity-weighted visit updates (no purpose classifier)** | Purpose model | Evidence ledger, radius by stratum | When visits exist but are few |
| **G-C. Full SUTRA** | — | + purpose classification, landmark table governance, offline packs | Field-bearing portfolios with real visit volume |

**Recommendation:** ship **G-A as the honest baseline**, **G-B as the MVP target**, and gate **G-C** on measured visit volume (the pilot's first counter).

---

# PART D — THE INTEGRATION QUESTION (§20)

## 21. Three options compared

| Criterion | **A. PS2 independent** | **B. PS3 independent** | **C. Integrated (PS2 + PS3)** |
|---|---|---|---|
| Business value | Widest: every portfolio with human calls | Narrower: only portfolios with field/legal actions | Highest where field actions exist; **zero marginal value** in pure-automated portfolios |
| Technical feasibility | High (tabular ML + rules) | Medium (geo + evidence integrity + licence) | Medium (both, plus a shared object model) |
| Differentiation | Medium — crowded contact-intelligence market | **High** — permission-to-serve on a new legal requirement | **High**, but the novelty lives in the *interface*, not in either half |
| Demo impact | Medium (numbers, queues) | **High** (map, radius, blocked notice) | **Highest**: a refusal caused by *both* an identity and an address judgement |
| Data requirements | Point-level dispositions + policy log | Visit-level evidence; geocoder licence | Both — and enough field volume for the address half to matter |
| Explainability | High (reason codes) | High (rule + evidence + radius) | High, if the record shows which constraint fired |
| Implementation time | 2–4 weeks | 4–6 weeks | 6–10 weeks (or 48 h for a demo cut) |
| CN fit | Fits Maestro's dialer layer as a policy input | Fits Maestro's field + legal/notice layer | Fits only if it *is* a thin layer in front of both |
| Judge appeal | Good | Better | Best — but only if the causal chain is real |
| Production potential | High (broad) | High (compliance-driven) | High, but staged: identity gate first, address gate second |

## 22. Candidate interfaces (researched, not assumed)

| Interface | Description | Assessment |
|---|---|---|
| **I-1. Sequential chain (our hypothesis):** identity confidence → address confidence → eligibility → economic decision | PS2 produces identity; PS3 produces address; both feed one eligibility filter, then an EV ranker | **Best fit to the evidence.** The RBI pre-visit notice is the only action that needs *both* judgements and is irreversible, so the chain has a real object to exist for |
| I-2. Address as a feature in PS2 | SUTRA's `radius_90`/purpose become columns in the contact model | Loses the compliance value: an address feature cannot *prohibit* a notice; only a gate can |
| I-3. Shared ledger only | Two independent engines, one decision-record service | Cheap, honest, but the demo becomes two demos |
| I-4. PS3-centric: address confidence drives an eligibility gate; identity is a simple rule | Identity handled by a deterministic "verified/not verified" flag | Defensible where identity verification events are sparse; weakens the strongest compliance control |
| I-5. PS2-centric with address handled by CN's existing geocoder | We own identity; address stays a vendor field | Least novel; abandons the only place where the new RBI notice rule bites |

**[INFERENCE] Verdict:** integrate **only through I-1, and only for irreversible actions** (notice, doorstep visit, legal escalation). Everything else stays independent. Both halves must remain independently deployable, because if the field channel is thin the integrated story collapses and PS2 alone must still be sellable.

## 23. Is the combination genuine or decorative?

**Genuine, conditionally.** The condition is the one our evidence supports: *a legally-required doorstep action needs (i) a defensible judgement about whose door it is and (ii) a defensible judgement about whose identity is being served — and the field visit is the only observation that improves (i), while the call is the only observation that improves (ii).* That is a closed loop with real substance: one observation type improves one belief, and both beliefs gate one irreversible action.

**Decorative if:** we cannot show a field channel with enough volume; or if we present the two halves as "one platform" without a decision that requires both.

---

# PART E — COMPONENT CHOICES (§23)

Every row: at least three alternatives, the choice, and the evidence.

## PS2

| Problem | Approach 1 | Approach 2 | Approach 3 | **Best choice** | Why (evidence) |
|---|---|---|---|---|---|
| Contact-point state | Rules (age/source/last outcome) | **Gradient-boosted multi-class outcome model** | Sequence model (LSTM/transformer over dial history) | **2**, with 1 as the floor | Tabular data at this scale is exactly where GBDT is used in the deployed collections literature; sequence models need volume and give up explainability |
| Right-party inference | Agent-entered disposition alone | **Model over identity-verified events + call outcomes + cross-account conflicts** | Graph/entity resolution across accounts | **2** now; **3** later with Splink | Splink provides probabilistic linkage without training labels (Fellegi-Sunter); graph contact targets are restricted by regulation |
| Action selection | Propensity classification (P(pay)) | **Expected-net-recovery ranking with a `wait` action** | Contextual bandit | **2** | The PS's own wording; the deployed systems optimise net benefit under constraints; bandits need exploration that collections cannot safely provide |
| Timing | Ignore timing | **Cohort-level hour/day priors** | Survival model / hazard | **2** in MVP, **3** only after a measured lift test | Timing effects are real but modest relative to action choice; survival needs censoring discipline and volume |
| Selection bias | Ignore | **Propensity weighting (clipped) + full-population features** | Full randomisation | **2** | Logged bandit feedback is biased *and* incomplete; IPW is the standard fix; randomisation is the lender's decision, not ours |
| Information purchases (trace/verify) | Trigger on attempt count | **EVSI-style threshold with sensitivity** | Full nested-Monte-Carlo EVSI | **2** | EVSI is the right framing and is computable with standard approximations; full machinery is unaffordable in a hackathon |
| Compliance | Post-hoc filtering of recommendations | **Candidate-set construction (hard gate) + recorded permission** | Audit log only | **2**, with 3 as evidence | RBI judges whether the system permitted the conduct; a log alone does not prevent anything |
| Exploration | ε-greedy live | **Zero-cost exploration: only within already-planned attempts; otherwise none** | Contextual bandit | **2** | Conduct exposure dominates any statistical gain |
| Evaluation | AUC / accuracy | **PR-AUC, calibration (ECE) per segment, precision at the operating budget, and shadow-mode counterfactuals** | Offline RL benchmarks | **2** | Business decision is threshold-based; calibration is what the EV comparison needs |

## PS3

| Problem | Approach 1 | Approach 2 | Approach 3 | **Best choice** | Why (evidence) |
|---|---|---|---|---|---|
| Address parsing | Regex + PIN anchor | **IndicBERT/CRF NER (open weights) + gazetteers** | Fine-tuned LLM | **2** (with 1 as fallback) | Open Indian address NER weights exist and run in tens of ms; LLM cost/latency and no accuracy edge evidenced for extraction |
| Geocoding | Build own model | **Commercial/India-native API at request time** | Self-hosted Nominatim + OSM | **2** as primary, **3** as fallback | Best Indian geocoders are built on proprietary corpora; Google's terms forbid the storage we would need; self-hosted OSM grants storage rights |
| Candidate set | Single point | **Top-k candidates + weights** | Full belief distribution only | **2** externally, **3** internally | Peer-reviewed Indian benchmarks show large single-point error; vendors already return uncertainty |
| Uncertainty | Fixed global radius | **Empirical radius by stratum** | Conformal with geographic weighting | **2** now; **3** validated later | GeoCP reports 93.67% coverage vs ≤81% bootstrap → conformal is the right *validation* frame; small n per stratum makes a headline coverage claim indefensible |
| Field evidence | Trust all check-ins | **Integrity-weighted observations (widening, not shifting)** | Reject check-ins outright | **2** | Dwell/time-window/speed plausibility are documented signals; rejection pushes gaming elsewhere, widening degrades gracefully |
| Purpose | Assume home | **Rule + POI classifier with abstain** | Learned model on visit histories | **2** in MVP, **3** with volume | Home/work inference from dwell + time window is established (65–70% within 100 m in cited studies); no Indian benchmark exists |
| Routing | Build VRP | **Emit location object; consume existing field systems** | OR-Tools route solver as a module | **2** | Routing is commoditised (OR-Tools; vendor beat plans); it is not where PS3's evidence is |
| Offline | Online-only | **District packs + offline capture + sync** | Full offline geocoder on device | **2** | Field apps already do this; on-device geocoding duplicates a licensed layer |
| Spatial key | PIN only | **PIN + H3 cell key** | Custom grid | **2** | H3's hierarchical hex indexing is designed for exactly this kind of bucketing |

---

# PART 25 — FINAL RESEARCH CONCLUSION

## PS2 — recommended direction

| Element | Answer | Basis |
|---|---|---|
| **Actual problem formulation** | A **constrained sequential decision problem**: choose the next action for an account from an eligible set, where the state (identity validity, contact health) is partially observed and the objective is expected net recovery on expensive actions | PS2 §1.2, §3 |
| **Recommended modelling approach** | **One multi-class outcome model** (no answer / wrong party / right party / refusal) on point-level features, isotonic-calibrated per segment, plus a **deterministic rules floor**; entity resolution via Fellegi-Sunter (Splink) for internal linking only | §3.3, §23 |
| **Recommended optimisation objective** | **Maximise expected net recovery per unit of the scarce resource, subject to hard eligibility constraints**, with an explicit `wait` action and EVSI-style pricing of traces/verifications | §5.3 |
| **Required data** | Point-level dispositions; the incumbent policy's attempt log (propensities); identity-verified events; payment/roll-back outcomes; complaint events | §2.4, §4.2 |
| **Biggest technical risk** | Policy-induced selection bias making any learned lift unverifiable; mitigated by propensity logging + shadow mode, not by model choice | §4 |
| **Biggest business risk** | Duplicating CN's own offer-layer capability and competing with Maestro — mitigated by owning only the eligibility/permission surface | §7.2 |
| **Biggest compliance risk** | A model that authorises a disclosure the law does not permit; mitigated by candidate-set construction and a recorded permission | §6.2 |
| **Strongest differentiator** | **Eligibility as a product**: an action absent from the candidate set because identity is unverified, provable from the record | §2.2, §6.2 |
| **Simplest viable architecture** | Rules floor → one model → EV gate with `wait` → decision record; no survival, no bandit, no graph | §19.1 |
| **Advanced production architecture** | + propensity-weighted training, segmented recalibration, hazard-based retest timing gated on a measured lift, offline policy evaluation of alternative strategies | §23 |

## PS3 — recommended direction

| Element | Answer | Basis |
|---|---|---|
| **Actual problem formulation** | **Representation + evidence + permission**: output a candidate distribution with calibrated uncertainty, fuse field evidence under integrity weighting, and gate the irreversible action | PS3 §9.1, §12 |
| **Recommended modelling approach** | Buy geocoding at request time; parse with open Indic NER + PIN anchor; maintain a belief over candidates updated by integrity-weighted observations; classify purpose with a small rule+POI model and an abstain class | §23 |
| **Recommended optimisation objective** | Not an objective but a **decision rule**: permit the notice/visit only when purpose ∈ {home-like, unknown-but-strong} and radius/confidence clear the threshold; otherwise **verify first** | §14, §15 |
| **Required data** | Visit-level GPS with accuracy, dwell, attestation; visit outcomes (met / not met / wrong door); notice outcomes; a geocoder licence permitting the intended use | §13, §17 |
| **Biggest technical risk** | Too few visits per locality to calibrate radii or classify purpose — mitigated by honest abstention and stratum fallbacks | §14 |
| **Biggest business risk** | Being a thin wrapper on a vendor API — mitigated only by evidence, integrity, purpose and the gate | §11.1 |
| **Biggest compliance risk** | Serving a legally-required notice at a location that is not the borrower's home (third-party disclosure). This is *the* reason PS3 exists | §15 |
| **Strongest differentiator** | **Address confidence as a permission input on an irreversible, legally-required action**, learned from recovery-visit evidence that geocoders do not have | §12, §15 |
| **Simplest viable architecture** | Runtime geocode + PIN polygon + candidate set + empirical radius + notice gate + "unknown → verify" | §20.1 (G-A) |
| **Advanced production architecture** | + integrity model v2 (device, sequence plausibility, door-plate evidence), purpose classifier, landmark alias table, district offline packs | §23 |

## PS2 + PS3 — recommended direction

| Question | Answer |
|---|---|
| **Should they be integrated?** | **Yes, but narrowly** — only for irreversible actions (notice, doorstep visit, legal escalation) and only through interface **I-1** |
| **Exact integration point** | The **eligibility filter**: an action enters the candidate set only if (identity confidence ≥ τ_identity for disclosure-capable actions) **and** (address confidence ≥ τ_address and purpose ≠ third-party-likely for notice/visit actions). Both thresholds are configuration, versioned, and recorded per decision |
| **Why** | Because the RBI framework from 1 Jan 2027 makes the pre-visit notice a legal precondition, and a doorstep action is the only action that requires *both* a location and an identity judgement; the field visit is also the only upstream observation that improves the address belief |
| **Why not (the counter-argument we accept)** | In a portfolio with few field actions, or where CN already gates notices elsewhere, integration adds cost without value. The identity half must stand alone |
| **What becomes the core product** | **The permission layer and its record** — not a predictor, not a geocoder, not a dashboard |
| **What remains separate** | The offer/negotiation layer (CN's), routing/beat planning (commodity), geocoding (vendor), identity/KYC rails (Perfios), generic propensity-ranking dashboards (existing 80+) |
| **What would falsify this** | Three facts, all checkable in one conversation with CN: no visit-level GPS history; no point-level dispositions; a portfolio whose ticket size makes field actions uneconomic. If any is true, the integration is demoted and the identity gate alone is the product |
