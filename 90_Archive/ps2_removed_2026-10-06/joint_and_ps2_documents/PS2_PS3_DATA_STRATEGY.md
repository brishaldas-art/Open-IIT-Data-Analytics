# DATA STRATEGY — A / B / C / D, per feature

**A = CN-provided** · **B = public / open / licensable** · **C = synthetic** · **D = must-not-fabricate**

Universal rules applied throughout:
1. **Never present C as measurement.** Every synthetic-derived output carries a `SYNTHETIC` marker in the API payload, the console and the deck.
2. **D is a hard line.** We would rather abstain than invent. Where a label or an input is unavailable, the product abstains (blocks the action) rather than guessing — abstention is the compliant default, not a failure.
3. **No new personal data purchased for the demo.** Enrichment in the demo is limited to what CN already holds.
4. **Immutable exclusions:** Bhuvan/ISRO (ToS); commercial geocoder output may be used **at runtime** but **must not be stored or cached as training data** (licence + DPDP minimisation).
5. **Minimum-necessary data** for every feature, with retention tied to the recovery record's life, and a documented lawful basis per processing purpose.

---

## 1. SANKET (PS2) features

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

## 2. SUTRA (PS3) features

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

## 3. Minimum viable data ask (the honest version)

**If CN gives us only two things, these are them:**
1. **Field-visit GPS + outcome at visit level** (SUTRA's learning loop),
2. **Point-level contact dispositions with the incumbent policy's attempts** (SANKET's labels and the propensity correction).

Without (1) SUTRA becomes a geocode + notice-gate product (still valuable, still novel in the permission sense, but no learner). Without (2) SANKET cannot claim any improvement over a rules floor and should ship as the identity gate + EV gate only — which is still the part that maps to the RBI framework.

---

## 4. Data-protection posture (short form)
- Lawful basis per purpose documented; geospatial inference and profiling are separate purposes from servicing.
- Field-agent location is **employee/work-device** data: purpose limitation, no continuous tracking outside the visit window.
- No training on commercial geocoder responses; no re-identification attempts on third parties; no contact data for non-borrowers as a *target*.
- Erasure vs retention conflict: the recovery record (audit) and the address evidence (product) must have documented, different retention clocks.
- Every pilot artefact that leaves CN's environment is aggregate-only.

**One sentence for the deck:** *our data strategy is to abstain where we cannot measure, and to measure only from evidence CN actually owns.*
