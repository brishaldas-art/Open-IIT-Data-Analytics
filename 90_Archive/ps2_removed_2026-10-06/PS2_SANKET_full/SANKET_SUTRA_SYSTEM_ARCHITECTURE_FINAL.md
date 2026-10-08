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
