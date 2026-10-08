import { ArrowRight } from "lucide-react";
import { fetchEvidence, fetchHealth, fetchMethodTrust, fetchOverview, fetchTasks, useQuery } from "@/lib/api";
import { useSession } from "@/lib/session";
import { cn, fmtInt, fmtM, fmtPct, fmtWhen } from "@/lib/utils";
import { Dot, Failed, KV, Loading, Meter, OUTCOME_LABEL, OUTCOME_TONE, Panel, POLARITY_TONE, Sec, Tag } from "@/components/u";
import { ViewHead, type ViewId } from "@/components/Shell";

function Kpi({
  label, value, unit, sub, tone = "ink",
}: { label: string; value: string; unit?: string; sub: React.ReactNode; tone?: "ink" | "accent" }) {
  return (
    <Panel className={cn("px-3.5 py-3 flex flex-col justify-between min-h-[104px]", tone === "accent" && "border-accent/45")}>
      <div className="mono text-[9px] uppercase tracking-[0.12em] text-mute">{label}</div>
      <div className="flex items-baseline gap-1.5 mt-1">
        <span className={cn("serif text-[30px] leading-none font-semibold tnum", tone === "accent" && "text-accent-deep")}>{value}</span>
        {unit && <span className="mono text-[10px] text-mute">{unit}</span>}
      </div>
      <div className="mono text-[9px] text-mute mt-1.5 leading-snug">{sub}</div>
    </Panel>
  );
}

