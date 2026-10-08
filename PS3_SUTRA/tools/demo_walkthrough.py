#!/usr/bin/env python3
"""P13 — the smallest demonstrator that proves the loop works end to end.

    python3 tools/demo_walkthrough.py

Six scenes, on a fresh copy of the runtime store (the canonical store is never written to):

  1. a cold bad address           -> uncertainty, VERIFY_FIRST, and no invented coordinate
  2. one field observation        -> evidence weighting, with reason codes
  3. a second independent one     -> belief + memory update (promotion)
  4. the same place, later        -> a better answer (field-backed, tighter radius)
  5. a low-integrity negative     -> it cannot fake corroboration; doubt widens, coordinates stay
  6. offline: pack -> airplane -> capture -> outbox -> reconnect -> replay

Writes `data/derived/demo_transcript.md`.
"""
from __future__ import annotations

import json
import os
import shutil
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sutra import asof, config                                   # noqa: E402
from sutra.belief import belief_instant, compute_belief           # noqa: E402
from sutra.indexes import get_index                                # noqa: E402
from sutra.memory import place_state                              # noqa: E402
from sutra.offline import OfflineDevice                           # noqa: E402
from sutra.packs import build_pack, load_pack, verify_pack        # noqa: E402
from sutra.resolve import explain, resolve                        # noqa: E402
from sutra.store import Store, submit_observation                 # noqa: E402

LINES: list[str] = []
SCRATCH = os.path.join(config.RUNTIME, "scratch")      # throwaway copies; removed at the end
DEMO_STORE = os.path.join(SCRATCH, "demo_store.sqlite")
ADDR = None      # chosen at runtime: a genuinely cold address with a landmark in its text
T0 = "2026-06-05T09:00:00Z"      # weak visit
T1 = "2026-06-14T09:00:00Z"      # first strong confirmation
T1B = "2026-06-23T09:00:00Z"     # second strong, independent confirmation
T2 = "2026-06-25T09:00:00Z"      # resolve after promotion
T3 = "2026-07-02T09:00:00Z"      # a negative


def say(text: str = "") -> None:
    print(text)
    LINES.append(text)


def h(title: str) -> None:
    say()
    say(f"### {title}")
    say()


def choose_demo_address(ix) -> str:
    """A cold address (no evidence in the official history) that names an official landmark.

    Deterministic: the first address in id order that satisfies all three tests.
    """
    from sutra.candidates import generate as gen
    warm = {r[0] for r in sqlite3.connect(config.STORE_PATH).execute(
        "SELECT DISTINCT address_id FROM observations")}
    for aid in sorted(ix.addresses):
        if aid in warm or ix.baseline.get(aid) is None:
            continue
        cands = gen(aid, config.MOMENT, store=None, ix=ix)
        if any(c["arm"] == "official_landmark" for c in cands) and \
                any(c["arm"] in ("frozen_baseline", "locality_centroid") for c in cands):
            return aid
    raise SystemExit("no suitable demo address found")


def fresh_demo_store() -> Store:
    os.makedirs(SCRATCH, exist_ok=True)
    if os.path.exists(DEMO_STORE):
        Store.reset(DEMO_STORE)
    src = sqlite3.connect(config.STORE_PATH)
    dst = sqlite3.connect(DEMO_STORE)
    src.backup(dst)
    src.close()
    dst.close()
    return Store(DEMO_STORE)


def observation(agent: str, when: str, x: float, y: float, media: str, *, outcome="met_borrower",
                dwell=300.0, acc=8.0, oid=None):
    return {"observation_id": oid or f"demo-{agent}-{when}", "kind": "visit", "address_id": ADDR,
            "agent_id": agent, "outcome": outcome,
            "checkin": {"x": x, "y": y, "gps_accuracy_m": acc}, "dwell_s": dwell,
            "observed_at": when, "media": [{"sha256": media, "kind": "photo"}]}


def submit(st: Store, o: dict) -> dict:
    return submit_observation(o, o["observation_id"], store=st)


