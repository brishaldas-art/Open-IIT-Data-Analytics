#!/usr/bin/env python3
"""Rebuild this section's acceptance table: derived/derived_ps3_radius_calibration.csv
   — the radius table PS3 must output, from two independent samples.
   Reads ../data/raw ; writes ../data/derived . Override with $CN_DATASET / $CN_OUT."""
import os, pandas as pd, numpy as np, warnings
warnings.filterwarnings('ignore')
_HERE = os.path.dirname(os.path.abspath(__file__)); _SEC = os.path.dirname(_HERE)
D = os.environ.get('CN_DATASET', os.path.join(_SEC, 'data', 'official_ps3')).rstrip('/') + '/'
OUT = os.environ.get('CN_OUT', os.path.join(_SEC, 'data', 'derived')).rstrip('/') + '/'
os.makedirs(OUT, exist_ok=True)
d = lambda a, b, c, e: np.hypot(np.asarray(a, float) - np.asarray(c, float), np.asarray(b, float) - np.asarray(e, float))
bg = pd.read_csv(D + 'baseline_geocodes.csv'); fv = pd.read_csv(D + 'field_visits.csv')
sv = pd.read_csv(D + 'surveyed_addresses.csv'); ad = pd.read_csv(D + 'addresses.csv')
MET = ['met_borrower', 'met_family', 'cash_collected']
v = fv.merge(bg, on='address_id', how='left'); v['nav'] = d(v.checkin_x, v.checkin_y, v.geocoder_x, v.geocoder_y)
met = v[v.outcome.isin(MET)].copy(); rows = []
for p, g in met.groupby('precision'):
    rows.append(dict(stratum='vendor_precision=' + p, n=len(g), median_m=round(g.nav.median(),1), p75_m=round(g.nav.quantile(.75),1),
        p90_m=round(g.nav.quantile(.9),1), hit_100m=round((g.nav < 100).mean(),3), hit_250m=round((g.nav < 250).mean(),3),
        hit_500m=round((g.nav < 500).mean(),3), evidence='field check-in vs geocode, met-someone visits only'))
s = sv.merge(ad, on='address_id').merge(bg, on='address_id', how='left'); s['err'] = d(s.surveyed_x, s.surveyed_y, s.geocoder_x, s.geocoder_y)
for p, g in s.groupby('precision'):
    rows.append(dict(stratum='SURVEY vendor_precision=' + p, n=len(g), median_m=round(g.err.median(),1), p75_m=round(g.err.quantile(.75),1),
        p90_m=round(g.err.quantile(.9),1), hit_100m=round((g.err < 100).mean(),3), hit_250m=round((g.err < 250).mean(),3),
        hit_500m=round((g.err < 500).mean(),3), evidence='surveyed ground truth (n=100) vs geocode'))
rows.append(dict(stratum='SURVEY all', n=len(s), median_m=round(s.err.median(),1), p75_m=round(s.err.quantile(.75),1),
    p90_m=round(s.err.quantile(.9),1), hit_100m=round((s.err < 100).mean(),3), hit_250m=round((s.err < 250).mean(),3),
    hit_500m=round((s.err < 500).mean(),3), evidence='surveyed ground truth (n=100) vs geocode'))
rows.append(dict(stratum='FIELD all met-someone check-ins', n=len(met), median_m=round(met.nav.median(),1),
    p75_m=round(met.nav.quantile(.75),1), p90_m=round(met.nav.quantile(.9),1),
    hit_100m=round((met.nav < 100).mean(),3), hit_250m=round((met.nav < 250).mean(),3),
    hit_500m=round((met.nav < 500).mean(),3),
    evidence='AGENT-GENERATED, NOT GROUND TRUTH: check-in vs vendor pin. '
             'Range of agent behaviour is a caveat, not a confidence interval.'))
neg = v[v.outcome == 'address_not_traceable']
rows.append(dict(stratum='FIELD address_not_traceable check-ins', n=len(neg), median_m=round(neg.nav.median(),1),
    p75_m=round(neg.nav.quantile(.75),1), p90_m=round(neg.nav.quantile(.9),1), hit_100m=round((neg.nav < 100).mean(),3),
    hit_250m=round((neg.nav < 250).mean(),3), hit_500m=round((neg.nav < 500).mean(),3),
    evidence='NOT A LOCATION LABEL: measured 1,603 m from surveyed truth at 1.3 min median dwell.'))
pd.DataFrame(rows).to_csv(OUT + 'derived_ps3_radius_calibration.csv', index=False)
print(open(OUT + 'derived_ps3_radius_calibration.csv').read())
print("PS3 acceptance table rebuilt ->", OUT + 'derived_ps3_radius_calibration.csv')
