import type { Workflow } from "../../api/client";

const TEMPLATES: Record<string, (symbol: string) => string> = {
  "vn-financial-data-collector": (s) => `Collect and audit financial data for stock ${s}`,
  "vn-fundamental-analysis": (s) => `Analyze the fundamentals of stock ${s}`,
  "vn-technical-analysis": (s) => `Analyze the technicals of stock ${s}`,
};

export function workflowPromptTemplate(workflowId: string): (symbol: string) => string {
  return TEMPLATES[workflowId] ?? ((s) => `Analyze stock ${s}`);
}

export function workflowShortLabel(workflow: Workflow): string {
  const id = workflow.id;
  if (id.includes("fundamental")) return "Fundamental Analysis";
  if (id.includes("technical")) return "Technical Analysis";
  if (id.includes("collector")) return "Data Collector";
  return workflow.title;
}

export function workflowIconKey(workflow: Workflow): string {
  const id = workflow.id;
  if (id.includes("fundamental")) return "fundamental";
  if (id.includes("technical")) return "technical";
  if (id.includes("collector")) return "collector";
  return "default";
}
