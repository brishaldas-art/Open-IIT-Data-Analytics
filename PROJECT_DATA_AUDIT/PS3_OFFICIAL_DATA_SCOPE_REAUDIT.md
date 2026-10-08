# PS3 OFFICIAL DATA SCOPE — RE-AUDIT (v2)

**Date:** 2026-10-07 (v2; supersedes v1 of the same day) · **Authority:** the official Drive folder `data` — <https://drive.google.com/drive/folders/11J0vOHyjHH0y4Vjw8_5HZxsBWyVgH48t>
**Verification:** all 21 files downloaded from the Drive and SHA-256 compared against the recorded hashes — **21/21 byte-identical, twice (morning and this pass)**. The 12 in-scope files were re-copied into `data/official_ps3/` with fresh hashes matching the Drive (12/12).
**Revision history.** v1 established scope from the pack README + structure. v2 adds: the A–G classification required by this pass, an explicit structural audit of **all eight** shared tables (including the two excluded ones), the language/agent integrity tests, candidate-anchor and radius-transfer measurements, the corrected warm/cold decomposition, and the workspace reconciliation. **v2 changes no v1 selection; it changes three published numbers (see §8).**

---

## 0. The evidence base for the scope decision

| Evidence | Status |
|---|---|
| Documentation inside the Drive | **None** — no README, no licence, no docs in any of the four folders (verified from listings) |
| The pack README ("CN Synthetic Collections Data") | Held in the workspace in two independent copies whose file-assignment rows are identical to each other (only path strings differ, because they were re-pathed by us) |
| Contemporaneous arrival record | `90_Archive/.../PS2_PS3_DATASET_REVIEW.md` — same four folders, same per-PS lists |
| Structural corroboration | every FK inside DATASET A resolves (0 orphans; one deliberate marker: `addresses.town_id='OUT'`, 237 rows) |
| Explicitly rejected as evidence | the archived **PS2-era README**, which labels agents/splits/lenders/payments "PS2 only" (see the reconciliation document) |

**The official assignment, verbatim (pack README table):** `accounts` PS1+PS2+PS3 · `splits` PS1+PS2+PS3 · `lenders` PS1+PS2+PS3 · `agents` PS1+PS2+PS3 · `dial_attempts` **PS1+PS2** · `payments` **PS1+PS2** · `addresses` **PS2+PS3** · `field_visits` **PS2+PS3** · `phones`/`skip_traces`/`verified_contact_points` **PS2** · the four `ps1_fake_ptp` files **PS1** · the six `ps3_geocoder` files **PS3**.
**The PS3 file list, verbatim:** `addresses.csv`, `baseline_geocodes.csv`, `field_visits.csv`, `visit_gps_points.csv`, `surveyed_addresses.csv`, `localities.csv`, `landmarks_poi.csv`, `towns.csv`, `accounts.csv`, `agents.csv` — plus "*All three also use* `splits.csv`", and `lenders.csv` assigned to PS3 in the table.

---

## 1. Full classification table — all 21 files

