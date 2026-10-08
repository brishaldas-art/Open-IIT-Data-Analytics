import { useState } from "react";
import Shell, { type ViewId } from "@/components/Shell";
import { SessionProvider, useSession } from "@/lib/session";
import { CASES } from "@/lib/fixtures";
import Overview from "@/views/Overview";
import Resolver from "@/views/Resolver";
import Places from "@/views/Places";
import FieldEvidence from "@/views/FieldEvidence";
import VerifyQueue from "@/views/VerifyQueue";
import Method from "@/views/Method";

function Workspace() {
  const [view, setView] = useState<ViewId>("resolver");
  const { openCasesDelta } = useSession();
  const queueCount = CASES.length + openCasesDelta;

  return (
    <Shell view={view} setView={setView} queueCount={queueCount}>
      {view === "overview" && <Overview go={setView} queueCount={queueCount} />}
      {view === "resolver" && <Resolver go={setView} />}
      {view === "places" && <Places go={setView} />}
      {view === "evidence" && <FieldEvidence go={setView} />}
      {view === "queue" && <VerifyQueue />}
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
