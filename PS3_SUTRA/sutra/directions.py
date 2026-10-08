"""Landmark direction cues (P9, contract §9; Purpose module Part 2).

Deterministic, official landmarks only, straight-line distance + bearing + a relation word that came
**verbatim from the address text**. Advisory: directions never change tier, radius or eligibility.
No cue is better than a wrong cue — unresolved means `null`, never a guess.
"""
from __future__ import annotations

from . import config, dataio, geo
from .version import DIRECTIONS_RULE_VERSION


def landmarks_for(address: dict, candidate: dict, ix) -> list[dict]:
    """Resolve the landmark named by the address text, town-scoped, ambiguity surfaced."""
    text = address.get("address_text_raw") or address.get("address_text", "")
    rel, before, after = dataio.relation_windows(text)
    if rel is None or not (before or after):
        return []

    scored = []
    for p in ix.landmarks:
        if p["town_id"] != address["town_id"]:
            continue
        name_toks = set(dataio.tokens(p["name"]))
        score = 2 * len(name_toks & set(after)) + len(name_toks & set(before))
        if score > 0:
            scored.append((score, p))
    if not scored:
        return []
    best = max(s for s, _ in scored)
    hits = [p for s, p in scored if s == best]

    out = []
    for p in hits:
        d = geo.dist(candidate["x"], candidate["y"], p["x"], p["y"])
        if d > config.DIRECTION_MAX_M:
            continue
        bearing = geo.bearing_deg(candidate["x"], candidate["y"], p["x"], p["y"])
        ambiguous = len(hits) > 1
        cue = f"{p['name']} ~{geo.round10(d)} m, bearing {geo.compass(bearing)}"
        if rel:
            cue += f", {rel} it"
        out.append({"landmark": p["name"], "landmark_type": p["landmark_type"],
                    "distance_m": geo.round10(d), "bearing_deg": round(bearing, 1),
                    "cue_text": cue, "ambiguous": ambiguous, "source_ref": f"landmark:{p['poi_id']}",
                    "parsed_relation": rel, "rule_version": DIRECTIONS_RULE_VERSION})
    out.sort(key=lambda r: (r["distance_m"], r["source_ref"]))
    return out


def directions_for(address: dict, candidate: dict | None, ix) -> list[dict] | None:
    """`null` when nothing is resolvable, or when there is no candidate to be relative to."""
    if candidate is None:
        return None
    got = landmarks_for(address, candidate, ix)
    return got or None