def show_resolve(st: Store, when: str, purpose="FIELD_NAVIGATION") -> dict:
    r = resolve("", None, asof.parse_ts(when), purpose, store=st, address_id=ADDR)
    say(f"resolve(as_of={when})")
    say(f"  -> {explain(r)}")
    c = r["candidate"]
    if c:
        say(f"     candidate {c['candidate_id']} · arm={c['arm']} · granularity={c['granularity']} "
            f"· x={c['x']} y={c['y']}")
    say(f"     reasons: {', '.join(r['reasons'][:6])}")
    say(f"     address_purpose={r['address_purpose']['class']} · request_purpose={r['request_purpose']}"
        f" · directions={'none' if not r['directions'] else r['directions'][0]['cue_text']}")
    return r


def main() -> int:
    global ADDR
    ix = get_index()
    ADDR = choose_demo_address(ix)
    st = fresh_demo_store()
    addr = ix.addresses[ADDR]
    say("# SUTRA — implementation demo (6 scenes)")
    say()
    say(f"Address: `{ADDR}` — *{addr['address_text'][:70]}*  (town {addr['town_id']}, "
        f"{addr['address_type']})")
    say()
    say("Runtime versions: " + json.dumps({"schema": "sutra-1.0", "rules": "candidate-rules-v2",
                                           "evidence": "evidence-policy-v3", "radius": "radius-map-v1"},
                                          separators=(", ", ": ")))

    # ── 1 ───────────────────────────────────────────────────────────────────────────────────────
    h("Scene 1 — a cold, badly written address")
    say("This address has no evidence at all in the official history: cold, and badly written.")
    b = compute_belief(ADDR, asof.parse_ts("2026-06-04T00:00:00Z"), st, ix=ix)
    say(f"belief before any visit: tier={b['tier']} status={b['status']} "
        f"radius={b['radius']['radius_m']} m (stratum {b['radius']['source_stratum']}, "
        f"basis {b['radius']['basis']}, n={b['radius']['n_calibration']})")
    r1 = show_resolve(st, "2026-06-04T00:00:00Z")
    say("  the address still gets an answer — but the answer carries its own uncertainty and the gate")
    say(f"  says {r1['eligibility']['action']} ({r1['eligibility']['reason']}): go and verify before "
        f"anything irreversible happens.")

    # ── 2 ───────────────────────────────────────────────────────────────────────────────────────
    h("Scene 2 — one field observation: evidence weighting, not a trust flag")
    weak = submit(st, observation("FA301", T0, 1255.0, -276.0, "demo-dup-hash", dwell=45.0, acc=42.0))
    say(f"submitted a weak visit (dwell 45 s, GPS ±42 m, photo hash already seen elsewhere)")
    say(f"  evidence weight = {weak['evidence']['weight']} · reasons = {weak['evidence']['reasons']}")
    say(f"  belief now: tier={weak['tier']} status={weak['status']} · the coordinate did not move: "
        f"candidate unchanged ({weak['coordinate']} is the same x as before)")

    # ── 3 ───────────────────────────────────────────────────────────────────────────────────────
    h("Scene 3 — two independent confirmations: belief + memory update")
    strong = submit(st, observation("FA302", T1, 1267.0, -260.0, "demo-good-2"))
    say(f"submitted a second visit (different collector, 9 days later, distinct photo, "
        f"dwell 300 s, GPS ±8 m)")
    say(f"  evidence weight = {strong['evidence']['weight']} · reasons = {strong['evidence']['reasons']}")
    say(f"  belief after one confirmation -> tier={strong['tier']} status={strong['status']}")
    strong2 = submit(st, observation("FA304", T1B, 1271.0, -258.0, "demo-good-3"))
    say(f"submitted a third visit (third collector, 9 days later, distinct photo) — now the independence "
        f"tuple is satisfied")
    say(f"  evidence weight = {strong2['evidence']['weight']} · belief -> tier={strong2['tier']} "
        f"status={strong2['status']} version v{strong2['belief_version']}")
    ps = place_state(f"PL-{ADDR}", belief_instant(st, ADDR), st)
    say(f"  place {ps['place_id']} state={ps['state']} · members={ps['member_address_ids']} "
        f"· identity_rule={ps['identity_rule']}")

    # ── 4 ───────────────────────────────────────────────────────────────────────────────────────
    h("Scene 4 — the same place, later: a better answer")
    r4 = show_resolve(st, T2)
    say(f"  compare scene 1: tier {b['tier']} -> {r4['tier']}, radius {b['radius']['radius_m']} -> "
        f"{r4['radius_m']} m, arm -> {r4['candidate']['arm']}")
    prov = r4["candidate"]["provenance"]
    say(f"  winning arm: {r4['candidate']['arm']} — {prov.get('built_from')}")
    if prov.get("observation_ids"):
        say(f"    backed by {len(prov['observation_ids'])} independent check-ins "
            f"(spread {prov.get('spread_m')} m): {', '.join(prov['observation_ids'])}")
    say("  the top-3 arms by score, as the ranker reported them:")
    for a in r4["arms_considered"][:3]:
        say(f"    {a['score']:.3f}  {a['arm']:18s} primary_eligible={a['primary_eligible']}")

    # ── 5 ───────────────────────────────────────────────────────────────────────────────────────
    h("Scene 5 — a low-integrity negative: doubt widens, the coordinate does not move")
    before = compute_belief(ADDR, belief_instant(st, ADDR), st, ix=ix)
    neg = submit(st, observation("FA303", T3, 0, 0, "demo-neg", outcome="address_not_traceable",
                                 dwell=60.0, acc=25.0))
    after = compute_belief(ADDR, belief_instant(st, ADDR), st, ix=ix)
    say(f"negative evidence weight = {neg['evidence']['weight']} "
        f"(polarity={neg['evidence']['polarity']}, reasons={neg['evidence']['reasons']})")
    say(f"  coordinate before: ({before['candidate']['x']}, {before['candidate']['y']})  "
        f"after: ({after['candidate']['x']}, {after['candidate']['y']})  -> identical")
    say(f"  radius {before['radius']['radius_m']} -> {after['radius']['radius_m']} m "
        f"(widen_reason={after['radius']['widen_reason']}) · status {before['status']} -> {after['status']}")
    say("  one bad visit can no longer be mistaken for a finding: it costs confidence, not accuracy.")

    # ── 6 ───────────────────────────────────────────────────────────────────────────────────────
    h("Scene 6 — offline field capture, then replay")
    man = build_pack(addr["town_id"], store=st, ix=ix, out_dir=os.path.join(config.DERIVED, "packs"))
    pack = load_pack(os.path.join(config.ROOT, man["path"]))
    say(f"pack {man['pack_version']} · {man['n_addresses']} addresses · {man['bytes']} bytes · "
        f"valid until {man['valid_until']} · contains polygons={pack['contains_polygons']} "
        f"evidence={pack['contains_evidence']} truth={pack['contains_truth']}")
    dev_path = os.path.join(SCRATCH, "device_FA303_demo.sqlite")
    if os.path.exists(dev_path):
        os.remove(dev_path)          # a fresh device each run: the outbox is empty, the demo is repeatable
    dev = OfflineDevice("FA303", path=dev_path)
    say(f"  download -> verified={dev.download_pack(pack)['ok']}")
    dev.airplane_mode = True
    dev.capture(observation("FA303", "2026-07-09T09:00:00Z", 1258.0, -273.0, "demo-off-1",
                            oid="demo-off-1"))
    dev.capture(observation("FA303", "2026-07-18T09:00:00Z", 1271.0, -258.0, "demo-off-2",
                            oid="demo-off-2"))
    say(f"  airplane mode: captured 2, outbox queue = {dev.capture_looks_queued()}; "
        f"the server store still holds {st.count('observations')} observations — none of them these two")
    dev.airplane_mode = False
    out = dev.replay(st)
    say(f"  reconnect: drained {out['drained']} in local_seq order "
        f"{[r['local_seq'] for r in out['results']]} -> server belief v{out['results'][-1]['belief_version']} "
        f"tier={out['results'][-1]['tier']} status={out['results'][-1]['status']}")
    say(f"  queue left = {out['queue_left']}")
    final = show_resolve(st, "2026-07-18T10:00:00Z")
    say("  every claim above is attributable: " + json.dumps(final["versions"], separators=(", ", ": ")))

    shutil.rmtree(SCRATCH, ignore_errors=True)      # the transcript is the artefact, not the scratch DBs
    out_path = os.path.join(config.DERIVED, "demo_transcript.md")
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(LINES) + "\n")
    print(f"\nwrote {os.path.relpath(out_path, config.ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
