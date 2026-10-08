"""The eligibility gate (P9, contract §10).

    address_purpose × tier/state × request_purpose  ->  SERVE | VERIFY_FIRST | REFUSE

`address_purpose` never grants permission by itself, and `request_purpose` is required and logged.
Refusal is a successful decision, not an error. Rule-based, versioned, auditable.
"""
from __future__ import annotations

from . import config, purpose as purpose_mod
from .version import GATE_RULE_VERSION


def decide(address_purpose: dict, belief: dict, request_purpose: str, *, radius_band_m: float | None = None,
           borrower_confirmed_residence: bool = False) -> dict:
    purpose_mod.validate_request_purpose(request_purpose)
    cls = address_purpose.get("class", "UNKNOWN")
    tier = belief.get("tier", "UNPLACEABLE")
    status = belief.get("status", "STABLE")
    n_neg = int(belief.get("support", {}).get("negatives_independent", 0) or 0)
    radius = (belief.get("radius") or {}).get("radius_m")
    band = radius_band_m

    def out(action: str, reason: str) -> dict:
        return {"action": action, "reason": reason, "rule_version": GATE_RULE_VERSION,
                "request_purpose": request_purpose, "address_purpose": cls, "tier": tier, "status": status}

    if cls == "OTHER":
        return out("REFUSE", "purpose_other")
    if cls == "WORK_LIKE" and not borrower_confirmed_residence:
        return out("REFUSE", "purpose_work_like")
    if cls == "UNKNOWN":
        # abstention is a success state: an unknown place is still navigable (VERIFY_FIRST), and is only
        # refused where the *task* demands a SERVE-grade location (notice/visit planning, [S55]).
        if tier in ("CONFIRMED", "PROBABLE") and status == "STABLE" and not n_neg:
            return out("VERIFY_FIRST", "purpose_unknown")
        if request_purpose in config.WORK_LIKE_REFUSE_PURPOSES:
            return out("REFUSE", "purpose_unknown_low_confidence")
        return out("VERIFY_FIRST", "tier_approximate" if tier == "APPROXIMATE" else "unplaceable")

    # HOME_LIKE (or a work-like address independently confirmed as the residence)
    if status in ("CONTESTED", "MOVED_SUSPECTED"):
        return out("VERIFY_FIRST", "negatives_accumulated" if n_neg else "status_contested")
    if tier == "UNPLACEABLE":
        return out("VERIFY_FIRST", "unplaceable")
    if n_neg >= config.NEG_ACCUMULATION_MIN:
        return out("VERIFY_FIRST", "negatives_accumulated")
    if tier in ("CONFIRMED", "PROBABLE"):
        if band is not None and radius is not None and radius > band:
            return out("VERIFY_FIRST", "radius_beyond_band")
        return out("SERVE", "purpose_home_like" if tier == "CONFIRMED" else "tier_probable")
    return out("VERIFY_FIRST", "tier_approximate")
