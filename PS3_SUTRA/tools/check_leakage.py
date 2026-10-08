#!/usr/bin/env python3
"""SUTRA — leakage guard, rewritten for the implementation contract (2026-10-07).

Fails the build if a feature artefact could see the future, if a pre-contract artefact is still being
produced, or if a truth label has leaked into anything that is not the evaluation file.

Checks (each prints PASS/FAIL and the reason):
  1. candidate artefacts exist and obey §4: contract arms only, `licence_class == "official"`,
     `as_of_valid` present **iff** the arm is evidence-backed, no truth column, no pre-contract vocabulary
  2. every feature artefact has a receipt stating what it is
  3. no feature column carries a forbidden prefix, and (T13) no shared-table column is a feature
  4. the cold-start matrix contains no evidence-backed arm; the warm matrix labels its evidence arms
  5. truth lives only in `labels_eval_v2.csv`, which is S-Eval-only and evaluation-only
  6. the superseded (pre-contract) directory is history: no active module reads it
  7. the official dataset is unmodified (hash check against the manifest)

    python3 tools/check_leakage.py
"""
import csv
import glob
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SEC = os.path.dirname(HERE)
OUT = os.path.join(SEC, "data", "derived")
SUPERSEDED = os.path.join(OUT, "superseded_pre_contract_2026-10-07")
ARMS = ("frozen_baseline", "locality_centroid", "town_centroid", "official_landmark", "address_book",
        "field_evidence", "memory", "place_neighbour")
EVIDENCE_ARMS = ("field_evidence", "memory", "place_neighbour")
FORBIDDEN = ("checkin", "gps_", "dwell", "outcome", "photo", "remark", "trail", "surveyed", "label_",
             "err_m", "truth")
SHARED = ("account_id", "agent_id", "split", "lender", "tenure", "shift", "exposure")
BANNED_VOCAB = ("vendor_tos", "open_sharealike", "prior_field_cluster")
FB, FAIL = [], 0


def chk(name, ok, why=""):
    global FAIL
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"   [{why}]" if why and not ok else ""))
    if not ok:
        FAIL = 1
        FB.append(name)


def rows_of(path):
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


# ── 1. candidate artefacts ──────────────────────────────────────────────────────────────────────
cand_path = os.path.join(OUT, "candidates_v2.csv")
chk("candidate artefact exists (contract §4 builder)", os.path.exists(cand_path), "run tools/build_candidates.py")
if os.path.exists(cand_path):
    C = rows_of(cand_path)
    cols = set(C[0]) if C else set()
    arms = {r["arm"] for r in C}
    chk("candidates: contract arms only", arms <= set(ARMS), f"saw {sorted(arms - set(ARMS))}")
    chk("candidates: place_neighbour stays disabled until C2", "place_neighbour" not in arms)
    # a silent-regression check: the memory arm must fire wherever a prior belief exists, or the warm
    # lane is quietly weaker than the report claims (this happened once: beliefs were materialised
    # only *at* the cut-point, so no belief was ever strictly "before" it)
    mem_idx = os.path.join(OUT, "runtime_indexes", "memory.json")
    mem_n = len(json.load(open(mem_idx, encoding="utf-8"))) if os.path.exists(mem_idx) else 0
    chk("candidates: the memory arm fires where a prior belief exists",
        mem_n == 0 or "memory" in arms, f"memory index has {mem_n} entries but no memory candidate")
    chk("candidates: licence_class is official everywhere", {r["licence_class"] for r in C} == {"official"},
        f"saw {sorted({r['licence_class'] for r in C})}")
    bad_asof = [r["candidate_id"] for r in C
                if (r["arm"] in EVIDENCE_ARMS) != bool(r["as_of_valid"])]
    chk("candidates: as_of_valid present iff evidence-backed", not bad_asof, f"{bad_asof[:3]}")
    chk("candidates: no truth column", not (cols & {"err_m", "truth", "surveyed_x", "surveyed_y", "label"}))
    blob = open(cand_path, encoding="utf-8").read()
    leftover = [b for b in BANNED_VOCAB if b in blob]
    chk("candidates: no pre-contract vocabulary", not leftover, f"saw {leftover}")

# ── 2/3/4. feature artefacts ────────────────────────────────────────────────────────────────────
feats = sorted(glob.glob(os.path.join(OUT, "features_*.csv")))
chk("a feature artefact exists", len(feats) > 0, "run tools/build_candidates.py")
for f in feats:
    base = os.path.basename(f)
    rec_path = f.replace(".csv", ".receipt.json")
    chk(f"{base}: has a leakage receipt", os.path.exists(rec_path), "missing receipt")
    if not os.path.exists(rec_path):
        continue
    rec = json.load(open(rec_path, encoding="utf-8"))
    cols = list(rows_of(f)[0]) if os.path.getsize(f) else []
    bad = [c for c in cols if any(t in c.lower() for t in FORBIDDEN)]
    chk(f"{base}: no forbidden feature column", not bad, f"saw {bad}")
    shared_hits = [c for c in cols if any(t in c.lower() for t in SHARED)]
    chk(f"{base}: no shared-table column is a feature (T13)", not shared_hits, f"saw {shared_hits}")
    chk(f"{base}: receipt states what it is", bool(rec.get("statement")), "receipt lacks a statement")
    chk(f"{base}: receipt records the arm set", set(rec.get("arms", [])) <= set(ARMS), f"{rec.get('arms')}")
    chk(f"{base}: receipt declares no external data", rec.get("external_data") is False)
    if "coldstart" in base:
        chk("coldstart: no evidence-backed arm", not (set(rec.get("arms", [])) & set(EVIDENCE_ARMS)),
            f"arms={rec.get('arms')}")
        chk("coldstart: every as_of_valid is empty", all(not r["as_of_valid"] for r in rows_of(f)))
        chk("coldstart: receipt says cold start", "cold" in rec.get("statement", "").lower())
    if "warm" in base:
        chk("warm: labelled as warm", "warm" in rec.get("statement", "").lower())
        W = rows_of(f)
        ev = [r for r in W if r["arm"] in EVIDENCE_ARMS]
        chk("warm: evidence arms carry as_of_valid", bool(ev) and all(r["as_of_valid"] for r in ev))

