# SUTRA — ADDRESS MEMORY ARCHITECTURE

The memory is the asset. A vendor pin is rented for 30 days [S8]; a locality gazetteer is public; a trained ranker is a
few kilobytes of parameters. What nobody else has — and what SUTRA builds — is a **per-place, append-only, reason-coded
record of what the field has actually confirmed**, with rules for decay, contradiction and identity.

---

## 1. What memory holds (and what it must never hold)

| Stored | Why | Never stored |
|---|---|---|
| **belief versions** (position(s), tier, radius, support, reasons) | the answer, plus how it was reached | an edited/superseded row (no UPDATE path) |
| **observations** (visit / adjudication / ingest / external) with `observed_at` | the only clock; makes as-of reads possible | a visit without its timestamps and provenance |
| **evidence scores** with policy version | re-derive beliefs when the policy changes | an evidence score without reason codes |
| **place identity links** (record ↔ place, merge/split events) | two accounts at one building should share what is known | a silent merge: every link is an event with a reason |
| **alias evidence** (locality/landmark variants seen in text) | feed the resolver and the gazetteer | unvetted aliases promoted into the gazetteer without review |
| **verification tasks & their outcomes** | the loop's to-do list and its history | a task deleted because it was inconvenient |
| **counters** (how many confirmations, from how many independent visits/agents) | the promotion rule depends on them | a "trust score" that hides its composition |

Two explicit non-holds: **vendor content beyond its licence window** [S8], and **raw media** (only hashes + verdicts).

---

## 2. Memory identity: memory belongs to a *place*, not to a row

A collections book contains the same building twice (the audit found 10 duplicated normalised texts, and accounts can
repeat an address). If memory were keyed on `address_id`, the system would learn the same house twice and never let the two
learnings meet.

```
address_record ──(link)──► place (place_key) ◄──(link)── address_record
                             ▲
                             └── belief versions, observations, evidence scores
place_key = sha1(town_id · matched_locality_id · house_number_norm · landmark_anchor?)
            OR  cluster(evidence_x, evidence_y, radius_class)   when text is unresolvable
```

Rules:
* **Linking is evidence-driven and append-only.** Two records link when (a) both resolve to the same `(town, locality,
  house_number)` and are within the tier radius, or (b) evidence coordinates from independent visits fall within the same
  cluster radius for two different records.
* **A merge event is a row** (`place_merge(from, into, reason, observed_at, actor)`), reversible by a later split event that
  cites it. Nothing is destroyed by a merge.
* **Split rule:** if new high-integrity evidence separates two links by more than 2 × radius, the place is split into two,
  and both keep their history (the merge event is annotated, not deleted).
* **Ambiguity is a state, not a guess:** if the link criterion is met by *three or more* records with distinct house
  numbers, the place is marked `AMBIGUOUS_GROUP` and evidence is *not* pooled across them.

Field-agent reality check: agents think in landmarks and streets, not in ids. The place key is the machine's attempt to
match that; the moment it cannot, it says so instead of pooling.

---

## 3. Lifecycle and decay (what expires, what widens, what never dies)

| Item | Decay / expiry rule | Rationale |
|---|---|---|
| raw `trail_point` | **90 days** retention | heavy + privacy; the derived score persists (`PS3_DATA_LINEAGE.md` §6) |
| evidence score | permanent; **weight decays** with age by policy horizon (e.g. a 24-month half-life for a rooftop confirmation, shorter for a coarse one) | addresses change; declining weight is how the system ages |
| belief version | never deleted; **superseded versions compacted** into a summary (counts, extremes, reason histogram) while the current version and any version that supported a decision are kept verbatim | auditability with bounded growth (F16) |
| tier `CONFIRMED` | demotes to `PROBABLE` after the horizon without fresh confirmation; radius widens before the tier drops | staleness is made visible *before* it becomes an error (R15.3) |
| contradiction state | `CONTESTED` persists until resolved by evidence or adjudication; never times out silently | an unresolved contradiction is a fact worth keeping |
| alias candidate | expires if not re-seen within the window | prevents one noisy record from polluting the gazetteer |
| verification task | closes on completion, or by explicit `deferred` with a reason | no silent queue rot |

**Never dies:** the fact that a position *was* once believed, and the fact that it was later demoted. History of belief is
what makes an audit possible.

---

## 4. Contradiction resolution (the hardest part, answered explicitly)

