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

// Citation appearance-ordering: panel order must match inline chip ordinals.
import { orderCitationsByAppearance, type LiveCitation } from "./mockChat";

const citationsInCollectionOrder: LiveCitation[] = [
  { citation_id: "citation_A", record_id: "rA", record_type: "generic", source_id: "srcA", dataset_id: "dsA", label: "Alpha", timestamp: "2026-07-05T00:00:00+00:00", display_content: "Alpha", payload_snapshot: {} },
  { citation_id: "citation_B", record_id: "rB", record_type: "generic", source_id: "srcB", dataset_id: "dsB", label: "Beta", timestamp: "2026-07-05T00:00:00+00:00", display_content: "Beta", payload_snapshot: {} },
  { citation_id: "citation_C", record_id: "rC", record_type: "generic", source_id: "srcC", dataset_id: "dsC", label: "Gamma", timestamp: "2026-07-05T00:00:00+00:00", display_content: "Gamma", payload_snapshot: {} }
];

// B appears first in the answer text, then A; C is never referenced.
const sourceWithBFirst = "Momentum is mixed [citation_B]. Valuation looks stretched [citation_A].";

const ordered = orderCitationsByAppearance(sourceWithBFirst, citationsInCollectionOrder);
assert.equal(ordered.citations.length, 3);
assert.equal(ordered.citations[0].citation_id, "citation_B", "B appears first in text so leads the panel");
assert.equal(ordered.citations[1].citation_id, "citation_A", "A appears second in text");
assert.equal(ordered.citations[2].citation_id, "citation_C", "unreferenced C is appended last");
assert.equal(ordered.ordinals.get("citation_B"), 1);
assert.equal(ordered.ordinals.get("citation_A"), 2);
assert.equal(ordered.ordinals.get("citation_C"), undefined, "unreferenced citations get no ordinal");

// `[cite:id]` form is also recognized and does not change ordering.
const sourceWithCiteForm = "First [cite:citation_A] then [cite:citation_B].";
const orderedCite = orderCitationsByAppearance(sourceWithCiteForm, citationsInCollectionOrder);
assert.equal(orderedCite.citations[0].citation_id, "citation_A");
assert.equal(orderedCite.citations[1].citation_id, "citation_B");
assert.equal(orderedCite.ordinals.get("citation_A"), 1);
assert.equal(orderedCite.ordinals.get("citation_B"), 2);
