/**
 * The local metric plane.
 *
 * Equal x/y scale in metres on `sutra_local_metric_plane:<town>`. No basemap, no tiles, no lat/lon —
 * the geometry comes from the service (`/v1/geometry/{address}` for the case, `/v1/plane/{town}` for
 * the reference backdrop) and this component only draws it.
 *
 * Negative observations arrive with `x`/`y` null and their position under
 * `metadata.captured_x/captured_y` with `coordinate_claim: false`: they are drawn as hollow,
 * dashed *captured positions* and never as a location claim. They also never contribute to the
 * uncertainty ring — the ring is drawn from the service's own authoritative ring.
 */
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import type { MapPayload, PlanePoint, TownPlanePayload } from '../api/types'

interface Props {
  geometry: MapPayload
  backdrop?: TownPlanePayload | null
  selectedCandidateId: string | null
  onSelectCandidate: (candidateId: string) => void
  onSelectObservation?: (observationId: string) => void
  height?: number
}

interface View { cx: number; cy: number; scale: number }

const PALETTE = {
  ink: '#22201D', survey: '#C4521E', pos: '#2F6B45', neg: '#9B2C2C', amb: '#8A6A15', warn: '#8A6A15',
  faint: '#7A736A', ref: '#C4BBAA', landmark: '#2F5B6B',
}

function isNegative(p: PlanePoint): boolean { return p.status === 'negative' || p.metadata?.coordinate_claim === false }
function markerPos(p: PlanePoint): { x: number; y: number } | null {
  if (typeof p.x === 'number' && typeof p.y === 'number') return { x: p.x, y: p.y }
  const cx = p.metadata?.captured_x, cy = p.metadata?.captured_y
  if (typeof cx === 'number' && typeof cy === 'number') return { x: cx, y: cy }
  return null
}

