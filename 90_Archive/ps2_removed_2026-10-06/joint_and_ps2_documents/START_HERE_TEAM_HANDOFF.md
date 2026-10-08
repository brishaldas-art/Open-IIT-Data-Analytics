# START HERE — team handoff

**CreditNirvana PS2 + PS3 · read this file first, then work from the folders.**

Written 6 October 2026. This is the version to circulate to the team: it says what we're building, what's already decided, who does what, what you must never claim, and where every number comes from.

---

## 1. The idea in 90 seconds

CreditNirvana gave us two problem statements — PS2 (who to call / when to skip-trace) and PS3 (find a messy Indian address and be honest about how sure we are). We researched 24 real systems that solve these problems in production (Experian, FICO, TransUnion, Pega, the New York State tax department, Meesho's GeoIndia, Indian logistics platforms) and then reviewed the official dataset table by table.

**Both problems turn out to be about permission, not prediction.** The prediction layers are already sold by a dozen vendors. What is missing is a system that decides what the platform is *allowed* to do, prices that decision in rupees, and records why it refused.

So we are building one product with two halves:

| Half | PS | What it permits | Name |
|---|---|---|---|
| Identity | PS2 → `../PS2_SANKET/` | A **disclosure-capable contact** — a call that reveals a debt to whoever answers | **SANKET** |
| Location | PS3 → `./` (this section) | A **legally-required notice and a doorstep visit** | **SUTRA** |

**The one-line pitch:** *the irreversible actions are gated on evidence, every refusal is recorded with the rule and the counterfactual value, information (a trace, a visit) is only bought when it can change a decision, and field evidence is integrity-weighted so it cannot be faked into moving the belief.*

**The architecture, in shape:**

```
state → evidence fusion → calibrated uncertainty → policy/permission (with refusal ledger)
      → economics (EV, EVSI, conduct penalty) → capacity allocation → execution
      → event-sourced feedback → back to state
```

Prediction is **one layer inside** this, not the system. If someone asks "what's your model?", the correct answer is "which layer?".

---

## 2. How the folder is divided, and what is binding

**Two sections, and nothing else.** The whole workspace — documents *and* data — is split by problem statement, so each half
can be handed to one owner. The joint material is duplicated, byte-for-byte, inside both.

| Section | Holds | Status |
|---|---|---|
| **`PS2_SANKET/`** | Everything PS2: assumptions, deep research, requirements, 12 architectures compared, 7 options scored, the selection, **the final 30-section design**, the SUPERSEDED hypothesis at the section root, its own `data/raw/`, its acceptance table `../PS2_SANKET/data/derived/derived_ps2_policy_baselines.csv`, its `tools/` | **BINDING for PS2.** Start at `README_PS2_SANKET.md` |
| **`PS3_SUTRA/`** | Everything PS3: 15 architectures compared, 7 options scored, the selection, **the final 30-section design**, the SUPERSEDED hypothesis, `data/raw/`, `data/derived/derived_ps3_radius_calibration.csv`, `tools/` | **BINDING for PS3.** Start at `../PS3_SUTRA/README_PS3_SUTRA.md` |
| **`90_Archive/ps1_fake_ptp_not_used/`** | Four tables from a third problem statement (promise-to-pay) that neither design uses — kept, not used | Outside both sections, deliberately |

| Where to look inside either section | Trust it for |
|---|---|
| `CreditNirvana_PS2_PS3_MASTER.md` | The whole deliverable in one file: Part 0 = this handoff, Part I = the 20 conclusions, Part XIV = dataset review, Part XV = all 13 Phase-4 files. **The file to email.** |
| `SANKET_SUTRA_SYSTEM_ARCHITECTURE_FINAL.md` · `FRONTIER_PS2_PS3_ARCHITECTURES.md` | **BINDING.** The integrated system (two contracts, the joint trace-vs-visit decision) and the frontier list where every idea is labelled BUILD NOW / BUILD IF TIME / PRODUCTION / RESEARCH ONLY |
| `SIMILAR_SYSTEMS_REVERSE_ENGINEERING.md` · `ARCHITECTURE_DECISION_LOG_FINAL.md` · the two bibliographies · `PS2_PS3_RESEARCH_SYNTHESIS.md` | **BINDING reference.** Reverse-engineering of 24 real systems, the 31 decisions with reversal conditions, the source registers, the research synthesis |
| `PS2_PS3_DATASET_REVIEW.md` · `data/` · `tools/dataset_audit.py` | **BINDING.** Every dataset number, the acceptance baselines, the 12 traps, and the runnable audit |
| The strategy files (`CN_QUESTIONS.md`, `PS2_PS3_RED_TEAM.md`, `NOVELTY_MATRIX.md`, `PS2_PS3_MARKET_RESEARCH.md`, `PS2_PS3_FINANCIAL_MODEL.md`, `PS2_PS3_DATA_STRATEGY.md`, `HACKATHON_EXECUTION_PLAN.md`) | Current strategy: competitor map, red team, novelty, money, data plan, **the questions we must ask CreditNirvana**, execution plan |
| `tools/financial_model.py` + output · `SANKET_SUTRA_DEMO.html` | The financial model and the clickable demo prop |
| `CreditNirvana_PS2_PS3_Research_and_Strategy.md` · `_superseded/` · the two `*_SOLUTION_ARCHITECTURE.md` | Historical: still the source of most external benchmarks, but its *design* is superseded |

**Read in this order if you're new:** `HOW_TO_USE_AND_UNDERSTAND_THIS_PACKAGE.md` (the manual, six acts) → `CreditNirvana_PS2_PS3_MASTER.md` Part I → `SIMILAR_SYSTEMS_REVERSE_ENGINEERING.md` §14 (the seven patterns) → `README_PS2_SANKET.md` and/or `../PS3_SUTRA/README_PS3_SUTRA.md` → the two `*_FINAL.md` designs.

## 3. The numbers that carry the argument

Memorise these five. Every one is reproducible from the official dataset with `dataset_audit.py` (see §6).

| # | Fact | Why it matters |
|---|---|---|
| 1 | Refusing only the **third consecutive** dead call to a point raises RPC per call **0.1762 → 0.1872** while removing **12.5%** of calls | We can do *less* and win — and the naive "never call a dead point" rule is **wrong** (points with ≥1 prior dead call are 42.7% of calls but 37.4% of successful contacts) |
| 2 | **77%** of trace spend (₹61,605 of ₹79,650) found nothing, and predicting which trace works is *not learnable* (CV AUC 0.574 vs 0.772 majority) | Kills the "predict the trace" idea; turns the waste into a visible, arithmetic refusal (EVSI: buy only if value of information > ₹104) |
| 3 | Vendor address error is **stratum-dependent by 35×**: median **37.7 m** (rooftop) → **1,336.5 m** (pincode), two independent samples agreeing | The geocoder already tells us its error band and nobody uses it. Calibrated truth is our cheapest, strongest PS3 deliverable |
| 4 | Free data cannot beat **370 m** (our own oracle test); field evidence reaches **29 m** median on visits where the agent met someone (82% under 100 m) | The accuracy engine is the **field visit**, not a better geocoder |
| 5 | **11.6%** of check-ins sit >500 m from their own GPS trail, and one agent has **162/172 duplicate photo hashes** | Without an integrity gate, the learning loop poisons itself. The gate is a feature, not plumbing |

**The honest ceiling we must state out loud:** honest pre-dial model AUC is **0.670** (logistic 0.604). If you add post-dial fields you get 0.933 — that number is **leakage** and must never be quoted as a result. It exists in our decks only as a warning.

---

## 4. What we are building (48 hours)

The frozen `BUILD NOW` list from `FRONTIER_PS2_PS3_ARCHITECTURES.md`:

**PS2 — SANKET:** event log → state machine (`CONTACT_POINT_STATE` with owners, decay, dead-streak) → identity fusion (P(borrower) with an interval) → one calibrated multi-class model (pre-dial features only) → **hard rulebook + refusal ledger** → EV with a published cost table → **EVSI on traces** → day-level allocator (greedy first, MILP if time) → outcomes back into the log.

**PS3 — SUTRA:** parse → retrieve → rank → vendor stratum prior → **integrity gate** → field-evidence fusion (dwell- and outcome-weighted stop detection) → **per-stratum conformal radius** → two contracts to PS2 → **two-confirmation promotion**.

**Integration:** exactly **two** contracts. PS3 → PS2: `P(within 200 m)` + promotions. PS2 → PS3: `visit.completed` + the value of confirmation. One shared event vocabulary. The single genuinely joint decision: **a field visit buys both identity and location information and cannot be undone — neither half can price it alone.**

### Workstreams (map to 3–5 people)

| WS | Owner (fill in) | Scope | Done when |
|---|---|---|---|
| **A. PS2 core** (`../../PS2_SANKET/`) | | State machine, gate, refusal ledger, EV + EVSI | Reproduces fact #1 and fact #2 with a ledger output |
| **B. PS3 core** (`../`) | | Integrity gate, fusion, radius table, promotion | Reproduces facts #3–#5; radius table with two-sample agreement |
| **C. Integration + allocator** | | The two contracts, joint visit EV, day plan + shadow prices | Changing `P(within 200 m)` visibly re-orders field slots |
| **D. Demo + evidence pack** | | Decision cards, replay, demo script, and checking every claim's tag | Every number on screen traceable to `[DATA]` / `[S-nn]` / `[ASSUMPTION]` |

### Cut-line if we run out of time
A + B ship; C degrades to a ranked list with a published budget cap; D never loses the **refusal ledger** — that is the submission's differentiator. Under no cut do we ship "we called an API".

---

## 5. The demo (8 beats)

1. The incumbent, warts and all — 51,105 calls, a constant trace trigger, ₹79,650 spent, 77% invisible waste.
2. One account's belief timeline — a third-party answer, a trace that kills a point, a payment that resets the state.
3. **A refusal with arithmetic** — we decline a ₹104 trace and a field slot, showing the EVSI computation and the counterfactual range.
4. The day plan — drop field slots 50 → 20 live: the shadow price moves, the plan re-orders, refusals change.
5. The replay — same events, new policy version (this is the argument for 1 Jan 2027 readiness).
6. One address's radius shrinking after an integrity-passing visit.
7. A **faked** check-in being rejected and *widening* the radius instead of moving the belief.
8. The honest slide — leakage 0.933 vs honest 0.670, the confounded arm, the cost table's ranges, what we refuse to claim.

---

## 6. Run things

The workspace is four tiers — `CreditNirvana_Submission/` (the deliverable), `10_Inputs/` (dataset, read-only),
`tools/` (scripts that reproduce and verify), `90_Archive/` (superseded drafts). Full map: `../../WORKSPACE.md`.

```bash
cd PS2_SANKET                   # or: cd PS3_SUTRA — the sibling section, same tooling

# 1. Reproduce every number this section quotes + regenerate its acceptance table
bash tools/reproduce.sh               # PS2 default: q p2 eco   |   PS3 default: q p3 eco
bash tools/reproduce.sh p2 eco        # selected audit sections only (PS3: p3)

# 2. Rebuild this section's zip and refresh the combined zip, then the manifest
bash tools/build_package.sh
python3 tools/build_manifest.py       # -> tools/section_manifest.csv

# 3. Invariant checks — must print ALL CHECKS PASSED before any hand-off
bash tools/check_section.sh

# 4. If this section's tables are ever missing (synthetic, 21 MB in total)
pip install gdown
gdown --folder "https://drive.google.com/drive/folders/18iqIR8TjXDqf9-hgEY34uJr_DraIl_3P" -O /tmp/cn_drive
# → flatten the subfolders into data/raw/*.csv ; ps1_fake_ptp → 90_Archive/ps1_fake_ptp_not_used/

# 5. The clickable demo prop (no server needed)
open SANKET_SUTRA_DEMO.html
```

The audit section meanings: `q` inventory · `p2` PS2 funnel, arm contrast, honest AUC, identity, trace waste ·
`p3` PS3 stratum error, free-data ceiling, integrity · `eco` trace ROI and the waste floor.

**Environment:** Python 3 + `pandas`, `numpy`. Scripts are path-portable (`$CN_DATASET`, `$CN_OUT`). The demo HTML needs no server.

---

## 7. Rules we do not break

**Never claim:**
- an uplift / incremental-effect number — the randomised arm is 5.4% of accounts, confounded, and *worse* than the incumbent (0.134 vs 0.166 RPC). No clean control exists, so no causal claim is licensed.
- a spoof-detection *rate* — we have no device telemetry, so we cannot measure recall.
- a market-size, market-share or "no competitor does X" claim without a named source.
- an accuracy or ROI figure from the synthetic dataset as if it were measured on reality: it is a **mechanism demo**, and the vendor-standard note is that real RPC "rarely exceeds 8–10%" (FICO), while our synthetic data sits at 16.4%.
- any single-point rupee number whose inputs are `[ASSUMPTION]` — every EV prints a **range**.

**Always:**
- tag numbers `[PUB]` / `[EXT]` / `[ASSUME]` / `[MODEL]` and claims `[VERIFIED]` / `[INFERENCE]` / `[ASSUMPTION]` / `[UNKNOWN]`.
- state the failure path of every action (timeout, partial, rejected, fallback, escalation).
- keep regulatory rules **hard and closed-vocabulary** (no fuzzy logic inside a legal gate), and keep policy parameters (thresholds, ceilings, budget) separate and owned.
- label any advanced idea with its class: `BUILD NOW` / `BUILD IF TIME` / `PRODUCTION` / `RESEARCH ONLY`. The 9 RESEARCH ONLY items and the 18 rejected alternatives are in `ARCHITECTURE_DECISION_LOG_FINAL.md` — each with the condition that would reverse it, so nobody has to re-litigate them.

---

## 8. What we still need from CreditNirvana (ask these first)

1. **Real cost and capacity table?** (agent minute, field slot, conduct cost; agent-hours, field slots, trace budget). This is the single biggest upgrade available: it promotes the day-level MILP allocator from *build-if-time* to the centrepiece.
2. **Do they hold visit-level GPS** (per-point accuracy, dwell, outcome) historically? If not, PS3 loses its learner and becomes a gate-and-radius product.
3. **Do they hold point-level call dispositions and the incumbent policy's attempt log?** If not, PS2 cannot benchmark and ships as the identity gate + EV gate.
4. **The real ticket band of the pilot portfolio.** Below roughly ₹13–15k, field actions stop being self-funding.
5. **Which recovery rules will bind at pilot time** — the RBI Amendment Directions take effect **1 Jan 2027** (08:00–19:00, ≥1-day pre-visit notice, ≥6-month recording, empanelled agencies, IIRB-certified agents, device-locking 30/60 days).

Full ranked list (34 questions) in `CN_QUESTIONS.md`.

---

## 9. Reading order by role

| You are | Read |
|---|---|
| **Building PS2** | `../PS2_SANKET/PS2_SANKET_SOLUTION_ARCHITECTURE_FINAL.md` (§6–§19, §29) → `../PS2_SANKET/PS2_ARCHITECTURE_SELECTION.md` → audit `p2` + `eco` |
| **Building PS3** | `PS3_SUTRA_SOLUTION_ARCHITECTURE_FINAL.md` (§6–§13, §29) → `PS3_ARCHITECTURE_SELECTION.md` → audit `p3` |
| **Doing the integration / demo** | `SANKET_SUTRA_SYSTEM_ARCHITECTURE_FINAL.md` → `FRONTIER_PS2_PS3_ARCHITECTURES.md` |
| **Presenting it** | `CreditNirvana_PS2_PS3_MASTER.md` Part I → `HOW_TO_USE_AND_UNDERSTAND_THIS_PACKAGE.md` §10 → demo script §5 above |
| **Arguing with judges / answering "why not RL?"** | `ARCHITECTURE_DECISION_LOG_FINAL.md` (31 decisions, each with a reversal condition) |
| **Checking our numbers** | `PS2_PS3_DATASET_REVIEW.md` §11 + run the audit yourself |

---

## 10. Before you send this to anyone outside the team

- The **synthetic dataset** ships inside each section (`data/raw/`, 21 MB in total, identical across the two where the table is shared) — so a forwarded folder is complete, and every number can be reproduced from it. It is synthetic: mechanism only, never magnitude.
- `ARCHITECTURE_RESEARCH_BIBLIOGRAPHY.md` honestly marks **six** sources as *URL unconfirmed* (captured with citation, URL not recorded). Resolve them to DOIs before external publication; nothing in the design depends on them being linkable.
- The MASTER document (Part XV) carries the Phase-4 files inline, so "the file to email" is still `CreditNirvana_PS2_PS3_MASTER.md`.
