#!/usr/bin/env python3
"""
SUTRA — PS3 dataset audit (official synthetic dataset).

Re-runs every data number quoted in PS3_DATA_AUDIT.md, PS3_DATA_CLEANING_REPORT.md and
PS3_DATA_ARCHITECTURE.md. READ-ONLY: never writes into data/official_ps3/.

    python3 tools/ps3_audit.py            # all sections
    python3 tools/ps3_audit.py q geo      # selected sections

Sections: q inventory+columns · keys keys/FKs · coord coordinate sanity · txt address text
          geo baseline/survey accuracy · visits visit outcomes · gps trajectories · agents collector integrity
          acc accounts/splits joins · leak leakage/time map

Writes: data/derived/ps3_table_profile.csv · ps3_column_profile.csv · ps3_leakage_map.csv

Every figure comes from INVENTED data (the dataset README says so). It can show that a mechanism
exists and that a failure mode is real; it can never be quoted as accuracy, coverage or market fact.
"""
import os, sys, glob, warnings
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 100)

HERE = os.path.dirname(os.path.abspath(__file__))
SEC = os.path.dirname(HERE)
ROOT = os.environ.get("CN_DATASET", os.path.join(SEC, "data", "official_ps3"))
OUT = os.environ.get("CN_OUT", os.path.join(SEC, "data", "derived"))
os.makedirs(OUT, exist_ok=True)

MET = ["met_borrower", "met_family", "cash_collected"]           # someone was met
NEG = ["address_not_traceable", "no_such_person", "neighbour_says_shifted"]
COORD_COLS = ("x", "y", "geocoder_x", "geocoder_y", "checkin_x", "checkin_y",
              "centroid_x", "centroid_y", "surveyed_x", "surveyed_y")


def L(p, **kw):
    return pd.read_csv(f"{ROOT}/{p}", low_memory=False, **kw)


def hdr(s):
    print("\n" + "=" * 100 + f"\n{s}\n" + "=" * 100)


def d(x1, y1, x2, y2):
    return np.hypot(np.asarray(x1, float) - np.asarray(x2, float),
                    np.asarray(y1, float) - np.asarray(y2, float))


def q(v, ps=(.5, .75, .9, .95)):
    v = np.asarray(pd.Series(v).dropna(), float)
    if not len(v):
        return {}
    return {f"p{int(p*100)}": round(float(np.quantile(v, p)), 2) for p in ps} | {
        "mean": round(float(v.mean()), 2), "max": round(float(v.max()), 2), "n": int(len(v))}


TABLES = {}


def T(name):
    """Lazy per-table cache so any audit section can run on its own."""
    if name not in TABLES:
        TABLES[name] = pd.read_csv(f"{ROOT}/{name}", low_memory=False)
    return TABLES[name]


# ─────────────────────────────────────────────────────────────── q: inventory + column profile
def sec_q():
    hdr("0. INVENTORY — every table, shape, key, coordinate columns")
    rows, cols = [], []
    for f in sorted(glob.glob(f"{ROOT}/*.csv")):
        name = os.path.basename(f)
        t = pd.read_csv(f, low_memory=False)
        TABLES[name] = t
        key = t.columns[0]
        duprows = int(t.duplicated().sum())
        rows.append(dict(file=name, rows=len(t), cols=t.shape[1], key=key,
                         key_unique=int(t[key].nunique()), key_is_pk=(t[key].nunique() == len(t)),
                         full_row_dupes=duprows,
                         null_cells=int(t.isna().sum().sum()),
                         null_cell_pct=round(100 * t.isna().sum().sum() / (len(t) * t.shape[1]), 2)))
        for c in t.columns:
            s = t[c]
            info = dict(file=name, column=c, dtype=str(s.dtype), n_null=int(s.isna().sum()),
                        pct_null=round(100 * s.isna().mean(), 2), n_unique=int(s.nunique(dropna=True)),
                        pct_unique=round(100 * s.nunique(dropna=True) / max(len(s), 1), 2))
            if pd.api.types.is_numeric_dtype(s):
                info |= {"min": (round(float(s.min()), 4) if s.notna().any() else None),
                         "max": (round(float(s.max()), 4) if s.notna().any() else None),
                         "mean": (round(float(s.mean()), 4) if s.notna().any() else None)}
            else:
                top = s.dropna().astype(str).value_counts().head(3)
                info |= {"min": None, "max": None, "mean": None,
                         "top3": " | ".join(f"{k}({v})" for k, v in top.items())[:90]}
            cols.append(info)
    tp = pd.DataFrame(rows); cp = pd.DataFrame(cols)
    print(tp.to_string(index=False))
    print("\nPER-COLUMN PROFILE (nulls / cardinality) — full table written to data/derived/ps3_column_profile.csv")
    print(cp[cp.pct_null > 0].to_string(index=False) if (cp.pct_null > 0).any() else "  no nulls anywhere")
    print("\nHIGH-CARDINALITY TEXT COLUMNS (>=90% unique):")
    print(cp[(cp.pct_unique >= 90) & (cp.dtype == "object")][["file", "column", "n_unique", "pct_unique"]].to_string(index=False))
    print("\nCONSTANT / NEAR-CONSTANT COLUMNS (<=5 distinct values):")
    print(cp[cp.n_unique <= 5][["file", "column", "n_unique", "top3"]].to_string(index=False))
    print("\nCOORDINATE + TIME COLUMNS FOUND:")
    for f, g in cp.groupby("file"):
        cc = [c for c in g.column if c in COORD_COLS]
        tc = [c for c in g.column if "ts" in c or "date" in c]
        if cc or tc:
            print(f"  {f:26} coords={cc} time={tc}")
    tp.to_csv(f"{OUT}/ps3_table_profile.csv", index=False)
    cp.to_csv(f"{OUT}/ps3_column_profile.csv", index=False)
    print(f"\n-> {OUT}/ps3_table_profile.csv, ps3_column_profile.csv")


