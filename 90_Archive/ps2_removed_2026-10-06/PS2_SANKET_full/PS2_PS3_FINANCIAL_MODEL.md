# PS2 / PS3 — FINANCIAL MODEL

*Illustrative model, deliberately conservative, sensitivity-tested. Companion script: `financial_model.py` (run it: `python3 financial_model.py`); raw output: `financial_model_output.txt`.*

**Labelling used everywhere:** `[PUB]` published/claimed · `[EXT]` external data point · `[ASSUME]` our assumption · `[MODEL]` computed. **No number here measures CreditNirvana's actual portfolio.**

---

## 1. The three findings that changed our product scope

1. **Dial volume is not where the money is.** An automated dial costs **₹1.35–2.60**; a field visit costs **₹220–370**; a trace **₹60–150** `[MODEL]`. That is a **185× spread**. Any effort spent optimising dial volume is worth **₹0.3–7 lakh/month** on a 100,000-account book — i.e. nothing. *We deleted dial optimisation from the value story.*
2. **The economics are ticket-conditional.** Field-visit ROI: **0.65× marginal / 0.38× standalone at a ₹5,000 ticket**; **2.43× / 1.45× at ₹18,802**; **19× / 12× at ₹1.5 lakh**; **104× / 62× at ₹8 lakh** `[MODEL]`. A single story cannot cover a digital-PL book and a vehicle-finance book. *Deployment becomes segment-conditional.*
3. **Trace is a 30× uncertainty business.** Trace EV at the average ticket spans **₹7–204 per case** against a **₹60–150 fee** `[MODEL]`, driven by yield (35–60%) and RPC uplift of a new point (6–14 pp). *A rule cannot fire this correctly — which is exactly the problem statement's point, and it is also why our own trace claim must be modest.*

---

## 2. Cost structure of each action

| Action | Cost | Basis |
|---|---|---|
| Automated dial (voice-AI 60–75 s, connect ~28%) | **₹1.35–2.60** | `[PUB]` India voice-AI ₹4–7/min + ₹0.55/min telephony; `[MODEL]` blend for non-connects |
| Human-agent dial | **₹8.48** | `[PUB]` agent salary ₹15,788/mo median (Indeed) + ~75% loading; `[ASSUME]` 3,300 dials/mo |
| HLR / number intelligence | **₹0.13–0.60** | `[PUB]` Telnyx $0.0015/dip; Neutrino $0.007; Twilio $0.005–0.04 |
| SMS / WhatsApp utility | **₹0.15–0.25** | `[PUB]` WhatsApp utility pricing |
| Skip-trace (data purchase) | **₹60–150** | `[EXT]`-anchored: global bulk $5–25/record; US one-off $50–175 |
| Field visit — **marginal** (on an existing beat) | **₹220** | `[MODEL]` ₹130 labour + ₹90 travel |
| Field visit — **standalone trip** | **₹370** | `[MODEL]` ₹130 labour + ₹240 travel |
| Voice-AI per resolved outcome | ₹8–25 | `[PUB]` India outcome-based pricing |

**Cost per RPC:** ₹5–14 automated (₹9–24 per *productive* RPC at 60% paying) · **₹32–47 per RPC on a human call** `[MODEL]`. A human call is **4–8× the cost of an automated connect** — which is why human minutes, not dials, are the scarce resource worth optimising.

---

## 3. Value pools (monthly, 100k accounts / ₹188 Cr book at ₹18,802 ticket `[PUB]` FACE, 1–30 DPD)

| Pool | Monthly value | Note |
|---|---|---|
| **VP-1 Dial-volume optimisation** | **₹2,700–25,900** | Listed first *so that nobody funds it*. 1–5 pp of dials avoided |
| **VP-2 Scarce-capacity arbitrage** — field slots | **₹9.4–42.4 lakh** | 6,600 slots/mo `[ASSUME]`; +10–45 pp slot-level success from better address confidence + timing |
| **VP-2b** — human-agent conversations | **₹3.4–14.7 lakh** | 33,000 conversations/mo `[ASSUME]`; +5–12 pp RPC × ₹205 incremental recovery per RPC |
| **VP-3 Wasted expensive actions** | **₹1.5–8.6 lakh** | 10–35% of field slots spent on wrong-door / low-confidence addresses |
| **VP-4 Conduct exposure** | see §5 | Bounded, probabilistic, and the pool a CFO funds without an ROI debate |
| *(reference)* 1 pp of connect rate | **₹5.01 lakh** | `[MODEL]` at ₹205 incremental recovery per RPC |

---

## 4. Incremental recovery per RPC — the assumption that decides everything

