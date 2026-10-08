"""Can a learned ranker exploit the v2 candidate set? Fit on S-TRAIN, judge on S-VAL + grouped OOF."""
import sys, collections, statistics as st, numpy as np
sys.path.insert(0,"/home/user/PS3_SUTRA"); import os; os.chdir("/home/user/PS3_SUTRA")
from sutra import config, geo, splits, dataio, ranking, learning, stats
from sutra.candidates import generate
from sutra.indexes import get_index
from sutra.replay import _manifest, _proxy_truth
from sutra.store import Store
ix=get_index(); store=Store(); as_of=config.MOMENT
man=_manifest(ix); pool=sorted(a for a,m in sorted(man.items()) if m["split"] in (splits.S_TRAIN,splits.S_VAL))
TRAIN=sorted(a for a,m in man.items() if m["split"]==splits.S_TRAIN); VAL=sorted(a for a,m in man.items() if m["split"]==splits.S_VAL)
T={a:_proxy_truth(store,a,as_of) for a in pool}
FOLD={a:ix.place_blocks[a]["fold"] if a in ix.place_blocks else 0 for a in pool}
def build(a):
    cs=[c for c in generate(a,as_of,store,ix=ix) if c["arm"] in config.STATIC_ARMS]
    f=ranking.features_matrix(ix.addresses[a],cs,ix)
    return cs,f
DATA={a:build(a) for a in pool}
def rows_for(ids):
    fr=[];y=[];g=[]
    for a in ids:
        cs,f=DATA[a]
        for c in cs:
            fr.append(f[c["candidate_id"]]); y.append(float(learning.grade_of(geo.dist(c["x"],c["y"],*T[a])))); g.append(a)
    return fr,np.array(y),g
def top1_metrics(name, ids, scorer):
    errs=[]; 
    for a in ids:
        cs,f=DATA[a]
        order=scorer(a,cs,f)
        c=next(x for x in cs if x["candidate_id"]==order[0]["candidate_id"])
        errs.append(geo.dist(c["x"],c["y"],*T[a]))
    s=sorted(errs); q=lambda p: round(float(s[int(p*(len(s)-1))]),1)
    return dict(name=name,n=len(ids),h100=round(sum(1 for x in errs if x<=100)/len(errs),4),
                h250=round(sum(1 for x in errs if x<=250)/len(errs),4),h500=round(sum(1 for x in errs if x<=500)/len(errs),4),
                med=q(.5),errs=errs)
rule_scorer=lambda a,cs,f: ranking.rank(cs,f,as_of)
print("R-VAL top-1 with the shipped rule, v2 candidate set:", {k:v for k,v in top1_metrics("RULE",VAL,rule_scorer).items() if k!="errs"})
# fit challengers on S-TRAIN
fr,y,g=rows_for(TRAIN); frv,yv,gv=rows_for(VAL)
res={}
for kind in ("logistic","lambdamart","pairwise"):
    m=learning.fit_model(kind, fr, y, g, feature_rows_val=frv, y_val=yv, groups_val=gv)
    sc=lambda a,cs,f,m=m: learning.rank_with(m,cs,f,as_of)
    mtr=top1_metrics(kind,VAL,sc)
    res[kind]=(m,mtr)
    print(f"  {kind:10s} S-VAL top-1: {[ (k,mtr[k]) for k in ('h100','h250','h500','med')]}")
# paired bootstrap vs RULE on S-VAL
r=top1_metrics("RULE",VAL,rule_scorer)
for kind,(m,mtr) in res.items():
    d=stats.paired_grouped_ci([1.0 if x<=500 else 0.0 for x in mtr["errs"]],[1.0 if x<=500 else 0.0 for x in r["errs"]],
                              [ix.block_of(a) for a in VAL],stat="mean",resamples=10000,seed=7,direction="higher_is_better")
    rev=stats.paired_grouped_ci([1.0 if x<=500 else 0.0 for x in r["errs"]],[1.0 if x<=500 else 0.0 for x in mtr["errs"]],
                              [ix.block_of(a) for a in VAL],stat="mean",resamples=10000,seed=7,direction="higher_is_better")
    print(f"  {kind:10s} vs RULE <500: {d['point_delta']:+.4f} [{d['lo']:+.4f},{d['hi']:+.4f}] challenger_resolved={d['resolved']} rule_resolved={rev['resolved']}")
# grouped OOF over the pool: 5 spatial folds, inner early stopping = other folds
print("\ngrouped OOF over the pool (5 spatial folds):")
folds=sorted(set(FOLD.values()))
oof={k:{} for k in ("RULE","logistic","lambdamart","pairwise")}
for fo in folds:
    tr=[a for a in pool if FOLD[a]!=fo]; te=[a for a in pool if FOLD[a]==fo]
    fr,y,g=rows_for(tr)
    # inner early-stopping: hold out one other fold
    other=[a for a in tr if FOLD[a]!=sorted(set(FOLD[a2] for a2 in tr))[0]]
    frv,yv,gv=rows_for(other)
    for k in ("logistic","lambdamart","pairwise"):
        m=learning.fit_model(k, fr, y, g, feature_rows_val=frv, y_val=yv, groups_val=gv)
        for a in te:
            cs,f=DATA[a]; order=learning.rank_with(m,cs,f,as_of)
            c=next(x for x in cs if x["candidate_id"]==order[0]["candidate_id"])
            oof[k][a]=geo.dist(c["x"],c["y"],*T[a])
    for a in te:
        cs,f=DATA[a]; order=ranking.rank(cs,f,as_of)
        c=next(x for x in cs if x["candidate_id"]==order[0]["candidate_id"])
        oof["RULE"][a]=geo.dist(c["x"],c["y"],*T[a])
for k,d in oof.items():
    e=list(d.values()); s=sorted(e)
    print(f"  {k:10s} n={len(e)} <100={sum(1 for x in e if x<=100)/len(e):.4f} <250={sum(1 for x in e if x<=250)/len(e):.4f} <500={sum(1 for x in e if x<=500)/len(e):.4f} med={round(float(s[len(s)//2]),1)}")
for k in ("logistic","lambdamart","pairwise"):
    va=[1.0 if oof[k][a]<=500 else 0.0 for a in pool]; vb=[1.0 if oof["RULE"][a]<=500 else 0.0 for a in pool]
    d=stats.paired_grouped_ci(va,vb,[ix.block_of(a) for a in pool],stat="mean",resamples=10000,seed=7,direction="higher_is_better")
    print(f"  OOF {k:10s} vs RULE <500: {d['point_delta']:+.4f} [{d['lo']:+.4f},{d['hi']:+.4f}] resolved={d['resolved']}")