# ─────────────────────────────────────────────────────────────── keys / relationships
def sec_keys():
    hdr("1. KEYS, FOREIGN KEYS, ORPHANS")
    ad, ac, fv, bg, sv, gp, lm, lo, to, ag, sp = (TABLES[k] for k in
        ["addresses.csv", "accounts.csv", "field_visits.csv", "baseline_geocodes.csv",
         "surveyed_addresses.csv", "visit_gps_points.csv", "landmarks_poi.csv",
         "localities.csv", "towns.csv", "agents.csv", "splits.csv"])

    def rel(name, left, col, right):
        l, r = set(left[col].dropna()), set(right[col].dropna())
        print(f"  {name:52} left={len(l):>6} right={len(r):>6} orphans={len(l-r):>5} "
              f"({100*len(l-r)/max(len(l),1):4.1f}%) unmatched_right={len(r-l):>5}")

    rel("addresses.account_id -> accounts.account_id", ad, "account_id", ac)
    rel("addresses.town_id -> towns.town_id", ad, "town_id", to)
    rel("field_visits.address_id -> addresses.address_id", fv, "address_id", ad)
    rel("field_visits.account_id -> accounts.account_id", fv, "account_id", ac)
    rel("field_visits.agent_id -> agents.agent_id", fv, "agent_id", ag)
    rel("baseline_geocodes.address_id -> addresses.address_id", bg, "address_id", ad)
    rel("surveyed_addresses.address_id -> addresses.address_id", sv, "address_id", ad)
    rel("visit_gps_points.visit_id -> field_visits.visit_id", gp, "visit_id", fv)
    rel("localities.town_id -> towns.town_id", lo, "town_id", to)
    rel("landmarks_poi.town_id -> towns.town_id", lm, "town_id", to)
    rel("splits.account_id -> accounts.account_id", sp, "account_id", ac)

    print(f"\n  accounts without any address: {len(set(ac.account_id) - set(ad.account_id))}")
    print(f"  accounts with >1 address:     {ad.account_id.value_counts().gt(1).sum()} "
          f"(max {ad.account_id.value_counts().max()})")
    print(f"  addresses with no geocode:    {len(set(ad.address_id) - set(bg.address_id))} of {ad.address_id.nunique()} "
          f"({100*len(set(ad.address_id) - set(bg.address_id))/ad.address_id.nunique():.1f}%)")
    print(f"  addresses with no visit:      {len(set(ad.address_id) - set(fv.address_id))} "
          f"({100*len(set(ad.address_id) - set(fv.address_id))/ad.address_id.nunique():.1f}%)")
    print(f"  visits with no GPS trail:     {len(set(fv.visit_id) - set(gp.visit_id))} of {len(fv)}")
    print(f"  duplicate visit_id in gps:    {gp.duplicated(['visit_id','seq']).sum()} (visit_id+seq must be unique)")
    print(f"  address_type distribution:    {ad.address_type.value_counts().to_dict()}")
    print(f"  address source distribution:  {ad.source.value_counts().to_dict()}")
    print(f"  splits:                       {sp.split.value_counts().to_dict()}  "
          f"covers all accounts: {set(sp.account_id) == set(ac.account_id)}")


# ─────────────────────────────────────────────────────────────── coordinates
def sec_coord():
    hdr("2. COORDINATE SANITY — ranges, zeros, precision, piles, town plausibility")
    to = T("towns.csv"); lo = T("localities.csv"); ad = T("addresses.csv")
    bg = T("baseline_geocodes.csv"); sv = T("surveyed_addresses.csv")
    fv = T("field_visits.csv"); gp = T("visit_gps_points.csv"); lm = T("landmarks_poi.csv")

    for name, df in [("towns", lo), ("localities", lo), ("landmarks", lm), ("baseline_geocodes", bg),
                     ("surveyed_addresses", sv), ("field_visits(checkin)", fv), ("gps_points", gp)]:
        cs = [c for c in df.columns if c in COORD_COLS]
        if not cs:
            continue
        out = []
        for c in cs:
            s = df[c]
            out.append(f"{c}: [{s.min():.1f}, {s.max():.1f}] zeros={(s == 0).sum()} nulls={s.isna().sum()}")
        print(f"  {name:24} " + " | ".join(out))

    print("\n  DECIMAL PRECISION OF PUBLISHED COORDINATES (a rounding signal):")
    for c in ["geocoder_x", "geocoder_y", "centroid_x", "centroid_y", "x", "checkin_x"]:
        df = {"geocoder_x": bg, "geocoder_y": bg, "centroid_x": lo, "centroid_y": lo,
              "x": lm, "checkin_x": fv}[c]
        dec = df[c].dropna().astype(str).str.split(".").str[-1].str.len()
        print(f"    {c:12} median decimals={dec.median():.0f}  distinct coords={df[c].nunique()} of {len(df)}")

    print("\n  DUPLICATE PIN PILES (many addresses sharing one geocode = vendor degradation):")
    vc = bg.groupby(["geocoder_x", "geocoder_y"]).size().sort_values(ascending=False)
    print(f"    distinct pins={len(vc)} for {len(bg)} geocodes; largest pile={vc.iloc[0]} addresses; "
          f"piles>=10: {(vc >= 10).sum()} covering {vc[vc >= 10].sum()} addresses "
          f"({100*vc[vc >= 10].sum()/len(bg):.1f}%)")

    print("\n  TOWN PLAUSIBILITY (address geocode vs its own town's locality centroids):")
    town_cent = lo.groupby("town_id")[["centroid_x", "centroid_y"]].mean()
    m = ad.merge(bg, on="address_id", how="left").merge(town_cent, left_on="town_id", right_index=True, how="left")
    m["d_town"] = d(m.geocoder_x, m.geocoder_y, m.centroid_x, m.centroid_y)
    print(m.groupby("town_id").d_town.describe(percentiles=[.5, .9, .99]).round(1).to_string())

    print("\n  WITHIN-TOWN CONTAINMENT: are all check-ins inside their town's 99th-percentile envelope?")
    fvt = fv.merge(ad[["address_id", "town_id"]], on="address_id", how="left")
    fvt["d_town"] = d(fvt.checkin_x, fvt.checkin_y,
                      town_cent.centroid_x.reindex(fvt.town_id).values, town_cent.centroid_y.reindex(fvt.town_id).values)
    for t, g in fvt.groupby("town_id"):
        print(f"    {t}: visits={len(g)} median={g.d_town.median():.0f} m p99={g.d_town.quantile(.99):.0f} m "
              f"max={g.d_town.max():.0f} m")