export function Plane({ geometry, backdrop, selectedCandidateId, onSelectCandidate, onSelectObservation, height = 460 }: Props) {
  const wrapRef = useRef<HTMLDivElement | null>(null)
  const [size, setSize] = useState({ w: 900, h: height })
  const [view, setView] = useState<View | null>(null)
  const [showBackdrop, setShowBackdrop] = useState(true)
  const [showObservations, setShowObservations] = useState(true)
  const [hover, setHover] = useState<string | null>(null)
  const drag = useRef<{ x: number; y: number; cx: number; cy: number } | null>(null)

  useEffect(() => {
    const el = wrapRef.current
    if (!el) return
    const ro = new ResizeObserver(() => setSize({ w: el.clientWidth, h: height }))
    ro.observe(el)
    setSize({ w: el.clientWidth, h: height })
    return () => ro.disconnect()
  }, [height])

  const candidates = useMemo(() => geometry.points.filter((p) => p.kind === 'candidate'), [geometry])
  const observations = useMemo(
    () => geometry.points.filter((p) => p.kind === 'observation' && markerPos(p)),
    [geometry],
  )

  const fit = useCallback((extent = geometry.extent) => {
    if (!extent) return
    const w = size.w, h = size.h
    const pad = 26
    const sx = (w - pad * 2) / Math.max(1, extent.x_max - extent.x_min)
    const sy = (h - pad * 2) / Math.max(1, extent.y_max - extent.y_min)
    const scale = Math.max(0.02, Math.min(sx, sy))
    setView({ cx: (extent.x_min + extent.x_max) / 2, cy: (extent.y_min + extent.y_max) / 2, scale })
  }, [geometry.extent, size.w, size.h])

  useEffect(() => { fit() }, [fit])

  useEffect(() => {
    const selected = candidates.find((c) => c.id === selectedCandidateId)
    if (!selected || !view) return
    const px = (selected.x - view.cx) * view.scale + size.w / 2
    const py = size.h / 2 - (selected.y - view.cy) * view.scale
    const m = 60
    if (px < m || px > size.w - m || py < m || py > size.h - m) {
      setView((v) => (v ? { ...v, cx: selected.x, cy: selected.y } : v))
    }
    // intentionally keyed on the selection only: panning must not fight the user
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedCandidateId])

  const v = view
  const toScreen = (x: number, y: number) => ({ sx: (x - v!.cx) * v!.scale + size.w / 2, sy: size.h / 2 - (y - v!.cy) * v!.scale })

  const onWheel = (e: React.WheelEvent) => {
    if (!v) return
    e.preventDefault()
    const rect = (e.currentTarget as SVGSVGElement).getBoundingClientRect()
    const mx = e.clientX - rect.left, my = e.clientY - rect.top
    const wx = (mx - size.w / 2) / v.scale + v.cx
    const wy = (size.h / 2 - my) / v.scale + v.cy
    const k = Math.exp(-e.deltaY * 0.0016)
    const scale = Math.max(0.02, Math.min(20, v.scale * k))
    const cx = wx - (mx - size.w / 2) / scale
    const cy = wy - (size.h / 2 - my) / scale
    setView({ cx, cy, scale })
  }
  const onDown = (e: React.PointerEvent) => {
    if (!v) return
    drag.current = { x: e.clientX, y: e.clientY, cx: v.cx, cy: v.cy }
    ;(e.currentTarget as SVGSVGElement).setPointerCapture(e.pointerId)
  }
  const onMove = (e: React.PointerEvent) => {
    if (!drag.current || !v) return
    const dx = e.clientX - drag.current.x, dy = e.clientY - drag.current.y
    setView({ ...v, cx: drag.current.cx - dx / v.scale, cy: drag.current.cy + dy / v.scale })
  }
  const onUp = () => { drag.current = null }
  const zoomBy = (k: number) => setView((cur) => (cur ? { ...cur, scale: Math.max(0.02, Math.min(20, cur.scale * k)) } : cur))

  if (!v) return <div className="plane-empty">preparing plane…</div>

  const grid = geometry.renderer_hint?.graticule_m || { minor: 10, major: 100 }
  const step = (() => {
    const target = 90 / v.scale // aim for a major line roughly every 90 px
    for (const s of [grid.minor, 50, grid.major, 500, 1000, 5000, 10000]) if (s >= target) return s
    return 20000
  })()

  const x0 = Math.floor((v.cx - size.w / 2 / v.scale) / step) * step
  const x1 = v.cx + size.w / 2 / v.scale
  const y0 = Math.floor((v.cy - size.h / 2 / v.scale) / step) * step
  const y1 = v.cy + size.h / 2 / v.scale
  const vlines: number[] = []
  for (let x = x0; x <= x1; x += step) vlines.push(x)
  const hlines: number[] = []
  for (let y = y0; y <= y1; y += step) hlines.push(y)

  const rings = geometry.rings.filter((r) => r.authoritative)
  const sel = candidates.find((c) => c.id === selectedCandidateId) || null
  const scaleBarM = (() => {
    const targetM = 90 / v.scale
    for (const s of [10, 25, 50, 100, 250, 500, 1000, 2000, 5000]) if (s >= targetM) return s
    return 10000
  })()

  return (
    <div className="plane-wrap" ref={wrapRef}>
      <div className="plane-toolbar">
        <span className="eyebrow">Local metric plane</span>
        <span className="mono" style={{ color: 'var(--ink-soft)' }}>{geometry.coordinate_space}</span>
        <ChipInline>{geometry.units}</ChipInline>
        <div className="right">
          <button className="btn sm" onClick={() => setShowBackdrop((s) => !s)} aria-pressed={showBackdrop}>Reference</button>
          <button className="btn sm" onClick={() => setShowObservations((s) => !s)} aria-pressed={showObservations}>Visits</button>
          <button className="btn sm" onClick={() => zoomBy(1.35)} aria-label="Zoom in">+</button>
          <button className="btn sm" onClick={() => zoomBy(1 / 1.35)} aria-label="Zoom out">−</button>
          <button className="btn sm" onClick={() => fit()}>Fit</button>
        </div>
      </div>

      <svg
        className="plane-svg" viewBox={`0 0 ${size.w} ${size.h}`} width={size.w} height={size.h} role="img"
        aria-label={`Local metric plane for ${geometry.address_id}, ${geometry.points.length} objects`}
        onWheel={onWheel} onPointerDown={onDown} onPointerMove={onMove} onPointerUp={onUp} onPointerCancel={onUp}
        onDoubleClick={() => zoomBy(1.7)}
      >
        {/* graticule */}
        <g>
          {vlines.map((x) => {
            const { sx } = toScreen(x, 0)
            const major = Math.abs(x % (grid.major * Math.max(1, step / grid.major))) < 1e-6 && step >= grid.major
            return <line key={`vx${x}`} className={major ? 'plane-grid-major' : 'plane-grid-minor'} x1={sx} y1={0} x2={sx} y2={size.h} />
          })}
          {hlines.map((y) => {
            const { sy } = toScreen(0, y)
            const major = Math.abs(y % (grid.major * Math.max(1, step / grid.major))) < 1e-6 && step >= grid.major
            return <line key={`hy${y}`} className={major ? 'plane-grid-major' : 'plane-grid-minor'} x1={0} y1={sy} x2={size.w} y2={sy} />
          })}
          {(() => { const { sx, sy } = toScreen(0, 0); return <>
            <line className="plane-axis" x1={sx} y1={0} x2={sx} y2={size.h} />
            <line className="plane-axis" x1={0} y1={sy} x2={size.w} y2={sy} />
          </> })()}
        </g>

        {/* reference backdrop: official localities and landmarks */}
        {showBackdrop && backdrop && (
          <g>
            {backdrop.points.map((p) => {
              const { sx, sy } = toScreen(p.x, p.y)
              if (sx < -20 || sx > size.w + 20 || sy < -20 || sy > size.h + 20) return null
              return p.kind === 'locality'
                ? <g key={p.id}><rect className="pt-reference" x={sx - 2.4} y={sy - 2.4} width={4.8} height={4.8} rx={0.8} />
                    <text className="plane-label" x={sx + 6} y={sy + 3}>{p.name}</text></g>
                : <circle key={p.id} className="pt-landmark" cx={sx} cy={sy} r={1.7} />
            })}
            {(() => { const { sx, sy } = toScreen(backdrop.town_centroid.x, backdrop.town_centroid.y)
              return <g><circle cx={sx} cy={sy} r={3.4} fill="none" stroke={PALETTE.faint} strokeWidth={1} strokeDasharray="2 2" />
                <text className="plane-label" x={sx + 6} y={sy - 5}>town centroid</text></g> })()}
          </g>
        )}

        {/* uncertainty rings — authoritative ring from the service only */}
        <g>
          {rings.map((r) => {
            const { sx, sy } = toScreen(r.center_x, r.center_y)
            const selRing = r.candidate_id === selectedCandidateId
            return (
              <g key={r.candidate_id} opacity={selRing ? 1 : 0.55}>
                <circle className={`plane-ring ${r.widened ? 'widened' : ''}`} cx={sx} cy={sy} r={r.radius_m * v.scale}
                  strokeWidth={selRing ? 1.6 : 1} />
                {selRing && (
                  <text className="plane-label sel" x={sx + 4} y={sy - r.radius_m * v.scale - 4}>
                    ±{Math.round(r.radius_m)} m · {r.basis}{r.widened ? ' · widened' : ''}
                  </text>
                )}
              </g>
            )
          })}
        </g>

        {/* visits: positives/ambiguous are claims, negatives are captured positions (non-claims) */}
        {showObservations && (
          <g>
            {observations.map((o) => {
              const pos = markerPos(o)!
              const { sx, sy } = toScreen(pos.x, pos.y)
              const neg = isNegative(o)
              const cls = neg ? 'neg' : o.status === 'positive' ? 'pos' : 'amb'
              const active = hover === o.id
              return (
                <g key={o.id} onMouseEnter={() => setHover(o.id)} onMouseLeave={() => setHover(null)}
                  onClick={(e) => { e.stopPropagation(); onSelectObservation?.(o.id) }} style={{ cursor: 'pointer' }}>
                  {neg
                    ? <circle className="pt-observation neg" cx={sx} cy={sy} r={5} strokeDasharray="1.6 1.6" />
                    : <circle className={`pt-observation ${cls}`} cx={sx} cy={sy} r={4.2} />}
                  <line x1={sx - 7} y1={sy} x2={sx - 2.4} y2={sy} stroke={PALETTE[cls as 'pos' | 'neg' | 'amb']} strokeWidth={0.8} opacity={0.6} />
                  <line x1={sx + 2.4} y1={sy} x2={sx + 7} y2={sy} stroke={PALETTE[cls as 'pos' | 'neg' | 'amb']} strokeWidth={0.8} opacity={0.6} />
                  {(active || neg) && (
                    <text className="plane-label" x={sx + 9} y={sy + 3}>
                      {neg ? `${o.id} · captured, no claim` : `${o.id} · ${o.metadata?.outcome || o.status}`}
                    </text>
                  )}
                </g>
              )
            })}
          </g>
        )}

        {/* candidates */}
        <g>
          {candidates.map((c) => {
            const { sx, sy } = toScreen(c.x, c.y)
            const isSel = c.id === selectedCandidateId
            const active = hover === c.id
            return (
              <g key={c.id} onMouseEnter={() => setHover(c.id)} onMouseLeave={() => setHover(null)}
                onClick={(e) => { e.stopPropagation(); onSelectCandidate(c.id) }} style={{ cursor: 'pointer' }}>
                {isSel && <circle className="plane-sel" cx={sx} cy={sy} r={9.5} />}
                <circle className={`pt-candidate ${isSel ? 'sel' : ''}`} cx={sx} cy={sy} r={isSel ? 4.6 : 3.6} />
                {(isSel || active) && (
                  <text className={`plane-label ${isSel ? 'sel' : ''}`} x={sx + 11} y={sy - 7}>
                    {c.source || 'candidate'}{c.granularity ? ` · ${c.granularity}` : ''}
                  </text>
                )}
                {(isSel || active) && (
                  <text className="plane-label" x={sx + 11} y={sy + 4}>{c.id}</text>
                )}
              </g>
            )
          })}
        </g>
      </svg>

      <div className="plane-hint">drag to pan · wheel to zoom · double-click to zoom in</div>
      <div className="plane-scale">
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, justifyContent: 'flex-end' }}>
          <div style={{ width: Math.round(scaleBarM * v.scale), height: 6, borderLeft: `1px solid ${PALETTE.faint}`, borderRight: `1px solid ${PALETTE.faint}`, borderBottom: `1px solid ${PALETTE.faint}` }} />
          <span>{scaleBarM >= 1000 ? `${scaleBarM / 1000} km` : `${scaleBarM} m`}</span>
        </div>
        <div>scale 1 : {Math.round(1 / v.scale)} (approx)</div>
      </div>

      <div className="readout">
        {sel ? (
          <>
            <div><div className="cap">selected candidate</div><div className="fig">{sel.source}</div></div>
            <div><div className="cap">x</div><div className="fig">{sel.x.toFixed(1)}<span style={{ fontSize: 11, color: 'var(--ink-faint)' }}> m</span></div></div>
            <div><div className="cap">y</div><div className="fig">{sel.y.toFixed(1)}<span style={{ fontSize: 11, color: 'var(--ink-faint)' }}> m</span></div></div>
            <div><div className="cap">granularity</div><div className="fig" style={{ fontSize: 15 }}>{sel.granularity || '—'}</div></div>
          </>
        ) : (
          <div><div className="cap">plane</div><div className="fig" style={{ fontSize: 15 }}>no selected candidate</div></div>
        )}
        <div className="space">{geometry.coordinate_space} · metres</div>
      </div>
    </div>
  )
}

function ChipInline({ children }: { children: React.ReactNode }) {
  return <span className="chip sm ghost" style={{ fontFamily: 'var(--font-mono)' }}>{children}</span>
}
