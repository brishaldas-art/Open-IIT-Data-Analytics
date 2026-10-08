"""Temporal holdout: candidates built from evidence < T0, label = promoted evidence >= T0. Non-circular."""
import sys, collections, statistics as st, sqlite3, json
sys.path.insert(0,"/home/user/PS3_SUTRA"); import os; os.chdir("/home/user/PS3_SUTRA")
from sutra import config, geo, splits, dataio, ranking
from sutra.candidates import generate, field_evidence_candidates, memory_candidates
from sutra.indexes import get_index
from sutra.replay import _manifest
from sutra.store import Store
ix=get_index(); store=Store(); as_of=config.MOMENT
A=dataio.addresses()
man=_manifest(ix); pool=sorted(a for a,m in sorted(man.items()) if m["split"] in (splits.S_TRAIN,splits.S_VAL))
con=sqlite3.connect("data/derived/runtime/sutra_store.sqlite"); con.row_factory=sqlite3.Row
O=[dict(r) for r in con.execute("select * from observations")]
E={r["observation_id"]:dict(r) for r in con.execute("select * from evidence_scores")}
byA=collections.defaultdict(list)
for o in O: byA[o["address_id"]].append(o)
def promoted(o): return E[o["observation_id"]]["polarity"]=="positive" and float(E[o["observation_id"]]["weight"])>=config.W_PROMOTE and o["x"] is not None
def med(rows): return (geo.median([r["x"] for r in rows]), geo.median([r["y"] for r in rows]))
def q(v,p): v=sorted(v); return round(float(v[int(p*(len(v)-1))]),1) if v else None
def fr(v,t): return round(sum(1 for x in v if x<=t)/len(v),4) if v else None
# ---- the warm candidate at T0: reuse the shipped machine (asof gate) ----
def warm_cand(a, T0):
    ev=field_evidence_candidates(a, T0, store)          # consolidated median (>=2 agreeing promoted)
    mem=memory_candidates(a, T0, store)                 # prequential belief candidate
    strong=[c for c in ev if c.get("provenance",{}).get("primary_eligible")]
    if strong: return strong[0], "field_evidence_median"
    if ev: return ev[0], "field_evidence_single"
    if mem: return mem[0], "memory"
    return None, None
def static_cand(a):
    cs=[c for c in generate(a, as_of, store, ix=ix) if c["arm"] in config.STATIC_ARMS]
    f=ranking.features_matrix(ix.addresses[a],cs,ix); rk=ranking.rank(cs,f,as_of)
    return {c["candidate_id"]:c for c in cs}[rk[0]["candidate_id"]]
for T0 in ("2026-05-01","2026-05-15"):
    rows=[]
    for a in pool:
        post=[o for o in byA.get(a,[]) if o["observed_at"][:10]>=T0 and promoted(o)]
        if not post: continue
        label=med(post)
        c,src=warm_cand(a,T0)
        s=static_cand(a)
        wx,wy = (c["x"],c["y"]) if c else (None,None)
        rows.append(dict(a=a,src=src,warm=geo.dist(wx,wy,*label) if c else None,
                         static=geo.dist(s["x"],s["y"],*label), n_post=len(post)))
    print(f"\nT0={T0} · label = promoted check-in median >= T0 (future evidence, never used as input)")
    print(f"  addresses with a post-T0 label: {len(rows)}")
    for lbl,key in (("COLD (pin/rule at as_of)", "static"), ("WARM (as-of evidence)", "warm")):
        v=[r[key] for r in rows if r[key] is not None]
        print(f"    {lbl:26s} n={len(v):3d} <100={fr(v,100)} <250={fr(v,250)} <500={fr(v,500)} median={q(v,.5)} p75={q(v,.75)} p90={q(v,.9)}")
    print("  warm candidate source:", collections.Counter(r["src"] for r in rows).most_common())
    # warm where available, cold otherwise = the shipped product behaviour
    mix=[r["warm"] if r["warm"] is not None else r["static"] for r in rows]
    print(f"    {'PRODUCT (warm→cold fallback)':26s} n={len(mix):3d} <100={fr(mix,100)} <250={fr(mix,250)} <500={fr(mix,500)} median={q(mix,.5)}")
    sub=[r for r in rows if r["src"]=="field_evidence_median"]
    if sub:
        v=[r["warm"] for r in sub]
        print(f"    {'  > where >=2 promoted pre':26s} n={len(v):3d} <100={fr(v,100)} <250={fr(v,250)} <500={fr(v,500)} median={q(v,.5)}")
        v2=[r["static"] for r in sub]
        print(f"    {'  > same rows, COLD':26s} n={len(v2):3d} <100={fr(v2,100)} <250={fr(v2,250)} <500={fr(v2,500)} median={q(v2,.5)}")
