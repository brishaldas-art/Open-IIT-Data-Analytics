#!/usr/bin/env python3
"""
SUTRA — feasibility probe for the OPERATIONAL PLACE-NEIGHBOUR INDEX (2026-10-07).

Question: using ONLY official data, can confirmed historical places serve as extra candidate
anchors for a new address — i.e. does a lightweight operational index have substance, or is it
a graph-database idea with no measurable retrieval value?

Method (oracle-style capacity probe; no fitting, evaluation-only):
  1. Confirmed places = addresses with >=1 met-someone visit; place coordinate = mean of their
     met check-ins.                                   (reads official field_visits)
  2. For each of the 100 surveyed addresses, take the official cold candidate set
     (data/derived/candidates_coldstart.csv) and collect confirmed places within R of an anchor.
  3. Compare min distance-to-truth of: official candidates alone vs candidates + place neighbours.
  4. Leave-block-out variant: drop neighbours that share the queried address's place block, so the
     gain cannot be pure self-place leakage.

Outputs data/derived/derived_place_neighbour_probe.csv + a printed summary. No training, no
external data, official dataset read-only.

    python3 tools/neighbour_index_probe.py
"""
import os
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
SEC = os.path.dirname(HERE)
A = os.path.join(SEC, "data", "official_ps3")
D = os.path.join(SEC, "data", "derived")
R_NEIGHBOUR = 1000.0          # neighbourhood radius for the index (metres, local plane)
MET = {"met_borrower", "met_family", "cash_collected"}

fv = pd.read_csv(f"{A}/field_visits.csv")
met = fv[fv.outcome.isin(MET)]
places = met.groupby("address_id").agg(px=("checkin_x", "mean"), py=("checkin_y", "mean")).reset_index()

cand = pd.read_csv(f"{D}/candidates_coldstart.csv")
truth = pd.read_csv(f"{A}/surveyed_addresses.csv")
blocks = pd.read_csv(f"{D}/ps3_place_blocks.csv")[["address_id", "block_id"]]
block_of = blocks.set_index("address_id").block_id.to_dict()
place_block = {r.address_id: block_of.get(r.address_id, r.address_id) for r in places.itertuples()}

P = places[["px", "py"]].to_numpy(float)
PIDS = places.address_id.to_numpy()

rows = []
for r in truth.itertuples():
    c = cand[cand.address_id == r.address_id]
    if c.empty:
        continue
    pts = c[["x", "y"]].to_numpy(float)
    arm_err = np.hypot(pts[:, 0] - r.surveyed_x, pts[:, 1] - r.surveyed_y)
    baseline = float(arm_err.min())

    # anchors: locality_centroid when present, else the full candidate set (fallback anchor region)
    loc = c[c.arm == "locality_centroid"]
    anchors = loc[["x", "y"]].to_numpy(float) if len(loc) else pts

    keep = (PIDS != r.address_id)
    d_anchor = np.min(np.hypot(
        P[keep][:, None, 0] - anchors[None, :, 0], P[keep][:, None, 1] - anchors[None, :, 1]), axis=1)
    near = np.where(d_anchor <= R_NEIGHBOUR)[0]
    nbr_ids = PIDS[keep][near]
    nbr_pts = P[keep][near]

    # leave-block-out: neighbours sharing the queried address's place block are removed
    keep2 = np.array([place_block.get(i, i) != block_of.get(r.address_id, r.address_id) for i in nbr_ids])
    nbr_pts_lbo = nbr_pts[keep2]

    def aug(base_err, extra):
        if len(extra) == 0:
            return base_err, base_err
        e = np.hypot(extra[:, 0] - r.surveyed_x, extra[:, 1] - r.surveyed_y)
        return base_err, float(min(base_err, e.min()))

    _, aug_all = aug(baseline, nbr_pts)
    _, aug_lbo = aug(baseline, nbr_pts_lbo)
    rows.append(dict(address_id=r.address_id, n_candidates=len(pts), n_neighbours=len(nbr_pts),
                     n_neighbours_lbo=len(nbr_pts_lbo), baseline_err_m=baseline,
                     knob_err_m=aug_all, knob_err_lbo_m=aug_lbo))


res = pd.DataFrame(rows)
res.to_csv(f"{D}/derived_place_neighbour_probe.csv", index=False)

