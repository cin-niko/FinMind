import type { Workflow } from "../../api/client";

export type WorkflowMarket = "VN_STOCK" | "GOLD";

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

const MARKET_LABELS: Record<WorkflowMarket, string> = {
  VN_STOCK: "VN stocks",
  GOLD: "Gold",
};

export function marketLabel(market: WorkflowMarket): string {
  return MARKET_LABELS[market];
}

export function isSupportedWorkflowMarket(market: string): market is WorkflowMarket {
  return market === "VN_STOCK" || market === "GOLD";
}

export function formatWorkflowMarket(market: string): string {
  return isSupportedWorkflowMarket(market) ? marketLabel(market) : "Unsupported market";
}

export function summarizeWorkflow(workflow: Workflow): WorkflowCatalogSummary {
  return {
    id: workflow.id,
    title: workflow.title,
    description: workflow.description,
    markets: workflow.market_scope.map(formatWorkflowMarket),
    requiredInputs: workflow.required_inputs.map((input) => input.name),
    stages: workflow.stages,
    sections: workflow.output_sections,
    citationLabel: workflow.requires_citations ? "Citations required" : "Citations optional",
    chartLabel: workflow.chart_requirements[0]?.title ?? "No chart",
  };
}