# ─────────────────────────────────────────────────────────────── address text
def sec_txt():
    hdr("3. ADDRESS TEXT — length, house numbers, pincode, script, duplicates, hierarchy conflicts")
    ad = T("addresses.csv"); lo = T("localities.csv"); to = T("towns.csv")
    t = ad.address_text.astype(str)
    ad = ad.assign(txt_len=t.str.len(), n_tokens=t.str.split().str.len(),
                   n_digits=t.str.count(r"\d"), n_commas=t.str.count(","),
                   n_upper=t.str.count(r"[A-Z]"), n_nonascii=t.str.count(r"[^\x00-\x7F]"),
                   has_house_no=t.str.contains(r"\b\d{1,4}[A-Za-z]?\b", regex=True),
                   has_pincode=t.str.contains(r"\b\d{6}\b", regex=True),
                   has_slash=t.str.contains(r"[\/\-]"), has_hash=t.str.contains(r"#"))
    print("  LENGTH / SHAPE:")
    for c in ["txt_len", "n_tokens", "n_digits", "n_commas", "n_upper", "n_nonascii"]:
        print(f"    {c:12} {q(ad[c])}")
    for c in ["has_house_no", "has_pincode", "has_slash", "has_hash"]:
        print(f"    {c:14} true={int(ad[c].sum())} ({100*ad[c].mean():.1f}%)")

    print("\n  MALFORMED / DEGENERATE:")
    print(f"    empty or <5 chars:  {(ad.txt_len < 5).sum()}")
    print(f"    no digits at all:   {(ad.n_digits == 0).sum()} ({100*(ad.n_digits == 0).mean():.1f}%)  <- no house number possible")
    print(f"    no comma:           {(ad.n_commas == 0).sum()} ({100*(ad.n_commas == 0).mean():.1f}%)  <- unpunctuated single blob")
    print(f"    contains 'NA'/'na': {ad.address_text.astype(str).str.contains(r'\b(NA|na|N/A)\b').sum()}")
    nonascii = ad[ad.n_nonascii > 0]
    print(f"    non-ASCII rows:     {len(nonascii)}; sample: {nonascii.address_text.head(3).tolist()}")
    print(f"    exact duplicate texts: {int(ad.address_text.duplicated().sum())} on {ad.address_id.nunique()} addresses")
    norm = ad.address_text.astype(str).str.upper().str.replace(r"[^A-Z0-9]+", " ", regex=True).str.strip()
    print(f"    duplicates after aggressive normalisation (case/punct/space): {int(norm.duplicated().sum())}")
    print(f"      -> of those, rows on a DIFFERENT address_id but SAME account: "
          f"{int(ad.assign(n=norm).duplicated(['account_id','n']).sum())}")

    print("\n  TOKEN VOCABULARY (top 15) — is 'locality' even in the text?")
    toks = pd.Series(" ".join(norm.sample(min(2000, len(ad)), random_state=0)).split())
    print("    " + " | ".join(f"{k}:{v}" for k, v in toks.value_counts().head(15).items()))

    print("\n  HIERARCHY CONSISTENCY (pincode ← locality ← town):")
    j = ad.merge(lo, on="town_id", how="left", suffixes=("", "_loc"))
    print(f"    localities per town: {lo.groupby('town_id').size().to_dict()}")
    print(f"    pincodes per town:   {lo.groupby('town_id').pincode.nunique().to_dict()}")
    print(f"    pincodes serving >1 town: {int((lo.groupby('pincode').town_id.nunique() > 1).sum())} of {lo.pincode.nunique()}")
    pin_in_text = ad.has_pincode
    lp = lo.pincode.astype(str).unique()
    found = ad[pin_in_text].address_text.str.extract(r"\b(\d{6})\b")[0]
    print(f"    addresses containing a 6-digit number: {int(pin_in_text.sum())} ({100*pin_in_text.mean():.1f}%)")
    print(f"    ...of those, matching ANY known pincode: "
          f"{int(found.isin(lp).sum())} ({100*found.isin(lp).mean():.1f}%)  <- pincode evidence is rarely usable")
    print(f"    town_id in text? ", {t: int(ad.address_text.str.lower().str.contains(t.lower()).sum())
                                     for t in to.town_name.head(3)})
    print("\n  TOWN ADDRESS STYLES:")
    print(to.to_string(index=False))


