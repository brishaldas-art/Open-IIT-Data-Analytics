/* ------------------------------------------------------------------ *
 * LocalPlaneMap — instrument-grade SVG map on the local metric plane.
 * Pure metres, monospaced survey labels, drag-pan + wheel-zoom,
 * click-to-select candidates. No lat/lng, no tiles, no web mercator.
 * ------------------------------------------------------------------ */

import { useEffect, useMemo, useRef, useState } from "react";
import { Maximize2, Minus, Plus } from "lucide-react";
import type { Candidate, Landmark, LocalPoint, Scene, Trail } from "@/lib/types";
import { C, cn, dist, extent, fmtCoord, fmtM } from "@/lib/utils";
import { TRAIL_TONE, toneColor } from "./u";

interface MemoryMark {
  at: LocalPoint;
  sigmaM: number;
  label: string;
  tone?: string;
}

export interface MapProps {
  scene: Scene;
  focus: LocalPoint;
  spanM?: number;
  candidates?: Candidate[];
  trails?: Trail[];
  memory?: MemoryMark | null;
  anchor?: { at: LocalPoint; sigmaM: number } | null;
  decision?: { at: LocalPoint; sigmaM: number; label: string } | null;
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

export default function LocalPlaneMap(props: MapProps) {
  const { scene, compact } = props;
  const wrapRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<SVGSVGElement>(null);
  const [size, setSize] = useState({ w: 820, h: 520 });
  const [view, setView] = useState<View>({ cx: props.focus.x, cy: props.focus.y, ppm: 0.55 });
  const [hover, setHover] = useState<LocalPoint | null>(null);
  const drag = useRef<{ sx: number; sy: number; cx: number; cy: number; moved: boolean } | null>(null);

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

  /* ------- fit ------- */
  const fit = useMemo(() => {
    return (v?: View) => {
      const w = size.w, h = size.h;
      if (props.spanM) {
        const ppm = Math.min(w / (props.spanM * 1.12), h / (props.spanM * 0.86));
        return { cx: props.focus.x, cy: props.focus.y, ppm };
      }
      const pts: LocalPoint[] = [];
      props.candidates?.forEach((c) => pts.push(c.at));
      props.trails?.forEach((t) => pts.push(...t.points));
      if (props.memory) pts.push(props.memory.at);
      if (props.anchor) pts.push(props.anchor.at);
      if (props.decision) pts.push(props.decision.at);
      if (pts.length < 2) {
        const s = 320;
        return { cx: props.focus.x, cy: props.focus.y, ppm: Math.min(w, h) / s };
      }
      const e = extent(pts);
      const pad = 90;
      const spanX = Math.max(80, e.maxX - e.minX + pad * 2);
      const spanY = Math.max(60, e.maxY - e.minY + pad * 2 + 60);
      const ppm = Math.min(w / spanX, h / spanY);
      void v;
      return { cx: (e.minX + e.maxX) / 2, cy: (e.minY + e.maxY) / 2 + 20, ppm };
    };
  }, [size, props.spanM, props.focus, props.candidates, props.trails, props.memory, props.anchor, props.decision]);

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

  const labelPt = (a: LocalPoint, b: LocalPoint) => {
    const mx = (X(a.x) + X(b.x)) / 2, my = (Y(a.y) + Y(b.y)) / 2;
    let ang = (Math.atan2(Y(b.y) - Y(a.y), X(b.x) - X(a.x)) * 180) / Math.PI;
    if (ang > 90) ang -= 180;
    if (ang < -90) ang += 180;
    return { mx, my, ang };
  };

  const landmarkGlyph = (lm: Landmark) => {
    const x = X(lm.at.x), y = Y(lm.at.y);
    const s = 4.2;
    switch (lm.kind) {
      case "temple":
        return <path d={`M${x},${y - s} L${x + s},${y + s * 0.8} L${x - s},${y + s * 0.8} Z`} fill="none" stroke={C.ink2} strokeWidth={1.1} />;
      case "school":
        return <rect x={x - s * 0.8} y={y - s * 0.8} width={s * 1.6} height={s * 1.6} fill="none" stroke={C.ink2} strokeWidth={1.1} />;
      case "tank":
        return (<g stroke={C.ink2} strokeWidth={1.1} fill="none">
          <circle cx={x} cy={y - 1.5} r={s * 0.75} />
          <path d={`M${x - s},${y + s * 0.9} H${x + s} M${x - s * 0.5},${y + s * 0.9} V${y + 0.5} M${x + s * 0.5},${y + s * 0.9} V${y + 0.5}`} />
        </g>);
      case "stand":
        return (<g stroke={C.ink2} strokeWidth={1.1} fill="none">
          <rect x={x - s} y={y - s * 0.8} width={s * 2} height={s * 1.1} />
          <path d={`M${x},${y + s * 0.3} V${y + s}`} />
        </g>);
      case "well":
        return (<g stroke={C.ink2} strokeWidth={1} fill="none">
          <circle cx={x} cy={y} r={s * 0.9} /><circle cx={x} cy={y} r={s * 0.4} />
        </g>);
      case "clinic":
        return <path d={`M${x - s},${y} H${x + s} M${x},${y - s} V${y + s}`} stroke={C.ink2} strokeWidth={1.2} />;
      case "bridge":
        return <path d={`M${x - s},${y - s * 0.6} V${y + s * 0.6} M${x + s},${y - s * 0.6} V${y + s * 0.6}`} stroke={C.ink2} strokeWidth={1.2} />;
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

        {/* hydro + rail under roads */}
        {scene.roads.filter((r) => r.kind === "stream").map((r) => (
          <polyline key={r.id} points={pathOf(r.path)} fill="none" stroke={"#8fa8b8"} strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" opacity={0.85} />
        ))}
        {scene.roads.filter((r) => r.kind === "rail").map((r) => (
          <g key={r.id}>
            <polyline points={pathOf(r.path)} fill="none" stroke={C.line3} strokeWidth={2.4} />
            <polyline points={pathOf(r.path)} fill="none" stroke={C.raised} strokeWidth={2.4} strokeDasharray="7 7" />
          </g>
        ))}

        {/* roads: casing then core */}
        {scene.roads.filter((r) => r.kind !== "stream" && r.kind !== "rail").map((r) => {
          const wpx = Math.max(r.kind === "arterial" ? 5 : r.kind === "street" ? 3.4 : r.kind === "lane" ? 2.2 : 1.4, r.widthM * view.ppm * 0.55);
          return (
            <g key={r.id}>
              <polyline points={pathOf(r.path)} fill="none" stroke={C.line3} strokeWidth={wpx + 1.8} strokeLinecap="round" strokeLinejoin="round" />
              <polyline points={pathOf(r.path)} fill="none" stroke={C.raised} strokeWidth={wpx} strokeLinecap="round" strokeLinejoin="round" />
            </g>
          );
        })}

        {/* road names */}
        {!compact && scene.roads.map((r) => {
          if (!r.name) return null;
          let bi = 0, bl = 0;
          for (let i = 0; i < r.path.length - 1; i++) {
            const L = dist(r.path[i], r.path[i + 1]);
            if (L > bl) { bl = L; bi = i; }
          }
          if (bl * view.ppm < 120) return null;
          const { mx, my, ang } = labelPt(r.path[bi], r.path[bi + 1]);
          return (
            <text key={`rn${r.id}`} x={mx} y={my - 4} fontSize={8.6} fill={C.mute} fontFamily={MONO}
              letterSpacing={1.1} textAnchor="middle" transform={`rotate(${ang} ${mx} ${my})`}
              style={{ paintOrder: "stroke" }} stroke={C.raised} strokeWidth={3}>
              {r.name.toUpperCase()}
            </text>
          );
        })}

        {/* landmarks */}
        {scene.landmarks.map((lm) => (
          <g key={lm.id}>
            {landmarkGlyph(lm)}
            {!compact && (
              <text x={X(lm.at.x) + 8} y={Y(lm.at.y) + 3} fontSize={8.6} fontFamily={MONO} fill={C.ink2} letterSpacing={0.4}
                style={{ paintOrder: "stroke" }} stroke={C.raised} strokeWidth={3}>
                {lm.label.toUpperCase()}
              </text>
            )}
          </g>
        ))}

        {/* parse anchor */}
        {props.anchor && (
          <g>
            <circle cx={X(props.anchor.at.x)} cy={Y(props.anchor.at.y)} r={Math.max(12, props.anchor.sigmaM * view.ppm)}
              fill="none" stroke={C.line3} strokeWidth={1} strokeDasharray="3 4" />
            <path d={`M${X(props.anchor.at.x) - 7},${Y(props.anchor.at.y)} H${X(props.anchor.at.x) + 7} M${X(props.anchor.at.x)},${Y(props.anchor.at.y) - 7} V${Y(props.anchor.at.y) + 7}`}
              stroke={C.faint} strokeWidth={1.1} />
            {!compact && (
              <text x={X(props.anchor.at.x) + 10} y={Y(props.anchor.at.y) - 8} fontSize={8.2} fill={C.faint} fontFamily={MONO}
                style={{ paintOrder: "stroke" }} stroke={C.raised} strokeWidth={3}>
                {`ANCHOR · σ ${props.anchor.sigmaM} m`}
              </text>
            )}
          </g>
        )}

        {/* evidence trails */}
        {props.trails?.map((t) => {
          const tone = toneColor(TRAIL_TONE[t.outcome]);
          const end = t.points[t.points.length - 1];
          const start = t.points[0];
          return (
            <g key={t.id}>
              <polyline points={pathOf(t.points)} fill="none" stroke={tone} strokeWidth={1.5} strokeDasharray="4 3" strokeLinejoin="round" opacity={0.9} />
              {t.points.map((p, i) => <circle key={i} cx={X(p.x)} cy={Y(p.y)} r={1.3} fill={tone} />)}
              <rect x={X(start.x) - 3} y={Y(start.y) - 3} width={6} height={6} fill="none" stroke={tone} strokeWidth={1.2} />
              <circle cx={X(end.x)} cy={Y(end.y)} r={3.2} fill={tone} stroke={C.raised} strokeWidth={1.2} />
              {!compact && (
                <text x={X(end.x) + 8} y={Y(end.y) + 12} fontSize={8.4} fontFamily={MONO} fill={tone} letterSpacing={0.4}
                  style={{ paintOrder: "stroke" }} stroke={C.raised} strokeWidth={3.4}>
                  {t.label}
                </text>
              )}
            </g>
          );
        })}

        {/* memory prior */}
        {props.memory && (
          <g>
            <circle cx={X(props.memory.at.x)} cy={Y(props.memory.at.y)} r={Math.max(9, props.memory.sigmaM * view.ppm)}
              fill="none" stroke={props.memory.tone ?? C.cool} strokeWidth={1} strokeDasharray="2 3" opacity={0.8} />
            <rect x={X(props.memory.at.x) - 4.5} y={Y(props.memory.at.y) - 4.5} width={9} height={9}
              transform={`rotate(45 ${X(props.memory.at.x)} ${Y(props.memory.at.y)})`}
              fill={C.panel} stroke={props.memory.tone ?? C.cool} strokeWidth={1.3} />
            {!compact && (
              <text x={X(props.memory.at.x) + 10} y={Y(props.memory.at.y) + 20} fontSize={8.2} fontFamily={MONO}
                fill={props.memory.tone ?? C.cool} style={{ paintOrder: "stroke" }} stroke={C.raised} strokeWidth={3.4}>
                {props.memory.label}
              </text>
            )}
          </g>
        )}

        {/* decision geometry */}
        {props.decision && (
          <g>
            <ellipse cx={X(props.decision.at.x)} cy={Y(props.decision.at.y)}
              rx={Math.max(7, props.decision.sigmaM * view.ppm)} ry={Math.max(7, props.decision.sigmaM * view.ppm * 0.78)}
              fill={C.accent} fillOpacity={0.06} stroke={C.accent} strokeWidth={1.3} strokeDasharray="5 3"
              className="marching" />
            <path d={`M${X(props.decision.at.x) - 6},${Y(props.decision.at.y)} H${X(props.decision.at.x) + 6} M${X(props.decision.at.x)},${Y(props.decision.at.y) - 6} V${Y(props.decision.at.y) + 6}`}
              stroke={C.accentDeep} strokeWidth={1.4} />
            {!compact && (
              <text x={X(props.decision.at.x) + 12} y={Y(props.decision.at.y) - 10} fontSize={8.6} fontFamily={MONO}
                fill={C.accentDeep} fontWeight={600} style={{ paintOrder: "stroke" }} stroke={C.raised} strokeWidth={3.4}>
                {props.decision.label}
              </text>
            )}
          </g>
        )}

        {/* candidates */}
        {props.candidates?.map((c, i) => {
          const x = X(c.at.x), y = Y(c.at.y);
          const active = sel === c.id;
          return (
            <g key={c.id} onClick={(e) => { if (!drag.current?.moved) { e.stopPropagation(); props.onSelect?.(c.id); } }}
              className="cursor-pointer">
              <circle cx={x} cy={y} r={Math.max(6, c.sigmaM * view.ppm)} fill="none"
                stroke={active ? C.accent : C.line3} strokeWidth={1} strokeDasharray="3 3" opacity={active ? 0.9 : 0.55} />
              {active && <circle cx={x} cy={y} r={13} fill="none" stroke={C.accent} strokeWidth={1.2} />}
              <circle cx={x} cy={y} r={8} fill={active ? C.accentSoft : C.raised} stroke={active ? C.accentDeep : C.ink} strokeWidth={active ? 1.5 : 1.2} />
              <text x={x} y={y + 3.2} textAnchor="middle" fontSize={9} fontFamily={MONO} fontWeight={600}
                fill={active ? C.accentDeep : C.ink} pointerEvents="none">
                {i + 1}
              </text>
              <text x={x} y={y + 26} textAnchor="middle" fontSize={8.6} fontFamily={MONO} fontWeight={600}
                fill={active ? C.accentDeep : C.ink2} pointerEvents="none"
                style={{ paintOrder: "stroke" }} stroke={C.raised} strokeWidth={3.4}>
                {c.score.toFixed(2)}
              </text>
            </g>
          );
        })}

        {/* frame */}
        <rect x={0.5} y={0.5} width={size.w - 1} height={size.h - 1} fill="none" stroke={C.line2} strokeWidth={1} pointerEvents="none" />
      </svg>

      {/* readout */}
      <div className="absolute left-2 top-2 border hairline bg-raised/95 px-2 py-1">
        <div className="mono text-[8.5px] tracking-[0.14em] text-faint uppercase">Local plane · SEAL-01 · metres · N↑</div>
        <div className="mono text-[10.5px] text-ink mt-px">
          E {fmtCoord(hover?.x ?? view.cx)}&nbsp;&nbsp;N {fmtCoord(hover?.y ?? view.cy)}
          <span className="text-faint"> · grid {step} m</span>
        </div>
      </div>

      {/* zoom controls */}
      {!compact && (
        <div className="absolute right-2 top-2 flex flex-col border hairline bg-raised">
          <button onClick={() => zoom(1.4)} className="p-1.5 text-ink2 hover:bg-accent-faint hover:text-accent-deep border-b hairline" title="Zoom in">
            <Plus size={13} strokeWidth={1.8} />
          </button>
          <button onClick={() => zoom(1 / 1.4)} className="p-1.5 text-ink2 hover:bg-accent-faint hover:text-accent-deep border-b hairline" title="Zoom out">
            <Minus size={13} strokeWidth={1.8} />
          </button>
          <button onClick={() => setView(fit())} className="p-1.5 text-ink2 hover:bg-accent-faint hover:text-accent-deep" title="Fit content">
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
