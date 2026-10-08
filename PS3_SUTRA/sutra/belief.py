"""The belief engine — Observation → Evidence → Belief → Place state → Projection (P6, contract §6).

Determinism is the whole point. `compute_belief(address_id, as_of, store)` is a pure function of
(store rows with `observed_at < as_of`, the candidate generator at `as_of`, the frozen policy tables).
Nothing in the payload is a wall-clock value: `built_at` is the query's own `as_of`. That is why
re-deriving a belief reproduces it byte-for-byte, and why `Store.append_belief` can refuse a write
that would differ from the stored one.

Frozen rules implemented here:
* promotion needs the F2.2 independence tuple (>= 2 collectors or periods, plus media independence);
* one negative never relocates a coordinate; >= 2 **independent** negatives demote, widen, mark
  MOVED_SUSPECTED/CONTESTED and create a verify-first task (F2.1/D36);
* only positive evidence (promotion-grade) or an adjudication can make a field position primary;
* a place keeps both supports when two strong positives disagree beyond 2 x radius (CONTESTED).
"""
from __future__ import annotations

from . import asof, candidates as cand_mod, config, evidence as ev_mod, geo, ranking, uncertainty
from .version import (EVIDENCE_POLICY_VERSION, RADIUS_MAP_VERSION, RULE_VERSION)

TIERS = ("CONFIRMED", "PROBABLE", "APPROXIMATE", "UNPLACEABLE")
STATUSES = ("STABLE", "CONTESTED", "MOVED_SUSPECTED", "STALE")


def belief_version_for(store, address_id: str, as_of) -> int:
    """A pure function of the store: 1 + the number of observations known at `as_of`."""
    return 1 + len(asof.observations_upto(store, as_of, address_id=address_id))


def belief_instant(store, address_id: str, as_of=None):
    """The canonical instant of a belief: one second after the newest observation **known at `as_of`**.

    Deterministic (a function of the store, not of the clock) **and** strictly after every observation it
    is allowed to see — so a belief computed right after a write includes that write. With `as_of` given
    it is the *prequential* instant for that cut-point (this is what the memory arm reads as its prior).
    `observed_at < as_of` stays the only temporal rule; this helper never bypasses it.
    """
    bound = as_of or asof.now_utc()
    obs = asof.observations_upto(store, bound, address_id=address_id)
    if not obs:
        return bound
    newest = max(asof.parse_ts(o["observed_at"]) for o in obs)
    from datetime import timedelta
    return newest + timedelta(seconds=1)


