"""The supervision firewall and the split protocol (P1, contract §2). No training may run without a
declared `SplitSpec` — `require_declared` is the choke point every metrics entry point calls first.

S-Eval = the 100 surveyed addresses, fixed forever. The firewall excludes, from every supervision /
feature-fit / tuning set:

    1. the 100 surveyed addresses themselves,
    2. their 100 accounts (128 addresses in total),
    3. every place block containing a surveyed address (99 blocks, 117 addresses),
    union = 145 addresses = 4.7% of 3,117; remaining pool 2,972 addresses.

S-Train / S-Val are **operational supervision only**: candidate–place pairs for addresses carrying
promotion-grade confirmations (F2.2 tuple), split by nested grouped CV — outer folds = place blocks,
inner folds = accounts.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
from dataclasses import asdict, dataclass, field

from . import asof, config, dataio, evidence as ev_mod
from .version import PROTOCOL_VERSION

S_TRAIN, S_VAL, S_EVAL, EXCLUDED, POOL = "S-TRAIN", "S-VAL", "S-EVAL", "EXCLUDED", "POOL_UNSUPERVISED"


class UndeclaredSplit(RuntimeError):
    """Raised when a metrics run does not name a SplitSpec that references §2."""


@dataclass(frozen=True)
class SplitSpec:
    spec_id: str
    populations: tuple[str, ...]
    as_of: str
    outer_grouping: str = "place_block"
    inner_grouping: str = "account"
    outer_fold: int | None = None
    label_source: str = "surveyed_ground_truth"
    protocol_version: str = PROTOCOL_VERSION
    firewall_receipt_sha256: str = ""
    note: str = ""

    def to_json(self) -> dict:
        d = asdict(self)
        d["populations"] = list(self.populations)
        return d


# ── the firewall ────────────────────────────────────────────────────────────────────────────────
def firewall_rows(ix) -> list[dict]:
    """The excluded addresses with the reason each one is excluded."""
    surveyed = set(dataio.surveyed())
    accounts = {ix.addresses[a]["account_id"] for a in surveyed if a in ix.addresses}
    blocks = {ix.block_of(a) for a in surveyed if ix.block_of(a)}
    rows = []
    for aid in sorted(ix.addresses):
        reasons = []
        if aid in surveyed:
            reasons.append("surveyed_s_eval")
        if ix.addresses[aid]["account_id"] in accounts:
            reasons.append("account_of_surveyed")
        if ix.block_of(aid) in blocks:
            reasons.append("block_of_surveyed")
        if reasons:
            rows.append({"address_id": aid, "account_id": ix.addresses[aid]["account_id"],
                         "place_block_id": ix.block_of(aid), "exclusion_reason": "+".join(reasons),
                         "eligible_for_supervision": False})
    return rows


def build(store, ix, out_dir: str | None = None, as_of=None) -> dict:
    """Write `supervision_firewall.csv`, `supervision_manifest.csv` and `split_receipt.json`."""
    out = out_dir or config.DERIVED
    as_of = as_of or config.MOMENT
    os.makedirs(out, exist_ok=True)

    fw = firewall_rows(ix)
    fw_ids = {r["address_id"] for r in fw}
    surveyed_ids = set(dataio.surveyed())

    manifest, n_eligible = [], 0
    for aid in sorted(ix.addresses):
        row = ix.addresses[aid]
        block = ix.block_of(aid)
        blockinfo = ix.place_blocks.get(aid, {})
        outer_fold = int(blockinfo.get("fold", 0))
        inner_fold = int(hashlib.sha1(row["account_id"].encode()).hexdigest(), 16) % 5
        src_ids, eligible, reason = [], False, ""
        if aid in fw_ids:
            eligible, reason = False, next(r["exclusion_reason"] for r in fw if r["address_id"] == aid)
        else:
            src_ids = _promotion_sources(store, aid, as_of)
            eligible = bool(src_ids)
            reason = "" if eligible else "pool_address_without_promotion_grade_confirmation"
        if aid in surveyed_ids:
            split = S_EVAL
        elif aid in fw_ids:
            split = EXCLUDED
        elif not eligible:
            split = POOL          # in the pool, but carries no promotion-grade confirmation yet
        elif inner_fold == outer_fold:
            split = S_VAL         # leave-one-account-fold-out inside the outer place-block fold
        else:
            split = S_TRAIN
        manifest.append({
            "address_id": aid, "account_id": row["account_id"], "place_block_id": block,
            "split": split, "as_of": asof.to_utc_str(as_of),
            "source_observation_ids": ";".join(src_ids), "eligible_for_training": bool(eligible and split in
                                                                                       (S_TRAIN, S_VAL)),
            "exclusion_reason": ("none" if eligible and not reason else reason),
            "outer_fold": outer_fold, "inner_fold": inner_fold,
            "firewalled": aid in fw_ids,
        })
        n_eligible += int(manifest[-1]["eligible_for_training"])

    _write_csv(os.path.join(out, "supervision_firewall.csv"), fw,
               ["address_id", "account_id", "place_block_id", "exclusion_reason",
                "eligible_for_supervision"])
    _write_csv(os.path.join(out, "supervision_manifest.csv"), manifest,
               ["address_id", "account_id", "place_block_id", "split", "as_of", "source_observation_ids",
                "eligible_for_training", "exclusion_reason", "outer_fold", "inner_fold", "firewalled"])

    counts = {k: sum(1 for m in manifest if m["split"] == k) for k in (S_EVAL, S_TRAIN, S_VAL, EXCLUDED, POOL)}
    member_hash = hashlib.sha256("".join(sorted(m["address_id"] for m in manifest)).encode()).hexdigest()
    receipt = {
        "protocol_version": PROTOCOL_VERSION,
        "valid_as_of": asof.to_utc_str(as_of),
        "rule": ("S-Eval = the 100 surveyed addresses (never trained, never tuned). Firewall = surveyed "
                 "∪ their accounts ∪ their place blocks, excluded from every supervision/feature-fit set. "
                 "S-Train/S-Val = operational supervision (promotion-grade confirmations), nested grouped CV: "
                 "outer folds = place blocks, inner folds = accounts."),
        "counts": {"n_addresses": len(manifest), **counts,
                   "n_firewalled": len(fw), "n_supervision_eligible": n_eligible},
        "firewall": {"n_surveyed": len(dataio.surveyed()), "n_surveyed_accounts": len(
            {ix.addresses[a]["account_id"] for a in dataio.surveyed() if a in ix.addresses}),
            "n_surveyed_blocks": len({ix.block_of(a) for a in dataio.surveyed() if ix.block_of(a)}),
            "union": len(fw_ids), "share_of_corpus": round(len(fw_ids) / max(1, len(ix.addresses)), 4)},
        "grouping": {"outer": "place_block (fold in ps3_place_blocks.csv)", "inner": "account"},
        "member_manifest_sha256": member_hash,
        "test_look_counter": 0,
    }
    # the declared specs are data: register the three populations the protocol allows
    receipt["declared_specs"] = [s.to_json() for s in declared_specs()]
    payload = json.dumps(receipt, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    receipt["receipt_sha256"] = hashlib.sha256(payload.encode()).hexdigest()
    with open(os.path.join(out, "split_receipt.json"), "w", encoding="utf-8") as fh:
        json.dump(receipt, fh, indent=2, sort_keys=True, ensure_ascii=False)
    return receipt


def _promotion_sources(store, address_id: str, as_of) -> list[str]:
    """Observation ids of the promotion-grade confirmations known at `as_of` (the supervision rows)."""
    obs = asof.observations_upto(store, as_of, address_id=address_id)
    if not obs:
        return []
    ev = store.evidence_for([o["observation_id"] for o in obs])
    strong = []
    for o in obs:
        e = ev.get(o["observation_id"])
        if not e or e["polarity"] != "positive" or float(e["weight"]) < config.W_PROMOTE:
            continue
        if o.get("duplicate_claim_of"):
            continue
        strong.append({"weight": float(e["weight"]), "independence": e["independence"],
                       "x": o.get("x"), "y": o.get("y"), "observation_id": o["observation_id"],
                       "duplicate_claim_of": o.get("duplicate_claim_of")})
    if len(strong) < 2:
        return []
    ok, _ = ev_mod.promotion_ok(strong)
    return sorted(s["observation_id"] for s in strong) if ok else []


def _base_spec(spec_id: str, populations, as_of=config.MOMENT, **kw) -> SplitSpec:
    return SplitSpec(spec_id=spec_id, populations=tuple(populations), as_of=asof.to_utc_str(as_of), **kw)


def declared_specs(receipt: dict | None = None) -> list[SplitSpec]:
    """The registry of legal splits. Anything not on this list aborts a metrics run (T15)."""
    return [
        _base_spec("S_EVAL_BASELINE", (S_EVAL,), label_source="surveyed_ground_truth",
                   note="the only place surveyed truth may be read; increments the test-look counter"),
        _base_spec("S_TRAIN_INNER", (S_TRAIN,), label_source="operational_confirmation_proxy",
                   note="ranker fitting, nested grouped CV inner split"),
        _base_spec("S_VAL_INNER", (S_VAL,), label_source="operational_confirmation_proxy",
                   note="challenger selection; never S-Eval"),
    ]


def registry_from_receipt(path: str | None = None) -> list[SplitSpec]:
    p = path or os.path.join(config.DERIVED, "split_receipt.json")
    if not os.path.exists(p):
        return declared_specs()
    d = json.load(open(p, encoding="utf-8"))
    out = []
    for s in d.get("declared_specs", []):
        out.append(SplitSpec(spec_id=s["spec_id"], populations=tuple(s["populations"]), as_of=s["as_of"],
                             outer_grouping=s.get("outer_grouping", "place_block"),
                             inner_grouping=s.get("inner_grouping", "account"),
                             outer_fold=s.get("outer_fold"), label_source=s.get("label_source", ""),
                             protocol_version=s.get("protocol_version", PROTOCOL_VERSION),
                             firewall_receipt_sha256=s.get("firewall_receipt_sha256", ""),
                             note=s.get("note", "")))
    return out


def require_declared(spec: SplitSpec | dict | None, path: str | None = None) -> SplitSpec:
    """Abort unless the split is declared, references §2's protocol, and its firewall receipt matches."""
    if spec is None:
        raise UndeclaredSplit("no SplitSpec supplied: every metrics run must declare its split (contract §2)")
    if isinstance(spec, dict):
        spec = SplitSpec(**{k: (tuple(v) if k == "populations" else v) for k, v in spec.items()})
    if not isinstance(spec, SplitSpec):
        raise UndeclaredSplit(f"not a SplitSpec: {type(spec)!r}")
    if spec.protocol_version != PROTOCOL_VERSION:
        raise UndeclaredSplit(f"SplitSpec references protocol {spec.protocol_version!r}, not {PROTOCOL_VERSION!r}")
    known = {s.spec_id for s in registry_from_receipt(path)}
    if spec.spec_id not in known:
        raise UndeclaredSplit(f"undeclared split: {spec.spec_id!r} (declared: {sorted(known)})")
    if S_EVAL in spec.populations and spec.label_source != "surveyed_ground_truth":
        raise UndeclaredSplit("S-Eval may only be read with label_source=surveyed_ground_truth")
    if spec.label_source == "surveyed_ground_truth" and spec.populations != (S_EVAL,):
        raise UndeclaredSplit("surveyed truth is readable only through the S_EVAL_BASELINE spec")
    if S_EVAL in spec.populations and spec.outer_fold is not None:
        raise UndeclaredSplit("S-Eval is never folded for fitting")
    return spec


def _write_csv(path: str, rows: list[dict], cols: list[str]) -> None:
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c) for c in cols})
