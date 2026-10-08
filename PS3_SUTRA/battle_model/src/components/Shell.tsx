import { useEffect, useState } from "react";
import {
  Activity,
  ClipboardCheck,
  Crosshair,
  Footprints,
  MapPinned,
  ScrollText,
  type LucideIcon,
} from "lucide-react";
import { cn, fmtInt } from "@/lib/utils";
import { fmtWhen } from "@/lib/utils";
import { fetchHealth, setAsOf as setApiAsOf, useQuery } from "@/lib/api";
import { useSession } from "@/lib/session";
import { Dot, Failed, Tag } from "./u";

export type ViewId = "overview" | "resolver" | "places" | "evidence" | "queue" | "method";

const NAV: { id: ViewId; no: string; label: string; icon: LucideIcon; sub: string }[] = [
  { id: "overview", no: "01", label: "Overview", icon: Activity, sub: "system & flow" },
  { id: "resolver", no: "02", label: "Resolver", icon: Crosshair, sub: "resolve & decide" },
  { id: "places", no: "03", label: "Places", icon: MapPinned, sub: "memory graph" },
  { id: "evidence", no: "04", label: "Field Evidence", icon: Footprints, sub: "visits & evidence" },
  { id: "queue", no: "05", label: "Verify Queue", icon: ClipboardCheck, sub: "field tasks" },
  { id: "method", no: "06", label: "Method / Trust", icon: ScrollText, sub: "how it decides" },
];

function LiveClock() {
  const [t, setT] = useState("");
  useEffect(() => {
    const f = () => {
      const d = new Date();
      const p = (n: number) => String(n).padStart(2, "0");
      setT(`${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`);
    };
    f();
    const id = setInterval(f, 1000);
    return () => clearInterval(id);
  }, []);
  return <span className="mono text-[11px] text-ink tnum">{t}</span>;
}

