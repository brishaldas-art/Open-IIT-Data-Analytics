/**
 * EVIDENCE — address-centric by necessity: the service exposes observations per address, so this
 * screen never fabricates a global feed. The claim/non-claim distinction is the headline here.
 */
import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { AlertTriangle, Info } from 'lucide-react'
import { belief, observations } from '../api/endpoints'
import { useApi } from '../api/useApi'
import type { BeliefPayload, EvidenceObservation, ObservationsPayload } from '../api/types'
import { EvidenceTimeline } from '../components/EvidenceTimeline'
import { Chip, Empty, Figure, Panel, Skeleton, fmtTime } from '../components/ui'
import { REFERENCE_CASES } from '../config/product'
import { useApp } from '../state/appState'

export function EvidencePage() {
  const { asOf } = useApp()
  const [params] = useSearchParams()
  const [address, setAddress] = useState(params.get('address') || 'AD002936')
  const [submitted, setSubmitted] = useState(params.get('address') || 'AD002936')
  const [focus, setFocus] = useState<string | null>(null)
  useEffect(() => { const a = params.get('address'); if (a) { setAddress(a); setSubmitted(a) } }, [params])

  const obsQ = useApi<ObservationsPayload>({
    key: ['evidence-obs', submitted, asOf],
    fixtureKey: `observations_${submitted}`,
    live: () => observations(submitted, asOf),
  })
  const beliefQ = useApi<BeliefPayload>({
    key: ['evidence-belief', submitted, asOf],
    fixtureKey: `belief_${submitted}`,
    live: () => belief(submitted, asOf),
  })
  const obs = obsQ.data?.data
  const b = beliefQ.data?.data
  const focused: EvidenceObservation | undefined = obs?.observations.find((o) => o.observation_id === focus)

  const negatives = obs?.observations.filter((o) => o.polarity === 'negative') ?? []
  const positives = obs?.observations.filter((o) => o.polarity === 'positive') ?? []
  const ambiguous = obs?.observations.filter((o) => o.polarity === 'ambiguous') ?? []

  return (
    <div className="grid" style={{ gap: 'var(--s4)' }}>
      <Panel title="Address under inspection">
        <form style={{ display: 'flex', gap: 'var(--s3)', flexWrap: 'wrap', alignItems: 'flex-end' }}
          onSubmit={(e) => { e.preventDefault(); setSubmitted(address.trim().toUpperCase()) }}>
          <div className="field" style={{ minWidth: 220 }}>
            <label htmlFor="addr">address id</label>
            <input id="addr" className="input mono" value={address} onChange={(e) => setAddress(e.target.value)} spellCheck={false} />
          </div>
          <button className="btn primary" type="submit">Load evidence</button>
          <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap' }}>
            {REFERENCE_CASES.map((c) => <button key={c.key} type="button" className="btn sm" onClick={() => { setAddress(c.address_id); setSubmitted(c.address_id) }}>{c.address_id}</button>)}
          </div>
          <div style={{ marginLeft: 'auto', display: 'flex', gap: 6, alignItems: 'center', fontSize: 11, color: 'var(--ink-faint)' }}>
            as of <span className="mono">{fmtTime(asOf)}</span>
            {b?.belief && <Link className="btn sm" to={`/resolve?address=${submitted}`}>Open in Resolve</Link>}
          </div>
        </form>
      </Panel>

      <div className="banner info" data-testid="non-claim-banner">
        <Info className="icon" size={15} color="var(--info)" />
        <div>
          <h4>Captured position ≠ location claim</h4>
          <p>
            A negative observation (for example <span className="mono">address_not_traceable</span>) records where the
            collector stood. It carries zero evidence weight towards a location and it can never move the coordinate —
            the service reports it with <span className="mono">coordinate_claim: false</span>, a <span className="mono">null</span>
            {' '}claim position and <span className="mono">contributes: negative_doubt</span>. It widens and caps; it never relocates.
          </p>
        </div>
      </div>

      <div className="grid cols-4">
        <Panel title="Visits" bodyClass="tight">
          {!obs ? <Skeleton lines={2} /> : <Figure value={obs.count} caption="observations at this instant" note={`${positives.length} positive · ${ambiguous.length} ambiguous · ${negatives.length} negative`} />}
        </Panel>
        <Panel title="Positive weight" bodyClass="tight">
          {!b ? <Skeleton lines={2} /> : <Figure value={b.evidence_summary.positive_weight_sum.toFixed(4)} caption="sum of positive weight" note={`${b.evidence_summary.independent_confirmations} independent confirmations`} tone="serve" />}
        </Panel>
        <Panel title="Independent negatives" bodyClass="tight">
          {!b ? <Skeleton lines={2} /> : <Figure value={b.evidence_summary.negatives_independent} caption="negatives, independent" tone={b.evidence_summary.negatives_independent ? 'warn' : undefined} note={`duplicate claims ${b.evidence_summary.duplicate_claims}`} />}
        </Panel>
        <Panel title="Effect on the answer" bodyClass="tight">
          {!b ? <Skeleton lines={2} /> : (
            <div style={{ display: 'grid', gap: 4, fontSize: 11.5 }}>
              <div>coordinate moves: <span className="mono">{String(b.evidence_summary.negatives_move_coordinate)}</span></div>
              <div>radius widened: <span className="mono">{String(b.evidence_summary.radius_widened)}</span>{b.evidence_summary.widen_reason ? ` · ${b.evidence_summary.widen_reason}` : ''}</div>
              <div>tier / status: <span className="mono">{b.belief.tier} · {b.belief.status}</span></div>
            </div>
          )}
        </Panel>
      </div>

      <div className="grid" style={{ gridTemplateColumns: focused ? 'minmax(0,1.55fr) minmax(0,1fr)' : 'minmax(0,1fr)', gap: 'var(--s4)' }}>
        <Panel title="Observation timeline"
          right={obs && <span className="mono" style={{ fontSize: 10, color: 'var(--ink-faint)' }}>{obs.observations[0] ? 'oldest → newest' : ''}</span>}>
          {obsQ.isLoading && <Skeleton lines={6} />}
          {obsQ.isError && <Empty title="could not load" hint={String(obsQ.error?.message)} />}
          {obs && <EvidenceTimeline observations={obs.observations} onFocus={(o) => setFocus(o.observation_id)} selectedId={focus} />}
        </Panel>

        {focused && (
          <Panel title={`Observation ${focused.observation_id}`} right={<button className="btn sm" onClick={() => setFocus(null)}>close</button>}>
            <div style={{ display: 'grid', gap: 12 }}>
              <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                <Chip tone={focused.polarity === 'negative' ? 'neg' : focused.polarity === 'positive' ? 'pos' : 'warn'} mono>{focused.polarity}</Chip>
                <Chip mono>{focused.evidence.evidence_class}</Chip>
                <Chip mono tone="ghost">weight {focused.evidence.weight.toFixed(4)}</Chip>
                {focused.coordinate_claim === false && <Chip tone="neg">not a location claim</Chip>}
              </div>

              {!focused.coordinate_claim && (
                <div className="banner refuse" style={{ padding: 'var(--s3)' }}>
                  <AlertTriangle className="icon" size={14} color="var(--neg)" />
                  <div style={{ fontSize: 11.5 }}>
                    This record can never move the coordinate. It contributes doubt only, and it is reported with no
                    claim position.
                  </div>
                </div>
              )}

              <dl className="kv">
                <dt>outcome</dt><dd className="mono">{focused.outcome}</dd>
                <dt>observed at</dt><dd className="mono">{fmtTime(focused.observed_at)}</dd>
                <dt>captured on device</dt><dd className="mono">{focused.captured_at_device || '—'}</dd>
                <dt>visit</dt><dd className="mono">{focused.visit_id || '—'}</dd>
                <dt>agent</dt><dd className="mono">{focused.agent_id || '—'} <span style={{ color: 'var(--ink-faint)' }}>(pseudonymous collector id)</span></dd>
                <dt>device</dt><dd className="mono">{focused.device_id || '—'}</dd>
                <dt>dwell</dt><dd className="mono">{focused.dwell_s !== null ? `${Math.round(focused.dwell_s)} s` : '—'}</dd>
                <dt>captured position</dt><dd className="mono">{focused.captured.x !== null ? `${focused.captured.x.toFixed(1)}, ${focused.captured.y?.toFixed(1)} m` : 'none'}{focused.captured.gps_accuracy_m !== null ? ` · ±${focused.captured.gps_accuracy_m} m GPS` : ''}</dd>
                <dt>location claim</dt><dd className="mono">{focused.coordinate_claim ? `${focused.x?.toFixed(1)}, ${focused.y?.toFixed(1)} m` : 'none — non-claim'}</dd>
                <dt>contributes</dt><dd className="mono">{focused.contributes.replace(/_/g, ' ')}</dd>
                <dt>policy</dt><dd className="mono">{focused.policy_version}</dd>
                <dt>device note</dt><dd>{focused.remark ? `“${focused.remark}”` : '—'}</dd>
                <dt>media</dt><dd className="mono">{focused.media.length ? focused.media.map((m) => `${m.kind}:${m.sha256.slice(0, 10)}…`).join(', ') : 'none'}</dd>
                {focused.duplicate_claim_of && <><dt>duplicate of</dt><dd className="mono">{focused.duplicate_claim_of}</dd></>}
              </dl>

              <div>
                <div className="eyebrow" style={{ marginBottom: 6 }}>reason codes · issued by the evidence policy</div>
                <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap' }}>
                  {focused.evidence.reason_codes.map((c) => <Chip key={c} sm mono>{c}</Chip>)}
                </div>
              </div>
            </div>
          </Panel>
        )}
      </div>

      {b && (
        <Panel title="Belief after these observations" right={<Link className="btn sm" to={`/places?place=${b.belief.place_id}`}>Place {b.belief.place_id}</Link>}>
          <div className="grid cols-3">
            <Figure value={b.belief.radius.radius_m.toFixed(1)} caption="radius (m)" note={`${b.belief.radius.basis} · n=${b.belief.radius.n_calibration} · stratum ${b.belief.radius.source_stratum}`} tone={b.belief.radius.widened ? 'warn' : 'serve'} />
            <Figure value={`${b.belief.tier}`} caption="tier" note={`status ${b.belief.status}`} />
            <Figure value={b.belief.candidate ? `${b.belief.candidate.x.toFixed(1)}, ${b.belief.candidate.y.toFixed(1)}` : '—'} caption="coordinate (m)" note={`${b.belief.candidate?.arm || 'none'} · ${b.coordinate_space}`} />
          </div>
          <div style={{ marginTop: 10, fontSize: 10.5, color: 'var(--ink-faint)' }}>
            Negatives move the coordinate: <span className="mono">{String(b.evidence_summary.negatives_move_coordinate)}</span>. Widened: <span className="mono">{String(b.belief.radius.widened)}</span>{b.belief.radius.widen_reason ? ` (${b.belief.radius.widen_reason})` : ''}.
          </div>
        </Panel>
      )}
    </div>
  )
}
