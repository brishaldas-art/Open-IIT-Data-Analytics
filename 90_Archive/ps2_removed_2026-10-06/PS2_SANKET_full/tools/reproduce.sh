#!/usr/bin/env bash
# Reproduce every dataset number this section quotes, and rebuild its acceptance table.
#   usage: ./tools/reproduce.sh [audit sections]     (default below)
# reads  ../data/raw   writes ../data/derived
set -euo pipefail
SEC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export CN_DATASET="${CN_DATASET:-$SEC/data/raw}"
echo "section : $(basename "$SEC")"
echo "data    : $CN_DATASET"
[ -d "$CN_DATASET" ] || { echo "MISSING data at $CN_DATASET"; exit 2; }
SECTIONS=("$@"); [ ${#SECTIONS[@]} -eq 0 ] && SECTIONS=(q p2 eco)

echo "== dataset_audit.py ${SECTIONS[*]} =="
python3 "$SEC/tools/dataset_audit.py" "${SECTIONS[@]}"
echo
echo "== acceptance table =="
python3 "$SEC/tools/build_derived_table.py"
