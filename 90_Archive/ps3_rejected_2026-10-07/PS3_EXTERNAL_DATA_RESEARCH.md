> ## REJECTED / SUPERSEDED — archived 2026-10-07 (final data policy)
>
> **External-data augmentation was considered during research but rejected by final project decision.**
> The final PS3 system uses **only the official CreditNirvana dataset and the legitimately PS3-relevant shared data**.
> Nothing in this document is an active plan: no arm described here may enter S4 candidate generation, the experiment
> grid, the training set, or any headline metric. It is retained **in the archive only**, as provenance for how the
> decision was reached. The binding statement is `PS3_FINAL_DATA_AND_ARCHITECTURE_FREEZE.md` (active workspace).
> Register entries S39–S47 are marked superseded/rejected accordingly.

---

# SUTRA — EXTERNAL DATA RESEARCH

**Purpose.** Decide, per candidate dataset: what it would actually change in the pipeline, whether we are *allowed* to
ship with it, what it costs, and how we would know it helped. The honest headline comes first.

> **Status: nothing external is loaded.** DATASET B (`data/external_research/`) is empty on purpose. Two of the four
> strongest candidates are licence-restricted, and the licence-clean ones must earn their place through experiments
> I/J/H before a single row enters a shipped artefact. This document is the *decision record and the plan*, not a claim
> of results. Every source is catalogued in `PS3_SOURCE_REGISTER.md` ([S40]–[S50] and the licence group).

---

## 1. What we are actually short of

| Gap | Why it matters | Can external data close it? |
|---|---|---|
| **Street-level and rooftop anchors in the target towns** | the audit's survey shows street 108.6 m, locality 385.9 m, pincode 1,375.8 m medians; only 1.7% of vendor pins are rooftop | **Partly.** Address-point and building-footprint sources can supply anchors, but India address-point coverage is uneven and must be measured per town |
| **A refusal region** ("no building here") | `UNPLACEABLE` needs evidence of absence, not just absence of evidence | **Partly.** Building footprints / open buildings give a weak "does a built structure exist" signal |
| **Road/street geometry for street-level snapping** | would allow `street` addresses to be refined to an anchor | **Partly.** OSM road graph is available; but our dataset has no lat/lon CRS, so this is a *deployment* capability, not something we can validate on Domain A |
| **Name/alias variants (locality, landmark)** | 8.9% of pincode-shaped tokens match nothing; landmark names repeat across towns | **Weakly.** OSM/Overture POI names could supply aliases; the audit's 14-distinct-name landmark table makes alias work look unpromising here but relevant in reality |
| **Postal truth** | pincodes in text are hypotheses | **Partly, and it is licence-blocked** (see §3) |
| **Human-labelled accuracy for the loop** | the real currency; no external source can supply it | **No.** Only field visits and adjudication can |

**What external data cannot do here:** it cannot supply ground truth, it cannot fix a wrong check-in, and it cannot make
the field loop honest. The loop is the product (S36–S38, S49); gazetteers are supporting cast.

---

## 2. Candidate catalogue (with the shippability verdict)

| # | Dataset | Licence / class | Geographic fit | What it changes | Verdict |
|---|---|---|---|---|---|
| 1 | **Overture Addresses** [S43] | CDLA Permissive 2.0 (+ ODbL where OSM-derived) | global; India coverage varies by town | a second, licence-clean candidate arm of address points; enables `street`-level candidates without the vendor | **TEST (I/J).** Highest expected value. Ship only if the ablation shows a hit-rate gain on S-Eval |
| 2 | **OSM via Geofabrik (India extract, ODbL)** [S42] | ODbL — attribution **and share-alike** duties on derived databases | dense in cities, sparse elsewhere | road geometry + POI names; a locality/landmark alias source | **TEST, cautiously.** Share-alike forces a legal decision on the derived index before shipping; recorded in the lineage file |
| 3 | **Google Open Buildings 2.5D** [S44] | CC BY 4.0 / ODbL | Global South; India covered reasonably | "does a built structure exist near this point?" → plausibility score, corroboration of a candidate | **TEST.** Cheap, clean licence, and it directly feeds the integrity/corroboration layer |
| 4 | **Microsoft Building Footprints** [S45] | ODbL | India available per region | same role as (3); useful as an *independent* source for corroboration | **TEST as a second opinion**, not as a duplicate of (3) |
| 5 | **DIGIPIN grid** [S41] | Department of Posts, published open implementation | national | a *stable, shareable, code-form* output for a confirmed coordinate — the shippable expression of our answer, not an input | **BUILD (cheap), as output encoding only.** Not a data source for candidate positions |
| 6 | **India Post PIN directory** [S40] | NDSAP **non-commercial** | national | pincode → locality/post-office mapping | **RESEARCH ONLY.** Cannot ship; may be used to *evaluate* our own pincode logic in a private experiment |
| 7 | **data.gov.in catalogues (NDSAP)** [S40] | non-commercial (dataset-dependent) | national/state | administrative boundaries, some local gazetteers | **RESEARCH ONLY** unless a specific licence says otherwise |
| 8 | **OpenAddresses** [S46] | open (per-source) | **thin in India** | would be ideal; measured coverage is poor here | **RECORDED LIMITATION.** Do not plan on it |
| 9 | **Nominatim** [S47] | TOS: ≈1 req/s, no bulk, attribution | global | reverse/forward lookups for spot checks | **TOS ENVELOPE.** Never a per-request dependency; any use is offline, cached, and must respect the cap |
| 10 | **Amazon Last Mile Routing Challenge** [S39] | **CC BY-NC 4.0** | 5 US metros | stop-sequence and stop-clustering research | **RESEARCH ONLY** (non-commercial). Never enters a shippable artefact |
| 11 | **Vendor geocoders (Google/Mapbox/HERE/TomTom/Mappls)** [group A in the register] | commercial TOS; caching limits (Google 30 days; Mapbox sells a permanent-geocoding product) | best coverage | an additional candidate arm + comparison baseline | **COST-GATED.** Used in evaluation only in this project (calls cost money and the licence forbids storage beyond the cache window); the operational substitute is `vendor_pin` from Domain A |

