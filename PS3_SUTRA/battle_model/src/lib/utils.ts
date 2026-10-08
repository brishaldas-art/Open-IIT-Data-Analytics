import type { LocalPoint } from "./types";

export const cn = (...xs: (string | false | null | undefined)[]) =>
  xs.filter(Boolean).join(" ");

/* ---------------- palette mirror for SVG (var() is unreliable in
   SVG presentation attributes, so we pass concrete values) -------- */

export const C = {
  paper: "#f2eee2",
  panel: "#f8f5ec",
  raised: "#fcfaf3",
  sunk: "#ece7d8",
  line: "#e0d9c5",
  line2: "#c9c0a6",
  line3: "#b3a988",
  ink: "#211d14",
  ink2: "#4a4433",
  mute: "#7c7260",
  faint: "#a2987f",
  accent: "#d2541e",
  accentDeep: "#a63e12",
  accentSoft: "#f5e0cf",
  ok: "#3e7a4c",
  warn: "#a9741b",
  crit: "#b23a2b",
  cool: "#51616c",
  plum: "#6d4f6e",
};

/* ---------------- local-plane maths ---------------- */

export const dist = (a: LocalPoint, b: LocalPoint) => Math.hypot(a.x - b.x, a.y - b.y);

export const lerp = (a: number, b: number, t: number) => a + (b - a) * t;

export function extent(pts: LocalPoint[]): {
  minX: number;
  minY: number;
  maxX: number;
  maxY: number;
} {
  let minX = Infinity,
    minY = Infinity,
    maxX = -Infinity,
    maxY = -Infinity;
  for (const p of pts) {
    if (p.x < minX) minX = p.x;
    if (p.y < minY) minY = p.y;
    if (p.x > maxX) maxX = p.x;
    if (p.y > maxY) maxY = p.y;
  }
  return { minX, minY, maxX, maxY };
}

/* ---------------- formatting ---------------- */

/** metres → "048 213.6" (survey-grouped, fixed width) */
export function fmtCoord(v: number, dp = 1): string {
  const neg = v < 0 ? "−" : "";
  const abs = Math.abs(v);
  const i = Math.floor(abs);
  const f = abs - i;
  const s = String(i).padStart(6, "0");
  const grouped = s.replace(/\B(?=(\d{3})+(?!\d))/g, " ");
  const dec = dp > 0 ? "." + f.toFixed(dp).slice(2) : "";
  return neg + grouped + dec;
}

/** plain grouped integer, e.g. 12,406 */
export const fmtInt = (n: number) => n.toLocaleString("en-IN");

export const fmtM = (v: number, dp = 1) =>
  v >= 1000 ? `${(v / 1000).toFixed(2)} km` : `${v.toFixed(dp)} m`;

export const fmtPct = (v: number, dp = 1) => `${(v * 100).toFixed(dp)}%`;

/** A radius, always in metres and always paired with its unit — number and ring travel together. */
export const fmtRadius = (m: number | null | undefined) =>
  m === null || m === undefined ? "—" : `${m.toFixed(1)} m`;

/** ISO timestamp → "30 May 05:45 UTC" — the store is UTC; the clock in the rail is local. */
export function fmtWhen(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return String(iso);
  const mon = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][d.getUTCMonth()];
  const p = (n: number) => String(n).padStart(2, "0");
  return `${p(d.getUTCDate())} ${mon} ${p(d.getUTCHours())}:${p(d.getUTCMinutes())}Z`;
}

/** ISO timestamp → "2026-05-30" (the day bucket the evidence feed groups by). */
export function dayOf(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? String(iso).slice(0, 10) : d.toISOString().slice(0, 10);
}

/** turn `moved_suspected` / `MOVED_SUSPECTED` into a readable phrase, never a new value */
export const humanise = (s: string | null | undefined) =>
  s ? s.replace(/_/g, " ").toLowerCase() : "—";

export const fmtScore = (v: number) => v.toFixed(2);
