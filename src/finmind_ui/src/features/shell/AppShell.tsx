import { LogOut, MessageSquarePlus } from "lucide-react";
import type { ReactNode } from "react";
import type { ChatConversation } from "../chat/mockChat";
import { getConversationTitle } from "../chat/mockChat";

type ShellProps = {
  active: "chat";
  role: string;
  conversations: ChatConversation[];
  selectedChatId: string | null;
  onLogout: () => void;
  onNavigate: () => void;
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
          <button className={active === "chat" ? "navItem active" : "navItem"} onClick={onNavigate} type="button">
            <MessageSquarePlus size={17} /> New Chat
          </button>
        </nav>
        <section className="historySection" aria-label="History">
          <div className="railHeading">History</div>
          <div className="historyGroup">
            {conversations.length ? (
              conversations.map((conversation) => {
                const title = getConversationTitle(conversation);
                return (
                  <button
                    className={conversation.id === selectedChatId ? "historyItem active" : "historyItem"}
                    key={conversation.id}
                    onClick={() => onSelectChat(conversation.id)}
                    type="button"
                  >
                    {title}
                  </button>
                );
              })
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
