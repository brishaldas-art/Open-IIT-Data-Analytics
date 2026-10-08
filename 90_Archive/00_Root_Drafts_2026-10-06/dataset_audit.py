#!/usr/bin/env python3
"""
PS2 / PS3 dataset audit — CreditNirvana synthetic collections data.

Re-runs every number quoted in PS2_PS3_DATASET_REVIEW.md.
Read-only: requires the dataset at DATASET_ROOT (default /home/user/dataset).

    python3 dataset_audit.py            # all sections
    python3 dataset_audit.py p2 p3      # selected sections (p2 | p3 | q | eco)

Every result is from *invented* synthetic data. It can validate mechanism and
build the pipeline; it cannot validate magnitude. Never quote a number from
this script as a market/accuracy/ROI claim.
"""
import sys, warnings
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 80)

ROOT = "/home/user/dataset/data"
RPC = {"rpc_ptp", "rpc_hung_up", "rpc_call_back", "rpc_refused",
       "rpc_hardship", "rpc_dispute", "rpc_claims_paid"}
DEAD = ["switched_off", "not_reachable", "number_does_not_exist"]
MET = ["met_borrower", "met_family", "cash_collected"]
WASTED = ["address_not_traceable", "no_such_person", "neighbour_says_shifted"]


def L(p, **kw):
    return pd.read_csv(f"{ROOT}/{p}", **kw)


def d(x1, y1, x2, y2):
    return np.hypot(np.asarray(x1, float) - np.asarray(x2, float),
                    np.asarray(y1, float) - np.asarray(y2, float))


def hdr(s):
    print("\n" + "=" * 100 + f"\n{s}\n" + "=" * 100)


def load_ps2():
    da = L("shared/dial_attempts.csv", low_memory=False)
    da["y"] = da.disposition.isin(RPC).astype(int)
    da["ts"] = pd.to_datetime(da.attempt_ts)
    da = da.sort_values(["account_id", "phone_id", "ts"])
    da["is_dead"] = da.network_response.isin(DEAD)
    g = da.groupby(["account_id", "phone_id"])
    da["prev_dead"] = g["is_dead"].apply(lambda s: s.shift().fillna(0).cumsum()).reset_index(level=[0, 1], drop=True)
    da["prev_wrong"] = g["disposition"].apply(lambda s: (s == "wrong_number").shift().fillna(False).cumsum()).reset_index(level=[0, 1], drop=True)
    da["prev_n"] = g.cumcount()
    return da


# ----------------------------------------------------------------------------- 0
def section_inventory():
    hdr("0. INVENTORY — every table, shape, key")
    import glob, os
    rows = []
    for f in sorted(glob.glob(f"{ROOT}/**/*.csv", recursive=True)):
        df = pd.read_csv(f, low_memory=False)
        rel = os.path.relpath(f, ROOT)
        first = df.columns[0]
        rows.append(dict(file=rel, rows=len(df), cols=df.shape[1],
                         first_col=first, uniq_first=df[first].nunique(),
                         unique_key_ok=(df[first].nunique() == len(df))))
    print(pd.DataFrame(rows).to_string(index=False))
    ph = L("ps2_right_party_contact/phones.csv")
    print(f"\nphones: rows={len(ph)} unique phone_id={ph.phone_id.nunique()} "
          f"unique (account,phone)={(ph.account_id + '|' + ph.phone_id).nunique()}  "
          f"-> phone_id is NOT a unique key")
    da = L("shared/dial_attempts.csv", low_memory=False)
    print(f"naive dial_attempts x phones join inflates {len(da)} -> {len(da.merge(ph, on='phone_id'))} rows")


