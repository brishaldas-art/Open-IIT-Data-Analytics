# PS3 — ASSUMPTION REGISTER & PROBLEM RE-READ

**Problem statement 3:** *An address geocoder that learns from field visits. Indian addresses are descriptive and landmark-based, mixed-language, transliterated, misspelt. Commercial geocoders land at locality/pincode centroids. Output must be lat/lon + confidence radius + landmark-based directions, continuously learning from new successful visits. The field app must work offline.*

Tags: `[PS]` problem statement · `[EXT]` external research · `[INFER]` our inference · `[UNVERIFIED]` unconfirmed.

---

## 1. The eleven questions

### 1.1 What is the exact user/customer?
| Layer | Who | Tag |
|---|---|---|
| Paying customer | The lender / ARC | `[PS]` |
| **Primary user of the output** | The **field agent** standing on a street at 4pm with a phone | `[PS]` implies ("field app", "offline") |
| Operational owner | Field operations manager allocating beats and slots | `[INFER]` |
| Silent beneficiary | **Household members, neighbours and shopkeepers** who must not learn about the debt | `[INFER]` — from the RBI third-party rule `[EXT]` |
| Data owner | CN's address/contact-data steward | `[INFER]` |

### 1.2 Who actually uses the output?
`[PS]` The field agent (pin + radius + directions), offline. `[INFER]` The allocator (is this address visit-worthy at all?) is the *higher-value* consumer, because that decision costs ₹220–370 per slot `[EXT]`/`[MODEL]`.

### 1.3 What decision are they making?
1. **Do we send a recovery notice / visit to this address at all?** (RBI now requires ≥1 day advance notice before the first visit `[EXT]` — so sending the notice is itself the irreversible act)
2. **Where exactly do we send the agent**, and what do we tell them to look for?
3. **Do we trust what came back?** (integrity)
4. **Has this borrower moved?** (a contactability signal that belongs to PS2)

### 1.4 What does "success" mean operationally?
`[INFER]`, ranked:
1. **Right-door rate** — visits that reach the intended household
2. **Zero notice-to-wrong-party events** — a notice delivered to the wrong home is a disclosure event
3. **Field-slot yield** (borrower met / slots spent), and slot cost
4. **Calibrated abstention** — the system says "I don't know" instead of guessing
5. Distance error (median and p90) — necessary but **not** the headline, because a 90 m error in a dense colony can be one building wrong

### 1.5 What does CN gain?
`[EXT]` CN already advertises **32% higher field efficiency** and RBI-compliant audit trails. So the gain is not "field efficiency" in general — it is:
1. **A number they cannot currently produce**: the confidence of each address, and the notice/visit decisions that confidence blocks
2. **A defensible answer to an RBI inspection** on exactly the control that is hardest to prove (advance notice delivered to the right door; borrower/guarantor-only contact)
3. **An asset that compounds**: every successful visit improves the address for the *next* account at that landmark `[PS]` requires continuous learning

### 1.6 What could go wrong?
| Failure | Mechanism | Tag |
|---|---|---|
| Notice disclosure | Advance notice sent to an address 1.3 km off in a dense colony | `[INFER]` ← new, highest severity |
| False confidence | Radius says 90 m; the actual home is 900 m away in a different lane | `[PS]` |
| Label poisoning | Agent fabricates a check-in; geocoder learns the wrong place | `[PS]` implies |
| Purpose confusion | Agent meets the borrower at his shop and the system treats *the shop* as home | `[PS]` |
| Staleness | Borrower moved 2 years ago; address is "correct" and useless | `[PS]` |
| Offline divergence | Two agents in the same locality hold different frozen packs | `[INFER]` |
| Commercial-ToS breach | Caching a commercial geocoder's coordinates as training data | `[EXT]` — Google/MapmyIndia terms restrict caching |

### 1.7 What constraints are mandatory?
| Constraint | Tag |
|---|---|
| Offline-capable field app | `[PS]` |
| Confidence radius output, not just a point | `[PS]` |
| Landmark-based, local-language directions | `[PS]` |
| Continuous learning from new successful visits | `[PS]` |
| No third-party debt disclosure (RBI) | `[EXT]` |
| ≥1 day advance notice before first visit (RBI) | `[EXT]` |
| Minimum-necessary data to agents; no employer/workplace details shared | `[EXT]` |
| Geotagged visit evidence already expected by buyers (Mobicule/Credgenics ship it) | `[EXT]` |

