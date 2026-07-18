import type { Artifact, ArtifactDownload, WorkflowRun } from "../../api/client";
import { isUiLanguage, translate, workflowStepTitle, type UiLanguage } from "../settings/catalog.ts";

export type ChatArtifactKind = "report" | "chart" | "file" | "table";

export type ChatArtifact = {
  id: string;
  artifactId?: string;
  kind: ChatArtifactKind;
  title: string;
  summary: string;
  typeLabel?: string;
  download?: ArtifactDownload;
};

export type LiveCitation = {
  citation_id: string;
  record_id: string;
  record_type: string;
  source_id: string;
  dataset_id: string;
  label: string;
  timestamp: string;
  instrument_id?: string | null;
  display_content?: string | null;
  payload_snapshot: Record<string, unknown>;
  methodology_version?: string | null;
};

export type LiveEvidence = {
  citations: LiveCitation[];
  citationOrdinals: Map<string, number>;
  artifacts: Artifact[];
};

const CITATION_TOKEN_RE = /\[cite:([A-Za-z0-9_.:-]+)\]|\[(citation_[A-Za-z0-9_.:-]+)\]/g;

export function orderCitationsByAppearance(
  source: string,
  citations: LiveCitation[]
): { citations: LiveCitation[]; ordinals: Map<string, number> } {
  const byId = new Map(citations.map((citation) => [citation.citation_id, citation]));
  const ordered: LiveCitation[] = [];
  const ordinals = new Map<string, number>();
  const seen = new Set<string>();
  CITATION_TOKEN_RE.lastIndex = 0;
  let match: RegExpExecArray | null;
  while ((match = CITATION_TOKEN_RE.exec(source)) !== null) {
    const id = match[1] ?? match[2];
    if (!id || seen.has(id) || !byId.has(id)) continue;
    seen.add(id);
    ordinals.set(id, ordered.length + 1);
    ordered.push(byId.get(id) as LiveCitation);
  }
  for (const citation of citations) {
    if (!seen.has(citation.citation_id)) ordered.push(citation);
  }
  return { citations: ordered, ordinals };
}

export function mapArtifactsToCards(
  artifacts: Artifact[],
  runId: string,
  language: UiLanguage = "en"
): ChatArtifact[] {
  return artifacts.map((artifact) => ({
    id: `${runId}-${artifact.artifact_id}`,
    artifactId: artifact.artifact_id,
    kind: artifact.artifact_type,
    title: artifactDisplayTitle(artifact, language),
    typeLabel: artifactTypeLabel(artifact, language),
    download: artifact.downloads[0] ?? (artifact.artifact_type === "file" ? {
      url: artifact.file.url,
      filename: artifact.file.filename,
      mime_type: artifact.file.mime_type
    } : undefined),
    summary:
      artifact.artifact_type === "chart"
        ? translate(language, "chartArtifact")
        : `${artifact.file_type.toUpperCase()} ${translate(language, "file")}`
  }));
}

function artifactDisplayTitle(artifact: Artifact, language: UiLanguage): string {
  if (artifact.artifact_type !== "chart") {
    return artifact.title;
  }
  const recordKey = typeof artifact.inputs.record_key === "string" ? artifact.inputs.record_key : "";
  const symbol = recordKey.split(/[-_:]/)[0]?.trim().toUpperCase();
  return symbol ? `${symbol} ${translate(language, "chart")}` : artifact.title;
}

function artifactTypeLabel(artifact: Artifact, language: UiLanguage): string {
  if (artifact.artifact_type === "chart") {
    return translate(language, "chart");
  }
  const fileType = artifact.file_type.toUpperCase();
  if (fileType === "XLSX" || fileType === "CSV") {
    return `${translate(language, "spreadsheet")} · ${fileType}`;
  }
  if (fileType === "PDF") {
    return "PDF";
  }
  return `${translate(language, "file")} · ${fileType}`;
}

export type ChatBlock =
  | {
      kind: "text";
      content: string;
    }
  | {
      kind: "inlineVisual";
      title: string;
      metrics: Array<{ label: string; value: string; tone: "neutral" | "up" | "down" | "warn" }>;
    };

export type WorkflowProgressStep = {
  id: string;
  title?: string;
  kind: "collect_data" | "skill";
  status: string;
  warnings: string[];
  inputContext?: string;
  market?: string;
};

export type WorkflowStreamState = {
  label: string;
  complete: boolean;
  steps: WorkflowProgressStep[];
  answer: string;
  citations: LiveCitation[];
  artifacts: Artifact[];
};

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  blocks: ChatBlock[];
  artifacts: ChatArtifact[];
  workflowRun?: WorkflowRun;
  pending?: boolean;
  streamState?: WorkflowStreamState;
};

export type ChatConversation = {
  id: string;
  title?: string;
  isWorkflowRun?: boolean;
  messages: ChatMessage[];
};

