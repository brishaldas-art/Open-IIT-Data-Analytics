import sys, csv, collections, statistics as st, re, json
sys.path.insert(0,"/home/user/PS3_SUTRA"); import os; os.chdir("/home/user/PS3_SUTRA")
from sutra import config, geo, splits, dataio
from sutra.candidates import generate
from sutra.indexes import get_index
from sutra.replay import _manifest, _proxy_truth
from sutra.store import Store
ix=get_index(); store=Store(); as_of=config.MOMENT
A=dataio.addresses(); L=dataio.localities(); LB={l["locality_id"]:l for l in L}
print("localities (36):")
for t in ("T1","T2","T3"):
    print(" ",t, " | ".join(f"{l['locality_id']}:{l['locality_name']}({l['pincode']})" for l in L if l["town_id"]==t))
man=_manifest(ix); pool=[a for a,m in sorted(man.items()) if m["split"] in (splits.S_TRAIN,splits.S_VAL)]
val=[a for a,m in sorted(man.items()) if m["split"]==splits.S_VAL]
T={a:_proxy_truth(store,a,as_of) for a in pool}
def strict_loc(t):
    """all name tokens present; prefer the longest match (deterministic)"""
    best=None
    for l in L:
        toks=[x for x in dataio.tokens(dataio.norm_text(l["locality_name"])) if len(x)>2]
        if toks and all(x in t for x in toks):
            k=(len(toks), l["locality_id"])
            if best is None or k>best[0]: best=(k,l["locality_id"])
    return best[1] if best else None
def arm_loc(cands):
    c=[x for x in cands if x["arm"]=="locality_centroid"]
    if not c: return None,None
    best=min(c,key=lambda x:geo.dist(float(x["x"]),float(x["y"]),float(LB[x["source_ref"].split(":")[1]]["centroid_x"]),float(LB[x["source_ref"].split(":")[1]]["centroid_y"])))
    return c[0]["source_ref"].split(":")[1], c
# compare: current arm choice vs strict text match, and their errors
agree=0; disagree=0; e_arm=[]; e_strict=[]; rows=[]
for a in pool:
    cands=[c for c in generate(a,as_of,store,ix=ix) if c["arm"] in config.STATIC_ARMS]
    lid_arm,_=arm_loc(cands); lid_strict=strict_loc(A[a].get("text_norm") or "")
    tx,ty=T[a]
    if lid_arm and lid_strict and lid_arm==lid_strict: agree+=1
    elif lid_strict: disagree+=1
    ea=geo.dist(float(LB[lid_arm]["centroid_x"]),float(LB[lid_arm]["centroid_y"]),tx,ty) if lid_arm else None
    es=geo.dist(float(LB[lid_strict]["centroid_x"]),float(LB[lid_strict]["centroid_y"]),tx,ty) if lid_strict else None
    e_arm.append(ea); e_strict.append(es)
    rows.append((a,lid_arm,lid_strict,ea,es))
def q(v,p): v=sorted(x for x in v if x is not None); return round(float(v[int(p*(len(v)-1))]),1) if v else None
def fr(v,thr): v=[x for x in v if x is not None]; return round(sum(1 for x in v if x<=thr)/len(v),4) if v else None
print(f"\npool n={len(pool)}: arm locality == strict text locality: {agree}; differ: {disagree}; arm none: {sum(1 for r in rows if r[1] is None)}; strict none: {sum(1 for r in rows if r[2] is None)}")
print(f"  ARM's chosen locality centroid : median={q(e_arm,0.5)} <500={fr(e_arm,500)} <250={fr(e_arm,250)}")
print(f"  STRICT text locality centroid  : median={q(e_strict,0.5)} <500={fr(e_strict,500)} <250={fr(e_strict,250)}")
print("  disagreements:")
for a,la,ls,ea,es in rows:
    if la!=ls and ls: print(f"    {a} arm={la}({ea and round(ea)}) strict={ls}({es and round(es)}) | {A[a]['address_text'][:70]}")
