"""Configuration: paths, frozen constants, and the small policy tables the contract fixes by name.

Everything here is data, not behaviour: the modules read these tables, so an experiment can be
reproduced by quoting the version strings in `version.py` plus this file's hash.
"""
from __future__ import annotations

import os

# ── paths ───────────────────────────────────────────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))          # PS3_SUTRA/
DATA = os.environ.get("SUTRA_DATA", os.path.join(ROOT, "data"))
OFFICIAL = os.path.join(DATA, "official_ps3")
CLEANED = os.path.join(DATA, "cleaned")
DERIVED = os.path.join(DATA, "derived")
RUNTIME = os.path.join(DERIVED, "runtime")
INDEX_DIR = os.path.join(DERIVED, "runtime_indexes")
STORE_PATH = os.environ.get("SUTRA_STORE", os.path.join(RUNTIME, "sutra_store.sqlite"))

# ── contract §4 — frozen arm set ────────────────────────────────────────────────────────────────
ARMS = ("frozen_baseline", "locality_centroid", "town_centroid", "official_landmark",
        "address_book", "field_evidence", "memory", "place_neighbour")
STATIC_ARMS = ("frozen_baseline", "locality_centroid", "town_centroid", "official_landmark", "address_book")
EVIDENCE_ARMS = ("field_evidence", "memory", "place_neighbour")   # carry as_of_valid
LICENCE_CLASS = "official"                                        # invariant: never anything else

# place_neighbour is experiment-gated (C2) and OFF until the official baseline pipeline is stable (D43).
ENABLE_PLACE_NEIGHBOUR = False

# ── granularity vocabulary (uncertainty doc §1) ─────────────────────────────────────────────────
GRANULARITY = ("town", "locality", "street", "rooftop")
# stratum of a candidate = the coarsest claim its arm/granularity can support
STRATUM_OF_GRANULARITY = {"rooftop": "rooftop", "street": "street", "locality": "locality", "town": "town"}

# ── radius map (Amendment U1/U2) ────────────────────────────────────────────────────────────────
# radius_m is the empirical p80 of held-out error for the stratum; measured_coverage is the hit-rate of
# that radius on an independent set; n_calibration is the evaluation n behind the coverage number.
# `publishable` follows the n >= 15 guard: below it the stratum is never published under its own name.
RADIUS_TABLE = {
    "locality": {"radius_m": 539.9, "n_calibration": 24, "measured_coverage": 0.792,
                 "publishable": True, "basis": "empirical_p80"},
    "street":   {"radius_m": 162.1, "n_calibration": 5,  "measured_coverage": 1.000,
                 "publishable": False, "basis": "empirical_p80"},
    "pincode":  {"radius_m": 1204.2, "n_calibration": 4, "measured_coverage": 0.000,
                 "publishable": False, "basis": "empirical_p80"},
    "rooftop":  {"radius_m": None,   "n_calibration": 1, "measured_coverage": None,
                 "publishable": False, "basis": "insufficient_n"},
}
# Every stratum that cannot be published falls back to this one — the only stratum with n >= 15 and a
# measured coverage. Fallbacks are visible in `source_stratum` and always widened + labelled.
FALLBACK_STRATUM = "locality"
# ── field-evidence / memory decision policy (2026-10-08) ─────────────────────────────────────────
# These knobs select how a prior observation becomes a candidate. All defaults reproduce the frozen
# pre-existing behaviour exactly; the evidence/memory policy experiment flips them only if a challenger
# clears the promotion gate on S-TRAIN/S-VAL and the temporal holdout. Every value is a constant, none
# is derived from S-Eval, and none depends on the address being resolved.
EVIDENCE_MEMORY_POLICY = "emp-v1"      # see data/derived/final_evidence_memory_policy.json
SINGLE_QUALITY_TIERING = False         # a check-in's granularity reflects its own measured quality
SINGLE_GATE_GPS_M = None               # drop a single check-in whose GPS accuracy is worse than this
SINGLE_GATE_MIN_WEIGHT = None          # drop a single check-in whose stored weight is below this
SINGLE_MAX_EMITTED = 3                 # how many single check-ins may enter the candidate set
MEMORY_REQUIRES_EVIDENCE_DERIVED = True    # memory must carry accumulated field evidence, not a pin
MEMORY_EMIT = "evidence_derived_only"  # always | evidence_derived_only
MEMORY_ON_DEMAND_BELIEF = True         # recompute the prior at `as_of` when no row was materialised there
SINGLE_TIEBREAK_QUALITY = False        # equal scores are ordered by the generator's quality order, not by id

# ── retrieval (precision optimisation, 2026-10-08) ───────────────────────────────────────────────
# v1: any shared token counts as a locality-name hit, plus a pincode tie-break, tie-broken by id.
#     Measured defect: "nagar"/"colony" matched everywhere and a stale pincode outvoted the text,
#     so the locality candidate was the WRONG locality on 118/292 supervision rows.
# v2: IDF-weighted token coverage — every distinctive token of the locality name must be present and
#     the name's rarest token always; deterministic tie-break. Same arm, same source table.
RETRIEVAL_VERSION = "v2"
RETRIEVAL_RING = "B2"            # the normalisation the IDF table is built under
LOCALITY_MIN_COVERAGE = 0.5      # fraction of the locality name's tokens that must be present

