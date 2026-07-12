---
id: SPEC-FEAT-002-CONTRACTS
feature: workflow
status: active
owner: solo
created: 2026-06-26
implements: []
validated_by: []
adr_refs:
  - docs/adr/ADR-001-hybrid-workflow-definitions-and-agent-skills.md
  - docs/adr/ADR-002-direct-async-sse-streaming.md
  - docs/adr/ADR-003-artifact-and-citation-inspection-contract.md
---

# API Contract: Workflow

All endpoints require an authenticated cookie-backed session.

## `GET /api/workflows`

Returns UI-runnable workflow catalog entries. Internal steps such as
`collect_data` and the data-audit skill are not primary catalog cards.

Response item shape:

```json
{
  "id": "stock-brief",
  "title": "Stock Brief",
  "description": "Combined cited stock research brief.",
  "workflow_type": "composite",
  "market_scope": ["VN_STOCK"],
  "required_inputs": [
    { "name": "market", "type": "string", "required": true },
    { "name": "symbol", "type": "string", "required": true }
  ],
  "stages": [
    "collect_data",
    "data-audit",
    "fundamental-analysis",
    "technical-analysis"
  ],
  "requires_citations": true,
  "chart_requirements": [
    {
      "chart_id": "price_trend",
      "chart_type": "line",
      "title": "Price trend",
      "source_types": ["market_price"],
      "required": true
    }
  ],
  "output_sections": [
    "Data Quality",
    "Fundamentals",
    "Technical Analysis"
  ]
}
```

Required catalog ids:

- `fundamental-analysis`
- `technical-analysis`
- `stock-brief`

## Final Workflow Run Shape

`POST /api/workflows/{workflow_id}/runs` emits this payload in a
`run.completed` stream event and persists the same shape for later
`GET /api/runs/{run_id}` reinspection.

