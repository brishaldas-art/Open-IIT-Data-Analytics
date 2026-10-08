/**
 * OPERATIONS — what the field operation actually looks like right now.
 *
 * Every figure on this page comes from `GET /v1/overview`: indexed addresses, where they stand, the
 * active verification work in the operator's language, recent field activity and how fresh the
 * offline packs are. There are no store counters, no firewall counters, no latency and no capability
 * matrix here — those are engineering concerns and they were deliberately moved off this page.
 */
import { Link } from 'react-router-dom'
import { ArrowRight, HardDriveDownload, Package } from 'lucide-react'
import { overview } from '../api/endpoints'
import { useApi } from '../api/useApi'
import type { OverviewPayload } from '../api/types'
import { Chip, Figure, Panel, Skeleton, fmtTime } from '../components/ui'
import { ASOF_MOMENT, REFERENCE_CASES } from '../config/product'
import { useApp } from '../state/appState'

export function OperationsPage() {
  const { apiReachable, asOf } = useApp()
  const cut = asOf || ASOF_MOMENT
  const q = useApi<OverviewPayload>({ key: ['overview', cut], live: () => overview(cut) })
  const o = q.data?.data

  return (
    <div className="grid" style={{ gap: 'var(--s4)' }}>
      <div style={{ display: 'flex', gap: 'var(--s3)', alignItems: 'center', flexWrap: 'wrap' }}>
        <span className={`pill ${apiReachable === false ? 'neg' : 'serve'}`} data-testid="live-state">
          <span className="dot" />{apiReachable === false ? 'Service unreachable' : 'Live service'}
        </span>
        <span className="mono" style={{ fontSize: 10.5, color: 'var(--ink-faint)' }}>
          figures as of {fmtTime(cut)}{q.data?.fixture ? ' · captured response' : ''}
        </span>
      </div>

      <div className="grid cols-4">
        <Panel title="Address coverage" bodyClass="tight">
          {!o ? <Skeleton lines={3} /> : (
            <div style={{ display: 'grid', gap: 10 }}>
              <Figure value={o.addresses.indexed.toLocaleString()} caption="addresses on record"
                note={`${o.addresses.with_location.toLocaleString()} with a usable location · ${o.addresses.confirmed.toLocaleString()} confirmed in the field`} />
              <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                <Chip sm tone={o.addresses.conflicting ? 'warn' : 'pos'}>
                  {o.addresses.conflicting} with conflicting evidence
                </Chip>
                <Chip sm tone="ghost">{o.addresses.not_confirmed.toLocaleString()} not yet confirmed</Chip>
              </div>
              <div style={{ fontSize: 11, color: 'var(--ink-soft)', lineHeight: 1.5 }}>
                with a field record at this instant: <span className="mono">{o.addresses.warm.toLocaleString()}</span> ·
                none yet: <span className="mono">{o.addresses.cold.toLocaleString()}</span>
                {' '}({o.addresses.warm_share != null ? `${Math.round(o.addresses.warm_share * 100)} %` : '—'} of the index)
                <br />
                beliefs materialised at this instant:{' '}
                <span className="mono">
                  {Object.values(o.addresses.by_tier).reduce((a, b) => a + b, 0).toLocaleString()}
                </span>
              </div>
              <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                {Object.entries(o.addresses.by_tier).map(([tier, n]) => (
                  <Chip key={tier} sm mono tone={tier === 'CONFIRMED' ? 'pos' : tier === 'APPROXIMATE' ? 'warn' : 'ghost'}>
                    {tier.toLowerCase()} {n.toLocaleString()}
                  </Chip>
                ))}
              </div>
            </div>
          )}
        </Panel>

        <Panel title="Needs attention" bodyClass="tight">
          {!o ? <Skeleton lines={3} /> : (
            <div style={{ display: 'grid', gap: 8 }}>
              <Figure value={o.workload.active_cases} caption="open cases" tone="warn"
                note={o.workload.by_reason.map((r) => `${r.title.toLowerCase()} ${r.count}`).join(' · ') || 'nothing waiting'} />
              <Link className="btn sm" to="/queue">Open the queue <ArrowRight size={12} /></Link>
            </div>
          )}
        </Panel>

        <Panel title="Field activity" bodyClass="tight">
          {!o ? <Skeleton lines={3} /> : (
            <div style={{ display: 'grid', gap: 8 }}>
              <Figure value={o.field_activity.visits_last_30_days.toLocaleString()} caption={`visits in the last ${o.field_activity.window_days} days`}
                note={`${o.field_activity.visits_recorded.toLocaleString()} on record at this cut · latest ${fmtTime(o.field_activity.latest_visit)}`} tone="survey" />
            </div>
          )}
        </Panel>

        <Panel title="Offline packs" right={<Package size={13} color="var(--ink-faint)" />} bodyClass="tight">
          {!o ? <Skeleton lines={3} /> : (
            <div style={{ display: 'grid', gap: 6 }}>
              {o.data_freshness.packs.map((p) => (
                <div key={p.town_id} style={{ display: 'flex', justifyContent: 'space-between', gap: 8, alignItems: 'baseline' }}>
                  <span className="mono" style={{ fontSize: 11 }}>{p.town_id}</span>
                  <span style={{ fontSize: 11, color: 'var(--ink-soft)' }}>
                    {p.addresses?.toLocaleString()} addresses · {p.age_days === 0 ? 'current' : `${p.age_days} d old`}
                  </span>
                </div>
              ))}
              <div style={{ display: 'flex', gap: 6, alignItems: 'center', color: 'var(--ink-faint)', fontSize: 10.5 }}>
                <HardDriveDownload size={12} /> {o.data_freshness.available_offline ? 'These packs travel with the field team.' : 'No offline pack is available.'}
              </div>
            </div>
          )}
        </Panel>
      </div>

      <div className="grid cols-2">
        <Panel title="Where the work is" right={<span className="eyebrow">as of {fmtTime(o?.as_of ?? cut)}</span>}>
          {!o ? <Skeleton lines={5} /> : (
            <>
              <table className="table">
                <thead><tr><th>area</th><th className="num">addresses</th><th className="num">open cases</th></tr></thead>
                <tbody>
                  {o.towns.map((t) => (
                    <tr key={t.town_id} style={{ cursor: 'default' }}>
                      <td className="mono">{t.town_id}</td>
                      <td className="num mono">{t.addresses.toLocaleString()}</td>
                      <td className="num mono">{t.needs_review}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <p style={{ fontSize: 10.5, color: 'var(--ink-faint)', marginBottom: 0 }}>
                A case appears here when new field evidence contradicts the current answer — it is never raised
                by this page. {apiReachable === false && 'The live service is unreachable, so this page is showing its last captured response.'}
              </p>
            </>
          )}
        </Panel>

        <div className="col" style={{ gap: 'var(--s4)' }}>
          <Panel title="Why cases are open">
            {!o ? <Skeleton lines={4} /> : (
              <div style={{ display: 'grid', gap: 10 }}>
                {o.workload.by_reason.map((r) => (
                  <div key={r.cause} style={{ display: 'grid', gap: 2 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, alignItems: 'baseline' }}>
                      <span style={{ fontSize: 12.5 }}>{r.title}</span>
                      <span className="mono" style={{ fontSize: 11, color: 'var(--ink-soft)' }}>{r.count}</span>
                    </div>
                    {r.detail && <div style={{ fontSize: 11, color: 'var(--ink-soft)', lineHeight: 1.5 }}>{r.detail}</div>}
                  </div>
                ))}
                <div style={{ fontSize: 10.5, color: 'var(--ink-faint)' }}>
                  Nothing is escalated automatically to a person; each case states what would clear it.
                </div>
              </div>
            )}
          </Panel>

          <Panel title="Saved examples" right={<Link className="btn sm" to="/resolve">Workbench <ArrowRight size={12} /></Link>}>
            <div style={{ display: 'grid', gap: 8 }}>
              {REFERENCE_CASES.map((c) => (
                <div key={c.key} style={{ display: 'flex', gap: 8, alignItems: 'baseline', flexWrap: 'wrap' }}>
                  <Chip mono tone={c.story === 'serve' ? 'pos' : c.story === 'verify' ? 'warn' : 'neg'}>{c.address_id}</Chip>
                  <span style={{ fontSize: 11.5, color: 'var(--ink-soft)' }}>{c.blurb}</span>
                </div>
              ))}
              <div style={{ fontSize: 10.5, color: 'var(--ink-faint)' }}>
                Real addresses from the official table. They are entry points only — every number behind them is
                computed by the service when you open them.
              </div>
            </div>
          </Panel>
        </div>
      </div>
    </div>
  )
}
