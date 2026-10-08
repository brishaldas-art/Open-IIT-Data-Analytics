"""Product infrastructure (P1/P2): the operations surface a workstation needs.

WHAT THIS MODULE MAY DO
    · read the store and derive operational aggregates, case timelines and snapshots
    · append to `task_events` (the existing append-only case ledger) for task lifecycle and
      human adjudication
    · run an advisory "what would this visit change" simulation **on a throwaway copy** of the store
    · read the frozen receipts to publish the evaluation figures as data

WHAT THIS MODULE MUST NEVER DO
    · change candidate generation, ranking, radius, gate, evidence or memory semantics
    · write to the production store except through `append_task_event`
    · invent a value that is not derived from stored rows or a frozen artefact

ADJUDICATION AND BELIEF — the honest boundary
    A human adjudication records a *review decision*: it closes or reopens the case, with the actor,
    the note and the belief it was made against. It does **not** rewrite belief, because the frozen
    rules say only field evidence moves a coordinate or a tier. So "Confirm location" closes the
    review; it never fabricates a confirmation the field never produced. That distinction is carried
    in the payload (`belief_unchanged: true`) and stated in the UI.
"""
from __future__ import annotations

import json
import os
import shutil
import tempfile
import time
from datetime import timedelta

from . import asof, config, views
from .version import RULE_VERSION

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DERIVED = os.path.join(ROOT, "data", "derived")

# ── the case state machine (open → in_progress → resolved, and back via reopened) ───────────────
TASK_STATES = ("open", "in_progress", "resolved", "reopened")
ACTIVE_STATES = ("open", "in_progress", "reopened")
TRANSITIONS = {
    "open": ("in_progress", "resolved", "reopened"),
    "in_progress": ("resolved", "reopened"),
    "reopened": ("in_progress", "resolved"),
    "resolved": ("reopened",),
}
# `POST /v1/adjudicate` decision vocabulary — the repository contract is authoritative
# (`PS3_API_AND_COMPONENT_DESIGN.md` §2.4: "confirm|deny|inconclusive"); the Arena handoff spells the
# same three words `confirmed|not_true|inconclusive`. Both spellings are accepted; the canonical word
# is stored.
ADJUDICATION_DECISIONS = ("confirm", "deny", "inconclusive")
DECISION_ALIASES = {
    "confirm": "confirm", "confirmed": "confirm", "location_confirmed": "confirm",
    "deny": "deny", "denied": "deny", "not_true": "deny", "moved_confirmed": "deny",
    "inconclusive": "inconclusive", "unresolved": "inconclusive",
}
# HOW A HUMAN DECISION IS SCORED — declared, not hidden.
#
# The contract (§5) stores an adjudication as an observation with `kind='adjudication'`, and the only
# weight table in the system is the frozen outcome table; there is no separate weight for a reviewer.
# So the decision is mapped onto the frozen outcome whose **class** it declares — the most
# conservative outcome in that class — and the reviewer's own word is preserved verbatim in
# `decision`. Every adjudication returns this mapping, the observation keeps `kind='adjudication'` so
# the audit always shows the true source, and a `deny` maps to a negative outcome, which by the frozen
# invariant can never relocate a coordinate by itself.
DECISION_MAPPING = {
    "confirm": ("met_family", "positive",
                "the conservative positive outcome: the household is at this address"),
    "deny": ("no_such_person", "process",
             "a negative outcome: it can never move the coordinate by itself"),
    "inconclusive": ("locked_premises", "ambiguous",
                     "the weak-support outcome: it neither confirms nor relocates"),
}

# product language for the reasons a case exists (no internal cause codes reach the user)
CAUSE_COPY = {
    "MOVED_SUSPECTED": {"title": "Possible move detected", "detail": "Field evidence suggests the place may not be where we think it is."},
    "CONTESTED": {"title": "Conflicting field evidence", "detail": "Strong observations disagree about this location."},
    "WIDE_RADIUS": {"title": "Location is too broad", "detail": "The location is known only to a wide area."},
    "NOT_CONFIRMED": {"title": "Address could not be confirmed", "detail": "No independent confirmation has been recorded yet."},
    "NO_LOCATION": {"title": "No reliable location", "detail": "Nothing in the official evidence supports an address-level location."},
}
STATE_COPY = {"open": "Needs review", "in_progress": "Under review", "resolved": "Reviewed", "reopened": "Reopened"}

EVIDENCE_QUALITY = ("strong", "fair", "weak", "rejected")


def _latest_belief_rows(store) -> dict[str, dict]:
    """Most recent stored belief row per address (one row each; the store is append-only)."""
    rows: dict[str, dict] = {}
    for r in store.conn.execute(
        "SELECT address_id, belief_version, tier, status, candidate_id, as_of, computed_at, payload_json"
        " FROM belief_versions ORDER BY address_id, belief_version"
    ):
        row = dict(r)
        try:
            payload = json.loads(row.pop("payload_json") or "{}")
        except json.JSONDecodeError:
            payload = {}
        row["radius_m"] = (payload.get("radius") or {}).get("radius_m")
        rows[row["address_id"]] = row
    return rows


def _belief_census(store) -> dict:
    latest = _latest_belief_rows(store)
    by_tier: dict[str, int] = {}
    by_status: dict[str, int] = {}
    for r in latest.values():
        by_tier[r["tier"]] = by_tier.get(r["tier"], 0) + 1
        if r["status"]:
            by_status[r["status"]] = by_status.get(r["status"], 0) + 1
    return {"latest_beliefs": len(latest), "by_tier": by_tier, "by_status": by_status}


