/**
 * METHOD & TRUST — the explanatory surface.
 *
 * The mechanism, the safety rules and the three evaluation populations are read from
 * `GET /v1/method-trust`, which assembles them from the frozen evaluation receipts. Nothing on this
 * page is typed in by hand and nothing is recomputed by the browser. The populations are never
 * merged, and there is no single accuracy claim anywhere.
 */
import { Link } from 'react-router-dom'
import { AlertTriangle, ArrowRight, BookOpen, ShieldCheck } from 'lucide-react'
import { health, methodTrust } from '../api/endpoints'
import { useApi } from '../api/useApi'
import type { HealthPayload, MethodTrustPayload } from '../api/types'
import { Chip, Panel, Skeleton } from '../components/ui'
import { useEffect, useState } from 'react'
import { FIXTURES_ENABLED } from '../config/product'

const FAST_LOOP = [
  { n: '01', t: 'Visit', d: 'A collector stands at the address. Check-in, dwell, photos, device time.' },
  { n: '02', t: 'Evidence', d: 'Graded: outcome × dwell × GPS × trail × media × timing × agent baseline.' },
  { n: '03', t: 'Weighting', d: 'Weight and reason codes per observation; negatives carry no location claim.' },
  { n: '04', t: 'Belief', d: 'A pure function of the store at an as-of instant: tier, status, candidate, radius.' },
  { n: '05', t: 'Memory', d: 'A settled place can answer later queries — evidence-derived priors only.' },
  { n: '06', t: 'Effects', d: 'Promotion, widening, verification tasks — appended, never rewritten.' },
]

const SLOW_LOOP = [
  { n: '01', t: 'Buffer', d: 'New evidence accumulates without touching production behaviour.' },
  { n: '02', t: 'Quality filter', d: 'Duplicates, agent oddities and stale claims are identified, not used.' },
  { n: '03', t: 'Drift', d: 'Monitors watch whether the frozen policies still describe the field.' },
  { n: '04', t: 'Challenger', d: 'A candidate change is defined before it is scored.' },
  { n: '05', t: 'Validation', d: 'Held-out splits, temporal cuts, paired bootstrap; no evaluation-set tuning.' },
  { n: '06', t: 'Promotion', d: 'Only a cleared challenger replaces a frozen policy — with a new version and hash.' },
]

type DevPop = { key: string; name: string; hit_500: number; n: number; median_m: number; caption: string }

