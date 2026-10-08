"""
SUTRA — "Address Geocoder That Learns from Field Visits" (PS3).

The runtime built against `PS3_IMPLEMENTATION_CONTRACTS_2026-10-07.md` (normative on any conflict).

One application, not microservices. Importable without network access: nothing in this package opens a
socket, calls a geocoding provider, or reads a dataset outside `data/official_ps3`, `data/cleaned` and
`data/derived` (final data policy, `[S95]`).

Frozen entry points (contract §3), all re-exported here:

    resolve(address_text, town_hint, as_of, request_purpose) -> ResolveResponse
    submit_observation(obs, idempotency_key)                 -> ObservationReceipt
    place_state(place_id, as_of)                             -> PlaceState
    verify_first_tasks(town_id, limit)                       -> list[Task]
    build_pack(town_id, valid_days)                          -> PackManifest
    replay(cutpoints)                                        -> ReplayReport
    candidate_metrics(split)                                 -> MetricsReport
"""

from . import version as _v  # noqa: F401  (kept importable as sutra.version)

__all__ = [
    "resolve", "submit_observation", "place_state", "verify_first_tasks",
    "build_pack", "replay", "candidate_metrics",
]


def __getattr__(name):  # lazy re-exports (no import cost, no import cycles)
    if name == "resolve":
        from .resolve import resolve
        return resolve
    if name == "submit_observation":
        from .store import submit_observation
        return submit_observation
    if name == "place_state":
        from .memory import place_state
        return place_state
    if name == "verify_first_tasks":
        from .memory import verify_first_tasks
        return verify_first_tasks
    if name == "build_pack":
        from .packs import build_pack
        return build_pack
    if name == "replay":
        from .replay import replay
        return replay
    if name == "candidate_metrics":
        from .replay import candidate_metrics
        return candidate_metrics
    raise AttributeError(name)
