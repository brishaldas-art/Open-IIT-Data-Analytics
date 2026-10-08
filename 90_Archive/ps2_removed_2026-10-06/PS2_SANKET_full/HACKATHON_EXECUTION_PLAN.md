# HACKATHON EXECUTION PLAN — SANKET + SUTRA

**Objective:** win, not submit. Translation: a judge must be able to say, in one sentence, *what changed and why it matters* — and see it happen on screen.

---

## 1. The win condition, read backwards

Hackathon judging in BFSI essentially reduces to four questions: **Is the problem real? Is the solution novel *for us*? Can it be built? Did you show it working?** Long architecture documents lose to a crisp story plus a working screen.

Therefore the plan is built so that the *minimum viable story* is also the *minimum viable build*:

> A recovery notice is about to be served at an address the system is only 41% sure is valid. The system refuses to serve it and says which rule drove the refusal. Evidence arrives — a field visit at a landmark near the address. The confidence clears the threshold and the notice is released, with the evidence and the rule recorded. Then someone submits a fake check-in from six kilometres away; the system does not move its belief — it **widens** and keeps the notice blocked on a second condition.

Everything else in the design exists only if it strengthens that loop or a number next to it.

---

## 2. 48-hour MVP — build exactly this, nothing else

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

## 3. What each demo beat needs from the build (contract)

| Beat | Screen | Machine requirement |
|---|---|---|
| Refusal | Decision | `conf_address = 0.41 < 0.70`; reason code `ADDR_CONF_LOW` + `NOTICE_PRECHECK` |
| Evidence | Evidence | One check-in: landmark match, dwell 6 min, `device_trust` high, `w = 0.95` |
| Reversal | Decision | `0.78 ≥ 0.70` → `ALLOW`; ledger row written with both reasons |
| Poisoning | Evidence | Spoofed check-in 6.1 km away; `w = 0.20`; `conf 0.79`, **`radius_90` 90 m → 520 m** |
| Identity gate | Queue | Two accounts with identical connect probability, opposite `P(right party)` → different permitted actions |

If **any** of these five cannot be produced, the demo must be re-cut to the four that can. Never narrate a screen that is not on screen.

---

## 4. Competition-final scope (4–8 weeks, if we advance)

Ordered by winning value, not by technical interest:

1. **Shadow-mode pilot evidence**: run against 2–4 weeks of historical cases; publish the counterfactual (how many notices/visits would have been blocked, how many traces avoided, at what claimed risk).
2. **Timing model (S3)** with the censoring fix, if and only if it beats the hour-of-day baseline on a held-out window.
3. **Address calibration by stratum** with real field outcomes; replace synthetic radii with empirical ones.
4. **Integrity model M3 v2**: device fingerprint, route plausibility between consecutive check-ins, photo-OCR of the door plate, collector-level anomaly detection.
5. **Permission ledger export** in a format a compliance officer can hand to a regulator (CSV + signed JSON).
6. **One integration** end-to-end: notice generation → gate → suppression or release, with the counterfactual logged — not a dashboard.

---

## 5. Production roadmap (12 months, with gates)

| Phase | Months | Deliverable | Gate to proceed |
|---|---|---|---|
| P0 Pilot | 0–1 | Shadow mode on one region; counters pre-registered | Field GPS captured on ≥70% of visits; geocoder licence permits runtime use |
| P1 Gate live | 2–3 | Notice/visit gate in production for one bucket; humans override with reason codes | Zero unlogged suppressions; override rate <15% |
| P2 Identity gate | 3–6 | Disclosure-capable actions restricted by modelled P(right party); point-level dispositions modelled | Measured wrong-party rate down; no drop in cure in bucket beyond tolerance |
| P3 Learning loop | 6–9 | Address confidence recalibrated on real field outcomes; radius replaced by empirical strata | Coverage of `radius_90` verified; drift monitor live |
| P4 Scale | 9–12 | Multi-portfolio (ticket-conditional policies), trace EV, field route integration | ROI holds in a **second** book (the real test) |

**Kill criteria (pre-registered):** if the identity gate does not reduce measured wrong-party contacts, or the address gate does not reduce wasted visits by ≥5 pp, or override rate exceeds 25%, **stop and re-scope** rather than iterate.

---

## 6. Anti-patterns we will not ship
Building our own geocoder · an LLM in the decision path · a GNN/sequence model · bandits before a real randomised holdout · a map UI nobody in collections asked for · a dashboard with no action attached · a compliance claim resting on "we log everything" · presenting synthetic results as measured · reusing the 1,400 m→90 m example as if it were real.

---

## 7. "How would I beat this team?" — adversarial pass

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
