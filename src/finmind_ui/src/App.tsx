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

type View = "chat" | "workflows" | "results";

export function App() {
  const [session, setSession] = useState<SessionState | null>(null);
  const [view, setView] = useState<View>("chat");
  const [conversations, setConversations] = useState<ChatConversation[]>([]);
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);
  const [workflowRuns, setWorkflowRuns] = useState<WorkflowRun[]>([]);
  const [selectedArtifact, setSelectedArtifact] = useState<ChatArtifact | null>(null);
  const [selectedArtifactRun, setSelectedArtifactRun] = useState<WorkflowRun | null>(null);

  useEffect(() => {
    getSession().then(setSession).catch(() => setSession({ authenticated: false }));
  }, []);

  const handleSessionExpired = useCallback(() => {
    setSession({ authenticated: false });
    setWorkflowRuns([]);
    setSelectedArtifact(null);
    setView("chat");
  }, []);

  useEffect(() => {
    if (!session?.authenticated) return;
    listRuns()
      .then(setWorkflowRuns)
      .catch((caught) => {
        if (isUnauthorizedError(caught)) handleSessionExpired();
      });
  }, [handleSessionExpired, session]);

  if (!session) return <LoadingState />;
  if (!session.authenticated) return <LoginPage onAuthenticated={setSession} />;

  async function handleLogout() {
    const next = await logout().catch(() => ({ authenticated: false }) as const);
    setSession(next);
    setWorkflowRuns([]);
    setSelectedArtifact(null);
    setView("chat");
  }

  function runToConversation(run: WorkflowRun, workflowId: string, symbol: string): ChatConversation {
    const userMessage = workflowPromptTemplate(workflowId)(symbol || (run.inputs?.market ?? ""));
    const conversation = createNewConversation(userMessage);
    const assistantMessage = createWorkflowAssistantMessage(run, 1);
    return { ...conversation, messages: [...conversation.messages, assistantMessage] };
  }

  async function handleRunStart(workflowId: string, symbol: string, market: string) {
    const userMessage = workflowPromptTemplate(workflowId)(symbol || market);
    const conversation = createNewConversation(userMessage);
    const pendingMessage = createPendingAssistantMessage(1);
    const conversationId = conversation.id;
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
      setWorkflowRuns((runs) => [run, ...runs.filter((existing) => existing.id !== run.id)]);
      setConversations((items) =>
        items.map((conv) => {
          if (conv.id !== conversationId) return conv;
          const assistantMessage = createWorkflowAssistantMessage(run, 1);
          return { ...conv, messages: [...conv.messages.filter((m) => !m.pending), assistantMessage] };
        })
      );
    } catch (caught) {
      if (isUnauthorizedError(caught)) {
        handleSessionExpired();
        return;
      }
      setConversations((items) =>
        items.map((conv) => {
          if (conv.id !== conversationId) return conv;
          const errorMsg = {
            id: `assistant-err-${1}`,
            role: "assistant" as const,
            content: caught instanceof Error ? caught.message : "Workflow failed",
            blocks: [{ kind: "text" as const, content: caught instanceof Error ? caught.message : "Workflow failed" }],
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

  function handleSelectRun(run: WorkflowRun) {
    const workflowId = inferWorkflowId(run);
    const symbol = (run.inputs?.symbol ?? "").toUpperCase();
    const existing = conversations.find((c) => c.id === run.id);
    if (existing) {
      setCurrentConversationId(existing.id);
    } else {
      const conversation = runToConversation(run, workflowId, symbol);
      setConversations((items) => [conversation, ...items]);
      setCurrentConversationId(conversation.id);
    }
    setSelectedArtifact(null);
    setView("chat");
  }

  const currentConversation =
    conversations.find((conversation) => conversation.id === currentConversationId) ?? null;

  const titleByView: Record<View, string> = {
    chat: currentConversation ? getConversationTitle(currentConversation) : "New Chat",
    workflows: "Workflows",
    results: "Workflow Result"
  };

  return (
    <AppShell
      active={view}
      chatHistory={conversations}
      selectedChatId={view === "chat" ? currentConversationId : null}
      selectedRunId={null}
      workflowRuns={workflowRuns}
      onLogout={handleLogout}
      onNavigate={handleNavigate}
      onSelectChat={(conversationId) => {
        setCurrentConversationId(conversationId);
        setSelectedArtifact(null);
        setView("chat");
      }}
      onSelectRun={handleSelectRun}
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

function inferWorkflowId(run: WorkflowRun): string {
  const skillSteps = run.output.steps.filter((s) => s.kind === "skill");
  if (skillSteps.some((s) => s.id.includes("fundamental-analysis"))) return "vn-fundamental-analysis";
  if (skillSteps.some((s) => s.id.includes("technical-analysis"))) return "vn-technical-analysis";
  if (skillSteps.some((s) => s.id.includes("data-auditor"))) return "vn-financial-data-collector";
  return "vn-financial-data-collector";
}
