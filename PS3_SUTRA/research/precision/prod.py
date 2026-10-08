import sys, collections, statistics as st
sys.path.insert(0,"/home/user/PS3_SUTRA"); import os; os.chdir("/home/user/PS3_SUTRA")
from sutra import config, geo, splits, dataio, ranking
from sutra.candidates import generate
from sutra.indexes import get_index
from sutra.replay import _manifest, _proxy_truth
from sutra.store import Store
ix=get_index(); store=Store(); as_of=config.MOMENT
A=dataio.addresses(); L=dataio.localities(); LB={l["locality_id"]:l for l in L}
man=_manifest(ix); pool=[a for a,m in sorted(man.items()) if m["split"] in (splits.S_TRAIN,splits.S_VAL)]
TRAIN=sorted(a for a,m in man.items() if m["split"]==splits.S_TRAIN); VAL=sorted(a for a,m in man.items() if m["split"]==splits.S_VAL)
T={a:_proxy_truth(store,a,as_of) for a in pool}
def build(a, ver):
    config.RETRIEVAL_VERSION=ver
    return [c for c in generate(a,as_of,store,ix=ix) if c["arm"] in config.STATIC_ARMS]
def t1(cands,a):
    f=ranking.features_matrix(ix.addresses[a],cands,ix); rk=ranking.rank(cands,f,as_of)
    return {c["candidate_id"]:c for c in cands}[rk[0]["candidate_id"]]
def q(v,p): v=sorted(v); return round(float(v[int(p*(len(v)-1))]),1)
def fr(v,t): return round(sum(1 for x in v if x<=t)/len(v),4)
for ver in ("v1","v2"):
    locerr=[]; top=[]; orc=[]; nc=[]; pincode_multi=0
    for a in pool:
        cs=build(a,ver)
        loc=[c for c in cs if c["arm"]=="locality_centroid"]
        if loc: locerr.append(min(geo.dist(float(LB[c["source_ref"].split(":")[1]]["centroid_x"]),float(LB[c["source_ref"].split(":")[1]]["centroid_y"]),*T[a]) for c in loc))
        pincode_multi += sum(1 for c in loc if c.get("provenance",{}).get("ambiguous_pincode"))
        top.append(geo.dist(t1(cs,a)["x"],t1(cs,a)["y"],*T[a]))
        orc.append(min(geo.dist(c["x"],c["y"],*T[a]) for c in cs)); nc.append(len(cs))
    print(f"{ver}: locality-candidate err (best) n={len(locerr)} med={q(locerr,.5)} <500={fr(locerr,500)} <250={fr(locerr,250)} | top-1 med={q(top,.5)} <500={fr(top,500)} | oracle med={q(orc,.5)} <500={fr(orc,500)} | cand/addr={q(nc,.5)} | ambiguous-pincode rows={pincode_multi}")
for ver in ("v1","v2"):
    for nm,ids in (("TRAIN",TRAIN),("VAL",VAL)):
        top=[geo.dist(*[(c:=t1(build(a,ver),a))["x"],c["y"]],*T[a]) for a in ids]
        orc=[min(geo.dist(x["x"],x["y"],*T[a]) for x in build(a,ver)) for a in ids]
        print(f"  {ver} {nm}: top-1 <500={fr(top,500)} <250={fr(top,250)} <100={fr(top,100)} med={q(top,.5)} | oracle <500={fr(orc,500)} med={q(orc,.5)}")
config.RETRIEVAL_VERSION="v2"
