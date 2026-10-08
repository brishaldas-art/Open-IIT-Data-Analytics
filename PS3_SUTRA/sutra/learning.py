"""Learned ranking challengers — governed, **never on the request path** (contract §3 M3b).

    rank_with(model, candidates, features, as_of) -> [{candidate_id, score, reasons}]

The frozen interface (§6.3) is `sutra.ranking.rank`: candidate set in, inspectable per-candidate score,
reason codes, deterministic order out. This module adds *challengers* that implement the same output
shape so an experiment can compare them; nothing here is imported by `resolve`, `api` or any module on
the request path, and the shipped ranker stays the rule baseline until an experiment promotes a
challenger and a configuration change says so.

What this module implements, and nothing else:

* `Logistic` — L2 logistic regression on **binary relevance** (relevant ⇔ the candidate is within the
  framework's primary 500 m threshold). Small, interpretable, standardised inputs.
* `LambdaMart` — gradient-boosted trees with the **listwise NDCG-weighted LambdaRank** gradient
  (LightGBM's formulation: λ_ij = σ·ρ·|ΔNDCG_swap|, Newton hessians).
* `Pairwise` — the same trees with the **RankNet** pairwise-logistic gradient (no NDCG weighting).
* `shuffled_grades` — the negative control: grades permuted *within* each address group.

No dependency beyond numpy/sklearn (already used by `sutra/stats.py` and the experiment tools); no
network, no external data, no model artefact written to disk.

Pre-registered configuration (`PS3_MODEL_SELECTION.md`, "Starting configuration"), honoured exactly:
`n_estimators ≤ 300`, `max_depth ≤ 4`, `learning_rate 0.05`, `subsample 0.8`, L2 regularisation on,
monotone constraints on `similarity↑`, `granularity↑`, `distance_to_town_centroid↓`, early stopping
only against grouped S-Val. Feature count is the frozen 15 (`sutra.ranking.FEATURES`, cap M2).

Implementation choices that the pre-registration does not fix are declared here, once:

* the tree learner is a **Newton (gradient/hessian) regression tree** — the same second-order
  construction LightGBM uses — with `min_data_in_leaf = 5` and L2 leaf weight `1.0`;
* rows are subsampled at 0.8 per boosting round with a fixed seed; features are never subsampled;
* categorical features (`f_baseline_stratum`) are one-hot expanded *inside* the model, so the frozen
  feature matrix keeps its 15 columns and the model's design matrix is wider;
* monotone constraints are enforced by **structural isotonic repair** after each tree is grown
  (violating leaves are clamped to the boundary value), and verified structurally per tree — a
  constraint is never merely assumed;
* early stopping uses the **S-Val nDCG@5** (smooth; the primary metric is a 1/69-step rate) with
  patience 30, and the ensemble is truncated to its best iteration.
"""
from __future__ import annotations

import numpy as np

from . import geo, ranking

FEATURES = ranking.FEATURES                       # the frozen 15 (M2 cap)
CATEGORICAL = ("f_baseline_stratum",)             # one-hot expanded inside the model
MONOTONE = {                                      # exactly the pre-registered three groups
    "f_sim_jaccard": 1, "f_sim_char3": 1, "f_sim_ratio": 1,   # similarity ↑
    "f_granularity_rank": 1,                                   # granularity ↑
    "f_dist_to_town_centroid_m": -1,                           # distance to town centroid ↓
}
GRADE_THRESHOLDS = ((100, 3), (250, 2), (500, 1))   # the framework's own hit thresholds
DEFAULTS = {
    "n_estimators": 300, "max_depth": 4, "learning_rate": 0.05, "subsample": 0.8,
    "l2_leaf": 1.0, "min_data_in_leaf": 5, "patience": 30, "seed": 7, "sigma": 1.0,
    "logistic_C": 1.0,
}


