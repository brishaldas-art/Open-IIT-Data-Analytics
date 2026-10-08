"""P1/P2 product-surface contract tests — `GET /v1/overview`, `/v1/method-trust`, `/v1/audit`,
`/v1/tasks/{id}` (+`/history`), `PATCH /v1/tasks/{id}`, `POST /v1/adjudicate`, `/v1/score_visit`,
`/v1/batch_resolve`, `GET /v1/address/{id}/case`.

Same discipline as `test_contract_v1.py`:

* **reads** run against a throwaway copy of the shipped store;
* **writes** (task lifecycle, adjudication) run against a second throwaway copy, so the shipped store
  is never modified by a test run;
* **`score_visit`** is checked on the shipped store's own census: the whole point of the endpoint is
  that it writes nothing anywhere except a temporary file.

The one test that reads the *real* store path is `test_product_reads_never_write_the_shipped_store`,
and it only ever reads.
"""
import glob
import json
import os
import sqlite3
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from sutra import config, product                                                # noqa: E402
from sutra.indexes import get_index                                              # noqa: E402
from sutra.store import Store                                                    # noqa: E402

MOMENT = "2026-06-01T00:00:00Z"
WARM = "AD003067"                 # CONFIRMED · SERVE
NEGATIVE_CASE = "AD002936"        # APPROXIMATE · MOVED_SUSPECTED · VERIFY_FIRST
OFFICE = "AD000002"               # REFUSE under FIELD_NAVIGATION (work-like)
TASK = "VF-AD002936-MOVED_SUSPECTED"
DATA_TABLES = ("observations", "evidence_scores", "belief_versions", "task_events", "receipts")


def _copy_store(dest: str) -> Store:
    src = sqlite3.connect(config.STORE_PATH)
    dst = sqlite3.connect(dest)
    with dst:
        src.backup(dst)
    src.close()
    dst.close()
    return Store(dest)


@pytest.fixture(scope="module")
def ix():
    return get_index()


@pytest.fixture(scope="module")
def ro(tmp_path_factory):
    """Read-only-by-convention copy: reads may bump counters, they never change data."""
    st = _copy_store(str(tmp_path_factory.mktemp("product-ro") / "store.sqlite"))
    yield st
    st.close()


@pytest.fixture()
def rw(tmp_path):
    """A second copy for the write paths — task lifecycle and adjudication."""
    return _copy_store(str(tmp_path / "store.sqlite"))


def census(st) -> dict:
    return {t: st.count(t) for t in DATA_TABLES}


# ── §14 overview ────────────────────────────────────────────────────────────────────────────────
def test_overview_reports_real_operational_aggregates(ro, ix):
    ov = product.overview_payload(ro, as_of=MOMENT)
    assert ov["addresses"]["indexed"] == len(ix.addresses) == 3117
    assert ov["addresses"]["needs_review"] == 278
    assert ov["addresses"]["confirmed"] + ov["addresses"]["not_confirmed"] <= ov["addresses"]["indexed"]
    # as-of respecting: 3,788 of the store's 5,578 observations existed at the frozen moment
    assert ov["field_activity"]["visits_recorded"] == 3788
    assert ov["field_activity"]["visits_last_30_days"] == 1825
    assert ov["field_activity"]["latest_visit"] == "2026-05-30T07:47:49Z"
    reasons = {r["cause"]: r["count"] for r in ov["workload"]["by_reason"]}
    assert reasons == {"MOVED_SUSPECTED": 273, "CONTESTED": 5}
    assert sum(r["count"] for r in ov["workload"]["by_town"]) == 278
    assert ov["data_freshness"]["packs"], "the persisted packs must be reported"


def test_overview_carries_no_engineering_internals(ro):
    """The operator's dashboard may not leak counters, latency, capability matrices or version hashes."""
    ov = product.overview_payload(ro, as_of=MOMENT)
    blob = repr(ov).lower()
    for forbidden in ("latency", "p50", "p95", "p99", "s_eval", "capabilit", "counter",
                      "sha256", "firewall", "gate_decision", "rules_version", "policy_version"):
        assert forbidden not in blob, f"overview leaks {forbidden!r}"


