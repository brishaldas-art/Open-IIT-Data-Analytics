import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Check, CirclePlay, CornerDownRight, FilePlus2, ShieldAlert, Undo2 } from "lucide-react";
import { fetchScenarios, fetchScene, useQuery } from "@/lib/api";
import { useSession } from "@/lib/session";
import type { Candidate, Scenario } from "@/lib/types";
import { C, cn, dist, fmtCoord, fmtM, fmtScore } from "@/lib/utils";
import LocalPlaneMap from "@/components/LocalPlaneMap";
import { Empty, Panel, ScoreBar, Sec, Tag, TRAIL_TONE } from "@/components/u";
import { ViewHead, type ViewId } from "@/components/Shell";

type Phase = "tracing" | "done";
type Outcome = "DECIDED" | "VERIFY_TASK" | "UNPLACEABLE";

const SCN_TAG: Record<string, string> = {
  "scn-a": "typo + landmark · warm",
  "scn-b": "clean · auto path",
  "scn-c": "drift 99.8 m · contested",
  "scn-d": "name-only · cold",
};

/* ---------------- policy gates ---------------- */

function verdict(cands: Candidate[]) {
  const s = [...cands].sort((a, b) => b.score - a.score);
  const t1 = s[0], t2 = s[1];
  const margin = t2 ? t1.score - t2.score : 1;
  const sep = t2 ? dist(t1.at, t2.at) : 0;
  if (t1.score < 0.6)
    return { code: "UNPLACEABLE" as const, tone: "crit" as const, label: "UNPLACEABLE — BELOW 0.60 FLOOR", t1, t2, margin, sep };
  if (margin < 0.15 && sep > 25)
    return { code: "CONTESTED" as const, tone: "plum" as const, label: "CONTESTED — HOLD FOR FIELD", t1, t2, margin, sep };
  if (margin < 0.15)
    return { code: "COMMIT_OK" as const, tone: "warn" as const, label: "COMMIT PERMITTED · SPATIAL CLUSTER", t1, t2, margin, sep };
  if (t1.score >= 0.85)
    return { code: "AUTO_OK" as const, tone: "ok" as const, label: "AUTO-CONFIRM ELIGIBLE", t1, t2, margin, sep };
  return { code: "VERIFY" as const, tone: "accent" as const, label: "VERIFY-FIRST RECOMMENDED", t1, t2, margin, sep };
}

/* ---------------- audit table (also used by Method view) ---------------- */

export function AuditTable({ limit }: { limit?: number }) {
  const { audit } = useSession();
  const rows = limit ? audit.slice(-limit) : audit;
  return (
    <div className="mono text-[9.5px] leading-[1.7]">
      <div className="grid grid-cols-[34px_64px_92px_150px_1fr_130px] gap-x-3 text-faint uppercase tracking-[0.08em] border-b hairline pb-1">
        <span>seq</span><span>time</span><span>actor</span><span>action</span><span>detail</span><span className="text-right">hash</span>
      </div>
      {rows.map((e) => (
        <div key={e.seq} className="grid grid-cols-[34px_64px_92px_150px_1fr_130px] gap-x-3 border-b border-line/60 py-px hover:bg-panel">
          <span className="text-faint">{String(e.seq).padStart(3, "0")}</span>
          <span className="text-mute">{e.ts}</span>
          <span className="text-mute truncate">{e.actor}</span>
          <span className="text-ink font-medium truncate">{e.action}</span>
          <span className="text-ink2 truncate">{e.detail}</span>
          <span className="text-right text-faint">⋯{e.hash.slice(-12)}</span>
        </div>
      ))}
    </div>
  );
}

/* ---------------- candidate card ---------------- */

