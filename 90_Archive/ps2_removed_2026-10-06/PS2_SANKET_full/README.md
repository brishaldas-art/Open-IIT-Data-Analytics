# CreditNirvana — PS2 + PS3 · Complete Deliverables

**Prepared by:** the CreditNirvana hackathon team
**Scope:** Right-Party Contact Prediction & Skip-Trace Prioritisation (PS2) · Self-Learning Address Geocoder (PS3)
**Last updated:** 6 October 2026 (divided strictly into two sections, PS2 and PS3; Phase 4 architecture inside)

---

## How this folder is divided

**Two sections, and this is one of them.** The whole workspace is split by problem statement — `PS2_SANKET/` and
`PS3_SUTRA/` — so each half can be handed to one owner and read end to end, with no third bucket and no file that
belongs to neither.

| Section | Holds | Start with |
|---|---|---|
| **`PS2_SANKET/`** | Everything that defines, researches, scores or specifies **PS2** — assumptions, deep research, requirements, 12 architectures compared, 7 options scored, the selection, the final 30-section design, the Phase-2 hypothesis (marked SUPERSEDED) at the section root, the section's own tables in `data/raw/`, its acceptance table in `data/derived/`, and its tools | `README_PS2_SANKET.md` |
| **`PS3_SUTRA/`** | The same for **PS3** — 15 architectures compared, 7 options scored, the selection, the final 30-section design, the SUPERSEDED hypothesis, `data/raw/`, `../PS3_SUTRA/data/derived/derived_ps3_radius_calibration.csv`, `tools/` | `README_PS3_SUTRA.md` |

**The joint material lives in both sections.** The master document, the Phase-1 research, the strategy work, the
integrated architecture, the cross-PS research and the dataset review are needed by PS2 and PS3 alike, so each
section carries its own copy — same words, section-relative links. The only files that must be **byte-identical**
across the two sections are the three tables both designs read: `accounts.csv`, `addresses.csv` and `field_visits.csv`
(`cmp` them any time). There is no shared folder to keep in sync; **if you edit a duplicated document, edit both copies.**

Plus three front-door files at the top of each section: this README, `HOW_TO_USE_AND_UNDERSTAND_THIS_PACKAGE.md`
(the manual, six acts) and `START_HERE_TEAM_HANDOFF.md` (the teammate brief). The only thing that sits outside both
sections is `90_Archive/ps1_fake_ptp_not_used/` — four tables from a third problem statement that neither design uses.

---

## Start here

> **On the team, and about to build?** Read **`START_HERE_TEAM_HANDOFF.md`** — the idea in 90 seconds, what is binding
> versus history, the five numbers that carry the argument, the 48-hour workstreams, the demo beats, the claims we must
> never make, and the commands that reproduce every figure.
>
> **New to this package?** Read **`HOW_TO_USE_AND_UNDERSTAND_THIS_PACKAGE.md`** first — it explains the structure, the
> ideas in plain language, how to read the evidence tags, how to drive the demo, and what is settled versus open.

| If you have… | Read this |
|---|---|
| **5 minutes** | `CreditNirvana_PS2_PS3_MASTER.md` → **Part I** (the whole answer in 20 numbered conclusions) |
| **30 minutes** | Part I, then `PS2_PS3_RESEARCH_SYNTHESIS.md` → **Part 25** (final research conclusion for PS2, PS3 and the integration) |
| **Owning PS2** | `README_PS2_SANKET.md` → `PS2_SANKET_SOLUTION_ARCHITECTURE_FINAL.md` → `PS2_ARCHITECTURE_SELECTION.md` |
| **Owning PS3** | `../PS3_SUTRA/README_PS3_SUTRA.md` → `../PS3_SUTRA/PS3_SUTRA_SOLUTION_ARCHITECTURE_FINAL.md` → `../PS3_SUTRA/PS3_ARCHITECTURE_SELECTION.md` |
| **The architecture, and why it is this one** | the two `*_ARCHITECTURE_SELECTION.md` files (the weighted decision), then the two `*_FINAL.md` designs, then `SANKET_SUTRA_SYSTEM_ARCHITECTURE_FINAL.md` |
| **The dataset we must build on** | `PS2_PS3_DATASET_REVIEW.md` — every table profiled, the baselines to beat, the 12 traps, and the requirement-by-requirement verdict |
| **A demo to watch** | `SANKET_SUTRA_DEMO.html` (open in a browser; synthetic data, labelled on screen) |
| **The single file to email** | `CreditNirvana_PS2_PS3_MASTER.md` — this one file already contains everything below it |

---

## How this body of work was produced, and how to read it

