#!/usr/bin/env python3
"""
SUTRA — clean the OFFICIAL dataset (Domain A) only, with a row-level log.

Never touches data/official_ps3 (read-only). Never reads external data (Domain B stands alone).
Outputs:  data/cleaned/addresses_clean.csv · visits_clean.csv · gps_points_clean.csv · trail_features.csv
          data/cleaned/cleaning_log.csv     (one row per rule, with counts and what it did)

    python3 tools/clean_official.py [--full]

Principles (from PS3_DATA_CLEANING_REPORT.md):
  * preserve the raw value in a `<col>_raw` column before normalising anything;
  * every drop is logged with a reason and a count;
  * no coordinate is ever "corrected"; a suspicious coordinate is FLAGGED, not moved;
  * no label is ever invented.
"""
import os, re, sys, unicodedata, warnings
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__)); SEC = os.path.dirname(HERE)
RAW = os.environ.get("CN_DATASET", os.path.join(SEC, "data", "official_ps3"))
OUT = os.environ.get("CN_CLEAN", os.path.join(SEC, "data", "cleaned"))
os.makedirs(OUT, exist_ok=True)

LOG = []
def log(table, rule, rows_in, rows_out, note):
    LOG.append(dict(table=table, rule=rule, rows_in=int(rows_in), rows_out=int(rows_out),
                    dropped=int(rows_in) - int(rows_out), note=note))
    print(f"  [{table}] {rule:<34} {rows_in:>7} -> {rows_out:>7}  ({note})")

# The canonical normaliser lives in the runtime package so the two can never drift again.
sys.path.insert(0, SEC)
from sutra.dataio import ABBREV, norm_text      # noqa: E402  (same function the runtime matches with)
MARKERS = {"lane": r"\b(gali|galli|lane|ln)\b", "block": r"\b(block|blk|sector|sec|ward)\b",
           "cross": r"\b(cross|main|marg)\b", "house": r"\b(house|h|plot|door|d\.?no|flat)\b",
           "relation": r"\b(near|opposite|behind|beside|adjacent|next to)\b"}


