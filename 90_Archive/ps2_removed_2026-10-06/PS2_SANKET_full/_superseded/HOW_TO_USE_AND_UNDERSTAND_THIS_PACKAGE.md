# How to use and understand this package

**CreditNirvana PS2 + PS3 — a reader's guide to the folder, the ideas, and the evidence behind them.**

This file is the manual. Read it once, then never read it again — everything else in the folder is what you'll actually work with.

---

## 1. What this package is, in 60 seconds

We were given two problem statements from CreditNirvana:

- **PS2** — predict right-party contact and prioritise skip-trace actions.
- **PS3** — geocode descriptive Indian addresses, learn from field visits, output a location with a confidence radius.

We concluded, and then tested the conclusion against regulation, competitor products, the academic literature and Indian geodata, that **neither problem is really about prediction**. Both are about **permission**: deciding what a collections platform is *allowed to do* with a prediction, when the action is expensive and irreversible.

That gave us one product with two halves:

| Half | Problem | What it permits | Name we gave it |
|---|---|---|---|
| Identity | PS2 | **A disclosure-capable contact** — a call that reveals a debt to whoever answers | **SANKET** |
| Location | PS3 | **A legally-required notice and a doorstep visit** — an action that reveals a debt at an address | **SUTRA** |

The pitch in one sentence: *the actions that are irreversible are gated on evidence, the refusals are recorded with the rule that caused them, and the field evidence that unlocks a refusal is weighted so it cannot be faked into moving the belief.*

Three things make this package different from a normal hackathon submission, and you should know them before you read anything else:

1. **We attacked our own design twice.** The first architecture is in the folder, and it is *not* our current position. The second research pass changed specific decisions in it. Both are kept so you can see the reasoning, not just the answer.
2. **Every number is labelled.** Nothing is asserted as fact without a tag saying what kind of claim it is.
3. **Nothing is claimed that we could not defend to a compliance officer.**

---

## 2. The 5-minute tour

```
CreditNirvana_Submission/
├── README.md                               ← one-page index of the folder
├── HOW_TO_USE_AND_UNDERSTAND_THIS_PACKAGE.md   ← this file
├── 00_MASTER_DOCUMENT/
│   └── CreditNirvana_PS2_PS3_MASTER.md     ← EVERYTHING in one file (start here)
├── 01_Phase1_Baseline_Research/            ← the original research, now partly superseded
├── 02_Phase2_Strategy/                     ← assumptions, competitors, red team, money, data, questions
├── 03_Architecture_Hypotheses/             ← the first designs (hypotheses, not final)
├── 04_Evidence_Pass_Deep_Research/         ← the evidence pass + the requirement spec (most current)
├── 05_Model_and_Demo/                      ← runnable model + clickable demo
└── 06_Dataset_Review/                      ← the official dataset profiled, table by table (newest)
```

**The single most important fact about this folder:** `00_MASTER_DOCUMENT/CreditNirvana_PS2_PS3_MASTER.md` already contains every other `.md` file in the package. The subfolders exist so you can work file-by-file, and so you can see which pass produced which claim. If you only ever open one file, open the master and read **Part I**.

---

## 3. Reading paths — pick the one that matches your role and your time

| You are / you have | Read, in this order | Time |
|---|---|---|
| **A judge or a busy exec** | Master → Part I (20 numbered conclusions) | 10 min |
| **The team, before a build** | Master → Part I, then `04/PS2_PS3_RESEARCH_SYNTHESIS.md` §25 (final conclusions), then the two requirement files | 45 min |
| **An ML engineer** | `04/PS2_ARCHITECTURE_REQUIREMENTS.md` + `04/PS3_ARCHITECTURE_REQUIREMENTS.md`, then `04/PS2_PS3_RESEARCH_SYNTHESIS.md` §19–23 (red team + component choices) | 60 min |
| **A PM or product owner** | `02/PS2_ASSUMPTIONS.md`, `02/PS3_ASSUMPTIONS.md`, `02/PS2_PS3_INTEGRATED_PRODUCT.md` (in `03/`) | 40 min |
| **A CFO or business reviewer** | `02/PS2_PS3_FINANCIAL_MODEL.md`, then run `05/financial_model.py` and change one assumption | 30 min |
| **A compliance officer** | Master → Part I items 9 and 12, then `02/PS2_ASSUMPTIONS.md` §1.7, then `04/PS2_DEEP_INTERNET_RESEARCH.md` §6 | 40 min |
| **Someone who just wants the demo** | `05/SANKET_SUTRA_DEMO.html` — open it and follow §7 of this file | 5 min |
| **Someone who will present it** | §10 of this file, then Master → Part I | 20 min |
| **The team, before writing code** | `06_Dataset_Review/PS2_PS3_DATASET_REVIEW.md` §8 (the 48-hour MVP with acceptance numbers) and §5 (the twelve traps), then run `python3 06_Dataset_Review/dataset_audit.py` | 30 min |
| **A reviewer who doubts our numbers** | `06_Dataset_Review/PS2_PS3_DATASET_REVIEW.md` §11, then run the audit script yourself — every figure in the review is reproducible | 15 min |

