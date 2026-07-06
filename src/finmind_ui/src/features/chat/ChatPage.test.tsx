import { strict as assert } from "node:assert";
import { renderToStaticMarkup } from "react-dom/server";
import { ArtifactPanel } from "./ArtifactPanel";
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
        content: "DXG remains range-bound with mixed momentum. [citation_vn_indicators_VIX-indicators]",
        citations: ["cite_1", "citation_vn_indicators_VIX-indicators"],
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
      },
      {
        citation_id: "citation_vn_indicators_VIX-indicators",
        source_id: "vnstock_indicators",
        dataset_id: "vn_indicators",
        label: "VIX indicators",
        timestamp: "2026-07-05T00:00:00+00:00"
      }
    ],
    artifacts: [
      {
        artifact_id: "art_chart_1",
        artifact_type: "chart",
        chart_intent: "price_trend",
        title: "DXG price chart",
        status: "ready",
        inputs: { dataset_id: "vn_prices", record_key: "DXG-prices" },
        spec: {
          supported_views: ["line", "candlestick"],
          default_view: "line",
          x_axis: { field: "date", type: "time" },
          series: [
            {
              name: "Close",
              type: "line",
              data: [{ date: "2026-07-05", value: 18200 }]
            }
          ],
          candles: [
            {
              date: "2026-07-05",
              open: 18200,
              high: 18400,
              low: 18000,
              close: 18200,
              volume: 1000
            }
          ]
        },
        downloads: [],
        source_refs: ["cite_1"]
      }
    ],
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
    onSelectCitation={() => undefined}
    onSubmit={() => undefined}
  />
);

assert.doesNotMatch(completedMarkup, />You</);
assert.doesNotMatch(completedMarkup, />FinMind</);
assert.match(completedMarkup, /Completed 2 steps/);
assert.match(completedMarkup, />Done</);
assert.match(completedMarkup, /DXG price chart/);
assert.match(completedMarkup, /data-citation-id="citation_vn_indicators_VIX-indicators"/);
assert.match(completedMarkup, /VIX indicators/);
assert.doesNotMatch(completedMarkup, /VN Prices/);
assert.doesNotMatch(completedMarkup, /\[citation_vn_indicators_VIX-indicators\]/);
assert.doesNotMatch(completedMarkup, /\[cite:cite_1\]/);
assert.doesNotMatch(completedMarkup, />citation_vn_indicators_VIX-indicators</);
assert.doesNotMatch(completedMarkup, /citationBundle/);
assert.doesNotMatch(completedMarkup, /Evidence &amp; Grounding/);
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
    onSelectCitation={() => undefined}
    onSubmit={() => undefined}
  />
);

assert.match(pendingMarkup, /Working/);
assert.match(pendingMarkup, /<details[^>]*workflowProgress[^>]*open/);
assert.doesNotMatch(pendingMarkup, /step\(s\)/);

const citationPanelMarkup = renderToStaticMarkup(
  <ArtifactPanel
    artifact={null}
    selectedCitationId="cite_1"
    run={workflowRun}
    onClose={() => undefined}
  />
);

assert.match(citationPanelMarkup, /Citations/);
assert.match(citationPanelMarkup, /VN Prices/);
assert.match(citationPanelMarkup, /selected/);
