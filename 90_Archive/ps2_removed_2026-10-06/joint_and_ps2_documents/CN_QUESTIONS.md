# CN_QUESTIONS.md — ranked questions for CreditNirvana

**Rule for this list:** every question is here because **the answer changes our architecture, our scope, or our ROI claim**. Questions we can answer ourselves from public sources are omitted. Nothing here is a sales question.

---

## Table A — Questions that can kill or reshape the design

| # | Q | Cat | Why it changes architecture |
|---|---|---|---|
| **1** | Which portfolio would this pilot run on — product, ticket band, DPD bucket, field-bearing or not — and what is the **actual average outstanding**? | DATA | Everything in §6 of the financial model is ticket-conditional. A digital-PL book (₹18.8k) and a used-car book (₹3–8 L) need different products; below ~₹15k, visits and traces stop being self-funding |
| **2** | **How many field visits per month, per collector-day, and what fraction are "standalone" trips** vs stops on an existing beat? | DATA | Determines whether per-visit ROI is marginal (₹220) or standalone (₹370) and whether the field learner has enough monthly volume to learn anything |
| **3** | What is **incremental** recovery per RPC (i.e. what would these accounts have paid anyway)? What is the current measured self-cure in the target bucket? | DATA | The single biggest swing factor in the model (§4). Without it every ROI number we publish is a guess |
| **4** | Of an identity-verified contact, what is the **right-party verification method today** (OTP, DOB, last-4, agent judgement), and what is the measured **wrong-party rate**? | DATA | The identity gate's threshold and the audit record both depend on it |
| **5** | Does CN already receive **call dispositions at contact-point level** (which number answered, at what time), and can that be modelled without changing the agent desktop? | DATA | PS2's core label needs point-level dispositions; if dispositions are account-level only, PS2 loses its best feature set |
| **6** | What **geocoder licence** does CN hold today (Google / Mappls / Ola / none), and what are the terms on **storing** returned coordinates? | DATA | Governs whether our runtime-only geocoding design is implementable, and whether we may persist coordinates at all |
| **7** | Does CN capture **GPS at the moment of the field visit**, with accuracy radius, dwell time, and a photo of the door/address? Can we read historical visit claims? | DATA | This is the *only* proprietary input that a commercial geocoder cannot have. If it does not exist, PS3 must be re-scoped to "geocode + notice gate", with no learning component |
| **8** | Which **field-workforce model** applies to the accounts we would pilot — own agents, empanelled agencies, or both? Who controls the mobile app the agent uses? | DATA | Determines whether an agent can be asked to confirm an address, and whether we can trust their claim (it is also the answer to "who is incentivised to fake a check-in") |

---

## Table B — Business questions

| # | Q | Cat | Why it changes the design |
|---|---|---|---|
| **9** | Is the commercial model **per account / per seat / per visit / outcome-based**? What has CN previously charged for a data product? | BUS | Sets the break-even target (§7). At ₹1–3/account the product must earn its keep on avoided visits alone |
| **10** | In the pilot region, what is the **cost per field visit** all-in, and is the marginal travel cost treated as free because agents already move through the beat? | BUS | Decides whether we optimise visits as go/no-go or as routing |
| **11** | Who signs off on **suppressing** a legal notice on modelled grounds? Does a credit officer or legal team have to approve a "do not serve notice" state? | BUS | Determines whether the notice gate is a hard block or an advisory flag — a compliance-driven product decision, not an ML one |
| **12** | Is there an existing SLA on notice delivery (e.g. within N days of bucket entry) that a blocked notice would **breach**? | BUS | If yes, the gate must propose an alternative (call/letter/e-mail) rather than simply refusing |
| **13** | What is CN's appetite for a **shadow-mode pilot** (recommendations logged, humans decide, no workflow change) for 2–4 weeks before anything is auto-suppressed? | BUS | Shadow mode is our lowest-risk proof and our fallback if CN's data is thinner than expected |
| **14** | Which single metric must improve for the pilot to be declared a success by CN's leadership — cost per productive contact, field-slot yield, complaint rate, or recovery in bucket? | BUS | Determines which of our two products leads the deck |

---

## Table C — Compliance questions

| # | Q | Cat | Why it changes the design |
|---|---|---|---|
| **15** | How is the **advance notice before the first field visit** (≥1 day by SMS/e-mail; 3 days by letter when applicable) currently generated, and from which address record? | COMP | That address record is precisely what PS3 must score; if it is the same field that the geocoder feeds, the gate is a small change with a large effect |
| **16** | For DPDP, are we acting as **Data Fiduciary or Data Processor** for the pilot data, and is consent collected at origination broad enough to cover geospatial inference and profiling? | COMP | Decides what we may store at all, and whether the "no cached commercial geocoder data" rule is about licence or about personal data |
| **17** | What does CN's **audit trail** currently record per action — the recommendation, the rule, the data snapshot, or only the human's decision? | COMP | Our whole compliance claim is "the constraint that permitted or blocked the action is recorded". If CN's log is decision-only, we must add a recommendation log, and that is a real engineering change |
| **18** | Has CN already had to defend an agent-conduct complaint where the system "permitted" a contact (e.g. hours, wrong party, repeat contact after a request to stop)? | COMP | If yes, the identity gate and the suppression gate become the product's spine rather than a feature |
| **19** | Are there **state-level** recovery-conduct or e-notice requirements (or a licence condition) beyond the central framework that apply to the pilot states? | COMP | May force state-conditional rules in the gate — cheap to add now, expensive to retrofit |
| **20** | What is CN's position on **recording and retention** under the new framework (≥6 months) — and would the geospatial evidence and integrity weights be considered part of the recovery record? | COMP | Determines retention design and whether the integrity weight must itself be auditable |