export function MethodPage() {
  const healthQ = useApi<HealthPayload>({ key: ['method-health'], live: health,
    fixtureKey: FIXTURES_ENABLED ? 'health' : undefined })
  const trustQ = useApi<MethodTrustPayload>({ key: ['method-trust'], live: methodTrust,
    fixtureKey: FIXTURES_ENABLED ? 'method-trust' : undefined })
  const trust = trustQ.data?.data
  // The development stand-in is fetched through a dynamic import that a production build never
  // enters, so no production code path can reach fixture data.
  const [devPops, setDevPops] = useState<DevPop[] | null>(null)
  const [devSource, setDevSource] = useState<string | null>(null)
  useEffect(() => {
    if (!FIXTURES_ENABLED) return
    let live = true
    import('../fixtures/demo').then((m) => {
      if (live) { setDevPops([...m.FROZEN_EVALUATION.populations] as DevPop[]); setDevSource(m.FROZEN_EVALUATION.source) }
    })
    return () => { live = false }
  }, [])
  const pops = (trust?.populations ?? (FIXTURES_ENABLED ? (devPops ?? []) : []))
    .map((p) => ({ key: p.key, name: p.name, n: p.n, median_m: p.median_m, caption: p.caption,
                   hit_500: 'hit_500m' in p ? (p as { hit_500m: number }).hit_500m : (p as { hit_500: number }).hit_500 }))

  return (
    <div className="grid" style={{ gap: 'var(--s4)' }}>
      <div className="grid cols-2">
        <Panel title="The claim this system makes">
          <p style={{ marginTop: 0, fontSize: 13, lineHeight: 1.55 }}>
            SUTRA resolves a messy address into a location <em>with a defensible uncertainty and a stated
            reason</em> — and it abstains when the evidence does not support serving one. Every answer in this
            console carries the decision, the visits behind it and a typed list of reasons. Nothing is asserted
            that the store cannot show.
          </p>
          <p style={{ fontSize: 12, color: 'var(--ink-soft)', lineHeight: 1.55 }}>
            Locations live on a <strong>local metric plane</strong> in metres — never latitude/longitude — and no
            third-party basemap or geocoder is consulted when an answer is produced. The unit of work is the
            place, not the account: memory is keyed by colocation, so no account identity ever maps to a location.
          </p>
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            <Chip mono tone="ghost">local metric plane, metres</Chip>
            <Chip mono tone="ghost">decisions are reproducible as of a date</Chip>
            <Chip mono tone="ghost">the record only ever grows</Chip>
          </div>
        </Panel>

        <Panel title="How an answer is produced" right={<span className="eyebrow">read from the service</span>}>
          {!trust ? <Skeleton lines={8} /> : (
            <div className="loop">
              {trust.how_it_works.map((s) => (
                <div className="loop-node" key={s.step}>
                  <div className="n">{String(s.step).padStart(2, '0')}</div>
                  <div className="t">{s.title}</div>
                  <div className="d">{s.detail}</div>
                </div>
              ))}
            </div>
          )}
        </Panel>
      </div>

      <Panel title="The learning loop" right={<span className="eyebrow">address → visit → evidence → belief → better answer</span>}>
        {!trust ? <Skeleton lines={2} /> : (
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
            {trust.learning_loop.map((step, i) => (
              <span key={step} style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                <Chip tone={i === trust.learning_loop.length - 1 ? 'pos' : 'ghost'}>{step}</Chip>
                {i < trust.learning_loop.length - 1 && <ArrowRight size={12} color="var(--ink-faint)" />}
              </span>
            ))}
          </div>
        )}
      </Panel>

      <div className="grid cols-2">
        <Panel title="Frozen evaluation — three populations, never merged"
          right={<span className="eyebrow">{trust?.evaluation_source ?? devSource ?? 'frozen evaluation receipts'}</span>}>
          {!pops.length ? <Skeleton lines={4} /> : (
            <>
              <div className="grid cols-3" style={{ gap: 'var(--s3)' }}>
                {pops.map((p) => (
                  <div className="eval-pop" key={p.key} style={{ padding: 0, borderLeftColor: p.key === 'warm' ? 'var(--pos)' : p.key === 'cold' ? 'var(--warn)' : 'var(--survey)' }}>
                    <div className="nm">{p.name}</div>
                    <div className="big">{(p.hit_500 * 100).toFixed(p.key === 'warm' ? 2 : 0)}<span style={{ fontSize: 14 }}> %</span></div>
                    <div className="cap">&lt; 500 m{p.n ? ` · n = ${p.n}` : ''} · median {p.median_m} m</div>
                  </div>
                ))}
              </div>
              <ul style={{ margin: 'var(--s3) 0 0', paddingLeft: 18, fontSize: 11.5, color: 'var(--ink-soft)', lineHeight: 1.6 }}>
                {pops.map((p) => <li key={p.key}>{p.caption}</li>)}
              </ul>
              {trust?.population_note && (
                <p style={{ fontSize: 11, color: 'var(--ink-faint)', marginBottom: 0 }}>{trust.population_note}</p>
              )}
              {trustQ.data?.fixture && (
                <p style={{ fontSize: 11, color: 'var(--warn)', marginBottom: 0 }}>
                  The live service is unreachable; these figures are the development stand-in, not a read.
                </p>
              )}
            </>
          )}
          <div className="banner refuse" style={{ marginTop: 'var(--s3)' }}>
            <AlertTriangle className="icon" size={14} color="var(--neg)" />
            <div style={{ fontSize: 11.5 }}>
              There is no 90 % cold-start claim in this project, and no single findability score. A number produced by
              dropping refusals from its own denominator would be dishonest, so one is never produced.
            </div>
          </div>
        </Panel>

        <Panel title="Safety rules the system enforces" right={<ShieldCheck size={13} color="var(--ink-faint)" />}>
          {!trust ? <Skeleton lines={6} /> : (
            <ul style={{ margin: 0, paddingLeft: 18, fontSize: 11.5, lineHeight: 1.7, color: 'var(--ink-soft)' }}>
              {trust.safety_rules.map((r) => <li key={r}>{r}</li>)}
            </ul>
          )}
        </Panel>
      </div>

      <div className="grid cols-2">
        <Panel title="Fast loop — every visit" right={<span className="eyebrow">runs on every request</span>}>
          <div className="loop">
            {FAST_LOOP.map((s) => (
              <div className="loop-node" key={s.n}>
                <div className="n">{s.n}</div>
                <div className="t">{s.t}</div>
                <div className="d">{s.d}</div>
              </div>
            ))}
          </div>
          <div style={{ marginTop: 10, fontSize: 11, color: 'var(--ink-faint)' }}>
            Belief is a pure calculation: the same store and the same as-of instant always produce the same answer,
            byte for byte. The stored row is a projection of that calculation, not the truth of it.
          </div>
        </Panel>

        <Panel title="Slow loop — learning without gambling" right={<span className="eyebrow">gated, pre-registered</span>}>
          <div className="loop">
            {SLOW_LOOP.map((s) => (
              <div className="loop-node slow" key={s.n}>
                <div className="n">{s.n}</div>
                <div className="t">{s.t}</div>
                <div className="d">{s.d}</div>
              </div>
            ))}
          </div>
          <div style={{ marginTop: 10, fontSize: 11, color: 'var(--ink-faint)' }}>
            A learned challenger was evaluated and <strong>not adopted</strong>: it did not beat the rule ranker on the
            frozen protocol. The production ranker is still rules, and that is recorded rather than quietly retried.
          </div>
        </Panel>
      </div>

      <div className="grid cols-2">
        <Panel title="What is implemented, and what is not" right={<ShieldCheck size={13} color="var(--ink-faint)" />}>
          {!trust ? <Skeleton lines={5} /> : (
            <>
              <p style={{ marginTop: 0, fontSize: 11.5, color: 'var(--ink-soft)' }}>{trust.development_note}</p>
              <div style={{ display: 'grid', gap: 12 }}>
                {trust.statuses.map((block) => (
                  <div key={block.label} style={{ display: 'grid', gap: 5 }}>
                    <Chip sm tone={block.label === 'IMPLEMENTED' ? 'pos' : block.label === 'NOT YET IMPLEMENTED' ? 'warn' : 'ghost'}>
                      {block.label}
                    </Chip>
                    <ul style={{ margin: 0, paddingLeft: 18, fontSize: 11.5, color: 'var(--ink-soft)', lineHeight: 1.55 }}>
                      {block.items.map((item) => <li key={item}>{item}</li>)}
                    </ul>
                  </div>
                ))}
                <div style={{ fontSize: 10.5, color: 'var(--ink-faint)' }}>
                  Labels are assembled by the service from its own capability map, not typed into this page.
                </div>
              </div>
            </>
          )}
        </Panel>

        <div className="col" style={{ gap: 'var(--s4)' }}>
          <Panel title="What we refuse to claim">
            <ul style={{ margin: 0, paddingLeft: 18, fontSize: 11.5, lineHeight: 1.65, color: 'var(--ink-soft)' }}>
              <li>No merged “overall accuracy”. The three evaluation populations stay separate.</li>
              <li>No confidence percentage anywhere in the product — tier, status, uncertainty and reasons instead.</li>
              <li>No rupee savings invented from the dataset; cost claims are third-party benchmarks only.</li>
              <li>No claim that field visits can be eliminated — only that unnecessary repeats can be targeted better.</li>
              <li>No latitude/longitude, no basemap, no external geography, ever.</li>
              <li>No negative observation may relocate a location: it widens and asks for verification.</li>
            </ul>
          </Panel>

          <Panel title="Where the detail lives" right={<BookOpen size={13} color="var(--ink-faint)" />}>
            <div style={{ display: 'grid', gap: 8, fontSize: 11.5 }}>
              <div>The contract the console renders is <span className="mono">SUTRA_FRONTEND_BACKEND_CONTRACT_V1_2026-10-08.md</span>, with the as-built record in its §21.</div>
              <div>These figures are read from <span className="mono">GET /v1/method-trust</span>, assembled from the frozen evaluation receipts.</div>
              <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 4 }}>
                <Link className="btn sm" to="/operations">Operations <ArrowRight size={12} /></Link>
                <Link className="btn sm" to="/queue">Verify queue</Link>
                <Link className="btn sm" to="/resolve">Workbench</Link>
                {healthQ.data?.data && <Chip sm mono>runtime {healthQ.data.data.versions.rules_version}</Chip>}
              </div>
            </div>
          </Panel>
        </div>
      </div>
    </div>
  )
}
