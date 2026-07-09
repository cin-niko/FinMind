---
id: SPEC-FEAT-002-PLAN
feature: workflow
status: active
owner: solo
created: 2026-06-26
implements: []
validated_by:
  - tests/test_app.py
  - tests/test_platform_services.py
  - src/finmind_ui/package.json
adr_refs:
  - docs/adr/ADR-001-hybrid-workflow-definitions-and-agent-skills.md
  - docs/adr/ADR-002-direct-async-sse-streaming.md
  - docs/adr/ADR-003-artifact-and-citation-inspection-contract.md
---

# Implementation Plan: Workflow

## Summary

Implement Phase 02 fixed, UI-runnable financial trading support workflows for VN
stocks and US stocks on top of a shared agent runtime that can later power
Phase 03 chatflow. Workflow and chatflow execution should be async-first on the
server so multiple authenticated users can run workflows or chatflow requests
concurrently without blocking API worker threads. The target repo split is `src/finmind_agents` for the agentic
and finance orchestration layer, `src/finmind_api` for the FastAPI delivery
layer, and `src/finmind_ui` for the frontend. The workflow contract remains
hybrid: YAML definitions declare inputs, skill refs, stages, output schemas,
runtime policy, and safety gates; Agent Skills own governed analyst procedure
and skill-level data requirements. The runtime, not the skill, owns the
deterministic data path described in `../system/data-record-flow.md`. The
skill reads those records and narrates from them; it does not decide what to
fetch or call providers directly. The MVP runtime should rely on LangChain
Deep Agents via `deepagents.create_deep_agent`, use `langchain-openai` for OpenAI-compatible endpoints (`LITELLM_API_BASE` set) and `langchain-litellm` for provider-routed models as the
default multi-provider model adapter, and defer LangGraph until workflow or
chatflow complexity actually requires graph state, checkpointing, or multi-agent
branching. Streaming uses a shared safe response-event format while keeping
workflow run and chat message APIs separate, so each request can return
stage/status/output events on the same HTTP response when the configured adapter
supports it. The first active workflow focus is the
VN financial data collector path, with broader workflow catalog and async
execution contracts retained for Phase 02. Transcript-style workflow responses
also need a lighter editorial assistant presentation: user prompts stay as
bubbles, workflow-backed assistant answers become frameless research-note
content, and safe execution visibility appears as a compact collapsible block
that is open while work is running and collapsed after completion.

## Technical Context

- Language/version: Python 3.12 backend, TypeScript React/Vite frontend.
- Backend dependencies: FastAPI, Pydantic, LangChain, Deep Agents
  (`deepagents`), `langchain-openai` for OpenAI-compatible endpoints and `langchain-litellm` for provider-routed models as the multi-provider model
  adapter, `httpx` as a runtime dependency for async provider clients,
  collection-first dataflow adapters, async run repositories, in-memory fallback
  repositories, pytest. LangGraph is intentionally deferred for the current MVP.
- Market-data providers: `vnstock` (4.x unified API) adapter for VN stock
  latest price and fundamentals, using the `vci` source (the legacy `kbs`
  endpoints reset connections); US provider adapter using Alpha Vantage for current/daily
  prices when an API key is configured; SEC EDGAR company facts
  adapter for public-company fundamentals; deterministic offline fallback for
  tests and provider outage paths.
- Frontend dependencies: React/Vite, existing app shell, existing workflow/result
  pages, existing chat transcript surface, Lightweight Charts.
- Storage: in-memory canonical record cache for Phase 02 provider results
  plus deterministic offline fallback records; completed workflow and chatflow runs
  persist to PostgreSQL via async `psycopg` support (one `runs` table,
  `kind` discriminator), bootstrapped with idempotent DDL. Reusable
  `price_series` base data and cited citation snapshots should be persisted in
  first-class tables while retaining run JSON citation metadata for
  backward-compatible result rendering. Intermediate derived records remain
  runtime objects by default and are recalculated from base data when needed.
  Development uses the `postgres` service in `docker-compose.yaml`; tests inject
  an async in-memory run repository via the `build_run_store` seam.
