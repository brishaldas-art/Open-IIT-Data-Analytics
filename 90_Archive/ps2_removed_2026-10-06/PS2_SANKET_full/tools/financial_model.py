#!/usr/bin/env python3
"""
CreditNirvana PS2/PS3 — unit-economics model v2 (illustrative, sensitivity-tested).

LABELS:  [PUB] public source | [ASSUME] our assumption | [MODEL] computed output
Nothing here measures CreditNirvana's actual portfolio.

v2 changes (v1 had three errors we caught in adversarial review):
  1. Wrong-party contact cost was applied to EVERY wrong-party dial. Fixed: P(escalates to a
     complaintable event) is a small conditional probability.
  2. "Value of reallocated attempts" assumed freed dials convert at portfolio-average rates and
     that dials are capacity-constrained. With Rs 1.35-2.6 automated dials, DIALS ARE NOT THE
     BOTTLENECK. Rebuilt around the actions that actually have material unit cost:
     human calls, field visits, traces, notices, legal - and around scarce HUMAN/FIELD capacity.
  3. Trace ROI was divided by a single fee, producing a fake-precise multiple. Rebuilt with
     ticket size as an explicit axis.
"""
def money(x):
    if abs(x) >= 1e7: return f"Rs {x/1e7:,.2f} Cr"
    if abs(x) >= 1e5: return f"Rs {x/1e5:,.2f} L"
    if abs(x) >= 1000: return f"Rs {x:,.0f}"
    return f"Rs {x:,.2f}"

ACCOUNTS, AVG_TICKET, ATTEMPTS_PA = 100_000, 18_802, 2.0   # [PUB] FACE/CRIF ticket Q1FY27; [ASSUME] rest

# --- how much recovery does one EXTRA right-party contact actually produce? -------------
P_PAY_GIVEN_RPC   = (0.20, 0.30)   # [ASSUME] pays within the cycle after being reached
PAY_FRACTION      = (0.20, 0.30)   # [ASSUME] fraction of outstanding paid in that cycle
INCREMENTALITY    = (0.20, 0.35)   # [ASSUME] share of those payments that would NOT have happened anyway
def incr_rec_per_rpc(ticket=AVG_TICKET):
    gross = sum(P_PAY_GIVEN_RPC)/2 * sum(PAY_FRACTION)/2 * ticket
    return gross * sum(INCREMENTALITY)/2, gross
INCR_RPC, GROSS_RPC = incr_rec_per_rpc()
print(f"[MODEL] gross recovery per RPC  = {money(GROSS_RPC)};  INCREMENTAL = {money(INCR_RPC)}  <-- used everywhere below")

print("="*100); print("S1 — WHAT ACTUALLY COSTS MONEY  (the scope decision)"); print("="*100)
rows = [
 ("Automated dial (voice-AI, 60-75s)", 1.35, 2.59,   "[PUB] India voice-AI Rs4-7/min + Rs0.55/min telephony"),
 ("Automated dial (human agent)",      8.48, 8.48,   "[PUB] Rs15,788/mo agent salary + loading / [ASSUME] 3,300 dials/mo"),
 ("HLR / number-intelligence lookup",  0.13, 0.60,   "[PUB] Telnyx $0.0015/dip; Neutrino $0.007; Twilio $0.005-0.04"),
 ("SMS / WhatsApp (utility)",          0.15, 0.25,   "[PUB] WhatsApp utility per-conversation price"),
 ("Skip-trace (data purchase)",        60.0, 150.0,  "[PUB-anchored] global bulk $5-25/record; India per-case higher"),
 ("Field visit, marginal (on an existing beat)", 220, 220, "[MODEL] Rs130 labour + Rs90 travel"),
 ("Field visit, standalone trip",      370.0, 370.0, "[MODEL] Rs130 labour + Rs240 travel"),
 ("Voice-AI, per resolved outcome",    8.0, 25.0,    "[PUB] per-outcome India pricing"),
]
print(f"{'action':<46}{'low':>10}{'high':>10}   source")
for n, lo, hi, s in rows:
    print(f"{n:<46}{money(lo):>10}{money(hi):>10}   {s}")
