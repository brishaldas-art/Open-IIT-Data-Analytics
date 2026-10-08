import { useMemo } from "react";
import { ArrowRight, TriangleAlert } from "lucide-react";
import { fetchCases, fetchOverview, fetchVisits, useQuery } from "@/lib/api";
import type { CaseKind, DayStat } from "@/lib/types";
import { C, cn, fmtInt, fmtM, fmtPct } from "@/lib/utils";
import { Dot, KIND_LABEL, KIND_TONE, Meter, OUTCOME_TONE, Panel, Ring, Sec, Spark, Tag } from "@/components/u";
import { ViewHead, type ViewId } from "@/components/Shell";
import { useSession } from "@/lib/session";

const MONO = "'IBM Plex Mono', monospace";

/* ---------------- resolution performance chart ---------------- */

function PerfChart({ series }: { series: DayStat[] }) {
  const W = 640, H = 216, pl = 34, pr = 14, pt = 14, pb = 22;
  const n = series.length;
  const aMin = 0.5, aMax = 1.0;
  const x = (i: number) => pl + (i * (W - pl - pr)) / (n - 1);
  const y = (a: number) => pt + (1 - (a - aMin) / (aMax - aMin)) * (H - pt - pb);
  const maxR = Math.max(...series.map((s) => s.resolutions));
  const bw = ((W - pl - pr) / n) * 0.52;

  const line = (key: "warmAcc" | "coldAcc") =>
    series.map((s, i) => `${x(i).toFixed(1)},${y(s[key]).toFixed(1)}`).join(" ");

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto block">
      {[0.6, 0.7, 0.8, 0.9, 1.0].map((g) => (
        <g key={g}>
          <line x1={pl} x2={W - pr} y1={y(g)} y2={y(g)} stroke={C.line} strokeWidth={0.6} />
          <text x={pl - 5} y={y(g) + 2.5} textAnchor="end" fontSize={8} fill={C.faint} fontFamily={MONO}>
            {g.toFixed(1)}
          </text>
        </g>
      ))}
      {series.map((s, i) => (
        <rect key={s.day} x={x(i) - bw / 2} y={H - pb - (s.resolutions / maxR) * 34}
          width={bw} height={(s.resolutions / maxR) * 34} fill={C.line2} opacity={0.55} />
      ))}
      <line x1={pl} x2={W - pr} y1={y(0.85)} y2={y(0.85)} stroke={C.accent} strokeWidth={0.9} strokeDasharray="4 3" />
      <text x={W - pr} y={y(0.85) - 4} textAnchor="end" fontSize={7.6} fill={C.accentDeep} fontFamily={MONO} letterSpacing={0.6}>
        AUTO-DECISION GATE 0.85
      </text>
      <polyline points={line("coldAcc")} fill="none" stroke={C.cool} strokeWidth={1.2} strokeDasharray="3 2" />
      <polyline points={line("warmAcc")} fill="none" stroke={C.accent} strokeWidth={1.8} strokeLinejoin="round" />
      {series.map((s, i) => (
        <g key={s.day}>
          <circle cx={x(i)} cy={y(s.warmAcc)} r={i === n - 1 ? 2.6 : 1.4} fill={C.accent} />
          {i % 2 === 0 && (
            <text x={x(i)} y={H - pb + 11} textAnchor="middle" fontSize={7.6} fill={C.faint} fontFamily={MONO}>
              {s.day.slice(0, 2)}
            </text>
          )}
        </g>
      ))}
      <circle cx={x(n - 1)} cy={y(series[n - 1].coldAcc)} r={2.4} fill={C.cool} />
      <text x={x(n - 1) - 6} y={y(series[n - 1].warmAcc) - 7} textAnchor="end" fontSize={9.5} fill={C.accentDeep}
        fontFamily={MONO} fontWeight={600}>
        {fmtPct(series[n - 1].warmAcc, 1)}
      </text>
      <text x={x(n - 1) - 6} y={y(series[n - 1].coldAcc) + 13} textAnchor="end" fontSize={9.5} fill={C.cool}
        fontFamily={MONO} fontWeight={600}>
        {fmtPct(series[n - 1].coldAcc, 1)}
      </text>
      <text x={pl} y={H - 4} fontSize={7.6} fill={C.faint} fontFamily={MONO} letterSpacing={0.5}>
        AGREEMENT WITH FINAL OUTCOME · BARS = DAILY VOLUME
      </text>
    </svg>
  );
}

/* ---------------- KPI tile ---------------- */

function Kpi({
  label, value, unit, sub, spark, tone = "ink",
}: { label: string; value: string; unit?: string; sub: React.ReactNode; spark?: number[]; tone?: "ink" | "accent" }) {
  return (
    <Panel className={cn("px-3.5 py-3 flex flex-col justify-between min-h-[104px]", tone === "accent" && "border-accent/45")}>
      <div className="flex items-center justify-between">
        <span className="mono text-[9px] uppercase tracking-[0.12em] text-mute">{label}</span>
        {spark && <Spark data={spark} w={64} h={18} tone={tone === "accent" ? "accent" : "ink"} />}
      </div>
      <div className="flex items-baseline gap-1.5 mt-1">
        <span className={cn("serif text-[30px] leading-none font-semibold tnum", tone === "accent" && "text-accent-deep")}>{value}</span>
        {unit && <span className="mono text-[10px] text-mute">{unit}</span>}
      </div>
      <div className="mono text-[9px] text-mute mt-1.5 leading-snug">{sub}</div>
    </Panel>
  );
}

