/**
 * Product configuration — the things the app is allowed to know before it talks to the service.
 *
 * This file exists so that production code never imports the fixture module. What lives here is not
 * data: it is the demo *clock* (real timestamps of real moments in the frozen runtime), the real
 * request-purpose vocabulary, and the two saved example addresses the brief names. Everything else
 * — coordinates, tiers, radii, scores, tasks, evidence — comes from the service.
 *
 * `FIXTURES_ENABLED` is the single gate. It is true in development, and can be forced on for an
 * explicitly offline demo with `VITE_DEV_FIXTURES=true`. In a production build it is false, and the
 * captured-response fallback is dead code that the bundler drops.
 */

/** Development builds, or an explicit offline demo build. Never true in production. */
export const FIXTURES_ENABLED: boolean =
  import.meta.env.DEV || import.meta.env.VITE_DEV_FIXTURES === 'true'

/* ── the demo clock: instants that exist in the frozen runtime, not invented dates ───────────── */
export const ASOF_MOMENT = '2026-06-01T00:00:00Z'
export const ASOF_BEFORE_FLIP = '2026-05-20T05:53:45Z'
export const ASOF_AFTER_FLIP = '2026-05-20T05:53:46Z'
export const ASOF_COLD = '2026-04-05T00:00:00Z'

/** The real request-purpose vocabulary (`sutra/purpose.py`). */
export const PURPOSES = [
  'FIELD_NAVIGATION', 'VISIT_PLANNING', 'NOTICE_SERVICE', 'PORTFOLIO_REVIEW', 'AUDIT', 'DEMO',
] as const

export interface ReferenceCase {
  /** the address id — the stable key the workbench tabs and the smoke test address */
  key: string
  address_id: string
  address_text: string
  town_hint: string
  /** the button label the workbench shows */
  label: string
  story: 'serve' | 'verify' | 'refuse'
  blurb: string
}

/**
 * The two saved examples from the official table, plus the refusal case. These are entry points, not
 * answers: clicking one submits the real address to the real service.
 */
export const REFERENCE_CASES: ReferenceCase[] = [
  {
    key: 'AD003067',
    address_id: 'AD003067',
    address_text: 'H.NO. 221, GALI 12, NR COMMUNITY HALL, PATEL NAGAR, DEVGARH NGR',
    town_hint: 'T2',
    label: 'AD003067 · stable field evidence',
    story: 'serve',
    blurb: 'Field evidence confirms the household — served with a narrow radius.',
  },
  {
    key: 'AD002936',
    address_id: 'AD002936',
    address_text: 'Gali no-11, Azad Mohalla, Devgarh Nagar - 970203',
    town_hint: 'T2',
    label: 'AD002936 · contradictory evidence',
    story: 'verify',
    blurb: 'Contradicting visits widened the circle without moving the place, and raised a verification task.',
  },
  {
    key: 'AD000002',
    address_id: 'AD000002',
    address_text: 'no. 173 12th cross 3rd main shanthi nagar kaveripura - 960101',
    town_hint: 'T1',
    label: 'AD000002 · work-like place',
    story: 'refuse',
    blurb: 'A real address the purpose rules refuse to serve as a home location.',
  },
]
