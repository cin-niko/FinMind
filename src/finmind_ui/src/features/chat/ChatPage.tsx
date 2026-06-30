import { Send, TrendingUp, BarChart3, Database, Plus } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import type { ChatArtifact, ChatConversation } from "./mockChat";
import { getLatestUserMessageId } from "./mockChat";
import { Markdown } from "../../components/Markdown";
import type { Workflow, WorkflowRun } from "../../api/client";
import { listWorkflows, runWorkflow } from "../../api/client";
import { workflowPromptTemplate, workflowShortLabel } from "../workflows/workflowTemplates";
import { ErrorAlert, LoadingState } from "../../components/layout";

type Props = {
  conversation: ChatConversation | null;
  onRunComplete: (run: WorkflowRun, userMessage: string) => void;
  onChatSubmit: (message: string) => void;
  onNewChat: () => void;
  onSelectArtifact: (artifact: ChatArtifact, run?: WorkflowRun) => void;
};

export function ChatPage({ conversation, onRunComplete, onChatSubmit, onNewChat, onSelectArtifact }: Props) {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [loadingWorkflows, setLoadingWorkflows] = useState(true);
  const [selectedWorkflow, setSelectedWorkflow] = useState<Workflow | null>(null);
  const [symbol, setSymbol] = useState("");
  const [draft, setDraft] = useState("");
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");
  const transcriptRef = useRef<HTMLDivElement | null>(null);
  const messageRefs = useRef<Record<string, HTMLElement | null>>({});
  const latestUserMessageId = conversation ? getLatestUserMessageId(conversation) : null;

  useEffect(() => {
    listWorkflows()
      .then(setWorkflows)
      .catch(() => setWorkflows([]))
      .finally(() => setLoadingWorkflows(false));
  }, []);

  useEffect(() => {
    if (!latestUserMessageId) return;
    const frame = window.requestAnimationFrame(() => {
      const transcript = transcriptRef.current;
      const target = messageRefs.current[latestUserMessageId];
      if (!transcript || !target) return;
      const transcriptTop = transcript.getBoundingClientRect().top;
      const targetTop = target.getBoundingClientRect().top;
      transcript.scrollTop += targetTop - transcriptTop;
    });
    return () => window.cancelAnimationFrame(frame);
  }, [latestUserMessageId, conversation?.messages.length]);

  async function handleRun() {
    if (!selectedWorkflow) return;
    const symbolValue = symbol.trim().toUpperCase();
    const symbolInput = selectedWorkflow.required_inputs.find((input) => input.name === "symbol");
    if (symbolInput?.required && !symbolValue) return;
    const market = selectedWorkflow.market_scope[0] ?? "VN_STOCK";
    setRunning(true);
    setError("");
    try {
      const run = await runWorkflow(selectedWorkflow.id, {
        market,
        ...(symbolInput && symbolValue ? { symbol: symbolValue } : {})
      });
      const userMessage = workflowPromptTemplate(selectedWorkflow.id)(symbolValue || market);
      onRunComplete(run, userMessage);
      setSelectedWorkflow(null);
      setSymbol("");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Workflow failed");
    } finally {
      setRunning(false);
    }
  }

  function submitChat(message: string) {
    const trimmed = message.trim();
    if (!trimmed) return;
    onChatSubmit(trimmed);
    setDraft("");
  }

  /* --- Conversation view: transcript + chat composer --- */
  if (conversation) {
    return (
      <section className="chatPage" aria-label="Chat">
        <div className="chatTranscript hasConversation" ref={transcriptRef}>
          <div className="messageStack">
            {conversation.messages.map((message) => (
              <article
                className={`chatMessage ${message.role}`}
                key={message.id}
                ref={(element) => { messageRefs.current[message.id] = element; }}
              >
                <div className="messageRole">{message.role === "user" ? "You" : "FinMind"}</div>
                {message.role === "assistant" && message.workflowRun ? (
                  <WorkflowReport message={message} onSelectArtifact={onSelectArtifact} />
                ) : (
                  message.blocks.map((block, index) =>
                    block.kind === "text" ? (
                      <Markdown content={block.content} key={`${message.id}-text-${index}`} />
                    ) : (
                      <div className="inlineVisual" key={`${message.id}-visual-${index}`}>
                        <h3>{block.title}</h3>
                        <div className="metricGrid">
                          {block.metrics.map((metric) => (
                            <div className={`metricCard ${metric.tone}`} key={metric.label}>
                              <span>{metric.label}</span>
                              <strong>{metric.value}</strong>
                            </div>
                          ))}
                        </div>
                      </div>
                    )
                  )
                )}
                {message.artifacts.length ? (
                  <div className="artifactCards">
                    {message.artifacts.map((artifact) => (
                      <button
                        className="artifactCard"
                        key={artifact.id}
                        onClick={() => onSelectArtifact(artifact, message.workflowRun)}
                        type="button"
                      >
                        <span>{artifact.kind}</span>
                        <strong>{artifact.title}</strong>
                        <small>{artifact.summary}</small>
                      </button>
                    ))}
                  </div>
                ) : null}
              </article>
            ))}
          </div>
        </div>
        <form
          className="chatComposer"
          onSubmit={(event) => { event.preventDefault(); submitChat(draft); }}
        >
          <button className="composerNewChat" onClick={onNewChat} type="button" aria-label="New chat">
            <Plus size={18} />
          </button>
          <textarea
            aria-label="Message"
            onChange={(event) => setDraft(event.target.value)}
            placeholder="Ask a follow-up question..."
            value={draft}
          />
          <button className="sendButton" type="submit" aria-label="Send message">
            <Send size={18} />
          </button>
        </form>
      </section>
    );
  }

  /* --- Empty view: workflow selection --- */
  return (
    <section className="chatPage" aria-label="New chat">
      <div className="chatTranscript empty">
        <div className="chatEmpty">
          <h2>What should we analyze?</h2>
          <p>Pick an analysis type and enter a ticker to run a workflow.</p>
          {loadingWorkflows ? (
            <LoadingState />
          ) : (
            <div className="promptGrid">
              {workflows.map((workflow) => (
                <WorkflowCard
                  key={workflow.id}
                  workflow={workflow}
                  selected={selectedWorkflow?.id === workflow.id}
                  onSelect={() => { setSelectedWorkflow(workflow); setError(""); }}
                />
              ))}
            </div>
          )}
          {error ? <ErrorAlert message={error} /> : null}
          {selectedWorkflow ? (
            <SymbolInputBar
              label={workflowShortLabel(selectedWorkflow)}
              symbol={symbol}
              setSymbol={setSymbol}
              running={running}
              onRun={handleRun}
            />
          ) : null}
        </div>
      </div>
    </section>
  );
}

