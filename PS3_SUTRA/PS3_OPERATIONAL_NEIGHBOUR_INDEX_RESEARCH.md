# SUTRA — OPERATIONAL PLACE-NEIGHBOUR INDEX — RESEARCH & VERDICT

**Question.** Meesho's GeoIndia-V2 line of work shows that **operational delivery traces create geographic structure**:
places connect through real operational behaviour, and that structure improves disambiguation [S80][S79]. Can PS3 get
the same benefit from **only the supplied official data** — without a graph database, without a GNN, and without
assuming the answer?

**Verdict (short).** **Experiment-gated, default OFF.** The index is cheap to build and *does* raise the retrieval
ceiling — but a placebo control shows most of that gain is candidate *density*, not place knowledge; used naively (pick
the nearest confirmed place) it is **worse** than the existing arms. It enters the candidate set only if experiment C2
shows the **ranked** pipeline beats official-arms-only beyond the interval on three populations.

---

## 1. The mechanism, as studied externally (no data imported)

| System | What it does with operational traces | What transfers to us |
|---|---|---|
| GeoIndia V2 (CIKM 2025) [S80] | Builds a **graph of neighbourhood connectivity from last-mile delivery data**; fuses it with a language model (Graphormer + PTLM + KMCA); decodes hierarchical H3 cells | The *idea*: confirmed operational locations are anchors for unconfirmed ones. **Not copied:** Graphormer/GNN compute, proprietary delivery graph, generative decoding |
| SCOUTCG / GeoIndia V3 (SIGSPATIAL 2026) [S80] | Mines **billions of GPS signals** into stable spatial structure via graph community detection | Confirms the pattern at a scale we will never have; our version must work with **900 confirmed places**, not billions |
| Delhivery Address Verification [S77] | Commercial product answers "**has this address been visited within a window**" from 4B+ deliveries | The commercial proof that visit history *is* address intelligence; their scale is not reproducible |
| ODK/KoboToolbox [S81] | Not geocoding — but proves the ordering rules required for the index's freshness (hold-then-apply, cursors) | The index must be **as-of queryable**, or it becomes leakage |

## 2. Definition for PS3 (lightweight, deterministic, official data only)

```
NEW ADDRESS ─► text/locality retrieval ─► historical place neighbours ─► verified place coordinates
             (official anchors)           (index lookup)                 become candidate anchors
                                                                        └─► transparent ranking (S5)
```

**Nodes.** Confirmed places = addresses with ≥1 integrity-passing met-someone visit; place coordinate = mean of their
met check-ins (900 places exist today `[S94]`). Place identity follows the M1 rules (co-location ≤30 m = one place);
**never keyed by account**.

**Edges / retrieval rules (all deterministic, all official):**

| Rule | Source | Prepared for |
|---|---|---|
| Same locality membership | `localities`, parsed locality token | retrieval key |
| Spatial proximity | confirmed check-ins | candidate expansion radius (1 km) |
| Same place cluster (≤30 m) | M1 clusters (81 clusters / 191 addresses) | identity, not expansion |
| Text similarity (identity/render keys, token-set Jaccard, char-3-gram) | `addresses` text | **ranking feature**, never a merge |
| Visit sequence (temporally valid pairs only) | `field_visits` | optional edge, as-of enforced |

**Storage.** One inverted index `locality → [confirmed_place_ids + coordinates + last_confirmed_at + integrity_weight]`.
No graph database, no message passing, no training. Build time measured: seconds at this scale.

**As-of discipline.** Every neighbour carries `last_confirmed_at`; a lookup at time *t* may only see neighbours
confirmed before *t*. Without this, the index is a leakage machine (the same rule the audit already applies to memory).

## 3. The feasibility probe (official data only; oracle-style, evaluation-only)

`tools/neighbour_index_probe.py` → `data/derived/derived_place_neighbour_probe.csv` `[S96]`. For each of the **100
surveyed addresses**: official cold candidate set vs the same set **plus** confirmed places within 1 km of the locality
anchor. Nothing is fitted; this measures *capacity*, not achieved accuracy.

| Variant | Median error to truth | ≤ 100 m | Notes |
|---|---|---|---|
| Official candidate arms alone (oracle) | **306.2 m** | **11.0%** | replicates the audit's frozen ceiling `[S94]` |
| + place-neighbour index (oracle) | **72.2 m** | **65.0%** | 85/100 addresses improve; coverage 100% (median **70** neighbours within 1 km) |
| + index, **leave-block-out** | 72.2 m | 65.0% | only 4 addresses had same-place neighbours removed (6 neighbours) → gains come from **other** places |
| **Placebo: random points, same count (median of 20 draws)** | **93.6 m** | **55.0%** | **the decisive control** |
| Naive nearest confirmed place (no ranker) | **397.2 m** | 5.0% | worse than the vendor pin (376.4 m) |

**Reading it honestly.** Adding ~70 candidate points anywhere near the anchor already moves the oracle from 306 m to
~94 m (placebo). Real confirmed places add a further, **real but modest** improvement (72.2 vs 93.6 m median; 65.0% vs
55.0% ≤100 m). And selecting naively is worse than not using the index at all. Conclusion: **the dataset has abundant
candidate mass; the bottleneck is *selection*, not anchor supply** — consistent with the audit's finding that ranking
the official arms alone is worth ~19% relative and memory is the bigger lever.

## 4. Verdict and admission test

**Status: experiment-gated (C2), default OFF.** The index is built once (seconds), shadowed in C2, and admitted to S4
only if **all** hold:

1. The **ranked** pipeline (not the oracle) beats official-arms-only beyond the grouped-bootstrap interval on the three
   populations (Amendment A1);
2. It beats the **placebo arm** (same candidate count, random points) — otherwise it is density, not knowledge, and is
   dropped;
3. No regression in coverage, refusal quality, stratum behaviour or cost shape (D21);
4. As-of lookup passes the leakage guard (no neighbour confirmed after the query time).

**If it fails:** delete `tools/neighbour_index_probe.py`'s index from the pipeline, keep the probe as the recorded
negative result, and say so in the report. (Precedent: the design already rejected landmark-snapping on evidence.)

**What SUTRA must not copy:** Graphormer/GNN stacks, generative H3 decoding, proprietary delivery graphs, or any claim
built on someone else's trace data `[S80]`. Our index is a **lookup table with coordinates and timestamps** — and it
earns its place by experiment or not at all.

**What this changes in the real workflow (if admitted):** a new address in a locality where collectors have already
confirmed nearby places arrives with those places as explicit, inspectable candidates — "two confirmed places within
150 m, both met last month" — instead of a bare locality centroid.
