import { strict as assert } from "node:assert";
import {
  createMockResponse,
  createNewConversation,
  createUserMessage,
  getConversationTitle,
  getLatestUserMessageId
} from "./mockChat";

const conversation = createNewConversation("What changed for VCB today?");
assert.equal(getConversationTitle(conversation), "What changed for VCB today?");
assert.match(conversation.id, /^chat-[0-9a-f-]{36}$/);

const duplicateConversation = createNewConversation("What changed for VCB today?");
assert.notEqual(duplicateConversation.id, conversation.id);

const longConversation = createNewConversation(
  "Review the full VN100 exposure and compare downside scenarios across banks"
);
const longTitle = getConversationTitle(longConversation);
assert.equal(longTitle, "Review the full VN100 expos...");
assert.ok(longTitle.endsWith("..."));
assert.ok(longTitle.length <= 32);

const response = createMockResponse("Show a VCB report with citations");
assert.equal(response.role, "assistant");
assert.ok(response.blocks.some((block) => block.kind === "inlineVisual"));
assert.ok(response.artifacts.some((artifact) => artifact.kind === "report"));
assert.ok(!response.artifacts.map((artifact) => artifact.kind).includes("citationBundle" as never));

const followUp = createUserMessage("What are the risks?", 3);
assert.equal(followUp.id, "user-3");
assert.equal(followUp.blocks[0]?.kind, "text");

assert.equal(
  getLatestUserMessageId({
    id: "chat-vcb",
    messages: [
      createUserMessage("First question", 1),
      createMockResponse("First answer"),
      createUserMessage("Follow up question", 2),
      createMockResponse("Follow up answer")
    ]
  }),
  "user-2"
);