| Source | Table | Rows | PS3 relevance | Role | Training? | Inference? | Evaluation? | Leakage risk | Decision | Reason |
|---|---|---|---|---|---|---|---|---|---|---|
| ps3_geocoder | `towns` | 3 | Required | Static reference | — | ✔ | — | none | **INCLUDE** | Coordinate frame + address style |
| ps3_geocoder | `localities` | 36 | Required | Candidate-generation input | — | ✔ | — | none | **INCLUDE** | Gazetteer level; pincode + centroid |
| ps3_geocoder | `landmarks_poi` | 240 | Required | Direction aid (never a target) | — | ✔ | — | none | **INCLUDE** | Directions only; README says incomplete/off |
| ps3_geocoder | `baseline_geocodes` | 2,880 | Required | Prior / comparator | — | ✔ | ✔ | none | **INCLUDE** | The baseline to beat; 237 unpinned |
| ps3_geocoder | `visit_gps_points` | 160,406 | Required | Field-evidence medium | ✔ (T3/T4 lanes) | ✘ (device only) | ✔ (geometry QA) | **yes** — post-visit | **INCLUDE** | Trail per visit; never for the same visit's prediction |
| ps3_geocoder | `surveyed_addresses` | 100 | Required | Ground truth | **✘ never** | ✘ | ✔ only | **yes — catastrophic** | **INCLUDE — EVALUATION ONLY** | The only survey truth |
| shared | `addresses` | 3,117 | **A REQUIRED** | Model feature + candidate input | ✔ (text) | ✔ | — | none | **INCLUDE** | The problem's input |
| shared | `field_visits` | 5,578 | **A REQUIRED** | Field-evidence input | ✔ (eligible subsets) | ✔ via earlier-visit memory only | ✔ | **yes** — T3/T4 fields | **INCLUDE** | "Learns from field visits" |
| shared | `accounts` | 2,400 | **E EXPOSURE** | Exposure/sampling + business-value context | ✘ | ✘ (location); ✔ as prioritisation context | ✘ | **yes, if used as feature** | **INCLUDE — exposure/context only** | Explains who is visited; carries no location truth |
| shared | `agents` | 30 | **B USEFUL** | Integrity/monitoring + exposure (language) | ✘ | ✘ | ✘ | **yes, if used as feature** | **INCLUDE — monitoring/exposure only** | Collector properties, not place properties |
| shared | `splits` | 2,400 | **C EVALUATION-ONLY** | Protocol artefact | ✘ | ✘ | ✔ | none | **INCLUDE — evaluation only** | Official partition; account-level, time-blind |
| shared | `lenders` | 6 | **D CONTEXT ONLY** | Business context | ✘ | ✘ | ✘ | none | **INCLUDE — context only** | Officially PS3-assigned; **measured zero signal** |
| shared | `dial_attempts` | 51,105 | — | — | ✘ | ✘ | ✘ | **yes** — cross-domain | **EXCLUDE (G)** | Officially **PS1+PS2**; call/phone semantics |
| shared | `payments` | 2,162 | — | — | ✘ | ✘ | ✘ | **yes** — post-outcome | **EXCLUDE (G)** | Officially **PS1+PS2**; every payment post-dates the visit |
| ps2_right_party_contact | `phones` | 5,719 | — | — | ✘ | ✘ | ✘ | — | **EXCLUDE (F: PS2-only)** | Contact inventory |
| ps2_right_party_contact | `skip_traces` | 766 | — | — | ✘ | ✘ | ✘ | — | **EXCLUDE (F)** | Trace requests/results |
| ps2_right_party_contact | `verified_contact_points` | 250 | — | — | ✘ | ✘ | ✘ | — | **EXCLUDE (F)** | Phone verification campaign |
| ps1_fake_ptp | `ptps` | 3,696 | — | — | ✘ | ✘ | ✘ | — | **EXCLUDE (PS1)** | Promise-to-pay records |
| ps1_fake_ptp | `call_transcripts` | 39,194 | — | — | ✘ | ✘ | ✘ | — | **EXCLUDE (PS1)** | Call content |
| ps1_fake_ptp | `post_call_events` | 8,466 | — | — | ✘ | ✘ | ✘ | — | **EXCLUDE (PS1)** | Post-PTP follow-through |
| ps1_fake_ptp | `annotated_ptp_sample` | 200 | — | — | ✘ | ✘ | ✘ | — | **EXCLUDE (PS1)** | PS1 labels |

**Note on category F:** **no shared table is PS2-only.** The three PS2-only tables live in `ps2_right_party_contact/`. Inside `shared/`, the two tables not used by PS3 (`dial_attempts`, `payments`) are assigned to **PS1+PS2** — category **G (should not be used)**, not F.

## 2. A–G classification of the eight shared tables — with justification

| # | Shared table | Class | Justification (official semantics + data) |
|---|---|---|---|
| 1 | `addresses` | **A — REQUIRED** | Named in the PS3 file list; text/town are the query itself. Multiple accounts per address (706 accounts hold 2–3) and 226 unvisited `permanent_native` rows are properties of the input, not reasons to exclude |
| 2 | `field_visits` | **A — REQUIRED** | Named in the PS3 file list; the statement's "learns from **successful** visits" needs outcomes, dwell, check-in, accuracy, photo hash |
| 3 | `accounts` | **E — EXPOSURE / SAMPLING VARIABLE** (secondary: D business-value context) | Assigned to all three PS; carries the targeting variables (DPD, portfolio, outstanding). Measured: exposure strongly targeted, **yield flat across value quintiles (Q1 43.1% → Q5 41.8%; median outstanding met/not-met ratio 0.99)** — so it explains *where effort goes*, never *where the place is* |
| 4 | `agents` | **B — USEFUL** (integrity/monitoring; exposure for language) | Assigned to all three PS; names the collector. Measured: not_traceable spread 19.5–29.1% and met spread 36.2–45.9% across the 9 field agents; media duplication concentrated in one agent (162/610); tenure↔met correlation −0.16 (nil); `shift` has one value; language-match shows no benefit (matched 38.7% vs unmatched 40.8%, n=331) |
| 5 | `splits` | **C — EVALUATION-ONLY** | "All three also use splits.csv". Account-level, time-blind. Measured entity leakage: 1 test address shares an identical identity text with train, but **124 of 344 test addresses with a met visit (36.0%) lie within 30 m of a train met check-in** → split-aware reporting is mandatory |
| 6 | `lenders` | **D — CONTEXT ONLY** | Assigned to PS3 in the table; measured **no signal** (address style varies ≤1.4 pts across all three `kyc_address_format` values). Kept for provenance, never a feature |
| 7 | `dial_attempts` | **G — SHOULD NOT BE USED** | Assigned **PS1+PS2, not PS3**; semantics are call/phone contact attempts (15 of 16 columns are telephony), including a PS2 experiment artefact (`selection_propensity`). Including it would re-define the problem from "find the place" to "reach the person". Structural audit only (§3) |
| 8 | `payments` | **G — SHOULD NOT BE USED** | Assigned **PS1+PS2, not PS3**; every row is a post-visit financial event — a T4-after-outcome variable by construction. It exists in the shared folder because PS1/PS2 share it, not because PS3 does |