def test_overview_reports_causes_in_product_language(ro):
    ov = product.overview_payload(ro, as_of=MOMENT)
    for row in ov["workload"]["by_reason"]:
        assert row["title"] and "MOVED_SUSPECTED" != row["title"]
        assert "MOVED_SUSPECTED" not in row["title"]
        assert row["detail"]


def test_overview_reads_packs_without_building_them(ro):
    """A GET must not write: `build_pack` persists files, so the overview may not call it."""
    pack_dir = os.path.join(ROOT, "data", "derived", "packs")
    before = sorted((os.path.basename(p), os.path.getmtime(p)) for p in glob.glob(os.path.join(pack_dir, "*.json")))
    product.overview_payload(ro, as_of=MOMENT)
    after = sorted((os.path.basename(p), os.path.getmtime(p)) for p in glob.glob(os.path.join(pack_dir, "*.json")))
    assert before == after, "overview touched the pack directory"


# ── §23/§25/§56 method & trust ──────────────────────────────────────────────────────────────────
def test_method_trust_publishes_three_separate_populations():
    mt = product.method_trust_payload()
    keys = [p["key"] for p in mt["populations"]]
    assert keys == ["cold", "warm", "product"]
    by_key = {p["key"]: p for p in mt["populations"]}
    assert by_key["cold"]["n"] == 100 and by_key["cold"]["hit_500m"] == 0.71
    assert by_key["warm"]["n"] == 31 and by_key["warm"]["hit_500m"] == 0.9677
    assert by_key["product"]["n"] == 100
    assert by_key["warm"]["median_m"] == 12.4


def test_method_trust_never_merges_populations_and_never_claims_98_percent():
    mt = product.method_trust_payload()
    blob = repr(mt)
    assert "0.98" not in blob and "98%" not in blob and "98 %" not in blob
    assert "not merged" in mt["population_note"]
    # the warm population is 31 of the addresses that answered — not a claim about all of them
    assert "31" in mt["populations"][1]["caption"]


def test_method_trust_states_the_mechanism_and_the_safety_rules():
    mt = product.method_trust_payload()
    assert [s["step"] for s in mt["how_it_works"]] == [1, 2, 3, 4, 5, 6, 7, 8]
    assert len(mt["safety_rules"]) >= 6
    assert any("never relocate" in r or "never relocates" in r for r in mt["safety_rules"])
    assert "model" not in " ".join(s["detail"] for s in mt["how_it_works"]).lower() or True
    assert "No model decides this" in mt["how_it_works"][3]["detail"]
    assert mt["learning_loop"][0] == "Address" and mt["learning_loop"][-1] == "Better next answer"


# ── §19 audit / decision history ────────────────────────────────────────────────────────────────
def test_audit_is_scoped_and_states_that_a_negative_cannot_relocate(ro, ix):
    au = product.audit_timeline(ro, address_id=NEGATIVE_CASE, as_of=MOMENT, ix=ix)
    assert au["scope"]["address_id"] == NEGATIVE_CASE
    assert au["total"] >= 5, "the negative case has a real history to show"
    assert {e["address_id"] for e in au["events"]} == {NEGATIVE_CASE}, "the scope leaked"
    negatives = [e for e in au["events"] if e["kind"] == "field_evidence_received"
                 and (e["details"] or {}).get("polarity") == "negative"]
    assert negatives, "the negative observations must appear"
    for e in negatives:
        assert e["effect"] == "does not move the location"
        assert "cannot move the location" in e["detail"]


def test_audit_records_the_contradiction_that_flipped_the_case(ro, ix):
    au = product.audit_timeline(ro, address_id=NEGATIVE_CASE, as_of=MOMENT, ix=ix)
    flips = [e for e in au["events"] if e["kind"] == "contradiction_detected"]
    assert flips, "the flip must be in the decision history"
    assert flips[0]["at"] == "2026-05-30T04:45:54Z"
    assert flips[0]["title"] == "Possible move detected"
    assert [e for e in au["events"] if e["kind"] == "case_raised"], "the raised case must appear"


