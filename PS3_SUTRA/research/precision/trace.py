"""Is a visit's GPS trace a better location estimator than its single check-in sample?
Non-circular test: pre-T0 estimator evaluated against post-T0 check-in evidence (the production label)."""
import sys, csv, collections, datetime as dt
sys.path.insert(0,"/home/user/PS3_SUTRA"); import os; os.chdir("/home/user/PS3_SUTRA")
from sutra import config, geo, splits
from sutra.indexes import get_index
from sutra.replay import _manifest
ix=get_index(); man=_manifest(ix)
V={r["visit_id"]:r for r in csv.DictReader(open("data/official_ps3/field_visits.csv",encoding="utf-8",newline=""))}
TR=collections.defaultdict(list)
with open("data/official_ps3/visit_gps_points.csv",encoding="utf-8",newline="") as fh:
    for r in csv.DictReader(fh): TR[r["visit_id"]].append(r)
for k in TR: TR[k].sort(key=lambda p:int(p["seq"]))
def ep(ts): return dt.datetime.strptime(ts[:19].replace("T"," "),"%Y-%m-%d %H:%M:%S").timestamp()
def med(pts): return (geo.median([p[0] for p in pts]), geo.median([p[1] for p in pts]))
def ck(v): return (float(v["checkin_x"]),float(v["checkin_y"]))
def tail(v,k=3):
    p=TR.get(v["visit_id"],[])[-k:]
    return med([(float(x["x"]),float(x["y"])) for x in p]) if p else ck(v)
def window(v,sec=120):
    p=TR.get(v["visit_id"])
    if not p: return ck(v)
    try: t1=ep(v["checkin_ts"])
    except Exception: t1=ep(p[-1]["point_ts"])
    w=[(float(x["x"]),float(x["y"])) for x in p if abs(ep(x["point_ts"])-t1)<=sec] or [(float(x["x"]),float(x["y"])) for x in p[-3:]]
    return med(w)
def accw(v,k=10):
    p=TR.get(v["visit_id"],[])[-k:]
    if not p: return ck(v)
    w=[1.0/max(1.0,float(x["accuracy_m"])) for x in p]; s=sum(w)
    return (sum(float(x["x"])*a for x,a in zip(p,w))/s, sum(float(x["y"])*a for x,a in zip(p,w))/s)
def medoid(v,k=10):
    p=TR.get(v["visit_id"],[])[-k:]
    if not p: return ck(v)
    P=[(float(x["x"]),float(x["y"])) for x in p]
    if len(P)<3: return med(P)
    best=min(P,key=lambda a:sum(geo.dist(a[0],a[1],b[0],b[1]) for b in P))
    near=[b for b in P if geo.dist(best[0],best[1],b[0],b[1])<=150]
    return med(near)
EST={"checkin":ck,"tail3":lambda v:tail(v,3),"window120s":lambda v:window(v,120),
     "accw10":lambda v:accw(v,10),"medoid10":lambda v:medoid(v,10)}
PROMO={"met_borrower","met_family","cash_collected"}
byA=collections.defaultdict(list)
for v in V.values(): byA[v["address_id"]].append(v)
pool=sorted(a for a,m in man.items() if m["split"] in (splits.S_TRAIN,splits.S_VAL))
def q(v,p): v=sorted(v); return round(float(v[int(p*(len(v)-1))]),1)
def fr(v,t): return round(sum(1 for x in v if x<=t)/len(v),4)
for T0 in ("2026-05-01","2026-05-15"):
    lab={}
    for a in pool:
        post=[v for v in byA.get(a,[]) if v["outcome"] in PROMO and v["visit_date"][:10]>=T0 and v["checkin_x"]]
        if post: lab[a]=med([ck(v) for v in post])
    print(f"T0={T0} · addresses with a post-T0 label: {len(lab)}")
    for name,fn in EST.items():
        d=[]; d_same=[]
        for a,(tx,ty) in lab.items():
            pre=[v for v in byA.get(a,[]) if v["outcome"] in PROMO and v["visit_date"][:10]<T0]
            if not pre: continue
            p=[fn(v) for v in pre]; mx,my=med(p)
            d.append(geo.dist(mx,my,tx,ty))
            # also: the *last* pre visit alone (closest in time to the label)
            d_same.append(geo.dist(*fn(sorted(pre,key=lambda v:v["visit_date"])[-1]),tx,ty))
        print(f"  {name:11s} median-of-pre-visits: n={len(d):3d} <100={fr(d,100)} <250={fr(d,250)} <500={fr(d,500)} med={q(d,.5)}"
              f" || last-pre-visit-only: <100={fr(d_same,100)} <250={fr(d_same,250)} <500={fr(d_same,500)} med={q(d_same,.5)}")
