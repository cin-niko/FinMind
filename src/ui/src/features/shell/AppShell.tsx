import { BarChart3, FileText, LogOut } from "lucide-react";
import type { ReactNode } from "react";

type ShellProps = {
  title: string;
  active: "workflow" | "results";
  role: string;
  onNavigate: (view: "workflow" | "results") => void;
  onLogout: () => void;
  children: ReactNode;
};

export function AppShell({ title, active, role, onNavigate, onLogout, children }: ShellProps) {
  return (
    <div className="shell">
      <aside className="leftRail" aria-label="Primary navigation">
        <div className="brand">FinMind</div>
        <button
          className={active === "workflow" ? "navItem active" : "navItem"}
          onClick={() => onNavigate("workflow")}
          type="button"
        >
          <BarChart3 size={18} /> Workflow
        </button>
        <button
          className={active === "results" ? "navItem active" : "navItem"}
          onClick={() => onNavigate("results")}
          type="button"
        >
          <FileText size={18} /> Results
        </button>
      </aside>
      <main className="workArea">
        <header className="topBar">
          <div>
            <h1>{title}</h1>
            <span className="meta">VN stocks and gold · Phase 1 MVP</span>
          </div>
          <div className="session">
            <span className="badge">{role}</span>
            <button className="iconButton" onClick={onLogout} type="button" aria-label="Log out">
              <LogOut size={18} />
            </button>
          </div>
        </header>
        {children}
      </main>
    </div>
  );
}