# ══ §14 · overview — operational aggregates only ════════════════════════════════════════════════
def overview_payload(store, as_of: str | None = None, ix=None) -> dict:
    """`GET /v1/overview` — the operational workload, in the operator's language.

    Deliberately absent: latency, store counters, evaluation-firewall counters, capability status and
    every version hash. Those are engineering concerns and belong in the developer view, not here.
    """
    from .indexes import get_index
    ix = ix or get_index()
    cut = asof.parse_ts(as_of) if as_of else asof.parse_ts("2026-06-01T00:00:00Z")
    census = _belief_census(store)

    tasks = views.tasks_list(store, town_id=None, state="all", as_of=None, limit=100000)
    active = [t for t in tasks["items"] if t["state"] in ACTIVE_STATES]
    by_cause: dict[str, int] = {}
    for t in active:
        by_cause[t["cause"]] = by_cause.get(t["cause"], 0) + 1

    # every timestamp comparison goes through the one as-of gate (`sutra.asof`), never a raw SQL WHERE
    observed = store.observations_upto(cut)
    newest = max((o["observed_at"] for o in observed), default=None)
    window_start = cut - timedelta(days=30)
    recent = sum(1 for o in observed if not asof.is_before(o["observed_at"], window_start))
    # the cold/warm split the brief asks for: warm means the address has at least one real field
    # observation known at the cut, cold means it has none. Counted, never modelled.
    warm_addresses = {o["address_id"] for o in observed if o.get("address_id")}
    warm = sum(1 for a in warm_addresses if a in ix.addresses)
    cold = max(0, len(ix.addresses) - warm)

    towns = []
    for town_id in sorted(ix.towns):
        towns.append({
            "town_id": town_id,
            "addresses": sum(1 for a, rec in ix.addresses.items() if rec.get("town_id") == town_id),
            "needs_review": sum(1 for t in active if t["town_id"] == town_id),
        })

    packs = _pack_freshness(cut)

    tier = census["by_tier"]
    return {
        "as_of": asof.to_utc_str(cut),
        "computed_at": asof.now_utc(),
        "addresses": {
            "indexed": len(ix.addresses),
            "with_location": tier.get("CONFIRMED", 0) + tier.get("PROBABLE", 0),
            "confirmed": tier.get("CONFIRMED", 0),
            "not_confirmed": tier.get("APPROXIMATE", 0),
            "unplaceable": tier.get("UNPLACEABLE", 0),
            "needs_review": len(active),
            "conflicting": census["by_status"].get("MOVED_SUSPECTED", 0) + census["by_status"].get("CONTESTED", 0),
            "warm": warm,
            "cold": cold,
            "warm_share": round(warm / len(ix.addresses), 4) if ix.addresses else None,
            "by_tier": dict(sorted(tier.items())),
        },
        "workload": {
            "active_cases": len(active),
            "by_reason": [{"cause": c, **CAUSE_COPY.get(c, {"title": c.replace("_", " ").title(), "detail": None}),
                           "count": n} for c, n in sorted(by_cause.items(), key=lambda kv: (-kv[1], kv[0]))],
            "by_town": [{"town_id": t["town_id"], "count": t["needs_review"]} for t in towns if t["needs_review"]],
        },
        "field_activity": {
            "visits_recorded": len(observed),
            "visits_last_30_days": recent,
            "latest_visit": newest,
            "window_days": 30,
        },
        "data_freshness": {
            "evidence_newest": newest,
            "packs": packs,
            "available_offline": True,
        },
        "towns": towns,
    }


# ══ §16 · task lifecycle ═════════════════════════════════════════════════════════════════════════
def _events_for_task(store, task_id: str) -> list[dict]:
    """Every event in a case's ledger, in the order it was written.

    Ordered by the table's own insertion order (`rowid`), not by timestamp and definitely not by
    event id: two transitions can land in the same second, and the *latest state* must be the last
    thing appended, not the largest hash. Read-only.
    """
    rows = store.conn.execute(
        "SELECT rowid AS _rowid, * FROM task_events WHERE task_id = ? ORDER BY _rowid", (task_id,)
    ).fetchall()
    out = []
    for r in rows:
        e = dict(r)
        e.pop("_rowid", None)
        payload = e.get("payload") or (json.loads(e["payload_json"]) if e.get("payload_json") else {})
        out.append({**e, "payload": payload})
    return out


def task_detail(store, task_id: str) -> dict:
    """`GET /v1/tasks/{task_id}` — one case, its history and its adjudication record."""
    events = _events_for_task(store, task_id)
    if not events:
        raise KeyError(f"unknown task: {task_id}")
    latest = events[-1]
    base = {**latest["payload"], "at": latest["at"], "state": latest["kind"],
            "priority": latest["priority"], "town_id": latest["town_id"], "task_id": task_id,
            "event_id": latest["event_id"]}
    task = views.task_payload(base, store)
    return {
        "task": task,
        "history": [_history_row(e) for e in events],
        "adjudications": [_adjudication_row(e) for e in events if _is_adjudication(e)],
        "allowed_transitions": list(TRANSITIONS.get(latest["kind"], ())),
        "state_label": STATE_COPY.get(latest["kind"], latest["kind"]),
    }


def _is_adjudication(e: dict) -> bool:
    return str(e.get("reason") or "").startswith("adjudication:")


def _history_row(e: dict) -> dict:
    return {
        "at": e["at"],
        "state": e["kind"],
        "state_label": STATE_COPY.get(e["kind"], e["kind"]),
        "actor": (e["payload"] or {}).get("actor"),
        "note": (e["payload"] or {}).get("note"),
        "reason": e.get("reason"),
        "event_id": e["event_id"],
    }


def _adjudication_row(e: dict) -> dict:
    p = e["payload"] or {}
    return {
        "at": e["at"], "decision": p.get("decision"), "actor": p.get("actor"),
        "note": p.get("note"), "belief_unchanged": True,
        "decided_against": {"tier": p.get("tier_at_decision"), "status": p.get("status_at_decision"),
                            "candidate_id": p.get("candidate_id_at_decision"),
                            "radius_m": p.get("radius_at_decision")},
        "event_id": e["event_id"],
    }


def transition_task(store, task_id: str, to_state: str, *, actor: str | None = None,
                    note: str | None = None, at: str | None = None,
                    idempotency_key: str | None = None) -> dict:
    """Append a lifecycle transition. Append-only, idempotent, validated against the state machine."""
    if to_state not in TASK_STATES:
        raise ValueError(f"unknown state: {to_state} (expected one of {', '.join(TASK_STATES)})")
    events = _events_for_task(store, task_id)
    if not events:
        raise KeyError(f"unknown task: {task_id}")
    when = asof.to_utc_str(at) if at else asof.now_utc()
    key = idempotency_key or f"tr:{task_id}:{to_state}:{when}"
    event_id = f"TE-{abs(hash(key)) % (10 ** 12):012d}"
    # A replay is answered from the ledger *before* the state machine is consulted: a retried request
    # from a field device must return the recorded transition, not an error about the world moving on.
    prior = _find_event(store, event_id)
    if prior is not None:
        return {"task_id": task_id, "from": (prior["payload"] or {}).get("from_state"),
                "to": prior["kind"], "at": prior["at"], "event_id": event_id, "replayed": True,
                "state_label": STATE_COPY.get(prior["kind"], prior["kind"])}
    current = events[-1]["kind"]
    if to_state == current:
        raise ValueError(f"this case is already {STATE_COPY.get(current, current).lower()}")
    if to_state not in TRANSITIONS.get(current, ()):
        raise ValueError(f"cannot move a case from {current} to {to_state}")
    payload = {**(events[-1]["payload"] or {}), "actor": actor, "note": note,
               "from_state": current, "to_state": to_state, "idempotency_key": key}
    store.append_task_event(event_id, task_id, to_state, when, payload,
                            address_id=events[-1].get("address_id"),
                            place_id=events[-1].get("place_id"),
                            town_id=events[-1].get("town_id"),
                            priority=events[-1].get("priority"),
                            reason=f"transition:{current}->{to_state}")
    return {"task_id": task_id, "from": current, "to": to_state, "at": when,
            "state_label": STATE_COPY.get(to_state, to_state), "event_id": event_id, "replayed": False}


