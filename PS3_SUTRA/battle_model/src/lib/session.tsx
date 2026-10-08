/* ------------------------------------------------------------------ *
 * SESSION — what is genuinely the browser's business:
 *
 *   · transient operator notices (toasts) that echo a backend response
 *   · the as-of cut the workbench is looking at (default = the service's
 *     own `as_of_cut`) — a real SUTRA feature, not a demo switch
 *   · the reviewer identity that will be written to the audit trail
 *
 * The audit ledger is NOT here. It lives in the store, is written by the
 * service, and is read back through /v1/audit/{belief_id} and the case
 * timeline. A second, browser-side ledger would be a second truth.
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

export interface Notice {
  id: number;
  text: string;
  tone: "info" | "ok" | "warn" | "crit";
}

interface SessionCtx {
  /** The as-of cut every read is answered against. */
  asOf: string;
  setAsOf: (v: string) => void;
  /** The service's own cut, so the workbench can show "reset". */
  defaultAsOf: string;
  adoptCut: (v: string) => void;
  notices: Notice[];
  notify: (text: string, tone?: Notice["tone"]) => void;
  dismiss: (id: number) => void;
  /** Reviewer identity for the human ground-truth write (required by the contract). */
  reviewer: string;
  setReviewer: (v: string) => void;
}

const Ctx = createContext<SessionCtx | null>(null);

export function SessionProvider({ children }: { children: ReactNode }) {
  const [asOf, setAsOfState] = useState("");
  const [defaultAsOf, setDefaultAsOf] = useState("");
  const [notices, setNotices] = useState<Notice[]>([]);
  const [reviewer, setReviewer] = useState("Operator 01");
  const nextId = useRef(1);
  const timers = useRef<Record<number, number>>({});

  const adoptCut = useCallback((v: string) => {
    setDefaultAsOf(v);
    setAsOfState((cur) => cur || v);
  }, []);

  const setAsOf = useCallback((v: string) => setAsOfState(v), []);

  const dismiss = useCallback((id: number) => {
    setNotices((ns) => ns.filter((n) => n.id !== id));
    const t = timers.current[id];
    if (t) window.clearTimeout(t);
    delete timers.current[id];
  }, []);

  const notify = useCallback((text: string, tone: Notice["tone"] = "info") => {
    const id = nextId.current++;
    setNotices((ns) => [...ns.slice(-3), { id, text, tone }]);
    timers.current[id] = window.setTimeout(() => {
      setNotices((ns) => ns.filter((n) => n.id !== id));
      delete timers.current[id];
    }, tone === "crit" ? 9000 : 5200);
  }, []);

  const value = useMemo(
    () => ({ asOf, setAsOf, defaultAsOf, adoptCut, notices, notify, dismiss, reviewer, setReviewer }),
    [asOf, setAsOf, defaultAsOf, adoptCut, notices, notify, dismiss, reviewer],
  );

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useSession(): SessionCtx {
  const v = useContext(Ctx);
  if (!v) throw new Error("useSession outside provider");
  return v;
}

/* ---------------- shared formatting of real values ---------------- */

/** Milliseconds → "12 ms"; a real measured value or nothing at all. */
export const fmtMs = (v: number | null | undefined) => (v === null || v === undefined ? "—" : `${Math.round(v)} ms`);