# ── 5. labels are evaluation-only ───────────────────────────────────────────────────────────────
label_path = os.path.join(OUT, "labels_eval_v2.csv")
chk("labels live in their own file", os.path.exists(label_path))
if os.path.exists(label_path):
    L = rows_of(label_path)
    chk("labels: evaluation-only (err_m present, no feature use)", rows_of(label_path) and "err_m" in L[0])
    chk("labels: S-Eval only", {r["split"] for r in L} == {"S-EVAL"}, f"{ {r['split'] for r in L} }")
    chk("labels: surveyed truth named as the source",
        {r["label_source"] for r in L} == {"surveyed_ground_truth"})
    LABEL_ONLY = {"err_m", "label_within_100m", "label_within_250m", "is_best_of_set", "label_source",
                  "split", "label_within_500m"}
    for f in feats:
        cols = list(rows_of(f)[0])
        leaked = sorted(set(cols) & LABEL_ONLY)
        chk(f"{os.path.basename(f)}: no label column", not leaked, f"leaked {leaked}")

# ── 6. the superseded directory is only history ─────────────────────────────────────────────────
# Experiment C's ceiling claim: the candidate path never reads the surveyed truth table, so no candidate
# can be the evaluation truth in disguise. Proven at runtime inside `tools/experiment_c.py` (0 reads while
# generating all 3,117 addresses); this is the standing guard that keeps it true between experiments.
_CAND_PATH = ["sutra/candidates.py", "sutra/indexes.py", "sutra/ranking.py", "sutra/geo.py",
              "sutra/evidence.py", "sutra/belief.py", "sutra/memory.py", "sutra/learning.py"]
_reads = {}
for _f in _CAND_PATH:
    _p = os.path.join(SEC, _f)
    if os.path.exists(_p):
        _reads[_f] = open(_p, encoding="utf-8").read().count("dataio.surveyed(")
chk("the candidate path never reads the surveyed truth table (C)",
    sum(_reads.values()) == 0, f"reads: { {k: v for k, v in _reads.items() if v} }")

# Experiment D's standing guard: the learned rankers are research. The production request path must stay
# exactly the frozen rule ranker — no request-path module may import the challengers, and the challenger
# library must not be reachable from the API surface.
_REQ_PATH = ["sutra/api.py", "sutra/resolve.py", "sutra/ranking.py", "sutra/candidates.py",
             "sutra/eligibility.py", "sutra/purpose.py", "sutra/directions.py", "sutra/memory.py",
             "sutra/belief.py"]
_importers = {}
for _f in _REQ_PATH:
    _p = os.path.join(SEC, _f)
    if os.path.exists(_p):
        _src = open(_p, encoding="utf-8").read()
        if "import learning" in _src or "from .learning" in _src or "sutra.learning" in _src:
            _importers[_f] = True
chk("no request-path module imports the learned-ranking challengers (D)", not _importers, f"{_importers}")
chk("the challenger library stays out of the shipped API surface (D)",
    "learning" not in open(os.path.join(SEC, "sutra/api.py"), encoding="utf-8").read()
    and "learning" not in open(os.path.join(SEC, "sutra/resolve.py"), encoding="utf-8").read())

chk("superseded (pre-contract) artefacts are kept for the record", os.path.isdir(SUPERSEDED))
SELF = os.path.abspath(__file__)
code = ""
for d in (os.path.join(SEC, "sutra"), os.path.join(SEC, "tools")):
    for f in sorted(os.listdir(d)):
        p = os.path.join(d, f)
        if f.endswith(".py") and os.path.abspath(p) != SELF:      # this guard is allowed to name it
            code += open(p, encoding="utf-8").read()
chk("no active module reads the superseded artefacts",
    "superseded_pre_contract" not in code, "active code references the superseded directory")

# ── 7. official data immutability ───────────────────────────────────────────────────────────────
man = os.path.join(HERE, "section_manifest.csv")
if os.path.exists(man):
    M = list(csv.DictReader(open(man, encoding="utf-8", newline="")))
    bad = []
    for row in M:
        if not row["path"].startswith("data/official_ps3/"):
            continue
        p = os.path.join(SEC, row["path"])
        if not os.path.exists(p) or hashlib.sha256(open(p, "rb").read()).hexdigest()[:12] != str(row["sha256_12"]):
            bad.append(row["path"])
    chk("official dataset unmodified (hash match)", not bad, f"changed: {bad}")
else:
    chk("official dataset has a manifest", False, "run tools/build_manifest.py first")

print(f"\nLEAKAGE CHECKS: {'ALL PASSED' if not FAIL else 'FAILED -> ' + ', '.join(FB)}")
sys.exit(FAIL)
