import { ChevronsLeft, ChevronsRight, History, LogOut, MoreVertical, Pencil, Trash2 } from "lucide-react";
import { useEffect, useRef, useState } from "react";
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

const MENU_WIDTH = 150;

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
  const [openMenuId, setOpenMenuId] = useState<string | null>(null);
  const [menuPosition, setMenuPosition] = useState({ left: 0, top: 0 });
  const [leftRailCollapsed, setLeftRailCollapsed] = useState(false);
  const menuRootRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!openMenuId) return;

    function closeOnOutsidePointer(event: PointerEvent) {
      if (menuRootRef.current?.contains(event.target as Node)) return;
      setOpenMenuId(null);
    }

    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setOpenMenuId(null);
      }
    }

    document.addEventListener("pointerdown", closeOnOutsidePointer);
    document.addEventListener("keydown", closeOnEscape);
    window.addEventListener("resize", closeMenu);
    window.addEventListener("scroll", closeMenu, true);
    return () => {
      document.removeEventListener("pointerdown", closeOnOutsidePointer);
      document.removeEventListener("keydown", closeOnEscape);
      window.removeEventListener("resize", closeMenu);
      window.removeEventListener("scroll", closeMenu, true);
    };

    function closeMenu() {
      setOpenMenuId(null);
    }
  }, [openMenuId]);

  function toggleMenu(conversationId: string, trigger: HTMLButtonElement) {
    setOpenMenuId((current) => {
      if (current === conversationId) {
        return null;
      }

      const rect = trigger.getBoundingClientRect();
      setMenuPosition({
        left: Math.min(window.innerWidth - MENU_WIDTH - 12, Math.max(12, rect.right - 54)),
        top: Math.min(window.innerHeight - 128, rect.bottom + 6)
      });
      return conversationId;
    });
  }

  function startRename(conversation: ChatConversation) {
    setOpenMenuId(null);
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

  function confirmDelete(conversation: ChatConversation) {
    setOpenMenuId(null);
    const title = getConversationTitle(conversation);
    if (window.confirm(`Delete this conversation?\n\n${title}`)) {
      onDeleteConversation(conversation.id);
    }
  }

  const openMenuConversation =
    conversations.find((conversation) => conversation.id === openMenuId) ?? null;

  return (
    <div className={leftRailCollapsed ? "shell leftCollapsed" : "shell"}>
      <aside className="leftRail" aria-label="Primary navigation">
        <div className="brandRow">
          <div className="brand">{leftRailCollapsed ? "FM" : "FinMind"}</div>
          <button
            aria-label={leftRailCollapsed ? "Expand left panel" : "Collapse left panel"}
            className="iconButton panelToggleButton"
            onClick={() => setLeftRailCollapsed((current) => !current)}
            type="button"
            title={leftRailCollapsed ? "Expand left panel" : "Collapse left panel"}
          >
            {leftRailCollapsed ? <ChevronsRight size={17} /> : <ChevronsLeft size={17} />}
          </button>
        </div>
        <nav className="primaryNav" aria-label="Primary surfaces">
          {PRIMARY_NAV_ITEMS.map(({ view, label, Icon }) => (
            <button
              className={active === view ? "navItem active" : "navItem"}
              onClick={() => onNavigate(view)}
              type="button"
              key={view}
              aria-label={leftRailCollapsed ? label : undefined}
              title={leftRailCollapsed ? label : undefined}
            >
              <Icon size={17} />
              <span className="navLabel">{label}</span>
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
                          onBlur={commitRename}
                          onKeyDown={(event) => {
                            if (event.key === "Enter") {
                              event.preventDefault();
                              event.currentTarget.blur();
                            }
                          }}
                          aria-label="Rename conversation"
                        />
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
                            className={openMenuId === conversation.id ? "historyAction menu active" : "historyAction menu"}
                            onClick={(event) => {
                              event.stopPropagation();
                              toggleMenu(conversation.id, event.currentTarget);
                            }}
                            type="button"
                            aria-label="Conversation actions"
                            aria-haspopup="menu"
                            aria-expanded={openMenuId === conversation.id}
                          >
                            <MoreVertical size={15} />
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
      {openMenuConversation ? (
        <div
          className="historyMenu"
          role="menu"
          aria-label="Conversation actions"
          ref={menuRootRef}
          style={{ left: menuPosition.left, top: menuPosition.top }}
        >
          <button
            className="historyMenuItem"
            onClick={() => startRename(openMenuConversation)}
            role="menuitem"
            type="button"
          >
            <Pencil size={14} />
            <span>Rename</span>
          </button>
          <button
            className="historyMenuItem danger"
            onClick={() => confirmDelete(openMenuConversation)}
            role="menuitem"
            type="button"
          >
            <Trash2 size={14} />
            <span>Delete</span>
          </button>
        </div>
      ) : null}
      <main className="workArea">{children}</main>
    </div>
  );
}