---

### Act 5 — the data answers back (folder 06)

Everything above was reasoned from published evidence. Then the official dataset arrived, and it was reviewed table by table. Act 5 is short because it is decisive — it **confirms the posture and kills three shortcuts**:

| Tempting shortcut | What the data says | What we do instead |
|---|---|---|
| "Show a measured uplift from the model" | The randomised arm is **5.4%** of accounts, is confounded, and performs **worse** than the incumbent (13.4% vs 16.6% RPC) | Benchmark against the incumbent's realised behaviour; no uplift language anywhere |
| "Predict which skip-traces will hit" | Predicting trace success gives CV AUC **0.574** against a 0.772 majority baseline; **77% of trace spend found nothing** | An EVSI rule with the ₹104 price as a named parameter, and a visible "refuse the trace" output |
| "Beat the commercial geocoder on accuracy" | The baseline is at the resolution ceiling of the free data (376 m vs an oracle-best 370 m from candidates), and naive landmark snapping is 4 km wrong | Sell the **visit-learning loop** (385 m → 29 m) and an **empirically calibrated radius** — the numbers the vendor does not give |

Act 5 does not change what we are building. It changes what we are allowed to *say*, and it hands the build its acceptance numbers: `06_Dataset_Review/derived_ps2_policy_baselines.csv` and `derived_ps3_radius_calibration.csv`.

---

## 4. How to understand the ideas — the four-act story

If you read the files cold, they look like a pile of documents. They aren't; they're one argument in four acts. Read them in this order and the reasoning is obvious.

### Act 1 — The problem as stated (folder 01)

We read PS2 and PS3 exactly as written and researched the field: what exists, what papers say, who sells what. The output was a full recommended solution with three calibrated model heads for PS2, a survival model, graph features, a parse→normalise→rank→conformal pipeline for PS3, and 191 sources.

**What it got right:** the research, the benchmark numbers, the URLs, and the observation that a landmark-based Indian address means you must output *a point plus a radius plus a route*, not a pin.

**What it got wrong:** almost everything about scope. It was twelve models and three dashboards, and its compliance story was "we log everything".

### Act 2 — The attack (folder 02)

We then tried to destroy it, as a collections head, a CFO, an ML lead, a compliance officer, a competitor and a judge. Thirty-six questions, every alternative design scored, a financial model built and then **rebuilt twice after it produced absurd numbers**, a data strategy, and 23 questions for CreditNirvana.

**The ideas that came out of this act and survive:**

- **The cost spread is the whole story.** An automated dial costs ₹1.35–2.60; a field visit costs ₹220–370. That is a **185× spread**, so optimising dial volume is worth almost nothing and deciding *whether to spend a field slot or serve a notice* is worth lakhs.
- **The economics are ticket-conditional.** A field visit returns 0.65× at a ₹5,000 ticket, 2.43× at ₹18,802, 104× at ₹8 lakh. One policy cannot cover a digital-loan book and a vehicle-finance book.
- **Use incremental recovery, never gross.** Most early-bucket borrowers who pay would have paid anyway, so multiplying gross recovery by contact volume overstates value by roughly 3.6×.
- **Refusals are the product.** Every decision we change is a *negative* one: a visit withheld, a notice blocked, a trace not ordered, a disclosure script replaced by an identity check.

### Act 3 — The design hypothesis (folder 03)

We wrote the two architectures as a hypothesis and an integrated product around one causal loop:

> A recovery notice or a doorstep visit is **irreversible** and now **legally regulated**. It requires a judgement about *whose door* it is (location) **and** *whose debt* is being revealed (identity). The only observation that improves the location judgement is the field visit itself. So the loop closes: **act → observe → reweight → permit or refuse next time.**

The demo lives here: a notice refused at 0.41 confidence, released at 0.78 after a verified visit, then a **fake check-in that widens the radius instead of moving the belief**.

### Act 4 — The evidence pass (folder 04) — *this is the current position*

We then went and checked whether the design was actually justified, using primary sources first: regulators, official API documentation, peer-reviewed papers, vendor documentation. Six files came out. Three findings changed the design materially:

1. **The deployed literature is lighter than our design.** The reference commercial deployment is a **Markov decision process with a LightGBM value function**, wrapped in a **rules engine that supplies the constraints** (Abe et al., KDD 2010, deployed at the New York State tax department). The agency deployment reports **4–6% higher collection rate with ~40% fewer calls** (van de Geer, PyData 2018). Conclusion: **cut PS2 to one multi-class outcome model plus a hard rules floor**, and drop the survival model until it beats a baseline.
2. **Google's terms decide PS3's storage design.** Geocoding coordinates may be cached for **only 30 days**, and stored indefinitely **only** to support direct end-user-facing display — and non-coordinate content may not be used with any map. So a stored address belief built from Google coordinates is a licensing problem, not a design preference. Conclusion: **consume the geocoder at runtime; build the belief from evidence you own.**
3. **Address learning from outcomes already exists commercially.** Shiprocket claims 72.69% of addresses within 100 m learned from delivery outcomes; Delhivery validates and verifies addresses against 4B+ deliveries. Conclusion: **our novelty is permission and integrity on *recovery* visits, not "learning addresses".**

Act 4 also produced the two files that matter most for the next phase: `PS2_ARCHITECTURE_REQUIREMENTS.md` and `PS3_ARCHITECTURE_REQUIREMENTS.md` — the checklist the rebuilt architectures must satisfy.

### The one thing to remember from all four acts

> **Prediction is commoditised. Permission is not. We are building the permission layer, and we can prove it refused.**

---

## 5. The core ideas, in plain language

Read this table before the research files; it is the vocabulary they assume.

| Term | Plain meaning | Why it matters here |
|---|---|---|
| **Right-party contact (RPC)** | Reaching the *borrower* — not just someone answering the phone | An answered call is not a lawful call. Disclosing a debt to a stranger is a conduct event |
| **Contact point / contact slate** | Each individual phone number or address on an account, as a separate object with its own source, age and history | You cannot predict "the contactability of an account". The unit is the *point* |
| **Candidate set** | The list of actions a system is *allowed* to choose from, built by rules before any model runs | The core compliance idea: an unlawful action is never *ranked*, it is never *in the list* |
| **Eligibility / permission gate** | The deterministic filter that puts an action into the candidate set only if its preconditions are met | This is the product. It is what makes the compliance claim architectural rather than aspirational |
| **`wait` / abstain** | An explicit "do nothing this week" option with its own expected value | Without it, a system that must produce an action will produce a harmful one |
| **Expected net recovery (ENRC)** | Probability × value − cost − expected conduct cost, for each eligible action | The ranking objective. Never P(success) alone — costs differ 185×, so probability alone picks the wrong action |
| **Incremental recovery per contact** | What a contact adds *over what would have happened anyway* | Gross recovery per contact overstates value ~3.6× because most early payers self-cure |
| **EVSI (expected value of sample information)** | What it is worth to *buy information* before deciding — e.g. pay for a skip-trace | Replaces "trace after three attempts" with "trace when the information is worth more than it costs" |
| **Selection bias / propensity** | The model can only learn from the actions the *old* system chose to take | Without the old policy's propensities, we learn collector behaviour, not contact health |
| **IPW (inverse propensity weighting)** | A standard correction that down-weights over-represented cases and up-weights rare ones | The honest way to train on logged collections data |
| **Shadow mode** | The system produces and logs decisions but humans still act | A zero-risk pilot, and the only way to produce a credible counterfactual without touching borrowers |
| **Off-policy evaluation (OPE)** | Estimating how a *new* policy would have performed on *old* logged data | Enables "your rule change would have saved 40 visits last month" without an experiment |
| **Radius_90** | The distance within which 90% of observed errors fell, computed per strata | The only honest location output. A bare pin is a lie about precision |
| **Integrity weight (w)** | How much a field observation is trusted, from dwell, accuracy, timing and device evidence | Fraud costs precision, not truth: a fake check-in *widens* the radius instead of moving the belief |
| **Purpose classification** | Is this place home-like, work-or-business-like, or unknown? | Serving a notice at a workplace exposes the debt to colleagues — which is exactly what the new rules prohibit |
| **Notice gate** | Whether a legally-required pre-visit notice may be issued for this address | The single new legal obligation that creates demand for PS3 |
| **Permission record / ledger** | An append-only record of the recommendation, the rule that permitted or blocked it, the data snapshot, and the human decision | "We log everything" is not compliance. "This action was never in the candidate set, and here is the rule that removed it" is |

