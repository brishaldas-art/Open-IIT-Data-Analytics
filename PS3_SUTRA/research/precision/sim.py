"""Retrieval-v2 simulation: improved locality resolution + pin-demotion policy.
   Evaluated with the frozen protocol on S-TRAIN (fit) and S-VAL (confirm)."""
import sys, csv, collections, statistics as st, math, json
sys.path.insert(0,"/home/user/PS3_SUTRA"); import os; os.chdir("/home/user/PS3_SUTRA")
from sutra import config, geo, ranking, splits, dataio
from sutra.candidates import (generate, make_candidate, _frozen_baseline, _town_centroid,
                              town_centroids)
from sutra.indexes import get_index
from sutra.replay import _manifest, _proxy_truth
from sutra.store import Store
ix=get_index(); store=Store(); as_of=config.MOMENT
A=dataio.addresses(); L=dataio.localities(); LB={l["locality_id"]:l for l in L}
man=_manifest(ix); pool=[a for a,m in sorted(man.items()) if m["split"] in (splits.S_TRAIN,splits.S_VAL)]
TRAIN={a for a,m in man.items() if m["split"]==splits.S_TRAIN}; VAL={a for a,m in man.items() if m["split"]==splits.S_VAL}
T={a:_proxy_truth(store,a,as_of) for a in pool}
# ── IDF over official addresses added before the cut (as-of clean) ──────────────────────────────
tok_freq=collections.Counter(); n_docs=0
for a,r in A.items():
    if r["added_date"] < "2026-06-01":
        n_docs+=1
        for t in set(dataio.tokens(r.get("text_norm") or "")): tok_freq[t]+=1
def idf(t): return math.log((n_docs+1)/(tok_freq.get(t,0)+1))+1.0
LOC_TOKS={l["locality_id"]:[t for t in dataio.tokens(dataio.norm_text(l["locality_name"]))] for l in L}
def resolve_v2(text, town):
    toks=set(dataio.tokens(text))
    if not toks: return None,None
    best=None
    for lid,ltoks in sorted(LOC_TOKS.items()):
        if not ltoks or LB[lid]["town_id"]!=town: continue
        present=[t for t in ltoks if t in toks]
        if not present: continue
        cover=len(present)/len(ltoks)
        rare=min(ltoks,key=lambda t:(tok_freq.get(t,0),t))
        if cover<0.5 or rare not in toks: continue
        score=round(sum(idf(t) for t in present),6)
        key=(-round(cover,6),-score,-len(ltoks),lid)
        if best is None or key<best[0]: best=(key,lid,present,cover,score)
    return (best[1],dict(cover=round(best[3],3),idf_sum=best[4],tokens=best[2])) if best else (None,None)
def cands_v2(aid):
    addr=ix.addresses[aid]; out=[]
    out+=_frozen_baseline(aid, {aid: dataio.baseline(aid)} if hasattr(dataio,'baseline') else {}, as_of) if False else []
    out+=[c for c in generate(aid,as_of,store,ix=ix)
          if c["arm"] in config.STATIC_ARMS and c["arm"]!="locality_centroid"]   # COLD lane only
    lid,why=resolve_v2(addr.get("text_norm") or "", addr["town_id"])
    if lid:
        l=LB[lid]
        out.append(make_candidate(aid,"locality_centroid",f"locality:{lid}", float(l["centroid_x"]),float(l["centroid_y"]),
                    "locality",{"built_from":"localities.csv","match":"idf_token_match","stratum":"locality",
                                "retrieval":"v2", **{k:v for k,v in (why or {}).items()}}, None))
    from sutra.candidates import _apply_landmark_plausibility, annotate_agreement
    out=_apply_landmark_plausibility(out); out=annotate_agreement(out)
    out.sort(key=lambda c:(config.ARMS.index(c["arm"]) if c["arm"] in config.ARMS else 99,
                           c.get("arm_rank",1), c["source_ref"], c["candidate_id"]))
    return out