- Testing: `UV_CACHE_DIR=/private/tmp/finmind-uv-cache uv run --group dev python -m pytest`
  and `npm run build` in `src/finmind_ui`.
- Target platform: internal browser app backed by FastAPI JSON APIs.
- Performance goals: streamed workflow/chatflow requests emit the first safe event
  in under 1 second in offline automated tests. Supported offline workflow runs
  complete under 3 seconds in automated tests.
  Live provider collection should target a 15-second per-run timeout budget,
  with per-provider timeout/failure surfaced to the `collect_data` step. Agent
  skill execution should have a bounded iteration and timeout budget per
  workflow stage. Local concurrency tests should support at least 10
  authenticated workflow/chatflow streams without event-loop blocking.
  Phase 02 concurrency is process-local and configured through
  `FINMIND_STREAM_GLOBAL_LIMIT`, `FINMIND_STREAM_PER_USER_LIMIT`, and
  `FINMIND_SYNC_OFFLOAD_LIMIT`. Provider/model-specific limit buckets and
  Redis/distributed leases are deferred until real usage or multi-worker /
  multi-instance deployment requires them.
- Constraints: VN stocks and US stocks only; gold/BTC/other assets blocked or
  roadmap-marked; no broker/order/trade execution; no raw reasoning exposure;
  workflow skill execution requires an explicit LLM configuration and fails
  closed when unavailable; async handlers must not directly perform blocking
  provider, database, filesystem, or model work.
- Scale/scope: latest provider fetch for one requested symbol per run, small
  canonical in-memory cache/fallback datasets, authenticated multi-user internal
  workbench, request-scoped async streaming execution for MVP, and persisted
  final run state for result inspection.

## Constitution Check

- Code quality: keep the `src/finmind_agents` split explicit: runtime,
  workflows, skills, and dataflows remain separate; `src/finmind_api` stays a
  delivery layer and does not absorb finance workflow logic.
- Testing standards: add/adjust pytest coverage for catalog, VN/US runs,
  unsupported assets, composite `stock-brief`, data-quality gating, citations,
  chart artifacts, and run reinspection; run frontend build for UI contract
  compatibility.
- Safety guardrails: unsupported assets are blocked, data-quality warnings gate
  claims, material claims require citations or unavailable marking, raw reasoning
  is excluded, LLM/tool failures fail closed or produce partial/unavailable
  output, and outputs remain advice support only.
- UX consistency: workflow catalog, forms, run result, stage status, data-quality
  warnings, citations, artifacts, and transcript-style workflow response
  presentation follow
  `../system/ui-ux-guidelines.md`.
- Performance requirements: streamed requests must emit the first safe event
  quickly; offline workflow execution target is under 3 seconds in automated
  tests; live provider collection has a 15-second per-run timeout budget and
  must surface timeout/failure state through the `collect_data` step;
  stream/concurrency tests must guard against event-loop blocking from sync
  operations.
- Spec traceability: feature behavior lives in this folder; shared state,
  contracts, runtime/security, and UI rules remain in `../system/`.

Gate result: pass. No constitution violations require exception.

## Architecture

- `src/finmind_agents/runtime/`: own `FinMindAgentRuntime`, model bootstrap,
  `deepagents.create_deep_agent` orchestration, `langchain-openai`/`langchain-litellm` adapter selection (see `research.md`)
  wiring, tool registry, runtime policies, and the seam where LangGraph may be
  added later. Phase 02 runtime configuration requires a LangChain/LiteLLM
  adapter that supports streaming; runtime entrypoints should be async and expose
  safe stream events without leaking raw reasoning. For the MVP, Deep Agents plus
  normal Python guardrail code are sufficient; do not
  introduce LangGraph graph state until workflow/chatflow needs it.
- `src/finmind_agents/workflows/`: own workflow definitions, catalog loading,
  validation, collection orchestration, quality gates, executor logic, and run
  result assembly.
