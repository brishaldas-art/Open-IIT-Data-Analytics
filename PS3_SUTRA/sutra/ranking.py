"""Ranking — the frozen interface, with the rule baseline as the shipped implementation (D42, §6.3).

    rank(candidates, features, as_of) -> [{candidate_id, score, reasons}]

The interface never changes: a challenger (logistic, shallow LambdaMART) can be swapped in by
configuration once experiment D says it beats the rule priority beyond the interval. Until then the
rule baseline *is* the product, and every score is inspectable — a sum of named contributions with
reason codes — and deterministic.

At most 15 features (M2). None of them is a T2+/visit-derived value: see `FEATURES`.
"""
from __future__ import annotations

from . import asof, config, dataio, geo

FEATURES = (
    "f_arm_prior", "f_granularity_rank", "f_locality_name_matched", "f_pin_in_text", "f_pin_unknown",
    "f_no_digit", "f_no_separator", "f_outside_town", "f_baseline_stratum", "f_sim_jaccard",
    "f_sim_char3", "f_sim_ratio", "f_n_candidates", "f_agreement_count", "f_dist_to_town_centroid_m",
)  # exactly 15 — M2 caps the feature count

ARM_PRIOR = {
    "field_evidence": 0.62,          # the consolidated median is boosted below
    "memory": 0.55,
    "frozen_baseline": 0.50,
    "official_landmark": 0.45,
    "address_book": 0.42,
    "locality_centroid": 0.38,
    "town_centroid": 0.15,
    "place_neighbour": 0.35,
}
GRANULARITY_RANK = {"rooftop": 1.00, "street": 0.85, "locality": 0.60, "town": 0.25}
COARSE_PRECISION = ("locality", "pincode")


# Levenshtein similarity: one implementation, shared with the preprocessing rings (no dependency).
from .dataio import edit_ratio as _ratio      # noqa: E402


def _jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 0.0
    return len(a & b) / max(1, len(a | b))


def _char3(s: str) -> set:
    s = s.replace(" ", "")
    return {s[i:i + 3] for i in range(max(0, len(s) - 2))}


def features_for(address: dict, candidate: dict, all_candidates: list[dict], ix) -> dict:
    """Feature vector for one candidate — T0/T1 text and geometry only, no visit-derived value."""
    text = address.get("text_norm") or dataio.norm_text(address.get("address_text", ""))
    toks = set(dataio.tokens(text))
    cands_coords = [(c["x"], c["y"]) for c in all_candidates]

    loc_names = [dataio.norm_text(L["locality_name"]) for L in ix.localities
                 if L["town_id"] == address["town_id"]]
    best_loc, best_jac, best_char = None, 0.0, 0.0
    for name in loc_names:
        j = _jaccard(toks, set(dataio.tokens(name)))
        key = (j, name)
        if key > (best_jac, best_loc or ""):
            best_loc, best_jac, best_char = name, j, _jaccard(_char3(text), _char3(name))
    sim_ratio = max((_ratio(text, n) for n in loc_names), default=0.0)

    pin = dataio.pin_in_text(address.get("address_text", ""))
    known_pins = {L.get("pincode") for L in ix.localities if L["town_id"] == address["town_id"]}
    agree = sum(1 for x, y in cands_coords if geo.dist(x, y, candidate["x"], candidate["y"]) <= 150.0) - 1
    tc = ix.town_centroids.get(address["town_id"])

    return {
        "f_arm_prior": ARM_PRIOR.get(candidate["arm"], 0.20),
        "f_granularity_rank": GRANULARITY_RANK.get(candidate["granularity"], 0.25),
        "f_locality_name_matched": int(bool(best_loc and best_jac > 0)),
        "f_pin_in_text": int(pin is not None),
        "f_pin_unknown": int(pin is not None and pin not in known_pins),
        "f_no_digit": int(not any(ch.isdigit() for ch in address.get("address_text", ""))),
        "f_no_separator": int("," not in address.get("address_text", "")),
        "f_outside_town": int(bool(address.get("flag_outside_town") in (True, "True", "true"))),
        "f_baseline_stratum": candidate.get("provenance", {}).get("stratum", candidate["granularity"]),
        "f_sim_jaccard": round(best_jac, 4),
        "f_sim_char3": round(best_char, 4),
        "f_sim_ratio": round(sim_ratio, 4),
        "f_n_candidates": len(all_candidates),
        "f_agreement_count": max(0, agree),
        "f_dist_to_town_centroid_m": round(geo.dist(candidate["x"], candidate["y"], tc[0], tc[1]), 1) if tc else None,
    }


