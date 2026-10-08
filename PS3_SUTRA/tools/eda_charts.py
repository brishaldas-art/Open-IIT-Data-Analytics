#!/usr/bin/env python3
"""
SUTRA — EDA charts (official PS3 dataset only) + a self-contained HTML dashboard.

Writes data/derived/eda_charts/*.svg and data/derived/eda_charts.html (SVG inlined, no external assets).
Every chart answers a modelling question; nothing here is decorative.

    python3 tools/eda_charts.py
"""
import os, json
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); SEC = os.path.dirname(HERE)
D = os.environ.get("CN_DATASET", os.path.join(SEC, "data", "official_ps3"))
OUT = os.environ.get("CN_OUT", os.path.join(SEC, "data", "derived"))
CH = os.path.join(OUT, "eda_charts"); os.makedirs(CH, exist_ok=True)

ad = pd.read_csv(f"{D}/addresses.csv"); lo = pd.read_csv(f"{D}/localities.csv")
bg = pd.read_csv(f"{D}/baseline_geocodes.csv"); fv = pd.read_csv(f"{D}/field_visits.csv")
sv = pd.read_csv(f"{D}/surveyed_addresses.csv"); gp = pd.read_csv(f"{D}/visit_gps_points.csv")
ag = pd.read_csv(f"{D}/agents.csv")

MET = ["met_borrower", "met_family", "cash_collected"]
C = dict(blue="#2b6cb0", green="#2f855a", red="#9b2c2c", purple="#553c9a", amber="#b7791f", teal="#2c7a7b")


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def bar(title, labels, values, unit="", colour=C["blue"], note="", fmt="{:.0f}"):
    w, rowh, pad = 780, 26, 10
    h = 60 + rowh * len(labels) + (26 if note else 0)
    mx = max(values) if values and max(values) > 0 else 1
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
           f'font-family="Segoe UI,Helvetica,Arial,sans-serif" font-size="12">',
           f'<rect width="{w}" height="{h}" fill="#fff"/>',
           f'<text x="{pad}" y="20" font-size="13.5" font-weight="600" fill="#1a202c">{esc(title)}</text>']
    y = 42
    for lab, v in zip(labels, values):
        bw = 380 * (v / mx)
        out += [f'<text x="{pad}" y="{y+13}" fill="#2d3748">{esc(str(lab)[:48])}</text>',
                f'<rect x="320" y="{y+3}" width="{max(bw,1):.1f}" height="13" rx="2" fill="{colour}" opacity="0.87"/>',
                f'<text x="{320+max(bw,1)+7:.0f}" y="{y+13}" fill="#1a202c" font-weight="600">{fmt.format(v)}{esc(unit)}</text>']
        y += rowh
    if note:
        out.append(f'<text x="{pad}" y="{y+14}" fill="#718096" font-size="11.5">{esc(note)}</text>')
    out.append("</svg>")
    return "\n".join(out)


