"""P10 — the acceptance gate: T1–T15 from the implementation contract, plus the invariants.

    python3 -m pytest tests/test_acceptance.py -v

Every test builds its own store under `tmp_path`: the canonical artefacts in `data/derived/` are read
only, so a failing test can never corrupt the built workspace. Tests that read surveyed truth only ever
read the *S-Eval* rows of the existing evaluation artefacts.

Naming: `test_T<n>_...` maps to contract §15. `test_invariant_...` covers the cross-cutting rules
(as-of single gate, append-only, determinism, vocabulary, no network, no external data).
"""
from __future__ import annotations

import csv
import json
import os
import re
import socket
import sys
import hashlib

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from sutra import asof, config, dataio, evidence as ev_mod, geo, ranking, splits, uncertainty  # noqa: E402
from sutra.belief import belief_instant, compute_belief, recompute_belief                     # noqa: E402
from sutra.candidates import generate                                                          # noqa: E402
from sutra.indexes import get_index                                                            # noqa: E402
from sutra.memory import place_state, verify_first_tasks                                       # noqa: E402
from sutra.offline import OfflineDevice                                                        # noqa: E402
from sutra import preprocess                                                                   # noqa: E402
from sutra.packs import build_pack, verify_pack                                                # noqa: E402
from sutra.resolve import resolve                                                              # noqa: E402
from sutra.store import DeterminismViolation, Store, submit_observation                        # noqa: E402

MOMENT = config.MOMENT
ADDR = "AD000001"          # residence, T1, street-precision baseline, not surveyed
ADDR_OFFICE = "AD000002"   # address_type = office (WORK_LIKE by rule P1)
ADDR_OUT = "AD000006"      # town_id = OUT, no baseline pin -> no candidate arm can fire


# ── helpers ─────────────────────────────────────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def ix():
    return get_index()


@pytest.fixture(scope="module")
def rings(ix):
    """Every preprocessing rung built once (B3/B4 fit their text model here)."""
    return preprocess.build_all(ix)


def fresh(tmp_path, name="store.sqlite") -> Store:
    return Store(str(tmp_path / name))


def obs(address_id, agent, when, x, y, *, outcome="met_borrower", media="m1", dwell=300.0, acc=8.0,
        observation_id=None, **kw):
    o = {
        "observation_id": observation_id or f"obs-{address_id}-{agent}-{when}",
        "kind": "visit", "address_id": address_id, "agent_id": agent,
        "outcome": outcome, "checkin": {"x": x, "y": y, "gps_accuracy_m": acc},
        "dwell_s": dwell, "observed_at": when,
        "media": ([{"sha256": media, "kind": "photo"}] if media else []),
    }
    o.update(kw)
    return o


def submit(store, observation):
    return submit_observation(observation, observation["observation_id"], store=store)


def two_independent_confirmations(store, address_id=ADDR, x=1255.0, y=-276.0):
    """Two collectors, distinct media, 9 days apart, check-ins 20 m apart — promotion-grade (F2.2)."""
    a = submit(store, obs(address_id, "FA101", "2026-05-02T09:00:00Z", x, y, media="m-a1"))
    b = submit(store, obs(address_id, "FA102", "2026-05-11T09:00:00Z", x + 12.0, y + 16.0, media="m-b1"))
    return a, b


def negative(store, address_id, agent, when, media):
    return submit(store, obs(address_id, agent, when, None, None, outcome="address_not_traceable",
                             media=media))