/* ---------------- main view ---------------- */

export default function Overview({ go, queueCount }: { go: (v: ViewId) => void; queueCount: number }) {
  const { data: ov } = useQuery(fetchOverview);
  const { data: visits } = useQuery(fetchVisits);
  const { data: cases } = useQuery(fetchCases);
  const { casePatches, extraCases } = useSession();

  const byKind = useMemo(() => {
    const m = new Map<CaseKind, { n: number; p1: number }>();
    [...(cases ?? []), ...extraCases].forEach((c) => {
      if (casePatches[c.id]?.closed) return;
      const e = m.get(c.kind) ?? { n: 0, p1: 0 };
      e.n += 1;
      if (c.priority === "P1") e.p1 += 1;
      m.set(c.kind, e);
    });
    return m;
  }, [cases, casePatches, extraCases]);

  if (!ov) return <div className="mono text-[11px] text-mute p-8">loading fixtures…</div>;

  const vols = ov.series.map((s) => s.resolutions);
  const degraded = ov.services.filter((s) => s.status !== "OK");

  return (
    <div className="max-w-[1440px] mx-auto">
      <ViewHead
        title="Operations overview"
        note="replay window 12–15 Feb 2026 · origin SEAL-01 · local metric plane"
        right={
          <>
            <Tag tone="ok"><Dot tone="ok" blink /> ledger live</Tag>
            {degraded.length > 0 && <Tag tone="warn"><TriangleAlert size={10} /> {degraded.length} service degraded</Tag>}
          </>
        }
      />

      {/* KPI row */}
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-3">
        <Kpi label="Resolutions today" value={fmtInt(ov.kpis.resolutionsToday)} spark={vols}
          sub={<span>▲ {ov.kpis.resolutionsDeltaPct}% vs 7-day mean</span>} />
        <Kpi label="Auto-decided share" value={fmtPct(ov.kpis.autoDecidedPct, 1)}
          sub={<span>human sign-off {fmtPct(1 - ov.kpis.autoDecidedPct, 1)} · all ledgered</span>} />
        <Kpi label="Median resolve latency" value={String(ov.kpis.medianResolveMs)} unit="ms"
          sub={<span>p95 640 ms · parse 12 ms cand-idx 31 ms</span>} />
        <Kpi label="Open verify cases" value={String(queueCount)} tone={ov.kpis.p1Cases > 0 ? "accent" : "ink"}
          sub={<span className="text-accent-deep">{ov.kpis.p1Cases} × P1 · 1 SLA breach risk</span>} />
      </div>

      {/* perf + warm/cold + queue */}
      <div className="grid grid-cols-12 gap-3 mt-3">
        <Panel className="col-span-12 xl:col-span-7 px-3.5 py-3">
          <Sec no="A" title="Resolution performance — 14 days"
            right={
              <span className="flex items-center gap-3 mono text-[9px] text-mute">
                <span className="flex items-center gap-1"><span className="inline-block w-3 h-[2px] bg-accent" /> warm</span>
                <span className="flex items-center gap-1"><span className="inline-block w-3 border-t border-dashed border-cool" /> cold</span>
              </span>
            } />
          <div className="pt-2">
            <PerfChart series={ov.series} />
          </div>
        </Panel>

        <div className="col-span-12 xl:col-span-5 grid grid-rows-2 gap-3">
          <Panel className="px-3.5 py-3">
            <Sec no="B" title="Decision accuracy — warm vs cold start" />
            <div className="grid grid-cols-2 gap-4 pt-2.5">
              {([
                { k: "warm", v: ov.warmCold.warm, n: ov.warmCold.warmN, d: "evidence / memory prior present", t: "accent" as const },
                { k: "cold", v: ov.warmCold.cold, n: ov.warmCold.coldN, d: "first-seen locality, no prior", t: "cool" as const },
              ]).map((r) => (
                <div key={r.k}>
                  <div className="mono text-[9px] uppercase tracking-[0.1em] text-mute">{r.k} start</div>
                  <div className={cn("serif text-[26px] font-semibold tnum leading-tight", r.t === "accent" ? "text-accent-deep" : "text-cool")}>
                    {fmtPct(r.v, 1)}
                  </div>
                  <Meter v={r.v} tone={r.t} w="100%" h={3} />
                  <div className="mono text-[8.5px] text-mute mt-1 leading-snug">n={fmtInt(r.n)} · {r.d}</div>
                </div>
              ))}
            </div>
            <p className="text-[11px] text-ink2 leading-snug mt-2.5 border-t hairline pt-2">
              Field evidence is worth <span className="serif font-semibold text-accent-deep">+28.6 pts</span> of agreement.
              Cold intakes above the 0.85 gate still auto-decide; everything else goes to the field.
            </p>
          </Panel>

          <Panel className="px-3.5 py-3 cursor-pointer hover:border-line2 transition-colors" >
            <div onClick={() => go("queue")}>
              <Sec no="C" title="Active verification queue"
                right={<span className="mono text-[9px] text-accent-deep flex items-center gap-1">open workbench <ArrowRight size={10} /></span>} />
              <div className="pt-1.5 divide-y divide-line">
                {(["VERIFY_FIRST", "REVERIFICATION", "CONTESTED", "MOVED_SUSPECTED", "UNPLACEABLE"] as CaseKind[]).map((k) => {
                  const e = byKind.get(k);
                  return (
                    <div key={k} className="flex items-center gap-2 py-[5px]">
                      <Tag tone={KIND_TONE[k]} className="w-[118px] justify-center">{KIND_LABEL[k]}</Tag>
                      <Meter v={(e?.n ?? 0) / 5} tone={KIND_TONE[k]} w="100%" h={3} />
                      <span className="mono text-[11px] w-5 text-right tnum">{e?.n ?? 0}</span>
                      {e && e.p1 > 0 && <span className="mono text-[8.5px] text-accent-deep">{e.p1}P1</span>}
                    </div>
                  );
                })}
              </div>
            </div>
          </Panel>
        </div>
      </div>

      {/* evidence + services */}
      <div className="grid grid-cols-12 gap-3 mt-3">
        <Panel className="col-span-12 xl:col-span-7 px-3.5 py-3">
          <Sec no="D" title="Recent field evidence"
            right={<button onClick={() => go("evidence")} className="mono text-[9px] text-accent-deep flex items-center gap-1 hover:underline">timeline <ArrowRight size={10} /></button>} />
          <div className="pt-1 divide-y divide-line">
            {(visits ?? []).slice(0, 6).map((v) => (
              <button key={v.id} onClick={() => go("evidence")}
                className="w-full grid grid-cols-[76px_1fr_88px_64px_58px_36px] items-center gap-2 py-[6px] text-left hover:bg-panel transition-colors px-1 -mx-1">
                <span className="mono text-[9.5px] text-mute">{v.day.slice(0, 6)} {v.ts}</span>
                <span className="min-w-0">
                  <span className="block text-[11.5px] truncate">{v.placeLabel}</span>
                  <span className="block mono text-[8.5px] text-faint">{v.id} · {v.officer}</span>
                </span>
                <Tag tone={OUTCOME_TONE[v.outcome]} className="justify-center">{v.outcome}</Tag>
                <span className="mono text-[10px] text-ink2 text-right">{v.outcome === "MOVED" ? `+${fmtM(v.offsetM, 1)}` : `±${fmtM(v.offsetM, 1)}`}</span>
                <span className={cn("mono text-[10px] text-right", v.integrity.mock ? "text-crit font-semibold" : "text-mute")}>
                  {v.integrity.mock ? "MOCK!" : `CEP ${v.fix.cepM}`}
                </span>
                <span className="justify-self-end"><Ring v={v.quality} size={26} /></span>
              </button>
            ))}
          </div>
        </Panel>

        <Panel className="col-span-12 xl:col-span-5 px-3.5 py-3">
          <Sec no="E" title="System health"
            right={<span className="mono text-[9px] text-mute">p50 · err% · depth</span>} />
          <div className="pt-1 divide-y divide-line">
            {ov.services.map((s) => (
              <div key={s.name} className={cn("grid grid-cols-[96px_1fr_44px_44px_64px_62px] items-center gap-2 py-[6.5px] px-1 -mx-1", s.status !== "OK" && "bg-warn-soft/50")}>
                <span className="mono text-[10px] font-semibold">{s.name}</span>
                <span className="mono text-[8.5px] text-mute truncate">{s.role}</span>
                <span className="mono text-[10px] text-right tnum">{s.p50ms}ms</span>
                <span className={cn("mono text-[10px] text-right tnum", s.errPct > 1 ? "text-warn" : "text-mute")}>{s.errPct.toFixed(1)}%</span>
                <span className="flex items-center gap-1.5 justify-end">
                  <Meter v={Math.min(1, s.queueDepth / 150)} tone={s.queueDepth > 20 ? "warn" : "ink"} w={30} h={3} />
                  <span className="mono text-[9.5px] tnum w-6 text-right">{s.queueDepth}</span>
                </span>
                <span className="justify-self-end">
                  <Tag tone={s.status === "OK" ? "ok" : "warn"}><Dot tone={s.status === "OK" ? "ok" : "warn"} blink={s.status !== "OK"} />{s.status}</Tag>
                </span>
              </div>
            ))}
          </div>
          <p className="mono text-[8.5px] text-faint leading-relaxed border-t hairline pt-2 mt-1">
            verify-orch backlog 137 field task dispatches · autoscaling engaged · no data loss risk — store-and-forward buffer 96 h
          </p>
        </Panel>
      </div>
    </div>
  );
}
