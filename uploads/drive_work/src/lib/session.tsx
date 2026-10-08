/* ------------------------------------------------------------------ *
 * SESSION STORE — in-browser operational state:
 * hash-chained audit ledger (append-only), verify-queue mutations,
 * resolver intake log, transient operator notices.
 * @backend PATCH/POST /v1/verify/cases · POST /v1/audit/events
 * ------------------------------------------------------------------ */

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import type { AuditEvent, VerifyCase } from "./types";
import { chainHash } from "./utils";

export interface CasePatch {
  assignee?: string;
  closed?: boolean;
  outcome?: string;
  note?: string;
}

interface SessionCtx {
  audit: AuditEvent[];
  push: (action: string, detail: string) => AuditEvent;
  casePatches: Record<string, CasePatch>;
  patchCase: (id: string, p: CasePatch, auditDetail?: string) => void;
  extraCases: VerifyCase[];
  addCase: (c: VerifyCase) => void;
  notice: string | null;
  notify: (msg: string) => void;
  openCasesDelta: number;
}

const Ctx = createContext<SessionCtx | null>(null);

const ACTOR = "OPR K. Deshmukh";

function stamp(): string {
  const d = new Date();
  const p = (n: number) => String(n).padStart(2, "0");
  return `${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`;
}

export function SessionProvider({ children }: { children: ReactNode }) {
  const [audit, setAudit] = useState<AuditEvent[]>([
    { seq: 1, ts: "08:30:04", actor: "SYS", action: "LEDGER_OPEN", detail: "session mounted · fixtures replay window 12–15 Feb 2026", hash: "9f3ac2e10b7d5518" },
    { seq: 2, ts: "08:30:04", actor: "SYS", action: "EPOCH_PIN", detail: `plane SEAL-01 · epoch 2025-W46 retrace`, hash: "41d0bb27c913e6a2" },
  ]);
  const [casePatches, setCasePatches] = useState<Record<string, CasePatch>>({});
  const [extraCases, setExtraCases] = useState<VerifyCase[]>([]);
  const [notice, setNotice] = useState<string | null>(null);
  const headRef = useRef("41d0bb27c913e6a2");
  const seqRef = useRef(2);
  const noticeTimer = useRef<number | null>(null);

  const push = useCallback((action: string, detail: string): AuditEvent => {
    const hash = chainHash(headRef.current, action + detail + Date.now());
    headRef.current = hash;
    const ev: AuditEvent = {
      seq: ++seqRef.current,
      ts: stamp(),
      actor: ACTOR,
      action,
      detail,
      hash,
    };
    setAudit((a) => [...a, ev]);
    return ev;
  }, []);

  const notify = useCallback((msg: string) => {
    setNotice(msg);
    if (noticeTimer.current) window.clearTimeout(noticeTimer.current);
    noticeTimer.current = window.setTimeout(() => setNotice(null), 2800);
  }, []);

  const patchCase = useCallback(
    (id: string, p: CasePatch, auditDetail?: string) => {
      setCasePatches((m) => ({ ...m, [id]: { ...m[id], ...p } }));
      if (auditDetail) push(`CASE_${p.closed ? "CLOSED" : "PATCHED"}`, `${id} · ${auditDetail}`);
    },
    [push],
  );

  const addCase = useCallback((c: VerifyCase) => {
    setExtraCases((xs) => [c, ...xs]);
  }, []);

  const openCasesDelta = useMemo(() => {
    const closed = Object.values(casePatches).filter((p) => p.closed).length;
    return extraCases.length - closed;
  }, [casePatches, extraCases]);

  const value = useMemo(
    () => ({ audit, push, casePatches, patchCase, extraCases, addCase, notify, notice, openCasesDelta }),
    [audit, push, casePatches, patchCase, extraCases, addCase, notify, notice, openCasesDelta],
  );

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useSession(): SessionCtx {
  const v = useContext(Ctx);
  if (!v) throw new Error("useSession outside provider");
  return v;
}
