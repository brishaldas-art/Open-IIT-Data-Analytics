import sys, csv, collections, statistics as st, json
sys.path.insert(0,"/home/user/PS3_SUTRA"); import os; os.chdir("/home/user/PS3_SUTRA")
from sutra import config, geo, splits, dataio, evidence
from sutra.indexes import get_index
from sutra.replay import _manifest
from sutra.store import Store
from sutra import asof
ix=get_index(); store=Store()
man=_manifest(ix); pool=[a for a,m in sorted(man.items()) if m["split"] in (splits.S_TRAIN,splits.S_VAL)]
# store observations
rows=store.rows("observations") if hasattr(store,"rows") else None
import sqlite3
con=sqlite3.connect("data/derived/runtime/sutra_store.sqlite"); con.row_factory=sqlite3.Row
obs=[dict(r) for r in con.execute("select * from observations order by address_id, observed_at")]
print("observations:", len(obs), "| cols:", list(obs[0].keys())[:12])
byA=collections.defaultdict(list)
for o in obs: byA[o["address_id"]].append(o)
print("addresses with observations:", len(byA), "| in pool:", sum(1 for a in pool if a in byA))
# how the evidence weights look: positives?
ev={r["observation_id"]:dict(r) for r in con.execute("select * from evidence")} if any(t[0]=="evidence" for t in con.execute("select name from sqlite_master where type='table'")) else {}
print("evidence rows:", len(ev), "| polarity mix:", collections.Counter(v.get("polarity") for v in ev.values()))
# temporal structure: promoted positives before/after a mid cut
def promoted(oids):
    out=[]
    for oid in oids:
        e=ev.get(oid)
        if e and e.get("polarity")=="positive" and float(e.get("weight") or 0)>=config.W_PROMOTE: out.append(oid)
    return out
for T0 in ("2026-05-01","2026-05-15","2026-06-01"):
    both=0; pre_only=0; post_only=0; spread=[]
    for a in pool:
        pre=[o for o in byA.get(a,[]) if o["observed_at"]<T0]; post=[o for o in byA.get(a,[]) if o["observed_at"]>=T0]
        pr=promoted([o["observation_id"] for o in pre]); po=promoted([o["observation_id"] for o in post])
        if pr and po: both+=1
        elif pr: pre_only+=1
        elif po: post_only+=1
    print(f"  T0={T0}: pool addresses with promoted-pre AND promoted-post={both}, pre-only={pre_only}, post-only={post_only}")
# what does the evidence weight mean: dwell/gps/timing policy
print("\nevidence policy constants:", {k:v for k,v in vars(config).items() if k.isupper() and ("W_" in k or "PERIOD" in k or "BAND" in k or "MIN" in k)})
# for addresses with promoted pre AND post: how far apart are the medians? (stability of field GPS)
d=[]
for a in pool:
    pre=[o for o in byA.get(a,[]) if o["observed_at"]<"2026-05-15" and o.get("x") is not None]
    post=[o for o in byA.get(a,[]) if o["observed_at"]>="2026-05-15" and o.get("x") is not None]
    pr=promoted([o["observation_id"] for o in pre]); po=promoted([o["observation_id"] for o in post])
    if len(pr)>=2 and po:
        px=geo.median([o["x"] for o in pre if o["observation_id"] in pr]); py=geo.median([o["y"] for o in pre if o["observation_id"] in pr])
        qx=geo.median([o["x"] for o in post if o["observation_id"] in po]); qy=geo.median([o["y"] for o in post if o["observation_id"] in po])
        d.append(geo.dist(px,py,qx,qy))
print(f"\npre->post median displacement (promoted, n={len(d)}): median={round(st.median(d),1)} p75={round(sorted(d)[int(.75*(len(d)-1))],1)} <100m={sum(1 for x in d if x<=100)/max(1,len(d)):.3f} <250={sum(1 for x in d if x<=250)/max(1,len(d)):.3f} <500={sum(1 for x in d if x<=500)/max(1,len(d)):.3f}")
