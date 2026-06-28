import type { Workflow } from "../../api/client";

export type WorkflowCatalogSummary = {
  id: string;
  title: string;
  description: string;
  metadata: string;
  sections: string;
  stages: string[];
};

export function summarizeWorkflow(workflow: Workflow): WorkflowCatalogSummary {
  return {
    id: workflow.id,
    title: workflow.title,
    description: workflow.description,
    metadata: `${workflow.workflow_type} · ${workflow.market_scope.join(", ")}`,
    sections: workflow.output_sections.join(", "),
    stages: workflow.stages,
  };
}
