#!/usr/bin/env python3
"""Manifest of the PS3_SUTRA workspace: path, bytes, sha256[:12], role, status, domain.
Writes tools/section_manifest.csv (the same file the leakage guard uses to prove Domain A is unchanged).

    python3 tools/build_manifest.py
"""
import os, csv, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
SEC = os.path.dirname(HERE)
# Vendored dependencies and build output are not workspace artefacts: `web/node_modules` and
# `web/site` are excluded, while everything we author under web/ (src, tools, config, lockfile) is
# manifest-covered like any other source file.
SKIP = {"__pycache__", ".ipynb_checkpoints", "node_modules", "site", "dist"}


def sha(p, n=12):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()[:n]


def describe(rel):
    if rel.startswith("data/official_ps3/") and rel.endswith(".csv"):
        return "input table — DATASET A, official benchmark", "INPUT (synthetic, READ-ONLY)", "A"
    if rel.startswith("data/official_ps3/"):
        return "dataset documentation (the dataset's own words)", "INPUT (read-only)", "A"
    if rel.startswith("data/external_research/"):
        return "augmentation data — DATASET B", "EXTERNAL (licence-tagged)", "B"
    if rel.startswith("data/cleaned/"):
        return "cleaned/derived table produced from Domain A", "DERIVED (logged transformation)", "A"
    if rel.startswith("data/derived/"):
        return "derived artefact (profile, candidates, features, calibration)", "DERIVED (reproducible)", "A"
    if rel.startswith("tools/"):
        return "tool", "TOOL", "—"
    if rel.startswith("web/"):
        return "frontend source (React + TypeScript console)", "CURRENT", "—"
    if rel == "Dockerfile" or rel.startswith(".docker") or rel.startswith("DEPLOYMENT"):
        return "deployment configuration", "CURRENT", "—"
    if rel.endswith(".md"):
        if rel.startswith("PS3_"):
            return "document", "CURRENT", "—"
        return "document (front door / handoff)", "CURRENT", "—"
    if rel.endswith(".json"):
        return "leakage receipt / config", "RECEIPT", "—"
    return "artefact", "CURRENT", "—"


def status_override(rel):
    if rel in ("PS3_SOURCE_REGISTER.md", "PS3_CANONICAL_SCHEMA.md"):
        return "CURRENT (method contract)"
    if rel.startswith("PS3_") and rel.endswith(".md"):
        return "CURRENT"
    return None


rows = []
for dp, dns, fns in os.walk(SEC):
    dns[:] = [d for d in dns if d not in SKIP]
    for fn in sorted(fns):
        if fn.endswith(".pyc") or fn == "section_manifest.csv":
            continue
        p = os.path.join(dp, fn)
        rel = os.path.relpath(p, SEC).replace(os.sep, "/")
        role, status, dom = describe(rel)
        status = status_override(rel) or status
        try:
            size = os.path.getsize(p)
        except OSError:
            continue
        rows.append(dict(path=rel, bytes=size, sha256_12=sha(p), role=role, status=status, domain=dom))

rows.sort(key=lambda r: r["path"])
out = os.path.join(HERE, "section_manifest.csv")
with open(out, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["path", "bytes", "sha256_12", "role", "status", "domain"])
    w.writeheader()
    w.writerows(rows)

by = {}
for r in rows:
    by[r["domain"]] = by.get(r["domain"], 0) + 1
print(f"manifest: {len(rows)} files, {sum(r['bytes'] for r in rows)/1e6:.2f} MB")
print("  " + " · ".join(f"{k}:{v}" for k, v in sorted(by.items())))
print(f"  written to {os.path.relpath(out, SEC)}")
