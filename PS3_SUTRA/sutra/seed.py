"""Seeding the store from the official visit history (an ingest, not a training run).

Every one of the 5,578 cleaned visits becomes an `ingest` observation with a deterministic id
(`obs-<visit_id>`), its own timestamp, GPS accuracy, dwell, outcome and media hash. That is what makes
the runtime *warm*: beliefs, memory and tasks are then computed from real evidence through exactly the
same code path a live capture uses. No model is fitted, no label is invented, and the seed is
reproducible: same inputs → same store bytes → same beliefs.

Trail agreement is precomputed in bulk (the cleaned trail features) and passed in, so the ingest does
not need an O(n²) duplicate-media scan.
"""
from __future__ import annotations

from collections import Counter

from . import asof, config, dataio
from .evidence import score_observation
from .store import Store

INGEST_ID = "ingest-official-ps3-field-visits-v3"   # v3: trace-tail coordinate policy


def bulk_duplicate_hashes() -> set[str]:
    """Photo hashes that appear more than once (the FA009 duplicate-media clusters)."""
    c = Counter(v.get("photo_hash") for v in dataio.visits() if v.get("photo_hash"))
    return {h for h, n in c.items() if n > 1}


COORD_TAIL_FIXES = 3          # how many trailing fixes form the dwell cluster


def trace_tail_point(trace: list[tuple] | None, checkin_x: float, checkin_y: float) -> tuple[float, float, str, int]:
    """Where did the visit happen? The trailing fixes of the official track, not one sample.

    A visit's track is the agent's approach; the last fixes are the ones taken at the address, and a
    single check-in sample carries the phone's instantaneous error (the official `gps_accuracy_m`
    has a 9.8 m median but a long tail). The median of the last few fixes is the same measurement
    with the sample noise averaged out. Measured on a non-circular temporal holdout (estimator from
    visits before a cut, judged against visits after it): P(<100 m) 0.7296 -> 0.8240, median error
    54.9 m -> 22.7 m. Falls back to the check-in whenever the track is missing or shorter than one fix.
    """
    pts = [(float(x), float(y)) for _, x, y, _ in (trace or [])][-COORD_TAIL_FIXES:]
    if not pts:
        return float(checkin_x), float(checkin_y), "checkin", 0
    xs = sorted(p[0] for p in pts)
    ys = sorted(p[1] for p in pts)
    mid = len(pts) // 2
    mx = xs[mid] if len(xs) % 2 else (xs[mid - 1] + xs[mid]) / 2.0
    my = ys[mid] if len(ys) % 2 else (ys[mid - 1] + ys[mid]) / 2.0
    return mx, my, "trace_tail%d" % len(pts), len(pts)


def visit_to_observation(v: dict, trail: dict | None, dup_hashes: set[str],
                         trace: list[tuple] | None = None) -> dict:
    media = [{"sha256": v["photo_hash"], "kind": "photo"}] if v.get("photo_hash") else []
    cx, cy, method, n_fixes = trace_tail_point(trace, v["checkin_x"], v["checkin_y"])
    obs = {
        "observation_id": f"obs-{v['visit_id']}",
        "kind": "ingest",
        "address_id": v["address_id"],
        "account_id": v["account_id"],
        "agent_id": v["agent_id"],
        "device_id": f"device-{v['agent_id']}",
        "outcome": v["outcome"],
        # the observation's coordinate is the dwell estimate; the raw check-in sample and the method
        # that replaced it travel with the observation as provenance (never silently overwritten)
        "checkin": {"x": cx, "y": cy,
                    "gps_accuracy_m": float(v["gps_accuracy_m"]) if v.get("gps_accuracy_m") else None},
        "coord_method": method,
        "coord_fixes": n_fixes,
        "checkin_sample": {"x": float(v["checkin_x"]), "y": float(v["checkin_y"])},
        "dwell_s": float(v["dwell_s"]) if v.get("dwell_s") else None,
        "observed_at": v["checkin_ts"] or v["visit_date"],
        "captured_at_device": v["checkin_ts"] or v["visit_date"],
        # Backfill semantics: the visit is already in the settled archive, so "received" is the archive's
        # own record time. Using the wall clock here would make a rebuild of history nondeterministic —
        # live captures keep a genuine receipt time (evidence.py).
        "server_received_at": v["checkin_ts"] or v["visit_date"],
        "local_seq": int(v["visit_id"][2:]) if v["visit_id"][2:].isdigit() else None,
        "media": media,
        "remark": v.get("remark"),
        "source": "official_ps3_field_visits",
    }
    if trail:
        obs["trail_agreement_m"] = float(trail["dist_checkin_to_median_m"]) if trail.get(
            "dist_checkin_to_median_m") not in (None, "") else None
        obs["trail_points"] = int(trail["n_points"]) if trail.get("n_points") not in (None, "") else None
    return obs


def seed(store: Store | None = None, limit: int | None = None, verbose: bool = False) -> dict:
    st = store or Store()
    already = st.conn.execute("SELECT COUNT(*) FROM ingest_log WHERE ingest_id = ?", (INGEST_ID,)).fetchone()[0]
    if already:
        return {"ingested": 0, "already": True, "n_observations": st.count("observations")}

    visits = dataio.visits()
    trails = dataio.trail_features()
    traces = dataio.visit_gps_traces()          # official approach tracks: the coordinate policy's input
    dups = bulk_duplicate_hashes()
    st.conn.execute("PRAGMA synchronous=OFF")
    n = 0
    for v in visits:
        if limit and n >= limit:
            break
        obs = visit_to_observation(v, trails.get(v["visit_id"]), dups, traces.get(v["visit_id"]))
        from .evidence import normalise_observation
        rec = normalise_observation(obs, None)
        st.append_observation(rec)
        ev = score_observation(rec, store=None, dup_hashes=dups)
        st.append_evidence(rec, ev["weight"], ev["polarity"], ev["evidence_class"], ev["reason_codes"],
                           ev["independence_tuple"], asof.to_utc_str(asof.now_utc()))
        n += 1
        if verbose and n % 1000 == 0:
            print(f"  seeded {n}/{len(visits)}")
    st.log_ingest(INGEST_ID, "official_ps3/cleaned field_visits", n, config.MOMENT,
                  {"source": "data/cleaned/visits_clean.csv", "policy": config.OUTCOME_CLASS,
                   "n_duplicate_media_hashes": len(dups), "deterministic_ids": "obs-<visit_id>",
                   "coord_policy": f"trace_tail{COORD_TAIL_FIXES} (fallback: checkin)",
                   "n_traces": len(traces)})
    st.conn.execute("PRAGMA synchronous=FULL")
    return {"ingested": n, "already": False, "n_observations": st.count("observations")}