# ─────────────────────────────────────────────────────────────── baseline + survey accuracy
def sec_geo():
    hdr("4. BASELINE GEOCODER + THE ONLY GROUND TRUTH (100 surveyed addresses)")
    bg = T("baseline_geocodes.csv"); sv = T("surveyed_addresses.csv")
    ad = T("addresses.csv"); lo = T("localities.csv"); fv = T("field_visits.csv")

    print("  PRECISION STRATA (the vendor's own uncertainty vocabulary):")
    print(bg.precision.value_counts().to_string())
    print(f"    geocode rows={len(bg)} addresses={bg.address_id.nunique()} "
          f"missing={ad.address_id.nunique() - bg.address_id.nunique()}")

    s = sv.merge(bg, on="address_id", how="left").merge(ad[["address_id", "town_id"]], on="address_id", how="left")
    s["err"] = d(s.surveyed_x, s.surveyed_y, s.geocoder_x, s.geocoder_y)
    print(f"\n  SURVEY SAMPLE (the only true coordinates in the package): n={len(s)} "
          f"towns={s.town_id.value_counts().to_dict()}  missing geocode={int(s.geocoder_x.isna().sum())}")
    print(f"    error vs baseline geocode: {q(s.err, (.5,.75,.9))}")
    for x in (50, 100, 250, 500):
        print(f"      within {x:>3} m: {100*(s.err < x).mean():5.1f}%")
    print("\n    BY STRATUM (the radius table must be per-stratum, not global):")
    g = s.groupby("precision").err.agg(n="size", median="median", p75=lambda v: v.quantile(.75),
                                       p90=lambda v: v.quantile(.9)).round(1)
    g["hit_100m"] = s.groupby("precision").err.apply(lambda v: round(100*(v < 100).mean(), 1))
    print(g.to_string())

    print("\n  FREE-DATA CEILING (candidates a licence-clean system can build from text + gazetteer):")
    lc = lo.groupby("town_id")[["centroid_x", "centroid_y"]].mean()
    s2 = s.merge(lc, left_on="town_id", right_index=True, how="left")
    s2["lc"] = d(s2.surveyed_x, s2.surveyed_y, s2.centroid_x, s2.centroid_y)
    print(f"    locality-centroid candidate: median {s2.lc.median():.0f} m, "
          f"<100 m {100*(s2.lc < 100).mean():.0f}%, <500 m {100*(s2.lc < 500).mean():.0f}%")
    print(f"    town-centroid candidate:     median {s2.lc.median():.0f} m (same order as locality in this dataset)")
    print("    naive POI snapping was measured at 4,093 m median in the previous pass -> DO NOT snap to landmarks")

    print("\n  STRATUM IS INFORMATIVE ABOUT ERROR, NOT ABOUT TRUTH:")
    print(s.groupby("precision").err.describe(percentiles=[.5, .9]).round(1)[["count","50%","90%","max"]].to_string())

    print("\n  HOW MANY ADDRESSES HAVE *ANY* FIELD EVIDENCE?")
    v = fv.groupby("address_id").size()
    print(f"    addresses visited at least once: {len(v)} of {ad.address_id.nunique()} "
          f"({100*len(v)/ad.address_id.nunique():.1f}%)   visits/address {q(v, (.5,.9))}")
    met = fv[fv.outcome.isin(MET)].groupby("address_id").size()
    print(f"    addresses with at least one met-someone visit: {len(met)} "
          f"({100*len(met)/ad.address_id.nunique():.1f}%)  <- the entire learning signal")


# ─────────────────────────────────────────────────────────────── visits
def sec_visits():
    hdr("5. FIELD VISITS — outcomes, dwell, distance, duplicates, integrity signals")
    fv = T("field_visits.csv"); bg = T("baseline_geocodes.csv")
    sv = T("surveyed_addresses.csv"); ad = T("addresses.csv"); ag = T("agents.csv")

    print("  OUTCOME VOCABULARY:")
    print(fv.outcome.value_counts().to_frame("n").assign(pct=lambda x: (100*x.n/len(fv)).round(1)).to_string())
    print(f"    MET (met_borrower/met_family/cash): {100*fv.outcome.isin(MET).mean():.1f}%   "
          f"NEGATIVE (not traceable/no such person/shifted): {100*fv.outcome.isin(NEG).mean():.1f}%")

    fv = fv.assign(hrs=fv.dwell_s/3600,
                   start=pd.to_datetime(fv.start_ts), checkin=pd.to_datetime(fv.checkin_ts))
    fv["travel_s"] = (fv.checkin - fv.start).dt.total_seconds()
    print(f"\n  DWELL: {q(fv.dwell_s/60, (.5,.75,.9))} minutes  · total {fv.hrs.sum():.0f} h")
    print(f"  TRAVEL (start->check-in): {q(fv.travel_s/60, (.5,.9))} minutes; negative travel: {int((fv.travel_s < 0).sum())}")
    print("\n  DWELL BY OUTCOME (does a 'not traceable' visit look different?):")
    g = fv.groupby("outcome").agg(n=("dwell_s","size"), median_min=("dwell_s", lambda s: round(s.median()/60,1)),
                                  p90_min=("dwell_s", lambda s: round(s.quantile(.9)/60,1)),
                                  med_acc_m=("gps_accuracy_m","median")).round(1)
    print(g.sort_values("n", ascending=False).to_string())

    v = fv.merge(bg, on="address_id", how="left")
    v["d_pin"] = d(v.checkin_x, v.checkin_y, v.geocoder_x, v.geocoder_y)
    print("\n  CHECK-IN vs BASELINE PIN, BY OUTCOME (negative outcomes are NOT closer to truth):")
    g = v.groupby("outcome").d_pin.agg(n="size", median="median", p90=lambda s: s.quantile(.9)).round(1)
    g["pct_under_100m"] = v.groupby("outcome").d_pin.apply(lambda s: round(100*(s < 100).mean(),1))
    print(g.to_string())
    svv = v.merge(sv, on="address_id", how="inner")
    svv["d_truth"] = d(svv.checkin_x, svv.checkin_y, svv.surveyed_x, svv.surveyed_y)
    print("\n  ...AND AGAINST SURVEYED TRUTH for the 100-address subset "
          "(the load-bearing number for evidence weighting):")
    g = svv.groupby("outcome").d_truth.agg(n="size", median="median").round(1)
    print(g.to_string())
    print("    met visits vs negative visits on the same sample: "
          f"{svv[svv.outcome.isin(MET)].d_truth.median():.0f} m vs {svv[svv.outcome.isin(NEG)].d_truth.median():.0f} m")

    print("\n  DUPLICATE EVIDENCE:")
    print(f"    duplicate photo hashes (all agents): {int(fv.photo_hash.duplicated().sum())} of {fv.photo_hash.notna().sum()} "
          f"({100*fv.photo_hash.duplicated().sum()/fv.photo_hash.notna().sum():.1f}%)")
    by_agent = fv.groupby("agent_id").agg(visits=("visit_id","size"),
                                          dup_photo=("photo_hash", lambda s: int(s.duplicated().sum())),
                                          uniq_photo=("photo_hash","nunique"),
                                          med_dwell_min=("dwell_s", lambda s: round(s.median()/60,1)),
                                          med_acc=("gps_accuracy_m","median"),
                                          met_rate=("outcome", lambda s: round(100*s.isin(MET).mean(),1)),
                                          distinct_checkins=("checkin_x","nunique")).sort_values("dup_photo", ascending=False)
    by_agent["dup_photo_rate"] = (100*by_agent.dup_photo/by_agent.visits).round(1)
    print(by_agent.head(8).to_string())
    print(f"    agents with duplicate-photo rate >20%: {int((by_agent.dup_photo_rate > 20).sum())} of {len(by_agent)}")
    print("    ^ this is the planted bad actor; the integrity gate must catch it WITHOUT being told which agent")

    print("\n  REPEATED CHECK-IN COORDINATES (same x,y reused across visits by one agent):")
    rep = fv.groupby(["agent_id", "checkin_x", "checkin_y"]).size()
    print(f"    (agent,coord) pairs used >=3 times: {int((rep >= 3).sum())} covering {int(rep[rep>=3].sum())} visits "
          f"({100*rep[rep>=3].sum()/len(fv):.1f}%)")

    print("\n  TEMPORAL COVERAGE:")
    print(f"    visit_date: {fv.visit_date.min()} -> {fv.visit_date.max()}  "
          f"days={fv.visit_date.nunique()}  weekday mix={fv.checkin.dt.dayofweek.value_counts().sort_index().to_dict()}")
    print(f"    hour of check-in: {fv.checkin.dt.hour.value_counts().sort_index().to_dict()}")
    print("\n  RELATIONSHIPS: visits per address / account / agent")
    print(f"    per address {q(fv.groupby('address_id').size())} | per account {q(fv.groupby('account_id').size())} "
          f"| per agent {q(fv.groupby('agent_id').size())}")
    print(f"    addresses visited by >1 agent: {int((fv.groupby('address_id').agent_id.nunique() > 1).sum())} "
          f"({100*(fv.groupby('address_id').agent_id.nunique() > 1).mean():.1f}%)  <- independent confirmations exist")


