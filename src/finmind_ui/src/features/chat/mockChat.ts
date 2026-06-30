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

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  blocks: ChatBlock[];
  artifacts: ChatArtifact[];
  workflowRun?: WorkflowRun;
};

export type ChatConversation = {
  id: string;
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
  if (trimmed.length <= 56) {
    return trimmed || "Untitled chat";
  }
  return `${trimmed.slice(0, 53)}...`;
}

export function getConversationTitle(conversation: ChatConversation): string {
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
    id: `chat-${slugify(firstMessage)}-${Date.now()}`,
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
    workflowRun: run
  };
}
