"""The append-only store — authoritative persistence (contract §5, M3).

Design rules this file obeys, and which the acceptance tests check mechanically:

* **Append-only.** There is no UPDATE and no DELETE in this module. Corrections arrive as new
  observations; tasks and places change by appending events; the test-look counter is a row count.
* **Idempotent writes.** `submit_observation` is keyed by the client-generated observation id
  (the idempotency key). Replaying it returns the *original* receipt and stores nothing new.
* **Deterministic payloads.** Every stored payload is canonical JSON (sorted keys, no whitespace) and
  carries its own sha256, so a re-derivation can be compared byte-for-byte.
* **Server-authoritative versions.** Belief versions are computed server-side from the store; a
  client never proposes a belief.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import threading
from typing import Any, Iterable, Sequence

from . import asof, config
from .version import EVIDENCE_POLICY_VERSION, STORE_SCHEMA_VERSION

SCHEMA = """
CREATE TABLE IF NOT EXISTS observations (
  observation_id TEXT PRIMARY KEY,
  kind TEXT NOT NULL,
  address_id TEXT, account_id TEXT, agent_id TEXT, device_id TEXT,
  outcome TEXT, evidence_class TEXT, polarity TEXT,
  x REAL, y REAL, gps_accuracy_m REAL, dwell_s REAL,
  observed_at TEXT NOT NULL, captured_at_device TEXT, server_received_at TEXT,
  local_seq INTEGER, tz_offset_minutes INTEGER, town_id TEXT,
  media_json TEXT, remark TEXT,
  duplicate_claim_of TEXT, idempotency_key TEXT, policy_version TEXT,
  payload_json TEXT NOT NULL, payload_sha256 TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_obs_addr_at ON observations(address_id, observed_at);
CREATE INDEX IF NOT EXISTS ix_obs_at ON observations(observed_at);
CREATE INDEX IF NOT EXISTS ix_obs_town ON observations(town_id, observed_at);

CREATE TABLE IF NOT EXISTS evidence_scores (
  observation_id TEXT NOT NULL, policy_version TEXT NOT NULL,
  weight REAL NOT NULL, polarity TEXT NOT NULL, evidence_class TEXT NOT NULL,
  reason_codes_json TEXT NOT NULL, independence_json TEXT NOT NULL,
  computed_at TEXT NOT NULL, payload_json TEXT NOT NULL, payload_sha256 TEXT NOT NULL,
  PRIMARY KEY (observation_id, policy_version)
);

CREATE TABLE IF NOT EXISTS belief_versions (
  address_id TEXT NOT NULL, belief_version INTEGER NOT NULL, as_of TEXT NOT NULL,
  rules_version TEXT NOT NULL DEFAULT '', evidence_policy_version TEXT NOT NULL DEFAULT '',
  radius_map_version TEXT NOT NULL DEFAULT '',
  candidate_id TEXT, tier TEXT, status TEXT, payload_json TEXT NOT NULL, payload_sha256 TEXT NOT NULL,
  computed_at TEXT NOT NULL, PRIMARY KEY (address_id, belief_version, as_of, rules_version)
);

CREATE TABLE IF NOT EXISTS place_events (
  event_id TEXT PRIMARY KEY, place_id TEXT NOT NULL, kind TEXT NOT NULL, address_id TEXT,
  at TEXT NOT NULL, reason TEXT, payload_json TEXT NOT NULL, payload_sha256 TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_place_events ON place_events(place_id, at);

CREATE TABLE IF NOT EXISTS place_members (
  place_id TEXT NOT NULL, address_id TEXT NOT NULL, link_event_id TEXT, linked_at TEXT NOT NULL,
  identity_rule TEXT, PRIMARY KEY (place_id, address_id)
);

CREATE TABLE IF NOT EXISTS task_events (
  event_id TEXT PRIMARY KEY, task_id TEXT NOT NULL, address_id TEXT, place_id TEXT, town_id TEXT,
  kind TEXT NOT NULL, priority REAL, reason TEXT, at TEXT NOT NULL,
  payload_json TEXT NOT NULL, payload_sha256 TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_task_events ON task_events(town_id, kind, at);

CREATE TABLE IF NOT EXISTS receipts (
  idempotency_key TEXT PRIMARY KEY, observation_id TEXT NOT NULL, received_at TEXT NOT NULL,
  payload_json TEXT NOT NULL, payload_sha256 TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS held_observations (
  observation_id TEXT NOT NULL, state TEXT NOT NULL, device_id TEXT, local_seq INTEGER,
  held_since TEXT NOT NULL, released_at TEXT, payload_json TEXT NOT NULL, payload_sha256 TEXT NOT NULL,
  PRIMARY KEY (observation_id, state)
);

CREATE TABLE IF NOT EXISTS counter_events (
  name TEXT NOT NULL, at TEXT NOT NULL, detail TEXT
);

CREATE TABLE IF NOT EXISTS ingest_log (
  ingest_id TEXT PRIMARY KEY, source TEXT NOT NULL, rows INTEGER, at TEXT NOT NULL,
  payload_json TEXT NOT NULL, payload_sha256 TEXT NOT NULL
);
"""


# ── canonical serialisation ─────────────────────────────────────────────────────────────────────
def canonical_json(obj: Any) -> str:
    """Canonical JSON: sorted keys, no insignificant whitespace, UTF-8 preserved."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canonical_payload(obj: Any) -> tuple[str, str]:
    j = canonical_json(obj)
    return j, sha256_text(j)


class DeterminismViolation(RuntimeError):
    """Raised when a re-derived artefact is not byte-identical to the stored one."""


class Store:
    """SQLite-backed, append-only. One process, one file; no server, no network.

    **Thread-safe by construction**: every thread gets its own connection to the same file (sqlite's
    supported model), in WAL mode so readers never block the writer. This is what lets the threaded
    HTTP runtime serve `/health`, `/resolve` and `/evidence` concurrently off one `Store` object.
    """

    def __init__(self, path: str | None = None, create: bool = True):
        self.path = path or config.STORE_PATH
        self._local = threading.local()
        if create:
            os.makedirs(os.path.dirname(os.path.abspath(self.path)), exist_ok=True)
        self._conn()                     # materialise the schema on the calling thread

    def _conn(self) -> sqlite3.Connection:
        """The calling thread's connection (created on first use, schema is idempotent)."""
        c = getattr(self._local, "conn", None)
        if c is None:
            c = sqlite3.connect(self.path, timeout=30.0)
            c.row_factory = sqlite3.Row
            c.execute("PRAGMA journal_mode=WAL")
            c.execute("PRAGMA busy_timeout=30000")
            c.executescript(SCHEMA)
            c.commit()
            self._local.conn = c
        return c

    @property
    def conn(self) -> sqlite3.Connection:
        return self._conn()

    @staticmethod
    def reset(path: str) -> list[str]:
        """Delete a store **and its WAL sidecars**.

        Removing only the `.sqlite` file leaves `-wal`/`-shm` behind, and sqlite then rejects the
        recreated file with a bare `disk I/O error` — a rebuild that looks like corruption but is
        just a stale journal. Every caller that resets a store goes through here.
        """
        gone = []
        for suffix in ("", "-wal", "-shm"):
            p = path + suffix
            if os.path.exists(p):
                os.remove(p)
                gone.append(os.path.basename(p))
        return gone

    # ── lifecycle ───────────────────────────────────────────────────────────────────────────────
    def close(self):
        c = getattr(self._local, "conn", None)
        if c is not None:
            c.close()
            self._local.conn = None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def meta(self) -> dict:
        return {"store_path": os.path.basename(self.path), "store_schema_version": STORE_SCHEMA_VERSION,
                "evidence_policy_version": EVIDENCE_POLICY_VERSION,
                "n_observations": self.count("observations")}

    def count(self, table: str) -> int:
        return int(self.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])

    # ── reads (all filtering goes through asof) ─────────────────────────────────────────────────
    @staticmethod
    def _row(r: sqlite3.Row) -> dict:
        """Rows come back with their `*_json` columns parsed (`independence`, `reason_codes`, `media`)."""
        d = dict(r)
        for k in [k for k in d if k.endswith("_json")]:
            if d[k]:
                try:
                    d[k[:-5]] = json.loads(d[k])
                except json.JSONDecodeError:
                    pass
        return d

    def observations_upto(self, as_of, address_id=None, town_id=None, kinds=None) -> list[dict]:
        """As-of read: strictly-before the cut-point — the only temporal filter in SUTRA."""
        sql = "SELECT * FROM observations WHERE observed_at < ?"   # asof-backend (asof.observations_upto)
        params: list[Any] = [asof.to_utc_str(as_of)]
        if address_id:
            sql += " AND address_id = ?"
            params.append(address_id)
        if town_id:
            sql += " AND town_id = ?"
            params.append(town_id)
        if kinds:
            sql += " AND kind IN (%s)" % ",".join("?" * len(kinds))
            params.extend(kinds)
        sql += " ORDER BY observed_at, local_seq, observation_id"
        return [self._row(r) for r in self.conn.execute(sql, params)]

    def get_observation(self, observation_id: str) -> dict | None:
        r = self.conn.execute("SELECT * FROM observations WHERE observation_id = ?", (observation_id,)).fetchone()
        return self._row(r) if r else None

    def evidence_for(self, observation_ids: Sequence[str], policy_version: str | None = None) -> dict[str, dict]:
        pv = policy_version or EVIDENCE_POLICY_VERSION
        out: dict[str, dict] = {}
        ids = list(observation_ids)
        for i in range(0, len(ids), 400):
            chunk = ids[i:i + 400]
            q = "SELECT * FROM evidence_scores WHERE policy_version = ? AND observation_id IN (%s)" % ",".join("?" * len(chunk))
            for r in self.conn.execute(q, [pv] + chunk):
                d = self._row(r)
                out[d["observation_id"]] = d
        return out

    def latest_belief_before(self, address_id: str, as_of, rules_version: str | None = None) -> dict | None:
        """The newest belief **strictly before** `as_of` — the memory arm's prior, and never the belief
        being computed (a belief may not be its own evidence). Filtering goes through the as-of gate.

        `rules_version` defaults to the current one, so the memory arm never reads a belief computed by
        a superseded rule set (belief rows are version-scoped; §12, M3).
        """
        from .version import RULE_VERSION
        rv = rules_version or RULE_VERSION
        prior = asof.rows_upto([b for b in self.belief_versions(address_id)
                                if b.get("rules_version") == rv], as_of, ts_field="as_of")
        return prior[-1] if prior else None

    def latest_belief(self, address_id: str, as_of=None) -> dict | None:
        sql = "SELECT * FROM belief_versions WHERE address_id = ?"
        params: list[Any] = [address_id]
        if as_of is not None:
            sql += " AND as_of <= ?"        # asof-backend (inclusive read for the /place projection)
            params.append(asof.to_utc_str(as_of))
        sql += " ORDER BY as_of DESC, belief_version DESC LIMIT 1"
        r = self.conn.execute(sql, params).fetchone()
        if not r:
            return None
        d = self._row(r)
        d["payload"] = json.loads(d["payload_json"])
        return d

    def belief_versions(self, address_id: str) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM belief_versions WHERE address_id = ? ORDER BY as_of, belief_version",
            (address_id,)).fetchall()
        out = []
        for r in rows:
            d = self._row(r)
            d["payload"] = json.loads(d["payload_json"])
            out.append(d)
        return out

    def receipt_for(self, idempotency_key: str) -> dict | None:
        r = self.conn.execute("SELECT * FROM receipts WHERE idempotency_key = ?", (idempotency_key,)).fetchone()
        return json.loads(r["payload_json"]) if r else None

    def place_events(self, place_id: str) -> list[dict]:
        return [self._row(r) for r in self.conn.execute(
            "SELECT * FROM place_events WHERE place_id = ? ORDER BY at, event_id", (place_id,))]

    def place_members(self, place_id: str) -> list[dict]:
        return [self._row(r) for r in self.conn.execute(
            "SELECT * FROM place_members WHERE place_id = ? ORDER BY address_id", (place_id,))]

    def members_of_address(self, address_id: str) -> list[str]:
        return [r[0] for r in self.conn.execute(
            "SELECT place_id FROM place_members WHERE address_id = ? ORDER BY place_id", (address_id,))]

    def task_events(self, town_id: str | None = None, kind: str | None = None) -> list[dict]:
        sql, params = "SELECT * FROM task_events WHERE 1=1", []
        if town_id:
            sql += " AND town_id = ?"; params.append(town_id)
        if kind:
            sql += " AND kind = ?"; params.append(kind)
        sql += " ORDER BY at, event_id"
        return [self._row(r) for r in self.conn.execute(sql, params)]

    # ── writes (append only) ────────────────────────────────────────────────────────────────────
    def append_observation(self, obs: dict) -> None:
        payload_json, payload_sha = canonical_payload(obs)
        self.conn.execute(
            "INSERT INTO observations (observation_id, kind, address_id, account_id, agent_id, device_id,"
            " outcome, evidence_class, polarity, x, y, gps_accuracy_m, dwell_s, observed_at,"
            " captured_at_device, server_received_at, local_seq, tz_offset_minutes, town_id, media_json,"
            " remark, duplicate_claim_of, idempotency_key, policy_version, payload_json, payload_sha256)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (obs["observation_id"], obs["kind"], obs.get("address_id"), obs.get("account_id"),
             obs.get("agent_id"), obs.get("device_id"), obs.get("outcome"),
             obs.get("evidence_class"), obs.get("polarity"), obs.get("x"), obs.get("y"),
             obs.get("gps_accuracy_m"), obs.get("dwell_s"), obs["observed_at"],
             obs.get("captured_at_device"), obs.get("server_received_at"), obs.get("local_seq"),
             obs.get("tz_offset_minutes"), obs.get("town_id"),
             json.dumps(obs.get("media", []), ensure_ascii=False), obs.get("remark"),
             obs.get("duplicate_claim_of"), obs.get("idempotency_key"),
             obs.get("policy_version", EVIDENCE_POLICY_VERSION), payload_json, payload_sha))
        self.conn.commit()

    def append_evidence(self, obs: dict, weight: float, polarity: str, evidence_class: str,
                        reason_codes: Iterable[str], independence: dict, computed_at: str) -> dict:
        payload = {"observation_id": obs["observation_id"], "policy_version": obs.get("policy_version",
                                                                                     EVIDENCE_POLICY_VERSION),
                   "weight": round(float(weight), 6), "polarity": polarity, "evidence_class": evidence_class,
                   "reason_codes": sorted(set(reason_codes)), "independence": independence}
        pj, ph = canonical_payload(payload)
        self.conn.execute(
            "INSERT OR IGNORE INTO evidence_scores (observation_id, policy_version, weight, polarity,"
            " evidence_class, reason_codes_json, independence_json, computed_at, payload_json, payload_sha256)"
            " VALUES (?,?,?,?,?,?,?,?,?,?)",
            (payload["observation_id"], payload["policy_version"], payload["weight"], polarity,
             evidence_class, json.dumps(payload["reason_codes"]), json.dumps(independence, sort_keys=True),
             computed_at, pj, ph))
        self.conn.commit()
        return payload

    def append_belief(self, address_id: str, belief: dict, computed_at: str) -> dict:
        """Append a belief version **scoped to the rule set that produced it**.

        Re-deriving under the *same* versions must reproduce the payload byte-for-byte — if it does not,
        the store refuses the write (`DeterminismViolation`). Re-deriving under a *newer* rule set is a
        migration, not a violation: it lands as its own row, leaving the older row intact, because a
        belief is a recomputable projection of the immutable evidence and history is never patched (§12).
        """
        cf = belief.get("computed_from", {})
        rv = cf.get("rule_version", "")
        pj, ph = canonical_payload(belief)
        prior = self.conn.execute(
            "SELECT payload_sha256 FROM belief_versions WHERE address_id = ? AND belief_version = ?"
            " AND as_of = ? AND rules_version = ?",
            (address_id, int(belief["belief_version"]), belief["as_of"], rv)).fetchone()
        if prior is not None and prior[0] != ph:
            raise DeterminismViolation(
                f"belief {address_id} v{belief['belief_version']}@{belief['as_of']} [{rv}] re-derived differently")
        self.conn.execute(
            "INSERT OR IGNORE INTO belief_versions (address_id, belief_version, as_of, rules_version,"
            " evidence_policy_version, radius_map_version, candidate_id, tier, status, payload_json,"
            " payload_sha256, computed_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (address_id, int(belief["belief_version"]), belief["as_of"], rv,
             cf.get("policy", ""), cf.get("radius_map_version", ""), belief.get("candidate_id"),
             belief.get("tier"), belief.get("status"), pj, ph, computed_at))
        self.conn.commit()
        return {"payload_sha256": ph, "belief_version": belief["belief_version"], "rules_version": rv}

    def belief_versions_by_rules(self) -> dict[str, int]:
        """How many stored belief rows exist per rule set — the migration view for the report."""
        return {r[0]: int(r[1]) for r in self.conn.execute(
            "SELECT rules_version, COUNT(*) FROM belief_versions GROUP BY rules_version ORDER BY 1")}

    def append_place_event(self, event_id: str, place_id: str, kind: str, address_id: str | None,
                           at: str, reason: str, payload: dict) -> None:
        pj, ph = canonical_payload(payload)
        self.conn.execute(
            "INSERT INTO place_events (event_id, place_id, kind, address_id, at, reason, payload_json,"
            " payload_sha256) VALUES (?,?,?,?,?,?,?,?)",
            (event_id, place_id, kind, address_id, asof.to_utc_str(at), reason, pj, ph))
        self.conn.commit()

    def link_place_member(self, place_id: str, address_id: str, link_event_id: str, at: str,
                          identity_rule: str) -> None:
        self.conn.execute(
            "INSERT OR IGNORE INTO place_members (place_id, address_id, link_event_id, linked_at, identity_rule)"
            " VALUES (?,?,?,?,?)",
            (place_id, address_id, link_event_id, asof.to_utc_str(at), identity_rule))
        self.conn.commit()

    def append_task_event(self, event_id: str, task_id: str, kind: str, at: str, payload: dict,
                          address_id: str | None = None, place_id: str | None = None,
                          town_id: str | None = None, priority: float | None = None,
                          reason: str | None = None) -> None:
        pj, ph = canonical_payload(payload)
        self.conn.execute(
            "INSERT OR IGNORE INTO task_events (event_id, task_id, address_id, place_id, town_id, kind,"
            " priority, reason, at, payload_json, payload_sha256) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (event_id, task_id, address_id, place_id, town_id, kind, priority, reason,
             asof.to_utc_str(at), pj, ph))
        self.conn.commit()

    def put_receipt(self, idempotency_key: str, observation_id: str, received_at: str, receipt: dict) -> None:
        pj, ph = canonical_payload(receipt)
        self.conn.execute(
            "INSERT OR IGNORE INTO receipts (idempotency_key, observation_id, received_at, payload_json,"
            " payload_sha256) VALUES (?,?,?,?,?)",
            (idempotency_key, observation_id, received_at, pj, ph))
        self.conn.commit()

    def hold_observation(self, observation_id: str, device_id: str | None, local_seq: int | None,
                         held_since: str, state: str, payload: dict, released_at: str | None = None) -> None:
        pj, ph = canonical_payload(payload)
        self.conn.execute(
            "INSERT OR IGNORE INTO held_observations (observation_id, state, device_id, local_seq, held_since,"
            " released_at, payload_json, payload_sha256) VALUES (?,?,?,?,?,?,?,?)",
            (observation_id, state, device_id, local_seq, asof.to_utc_str(held_since),
             asof.to_utc_str(released_at) if released_at else None, pj, ph))
        self.conn.commit()

    def held_state(self, observation_id: str) -> str | None:
        rows = [r[0] for r in self.conn.execute(
            "SELECT state FROM held_observations WHERE observation_id = ? ORDER BY held_since", (observation_id,))]
        if not rows:
            return None
        return "released" if "released" in rows else ("conflict" if "conflict" in rows else "held")

    def release_held(self, observation_id: str, at: str) -> None:
        """Promote a held observation by appending a `released` row (never by editing the held row)."""
        r = self.conn.execute(
            "SELECT * FROM held_observations WHERE observation_id = ? AND state = 'held'", (observation_id,)).fetchone()
        if not r:
            return
        self.hold_observation(observation_id, r["device_id"], r["local_seq"], r["held_since"], "released",
                              json.loads(r["payload_json"]), released_at=at)

    def held_since(self, observation_id: str) -> str | None:
        r = self.conn.execute("SELECT MIN(held_since) FROM held_observations WHERE observation_id = ?",
                              (observation_id,)).fetchone()
        return r[0] if r else None

    def max_local_seq(self, device_id: str | None) -> int:
        q = self.conn.execute(
            "SELECT MAX(local_seq) FROM observations WHERE device_id IS ?", (device_id,)).fetchone()[0]
        return int(q) if q is not None else -1

    def counters(self, name: str) -> int:
        return int(self.conn.execute("SELECT COUNT(*) FROM counter_events WHERE name = ?", (name,)).fetchone()[0])

    def bump_counter(self, name: str, at: str | None = None, detail: str | None = None) -> int:
        when = asof.to_utc_str(at) if at else asof.to_utc_str(asof.now_utc())
        self.conn.execute("INSERT INTO counter_events (name, at, detail) VALUES (?,?,?)", (name, when, detail))
        self.conn.commit()
        return self.counters(name)

    def log_ingest(self, ingest_id: str, source: str, rows: int, at: str, payload: dict) -> None:
        pj, ph = canonical_payload(payload)
        self.conn.execute(
            "INSERT OR IGNORE INTO ingest_log (ingest_id, source, rows, at, payload_json, payload_sha256)"
            " VALUES (?,?,?,?,?,?)", (ingest_id, source, rows, asof.to_utc_str(at), pj, ph))
        self.conn.commit()

    def attestation(self) -> dict:
        """A cheap fingerprint of the whole store: row counts + payload hashes (order-independent)."""
        fp = {}
        for table in ("observations", "evidence_scores", "belief_versions", "place_events", "task_events"):
            rows = [r[0] for r in self.conn.execute(f"SELECT payload_sha256 FROM {table} ORDER BY 1")]
            fp[table] = {"n": len(rows), "digest": sha256_text("".join(rows))}
        return fp


