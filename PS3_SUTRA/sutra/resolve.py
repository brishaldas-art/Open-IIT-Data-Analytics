"""`resolve` — the frozen request path (contract §3, §11).

    resolve(address_text, town_hint, as_of, request_purpose) -> ResolveResponse

Deterministic, no model, no network, no CSV scan: candidates come from the precomputed indexes, the
belief from the append-only store as of `as_of`, the radius from the published radius map, and the
gate from `address_purpose`. A refusal is a decision, not an error — and when there is no candidate
there is **no coordinate** anywhere in the response (D35).
"""
from __future__ import annotations

from . import (asof, config, dataio, directions as dir_mod, eligibility as gate_mod, ranking,
               uncertainty)
from .belief import compute_belief
from .candidates import generate
from .indexes import get_index
from .purpose import validate_request_purpose
from .version import (DIRECTIONS_RULE_VERSION, EVIDENCE_POLICY_VERSION, GATE_RULE_VERSION,
                      PURPOSE_RULE_VERSION, RADIUS_MAP_VERSION, RULE_VERSION, SCHEMA_VERSION)


# generic address words carry no identity: they may never be the *only* reason a locality matches
GENERIC = {"road", "street", "nagar", "layout", "layt", "colony", "cross", "main", "block", "gali",
           "extension", "sector", "ward", "village", "town", "near", "opposite", "behind", "beside",
           "house", "plot", "door", "flat", "floor", "society", "apartment", "east", "west", "north", "south"}
FUZZY_MIN_JACCARD = 0.85      # identifying a *record* needs a strong, unambiguous token match
FUZZY_MIN_MARGIN = 0.10       # ... and a clear margin over the runner-up


def locality_of_pin(pin: str, towns: list[str], ix) -> list[dict]:
    return [L for L in ix.localities if L["town_id"] in towns and str(L.get("pincode") or "") == str(pin)]


def find_address(address_text: str, town_hint: str | None = None, ix=None) -> tuple[str | None, str]:
    """Identify the address record behind a *typed* address; never guess.

    1. exact match on the corpus normalisation (the only thing that can be exact here);
    2. a strong, unambiguous token match against one record — all numbers in the query must be present
       in the record, Jaccard >= 0.85 and a margin over the runner-up;
    3. otherwise `area_context:<locality_id>` when the locality itself is identifiable (pin or a
       distinctive name token), so the caller gets a labelled area, never a fabricated address.

    Returns `(address_id | None, how)`. "how" is echoed into the response for auditability.
    """
    ix = ix or get_index()
    text = dataio.norm_text(address_text)
    if not text:
        return None, "empty_text"
    towns = [town_hint] if town_hint else sorted(ix.towns)
    for t in towns:
        hits = ix.text_index.get((t, text))
        if hits:
            return sorted(hits)[0], "exact_text_match"

    toks = set(dataio.tokens(text))
    nums = {x for x in toks if x.isdigit()}
    pin = dataio.pin_in_text(address_text)

    # 2) strong unambiguous fuzzy match, restricted to the pin when the query carries one
    scored = []
    for t in towns:
        for aid, row in ix.addresses.items():
            if row["town_id"] != t:
                continue
            rt = set(dataio.tokens(row.get("text_norm") or ""))
            if not rt:
                continue
            if nums and not nums <= rt:            # a door/cross number that the record does not carry
                continue
            j = len(toks & rt) / len(toks | rt)
            if j >= FUZZY_MIN_JACCARD:
                scored.append((-j, aid))
    scored.sort()
    if scored and (len(scored) == 1 or -scored[1][0] + FUZZY_MIN_MARGIN <= -scored[0][0]):
        return scored[0][1], "fuzzy_text_match"

    # 3) area context: name the area, do not name an address
    if pin:
        by_pin = locality_of_pin(pin, towns, ix)
        if len(by_pin) == 1:
            return None, f"area_context:{by_pin[0]['locality_id']}"
    hits = []
    for t in towns:
        for L in ix.localities:
            if L["town_id"] != t:
                continue
            distinctive = set(dataio.tokens(L["locality_name"])) - GENERIC
            overlap = distinctive & toks
            if overlap:
                hits.append((-len(overlap), L["locality_id"]))
    hits.sort()
    if hits and (len(hits) == 1 or hits[1][0] != hits[0][0]):
        return None, f"area_context:{hits[0][1]}"
    return None, "no_match"


def area_context_payload(how: str, ix) -> dict | None:
    """The labelled coarse anchor for an unidentified address: area identity only, never a coordinate."""
    if not how.startswith("area_context:"):
        return None
    lid = how.split(":", 1)[1]
    L = next((x for x in ix.localities if x["locality_id"] == lid), None)
    if L is None:
        return None
    return {"locality_id": L["locality_id"], "locality_name": L["locality_name"],
            "town_id": L["town_id"], "pincode": L.get("pincode"), "coordinate": None,
            "note": "coarse area anchor only: no address-level coordinate exists (D35)"}


