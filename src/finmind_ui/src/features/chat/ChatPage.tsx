import { Send } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import type { ChatArtifact, ChatConversation } from "./mockChat";
import type { WorkflowRun } from "../../api/client";
import { getLatestUserMessageId } from "./mockChat";
import { Markdown } from "../../components/Markdown";

type Props = {
  conversation: ChatConversation | null;
  onSubmit: (message: string) => void;
  onSelectArtifact: (artifact: ChatArtifact, run?: WorkflowRun) => void;
};

const prompts = [
  "What changed for VCB today?",
  "Explain gold price pressure this week.",
  "Compare banking and retail momentum.",
  "What risks should I watch before market close?"
];

export function ChatPage({ conversation, onSubmit, onSelectArtifact }: Props) {
  const [draft, setDraft] = useState("");
  const transcriptRef = useRef<HTMLDivElement | null>(null);
  const messageRefs = useRef<Record<string, HTMLElement | null>>({});
  const latestUserMessageId = conversation ? getLatestUserMessageId(conversation) : null;

  useEffect(() => {
    if (!latestUserMessageId) {
      return;
    }

    const frame = window.requestAnimationFrame(() => {
      const transcript = transcriptRef.current;
      const target = messageRefs.current[latestUserMessageId];
      if (!transcript || !target) {
        return;
      }

      const transcriptTop = transcript.getBoundingClientRect().top;
      const targetTop = target.getBoundingClientRect().top;
      transcript.scrollTop += targetTop - transcriptTop;
    });

    return () => window.cancelAnimationFrame(frame);
  }, [latestUserMessageId, conversation?.messages.length]);

  function submit(message: string) {
    const trimmed = message.trim();
    if (!trimmed) {
      return;
    }
    onSubmit(trimmed);
    setDraft("");
  }

  return (
    <section className="chatPage" aria-label="New chat">
      <div className={conversation ? "chatTranscript hasConversation" : "chatTranscript empty"} ref={transcriptRef}>
        {!conversation ? (
          <div className="chatEmpty">
            <h2>What should we research?</h2>
            <p>
              Ask a finance research question. V1 returns deterministic mock responses with trusted
              local visual artifacts.
            </p>
            <div className="promptGrid">
              {prompts.map((prompt) => (
                <button className="promptCard" key={prompt} onClick={() => submit(prompt)} type="button">
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="messageStack">
            {conversation.messages.map((message) => (
              <article
                className={`chatMessage ${message.role}`}
                key={message.id}
                ref={(element) => {
                  messageRefs.current[message.id] = element;
                }}
              >
                <div className="messageRole">{message.role === "user" ? "You" : "FinMind"}</div>
                {message.blocks.map((block, index) =>
                  block.kind === "text" ? (
                    message.pending ? (
                      <div className="pendingMessage" key={`${message.id}-text-${index}`}>
                        <span className="typingDots"><span></span><span></span><span></span></span>
                        {block.content}
                      </div>
                    ) : message.workflowRun ? (
                      <Markdown content={block.content} key={`${message.id}-text-${index}`} />
                    ) : (
                      <p key={`${message.id}-text-${index}`}>{block.content}</p>
                    )
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
        )}
      </div>
      <form
        className="chatComposer"
        onSubmit={(event) => {
          event.preventDefault();
          submit(draft);
        }}
      >
        <textarea
          aria-label="Message"
          onChange={(event) => setDraft(event.target.value)}
          placeholder="Ask FinMind..."
          value={draft}
        />
        <button className="sendButton" type="submit" aria-label="Send message">
          <Send size={18} />
        </button>
      </form>
    </section>
  );
}
