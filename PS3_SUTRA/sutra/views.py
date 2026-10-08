"""Read-model composition for frontend contract v1 (P0-1 … P0-11).

Every function here **projects a value the frozen runtime has already computed** into the shape the
interface is contracted to receive (`SUTRA_FRONTEND_BACKEND_CONTRACT_V1_2026-10-08.md`). Nothing in
this module generates candidates, scores evidence, chooses a radius, decides eligibility, mutates the
store, or reaches the network. If a value is not already in the runtime's own output, it is not here
— the honest answer is a documented gap, never an invented field.

Two deliberate pieces of *presentation* logic live here and nowhere else:

* `lost_reason` — read off the score terms the ranker already emitted, so the browser never parses
  backend text (contract §11);
* `next_action` — a lookup over `(gate action, gate reason)`, the same pair the gate already decided.

Both are re-derivable by the frontend from strings it also receives; the gate decision itself stays
authoritative.
"""
from __future__ import annotations

import base64
import json
import re

from . import asof, config, packs as packs_mod, uncertainty
from .version import ALL as VERSIONS
from .version import RADIUS_MAP_VERSION, RULE_VERSION

COORDINATE_SPACE_PREFIX = "sutra_local_metric_plane"

# The gate actions, in the frozen vocabulary (`sutra/eligibility.py`).
_GATE_SERVE = "SERVE"
_GATE_VERIFY = "VERIFY_FIRST"
_GATE_REFUSE = "REFUSE"

# ── presentation tables (not policy: each row is a rendering of a decision already made) ──────────
_HEADLINE = {
    _GATE_SERVE: "Serve this location",
    _GATE_VERIFY: "Answer, but verify first",
    _GATE_REFUSE: "Not served for this purpose",
}
_NEXT_ACTION = {
    (_GATE_SERVE, "purpose_home_like"): ("none", "Serve as resolved.", None),
    (_GATE_SERVE, "tier_probable"): ("none", "Serve as resolved.", None),
    (_GATE_VERIFY, "tier_approximate"): ("verification_visit", "Visit and confirm the address.",
                                         "one independent field confirmation"),
    (_GATE_VERIFY, "negatives_accumulated"): ("verification_visit",
                                              "Re-visit with a fresh independent collector.",
                                              "two clean independent positives"),
    (_GATE_VERIFY, "status_contested"): ("adjudicate", "Review the conflicting observations.",
                                         "a recorded adjudication"),
    (_GATE_VERIFY, "radius_beyond_band"): ("verification_visit", "Visit to tighten the radius.",
                                           "one independent field confirmation"),
    (_GATE_VERIFY, "unplaceable"): ("field_capture", "Capture a field observation to establish a place.",
                                    "any first field observation"),
    (_GATE_VERIFY, "purpose_unknown"): ("confirm_purpose", "Confirm what this place is.",
                                        "a visit that shows the place is home-like"),
    (_GATE_REFUSE, "purpose_work_like"): ("use_other_purpose", "This place is work-like; it is not served for this purpose.",
                                          None),
    (_GATE_REFUSE, "purpose_unknown_low_confidence"): ("confirm_purpose",
                                                       "Confirm what this place is before acting.",
                                                       "a recorded adjudication"),
    (_GATE_REFUSE, "purpose_other"): ("not_servable", "No candidate exists; there is nothing to serve.",
                                      None),
    (_GATE_REFUSE, "unplaceable"): ("field_capture", "Capture a field observation to establish a place.",
                                    "any first field observation"),
}
_NEXT_ACTION_FALLBACK = {
    _GATE_SERVE: ("none", "Serve as resolved.", None),
    _GATE_VERIFY: ("verification_visit", "Verify before acting.", "a field confirmation"),
    _GATE_REFUSE: ("not_servable", "Not served.", None),
}

SCORE_TERM = re.compile(r"^(?P<name>[A-Za-z_][A-Za-z0-9_]*)(?::(?P<subject>[A-Za-z0-9_\-]+))?=(?P<value>[+-]?[0-9.]+)$")


# ── §2 Coordinate ────────────────────────────────────────────────────────────────────────────────
def coordinate_space(town_id: str | None) -> str:
    return f"{COORDINATE_SPACE_PREFIX}:{town_id}"


def coordinate_block(resp: dict, town_id: str | None) -> dict | None:
    """The single v1 coordinate claim, or `None`.

    `None` on two conditions, both deliberate: there is no candidate, or the gate refused. A refused
    decision carries no usable coordinate anywhere in the v1 surface — the legacy flat `candidate`
    field is untouched for backward compatibility, and the interface is contracted not to render it.
    """
    cand = resp.get("candidate")
    action = (resp.get("eligibility") or {}).get("action")
    if not cand or action == _GATE_REFUSE:
        return None
    if cand.get("x") is None or cand.get("y") is None:
        return None
    return {"x": cand["x"], "y": cand["y"], "granularity": cand.get("granularity"),
            "coordinate_space": coordinate_space(town_id), "radius_m": resp.get("radius_m")}


# ── §4 Uncertainty ───────────────────────────────────────────────────────────────────────────────
def uncertainty_block(resp: dict) -> dict | None:
    if resp.get("radius_m") is None:
        return None
    gran = (resp.get("candidate") or {}).get("granularity")
    stratum = resp.get("source_stratum")
    return {
        "radius_m": resp.get("radius_m"),
        "basis": resp.get("radius_basis"),
        "nominal": resp.get("nominal"),                       # always null: never a claim without a measurement
        "measured_coverage": resp.get("measured_coverage"),
        "n_calibration": resp.get("n_calibration"),
        "source_stratum": stratum,
        "fallback_applied": bool(gran and stratum and gran != stratum and stratum == config.FALLBACK_STRATUM),
        "widened": resp.get("widened"),
        "widen_reason": resp.get("widen_reason"),
        "radius_map_version": RADIUS_MAP_VERSION,
    }


