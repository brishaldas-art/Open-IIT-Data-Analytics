/* ------------------------------------------------------------------ *
 * SUTRA domain model — the shapes the service actually sends.
 *
 * All geometry lives on a LOCAL METRIC PLANE (metres, easting/northing
 * from a declared survey origin). No latitude/longitude anywhere, and
 * nothing in this file is computed in the browser: the backend decides,
 * the workbench renders.
 * ------------------------------------------------------------------ */

export interface LocalPoint {
  x: number; // metres, east of origin
  y: number; // metres, north of origin
}

/** `sutra_local_metric_plane:<town>` — the only coordinate space that exists. */
export type CoordinateSpace = string;

/* ---------------- resolver ---------------- */

/** The frozen candidate arms. Names come from the service, never from the UI. */
export type ArmName =
  | "field_evidence"
  | "frozen_baseline"
  | "locality_centroid"
  | "town_centroid"
  | "memory"
  | "official_landmark"
  | (string & {});

export type Granularity = "rooftop" | "street" | "locality" | "town" | (string & {});

/** Typed reason code — the frontend never parses the `code` string. */
export interface ReasonCode {
  code: string;
  kind: "score_term" | "support" | "penalty" | "rule" | (string & {});
  subject: string | null;
  effect: number | null;
  direction: "positive" | "negative" | "neutral";
  label: string;
}

export interface CandidateProvenance {
  rule_version?: string;
  built_at?: string | null;
  built_from?: string | null;
  n_observations?: number | null;
  spread_m?: number | null;
  observation_ids?: string[];
  stratum?: string | null;
  primary_eligible?: boolean | null;
  agreement_arms?: number | null;
  agreement_list?: string[] | null;
  prior_candidate_arm?: string | null;
  memory_evidence_derived?: boolean | null;
  baseline_precision?: string | null;
  [k: string]: unknown;
}

export interface Candidate {
  candidate_id: string;
  address_id?: string;
  arm: ArmName;
  source_ref: string | null;
  x: number | null;
  y: number | null;
  granularity: Granularity | null;
  arm_rank: number | null;
  licence_class: string | null;
  as_of_valid: string | null;
  provenance: CandidateProvenance | null;
}

export interface ArmConsidered {
  candidate_id: string;
  arm: ArmName;
  score: number;
  primary_eligible: boolean;
  reasons: string[];
  rank?: number;
  granularity?: Granularity | null;
}

export interface Alternative {
  candidate_id: string;
  arm: ArmName;
  score: number;
  rank: number;
  granularity: Granularity | null;
  primary_eligible: boolean;
  reasons: string[];
}

export type Tier = "CONFIRMED" | "PROBABLE" | "APPROXIMATE" | (string & {});
export type BeliefStatus = "STABLE" | "MOVED_SUSPECTED" | "CONTESTED" | (string & {});

export interface Uncertainty {
  radius_m: number | null;
  basis: string | null;
  nominal: number | null;
  measured_coverage: number | null;
  n_calibration: number | null;
  source_stratum: string | null;
  fallback_applied: boolean | null;
  widened: boolean | null;
  widen_reason: string | null;
  radius_map_version: string | null;
}

export type GateAction = "SERVE" | "VERIFY_FIRST" | "REFUSE" | (string & {});

export interface Eligibility {
  action: GateAction;
  reason: string | null;
  rule_version: string;
  request_purpose: string | null;
  address_purpose: string | null;
  tier: Tier | null;
  status: BeliefStatus | null;
}

export interface EvidenceSummary {
  n_observations: number;
  n_positives: number;
  negatives_independent: number;
  independent_confirmations: number;
  duplicate_claims: number;
  positive_weight_sum: number | null;
  negatives_move_coordinate: boolean;
  radius_widenened?: unknown;
  radius_widened: boolean;
  widen_reason: string | null;
}

export interface NextAction {
  kind: string;
  label: string;
  clears_when: string | null;
}

export interface VerificationTask {
  task_id: string;
  address_label?: string | null;
  kind: string;
  cause: string;
  state: string;
  state_label?: string;
  priority: number | null;
  town_id: string | null;
  address_id: string;
  place_id: string | null;
  tier: Tier | null;
  status: BeliefStatus | null;
  negatives_independent: number | null;
  radius_m: number | null;
  rule_version: string | null;
  at: string | null;
  recommended_action: NextAction | null;
  evidence_refs: string[];
  evidence_refs_basis: string | null;
}