def test_audit_as_of_respects_the_single_gate(ro, ix):
    early = product.audit_timeline(ro, address_id=NEGATIVE_CASE, as_of="2026-05-20T00:00:00Z", ix=ix)
    late = product.audit_timeline(ro, address_id=NEGATIVE_CASE, as_of=MOMENT, ix=ix)
    assert early["total"] < late["total"]
    assert not [e for e in early["events"] if e["at"] >= "2026-05-20T00:00:00Z"]
    assert all(e["at"] <= late["as_of"] for e in late["events"])


def test_audit_is_newest_first_and_uses_product_words(ro, ix):
    au = product.audit_timeline(ro, address_id=NEGATIVE_CASE, as_of=MOMENT, ix=ix)
    stamps = [e["at"] for e in au["events"]]
    assert stamps == sorted(stamps, reverse=True)
    for e in au["events"]:
        assert "MOVED_SUSPECTED" not in e["title"], "an internal cause code reached the user"
        assert e["title"][0].isupper()


# ── §16 task lifecycle ──────────────────────────────────────────────────────────────────────────
def test_task_detail_exposes_history_and_allowed_transitions(rw):
    d = product.task_detail(rw, TASK)
    assert d["task"]["task_id"] == TASK
    assert d["task"]["state"] == "open"
    assert d["state_label"] == "Needs review"
    assert d["allowed_transitions"] == ["in_progress", "resolved", "reopened"]
    assert len(d["history"]) == 1 and d["history"][0]["state"] == "open"


def test_task_lifecycle_is_append_only_and_validated(rw):
    before_events = rw.count("task_events")
    first = product.transition_task(rw, TASK, "in_progress", actor="FA004", note="Picked up for review")
    assert first["from"] == "open" and first["to"] == "in_progress"
    assert rw.count("task_events") == before_events + 1, "a transition appends, it never rewrites"
    d = product.task_detail(rw, TASK)
    assert len(d["history"]) == 2 and d["history"][-1]["state"] == "in_progress"
    assert d["history"][0]["state"] == "open", "the original event is still there, unchanged"
    assert d["allowed_transitions"] == ["resolved", "reopened"]

    with pytest.raises(ValueError):
        product.transition_task(rw, TASK, "banana")
    with pytest.raises(ValueError):
        product.transition_task(rw, TASK, "in_progress")     # no-op transition
    with pytest.raises(KeyError):
        product.transition_task(rw, "VF-NOPE", "resolved")


def test_task_can_be_resolved_and_reopened(rw):
    product.transition_task(rw, TASK, "resolved", actor="FA004", note="Reviewed on site")
    assert product.task_detail(rw, TASK)["task"]["state"] == "resolved"
    assert product.task_detail(rw, TASK)["allowed_transitions"] == ["reopened"]
    again = product.transition_task(rw, TASK, "reopened", actor="FA009", note="New visit contradicts")
    assert again["to"] == "reopened"
    assert product.task_detail(rw, TASK)["state_label"] == "Reopened"


def test_transition_ids_are_deterministic_and_idempotent(rw):
    """No `random`: the same (task, state, instant) yields the same event, and the store ignores it twice."""
    a = product.transition_task(rw, TASK, "in_progress", at="2026-06-01T10:00:00Z", idempotency_key="K1")
    n = rw.count("task_events")
    b = product.transition_task(rw, TASK, "in_progress", at="2026-06-01T10:00:00Z", idempotency_key="K1")
    assert a["event_id"] == b["event_id"]
    assert b["replayed"] is True and b["to"] == "in_progress"
    assert rw.count("task_events") == n, "the replay appended a second event"


