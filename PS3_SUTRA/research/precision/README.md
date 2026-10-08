# Precision optimisation — research notes

These are the **as-run** probe scripts behind the precision-optimisation pass (2026-10-07/08). They
exist so that every dead end in `data/derived/precision_optimization_report.md` can be re-derived
rather than taken on trust. They are research code, off the request path, and they write nothing:
all of them read the frozen official tables and the append-only store and print measurements.

**The reproducible record of the pass is `tools/precision_opt.py`** (frozen configuration, one locked
S-Eval read, artefacts in `data/derived/`). The scripts here are the exploration that chose what to
put in it, and several were written *before* the retrieval-v2 patch, so a few reference pre-v2
internals; they are kept as run, not maintained.

Run any of them from the repository root: `python3 research/precision/<script>.py`.

| script | question it answered | verdict |
|---|---|---|
| `audit.py` | Mandatory bottleneck audit: failure taxonomy, arm availability, pin class, pincode-demotion simulation on the 292 supervision rows. | Superseded by `precision_opt.py` §1–§3 (same taxonomy, now computed inside the frozen tool). |
| `bound.py` | **Hard ceiling**: the best any "choose an official point" method could do, per row — own pin · town-scoped locality centres · any locality centre · any POI · any other address's pin. | The information exists (absolute bound <500 m ≈ 1.00, median 38.8 m) but reaching it needs a per-address selector that only the answer supplies. Own pin 0.839; town-scoped centres 0.894; **POIs alone 0.997** — which is why the landmark arm was pursued. |
| `lm.py` | Landmark ceiling: for addresses containing a landmark mention, how far is the *nearest POI of the mentioned type* from the surveyed/proxy truth? | 32/292 rows carry a recognisable landmark mention; nearest same-type POI median 269.4 m, <250 m 0.4375, <500 m 0.7188. Per-town same-type POIs median 6 (the name is generic), so the landmark cannot be identified without the relation word — **floor for landmark-directed placement, not a solution**. |
| `loc.py` | Is the shipped locality arm picking the right locality? | No: `_locality_centroid` matched on *any single shared token* and let the pincode outvote the text — the wrong locality on 118/292 rows (median 799.5 m). Strict all-token matching gave 339.7 m. ⇒ became **retrieval-v2**. |
| `resolver.py` | Prototype IDF/rare-token locality resolvers (V0–V4) fitted on S-TRAIN, checked on S-VAL. | V3 (coverage ≥0.5 + rarest token present) chosen: S-VAL top-1 <500 m 0.8571, median 314.8 m, 6 unresolved. ⇒ the rule shipped in `sutra/candidates.py`. |
| `prod.py` | The v2 change measured inside the shipped code path (v1 vs v2 on the same pool). | Oracle <500 m 0.8801 → **0.9144** (pool), S-VAL 0.8696 → 0.8986; ranked answer unchanged. |
| `rule_study.py` | Can any selector beat the rule on the improved candidate set? rule · coarse-pin demotion · agreement-first · medoid (v1 and v2). | Rule 0.8386/0.8406 (TRAIN/VAL) and every variant equal or worse; medoid on v1 collapses to 0.7444/0.7826. |
| `rank2.py` | Can a *learned* ranker exploit the newly-correct locality candidate? LOGISTIC / LAMBDAMART / PAIRWISE, fit on S-TRAIN, judged on S-VAL + grouped OOF. | No: LOGISTIC −0.029 [−0.101, +0.044] nR; LAMBDAMART/PAIRWISE **resolved worse** (−0.246). OOF agrees. ⇒ rule priority retained. |
| `sib.py` | Sibling transfer: do other addresses' pins in the same *strict* place predict the target? | No — worse than the address's own pin. |
| `sib2.py` | Sibling transfer re-tested with the *correct* locality key (v2), including fine-street subsets and an agreement test. | Still no: town+locality+road median 329.5 m vs own pin 258 m; when pin and sibling cluster disagree (>500 m apart) the sibling is better on only 9/39 rows. **Dead end, closed.** |
| `pin.py` | Pincode-class rescue: can centroid switching rescue pincode-precision pins? | Only 5/21 rows; swapping arms fixes 6 and breaks 15 (pool 0.8390 → 0.8527, S-VAL unchanged). Superseded by the taxonomy in `precision_opt.py`. |
| `v2cand.py` | Two candidate-generation ideas: empirical locality centres built from fine pins, and their agreement with the supplied centres. | Empirical centres are *not* better (median 321.6 m vs 315.5 m supplied; better on 126/264 rows) — the supplied centroids are already good. Kept as a negative control. |
| `temporal.py`, `temporal2.py` | Temporal structure of field evidence: promoted pre/post splits, displacement of promoted check-ins across a T0 cut, GPS accuracy. | Pre→post displacement median 39–43 m, 97–99% within 500 m; `gps_accuracy_m` median 9.8 m. ⇒ the check-ins are the accurate signal and the pin is the noisy one ⇒ built the **temporal holdout** (in `precision_opt.py` §5) and the product policy. |
| `sim.py` | End-to-end protocol simulation of rule vs retrieval variants (paired grouped bootstrap on S-VAL). | Superseded by `precision_opt.py` §3/§5; kept because it is the first place the pairing mirror was exercised. |
| `trace.py` | Is a visit's GPS **track** a better location estimator than its single check-in sample? Estimators compared: check-in · last-3-fixes median · ±120 s window · accuracy-weighted · spatial medoid; judged non-circularly (pre-T0 estimator vs post-T0 labels). | **Yes, decisively**: <100 m 0.7296 → 0.8240, median 54.9 → 22.7 m. Became the production coordinate policy (`coord-v2-trace-tail`, `sutra/seed.py`) and is re-measured inside the frozen tool (§5b). |
| `lexicon.py` | Script-aware matching: 8.4% of official addresses are Kannada/Devanagari but every locality name is Latin. Induce a token→token lexicon from co-occurrence inside official addresses, then re-resolve the script-only rows. | **Rejected on the measurement** (lexicon path 257.7 m median vs 250.6 m current, better on 0/32 rows) — the pincode path already places them. Re-measured inside the frozen tool as §5c2. |
| `warm.py` | The warm→cold product measured against *future* evidence (T0 cut) instead of the circular same-visit proxy. | Warm 0.975–0.987 within 500 m, median 45–53 m; cold on the same rows 0.83. ⇒ became the S-VAL temporal holdout in the frozen tool. |
| `policies.py` | The evidence/memory policy challenger protocol (P0…P_FINAL) over the 292-row S-TRAIN+S-VAL pool, the two non-circular temporal cuts, leave-block-out and paired grouped bootstrap. The canonical copy of this protocol is imported by `tools/evidence_memory_policy.py` — one implementation, exercised by the frozen tool. | Pin-derived memory (a prior that merely re-wraps the vendor pin) counted as corroboration and outranked real check-ins; restricting emission to evidence-derived priors fixes 4 pool rows and breaks none. |

**Two traps encountered, recorded so they are not repeated.** (1) Naming a probe script after a
stdlib module shadows that module for the whole process: one probe was named after the `struct`
module and another after the `select` module, and both broke `numpy`/`sklearn` imports until they
were renamed (`ImportError: cannot import name 'pack'`; `module 'select' has no attribute
'select'`). Never give a script a stdlib name. (2) `sutra.preprocess` exposes its ring registry as
`get(ring_id)`, not `get_ring`/`RING_B2` — the `RING_B2` constant lives in `sutra/candidates.py`.
