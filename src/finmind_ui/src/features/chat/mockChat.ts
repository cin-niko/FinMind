import type { Artifact, ArtifactDownload, WorkflowRun } from "../../api/client";

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

export function mapArtifactsToCards(artifacts: Artifact[], runId: string): ChatArtifact[] {
  return artifacts.map((artifact) => ({
    id: `${runId}-${artifact.artifact_id}`,
    artifactId: artifact.artifact_id,
    kind: artifact.artifact_type,
    title: artifactDisplayTitle(artifact),
    typeLabel: artifactTypeLabel(artifact),
    download: artifact.downloads[0] ?? (artifact.artifact_type === "file" ? {
      url: artifact.file.url,
      filename: artifact.file.filename,
      mime_type: artifact.file.mime_type
    } : undefined),
    summary:
      artifact.artifact_type === "chart"
        ? "Chart artifact"
        : `${artifact.file_type.toUpperCase()} file`
  }));
}

function artifactDisplayTitle(artifact: Artifact): string {
  if (artifact.artifact_type !== "chart") {
    return artifact.title;
  }
  const recordKey = typeof artifact.inputs.record_key === "string" ? artifact.inputs.record_key : "";
  const symbol = recordKey.split(/[-_:]/)[0]?.trim().toUpperCase();
  return symbol ? `${symbol} Chart` : artifact.title;
}

function artifactTypeLabel(artifact: Artifact): string {
  if (artifact.artifact_type === "chart") {
    return "Chart";
  }
  const fileType = artifact.file_type.toUpperCase();
  if (fileType === "XLSX" || fileType === "CSV") {
    return `Spreadsheet · ${fileType}`;
  }
  if (fileType === "PDF") {
    return "PDF";
  }
  return `File · ${fileType}`;
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
  title: string;
  kind: "collect_data" | "skill";
  status: string;
  warnings: string[];
  inputContext?: string;
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

export function createMockResponse(prompt: string): ChatMessage {
  const normalized = prompt.toLowerCase();
  const subject = normalized.includes("gold") ? "SJC Gold" : "VCB";

  return {
    id: `assistant-${slugify(prompt)}`,
    role: "assistant",
    content: `Mock response for ${subject}. This is a deterministic V1 chat answer; it does not call the production orchestrator.`,
    blocks: [
      {
        kind: "text",
        content: `Here is a mock research view for ${subject}. Inline visuals are rendered from trusted local templates only.`
      },
      {
        kind: "inlineVisual",
        title: `${subject} quick view`,
        metrics: [
          { label: "Direction", value: normalized.includes("risk") ? "Mixed" : "Constructive", tone: "up" },
          { label: "Freshness", value: "Demo", tone: "warn" },
          { label: "Evidence", value: "Mock citations", tone: "neutral" }
        ]
      }
    ],
    artifacts: [
      {
        id: "artifact-report",
        kind: "report",
        title: `${subject} mock report`,
        summary: "Open the full deterministic report in the right-side panel."
      }
    ]
  };
}


export function createWorkflowAssistantMessage(run: WorkflowRun, index: number): ChatMessage {
  const sections = run.output.sections;
  const reportContent = sections.map((section) => section.content).join("\n\n---\n\n");
  const artifacts: ChatArtifact[] = mapArtifactsToCards(run.output.artifacts, run.id);
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
      label: "Working",
      complete: false,
      steps: inputContext
        ? [
            {
              id: "collect_data",
              title: "Collect market data",
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
    label: `Completed ${run.output.steps.length} steps`,
    complete: true,
    steps: run.output.steps.map((step) => ({
      id: step.id,
      title: titleForStep(step.id, run.inputs),
      kind: step.kind,
      status: step.status,
      warnings: step.warnings,
      inputContext
    })),
    answer: run.output.sections.map((section) => section.content).join("\n\n---\n\n"),
    citations: run.output.citations,
    artifacts: run.output.artifacts
  };
}


export function titleForStep(stepId: string, inputs?: Record<string, string>): string {
  const marketLabel = marketLabelForInputs(inputs);
  if (stepId === "collect_data") {
    return marketLabel ? `Collect ${marketLabel} data` : "Collect market data";
  }
  if (stepId.includes("data-auditor")) {
    return "Audit source coverage";
  }
  if (stepId.includes("technical-analysis")) {
    return "Analyze technical momentum";
  }
  if (stepId.includes("fundamental-analysis")) {
    return "Analyze fundamentals";
  }
  if (stepId.includes("news")) {
    return "Review news signals";
  }
  if (stepId.includes("risk")) {
    return "Review downside risks";
  }
  return humanizeStepId(stepId);
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

function marketLabelForInputs(inputs?: Record<string, string>): string | null {
  const market = inputs?.market?.trim().toUpperCase();
  if (market === "VN_STOCK") {
    return "VN stock";
  }
  if (market === "US_STOCK") {
    return "US stock";
  }
  return null;
}

function humanizeStepId(stepId: string): string {
  return stepId
    .replace(/^vn-|^us-/, "")
    .replace(/-/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}