# ── relevance and metrics (the framework's own thresholds) ──────────────────────────────────────
def grade_of(err_m: float | None) -> int:
    """Graded relevance from a candidate's error against the proxy label: 3 ≤100 m · 2 ≤250 · 1 ≤500 · 0."""
    if err_m is None:
        return 0
    for threshold, grade in GRADE_THRESHOLDS:
        if err_m <= threshold:
            return grade
    return 0


def dcg(grades: np.ndarray, k: int = 5) -> float:
    g = np.asarray(grades, dtype=np.float64)[:k]
    disc = 1.0 / np.log2(np.arange(2, len(g) + 2))
    return float(np.sum((2.0 ** g - 1.0) * disc))


def ndcg_at_k(grades: np.ndarray, k: int = 5) -> float:
    ideal = dcg(np.sort(np.asarray(grades, dtype=np.float64))[::-1], k)
    if ideal <= 0.0:
        return float("nan")                     # no relevant document: the metric is undefined, not 0
    return dcg(np.asarray(grades, dtype=np.float64), k) / ideal


def group_ndcg(order_grades: list[np.ndarray], k: int = 5) -> tuple[float, int]:
    """Mean nDCG@k over groups; returns (mean, n_groups_used). Groups with no relevance are excluded."""
    vals = [ndcg_at_k(g, k) for g in order_grades]
    vals = [v for v in vals if v == v]
    return (float(np.mean(vals)) if vals else float("nan")), len(vals)


# ── design matrix ───────────────────────────────────────────────────────────────────────────────
def design_matrix(feature_rows: list[dict], strata: tuple[str, ...] | None = None):
    """(X, columns, strata) — numeric features + one-hot categoricals, with a *fixed* vocabulary.

    `strata` must come from the training set and be reused at prediction time, otherwise the model
    would see different columns than it was fitted on.
    """
    if strata is None:
        strata = tuple(sorted({str(r.get("f_baseline_stratum") or "") for r in feature_rows}))
    cols = [f for f in FEATURES if f not in CATEGORICAL] + [f"stratum={s}" for s in strata]
    X = np.zeros((len(feature_rows), len(cols)), dtype=np.float64)
    for i, row in enumerate(feature_rows):
        for j, f in enumerate(cols):
            if f.startswith("stratum="):
                X[i, j] = 1.0 if str(row.get("f_baseline_stratum") or "") == f[8:] else 0.0
            else:
                v = row.get(f)
                X[i, j] = 0.0 if v is None or v == "" else float(v)
    return X, tuple(cols), strata


def monotone_vector(cols: tuple[str, ...]) -> np.ndarray:
    return np.array([MONOTONE.get(c, 0) for c in cols], dtype=np.int64)


# ── the Newton tree (LightGBM-style second-order construction) ──────────────────────────────────
class _Node:
    __slots__ = ("feature", "threshold", "left", "right", "value", "n")

    def __init__(self):
        self.feature = -1
        self.threshold = 0.0
        self.left = None
        self.right = None
        self.value = 0.0
        self.n = 0


def _gain(gl, hl, gr, hr, l2):
    return (gl * gl) / (hl + l2) + (gr * gr) / (hr + l2) - ((gl + gr) ** 2) / (hl + hr + l2)


def _best_split(X, lam, hess, idx, min_data, l2, cols_n):
    best = (0.0, -1, 0.0)
    hsum, lsum = hess[idx].sum(), lam[idx].sum()
    for j in range(cols_n):
        x = X[idx, j]
        order = np.argsort(x, kind="mergesort")
        xs, ls, hs = x[order], lam[idx][order], hess[idx][order]
        cl, ch = np.cumsum(ls), np.cumsum(hs)
        n = len(idx)
        for cut in range(1, n):
            if xs[cut] == xs[cut - 1]:
                continue
            if cut < min_data or (n - cut) < min_data:
                continue
            gain = _gain(cl[cut - 1], ch[cut - 1], lsum - cl[cut - 1], hsum - ch[cut - 1], l2)
            if gain > best[0] + 1e-12:
                best = (float(gain), j, float((xs[cut] + xs[cut - 1]) / 2.0))
    return best


