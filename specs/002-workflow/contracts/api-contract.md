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
  "market_scope": ["VN_STOCK", "US_STOCK"],
  "required_inputs": [
    { "name": "market", "type": "string", "required": true },
    { "name": "symbol", "type": "string", "required": true }
  ],
  "stages": [
    "collect_data",
    "data-audit",
    "fundamental-analysis",
    "technical-analysis",
    "news-digest",
    "risk-review"
  ],
  "requires_citations": true,
  "chart_requirements": ["price_series"],
  "output_sections": [
    "Data Quality",
    "Fundamentals",
    "Technical Analysis",
    "News Digest",
    "Risk Review"
  ]
}
```

Required catalog ids:

- `fundamental-analysis`
- `technical-analysis`
- `news-digest`
- `risk-review`
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
        "content": "Fundamental analysis on available statements; news-dependent claims blocked.",
        "citations": ["cite_1"],
        "warnings": ["news_missing"],
        "allowed_claims": ["financial_history"],
        "blocked_claims": ["recent_news_impact"]
      }
    ],
    "steps": [
      { "id": "collect_data", "kind": "collect_data", "status": "fallback", "warnings": [] },
      { "id": "vn-financial-data-auditor", "kind": "skill", "status": "success", "warnings": [] },
      { "id": "vn-fundamental-analysis", "kind": "skill", "status": "partial", "warnings": ["news_missing"] }
    ],
    "collection": {
      "status": "partial",
      "collection_id": "collection_abc123",
      "providers": ["vnstock", "offline_fallback"],
      "requested_dataset_groups": ["market_price", "fundamental", "news"],
      "provider_results": [
        {
          "provider_id": "vnstock",
          "dataset_groups": ["market_price", "fundamental"],
          "status": "success",
          "source_ids": ["vnstock_prices", "vnstock_fundamentals"],
          "warnings": []
        },
        {
          "provider_id": "offline_fallback",
          "dataset_groups": ["news"],
          "status": "fallback",
          "source_ids": ["offline_source_documents"],
          "warnings": ["news_provider_unavailable"]
        }
      ],
      "records_collected": 2,
      "documents_collected": 1,
      "warnings": ["source_documents_fallback"],
      "failure_reasons": [],
      "started_at": "2026-06-27T00:00:00+00:00",
      "completed_at": "2026-06-27T00:00:01+00:00"
    },
    "citations": [
      {
        "citation_id": "cite_1",
        "source_id": "vnstock_prices",
        "dataset_id": "vn_prices",
        "label": "Demo VN Prices",
        "timestamp": "2026-06-18T07:00:00+00:00"
      }
    ],
    "artifacts": {
      "chart": {
        "artifact_id": "artifact_1",
        "artifact_type": "chart",
        "title": "VCB Price Series",
        "inputs": ["vn_prices"],
        "payload": {
          "series": [{ "time": "2026-06-18", "value": 58200 }],
          "table": [
            {
              "record_key": "VCB-2026-06-18",
              "market_time": "2026-06-18T07:00:00+00:00",
              "close": 58200
            }
          ]
        },
        "source_refs": ["cite_1"]
      }
    },
    "grounding": {
      "grounding_status": "pass",
      "blocked_claims": ["recent_news_impact"],
      "uncited_claims": []
    }
  },
  "logs": [
    { "event": "workflow_started", "stage": "collect_data" },
    { "event": "workflow_completed", "status": "partial" }
  ]
}
```

Raw agent reasoning must never appear in responses.

Step and grounding contract:

- `steps` is the ordered `step_sequence` execution trace. Each step has `kind`
  `collect_data` or `skill`, a `status`, and `warnings`.
- `collect_data` step status is informational only (`success`, `partial`,
  `failed`, `fallback`); run status is derived from skill steps.
- Skill step `status` values: `success`, `partial`, `failed`. There is no
  pre-skill fail-fast: a skill runs on whatever `collect_data` returned and
  resolves which claims it can support, reporting `blocked_claims` for the rest.
  Run status is `failed` if any skill step failed, else `partial` if any skill
  step is `partial`, else `success`.
- `collect_data` is the only hard floor: zero records and zero source documents
  fails the run before any skill step.