# ── §17 ReasonCode ───────────────────────────────────────────────────────────────────────────────
def _score_terms(code: str) -> tuple[str, str | None, float | None]:
    m = SCORE_TERM.match(code)
    if not m:
        return code, None, None
    name = m.group("name") if not m.group("subject") else f"{m.group('name')}:{m.group('subject')}"
    return name, m.group("subject"), float(m.group("value"))


def _phrase(code: str) -> str:
    name = code.split("=")[0]
    word = name.replace("_", " ").replace(":", " ")
    return word.strip().capitalize()


def reason_codes(resp: dict) -> list[dict]:
    """The typed expansion of every reason string the response carries (contract §17)."""
    out: list[dict] = []
    seen: set[tuple[str, str]] = set()

    def add(code: str, kind: str) -> None:
        if not code or (code, kind) in seen:
            return
        seen.add((code, kind))
        subject, effect = None, None
        if kind == "score_term":
            _, subject, effect = _score_terms(code)
        out.append({"code": code, "kind": kind, "subject": subject, "effect": effect,
                    "direction": ("neutral" if effect is None else ("positive" if effect >= 0 else "negative")),
                    "label": _phrase(code)})

    for code in resp.get("score_reasons") or []:
        add(code, "score_term")
    for code in resp.get("reasons") or []:
        if code.startswith("resolution:"):
            add(code, "resolution")
        elif code in ("no_candidate", "no_match_in_address_book", "area_context_locality_only"):
            add(code, "refusal")
        else:
            add(code, "support")
    if resp.get("widen_reason"):
        add(resp["widen_reason"], "widen")
    gate = resp.get("eligibility") or {}
    if gate.get("reason"):
        add(gate["reason"], "gate")
    return out


# ── §11 / P0-2 alternatives + lost reasons ───────────────────────────────────────────────────────
def _lost_reasons(alt: dict, winner: dict) -> list[str]:
    """Why this candidate did not win — read off the score terms both sides already carry.

    Deterministic, and additive to nothing: the winner's own terms are the reference, the
    alternative's own terms are the evidence. No threshold, weight or ordering is recomputed.
    """
    alt_terms = {_score_terms(c)[0]: _score_terms(c)[2] for c in alt.get("reasons") or []}
    win_terms = {_score_terms(c)[0]: _score_terms(c)[2] for c in winner.get("reasons") or []}
    out: list[str] = []

    alt_prior = next((v for k, v in alt_terms.items() if k.startswith("arm_prior:")), None)
    win_prior = next((v for k, v in win_terms.items() if k.startswith("arm_prior:")), None)
    if alt_prior is not None and win_prior is not None and alt_prior < win_prior:
        out.append(f"lower_arm_prior {alt_prior:+.3f} vs {win_prior:+.3f}")

    alt_gran = next((k.split(":", 1)[1] for k in alt_terms if k.startswith("granularity:")), None)
    win_gran = next((k.split(":", 1)[1] for k in win_terms if k.startswith("granularity:")), None)
    if alt_gran and win_gran:
        from .ranking import GRANULARITY_RANK
        if GRANULARITY_RANK.get(alt_gran, 0.25) < GRANULARITY_RANK.get(win_gran, 0.25):
            out.append(f"coarser_granularity {alt_gran} < {win_gran}")

    if "evidence_promotion_eligible" in win_terms and "evidence_promotion_eligible" not in alt_terms:
        out.append("no_promotion_credit")
    if alt.get("primary_eligible") is False:
        out.append("single_observation_not_primary_eligible")
    if "locality_match" in win_terms and "locality_match" not in alt_terms:
        out.append("locality_name_mismatch")
    for term, label in (("pin_unknown_penalty", "pin_unknown_penalty"),
                        ("outside_town_penalty", "outside_town_penalty"),
                        ("landmark_ambiguous_penalty", "landmark_ambiguous"),
                        ("coarse_precision_penalty", "coarse_precision_penalty")):
        if term in alt_terms:
            out.append(label)
    return out


def alternatives_block(resp: dict, limit: int = 6) -> list[dict]:
    """Every non-winning candidate from the already-ranked set, with its rank, margin and why-not.

    Ordering is the contract's deterministic rule — score descending, `candidate_id` ascending — and
    `rank` is the candidate's position in that one ordering over the whole ranked set (the winner is
    rank 1). No second scoring system: every number here is read off the ranked set the frozen ranker
    already produced.
    """
    considered = list(resp.get("arms_considered") or [])
    winner_id = resp.get("candidate_id")
    winner = next((c for c in considered if c["candidate_id"] == winner_id), None)
    win_score = resp.get("score")
    if winner is None or win_score is None:
        return []
    ordered = sorted(considered, key=lambda c: (-float(c.get("score") or 0.0), c["candidate_id"]))
    rank_of = {c["candidate_id"]: i + 1 for i, c in enumerate(ordered)}
    out = []
    for c in [x for x in ordered if x["candidate_id"] != winner_id][:limit]:
        lost = _lost_reasons(c, winner)
        margin = round(float(win_score) - float(c.get("score") or 0.0), 6)
        lost.append(f"score_margin {margin:+.6f}")
        out.append({"candidate_id": c["candidate_id"], "arm": c["arm"], "score": c.get("score"),
                    "rank": rank_of[c["candidate_id"]],
                    "granularity": _granularity_of(resp, c["candidate_id"]),
                    "primary_eligible": bool(c.get("primary_eligible")),
                    "reasons": list(c.get("reasons") or []),
                    "lost_reason": lost, "score_margin": margin})
    return out