def _build(X, lam, hess, idx, depth, min_data, l2, cols_n):
    node = _Node()
    node.n = len(idx)
    if depth <= 0 or node.n < 2 * min_data:
        node.value = float(-lam[idx].sum() / (hess[idx].sum() + l2))
        return node
    gain, j, thr = _best_split(X, lam, hess, idx, min_data, l2, cols_n)
    if j < 0:
        node.value = float(-lam[idx].sum() / (hess[idx].sum() + l2))
        return node
    left = idx[X[idx, j] <= thr]
    right = idx[X[idx, j] > thr]
    if len(left) < min_data or len(right) < min_data:
        node.value = float(-lam[idx].sum() / (hess[idx].sum() + l2))
        return node
    node.feature, node.threshold = j, thr
    node.left = _build(X, lam, hess, left, depth - 1, min_data, l2, cols_n)
    node.right = _build(X, lam, hess, right, depth - 1, min_data, l2, cols_n)
    return node


def _leaves(node, out=None):
    out = [] if out is None else out
    if node.feature < 0:
        out.append(node)
        return out
    _leaves(node.left, out)
    _leaves(node.right, out)
    return out


def _clamp(node, lo=None, hi=None):
    for leaf in _leaves(node):
        if lo is not None and leaf.value < lo:
            leaf.value = lo
        if hi is not None and leaf.value > hi:
            leaf.value = hi


def _repair(node, mono, rounds=8):
    """Isotonic repair: for a monotone split, clamp both sides to a feasible boundary."""
    if node.feature < 0:
        return
    _repair(node.left, mono)
    _repair(node.right, mono)
    d = int(mono[node.feature])
    if d == 0:
        return
    for _ in range(rounds):
        lv = [leaf.value for leaf in _leaves(node.left)]
        rv = [leaf.value for leaf in _leaves(node.right)]
        if d > 0 and max(lv) <= min(rv):
            return
        if d < 0 and max(rv) <= min(lv):
            return
        if d > 0:
            m = (max(lv) + min(rv)) / 2.0
            _clamp(node.left, hi=m)
            _clamp(node.right, lo=m)
        else:
            m = (max(rv) + min(lv)) / 2.0
            _clamp(node.left, lo=m)
            _clamp(node.right, hi=m)


def _predict_tree(node, X, out, idx_rows):
    for r in idx_rows:
        n = node
        while n.feature >= 0:
            n = n.left if X[r, n.feature] <= n.threshold else n.right
        out[r] += n.value


def structural_monotone_check(node, mono, tol=1e-9) -> bool:
    """Exact per-tree verification: on a monotone split, every left leaf ≤ every right leaf."""
    if node.feature < 0:
        return True
    if not (structural_monotone_check(node.left, mono, tol)
            and structural_monotone_check(node.right, mono, tol)):
        return False
    d = int(mono[node.feature])
    if d == 0:
        return True
    lv = [leaf.value for leaf in _leaves(node.left)]
    rv = [leaf.value for leaf in _leaves(node.right)]
    return max(lv) <= min(rv) + tol if d > 0 else max(rv) <= min(lv) + tol