export interface DecisionAnswer {
  candidate_id: string;
  arm: ArmName;
  granularity: Granularity | null;
  score: number;
  tier: Tier | null;
  status: BeliefStatus | null;
}

export interface DecisionTicket {
  headline: string;
  case_id: string;
  town_id: string | null;
  gate: { action: GateAction; reason: string | null; rule_version: string; request_purpose: string | null };
  answer: DecisionAnswer | null;
  why: ReasonCode[];
  score_terms: ReasonCode[];
  provenance: Record<string, unknown> | null;
  margin: { top_alternative_candidate_id: string | null; score_margin: number | null } | null;
  confidence: { tier: Tier | null; status: BeliefStatus | null; measured_coverage: number | null; n_calibration: number | null } | null;
  belief_version: number | null;
  place_id: string | null;
  next_action: NextAction | null;
  task: string | null;
  refusal: { kind: string; coordinate_withheld?: boolean; reason_codes?: string[]; note?: string | null } | null;
}

export interface AddressPurpose {
  class: string;
  confidence: string;
  basis: string[];
  model_version: string;
}

export interface ResolveResponse {
  /** Present when the resolver answered with a coordinate; null on refusal. */
  candidate: Candidate | null;
  candidate_id: string | null;
  score: number | null;
  score_reasons: string[];
  granularity: Granularity | null;
  tier: Tier | null;
  status: BeliefStatus | null;
  radius_m: number | null;
  radius_basis: string | null;
  nominal: number | null;
  measured_coverage: number | null;
  n_calibration: number | null;
  source_stratum: string | null;
  widened: boolean | null;
  widen_reason: string | null;
  reasons: string[];
  request_purpose: string;
  address_id: string | null;
  address_purpose: AddressPurpose | null;
  directions: Record<string, unknown> | null;
  is_area_context: boolean;
  area_context: Record<string, unknown> | null;
  eligibility: Eligibility;
  stage: string | null;
  arms_available: ArmName[];
  arms_considered: ArmConsidered[];
  support: EvidenceSummary | null;
  place_id: string | null;
  belief_version: number | null;
  resolution: string | null;
  versions: Record<string, string>;
  town_id: string | null;
  as_of: string;
  coordinate: { x: number; y: number; granularity: Granularity | null; coordinate_space: CoordinateSpace; radius_m: number | null } | null;
  uncertainty: Uncertainty | null;
  alternatives: Alternative[];
  reason_codes: ReasonCode[];
  decision_ticket: DecisionTicket;
  evidence_summary: EvidenceSummary | null;
  task: VerificationTask | null;
  computed_at: string;
  /** Refusal path: no coordinate is returned or rendered. */
  refusal?: { reason: string; note?: string; withheld?: string[] } | null;
  resolved_text?: string | null;
  town_hint?: string | null;
}

/* ---------------- local plane geometry ---------------- */

export interface PlanePoint {
  id: string;
  kind: "candidate" | "observation" | "landmark" | "locality" | "anchor" | (string & {});
  x: number;
  y: number;
  /** candidates */
  source?: ArmName;
  granularity?: Granularity;
  status?: BeliefStatus;
  selected?: boolean;
  score?: number;
  primary_eligible?: boolean;
  /** landmarks / localities */
  name?: string;
  pincode?: string | null;
  landmark_type?: string | null;
  /** observations */
  observation_id?: string;
  outcome?: string;
  polarity?: string;
  observed_at?: string;
  metadata?: Record<string, unknown>;
}

export interface PlaneRing {
  center_x: number;
  center_y: number;
  radius_m: number;
  candidate_id?: string;
  basis: string | null;
  n_calibration: number | null;
  measured_coverage: number | null;
  stratum: string | null;
  widened: boolean | null;
  widen_reason: string | null;
}

export interface PlaneTrace {
  observation_id?: string;
  points?: LocalPoint[];
  outcome?: string;
  label?: string;
  [k: string]: unknown;
}

export interface PlaneExtent {
  x_min: number;
  x_max: number;
  y_min: number;
  y_max: number;
  basis: string;
  pad_m: number;
}

