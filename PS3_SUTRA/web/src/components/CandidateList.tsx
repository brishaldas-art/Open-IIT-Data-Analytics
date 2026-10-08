/**
 * Candidate list. Ordering is the contract's own: score desc, candidate_id asc; `rank` is supplied
 * by the service (the winner is rank 1). Nothing here re-scores anything.
 */
import type { CandidateRef, CandidateRow, ResolveResponse } from '../api/types'
import { Chip } from './ui'

interface Props {
  response: ResolveResponse
  selected: string | null
  onSelect: (candidateId: string) => void
}

function Term({ term }: { term: string }) {
  // Rendered verbatim: these are the service's own score terms, not a string we interpret.
  const eq = term.indexOf('=')
  const label = eq > 0 ? term.slice(0, eq) : term
  const value = eq > 0 ? term.slice(eq + 1) : ''
  const negative = value.trim().startsWith('-')
  return (
    <div className="term">
      <span>{label}</span>
      <span className={`e ${negative ? 'neg' : ''}`}>{value}</span>
    </div>
  )
}

export function CandidateList({ response, selected, onSelect }: Props) {
  const winner: CandidateRef | null = response.candidate
    ? {
        candidate_id: response.candidate.candidate_id,
        arm: response.candidate.arm,
        score: response.score,
        primary_eligible: true,
        reasons: response.score_reasons,
      }
    : null
  const rows: CandidateRow[] = response.alternatives || []

  return (
    <div className="cand">
      {winner && (
        <div>
          <button className="cand-row" aria-selected={selected === winner.candidate_id} onClick={() => onSelect(winner.candidate_id)}>
            <span className="rk">1</span>
            <span>
              <span className="arm">{winner.arm}</span>
              <span className="meta">
                <span>{response.granularity}</span>
                <span>·</span>
                <span>selector rank 1</span>
                {response.coordinate && <><span>·</span><span>{response.coordinate.x.toFixed(1)}, {response.coordinate.y.toFixed(1)} m</span></>}
              </span>
            </span>
            <span className="sc">{winner.score !== null ? winner.score.toFixed(3) : '—'}</span>
          </button>
          {selected === winner.candidate_id && (
            <div className="cand-detail">
              <div className="eyebrow" style={{ marginBottom: 2 }}>score terms · from the ranker</div>
              {winner.reasons.length ? winner.reasons.map((t, i) => <Term key={i} term={t} />)
                : <div className="term" style={{ color: 'var(--ink-faint)' }}>no score terms on this response</div>}
            </div>
          )}
        </div>
      )}

      {rows.map((c) => (
        <div key={c.candidate_id}>
          <button className="cand-row" aria-selected={selected === c.candidate_id} onClick={() => onSelect(c.candidate_id)}>
            <span className="rk">{c.rank}</span>
            <span>
              <span className="arm">{c.arm}</span>
              <span className="meta">
                <span>{c.granularity || '—'}</span>
                {!c.primary_eligible && <><span>·</span><span>not primary-eligible</span></>}
                <span>·</span><span className="mono">{c.candidate_id}</span>
              </span>
            </span>
            <span className="sc">{c.score.toFixed(3)}</span>
          </button>
          {selected === c.candidate_id && (
            <div className="cand-detail">
              <div className="eyebrow" style={{ marginBottom: 2 }}>why it did not win · supplied by the service</div>
              <div className="lost">
                {c.lost_reason.map((l, i) => <Chip key={i} sm mono tone={l.startsWith('score_margin') ? 'ghost' : 'warn'}>{l}</Chip>)}
              </div>
              <div className="eyebrow" style={{ marginTop: 8, marginBottom: 2 }}>score terms</div>
              {c.reasons.map((t, i) => <Term key={i} term={t} />)}
            </div>
          )}
        </div>
      ))}

      {!winner && !rows.length && (
        <div className="empty" style={{ padding: 'var(--s5) 0' }}>
          <div className="eyebrow">no ranked candidate</div>
          <div style={{ fontSize: 11.5 }}>The service returned no candidate for this query.</div>
        </div>
      )}
    </div>
  )
}
