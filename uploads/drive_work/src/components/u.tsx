import type { ReactNode } from "react";
import { cn, C } from "@/lib/utils";
import type { CaseKind, PlaceState, TrailOutcome, VisitOutcome } from "@/lib/types";

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

export function ScoreBar({ label, v, tone = "ink" }: { label: string; v: number; tone?: Tone }) {
  return (
    <div className="flex items-center gap-2">
      <span className="mono text-[9px] uppercase tracking-[0.06em] text-mute w-[74px] shrink-0">{label}</span>
      <span className="relative h-[3px] flex-1 bg-line/70">
        <span className="absolute inset-y-0 left-0" style={{ width: `${v * 100}%`, background: toneColor(tone) }} />
      </span>
      <span className={cn("mono text-[9.5px] w-7 text-right", toneText[tone])}>{v.toFixed(2)}</span>
    </div>
  );
}

/* ---------------- sparkline ---------------- */

export function Spark({ data, w = 72, h = 22, tone = "ink", base }: { data: number[]; w?: number; h?: number; tone?: Tone; base?: number }) {
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

/* ---------------- quality ring ---------------- */

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
      <span className={cn("absolute mono text-[9px]", toneText[tone])}>{label ?? v.toFixed(2).slice(1)}</span>
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

/* ---------------- domain tag maps ---------------- */

export const OUTCOME_TONE: Record<VisitOutcome, Tone> = {
  CONFIRMED: "ok",
  NOT_FOUND: "crit",
  MOVED: "warn",
  REFUTED: "crit",
  PARTIAL: "cool",
};

export const TRAIL_TONE: Record<TrailOutcome, Tone> = {
  confirm: "ok",
  refute: "crit",
  relocate: "warn",
  search: "cool",
};

export const KIND_TONE: Record<CaseKind, Tone> = {
  VERIFY_FIRST: "accent",
  REVERIFICATION: "cool",
  CONTESTED: "plum",
  MOVED_SUSPECTED: "warn",
  UNPLACEABLE: "crit",
};

export const KIND_LABEL: Record<CaseKind, string> = {
  VERIFY_FIRST: "Verify first",
  REVERIFICATION: "Reverification",
  CONTESTED: "Contested",
  MOVED_SUSPECTED: "Moved suspected",
  UNPLACEABLE: "Unplaceable",
};

export const STATE_TONE: Record<PlaceState, Tone> = {
  STABLE: "ok",
  PROVISIONAL: "cool",
  CONTESTED: "plum",
  STALE: "warn",
  RETIRED: "mute",
};

export function ReasonCode({ code }: { code: string }) {
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

export function Panel({ className, children }: { className?: string; children: ReactNode }) {
  return <div className={cn("bg-raised border hairline", className)}>{children}</div>;
}