function CandidateCard({
  c, rank, active, onClick,
}: { c: Candidate; rank: number; active: boolean; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "w-full text-left border px-2.5 py-2 transition-colors rise",
        active ? "border-accent bg-accent-faint/60" : "hairline bg-raised hover:border-line2",
      )}
      style={{ animationDelay: `${rank * 45}ms` }}
    >
      <div className="flex items-start gap-2">
        <span className={cn(
          "grid place-items-center size-[22px] border mono text-[10.5px] font-semibold mt-px shrink-0",
          active ? "border-accent-deep text-accent-deep bg-raised" : "border-line2 text-ink2",
        )}>
          r{rank}
        </span>
        <span className="flex-1 min-w-0">
          <span className="block text-[12px] font-medium leading-snug">{c.canonical}</span>
          <span className="block mono text-[8.5px] uppercase tracking-[0.06em] text-mute mt-0.5">
            {c.source} · {c.sourceRef}
          </span>
        </span>
        <span className={cn("serif text-[22px] font-semibold tnum leading-none", active ? "text-accent-deep" : "text-ink")}>
          {fmtScore(c.score)}
        </span>
      </div>

      <div className="mt-2 space-y-[3px]">
        <ScoreBar label="text sim" v={c.parts.text} tone={active ? "accent" : "ink"} />
        <ScoreBar label="components" v={c.parts.component} />
        <ScoreBar label="src trust" v={c.parts.source} />
        <ScoreBar label="evidence" v={c.parts.evidence} tone={c.parts.evidence > 0 ? "ok" : "mute"} />
        <ScoreBar label="memory" v={c.parts.memory} tone={c.parts.memory > 0 ? "cool" : "mute"} />
      </div>

      <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 mono text-[8.5px] text-mute border-t hairline pt-1.5">
        <span>σ {c.sigmaM} m</span>
        <span>Δanchor {fmtM(c.distFromAnchorM, 0)}</span>
        <span className={c.evidenceSupport > 0 ? "text-ok" : ""}>{c.evidenceSupport} visit{c.evidenceSupport === 1 ? "" : "s"}</span>
      </div>
      {c.conflict && (
        <div className="mt-1.5 flex items-start gap-1.5 mono text-[8.5px] text-warn leading-snug">
          <ShieldAlert size={10} className="mt-px shrink-0" /> {c.conflict}
        </div>
      )}
    </button>
  );
}

/* ---------------- main view ---------------- */

