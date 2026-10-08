/**
 * RESOLVE — the workbench.
 *
 * Three zones: query + ranked candidates · the local metric plane · the decision ticket.
 * Underneath: the visit timeline and a belief replay strip whose steps are real belief reads at real
 * observation instants (the ladder is derived from the address's own observation timestamps, never
 * from a hard-coded script).
 *
 * The frontend renders; it never re-derives tier, radius, gate action, eligibility, priority or the
 * winning reason.
 */
import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { RotateCcw, Search } from 'lucide-react'
import { belief, geometry, observations, place, resolveAddress, resolveById, townPlane } from '../api/endpoints'
import { useApi, useCapturedMeta } from '../api/useApi'
import type { BeliefPayload, EvidenceObservation, MapPayload, ObservationsPayload, PlaceHistory, ResolveResponse, TownPlanePayload } from '../api/types'
import { CandidateList } from '../components/CandidateList'
import { DecisionTicket } from '../components/DecisionTicket'
import { EvidenceTimeline } from '../components/EvidenceTimeline'
import { Plane } from '../components/Plane'
import { Chip, Empty, Figure, Panel, Skeleton, fmtTime } from '../components/ui'
import { ASOF_AFTER_FLIP, ASOF_BEFORE_FLIP, ASOF_COLD, ASOF_MOMENT, PURPOSES, REFERENCE_CASES } from '../config/product'
import { useApp } from '../state/appState'