The work ran in phases, and **every later pass attacks the earlier one**. Nothing here is presented as settled: earlier designs are kept deliberately, because the newest research and the official dataset say which parts of them survive.

| Where it is now | What it is | Status |
|---|---|---|
| `CreditNirvana_PS2_PS3_Research_and_Strategy.md` / `.docx` | The original 16-section research → recommended solution (191 URLs) | **Research record.** Benchmarks and URLs still cited; its **design** is superseded |
| The strategy files (`CN_QUESTIONS.md`, `PS2_PS3_RED_TEAM.md`, `NOVELTY_MATRIX.md`, `PS2_PS3_MARKET_RESEARCH.md`, `PS2_PS3_FINANCIAL_MODEL.md`, `PS2_PS3_DATA_STRATEGY.md`, `HACKATHON_EXECUTION_PLAN.md`) | Competitor map, red team, novelty matrix, financial model, data strategy, questions for CN, execution plan | **Current** |
| The cross-PS research files (`SIMILAR_SYSTEMS_REVERSE_ENGINEERING.md`, `ARCHITECTURE_DECISION_LOG_FINAL.md`, `ARCHITECTURE_RESEARCH_BIBLIOGRAPHY.md`, `PS2_PS3_RESEARCH_SYNTHESIS.md`, `PS2_PS3_SOURCE_BIBLIOGRAPHY.md`) | The evidence pass and the reverse-engineering pass: how 24 real systems are built, and the 31 decisions with their reversal conditions | **Current** |
| `PS2_PS3_DATASET_REVIEW.md` + `data/raw/` + `tools/dataset_audit.py` | The official synthetic dataset profiled against both PSes: what it supports, what it refutes, the baselines to beat, the 12 traps, the reproducible audit | **Current — the acceptance numbers** |
| `PS2_*_FINAL.md`, `PS3_*_FINAL.md`, `SANKET_SUTRA_SYSTEM_ARCHITECTURE_FINAL.md` | The Phase-4 rebuild: 12 + 15 architectures compared, 7 + 7 options scored, weighted selections, then the final 30-section designs and the integration | **Newest and binding** |
| `FRONTIER_PS2_PS3_ARCHITECTURES.md`, `PS2_PS3_INTEGRATED_PRODUCT.md` | The frontier list (every idea labelled BUILD NOW / BUILD IF TIME / PRODUCTION / RESEARCH ONLY) and the product definition | **Newest and binding** |
| `financial_model.py`, `financial_model_output.txt`, `SANKET_SUTRA_DEMO.html`, `tools/` | The financial model, the clickable demo prop, and every script that regenerates the numbers | Supporting artefacts |
| `_superseded/` and the two `*_SOLUTION_ARCHITECTURE.md` hypotheses at the section roots | Earlier passes: the Phase-2 designs and the intermediate files | **History, deliberately kept.** Nothing here is our current position |

**Honesty rules applied throughout — please hold us to them:** every number is tagged `[PUB]` (published/vendor-claimed), `[EXT]` (external data point), `[ASSUME]` (ours) or `[MODEL]` (computed); sources are tagged `[VERIFIED]` / `[INFERENCE]` / `[ASSUMPTION]` / `[UNKNOWN]`; synthetic data is labelled wherever it appears and is never presented as measured performance; no market gap is claimed without a named competitor; no compliance is claimed merely because a log exists.

---

## File index

### This section — `PS2_SANKET/`
| File | Contents |
|---|---|
| `README_PS2_SANKET.md` | Section brief: what PS2 is, reading order, the numbers, build scope |
| `PS2_DEEP_INTERNET_RESEARCH.md` | What PS2 actually is once the literature is checked: contact-intelligence landscape, six next-best-action approaches, selection bias, the economics of each action, Indian regulation, competitor capabilities |
| `PS2_ASSUMPTIONS.md` | PS2 re-read from scratch: the 11 questions + assumption register A1–A25 with compliance citations |
| `PS2_ARCHITECTURE_REQUIREMENTS.md` | The MUST / SHOULD / MAY checklist the design has to satisfy, each item tied to "what it changes in the collection workflow" |
| `PS2_ADVANCED_ARCHITECTURE_RESEARCH.md` | Twelve genuinely different architectures compared, each with data needs, cold start, interpretability and failure modes |
| `PS2_ARCHITECTURE_OPTIONS.md` | Seven buildable options, scored, with the evidence table that decides them |
| `PS2_ARCHITECTURE_SELECTION.md` | The weighted decision, the worked arithmetic, the rejected alternatives, the risk register and the cut-line |
| `PS2_SANKET_SOLUTION_ARCHITECTURE_FINAL.md` | **The PS2 architecture — 30 sections:** state model, evidence fusion, prediction + leakage guard, calibration table, rulebook, EV/EVSI/CVaR, allocator with shadow prices, failure paths, event sourcing, data mapping, build plan |
| `PS2_SANKET_SOLUTION_ARCHITECTURE.md` | The Phase-2 hypothesis (25 sections) | **SUPERSEDED** — kept at the section root as the reasoning record; the `*_FINAL.md` file replaces it |
| `data/raw/` | This section's **eleven** tables + the original `DATASET_README.md` + `README_DATA_PS2.md` (what each table is, and the traps inside it) |
| `data/derived/derived_ps2_policy_baselines.csv` | The acceptance table: the incumbent, the dead-streak rule, the cold-start policy |
| `tools/` | `dataset_audit.py` (`q\|p2\|eco`) · `build_derived_table.py` · `reproduce.sh` · `check_section.sh` · `check_links.py` · `build_manifest.py` · `build_package.sh` · `financial_model.py` + its output |
| `_superseded/` | 32 historical drafts — both PSes' earlier material, intermediate versions and the pre-division audit script |

