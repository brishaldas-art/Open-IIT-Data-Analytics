import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { CheckCircle2, CirclePlay, CornerDownRight, FilePlus2, Gavel, ShieldAlert, Undo2 } from "lucide-react";
import {
  adjudicate,
  fetchAudit,
  fetchGeometry,
  fetchTownPlane,
  newIdempotencyKey,
  resolveAddress,
  useQuery,
} from "@/lib/api";
import { useSession } from "@/lib/session";
import type { AdjudicationDecision, AdjudicationResponse, ReasonCode as ReasonCodeT } from "@/lib/types";
import { cn, fmtCoord, fmtRadius, fmtScore, fmtWhen } from "@/lib/utils";
import LocalPlaneMap from "@/components/LocalPlaneMap";
import { Empty, Failed, GATE_TONE, KV, Loading, OUTCOME_LABEL, Panel, RawCode, ReasonChip, Sec, Tag, TermBar, Tone } from "@/components/u";
import { ViewHead, type ViewId } from "@/components/Shell";

/* The three real store cases the workbench demos. Ids only — every value
   below them is fetched from the service, never written here. */
const DEMO: { id: string; tag: string }[] = [
  { id: "AD003067", tag: "clean · serve" },
  { id: "AD002936", tag: "drift · verify first" },
  { id: "AD000002", tag: "work-like · refuse" },
];

const TERM_TONE = (rc: ReasonCodeT): Tone => (rc.direction === "positive" ? "ok" : rc.direction === "negative" ? "crit" : "ink");

