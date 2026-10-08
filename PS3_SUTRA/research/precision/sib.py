import sys, csv, collections, statistics as st, re
sys.path.insert(0,"/home/user/PS3_SUTRA")
import os; os.chdir("/home/user/PS3_SUTRA")
from sutra import config, geo, ranking, splits, dataio
from sutra.candidates import generate
from sutra.indexes import get_index
from sutra.replay import _manifest, _proxy_truth
from sutra.store import Store
ix=get_index(); store=Store(); as_of=config.MOMENT
man=_manifest(ix)
pool=[a for a,m in sorted(man.items()) if m["split"] in (splits.S_TRAIN, splits.S_VAL)]
A=dataio.addresses()
BG={}
for k,v in csv.DictReader(open("data/official_ps3/baseline_geocodes.csv")) and [] or []: pass
import io
with open("data/official_ps3/baseline_geocodes.csv",encoding="utf-8",newline="") as fh:
    for r in csv.DictReader(fh): BG[r["address_id"]]=r
print("baseline rows:", len(BG))
print("pin precision over the book:", collections.Counter(BG[a]["precision"] for a in A if a in BG).most_common())
L=dataio.localities()
def loc_of(t):
    best=None
    for l in L:
        toks=[x for x in dataio.tokens(l["locality_name"]) if len(x)>2]
        if toks and all(x in t for x in toks) and (best is None or len(" ".join(toks))>best[1]):
            best=(l["locality_id"],len(" ".join(toks)))
    return best[0] if best else None
def road_of(t):
    m=re.search(r"\bgali (?:no )?(\d+)\b",t)
    if m: return ("gali",m.group(1))
    m=re.search(r"\b(?:road|rd) (\d+)\b",t)
    if m: return ("road",m.group(1))
    m=re.search(r"(\d+)(?:st|nd|rd|th) cross\b",t)
    if m: return ("cross",m.group(1))
    return None
PK={aid:(r["town_id"], loc_of(r.get("text_norm") or ""), road_of(r.get("text_norm") or "")) for aid,r in A.items()}
groups=collections.defaultdict(list)
for aid in sorted(A): groups[PK[aid]].append(aid)
sizes=collections.Counter(len(v) for v in groups.values())
print("place-group sizes:", sorted(sizes.items())[:10], "| groups:", len(groups), "| singletons:", sizes.get(1,0))

rows=[]
for aid in pool:
    tx,ty=_proxy_truth(store,aid,as_of)
    b=BG.get(aid)
    own_err=geo.dist(float(b["geocoder_x"]),float(b["geocoder_y"]),tx,ty) if b else None
    sib=[x for x in groups[PK[aid]] if x!=aid]
    sib_pins=[(float(BG[x]["geocoder_x"]),float(BG[x]["geocoder_y"]),BG[x]["precision"],x) for x in sib if x in BG]
    sib_fine=[p for p in sib_pins if p[2] in ("street","rooftop")]
    med=(geo.median([p[0] for p in sib_pins]), geo.median([p[1] for p in sib_pins])) if sib_pins else None
    medf=(geo.median([p[0] for p in sib_fine]), geo.median([p[1] for p in sib_fine])) if sib_fine else None
    rows.append(dict(aid=aid,own_prec=(b["precision"] if b else None),own_err=own_err,n_sib=len(sib_pins),n_fine=len(sib_fine),
                     sib_err=geo.dist(med[0],med[1],tx,ty) if med else None,
                     sibf_err=geo.dist(medf[0],medf[1],tx,ty) if medf else None,
                     n_sib_total=len(sib)))
def q(v,p): v=[x for x in v if x is not None]; return None if not v else round(float(sorted(v)[int(p*(len(v)-1))]),1)
def frac(v,thr): v=[x for x in v if x is not None]; return None if not v else round(sum(1 for x in v if x<=thr)/len(v),4)
own=[r['own_err'] for r in rows]
print(f"\npool n={len(rows)}")
print(f"  own pin err: median={q(own,0.5)} <500={frac(own,500)} <250={frac(own,250)} <100={frac(own,100)}")
print(f"  addrs with >=1 sibling: {sum(1 for r in rows if r['n_sib'])} | with >=1 FINE sibling: {sum(1 for r in rows if r['n_fine'])}")
s=[r for r in rows if r['sibf_err'] is not None]
print(f"  FINE-sibling median (n={len(s)}): median={q([r['sibf_err'] for r in s],0.5)} <500={frac([r['sibf_err'] for r in s],500)} <250={frac([r['sibf_err'] for r in s],250)} <100={frac([r['sibf_err'] for r in s],100)}")
print(f"    own pin for those: median={q([r['own_err'] for r in s],0.5)} <500={frac([r['own_err'] for r in s],500)}")
print(f"    sibling better than own: {sum(1 for r in s if r['own_err'] and r['sibf_err']<r['own_err'])} / {len(s)}")
s2=[r for r in rows if r['sib_err'] is not None]
print(f"  ANY-sibling median (n={len(s2)}): median={q([r['sib_err'] for r in s2],0.5)} <500={frac([r['sib_err'] for r in s2],500)} <250={frac([r['sib_err'] for r in s2],250)}")
print(f"    sibling better than own: {sum(1 for r in s2 if r['own_err'] and r['sib_err']<r['own_err'])} / {len(s2)}")