export interface AddressGeometry {
  address_id: string;
  town_id: string | null;
  as_of: string;
  coordinate_space: CoordinateSpace;
  units: string;
  extent: PlaneExtent | null;
  points: PlanePoint[];
  rings: PlaneRing[];
  traces: PlaneTrace[];
  counts: { candidates: number; observations: number; traces: number; rings: number };
  gate: { action: GateAction; reason: string | null };
  /** Set when the answer is withheld (refusal): the plane renders no coordinate. */
  withheld: {
    reason: string;
    gate_action?: GateAction;
    gate_reason?: string;
    suppressed?: { candidate_points?: number; observation_points?: number; rings?: number };
    note?: string;
  } | null;
  belief_version: number | null;
  place_id: string | null;
  renderer_hint: { preferred: string; max_objects: number; note: string };
}

export interface TownPlane {
  town_id: string;
  town_name: string | null;
  as_of: string | null;
  coordinate_space: CoordinateSpace;
  units: string;
  town_centroid: LocalPoint | null;
  points: PlanePoint[];
  counts: { localities: number; landmarks: number; addresses_indexed: number };
  extent: PlaneExtent;
  address_geometry_endpoint: string;
  renderer_hint: { preferred: string; graticule_m: { minor: number; major: number }; note: string };
}

/* ---------------- places (memory) ---------------- */

export type PlaceState = "CONFIRMED" | "WARM" | "COLD" | "MOVED_SUSPECTED" | "CONTESTED";

export interface PlaceRow {
  place_id: string;
  address_id: string;
  town_id: string | null;
  label: string;
  account_id: string | null;
  address_type: string | null;
  source: string | null;
  added_date: string | null;
  state: PlaceState;
  tier: Tier | null;
  status: BeliefStatus | null;
  belief_version: number | null;
  coordinate_space: CoordinateSpace;
  coordinate: { x: number; y: number; granularity: Granularity | null; radius_m: number | null; basis: string | null } | null;
  uncertainty: Uncertainty | null;
  contradictions: string[];
  visits: number;
  positives: number;
  last_evidence_at: string | null;
  last_positive_at: string | null;
  evidence_newest_kind: string | null;
  has_belief: boolean;
}

export interface PlacesResponse {
  as_of: string;
  query: string | null;
  filters: { state: string | null; tier: string | null; town_id: string | null; limit: number };
  count: number;
  total_matching: number;
  items: PlaceRow[];
  facets: { by_state: Record<string, number>; by_tier: Record<string, number>; by_town: Record<string, number> };
  next_cursor: string | null;
  states: PlaceState[];
  identity_rule: string;
  projection: boolean;
  note: string;
}

export interface PlaceContradiction {
  address_id: string;
  kind: string;
  separation_m: number | null;
  threshold_m: number | null;
  radius_m: number | null;
  widen_reason: string | null;
  negatives_independent: number | null;
  tier: Tier | null;
  status: BeliefStatus | null;
  belief_version: number | null;
}

export interface PlaceVersion {
  address_id: string;
  belief_version: number;
  as_of: string;
  tier: Tier | null;
  status: BeliefStatus | null;
  candidate_id: string | null;
  radius_m: number | null;
  rules_version: string | null;
  evidence_policy_version: string | null;
  computed_at: string | null;
}

export interface PlaceDetail {
  place_id: string;
  as_of: string;
  member_address_ids: string[];
  identity_rule: string;
  state: PlaceState;
  coordinate: { x: number; y: number; radius_m: number | null; basis: string | null; n_calibration: number | null } | null;
  anchor_address_id: string | null;
  members: Record<string, { tier: Tier; status: BeliefStatus; belief_version: number; candidate_id: string | null }>;
  contradictions: string[];
  history: { observation_id: string; at: string }[];
  merge_review: string | null;
  projection: boolean;
  versions: PlaceVersion[];
  contradictions_detail: PlaceContradiction[];
  unplaced: boolean;
  versions_note: string;
}

/* ---------------- field evidence ---------------- */