print("""
INSIGHT [MODEL-1]: the spread between a Rs 2 dial and a Rs 370 visit is 185x. Any optimisation
effort spent on automated dial VOLUME is economically trivial; the money is in the four actions
that carry material unit cost AND compliance exposure: HUMAN call, FIELD VISIT, TRACE, LEGAL/NOTICE.
=> PRODUCT SCOPE DECISION: SANKET/SUTRA govern the expensive, reviewable actions. We do NOT compete
   with a dialer on dial volume.""")

print("\n"+"="*100); print("S2 — UNIT METRICS: cost per RPC and per productive RPC"); print("="*100)
CONNECT, RPC_GIVEN = (0.26, 0.31), (0.70, 0.85)   # [PUB] NBFC unsecured connect; [ASSUME] right-party share
for label, cpd in (("automated low", 1.35), ("automated high", 2.59), ("human call", 8.48)):
    for cr, rg in zip(CONNECT, RPC_GIVEN):
        rpc = cr*rg
        print(f"  {label:<16} connect={cr:.0%} rightparty={rg:.0%} -> cost/RPC {money(cpd/rpc):>7} "
              f"| cost/productive-RPC @60% pay {money(cpd/(rpc*0.60)):>7}")
print("  => Range: Rs 6-11 per RPC automated, Rs 33-44 per RPC on a human call [MODEL]")

print("\n"+"="*100); print("S3 — VALUE POOLS (monthly, 100k-account / Rs188 Cr book, 1-30 DPD)"); print("="*100)

print("""
VP-1 · DIAL-VOLUME OPTIMISATION  ->  negligible. Deliberately listed first so nobody funds it.
""")
for pp in (0.01, 0.02, 0.05):
    wasted = ACCOUNTS*ATTEMPTS_PA*pp
    print(f"    {pp*100:.0f} pp of dials avoided = {wasted:>7,.0f} dials/mo = {money(wasted*1.35):>10} - {money(wasted*2.59):>9} / month [MODEL]")

print("""
VP-2 · SCARCE-CAPACITY ARBITRAGE  ->  the largest legitimate pool. Human agent minutes and field
       slots are the real constraint. Reallocating ONE field slot from a low-yield stop to a
       high-yield stop is worth the difference in expected recovery, not the travel cost.""")
FIELD_SLOTS = 300*22          # [ASSUME] 300 field agents x 22 days x 1 slot/day
for lo, hi in ((0.10, 0.25), (0.25, 0.45)):
    print(f"    {FIELD_SLOTS:,.0f} field slots/mo; +{lo*100:.0f}-{hi*100:.0f} pp slot-level success (better address confidence + timing)"
          f" -> {money(FIELD_SLOTS*lo*sum([0.35,0.50])/2*sum([0.25,0.40])/2*AVG_TICKET*0.55):>10}"
          f" - {money(FIELD_SLOTS*hi*sum([0.35,0.50])/2*sum([0.25,0.40])/2*AVG_TICKET*0.55):>10} / month")
HUMAN_AGENTS, TALKS_PER_DAY = 60, 25   # [ASSUME] 60 human agents; 25 conversations/day incl. wrap-up
TALKS = HUMAN_AGENTS*TALKS_PER_DAY*22
print(f"    {TALKS:,} human conversations/mo (60 agents x 25/day x 22d [ASSUME]); +5-12 pp RPC on these -> "
      f"{money(TALKS*0.05*INCR_RPC):>10} - {money(TALKS*0.12*INCR_RPC):>10} / month incremental recovery")
print("    (human calls are reserved for high-value accounts; this is the pool that pays for better targeting)")

print("""
VP-3 · WASTED EXPENSIVE ACTIONS  ->  real but bounded. Every field visit or trace fired on a wrong
       address / a recycled number is a ~100% loss, not a partial one.""")
for wastage in (0.10, 0.20, 0.35):
    print(f"    {wastage*100:.0f}% of field slots wasted on wrong-door/low-confidence addresses -> "
          f"{money(FIELD_SLOTS*wastage*220):>10} - {money(FIELD_SLOTS*wastage*370):>10} / month")
