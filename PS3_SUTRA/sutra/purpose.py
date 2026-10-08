"""Purpose classification (P9, contract §8; Purpose module P1–P5).

Three separate concepts, never collapsed (D41):

    request_purpose  — the caller's declared reason; an access-control input, never inferred
    address_purpose  — what the place IS: HOME_LIKE · WORK_LIKE · OTHER · UNKNOWN
    eligibility      — what ACTION is permitted (see `eligibility.py`)

Rule-based, deterministic, abstaining, LLM-free. `UNKNOWN` is a success state. A single observation
never decides; no purpose model is trained (there are no purpose labels — inventing them is forbidden).
"""
from __future__ import annotations

from . import asof, config, evidence as ev_mod
from .version import PURPOSE_RULE_VERSION


def classify(address_id: str, as_of, store, address: dict | None = None, ix=None) -> dict:
    from .indexes import get_index
    ix = ix or get_index()
    addr = address or ix.addresses.get(address_id) or {}
    obs = asof.observations_upto(store, as_of, address_id=address_id) if store is not None else []
    ev = store.evidence_for([o["observation_id"] for o in obs]) if (store is not None and obs) else {}

    met = []
    for o in obs:
        e = ev.get(o["observation_id"])
        if not e or e["polarity"] != "positive" or float(e["weight"]) < config.W_PROMOTE:
            continue
        met.append((o, e))

    kind = (addr.get("address_type") or "").strip()
    if kind == "office":
        return _out("WORK_LIKE", "high", ["address_type_office"], address_id)

    if len(met) >= 2:
        indep_ok, _ = ev_mod.promotion_ok([{**e, "independence": e["independence"], "x": o.get("x"),
                                            "y": o.get("y"), "duplicate_claim_of": o.get("duplicate_claim_of")}
                                           for o, e in met])
        dwell_ok = all((o.get("dwell_s") or 0) >= 180 for o, _ in met)
        hours = [asof.parse_ts(o["observed_at"]).astimezone(asof.IST) for o, _ in met]
        weekdayish = sum(1 for h in hours if h.weekday() < 5) >= max(1, len(hours) // 2)
        daytime = sum(1 for h in hours if config.VISIT_HOUR_START <= h.hour < config.VISIT_HOUR_END)
        if indep_ok and dwell_ok and weekdayish and daytime >= len(hours) - 1:
            basis = ["met_x2", "independence_ok", "dwell_ge_180s", "weekday_daytime_visits"]
            if kind != "office":
                basis.append("not_office_type")
            return _out("HOME_LIKE", "medium", basis, address_id)
        return _out("UNKNOWN", "low", ["mixed_evidence"], address_id)

    if kind == "permanent_native":
        return _out("OTHER", "medium", ["address_type_permanent_native"], address_id)

    if not obs:
        return _out("UNKNOWN", "low", ["insufficient_evidence"], address_id)
    return _out("UNKNOWN", "low", ["insufficient_evidence"], address_id)


def _out(cls: str, confidence: str, basis: list[str], address_id: str) -> dict:
    return {"address_id": address_id, "class": cls, "confidence": confidence, "basis": sorted(basis),
            "model_version": PURPOSE_RULE_VERSION}


def validate_request_purpose(request_purpose: str) -> str:
    """The declared purpose is required and must be from the frozen vocabulary (invariant 10)."""
    if not request_purpose:
        raise ValueError("request_purpose is required")
    if request_purpose not in config.REQUEST_PURPOSES:
        raise ValueError(f"unknown request_purpose: {request_purpose}")
    return request_purpose
