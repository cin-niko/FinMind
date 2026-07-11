---
id: SPEC-FEAT-002-RESEARCH
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

# Research: Workflow

## Decision: Use FileArtifact and ChartArtifact as production artifact children

Production workflow artifacts should use `artifact_type=file|chart`. Files cover
physical assets such as PDF, PPTX, DOCX, XLSX, CSV, PNG, JPG, and SVG through
`file_type` plus `mime_type`. Charts cover structured chart output through chart
intent, supported views, default view, renderable spec, downloads, and source
refs.

Rationale: Most generated outputs are physical files and should not become
separate top-level artifact categories. The current non-file output is charting,
which is specific enough to model directly instead of introducing a broad
`visualization` abstraction. `mime_type` remains necessary for browser,
download, storage, and security handling even when `file_type` drives product UI.

Alternatives considered: top-level `document`/`spreadsheet`/`image` categories,
a generic `visualization` type, or treating citation bundles as artifacts.
Rejected because they either over-expand taxonomy, abstract too early, or blur
generated outputs with evidence sources.

## Decision: Keep citation inspection separate from artifacts

Inline citations should render as compact chips at the cited answer location.
Clicking a chip opens the right-side panel in citation-list mode, shows all
sources for the answer/run, and jumps to the selected source. Internal fetched
data is inspectable in the panel; external web links are shown as outbound links.

Rationale: Citations prove claims; artifacts are generated outputs users can open
or download. Keeping them separate preserves grounding semantics and avoids
turning source inspection into another artifact card type.

Alternatives considered: citation bundle artifacts or separate citation drawer.
Rejected because the shared right panel already supports contextual inspection,
and citation bundles would duplicate the evidence model.

## Decision: VN stocks are Phase 02 workflow scope

VN stocks prove the Phase 02 equity research workflow surface while keeping US
stocks and other assets out of active scope. Gold dataflows and gold
workflows are deferred to `../003-vn-gold-dataflows-workflows/`.

Rationale: The product goal is agentic financial trading research advice, but data
access and safety scope must stay bounded. Two equity markets are enough for the
current workflow contract.

Alternatives considered: VN stocks plus gold or all markets.
Rejected for Phase 02 because the current foundation scope is VN stocks only.

## Decision: Use fixed workflow execution before flexible chatflow

Fixed workflows provide predictable, testable analysis paths and make evidence,
citations, chart artifacts, and run inspection easier to verify.

Alternatives considered: production flexible agentic Q&A first. Rejected because
trusted-source collection and chatflow safety need a separate bounded spec.

## Decision: Use one shared agent runtime

Workflow execution and future chatflow execution should converge on one
`FinMindAgentRuntime` abstraction. The runtime owns skill loading, policy
envelopes, tool registration, model adapter selection, structured output
validation, and safe execution metadata. Workflow mode uses a strict policy
envelope; chatflow mode can later use a broader research policy without
duplicating the skill/tool substrate.

Rationale: If workflows are agents that use skills, keeping a separate workflow
orchestrator and chatflow orchestrator would duplicate the hardest parts:
grounding, citations, dataflow tool access, model invocation, output validation,
and no-raw-reasoning guarantees. A shared runtime lets Phase 02 validate the
agent substrate on bounded workflow runs before Phase 04 adds flexible Q&A.

Alternatives considered: separate workflow and chatflow runtimes, a hard-coded
workflow-only runner, or an unguarded agent framework. Rejected because separate
runtimes drift, hard-coded runners are harder to reuse as future plugins, and an
unguarded framework would bypass FinMind authority boundaries.

## Decision: Use LangChain Deep Agents first and defer LangGraph

Phase 02 should rely on LangChain Deep Agents (`deepagents.create_deep_agent`)
for the bounded workflow agent core, with normal Python service/runtime code
retaining FinMind validation, collection approval, persistence, and output
guardrails. LangGraph should not be a direct MVP dependency yet; it should be
introduced only when workflow or chatflow needs explicit graph state,
checkpointing, human pause/resume, or multi-agent branching beyond what Deep
Agents provides.

