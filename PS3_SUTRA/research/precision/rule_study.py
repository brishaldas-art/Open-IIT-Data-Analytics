"""Selection-rule study on the static lane (fit on S-TRAIN, confirm on S-VAL)."""
import sys, csv, collections, statistics as st, math, re
sys.path.insert(0,"/home/user/PS3_SUTRA"); import os; os.chdir("/home/user/PS3_SUTRA")
from sutra import config, geo, splits, dataio, ranking, stats
from sutra.candidates import generate, make_candidate, _apply_landmark_plausibility, annotate_agreement
from sutra.indexes import get_index
from sutra.replay import _manifest, _proxy_truth
from sutra.store import Store
ix=get_index(); store=Store(); as_of=config.MOMENT
A=dataio.addresses(); L=dataio.localities(); LB={l["locality_id"]:l for l in L}
man=_manifest(ix); pool=[a for a,m in sorted(man.items()) if m["split"] in (splits.S_TRAIN,splits.S_VAL)]
TRAIN=sorted(a for a,m in man.items() if m["split"]==splits.S_TRAIN); VAL=sorted(a for a,m in man.items() if m["split"]==splits.S_VAL)
T={a:_proxy_truth(store,a,as_of) for a in pool}
tok=collections.Counter(); nd=0
for a,r in A.items():
    if r["added_date"]<"2026-06-01":
        nd+=1
        for t in set(dataio.tokens(r.get("text_norm") or "")): tok[t]+=1
def idf(t): return math.log((nd+1)/(tok.get(t,0)+1))+1.0
LT={l["locality_id"]:[t for t in dataio.tokens(dataio.norm_text(l["locality_name"]))] for l in L}
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
CACHE={}
def cands(a, v):
    key=(a,v)
    if key in CACHE: return CACHE[key]
    out=[c for c in generate(a,as_of,store,ix=ix) if c["arm"] in config.STATIC_ARMS]
    if v=="v2":
        out=[c for c in out if c["arm"]!="locality_centroid"]
        lid=resolve(A[a].get("text_norm") or "", A[a]["town_id"])
        if lid:
            l=LB[lid]
            out.append(make_candidate(a,"locality_centroid",f"locality:{lid}",float(l["centroid_x"]),float(l["centroid_y"]),
                       "locality",{"built_from":"localities.csv","match":"idf_token_match","stratum":"locality"},None))
    out=_apply_landmark_plausibility(out); out=annotate_agreement(out)
    out.sort(key=lambda c:(config.ARMS.index(c["arm"]) if c["arm"] in config.ARMS else 99, c.get("arm_rank",1), c["source_ref"], c["candidate_id"]))
    CACHE[key]=out; return out
def feats(a,cands): return ranking.features_matrix(ix.addresses[a],cands,ix)
def dist(a,c): return geo.dist(c["x"],c["y"],*T[a])
# ── selection rules ─────────────────────────────────────────────────────────────────────────────
def rule_A(a,cands,f):         # shipped rule
    rk=ranking.rank(cands,f,as_of); return {c["candidate_id"]:c for c in cands}[rk[0]["candidate_id"]]
def rule_B(a,cands,f):         # pin demotion when the pin is pincode-coarse AND another arm agrees nearby
    byid={c["candidate_id"]:c for c in cands}; rk=ranking.rank(cands,f,as_of)
    top=byid[rk[0]["candidate_id"]]
    if top["arm"]=="frozen_baseline" and top.get("provenance",{}).get("baseline_precision")=="pincode":
        for r in rk[1:]:
            c=byid[r["candidate_id"]]
            if c["arm"]!="frozen_baseline" and geo.dist(c["x"],c["y"],top["x"],top["y"])<=800: return c
    return top
def rule_C(a,cands,f):         # agreement-first: prefer a candidate with >=1 agreeing arm, then the rule
    byid={c["candidate_id"]:c for c in cands}; rk=ranking.rank(cands,f,as_of)
    for r in rk:
        c=byid[r["candidate_id"]]
        if f[c["candidate_id"]].get("f_agreement_count",0)>=1 and c["arm"]!="town_centroid": return c
    return byid[rk[0]["candidate_id"]]
def rule_D(a,cands,f):         # closest to the medoid of the *spatial* candidate set (agreement consensus)
    pts=[c for c in cands if c["arm"]!="town_centroid"] or cands
    mx=geo.median([c["x"] for c in pts]); my=geo.median([c["y"] for c in pts])
    byid={c["candidate_id"]:c for c in cands}; rk=ranking.rank(cands,f,as_of)
    best=None
    for r in rk:
        c=byid[r["candidate_id"]]
        k=(round(geo.dist(c["x"],c["y"],mx,my),3), rk.index(r))
        if best is None or k<best[0]: best=(k,c)
    return best[1]
def rule_E(a,cands,f,W):       # hand-parameterised score, fitted on S-TRAIN only
    import itertools
    best=None
    for c in cands:
        fc=f[c["candidate_id"]]
        gran={"rooftop":1.0,"street":0.85,"locality":0.6,"town":0.25}.get(c["granularity"],0.25)
        strat=c.get("provenance",{}).get("baseline_precision") or c.get("provenance",{}).get("stratum")
        pinpen=0.0
        if c["arm"]=="frozen_baseline":
            pinpen = {"pincode":W["pen_pin_pincode"],"locality":W["pen_pin_locality"]}.get(strat,0.0)
        s=(W["arm"].get(c["arm"],0.2)+W["gran"]*gran+W["agree"]*min(fc.get("f_agreement_count",0),2)
           - pinpen + W["sim"]*fc.get("f_sim_jaccard",0.0))
        k=(-round(s,6), c["candidate_id"])
        if best is None or k<best[0]: best=(k,c)
    return best[1]
W0=dict(arm={"frozen_baseline":0.50,"official_landmark":0.45,"address_book":0.42,"locality_centroid":0.38,"town_centroid":0.15},
        gran=0.12, agree=0.06, sim=0.05, pen_pin_pincode=0.06, pen_pin_locality=0.06)
def evals(name, ids, v, rule):
    errs=[]; arms=collections.Counter()
    for a in ids:
        cs=cands(a,v); f=feats(a,cs)
        c=rule(a,cs,f)
        e=dist(a,c); errs.append(e); arms[c["arm"]]+=1
    def q(p): s=sorted(errs); return round(float(s[int(p*(len(s)-1))]),1)
    def fr(t): return round(sum(1 for x in errs if x<=t)/len(errs),4)
    return dict(name=name,n=len(ids),med=q(.5),h100=fr(100),h250=fr(250),h500=fr(500),arms=dict(arms))
COMBOS=[("v1 + rule",  "v1", rule_A),("v2 + rule","v2",rule_A),("v2 + pin-demote","v2",rule_B),
        ("v2 + agreement-first","v2",rule_C),("v2 + medoid","v2",rule_D),
        ("v1 + medoid","v1",rule_D),("v1 + agreement-first","v1",rule_C)]
print(f"{'rule':26s} {'split':6s} {'n':>3s} {'<100':>6s} {'<250':>6s} {'<500':>6s} {'median':>7s}   arms")
for name,v,rule in COMBOS:
    for split,ids in (("TRAIN",TRAIN),("VAL",VAL)):
        r=evals(name,ids,v,rule)
        print(f"{r['name']:26s} {split:6s} {r['n']:3d} {r['h100']:6.4f} {r['h250']:6.4f} {r['h500']:6.4f} {r['med']:7.1f}   {r['arms']}")