### The idea in one diagram

```
   evidence                    prediction                    permission                 action
┌───────────────┐        ┌──────────────────┐        ┌────────────────────┐      ┌──────────────┐
│ call outcomes │──────▶ │ P(connect)       │──┐     │  ELIGIBILITY GATE  │      │ human call   │
│ identity check│        │ P(right party)   │  ├───▶ │  identity ≥ τ₁     │────▶ │ field visit  │
│ field visits  │──────▶ │ location belief  │──┘     │  address  ≥ τ₂     │      │ notice       │
│ (weighted)    │        │ + radius_90      │        │  purpose ≠ work    │      │ trace        │
└───────────────┘        │ + purpose        │        │  suppression clear │      │ WAIT         │
        ▲                └──────────────────┘        └────────────────────┘      └──────┬───────┘
        │                                                                            │
        └──────────────────────── outcome + rule fired, recorded ───────────────────┘
```

Models estimate. **Rules permit.** The record proves it.

---

## 6. How to read the evidence responsibly

Two tagging systems run through the files. Learn them and you will never be fooled by your own documents.

**Claim tags** — used in the research files:

| Tag | Meaning | How to treat it |
|---|---|---|
| `[VERIFIED]` | Directly supported by the source named next to it | Cite it as-is |
| `[INFERENCE]` | Our conclusion from two or more sources | Say "we concluded", not "it is proven" |
| `[ASSUMPTION]` | We still have to assume this | Say so out loud in any pitch |
| `[UNKNOWN]` | Insufficient evidence | Never fill this gap with a number |

**Number tags** — used in the model and the deliverables:

| Tag | Meaning |
|---|---|
| `[PUB]` | Published or claimed (often by a vendor — a claim, not a measurement) |
| `[EXT]` | An external data point |
| `[ASSUME]` | Our assumption |
| `[MODEL]` | Computed by our own model from the above |

**Three rules that follow from this:**

1. **No synthetic result is ever presented as measured performance.** The demo runs on synthetic cases and says `SYNTHETIC` on screen. Say it before anyone asks.
2. **Vendor claims are not facts.** TransUnion's ~25% RPC improvement, Spocto's ₹50,000 Cr saved, Skit's liquidation rates — all *vendor-stated*. Cite them as claims.
3. **A gap is not a market gap unless you name the competitors who don't fill it.** The file does that; do the same in conversation.

---

## 7. How to use the demo (`05/SANKET_SUTRA_DEMO.html`)

Open it in any browser — it is self-contained, needs no internet, and works offline.

**The click sequence, and what to say:**

1. **Case AC-8841 is selected.** Address confidence **0.41**, radius **1,400 m**. Press **"1 · Attempt to serve the 1-day advance notice"**.
   → Watch the verdict panel: the notice is **REFUSED**, with the rule `NOTICE_PRECHECK / ADDR_CONF_LOW` on screen. *Say: "The notice does not exist. That refusal is the product."*
2. **Press "2 · Field agent check-in at the landmark."** Landmark matched, 6 minutes dwell, photo matched, integrity weight **0.95**.
   → Confidence rises to **0.78**, radius falls to **90 m**, the notice is **RELEASED**, and the ledger now shows the evidence and the weight. *Say: "One verified observation moved a legal decision, and the record shows why."*
3. **Press "3 · A second check-in arrives, 6.1 km away."** No dwell, no photo, flagged device, weight **0.20**.
   → The belief **holds at 0.79** and the radius **widens to 520 m**; the visit is refused again. *Say: "Fraud can cost us precision. It cannot teach us the wrong door."*