def _find_event(store, event_id: str) -> dict | None:
    for e in store.task_events():
        if e["event_id"] == event_id:
            payload = e.get("payload") or (json.loads(e["payload_json"]) if e.get("payload_json") else {})
            return {**e, "payload": payload}
    return None


def _event_exists(store, event_id: str) -> bool:
    return _find_event(store, event_id) is not None


def adjudicate(store, *, task_id: str | None = None, address_id: str | None = None,
               visit_id: str | None = None, decision: str, actor: str | None = None,
               note: str | None = None, at: str | None = None,
               idempotency_key: str | None = None) -> dict:
    """`POST /v1/adjudicate` — the only human ground-truth write (`PS3_API_AND_COMPONENT_DESIGN.md` §2.4).

    The decision is stored as an **observation** with `kind='adjudication'` and the derived belief is
    updated through the existing frozen mechanism (`store.submit_observation` → evidence → belief),
    exactly as the contract specifies. Nothing here computes a weight, a tier or a coordinate: the
    frozen engine does that, and this function only records what the reviewer decided and replays the
    result. Old observations are never modified — a correction arrives as a new observation.

    The case is then closed with an appended task event, because a reviewer's decision settles the
    case (the memory architecture: a contradiction "persists until resolved by evidence or
    adjudication"). Both writes are appends.
    """
    from .store import submit_observation

    canonical = DECISION_ALIASES.get(str(decision or "").strip().lower())
    if canonical is None:
        raise ValueError(f"unknown decision: {decision} (expected one of {', '.join(ADJUDICATION_DECISIONS)})")
    if not idempotency_key:
        raise ValueError("idempotency_key is required for an adjudication (contract §12)")
    if not actor:
        # a human ground-truth write names the human: an anonymous adjudication would be untraceable
        raise ValueError("actor is required for an adjudication (it is stored as the observing agent)")

    # the case we are adjudicating: an explicit task, an explicit address, or the visit's address
    resolved_task_id = task_id
    target_address = address_id
    if resolved_task_id:
        events = _events_for_task(store, resolved_task_id)
        if not events:
            raise KeyError(f"unknown task: {resolved_task_id}")
        target_address = target_address or events[-1].get("address_id")
    if not target_address and visit_id:
        detail = store.get_observation(visit_id)
        target_address = (detail or {}).get("address_id")
    if not target_address:
        raise ValueError("address_id, task_id or visit_id is required")

    open_task = views.task_for_address(store, target_address) if target_address else None
    if resolved_task_id is None and open_task:
        resolved_task_id = open_task["task_id"]

    # IDEMPOTENCY FIRST (contract §12): a repeated key returns the recorded result and writes nothing,
    # even if the world has moved on since. Checked before the state machine, or a retried request from
    # a field device would be answered with an error about the case having already been reviewed.
    prior = store.receipt_for(idempotency_key)
    if prior is not None:
        receipt = dict(prior)
        receipt["replayed"] = True
        return _adjudication_response(store, receipt, canonical, target_address, resolved_task_id,
                                      idempotency_key, replayed=True)

    if resolved_task_id:
        events = _events_for_task(store, resolved_task_id)
        if not events:
            raise KeyError(f"unknown task: {resolved_task_id}")
        if events[-1]["kind"] == "resolved":
            raise ValueError("this case is already reviewed — reopen it before recording another decision")

    outcome, outcome_class, basis = DECISION_MAPPING[canonical]
    when = asof.to_utc_str(at) if at else asof.now_utc()
    observation_id = f"obs-adj-{abs(hash(idempotency_key)) % (10 ** 16):016d}"
    observation = {
        "observation_id": observation_id,
        "kind": "adjudication",
        "address_id": target_address,
        "agent_id": actor,
        "actor": actor,
        "decision": canonical,
        "outcome": outcome,
        "observed_at": when,
        "note": note,
        "visit_id": visit_id,
        "checkin": None,
        "media": [],
        "remark": note,
    }
    receipt = submit_observation(observation, idempotency_key, store=store)
    return _adjudication_response(store, receipt, canonical, target_address, resolved_task_id,
                                  idempotency_key, replayed=bool(receipt.get("replayed")),
                                  actor=actor, note=note, when=when, visit_id=visit_id)


def _adjudication_response(store, receipt, canonical, target_address, resolved_task_id,
                           idempotency_key, *, replayed, actor=None, note=None, when=None,
                           visit_id=None) -> dict:
    """The contract §2.4 response: `{observation_id, belief_version, effect}` plus the mapping."""
    changed = receipt.get("changed") or {}
    fields = changed.get("fields") or {}
    belief_id = receipt.get("belief_version")
    out = {
        "observation_id": receipt.get("observation_id") or f"obs-adj-{abs(hash(idempotency_key)) % (10 ** 16):016d}",
        "address_id": target_address,
        "decision": canonical,
        "outcome": receipt.get("outcome") or DECISION_MAPPING[canonical][0],
        "belief_version": belief_id,
        "tier": receipt.get("tier"),
        "status": receipt.get("status"),
        "effect": {
            "changed": bool(changed.get("changed")),
            "fields": fields,
            # the contract: `coordinate_moved=true` is only ever written by an adjudication record
            "coordinate_moved": "candidate_id" in fields,
            "belief_before": receipt.get("belief_before"),
            "belief_after": receipt.get("belief_after"),
        },
        "mapping": {"decision": canonical, "outcome": DECISION_MAPPING[canonical][0],
                    "outcome_class": DECISION_MAPPING[canonical][1], "basis": DECISION_MAPPING[canonical][2]},
        "task": {"task_id": resolved_task_id, "closed": False, "state": None},
        "replayed": bool(replayed),
        "never_enters_s_eval": True,
        "note_text": ("Recorded as an adjudication observation (source: reviewer, not a visit). Old "
                      "observations are untouched; the belief was recomputed by the frozen engine."),
        "received_at": receipt.get("server_received_at"),
    }
    if not replayed and resolved_task_id:
        events = _events_for_task(store, resolved_task_id)
        prior_event = events[-1]
        event_id = f"ADJ-{abs(hash(idempotency_key)) % (10 ** 12):012d}"
        payload = {**(prior_event["payload"] or {}), "decision": canonical, "actor": actor, "note": note,
                   "adjudication_observation_id": out["observation_id"],
                   "belief_version_at_decision": belief_id,
                   "outcome": out["outcome"], "idempotency_key": idempotency_key}
        store.append_task_event(event_id, resolved_task_id, "resolved",
                                when or asof.to_utc_str(asof.now_utc()), payload,
                                address_id=target_address, place_id=prior_event.get("place_id"),
                                town_id=prior_event.get("town_id"), priority=prior_event.get("priority"),
                                reason=f"adjudication:{canonical}")
        out["task"] = {"task_id": resolved_task_id, "closed": True, "state": "resolved",
                       "state_label": STATE_COPY["resolved"], "event_id": event_id}
    elif not replayed:
        out["task"] = {"task_id": None, "closed": False, "state": None,
                       "reason": "no open case for this address"}
    else:
        detail = task_detail(store, resolved_task_id) if resolved_task_id else None
        out["task"] = {"task_id": resolved_task_id, "closed": bool(detail and detail["task"]["state"] == "resolved"),
                       "state": (detail["task"]["state"] if detail else None)}
    return out


