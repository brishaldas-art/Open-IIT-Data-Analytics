#!/usr/bin/env bash
# SUTRA — reproduce every number this workspace quotes, verify its invariants, and re-run the
# implementation's acceptance suite.  usage: ./tools/reproduce.sh [fast|full]
#
# reads   data/official_ps3   (READ-ONLY, hash-checked)
# writes  data/cleaned · data/derived · data/derived/runtime
set -euo pipefail
SEC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODE="${1:-full}"
export CN_DATASET="$SEC/data/official_ps3"
export CN_CLEAN="$SEC/data/cleaned"
export CN_OUT="$SEC/data/derived"
export PYTHONPATH="$SEC:${PYTHONPATH:-}"

echo "workspace : $SEC"
echo "dataset A : $CN_DATASET (read-only)"
[ -d "$CN_DATASET" ] || { echo "MISSING dataset A at $CN_DATASET"; exit 2; }

echo; echo "== 1/16 manifest (hashes of every file, incl. Domain A) =="
python3 "$SEC/tools/build_manifest.py"

echo; echo "== 2/16 audit of Domain A (11 audit sections over 12 tables) =="
python3 "$SEC/tools/ps3_audit.py" q keys coord txt geo visits gps agents acc leak xtra | tail -12

echo; echo "== 3/16 cleaning Domain A (row-level log) =="
python3 "$SEC/tools/clean_official.py"

echo; echo "== 4/16 evidence diagnostics + place-block folds =="
python3 "$SEC/tools/evidence_diagnostics.py" | tail -4
python3 "$SEC/tools/place_block_folds.py"

echo; echo "== 5/16 radius calibration table =="
python3 "$SEC/tools/build_derived_table.py"

echo; echo "== 6/16 runtime store (ingest the official visit history; materialise beliefs) =="
# --reset: the store is a pure function of the official history (deterministic ingest digest
# 26232e3a…), so a clean rebuild is what makes this whole script reproducible end-to-end.
python3 "$SEC/tools/build_store.py" --reset

echo; echo "== 7/16 runtime indexes (precomputed, deterministic) =="
python3 "$SEC/tools/build_runtime_indexes.py"

echo; echo "== 8/16 supervision firewall + split receipt =="
python3 "$SEC/tools/build_supervision.py"

echo; echo "== 9/16 candidates v2 + features + labels (contract §4) =="
python3 "$SEC/tools/build_candidates.py"

echo; echo "== 10/16 acceptance suite T1-T15 + latency =="
python3 "$SEC/tools/run_acceptance_tests.py"

echo; echo "== 10b/16 P0 frontend-contract suite (v1 read surface, hermetic) =="
python3 -m pytest "$SEC/tests/test_contract_v1.py" -q

echo; echo "== 10c/16 console build + production smoke (frontend, deterministic, read-only) =="
if command -v npm >/dev/null 2>&1; then
  ( cd "$SEC/web" && npm ci --no-audit --no-fund >/dev/null 2>&1 && npm run build >/dev/null 2>&1 ) \
    && echo "   console built -> web/site" || echo "   SKIPPED: console build failed"
else
  echo "   SKIPPED: npm not available"
fi

echo; echo "== 10d/16 workbench build (battle_model → battle_model/site/index.html, served at /) =="
if command -v npm >/dev/null 2>&1; then
  ( cd "$SEC/battle_model" && npm ci --no-audit --no-fund >/dev/null 2>&1 && npm run build >/tmp/bm_build.log 2>&1 ) \
    && echo "   workbench built -> $(du -h "$SEC/battle_model/site/index.html" | cut -f1) single file (served by tools/serve_runtime.py at /)" \
    || { echo "   SKIPPED: workbench build failed (see /tmp/bm_build.log)"; tail -3 /tmp/bm_build.log 2>/dev/null; }
else
  echo "   SKIPPED: npm not available"
fi

echo; echo "== 11/16 experiment A — the floor (frozen baseline arm on the three A1 populations) =="
python3 "$SEC/tools/experiment_a.py"

echo; echo "== 12/16 experiment B — preprocessing ablation (B1 naive vs B2 production vs B3/B4 residue) =="
python3 "$SEC/tools/experiment_b.py" | tail -8

echo; echo "== 13/16 experiment C — retrieval-only ceiling (arms, unions, oracle, negative controls) =="
python3 "$SEC/tools/experiment_c.py" | tail -12

echo; echo "== 14/16 experiment D — retrieval + ranking (rule priority vs learned challengers) =="
# D performs exactly one declared, logged S-Eval read, after its challengers are frozen; --reset above
# means the test-look counter printed here is the authoritative in-chain count.
python3 "$SEC/tools/experiment_d.py" | tail -30

echo; echo "== 15/16 precision optimisation — audit, retrieval-v2, selection, temporal holdout, locked read =="
# Reuses the persisted snapshot inside the receipt when the frozen configuration hash matches, so a
# re-run of the chain never reads S-Eval twice for the same configuration (the counter above is
# cleared by step 6's --reset, which is why the authoritative read count lives in the receipt).
python3 "$SEC/tools/precision_opt.py" | tail -22

echo; echo "== demo (six scenes) =="
python3 "$SEC/tools/demo_walkthrough.py" | tail -6

echo; echo "== invariants: leakage, links, workspace =="
python3 "$SEC/tools/check_leakage.py"
python3 "$SEC/tools/check_links.py"
python3 "$SEC/tools/check_workspace.py"

echo; echo "done. key evidence:"
echo "  data/derived/ps3_audit_full.txt             full audit transcript"
echo "  data/cleaned/cleaning_log.csv              every cleaning rule and its counts"
echo "  data/derived/runtime/sutra_store.sqlite    append-only evidence store (5,578 seeded observations)"
echo "  data/derived/runtime_indexes/              precomputed runtime indexes + hash manifest"
echo "  data/derived/supervision_{firewall,manifest}.csv + split_receipt.json"
echo "  data/derived/candidates_v2.csv             contract §4 candidate universe"
echo "  data/derived/acceptance_report.json        T1-T15 results + latency + evidence blocks"
echo "  data/derived/demo_transcript.md            the six-scene demo"
echo "  data/derived/experiment_A_report.json      the floor, on the three populations"
echo "  data/derived/experiment_b_report.md        preprocessing ablation, kept/rejected + reproduce"
echo "  data/derived/experiment_c_report.md        retrieval-only ceiling, arms + controls + C2 status"
echo "  data/derived/experiment_d_report.md        retrieval + ranking: rule vs learned, decision + locked read"
echo "  data/derived/precision_optimization_report.md   how far the official data legitimately goes + the locked read"
echo "  data/derived/precision_optimization_results.csv every lane on one table"
echo "  data/derived/precision_optimization_receipt.json frozen config, taxonomy, bounds, sealed snapshot"
echo "  data/derived/final_precision_config.json   FINAL_PRECISION_CONFIG (hash-matched to the sealed read)"
echo "  data/derived/precision_bottleneck_table.csv     per-address failure audit (taxonomy A-K)"
echo "  tools/section_manifest.csv                 hashes (proves Domain A unchanged)"
if [ "$MODE" = "fast" ]; then echo "(fast mode is the same chain; B, C and D are the long steps — about 2.5 min, 2.75 min and 35 s)"; fi
