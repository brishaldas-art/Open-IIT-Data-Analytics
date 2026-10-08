import sys, csv, collections, statistics as st, math, re
sys.path.insert(0,"/home/user/PS3_SUTRA"); import os; os.chdir("/home/user/PS3_SUTRA")
from sutra import config, geo, splits, dataio
from sutra.indexes import get_index
from sutra.replay import _manifest, _proxy_truth
from sutra.store import Store
ix=get_index(); store=Store(); as_of=config.MOMENT
A=dataio.addresses(); L=dataio.localities(); LM=dataio.landmarks()
man=_manifest(ix); pool=[a for a,m in sorted(man.items()) if m["split"] in (splits.S_TRAIN,splits.S_VAL)]
TR={a for a,m in man.items() if m["split"]==splits.S_TRAIN}; VA={a for a,m in man.items() if m["split"]==splits.S_VAL}
T={a:_proxy_truth(store,a,as_of) for a in pool}
PINS={}
with open("data/official_ps3/baseline_geocodes.csv",encoding="utf-8",newline="") as fh:
    for r in csv.DictReader(fh): PINS[r["address_id"]]=(float(r["geocoder_x"]),float(r["geocoder_y"]),r["precision"])
tok=collections.Counter(); nd=0
for a,r in A.items():
    if r["added_date"]<"2026-06-01":
        nd+=1
        for t in set(dataio.tokens(r.get("text_norm") or "")): tok[t]+=1
def idf(t): return math.log((nd+1)/(tok.get(t,0)+1))+1.0
LT={l["locality_id"]:[t for t in dataio.tokens(dataio.norm_text(l["locality_name"]))] for l in L}
LB={l["locality_id"]:l for l in L}
def resolve(text,town):
    toks=set(dataio.tokens(text)); best=None
    for lid,lt in sorted(LT.items()):
        if not lt or LB[lid]["town_id"]!=town: continue
        pres=[t for t in lt if t in toks]
        if not pres: continue
        cov=len(pres)/len(lt); rare=min(lt,key=lambda t:(tok.get(t,0),t))
        if cov<0.5 or rare not in toks: continue
        key=(-round(cov,6),-round(sum(idf(t) for t in pres),6),-len(lt),lid)
        if best is None or key<best[0]: best=(key,lid)
    return best[1] if best else None
# (a) EMPIRICAL locality centre: median of street/rooftop pins of addresses resolved to that locality (as-of clean)
mem=collections.defaultdict(list)
for a,r in A.items():
    if r["added_date"]>="2026-06-01" or a not in PINS: continue
    if PINS[a][2] not in ("street","rooftop"): continue
    lid=resolve(r.get("text_norm") or "", r["town_id"])
    if lid: mem[lid].append((PINS[a][0],PINS[a][1]))
EMP={lid:(geo.median([p[0] for p in v]),geo.median([p[1] for p in v])) for lid,v in mem.items() if len(v)>=3}
print("empirical locality centres built from fine pins:", len(EMP), "of", len(L), "| sizes:", sorted(collections.Counter({k:len(v) for k,v in mem.items()}).values())[:8], "...")
# compare supplied vs empirical centre error
sup_e=[]; emp_e=[]
for a in pool:
    lid=resolve(A[a].get("text_norm") or "", A[a]["town_id"])
    if not lid or lid not in EMP: continue
    s=geo.dist(float(LB[lid]["centroid_x"]),float(LB[lid]["centroid_y"]),*T[a]); e=geo.dist(*EMP[lid],*T[a])
    sup_e.append(s); emp_e.append(e)
def q(v,p): v=sorted(v); return round(float(v[int(p*(len(v)-1))]),1)
def fr(v,t): return round(sum(1 for x in v if x<=t)/len(v),4)
print(f"  n={len(sup_e)} supplied centre: med={q(sup_e,.5)} <500={fr(sup_e,500)} <250={fr(sup_e,250)} | empirical centre: med={q(emp_e,.5)} <500={fr(emp_e,500)} <250={fr(emp_e,250)} | empirical better: {sum(1 for s,e in zip(sup_e,emp_e) if e<s)}/{len(sup_e)}")
print(f"  supplied vs empirical centre distance: med={q([geo.dist(float(c['centroid_x']),float(c['centroid_y']),*EMP[c['locality_id']]) for c in L if c['locality_id'] in EMP],.5)}")
