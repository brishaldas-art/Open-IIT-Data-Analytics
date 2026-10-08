"""Official-data-only script bridge: learn Kannada/Devanagari token -> Latin token from co-occurrence
inside official addresses, then re-resolve the script-script rows and measure."""
import sys, collections, math, statistics as st
sys.path.insert(0,"/home/user/PS3_SUTRA"); import os; os.chdir("/home/user/PS3_SUTRA")
from sutra import config, geo, splits, dataio
from sutra.indexes import get_index
from sutra.replay import _manifest, _proxy_truth
from sutra.candidates import generate
from sutra.store import Store
ix=get_index(); store=Store(); man=_manifest(ix)
pool=sorted(a for a,m in man.items() if m["split"] in (splits.S_TRAIN,splits.S_VAL))
A=ix.addresses
def script(t): 
    return "k" if any(0x0C80<=ord(c)<=0x0CFF for c in t) else ("d" if any(0x0900<=ord(c)<=0x097F for c in t) else "l")
def toks(t):
    return [x for x in dataio.norm_text(t).split() if x]
def is_latin(t): return all(ord(c)<0x0900 for c in t)
# co-occurrence within the same address (a bilingual address states the same place twice)
co=collections.defaultdict(collections.Counter)
for r in A.values():
    ts=toks(r.get("address_text",""))
    ind=[t for t in ts if not is_latin(t)]; lat=[t for t in ts if is_latin(t) and not t.isdigit() and len(t)>2]
    for i in ind:
        for l in lat: co[i][l]+=1
print("foreign-script tokens seen in official addresses:", len(co))
print("example lexical entries:")
for i,(k,v) in enumerate(sorted(co.items(), key=lambda kv:-sum(kv[1].values()))[:6]):
    print(f"   {k} -> {v.most_common(4)}")
# same-town restriction (a token means the same place inside a town)
co_town=collections.defaultdict(collections.Counter)
for r in A.values():
    ts=toks(r.get("address_text","")); ind=[t for t in ts if not is_latin(t)]
    lat=[t for t in ts if is_latin(t) and not t.isdigit() and len(t)>2]
    for i in ind:
        for l in lat: co_town[(r["town_id"],i)][l]+=1
LOC={l["locality_id"]:dataio.norm_text(l["locality_name"]).split() for l in ix.localities}
LB={l["locality_id"]:l for l in ix.localities}
def resolve(town, tokens, extra):
    best=None
    for lid,lt in LOC.items():
        if LB[lid]["town_id"]!=town or not lt: continue
        pres=[t for t in lt if t in tokens or (t in extra)]
        if not pres: continue
        cov=len(pres)/len(lt)
        if cov<0.5: continue
        key=(-round(cov,6), lid)
        if best is None or key<best[0]: best=(key,lid)
    return best[1] if best else None
def current_lid(a):
    cs=[c for c in generate(a,config.MOMENT,store,ix=ix) if c["arm"]=="locality_centroid"
        and not c.get("provenance",{}).get("ambiguous_pincode")]
    return cs[0]["source_ref"].split(":")[1] if cs else None
rows=[a for a in pool if script(A[a].get("address_text",""))!="l"]
print(f"\npool rows in a non-Latin script: {len(rows)}")
gain=new_lid=hits=0; before=[]; after=[]
for a in rows:
    tx,ty=_proxy_truth(store,a,config.MOMENT)
    town=A[a]["town_id"]; ts=toks(A[a].get("address_text",""))
    extra=set()
    for t in ts:
        if not is_latin(t):
            entry=co_town.get((town,t)) or co[t]
            if entry: extra.update([tok for tok,_ in entry.most_common(2)])
    lid_now=current_lid(a); lid_new=resolve(town,set(ts),extra)
    e_now=geo.dist(float(LB[lid_now]["centroid_x"]),float(LB[lid_now]["centroid_y"]),tx,ty) if lid_now else None
    e_new=geo.dist(float(LB[lid_new]["centroid_x"]),float(LB[lid_new]["centroid_y"]),tx,ty) if lid_new else None
    if lid_new: new_lid+=1
    if e_now is not None and e_new is not None:
        before.append(e_now); after.append(e_new)
        if e_new+50<e_now: gain+=1
print(f"  resolved by the lexicon path: {new_lid}/{len(rows)} | compared on {len(before)} rows")
if before:
    def q(v,p): v=sorted(v); return round(float(v[int(p*(len(v)-1))]),1)
    print(f"  current resolution: med={q(before,.5)} m <500={sum(1 for x in before if x<=500)/len(before):.2f}")
    print(f"  lexicon resolution: med={q(after,.5)} m <500={sum(1 for x in after if x<=500)/len(after):.2f}")
    print(f"  lexicon better by >50 m on {gain} of {len(before)}")
