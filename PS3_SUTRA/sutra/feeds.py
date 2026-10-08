"""Two additive read-only feeds the workbench frontend needs, and nothing else (§3, additive-only).

    GET /v1/places?as_of=&q=&state=&tier=&town_id=&limit=&cursor=   the place list
    GET /v1/evidence?as_of=&q=&outcome=&polarity=&town_id=&limit=&cursor=   the evidence feed

Both are **projections over stored rows**: nothing here computes a candidate, a score, a tier, a
radius, a gate, a priority or a weight. Every value is read from `belief_versions`, `observations`
and `evidence_scores` through the same as-of gate the rest of the API uses, or from the frozen index.

Place identity: SUTRA keys places by address under the frozen rule `colocation<=30m|adjudicated`
(`sutra/memory.py`). With one member per place in the current store the projection collapses to the
member's belief — which is exactly what `/v1/place/{place_id}` serves for a single place. The list
endpoint therefore reads the stored belief rows rather than recomputing 3,000 beliefs.
"""
from __future__ import annotations

from . import views
from .indexes import get_index

# The five states the frozen projection can produce for a place (`sutra/memory.py::place_state`).
PLACE_STATES = ("CONTESTED", "MOVED_SUSPECTED", "CONFIRMED", "WARM", "COLD")

_FEED_NOTE = ("read-only projection over stored rows: no arm, weight, tier, radius or gate is "
              "computed here, and the as-of gate is the only temporal filter")


def _project_place_state(tier: str | None, status: str | None, has_belief: bool) -> str:
    """The single-member case of the frozen projection, restated once, in one place."""
    if status == "CONTESTED":
        return "CONTESTED"
    if status == "MOVED_SUSPECTED":
        return "MOVED_SUSPECTED"
    if tier == "CONFIRMED":
        return "CONFIRMED"
    if tier == "PROBABLE":
        return "WARM"
    return "COLD" if has_belief else "COLD"


def _place_row(address_id: str, ix, store, as_of: str, visits: dict[str, dict]) -> dict:
    rec = ix.addresses.get(address_id) or {}
    town_id = rec.get("town_id") or ix.town_of(address_id)
    belief = store.latest_belief_before(address_id, as_of)
    payload = (belief or {}).get("payload") or {}
    candidate = payload.get("candidate") or {}
    radius = payload.get("radius") or {}
    agg = visits.get(address_id) or {}
    status = (belief or {}).get("status")
    tier = (belief or {}).get("tier")
    state = _project_place_state(tier, status, bool(belief))
    return {
        "place_id": payload.get("place_id") or f"PL-{address_id}",
        "address_id": address_id,
        "town_id": town_id,
        "label": rec.get("address_text") or rec.get("address_text_raw") or address_id,
        "account_id": rec.get("account_id"),
        "address_type": rec.get("address_type"),
        "source": rec.get("source"),                       # the address master's own source column
        "added_date": rec.get("added_date"),
        "state": state,
        "tier": tier,
        "status": status,
        "belief_version": payload.get("belief_version"),
        "coordinate_space": views.coordinate_space(town_id),
        "coordinate": ({"x": candidate.get("x"), "y": candidate.get("y"),
                        "granularity": candidate.get("granularity"),
                        "radius_m": radius.get("radius_m"), "basis": radius.get("basis")}
                       if candidate.get("x") is not None else None),
        "uncertainty": ({"radius_m": radius.get("radius_m"), "basis": radius.get("basis"),
                         "measured_coverage": radius.get("measured_coverage"),
                         "n_calibration": radius.get("n_calibration"),
                         "source_stratum": radius.get("source_stratum"),
                         "widened": radius.get("widened"), "widen_reason": radius.get("widen_reason")}
                        if radius else None),
        "contradictions": ([address_id] if status in ("CONTESTED", "MOVED_SUSPECTED") else []),
        "visits": agg.get("n", 0),
        "positives": agg.get("positives", 0),
        "last_evidence_at": agg.get("last_at"),
        "last_positive_at": agg.get("last_positive_at"),
        "evidence_newest_kind": agg.get("last_kind"),
        "has_belief": bool(belief),
    }


def _visit_counts(store, as_of: str, ix) -> dict[str, dict]:
    """One pass over the as-of-gated observation set: counts and latest timestamps per address."""
    out: dict[str, dict] = {}
    for o in store.observations_upto(as_of):
        a = o.get("address_id")
        agg = out.setdefault(a, {"n": 0, "positives": 0, "last_at": None, "last_positive_at": None,
                                 "last_kind": None, "last_polarity": None})
        agg["n"] += 1
        at = o.get("observed_at")
        if agg["last_at"] is None or (at or "") > agg["last_at"]:
            agg["last_at"] = at
            agg["last_kind"] = o.get("kind")
            agg["last_polarity"] = o.get("polarity")
        if o.get("polarity") == "positive":
            agg["positives"] += 1
            if agg["last_positive_at"] is None or (at or "") > agg["last_positive_at"]:
                agg["last_positive_at"] = at
    return out