### The sibling section — `../PS3_SUTRA/`
| File | Contents |
|---|---|
| `README_PS3_SUTRA.md` | Section brief for the other half: reading order, numbers, build scope |
| `PS3_SUTRA_SOLUTION_ARCHITECTURE_FINAL.md` | The other 30-section design |
| `../PS3_SUTRA/data/derived/derived_ps3_radius_calibration.csv` | The radius table PS3 must output |
| `data/raw/` · `tools/` · `_superseded/` | The other section's tables, tools and history |

### Duplicated in both sections — the joint material
| File | Contents |
|---|---|
| `CreditNirvana_PS2_PS3_MASTER.md` | **The complete deliverable in one file:** Part 0 team handoff · Part I the 20 conclusions · Parts II–XIII strategy and both hypotheses · Part XIV dataset review · Part XV all 13 Phase-4 files |
| `CreditNirvana_PS2_PS3_Research_and_Strategy.md` / `.docx` | The original research + recommended solution (191 URLs) |
| `CN_QUESTIONS.md` · `PS2_PS3_RED_TEAM.md` · `NOVELTY_MATRIX.md` · `PS2_PS3_MARKET_RESEARCH.md` · `PS2_PS3_FINANCIAL_MODEL.md` · `PS2_PS3_DATA_STRATEGY.md` · `HACKATHON_EXECUTION_PLAN.md` | Strategy: 34 ranked questions, 36 adversarial questions, the novelty matrix, the competitor map + 12-persona board, the money model, the data plan, the execution plan |
| `SANKET_SUTRA_SYSTEM_ARCHITECTURE_FINAL.md` | The joint belief state, the two contracts, and the one genuinely joint decision (trace vs visit) |
| `FRONTIER_PS2_PS3_ARCHITECTURES.md` | Every frontier idea labelled BUILD NOW / BUILD IF TIME / PRODUCTION / RESEARCH ONLY |
| `PS2_PS3_INTEGRATED_PRODUCT.md` | The integrated product definition + demo storyboard |
| `SIMILAR_SYSTEMS_REVERSE_ENGINEERING.md` | 24 systems, 12 tear-downs, 7 patterns |
| `ARCHITECTURE_DECISION_LOG_FINAL.md` | 31 ADRs + 18 rejected alternatives, each with its reversal condition |
| `ARCHITECTURE_RESEARCH_BIBLIOGRAPHY.md` · `PS2_PS3_SOURCE_BIBLIOGRAPHY.md` | Every `[S-nn]` with URL and status · ~90 sources with what each proves |
| `PS2_PS3_RESEARCH_SYNTHESIS.md` | The research synthesis, including Part 25, the final conclusion |
| `PS2_PS3_DATASET_REVIEW.md` | The full review: 11 sections, 12 traps, requirement verdicts, MVP acceptance numbers |
| `SANKET_SUTRA_DEMO.html` | The clickable prop; synthetic data, labelled on screen |
| `README.md` · `HOW_TO_USE_AND_UNDERSTAND_THIS_PACKAGE.md` · `START_HERE_TEAM_HANDOFF.md` | This index · the manual (six acts) · the teammate brief |

**Duplication rule:** every file in this last table exists **twice**, once per section, with the same words and
section-relative links. The three tables both designs read (`accounts.csv`, `addresses.csv`, `field_visits.csv`) are
byte-identical copies — verify with `cmp`. Change one copy of a document, change the other.

---

## The conclusions in brief