# ── control 1: placebo — same number of RANDOM points in the same disc, 20 draws ──
rng = np.random.default_rng(20261007)
placebo_med, placebo100 = [], []
for trial in range(20):
    errs = []
    for r in truth.itertuples():
        c = cand[cand.address_id == r.address_id]
        if c.empty:
            continue
        pts = c[["x", "y"]].to_numpy(float)
        loc = c[c.arm == "locality_centroid"]
        anchors = loc[["x", "y"]].to_numpy(float) if len(loc) else pts
        k = max(1, int(res.loc[res.address_id == r.address_id, "n_neighbours"].iloc[0]))
        ang = rng.uniform(0, 2 * np.pi, k)
        rad = R_NEIGHBOUR * np.sqrt(rng.uniform(0, 1, k))
        a0 = anchors[0]
        pts_r = np.c_[a0[0] + rad * np.cos(ang), a0[1] + rad * np.sin(ang)]
        e = np.hypot(pts_r[:, 0] - r.surveyed_x, pts_r[:, 1] - r.surveyed_y)
        base = np.hypot(pts[:, 0] - r.surveyed_x, pts[:, 1] - r.surveyed_y).min()
        errs.append(min(base, e.min()))
    errs = np.array(errs)
    placebo_med.append(float(np.median(errs))); placebo100.append(float((errs <= 100).mean() * 100))
print(f"placebo (random points, same count) : median of 20 draws = {np.median(placebo_med):.1f} m | "
      f"<=100 m {np.median(placebo100):.1f}%")

# ── control 2: naive nearest-neighbour estimate (no ranker): the confirmed place closest to the anchor ──
naive = []
for r in truth.itertuples():
    c = cand[cand.address_id == r.address_id]
    if c.empty:
        continue
    pts = c[["x", "y"]].to_numpy(float)
    loc = c[c.arm == "locality_centroid"]
    a0 = (loc[["x", "y"]].to_numpy(float) if len(loc) else pts)[0]
    keep = PIDS != r.address_id
    d = np.hypot(P[keep][:, 0] - a0[0], P[keep][:, 1] - a0[1])
    j = int(np.argmin(d))
    q = P[keep][j]
    naive.append(float(np.hypot(q[0] - r.surveyed_x, q[1] - r.surveyed_y)))
naive = np.array(naive)
print(f"naive nearest confirmed place       : median {np.median(naive):.1f} m | <=100 m {(naive <= 100).mean()*100:.1f}%")
print(f"LBO actually removed neighbours for {int((res.n_neighbours_lbo < res.n_neighbours).sum())} addresses "
      f"(removed total {int((res.n_neighbours - res.n_neighbours_lbo).sum())} neighbours)")


n = len(res)
print(f"surveyed addresses scored: {n} | confirmed places in index: {len(places)}")
print(f"coverage: addresses with >=1 neighbour within {R_NEIGHBOUR:.0f} m: "
      f"{(res.n_neighbours > 0).mean() * 100:.1f}%  (median neighbours {res.n_neighbours.median():.0f})")
print(f"baseline official-candidate oracle : median {res.baseline_err_m.median():.1f} m | "
      f"<=100 m {(res.baseline_err_m <= 100).mean() * 100:.1f}%")
print(f"+ place-neighbour index            : median {res.knob_err_m.median():.1f} m | "
      f"<=100 m {(res.knob_err_m <= 100).mean() * 100:.1f}%")
print(f"+ index, leave-block-out           : median {res.knob_err_lbo_m.median():.1f} m | "
      f"<=100 m {(res.knob_err_lbo_m <= 100).mean() * 100:.1f}%")
gain = res[res.knob_err_m < res.baseline_err_m - 1e-9]
gain_lbo = res[res.knob_err_lbo_m < res.baseline_err_m - 1e-9]
print(f"addresses where the index improves the oracle: {len(gain)} ({len(gain)/n*100:.0f}%)  "
      f"| leave-block-out: {len(gain_lbo)} ({len(gain_lbo)/n*100:.0f}%)")
print(f"newly <=100 m thanks to the index: {int(((res.knob_err_m <= 100) & (res.baseline_err_m > 100)).sum())}  "
      f"| leave-block-out: {int(((res.knob_err_lbo_m <= 100) & (res.baseline_err_m > 100)).sum())}")
print("written: data/derived/derived_place_neighbour_probe.csv")
