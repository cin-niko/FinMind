import { useCallback, useEffect, useState } from "react";
import {
  getSession,
  isUnauthorizedError,
  listRuns,
  logout,
  type SessionState,
  type WorkflowRun
} from "./api/client";
import { LoadingState } from "./components/layout";
import { LoginPage } from "./features/auth/LoginPage";
import { ArtifactPanel } from "./features/chat/ArtifactPanel";
import { ChatPage } from "./features/chat/ChatPage";
import {
  createMockResponse,
  createNewConversation,
  createUserMessage,
  getConversationTitle,
  type ChatArtifact,
  type ChatConversation
} from "./features/chat/mockChat";
import { MarketPage } from "./features/market/MarketPage";
import { ResultView } from "./features/results/ResultView";
import { AppShell } from "./features/shell/AppShell";
import { WorkflowPage } from "./features/workflows/WorkflowPage";

type View = "chat" | "market" | "workflows" | "results";

export function App() {
  const [session, setSession] = useState<SessionState | null>(null);
  const [view, setView] = useState<View>("chat");
  const [conversations, setConversations] = useState<ChatConversation[]>([]);
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);
  const [currentRun, setCurrentRun] = useState<WorkflowRun | null>(null);
  const [workflowRuns, setWorkflowRuns] = useState<WorkflowRun[]>([]);
  const [selectedArtifact, setSelectedArtifact] = useState<ChatArtifact | null>(null);

  useEffect(() => {
    getSession().then(setSession).catch(() => setSession({ authenticated: false }));
  }, []);

  const handleSessionExpired = useCallback(() => {
    setSession({ authenticated: false });
    setCurrentRun(null);
    setWorkflowRuns([]);
    setSelectedArtifact(null);
    setView("chat");
  }, []);

  useEffect(() => {
    if (!session?.authenticated) {
      return;
    }
    listRuns()
      .then(setWorkflowRuns)
      .catch((caught) => {
        if (isUnauthorizedError(caught)) {
          handleSessionExpired();
        }
      });
  }, [handleSessionExpired, session]);

  if (!session) {
    return <LoadingState />;
  }

  if (!session.authenticated) {
    return <LoginPage onAuthenticated={setSession} />;
  }

  async function handleLogout() {
    const next = await logout().catch(() => ({ authenticated: false }) as const);
    setSession(next);
    setCurrentRun(null);
    setWorkflowRuns([]);
    setSelectedArtifact(null);
    setView("chat");
  }

  function handleRunComplete(run: WorkflowRun) {
    setCurrentRun(run);
    setWorkflowRuns((runs) => [run, ...runs.filter((existing) => existing.id !== run.id)]);
    setView("results");
  }

  function handleNavigate(nextView: View) {
    setSelectedArtifact(null);
    if (nextView === "chat") {
      setCurrentConversationId(null);
    }
    setView(nextView);
  }

  function handleChatSubmit(message: string) {
    setSelectedArtifact(null);
    if (!currentConversationId) {
      const conversation = createNewConversation(message);
      const response = createMockResponse(message);
      const nextConversation = {
        ...conversation,
        messages: [...conversation.messages, response]
      };
      setConversations((items) => [nextConversation, ...items]);
      setCurrentConversationId(nextConversation.id);
      return;
    }

    setConversations((items) =>
      items.map((conversation) => {
        if (conversation.id !== currentConversationId) {
          return conversation;
        }
        const nextIndex = conversation.messages.filter((item) => item.role === "user").length + 1;
        return {
          ...conversation,
          messages: [
            ...conversation.messages,
            createUserMessage(message, nextIndex),
            createMockResponse(message)
          ]
        };
      })
    );
  }

  const currentConversation =
    conversations.find((conversation) => conversation.id === currentConversationId) ?? null;

  const titleByView: Record<View, string> = {
    chat: currentConversation ? getConversationTitle(currentConversation) : "New Chat",
    market: "Market",
    workflows: "Workflows",
    results: "Workflow Result"
  };

  return (
    <AppShell
      active={view}
      chatHistory={conversations}
      selectedChatId={view === "chat" ? currentConversationId : null}
      selectedRunId={view === "results" ? currentRun?.id ?? null : null}
      workflowRuns={workflowRuns}
      onLogout={handleLogout}
      onNavigate={handleNavigate}
      onSelectChat={(conversationId) => {
        setCurrentConversationId(conversationId);
        setSelectedArtifact(null);
        setView("chat");
      }}
      onSelectRun={(run) => {
        setCurrentRun(run);
        setSelectedArtifact(null);
        setView("results");
      }}
      role={session.role}
    >
      <div className={selectedArtifact ? "contentWithArtifact" : "contentWithArtifact noArtifact"}>
        <div className="primaryPane">
          <header className="topBar">
            <h1>{titleByView[view]}</h1>
            <span className="headerActionSlot" aria-hidden="true" />
          </header>
          <div className={view === "chat" ? "primaryContent chatSurface" : "primaryContent"}>
            {view === "chat" ? (
              <ChatPage
                conversation={currentConversation}
                onSelectArtifact={setSelectedArtifact}
                onSubmit={handleChatSubmit}
              />
            ) : null}
            {view === "market" ? <MarketPage /> : null}
            {view === "workflows" ? (
              <WorkflowPage
                onRunComplete={handleRunComplete}
                onSessionExpired={handleSessionExpired}
              />
            ) : null}
            {view === "results" ? <ResultView run={currentRun} /> : null}
          </div>
        </div>
        <ArtifactPanel artifact={selectedArtifact} onClose={() => setSelectedArtifact(null)} />
      </div>
    </AppShell>
  );
}
