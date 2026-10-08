/* ------------------------------------------------------------------ *
 * LocalPlaneMap — instrument-grade SVG map on the local metric plane.
 * Pure metres, monospaced survey labels, drag-pan + wheel-zoom,
 * click-to-select candidates, uncertainty rings, evidence traces.
 *
 * The geometry is the service's: `/v1/plane/{town}` for reference points
 * (localities, official landmarks) and `/v1/geometry/{address_id}` for
 * candidates, the uncertainty ring and traces. No lat/lng, no tiles, no
 * basemap, no external geography — and when an answer is withheld the
 * plane renders no coordinate at all.
 * ------------------------------------------------------------------ */

import { useEffect, useMemo, useRef, useState } from "react";
import { Maximize2, Minus, Plus, ShieldAlert } from "lucide-react";
import type { AddressGeometry, LocalPoint, PlanePoint, TownPlane } from "@/lib/types";
import { C, cn, extent, fmtCoord, fmtM } from "@/lib/utils";
import { toneColor } from "./u";

export interface MapProps {
  /** Reference geometry for the town (localities + official landmarks). */
  plane?: TownPlane | null;
  /** Address-scoped geometry (candidates, uncertainty ring, traces). */
  geometry?: AddressGeometry | null;
  focus?: LocalPoint | null;
  selectedId?: string | null;
  onSelect?: (id: string) => void;
  compact?: boolean;
  className?: string;
  fitKey?: string;
}

interface View {
  cx: number;
  cy: number;
  ppm: number; // pixels per metre
}

const GRID_STEPS = [10, 20, 50, 100, 200, 500, 1000];
const SCALE_STEPS = [2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000];
const MONO = "'IBM Plex Mono', monospace";

function niceGrid(ppm: number) {
  for (const s of GRID_STEPS) if (s * ppm >= 52) return s;
  return 1000;
}

/** Landmark glyph families, keyed by the official landmark_type the service sends. */
function glyphFamily(t: string | null | undefined): "temple" | "faith" | "school" | "stop" | "shop" | "civic" | "tank" | "park" | "dot" {
  switch (t) {
    case "hanuman_temple":
    case "ganesha_temple":
      return "temple";
    case "masjid":
    case "church":
      return "faith";
    case "govt_school":
      return "school";
    case "bus_stop":
      return "stop";
    case "medical_store":
    case "ration_shop":
    case "milk_dairy":
    case "petrol_bunk":
      return "shop";
    case "post_office":
    case "community_hall":
      return "civic";
    case "water_tank":
      return "tank";
    case "park":
      return "park";
    default:
      return "dot";
  }
}