def resolve(address_text: str, town_hint: str | None = None, as_of=None,
            request_purpose: str = "FIELD_NAVIGATION", *, store=None, ix=None,
            radius_band_m: float | None = None, address_id: str | None = None) -> dict:
    """The frozen entry point. Returns the §11 response object."""
    validate_request_purpose(request_purpose)
    ix = ix or get_index()
    as_of = as_of or asof.now_utc()
    if store is None:
        from .store import Store
        store = Store()

    if address_id is None:
        address_id, how = find_address(address_text, town_hint, ix)
    else:
        how = "address_id_given"
    if address_id is None or address_id not in ix.addresses:
        if store is not None:
            store.bump_counter("gate_decisions", detail="VERIFY_FIRST|unplaceable|no_candidate")
        refusal = {
            "candidate": None, "granularity": None, "tier": "UNPLACEABLE", "status": "UNPLACEABLE",
            "radius_m": None, "radius_basis": None, "nominal": None, "measured_coverage": None,
            "n_calibration": None, "source_stratum": None, "widened": None, "widen_reason": None,
            "reasons": (["no_candidate", "no_match_in_address_book"]
                        + (["area_context_locality_only"] if how.startswith("area_context:") else [])),
            "request_purpose": request_purpose,
            "address_id": None, "address_purpose": {"class": "UNKNOWN", "confidence": "low",
                                                    "basis": ["insufficient_evidence"],
                                                    "model_version": PURPOSE_RULE_VERSION},
            "directions": None, "is_area_context": how.startswith("area_context:"),
            "area_context": area_context_payload(how, ix),
            "eligibility": {"action": "VERIFY_FIRST", "reason": "unplaceable",
                            "rule_version": GATE_RULE_VERSION, "request_purpose": request_purpose},
            "stage": "T1", "arms_available": [], "resolution": how,
            "versions": _versions(),
            "town_id": None, "as_of": asof.to_utc_str(as_of),
        }
        refusal.update(_v1_blocks(refusal, None, store, as_of))
        return refusal

    belief = compute_belief(address_id, as_of, store, ix=ix)
    cand = belief["candidate"]
    addr = ix.addresses[address_id]

    # purpose needs the resolved address; directions need the candidate (advisory only)
    purpose = _purpose(address_id, as_of, store, addr, ix)
    directions = dir_mod.directions_for(addr, cand, ix)
    eligibility = gate_mod.decide(purpose, belief, request_purpose, radius_band_m=radius_band_m)
    if store is not None:
        store.bump_counter("gate_decisions",
                           detail=f"{eligibility['action']}|{eligibility['reason']}|{eligibility['rule_version']}")

    radius = belief["radius"]
    reasons = list(belief["reasons"]) + [f"resolution:{how}"]
    if cand is None:
        reasons.append("no_coordinate_returned")

    out = {
        "candidate": cand,
        "candidate_id": belief["candidate_id"],
        "score": belief["score"], "score_reasons": belief["score_reasons"],
        "granularity": cand["granularity"] if cand else None,
        "tier": belief["tier"], "status": belief["status"],
        "radius_m": radius["radius_m"], "radius_basis": radius["basis"], "nominal": radius["nominal"],
        "measured_coverage": radius["measured_coverage"], "n_calibration": radius["n_calibration"],
        "source_stratum": radius["source_stratum"], "widened": radius["widened"],
        "widen_reason": radius["widen_reason"],
        "reasons": sorted(set(reasons)),
        "request_purpose": request_purpose,
        "address_id": address_id,
        "address_purpose": {k: purpose[k] for k in ("class", "confidence", "basis", "model_version")},
        "directions": directions,
        "is_area_context": bool(cand is None or (cand["granularity"] in ("town",))),
        "area_context": None,
        "eligibility": eligibility,
        "stage": "T1",
        "arms_available": belief["arms_available"],
        "arms_considered": belief["arms_considered"],
        "support": belief["support"],
        "place_id": belief["place_id"],
        "belief_version": belief["belief_version"],
        "resolution": how,
        "versions": _versions(),
        "town_id": ix.town_of(address_id), "as_of": asof.to_utc_str(as_of),
    }
    out.update(_v1_blocks(out, out["town_id"], store, as_of))
    return out


def _v1_blocks(response: dict, town_id: str | None, store, as_of) -> dict:
    """The contract-v1 additive blocks (P0-1). A projection only — see `sutra/views.py`."""
    from . import views
    return views.resolve_blocks(response, town_id, store=store, as_of=as_of)


def _purpose(address_id, as_of, store, addr, ix):
    from . import purpose as purpose_mod
    return purpose_mod.classify(address_id, as_of, store, address=addr, ix=ix)


def _versions() -> dict:
    return {"rule_version": RULE_VERSION, "radius_map_version": RADIUS_MAP_VERSION,
            "evidence_policy_version": EVIDENCE_POLICY_VERSION, "schema_version": SCHEMA_VERSION,
            "gate_rule_version": GATE_RULE_VERSION, "purpose_rule_version": PURPOSE_RULE_VERSION,
            "directions_rule_version": DIRECTIONS_RULE_VERSION}


def explain(response: dict) -> str:
    """One-line human summary — used by the demo and the API's text view."""
    if not response.get("candidate"):
        return (f"no candidate -> no coordinate · {response['eligibility']['action']} "
                f"({response['eligibility']['reason']})")
    c = response["candidate"]
    return (f"{c['arm']} @ {c['granularity']} · {response['tier']}/{response['status']} · "
            f"±{response['radius_m']:.0f} m ({response['radius_basis']}, n={response['n_calibration']}, "
            f"stratum {response['source_stratum']}) · {response['eligibility']['action']} "
            f"({response['eligibility']['reason']})")
