"""P0 contract tests — the v1 frontend/backend surface (`SUTRA_FRONTEND_BACKEND_CONTRACT_V1_2026-10-08.md`).

Two stores are used, deliberately:

* **a read-only copy of the shipped store** for every read path. The copy is made with sqlite's backup
  API once per session, so `resolve` may bump its `gate_decisions` counter freely — the shipped store
  and the frozen artefacts are never touched by a test run.
* **throwaway stores** for the write path (receipt enrichment), so ingest is exercised without
  touching the copy.

Every value asserted below is a real value from the frozen runtime at `as_of = 2026-06-01T00:00:00Z`.
No fixture is hand-authored; when a number changes, the assertion is wrong and the change must be
explained, never the other way round.
"""
import os
import shutil
import sqlite3
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from sutra import asof, config, views                                                    # noqa: E402
from sutra.belief import compute_belief                                                   # noqa: E402
from sutra.indexes import get_index                                                        # noqa: E402
from sutra.memory import verify_first_tasks                                                # noqa: E402
from sutra.resolve import resolve                                                          # noqa: E402
from sutra.store import Store, submit_observation                                           # noqa: E402
from sutra.version import RULE_VERSION                                                      # noqa: E402

MOMENT = "2026-06-01T00:00:00Z"          # the frozen moment, verbatim
WARM = "AD003067"                        # CONFIRMED · SERVE · street · 566.9 m
NEGATIVE_CASE = "AD002936"               # APPROXIMATE · MOVED_SUSPECTED · VERIFY_FIRST · 1202.6 m
COLD = "AD000004"                        # no field evidence · frozen_baseline @ locality
NO_CANDIDATE = "AD000006"                # a real record whose town is outside every modelled town
OFFICE = "AD000002"                      # WORK_LIKE by rule → REFUSE under NOTICE_SERVICE

LOST_VOCABULARY = {
    "lower_arm_prior", "coarser_granularity", "no_promotion_credit",
    "single_observation_not_primary_eligible", "memory_not_evidence_derived",
    "locality_name_mismatch", "pin_unknown_penalty", "outside_town_penalty",
    "landmark_ambiguous", "coarse_precision_penalty", "score_margin",
}


# ── fixtures ─────────────────────────────────────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def ix():
    return get_index()


@pytest.fixture(scope="module")
def live(tmp_path_factory):
    """A byte-copy of the shipped store (sqlite backup), so this suite can never write to the real one."""
    src = sqlite3.connect(config.STORE_PATH)
    dst_path = tmp_path_factory.mktemp("contract") / "store_copy.sqlite"
    dst = sqlite3.connect(str(dst_path))
    with dst:
        src.backup(dst)
    src.close()
    dst.close()
    st = Store(str(dst_path))
    yield st
    st.close()


@pytest.fixture()
def scratch(tmp_path):
    """A throwaway store for the one write path under test."""
    return Store(str(tmp_path / "scratch.sqlite"))


def _obs(address_id, agent, when, x, y, *, outcome="met_family", media="m1", dwell=300.0, acc=8.0):
    return {"observation_id": f"obs-{address_id}-{agent}-{when}", "kind": "visit", "address_id": address_id,
            "agent_id": agent, "outcome": outcome,
            "checkin": {"x": x, "y": y, "gps_accuracy_m": acc}, "dwell_s": dwell, "observed_at": when,
            "media": ([{"sha256": media, "kind": "photo"}] if media else [])}