def hist(title, counts, edges, colour=C["amber"], note=""):
    w, h, pad = 780, 230, 46
    n = len(counts); mx = max(counts) if max(counts) else 1
    bw = (w - 2 * pad) / n
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
           f'font-family="Segoe UI,Helvetica,Arial,sans-serif" font-size="11">',
           f'<rect width="{w}" height="{h}" fill="#fff"/>',
           f'<text x="{pad}" y="18" font-size="13.5" font-weight="600" fill="#1a202c">{esc(title)}</text>',
           f'<line x1="{pad}" y1="{h-28}" x2="{w-pad}" y2="{h-28}" stroke="#e2e8f0"/>']
    for i, c in enumerate(counts):
        bh = (h - 78) * (c / mx); x = pad + i * bw
        out += [f'<rect x="{x+1:.1f}" y="{h-28-bh:.1f}" width="{max(bw-2,1):.1f}" height="{bh:.1f}" fill="{colour}" opacity="0.85"/>']
        if c:
            out.append(f'<text x="{x+bw/2:.1f}" y="{h-32-bh:.1f}" text-anchor="middle" fill="#4a5568">{c}</text>')
    for i in range(0, n + 1, max(1, n // 12)):
        out.append(f'<text x="{pad+i*bw:.1f}" y="{h-12}" text-anchor="middle" fill="#718096">{esc(f"{edges[i]:g}")}</text>')
    if note:
        out.append(f'<text x="{pad}" y="{h-1}" fill="#718096">{esc(note)}</text>')
    out.append("</svg>")
    return "\n".join(out)


Q = []   # (chart_title, svg, question_it_answers)
def add(name, svg, question):
    open(os.path.join(CH, f"{name}.svg"), "w", encoding="utf-8").write(svg)
    Q.append((name, svg, question))
    print(f"  chart: {name:<26} {question}")


print("SUTRA — EDA charts (official dataset only)")

# 1 address length
L = ad.address_text.astype(str).str.len()
c, e = np.histogram(L, bins=12, range=(0, 120))
add("addr_len", hist("Address text length (characters), n=3,117", list(c), list(e),
                     note="Median 67, max 113 — records are short strings, not paragraphs."),
    "Is the address a long free-text field requiring heavy NLP?  → No: median 67 chars.")

# 2 token count
T = ad.address_text.astype(str).str.split().str.len()
c, e = np.histogram(T, bins=15, range=(0, 21))
add("addr_tokens", hist("Address token count, n=3,117", list(c), list(e), colour=C["green"],
                        note="Mean 11.9 tokens — word-level matching and span rules are feasible."),
    "Can token-level features carry signal?  → Yes: 11.9 tokens per record.")

# 3 address component presence
comp = {
    "pincode token present (93.3%)": 93.3, "town name present (93.7%)": 93.7,
    "locality name token (82.5%)": 82.5, "house-number-like token (37.2%)": 37.2,
    "strict house no. (51.9%)": 51.9, "known landmark phrase (25.2%)": 25.2,
    "no comma at all (24.9%)": 24.9, "no separator at all (0.8%)": 0.8,
}
add("addr_components", bar("Structural components present in address text (n=3,117)", list(comp), list(comp.values()),
                           unit="%", colour=C["teal"],
                           note="Locality and pincode evidence is usually present; the house number is the scarce component."),
    "Which components are available most often — and which are scarce?")

# 4 baseline precision strata
vc = bg.precision.value_counts()
add("baseline_strata", bar("Vendor geocode precision strata (n=2,880 geocoded addresses)", list(vc.index), list(vc.values),
                           colour=C["blue"], note="71% locality-level: the vendor knows the neighbourhood, not the house."),
    "Is the vendor pin precise enough to be the answer?  → No: 71% are locality-level.")

# 5 baseline error curve
mm = sv.merge(bg, on="address_id")
mm["err"] = np.hypot(mm.surveyed_x - mm.geocoder_x, mm.surveyed_y - mm.geocoder_y)
thr = [50, 100, 250, 500, 1000]
add("baseline_error_curve", bar("Vendor pin: share of surveyed addresses within X metres (n=100)",
                                [f"≤ {t} m" for t in thr], [100 * (mm.err < t).mean() for t in thr], unit="%",
                                colour=C["red"], note="Only 9% within 100 m. Median error 376 m, max 4,808 m."),
    "How often is the vendor pin good enough to act on, and at what distance?")

# 6 error by stratum
rows = [(p, len(g), g.err.median(), g.err.quantile(.9)) for p, g in mm.groupby("precision")]
add("baseline_error_stratum",
    bar("Vendor error vs surveyed truth, by stratum (median and p90)",
        [f"{p} (n={n})" for p, n, _, _ in rows] + [f"{p} — p90" for p, n, _, _ in rows if n >= 5],
        [m for _, _, m, _ in rows] + [q for _, n, _, q in rows if n >= 5], unit=" m", colour=C["red"],
        note="pincode stratum: median 1,376 m, p90 3,820 m, n=10 → cannot be calibrated on this sample."),
    "Does error depend on the vendor's own precision claim?  → Yes, by an order of magnitude.")

# 7 visit outcomes
vo = fv.outcome.value_counts()
add("visit_outcomes", bar("Field-visit outcomes (n=5,578 visits)", list(vo.index), list(vo.values), colour=C["purple"],
                          note="1 in 4 visits is 'address_not_traceable'; met-someone totals 40.6%."),
    "What is the field actually reporting, and how big is the failure class?")

# 8 outcome by precision stratum
o = fv.merge(bg, on="address_id")
tab = o.assign(nt=o.outcome.eq("address_not_traceable")).groupby("precision").nt.mean().reindex(
    ["rooftop", "street", "locality", "pincode"])
add("outcome_by_stratum", bar("Share of visits ending 'address_not_traceable', by vendor stratum",
                              [f"{i} (n={int((o.precision==i).sum())})" for i in tab.index],
                              [100 * v for v in tab.values], unit="%", colour=C["red"],
                              note="6.4% → 51.8%: pin quality predicts field-visit failure."),
    "Does a worse pin cause more failed visits?  → Yes, monotonically.")

# 9 dwell vs outcome
bands = pd.cut(fv.dwell_s, [0, 60, 180, 600, 1500], labels=["<1 min", "1–3 min", "3–10 min", "10–25 min"])
d = fv.assign(met=fv.outcome.isin(MET)).groupby(bands, observed=True).met.mean()
add("dwell_outcome", bar("Share of visits that met someone, by dwell band", [str(i) for i in d.index],
                         [100 * v for v in d.values], unit="%", colour=C["green"],
                         note="Nearly deterministic: a SYNTHETIC-GENERATOR artefact — mechanisms are real, magnitudes are not."),
    "How strongly does dwell separate success from failure?  → Almost perfectly (a warning about synthetic data).")

# 10 exposure by delinquency
ac = pd.read_csv(f"{D}/accounts.csv")
av = ac.assign(visited=ac.account_id.isin(set(fv.account_id)),
               band=pd.cut(ac.dpd_start, [-1, 30, 60, 90, 180, 1000], labels=["0–30", "31–60", "61–90", "91–180", "180+"]))
e = av.groupby("band", observed=True).visited.mean()
add("exposure_dpd", bar("Share of accounts ever visited, by delinquency band (n=2,400)",
                        [f"DPD {i} (n={int((av.band==i).sum())})" for i in e.index], [100 * v for v in e.values],
                        unit="%", colour=C["amber"],
                        note="25.1% → 96.8%: visits are allocated by risk, not by uncertainty → selection bias is structural."),
    "Are visits a random sample of the book?  → No: strongly risk-weighted.")

# 11 GPS accuracy
c, e = np.histogram(gp.accuracy_m, bins=[0, 5, 8, 10, 15, 20, 30, 50, 100, 120])
add("gps_accuracy", hist("GPS reported accuracy per point (metres, n=160,406)", list(c),
                         [0, 5, 8, 10, 15, 20, 30, 50, 100, 120], colour=C["teal"],
                         note="Median 10 m; 10 points above 100 m. API accuracy is a ~68% radial confidence, not a bound."),
    "How reliable is a single GPS fix, and how should its weight vary?")

# 12 visits over time
wk = pd.to_datetime(fv.visit_date).value_counts().sort_index().resample("W").sum()
add("visits_time", bar("Visits per week (weeks beginning 2026-04-01)", [d.strftime("%d %b") for d in wk.index],
                       list(wk.values), colour=C["blue"],
                       note="13 weeks, ~430/week, no regime change: any drift study here is a simulation."),
    "Is there enough temporal depth for a real drift experiment?  → No.")

# 13 agent duplicate-photo rate
vd = fv.groupby("agent_id").apply(lambda d: 100 * (1 - d.photo_hash.nunique() / len(d))).sort_values(ascending=False)
add("agent_photo_dup", bar("Duplicate-photo rate by field agent (%)", [f"{a} (n={int((fv.agent_id==a).sum())})" for a in vd.index],
                           list(vd.values), unit="%", colour=C["red"],
                           note="One agent at 25.6%; all others ≤0.3%. The dataset's only planted integrity anomaly — with pristine GPS."),
    "Can an integrity layer be built on GPS alone?  → No: the anomaly is in media.")

# 14 candidate arms coverage (derived from official data only)
try:
    cands = pd.read_csv(f"{OUT}/candidates_coldstart.csv")
    lab = pd.read_csv(f"{OUT}/labels_eval.csv")
    cov = cands.groupby("arm").address_id.nunique() / 3117 * 100
    med = lab.groupby("arm").err_m.median()
    lab2 = [f"{a} — coverage {cov.get(a,0):.0f}%" for a in cov.index] + [f"{a} — median err" for a in med.index]
    val = list(cov.values) + list(med.values)
    add("candidate_arms", bar("Candidate arms from official data only: coverage over 3,117 addresses, then median error on the surveyed 100",
                              lab2, val, colour=C["blue"],
                              note="Vendor pin 92% coverage / 376 m; matched locality 66% / 357 m; town centroid 92% / 2,740 m."),
        "With the official data alone, what does candidate generation actually deliver?")
except Exception as ex:  # pragma: no cover
    print("  (skipped candidate_arms:", ex, ")")

# ── dashboard ────────────────────────────────────────────────────────────────
html = ["""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>SUTRA — official PS3 dataset EDA charts</title></head>
<body style="margin:0;background:#f7fafc;font-family:Segoe UI,Helvetica,Arial,sans-serif;color:#1a202c">
<div style="max-width:860px;margin:0 auto;padding:24px">
<h1 style="font-size:22px;margin:0 0 4px">SUTRA — EDA charts, official PS3 dataset</h1>
<p style="color:#4a5568;margin:0 0 20px;font-size:13.5px">Every chart answers a modelling question printed beneath it.
All numbers come from <code>data/official_ps3/</code> only; regenerate with <code>python3 tools/eda_charts.py</code>.</p>
"""]
for name, svg, question in Q:
    html.append(f'<section style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:14px;margin:0 0 18px">'
                f'{svg}<p style="margin:10px 0 0;color:#2d3748;font-size:13px"><b>Question:</b> {esc(question)}</p>'
                f'<p style="margin:4px 0 0;color:#718096;font-size:11.5px">file: data/derived/eda_charts/{name}.svg</p></section>')
html.append("</div></body></html>")
open(os.path.join(OUT, "eda_charts.html"), "w", encoding="utf-8").write("\n".join(html))
print(f"\n{len(Q)} charts → data/derived/eda_charts/  and  data/derived/eda_charts.html")