# ----------------------------------------------------------------------------- 1
def section_ps2():
    da = load_ps2()
    acc = L("shared/accounts.csv")
    ph = L("ps2_right_party_contact/phones.csv")
    vc = L("ps2_right_party_contact/verified_contact_points.csv")
    st = L("ps2_right_party_contact/skip_traces.csv")
    pay = L("shared/payments.csv")
    n = len(da)

    hdr("1. PS2 — funnel, target vocabulary, logged propensity")
    print(f"attempts {n} | answered {da.network_response.eq('answered').sum()} "
          f"({100*da.network_response.eq('answered').mean():.1f}%) | RPC {da.y.sum()} ({100*da.y.mean():.1f}%)")
    print(f"RPC | answered = {100*da[da.network_response.eq('answered')].y.mean():.1f}%")
    print(f"dead network responses {da.is_dead.sum()} ({100*da.is_dead.mean():.1f}%), RPCs among them {da[da.is_dead].y.sum()}")
    print("\ndisposition vocabulary (16 values):")
    print(da.disposition.value_counts().to_string())
    print("\nlogged propensity by arm:")
    print(da.groupby("dialling_arm").selection_propensity.agg(["count", "mean", "min", "max"]).round(3).to_string())
    print(f"randomised arm share {100*da.dialling_arm.eq('random_contact_point').mean():.1f}% of attempts "
          f"({acc.dialling_arm.eq('random_contact_point').sum()} of {len(acc)} accounts)")
    print("\narm contrast (CONFOUNDED — allocation is not balanced on covariates):")
    print(da.groupby("dialling_arm").agg(n=("y", "size"), answer=("network_response", lambda s: (s == "answered").mean()),
                                         rpc=("y", "mean"), tp=("disposition", lambda s: (s == "third_party_contact").mean())).round(3).to_string())

    hdr("2. PS2 — the signal is contactability memory, not account financials")
    print("RPC per attempt by prior point-level evidence:")
    for nm, c in [("first-ever call to this point", da.prev_n == 0),
                  ("point already dead >=1 time", da.prev_dead >= 1),
                  ("point already dead >=2 times", da.prev_dead >= 2),
                  ("point already dead >=3 times", da.prev_dead >= 3),
                  ("point already marked wrong_number", da.prev_wrong >= 1)]:
        s = da[c]
        print(f"  {nm:34s} n={len(s):5d} ({100*len(s)/n:4.1f}%)  RPC/attempt={s.y.mean():.3f}  "
              f"RPCs={s.y.sum():4d} ({100*s.y.sum()/da.y.sum():4.1f}% of all RPCs)")
    print("  NOTE: blanket 'dead-point suppression' would delete 37% of all RPCs. Only the 3rd consecutive dead outcome collapses.")

    hdr("3. PS2 — provenance and relation gradients (OBSERVATIONAL, not causal)")
    m = da.merge(ph[["phone_id", "source", "relation_recorded", "priority_slot"]].drop_duplicates("phone_id", keep="first"),
                 on="phone_id", how="left")
    print(m.groupby("source").agg(n=("y", "size"), answer=("network_response", lambda s: (s == "answered").mean()),
                                  rpc=("y", "mean"), third_party=("disposition", lambda s: (s == "third_party_contact").mean()),
                                  wrong=("disposition", lambda s: (s == "wrong_number").mean())).round(3).to_string())
    print()
    print(m.groupby("relation_recorded").agg(n=("y", "size"), answer=("network_response", lambda s: (s == "answered").mean()),
                                             rpc=("y", "mean"), third_party=("disposition", lambda s: (s == "third_party_contact").mean())).round(3).to_string())

    hdr("4. PS2 — identity labels (verified_contact_points, 250 rows, all dated 2026-07-02 = AFTER the dial window)")
    A = da.groupby(["account_id", "phone_id"]).agg(n=("y", "size"), ans=("network_response", lambda s: (s == "answered").sum()),
                                                   rpc=("y", "sum"),
                                                   tp=("disposition", lambda s: (s == "third_party_contact").sum()),
                                                   wrong=("disposition", lambda s: (s == "wrong_number").sum())).reset_index()
    T = vc.merge(A, on=["account_id", "phone_id"], how="left")
    T["label"] = (T.verified_status == "borrower_number").astype(int)
    print(f"verified_status: {vc.verified_status.value_counts().to_dict()}")
    print(f"verified points with any prior call history: {T.n.notna().sum()} of {len(T)}")
    T = T.fillna({"n": 0, "ans": 0, "rpc": 0, "tp": 0, "wrong": 0})
    for nm, c in [("ever RPC", T.rpc > 0), ("ever answered", T.ans > 0), ("ever third-party", T.tp > 0),
                  ("never answered", T.ans == 0), (">=10 attempts, 0 RPC", (T.n >= 10) & (T.rpc == 0))]:
        s = T[c]
        if not len(s):
            continue
        print(f"  {nm:22s} n={len(s):3d}  P(borrower)={s.label.mean():.2f}  "
              f"P(3rd party)={(s.verified_status == 'third_party_number').mean():.2f}  "
              f"P(not borrower)={(s.verified_status == 'not_borrower_number').mean():.2f}")
    Tf = T.merge(ph.drop_duplicates(["account_id", "phone_id"]), on=["account_id", "phone_id"], how="left")
    print("\nP(borrower) by recorded provenance (n small — directional only):")
    print(Tf.assign(bor=T.label).groupby("source").agg(n=("bor", "size"), p_borrower=("bor", "mean"),
                                                       p_3rd=("verified_status", lambda s: (s == "third_party_number").mean())).round(3).to_string())
    try:
        from sklearn.linear_model import LogisticRegression
        from sklearn.model_selection import cross_val_score, StratifiedKFold
        cv = StratifiedKFold(5, shuffle=True, random_state=0)
        X1 = pd.get_dummies(Tf[["source", "relation_recorded", "n", "ans", "rpc", "tp", "wrong"]],
                            columns=["source", "relation_recorded"], drop_first=True).fillna(-1)
        X0 = pd.get_dummies(Tf[["source", "relation_recorded"]], drop_first=True).fillna(-1)
        a1 = cross_val_score(LogisticRegression(max_iter=2000), X1, T.label, cv=cv, scoring="roc_auc")
        a0 = cross_val_score(LogisticRegression(max_iter=2000), X0, T.label, cv=cv, scoring="roc_auc")
        print(f"\nCV AUC provenance+behaviour {a1.mean():.3f}+/-{a1.std():.3f} | provenance only {a0.mean():.3f}+/-{a0.std():.3f} "
              f"| majority-class {max(T.label.mean(), 1-T.label.mean()):.3f}")
    except Exception as e:  # sklearn optional
        print("sklearn unavailable:", e)

    hdr("5. PS2 — skip-trace ROI (the 'prioritisation' question)")
    st["hit"] = (st.result != "no_new_info").astype(int)
    print(f"traces {len(st)} over {st.account_id.nunique()} accounts; single trigger rule: {st.trigger_rule.unique()}")
    print(f"results {st.result.value_counts().to_dict()}")
    print(f"spend Rs {st.cost_inr.sum():.0f}; cost/trace Rs {st.cost_inr.mean():.0f}; "
          f"cost/HIT Rs {st.cost_inr.sum()/st.hit.sum():.0f}; wasted on no_new_info Rs {st[st.result=='no_new_info'].cost_inr.sum():.0f} "
          f"({100*st[st.result=='no_new_info'].cost_inr.sum()/st.cost_inr.sum():.0f}% of trace spend)")
    hp = ph[ph.source == "skip_trace"]
    tpts = da.merge(hp[["account_id", "phone_id"]].drop_duplicates(), on=["account_id", "phone_id"])
    print(f"traced points dialled: {len(tpts)} attempts on {tpts.phone_id.nunique()} numbers -> RPC {tpts.y.sum()} "
          f"({100*tpts.y.mean():.1f}% vs {100*da.y.mean():.1f}% overall); Rs {st.cost_inr.sum()/max(tpts.y.sum(),1):.0f} per RPC generated")
    S = st.merge(acc, on="account_id", how="left").merge(L("shared/splits.csv"), on="account_id", how="left")
    print("\ntrace hit rate by account segment (all near the 22.8% base rate):")
    for c in ["bucket_start", "portfolio", "income_type"]:
        print(S.groupby(c).agg(n=("hit", "size"), hit=("hit", "mean")).round(3).to_string(), "\n")
    try:
        from sklearn.linear_model import LogisticRegression
        from sklearn.model_selection import cross_val_score, StratifiedKFold
        fail = da[~da.network_response.eq("answered")]
        pre = fail.groupby("account_id").agg(fails=("y", "size"),
                                             dead=("is_dead", "mean"), agent_n=("agent_id", "nunique"))
        P = S.merge(pre, on="account_id", how="left")
        X = pd.get_dummies(P[["bucket_start", "portfolio", "income_type", "bureau_score_band",
                              "fails", "dead", "agent_n", "dpd_start", "outstanding", "ability_to_pay_estimate"]],
                           drop_first=True).fillna(-1)
        a = cross_val_score(LogisticRegression(max_iter=2000), X, P.hit.values,
                            cv=StratifiedKFold(5, shuffle=True, random_state=0), scoring="roc_auc")
        print(f"predicting trace SUCCESS from pre-trace features: CV AUC {a.mean():.3f}+/-{a.std():.3f} "
              f"(majority-class {max(P.hit.mean(), 1-P.hit.mean()):.3f})  <-- no usable signal")
    except Exception as e:
        print("sklearn unavailable:", e)

    hdr("6. PS2 — shared numbers: cross-account exposure")
    sh = ph.groupby("phone_masked").account_id.nunique()
    key = ph.sort_values("added_date").drop_duplicates("phone_id").set_index("phone_id").phone_masked
    da["shared"] = da.phone_id.map(key).map(sh) > 1
    print(f"distinct numbers {ph.phone_masked.nunique()}; shared by >1 account {(sh>1).sum()}; max accounts on one number {sh.max()}")
    print(f"phones rows sitting on a shared number {int((ph.phone_masked.map(sh)>1).sum())} ({100*(ph.phone_masked.map(sh)>1).mean():.0f}%)")
    print(f"attempts to a shared number {int(da.shared.sum())} ({100*da.shared.mean():.1f}%) | "
          f"RPC {da[da.shared].y.mean():.3f} vs {da[~da.shared].y.mean():.3f} exclusive | "
          f"third-party {da[da.shared].disposition.eq('third_party_contact').mean():.3f} vs "
          f"{da[~da.shared].disposition.eq('third_party_contact').mean():.3f}")

    hdr("7. PS2 — timing, and whether 'wait' is representable")
    da["hr"] = da.ts.dt.hour
    print("RPC rate by hour (attempts exist only inside 08:00-18:59):")
    print(da.groupby("hr").agg(n=("y", "size"), answer=("network_response", lambda s: (s == "answered").mean()),
                               rpc=("y", "mean")).round(3).to_string())
    da["seq"] = da.groupby("account_id").cumcount() + 1
    print("\nRPC rate by attempt sequence:")
    print(da.groupby(pd.cut(da.seq, [0, 3, 8, 15, 25, 60])).agg(n=("y", "size"), rpc=("y", "mean")).round(3).to_string())
    gap = da.groupby("account_id").ts.apply(lambda s: s.diff().dt.total_seconds().max() / 86400)
    print(f"\naccounts whose longest call-free gap exceeds 7 days: {(gap>7).sum()} of {len(gap)} "
          f"-> a 'wait' action is representable as a real decision, not a hypothetical")

    hdr("8. PS2 — payment attribution (constructible window, no campaign field)")
    pay["ts"] = pd.to_datetime(pay.payment_ts)
    att = da[da.y == 1][["account_id", "ts"]]
    j = pay.merge(att, on="account_id", suffixes=("_pay", "_att"))
    j["gap_d"] = (j.ts_pay - j.ts_att).dt.total_seconds() / 86400
    win = j[(j.gap_d >= 0) & (j.gap_d <= 7)]
    print(f"payments {len(pay)} | accounts with a payment {pay.account_id.nunique()} | "
          f"payments with a prior RPC within 7 days {len(win)} ({100*len(win)/len(pay):.0f}%), median gap {win.gap_d.median():.1f} d")
    print("No campaign/case id exists, so payment-after-contact is a correlation, never a measured increment (R10.4).")