export default function Resolver({ go }: { go: (v: ViewId) => void }) {
  const { data: scene } = useQuery(fetchScene);
  const { data: scenarios } = useQuery(fetchScenarios);
  const { push, addCase, notify } = useSession();

  const [scnId, setScnId] = useState<string | null>(null);
  const scn: Scenario | null = useMemo(
    () => scenarios?.find((s) => s.id === scnId) ?? scenarios?.[0] ?? null,
    [scenarios, scnId],
  );
  const [input, setInput] = useState("");
  const [phase, setPhase] = useState<Phase>("tracing");
  const [traceCount, setTraceCount] = useState(0);
  const [selId, setSelId] = useState<string | null>(null);
  const [outcome, setOutcome] = useState<Outcome | null>(null);
  const [ledgerRef, setLedgerRef] = useState<{ seq: number; hash: string } | null>(null);
  const [mismatch, setMismatch] = useState(false);
  const runToken = useRef(0);

  const run = useCallback((s: Scenario) => {
    const token = ++runToken.current;
    setPhase("tracing");
    setTraceCount(0);
    setOutcome(null);
    setLedgerRef(null);
    setMismatch(false);
    push("RESOLVE_REQUEST", `${s.id} · "${s.raw.slice(0, 44)}…"`);
    s.pipeline.forEach((_, i) => {
      window.setTimeout(() => {
        if (runToken.current !== token) return;
        setTraceCount(i + 1);
      }, 420 + i * 150);
    });
    window.setTimeout(() => {
      if (runToken.current !== token) return;
      setPhase("done");
      const top = [...s.candidates].sort((a, b) => b.score - a.score)[0];
      setSelId(top.id);
    }, 420 + s.pipeline.length * 150 + 140);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const pick = useCallback((s: Scenario) => {
    setScnId(s.id);
    setInput(s.raw);
    setSelId(null);
    run(s);
  }, [run]);

  /* boot: run first scenario once loaded */
  useEffect(() => {
    if (scenarios && scenarios.length && scnId === null) {
      pick(scenarios[0]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scenarios]);

  const done = phase === "done" && scn !== null;
  const v = scn && done ? verdict(scn.candidates) : null;
  const sel = scn?.candidates.find((c) => c.id === selId) ?? null;
  const selRank = scn ? [...scn.candidates].sort((a, b) => b.score - a.score).findIndex((c) => c.id === selId) + 1 : 0;

  const act = (kind: Outcome) => {
    if (!scn || !v) return;
    if (kind === "DECIDED" && sel) {
      const ev = push("DECISION_COMMITTED",
        `${scn.id} → ${sel.canonical.slice(0, 38)} · E${fmtCoord(sel.at.x)} N${fmtCoord(sel.at.y)} σ${sel.sigmaM}m · score ${fmtScore(sel.score)}`);
      setOutcome("DECIDED");
      setLedgerRef({ seq: ev.seq, hash: ev.hash });
      notify(`decision committed · ledger #${ev.seq}`);
    } else if (kind === "VERIFY_TASK") {
      const id = `VQ-49${String(20 + Math.floor(Math.random() * 60)).slice(0, 2)}`;
      addCase({
        id, kind: "VERIFY_FIRST", placeLabel: v.t1.canonical, rawAddress: scn.raw,
        priority: v.code === "CONTESTED" ? "P1" : "P2", ageDays: 0, slaHoursLeft: 48, slaHoursTotal: 48,
        reasonCodes: v.code === "CONTESTED" ? ["CONTESTED_SPLIT", `MARGIN_${v.margin.toFixed(2)}`] : [`MARGIN_${v.margin.toFixed(2)}_LT_GATE`],
        score: v.t1.score, margin: v.margin, at: v.t1.at, sigmaM: v.t1.sigmaM,
        recommendation: v.code === "CONTESTED"
          ? "Field officer to arbitrate between separated claims; capture occupant attestation."
          : "Photo fix at proposed point; confirm entrance and signboard.",
      });
      const ev = push("VERIFY_TASK_CREATED", `${id} · ${scn.id} · ${v.code} · top1 ${fmtScore(v.t1.score)} Δ${v.margin.toFixed(2)}`);
      setOutcome("VERIFY_TASK");
      setLedgerRef({ seq: ev.seq, hash: ev.hash });
      notify(`verify task ${id} opened`);
    } else {
      const id = `VQ-49${String(20 + Math.floor(Math.random() * 60)).slice(0, 2)}`;
      addCase({
        id, kind: "UNPLACEABLE", placeLabel: scn.parsed.find((p) => p.k === "business")?.t ?? scn.raw.slice(0, 30),
        rawAddress: scn.raw, priority: "P1", ageDays: 0, slaHoursLeft: 48, slaHoursTotal: 48,
        reasonCodes: ["BELOW_FLOOR_0.60", ...(scn.memory ? [] : ["NO_MEMORY_PRIOR"])],
        score: v.t1.score, at: v.t1.at, sigmaM: v.t1.sigmaM,
        recommendation: "Local inquiry + caller callback for cross-street; no blind dispatch.",
      });
      const ev = push("UNPLACEABLE_DECLARED", `${id} · ${scn.id} · top1 ${fmtScore(v.t1.score)} below floor`);
      setOutcome("UNPLACEABLE");
      setLedgerRef({ seq: ev.seq, hash: ev.hash });
      notify(`unplaceable · field task ${id} opened`);
    }
  };

  if (!scene || !scenarios || !scn) {
    return <div className="mono text-[11px] text-mute p-8">loading resolver fixtures…</div>;
  }

  return (
    <div className="max-w-[1500px] mx-auto">
      <ViewHead
        title="Resolver"
        note="messy address → ranked candidates → local-plane evidence → ledgered decision"
        right={
          <>
            {scenarios.map((s) => (
              <button key={s.id} onClick={() => pick(s)}
                className={cn("border px-2 py-1 mono text-[9px] uppercase tracking-[0.06em] transition-colors",
                  scn.id === s.id ? "border-accent-deep bg-accent-faint text-accent-deep" : "hairline bg-raised text-mute hover:text-ink")}>
                {s.id.replace("scn-", "case ")} · {SCN_TAG[s.id]}
              </button>
            ))}
          </>
        }
      />

      {/* intake console */}
      <Panel className="px-3.5 py-3">
        <Sec no="01" title="Messy address intake"
          right={<span className="mono text-[9px] text-mute">{scn.context}</span>} />
        <div className="flex gap-2 mt-2.5">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") { if (input.trim() !== scn.raw) { setMismatch(true); } else run(scn); } }}
            spellCheck={false}
            className="flex-1 border hairline bg-paper px-3 py-2 mono text-[12px] text-ink placeholder:text-faint focus:outline-none focus:border-accent"
            placeholder="type or paste a messy address…"
          />
          <button
            onClick={() => { if (input.trim() !== scn.raw) { setMismatch(true); return; } run(scn); }}
            className="flex items-center gap-1.5 bg-accent hover:bg-accent-deep text-paper mono text-[10.5px] uppercase tracking-[0.08em] px-4 transition-colors"
          >
            <CirclePlay size={13} strokeWidth={1.8} /> Resolve
          </button>
          <button onClick={() => pick(scn)} title="Reset case"
            className="grid place-items-center w-9 border hairline text-mute hover:text-ink hover:border-line2 transition-colors">
            <Undo2 size={13} strokeWidth={1.8} />
          </button>
        </div>

        {mismatch && (
          <div className="mt-2 border border-warn/50 bg-warn-soft px-2.5 py-1.5 mono text-[9.5px] text-warn rise">
            FREE-TEXT RESOLUTION NEEDS THE LIVE PIPELINE — THIS DEMO REPLAYS 4 CAPTURED INTAKES.{" "}
            <button className="underline" onClick={() => pick(scn)}>reload current case</button>
          </div>
        )}

        {/* parsed tokens + trace */}
        <div className="grid grid-cols-12 gap-3 mt-3">
          <div className="col-span-12 xl:col-span-5">
            <div className="mono text-[8.5px] uppercase tracking-[0.12em] text-faint mb-1.5">Parsed tokens</div>
            <div className="flex flex-wrap gap-1.5">
              {scn.parsed.map((p, i) => (
                <span key={i} className={cn(
                  "border px-1.5 py-0.5 mono text-[9.5px]",
                  p.k === "noise" ? "border-line text-faint line-through" :
                  p.k === "house-no" ? "border-accent/50 bg-accent-faint text-accent-deep font-semibold" :
                  p.k === "landmark" ? "border-cool/40 bg-cool-soft text-cool" :
                  p.k === "business" ? "border-ink/30 text-ink" : "hairline text-ink2 bg-raised",
                )}>
                  {p.t}
                  <span className="text-faint font-normal"> · {p.k}</span>
                </span>
              ))}
            </div>
            <div className="mt-2.5 mono text-[8.5px] text-mute leading-relaxed border-t hairline pt-2">
              anchor from locality graph · E {fmtCoord(scn.anchor.x, 0)} N {fmtCoord(scn.anchor.y, 0)} · σ {scn.anchorSigmaM} m
              {scn.memory ? <> · memory prior {scn.memory.placeId} (σ {scn.memory.sigmaM} m, {scn.memory.lastVerifiedDays} d)</> : " · no memory prior — cold start"}
            </div>
          </div>
          <div className="col-span-12 xl:col-span-7">
            <div className="mono text-[8.5px] uppercase tracking-[0.12em] text-faint mb-1.5 flex items-center justify-between">
              <span>Pipeline trace</span>
              {phase === "tracing" && <span className="text-accent-deep blink">running…</span>}
            </div>
            <div className="border hairline bg-paper px-2.5 py-1.5 h-[104px] overflow-y-auto">
              {phase === "tracing" && traceCount === 0 && (
                <div className="mono text-[10px] text-mute blink">resolving intake…</div>
              )}
              {scn.pipeline.slice(0, Math.max(traceCount, phase === "done" ? scn.pipeline.length : 0)).map((p, i) => (
                <div key={p.stage} className="mono text-[10px] leading-[1.65] flex gap-2 rise">
                  <span className="text-faint w-5">{String(i).padStart(2, "0")}</span>
                  <span className="text-accent-deep w-[104px] shrink-0 uppercase">{p.stage}</span>
                  <span className="text-faint w-12 text-right shrink-0 tnum">{p.ms}ms</span>
                  <span className="text-ink2 truncate">{p.note}</span>
                </div>
              ))}
              {phase === "tracing" && traceCount > 0 && traceCount < scn.pipeline.length && (
                <div className="mono text-[10px] text-faint blink">▌</div>
              )}
            </div>
          </div>
        </div>
      </Panel>

      {/* workspace */}
      {!done ? (
        <Panel className="mt-3 px-3.5 py-16">
          <div className="text-center">
            <CrosshairAnim />
            <div className="mono text-[10px] uppercase tracking-[0.16em] text-mute mt-3">scoring candidates against evidence…</div>
          </div>
        </Panel>
      ) : (
        <div className="grid grid-cols-12 gap-3 mt-3">
          {/* candidates */}
          <div className="col-span-12 lg:col-span-3 space-y-2">
            <Sec no="02" title={`Ranked candidates · ${scn.candidates.length}`}
              right={<span className="mono text-[8.5px] text-faint">gate 0.85 / floor 0.60</span>} />
            {[...scn.candidates].sort((a, b) => b.score - a.score).map((c, i) => (
              <CandidateCard key={c.id} c={c} rank={i + 1} active={selId === c.id} onClick={() => setSelId(c.id)} />
            ))}
            {scn.memory && (
              <div className="border border-dashed border-cool/50 bg-cool-soft/40 px-2.5 py-2">
                <div className="mono text-[8.5px] uppercase tracking-[0.1em] text-cool mb-1">memory prior</div>
                <div className="text-[11.5px] font-medium">{scn.memory.placeId}</div>
                <div className="mono text-[8.5px] text-mute mt-0.5">
                  E {fmtCoord(scn.memory.at.x, 0)} N {fmtCoord(scn.memory.at.y, 0)} · σ {scn.memory.sigmaM} m<br />
                  last verified {scn.memory.lastVerifiedDays} d ago · priors damp evidence, never replace it
                </div>
              </div>
            )}
          </div>

          {/* map */}
          <div className="col-span-12 lg:col-span-5">
            <Sec no="03" title="Local plane · metres" right={<span className="mono text-[8.5px] text-faint">drag to pan · scroll to zoom</span>} />
            <LocalPlaneMap
              className="h-[470px] mt-2"
              scene={scene}
              focus={scn.anchor}
              candidates={scn.candidates}
              trails={scn.trails}
              anchor={{ at: scn.anchor, sigmaM: scn.anchorSigmaM }}
              memory={scn.memory ? { at: scn.memory.at, sigmaM: scn.memory.sigmaM, label: `MEMORY ${scn.memory.placeId}`, tone: C.cool } : null}
              decision={sel && outcome !== "UNPLACEABLE" ? { at: sel.at, sigmaM: sel.sigmaM, label: `${outcome === "DECIDED" ? "FINAL" : "PROPOSED"} r${selRank} · σ ${sel.sigmaM} m` } : null}
              selectedId={selId}
              onSelect={setSelId}
              fitKey={scn.id + String(done)}
            />
            <div className="flex flex-wrap gap-x-3 gap-y-1 mt-2 mono text-[8.5px] text-mute">
              <span className="flex items-center gap-1"><span className="inline-block size-[8px] rounded-full border border-ink bg-raised" /> candidate</span>
              <span className="flex items-center gap-1"><span className="inline-block size-[8px] rotate-45 border" style={{ borderColor: C.cool }} /> memory</span>
              {(["confirm", "refute", "relocate", "search"] as const).map((t) => (
                <span key={t} className="flex items-center gap-1">
                  <span className="inline-block w-3.5 border-t border-dashed" style={{ borderColor: ({ confirm: C.ok, refute: C.crit, relocate: C.warn, search: C.cool })[t] }} />
                  {t}
                </span>
              ))}
              <span className="flex items-center gap-1"><span className="inline-block w-3.5 border-t border-dashed border-accent" /> decision σ</span>
            </div>
            <div className="mt-2 border-l-2 border-accent bg-accent-faint/50 px-2.5 py-1.5 text-[11px] text-ink2 leading-snug flex gap-1.5">
              <CornerDownRight size={12} className="shrink-0 mt-0.5 text-accent-deep" />
              <span><span className="mono text-[9px] uppercase tracking-[0.08em] text-accent-deep">policy note — </span>{scn.gateNote}</span>
            </div>
          </div>

          {/* decision */}
          <div className="col-span-12 lg:col-span-4">
            <Sec no="04" title="Decision & evidence" right={v && <Tag tone={v.tone}>{v.label}</Tag>} />
            <Panel className="mt-2 px-3 py-2.5">
              {sel ? (
                <>
                  <div className="mono text-[8.5px] uppercase tracking-[0.12em] text-faint">proposed point · r{selRank}</div>
                  <div className="serif text-[24px] font-semibold tnum leading-tight mt-1">
                    E {fmtCoord(sel.at.x)}
                  </div>
                  <div className="serif text-[24px] font-semibold tnum leading-tight">
                    N {fmtCoord(sel.at.y)}
                  </div>
                  <div className="mono text-[9px] text-mute mt-1">σ {sel.sigmaM} m · local plane SEAL-01 · {sel.sourceRef}</div>

                  {v && (
                    <div className="mt-2.5 border-t hairline pt-2 space-y-1">
                      <GateRow label="top1 ≥ 0.85" pass={v.t1.score >= 0.85} val={fmtScore(v.t1.score)} />
                      <GateRow label="margin ≥ 0.15" pass={v.margin >= 0.15} val={v.margin.toFixed(2)} />
                      <GateRow label="r1–r2 split ≤ 25 m" pass={v.sep <= 25} val={fmtM(v.sep, 1)} />
                      <GateRow label="evidence support" pass={sel.evidenceSupport > 0} val={`${sel.evidenceSupport} visits`} />
                    </div>
                  )}

                  <div className="mt-2.5 border-t hairline pt-2">
                    <div className="mono text-[8.5px] uppercase tracking-[0.12em] text-faint mb-1">attached field evidence</div>
                    {scn.trails.length === 0 && <div className="mono text-[9.5px] text-mute py-1">none — cold start</div>}
                    {scn.trails.map((t) => (
                      <div key={t.id} className="flex items-center gap-2 py-1">
                        <Tag tone={TRAIL_TONE[t.outcome]}>{t.outcome}</Tag>
                        <span className="min-w-0">
                          <span className="block mono text-[9px] text-ink truncate">{t.label}</span>
                          <span className="block mono text-[8px] text-mute truncate">{t.meta}</span>
                        </span>
                      </div>
                    ))}
                  </div>

                  {outcome ? (
                    <div className={cn("mt-3 border px-2.5 py-2 rise",
                      outcome === "DECIDED" ? "border-ok/50 bg-ok-soft/60" :
                      outcome === "VERIFY_TASK" ? "border-accent/50 bg-accent-faint/70" : "border-crit/50 bg-crit-soft/60")}>
                      <div className="mono text-[9.5px] font-semibold tracking-[0.06em]">
                        {outcome === "DECIDED" ? "✓ DECISION COMMITTED TO LEDGER" :
                         outcome === "VERIFY_TASK" ? "→ FIELD VERIFICATION TASK OPEN" : "✕ DECLARED UNPLACEABLE"}
                      </div>
                      {ledgerRef && (
                        <div className="mono text-[8.5px] text-mute mt-1">
                          ledger seq #{ledgerRef.seq} · hash ⋯{ledgerRef.hash.slice(-12)} · immutable
                        </div>
                      )}
                      {outcome !== "DECIDED" && (
                        <button onClick={() => go("queue")} className="mono text-[9px] underline mt-1 text-accent-deep">
                          inspect in verify queue
                        </button>
                      )}
                    </div>
                  ) : (
                    <div className="mt-3 grid grid-cols-2 gap-1.5">
                      {v && (v.code === "AUTO_OK" || v.code === "COMMIT_OK" || v.code === "VERIFY") && (
                        <button onClick={() => act("DECIDED")}
                          className="col-span-2 flex items-center justify-center gap-1.5 bg-accent hover:bg-accent-deep text-paper mono text-[10px] uppercase tracking-[0.08em] py-2 transition-colors">
                          <Check size={12} /> Commit decision
                        </button>
                      )}
                      <button onClick={() => act("VERIFY_TASK")}
                        className={cn("flex items-center justify-center gap-1.5 border mono text-[10px] uppercase tracking-[0.08em] py-2 transition-colors",
                          v && (v.code === "CONTESTED" || v.code === "VERIFY") ? "col-span-2 border-accent-deep text-accent-deep bg-accent-faint hover:bg-accent-soft" : "hairline hover:border-line2 text-ink2")}>
                        <FilePlus2 size={12} /> Queue verification
                      </button>
                      <button onClick={() => act("UNPLACEABLE")}
                        className={cn("flex items-center justify-center gap-1.5 border mono text-[10px] uppercase tracking-[0.08em] py-2 transition-colors",
                          v && v.code === "UNPLACEABLE" ? "col-span-2 border-crit text-crit bg-crit-soft/60 hover:bg-crit-soft" : "hairline text-mute hover:text-crit hover:border-crit/50")}>
                        Declare unplaceable
                      </button>
                    </div>
                  )}
                </>
              ) : (
                <Empty msg="select a candidate" />
              )}
            </Panel>
          </div>
        </div>
      )}

      {/* session ledger */}
      <Panel className="mt-3 px-3.5 py-3">
        <Sec no="05" title="Session audit ledger · hash-chained, append-only"
          right={<span className="mono text-[8.5px] text-faint">every action above is replayable</span>} />
        <div className="pt-2 max-h-[168px] overflow-y-auto">
          <AuditTable />
        </div>
      </Panel>
    </div>
  );
}

function CrosshairAnim() {
  return (
    <svg width={44} height={44} className="mx-auto marching">
      <circle cx={22} cy={22} r={14} fill="none" stroke={C.accent} strokeWidth={1.4} strokeDasharray="6 4" />
      <path d="M22,2 V12 M22,32 V42 M2,22 H12 M32,22 H42" stroke={C.ink2} strokeWidth={1.2} />
      <circle cx={22} cy={22} r={2.4} fill={C.accent} />
    </svg>
  );
}

function GateRow({ label, pass, val }: { label: string; pass: boolean; val: string }) {
  return (
    <div className="flex items-center justify-between mono text-[9.5px]">
      <span className="text-mute uppercase tracking-[0.06em]">{label}</span>
      <span className={cn("flex items-center gap-2", pass ? "text-ok" : "text-crit")}>
        <span className="tnum">{val}</span>
        <span className={cn("size-[8px] border", pass ? "bg-ok border-ok" : "border-crit")} />
      </span>
    </div>
  );
}
