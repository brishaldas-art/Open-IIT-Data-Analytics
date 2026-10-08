# DATA — the tables in the PS2 section

**Source:** the official CreditNirvana PS2/PS3 dataset, delivered as a Google Drive folder
(`18iqIR8TjXDqf9-hgEY34uJr_DraIl_3P`). **Everything in it is synthetic** — the dataset README says so
(`DATASET_README.md`, a copy of the original, sits next to this file). It validates *mechanism* — that a signal
exists, that a failure mode is real — never magnitude. Never quote a number from these tables as a market or
accuracy claim.

**This section is self-contained:** every table PS2 needs is here, including byte-identical copies of the three
tables PS3 also uses. Nothing is read from `../PS3_SUTRA/`.

---

## 1. What is here, and why PS2 needs it

| File | Rows | Why PS2 needs it | Owner |
|---|---|---|---|
| `dial_attempts.csv` | 51,105 | The funnel and the target: dispositions, network response, sequence, hour, attempt count, logged arm. Source of **RPC 16.4%**, the **dead-streak collapse** (0.180→0.067) and the **waste floor** (0.1762→0.1872) | PS2 only |
| `phones.csv` | 5,719 | Contact points with **provenance** — P(borrower) by source (skip_trace 1.00 … employer 0.07). ⚠ `phone_id` is **not unique** (74 repeats): join on `(account_id, phone_id)` or the merge inflates to 52,367 rows | PS2 only |
| `skip_traces.csv` | 766 | The EVSI price and the waste: **₹104 mean**, 22.8% hit rate, ₹455/hit, **77% of ₹79,650 produced nothing** | PS2 only |
| `verified_contact_points.csv` | 250 | Identity labels — ⚠ **all dated 2026-07-02, after the dial window**: evaluation only, never training features | PS2 only |
| `payments.csv` | 2,162 | The outcome side of the value model. ⚠ No campaign id → the "60% within 7 days of an RPC" is **correlation**, never uplift | PS2 only |
| `splits.csv` | 2,400 | Account-level train/val/test (1,680/360/360) — the evaluation protocol; no account appears in two splits | PS2 only |
| `agents.csv` | 30 | Agent capacity: channel, language team, tenure, shift — the scarce resource the allocator spends | PS2 only |
| `lenders.csv` | 6 | Lender registry incl. the `kyc_address_format` flag — account-side metadata | PS2 only |
| `accounts.csv` | 2,400 | The case: product, DPD band, outstanding, EMI, ticket size, PTP history, dialling arm | **copy** (also in PS3) |
| `addresses.csv` | 3,117 | Links accounts to addresses; source of the address text and the town/locality keys | **copy** (also in PS3) |
| `field_visits.csv` | 5,578 | Visit outcomes and dwell — PS2 prices a field slot with it; PS3 learns from it | **copy** (also in PS3) |

**Copies are byte-identical to the same table in `../PS3_SUTRA/data/raw/`.** Verify with
`sha256sum data/raw/accounts.csv ../PS3_SUTRA/data/raw/accounts.csv` — the check script `tools/check_section.sh`
does not tolerate drift between them: edit neither, re-derive both from the source instead.

## 2. What is deliberately **not** here

| Table | Why not |
|---|---|
| `visit_gps_points.csv` (160,406 rows), `baseline_geocodes.csv`, `surveyed_addresses.csv`, `landmarks_poi.csv`, `localities.csv`, `towns.csv` | PS3-owned location evidence. PS2 consumes their *result* — `P(truth within 200 m)` — through the contract in `../../PS3_SUTRA/SANKET_SUTRA_SYSTEM_ARCHITECTURE_FINAL.md`, never the raw rows |
| `ps1_fake_ptp/` (4 files, 4 MB: transcripts, PTPs, post-call events, a partly mislabelled sample) | Belongs to a **third problem statement** (promise-to-pay) that neither design uses. Preserved once at `90_Archive/ps1_fake_ptp_not_used/` rather than forced into a section it does not belong to |

## 3. Traps these tables carry (carried into the design, not worked around)

1. **Leakage:** adding post-dial fields lifts model AUC to 0.933 — meaningless. The feature builder bans them and a test fails the build if one appears.
2. **The arm is not clean:** 2,766 of 51,105 attempts sit on the randomised arm, 123 accounts, skewed by DPD/outstanding, propensity ≡ 1.0 → no uplift claim is licensed.
3. **`priority_slot` semantics are inverted** — documented and tested explicitly.
4. **Cash exists only in free text** (`remark` in field visits, 43/92 parseable) — treated as a flagged, lossy signal, never as a payment record.
5. **No cost, notice or campaign column exists anywhere** — every rupee figure in the EV gate is a named parameter with a range (`tools/financial_model.py`).

## 4. Reproduce the numbers from these tables

```bash
./tools/reproduce.sh          # audit sections q + p2 + eco, then rebuilds the acceptance table
./tools/reproduce.sh p2 eco   # PS2 evidence + field economics only
```
Outputs the funnel, provenance gradients, dead-streak collapse, honest AUC (0.670 vs the leakage 0.933),
skip-trace ROI, payment attribution, field economics — then rewrites
`data/derived/derived_ps2_policy_baselines.csv`.
