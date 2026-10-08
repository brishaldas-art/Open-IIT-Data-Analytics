/**
 * SUTRA contract types.
 *
 * These mirror the payloads the runtime actually returns (captured from the live service on
 * 2026-10-08 and kept verbatim in `fixtures/captured.json`). The backend is authoritative:
 * if a field is not produced by `sutra/views.py`, it does not belong here.
 *
 * Nothing in this app re-derives backend decisions. Tier, status, radius, gate action, evidence
 * weights, eligibility and priority are rendered exactly as received.
 */

// ── shared ────────────────────────────────────────────────────────────────────────────────────
export type GateAction = 'SERVE' | 'VERIFY_FIRST' | 'REFUSE'
export type Tier = 'CONFIRMED' | 'PROBABLE' | 'APPROXIMATE' | 'UNPLACEABLE'
export type Status = 'STABLE' | 'MOVED_SUSPECTED' | 'CONTESTED' | 'STALE' | 'UNPLACEABLE'
export type Polarity = 'positive' | 'negative' | 'ambiguous'

export interface AsOfMetadata {
  as_of: string | null
  computed_at?: string
}

export interface Coordinate {
  x: number
  y: number
  granularity: string
  coordinate_space: string
  radius_m: number
}

export interface Uncertainty {
  radius_m: number
  basis: string
  nominal: number | null
  measured_coverage: number | null
  n_calibration: number
  source_stratum: string | null
  fallback_applied: boolean
  widened: boolean
  widen_reason: string | null
  radius_map_version: string
}

/** A typed reason, composed by the backend. The frontend never parses `code`. */
export interface ReasonCode {
  code: string
  kind: string // arm_prior_choice | granularity | support | doubt | score_term | …
  subject: string | null
  effect: number | null // score contribution, when the code is a scored term
  direction: 'positive' | 'negative' | 'neutral'
  label: string
}

export interface CandidateRow {
  candidate_id: string
  arm: string
  score: number
  rank: number
  granularity: string | null
  primary_eligible: boolean
  reasons: string[] // raw backend score terms (displayed verbatim, never parsed)
  lost_reason: string[]
  score_margin: number
}

export interface CandidateRef {
  candidate_id: string
  arm: string
  score: number | null
  primary_eligible: boolean
  reasons: string[]
}

export interface EvidenceSummary {
  n_observations: number
  n_positives: number
  negatives_independent: number
  independent_confirmations: number
  duplicate_claims: number
  positive_weight_sum: number
  negatives_move_coordinate: boolean
  radius_widened: boolean
  widen_reason: string | null
}

export interface DecisionTicket {
  headline: string
  case_id: string
  town_id: string | null
  gate: {
    action: GateAction
    reason: string
    rule_version: string
    request_purpose: string
  }
  answer: {
    candidate_id: string | null
    arm: string | null
    granularity: string | null
    score: number | null
    tier: Tier
    status: Status
  }
  why: ReasonCode[]
}

export interface VerificationTask {
  task_id: string
  kind: string
  cause: string
  state: string
  priority: number
  town_id: string
  address_id: string
  place_id: string
  tier: string
  status: string
  negatives_independent: number
  radius_m: number
  rule_version: string
  at: string
  recommended_action: { kind: string; label: string; clears_when: string }
  evidence_refs: string[]
  evidence_refs_basis: string
}

export interface ResolveResponse {
  // —— contract v1 blocks ——————————————————————————————————————————————————————
  coordinate: Coordinate | null
  uncertainty: Uncertainty | null
  alternatives: CandidateRow[]
  decision_ticket: DecisionTicket
  evidence_summary: EvidenceSummary | null
  task: VerificationTask | null
  as_of: string | null
  computed_at: string
  versions: Record<string, string>
  resolution: string
  // —— legacy flat fields (kept: every consumer that predates v1 still works) ——
  address_id: string | null
  address_purpose: { class: string; confidence: string; basis: string[]; model_version: string }
  candidate: { candidate_id: string; arm: string; x: number; y: number; granularity: string; arm_rank: number; licence_class: string; as_of_valid?: string; source_ref?: string; provenance?: Record<string, unknown> } | null
  candidate_id: string | null
  granularity: string | null
  tier: Tier
  status: Status
  radius_m: number | null
  radius_basis: string | null
  nominal: number | null
  measured_coverage: number | null
  n_calibration: number | null
  source_stratum: string | null
  widened: boolean | null
  widen_reason: string | null
  reasons: string[]
  score: number | null
  score_reasons: string[]
  reason_codes: ReasonCode[]
  eligibility: {
    action: GateAction
    reason: string
    rule_version: string
    request_purpose: string
    address_purpose?: string
    tier?: string
    status?: string
  }
  support: EvidenceSummary
  belief_version: number | null
  place_id: string | null
  town_id: string | null
  arms_available: string[]
  arms_considered: CandidateRef[]
  directions: Direction[]
  request_purpose: string
  stage: string
  is_area_context: boolean
  area_context: unknown
}

export interface Direction {
  landmark: string
  landmark_type: string
  distance_m: number
  bearing_deg: number
  cue_text: string
  ambiguous: boolean
  source_ref: string
  parsed_relation: string
  rule_version: string
}