export default function Resolver({ go, openTask }: { go: (v: ViewId) => void; openTask?: (taskId: string) => void }) {
  const { asOf, reviewer, notify } = useSession();
  const [draft, setDraft] = useState("");
  const [req, setReq] = useState<{ kind: "id" | "text"; value: string }>({ kind: "id", value: DEMO[0].id });
  const [selArm, setSelArm] = useState<string | null>(null);
  const [decision, setDecision] = useState<AdjudicationDecision>("confirmed");
  const [note, setNote] = useState("");
  const [receipt, setReceipt] = useState<AdjudicationResponse | null>(null);
  const keyRef = useRef<string | null>(null);

  const { data: res, loading, error, reload } = useQuery(
    () =>
      req.kind === "id"
        ? resolveAddress({ address_id: req.value })
        : resolveAddress({ address_text: req.value }),
    [req, asOf],
  );
  const { data: geom } = useQuery(
    () => (res?.address_id ? fetchGeometry(res.address_id, "FIELD_NAVIGATION") : Promise.resolve(null)),
    [res?.address_id, asOf],
  );
  const { data: plane } = useQuery(
    () => (res?.town_id ? fetchTownPlane(res.town_id) : Promise.resolve(null)),
    [res?.town_id, asOf],
  );
  const { data: audit } = useQuery(
    () => (res?.address_id && res.belief_version ? fetchAudit(`${res.address_id}:${res.belief_version}`) : Promise.resolve(null)),
    [res?.address_id, res?.belief_version, asOf],
  );

  /* a fresh answer starts with the winner selected (the service marks it `selected`) */
  useEffect(() => {
    setReceipt(null);
    keyRef.current = null;
    const sel = geom?.points?.find((p) => p.kind === "candidate" && p.selected);
    setSelArm(sel?.id ?? res?.candidate_id ?? null);
  }, [geom, res?.candidate_id, res?.belief_version]);

  const run = useCallback(() => {
    const v = draft.trim();
    if (!v) return;
    setReq({ kind: "text", value: v });
    setDraft("");
  }, [draft]);

  const pick = useCallback((id: string) => {
    setReq({ kind: "id", value: id });
    setReceipt(null);
  }, []);

  const rec = useMemo(() => {
    if (!res) return null;
    const coords = geom?.points?.filter((p) => p.kind === "candidate") ?? [];
    const sel = coords.find((p) => p.id === selArm) ?? null;
    const arms = [...res.arms_considered].sort((a, b) => b.score - a.score);
    const terms = res.decision_ticket.score_terms ?? [];
    const maxTerm = Math.max(0.001, ...terms.map((t) => Math.abs(t.effect ?? 0)));
    return { coords, sel, arms, terms, maxTerm };
  }, [res, geom, selArm]);

  const gate = res?.eligibility.action ?? "VERIFY_FIRST";
  const refused = gate === "REFUSE" || !res?.coordinate;
  const withheld = geom?.withheld ?? null;

  const submit = async () => {
    if (!res?.address_id) return;
    const key = keyRef.current ?? newIdempotencyKey("adj");
    keyRef.current = key;
    try {
      const out = await adjudicate({
        address_id: res.address_id,
        decision,
        actor: reviewer,
        note: note.trim() || undefined,
        idempotency_key: key,
      });
      setReceipt(out);
      notify(
        out.replayed
          ? `adjudication replayed · ${out.observation_id}`
          : `recorded · belief v${out.belief_version ?? "—"} → ${out.tier ?? "—"} / ${out.status ?? "—"}`,
        "ok",
      );
      reload();                                  // the ticket now shows the recomputed belief
    } catch (e) {
      notify(`adjudication failed · ${(e as Error).message}`, "crit");
    }
  };

  if (loading && !res) return <Loading what="the resolver" />;
  if (error && !res) return <Failed what="the resolver" error={error} onRetry={reload} />;
  if (!res || !rec) return <Empty msg="no answer" />;

  const ticket = res.decision_ticket;

  return (
    <div className="max-w-[1500px] mx-auto">
      <ViewHead
        title="Resolver"
        note="address → ranked arms over official candidates and field evidence → local-plane decision"
        right={
          <>
            {DEMO.map((d) => (
              <button key={d.id} onClick={() => pick(d.id)}
                className={cn("border px-2 py-1 mono text-[9px] uppercase tracking-[0.06em] transition-colors",
                  req.kind === "id" && req.value === d.id ? "border-accent-deep bg-accent-faint text-accent-deep" : "hairline bg-raised text-mute hover:text-ink")}>
                {d.id} · {d.tag}
              </button>
            ))}
          </>
        }
      />

      {/* ---------------- intake console ---------------- */}
      <Panel className="px-3.5 py-3">
        <Sec no="01" title="Address intake"
          right={<span className="mono text-[9px] text-mute">{res.town_id ? `town ${res.town_id} · ${res.stage ?? "—"}` : "—"} · {res.resolution ?? "—"}</span>} />
        <div className="flex gap-2 mt-2.5">
          <input
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") run(); }}
            spellCheck={false}
            data-testid="intake-input"
            className="flex-1 border hairline bg-paper px-3 py-2 mono text-[12px] text-ink placeholder:text-faint focus:outline-none focus:border-accent"
            placeholder="type or paste a messy address, exactly as written…"
          />
          <button onClick={run} data-testid="intake-resolve"
            className="flex items-center gap-1.5 bg-accent hover:bg-accent-deep text-paper mono text-[10.5px] uppercase tracking-[0.08em] px-4 transition-colors">
            <CirclePlay size={13} strokeWidth={1.8} /> Resolve
          </button>
          <button onClick={() => pick(req.kind === "id" ? req.value : DEMO[0].id)} title="Re-run current case"
            className="grid place-items-center w-9 border hairline text-mute hover:text-ink hover:border-line2 transition-colors">
            <Undo2 size={13} strokeWidth={1.8} />
          </button>
        </div>

        <div className="grid grid-cols-12 gap-3 mt-3">
          <div className="col-span-12 xl:col-span-5">
            <div className="mono text-[8.5px] uppercase tracking-[0.12em] text-faint mb-1.5">Request, as the service read it</div>
            <div className="mono text-[10.5px] text-ink leading-relaxed border hairline bg-paper px-2.5 py-2">
              {req.kind === "id" ? <><span className="text-faint">address_id · </span>{req.value}</> : <><span className="text-faint">address_text · </span>“{req.value}”</>}
              <div className="mt-1 text-[9px] text-mute">
                purpose {res.request_purpose} · resolved to {res.address_id ?? "—"} · belief v{res.belief_version ?? "—"} · place {res.place_id ?? "—"}
              </div>
            </div>
            {res.address_purpose && (
              <div className="mt-2 border-t hairline pt-2">
                <div className="mono text-[8.5px] uppercase tracking-[0.12em] text-faint mb-1">
                  Address purpose · {res.address_purpose.model_version}
                </div>
                <div className="flex flex-wrap items-center gap-1.5">
                  <Tag tone="ink">{res.address_purpose.class.replace(/_/g, " ")}</Tag>
                  <span className="mono text-[9px] text-mute">confidence {res.address_purpose.confidence}</span>
                </div>
                <div className="flex flex-wrap gap-1 mt-1.5">
                  {res.address_purpose.basis.map((b) => <RawCode key={b} code={b} />)}
                </div>
                <div className="mt-2 mono text-[8.5px] text-mute leading-relaxed border-t hairline pt-2">
                  anchor stage {res.stage ?? "—"} · arms available {res.arms_available.length} · candidates considered {res.arms_considered.length}
                  {res.is_area_context ? " · area context" : ""}
                </div>
              </div>
            )}
          </div>

          <div className="col-span-12 xl:col-span-7">
            <div className="mono text-[8.5px] uppercase tracking-[0.12em] text-faint mb-1.5 flex items-center justify-between">
              <span>Arms considered · {res.arms_considered.length}</span>
              <span className="text-faint">{res.versions?.rule_version}</span>
            </div>
            <div className="border hairline bg-paper px-2.5 py-1.5 h-[132px] overflow-y-auto" data-testid="arms-considered">
              {rec.arms.map((a, i) => (
                <div key={a.candidate_id} className={cn("mono text-[10px] leading-[1.7] flex gap-2 items-baseline", a.candidate_id === selArm && "bg-accent-faint/50")}>
                  <span className="text-faint w-5">{String(i).padStart(2, "0")}</span>
                  <span className={cn("w-[124px] shrink-0 truncate", a.candidate_id === res.candidate_id ? "text-accent-deep font-semibold" : "text-ink2")}>{a.arm}</span>
                  <span className="w-16 text-right shrink-0 tnum">{fmtScore(a.score)}</span>
                  <span className={cn("w-14 shrink-0", a.primary_eligible ? "text-ok" : "text-faint")}>{a.primary_eligible ? "eligible" : "—"}</span>
                  <span className="text-mute truncate">{a.reasons.join(" · ")}</span>
                </div>
              ))}
              {rec.arms.length === 0 && <div className="mono text-[10px] text-mute">no arm produced a candidate</div>}
            </div>
          </div>
        </div>
      </Panel>

      {/* ---------------- workspace ---------------- */}
      <div className="grid grid-cols-12 gap-3 mt-3">
        {/* ranked arms */}
        <div className="col-span-12 lg:col-span-3 space-y-2">
          <Sec no="02" title={`Ranked arms · ${rec.arms.length}`}
            right={<span className="mono text-[8.5px] text-faint">{res.versions?.gate_rule_version}</span>} />
          {rec.arms.map((a, i) => {
            const c = rec.coords.find((p) => p.id === a.candidate_id) ?? null;
            const active = selArm === a.candidate_id;
            return (
              <button key={a.candidate_id} onClick={() => setSelArm(a.candidate_id)}
                data-testid={`arm-${i}`}
                className={cn("w-full text-left border px-2.5 py-2 transition-colors",
                  active ? "border-accent bg-accent-faint/60" : "hairline bg-raised hover:border-line2")}>
                <div className="flex items-start gap-2">
                  <span className={cn("grid place-items-center size-[22px] border mono text-[10.5px] font-semibold mt-px shrink-0",
                    active ? "border-accent-deep text-accent-deep bg-raised" : "border-line2 text-ink2")}>
                    r{i + 1}
                  </span>
                  <span className="flex-1 min-w-0">
                    <span className="block text-[12px] font-medium leading-snug truncate">{a.arm}</span>
                    <span className="block mono text-[8.5px] uppercase tracking-[0.06em] text-mute mt-0.5">
                      {c ? `${c.granularity} · official-plane point` : "no coordinate published"} · {a.primary_eligible ? "primary eligible" : "not primary"}
                    </span>
                  </span>
                  <span className={cn("serif text-[22px] font-semibold tnum leading-none", active ? "text-accent-deep" : "text-ink")}>
                    {fmtScore(a.score)}
                  </span>
                </div>
                {a.candidate_id === res.candidate_id && rec.terms.length > 0 && (
                  <div className="mt-2 space-y-[3px]">
                    {rec.terms.slice(0, 6).map((t) => (
                      <TermBar key={t.code} label={t.label} effect={t.effect ?? 0} max={rec.maxTerm} tone={TERM_TONE(t)} />
                    ))}
                    {rec.terms.length > 6 && (
                      <div className="mono text-[8.5px] text-faint">+{rec.terms.length - 6} more terms · full list in the ticket</div>
                    )}
                  </div>
                )}
                <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 mono text-[8.5px] text-mute border-t hairline pt-1.5">
                  <span>{a.reasons.length} reason terms</span>
                  {c && <span>ring {fmtRadius(res.radius_m)}</span>}
                </div>
              </button>
            );
          })}

          {res.alternatives.length > 0 && (
            <div className="border border-dashed border-cool/50 bg-cool-soft/40 px-2.5 py-2">
              <div className="mono text-[8.5px] uppercase tracking-[0.1em] text-cool mb-1">nearest alternative</div>
              <div className="text-[11.5px] font-medium">{res.alternatives[0].arm} · r{res.alternatives[0].rank}</div>
              <div className="mono text-[8.5px] text-mute mt-0.5">
                score {fmtScore(res.alternatives[0].score)} · margin {res.decision_ticket.margin?.score_margin?.toFixed(3) ?? "—"} to the winner
              </div>
            </div>
          )}
        </div>

        {/* map */}
        <div className="col-span-12 lg:col-span-5">
          <Sec no="03" title="Local plane · metres" right={<span className="mono text-[8.5px] text-faint">drag to pan · scroll to zoom</span>} />
          <LocalPlaneMap
            className="h-[470px] mt-2"
            plane={plane}
            geometry={geom}
            focus={res.coordinate ? { x: res.coordinate.x, y: res.coordinate.y } : null}
            selectedId={selArm}
            onSelect={setSelArm}
            fitKey={`${res.address_id}-${res.belief_version}`}
          />
          <div className="flex flex-wrap gap-x-3 gap-y-1 mt-2 mono text-[8.5px] text-mute">
            <span className="flex items-center gap-1"><span className="inline-block size-[8px] rounded-full border border-ink bg-raised" /> candidate (R roofline · S street · L locality)</span>
            <span className="flex items-center gap-1"><span className="inline-block size-[8px] rotate-45 border" style={{ borderColor: "#51616c" }} /> locality</span>
            <span className="flex items-center gap-1"><span className="inline-block w-3.5 border-t border-dashed border-accent" /> uncertainty radius</span>
            <span className="flex items-center gap-1"><span className="inline-block w-3.5 border-t border-dotted border-line3" /> official landmark</span>
          </div>
          <div className="mt-2 border-l-2 border-accent bg-accent-faint/50 px-2.5 py-1.5 text-[11px] text-ink2 leading-snug flex gap-1.5">
            <CornerDownRight size={12} className="shrink-0 mt-0.5 text-accent-deep" />
            <span>
              <span className="mono text-[9px] uppercase tracking-[0.08em] text-accent-deep">gate — </span>
              {ticket.headline}. Rule {res.eligibility.rule_version}
              {res.eligibility.reason ? <> · reason <span className="mono text-[10px]">{res.eligibility.reason}</span></> : null}
            </span>
          </div>
        </div>

        {/* decision */}
        <div className="col-span-12 lg:col-span-4">
          <Sec no="04" title="Decision & evidence" right={<Tag tone={GATE_TONE[gate]}>{gate.replace(/_/g, " ")}</Tag>} />
          <Panel className="mt-2 px-3 py-2.5">
            {refused ? (
              <div data-testid="refusal-panel">
                <div className="flex items-center gap-1.5 mono text-[9.5px] uppercase tracking-[0.1em] text-crit font-semibold">
                  <ShieldAlert size={12} /> no coordinate is served
                </div>
                <p className="text-[11.5px] text-ink2 leading-snug mt-1.5">{ticket.headline}.</p>
                <div className="mt-2 border-t hairline pt-2">
                  <KV k="gate" v={`${gate.replace(/_/g, " ")} · ${res.eligibility.reason ?? "—"}`} tone="crit" />
                  <KV k="rule" v={res.eligibility.rule_version} />
                  <KV k="address purpose" v={res.address_purpose?.class.replace(/_/g, " ") ?? "—"} />
                  <KV k="request purpose" v={res.request_purpose} />
                  <KV k="belief" v={`v${res.belief_version ?? "—"} · ${res.tier ?? "—"} / ${res.status ?? "—"}`} />
                </div>
                {withheld && (
                  <div className="mt-2 border border-crit/40 bg-crit-soft/50 px-2.5 py-2 mono text-[9.5px] text-ink2 leading-relaxed">
                    withheld by the geometry endpoint · {withheld.reason}
                    {withheld.suppressed ? <> · suppressed {withheld.suppressed.candidate_points} candidate points, {withheld.suppressed.rings} ring</> : null}
                    <div className="text-crit mt-1">{withheld.note}</div>
                  </div>
                )}
                <div className="mt-2 flex flex-wrap gap-1">
                  {(ticket.refusal?.reason_codes ?? res.reasons).map((c: string) => <RawCode key={c} code={c} />)}
                </div>
                <div className="mt-2.5 border-t hairline pt-2 mono text-[8.5px] text-mute leading-relaxed">
                  no task was raised for this answer{res.task ? ` · task ${res.task.task_id}` : ""} · evidence {res.evidence_summary?.n_observations ?? 0} observation(s) on record
                </div>
              </div>
            ) : (
              <>
                <div className="mono text-[8.5px] uppercase tracking-[0.12em] text-faint">answered point · {res.candidate?.arm} · {res.granularity}</div>
                <div className="serif text-[24px] font-semibold tnum leading-tight mt-1" data-testid="answer-x">E {fmtCoord(rec.sel?.x ?? res.coordinate!.x)}</div>
                <div className="serif text-[24px] font-semibold tnum leading-tight" data-testid="answer-y">N {fmtCoord(rec.sel?.y ?? res.coordinate!.y)}</div>
                <div className="mono text-[9px] text-mute mt-1" data-testid="answer-meta">
                  radius {fmtRadius(res.radius_m)} · {res.radius_basis ?? "—"} · {res.coordinate?.coordinate_space} · {res.candidate?.source_ref ?? "—"}
                </div>

                <div className="mt-2.5 border-t hairline pt-2 space-y-1">
                  <KV k="tier" v={res.tier ?? "—"} />
                  <KV k="status" v={res.status ?? "—"} />
                  <KV k="measured coverage" v={res.measured_coverage !== null && res.measured_coverage !== undefined ? `${(res.measured_coverage * 100).toFixed(1)}% · n=${res.n_calibration}` : "—"} />
                  <KV k="stratum" v={`${res.source_stratum ?? "—"}${res.widened ? ` · widened (${res.widen_reason})` : ""}`} tone={res.widened ? "warn" : undefined} />
                  <KV k="independent confirmations" v={String(res.support?.independent_confirmations ?? 0)} />
                  <KV k="negative claims · duplicates" v={`${res.support?.negatives_independent ?? 0} · ${res.support?.duplicate_claims ?? 0}`} />
                </div>

                <div className="mt-2.5 border-t hairline pt-2">
                  <div className="mono text-[8.5px] uppercase tracking-[0.12em] text-faint mb-1">why — typed reason codes</div>
                  <div className="flex flex-wrap gap-1">
                    {(ticket.why ?? []).slice(0, 10).map((rc) => <ReasonChip key={rc.code} rc={rc} />)}
                  </div>
                </div>

                {rec.terms.length > 0 && (
                  <div className="mt-2.5 border-t hairline pt-2">
                    <div className="mono text-[8.5px] uppercase tracking-[0.12em] text-faint mb-1">score terms · effect on the winner</div>
                    <div className="space-y-[3px]">
                      {rec.terms.map((t) => <TermBar key={t.code} label={t.label} effect={t.effect ?? 0} max={rec.maxTerm} tone={TERM_TONE(t)} />)}
                    </div>
                  </div>
                )}

                <div className="mt-2.5 border-t hairline pt-2">
                  <div className="mono text-[8.5px] uppercase tracking-[0.12em] text-faint mb-1">provenance</div>
                  <div className="mono text-[9.5px] text-ink2 leading-relaxed" data-testid="provenance">
                    {String(res.candidate?.provenance?.built_from ?? "—")}
                    <br />licence {res.candidate?.licence_class ?? "—"} · as-of valid {fmtWhen(res.candidate?.as_of_valid)} · built {fmtWhen((res.candidate?.provenance?.built_at as string) || null)}
                    <br />observations {String(res.candidate?.provenance?.n_observations ?? 0)} · spread {res.candidate?.provenance?.spread_m !== null && res.candidate?.provenance?.spread_m !== undefined ? `${res.candidate.provenance.spread_m} m` : "—"} · agreement arms {String(res.candidate?.provenance?.agreement_arms ?? 0)}
                  </div>
                </div>

                {res.task && (
                  <div className="mt-2.5 border-t hairline pt-2">
                    <div className="mono text-[8.5px] uppercase tracking-[0.12em] text-faint mb-1">open task · raised by the engine</div>
                    <div className="flex items-center gap-2">
                      <Tag tone="warn">{res.task.cause.replace(/_/g, " ")}</Tag>
                      <span className="mono text-[9.5px] text-ink truncate">{res.task.task_id}</span>
                    </div>
                    <div className="mono text-[9px] text-mute mt-1 leading-relaxed">
                      priority {res.task.priority ?? "—"} · at {fmtWhen(res.task.at)}<br />
                      {res.task.recommended_action?.label} — clears when {res.task.recommended_action?.clears_when}
                    </div>
                  </div>
                )}

                {receipt && (
                  <div className="mt-3 border border-ok/50 bg-ok-soft/60 px-2.5 py-2" data-testid="adjudication-receipt">
                    <div className="mono text-[9.5px] font-semibold text-ok tracking-[0.06em]">
                      ✓ ADJUDICATION RECORDED · {receipt.decision.toUpperCase()}
                    </div>
                    <div className="mono text-[8.5px] text-ink2 mt-1 leading-relaxed">
                      {receipt.observation_id} · belief {String(receipt.effect.belief_before?.belief_version ?? "—")} → v{receipt.belief_version ?? "—"}
                      <br />{receipt.tier ?? "—"} / {receipt.status ?? "—"} · coordinate_moved {String(receipt.effect.coordinate_moved)} · changed {String(receipt.effect.changed)}
                      <br />task {receipt.task.task_id ?? "—"} closed {String(receipt.task.closed)} · never enters S-Eval: {String(receipt.never_enters_s_eval)}
                      {receipt.replayed && <><br />replayed from the receipt ledger (idempotent retry)</>}
                    </div>
                  </div>
                )}

                <div className="mt-3 space-y-1.5">
                  {res.task && (
                    <button onClick={() => { notify(`opening ${res.task!.task_id}`); openTask?.(res.task!.task_id); go("queue"); }}
                      data-testid="open-task"
                      className="w-full flex items-center justify-center gap-1.5 border border-accent-deep text-accent-deep bg-accent-faint hover:bg-accent-soft mono text-[10px] uppercase tracking-[0.08em] py-2 transition-colors">
                      <FilePlus2 size={12} /> Open verification task
                    </button>
                  )}
                  <div className="border hairline bg-panel px-2.5 py-2">
                    <div className="mono text-[8.5px] uppercase tracking-[0.12em] text-faint mb-1.5 flex items-center gap-1.5">
                      <Gavel size={11} /> record a reviewer decision · the only human ground-truth write
                    </div>
                    <div className="flex gap-1.5">
                      {(["confirmed", "not_true", "inconclusive"] as AdjudicationDecision[]).map((d) => (
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
                    <button onClick={submit} data-testid="record-decision"
                      className="mt-1.5 w-full flex items-center justify-center gap-1.5 bg-accent hover:bg-accent-deep text-paper mono text-[10px] uppercase tracking-[0.08em] py-2 transition-colors">
                      <CheckCircle2 size={12} /> Record decision
                    </button>
                    <div className="mono text-[8px] text-faint mt-1 leading-relaxed">
                      appended as an adjudication observation · the frozen engine recomputes the belief · old observations are never rewritten
                    </div>
                  </div>
                </div>
              </>
            )}
          </Panel>
        </div>
      </div>

      {/* ---------------- decision history ---------------- */}
      <Panel className="mt-3 px-3.5 py-3">
        <Sec no="05" title="Decision history · read-only reconstruction"
          right={<span className="mono text-[8.5px] text-faint">{audit ? `${audit.steps} weighted steps · belief ${audit.belief_id}` : "—"}</span>} />
        {!audit ? (
          <div className="mono text-[10px] text-mute pt-2">no stored belief to reconstruct</div>
        ) : (
          <>
            <div className="grid grid-cols-12 gap-3 pt-2">
              <div className="col-span-12 xl:col-span-4">
                <KV k="belief" v={`v${audit.belief.belief_version} · ${audit.belief.tier ?? "—"} / ${audit.belief.status ?? "—"}`} />
                <KV k="answered arm" v={audit.winner?.arm ?? "—"} />
                <KV k="payload sha256" v={<span className="truncate">{audit.belief.payload_sha256.slice(0, 16)}…</span>} />
                <KV k="radius" v={`${fmtRadius(audit.belief.radius_m)}${audit.uncertainty?.previous_radius_m ? ` · was ${fmtRadius(audit.uncertainty.previous_radius_m)}` : ""}`} />
                <KV k="versions" v={`${audit.belief.rules_version} · ${audit.belief.evidence_policy_version} · ${audit.belief.radius_map_version}`} />
                <KV k="tasks on this address" v={String(audit.tasks.length)} />
                <div className="mono text-[8.5px] text-faint leading-relaxed border-t hairline pt-2 mt-1">{audit.note}</div>
              </div>
              <div className="col-span-12 xl:col-span-8">
                <div className="mono text-[8.5px] uppercase tracking-[0.12em] text-faint mb-1">evidence the belief was computed from</div>
                <div className="max-h-[190px] overflow-y-auto border hairline bg-paper">
                  <div className="grid grid-cols-[96px_112px_120px_58px_74px_1fr] gap-x-3 px-2.5 py-1 mono text-[8.5px] text-faint uppercase tracking-[0.08em] border-b hairline sticky top-0 bg-paper">
                    <span>at</span><span>observation</span><span>outcome</span><span>weight</span><span>class</span><span>reasons</span>
                  </div>
                  {(audit.evidence || []).map((e) => (
                    <div key={e.observation_id} className="grid grid-cols-[96px_112px_120px_58px_74px_1fr] gap-x-3 px-2.5 py-[3px] mono text-[9.5px] border-b border-line/60 last:border-0 hover:bg-panel">
                      <span className="text-mute">{fmtWhen(e.at)}</span>
                      <span className="text-ink2 truncate">{e.observation_id}</span>
                      <span className="text-ink truncate">{OUTCOME_LABEL[e.outcome] ?? e.outcome.replace(/_/g, " ")}</span>
                      <span className={cn("text-right tnum", (e.weight ?? 0) > 0 ? "text-ink" : "text-mute")}>{(e.weight ?? 0).toFixed(4)}</span>
                      <span className="text-mute truncate">{e.evidence_class ?? "—"}</span>
                      <span className="text-faint truncate">{(e.reason_codes || []).join(" · ")}</span>
                    </div>
                  ))}
                  {(audit.evidence || []).length === 0 && <div className="mono text-[10px] text-mute p-2">no evidence rows</div>}
                </div>
                {audit.alternatives_lost.length > 0 && (
                  <div className="mt-2 border-t hairline pt-2">
                    <div className="mono text-[8.5px] uppercase tracking-[0.12em] text-faint mb-1">why the runner-up lost</div>
                    {(audit.alternatives_lost || []).slice(0, 2).map((a) => (
                      <div key={a.candidate_id} className="mono text-[9.5px] text-ink2 leading-relaxed">
                        {a.arm} · {a.candidate_id} — {a.reasons.slice(0, 5).join(" · ")}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </>
        )}
      </Panel>
    </div>
  );
}
