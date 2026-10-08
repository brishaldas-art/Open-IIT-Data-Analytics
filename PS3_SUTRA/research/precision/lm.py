import sys, csv, collections, statistics as st, math, re
sys.path.insert(0,"/home/user/PS3_SUTRA"); import os; os.chdir("/home/user/PS3_SUTRA")
from sutra import config, geo, splits, dataio
from sutra.indexes import get_index
from sutra.replay import _manifest, _proxy_truth
from sutra.store import Store
from sutra.preprocess import get as get_ring
ix=get_index(); store=Store(); as_of=config.MOMENT
A=dataio.addresses(); L=dataio.localities(); LM=dataio.landmarks()
man=_manifest(ix); pool=[a for a,m in sorted(man.items()) if m["split"] in (splits.S_TRAIN,splits.S_VAL)]
T={a:_proxy_truth(store,a,as_of) for a in pool}
ring=get_ring("B2")
def q(v,p): v=sorted(v); return round(float(v[int(p*(len(v)-1))]),1)
def fr(v,t): return round(sum(1 for x in v if x<=t)/len(v),4) if v else None
# mention vocabulary in addresses (relation windows)
kinds={"bus stop":"bus_stop","ಬಸ್ ಸ್ಟಾಪ್":"bus_stop","बस स्टॉप":"bus_stop","bus_stop":"bus_stop",
 "water tank":"water_tank","ಟ್ಯಾಂಕ್":"water_tank","टंकी":"water_tank","tanki":"water_tank","tank":"water_tank",
 "milk dairy":"milk_dairy","milk booth":"milk_dairy","doodh dairy":"milk_dairy","ಡೇರಿ":"milk_dairy",
 "medical store":"medical_store","medicals":"medical_store","medical shop":"medical_store","pharmacy":"medical_store",
 "मेडिकल":"medical_store","ಮೆಡಿಕಲ್":"medical_store",
 "ration shop":"ration_shop","ration dukan":"ration_shop","pds shop":"ration_shop","सरकारी राशन":"ration_shop",
 "गणपति":"ganesha_temple","ganesh temple":"ganesha_temple","ganapathi temple":"ganesha_temple","ganapathi gudi":"ganesha_temple","ganesh mandir":"ganesha_temple","ganesha":"ganesha_temple",
 "hanuman temple":"hanuman_temple","hanuman mandir":"hanuman_temple","ಆಂಜನೇಯ":"hanuman_temple",
 "masjid":"masjid","mosque":"masjid","मस्जिद":"masjid","ಮಸೀದಿ":"masjid",
 "church":"church","ಚರ್ಚ್":"church","चर्च":"church",
 "community hall":"community_hall","kalyana mantapa":"community_hall","kalyan mantapa":"community_hall",
 "govt school":"govt_school","government school":"govt_school","sarkari school":"govt_school","sarkari school ke pass":"govt_school","children park":"park","park":"park",
 "post office":"post_office","dak ghar":"post_office","petrol bunk":"petrol_bunk","petrol pump":"petrol_bunk","ಪೆಟ್ರೋಲ್":"petrol_bunk"}
POI=collections.defaultdict(list)
for r in LM: POI[r["town_id"]].append(r)
# locate reference POI for each address = nearest POI of the mentioned kind to the TRUTH (upper bound)
hit_any=0; hit_unique_loc=0; n=0; dmin=[]; n_multi=0; loc_of_best=[]
for a in pool:
    t=ring.match_text(A[a]); rel,before,after=ring.relation_windows(t)
    if rel is None: continue
    window=set(before)|set(after)|set(dataio.tokens(t))
    kinds_here=sorted({k for k in kinds if k in t})
    if not kinds_here: continue
    n+=1
    kmax=max(kinds_here,key=len); typ=kinds[kmax]
    cands=POI[A[a]["town_id"]]
    same=[p for p in cands if p["landmark_type"]==typ]
    if not same: continue
    d=[(geo.dist(float(p["x"]),float(p["y"]),*T[a]),p) for p in same]
    d.sort(key=lambda x:x[0])
    dmin.append(d[0][0])
    if d[0][0]<=250: hit_any+=1
    # unique within the resolved locality?  (use nearest-locality of the POI vs of the address by truth)
    best=d[0][1]
print(f"addresses with a recognisable landmark mention: {n}/{len(pool)}")
print(f"  nearest POI of the mentioned type (town-scoped) to TRUTH: median={q(dmin,0.5)} <250m={fr(dmin,250)} <500m={fr(dmin,500)}")
# how many same-type POIs per town (ambiguity scale)
amb=collections.Counter((p["town_id"],p["landmark_type"]) for p in LM)
print("  same-type POIs per town: median", st.median(amb.values()), "max", max(amb.values()))
# uniqueness within a locality: assign each POI to nearest locality; count same-type POIs per (locality,type)
byt=collections.defaultdict(list)
for p in LM:
    nl=min(L,key=lambda l:geo.dist(float(p["x"]),float(p["y"]),float(l["centroid_x"]),float(l["centroid_y"])))
    byt[(nl["locality_id"],p["landmark_type"])].append(p["poi_id"])
cnt=collections.Counter(len(v) for v in byt.values())
print("  same-type POIs per (nearest locality, type):", sorted(cnt.items()))
# is the truth nearest to the SAME locality as the best POI?
ok=0; tot=0
for a in pool:
    t=ring.match_text(A[a]); rel,before,after=ring.relation_windows(t)
    if rel is None: continue
    kinds_here=sorted({k for k in kinds if k in t})
    if not kinds_here: continue
    typ=kinds[max(kinds_here,key=len)]
    same=[p for p in POI[A[a]["town_id"]] if p["landmark_type"]==typ]
    if not same: continue
    best=min(same,key=lambda p:geo.dist(float(p["x"]),float(p["y"]),*T[a]))
    nearL=lambda x,y: min(L,key=lambda l:geo.dist(x,y,float(l["centroid_x"]),float(l["centroid_y"])))["locality_id"]
    tot+=1; ok+= (nearL(float(best["x"]),float(best["y"]))==nearL(*T[a]))
print(f"  the truth's nearest locality == the best POI's nearest locality: {ok}/{tot} = {ok/max(1,tot):.3f}")
