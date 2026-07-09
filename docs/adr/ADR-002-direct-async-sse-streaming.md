---
id: ADR-002
status: accepted
date: 2026-07-04
deciders:
  - product-owner
  - engineering
related_specs:
  - specs/002-workflow/spec.md
  - specs/002-workflow/plan.md
  - specs/002-workflow/contracts/api-contract.md
related_risks:
  - docs/risks/RISK-004-async-stream-resource-saturation.md
---

# ADR-002: Direct Async SSE Streaming For Workflow And Chatflow

## Status

Accepted

## Context

Phase 02 needs workflow and chatflow responses to stream progressively to the UI,
similar to an OpenAI completion stream. The desired interaction is one async API
call that starts execution and returns stream frames on the same HTTP response.
The project is still on a development branch, so there is no compatibility
requirement to preserve a separate synchronous workflow run API.

## Decision

FinMind MUST use direct request-scoped SSE streaming for Phase 02 workflow and
chatflow execution:

- Workflow execution uses `POST /api/workflows/{workflow_id}/runs`.
- Chatflow execution appends a user message to a chat and streams the assistant
  response through `POST /api/chatflow/chats/{chat_id}/messages`.
- Each endpoint returns `200 OK` with `Content-Type: text/event-stream`.
- Streaming is expressed by the response contract and `Accept:
  text/event-stream`, not by a `/stream` path suffix or `stream=true` request
  field.
- `workflow_id` remains in the path because it identifies the executable
  workflow resource. The request body contains run inputs only. This applies to
  built-in workflows now and user-customized workflows later.
- `chat_id` remains in the path because it identifies the conversation resource.
  The request body contains the new user message and optional bounded market
  context only.
- The request coroutine executes the workflow or chatflow and yields safe events
  as stages, citations, artifacts, output deltas, final output, or failures are
  produced.
- Phase 02 model/provider adapters MUST support streaming through
  LangChain. The runtime does not expose a separate stream-mode policy
  field; unsupported streaming capability fails closed during configuration.
  `build_chat_model` selects `langchain-openai` `ChatOpenAI(streaming=True)`
  for OpenAI-compatible endpoints (`LITELLM_API_BASE` set) and
  `langchain-litellm` `ChatLiteLLM` for provider-routed model ids.
  `langchain-litellm` is not used for OpenAI-compatible endpoints because it
  buffers the streamed completion into a single chunk, defeating token
  streaming (verified via `scripts/diagnose_model_streaming.py`).
- Workflow and chatflow answer streaming MUST go through the deep agent's
  event-stream API (`agent.astream_events(..., version="v3")`), consuming the
  `messages` projection text deltas as `answer.delta`. Streaming MUST NOT call a
  raw chat model (`model.astream`) or a hand-rolled provider SSE client directly,
  so the run uses `create_deep_agent` (skill tool, middleware) for execution.
  Workflow execution is streaming-only; there is no separate synchronous run path. The v3 typed-projection API is chosen over
  `stream_mode="messages"` to keep `subagents`/`tool_calls` projections available
  for future `run.stage` progress once subagent delegation is introduced.
- The streaming path is not a background queue, does not return `202 Accepted`,
  and does not require a second subscription URL.
- Phase 02 chatflow may return deterministic mock output, but it must still use
  the same stream event contract and no-raw-reasoning rules.
- Final completed, partial, or failed output is persisted for history after the
  stream completes where possible.
- SSE is the transport only. Durable reconnect/replay semantics are separate and
  are not part of the request-scoped stream design.
- Async execution still requires bounded concurrency for total active streams,
  per-user active streams, and sync offload workers.
- Phase 02 MUST use process-local configurable semaphores for concurrency
  control. Redis or another distributed lease/counter backend is deferred until
  FinMind runs multiple API worker processes or multiple app instances.
- The initial limiter interface SHOULD support global stream, per-user stream,
  and sync-offload limits. Provider/model-specific buckets are deferred until
  real usage or multi-worker deployment requires them.

## Alternatives Considered

| Alternative | Reason Not Chosen |
|-------------|-------------------|
| `202 Accepted` plus `stream_url` | Adds a queue/subscription protocol that does not match the desired OpenAI-style single-call stream. |
| Keep a synchronous compatibility wrapper | Not needed on the development branch and would create a second execution contract to maintain. |
| `/stream` path suffix | Redundant when streaming is the only run behavior; the media type already defines the streaming response. |
| Put `workflow_id` in the payload | Works for a generic execution router, but makes the workflow resource less explicit for authorization, workflow-specific validation, route metrics, and audit logs. |
| `POST /api/chatflow/runs` for chat | Treats chat as a generic run instead of appending a message to a conversation resource, making chat ownership, history, and audit semantics less explicit. |
| WebSockets | Useful later for bidirectional collaboration or tool-control events, but unnecessary for current server-to-client answer streaming. |
| Final JSON only | Does not support progressive UI rendering or long-running workflow status. |
| Unlimited async streams | Async removes thread blocking but does not make provider quotas, model budgets, DB pools, memory, or file descriptors unlimited. |
| Redis-backed distributed limits immediately | Useful for multi-worker deployment, but premature for Phase 02 single-process development and local validation. |
| Raw `model.astream` / hand-rolled provider SSE client | Bypasses `create_deep_agent`, so the streamed run diverges from the non-streaming run (no `load_skill` tool, middleware, or subagent support) and depends on provider-specific chunk shapes. |

## Consequences

- UI code can consume workflow runs and chat replies with one streaming request.
- Backend implementation must expose async generator-style execution paths.
- Runtime, dataflow, model, repository, and provider boundaries must avoid
  blocking the event loop.
- Sync-only libraries must run through bounded offload with timeout and safe
  failure metadata.
- Concurrency limits are process-local in Phase 02. They do not coordinate
  across multiple `uvicorn` workers, containers, or hosts until a Redis-backed
  limiter is added.
- Stream events are transient request frames; final run output remains the
  durable history contract.
- Reconnect/replay requires a later explicit design if it becomes necessary.
- Before multi-worker deployment, the limiter backend must be revisited and moved
  to Redis or another shared lease/counter mechanism with TTLs for dead workers.

## Validation

- API tests assert `POST /api/workflows/{workflow_id}/runs` returns
  `text/event-stream` and emits `response_started`, stage, delta/final, and
  terminal events.
- API tests assert `POST /api/chatflow/chats/{chat_id}/messages` can append a
  user message and return deterministic mock output through the same event
  contract.
- Tests assert no streamed event exposes raw reasoning, hidden prompts, provider
  secrets, raw provider payloads, or unsafe diagnostics.
- Concurrency tests assert capacity exhaustion returns safe `429` before stream
  start.
- Tests cover process-local limiter behavior for global stream, per-user stream,
  and sync-offload capacity where practical.
- Event-loop tests or integration checks assert sync-only provider paths use
  bounded offload.

## References

- `specs/002-workflow/spec.md`
- `specs/002-workflow/plan.md`
- `specs/002-workflow/contracts/api-contract.md`
- `docs/risks/RISK-004-async-stream-resource-saturation.md`