| Situation | Memory behaviour | Resolution path |
|---|---|---|
| Two positive visits, positions within 1 × tier radius | merge into one support set; weighted centroid is *not* used as the answer — the answer stays a candidate-backed position, and the evidence is the support | automatic |
| Two positive visits, positions > 2 × tier radius | keep **both** supports; state `CONTESTED`; radius = max(tier radius, half the separation); queue a task | high-integrity third visit, or human adjudication |
| A new confirmation far from a `CONFIRMED` position | do **not** overwrite; create a second supported position, mark `CONTESTED`, and raise priority (this is the signature of a genuine address change, F5) | after two *independent* high-integrity confirmations at the new position, the *primary* moves and the old position is retained as `historical` |
| Negative outcome vs a confirmed position | no movement; `record_suspect` increment only | re-verification |
| Coarse candidate (locality) vs fine evidence (rooftop) | fine evidence wins for the position; the coarse candidate stays as a fallback with its own reason | automatic, recorded |
| Two agents disagree, one flagged | the flagged evidence is down-weighted, not discarded; if the state flips, the flip names the weight that caused it | automatic + audit |
| Vendor pin vs field evidence | field evidence wins if `w_place` ≥ threshold; otherwise the pin stays as an arm, never as truth | automatic |

**Rule of the house:** the memory never averages its way to a coordinate. Positions are *candidate-backed* (they come from
an address point, a locality centroid, a building anchor, or an evidence cluster). Averaging creates coordinates that
correspond to no real place — the classic failure of "learned" geocoders.

---

## 5. States (what a place can be, and how it leaves each state)

```
UNSEEN ─► COLD ─► WARM ─► CONFIRMED ─► STALE ──┐
   │         │        │         │              │
   │         └────────┴─────────┴──► CONTESTED ┴─► CONFIRMED / APPROXIMATE / UNPLACEABLE
   └──────────────────────────────► UNPLACEABLE  (a legitimate terminal state)
```

| State | Meaning | Entered by | Leaves by |
|---|---|---|---|
| `UNSEEN` | no record of evidence | ingest | first observation |
| `COLD` | has candidates, no field evidence | candidate build | first visit |
| `WARM` | ≥ 1 usable visit, below promotion threshold | evidence weight ≥ w_min | second independent confirmation |
| `CONFIRMED` | ≥ 2 independent confirmations, coverage-verified radius | promotion rule [S49] | staleness → `STALE`; contradiction → `CONTESTED` |
| `STALE` | past validity horizon without fresh evidence | decay rule | new confirmation, or demotion to `PROBABLE` with a widened radius |
| `CONTESTED` | contradictory strong supports | contradiction rule | resolution paths (§4) |
| `UNPLACEABLE` | no candidate and/or no evidence; explicit reason (`outside_town`, `no_local_evidence`, …) | resolver + candidate build | gazetteer/memory improvement, or a visit that supplies a position |

The 237 `OUT` records in the official data are `UNPLACEABLE` today with reason `outside_town` — a state the system must be
able to *hold* indefinitely without pretending.

---

## 6. Query patterns (and why the store is shaped this way)

| Query | Frequency | Shape | Design feature that makes it cheap |
|---|---|---|---|
| `belief_at(address, as_of)` | per resolve, per feature build | indexed range scan on `(address_id, as_of DESC)` | append-only versions + index |
| `support(address)` | per resolve / review | fetch current version's support JSON | denormalised support to avoid joins on the hot path |
| `observations(address, window)` | per review, per retrain | range scan on `(address_id, observed_at)` | partitioned by month |
| `place(record)` | per belief write | key lookup + link table | place identity table |
| `contradictions(town)` | per review dashboard | partial index on state | state column |
| `tasks(priority, state)` | per shift | ordered index | priority is a computed column, deterministic |
| `aliases(town, name)` | per resolve | trie/sorted index | alias table scoped by town (F14) |

---

## 7. Memory and leakage (the two must never touch wrongly)

* Every read used for a decision carries `as_of`; a read *without* `as_of` is only allowed in the review UI, and such a
  read can never feed a model.
* A memory write caused by a visit cannot be read by the decision that caused that visit — enforced by construction, since
  the decision's `as_of` precedes the visit's `observed_at` (`PS3_SYSTEM_DESIGN.md` §2, invariant 1).
* Warm feature sets are built with the address's cut-off; the receipt records it (`features_warm_v2.receipt.json`). *(Pre-contract warm receipts are archived under `data/derived/superseded_pre_contract_2026-10-07/`; the v2 set is produced by `tools/build_candidates.py`.)*
* The memory is **not** an evaluation set: performance is measured on the 100 surveyed records and on adjudications outside
  the training window, never on "what the memory currently believes".

---

## 8. Governance of memory content