# ----------------------------------------------------------------------------- 2
def section_p3():
    ad = L("shared/addresses.csv")
    bg = L("ps3_geocoder/baseline_geocodes.csv")
    sv = L("ps3_geocoder/surveyed_addresses.csv")
    lo = L("ps3_geocoder/localities.csv")
    lm = L("ps3_geocoder/landmarks_poi.csv")
    tw = L("ps3_geocoder/towns.csv")
    gps = L("ps3_geocoder/visit_gps_points.csv")
    fv = L("shared/field_visits.csv")

    hdr("9. PS3 — the baseline to beat (100 surveyed addresses = only ground truth in the package)")
    s = sv.merge(ad, on="address_id").merge(bg, on="address_id", how="left")
    s["err"] = d(s.surveyed_x, s.surveyed_y, s.geocoder_x, s.geocoder_y)
    print(s.err.describe(percentiles=[.5, .75, .9, .95]).round(0).to_string())
    print("hit rates: " + "  ".join(f"<{k}m {100*(s.err<k).mean():.0f}%" for k in (100, 250, 500, 1000)))
    print("\nTHE KEY TABLE — error by the vendor's own precision label (this becomes the radius calibration):")
    print(s.groupby("precision").err.agg(["count", "median", "mean"]).round(0).to_string())
    print(f"\nbook coverage: {len(bg)} geocodes for {ad.address_id.nunique()} addresses "
          f"({ad.address_id.nunique()-len(bg)} missing, {100*(1-len(bg)/ad.address_id.nunique()):.1f}%)")
    print("survey vs book precision mix (selection check):")
    print(pd.concat([bg.precision.value_counts(normalize=True).rename("book"),
                     s.precision.value_counts(normalize=True).rename("survey100")], axis=1).round(3).to_string())

    hdr("10. PS3 — large-sample confirmation: baseline geocode -> actual agent check-in (proxy ground truth)")
    v = fv.merge(bg, on="address_id", how="left")
    v["nav"] = d(v.checkin_x, v.checkin_y, v.geocoder_x, v.geocoder_y)
    met = v[v.outcome.isin(MET)]
    print(f"visits with a geocode {v.nav.notna().sum()}; met-someone visits {len(met)}")
    print(f"met subset: median {met.nav.median():.0f} m, p90 {met.nav.quantile(.9):.0f} m, "
          + "  ".join(f"<{k}m {100*(met.nav<k).mean():.0f}%" for k in (100, 250, 500)))
    print("\nby precision class of the geocode:")
    print(met.groupby("precision").nav.agg(["count", "median", lambda s: (s < 100).mean()]).round(2).to_string())
    print("\nby outcome (negative outcomes are CLOSER to the pin — agents give up early, median dwell 2 min):")
    print(v.groupby("outcome").agg(n=("visit_id", "size"), nav_median=("nav", "median"),
                                   dwell_min=("dwell_s", lambda s: s.median() / 60)).round(0).to_string())

    hdr("11. PS3 — can free data beat the commercial geocoder? (candidate = locality centroid)")
    def match_loc(txt, town):
        t = txt.lower()
        best = None
        for _, r in lo[lo.town_id == town].iterrows():
            k = r.locality_name.lower().split()[0][:6]
            if len(k) >= 5 and k in t and (best is None or len(k) > best[3]):
                best = (r.centroid_x, r.centroid_y, r.locality_name, len(k))
        return best
    # NB: do not name this column "loc" — it shadows pandas' .loc indexer.
    s["loc_match"] = [match_loc(r.address_text, r.town_id) for _, r in s.iterrows()]
    s["err_loc"] = [np.nan if not isinstance(c, tuple) else d(a_, b_, c[0], c[1])
                    for a_, b_, c in zip(s.surveyed_x, s.surveyed_y, s.loc_match)]
    print(f"locality matched in text: {s.err_loc.notna().sum()} of {len(s)}")
    print(f"median error: baseline {s.err.median():.0f} m vs locality centroid {s.err_loc.median():.0f} m")
    for k in (100, 250, 500, 1000):
        print(f"  <{k}m: baseline {100*(s.err<k).mean():3.0f}%   locality {100*(s.err_loc<k).mean():3.0f}%")
    # oracle over all localities in town
    orc = []
    for _, r in s.iterrows():
        cand = lo[lo.town_id == r.town_id]
        orc.append(min(d(r.surveyed_x, r.surveyed_y, c.centroid_x, c.centroid_y) for _, c in cand.iterrows()))
    s["orc"] = orc
    print(f"\nORACLE over all 12 localities in the town: median {s.orc.median():.0f} m, p90 {s.orc.quantile(.9):.0f} m, "
          f"<100m {100*(s.orc<100).mean():.0f}%  ->  locality centroid IS the resolution ceiling of the free data")
    # naive POI snap failure
    lm["kw"] = lm.landmark_type.str.replace("_", " ")
    rows = []
    for _, r in s.iterrows():
        cands = lm[(lm.town_id == r.town_id) & lm.kw.apply(lambda k: k in r.address_text.lower())]
        rows.append(np.nan if not len(cands) else d(r.surveyed_x, r.surveyed_y, cands.iloc[0].x, cands.iloc[0].y))
    s["err_poi_naive"] = rows
    sub = s[s.err_poi_naive.notna()]
    print(f"\nnaive POI snap (first same-type landmark in the town, no disambiguation) on {len(sub)} addresses: "
          f"median {sub.err_poi_naive.median():.0f} m vs baseline {sub.err.median():.0f} m "
          f"-> worse in {100*(sub.err_poi_naive>sub.err).mean():.0f}% of cases")
    print(f"landmark names repeating across towns: {(lm.groupby(lm.name.str.lower()).town_id.nunique()>1).sum()} of {lm.name.str.lower().nunique()} "
          "-> R3.4 (scoping) is not a nicety")

    hdr("12. PS3 — the learning loop: what a field visit is actually worth")
    j = fv.merge(sv, on="address_id").merge(bg, on="address_id", how="left")
    j["err_base"] = d(j.surveyed_x, j.surveyed_y, j.geocoder_x, j.geocoder_y)
    j["err_visit"] = d(j.surveyed_x, j.surveyed_y, j.checkin_x, j.checkin_y)
    jm = j[j.outcome.isin(MET)]
    print(f"surveyed addresses with >=1 visit: {j.address_id.nunique()} of 100; visits on them {len(j)}; met-someone visits {len(jm)}")
    print(f"met visits: median error {jm.err_base.median():.0f} m -> {jm.err_visit.median():.0f} m "
          f"({100*(jm.err_visit<jm.err_base).mean():.0f}% improve); <100m {100*(jm.err_visit<100).mean():.0f}%")
    print("per outcome:")
    print(j.groupby("outcome")[["err_base", "err_visit"]].median().round(0).to_string())
    print(f"\nshare of ALL visits on surveyed addresses producing a <100 m fix: {100*(j.err_visit<100).mean():.0f}%")

    hdr("13. PS3 — integrity: the dataset contains a deliberately planted bad actor")
    g = gps.groupby("visit_id").agg(n=("x", "size"), xmed=("x", "median"), ymed=("y", "median"))
    f = fv.merge(g, left_on="visit_id", right_index=True, how="left")
    f["trail_disagree"] = d(f.xmed, f.ymed, f.checkin_x, f.checkin_y)
    f["dup"] = f.photo_hash.duplicated(keep=False)
    print(f"visits {len(f)} | median GPS points/visit {f.n.median():.0f} (p90 {f.n.quantile(.9):.0f}) | median accuracy {f.gps_accuracy_m.median():.1f} m")
    print(f"check-in >500 m from own trail median: {(f.trail_disagree>500).sum()} ({100*(f.trail_disagree>500).mean():.1f}%)")
    print(f"visits sharing a duplicated photo_hash: {f.dup.sum()}")
    a = f.groupby("agent_id").agg(visits=("visit_id", "size"), dup=("dup", "sum"),
                                  met=("outcome", lambda s: s.isin(["met_borrower", "met_family"]).mean()))
    a["dup_share"] = (a.dup / a.visits).round(3)
    print(a.sort_values("dup_share", ascending=False).round(2).to_string())
    print("-> one collector supplies 162 of 172 duplicated photos (26.6% of that agent's visits, others <=1%).")
    print("   No pipeline without collector-level anomaly monitoring (R10.3) can avoid absorbing those observations.")

    hdr("14. PS3 — town/locality structure and address text")
    print(tw.to_string(index=False))
    print(f"\nlocalities {len(lo)} ({lo.groupby('town_id').size().to_dict()}); "
          f"pincodes shared by >1 locality: {(lo.groupby('pincode').size()>1).sum()}")
    print(f"POIs {len(lm)} ({lm.groupby('town_id').size().to_dict()}), {lm.landmark_type.nunique()} types")
    ad = ad.copy()
    ad["pin"] = ad.address_text.str.extract(r"(\d{6})")[0]
    ad["has_lm"] = ad.address_text.str.lower().str.contains(r"near|behind|opp|bagal|paas|hattira|beside|nr ")
    print(f"addresses with a 6-digit PIN: {100*ad.pin.notna().mean():.0f}% | matching a known locality PIN: {100*ad.pin.isin(lo.pincode.astype(str)).mean():.0f}%")
    print(f"addresses carrying a landmark phrase: {100*ad.has_lm.mean():.0f}% | median length {ad.address_text.str.len().median():.0f} chars")
    print("address_type mix: " + str(ad.address_type.value_counts().to_dict()) + "  (office/permanent_native must never receive a notice)")
    print("address_style: " + "; ".join(f"{r.town_name}={r.address_style}" for _, r in tw.iterrows()))


