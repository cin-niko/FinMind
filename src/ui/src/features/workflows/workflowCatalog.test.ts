import { strict as assert } from "node:assert";
import type { Workflow } from "../../api/client";
import { summarizeWorkflow } from "./workflowCatalog";

const workflow: Workflow = {
  id: "stock-brief",
  title: "Stock Brief",
  description: "Combined cited stock research brief.",
  workflow_type: "composite",
  market_scope: ["VN_STOCK", "US_STOCK"],
  required_inputs: [
    { name: "market", type: "string", required: true },
    { name: "symbol", type: "string", required: true },
  ],
  stages: ["data-collector", "data-quality-check", "technical-analysis"],
  requires_citations: true,
  chart_requirements: ["price_series"],
  output_sections: ["Data Quality", "Technical Analysis"],
};

const summary = summarizeWorkflow(workflow);

assert.equal(summary.id, "stock-brief");
assert.equal(summary.metadata, "composite · VN_STOCK, US_STOCK");
assert.equal(summary.sections, "Data Quality, Technical Analysis");
assert.deepEqual(summary.stages, workflow.stages);