print("    NOTE: field slots assume a field-bearing portfolio (vehicle/MFI/consumer-durable/ARC).")

print("""
VP-4 · CONDUCT / COMPLAINT EXPOSURE  ->  the pool a CFO funds without an ROI debate.""")
P_ESC = (0.002, 0.010)        # [ASSUME] share of wrong-party contacts that escalate into a complaint
COMP  = (15_000, 75_000)      # [PUB] RB-IOS 2026 caps harassment at Rs 3,00,000; expected award far lower + officer time
wp_lo = ACCOUNTS*ATTEMPTS_PA*0.05*P_ESC[0]*COMP[0]
wp_hi = ACCOUNTS*ATTEMPTS_PA*0.05*P_ESC[1]*COMP[1]
print(f"    5% of {ACCOUNTS*ATTEMPTS_PA:,.0f} dials reach a wrong party; {P_ESC[0]*100:.1f}-{P_ESC[1]*100:.1f}% escalate:")
print(f"      wrong-party exposure = {money(wp_lo)} - {money(wp_hi)} / month  [MODEL]")
print(f"    [PUB] FY24 RBI Ombudsman: 85,281 loan/recovery complaints (+42.7% YoY, ~29% of all complaints)")
print(f"    [PUB] Bajaj Finance fined Rs 2.5 Cr for recovery-agent conduct — the LENDER pays, not the agent")

print("\n"+"="*100); print("S4 — FIELD VISIT & TRACE ROI BY TICKET (the segment-conditional finding)"); print("="*100)
def visit_roi(ticket, marginal=True):
    cost = 220 if marginal else 370
    p = sum([0.35,0.50])/2 * sum([0.30,0.45])/2
    rec = p*sum([0.25,0.40])/2*ticket*0.55     # 0.55 = incrementality
    return rec, cost, rec/cost
print(f"{'ticket':>10} | {'visit ROI (marginal)':>20} | {'visit ROI (standalone)':>22} | {'trace EV (Rs)':>24}")
print("-"*90)
for ticket in (5_000, 18_802, 50_000, 150_000, 800_000):
    rm, cm, roi_m = visit_roi(ticket); rs, cs, roi_s = visit_roi(ticket, False)
    scale = ticket/AVG_TICKET
    t_lo = 0.35*1.0*0.06*INCR_RPC*scale; t_hi = 0.60*2.5*0.14*INCR_RPC*scale*3
    print(f"{money(ticket):>10} | {roi_m:>19.2f}x | {roi_s:>21.2f}x | {money(t_lo):>10} - {money(t_hi):>10} vs fee Rs60-150")
print("""
FINDING [MODEL-2]: at the DIGITAL-PL average ticket (Rs 18.8k) a field visit only pays when it is
MARGINAL to an existing beat (2.4x) — as a standalone trip it barely clears 1x. Trace EV spans
Rs 7-204 per case at the average ticket depending on yield and uplift: a ~30x spread. Therefore BOTH actions must be
priced per account, not triggered by a rule or a bucket. Above Rs 1.5 L tickets, visit ROI is 10-100x
and the discipline that matters is ROUTE EFFICIENCY, not whether to visit at all.
=> PRODUCT SCOPE DECISION: SUTRA's confidence gate matters most in the Rs 5k-50k band (where a bad
   visit destroys the ROI) and matters least in vehicle/secured/ARC portfolios (where route
   optimisation dominates). Segment the deployment, do not oversell one story for all portfolios.""")