export interface VisitRow {
  observation_id: string;
  visit_id: string | null;
  address_id: string;
  address_label: string | null;
  place_id: string | null;
  town_id: string | null;
  kind: string;
  observed_at: string;
  captured_at_device: string | null;
  server_received_at: string | null;
  local_seq: number | null;
  outcome: string;
  polarity: "positive" | "negative" | "ambiguous" | (string & {});
  coordinate_claim: boolean;
  x: number | null;
  y: number | null;
  captured: { x: number | null; y: number | null; gps_accuracy_m: number | null; note: string | null };
  dwell_s: number | null;
  evidence: {
    weight: number | null;
    polarity: string;
    evidence_class: string | null;
    reason_codes: string[];
    policy_version: string | null;
  };
  contributes: "positive_support" | "negative_doubt" | "no_weight" | (string & {});
  duplicate_claim_of: string | null;
  agent_id: string | null;
  device_id: string | null;
  remark: string | null;
  media: { sha256: string; kind: string }[];
  policy_version: string | null;
}

export interface EvidenceResponse {
  as_of: string;
  query: string | null;
  filters: { outcome: string | null; polarity: string | null; town_id: string | null; limit: number };
  count: number;
  total_matching: number;
  items: VisitRow[];
  facets: {
    by_outcome: Record<string, number>;
    by_polarity: Record<string, number>;
    by_town: Record<string, number>;
    by_evidence_class: Record<string, number>;
  };
  next_cursor: string | null;
  negatives_move_coordinate: boolean;
  note: string;
}

/* ---------------- case (belief + place + task + timeline) ---------------- */

export interface BeliefPayload {
  address_id: string;
  as_of: string;
  belief_version: number;
  computed_from: Record<string, string>;
  place_id: string | null;
  candidate_id: string | null;
  candidate: Candidate | null;
  tier: Tier | null;
  status: BeliefStatus | null;
  radius: Uncertainty | null;
  support: EvidenceSummary | null;
  score: number | null;
  score_reasons: string[];
  arms_available: ArmName[];
  arms_considered: ArmConsidered[];
  promotion_detail: Record<string, unknown> | null;
  reasons: string[];
}

export interface CaseEvent {
  at: string;
  kind: string;
  address_id: string;
  title: string;
  detail: string;
  quality: string | null;
  effect: string | null;
  details: Record<string, unknown> | null;
}

export interface CasePayload {
  address_id: string;
  town_id: string | null;
  as_of: string;
  coordinate_space: CoordinateSpace;
  belief: {
    address_id: string;
    town_id: string | null;
    as_of: string;
    coordinate_space: CoordinateSpace;
    belief: BeliefPayload;
    observation_refs: { observation_id: string; visit_id: string | null; observed_at: string; polarity: string; weight: number | null }[];
    uncertainty: Uncertainty;
    evidence_summary: EvidenceSummary;
    reason_codes: ReasonCode[];
    versions: Record<string, string>;
  };
  place: PlaceDetail;
  task: VerificationTask | null;
  task_history: { at: string; state: string; state_label: string; actor: string | null; note: string | null; reason: string; event_id: string }[];
  evidence: {
    address_id: string;
    town_id: string | null;
    as_of: string;
    coordinate_space: CoordinateSpace;
    count: number;
    observations: VisitRow[];
    negatives_move_coordinate: boolean;
  };
  history: { scope: Record<string, string | null>; as_of: string; count: number; total: number; events: CaseEvent[] };
  decision: {
    coordinate: { x: number; y: number; granularity: Granularity | null; coordinate_space: CoordinateSpace; radius_m: number | null } | null;
    uncertainty: Uncertainty | null;
    alternatives: Alternative[];
    reason_codes: ReasonCode[];
    decision_ticket: DecisionTicket;
    evidence_summary: EvidenceSummary | null;
    task: VerificationTask | null;
    as_of: string;
    computed_at: string;
  };
}

/* ---------------- overview / workload ---------------- */

export interface OverviewResponse {
  as_of: string;
  computed_at: string;
  addresses: {
    indexed: number;
    with_location: number;
    confirmed: number;
    not_confirmed: number;
    unplaceable: number;
    needs_review: number;
    conflicting: number;
    warm: number;
    cold: number;
    warm_share: number;
    by_tier: Record<string, number>;
  };
  workload: {
    active_cases: number;
    by_reason: { cause: string; title: string; detail: string; count: number }[];
    by_town: { town_id: string; count: number }[];
  };
  field_activity: {
    visits_recorded: number;
    visits_last_30_days: number;
    latest_visit: string | null;
    window_days: number;
  };
  data_freshness: {
    evidence_newest: string | null;
    packs: { town_id: string; pack_version: string; updated: string; age_days: number; valid_until: string; stale: boolean; addresses: number; landmarks: number; localities: number; valid_days: number }[];
    available_offline: boolean;
  };
  towns: { town_id: string; addresses: number; needs_review: number }[];
}