export default function Shell({
  view,
  setView,
  queueCount,
  children,
}: {
  view: ViewId;
  setView: (v: ViewId) => void;
  queueCount: number;
  children: React.ReactNode;
}) {
  const { asOf, setAsOf, defaultAsOf, adoptCut, notices, dismiss, reviewer, setReviewer } = useSession();
  const { data: health, loading, error, reload } = useQuery(fetchHealth, []);
  const current = NAV.find((n) => n.id === view)!;

  /* the service tells the workbench its own cut; the workbench never invents one */
  useEffect(() => {
    if (health?.as_of_cut) adoptCut(health.as_of_cut);
  }, [health?.as_of_cut, adoptCut]);
  useEffect(() => {
    setApiAsOf(asOf || null);           // every read below is answered against this cut
  }, [asOf]);

  const store = health?.store;
  const counts = store?.counts as Record<string, number> | undefined;
  const pack = health?.packs?.find((p) => !p.stale) || health?.packs?.[0];
  const mode = health ? "LIVE RUNTIME" : loading ? "CONNECTING" : "UNREACHABLE";

  if (!health && (loading || error)) {
    return (
      <div className="flex h-full items-center justify-center bg-paper p-6">
        <div className="max-w-[560px] w-full">
          {error ? (
            <>
              <Failed what="the SUTRA service" error={error} onRetry={reload} />
              <p className="mono text-[9.5px] text-mute mt-2 leading-relaxed">
                the workbench has no offline copy of its own: evidence, beliefs and the audit trail live in the
                service. start it with <span className="text-ink">python3 tools/serve_runtime.py --port 8000</span>.
              </p>
            </>
          ) : (
            <div className="mono text-[11px] text-mute">connecting to the SUTRA service…</div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full overflow-hidden">
      {/* ---------------- rail ---------------- */}
      <aside className="w-[228px] shrink-0 border-r hairline bg-panel flex flex-col">
        <div className="px-4 pt-4 pb-3 border-b hairline">
          <div className="flex items-center gap-2">
            <span className="grid place-items-center size-[26px] border border-line2 bg-raised">
              <Crosshair size={15} strokeWidth={1.7} className="text-accent-deep" />
            </span>
            <div>
              <div className="text-[15px] font-bold tracking-[0.22em] leading-none">SUTRA</div>
              <div className="mono text-[8px] tracking-[0.18em] text-mute mt-1 uppercase">Evidence-driven geocoder</div>
            </div>
          </div>
          <div className="mt-3 border hairline bg-raised px-2 py-1.5 mono text-[8.5px] text-mute leading-relaxed uppercase tracking-[0.08em]" data-testid="plane-label">
            {health?.versions?.schema_version ? `${health.versions.schema_version} · ` : ""}local metric plane · metres · N↑<br />
            {health?.versions?.rule_version || "—"} · {health?.radius_map_version || "—"}
          </div>
        </div>

        <nav className="flex-1 overflow-y-auto py-2">
          {NAV.map((n) => {
            const active = n.id === view;
            const badge = n.id === "queue" ? queueCount : undefined;
            const Icon = n.icon;
            return (
              <button
                key={n.id}
                onClick={() => setView(n.id)}
                className={cn(
                  "group w-full flex items-center gap-2.5 px-4 py-[7px] text-left border-l-2 -ml-px transition-colors",
                  active ? "border-accent bg-accent-faint/70" : "border-transparent hover:bg-raised",
                )}
              >
                <span className={cn("mono text-[9px]", active ? "text-accent-deep" : "text-faint")}>{n.no}</span>
                <Icon size={14} strokeWidth={1.7} className={cn(active ? "text-accent-deep" : "text-mute group-hover:text-ink2")} />
                <span className="flex-1 min-w-0">
                  <span className={cn("block text-[12px] leading-tight", active ? "font-semibold text-ink" : "text-ink2")}>{n.label}</span>
                  <span className="block mono text-[8px] uppercase tracking-[0.1em] text-faint leading-tight">{n.sub}</span>
                </span>
                {badge !== undefined && (
                  <span className={cn("mono text-[9px] px-1 border", active ? "border-accent/50 text-accent-deep bg-raised" : "hairline text-mute bg-raised")}>
                    {fmtInt(badge)}
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        <div className="border-t hairline px-4 py-3 space-y-2">
          <div className="flex items-center justify-between">
            <span className="mono text-[9px] uppercase tracking-[0.1em] text-mute">Store</span>
            <span className="flex items-center gap-1.5 mono text-[9px] text-ok">
              <Dot tone="ok" blink={mode === "LIVE RUNTIME"} /> {mode}
            </span>
          </div>
          <div className="mono text-[8.5px] text-mute leading-relaxed">
            {counts ? <>{fmtInt(counts.observations)} observations · {fmtInt(counts.belief_versions)} belief versions</> : "—"}
            <br />
            {(() => {
              const att = store?.attestation as unknown as { observations?: { digest?: string } } | undefined;
              return att?.observations?.digest ? <>digest {att.observations.digest.slice(0, 12)}</> : null;
            })()}
          </div>
          <div className="pt-1">
            <label className="mono text-[8px] uppercase tracking-[0.1em] text-faint block" htmlFor="reviewer">reviewer (written to the audit trail)</label>
            <input
              id="reviewer"
              value={reviewer}
              onChange={(e) => setReviewer(e.target.value)}
              spellCheck={false}
              className="mt-1 w-full border hairline bg-raised px-1.5 py-1 mono text-[9.5px] text-ink focus:outline-none focus:border-accent"
            />
          </div>
          <div className="mono text-[8px] text-faint uppercase tracking-[0.1em]">
            {pack ? <>offline pack {pack.pack_version} · age {pack.age_days ?? 0} d</> : "no offline pack"}
          </div>
        </div>
      </aside>

      {/* ---------------- main ---------------- */}
      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-11 shrink-0 border-b hairline bg-panel flex items-center justify-between gap-4 px-5">
          <div className="flex items-baseline gap-2.5 min-w-0">
            <span className="mono text-[9.5px] tracking-[0.16em] text-faint uppercase">SUTRA /</span>
            <span className="mono text-[10.5px] tracking-[0.16em] text-ink uppercase font-semibold">{current.label}</span>
            <span className="mono text-[9px] tracking-[0.1em] text-mute uppercase hidden md:inline">— {current.sub}</span>
          </div>
          <div className="flex items-center gap-3 shrink-0">
            <span className="mono text-[9px] uppercase tracking-[0.1em] text-mute hidden lg:inline">local metric plane · no lat/lng</span>
            <span className="border hairline bg-raised px-2 py-1 flex items-center gap-2" data-testid="asof-control">
              <span className="mono text-[8.5px] uppercase tracking-[0.12em] text-faint">as of</span>
              <span className="mono text-[10px] text-ink tnum">{fmtWhen(asOf)}</span>
              {defaultAsOf && asOf && asOf !== defaultAsOf && (
                <button onClick={() => setAsOf(defaultAsOf)} className="mono text-[8.5px] uppercase tracking-[0.08em] text-accent-deep underline">
                  reset
                </button>
              )}
            </span>
            <span className="border hairline bg-raised px-2 py-1 flex items-center gap-2">
              <span className="mono text-[8.5px] uppercase tracking-[0.12em] text-faint">IST</span>
              <LiveClock />
            </span>
            <span data-testid="runtime-mode">
              <Tag tone={mode === "LIVE RUNTIME" ? "ok" : mode === "UNREACHABLE" ? "crit" : "mute"}>
                <Dot tone={mode === "LIVE RUNTIME" ? "ok" : mode === "UNREACHABLE" ? "crit" : "mute"} blink={mode === "CONNECTING"} />
                {mode}
              </Tag>
            </span>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto bg-paper">
          <div className="p-5 min-h-full">{children}</div>
        </main>
      </div>

      {/* ---------------- notices (real echoes of service responses) ---------------- */}
      {notices.length > 0 && (
        <div className="fixed bottom-5 right-5 z-50 space-y-1.5">
          {notices.map((n) => (
            <div key={n.id}
              className={cn(
                "rise border pl-2 pr-3 py-2 flex items-center gap-2.5 shadow-[4px_4px_0_rgba(33,29,20,0.18)]",
                n.tone === "crit" ? "border-crit bg-crit-soft" : n.tone === "ok" ? "border-ink bg-ink text-paper" : "border-ink bg-ink text-paper",
              )}>
              <span className={cn("block w-1 self-stretch", n.tone === "crit" ? "bg-crit" : n.tone === "ok" ? "bg-ok" : "bg-accent")} />
              <span className="mono text-[10px] tracking-[0.04em]">{n.text}</span>
              <button onClick={() => dismiss(n.id)} className="mono text-[9px] opacity-70 hover:opacity-100">✕</button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/* shared view header */
export function ViewHead({ title, note, right }: { title: string; note: string; right?: React.ReactNode }) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-3 mb-4">
      <div>
        <h1 className="serif text-[21px] font-semibold leading-tight">{title}</h1>
        <p className="mono text-[9.5px] uppercase tracking-[0.12em] text-mute mt-0.5">{note}</p>
      </div>
      {right && <div className="flex items-center gap-2">{right}</div>}
    </div>
  );
}
