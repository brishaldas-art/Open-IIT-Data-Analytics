"""The HTTP surface (contract §11) on the standard library only — no framework, no network egress.

    POST /resolve                    {address_text, town_hint?, as_of?, request_purpose}
    POST /evidence                   {observation…, idempotency_key}   -> 202 + receipt
    GET  /place/{id}?as_of=          belief + state + history + versions + contradictions
    GET  /tasks/verify-first?town_id=          (legacy queue read, unchanged)
    GET  /packs/{town_id}
    GET  /                           the SUTRA console when a built frontend is present, else a
                                     small read-only page (the console is static; the API is unchanged)
    GET  /health                     runtime status (versions, store, packs, gauges, counters)

Contract-v1 read surface (P0, additive — see SUTRA_FRONTEND_BACKEND_CONTRACT_V1_2026-10-08.md):

    GET  /v1/belief/{address_id}?as_of=            the authoritative belief object
    GET  /v1/address/{address_id}/observations?as_of=   the evidence timeline
    GET  /v1/tasks?town_id=&cause=&state=&as_of=&limit=&cursor=   queue + facets
    GET  /v1/geometry/{address_id}?as_of=&town_id=&request_purpose=   address-scoped plane payload
    GET  /v1/plane/{town_id}?as_of=                town reference geometry (localities, landmarks)
    GET  /v1/plane/address/{address_id}?as_of=     alias of /v1/geometry/{address_id}
    GET  /v1/place/{place_id}?as_of=               alias of /place/{id}
    GET  /v1/health                                alias of /health
    GET  /v1/places?as_of=&q=&state=&tier=&town_id=&limit=&cursor=   place list (projection)
    GET  /v1/evidence?as_of=&q=&outcome=&polarity=&town_id=&limit=&cursor=   visit feed

Errors follow §14: a refusal is a 200 with a decision in it; a malformed request is a 400 with no
partial belief. Nothing here calls out to the network.
"""
from __future__ import annotations

import json
import mimetypes
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from . import asof, config, feeds, packs as packs_mod, product, purpose as purpose_mod, views
from .memory import verify_first_tasks
from .resolve import explain, resolve
from .store import Store, submit_observation
from .version import ALL as VERSIONS

_STORE: Store | None = None
_LOCK = threading.Lock()

# The console build (web/site) is served from this same process: one origin, no CORS, no second host.
# Absent the build, the legacy read-only page at "/" is served exactly as before.
_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB_ROOT = os.path.join(_REPO, "web", "site")            # the console build (reference)
BM_ROOT = os.path.join(_REPO, "battle_model", "site")    # the deployed workbench build


def _web_root() -> str:
    """The frontend served at `/`: the workbench build when it exists, else the console build."""
    return BM_ROOT if os.path.isfile(os.path.join(BM_ROOT, "index.html")) else WEB_ROOT
_CACHE_IMMUTABLE = "public, max-age=31536000, immutable"
_CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8", ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
    ".ico": "image/x-icon", ".woff2": "font/woff2", ".woff": "font/woff", ".map": "application/json",
    ".txt": "text/plain; charset=utf-8", ".webmanifest": "application/manifest+json",
}


def _static_file(rel: str) -> tuple[str, bytes] | None:
    """Resolve a request path inside WEB_ROOT. Returns (content_type, bytes) or None.

    Traversal-safe: the resolved real path must sit inside the build directory. API prefixes are
    never handled here — routes are matched before this is consulted.
    """
    rel = rel.lstrip("/")
    if not rel or rel.endswith("/"):
        rel = os.path.join(rel, "index.html")
    target = os.path.realpath(os.path.join(_web_root(), rel))
    root = os.path.realpath(_web_root())
    if not (target == root or target.startswith(root + os.sep)):
        return None
    if not os.path.isfile(target):
        return None
    ext = os.path.splitext(target)[1].lower()
    ctype = _CONTENT_TYPES.get(ext) or (mimetypes.guess_type(target)[0] or "application/octet-stream")
    with open(target, "rb") as fh:
        return ctype, fh.read()


