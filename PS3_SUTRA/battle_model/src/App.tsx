import { useCallback, useEffect, useState } from "react";
import Shell, { type ViewId } from "@/components/Shell";
import { SessionProvider, useSession } from "@/lib/session";
import { fetchTasks, useQuery } from "@/lib/api";
import Overview from "@/views/Overview";
import Resolver from "@/views/Resolver";
import Places from "@/views/Places";
import FieldEvidence from "@/views/FieldEvidence";
import VerifyQueue from "@/views/VerifyQueue";
import Method from "@/views/Method";

const VIEWS: ViewId[] = ["overview", "resolver", "places", "evidence", "queue", "method"];

const fromHash = (): ViewId => {
  const h = (window.location.hash || "").replace(/^#\/?/, "") as ViewId;
  return VIEWS.includes(h) ? h : "resolver";
};

function Workspace() {
  const { asOf } = useSession();
  const [view, setView] = useState<ViewId>(fromHash);
  const [focusTask, setFocusTask] = useState<string | null>(null);

  /* deep links: the hash names the destination, the service names everything else */
  useEffect(() => {
    const onHash = () => setView(fromHash());
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  const go = useCallback((v: ViewId) => {
    setView(v);
    window.location.hash = `#/${v}`;
  }, []);

  const openTask = useCallback((taskId: string) => setFocusTask(taskId), []);

  /* one real number for the rail badge: open tasks, counted by the service */
  const { data: openTasks } = useQuery(() => fetchTasks({ state: "open", limit: 1 }), [asOf]);
  const queueCount = openTasks?.total_matching ?? 0;

  return (
    <Shell view={view} setView={go} queueCount={queueCount}>
      {view === "overview" && <Overview go={go} queueCount={queueCount} />}
      {view === "resolver" && <Resolver go={go} openTask={openTask} />}
      {view === "places" && <Places go={go} openTask={openTask} />}
      {view === "evidence" && <FieldEvidence go={go} />}
      {view === "queue" && <VerifyQueue focusTaskId={focusTask} />}
      {view === "method" && <Method />}
    </Shell>
  );
}

export default function App() {
  return (
    <SessionProvider>
      <Workspace />
    </SessionProvider>
  );
}
