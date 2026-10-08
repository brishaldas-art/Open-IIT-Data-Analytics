/**
 * VERIFY QUEUE — every human action on this screen is a real API call.
 *
 * Lifecycle buttons call `PATCH /v1/tasks/{id}` (append-only transitions); a reviewer's decision calls
 * `POST /v1/adjudicate`, which stores an adjudication observation and lets the frozen engine recompute
 * the belief. Both are idempotent with deterministic keys, and this screen never invents a state: the
 * allowed transitions are the ones the service says are allowed.
 */
import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { CheckCircle2, ChevronRight, Filter, ListFilter, ShieldCheck } from 'lucide-react'
import { adjudicate, taskDetail, tasks, transitionTask, type AdjudicationResult, type TaskDetail } from '../api/endpoints'
import { useApi } from '../api/useApi'
import type { TasksPayload, VerificationTask } from '../api/types'
import { Chip, Empty, Figure, Panel, Skeleton, fmtTime } from '../components/ui'
import { useApp } from '../state/appState'

function FacetBar({ label, values, active, onPick }: {
  label: string; values: Record<string, number>; active: string | null; onPick: (v: string | null) => void
}) {
  const entries = Object.entries(values).sort((a, b) => b[1] - a[1])
  return (
    <div style={{ display: 'grid', gap: 5 }}>
      <div className="eyebrow">{label}</div>
      <div className="facets">
        <button className="btn tab" aria-pressed={active === null} onClick={() => onPick(null)}>all</button>
        {entries.map(([k, n]) => (
          <span className="facet" key={k}>
            <button className="btn tab" aria-pressed={active === k} onClick={() => onPick(active === k ? null : k)}>{k.toLowerCase().replace(/_/g, ' ')}</button>
            <span className="n tnum">{n}</span>
          </span>
        ))}
      </div>
    </div>
  )
}

