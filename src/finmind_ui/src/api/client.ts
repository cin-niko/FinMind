export type SessionState = { authenticated: false } | { authenticated: true; role: "admin" };

export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export type Workflow = {
  id: string;
  title: string;
  description: string;
  workflow_type: "atomic" | "internal" | "composite";
  market_scope: string[];
  required_inputs: Array<{ name: string; type: string; required: boolean }>;
  stages: string[];
  requires_citations: boolean;
  chart_requirements: string[];
  output_sections: string[];
};

export type WorkflowRunInput = {
  market: string;
  symbol?: string;
};

export type WorkflowRun = {
  id: string;
  kind: "workflow";
  status: "success" | "partial" | "failed";
  title: string | null;
  inputs: Record<string, string>;
  output: {
    sections: Array<{
      title: string;
      status: string;
      content: string;
      citations: string[];
      warnings: string[];
      allowed_claims: string[];
      blocked_claims: string[];
    }>;
    steps: Array<{ id: string; kind: "collect_data" | "skill"; status: string; warnings: string[] }>;
    collection: {
      collection_id: string;
      status: "success" | "partial" | "failed" | "fallback";
      providers: string[];
      requested_dataset_groups: string[];
      provider_results: Array<{
        provider_id: string;
        dataset_groups: string[];
        status: string;
        source_ids: string[];
        warnings: string[];
        failure_reason?: string;
        rate_limit_hint?: string;
      }>;
      records_collected: number;
      documents_collected: number;
      warnings: string[];
      failure_reasons: string[];
      started_at: string;
      completed_at: string | null;
    };
    citations: Array<{
      citation_id: string;
      source_id: string;
      dataset_id: string;
      label: string;
      timestamp: string;
    }>;
    artifacts: {
      chart?: {
        artifact_id: string;
        artifact_type: "chart";
        title: string;
        payload: {
          series: Array<{ time: string; value: number; change_percent?: number }>;
          table: Array<{ date: string; close: number; volume?: number }>;
        };
        source_refs: string[];
      };
    };
    grounding: {
      grounding_status: "pass" | "blocked";
      blocked_claims: string[];
      uncited_claims: string[];
    };
  };
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    credentials: "include",
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init
  });

  if (!response.ok) {
    const payload = (await response.json().catch(() => ({}))) as { detail?: string };
    throw new ApiError(payload.detail ?? `Request failed with ${response.status}`, response.status);
  }

  return (await response.json()) as T;
}

export function getSession(): Promise<SessionState> {
  return request<SessionState>("/api/session");
}

export function login(username: string, password: string): Promise<SessionState> {
  return request<SessionState>("/api/login", {
    method: "POST",
    body: JSON.stringify({ username, password })
  });
}

export function logout(): Promise<SessionState> {
  return request<SessionState>("/api/logout", { method: "POST" });
}

export function listWorkflows(): Promise<Workflow[]> {
  return request<Workflow[]>("/api/workflows");
}

export function runWorkflow(
  workflowId: string,
  inputs: WorkflowRunInput
): Promise<WorkflowRun> {
  return request<WorkflowRun>(`/api/workflows/${workflowId}/run`, {
    method: "POST",
    body: JSON.stringify(inputs)
  });
}

export function listRuns(): Promise<WorkflowRun[]> {
  return request<WorkflowRun[]>("/api/runs");
}

export function getRun(runId: string): Promise<WorkflowRun> {
  return request<WorkflowRun>(`/api/runs/${runId}`);
}

export function deleteRun(runId: string): Promise<void> {
  return request<void>(`/api/runs/${runId}`, { method: "DELETE" });
}

export function renameRun(runId: string, title: string): Promise<WorkflowRun> {
  return request<WorkflowRun>(`/api/runs/${runId}`, {
    method: "PATCH",
    body: JSON.stringify({ title })
  });
}

export function isUnauthorizedError(caught: unknown): boolean {
  return caught instanceof ApiError && caught.status === 401;
}