function WorkflowCard({ workflow, selected, onSelect }: { workflow: Workflow; selected: boolean; onSelect: () => void; }) {
  const Icon = workflow.id.includes("technical") ? TrendingUp : workflow.id.includes("fundamental") ? BarChart3 : Database;
  return (
    <button className={selected ? "promptCard selected" : "promptCard"} onClick={onSelect} type="button">
      <Icon size={20} />
      <strong>{workflowShortLabel(workflow)}</strong>
      <small>{workflow.description}</small>
    </button>
  );
}

function SymbolInputBar({ label, symbol, setSymbol, running, onRun }: { label: string; symbol: string; setSymbol: (v: string) => void; running: boolean; onRun: () => void; }) {
  return (
    <div className="symbolBar">
      <label>
        {label} — Symbol
        <input
          autoCapitalize="characters"
          value={symbol}
          onChange={(event) => setSymbol(event.target.value)}
          placeholder="e.g. TPB, VCB, HPG"
          onKeyDown={(event) => { if (event.key === "Enter") { event.preventDefault(); onRun(); } }}
        />
      </label>
      <button className="primaryButton" disabled={running || !symbol.trim()} onClick={onRun} type="button">
        <Send size={16} /> {running ? "Running..." : "Run"}
      </button>
    </div>
  );
}

function WorkflowReport({ message, onSelectArtifact }: { message: import("./mockChat").ChatMessage; onSelectArtifact: (artifact: ChatArtifact, run?: WorkflowRun) => void; }) {
  const run = message.workflowRun!;
  return (
    <div className="workflowReport">
      <div className="reportHeader">
        <span className="badge">{run.status}</span>
        <span className="meta">Grounding: {run.output.grounding.grounding_status}</span>
      </div>
      {run.output.sections.map((section) => (
        <div className="reportSection" key={section.title}>
          <h3>{section.title}</h3>
          <Markdown content={section.content} />
          {section.warnings.length ? (
            <div className="freshness">⚠ {section.warnings.join(", ")}</div>
          ) : null}
        </div>
      ))}
    </div>
  );
}