def _serve_static(handler, rel: str) -> bool:
    """Serve a built asset, or fall back to the SPA entry point for client-side routes."""
    found = _static_file(rel)
    cache = _CACHE_IMMUTABLE if rel.startswith("/assets/") else "no-cache"
    if found is None:
        index = os.path.join(_web_root(), "index.html")
        if os.path.isfile(index):                      # SPA fallback (hash routing keeps this rare)
            with open(index, "rb") as fh:
                body = fh.read()
            handler.send_response(200)
            handler.send_header("Content-Type", "text/html; charset=utf-8")
            handler.send_header("Content-Length", str(len(body)))
            handler.send_header("Cache-Control", "no-cache")
            handler.end_headers()
            handler.wfile.write(body)
            return True
        return False
    ctype, body = found
    handler.send_response(200)
    handler.send_header("Content-Type", ctype)
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", cache)
    handler.end_headers()
    handler.wfile.write(body)
    return True


def get_store() -> Store:
    """One shared `Store`; the store itself hands each thread its own connection (see `sutra.store`)."""
    global _STORE
    if _STORE is None:
        with _LOCK:
            if _STORE is None:
                _STORE = Store()
    return _STORE


def _json(handler, code: int, obj) -> None:
    body = json.dumps(obj, indent=2, ensure_ascii=False, default=str).encode("utf-8")
    handler.send_response(code)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


