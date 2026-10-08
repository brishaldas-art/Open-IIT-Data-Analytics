#!/usr/bin/env python3
"""Seed the runtime store from the official visit history (P5/P6). Not a training run.

    python3 tools/build_store.py [--reset]

Writes `data/derived/runtime/sutra_store.sqlite`: 5,578 ingest observations with deterministic ids
(`obs-<visit_id>`), their evidence scores, and the beliefs/tasks they imply. Re-running is a no-op
unless `--reset` is given (the store is append-only, so a reset means deleting the file and rebuilding).
"""
from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sutra import asof, config                  # noqa: E402
from sutra.belief import belief_instant, recompute_belief    # noqa: E402
from sutra.seed import seed                    # noqa: E402
from sutra.store import Store                  # noqa: E402


def materialise_beliefs(st: Store, at=config.MOMENT) -> dict:
    """Compute and store the belief of every address that carries evidence.

    Two instants per address, and both matter:
      * the **prequential instant** (`last observation + 1s`) — this is the prior the memory arm reads
        at the canonical moment. Without it the memory arm finds "the belief being computed" and
        correctly refuses to use it, which silently removes the arm from the artefacts;
      * the **canonical instant** (`config.MOMENT`) — the on-record state the report and the demo quote.

    Deterministic: the same store reproduces the same belief bytes, so this is a rebuild, not a drift.
    """
    rows = st.conn.execute("SELECT DISTINCT address_id FROM observations ORDER BY address_id").fetchall()
    n, tiers, priors = 0, {}, 0
    for (aid,) in rows:
        instant = belief_instant(st, aid, as_of=at)      # prequential instant *for this cut-point*
        if asof.parse_ts(instant) < asof.parse_ts(at):
            recompute_belief(aid, st, as_of=instant, persist=True)     # the memory arm's prior
            priors += 1
        b = recompute_belief(aid, st, as_of=at, persist=True)          # the canonical record
        tiers[b["tier"]] = tiers.get(b["tier"], 0) + 1
        n += 1
    return {"addresses": n, "tiers": tiers, "at": asof.to_utc_str(at), "with_prior": priors}


def main() -> int:
    t0 = time.time()
    if "--reset" in sys.argv and os.path.exists(config.STORE_PATH):
        gone = Store.reset(config.STORE_PATH)
        print(f"removed {os.path.relpath(config.STORE_PATH, config.ROOT)} (+ sidecars: {len(gone) - 1})")
    st = Store()
    res = seed(st, verbose=True)
    print(f"store  : {os.path.relpath(config.STORE_PATH, config.ROOT)}")
    print(f"ingest : {res}")
    mat = materialise_beliefs(st)
    print(f"beliefs: {mat['addresses']} addresses materialised at {mat['at']} -> {mat['tiers']}")
    print(f"tasks  : {st.count('task_events')} verify-first task events")
    print(f"attest : {st.attestation()['observations']}")
    print(f"seconds: {time.time() - t0:.1f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
