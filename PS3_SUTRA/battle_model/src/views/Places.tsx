import { useEffect, useMemo, useState } from "react";
import { FilePlus2, Footprints, Search, TriangleAlert } from "lucide-react";
import { fetchCase, fetchGeometry, fetchPlace, fetchPlaces, fetchTownPlane, useQuery } from "@/lib/api";
import { useSession } from "@/lib/session";
import type { PlaceRow } from "@/lib/types";
import { cn, fmtCoord, fmtInt, fmtRadius, fmtWhen } from "@/lib/utils";
import LocalPlaneMap from "@/components/LocalPlaneMap";
import { Empty, Failed, KV, Loading, OUTCOME_LABEL, OUTCOME_TONE, Panel, Sec, STATE_TONE, Tag } from "@/components/u";
import { ViewHead, type ViewId } from "@/components/Shell";

const STATES = ["ALL", "CONFIRMED", "WARM", "COLD", "MOVED_SUSPECTED", "CONTESTED"] as const;
const TIERS = ["ALL", "CONFIRMED", "PROBABLE", "APPROXIMATE"] as const;

export default function Places({ go, openTask }: { go: (v: ViewId) => void; openTask?: (taskId: string) => void }) {
  const { asOf, notify } = useSession();
  const [state, setState] = useState<string>("ALL");
  const [tier, setTier] = useState<string>("ALL");
  const [q, setQ] = useState("");
  const [query, setQuery] = useState("");
  const [selId, setSelId] = useState<string | null>(null);

  useEffect(() => {
    const t = window.setTimeout(() => setQuery(q.trim()), 350);
    return () => window.clearTimeout(t);
  }, [q]);

  const { data: list, loading, error, reload } = useQuery(
    () => fetchPlaces({ state: state === "ALL" ? undefined : state, tier: tier === "ALL" ? undefined : tier, q: query || undefined, limit: 60 }),
    [state, tier, query, asOf],
  );

  const rows = list?.items ?? [];
  const sel: PlaceRow | null = rows.find((r) => r.place_id === selId) ?? rows[0] ?? null;

  const { data: detail } = useQuery(
    () => (sel ? fetchPlace(sel.place_id) : Promise.resolve(null)),
    [sel?.place_id, asOf],
  );
  const { data: kase } = useQuery(
    () => (sel ? fetchCase(sel.address_id) : Promise.resolve(null)),
    [sel?.address_id, asOf],
  );
  const { data: geom } = useQuery(
    () => (sel ? fetchGeometry(sel.address_id, "FIELD_NAVIGATION") : Promise.resolve(null)),
    [sel?.address_id, asOf],
  );
  const { data: plane } = useQuery(
    () => (sel?.town_id ? fetchTownPlane(sel.town_id) : Promise.resolve(null)),
    [sel?.town_id, asOf],
  );

  const facets = list?.facets;
  const counts = useMemo(() => {
    const m = new Map<string, number>();
    Object.entries(facets?.by_state ?? {}).forEach(([k, v]) => m.set(k, v));
    return m;
  }, [facets]);

  if (loading && !list) return <Loading what="the place index" />;
  if (error && !list) return <Failed what="the place index" error={error} onRetry={reload} />;

  return (
    <div className="max-w-[1500px] mx-auto">
      <ViewHead
        title="Places"
        note={`address-keyed places under the frozen identity rule ${list?.identity_rule ?? ""} · projection over stored beliefs`}
        right={
          <>
            <Tag tone="ink">{fmtInt(list?.total_matching ?? 0)} matching</Tag>
            <span className="mono text-[9px] text-mute">of {fmtInt(list?.facets ? Object.values(list.facets.by_town).reduce((a, b) => a + b, 0) : 0)} indexed</span>
          </>
        }
      />

      {/* filters */}
      <div className="flex flex-wrap items-center gap-1.5 mb-3">
        {STATES.map((s) => (
          <button key={s} onClick={() => setState(s)}
            className={cn("mono text-[9px] uppercase tracking-[0.08em] border px-2 py-1 transition-colors",
              state === s ? "border-ink bg-ink text-paper" : "hairline bg-raised text-mute hover:text-ink")}>
            {s === "ALL" ? "all states" : s.replace(/_/g, " ").toLowerCase()}
            {s !== "ALL" && counts.get(s) !== undefined && <span className="ml-1 opacity-70 tnum">{counts.get(s)}</span>}
          </button>
        ))}
        <span className="w-px h-4 bg-line2 mx-1" />
        {TIERS.map((t) => (
          <button key={t} onClick={() => setTier(t)}
            className={cn("mono text-[9px] uppercase tracking-[0.08em] border px-2 py-1 transition-colors",
              tier === t ? "border-ink bg-ink text-paper" : "hairline bg-raised text-mute hover:text-ink")}>
            {t === "ALL" ? "all tiers" : t.toLowerCase()}
          </button>
        ))}
        <span className="w-px h-4 bg-line2 mx-1" />
        <div className="flex items-center gap-1.5 border hairline bg-raised px-2 py-1">
          <Search size={11} className="text-mute" />
          <input value={q} onChange={(e) => setQ(e.target.value)} spellCheck={false} placeholder="search label, id, account…"
            className="bg-transparent mono text-[10px] text-ink placeholder:text-faint focus:outline-none w-[210px]" />
        </div>
      </div>

      <div className="grid grid-cols-12 gap-3">
        {/* list */}
        <div className="col-span-12 xl:col-span-7">
          <Panel className="px-3.5 py-3">
            <Sec no="A" title="Place index"
              right={<span className="mono text-[9px] text-mute">{fmtInt(rows.length)} shown · sorted by place id</span>} />
            <div className="pt-1.5 max-h-[620px] overflow-y-auto">
              <div className="grid grid-cols-[1fr_96px_88px_78px_64px] gap-x-3 px-1 mono text-[8.5px] uppercase tracking-[0.08em] text-faint border-b hairline pb-1 sticky top-0 bg-raised">
                <span>place</span><span>state</span><span>tier</span><span className="text-right">radius</span><span className="text-right">visits</span>
              </div>
              {rows.map((p) => (
                <button key={p.place_id} data-testid="place-row" onClick={() => setSelId(p.place_id)}
                  className={cn("w-full grid grid-cols-[1fr_96px_88px_78px_64px] gap-x-3 items-center px-1 py-[6px] text-left border-b border-line/60 transition-colors",
                    sel?.place_id === p.place_id ? "bg-accent-faint/60" : "hover:bg-panel")}>
                  <span className="min-w-0">
                    <span className="block text-[11.5px] truncate">{p.label}</span>
                    <span className="block mono text-[8.5px] text-faint truncate">{p.place_id} · {p.address_id} · {p.town_id} · {p.source ?? "—"}</span>
                  </span>
                  <Tag tone={STATE_TONE[p.state]} className="justify-center">{p.state.replace(/_/g, " ").toLowerCase()}</Tag>
                  <span className={cn("mono text-[9.5px]", p.tier ? "text-ink2" : "text-faint")}>{p.tier ?? "unresolved"}</span>
                  <span className="mono text-[10px] text-right tnum">{fmtRadius(p.coordinate?.radius_m ?? null)}</span>
                  <span className="mono text-[10px] text-right tnum">{p.visits}</span>
                </button>
              ))}
              {rows.length === 0 && <div className="py-8 text-center mono text-[10px] text-mute uppercase tracking-[0.1em]">no records match</div>}
              {list?.next_cursor && (
                <div className="mono text-[9px] text-faint py-2">page 1 of {fmtInt(list.total_matching)} — narrow the search to see the rest</div>
              )}
            </div>
          </Panel>
        </div>

        {/* detail */}
        <div className="col-span-12 xl:col-span-5 space-y-3 self-start">
          {sel && (
            <Panel className="px-3.5 py-3 rise" key={sel.place_id}>
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <h2 className="serif text-[19px] font-semibold leading-tight">{sel.label}</h2>
                  <div className="mono text-[9px] text-mute mt-0.5 uppercase tracking-[0.06em]">
                    {sel.place_id} · {sel.address_id} · {sel.town_id} · {sel.address_type ?? "—"}
                  </div>
                </div>
                <Tag tone={STATE_TONE[sel.state]}>{sel.state.replace(/_/g, " ")}</Tag>
              </div>

              <div className="grid grid-cols-2 gap-3 mt-3 border-t hairline pt-3">
                <div>
                  <div className="mono text-[8.5px] uppercase tracking-[0.12em] text-faint">stored point · {sel.coordinate_space}</div>
                  {sel.coordinate ? (
                    <>
                      <div className="serif text-[19px] font-semibold tnum leading-snug mt-0.5">E {fmtCoord(sel.coordinate.x)}</div>
                      <div className="serif text-[19px] font-semibold tnum leading-snug">N {fmtCoord(sel.coordinate.y)}</div>
                      <div className="mono text-[8.5px] text-mute mt-0.5">
                        radius {fmtRadius(sel.coordinate.radius_m)} · {sel.coordinate.basis ?? "—"} · {sel.coordinate.granularity ?? "—"}
                      </div>
                    </>
                  ) : (
                    <div className="mono text-[10.5px] text-mute mt-1">no coordinate stored for this place</div>
                  )}
                </div>
                <div className="border-l hairline pl-3">
                  <KV k="visits on record" v={fmtInt(sel.visits)} />
                  <KV k="positive visits" v={fmtInt(sel.positives)} />
                  <KV k="last evidence" v={fmtWhen(sel.last_evidence_at)} />
                  <KV k="last positive" v={fmtWhen(sel.last_positive_at)} />
                </div>
              </div>

              {sel.uncertainty && (
                <div className="mt-2 border-t hairline pt-2">
                  <div className="mono text-[8.5px] uppercase tracking-[0.12em] text-faint mb-1">uncertainty — as served</div>
                  <div className="mono text-[9.5px] text-ink2 leading-relaxed">
                    {sel.uncertainty.basis} · measured coverage{" "}
                    {sel.uncertainty.measured_coverage !== null ? `${(sel.uncertainty.measured_coverage * 100).toFixed(1)}%` : "—"}{" "}
                    · n={sel.uncertainty.n_calibration ?? "—"} · stratum {sel.uncertainty.source_stratum ?? "—"}
                    {sel.uncertainty.widened ? <span className="text-warn"> · widened ({sel.uncertainty.widen_reason})</span> : null}
                    <br />radius map {sel.uncertainty.radius_map_version ?? "—"}
                  </div>
                </div>
              )}

              <LocalPlaneMap className="h-[188px] mt-3" compact plane={plane} geometry={geom}
                focus={sel.coordinate ? { x: sel.coordinate.x, y: sel.coordinate.y } : null}
                selectedId={geom?.points?.find((p) => p.kind === "candidate" && p.selected)?.id ?? null}
                fitKey={sel.place_id} />

              <div className="mt-3 border-t hairline pt-2">
                <KV k="account" v={sel.account_id ?? "—"} />
                <KV k="address source" v={sel.source ?? "—"} />
                <KV k="added" v={sel.added_date ?? "—"} />
                <KV k="belief version" v={sel.belief_version !== null && sel.belief_version !== undefined ? `v${sel.belief_version} · ${sel.tier ?? "—"} / ${sel.status ?? "—"}` : "no stored belief"} />
              </div>

              {(detail?.contradictions_detail?.length ?? 0) > 0 && (
                <div className="mt-2.5 border border-plum/45 bg-plum-soft/50 px-2.5 py-2">
                  <div className="mono text-[8.5px] uppercase tracking-[0.12em] text-plum mb-1">contradictions on record</div>
                  {detail!.contradictions_detail.map((c) => (
                    <div key={c.address_id} className="text-[11px] text-ink2 leading-snug py-px">
                      <span className="mono text-[9px] text-plum">{c.kind.replace(/_/g, " ").toLowerCase()}</span>{" "}
                      · {c.negatives_independent} independent negative(s) · widen {c.widen_reason ?? "—"} · threshold {fmtRadius(c.threshold_m)} · radius {fmtRadius(c.radius_m)}
                    </div>
                  ))}
                </div>
              )}

              {(detail?.versions?.length ?? 0) > 0 && (
                <div className="mt-3 border-t hairline pt-2">
                  <div className="mono text-[8.5px] uppercase tracking-[0.12em] text-faint mb-1">
                    belief versions · stored rows only ({detail!.versions.length})
                  </div>
                  <div className="max-h-[150px] overflow-y-auto">
                    {detail!.versions.map((v) => (
                      <div key={`${v.address_id}-${v.belief_version}`} className="grid grid-cols-[54px_104px_80px_76px] gap-x-2 mono text-[9.5px] py-px border-b border-line/60 last:border-0">
                        <span className="text-faint">v{v.belief_version}</span>
                        <span className="text-mute">{fmtWhen(v.as_of)}</span>
                        <span className="text-ink2">{v.tier ?? "—"}</span>
                        <span className="text-mute truncate">{v.radius_m !== null ? fmtRadius(v.radius_m) : "—"}</span>
                      </div>
                    ))}
                  </div>
                  <div className="mono text-[8.5px] text-faint mt-1">{detail!.versions_note}</div>
                </div>
              )}

              <div className="mt-3 border-t hairline pt-2">
                <div className="mono text-[8.5px] uppercase tracking-[0.12em] text-faint mb-1">evidence on this place</div>
                {(kase?.evidence.observations ?? []).slice(0, 6).map((v) => (
                  <div key={v.observation_id} className="flex items-center gap-2 py-1 border-b border-line/60 last:border-0">
                    <span className="mono text-[9px] text-mute w-[92px] shrink-0">{fmtWhen(v.observed_at)}</span>
                    <span className="min-w-0 flex-1">
                      <span className="block mono text-[9px] text-ink truncate">{v.observation_id} · {v.agent_id ?? "—"}</span>
                      <span className="block mono text-[8px] text-mute truncate">{v.remark ?? v.evidence.reason_codes.join(" · ")}</span>
                    </span>
                    <Tag tone={OUTCOME_TONE[v.outcome] ?? "ink"}>{OUTCOME_LABEL[v.outcome] ?? v.outcome}</Tag>
                  </div>
                ))}
                {(kase?.evidence.observations ?? []).length === 0 && <div className="mono text-[9.5px] text-mute py-1">no visits on record</div>}
              </div>

              {kase && kase.history.events.length > 0 && (
                <div className="mt-3 border-t hairline pt-2">
                  <div className="mono text-[8.5px] uppercase tracking-[0.12em] text-faint mb-1">
                    decision history ({kase.history.count} events · read-only)
                  </div>
                  {kase.history.events.slice(0, 5).map((e, i) => (
                    <div key={`${e.at}-${i}`} className="flex gap-2 py-px text-[10.5px] text-ink2 leading-snug">
                      <span className="mono text-[9px] text-faint w-[92px] shrink-0">{fmtWhen(e.at)}</span>
                      <span className="min-w-0">
                        <span className="block truncate">{e.title}</span>
                      </span>
                    </div>
                  ))}
                </div>
              )}

              <div className="mt-3 flex gap-1.5">
                {kase?.task ? (
                  <button onClick={() => { notify(`opening ${kase.task!.task_id}`); openTask?.(kase.task!.task_id); go("queue"); }}
                    className="flex-1 flex items-center justify-center gap-1.5 border border-accent-deep text-accent-deep bg-accent-faint hover:bg-accent-soft mono text-[10px] uppercase tracking-[0.08em] py-2 transition-colors">
                    <FilePlus2 size={12} /> Open verification task
                  </button>
                ) : (
                  <div className="flex-1 flex items-center justify-center gap-1.5 border hairline text-faint mono text-[9.5px] uppercase tracking-[0.08em] py-2">
                    <TriangleAlert size={11} /> no open task for this place
                  </div>
                )}
                <button onClick={() => go("evidence")}
                  className="flex-1 flex items-center justify-center gap-1.5 border hairline hover:border-line2 text-ink2 mono text-[10px] uppercase tracking-[0.08em] py-2 transition-colors">
                  <Footprints size={12} /> Open evidence
                </button>
              </div>
              <div className="mono text-[8.5px] text-faint mt-2 leading-relaxed">
                tasks are raised by the frozen engine — the workbench can open one, re-state it, or record a decision,
                but it cannot invent a verification task.
              </div>
            </Panel>
          )}
          {!sel && rows.length === 0 && <Empty msg="no place selected" />}
        </div>
      </div>
    </div>
  );
}
