import { useMemo, useState } from "react";
import { Check, UserCheck } from "lucide-react";
import { fetchCases, fetchPlaces, useQuery } from "@/lib/api";
import { useSession } from "@/lib/session";
import type { CaseKind, Priority, VerifyCase } from "@/lib/types";
import { cn, fmtCoord, fmtM, fmtScore } from "@/lib/utils";
import { KIND_LABEL, KIND_TONE, KV, Meter, Panel, ReasonCode, Sec, Tag } from "@/components/u";
import { ViewHead } from "@/components/Shell";

const KINDS: CaseKind[] = ["VERIFY_FIRST", "REVERIFICATION", "CONTESTED", "MOVED_SUSPECTED", "UNPLACEABLE"];
const PRIOS: (Priority | "ALL")[] = ["ALL", "P1", "P2", "P3"];

type CaseOutcome = "CONFIRMED" | "MOVED" | "REFUTED";

export default function VerifyQueue() {
  const { data: cases } = useQuery(fetchCases);
  const { data: places } = useQuery(fetchPlaces);
  const { casePatches, patchCase, extraCases, notify } = useSession();
  const [kind, setKind] = useState<CaseKind | "ALL">("ALL");
  const [prio, setPrio] = useState<Priority | "ALL">("ALL");
  const [showClosed, setShowClosed] = useState(false);
  const [selId, setSelId] = useState<string | null>(null);

  const all = useMemo(() => [...extraCases, ...(cases ?? [])], [extraCases, cases]);

  const filtered = useMemo(() => {
    return all.filter((c) => {
      const p = casePatches[c.id];
      if (!showClosed && p?.closed) return false;
      if (showClosed && !p?.closed) return false;
      if (kind !== "ALL" && c.kind !== kind) return false;
      if (prio !== "ALL" && c.priority !== prio) return false;
      return true;
    });
  }, [all, casePatches, kind, prio, showClosed]);

  const sel: VerifyCase | null = filtered.find((c) => c.id === selId) ?? filtered[0] ?? null;
  const selPatch = sel ? casePatches[sel.id] : undefined;
  const selPlace = sel?.placeId ? places?.find((p) => p.id === sel.placeId) : null;

  if (!cases || !places) return <div className="mono text-[11px] text-mute p-8">loading queue…</div>;

  const openCount = all.filter((c) => !casePatches[c.id]?.closed).length;

  const close = (c: VerifyCase, outcome: CaseOutcome) => {
    patchCase(c.id, { closed: true, outcome, assignee: casePatches[c.id]?.assignee ?? "OPR K. Deshmukh" },
      `outcome ${outcome} · ${c.placeLabel.slice(0, 40)}`);
    notify(`${c.id} closed · ${outcome}`);
  };

  return (
    <div className="max-w-[1500px] mx-auto">
      <ViewHead
        title="Verify queue"
        note="cases the evidence cannot settle alone — routed to the field, not averaged away"
        right={
          <>
            <Tag tone="accent">{openCount} open</Tag>
            <button onClick={() => setShowClosed(!showClosed)}
              className={cn("mono text-[9px] uppercase tracking-[0.08em] border px-2 py-1 transition-colors",
                showClosed ? "border-ink bg-ink text-paper" : "hairline bg-raised text-mute hover:text-ink")}>
              {showClosed ? "closed tray" : "show closed"}
            </button>
          </>
        }
      />

      {/* kind tabs */}
      <div className="flex flex-wrap items-center gap-1.5 mb-1.5">
        {(["ALL", ...KINDS] as const).map((k) => {
          const n = k === "ALL" ? openCount : all.filter((c) => c.kind === k && !casePatches[c.id]?.closed).length;
          return (
            <button key={k} onClick={() => setKind(k)}
              className={cn("mono text-[9px] uppercase tracking-[0.06em] border px-2 py-1 transition-colors",
                kind === k ? "border-ink bg-ink text-paper" : "hairline bg-raised text-mute hover:text-ink")}>
              {k === "ALL" ? "all" : KIND_LABEL[k]} · {n}
            </button>
          );
        })}
      </div>
      <div className="flex flex-wrap items-center gap-1.5 mb-3">
        <span className="mono text-[8.5px] uppercase tracking-[0.1em] text-faint">priority</span>
        {PRIOS.map((p) => (
          <button key={p} onClick={() => setPrio(p)}
            className={cn("mono text-[9px] border px-1.5 py-0.5 transition-colors",
              prio === p ? "border-accent-deep bg-accent-faint text-accent-deep" : "hairline bg-raised text-mute hover:text-ink")}>
            {p}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-12 gap-3">
        {/* case list */}
        <Panel className="col-span-12 xl:col-span-7 px-3 py-2.5 self-start">
          <Sec no="01" title={showClosed ? `Closed cases · ${filtered.length}` : `Open cases · ${filtered.length}`}
            right={<span className="mono text-[8.5px] text-faint">age · score · sla burn</span>} />
          <div className="divide-y divide-line">
            {filtered.map((c) => {
              const p = casePatches[c.id];
              const active = sel?.id === c.id;
              const sla = c.slaHoursLeft / c.slaHoursTotal;
              const slaTone = p?.closed ? "mute" : sla < 0.25 ? "crit" : sla < 0.5 ? "warn" : "ink";
              return (
                <button key={c.id} onClick={() => setSelId(c.id)}
                  className={cn("w-full text-left px-1.5 -mx-1.5 py-2 transition-colors grid grid-cols-[58px_112px_1fr_44px_120px] gap-2 items-center",
                    active ? "bg-accent-faint/60" : "hover:bg-panel", p?.closed && "opacity-55")}>
                  <span className="mono text-[10px] font-semibold">{c.id}</span>
                  <span className="flex flex-col items-start gap-0.5">
                    <Tag tone={KIND_TONE[c.kind]}>{KIND_LABEL[c.kind]}</Tag>
                    <span className={cn("mono text-[8.5px]", c.priority === "P1" ? "text-accent-deep font-semibold" : "text-mute")}>{c.priority}</span>
                  </span>
                  <span className="min-w-0">
                    <span className="block text-[11.5px] font-medium truncate">{c.placeLabel}</span>
                    <span className="block mono text-[8.5px] text-faint truncate">{c.rawAddress}</span>
                    <span className="flex gap-1 mt-0.5 flex-wrap">
                      {c.reasonCodes.slice(0, 3).map((r) => <ReasonCode key={r} code={r} />)}
                    </span>
                    {p?.closed && <span className="mono text-[8.5px] text-ok">CLOSED · {p.outcome} · {p.assignee}</span>}
                  </span>
                  <span className="mono text-[11px] tnum text-right">{c.score !== undefined ? fmtScore(c.score) : "—"}</span>
                  <span>
                    <span className="flex justify-between mono text-[8.5px] text-mute">
                      <span>{c.ageDays}d old</span>
                      <span className={cn("tnum", slaTone === "crit" && "text-crit font-semibold")}>{c.slaHoursLeft}h left</span>
                    </span>
                    <Meter v={sla} tone={slaTone} w="100%" h={3} />
                  </span>
                </button>
              );
            })}
            {filtered.length === 0 && (
              <div className="py-10 text-center mono text-[10px] uppercase tracking-[0.12em] text-mute">
                {showClosed ? "no cases closed this session" : "queue clear for this filter"}
              </div>
            )}
          </div>
        </Panel>

        {/* detail */}
        <div className="col-span-12 xl:col-span-5 self-start">
          {sel && (
            <Panel className="px-3.5 py-3 rise" key={sel.id}>
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <h2 className="serif text-[18px] font-semibold leading-tight">{sel.id} — {sel.placeLabel}</h2>
                  <div className="mono text-[9px] text-mute mt-0.5 uppercase tracking-[0.06em]">{sel.rawAddress}</div>
                </div>
                <Tag tone={KIND_TONE[sel.kind]}>{KIND_LABEL[sel.kind]}</Tag>
              </div>

              {sel.at && (
                <div className="grid grid-cols-2 gap-3 mt-3 border-t hairline pt-2.5">
                  <div>
                    <div className="mono text-[8.5px] uppercase tracking-[0.12em] text-faint">candidate point · SEAL-01</div>
                    <div className="serif text-[17px] font-semibold tnum leading-snug mt-0.5">E {fmtCoord(sel.at.x)}</div>
                    <div className="serif text-[17px] font-semibold tnum leading-snug">N {fmtCoord(sel.at.y)}</div>
                    <div className="mono text-[8.5px] text-mute">σ {sel.sigmaM} m</div>
                  </div>
                  <div className="border-l hairline pl-3">
                    <KV k="resolver score" v={sel.score !== undefined ? fmtScore(sel.score) : "—"} />
                    <KV k="margin" v={sel.margin !== undefined ? sel.margin.toFixed(2) : "—"} />
                    <KV k="sla" v={`${sel.slaHoursLeft}h / ${sel.slaHoursTotal}h`} tone={sel.slaHoursLeft < 12 && !selPatch?.closed ? "crit" : undefined} />
                    {selPlace && <KV k="memory record" v={selPlace.id} />}
                  </div>
                </div>
              )}

              <div className="mt-2.5 border-t hairline pt-2">
                <div className="mono text-[8.5px] uppercase tracking-[0.12em] text-faint mb-1">reason codes</div>
                <div className="flex flex-wrap gap-1">
                  {sel.reasonCodes.map((r) => <ReasonCode key={r} code={r} />)}
                </div>
              </div>

              <div className="mt-2.5 border-l-2 border-accent bg-accent-faint/50 px-2.5 py-2">
                <div className="mono text-[8.5px] uppercase tracking-[0.12em] text-accent-deep mb-0.5">recommended field action</div>
                <p className="text-[11.5px] text-ink2 leading-snug">{sel.recommendation}</p>
              </div>

              {selPlace && (
                <div className="mt-2.5 border hairline bg-panel px-2.5 py-2 flex items-center justify-between gap-3">
                  <div className="min-w-0">
                    <div className="mono text-[8.5px] uppercase tracking-[0.1em] text-faint">memory record</div>
                    <div className="text-[11.5px] font-medium truncate">{selPlace.label}</div>
                    <div className="mono text-[8.5px] text-mute">
                      conf {(selPlace.confidence * 100).toFixed(0)}% · drift {fmtM(selPlace.driftM, 1)} · verified {selPlace.lastVerified}
                    </div>
                  </div>
                  <Tag tone={selPlace.state === "CONTESTED" ? "plum" : selPlace.state === "STABLE" ? "ok" : "warn"}>{selPlace.state}</Tag>
                </div>
              )}

              {selPatch?.closed ? (
                <div className="mt-3 border border-ok/50 bg-ok-soft/60 px-2.5 py-2 rise">
                  <div className="mono text-[9.5px] font-semibold text-ok tracking-[0.06em]">✓ CASE CLOSED — {selPatch.outcome}</div>
                  <div className="mono text-[8.5px] text-mute mt-0.5">by {selPatch.assignee} · written to audit ledger</div>
                </div>
              ) : (
                <div className="mt-3 space-y-1.5">
                  <button
                    onClick={() => {
                      patchCase(sel.id, { assignee: "OPR K. Deshmukh" }, `assigned to OPR K. Deshmukh`);
                      notify(`${sel.id} assigned to you`);
                    }}
                    className="w-full flex items-center justify-center gap-1.5 border hairline hover:border-line2 text-ink2 mono text-[10px] uppercase tracking-[0.08em] py-2 transition-colors"
                  >
                    <UserCheck size={12} />
                    {selPatch?.assignee ? `assigned · ${selPatch.assignee}` : "Assign to me"}
                  </button>
                  <div className="grid grid-cols-3 gap-1.5">
                    {(["CONFIRMED", "MOVED", "REFUTED"] as CaseOutcome[]).map((o) => (
                      <button key={o} onClick={() => close(sel, o)}
                        className={cn("flex items-center justify-center gap-1 border mono text-[9.5px] uppercase tracking-[0.06em] py-2 transition-colors",
                          o === "CONFIRMED" ? "border-ok/60 text-ok bg-ok-soft/50 hover:bg-ok-soft" :
                          o === "MOVED" ? "border-warn/60 text-warn bg-warn-soft/50 hover:bg-warn-soft" :
                          "border-crit/60 text-crit bg-crit-soft/50 hover:bg-crit-soft")}>
                        <Check size={11} /> {o}
                      </button>
                    ))}
                  </div>
                  <div className="mono text-[8.5px] text-faint text-center pt-0.5">recording an outcome closes the case and feeds place memory</div>
                </div>
              )}
            </Panel>
          )}
        </div>
      </div>
    </div>
  );
}