```json
{
  "id": "run_abc123",
  "kind": "workflow",
  "status": "partial",
  "inputs": { "market": "VN_STOCK", "symbol": "VCB" },
  "started_at": "2026-06-27T00:00:00+00:00",
  "completed_at": "2026-06-27T00:00:02+00:00",
  "output": {
    "sections": [
      {
        "title": "Collected Data",
        "status": "success",
        "content": "Audited VCB financial data package with citations.",
        "citations": ["cite_1"],
        "warnings": [],
        "allowed_claims": ["data_availability"],
        "blocked_claims": []
      },
      {
        "title": "Fundamentals",
        "status": "partial",
        "content": "Fundamental analysis on available statements; catalyst claims unavailable.",
        "citations": ["cite_1"],
        "warnings": ["unsupported_news_scope"],
        "allowed_claims": ["financial_history"],
        "blocked_claims": ["recent_news_impact", "catalyst_analysis"]
      }
    ],
    "steps": [
      { "id": "collect_data", "kind": "collect_data", "status": "partial", "warnings": ["provider_unavailable"] },
      { "id": "vn-financial-data-auditor", "kind": "skill", "status": "success", "warnings": [] },
      { "id": "vn-fundamental-analysis", "kind": "skill", "status": "partial", "warnings": ["unsupported_news_scope"] }
    ],
    "collection": {
      "status": "partial",
      "collection_id": "collection_abc123",
      "providers": ["vnstock"],
      "requested_dataset_groups": ["market_price", "fundamental"],
      "provider_results": [
        {
          "provider_id": "vnstock",
          "dataset_groups": ["market_price", "fundamental"],
          "status": "success",
          "source_ids": ["vnstock_prices", "vnstock_fundamentals"],
          "warnings": []
        }
      ],
      "records_collected": 2,
      "documents_collected": 0,
      "warnings": [],
      "failure_reasons": [],
      "started_at": "2026-06-27T00:00:00+00:00",
      "completed_at": "2026-06-27T00:00:01+00:00"
    },
    "citations": [
      {
        "citation_id": "cite_1",
        "record_id": "data_price_summary_VN_STOCK_VCB_2026-06-18_v1",
        "record_type": "price_summary_record",
        "source_id": "vnstock_prices",
        "dataset_id": "vn_prices",
        "label": "Demo VN Prices",
        "timestamp": "2026-06-18T07:00:00+00:00",
        "cited_fields": ["payload.close", "payload.change_pct"],
        "payload_snapshot": {
          "close": 87200,
          "change_pct": 1.2,
          "volume": 1200000
        },
        "display_content": "- Close: 87,200\n- Daily change: +1.2%\n- Volume: 1,200,000",
        "methodology_version": "price-summary-v1"
      }
    ],
    "artifacts": [
      {
        "artifact_id": "artifact_1",
        "artifact_type": "chart",
        "chart_intent": "price_trend",
        "title": "VCB Price Series",
        "status": "ready",
        "inputs": {
          "dataset_id": "vn_prices",
          "record_key": "VCB-2026-06-18"
        },
        "spec": {
          "supported_views": ["line", "candlestick"],
          "default_view": "line",
          "x_axis": { "field": "date", "type": "time" },
          "series": [
            {
              "name": "Close",
              "type": "line",
              "data": [{ "date": "2026-06-18", "value": 58200 }]
            }
          ],
          "candles": [
            {
              "date": "2026-06-18",
              "open": 58000,
              "high": 58500,
              "low": 57800,
              "close": 58200,
              "volume": 1000000
            }
          ]
        },
        "downloads": [
          {
            "format": "svg",
            "url": "/api/artifacts/artifact_1/download?format=svg",
            "filename": "vcb-price-series.svg",
            "mime_type": "image/svg+xml"
          },
          {
            "format": "csv",
            "url": "/api/artifacts/artifact_1/download?format=csv",
            "filename": "vcb-price-series.csv",
            "mime_type": "text/csv"
          }
        ],
        "source_refs": ["cite_1"]
      }
    ],
    "grounding": {
      "grounding_status": "pass",
      "blocked_claims": ["recent_news_impact", "catalyst_analysis"],
      "uncited_claims": []
    }
  },
  "logs": [
    { "event": "workflow_started", "stage": "collect_data" },
    { "event": "workflow_completed", "status": "partial" }
  ]
}
```

Artifact rules:

- `artifact_type` is the top-level discriminator. Phase 02 supports `file` and
  `chart`.
- `artifacts` is an ordered list of `Artifact` objects rather than a map keyed
  by type. Multiple files or charts may be attached to one answer.
- File artifacts include `file_type`, file metadata, `mime_type`, downloads,
  status, and `source_refs`.
- Chart artifacts include `chart_intent`, `spec.supported_views`,
  `spec.default_view`, renderable chart data, downloads, status, and
  `source_refs`.
- Chart artifacts do not require a price table in the main answer payload.
- Citations remain source references and are not returned as artifact cards.

Raw agent reasoning must never appear in responses.

Step and grounding contract:

- `steps` is the ordered `step_sequence` execution trace. Each step has `kind`
  `collect_data` or `skill`, a `status`, and `warnings`.
- `collect_data` step status is informational only (`success`, `partial`, or
  `failed`); run status is derived from skill steps.
- Skill step `status` values: `success`, `partial`, `failed`. There is no
  pre-skill fail-fast: a skill runs on whatever `collect_data` returned and
  resolves which claims it can support, reporting `blocked_claims` for the rest.
  Run status is `failed` if any skill step failed, else `partial` if any skill
  step is `partial`, else `success`.
- `collect_data` is the only hard floor: zero records and zero source documents
  fails the run before any skill step.
- `grounding.grounding_status` is `pass` or `blocked`. It is `blocked` only when
  claims cite ids not present in the returned citation allowlist
  (`uncited_claims`).
- `grounding.blocked_claims` lists claim categories the skill reported blocked
  (surfaced for transparency).
- `grounding.uncited_claims` lists claims whose citations are not a subset of the
  returned citation ids (a grounding violation).
