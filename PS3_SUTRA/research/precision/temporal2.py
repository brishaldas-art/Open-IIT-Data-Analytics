import sys, collections, statistics as st, sqlite3, json
sys.path.insert(0,"/home/user/PS3_SUTRA"); import os; os.chdir("/home/user/PS3_SUTRA")
from sutra import config, geo, splits
from sutra.indexes import get_index
from sutra.replay import _manifest
con=sqlite3.connect("data/derived/runtime/sutra_store.sqlite"); con.row_factory=sqlite3.Row
O=[dict(r) for r in con.execute("select * from observations")]
E={r["observation_id"]:dict(r) for r in con.execute("select * from evidence_scores")}
ix=get_index(); man=_manifest(ix)
pool=[a for a,m in sorted(man.items()) if m["split"] in (splits.S_TRAIN,splits.S_VAL)]
byA=collections.defaultdict(list)
for o in O: byA[o["address_id"]].append(o)
print("observations:", len(O), "| dates:", min(o["observed_at"] for o in O)[:10], "->", max(o["observed_at"] for o in O)[:10])
print("evidence weights: positives:", sum(1 for e in E.values() if e["polarity"]=="positive"),
      "| >= W_PROMOTE:", sum(1 for e in E.values() if e["polarity"]=="positive" and float(e["weight"])>=config.W_PROMOTE))
print("outcome mix by polarity:", collections.Counter((o["outcome"], E[o["observation_id"]]["polarity"]) for o in O).most_common(8))
def med(rows):
    return (geo.median([r["x"] for r in rows]), geo.median([r["y"] for r in rows]))
for T0 in ("2026-05-01","2026-05-15","2026-06-01"):
    stat=collections.Counter(); disp=[]
    for a in pool:
        pre=[o for o in byA.get(a,[]) if o["observed_at"][:10]<T0]
        post=[o for o in byA.get(a,[]) if o["observed_at"][:10]>=T0]
        pr=[o for o in pre if E[o["observation_id"]]["polarity"]=="positive" and float(E[o["observation_id"]]["weight"])>=config.W_PROMOTE and o["x"] is not None]
        po=[o for o in post if E[o["observation_id"]]["polarity"]=="positive" and float(E[o["observation_id"]]["weight"])>=config.W_PROMOTE and o["x"] is not None]
        if len(pr)>=2 and po:
            stat["both"]+=1; disp.append(geo.dist(*med(pr),*med(po)))
        elif len(pr)>=2: stat["pre_only"]+=1
        elif po: stat["post_only"]+=1
        else: stat["neither"]+=1
    if disp:
        d=sorted(disp); q=lambda p: round(float(d[int(p*(len(d)-1))]),1)
        print(f"T0={T0}: both={stat['both']} pre_only={stat['pre_only']} post_only={stat['post_only']} neither={stat['neither']}"
              f" | pre->post displacement n={len(d)} med={q(.5)} p75={q(.75)} <100={sum(1 for x in d if x<=100)/len(d):.3f} <250={sum(1 for x in d if x<=250)/len(d):.3f} <500={sum(1 for x in d if x<=500)/len(d):.3f}")
    else:
        print(f"T0={T0}: both={stat['both']} pre_only={stat['pre_only']} post_only={stat['post_only']} neither={stat['neither']}")
# gps accuracy distribution + dwell
acc=[o["gps_accuracy_m"] for o in O if o["gps_accuracy_m"] is not None]
print("\ngps_accuracy_m: median", round(st.median(acc),1), "p90", round(sorted(acc)[int(.9*(len(acc)-1))],1))
