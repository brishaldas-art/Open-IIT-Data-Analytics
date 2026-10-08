# SANKET — PS2 SOLUTION ARCHITECTURE
### Contact-point eligibility, right-party confidence and the priced next action

*25 sections as specified. Every component must justify itself against a simpler baseline; components that fail that test are marked **[CUT]** or **[v2]**, not quietly retained.*

---

## 1. Problem
CreditNirvana must predict P(right-party contact) **per contact point** and choose the next action — continue, switch point, switch channel, trace, visit — where **skip-trace is triggered by expected recovery versus cost, never by an attempt counter**. Three sub-problems: latent contact health is unobserved; most points are untested; and "borrower avoiding" vs "invalid" vs "recycled" look alike but need opposite actions. Add the 2026 regulatory frame: every contact is a *conduct* event, and debt-disclosing actions against unverified identities are prohibited.

## 2. User
| Consumer | What they see | Why they care |
|---|---|---|
| Allocation/strategy analyst | Nightly action list + exception queue | Cure rate, cost per rupee |
| Supervisor | Accounts the system refused to auto-touch | Is the refusal defensible? |
| Compliance officer | Decision records + conduct counters | Regulatory inspection |
| Dialer / orchestrator (machine) | Per-contact-point action with window | Execution |
| **Not the borrower** — the borrower is the subject of the decision, and the party the system protects | | |

## 3. Business objective
Primary: **reduce avoided waste and avoided conduct exposure** on the four expensive/irreversible actions (human call, field visit, trace, notice/legal), while holding or improving recovery. Deliberately *not*: maximising RPC, minimising dials, or maximising model AUC.

## 4. Data flow
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

## 5. Feature architecture
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

## 6. Model architecture
**Two models, not five.**
- **S1** `P(contact succeeds at this point, in this window | features)` — LightGBM, monotone constraints where sensible, isotonic-calibrated per channel × window bucket
- **S2** `P(right party | answer)` — LightGBM + isotonic, **trained only on answered calls** with tiered labels
- **S3 (timing sub-component)** hazard of "next successful contact", used **only** to rank retest times, not to produce probabilities shown to users
- **Rules floor** runs before both, and can veto their output.