export default function LocalPlaneMap(props: MapProps) {
  const { compact, plane, geometry } = props;
  const wrapRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<SVGSVGElement>(null);
  const [size, setSize] = useState({ w: 820, h: 520 });
  const [view, setView] = useState<View>({ cx: props.focus?.x ?? 0, cy: props.focus?.y ?? 0, ppm: 0.55 });
  const [hover, setHover] = useState<LocalPoint | null>(null);
  const drag = useRef<{ sx: number; sy: number; cx: number; cy: number; moved: boolean } | null>(null);

  const withheld = geometry?.withheld ?? null;
  const candidates = useMemo(
    () => (withheld ? [] : (geometry?.points || []).filter((p) => p.kind === "candidate")),
    [geometry, withheld],
  );
  const rings = useMemo(() => (withheld ? [] : geometry?.rings || []), [geometry, withheld]);
  const traces = useMemo(() => (withheld ? [] : geometry?.traces || []), [geometry, withheld]);
  const refPoints = useMemo(
    () => (plane?.points || []).filter((p) => p.kind === "locality" || p.kind === "landmark"),
    [plane],
  );

  /* ------- measure ------- */
  useEffect(() => {
    if (!wrapRef.current) return;
    const ro = new ResizeObserver((es) => {
      const r = es[0].contentRect;
      setSize({ w: Math.max(120, r.width), h: Math.max(120, r.height) });
    });
    ro.observe(wrapRef.current);
    return () => ro.disconnect();
  }, []);

  /* ------- fit: the service's own extent first, else the points ------- */
  const fit = useMemo(() => {
    return () => {
      const w = size.w, h = size.h;
      const pts: LocalPoint[] = [];
      candidates.forEach((c) => pts.push({ x: c.x, y: c.y }));
      rings.forEach((r) => { pts.push({ x: r.center_x - r.radius_m, y: r.center_y }); pts.push({ x: r.center_x + r.radius_m, y: r.center_y }); });
      traces.forEach((t) => (t.points || []).forEach((p) => pts.push(p)));
      if (props.focus) pts.push(props.focus);
      const e =
        geometry?.extent && pts.length
          ? { minX: geometry.extent.x_min, minY: geometry.extent.y_min, maxX: geometry.extent.x_max, maxY: geometry.extent.y_max }
          : plane?.extent && !pts.length
            ? { minX: plane.extent.x_min, minY: plane.extent.y_min, maxX: plane.extent.x_max, maxY: plane.extent.y_max }
            : pts.length
              ? extent(pts)
              : { minX: -500, minY: -500, maxX: 500, maxY: 500 };
      const pad = pts.length && !geometry?.extent ? 90 : 0;
      const spanX = Math.max(80, e.maxX - e.minX + pad * 2);
      const spanY = Math.max(60, e.maxY - e.minY + pad * 2 + 60);
      const ppm = Math.min(w / spanX, h / spanY);
      return { cx: (e.minX + e.maxX) / 2, cy: (e.minY + e.maxY) / 2 + 20, ppm };
    };
  }, [size, geometry, plane, candidates, rings, traces, props.focus]);

  useEffect(() => {
    setView(fit());
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [props.fitKey, size.w, size.h]);

  /* ------- projections ------- */
  const X = (x: number) => (x - view.cx) * view.ppm + size.w / 2;
  const Y = (y: number) => size.h / 2 - (y - view.cy) * view.ppm;
  const px = (p: LocalPoint) => `${X(p.x).toFixed(1)},${Y(p.y).toFixed(1)}`;
  const pathOf = (pts: LocalPoint[]) => pts.map(px).join(" ");

  /* ------- wheel zoom (native, non-passive) ------- */
  useEffect(() => {
    const el = svgRef.current;
    if (!el) return;
    const onWheel = (e: WheelEvent) => {
      e.preventDefault();
      const r = el.getBoundingClientRect();
      const mx = e.clientX - r.left, my = e.clientY - r.top;
      setView((v) => {
        const f = e.deltaY < 0 ? 1.18 : 1 / 1.18;
        const ppm = Math.min(9, Math.max(0.05, v.ppm * f));
        const mxM = v.cx + (mx - r.width / 2) / v.ppm;
        const myM = v.cy - (my - r.height / 2) / v.ppm;
        return {
          ppm,
          cx: mxM - (mx - r.width / 2) / ppm,
          cy: myM + (my - r.height / 2) / ppm,
        };
      });
    };
    el.addEventListener("wheel", onWheel, { passive: false });
    return () => el.removeEventListener("wheel", onWheel);
  }, []);

  /* ------- drag pan ------- */
  const onPointerDown = (e: React.PointerEvent<SVGSVGElement>) => {
    (e.target as Element).setPointerCapture?.(e.pointerId);
    drag.current = { sx: e.clientX, sy: e.clientY, cx: view.cx, cy: view.cy, moved: false };
  };
  const onPointerMove = (e: React.PointerEvent<SVGSVGElement>) => {
    const r = svgRef.current!.getBoundingClientRect();
    const pxX = e.clientX - r.left, pxY = e.clientY - r.top;
    if (drag.current) {
      const d = drag.current;
      if (Math.abs(e.clientX - d.sx) + Math.abs(e.clientY - d.sy) > 4) d.moved = true;
      setView((v) => ({ ...v, cx: d.cx - (e.clientX - d.sx) / v.ppm, cy: d.cy + (e.clientY - d.sy) / v.ppm }));
    } else {
      setHover({
        x: view.cx + (pxX - size.w / 2) / view.ppm,
        y: view.cy - (pxY - size.h / 2) / view.ppm,
      });
    }
  };
  const onPointerUp = () => {
    window.setTimeout(() => { drag.current = null; }, 0);
  };

  const zoom = (f: number) =>
    setView((v) => ({ ...v, ppm: Math.min(9, Math.max(0.05, v.ppm * f)) }));

  /* ------- derived ------- */
  const step = niceGrid(view.ppm);
  const halfW = size.w / 2 / view.ppm;
  const halfH = size.h / 2 / view.ppm;
  const gx0 = Math.floor((view.cx - halfW) / step) * step;
  const gy0 = Math.floor((view.cy - halfH) / step) * step;
  const gridX: number[] = [];
  const gridY: number[] = [];
  for (let x = gx0; x <= view.cx + halfW; x += step) gridX.push(x);
  for (let y = gy0; y <= view.cy + halfH; y += step) gridY.push(y);

  let scaleLen = SCALE_STEPS[SCALE_STEPS.length - 1];
  for (const s of SCALE_STEPS) if (s * view.ppm <= 128) scaleLen = s;

  const landmarkGlyph = (p: PlanePoint) => {
    const x = X(p.x), y = Y(p.y);
    const s = 4.2;
    switch (glyphFamily(p.landmark_type)) {
      case "temple":
        return <path d={`M${x},${y - s} L${x + s},${y + s * 0.8} L${x - s},${y + s * 0.8} Z`} fill="none" stroke={C.ink2} strokeWidth={1.1} />;
      case "faith":
        return (<g stroke={C.ink2} strokeWidth={1.1} fill="none">
          <path d={`M${x},${y - s} V${y + s} M${x - s * 0.8},${y - s * 0.3} H${x + s * 0.8}`} />
        </g>);
      case "school":
        return <rect x={x - s * 0.8} y={y - s * 0.8} width={s * 1.6} height={s * 1.6} fill="none" stroke={C.ink2} strokeWidth={1.1} />;
      case "stop":
        return (<g stroke={C.ink2} strokeWidth={1.1} fill="none">
          <circle cx={x} cy={y - s * 0.6} r={s * 0.55} /><path d={`M${x},${y} V${y + s}`} />
        </g>);
      case "shop":
        return (<g stroke={C.ink2} strokeWidth={1.1} fill="none">
          <rect x={x - s} y={y - s * 0.7} width={s * 2} height={s * 1.3} />
        </g>);
      case "civic":
        return (<g stroke={C.ink2} strokeWidth={1.1} fill="none">
          <path d={`M${x - s},${y + s * 0.7} H${x + s} M${x - s * 0.7},${y + s * 0.7} V${y - s * 0.3} M${x + s * 0.7},${y + s * 0.7} V${y - s * 0.3} M${x - s},${y - s * 0.3} H${x + s} L${x},${y - s}`} />
        </g>);
      case "tank":
        return (<g stroke={C.ink2} strokeWidth={1.1} fill="none">
          <circle cx={x} cy={y - 1.5} r={s * 0.75} />
          <path d={`M${x - s},${y + s * 0.9} H${x + s} M${x - s * 0.5},${y + s * 0.9} V${y + 0.5} M${x + s * 0.5},${y + s * 0.9} V${y + 0.5}`} />
        </g>);
      case "park":
        return (<g stroke={C.ink2} strokeWidth={1.1} fill="none">
          <circle cx={x} cy={y - s * 0.3} r={s * 0.7} /><path d={`M${x},${y + s * 0.4} V${y + s}`} />
        </g>);
      default:
        return <circle cx={x} cy={y} r={2.2} fill={C.ink2} />;
    }
  };

  const sel = props.selectedId;

  return (
    <div ref={wrapRef} className={cn("relative overflow-hidden bg-raised border hairline no-select", props.className)}>
      <svg
        ref={svgRef}
        width={size.w}
        height={size.h}
        className={cn("block", drag.current?.moved ? "cursor-grabbing" : "xh")}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerLeave={() => { setHover(null); drag.current = null; }}
      >
        <rect x={0} y={0} width={size.w} height={size.h} fill={C.raised} />

        {/* survey grid */}
        <g>
          {gridY.map((gy) => (
            <line key={`gy${gy}`} x1={0} x2={size.w} y1={Y(gy)} y2={Y(gy)}
              stroke={gy % (step * 5) === 0 ? C.line2 : C.line} strokeWidth={gy % (step * 5) === 0 ? 0.9 : 0.5} />
          ))}
          {gridX.map((gx) => (
            <line key={`gx${gx}`} y1={0} y2={size.h} x1={X(gx)} x2={X(gx)}
              stroke={gx % (step * 5) === 0 ? C.line2 : C.line} strokeWidth={gx % (step * 5) === 0 ? 0.9 : 0.5} />
          ))}
          {!compact && gridX.filter((_, i) => i % 2 === 0).map((gx) => (
            <text key={`tx${gx}`} x={X(gx) + 3} y={12} fontSize={8.5} fill={C.faint} fontFamily={MONO} letterSpacing={0.5}>
              E{fmtCoord(gx, 0)}
            </text>
          ))}
          {!compact && gridY.filter((_, i) => i % 2 === 0).map((gy) => (
            <text key={`ty${gy}`} x={4} y={Y(gy) - 3} fontSize={8.5} fill={C.faint} fontFamily={MONO} letterSpacing={0.5}>
              N{fmtCoord(gy, 0)}
            </text>
          ))}
        </g>

        {/* localities (reference) */}
        {refPoints.filter((p) => p.kind === "locality").map((p) => (
          <g key={p.id}>
            <circle cx={X(p.x)} cy={Y(p.y)} r={7} fill="none" stroke={C.line3} strokeWidth={1} strokeDasharray="2 2" />
            {!compact && (
              <text x={X(p.x) + 10} y={Y(p.y) + 3} fontSize={8.8} fontFamily={MONO} fill={C.mute} letterSpacing={0.5}
                style={{ paintOrder: "stroke" }} stroke={C.raised} strokeWidth={3}>
                {p.name?.toUpperCase()}
              </text>
            )}
          </g>
        ))}

        {/* official landmarks (reference) */}
        {refPoints.filter((p) => p.kind === "landmark").map((p) => (
          <g key={p.id}>
            {landmarkGlyph(p)}
            {!compact && view.ppm > 0.28 && (
              <text x={X(p.x) + 8} y={Y(p.y) + 3} fontSize={8.4} fontFamily={MONO} fill={C.ink2} letterSpacing={0.4}
                style={{ paintOrder: "stroke" }} stroke={C.raised} strokeWidth={3}>
                {p.name?.toUpperCase()}
              </text>
            )}
          </g>
        ))}

        {/* evidence traces (real, usually empty until a device syncs a walk-in) */}
        {traces.map((t, i) => {
          const pts = (t.points || []) as LocalPoint[];
          if (pts.length < 2) return null;
          const tone = toneColor("cool");
          const start = pts[0], end = pts[pts.length - 1];
          return (
            <g key={t.observation_id || i}>
              <polyline points={pathOf(pts)} fill="none" stroke={tone} strokeWidth={1.5} strokeDasharray="4 3" strokeLinejoin="round" opacity={0.9} />
              {pts.map((p, j) => <circle key={j} cx={X(p.x)} cy={Y(p.y)} r={1.3} fill={tone} />)}
              <rect x={X(start.x) - 3} y={Y(start.y) - 3} width={6} height={6} fill="none" stroke={tone} strokeWidth={1.2} />
              <circle cx={X(end.x)} cy={Y(end.y)} r={3.2} fill={tone} stroke={C.raised} strokeWidth={1.2} />
            </g>
          );
        })}

        {/* the service's uncertainty ring(s) — every ring carries its number */}
        {rings.map((r, i) => (
          <g key={`${r.candidate_id || "ring"}-${i}`}>
            <ellipse cx={X(r.center_x)} cy={Y(r.center_y)}
              rx={Math.max(7, r.radius_m * view.ppm)} ry={Math.max(7, r.radius_m * view.ppm * 0.78)}
              fill={C.accent} fillOpacity={0.05} stroke={C.accent} strokeWidth={1.3} strokeDasharray="5 3"
              className="marching" />
            {!compact && (
              <text x={X(r.center_x) + 12} y={Y(r.center_y) - 10} fontSize={8.6} fontFamily={MONO}
                fill={C.accentDeep} fontWeight={600} style={{ paintOrder: "stroke" }} stroke={C.raised} strokeWidth={3.4}>
                {`radius ${fmtM(r.radius_m, 1)} · ${r.basis || ""}${r.widened ? " · widened" : ""}`}
              </text>
            )}
          </g>
        ))}

        {/* candidates */}
        {candidates.map((c) => {
          const x = X(c.x), y = Y(c.y);
          const active = sel === c.id;
          return (
            <g key={c.id} onClick={(e) => { if (!drag.current?.moved) { e.stopPropagation(); props.onSelect?.(c.id); } }}
              className="cursor-pointer">
              {active && <circle cx={x} cy={y} r={13} fill="none" stroke={C.accent} strokeWidth={1.2} />}
              <circle cx={x} cy={y} r={8} fill={active ? C.accentSoft : C.raised} stroke={active ? C.accentDeep : C.ink} strokeWidth={active ? 1.5 : 1.2} />
              <text x={x} y={y + 3.2} textAnchor="middle" fontSize={9} fontFamily={MONO} fontWeight={600}
                fill={active ? C.accentDeep : C.ink} pointerEvents="none">
                {c.granularity === "rooftop" ? "R" : c.granularity === "street" ? "S" : "L"}
              </text>
              <text x={x} y={y + 26} textAnchor="middle" fontSize={8.6} fontFamily={MONO} fontWeight={600}
                fill={active ? C.accentDeep : C.ink2} pointerEvents="none"
                style={{ paintOrder: "stroke" }} stroke={C.raised} strokeWidth={3.4}>
                {typeof c.score === "number" ? c.score.toFixed(2) : (c.source ?? "·")}
              </text>
            </g>
          );
        })}

        {/* frame */}
        <rect x={0.5} y={0.5} width={size.w - 1} height={size.h - 1} fill="none" stroke={C.line2} strokeWidth={1} pointerEvents="none" />
      </svg>

      {/* withheld answers render no coordinate at all */}
      {withheld && (
        <div className="absolute inset-x-6 top-1/2 -translate-y-1/2 border border-crit/50 bg-crit-soft/90 px-3 py-3" data-testid="plane-withheld">
          <div className="flex items-center gap-1.5 mono text-[9.5px] uppercase tracking-[0.12em] text-crit font-semibold">
            <ShieldAlert size={12} /> answer withheld — no coordinate on the plane
          </div>
          <div className="mono text-[10px] text-ink2 mt-1 leading-relaxed">
            {[withheld.reason, withheld.gate_reason].filter(Boolean).join(" · ") || "the gate refused this request"}
            {withheld.suppressed ? <> — suppressed {withheld.suppressed.candidate_points ?? 0} candidate points, {withheld.suppressed.rings ?? 0} ring</> : null}
          </div>
        </div>
      )}

      {/* readout */}
      <div className="absolute left-2 top-2 border hairline bg-raised/95 px-2 py-1">
        <div className="mono text-[8.5px] tracking-[0.14em] text-faint uppercase">
          {geometry?.coordinate_space || plane?.coordinate_space || "local metric plane"} · metres · N↑
        </div>
        <div className="mono text-[10.5px] text-ink mt-px">
          E {fmtCoord(hover?.x ?? view.cx)}&nbsp;&nbsp;N {fmtCoord(hover?.y ?? view.cy)}
          <span className="text-faint"> · grid {step} m</span>
        </div>
      </div>

      {/* zoom controls */}
      {!compact && (
        <div className="absolute right-2 top-2 flex flex-col border hairline bg-raised">
          <button onClick={() => zoom(1.4)} className="p-1.5 text-ink2 hover:bg-accent-faint hover:text-accent-deep border-b hairline" title="Zoom in" aria-label="Zoom in">
            <Plus size={13} strokeWidth={1.8} />
          </button>
          <button onClick={() => zoom(1 / 1.4)} className="p-1.5 text-ink2 hover:bg-accent-faint hover:text-accent-deep border-b hairline" title="Zoom out" aria-label="Zoom out">
            <Minus size={13} strokeWidth={1.8} />
          </button>
          <button onClick={() => setView(fit())} className="p-1.5 text-ink2 hover:bg-accent-faint hover:text-accent-deep" title="Fit content" aria-label="Fit content">
            <Maximize2 size={13} strokeWidth={1.8} />
          </button>
        </div>
      )}

      {/* scale bar */}
      <div className="absolute left-2 bottom-2 border hairline bg-raised/95 px-2 py-1">
        <div className="flex items-end gap-2">
          <svg width={scaleLen * view.ppm + 8} height={10}>
            <path d={`M4,9 V4 H${4 + scaleLen * view.ppm} V9`} fill="none" stroke={C.ink} strokeWidth={1.1} />
            <path d={`M${4 + scaleLen * view.ppm / 2},9 V6`} stroke={C.ink} strokeWidth={1} />
          </svg>
          <span className="mono text-[9.5px] text-ink">0 — {fmtM(scaleLen, 0)}</span>
        </div>
      </div>

      {/* north arrow */}
      <div className="absolute right-2 bottom-2 flex flex-col items-center border hairline bg-raised/95 px-1.5 py-1">
        <svg width={14} height={18}>
          <path d="M7,1 L11,13 L7,10 L3,13 Z" fill={C.ink} />
        </svg>
        <span className="mono text-[8.5px] text-ink -mt-px">N</span>
      </div>
    </div>
  );
}
