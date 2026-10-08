/**
 * Demo material — every value here is a real project fact, and nothing else is allowed in.
 *
 * · Addresses and their address text: copied from the official `addresses` table.
 * · Captured responses: byte-for-byte replies from the running service (2026-10-08), used only if
 *   the API is unreachable, and always labelled as captured in the UI.
 * · Evaluation figures: the frozen evaluation only (three separated populations). The single
 *   report that produced them is `PS3_IMPLEMENTATION_PHASE_REPORT_2026-10-07.md`.
 *
 * No invented coordinates, task ids, agent names, counts or scores.
 */
import captured from './captured.json'

export const CAPTURED = captured

export interface DemoCase {
  key: string
  address_id: string
  address_text: string
  town_hint: string
  label: string
  blurb: string
  story: 'serve' | 'verify' | 'refuse'
}

export const CASES: DemoCase[] = [
  {
    key: 'AD003067',
    address_id: 'AD003067',
    address_text: 'H.NO. 221, GALI 12, NR COMMUNITY HALL, PATEL NAGAR, DEVGARH NGR',
    town_hint: 'T2',
    label: 'AD003067 · stable field evidence',
    blurb: 'Four real visits, three independent confirmations, cross-arm agreement. This is what good looks like.',
    story: 'serve',
  },
  {
    key: 'AD002936',
    address_id: 'AD002936',
    address_text: 'Gali no-11, Azad Mohalla, Devgarh Nagar - 970203',
    town_hint: 'T2',
    label: 'AD002936 · contradictory evidence',
    blurb: 'Two independent address-not-traceable reports. The coordinate never moved; the radius did.',
    story: 'verify',
  },
  {
    key: 'AD000002',
    address_id: 'AD000002',
    address_text: 'no. 173 12th cross 3rd main shanthi nagar kaveripura - 960101',
    town_hint: 'T1',
    label: 'AD000002 · work-like place',
    blurb: 'A cold, office-type address. The gate refuses to serve a home-visit answer for it.',
    story: 'refuse',
  },
]

export const PURPOSES = ['FIELD_NAVIGATION', 'VISIT_PLANNING', 'NOTICE_SERVICE', 'PORTFOLIO_REVIEW', 'AUDIT', 'DEMO'] as const

/** as-of anchors. Both are the project's own frozen instants, not arbitrary dates. */
export const ASOF_MOMENT = '2026-06-01T00:00:00Z'
export const ASOF_BEFORE_FLIP = '2026-05-20T05:53:45Z'
export const ASOF_AFTER_FLIP = '2026-05-20T05:53:46Z'
export const ASOF_COLD = '2026-04-05T00:00:00Z'

/**
 * The frozen evaluation, as published. Three populations that must never be merged or recombined:
 * the cold independent lane, the warm independent subset that answered, and the product lane.
 */
export const FROZEN_EVALUATION = {
  note: 'Frozen evaluation — not live telemetry. These three populations are separate by construction and must never be merged into one number.',
  source: 'PS3_IMPLEMENTATION_PHASE_REPORT_2026-10-07.md',
  populations: [
    { key: 'cold', name: 'Cold S-Eval (independent)', hit_500: 0.71, n: 100, median_m: 375.8,
      caption: '100 surveyed addresses, no field evidence available at the query instant. The honest cold-start floor.' },
    { key: 'warm', name: 'Warm S-Eval (independent subset)', hit_500: 0.9677, n: 31, median_m: 12.4,
      caption: 'The 31 addresses of the independent set that answered under the frozen policy. Not 96.77 % of 100 — of 31.' },
    { key: 'product', name: 'Product lane', hit_500: 0.76, n: null, median_m: 202.2,
      caption: 'Field navigation with the warm lane active where evidence exists, falling back where it does not.' },
  ],
} as const
