# SUTRA — FIELD EVIDENCE ARCHITECTURE

The component that turns a visit into *structured, weighted, auditable evidence* — and the reason SUTRA is not
`address → ML → coordinates`. Its one-line rule: **weight, don't accuse; positive evidence moves belief, negative
evidence moves priorities, and neither is ever taken as truth.**

---

## 1. What a visit actually produces (measured, not assumed)

| Observable | Source field(s) | Measured behaviour in the official dataset [S90] |
|---|---|---|
| outcome (two dimensions) | `outcome` | met-someone 40.6% · `locked_premises` 22.4% · `address_not_traceable` 25.1% |
| dwell | `dwell_s` | met_borrower 16.6 min · `address_not_traceable` **1.3 min** · 443 visits < 60 s |
| check-in vs trail | `visit_gps_points` | median agreement 7.6 m; worst visit 500 m; max implied speed 32.2 km/h (i.e. **no spoof in this data**) |
| trail shape | points per visit | median 26 points; 68 visits with < 5 points (weak evidence class) |
| media integrity | `photo_hash` (agents) | one agent at 25.6% duplicate hashes vs < 0.3% for all others |
| agent behaviour | rolling agent baseline | dwell/agreement/duplicate-rate per agent, windowed |
| geo reliability | `gps_accuracy_m` | median 10.0 m, p90 21.0 m — a **68% radial confidence**, not a bound [S26] |
| absence signal | repeated negative outcomes | 1,400 `address_not_traceable` visits, 53 of them on surveyed records: **1,603.2 m from truth** |

**The decisive measurement** (`ps3_evidence_diagnostics.csv`): on the surveyed subset, met-someone check-ins are closer to
the vendor pin than to truth only **3.2%** of the time, while `address_not_traceable` check-ins are closer to the pin
**84.9%** of the time. Failure visits collect *at the pin*. Any architecture that reads a check-in as "where the place is"
without conditioning on outcome is measuring the wrong thing — and that is precisely the trap this component exists to
avoid.

---

## 2. The evidence object (what is stored per visit)

```
evidence_score {
  visit_id, address_id, observed_at,
  w_place ∈ [0,1], w_person ∈ [0,1],          -- two dimensions, never summed into one "trust" score
  reason_codes[],                             -- e.g. ["dwell_short","photo_duplicate","trail_agree_high"]
  dims { outcome_place, outcome_person, dwell_band, trail_agreement, media_integrity,
         agent_baseline_z, accuracy_class, points_class },
  policy_version, created_at
}
```

Design rules baked into the object:

1. **Two dimensions.** "The place is right" and "the person is there" are different beliefs. `locked_premises` is a
   *place-positive, person-indeterminate* visit; `neighbour_says_shifted` is place-positive and person-negative (a real
   product signal: the address is right, the household may have moved).
2. **Reason codes, always.** A weight without a reason cannot be reviewed, appealed, or debugged.
3. **Policy version.** Weights are a policy; changing the policy re-derives scores from immutable observations
   (`PS3_DATA_ARCHITECTURE.md` §2.3).
4. **No single signal can zero a visit.** Only the *absence of usable evidence* produces `w = 0` (e.g. no trail, no dwell,
   no outcome) — never one suspicious field.

---

## 3. Weighting (the mechanism, in order of application)

```
w_place = w_outcome(place_dim)
        × m_dwell(dwell_band, stratum)
        × m_trail(agreement_class, points_class)
        × m_media(duplicate/near-duplicate ratio, per agent window)
        × m_agent(agent rolling baseline z-score)
        × m_accuracy(accuracy_class)
        × m_recency(policy horizon)      -- old evidence decays; it is never deleted
```
Each multiplier is in a stated band (documented in the policy table, not invented per call):
`m_dwell`: met-someone with a realistic dwell → 1.0; sub-minute dwell → ≤ 0.35; `m_trail`: agreement ≤ 25 m and ≥ 5 points
→ 1.0, no trail → 0.6 with `trail_missing`; `m_media`: duplicate ratio in the agent's control band → 1.0, above the
fleet p99 → ≥ 0.4 with `photo_duplicate`; `m_agent`: the agent's own rolling window, so an agent who improves is not
punished forever; `m_accuracy`: 10 m → 1.0, 50 m → ≤ 0.7.

**Neutrality is explicit:** with no adverse signals, all multipliers are 1.0 and the weight is the outcome's base weight.
The system does not require anyone to be suspected in order to work; `insufficient_evidence` is a normal, recorded state.

---

## 4. Integrity layer — "weight, don't accuse"