def _granularity_of(resp: dict, candidate_id: str) -> str | None:
    """The ranked set does not carry granularity; the response's own winner does. For any other
    candidate it is read off its own `granularity:<value>` score term — the term the ranker emitted."""
    for c in resp.get("arms_considered") or []:
        if c["candidate_id"] != candidate_id:
            continue
        for code in c.get("reasons") or []:
            if code.startswith("granularity:"):
                return code.split(":", 1)[1].split("=")[0]
    return None


# ── §5 evidence summary (counts the runtime already carries — no recomputation) ───────────────────
def evidence_summary(resp: dict) -> dict | None:
    support = resp.get("support")
    if support is None:
        return None
    return {
        "n_observations": support.get("n_observations"),
        "n_positives": support.get("n_positives"),
        "negatives_independent": support.get("negatives_independent"),
        "independent_confirmations": support.get("independent_confirmations"),
        "duplicate_claims": support.get("duplicate_claims"),
        "positive_weight_sum": support.get("positive_weight_sum"),
        "negatives_move_coordinate": False,                    # invariant, stated for the interface
        "radius_widened": resp.get("widened"),
        "widen_reason": resp.get("widen_reason"),
    }


# ── §8 decision ticket ───────────────────────────────────────────────────────────────────────────
def decision_ticket(resp: dict, town_id: str | None, task: dict | None = None,
                    codes: list[dict] | None = None, alts: list[dict] | None = None) -> dict:
    gate = resp.get("eligibility") or {}
    action, reason = gate.get("action"), gate.get("reason")
    has_cand = resp.get("candidate") is not None
    headline = "No candidate → no coordinate" if not has_cand else _HEADLINE.get(action, action or "")
    kind, label, clears = _NEXT_ACTION.get((action, reason), _NEXT_ACTION_FALLBACK.get(action, ("none", "", None)))
    cand = resp.get("candidate") or {}
    provenance = None
    if cand:
        prov = cand.get("provenance") or {}
        provenance = {"arm": cand.get("arm"), "source_ref": cand.get("source_ref"),
                      "granularity": cand.get("granularity"), "licence_class": cand.get("licence_class"),
                      "as_of_valid": cand.get("as_of_valid"), "built_at": cand.get("built_at"),
                      "stratum": prov.get("stratum"), "prior_candidate_arm": prov.get("prior_candidate_arm"),
                      "memory_evidence_derived": prov.get("memory_evidence_derived")}
    top_alt = (alts or [None])[0] if alts else None
    return {
        "headline": headline,
        "case_id": resp.get("address_id"),
        "town_id": town_id,
        "gate": {"action": action, "reason": reason, "rule_version": gate.get("rule_version"),
                 "request_purpose": gate.get("request_purpose")},
        "answer": ({"candidate_id": resp.get("candidate_id"), "arm": cand.get("arm"),
                    "granularity": cand.get("granularity"), "score": resp.get("score"),
                    "tier": resp.get("tier"), "status": resp.get("status")} if cand else None),
        "why": [c for c in (codes or []) if c["kind"] in ("support", "resolution", "widen")],
        "score_terms": [c for c in (codes or []) if c["kind"] == "score_term"],
        "provenance": provenance,
        "margin": ({"top_alternative_candidate_id": top_alt["candidate_id"],
                    "score_margin": top_alt["score_margin"]} if top_alt else None),
        "confidence": {"tier": resp.get("tier"), "status": resp.get("status"),
                       "measured_coverage": resp.get("measured_coverage"),
                       "n_calibration": resp.get("n_calibration")},
        "belief_version": resp.get("belief_version"),
        "place_id": resp.get("place_id"),
        "next_action": {"kind": kind, "label": label, "clears_when": clears},
        "task": (task or {}).get("task_id") if task else None,
        "refusal": (None if cand else {"kind": "no_candidate",
                                       "coordinate_withheld": True,
                                       "reason_codes": [c["code"] for c in (codes or [])
                                                        if c["kind"] in ("refusal", "gate")]})
                   if action != _GATE_REFUSE else {"kind": reason, "coordinate_withheld": True,
                                                   "reason_codes": [c["code"] for c in (codes or [])
                                                                    if c["kind"] in ("refusal", "gate")]},
    }


# ── §9 the composed read (P0-1): eight additive blocks on the frozen resolve response ────────────
def resolve_blocks(resp: dict, town_id: str | None, store=None, as_of=None) -> dict:
    """Everything contract v1 adds to `POST /resolve`, and nothing else.

    Called with a completed flat response — it never recomputes the decision. Every block is a
    projection of values already in `resp` (plus, for the task link, one read of the task store).
    """
    task = None
    if store is not None and resp.get("address_id"):
        task = task_for_address(store, resp["address_id"], as_of=asof_iso(as_of) or resp.get("as_of"))
    codes = reason_codes(resp)
    alts = alternatives_block(resp)
    coordinate = coordinate_block(resp, town_id)
    return {
        "coordinate": coordinate,
        # uncertainty is a statement *about a position*: with no position there is no claim to qualify
        "uncertainty": (uncertainty_block(resp) if coordinate is not None else None),
        "alternatives": alts,
        "reason_codes": codes,
        "decision_ticket": decision_ticket(resp, town_id, task=task, codes=codes, alts=alts),
        "evidence_summary": evidence_summary(resp),
        "task": task,
        "as_of": resp.get("as_of"),
        "computed_at": asof.to_utc_str(asof.now_utc()),
    }


# ── §7 verification tasks ────────────────────────────────────────────────────────────────────────
_CAUSE_POLARITY = {"MOVED_SUSPECTED": "negative", "CONTESTED": "positive"}


