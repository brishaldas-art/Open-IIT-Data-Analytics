#!/usr/bin/env python3
"""
SUTRA — workspace invariants (PS3-only). Prints PASS/FAIL; non-zero exit on any failure.

Enforces the commission's hard boundaries: PS3 only, no PS2 anywhere, two data domains kept apart,
no premature training, every claim reproducible, licences recorded, links resolving.

    python3 tools/check_workspace.py
"""
import os, re, sys, glob, hashlib, subprocess

HERE = os.path.dirname(os.path.abspath(__file__)); SEC = os.path.dirname(HERE)
WS = os.path.dirname(SEC)
FAIL, FB = 0, []


def chk(name, ok, why=""):
    global FAIL
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"   [{why}]" if why and not ok else ""))
    if not ok:
        FAIL = 1; FB.append(name)


def has(pattern, paths="*.md", flags=re.I):
    """Search OUR authored documents only. data/official_ps3/ is immutable input: its own README
    describes the original drop (including a different problem statement), and the manifest proves
    we never edited it — so it is excluded from every prose rule."""
    out = []
    rx = re.compile(pattern, flags)
    for p in glob.glob(f"{SEC}/{paths}"):
        if p.startswith(os.path.join(SEC, "data")):
            continue
        if rx.search(open(p, encoding="utf-8", errors="ignore").read()):
            out.append(p)
    return out or None


# ── 1. PS3 only ─────────────────────────────────────────────────────────────────
ps2_files = [f for f in glob.glob(f"{SEC}/**/*", recursive=True)
             if re.search(r"PS2|SANKET", os.path.basename(f))]
chk("no PS2-named file in the active workspace", not ps2_files, f"{ps2_files[:3]}")
# The workspace manifest is required to record exactly what was removed, so it is the one document
# allowed to name the retired project. Every other document must be free of the reference.
MANIFEST_EXEMPT = "PS3_WORKSPACE_MANIFEST.md"
leftovers = [p for p in has(r"\bPS2\b|\bSANKET\b") or [] if not p.endswith(MANIFEST_EXEMPT)]
chk("no reference to the retired project outside the workspace manifest", not leftovers,
    f"{[os.path.basename(p) for p in leftovers]}")
chk("no unrelated-project artefacts (venue/audience keyword guard)",
    not has(r"\bqloo\b|\bcinema\b|\bticketing\b|\bbox office\b"))
chk("no reference to the retired shared bucket or numbered folders",
    not has(r"SHARED/|0[0-9]_Master|0[0-9]_(Phase|Architecture|Evidence|Model|Dataset)\b"))

# ── 2. the required document set ────────────────────────────────────────────────
REQ = ["PS3_FINAL_REPORT.md", "PS3_MASTER_ARCHITECTURE.md", "PS3_SYSTEM_DESIGN.md", "PS3_DATA_ARCHITECTURE.md",
       "PS3_MODEL_ARCHITECTURE.md", "PS3_DYNAMIC_LEARNING_ARCHITECTURE.md",
       "PS3_FIELD_EVIDENCE_ARCHITECTURE.md", "PS3_ADDRESS_MEMORY_ARCHITECTURE.md",
       "PS3_UNCERTAINTY_ARCHITECTURE.md", "PS3_DATA_CLEANING_REPORT.md", "PS3_DATA_PREPROCESSING.md",
       "PS3_FINAL_DATA_AND_ARCHITECTURE_FREEZE.md",
       "PS3_REAL_SYSTEMS_RESEARCH.md", "PS3_RED_TEAM.md",
       "PS3_COST_ARCHITECTURE.md", "PS3_LEAKAGE_AND_VALIDATION.md", "PS3_MLOPS_ARCHITECTURE.md",
       "PS3_API_AND_COMPONENT_DESIGN.md", "PS3_EXPERIMENT_PLAN.md", "PS3_MODEL_SELECTION.md",
       "PS3_DECISION_LOG.md", "PS3_NOVELTY_AND_DIFFERENTIATION.md", "PS3_WORKSPACE_MANIFEST.md",
       "PS3_DATA_AUDIT.md", "PS3_CANONICAL_SCHEMA.md", "PS3_DATA_LINEAGE.md", "PS3_SOURCE_REGISTER.md",
       "PS3_DATA_EDA_AND_PREPROCESSING.md", "PS3_BUSINESS_AND_OPERATIONAL_RETHINK.md",
       "PS3_ARCHITECTURE_REQUIREMENTS_RECONCILED.md", "PS3_OPERATIONAL_NEIGHBOUR_INDEX_RESEARCH.md",
       "PS3_PURPOSE_AND_DIRECTION_MODULES.md", "PS3_ARCHITECTURE_DUE_DILIGENCE_2026-10-07.md",
       "PS3_ARCHITECTURE_LOCK_CANDIDATE_2026-10-07.md", "PS3_IMPLEMENTATION_CONTRACTS_2026-10-07.md", "PS3_IMPLEMENTATION_PHASE_REPORT_2026-10-07.md",
       "README.md"]
