/* ------------------------------------------------------------------ *
 * DATA ACCESS SEAM — every view reads through these fetchers.
 *
 * The workbench is served by the SUTRA service itself: all calls are
 * same-origin relative URLs. Nothing here invents a value, a delay, a
 * delay-shaped promise or an identifier: a canonical client key
 * (idempotency key) is the only thing the browser mints, and only so a
 * retried write cannot be applied twice.
 * ------------------------------------------------------------------ */

import { useEffect, useRef, useState } from "react";
import type {
  AddressGeometry,
  AdjudicationDecision,
  AdjudicationResponse,
  AuditResponse,
  CasePayload,
  EvidenceResponse,
  HealthResponse,
  MethodTrust,
  OverviewResponse,
  PlaceDetail,
  PlacesResponse,
  ResolveResponse,
  TaskDetail,
  TaskTransition,
  TasksResponse,
  TownPlane,
} from "./types";

export class ApiError extends Error {
  status: number;
  detail: string;
  constructor(status: number, detail: string, path: string) {
    super(`${path} → ${status}: ${detail}`);
    this.status = status;
    this.detail = detail;
  }
}

/** One as-of for the whole workbench, set by the shell from the service's own cut. */
let AS_OF: string | null = null;
export const setAsOf = (v: string | null) => { AS_OF = v; };
export const getAsOf = () => AS_OF;

const qs = (params: Record<string, string | number | null | undefined | false> = {}) => {
  const p = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v === null || v === undefined || v === false) continue;
    p.set(k, String(v));
  }
  const s = p.toString();
  return s ? `?${s}` : "";
};

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  let r: Response;
  try {
    r = await fetch(path, { ...init, headers: { accept: "application/json", ...(init?.headers || {}) } });
  } catch (e) {
    throw new ApiError(0, `service unreachable (${(e as Error).message})`, path);
  }
  const text = await r.text();
  let body: unknown = null;
  try { body = text ? JSON.parse(text) : null; } catch { /* non-JSON error body */ }
  if (!r.ok) {
    const d = (body as { detail?: string; error?: string } | null)?.detail
      || (body as { error?: string } | null)?.error || r.statusText;
    throw new ApiError(r.status, String(d), path);
  }
  return body as T;
}

const GET = <T,>(path: string, params?: Record<string, string | number | null | undefined | false>) =>
  req<T>(path + qs(params));

const POST = <T,>(path: string, body: unknown) =>
  req<T>(path, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body) });

const PATCH = <T,>(path: string, body: unknown) =>
  req<T>(path, { method: "PATCH", headers: { "content-type": "application/json" }, body: JSON.stringify(body) });

/* ---------------- reads ---------------- */

/** GET /health — every number in it is counted or read. */
export const fetchHealth = () => GET<HealthResponse>("/health");

/** GET /v1/overview */
export const fetchOverview = () => GET<OverviewResponse>("/v1/overview", { as_of: AS_OF });

/** GET /v1/method-trust — the frozen evaluation and the status labels. */
export const fetchMethodTrust = () => GET<MethodTrust>("/v1/method-trust");

/** GET /v1/places — the place list (projection over stored beliefs). */
export const fetchPlaces = (p: { q?: string; state?: string; tier?: string; town_id?: string; limit?: number } = {}) =>
  GET<PlacesResponse>("/v1/places", { ...p, as_of: AS_OF });

/** GET /v1/place/{place_id} */
export const fetchPlace = (placeId: string) => GET<PlaceDetail>(`/v1/place/${encodeURIComponent(placeId)}`, { as_of: AS_OF });

/** GET /v1/evidence — the visit feed. */
export const fetchEvidence = (p: { q?: string; outcome?: string; polarity?: string; town_id?: string; limit?: number } = {}) =>
  GET<EvidenceResponse>("/v1/evidence", { ...p, as_of: AS_OF });

/** GET /v1/tasks */
export const fetchTasks = (p: { state?: string; cause?: string; town_id?: string; limit?: number } = {}) =>
  GET<TasksResponse>("/v1/tasks", { ...p, as_of: AS_OF });

/** GET /v1/tasks/{task_id} */
export const fetchTask = (taskId: string) => GET<TaskDetail>(`/v1/tasks/${encodeURIComponent(taskId)}`);

/** GET /v1/address/{address_id}/case — belief + place + task + timeline + decision ticket. */
export const fetchCase = (addressId: string) => GET<CasePayload>(`/v1/address/${encodeURIComponent(addressId)}/case`, { as_of: AS_OF });

/** GET /v1/geometry/{address_id} — the address-scoped plane payload. */
export const fetchGeometry = (addressId: string, purpose = "FIELD_NAVIGATION") =>
  GET<AddressGeometry>(`/v1/geometry/${encodeURIComponent(addressId)}`, { as_of: AS_OF, request_purpose: purpose });

/** GET /v1/plane/{town_id} — town reference geometry (localities + official landmarks). */
export const fetchTownPlane = (townId: string) => GET<TownPlane>(`/v1/plane/${encodeURIComponent(townId)}`, { as_of: AS_OF });

/** GET /v1/audit/{belief_id} — why the answer is what it is, step by step.
 *  Belief ids are `AD######:<version>`; the colon belongs to the identifier and is left unescaped. */
const seg = (v: string) => encodeURIComponent(v).replace(/%3A/gi, ":");
export const fetchAudit = (beliefId: string) => GET<AuditResponse>(`/v1/audit/${seg(beliefId)}`);

/* ---------------- writes ---------------- */

/** POST /resolve — free text, or an address id from the store. */
export const resolveAddress = (body: { address_text?: string; address_id?: string; town_hint?: string; request_purpose?: string }) =>
  POST<ResolveResponse>("/resolve", { ...body, as_of: AS_OF, request_purpose: body.request_purpose ?? "FIELD_NAVIGATION" });

/** POST /v1/adjudicate — the only human ground-truth write. Idempotent by key. */
export const adjudicate = (body: {
  task_id?: string; address_id?: string; decision: AdjudicationDecision;
  actor: string; note?: string; idempotency_key: string;
}) => POST<AdjudicationResponse>("/v1/adjudicate", body);

/** PATCH /v1/tasks/{task_id} — append-only lifecycle transition. */
export const transitionTask = (taskId: string, body: { state: string; actor: string; note?: string }) =>
  PATCH<TaskTransition>(`/v1/tasks/${encodeURIComponent(taskId)}`, body);

/** A canonical client key: unique per attempted action, re-used on retry so the write is idempotent. */
export const newIdempotencyKey = (scope: string) =>
  `wb-${scope}-${(globalThis.crypto?.randomUUID?.() ?? `${performance.now()}`).replace(/-/g, "").slice(0, 24)}`;

/* ---------------- tiny async hook ---------------- */

export interface Query<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  reload: () => void;
}

export function useQuery<T>(fn: () => Promise<T>, deps: unknown[] = []): Query<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [nonce, setNonce] = useState(0);
  const seq = useRef(0);
  useEffect(() => {
    const id = ++seq.current;
    setLoading(true);
    setError(null);
    fn()
      .then((d) => { if (seq.current === id) { setData(d); setLoading(false); } })
      .catch((e: Error) => { if (seq.current === id) { setError(e.message); setLoading(false); } });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, nonce]);
  return { data, loading, error, reload: () => setNonce((n) => n + 1) };
}
