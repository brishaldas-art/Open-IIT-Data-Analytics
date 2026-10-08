"""Evidence scoring — the rule-based MVP (P7, contract §5).

An observation becomes an **evidence score**: a weight in [0,1] plus reason codes plus the
independence tuple. There is no binary trust flag anywhere in this module, and no model.

Weight = base(outcome) × dwell × gps · trail × media × timing × agent-baseline × recency, every
factor recorded as a reason code. Recency is stored with the score but applied by the belief engine at
the as-of instant (a weight is a fact about a moment, not about now).

Negatives (`no_such_person`, `address_not_traceable`) score 0.00 with polarity `negative`: they can
never move a coordinate, and accumulation demotes/widens/marks/creates a task (F2.1/D36).
"""
from __future__ import annotations

import uuid

from . import asof, config, dataio, geo
from .version import EVIDENCE_POLICY_VERSION

_REQUIRED = ("kind", "address_id", "outcome", "agent_id")


def normalise_observation(obs: dict, store=None) -> dict:
    """Validate + fill the stored form of an observation. Raises ValueError on invalid input."""
    for f in _REQUIRED:
        if not obs.get(f):
            raise ValueError(f"observation missing required field: {f}")
    outcome = obs["outcome"]
    if outcome not in config.OUTCOME_BASE:
        raise ValueError(f"unknown outcome: {outcome}")
    kind = obs.get("kind", "visit")
    if kind not in ("visit", "adjudication", "ingest"):
        raise ValueError(f"unknown observation kind: {kind}")

    rec = dict(obs)
    rec["observation_id"] = str(obs.get("observation_id") or uuid.uuid4())
    rec["kind"] = kind
    rec["policy_version"] = obs.get("policy_version", EVIDENCE_POLICY_VERSION)
    rec["evidence_class"] = config.OUTCOME_CLASS[outcome]          # policy owns the class, not the caller
    rec["polarity"] = "negative" if outcome in config.NEGATIVE_OUTCOMES else (
        "ambiguous" if config.OUTCOME_CLASS[outcome] == "ambiguous" else "positive")
    rec["media"] = list(obs.get("media") or [])

    observed = obs.get("observed_at") or obs.get("checkin_ts") or obs.get("captured_at_device")
    if not observed:
        raise ValueError("observation missing a timestamp (observed_at / checkin_ts / captured_at_device)")
    rec["observed_at"] = asof.to_utc_str(observed)
    rec["server_received_at"] = asof.to_utc_str(obs.get("server_received_at") or asof.now_utc())
    rec["tz_offset_minutes"] = int(obs.get("tz_offset_minutes", 330))
    if obs.get("checkin"):
        rec["x"] = obs["checkin"].get("x", obs.get("x"))
        rec["y"] = obs["checkin"].get("y", obs.get("y"))
        rec["gps_accuracy_m"] = obs["checkin"].get("gps_accuracy_m", obs.get("gps_accuracy_m"))

    if rec["polarity"] == "negative" and rec.get("x") is not None and obs.get("coordinate_claim"):
        raise ValueError("a negative observation may never carry a coordinate claim (invariant 8)")

    # duplicate claim: the same visit arriving from a second device is linked, never counted twice
    if store is not None:
        rec["duplicate_claim_of"] = _find_duplicate_claim(rec, store)
        rec["state"] = "DUPLICATE_CLAIM" if rec["duplicate_claim_of"] else "STORED"
    return rec


def _find_duplicate_claim(rec: dict, store) -> str | None:
    hashes = {m.get("sha256") for m in rec.get("media", []) if m.get("sha256")}
    if not hashes:
        return None
    for other in store.observations_upto(asof.now_utc(), address_id=rec["address_id"]):
        if other["observation_id"] == rec["observation_id"]:
            continue
        for m in other.get("media", []) or []:
            if m.get("sha256") in hashes:
                return other["observation_id"]
    return None