Rationale: Deep Agents provides the planning/tool/subagent substrate already
aligned with LangChain while avoiding custom orchestration. The current workflow
path is still linear enough that direct LangGraph graph construction would add
framework overhead before it adds real value.

Alternatives considered: adopt LangGraph directly, use plain `create_agent`, or
build a custom graph runtime. Rejected because direct LangGraph and custom graph
code increase complexity early, while plain `create_agent` does not match the
agreed future chatflow/workflow agent substrate.

## Decision: `langchain-openai` for OpenAI-compatible endpoints, `langchain-litellm` for provider-routed models

The model adapter is selected by `build_chat_model` based on configuration:

- When `LITELLM_API_BASE` is set (OpenAI-compatible endpoint, e.g. an Azure
  OpenAI `/openai/v1` surface or an OpenAI proxy), use `langchain-openai`
  `ChatOpenAI` with `streaming=True`. `langchain-litellm` was found to buffer
  the streamed completion into a single chunk for these endpoints, which
  defeats token streaming; `ChatOpenAI` forwards per-SSE deltas.
- Without `LITELLM_API_BASE`, use `langchain-litellm` `ChatLiteLLM` for
  provider-routed model ids (e.g. `gemini/...`, `cohere/...`, `anthropic/...`).

Rationale: The MVP needs both model portability and real token streaming. The
diagnostic in `scripts/diagnose_model_streaming.py` showed the same
`gpt-5.4` Azure `/openai/v1` endpoint streaming 479 incremental chunks through
`ChatOpenAI` but a single 1827-char chunk through `ChatLiteLLM`. Streaming is a
product requirement (FR-035/FR-037), so the OpenAI-compatible path must use the
adapter that actually streams.

Alternatives considered: keep `langchain-litellm` as the single default.
Rejected because it does not stream token-by-token for the configured
OpenAI-compatible endpoint. Direct provider packages for every model family:
rejected because they multiply integration surface; `langchain-litellm` remains
the fallback for provider-routed ids.

## Decision: Prototype with Deep Agents orchestration instead of rebuilding it

Phase 02 should prototype directly with `deepagents.create_deep_agent`, wire
existing Agent Skills and dataflows collection as tools, and use sub-agents per
data domain only when they improve clarity. FinMind should spend engineering
effort on the grounding/citation layer, data-quality gates, safe output schemas,
and synthesis prompts rather than rebuilding generic planning and delegation.

Rationale: Deep Agents is enough for the current bounded workflow runtime and
keeps the substrate aligned with a future chatflow agent. It also lets the
project test whether framework planning and tool behavior is controllable enough
under FinMind policies before committing to direct LangGraph code or a custom
substrate.

Alternatives considered: implement a full orchestrator from scratch, add
LangGraph directly, use plain LangChain `create_agent`, or stay with a minimal
direct LLM call forever. Rejected for now because a scratch runtime would consume
effort on solved orchestration mechanics, direct LangGraph is early for the
current workflow complexity, plain `create_agent` is weaker than the agreed Deep
Agents direction, and a direct LLM call is not representative of the future
multi-skill chatflow.

## Decision: Keep FinMind guardrails outside the agent framework

Deep Agents, future direct LangGraph, `langchain-litellm`, or any provider-specific model
adapter is an execution substrate only. FinMind code remains responsible for market scope,
allowed tools, provider access through `dataflows`, citation enforcement,
citation provenance, no-trade/no-order safety, output schemas, persistence,
visible execution status, and audit-safe logs.

Rationale: Financial research output must be auditable and bounded even when the
model or agent framework changes. The framework can plan and delegate; FinMind
decides what data is available, which claims are allowed, and what can be shown.

Alternatives considered: letting the agent framework own validation and safety.
Rejected because model/framework behavior is too provider-dependent for product
contracts and safety invariants.

## Decision: Use policy envelopes for workflow and chatflow modes

The shared runtime should support at least two policy envelopes:

- Workflow policy: fixed YAML-selected skills, skill-owned data requirements,
  strict schema, low iteration budget, dataflows-only tools, fail-closed
  behavior, and completed/partial/failed run persistence.
- Chatflow policy: future dynamic skill loading, dynamic data requirements,
  broader approved tools, larger iteration budget, clarification or partial
  answer behavior, and chat-specific answer schemas.

Rationale: One runtime is useful only if it can preserve different UX and safety
semantics. Workflow users expect repeatability; chat users expect flexible
question answering. Policy envelopes keep those modes separate without
duplicating implementation.

Alternatives considered: one global agent policy. Rejected because workflow and
chatflow have materially different user expectations and failure behavior.

## Decision: Use async-first execution boundaries

Workflow and chatflow execution should expose async service methods from FastAPI
routes through repositories, dataflows, runtime orchestration, and model calls.
Async HTTP providers should use `httpx.AsyncClient`; PostgreSQL persistence
should use `psycopg` async support; runtime adapters should prefer async
`ainvoke` or streaming APIs when available.

Rationale: The product must support multiple authenticated users running
workflows and chatflow requests concurrently. A synchronous provider, database, or model call
inside an async request handler can block the event loop and delay unrelated
users.

Alternatives considered: keep sync routes and increase worker count, or use
sync internals under async routes without isolation. Rejected because worker
scaling hides but does not remove head-of-line blocking, and sync internals in
async routes would violate the multi-user requirement.

## Decision: Use SSE for Phase 02 run streaming

Phase 02 should use Server-Sent Events for workflow and chatflow streams. The
client makes one async `POST` request and the response itself is
`text/event-stream`, mirroring OpenAI-style completion streaming. Workflow runs
use `POST /api/workflows/{workflow_id}/runs`; chatflow appends a message to an
existing chat through `POST /api/chatflow/chats/{chat_id}/messages`. The response
emits safe JSON events: response start, stage status, warnings, citations,
artifacts, output deltas, final output, failure, and heartbeat events.

Rationale: Workflow/chatflow output is server-to-client for the current product
shape. SSE works well with browser clients, cookie-backed sessions, HTTP
infrastructure, and progressive answer rendering. SSE is only the transport;
durable reconnect or replay is a separate persistence feature and is not
required for the current request-scoped stream design. It is simpler than
WebSockets and avoids a background queue/subscription protocol for the current
request-response UX.

Alternatives considered: WebSockets, long polling, `/stream` path suffixes,
`POST /api/chatflow/runs`, and only returning the final JSON result. WebSockets
are useful later for bidirectional collaboration or tool control, but add
unnecessary protocol state now. Long polling is noisier and less natural for
answer deltas. A `/stream` suffix is redundant when streaming is the only run
behavior. A generic chatflow run endpoint is less explicit than appending a
message to a chat resource for ownership, history, and audit semantics.
Final-only JSON does not satisfy streaming UX.

## Decision: Persist final run output, not a background event queue

Workflow and chatflow streams should emit events directly from the request-scoped
async generator. The final completed/partial/failed run output is persisted for
history and result inspection after the stream closes. Stream events may be kept
in memory only for assembling the final response and tests unless a later spec
requires durable event replay.

Rationale: The target UX is an OpenAI-style completion stream: call one async API
and render events from that response. A queued run plus separate subscription URL
adds protocol complexity and does not match the desired interaction model.
Persisting final output preserves history without turning streaming into a job
queue.

Alternatives considered: background queue with `202 Accepted` and replayable
run events, or final-only JSON. The queue model was rejected because the user
expects direct completion streaming. Final-only JSON was rejected because it does
not support progressive UI rendering.

## Decision: Persist `price_series` base data and cited citation snapshots by default

Phase 02 should persist reusable `price_series` data, final run output, and the
citation snapshots actually cited by the LLM answer. Intermediate derived
records such as indicators, pattern setups, and price summaries should remain
runtime objects by default and be recalculated from the persisted base data when
needed.

