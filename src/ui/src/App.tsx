import { useEffect, useState } from "react";
import { getSession, logout, type SessionState, type WorkflowRun } from "./api/client";
import { LoadingState } from "./components/layout";
import { LoginPage } from "./features/auth/LoginPage";
import { ResultView } from "./features/results/ResultView";
import { AppShell } from "./features/shell/AppShell";
import { WorkflowPage } from "./features/workflows/WorkflowPage";

type View = "workflow" | "results";

export function App() {
  const [session, setSession] = useState<SessionState | null>(null);
  const [view, setView] = useState<View>("workflow");
  const [currentRun, setCurrentRun] = useState<WorkflowRun | null>(null);

  useEffect(() => {
    getSession().then(setSession).catch(() => setSession({ authenticated: false }));
  }, []);

  if (!session) {
    return <LoadingState />;
  }

  if (!session.authenticated) {
    return <LoginPage onAuthenticated={setSession} />;
  }

  async function handleLogout() {
    const next = await logout();
    setSession(next);
    setCurrentRun(null);
    setView("workflow");
  }

  function handleRunComplete(run: WorkflowRun) {
    setCurrentRun(run);
    setView("results");
  }

  return (
    <AppShell
      active={view}
      onLogout={handleLogout}
      onNavigate={setView}
      role={session.role}
      title={view === "workflow" ? "Workflow" : "Results"}
    >
      {view === "workflow" ? <WorkflowPage onRunComplete={handleRunComplete} /> : null}
      {view === "results" ? <ResultView run={currentRun} /> : null}
    </AppShell>
  );
}
