import { ChevronsLeft, ChevronsRight, History, LogOut, MoreVertical, Pencil, Settings, Trash2 } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";
import type { ChatConversation } from "../chat/mockChat";
import { getConversationTitle } from "../chat/mockChat";
import { PRIMARY_NAV_ITEMS } from "./shellNavigation";
import type { LanguageSelection } from "../settings/language";
import { useI18n } from "../settings/i18n";

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
  languageSelection?: LanguageSelection;
  onLanguageSelectionChange?: (selection: LanguageSelection) => void;
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
  languageSelection = "auto",
  onLanguageSelectionChange = () => undefined,
  children
}: ShellProps) {
  const { t } = useI18n();
  const [editingId, setEditingId] = useState<string | null>(null);
  const [draftTitle, setDraftTitle] = useState("");
  const [openMenuId, setOpenMenuId] = useState<string | null>(null);
  const [menuPosition, setMenuPosition] = useState({ left: 0, top: 0 });
  const [leftRailCollapsed, setLeftRailCollapsed] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
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
    if (window.confirm(t("deleteConversationConfirm", { title }))) {
      onDeleteConversation(conversation.id);
    }
  }

  const openMenuConversation =
    conversations.find((conversation) => conversation.id === openMenuId) ?? null;

  return (
    <div className={leftRailCollapsed ? "shell leftCollapsed" : "shell"}>
      <aside className="leftRail" aria-label={t("primaryNav")}>
        <div className="brandRow">
          <div className="brand">{leftRailCollapsed ? "FM" : "FinMind"}</div>
          <button
            aria-label={leftRailCollapsed ? t("expandLeftPanel") : t("collapseLeftPanel")}
            className="iconButton panelToggleButton"
            onClick={() => setLeftRailCollapsed((current) => !current)}
            type="button"
            title={leftRailCollapsed ? t("expandLeftPanel") : t("collapseLeftPanel")}
          >
            {leftRailCollapsed ? <ChevronsRight size={17} /> : <ChevronsLeft size={17} />}
          </button>
        </div>
        <nav className="primaryNav" aria-label={t("primarySurfaces")}>
          {PRIMARY_NAV_ITEMS.map(({ view, Icon }) => {
            const translatedLabel = view === "chat" ? t("newChat") : t("workflows");
            return (
            <button
              className={active === view ? "navItem active" : "navItem"}
              onClick={() => onNavigate(view)}
              type="button"
              key={view}
              aria-label={leftRailCollapsed ? translatedLabel : undefined}
              title={leftRailCollapsed ? translatedLabel : undefined}
            >
              <Icon size={17} />
              <span className="navLabel">{translatedLabel}</span>
            </button>
          )})}
        </nav>
        <section className="historySection" aria-label={t("history")}>
          <div className="railHeading">
            <History size={14} /> {t("history")}
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
                          aria-label={t("renameConversation")}
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
                            aria-label={t("conversationActions")}
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
              <span className="emptyHistory">{t("noHistory")}</span>
            )}
          </div>
        </section>
        <div className="railFooter">
          <div>
            <div className="railUser">{role}</div>
            <div className="railUserMeta">{t("signedIn")}</div>
          </div>
          <button
            className="iconButton"
            onClick={() => setSettingsOpen(true)}
            type="button"
            aria-label={t("openSettings")}
            title={t("settings")}
          >
            <Settings size={18} />
          </button>
          <button className="iconButton" onClick={onLogout} type="button" aria-label={t("logoutRole", { role })}>
            <LogOut size={18} />
          </button>
        </div>
      </aside>
      {openMenuConversation ? (
        <div
          className="historyMenu"
          role="menu"
          aria-label={t("conversationActions")}
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
            <span>{t("rename")}</span>
          </button>
          <button
            className="historyMenuItem danger"
            onClick={() => confirmDelete(openMenuConversation)}
            role="menuitem"
            type="button"
          >
            <Trash2 size={14} />
            <span>{t("delete")}</span>
          </button>
        </div>
      ) : null}
      {settingsOpen ? (
        <div className="workflowDialogOverlay" onClick={() => setSettingsOpen(false)}>
          <section
            className="settingsDialog"
            role="dialog"
            aria-modal="true"
            aria-labelledby="settings-title"
            onClick={(event) => event.stopPropagation()}
          >
            <button className="dialogCloseButton" onClick={() => setSettingsOpen(false)} type="button" aria-label={t("closeSettings")}>×</button>
            <h2 id="settings-title">{t("settings")}</h2>
            <label className="settingsField" htmlFor="language-selection">
              {t("language")}
              <select
                id="language-selection"
                value={languageSelection}
                onChange={(event) => onLanguageSelectionChange(event.target.value as LanguageSelection)}
              >
                <option value="auto">{t("auto")}</option>
                <option value="en">{t("english")}</option>
                <option value="vi">{t("vietnamese")}</option>
              </select>
            </label>
          </section>
        </div>
      ) : null}
      <main className="workArea">{children}</main>
    </div>
  );
}