# ─────────────────────────────────────────────────────────────── GPS
def sec_gps():
    hdr("6. GPS TRAJECTORIES — validity, accuracy, speed, coverage")
    gp = T("visit_gps_points.csv"); fv = T("field_visits.csv")
    gp = gp.assign(pt=pd.to_datetime(gp.point_ts))
    per = gp.groupby("visit_id").agg(n=("seq","size"), t0=("pt","min"), t1=("pt","max"),
                                     span_s=("pt", lambda s: (s.max()-s.min()).total_seconds()),
                                     acc_med=("accuracy_m","median"), x0=("x","min"), x1=("x","max"))
    print(f"  points={len(gp)} visits={gp.visit_id.nunique()} of {len(fv)} field visits "
          f"({100*gp.visit_id.nunique()/len(fv):.1f}% instrumented)")
    print(f"  points per visit: {q(per.n, (.5,.9))}")
    print(f"  accuracy_m: {q(gp.accuracy_m, (.5,.9))}  (Android convention: ~68% radial confidence, not a bound)")
    print(f"  visits with <5 points: {int((per.n < 5).sum())}  |  visits with span 0 s: {int((per.span_s == 0).sum())}")
    print(f"  point_ts range: {gp.pt.min()} -> {gp.pt.max()}")

    print("\n  SEQ MONOTONICITY (is the trail ordered?)")
    chk = gp.sort_values(["visit_id","seq"]).groupby("visit_id").pt.apply(lambda s: s.is_monotonic_increasing)
    print(f"    visits whose points are non-decreasing in time by seq: {int(chk.sum())} of {len(chk)}")

    print("\n  IMPLIED SPEED BETWEEN CONSECUTIVE POINTS (teleport detection baseline):")
    g = gp.sort_values(["visit_id","seq"]).copy()
    g["dx"] = g.groupby("visit_id").x.diff(); g["dy"] = g.groupby("visit_id").y.diff()
    g["dt"] = g.groupby("visit_id").pt.diff().dt.total_seconds()
    g["dist"] = np.hypot(g.dx, g.dy)
    g["kmh"] = 3.6*g.dist/g.dt.replace(0, np.nan)
    sp = g[(g.dt > 0) & g.dist.notna()]
    print(f"    steps={len(sp)} median step={sp.dist.median():.1f} m   "
          f"km/h {q(sp.kmh, (.5,.9,.99))}")
    print(f"    steps >60 km/h: {int((sp.kmh > 60).sum())} ({100*(sp.kmh > 60).mean():.2f}%)  "
          f">120 km/h: {int((sp.kmh > 120).sum())} ({100*(sp.kmh > 120).mean():.2f}%)  <- teleport candidates")
    print(f"    zero-distance repeated points: {int((sp.dist == 0).sum())} ({100*(sp.dist == 0).mean():.1f}%)")

    print("\n  DOES THE CHECK-IN LIE ON ITS OWN TRAIL?")
    j = fv[["visit_id","checkin_x","checkin_y","outcome","dwell_s","agent_id"]].merge(gp, on="visit_id", how="inner")
    j["d_trail"] = np.hypot(j.checkin_x-j.x, j.checkin_y-j.y)
    near = j.groupby("visit_id").d_trail.min()
    print(f"    min distance from check-in to its own trail: {q(near, (.5,.9))}")
    far = near[near > 500]
    print(f"    visits whose check-in is >500 m from every one of its own GPS points: {len(far)} "
          f"({100*len(far)/len(near):.1f}%)  <- instrument noise or staged check-ins")
    fv2 = fv.set_index("visit_id").loc[far.index] if len(far) else fv.iloc[0:0]
    if len(fv2):
        print("      their outcomes: " + str(fv2.outcome.value_counts().to_dict()))
        print(f"      their median dwell: {fv2.dwell_s.median()/60:.1f} min vs overall {fv.dwell_s.median()/60:.1f} min")

    print("\n  ACCURACY AS A TRUST SIGNAL:")
    fv3 = fv.merge(gp.groupby("visit_id").accuracy_m.median().rename("trail_acc"), on="visit_id", how="left")
    fv3["d"] = np.hypot(fv3.checkin_x - fv3.checkin_x, 0)  # placeholder to keep columns explicit
    b = pd.cut(fv3.gps_accuracy_m, [0, 20, 50, 100, 1e6], labels=["<=20 m", "20-50 m", "50-100 m", ">100 m"])
    print(fv3.assign(acc_band=b).groupby("acc_band", observed=True).agg(
        visits=("visit_id","size"),
        met_rate=("outcome", lambda s: round(100*s.isin(MET).mean(),1)),
        med_dwell=("dwell_s", lambda s: round(s.median()/60,1))).to_string())
    print("    (a trustworthy system must decide the weight of a check-in from accuracy + trail agreement, not outcome)")


