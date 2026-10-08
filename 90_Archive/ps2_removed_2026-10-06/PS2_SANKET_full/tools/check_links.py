#!/usr/bin/env python3
"""Every document-path reference in this section must resolve.

  * a reference that points INSIDE the section must resolve, or the check FAILS;
  * a reference that crosses the section boundary (starts with ../ — the sibling section or the
    workspace root) is verified when that target is on disk and otherwise reported as
    unverified-but-not-an-error, so this file is equally valid in a single-section zip.
"""
import os, re, sys
SEC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WS = os.path.dirname(SEC)
OTHER = "PS3_SUTRA" if os.path.basename(SEC) == "PS2_SANKET" else "PS2_SANKET"
SIB = os.path.isdir(os.path.join(WS, OTHER))
PAT = re.compile(r'`((?:\.\./)*[A-Za-z0-9_][A-Za-z0-9_./\-]*\.(?:md|csv|py|sh|html|txt|docx))`')
bad, outside = [], []
n_in = n_out = 0
for dp, dns, fns in os.walk(SEC):
    dns[:] = [d for d in dns if d not in ("__pycache__", "_superseded")]
    for fn in fns:
        if not fn.endswith((".md", ".sh", ".py", ".html")):
            continue
        p = os.path.join(dp, fn)
        for tok in PAT.findall(open(p, encoding="utf-8", errors="ignore").read()):
            if "/" not in tok:
                continue
            rel = re.sub(r'^\./', '', tok)
            target = os.path.join(os.path.dirname(p), rel)
            where = os.path.relpath(p, SEC)
            if rel.startswith("../"):                      # crosses the section boundary
                n_out += 1
                if not os.path.exists(target):
                    outside.append(f"{where} -> {tok}")
            elif os.path.exists(target) or os.path.exists(os.path.join(SEC, rel)):
                n_in += 1
            else:
                n_in += 1
                bad.append(f"{where} -> {tok}")
for b in bad:
    print("  BROKEN:", b)
print(f"{os.path.basename(SEC)}: {n_in} links inside the section ({len(bad)} broken) · "
      f"{n_out} cross-section/root links ({len(outside)} unresolved "
      f"{'— expected in a single-section extraction' if not SIB else '— target present, check these'})")
if outside and SIB:
    for o in outside:
        print("  check:", o)
sys.exit(1 if bad else 0)
