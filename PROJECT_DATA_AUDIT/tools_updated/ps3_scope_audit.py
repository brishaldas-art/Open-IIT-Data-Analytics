#!/usr/bin/env python3
"""
PS3 official data-scope re-audit (2026-10-07).
Reads ONLY the official CreditNirvana pack (PS3-specific + shared tables).
Writes: PROJECT_DATA_AUDIT/data/official_ps3/ (hash-verified canonical copy),
        PROJECT_DATA_AUDIT/data/derived/*.csv + updated_eda_report.txt
No external data. No PS1/PS2-only tables are read for any PS3 statistic.
"""
import os, sys, json, time, hashlib, re
import numpy as np
import pandas as pd

t0 = time.time()
ROOT = "/home/user/PROJECT_DATA_AUDIT"
PS3SRC = "/home/user/PS3_SUTRA/data/official_ps3/"
arc = "/home/user/90_Archive/ps2_removed_2026-10-06/PS2_SANKET_full/data/raw/"
OFF = os.path.join(ROOT, "data", "official_ps3")
DER = os.path.join(ROOT, "data", "derived")
CLN = os.path.join(ROOT, "data", "cleaned")
for d in (OFF, DER, CLN):
    os.makedirs(d, exist_ok=True)

# ── 0. canonical DATASET A: PS3-specific + officially PS3-relevant shared ──────
SCOPE = [
    # (file, group, source)
    ("towns.csv",               "ps3_specific", PS3SRC + "towns.csv"),
    ("localities.csv",          "ps3_specific", PS3SRC + "localities.csv"),
    ("landmarks_poi.csv",       "ps3_specific", PS3SRC + "landmarks_poi.csv"),
    ("baseline_geocodes.csv",   "ps3_specific", PS3SRC + "baseline_geocodes.csv"),
    ("visit_gps_points.csv",    "ps3_specific", PS3SRC + "visit_gps_points.csv"),
    ("surveyed_addresses.csv",  "ps3_specific", PS3SRC + "surveyed_addresses.csv"),
    ("accounts.csv",            "shared",       PS3SRC + "accounts.csv"),
    ("addresses.csv",           "shared",       PS3SRC + "addresses.csv"),
    ("agents.csv",              "shared",       PS3SRC + "agents.csv"),
    ("field_visits.csv",        "shared",       PS3SRC + "field_visits.csv"),
    ("lenders.csv",             "shared",       arc + "lenders.csv"),
    ("splits.csv",              "shared",       PS3SRC + "splits.csv"),
]

def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()

receipts = []
for name, group, src in SCOPE:
    dst = os.path.join(OFF, name)
    if not os.path.exists(dst) or sha(dst) != sha(src):
        with open(src, "rb") as f, open(dst, "wb") as g:
            g.write(f.read())
    receipts.append(dict(file=name, group=group, source_path=src, sha256=sha(dst),
                         bytes=os.path.getsize(dst)))
pd.DataFrame(receipts).to_csv(os.path.join(DER, "updated_scope_receipts.csv"), index=False)
print(f"[scope] canonical DATASET A materialised: {len(SCOPE)} tables -> {OFF}")

D = {n[:-4]: pd.read_csv(os.path.join(OFF, n), low_memory=False) for n, _, _ in SCOPE}

# ── 1. profile every table in scope ───────────────────────────────────────────
rows = []
for n, d in D.items():
    pk = d.columns[0]
    nulls = {c: round(100 * d[c].isna().mean(), 1) for c in d.columns if d[c].isna().any()}
    dr = ""
    for c in d.columns:
        if "date" in c or "_ts" in c:
            s = pd.to_datetime(d[c], errors="coerce")
            dr = f"{s.min()} .. {s.max()}"
            break
    rows.append(dict(table=n, rows=len(d), cols=d.shape[1], key=pk,
                     dup_key=int(d.duplicated(pk).sum()), dup_rows=int(d.duplicated().sum()),
                     null_cols=";".join(f"{k}={v}%" for k, v in nulls.items()), date_range=dr))
prof = pd.DataFrame(rows).sort_values("table")
prof.to_csv(os.path.join(DER, "updated_table_profile.csv"), index=False)
print("\n[profile]\n" + prof[["table", "rows", "cols", "dup_key", "dup_rows"]].to_string(index=False))

# ── 2. foreign keys, both directions ──────────────────────────────────────────
fk = []
def chk(child, cc, parent, pc):
    if child not in D or parent not in D:
        return
    L, R = set(D[child][cc].dropna()), set(D[parent][pc].dropna())
    fk.append(dict(child=f"{child}.{cc}", parent=f"{parent}.{pc}",
                   orphans=len(L - R), values_checked=len(L)))