* **Who may write:** only the fast loop (evidence), the adjudication workflow (human confirmation), and the reviewed alias
  process. No ad-hoc writes; every row names its actor.
* **Who may read:** consumers declare a purpose; the eligibility gate is separate (`PS3_SYSTEM_DESIGN.md` §8).
* **What may be corrected:** a belief can be superseded (new version citing the reason), never edited. A data-protection
  request is honoured by *redaction of raw fields* (trail/media) while derived aggregates that no longer identify a person
  are retained, with the redaction event itself recorded — the audit trail is not silently rewritten.
* **What is periodically recomputed:** agent baselines (rolling), alias candidates (expiry), verification priorities
  (daily), calibration maps (per slow loop).

---

## 9. Why a cache cannot replace this

| Cache-like alternative | What it cannot do |
|---|---|
| "Last geocode seen for this text" table | no credibility, no contradiction, no decay, no provenance, no reason codes — and it silently serves whichever value was written last, including a poisoned one |
| Vendor "permanent geocoding" product [S4] | it is *their* memory purchased; it freezes their error and gives us no mechanism to learn from our own visits |
| Model-only memory (fine-tune on visits) | ungovernable at this data scale, unreproducible per record, and it cannot express "I have two plausible places, one of them contested" |
| An average of evidence points | produces coordinates that are not places (§4) |

**What this changes in the workflow:** an operator can ask *why* the system believes a coordinate, see the confirming
visits, their weights and their reasons, and act on the uncertainty — instead of being handed a point with no history.


## Amendment M1 — place identity by evidence: two thresholds, no forced merges · 2026-10-07

**Measured.** Independent met visits place **191 addresses into 81 co-location clusters** (≤30 m; every pair a
different account; 39 of the blocks cross the official split) `[S94]`. In the opposite direction, an account's two
met-visited addresses sit a **median 3,011.6 m** apart — **0% within 100 m** (38 pairs). Account identity says
nothing about place identity.

**What changes.**
1. **Identity key vs render key.** The place-identity key keeps the trailing `- <6 digits>` token; stripping it merges
   193 distinct village rows into 70 false places. The render key exists only for parsing. Cleaning produces both.
2. **Two thresholds with review between them** [S72]: `CONFIRMED_MERGE` (independent met visits inside the co-location
   radius) · `POSSIBLE_MATCH` (human/field confirmation queue) · `DISTINCT`. No path merges on text similarity alone,
   and no path merges on `account_id`.
3. **Contradiction stays a state, not an error** (D06/D07 unchanged): a block whose members' evidence disagrees stays
   `CONTESTED` until a visit or an operator resolves it; nothing is overwritten.
4. **Consistency expectations from measurement:** repeat met visits to one place agree at median **77.7 m** (same
   agent) vs **75.8 m** (different agent) `[S94]` — memory is agent-independent, so collector identity may never
   decide a merge.
5. **Memory's value is validated leave-block-out** (Amendment A1): 24.0 m overall vs **21.1 m** on non-training
   entities, against a pin at 380.3 / 383.7 m.

**What this changes in the real workflow:** two collectors working one building for two borrowers finally share one
verified place — and the system asks before it decides they are the same.

---


## Amendment M3 — ownership: belief engine vs memory store vs projection (2026-10-07)

The audit-era phrasing let "belief" and "memory" blur. Ownership is now explicit:

| Layer | Owns | Is | May never |
|---|---|---|---|
| **Belief engine** | the current best answer for one address: candidate, tier, radius, reasons, evidence counts | a **pure, deterministic calculation** over observations + memory (recomputable from the append-only log; same inputs → same output, `evidence_policy_version` pinned) | persist state of its own; be the source of truth for anything |
| **Memory / event store** | `observation` (visit, adjudication, ingest), `evidence_score`, `belief_version` snapshots, place clusters | **the authoritative persistence**: append-only, as-of queryable, the only thing that survives a restart | be edited in place; contain model-derived values marked as truth |
| **Projection** | `address_current`-style read models, caches, offline packs, per-place aggregates | **query optimisation** — derived, versioned by the belief version it was built from, discardable and rebuildable at any time | be read by a model as a feature source (features come from the store, as-of) |

Consequences: (i) any belief can be re-derived and diffed after a policy change (S11/D07); (ii) recovery = restore
store + replay — the projection is never restored *as truth*; (iii) contradiction handling (CONTESTED, MOVED_SUSPECTED
per F2) lives in the **store's status field**, not in anyone's local cache; (iv) the offline app's local database is
a projection plus an outbox of pending observations — never a divergent belief store (sync contract,
`PS3_MLOPS_ARCHITECTURE.md`).
