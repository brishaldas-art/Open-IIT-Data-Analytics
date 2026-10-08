# NOVELTY MATRIX

**Rule applied:** novelty is not claimed because our architecture has many components. It is claimed only where **a specific existing system does the adjacent thing and still cannot produce our outcome**. Five candidate novelty directions were enumerated, scored, and ranked. Two were rejected outright because the research showed they already exist commercially.

---

## 1. The five directions, with the evidence that ranks them

| # | Novelty direction | Existing industry solution that does the adjacent thing | What it does | Our approach | **Why existing systems don't already do it** | Technical moat | Data moat | Workflow moat | Economic moat | Compliance moat | Demonstrability | Difficulty to copy |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **N1** | **Notice/visit gated on modelled *address confidence*** | Delhivery GeoNaksha returns an **error radius**; Mobicule/Credgenics geo-tag visits | Returns a coordinate + radius; records where the agent went | The radius is a **gate**: below a threshold, the RBI-mandated advance notice and the visit are **not generated at all** | Geocoding vendors have no stake in *whether an action is lawful*; collections platforms treat geo-tagging as proof-of-visit, i.e. the decision is already made before geo data is consulted | Low (arithmetic) | **High** — needs field-visit evidence per address | **High** — must sit inside the allocation/notice workflow | **High** — converts geo uncertainty into avoided notices/visits | **Very high** — directly implements the 2026 advance-notice rule | **Very high** — the blocked notice is a 20-second visual | Hard for a geocoder (no workflow); easy for a collections platform *once it thinks of it* |
| **N2** | **Identity gate: disclosure-capable actions removed from the candidate set** | TransUnion **Contact Compliance Risk**; Skit.ai RPC verification in-call; script-level guards | Verifies identity **during or before** the call; flags compliance risk | Modelled P(right party) **structurally excludes** the action; the audit shows the constraint that removed it | Vendors verify *after* the call connects; law firms and DBs see compliance as a property of the *call*, not of the *decision* | Low | Medium | High | High (avoided conduct cost) | **Very high** | **High** — two accounts, same connect probability, opposite allowed actions | Medium |
| **N3** | **Integrity-weighted field evidence (anti-poisoning by widening, not rejecting)** | Mobicule: geo-fencing, liveness, "prevent location spoofing" | Detects/penalises fraudulent check-ins | Fraud **degrades gracefully**: the observation is down-weighted and the confidence radius **widens** instead of the belief shifting | Fraud systems are punitive and binary; geographic systems assume observations are true or junk — nobody formalises *credibility as a weight on belief* | Medium | High | Medium | Medium | Low–Medium | **Very high** — inject a fake check-in live and show the estimate not moving | Medium |
| **N4** | **Priced skip-trace (EVSI) instead of attempt-count triggering** | SkipTracer.in; TruLookup; every dialer vendor's "smart trace" | Finds updated contacts faster; traces at a configured cadence | Trace fires only when **expected information value > fee**, computed per account | Trace vendors monetise volume; platforms configure a cadence. Neither has an incentive to *suppress* trace volume | Low | Medium (needs our own trace-yield history) | Medium | **High** | None | High — move the price slider and watch decisions flip | **Low — easiest to copy** |
| **N5** | **Contact-point-level, censoring-aware health with a rules floor** | Account-level propensity models everywhere; contactability scores (Spocto, TransUnion PBI) | Scores accounts or phone numbers | Scores **each point on a slate**, never-tested points **censored not failed**, with a deterministic floor that can veto | Contactability scoring is account/identity-centric; slates are an operations concept, not a data-product concept | Medium | Medium | High | Medium | Low | Medium | Medium |

### Rejected novelty claims (research killed them)
| Claim we nearly made | Why it is dead |
|---|---|
| "An address engine that learns from field outcomes" | **Shiprocket Address Intelligence**: learns from every successful delivery and correction; claims 72.69% <100 m, 90.57% <500 m `[PUB]` |
| "Calibrated uncertainty from a geocoder" | **Delhivery GeoNaksha returns an error radius**; Google returns component-level accuracy `[PUB]` |
| "Distinguishing residential from commercial addresses" | **Google Address Validation for India already does this** `[PUB]` |
| "Predicting which number is right, and when to call" | TransUnion **Phone Behavior Intelligence claims +33% RPC**; Spocto markets contactability; every dialer vendor claims timing uplift `[PUB]` |
| "Using field GPS to improve routing" | Mobicule and Credgenics sell AI beat plans and geo-tagged visits today `[PUB]` |

---

## 2. Ranking (weighted: compliance 25%, data moat 20%, demonstrability 20%, workflow 15%, technical 10%, economic 10%)

| Rank | Direction | Score | Verdict |
|---|---|---|---|
| **1** | **N1 — confidence-gated notice/visit** | **4.6 / 5** | The hero. Maps to a brand-new legal obligation, is visually undeniable, and requires the field-evidence stream that a geocoder cannot have |
| **2** | **N2 — identity-gated eligibility** | **4.4 / 5** | The co-star. Makes the compliance claim structural rather than aspirational, and it is the only part that applies to **every** portfolio, including pure automated digital |
| **3** | **N3 — integrity-weighted evidence** | **3.8 / 5** | The credibility move. Turns "we built a learning geocoder" into "we built one that cannot be fooled" — and it is the piece a judge remembers |
| **4** | **N5 — contact-point slates with censoring** | **3.2 / 5** | Real but explainable in one sentence; a supporting argument, not a headline |
| **5** | **N4 — priced trace** | **3.0 / 5** | Genuinely required by the problem statement and impressive in a slider, but trivially copyable |

---

## 3. The honest novelty statement (use this verbatim)

> We are not claiming a better geocoder or a better RPC model — both are mature markets with strong incumbents. We are claiming the **first implementation of a permission layer that sits between prediction and action in Indian collections**: an action that would disclose a debt is not in the candidate set unless the identity is verified to a modelled threshold, and a recovery notice or visit is not generated unless the address confidence clears a threshold — and both refusals are recorded, with the rule that caused them, in the same record that proves the action was allowed. The field evidence that unlocks those refusals is weighted by an integrity model, so the system cannot be taught the wrong address by a fake check-in.

**Why it is credible:** every element of that sentence maps to a system that exists (geocoder, dialer, identity check, geo-tagged visit) but none of which connects them to *permission*. And every element maps to a rule that is now enforceable: 08:00–19:00, borrower/guarantor only, one-day advance notice, no contact during hardship `[EXT]`.

**Why it is not "AI-powered" fluff:** the claim is falsifiable in one click — block the notice, show the rule, unblock it after evidence, show the record.