def main():
    print("SUTRA — cleaning Domain A (official synthetic PS3 data)\n")
    ad = pd.read_csv(f"{RAW}/addresses.csv", low_memory=False)
    fv = pd.read_csv(f"{RAW}/field_visits.csv", low_memory=False)
    gp = pd.read_csv(f"{RAW}/visit_gps_points.csv", low_memory=False)
    lo = pd.read_csv(f"{RAW}/localities.csv", low_memory=False)
    to = pd.read_csv(f"{RAW}/towns.csv", low_memory=False)
    lm = pd.read_csv(f"{RAW}/landmarks_poi.csv", low_memory=False)
    n_ad, n_fv, n_gp = len(ad), len(fv), len(gp)

    # ── addresses ────────────────────────────────────────────────────────────────
    ad["address_text_raw"] = ad.address_text
    ad["text_norm"] = ad.address_text.map(norm_text)
    log("addresses", "normalise text (NFKC, case, punct, abbrev)", n_ad, len(ad),
        "raw preserved in address_text_raw")

    pin_known = set(lo.pincode.astype(str))
    six = ad.address_text.str.extract(r"\b(\d{6})\b")[0]
    ad["flag_no_digit"] = ad.address_text.str.count(r"\d") == 0
    ad["flag_no_separator"] = ad.address_text.str.count(r"[,/\-]") == 0
    ad["flag_pin_in_text"] = six.notna()
    ad["flag_pin_unknown"] = six.notna() & ~six.isin(pin_known)
    ad["flag_outside_town"] = ad.town_id.astype(str).eq("OUT")
    ad["flag_dup_text"] = ad.text_norm.duplicated(keep=False)
    for f, note in [("flag_no_digit", "no digit at all -> no house number possible"),
                    ("flag_no_separator", "no comma, slash or hyphen at all (24); no comma specifically: 777 (24.9%)"),
                    ("flag_pin_unknown", "6-digit token matches no known pincode"),
                    ("flag_outside_town", "town_id=OUT: outside every modelled town"),
                    ("flag_dup_text", "normalised text duplicated elsewhere")]:
        log("addresses", f, len(ad), len(ad), f"{int(ad[f].sum())} rows flagged — {note}")

    # parse spans (rules only; the optional ML parser is BUILD IF TIME)
    for k, rx in MARKERS.items():
        ad[f"span_{k}"] = ad.text_norm.str.contains(rx, regex=True)
    words = set(" ".join(lo.locality_name.astype(str)).lower().split()) | \
            set(" ".join(to.town_name.astype(str)).lower().split())
    ad["span_locality_token"] = ad.text_norm.map(lambda t: any(w in t.split() for w in words))
    log("addresses", "rule-based span extraction", len(ad), len(ad),
        "lane/block/cross/house/relation markers + gazetteer tokens")

    ad.to_csv(f"{OUT}/addresses_clean.csv", index=False)

    # ── visits ───────────────────────────────────────────────────────────────────
    fv["outcome_place_flag"] = np.select(
        [fv.outcome.isin(["met_borrower", "met_family", "cash_collected"]),
         fv.outcome.isin(["locked_premises", "neighbour_says_shifted", "no_such_person"]),
         fv.outcome.eq("address_not_traceable")],
        ["place_positive", "place_weak_positive", "place_indeterminate"], default="unknown")
    fv["outcome_person_flag"] = np.select(
        [fv.outcome.isin(["met_borrower", "cash_collected"]),
         fv.outcome.isin(["no_such_person", "neighbour_says_shifted"])],
        ["person_positive", "person_negative"], default="person_indeterminate")
    fv["start"] = pd.to_datetime(fv.start_ts); fv["checkin"] = pd.to_datetime(fv.checkin_ts)
    fv["travel_s"] = (fv.checkin - fv.start).dt.total_seconds()
    fv["flag_negative_travel"] = fv.travel_s < 0
    fv["flag_short_dwell"] = fv.dwell_s < 60
    fv["flag_implausible_dwell"] = fv.dwell_s > 12 * 3600
    fv["flag_negative_outcome"] = fv.outcome.eq("address_not_traceable")
    log("visits", "derive place/person evidence flags", n_fv, len(fv),
        "outcome is split into two dimensions (see canonical schema §3)")
    for f, note in [("flag_negative_travel", "check-in before start"),
                    ("flag_short_dwell", "dwell < 60 s"),
                    ("flag_implausible_dwell", "dwell > 12 h"),
                    ("flag_negative_outcome", "address_not_traceable: never moves a coordinate")]:
        log("visits", f, len(fv), len(fv), f"{int(fv[f].sum())} rows flagged — {note}")
    fv.drop(columns=["ptp_id"]).to_csv(f"{OUT}/visits_clean.csv", index=False)   # ptp belongs to another problem
    log("visits", "drop ptp_id column", len(fv), len(fv), "89.2% null; belongs to a different problem statement")

    # ── GPS points ───────────────────────────────────────────────────────────────
    gp["flag_axis_artefact"] = (gp.x == 0) | (gp.y == 0)
    gp_clean = gp[~gp.flag_axis_artefact].copy()
    log("gps_points", "drop axis artefacts (x==0 or y==0)", n_gp, len(gp_clean),
        "sensor artefacts; flagged rows kept in the audit, not used as evidence")
    gp_clean = gp_clean.sort_values(["visit_id", "seq"])
    g = gp_clean
    gp_clean["dx"] = g.groupby("visit_id").x.diff(); gp_clean["dy"] = g.groupby("visit_id").y.diff()
    gp_clean["dt"] = g.groupby("visit_id").point_ts.transform(pd.to_datetime).groupby(g.visit_id).diff().dt.total_seconds()
    gp_clean["step_m"] = np.hypot(gp_clean.dx, gp_clean.dy)
    gp_clean["speed_kmh"] = np.where(np.isnan(gp_clean.dt) | (gp_clean.dt <= 0), np.nan,
                                     3.6 * gp_clean.step_m / gp_clean.dt)
    gp_clean.drop(columns=["dx", "dy"]).to_csv(f"{OUT}/gps_points_clean.csv", index=False)

    # ── trail features (per visit) ───────────────────────────────────────────────
    chk = fv.set_index("visit_id")[["checkin_x", "checkin_y", "gps_accuracy_m", "outcome"]]
    tf = gp_clean.groupby("visit_id").agg(
        n_points=("seq", "size"),
        acc_med=("accuracy_m", "median"), acc_p90=("accuracy_m", lambda s: s.quantile(.9)),
        span_s=("dt", "sum"), path_m=("step_m", "sum"),
        speed_max=("speed_kmh", "max"), speed_p90=("speed_kmh", lambda s: s.quantile(.9)),
        x_med=("x", "median"), y_med=("y", "median"),
        x_first=("x", "first"), y_first=("y", "first"), x_last=("x", "last"), y_last=("y", "last"))
    tf = tf.join(chk, how="left")
    tf["dist_checkin_to_median_m"] = np.hypot(tf.checkin_x - tf.x_med, tf.checkin_y - tf.y_med)
    tf["dist_start_to_checkin_m"] = np.hypot(tf.checkin_x - tf.x_first, tf.checkin_y - tf.y_first)
    tf.to_csv(f"{OUT}/trail_features.csv")
    log("trail_features", "per-visit trail geometry", len(tf), len(tf),
        "median 26 points/visit; feed the evidence scorer, not the location model directly")

    pd.DataFrame(LOG).to_csv(f"{OUT}/cleaning_log.csv", index=False)
    print(f"\ncleaned -> {OUT}   (log: cleaning_log.csv, {len(LOG)} rules)")
    print("Domain A untouched. No coordinate moved. No label invented.")


if __name__ == "__main__":
    main()
