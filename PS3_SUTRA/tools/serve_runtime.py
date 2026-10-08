#!/usr/bin/env python3
"""Run the SUTRA service — API + console — on the standard library only, with no network egress.

    python3 tools/serve_runtime.py [--port 8000] [--host 0.0.0.0]

Port resolution order: `--port`, then `$PORT` (containers pass this), then 8000. Host defaults to
0.0.0.0 so the process is reachable from outside its container; it never binds loopback-only.

The same process serves both surfaces:

    /                 the SUTRA workbench (battle_model/site) when built, else the console build
                      (web/site), else the legacy read-only page
    /v1/*, /health,   the contract API — unchanged
    /place, /tasks…   the legacy readers — unchanged

Build the workbench:  cd battle_model && npm ci && npm run build
Rebuild the console:  cd web && npm ci && npm run build
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sutra.api import serve       # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default=os.environ.get("HOST", "0.0.0.0"))
    ap.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8000")))
    a = ap.parse_args()
    from sutra.api import _web_root
    web_root = _web_root()
    console = (os.path.relpath(os.path.join(web_root, "index.html"))
               if os.path.isfile(os.path.join(web_root, "index.html")) else "legacy page")
    print(f"SUTRA service on http://{a.host}:{a.port}  ·  frontend: {console}")
    httpd = serve(a.host, a.port)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopping")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