- Raw agent reasoning must never appear in `steps`, `sections`, or `grounding`.
- Material claims generated by a skill must pass FinMind validators for
  citations, market scope, and advice-only framing before appearing in
  `sections`. Data age is conveyed by citation `timestamp`; there is no separate
  freshness field.
- The run result plus its `inputs` must provide enough safe metadata for the UI
  to derive product-facing execution labels and optional input subtext without
  exposing hidden reasoning or raw internal diagnostics.

Collection contract:

- `collection.status` values: `success`, `partial`, or `failed`.
- `collection` is produced by `src/finmind_agents/dataflows/` after a
  FinMind-validated collection plan, not direct workflow or agent provider calls.
- `providers` may include configured live source providers such as `vnstock`.
- `requested_dataset_groups` values are `market_price` and `fundamental` for
  Phase 02.
- Requested dataset groups are derived from the referenced skills'
  `DATA_REQUIREMENTS.yaml` (raw-data skills only; upstream-dependent skills have
  none and are not added to the collect fetch list). Workflow YAML must not
  duplicate detailed dataset requirements.
- `provider_results` are safe status summaries. They must not include raw
  provider payloads.
- Provider API keys, credentials, raw responses, hidden prompts, and unsafe
  diagnostics must never appear in API responses.
- If live provider collection fails, the response must preserve safe warnings or
  failure reasons so affected claims are marked unavailable.

Evidence and citation contract:

- Derived `DataRecord` objects are deterministic runtime records built after
  collection and before the LLM call.
- The data bundle is the compact model-visible subset plus citation allowlist.
- `citations` are persisted pointers to data records; they include
  `record_id`, `record_type`, source id, dataset id, label, timestamp,
  optional cited fields, structured `payload_snapshot`, and optional
  `display_content`.
- `price_series_record` may be persisted for chart rendering and reuse but is
  excluded from the normal LLM data bundle.
- Intermediate derived records are not required to be persisted durably for
  every run.
- `fundamental_record.is_audited=true` is required for confident fundamental
  claims. If false, the answer must mark affected claims unavailable or
  preliminary according to workflow policy.

## `POST /api/workflows/{workflow_id}/runs`

Starts a workflow run and streams safe events on the same HTTP response. This is
the preferred UI contract and mirrors OpenAI-style completion streaming.
`workflow_id` identifies the executable workflow resource in the path; the
request body contains run inputs only.

Request:

```json
{
  "market": "VN_STOCK",
  "symbol": "VCB"
}
```

Response: `200 OK` with `Content-Type: text/event-stream`

Validation errors:

- Unsupported market or asset: `422`
- Unsupported symbol for market: `422`
- Missing required input: `422`
- Unknown workflow: `404`
- Per-user, global, or sync-offload concurrency limit exceeded before stream
  start: `429`

Concurrency error response shape:

```json
{
  "error": {
    "code": "concurrency_limit_exceeded",
    "message": "Too many active workflow streams. Retry after a short delay.",
    "retry_after_seconds": 5
  }
}
```

Phase 02 limiter configuration:

- `FINMIND_STREAM_GLOBAL_LIMIT`
- `FINMIND_STREAM_PER_USER_LIMIT`
- `FINMIND_SYNC_OFFLOAD_LIMIT`

These limits are process-local semaphores in Phase 02. They do not coordinate
across multiple API workers or app instances until a Redis-backed limiter is
introduced later.
Provider/model-specific limit buckets are deferred until real usage or
multi-worker deployment requires them.

Rules:

- The endpoint executes the workflow in the request's async coroutine and yields
  stream frames as execution progresses.
- The endpoint is not a background queue and must not require a second
  subscription URL.
- The stream emits at least one `run.started` event before provider/model
  work where possible.
- `answer.delta` must come only from the final user-visible workflow step and
  must carry plain text chunks, not partial JSON fragments.
- Sync-only provider/model calls must not execute in the request handler.

## Chatflow APIs

