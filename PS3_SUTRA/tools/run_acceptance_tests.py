#!/usr/bin/env python3
"""P10/P12 gate — run the acceptance suite, benchmark the request path, and write the receipt.

    python3 tools/run_acceptance_tests.py [--quick]

Writes `data/derived/acceptance_report.json`: every T1–T15 result, the invariant results, the
resolution-latency distribution (target: p95 < 250 ms on CPU), and the evidence blocks the report
quotes (firewall counts, split counts, candidate counts by arm, store attestation, index verify).

Exit code is non-zero if any test fails: **Experiment A must not run** (the caller checks this).
"""
from __future__ import annotations

import json
import os
import re
import shutil
import sqlite3
import statistics
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sutra import asof, config                                   # noqa: E402
from sutra.indexes import get_index                              # noqa: E402
from sutra.resolve import resolve                                # noqa: E402
from sutra.store import Store                                    # noqa: E402

ROOT = config.ROOT
TEST_FILE = os.path.join(ROOT, "tests", "test_acceptance.py")


def run_pytest(quick: bool) -> tuple[int, list[dict], str]:
    args = [sys.executable, "-m", "pytest", TEST_FILE, "-v", "--tb=short", "-p", "no:cacheprovider"]
    p = subprocess.run(args, capture_output=True, text=True, cwd=ROOT)
    out = p.stdout + p.stderr
    rows = []
    for line in out.splitlines():
        m = re.match(r"^(tests/\S+::(\w+))\s+(PASSED|FAILED|SKIPPED|ERROR)", line)
        if m:
            rows.append({"node": m.group(1), "test": m.group(2), "outcome": m.group(3)})
    return p.returncode, rows, out


def benchmark(n: int = 400, warmup: int = 25) -> dict:
    """Latency of `resolve` on the full path (candidate generation + rank + belief + gate + logging)."""
    bench_store = os.path.join(tempfile.gettempdir(), "sutra_bench_store.sqlite")   # outside the workspace
    if not os.path.exists(bench_store):
        src = sqlite3.connect(config.STORE_PATH)
        dst = sqlite3.connect(bench_store)
        src.backup(dst)
        src.close()
        dst.close()
    st = Store(bench_store)
    ix = get_index()
    ids = sorted(ix.addresses)
    step = max(1, len(ids) // n)
    sample = ids[::step][:n]
    when = asof.parse_ts("2026-06-30T00:00:00Z")
    for aid in sample[:warmup]:
        resolve("", None, when, "FIELD_NAVIGATION", store=st, address_id=aid)
    times = []
    for aid in sample:
        t0 = time.perf_counter()
        resolve("", None, when, "FIELD_NAVIGATION", store=st, address_id=aid)
        times.append((time.perf_counter() - t0) * 1000.0)
    times.sort()

    def q(p):
        return round(times[min(len(times) - 1, int(round(p * (len(times) - 1))))], 3)
    return {"n": len(times), "p50_ms": q(0.5), "p95_ms": q(0.95), "p99_ms": q(0.99),
            "max_ms": round(times[-1], 3), "mean_ms": round(statistics.fmean(times), 3),
            "target_p95_ms": 250.0, "target_met": q(0.95) < 250.0,
            "note": "full request path incl. gate-decision logging, on a copy of the runtime store"}


def evidence_blocks() -> dict:
    st = Store()
    ix = get_index()
    receipt = json.load(open(os.path.join(config.DERIVED, "split_receipt.json"), encoding="utf-8"))
    pack_dir = os.path.join(config.DERIVED, "packs")
    packs = sorted(f for f in os.listdir(pack_dir)) if os.path.isdir(pack_dir) else []
    return {
        "store": st.meta(),
        "store_attestation": st.attestation(),
        "counters": {"s_eval_looks": st.counters("s_eval_looks"),
                     "gate_decisions": st.counters("gate_decisions")},
        "indexes": {"dir": os.path.relpath(config.INDEX_DIR, ROOT), **ix.verify(),
                    "n_addresses": len(ix.addresses), "n_places": len({v["block_id"] for v in ix.place_blocks.values()}),
                    "memory_entries": len(ix.memory)},
        "firewall": receipt["firewall"],
        "splits": receipt["counts"],
        "receipt_sha256": receipt["receipt_sha256"],
        "packs": packs,
    }


def main() -> int:
    t0 = time.time()
    quick = "--quick" in sys.argv
    code, rows, out = run_pytest(quick)
    passed = sum(1 for r in rows if r["outcome"] == "PASSED")
    failed = [r for r in rows if r["outcome"] in ("FAILED", "ERROR")]
    skipped = [r for r in rows if r["outcome"] == "SKIPPED"]

    bench = {} if quick else benchmark()
    report = {
        "generated_for": "PS3 implementation phase (contracts 2026-10-07)",
        "tests": rows, "n_passed": passed, "n_failed": len(failed), "n_skipped": len(skipped),
        "failed_tests": [r["test"] for r in failed],
        "all_passed": not failed,
        "latency": bench,
        "evidence": evidence_blocks(),
        "seconds": round(time.time() - t0, 1),
    }
    p = os.path.join(config.DERIVED, "acceptance_report.json")
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, sort_keys=True, ensure_ascii=False)

    print(out.strip().splitlines()[-1] if out.strip() else "")
    print(f"acceptance: {passed} passed · {len(failed)} failed · {len(skipped)} skipped")
    if bench:
        print(f"latency   : p50 {bench['p50_ms']} ms · p95 {bench['p95_ms']} ms · "
              f"p99 {bench['p99_ms']} ms (target p95 < {bench['target_p95_ms']:.0f} ms -> "
              f"{'MET' if bench['target_met'] else 'NOT MET'})")
    print(f"wrote {os.path.relpath(p, ROOT)}")
    if failed:
        print("FAILED: " + ", ".join(r["test"] for r in failed))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
