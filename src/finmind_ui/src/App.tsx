import { useCallback, useEffect, useState } from "react";
import {
  getSession,
  isUnauthorizedError,
  listRuns,
  logout,
  runWorkflow,
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
  createPendingAssistantMessage,
  createWorkflowAssistantMessage,
  createUserMessage,
  getConversationTitle,
  type ChatArtifact,
  type ChatConversation
} from "./features/chat/mockChat";
import { AppShell } from "./features/shell/AppShell";
import { WorkflowPage } from "./features/workflows/WorkflowPage";
import { workflowPromptTemplate } from "./features/workflows/workflowTemplates";

type View = "chat" | "workflows";

export function App() {
  const [session, setSession] = useState<SessionState | null>(null);
  const [view, setView] = useState<View>("chat");
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
    setView("chat");
  }, []);

  useEffect(() => {
    if (!session?.authenticated) return;
    listRuns()
      .then((runs) => {
        setConversations(runs.map(runToConversation).reverse());
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
    setView("chat");
  }

  async function handleRunStart(workflowId: string, symbol: string, market: string) {
    const userMessage = workflowPromptTemplate(workflowId)(symbol || market);
    const conversation = createNewConversation(userMessage);
    const conversationId = conversation.id;
    const pendingMessage = createPendingAssistantMessage(1);
    const nextConversation = { ...conversation, messages: [...conversation.messages, pendingMessage] };
    setConversations((items) => [nextConversation, ...items]);
    setCurrentConversationId(conversationId);
    setSelectedArtifact(null);
    setView("chat");
    try {
      const run = await runWorkflow(workflowId, {
        market,
        ...(symbol ? { symbol } : {})
      });
      setConversations((items) =>
        items.map((conv) => {
          if (conv.id !== conversationId) return conv;
          const assistantMessage = createWorkflowAssistantMessage(run, 1);
          return { ...conv, id: run.id, messages: [...conv.messages.filter((m) => !m.pending), assistantMessage] };
        })
      );
      setCurrentConversationId(run.id);
    } catch (caught) {
      if (isUnauthorizedError(caught)) {
        handleSessionExpired();
        return;
      }
      setConversations((items) =>
        items.map((conv) => {
          if (conv.id !== conversationId) return conv;
          const msg = caught instanceof Error ? caught.message : "Workflow failed";
          const errorMsg = {
            id: `assistant-err-1`,
            role: "assistant" as const,
            content: msg,
            blocks: [{ kind: "text" as const, content: msg }],
            artifacts: []
          };
          return { ...conv, messages: [...conv.messages.filter((m) => !m.pending), errorMsg] };
        })
      );
    }
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
      const nextConversation = { ...conversation, messages: [...conversation.messages, response] };
      setConversations((items) => [nextConversation, ...items]);
      setCurrentConversationId(nextConversation.id);
      return;
    }
    setConversations((items) =>
      items.map((conversation) => {
        if (conversation.id !== currentConversationId) return conversation;
        const nextIndex = conversation.messages.filter((item) => item.role === "user").length + 1;
        return {
          ...conversation,
          messages: [...conversation.messages, createUserMessage(message, nextIndex), createMockResponse(message)]
        };
      })
    );
  }

  function handleSelectArtifact(artifact: ChatArtifact, run?: WorkflowRun) {
    setSelectedArtifact(artifact);
    setSelectedArtifactRun(run ?? null);
  }

  const currentConversation =
    conversations.find((conversation) => conversation.id === currentConversationId) ?? null;

  const titleByView: Record<View, string> = {
    chat: currentConversation ? getConversationTitle(currentConversation) : "New Chat",
    workflows: "Workflows"
  };

  return (
    <AppShell
      active={view}
      role={session.role}
      conversations={conversations}
      selectedChatId={view === "chat" ? currentConversationId : null}
      onLogout={handleLogout}
      onNavigate={handleNavigate}
      onSelectChat={(conversationId) => {
        setCurrentConversationId(conversationId);
        setSelectedArtifact(null);
        setView("chat");
      }}
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
                onSelectArtifact={handleSelectArtifact}
                onSubmit={handleChatSubmit}
              />
            ) : null}
            {view === "workflows" ? (
              <WorkflowPage
                onRunStart={handleRunStart}
                onSessionExpired={handleSessionExpired}
              />
            ) : null}
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
  const workflowId = inferWorkflowId(run);
  const symbol = (run.inputs?.symbol ?? "").toUpperCase();
  const userMessage = workflowPromptTemplate(workflowId)(symbol || (run.inputs?.market ?? ""));
  const assistantMessage = createWorkflowAssistantMessage(run, 1);
  return {
    id: run.id,
    messages: [createUserMessage(userMessage, 1), assistantMessage]
  };
}

function inferWorkflowId(run: WorkflowRun): string {
  const skillSteps = run.output.steps.filter((s) => s.kind === "skill");
  if (skillSteps.some((s) => s.id.includes("fundamental-analysis"))) return "vn-fundamental-analysis";
  if (skillSteps.some((s) => s.id.includes("technical-analysis"))) return "vn-technical-analysis";
  if (skillSteps.some((s) => s.id.includes("data-auditor"))) return "vn-financial-data-collector";
  return "vn-financial-data-collector";
}
