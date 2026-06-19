import { History, LogOut } from "lucide-react";
import type { ReactNode } from "react";
import type { ChatConversation } from "../chat/mockChat";
import { getConversationTitle } from "../chat/mockChat";
import type { WorkflowRun } from "../../api/client";
import { HISTORY_SECTIONS, PRIMARY_NAV_ITEMS } from "./shellNavigation";

type ShellProps = {
  active: "chat" | "dataHub" | "workflows" | "results";
  role: string;
  chatHistory: ChatConversation[];
  workflowRuns: WorkflowRun[];
  selectedChatId: string | null;
  selectedRunId: string | null;
  onNavigate: (view: "chat" | "dataHub" | "workflows" | "results") => void;
  onSelectChat: (conversationId: string) => void;
  onSelectRun: (run: WorkflowRun) => void;
  onLogout: () => void;
  children: ReactNode;
};

export function AppShell({
  active,
  role,
  chatHistory,
  workflowRuns,
  selectedChatId,
  selectedRunId,
  onNavigate,
  onSelectChat,
  onSelectRun,
  onLogout,
  children
}: ShellProps) {
  return (
    <div className="shell">
      <aside className="leftRail" aria-label="Primary navigation">
        <div className="brand">FinMind</div>
        <nav className="primaryNav" aria-label="Primary surfaces">
          {PRIMARY_NAV_ITEMS.map(({ view, label, Icon }) => {
            const isActive = view === "workflows" ? active === "workflows" || active === "results" : active === view;
            return (
              <button className={isActive ? "navItem active" : "navItem"} onClick={() => onNavigate(view)} type="button" key={view}>
                <Icon size={17} /> {label}
              </button>
            );
          })}
        </nav>
        <section className="historySection" aria-label="History">
          <div className="railHeading">
            <History size={14} /> History
          </div>
          <div className="historyGroup">
            <span className="historySubhead">{HISTORY_SECTIONS[0].label}</span>
            {chatHistory.length ? (
              chatHistory.map((conversation) => (
                <button
                  className={conversation.id === selectedChatId ? "historyItem active" : "historyItem"}
                  key={conversation.id}
                  onClick={() => onSelectChat(conversation.id)}
                  type="button"
                >
                  {getConversationTitle(conversation)}
                </button>
              ))
            ) : (
              <span className="emptyHistory">No chats yet</span>
            )}
          </div>
          <div className="historyGroup">
            <span className="historySubhead">{HISTORY_SECTIONS[1].label}</span>
            {workflowRuns.length ? (
              workflowRuns.map((run) => (
                <button
                  className={run.id === selectedRunId ? "historyItem active" : "historyItem"}
                  key={run.id}
                  onClick={() => onSelectRun(run)}
                  type="button"
                >
                  {run.id}
                </button>
              ))
            ) : (
              <span className="emptyHistory">No runs yet</span>
            )}
          </div>
        </section>
        <div className="railFooter">
          <div>
            <div className="railUser">{role}</div>
            <div className="railUserMeta">Signed in</div>
          </div>
          <button className="iconButton" onClick={onLogout} type="button" aria-label={`Log out ${role}`}>
            <LogOut size={18} />
          </button>
        </div>
      </aside>
      <main className="workArea">{children}</main>
    </div>
  );
}
