"""Radius and uncertainty (P8, contract §7; Amendments U1/U2).

The published payload is exactly:

    {radius_m, basis, nominal, measured_coverage, n_calibration, source_stratum, widened, widen_reason}

Rules enforced here:
* `basis` is `empirical_p80` — the shipped basis. `nominal` is non-null only where a nominal level was
  **measured** on this dataset, which is nowhere: it stays `null` and no document may claim 90%.
* a stratum is published under its own name only if it is publishable (n >= 15 **and** transfer held);
  otherwise it falls back to `locality` (the only published stratum) with `source_stratum` naming it.
* the pincode stratum is **withheld**: measured to fail transfer (0% coverage at p80, n=4).
* `widened` has exactly three triggers — `calibration_fallback`, `stale_pack`, `negative_accumulation`
  — and always carries `widen_reason`.
"""
from __future__ import annotations

from . import config

NO_RADIUS = {"radius_m": None, "basis": None, "nominal": None, "measured_coverage": None,
             "n_calibration": None, "source_stratum": None, "widened": None, "widen_reason": None}


def published_stratum(stratum: str) -> tuple[str, bool]:
    """(stratum actually used, was it a fallback)."""
    entry = config.RADIUS_TABLE.get(stratum)
    if entry is None or not entry.get("publishable") or (entry.get("n_calibration") or 0) < config.N_GUARD:
        return config.FALLBACK_STRATUM, True
    return stratum, False


def radius_for(candidate: dict | None, tier: str, status: str = "STABLE", n_negatives: int = 0,
               stale: bool = False) -> dict:
    """The one place a radius is produced."""
    if candidate is None or tier == "UNPLACEABLE":
        return dict(NO_RADIUS)

    stratum = candidate.get("provenance", {}).get("stratum") or candidate.get("granularity") or "locality"
    used, fallback = published_stratum(stratum)
    entry = config.RADIUS_TABLE[used]
    base = float(entry["radius_m"])

    factor = 1.0
    triggers: list[str] = []
    if fallback:
        factor *= config.WIDEN["calibration_fallback"]
        triggers.append("calibration_fallback")
    if tier == "PROBABLE":
        factor *= config.WIDEN["probable"]
    elif tier == "APPROXIMATE":
        factor *= config.WIDEN["approximate"]
    if n_negatives >= 1:
        factor *= min(1.5, 1.0 + 0.05 * n_negatives) * (
            config.WIDEN["negative_accumulation"] if n_negatives >= config.NEG_ACCUMULATION_MIN else 1.0)
        triggers.append("negative_accumulation")
    if stale:
        factor *= config.WIDEN["stale_pack"]
        triggers.append("stale_pack")
    # the event that forced the widening is named first; a static fallback is the least informative
    order = ("negative_accumulation", "stale_pack", "calibration_fallback")
    trigger = next((t for t in order if t in triggers), None)

    return {
        "radius_m": round(base * factor, 1),
        "basis": "empirical_p80",
        "nominal": None,                       # never a nominal claim without a measured one (U2)
        "measured_coverage": entry["measured_coverage"],
        "n_calibration": entry["n_calibration"],
        "source_stratum": used,
        "widened": bool(trigger is not None),
        "widen_reason": trigger,
        "radius_map_version": None,            # filled by the caller from version.py
    }


def radius_table_view() -> dict:
    """The published radius map, for receipts and docs (no hidden numbers)."""
    out = {}
    for stratum, e in config.RADIUS_TABLE.items():
        used, fallback = published_stratum(stratum)
        out[stratum] = {"published_as": used, "fallback": fallback, "radius_m": e["radius_m"],
                        "n_calibration": e["n_calibration"], "measured_coverage": e["measured_coverage"],
                        "publishable": e["publishable"]}
    return out