### 1.8 What data is required?
`[PS]` successful-visit GPS (which may be home, shop, workplace or a road), failed-visit GPS, GPS trails, dwell time, visit outcomes, agent remarks, nearby confirmed locations.
`[UNVERIFIED]` Whether CN's sandbox has **trails** (not just final points), **dwell**, **attestation/mock-location flags**, **failed-visit coordinates**, and **multilingual remarks**. These four determine whether the integrity model and the purpose classifier are buildable or just aspirational.

### 1.9 Explicitly required vs merely suggested
| Element | Status |
|---|---|
| Geocode with confidence radius | **Required** `[PS]` |
| Landmark-based directions | **Required** `[PS]` |
| Learn continuously from visits | **Required** `[PS]` |
| Offline operation | **Required** `[PS]` |
| Parse → normalise → candidates → rank → robust estimator → conformal radius → directions | Our pipeline `[INFER]` |
| libpostal / deepparse / IndicXlit / LambdaMART / GeoConformal / H3 | Our tool choices `[INFER]`, **all replaceable** |
| Integrity/anti-fabrication model | Our addition — `[INFER]`, but strongly implied by "fake check-ins" being a named challenge `[PS]` |

### 1.10 Our own assumptions (the ones we must not smuggle into the pitch as facts)
| # | Assumption | Tag |
|---|---|---|
| B1 | Field-visit volume is sufficient to train a geocoder in CN's portfolios | `[UNVERIFIED]` — **at ₹18.8k average digital-PL ticket, visits are rare; this may be false for the highest-volume portfolio** |
| B2 | Successful-visit GPS is a good label for *home* | `[UNVERIFIED]` — `[PS]` explicitly says it may be shop/workplace/road |
| B3 | Third-party geocoders can be used at runtime but not cached as training data | `[EXT]` |
| B4 | An outcome-learning Indian address engine does not already exist | **FALSE** — see §1.11 |
| B5 | Calibrated radii are not commercially available for India | **MOSTLY FALSE** — Delhivery GeoNaksha returns an *error radius* `[EXT]` |
| B6 | Agents can be trusted to self-report | **FALSE by design** — hence the integrity model |

### 1.11 The three findings that invalidate part of our previous PS3 story
1. **Shiprocket Address Intelligence** `[EXT]`: NLP + spatial reasoning, **learns from every successful delivery and every delivery-partner correction**, claims **72.69% of addresses within 100 m** and **90.57% within 500 m**, sub-200 ms on CPU. → *"Nobody learns from field outcomes"* is false. It exists, at national scale, in India.
2. **Delhivery GeoNaksha / Maps** `[EXT]`: LLM geocoding that returns **structured coordinates with an error radius for positional confidence**, validates against **4 billion+ deliveries / 3M+ daily**, and offers **Address Verification ("has this address been visited in the last N months?")**. → *"Geocoders return a point with no uncertainty"* is false, and *"visit-history verification"* already ships — in logistics.
3. **Google Address Validation API for India** `[EXT]`: ML parsing that returns **component-level accuracy**, and explicitly **distinguishes residential from commercial** addresses. → Part of our "place-purpose classification" novelty is also productised.

**Consequence for the pitch.** PS3 cannot be sold as "a better geocoder", "an outcome-learning geocoder", or "the first to give uncertainty". The defensible residue is narrower and — fortunately — sharper:
- **(i)** these systems learn from **deliveries**; collections needs evidence from **recovery visits**, whose failure modes differ (refusal, borrower not at home, hostile household, agent incentive to fake);
- **(ii)** nobody maps address confidence to a **compliance decision** — *whether the RBI-mandated advance notice may be sent and whether a recovery action may be taken at that door*;
- **(iii)** nobody treats a returned visit as **weighted evidence with an integrity discount** rather than a fact;
- **(iv)** nobody separates **home / workplace / shop / a family member's address** for the specific purpose of *not exposing a debt to the wrong person*.

That residue is the PS3 product. It is narrower, more credible, and much harder for a logistics company to copy.

### 1.12 What we should NOT claim
- Not "we beat Google on Indian addresses" (Shiprocket/Delhivery already claim better, and we cannot verify either).
- Not "calibrated coverage guarantees" as a headline (conformal on a handful of synthetic visits is unfalsifiable).
- Not "we replace the geocoder" (we consume one).
- Not "our model found the home" without stating the **integrity weight** and the **abstention rate** alongside it.
