"""
verify_slide1_numbers.py — independent re-computation of the numbers quoted on
Slide 1 of the SUTRA report.

Reads ONLY the official frozen tree (read-only) and prints the measurements.
Nothing is written, nothing is fitted, no model is involved.

Run:  python3 tools/verify_slide1_numbers.py
"""

from __future__ import annotations

import csv
import math
import os
import statistics as st
from collections import Counter, defaultdict

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "official_ps3")


def load(name: str) -> list[dict]:
    with open(os.path.join(ROOT, name + ".csv"), newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def f(row: dict, key: str):
    v = row.get(key, "")
    return float(v) if v not in ("", None) else None


def dist(a, b):
    if a is None or b is None:
        return None
    return math.hypot(a[0] - b[0], a[1] - b[1])


def med(xs):
    xs = [x for x in xs if x is not None]
    return st.median(xs) if xs else None


def pct(xs, p):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    k = (len(xs) - 1) * p / 100.0
    lo, hi = math.floor(k), math.ceil(k)
    return xs[lo] if lo == hi else xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


def main() -> None:
    addresses = load("addresses")
    geocodes = load("baseline_geocodes")
    surveyed = load("surveyed_addresses")
    visits = load("field_visits")

    print("=" * 78)
    print("SLIDE-1 NUMBER VERIFICATION — official PS3 tree (read-only)")
    print("=" * 78)

    # ---- F1: the book and the vendor pin -------------------------------------
    print("\n[F1] The book and the vendor pin")
    print(f"  addresses                 n = {len(addresses)}")
    lens = [len(r['address_text']) for r in addresses]
    print(f"  address_text length       median = {med(lens):.0f} chars")
    nocomma = sum(1 for r in addresses if ',' not in r['address_text'])
    print(f"  no comma at all           {nocomma} ({100*nocomma/len(addresses):.1f}%)")
    nodigit = sum(1 for r in addresses if not any(c.isdigit() for c in r['address_text']))
    print(f"  no digit at all           {nodigit}")
    out = sum(1 for r in addresses if r['town_id'] == 'OUT')
    print(f"  town_id = 'OUT'           {out}")

    geo = {r['address_id']: r for r in geocodes}
    print(f"  baseline_geocodes         n = {len(geocodes)}")
    print(f"  addresses WITHOUT a pin   {len(addresses) - len(geocodes)} "
          f"({100*(len(addresses)-len(geocodes))/len(addresses):.1f}%)")
    strata = Counter(r['precision'] for r in geocodes)
    for k, v in strata.most_common():
        print(f"    {k:<10} {v:>5}  ({100*v/len(geocodes):.1f}%)")

    # ---- F2: how wrong the pin is, measured on the 100 surveyed ---------------
    print("\n[F2] Vendor pin vs surveyed truth (the only ground truth, n=100)")
    errs, by_stratum = [], defaultdict(list)
    for r in surveyed:
        g = geo.get(r['address_id'])
        if not g:
            continue
        d = dist((f(g, 'geocoder_x'), f(g, 'geocoder_y')),
                 (f(r, 'surveyed_x'), f(r, 'surveyed_y')))
        errs.append(d)
        by_stratum[g['precision']].append(d)
    print(f"  n scored                  {len(errs)}")
    print(f"  median error              {med(errs):.1f} m")
    print(f"  p90 error                 {pct(errs, 90):.1f} m")
    print(f"  within 100 m              {100*sum(1 for d in errs if d <= 100)/len(errs):.1f}%")
    print(f"  within 500 m              {100*sum(1 for d in errs if d <= 500)/len(errs):.1f}%")
    for k in sorted(by_stratum, key=lambda k: med(by_stratum[k])):
        v = by_stratum[k]
        flag = "" if len(v) >= 15 else "   <-- below n>=15 guard, indicative only"
        print(f"    {k:<10} n={len(v):>3}  median {med(v):>8.1f} m  "
              f"max {max(v):>8.1f} m{flag}")

    # ---- F3: what a visit actually means -------------------------------------
    print("\n[F3] What a field visit actually means (surveyed subset)")
    truth = {r['address_id']: (f(r, 'surveyed_x'), f(r, 'surveyed_y')) for r in surveyed}
    rows = defaultdict(list)
    for v in visits:
        aid = v['address_id']
        if aid not in truth:
            continue
        pt = (f(v, 'checkin_x'), f(v, 'checkin_y'))
        g = geo.get(aid)
        pin = (f(g, 'geocoder_x'), f(g, 'geocoder_y')) if g else None
        rows[v['outcome']].append((
            dist(pt, truth[aid]),
            dist(pt, pin),
            int(float(v['dwell_s'])) if v['dwell_s'] else None,
        ))
    for outcome in sorted(rows, key=lambda k: -len(rows[k])):
        v = rows[outcome]
        d_t, d_p, dw = [x[0] for x in v], [x[1] for x in v], [x[2] for x in v]
        closer_pin = sum(1 for a, b in zip(d_t, d_p) if a is not None and b is not None and b < a)
        n_pair = sum(1 for a, b in zip(d_t, d_p) if a is not None and b is not None)
        print(f"  {outcome:<24} n={len(v):>3}  med->truth {med(d_t):>8.1f} m  "
              f"med->pin {med(d_p):>7.1f} m  closer-to-pin "
              f"{100*closer_pin/max(n_pair,1):>5.1f}%  med dwell {med(dw)/60 if med(dw) else 0:>5.1f} min")

    pos = [x for k in ('met_borrower', 'met_family', 'cash_collected') for x in rows.get(k, [])]
    neg = rows.get('address_not_traceable', [])
    if pos and neg:
        print(f"  --> success visits (n={len(pos)}): median {med([x[0] for x in pos]):.1f} m from truth")
        print(f"  --> not_traceable (n={len(neg)}): median {med([x[0] for x in neg]):.1f} m from truth, "
              f"median {med([x[1] for x in neg]):.1f} m from the PIN")

    # ---- F4: exposure and integrity ------------------------------------------
    print("\n[F4] Exposure and integrity")
    print(f"  field_visits              n = {len(visits)}")
    print(f"  distinct addresses visited  {len(set(v['address_id'] for v in visits))} "
          f"({100*len(set(v['address_id'] for v in visits))/len(addresses):.1f}% of the book)")
    oc = Counter(v['outcome'] for v in visits)
    for k, v in oc.most_common():
        print(f"    {k:<26} {v:>5} ({100*v/len(visits):.1f}%)")
    fast = sum(1 for v in visits if v['dwell_s'] and float(v['dwell_s']) < 60)
    print(f"  visits under 60 s         {fast}")

    per_agent = defaultdict(lambda: [0, Counter()])
    for v in visits:
        per_agent[v['agent_id']][0] += 1
        if v['photo_hash']:
            per_agent[v['agent_id']][1][v['photo_hash']] += 1
    worst = []
    for aid, (n, hashes) in per_agent.items():
        dup = sum(c - 1 for c in hashes.values() if c > 1)
        worst.append((dup / n if n else 0.0, aid, dup, n))
    worst.sort(reverse=True)
    print("  duplicate photo-hash rate, top 3 agents:")
    for rate, aid, dup, n in worst[:3]:
        print(f"    {aid}  {dup}/{n} = {100*rate:.1f}%")
    others = [w for w in worst[1:]]
    print(f"  every other agent max     {100*max(r for r, *_ in others):.2f}%")

    print("\nAll figures above are recomputed from the frozen official CSVs in this run.")


if __name__ == "__main__":
    main()
