import type { WorkflowRun } from "../../api/client";

export type ChatArtifactKind = "report" | "chart" | "table" | "evidenceList" | "citationBundle";

export type ChatArtifact = {
  id: string;
  kind: ChatArtifactKind;
  title: string;
  summary: string;
};

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
      },
      {
        id: "artifact-citations",
        kind: "citationBundle",
        title: "Mock citation bundle",
        summary: "Shows the citation UX pattern without real chat evidence plumbing."
      },
      {
        id: "artifact-evidence",
        kind: "evidenceList",
        title: "Mock evidence list",
        summary: "Demonstrates how detailed evidence lists will open later."
      }
    ]
  };
}


export function createWorkflowAssistantMessage(run: WorkflowRun, index: number): ChatMessage {
  const sections = run.output.sections;
  const reportContent = sections.map((section) => section.content).join("\n\n---\n\n");
  const artifacts: ChatArtifact[] = [];
  if (run.output.artifacts.chart) {
    artifacts.push({
      id: `${run.id}-chart`,
      kind: "chart",
      title: run.output.artifacts.chart.title,
      summary: "Price chart from collected data"
    });
  }
  if (run.output.citations.length) {
    artifacts.push({
      id: `${run.id}-citations`,
      kind: "citationBundle",
      title: "Citations",
      summary: `${run.output.citations.length} source citation(s)`
    });
  }
  artifacts.push({
    id: `${run.id}-evidence`,
    kind: "evidenceList",
    title: "Evidence & Grounding",
    summary: `Grounding: ${run.output.grounding.grounding_status}`
  });
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
      answer: ""
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
    answer: run.output.sections.map((section) => section.content).join("\n\n---\n\n")
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
