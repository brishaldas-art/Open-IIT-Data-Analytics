import { useState } from "react";
import { CornerUpLeft } from "lucide-react";
import { fetchAudit, fetchEvidence, fetchHealth, fetchMethodTrust, useQuery } from "@/lib/api";
import { useSession } from "@/lib/session";
import { cn, fmtInt, fmtPct, fmtWhen } from "@/lib/utils";
import { CAPABILITY_TONE, Failed, KV, Loading, Meter, OUTCOME_LABEL, Panel, RawCode, Sec, Tag } from "@/components/u";
import { ViewHead } from "@/components/Shell";

export default function Method() {
  const { asOf } = useSession();
  const { data: m, loading, error, reload } = useQuery(fetchMethodTrust, []);
  const { data: health } = useQuery(fetchHealth, []);
  /* one real decision, reconstructed read-only, so the audit claim is checkable in-product */
  const { data: audit } = useQuery(() => fetchAudit("AD002936:7"), []);
  const { data: feed } = useQuery(() => fetchEvidence({ limit: 400 }), [asOf]);

  const [tab, setTab] = useState<"chain" | "rules">("chain");

  if (loading && !m) return <Loading what="method & trust" />;
  if (error && !m) return <Failed what="method & trust" error={error} onRetry={reload} />;
  if (!m) return null;

  /* a real worked example from the feed: the heaviest non-positive row the policy admits */
  const example = (feed?.items ?? [])
    .filter((v) => v.polarity !== "positive" && (v.evidence.weight ?? 0) > 0)
    .sort((a, b) => (b.evidence.weight ?? 0) - (a.evidence.weight ?? 0))[0];

  return (
    <div className="max-w-[1500px] mx-auto">
      <ViewHead
        title="Method & trust"
        note="how the answer is produced, what the system refuses to do, and what has actually been measured"
        right={
          <>
            <Tag tone="ink">{health ? `${health.versions.schema_version}` : "—"}</Tag>
            <span className="mono text-[9px] text-mute">source: {m.evaluation_source}</span>
          </>
        }
      />

      <div className="grid grid-cols-12 gap-3">
        <div className="col-span-12 xl:col-span-8 space-y-3">
          {/* 01 pipeline */}
          <Panel className="px-3.5 py-3">
            <Sec no="01" title="Resolution pipeline" right={<span className="mono text-[8.5px] text-faint">as the service describes itself</span>} />
            <div className="grid grid-cols-1 md:grid-cols-2 gap-x-4 gap-y-2 pt-2.5">
              {m.how_it_works.map((s) => (
                <div key={s.step} className="flex gap-2">
                  <span className="mono text-[10px] text-accent-deep w-5 shrink-0">{String(s.step).padStart(2, "0")}</span>
                  <span className="min-w-0">
                    <span className="block text-[11.5px] font-semibold">{s.title}</span>
                    <span className="block text-[11px] text-ink2 leading-snug">{s.detail}</span>
                  </span>
                </div>
              ))}
            </div>
            <div className="mt-3 border-t hairline pt-2 flex flex-wrap items-center gap-2">
              <span className="mono text-[8.5px] uppercase tracking-[0.12em] text-faint">learning loop</span>
              {m.learning_loop.map((l, i) => (
                <span key={l} className="flex items-center gap-1.5">
                  <span className="mono text-[9.5px] text-ink2">{l}</span>
                  {i < m.learning_loop.length - 1 && <span className="mono text-[9px] text-faint">→</span>}
                </span>
              ))}
            </div>
          </Panel>

          {/* 02 gates & safety rules */}
          <Panel className="px-3.5 py-3">
            <Sec no="02" title="Decision rule & safety rules"
              right={<span className="mono text-[8.5px] text-faint">{health?.rule_version}</span>} />
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2.5">
              <div>
                <div className="mono text-[8.5px] uppercase tracking-[0.12em] text-faint mb-1.5">the three outcomes the gate can return</div>
                <div className="space-y-1.5">
                  {[
                    { a: "SERVE", d: "a location may be handed to the field, with its radius. Live example: AD003067 (home-like purpose)." },
                    { a: "VERIFY_FIRST", d: "an answer exists but the field must settle it. Live example: AD002936 (negatives accumulated)." },
                    { a: "REFUSE", d: "no coordinate is served at all, and none is rendered. Live example: AD000002 (work-like purpose)." },
                  ].map((g) => (
                    <div key={g.a} className="border hairline bg-paper px-2.5 py-2">
                      <Tag tone={g.a === "SERVE" ? "ok" : g.a === "VERIFY_FIRST" ? "accent" : "crit"}>{g.a.replace(/_/g, " ")}</Tag>
                      <div className="text-[11px] text-ink2 leading-snug mt-1">{g.d}</div>
                    </div>
                  ))}
                </div>
                <div className="mono text-[8.5px] text-faint mt-2 leading-relaxed">
                  the threshold arithmetic is not published here because it is not this page's to state —
                  the rule versions are ({health?.versions?.gate_rule_version ?? "gate-v2"}), and every
                  decision carries its rule version and typed reasons.
                </div>
              </div>
              <div>
                <div className="mono text-[8.5px] uppercase tracking-[0.12em] text-faint mb-1.5">safety rules enforced in the engine</div>
                <ul className="space-y-1.5">
                  {m.safety_rules.map((r) => (
                    <li key={r} className="flex gap-2 text-[11px] text-ink2 leading-snug">
                      <span className="text-accent-deep mt-px">▪</span>
                      <span>{r}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </Panel>

          {/* 03 the plane */}
          <Panel className="px-3.5 py-3">
            <Sec no="03" title="Why a local metric plane, and not latitude/longitude" />
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2.5">
              <div className="text-[11.5px] text-ink2 leading-snug space-y-2">
                <p>
                  A metre is what the field collector actually has: a walked distance, a dwell, a doorstep. The plane keeps
                  every measurement in the unit the evidence was gathered in — easting and northing in metres from a
                  declared origin — so uncertainty is a radius in metres, not a degree.
                </p>
                <p>
                  No basemap, no tiles and no external geocoder are consulted: the workbench draws the survey grid, the
                  official landmarks and the town's own localities, all of which come from the store. Nothing about the
                  answer leaves the local frame, and the frame is named in every payload
                  (<span className="mono text-[10.5px]">sutra_local_metric_plane:&lt;town&gt;</span>).
                </p>
              </div>
              <div className="border hairline bg-paper px-2.5 py-2 self-start">
                <div className="mono text-[8.5px] uppercase tracking-[0.12em] text-faint mb-1">the plane at this cut</div>
                <div className="mono text-[9.5px] text-ink2 leading-[1.75]">
                  {health ? (
                    <>
                      addresses indexed · {fmtInt((health.gauges as { n_addresses_indexed?: number }).n_addresses_indexed ?? 0)}<br />
                      open tasks by cause · {Object.entries((health.gauges as { open_tasks_by_cause?: Record<string, number> }).open_tasks_by_cause ?? {}).map(([k, v]) => `${k} ${v}`).join(" · ")}<br />
                      evidence policy · {String((health.store as { evidence_policy_version?: string }).evidence_policy_version ?? "—")}<br />
                      radius map · {health.radius_map_version}<br />
                      S-Eval reads by tools · {String(health.counters.s_eval_looks ?? "—")} · tuning uses {String((health.s_eval_firewall as { tuning_uses?: number }).tuning_uses ?? 0)}
                    </>
                  ) : "reading runtime status…"}
                </div>
              </div>
            </div>
          </Panel>

          {/* 04 evidence integrity, with a real worked example */}
          <Panel className="px-3.5 py-3">
            <Sec no="04" title="Evidence integrity — what the policy admits" />
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2.5">
              <div className="text-[11.5px] text-ink2 leading-snug space-y-2">
                <p>
                  Every visit is scored by the frozen evidence policy ({String((health?.store as { evidence_policy_version?: string })?.evidence_policy_version ?? "evidence-policy-v3")})
                  before it can influence anything: what kind of evidence it is, whether it is independent, whether it carries a
                  coordinate claim at all, and what it can therefore do. The score, the class and the typed reason codes are stored
                  with the row — they are not recomputed for display.
                </p>
                <p>
                  Failures are kept, visibly. A negative never relocates an address: it widens uncertainty and asks for a visit.
                  Duplicate claims are recorded as duplicates rather than counted twice, and one visit is never enough to confirm.
                </p>
              </div>
              <div className="border border-crit/45 bg-crit-soft/50 px-2.5 py-2 self-start">
                <div className="mono text-[8.5px] uppercase tracking-[0.12em] text-crit mb-1">
                  worked example {example ? `· ${example.observation_id}` : ""}
                </div>
                {example ? (
                  <div className="mono text-[9px] text-ink2 leading-[1.75]">
                    {OUTCOME_LABEL[example.outcome] ?? example.outcome} · polarity {example.polarity}<br />
                    weight {example.evidence.weight?.toFixed(4)} · class {example.evidence.evidence_class}<br />
                    coordinate claim · {example.coordinate_claim ? "yes" : "no — device position only"}<br />
                    contributes · {example.contributes.replace(/_/g, " ")}<br />
                    <div className="flex flex-wrap gap-1 mt-1">
                      {example.evidence.reason_codes.map((c) => <RawCode key={c} code={c} />)}
                    </div>
                    <span className="text-crit font-semibold">
                      → {example.polarity === "negative" ? "held to widening only · cannot move the coordinate" : "counted as doubt · verification required"}
                    </span>
                  </div>
                ) : (
                  <div className="mono text-[9.5px] text-mute">reading the evidence feed…</div>
                )}
              </div>
            </div>
          </Panel>

          {/* 05 auditability */}
          <Panel className="px-3.5 py-3">
            <div className="flex items-baseline justify-between gap-3 border-b hairline pb-1.5">
              <div className="flex items-baseline gap-2">
                <span className="mono text-[10px] text-faint">05</span>
                <span className="text-[11px] font-semibold uppercase tracking-[0.12em] text-ink2">Auditability</span>
              </div>
              <div className="flex items-center gap-1">
                <button onClick={() => setTab("chain")}
                  className={cn("mono text-[9px] uppercase tracking-[0.08em] border px-2 py-0.5", tab === "chain" ? "border-ink bg-ink text-paper" : "hairline text-mute hover:text-ink")}>
                  decision chain
                </button>
                <button onClick={() => setTab("rules")}
                  className={cn("mono text-[9px] uppercase tracking-[0.08em] border px-2 py-0.5", tab === "rules" ? "border-ink bg-ink text-paper" : "hairline text-mute hover:text-ink")}>
                  write path
                </button>
              </div>
            </div>

            {tab === "chain" ? (
              <div className="pt-2">
                <div className="flex items-baseline justify-between gap-3">
                  <span className="mono text-[9.5px] text-ink2">
                    belief {audit?.belief_id ?? "—"} · {audit?.steps ?? "—"} weighted steps · winner {audit?.winner?.arm ?? "—"}
                  </span>
                  <span className="mono text-[8.5px] text-faint truncate">payload sha256 {audit?.belief.payload_sha256.slice(0, 24) ?? "—"}…</span>
                </div>
                <div className="mt-1.5 max-h-[230px] overflow-y-auto border hairline bg-paper">
                  <div className="grid grid-cols-[96px_118px_128px_58px_74px_1fr] gap-x-3 px-2.5 py-1 mono text-[8.5px] text-faint uppercase tracking-[0.08em] border-b hairline sticky top-0 bg-paper">
                    <span>at</span><span>observation</span><span>outcome</span><span>weight</span><span>class</span><span>reasons</span>
                  </div>
                  {(audit?.evidence ?? []).map((e) => (
                    <div key={e.observation_id} className="grid grid-cols-[96px_118px_128px_58px_74px_1fr] gap-x-3 px-2.5 py-[3px] mono text-[9.5px] border-b border-line/60 last:border-0 hover:bg-panel">
                      <span className="text-mute">{fmtWhen(e.at)}</span>
                      <span className="text-ink2 truncate">{e.observation_id}</span>
                      <span className="text-ink truncate">{OUTCOME_LABEL[e.outcome] ?? e.outcome}</span>
                      <span className={cn("text-right tnum", (e.weight ?? 0) > 0 ? "text-ink" : "text-mute")}>{(e.weight ?? 0).toFixed(4)}</span>
                      <span className="text-mute truncate">{e.evidence_class ?? "—"}</span>
                      <span className="text-faint truncate">{(e.reason_codes || []).join(" · ")}</span>
                    </div>
                  ))}
                </div>
                <div className="mono text-[8.5px] text-faint mt-1.5 leading-relaxed">{audit?.note}</div>
              </div>
            ) : (
              <div className="pt-2 grid grid-cols-1 md:grid-cols-2 gap-3">
                <div className="text-[11.5px] text-ink2 leading-snug space-y-2">
                  <p>
                    The store is append-only. A belief is never edited: a new observation produces a new belief version, and
                    both are kept. A reviewer's decision is itself an observation of kind <span className="mono text-[10.5px]">adjudication</span>,
                    fed through exactly the same frozen mechanism as a field visit — there is no second truth store.
                  </p>
                  <p>
                    Every write is idempotent: a retried request is answered with the receipt of the first one instead of being
                    applied twice. The workbench cannot rewrite history; it can only append to it.
                  </p>
                </div>
                <div className="border hairline bg-paper px-2.5 py-2">
                  <div className="mono text-[8.5px] uppercase tracking-[0.12em] text-faint mb-1">store at this cut</div>
                  <KV k="observations" v={fmtInt(Number((health?.store as { n_observations?: number })?.n_observations ?? 0))} />
                  <KV k="belief versions" v={fmtInt(Number((health?.store as { counts?: { belief_versions?: number } })?.counts?.belief_versions ?? 0))} />
                  <KV k="task events" v={fmtInt(Number((health?.store as { counts?: { task_events?: number } })?.counts?.task_events ?? 0))} />
                  <KV k="held (offline) observations" v={fmtInt(Number((health?.store as { counts?: { held_observations?: number } })?.counts?.held_observations ?? 0))} />
                  <KV k="as-of cut" v={fmtWhen(health?.as_of_cut ?? asOf)} />
                </div>
              </div>
            )}
          </Panel>
        </div>

        {/* right column: evaluation + status + limits */}
        <div className="col-span-12 xl:col-span-4 space-y-3 self-start">
          <Panel className="px-3.5 py-3">
            <Sec no="F" title="Measured — the frozen evaluation" />
            <div className="pt-2.5 space-y-2.5">
              {m.populations.map((p) => (
                <div key={p.key}>
                  <div className="flex items-baseline justify-between gap-2">
                    <span className="text-[11px] font-medium">{p.name}</span>
                    <span className="mono text-[10.5px] tnum">{p.hit_500m !== null ? fmtPct(p.hit_500m, 2) : "—"}</span>
                  </div>
                  <Meter v={p.hit_500m ?? 0} tone={p.key === "cold" ? "cool" : p.key === "warm" ? "accent" : "ink"} w="100%" h={3} />
                  <div className="mono text-[8.5px] text-mute mt-0.5">n={p.n} · median {p.median_m !== null ? `${p.median_m} m` : "—"}</div>
                </div>
              ))}
            </div>
            <p className="text-[11px] text-ink2 leading-snug border-t hairline pt-2 mt-2.5">{m.population_note}</p>
            <div className="mt-1.5 flex items-center gap-1.5">
              <CornerUpLeft size={11} className="text-mute" />
              <span className="mono text-[8.5px] text-faint">reproduce with <span className="text-ink2">tools/reproduce.sh</span> · figures never re-tuned</span>
            </div>
          </Panel>

          <Panel className="px-3.5 py-3">
            <Sec no="S" title="What this build is" right={<span className="mono text-[8.5px] text-faint">four labels</span>} />
            <div className="pt-2 space-y-2.5">
              {m.statuses.map((s) => (
                <div key={s.label}>
                  <Tag tone={CAPABILITY_TONE[s.label] ?? "ink"}>{s.label} · {s.items.length}</Tag>
                  <ul className="mt-1.5 space-y-[3px]">
                    {s.items.map((i) => (
                      <li key={i} className="flex gap-1.5 text-[10.5px] text-ink2 leading-snug">
                        <span className="text-faint">—</span><span>{i}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
            <div className="mono text-[8.5px] text-faint leading-relaxed border-t hairline pt-2 mt-2">{m.development_note}</div>
          </Panel>

          <Panel className="px-3.5 py-3">
            <Sec no="L" title="Limits stated plainly" />
            <ul className="pt-2 space-y-1.5">
              {[
                "no accuracy figure beyond the three frozen populations is claimed",
                "no cost or rupee saving is claimed",
                "no vendor comparison has been run",
                "the map is schematic: metres on a local plane, not a map of the world",
                `every figure here is as of ${fmtWhen(health?.as_of_cut ?? asOf)} — the store's own cut`,
              ].map((t) => (
                <li key={t} className="flex gap-1.5 text-[10.5px] text-ink2 leading-snug">
                  <span className="text-faint">—</span><span>{t}</span>
                </li>
              ))}
            </ul>
          </Panel>
        </div>
      </div>
    </div>
  );
}
