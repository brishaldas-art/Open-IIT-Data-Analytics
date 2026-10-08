import sys, csv, collections, statistics as st, re, json
sys.path.insert(0,"/home/user/PS3_SUTRA"); import os; os.chdir("/home/user/PS3_SUTRA")
from sutra import config, geo, ranking, splits, dataio
from sutra.candidates import generate
from sutra.indexes import get_index
from sutra.replay import _manifest, _proxy_truth
from sutra.store import Store
ix=get_index(); store=Store(); as_of=config.MOMENT
man=_manifest(ix); A=dataio.addresses()
train=[a for a,m in sorted(man.items()) if m["split"]==splits.S_TRAIN]
val=[a for a,m in sorted(man.items()) if m["split"]==splits.S_VAL]
pool=train+val
def q(v,p): v=sorted(v); return round(float(v[int(p*(len(v)-1))]),1)
def row(aid):
    tx,ty=_proxy_truth(store,aid,as_of); addr=ix.addresses[aid]
    cands=[c for c in generate(aid,as_of,store,ix=ix) if c["arm"] in config.STATIC_ARMS]
    feats=ranking.features_matrix(addr,cands,ix); rk=ranking.rank(cands,feats,as_of)
    top=next(c for c in cands if c["candidate_id"]==rk[0]["candidate_id"])
    err={c["candidate_id"]:geo.dist(c["x"],c["y"],tx,ty) for c in cands}
    return dict(aid=aid,cands=cands,err=err,top=top,top_err=err[top["candidate_id"]],
                oracle=min(err.values()),pinprec=top.get("provenance",{}).get("baseline_precision"))
R={a:row(a) for a in pool}
def frac(rows,thr): return round(sum(1 for r in rows if r["top_err"]<=thr)/len(rows),4)
print("── top-1 by pin precision class (pool) ──")
for cls in ("locality","street","rooftop","pincode",None):
    rr=[r for r in R.values() if r["pinprec"]==cls]
    if rr: print(f"  pin={str(cls):9s} n={len(rr):3d} top-1<500={frac(rr,500)} oracle<500={round(sum(1 for r in rr if r['oracle']<=500)/len(rr),4)} median={q([r['top_err'] for r in rr],0.5)}")
print("\n── S-VAL detail by class ──")
V=[R[a] for a in val]
for cls in ("locality","street","rooftop","pincode"):
    rr=[r for r in V if r["pinprec"]==cls]
    if rr: print(f"  pin={cls:9s} n={len(rr):3d} top-1<500={frac(rr,500)} median={q([r['top_err'] for r in rr],0.5)}")
print("\n── SIMULATION W1: when the pin is pincode-precision, take the best non-pin candidate ──")
def sim(ids, only_pincode=True):
    fixed=0; broke=0; gains=[]
    for a in ids:
        r=R[a]; 
        if only_pincode and r["pinprec"]!="pincode": continue
        alt=[c for c in r["cands"] if c["arm"]!="frozen_baseline"]
        if not alt: continue
        best=min(alt,key=lambda c:(r["err"][c["candidate_id"]],c["candidate_id"]))
        if r["err"][best["candidate_id"]] < r["top_err"]-1e-9:
            fixed+=1; gains.append(r["top_err"]-r["err"][best["candidate_id"]])
        elif r["err"][best["candidate_id"]] > r["top_err"]+1e-9: broke+=1
    return fixed,broke,gains
for name,ids in (("S-TRAIN",train),("S-VAL",val),("pool",pool)):
    f,b,g=sim(ids); base=sum(1 for a in ids if R[a]["top_err"]<=500)/len(ids)
    pc=[a for a in ids if R[a]["pinprec"]=="pincode"]
    if pc:
        after=sum(1 for a in ids if (R[a]["top_err"]<=500) or (R[a]["pinprec"]=="pincode" and min(R[a]["err"][c["candidate_id"]] for c in R[a]["cands"] if c["arm"]!="frozen_baseline")<=500))
        print(f"  {name:8s} pincode-pins={len(pc):3d} fixed={f} broken={b} → top-1<500 {base:.4f} → {after/len(ids):.4f}")
    else: print(f"  {name:8s} no pincode pins")
print("\n── which non-pin arm is best for pincode-pin rows? ──")
c=collections.Counter(); e=[]
for a in pool:
    r=R[a]
    if r["pinprec"]!="pincode": continue
    alt=[x for x in r["cands"] if x["arm"]!="frozen_baseline"]
    e.append(r["top_err"])
    if alt:
        b=min(alt,key=lambda x:(r["err"][x["candidate_id"]],x["candidate_id"])); c[b["arm"]]+=1; e.append(r["err"][b["candidate_id"]])
print("  best alt arm:",c.most_common(),"| pin err median:",q(e[0::2],0.5),"alt err median:",q(e[1::2],0.5) if len(e)>1 else None)
print("\n── arm availability + error on the pool (any candidate of that arm) ──")
for arm in config.STATIC_ARMS:
    rr=[(a,r) for a,r in R.items() if any(c["arm"]==arm for c in r["cands"])]
    if rr:
        errs=[r["err"][next(c["candidate_id"] for c in r["cands"] if c["arm"]==arm)] for a,r in rr]
        print(f"  {arm:18s} present={len(rr):3d}/{len(pool)} median_err_when_present={q(errs,0.5):7.1f} <500={round(sum(1 for x in errs if x<=500)/len(errs),3)}")
    else: print(f"  {arm:18s} present=0")
print("\n── the 35 retrieval failures (oracle>500m): what are they? ──")
f=[r for r in R.values() if r["oracle"]>500]
print("  n:",len(f), "| pin precision:",collections.Counter(r["pinprec"] for r in f).most_common())
for r in sorted(f,key=lambda r:-r["oracle"])[:12]:
    a=A[r["aid"]]
    print(f"   {r['aid']} pin={str(r['pinprec']):8s} pin_err={r['top_err']:7.0f} oracle={r['oracle']:7.0f} ncand={len(r['cands'])} | {a['address_text'][:74]}")