`[CUT]` separate productive/PTP head in the MVP (it belongs to CN's offer layer, where our model adds nothing `[MODEL]`).

## 7. Label strategy
| Label | Source | Tier |
|---|---|---|
| Payment/PTP within N days of an RPC | ledger | 1 (near-gold) |
| Inbound call from the number | telephony | 1 |
| Agent-confirmed identity (doc/DOB challenge passed) | disposition | 2 |
| RPC inferred from disposition text | NLP | 3 |
| "Answered" | ring/talk duration + cause code | 1 (objective) |
| Recycled | agent marking, cross-account conflicts, ≥90-day disruption | 2–3 |
Never train on "which point was dialled" — train on "what happened when it was dialled", weighted by the propensity with which the policy chose it.

## 8. Bias / selection correction
- log `p(action chosen | context)` for every decision (a **requirement**, not a nicety)
- inverse-propensity weighting for training; report weighted *and* unweighted metrics
- **no randomised exploration stream** on small-ticket portfolios — at ₹205 incremental recovery per RPC, random contact has no ROI and creates conduct risk. Exploration is instead **within-envelope**: choose a different window/CLI among attempts we were already going to make.
- field-visit outcomes are treated as *policy-partially-independent* evidence and used to sanity-check calibration

## 9. Calibration
Isotonic on a held-out temporal fold for both models; **segmented** by channel × window × supplier-age; Platt where the segment has <1,000 points. Monitor ECE per segment weekly. Reason: a mid-range miscalibration changes which action wins the EV comparison.

## 10. Decision engine
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

## 11. Compliance gate (candidate-set construction, not post-hoc filtering)
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

## 12. Exploration strategy
- **No additional contacts** for exploration.
- VoI-directed **within-envelope** exploration: for ambiguous points, choose the window/CLI/channel that maximises information gain per attempt we already planned.
- **Retest scheduling** from the hazard sub-model (cheap, reversible, high-yield).
- `[v2]` Thompson/LinUCB **only** if a real randomised holdout becomes possible and the portfolio has the ticket size to fund it.

## 13. Expected-value / financial model
Inputs from `PS2_PS3_FINANCIAL_MODEL.md`: human call ₹33–44 per RPC; field visit ₹220 marginal / ₹370 standalone; trace ₹60–150; incremental recovery per RPC ≈ ₹205 at an ₹18.8k ticket `[MODEL]`. The engine's job is to **refuse** actions whose ENRC is negative — and to show that count.

## 14. API design
```
POST /v1/eligibility      {account, point, t} -> {eligible_actions[], blocked[{action, rule, config_version}]}
POST /v1/score            {account, points[]} -> {p_contact[], p_right_party[], hazard_band, drivers[]}
POST /v1/next-action      {account}          -> {action, window, channel, ENRC_breakdown, alternatives[], decision_id}
POST /v1/decision/{id}    -> full decision record (audit)
POST /v1/feedback         {decision_id, outcome}  -> ack + propensity stored
GET  /v1/health           -> model versions, ECE per segment, drift, refuse-rate
```

## 15. Database schema (PostgreSQL)
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

## 16. Training pipeline
Temporal split (train <T, validate T..T+14d, test T+14d..T+28d) → point-in-time feature build → IPW-weighted training → isotonic calibration on the validation fold → model card → registry. Nightly recalibration, weekly retrain, drift alarms on feature PSI and per-segment ECE.

## 17. Inference pipeline
Batch overnight for allocation (the primary path) + synchronous `/next-action` for interactive use. p95 target < 150 ms. Refusals and their reasons are recomputed at decision time from the *current* rule-config version, never cached.

## 18. Monitoring
Feature drift (PSI/KS) · per-segment ECE and Brier · refuse-rate by reason (a sudden rise = a rule misfiring) · conduct counters (out-of-window contacts, wrong-party contacts, grievance-state contacts — target zero) · decision-regret proxy on logged data · rule-config change log.

## 19. Explainability
Two layers only: (a) **reason codes** — human sentences ("identity unconfirmed at this point; disclosure actions blocked", "hazard peaks 19:00–20:00", "supplier age 11 days"); (b) SHAP top-5 attached to the record, never shown first. The reason codes are generated from the gate and the feature thresholds, so they cannot drift from the actual logic.

## 20. Audit trail
Every decision writes an immutable, versioned record containing: rule-config version, cost-table version, model versions, per-candidate ENRC, blocked candidates with the rule that blocked them, chosen action, propensity, and the timestamp in IST. Retention aligned to the mandated ≥6-month recording window, with a DPDP-compatible purge policy.

## 21. Failure modes
| Failure | Detection | Fallback |
|---|---|---|
| Labels are just dialer behaviour | calibration drifts off; field evidence disagrees | down-weight model, widen to rules floor |
| Disposition quality poor | high share of "other/unknown" | identity head disabled; all actions become no-disclosure |
| Rule-config stale vs a regulatory change | config-review SLA breach | freeze disclosure-capable actions until reviewed |
| Over-refusal (system blocks too much) | refuse-rate alarm + supervisor sampling | τ tuning with compliance sign-off, logged |
| Cost table wrong | ENRC decisions look absurd to ops | ops override with reason; override is logged and fed back |
| Recycling false positives | complaints from "answered-by-other" points | lower threshold sensitivity, keep challenge-only path |

## 22. MVP architecture (48 h)
Rules floor + S1 (contact) + S2 (right party) + EV gate with `wait` + identity gate + decision record + synthetic CN simulator + one screen showing **the refused action and why**. `[CUT]` hazard model, `[CUT]` IPW, `[CUT]` SHAP UI, `[CUT]` any exploration.

## 23. Production architecture
Feature store with point-in-time semantics · MLflow registry · nightly recalibration jobs · segment-level calibration monitors · rule-config service with change control and four-eyes approval · integration to Maestro's allocation and dialer layers · conduct dashboards for compliance.

## 24. Demo architecture
A single account, three contact points, one refused action, one unblocked action after evidence arrives (the PS2↔PS3 handshake), and an audit record opened live. Runs against the synthetic simulator **or** the sandbox, whichever is available, behind one switch.

## 25. Evaluation metrics
**Model:** PR-AUC (not ROC-AUC), Brier, ECE per segment, Precision@operating budget, and **precision of the recycled flag at the operating threshold** (a false positive costs an identity check; a false negative costs a disclosure).
**Decision:** refuse-rate by reason, % of disclosure-capable actions blocked below τ (must be 100%), avoided field slots, avoided traces, decision-regret proxy.
**Business:** cost per RPC, cost per productive RPC, ₹ recovered per human-agent hour, field-slot yield, trace ROI, cure/roll-back rate in bucket.
**Guardrails (all must be zero-or-alert):** out-of-window contacts, wrong-party contacts, contact while grievance open, contacts to non-borrower/non-guarantor, decisions without a complete record.
