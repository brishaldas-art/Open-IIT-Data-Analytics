import type { ReactNode } from "react";
import { cn, C } from "@/lib/utils";
import type { BeliefStatus, GateAction, PlaceState, ReasonCode as ReasonCodeT, Tier } from "@/lib/types";

export type Tone = "ink" | "accent" | "ok" | "warn" | "crit" | "cool" | "plum" | "mute";

const toneText: Record<Tone, string> = {
  ink: "text-ink",
  accent: "text-accent-deep",
  ok: "text-ok",
  warn: "text-warn",
  crit: "text-crit",
  cool: "text-cool",
  plum: "text-plum",
  mute: "text-mute",
};

const toneChip: Record<Tone, string> = {
  ink: "bg-sunk text-ink2 border-line2",
  accent: "bg-accent-faint text-accent-deep border-accent/40",
  ok: "bg-ok-soft text-ok border-ok/30",
  warn: "bg-warn-soft text-warn border-warn/30",
  crit: "bg-crit-soft text-crit border-crit/30",
  cool: "bg-cool-soft text-cool border-cool/30",
  plum: "bg-plum-soft text-plum border-plum/30",
  mute: "bg-sunk text-mute border-line",
};

export const toneColor = (t: Tone): string =>
  ({ ink: C.ink, accent: C.accent, ok: C.ok, warn: C.warn, crit: C.crit, cool: C.cool, plum: C.plum, mute: C.mute })[t];

/* ---------------- section header ---------------- */

export function Sec({
  no,
  title,
  right,
  className,
}: {
  no?: string;
  title: string;
  right?: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("flex items-baseline justify-between gap-3 border-b hairline pb-1.5", className)}>
      <div className="flex items-baseline gap-2 min-w-0">
        {no && <span className="mono text-[10px] text-faint">{no}</span>}
        <span className="text-[11px] font-semibold uppercase tracking-[0.12em] text-ink2 truncate">{title}</span>
      </div>
      {right && <div className="shrink-0">{right}</div>}
    </div>
  );
}

/* ---------------- tag / chip ---------------- */

export function Tag({ tone = "ink", children, className }: { tone?: Tone; children: ReactNode; className?: string }) {
  return (
    <span className={cn("inline-flex items-center gap-1 border px-1.5 py-px mono text-[9.5px] uppercase tracking-[0.08em] leading-[1.5]", toneChip[tone], className)}>
      {children}
    </span>
  );
}

export function Dot({ tone = "ink", className, blink }: { tone?: Tone; className?: string; blink?: boolean }) {
  return (
    <span
      className={cn("inline-block size-[7px] rounded-full", blink && "blink", className)}
      style={{ background: toneColor(tone) }}
    />
  );
}

/* ---------------- score / meter bars ---------------- */

export function Meter({ v, tone = "ink", w = 56, h = 3 }: { v: number; tone?: Tone; w?: number | string; h?: number }) {
  return (
    <span className="inline-block align-middle bg-line" style={{ width: w, height: h }}>
      <span className="block h-full" style={{ width: `${Math.max(0, Math.min(1, v)) * 100}%`, background: toneColor(tone) }} />
    </span>
  );
}

/** One real score term. The bar is the term's own effect; the number is that effect, never a guess. */
export function TermBar({
  label,
  effect,
  max,
  tone = "ink",
}: {
  label: string;
  effect: number;
  max: number;
  tone?: Tone;
}) {
  const frac = max > 0 ? Math.min(1, Math.abs(effect) / max) : 0;
  return (
    <div className="flex items-center gap-2">
      <span className="mono text-[9px] tracking-[0.04em] text-mute w-[128px] shrink-0 truncate" title={label}>
        {label}
      </span>
      <span className="relative h-[3px] flex-1 bg-line/70">
        <span className="absolute inset-y-0 left-0" style={{ width: `${frac * 100}%`, background: toneColor(tone) }} />
      </span>
      <span className={cn("mono text-[9.5px] w-9 text-right", toneText[tone])}>{effect.toFixed(3)}</span>
    </div>
  );
}

/* ---------------- sparkline ---------------- */

export function Spark({ data, w = 72, h = 22, tone = "ink", base }: { data: number[]; w?: number; h?: number; tone?: Tone; base?: number }) {
  if (data.length < 2) return null;
  const min = base ?? Math.min(...data);
  const max = Math.max(...data);
  const span = max - min || 1;
  const pts = data.map((d, i) => `${(i / (data.length - 1)) * (w - 2) + 1},${h - 2 - ((d - min) / span) * (h - 4)}`).join(" ");
  return (
    <svg width={w} height={h} className="block">
      <polyline points={pts} fill="none" stroke={toneColor(tone)} strokeWidth={1.2} strokeLinejoin="round" />
    </svg>
  );
}

/* ---------------- coverage ring (always paired with its number) ---------------- */

export function Ring({ v, size = 40, label }: { v: number; size?: number; label?: string }) {
  const r = (size - 6) / 2;
  const c = 2 * Math.PI * r;
  const tone: Tone = v >= 0.8 ? "ok" : v >= 0.5 ? "warn" : "crit";
  return (
    <span className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={C.line} strokeWidth={2.5} />
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={toneColor(tone)} strokeWidth={2.5}
          strokeDasharray={`${c * v} ${c}`} strokeLinecap="butt" />
      </svg>
      <span className={cn("absolute mono text-[9px]", toneText[tone])}>{label ?? `${Math.round(v * 100)}%`}</span>
    </span>
  );
}

