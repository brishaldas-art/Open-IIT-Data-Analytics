#!/usr/bin/env python3
"""Rebuild this section's acceptance table: derived/derived_ps2_policy_baselines.csv
   — the policies the PS2 demo must beat, measured on the supplied split.
   Reads ../data/raw ; writes ../data/derived . Override with $CN_DATASET / $CN_OUT."""
import os, pandas as pd, numpy as np, warnings
warnings.filterwarnings('ignore')
_HERE = os.path.dirname(os.path.abspath(__file__)); _SEC = os.path.dirname(_HERE)
D = os.environ.get('CN_DATASET', os.path.join(_SEC, 'data', 'raw')).rstrip('/') + '/'
OUT = os.environ.get('CN_OUT', os.path.join(_SEC, 'data', 'derived')).rstrip('/') + '/'
os.makedirs(OUT, exist_ok=True)
# --- PS2: policy baselines ---
da = pd.read_csv(D + 'dial_attempts.csv', low_memory=False)
sp = pd.read_csv(D + 'splits.csv')
sp['split'] = sp['split'].astype(str).str.lower()
da = da.merge(sp[['account_id', 'split']], on='account_id', how='left')
RPC = {"rpc_ptp","rpc_hung_up","rpc_call_back","rpc_refused","rpc_hardship","rpc_dispute","rpc_claims_paid"}
DA = ["switched_off","not_reachable","number_does_not_exist"]
da = da.sort_values(['account_id','phone_id','attempt_ts'])
da['y'] = da.disposition.isin(RPC).astype(int)
da['tp'] = (da.disposition == 'third_party_pickup').astype(int)
g = da.groupby(['account_id','phone_id'], sort=False)
da['prev_dead'] = g['network_response'].apply(lambda s: s.isin(DA).shift().fillna(False).cumsum()).reset_index(level=[0,1], drop=True)
da['prev_n'] = g.cumcount()
da['attempt_in_account'] = da.groupby('account_id').cumcount() + 1
rows = []
def add(pol, mask, note):
    x = da[mask]
    rows.append(dict(policy=pol, calls=len(x), rpc_per_call=round(x.y.mean(),4), rpcs=int(x.y.sum()),
                     third_party_contacts=int(x.tp.sum()), note=note))
T = da.split == 'test'
add('incumbent_realised_first_3_calls_per_account', T & (da.attempt_in_account <= 3), 'what the incumbent policy actually did first, per test account')
add('incumbent_all_calls', T, 'every attempt the incumbent made in the test window')
add('rule_drop_3rd_consecutive_dead_call', T & (da.prev_dead < 3), 'deterministic waste floor: never make the 3rd+ consecutive dead call to the same point')
add('rule_first_ever_call_only', T & (da.prev_n == 0), 'only the first call to each contact point (upper bound on a cold-start policy)')
pd.DataFrame(rows).to_csv(OUT + 'derived_ps2_policy_baselines.csv', index=False)
print(open(OUT + 'derived_ps2_policy_baselines.csv').read())
print("PS2 acceptance table rebuilt ->", OUT + 'derived_ps2_policy_baselines.csv')