for a, b in [("addresses", "account_id|accounts|account_id"), ("addresses", "town_id|towns|town_id"),
             ("accounts", "lender_id|lenders|lender_id"), ("accounts", "town_id|towns|town_id"),
             ("field_visits", "address_id|addresses|address_id"), ("field_visits", "account_id|accounts|account_id"),
             ("field_visits", "agent_id|agents|agent_id"), ("visit_gps_points", "visit_id|field_visits|visit_id"),
             ("splits", "account_id|accounts|account_id"), ("baseline_geocodes", "address_id|addresses|address_id"),
             ("surveyed_addresses", "address_id|addresses|address_id"), ("localities", "town_id|towns|town_id"),
             ("landmarks_poi", "town_id|towns|town_id"), ("agents", "town_id|towns|town_id")]:
    cc, p, pc = b.split("|")
    chk(a, cc, p, pc)
fkdf = pd.DataFrame(fk)
fkdf.to_csv(os.path.join(DER, "updated_fk_checks.csv"), index=False)
print("\n[foreign keys] orphans:", {r["child"]: int(r["orphans"]) for _, r in fkdf.iterrows()})

# ── 3. join chain + splits (entity leakage checks) ───────────────────────────
ad, ac, fv, sp = D["addresses"], D["accounts"], D["field_visits"], D["splits"]
chain = ad.merge(sp, on="account_id", how="left").merge(ac[["account_id", "dpd_start", "portfolio", "preferred_language"]], on="account_id", how="left")
chain.to_csv(os.path.join(DER, "updated_address_split_chain.csv"), index=False)
print("\n[split] addresses per split:", chain["split"].value_counts().to_dict())
vsplit = fv.merge(sp, on="account_id", how="left")
print("[split] visits per split:", vsplit["split"].value_counts().to_dict(),
      "| distinct addresses per split:", vsplit.groupby("split")["address_id"].nunique().to_dict())
sv = D["surveyed_addresses"].merge(chain[["address_id", "split"]], on="address_id", how="left")
print("[split] the 100 surveyed truths by split:", sv["split"].value_counts(dropna=False).to_dict())

# ── 4. place identity: normalised text, near-duplicates, same building ────────
def norm(t):
    t = str(t).lower()
    t = re.sub(r"\s*-\s*\d{6}\s*$", "", t)              # trailing pincode tail
    t = re.sub(r"[^0-9a-z\u0900-\u0D7F]+", " ", t)      # keep alnum + Indic blocks
    return re.sub(r"\s+", " ", t).strip()

ad_ = ad.copy()
ad_["norm"] = ad_["address_text"].map(norm)
g = ad_.groupby("norm").agg(n=("address_id", "size"), accts=("account_id", "nunique"),
                            towns=("town_id", "nunique")).reset_index()
gd = g[g.n > 1].merge(ad_[["address_id", "account_id", "town_id", "address_type", "norm"]], on="norm")
gd = gd.merge(sp, on="account_id", how="left")
gd.to_csv(os.path.join(DER, "updated_place_duplicate_groups.csv"), index=False)
print(f"\n[place] identical normalised texts: {len(gd)} rows in {gd['norm'].nunique()} groups; "
      f"groups spanning >1 account: {int((g[g.n>1].accts>1).sum())}; groups spanning >1 town: {int((g[g.n>1].towns>1).sum())}")
sp_pairs = gd.groupby("norm")["split"].apply(lambda s: s.dropna().nunique())
print(f"[place] identical-text groups crossing >1 split: {int((sp_pairs>1).sum())} "
      f"(rows involved: {int(gd[gd['norm'].isin(sp_pairs[sp_pairs>1].index)].shape[0])})")
print("[place] duplicate-group address_type mix:", gd["address_type"].value_counts().to_dict())

# token-level near duplicates (Jaccard >= 0.80), split awareness
tok = ad_.set_index("address_id")["norm"].map(lambda s: set(s.split()))
ids = list(tok.index)
doc_sets = [tok[i] for i in ids]
idx = {i: k for k, i in enumerate(ids)}
size = {k: len(doc_sets[k]) for k in idx.values()}
inverted = {}
for k, s in enumerate(doc_sets):
    for w in s:
        inverted.setdefault(w, []).append(k)
from collections import defaultdict
pair = defaultdict(int)
for w, ks in inverted.items():
    if len(ks) > 400:
        continue
    for a in range(len(ks)):
        for b in range(a + 1, len(ks)):
            pair[(ks[a], ks[b])] += 1
