import sys, csv, collections, statistics as st, re, math, json
sys.path.insert(0,"/home/user/PS3_SUTRA"); import os; os.chdir("/home/user/PS3_SUTRA")
from sutra import config, geo, splits, dataio
from sutra.indexes import get_index
from sutra.replay import _manifest, _proxy_truth
from sutra.store import Store
ix=get_index(); store=Store(); as_of=config.MOMENT
A=dataio.addresses(); L=dataio.localities(); LB={l["locality_id"]:l for l in L}
man=_manifest(ix); pool=[a for a,m in sorted(man.items()) if m["split"] in (splits.S_TRAIN,splits.S_VAL)]
train=set(a for a,m in man.items() if m["split"]==splits.S_TRAIN); val=set(a for a,m in man.items() if m["split"]==splits.S_VAL)
T={a:_proxy_truth(store,a,as_of) for a in pool}
towns=collections.Counter(); tok_freq=collections.Counter()
for r in A.values():
    towns[r["town_id"]]+=1
    for t in set(dataio.tokens(r.get("text_norm") or "")): tok_freq[t]+=1
N=len(A)
def idf(t): return math.log((N+1)/(tok_freq.get(t,0)+1))+1.0
LOC_TOKS={l["locality_id"]:[t for t in dataio.tokens(dataio.norm_text(l["locality_name"]))] for l in L}
def resolve(text, town, cross_town=True, min_cover=1.0, need_rare=True):
    toks=set(dataio.tokens(text))
    if not toks: return None
    cands=[]
    for lid,ltoks in LOC_TOKS.items():
        if not ltoks: continue
        present=[t for t in ltoks if t in toks]
        cover=len(present)/len(ltoks)
        if cover < min_cover: continue
        if need_rare:
            rare=min(ltoks,key=lambda t:tok_freq.get(t,0))
            if rare not in toks: continue
        score=sum(idf(t) for t in present)
        in_town = LB[lid]["town_id"]==town
        cands.append((in_town, score, len(ltoks), lid))
    if not cands: return None
    intown=[c for c in cands if c[0]]
    if intown: pick=max(intown,key=lambda c:(c[1],c[2],-ord(c[3][0])-len(c[3])))  # deterministic
    elif cross_town: pick=max(cands,key=lambda c:(c[1],c[2]))
    else: return None
    return pick[3]
def err(lid,a):
    if not lid: return None
    l=LB[lid]; return geo.dist(float(l["centroid_x"]),float(l["centroid_y"]),*T[a])
def q(v,p): v=sorted(x for x in v if x is not None); return round(float(v[int(p*(len(v)-1))]),1) if v else None
def fr(v,thr): v=[x for x in v if x is not None]; return round(sum(1 for x in v if x<=thr)/len(v),4) if v else None
variants={
 "V0 strict-all-tokens, town-scoped":      dict(cross_town=False, min_cover=1.0, need_rare=True),
 "V1 strict-all-tokens, cross-town":       dict(cross_town=True,  min_cover=1.0, need_rare=True),
 "V2 cover>=1.0 no rare-token req, town":  dict(cross_town=False, min_cover=1.0, need_rare=False),
 "V3 cover>=0.5 + rare token, town":       dict(cross_town=False, min_cover=0.5, need_rare=True),
 "V4 cover>=0.67 + rare, town":            dict(cross_town=False, min_cover=0.67, need_rare=True),
}
for name,kw in variants.items():
    out={}
    for split,ids in (("TRAIN",train),("VAL",val),("pool",set(pool))):
        e=[err(resolve(A[a].get("text_norm") or "", A[a]["town_id"], **kw), a) for a in ids]
        out[split]=(q(e,0.5), fr(e,500), fr(e,250), sum(1 for x in e if x is None))
    print(f"{name:40s} TRAIN med={out['TRAIN'][0]:7} <500={out['TRAIN'][1]} <250={out['TRAIN'][2]} none={out['TRAIN'][3]} | VAL med={out['VAL'][0]:7} <500={out['VAL'][1]} <250={out['VAL'][2]} none={out['VAL'][3]}")
# what does the CURRENT arm do, for reference (already measured): median 799.5 / 0.4555
# cross-town reality check: when text names an out-of-town locality, is truth nearer that town's locality?
print("\ncross-town cases (text names a locality only present in another town):")
n=0; e_intown_centroid=[]; e_xtown=[]
for a in pool:
    t=A[a].get("text_norm") or ""; t2=A[a]["town_id"]
    lid_in=resolve(t,t2,cross_town=False); lid_x=resolve(t,t2,cross_town=True)
    if lid_in is None and lid_x is not None:
        n+=1; e_xtown.append(err(lid_x,a))
print(f"  n={n} | out-of-town centroid error median={q(e_xtown,0.5)} <500={fr(e_xtown,500)}")
