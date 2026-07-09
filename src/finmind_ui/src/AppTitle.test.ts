import { strict as assert } from "node:assert";
import { getChatHeaderTitle } from "./App";
import { createNewConversation } from "./features/chat/mockChat";

assert.equal(getChatHeaderTitle(null), "Chat");
assert.equal(getChatHeaderTitle(createNewConversation("Review request")), "Review request");
