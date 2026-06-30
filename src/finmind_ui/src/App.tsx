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
  createNewConversation,
  createWorkflowAssistantMessage,
  createUserMessage,
  getConversationTitle,
  type ChatArtifact,
  type ChatConversation
} from "./features/chat/mockChat";
import { AppShell } from "./features/shell/AppShell";

export function App() {
  const [session, setSession] = useState<SessionState | null>(null);
  const [conversations, setConversations] = useState<ChatConversation[]>([]);
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);
  const [selectedArtifact, setSelectedArtifact] = useState<ChatArtifact | null>(null);
  const [selectedArtifactRun, setSelectedArtifactRun] = useState<WorkflowRun | null>(null);

  useEffect(() => {
    getSession().then(setSession).catch(() => setSession({ authenticated: false }));
  }, []);

  const handleSessionExpired = useCallback(() => {
    setSession({ authenticated: false });
    setSelectedArtifact(null);
  }, []);

  useEffect(() => {
    if (!session?.authenticated) return;
    listRuns()
      .then((runs) => {
        setConversations(runs.map(runToConversation));
      })
      .catch((caught) => {
        if (isUnauthorizedError(caught)) handleSessionExpired();
      });
  }, [handleSessionExpired, session]);

  if (!session) return <LoadingState />;
  if (!session.authenticated) return <LoginPage onAuthenticated={setSession} />;

  async function handleLogout() {
    const next = await logout().catch(() => ({ authenticated: false }) as const);
    setSession(next);
    setSelectedArtifact(null);
  }

  function handleRunComplete(run: WorkflowRun, userMessage: string) {
    const conversation = createNewConversation(userMessage);
    const assistantMessage = createWorkflowAssistantMessage(run, 1);
    const nextConversation = {
      ...conversation,
      messages: [...conversation.messages, assistantMessage]
    };
    setConversations((items) => [nextConversation, ...items]);
    setCurrentConversationId(nextConversation.id);
  }

  function handleChatSubmit(message: string) {
    if (!currentConversationId) return;
    setConversations((items) =>
      items.map((conversation) => {
        if (conversation.id !== currentConversationId) return conversation;
        const userCount = conversation.messages.filter((m) => m.role === "user").length + 1;
        const userMsg = createUserMessage(message, userCount);
        const assistantMsg = {
          id: `assistant-${userCount}`,
          role: "assistant" as const,
          content: "Follow-up chat is powered by the agentic chatflow (phase 003). This placeholder will connect to the chatflow API when available.",
          blocks: [{ kind: "text" as const, content: "Follow-up chat is powered by the agentic chatflow (phase 003). This placeholder will connect to the chatflow API when available." }],
          artifacts: []
        };
        return { ...conversation, messages: [...conversation.messages, userMsg, assistantMsg] };
      })
    );
  }

  function handleNewChat() {
    setCurrentConversationId(null);
    setSelectedArtifact(null);
  }

  function handleSelectArtifact(artifact: ChatArtifact, run?: WorkflowRun) {
    setSelectedArtifact(artifact);
    setSelectedArtifactRun(run ?? null);
  }

  const currentConversation =
    conversations.find((conversation) => conversation.id === currentConversationId) ?? null;
  const title = currentConversation ? getConversationTitle(currentConversation) : "New Chat";

  return (
    <AppShell
      active="chat"
      role={session.role}
      conversations={conversations}
      selectedChatId={currentConversationId}
      onLogout={handleLogout}
      onNavigate={handleNewChat}
      onSelectChat={(conversationId) => {
        setCurrentConversationId(conversationId);
        setSelectedArtifact(null);
      }}
    >
      <div className={selectedArtifact ? "contentWithArtifact" : "contentWithArtifact noArtifact"}>
        <div className="primaryPane">
          <header className="topBar">
            <h1>{title}</h1>
            <span className="headerActionSlot" aria-hidden="true" />
          </header>
          <div className="primaryContent chatSurface">
            <ChatPage
              conversation={currentConversation}
              onRunComplete={handleRunComplete}
              onChatSubmit={handleChatSubmit}
              onNewChat={handleNewChat}
              onSelectArtifact={handleSelectArtifact}
            />
          </div>
        </div>
        <ArtifactPanel
          artifact={selectedArtifact}
          run={selectedArtifactRun}
          onClose={() => setSelectedArtifact(null)}
        />
      </div>
    </AppShell>
  );
}

function runToConversation(run: WorkflowRun): ChatConversation {
  const firstSection = run.output.sections[0];
  const title = firstSection?.title ?? run.id;
  const userMessage = createUserMessage(`Workflow: ${title} (${run.id})`, 1);
  const assistantMessage = createWorkflowAssistantMessage(run, 1);
  return {
    id: run.id,
    messages: [userMessage, assistantMessage]
  };
}
