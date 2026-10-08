"""THE as-of gate (contract §2 + P4).

Every temporal question in SUTRA is answered here and nowhere else. No component may implement its
own timestamp filtering: if a module needs "what did we know at `as_of`", it calls one of the three
functions below. `tests/test_acceptance.py::test_asof_single_gate` enforces that mechanically by
scanning the package for timestamp comparisons outside this file.

Timestamps: the official dataset stores local (IST) wall-clock strings without an offset. They are
parsed as IST and stored as canonical UTC ISO-8601 (`…Z`), with the offset recorded on the record —
so an as-of query is always comparing one clock with one clock.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

IST = timezone(timedelta(hours=5, minutes=30))
UTC = timezone.utc


def parse_ts(value, assume_tz=IST) -> datetime:
    """Parse a dataset/API timestamp into an aware UTC datetime.

    Accepts `2026-04-01 11:00:13`, `2026-04-01T11:00:13`, `…Z`, `…+05:30`, `2026-04-01`.
    Naive values are read as IST (the dataset's own clock) and converted.
    """
    if isinstance(value, datetime):
        return value.astimezone(UTC) if value.tzinfo else value.replace(tzinfo=assume_tz).astimezone(UTC)
    s = str(value).strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        dt = datetime.fromisoformat(s[:10])
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=assume_tz)
    return dt.astimezone(UTC)


def to_utc_str(value) -> str:
    """Canonical storage form: `YYYY-MM-DDTHH:MM:SSZ`."""
    return parse_ts(value).strftime("%Y-%m-%dT%H:%M:%SZ")


def now_utc() -> datetime:
    return datetime.now(UTC)


# ── the one comparison ──────────────────────────────────────────────────────────────────────────
def is_before(observed_at, as_of) -> bool:
    """True iff `observed_at` is strictly before `as_of` — the only temporal predicate in SUTRA."""
    if observed_at is None or as_of is None:
        return False
    return parse_ts(observed_at) < parse_ts(as_of)


def age_days(observed_at, as_of) -> float:
    """Age in days of `observed_at` as of `as_of` (never negative)."""
    d = (parse_ts(as_of) - parse_ts(observed_at)).total_seconds() / 86400.0
    return max(0.0, d)


# ── the three query forms every component must use ──────────────────────────────────────────────
def rows_upto(records, as_of, ts_field: str = "observed_at"):
    """Filter an in-memory sequence of dicts/rows to those observed strictly before `as_of`."""
    return [r for r in records if is_before(_get(r, ts_field), as_of)]


def _get(row, field):
    try:
        return row[field] if not isinstance(row, dict) else row.get(field)
    except (KeyError, IndexError, TypeError):
        return None


def observations_upto(store, as_of, address_id=None, town_id=None, kinds=None):
    """Read observations from the store as-of `as_of` (append-only store, indexed scan)."""
    return store.observations_upto(as_of, address_id=address_id, town_id=town_id, kinds=kinds)


def candidates_upto(candidates, as_of):
    """Static candidates have no `as_of_valid`; evidence-backed ones are valid only from their
    `as_of_valid` — i.e. they enter the answer at the first moment *after* the evidence existed."""
    return [c for c in candidates
            if c.get("as_of_valid") is None or is_before(c["as_of_valid"], as_of)]