def _task_evidence_refs(store, address_id: str, at: str, cause: str | None, cap: int = 10) -> list[str]:
    """The observations that raised the task, read back from the store at the task's own instant.

    For `MOVED_SUSPECTED` those are the negatives (they are what accumulates); for `CONTESTED` the
    positives that disagree. This is a read of the same frozen store the task was raised from, and the
    basis is named in the payload so nothing about it is implicit.
    """
    if store is None or not address_id or not at:
        return []
    want = _CAUSE_POLARITY.get(cause)
    if want is None:
        return []
    rows = store.observations_upto(at, address_id=address_id)
    if not rows:
        return []
    ev = store.evidence_for([r["observation_id"] for r in rows])
    refs = [r["observation_id"] for r in rows if (ev.get(r["observation_id"]) or {}).get("polarity") == want]
    return refs[-cap:]


def task_payload(task: dict, store=None) -> dict:
    cause = task.get("cause")
    kind, label, clears = _NEXT_ACTION.get((_GATE_VERIFY, {
        "MOVED_SUSPECTED": "negatives_accumulated",
        "CONTESTED": "status_contested",
    }.get(cause, "tier_approximate")), ("verification_visit", "Verify before acting.", None))
    refs = _task_evidence_refs(store, task.get("address_id"), task.get("at"), cause)
    from .indexes import get_index
    label_of = ((get_index().addresses.get(task.get("address_id")) or {}).get("address_text")
                or task.get("address_id"))
    return {
        "task_id": task.get("task_id"), "kind": task.get("kind"), "cause": cause,
        "state": task.get("state"), "priority": task.get("priority"),
        "address_label": label_of,
        "town_id": task.get("town_id"), "address_id": task.get("address_id"),
        "place_id": task.get("place_id"), "tier": task.get("tier"), "status": task.get("status"),
        "negatives_independent": task.get("negatives_independent"),
        "radius_m": task.get("radius_m"), "rule_version": task.get("rule_version"),
        "at": task.get("at"),
        "recommended_action": {"kind": kind, "label": label, "clears_when": clears},
        "evidence_refs": refs,
        "evidence_refs_basis": (f"{_CAUSE_POLARITY.get(cause)}_observations_upto_task_at"
                                if cause in _CAUSE_POLARITY else None),
    }


def _latest_tasks(store) -> list[dict]:
    """Latest stored event per task id, flattened exactly as `verify_first_tasks` already flattens it.

    `task_events.kind` is the *state* (`open`); the payload carries the task's own `kind`, `cause`,
    `tier`, `status`, `negatives_independent`, `radius_m` and `rule_version`. The merge below is the
    same merge the existing queue reader performs, so both endpoints describe one task identically.
    """
    latest: dict[str, dict] = {}
    for e in store.task_events():
        payload = e.get("payload") or (json.loads(e["payload_json"]) if e.get("payload_json") else {})
        latest[e["task_id"]] = {**payload, "at": e.get("at"), "state": e.get("kind"),
                                "priority": e.get("priority"),
                                "town_id": e.get("town_id"), "event_id": e.get("event_id")}
    return list(latest.values())


def task_for_address(store, address_id: str, as_of=None) -> dict | None:
    """The open verification task for an address, as known at `as_of` (via the single as-of gate)."""
    rows = [e for e in _latest_tasks(store) if e.get("address_id") == address_id]
    if as_of is not None:
        rows = asof.rows_upto(rows, as_of, ts_field="at")
    for e in rows:
        if e.get("state") == "open":
            return task_payload(e, store)
    return None


def _cursor_key(task: dict) -> tuple:
    return (-float(task.get("priority") or 0.0), task.get("address_id") or "", task.get("task_id") or "")


def _encode_cursor(task: dict) -> str:
    raw = json.dumps([task.get("priority"), task.get("address_id"), task.get("task_id")])
    return base64.urlsafe_b64encode(raw.encode("utf-8")).decode("ascii")


def _decode_cursor(cursor: str) -> tuple:
    try:
        priority, address_id, task_id = json.loads(base64.urlsafe_b64decode(cursor.encode("ascii")))
        return (-float(priority or 0.0), address_id or "", task_id or "")
    except Exception:
        raise ValueError("invalid cursor")


def tasks_list(store, town_id: str | None = None, cause: str | None = None, state: str = "open",
               as_of: str | None = None, limit: int = 100, cursor: str | None = None) -> dict:
    """`GET /v1/tasks` (P0-6): filters, facets and a stable cursor over the stored task events.

    Read-only. Task state transitions are P1 — every row here is whatever state the store last
    recorded, and the queue never pretends to be a workflow engine.
    """
    from .indexes import get_index
    ix = get_index()
    rows = _latest_tasks(store)
    if as_of is not None:
        rows = asof.rows_upto(rows, as_of, ts_field="at")
    out_rows = []
    for e in rows:
        town = e.get("town_id") or ix.town_of(e.get("address_id"))
        if town_id and town != town_id:
            continue
        out_rows.append({**e, "town_id": town})
    rows = out_rows
    rows.sort(key=_cursor_key)
    facets: dict[str, dict] = {"by_cause": {}, "by_state": {}, "by_town": {}}
    for r in rows:
        facets["by_cause"][r.get("cause") or "unknown"] = facets["by_cause"].get(r.get("cause") or "unknown", 0) + 1
        facets["by_state"][r.get("state")] = facets["by_state"].get(r.get("state"), 0) + 1
        facets["by_town"][r.get("town_id")] = facets["by_town"].get(r.get("town_id"), 0) + 1
    # `state` is the task's own lifecycle state (`task_events.kind`); `cause` is why it was raised
    filtered = [r for r in rows if (state in (None, "all") or r.get("state") == state)
                and (cause is None or r.get("cause") == cause)]
    start = 0
    if cursor:
        key = _decode_cursor(cursor)
        start = next((i for i, r in enumerate(filtered) if _cursor_key(r) > key), len(filtered))
    page = filtered[start:start + int(limit)]
    return {
        "as_of": as_of,
        "filters": {"town_id": town_id, "cause": cause, "state": state, "limit": int(limit)},
        "count": len(page),
        "total_matching": len(filtered),
        "items": [task_payload(t, store) for t in page],
        "facets": facets,
        "next_cursor": (_encode_cursor(page[-1]) if page and start + int(limit) < len(filtered) else None),
    }