- `src/finmind_agents/skills/`: own skill loading and skill assets in
  `<skill-name>/SKILL.md` and `DATA_REQUIREMENTS.yaml`.
- `src/finmind_agents/dataflows/`: own provider selection, latest data fetch,
  normalization, fallback policy, provider status, and canonical collection
  results. It remains shared by workflows now and chatflow later. Provider
  adapters should be async where possible; unavoidable sync libraries such as
  `vnstock` must run through bounded offload wrappers with timeout/failure
  reporting so the event loop is not blocked.
- `src/finmind_agents/domain/`: own shared finance domain models and canonical
  workflow/dataflow entities.
- `src/finmind_agents/evidence/`: own deterministic data record builders,
  record rendering/templates, citation allowlist creation, data bundle
  packaging, and grounding helpers that operate before the LLM call.
- `src/finmind_api/`: own FastAPI app setup, auth, dependencies, routes,
  schemas, request-scoped SSE stream endpoints, async final-run persistence,
  evidence/citation persistence, and API-facing error mapping. It should call
  into `finmind_agents` and stay thin.
- `src/finmind_ui/`: own workflow forms, result views, app shell integration,
  transcript-style workflow response rendering, and API client bindings for
  workflow contracts.

## Workflow Execution Design

Atomic user-facing workflows:

- `fundamental-analysis`
- `technical-analysis`

Deterministic step:

- `collect_data`

The data audit is the `vn-financial-data-auditor` skill step; the post-skill
`GroundingCheck` audits cited sources and blocks claims missing required data.

Composite workflow:

```text
stock-brief
  -> collect_data
  -> vn-financial-data-auditor
  -> fundamental-analysis
  -> technical-analysis
```

Execution rules:

- Every workflow run starts with validation.
- A streamed workflow request validates input, creates a run context, returns a
  `text/event-stream` response, and executes collection/model work inside the
  request's async coroutine. There is no background queue for the streaming path.
- Streaming uses a shared safe event contract with `run.started`,
  `run.stage`, `answer.delta`, `citation`, `artifact`, `run.completed`, and
  `run.failed`. Workflow execution must fail closed if the configured runtime
  cannot produce streamed answer deltas through the adapter boundary.
- The final visible workflow step streams plain answer text through the deep
  agent's event-stream API (`agent.astream_events(..., version="v3")`), consuming
  the `messages` projection's per-LLM-call text deltas as `answer.delta`. This
  routes streaming through `create_deep_agent` (including its `load_skill` tool
  and middleware) instead of calling a raw chat model or a hand-rolled provider
  SSE client directly. Workflow execution is streaming-only; there is no separate
  synchronous run path. Structured
  workflow metadata is finalized after the streamed answer completes through a
  second async metadata pass. The stream must not depend on recovering answer
  text from partial JSON. The v3 typed-projection API is chosen over
  `stream_mode="messages"` so future subagent delegation (Phase 03 chatflow,
  composite workflows) can use the `subagents`/`tool_calls` projections for
  `run.stage` progress without changing the streaming contract.
- Workflow YAML is the executable product contract for inputs, markets, skill
  refs, stages, output sections, citations, chart requirements, runtime policy,
  and safety gates. It must not duplicate detailed skill data requirements.
- Markdown agent skills are governed analysis instructions and cannot bypass
  runtime validation, citation enforcement, or advice-only safety rules.
- Workflow mode is a constrained agent run: fixed skill selection from YAML,
  skill-owned data requirements, strict output schema, low iteration budget,
  dataflows-only tool access, no provider-direct access, and fail-closed
  behavior. The workflow runtime follows the product-wide data-record
  boundary in `../system/data-record-flow.md` before the LLM call; the skill
  consumes those records only.
- Future chatflow mode should reuse the same runtime with a flexible research
  policy: dynamic skill loading, dynamic data requirements, broader approved
  tool access, larger iteration budget, clarification/partial-answer behavior,
  and chat-specific answer schemas.