INDEX_HTML = """<!doctype html><html><head><meta charset="utf-8"><title>SUTRA runtime</title>
<style>body{font:14px/1.5 ui-monospace,Menlo,monospace;margin:2rem;max-width:70rem}
input,select,button{font:inherit;padding:.35rem}pre{background:#f5f5f0;padding:1rem;overflow:auto}
.ok{color:#0a7d3b}.warn{color:#a86a00}</style></head><body>
<h1>SUTRA — address resolution runtime</h1>
<p>Built against <code>PS3_IMPLEMENTATION_CONTRACTS_2026-10-07.md</code>. No model, no vendor call,
official data only. Refusal is a successful decision.</p>
<form onsubmit="return go()"><input id="q" size="60" value="6th Cross, 5th Main, ಚರ್ಚ್ ಹತ್ತಿರ, Kuvempu Layt, Kaveripura - 960102">
<select id="p"><option>FIELD_NAVIGATION</option><option>NOTICE_SERVICE</option>
<option>VISIT_PLANNING</option><option>PORTFOLIO_REVIEW</option><option>AUDIT</option></select>
<button>resolve</button></form><pre id="out">…</pre>
<script>
async function go(){const r=await fetch('/resolve',{method:'POST',headers:{'Content-Type':'application/json'},
body:JSON.stringify({address_text:document.getElementById('q').value,request_purpose:document.getElementById('p').value})});
document.getElementById('out').textContent=JSON.stringify(await r.json(),null,2);return false}
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    server_version = "sutra/1.0"
    protocol_version = "HTTP/1.1"        # keep-alive; every response sets Content-Length

    def log_message(self, fmt, *args):   # keep the terminal readable
        pass

    # ── helpers ─────────────────────────────────────────────────────────────────────────────────
    def _body(self) -> dict:
        n = int(self.headers.get("Content-Length") or 0)
        if not n:
            return {}
        try:
            return json.loads(self.rfile.read(n).decode("utf-8"))
        except json.JSONDecodeError:
            return {}

    # ── routes ──────────────────────────────────────────────────────────────────────────────────
    def do_GET(self):  # noqa: N802
        u = urlparse(self.path)
        qs = parse_qs(u.query)
        if u.path in ("/", "/index.html"):
            if not _serve_static(self, "index.html"):       # console build present?
                body = INDEX_HTML.encode("utf-8")           # legacy one-page view, unchanged
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            return
        if u.path in ("/health", "/v1/health"):
            return _json(self, 200, views.health_payload(get_store()))
        if u.path == "/v1/overview":
            when = (qs.get("as_of") or [None])[0]
            try:
                return _json(self, 200, product.overview_payload(get_store(), as_of=when))
            except ValueError as e:
                return _json(self, 400, {"error": "INVALID_REQUEST", "detail": str(e)})
        if u.path == "/v1/method-trust":
            return _json(self, 200, product.method_trust_payload())
        if u.path.startswith("/v1/audit/"):
            belief_id = u.path[len("/v1/audit/"):]
            try:
                return _json(self, 200, product.audit_chain(get_store(), belief_id))
            except ValueError as e:
                return _json(self, 400, {"error": "INVALID_REQUEST", "detail": str(e)})
            except KeyError as e:
                return _json(self, 404, {"error": "unknown_belief", "detail": str(e)})
        if u.path == "/v1/audit":
            try:
                limit = int((qs.get("limit") or ["200"])[0])
            except ValueError:
                return _json(self, 400, {"error": "INVALID_REQUEST", "detail": "limit must be an integer"})
            try:
                return _json(self, 200, product.audit_timeline(
                    get_store(), address_id=(qs.get("address_id") or [None])[0],
                    place_id=(qs.get("place_id") or [None])[0], as_of=(qs.get("as_of") or [None])[0],
                    limit=limit))
            except ValueError as e:
                return _json(self, 400, {"error": "INVALID_REQUEST", "detail": str(e)})
        if u.path.startswith("/v1/address/") and u.path.endswith("/case"):
            aid = u.path[len("/v1/address/"):-len("/case")]
            when = (qs.get("as_of") or [None])[0]
            try:
                return _json(self, 200, product.case_snapshot(get_store(), aid, as_of=when))
            except ValueError as e:
                return _json(self, 400, {"error": "INVALID_REQUEST", "detail": str(e)})
            except KeyError as e:
                return _json(self, 404, {"error": "unknown_address", "detail": str(e)})
        if u.path.startswith("/place/") or u.path.startswith("/v1/place/"):
            prefix = "/v1/place/" if u.path.startswith("/v1/place/") else "/place/"
            pid = u.path[len(prefix):]
            when = (qs.get("as_of") or [config.MOMENT])[0]
            try:
                return _json(self, 200, views.place_history_v1(pid, asof.parse_ts(when), get_store()))
            except KeyError as e:
                return _json(self, 404, {"error": "unknown_place", "detail": str(e)})
        if u.path.startswith("/v1/belief/"):
            aid = u.path[len("/v1/belief/"):]
            when = (qs.get("as_of") or [config.MOMENT])[0]
            try:
                return _json(self, 200, views.belief_payload(get_store(), aid, when))
            except KeyError as e:
                return _json(self, 404, {"error": "unknown_address", "detail": str(e)})
        if u.path.startswith("/v1/address/") and u.path.endswith("/observations"):
            aid = u.path[len("/v1/address/"):-len("/observations")]
            when = (qs.get("as_of") or [config.MOMENT])[0]
            try:
                return _json(self, 200, views.observations_payload(get_store(), aid, when))
            except KeyError as e:
                return _json(self, 404, {"error": "unknown_address", "detail": str(e)})
        if u.path.startswith("/v1/plane/address/"):
            aid = u.path[len("/v1/plane/address/"):]
            when = (qs.get("as_of") or [config.MOMENT])[0]
            town = (qs.get("town_id") or [None])[0]
            try:
                rp = purpose_mod.validate_request_purpose(
                    (qs.get("request_purpose") or ["FIELD_NAVIGATION"])[0])
            except ValueError as e:
                return _json(self, 400, {"error": "INVALID_REQUEST", "detail": str(e)})
            try:
                return _json(self, 200, views.geometry_payload(get_store(), aid, when, town_id=town,
                                                               request_purpose=rp))
            except KeyError as e:
                return _json(self, 404, {"error": "unknown_address", "detail": str(e)})
        if u.path.startswith("/v1/plane/"):
            town = u.path[len("/v1/plane/"):]
            when = (qs.get("as_of") or [None])[0]
            try:
                return _json(self, 200, views.plane_payload(town, as_of=when))
            except KeyError as e:
                return _json(self, 404, {"error": "unknown_town", "detail": str(e)})
        if u.path.startswith("/v1/geometry/"):
            aid = u.path[len("/v1/geometry/"):]
            when = (qs.get("as_of") or [config.MOMENT])[0]
            town = (qs.get("town_id") or [None])[0]
            try:
                rp = purpose_mod.validate_request_purpose(
                    (qs.get("request_purpose") or ["FIELD_NAVIGATION"])[0])
            except ValueError as e:
                return _json(self, 400, {"error": "INVALID_REQUEST", "detail": str(e)})
            try:
                return _json(self, 200, views.geometry_payload(get_store(), aid, when, town_id=town,
                                                               request_purpose=rp))
            except KeyError as e:
                return _json(self, 404, {"error": "unknown_address", "detail": str(e)})
        if u.path == "/v1/places":
            try:
                limit = int((qs.get("limit") or ["60"])[0])
            except ValueError:
                return _json(self, 400, {"error": "INVALID_REQUEST", "detail": "limit must be an integer"})
            return _json(self, 200, feeds.places_feed(
                get_store(), (qs.get("as_of") or [config.MOMENT])[0],
                q=(qs.get("q") or [None])[0], state=(qs.get("state") or [None])[0],
                tier=(qs.get("tier") or [None])[0], town_id=(qs.get("town_id") or [None])[0],
                limit=limit, cursor=(qs.get("cursor") or [None])[0]))
        if u.path == "/v1/evidence":
            try:
                limit = int((qs.get("limit") or ["120"])[0])
            except ValueError:
                return _json(self, 400, {"error": "INVALID_REQUEST", "detail": "limit must be an integer"})
            return _json(self, 200, feeds.evidence_feed(
                get_store(), (qs.get("as_of") or [config.MOMENT])[0],
                q=(qs.get("q") or [None])[0], outcome=(qs.get("outcome") or [None])[0],
                polarity=(qs.get("polarity") or [None])[0], town_id=(qs.get("town_id") or [None])[0],
                limit=limit, cursor=(qs.get("cursor") or [None])[0]))
        if u.path == "/v1/tasks":
            try:
                limit = int((qs.get("limit") or ["100"])[0])
            except ValueError:
                return _json(self, 400, {"error": "INVALID_REQUEST", "detail": "limit must be an integer"})
            try:
                return _json(self, 200, views.tasks_list(
                    get_store(), town_id=(qs.get("town_id") or [None])[0],
                    cause=(qs.get("cause") or [None])[0], state=(qs.get("state") or ["open"])[0],
                    as_of=(qs.get("as_of") or [None])[0], limit=limit,
                    cursor=(qs.get("cursor") or [None])[0]))
            except ValueError as e:
                return _json(self, 400, {"error": "INVALID_REQUEST", "detail": str(e)})
        if u.path.startswith("/v1/tasks/"):
            rest = u.path[len("/v1/tasks/"):]
            if rest.endswith("/history"):
                task_id = rest[:-len("/history")]
                try:
                    detail = product.task_detail(get_store(), task_id)
                except KeyError as e:
                    return _json(self, 404, {"error": "unknown_task", "detail": str(e)})
                return _json(self, 200, {"task_id": task_id, "history": detail["history"],
                                         "adjudications": detail["adjudications"],
                                         "state": detail["task"]["state"],
                                         "state_label": detail["state_label"]})
            try:
                return _json(self, 200, product.task_detail(get_store(), rest))
            except KeyError as e:
                return _json(self, 404, {"error": "unknown_task", "detail": str(e)})
        if u.path == "/tasks/verify-first":
            town = (qs.get("town_id") or [None])[0]
            if not town:
                return _json(self, 400, {"error": "INVALID_REQUEST", "detail": "town_id is required"})
            limit = int((qs.get("limit") or ["100"])[0])
            return _json(self, 200, {"town_id": town, "tasks": verify_first_tasks(town, limit, get_store())})
        if u.path.startswith("/packs/"):
            town = u.path[len("/packs/"):]
            try:
                with _LOCK:
                    return _json(self, 200, packs_mod.build_pack(town, store=get_store()))
            except KeyError as e:
                return _json(self, 404, {"error": "unknown_town", "detail": str(e)})
        if _serve_static(self, u.path):                     # console assets / client-side routes
            return
        return _json(self, 404, {"error": "not_found", "path": u.path})

    def do_HEAD(self):  # noqa: N802
        """Health probes and asset checks: same routing as GET, headers only."""
        u = urlparse(self.path)
        if u.path in ("/health", "/v1/health"):
            body = json.dumps(views.health_payload(get_store())).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            return
        found = _static_file(u.path if u.path != "/" else "index.html")
        if found:
            ctype, body = found
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            return
        self.send_response(404)
        self.end_headers()

    def do_PATCH(self):  # noqa: N802
        """Task lifecycle (P1-2). Append-only: a transition adds an event, it never edits one."""
        u = urlparse(self.path)
        if not u.path.startswith("/v1/tasks/"):
            return _json(self, 404, {"error": "not_found", "path": u.path})
        task_id = u.path[len("/v1/tasks/"):]
        payload = self._body()
        to_state = payload.get("state") or payload.get("to_state")
        if not to_state:
            return _json(self, 400, {"error": "INVALID_REQUEST", "detail": "state is required"})
        try:
            with _LOCK:
                out = product.transition_task(
                    get_store(), task_id, to_state, actor=payload.get("actor"), note=payload.get("note"),
                    at=payload.get("at"), idempotency_key=payload.get("idempotency_key"))
        except ValueError as e:
            return _json(self, 400, {"error": "INVALID_REQUEST", "detail": str(e)})
        except KeyError as e:
            return _json(self, 404, {"error": "unknown_task", "detail": str(e)})
        return _json(self, 200, out)

    def do_POST(self):  # noqa: N802
        u = urlparse(self.path)
        payload = self._body()
        if u.path == "/resolve":
            try:
                request_purpose = purpose_mod.validate_request_purpose(payload.get("request_purpose", "FIELD_NAVIGATION"))
            except ValueError as e:
                return _json(self, 400, {"error": "INVALID_REQUEST", "detail": str(e)})
            when = payload.get("as_of")
            # `address_id` is opt-in plumbing for the console's "Open in Resolve": when it is absent
            # the request is byte-for-byte the legacy one. resolve() itself is untouched.
            resp = resolve(payload.get("address_text", ""), payload.get("town_hint"),
                           asof.parse_ts(when) if when else None, request_purpose, store=get_store(),
                           address_id=payload.get("address_id") or None)
            return _json(self, 200, resp)
        if u.path == "/evidence":
            obs = payload.get("observation") or payload
            key = payload.get("idempotency_key") or obs.get("observation_id")
            if not key:
                return _json(self, 400, {"error": "INVALID_REQUEST", "detail": "idempotency_key is required"})
            try:
                with _LOCK:
                    receipt = submit_observation(obs, key, store=get_store())
            except ValueError as e:
                return _json(self, 400, {"error": "INVALID_REQUEST", "detail": str(e)})
            return _json(self, 202, receipt)
        if u.path == "/v1/adjudicate":
            try:
                with _LOCK:
                    out = product.adjudicate(
                        get_store(), task_id=payload.get("task_id"), address_id=payload.get("address_id"),
                        decision=payload.get("decision"), actor=payload.get("actor"),
                        note=payload.get("note"), at=payload.get("as_of"),
                        idempotency_key=payload.get("idempotency_key"))
            except ValueError as e:
                return _json(self, 400, {"error": "INVALID_REQUEST", "detail": str(e)})
            except KeyError as e:
                return _json(self, 404, {"error": "unknown_case", "detail": str(e)})
            return _json(self, 200, out)
        if u.path == "/v1/score_visit":
            obs = payload.get("observation") or payload
            try:
                out = product.score_visit(get_store(), obs,
                                          idempotency_key=payload.get("idempotency_key"))
            except ValueError as e:
                return _json(self, 400, {"error": "INVALID_REQUEST", "detail": str(e)})
            return _json(self, 200, out)
        if u.path == "/v1/batch_resolve":
            items = payload.get("items")
            try:
                out = product.batch_resolve(get_store(), items,
                                            as_of=payload.get("as_of"),
                                            request_purpose=payload.get("request_purpose", "FIELD_NAVIGATION"))
            except ValueError as e:
                return _json(self, 400, {"error": "INVALID_REQUEST", "detail": str(e)})
            return _json(self, 200, out)
        if u.path == "/explain":
            resp = resolve(payload.get("address_text", ""), payload.get("town_hint"),
                           None, payload.get("request_purpose", "FIELD_NAVIGATION"), store=get_store())
            return _json(self, 200, {"explain": explain(resp), "response": resp})
        return _json(self, 404, {"error": "not_found", "path": u.path})


class Server(ThreadingHTTPServer):
    """Threaded, but built for a burst: the default listen backlog of 5 resets connections when a
    field team's devices sync at once."""
    daemon_threads = True
    request_queue_size = 128


def serve(host: str = "0.0.0.0", port: int = 8000):
    get_store()
    httpd = Server((host, port), Handler)
    print(f"sutra runtime listening on http://{host}:{port}  (versions: {VERSIONS['schema_version']})")
    return httpd


if __name__ == "__main__":  # pragma: no cover
    serve().serve_forever()
