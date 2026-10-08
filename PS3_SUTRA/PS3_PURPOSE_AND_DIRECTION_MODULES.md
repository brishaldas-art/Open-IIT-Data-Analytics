# SUTRA — PURPOSE CLASSIFICATION, ACTION ELIGIBILITY & LANDMARK DIRECTION CUES

**Why this document exists.** Requirements R11.x demand purpose classification and the 48-hour brief demands
*purpose → action eligibility* as a first-class decision module; section 4I of the due-diligence brief demands a
deterministic **landmark direction cue generator**. Both were previously scattered across sections. This document places
them, specifies them, and states their limits. Both are **rule-based, deterministic, abstaining, LLM-free** `[S96]`.

---

## Part 1 — Purpose classification + action eligibility (M7)

### 1.1 The second decision the product makes

Three **separate** named concepts — never collapsed into one `purpose` field:

```
belief + uncertainty ──► address_purpose ──► eligibility
(candidate, tier, radius)  HOME_LIKE | WORK_LIKE | OTHER | UNKNOWN  ──►  SERVE | VERIFY_FIRST | REFUSE

request_purpose  — the caller's declared purpose (security / purpose limitation; an access-control input, not an inference)
address_purpose  — what this place IS (the classifier below)
eligibility      — what ACTION is permitted here, for this request purpose
```

RBI's framework makes the **notice/visit decision** the irreversible act `[S55]`; purpose is what turns a coordinate
into a *permitted action*. It is therefore a module with its own contract, not a field on a form.

### 1.2 Inputs (all available at decision time; T0–T2 only)

| Signal | Source | Why it is admissible |
|---|---|---|
| `address_type` (residence / office / permanent_native) | official `addresses` | borrower-declared type; a prior, never a verdict |
| Visit outcome mix, dwell, time-of-day, weekday | official `field_visits` | measured practice: dwell median 207 s; outcome semantics already mapped `[S94]` |
| Repeat-visit pattern | memory (S12) | repeated successful visits at plausible hours |
| Nearest landmark **classes** (temple/school/water tank…) | official `landmarks_poi` (14 types) | a temple beside a house is context, not proof; class only, never the name for scoring |
| Note | `accounts` exposure fields are **not** inputs (role contract) | exposure explains targeting, not place purpose `[S96]` |

### 1.3 Rules (MVP — frozen unless labels justify a model)

| Rule | Condition (evaluated in order) | `address_purpose` | Confidence |
|---|---|---|---|
| P1 | `address_type = office` | **WORK_LIKE** | high |
| P2 | ≥2 integrity-passing `met_borrower` visits (independence per F2.2), dwell ≥180 s, majority of successes in 08:00–19:00 on weekdays, address not office-type | **HOME_LIKE** | medium |
| P3 | `permanent_native` (226 records, 0 ever visited) | **OTHER** — never a visit target by default | — |
| P4 | mixed evidence (P2 signals with ≥1 dominating business-hours-only success) | **abstain** | published as `UNKNOWN`, `basis: mixed_evidence` |
| P5 | no usable evidence | **UNKNOWN** | low, `basis: insufficient_evidence` |

**Never:** score purpose from a single observation (R11.2); infer home from a workforce address; use collector identity.

### 1.4 Eligibility gate (R11.3), explicit mapping

| `address_purpose` | Tier / state | `eligibility` |
|---|---|---|
| HOME_LIKE | CONFIRMED / PROBABLE | **SERVE** |
| HOME_LIKE | APPROXIMATE, or `n_neg ≥ 2`, or radius beyond the address band | **VERIFY_FIRST** (cheap task) |
| WORK_LIKE | any | **REFUSE** for notice/visit purposes — **unless** the borrower has independently confirmed this address as residence (flag `borrower_confirmed_residence`) |
| OTHER / UNKNOWN | any | **VERIFY_FIRST**, or **REFUSE** where the task requires a SERVE-grade location |