# ── §6 the authoritative belief read (P0-3) ──────────────────────────────────────────────────────
def belief_payload(store, address_id: str, as_of: str, ix=None) -> dict:
    """`GET /v1/belief/{address_id}?as_of=` — the belief object itself, never a reconstruction.

    The payload under `belief` is exactly what `sutra.belief.compute_belief` returns: this endpoint
    adds the envelope (coordinate space, the observation references it read, the typed reason codes)
    and renames nothing.
    """
    from .belief import compute_belief
    from .indexes import get_index
    ix = ix or get_index()
    if address_id not in ix.addresses:
        raise KeyError(f"unknown address_id: {address_id}")
    when = asof.parse_ts(as_of)
    belief = compute_belief(address_id, when, store, ix=ix)
    obs = store.observations_upto(asof.to_utc_str(when), address_id=address_id)
    ev = store.evidence_for([o["observation_id"] for o in obs]) if obs else {}
    refs = [{"observation_id": o["observation_id"],
             "visit_id": (o["observation_id"][4:] if o["observation_id"].startswith("obs-") else None),
             "observed_at": o.get("observed_at"),
             "polarity": (ev.get(o["observation_id"]) or {}).get("polarity") or o.get("polarity"),
             "weight": (ev.get(o["observation_id"]) or {}).get("weight")} for o in obs]
    town = ix.town_of(address_id)
    radius = belief["radius"] or {}
    flat = {"radius_m": radius.get("radius_m"), "radius_basis": radius.get("basis"),
            "nominal": radius.get("nominal"), "measured_coverage": radius.get("measured_coverage"),
            "n_calibration": radius.get("n_calibration"), "source_stratum": radius.get("source_stratum"),
            "widened": radius.get("widened"), "widen_reason": radius.get("widen_reason"),
            "candidate": belief["candidate"], "tier": belief["tier"], "status": belief["status"]}
    codes = reason_codes({"score_reasons": belief.get("score_reasons"),
                          "reasons": belief.get("reasons"),
                          "widen_reason": radius.get("widen_reason"), "eligibility": None})
    return {
        "address_id": address_id, "town_id": town, "as_of": belief["as_of"],
        "coordinate_space": coordinate_space(town),
        "belief": belief,                      # verbatim, authoritative, never rebuilt here
        "observation_refs": refs,
        "uncertainty": uncertainty_block(flat),
        "evidence_summary": evidence_summary({"support": belief.get("support"),
                                              "widened": radius.get("widened"),
                                              "widen_reason": radius.get("widen_reason")}),
        "reason_codes": codes,
        "versions": VERSIONS,
    }


# ── §5 observations payload (P0-4) ───────────────────────────────────────────────────────────────
def shape_observation(ix, r: dict, e: dict, town_id: str | None = None) -> dict:
    """One observation row as the frontend sees it — the single shaper, used by both feeds.

    A negative carries no coordinate claim: the device position at capture is kept, labelled, and
    never presented as a claim about the address (`negatives_move_coordinate` is false, always).
    """
    polarity = e.get("polarity") or r.get("polarity")
    claim = polarity != "negative"
    oid = r["observation_id"]
    town = town_id or r.get("town_id") or ix.town_of(r.get("address_id"))
    place_id = f"PL-{r.get('address_id')}" if r.get("address_id") else None
    return {
        "observation_id": oid,
        "visit_id": oid[4:] if oid.startswith("obs-") else None,   # storage convention: obs-<visit_id>
        "address_id": r.get("address_id"), "place_id": place_id, "town_id": town,
        "address_label": ((ix.addresses.get(r.get("address_id")) or {}).get("address_text")
                          or r.get("address_id")),
        "kind": r.get("kind"), "observed_at": r.get("observed_at"),
        "captured_at_device": r.get("captured_at_device"),
        "server_received_at": r.get("server_received_at"), "local_seq": r.get("local_seq"),
        "outcome": r.get("outcome"), "polarity": polarity, "coordinate_claim": claim,
        "x": (r.get("x") if claim else None), "y": (r.get("y") if claim else None),
        "captured": {"x": r.get("x"), "y": r.get("y"), "gps_accuracy_m": r.get("gps_accuracy_m"),
                     "note": ("device position at capture — not a coordinate claim for a negative"
                              if not claim else None)},
        "dwell_s": r.get("dwell_s"),
        "evidence": {"weight": e.get("weight"), "polarity": polarity,
                     "evidence_class": e.get("evidence_class"),
                     "reason_codes": e.get("reason_codes") or [],
                     "policy_version": e.get("policy_version")},
        "contributes": ("negative_doubt" if not claim else
                        ("positive_support" if e.get("weight") else "no_weight")),
        "duplicate_claim_of": r.get("duplicate_claim_of"),
        "agent_id": r.get("agent_id"), "device_id": r.get("device_id"),
        "remark": (r.get("remark") or None), "media": r.get("media") or [],
        "policy_version": r.get("policy_version"),
    }


def observations_payload(store, address_id: str, as_of: str, town_id: str | None = None) -> dict:
    """The evidence timeline: storage order is time order, and the as-of gate is the only filter."""
    from .indexes import get_index
    ix = get_index()
    if address_id not in ix.addresses:
        raise KeyError(f"unknown address_id: {address_id}")
    rows = store.observations_upto(as_of, address_id=address_id)
    ev = store.evidence_for([r["observation_id"] for r in rows]) if rows else {}
    out = [shape_observation(ix, r, ev.get(r["observation_id"]) or {}, town_id) for r in rows]
    return {"address_id": address_id, "town_id": town_id or ix.town_of(address_id), "as_of": as_of,
            "coordinate_space": coordinate_space(town_id or ix.town_of(address_id)),
            "count": len(out), "observations": out,
            "negatives_move_coordinate": False}