Rationale: This keeps the data store lean while preserving the durable product
surfaces users need today: charting, run history, and citation inspection. It
avoids storing every intermediate deterministic record before there is a proven
audit/debug requirement for full snapshot persistence.

Alternatives considered: persist every derived record used by the LLM, or
persist only final answer text with no citation snapshot details. Rejected
because full derived-record persistence adds storage and repository complexity
too early, while answer-only persistence is too weak for citation inspection.

## Decision: Use structured record payload plus deterministic rendered `context`

Each deterministic record should keep structured fields as the canonical data
representation and expose a deterministic human-readable `context` rendering.
That `context` output may be reused for LLM input, citation snippet generation,
and UI display. The default path should use a class-owned template-backed
renderer, while subclasses may override rendering when they need custom logic.

Rationale: Structured fields remain testable, filterable, and stable as the
source of truth, while one deterministic rendered projection keeps LLM and UI
presentation aligned. This avoids coupling product meaning to markdown strings
alone and keeps content changes separate from calculation logic.

Alternatives considered: make markdown the canonical record representation, or
inline long templates directly in every record class. Rejected because markdown
as the source of truth weakens validation/reuse, and large inline templates make
schema classes harder to read and maintain.

## Decision: Bound concurrency even with async execution

Async-native FastAPI handlers and SSE streams can hold many idle or waiting
connections, but Phase 02 still needs explicit process-local global stream,
per-user stream, and sync-offload limits. These limits should return safe `429`
errors before stream start when capacity is exhausted. Provider/model-specific
limit buckets are deferred until real usage or multi-worker deployment requires
them.

Rationale: Async execution prevents a blocked thread from monopolizing the
server, but it does not make downstream resources unlimited. Provider APIs have
rate limits, model calls have latency/cost caps, PostgreSQL pools have finite
connections, CPU-bound work can starve the event loop, and sync-only libraries
must be isolated behind bounded thread/process offload.

Alternatives considered: allow unlimited async requests. Rejected because
unbounded streams can exhaust memory, file descriptors, provider quotas, model
budgets, DB pool slots, or offload workers, causing one user or workload to
degrade service for others.

## Decision: Isolate sync-only libraries with bounded offload

Any unavoidable synchronous dependency, such as a provider library that lacks
native async support, must run through a bounded offload wrapper with timeout,
concurrency limits, cancellation handling, and safe failure metadata. New
provider and model integrations should prefer native async APIs.

Rationale: Some useful finance libraries are synchronous, but calling them
directly from async execution would block the event loop. Bounded offload lets
Phase 02 keep current provider choices while making the blocking behavior
explicit, measurable, and testable.

Alternatives considered: ban sync libraries completely, or allow direct sync
calls in async routes. A total ban would discard useful provider adapters too
early. Direct sync calls would fail the multi-user performance requirement.

## Decision: Skill-owned data requirements drive collection planning

Detailed data requirements belong beside the Agent Skill in
`DATA_REQUIREMENTS.yaml`. Workflow YAML references the skill and constrains
runtime behavior; it does not duplicate detailed dataset requirements. During a
workflow run, the Deep Agents-backed runtime reads the skill and data
requirements, derives required and optional dataflow collection calls, and sends
those calls through FinMind's `collect_dataflow` tool. FinMind validates and
executes the calls; the agent never reaches provider clients directly.

Rationale: Duplicating requirements in workflow YAML and skill files creates two
sources of truth. It also makes future chatflow reuse ambiguous because chatflow
would load the skill but may not load the workflow. Keeping data needs with the
skill lets workflow and chatflow share one data contract while policy envelopes
explain why workflow output is strict/repeatable and chatflow output can be
question-specific.

Alternatives considered: workflow-owned data requirements, duplicated
workflow-and-skill requirements, or fully free agent collection. Workflow-owned
requirements make skills less reusable by chatflow. Duplicated requirements
drift. Fully free collection gives the agent too much authority over evidence in
a financial setting.

## Decision: Make workflows composable