---

## Table D — Competition / positioning questions

| # | Q | Cat | Why it changes the design |
|---|---|---|---|
| **21** | Which of TransUnion / Spocto / Credgenics / Mobicule capabilities does CN **already resell or integrate**, and where does ours overlap? | COMP | We must position as a layer *between* predictors, not a replacement for any of them |
| **22** | Is Maestro's field module already geo-tagging visits and using that data for anything beyond proof-of-visit? | COMP | If yes, our PS3 learning loop is a fast follower, and we should lead with the **notice gate** instead |
| **23** | Would CN accept a design where the geocoder is called **at runtime and nothing is cached** — and does that pass their own security/procurement review? | COMP | It is our legal position for PS3; if rejected, the product must fall back to open data + field evidence, which is weaker |

---

## Table E — New questions raised by the dataset review (`PS2_PS3_DATASET_REVIEW.md`, 2026-10-06)

| # | Q | Cat | Why it changes the design |
|---|---|---|---|
| **24** | What is the **internal cost of a call attempt, an agent minute and a field visit** (wage + travel + fuel), and what **recovery value** do you use for a rupee recovered in each bucket? | ECON | The synthetic data has **no cost column at all** except skip-trace price (₹60–150). The EV gate (R5.1/R5.2) is therefore a parameter table with ranges until these arrive |
| **25** | Is there a **pre-visit notice record** in production, and is it machine-readable? | COMP | Notice-before-visit is a hard precondition from 1 Jan 2027 and there is **no notice field anywhere** in the dataset, so the gate can only be demonstrated as configuration |
| **26** | Where do **suppression states** (hardship, grievance, bereavement, DNC/preference, legal hold) live, and can they be exposed to a decision engine as a barrier list? | COMP | Absent from the data; they are hard barriers, not features (R1.6). Without them the gate's most important refusal is undemonstrable |
| **27** | Is there a **campaign, case or contact id** linking a payment to the contact that caused it? | DATA | 60% of payments in the data follow an RPC within 7 days and **none** are attributable; without an id no incrementality can ever be measured on real data (R1.5/R10.4) |
| **28** | How is **wrong-party contact** counted in production — disposition only, or a QA sample of calls? | DATA | In the data 6.9% of calls are third-party contacts, and 81–93% of recorded reference/employer points verify as third-party numbers. If production counts only dispositions, the true rate is unknown |
| **29** | What is the **real monthly call volume and field-force size**, and are there per-shift capacity limits? | DATA | 2,400 accounts / 30 agents cannot support capacity-constrained allocation (R5.4); the ≤60-minute portfolio pass (R9.2) is an unverified assumption |
| **30** | Do you hold **PIN-level polygons or a licensed administrative boundary source**? | DATA | The dataset has 36 locality centroids and no polygons; R5.2's PIN/locality candidate is a centroid + radius until this is answered |
| **31** | Which geocoder is **actually in production**, and under which **licence terms** (caching window, storage, display, model-training prohibition)? | COMP | The dataset ships a static baseline file with no vendor identity; R4.1–R4.5 (licence-aware storage) cannot be finalised without the vendor name and terms |
| **32** | Does the field app record a **mock-location / rooted-device flag**, and are **inter-point timestamps** at speed resolution available? | DATA | R10.1's spoof detection is design-only here; the data gives accuracy, dwell and duplicates but no mock flag and no speed signal |
| **33** | Was **"15 consecutive failed contacts"** the real production trace trigger, or a simplification? | DATA | It is a constant in the dataset (zero variance), so "when to trace" cannot be learned from history — the trace decision must be modelled as a rule, not a policy learned from logs |
| **34** | For the 250 verified points: what was the **verification method** (OTP, DOB check, voice match, field confirmation), and is that method available in production? | DATA | The identity model's label quality, and therefore its AUC 0.899, depends entirely on how the label was produced |

---

## The five questions we would ask in the first 15 minutes of a hackathon mentor session
**Q1** (portfolio + ticket band) · **Q7** (is visit GPS captured historically) · **Q3** (incremental vs gross recovery) · **Q15** (how the advance notice is generated today) · **Q17** (what the audit trail records).

Those five answers decide (a) which product leads, (b) whether PS3 has a learning loop at all, (c) whether our ROI is credible, and (d) whether the compliance story is a small change or a rebuild.