- Sub-agents may be used per data domain, such as VN market data, fundamentals,
  and technical data. Their outputs remain
  intermediate and must pass FinMind grounding/citation validators before being
  shown.
- Internal steps may contribute progress events and later validation context,
  but only the final user-visible workflow step may emit `answer.delta` events
  or persisted user-facing sections.
- Every claim-generating workflow runs `collect_data` then the data-audit skill
  before claim-generating synthesis, even if the UI selected an atomic workflow.
  `collect_data` is a deterministic, FinMind-validated collection through the
  dataflows tool boundary driven by each raw-data skill's `DATA_REQUIREMENTS.yaml`.
- After collection, the runtime must transform raw provider output into stable
  deterministic records before the LLM sees the context bundle, following
  `../system/data-record-flow.md`.
- Data packaging order is fixed:
  `collect_data -> normalize -> build data records -> render record context ->
  persist reusable base data -> assign/persist citations -> build data bundle -> LLM -> validate
  citations -> persist final output`.
- The first implementation keeps existing `CanonicalMarketDataRecord` as the
  normalized source layer and adds `DataRecord` as the compact model-visible
  layer. `price_series_record` is stored for charts/reuse and excluded from the
  default LLM bundle.
- Each `DataRecord` keeps structured fields as the canonical representation and
  exposes a deterministic rendered `context` projection for LLM input and
  human-readable display. The default implementation uses a class-owned template
  with cached rendering; subclasses may override `context` for custom logic.
- `fundamental_record` is the canonical audited financial record. Use
  `is_audited: boolean` as the audit gate; audit warnings, allowed claims, and
  blocked claims live inside the same record instead of a separate flags record.
- Technical-pattern calculation is also split into two deterministic record
  builders before the LLM call:
  - `pattern_evidence_record`: ports strict verdict detectors from
    `src/finmind_agents/workflows/skills/vn-technical-analysis/references/pattern_detection.md`
    and stores only patterns that have clear evidence or explicit
    `not_detected` verdicts.
  - `pattern_setup_record`: ports heuristic bullish setup scoring from
    `equity-research-vn/vn-technical-analysis/references/pattern_scoring.md`
    and stores ranked forming/near-confirmation setups with watch zones,
    confirmation price, and deterministic score/status.
- The agent runtime reads the skill before collection planning. Required data
  declared by the skill must be attempted; optional data may be attempted when
  allowed by policy and timeout budget.
- Agent-planned collection is only a request. FinMind validates market, symbol,
  dataset ids, required/optional status, fallback permission, and tool policy
  before executing the collection.
- SKILL.md may define how to interpret the deterministic records, cite them,
  and label unsupported claims, but it must not define a tool-driven dataflow
  path or request raw provider payloads.
- There is no pre-skill fail-fast. A skill step runs on whatever `collect_data`
  returned and resolves which claims it can support, reporting `blocked_claims`
  for categories it cannot ground. Run status is `failed` if any skill step
  failed, else `partial` if any skill step is `partial`, else `success`.

## Data Record And Citation Implementation Design

Deterministic packaging order:

```text
collect_data
  -> normalize canonical market records
  -> build stored price_series_record
  -> build llm-facing data records
  -> render record context
  -> assign and persist citation ids
  -> build data bundle
  -> LLM analysis
  -> grounding validation
  -> persist final answer and cited rows
```

Record builders in Phase 2A:

- `price_summary_record`: compact latest price action, change, volume context,
  and support/resistance summary.
- `indicator_record`: deterministic technical indicators computed from the
  stored price series.
- `pattern_evidence_record`: strict evidence verdicts from
  `pattern_detection.md`.
- `pattern_setup_record`: ranked heuristic setups from
  `pattern_scoring.md`.
- `company_profile_record`: compact issuer identity and sector/business facts.
- `fundamental_record`: audited financial metrics and warnings.
- `price_series_record`: stored separately for chart rendering and reuse, not
  included in normal LLM payloads.