def places_feed(store, as_of: str, *, q: str | None = None, state: str | None = None,
                tier: str | None = None, town_id: str | None = None, limit: int = 60,
                cursor: str | None = None) -> dict:
    """`GET /v1/places` — the workbench's place list over the stored beliefs."""
    ix = get_index()
    visits = _visit_counts(store, as_of, ix)
    ids = sorted(ix.addresses)
    rows = [_place_row(a, ix, store, as_of, visits) for a in ids]
    facets = {"by_state": {}, "by_tier": {}, "by_town": {}}
    for r in rows:
        facets["by_state"][r["state"]] = facets["by_state"].get(r["state"], 0) + 1
        facets["by_tier"][r["tier"] or "UNRESOLVED"] = facets["by_tier"].get(r["tier"] or "UNRESOLVED", 0) + 1
        facets["by_town"][r["town_id"]] = facets["by_town"].get(r["town_id"], 0) + 1
    out = rows
    if town_id:
        out = [r for r in out if r["town_id"] == town_id]
    if state and state.upper() != "ALL":
        out = [r for r in out if r["state"] == state.upper()]
    if tier and tier.upper() != "ALL":
        out = [r for r in out if (r["tier"] or "UNRESOLVED") == tier.upper()]
    if q:
        needle = q.strip().lower()
        out = [r for r in out
               if needle in " ".join(str(r.get(k) or "") for k in
                                     ("place_id", "address_id", "label", "account_id", "town_id")).lower()]
    out.sort(key=lambda r: r["place_id"])
    start = 0
    if cursor:
        start = next((i for i, r in enumerate(out) if r["place_id"] > cursor), len(out))
    page = out[start:start + int(limit)]
    return {
        "as_of": as_of,
        "query": q, "filters": {"state": state, "tier": tier, "town_id": town_id, "limit": int(limit)},
        "count": len(page), "total_matching": len(out),
        "items": page,
        "facets": facets,
        "next_cursor": (page[-1]["place_id"] if page and start + int(limit) < len(out) else None),
        "states": list(PLACE_STATES),
        "identity_rule": "colocation<=30m|adjudicated",
        "projection": True,
        "note": _FEED_NOTE + "; places are address-keyed under the frozen identity rule",
    }


def evidence_feed(store, as_of: str, *, q: str | None = None, outcome: str | None = None,
                  polarity: str | None = None, town_id: str | None = None, limit: int = 120,
                  cursor: str | None = None) -> dict:
    """`GET /v1/evidence` — the visit feed, shaped exactly like `/v1/address/{id}/observations`."""
    ix = get_index()
    rows = store.observations_upto(as_of)
    ids = [r["observation_id"] for r in rows]
    ev = store.evidence_for(ids) if ids else {}
    items = []
    for r in sorted(rows, key=lambda r: (r.get("observed_at") or "", r["observation_id"]), reverse=True):
        o = views.shape_observation(ix, r, ev.get(r["observation_id"]) or {})
        items.append(o)
    facets = {"by_outcome": {}, "by_polarity": {}, "by_town": {}, "by_evidence_class": {}}
    for o in items:
        facets["by_outcome"][o["outcome"]] = facets["by_outcome"].get(o["outcome"], 0) + 1
        facets["by_polarity"][o["polarity"]] = facets["by_polarity"].get(o["polarity"], 0) + 1
        facets["by_town"][o["town_id"]] = facets["by_town"].get(o["town_id"], 0) + 1
        cls = (o.get("evidence") or {}).get("evidence_class")
        facets["by_evidence_class"][cls] = facets["by_evidence_class"].get(cls, 0) + 1
    out = items
    if town_id:
        out = [o for o in out if o["town_id"] == town_id]
    if outcome and outcome.upper() != "ALL":
        out = [o for o in out if o["outcome"] == outcome]
    if polarity and polarity.upper() != "ALL":
        out = [o for o in out if o["polarity"] == polarity]
    if q:
        needle = q.strip().lower()
        out = [o for o in out
               if needle in " ".join(str(o.get(k) or "") for k in
                                     ("observation_id", "address_id", "agent_id", "device_id",
                                      "remark", "place_id")).lower()]
    start = 0
    if cursor:
        start = next((i for i, o in enumerate(out) if _ev_key(o) < cursor), len(out))
    page = out[start:start + int(limit)]
    return {
        "as_of": as_of,
        "query": q, "filters": {"outcome": outcome, "polarity": polarity, "town_id": town_id,
                                "limit": int(limit)},
        "count": len(page), "total_matching": len(out),
        "items": page,
        "facets": facets,
        "next_cursor": (_ev_key(page[-1]) if page and start + int(limit) < len(out) else None),
        "negatives_move_coordinate": False,
        "note": _FEED_NOTE,
    }


def _ev_key(o: dict) -> str:
    return f"{o.get('observed_at') or ''}|{o.get('observation_id')}"
