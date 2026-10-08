# THE INTEGRATED PRODUCT
### A permission layer for the two irreversible actions in collections

---

# 1. The product in one paragraph

**SANKET/SUTRA is not a better dialer and not a better geocoder.** It is the layer that decides **whether a recovery action is permissible right now** — because the action is against an *unverified identity* (PS2) or at an *unverified location* (PS3) — and then proves that decision. Everything else in collections optimises *what to do*. This optimises *whether we are allowed to do it, and whether it is worth its cost* — and it learns from every visit that comes back.

**Positioning inside CreditNirvana:** a module behind Maestro. It makes Maestro's existing claims (*RBI compliant, audit trails, field efficiency*) **provable per decision** under the RBI framework effective 1 Jan 2027 and the TRAI rules notified 18 Sep 2026.

---

# 2. The product definition (Part-10 format)

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

# 3. The workflow

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

# 4. The one causal loop we will actually demonstrate

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

# 5. The 2–3 minute demo

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

# 6. Level 1 — 48-hour hackathon MVP (only what increases win probability)

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

# 7. Level 2 — competition-final version

Adds: hazard model for retest timing · purpose classification (home/work/shop) with the derived rule *"never deliver a notice to a non-home purpose"* · full integrity model with agent-level shrinkage · per-stratum radius with sample-size guards · IPW-corrected training metrics · field route with time windows (OR-Tools) computing **marginal** visit cost · an off-policy evaluation vs the synthetic legacy policy · a monitoring panel (ECE per segment, abstention rate, notice-gate block rate, refuse reasons) · 30-day pilot design with pre-registered counters.

---

# 8. Level 3 — production roadmap inside CN

Phase 0 (weeks 1–2): data contracts + rule-config service + decision-record table in CN's environment.
Phase 1 (weeks 3–8): real telephony/label ingestion, calibration on CN's book, notice gate live for one region, field packs for two districts.
Phase 2 (months 3–6): purpose classifier, integrity model, radius strata per district, Landmark table governance with a review queue, DPDP documentation (DPIA, retention, erasure workflow), model cards.
Phase 3 (months 6–12): graph features and LTR **only if they clear a measured-lift gate**; route optimisation coupled to the confidence output; conduct dashboard as a client-facing artefact; extension of the same evidence loop to repossession/legal workflows where the notice problem is identical.

---

# 9. Competitor-defensible story — "why can't CreditNirvana just build this?"

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

# 10. Failure scenarios (16)

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

# 11. What we will **not** do (so the scope stays honest)
Not building a dialer · not building a geocoder · not competing on offer/negotiation (CN's layer) · not claiming accuracy on synthetic data · not shipping GNN/sequence/bandit/lift models in the MVP · not building a customer-facing UI · not purchasing new personal data for the demo · not asserting compliance from logs alone.