def compute_belief(address_id: str, as_of, store, *, ix=None, candidates: list[dict] | None = None) -> dict:
    from .indexes import get_index
    from .memory import place_id_for
    ix = ix or get_index()
    addr = ix.addresses.get(address_id)
    if addr is None:
        raise KeyError(f"unknown address_id: {address_id}")

    as_of_iso = asof.to_utc_str(as_of)
    cands = candidates if candidates is not None else cand_mod.generate(address_id, as_of, store)
    feats = ranking.features_matrix(addr, cands, ix)
    ranked = ranking.rank(cands, feats, as_of)
    by_id = {c["candidate_id"]: c for c in cands}

    # ── evidence as of the query instant (never "latest visit") ──────────────────────────────────
    obs = asof.observations_upto(store, as_of, address_id=address_id)
    ev_rows = store.evidence_for([o["observation_id"] for o in obs]) if obs else {}
    joined = []
    for o in obs:
        e = ev_rows.get(o["observation_id"])
        if not e:
            continue
        joined.append({"obs": o, "weight": float(e["weight"]), "polarity": e["polarity"],
                       "evidence_class": e["evidence_class"], "independence": e["independence"],
                       "reasons": e["reason_codes"], "duplicate_claim_of": o.get("duplicate_claim_of"),
                       "x": o.get("x"), "y": o.get("y"), "observed_at": o["observed_at"]})

    positives = [j for j in joined if j["polarity"] == "positive" and j["weight"] >= config.W_MIN
                 and not j["duplicate_claim_of"]]
    strong = [j for j in positives if j["weight"] >= config.W_PROMOTE]
    weak = [j for j in positives if j["weight"] < config.W_PROMOTE]
    negs_all = [j for j in joined if j["polarity"] == "negative"]
    negs_ind = _independent(negs_all)

    # recency applies at the as-of instant (the stored weight is a fact about its own moment)
    stratum_for_decay = (by_id.get(ranked[0]["candidate_id"], {}).get("granularity", "locality")
                         if ranked else "locality")
    for j in positives:
        j["w_eff"] = round(j["weight"] * ev_mod.recency_factor(j["observed_at"], as_of, stratum_for_decay), 6)
    strong_eff = [j for j in positives if j["w_eff"] >= config.W_PROMOTE]
    weak_eff = [j for j in positives if config.W_MIN <= j["w_eff"] < config.W_PROMOTE]

    promo_ok, promo_detail = ev_mod.promotion_ok(strong)   # reports which dimension failed, even at n<2

    # ── primary candidate: ranker over primary-eligible arms only (negatives never touch it) ─────
    eligible = [r for r in ranked if by_id[r["candidate_id"]].get("provenance", {}).get("primary_eligible") is not False]
    if not eligible:
        eligible = ranked
    primary = by_id[eligible[0]["candidate_id"]] if eligible else None
    primary_rank = eligible[0] if eligible else None

    base_radius = None
    if primary is not None:
        base_radius = uncertainty.radius_for(primary, "APPROXIMATE", "STABLE", 0, False)["radius_m"]

    # ── contest: two strong positives that disagree beyond 2 x radius keep BOTH supports ────────
    contested = False
    separation = None
    if len(strong) >= 2 and all(j["x"] is not None for j in strong):
        xs, ys = [j["x"] for j in strong], [j["y"] for j in strong]
        mx, my = geo.median(xs), geo.median(ys)
        spread = max(geo.dist(j["x"], j["y"], mx, my) for j in strong)
        separation = round(spread, 1)
        if base_radius and spread > config.CONTEST_SEPARATION_MULT * base_radius:
            contested = True

    # ── tier ────────────────────────────────────────────────────────────────────────────────────
    tier, tier_reasons = _tier(primary, promo_ok, strong_eff, weak_eff, contested, separation, base_radius)
    if len(negs_ind) >= config.NEG_ACCUMULATION_MIN and tier in ("CONFIRMED", "PROBABLE"):
        tier = "APPROXIMATE"
        tier_reasons.append("negative_accumulation_cap")

    # ── status ──────────────────────────────────────────────────────────────────────────────────
    status = "STABLE"
    stale = False
    if contested:
        status = "CONTESTED"
    elif len(negs_ind) >= config.NEG_ACCUMULATION_MIN:
        status = "MOVED_SUSPECTED"
    else:
        newest = max((j["observed_at"] for j in positives), default=None)
        if newest and asof.age_days(newest, as_of) > 365.0:
            status, stale = "STALE", True

    radius = uncertainty.radius_for(primary, tier, status, len(negs_ind), stale)
    radius["radius_map_version"] = RADIUS_MAP_VERSION

    reasons = list(tier_reasons)
    if len(negs_ind):
        reasons.append(f"negatives_independent={len(negs_ind)}")
    if promo_detail.get("rule"):
        reasons.append("promotion:" + ("ok" if promo_ok else "not_ok"))
    if contested:
        reasons.append(f"contested_separation_m={separation}")

    support = {
        "independent_confirmations": promo_detail.get("n_strong", len(strong)),
        "negatives_independent": len(negs_ind),
        "n_positives": len(positives),
        "n_observations": len(obs),
        "positive_weight_sum": round(sum(j["w_eff"] for j in positives), 6),
        "duplicate_claims": sum(1 for j in joined if j["duplicate_claim_of"]),
    }

    payload = {
        "address_id": address_id,
        "as_of": as_of_iso,          # the instant the belief is *about* (the pure function's argument)
        "belief_version": belief_version_for(store, address_id, as_of),
        "computed_from": {"observations_upto": as_of_iso, "policy": EVIDENCE_POLICY_VERSION,
                          "rule_version": RULE_VERSION, "radius_map_version": RADIUS_MAP_VERSION},
        "place_id": place_id_for(address_id, ix),
        "candidate_id": primary["candidate_id"] if primary else None,
        "candidate": primary,
        "tier": tier,
        "status": status,
        "radius": radius,
        "support": support,
        "score": primary_rank["score"] if primary_rank else None,
        "score_reasons": primary_rank["reasons"] if primary_rank else [],
        "arms_available": sorted({c["arm"] for c in cands}),
        "arms_considered": [{"candidate_id": r["candidate_id"], "arm": by_id[r["candidate_id"]]["arm"],
                             "score": r["score"], "primary_eligible":
                             by_id[r["candidate_id"]].get("provenance", {}).get("primary_eligible") is not False,
                             "reasons": r["reasons"]} for r in ranked],
        "promotion_detail": promo_detail,
        "reasons": sorted(set(reasons)),
    }
    return payload


def _tier(primary, promo_ok, strong_eff, weak_eff, contested, separation, base_radius):
    reasons: list[str] = []
    if primary is None:
        return "UNPLACEABLE", ["no_candidate"]
    if contested:
        return "APPROXIMATE", ["contested_supports"]
    if promo_ok:
        reasons.append(f"field_confirmed_x{max(len(strong_eff), 2)}")
        if primary.get("provenance", {}).get("agreement_arms", 0) > 0:
            reasons.append("cross_arm_agreement")
        return "CONFIRMED", reasons
    if len(strong_eff) >= 1:
        return "PROBABLE", ["field_confirmed_x1"]
    if len(weak_eff) >= 2:
        return "PROBABLE", ["weak_positives_x2"]
    fine = primary.get("granularity") in ("street", "rooftop")
    agree = primary.get("provenance", {}).get("agreement_arms", 0)
    if fine and agree:
        return "PROBABLE", ["fine_pin_with_cross_arm_agreement"]
    if primary["granularity"] == "town":
        return "APPROXIMATE", ["town_anchor_only"]
    return "APPROXIMATE", ["cold_start_no_field_evidence"]


def _independent(negs: list[dict]) -> list[dict]:
    seen, out = set(), []
    for j in negs:
        key = (j["independence"].get("collector"), j["independence"].get("period"), j["independence"].get("media"))
        if key in seen:
            continue
        seen.add(key)
        out.append(j)
    return out


# ── the write path: recompute + persist ─────────────────────────────────────────────────────────
def recompute_belief(address_id: str, store, as_of=None, persist: bool = True, trigger: dict | None = None) -> dict:
    """Recompute the belief at `as_of` (default: the observation's own instant) and persist it.

    The trigger does not influence the payload — it only decides which *task* bookkeeping follows.
    """
    when = as_of
    if when is None:
        when = belief_instant(store, address_id)
    belief = compute_belief(address_id, when, store)
    if persist:
        store.append_belief(address_id, belief, computed_at=asof.to_utc_str(asof.now_utc()))
        if belief["status"] in ("MOVED_SUSPECTED", "CONTESTED"):
            from .memory import ensure_verify_first_task
            ensure_verify_first_task(store, belief)
    return belief
