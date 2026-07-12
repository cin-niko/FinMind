import { strict as assert } from "node:assert";
import type { Workflow } from "../../api/client";
import { marketLabel, parseWorkflowMarket, summarizeWorkflow } from "./workflowCatalog";

const workflow: Workflow = {
  id: "vn-financial-data-collector",
  title: "VN Financial Data Collector",
  description: "Collects and checks VN stock financial data.",
  workflow_type: "atomic",
  market_scope: ["VN_STOCK"],
  required_inputs: [
    { name: "market", type: "string", required: true },
    { name: "symbol", type: "string", required: true },
  ],
  stages: ["data-collector", "data-quality-check"],
  requires_citations: true,
  chart_requirements: [
    {
      chart_id: "price_trend",
      chart_type: "line",
      title: "Price trend",
      source_types: ["market_price"],
      required: true
    }
  ],
  output_sections: ["Data Quality", "Collected Data"],
};

const summary = summarizeWorkflow(workflow);

assert.equal(summary.id, "vn-financial-data-collector");
assert.equal(summary.title, "VN Financial Data Collector");
assert.equal(summary.description, "Collects and checks VN stock financial data.");
assert.deepEqual(summary.markets, ["VN stocks"]);
assert.deepEqual(summary.requiredInputs, ["market", "symbol"]);
assert.deepEqual(summary.stages, ["data-collector", "data-quality-check"]);
assert.deepEqual(summary.sections, ["Data Quality", "Collected Data"]);
assert.equal(summary.citationLabel, "Citations required");
assert.equal(summary.chartLabel, "Price trend");
assert.equal(marketLabel("GOLD"), "Gold");
assert.throws(() => parseWorkflowMarket("FUTURE_MARKET"), /Unsupported workflow market/);