- `grounding.grounding_status` is `pass` or `blocked`. It is `blocked` only when
  claims cite sources not present in the returned citations (`uncited_claims`).
- `grounding.blocked_claims` lists claim categories the skill reported blocked
  (surfaced for transparency).
- `grounding.uncited_claims` lists claims whose citations are not a subset of the
  returned citation ids (a grounding violation).
- Raw agent reasoning must never appear in `steps`, `sections`, or `grounding`.
- Material claims generated by a skill must pass FinMind validators for
  citations, market scope, and advice-only framing before appearing in
  `sections`. Data age is conveyed by citation `timestamp`; there is no separate
  freshness field.

Collection contract:

- `collection.status` values: `success`, `partial`, `failed`, `fallback`.
- `collection` is produced by `src/finmind_agents/dataflows/` after a
  FinMind-validated collection plan, not direct workflow or agent provider calls.
- `providers` may include provider ids such as `vnstock`, `alpha_vantage`,
  `sec_edgar`, and `offline_fallback`.
- `requested_dataset_groups` values are `market_price`, `fundamental`, and
  `news` for Phase 02.
- Requested dataset groups are derived from the referenced skills'
  `DATA_REQUIREMENTS.yaml` (raw-data skills only; upstream-dependent skills have
  none and are not added to the collect fetch list). Workflow YAML must not
  duplicate detailed dataset requirements.
- `provider_results` are safe status summaries. They must not include raw
  provider payloads.
- Provider API keys, credentials, raw responses, hidden prompts, and unsafe
  diagnostics must never appear in API responses.
- If live provider collection fails and fallback data is used, the response must
  preserve the fallback provider id and quality warnings so user-facing claims
  are caveated or marked unavailable.

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
    "message": "Too many active workflow or chatflow streams. Retry after a short delay.",
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

## `POST /api/chatflow/chats`

Creates a chat conversation owned by the authenticated user. Phase 02 may use a
minimal deterministic chat resource so the streaming message endpoint has clear
ownership and history semantics.

Request:

```json
{
  "title": "VCB research"
}
```

Response:

```json
{
  "chat_id": "chat_123",
  "title": "VCB research",
  "created_at": "2026-06-27T00:00:00+00:00"
}
```

## `GET /api/chatflow/chats/{chat_id}/messages`

Returns safe persisted messages visible to the authenticated user. Unknown or
unauthorized chats return `404` or `403`; raw reasoning is never returned.

## `POST /api/chatflow/chats/{chat_id}/messages`

Appends one user message to an existing chat and streams safe assistant
answer/status events on the same HTTP response. Phase 02 may return
deterministic mock chatflow output through this contract; production flexible
Q&A behavior remains governed by `../003-agentic-chatflow/`.

Request:

```json
{
  "message": "What changed for VCB fundamentals?",
  "market_context": { "market": "VN_STOCK", "symbol": "VCB" }
}
```

Response: `200 OK` with `Content-Type: text/event-stream`

Rules:

- Chatflow output must follow citation, unsupported-claim, advice-only, and
  no-raw-reasoning rules.
- Configured model/provider adapters must support streaming through
  LangChain/LiteLLM in Phase 02. Unsupported streaming capability fails closed
  during runtime configuration.
- Chatflow streams share the direct response event format with workflows but use
  a chatflow-specific runtime policy and output schema.
- Mock chatflow output in Phase 02 must still use the stream event contract and
  no-raw-reasoning rules.

## Streaming Event Frames

Workflow and chatflow streaming endpoints return ordered safe events using SSE.

Request headers:

- `Accept: text/event-stream`

Route semantics:

- Workflow runs use `POST /api/workflows/{workflow_id}/runs`; `workflow_id`
  stays in the path because it selects the executable workflow resource.
- Chatflow messages use `POST /api/chatflow/chats/{chat_id}/messages`;
  `chat_id` stays in the path because it selects the conversation resource.
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
- Unknown or unauthorized workflow/chatflow contexts return `404` or `403`; stream
  payloads must not leak whether another user's run exists.

## `GET /api/runs`

Returns workflow and chatflow runs visible to the authenticated user for history and
result reinspection. Latest runs appear first.

## `GET /api/runs/{run_id}`

Returns a completed, partial, or failed workflow/chatflow run. Unknown run ids return
`404`.
