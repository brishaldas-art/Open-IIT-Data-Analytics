#!/usr/bin/env python3
"""Production smoke test — exercise the real service the way the console does.

    python3 tools/smoke_test.py [--base http://127.0.0.1:8000]

Checks, in order: the served workbench bundle, runtime health, both resolve demo cases, the refusal case,
geometry, belief, observations, place, the verification queue, the town plane, the offline pack, the
error paths, and that a repeated call is byte-identical. Exits non-zero on the first failure.

Read-only against the store apart from the counters the runtime appends while serving (by design).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.error
import urllib.request

MOMENT = "2026-06-01T00:00:00Z"
AD_GOOD = "H.NO. 221, GALI 12, NR COMMUNITY HALL, PATEL NAGAR, DEVGARH NGR"
AD_MOVED = "Gali no-11, Azad Mohalla, Devgarh Nagar - 970203"
AD_WORKLIKE = "no. 173 12th cross 3rd main shanthi nagar kaveripura - 960101"

_results: list[tuple[bool, str, str]] = []


def call(base: str, path: str, body: dict | None = None, method: str | None = None):
    url = base + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method or ("POST" if data else "GET"),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            raw = r.read()
            return r.status, raw
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def check(name: str, ok: bool, detail: str = "") -> None:
    _results.append((ok, name, detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {name}{('  — ' + detail) if detail else ''}")


def jget(base: str, path: str, body: dict | None = None):
    status, raw = call(base, path, body)
    try:
        return status, json.loads(raw)
    except json.JSONDecodeError:
        return status, {"_raw": raw[:120].decode("utf-8", "replace")}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:8000")
    a = ap.parse_args()
    base = a.base.rstrip("/")
    print(f"SUTRA production smoke test against {base}\n")

    # 1 · the console itself
    status, raw = call(base, "/")
    html = raw.decode("utf-8", "replace")
    check("GET / serves the workbench bundle", status == 200 and "<div id=\"root\">" in html,
          f"HTTP {status}, {len(raw)} bytes")
    assets = [t for t in html.split('"') if t.startswith("./assets/") or t.startswith("/assets/")]
    for asset in assets[:2]:
        astatus, araw = call(base, asset if asset.startswith("/") else "/" + asset.lstrip("./"))
        check(f"asset {asset.split('/')[-1]}", astatus == 200 and len(araw) > 1000, f"HTTP {astatus}, {len(araw)} bytes")

    # 2 · runtime health, both aliases
    for path in ("/health", "/v1/health"):
        status, h = jget(base, path)
        ok = status == 200 and h.get("ok") is True and h.get("versions", {}).get("schema_version")
        check(f"GET {path}", ok, f"packs {len(h.get('packs', []))}, s_eval_looks {h.get('counters', {}).get('s_eval_looks')}, "
                                f"obs {h.get('store', {}).get('counts', {}).get('observations')}")

    # 3 · resolve, both demo cases
    status, good = jget(base, "/resolve", {"address_text": AD_GOOD, "town_hint": "T2", "as_of": MOMENT,
                                           "request_purpose": "FIELD_NAVIGATION"})
    check("POST /resolve AD003067", status == 200 and good.get("address_id") == "AD003067"
          and good["coordinate"] is not None and good["eligibility"]["action"] == "SERVE",
          f"{good.get('tier')}/{good.get('status')} r={good.get('radius_m')} space={ (good.get('coordinate') or {}).get('coordinate_space') }")
    check("  · contract blocks present", all(k in good for k in
          ("coordinate", "uncertainty", "alternatives", "decision_ticket", "evidence_summary", "task",
           "as_of", "computed_at", "versions", "resolution", "reason_codes")))

    status, moved = jget(base, "/resolve", {"address_text": AD_MOVED, "town_hint": "T2", "as_of": MOMENT,
                                            "request_purpose": "FIELD_NAVIGATION"})
    check("POST /resolve AD002936", status == 200 and moved.get("address_id") == "AD002936"
          and moved["eligibility"]["action"] == "VERIFY_FIRST" and moved.get("task") is not None,
          f"{moved.get('status')} r={moved.get('radius_m')} task={ (moved.get('task') or {}).get('task_id') }")

    # 4 · refusal is a product state, not an error
    status, ref = jget(base, "/resolve", {"address_text": AD_WORKLIKE, "town_hint": "T1", "as_of": MOMENT,
                                          "request_purpose": "NOTICE_SERVICE"})
    check("POST /resolve refusal (work-like place)", status == 200 and ref["eligibility"]["action"] == "REFUSE"
          and ref["coordinate"] is None and ref["uncertainty"] is None,
          f"reason={ref['eligibility']['reason']}, coordinate withheld")

    # 5 · deterministic repeated call
    s1, r1 = call(base, "/resolve", {"address_text": AD_GOOD, "town_hint": "T2", "as_of": MOMENT,
                                     "request_purpose": "FIELD_NAVIGATION"})
    s2, r2 = call(base, "/resolve", {"address_text": AD_GOOD, "town_hint": "T2", "as_of": MOMENT,
                                     "request_purpose": "FIELD_NAVIGATION"})
    check("repeated resolve is byte-identical", hashlib.sha256(r1).hexdigest() == hashlib.sha256(r2).hexdigest())

    # 6 · the read surface the console binds to
    status, geom = jget(base, f"/v1/geometry/AD002936?as_of={MOMENT}")
    check("GET /v1/geometry/AD002936", status == 200 and geom.get("coordinate_space") == "sutra_local_metric_plane:T2"
          and geom["counts"]["candidates"] > 0 and geom["extent"] is not None,
          f"{geom.get('counts')}, ring r={geom['rings'][0]['radius_m'] if geom.get('rings') else None}")

    status, bel = jget(base, f"/v1/belief/AD003067?as_of={MOMENT}")
    check("GET /v1/belief/AD003067", status == 200 and bel["belief"]["tier"] == "CONFIRMED"
          and bel["belief"]["support"]["independent_confirmations"] == 3,
          f"v{bel['belief']['belief_version']}, refs {len(bel.get('observation_refs', []))}")

    status, obs = jget(base, f"/v1/address/AD002936/observations?as_of={MOMENT}")
    negatives = [o for o in obs.get("observations", []) if o["polarity"] == "negative"]
    check("GET /v1/address/AD002936/observations", status == 200 and obs.get("count", 0) >= 6
          and all(o["coordinate_claim"] is False and o["x"] is None for o in negatives),
          f"{obs.get('count')} rows, {len(negatives)} negatives all non-claims, moves coordinate: {obs.get('negatives_move_coordinate')}")

    status, pl = jget(base, f"/v1/place/PL-AD002936?as_of={MOMENT}")
    check("GET /v1/place/PL-AD002936", status == 200 and pl.get("state") == "MOVED_SUSPECTED"
          and pl.get("contradictions_detail") and pl["contradictions_detail"][0]["coordinate_unchanged"] is True,
          f"{len(pl.get('versions', []))} stored versions, contradictions {pl.get('contradictions')}")

    status, tasks = jget(base, "/v1/tasks?town_id=T2&limit=5")
    check("GET /v1/tasks?town_id=T2", status == 200 and tasks.get("total_matching") == 84
          and tasks["facets"]["by_cause"] == {"MOVED_SUSPECTED": 84} and tasks.get("next_cursor"),
          f"{tasks.get('count')} of {tasks.get('total_matching')}, cursor {'present' if tasks.get('next_cursor') else 'absent'}")

    status, plane = jget(base, "/v1/plane/T2")
    check("GET /v1/plane/T2", status == 200 and plane.get("counts", {}).get("landmarks") == 77
          and plane["coordinate_space"].endswith(":T2"),
          f"{len(plane.get('points', []))} reference points")

    status, pack = jget(base, "/packs/T2")
    check("GET /packs/T2 (legacy)", status == 200 and pack.get("counts", {}).get("addresses", pack.get("n_addresses", 0)) or pack.get("pack_version"),
          f"pack {pack.get('pack_version')}")

    status, places = jget(base, f"/v1/places?limit=5&town_id=T2&as_of={MOMENT}")
    check("GET /v1/places (workbench projection)", status == 200 and places.get("total_matching", 0) > 900
          and places.get("identity_rule") == "colocation<=30m|adjudicated",
          f"{places.get('total_matching')} places in T2, identity rule from the service")

    status, ev = jget(base, f"/v1/evidence?limit=5&polarity=negative&as_of={MOMENT}")
    check("GET /v1/evidence (workbench projection)", status == 200 and ev.get("total_matching", 0) > 500
          and ev.get("negatives_move_coordinate") is False
          and all(row.get("coordinate_claim") is False for row in ev["items"] if row.get("polarity") == "negative"),
          f"{ev.get('total_matching')} negatives, none claims a coordinate")

    status, legacy = jget(base, f"/place/PL-AD003067?as_of={MOMENT}")
    check("GET /place/{id} (legacy read)", status == 200 and legacy.get("state") in ("CONFIRMED", "MOVED_SUSPECTED", "CONTESTED"),
          f"state {legacy.get('state')}")

    # 7 · error paths the console must handle
    status, err = jget(base, "/v1/tasks?cursor=%25%25garbage")
    check("bad cursor → 400", status == 400 and err.get("error") == "INVALID_REQUEST", str(err.get("detail"))[:60])
    status, err = jget(base, f"/v1/belief/AD999999?as_of={MOMENT}")
    check("unknown address → 404", status == 404 and err.get("error") == "unknown_address")
    status, err = jget(base, f"/v1/geometry/AD000006?as_of={MOMENT}")
    check("unplaceable geometry → withheld, no points", status == 200 and err.get("points") == []
          and err.get("withheld") is not None, f"withheld { (err.get('withheld') or {}).get('reason') }")

    failed = [r for r in _results if not r[0]]
    print(f"\n{len(_results) - len(failed)}/{len(_results)} checks passed")
    if failed:
        print("FAILED: " + "; ".join(f[1] for f in failed))
        return 1
    print("SMOKE TEST: ALL PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
