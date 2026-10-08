/** Small primitives. No component here knows anything about SUTRA's business rules. */
import type { ReactNode } from 'react'
import type { GateAction, CapabilityStatus, ReasonCode } from '../api/types'

export function Panel({ title, right, children, bodyClass, className }: {
  title?: ReactNode; right?: ReactNode; children: ReactNode; bodyClass?: string; className?: string
}) {
  return (
    <section className={`panel ${className || ''}`}>
      {title !== undefined && (
        <header className="panel-head">
          <h3>{title}</h3>
          {right && <div className="right">{right}</div>}
        </header>
      )}
      <div className={`panel-body ${bodyClass || ''}`}>{children}</div>
    </section>
  )
}

export function Label({ children }: { children: ReactNode }) { return <div className="eyebrow">{children}</div> }

export function KV({ items }: { items: [string, ReactNode][] }) {
  return (
    <dl className="kv">
      {items.map(([k, v]) => (<div key={k} style={{ display: 'contents' }}><dt>{k}</dt><dd>{v}</dd></div>))}
    </dl>
  )
}

export function Chip({ children, tone, mono, title, sm }: {
  children: ReactNode; tone?: 'pos' | 'neg' | 'warn' | 'info' | 'survey' | 'ghost'; mono?: boolean; title?: string; sm?: boolean
}) {
  return <span className={`chip ${tone || ''} ${mono ? 'mono' : ''} ${sm ? 'sm' : ''}`} title={title}>{children}</span>
}

export function GatePill({ action, reason }: { action: GateAction; reason?: string }) {
  const cls = action === 'SERVE' ? 'serve' : action === 'VERIFY_FIRST' ? 'verify' : 'refuse'
  return <span className={`pill ${cls}`} title={reason}><span className="dot" />{action.replace('_', ' ')}</span>
}

export function TierPill({ tier, status }: { tier: string; status: string }) {
  const tone = tier === 'CONFIRMED' ? 'pos' : tier === 'PROBABLE' ? 'info' : tier === 'APPROXIMATE' ? 'warn' : 'ghost'
  return (
    <span style={{ display: 'inline-flex', gap: 6, alignItems: 'center' }}>
      <Chip tone={tone as never} mono>{tier}</Chip>
      <Chip mono tone={status === 'MOVED_SUSPECTED' ? 'warn' : status === 'CONTESTED' ? 'neg' : 'ghost'}>{status}</Chip>
    </span>
  )
}

export function Figure({ value, caption, note, tone }: { value: ReactNode; caption: string; note?: ReactNode; tone?: 'serve' | 'warn' | 'neg' | 'survey' }) {
  return (
    <div className={`figure ${tone || ''}`}>
      <div className="k">{caption}</div>
      <div className="v">{value}</div>
      {note && <div className="n">{note}</div>}
    </div>
  )
}

/** Typed, backend-composed reasons. The label and the effect come from the service; nothing is parsed. */
export function WhyList({ codes, limit }: { codes: ReasonCode[]; limit?: number }) {
  const shown = limit ? codes.slice(0, limit) : codes
  if (!shown.length) return <div style={{ color: 'var(--ink-faint)', fontSize: 11.5 }}>no reason codes on this response</div>
  return (
    <div className="why">
      {shown.map((c, i) => (
        <div className="why-row" key={`${c.code}-${i}`}>
          <div>
            <div className="lab">{c.label}</div>
            <span className="code">{c.code}</span>
          </div>
          <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
            {c.effect !== null && c.effect !== undefined && (
              <span className="mono" style={{ color: c.effect >= 0 ? 'var(--pos)' : 'var(--neg)' }}>
                {c.effect >= 0 ? '+' : ''}{c.effect.toFixed(3)}
              </span>
            )}
            <Chip sm tone={c.direction === 'positive' ? 'pos' : c.direction === 'negative' ? 'neg' : 'ghost'}>{c.direction}</Chip>
          </div>
        </div>
      ))}
    </div>
  )
}

export function Skeleton({ lines = 4 }: { lines?: number }) {
  return <div aria-busy="true" aria-live="polite">{Array.from({ length: lines }).map((_, i) => <div key={i} className="skel line" style={{ width: `${92 - i * 9}%` }} />)}</div>
}

export function Empty({ title, hint, action }: { title: string; hint?: ReactNode; action?: ReactNode }) {
  return (
    <div className="empty">
      <div className="eyebrow">{title}</div>
      {hint && <div style={{ fontSize: 11.5, maxWidth: 380 }}>{hint}</div>}
      {action}
    </div>
  )
}

export function CapabilityTag({ status }: { status: CapabilityStatus }) {
  const text: Record<CapabilityStatus, string> = {
    implemented: 'implemented', designed: 'designed', not_implemented: 'not yet implemented',
    evaluated_not_adopted: 'evaluated · not adopted', research_only: 'research only',
  }
  return <span className={`status-tag ${status}`}>{text[status]}</span>
}

export function Num({ v, digits = 1, suffix }: { v: number | null | undefined; digits?: number; suffix?: string }) {
  if (v === null || v === undefined) return <span style={{ color: 'var(--ink-faint)' }}>—</span>
  return <span>{v.toFixed(digits)}{suffix ? <span style={{ fontSize: '0.68em', color: 'var(--ink-faint)' }}>{suffix}</span> : null}</span>
}

export function fmtTime(iso: string | null | undefined): string {
  if (!iso) return '—'
  return iso.replace('T', ' ').replace('Z', 'Z').slice(0, 19) + 'Z'
}