Phase 02 workflows should be reusable steps that can be run alone or as part of a
larger composite workflow. `stock-brief` is the first composite workflow and runs
`collect_data`, `vn-financial-data-auditor`, `fundamental-analysis`,
and `technical-analysis` as ordered `step_sequence`.

Rationale: Composition avoids duplicating collection, quality checks, citations,
citation handling, and step status across each user-facing workflow. Standalone
news digest and risk review are intentionally deferred until deterministic
`news_record` or `risk_record` contracts exist.

Alternatives considered: independent monolithic workflow implementations.
Rejected because they make evidence, quality gating, partial failure, and future
workflow reuse harder to keep consistent.

## Decision: Use deterministic data records before LLM citation

Runtime should transform collected canonical records into deterministic evidence
records, assign citation ids to those records, persist reusable `price_series`
base data plus cited citation snapshots, and then send only the compact data
bundle plus citation allowlist to the LLM. The model may write narrative and
reference allowed citation ids, but it does not inspect full raw provider
payloads or invent citation ids.

Rationale: This makes the data path reproducible, limits prompt size, keeps raw
provider data out of model context, and gives the UI stable cited snapshots for
inspection without forcing durable storage of every intermediate record.
`fundamental_record.is_audited` is the simple boolean gate for confident
fundamental claims; audit warnings and blocked claims live in the same record
rather than a separate flags record.

Alternatives considered: direct citation from raw provider records, a separate
`fundamental_flags_record`, or LLM-selected tool/data flow. Direct raw citations
make prompt context too large and blur provenance. A separate flags record
duplicates the fundamental audit state. LLM-selected data flow weakens
determinism and conflicts with the workflow-first safety model.

## Decision: Use hybrid YAML workflow definitions and Markdown agent skills

Workflow structure should be machine-readable YAML, while per-analysis behavior
should live in governed Markdown agent skills. Fixed runtime code enforces
validation, citations, safety, and output contracts.

Rationale: YAML definitions keep workflows portable for UI/API tests and future
Claude or MCP-style integrations. Markdown skills keep analysis behavior readable
and easier to evolve without letting instructions replace runtime guardrails.

Alternatives considered: fixed code only, Markdown skills only, and YAML
definitions only. Rejected because each misses either portability, deterministic
validation, or analyst guidance.

## Decision: Keep data collection and grounding internal

`collect_data` is a deterministic internal step and the data audit is the
`vn-financial-data-auditor` skill step, not primary user-facing workflows in
Phase 02. Users see source coverage, citations (with timestamps), warnings, and
blocked claims when relevant. A post-skill `GroundingCheck` audits that cited
sources are a subset of collected sources; there is no pre-skill fail-fast.

Rationale: Users need trustworthy results, not operational noise. Internal
collection and grounding can protect claims while keeping the UI focused on
research output.

## Decision: Use an editorial stream presentation for workflow-backed assistant responses

Transcript-style workflow responses should keep user prompts as bubbles but
render workflow-backed assistant answers as frameless editorial content in the
chat stream. Safe execution visibility should appear as a compact collapsible
metadata block above the answer body, with the summary label `Working` while
the run is active and `Completed N steps` after completion. Completed step lists
end with `Done`, and product-facing step labels may show optional symbol/period
subtext on a lighter secondary line.

Rationale: The existing white assistant message card and raw-ish progress list
look closer to a debug panel than a finance research workbench. The editorial
stream pattern reduces chrome, saves vertical space, and makes the answer read
like a research note while preserving visible bounded execution state. Keeping
the disclosure open during active work gives immediate reassurance that the run
is progressing; auto-collapsing when complete reduces clutter once the answer is
available.

Alternatives considered: keep the existing full-card assistant message layout,
show progress in a permanently expanded debug-style accordion, or separate
progress into a side panel. Rejected because the full-card layout is visually
heavy, the always-open accordion competes with the answer body, and a side panel
breaks the transcript reading flow for chat-first use.

Alternatives considered: exposing the data audit as a standalone workflow.
Deferred until there is enough operational need for a diagnostics-focused view.

