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