export interface UnplacedResponse extends ResolveResponse {
  candidate: null
  coordinate: null
  uncertainty: null
}

// ── belief ────────────────────────────────────────────────────────────────────────────────────
export interface BeliefVersion {
  address_id: string
  belief_version: number
  as_of: string
  tier: Tier
  status: Status
  candidate_id: string | null
  score: number | null
  candidate: {
    candidate_id: string
    address_id: string
    arm: string
    x: number
    y: number
    granularity: string
    arm_rank: number
    licence_class: string
    as_of_valid: string | null
    source_ref: string
    provenance: {
      rule_version: string
      built_at: string
      built_from: string
      n_observations: number
      spread_m: number | null
      stratum: string
      agreement_arms: number
      primary_eligible: boolean
      memory_evidence_derived?: boolean
    }
  } | null
  radius: Omit<Uncertainty, 'fallback_applied'> & { radius_map_version: string }
  support: EvidenceSummary
  promotion_detail: {
    rule: string
    n_strong: number
    media_distinct: number
    media_ok: boolean
    period_ok: boolean
    space_ok: boolean
    space_spread_m: number | null
  }
  computed_from: {
    observations_upto: string
    policy: string
    rule_version: string
    radius_map_version: string
  }
  place_id: string
}

export interface BeliefPayload extends AsOfMetadata {
  address_id: string
  town_id: string | null
  coordinate_space: string
  belief: BeliefVersion
  uncertainty: Uncertainty
  evidence_summary: EvidenceSummary
  reason_codes: ReasonCode[]
  observation_refs: string[]
  versions: Record<string, string>
}

// ── observations ──────────────────────────────────────────────────────────────────────────────
export interface EvidenceObservation {
  observation_id: string
  visit_id: string | null
  address_id: string
  town_id: string | null
  kind: string
  observed_at: string
  captured_at_device: string | null
  server_received_at: string | null
  local_seq: number | null
  outcome: string
  polarity: Polarity
  coordinate_claim: boolean
  x: number | null
  y: number | null
  captured: { x: number | null; y: number | null; gps_accuracy_m: number | null; note: string | null }
  dwell_s: number | null
  evidence: {
    weight: number
    polarity: Polarity
    evidence_class: string
    reason_codes: string[]
    policy_version: string
  }
  contributes: string
  duplicate_claim_of: string | null
  agent_id: string | null
  device_id: string | null
  remark: string | null
  media: { sha256: string; kind: string }[]
  policy_version: string
}

export interface ObservationsPayload extends AsOfMetadata {
  address_id: string
  town_id: string | null
  coordinate_space: string
  count: number
  negatives_move_coordinate: boolean
  observations: EvidenceObservation[]
}

// ── place history ─────────────────────────────────────────────────────────────────────────────
export interface PlaceVersion {
  address_id: string
  belief_version: number
  as_of: string
  tier: Tier
  status: Status
  candidate_id: string | null
  radius_m: number | null
  rules_version: string
  evidence_policy_version: string
  computed_at: string
}

export interface Contradiction {
  address_id: string
  kind: string
  separation_m: number | null
  threshold_m: number | null
  radius_m: number
  widen_reason: string | null
  negatives_independent: number
  tier: Tier
  status: Status
  belief_version: number
  coordinate_unchanged: boolean
  effect: string
}

export interface PlaceHistory extends AsOfMetadata {
  place_id: string
  state: string
  anchor_address_id: string
  unplaced: boolean
  projection: boolean
  identity_rule: string
  versions_note: string
  merge_review: string
  versions: PlaceVersion[]
  contradictions: string[]
  contradictions_detail: Contradiction[]
  history: { observation_id: string; at: string }[]
  members: Record<string, { tier: string; status: string; belief_version: number; candidate_id: string | null }>
  member_address_ids: string[]
  coordinate: { x: number; y: number; radius_m: number; basis: string; n_calibration: number } | null
}

// ── geometry (local metric plane) ─────────────────────────────────────────────────────────────
export interface PlanePoint {
  id: string
  kind: string // candidate | observation | locality | landmark
  x: number
  y: number
  name?: string | null
  source?: string
  granularity?: string
  status?: string | null
  selected?: boolean
  score?: number | null
  primary_eligible?: boolean
  landmark_type?: string
  pincode?: string | null
  metadata?: Record<string, unknown>
}

export interface PlaneRing {
  center_x: number
  center_y: number
  radius_m: number
  candidate_id: string
  basis: string
  n_calibration: number
  measured_coverage: number | null
  stratum: string | null
  widened: boolean
  widen_reason: string | null
  authoritative: boolean
}

export interface PlaneTrace {
  observation_id: string
  points: { x: number; y: number; at?: string }[]
}