4. **Now click AC-2210, then AC-3311.** Same connect probability (0.31) on both; P(right party) of 0.36 versus 0.88.
   → One account may receive a debt-disclosing call; the other may not. *Say: "Identical predicted value, opposite permitted actions. That is the identity gate."*

**What to be honest about while demoing:** the numbers are synthetic and the console says so; the demo proves the *mechanism*, the pilot proves the *measurement*.

---

## 8. How to use the financial model (`05/financial_model.py`)

Run it:

```bash
python3 financial_model.py > financial_model_output.txt
```

It has seven sections (S1–S7): cost structure · value pools · wasted expensive actions · conduct exposure · ROI by ticket band · break-even at a price · sensitivity. Every input is tagged.

**The three experiments worth doing in front of an audience:**

1. **Change the ticket size** from ₹18,802 to ₹5,000. Watch the field-visit ROI fall from 2.43× to 0.65×. *This is why the product must be segment-conditional.*
2. **Change the incrementality factor** (currently 0.20–0.35). It is the single biggest swing factor in the entire model. *This is question 3 for CreditNirvana.*
3. **Change the price** from ₹1 to ₹5 per account per month. Break-even moves from +0.20 pp of connect rate (or ~455 avoided visits) to +1.00 pp (or ~2,273 visits). *This is the honest size of the claim.*

**What the model will not do, and you must not pretend it does:** tell you anything about a real portfolio. It is a decision tool with named assumptions — not a measurement.

---

## 9. What is settled, what is open

**Settled (we would defend these):**
- The product is a permission layer, not a predictor.
- Eligibility is constructed by hard rules before any model runs.
- PS2 collapses to **one** outcome model plus the rules floor.
- PS3 does **not** build a geocoder, does **not** store vendor coordinates as its belief, and does **not** do routing.
- Integrate the two halves **only** through the eligibility filter, and only for irreversible actions.
- The radius is empirical and per-stratum; `unknown` is a first-class output.
- Field evidence is integrity-weighted: it widens uncertainty rather than shifting belief.
- Lead with avoided waste and avoided exposure — never gross recovery uplift.

**Open, and decided by three facts only CreditNirvana has:**
1. Does CN hold **visit-level GPS** (with accuracy, dwell, outcome) historically? If not, PS3 loses its learner and becomes a gate-only product.
2. Does CN hold **point-level call dispositions** and the **incumbent policy's attempt log**? If not, PS2 cannot claim lift and ships as the identity gate + EV gate.
3. What is the **real ticket band** of the pilot portfolio? Below roughly ₹13–15k, field actions stop being self-funding and the address half thins out.

These are questions 1, 3, 5, 7 and 15 in `02/CN_QUESTIONS.md`. Ask them before arguing about models.

---

## 10. If you are presenting this

**The 3-minute version:**

| Time | Say | Show |
|---|---|---|
| 0:00–0:30 | "Indian collections is governed by a rule that lands on 1 January 2027: no recovery visit without at least one day's notice. A notice is a disclosure. A wrong address is now a compliance event, not an inefficiency." | The RBI dates |
| 0:30–1:15 | "We don't predict better than TransUnion or Spocto — they sell that. We decide what the platform is *permitted* to do with a prediction." | The candidate-set diagram |
| 1:15–2:15 | "Here is a notice refused at 0.41 confidence, released after one verified visit, and here is a fake check-in that widens the radius instead of moving the belief." | The demo, beats 1–3 |
| 2:15–2:45 | "The money is avoided waste on expensive actions and avoided conduct exposure — ₹1–3 per account needs only +0.2 to +1.0 pp of connect, or 455–2,273 avoided visits." | The break-even table |
| 2:45–3:00 | "What would beat us is measurement, not cleverness — so the next step is a 30-day shadow pilot with counters pre-registered." | The counter list |

**The five questions you will be asked, and the honest answers:**

| Question | Answer |
|---|---|
| "Isn't this just a threshold with an audit log?" | Partly — and that is deliberate. Then show the widening behaviour and the identity gate: a threshold cannot be poisoned and cannot express *who* an action is permitted for |
| "TransUnion / Spocto / Credgenics already do this" | At the model level, yes. We compete at the permission level, with recovery-visit evidence and a regulator-facing record |
| "Shiprocket and Delhivery already learn addresses" | True — from deliveries. Our evidence is recovery visits under an integrity constraint, plus a legal gate they have no reason to build |
| "Where is the AI?" | A calibrated identity model, an integrity-weighted evidence model, a stratified uncertainty model, and a deliberate refusal to put a model where a rule belongs |
| "What if CN has none of the data?" | Then we say so and ship the identity gate alone, which applies to every portfolio. The design degrades in a stated way, not silently |