print("\n"+"="*100); print("S5 — SENSITIVITY: which lever buys the most recovery per 1 pp of its own probability"); print("="*100)
ATT = ACCOUNTS*ATTEMPTS_PA
rpc_mid, rg_mid = sum(CONNECT)/2, sum(RPC_GIVEN)/2
lever = [
  ("+1 pp connect rate (timing/window/contact point)", ATT*0.01*rg_mid*INCR_RPC, "new RPCs x incremental recovery per RPC"),
  ("+1 pp right-party share (identity gate)",          ATT*0.01*rpc_mid*INCR_RPC + ATT*0.01*rpc_mid*0.0005*45_000, "recovered RPCs + avoided conduct exposure"),
  ("+1 pp P(pay | RPC) (offer/agent/script)",          ATT*rpc_mid*0.01*AVG_TICKET*sum(PAY_FRACTION)/2*sum(INCREMENTALITY)/2, "Maestro already owns this layer"),
  ("+1 pp field-slot success",                         FIELD_SLOTS*0.01*sum([0.35,0.50])/2*sum([0.25,0.40])/2*AVG_TICKET*0.55, "6,600 slots/mo [ASSUME]"),
  ("+1 pp trace yield (new usable point found)",       2_000*0.01*1.75*0.10*INCR_RPC, "2,000 traces/mo [ASSUME]"),
]
for n, v, note in lever:
    print(f"  {n:<52} {money(v):>14} / month per pp   ({note})")
print("""
FINDING [MODEL-3]: per percentage point, identity/conduct corrections and field-slot success move
the most money — but they are also the two hardest to move. The CHEAPEST large lever is
P(pay | RPC), which belongs to the OFFER/agent layer (CN's Maestro already owns it).
We should therefore NOT claim that layer. Our defensible claim is the two control levers:
(a) never spend a Rs 220-370 slot or a Rs 60-150 trace on an unverified target, and
(b) never take a compliance-bearing action on an unverified identity. Both are measurable as
    AVOIDED WASTE and AVOIDED EXPOSURE — not as invented recovery uplift.""")

print("\n"+"="*100); print("S6 — BREAK-EVEN AT A PRICE (what has to be true for CN to buy this)"); print("="*100)
rpc_now = rpc_mid*rg_mid
per_pp = ATT*0.01*rg_mid*INCR_RPC
print(f"  [MODEL] one percentage point of connect rate on this book = {money(per_pp)}/month of incremental recovery")
for price in (1.0, 3.0, 5.0):
    need = price*ACCOUNTS
    pp = need/per_pp
    print(f"  Rs {price:.0f}/account/month = {money(need)}/mo -> requires +{pp:.2f} pp connect "
          f"(baseline connect {rpc_mid:.1%} -> {rpc_mid+pp/100:.2%}); or ~{need/220:,.0f} avoided field visits/month")
print("""
FINDING [MODEL-4]: at Rs 1-5 per account per month the required lift is TINY (a few basis points of
connect rate, or one avoided field visit per ~60 accounts). The product does not need a heroic
claim. It needs a DEMONSTRABLE one: show avoided expensive actions and avoided exposure on real
accounts. That is the single most important design constraint in this whole document.
If we cannot show avoided waste + avoided exposure, the ROI story collapses — no matter how good
the model is.""")

print("\n"+"="*100); print("S7 — EXECUTIVE SUMMARY OF THE ECONOMICS"); print("="*100)
print("""
  1. The expensive actions are human call (Rs33-44/RPC), field visit (Rs220-370), trace (Rs60-150),
     notice/legal. Those four are the product's scope.
  2. Automated dial-volume optimisation is worth Rs 0.3-7 L/month on a 100k book. Do not pitch it.
  3. Field-visit ROI is ticket-conditional: 0.4x standalone at Rs5k, 2.4x marginal at Rs18.8k,
     60-100x at Rs8L. One story cannot cover all portfolios.
  4. Trace EV spans 30x by account. The only honest way to fire it is per-account EVSI.
  5. Conduct exposure is bounded but real and is the pool a lender funds without argument: see S3
     VP-4 for the band, plus lumpy RBI penalties (Rs 2.5 Cr against Bajaj Finance) that dwarf the
     compensated amounts.
  6. Break-even needs only basis points of improvement. So the deliverable is EVIDENCE OF AVOIDED
     WASTE AND AVOIDED EXPOSURE, not a recovery-uplift claim.
""")
print("[MODEL END] every figure depends on [ASSUME] inputs that CN must replace with actuals.")