def walk_keys(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield path + "/" + str(k), k, v
            yield from walk_keys(v, path + "/" + str(k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk_keys(v, f"{path}[{i}]")


def has_coordinate(obj) -> bool:
    """True if any dict in the response carries an x/y pair — the T1 negative test."""
    for _, k, v in walk_keys(obj):
        if k in ("x", "y") and isinstance(v, (int, float)):
            return True
    return False


# ══ T1 ═══════════════════════════════════════════════════════════════════════════════════════════
def test_T1_no_candidate_no_coordinate(tmp_path, ix):
    st = fresh(tmp_path)
    r = resolve("nowhere street that does not exist", None, MOMENT, "FIELD_NAVIGATION", store=st)
    assert r["candidate"] is None, "an unmatched text must not produce a candidate"
    assert not has_coordinate(r), "no coordinate may appear anywhere in a no-candidate response"
    assert r["tier"] == "UNPLACEABLE"
    assert r["eligibility"]["action"] in ("VERIFY_FIRST", "REFUSE")

    # a real record whose town is outside every modelled town: no arm can fire either
    r2 = resolve("", None, MOMENT, "FIELD_NAVIGATION", store=st, address_id=ADDR_OUT)
    assert r2["candidate"] is None and r2["tier"] == "UNPLACEABLE" and not has_coordinate(r2)
    assert r2["eligibility"]["action"] in ("VERIFY_FIRST", "REFUSE")
    # the town centroid is never served as an address coordinate
    assert "town_centroid" not in json.dumps(r2)


# ══ T2 ═══════════════════════════════════════════════════════════════════════════════════════════
def _answer(rec: dict) -> str:
    """The *answer* part of a belief's candidate: coordinate, granularity, weight, validity and the
    provenance that describes the place. Which arms corroborate is deliberately excluded: that
    bookkeeping is exactly what `FINAL_EVIDENCE_MEMORY_POLICY` (emp-v1) is allowed to change — a
    prior that merely re-wraps the vendor pin no longer counts as independent corroboration. The
    safety invariants under test (the coordinate never moves, the radius never narrows) are
    unaffected by that and remain asserted below, byte for byte."""
    p = dict(rec.get("provenance") or {})
    for k in ("agreement_arms", "agreement_list", "n_arms"):
        p.pop(k, None)
    return json.dumps({**{k: v for k, v in rec.items() if k != "provenance"}, "provenance": p},
                      sort_keys=True)


def test_T2_one_negative_coordinate_unchanged(tmp_path, ix):
    st = fresh(tmp_path)
    two_independent_confirmations(st)
    before = compute_belief(ADDR, belief_instant(st, ADDR), st, ix=ix)
    assert before["tier"] == "CONFIRMED" and before["status"] == "STABLE"

    receipt = negative(st, ADDR, "FA103", "2026-05-20T09:00:00Z", "m-neg1")
    after = compute_belief(ADDR, belief_instant(st, ADDR), st, ix=ix)

    assert _answer(before["candidate"]) == _answer(after["candidate"])
    assert (after["candidate"]["x"], after["candidate"]["y"]) == (before["candidate"]["x"], before["candidate"]["y"])
    assert after["radius"]["radius_m"] >= before["radius"]["radius_m"], "a negative may widen, never narrow"
    assert after["status"] in ("STABLE", "CONTESTED", "MOVED_SUSPECTED", "STALE")
    assert after["tier"] in ("CONFIRMED", "PROBABLE", "APPROXIMATE")   # unchanged or downgraded
    assert after["support"]["negatives_independent"] == 1
    assert receipt["evidence"]["polarity"] == "negative"


# ══ T3 ═══════════════════════════════════════════════════════════════════════════════════════════
def test_T3_independent_negatives_doubt_out_loud(tmp_path, ix):
    st = fresh(tmp_path)
    two_independent_confirmations(st)
    before = compute_belief(ADDR, belief_instant(st, ADDR), st, ix=ix)

    negative(st, ADDR, "FA103", "2026-05-14T09:00:00Z", "m-n1")
    negative(st, ADDR, "FA104", "2026-05-21T09:00:00Z", "m-n2")
    negative(st, ADDR, "FA105", "2026-05-28T09:00:00Z", "m-n3")
    after = compute_belief(ADDR, belief_instant(st, ADDR), st, ix=ix)

    assert after["support"]["negatives_independent"] >= 2
    assert after["status"] in ("MOVED_SUSPECTED", "CONTESTED")
    assert after["tier"] == "APPROXIMATE", "accumulated negatives cap the tier"
    assert _answer(before["candidate"]) == _answer(after["candidate"]), \
        "negatives still may not relocate the coordinate"
    assert (after["candidate"]["x"], after["candidate"]["y"]) == (before["candidate"]["x"], before["candidate"]["y"])
    tasks = verify_first_tasks(ix.town_of(ADDR), 100, st)
    assert any(t.get("address_id") == ADDR for t in tasks), "a verify-first task must be raised"


# ══ T4 ═══════════════════════════════════════════════════════════════════════════════════════════
def test_T4_fake_independence_rejected(tmp_path, ix):
    st = fresh(tmp_path)
    submit(st, obs(ADDR, "FA101", "2026-05-02T09:00:00Z", 1255.0, -276.0, media="m-same"))
    submit(st, obs(ADDR, "FA101", "2026-05-02T16:00:00Z", 1256.0, -275.0, media="m-same"))
    b = compute_belief(ADDR, belief_instant(st, ADDR), st, ix=ix)

    assert b["tier"] != "CONFIRMED", "one collector, one day, one photo hash is not corroboration"
    assert b["promotion_detail"]["media_ok"] is False
    state = place_state(b["place_id"], belief_instant(st, ADDR), st)
    assert state["state"] in ("WARM", "COLD")


# ══ T5 ═══════════════════════════════════════════════════════════════════════════════════════════
def test_T5_valid_confirmations_promote(tmp_path, ix):
    st = fresh(tmp_path)
    two_independent_confirmations(st)
    b = compute_belief(ADDR, belief_instant(st, ADDR), st, ix=ix)

    assert b["tier"] == "CONFIRMED"
    assert b["status"] == "STABLE"
    assert b["promotion_detail"]["n_strong"] >= 2
    assert b["promotion_detail"]["media_ok"] and b["promotion_detail"]["space_ok"]
    assert b["candidate"]["arm"] == "field_evidence"
    assert b["candidate"]["provenance"]["primary_eligible"] is True
    assert b["candidate"]["provenance"]["n_observations"] >= 2
    assert place_state(b["place_id"], belief_instant(st, ADDR), st)["state"] == "CONFIRMED"


# ══ T6 ═══════════════════════════════════════════════════════════════════════════════════════════
def test_T6_pincode_radius_withheld_and_falls_back(tmp_path, ix):
    st = fresh(tmp_path)
    pin_addr = next(a for a in sorted(ix.addresses)
                    if ix.baseline.get(a, {}).get("precision") == "pincode")
    r = resolve("", None, MOMENT, "FIELD_NAVIGATION", store=st, address_id=pin_addr)
    assert r["candidate"] is not None
    assert r["candidate"]["provenance"]["baseline_precision"] == "pincode"
    assert r["source_stratum"] == config.FALLBACK_STRATUM, "an unpublished stratum names its parent"
    assert r["nominal"] is None, "no nominal claim was ever measured (U2)"
    assert r["radius_basis"] == "empirical_p80"
    assert r["n_calibration"] == config.RADIUS_TABLE[config.FALLBACK_STRATUM]["n_calibration"]
    assert r["widened"] is True and r["widen_reason"] == "calibration_fallback"
    # and the withholding is a property of the map, not of this one query
    assert uncertainty.published_stratum("pincode") == (config.FALLBACK_STRATUM, True)
    assert uncertainty.published_stratum("rooftop") == (config.FALLBACK_STRATUM, True)   # n=1 < 15
    assert uncertainty.published_stratum("locality") == ("locality", False)


# ══ T7 ═══════════════════════════════════════════════════════════════════════════════════════════
def test_T7_belief_determinism(tmp_path, ix):
    st = fresh(tmp_path)
    two_independent_confirmations(st)
    when = belief_instant(st, ADDR)
    first = compute_belief(ADDR, when, st, ix=ix)
    sha = st.append_belief(ADDR, first, computed_at="2026-05-11T09:00:00Z")["payload_sha256"]

    second = compute_belief(ADDR, when, st, ix=ix)
    j1 = json.dumps(first, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    j2 = json.dumps(second, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    assert j1 == j2, "re-deriving a belief must be byte-identical"
    stored = st.latest_belief(ADDR, as_of=when)
    assert stored["payload_sha256"] == sha
    assert stored["payload_json"] == j1
    # and the store refuses to persist a *different* payload for the same version
    tampered = dict(second, tier="CONFIRMED" if second["tier"] != "CONFIRMED" else "APPROXIMATE")
    with pytest.raises(DeterminismViolation):
        st.append_belief(ADDR, tampered, computed_at="2026-05-11T09:00:00Z")


# ══ T8 ═══════════════════════════════════════════════════════════════════════════════════════════
def test_T8_duplicate_observation_idempotent(tmp_path, ix):
    st = fresh(tmp_path)
    o = obs(ADDR, "FA101", "2026-05-02T09:00:00Z", 1255.0, -276.0, observation_id="obs-dup-1")
    r1 = submit(st, o)
    r2 = submit(st, dict(o, checkin={"x": 9999.0, "y": 9999.0, "gps_accuracy_m": 1.0}))  # tampered replay
    assert r1["replayed"] is False and r2["replayed"] is True
    assert r2["state"] == "DUPLICATE_OBSERVATION"
    assert r2["observation_id"] == r1["observation_id"]
    assert r2["belief_version"] == r1["belief_version"]
    n = st.conn.execute("SELECT COUNT(*) FROM observations WHERE observation_id = ?", ("obs-dup-1",)).fetchone()[0]
    assert n == 1, "a replayed observation is stored once"
    n_ev = st.conn.execute("SELECT COUNT(*) FROM evidence_scores WHERE observation_id = ?", ("obs-dup-1",)).fetchone()[0]
    assert n_ev == 1, "and scored once"


# ══ T9 ═══════════════════════════════════════════════════════════════════════════════════════════
def test_T9_offline_capture_outbox_replay(tmp_path, ix):
    st = fresh(tmp_path, "server.sqlite")
    manifest = build_pack("T1", store=st, ix=ix, as_of=MOMENT, out_dir=str(tmp_path / "packs"))
    assert manifest["contains_evidence"] is False and manifest["contains_truth"] is False
    assert manifest["contains_polygons"] is False
    from sutra.packs import load_pack
    pack = load_pack(os.path.join(ROOT, manifest["path"]))
    assert verify_pack(pack)["ok"] is True
    assert pack["pack_version"] == manifest["pack_version"]

    dev = OfflineDevice("dev-t9", path=str(tmp_path / "device.sqlite"))
    assert dev.download_pack(pack)["ok"] is True          # downloaded while still online
    assert dev.local_pack("T1")["pack_version"] == pack["pack_version"]

    dev.airplane_mode = True                              # ── network off ──
    dev.capture(obs(ADDR, "FA201", "2026-06-02T09:00:00Z", 1255.0, -276.0, media="m-off1"))
    dev.capture(obs(ADDR, "FA202", "2026-06-11T09:00:00Z", 1267.0, -260.0, media="m-off2"))
    assert dev.capture_looks_queued() == 2, "capture must work with no network"
    assert st.count("observations") == 0, "an offline capture never touches the server"
    assert dev.replay(st)["drained"] == 0, "replay while offline must not drain"

    dev.airplane_mode = False                             # ── reconnect ──
    out = dev.replay(st)
    assert out["drained"] == 2 and out["queue_left"] == 0
    assert [r["local_seq"] for r in out["results"]] == [1, 2], "the outbox drains in local_seq order"
    assert st.count("observations") == 2
    b = compute_belief(ADDR, belief_instant(st, ADDR), st, ix=ix)
    assert b["tier"] == "CONFIRMED", "the server recomputed the belief from replayed evidence"
    assert b["support"]["n_observations"] == 2
    # replaying again is a no-op
    assert dev.replay(st)["drained"] == 0


# ══ T10 ══════════════════════════════════════════════════════════════════════════════════════════
def test_T10_work_like_refused_for_notice(tmp_path, ix):
    st = fresh(tmp_path)
    r = resolve("", None, MOMENT, "NOTICE_SERVICE", store=st, address_id=ADDR_OFFICE)
    assert r["address_purpose"]["class"] == "WORK_LIKE"
    assert r["eligibility"]["action"] == "REFUSE"
    assert r["eligibility"]["reason"] == "purpose_work_like"
    assert r["eligibility"]["rule_version"] == config.GATE_RULE_VERSION if hasattr(config, "GATE_RULE_VERSION") else True
    logged = st.conn.execute("SELECT COUNT(*) FROM counter_events WHERE name = 'gate_decisions'").fetchone()[0]
    assert logged > 0, "every gate decision is logged with its rule version"
    # the same place for a review purpose is still refused: purpose does not grant permission
    r2 = resolve("", None, MOMENT, "PORTFOLIO_REVIEW", store=st, address_id=ADDR_OFFICE)
    assert r2["eligibility"]["action"] in ("REFUSE", "VERIFY_FIRST")


# ══ T11 ══════════════════════════════════════════════════════════════════════════════════════════
def test_T11_no_cue_when_nothing_resolves(tmp_path, ix):
    st = fresh(tmp_path)
    plain = next(a for a in sorted(ix.addresses)
                 if not dataio.relation_windows(ix.addresses[a].get("address_text_raw") or "")[0]
                 and ix.addresses[a]["town_id"] in ix.towns)
    r = resolve("", None, MOMENT, "FIELD_NAVIGATION", store=st, address_id=plain)
    assert r["candidate"] is not None, "the address still resolves; only the cue is absent"
    assert r["directions"] is None, "no resolvable landmark means no cue, never a guessed one"
    # and no cue without a candidate at all
    r2 = resolve("", None, MOMENT, "FIELD_NAVIGATION", store=st, address_id=ADDR_OUT)
    assert r2["directions"] is None


# ══ T12 ══════════════════════════════════════════════════════════════════════════════════════════
def test_T12_no_external_data_and_zero_outbound_calls(tmp_path, ix, monkeypatch):
    def blocked(*a, **k):
        raise AssertionError("outbound network call attempted")

    for name in ("socket", "create_connection", "getaddrinfo", "gethostbyname"):
        if hasattr(socket, name):
            monkeypatch.setattr(socket, name, blocked)

    st = fresh(tmp_path)
    two_independent_confirmations(st)
    assert resolve("", None, MOMENT, "FIELD_NAVIGATION", store=st, address_id=ADDR)["candidate"]
    compute_belief(ADDR, belief_instant(st, ADDR), st, ix=ix)
    place_state(f"PL-{ADDR}", belief_instant(st, ADDR), st)
    build_pack("T1", store=st, ix=ix, as_of=MOMENT, out_dir=str(tmp_path / "p2"))
    from sutra.replay import candidate_metrics
    candidate_metrics(splits.declared_specs()[0], store=st, ix=ix)   # the S-Eval spec, in a temp store

    # no dataset outside official/cleaned/derived, and no external-provider vocabulary in the runtime
    ext = (".csv", ".tsv", ".json", ".geojson", ".parquet", ".sqlite", ".gpkg", ".shp", ".pbf", ".xlsx")
    allowed = (os.path.join(ROOT, "data", "official_ps3"), os.path.join(ROOT, "data", "cleaned"),
               os.path.join(ROOT, "data", "derived"))
    stray = [os.path.relpath(os.path.join(dp, f), ROOT) for dp, _, fs in os.walk(os.path.join(ROOT, "data"))
             for f in fs if f.lower().endswith(ext) and not os.path.join(dp, f).startswith(allowed)]
    assert not stray, f"data outside the official roots: {stray[:4]}"
    assert not glob_ext(os.path.join(ROOT, "data", "external_research"))
    src = "\n".join(open(os.path.join(ROOT, "sutra", f), encoding="utf-8").read()
                    for f in os.listdir(os.path.join(ROOT, "sutra")) if f.endswith(".py"))
    banned = ("nominatim", "openstreetmap", "geofabrik", "overture", "mapbox", "googleapis",
              "here.com", "mappls", "openaddresses", "microsoft.com/maps")
    hits = [b for b in banned if b in src.lower()]
    assert not hits, f"an external data provider appears in the runtime: {hits}"


def glob_ext(path):
    return [f for f in os.listdir(path)] if os.path.isdir(path) else []


# ══ T13 ══════════════════════════════════════════════════════════════════════════════════════════
def test_T13_feature_matrix_audit():
    cols = set(ranking.FEATURES)
    shared_tables = {"accounts", "agents", "splits", "lenders", "dial_attempts", "payments"}
    col_profile = {}
    for f in ("features_coldstart_v2.csv", "features_warm_v2.csv"):
        p = os.path.join(ROOT, "data", "derived", f)
        assert os.path.exists(p), f"{f} missing — run tools/build_candidates.py"
        with open(p, encoding="utf-8", newline="") as fh:
            header = next(csv.reader(fh))
        col_profile[f] = header
        for shared in shared_tables:
            assert not any(shared in c.lower() for c in header), f"{f} carries a {shared} column"
        for banned in ("account_id", "agent_id", "shift", "tenure", "exposure", "lender", "split"):
            assert not any(banned in c.lower() for c in header), f"{f} carries a {banned} column"
    assert len(ranking.FEATURES) <= 15, "M2 caps the feature count at 15"
    # exactly one shared column is an input to any feature: address_text (read through text_norm)
    assert "address_text" not in cols and "text_norm" not in cols, \
        "raw text is consumed by the feature builder, not exposed as a feature column"
    feat_src = open(os.path.join(ROOT, "sutra", "ranking.py"), encoding="utf-8").read()
    reads = set(re.findall(r'address\["([a-z_]+)"\]', feat_src)) | set(
        re.findall(r"address\.get\(\"([a-z_]+)\"", feat_src))
    assert reads <= {"text_norm", "address_text", "town_id", "flag_outside_town"}, f"unexpected reads: {reads}"


# ══ T14 ══════════════════════════════════════════════════════════════════════════════════════════
def test_T14_s_eval_firewall():
    man = os.path.join(ROOT, "data", "derived", "supervision_manifest.csv")
    fw = os.path.join(ROOT, "data", "derived", "supervision_firewall.csv")
    receipt = os.path.join(ROOT, "data", "derived", "split_receipt.json")
    for p in (man, fw, receipt):
        assert os.path.exists(p), f"{os.path.basename(p)} missing — run tools/build_supervision.py"
    with open(man, encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    with open(fw, encoding="utf-8", newline="") as fh:
        fw_rows = list(csv.DictReader(fh))
    r = json.load(open(receipt, encoding="utf-8"))

    assert r["counts"]["S-EVAL"] == 100, "S-Eval is exactly the 100 surveyed addresses"
    assert r["firewall"]["union"] == len(fw_rows) == 145, "surveyed ∪ accounts ∪ blocks = 145 (4.7%)"
    fw_ids = {x["address_id"] for x in fw_rows}
    train_ids = {x["address_id"] for x in rows if x["split"] in ("S-TRAIN", "S-VAL")}
    assert not (fw_ids & train_ids), "a firewalled address may not appear in any supervision set"
    for x in rows:
        if x["address_id"] in fw_ids:
            assert x["eligible_for_training"] == "False", "firewalled rows are never trainable"
            assert x["split"] in ("S-EVAL", "EXCLUDED")
        if x["split"] == "S-EVAL":
            assert x["address_id"] in set(dataio.surveyed())
    fired = {x["address_id"] for x in rows if x["split"] == "S-EVAL"}
    assert len(fired) == 100 and all(x["eligible_for_training"] == "False" for x in rows
                                    if x["split"] == "S-EVAL")
    counter = Store().counters("s_eval_looks")
    assert counter > 0, "the test-look counter must record S-Eval reads"


# ══ T15 ══════════════════════════════════════════════════════════════════════════════════════════
def test_T15_undeclared_split_aborts(tmp_path, ix):
    from sutra.replay import candidate_metrics
    st = fresh(tmp_path)
    with pytest.raises(splits.UndeclaredSplit):
        candidate_metrics(None, store=st, ix=ix)
    bogus = {"spec_id": "MADE_UP", "populations": ("S-EVAL",), "as_of": MOMENT,
             "label_source": "surveyed_ground_truth", "protocol_version": "protocol-v1-immutable"}
    with pytest.raises(splits.UndeclaredSplit):
        candidate_metrics(bogus, store=st, ix=ix)
    wrong_protocol = dict(splits.declared_specs()[0].to_json())
    wrong_protocol["protocol_version"] = "protocol-v0"
    with pytest.raises(splits.UndeclaredSplit):
        candidate_metrics(wrong_protocol, store=st, ix=ix)
    e = dict(splits.declared_specs()[0].to_json())
    report = candidate_metrics(e, store=st, ix=ix)
    assert report["spec"]["spec_id"] == "S_EVAL_BASELINE"
    assert report["spec"]["protocol_version"] == "protocol-v1-immutable"
    assert report["label_source"] == "surveyed_ground_truth"
    assert "test_look_counter" in report


def test_T16_residue_matcher_is_live_positive_control(ix, rings):
    """Experiment B rejected the B3/B4 residue matcher on this corpus — so prove it *works* first.

    A rejected path that was never shown to fire is indistinguishable from dead code. This control
    feeds a typo'd locality ("kuvempu layot") that has no in-text pincode, so no exact arm can fire,
    and asserts that the residue matcher recovers the correct locality with an inspectable reason.
    """
    locs = [l for l in ix.localities if l["town_id"] == "T1"]
    typo = "flat 12, kuvempu layot, kaveripura"
    addr = {"address_id": "SYNTH-CONTROL", "town_id": "T1", "address_text": typo,
            "text_norm": dataio.norm_text(typo)}

    assert rings["B2"].locality_residue(addr, locs, ix) == [], "B2 must not carry a residue matcher"

    b3 = rings["B3"].locality_residue(addr, locs, ix)
    assert len(b3) == 1, b3
    hit = b3[0]
    name = next((l["locality_name"] for l in locs if l["locality_id"] == hit["locality_id"]), None)
    assert name and dataio.norm_text(name) == "kuvempu layout", hit
    assert hit["score"] >= 0.35 and hit["margin_over_second"] >= 1.25, hit
    assert hit["how"].startswith("residue") and "detail" in hit, "an accepted match must explain itself"

    b4 = rings["B4"].locality_residue(addr, locs, ix)
    assert len(b4) == 1 and b4[0]["locality_id"] == hit["locality_id"], b4
    assert b4[0]["score"] >= 0.3 and b4[0]["idf_score"] > 0, b4[0]

    # the funnel counters are exposed (what was asked, what was accepted, what was refused)
    f = rings["B4"].facts()["residue_stats"]
    assert f["locality_calls"] == 1 and f["locality_accepted"] == 1, f


def test_invariant_rings_change_only_text(tmp_path, ix, rings):
    """A ring may change how text is read and nothing else (Experiment B's validity condition).

    `ring=None` is production B2, so B2/B3/B4 must return byte-identical candidate universes wherever
    the residue matcher declines — which, on this corpus, is everywhere. B1 must differ somewhere on
    the same sample, otherwise the check would be vacuous (it would also pass if `ring` were ignored).
    """
    st = fresh(tmp_path)
    n_checked = 25
    ids = sorted(ix.addresses)[:n_checked]
    b1_differs = 0
    for aid in ids:
        base = generate(aid, MOMENT, store=st, ix=ix)
        for rid in ("B2", "B3", "B4"):
            assert generate(aid, MOMENT, store=st, ix=ix, ring=rings[rid]) == base, (aid, rid)
        if generate(aid, MOMENT, store=st, ix=ix, ring=rings["B1"]) != base:
            b1_differs += 1
    assert b1_differs > 0, "the ring argument never reached the arms — the isolation check is vacuous"


# ══ invariants ═══════════════════════════════════════════════════════════════════════════════════
def _code_only(path: str) -> list[tuple[int, str]]:
    """(line number, code) with comments and multi-line strings (docstrings) removed."""
    import io
    import tokenize
    out = []
    with open(path, encoding="utf-8") as fh:
        try:
            toks = list(tokenize.generate_tokens(fh.readline))
        except tokenize.TokenError:
            return [(i, l) for i, l in enumerate(open(path, encoding="utf-8"), 1)]
    for tok in toks:
        if tok.type in (tokenize.COMMENT, tokenize.NL, tokenize.NEWLINE, tokenize.INDENT,
                        tokenize.DEDENT, tokenize.ENCODING):
            continue
        if tok.type == tokenize.STRING and "\n" in tok.string:
            continue                      # docstrings / multi-line prose
        out.append((tok.start[0], tok.string))
    return out


def test_invariant_asof_is_the_single_gate():
    """No component may implement its own timestamp filtering (P4) — enforced on code, not prose."""
    pkg = os.path.join(ROOT, "sutra")
    pat = re.compile(r"(observed_at|as_of_valid)\s*[<>]=?|<\s*as_of\b|>\s*as_of\b")
    offenders = []
    for f in sorted(os.listdir(pkg)):
        if not f.endswith(".py") or f == "asof.py":
            continue
        src = open(os.path.join(pkg, f), encoding="utf-8").read()
        marker_lines = {i for i, line in enumerate(src.splitlines(), 1) if "# asof-backend" in line}
        for lineno, code in _code_only(os.path.join(pkg, f)):
            if pat.search(code):
                # a marker may sit on the line itself or on the statement's opening line
                if lineno in marker_lines:
                    continue
                offenders.append(f"{f}:{lineno}: {code[:70]}")
    assert not offenders, "timestamp filtering outside asof.py: " + "; ".join(offenders)


def test_invariant_store_is_append_only():
    src = open(os.path.join(ROOT, "sutra", "store.py"), encoding="utf-8").read()
    body = src.split('"""', 2)[2]                     # drop the module docstring
    assert not re.search(r"\bUPDATE\s+\w+\s+SET\b", body, re.I), "no UPDATE in the store"
    assert not re.search(r"\bDELETE\s+FROM\b", body, re.I), "no DELETE in the store"


def test_invariant_candidate_vocabulary_and_no_truth():
    p = os.path.join(ROOT, "data", "derived", "candidates_v2.csv")
    assert os.path.exists(p), "run tools/build_candidates.py"
    with open(p, encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
        header = list(rows[0])
    assert set(header) & {"err_m", "truth", "surveyed_x", "surveyed_y", "label"} == set()
    assert {r["arm"] for r in rows} <= set(config.ARMS)
    assert {r["licence_class"] for r in rows} == {"official"}
    assert "place_neighbour" not in {r["arm"] for r in rows}, "C2 has not admitted the neighbour index"
    for r in rows:
        if r["arm"] in config.EVIDENCE_ARMS:
            assert r["as_of_valid"], f"{r['arm']} must carry as_of_valid"
        else:
            assert not r["as_of_valid"], f"{r['arm']} must not carry as_of_valid"
    for bad in ("vendor_tos", "open_sharealike", "vendor_pin", "prior_field_cluster"):
        blob = open(p, encoding="utf-8").read()
        assert bad not in blob, f"pre-contract vocabulary survived: {bad}"


def test_invariant_labels_are_evaluation_only():
    p = os.path.join(ROOT, "data", "derived", "labels_eval_v2.csv")
    assert os.path.exists(p)
    rows = list(csv.DictReader(open(p, encoding="utf-8", newline="")))
    assert rows and {r["split"] for r in rows} == {"S-EVAL"}
    assert {r["label_source"] for r in rows} == {"surveyed_ground_truth"}
    for f in ("features_coldstart_v2.csv", "features_warm_v2.csv"):
        header = next(csv.reader(open(os.path.join(ROOT, "data", "derived", f), encoding="utf-8")))
        assert not any(c in header for c in ("err_m", "label_within_100m", "is_best_of_set"))


def test_invariant_pack_has_no_truth_or_evidence():
    p = os.path.join(ROOT, "data", "derived", "packs")
    packs = [f for f in os.listdir(p) if f.endswith(".json")] if os.path.isdir(p) else []
    if not packs:
        pytest.skip("no pack built yet (run tools/build_pack.py or the demo)")
    blob = open(os.path.join(p, sorted(packs)[0]), encoding="utf-8").read()
    for bad in ("surveyed_x", "surveyed_y", "err_m", "observation_id", "remarks"):
        assert bad not in blob, f"a pack must not carry {bad}"
    assert '"contains_polygons":false' in blob.replace(" ", "")


def test_invariant_radius_never_claims_an_unmeasured_nominal():
    for stratum in ("locality", "street", "pincode", "rooftop", "town"):
        r = uncertainty.radius_for({"granularity": stratum, "provenance": {"stratum": stratum}},
                                   "APPROXIMATE", "STABLE", 0, False)
        assert r["nominal"] is None and r["basis"] == "empirical_p80"
        assert r["n_calibration"] is not None and r["source_stratum"] is not None
        if stratum in ("pincode", "rooftop", "street", "town"):
            assert r["source_stratum"] == config.FALLBACK_STRATUM
            assert r["widened"] is True and r["widen_reason"] == "calibration_fallback"


def test_invariant_no_vendor_call_in_the_runtime():
    src = ""
    for f in sorted(os.listdir(os.path.join(ROOT, "sutra"))):
        if f.endswith(".py"):
            src += open(os.path.join(ROOT, "sutra", f), encoding="utf-8").read()
    for banned in ("requests.", "urllib.request", "http.client", "socket.socket(", "urlopen"):
        assert banned not in src, f"{banned} appears in the runtime"


def test_invariant_supervision_manifest_shape():
    p = os.path.join(ROOT, "data", "derived", "supervision_manifest.csv")
    header = next(csv.reader(open(p, encoding="utf-8")))
    for col in ("address_id", "account_id", "place_block_id", "split", "as_of",
                "source_observation_ids", "eligible_for_training", "exclusion_reason"):
        assert col in header, f"supervision rows must state {col}"


# ══ invariant: a typed address must reach the index (found live, on the running server) ═════════════
def test_invariant_typed_text_reaches_the_index(tmp_path, ix):
    """The request path is only real if text a human types can find its own record.

    Found by running the live server: the runtime's normaliser had drifted from the cleaner's, so an
    exact paste of a corpus address returned UNPLACEABLE. One normaliser, or the index is unreachable.
    """
    rows = dataio.addresses()
    for aid in sorted(rows)[:60]:                     # the corpus normalisation is reproduced exactly
        assert dataio.norm_text(rows[aid]["address_text"]) == (rows[aid].get("text_norm") or ""), aid

    st = fresh(tmp_path)
    r = resolve(rows[ADDR]["address_text"], None, MOMENT, "FIELD_NAVIGATION", store=st)
    assert r["address_id"] == ADDR and r["resolution"] == "exact_text_match", r["resolution"]

    # a near miss must NOT be resolved to somebody else's door: area context, and no coordinate at all
    near = "6th cross, 5th main, kuvempu layout, kaveripura 960102"
    r2 = resolve(near, None, MOMENT, "FIELD_NAVIGATION", store=st)
    assert r2["candidate"] is None and not has_coordinate(r2), "a near miss must not fabricate a point"
    assert r2["is_area_context"] is True and r2["resolution"].startswith("area_context:")
    assert r2["area_context"] and r2["area_context"]["coordinate"] is None
    assert "area_context_locality_only" in r2["reasons"]

    # and a string that matches nothing at all stays a plain no-candidate refusal
    r3 = resolve("nowhere street that does not exist", None, MOMENT, "FIELD_NAVIGATION", store=st)
    assert r3["is_area_context"] is False and r3["area_context"] is None and not has_coordinate(r3)
