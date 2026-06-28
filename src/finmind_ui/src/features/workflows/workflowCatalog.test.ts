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
assert.equal(summary.metadata, "atomic · VN_STOCK");
assert.equal(summary.sections, "Data Quality, Collected Data");
assert.deepEqual(summary.stages, workflow.stages);
assert.equal(summary.metadata.includes("vnstock"), false);
assert.equal(summary.metadata.includes("alpha_vantage"), false);
