/**
 * PLACES — the durable object behind the address: state, stored belief versions, contradictions.
 * History is what the store actually holds (`versions_note` says so); nothing is reconstructed here.
 */
import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { ArrowUpRight, GitBranch } from 'lucide-react'
import { belief, observations, place } from '../api/endpoints'
import { useApi } from '../api/useApi'
import type { BeliefPayload, ObservationsPayload, PlaceHistory } from '../api/types'
import { EvidenceTimeline } from '../components/EvidenceTimeline'
import { Chip, Empty, Figure, KV, Panel, Skeleton, TierPill, fmtTime } from '../components/ui'
import { useApp } from '../state/appState'

const KNOWN = ['PL-AD002936', 'PL-AD003067', 'PL-AD000002']

export function PlacesPage() {
  const { asOf, setAsOf } = useApp()
  const [params] = useSearchParams()
  const [input, setInput] = useState(params.get('place') || 'PL-AD002936')
  const [submitted, setSubmitted] = useState(params.get('place') || 'PL-AD002936')
  useEffect(() => { const p = params.get('place'); if (p) { setInput(p); setSubmitted(p) } }, [params])

  const placeQ = useApi<PlaceHistory>({
    key: ['place-page', submitted, asOf],
    live: () => place(submitted, asOf),
    fixtureKey: submitted === 'PL-AD002936' ? 'place_AD002936' : undefined,
  })
  const p = placeQ.data?.data
  const anchor = p?.anchor_address_id || null

  const beliefQ = useApi<BeliefPayload>({
    key: ['place-belief', anchor, asOf], enabled: !!anchor,
    fixtureKey: anchor ? `belief_${anchor}` : undefined,
    live: () => belief(anchor!, asOf),
  })
  const obsQ = useApi<ObservationsPayload>({
    key: ['place-obs', anchor, asOf], enabled: !!anchor,
    fixtureKey: anchor ? `observations_${anchor}` : undefined,
    live: () => observations(anchor!, asOf),
  })

  const b = beliefQ.data?.data
  const obs = obsQ.data?.data

  return (
    <div className="grid" style={{ gap: 'var(--s4)' }}>
      <div className="grid cols-3">
        <Panel title="Place lookup" className="col-span">
          <form className="grid" style={{ gap: 'var(--s3)' }} onSubmit={(e) => { e.preventDefault(); setSubmitted(input.trim()) }}>
            <div className="field">
              <label htmlFor="place">place id or address id</label>
              <input id="place" className="input mono" value={input} onChange={(e) => setInput(e.target.value)} spellCheck={false} />
            </div>
            <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap' }}>
              {KNOWN.map((k) => <button key={k} type="button" className="btn sm" onClick={() => { setInput(k); setSubmitted(k) }}>{k}</button>)}
            </div>
            <button className="btn primary" type="submit">Open place</button>
            <div style={{ fontSize: 10.5, color: 'var(--ink-faint)' }}>
              A place is keyed by colocation, never by account: <span className="mono">{p?.identity_rule || 'colocation<=30m|adjudicated'}</span>
            </div>
          </form>
        </Panel>

        <Panel title="Current state" bodyClass="tight">
          {placeQ.isLoading && <Skeleton lines={4} />}
          {placeQ.isError && <Empty title="not found" hint={String(placeQ.error?.message)} />}
          {p && (
            <div style={{ display: 'grid', gap: 10 }}>
              <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
                <span className="headline" style={{ fontSize: 18, margin: 0 }}>{p.state}</span>
                <Chip mono>{p.place_id}</Chip>
                {p.unplaced && <Chip tone="neg">unplaced</Chip>}
                {p.projection && <Chip tone="info" title="Served from the belief projection">projection</Chip>}
              </div>
              {p.coordinate && (
                <div className="figure-row">
                  <Figure value={`${p.coordinate.x.toFixed(1)}`} caption="x (m)" note={`${p.coordinate.basis} · n=${p.coordinate.n_calibration}`} />
                  <Figure value={`${p.coordinate.y.toFixed(1)}`} caption="y (m)" />
                  <Figure value={p.coordinate.radius_m.toFixed(0)} caption="radius (m)" tone={p.state === 'MOVED_SUSPECTED' ? 'warn' : 'serve'} />
                </div>
              )}
              <KV items={[
                ['anchor address', <span className="mono">{p.anchor_address_id}</span>],
                ['members', <span className="mono">{p.member_address_ids.length}</span>],
                ['merge review', <span className="mono">{p.merge_review}</span>],
                ['as of', <span className="mono">{fmtTime(p.as_of)}</span>],
              ]} />
              <div style={{ display: 'flex', gap: 6 }}>
                <Link className="btn sm" to={`/resolve?address=${anchor}`}>Open in Resolve</Link>
                <Link className="btn sm" to={`/evidence?address=${anchor}`}>Evidence</Link>
              </div>
            </div>
          )}
        </Panel>

        <Panel title="Contradictions" right={<GitBranch size={13} color="var(--ink-faint)" />} bodyClass="tight">
          {placeQ.isLoading && <Skeleton lines={3} />}
          {p && (p.contradictions_detail.length === 0
            ? <Empty title="no contradiction" hint="No stored contradiction for this place at the selected as-of instant." />
            : (
              <div style={{ display: 'grid', gap: 10 }}>
                {p.contradictions_detail.map((c) => (
                  <div key={c.address_id} style={{ display: 'grid', gap: 4 }}>
                    <div style={{ display: 'flex', gap: 6, alignItems: 'center', flexWrap: 'wrap' }}>
                      <Chip sm mono tone="warn">{c.kind}</Chip>
                      <Chip sm mono>{c.belief_version !== null ? `belief v${c.belief_version}` : '—'}</Chip>
                      <span className="mono" style={{ fontSize: 10.5, color: 'var(--ink-faint)' }}>{c.address_id}</span>
                    </div>
                    <div style={{ fontSize: 11.5, color: 'var(--ink-soft)' }}>{c.effect}</div>
                    <dl className="kv" style={{ gridTemplateColumns: 'minmax(120px, auto) minmax(0,1fr)' }}>
                      <dt>radius</dt><dd className="mono">{c.radius_m} m {c.widen_reason ? `· ${c.widen_reason}` : ''}</dd>
                      <dt>independent negatives</dt><dd className="mono">{c.negatives_independent}</dd>
                      <dt>separation / threshold</dt><dd className="mono">{c.separation_m ?? '—'} / {c.threshold_m ?? '—'} m</dd>
                      <dt>coordinate unchanged</dt><dd className="mono">{String(c.coordinate_unchanged)}</dd>
                    </dl>
                  </div>
                ))}
              </div>
            ))}
        </Panel>
      </div>

      <div className="grid cols-2">
        <Panel title="Stored belief versions" right={<span className="eyebrow">{p?.versions_note}</span>}>
          {placeQ.isLoading && <Skeleton lines={4} />}
          {p && (
            <table className="table">
              <thead>
                <tr><th className="num">v</th><th>as of</th><th>tier</th><th>status</th><th className="num">radius (m)</th><th>candidate</th><th>computed</th><th /></tr>
              </thead>
              <tbody>
                {[...p.versions].reverse().map((v) => (
                  <tr key={v.belief_version} onClick={() => setAsOf(v.as_of)} title="set this version's instant as the as-of">
                    <td className="num mono">{v.belief_version}</td>
                    <td className="mono">{fmtTime(v.as_of)}</td>
                    <td>{v.tier}</td>
                    <td>{v.status}</td>
                    <td className="num mono">{v.radius_m?.toFixed(1) ?? '—'}</td>
                    <td className="mono" style={{ fontSize: 10.5 }}>{v.candidate_id || '—'}</td>
                    <td className="mono" style={{ fontSize: 10.5 }}>{fmtTime(v.computed_at)}</td>
                    <td><ArrowUpRight size={12} color="var(--ink-faint)" /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Panel>

        <div className="col" style={{ gap: 'var(--s4)' }}>
          <Panel title="Current answer" bodyClass="tight">
            {beliefQ.isLoading && <Skeleton lines={3} />}
            {b && (
              <div style={{ display: 'grid', gap: 8 }}>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
                  <TierPill tier={b.belief.tier} status={b.belief.status} />
                  <Chip sm mono>{b.belief.radius.basis} · n={b.belief.radius.n_calibration}</Chip>
                  {b.belief.radius.widened && <Chip sm tone="warn">widened · {b.belief.radius.widen_reason}</Chip>}
                </div>
                <dl className="kv">
                  <dt>coordinate</dt>
                  <dd className="mono">{b.belief.candidate ? `${b.belief.candidate.x.toFixed(1)}, ${b.belief.candidate.y.toFixed(1)} m` : 'none'}</dd>
                  <dt>space</dt><dd className="mono">{b.coordinate_space}</dd>
                  <dt>arm</dt><dd className="mono">{b.belief.candidate?.arm || '—'}</dd>
                  <dt>memory</dt><dd className="mono">{String(b.belief.candidate?.provenance.memory_evidence_derived ?? 'n/a')}</dd>
                </dl>
              </div>
            )}
          </Panel>
          <Panel title="Visit history" right={obs && <span className="mono" style={{ fontSize: 10, color: 'var(--ink-faint)' }}>{obs.count} visits</span>}>
            {obsQ.isLoading ? <Skeleton lines={3} /> : obs ? <EvidenceTimeline observations={obs.observations} compact /> : null}
          </Panel>
        </div>
      </div>
    </div>
  )
}