Record rendering contract in Phase 2A:

- Each record type defines structured fields plus a deterministic `context`
  projection.
- The default `context` path is template-backed and suitable for both LLM input
  and UI display.
- Templates stay presentation-only; all calculation and validation logic
  remains in Python before rendering.
- Rendered `context` may be cached on the record instance during a run, so
  record instances should be treated as immutable after construction.

Pattern implementation boundary:

- `pattern_detection.md` is used when FinMind needs a direct yes/no verdict
  backed by explicit evidence. These outputs become
  `pattern_evidence_record.detected_patterns[]`.
- `pattern_scoring.md` is used when FinMind needs to summarize forming setups,
  ranked opportunities, watch zones, and confirmation distance. These outputs
  become `pattern_setup_record.setups[]`.
- The LLM receives the compact verdict/setup records, not the full candle
  series.

Phase 2A implementation scope for pattern logic:

1. Port the shared numeric helpers required by the reference logic into
   `src/finmind_agents/evidence/`.
2. Port strict detectors from `pattern_detection.md` for:
   double bottom/top, ascending/descending channel, candlestick patterns, and
   RSI divergence.
3. Port the 8 bullish heuristic setup detectors from `pattern_scoring.md`.
4. Port setup status mapping, reader-note generation, and pattern-family
   classification required by `pattern_setup_record`.
5. Keep archetype optional in Phase 2A. It may be stored in
   `pattern_setup_record` only if the required deterministic inputs are already
   available inside the same bounded implementation.

Runtime shape:

```text
DataflowService.collect(...)
  -> CanonicalMarketDataRecord[]
  -> PriceSeriesRepository.upsert(...)
  -> DataRecordBuilder.build(...)
  -> DataRecord.context render
  -> CitationBuilder.build_allowlist(...)
  -> CitationRepository.upsert_many(...)
  -> DataBundle
  -> FinMindAgentRuntime.run(data_bundle, citation_ids)
  -> GroundingCheck.validate(...)
```
- The post-skill `GroundingCheck` is `pass` or `blocked`. It is `blocked` only
  when claims cite ids outside the data bundle citation allowlist
  (`uncited_claims`); blocked claims are surfaced for transparency and affected
  sections are caveated. Data age is conveyed by citation `timestamp`; there is
  no separate freshness concept.
- Composite workflows preserve completed sections even when later stages are
  partial.

## Async Execution And Streaming Design

Transport:

- Use Server-Sent Events (SSE) for browser-facing run streams in Phase 02 because
  workflow/chatflow output is server-to-client and authenticated cookie sessions
  already exist. SSE is the transport only; durable reconnect/replay semantics
  are not part of the request-scoped stream design. WebSockets remain a later
  option if bidirectional collaboration or tool-control events are specified.
- Stream endpoint response type is `text/event-stream`. Events are JSON payloads
  with `event_id`, `run_id`, `kind`, `sequence`, `created_at`, and safe payload.
- Stream events are generated directly by the request-scoped async response
  generator. Final run state remains available through `GET /api/runs/{id}`
  after the stream completes or fails.
- Phase 02 stream events are intentionally generic enough for future chatflow
  reuse, but Phase 02 only implements workflow streaming.
- `answer.delta` events carry plain text chunks from the final visible step.
  Metadata such as final status, citations, blocked claims, and warnings is
  finalized after the answer stream completes and reconciled in
  `run.completed`.

Request-scoped stream runner:

- `src/finmind_api/streaming.py` owns safe SSE serialization, heartbeat events,
  client-disconnect handling, and process-local global/per-user stream
  semaphores.
  The semaphore backend is process-local in Phase 02 but should sit behind an
  internal limiter interface so Redis-backed leases can replace it later.
- The stream runner invokes async workflow/chatflow services directly and yields safe
  events as the runtime produces them. It does not enqueue a background job or
  require a second subscription endpoint.