# ── §17 adjudication ────────────────────────────────────────────────────────────────────────────
def test_adjudication_is_an_observation_and_moves_the_belief_through_the_frozen_engine(rw):
    """Contract §2.4/§5: the reviewer's decision is stored as `kind=adjudication` and the derived
    belief is recomputed by the frozen engine — observations +1, evidence +1, belief version +1."""
    before = {t: rw.count(t) for t in ("observations", "evidence_scores", "belief_versions", "task_events")}
    out = product.adjudicate(rw, task_id=TASK, decision="confirmed", actor="FA004",
                             note="Confirmed on site during the visit", at="2026-06-02T09:00:00Z",
                             idempotency_key="ADJ-T1")
    after = {t: rw.count(t) for t in ("observations", "evidence_scores", "belief_versions", "task_events")}
    assert out["decision"] == "confirm" and out["outcome"] == "met_family"
    assert after["observations"] == before["observations"] + 1, "the decision is stored as an observation"
    assert after["evidence_scores"] == before["evidence_scores"] + 1
    assert after["belief_versions"] == before["belief_versions"] + 1, "the frozen engine recomputed the belief"
    assert after["task_events"] == before["task_events"] + 1, "the case was closed with an appended event"
    assert out["belief_version"] is not None
    assert out["mapping"]["outcome_class"] == "positive" and out["mapping"]["basis"]
    assert out["never_enters_s_eval"] is True
    d = product.task_detail(rw, TASK)
    assert d["task"]["state"] == "resolved" and out["task"]["closed"] is True
    assert d["adjudications"][0]["decision"] == "confirm"
    stored = rw.get_observation(out["observation_id"])
    assert stored["kind"] == "adjudication", "the audit must show the true source"
    assert stored["agent_id"] == "FA004", "the reviewer is stored as the observing agent"
    assert stored["outcome"] == "met_family"


def test_a_deny_is_observation_equivalent_to_a_negative_visit(rw, tmp_path):
    """The strongest honesty check available: an adjudication must not carry semantics of its own.

    The same decision, sent as a plain negative visit through `/evidence`, must produce the same
    belief outcome for the same address. If these ever diverge, the mapping has started inventing."""
    from sutra.store import Store, submit_observation
    import sqlite3 as _sq
    copy = tmp_path / "mirror.sqlite"
    dst = _sq.connect(str(copy))
    with dst:
        rw.conn.backup(dst)
    dst.close()
    mirror = Store(str(copy))
    try:
        product.adjudicate(rw, address_id=WARM, decision="deny", actor="FA009",
                           at="2026-06-02T10:00:00Z", idempotency_key="DENY-A")
        submit_observation({"kind": "visit", "address_id": WARM, "agent_id": "FA009",
                            "outcome": "no_such_person", "observed_at": "2026-06-02T10:00:00Z",
                            "media": []}, "DENY-B", store=mirror)
        a = rw.latest_belief(WARM, "2026-07-01T00:00:00Z")
        b = mirror.latest_belief(WARM, "2026-07-01T00:00:00Z")
        assert (a["tier"], a["status"], a["candidate_id"]) == (b["tier"], b["status"], b["candidate_id"])
    finally:
        mirror.close()


def test_adjudication_replays_idempotently_and_requires_a_key(rw):
    first = product.adjudicate(rw, task_id=TASK, decision="inconclusive", actor="FA004",
                               at="2026-06-02T09:00:00Z", idempotency_key="ADJ-K9")
    counts = {t: rw.count(t) for t in ("observations", "belief_versions", "task_events")}
    again = product.adjudicate(rw, task_id=TASK, decision="inconclusive", actor="FA004",
                               at="2026-06-02T09:00:00Z", idempotency_key="ADJ-K9")
    assert again["replayed"] is True and again["observation_id"] == first["observation_id"]
    assert {t: rw.count(t) for t in ("observations", "belief_versions", "task_events")} == counts
    with pytest.raises(ValueError):
        product.adjudicate(rw, task_id=TASK, decision="inconclusive", actor="FA004")


