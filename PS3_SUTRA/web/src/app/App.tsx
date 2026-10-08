import { useState } from 'react'
import { HashRouter, NavLink, Route, Routes, useLocation } from 'react-router-dom'
import { Menu } from 'lucide-react'
import { OperationsPage } from '../pages/Operations'
import { ResolvePage } from '../pages/Resolve'
import { PlacesPage } from '../pages/Places'
import { EvidencePage } from '../pages/Evidence'
import { QueuePage } from '../pages/Queue'
import { MethodPage } from '../pages/Method'
import { useApp } from '../state/appState'
import { ASOF_MOMENT } from '../config/product'

const NAV = [
  { to: '/', idx: '01', label: 'Operations', el: <OperationsPage />, sub: 'runtime, store, packs, frozen evaluation' },
  { to: '/resolve', idx: '02', label: 'Resolve', el: <ResolvePage />, sub: 'workbench · candidates · plane · decision ticket' },
  { to: '/places', idx: '03', label: 'Places', el: <PlacesPage />, sub: 'durable place objects, versions, contradictions' },
  { to: '/evidence', idx: '04', label: 'Evidence', el: <EvidencePage />, sub: 'visit timeline channel by channel' },
  { to: '/queue', idx: '05', label: 'Verify Queue', el: <QueuePage />, sub: 'open verification demand (read-only)' },
  { to: '/method', idx: '06', label: 'Method & Trust', el: <MethodPage />, sub: 'how the answer is made and what is not claimed' },
]

function Shell() {
  const { asOf, setAsOf, purpose, source, apiReachable } = useApp()
  const [open, setOpen] = useState(false)
  const loc = useLocation()
  const current = NAV.find((n) => (n.to === '/' ? loc.pathname === '/' : loc.pathname.startsWith(n.to)))
  const live = source === 'live' && apiReachable !== false

  return (
    <div className="shell">
      <aside className={`rail ${open ? 'open' : ''}`}>
        <div className="rail-brand">
          <div className="rail-mark"><h1>SUTRA</h1><span>v1.0</span></div>
          <div className="rail-tag">Address resolution workstation · CreditNirvana field intelligence</div>
        </div>
        <nav className="rail-nav" onClick={() => setOpen(false)}>
          {NAV.map((n) => (
            <NavLink key={n.to} to={n.to} end={n.to === '/'}>
              <span className="idx">{n.idx}</span>{n.label}
            </NavLink>
          ))}
        </nav>
        <div className="rail-foot">
          <div className="row"><span>API</span><span className="v" style={{ color: live ? 'var(--pos)' : 'var(--warn)' }}>{live ? 'live' : 'captured'}</span></div>
          <div className="row"><span>purpose</span><span className="v">{purpose.replace(/_/g, ' ').toLowerCase()}</span></div>
          <div className="row"><span>as of</span><span className="v">{asOf.slice(0, 10)}</span></div>
          <div style={{ fontSize: 9.5, lineHeight: 1.4 }}>
            coordinates are local metric metres.<br />no lat/lon, no basemap, no external geography.
          </div>
        </div>
      </aside>
      {open && <div className="scrim" onClick={() => setOpen(false)} />}

      <div className="main">
        <header className="topbar">
          <button className="btn sm rail-toggle" onClick={() => setOpen((o) => !o)} aria-label="Toggle navigation"><Menu size={14} /></button>
          <div>
            <h2>{current?.label || 'SUTRA'}</h2>
            <div className="sub">{current?.sub}</div>
          </div>
          <div className="right">
            <span className={`chip ${live ? 'pos' : 'warn'}`} title={live ? 'The API answered this session' : 'The API was unreachable; captured responses are in use'}>
              {live ? 'live runtime' : 'captured data'}
            </span>
            <label className="chip mono ghost" style={{ gap: 6 }}>
              as of
              <input value={asOf} onChange={(e) => setAsOf(e.target.value)} spellCheck={false}
                style={{ border: 0, background: 'transparent', fontFamily: 'var(--font-mono)', fontSize: 10.5, width: 168, color: 'var(--ink)' }} />
            </label>
            {asOf !== ASOF_MOMENT && <button className="btn sm" onClick={() => setAsOf(ASOF_MOMENT)}>reset</button>}
          </div>
        </header>
        <main className="view">
          <Routes>
            {NAV.map((n) => <Route key={n.to} path={n.to} element={n.el} />)}
            <Route path="*" element={<OperationsPage />} />
          </Routes>
        </main>
      </div>
    </div>
  )
}

export function App() {
  return (
    <HashRouter>
      <Shell />
    </HashRouter>
  )
}