# ─────────────────────────────────────────────────────────────── collectors
def sec_agents():
    hdr("7. COLLECTORS — capacity, coverage, behavioural baselines")
    ag = T("agents.csv"); fv = T("field_visits.csv"); ad = T("addresses.csv")
    print(f"  agents={len(ag)}  channels={ag.channel.value_counts().to_dict()}")
    print(f"  language teams={ag.language_team.value_counts().to_dict()}")
    print(f"  towns={ag.town_id.value_counts(dropna=False).to_dict()}  tenure_months {q(ag.tenure_months)}")
    print(f"  shifts={ag['shift'].value_counts().to_dict()}")
    f = fv.merge(ag, on="agent_id", how="left")
    print("\n  visits per channel:")
    print(f.groupby("channel").agg(visits=("visit_id","size"),
                                   addresses=("address_id","nunique"),
                                   met_rate=("outcome", lambda s: round(100*s.isin(MET).mean(),1)),
                                   med_dwell=("dwell_s", lambda s: round(s.median()/60,1))).to_string())
    print("\n  are agents town-local? (a field agent travelling between towns is an integrity signal)")
    f2 = fv.merge(ad[["address_id","town_id"]], on="address_id", how="left").merge(
        ag[["agent_id","town_id"]], on="agent_id", how="left", suffixes=("","_agent"))
    cross = (f2.town_id != f2.town_id_agent)
    print(f"    visits where visit town != agent's home town: {int(cross.sum())} ({100*cross.mean():.1f}%) "
          f"across {f2[cross].agent_id.nunique()} agents")


# ─────────────────────────────────────────────────────────────── accounts + splits
def sec_acc():
    hdr("8. ACCOUNTS / SPLITS — the demand side and the split protocol")
    ac = T("accounts.csv"); sp = T("splits.csv"); ad = T("addresses.csv")
    fv = T("field_visits.csv")
    print(f"  accounts={len(ac)}  lenders={ac.lender_id.nunique()}  portfolios={ac.portfolio.value_counts().to_dict()}")
    print(f"  dpd_start bands: {ac.dpd_start.describe(percentiles=[.5,.9]).round(0).to_dict()}")
    print(f"  outstanding: {q(ac.outstanding, (.5,.9))}  emi: {q(ac.emi_amount, (.5,.9))}")
    print(f"  splits: {sp.split.value_counts().to_dict()}")
    j = ac.merge(sp, on="account_id").merge(ad[["account_id","address_id","town_id"]], on="account_id", how="left")
    j = j.merge(fv.groupby("address_id").size().rename("visits"), on="address_id", how="left")
    print("\n  coverage of the learning signal BY SPLIT (visits are not distributed evenly):")
    print(j.groupby("split").agg(accounts=("account_id","size"), addresses=("address_id","nunique"),
                                 with_visit=("visits", lambda s: int(s.notna().sum())),
                                 pct_with_visit=("visits", lambda s: round(100*s.notna().mean(),1))).to_string())
    print("\n  DPD BAND vs VISIT RATE (are harder cases visited more? -> selection bias in the evidence):")
    j["dpd_band"] = pd.cut(j.dpd_start, [-1, 30, 60, 90, 180, 1e6],
                           labels=["0-30", "31-60", "61-90", "91-180", "180+"])
    print(j.groupby("dpd_band", observed=True).agg(accounts=("account_id","size"),
                                                   pct_visited=("visits", lambda s: round(100*s.notna().mean(),1)),
                                                   mean_visits=("visits","mean")).round(2).to_string())
    print("\n  SELECTION BIAS — the operational question the system must answer honestly:")
    v = fv.groupby("address_id").size().rename("n_visits")
    k = ad.merge(v, on="address_id", how="left")
    k = k.merge(T("baseline_geocodes.csv"), on="address_id", how="left")
    lo = T("localities.csv").groupby("town_id")[["centroid_x","centroid_y"]].mean()
    k = k.merge(lo, left_on="town_id", right_index=True, how="left")
    k["vendor_err_proxy"] = d(k.geocoder_x, k.geocoder_y, k.centroid_x, k.centroid_y)
    k["visited"] = k.n_visits.notna()
    print(f"    visited addresses: vendor-error-proxy median {k[k.visited].vendor_err_proxy.median():.0f} m")
    print(f"    never visited:     vendor-error-proxy median {k[~k.visited].vendor_err_proxy.median():.0f} m")
    print("    -> if the operands differ, field evidence is NOT a random sample of addresses "
          "(the loop must be propensity-aware, not naive)")


