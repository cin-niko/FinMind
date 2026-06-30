import { History, LogOut, Pencil, Trash2, Check, X } from "lucide-react";
import { useState } from "react";
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
  onRenameConversation: (conversationId: string, title: string) => void;
  onDeleteConversation: (conversationId: string) => void;
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
  onRenameConversation,
  onDeleteConversation,
  onSelectChat,
  children
}: ShellProps) {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [draftTitle, setDraftTitle] = useState("");

  function startRename(conversation: ChatConversation) {
    setEditingId(conversation.id);
    setDraftTitle(getConversationTitle(conversation));
  }

  function commitRename() {
    if (editingId && draftTitle.trim()) {
      onRenameConversation(editingId, draftTitle);
    }
    setEditingId(null);
    setDraftTitle("");
  }

  function cancelRename() {
    setEditingId(null);
    setDraftTitle("");
  }

  function confirmDelete(conversation: ChatConversation) {
    const title = getConversationTitle(conversation);
    if (window.confirm(`Delete this conversation?\n\n${title}`)) {
      onDeleteConversation(conversation.id);
    }
  }

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
              conversations.map((conversation) => {
                const isSelected = conversation.id === selectedChatId;
                const isEditing = editingId === conversation.id;
                return (
                  <div
                    className={isSelected ? "historyRow active" : "historyRow"}
                    key={conversation.id}
                  >
                    {isEditing ? (
                      <div className="historyEdit">
                        <input
                          autoFocus
                          className="historyEditInput"
                          value={draftTitle}
                          onChange={(event) => setDraftTitle(event.target.value)}
                          onKeyDown={(event) => {
                            if (event.key === "Enter") commitRename();
                            if (event.key === "Escape") cancelRename();
                          }}
                          aria-label="Rename conversation"
                        />
                        <button
                          className="historyAction confirm"
                          onClick={commitRename}
                          type="button"
                          aria-label="Save name"
                        >
                          <Check size={14} />
                        </button>
                        <button
                          className="historyAction"
                          onClick={cancelRename}
                          type="button"
                          aria-label="Cancel rename"
                        >
                          <X size={14} />
                        </button>
                      </div>
                    ) : (
                      <>
                        <button
                          className={isSelected ? "historyItem active" : "historyItem"}
                          onClick={() => onSelectChat(conversation.id)}
                          type="button"
                        >
                          {getConversationTitle(conversation)}
                        </button>
                        <div className="historyActions">
                          <button
                            className="historyAction"
                            onClick={() => startRename(conversation)}
                            type="button"
                            aria-label="Rename conversation"
                          >
                            <Pencil size={13} />
                          </button>
                          <button
                            className="historyAction danger"
                            onClick={() => confirmDelete(conversation)}
                            type="button"
                            aria-label="Delete conversation"
                          >
                            <Trash2 size={13} />
                          </button>
                        </div>
                      </>
                    )}
                  </div>
                );
              })
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
