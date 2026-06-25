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

export type MarketOverview = {
  available_markets: string[];
  selected_market: "VN" | "US" | "Commodity";
  watchlists: MarketCollection[];
  collections: MarketCollection[];
  index_charts: Array<{
    symbol: string;
    name: string;
    last: number;
    change_percent: number;
    series: Array<{ time: string; value: number }>;
  }>;
  heatmap: MarketInstrumentRow[];
  instrument_rows: MarketInstrumentRow[];
  meta?: MarketOverviewMeta;
};

export type MarketOverviewMeta = {
  roadmap_markets_enabled?: boolean;
};

export type MarketCollection = {
  id: string;
  name: string;
  type: "index" | "watchlist" | "sector" | "theme";
};

export type MarketInstrumentRow = {
  id: string;
  symbol: string;
  name: string;
  market: string;
  asset_class: string;
  exchange: string | null;
  currency: string;
  sector: string | null;
  industry: string | null;
  sub_industry: string | null;
  last: number;
  change_percent: number;
  volume: number;
  value: number;
  freshness: string;
  source_id?: string;
  as_of?: string;
};

export type LazyFetchStatus =
  | "success"
  | "already_present"
  | "blocked"
  | "failed"
  | "out_of_scope";

export type SerializedJob = {
  job_id: string;
  source_id: string;
  dataset_id: string;
  status: string;
  trigger?: string;
  started_at?: string;
  completed_at?: string | null;
  record_count?: number;
};

export type LazyFetch = {
  status: LazyFetchStatus;
  dataset_id: "vn_prices_daily";
  instrument_id: string;
  reason: string | null;
  jobs: SerializedJob[];
};

export type InstrumentChart = {
  instrument: {
    id: string;
    symbol: string;
    name: string;
    market: string;
    asset_class: string;
    exchange: string | null;
    currency: string;
    sector: string | null;
    industry: string | null;
    sub_industry: string | null;
  };
  timeframe: "1h" | "4h" | "1d" | "1M";
  freshness: { status: string; as_of: string };
  records: Array<{
    time: string;
    open: number;
    high: number;
    low: number;
    close: number;
    volume?: number;
  }>;
  table: Array<{
    time: string;
    open: number;
    high: number;
    low: number;
    close: number;
    volume?: number;
  }>;
  lazy_fetch?: LazyFetch;
};

export type IngestionJob = {
  job_id: string;
  source_id: string;
  dataset_id: string;
  period: string;
  trigger: "manual" | "scheduled" | "backfill";
  status: "queued" | "running" | "success" | "failed" | "blocked";
  started_at: string;
  completed_at: string | null;
  record_count: number;
  diagnostics: Record<string, unknown>;
};

export type DatasetFreshness = {
  dataset: string;
  status: "fresh" | "stale" | "missing" | "failed";
  as_of: string | null;
  record_count: number;
};

export type IngestionStatus = {
  jobs: IngestionJob[];
  freshness: DatasetFreshness[];
};

export type IngestionFetchRequest = {
  source_id: string;
  mode: "latest" | "period";
  period?: string;
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

export function getMarketOverview(
  market: "VN" | "US" | "Commodity",
  collectionId?: string
): Promise<MarketOverview> {
  const params = new URLSearchParams({ market });
  if (collectionId) {
    params.set("collection_id", collectionId);
  }
  return request<MarketOverview>(`/api/market/overview?${params.toString()}`);
}

export function getInstrumentChart(
  instrumentId: string,
  timeframe: InstrumentChart["timeframe"]
): Promise<InstrumentChart> {
  const params = new URLSearchParams({ timeframe });
  return request<InstrumentChart>(
    `/api/market/instruments/${encodeURIComponent(instrumentId)}/chart?${params.toString()}`
  );
}

export function getIngestionStatus(): Promise<IngestionStatus> {
  return request<IngestionStatus>("/api/admin/ingestion");
}

export function triggerManualFetch(payload: IngestionFetchRequest): Promise<IngestionJob> {
  return request<IngestionJob>("/api/admin/fetch", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function isUnauthorizedError(caught: unknown): boolean {
  return caught instanceof ApiError && caught.status === 401;
}