export default function Overview({ go, queueCount }: { go: (v: ViewId) => void; queueCount: number }) {
  const { asOf, notify } = useSession();
  const { data: ov, loading, error, reload } = useQuery(fetchOverview, [asOf]);
  const { data: method } = useQuery(fetchMethodTrust, []);
  const { data: feed } = useQuery(() => fetchEvidence({ limit: 6 }), [asOf]);
  const { data: tasks } = useQuery(() => fetchTasks({ state: "open", limit: 1 }), [asOf]);
  const { data: health } = useQuery(fetchHealth, []);

  if (loading && !ov) return <Loading what="the operational overview" />;
  if (error && !ov) return <Failed what="the operational overview" error={error} onRetry={reload} />;
  if (!ov) return null;

  const tiers = ov.addresses.by_tier || {};
  const reasons = ov.workload.by_reason || [];
  const tierRows: [string, number][] = Object.entries(tiers).sort((a, b) => b[1] - a[1]);

  return (
    <div className="max-w-[1440px] mx-auto">
      <ViewHead
        title="Operations overview"
        note={`as of ${fmtWhen(ov.as_of)} · operational counts read from the store · computed ${fmtWhen(ov.computed_at)}`}
        right={
          <>
            <Tag tone="ok"><Dot tone="ok" /> live service</Tag>
            <Tag tone={ov.data_freshness.available_offline ? "cool" : "mute"}>
              offline packs {ov.data_freshness.available_offline ? "available" : "—"}
            </Tag>
          </>
        }
      />

      {/* KPI row */}
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-3">
        <Kpi label="Addresses indexed" value={fmtInt(ov.addresses.indexed)}
          sub={<span>{fmtInt(ov.addresses.warm)} warm · {fmtInt(ov.addresses.cold)} cold at this cut</span>} />
        <Kpi label="Answered with a location" value={fmtInt(ov.addresses.with_location)} tone="accent"
          sub={<span>{tierRows.map(([t, n]) => `${t.toLowerCase()} ${fmtInt(n)}`).join(" · ")}</span>} />
        <Kpi label="Cases needing the field" value={fmtInt(ov.workload.active_cases)}
          sub={<span>{reasons.map((r) => `${r.count} × ${r.cause.replace(/_/g, " ").toLowerCase()}`).join(" · ") || "none open"}</span>} />
        <Kpi label="Field visits recorded" value={fmtInt(ov.field_activity.visits_recorded)}
          sub={<span>{fmtInt(ov.field_activity.visits_last_30_days)} in the last {ov.field_activity.window_days} days · newest {fmtWhen(ov.field_activity.latest_visit)}</span>} />
      </div>

      {/* frozen evaluation + queue */}
      <div className="grid grid-cols-12 gap-3 mt-3">
        <Panel className="col-span-12 xl:col-span-7 px-3.5 py-3">
          <Sec no="A" title="Answer quality — the three frozen populations"
            right={<span className="mono text-[9px] text-mute">hit within 500 m · n stated</span>} />
          <div className="pt-2.5 space-y-2.5">
            {(method?.populations ?? []).map((p) => (
              <div key={p.key}>
                <div className="flex items-baseline justify-between gap-3">
                  <span className="text-[11.5px] font-medium">{p.name}</span>
                  <span className="mono text-[11px] tnum">
                    {p.hit_500m !== null ? fmtPct(p.hit_500m, 2) : "—"} <span className="text-mute">· n={p.n} · median {p.median_m !== null ? fmtM(p.median_m, 1) : "—"}</span>
                  </span>
                </div>
                <Meter v={p.hit_500m ?? 0} tone={p.key === "cold" ? "cool" : p.key === "warm" ? "accent" : "ink"} w="100%" h={4} />
                <div className="mono text-[8.5px] text-mute mt-1 leading-snug">{p.caption}</div>
              </div>
            ))}
            {!method && <div className="mono text-[10px] text-mute">reading the frozen evaluation…</div>}
          </div>
          <p className="text-[11px] text-ink2 leading-snug mt-3 border-t hairline pt-2">{method?.population_note}</p>
          <p className="mono text-[8.5px] text-faint mt-1.5 leading-relaxed">
            no single blended accuracy figure is published, and none is claimed for every address.
          </p>
        </Panel>

        <div className="col-span-12 xl:col-span-5 grid grid-rows-2 gap-3">
          <Panel className="px-3.5 py-3 cursor-pointer hover:border-line2 transition-colors"
            onClick={() => { notify("opening the verification queue"); go("queue"); }}>
            <Sec no="B" title="Active verification queue"
              right={<span className="mono text-[9px] text-accent-deep flex items-center gap-1">open workbench <ArrowRight size={10} /></span>} />
            <div className="pt-1.5 divide-y divide-line">
              {reasons.map((r) => (
                <div key={r.cause} className="flex items-center gap-2 py-[6px]">
                  <Tag tone={r.cause === "CONTESTED" ? "plum" : "warn"} className="w-[142px] justify-center">{r.cause.replace(/_/g, " ").toLowerCase()}</Tag>
                  <span className="text-[10.5px] text-mute flex-1 truncate">{r.detail}</span>
                  <span className="mono text-[11px] tnum">{fmtInt(r.count)}</span>
                </div>
              ))}
              {(tasks?.facets?.by_state?.resolved ?? 0) > 0 && (
                <div className="py-[6px] mono text-[9.5px] text-mute">
                  {fmtInt(tasks!.facets.by_state.resolved)} resolved in the store
                </div>
              )}
              {reasons.length === 0 && <div className="mono text-[10px] text-mute py-2">no open cases</div>}
            </div>
          </Panel>

          <Panel className="px-3.5 py-3">
            <Sec no="C" title="Workload by town" right={<span className="mono text-[9px] text-mute">indexed · needs field</span>} />
            <div className="pt-2 space-y-2">
              {ov.towns.map((t) => (
                <div key={t.town_id} className="flex items-center gap-3">
                  <span className="mono text-[10.5px] font-semibold w-8">{t.town_id}</span>
                  <Meter v={t.addresses / Math.max(...ov.towns.map((x) => x.addresses))} tone="ink" w="100%" h={4} />
                  <span className="mono text-[10px] tnum w-16 text-right">{fmtInt(t.addresses)}</span>
                  <span className="mono text-[10px] tnum w-14 text-right text-warn">{fmtInt(t.needs_review)}</span>
                </div>
              ))}
            </div>
            <p className="mono text-[8.5px] text-faint leading-relaxed border-t hairline pt-2 mt-2">
              the queue count in the rail ({fmtInt(queueCount)}) is the same number, read from the task store.
            </p>
          </Panel>
        </div>
      </div>

      {/* evidence + system */}
      <div className="grid grid-cols-12 gap-3 mt-3">
        <Panel className="col-span-12 xl:col-span-7 px-3.5 py-3">
          <Sec no="D" title="Newest field evidence"
            right={<button onClick={() => go("evidence")} className="mono text-[9px] text-accent-deep flex items-center gap-1 hover:underline">full feed <ArrowRight size={10} /></button>} />
          <div className="pt-1 divide-y divide-line">
            {(feed?.items ?? []).map((v) => (
              <button key={v.observation_id} onClick={() => go("evidence")}
                className="w-full grid grid-cols-[92px_1fr_118px_64px_54px] items-center gap-2 py-[6px] text-left hover:bg-panel transition-colors px-1 -mx-1">
                <span className="mono text-[9.5px] text-mute">{fmtWhen(v.observed_at)}</span>
                <span className="min-w-0">
                  <span className="block text-[11.5px] truncate">{v.address_label ?? v.address_id}</span>
                  <span className="block mono text-[8.5px] text-faint">{v.observation_id} · {v.agent_id ?? "—"} · {v.address_id}</span>
                </span>
                <Tag tone={OUTCOME_TONE[v.outcome] ?? "ink"} className="justify-center">{OUTCOME_LABEL[v.outcome] ?? v.outcome}</Tag>
                <Tag tone={POLARITY_TONE[v.polarity] ?? "ink"} className="justify-center">{v.polarity}</Tag>
                <span className="mono text-[10px] text-right text-ink2 tnum">
                  {v.evidence.weight !== null ? v.evidence.weight.toFixed(3) : "—"}
                </span>
              </button>
            ))}
            {!feed && <div className="mono text-[10px] text-mute py-2">reading the evidence feed…</div>}
            {feed && feed.items.length === 0 && <div className="mono text-[10px] text-mute py-2">no visits at this cut</div>}
          </div>
        </Panel>

        <Panel className="col-span-12 xl:col-span-5 px-3.5 py-3">
          <Sec no="E" title="System health" right={<span className="mono text-[9px] text-mute">every number counted or read</span>} />
          <div className="pt-1.5">
            <KV k="cut (as-of default)" v={fmtWhen(asOf)} />
            <KV k="versions" v={health ? `${health.versions.schema_version} · ${health.rule_version} · ${health.radius_map_version}` : "—"} />
            <KV k="S-Eval reads · tuning uses" v={health ? `${String(health.counters.s_eval_looks ?? "—")} · ${String((health.s_eval_firewall as { tuning_uses?: number }).tuning_uses ?? 0)}` : "—"} />
            <div className="border-t hairline mt-1 pt-1.5">
              <div className="mono text-[8.5px] uppercase tracking-[0.12em] text-faint mb-1">offline packs</div>
              {ov.data_freshness.packs.map((p) => (
                <div key={p.pack_version} className="flex items-center justify-between gap-2 py-[3px]">
                  <span className="mono text-[9.5px] text-ink2 truncate">{p.town_id} · {p.pack_version}</span>
                  <span className={cn("mono text-[9.5px]", p.stale ? "text-warn" : "text-ok")}>
                    {p.age_days.toFixed(1)} d · {p.stale ? "stale" : "fresh"}
                  </span>
                </div>
              ))}
            </div>
            <div className="border-t hairline mt-1 pt-1.5">
              <div className="mono text-[8.5px] uppercase tracking-[0.12em] text-faint mb-1">evidence freshness</div>
              <KV k="newest observation" v={fmtWhen(ov.data_freshness.evidence_newest)} />
              <KV k="evidence rows" v={fmtInt(ov.field_activity.visits_recorded)} />
            </div>
          </div>
          <p className="mono text-[8.5px] text-faint leading-relaxed border-t hairline pt-2 mt-2">
            no latency percentiles, error rates or queue depths are shown: the service does not publish them,
            and the workbench does not estimate them.
          </p>
        </Panel>
      </div>
    </div>
  );
}