# ── the boosted ranker base ─────────────────────────────────────────────────────────────────────
class _GBTRanker:
    """Shared boosting loop; subclasses supply the per-group gradients (λ, h)."""

    name = "gbt"

    def __init__(self, **kw):
        self.p = {**DEFAULTS, **kw}
        self.trees: list[_Node] = []
        self.base = 0.0
        self.best_iteration = 0
        self.history: list[dict] = []
        self.cols: tuple[str, ...] = ()
        self.strata: tuple[str, ...] = ()
        self.mono = None

    # subclasses override
    def _gradients(self, scores, groups, grades, sigma):
        raise NotImplementedError

    def fit(self, X, y, groups, Xval=None, yval=None, groups_val=None):
        if self.mono is None:
            self.mono = np.zeros(np.asarray(X, dtype=np.float64).shape[1], dtype=np.int64)
        rng = np.random.default_rng(self.p["seed"])
        Xtr = np.asarray(X, dtype=np.float64)
        ytr = np.asarray(y, dtype=np.float64)
        gtr = np.asarray(groups)
        gidx = [np.where(gtr == g)[0] for g in dict.fromkeys(gtr.tolist())]
        self.base = float(np.mean(ytr)) if len(ytr) else 0.0
        scores = np.full(len(ytr), self.base)
        best = (-np.inf, 0)
        stale = 0
        val_scores = None
        for it in range(1, self.p["n_estimators"] + 1):
            rows = np.where(rng.random(len(ytr)) < self.p["subsample"])[0]
            lam, hess = self._gradients(scores, gidx, ytr, self.p["sigma"], rows)
            lam, hess = lam[rows], hess[rows]
            idx = np.arange(len(rows))
            node = _build(Xtr[rows], lam, hess, idx, self.p["max_depth"],
                          self.p["min_data_in_leaf"], self.p["l2_leaf"], Xtr.shape[1])
            _repair(node, self.mono)
            upd = np.zeros(len(ytr))
            _predict_tree(node, Xtr, upd, np.arange(len(ytr)))
            scores = scores + self.p["learning_rate"] * upd
            self.trees.append(node)
            if Xval is not None and len(Xval):
                if val_scores is None:
                    val_scores = np.full(len(yval), self.base)
                updv = np.zeros(len(yval))
                _predict_tree(node, np.asarray(Xval, dtype=np.float64), updv, np.arange(len(yval)))
                val_scores = val_scores + self.p["learning_rate"] * updv
                metric, n_used = self._val_metric(val_scores, groups_val, yval)
                self.history.append({"iteration": it, "val_ndcg5": metric, "n_groups": n_used})
                if metric == metric and metric > best[0] + 1e-9:
                    best, stale = (metric, it), 0
                else:
                    stale += 1
                    if stale >= self.p["patience"]:
                        break
        if Xval is not None and len(Xval) and best[1] > 0:
            self.best_iteration = best[1]
        else:
            self.best_iteration = len(self.trees)
        self.trees = self.trees[:self.best_iteration]
        return self

    def _val_metric(self, scores, groups_val, grades):
        gv = np.asarray(groups_val)
        order = []
        for g in dict.fromkeys(gv.tolist()):
            m = np.where(gv == g)[0]
            order.append(np.asarray(grades, dtype=np.float64)[m][np.argsort(-scores[m], kind="mergesort")])
        return group_ndcg(order, 5)

    def predict_raw(self, X) -> np.ndarray:
        Xa = np.asarray(X, dtype=np.float64)
        out = np.zeros(len(Xa))
        for t in self.trees:
            _predict_tree(t, Xa, out, np.arange(len(Xa)))
        return self.base + self.p["learning_rate"] * out

    def monotone_ok(self) -> bool:
        return all(structural_monotone_check(t, self.mono) for t in self.trees)

    def importances(self) -> list[dict]:
        """Split-count importance — for reporting and reason codes, never for fitting."""
        counts = np.zeros(len(self.cols))
        def walk(n):
            if n.feature < 0:
                return
            counts[n.feature] += 1
            walk(n.left); walk(n.right)
        for t in self.trees:
            walk(t)
        total = counts.sum() or 1.0
        return sorted(({"feature": self.cols[i], "share": round(float(counts[i] / total), 4)}
                       for i in range(len(self.cols))), key=lambda d: (-d["share"], d["feature"]))


