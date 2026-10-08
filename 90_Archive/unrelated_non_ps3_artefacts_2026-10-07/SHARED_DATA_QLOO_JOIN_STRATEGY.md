# SHARED DATA ⇄ QLOO JOIN STRATEGY

**Status: NO JOIN EXISTS TODAY.** This is the audit's finding, not a refusal to work. The strategy below (a) proves the absence on the actual bytes, (b) states what a join would require, and (c) defines the protocol that must be followed *if and when* a dataset with cultural entities is supplied.

Rule adopted from the brief and applied: **never join through fuzzy title matching alone when a stronger identifier exists** — and, additionally: never join through fuzzy matching at all when *no* title exists.

---

## 1. What a Qloo join requires

Qloo's value is an affinity graph over **cultural entities** (works, artists, brands, places, etc.) keyed by entity identity, not by free text. A usable join therefore needs, at minimum:

1. a column whose semantics is a cultural entity (a title, an artist, a venue, a brand), **and**
2. an identifier scheme Qloo recognises (its own entity IDs) **or** a resolvable external ID (IMDb, TMDB, Wikidata, MusicBrainz…) to cross-map through.

Anything less (a name alone, a pincode, an internal loan ID) cannot be joined, and should not be forced.

## 2. Identifier census of the actual pack

Every identifier-like column across all 21 files (full inventory: `docs/DRIVE_DATA_INVENTORY.md` §7):

| Candidate family | Examples | What it keys on | Verdict |
|---|---|---|---|
| Loan/account keys | `account_id`, `address_id`, `visit_id`, `attempt_id`, `ptp_id`, `payment_id`, `trace_id`, `call_id`, `phone_id` | One synthetic borrower, address, or event inside a lending book | **No Qloo mapping exists** — internal, non-cultural |
| Organisation keys | `lender_id` (L01–L06), `agent_id`, `town_id` (T1–T3), `locality_id` (T1-L01…), `poi_id` | A fictional lender, an agent, a synthetic town, a locality, a landmark | **No Qloo mapping** — synthetic names (`Kaveripura`, `Devgarh Nagar`, `Navanagara East`) that correspond to no real, mappable place |
| Quasi-external key | `phones.phone_masked` | A **masked** phone string | Not a Qloo key; unusable even as a contact join |
| Geography | pincodes 960101–980304 (inside `localities`, not on `addresses`) | Synthetic, non-routable 9xxxxx pincodes | Not joinable to any real geographic graph |
| Free text candidates | `addresses.address_text`, `field_visits.remark`, `dial_attempts.remark`, `call_transcripts.text` | Indian street/landmark text, collections remarks, call turns | **Scanned: zero culture tokens** (`film|cinema|movie|theatre|song|music|album|actor|hero|qloo` → 0 matches across all text columns). Nothing to resolve |
| External IDs | IMDb / TMDB / Wikidata / MusicBrainz / Qloo | — | **None present anywhere in the pack** |

## 3. Candidate join audit

For each candidate the brief asked to assess — source → identifier → normalisation → matching method → verification → ambiguity handling:

| Source | Identifier | Normalisation | Matching method | Verification | Ambiguity handling | Verdict |
|---|---|---|---|---|---|---|
| `accounts` / `addresses` / `field_visits` / … | `account_id` etc. | none needed | exact key match | referential integrity is clean (0 orphans) | n/a | **Dead end** — keys are internal; Qloo has no counterpart class |
| `localities` | locality name; pincode | case/diacritics | exact then fuzzy name match | — | — | **Dead end** — synthetic names/pincodes; a match would resolve to nothing meaningful, and would be a fabricated equivalence |
| `landmarks_poi` | 14 landmark *types*, 240 named points | — | name match to a cultural graph | — | 198 duplicate (town, name) pairs would be ambiguous | **Dead end for Qloo** (and, per the pack README, unreliable even for its own purpose) |
| `address_text`, remarks, transcripts | free text | — | any | — | — | **Dead end** — 0 culture tokens; no titles to match |
| (absent) | IMDb / TMDB / Wikidata / title+year | — | — | — | — | **Not available** — these columns do not exist |

## 4. Consequence for the central research question

> *"What can Adjacent learn from real cinema programming data, and where does Qloo add information the dataset alone does not contain?"*

On **this** data pack, the first half has no subject (there is no cinema programming data), and the second half is untestable (there is nothing to join Qloo to). Any number produced by forcing such a join — including any coverage percentage from an earlier resolver exercise — **must not be reported as evidence about this pack**. The old "92.6% Qloo coverage" figure is not reproducible here because no Qloo-resolvable entity exists here at all; if it belongs to a different dataset, it must stay with that dataset and must never be quoted as general Qloo coverage.

## 5. What must be true before a Qloo join is attempted (data-foundation requirements)

1. The dataset contains at least one cultural-entity column (film title, venue, artist, brand…).
2. Each entity carries at least one **standard external identifier** (IMDb/TMDB/Wikidata/MusicBrainz id) or a stable Qloo-internal id.
3. A crosswalk table exists and is versioned, with a recorded extraction date (entity graphs change).
4. The join's purpose is stated before the join (affinity features for which decision?).

None of the four is satisfied by the current pack.

## 6. Protocol — to be followed when such a dataset exists

1. **Identifier hierarchy:** Qloo entity id > Wikidata QID > domain id (IMDb/TMDB) + year > normalised title (+year, +director) > fuzzy title **only with ≥0.95 similarity and manual review**.
2. **Normalisation:** Unicode NFC; case folding; strip diacritics for matching only (keep original); language/transliteration handling recorded per source; version-pinned title table.
3. **Matching:** exact first, then rule-based alias table, then similarity; **two-key rule** — a fuzzy match is accepted only if a second attribute (year, country, director) agrees.
4. **Verification:** sample audit (≥200 pairs, stratified by source), precision target ≥99% for accepted pairs; every accepted pair stored with method + evidence.
5. **Ambiguity:** unresolved and many-to-many pairs go to a manual queue; **never silently pick one**; unmatched entities remain unmatched, with counts published.
6. **Governance:** the crosswalk is a data contract (producer, consumer, version, review date); re-joins on new graph dumps are diffed, not overwritten.

## 7. Data-protection note

The current pack is synthetic ("everything in it is invented"), so there is no personal-data exposure in this audit. If a future foundation contains real venue/programme/attendance data and joins were ever attempted back to individuals or households, re-identification risk becomes a first-class design constraint — recorded here so that the point is not rediscovered later.

**Provenance note.** This document was commissioned as `data/SHARED_DATA_QLOO_JOIN_STRATEGY.md` under an "Adjacent/Qloo" framing. The honest result is a negative finding proven against the actual bytes, plus the protocol that would govern any future join. No join was built, and no synthetic benchmark was created.