export function QueuePage() {
  const { asOf } = useApp()
  const [town, setTown] = useState<string | null>('T2')
  const [cause, setCause] = useState<string | null>(null)
  const [stateFilter, setStateFilter] = useState<string | null>(null)
  const [limit, setLimit] = useState(15)
  const [cursor, setCursor] = useState<string | null>(null)
  const [pages, setPages] = useState<VerificationTask[][]>([])
  /** the whole task object, not just its id: a decided case leaves the open queue, and its panel
   *  must stay put — the reviewer has to see what their decision did. */
  const [selected, setSelected] = useState<VerificationTask | null>(null)

  const q = useApi<TasksPayload>({
    key: ['tasks', town, cause, stateFilter, String(limit), cursor, asOf],
    fixtureKey: !cursor ? 'tasks_T2' : undefined,
    live: () => tasks({
      town_id: town || undefined, cause: cause || undefined, state: stateFilter || undefined,
      as_of: asOf, limit, cursor: cursor || undefined,
    }),
  })
  const data = q.data?.data

  const rows = useMemo(() => [...pages.flat(), ...(data?.items || [])], [pages, data])
  const uniqueRows = useMemo(() => {
    const seen = new Set<string>()
    const out: VerificationTask[] = []
    for (const r of rows) {
      if (seen.has(r.task_id)) continue
      seen.add(r.task_id)
      out.push(r)
    }
    return out
  }, [rows])
  const selectedTask = selected

  const loadMore = () => {
    if (!data?.next_cursor) return
    setPages((p) => [...p, data.items])
    setCursor(data.next_cursor)
  }

  return (
    <div className="grid" style={{ gap: 'var(--s4)' }}>
      <div className="banner info">
        <ShieldCheck className="icon" size={15} color="var(--info)" />
        <div>
          <h4>Actions are real, and they are appended</h4>
          <p>
            Starting a review, recording a decision and reopening a case all write to the service: the case
            lifecycle is an append-only ledger and a reviewer's decision is stored as an <span className="mono">adjudication</span>
            {' '}observation, after which the frozen engine recomputes the belief. Nothing on this screen changes
            state locally. Every write carries an idempotency key, so a retry replays rather than duplicates.
          </p>
        </div>
      </div>

      <div className="grid cols-4">
        <Panel title="Open tasks" bodyClass="tight">
          {!data ? <Skeleton lines={2} /> : <Figure value={data.total_matching} caption="matching this filter" note={`${data.count} on this page`} tone="warn" />}
        </Panel>
        <Panel title="Cause mix" bodyClass="tight">
          {!data ? <Skeleton lines={2} /> : (
            <div style={{ display: 'grid', gap: 3, fontSize: 11.5 }}>
              {Object.entries(data.facets.by_cause).map(([k, v]) => (
                <div key={k} style={{ display: 'flex', justifyContent: 'space-between' }}><span>{k.toLowerCase().replace(/_/g, ' ')}</span><span className="mono tnum">{v}</span></div>
              ))}
            </div>
          )}
        </Panel>
        <Panel title="Town spread" bodyClass="tight">
          {!data ? <Skeleton lines={2} /> : (
            <div style={{ display: 'grid', gap: 3, fontSize: 11.5 }}>
              {Object.entries(data.facets.by_town).map(([k, v]) => (
                <div key={k} style={{ display: 'flex', justifyContent: 'space-between' }}><span className="mono">{k}</span><span className="mono tnum">{v}</span></div>
              ))}
            </div>
          )}
        </Panel>
        <Panel title="State" bodyClass="tight">
          {!data ? <Skeleton lines={2} /> : (
            <div style={{ display: 'grid', gap: 3, fontSize: 11.5 }}>
              {Object.entries(data.facets.by_state).map(([k, v]) => (
                <div key={k} style={{ display: 'flex', justifyContent: 'space-between' }}><span>{k}</span><span className="mono tnum">{v}</span></div>
              ))}
              <div style={{ fontSize: 10.5, color: 'var(--ink-faint)' }}>States come from the task ledger: needs review, under review, reviewed, reopened.</div>
            </div>
          )}
        </Panel>
      </div>

      <Panel title="Filters" right={<ListFilter size={13} color="var(--ink-faint)" />}>
        <div className="grid cols-3" style={{ gap: 'var(--s4)' }}>
          <div style={{ display: 'grid', gap: 5 }}>
            <div className="eyebrow">town</div>
            <div className="facets">
              <button className="btn tab" aria-pressed={town === null} onClick={() => { setTown(null); setCursor(null); setPages([]) }}>all</button>
              {(data ? Object.keys(data.facets.by_town) : ['T1', 'T2', 'T3']).map((t) => (
                <button key={t} className="btn tab" aria-pressed={town === t} onClick={() => { setTown(t); setCursor(null); setPages([]) }}>{t}</button>
              ))}
            </div>
          </div>
          <FacetBar label="cause" values={data?.facets.by_cause || {}} active={cause} onPick={(v) => { setCause(v); setCursor(null); setPages([]) }} />
          <FacetBar label="state" values={data?.facets.by_state || {}} active={stateFilter} onPick={(v) => { setStateFilter(v); setCursor(null); setPages([]) }} />
        </div>
        <div style={{ marginTop: 'var(--s3)', display: 'flex', gap: 'var(--s4)', alignItems: 'center', flexWrap: 'wrap' }}>
          <div className="field" style={{ width: 130 }}>
            <label htmlFor="limit">page size</label>
            <select id="limit" className="select mono" value={limit} onChange={(e) => { setLimit(Number(e.target.value)); setCursor(null); setPages([]) }}>
              {[15, 30, 60].map((n) => <option key={n} value={n}>{n}</option>)}
            </select>
          </div>
          <div style={{ fontSize: 10.5, color: 'var(--ink-faint)', display: 'flex', gap: 8, alignItems: 'center' }}>
            <Filter size={12} /> Filters are sent to <span className="mono">GET /v1/tasks</span> as query parameters; facet counts come from the same response.
          </div>
          {data?.next_cursor && <button className="btn sm" style={{ marginLeft: 'auto' }} onClick={loadMore}>Load next page <ChevronRight size={12} /></button>}
        </div>
      </Panel>

      <div className="grid" style={{ gridTemplateColumns: selectedTask ? 'minmax(0,1.6fr) minmax(0,1fr)' : 'minmax(0,1fr)', gap: 'var(--s4)' }}>
        <Panel title="Tasks" right={data && <span className="mono" style={{ fontSize: 10, color: 'var(--ink-faint)' }}>{uniqueRows.length} shown · as of {fmtTime(data.as_of)}</span>}>
          {q.isLoading && <Skeleton lines={8} />}
          {q.isError && <Empty title="could not load queue" hint={String(q.error?.message)} />}
          {data && !uniqueRows.length && <Empty title="nothing matches" hint="No verification task matches the current filters at this as-of instant." />}
          {uniqueRows.length > 0 && (
            <table className="table" data-testid="task-table">
              <thead>
                <tr>
                  <th>task</th><th>cause</th><th>town</th><th>address</th>
                  <th className="num">indep. neg.</th><th className="num">radius (m)</th><th className="num">priority</th><th>at</th>
                </tr>
              </thead>
              <tbody>
                {uniqueRows.map((t) => (
                  <tr key={t.task_id} aria-selected={selected?.task_id === t.task_id} onClick={() => setSelected(t)}>
                    <td className="mono" style={{ fontSize: 10.5 }}>{t.task_id}</td>
                    <td><Chip sm mono tone="warn">{t.cause.toLowerCase().replace(/_/g, ' ')}</Chip></td>
                    <td className="mono">{t.town_id}</td>
                    <td className="mono">{t.address_id}</td>
                    <td className="num mono">{t.negatives_independent}</td>
                    <td className="num mono">{t.radius_m.toFixed(1)}</td>
                    <td className="num mono">{t.priority.toFixed(2)}</td>
                    <td className="mono" style={{ fontSize: 10.5 }}>{fmtTime(t.at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Panel>

        {selectedTask && (
          <CasePanel task={selectedTask} onClose={() => setSelected(null)} />
        )}
      </div>
    </div>
  )
}

/**
 * The case panel: the service's own view of one case, plus the two real writes a reviewer can make.
 * `allowed_transitions` comes from `GET /v1/tasks/{id}` — this component never decides what is legal.
 */
function CasePanel({ task, onClose }: { task: VerificationTask; onClose: () => void }) {
  const { reviewer, asOf } = useApp()
  const qc = useQueryClient()
  const [note, setNote] = useState('')
  const [pending, setPending] = useState<string | null>(null)
  const [problem, setProblem] = useState<string | null>(null)
  const [result, setResult] = useState<AdjudicationResult | null>(null)

  const detail = useApi<TaskDetail>({
    key: ['task', task.task_id, asOf],
    live: () => taskDetail(task.task_id),
  })
  const d = detail.data?.data

  const refresh = async () => {
    await Promise.all([
      qc.invalidateQueries({ queryKey: ['task', task.task_id] }),
      qc.invalidateQueries({ queryKey: ['tasks'] }),
      qc.invalidateQueries({ queryKey: ['overview'] }),
    ])
  }

  const move = async (to: string) => {
    setPending(to); setProblem(null)
    try {
      await transitionTask(task.task_id, {
        state: to, actor: reviewer, note: note || null, at: null,
        idempotency_key: `tr:${task.task_id}:${to}:${asOf}:${reviewer}`,
      })
      await refresh()
    } catch (e) {
      setProblem((e as Error).message)
    } finally {
      setPending(null)
    }
  }

  const decide = async (decision: string) => {
    setPending(decision); setProblem(null); setResult(null)
    try {
      const out = await adjudicate({
        task_id: task.task_id, decision, actor: reviewer, note: note || null, as_of: null,
        idempotency_key: `adj:${task.address_id}:${decision}:${asOf}:${reviewer}`,
      })
      setResult(out)
      await refresh()
    } catch (e) {
      setProblem((e as Error).message)
    } finally {
      setPending(null)
    }
  }

  const canReopen = d ? d.allowed_transitions.includes('reopened') : false
  const canStart = d ? d.allowed_transitions.includes('in_progress') : false
  const canDecide = d ? d.task.state === 'open' || d.task.state === 'in_progress' || d.task.state === 'reopened' : false

  return (
    <Panel title={task.task_id}
      right={<button className="btn sm" onClick={onClose}>close</button>}>
      <div style={{ display: 'grid', gap: 12 }}>
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', alignItems: 'center' }}>
          <Chip mono tone={d && d.task.state === 'resolved' ? 'pos' : 'warn'}>
            {d ? d.state_label : task.state}
          </Chip>
          <Chip mono>{task.cause.replace(/_/g, ' ').toLowerCase()}</Chip>
          <Chip mono tone="ghost">rule {task.rule_version}</Chip>
        </div>

        <dl className="kv">
          <dt>address</dt><dd className="mono">{task.address_id}</dd>
          <dt>place</dt><dd className="mono">{task.place_id}</dd>
          <dt>tier / status</dt><dd className="mono">{task.tier} · {task.status}</dd>
          <dt>uncertainty</dt><dd className="mono">± {task.radius_m.toFixed(1)} m</dd>
          <dt>independent negatives</dt><dd className="mono">{task.negatives_independent}</dd>
          <dt>raised at</dt><dd className="mono">{fmtTime(task.at)}</dd>
          <dt>recommended action</dt><dd>{task.recommended_action.label}</dd>
          <dt>clears when</dt><dd className="mono">{task.recommended_action.clears_when}</dd>
          <dt>evidence refs</dt>
          <dd>
            <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap' }}>
              {task.evidence_refs.map((e) => (
                <Link key={e} className="chip mono" to={`/evidence?address=${task.address_id}`}>{e}</Link>
              ))}
              <span style={{ fontSize: 10, color: 'var(--ink-faint)' }}>{task.evidence_refs_basis}</span>
            </div>
          </dd>
        </dl>

        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          <Link className="btn primary" to={`/resolve?address=${task.address_id}&town=${task.town_id}`}>Open in Resolve</Link>
          <Link className="btn" to={`/evidence?address=${task.address_id}`}>View evidence</Link>
          <Link className="btn" to={`/places?place=${task.place_id}`}>Place</Link>
        </div>

        <div className="field">
          <label htmlFor="revnote">note (stored with the decision)</label>
          <input id="revnote" className="input" value={note} placeholder="what the reviewer observed"
            onChange={(e) => setNote(e.target.value)} />
        </div>

        <div style={{ display: 'grid', gap: 6 }}>
          <div className="eyebrow">case actions · recorded by {reviewer}</div>
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            {canStart && (
              <button className="btn sm" data-testid="action-start" disabled={pending !== null}
                onClick={() => move('in_progress')}>Start review</button>
            )}
            {canDecide && (
              <button className="btn sm primary" data-testid="action-confirm" disabled={pending !== null}
                onClick={() => decide('confirmed')}>
                <CheckCircle2 size={12} /> {pending === 'confirmed' ? 'recording…' : 'Confirm location'}
              </button>
            )}
            {canDecide && (
              <button className="btn sm" data-testid="action-not-true" disabled={pending !== null}
                onClick={() => decide('not_true')}>Mark not true</button>
            )}
            {canDecide && (
              <button className="btn sm" data-testid="action-inconclusive" disabled={pending !== null}
                onClick={() => decide('inconclusive')}>Inconclusive</button>
            )}
            {canReopen && (
              <button className="btn sm" data-testid="action-reopen" disabled={pending !== null}
                onClick={() => move('reopened')}>Reopen case</button>
            )}
          </div>
          <div style={{ fontSize: 10.5, color: 'var(--ink-faint)' }}>
            A decision is stored as an adjudication observation (source: reviewer, not a visit) and the belief is
            recomputed by the frozen engine. Only field evidence or an adjudication can move a location; a
            “not true” decision can never relocate one by itself.
          </div>
        </div>

        {problem && <div className="banner refuse"><div style={{ fontSize: 11.5 }}>{problem}</div></div>}

        {d && d.task.state === 'resolved' && (
          <div style={{ fontSize: 10.5, color: 'var(--ink-faint)' }}>
            This case has left the open queue. Its history stays here and in the audit chain — a case is never
            deleted, only reviewed.
          </div>
        )}

        {result && (
          <div className="banner" data-testid="adjudication-effect"
            style={{ borderLeftColor: 'var(--pos)' }}>
            <div style={{ fontSize: 11.5, display: 'grid', gap: 4 }}>
              <div>
                {result.replayed ? 'Already recorded — replayed' : 'Recorded'}: decision <strong>{result.decision}</strong> as
                {' '}<span className="mono">kind=adjudication</span>, scored as <span className="mono">{result.outcome}</span>
                {' '}({result.mapping.outcome_class}).
              </div>
              <div>
                belief {result.effect.belief_before?.tier} → {result.effect.belief_after?.tier}
                {' '}· uncertainty {(result.effect.belief_before?.radius_m ?? 0).toFixed(1)} m → {(result.effect.belief_after?.radius_m ?? 0).toFixed(1)} m
                {' '}· location {result.effect.coordinate_moved ? 'moved' : 'unchanged'} · belief v{result.belief_version}
              </div>
              {result.task.closed && <div>case closed: {result.task.state_label}</div>}
            </div>
          </div>
        )}

        {d && d.history.length > 0 && (
          <div style={{ display: 'grid', gap: 6 }}>
            <div className="eyebrow">decision history · appended, never rewritten</div>
            <div style={{ display: 'grid', gap: 4 }}>
              {[...d.history].reverse().map((h) => (
                <div key={h.event_id} style={{ display: 'flex', gap: 8, alignItems: 'baseline', fontSize: 11 }}>
                  <span className="mono" style={{ fontSize: 10, color: 'var(--ink-faint)' }}>{fmtTime(h.at)}</span>
                  <span>{h.state_label}</span>
                  {h.actor && <span className="mono" style={{ fontSize: 10 }}>{h.actor}</span>}
                  {h.note && <span style={{ color: 'var(--ink-soft)' }}>“{h.note}”</span>}
                </div>
              ))}
            </div>
            {d.adjudications.map((a) => (
              <div key={a.event_id} style={{ fontSize: 10.5, color: 'var(--ink-faint)' }}>
                decided against {a.decided_against.tier} · {a.decided_against.status}
                {a.decided_against.radius_m != null && ` · ± ${a.decided_against.radius_m.toFixed(1)} m`}
              </div>
            ))}
          </div>
        )}

        {detail.isError && (
          <div style={{ fontSize: 10.5, color: 'var(--neg)' }}>case detail unavailable: {detail.error?.message}</div>
        )}
      </div>
    </Panel>
  )
}