## Decision: Fetch latest provider data with deterministic fallback

Phase 02 should fetch latest available provider data for requested VN stock
symbols before workflow analysis runs. Deterministic seeded records remain
only for tests, local offline development, and explicit degraded fallback paths.

Rationale: User-facing workflows need current evidence to be useful as trading
research support. Keeping provider output normalized behind canonical records
preserves testability, citation enforcement, and future provider
replacement.

Alternatives considered: demo-only repositories. Rejected because demo-only data
cannot satisfy the phase 02 workflow goal once users run live stock research.

## Decision: Build `dataflows` as the shared collection layer

Provider collection should live in `src/finmind_agents/dataflows/`, not inside
workflow execution or the API layer. The module is collection-first for workflows
and future chatflow; it does not implement admin ingestion, scheduled backfill,
warehouse storage, or a broad realtime data platform in Phase 02.

Rationale: Workflows and chatflow both need current, evidence-ready finance data,
but neither should know provider APIs or fallback rules. A dedicated collection
boundary keeps provider selection, normalization, failure handling, and fallback
labeling in one place while preserving the existing workflow runtime as the
analysis/orchestration layer.

Alternatives considered: keep provider calls in `workflows/collector.py`, build a
full ingestion/backfill platform, or copy TradingAgents-style dataflows directly.
Provider calls inside workflows would couple analysis to source mechanics. A full
ingestion platform is beyond short-term scope. TradingAgents is useful as a
reference, but FinMind needs stricter canonical contracts, provider status,
fallback labeling, and no trading/autonomous action coupling.

## Decision: Use `vnstock` for VN market collection

The VN provider adapter should use `vnstock` for VN stock price and fundamental
collection where the requested symbol and dataset are supported. Critical VN
fundamental claims should keep source identity and period metadata so later
cross-checking against CafeF, exchange disclosures, or company/audited reports is
possible.

Rationale: The referenced `equity-research-vn` collector flow uses `vnstock` as
the primary VN collection path and treats source provenance/period quality as a
first-class workflow concern. This matches FinMind's VN stock scope and
citation-grounding design.

Alternatives considered: scraping individual VN websites first, manual CSVs, or
demo-only VN data. Rejected because they are less reusable, harder to normalize,
or not current enough for workflow output.

## Decision: US Market Collection Is Unsupported

Non-VN collection and provider adapters are outside the current product plan.
The active scope is VN stocks and gold; Phase 03 tasks retire US choices from
workflow validation, catalog, and active provider configuration.

## Source Review: TradingAgents

Source: https://github.com/tauricresearch/tradingagents

Useful ideas for Phase 02:

- Split workflow outputs into analyst-style sections: fundamentals, technical
  analysis, and clearly labeled unavailable categories when evidence is missing.
- Preserve a debate-like balance through bull/bear or upside/downside framing
  without implementing autonomous trading decisions.
- Keep a visible run/progress model so users can see which analysis stages are
  complete, partial, failed, or unavailable.

Rejected for Phase 02:

- Trader, portfolio manager, simulated exchange, order execution, and autonomous
  decision steps. FinMind must remain advice support only.

## Source Review: equity-research-vn

Source: https://github.com/Thanhtran-165/equity-research-vn

Useful ideas for Phase 02:

- Treat the workflow suite as a repeatable pipeline: data collection, fundamental
  analysis, valuation, technical analysis, and report/dashboard presentation.
- Include VN-specific data-quality checks such as split-adjusted price handling,
  changed share counts, stale ratio data, source period mismatches, and
  inconsistent EPS/BVPS bases.
- Include bull/bear framing, catalysts, and an independent view instead of a
  one-sided recommendation.
- Allow peer/industry comparison when peer data is available.

Rejected for Phase 02:

- Full HTML dashboard generation/deploy and broad provider-specific ingestion.
  Phase 02 should produce UI-runnable workflow results and artifacts inside
  FinMind, while broad ingestion, persistence, and dashboard publishing remain
  later specs.