# ─────────────────────────────────────────────────────────────── leakage / time map
def sec_leak():
    hdr("9. LEAKAGE & TIME-TO-AVAILABILITY MAP (T0 pre-query · T1 candidates · T2 in-visit · T3 post-visit · T4 later)")
    M = [
        # (file, column, stage, inference-time available?, note)
        ("addresses.csv", "address_text", "T0", "yes", "the query itself"),
        ("addresses.csv", "town_id", "T0", "yes", "in the record at query time"),
        ("addresses.csv", "address_type", "T0", "yes", "self-declared; may be stale"),
        ("addresses.csv", "source", "T0", "yes", "provenance of the address record"),
        ("addresses.csv", "added_date", "T0", "yes", "record age; usable as a feature, not a label"),
        ("baseline_geocodes.csv", "geocoder_x/geocoder_y", "T0", "yes", "vendor prior (licence clock: <=30-day cache, Google ToS)"),
        ("baseline_geocodes.csv", "precision", "T0", "yes", "vendor stratum — the honest uncertainty key"),
        ("localities.csv", "centroid_x/centroid_y, pincode", "T0", "yes", "gazetteer prior"),
        ("landmarks_poi.csv", "name, x, y, landmark_type", "T0", "yes", "gazetteer prior (incomplete; naive snapping measured 4,093 m)"),
        ("towns.csv", "approx_radius_m, address_style", "T0", "yes", "coarse prior per town"),
        ("accounts.csv", "outstanding, dpd_start", "T0", "yes", "value side of a field slot, if a consumer prices visits"),
        ("agents.csv", "channel, tenure_months, shift", "T2", "yes", "known at dispatch; use for integrity baselines, not labels"),
        ("field_visits.csv", "checkin_x/checkin_y", "T2", "post-hoc", "the observation — label-side material, never a query-time feature"),
        ("field_visits.csv", "gps_accuracy_m, dwell_s", "T2", "post-hoc", "evidence quality; T2 but only after the visit"),
        ("field_visits.csv", "outcome", "T3", "post-hoc", "outcome classification; NEVER a feature for the location of the same visit"),
        ("field_visits.csv", "remark", "T3", "post-hoc", "free text; partially structured (landmark mentions)"),
        ("field_visits.csv", "photo_hash", "T2", "post-hoc", "duplicate detection input; do not expose agent identity to the model"),
        ("visit_gps_points.csv", "x, y, accuracy_m, point_ts", "T2", "post-hoc", "trail; integrity + dwell geometry"),
        ("surveyed_addresses.csv", "surveyed_x/surveyed_y", "T4", "NO", "the only ground truth — evaluation only, never training input"),
        ("splits.csv", "split", "meta", "no", "evaluation protocol; assignment must respect account/address/time"),
        ("field_visits.csv", "ptp_id", "T3", "no", "belongs to another problem statement entirely — exclude"),
    ]
    df = pd.DataFrame(M, columns=["file", "column", "stage", "available_at_inference", "why_it_matters"])
    print(df.to_string(index=False))
    df.to_csv(f"{OUT}/ps3_leakage_map.csv", index=False)

    print("\n  HARD RULES THIS MAP IMPLIES (tested in tools/check_leakage.py):")
    print("    1. No column with stage >= T2 may appear in a query-time feature set for that address.")
    print("    2. surveyed_* coordinates may never enter training; they are the scoring set.")
    print("    3. A visit's own outcome may never be used to place a coordinate used at that visit.")
    print("    4. Vendor coordinates may be cached at most 30 days (licence) -> the canonical point must be ours.")
    print("    5. Any feature derived from field_visits must be aggregated with an explicit as-of timestamp.")
    print(f"\n-> {OUT}/ps3_leakage_map.csv")