- Heartbeats are emitted as SSE comment frames (`: heartbeat`) when the stream is
  idle so browsers and proxies keep the connection alive during long model phases
  (for example a reasoning model's pre-answer phase). The interval is configured via
  `FINMIND_STREAM_HEARTBEAT_SECONDS` (default 5s; `0` disables). A `run.stage`
  event with `status: running` is emitted when a visible skill step starts, before
  answer deltas, so the UI shows progress during answer generation.
- Client disconnect policy: cooperative cancellation is attempted for in-flight
  work; completed partial/final output already persisted remains inspectable.

Transcript-style workflow response rendering:

- Workflow-backed assistant responses in the chat/transcript surface use an
  editorial stream layout rather than a full white assistant message card.
- User prompts remain bubble-style and visually distinct; assistant responses do
  not repeat `You` or `FinMind` role headers.
- Safe execution visibility renders above the answer body as a compact
  disclosure block with the summary label `Working` while incomplete and
  `Completed N steps` once complete.
- The disclosure is expanded by default while work is running, collapses by
  default after completion, and remains user-expandable for later review.
- Visible step rows use product-facing action labels, optional input subtext
  such as symbol/period, connector lines, and bounded step-type icons. The list
  appends a terminal `Done` row once the run completes.

Artifact and citation inspection:

- Production artifacts use a parent `Artifact` contract with
  `artifact_type=file|chart`.
- `FileArtifact` represents a physical asset. It carries `file_type`,
  `mime_type`, filename, status, file location, downloads, and source refs when
  applicable.
- `ChartArtifact` represents structured chart output. It carries chart intent,
  supported views, default view, renderable chart spec, status, downloads, and
  source refs. Phase 02 chart viewers support line/candlestick switching when
  both views are present.
- Citation/source references are not artifacts. Inline citation chips open the
  right-side panel in citation-list mode and jump to the selected source.
- Artifact cards open the same right-side panel in artifact-viewer mode and show
  the full artifact. Chart artifacts do not need a price table in the main
  answer; raw data access uses declared downloads or a future file artifact.

Non-blocking boundaries:

- FastAPI routes, repository calls, dataflow collection, workflow execution, and
  chatflow execution should expose async methods.
- Use async database connections/cursors through `psycopg` async support.
- Use `httpx.AsyncClient` for HTTP providers.
- Any sync-only provider/model/library call must be wrapped in a bounded
  offload helper (`asyncio.to_thread`/AnyIO equivalent) with concurrency limits,
  timeout, cancellation handling, and safe provider failure metadata.

Chatflow streaming:

- Phase 02 owns a separate direct async chatflow message API and the runtime
  policy seam. `POST /api/chatflow/chats/{chat_id}/messages` appends a user
  message to an authenticated chat resource and streams the assistant response on
  the same HTTP response. Production flexible Q&A behavior remains in
  `../003-agentic-chatflow/`.
- Chatflow streams use the same direct SSE response event format as workflows,
  with `kind=chatflow` and a chatflow-specific policy/output schema.
- Phase 02 may return deterministic mock chatflow output through the stream
  contract.
- Chatflow answers must obey the same citation, advice-only, no-raw-reasoning,
  and unsupported-claim behavior as workflow output.

## Dataflows Collection Design

`src/finmind_agents/dataflows/` is a collection module, not an admin ingestion or
backfill platform. It serves Phase 02 workflows and is intentionally reusable by
the Phase 03 chatflow.

Module layout:

```text
src/finmind_agents/dataflows/
  __init__.py
  models.py
  service.py
  registry.py
  fallback.py
  normalizers.py
  providers/
    __init__.py
    base.py
    vnstock.py
    alpha_vantage.py
    sec_edgar.py
```

Responsibilities:

- `models.py`: collection requests, collection results, provider results,
  provider status, and dataset ids.
- `service.py`: one `DataflowService.collect(...)` entry point for workflows
  and future chatflow.
- `registry.py`: provider selection by market and dataset group.
- `fallback.py`: deterministic offline fallback policy and fallback labeling.
- `normalizers.py`: provider payload to canonical records/source documents.
- `providers/`: provider adapters only; no workflow or UI behavior.

Dataset groups:

- `market_price`: latest quote/history/volume for charts and technical analysis.
- `fundamental`: EPS, BVPS, revenue, profit, ratios, and company facts.
- Future groups may include `news`, `macro`, `peer`, `filings`, and `events`.

Execution boundary:

```text
finmind_api route
  -> workflow validation
  -> request-scoped SSE response generator starts workflow execution
  -> finmind_agents.workflows loads workflow YAML and allowed skill ref
  -> FinMindAgentRuntime loads SKILL.md and DATA_REQUIREMENTS.yaml
  -> Deep Agents runtime derives required/optional collection plan inside policy
  -> FinMind validates collection plan
  -> collect_dataflow tool calls DataflowService.collect(...)
  -> FinMind runs the data-audit / analysis skill steps on collected data
  -> Deep Agents runtime synthesizes governed draft output
  -> post-skill GroundingCheck (cited sources subset only; no pre-skill gate)
  -> grounding/citation/output validators
  -> finmind_api serializes result output
  -> SSE response emits status/stage/output/final events directly
```

Rules:

- Workflows and chatflow do not know provider internals.
- Workflows and chatflow share async runtime, dataflows, final-run persistence,
  and safe direct stream event format; they use separate API endpoints and differ
  by policy envelope and output schema.
- Provider raw responses, API keys, credentials, hidden prompts, and unsafe
  diagnostics never reach user-facing responses.
- Provider failure returns `partial`, `failed`, or `fallback`; it never fabricates
  successful evidence.
- Fallback records are labeled as fallback and remain distinguishable from live
  provider data.
- The LLM-facing bundle is intentionally smaller than the raw collection result;
  the runtime should chunk records for evidence use, not expose full provider
  dumps to the skill.

## Phase 0 Research Output

Resolved in `research.md`:

- Use composable fixed workflows before flexible chatflow.
- Use hybrid YAML workflow definitions and Markdown agent skills instead of
  one-off fixed-code workflows or unconstrained skill-only execution.
- Use one shared `FinMindAgentRuntime` for workflow now and chatflow later, with
  different policy envelopes.
- Use async-first execution and OpenAI-style SSE response streaming for workflow
  and chat transport, with bounded offload for unavoidable sync libraries.
- Treat Agent Skill `DATA_REQUIREMENTS.yaml` as the canonical source for detailed
  data needs; workflow YAML references skills and constrains runtime policy
  instead of duplicating collection requirements.
- Use Deep Agents (`deepagents.create_deep_agent`) for the shared workflow
  runtime core and `langchain-openai`/`langchain-litellm` adapter selection so multiple
  providers can run behind one LangChain-facing integration point.
- Defer LangGraph until the runtime truly needs graph state, checkpoints,
  multi-agent branching, or pause/resume orchestration.
- Spend implementation effort on dataflows, grounding, citations, validators,
  and synthesis prompts; do not rebuild planning/delegation primitives unless
  the framework proves too hard to control.
- Use latest real provider data for VN and US stocks, with deterministic
  seeded/offline fallback for tests and degraded provider paths.
- Keep data collection and quality checks internal but visible through status.
- Keep data packaging deterministic so the same raw inputs produce the same
  derived records, citation ids, and model-visible claims.
- Incorporate useful TradingAgents and equity-research-vn workflow ideas while
  rejecting autonomous trading/order execution and broad ingestion.

## Phase 1 Design Output

Generated/updated artifacts:

- `data-model.md`
- `contracts/api-contract.md`
- `quickstart.md`

## Post-Design Constitution Check

- Code ownership remains bounded by existing API/platform/UI layers.
- Test targets are explicit.
- Safety and human control are represented in validation, quality gates, and
  output contracts.
- UX surfaces reference the system UI/UX guidelines.
- Performance expectations are documented for offline execution and live
  provider collection.
- No unresolved clarifications remain.