class LambdaMart(_GBTRanker):
    """Listwise: NDCG-weighted LambdaRank gradients (LightGBM's λ formulation)."""

    name = "lambdamart"

    def _gradients(self, scores, gidx, grades, sigma, rows=None):
        lam = np.zeros(len(scores))
        hess = np.zeros(len(scores))
        for idx in gidx:
            g = grades[idx]
            s = scores[idx]
            order = np.argsort(-s, kind="mergesort")
            pos = np.empty(len(idx), dtype=np.int64)
            pos[order] = np.arange(len(idx))
            disc = 1.0 / np.log2(np.arange(2, len(idx) + 2))
            gains = 2.0 ** g - 1.0
            cur = float(np.sum(gains * disc))
            ideal_positions = np.argsort(-g, kind="mergesort")
            ideal = float(np.sum(gains[ideal_positions] * disc))
            if ideal <= 0:
                continue
            for a in range(len(idx)):
                for b in range(a + 1, len(idx)):
                    i, j = (a, b) if g[a] > g[b] else ((b, a) if g[b] > g[a] else (None, None))
                    if i is None:
                        continue
                    pi, pj = pos[i], pos[j]
                    swapped = cur - gains[i] * disc[pi] - gains[j] * disc[pj] \
                        + gains[i] * disc[pj] + gains[j] * disc[pi]
                    dndcg = abs(swapped - cur) / ideal
                    rho = 1.0 / (1.0 + np.exp(sigma * (s[i] - s[j])))
                    l = sigma * rho * dndcg
                    lam[idx[i]] -= l
                    lam[idx[j]] += l
                    h = sigma * sigma * rho * (1.0 - rho) * dndcg
                    hess[idx[i]] += h
                    hess[idx[j]] += h
        hess = np.maximum(hess, 1e-6)
        return lam, hess


class Pairwise(_GBTRanker):
    """RankNet-style: pairwise logistic gradients, no NDCG weighting."""

    name = "pairwise"

    def _gradients(self, scores, gidx, grades, sigma, rows=None):
        lam = np.zeros(len(scores))
        hess = np.zeros(len(scores))
        for idx in gidx:
            g = grades[idx]
            s = scores[idx]
            for a in range(len(idx)):
                for b in range(a + 1, len(idx)):
                    if g[a] == g[b]:
                        continue
                    i, j = (a, b) if g[a] > g[b] else (b, a)
                    rho = 1.0 / (1.0 + np.exp(sigma * (s[i] - s[j])))
                    lam[idx[i]] -= sigma * rho
                    lam[idx[j]] += sigma * rho
                    h = sigma * sigma * rho * (1.0 - rho)
                    hess[idx[i]] += h
                    hess[idx[j]] += h
        hess = np.maximum(hess, 1e-6)
        return lam, hess


class Logistic:
    """L2 logistic regression on binary relevance — the interpretable challenger."""

    name = "logistic"

    def __init__(self, **kw):
        self.p = {**DEFAULTS, **kw}
        self.model = None
        self.cols: tuple[str, ...] = ()
        self.strata: tuple[str, ...] = ()
        self._scaler = None

    def fit(self, X, y, groups, Xval=None, yval=None, groups_val=None):
        from sklearn.linear_model import LogisticRegression
        from sklearn.preprocessing import StandardScaler
        Xtr = np.asarray(X, dtype=np.float64)
        ybin = (np.asarray(y, dtype=np.float64) >= 1).astype(int)
        if ybin.min() == ybin.max():                      # a degenerate target: refuse to pretend
            raise ValueError("training labels contain a single class")
        self._scaler = StandardScaler().fit(Xtr)
        self.model = LogisticRegression(C=self.p["logistic_C"], class_weight="balanced", max_iter=2000,
                                        solver="lbfgs", random_state=self.p["seed"])
        self.model.fit(self._scaler.transform(Xtr), ybin)
        return self

    def predict_raw(self, X) -> np.ndarray:
        return self.model.decision_function(self._scaler.transform(np.asarray(X, dtype=np.float64)))

    def importances(self) -> list[dict]:
        coef = np.abs(self.model.coef_[0])
        total = coef.sum() or 1.0
        return sorted(({"feature": self.cols[i], "share": round(float(coef[i] / total), 4)}
                       for i in range(len(self.cols))), key=lambda d: (-d["share"], d["feature"]))

    def monotone_ok(self) -> bool:
        return not self.monotone_violations()

    def monotone_violations(self) -> list[dict]:
        """Which coefficients wanted the pre-registered sign and did not.

        `fit` bounds nothing, so the structural check is a *test*, not a constraint: the failure is
        reported (column, fitted sign, required sign) instead of being silently regularised away.
        """
        coef = self.model.coef_[0]
        out = []
        for i, c in enumerate(self.cols):
            d = MONOTONE.get(c)
            if d == 1 and coef[i] < -1e-12:
                out.append({"column": c, "required": ">= 0 (up)", "fitted_sign": "negative",
                            "coefficient": round(float(coef[i]), 4)})
            if d == -1 and coef[i] > 1e-12:
                out.append({"column": c, "required": "<= 0 (down)", "fitted_sign": "positive",
                            "coefficient": round(float(coef[i]), 4)})
        return out