export interface MapPayload {
  address_id: string
  town_id: string
  as_of: string | null
  coordinate_space: string
  units: string
  extent: { x_min: number; x_max: number; y_min: number; y_max: number; basis: string; pad_m: number } | null
  points: PlanePoint[]
  rings: PlaneRing[]
  traces: PlaneTrace[]
  counts: { candidates: number; observations: number; traces: number; rings: number }
  gate: { action: GateAction; reason: string }
  withheld: { reason: string; suppressed: { candidates: number; observations: number; traces: number } } | null
  belief_version: number | null
  place_id: string | null
  renderer_hint: { preferred: string; graticule_m: { minor: number; major: number }; max_objects: number; note: string }
}

export interface TownPlanePayload extends AsOfMetadata {
  town_id: string
  town_name: string
  coordinate_space: string
  units: string
  town_centroid: { x: number; y: number }
  points: PlanePoint[]
  counts: { localities: number; landmarks: number; addresses_indexed: number }
  extent: { x_min: number; x_max: number; y_min: number; y_max: number; basis: string; pad_m: number }
  address_geometry_endpoint: string
  renderer_hint: { preferred: string; graticule_m: { minor: number; major: number }; note: string }
}

// ── tasks ─────────────────────────────────────────────────────────────────────────────────────
export interface TasksPayload {
  as_of: string | null
  count: number
  total_matching: number
  next_cursor: string | null
  filters: { town_id: string | null; cause: string | null; state: string | null; limit: number }
  facets: { by_cause: Record<string, number>; by_state: Record<string, number>; by_town: Record<string, number> }
  items: VerificationTask[]
}

export type CapabilityStatus = 'implemented' | 'designed' | 'not_implemented' | 'evaluated_not_adopted' | 'research_only'

// ── health ────────────────────────────────────────────────────────────────────────────────────
export interface HealthPayload {
  ok: boolean
  versions: Record<string, string>
  rule_version: string
  radius_map_version: string
  store: {
    store_path: string
    store_schema_version: string
    evidence_policy_version: string
    n_observations: number
    counts: Record<string, number>
    attestation: Record<string, { n: number; digest: string }>
  }
  counters: { s_eval_looks: number; gate_decisions: number; evidence_memory_policy_runs?: number }
  gauges: {
    cold_addresses_by_town: Record<string, number>
    open_tasks_by_cause: Record<string, number>
    n_addresses_indexed: number
  }
  indexes: Record<string, string> & { ok?: boolean; mismatched?: string[] }
  packs: {
    town_id: string
    pack_version: string
    valid_days: number
    valid_until: string
    built_for_as_of: string
    age_days_at_cut: number
    n_addresses: number
    n_landmarks: number
    n_localities: number
    contains_truth: boolean
    contains_evidence: boolean
    contains_polygons: boolean
  }[]
  offline: { held_observations: number; receipts: number; ingest_batches: number }
  s_eval_firewall: { reads_by_tools_total: number; tuning_uses: number; note: string }
  capabilities: Record<string, CapabilityStatus>
  capabilities_note: string
  as_of_cut: string
}

export interface EvidenceReceipt {
  observation_id: string
  address_id: string
  accepted: boolean
  replayed?: boolean
  belief_before: { tier: Tier | null; status: Status | null; candidate_id: string | null; radius_m: number | null; belief_version: number | null }
  belief_after: { tier: Tier | null; status: Status | null; candidate_id: string | null; radius_m: number | null; belief_version: number | null }
  changed: { changed: boolean; fields: string[] }
  task_delta: { added: string[]; changed: string[] }
  [k: string]: unknown
}

export interface ApiError {
  error: string
  detail?: string
  path?: string
}

/* ── product surface (contract §27: `GET /v1/overview`, `GET /v1/method-trust`) ──────────────────
 * These mirror the payloads `sutra/product.py` returns. The UI renders them; it never recomputes
 * anything from them.
 */
export interface OverviewPayload {
  as_of: string
  computed_at: string
  addresses: {
    indexed: number
    with_location: number
    confirmed: number
    not_confirmed: number
    unplaceable: number
    needs_review: number
    conflicting: number
    /** addresses with at least one real field observation known at the cut */
    warm: number
    /** addresses never visited */
    cold: number
    warm_share: number | null
    by_tier: Record<string, number>
  }
  workload: {
    active_cases: number
    by_reason: { cause: string; title: string; detail: string | null; count: number }[]
    by_town: { town_id: string; count: number }[]
  }
  field_activity: {
    visits_recorded: number
    visits_last_30_days: number
    latest_visit: string | null
    window_days: number
  }
  data_freshness: {
    evidence_newest: string | null
    packs: {
      town_id: string
      pack_version: string
      updated: string | null
      age_days: number | null
      addresses: number | null
      landmarks: number | null
      localities: number | null
      valid_days: number | null
      valid_until: string | null
      stale: boolean
      downloaded_at: string | null
      downloaded_at_note: string
    }[]
    available_offline: boolean
  }
  towns: { town_id: string; addresses: number; needs_review: number }[]
}

export interface MethodTrustPayload {
  populations: {
    key: string
    name: string
    hit_500m: number
    n: number
    median_m: number
    caption: string
  }[]
  population_note: string
  statuses: { label: string; items: string[] }[]
  how_it_works: { step: number; title: string; detail: string }[]
  safety_rules: string[]
  learning_loop: string[]
  development_note: string
  evaluation_source: string
}