| Signal | Detects (red-team class) | Rule | Weight effect | Never does |
|---|---|---|---|---|
| mock-location flag / device attestation | F1 spoofing | platform signal [S26] | hard multiplier ≤ 0.2 + reason | reject the visit outright |
| implied speed / teleport | F1 | > fleet p99.5 step speed | ≤ 0.3 + reason | accuse the agent in the log's narrative |
| coordinate reuse across agents/days | F1/F2 | identical coords beyond plausibility | ≤ 0.5 | block the record |
| duplicate / near-duplicate media | F2 | hash identity + perceptual distance | ≤ 0.4 (per above) | invalidate the agent's whole history |
| trail↔check-in disagreement | F3/F1 | > 3 × accuracy-class radius | ≤ 0.6 | move the coordinate to the trail |
| dwell implausibility | F3 | sub-minute for a place claim | ≤ 0.35 | overrule the outcome |
| agent rolling baseline deviation | F2/F6 | z-score on dup-rate/dwell/agreement | scoped multiplier | permanently label a person |
| **insufficient evidence** | — | missing trail/media/accuracy | ≤ 0.6 + `insufficient_evidence` | pretend certainty |

Two invariants enforced by tests:
* **No negative-evidence movement:** no instruction type exists that changes a coordinate from a negative outcome
  (`PS3_UNCERTAINTY_ARCHITECTURE.md` §4).
* **No zeroing by one signal:** a unit test fails if any single multiplier can drive `w_place` to 0.

---

## 5. How evidence changes belief (the update rule)

| Evidence | Effect on belief (fast loop) |
|---|---|
| met-someone / cash-collected, integrity ≥ threshold, at a position within the record's current tier radius | reinforces that position (weight accumulation), may step the tier up by **one** level, never straight to `CONFIRMED` |
| met-someone far from the current position (> 2 × tier radius) | creates a **second supported position** and marks the record `CONTESTED` (F4) |
| met-someone with low integrity weight | recorded as support, no tier change, contributes to the buffer only if above `w_min` |
| `locked_premises`, place-positive | weak support; widens nothing; strengthens the *record* (the door exists) |
| `no_such_person` | person-dimension negative; the *place* may be confirmed; raises a "household moved" note |
| `neighbour_says_shifted` | raises re-verification priority; contributes to `record_suspect`; **no coordinate change** |
| `address_not_traceable` | `record_suspect` only; higher re-verification priority; **never** a coordinate change (F15) |
| contradiction between two strong supports | `CONTESTED` + widened radius + review task (F4) |
| second independent confirmation (different visit, different day, integrity ≥ threshold) | the only path to `CONFIRMED` [S49] |

**"Independent" is defined:** different `visit_id`, different `observed_at` day, integrity weight ≥ threshold, and not
traceable to the same media hash or the same agent-day cluster.

---

## 6. Re-verification and adjudication

* **Queue:** `verification_task(address_id, priority, reason_code, created_at, state, outcome)`.
  Priority = f(value at stake × current uncertainty × age × suspicion) — a *rule*, and the rule is published.
* **Adjudication** (supervisor confirms/denies a visit) is the only source of new ground truth. It enters as an
  `observation` with `kind='adjudication'` and the **highest** evidence class; a surveyed record [S90] remains the
  benchmark (adjudications are not used as S-Eval, to keep the test set pristine).
* **Dispute path:** a field agent or an operator can attach a note to an evidence score; the note is stored with the score
  and is visible in review — the record is not silently altered.

---

## 7. The fault-injection bed (how detections are measured)

Because this dataset contains no spoofing and exactly one anomaly type, every integrity claim is measured on injected
faults (`PS3_RED_TEAM.md` §2): mock-offset trails (300–2,000 m), teleports (> 80 km/h), photo reuse, coordinated fake
confirmations, stale beliefs, contradictions. Reported per detector: **recall, false-positive rate on clean visits, and
detection delay**, always as *injection-based* figures — never presented as real-world rates. The clean-visit
false-positive rate is the one that decides whether the weighting ships: a layer that punishes honest agents is worse
than no layer.

---

## 8. Privacy, purpose, and the data subject

* **Minimisation:** raw trails are retained 90 days; the derived evidence score persists (`PS3_DATA_LINEAGE.md` §6). Media
  beyond hashes/verdicts is not part of the learning asset.
