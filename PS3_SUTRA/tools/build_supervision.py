#!/usr/bin/env python3
"""P1 — build the supervision firewall, the supervision manifest and the split receipt.

    python3 tools/build_supervision.py

Writes, into `data/derived/`:
  supervision_firewall.csv   the excluded addresses (surveyed ∪ their accounts ∪ their place blocks)
  supervision_manifest.csv   every address: split, as-of, source observation ids, eligibility, reason
  split_receipt.json         counts, membership hash, declared SplitSpec registry

The 100 surveyed addresses never enter supervision or tuning. `replay.candidate_metrics` refuses to run
for any spec that is not on this receipt's registry (T15).
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sutra import config, splits                 # noqa: E402
from sutra.indexes import get_index              # noqa: E402
from sutra.store import Store                    # noqa: E402


def main() -> int:
    st = Store()
    ix = get_index()
    r = splits.build(st, ix, as_of=config.MOMENT)
    c = r["counts"]
    print(f"S-Eval          : {c['S-EVAL']} surveyed addresses (never trained, never tuned)")
    print(f"firewall        : {r['firewall']['union']} addresses = surveyed(100) + accounts"
          f"({r['firewall']['n_surveyed_accounts']}) + blocks({r['firewall']['n_surveyed_blocks']})"
          f"  = {r['firewall']['share_of_corpus']:.1%} of the corpus")
    print(f"S-Train / S-Val : {c['S-TRAIN']} / {c['S-VAL']} (nested grouped CV: outer=place block, inner=account)")
    print(f"pool (no promotion-grade confirmation yet): {c['POOL_UNSUPERVISED']}")
    print(f"receipt         : {r['receipt_sha256'][:16]}…  member hash {r['member_manifest_sha256'][:16]}…")
    for f in ("supervision_firewall.csv", "supervision_manifest.csv", "split_receipt.json"):
        p = os.path.join(config.DERIVED, f)
        print(f"  wrote {os.path.relpath(p, config.ROOT)}  ({os.path.getsize(p)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
