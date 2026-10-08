import sys, csv, collections, statistics as st, math
sys.path.insert(0,"/home/user/PS3_SUTRA"); import os; os.chdir("/home/user/PS3_SUTRA")
from sutra import config, geo, splits, dataio
from sutra.candidates import generate
from sutra.indexes import get_index
from sutra.replay import _manifest, _proxy_truth
from sutra.store import Store
ix=get_index(); store=Store(); as_of=config.MOMENT
A=dataio.addresses(); L=dataio.localities(); LB={l["locality_id"]:l for l in L}
man=_manifest(ix); pool=[a for a,m in sorted(man.items()) if m["split"] in (splits.S_TRAIN,splits.S_VAL)]
spl={a:m["split"] for a,m in man.items()}
T={a:_proxy_truth(store,a,as_of) for a in pool}
BG={}
with open("data/official_ps3/baseline_geocodes.csv",encoding="utf-8",newline="") as fh:
    for r in csv.DictReader(fh): BG[r["address_id"]]=r
def q(v,p): v=sorted(v); return round(float(v[int(p*(len(v)-1))]),1)
print("the 21 pincode-precision-pin rows in the pool:")
print(f"{'addr':10s} {'split':6s} {'pin_err':>8s} {'textpin':>8s} {'resolved':10s} {'ctr_err':>8s} | address")
rows=[]
for a in pool:
    if BG[a]["precision"]!="pincode": continue
    tx,ty=T[a]; pe=geo.dist(float(BG[a]["geocoder_x"]),float(BG[a]["geocoder_y"]),tx,ty)
    txt=A[a].get("text_norm") or ""
    # resolved locality via the v1 arm for now
    c=[x for x in generate(a,as_of,store,ix=ix) if x["arm"]=="locality_centroid"]
    lid=c[0]["source_ref"].split(":")[1] if c else None
    ce=geo.dist(float(LB[lid]["centroid_x"]),float(LB[lid]["centroid_y"]),tx,ty) if lid else None
    d_pc=geo.dist(float(BG[a]["geocoder_x"]),float(BG[a]["geocoder_y"]),float(LB[lid]["centroid_x"]),float(LB[lid]["centroid_y"])) if lid else None
    rows.append((a,spl[a],pe,ce,d_pc,lid))
    print(f"{a:10s} {spl[a]:6s} {pe:8.0f} {'':8s} {str(lid):10s} {ce and round(ce):>8} | {A[a]['address_text'][:66]}")
print("\nwhen is the centroid better than the pin? (pool pincode rows)")
for a,s,pe,ce,dpc,lid in rows:
    print(f"  {a} pin={pe:6.0f} ctr={ce:6.0f} {'CTR' if ce<pe else 'PIN'}  |pin-ctr|={dpc:7.0f}  textpin={dataio.pin_in_text(A[a]['address_text'])} pin_row={BG[a].get('precision')}")
print("\nrule candidate: choose centroid when |pin - centroid| > T; fit T on S-TRAIN")
tr=[r for r in rows if r[1]=="S_TRAIN"]; va=[r for r in rows if r[1]=="S_VAL"]
for T_ in (300,600,1000,1500):
    fix_tr=sum(1 for a,s,pe,ce,dpc,lid in tr if dpc>T_ and ce<pe); brk_tr=sum(1 for a,s,pe,ce,dpc,lid in tr if dpc>T_ and ce>=pe)
    fix_va=sum(1 for a,s,pe,ce,dpc,lid in va if dpc>T_ and ce<pe); brk_va=sum(1 for a,s,pe,ce,dpc,lid in va if dpc>T_ and ce>=pe)
    print(f"  T={T_:4d} TRAIN fire={fix_tr+brk_tr:2d} fix={fix_tr} break={brk_tr} | VAL fire={fix_va+brk_va:2d} fix={fix_va} break={brk_va}")
