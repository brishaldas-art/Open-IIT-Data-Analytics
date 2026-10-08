"""The offline field MVP (P11): pack → airplane mode → capture → durable outbox → replay.

Deliberately *not* built here: distributed production sync (that stays RED). What is built is the
minimal contract [S81][S82]:

* the device keeps its own SQLite database — append-only on the device too (the outbox is a log, and a
  delivery is recorded by appending an attempt row, never by editing evidence);
* every capture gets a client-generated id and a monotonic `local_seq`;
* capture works with the network off (nothing in this module touches a socket);
* on reconnect the outbox drains in `local_seq` order, each item idempotent by its observation id;
* the server recomputes the belief after replay — the device never proposes a belief.
"""
from __future__ import annotations

import json
import os
import sqlite3

from . import asof, config
from .store import canonical_payload

DEVICE_SCHEMA = """
CREATE TABLE IF NOT EXISTS outbox (
  observation_id TEXT PRIMARY KEY, local_seq INTEGER NOT NULL, captured_at TEXT NOT NULL,
  observed_at TEXT NOT NULL, payload_json TEXT NOT NULL, payload_sha256 TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS pack (
  pack_version TEXT PRIMARY KEY, town_id TEXT, payload_json TEXT NOT NULL, sha256 TEXT NOT NULL,
  downloaded_at TEXT
);
CREATE TABLE IF NOT EXISTS local_evidence (
  observation_id TEXT PRIMARY KEY, payload_json TEXT NOT NULL, captured_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS attempt_log (
  observation_id TEXT NOT NULL, attempt INTEGER, at TEXT, result TEXT
);
"""


class OfflineDevice:
    """A field device with a durable, append-only outbox. No network call anywhere in this class."""

    def __init__(self, device_id: str, path: str | None = None):
        self.device_id = device_id
        self.path = path or os.path.join(config.RUNTIME, f"device_{device_id}.sqlite")
        os.makedirs(os.path.dirname(os.path.abspath(self.path)), exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(DEVICE_SCHEMA)
        self.conn.commit()
        self.airplane_mode = True          # the field demo starts with no network

    # ── pack ────────────────────────────────────────────────────────────────────────────────────
    def download_pack(self, pack: dict, at=None) -> dict:
        from .packs import verify_pack
        v = verify_pack(pack)
        if not v["ok"]:
            return {"ok": False, "reason": "pack_hash_mismatch", "pack_sha256": v["pack_sha256"]}
        pj, ph = canonical_payload(pack)
        self.conn.execute("INSERT OR REPLACE INTO pack (pack_version, town_id, payload_json, sha256,"
                          " downloaded_at) VALUES (?,?,?,?,?)",
                          (pack["pack_version"], pack["town_id"], pj, ph,
                           asof.to_utc_str(at or asof.now_utc())))
        self.conn.commit()
        return {"ok": True, "pack_version": pack["pack_version"], "town_id": pack["town_id"],
                "valid_until": pack["valid_until"], "verify": v}

    def local_pack(self, town_id: str) -> dict | None:
        r = self.conn.execute("SELECT payload_json FROM pack WHERE town_id = ? ORDER BY pack_version DESC"
                              " LIMIT 1", (town_id,)).fetchone()
        return json.loads(r["payload_json"]) if r else None

    # ── capture ─────────────────────────────────────────────────────────────────────────────────
    def next_local_seq(self) -> int:
        r = self.conn.execute("SELECT MAX(local_seq) FROM outbox").fetchone()[0]
        return int(r or 0) + 1

    def capture(self, observation: dict, *, offline: bool | None = None) -> dict:
        """Capture evidence in the field. Works with the network off; queues into the outbox."""
        offline = self.airplane_mode if offline is None else offline
        seq = int(observation.get("local_seq") or self.next_local_seq())
        rec = dict(observation)
        rec["local_seq"] = seq
        rec["device_id"] = self.device_id
        rec["captured_at_device"] = rec.get("captured_at_device") or asof.to_utc_str(asof.now_utc())
        rec["observed_at"] = rec.get("observed_at") or rec["captured_at_device"]
        rec.setdefault("observation_id", f"{self.device_id}-{seq:05d}")
        pj, ph = canonical_payload(rec)
        self.conn.execute("INSERT OR IGNORE INTO outbox (observation_id, local_seq, captured_at, observed_at,"
                          " payload_json, payload_sha256) VALUES (?,?,?,?,?,?)",
                          (rec["observation_id"], seq, rec["captured_at_device"], rec["observed_at"], pj, ph))
        self.conn.execute("INSERT OR IGNORE INTO local_evidence (observation_id, payload_json, captured_at)"
                          " VALUES (?,?,?)", (rec["observation_id"], pj, rec["captured_at_device"]))
        self.conn.commit()
        return {"observation_id": rec["observation_id"], "local_seq": seq, "queued": True,
                "offline": bool(offline), "state": "queued_local", "payload_sha256": ph}

    # ── outbox views (derived from the logs; nothing is edited) ──────────────────────────────────
    def _acked(self) -> set[str]:
        rows = self.conn.execute("SELECT DISTINCT observation_id FROM attempt_log WHERE result NOT IN"
                                 " ('still_offline','error')").fetchall()
        return {r[0] for r in rows}

    def outbox(self, state: str | None = None) -> list[dict]:
        acked = self._acked()
        rows = [dict(r) for r in self.conn.execute("SELECT * FROM outbox ORDER BY local_seq")]
        if state == "queued":
            return [r for r in rows if r["observation_id"] not in acked]
        if state == "synced":
            return [r for r in rows if r["observation_id"] in acked]
        return rows

    def capture_looks_queued(self) -> int:
        return len(self.outbox("queued"))

    # ── replay ──────────────────────────────────────────────────────────────────────────────────
    def replay(self, server_store, *, at=None) -> dict:
        """Drain the outbox into the server store, in `local_seq` order, idempotently."""
        at = at or asof.now_utc()
        results = []
        if self.airplane_mode:
            return {"device_id": self.device_id, "drained": 0, "airplane_mode": True,
                    "queue_left": self.capture_looks_queued(),
                    "reason": "network still off — the outbox holds the evidence"}
        from .store import submit_observation
        attempt = 1 + int(self.conn.execute("SELECT COUNT(*) FROM attempt_log").fetchone()[0])
        for item in self.outbox("queued"):
            payload = json.loads(item["payload_json"])
            receipt = submit_observation(payload, idempotency_key=payload["observation_id"],
                                         store=server_store)
            self.conn.execute("INSERT INTO attempt_log (observation_id, attempt, at, result)"
                              " VALUES (?,?,?,?)",
                              (payload["observation_id"], attempt, asof.to_utc_str(at), receipt["state"]))
            self.conn.commit()
            results.append({"observation_id": payload["observation_id"], "local_seq": item["local_seq"],
                            "state": receipt["state"], "belief_version": receipt.get("belief_version"),
                            "tier": receipt.get("tier"), "status": receipt.get("status"),
                            "replayed": receipt.get("replayed", False)})
        return {"device_id": self.device_id, "drained": len(results), "airplane_mode": False,
                "results": results, "queue_left": self.capture_looks_queued()}
