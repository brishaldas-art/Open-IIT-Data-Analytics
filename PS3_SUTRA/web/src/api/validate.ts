/**
 * Runtime shape guards for the contract layer.
 *
 * `types.ts` is compile-time only; these guards fail loudly if the service ever returns a payload
 * the frontend does not understand, rather than rendering `undefined` into the UI.
 */
import type { BeliefPayload, EvidenceObservation, MapPayload, ResolveResponse, TasksPayload } from './types'

function missing(obj: unknown, keys: string[], label: string): string[] {
  if (!obj || typeof obj !== 'object') return [`${label}: not an object`]
  const o = obj as Record<string, unknown>
  return keys.filter((k) => !(k in o)).map((k) => `${label}.${k}`)
}

export function checkResolve(r: unknown): string[] {
  return missing(r, ['coordinate', 'uncertainty', 'alternatives', 'decision_ticket', 'eligibility',
    'as_of', 'computed_at', 'versions', 'resolution'], 'resolve')
}

export function checkBelief(r: unknown): string[] {
  const errs = missing(r, ['belief', 'uncertainty', 'evidence_summary', 'versions', 'coordinate_space'], 'belief')
  if (errs.length) return errs
  return missing((r as BeliefPayload).belief, ['belief_version', 'tier', 'status', 'radius', 'support'], 'belief.belief')
}

export function checkObservations(r: unknown): string[] {
  const errs = missing(r, ['address_id', 'observations', 'count'], 'observations')
  if (errs.length) return errs
  const list = (r as { observations: unknown }).observations
  if (!Array.isArray(list)) return ['observations.observations: not an array']
  return list.length ? missing(list[0] as EvidenceObservation, ['observation_id', 'observed_at', 'polarity', 'evidence'], 'observations[0]') : []
}

export function checkGeometry(r: unknown): string[] {
  return missing(r, ['coordinate_space', 'points', 'rings', 'counts', 'gate'], 'geometry')
}

export function checkTasks(r: unknown): string[] {
  const errs = missing(r, ['items', 'facets', 'count', 'total_matching'], 'tasks')
  if (errs.length) return errs
  const { facets } = r as TasksPayload
  if (!facets || typeof facets.by_cause !== 'object') errs.push('tasks.facets.by_cause')
  return errs
}

export function assertClean<T>(payload: T, errs: string[], label: string): T {
  if (errs.length) {
    // eslint-disable-next-line no-console
    console.error(`[sutra] contract mismatch in ${label}:`, errs)
  }
  return payload
}

export type { MapPayload, ResolveResponse }
