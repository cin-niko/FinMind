import { useCallback, useEffect, useState } from "react";
import {
  deleteRun,
  getSession,
  isUnauthorizedError,
  listRuns,
  logout,
  renameRun,
  runWorkflow,
  type Artifact,
  type SessionState,
  type WorkflowRun,
  type WorkflowStreamEvent
} from "./api/client";
import { LoadingState } from "./components/layout";
import { LoginPage } from "./features/auth/LoginPage";
import { ArtifactPanel } from "./features/chat/ArtifactPanel";
import { ChatPage } from "./features/chat/ChatPage";
import {
  createMockResponse,
  createNewConversation,
  createPendingAssistantMessage,
  inputContextForInputs,
  titleForStep,
  workflowStreamStateFromRun,
  createWorkflowAssistantMessage,
  createUserMessage,
  getConversationTitle,
  type ChatArtifact,
  type ChatConversation,
  type LiveCitation,
  type LiveEvidence
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
  const [selectedCitationId, setSelectedCitationId] = useState<string | null>(null);
  const [citationFlashKey, setCitationFlashKey] = useState(0);
  const [selectedLive, setSelectedLive] = useState<LiveEvidence | null>(null);
  const [rightPanelCollapsed, setRightPanelCollapsed] = useState(false);

  useEffect(() => {
    getSession().then(setSession).catch(() => setSession({ authenticated: false }));
  }, []);

  const handleSessionExpired = useCallback(() => {
    setSession({ authenticated: false });
    setSelectedArtifact(null);
    setSelectedCitationId(null);
    setSelectedLive(null);
    setRightPanelCollapsed(false);
    setView("chat");
  }, []);

  useEffect(() => {
    if (!session?.authenticated) return;
    listRuns()
      .then((runs) => {
        setConversations((items) => {
          const hydrated = runs.map(runToConversation).reverse();
          const hydratedIds = new Set(hydrated.map((conversation) => conversation.id));
          const pending = items.filter((conversation) =>
            conversation.messages.some((message) => message.pending) &&
            !hydratedIds.has(conversation.id)
          );
          return [...pending, ...hydrated];
        });
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
    setSelectedCitationId(null);
    setSelectedLive(null);
    setRightPanelCollapsed(false);
    setView("chat");
  }

  async function handleRunStart(workflowId: string, symbol: string, market: string) {
    const userMessage = workflowPromptTemplate(workflowId)(symbol || market);
    const conversation = createNewConversation(userMessage);
    const conversationId = conversation.id;
    const streamInputs = {
      market,
      ...(symbol ? { symbol } : {})
    };
    const pendingMessage = createPendingAssistantMessage(1);
    const nextConversation = { ...conversation, isWorkflowRun: true, messages: [...conversation.messages, pendingMessage] };
    setConversations((items) => [nextConversation, ...items]);
    setCurrentConversationId(conversationId);
    setSelectedArtifact(null);
    setView("chat");
    try {
      const run = await runWorkflow(workflowId, streamInputs, (event: WorkflowStreamEvent) => {
        if (
          event.kind !== "answer.delta" &&
          event.kind !== "run.stage" &&
          event.kind !== "run.completed" &&
          event.kind !== "citation" &&
          event.kind !== "artifact"
        ) {
          return;
        }
        setConversations((items) =>
          items.map((conv) => {
            if (conv.id !== conversationId) return conv;
            return {
              ...conv,
              messages: conv.messages.map((message) => {
                if (!message.pending) return message;
                const currentState = message.streamState ?? {
                  label: "Working",
                  complete: false,
                  steps: [],
                  answer: "",
                  citations: [],
                  artifacts: []
                };
                let nextState;
                if (event.kind === "answer.delta") {
                  nextState = {
                    ...currentState,
                    answer: `${currentState.answer}${String(event.payload.text ?? "")}`
                  };
                } else if (event.kind === "run.completed") {
                  nextState = workflowStreamStateFromRun(event.payload.run as WorkflowRun);
                } else if (event.kind === "citation") {
                  const citation = event.payload as unknown as LiveCitation;
                  const exists = currentState.citations.some(
                    (item) => item.citation_id === citation.citation_id
                  );
                  nextState = {
                    ...currentState,
                    citations: exists ? currentState.citations : [...currentState.citations, citation]
                  };
                } else if (event.kind === "artifact") {
                  const artifact = event.payload as unknown as Artifact;
                  const exists = currentState.artifacts.some(
                    (item) => item.artifact_id === artifact.artifact_id
                  );
                  nextState = {
                    ...currentState,
                    artifacts: exists ? currentState.artifacts : [...currentState.artifacts, artifact]
                  };
                } else {
                  nextState = updateStreamState(currentState, event, streamInputs);
                }
                const nextText = nextState.answer;
                return {
                  ...message,
                  content: nextText,
                  blocks: [{ kind: "text", content: nextText }],
                  streamState: nextState
                };
              })
            };
          })
        );
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
    setSelectedLive(null);
    setRightPanelCollapsed(false);
    if (nextView === "chat") {
      if (view === "chat" && currentConversationId === null) {
        return;
      }
      setCurrentConversationId(null);
    }
    setView(nextView);
  }

  function handleChatSubmit(message: string) {
    setSelectedArtifact(null);
    setSelectedLive(null);
    setRightPanelCollapsed(false);
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

  async function handleRenameConversation(conversationId: string, title: string) {
    const conversation = conversations.find((item) => item.id === conversationId);
    if (!conversation) return;
    const trimmed = title.trim();
    if (!trimmed) return;
    if (conversation.isWorkflowRun) {
      try {
        const updated = await renameRun(conversationId, trimmed);
        setConversations((items) =>
          items.map((item) =>
            item.id === conversationId ? { ...item, title: updated.title ?? trimmed } : item
          )
        );
      } catch (caught) {
        if (isUnauthorizedError(caught)) handleSessionExpired();
      }
    } else {
      setConversations((items) =>
        items.map((item) =>
          item.id === conversationId ? { ...item, title: trimmed } : item
        )
      );
    }
  }

  async function handleDeleteConversation(conversationId: string) {
    const conversation = conversations.find((item) => item.id === conversationId);
    if (!conversation) return;
    if (conversation.isWorkflowRun) {
      try {
        await deleteRun(conversationId);
      } catch (caught) {
        if (isUnauthorizedError(caught)) {
          handleSessionExpired();
          return;
        }
      }
    }
    setConversations((items) => items.filter((item) => item.id !== conversationId));
    if (currentConversationId === conversationId) {
      setCurrentConversationId(null);
      setSelectedArtifact(null);
      setSelectedCitationId(null);
      setSelectedLive(null);
      setRightPanelCollapsed(false);
    }
  }

  function handleSelectArtifact(artifact: ChatArtifact, run?: WorkflowRun, live?: LiveEvidence) {
    setSelectedArtifact(artifact);
    setSelectedArtifactRun(run ?? null);
    setSelectedLive(live ?? null);
    setSelectedCitationId(null);
    setRightPanelCollapsed(false);
  }

  function handleSelectCitation(citationId: string, run?: WorkflowRun, live?: LiveEvidence) {
    setSelectedArtifact(null);
    setSelectedArtifactRun(run ?? null);
    setSelectedLive(live ?? null);
    setSelectedCitationId(citationId);
    setCitationFlashKey((current) => current + 1);
    setRightPanelCollapsed(false);
  }

  const currentConversation =
    conversations.find((conversation) => conversation.id === currentConversationId) ?? null;

  const titleByView: Record<View, string> = {
    chat: getChatHeaderTitle(currentConversation),
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
      onRenameConversation={handleRenameConversation}
      onDeleteConversation={handleDeleteConversation}
      onSelectChat={(conversationId) => {
        setCurrentConversationId(conversationId);
        setSelectedArtifact(null);
        setSelectedCitationId(null);
        setSelectedLive(null);
        setRightPanelCollapsed(false);
        setView("chat");
      }}
    >
      <div
        className={
          selectedArtifact || selectedCitationId
            ? rightPanelCollapsed
              ? "contentWithArtifact rightCollapsed"
              : "contentWithArtifact"
            : "contentWithArtifact noArtifact"
        }
      >
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
                onSelectCitation={handleSelectCitation}
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
          selectedCitationId={selectedCitationId}
          citationFlashKey={citationFlashKey}
          run={selectedArtifactRun}
          citations={selectedLive?.citations}
          citationOrdinals={selectedLive?.citationOrdinals}
          artifacts={selectedLive?.artifacts}
          collapsed={rightPanelCollapsed}
          onToggleCollapse={() => setRightPanelCollapsed((current) => !current)}
        />
      </div>
    </AppShell>
  );
}

function updateStreamState(
  currentState: NonNullable<ChatConversation["messages"][number]["streamState"]>,
  event: WorkflowStreamEvent,
  inputs?: Record<string, string>
): NonNullable<ChatConversation["messages"][number]["streamState"]> {
  const stageId = String(event.payload.stage ?? "");
  const inputContext = inputContextForInputs(inputs);
  const nextStep = {
    id: stageId,
    title: titleForStep(stageId, inputs),
    kind: String(event.payload.kind ?? "skill") === "collect_data" ? "collect_data" as const : "skill" as const,
    status: String(event.payload.status ?? "running"),
    warnings: Array.isArray(event.payload.warnings)
      ? event.payload.warnings.map((warning) => String(warning))
      : [],
    inputContext
  };
  const steps = currentState.steps.some((step) => step.id === stageId)
    ? currentState.steps.map((step) => (step.id === stageId ? nextStep : step))
    : [...currentState.steps, nextStep];
  const completedSteps = steps.filter((step) => step.status !== "running").length;
  return {
    ...currentState,
    label: completedSteps > 0 && completedSteps === steps.length ? `Completed ${completedSteps} steps` : "Working",
    complete: completedSteps > 0 && completedSteps === steps.length,
    steps
  };
}

export function getChatHeaderTitle(conversation: ChatConversation | null): string {
  return conversation ? getConversationTitle(conversation) : "Chat";
}

function runToConversation(run: WorkflowRun): ChatConversation {
  const workflowId = inferWorkflowId(run);
  const symbol = (run.inputs?.symbol ?? "").toUpperCase();
  const userMessage = workflowPromptTemplate(workflowId)(symbol || (run.inputs?.market ?? ""));
  const assistantMessage = createWorkflowAssistantMessage(run, 1);
  return {
    id: run.id,
    title: run.title ?? undefined,
    isWorkflowRun: true,
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