/* ---------------- key/value row ---------------- */

export function KV({ k, v, tone }: { k: string; v: ReactNode; tone?: Tone }) {
  return (
    <div className="flex items-baseline justify-between gap-3 py-[3px]">
      <span className="mono text-[9.5px] uppercase tracking-[0.07em] text-mute">{k}</span>
      <span className={cn("mono text-[11px] text-right", tone ? toneText[tone] : "text-ink")}>{v}</span>
    </div>
  );
}

/* ---------------- domain maps over the vocabularies the service emits ---------------- */

export const OUTCOME_LABEL: Record<string, string> = {
  met_borrower: "Borrower met",
  met_family: "Family met",
  cash_collected: "Cash collected",
  locked_premises: "Locked premises",
  neighbour_says_shifted: "Neighbour: shifted",
  address_not_traceable: "Not traceable",
  no_such_person: "No such person",
};

export const OUTCOME_TONE: Record<string, Tone> = {
  met_borrower: "ok",
  met_family: "ok",
  cash_collected: "ok",
  locked_premises: "warn",
  neighbour_says_shifted: "plum",
  address_not_traceable: "crit",
  no_such_person: "crit",
};

export const POLARITY_TONE: Record<string, Tone> = {
  positive: "ok",
  negative: "crit",
  ambiguous: "warn",
};

export const STATE_TONE: Record<PlaceState, Tone> = {
  CONFIRMED: "ok",
  WARM: "accent",
  COLD: "mute",
  MOVED_SUSPECTED: "warn",
  CONTESTED: "plum",
};

export const TIER_TONE: Record<Tier, Tone> = {
  CONFIRMED: "ok",
  PROBABLE: "accent",
  APPROXIMATE: "cool",
};

export const STATUS_TONE: Record<BeliefStatus, Tone> = {
  STABLE: "ok",
  MOVED_SUSPECTED: "warn",
  CONTESTED: "plum",
};

export const GATE_TONE: Record<GateAction, Tone> = {
  SERVE: "ok",
  VERIFY_FIRST: "accent",
  REFUSE: "crit",
};

export const GATE_LABEL: Record<GateAction, string> = {
  SERVE: "Serve",
  VERIFY_FIRST: "Verify first",
  REFUSE: "Refuse",
};

export const TASK_STATE_TONE: Record<string, Tone> = {
  open: "warn",
  in_progress: "accent",
  resolved: "ok",
  reopened: "plum",
};

/** The four labels Method & Trust is allowed to use about this build. */
export const CAPABILITY_TONE: Record<string, Tone> = {
  IMPLEMENTED: "ok",
  DESIGNED: "accent",
  "NOT YET IMPLEMENTED": "mute",
  "NOT MEASURED": "cool",
};

/* ---------------- typed reason chips ---------------- */

/** A typed reason as the service sent it: the UI renders `label` and `effect`, never parses `code`. */
export function ReasonChip({ rc }: { rc: ReasonCodeT }) {
  return (
    <span
      className={cn(
        "inline-flex items-baseline gap-1.5 border px-1.5 py-px mono text-[9px] leading-[1.6]",
        rc.direction === "positive" ? toneChip.ok : rc.direction === "negative" ? toneChip.crit : toneChip.ink,
      )}
      title={rc.code}
    >
      <span>{rc.label}</span>
      {rc.effect !== null && rc.effect !== undefined && <span className="font-semibold tnum">{rc.effect > 0 ? "+" : ""}{rc.effect.toFixed(3)}</span>}
    </span>
  );
}

/** Raw backend string (a reason list entry) — shown verbatim, never interpreted. */
export function RawCode({ code }: { code: string }) {
  return (
    <span className="mono text-[9px] tracking-[0.04em] text-ink2 bg-sunk border hairline px-1 py-px">{code}</span>
  );
}

export function Empty({ msg }: { msg: string }) {
  return (
    <div className="border border-dashed border-line2 bg-panel/60 px-4 py-8 text-center mono text-[10.5px] text-mute uppercase tracking-[0.1em]">
      {msg}
    </div>
  );
}

export function Panel({
  className, children, onClick, testId,
}: { className?: string; children: ReactNode; onClick?: () => void; testId?: string }) {
  return (
    <div className={cn("bg-raised border hairline", className)} onClick={onClick} data-testid={testId}>
      {children}
    </div>
  );
}

/** Loading / error / empty are real states here: the service decides what exists. */
export function Loading({ what }: { what: string }) {
  return <div className="mono text-[11px] text-mute p-8">reading {what} from the service…</div>;
}

export function Failed({ what, error, onRetry }: { what: string; error: string; onRetry?: () => void }) {
  return (
    <div className="border border-crit/50 bg-crit-soft/50 px-3.5 py-3">
      <div className="mono text-[9.5px] uppercase tracking-[0.12em] text-crit">could not read {what}</div>
      <p className="mono text-[10.5px] text-ink2 mt-1 break-words">{error}</p>
      {onRetry && (
        <button onClick={onRetry} className="mt-2 border border-crit/50 text-crit mono text-[9.5px] uppercase tracking-[0.08em] px-2 py-1 hover:bg-crit-soft">
          retry
        </button>
      )}
    </div>
  );
}