Chatflow APIs are not owned by Phase 02. Production flexible Q&A behavior,
chatflow transport, chatflow persistence, and any `/api/chatflow/...` contract
belong to `../004-agentic-chatflow/`.

## Streaming Event Frames

Workflow streaming endpoints return ordered safe events using SSE.

Request headers:

- `Accept: text/event-stream`

Route semantics:

- Workflow runs use `POST /api/workflows/{workflow_id}/runs`; `workflow_id`
  stays in the path because it selects the executable workflow resource.
- Streaming is defined by `Accept: text/event-stream` and response
  `Content-Type: text/event-stream`, not by a `/stream` path suffix or request
  payload flag.

Event frame format:

```text
event: answer.delta
data: {"event_id":"evt_0005","run_id":"run_abc123","sequence":5,"kind":"answer.delta","created_at":"2026-06-27T00:00:01+00:00","payload":{"text":"Momentum remains"}}
```

Canonical event payload shape:

```json
{
  "event_id": "evt_0005",
  "run_id": "run_abc123",
  "sequence": 5,
  "kind": "answer.delta",
  "created_at": "2026-06-27T00:00:01+00:00",
  "payload": {
    "text": "Momentum remains"
  }
}
```

Required event kinds:

- `run.started`
- `run.stage`
- `answer.delta`
- `citation`
- `artifact`
- `run.completed`
- `run.failed`

Rules:

- Events are ordered by `sequence` within one run.
- Events must be safe for UI display and must not include raw reasoning, hidden
  prompts, provider secrets, raw provider payloads, or unsafe diagnostics.
- `run.stage` events feed the visible progress lane; `answer.delta` feeds the
  final answer lane; `run.completed` carries the persisted final run payload.
- Internal workflow steps such as collection or audit may produce `run.stage`
  progress only. Their intermediate output must not be emitted as
  `answer.delta` or persisted as user-facing final sections.
- `run.completed` is emitted only after final metadata reconciliation, so the
  answer stream can start before status/citation finalization is complete.
- Stream events are request-scoped and are not required to be replayable after
  disconnect.
- Disconnecting from the stream cancels request-scoped execution cooperatively
  where possible. Already-persisted final/partial output remains inspectable.
- Unknown or unauthorized workflow contexts return `404` or `403`; stream
  payloads must not leak whether another user's run exists.

## `GET /api/runs`

Returns workflow runs visible to the authenticated user for history and
result reinspection. Latest runs appear first.

## `GET /api/runs/{run_id}`

Returns a completed, partial, or failed workflow run. Unknown run ids return
`404`.

## `GET /api/runs/{run_id}/citations`

Returns persisted citation records for an authenticated run. The response is used
by citation inspection surfaces and must match the citation summaries embedded in
`GET /api/runs/{run_id}`.

Response shape:

```json
{
  "run_id": "run_abc123",
  "citations": [
    {
      "citation_id": "cite_1",
      "record_id": "data_price_summary_VN_STOCK_VCB_2026-06-18_v1",
      "record_type": "price_summary_record",
      "source_id": "vnstock_prices",
      "dataset_id": "vn_prices",
      "label": "Demo VN Prices",
      "timestamp": "2026-06-18T07:00:00+00:00",
      "cited_fields": ["payload.close", "payload.change_pct"],
      "payload_snapshot": {
        "close": 87200,
        "change_pct": 1.2,
        "volume": 1200000
      },
      "display_content": "- Close: 87,200\n- Daily change: +1.2%\n- Volume: 1,200,000",
      "methodology_version": "price-summary-v1"
    }
  ]
}
```

Rules:

- The caller must own the run.
- Unknown runs return not-found behavior.
- `display_content` is an optional rendered snippet for UI display; structured
  `payload_snapshot` remains the canonical cited snapshot.
- Citation rows must never expose raw provider payloads or hidden model
  reasoning.
- The endpoint must not depend on reconstructing citations from raw provider
  payloads, full intermediate runtime records, or hidden model prompts.
