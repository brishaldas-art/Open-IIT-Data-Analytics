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

/** deterministic PRNG for fixture jitter */
export function mulberry32(seed: number) {
  let a = seed >>> 0;
  return () => {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
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

export const fmtScore = (v: number) => v.toFixed(2);

/** pseudo hash chain link */
export function chainHash(prev: string, payload: string): string {
  let h = 0;
  const s = prev + payload;
  for (let i = 0; i < s.length; i++) {
    h = (Math.imul(h, 31) + s.charCodeAt(i)) >>> 0;
    h ^= h >>> 13;
  }
  let out = "";
  let x = h;
  for (let i = 0; i < 3; i++) {
    x = (Math.imul(x, 2654435761) + i * 97) >>> 0;
    x ^= x >>> 15;
    out += (x >>> 0).toString(16).padStart(8, "0");
  }
  return out.slice(0, 16);
}