export interface HealthResponse {
  ok: boolean;
  versions: Record<string, string>;
  rule_version: string;
  radius_map_version: string;
  store: Record<string, number>;
  packs: { town_id?: string; pack_version?: string; age_days?: number; stale?: boolean; addresses?: number; updated?: string; valid_until?: string }[];
  gauges: Record<string, number>;
  indexes: Record<string, number>;
  counters: Record<string, unknown>;
  offline: Record<string, unknown>;
  s_eval_firewall: Record<string, unknown>;
  capabilities: Record<string, string>;
  capabilities_note: string;
  as_of_cut: string;
}

/* ---------------- method & trust ---------------- */

export interface MethodTrust {
  populations: { key: string; name: string; hit_500m: number | null; n: number; median_m: number | null; caption: string }[];
  population_note: string;
  how_it_works: { step: number; title: string; detail: string }[];
  safety_rules: string[];
  learning_loop: string[];
  statuses: { label: string; items: string[] }[];
  development_note: string;
  evaluation_source: string;
}

/* ---------------- audit ---------------- */

export interface AuditResponse {
  belief_id: string;
  address_id: string;
  steps: number;
  uncertainty: {
    radius_m: number | null;
    basis: string | null;
    measured_coverage: number | null;
    n_calibration: number | null;
    previous_radius_m: number | null;
    widened: boolean | null;
  } | null;
  evidence: {
    at: string; observation_id: string; kind: string | null; outcome: string; agent_id: string | null;
    weight: number | null; polarity: string | null; evidence_class: string | null;
    reason_codes: string[]; independence: unknown;
  }[];
  tasks: { at: string; task_id: string; state: string; reason: string | null; decision: string | null; actor: string | null; note: string | null }[];
  note: string;
  belief: {
    belief_version: number;
    as_of: string;
    tier: Tier | null;
    status: BeliefStatus | null;
    candidate_id: string | null;
    radius_m: number | null;
    rules_version: string;
    evidence_policy_version: string;
    radius_map_version: string;
    payload_sha256: string;
  };
  winner: { arm: ArmName; candidate_id: string; score: number | null; granularity?: Granularity | null; licence_class?: string | null } | null;
  alternatives_lost: { candidate_id: string; arm: ArmName; rank?: number; score?: number; reasons: string[] }[];
}

/* ---------------- adjudication / task lifecycle ---------------- */

export type AdjudicationDecision = "confirmed" | "not_true" | "inconclusive";

export interface AdjudicationResponse {
  observation_id: string;
  address_id: string;
  decision: AdjudicationDecision;
  outcome: string;
  belief_version: number | null;
  tier: Tier | null;
  status: BeliefStatus | null;
  effect: {
    changed: boolean;
    fields: Record<string, { before?: unknown; after?: unknown } | unknown>;
    coordinate_moved: boolean;
    belief_before: Record<string, unknown> | null;
    belief_after: Record<string, unknown> | null;
  };
  mapping: { decision: string; outcome: string; outcome_class: string; basis: string };
  task: { task_id: string | null; closed: boolean; state: string | null };
  replayed: boolean;
  never_enters_s_eval: boolean;
  note_text: string;
  received_at: string | null;
}

export interface TaskTransition {
  task_id: string;
  from: string;
  to: string;
  at: string;
  state_label: string;
  event_id: string;
  replayed: boolean;
}

export interface TaskDetail {
  task: VerificationTask;
  history: { at: string; state: string; state_label: string; actor: string | null; note: string | null; reason: string; event_id: string }[];
  adjudications: Record<string, unknown>[];
  allowed_transitions: string[];
  state_label: string;
}

export interface TasksResponse {
  as_of: string;
  filters: { town_id: string | null; cause: string | null; state: string | null; limit: number };
  count: number;
  total_matching: number;
  items: VerificationTask[];
  facets: { by_cause: Record<string, number>; by_state: Record<string, number>; by_town: Record<string, number> };
  next_cursor: string | null;
}