def walk_keys(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield path + "/" + str(k), k, v
            yield from walk_keys(v, path + "/" + str(k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk_keys(v, f"{path}[{i}]")


def has_coordinate(obj) -> bool:
    for _, k, v in walk_keys(obj):
        if k in ("x", "y") and isinstance(v, (int, float)):
            return True
    return False


def decision_fields(resp: dict) -> dict:
    """The response with the two clock fields removed — determinism is defined over `as_of` only."""
    return {k: v for k, v in resp.items() if k not in ("computed_at",)}


# ══ the three canonical resolves ═════════════════════════════════════════════════════════════════
def test_contract_warm_resolve_serves(live):
    r = resolve("", None, MOMENT, "FIELD_NAVIGATION", store=live, address_id=WARM)
    assert (r["tier"], r["status"]) == ("CONFIRMED", "STABLE")
    assert r["eligibility"]["action"] == "SERVE"
    assert r["candidate"]["arm"] == "field_evidence"
    assert r["candidate"]["granularity"] == "street"
    assert r["radius_m"] == 566.9 and r["radius_basis"] == "empirical_p80"
    assert (r["n_calibration"], r["measured_coverage"], r["source_stratum"]) == (24, 0.792, "locality")
    assert r["coordinate"] == {"x": 1390.0, "y": -1818.0, "granularity": "street",
                               "coordinate_space": "sutra_local_metric_plane:T2", "radius_m": 566.9}
    assert r["uncertainty"]["fallback_applied"] is True          # street is withheld under the n-guard
    assert r["uncertainty"]["widened"] is True and r["uncertainty"]["widen_reason"] == "negative_accumulation"
    assert r["decision_ticket"]["headline"] == "Serve this location"
    assert r["decision_ticket"]["next_action"]["kind"] == "none"
    assert r["belief_version"] == 7 and r["town_id"] == "T2"
    assert r["as_of"] == MOMENT and r["computed_at"].endswith("Z")


def test_contract_cold_resolve_is_baseline_locality(live):
    r = resolve("", None, MOMENT, "FIELD_NAVIGATION", store=live, address_id=COLD)
    assert (r["tier"], r["status"]) == ("APPROXIMATE", "STABLE")
    assert r["eligibility"] == {**r["eligibility"], "action": "VERIFY_FIRST", "reason": "tier_approximate"}
    assert r["candidate"]["arm"] == "frozen_baseline" and r["candidate"]["granularity"] == "locality"
    assert r["radius_m"] == 809.8 and r["n_calibration"] == 24
    assert r["support"]["n_observations"] == 0
    assert "cold_start_no_field_evidence" in r["reasons"]
    assert r["coordinate"]["coordinate_space"] == "sutra_local_metric_plane:T2"
    assert r["decision_ticket"]["headline"] == "Answer, but verify first"


def test_contract_verify_first_keeps_the_coordinate_but_the_gate_leads(live):
    r = resolve("", None, MOMENT, "FIELD_NAVIGATION", store=live, address_id=NEGATIVE_CASE)
    assert (r["tier"], r["status"]) == ("APPROXIMATE", "MOVED_SUSPECTED")
    assert r["eligibility"]["action"] == "VERIFY_FIRST" and r["eligibility"]["reason"] == "negatives_accumulated"
    assert r["coordinate"] is not None                            # a best-known location may exist
    assert r["coordinate"]["x"] == 1130.5 and r["radius_m"] == 1202.6
    assert r["decision_ticket"]["gate"]["action"] == "VERIFY_FIRST"
    assert r["decision_ticket"]["next_action"]["kind"] == "verification_visit"
    assert r["task"]["task_id"] == "VF-AD002936-MOVED_SUSPECTED"
    assert r["task"]["state"] == "open" and r["task"]["negatives_independent"] == 2
    assert r["evidence_summary"]["negatives_move_coordinate"] is False


# ══ refusal ═══════════════════════════════════════════════════════════════════════════════════════
def test_contract_refusal_by_purpose_exposes_no_v1_coordinate(live):
    r = resolve("", None, MOMENT, "NOTICE_SERVICE", store=live, address_id=OFFICE)
    assert r["eligibility"]["action"] == "REFUSE" and r["eligibility"]["reason"] == "purpose_work_like"
    assert r["coordinate"] is None and r["uncertainty"] is None
    assert r["decision_ticket"]["refusal"]["coordinate_withheld"] is True
    assert r["decision_ticket"]["refusal"]["kind"] == "purpose_work_like"
    assert r["decision_ticket"]["next_action"]["kind"] == "use_other_purpose"


def test_contract_refusal_without_candidate_has_no_coordinate_anywhere(live):
    r = resolve("", None, MOMENT, "FIELD_NAVIGATION", store=live, address_id=NO_CANDIDATE)
    assert r["candidate"] is None and r["tier"] == "UNPLACEABLE"
    assert r["coordinate"] is None and r["alternatives"] == [] and r["uncertainty"] is None
    assert not has_coordinate({k: v for k, v in r.items() if k != "candidate"}), \
        "no v1 block may introduce an x/y pair on a no-candidate response"
    assert "town_centroid" not in __import__("json").dumps(r)
    assert r["decision_ticket"]["headline"] == "No candidate → no coordinate"


def test_contract_unmatched_text_refuses_without_a_coordinate(live):
    r = resolve("nowhere street that does not exist at all", None, MOMENT, "FIELD_NAVIGATION", store=live)
    assert r["candidate"] is None and r["tier"] == "UNPLACEABLE"
    assert r["coordinate"] is None and not has_coordinate({k: v for k, v in r.items() if k != "candidate"})
    assert r["eligibility"]["action"] in ("VERIFY_FIRST", "REFUSE")


# ══ alternatives + lost reasons ═══════════════════════════════════════════════════════════════════
def test_contract_alternatives_are_the_ranked_losers(live):
    r = resolve("", None, MOMENT, "FIELD_NAVIGATION", store=live, address_id=WARM)
    alts = r["alternatives"]
    assert alts and all(a["candidate_id"] != r["candidate_id"] for a in alts)
    scores = [a["score"] for a in alts]
    assert scores == sorted(scores, reverse=True), "alternatives keep rank order"
    for a in alts:
        assert a["score_margin"] == pytest.approx(round(r["score"] - a["score"], 6))
        assert "score_margin" in " ".join(a["lost_reason"])
        for reason in a["lost_reason"]:
            assert reason.split()[0] in LOST_VOCABULARY, reason
        assert set(a) >= {"candidate_id", "arm", "score", "primary_eligible", "reasons", "lost_reason",
                          "score_margin"}
    # the runner-up here is the memory arm: it loses on the arm prior, and says so
    top = alts[0]
    assert top["arm"] == "memory" and any(x.startswith("lower_arm_prior") for x in top["lost_reason"])


def test_contract_alternatives_explain_coarser_and_unpromoted(live):
    r = resolve("", None, MOMENT, "FIELD_NAVIGATION", store=live, address_id=NEGATIVE_CASE)
    joined = " | ".join(" ".join(a["lost_reason"]) for a in r["alternatives"])
    assert "coarser_granularity" in joined
    assert "no_promotion_credit" in joined
    assert "single_observation_not_primary_eligible" in joined


def test_contract_alternatives_are_deterministic(live):
    a = resolve("", None, MOMENT, "FIELD_NAVIGATION", store=live, address_id=WARM)["alternatives"]
    b = resolve("", None, MOMENT, "FIELD_NAVIGATION", store=live, address_id=WARM)["alternatives"]
    assert a == b


def test_contract_alternatives_never_include_a_refusal_winner(live):
    r = resolve("", None, MOMENT, "FIELD_NAVIGATION", store=live, address_id=NO_CANDIDATE)
    assert r["alternatives"] == [] and r["decision_ticket"]["margin"] is None


# ══ reason codes ══════════════════════════════════════════════════════════════════════════════════
def test_contract_reason_codes_typed_and_additive_to_score(live):
    r = resolve("", None, MOMENT, "FIELD_NAVIGATION", store=live, address_id=WARM)
    codes = r["reason_codes"]
    kinds = {c["kind"] for c in codes}
    assert {"score_term", "support", "widen", "gate"} <= kinds
    terms = [c for c in codes if c["kind"] == "score_term"]
    assert terms and all(c["effect"] is not None for c in terms)
    # the typed terms are the score terms, verbatim and complete
    assert [c["code"] for c in terms] == list(r["score_reasons"])
    assert [c["code"] for c in codes if c["kind"] == "widen"] == [r["widen_reason"]]


# ══ P0-3 belief read ══════════════════════════════════════════════════════════════════════════════
def test_contract_belief_read_is_the_authoritative_object(live):
    out = views.belief_payload(live, WARM, MOMENT)
    b = out["belief"]
    direct = compute_belief(WARM, asof.parse_ts(MOMENT), live)
    assert b == direct, "the endpoint must return the belief function's own object, unchanged"
    assert set(out) >= {"address_id", "town_id", "as_of", "coordinate_space", "belief",
                        "observation_refs", "uncertainty", "reason_codes", "versions"}
    assert out["coordinate_space"] == "sutra_local_metric_plane:T2"
    assert b["belief_version"] == 7 and b["tier"] == "CONFIRMED"
    assert b["computed_from"]["policy"] == "evidence-policy-v3"
    assert len(out["observation_refs"]) == b["support"]["n_observations"] == 6
    assert all(r["observation_id"] and r["polarity"] for r in out["observation_refs"])


def test_contract_belief_read_unknown_address(live):
    with pytest.raises(KeyError):
        views.belief_payload(live, "AD999999", MOMENT)


def test_contract_belief_as_of_is_respected(live):
    early = views.belief_payload(live, WARM, "2026-04-05T00:00:00Z")
    late = views.belief_payload(live, WARM, MOMENT)
    assert early["belief"]["tier"] == "APPROXIMATE" and len(early["observation_refs"]) == 1
    assert late["belief"]["tier"] == "CONFIRMED" and len(late["observation_refs"]) == 6


# ══ P0-4 observations ═════════════════════════════════════════════════════════════════════════════
def test_contract_observations_are_ordered_and_typed(live):
    out = views.observations_payload(live, NEGATIVE_CASE, MOMENT)
    rows = out["observations"]
    assert out["count"] == len(rows) == 6
    assert [r["observed_at"] for r in rows] == sorted(r["observed_at"] for r in rows)
    assert rows[0]["observation_id"] == "obs-VS000244" and rows[0]["visit_id"] == "VS000244"
    for r in rows:
        assert set(r) >= {"observation_id", "visit_id", "address_id", "observed_at", "outcome",
                          "polarity", "coordinate_claim", "captured", "evidence", "contributes"}
        assert r["evidence"]["policy_version"] == "evidence-policy-v3"
        assert r["evidence"]["weight"] is not None


def test_contract_negative_observations_claim_no_coordinate(live):
    out = views.observations_payload(live, NEGATIVE_CASE, MOMENT)
    negs = [r for r in out["observations"] if r["polarity"] == "negative"]
    assert len(negs) == 2
    for r in negs:
        assert r["coordinate_claim"] is False
        assert r["x"] is None and r["y"] is None, "a negative carries no coordinate claim"
        assert r["captured"]["x"] is not None, "…but the captured device position is preserved"
        assert r["contributes"] == "negative_doubt"


def test_contract_observations_never_show_the_future(live):
    early = views.observations_payload(live, NEGATIVE_CASE, "2026-04-10T00:00:00Z")
    assert early["count"] == 1 and early["observations"][0]["observed_at"] < "2026-04-10T00:00:00Z"


# ══ P0-5 place history ════════════════════════════════════════════════════════════════════════════
def test_contract_place_history_versions_and_contradictions(live):
    p = views.place_history_v1("PL-AD002936", asof.parse_ts(MOMENT), live)
    assert p["place_id"] == "PL-AD002936" and p["projection"] is True
    assert p["versions"], "stored belief rows are exposed as versions"
    assert all(v["address_id"] for v in p["versions"])
    vs = [v["belief_version"] for v in p["versions"]]
    assert vs == sorted(vs), "versions come back in stored order"
    assert p["contradictions"] == ["AD002936"], "the legacy id list is preserved"
    d = p["contradictions_detail"][0]
    assert d["kind"] == "MOVED_SUSPECTED" and d["coordinate_unchanged"] is True
    assert d["negatives_independent"] == 2 and d["radius_m"] == 1202.6
    assert p["unplaced"] is False


def test_contract_place_history_is_additive(live):
    from sutra.memory import place_state
    base = place_state("PL-AD003067", asof.parse_ts(MOMENT), live)
    v1 = views.place_history_v1("PL-AD003067", asof.parse_ts(MOMENT), live)
    for k, v in base.items():
        assert v1[k] == v, f"place_state key {k} must be unchanged"
    assert set(v1) - set(base) == {"versions", "contradictions_detail", "unplaced", "versions_note"}


# ══ P0-6 verification queue ═══════════════════════════════════════════════════════════════════════
def test_contract_task_queue_matches_the_legacy_reader(live):
    legacy = verify_first_tasks("T2", 500, live)
    v1 = views.tasks_list(live, town_id="T2", limit=500)
    assert v1["total_matching"] == len(legacy) == 84
    assert [t["task_id"] for t in v1["items"]] == [t["task_id"] for t in legacy]
    assert all(t["state"] == "open" for t in v1["items"])


def test_contract_task_filters_and_facets(live):
    allt = views.tasks_list(live, limit=500)
    assert allt["total_matching"] == 278
    assert allt["facets"]["by_cause"] == {"MOVED_SUSPECTED": 273, "CONTESTED": 5}
    contested = views.tasks_list(live, town_id="T3", cause="CONTESTED", limit=50)
    assert contested["total_matching"] == 5
    assert all(t["cause"] == "CONTESTED" and t["town_id"] == "T3" for t in contested["items"])
    assert all(t["recommended_action"]["kind"] == "adjudicate" for t in contested["items"])


def test_contract_task_cursor_pages_without_gaps_or_repeats(live):
    page1 = views.tasks_list(live, town_id="T2", limit=10)
    page2 = views.tasks_list(live, town_id="T2", limit=10, cursor=page1["next_cursor"])
    ids1 = [t["task_id"] for t in page1["items"]]
    ids2 = [t["task_id"] for t in page2["items"]]
    assert len(ids1) == 10 and len(ids2) == 10 and not set(ids1) & set(ids2)
    everything = views.tasks_list(live, town_id="T2", limit=500)["items"]
    assert ids1 + ids2 == [t["task_id"] for t in everything][:20]


def test_contract_task_rows_carry_action_and_evidence_refs(live):
    row = views.tasks_list(live, town_id="T2", limit=1)["items"][0]
    assert row["task_id"] == "VF-AD000105-MOVED_SUSPECTED"
    assert row["priority"] == 0.8 and row["negatives_independent"] == 2 and row["radius_m"] == 1202.6
    assert row["rule_version"] == RULE_VERSION
    assert row["recommended_action"]["clears_when"]
    assert row["evidence_refs"] and row["evidence_refs_basis"] == "negative_observations_upto_task_at"


def test_contract_task_cursor_rejects_garbage(live):
    with pytest.raises(ValueError):
        views.tasks_list(live, cursor="not-a-cursor")


# ══ P0-7 health ═══════════════════════════════════════════════════════════════════════════════════
_freeze_hash = "ac61cf2e71f77454d91c854c0738b81f11a1b81d1261d2f63145f37df7401989"


def test_contract_health_is_operational_metadata_only(live):
    h = views.health_payload(live)
    assert h["ok"] is True
    assert len(h["versions"]) == 9
    assert h["store"]["counts"]["observations"] == 5578
    assert h["store"]["counts"]["belief_versions"] == 2757
    assert h["gauges"]["cold_addresses_by_town"] == {"T1": 486, "T2": 560, "T3": 554}
    assert h["gauges"]["n_addresses_indexed"] == 3117
    assert len(h["indexes"]) == 10 and all(len(v) == 64 for v in h["indexes"].values())
    # The locked-read ledger is disclosed as an integer and **reading it never advances it**. The
    # absolute value is a property of the store's history, not of this code: a deterministic rebuild
    # (`tools/build_store.py --reset`) restarts the ledger at the rebuild's own single read. The
    # historical record — all ten reads with their timestamps — is persisted in the frozen artefact
    # of record `data/derived/evidence_memory_policy_receipt.json` (`read.timeline`).
    first = h["counters"]["s_eval_looks"]
    assert isinstance(first, int) and first >= 1
    again = views.health_payload(live)["counters"]["s_eval_looks"]
    assert again == first, "reading the ledger must not advance it"
    import json as _json
    with open("data/derived/evidence_memory_policy_receipt.json", encoding="utf-8") as fh:
        receipt = _json.load(fh)
    hist = receipt["s_eval"]["read"]
    assert len(hist["timeline"]) == 10, "the historical read ledger must survive in the receipt"
    assert hist["counter_after"] == 10
    assert receipt["s_eval"]["frozen_reference"]["config_sha256"] == _freeze_hash
    assert h["s_eval_firewall"]["tuning_uses"] == 0
    assert h["packs"] and all(p["contains_truth"] is False and p["contains_evidence"] is False
                              for p in h["packs"])
    assert h["offline"]["receipts"] >= 0 and "held_observations" in h["offline"]


def test_contract_health_has_no_accuracy_claim(live):
    import json
    blob = json.dumps(views.health_payload(live)).lower()
    for banned in ("accuracy", "precision_pct", "confidence_pct", "guarantee", "s_eval_p1"):
        assert banned not in blob


# ══ P0-8 evidence receipt enrichment ══════════════════════════════════════════════════════════════
def test_contract_evidence_receipt_shows_the_delta(scratch):
    r1 = submit_observation(_obs(WARM, "FA101", "2026-05-10T05:00:00Z", 1390.0, -1818.0,
                                 media="c1"), "k1", store=scratch)
    assert r1["belief_before"]["tier"] == "APPROXIMATE" and r1["belief_before"]["radius_m"] == 809.8
    assert r1["belief_after"]["tier"] == "PROBABLE" and r1["belief_after"]["radius_m"] == 674.9
    assert r1["changed"]["changed"] is True
    assert r1["changed"]["fields"]["tier"] == {"before": "APPROXIMATE", "after": "PROBABLE"}
    assert r1["task_delta"]["added"] == []
    assert r1["belief_before"]["candidate_id"] == r1["belief_after"]["candidate_id"], \
        "a positive confirmation narrows the radius; it does not move the place"


def test_contract_two_independent_negatives_doubt_without_moving_the_coordinate(scratch):
    submit_observation(_obs(WARM, "FA101", "2026-05-10T05:00:00Z", 1390.0, -1818.0, media="c1"),
                       "k1", store=scratch)
    first = submit_observation(_obs(WARM, "FA102", "2026-05-12T05:00:00Z", 1390.0, -1818.0,
                                    outcome="address_not_traceable", media="c2", dwell=None),
                               "k2", store=scratch)
    assert first["changed"]["fields"].keys() <= {"radius_m"}, "one negative widens, nothing else"
    before = first["belief_after"]
    second = submit_observation(_obs(WARM, "FA103", "2026-05-20T05:00:00Z", 1390.0, -1818.0,
                                     outcome="address_not_traceable", media="c3", dwell=None),
                                "k3", store=scratch)
    after = second["belief_after"]
    assert after["status"] == "MOVED_SUSPECTED" and after["tier"] == "APPROXIMATE"
    assert after["radius_m"] > before["radius_m"], "doubt widens the radius"
    assert after["candidate_id"] == before["candidate_id"], \
        "and the coordinate does not move — negatives carry no coordinate claim"
    assert second["task_delta"]["added"] == [f"VF-{WARM}-MOVED_SUSPECTED"]


def test_contract_evidence_replay_is_still_idempotent(scratch):
    o = _obs(WARM, "FA101", "2026-05-10T05:00:00Z", 1390.0, -1818.0, media="c1")
    r1 = submit_observation(o, "k1", store=scratch)
    r2 = submit_observation(dict(o, checkin={"x": 1.0, "y": 1.0}), "k1", store=scratch)
    assert r2["replayed"] is True and r2["state"] == "DUPLICATE_OBSERVATION"
    assert r2["belief_version"] == r1["belief_version"]
    assert scratch.count("observations") == 1


# ══ P0-9 local metric plane geometry ══════════════════════════════════════════════════════════════
def test_contract_geometry_is_local_metric(live):
    g = views.geometry_payload(live, WARM, MOMENT)
    assert g["coordinate_space"] == "sutra_local_metric_plane:T2" and g["units"] == "metres"
    assert g["withheld"] is None and g["counts"]["candidates"] >= 3 and g["counts"]["rings"] == 1
    ring = g["rings"][0]
    assert ring["radius_m"] == 566.9 and ring["authoritative"] is True and ring["candidate_id"] == "c-28f5aface67c"
    xs = [p["x"] for p in g["points"] if p["x"] is not None]
    ext = g["extent"]
    assert ext["x_min"] <= min(xs) and max(xs) <= ext["x_max"]
    assert ext["basis"] == "bbox_of_returned_points_padded"
    selected = [p for p in g["points"] if p["selected"]]
    assert len(selected) == 1 and selected[0]["id"] == "c-28f5aface67c"
    assert g["renderer_hint"]["preferred"] == "svg"
    blob = __import__("json").dumps(g).lower()
    for banned in ("latitude", "longitude", "wgs84", "epsg", "mercator", "basemap", "tile"):
        assert banned not in blob


def test_contract_geometry_never_publishes_a_refused_coordinate(live):
    g = views.geometry_payload(live, OFFICE, MOMENT, request_purpose="NOTICE_SERVICE")
    assert g["withheld"]["reason"] == "gate_refuse"
    assert g["rings"] == [] and g["points"] == [] and not has_coordinate(g), \
        "a refused decision publishes no position of any kind"
    assert g["withheld"]["suppressed"]["observation_points"] > 0, "and says what it withheld"
    assert g["extent"] is None
    g2 = views.geometry_payload(live, NO_CANDIDATE, MOMENT)
    assert g2["withheld"]["reason"] in ("no_candidate", "gate_refuse") and g2["points"] == []


def test_contract_geometry_marks_negatives_as_non_claims(live):
    g = views.geometry_payload(live, NEGATIVE_CASE, MOMENT)
    negs = [p for p in g["points"] if p["kind"] == "observation" and p["status"] == "negative"]
    assert negs
    for p in negs:
        assert p["x"] is None and p["y"] is None and p["metadata"]["coordinate_claim"] is False
        assert p["metadata"]["captured_x"] is not None


def test_contract_geometry_traces_are_real_sequences(live):
    g = views.geometry_payload(live, WARM, MOMENT)
    for t in g["traces"]:
        assert len(t["points"]) >= 2 and t["basis"] == "device_day_sequence"
        ts = [p["t"] for p in t["points"]]
        assert ts == sorted(ts)


# ══ determinism, as-of, leakage ═══════════════════════════════════════════════════════════════════
def test_contract_repeated_calls_are_deterministic(live):
    a = resolve("", None, MOMENT, "FIELD_NAVIGATION", store=live, address_id=WARM)
    b = resolve("", None, MOMENT, "FIELD_NAVIGATION", store=live, address_id=WARM)
    assert decision_fields(a) == decision_fields(b)


def test_contract_belief_is_byte_identical_on_recompute(live):
    import json
    a = compute_belief(WARM, asof.parse_ts(MOMENT), live)
    b = compute_belief(WARM, asof.parse_ts(MOMENT), live)
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_contract_no_future_evidence_appears_at_an_earlier_cut(live):
    early = resolve("", None, "2026-04-05T00:00:00Z", "FIELD_NAVIGATION", store=live, address_id=WARM)
    assert early["support"]["n_observations"] == 1
    assert early["as_of"] == "2026-04-05T00:00:00Z"
    assert early["belief_version"] < 7


def test_contract_negative_evidence_cannot_move_the_place(live):
    """The headline invariant, on the exact second the real store flips.

    `obs-VS003098` (`address_not_traceable`, 2026-05-20T05:53:45Z) is the second independent negative
    for `AD002936`. One second either side of it: same candidate, same x/y — and radius 566.9 → 1202.6.
    """
    from sutra.belief import compute_belief
    before = compute_belief(NEGATIVE_CASE, asof.parse_ts("2026-05-20T05:53:45Z"), live)
    after = compute_belief(NEGATIVE_CASE, asof.parse_ts("2026-05-20T05:53:46Z"), live)
    assert (before["tier"], before["status"]) == ("CONFIRMED", "STABLE")
    assert (after["tier"], after["status"]) == ("APPROXIMATE", "MOVED_SUSPECTED")
    assert before["candidate_id"] == after["candidate_id"], "the coordinate never moves on a negative"
    assert before["candidate"]["x"] == after["candidate"]["x"] == 1130.5
    assert (before["radius"]["radius_m"], after["radius"]["radius_m"]) == (566.9, 1202.6)
    assert before["support"]["negatives_independent"] == 1 and after["support"]["negatives_independent"] == 2


# ══ backward compatibility ════════════════════════════════════════════════════════════════════════
def test_contract_flat_fields_survive(live):
    r = resolve("", None, MOMENT, "FIELD_NAVIGATION", store=live, address_id=WARM)
    flat = {"candidate", "candidate_id", "score", "score_reasons", "granularity", "tier", "status",
            "radius_m", "radius_basis", "nominal", "measured_coverage", "n_calibration", "source_stratum",
            "widened", "widen_reason", "reasons", "request_purpose", "address_id", "address_purpose",
            "directions", "is_area_context", "area_context", "eligibility", "stage", "arms_available",
            "arms_considered", "support", "place_id", "belief_version", "resolution", "versions"}
    assert flat <= set(r), f"missing legacy fields: {flat - set(r)}"
    assert r["candidate"]["x"] == 1390.0, "the legacy candidate is untouched"


def test_contract_explain_still_works(live):
    from sutra.resolve import explain
    r = resolve("", None, MOMENT, "FIELD_NAVIGATION", store=live, address_id=WARM)
    line = explain(r)
    assert "field_evidence" in line and "SERVE" in line


# ══ P0-2 review feedback: rank + granularity on alternatives ═════════════════════════════════════
def test_contract_alternatives_carry_rank_and_granularity(live):
    r = resolve("", None, MOMENT, "FIELD_NAVIGATION", store=live, address_id=WARM)
    alts = r["alternatives"]
    ranks = [a["rank"] for a in alts]
    assert ranks == sorted(ranks) and ranks[0] == 2, "the winner is rank 1; alternatives start at 2"
    assert len(set(ranks)) == len(ranks), "ranks are unique"
    scores = [a["score"] for a in alts]
    assert scores == sorted(scores, reverse=True), "rank order is score-descending"
    assert all(a["granularity"] for a in alts), "granularity is read off each candidate's own term"
    assert all(a["granularity"] in ("rooftop", "street", "locality", "town") for a in alts)


def test_contract_alternative_ranks_are_stable_across_calls(live):
    a = resolve("", None, MOMENT, "FIELD_NAVIGATION", store=live, address_id=NEGATIVE_CASE)["alternatives"]
    b = resolve("", None, MOMENT, "FIELD_NAVIGATION", store=live, address_id=NEGATIVE_CASE)["alternatives"]
    assert a == b and [x["rank"] for x in a] == [x["rank"] for x in b]


# ══ P0-9 review feedback: the town plane ═════════════════════════════════════════════════════════
def test_contract_plane_town_reference_geometry(live):
    p = views.plane_payload("T2")
    assert p["coordinate_space"] == "sutra_local_metric_plane:T2" and p["units"] == "metres"
    assert p["town_name"] == "Devgarh Nagar"
    assert p["counts"] == {"localities": 12, "landmarks": 77, "addresses_indexed": 952}
    assert len(p["points"]) == p["counts"]["localities"] + p["counts"]["landmarks"] == 89
    assert [x["id"] for x in p["points"]] == sorted(x["id"] for x in p["points"]), "deterministic by id"
    ext = p["extent"]
    for pt in p["points"] + [p["town_centroid"]]:
        assert ext["x_min"] <= pt["x"] <= ext["x_max"] and ext["y_min"] <= pt["y"] <= ext["y_max"], \
            "the extent must contain every returned point"
    assert ext["basis"] == "bbox_of_returned_points_padded" and ext["pad_m"] > 0
    assert p["renderer_hint"]["graticule_m"] == {"minor": 10, "major": 100}
    assert views.plane_payload("T2") == p, "repeated calls are byte-identical"


def test_contract_plane_is_reference_geometry_only(live):
    """The town plane must never become a bulk address-coordinate dump."""
    p = views.plane_payload("T2")
    for pt in p["points"]:
        assert pt["id"].startswith(("T2-L", "LM")), f"unexpected point id: {pt['id']}"
        assert not pt["id"].startswith(("AD", "c-"))
    blob = __import__("json").dumps(p).lower()
    for banned in ("latitude", "longitude", "wgs84", "epsg", "mercator", "basemap", "tile"):
        assert banned not in blob
    with pytest.raises(KeyError):
        views.plane_payload("T9")


def test_contract_plane_extent_differs_per_town(live):
    extents = {t: views.plane_payload(t)["extent"] for t in ("T1", "T2", "T3")}
    assert len({__import__("json").dumps(e, sort_keys=True) for e in extents.values()}) == 3
    for t, p in ((t, views.plane_payload(t)) for t in ("T1", "T2", "T3")):
        assert p["coordinate_space"] == f"sutra_local_metric_plane:{t}"


# ══ P0-4 review feedback: address_not_traceable is never a relocation signal ═════════════════════
def test_contract_address_not_traceable_is_never_a_relocation_signal(live):
    out = views.observations_payload(live, NEGATIVE_CASE, MOMENT)
    untraceable = [r for r in out["observations"] if r["outcome"] == "address_not_traceable"]
    assert len(untraceable) == 2, "the real record carries two of them"
    for r in untraceable:
        assert r["polarity"] == "negative" and r["coordinate_claim"] is False
        assert r["x"] is None and r["y"] is None
        assert r["evidence"]["weight"] == 0.0, "a negative carries zero evidence weight"
        assert r["contributes"] == "negative_doubt"
        assert r["captured"]["x"] is not None, "the captured position is retained, not claimed"
    # and the decision's coordinate is untouched by them
    r0 = resolve("", None, MOMENT, "FIELD_NAVIGATION", store=live, address_id=NEGATIVE_CASE)
    assert r0["coordinate"] == {"x": 1130.5, "y": 2970.0, "granularity": "rooftop",
                                "coordinate_space": "sutra_local_metric_plane:T2", "radius_m": 1202.6}


# ══ P0-8 review feedback: a visit that changes nothing must say so ═══════════════════════════════
def test_contract_receipt_reports_no_change_when_nothing_changed(scratch):
    submit_observation(_obs(WARM, "FA101", "2026-05-02T09:00:00Z", 1390.0, -1818.0, media="n1"),
                       "k1", store=scratch)
    second = submit_observation(_obs(WARM, "FA102", "2026-05-11T09:00:00Z", 1390.0, -1818.0, media="n2"),
                                "k2", store=scratch)
    assert (second["belief_after"]["tier"], second["belief_after"]["status"]) == ("CONFIRMED", "STABLE")
    assert second["changed"]["changed"] is True, "the second confirmation promotes the place"
    third = submit_observation(_obs(WARM, "FA103", "2026-11-20T09:00:00Z", 1390.0, -1818.0, media="n3"),
                               "k3", store=scratch)
    assert third["changed"]["changed"] is False and third["changed"]["fields"] == {}, \
        "a further confirmation of an already-settled place changes none of the four decision fields"
    assert third["belief_before"]["candidate_id"] == third["belief_after"]["candidate_id"]
    assert (third["belief_before"]["tier"], third["belief_before"]["radius_m"]) == \
           (third["belief_after"]["tier"], third["belief_after"]["radius_m"])
    assert third["task_delta"]["added"] == []


# ══ contract review feedback B: capability status is explicit, and carries no metric ════════════
def test_contract_health_capabilities_are_status_only(live):
    h = views.health_payload(live)
    caps = h["capabilities"]
    assert caps and set(caps.values()) <= set(views.CAPABILITY_STATUSES)
    assert caps["resolve"] == "implemented" and caps["plane_geometry"] == "implemented"
    # P1/P2 landed on 2026-10-08: these four are now implemented, and the map says so.
    assert caps["task_state_transitions"] == "implemented"
    assert caps["adjudication_write"] == "implemented"
    assert caps["audit_chain_read"] == "implemented"
    assert caps["batch_resolve"] == "implemented"
    assert caps["overview"] == "implemented"
    assert caps["learned_ranker"] == "evaluated_not_adopted"
    assert caps["metrics_api"] == "not_implemented", "no accuracy figure is served by the API"
    assert h["capabilities_note"]
    import json
    assert not any(ch.isdigit() for ch in json.dumps(caps)), \
        "capability statuses must not smuggle a number"


def test_contract_health_pack_age_is_computed_not_guessed(live):
    h = views.health_payload(live)
    for p in h["packs"]:
        assert p["built_for_as_of"] and p["age_days_at_cut"] is not None
        assert p["age_days_at_cut"] >= 0.0


# ══ review feedback C: place_neighbour stays disabled ════════════════════════════════════════════
def test_contract_place_neighbour_stays_disabled(live):
    from sutra import candidates as cand_mod
    import json as _json
    frozen = _json.load(open(os.path.join(ROOT, "data", "derived", "final_precision_config.json")))
    assert frozen["frozen_configuration"]["place_neighbour"] == {"c2_gate": "locked", "enabled": False}
    assert config.ENABLE_PLACE_NEIGHBOUR is False
    for aid in sorted(get_index().addresses)[:15]:
        arms = {c["arm"] for c in cand_mod.generate(aid, MOMENT, live)}
        assert "place_neighbour" not in arms, f"{aid} emitted a locked arm"
    with pytest.raises(RuntimeError):
        cand_mod.place_neighbour_candidates(WARM, MOMENT, live, enable=True)


# ══ review feedback 6: runtime knobs cannot silently diverge from the frozen policy ═════════════
def test_contract_memory_policy_runtime_matches_frozen_document(live):
    """emp-v1 is authoritative; the runtime must implement what the frozen document declares.

    The document carries two representations: `memory.emit_rule` (the adopted policy, in prose) and a
    `knobs` map that records the **revert** set (`revert` in the same document: EMIT always,
    ON_DEMAND False). The `knobs` map is therefore not the shipped configuration, and reading it as
    such is exactly the mistake this test exists to prevent.
    """
    import json as _json
    pol = _json.load(open(os.path.join(ROOT, "data", "derived", "final_evidence_memory_policy.json")))
    assert pol["policy_sha256"] == "a110f08962993e3ca6b7151edbc01002029019faa4e583625eb599f8379b2775"
    assert pol["s_eval_used_for_selection"] is False
    # 1. the adopted rule, as the document states it in prose
    assert "evidence_derived_only" in pol["memory"]["emit_rule"]
    assert "pin/address-book" not in pol["memory"]["evidence_derived_definition"]
    assert "NOT memory" in pol["memory"]["evidence_derived_definition"]
    # 2. the runtime implements exactly that
    assert config.MEMORY_EMIT == "evidence_derived_only"
    assert config.MEMORY_ON_DEMAND_BELIEF is True
    # 3. and the behaviour, not just the strings: a pin-derived prior is not emitted as memory
    from sutra import candidates as cand_mod
    cold = views.belief_payload(live, COLD, MOMENT)["belief"]
    assert cold["candidate"]["arm"] == "frozen_baseline", "the control: this prior is a static pin"
    assert cand_mod.memory_candidates(COLD, asof.parse_ts(MOMENT), live) == [], \
        "a prior that re-wraps the vendor pin must not enter the memory arm"
    warm = cand_mod.memory_candidates(WARM, asof.parse_ts(MOMENT), live)
    assert len(warm) == 1 and warm[0]["provenance"]["memory_evidence_derived"] is True, \
        "a field-evidence-derived prior is the only thing memory may emit"
    # 4. the inert third knob is recorded, not silently changed
    assert config.MEMORY_REQUIRES_EVIDENCE_DERIVED is True
    assert pol["knobs"]["MEMORY_REQUIRES_EVIDENCE_DERIVED"] is False, \
        "the frozen arm's tuple differs here; under the emit gate it is inert (both are pinned by test)"


def test_contract_memory_policy_wording_cannot_drift_in_our_docs():
    """No active productisation document may *claim* the revert set as the shipped configuration.

    Describing the defect is allowed — and required — so a line that marks itself as a correction
    (`revert`, `wrong`, `incorrect`, `stale`, `defect`) is not an offender. Only an unqualified claim
    is. This is the guard that caught the stale handoff sentence on 2026-10-08.
    """
    import glob
    correction_markers = ("revert", "wrong", "incorrect", "stale", "defect", "not the shipped")
    offenders = []
    for path in sorted(glob.glob(os.path.join(ROOT, "SUTRA_*.md"))):
        for line in open(path, encoding="utf-8"):
            if "MEMORY_EMIT" not in line:
                continue
            states_always = any(tok in line for tok in ("MEMORY_EMIT: always", "MEMORY_EMIT=\"always\"",
                                                         '"MEMORY_EMIT": "always"'))
            low = line.lower()
            if states_always and not any(m in low for m in correction_markers):
                offenders.append(f"{os.path.basename(path)}: {line.strip()[:110]}")
    assert not offenders, "a doc claims the revert set is shipped: " + " | ".join(offenders)
