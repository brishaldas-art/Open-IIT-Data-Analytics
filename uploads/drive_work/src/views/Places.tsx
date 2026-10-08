import { useMemo, useState } from "react";
import { FilePlus2, Footprints, Search, TriangleAlert } from "lucide-react";
import { fetchPlaces, fetchScene, fetchScenarios, fetchVisits, useQuery } from "@/lib/api";
import { useSession } from "@/lib/session";
import type { Place, PlaceState } from "@/lib/types";
import { cn, fmtCoord, fmtM, fmtPct } from "@/lib/utils";
import LocalPlaneMap from "@/components/LocalPlaneMap";
import { KV, Meter, OUTCOME_TONE, Panel, Ring, Sec, STATE_TONE, Tag } from "@/components/u";
import { ViewHead, type ViewId } from "@/components/Shell";

const STATES: PlaceState[] = ["STABLE", "PROVISIONAL", "CONTESTED", "STALE", "RETIRED"];

/** which evidence trails belong to which place (fixture linkage) */
const PLACE_EVIDENCE: Record<string, string[]> = {
  "PL-AMB-0142": ["EV-2311", "EV-1977"],
  "PL-CHK-0087": ["EV-2306", "EV-2064"],
  "PL-RJG-0231": ["EV-2309", "EV-2310"],
  "PL-KHD-0310": ["EV-2301"],
};