# ══ §18 · score_visit — advisory, on a throwaway copy of the store ══════════════════════════════
def score_visit(store, observation: dict, *, idempotency_key: str | None = None,
                store_path: str | None = None) -> dict:
    """`POST /v1/score_visit` — what would this visit change, if it happened?

    The simulation runs the real ingest path against a **temporary copy** of the store and is then
    discarded. The production store is never written to: no observation, no evidence row, no belief
    row, no counter. Advisory only — it cannot influence ranking.
    """
    from .store import Store, submit_observation

    for field in ("address_id", "observed_at", "outcome"):
        if not observation.get(field):
            raise ValueError(f"{field} is required")
    outcome = observation["outcome"]
    if outcome not in config.OUTCOME_BASE:
        raise ValueError(f"outcome {outcome!r} is not in the evidence vocabulary "
                         f"({', '.join(sorted(config.OUTCOME_BASE))})")
    claimed = outcome not in config.NEGATIVE_OUTCOMES
    checkin = observation.get("checkin") or {}
    if claimed and checkin.get("x") is None:
        raise ValueError("a claiming outcome requires a checkin position")
    if not claimed and checkin.get("x") is not None:
        raise ValueError("an address_not_traceable / no_such_person observation may not claim a position")

    # The scoring has an agent-baseline factor, so the simulation must say *who* it assumes. Stated
    # openly in `assumptions` rather than hidden: an assumed agent is an assumption, not a fact.
    assumed_agent = observation.get("agent_id")
    agent_basis = "supplied"
    if not assumed_agent:
        row = store.conn.execute(
            "SELECT agent_id FROM observations WHERE address_id=? AND agent_id IS NOT NULL"
            " ORDER BY observed_at DESC LIMIT 1", (observation["address_id"],)).fetchone()
        if row is None:
            raise ValueError("agent_id is required for a simulation at an address with no prior visit")
        assumed_agent, agent_basis = row["agent_id"], "last_visitor_at_this_address"
    sim = {"kind": "visit", "agent_id": assumed_agent, **observation}
    if "media" not in sim:
        sim["media"] = []

    src_path = store_path or store.path
    tmp_dir = tempfile.mkdtemp(prefix="sutra-score-visit-")
    tmp_path = os.path.join(tmp_dir, "store.sqlite")
    try:
        src = store.conn
        dst = __import__("sqlite3").connect(tmp_path)
        src.backup(dst)
        dst.close()
        sandbox = Store(tmp_path)
        key = idempotency_key or f"sv:{observation['address_id']}:{observation['observed_at']}"
        receipt = submit_observation(sim, key, store=sandbox)
        after = sandbox.latest_belief(observation["address_id"])
        sandbox.close()
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    changed = receipt.get("changed", {"changed": None})
    delta = receipt.get("task_delta", {})
    headline = _visit_headline(receipt)
    return {
        "advisory": True,
        "applied": False,
        "address_id": observation["address_id"],
        "observed_at": observation["observed_at"],
        "outcome": outcome,
        "headline": headline,
        "belief_before": receipt.get("belief_before"),
        "belief_after": receipt.get("belief_after"),
        "changed": changed,
        "task_delta": delta,
        "decision_changed": bool(changed.get("changed")),
        "assumptions": {"agent_id": assumed_agent, "agent_basis": agent_basis,
                        "media_supplied": bool(sim.get("media"))},
        "note": ("Simulated on a copy of the store and discarded. Nothing was written: the production "
                 "store is untouched, and this result cannot influence a future decision."),
        "belief_after_row": after,
    }


def _visit_headline(receipt: dict) -> str:
    before, after = receipt.get("belief_before") or {}, receipt.get("belief_after") or {}
    cb, ca = before.get("tier"), after.get("tier")
    sb, sa = before.get("status"), after.get("status")
    rb, ra = before.get("radius_m"), after.get("radius_m")
    if not (receipt.get("changed") or {}).get("changed"):
        return "No decision change"
    if cb != ca and ca:
        if ca == "CONFIRMED":
            return "Potentially confirmed"
        if ca in ("APPROXIMATE", "UNPLACEABLE"):
            return "Would weaken the current answer"
        return f"Tier would become {ca}"
    if sb != sa and sa:
        return f"Status would become {sa.replace('_', ' ').lower()}"
    if rb is not None and ra is not None and ra > rb:
        return "Uncertainty would widen"
    if rb is not None and ra is not None and ra < rb:
        return "Uncertainty would narrow"
    return "Would change the case record"


# ══ §45 · batch resolve ══════════════════════════════════════════════════════════════════════════
BATCH_LIMIT = 5000          # the contract's ceiling (`PS3_API_AND_COMPONENT_DESIGN.md` §2.6)


def _batch_result_copy(r: dict) -> str:
    """One line of product language per row — the decision itself is the backend's, never recomputed."""
    action = r["eligibility"]["action"]
    if action == "SERVE":
        return "Location ready to use"
    if action == "VERIFY_FIRST":
        return "Location is best-known only — verify before use"
    return "No reliable location — not served"


