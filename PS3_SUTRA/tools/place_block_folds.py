#!/usr/bin/env python3
"""
SUTRA — place-blocked evaluation folds (amendment A1, 2026-10-07).

Why this exists. The official split is account-level, but the signal lives in *places*:
124 of the 344 test addresses with a met-someone visit (36.0%) have a train-split met
check-in within 30 m [S94]. Random or account-level evaluation therefore scores a model
partly on evidence it has already seen. Block cross-validation is the standard remedy
wherever dependence structures exist [S67], and blocked folds are its implemented form [S68].

What it builds. Deterministic blocks and a spatially ordered 5-fold assignment:
  * a block  = addresses whose independent met-someone visits lie within CO_LINK_M of each
               other (union-find), i.e. one physical place seen through several records;
  * singletons = every address without such a neighbour (its own block);
  * folds are assigned to whole blocks, ordered by (town, centroid x) so folds are also
               spatially separated rather than interleaved.

Reads DATASET A read-only. Writes data/derived/ps3_place_blocks.csv. No training.

    python3 tools/place_block_folds.py
"""
import os
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
SEC = os.path.dirname(HERE)
A = os.path.join(SEC, "data", "official_ps3")
OUT = os.path.join(SEC, "data", "derived")

CO_LINK_M = 30.0          # evidence rule: independent met visits this close share a place
N_FOLDS = 5
MET = {"met_borrower", "met_family", "cash_collected"}

fv = pd.read_csv(f"{A}/field_visits.csv")
ad = pd.read_csv(f"{A}/addresses.csv")
sp = pd.read_csv(f"{A}/splits.csv")

met = fv[fv.outcome.isin(MET)]
cent = met.groupby("address_id").agg(cx=("checkin_x", "mean"), cy=("checkin_y", "mean")).reset_index()

# ── union-find over address pairs whose independent met check-ins are <= CO_LINK_M apart ──
parent = {}


def find(x):
    parent.setdefault(x, x)
    r = x
    while parent[r] != r:
        r = parent[r]
    while parent[x] != r:
        parent[x], x = r, parent[x]
    return r


def union(a, b):
    ra, rb = find(a), find(b)
    if ra != rb:
        parent[ra] = rb


P = cent[["cx", "cy"]].to_numpy(float)
IDS = cent.address_id.to_numpy()
pairs = 0
for i in range(len(P)):
    d = np.hypot(P[:, 0] - P[i, 0], P[:, 1] - P[i, 1])
    for j in np.where((d > 0) & (d <= CO_LINK_M))[0]:
        union(IDS[i], IDS[j])
        pairs += 1
pairs //= 2

# block id = smallest member address_id (deterministic, readable)
members = {}
for a in IDS:
    members.setdefault(find(a), []).append(a)
block_of = {a: min(v) for k, v in members.items() for a in v}

# ── assemble every address into a block (singletons included) ──
rows = []
centmap = cent.set_index("address_id")[["cx", "cy"]].to_dict("index")
pin = pd.read_csv(f"{A}/baseline_geocodes.csv").set_index("address_id")[["geocoder_x", "geocoder_y"]].to_dict("index")
split = sp.set_index("account_id")["split"].to_dict()

for r in ad.itertuples():
    bid = block_of.get(r.address_id, r.address_id)
    rows.append(dict(address_id=r.address_id, account_id=r.account_id, town_id=r.town_id,
                     split=split.get(r.account_id, "UNASSIGNED"), block_id=bid))
B = pd.DataFrame(rows)

# summary stats per block
info = []
for bid, g in B.groupby("block_id"):
    tabs = [centmap[a] for a in g.address_id if a in centmap]
    if tabs:
        Q = np.array([[t["cx"], t["cy"]] for t in tabs])
        span = float(max((np.hypot(*(Q[i] - Q[j])) for i in range(len(Q)) for j in range(i + 1, len(Q))), default=0.0))
        cx, cy = float(Q[:, 0].mean()), float(Q[:, 1].mean())
    else:
        p = [pin[a] for a in g.address_id if a in pin]
        if p:
            cx, cy = float(np.mean([q["geocoder_x"] for q in p])), float(np.mean([q["geocoder_y"] for q in p]))
        else:
            cx, cy = np.inf, np.inf
        span = np.nan
    info.append(dict(block_id=bid, town_id=g.town_id.iloc[0], size=len(g),
                     cx=cx, cy=cy, span_m=span, n_splits=g.split.nunique()))
I = pd.DataFrame(info)

# ── spatially ordered, block-level folds (deterministic) ──
I = I.sort_values(["town_id", "cx", "cy", "block_id"]).reset_index(drop=True)
I["fold"] = I.index % N_FOLDS
B = B.merge(I[["block_id", "fold", "size", "span_m", "n_splits"]], on="block_id", how="left")
B = B.sort_values(["fold", "block_id", "address_id"])
B.to_csv(f"{OUT}/ps3_place_blocks.csv", index=False)

# ── report ──
n_blocks = len(I)
n_multi = int((I["size"] > 1).sum())
print(f"place-blocked folds: {len(B)} addresses -> {n_blocks} blocks ({n_multi} multi-address, "
      f"{n_blocks - n_multi} singletons) | co-location pairs used: {pairs}")
print(f"largest block: {int(I['size'].max())} addresses | median block size {I['size'].median():.0f}")
print("fold sizes:", I.groupby("fold")["size"].sum().to_dict())
print(f"blocks crossing the official split: {int((I['n_splits'] > 1).sum())} of {n_blocks} "
      f"(addresses affected: {int(I.loc[I['n_splits'] > 1, 'size'].sum())})")

# the leakage statistic this ledger exists to expose
test_ids = set(ad[ad.account_id.isin(sp[sp.split == 'test'].account_id)].address_id)
train_ids = set(ad[ad.account_id.isin(sp[sp.split == 'train'].account_id)].address_id)
tr = met[met.address_id.isin(train_ids)][["checkin_x", "checkin_y"]].to_numpy(float)
te = met[met.address_id.isin(test_ids)]
d = np.array([np.hypot(tr[:, 0] - r.checkin_x, tr[:, 1] - r.checkin_y).min() for r in te.itertuples()])
print(f"leakage check: test addresses with a met visit {len(te)} | within 30 m of a train met check-in: "
      f"{int((d <= 30).sum())} ({(d <= 30).mean() * 100:.1f}%) | within 100 m: {int((d <= 100).sum())}")
print(f"written: data/derived/ps3_place_blocks.csv")
