import { strict as assert } from "node:assert";
import { renderToStaticMarkup } from "react-dom/server";
import { ChatPage } from "./ChatPage";
import {
  createPendingAssistantMessage,
  createUserMessage,
  createWorkflowAssistantMessage,
  type ChatConversation
} from "./mockChat";
import type { WorkflowRun } from "../../api/client";

const workflowRun: WorkflowRun = {
  id: "run-dxg",
  kind: "workflow",
  status: "success",
  title: "DXG technical analysis",
  inputs: { market: "VN_STOCK", symbol: "DXG" },
  output: {
    sections: [
      {
        title: "Technical Analysis",
        status: "success",
        content: "DXG remains range-bound with mixed momentum.",
        citations: ["cite_1"],
        warnings: [],
        allowed_claims: ["trend"],
        blocked_claims: []
      }
    ],
    steps: [
      { id: "collect_data", kind: "collect_data", status: "success", warnings: [] },
      { id: "vn-technical-analysis", kind: "skill", status: "success", warnings: [] }
    ],
    collection: {
      collection_id: "collection-1",
      status: "success",
      providers: ["vnstock"],
      requested_dataset_groups: ["market_price"],
      provider_results: [],
      records_collected: 1,
      documents_collected: 0,
      warnings: [],
      failure_reasons: [],
      started_at: "2026-07-05T00:00:00+00:00",
      completed_at: "2026-07-05T00:00:01+00:00"
    },
    citations: [
      {
        citation_id: "cite_1",
        source_id: "vnstock_prices",
        dataset_id: "vn_prices",
        label: "VN Prices",
        timestamp: "2026-07-05T00:00:00+00:00"
      }
    ],
    artifacts: {},
    grounding: {
      grounding_status: "pass",
      blocked_claims: [],
      uncited_claims: []
    }
  }
};

const completedConversation: ChatConversation = {
  id: "conversation-complete",
  messages: [
    createUserMessage("Analyze DXG", 1),
    createWorkflowAssistantMessage(workflowRun, 1)
  ]
};

const completedMarkup = renderToStaticMarkup(
  <ChatPage
    conversation={completedConversation}
    onSelectArtifact={() => undefined}
    onSubmit={() => undefined}
  />
);

assert.doesNotMatch(completedMarkup, />You</);
assert.doesNotMatch(completedMarkup, />FinMind</);
assert.match(completedMarkup, /Completed 2 steps/);
assert.doesNotMatch(completedMarkup, />DXG</);
assert.match(completedMarkup, />Done</);
assert.doesNotMatch(completedMarkup, /<details[^>]*workflowProgress[^>]*open/);
assert.doesNotMatch(completedMarkup, /step\(s\)/);

const pendingMessage = createPendingAssistantMessage(1, "DXG");
pendingMessage.streamState = {
  label: "Working",
  complete: false,
  answer: "Collecting data",
  steps: [
    {
      id: "collect_data",
      title: "Collect VN stock data",
      kind: "collect_data",
      status: "running",
      warnings: [],
      inputContext: "DXG"
    }
  ]
};

const pendingConversation: ChatConversation = {
  id: "conversation-pending",
  messages: [createUserMessage("Analyze DXG", 1), pendingMessage]
};

const pendingMarkup = renderToStaticMarkup(
  <ChatPage
    conversation={pendingConversation}
    onSelectArtifact={() => undefined}
    onSubmit={() => undefined}
  />
);

assert.match(pendingMarkup, /Working/);
assert.match(pendingMarkup, /<details[^>]*workflowProgress[^>]*open/);
assert.doesNotMatch(pendingMarkup, /step\(s\)/);
