#!/usr/bin/env python3
"""Every document-path reference inside PS3_SUTRA must resolve. PS3-only: a reference into the archive
(../90_Archive/...) is an error, because active documents must not cite inactive material.

    python3 tools/check_links.py
"""
import os, re, sys

SEC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAT = re.compile(r'`((?:\.\./)*[A-Za-z0-9_][A-Za-z0-9_./\-]*\.(?:md|csv|py|sh|html|txt|json|docx|png))`')
PLANNED = {  # deliverables not yet authored: allowed to dangle while the set is being written
    "PS3_WORKSPACE_MANIFEST.md", "PS3_DATA_AUDIT.md", "PS3_DATA_LINEAGE.md", "PS3_EXTERNAL_DATA_RESEARCH.md",
    "PS3_DATA_CLEANING_REPORT.md", "PS3_DATA_PREPROCESSING.md", "PS3_LEAKAGE_AND_VALIDATION.md",
    "PS3_REAL_SYSTEMS_RESEARCH.md", "PS3_RED_TEAM.md", "PS3_MASTER_ARCHITECTURE.md", "PS3_SYSTEM_DESIGN.md",
    "PS3_DATA_ARCHITECTURE.md", "PS3_MODEL_ARCHITECTURE.md", "PS3_DYNAMIC_LEARNING_ARCHITECTURE.md",
    "PS3_FIELD_EVIDENCE_ARCHITECTURE.md", "PS3_ADDRESS_MEMORY_ARCHITECTURE.md", "PS3_UNCERTAINTY_ARCHITECTURE.md",
    "PS3_API_AND_COMPONENT_DESIGN.md", "PS3_MODEL_SELECTION.md", "PS3_EXPERIMENT_PLAN.md",
    "PS3_COST_ARCHITECTURE.md", "PS3_MLOPS_ARCHITECTURE.md", "PS3_NOVELTY_AND_DIFFERENTIATION.md",
    "PS3_DECISION_LOG.md", "README.md",
}
ARCHIVED_NAMES = {"WORKSPACE.md", "CHANGELOG_OF_REFRAME.md", "divide_strict.py",
                 "fix_two_section_prose.py", "dataset_audit.py", "check_section.sh", "build_package.sh",
                 "README_PS3_SUTRA.md", "HOW_TO_USE_AND_UNDERSTAND_THIS_PACKAGE.md", "START_HERE_TEAM_HANDOFF.md"}
ROOTS = [SEC, os.path.join(SEC, "data"), os.path.join(SEC, "data", "official_ps3"),
         os.path.join(SEC, "data", "derived"), os.path.join(SEC, "data", "cleaned"), os.path.join(SEC, "tools")]
bad, n, planned, archived = [], 0, [], []
IMMUTABLE_INPUT = os.path.join(SEC, "data", "official_ps3")   # Domain A: read-only, never edited by us
# `web/node_modules` and `web/site` are a dependency tree and a build output: vendored markdown there
# is not our prose and must not be link-checked. Everything we author under web/src and web/tools is.
SKIP_DIRS = {"__pycache__", "node_modules", "site", "dist", ".vite"}
for dp, dns, fns in os.walk(SEC):
    dns[:] = [d for d in dns if d not in SKIP_DIRS]
    if os.path.abspath(dp).startswith(IMMUTABLE_INPUT):
        print(f"skipped immutable inputs at {os.path.relpath(dp, SEC)} "
              f"(Domain A's own README describes its original drop, including other problem statements)")
        continue
    for fn in fns:
        if not fn.endswith((".md", ".sh", ".py", ".html")):
            continue
        p = os.path.join(dp, fn)
        for tok in PAT.findall(open(p, encoding="utf-8", errors="ignore").read()):
            rel = re.sub(r"^\./", "", tok)
            target = os.path.normpath(os.path.join(os.path.dirname(p), rel))
            n += 1
            where = os.path.relpath(p, SEC)
            cands = [target] + [os.path.join(r, rel) for r in ROOTS]
            if not any(os.path.exists(c) for c in cands):
                if os.path.basename(rel) in PLANNED:
                    planned.append(os.path.basename(rel)); continue
                if os.path.basename(rel) in ARCHIVED_NAMES:
                    archived.append(os.path.basename(rel)); continue
                bad.append(f"{where} -> {rel}")
            if rel.startswith("../") and "90_Archive" in rel:
                bad.append(f"{where} -> {rel} (active doc cites the archive)")
            if rel.startswith("../../"):
                bad.append(f"{where} -> {rel} (escapes the section)")

print(f"checked {n} path references in OUR prose ({len(planned)} to planned deliverables, "
      f"{len(set(archived))} historical names of archived files)")
for b in bad:
    print(f"  UNRESOLVED: {b}")
print("LINKS: " + ("ALL RESOLVE" if not bad else f"{len(bad)} PROBLEM(S)"))
sys.exit(1 if bad else 0)
