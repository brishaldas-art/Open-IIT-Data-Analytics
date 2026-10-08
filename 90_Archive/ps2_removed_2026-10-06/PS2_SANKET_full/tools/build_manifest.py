#!/usr/bin/env python3
"""Manifest of the PS2_SANKET section: path, bytes, sha256, role, status."""
import os, csv, hashlib
SEC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def sha(p, n=12):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()[:n]
def role(rel):
    if rel.startswith("data/raw/"):  return "input table (read-only)"
    if rel.startswith("data/derived/"): return "acceptance table"
    if rel.startswith("tools/"):     return "tool"
    if rel.startswith("_superseded/"): return "superseded draft"
    if rel.endswith(".md"):          return "document"
    if rel.endswith(".html"):        return "demo prop"
    return "artifact"
def status(rel):
    if rel.startswith("tools/"):     return "TOOL"
    if rel.startswith("data/raw/"):  return "INPUT (synthetic, read-only)"
    if rel.startswith("data/derived/"): return "BINDING (acceptance numbers)"
    if rel.startswith("_superseded/"): return "SUPERSEDED"
    if "SOLUTION_ARCHITECTURE_FINAL" in rel or "MASTER" in rel: return "BINDING"
    if "SOLUTION_ARCHITECTURE.md" in rel: return "SUPERSEDED (hypothesis)"
    return "CURRENT"
rows = []
for dp, dns, fns in os.walk(SEC):
    dns[:] = [d for d in dns if d != "__pycache__"]
    for fn in sorted(fns):
        if fn.endswith(".pyc") or fn == "section_manifest.csv":
            continue
        p = os.path.join(dp, fn); rel = os.path.relpath(p, SEC)
        rows.append([rel, os.path.getsize(p), sha(p), role(rel), status(rel)])
out = os.path.join(SEC, "tools", "section_manifest.csv")
with open(out, "w", newline="") as f:
    w = csv.writer(f); w.writerow(["path", "bytes", "sha256_12", "role", "status"]); w.writerows(rows)
print(f"manifest: {out} ({len(rows)} files)")
