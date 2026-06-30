import { strict as assert } from "node:assert";
import {
  createNewConversation,
  createUserMessage,
  getConversationTitle,
  getLatestUserMessageId
} from "./mockChat";

const conversation = createNewConversation("Analyze the fundamentals of stock TPB");
assert.equal(getConversationTitle(conversation), "Analyze the fundamentals of stock TPB");

const followUp = createUserMessage("What are the risks?", 3);
assert.equal(followUp.id, "user-3");
assert.equal(followUp.blocks[0]?.kind, "text");

assert.equal(
  getLatestUserMessageId({
    id: "chat-vcb",
    messages: [
      createUserMessage("First question", 1),
      createUserMessage("Follow up question", 2),
    ]
  }),
  "user-2"
);
