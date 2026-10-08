#!/usr/bin/env bash
# Browser deps for the smoke runs, in one command. Idempotent: safe to re-run every session.
#
# The sandbox runs as uid 1000 on trixie, so `apt-get install` cannot write the system directories.
# We download the packages and unpack them under /var/tmp/root, then point the loader at them:
#
#   bash web/tools/install_browser_deps.sh
#   LD_LIBRARY_PATH=/var/tmp/root/usr/lib/x86_64-linux-gnu:/var/tmp/root/usr/lib/x86_64-linux-gnu/nss \
#     PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS=1 \
#     node battle_model/tools/browser_smoke.mjs http://127.0.0.1:8001 ../screenshots
set -euo pipefail
ROOT=/var/tmp/root
DEB=/var/tmp/deb
LIBS=(libxdamage1 libasound2t64 libatk1.0-0t64 libatk-bridge2.0-0t64 libatspi2.0-0t64
      libcups2t64 libnspr4 libnss3 libxkbcommon0)

mkdir -p "$DEB" "$ROOT"
if [ "$(ls -1 "$DEB"/*.deb 2>/dev/null | wc -l)" -lt 10 ]; then
  ( cd "$DEB" && apt-get download $(apt-cache depends --recurse --no-recommends --no-suggests \
      --no-conflicts --no-breaks --no-replaces --no-enhances "${LIBS[@]}" 2>/dev/null \
      | grep '^[a-z]' | sort -u) )
fi
for f in "$DEB"/*.deb; do dpkg-deb -x "$f" "$ROOT" 2>/dev/null || true; done

cd "$(dirname "$0")/.."                 # web/
[ -d node_modules/playwright ] || npm ci --no-audit --no-fund
PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS=1 npx playwright install chromium >/dev/null 2>&1 || true

CHROME=$(ls -d "$HOME"/.cache/ms-playwright/chromium-*/chrome-linux/chrome 2>/dev/null | head -1)
echo "libs: $(ls -1 "$DEB"/*.deb | wc -l) packages unpacked into $ROOT"
echo "chromium: ${CHROME:-MISSING}"
LD_LIBRARY_PATH="$ROOT/usr/lib/x86_64-linux-gnu:$ROOT/usr/lib/x86_64-linux-gnu/nss" \
  ldd "$CHROME" 2>/dev/null | grep 'not found' && echo "!! still missing libs above" || echo "all chromium libs resolve"