## 3. Structural audit of the two excluded shared tables (facts only — no PS3 statistic is derived from them)

| Table | Rows | Key (unique?) | Join keys to PS3 entities | Temporal | Leakage character | Verdict |
|---|---|---|---|---|---|---|
| `dial_attempts` | 51,105 | `attempt_id` ✔ | `account_id` → accounts (all PS3-relevant linkage would run through the borrower, never the address) | 2026-04-01 → 06-29 | contact-outcome fields describe **the phone**, and a call can post-date/precede any visit; using them would import PS2's target variable | Excluded. No feature, label, filter, weight or split uses it |
| `payments` | 2,162 | `payment_id` ✔ | `account_id` → accounts | 2026-04-01 → **07-24** (extends past the visit window) | every payment is a **post-outcome** event (T4); treating it as a signal would leak the future into the past | Excluded. No PS3 artefact reads it |

*Their exclusion removes no capability listed in the PS3 statement: the statement asks for a location with radius and directions learned from successful visits — not for recovery prediction. The cost of exclusion (no financial outcome variable) is documented in `PS3_SHARED_DATA_USAGE.md` §5.*

## 4. DATASET A — the canonical PS3 dataset

```
DATASET A = the 6 PS3-specific tables + the 6 officially PS3-assigned shared tables
          = 12 tables · 177,196 rows · 83 columns
```
```
                        lenders (6)   ── context only
                            │ lender_id
                            ▼
   towns (3) ◄── town_id ── accounts (2,400) ──1:1──► splits (2,400)  [EVALUATION ONLY]
      ▲                        │ account_id
      │ town_id                ▼
   localities (36)        addresses (3,117)          [model feature: text · candidate input: town]
      ▲                        │ address_id
      │                        ▼
   landmarks_poi (240)    field_visits (5,578) ──1:N──► visit_gps_points (160,406)
      ▲  (directions)          ▲ agent_id
      │                        │
   baseline_geocodes (2,880)  agents (30; 9 field)     [monitoring / exposure]
   surveyed_addresses (100)   ← EVALUATION ONLY, never a feature or label
```
Materialised hash-verified at `data/official_ps3/` (12 files). Raw Drive stays read-only. Cleaning → `data/cleaned/`; derived → `data/derived/`. Excluded: 9 tables · 111,558 rows.

## 5. Task 6 — can shared data improve these twelve things? (answer per line, with evidence)