def shuffled_grades(y, groups, seed: int = 7):
    """Within-group permutation of the relevance grades — the leakage control."""
    rng = np.random.default_rng(seed)
    out = np.array(y, dtype=np.float64)
    g = np.asarray(groups)
    for grp in dict.fromkeys(g.tolist()):
        m = np.where(g == grp)[0]
        out[m] = out[m][rng.permutation(len(m))]
    return out


# ── the frozen output shape ─────────────────────────────────────────────────────────────────────
def rank_with(model, candidates: list[dict], features: dict, as_of) -> list[dict]:
    """Score candidates with a challenger and return the frozen ranker's output shape (§6.3).

    Reasons are the model identity, the score, the trained iteration count and the model's global
    feature importances — a tree ensemble cannot produce the rule baseline's per-candidate additive
    reasons without a SHAP-style pass, and pretending otherwise would be worse than saying so.
    """
    rows = [features.get(c["candidate_id"], {}) for c in candidates]
    if not rows:
        return []
    X = apply_design(model, rows)
    scores = model.predict_raw(X)
    imp = model.importances()[:3]
    ctx = ", ".join(f"{d['feature']}={d['share']}" for d in imp)
    out = []
    for c, s in zip(candidates, scores):
        out.append({"candidate_id": c["candidate_id"], "score": round(float(s), 6),
                    "reasons": [f"model:{model.name}", f"score={float(s):+.4f}",
                                f"iterations={getattr(model, 'best_iteration', 0) or len(getattr(model, 'trees', []))}",
                                f"top_features:{ctx}"]})
    out.sort(key=lambda r: (-r["score"], r["candidate_id"]))
    return out


def apply_design(model, rows) -> np.ndarray:
    """Build the design matrix with the model's own column vocabulary (train/predict consistency)."""
    cols = model.cols
    X = np.zeros((len(rows), len(cols)), dtype=np.float64)
    for i, row in enumerate(rows):
        for j, f in enumerate(cols):
            if f.startswith("stratum="):
                X[i, j] = 1.0 if str(row.get("f_baseline_stratum") or "") == f[8:] else 0.0
            else:
                v = row.get(f)
                X[i, j] = 0.0 if v is None or v == "" else float(v)
    return X


def prepare(feature_rows: list[dict], strata: tuple[str, ...]):
    X, cols, strata = design_matrix(feature_rows, strata)
    return X, cols, strata


def fit_model(kind: str, feature_rows: list[dict], y, groups, feature_rows_val=None, y_val=None,
              groups_val=None, strata=None, **kw):
    """Fit one challenger by name. Returns the model (columns are captured from the training rows)."""
    X, cols, strata = design_matrix(feature_rows, strata)
    if feature_rows_val is not None and len(feature_rows_val):
        Xv, _, _ = design_matrix(feature_rows_val, strata)
    else:
        Xv = None
    if kind == "logistic":
        m = Logistic(**kw)
    elif kind == "lambdamart":
        m = LambdaMart(**kw)
    elif kind == "pairwise":
        m = Pairwise(**kw)
    else:
        raise ValueError(f"unknown model kind {kind!r}")
    m.cols, m.strata = cols, strata
    if isinstance(m, _GBTRanker):
        m.mono = monotone_vector(cols)
        m.fit(X, y, groups, Xval=Xv, yval=y_val, groups_val=groups_val)
    else:
        m.fit(X, y, groups)
    return m