**Role of `request_purpose`.** It is an *access-control input*: the API requires the caller to declare why the
coordinate is being requested; the gate checks the declared purpose against `address_purpose` and this table and records
the decision (a notice requested at a WORK_LIKE place returns **REFUSE** with the reason logged).

**Abstention is a success state** and is counted in D21's metrics; the gate decision is logged with its rule version
(R11.5, R12.1).

### 1.5 Training policy

No `address_purpose` model is trained. There are **no purpose labels** in the official data, and inventing them is
forbidden. A learned classifier is admissible only after adjudicated labels exist (an operator workflow accepting or
rejecting purpose verdicts at scale) — recorded as a production-research option, not a gap to fill now.

---

## Part 2 — Landmark direction cue generator

### 2.1 What it is (and is not)

A **deterministic textual/directional enrichment** of a resolved candidate, built from official landmark coordinates
and landmark references already present in the address text. It is **not** road navigation, not turn-by-turn, not a
route: no road graph exists in the data, and none is assumed `[S96]`.

### 2.2 Inputs

| Input | Source | Notes |
|---|---|---|
| Landmark reference in the address text | parsed span: relation words (`near, opposite, behind, beside, adjacent, next to`) + landmark noun | the cleaning rules already extract these spans `[S90]` |
| Landmark candidates | official `landmarks_poi` — 240 POIs, 14 types, **names are not unique** (globally and even `(town_id, name)` repeats) | resolution is **town-scoped** and may return several; ambiguity is shown, not hidden |
| The candidate coordinate | S4/S7 output | directions are computed **from the candidate**, never from the truth |

### 2.3 Algorithm (all steps deterministic)

1. **Parse** the relation (if present) and the landmark noun phrase.
2. **Resolve** within the address's `town_id`; if several landmarks match, keep all within a plausibility radius and
   mark `ambiguous: true` (the memory rule: a repeated name is not an identity).
3. **Nearest relevant landmark:** compute distance from the candidate; if the parsed reference resolved, that landmark
   wins; otherwise the nearest of its type/class.
4. **Cue:** straight-line distance (rounded to 10 m), **bearing** relative to the resolved grid north, and — only where
   the parsed relation supports it — a relation word: *behind / opposite / beside / near*. No relation word is invented.
5. **Text template** (fixed strings, no generation):
   `"{landmark} ~{distance} m, bearing {N°/compass}{, behind/opposite/beside/before} it"`.

### 2.4 Output contract (in `/resolve` and in offline packs)

```json
"directions": [
  {"landmark": "water tank", "landmark_type": "water_tank", "distance_m": 120,
   "bearing_deg": 34, "cue_text": "water tank ~120 m, bearing NE, behind it", "ambiguous": false}
]
```

If no landmark is resolvable, or the nearest is beyond the plausibility radius (1.5 km in the supplied towns), return
`null` — **no cue is better than a wrong cue**. Directions are advisory: they never change tier, radius or eligibility.

### 2.5 Honest limits

* Bearing is a **straight line**, not a path; in dense lanes it may not match the walking route.
* Landmark names repeat across towns (and within them); resolution is scoped and ambiguity surfaced.
* The parser's relation words can be wrong in messy text; a relation word is only repeated verbatim, so a wrong parse
  shows the same wrong word the address contained — auditable, not amplified.

### 2.6 What this changes in the real workflow

A collector approaching a `PROBABLE` candidate reads "water tank ~120 m, bearing NE, behind it" and skips the
wrong-lane approach; a VERIFY_FIRST task ("photograph the landmark and the door") becomes cheap and specific. That is
the value: **fewer wrong-door attempts and shorter hunts**, using only what CreditNirvana already owns.

---

*Sources: `[S55]` RBI visit framework · `[S90]` official-data measurements · `[S94]` re-audit measurements ·
`[S96]` due-diligence pass. Locked architecture: `PS3_ARCHITECTURE_LOCK_CANDIDATE_2026-10-07.md`; API fields:
`PS3_API_AND_COMPONENT_DESIGN.md` amendment.*