def rank(candidates: list[dict], features: dict, as_of) -> list[dict]:
    """FROZEN INTERFACE (contract §6.3). Rule baseline: an additive, inspectable score.

    `features` maps candidate_id -> feature dict (built by `features_for`).
    """
    out = []
    for c in candidates:
        f = features.get(c["candidate_id"], {})
        prior = ARM_PRIOR.get(c["arm"], 0.20)
        contrib: list[tuple[str, float]] = [(f"arm_prior:{c['arm']}", prior)]
        gran = GRANULARITY_RANK.get(c["granularity"], 0.25)
        contrib.append((f"granularity:{c['granularity']}", 0.12 * gran))
        if c["arm"] == "frozen_baseline":
            strat = c.get("provenance", {}).get("baseline_precision")
            if strat in COARSE_PRECISION:
                contrib.append(("coarse_precision_penalty", -0.06))
            elif strat == "rooftop":
                contrib.append(("fine_precision_bonus", 0.04))
        if c.get("provenance", {}).get("primary_eligible") is True:
            contrib.append(("evidence_promotion_eligible", 0.08))
        prov = c.get("provenance", {})
        if prov.get("ambiguous"):
            contrib.append(("landmark_ambiguous_penalty", -0.08))
        if prov.get("away_from_parsed_relation"):
            contrib.append(("away_from_parsed_relation", -0.05))
        if f.get("f_locality_name_matched"):
            contrib.append(("locality_match", 0.05))
        if f.get("f_pin_in_text") and not f.get("f_pin_unknown"):
            contrib.append(("pin_in_text_known", 0.04))
        if f.get("f_pin_unknown"):
            contrib.append(("pin_unknown_penalty", -0.05))
        if f.get("f_no_digit"):
            contrib.append(("no_house_number", -0.03))
        if f.get("f_outside_town"):
            contrib.append(("outside_town_penalty", -0.20))
        contrib.append(("text_locality_similarity", round(0.05 * f.get("f_sim_jaccard", 0.0), 6)))
        contrib.append(("text_char_similarity", round(0.03 * f.get("f_sim_char3", 0.0), 6)))
        n_agree = f.get("f_agreement_count", 0)
        if n_agree:
            contrib.append((f"arm_agreement_x{n_agree}", round(0.04 * min(n_agree, 3), 6)))
        score = round(sum(v for _, v in contrib), 6)
        out.append({"candidate_id": c["candidate_id"], "score": score,
                    "reasons": [f"{k}={v:+.3f}" for k, v in contrib if abs(v) > 1e-9]})
    if config.SINGLE_TIEBREAK_QUALITY:
        # Three check-ins of the same arm score identically (weight and GPS spread are not additive
        # features), so the shipped tie-break is the hash of the source ref — i.e. arbitrary. Order
        # equal scores by the generator's own deterministic quality order (`arm_rank`: confident and
        # well-measured first). `candidate_id` remains the final tie-break, so the order is total.
        cmap = {c["candidate_id"]: c for c in candidates}
        out.sort(key=lambda r: (-r["score"], cmap[r["candidate_id"]].get("arm_rank", 99),
                                r["candidate_id"]))
    else:
        out.sort(key=lambda r: (-r["score"], r["candidate_id"]))
    return out


def features_matrix(address: dict, candidates: list[dict], ix) -> dict:
    return {c["candidate_id"]: features_for(address, c, candidates, ix) for c in candidates}