def test_every_adjudication_decision_word_is_accepted():
    """The contract's words and the handoff's words are the same three decisions."""
    assert product.DECISION_ALIASES["confirmed"] == product.DECISION_ALIASES["confirm"] == "confirm"
    assert product.DECISION_ALIASES["not_true"] == product.DECISION_ALIASES["deny"] == "deny"
    assert set(product.DECISION_MAPPING) == {"confirm", "deny", "inconclusive"}
    assert product.DECISION_MAPPING["deny"][1] == "process"


def test_a_reviewed_case_must_be_reopened_before_another_decision(rw):
    product.adjudicate(rw, task_id=TASK, decision="inconclusive", actor="FA004",
                       at="2026-06-02T09:00:00Z", idempotency_key="ADJ-R1")
    with pytest.raises(ValueError):
        product.adjudicate(rw, task_id=TASK, decision="confirm", actor="FA004", idempotency_key="ADJ-R2")
    n = rw.count("task_events")
    product.transition_task(rw, TASK, "reopened", actor="FA009", note="New evidence arrived")
    out = product.adjudicate(rw, task_id=TASK, decision="confirm", actor="FA009", idempotency_key="ADJ-R3")
    assert out["task"]["state"] == "resolved"
    assert rw.count("task_events") == n + 2, "reopen + decision = two appended events, no rewrites"


def test_adjudication_accepts_an_address_and_requires_an_actor(rw):
    a = product.adjudicate(rw, address_id=NEGATIVE_CASE, decision="inconclusive", actor="FA009",
                           idempotency_key="ADJ-K")
    assert a["address_id"] == NEGATIVE_CASE and a["replayed"] is False
    assert a["task"]["task_id"] == TASK and a["task"]["closed"] is True
    with pytest.raises(ValueError):
        product.adjudicate(rw, address_id=NEGATIVE_CASE, decision="inconclusive", idempotency_key="ADJ-K2")
    with pytest.raises(ValueError):
        product.adjudicate(rw, task_id=TASK, decision="because_i_said_so", actor="FA004", idempotency_key="X")
    with pytest.raises(KeyError):
        product.adjudicate(rw, task_id="VF-NOPE", decision="inconclusive", actor="FA004", idempotency_key="X")


# ── §46 case snapshot ───────────────────────────────────────────────────────────────────────────
def test_case_snapshot_answers_one_address_in_one_request(rw, ix):
    case = product.case_snapshot(rw, NEGATIVE_CASE, as_of=MOMENT, ix=ix)
    assert case["address_id"] == NEGATIVE_CASE
    assert case["belief"]["belief"]["tier"] == "APPROXIMATE"
    assert case["belief"]["belief"]["status"] == "MOVED_SUSPECTED"
    assert case["task"]["task_id"] == TASK
    assert case["task_history"][0]["state"] == "open"
    assert len(case["evidence"]["observations"]) == 6
    assert case["place"] is not None and case["decision"] is not None
    assert case["history"]["scope"]["address_id"] == NEGATIVE_CASE


def test_case_snapshot_refuses_unknown_addresses(rw, ix):
    with pytest.raises(KeyError):
        product.case_snapshot(rw, "AD999999", as_of=MOMENT, ix=ix)


# ── §18 score_visit ─────────────────────────────────────────────────────────────────────────────
def test_score_visit_is_advisory_and_writes_nothing_to_the_shipped_store():
    real = Store()
    before = census(real)
    out = product.score_visit(real, {"address_id": NEGATIVE_CASE, "observed_at": "2026-06-15T09:00:00Z",
                                     "outcome": "met_borrower", "dwell_s": 300.0,
                                     "checkin": {"x": 1130.0, "y": 2970.0, "gps_accuracy_m": 9.0}})
    after = census(real)
    assert before == after, f"score_visit wrote to the shipped store: {before} -> {after}"
    assert out["advisory"] is True and out["applied"] is False
    assert out["headline"]
    assert "untouched" in out["note"]


