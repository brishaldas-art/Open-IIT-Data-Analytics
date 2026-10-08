# SUPERSEDED — pre-contract candidate artefacts (frozen 2026-10-07)

**Status: `SUPERSEDED_PRE_CONTRACT`. Do not train on, evaluate against, or merge anything in this directory.**

The files here were produced by `tools/build_candidates.py` **before** the implementation contracts
(`PS3_IMPLEMENTATION_CONTRACTS_2026-10-07.md`) existed. They carry three defects the contract removes:

| Defect | Evidence in these files | Contract rule that supersedes it |
|---|---|---|
| Non-contract arm names | `arm = vendor_pin`, `prior_field_cluster` | §4 — arms are exactly `frozen_baseline · locality_centroid · town_centroid · official_landmark · address_book · field_evidence · memory · place_neighbour` |
| Prohibited licence classes | `licence_class ∈ {vendor_tos, open_sharealike}` | §4 — `licence_class == "official"` always |
| No as-of semantics | no `as_of_valid` column; warm rows built from "latest visit per address" | §4 + §2 — evidence-backed arms carry `as_of_valid`; every read is as-of (`observed_at < as_of`) |

| File | Rows | Superseded by |
|---|---|---|
| `candidates_coldstart.csv` | 7,813 | `data/derived/candidates_v2.csv` (all arms, as-of labelled) |
| `candidates_warm.csv` | — | `data/derived/candidates_v2.csv` |
| `features_coldstart.csv` + receipt | — | `data/derived/features_coldstart_v2.csv` + receipt |
| `features_warm.csv` + receipt | — | `data/derived/features_warm_v2.csv` + receipt |
| `labels_eval.csv` | — | `data/derived/labels_eval_v2.csv` (evaluation-only, S-Eval) |

Nothing here was deleted: the pre-contract build stays readable as history, exactly as the leakage/decision-log
convention requires. Official raw data was never touched — `tools/section_manifest.csv` proves
`data/official_ps3/` is byte-identical.

*See `PS3_IMPLEMENTATION_CONTRACTS_2026-10-07.md` §§2, 4, 12.*