# ── §7 place history (P0-5) ──────────────────────────────────────────────────────────────────────
def place_history_v1(place_id: str, as_of, store) -> dict:
    """`place_state` + the two things the UI needs to see memory as durable: versions and contradictions.

    Additive: the existing keys (including `contradictions` as a list of address ids) are untouched;
    the v1 objects live beside them under `contradictions_detail`.
    """
    from .memory import place_state
    base = place_state(place_id, as_of, store)
    cut = base["as_of"]
    versions: list[dict] = []
    for member in base["member_address_ids"]:
        for row in asof.rows_upto(store.belief_versions(member), cut, ts_field="as_of"):
            payload = row.get("payload") or {}
            versions.append({
                "address_id": member, "belief_version": row.get("belief_version"),
                "as_of": row.get("as_of"), "tier": row.get("tier"), "status": row.get("status"),
                "candidate_id": row.get("candidate_id"),
                "radius_m": (payload.get("radius") or {}).get("radius_m"),
                "rules_version": row.get("rules_version"),
                "evidence_policy_version": row.get("evidence_policy_version"),
                "computed_at": row.get("computed_at"),
            })
    versions.sort(key=lambda v: (v["as_of"] or "", v["address_id"], v["belief_version"] or 0))

    detail = []
    from .belief import compute_belief
    for member in base["member_address_ids"]:
        if (base["members"].get(member) or {}).get("status") not in ("CONTESTED", "MOVED_SUSPECTED"):
            continue                     # only contradicting members are recomputed — the rest are counts
        try:
            b = compute_belief(member, as_of, store)
        except KeyError:
            continue
        separation = next((float(c.split("=", 1)[1]) for c in b["reasons"]
                           if c.startswith("contested_separation_m=")), None)
        base_radius = uncertainty.radius_for(b["candidate"], "APPROXIMATE", "STABLE", 0, False)["radius_m"] \
            if b["candidate"] else None
        detail.append({
            "address_id": member, "kind": b["status"],
            "separation_m": separation,
            "threshold_m": (round(config.CONTEST_SEPARATION_MULT * base_radius, 1) if base_radius else None),
            "radius_m": (b["radius"] or {}).get("radius_m"),
            "widen_reason": (b["radius"] or {}).get("widen_reason"),
            "negatives_independent": b["support"]["negatives_independent"],
            "tier": b["tier"], "status": b["status"], "belief_version": b["belief_version"],
            "coordinate_unchanged": True,
            "effect": ("radius widened; tier capped" if b["status"] == "MOVED_SUSPECTED"
                       else "competing supports kept"),
        })
    return {**base, "versions": versions, "contradictions_detail": detail,
            "unplaced": base.get("coordinate") is None,
            "versions_note": "stored belief rows only — history is never recomputed into invented versions"}


