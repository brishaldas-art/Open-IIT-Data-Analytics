"""Grouped bootstrap intervals — the ONLY interval machinery in this project (experiment plan §1).

The plan fixes the method, so nothing here is a new statistical choice:

    "grouped bootstrap 95% (10,000 resamples). A difference inside the interval is reported as
     'not resolved by this dataset'."

Implementation notes, all of them deliberate:

* **Resampling is by group, not by row.** Rows inside a group move together. With spatial
  dependence present (addresses in one place block, households on one account) an ungrouped
  interval would be too narrow and would manufacture confidence `[S67][S68]`.
* **Paired comparisons resample the same groups for both arms**, so the reported interval is on the
  *difference* of the two arms rather than on two overlapping marginal intervals.
* **The seed is fixed and travels in the receipt**, so an interval is reproducible: same inputs →
  same bounds.
* No statistic is inferred beyond mean and median. A rate is a mean; an error median is a median.

Nothing in this module is fitted to any data: it is a resampling routine.
"""
from __future__ import annotations

DEFAULT_RESAMPLES = 10_000          # the plan's number; not a knob to tune
DEFAULT_LEVEL = 0.95
DEFAULT_SEED = 7                    # arbitrary but fixed, and printed in every receipt

STATS = ("mean", "median")


def _stat_fn(stat: str):
    if stat not in STATS:
        raise ValueError(f"unsupported statistic: {stat!r} (allowed: {STATS})")
    if stat == "mean":
        return lambda arr: float(arr.mean())
    return lambda arr: float(_median(arr))


def _median(arr):
    import numpy as np
    return np.median(arr)


def _group_index(groups) -> tuple[list, "object"]:
    """(group labels, values-index per group). Group order is sorted for determinism."""
    import numpy as np
    labels = sorted(set(groups))
    pos = {g: i for i, g in enumerate(labels)}
    by_group: list[list[int]] = [[] for _ in labels]
    for i, g in enumerate(groups):
        by_group[pos[g]].append(i)
    return labels, by_group


def _resample_means(rng, by_group, values, n_resamples: int):
    """Vectorised resampling of the *mean*: sum and count per group, then a multinomial draw."""
    import numpy as np
    sizes = np.array([len(idx) for idx in by_group], dtype=np.int64)
    sums = np.array([values[idx].sum() for idx in by_group], dtype=np.float64)
    # one draw of group multiplicities per resample (multinomial ~ sampling G groups with replacement)
    draws = rng.multinomial(len(by_group), np.full(len(by_group), 1.0 / len(by_group)),
                            size=n_resamples)
    num = draws @ sums
    den = draws @ sizes
    return num / np.maximum(den, 1)


def _resample_stat(rng, by_group, values, n_resamples: int, stat: str):
    """Generic path (used for medians): materialise each resample's index vector."""
    import numpy as np
    g = len(by_group)
    idx_arrays = [np.asarray(idx, dtype=np.int64) for idx in by_group]
    draws = rng.integers(0, g, size=(n_resamples, g))
    out = np.empty(n_resamples, dtype=np.float64)
    fn = _stat_fn(stat)
    for r in range(n_resamples):
        pick = np.concatenate([idx_arrays[i] for i in draws[r]])
        out[r] = fn(values[pick])
    return out


def grouped_ci(values, groups, *, stat: str = "mean", resamples: int = DEFAULT_RESAMPLES,
               level: float = DEFAULT_LEVEL, seed: int = DEFAULT_SEED) -> dict:
    """Grouped bootstrap interval of one statistic.

    `values` and `groups` are aligned per-row sequences (rates → 0/1 rows; errors → metres).
    """
    import numpy as np
    if len(values) != len(groups):
        raise ValueError("values and groups must be aligned")
    if not len(values):
        return {"stat": stat, "point": None, "lo": None, "hi": None, "n": 0, "n_groups": 0,
                "resamples": resamples, "level": level, "seed": seed}
    vals = np.asarray(values, dtype=np.float64)
    labels, by_group = _group_index(groups)
    rng = np.random.default_rng(seed)
    if stat == "mean":
        boots = _resample_means(rng, by_group, vals, resamples)
    else:
        boots = _resample_stat(rng, by_group, vals, resamples, stat)
    lo, hi = np.quantile(boots, [(1 - level) / 2, 1 - (1 - level) / 2])
    return {"stat": stat, "point": round(float(_stat_fn(stat)(vals)), 4),
            "lo": round(float(lo), 4), "hi": round(float(hi), 4),
            "n": int(len(vals)), "n_groups": int(len(labels)),
            "resamples": int(resamples), "level": level, "seed": seed}


def paired_grouped_ci(values_a, values_b, groups, *, stat: str = "mean",
                      resamples: int = DEFAULT_RESAMPLES, level: float = DEFAULT_LEVEL,
                      seed: int = DEFAULT_SEED, direction: str = "higher_is_better",
                      min_effect: float = 0.0) -> dict:
    """Grouped bootstrap interval of the **paired difference** `a - b`.

    `resolved` is true only when the interval excludes 0 **and** the point difference clears
    `min_effect` in the stated direction. Everything else is "not resolved by this dataset" —
    the plan's phrasing, and the honest reading of a small sample.
    """
    import numpy as np
    if not (len(values_a) == len(values_b) == len(groups)):
        raise ValueError("a, b and groups must be aligned")
    if not len(values_a):
        return {"stat": stat, "n": 0, "point_delta": None, "lo": None, "hi": None,
                "resolved": False, "direction": direction, "resamples": resamples, "seed": seed}
    a = np.asarray(values_a, dtype=np.float64)
    b = np.asarray(values_b, dtype=np.float64)
    d = a - b
    labels, by_group = _group_index(groups)
    rng = np.random.default_rng(seed)
    if stat == "mean":
        boots = _resample_means(rng, by_group, d, resamples)
    else:
        boots = _resample_stat(rng, by_group, d, resamples, stat)
    lo, hi = np.quantile(boots, [(1 - level) / 2, 1 - (1 - level) / 2])
    point = float(_stat_fn(stat)(d))
    if direction == "higher_is_better":
        resolved = bool(lo > 0.0 and point >= min_effect)
        favours = "a" if point > 0 else ("b" if point < 0 else "neither")
    else:
        resolved = bool(hi < 0.0 and -point >= min_effect)
        favours = "a" if point < 0 else ("b" if point > 0 else "neither")
    return {"stat": stat, "n": int(len(d)), "n_groups": int(len(labels)),
            "point_delta": round(point, 4), "lo": round(float(lo), 4), "hi": round(float(hi), 4),
            "resolved": resolved, "favours": favours if resolved else "not_resolved",
            "direction": direction, "resamples": int(resamples), "level": level, "seed": seed}