near = []
for (a, b), inter in pair.items():
    union = size[a] + size[b] - inter
    j = inter / union if union else 0
    if j >= 0.80:
        near.append((ids[a], ids[b], round(j, 3), inter, union))
near = pd.DataFrame(near, columns=["address_id_a", "address_id_b", "jaccard", "inter", "union"])
near = near.merge(ad_[["address_id", "account_id"]], left_on="address_id_a", right_on="address_id",
                  how="left").rename(columns={"account_id": "account_a"}).drop(columns=["address_id"])
near = near.merge(ad_[["address_id", "account_id"]], left_on="address_id_b", right_on="address_id",
                  how="left").rename(columns={"account_id": "account_b"}).drop(columns=["address_id"])
near = near.merge(sp, left_on="account_a", right_on="account_id", how="left").rename(columns={"split": "split_a"}).drop(columns=["account_id"])
near = near.merge(sp, left_on="account_b", right_on="account_id", how="left").rename(columns={"split": "split_b"}).drop(columns=["account_id"])
near["same_account"] = near.account_a == near.account_b
near.to_csv(os.path.join(DER, "updated_near_duplicate_pairs.csv"), index=False)
print(f"[place] J>=0.80 pairs: {len(near)}; same account: {int(near.same_account.sum())}; "
      f"cross-account: {int((~near.same_account).sum())}; crossing splits: {int((near.split_a != near.split_b).sum())}")

# ── 5. multiple accounts / addresses per place: check-in proximity ───────────
met = fv[fv.outcome.isin(["met_borrower", "met_family", "cash_collected"])]
c = met.groupby("address_id").agg(cx=("checkin_x", "mean"), cy=("checkin_y", "mean"), visits=("visit_id", "size")).reset_index()
P = c[["cx", "cy"]].to_numpy(float)
A = c["address_id"].to_numpy()
n = len(P)
close = []
for i in range(n):
    d2 = np.hypot(P[:, 0] - P[i, 0], P[:, 1] - P[i, 1])
    for j in np.where((d2 > 0) & (d2 <= 30))[0]:
        if j > i:
            close.append((A[i], A[j], round(float(d2[j]), 1)))
cl = pd.DataFrame(close, columns=["address_id_a", "address_id_b", "metres"])
cl.to_csv(os.path.join(DER, "updated_cross_address_proximity.csv"), index=False)
print(f"\n[place] met-check-in pairs within 30 m across DIFFERENT addresses: {len(cl)} "
      f"involving {len(set(cl.address_id_a) | set(cl.address_id_b)) if len(cl) else 0} addresses "
      f"(of {n} addresses with a met visit)")

# ── 6. remarks: what survives in free text ───────────────────────────────────
rm = fv["remark"].astype(str)
loc_names = set(D["localities"]["locality_name"].str.lower())
lm_names = set(D["landmarks_poi"]["name"].str.lower())
lm_types = set(D["landmarks_poi"]["landmark_type"].str.lower().str.replace("_", " "))
digit = rm.str.contains(r"\d")
nonzero = rm.str.contains(r"[^\s]", na=False)
indic = rm.str.contains(r"[\u0900-\u0D7F]")
loc_hit = rm.map(lambda s: any(l in s.lower() for l in loc_names))
lm_hit = rm.map(lambda s: any(l in s.lower() for l in lm_names | lm_types))
shift = rm.str.contains(r"shift|moved|kalla|badal", case=False, na=False)
empty = rm.str.strip().eq("")
prof_rm = dict(visits=len(rm), empty=int(empty.sum()), with_digits=int(digit.sum()),
               locality_named=int(loc_hit.sum()), landmark_named=int(lm_hit.sum()),
               indic_script=int(indic.sum()), relocation_words=int(shift.sum()),
               distinct=int(rm.nunique()))
print("\n[remark]", prof_rm)
print("[remark] top repeated:", rm.value_counts().head(8).to_dict())
by_out = fv.assign(has_loc=loc_hit, has_lm=lm_hit).groupby("outcome")[["has_loc", "has_lm"]].mean().round(3)
by_out.to_csv(os.path.join(DER, "updated_remark_by_outcome.csv"))
print("[remark] locality named by outcome:\n", (100 * by_out["has_loc"]).round(1).to_string())

# ── 7. lender KYC format vs address style ────────────────────────────────────
lk = ad.merge(ac[["account_id", "lender_id"]], on="account_id").merge(D["lenders"], on="lender_id")
style = lk.assign(non_ascii=lk.address_text.str.contains(r"[^\x00-\x7F]"),
                  tail=lk.address_text.str.contains(r"-\s*\d{6}\s*$", regex=True),
                  house=lk.address_text.str.contains(r"(?i)\b(house|plot|door|flat|no\.?|#)\b", regex=True),
                  length=lk.address_text.str.len())
