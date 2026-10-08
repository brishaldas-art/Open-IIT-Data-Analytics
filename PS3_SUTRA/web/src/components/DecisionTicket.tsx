/** The decision ticket: the authoritative answer, rendered as received. */
import { AlertTriangle, ArrowRight, Ban, CheckCircle2, MapPin, ShieldAlert } from 'lucide-react'
import { Link } from 'react-router-dom'
import type { ResolveResponse } from '../api/types'
import { Chip, Figure, GatePill, KV, Num, TierPill, WhyList, fmtTime } from './ui'

export function DecisionTicket({ r }: { r: ResolveResponse }) {
  const gate = r.eligibility.action
  const ticket = r.decision_ticket
  const refused = r.coordinate === null

  const Banner = () => {
    if (gate === 'REFUSE') return (
      <div className="banner refuse">
        <Ban className="icon" size={16} color="var(--neg)" />
        <div>
          <h4>Not served · {r.eligibility.reason}</h4>
          <p>No usable coordinate is exposed for this request. The gate refused under the {r.eligibility.rule_version} rule for request purpose {r.eligibility.request_purpose}.{r.address_purpose?.class ? ` The place reads as ${r.address_purpose.class.replace('_', '-').toLowerCase()}.` : ''}</p>
        </div>
      </div>
    )
    if (gate === 'VERIFY_FIRST') return (
      <div className="banner verify">
        <AlertTriangle className="icon" size={16} color="var(--warn)" />
        <div>
          <h4>Verify first · {r.eligibility.reason}</h4>
          <p>The coordinate below is the best known location, not a confirmed one. The gate keeps the verification action authoritative until a fresh independent visit clears it.</p>
        </div>
      </div>
    )
    return (
      <div className="banner serve">
        <CheckCircle2 className="icon" size={16} color="var(--pos)" />
        <div>
          <h4>{ticket?.headline || 'Serve this location'}</h4>
          <p>Served under {r.eligibility.rule_version} for {r.eligibility.request_purpose}. {r.widened ? `Radius widened: ${r.widen_reason}.` : 'Radius is the calibrated value for this stratum.'}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="panel">
      <header className="panel-head">
        <h3>Decision ticket</h3>
        <div className="right"><GatePill action={gate} reason={r.eligibility.reason} /></div>
      </header>
      <div className="panel-body" style={{ display: 'grid', gap: 'var(--s4)' }}>
        <Banner />

        <div className="answer-line">
          <span className="headline" style={{ margin: 0 }}>{ticket?.case_id || r.address_id || '—'}</span>
          <TierPill tier={r.tier} status={r.status} />
          {r.town_id && <Chip mono>{r.town_id}</Chip>}
        </div>

        <div className="figure-row">
          <Figure
            value={refused ? <span style={{ color: 'var(--ink-faint)' }}>withheld</span> : <><Num v={r.radius_m} digits={1} /><span style={{ fontSize: 12, color: 'var(--ink-faint)' }}> m</span></>}
            caption="radius" tone={refused ? undefined : r.widened ? 'warn' : 'serve'}
            note={refused ? 'no coordinate' : `${r.radius_basis || '—'} · n=${r.n_calibration ?? '—'}`}
          />
          <Figure
            value={r.measured_coverage === null || r.measured_coverage === undefined ? '—' : `${(r.measured_coverage * 100).toFixed(1)}%`}
            caption="measured coverage"
            note={`empirical p80 · stratum ${r.source_stratum || '—'}`}
          />
          <Figure
            value={r.score === null ? '—' : r.score.toFixed(3)}
            caption="rank score" tone="survey"
            note={r.candidate?.arm || 'no candidate'}
          />
        </div>

        <KV items={[
          ['answer', r.candidate ? `${r.candidate.arm} · ${r.candidate.granularity}` : 'no candidate'],
          ['source', r.candidate?.source_ref || '—'],
          ['coordinate space', <span className="mono">{r.coordinate?.coordinate_space || `sutra_local_metric_plane:${r.town_id || '—'}`}</span>],
          ['as of', <span className="mono">{fmtTime(r.as_of)}</span>],
          ['computed at', <span className="mono">{fmtTime(r.computed_at)}</span>],
          ['belief version', <span className="mono">v{r.belief_version ?? '—'}</span>],
          ['place', r.place_id ? <Link className="mono" to={`/places?place=${r.place_id}`}>{r.place_id}</Link> : '—'],
          ['resolution', <span className="mono">{r.resolution}</span>],
        ]} />

        <div>
          <div className="eyebrow" style={{ marginBottom: 6 }}>why · typed reason codes</div>
          <WhyList codes={r.reason_codes || []} limit={9} />
        </div>

        {r.evidence_summary && (
          <div>
            <div className="eyebrow" style={{ marginBottom: 6 }}>evidence summary</div>
            <div className="figure-row">
              <Figure value={r.evidence_summary.n_observations} caption="visits" note={`${r.evidence_summary.n_positives} positive · ${r.evidence_summary.negatives_independent} independent negative`} />
              <Figure value={r.evidence_summary.independent_confirmations} caption="independent confirmations" note={`duplicate claims ${r.evidence_summary.duplicate_claims}`} tone={r.evidence_summary.independent_confirmations >= 2 ? 'serve' : undefined} />
              <Figure value={r.evidence_summary.positive_weight_sum.toFixed(3)} caption="positive weight" note={`negatives move the coordinate: ${r.evidence_summary.negatives_move_coordinate ? 'yes' : 'no'}`} />
            </div>
          </div>
        )}

        {r.task && (
          <div className="banner verify" style={{ display: 'block' }}>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 6 }}>
              <ShieldAlert size={15} color="var(--warn)" />
              <strong style={{ fontSize: 12, letterSpacing: '0.02em' }}>{r.task.task_id}</strong>
              <Chip sm mono tone="warn">{r.task.cause}</Chip>
              <Chip sm mono>{r.task.state}</Chip>
            </div>
            <div style={{ fontSize: 11.5, color: 'var(--ink-soft)' }}>{r.task.recommended_action.label}</div>
            <div style={{ fontSize: 11, color: 'var(--ink-faint)', marginTop: 3 }}>clears when: {r.task.recommended_action.clears_when}</div>
            <div style={{ marginTop: 8, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              <Link className="btn sm" to={`/evidence?address=${r.address_id}`}>Evidence</Link>
              <Link className="btn sm" to="/queue">Verify queue <ArrowRight size={12} /></Link>
              {r.place_id && <Link className="btn sm" to={`/places?place=${r.place_id}`}>Place history</Link>}
            </div>
          </div>
        )}

        {r.directions?.length > 0 && (
          <div>
            <div className="eyebrow" style={{ marginBottom: 6 }}>landmark cues · official landmarks only</div>
            <div style={{ display: 'grid', gap: 4 }}>
              {r.directions.slice(0, 3).map((d) => (
                <div key={d.source_ref} style={{ display: 'flex', gap: 8, alignItems: 'baseline', fontSize: 11.5 }}>
                  <MapPin size={12} color="var(--ink-faint)" />
                  <span>{d.cue_text}</span>
                  {d.ambiguous && <Chip sm tone="warn">ambiguous landmark</Chip>}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
