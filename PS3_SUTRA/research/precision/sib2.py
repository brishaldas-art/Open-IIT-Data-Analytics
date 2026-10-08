import sys, csv, collections, statistics as st, math, re
sys.path.insert(0,"/home/user/PS3_SUTRA"); import os; os.chdir("/home/user/PS3_SUTRA")
from sutra import config, geo, splits, dataio
from sutra.indexes import get_index
from sutra.replay import _manifest, _proxy_truth
from sutra.store import Store
ix=get_index(); store=Store(); as_of=config.MOMENT
A=dataio.addresses(); L=dataio.localities(); LB={l["locality_id"]:l for l in L}
man=_manifest(ix); pool=[a for a,m in sorted(man.items()) if m["split"] in (splits.S_TRAIN,splits.S_VAL)]
TR={a for a,m in man.items() if m["split"]==splits.S_TRAIN}; VA={a for a,m in man.items() if m["split"]==splits.S_VAL}
T={a:_proxy_truth(store,a,as_of) for a in pool}
PINS={}
with open("data/official_ps3/baseline_geocodes.csv",encoding="utf-8",newline="") as fh:
    for r in csv.DictReader(fh): PINS[r["address_id"]]=(float(r["geocoder_x"]),float(r["geocoder_y"]),r["precision"])
# as-of clean: only addresses added before the cut may act as siblings
ADDED={a:A[a]["added_date"] for a in A}
tok_freq=collections.Counter(); nd=0
for a,r in A.items():
    if r["added_date"]<"2026-06-01":
        nd+=1
        for t in set(dataio.tokens(r.get("text_norm") or "")): tok_freq[t]+=1
def idf(t): return math.log((nd+1)/(tok_freq.get(t,0)+1))+1.0
LOC_TOKS={l["locality_id"]:[t for t in dataio.tokens(dataio.norm_text(l["locality_name"]))] for l in L}
def resolve(text,town):
    toks=set(dataio.tokens(text)); best=None
    for lid,ltoks in sorted(LOC_TOKS.items()):
        if not ltoks or LB[lid]["town_id"]!=town: continue
        pres=[t for t in ltoks if t in toks]
        if not pres: continue
        cov=len(pres)/len(ltoks); rare=min(ltoks,key=lambda t:(tok_freq.get(t,0),t))
        if cov<0.5 or rare not in toks: continue
        key=(-round(cov,6),-round(sum(idf(t) for t in pres),6),-len(ltoks),lid)
        if best is None or key<best[0]: best=(key,lid,cov)
    return (best[1],best[2]) if best else (None,None)
def road(t):
    m=re.search(r"\bgali (?:no )?(\d+)\b",t) or re.search(r"\b(?:road|rd) (\d+)\b",t)
    if m: return ("gali" if "gali" in m.group(0) else "road", m.group(1))
    m=re.search(r"(\d+)(?:st|nd|rd|th) cross\b",t); c=m.group(1) if m else None
    m2=re.search(r"(\d+)(?:st|nd|rd|th) main\b",t); mn=m2.group(1) if m2 else None
    if c or mn: return ("grid", f"{c or '-'}/{mn or '-'}")
    return None
def blk(t):
    m=re.search(r"\bblk ([a-z0-9]+)\b",t) or re.search(r"\bblock ([a-z0-9]+)\b",t)
    return m.group(1) if m else None
def house(t):
    m=re.search(r"\b(?:house|h\.no\.?|no\.?) ?(\d+)\b",t) or re.search(r"\b(\d{2,4})\b",t)
    return m.group(1) if m else None
KEY={}
for a,r in A.items():
    t=r.get("text_norm") or ""; lid,cov=resolve(t,r["town_id"])
    KEY[a]=(r["town_id"],lid,road(t),blk(t),house(t),cov)
def siblings(a,keys):
    ka=KEY[a]; out=[]
    for b in A:
        if b==a or ADDED[b]>="2026-06-01" or b not in PINS: continue
        kb=KEY[b]
        if all(ka[i]==kb[i] for i in keys): out.append(b)
    return out
def q(v,p): v=sorted(v); return round(float(v[int(p*(len(v)-1))]),1) if v else None
def fr(v,t): return round(sum(1 for x in v if x<=t)/len(v),4) if v else None
print("sibling-derived candidate error vs proxy truth (v2 locality keys, as-of clean siblings)")
KEYSETS={"town+loc+road":(0,1,2),"town+loc+blk+road":(0,1,3,2),"town+loc+blk":(0,1,3),
         "town+loc+road+blk+house":(0,1,2,3,4),"town+loc+house":(0,1,4)}
for label,keys in KEYSETS.items():
    allerr=[]; finer=[]; n_sib=[]; valerr=[]
    for a in pool:
        sib=siblings(a,keys)
        if not sib: continue
        pts=[PINS[b] for b in sib]
        mx=geo.median([p[0] for p in pts]); my=geo.median([p[1] for p in pts])
        e=geo.dist(mx,my,*T[a]); allerr.append(e); n_sib.append(len(sib))
        if a in VA: valerr.append(e)
        fine=[p for p in pts if p[2] in ("street","rooftop")]
        if fine:
            fx=geo.median([p[0] for p in fine]); fy=geo.median([p[1] for p in fine])
            finer.append(geo.dist(fx,fy,*T[a]))
    print(f"  {label:26s} cov={len(allerr):3d}/{len(pool)} med={q(allerr,0.5)} <100={fr(allerr,100)} <250={fr(allerr,250)} <500={fr(allerr,500)} | S-VAL med={q(valerr,0.5)} <500={fr(valerr,500)} | fine-subset n={len(finer)} med={q(finer,0.5)} <100={fr(finer,100)} <500={fr(finer,500)} | med #sib={q(n_sib,0.5)}")
# does the own pin agree with the sibling cluster? (agreement as a confidence signal)
print("\nagreement test (town+loc+road siblings, fine pins only):")
rows=[]
for a in pool:
    sib=[b for b in siblings(a,(0,1,2)) if PINS[b][2] in ("street","rooftop")]
    if not sib: continue
    fx=geo.median([PINS[b][0] for b in sib]); fy=geo.median([PINS[b][1] for b in sib])
    own=PINS[a]; d_agree=geo.dist(own[0],own[1],fx,fy)
    rows.append((a,own[2],d_agree,geo.dist(fx,fy,*T[a]),geo.dist(own[0],own[1],*T[a]),geo.dist(geo.median([PINS[b][0] for b in sib]),geo.median([PINS[b][1] for b in sib]),*T[a]) if len(sib)>1 else None))
print(f"  n={len(rows)} | when |pin - fine_sibling_median| > 500 m: {sum(1 for r in rows if r[2]>500)} rows")
sub=[r for r in rows if r[2]>500]
print(f"    on those, sibling is better: {sum(1 for r in sub if r[3]<r[4])} / {len(sub)} | mean gain {q([r[4]-r[3] for r in sub],0.5)}")
sub2=[r for r in rows if r[2]<=500]
print(f"    when they agree (<=500): {len(sub2)} rows, own pin better: {sum(1 for r in sub2 if r[4]<r[3])} / {len(sub2)}")