---

## 3. The licence rules we operate under (these are constraints, not preferences)

1. **Classify every row.** `licence_class ∈ {open_attribution, open_sharealike, vendor_tos, noncommercial_research}`.
   Only the first two may enter a shipped artefact; `open_sharealike` additionally requires a decision about derived-database
   duties (ODbL). The loader refuses `shippable = false` rows.
2. **Never overwrite official data.** External rows are new rows with `provenance = external`, never updates to
   Domain A (`PS3_DATA_LINEAGE.md` §1).
3. **Vendor content is not ours to keep.** Google's terms cap caching (30 days for geocoding results), which is precisely
   why SUTRA's *own* memory — validated field evidence — is the asset, and a vendor pin is a transient input.
4. **Non-commercial means non-commercial.** S39 (Amazon) and S40/S41-NDSAP rows are used only in private research runs and
   are excluded from every shipped index and every "official benchmark" line.
5. **Attribution is a build task, not a footnote.** Any shipped artefact built on OSM/Overture/Open Buildings carries the
   attribution file, generated by the build, listing each source and licence.

---

## 4. How each candidate is tested (the ablation that decides)

| Experiment | Question | Pass condition |
|---|---|---|
| **H** (official only) | the frozen floor | baseline numbers |
| **I** (official + external candidates) | does adding the arm improve candidate coverage and S-Eval hit-rate? | hit-rate@100 m improves beyond the bootstrap interval, at acceptable index size; else the arm is dropped |
| **J** (dynamic retrain with/without external features) | do external features help under the loop, or only add drift surface? | no degradation under time splits, or the arm stays out |

Rule for a shipped build: **an external source enters production only if it improves a pre-registered metric on S-Eval
and carries a licence class we may ship.** "It might help" is not a reason. Every test reports the three-line shape:
A) official-only · B) official + external (research) · C) ablation delta.

---

## 5. Practical build notes (so the plan is executable)

* **Overture + OSM:** pull per-state extracts (Geofabrik state files rather than the 1.6 GB national file), build a local
  SQLite/R-tree index keyed by town, keep only address points/POIs inside our three town envelopes. Expect tens of MB per
  town, not GB.
* **Open Buildings / MS Footprints:** raster/polygon lookups at candidate positions only — a boolean plus a distance-to-
  nearest-structure feature. No global join.
* **DIGIPIN:** generate the code for our output coordinate at serve time (a pure function of lat/lng, [S41]); in this
  dataset (local metric plane) the code is computed only when a real CRS is supplied, so the capability is *implemented
  and switched off* until then — no fake coordinates.
* **Every ingest** writes the metadata block from `PS3_DATA_LINEAGE.md` §4, then `tools/check_workspace.py` must still
  pass (licence recorded for each external artefact).

---

## 6. What we will NOT do (and why)

| Temptation | Why not |
|---|---|
| Scrape or bulk-download Google/Mapbox results to build a private address database | violates TOS and caching limits; poisons the benchmark; the whole point is a *licit* own asset |
| Ship non-commercial data (Amazon LMRRC, NDSAP) | licence; would also misrepresent the benchmark |
| Treat Open Buildings footprints as addresses | a building is not a postal address; it corroborates, it cannot resolve house numbers |
| Use OSM addresses as ground truth | crowd-sourced; useful as candidates, invalid as labels |
| Buy a vendor "permanent geocoding" cache and call it our memory | it is *their* memory purchased; our asset is field-validated belief, not a rented lookup table |
| Add external data now, before the official-only floor is frozen | the commission's order: benchmark first. A floor measured after augmentation is not a floor |
