"""Reading the official corpus. `data/official_ps3/` is READ-ONLY; nothing here ever writes.

Only three roots may be read: `official_ps3/`, `cleaned/`, `derived/` (final data policy, `[S95]`).
Address text parsing is deterministic and regex-only: no model, no LLM, no external gazetteer.
"""
from __future__ import annotations

import csv
import functools
import os
import re
import unicodedata

from . import config

# ── text parsing (deterministic; the only "NLP" in the preprocessing lane) ──────────────────────
_WS = re.compile(r"\s+")
_TOKEN = re.compile(r"[0-9A-Za-z\u0C80-\u0CFF]+")
_PIN = re.compile(r"\b(\d{6})\b")
_NUMWORD = re.compile(r"\b(\d{1,3})(?:st|nd|rd|th)\b", re.I)


ABBREV = {                       # the corpus-attested abbreviations (same table as the cleaner)
    r"\brd\b": "road", r"\bst\b": "street", r"\bngr\b": "nagar", r"\bblk\b": "block",
    r"\bh\.?\s?no\.?\b": "house", r"\bno\.\b": "number", r"\bgal\b": "gali",
    r"\bopp\.?\b": "opposite", r"\bnr\b": "near", r"\bflr\b": "floor",
    r"\bsoc\b": "society", r"\bapt\b": "apartment", r"\bxtn\b": "extension", r"\bext\b": "extension",
}
_KEEP = r"[^0-9a-z\u0900-\u097F\u0C80-\u0CFF]+"      # Latin + Devanagari + Kannada


def norm_text(s: str) -> str:
    """THE text normaliser — the runtime must reproduce the cleaner's `text_norm` exactly, or a typed
    address never matches its own indexed record. Kept here so there is exactly one definition;
    `tools/clean_official.py` imports this one (a second copy is how the two drifted apart)."""
    t = unicodedata.normalize("NFKC", str(s or ""))
    t = t.lower()
    for k, v in ABBREV.items():
        t = re.sub(k, v, t)
    t = re.sub(_KEEP, " ", t)
    return _WS.sub(" ", t).strip()


def tokens(s: str) -> list[str]:
    return _TOKEN.findall(norm_text(s))


def edit_ratio(a: str, b: str) -> float:
    """Levenshtein similarity in [0,1] — the one definition, shared by the ranker and the rings.

    The ranker's `_ratio` is an alias of this function (imported, never copied), so a fuzzy match
    means the same thing everywhere in the project.
    """
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    la, lb = len(a), len(b)
    prev = list(range(lb + 1))
    for i in range(1, la + 1):
        cur = [i] + [0] * lb
        for j in range(1, lb + 1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (a[i - 1] != b[j - 1]))
        prev = cur
    return 1.0 - prev[lb] / max(la, lb)


def pin_in_text(s: str) -> str | None:
    m = _PIN.search(s or "")
    return m.group(1) if m else None


def relation_windows(text: str, window: int = 3):
    """`(relation, tokens_before, tokens_after)` for the first relation phrase in the text.

    Both windows are returned because the corpus uses both orders: English "close to Hanuman Temple"
    (noun after) and Kannada "ಚರ್ಚ್ ಹತ್ತಿರ" — "church near" (noun before). Deterministic; the relation
    word is matched from a fixed, corpus-attested list and is only ever echoed back, never invented
    (`PS3_PURPOSE_AND_DIRECTION_MODULES.md` §2.5).
    """
    toks = tokens(text)
    for i in range(len(toks)):
        for rel in config.RELATION_WORDS:
            rel_toks = rel.split()
            if toks[i:i + len(rel_toks)] == rel_toks:
                j = i + len(rel_toks)
                return rel, toks[max(0, i - window):i], toks[j:j + window]
    return None, [], []


def relation_and_noun(text: str):
    """Back-compatible helper: the first noun token after the relation (else the one before it)."""
    rel, before, after = relation_windows(text)
    if rel is None:
        return None, None
    if after:
        return rel, after[0]
    if before:
        return rel, before[-1]
    return rel, None


# ── loaders ─────────────────────────────────────────────────────────────────────────────────────
def _read(path: str) -> list[dict]:
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


@functools.lru_cache(maxsize=None)
def _cached(path: str) -> tuple[dict, ...]:
    rows = _read(path)
    return tuple(rows)


def official(name: str) -> list[dict]:
    return [dict(r) for r in _cached(os.path.join(config.OFFICIAL, name))]


def cleaned(name: str) -> list[dict]:
    return [dict(r) for r in _cached(os.path.join(config.CLEANED, name))]


def derived(name: str) -> list[dict]:
    return [dict(r) for r in _cached(os.path.join(config.DERIVED, name))]


# ── typed views the runtime actually uses ───────────────────────────────────────────────────────
def addresses() -> dict[str, dict]:
    return {r["address_id"]: r for r in cleaned("addresses_clean.csv")}


def towns() -> dict[str, dict]:
    return {r["town_id"]: r for r in official("towns.csv")}


def localities() -> list[dict]:
    return official("localities.csv")


def landmarks() -> list[dict]:
    return official("landmarks_poi.csv")


def baseline_geocodes() -> dict[str, dict]:
    """The supplied frozen arm — no vendor call is ever made (contract §1, D44)."""
    return {r["address_id"]: r for r in official("baseline_geocodes.csv")}


@functools.lru_cache(maxsize=1)
def visit_gps_traces() -> dict[str, list[tuple[int, float, float, float | None]]]:
    """Official `visit_gps_points`: visit_id -> [(seq, x, y, accuracy_m)] ordered by seq.

    Read-only, no derivation: this is the raw approach track the field app recorded for each visit.
    It is used for exactly one thing — estimating *where the visit happened* better than a single
    check-in sample can (see `sutra.seed.trace_tail_point`).
    """
    out: dict[str, list[tuple[int, float, float, float | None]]] = {}
    for row in official("visit_gps_points.csv"):
        try:
            seq = int(row["seq"])
            x, y = float(row["x"]), float(row["y"])
        except (KeyError, TypeError, ValueError):
            continue
        acc = row.get("accuracy_m")
        try:
            acc = float(acc) if acc not in (None, "") else None
        except ValueError:
            acc = None
        out.setdefault(row["visit_id"], []).append((seq, x, y, acc))
    for k in out:
        out[k].sort(key=lambda p: p[0])
    return out


def visits() -> list[dict]:
    return cleaned("visits_clean.csv")


def trail_features() -> dict[str, dict]:
    return {r["visit_id"]: r for r in cleaned("trail_features.csv")}


def place_blocks() -> dict[str, dict]:
    return {r["address_id"]: r for r in derived("ps3_place_blocks.csv")}


def surveyed() -> dict[str, dict]:
    """Ground truth. **Evaluation only** — never a feature, never a supervision label (contract §2)."""
    return {r["address_id"]: r for r in official("surveyed_addresses.csv")}


def splits_table() -> dict[str, dict]:
    return {r["account_id"]: r for r in official("splits.csv")}


def baseline_precision(address_id: str) -> str | None:
    b = baseline_geocodes().get(address_id)
    return (b or {}).get("precision")