def top1(aid,cands,policy):
    feats=ranking.features_matrix(ix.addresses[aid],cands,ix); rk=ranking.rank(cands,feats,as_of)
    byid={c["candidate_id"]:c for c in cands}
    if policy=="demote_pincode_pin":
        first=byid[rk[0]["candidate_id"]]
        if first["arm"]=="frozen_baseline" and first.get("provenance",{}).get("baseline_precision")=="pincode":
            for r in rk[1:]:
                c=byid[r["candidate_id"]]
                if c["arm"]!="frozen_baseline": return c
    return byid[rk[0]["candidate_id"]]
def err(c,aid): return geo.dist(c["x"],c["y"],*T[aid])
def q(v,p): v=sorted(v); return round(float(v[int(p*(len(v)-1))]),1)
def fr(v,thr): return round(sum(1 for x in v if x<=thr)/len(v),4)
def evaluate(name, ids, builder, policy):
    rows={}
    for aid in ids:
        cands=builder(aid)
        t1=top1(aid,cands,policy)
        errs=[err(c,aid) for c in cands]
        rows[aid]=dict(t1=err(t1,aid), arm=t1["arm"], oracle=min(errs), ncand=len(cands))
    t1=[r["t1"] for r in rows.values()]; orc=[r["oracle"] for r in rows.values()]
    print(f"  {name:34s} n={len(ids):3d} top1<500={fr(t1,500)} <250={fr(t1,250)} <100={fr(t1,100)} med={q(t1,0.5):7.1f} | oracle<500={fr(orc,500)} med={q(orc,0.5):7.1f}")
    return rows
v1=lambda a: [c for c in generate(a,as_of,store,ix=ix) if c["arm"] in config.STATIC_ARMS]
print("retrieval v1 (shipped) vs v2 (IDF locality resolver), frozen rule:")
print(" S-TRAIN:")
r1t=evaluate("R1 v1 + rule", sorted(TRAIN), v1, "none")
r2t=evaluate("R2 v2 + rule", sorted(TRAIN), cands_v2, "none")
r3t=evaluate("R3 v2 + demote pincode pin", sorted(TRAIN), cands_v2, "demote_pincode_pin")
print(" S-VAL:")
r1v=evaluate("R1 v1 + rule", sorted(VAL), v1, "none")
r2v=evaluate("R2 v2 + rule", sorted(VAL), cands_v2, "none")
r3v=evaluate("R3 v2 + demote pincode pin", sorted(VAL), cands_v2, "demote_pincode_pin")
print("\npaired bootstrap vs R1 (S-VAL, place-block groups, 10k):")
from sutra import stats
def paired(ra,rb,key="hit500"):
    va=[];vb=[];gr=[]
    for a in sorted(VAL):
        x=1.0 if ra[a]["t1"]<=500 else 0.0; y=1.0 if rb[a]["t1"]<=500 else 0.0
        va.append(x);vb.append(y);gr.append(ix.block_of(a))
    d=stats.paired_grouped_ci(va,vb,gr,stat="mean",resamples=10000,seed=7,direction="higher_is_better")
    rev=stats.paired_grouped_ci(vb,va,gr,stat="mean",resamples=10000,seed=7,direction="higher_is_better")
    return d,rev
for nm,rx in (("R2",r2v),("R3",r3v)):
    d,rev=paired(rx,r1v)
    print(f"  {nm} vs R1 <500: {d['point_delta']:+.4f} [{d['lo']:+.4f},{d['hi']:+.4f}] resolved={d['resolved']} | mirror(resolved)={rev['resolved']}")
# also: median top-1 error paired
for nm,rx in (("R2",r2v),("R3",r3v)):
    va=[rx[a]["t1"] for a in sorted(VAL)]; vb=[r1v[a]["t1"] for a in sorted(VAL)]; gr=[ix.block_of(a) for a in sorted(VAL)]
    d=stats.paired_grouped_ci(va,vb,gr,stat="median",resamples=10000,seed=7,direction="lower_is_better")
    print(f"  {nm} vs R1 median err: {d['point_delta']:+.1f} [{d['lo']:+.1f},{d['hi']:+.1f}] resolved={d['resolved']}")
