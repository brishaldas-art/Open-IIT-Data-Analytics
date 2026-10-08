/** Every call the app makes, one place, typed. No endpoint here is invented. */
import { get, patch, post } from './client'
import { assertClean, checkBelief, checkGeometry, checkObservations, checkResolve, checkTasks } from './validate'
import type {
  BeliefPayload, EvidenceObservation, EvidenceReceipt, HealthPayload, MapPayload,
  MethodTrustPayload, ObservationsPayload, OverviewPayload, PlaceHistory, ResolveResponse,
  TasksPayload, TownPlanePayload, VerificationTask,
} from './types'

export const frozenCut = '2026-06-01T00:00:00Z'

export function resolveAddress(address_text: string, town_hint: string | null, as_of: string | null, request_purpose: string) {
  return post<ResolveResponse>('/resolve', { address_text, town_hint, as_of, request_purpose })
    .then((r) => assertClean(r, checkResolve(r), '/resolve'))
}

export function resolveById(address_id: string, town_hint: string | null, as_of: string | null, request_purpose: string) {
  return post<ResolveResponse>('/resolve', { address_id, town_hint, as_of, request_purpose })
    .then((r) => assertClean(r, checkResolve(r), '/resolve'))
}

export const health = () => get<HealthPayload>('/v1/health')
/** GET /v1/overview — operational aggregates, as of a cut. Product surface, no counters. */
export const overview = (as_of?: string | null) =>
  get<OverviewPayload>(`/v1/overview?as_of=${encodeURIComponent(as_of || frozenCut)}`)
/** GET /v1/method-trust — the mechanism, the safety rules and the three frozen populations. */
export const methodTrust = () => get<MethodTrustPayload>('/v1/method-trust')
export const belief = (address_id: string, as_of: string | null) =>
  get<BeliefPayload>(`/v1/belief/${encodeURIComponent(address_id)}?as_of=${encodeURIComponent(as_of || frozenCut)}`)
    .then((r) => assertClean(r, checkBelief(r), '/v1/belief'))
export const observations = (address_id: string, as_of: string | null) =>
  get<ObservationsPayload>(`/v1/address/${encodeURIComponent(address_id)}/observations?as_of=${encodeURIComponent(as_of || frozenCut)}`)
    .then((r) => assertClean(r, checkObservations(r), '/v1/address/observations'))
export const geometry = (address_id: string, as_of: string | null, town_id?: string | null, request_purpose = 'FIELD_NAVIGATION') => {
  const p = new URLSearchParams({ as_of: as_of || frozenCut, request_purpose })
  if (town_id) p.set('town_id', town_id)
  return get<MapPayload>(`/v1/geometry/${encodeURIComponent(address_id)}?${p}`)
    .then((r) => assertClean(r, checkGeometry(r), '/v1/geometry'))
}
export const place = (place_id: string, as_of: string | null) =>
  get<PlaceHistory>(`/v1/place/${encodeURIComponent(place_id)}?as_of=${encodeURIComponent(as_of || frozenCut)}`)
export const townPlane = (town_id: string) => get<TownPlanePayload>(`/v1/plane/${encodeURIComponent(town_id)}`)
export const tasks = (q: { town_id?: string; cause?: string; state?: string; as_of?: string; limit?: number; cursor?: string | null }) => {
  const p = new URLSearchParams()
  Object.entries(q).forEach(([k, v]) => { if (v !== undefined && v !== null && v !== '') p.set(k, String(v)) })
  return get<TasksPayload>(`/v1/tasks?${p}`).then((r) => assertClean(r, checkTasks(r), '/v1/tasks'))
}
export const submitEvidence = (body: unknown) => post<EvidenceReceipt>('/evidence', body)

/* ── the human workflow (contract §12/§341 rows 8, 9) ─────────────────────────────────────────
 * Every one of these is an append on the server: a transition adds a task event, an adjudication
 * adds an observation and lets the frozen engine recompute the belief. Nothing is computed here.
 */
export interface TaskDetail {
  task: VerificationTask & { state: string }
  history: { at: string; state: string; state_label: string; actor: string | null; note: string | null
             reason: string | null; event_id: string }[]
  adjudications: { at: string; decision: string; actor: string | null; note: string | null
                   belief_unchanged: boolean
                   decided_against: { tier: string | null; status: string | null; radius_m: number | null }
                   event_id: string }[]
  allowed_transitions: string[]
  state_label: string
}

export interface AdjudicationResult {
  observation_id: string
  address_id: string
  decision: string
  outcome: string
  belief_version: number | null
  tier: string | null
  status: string | null
  effect: { changed: boolean; coordinate_moved: boolean
            fields: Record<string, { before: unknown; after: unknown }>
            belief_before: { tier?: string; status?: string; radius_m?: number } | null
            belief_after: { tier?: string; status?: string; radius_m?: number } | null }
  mapping: { decision: string; outcome: string; outcome_class: string; basis: string }
  task: { task_id: string | null; closed: boolean; state: string | null; state_label?: string }
  replayed: boolean
  never_enters_s_eval: boolean
  note_text: string
}

export const taskDetail = (task_id: string) =>
  get<TaskDetail>(`/v1/tasks/${encodeURIComponent(task_id)}`)

/** PATCH /v1/tasks/{id} — append-only lifecycle. Deterministic idempotency key, never random. */
export const transitionTask = (task_id: string, body: { state: string; actor?: string | null
                                                        note?: string | null; at?: string | null
                                                        idempotency_key: string }) =>
  patch<{ task_id: string; from: string; to: string; at: string; state_label: string
          event_id: string; replayed: boolean }>(`/v1/tasks/${encodeURIComponent(task_id)}`, body)

/** POST /v1/adjudicate — the only human ground-truth write. */
export const adjudicate = (body: { address_id?: string; task_id?: string; decision: string
                                   actor: string; note?: string | null; as_of?: string | null
                                   idempotency_key: string }) =>
  post<AdjudicationResult>('/v1/adjudicate', body)
export const explain = (address_text: string, town_hint: string | null, request_purpose: string) =>
  post<{ explain: string; response: ResolveResponse }>('/explain', { address_text, town_hint, request_purpose })

export type { EvidenceObservation }