# ── §10 local metric plane geometry (P0-9) ───────────────────────────────────────────────────────
def geometry_payload(store, address_id: str, as_of: str, town_id: str | None = None,
                     request_purpose: str = "FIELD_NAVIGATION") -> dict:
    """Everything the plane needs, in metres, in one coordinate space. The frontend owns rendering.

    Markers come from the same generator and the same store the decision came from; the radius ring
    belongs to the **authoritative** answer only. Alternatives are markers without rings, because the
    runtime publishes one radius per decision — a per-arm ring would be a claim nobody made.
    """
    from . import candidates as cand_mod
    from .indexes import get_index
    from .resolve import resolve
    ix = get_index()
    if address_id not in ix.addresses:
        raise KeyError(f"unknown address_id: {address_id}")
    town = town_id or ix.town_of(address_id)
    resp = resolve("", None, as_of, request_purpose, store=store, address_id=address_id)
    cands = {c["candidate_id"]: c for c in cand_mod.generate(address_id, as_of, store)}
    winner = resp.get("candidate_id")
    action = (resp.get("eligibility") or {}).get("action")

    points: list[dict] = []
    rings: list[dict] = []
    withheld = None
    obs = store.observations_upto(as_of, address_id=address_id)
    ev = store.evidence_for([o["observation_id"] for o in obs]) if obs else {}
    if action == _GATE_REFUSE or resp.get("candidate") is None:
        # A refused decision publishes no position at all — not the served claim, and not the
        # evidence markers either, because a marker is readable as a position and the gate just
        # refused to give one. The counts stay, so the interface can say what is being withheld.
        withheld = {"reason": ("gate_refuse" if action == _GATE_REFUSE else "no_candidate"),
                    "gate_action": action, "gate_reason": (resp.get("eligibility") or {}).get("reason"),
                    "suppressed": {"candidate_points": len(cands), "observation_points": len(obs),
                                   "rings": 1 if resp.get("candidate") else 0},
                    "note": "a refused or unplaceable decision publishes no usable coordinate"}
        cands = {}
        obs = []
    else:
        # rank order comes from the response; coordinates come from the same generator the response used
        for a in resp.get("arms_considered") or []:
            c = cands.get(a["candidate_id"])
            if not c or c.get("x") is None:
                continue
            points.append({"id": c["candidate_id"], "kind": "candidate", "x": c["x"], "y": c["y"],
                           "source": c["arm"], "granularity": c.get("granularity"),
                           "status": resp.get("tier") if c["candidate_id"] == winner else None,
                           "selected": c["candidate_id"] == winner,
                           "score": a.get("score"), "primary_eligible": a.get("primary_eligible"),
                           "metadata": {"source_ref": c.get("source_ref"), "as_of_valid": c.get("as_of_valid"),
                                        "licence_class": c.get("licence_class")}})
        rings.append({"center_x": resp["candidate"]["x"], "center_y": resp["candidate"]["y"],
                      "radius_m": resp.get("radius_m"), "candidate_id": winner,
                      "basis": resp.get("radius_basis"), "n_calibration": resp.get("n_calibration"),
                      "measured_coverage": resp.get("measured_coverage"),
                      "stratum": resp.get("source_stratum"), "widened": resp.get("widened"),
                      "widen_reason": resp.get("widen_reason"), "authoritative": True})

    for o in obs:
        e = ev.get(o["observation_id"]) or {}
        polarity = e.get("polarity") or o.get("polarity")
        points.append({"id": o["observation_id"], "kind": "observation",
                       "x": (o.get("x") if polarity != "negative" else None),
                       "y": (o.get("y") if polarity != "negative" else None),
                       "source": e.get("evidence_class") or o.get("evidence_class"),
                       "granularity": None, "status": polarity, "selected": False, "score": e.get("weight"),
                       "primary_eligible": None,
                       "metadata": {"observed_at": o.get("observed_at"), "outcome": o.get("outcome"),
                                    "visit_id": (o["observation_id"][4:] if o["observation_id"].startswith("obs-")
                                                 else None),
                                    "captured_x": o.get("x"), "captured_y": o.get("y"),
                                    "coordinate_claim": polarity != "negative"}})

    # device-day point sequences: real captured positions, only where a day carries at least two
    traces: list[dict] = []
    buckets: dict[tuple, list] = {}
    for o in obs:
        if o.get("x") is None or o.get("y") is None:
            continue
        day = (o.get("observed_at") or "")[:10]
        buckets.setdefault((o.get("device_id"), day), []).append(o)
    for (device, day), items in sorted(buckets.items(), key=lambda kv: (str(kv[0][0]), kv[0][1])):
        if len(items) < 2:
            continue
        items.sort(key=lambda o: (o.get("observed_at") or "", o.get("local_seq") or 0))
        traces.append({"trace_id": f"{device or 'unknown'}|{day}", "device_id": device, "day": day,
                       "basis": "device_day_sequence",
                       "points": [{"x": o["x"], "y": o["y"], "t": o.get("observed_at"),
                                   "visit_id": (o["observation_id"][4:] if
                                                o["observation_id"].startswith("obs-") else None)}
                                  for o in items]})

    xs = [p["x"] for p in points if p.get("x") is not None]
    ys = [p["y"] for p in points if p.get("y") is not None]
    pad = max([r["radius_m"] or 0.0 for r in rings] + [150.0])
    extent = ({"x_min": round(min(xs) - pad, 1), "x_max": round(max(xs) + pad, 1),
               "y_min": round(min(ys) - pad, 1), "y_max": round(max(ys) + pad, 1),
               "basis": "bbox_of_returned_points_padded", "pad_m": round(pad, 1)} if xs and ys else None)
    return {
        "address_id": address_id, "town_id": town, "as_of": as_of,
        "coordinate_space": coordinate_space(town),
        "units": "metres",
        "extent": extent, "points": points, "rings": rings, "traces": traces,
        "counts": {"candidates": sum(1 for p in points if p["kind"] == "candidate"),
                   "observations": sum(1 for p in points if p["kind"] == "observation"),
                   "traces": len(traces), "rings": len(rings)},
        "gate": {"action": action, "reason": (resp.get("eligibility") or {}).get("reason")},
        "withheld": withheld,
        "belief_version": resp.get("belief_version"),
        "place_id": resp.get("place_id"),
        "renderer_hint": {"preferred": "svg", "max_objects": 2000,
                          "note": "equal-scale x/y; the frontend owns viewBox and presentation"},
    }


# ── §10b the town plane (P0-9): reference geometry only ─────────────────────────────────────────
def plane_payload(town_id: str, as_of: str | None = None, ix=None) -> dict:
    """`GET /v1/plane/{town_id}` — the town's reference geometry in the local metric plane.

    Contents are exactly what the official tables already hold for this town: locality centroids and
    landmark points, plus the town centroid. **No address-level candidate appears here** — that is the
    address-scoped payload (`GET /v1/geometry/{address_id}`), and keeping the two separate is what
    stops this endpoint from becoming a bulk coordinate dump that no gate approved.

    Deterministic: points are sorted by id, the extent is a bbox over the returned points, and the
    only time field is the echoed `as_of` (the geometry itself is static official data).
    """
    from .indexes import get_index
    ix = ix or get_index()
    if town_id not in ix.towns:
        raise KeyError(f"unknown town_id: {town_id}")

    localities = sorted(({"id": L["locality_id"], "kind": "locality", "name": L["locality_name"],
                          "x": float(L["centroid_x"]), "y": float(L["centroid_y"]),
                          "pincode": L.get("pincode")}
                         for L in ix.localities if L["town_id"] == town_id), key=lambda p: p["id"])
    landmarks = sorted(({"id": p["poi_id"], "kind": "landmark", "name": p.get("name"),
                         "x": float(p["x"]), "y": float(p["y"]), "pincode": None,
                         "landmark_type": p.get("landmark_type")}
                        for p in ix.landmarks if p.get("town_id") == town_id), key=lambda p: p["id"])
    points = sorted(localities + landmarks, key=lambda p: p["id"])
    cx, cy = ix.town_centroids[town_id]
    xs = [p["x"] for p in points] + [cx]
    ys = [p["y"] for p in points] + [cy]
    span = max(max(xs) - min(xs), max(ys) - min(ys))
    pad = round(max(100.0, 0.05 * span), 1)
    n_addr = sum(1 for a, rec in ix.addresses.items() if rec.get("town_id") == town_id)
    return {
        "town_id": town_id,
        "town_name": ix.towns[town_id].get("town_name"),
        "as_of": as_of,
        "coordinate_space": coordinate_space(town_id),
        "units": "metres",
        "town_centroid": {"x": float(cx), "y": float(cy)},
        "points": points,
        "counts": {"localities": len(localities), "landmarks": len(landmarks),
                   "addresses_indexed": n_addr},
        "extent": {"x_min": round(min(xs) - pad, 1), "x_max": round(max(xs) + pad, 1),
                   "y_min": round(min(ys) - pad, 1), "y_max": round(max(ys) + pad, 1),
                   "basis": "bbox_of_returned_points_padded", "pad_m": pad},
        "address_geometry_endpoint": f"/v1/geometry/{{address_id}}?town_id={town_id}",
        "renderer_hint": {"preferred": "svg", "graticule_m": {"minor": 10, "major": 100},
                          "note": "equal-scale x/y; the frontend owns viewBox and presentation"},
    }


