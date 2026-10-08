import { useMemo, useState } from "react";
import { Camera, ShieldAlert, ShieldCheck } from "lucide-react";
import { fetchPlaces, fetchScene, fetchScenarios, fetchVisits, useQuery } from "@/lib/api";
import type { FieldVisit, Trail, VisitOutcome } from "@/lib/types";
import { cn, fmtM } from "@/lib/utils";
import LocalPlaneMap from "@/components/LocalPlaneMap";
import { KV, Meter, OUTCOME_TONE, Panel, Ring, Tag } from "@/components/u";
import { ViewHead, type ViewId } from "@/components/Shell";

const OUTCOMES: VisitOutcome[] = ["CONFIRMED", "NOT_FOUND", "MOVED", "PARTIAL", "REFUTED"];

function signal(label: string, val: string, ok: boolean, hardFail = false) {
  return { label, val, ok, hardFail };
}

export default function FieldEvidence({ go }: { go: (v: ViewId) => void }) {
  const { data: visits } = useQuery(fetchVisits);
  const { data: places } = useQuery(fetchPlaces);
  const { data: scene } = useQuery(fetchScene);
  const { data: scenarios } = useQuery(fetchScenarios);
  const [outcome, setOutcome] = useState<VisitOutcome | "ALL">("ALL");
  const [flaggedOnly, setFlaggedOnly] = useState(false);
  const [selId, setSelId] = useState<string | null>(null);

  const filtered = useMemo(() => {
    return (visits ?? []).filter((v) => {
      if (outcome !== "ALL" && v.outcome !== outcome) return false;
      if (flaggedOnly && !v.integrity.mock && v.integrity.timeSkewS < 2 && v.integrity.trailSigmaM < 5) return false;
      return true;
    });
  }, [visits, outcome, flaggedOnly]);

  const sel: FieldVisit | null = filtered.find((v) => v.id === selId) ?? filtered[0] ?? null;
  const days = useMemo(() => {
    const m = new Map<string, FieldVisit[]>();
    filtered.forEach((v) => {
      const arr = m.get(v.day) ?? [];
      arr.push(v);
      m.set(v.day, arr);
    });
    return [...m.entries()];
  }, [filtered]);

  const selTrails: Trail[] = useMemo(() => {
    if (!sel || !scenarios) return [];
    return scenarios.flatMap((s) => s.trails).filter((t) => t.label.startsWith(sel.id));
  }, [sel, scenarios]);

  const selPlace = useMemo(() => places?.find((p) => p.id === sel?.placeId) ?? null, [places, sel]);

  if (!visits || !places || !scene) return <div className="mono text-[11px] text-mute p-8">loading evidence…</div>;

  const avgQ = visits.reduce((a, v) => a + v.quality, 0) / visits.length;
  const rejected = visits.filter((v) => v.integrity.mock).length;

  const signals = sel
    ? [
        signal("mock provider", sel.integrity.mock ? "FLAGGED" : "clear", !sel.integrity.mock, true),
        signal("clock skew Δt", `${sel.integrity.timeSkewS.toFixed(1)} s`, sel.integrity.timeSkewS < 2),
        signal("trail σ", fmtM(sel.integrity.trailSigmaM, 1), sel.integrity.trailSigmaM < 5),
        signal("dwell plausibility", `${sel.dwellS} s`, sel.dwellS >= 20),
        signal("fix CEP", fmtM(sel.fix.cepM, 1), sel.fix.cepM < 6),
        signal("constellation", `${sel.fix.sats} sats · HDOP ${sel.fix.hdop.toFixed(1)}`, sel.fix.hdop < 2),
      ]
    : [];
  void go;

  return (
    <div className="max-w-[1500px] mx-auto">
      <ViewHead
        title="Field evidence"
        note="visits, GNSS fixes and integrity signals — the system's ground truth"
        right={
          <>
            <Tag tone="ink">{visits.length} visits</Tag>
            <Tag tone="ok">avg quality {avgQ.toFixed(2)}</Tag>
            <Tag tone={rejected > 0 ? "crit" : "ok"}>{rejected} rejected</Tag>
          </>
        }
      />

      <div className="flex flex-wrap items-center gap-1.5 mb-3">
        {(["ALL", ...OUTCOMES] as const).map((o) => (
          <button key={o} onClick={() => setOutcome(o)}
            className={cn("mono text-[9px] uppercase tracking-[0.08em] border px-2 py-1 transition-colors",
              outcome === o ? "border-ink bg-ink text-paper" : "hairline bg-raised text-mute hover:text-ink")}>
            {o}
          </button>
        ))}
        <span className="w-px h-4 bg-line2 mx-1" />
        <button onClick={() => setFlaggedOnly(!flaggedOnly)}
          className={cn("mono text-[9px] uppercase tracking-[0.08em] border px-2 py-1 transition-colors flex items-center gap-1",
            flaggedOnly ? "border-crit bg-crit text-paper" : "hairline bg-raised text-mute hover:text-ink")}>
          <ShieldAlert size={10} /> integrity flags only
        </button>
      </div>

      <div className="grid grid-cols-12 gap-3">
        {/* timeline */}
        <div className="col-span-12 xl:col-span-7 self-start">
          {days.map(([day, rows]) => (
            <div key={day} className="mb-3">
              <div className="flex items-center gap-2 mb-1.5">
                <span className="mono text-[9.5px] uppercase tracking-[0.14em] text-ink2 font-semibold">{day}</span>
                <span className="flex-1 h-px bg-line" />
                <span className="mono text-[8.5px] text-faint">{rows.length} visit{rows.length > 1 ? "s" : ""}</span>
              </div>
              <Panel className="divide-y divide-line px-3">
                {rows.map((v) => {
                  const active = sel?.id === v.id;
                  const bad = v.integrity.mock;
                  return (
                    <button key={v.id} onClick={() => setSelId(v.id)}
                      className={cn("w-full text-left grid grid-cols-[40px_1fr_92px_120px_90px] items-center gap-3 px-1 -mx-1 py-2 transition-colors",
                        active ? "bg-accent-faint/60" : "hover:bg-panel")}>
                      <Ring v={v.quality} size={34} />
                      <span className="min-w-0">
                        <span className="flex items-center gap-1.5">
                          <span className="text-[12px] font-medium truncate">{v.placeLabel}</span>
                          {bad && <ShieldAlert size={11} className="text-crit shrink-0" />}
                        </span>
                        <span className="block mono text-[8.5px] text-faint truncate">
                          {v.id} · {v.ts} · {v.officer} · {v.device}
                        </span>
                        <span className="block mono text-[8.5px] text-mute truncate">{v.note}</span>
                      </span>
                      <Tag tone={OUTCOME_TONE[v.outcome]} className="justify-center">{v.outcome}</Tag>
                      <span className="mono text-[9px] text-ink2 text-right">
                        CEP {v.fix.cepM} m · {v.fix.sats}sat<br />
                        <span className="text-mute">Δmem {v.outcome === "MOVED" ? "+" : "±"}{fmtM(v.offsetM, 1)}</span>
                      </span>
                      <span className="mono text-[9px] text-mute text-right flex items-center justify-end gap-1">
                        <Camera size={10} /> {v.photos} · {v.dwellS >= 600 ? `${Math.round(v.dwellS / 60)} min` : `${v.dwellS} s`}
                      </span>
                    </button>
                  );
                })}
              </Panel>
            </div>
          ))}
        </div>

        {/* detail */}
        <div className="col-span-12 xl:col-span-5 self-start">
          {sel && (
            <Panel className="px-3.5 py-3 rise" key={sel.id}>
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <h2 className="serif text-[18px] font-semibold leading-tight">{sel.id} — {sel.placeLabel}</h2>
                  <div className="mono text-[9px] text-mute mt-0.5 uppercase tracking-[0.06em]">
                    {sel.day} · {sel.ts} IST · {sel.officer} · {sel.device}
                  </div>
                </div>
                <Tag tone={OUTCOME_TONE[sel.outcome]}>{sel.outcome}</Tag>
              </div>

              <LocalPlaneMap
                className="h-[218px] mt-3"
                compact
                scene={scene}
                focus={sel.point}
                trails={selTrails}
                memory={selPlace ? { at: selPlace.at, sigmaM: selPlace.sigmaM, label: "MEMORY" } : null}
                decision={{ at: sel.point, sigmaM: sel.fix.cepM, label: "FIX" }}
                fitKey={sel.id}
              />

              <div className="grid grid-cols-2 gap-x-4 mt-3 border-t hairline pt-2">
                <div>
                  <KV k="offset vs memory" v={`${sel.outcome === "MOVED" ? "+" : "±"}${fmtM(sel.offsetM, 1)}`} tone={sel.offsetM > 10 ? "warn" : undefined} />
                  <KV k="fix CEP" v={fmtM(sel.fix.cepM, 1)} />
                  <KV k="hdop / sats" v={`${sel.fix.hdop.toFixed(1)} / ${sel.fix.sats}`} />
                </div>
                <div>
                  <KV k="dwell at point" v={sel.dwellS >= 600 ? `${Math.round(sel.dwellS / 60)} min` : `${sel.dwellS} s`} />
                  <KV k="motion state" v={sel.motion} />
                  <KV k="photos" v={`${sel.photos} attached`} />
                </div>
              </div>

              <div className="mt-2 border-t hairline pt-2">
                <div className="mono text-[8.5px] uppercase tracking-[0.12em] text-faint mb-1.5 flex items-center justify-between">
                  <span>integrity signals</span>
                  {sel.integrity.mock
                    ? <span className="text-crit flex items-center gap-1"><ShieldAlert size={10} /> hard fail — rejected from priors</span>
                    : <span className="text-ok flex items-center gap-1"><ShieldCheck size={10} /> admitted to priors</span>}
                </div>
                <div className="grid grid-cols-2 gap-1.5">
                  {signals.map((s) => (
                    <div key={s.label} className={cn("flex items-center justify-between border px-2 py-1 mono text-[9px]",
                      s.ok ? "hairline bg-raised" : s.hardFail ? "border-crit/60 bg-crit-soft/60 text-crit" : "border-warn/50 bg-warn-soft/60 text-warn")}>
                      <span className="uppercase tracking-[0.06em] text-mute">{s.label}</span>
                      <span className="font-semibold tnum">{s.val}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="mt-3 flex items-center gap-3 border-t hairline pt-2.5">
                <Ring v={sel.quality} size={44} label={sel.quality.toFixed(2)} />
                <div className="flex-1">
                  <div className="mono text-[8.5px] uppercase tracking-[0.12em] text-faint">evidence quality composite</div>
                  <Meter v={sel.quality} tone={sel.quality >= 0.8 ? "ok" : sel.quality >= 0.5 ? "warn" : "crit"} w="100%" h={4} />
                  <p className="text-[11px] text-ink2 leading-snug mt-1.5">{sel.note}</p>
                </div>
              </div>
            </Panel>
          )}
        </div>
      </div>
    </div>
  );
}