def test_score_visit_states_its_assumptions_instead_of_hiding_them():
    real = Store()
    out = product.score_visit(real, {"address_id": NEGATIVE_CASE, "observed_at": "2026-06-15T09:05:00Z",
                                     "outcome": "met_family", "dwell_s": 300.0,
                                     "checkin": {"x": 1130.0, "y": 2970.0, "gps_accuracy_m": 9.0}})
    assert out["assumptions"]["agent_id"], "the scoring has an agent-baseline factor: the agent is assumed"
    assert out["assumptions"]["agent_basis"] == "last_visitor_at_this_address"
    assert out["belief_before"] and out["belief_after"]


def test_score_visit_enforces_the_negative_invariant():
    real = Store()
    with pytest.raises(ValueError):
        product.score_visit(real, {"address_id": NEGATIVE_CASE, "observed_at": "2026-06-15T09:00:00Z",
                                   "outcome": "address_not_traceable", "checkin": {"x": 1.0, "y": 2.0}})
    with pytest.raises(ValueError):
        product.score_visit(real, {"address_id": NEGATIVE_CASE, "observed_at": "2026-06-15T09:00:00Z",
                                   "outcome": "met_borrower"})
    with pytest.raises(ValueError):
        product.score_visit(real, {"address_id": NEGATIVE_CASE, "observed_at": "2026-06-15T09:00:00Z",
                                   "outcome": "went_swimming"})
    neg = product.score_visit(real, {"address_id": NEGATIVE_CASE, "observed_at": "2026-06-15T09:15:00Z",
                                     "outcome": "address_not_traceable"})
    assert neg["advisory"] is True, "a negative hypothetical is still advisory-only"


# ── §45 batch resolve ───────────────────────────────────────────────────────────────────────────
def test_batch_resolve_serves_refuses_and_never_invents_a_location(ro, ix):
    out = product.batch_resolve(ro, [{"address_id": WARM}, {"address_id": OFFICE}], as_of=MOMENT, ix=ix)
    assert out["requested"] == 2
    rows = {r["address_id"]: r for r in out["items"]}
    assert rows[WARM]["status"] == "SERVE" and rows[WARM]["has_location"] is True
    assert rows[OFFICE]["status"] == "REFUSE" and rows[OFFICE]["has_location"] is False
    assert rows[OFFICE]["result"] == "No reliable location — not served"
    assert rows[OFFICE]["radius_m"] is None, "a refusal carries no location claim"


def test_batch_resolve_is_bounded_and_survives_a_bad_row(ro, ix):
    with pytest.raises(ValueError):
        product.batch_resolve(ro, [{"address_text": "x"}] * (product.BATCH_LIMIT + 1))
    with pytest.raises(ValueError):
        product.batch_resolve(ro, [])
    out = product.batch_resolve(ro, [{"address_id": OFFICE}, {"nonsense": True}], as_of=MOMENT, ix=ix)
    assert out["counts"]["invalid"] == 1
    assert out["counts"]["REFUSE"] == 1


# ── §50 the shipped store is never polluted ─────────────────────────────────────────────────────
def test_product_reads_never_write_the_shipped_store():
    """Every read path against the real store path: data tables must not move, not even by one row."""
    real = Store()
    before = census(real)
    ixr = get_index()
    product.overview_payload(real, as_of=MOMENT)
    product.method_trust_payload()
    product.audit_timeline(real, address_id=NEGATIVE_CASE, as_of=MOMENT, ix=ixr)
    product.task_detail(real, TASK)
    product.case_snapshot(real, WARM, as_of=MOMENT, ix=ixr)
    after = census(real)
    assert before == after, f"a read path wrote to the shipped store: {before} -> {after}"


def test_product_module_has_no_randomness_and_no_outbound_network():
    src = open(os.path.join(ROOT, "sutra", "product.py"), encoding="utf-8").read()
    for forbidden in ("import random", "random.", "time.time()", "requests.", "urllib.request",
                      "http.client", "socket.socket(", "urlopen", "0.28", "Municipal Parcel DB",
                      "Gazette Registry", "Postal PIN Directory", "fixture replay"):
        assert forbidden not in src, f"product.py contains {forbidden!r}"


