import { useEffect, useMemo, useRef, useState } from "react";
import { ArrowRight, CheckCircle2, Gavel, UserCheck } from "lucide-react";
import {
  adjudicate,
  fetchCase,
  fetchGeometry,
  fetchTask,
  fetchTasks,
  fetchTownPlane,
  newIdempotencyKey,
  transitionTask,
  useQuery,
} from "@/lib/api";
import { useSession } from "@/lib/session";
import type { AdjudicationDecision, AdjudicationResponse, TaskTransition, VerificationTask } from "@/lib/types";
import { cn, fmtInt, fmtRadius, fmtScore, fmtWhen } from "@/lib/utils";
import LocalPlaneMap from "@/components/LocalPlaneMap";
import { Empty, Failed, KV, Loading, OUTCOME_LABEL, Panel, RawCode, Sec, TASK_STATE_TONE, Tag } from "@/components/u";
import { ViewHead } from "@/components/Shell";

const STATES = ["open", "in_progress", "resolved", "reopened"] as const;
const DECISIONS: AdjudicationDecision[] = ["confirmed", "not_true", "inconclusive"];

export default function VerifyQueue({ focusTaskId }: { focusTaskId?: string | null }) {
  const { asOf, reviewer, notify } = useSession();
  const [state, setState] = useState<string>("open");
  const [cause, setCause] = useState<string>("ALL");
  const [selId, setSelId] = useState<string | null>(focusTaskId ?? null);
  const [decision, setDecision] = useState<AdjudicationDecision>("confirmed");
  const [note, setNote] = useState("");
  const [receipt, setReceipt] = useState<AdjudicationResponse | null>(null);
  const [transitioned, setTransitioned] = useState<string | null>(null);
  const keyRef = useRef<string | null>(null);

  useEffect(() => { if (focusTaskId) { setSelId(focusTaskId); setState("all"); } }, [focusTaskId]);

  const { data: tasks, loading, error, reload } = useQuery(
    () => fetchTasks({ state: state === "all" ? "all" : state, cause: cause === "ALL" ? undefined : cause, limit: 200 }),
    [state, cause, asOf],
  );

  const items = useMemo(() => tasks?.items ?? [], [tasks]);
  const sel: VerificationTask | null = items.find((t) => t.task_id === selId) ?? items[0] ?? null;

  const { data: detail, reload: reloadDetail } = useQuery(
    () => (sel ? fetchTask(sel.task_id) : Promise.resolve(null)),
    [sel?.task_id],
  );
  const { data: kase, reload: reloadCase } = useQuery(
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

  useEffect(() => { setReceipt(null); setTransitioned(null); keyRef.current = null; }, [sel?.task_id]);

  const recordDecision = async () => {
    if (!sel) return;
    const key = keyRef.current ?? newIdempotencyKey("q");
    keyRef.current = key;
    try {
      const out = await adjudicate({
        task_id: sel.task_id,
        address_id: sel.address_id,
        decision,
        actor: reviewer,
        note: note.trim() || undefined,
        idempotency_key: key,
      });
      setReceipt(out);
      notify(out.replayed ? `replayed · ${out.observation_id}` : `recorded · belief v${out.belief_version ?? "—"} · case closed`, "ok");
      /* the decided case leaves the "open" filter, so widen the view: the receipt must stay on
         screen with the case it belongs to, not vanish when the queue refreshes */
      setState("all");
      reloadDetail(); reloadCase(); reload();
    } catch (e) {
      notify(`could not record the decision · ${(e as Error).message}`, "crit");
    }
  };

  const move = async (to: string) => {
    if (!sel) return;
    try {
      const out = await transitionTask(sel.task_id, { state: to, actor: reviewer, note: note.trim() || undefined });
      const t: TaskTransition = out;
      setTransitioned(`${t.from} → ${t.to} · ${t.event_id}`);
      notify(`case ${out.state_label ?? out.to}`, "ok");
      reloadDetail(); reload();
    } catch (e) {
      notify(`transition refused · ${(e as Error).message}`, "crit");
    }
  };

  if (loading && !tasks) return <Loading what="the verification queue" />;
  if (error && !tasks) return <Failed what="the verification queue" error={error} onRetry={reload} />;

  const facets = tasks?.facets;
  const ticket = kase?.decision.decision_ticket;

  return (
    <div className="max-w-[1500px] mx-auto">
      <ViewHead
        title="Verify queue"
        note="cases the evidence cannot settle alone — routed to the field, never averaged away"
        right={
          <>
            <Tag tone="accent">{fmtInt(facets?.by_state?.open ?? 0)} open</Tag>
            <span className="mono text-[9px] text-mute">
              {fmtInt(Object.values(facets?.by_state ?? {}).reduce((a, b) => a + b, 0))} task events in the store
            </span>
          </>
        }
      />

      <div className="flex flex-wrap items-center gap-1.5 mb-3">
        {(["all", ...STATES] as const).map((s) => (
          <button key={s} onClick={() => setState(s)}
            className={cn("mono text-[9px] uppercase tracking-[0.08em] border px-2 py-1 transition-colors",
              state === s ? "border-ink bg-ink text-paper" : "hairline bg-raised text-mute hover:text-ink")}>
            {s.replace(/_/g, " ")}
            {s !== "all" && facets?.by_state[s] !== undefined && <span className="ml-1 opacity-70 tnum">{facets.by_state[s]}</span>}
          </button>
        ))}
        <span className="w-px h-4 bg-line2 mx-1" />
        {["ALL", ...Object.keys(facets?.by_cause ?? {})].map((c) => (
          <button key={c} onClick={() => setCause(c)}
            className={cn("mono text-[9px] uppercase tracking-[0.08em] border px-2 py-1 transition-colors",
              cause === c ? "border-ink bg-ink text-paper" : "hairline bg-raised text-mute hover:text-ink")}>
            {c === "ALL" ? "all causes" : c.replace(/_/g, " ").toLowerCase()}
            {c !== "ALL" && <span className="ml-1 opacity-70 tnum">{facets!.by_cause[c]}</span>}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-12 gap-3">
        {/* table */}
        <div className="col-span-12 xl:col-span-7 self-start">
          <Panel className="px-3.5 py-3">
            <Sec no="A" title="Cases"
              right={<span className="mono text-[9px] text-mute">{fmtInt(tasks?.total_matching ?? 0)} matching · priority desc</span>} />
            <div className="pt-1.5 max-h-[620px] overflow-y-auto" data-testid="task-table">
              <div className="grid grid-cols-[1fr_104px_96px_78px_72px] gap-x-3 px-1 mono text-[8.5px] uppercase tracking-[0.08em] text-faint border-b hairline pb-1 sticky top-0 bg-raised">
                <span>case</span><span>cause</span><span>state</span><span className="text-right">priority</span><span className="text-right">raised</span>
              </div>
              {items.map((t) => (
                <button key={t.task_id} data-testid={`task-row-${t.task_id}`} onClick={() => setSelId(t.task_id)}
                  className={cn("w-full grid grid-cols-[1fr_104px_96px_78px_72px] gap-x-3 items-center px-1 py-[6px] text-left border-b border-line/60 transition-colors",
                    sel?.task_id === t.task_id ? "bg-accent-faint/60" : "hover:bg-panel")}>
                  <span className="min-w-0">
                    <span className="block text-[11.5px] truncate">{t.address_label ?? t.address_id}</span>
                    <span className="block mono text-[8.5px] text-faint truncate">{t.task_id} · {t.town_id} · {t.tier ?? "—"} / {t.status ?? "—"}</span>
                  </span>
                  <Tag tone={t.cause === "CONTESTED" ? "plum" : "warn"} className="justify-center">{t.cause.replace(/_/g, " ").toLowerCase()}</Tag>
                  <Tag tone={TASK_STATE_TONE[t.state] ?? "ink"} className="justify-center">{(t.state_label ?? t.state).toLowerCase()}</Tag>
                  <span className="mono text-[10.5px] text-right tnum">{t.priority !== null ? fmtScore(t.priority) : "—"}</span>
                  <span className="mono text-[9.5px] text-right text-mute">{fmtWhen(t.at).slice(0, 11)}</span>
                </button>
              ))}
              {items.length === 0 && <div className="py-8 text-center mono text-[10px] text-mute uppercase tracking-[0.1em]">no cases in this state</div>}
            </div>
          </Panel>
        </div>

        {/* case panel */}
        <div className="col-span-12 xl:col-span-5 self-start">
          {sel && (
            <Panel className="px-3.5 py-3 rise" key={sel.task_id}>
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <h2 className="serif text-[18px] font-semibold leading-tight">{sel.address_id}</h2>
                  <div className="mono text-[9px] text-mute mt-0.5">
                    {sel.task_id} · {sel.kind.replace(/_/g, " ")} · raised {fmtWhen(sel.at)}
                  </div>
                </div>
                <Tag tone={TASK_STATE_TONE[sel.state] ?? "ink"}>{sel.state_label ?? sel.state}</Tag>
              </div>

              <div className="mt-2.5 border hairline bg-paper px-2.5 py-2">
                <div className="mono text-[8.5px] uppercase tracking-[0.12em] text-faint mb-1">recommended field action</div>
                <p className="text-[11.5px] text-ink2 leading-snug">
                  {sel.recommended_action?.label ?? "—"}
                  {sel.recommended_action?.clears_when ? <> — clears when {sel.recommended_action.clears_when}</> : null}
                </p>
                <div className="mono text-[9px] text-mute mt-1">
                  evidence refs {sel.evidence_refs.join(" · ")} ({sel.evidence_refs_basis ?? "—"})
                </div>
              </div>

              {kase && (
                <div className="grid grid-cols-2 gap-3 mt-3 border-t hairline pt-2.5">
                  <div>
                    <div className="mono text-[8.5px] uppercase tracking-[0.12em] text-faint">answered point · {kase.coordinate_space}</div>
                    {kase.decision.coordinate ? (
                      <>
                        <div className="serif text-[17px] font-semibold tnum leading-snug mt-0.5">E {kase.decision.coordinate.x.toFixed(1)}</div>
                        <div className="serif text-[17px] font-semibold tnum leading-snug">N {kase.decision.coordinate.y.toFixed(1)}</div>
                        <div className="mono text-[8.5px] text-mute">
                          radius {fmtRadius(kase.decision.coordinate.radius_m)} · {kase.decision.coordinate.granularity ?? "—"}
                        </div>
                      </>
                    ) : (
                      <div className="mono text-[10px] text-crit mt-1">no coordinate served for this answer</div>
                    )}
                  </div>
                  <div className="border-l hairline pl-3">
                    <KV k="tier / status" v={`${sel.tier ?? "—"} / ${sel.status ?? "—"}`} />
                    <KV k="radius" v={fmtRadius(sel.radius_m)} />
                    <KV k="independent negatives" v={String(sel.negatives_independent ?? 0)} tone={(sel.negatives_independent ?? 0) > 0 ? "warn" : undefined} />
                    <KV k="priority" v={sel.priority !== null ? fmtScore(sel.priority) : "—"} />
                  </div>
                </div>
              )}

              {kase && (
                <LocalPlaneMap className="h-[176px] mt-3" compact plane={plane} geometry={geom}
                  focus={kase.decision.coordinate ? { x: kase.decision.coordinate.x, y: kase.decision.coordinate.y } : null}
                  selectedId={geom?.points?.find((p) => p.kind === "candidate" && p.selected)?.id ?? null}
                  fitKey={sel.task_id} />
              )}

              {ticket && (
                <div className="mt-2.5 border-t hairline pt-2">
                  <div className="mono text-[8.5px] uppercase tracking-[0.12em] text-faint mb-1">why this case exists</div>
                  <div className="flex flex-wrap gap-1">
                    {ticket.why.slice(0, 8).map((rc) => <RawCode key={rc.code} code={rc.code} />)}
                  </div>
                  <div className="mono text-[9.5px] text-mute mt-1.5">
                    gate {ticket.gate.action.replace(/_/g, " ")} · {ticket.gate.reason ?? "—"} · {ticket.gate.rule_version}
                    {ticket.margin?.score_margin !== null && ticket.margin?.score_margin !== undefined
                      ? <> · margin {ticket.margin.score_margin.toFixed(3)} to the runner-up</> : null}
                  </div>
                </div>
              )}

              {kase && kase.evidence.observations.length > 0 && (
                <div className="mt-2.5 border-t hairline pt-2">
                  <div className="mono text-[8.5px] uppercase tracking-[0.12em] text-faint mb-1">
                    evidence on the address ({kase.evidence.count})
                  </div>
                  {kase.evidence.observations.slice(-5).reverse().map((v) => (
                    <div key={v.observation_id} className="flex items-center gap-2 py-[3px]">
                      <span className="mono text-[9px] text-mute w-[92px] shrink-0">{fmtWhen(v.observed_at)}</span>
                      <span className="mono text-[9px] text-ink2 flex-1 truncate">{v.observation_id}</span>
                      <Tag tone={v.polarity === "negative" ? "crit" : v.polarity === "ambiguous" ? "warn" : "ok"}>{OUTCOME_LABEL[v.outcome] ?? v.outcome}</Tag>
                    </div>
                  ))}
                </div>
              )}

              {/* task history — the real lifecycle */}
              <div className="mt-2.5 border-t hairline pt-2">
                <div className="mono text-[8.5px] uppercase tracking-[0.12em] text-faint mb-1">
                  case history ({(detail?.history ?? kase?.task_history ?? []).length} events)
                </div>
                {(detail?.history ?? kase?.task_history ?? []).map((h) => (
                  <div key={h.event_id} className="flex gap-2 py-[2px]">
                    <span className="mono text-[9px] text-mute w-[92px] shrink-0">{fmtWhen(h.at)}</span>
                    <span className="min-w-0 text-[10.5px] text-ink2 leading-snug">
                      <span className="mono text-[9.5px] text-ink">{(h.state_label ?? h.state).toLowerCase()}</span>
                      {h.actor ? <> · {h.actor}</> : null}{h.note ? <> · “{h.note}”</> : null}
                    </span>
                  </div>
                ))}
                {detail?.adjudications && detail.adjudications.length > 0 && (
                  <div className="mono text-[9px] text-mute mt-1">{detail.adjudications.length} adjudication record(s) attached</div>
                )}
              </div>

              {/* actions */}
              {receipt ? (
                <div className="mt-3 border border-ok/50 bg-ok-soft/60 px-2.5 py-2" data-testid="queue-receipt">
                  <div className="mono text-[9.5px] font-semibold text-ok tracking-[0.06em]">
                    ✓ CASE {String(receipt.task.closed).toUpperCase() === "TRUE" ? "CLOSED" : "UPDATED"} · {receipt.decision.toUpperCase()}
                  </div>
                  <div className="mono text-[8.5px] text-ink2 mt-1 leading-relaxed">
                    {receipt.observation_id} · belief v{receipt.belief_version ?? "—"} · {receipt.tier ?? "—"} / {receipt.status ?? "—"}
                    <br />coordinate_moved {String(receipt.effect.coordinate_moved)} · changed {String(receipt.effect.changed)} · never enters S-Eval {String(receipt.never_enters_s_eval)}
                    <br />{receipt.note_text}
                  </div>
                </div>
              ) : (
                <div className="mt-3 space-y-1.5">
                  <div className="flex gap-1.5">
                    {(detail?.allowed_transitions ?? []).map((to) => (
                      <button key={to} onClick={() => move(to)} data-testid={`transition-${to}`}
                        className={cn("flex-1 flex items-center justify-center gap-1 border mono text-[9.5px] uppercase tracking-[0.06em] py-2 transition-colors",
                          to === "in_progress" ? "border-accent-deep text-accent-deep bg-accent-faint hover:bg-accent-soft"
                            : to === "resolved" ? "border-ok/60 text-ok bg-ok-soft/50 hover:bg-ok-soft"
                              : "border-plum/60 text-plum bg-plum-soft/50 hover:bg-plum-soft")}>
                        {to === "in_progress" ? <UserCheck size={11} /> : to === "resolved" ? <CheckCircle2 size={11} /> : <ArrowRight size={11} />}
                        {to.replace(/_/g, " ")}
                      </button>
                    ))}
                    {(detail?.allowed_transitions ?? []).length === 0 && (
                      <div className="flex-1 border hairline text-faint mono text-[9.5px] uppercase tracking-[0.06em] py-2 text-center">
                        no transitions offered from {detail?.state_label ?? sel.state}
                      </div>
                    )}
                  </div>
                  {transitioned && <div className="mono text-[9px] text-ok">{transitioned}</div>}

                  <div className="border hairline bg-panel px-2.5 py-2">
                    <div className="mono text-[8.5px] uppercase tracking-[0.12em] text-faint mb-1.5 flex items-center gap-1.5">
                      <Gavel size={11} /> record the reviewer's decision
                    </div>
                    <div className="flex gap-1.5">
                      {DECISIONS.map((d) => (
                        <button key={d} onClick={() => setDecision(d)}
                          className={cn("flex-1 mono text-[9px] uppercase tracking-[0.06em] border py-1.5 transition-colors",
                            decision === d ? "border-ink bg-ink text-paper" : "hairline bg-raised text-mute hover:text-ink")}>
                          {d.replace(/_/g, " ")}
                        </button>
                      ))}
                    </div>
                    <input value={note} onChange={(e) => setNote(e.target.value)} spellCheck={false}
                      placeholder="note (optional, stored with the observation)"
                      className="mt-1.5 w-full border hairline bg-raised px-2 py-1.5 mono text-[10px] text-ink placeholder:text-faint focus:outline-none focus:border-accent" />
                    <button onClick={recordDecision} data-testid="queue-record"
                      className="mt-1.5 w-full flex items-center justify-center gap-1.5 bg-accent hover:bg-accent-deep text-paper mono text-[10px] uppercase tracking-[0.08em] py-2 transition-colors">
                      <CheckCircle2 size={12} /> Record decision & close case
                    </button>
                    <div className="mono text-[8px] text-faint mt-1 leading-relaxed">
                      appended as an adjudication observation and a task event · receipt first: a retried request returns
                      the recorded receipt instead of writing twice
                    </div>
                  </div>
                </div>
              )}
            </Panel>
          )}
          {!sel && <Empty msg="no case selected" />}
        </div>
      </div>
    </div>
  );
}