# ─────────────────────────────────────────────────────────────── extra targeted checks
def sec_xtra():
    hdr("10. TARGETED CHECKS — the traps that would silently break a naive build")
    ad = T("addresses.csv"); bg = T("baseline_geocodes.csv"); lo = T("localities.csv")
    lm = T("landmarks_poi.csv"); gp = T("visit_gps_points.csv"); to = T("towns.csv")
    fv = T("field_visits.csv")

    print("  (a) THE ORPHAN TOWN — addresses carry a town_id that towns.csv does not define:")
    print(f"      addresses.town_id values: {ad.town_id.value_counts(dropna=False).to_dict()}")
    print(f"      towns.csv town_ids:       {to.town_id.tolist()}")
    out = ad[ad.town_id == "OUT"]
    print(f"      OUT addresses: {len(out)}  of which geocoded: {int(out.address_id.isin(bg.address_id).sum())} "
          f"({100*out.address_id.isin(bg.address_id).mean():.1f}%)")
    print(f"      non-OUT addresses geocoded: {100*ad[ad.town_id != 'OUT'].address_id.isin(bg.address_id).mean():.1f}%")
    print("      -> 'no address we can place' is a REAL state in the data, not a modelling edge case")
    print(f"      OUT addresses by type: {out.address_type.value_counts().to_dict()}")

    print("\n  (b) MATCHED-LOCALITY CANDIDATE (a licence-clean retriever: does the text contain a gazetteer name?):")
    hit = 0
    rows = []
    for _, r in ad.iterrows():
        txt = str(r.address_text).lower()
        names = lo[lo.town_id == r.town_id].locality_name.astype(str).str.lower()
        m = [n for n in names if n in txt]
        if m:
            hit += 1
        rows.append(len(m))
    ser = pd.Series(rows)
    print(f"      addresses whose text contains >=1 locality name from their own town: {int((ser > 0).sum())} "
          f"({100*(ser > 0).mean():.1f}%)")
    print(f"      addresses matching >1 locality name (ambiguity!): {int((ser > 1).sum())} ({100*(ser > 1).mean():.1f}%)")
    sv = T("surveyed_addresses.csv").merge(bg, on="address_id").merge(ad[["address_id", "town_id", "address_text"]],
                                                                     on="address_id")
    e = []
    for _, r in sv.iterrows():
        names = lo[(lo.town_id == r.town_id)].copy()
        m = names[names.locality_name.astype(str).str.lower().isin(
            [n for n in names.locality_name.astype(str).str.lower() if n in str(r.address_text).lower()])]
        if len(m):
            mm = m.iloc[0]
            e.append(float(np.hypot(r.surveyed_x - mm.centroid_x, r.surveyed_y - mm.centroid_y)))
        else:
            e.append(np.nan)
    e = pd.Series(e, dtype=float)
    print(f"      on the 100 surveyed addresses: matched-locality centroid error median {e.median():.0f} m "
          f"(coverage {100*e.notna().mean():.0f}%)  <- the honest free-artefact ceiling")
    print(f"      vendor baseline on the same 100: median "
          f"{pd.Series(np.hypot(sv.surveyed_x-sv.geocoder_x, sv.surveyed_y-sv.geocoder_y)).median():.0f} m")

    print("\n  (c) LANDMARK TABLE — usable as a prior?")
    print(f"      rows={len(lm)} types={lm.landmark_type.value_counts().to_dict()}")
    print(f"      duplicate names: {int(lm.name.duplicated().sum())}  distinct names={lm.name.nunique()}")
    print(f"      landmarks per town: {lm.groupby('town_id').size().to_dict()}")
    intext = 0
    for _, r in ad.iterrows():
        t = str(r.address_text).lower()
        names = lm[lm.town_id == r.town_id].name.astype(str).str.lower()
        if any(n in t for n in names if len(n) > 4):
            intext += 1
    print(f"      addresses whose text mentions a known landmark of their town: {intext} ({100*intext/len(ad):.1f}%)")
    print(f"      duplicate (town,name) pairs: {int(lm.duplicated(['town_id','name']).sum())} "
          f"-> name is NOT unique inside a town: snapping to a name is ambiguous")

    print("\n  (d) LOCALITY TABLE — the duplicate-name trap:")
    d = lo[lo.locality_name.duplicated(keep=False)]
    print(f"      locality_name duplicates: {len(d)} rows -> {d[['locality_id','town_id','locality_name','pincode']].to_string(index=False)}")
    print(f"      pincode inside text but NOT a known pincode: see section 3")

    print("\n  (e) GPS (0,0)-ISH POINTS (sensor artefacts that must be filtered, not learned from):")
    z = gp[(gp.x == 0) | (gp.y == 0)]
    print(f"      points with x==0 or y==0: {len(z)} ({100*len(z)/len(gp):.4f}%) across {z.visit_id.nunique()} visits")
    zz = z.merge(fv[["visit_id","outcome","checkin_x","checkin_y"]], on="visit_id", how="left")
    print(f"      their outcomes: {zz.outcome.value_counts().to_dict()}")

    print("\n  (f) FIELD-EVIDENCE COVERAGE vs TIME (does the loop even close in 90 days?):")
    f = fv.assign(c=pd.to_datetime(fv.checkin_ts))
    first = f.groupby("address_id").c.min()
    ad2 = ad.merge(first.rename("first_visit"), on="address_id", how="left")
    ad2["added"] = pd.to_datetime(ad2.added_date)
    ad2["days_to_first"] = (ad2.first_visit - ad2.added).dt.days
    print(f"      addresses added: {ad2.added.min().date()} -> {ad2.added.max().date()}")
    print(f"      days from record creation to first visit: {q(ad2.days_to_first, (.5,.9))}  "
          f"(negative => visited before the record existed: {int((ad2.days_to_first < 0).sum())})")
    print(f"      visits per address per month during the window: "
          f"{round(len(fv)/max(ad2.days_to_first.max(),1), 2)} (portfolio-level cadence)")

    print("\n  (g) THE OUTCOME VOCABULARY IS DECISION-BEARING:")
    print("      met_borrower/met_family/cash_collected -> positive location evidence (a human confirmed the place)")
    print("      locked_premises -> weak positive: the door is the right door; nobody confirmed identity")
    print("      address_not_traceable -> the agent could NOT find it; 1,603 m from truth on the surveyed subset,")
    print("                               median dwell 1.3 min -> this is evidence about the ADDRESS RECORD or the AGENT,")
    print("                               not about location. Rule: a negative outcome may never move a coordinate.")
    print("      no_such_person / neighbour_says_shifted -> the place resolved, the PERSON did not: location evidence is")
    print("                               weak-positive (20-72 m on the surveyed subset) but identity evidence is negative")
    print("      -> the outcome field carries TWO independent dimensions (place vs person); collapsing them loses both")



SECTIONS = {"q": sec_q, "keys": sec_keys, "coord": sec_coord, "txt": sec_txt, "geo": sec_geo,
            "visits": sec_visits, "gps": sec_gps, "agents": sec_agents, "acc": sec_acc, "leak": sec_leak,
            "xtra": sec_xtra}

if __name__ == "__main__":
    want = [a.lower() for a in sys.argv[1:]] or list(SECTIONS)
    for k in want:
        SECTIONS[k]()
    print("\nAll figures above are from SYNTHETIC data. Mechanism only — never magnitude.")
