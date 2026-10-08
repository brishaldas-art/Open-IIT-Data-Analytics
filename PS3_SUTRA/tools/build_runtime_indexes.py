#!/usr/bin/env python3
"""P3 — build the precomputed runtime indexes.

    python3 tools/build_runtime_indexes.py [--verify]

Writes `data/derived/runtime_indexes/` (canonical JSON + a hash manifest). Rebuilding is
deterministic; `--verify` recomputes every hash and compares it with the manifest.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sutra import config                     # noqa: E402
from sutra.indexes import RuntimeIndex, build  # noqa: E402
from sutra.store import Store                 # noqa: E402


def main() -> int:
    st = Store()
    out = build(store=st)
    ix = RuntimeIndex(out["dir"], autobuild=False)
    v = ix.verify()
    print(f"indexes  : {len(out['manifest']['files'])} files in {os.path.relpath(out['dir'], config.ROOT)}")
    for name, h in sorted(out["manifest"]["files"].items()):
        print(f"  {name:20s} {h[:16]}…")
    print(f"indexed  : {len(ix.addresses)} addresses · {len(ix.localities)} localities · "
          f"{len(ix.landmarks)} landmarks · {len(ix.place_blocks)} place-block members · "
          f"{len(ix.memory)} memory entries")
    print(f"verify   : {'OK' if v['ok'] else 'MISMATCH ' + str(v['mismatched'])}")
    return 0 if v["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
