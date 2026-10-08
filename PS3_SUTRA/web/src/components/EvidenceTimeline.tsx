/**
 * Visit timeline. The claim/non-claim distinction is the point of this component: a negative
 * observation carries a captured position but is *not* a location claim, and the service says so
 * explicitly (`coordinate_claim: false`, `contributes: negative_doubt`). We render that verbatim.
 */
import type { EvidenceObservation } from '../api/types'
import { Chip, Empty, fmtTime } from './ui'

function PolarityDot({ o }: { o: EvidenceObservation }) {
  const cls = o.polarity === 'negative' ? 'neg' : o.polarity === 'positive' ? 'pos' : 'amb'
  return <span className={`tl-dot ${cls}`} />
}

export function EvidenceTimeline({ observations, onFocus, selectedId, compact }: {
  observations: EvidenceObservation[]
  onFocus?: (o: EvidenceObservation) => void
  selectedId?: string | null
  compact?: boolean
}) {
  if (!observations.length) {
    return <Empty title="no visits" hint="No observation exists for this address at the selected as-of instant." />
  }
  const rows = compact ? observations.slice(-3) : observations
  return (
    <div className="timeline">
      {rows.map((o) => {
        const nonClaim = o.coordinate_claim === false || o.polarity === 'negative'
        return (
          <div className="tl-row" key={o.observation_id} onClick={() => onFocus?.(o)}
            style={{ cursor: onFocus ? 'pointer' : 'default', background: selectedId === o.observation_id ? 'rgba(196,82,30,0.05)' : undefined }}>
            <div className="tl-time">{fmtTime(o.observed_at)}</div>
            <div className="tl-spine"><span className="tl-line" /><PolarityDot o={o} /></div>
            <div className="tl-body">
              <div className="tl-top">
                <span className="tl-outcome">{o.outcome}</span>
                <Chip sm mono tone={o.polarity === 'negative' ? 'neg' : o.polarity === 'positive' ? 'pos' : 'warn'}>{o.polarity}</Chip>
                <Chip sm mono>{o.evidence.evidence_class}</Chip>
                <Chip sm mono tone="ghost">weight {o.evidence.weight.toFixed(4)}</Chip>
                {nonClaim && <Chip sm tone="neg">non-claim</Chip>}
                {o.duplicate_claim_of && <Chip sm tone="warn">duplicate of {o.duplicate_claim_of}</Chip>}
              </div>
              {o.remark && <div className="tl-note">“{o.remark}”</div>}
              <div className="tl-meta">
                <span className="mono">{o.observation_id}</span>
                {o.visit_id && <span className="mono">visit {o.visit_id}</span>}
                {o.agent_id && <span className="mono">agent {o.agent_id}</span>}
                {o.dwell_s !== null && <span>dwell {Math.round(o.dwell_s)}s</span>}
                {o.media?.length ? <span>{o.media.length} photo hash{o.media.length > 1 ? 'es' : ''}</span> : null}
                <span>{o.contributes.replace(/_/g, ' ')}</span>
              </div>
              {!compact && (
                <div className="claim-split" style={{ marginTop: 6, maxWidth: 520 }}>
                  <div>
                    <span className="cap">captured position</span>
                    <div className="mono">{o.captured.x !== null ? `${o.captured.x.toFixed(1)}, ${o.captured.y?.toFixed(1)} m` : 'none recorded'}
                      {o.captured.gps_accuracy_m !== null && <span style={{ color: 'var(--ink-faint)' }}> · ±{o.captured.gps_accuracy_m} m GPS</span>}</div>
                  </div>
                  <div className="neq">{nonClaim ? '≠' : '='}</div>
                  <div>
                    <span className="cap">location claim</span>
                    <div className="mono" style={{ color: nonClaim ? 'var(--neg)' : 'var(--pos)' }}>
                      {o.coordinate_claim ? `${o.x?.toFixed(1)}, ${o.y?.toFixed(1)} m` : 'none — never a claim'}
                    </div>
                  </div>
                </div>
              )}
              {!compact && (
                <div style={{ marginTop: 6, display: 'flex', gap: 5, flexWrap: 'wrap' }}>
                  {o.evidence.reason_codes.map((c) => <Chip key={c} sm mono tone="ghost">{c}</Chip>)}
                </div>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}