export default function Places({ go }: { go: (v: ViewId) => void }) {
  const { data: places } = useQuery(fetchPlaces);
  const { data: visits } = useQuery(fetchVisits);
  const { data: scene } = useQuery(fetchScene);
  const { data: scenarios } = useQuery(fetchScenarios);
  const { addCase, push, notify, } = useSession();
  const [state, setState] = useState<PlaceState | "ALL">("ALL");
  const [q, setQ] = useState("");
  const [selId, setSelId] = useState<string | null>(null);

  const filtered = useMemo(() => {
    if (!places) return [];
    return places.filter((p) => {
      if (state !== "ALL" && p.state !== state) return false;
      if (q && !`${p.label} ${p.address} ${p.id}`.toLowerCase().includes(q.toLowerCase())) return false;
      return true;
    });
  }, [places, state, q]);

  const sel: Place | null = filtered.find((p) => p.id === selId) ?? filtered[0] ?? null;
  const selVisits = useMemo(() => (visits ?? []).filter((v) => v.placeId === sel?.id), [visits, sel]);
  const selTrails = useMemo(() => {
    if (!sel || !scenarios) return [];
    const ids = PLACE_EVIDENCE[sel.id] ?? [];
    return scenarios.flatMap((s) => s.trails).filter((t) => ids.some((id) => t.label.startsWith(id)));
  }, [sel, scenarios]);

  if (!places || !scene) return <div className="mono text-[11px] text-mute p-8">loading places…</div>;

  const counts = new Map(STATES.map((s) => [s, places.filter((p) => p.state === s).length]));

  const queueRever = (p: Place) => {
    const id = `VQ-49${String(30 + Math.floor(Math.random() * 40))}`;
    addCase({
      id, kind: p.state === "CONTESTED" ? "CONTESTED" : "REVERIFICATION",
      placeLabel: p.label, placeId: p.id, rawAddress: p.address,
      priority: p.state === "CONTESTED" ? "P2" : "P3", ageDays: 0, slaHoursLeft: 96, slaHoursTotal: 96,
      reasonCodes: [p.state === "STALE" ? "STALE_REFRESH" : "OPERATOR_REQUEST"],
      at: p.at, sigmaM: p.sigmaM, score: p.confidence,
      recommendation: "Operator-initiated recheck from place record.",
    });
    push("REVERIFICATION_QUEUED", `${id} · ${p.id} ${p.label}`);
    notify(`reverification ${id} opened for ${p.id}`);
  };

  return (
    <div className="max-w-[1500px] mx-auto">
      <ViewHead
        title="Places — address memory"
        note="what the system believes, with confidence, contradictions and lineage"
        right={
          <span className="flex items-center border hairline bg-raised px-2 py-1.5 gap-1.5">
            <Search size={12} className="text-mute" />
            <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="search places…"
              className="bg-transparent mono text-[10.5px] w-40 focus:outline-none placeholder:text-faint" />
          </span>
        }
      />

      <div className="flex flex-wrap gap-1.5 mb-3">
        {(["ALL", ...STATES] as const).map((s) => (
          <button key={s} onClick={() => setState(s)}
            className={cn("mono text-[9px] uppercase tracking-[0.08em] border px-2 py-1 transition-colors",
              state === s ? "border-ink bg-ink text-paper" : "hairline bg-raised text-mute hover:text-ink")}>
            {s} · {s === "ALL" ? places.length : counts.get(s)}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-12 gap-3">
        {/* list */}
        <Panel className="col-span-12 xl:col-span-7 px-3 py-2.5 self-start">
          <Sec no="01" title={`Memory records · ${filtered.length}`}
            right={<span className="mono text-[8.5px] text-faint">conf · σ · drift · last verified</span>} />
          <div className="divide-y divide-line">
            {filtered.map((p) => {
              const active = sel?.id === p.id;
              return (
                <button key={p.id} onClick={() => setSelId(p.id)}
                  className={cn("w-full text-left grid grid-cols-[1fr_86px_128px_58px_64px_88px] items-center gap-2 px-1.5 -mx-1.5 py-[7px] transition-colors",
                    active ? "bg-accent-faint/60" : "hover:bg-panel")}>
                  <span className="min-w-0">
                    <span className="flex items-center gap-1.5">
                      <span className="text-[12px] font-medium truncate">{p.label}</span>
                      {p.contradictions.length > 0 && <TriangleAlert size={11} className="text-plum shrink-0" />}
                    </span>
                    <span className="block mono text-[8.5px] text-faint truncate">{p.id} · {p.address}</span>
                  </span>
                  <Tag tone={STATE_TONE[p.state]} className="justify-center">{p.state}</Tag>
                  <span className="flex items-center gap-1.5">
                    <Meter v={p.confidence} tone={p.confidence >= 0.8 ? "ok" : p.confidence >= 0.5 ? "warn" : "crit"} w={48} h={3} />
                    <span className="mono text-[10px] tnum text-ink2">{fmtPct(p.confidence, 0)}</span>
                  </span>
                  <span className="mono text-[10px] tnum text-ink2 text-right">±{p.sigmaM}m</span>
                  <span className={cn("mono text-[10px] tnum text-right", p.driftM > 10 ? "text-warn" : "text-ink2")}>
                    {p.driftM > 0 ? fmtM(p.driftM, 1) : "—"}
                  </span>
                  <span className="mono text-[9px] text-mute text-right">{p.lastVerified}</span>
                </button>
              );
            })}
            {filtered.length === 0 && <div className="py-8 text-center mono text-[10px] text-mute uppercase tracking-[0.1em]">no records match</div>}
          </div>
        </Panel>

        {/* detail */}
        <div className="col-span-12 xl:col-span-5 space-y-3 self-start">
          {sel && (
            <Panel className="px-3.5 py-3 rise" key={sel.id}>
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <h2 className="serif text-[19px] font-semibold leading-tight">{sel.label}</h2>
                  <div className="mono text-[9px] text-mute mt-0.5 uppercase tracking-[0.06em]">{sel.id} · {sel.address}</div>
                </div>
                <Tag tone={STATE_TONE[sel.state]}>{sel.state}</Tag>
              </div>

              <div className="grid grid-cols-2 gap-3 mt-3 border-t hairline pt-3">
                <div>
                  <div className="mono text-[8.5px] uppercase tracking-[0.12em] text-faint">stored point · SEAL-01</div>
                  <div className="serif text-[19px] font-semibold tnum leading-snug mt-0.5">E {fmtCoord(sel.at.x)}</div>
                  <div className="serif text-[19px] font-semibold tnum leading-snug">N {fmtCoord(sel.at.y)}</div>
                  <div className="mono text-[8.5px] text-mute mt-0.5">σ {sel.sigmaM} m standard error</div>
                </div>
                <div className="flex flex-col items-end justify-between">
                  <div className="text-right">
                    <div className="mono text-[8.5px] uppercase tracking-[0.12em] text-faint">confidence</div>
                    <div className={cn("serif text-[30px] font-semibold tnum leading-none",
                      sel.confidence >= 0.8 ? "text-ok" : sel.confidence >= 0.5 ? "text-warn" : "text-crit")}>
                      {fmtPct(sel.confidence, 0)}
                    </div>
                  </div>
                  <Meter v={sel.confidence} tone={sel.confidence >= 0.8 ? "ok" : sel.confidence >= 0.5 ? "warn" : "crit"} w={120} h={4} />
                </div>
              </div>

              <LocalPlaneMap
                className="h-[188px] mt-3"
                compact
                scene={scene}
                focus={sel.at}
                trails={selTrails}
                decision={{ at: sel.at, sigmaM: sel.sigmaM, label: `STORED · σ ${sel.sigmaM} m` }}
                fitKey={sel.id}
              />

              <div className="mt-3 border-t hairline pt-2">
                <KV k="median visit drift" v={sel.driftM > 0 ? fmtM(sel.driftM, 1) : "—"} tone={sel.driftM > 10 ? "warn" : undefined} />
                <KV k="field visits on record" v={`${sel.visits} (${selVisits.length} in window)`} />
                <KV k="last verified" v={sel.lastVerified === "never" ? "never" : `${sel.lastVerified} · ${sel.lastVerifiedDays} d ago`} />
                <KV k="sources" v={sel.sources.join(" + ")} />
              </div>

              <p className="text-[11.5px] text-ink2 leading-snug border-t hairline mt-1 pt-2">{sel.note}</p>

              {sel.contradictions.length > 0 && (
                <div className="mt-2.5 border border-plum/45 bg-plum-soft/50 px-2.5 py-2">
                  <div className="mono text-[8.5px] uppercase tracking-[0.12em] text-plum mb-1">contradictions on record</div>
                  {sel.contradictions.map((c, i) => (
                    <div key={i} className="flex gap-1.5 text-[11px] text-ink2 leading-snug py-px">
                      <span className="mono text-[9px] text-plum mt-0.5 shrink-0">{i + 1}.</span> {c}
                    </div>
                  ))}
                </div>
              )}

              <div className="mt-3 border-t hairline pt-2">
                <div className="mono text-[8.5px] uppercase tracking-[0.12em] text-faint mb-1">evidence ledger — this window</div>
                {selVisits.length === 0 && <div className="mono text-[9.5px] text-mute py-1">no visits in replay window</div>}
                {selVisits.map((v) => (
                  <div key={v.id} className="flex items-center gap-2 py-1 border-b border-line/60 last:border-0">
                    <Ring v={v.quality} size={26} />
                    <span className="min-w-0 flex-1">
                      <span className="block mono text-[9px] text-ink">{v.id} · {v.day.slice(0, 6)} {v.ts} · {v.officer}</span>
                      <span className="block mono text-[8px] text-mute truncate">{v.note}</span>
                    </span>
                    <Tag tone={OUTCOME_TONE[v.outcome]}>{v.outcome}</Tag>
                  </div>
                ))}
              </div>

              <div className="mt-3 flex gap-1.5">
                <button onClick={() => queueRever(sel)}
                  className="flex-1 flex items-center justify-center gap-1.5 border border-accent-deep text-accent-deep bg-accent-faint hover:bg-accent-soft mono text-[10px] uppercase tracking-[0.08em] py-2 transition-colors">
                  <FilePlus2 size={12} /> Queue reverification
                </button>
                <button onClick={() => go("evidence")}
                  className="flex-1 flex items-center justify-center gap-1.5 border hairline hover:border-line2 text-ink2 mono text-[10px] uppercase tracking-[0.08em] py-2 transition-colors">
                  <Footprints size={12} /> Open evidence
                </button>
              </div>
            </Panel>
          )}
        </div>
      </div>
    </div>
  );
}