* **Purpose:** every reading of evidence or belief declares a purpose; the eligibility gate is a separate rule component
  ([S48]'s shipped pattern: status + human review before an action is taken), so evidence weight never silently becomes a
  consequential decision.
* **Person-dimension caution:** `no_such_person` and `neighbour_says_shifted` are useful for the *address record*, but
  they must not become a standing judgement about a household. They are stored, decay like other evidence, and expire
  from the queue when the record resolves.
* **Agent-facing fairness:** integrity weights are windowed, reason-coded, and visible to the agent's supervisor with the
  clean-visit false-positive rate attached; no *rate* is ever claimed without its measurement basis.

---

## 9. Why this component cannot be replaced by something simpler

| Simpler alternative | Why it fails here |
|---|---|
| Treat the check-in as the label | measured 1,603 m error on failures and a 1.3-minute dwell (F15) |
| Binary accept/reject per visit | loses good visits, and still lets coordinated fakes through once; and it makes an *accusation*, which is a fairness and governance problem |
| Trust the outcome field | outcomes are agent-reported; the dataset's own duplicate-photo agent shows reporting and reality diverge |
| Trust GPS accuracy as a bound | it is a 68% radial confidence [S26] |
| Aggregate everything into one "trust score" | destroys the place/person distinction that makes `locked_premises` and `no_such_person` informative, and makes the logic unauditable |

**What it changes in the real workflow:** the field app can tell an agent *where doubt lies* while they are still standing
there (`score_visit`, T2), the back office gets a queue ordered by evidence-driven suspicion instead of by hand, and the
record carries a reason for every belief it holds. None of that exists in `address → ML → coordinates`.


## Amendment F1 — the integrity basis is media and timing; agent traits are not features · 2026-10-07

**Correction of record (retraction).** The integrity justification originally quoted "645 check-ins (11.6%) >500 m
from their own trail". That figure is **not reproducible**: measured against the *nearest* own-trail point the largest
gap is **90.8 m** (median 7.6 m; zero visits >100 m). The claim measured to the trail *centroid* (1,016 visits,
18.2%) and to the trail *start* (2,353, 42.2%) — neither is anomalous, because a check-in is by construction a point
on the agent's own path. The sentence is withdrawn; the weight-based design (D11) is unchanged.

**What replaces it (measured).** (i) **Media duplication** — one collector carries a repeated photo hash on
**162 of 610 visits**, next highest 4 (172 visits overall) `[S94]`; the only sharp integrity signal in the data.
(ii) **Timing plausibility** (server-time checks, dwell, sequence). (iii) **Per-collector monitoring baselines** —
the not-traceable rate spread across the nine field collectors is **19.5–29.1%** and met 36.2–45.9%: enough to
compare a collector against their own windowed history, never to score a visit by who collected it by default.

**Explicitly rejected as features, with the measurement.** Tenure ↔ met correlation **−0.16**; `shift` has a single
value; borrower↔collector language match shows **no** benefit (38.7% matched vs 40.8% unmatched, n=331) `[S94]`.
Collector identity therefore stays a weight and a monitoring key, never a ranking feature.

**The remark lane becomes a designed channel.** **208 of 5,578 remarks (3.7%)** carry corrective location knowledge
("actual house behind Park, 2 lanes ahead"); **zero** name a locality. The next capture design turns that prose into
structure — a landmark pick-list and a "where is it really" nudge inside the ~20-second capture budget — extracted,
audited, and never trained on as a label.

---


## Amendment F2 — negative-evidence semantics and confirmation independence (2026-10-07)

### F2.1 Negative evidence: from an absolute rule to a graded, audited one

**Old wording (now withdrawn as too absolute):** "negative evidence can never move a coordinate."
**Corrected rule:**

> **One negative observation can never relocate a coordinate by itself. Accumulated independent negative evidence can demote, widen, mark MOVED_SUSPECTED/CONTESTED and trigger re-verification. Only positive evidence or adjudication can establish a new primary coordinate.**

Why the change is *earned*, not convenient: 1,400 `address_not_traceable` check-ins sit **1,603.2 m** from truth
(median) and 84.9% of them are nearer the *pin* than the truth `[S90]` — that is why one negative alone can never
relocate a coordinate, while accumulation is what earns the system the right to doubt out loud. But a place that fails twice across different collectors and periods, while the pin is served as
CONFIRMED, is exactly the case the system must be able to *doubt out loud* (T8 auditability; D05's honesty ladder).

Mechanics (deterministic, no model): count **independent** negatives `n_neg` (definition F2.2);
`n_neg ≥ 2` across distinct collectors or periods ⇒ tier capped at `APPROXIMATE`, radius widened to the
parent stratum, reason code `negative_accumulation`, and a `verify-first` task is generated. Coordinates do not
move; the *state* does. The change is unit-tested and alarm-monitored, and experiment **M** now measures the
graded rule against the old absolute rule instead of only a strawman.

### F2.2 What "independent" means (promotion rule v2)

Two observations are **not** independent merely because they are two visits. Independence is now a scored tuple —
promotion to `CONFIRMED` requires **≥ 2 independent positive confirmations** where independence counts:

| Dimension | Counts as independent when… |
|---|---|
| Visit | different `visit_id` (trivial) and different day |
| Collector | different `agent_id` **or** a media-verified solo visit |
| Period | ≥ 7 days apart (label-lag realism), or across the 2026-05-15 cut |
| Media | different photo hash **and** not part of a duplicate-hash cluster (FA009 rule) |
| Source | candidates from different arms agree (vendor ∧ gazetteer ∧ field), not two rows from one arm |
| Space | the two check-ins agree within the measured consistency band (median 77.7 m; use p80 by stratum) |

One visit can satisfy several dimensions; the rule requires **at least two distinct collectors or periods plus
media independence** to promote. `WARM` remains the state for anything weaker — visible, usable as a prior,
never published as confirmed. This directly implements the audit finding that **same-account / same-agent
repetition is not corroboration** (the 73.5% repeat-visit share means the naive count overstates evidence).

### F2.3 What changes in the workflow

An unreachable address no longer sits forever as "confirmed, someone failed once" nor flips on one bad visit: it
ages into **`MOVED_SUSPECTED` → verify-first**, which is precisely the cheap task R9.4 promised and the notice gate
(D05/D19) can rely on.
