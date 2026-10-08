# SUTRA — implementation demo (6 scenes)

Address: `AD000005` — *behind PDS Shop, Shivaji Nagar, Devgarh Nagar - 970202*  (town T2, residence)

Runtime versions: {"schema": "sutra-1.0", "rules": "candidate-rules-v2", "evidence": "evidence-policy-v3", "radius": "radius-map-v1"}

### Scene 1 — a cold, badly written address

This address has no evidence at all in the official history: cold, and badly written.
belief before any visit: tier=APPROXIMATE status=STABLE radius=809.8 m (stratum locality, basis empirical_p80, n=24)
resolve(as_of=2026-06-04T00:00:00Z)
  -> frozen_baseline @ locality · APPROXIMATE/STABLE · ±810 m (empirical_p80, n=24, stratum locality) · VERIFY_FIRST (tier_approximate)
     candidate c-8ee3b8f3763a · arm=frozen_baseline · granularity=locality · x=512.8 y=-2797.8
     reasons: cold_start_no_field_evidence, promotion:not_ok, resolution:address_id_given
     address_purpose=UNKNOWN · request_purpose=FIELD_NAVIGATION · directions=Ration Shop ~460 m, bearing S, behind it
  the address still gets an answer — but the answer carries its own uncertainty and the gate
  says VERIFY_FIRST (tier_approximate): go and verify before anything irreversible happens.

### Scene 2 — one field observation: evidence weighting, not a trust flag

submitted a weak visit (dwell 45 s, GPS ±42 m, photo hash already seen elsewhere)
  evidence weight = 0.35625 · reasons = ['business_hours', 'dwell_short', 'gps_coarse', 'media_present', 'outcome:met_borrower']
  belief now: tier=APPROXIMATE status=STABLE · the coordinate did not move: candidate unchanged (512.8 is the same x as before)

### Scene 3 — two independent confirmations: belief + memory update

submitted a second visit (different collector, 9 days later, distinct photo, dwell 300 s, GPS ±8 m)
  evidence weight = 0.95 · reasons = ['business_hours', 'gps_fine', 'media_present', 'outcome:met_borrower']
  belief after one confirmation -> tier=PROBABLE status=STABLE
submitted a third visit (third collector, 9 days later, distinct photo) — now the independence tuple is satisfied
  evidence weight = 0.95 · belief -> tier=CONFIRMED status=STABLE version v4
  place PL-AD000005 state=CONFIRMED · members=['AD000005'] · identity_rule=colocation<=30m|adjudicated

### Scene 4 — the same place, later: a better answer

resolve(as_of=2026-06-25T09:00:00Z)
  -> field_evidence @ rooftop · CONFIRMED/STABLE · ±540 m (empirical_p80, n=24, stratum locality) · SERVE (purpose_home_like)
     candidate c-0f0b6f6581c1 · arm=field_evidence · granularity=rooftop · x=1269.0 y=-259.0
     reasons: cross_arm_agreement, field_confirmed_x2, promotion:ok, resolution:address_id_given
     address_purpose=HOME_LIKE · request_purpose=FIELD_NAVIGATION · directions=none
  compare scene 1: tier APPROXIMATE -> CONFIRMED, radius 809.8 -> 539.9 m, arm -> field_evidence
  winning arm: field_evidence — store observations (median of agreeing independent check-ins)
    backed by 2 independent check-ins (spread 2.2 m): demo-FA302-2026-06-14T09:00:00Z, demo-FA304-2026-06-23T09:00:00Z
  the top-3 arms by score, as the ranker reported them:
    1.052  field_evidence     primary_eligible=True
    0.982  memory             primary_eligible=True
    0.954  field_evidence     primary_eligible=False

### Scene 5 — a low-integrity negative: doubt widens, the coordinate does not move

negative evidence weight = 0.0 (polarity=negative, reasons=['outcome:address_not_traceable', 'negative_no_coordinate_claim'])
  coordinate before: (1269.0, -259.0)  after: (1269.0, -259.0)  -> identical
  radius 539.9 -> 566.9 m (widen_reason=negative_accumulation) · status STABLE -> STABLE
  one bad visit can no longer be mistaken for a finding: it costs confidence, not accuracy.

### Scene 6 — offline field capture, then replay

pack pack-T2-7247f0bd3d96 · 952 addresses · 1774492 bytes · valid until 2026-06-08T00:00:00Z · contains polygons=False evidence=False truth=False
  download -> verified=True
  airplane mode: captured 2, outbox queue = 2; the server store still holds 5582 observations — none of them these two
  reconnect: drained 2 in local_seq order [1, 2] -> server belief v7 tier=CONFIRMED status=STABLE
  queue left = 0
resolve(as_of=2026-07-18T10:00:00Z)
  -> field_evidence @ rooftop · CONFIRMED/STABLE · ±567 m (empirical_p80, n=24, stratum locality) · SERVE (purpose_home_like)
     candidate c-c9d499fef641 · arm=field_evidence · granularity=rooftop · x=1269.0 y=-259.0
     reasons: cross_arm_agreement, field_confirmed_x4, negatives_independent=1, promotion:ok, resolution:address_id_given
     address_purpose=HOME_LIKE · request_purpose=FIELD_NAVIGATION · directions=none
  every claim above is attributable: {"rule_version": "candidate-rules-v2", "radius_map_version": "radius-map-v1", "evidence_policy_version": "evidence-policy-v3", "schema_version": "sutra-1.0", "gate_rule_version": "gate-v2", "purpose_rule_version": "purpose_rules-v1", "directions_rule_version": "directions-v1"}
