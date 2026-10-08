import { useMemo, useState } from "react";
import { Camera, Search, ShieldCheck } from "lucide-react";
import { fetchEvidence, fetchGeometry, fetchTownPlane, useQuery } from "@/lib/api";
import { useSession } from "@/lib/session";
import type { VisitRow } from "@/lib/types";
import { cn, dayOf, fmtInt, fmtRadius, fmtWhen } from "@/lib/utils";
import LocalPlaneMap from "@/components/LocalPlaneMap";
import { Empty, Failed, KV, Loading, OUTCOME_LABEL, OUTCOME_TONE, Panel, POLARITY_TONE, RawCode, Tag } from "@/components/u";
import { ViewHead, type ViewId } from "@/components/Shell";

export default function FieldEvidence({ go }: { go: (v: ViewId) => void }) {
  const { asOf } = useSession();
  const [outcome, setOutcome] = useState<string>("ALL");
  const [polarity, setPolarity] = useState<string>("ALL");
  const [q, setQ] = useState("");
  const [selId, setSelId] = useState<string | null>(null);

  const { data: feed, loading, error, reload } = useQuery(
    () => fetchEvidence({ outcome: outcome === "ALL" ? undefined : outcome, polarity: polarity === "ALL" ? undefined : polarity, q: q || undefined, limit: 150 }),
    [outcome, polarity, q, asOf],
  );

  const items = feed?.items ?? [];
  const sel: VisitRow | null = items.find((v) => v.observation_id === selId) ?? items[0] ?? null;

  const { data: geom } = useQuery(
    () => (sel?.address_id ? fetchGeometry(sel.address_id, "FIELD_NAVIGATION") : Promise.resolve(null)),
    [sel?.address_id, asOf],
  );
  const { data: plane } = useQuery(
    () => (sel?.town_id ? fetchTownPlane(sel.town_id) : Promise.resolve(null)),
    [sel?.town_id, asOf],
  );

  const days = useMemo(() => {
    const m = new Map<string, VisitRow[]>();
    items.forEach((v) => {
      const d = dayOf(v.observed_at);
      const arr = m.get(d) ?? [];
      arr.push(v);
      m.set(d, arr);
    });
    return [...m.entries()];
  }, [items]);

  const facets = feed?.facets;
  const thisAddress = useMemo(
    () => items.filter((v) => v.address_id === sel?.address_id).slice(0, 8),
    [items, sel?.address_id],
  );

  if (loading && !feed) return <Loading what="the evidence feed" />;
  if (error && !feed) return <Failed what="the evidence feed" error={error} onRetry={reload} />;

  return (
    <div className="max-w-[1500px] mx-auto">
      <ViewHead
        title="Field evidence"
        note={`visits as recorded, with the evidence policy's verdict on each · ${fmtInt(feed?.total_matching ?? 0)} rows at this cut`}
        right={
          <>
            <Tag tone="ink">{fmtInt(feed?.count ?? 0)} shown</Tag>
            <Tag tone="ok">negatives never move a coordinate</Tag>
          </>
        }
      />

      <div className="flex flex-wrap items-center gap-1.5 mb-3">
        {(["ALL", "positive", "ambiguous", "negative"] as const).map((p) => (
          <button key={p} data-testid={`polarity-${p.toLowerCase()}`} onClick={() => setPolarity(p)}
            className={cn("mono text-[9px] uppercase tracking-[0.08em] border px-2 py-1 transition-colors",
              polarity === p ? "border-ink bg-ink text-paper" : "hairline bg-raised text-mute hover:text-ink")}>
            {p === "ALL" ? "all polarities" : p}
            {p !== "ALL" && facets?.by_polarity[p] !== undefined && <span className="ml-1 opacity-70 tnum">{facets.by_polarity[p]}</span>}
          </button>
        ))}
        <span className="w-px h-4 bg-line2 mx-1" />
        {["ALL", ...Object.keys(facets?.by_outcome ?? {})].map((o) => (
          <button key={o} onClick={() => setOutcome(o)}
            className={cn("mono text-[9px] uppercase tracking-[0.08em] border px-2 py-1 transition-colors",
              outcome === o ? "border-ink bg-ink text-paper" : "hairline bg-raised text-mute hover:text-ink")}>
            {o === "ALL" ? "all outcomes" : (OUTCOME_LABEL[o] ?? o.replace(/_/g, " "))}
            {o !== "ALL" && <span className="ml-1 opacity-70 tnum">{facets!.by_outcome[o]}</span>}
          </button>
        ))}
        <span className="w-px h-4 bg-line2 mx-1" />
        <div className="flex items-center gap-1.5 border hairline bg-raised px-2 py-1">
          <Search size={11} className="text-mute" />
          <input value={q} onChange={(e) => setQ(e.target.value)} spellCheck={false} placeholder="search observation, agent, remark…"
            className="bg-transparent mono text-[10px] text-ink placeholder:text-faint focus:outline-none w-[200px]" />
        </div>
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
              <div className="border hairline bg-raised">
                {rows.map((v) => (
                  <button key={v.observation_id} onClick={() => setSelId(v.observation_id)}
                    className={cn("w-full grid grid-cols-[64px_1fr_112px_78px_60px] items-center gap-2 px-2.5 py-[6px] text-left border-b border-line/60 last:border-0 transition-colors",
                      sel?.observation_id === v.observation_id ? "bg-accent-faint/60" : "hover:bg-panel")}>
                    <span className="mono text-[9.5px] text-mute">{fmtWhen(v.observed_at).slice(7, 12)}</span>
                    <span className="min-w-0">
                      <span className="block text-[11.5px] truncate">{v.address_label ?? v.address_id}</span>
                      <span className="block mono text-[8.5px] text-faint truncate">{v.observation_id} · {v.agent_id ?? "—"} · {v.device_id ?? "—"}</span>
                    </span>
                    <Tag tone={OUTCOME_TONE[v.outcome] ?? "ink"} className="justify-center">{OUTCOME_LABEL[v.outcome] ?? v.outcome}</Tag>
                    <Tag tone={POLARITY_TONE[v.polarity] ?? "ink"} className="justify-center">{v.polarity}</Tag>
                    <span className="mono text-[10px] text-right tnum text-ink2">{v.evidence.weight !== null ? v.evidence.weight.toFixed(3) : "0.000"}</span>
                  </button>
                ))}
              </div>
            </div>
          ))}
          {items.length === 0 && <Empty msg="no visits match" />}
          {feed?.next_cursor && (
            <div className="mono text-[9px] text-faint py-1">
              showing {items.length} of {fmtInt(feed.total_matching)} — narrow the filters to reach the rest
            </div>
          )}
        </div>

        {/* detail */}
        <div className="col-span-12 xl:col-span-5 self-start">
          {sel && (
            <Panel className="px-3.5 py-3 rise" key={sel.observation_id}>
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <h2 className="serif text-[18px] font-semibold leading-tight">{sel.observation_id}</h2>
                  <div className="mono text-[9px] text-mute mt-0.5">
                    {fmtWhen(sel.observed_at)} · observed {sel.observed_at}<br />
                    {sel.agent_id ?? "—"} · {sel.device_id ?? "—"} · local seq {sel.local_seq ?? "—"}
                  </div>
                </div>
                <Tag tone={OUTCOME_TONE[sel.outcome] ?? "ink"}>{OUTCOME_LABEL[sel.outcome] ?? sel.outcome}</Tag>
              </div>

              <div className="mt-2.5 border hairline bg-paper px-2.5 py-2">
                <div className="mono text-[8.5px] uppercase tracking-[0.12em] text-faint mb-1">the address this visit speaks about</div>
                <div className="text-[11.5px] leading-snug">{sel.address_label ?? "—"}</div>
                <div className="mono text-[9px] text-mute mt-0.5">{sel.address_id} · {sel.place_id ?? "—"} · {sel.town_id ?? "—"}</div>
              </div>

              <LocalPlaneMap className="h-[196px] mt-3" compact plane={plane} geometry={geom}
                focus={sel.x !== null && sel.y !== null ? { x: sel.x, y: sel.y } : { x: sel.captured.x ?? 0, y: sel.captured.y ?? 0 }}
                selectedId={geom?.points?.find((p) => p.kind === "candidate" && p.selected)?.id ?? null}
                fitKey={sel.observation_id} />

              <div className="mt-3 border-t hairline pt-2">
                <KV k="polarity" v={sel.polarity} tone={POLARITY_TONE[sel.polarity]} />
                <KV k="coordinate claim" v={sel.coordinate_claim ? "yes — a claim about the address" : "no — device position only"} />
                <KV k="dwell at point" v={sel.dwell_s !== null ? `${Math.round(sel.dwell_s)} s` : "—"} />
                <KV k="device accuracy" v={fmtRadius(sel.captured.gps_accuracy_m)} />
                <KV k="evidence weight" v={sel.evidence.weight !== null ? sel.evidence.weight.toFixed(4) : "—"} />
                <KV k="evidence class" v={sel.evidence.evidence_class ?? "—"} />
                <KV k="contributes" v={sel.contributes.replace(/_/g, " ")} tone={sel.contributes === "negative_doubt" ? "warn" : sel.contributes === "positive_support" ? "ok" : undefined} />
                <KV k="policy" v={sel.policy_version ?? "—"} />
                <KV k="duplicate claim of" v={sel.duplicate_claim_of ?? "—"} />
              </div>

              {!sel.coordinate_claim && (
                <div className="mt-2 border-l-2 border-crit bg-crit-soft/50 px-2.5 py-1.5 mono text-[9.5px] text-ink2 leading-snug">
                  {sel.captured.note}
                  {sel.captured.x !== null ? <> · captured at E {sel.captured.x.toFixed(1)} N {(sel.captured.y ?? 0).toFixed(1)}</> : null}
                </div>
              )}

              <div className="mt-2.5 border-t hairline pt-2">
                <div className="mono text-[8.5px] uppercase tracking-[0.12em] text-faint mb-1">what the policy said</div>
                <div className="flex flex-wrap gap-1">
                  {sel.evidence.reason_codes.map((c) => <RawCode key={c} code={c} />)}
                </div>
                <div className="mono text-[9px] text-mute mt-1.5 flex items-center gap-1.5">
                  <ShieldCheck size={11} className="text-ok" />
                  {sel.polarity === "negative"
                    ? "a negative can only widen uncertainty and ask for verification — it never relocates the address"
                    : sel.polarity === "ambiguous"
                      ? "an ambiguous visit counts for what it witnessed and nothing more"
                      : "a positive counts only with independence: one visit is never enough to confirm"}
                </div>
              </div>

              {sel.remark && (
                <div className="mt-2.5 border-t hairline pt-2">
                  <div className="mono text-[8.5px] uppercase tracking-[0.12em] text-faint mb-1">collector's remark, verbatim</div>
                  <div className="text-[11.5px] text-ink2">“{sel.remark}”</div>
                </div>
              )}

              <div className="mt-2.5 border-t hairline pt-2">
                <div className="mono text-[8.5px] uppercase tracking-[0.12em] text-faint mb-1">
                  media attached ({sel.media.length})
                </div>
                {sel.media.length === 0 && <div className="mono text-[9.5px] text-mute">none</div>}
                {sel.media.map((m) => (
                  <div key={m.sha256} className="flex items-center gap-1.5 mono text-[9.5px] text-ink2">
                    <Camera size={11} className="text-mute" /> {m.kind} · sha256 {m.sha256.slice(0, 12)}…
                  </div>
                ))}
              </div>

              {thisAddress.length > 1 && (
                <div className="mt-2.5 border-t hairline pt-2">
                  <div className="mono text-[8.5px] uppercase tracking-[0.12em] text-faint mb-1">
                    other visits on {sel.address_id} in this view
                  </div>
                  {thisAddress.filter((v) => v.observation_id !== sel.observation_id).map((v) => (
                    <button key={v.observation_id} onClick={() => setSelId(v.observation_id)}
                      className="w-full flex items-center gap-2 py-1 text-left border-b border-line/60 last:border-0 hover:bg-panel">
                      <span className="mono text-[9px] text-mute w-[92px] shrink-0">{fmtWhen(v.observed_at)}</span>
                      <span className="mono text-[9px] text-ink2 flex-1 truncate">{v.observation_id}</span>
                      <Tag tone={POLARITY_TONE[v.polarity] ?? "ink"}>{v.polarity}</Tag>
                    </button>
                  ))}
                </div>
              )}

              <button onClick={() => go("places")}
                className="mt-3 w-full flex items-center justify-center gap-1.5 border hairline hover:border-line2 text-ink2 mono text-[10px] uppercase tracking-[0.08em] py-2 transition-colors">
                open the place record
              </button>
            </Panel>
          )}
        </div>
      </div>
    </div>
  );
}