**Ten things not to say.** No "AI-powered". No "enterprise-grade". No "we increase recovery by X%". No "nobody has done this" (name the competitor instead). No "our model is 95% accurate" (on what population?). No "the audit log makes us compliant". No "we'll use an LLM to decide". No "we ramp up automatically". No "trust the model". No number without its tag.

---

## 11. Common misreadings, answered

**"So you're building a geocoder?"**
No. We buy geocoding at request time and build a *belief* from evidence a geocoder cannot have — our own field visits, weighted for integrity — and then use that belief to permit or refuse a legal action. Building a geocoder would fail: the Indian systems that beat Google use proprietary delivery corpora.

**"Isn't PS3 the weaker half?"**
It is the more *regulated* half. Its value is ticket-conditional: strong where field and legal actions exist, thin at an ₹18,802 average ticket. We say this in the deck rather than hiding it.

**"Why not a contextual bandit? Everyone uses one now."**
Because exploration in collections spends real borrower contacts and creates conduct exposure. The deployed literature itself wraps optimisation in hard constraints. We use bandit-style thinking *offline* (policy evaluation on logged data) and never as live exploration.

**"Why did you cut the survival model you spent so long on?"**
Because its published value comes from full MDP scheduling with volume and logged propensities, and it changes retest timing — worth roughly ₹94k per month per point of slot success in our own model. It stays as a sub-component until a measured lift test earns it back.

**"The financial numbers feel small."**
They are, deliberately. The honest pools are avoided waste (₹1.5–8.6 lakh/month) and avoided exposure (a ₹2.5 Cr penalty precedent exists). The biggest lever in the whole model is P(pay | RPC) at ₹7.4 L per point — and that belongs to CreditNirvana's own Maestro layer. Claiming it would be dishonest and would lose the room.

**"Which file is the actual submission?"**
`00_MASTER_DOCUMENT/CreditNirvana_PS2_PS3_MASTER.md`. Everything else is the working set behind it.

---

## 12. What happens next (so the folder doesn't go stale)

The two architecture files in `03_Architecture_Hypotheses/` are **hypotheses written before the evidence pass**. They are kept because the failure modes and the demo storyboard are still good, but they must be **rebuilt** against:

- `04/PS2_ARCHITECTURE_REQUIREMENTS.md` (PS2), and
- `04/PS3_ARCHITECTURE_REQUIREMENTS.md` (PS3),

with the divergences recorded in `04/PS2_PS3_RESEARCH_SYNTHESIS.md` §19–20 (red team) applied — **and now with the dataset review in `06_Dataset_Review/` as the third input**, which fixes the acceptance numbers, marks every requirement that has no data behind it, and re-weights three decisions (PS2: drop the trace-success model, promote the waste floor and the identity gate; PS3: promote the visit-learning loop and the radius calibration; PS2+PS3: the compliance layer stays configuration and refusal logs, because no data can prove it). That is the next deliverable: **two architecture files built from evidence, not from ambition.**

**And the first thing to do after that is not more modelling. It is asking CreditNirvana the five questions in §9 of this file.** If the answers are good, we build the integrated loop. If they are not, we build the identity gate, which stands alone, applies to every portfolio, and maps directly to a rule that takes effect on 1 January 2027.

---

*Addendum, 6 October 2026 — the official synthetic dataset has been downloaded, profiled end to end, and reviewed against both problem statements (`06_Dataset_Review/`). Every figure in that review is reproducible with one command. Nothing in it is a real measurement: the dataset says of itself that everything in it is invented, so it validates mechanism and never magnitude.*

*Honesty rules applied throughout this package: no invented facts; every number tagged `[PUB]` / `[EXT]` / `[ASSUME]` / `[MODEL]`; every source tagged `[VERIFIED]` / `[INFERENCE]` / `[ASSUMPTION]` / `[UNKNOWN]`; synthetic data labelled wherever it appears and never presented as measured performance; no market gap claimed without a named competitor; no compliance claimed merely because a log exists; no advanced model without a simpler baseline it had to beat.*