# ----------------------------------------------------------------------------- 3
def section_econ():
    fv = L("shared/field_visits.csv")
    hdr("15. FIELD ECONOMICS — what exists, what must be a parameter")
    fv["hrs"] = fv.dwell_s / 3600
    w = fv.outcome.isin(WASTED)
    print(f"visits {len(fv)} on {fv.address_id.nunique()} addresses ({100*fv.address_id.nunique()/3117:.0f}% of the book)")
    print(f"logged dwell hours {fv.hrs.sum():.0f} h; median dwell {fv.dwell_s.median()/60:.1f} min "
          f"(productive {fv[~w].dwell_s.median()/60:.1f} min vs wasted {fv[w].dwell_s.median()/60:.1f} min)")
    print(f"productive (met_* + cash) {100*fv.outcome.isin(MET).mean():.0f}% | wasted (not_traceable/no_such_person/shifted) {100*w.mean():.0f}%")
    print(f"hours on wasted outcomes {fv[w].hrs.sum():.0f} h ({100*fv[w].hrs.sum()/fv.hrs.sum():.0f}% of field hours)")
    cash = fv[fv.outcome == "cash_collected"]
    amt = cash.remark.str.extract(r"([\d,]{3,})")[0].str.replace(",", "").astype(float)
    print(f"\ncash_collected {len(cash)} visits; amount recoverable ONLY from free text: {amt.notna().sum()} parseable, "
          f"sum Rs {amt.sum():.0f}")
    print("structured columns absent from field_visits: amount, travel time, distance, fuel, vehicle, notice-served")
    print("structured cost columns absent from dial_attempts: call cost, agent minute, outcome value")
    print("-> every rupee figure in the EV gate (R5.1/R5.2) MUST be a named parameter with a range, never learned.")


SECTIONS = {"q": section_inventory, "p2": section_ps2, "p3": section_p3, "eco": section_econ}

if __name__ == "__main__":
    want = [a.lower() for a in sys.argv[1:]] or ["q", "p2", "p3", "eco"]
    for k in want:
        SECTIONS[k]()
    print("\nAll figures above are from SYNTHETIC data. Mechanism only — never magnitude.")