function slugify(value: string): string {
  const slug = value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "");
  return slug || "chat";
}

function truncateTitle(value: string): string {
  const trimmed = value.trim();
  if (trimmed.length <= 30) {
    return trimmed || "Untitled chat";
  }
  return `${trimmed.slice(0, 27)}...`;
}

export function getConversationTitle(conversation: ChatConversation): string {
  if (conversation.title) {
    return truncateTitle(conversation.title);
  }
  const firstUserMessage = conversation.messages.find((message) => message.role === "user");
  return truncateTitle(firstUserMessage?.content ?? "");
}

export function getLatestUserMessageId(conversation: ChatConversation): string | null {
  for (let index = conversation.messages.length - 1; index >= 0; index -= 1) {
    const message = conversation.messages[index];
    if (message?.role === "user") {
      return message.id;
    }
  }
  return null;
}

export function createNewConversation(firstMessage: string): ChatConversation {
  return {
    id: `chat-${crypto.randomUUID()}`,
    messages: [createUserMessage(firstMessage, 1)]
  };
}

export function createUserMessage(content: string, index: number): ChatMessage {
  return {
    id: `user-${index}`,
    role: "user",
    content,
    blocks: [{ kind: "text", content }],
    artifacts: []
  };
}

export function createMockResponse(prompt: string, language: "en" | "vi" = "en"): ChatMessage {
  const normalized = prompt.toLowerCase();
  const subject = normalized.includes("gold") ? "SJC Gold" : "VCB";

  return {
    id: `assistant-${slugify(prompt)}`,
    role: "assistant",
    content: translate(language, "mockResponse", { subject }),
    blocks: [
      {
        kind: "text",
        content: translate(language, "mockResearchView", { subject })
      },
      {
        kind: "inlineVisual",
        title: translate(language, "quickView", { subject }),
        metrics: [
          { label: translate(language, "direction"), value: translate(language, normalized.includes("risk") ? "mixed" : "constructive"), tone: "up" },
          { label: translate(language, "freshness"), value: "Demo", tone: "warn" },
          { label: translate(language, "evidence"), value: translate(language, "mockEvidence"), tone: "neutral" }
        ]
      }
    ],
    artifacts: [
      {
        id: "artifact-report",
        kind: "report",
        title: translate(language, "mockReport", { subject }),
        summary: translate(language, "mockReportSummary")
      }
    ]
  };
}


export function createWorkflowAssistantMessage(run: WorkflowRun, index: number): ChatMessage {
  const sections = run.output.sections;
  const reportContent = sections.map((section) => section.content).join("\n\n---\n\n");
  const language = isUiLanguage(run.inputs.language) ? run.inputs.language : "en";
  const artifacts: ChatArtifact[] = mapArtifactsToCards(run.output.artifacts, run.id, language);
  return {
    id: `assistant-wf-${index}`,
    role: "assistant",
    content: reportContent,
    blocks: [{ kind: "text", content: reportContent }],
    artifacts,
    workflowRun: run,
    streamState: workflowStreamStateFromRun(run)
  };
}


export function createPendingAssistantMessage(index: number, inputContext?: string): ChatMessage {
  return {
    id: `assistant-pending-${index}`,
    role: "assistant",
    content: "",
    blocks: [{ kind: "text", content: "" }],
    artifacts: [],
    pending: true,
    streamState: {
      label: "working",
      complete: false,
      steps: inputContext
        ? [
            {
              id: "collect_data",
              kind: "collect_data",
              status: "running",
              warnings: [],
              inputContext
            }
          ]
        : [],
      answer: "",
      citations: [],
      artifacts: []
    }
  };
}


export function workflowStreamStateFromRun(run: WorkflowRun): WorkflowStreamState {
  const inputContext = inputContextForRun(run);
  return {
    label: "completed",
    complete: true,
    steps: run.output.steps.map((step) => ({
      id: step.id,
      kind: step.kind,
      status: step.status,
      warnings: step.warnings,
      inputContext,
      market: run.inputs.market
    })),
    answer: run.output.sections.map((section) => section.content).join("\n\n---\n\n"),
    citations: run.output.citations,
    artifacts: run.output.artifacts
  };
}


export function titleForStep(
  stepId: string,
  inputs?: Record<string, string>,
  language: UiLanguage = "en"
): string {
  return workflowStepTitle(language, stepId, inputs?.market);
}

export function inputContextForRun(run: WorkflowRun): string | undefined {
  return inputContextForInputs(run.inputs);
}

export function inputContextForInputs(inputs?: Record<string, string>): string | undefined {
  const symbol = inputs?.symbol?.trim().toUpperCase();
  if (symbol) {
    return symbol;
  }
  const market = inputs?.market?.trim().replace(/_/g, " ");
  return market || undefined;
}