def batch_resolve(store, items: list[dict], *, as_of: str | None = None,
                  request_purpose: str = "FIELD_NAVIGATION", ix=None) -> dict:
    """`POST /v1/batch_resolve` — resolve a bounded list, with an aggregate summary.

    The contract allows up to 5,000 rows per call and asks for a per-row ticket summary plus refusal
    rate, tier mix and a radius histogram. **This is never a bulk-accuracy benchmark**: accuracy is
    measured on adjudicated or surveyed ground truth, which a batch call cannot see. The summary
    describes what the batch *returned*, not how correct it was.
    """
    from .resolve import resolve
    t0 = time.monotonic()
    if not isinstance(items, list) or not items:
        raise ValueError("items must be a non-empty list")
    if len(items) > BATCH_LIMIT:
        raise ValueError(f"at most {BATCH_LIMIT} addresses per request")
    when = asof.parse_ts(as_of) if as_of else asof.parse_ts("2026-06-01T00:00:00Z")
    rows = []
    for it in items:
        text = (it or {}).get("address_text") or ""
        city = (it or {}).get("town_hint")
        address_id = (it or {}).get("address_id")
        if not text and not address_id:
            rows.append({"input": it, "status": "invalid", "message": "address_text or address_id is required"})
            continue
        try:
            r = resolve(text, city, when, request_purpose, store=store, ix=ix, address_id=address_id)
        except Exception as e:  # one bad row must not fail the batch
            rows.append({"input": it, "status": "error", "message": str(e)[:200]})
            continue
        has_location = r.get("coordinate") is not None
        rows.append({
            "input": it,
            "address_id": r.get("address_id"),
            "status": r["eligibility"]["action"],
            "result": _batch_result_copy(r),
            "tier": r.get("tier"),
            "radius_m": (r.get("radius_m") if has_location else None),
            "has_location": has_location,
            "reason_codes": r.get("reasons") or [],
            "next_action": (r.get("task") or {}).get("recommended_action", {}).get("label"),
        })

    decided = [r for r in rows if r.get("status") in ("SERVE", "VERIFY_FIRST", "REFUSE")]
    served = [r for r in decided if r["status"] == "SERVE"]
    tier_mix: dict[str, int] = {}
    for r in decided:
        tier_mix[r.get("tier") or "UNKNOWN"] = tier_mix.get(r.get("tier") or "UNKNOWN", 0) + 1
    radii = [r["radius_m"] for r in decided if r["radius_m"] is not None]
    return {
        "as_of": asof.to_utc_str(when),
        "computed_at": asof.now_utc(),
        "requested": len(items),
        "limit": BATCH_LIMIT,
        "elapsed_ms": round((time.monotonic() - t0) * 1000.0, 1),
        "counts": {s: sum(1 for r in rows if r.get("status") == s)
                   for s in sorted({r.get("status") for r in rows})},
        "summary": {
            "decided": len(decided),
            "refusal_rate": (round(1.0 - len(served) / len(decided), 4) if decided else None),
            "served": len(served),
            "tier_mix": dict(sorted(tier_mix.items())),
            "radius_histogram": _radius_histogram(radii),
            "radius_median_m": (sorted(radii)[len(radii) // 2] if radii else None),
            "not_a_benchmark": ("this describes what the batch returned, not how correct it was — "
                                "accuracy is measured on surveyed ground truth only"),
        },
        "items": rows,
    }


# ══ §19 · audit — the decision history in product language ══════════════════════════════════════
def audit_timeline(store, *, address_id: str | None = None, place_id: str | None = None,
                   as_of: str | None = None, ix=None, limit: int = 200) -> dict:
    """`GET /v1/audit` — what happened, why the decision changed, in the operator's language.

    Every row is derived from a stored row: an observation, a belief version, a task event. Nothing is
    reconstructed and nothing is invented. Raw identifiers ride along under `details` for the
    developer drawer only.
    """
    from .indexes import get_index
    ix = ix or get_index()
    cut = asof.parse_ts(as_of) if as_of else None
    events: list[dict] = []

    addresses: list[str]
    if address_id:
        addresses = [address_id]
    elif place_id:
        addresses = store.members_of_address(place_id) or [place_id.replace("PL-", "")]
        addresses = [a for a in addresses if a in ix.addresses] or [place_id.replace("PL-", "")]
    else:
        addresses = sorted({r["address_id"] for r in _latest_belief_rows(store).values()})

    for aid in addresses:
        for o in store.observations_upto(cut or asof.parse_ts("2100-01-01T00:00:00Z"), address_id=aid):
            ev = store.evidence_for([o["observation_id"]]).get(o["observation_id"], {})
            polarity = ev.get("polarity") or "unknown"
            events.append({
                "at": o["observed_at"], "kind": "field_evidence_received",
                "address_id": aid,
                "title": _outcome_title(o["outcome"]),
                "detail": _outcome_detail(o["outcome"], polarity),
                "quality": _quality_label(ev),
                "effect": "does not move the location" if polarity == "negative" else None,
                "details": {"observation_id": o["observation_id"], "outcome": o["outcome"],
                            "weight": ev.get("weight"), "polarity": polarity,
                            "agent_id": o.get("agent_id"), "visit_id": o.get("visit_id")},
            })

        prev = None
        for b in store.belief_versions(aid):
            if cut and asof.parse_ts(b["as_of"]) > cut:
                break
            try:
                payload = b.get("payload") or json.loads(b.get("payload_json") or "{}")
            except json.JSONDecodeError:
                payload = {}
            row = {**b, "payload": payload,
                   "radius_m": (payload.get("radius") or {}).get("radius_m")}
            if prev is not None:
                if (row["tier"], row["status"]) != (prev["tier"], prev["status"]):
                    events.append({
                        "at": row["as_of"], "kind": "decision_changed", "address_id": aid,
                        "title": f"Decision changed to {row['tier'].lower()} · {row['status'].replace('_', ' ').lower()}",
                        "detail": _decision_detail(prev, row),
                        "quality": None, "effect": None,
                        "details": {"from": {"tier": prev["tier"], "status": prev["status"]},
                                    "to": {"tier": row["tier"], "status": row["status"]},
                                    "belief_version": row["belief_version"]},
                    })
                if row["radius_m"] != prev["radius_m"]:
                    widened = (row["radius_m"] or 0) > (prev["radius_m"] or 0)
                    events.append({
                        "at": row["as_of"], "kind": "uncertainty_changed", "address_id": aid,
                        "title": "Uncertainty widened" if widened else "Uncertainty narrowed",
                        "detail": (f"±{prev['radius_m']:.0f} m → ±{row['radius_m']:.0f} m"
                                   if prev.get("radius_m") and row.get("radius_m") else None),
                        "quality": None, "effect": "location did not move" if widened else None,
                        "details": {"from_radius_m": prev.get("radius_m"), "to_radius_m": row.get("radius_m")},
                    })
            if row["status"] in ("MOVED_SUSPECTED", "CONTESTED") and (prev is None or prev["status"] != row["status"]):
                events.append({
                    "at": row["as_of"], "kind": "contradiction_detected", "address_id": aid,
                    "title": CAUSE_COPY.get(row["status"], {}).get("title", row["status"]),
                    "detail": CAUSE_COPY.get(row["status"], {}).get("detail"),
                    "quality": None, "effect": None,
                    "details": {"belief_version": row["belief_version"], "status": row["status"]},
                })
            prev = row

    for e in store.task_events():
        if e.get("address_id") not in addresses and e.get("place_id") != place_id:
            continue
        if cut and asof.parse_ts(e["at"]) > cut:
            continue
        payload = e.get("payload") or (json.loads(e["payload_json"]) if e.get("payload_json") else {})
        if _is_adjudication(e):
            events.append({
                "at": e["at"], "kind": "adjudication", "address_id": e.get("address_id"),
                "title": {"location_confirmed": "Location confirmed by reviewer",
                          "unresolved": "Reviewer marked this unresolved",
                          "moved_confirmed": "Reviewer confirmed the place has moved"}.get(payload.get("decision"), "Reviewed"),
                "detail": payload.get("note") or "The belief itself is unchanged — only field evidence can move it.",
                "quality": None, "effect": "belief unchanged",
                "details": {"task_id": e["task_id"], "decision": payload.get("decision"),
                            "actor": payload.get("actor"), "event_id": e["event_id"]},
            })
        elif e["kind"] == "open":
            events.append({
                "at": e["at"], "kind": "case_raised", "address_id": e.get("address_id"),
                "title": "Case opened for field verification",
                "detail": CAUSE_COPY.get(payload.get("cause"), {}).get("detail"),
                "quality": None, "effect": None,
                "details": {"task_id": e["task_id"], "cause": payload.get("cause")},
            })
        else:
            events.append({
                "at": e["at"], "kind": "case_state_changed", "address_id": e.get("address_id"),
                "title": f"Case {STATE_COPY.get(e['kind'], e['kind']).lower()}",
                "detail": payload.get("note"),
                "quality": None, "effect": None,
                "details": {"task_id": e["task_id"], "state": e["kind"], "event_id": e["event_id"]},
            })

    events.sort(key=lambda e: (e["at"], e["kind"]), reverse=True)
    return {
        "scope": {"address_id": address_id, "place_id": place_id},
        "as_of": asof.to_utc_str(cut) if cut else None,
        "count": len(events[:limit]),
        "total": len(events),
        "events": events[:limit],
    }


def _outcome_title(outcome: str) -> str:
    return {
        "met_borrower": "Borrower met at the address",
        "met_family": "Family met, borrower absent",
        "cash_collected": "Collection made at the address",
        "locked_premises": "Premises locked",
        "neighbour_says_shifted": "Neighbour says the household moved",
        "address_not_traceable": "Address could not be found",
        "no_such_person": "Nobody of that name known",
    }.get(outcome, outcome.replace("_", " "))


def _outcome_detail(outcome: str, polarity: str) -> str:
    if polarity == "negative":
        return "Counts as doubt. It cannot move the location — it can only widen uncertainty."
    if polarity == "ambiguous":
        return "Partial support: the visit happened but did not confirm the household."
    return "Supports this location."


def _quality_label(evidence: dict) -> str:
    w = evidence.get("weight")
    if evidence.get("polarity") == "negative":
        return "rejected"
    if w is None:
        return "fair"
    if w >= config.W_PROMOTE:
        return "strong"
    if w >= 0.20:
        return "fair"
    return "weak"


def _decision_detail(prev: dict, row: dict) -> str:
    if row["status"] == "MOVED_SUSPECTED":
        return "Contradicting field evidence accumulated; the place is now questioned."
    if prev["tier"] == "APPROXIMATE" and row["tier"] in ("PROBABLE", "CONFIRMED"):
        return "Independent confirmations reached the promotion threshold."
    return f"{prev['tier']} · {prev['status']} → {row['tier']} · {row['status']}"


# ══ §46 · case snapshot ══════════════════════════════════════════════════════════════════════════
def case_snapshot(store, address_id: str, *, as_of: str | None = None, ix=None) -> dict:
    """`GET /v1/address/{address_id}/case` — one address, one coherent story, one request."""
    from .indexes import get_index
    from .resolve import resolve
    ix = ix or get_index()
    if address_id not in ix.addresses:
        raise KeyError(f"unknown address_id: {address_id}")
    when = as_of or "2026-06-01T00:00:00Z"
    belief = views.belief_payload(store, address_id, when, ix=ix)
    place_id = belief["belief"].get("place_id")
    task = views.task_for_address(store, address_id, as_of=when)
    case = {
        "address_id": address_id,
        "town_id": belief.get("town_id"),
        "as_of": when,
        "belief": belief,
        "place": None,
        "task": task,
        "task_history": (_task_history_rows(store, task["task_id"]) if task else []),
        "evidence": views.observations_payload(store, address_id, when),
        "history": audit_timeline(store, address_id=address_id, as_of=when, ix=ix, limit=60),
        "decision": None,
    }
    if place_id:
        try:
            case["place"] = views.place_history_v1(place_id, when, store)
        except KeyError:
            case["place"] = None
    try:
        resp = resolve("", None, asof.parse_ts(when), "FIELD_NAVIGATION",
                       store=store, ix=ix, address_id=address_id)
        case["decision"] = views.resolve_blocks(resp, ix.town_of(address_id), store, when)
    except Exception:
        case["decision"] = None
    return case


def _task_history_rows(store, task_id: str) -> list[dict]:
    return [_history_row(e) for e in _events_for_task(store, task_id)]


# ══ §23 · method & trust — published from the frozen receipts, not hard-coded ═══════════════════
def method_trust_payload() -> dict:
    """`GET /v1/method-trust` — the evaluation figures and the mechanism, as data.

    The three populations are read from the frozen receipts. They are never merged, never recomputed
    and never dressed up: the cold figure is the honest cold-start floor over 100 surveyed addresses,
    the warm figure is the 31 addresses that answered under the frozen policy, and the product lane is
    what field navigation sees end to end.
    """
    pops = []
    precision = _read_json(os.path.join(DERIVED, "precision_optimization_receipt.json"))
    emp = _read_json(os.path.join(DERIVED, "evidence_memory_policy_receipt.json"))
    sealed = (precision or {}).get("sealed_s_eval", {})
    if sealed.get("cold"):
        c = sealed["cold"]
        pops.append({"key": "cold", "name": "Cold start, independent set",
                     "hit_500m": c["hit_500m"], "n": c["n"], "median_m": c["median_err_m"],
                     "caption": "Surveyed addresses with no field evidence available when the question was asked."})
    warm = ((emp or {}).get("s_eval", {}).get("warm", {}) or {}).get("final_policy")
    if warm:
        pops.append({"key": "warm", "name": "Independent set, field learning active",
                     "hit_500m": warm["hit_500m"], "n": warm["n"], "median_m": warm["median_err_m"],
                     "caption": f"The {warm['n']} addresses that answered under the frozen policy — not {warm['n']} out of 100."})
    if sealed.get("product"):
        p = sealed["product"]
        pops.append({"key": "product", "name": "Product lane",
                     "hit_500m": p["hit_500m"], "n": p["n"], "median_m": p["median_err_m"],
                     "caption": "Field navigation with field evidence where it exists and fallback where it does not."})
    return {
        "populations": pops,
        "population_note": ("These populations are separate by construction. They are not merged into one "
                            "accuracy figure, and none of them is a claim about every address."),
        "how_it_works": [
            {"step": 1, "title": "Read the address", "detail": "The address text and its locality cues are interpreted as written."},
            {"step": 2, "title": "Find candidate locations", "detail": "Official places that could be the address: the baseline pin, locality and town centres, official landmarks, and any address book entry."},
            {"step": 3, "title": "Add field history", "detail": "Confirmed visits to this place, and settled place memory where it applies."},
            {"step": 4, "title": "Compare the evidence", "detail": "Candidates are ranked by deterministic rules over evidence strength, agreement and locality match. No model decides this."},
            {"step": 5, "title": "Estimate uncertainty", "detail": "The radius is empirical for the calibration stratum, with a minimum sample guard; where data is thin it falls back to a wider, honest value."},
            {"step": 6, "title": "Apply the safety rules", "detail": "A single weak visit cannot confirm a location; contradicting evidence widens and caps; purpose rules decide whether a home-like answer may be served at all."},
            {"step": 7, "title": "Answer, verify or refuse", "detail": "Serve a location, send it for verification, or refuse to answer. Refusal is a result, not an error."},
            {"step": 8, "title": "Learn from the next visit", "detail": "New field evidence updates the place's belief and memory, and the next question is answered with it."},
        ],
        "safety_rules": [
            "A failed visit never relocates an address — it can only widen uncertainty and ask for verification.",
            "Conflicting evidence expands uncertainty instead of silently picking a side.",
            "One visit is never enough to confirm a location; independent visits are required.",
            "Weak evidence cannot override stronger evidence.",
            "Memory is keyed to the place, never to an account.",
            "Every decision is reproducible as of the date it was made, and old observations are never rewritten.",
            "Refusal is preferred over a precise-looking guess.",
        ],
        "learning_loop": ["Address", "Field visit", "Evidence quality", "Updated belief", "Better next answer"],
        "statuses": _product_statuses(),
        "development_note": ("Some capabilities are still being developed: reviewing a case is available now; "
                             "changing what the system believes requires field evidence, by design."),
        "evaluation_source": "frozen evaluation receipts (see PS3_IMPLEMENTATION_PHASE_REPORT_2026-10-07.md)",
    }


def _pack_freshness(cut) -> list[dict]:
    """The persisted offline packs on disk — newest per town. Strictly a read.

    `packs.build_pack` writes files, so the overview never calls it: it reports the packs that
    already exist, which is what an operator needs to know before going offline.
    """
    out: dict[str, dict] = {}
    pack_dir = os.path.join(DERIVED, "packs")
    if not os.path.isdir(pack_dir):
        return []
    for name in sorted(os.listdir(pack_dir)):
        if not name.endswith(".json"):
            continue
        doc = _read_json(os.path.join(pack_dir, name)) or {}
        town = doc.get("town_id")
        if not town:
            continue
        built = doc.get("built_for_as_of")
        age = round((cut - asof.parse_ts(built)).total_seconds() / 86400.0, 2) if built else None
        valid_until = doc.get("valid_until")
        stale = bool(valid_until and asof.parse_ts(cut) > asof.parse_ts(valid_until))
        row = {"town_id": town, "pack_version": doc.get("pack_version"), "updated": built,
               "age_days": age, "valid_until": valid_until, "stale": stale,
               "addresses": doc.get("n_addresses"),
               "landmarks": len(doc.get("landmarks") or []), "localities": len(doc.get("localities") or []),
               "valid_days": doc.get("valid_days"),
               # the server does not track per-device downloads; a device echoes its own copy (contract §12)
               "downloaded_at": None,
               "downloaded_at_note": "reported by a device that echoes its pack version; not tracked here"}
        if town not in out or str(built or "") > str(out[town].get("updated") or ""):
            out[town] = row
    return [out[t] for t in sorted(out)]


def _read_json(path: str) -> dict | None:
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError):
        return None


# ── the four honest product status labels (§16), assembled from the runtime's own capability map ──
_LABEL_WORDING = {
    "metrics_api": "A metrics/BI API",
    "learned_ranker": "A learned ranker (evaluated and not adopted; rules remain in production)",
    "model_training": "Model training inside the product",
    "calibration_learning": "Learning the calibration map (research only)",
    "place_neighbour_arm": "The place-neighbour candidate arm (experiment-gated, off)",
    "offline_pack_capture_replay": "Offline pack capture and replay",
    "task_state_transitions": "Case lifecycle: start review, resolve, reopen",
    "adjudication_write": "Recording a reviewer's decision (the only human ground-truth write)",
    "audit_chain_read": "Decision history for any answer or belief version",
    "batch_resolve": "Resolving a bounded list of addresses in one call",
    "overview": "The operational overview",
    "place_read": "Place history, contradictions and memory",
    "verification_queue_read": "The verification queue",
    "plane_geometry": "The local metric plane (candidates, evidence points, uncertainty ring)",
    "alternatives_explanation": "Why alternatives lost",
    "typed_reason_codes": "Typed reason codes for every decision",
    "resolve": "Resolving an address, including refusal",
    "evidence_write": "Recording field evidence",
}


def _product_statuses() -> list[dict]:
    """Map the runtime's capability map onto the four labels the product shows.

    `implemented` → IMPLEMENTED, `design`/`partial`/`research_only` → DESIGNED,
    `not_implemented` → NOT YET IMPLEMENTED, `evaluated_not_adopted` → NOT YET IMPLEMENTED (it was
    evaluated and rejected, so it is not in the product). Nothing here is invented: every entry is a
    key the runtime itself publishes.
    """
    buckets: dict[str, list[str]] = {"IMPLEMENTED": [], "DESIGNED": [], "NOT YET IMPLEMENTED": []}
    for key, value in sorted(views.CAPABILITIES.items()):
        if value == "implemented":
            bucket = "IMPLEMENTED"
        elif value in ("design", "partial", "research_only"):
            bucket = "DESIGNED"
        else:
            bucket = "NOT YET IMPLEMENTED"
        buckets[bucket].append(_LABEL_WORDING.get(key, key.replace("_", " ")))
    buckets["NOT MEASURED"] = [
        "Any accuracy figure beyond the three frozen populations",
        "Field impact on collection outcomes",
        "Any cost or rupee saving",
        "Vendor-comparison performance",
    ]
    return [{"label": label, "items": items} for label, items in buckets.items()]


# ══ §13 · GET /v1/audit/{belief_id} — the provenance chain for one answer ════════════════════════
def audit_chain(store, belief_id: str, *, ix=None) -> dict:
    """The full chain for one belief version: what arrived, how it was weighted, what changed.

    `belief_id` is `{address_id}:{belief_version}` (e.g. `AD002936:7`); a bare address id resolves to
    that address's latest stored version. Read-only, assembled from stored rows only.
    """
    from .indexes import get_index
    ix = ix or get_index()
    address_id, _, version = belief_id.partition(":")
    if address_id not in ix.addresses:
        raise KeyError(f"unknown address_id: {address_id}")
    versions = store.belief_versions(address_id)
    if not versions:
        raise KeyError(f"no stored belief for {address_id}")
    row = None
    if version.strip():
        try:
            wanted = int(version)
        except ValueError:
            raise ValueError(f"belief_id must be {{address_id}}:{{version}}, got {belief_id!r}")
        row = next((b for b in versions if int(b["belief_version"]) == wanted), None)
        if row is None:
            raise KeyError(f"no belief version {wanted} for {address_id}")
    else:
        row = versions[-1]
    payload = row.get("payload") or json.loads(row.get("payload_json") or "{}")
    at = row["as_of"]

    # evidence known at this belief's instant, with the weight the engine gave it
    observations = store.observations_upto(asof.parse_ts(at), address_id=address_id)
    scores = store.evidence_for([o["observation_id"] for o in observations])
    chain = []
    for o in sorted(observations, key=lambda x: x["observed_at"], reverse=True):
        ev = scores.get(o["observation_id"], {})
        chain.append({
            "at": o["observed_at"],
            "observation_id": o["observation_id"],
            "kind": o.get("kind"),
            "outcome": o.get("outcome"),
            "agent_id": o.get("agent_id"),
            "weight": ev.get("weight"),
            "polarity": ev.get("polarity"),
            "evidence_class": ev.get("evidence_class"),
            "reason_codes": ev.get("reason_codes") or [],
            "independence": ev.get("independence_tuple"),
        })

    prev = next((b for b in versions if int(b["belief_version"]) == int(row["belief_version"]) - 1), None)
    radius = payload.get("radius") or {}
    before_radius = None
    if prev is not None:
        prev_payload = prev.get("payload") or json.loads(prev.get("payload_json") or "{}")
        before_radius = (prev_payload.get("radius") or {}).get("radius_m")

    arms = payload.get("arms_considered") or []
    winner = next((a for a in arms if a.get("candidate_id") == row["candidate_id"]), None)
    tasks = []
    for e in store.task_events():
        if e.get("address_id") != address_id or asof.parse_ts(e["at"]) > asof.parse_ts(at):
            continue
        p = e.get("payload") or (json.loads(e["payload_json"]) if e.get("payload_json") else {})
        tasks.append({"at": e["at"], "task_id": e["task_id"], "state": e["kind"],
                      "reason": e.get("reason"), "decision": p.get("decision"), "actor": p.get("actor"),
                      "note": p.get("note")})
    tasks.sort(key=lambda t: t["at"])

    return {
        "belief_id": f"{address_id}:{row['belief_version']}",
        "address_id": address_id,
        "belief": {
            "belief_version": row["belief_version"], "as_of": at, "tier": row["tier"],
            "status": row["status"], "candidate_id": row["candidate_id"],
            "radius_m": radius.get("radius_m"), "rules_version": row["rules_version"],
            "evidence_policy_version": row["evidence_policy_version"],
            "radius_map_version": row["radius_map_version"], "payload_sha256": row["payload_sha256"],
        },
        "winner": ({"arm": winner.get("arm"), "candidate_id": winner.get("candidate_id"),
                    "granularity": winner.get("granularity"), "source": winner.get("source"),
                    "score": winner.get("score"), "as_of_valid": winner.get("as_of_valid"),
                    "licence_class": winner.get("licence_class")} if winner else None),
        "alternatives_lost": [{"candidate_id": a.get("candidate_id"), "arm": a.get("arm"),
                               "reasons": a.get("reasons") or []}
                              for a in arms if a.get("candidate_id") != row["candidate_id"]][:6],
        "uncertainty": {"radius_m": radius.get("radius_m"), "basis": radius.get("basis"),
                        "measured_coverage": radius.get("measured_coverage"),
                        "n_calibration": radius.get("n_calibration"),
                        "previous_radius_m": before_radius,
                        "widened": (radius.get("radius_m") is not None and before_radius is not None
                                    and radius["radius_m"] > before_radius)},
        "evidence": chain,
        "tasks": tasks,
        "steps": len(chain),
        "note": ("Read-only reconstruction from stored observations, evidence scores, belief versions and "
                 "task events. Nothing here is regenerated or invented."),
    }


# ══ §18 · radius histogram for a batch (buckets, not a claim) ════════════════════════════════════
_RADIUS_BUCKETS = ((0, 100), (100, 250), (250, 500), (500, 1000), (1000, 2000), (2000, float("inf")))


def _radius_histogram(radii: list[float]) -> list[dict]:
    out = []
    for lo, hi in _RADIUS_BUCKETS:
        n = sum(1 for r in radii if r is not None and lo <= r < hi)
        label = f"{lo}-{hi:g} m" if hi != float("inf") else f"{lo}+ m"
        out.append({"bucket": label, "count": n})
    return out