missing = [f for f in REQ if not os.path.exists(f"{SEC}/{f}")]
chk(f"all {len(REQ)} required documents present", not missing, f"missing {missing}")

# ── 3. structure ────────────────────────────────────────────────────────────────
for d, why in [("data/official_ps3", "Domain A"), ("data/cleaned", "cleaned tables"),
               ("data/derived", "derived artefacts"), ("tools", "tooling")]:
    chk(f"directory present: {d} ({why})", os.path.isdir(f"{SEC}/{d}"))

# ── 4. Domain A read-only and complete ──────────────────────────────────────────
A = sorted(os.path.basename(p) for p in glob.glob(f"{SEC}/data/official_ps3/*.csv"))
# 2026-10-07: the assigned shared table `lenders` joined the frozen tree in the official-scope re-audit
chk("official dataset has its 12 tables (6 task-specific + 6 assigned shared)", len(A) == 12, f"found {len(A)}: {A}")

# ── 5. no premature training ────────────────────────────────────────────────────
modelish = [p for p in glob.glob(f"{SEC}/**/*", recursive=True)
            if re.search(r"\.(pkl|joblib|model|pt|onnx|h5|cbm|txt\.model)$|/models?/", p)]
chk("no trained model artefact in the workspace (Experiment D fits in memory and ships nothing)",
    not modelish,
    f"{modelish[:3]}")
chk("no free-standing training script (challengers live in sutra/learning.py, gated by tools/experiment_d.py)",
    not glob.glob(f"{SEC}/tools/train*.py"),
    "a training entry point exists; experiments must be designed first")

# ── 6. leakage guard passes ─────────────────────────────────────────────────────
r = subprocess.run([sys.executable, f"{HERE}/check_leakage.py"], capture_output=True, text=True)
chk("leakage guard passes", r.returncode == 0, r.stdout.strip().splitlines()[-1] if r.stdout else "")

# ── 7. audit reproduces a known number ──────────────────────────────────────────
log = f"{SEC}/data/derived/ps3_audit_full.txt"
chk("audit log exists", os.path.exists(log))
if os.path.exists(log):
    t = open(log).read()
    chk("audit reproduces the surveyed baseline (median 376 m)", "376.4" in t or "376" in t)
    chk("audit reproduces the integrity finding (FA009 duplicate photos)",
        "FA009" in t and "156" in t)

# ── 8. licences recorded for everything external ────────────────────────────────
# 2026-10-07 FINAL DATA POLICY: no external/scraped/third-party geographic data may exist anywhere
# in the active tree. This guard is absolute — it is not a licence check, it is a prohibition.
DATA_EXT = (".csv", ".tsv", ".json", ".geojson", ".parquet", ".sqlite", ".gpkg", ".shp", ".pbf", ".zip", ".xlsx")
OFFICIAL_AREAS = (os.path.join(SEC, "data", "official_ps3"), os.path.join(SEC, "data", "cleaned"),
                  os.path.join(SEC, "data", "derived"))
stray = []
for root, _, files in os.walk(os.path.join(SEC, "data")):
    for f in files:
        fp = os.path.join(root, f)
        if f.lower().endswith(DATA_EXT) and not fp.startswith(OFFICIAL_AREAS):
            stray.append(os.path.relpath(fp, SEC))
ext = glob.glob(f"{SEC}/data/external_research/*")
chk("no dataset outside official/cleaned/derived (final data policy: official data only)",
    not stray, f"{stray[:4]}")
chk("external-data holding area is empty (no external dataset anywhere in the active tree)",
    not ext, f"{ext[:4]}")
reg = open(f"{SEC}/PS3_SOURCE_REGISTER.md", encoding="utf-8").read() if os.path.exists(
    f"{SEC}/PS3_SOURCE_REGISTER.md") else ""
chk("source register has >= 40 entries", len(re.findall(r"^\| S\d+", reg, re.M)) >= 40,
    f"{len(re.findall(r'^\| S\d+', reg, re.M))} entries")

# ── 9. cross-references ─────────────────────────────────────────────────────────
docs = glob.glob(f"{SEC}/*.md")
nocite = [os.path.basename(d) for d in docs
          if os.path.basename(d) not in ("README.md", "PS3_WORKSPACE_MANIFEST.md")
          and not re.search(r"\[S\d+", open(d, encoding="utf-8").read())]
chk("every document cites at least one register source", not nocite, f"{nocite}")

# ── 10. links resolve ───────────────────────────────────────────────────────────
r = subprocess.run([sys.executable, f"{HERE}/check_links.py"], capture_output=True, text=True)
chk("document links resolve", r.returncode == 0, r.stdout.strip()[-160:])

print(f"\nWORKSPACE: {'ALL CHECKS PASSED' if not FAIL else 'FAILED -> ' + ', '.join(FB)}")
sys.exit(FAIL)