st = style.groupby("kyc_address_format").agg(n=("address_id", "size"), non_ascii=("non_ascii", "mean"),
                                             pincode_tail=("tail", "mean"), house_marker=("house", "mean"),
                                             median_len=("length", "median")).round(3)
st.to_csv(os.path.join(DER, "updated_lender_style.csv"))
print("\n[lender style]\n", st.to_string())

# ── 8. agents & field coverage ───────────────────────────────────────────────
ag = fv.merge(D["agents"], on="agent_id", how="left")
cov = ag.groupby(["agent_id", "channel"]).agg(visits=("visit_id", "size"), addresses=("address_id", "nunique")).reset_index()
cov.to_csv(os.path.join(DER, "updated_agent_coverage.csv"), index=False)
print("\n[agents] visits by channel:", ag.groupby("channel")["visit_id"].size().to_dict(),
      "| field agents:", ag[ag.channel == "field"]["agent_id"].nunique(),
      "| visits per field agent range:", ag[ag.channel == "field"].groupby("agent_id").size().agg(["min", "max"]).to_dict())
print("[agents] town_id present for field agents:",
      D["agents"][D["agents"].channel == "field"]["town_id"].notna().mean().round(2))

# ── 9. visit selection bias & yield (PS3 scope only) ─────────────────────────
ch = fv.merge(chain[["address_id", "split", "dpd_start", "portfolio", "preferred_language", "address_type"]],
              on="address_id", how="left")
ch["met"] = ch.outcome.isin(["met_borrower", "met_family", "cash_collected"])
ch["nt"] = ch.outcome.eq("address_not_traceable")
ch["dpd_band"] = pd.cut(ch.dpd_start, [-1, 30, 90, 180, 360, 721],
                        labels=["0-30", "31-90", "91-180", "181-360", "361+"])
sel = ch.groupby("dpd_band", observed=True).agg(visits=("visit_id", "size"), met=("met", "mean"),
                                                not_traceable=("nt", "mean")).round(3)
sel.to_csv(os.path.join(DER, "updated_selection_bias.csv"))
print("\n[selection] by DPD band:\n", sel.to_string())
print("[selection] by address_type:",
      ch.groupby("address_type").agg(v=("visit_id", "size"), met=("met", "mean")).round(3).to_dict())
print("[selection] by portfolio:",
      ch.groupby("portfolio").agg(v=("visit_id", "size"), met=("met", "mean")).round(3).to_dict())
first = ch.sort_values("visit_date").groupby("address_id").head(1)
later = ch.drop(first.index)
print(f"[selection] first visits {len(first)} met {first.met.mean():.3f} | later {len(later)} met {later.met.mean():.3f}")

# ── 10. values / outcomes in scope ───────────────────────────────────────────
print("\n[outcomes] visit outcome mix:", fv.outcome.value_counts(normalize=True).round(3).to_dict())

# ── 11. temporal ─────────────────────────────────────────────────────────────
ad_days = pd.to_datetime(ad.added_date)
first_v = fv.assign(d=pd.to_datetime(fv.visit_date)).groupby("address_id")["d"].min()
lag = (first_v.reindex(ad.set_index("address_id").index).values - ad_days.values)
lag = pd.Series(pd.to_timedelta(lag)).dt.days.dropna()
print(f"\n[temporal] added_date->first visit lag: median {lag.median()} d, p90 {lag.quantile(.9)} d")
print("[temporal] window:", pd.to_datetime(ad.added_date).min().date(), "->",
      pd.to_datetime(fv.visit_date).max().date(), "| distinct visit dates:", fv.visit_date.nunique())

# ── 12. text structure quick re-baseline (PS3 scope) ─────────────────────────
at = ad.address_text
print("\n[text] median len:", int(at.str.len().median()), "| trailing pincode tail:",
      int(at.str.contains(r"-\s*\d{6}\s*$").sum()), "| non-ascii:", int(at.str.contains(r"[^\x00-\x7F]").sum()),
      "| comma-free:", int((~at.str.contains(",")).sum()))

run = time.time() - t0
print(f"\n[done] audit runtime {run:.1f}s, peak RSS {int(open('/proc/self/status').read().split('VmHWM:')[1].split()[0])/1024:.0f} MB")
with open(os.path.join(DER, "updated_eda_runtime.txt"), "w") as f:
    f.write(f"runtime_s={run:.1f}\n")