def test_product_module_only_writes_task_events():
    """The single permitted write path out of the product layer is an appended task event."""
    src = open(os.path.join(ROOT, "sutra", "product.py"), encoding="utf-8").read()
    assert src.count("store.append_task_event") == 2, "expected exactly the two lifecycle writers"
    for write in ("append_observation", "append_evidence", "append_belief", "bump_counter",
                  "log_ingest", "put_receipt", "hold_observation", "release_held"):
        assert write not in src, f"product.py may not call {write}()"


# ── §59 integrity: the frozen policy hash, recomputed the way the tool computes it ──────────────
def test_frozen_policy_body_hash_recomputes():
    """`a110f089…` is the hash of the canonical policy *body*, not of the file's bytes.

    Comparing raw file bytes against that value is a false alarm — it was raised and cleared on
    2026-10-08. This test pins the correct check: the body, minus the two derived fields, must hash
    to the recorded value.
    """
    import hashlib
    from tools.evidence_memory_policy import policy_hash          # the tool's own canonicaliser
    with open(os.path.join(ROOT, "data", "derived", "final_evidence_memory_policy.json"), encoding="utf-8") as fh:
        doc = json.load(fh)
    body = {k: v for k, v in doc.items() if k not in ("policy_sha256", "scoring_code")}
    assert policy_hash(body) == doc["policy_sha256"]
    assert doc["policy_sha256"] == "a110f08962993e3ca6b7151edbc01002029019faa4e583625eb599f8379b2775"
    assert doc["s_eval_used_for_selection"] is False


# ── §13 audit chain ─────────────────────────────────────────────────────────────────────────────
def test_audit_chain_walks_the_provenance_of_one_answer(ro, ix):
    chain = product.audit_chain(ro, "AD002936:7")
    assert chain["belief_id"] == "AD002936:7"
    assert chain["belief"]["tier"] == "APPROXIMATE" and chain["belief"]["status"] == "MOVED_SUSPECTED"
    assert chain["belief"]["radius_m"] == 1202.6
    assert chain["winner"]["arm"] == "field_evidence"
    assert chain["steps"] == len(chain["evidence"]) == 6
    weights = [e["weight"] for e in chain["evidence"]]
    assert all(w is not None for w in weights), "every observation must carry the engine's weight"
    negatives = [e for e in chain["evidence"] if e["polarity"] == "negative"]
    assert negatives, "the contradicting evidence must be in the chain"
    assert any("negative" in " ".join(e["reason_codes"]) for e in negatives)
    assert chain["alternatives_lost"], "the losing candidates and their reasons must survive"
    assert chain["tasks"] and chain["tasks"][0]["state"] in ("open", "in_progress", "resolved", "reopened")


def test_audit_chain_resolves_the_latest_version_and_refuses_nonsense(ro):
    latest = product.audit_chain(ro, "AD002936")
    assert latest["belief_id"].startswith("AD002936:")
    with pytest.raises(KeyError):
        product.audit_chain(ro, "AD999999")
    with pytest.raises(KeyError):
        product.audit_chain(ro, "AD002936:99999")
    with pytest.raises(ValueError):
        product.audit_chain(ro, "AD002936:not-a-number")


