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

export type WorkflowStreamEvent = {
  event_id: string;
  run_id: string;
  sequence: number;
  kind:
    | "run.started"
    | "run.stage"
    | "answer.delta"
    | "citation"
    | "artifact"
    | "run.completed"
    | "run.failed";
  created_at: string;
  payload: Record<string, unknown>;
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
  inputs: WorkflowRunInput,
  onEvent?: (event: WorkflowStreamEvent) => void
): Promise<WorkflowRun> {
  return requestEventStream(`/api/workflows/${workflowId}/runs`, inputs, onEvent);
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

async function requestEventStream<T>(
  path: string,
  payload: object,
  onEvent?: (event: WorkflowStreamEvent) => void
): Promise<T> {
  const response = await fetch(path, {
    method: "POST",
    credentials: "include",
    headers: {
      Accept: "text/event-stream",
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    const errorPayload = (await response.json().catch(() => ({}))) as {
      detail?: string | { error?: { message?: string } };
      error?: { message?: string };
    };
    const message =
      typeof errorPayload.detail === "string"
        ? errorPayload.detail
        : errorPayload.detail?.error?.message ?? errorPayload.error?.message ?? `Request failed with ${response.status}`;
    throw new ApiError(message, response.status);
  }

  if (!response.body) {
    throw new ApiError("Streaming response body is missing", response.status);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let finalResult: T | null = null;

  while (true) {
    const { done, value } = await reader.read();
    buffer += decoder.decode(value ?? new Uint8Array(), { stream: !done });
    const frames = parseSseFrames(buffer);
    buffer = frames.remainder;
    for (const frame of frames.frames) {
      const event = parseSseFrame(frame);
      if (!event) continue;
      onEvent?.(event);
      if (event.kind === "run.completed") {
        finalResult = event.payload.run as T;
      }
      if (event.kind === "run.failed") {
        throw new ApiError(String(event.payload.message ?? "Workflow failed"), response.status);
      }
    }
    if (done) break;
  }

  if (finalResult === null) {
    throw new ApiError("Stream completed without final output", response.status);
  }
  return finalResult;
}

export function parseSseFrames(buffer: string): { frames: string[]; remainder: string } {
  const frames = buffer.split("\n\n");
  return {
    frames: frames.slice(0, -1),
    remainder: frames.at(-1) ?? ""
  };
}

export function parseSseFrame(frame: string): WorkflowStreamEvent | null {
  const event = { name: "message", data: "" };
  for (const line of frame.split("\n")) {
    if (line.startsWith("event:")) {
      event.name = line.slice("event:".length).trim();
    } else if (line.startsWith("data:")) {
      event.data += line.slice("data:".length).trim();
    }
  }
  if (!event.data) return null;
  return JSON.parse(event.data) as WorkflowStreamEvent;
}
