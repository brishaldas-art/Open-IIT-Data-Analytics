"""Geometry helpers for the declared local metric plane (no reprojection, no CRS juggling).

`PS3_CANONICAL_SCHEMA.md` §4: all coordinates in the official dataset live in one local metric plane,
x and y in metres. Distance is therefore plain Euclidean distance; bearing is measured from **grid
north** (the +y axis), clockwise, which is the only north this dataset can support.
"""
from __future__ import annotations

import math

COMPASS = ("N", "NE", "E", "SE", "S", "SW", "W", "NW")


def dist(x1: float, y1: float, x2: float, y2: float) -> float:
    """Euclidean distance in metres in the declared plane."""
    return math.hypot(float(x2) - float(x1), float(y2) - float(y1))


def bearing_deg(x1: float, y1: float, x2: float, y2: float) -> float:
    """Bearing from (x1,y1) to (x2,y2) in degrees clockwise from grid north (+y), 0..360."""
    dx, dy = float(x2) - float(x1), float(y2) - float(y1)
    if dx == 0 and dy == 0:
        return 0.0
    return (math.degrees(math.atan2(dx, dy)) + 360.0) % 360.0


def compass(bearing: float) -> str:
    """8-way compass name for a bearing (deterministic, integer bins of 45°)."""
    return COMPASS[int(((float(bearing) % 360.0) + 22.5) // 45.0) % 8]


def round10(v: float) -> int:
    """Round a distance to 10 m — cues are advisory, never spuriously precise (contract §9)."""
    return int(round(float(v) / 10.0) * 10)


def median(values):
    """Deterministic median (even n -> mean of the two middle values)."""
    xs = sorted(float(v) for v in values)
    n = len(xs)
    if n == 0:
        return None
    m = n // 2
    return xs[m] if n % 2 else (xs[m - 1] + xs[m]) / 2.0