# ── the scorer ──────────────────────────────────────────────────────────────────────────────────
def score_observation(obs: dict, store=None, dup_hashes: set | None = None) -> dict:
    """Deterministic weight + reason codes + independence tuple for one observation."""
    outcome = obs["outcome"]
    base = float(config.OUTCOME_BASE[outcome])
    reasons: list[str] = [f"outcome:{outcome}"]
    weight = base

    if base == 0.0:
        reasons.append("negative_no_coordinate_claim")
        return {"weight": 0.0, "polarity": "negative", "evidence_class": obs["evidence_class"],
                "reason_codes": reasons, "recency_factor": 0.0,
                "independence_tuple": independence_tuple(obs, store)}

    dwell = obs.get("dwell_s")
    if dwell is not None:
        dwell = float(dwell)
        if dwell < config.DWELL_SHORT_S:
            weight *= 0.50; reasons.append("dwell_short")
        elif dwell < config.DWELL_OK_S:
            weight *= 0.80; reasons.append("dwell_brief")
        if dwell > config.DWELL_IMPLAUSIBLE_S:
            weight *= 0.70; reasons.append("dwell_implausible")

    acc = obs.get("gps_accuracy_m")
    if acc is not None:
        acc = float(acc)
        if acc <= config.GPS_FINE_M:
            reasons.append("gps_fine")
        elif acc <= config.GPS_OK_M:
            weight *= 0.90; reasons.append("gps_moderate")
        elif acc <= config.GPS_COARSE_M:
            weight *= 0.75; reasons.append("gps_coarse")
        else:
            weight *= 0.50; reasons.append("gps_very_coarse")
    else:
        weight *= 0.90; reasons.append("gps_unknown")

    agree = obs.get("trail_agreement_m")
    if agree is not None:
        agree = float(agree)
        if agree <= config.TRAIL_AGREE_M:
            reasons.append("trail_agrees")
        elif agree <= config.TRAIL_LOOSE_M:
            weight *= 0.85; reasons.append("trail_loose")
        else:
            weight *= 0.60; reasons.append("trail_disagreement")

    media = obs.get("media") or []
    if media:
        mine = {m.get("sha256") for m in media if m.get("sha256")}
        dup_cluster = bool(mine & dup_hashes) if dup_hashes is not None else (
            bool(store) and _hash_is_duplicated([m.get("sha256") for m in media], obs, store))
        if dup_cluster:
            weight *= 0.40; reasons.append("duplicate_media_cluster")
        else:
            reasons.append("media_present")
    else:
        weight *= 0.85; reasons.append("no_media")

    hour = asof.parse_ts(obs["observed_at"]).astimezone(asof.IST).hour
    if config.VISIT_HOUR_START <= hour < config.VISIT_HOUR_END:
        reasons.append("business_hours")
    else:
        weight *= 0.70; reasons.append("off_hours")

    if store is not None:
        rate = agent_negative_rate(store, obs.get("agent_id"), as_of=obs["observed_at"])
        if rate is not None and rate > config.AGENT_NEG_RATE_HIGH:
            weight *= 0.90; reasons.append("agent_negative_rate_high")
        elif rate is not None and rate < config.AGENT_NEG_RATE_LOW:
            reasons.append("agent_negative_rate_low")

    if obs.get("duplicate_claim_of"):
        reasons.append("linked_duplicate_claim")
        weight *= 0.0            # stored for audit, never counted as corroboration (F2.2)

    weight = round(max(0.0, min(1.0, weight)), 6)
    return {"weight": weight, "polarity": obs["polarity"], "evidence_class": obs["evidence_class"],
            "reason_codes": sorted(set(reasons)), "recency_factor": 1.0,
            "independence_tuple": independence_tuple(obs, store)}


def _hash_is_duplicated(hashes, obs, store) -> bool:
    mine = {h for h in hashes if h}
    if not mine:
        return False
    n = 0
    for other in store.observations_upto(asof.now_utc()):
        if other["observation_id"] == obs["observation_id"]:
            continue
        for m in other.get("media", []) or []:
            if m.get("sha256") in mine:
                n += 1
                break
    return n > 0


def agent_negative_rate(store, agent_id, as_of, window_days: int = 60) -> float | None:
    """The collector's own windowed negative rate — a weight and a monitoring key, never a ranking
    feature (`PS3_FIELD_EVIDENCE_ARCHITECTURE.md` §3)."""
    if not agent_id or store is None:
        return None
    obs = store.observations_upto(as_of, kinds=("visit", "ingest"))
    seen = [o for o in obs if o.get("agent_id") == agent_id]
    seen = [o for o in seen if asof.age_days(o["observed_at"], as_of) <= window_days]
    if len(seen) < 10:
        return None
    neg = sum(1 for o in seen if o.get("polarity") == "negative")
    return neg / len(seen)