1. **The problem is permission, not prediction.** Both problem statements are about deciding what a collections platform may *do* with a prediction. TransUnion, Spocto, Credgenics, Mobicule, Shiprocket and Delhivery already sell the prediction layers.
2. **The new legal obligation creates the demand.** RBI's recovery Directions (issued 6 Aug 2026, **effective 1 Jan 2027**) require at least one day's notice before the first recovery visit, restrict contact to 08:00–19:00 and to the borrower/guarantor, and require a recorded, board-approved process. RBI judges whether the **system permitted** the conduct — so a log is not a defence; an eligibility gate is.
3. **Address intelligence is commoditised; address *permission* is not.** Shiprocket learns from delivery outcomes; Delhivery returns address verification against 4B+ deliveries. What none of them does is refuse a legally-required notice because confidence is too low.
4. **Google's terms settle the storage design.** Geocoding coordinates may be cached only 30 days — so a stored address belief must be built from our own field evidence, never a cache of vendor coordinates.
5. **Three models is one too many.** The deployed literature uses **one learned value function inside a rules engine** (4–6% higher collection rate with ~40% fewer calls, agency deployment). Collapse PS2 to one multi-class outcome model plus a hard rules floor.
6. **Integrate, but narrowly** — only through the eligibility filter, and only for irreversible actions (notice, doorstep visit, legal escalation), because the doorstep action is the only one that needs both an identity judgement and a location judgement, and the field visit is the only observation that improves the location judgement.
7. **Lead with refusals.** Refusals are the product: an action absent from the candidate set, with the rule that removed it, in the same record that proves the action was allowed.
8. **Three facts decide everything, and all three are checkable in one conversation with CN:** does CN hold visit-level GPS; does it hold point-level call dispositions; and what is the real ticket band of the pilot portfolio. If any is missing or uneconomic, the design degrades in a stated, planned way rather than a silent one.
9. **The architecture is reverse-engineered from real systems, not invented (Phase 4).** Experian, FICO, Pega, TransUnion and the NYS tax department all converge on the same five layers — **state → prediction → rules → constrained optimization → feedback** — and the one publicly reported value (+8% collections on the same resources, operator-reported) came from the *allocation and constraint* layers, not from model accuracy. SANKET is built as those layers, with a refusal ledger as its primary artefact and **EVSI** as the rule that stops us buying traces and visits that cannot change a decision. SUTRA's accuracy engine is the **field visit**, and its honesty engine is a **conformal, two-sample-validated radius**; the vendor geocoder stays, as a prior. See `SIMILAR_SYSTEMS_REVERSE_ENGINEERING.md` and the two `*_FINAL.md` designs.
10. **The dataset confirms the posture and kills three tempting shortcuts.** The randomised arm is 5.4% of accounts and *worse* than the incumbent, so no uplift claim is possible; skip-trace success is unpredictable (CV AUC 0.574), so prioritisation must be a rule with a named cost; and the commercial geocoder sits at the resolution ceiling of the free data (376 m vs an oracle-best 370 m), so PS3's deliverable is the **learning loop** — field visits move an address from 385 m to 29 m — plus an honest radius. See `PS2_PS3_DATASET_REVIEW.md`.

---

## Notes for whoever receives this package

- **One file is the whole package at lower granularity:** `CreditNirvana_PS2_PS3_MASTER.md` contains every other `.md` here, minus the `.docx`, the model script and the demo. Use the MASTER file to send; use the sections to work.
- **The demo is a prop, not a result.** It runs on synthetic cases and says so on screen. No number in it is a measurement.
- **The financial model is illustrative and tagged as such.** It is a decision tool with named assumptions and sensitivity — not a claim about any real portfolio.
- **Every dataset number is synthetic.** The dataset README says everything in it is invented. It validates mechanism — that a signal exists, that a failure mode is real — never magnitude.
- **The architecture has been rebuilt (Phase 4).** The two `*_FINAL.md` files in the PS sections are the design we build; the requirement files (`PS2_ARCHITECTURE_REQUIREMENTS.md`, `PS3_ARCHITECTURE_REQUIREMENTS.md`) and the dataset review (`PS2_PS3_DATASET_REVIEW.md`) are what they were rebuilt against. The Phase-2 hypotheses stay in the sections, marked SUPERSEDED, as the reasoning record.
- **What remains open is not design** — it is the four facts only CreditNirvana can supply (cost/capacity table, visit-level GPS, point-level dispositions, real ticket band) plus three data prerequisites (road graph, labelled address corpus, clean randomised pilot). Each is written as a reversal condition in `ARCHITECTURE_DECISION_LOG_FINAL.md`.