```
E[gross recovery | RPC] = P(pay | RPC)     0.20–0.30   [ASSUME]
                        × payment fraction 0.20–0.30   [ASSUME]
                        × ticket           ₹18,802     [PUB]
                        = ₹752 – ₹1,692  (mid ₹1,183)
E[INCREMENTAL recovery | RPC] = gross × incrementality 0.20–0.35  [ASSUME]
                             ≈ ₹205 at the midpoint
```
**Why we use the incremental figure:** most 1–30 DPD accounts that pay would have paid anyway (15–25% self-cure `[EXT]` vendor-published). Using gross recovery inflates every benefit by ~4×. **If CN has better numbers, this single assumption changes the model more than any other** — it is question B1 in `CN_QUESTIONS.md`.

---

## 5. Conduct exposure (the part a lender funds without argument)

| Element | Value | Source |
|---|---|---|
| FY24 RBI Ombudsman complaints (loans/recovery) | **85,281**, +42.7% YoY, ≈29% of all complaints | `[PUB]` |
| Harassment/mental-anguish compensation cap (RB-IOS 2026) | **₹3,00,000** (was ₹1,00,000); 90-day filing window | `[PUB]` |
| Lender penalty precedent | **₹2.5 crore** against Bajaj Finance for agent conduct — the **lender** pays | `[PUB]` |
| Our model | 5% of dials reach a wrong party; 0.2–1.0% of those escalate at ₹15k–75k expected cost → **₹3–75 lakh/month** on a 100k book | `[MODEL]` |

**Framing rule:** call this *avoided exposure*, never "savings". The lumpy ₹2.5 crore penalty class dwarfs the compensated amounts, which is why the budget is defensible even though the expected value is bounded.

---

## 6. Trace and visit ROI by ticket size

| Ticket | Visit ROI (marginal) | Visit ROI (standalone) | Trace EV (vs ₹60–150 fee) |
|---|---|---|---|
| ₹5,000 | 0.65× | 0.38× | ₹2–54 → **negative** |
| **₹18,802 (digital-PL average)** | **2.43×** | 1.45× | ₹7–204 → **indeterminate** |
| ₹50,000 | 6.47× | 3.85× | ₹18–541 → positive if yield is good |
| ₹1,50,000 | 19.4× | 11.6× | ₹54–1,624 → positive |
| ₹8,00,000 | 103.6× | 61.6× | ₹289–8,663 → clearly positive |

**Decision consequence:** in small-ticket books, both visits and traces must be priced per account and, for visits, evaluated **marginally to an existing beat**. In large-ticket books, the discipline is route efficiency, not go/no-go.

---

## 7. Break-even at a price

One percentage point of connect rate is worth **₹5.01 lakh/month** on this book `[MODEL]`.

| Price | Monthly cost | Improvement needed |
|---|---|---|
| ₹1 / account / month | ₹1.0 lakh | **+0.20 pp connect**, or ~**455 avoided field visits/month** |
| ₹3 / account / month | ₹3.0 lakh | +0.60 pp connect, or ~1,364 avoided visits/month |
| ₹5 / account / month | ₹5.0 lakh | +1.00 pp connect, or ~2,273 avoided visits/month |

**This is the most important number in the deck.** The product does not need a heroic claim — it needs a **demonstrable** one. If we cannot show avoided expensive actions and avoided exposure on real accounts, no model quality will save the ROI story.

---

## 8. Which decision produces the largest financial impact?

| Rank | Decision | Value per pp | Why it ranks here |
|---|---|---|---|
| 1 | **P(pay \| RPC)** — offer/agent/script | ₹7.4 L/month per pp | Largest, cheapest lever — **and it belongs to CN's existing Maestro layer. We must not claim it** |
| 2 | **Connect rate** via timing/contact point | ₹5.0 L/month per pp | Ours, but shared with every dialer vendor's claim |
| 3 | **Identity gate** (right-party share + avoided conduct) | ₹2.0 L/month per pp *plus* avoided exposure | Ours, defensible, compliance-anchored |
| 4 | **Field-slot success** | ₹0.94 L/month per pp | Ours via PS3; small per pp but directly controllable |
| 5 | **Trace yield** | ₹0.01 L/month per pp | Small per pp; the win is *avoided negative-EV traces*, not yield |

**Answer to "which decision moves the most money":** *the offer layer does — which is why we do not touch it.* Within what is defensibly ours, the biggest movers are **connect timing, the identity gate and field-slot quality**, and all three are best expressed as **avoided waste and avoided exposure on expensive actions**.

---

## 9. What the model cannot tell us (stated plainly)
- Whether CN's portfolio looks like this book (ticket, DPD mix, field intensity) — **unknown**.
- Whether field visits are frequent enough to train an address learner in the target segment — **unknown, and material to PS3**.
- Whether the trace fee in India is ₹60–150 (**our estimate**), and whether vendors charge per hit or per query.
- The true incremental-recovery-per-RPC — the single biggest swing factor.
- Anything about borrower-experience cost (complaints, NPS, attrition), which we have deliberately left out of the ROI rather than invent.

**Pilot counters we would pre-register (30 days, one region):** field-slot yield · standalone-trip share · notices blocked below confidence · traces ordered and their realised yield · wrong-party contacts · complaints · cost per RPC · cost per productive RPC · cure/roll-back rate in bucket.
