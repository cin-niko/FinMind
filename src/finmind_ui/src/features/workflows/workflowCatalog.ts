import type { Workflow } from "../../api/client";

export type WorkflowCatalogSummary = {
  id: string;
  title: string;
  description: string;
  markets: string[];
  requiredInputs: string[];
  stages: string[];
  sections: string[];
  citationLabel: string;
  chartLabel: string;
};

const MARKET_LABELS: Record<string, string> = {
  VN_STOCK: "VN stocks",
  GOLD: "Gold",
};

export function marketLabel(market: string): string {
  return MARKET_LABELS[market] ?? market;
}

export function summarizeWorkflow(workflow: Workflow): WorkflowCatalogSummary {
  return {
    id: workflow.id,
    title: workflow.title,
    description: workflow.description,
    markets: workflow.market_scope.map(marketLabel),
    requiredInputs: workflow.required_inputs.map((input) => input.name),
    stages: workflow.stages,
    sections: workflow.output_sections,
    citationLabel: workflow.requires_citations ? "Citations required" : "Citations optional",
    chartLabel: workflow.chart_requirements[0]?.title ?? "No chart",
  };
}