# ── the frozen write entry point (contract §3) ──────────────────────────────────────────────────
_WRITE_LOCK = threading.Lock()          # one in-process writer at a time; the file stays consistent

_DELTA_FIELDS = ("tier", "status", "candidate_id", "radius_m")


def _belief_summary(belief: dict | None) -> dict | None:
    """The four things the interface shows about a belief state. Presentational, never persisted."""
    if not belief:
        return None
    return {"as_of": belief.get("as_of"), "tier": belief.get("tier"), "status": belief.get("status"),
            "candidate_id": belief.get("candidate_id"),
            "radius_m": (belief.get("radius") or {}).get("radius_m"),
            "belief_version": belief.get("belief_version")}


def _changed(before: dict | None, after: dict | None) -> dict:
    """Which of the four decision fields this observation moved — and nothing else is claimed."""
    if not before or not after:
        return {"changed": None, "fields": {}, "note": "belief not defined before the write"}
    fields = {}
    for k in _DELTA_FIELDS:
        b = before.get(k) if k != "radius_m" else (before.get("radius") or {}).get("radius_m")
        a = after.get(k) if k != "radius_m" else (after.get("radius") or {}).get("radius_m")
        if b != a:
            fields[k] = {"before": b, "after": a}
    return {"changed": bool(fields), "fields": fields}


