import { strict as assert } from "node:assert";
import type { Workflow } from "../../api/client";
import { summarizeWorkflow } from "./workflowCatalog";

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
  chart_requirements: ["price_series"],
  output_sections: ["Data Quality", "Collected Data"],
};

const summary = summarizeWorkflow(workflow);

assert.equal(summary.id, "vn-financial-data-collector");
assert.equal(summary.title, "VN Financial Data Collector");
assert.equal(summary.description, "Collects and checks VN stock financial data.");
assert.equal("metadata" in summary, false);
assert.equal("sections" in summary, false);
assert.equal("stages" in summary, false);
