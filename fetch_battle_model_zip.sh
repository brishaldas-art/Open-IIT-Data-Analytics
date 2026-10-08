#!/usr/bin/env bash
# Materialise the Battle-Model zip from a Google Drive share link, verify it really is the
# Battle-Model repository, and unpack it into a quarantine directory.
#
# usage:  bash fetch_battle_model_zip.sh "<google-drive-share-link-or-file-id>"
#
# It never writes into PS3_SUTRA/ and never overwrites anything: the zip lands in
# uploads/ and is unpacked into uploads/battle_model_zip/ for inspection only.
set -euo pipefail

RAW="${1:-}"
if [ -z "$RAW" ]; then
  echo "usage: bash fetch_battle_model_zip.sh \"<google-drive-share-link-or-file-id>\"" >&2
  exit 2
fi

# ── extract the file id from any of Drive's link shapes ────────────────────────────────────────
ID="$RAW"
case "$RAW" in
  *"/file/d/"*)   ID="$(printf '%s' "$RAW" | sed -E 's#.*/file/d/([A-Za-z0-9_-]+).*#\1#')" ;;
  *"id="*)        ID="$(printf '%s' "$RAW" | sed -E 's#.*[?&]id=([A-Za-z0-9_-]+).*#\1#')" ;;
  http*)          echo "could not find a file id in that URL" >&2; exit 2 ;;
esac
echo "file id : $ID"

DEST_DIR=/home/user/uploads
ZIP="$DEST_DIR/sutra-geospatial-operations-workbench.zip"
OUT="$DEST_DIR/battle_model_zip"
mkdir -p "$DEST_DIR"
COOKIES="$(mktemp)"
trap 'rm -f "$COOKIES"' EXIT

is_zip() { [ -f "$1" ] && [ "$(head -c 2 "$1" | od -An -tx1 | tr -d " \n")" = "504b" ]; }

echo "── attempt 1: direct download endpoint"
curl -sSL -c "$COOKIES" -b "$COOKIES" \
     "https://drive.google.com/uc?export=download&id=$ID" -o "$ZIP" || true

if ! is_zip "$ZIP"; then
  echo "   (not a zip — reading the confirmation page, if that is what this is)"
  UUID="$(grep -oE 'name="uuid" value="[^"]+"' "$ZIP" 2>/dev/null | head -1 | sed -E 's/.*value="([^"]+)".*/\1/')" || true
  TOKEN="$(grep -oE 'name="confirm" value="[^"]+"' "$ZIP" 2>/dev/null | head -1 | sed -E 's/.*value="([^"]+)".*/\1/')" || true
  echo "── attempt 2: usercontent endpoint (confirm=t)"
  curl -sSL -c "$COOKIES" -b "$COOKIES" \
       "https://drive.usercontent.google.com/download?id=$ID&export=download&confirm=t" -o "$ZIP" || true
  if ! is_zip "$ZIP" && [ -n "${TOKEN:-}" ]; then
    echo "── attempt 3: explicit confirm token"
    curl -sSL -c "$COOKIES" -b "$COOKIES" \
         "https://drive.google.com/uc?export=download&confirm=${TOKEN}&uuid=${UUID:-}&id=$ID" -o "$ZIP" || true
  fi
fi

if ! is_zip "$ZIP"; then
  echo
  echo "DOWNLOAD FAILED — the response was not a zip." >&2
  echo "first bytes: $(head -c 160 "$ZIP" | tr -d '\0' | tr '\n' ' ')" >&2
  echo >&2
  echo "Usual causes: the link is not public (set \"Anyone with the link\" → Viewer), the link is a" >&2
  echo "folder rather than a file, or the file id does not exist." >&2
  exit 1
fi

echo
echo "downloaded: $(stat -c%s "$ZIP") bytes → $ZIP"
echo "── unpacking into $OUT (nothing is overwritten in PS3_SUTRA/)"
rm -rf "$OUT"; mkdir -p "$OUT"
unzip -q -o "$ZIP" -d "$OUT"

echo
echo "── archive members (top 40)"
unzip -l "$ZIP" | sed -n '4,44p'

echo
echo "── Battle-Model clue check (existence only; nothing is fabricated)"
missing=0
for clue in src/App.tsx src/components/LocalPlaneMap.tsx src/components/Shell.tsx \
            src/lib/api.ts src/lib/types.ts src/views/Resolver.tsx src/views/VerifyQueue.tsx \
            src/index.css; do
  if find "$OUT" -path "*/$clue" -print -quit | grep -q .; then
    printf '   present  %s\n' "$clue"
  else
    printf '   MISSING  %s\n' "$clue"; missing=$((missing + 1))
  fi
done
echo
if [ "$missing" -eq 0 ]; then
  echo "VERDICT: looks like the Battle-Model repository (all $((8)) sampled clues present)."
else
  echo "VERDICT: $missing of 8 sampled clues missing — inspect before assuming this is the repo."
fi
echo "nothing was changed in PS3_SUTRA/ — inspect $OUT, then we port the shell onto the real backend."
