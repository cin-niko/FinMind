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
    id: `chat-${slugify(firstMessage)}`,
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
