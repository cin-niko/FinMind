import {
  CheckCircle2,
  ChevronRight,
  Database,
  Download,
  FilePenLine,
  FileText,
  LineChart,
  SearchCheck,
  Send,
  ShieldCheck
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import type { ChatArtifact, ChatConversation, LiveEvidence } from "./mockChat";
import type { Artifact, WorkflowRun } from "../../api/client";
import { getLatestUserMessageId, mapArtifactsToCards, orderCitationsByAppearance } from "./mockChat";
import { Markdown } from "../../components/Markdown";
import { useI18n } from "../settings/i18n";
import { workflowStepTitle } from "../settings/i18n";

type Props = {
  conversation: ChatConversation | null;
  onSubmit: (message: string) => void;
  onSelectArtifact: (artifact: ChatArtifact, run?: WorkflowRun, live?: LiveEvidence) => void;
  onSelectCitation: (citationId: string, run?: WorkflowRun, live?: LiveEvidence) => void;
};

function messageSource(message: ChatConversation["messages"][number]): string {
  if (message.workflowRun) {
    return message.workflowRun.output.sections
      .map((section) => section.content)
      .join("\n\n---\n\n");
  }
  return message.streamState?.answer ?? "";
}

export function evidenceFor(message: ChatConversation["messages"][number]): LiveEvidence {
  const source = messageSource(message);
  const rawCitations = message.workflowRun
    ? message.workflowRun.output.citations
    : (message.streamState?.citations ?? []);
  const artifacts = message.workflowRun
    ? message.workflowRun.output.artifacts
    : (message.streamState?.artifacts ?? []);
  const { citations, ordinals } = orderCitationsByAppearance(source, rawCitations);
  return { citations, citationOrdinals: ordinals, artifacts };
}

function visibleArtifacts(
  message: ChatConversation["messages"][number],
  language: "en" | "vi"
): ChatArtifact[] {
  if (message.pending && message.streamState && !message.workflowRun) {
    return mapArtifactsToCards(message.streamState.artifacts, message.id, language);
  }
  return message.artifacts;
}

export function ChatPage({ conversation, onSubmit, onSelectArtifact, onSelectCitation }: Props) {
  const { language, t } = useI18n();
  const prompts = [
    t("promptVcbChange"),
    t("promptGoldPressure"),
    t("promptSectorMomentum"),
    t("promptClosingRisks")
  ];
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
    <section className="chatPage" aria-label={t("newChat")}>
      <div className={conversation ? "chatTranscript hasConversation" : "chatTranscript empty"} ref={transcriptRef}>
        {!conversation ? (
          <div className="chatEmpty">
            <h2>{t("researchPrompt")}</h2>
            <p>
              {t("researchIntro")}
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
                className={`chatMessage ${message.role}${message.role === "assistant" && (message.workflowRun || message.streamState) ? " workflowMessage" : ""}`}
                key={message.id}
                ref={(element) => {
                  messageRefs.current[message.id] = element;
                }}
              >
                {message.streamState ? (
                  <details className="workflowProgress" open={!message.streamState.complete}>
                    <summary>
                      <span className="workflowProgressSummary">
                        <span>
                          {message.streamState.complete
                            ? t("completedSteps", { count: message.streamState.steps.length })
                            : t("working")}
                        </span>
                        <ChevronRight className="workflowProgressChevron" size={14} aria-hidden="true" />
                      </span>
                    </summary>
                    <ul className="workflowProgressList">
                      {message.streamState.steps.map((step) => (
                        <li className={`workflowProgressItem ${step.status}`} key={step.id}>
                          <span className="workflowProgressRail" aria-hidden="true">
                            <span className="workflowProgressLine"></span>
                            <span className="workflowProgressMarker">{iconForStep(step.id, step.kind, step.status)}</span>
                          </span>
                          <span className="workflowProgressCopy">
                            <span>{workflowStepTitle(language, step.id, step.market)}</span>
                            {step.inputContext ? <small>{step.inputContext}</small> : null}
                          </span>
                        </li>
                      ))}
                      {message.streamState.complete ? (
                        <li className="workflowProgressItem done">
                          <span className="workflowProgressRail" aria-hidden="true">
                            <span className="workflowProgressLine"></span>
                            <span className="workflowProgressMarker"><CheckCircle2 size={14} /></span>
                          </span>
                          <span className="workflowProgressCopy">
                            <span>{t("done")}</span>
                          </span>
                        </li>
                      ) : null}
                    </ul>
                  </details>
                ) : null}
                {message.blocks.map((block, index) =>
                  block.kind === "text" ? (
                    message.pending ? (
                      <div className="pendingMessage" key={`${message.id}-text-${index}`}>
                        <span className="typingDots"><span></span><span></span><span></span></span>
                        {message.streamState?.answer ? (
                          <Markdown
                            content={message.streamState.answer}
                            citations={message.streamState?.citations ?? message.workflowRun?.output.citations ?? []}
                            onCitationClick={(citationId) =>
                              onSelectCitation(
                                citationId,
                                message.workflowRun,
                                evidenceFor(message)
                              )
                            }
                          />
                        ) : (
                          t("waiting")
                        )}
                      </div>
                    ) : message.workflowRun ? (
                      <Markdown
                        content={block.content}
                        citations={message.workflowRun.output.citations}
                        key={`${message.id}-text-${index}`}
                        onCitationClick={(citationId) =>
                          onSelectCitation(citationId, message.workflowRun, evidenceFor(message))
                        }
                      />
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
                {visibleArtifacts(message, language).length ? (
                  <div className="artifactCards">
                    {visibleArtifacts(message, language).map((artifact) => (
                      <div className="artifactCard" key={artifact.id}>
                        <button
                          className="artifactOpenButton"
                          onClick={() =>
                            onSelectArtifact(artifact, message.workflowRun, evidenceFor(message))
                          }
                          type="button"
                        >
                          <span className="artifactIcon" aria-hidden="true">
                            {artifact.kind === "chart" ? <LineChart size={22} /> : <FileText size={22} />}
                          </span>
                          <span className="artifactCopy">
                            <strong>{artifact.title}</strong>
                            <small>{artifact.typeLabel ?? artifact.summary}</small>
                          </span>
                        </button>
                        {artifact.download ? (
                          <a
                            className="artifactDownloadButton"
                            href={artifact.download.url}
                            onClick={(event) => event.stopPropagation()}
                            title={`${t("download")} ${artifact.download.filename}`}
                          >
                            <Download size={16} />
                            <span>{t("download")}</span>
                          </a>
                        ) : null}
                      </div>
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
          aria-label={t("message")}
          onChange={(event) => setDraft(event.target.value)}
          placeholder={t("askPlaceholder")}
          value={draft}
        />
        <button className="sendButton" type="submit" aria-label={t("send")}>
          <Send size={18} />
        </button>
      </form>
    </section>
  );
}

function iconForStep(stepId: string, kind: "collect_data" | "skill", status: string) {
  const size = 14;
  if (status === "failed") {
    return <ShieldCheck size={size} />;
  }
  if (kind === "collect_data") {
    return <Database size={size} />;
  }
  if (stepId.includes("data-auditor")) {
    return <SearchCheck size={size} />;
  }
  if (stepId.includes("technical-analysis")) {
    return <LineChart size={size} />;
  }
  if (stepId.includes("fundamental-analysis")) {
    return <ShieldCheck size={size} />;
  }
  return <FilePenLine size={size} />;
}
