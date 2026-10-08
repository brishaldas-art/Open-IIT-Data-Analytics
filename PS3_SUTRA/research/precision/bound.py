import sys, csv, collections, statistics as st
sys.path.insert(0,"/home/user/PS3_SUTRA"); import os; os.chdir("/home/user/PS3_SUTRA")
from sutra import config, geo, splits, dataio
from sutra.indexes import get_index
from sutra.replay import _manifest, _proxy_truth
from sutra.store import Store
ix=get_index(); store=Store(); as_of=config.MOMENT
A=dataio.addresses(); L=dataio.localities(); LM=dataio.landmarks()
man=_manifest(ix); pool=[a for a,m in sorted(man.items()) if m["split"] in (splits.S_TRAIN,splits.S_VAL)]
TRAIN={a for a,m in man.items() if m["split"]==splits.S_TRAIN}; VAL={a for a,m in man.items() if m["split"]==splits.S_VAL}
T={a:_proxy_truth(store,a,as_of) for a in pool}
PINS={}
with open("data/official_ps3/baseline_geocodes.csv",encoding="utf-8",newline="") as fh:
    for r in csv.DictReader(fh): PINS[r["address_id"]]=(float(r["geocoder_x"]),float(r["geocoder_y"]),r["precision"])
LOCP=[(float(l["centroid_x"]),float(l["centroid_y"]),l["locality_id"],l["town_id"]) for l in L]
POIP=[(float(p["x"]),float(p["y"]),p["poi_id"]) for p in LM]
def q(v,p): v=sorted(v); return round(float(v[int(p*(len(v)-1))]),1)
def fr(v,t): return round(sum(1 for x in v if x<=t)/len(v),4)
res={}
for name,pts in (("own pin",1),("town-scoped locality centres",2),("all locality centres (cheat)",3),
                 ("all POIs (cheat)",4),("all other pins (cheat)",5)):
    pass
rows=[]
for a in pool:
    tx,ty=T[a]
    own=geo.dist(PINS[a][0],PINS[a][1],tx,ty) if a in PINS else None
    lc=min(geo.dist(x,y,tx,ty) for x,y,_,t in LOCP if t==A[a]["town_id"])
    lcall=min(geo.dist(x,y,tx,ty) for x,y,_,_ in LOCP)
    poi=min(geo.dist(x,y,tx,ty) for x,y,_ in POIP)
    pins=min(geo.dist(x,y,tx,ty) for b,(x,y,_) in PINS.items() if b!=a)
    rows.append(dict(a=a,own=own,lc=lc,lcall=lcall,poi=poi,pins=pins,
                     best=min(x for x in (own,lc,lcall,poi,pins) if x is not None)))
for k,label in (("own","own vendor pin only"),("lc","+/- best town-scoped locality centre"),
                ("lcall","+ ANY locality centre"),("poi","+ ANY POI"),("pins","+ ANY other address's pin"),
                ("best","= best over ALL official points (absolute bound)")):
    v=[r[k] for r in rows]
    vt=[r[k] for r in rows if r["a"] in TRAIN]; vv=[r[k] for r in rows if r["a"] in VAL]
    print(f"{label:44s} pool med={q(v,0.5):7} <500={fr(v,500)} | S-TRAIN <500={fr(vt,500)} | S-VAL <500={fr(vv,500)} med={q(vv,0.5)}")
print("\nper-row: how many need something beyond the pin+locality?")
need=[r for r in rows if min(r["own"],r["lc"])>500]
print(f"  rows where pin AND town locality are both >500m: {len(need)} (pool {len(rows)})")
print(f"  ... of those, could any POI fix it (<500m)? {sum(1 for r in need if r['poi']<=500)}")
print(f"  ... of those, could another address's pin fix it? {sum(1 for r in need if r['pins']<=500)}")
print(f"  ... of those, could ANY locality centre fix it? {sum(1 for r in need if r['lcall']<=500)}")
print("  rows where the pin alone is >500 but a town locality centre is <=500:", sum(1 for r in rows if r["own"]>500 and r["lc"]<=500))
print("  rows where the pin is <=500 but the bias could be improved:", sum(1 for r in rows if r["own"]<=500))
# distribution of the *best achievable* error (absolute bound over official points)
b=[r["best"] for r in rows]
print(f"\nABSOLUTE BOUND over every official point (pin/any centre/any POI/any other pin): median={q(b,0.5)} <100={fr(b,100)} <250={fr(b,250)} <500={fr(b,500)}")