def submit_observation(obs: dict, idempotency_key: str, store: Store | None = None) -> dict:
    """Append an observation. Idempotent; the only write path into the store.

    Returns an `ObservationReceipt`. Replaying the same idempotency key returns the original receipt
    unchanged (`DUPLICATE_OBSERVATION`), and a second device claiming the same visit is stored as a
    linked duplicate claim — never as a second confirmation (F2.2, contract §5).
    """
    from . import evidence as evidence_mod   # local import: evidence -> store -> evidence is a cycle

    st = store or Store()
    key = idempotency_key or obs.get("observation_id")
    with _WRITE_LOCK:            # the receipt check and the append must not interleave (idempotency, §5)
        prior = st.receipt_for(key)
        if prior is not None:
            prior = dict(prior)
            prior["replayed"] = True
            prior["state"] = "DUPLICATE_OBSERVATION"
            return prior

        rec = evidence_mod.normalise_observation(obs, st)      # validates, derives class/polarity, adds observed_at
        # P0-8: the state the operator's system would have served *before* this visit. A pure read of
        # the same belief function at the canonical instant for this observation's own timestamp —
        # it cannot see the row that has not been appended yet, so nothing about it is a guess.
        from .belief import belief_instant, compute_belief, recompute_belief
        before = None
        try:
            before = compute_belief(rec["address_id"], belief_instant(st, rec["address_id"],
                                                                     as_of=rec["observed_at"]), st)
        except KeyError:            # an address outside the index: the belief is simply not defined
            before = None
        tasks_before = {e["task_id"] for e in st.task_events()}
        st.append_observation(rec)
        ev = evidence_mod.score_observation(rec, st)
        st.append_evidence(rec, ev["weight"], ev["polarity"], ev["evidence_class"], ev["reason_codes"],
                           ev["independence_tuple"], asof.to_utc_str(asof.now_utc()))
        # a negative or a change in support may create a verification task; the belief is recomputed below
        belief = recompute_belief(rec["address_id"], st, as_of=None, persist=True, trigger=rec)
        added_tasks = sorted({e["task_id"] for e in st.task_events()} - tasks_before)
    receipt = {
        "observation_id": rec["observation_id"], "state": rec.get("state", "STORED"),
        "duplicate_claim_of": rec.get("duplicate_claim_of"),
        "evidence": {"weight": ev["weight"], "polarity": ev["polarity"], "reasons": ev["reason_codes"]},
        "belief_version": belief["belief_version"], "tier": belief["tier"], "status": belief["status"],
        "coordinate": (belief.get("candidate") or {}).get("x"),
        "address_id": rec["address_id"],
        "server_received_at": rec["server_received_at"], "replayed": False,
        "policy_version": rec["policy_version"],
        # ── P0-8 additive: what the visit changed, as a projection of two pure belief computations ──
        "belief_before": _belief_summary(before),
        "belief_after": _belief_summary(belief),
        "changed": _changed(before, belief),
        "task_delta": {"added": added_tasks, "reopened": False,
                       "note": "task state transitions are P1; ingest can only raise a task"},
    }
    st.put_receipt(key, rec["observation_id"], rec["server_received_at"], receipt)
    return receipt