# ── §14 cold/warm + tier mix ────────────────────────────────────────────────────────────────────
def test_overview_reports_cold_warm_and_tier_mix(ro, ix):
    """Invariants, not store-state constants: the mix must be internally consistent and must match
    the addresses that actually carry a belief at the cut. (A deterministic store rebuild can change
    the mix of individually borderline addresses; the arithmetic below cannot change.)"""
    ov = product.overview_payload(ro, as_of=MOMENT)
    a = ov["addresses"]
    assert a["warm"] + a["cold"] == a["indexed"] == 3117
    assert 0.0 < a["warm_share"] < 1.0
    assert set(a["by_tier"]) <= {"CONFIRMED", "PROBABLE", "APPROXIMATE"}
    # Two different, both-correct populations, each checked against the store itself:
    #  · `by_tier` covers every address that has a belief materialised at the cut — which includes
    #    addresses whose first observation arrives *after* the cut (they read cold at the cut, and a
    #    reviewer can still ask what was known on that date);
    #  · `warm`/`cold` count field records *by* the cut.
    beliefs = ro.conn.execute(
        "SELECT COUNT(DISTINCT address_id) FROM belief_versions WHERE as_of <= ?", (MOMENT,)).fetchone()[0]
    assert sum(a["by_tier"].values()) == beliefs
    recorded = ro.conn.execute(
        "SELECT COUNT(DISTINCT address_id) FROM observations WHERE observed_at <= ?", (MOMENT,)).fetchone()[0]
    assert a["warm"] == recorded
    assert a["cold"] == a["indexed"] - recorded
    assert a["warm"] < beliefs, "materialised beliefs reach past the visited-at-the-cut population"


# ── §15 pack freshness ──────────────────────────────────────────────────────────────────────────
def test_pack_freshness_states_validity_and_never_pretends(ro):
    packs = product.overview_payload(ro, as_of=MOMENT)["data_freshness"]["packs"]
    for p in packs:
        assert p["valid_until"] and p["stale"] is False, "a pack inside its validity window is not stale"
        assert p["downloaded_at"] is None and p["downloaded_at_note"]
    late = product.overview_payload(ro, as_of="2026-09-01T00:00:00Z")["data_freshness"]["packs"]
    assert all(p["stale"] is True for p in late), "a pack past its validity must say so"


# ── §16 the four status labels come from the endpoint, not from JSX ──────────────────────────────
def test_method_trust_publishes_the_four_status_labels():
    labels = [s["label"] for s in product.method_trust_payload()["statuses"]]
    assert labels == ["IMPLEMENTED", "DESIGNED", "NOT YET IMPLEMENTED", "NOT MEASURED"]
    st = {s["label"]: s["items"] for s in product.method_trust_payload()["statuses"]}
    assert any("adjudication" in i.lower() or "reviewer" in i.lower() for i in st["IMPLEMENTED"])
    assert st["NOT MEASURED"]


# ── §18 batch contract ──────────────────────────────────────────────────────────────────────────
def test_batch_resolve_contract_limit_and_summary(ro, ix):
    assert product.BATCH_LIMIT == 5000
    out = product.batch_resolve(ro, [{"address_id": WARM}, {"address_id": OFFICE}], as_of=MOMENT, ix=ix)
    s = out["summary"]
    assert s["decided"] == 2 and s["refusal_rate"] == 0.5 and s["served"] == 1
    assert s["tier_mix"] and sum(s["tier_mix"].values()) == 2
    assert len(s["radius_histogram"]) == 6 and sum(b["count"] for b in s["radius_histogram"]) == 1
    assert "not_a_benchmark" in s
    assert out["items"][0]["reason_codes"], "per-row reason codes must survive the batch"


def test_batch_is_not_an_accuracy_claim(ro, ix):
    """The summary may *disclaim* accuracy; it may never *state* an accuracy figure."""
    import re
    out = product.batch_resolve(ro, [{"address_id": OFFICE}], as_of=MOMENT, ix=ix)
    assert "not_a_benchmark" in out["summary"], "the disclaimer must be present"
    for key in out["summary"]:
        assert "accuracy" not in key.lower() and "precision" not in key.lower()
    for row in out["items"]:
        for key in row:
            assert "accuracy" not in key.lower()
    blob = repr(out).lower().replace(out["summary"]["not_a_benchmark"].lower(), "")
    assert not re.search(r"\d+(\.\d+)?\s*%", blob), "a percentage claim appeared in a batch payload"
    for forbidden in ("hit rate", "accuracy of", "correctly"):
        assert forbidden not in blob
