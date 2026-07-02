import type { Workflow } from "../../api/client";

export type WorkflowCatalogSummary = {
  id: string;
  title: string;
  description: string;
};

export function summarizeWorkflow(workflow: Workflow): WorkflowCatalogSummary {
  return {
    id: workflow.id,
    title: workflow.title,
    description: workflow.description,
  };
}
