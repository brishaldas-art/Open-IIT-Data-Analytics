/* ------------------------------------------------------------------ *
 * SUTRA domain model.
 * All geometry lives on a LOCAL METRIC PLANE (metres, easting/northing
 * from a declared survey origin). No latitude/longitude anywhere.
 * ------------------------------------------------------------------ */

export interface LocalPoint {
  x: number; // metres, east of origin
  y: number; // metres, north of origin
}

export interface PlaneRef {
  originId: string; // survey anchor, e.g. SEAL-01
  epoch: string;
}

/* ---------------- scene (base cartography) ---------------- */

export type RoadKind = "arterial" | "street" | "lane" | "track" | "stream" | "rail";

export interface RoadFeature {
  id: string;
  kind: RoadKind;
  name?: string;
  path: LocalPoint[];
  widthM: number;
}

export type LandmarkKind = "temple" | "school" | "tank" | "stand" | "well" | "clinic" | "bridge";

export interface Landmark {
  id: string;
  kind: LandmarkKind;
  label: string;
  at: LocalPoint;
}

export interface Scene {
  roads: RoadFeature[];
  landmarks: Landmark[];
}

/* ---------------- resolver ---------------- */

export type CandidateSource =
  | "Gazette Registry"
  | "Municipal Parcel DB"
  | "Postal PIN Directory"
  | "Field Memory";

export interface ScoreParts {
  text: number; // token similarity 0..1
  component: number; // structured component match 0..1
  source: number; // source reliability 0..1
  evidence: number; // field-evidence prior 0..1 (0 = none)
  memory: number; // place-memory prior 0..1 (0 = none)
  freshness: number; // decay factor 0..1
}

export interface Candidate {
  id: string;
  at: LocalPoint;
  sigmaM: number; // standard error of the point, metres
  canonical: string;
  source: CandidateSource;
  sourceRef: string;
  score: number;
  parts: ScoreParts;
  distFromAnchorM: number;
  evidenceSupport: number; // number of visits supporting
  conflict?: string;
}

export type TrailOutcome = "confirm" | "refute" | "relocate" | "search";

export interface Trail {
  id: string;
  label: string;
  meta: string;
  outcome: TrailOutcome;
  points: LocalPoint[];
}

export interface ParsedToken {
  t: string;
  k: "business" | "unit" | "house-no" | "street" | "landmark" | "locality" | "pin" | "noise";
}

export interface PipelineStage {
  stage: string;
  ms: number;
  note: string;
}

export interface MemoryPrior {
  placeId: string;
  at: LocalPoint;
  sigmaM: number;
  lastVerifiedDays: number;
}

export type DecisionCode =
  | "AUTO-CONFIRM"
  | "HUMAN-COMMIT"
  | "VERIFY_FIRST"
  | "CONTESTED"
  | "UNPLACEABLE";

export interface Scenario {
  id: string;
  raw: string;
  context: string; // short description of why it is interesting
  parsed: ParsedToken[];
  anchor: LocalPoint; // coarse locality anchor from parsing
  anchorSigmaM: number;
  memory: MemoryPrior | null;
  candidates: Candidate[];
  trails: Trail[];
  pipeline: PipelineStage[];
  gateNote: string;
}

/* ---------------- places (memory) ---------------- */

export type PlaceState = "STABLE" | "PROVISIONAL" | "CONTESTED" | "STALE" | "RETIRED";

export interface Place {
  id: string;
  label: string;
  address: string;
  at: LocalPoint;
  sigmaM: number;
  confidence: number;
  state: PlaceState;
  visits: number;
  lastVerified: string;
  lastVerifiedDays: number;
  sources: string[];
  driftM: number; // median offset of recent visits vs stored point
  contradictions: string[];
  note: string;
}

/* ---------------- field evidence ---------------- */

export type VisitOutcome = "CONFIRMED" | "NOT_FOUND" | "MOVED" | "REFUTED" | "PARTIAL";

export interface FieldVisit {
  id: string;
  ts: string;
  day: string;
  placeId: string;
  placeLabel: string;
  officer: string;
  device: string;
  outcome: VisitOutcome;
  point: LocalPoint;
  offsetM: number; // offset vs stored memory point at time of visit
  fix: { cepM: number; hdop: number; sats: number };
  photos: number;
  dwellS: number;
  motion: "STATIONARY" | "WALKING";
  integrity: { mock: boolean; timeSkewS: number; trailSigmaM: number };
  quality: number; // 0..1 composite
  note: string;
}

/* ---------------- verification queue ---------------- */

export type CaseKind =
  | "VERIFY_FIRST"
  | "REVERIFICATION"
  | "CONTESTED"
  | "MOVED_SUSPECTED"
  | "UNPLACEABLE";

export type Priority = "P1" | "P2" | "P3";

export interface VerifyCase {
  id: string;
  kind: CaseKind;
  placeLabel: string;
  placeId?: string;
  rawAddress: string;
  priority: Priority;
  ageDays: number;
  slaHoursLeft: number;
  slaHoursTotal: number;
  reasonCodes: string[];
  score?: number;
  margin?: number;
  at?: LocalPoint;
  sigmaM?: number;
  recommendation: string;
  assignee?: string;
}

/* ---------------- overview / system ---------------- */

export type ServiceStatus = "OK" | "DEGRADED" | "DOWN";

export interface ServiceHealth {
  name: string;
  role: string;
  p50ms: number;
  errPct: number;
  queueDepth: number;
  status: ServiceStatus;
}

export interface DayStat {
  day: string;
  resolutions: number;
  warmAcc: number; // agreement with final outcome, evidence prior present
  coldAcc: number; // agreement, first-seen locality
}

export interface SystemOverview {
  kpis: {
    resolutionsToday: number;
    resolutionsDeltaPct: number;
    autoDecidedPct: number;
    medianResolveMs: number;
    openCases: number;
    p1Cases: number;
  };
  warmCold: { warm: number; cold: number; warmN: number; coldN: number };
  series: DayStat[];
  services: ServiceHealth[];
}

/* ---------------- audit ---------------- */

export interface AuditEvent {
  seq: number;
  ts: string;
  actor: string;
  action: string;
  detail: string;
  hash: string;
}
