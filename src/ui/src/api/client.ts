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
  market_scope: string[];
  required_inputs: Array<{ name: string; type: string; required: boolean }>;
  stages: string[];
  requires_citations: boolean;
  chart_requirements: string[];
};

export type WorkflowRunInput = {
  market: string;
  symbol?: string;
};

export type WorkflowRun = {
  id: string;
  kind: "workflow";
  status: "success" | "partial" | "failed";
  output: {
    sections: Array<{ title: string; content: string; citations: string[] }>;
    citations: Array<{
      citation_id: string;
      evidence_id: string;
      label: string;
      source_type: string;
      source_reference: string;
      timestamp: string;
    }>;
    freshness: Array<{ dataset: string; status: string; as_of: string }>;
    artifacts: {
      chart?: {
        artifact_id: string;
        artifact_type: "chart";
        title: string;
        payload: {
          series: Array<{ time: string; value: number; change_percent?: number }>;
          table: Array<{ record_key: string; market_time: string; close: number }>;
        };
        evidence_refs: string[];
      };
    };
    visible_execution: { stages: string[]; tool_status: string };
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

export function isUnauthorizedError(caught: unknown): boolean {
  return caught instanceof ApiError && caught.status === 401;
}
