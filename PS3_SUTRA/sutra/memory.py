"""Place memory: identity, state, tasks (P5/P6, contract §6.2, Address Memory M1/M3).

* Memory belongs to a **place**, never to an account and never to a row. Identity comes from the
  place blocks (`ps3_place_blocks.csv`: ≤ 30 m co-location, city-blocked) plus adjudicated links,
  which are **events**: merges and splits are appended, reversible, and never silent.
* `place_state(place_id, as_of)` is a *read model*: it recomputes the belief of each member at
  `as_of` and aggregates the state. It is not a feature source (M3).
"""
from __future__ import annotations

from . import asof, config
from .version import RULE_VERSION
from . import store as store_mod


def place_id_for(address_id: str, ix) -> str:
    block = ix.block_of(address_id) if ix is not None else None
    return f"PL-{block}" if block else f"PL-{address_id}"


def place_members(place_id: str, ix) -> list[str]:
    key = place_id[3:] if place_id.startswith("PL-") else place_id
    members = sorted(a for a, b in ix.place_blocks.items() if b["block_id"] == key)
    return members or [key]


def record_link_event(store, place_id: str, address_id: str, reason: str, at) -> dict:
    """Append a link event (never a silent merge) and register the membership."""
    ev_id = f"{place_id}|{address_id}|link|{asof.to_utc_str(at)}"
    payload = {"place_id": place_id, "address_id": address_id, "kind": "link", "reason": reason,
               "rule_version": RULE_VERSION, "at": asof.to_utc_str(at)}
    store.append_place_event(ev_id, place_id, "link", address_id, at, reason, payload)
    store.link_place_member(place_id, address_id, ev_id, at, reason)
    return payload


def record_split_event(store, place_id: str, address_id: str, reason: str, at) -> dict:
    ev_id = f"{place_id}|{address_id}|split|{asof.to_utc_str(at)}"
    payload = {"place_id": place_id, "address_id": address_id, "kind": "split", "reason": reason,
               "rule_version": RULE_VERSION, "at": asof.to_utc_str(at)}
    store.append_place_event(ev_id, place_id, "split", address_id, at, reason, payload)
    return payload


def merge_review(place_id: str, ix, store) -> str:
    """`none` unless another place shares a member's identity evidence — surfaced, never auto-merged."""
    for member in place_members(place_id, ix)[:1]:
        others = ix.memory.get(member, {}).get("place_id")
        if others and others != place_id:
            return f"POSSIBLE_MATCH({others})"
    return "none"


def place_state(place_id: str, as_of, store=None) -> dict:
    """Aggregate read model over the place's members, recomputed as of `as_of`."""
    from .belief import compute_belief
    from .indexes import get_index
    ix = get_index()
    st = store or store_mod.Store()
    members = place_members(place_id, ix)
    beliefs = {}
    for a in members:
        try:
            beliefs[a] = compute_belief(a, as_of, st, ix=ix)
        except KeyError:
            continue
    tiers = [b["tier"] for b in beliefs.values()]
    statuses = {b["status"] for b in beliefs.values()}
    state = "COLD"
    if "CONTESTED" in statuses:
        state = "CONTESTED"
    elif "MOVED_SUSPECTED" in statuses:
        state = "MOVED_SUSPECTED"
    elif any(t == "CONFIRMED" for t in tiers):
        state = "CONFIRMED"
    elif any(t == "PROBABLE" for t in tiers):
        state = "WARM"
    elif beliefs:
        state = "COLD"
    conf = next((b for a, b in sorted(beliefs.items()) if b["tier"] == "CONFIRMED"), None)
    anchor = conf or next((b for a, b in sorted(beliefs.items()) if b["candidate"]), None)
    payload = {
        "place_id": place_id,
        "as_of": asof.to_utc_str(as_of),
        "member_address_ids": members,
        "identity_rule": "colocation<=30m|adjudicated",
        "state": state,
        "coordinate": ({"x": anchor["candidate"]["x"], "y": anchor["candidate"]["y"],
                        "radius_m": anchor["radius"]["radius_m"],
                        "basis": anchor["radius"]["basis"],
                        "n_calibration": anchor["radius"]["n_calibration"]} if anchor else None),
        "anchor_address_id": anchor["address_id"] if anchor else None,
        "members": {a: {"tier": b["tier"], "status": b["status"], "belief_version": b["belief_version"],
                        "candidate_id": b["candidate_id"]} for a, b in sorted(beliefs.items())},
        "contradictions": sorted(a for a, b in beliefs.items() if b["status"] in ("CONTESTED", "MOVED_SUSPECTED")),
        "history": [{"observation_id": r["observation_id"], "at": r["observed_at"]}
                    for a in members
                    for r in asof.observations_upto(st, as_of, address_id=a)][:50],
        "merge_review": merge_review(place_id, ix, st),
        "projection": True,          # this is a read model, never a feature source (M3)
    }
    return payload


# ── verification tasks ──────────────────────────────────────────────────────────────────────────
def ensure_verify_first_task(store, belief: dict, town_id: str | None = None) -> str:
    """Idempotently append a verify-first task event for a place that must be re-checked."""
    if town_id is None:
        from .indexes import get_index
        town_id = get_index().town_of(belief["address_id"])
    cause = belief["status"] if belief["status"] in ("MOVED_SUSPECTED", "CONTESTED") else "low_confidence"
    task_id = f"VF-{belief['address_id']}-{cause}"
    existing = {e["task_id"] for e in store.task_events()}
    if task_id in existing:
        return task_id
    priority = {"CONTESTED": 0.9, "MOVED_SUSPECTED": 0.8}.get(cause, 0.5)
    payload = {"task_id": task_id, "kind": "verify_first", "address_id": belief["address_id"],
               "place_id": belief.get("place_id"), "cause": cause,
               "tier": belief["tier"], "status": belief["status"],
               "negatives_independent": belief["support"]["negatives_independent"],
               "radius_m": belief["radius"]["radius_m"], "rule_version": RULE_VERSION}
    store.append_task_event(f"{task_id}|open", task_id, "open", belief["computed_from"]["observations_upto"],
                            payload, address_id=belief["address_id"], place_id=belief.get("place_id"),
                            town_id=town_id, priority=priority, reason=cause)
    return task_id


def verify_first_tasks(town_id: str, limit: int = 100, store=None) -> list[dict]:
    """Open verify-first tasks for a town, highest priority first (deterministic order)."""
    from .indexes import get_index
    st = store or store_mod.Store()
    ix = get_index()
    latest: dict[str, dict] = {}
    for e in st.task_events():
        aid = e.get("address_id")
        if town_id and ix.town_of(aid) != town_id:
            continue
        payload = e.get("payload_json")
        import json as _json
        p = _json.loads(payload) if isinstance(payload, str) else (payload or {})
        latest[e["task_id"]] = {**p, "at": e["at"], "state": e["kind"], "priority": e["priority"],
                                "town_id": e.get("town_id") or ix.town_of(aid)}
    items = [t for t in latest.values() if t.get("state") == "open"]
    items.sort(key=lambda t: (-float(t.get("priority") or 0.0), t["address_id"]))
    return items[:limit]