N_GUARD = 15

# tier widening factors (policy, reason-coded). `widened` has exactly three triggers:
# calibration_fallback · stale_pack · negative_accumulation
WIDEN = {
    "calibration_fallback": 1.0,
    "probable": 1.25,
    "approximate": 1.5,
    "stale_pack": 1.2,
    "negative_accumulation": 1.35,
    "cold_start": 1.35,
}

# ── evidence policy (rule-based MVP; weights + reason codes, never a binary trust flag) ─────────
OUTCOME_BASE = {
    "met_borrower": 0.95, "met_family": 0.80, "cash_collected": 1.00,
    "neighbour_says_shifted": 0.35, "locked_premises": 0.45,
    "no_such_person": 0.00, "address_not_traceable": 0.00,
}
OUTCOME_CLASS = {
    "met_borrower": "positive", "met_family": "positive", "cash_collected": "positive",
    "neighbour_says_shifted": "ambiguous", "locked_premises": "ambiguous",
    "no_such_person": "process", "address_not_traceable": "process",
}
NEGATIVE_OUTCOMES = ("no_such_person", "address_not_traceable")
W_MIN = 0.35            # entry weight for WARM
W_PROMOTE = 0.50        # a confirmation must reach this to count toward promotion
WEAK_POSITIVE = 0.45    # two weak positives (ambiguous class) -> PROBABLE

# dwell (seconds) — measured practice: median 207 s (PS3_FIELD_EVIDENCE_ARCHITECTURE §1)
DWELL_SHORT_S, DWELL_OK_S, DWELL_IMPLAUSIBLE_S = 60, 180, 7200
# gps accuracy (metres) — dataset median 9.8 m
GPS_FINE_M, GPS_OK_M, GPS_COARSE_M = 15.0, 30.0, 50.0
# trail/check-in agreement (metres) — own-trail median 7.6 m
TRAIL_AGREE_M, TRAIL_LOOSE_M = 50.0, 150.0
# business hours for timing plausibility (RBI visit window 08:00–19:00, [S55])
VISIT_HOUR_START, VISIT_HOUR_END = 8, 19
TZ_OFFSET_HOURS = 5.5                      # IST — the dataset's local offset, recorded per timestamp
# per-collector monitoring band, from the measured spread (19.5–29.1% not-traceable)
AGENT_NEG_RATE_HIGH = 0.40
AGENT_NEG_RATE_LOW = 0.20
# recency half-life (months) — evidence weight decays; beliefs do not change silently
HALF_LIFE_MONTHS = {"rooftop": 24.0, "street": 18.0, "locality": 12.0, "town": 6.0}

# ── promotion / independence (F2.2) ─────────────────────────────────────────────────────────────
INDEPENDENCE_DIMS = ("visit", "collector", "period", "media", "source", "space")
PERIOD_GAP_DAYS = 7          # "at least 7 days apart" (label-lag realism)
CONSISTENCY_BAND_M = 30.0    # two confirmations agreeing within this are the same place, fining to rooftop
SPACE_BAND_M = 150.0         # check-in agreement band for the `space` dimension
CONTEST_SEPARATION_MULT = 2.0  # > 2 x radius apart => CONTESTED (memory §4)
NEG_ACCUMULATION_MIN = 2       # independent negatives needed to doubt out loud (F2.1)

# ── purpose / eligibility ───────────────────────────────────────────────────────────────────────
REQUEST_PURPOSES = ("NOTICE_SERVICE", "VISIT_PLANNING", "FIELD_NAVIGATION", "PORTFOLIO_REVIEW",
                    "AUDIT", "DEMO")
ELIGIBILITY_ACTIONS = ("SERVE", "VERIFY_FIRST", "REFUSE")
ADDRESS_PURPOSES = ("HOME_LIKE", "WORK_LIKE", "OTHER", "UNKNOWN")
WORK_LIKE_REFUSE_PURPOSES = ("NOTICE_SERVICE", "VISIT_PLANNING")   # purposes needing a SERVE-grade place

# ── directions ──────────────────────────────────────────────────────────────────────────────────
DIRECTION_MAX_M = 1500.0     # plausibility radius in the supplied towns; beyond it: no cue
LANDMARK_PLAUSIBILITY_M = 1000.0   # a landmark named *in the address* must sit near the address's
                                   # other arms; hits beyond this from every other-arm candidate are dropped
# relation phrases attested in the corpus (counts in the receipt), longest-first so "next to" wins
# over "next": near(207) · opposite(55) · opp(173) · behind(50) · beside(17) · next to(18) ·
# close to(233) · adjacent(0) · ಹತ್ತಿರ(76)
RELATION_WORDS = ("close to", "next to", "opposite", "opp", "near", "behind", "beside", "adjacent",
                  "ಹತ್ತಿರ")

# ── packs / offline ─────────────────────────────────────────────────────────────────────────────
PACK_VALID_DAYS_DEFAULT = 7
HELD_MAX_DAYS = 7            # out-of-order observations wait (sync contract, [S81])
TRAIL_RETENTION_DAYS = 90

MOMENT = "2026-06-01T00:00:00Z"      # default reference cut-point used by build tools