# ── capability status (contract §22): what this build actually does ───────────────────────────
# Statuses are a closed vocabulary. They describe *implementation*, never accuracy: no figure from
# the frozen evaluation is served by this API — those live on the Method & Trust page.
CAPABILITY_STATUSES = ("implemented", "designed", "not_implemented", "evaluated_not_adopted",
                       "research_only")
CAPABILITIES = {
    "resolve": "implemented",
    "evidence_ingest": "implemented",
    "belief_read": "implemented",
    "observations_read": "implemented",
    "place_read": "implemented",
    "verification_queue_read": "implemented",
    "plane_geometry": "implemented",
    "alternatives_explanation": "implemented",
    "typed_reason_codes": "implemented",
    "offline_pack_capture_replay": "implemented",
    "task_state_transitions": "implemented",
    "adjudication_write": "implemented",
    "audit_chain_read": "implemented",
    "batch_resolve": "implemented",
    "overview": "implemented",
    "metrics_api": "not_implemented",
    "learned_ranker": "evaluated_not_adopted",
    "model_training": "not_implemented",
    "calibration_learning": "research_only",
    "place_neighbour_arm": "not_implemented",
}
CAPABILITIES_NOTE = ("status describes this build only; no measured figure is served by the API — "
                     "the frozen evaluation is published on the Method & Trust page")


# ── §13 health / runtime status (P0-7) ───────────────────────────────────────────────────────────
def health_payload(store, pack_dir: str | None = None) -> dict:
    """Operational metadata only. Every number here is counted or read — nothing is estimated."""
    from .indexes import get_index
    ix = get_index()
    counts = {t: store.count(t) for t in ("observations", "evidence_scores", "belief_versions",
                                          "task_events", "place_events", "place_members",
                                          "held_observations", "receipts", "ingest_log")}
    meta = store.meta()
    cut = config.MOMENT
    warm = {r[0] for r in store.conn.execute(
        "SELECT DISTINCT address_id FROM observations WHERE observed_at < ?", (cut,))}  # asof-backend
    towns = sorted(ix.towns)
    cold = {}
    for t in towns:
        addrs = [a for a, rec in ix.addresses.items() if rec.get("town_id") == t]
        cold[t] = sum(1 for a in addrs if a not in warm)
    by_cause = {}
    for e in _latest_tasks(store):
        by_cause[e.get("cause") or "unknown"] = by_cause.get(e.get("cause") or "unknown", 0) + 1
    packs = []
    try:
        import os
        d = pack_dir or packs_mod.PACK_DIR
        for fn in sorted(os.listdir(d)):
            if not fn.startswith("pack-") or not fn.endswith(".json"):
                continue
            p = packs_mod.load_pack(os.path.join(d, fn))
            built_for = p.get("built_for_as_of")
            age = None
            if built_for:
                age = round((asof.parse_ts(cut) - asof.parse_ts(built_for)).total_seconds() / 86400.0, 2)
            packs.append({"town_id": p.get("town_id"), "pack_version": p.get("pack_version"),
                          "valid_days": p.get("valid_days"), "valid_until": p.get("valid_until"),
                          "built_for_as_of": built_for, "age_days_at_cut": age,
                          "n_addresses": p.get("n_addresses"), "n_landmarks": len(p.get("landmarks") or []),
                          "n_localities": len(p.get("localities") or []),
                          "contains_truth": bool(p.get("contains_truth")),
                          "contains_evidence": bool(p.get("contains_evidence")),
                          "contains_polygons": bool(p.get("contains_polygons"))})
    except Exception:            # a missing pack directory is not a health failure
        packs = []
    reads = store.counters("s_eval_looks")
    return {
        "ok": True,
        "versions": VERSIONS,
        "rule_version": RULE_VERSION,
        "radius_map_version": RADIUS_MAP_VERSION,
        "store": {**meta, "counts": counts, "attestation": store.attestation()},
        "packs": packs,
        "gauges": {"cold_addresses_by_town": cold, "open_tasks_by_cause": by_cause,
                   "n_addresses_indexed": len(ix.addresses)},
        "indexes": (ix.manifest.get("files") or {}),
        "counters": {"s_eval_looks": reads, "gate_decisions": store.counters("gate_decisions"),
                     "evidence_memory_policy_runs": store.counters("evidence_memory_policy_runs")},
        "offline": {"held_observations": counts["held_observations"], "receipts": counts["receipts"],
                    "ingest_batches": counts["ingest_log"]},
        "s_eval_firewall": {"reads_by_tools_total": reads, "tuning_uses": 0,
                            "note": "the 100 surveyed addresses are never trained or tuned on"},
        "capabilities": dict(CAPABILITIES),
        "capabilities_note": CAPABILITIES_NOTE,
        "as_of_cut": asof_iso(cut),
    }


def asof_iso(value) -> str:
    return asof.to_utc_str(value) if value is not None else None