export function ResolvePage() {
  const { asOf, setAsOf, purpose, setPurpose, apiReachable } = useApp()
  const [params, setParams] = useSearchParams()

  const initialCase = REFERENCE_CASES[0]!
  const [text, setText] = useState(params.get('text') || initialCase.address_text)
  const [town, setTown] = useState(params.get('town') || initialCase.town_hint)
  const [submitted, setSubmitted] = useState<{ text: string; town: string; byId: string | null; asOf: string; purpose: string } | null>(null)

  // A queue row "Open in Resolve" arrives with ?address=… — resolve that address directly.
  useEffect(() => {
    const address = params.get('address')
    if (address) {
      setSubmitted({ text: '', town: params.get('town') || '', byId: address, asOf, purpose })
      setParams((p) => { p.delete('address'); return p }, { replace: true })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const resolveQuery = useApi<ResolveResponse>({
    key: ['resolve', submitted?.byId || submitted?.text || '', submitted?.town || '', submitted?.asOf || '', submitted?.purpose || ''],
    enabled: !!submitted,
    fixtureKey: submitted?.byId ? `resolve_${submitted.byId}` : undefined,
    live: () => (submitted!.byId
      ? resolveById(submitted!.byId, submitted!.town || null, submitted!.asOf, submitted!.purpose)
      : resolveAddress(submitted!.text, submitted!.town || null, submitted!.asOf, submitted!.purpose)),
  })

  const r = resolveQuery.data?.data
  const addressId = r?.address_id || null
  const [selectedCandidate, setSelectedCandidate] = useState<string | null>(null)
  const [selectedObservation, setSelectedObservation] = useState<string | null>(null)
  const [showRefusedPlane, setShowRefusedPlane] = useState(false)

  useEffect(() => { setSelectedCandidate(r?.candidate_id || null); setSelectedObservation(null) }, [r?.candidate_id, r?.as_of])

  const geomQuery = useApi<MapPayload>({
    key: ['geometry', addressId, submitted?.asOf || '', r?.town_id || ''],
    enabled: !!addressId,
    fixtureKey: addressId ? `geometry_${addressId}` : undefined,
    live: () => geometry(addressId!, submitted!.asOf, r?.town_id || null, submitted!.purpose),
  })
  const obsQuery = useApi<ObservationsPayload>({
    key: ['observations', addressId, submitted?.asOf || ''],
    enabled: !!addressId,
    fixtureKey: addressId ? `observations_${addressId}` : undefined,
    live: () => observations(addressId!, submitted!.asOf),
  })
  const beliefQuery = useApi<BeliefPayload>({
    key: ['belief', addressId, submitted?.asOf || ''],
    enabled: !!addressId,
    fixtureKey: addressId ? `belief_${addressId}` : undefined,
    live: () => belief(addressId!, submitted!.asOf),
  })
  const placeQuery = useApi<PlaceHistory>({
    key: ['place', r?.place_id || ''],
    enabled: !!r?.place_id,
    live: () => place(r!.place_id!, submitted!.asOf),
  })
  const backdropQuery = useApi<TownPlanePayload>({
    key: ['plane', r?.town_id || ''],
    enabled: !!r?.town_id,
    fixtureKey: r?.town_id === 'T2' ? 'plane_T2' : undefined,
    live: () => townPlane(r!.town_id!),
  })

  const obs = obsQuery.data?.data
  const geom = geomQuery.data?.data
  const world = beliefQuery.data?.data

  /**
   * The replay ladder: this address's own observation instants, the frozen anchors, and the two
   * boundary instants one second either side of the real flip. Every column is a real belief read;
   * nothing here is scripted.
   */
  const ladder = useMemo(() => {
    const times = (obs?.observations || []).map((o) => o.observed_at)
    const marks = [ASOF_COLD, ...times, ASOF_BEFORE_FLIP, ASOF_AFTER_FLIP, ASOF_MOMENT]
    return Array.from(new Set(marks)).sort()
  }, [obs])

  const ladderQuery = useApi<{ t: string; belief: BeliefPayload }[]>({
    key: ['ladder', addressId, ladder.join('|')],
    enabled: !!addressId && ladder.length > 0,
    live: async () => {
      const reads = await Promise.all(ladder.map(async (t) => ({ t, belief: await belief(addressId!, t) })))
      return reads
    },
  })

  const submit = (e?: React.FormEvent) => {
    e?.preventDefault()
    setSubmitted({ text, town, byId: null, asOf, purpose })
  }
  const runCase = (key: string) => {
    const c = REFERENCE_CASES.find((x) => x.key === key)
    if (!c) return
    setText(c.address_text); setTown(c.town_hint)
    setSubmitted({ text: c.address_text, town: c.town_hint, byId: null, asOf: ASOF_MOMENT, purpose })
    setAsOf(ASOF_MOMENT)
  }

  const fixture = resolveQuery.data?.fixture
  const meta = useCapturedMeta()

  return (
    <div className="grid" style={{ gap: 'var(--s4)' }}>
      <div style={{ display: 'flex', gap: 'var(--s3)', alignItems: 'center', flexWrap: 'wrap' }}>
        <div className="eyebrow">demo cases · real addresses from the official table</div>
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          {REFERENCE_CASES.map((c) => (
            <button key={c.key} className="btn tab demo-tab" data-case={c.key} onClick={() => runCase(c.key)} title={c.blurb}>{c.label}</button>
          ))}
        </div>
        <div style={{ marginLeft: 'auto' }} className="legend">
          <span className="k"><span className="sw cand" /> candidate</span>
          <span className="k"><span className="sw sel" /> selected</span>
          <span className="k"><span className="sw pos" /> positive visit</span>
          <span className="k"><span className="sw amb" /> ambiguous visit</span>
          <span className="k"><span className="sw neg" /> negative visit (captured position, no claim)</span>
          <span className="k"><span className="sw ref" /> official locality / landmark</span>
          <span className="k"><span className="sw ring" /> authoritative radius</span>
        </div>
      </div>

      {fixture && (
        <div className="banner info">
          <div>
            <h4>Captured response — the live service is unreachable from this page</h4>
            <p>{meta?.note} Captured from {meta?.from} on {meta?.on}. This is a demo fixture, not live telemetry.</p>
          </div>
        </div>
      )}

      <div className="workbench">
        {/* ── LEFT: query + candidates ─────────────────────────────────────────────────────── */}
        <div className="col left">
          <Panel title="Query"
            right={<span className="mono" style={{ fontSize: 10, color: apiReachable === false ? 'var(--neg)' : 'var(--pos)' }}>{apiReachable === false ? 'captured' : 'live'}</span>}>
            <form onSubmit={submit} className="grid" style={{ gap: 'var(--s3)' }}>
              <div className="field">
                <label htmlFor="addr">address text</label>
                <textarea id="addr" className="textarea mono" value={text} onChange={(e) => setText(e.target.value)}
                  placeholder="paste the address as it was captured" />
              </div>
              <div className="grid cols-2" style={{ gap: 'var(--s3)' }}>
                <div className="field">
                  <label htmlFor="town">town hint</label>
                  <select id="town" className="select mono" value={town} onChange={(e) => setTown(e.target.value)}>
                    <option value="">any</option><option value="T1">T1</option><option value="T2">T2</option><option value="T3">T3</option>
                  </select>
                </div>
                <div className="field">
                  <label htmlFor="purpose">request purpose</label>
                  <select id="purpose" className="select mono" value={purpose} onChange={(e) => setPurpose(e.target.value)}>
                    {PURPOSES.map((p) => <option key={p} value={p}>{p}</option>)}
                  </select>
                </div>
              </div>
              <div className="field">
                <label htmlFor="asof">as of</label>
                <input id="asof" className="input mono" value={asOf} onChange={(e) => setAsOf(e.target.value)} spellCheck={false} />
                <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap', marginTop: 2 }}>
                  <button type="button" className="btn sm" onClick={() => setAsOf(ASOF_MOMENT)}>moment</button>
                  <button type="button" className="btn sm" onClick={() => setAsOf(ASOF_BEFORE_FLIP)}>1 s before flip</button>
                  <button type="button" className="btn sm" onClick={() => setAsOf(ASOF_AFTER_FLIP)}>1 s after flip</button>
                  <button type="button" className="btn sm" onClick={() => setAsOf(ASOF_COLD)}>cold</button>
                </div>
              </div>
              <div style={{ display: 'flex', gap: 6 }}>
                <button className="btn primary" type="submit" disabled={resolveQuery.isFetching}>
                  <Search size={13} /> {resolveQuery.isFetching ? 'Resolving…' : 'Resolve'}
                </button>
                {submitted && <button type="button" className="btn" onClick={() => { setSubmitted(null); setText(''); }}>
                  <RotateCcw size={12} /> Clear
                </button>}
              </div>
              <div style={{ fontSize: 10.5, color: 'var(--ink-faint)' }}>
                Every request carries an explicit as-of instant and purpose. Both are recorded on the response.
              </div>
            </form>
          </Panel>

          <Panel title="Ranked candidates" right={r && <span className="mono" style={{ fontSize: 10, color: 'var(--ink-faint)' }}>{r.arms_considered?.length ?? 0} considered</span>}>
            {resolveQuery.isLoading && <Skeleton lines={5} />}
            {resolveQuery.isError && <Empty title="resolve failed" hint={String(resolveQuery.error?.message)} />}
            {r && <CandidateList response={r} selected={selectedCandidate} onSelect={setSelectedCandidate} />}
            {r && (
              <div style={{ marginTop: 'var(--s3)', display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                <Chip sm tone="ghost">{r.arms_available?.length ?? 0} arms available</Chip>
                {(r.alternatives || []).length > 0 && <Chip sm tone="warn">{r.alternatives.length} lost</Chip>}
              </div>
            )}
          </Panel>

          {r && r.coordinate && (
            <Panel title="Answer" bodyClass="tight">
              <div style={{ display: 'grid', gap: 6 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8 }}>
                  <span className="eyebrow">tier / status</span>
                  <span className="mono" style={{ fontSize: 11 }}>{r.tier} · {r.status}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8 }}>
                  <span className="eyebrow">radius</span>
                  <span className="mono" style={{ fontSize: 11 }}>{r.radius_m?.toFixed(1)} m {r.widened ? `(widened: ${r.widen_reason})` : ''}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8 }}>
                  <span className="eyebrow">space</span>
                  <span className="mono" style={{ fontSize: 11 }}>{r.coordinate.coordinate_space}</span>
                </div>
                <Link className="btn sm" to={`/evidence?address=${r.address_id}`}>Open evidence</Link>
              </div>
            </Panel>
          )}
        </div>

        {/* ── CENTER: plane ───────────────────────────────────────────────────────────────── */}
        <div className="col">
          {geom && (!r?.coordinate && !showRefusedPlane) ? (
            <div className="banner refuse" style={{ alignItems: 'center' }}>
              <div style={{ display: 'flex', gap: 8, alignItems: 'flex-start' }}>
                <div>
                  <h4>Coordinate withheld · {r?.eligibility.reason}</h4>
                  <p>
                    The service refused this request, so the plane is suppressed as well: no candidate markers, no
                    radius, no visit positions. Showing them would be a usable coordinate by another route.
                  </p>
                </div>
                <button className="btn sm" style={{ marginLeft: 'auto' }} onClick={() => setShowRefusedPlane(true)}>
                  Inspect suppressed payload
                </button>
              </div>
            </div>
          ) : geom ? (
            <>
              <Plane geometry={geom} backdrop={backdropQuery.data?.data || null}
                selectedCandidateId={selectedCandidate} onSelectCandidate={setSelectedCandidate}
                onSelectObservation={setSelectedObservation} />
              <div style={{ display: 'flex', gap: 'var(--s4)', flexWrap: 'wrap', marginTop: 6, fontSize: 10.5, color: 'var(--ink-faint)' }}>
                <span>{geom.counts.candidates} candidates · {geom.counts.observations} visit markers · {geom.counts.rings} ring{geom.counts.rings === 1 ? '' : 's'} · {geom.counts.traces} traces</span>
                <span>extent x {geom.extent?.x_min?.toFixed(0)}…{geom.extent?.x_max?.toFixed(0)} m · y {geom.extent?.y_min?.toFixed(0)}…{geom.extent?.y_max?.toFixed(0)} m</span>
              </div>
            </>
          ) : (
            <Panel title="Local metric plane"><Skeleton lines={8} /></Panel>
          )}

          {r && ladder.length > 0 && (
            <Panel title="Belief replay · real belief reads at this address's own visit instants"
              right={<span className="mono" style={{ fontSize: 10, color: ladderQuery.isFetching && ladderQuery.data ? 'var(--survey)' : 'var(--ink-faint)' }}>
              {ladderQuery.isFetching && ladderQuery.data ? 'reading…' : `${ladder.length} instants`}
            </span>}>
              {!ladderQuery.data ? <Skeleton lines={2} /> : (
                <div className="replay">
                  {(ladderQuery.data?.data || []).map((step) => {
                    const b = step.belief.belief
                    const active = step.t === asOf
                    const flip = step.t === ASOF_BEFORE_FLIP || step.t === ASOF_AFTER_FLIP
                    return (
                      <button key={step.t} className="replay-step" aria-pressed={active}
                        onClick={() => { setAsOf(step.t); setSubmitted({ text, town, byId: null, asOf: step.t, purpose }) }}>
                        <span className="t">{step.t.slice(0, 19).replace('T', ' ')}{flip ? ' ◆' : ''}</span>
                        <span className="v">{b.radius.radius_m.toFixed(0)}<span style={{ fontSize: 10, color: 'var(--ink-faint)' }}> m</span></span>
                        <span className="s">{b.tier} · {b.status}</span>
                        <span className="s mono">{b.candidate ? `${b.candidate.x.toFixed(0)}, ${b.candidate.y.toFixed(0)}` : 'no coordinate'}</span>
                      </button>
                    )
                  })}
                </div>
              )}
              <div style={{ marginTop: 8, fontSize: 10.5, color: 'var(--ink-faint)' }}>
                Each column is one real <span className="mono">GET /v1/belief/&lt;address&gt;?as_of=…</span> response. Clicking a column re-resolves at that instant.
                Watch the coordinate stay fixed while the radius and the status move.
              </div>
            </Panel>
          )}

          <Panel title="Visit timeline" right={obs && <span className="mono" style={{ fontSize: 10, color: 'var(--ink-faint)' }}>{obs.count} observations · negatives move the coordinate: {String(obs.negatives_move_coordinate)}</span>}>
            {obsQuery.isLoading && <Skeleton lines={4} />}
            {obs && <EvidenceTimeline observations={obs.observations} selectedId={selectedObservation}
              onFocus={(o: EvidenceObservation) => setSelectedObservation(o.observation_id)} />}
          </Panel>
        </div>

        {/* ── RIGHT: ticket ────────────────────────────────────────────────────────────────── */}
        <div className="col right">
          {resolveQuery.isLoading && <Panel title="Decision ticket"><Skeleton lines={10} /></Panel>}
          {!submitted && (
            <Panel title="Decision ticket">
              <Empty title="no case open" hint="Resolve an address, or pick one of the demo cases. The ticket shows exactly what the service returned — answer, tier, radius, reasons, task." />
            </Panel>
          )}
          {r && <DecisionTicket r={r} />}

          {world && (
            <Panel title="Belief read · GET /v1/belief/{address}" bodyClass="tight">
              <div className="grid" style={{ gap: 8 }}>
                <div className="figure-row">
                  <Figure value={`v${world.belief.belief_version}`} caption="belief version" note={`computed from observations up to ${fmtTime(world.belief.computed_from.observations_upto)}`} />
                  <Figure value={world.belief.radius.radius_m.toFixed(0)} caption="radius (m)" note={`${world.belief.radius.basis} · n=${world.belief.radius.n_calibration}`} tone={world.belief.radius.widened ? 'warn' : 'serve'} />
                  <Figure value={world.belief.support.independent_confirmations} caption="confirmations" note={`${world.belief.support.n_observations} visits`} />
                </div>
                <dl className="kv">
                  <dt>candidate</dt><dd className="mono">{world.belief.candidate?.candidate_id || '—'}</dd>
                  <dt>arm</dt><dd className="mono">{world.belief.candidate?.arm || '—'} · {world.belief.candidate?.granularity || '—'}</dd>
                  <dt>memory derived</dt><dd className="mono">{String(world.belief.candidate?.provenance.memory_evidence_derived ?? 'n/a')}</dd>
                  <dt>promotion</dt>
                  <dd className="mono">{world.belief.promotion_detail.rule} · strong {world.belief.promotion_detail.n_strong} · media {world.belief.promotion_detail.media_ok ? 'ok' : 'no'} · period {world.belief.promotion_detail.period_ok ? 'ok' : 'no'} · space {world.belief.promotion_detail.space_ok ? 'ok' : 'no'}</dd>
                </dl>
              </div>
            </Panel>
          )}

          {placeQuery.data && (
            <Panel title="Place" right={<Link className="btn sm" to={`/places?place=${placeQuery.data.data.place_id}`}>Open</Link>} bodyClass="tight">
              <div style={{ display: 'grid', gap: 6 }}>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                  <span className="mono" style={{ fontSize: 11.5 }}>{placeQuery.data.data.place_id}</span>
                  <Chip sm mono tone={placeQuery.data.data.state === 'MOVED_SUSPECTED' ? 'warn' : 'pos'}>{placeQuery.data.data.state}</Chip>
                  <span className="mono" style={{ fontSize: 10.5, color: 'var(--ink-faint)' }}>{placeQuery.data.data.versions.length} stored version{placeQuery.data.data.versions.length === 1 ? '' : 's'}</span>
                </div>
                {placeQuery.data.data.contradictions_detail.map((c) => (
                  <div key={c.address_id} style={{ fontSize: 11, color: 'var(--ink-soft)' }}>
                    contradiction · <span className="mono">{c.kind}</span> · {c.effect} · coordinate unchanged: <span className="mono">{String(c.coordinate_unchanged)}</span>
                  </div>
                ))}
              </div>
            </Panel>
          )}
        </div>
      </div>
    </div>
  )
}