| # | Question | Answer | Evidence from this pass |
|---|---|---|---|
| 1 | Address/entity resolution | **Yes — improved** | 81 co-located clusters (191 addresses, all cross-account) require evidence-based place identity; and an account's two met-visited addresses are **never** within 100 m (median 3,011.6 m, n=38 pairs) → **do not merge addresses by account** |
| 2 | Address normalisation | **No improvement available** | `kyc_address_format` carries no signal (≤1.4 pts); nothing new to normalise; rules stay text-driven |
| 3 | Candidate generation | **Yes** | `town_id` is 100% consistent between address and account (0 mismatches, 237 `OUT` excepted); **96.7% of the 2,326 coarse-pinned addresses have a street/rooftop pin of another address within 300 m (median 96 m)** — finer anchors exist for candidate generation |
| 4 | Candidate ranking | **Marginal** | Precision strata + anchor proximity are usable ranking inputs (PS3-table features); no shared field adds ranking power |
| 5 | Visit selection / exposure | **Yes — required for honesty** | Visits are targeted (exposure by DPD band and portfolio) while yield is flat (37.5–42.9% met; Q1–Q5 outstanding 43.1–41.8%); exposure variables must condition every yield claim |
| 6 | Field-visit evidence weighting | **Yes** | Outcome class + `gps_accuracy_m` + dwell + repeat-hash; per-agent not_traceable varies 19.5–29.1% → evidence quality is agent-influenced, so weights, not trust |
| 7 | Collector/agent integrity | **Partially — media duplication only** | 162/610 FA009 visits share a hash; tenure↔met r=−0.16; `shift` single-valued; language match unhelpful → **only media/timing integrity signals are justified** |
| 8 | Address-memory construction | **Yes** | Warm/cold cut test split-aware: warm **56.7%** met (val+test, n=441) vs cold **25.1%** (n=410); re-visit consistency median 77.7 m (same agent) vs 75.8 m (different agent) → memory is agent-independent |
| 9 | Uncertainty / radius calibration | **Yes, per stratum** | Train-fitted p80 radii: locality 539.9 m → **79.2% eval coverage**; street 162.1 m → 100% (n=5); **pincode 1,204.2 m → 0% (n=4)** → per-stratum radius table valid only where n allows; publish failures |
| 10 | Business prioritisation | **Yes — context** | Value does not predict visit success (above) → prioritise evidence spending by value × confirmability, never claim value raises accuracy |
| 11 | Dynamic learning / replay | **Yes** | Historical ordering with the 2026-05-15 cut; warm/cold decomposition on val+test only |
| 12 | Train/val/test splitting | **Partially** | Official split is usable for account-level claims; its account-level design leaves place-level leakage (36.0% of met test addresses within 30 m of train evidence) → add an entity/time-aware split ledger for address-level claims (evaluation-only, official benchmark untouched) |

## 6. Task 8 — does the corrected scope change the architecture?

**No component is added, removed or re-weighted by the scope correction.** Each impact area was checked against its evidence:

| Area | Verdict | Why |
|---|---|---|
| Exposure-aware learning | **Already in design; now mandatory** | Flat yield across value/DPD demands conditioning; no new component |
| Agent-integrity weighting | **Unchanged** | Media duplication was already the gate; the new tests (tenure/language/shift) justify *not* adding agent-based scoring |
| Memory / entity resolution | **Unchanged, strengthened** | Place clusters (81) now measured; "same account ≠ same place" adds a prohibition, not a component |
| Address ranking | **Unchanged** | Anchor-proximity signal is a feature inside the existing candidate ranker |
| Uncertainty | **Unchanged** | Per-stratum radius was the plan; the transfer test confirms locality and falsifies pincode — a calibration-table caveat, not a redesign |
| Field-visit replay | **Unchanged** | The cut test is the existing replay template; corrected cold number strengthens it |
| Business prioritisation | **Unchanged** | Value × confirmability framing already present |
| Evaluation protocol | **One amendment** | Split-aware reporting + the 66/19/15 surveyed-truth composition + the 36% place-proximity finding |

**Explicitly documented non-improvements (required by the brief):** `lenders` (no signal), `agents.language_team/shift/tenure` (no signal), `accounts.*` as location features (wrong variable class), `dial_attempts`/`payments` (out of scope + leakage). Nothing was added merely because it exists.

## 7. What would change if the organisers publish a different assignment

A single, clearly-marked revision path: if `dial_attempts` or `payments` were declared PS3-relevant, they enter as **context/exposure only** (never features or labels — their temporal character does not change), and the PS3 statement's scope would still not require them. No other table's classification would move.

## 8. Corrections issued by this pass (no silent overwrite)

| # | Previously stated | Correct now | Where corrected |
|---|---|---|---|
| C-1 | "post-cut confirmed addresses succeed 56.0% vs **40.5% for all other post-cut visits**" | 40.5% is the **overall** post-cut rate. Correct decomposition: **warm 56.0% (n=1,383) vs cold 24.5% (n=1,343)**; val+test only: 56.7% vs 25.1%. The finding is **stronger** than stated | v2 docs + dated note appended to the workspace business document |
| C-2 | "FA009's **83% of check-ins 10:00–13:00** is a missed-slot anomaly" | **Retracted.** Every agent is 79.5–88.7% in that window (schedule artefact). FA009's only measured anomaly is media duplication (162/610) | this re-audit; no active document carried it |
| C-3 | same/different-agent memory consistency 90.0 m / 98.0 m | Re-measured with a stated definition (median of per-address medians): **77.7 m / 75.8 m** — identical in substance (agent-independent), definitions now printed | v2 EDA |
| C-4 | "multiple accounts at one building ≥ 5 text groups" | 81 co-located clusters / 191 addresses; and **same-account addresses are far apart** (median 3,011.6 m) | v2 EDA/audit |

**v1 → v2 net effect on scope: none. On numbers: four corrections, all toward more conservative or better-evidenced statements.**