# ── independence (F2.2) ─────────────────────────────────────────────────────────────────────────
def independence_tuple(obs: dict, store=None) -> dict:
    """The six dimensions. `visit`/`collector`/`period`/`media` are properties of the observation;
    `source` and `space` are resolved when a *set* of positives is compared (`promotion_ok`)."""
    return {
        "visit": obs.get("visit_id") or obs.get("observation_id"),
        "collector": obs.get("agent_id"),
        "period": asof.parse_ts(obs["observed_at"]).strftime("%Y-%m"),
        "day": asof.parse_ts(obs["observed_at"]).strftime("%Y-%m-%d"),
        "media": (obs.get("media") or [{}])[0].get("sha256") if obs.get("media") else None,
        "source": obs.get("kind"),
        "space": None,
    }


def promotion_ok(positives: list[dict]) -> tuple[bool, dict]:
    """Promotion rule v2: >= 2 independent confirmations, where independence means at least two
    distinct collectors **or** periods **plus** media independence (F2.2).

    `positives` are evidence rows (each with `independence` and `x`/`y` from the observation).
    """
    strong = [p for p in positives if float(p["weight"]) >= config.W_PROMOTE and not p.get("duplicate_claim_of")]
    collectors = {p["independence"].get("collector") for p in strong}
    periods = {p["independence"].get("period") for p in strong}
    days = {p["independence"].get("day") for p in strong}
    media = [p["independence"].get("media") for p in strong]

    # period independence: >= 2 periods, or >= 7 days apart, or across the 2026-05-15 cut
    cut = asof.parse_ts("2026-05-15T00:00:00Z")
    across_cut = any(asof.parse_ts(p["independence"]["day"]) < cut for p in strong) and \
                 any(asof.parse_ts(p["independence"]["day"]) >= cut for p in strong)
    period_ok = len(periods) >= 2 or across_cut
    if not period_ok and len(days) >= 2:
        ds = sorted(asof.parse_ts(p["independence"]["day"]) for p in strong)
        period_ok = (ds[-1] - ds[0]).days >= config.PERIOD_GAP_DAYS

    media_ok = len(media) >= 2 and len({m for m in media if m}) == len([m for m in media if m]) and \
        all(m is not None for m in media)

    # space: the strong positives must agree — measured as a spread around their median
    spread = None
    if all(p.get("x") is not None for p in strong) and len(strong) >= 2:
        mx, my = geo.median([p["x"] for p in strong]), geo.median([p["y"] for p in strong])
        spread = max(geo.dist(p["x"], p["y"], mx, my) for p in strong)
    space_ok = spread is not None and spread <= config.SPACE_BAND_M

    ok = len(strong) >= 2 and (len(collectors) >= 2 or period_ok) and media_ok
    detail = {
        "n_strong": len(strong), "collectors": sorted(c for c in collectors if c),
        "periods": sorted(periods), "media_distinct": len({m for m in media if m}),
        "period_ok": bool(period_ok), "media_ok": bool(media_ok), "space_ok": bool(space_ok),
        "space_spread_m": round(spread, 1) if spread is not None else None,
        "rule": ">=2 strong positives and (>=2 collectors or period-independent) and distinct media",
    }
    return bool(ok), detail


def positives(evidence_rows: list[dict]) -> list[dict]:
    return [e for e in evidence_rows if e["polarity"] == "positive" and float(e["weight"]) > 0]


def negatives(evidence_rows: list[dict]) -> list[dict]:
    return [e for e in evidence_rows if e["polarity"] == "negative"]


def independent_negatives(evidence_rows: list[dict]) -> list[dict]:
    """Distinct negatives by (collector, period, media) — accumulation must be genuinely independent."""
    seen, out = set(), []
    for e in negatives(evidence_rows):
        key = (e["independence"].get("collector"), e["independence"].get("period"),
               e["independence"].get("media"))
        if key in seen:
            continue
        seen.add(key)
        out.append(e)
    return out


def recency_factor(observed_at, as_of, stratum: str) -> float:
    """Weight decay with age (half-life by stratum). Applied at the as-of instant, never baked in."""
    hl = config.HALF_LIFE_MONTHS.get(stratum, 12.0)
    age_m = asof.age_days(observed_at, as_of) / 30.44
    return round(0.5 ** (age_m / hl), 6) if hl > 0 else 1.0
