import { History, LogOut } from "lucide-react";
import type { ReactNode } from "react";
import type { ChatConversation } from "../chat/mockChat";
import { getConversationTitle } from "../chat/mockChat";
import { PRIMARY_NAV_ITEMS } from "./shellNavigation";

type ShellProps = {
  active: "chat" | "workflows";
  role: string;
  conversations: ChatConversation[];
  selectedChatId: string | null;
  onLogout: () => void;
  onNavigate: (view: "chat" | "workflows") => void;
  onSelectChat: (conversationId: string) => void;
  children: ReactNode;
};

export function AppShell({
  active,
  role,
  conversations,
  selectedChatId,
  onLogout,
  onNavigate,
  onSelectChat,
  children
}: ShellProps) {
  return (
    <div className="shell">
      <aside className="leftRail" aria-label="Primary navigation">
        <div className="brand">FinMind</div>
        <nav className="primaryNav" aria-label="Primary surfaces">
          {PRIMARY_NAV_ITEMS.map(({ view, label, Icon }) => (
            <button
              className={active === view ? "navItem active" : "navItem"}
              onClick={() => onNavigate(view)}
              type="button"
              key={view}
            >
              <Icon size={17} /> {label}
            </button>
          ))}
        </nav>
        <section className="historySection" aria-label="History">
          <div className="railHeading">
            <History size={14} /> History
          </div>
          <div className="historyGroup">
            {conversations.length ? (
              conversations.map((conversation) => (
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
              <span className="emptyHistory">No history yet</span>
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
