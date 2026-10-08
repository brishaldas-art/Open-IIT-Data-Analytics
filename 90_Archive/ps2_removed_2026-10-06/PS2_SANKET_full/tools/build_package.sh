#!/usr/bin/env bash
# Build this section's zip (self-contained: documents + its own data + tools) and refresh the
# combined zip that carries both sections. Zips land in the workspace root, one level above the
# package folder. Run from anywhere.
set -euo pipefail
SEC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PACK="$(dirname "$SEC")"                 # the folder holding both sections
WS="$(dirname "$PACK")"                  # the workspace root: zips + WORKSPACE.md live here
NAME="$(basename "$SEC")"

rm -f "$WS/${NAME}_Package.zip"
(cd "$PACK" && zip -r -q "$WS/${NAME}_Package.zip" "$NAME")     # entries start at PS?_*/...
unzip -t "$WS/${NAME}_Package.zip" >/dev/null && echo "zip OK: ${NAME}_Package.zip"
echo "  size : $(du -h "$WS/${NAME}_Package.zip" | cut -f1)"
echo "  files: $(unzip -Z1 "$WS/${NAME}_Package.zip" | grep -vc '/$')"

if [ -d "$PACK/PS2_SANKET" ] && [ -d "$PACK/PS3_SUTRA" ]; then
  cd "$WS"
  OUT="$(basename "$PACK")"
  [ -d "$WS/90_Archive" ] && OUT="$OUT 90_Archive"
  for f in WORKSPACE.md CHANGELOG_OF_REFRAME.md; do [ -f "$WS/$f" ] && OUT="$OUT $f"; done
  rm -f CreditNirvana_PS2_PS3_Deliverables.zip
  zip -r -q CreditNirvana_PS2_PS3_Deliverables.zip $OUT
  unzip -t CreditNirvana_PS2_PS3_Deliverables.zip >/dev/null && echo "zip OK: CreditNirvana_PS2_PS3_Deliverables.zip (both sections)"
  echo "  size : $(du -h CreditNirvana_PS2_PS3_Deliverables.zip | cut -f1)"
  echo "  files: $(unzip -Z1 CreditNirvana_PS2_PS3_Deliverables.zip | grep -vc '/$')"
fi
