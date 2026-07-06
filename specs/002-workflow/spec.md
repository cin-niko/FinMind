---
id: SPEC-FEAT-002
feature: workflow
status: draft
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

# Feature Specification: Workflow

## Summary

Define phase 02 fixed, system-defined financial trading support workflows for the
current market scope: VN stocks and US stocks only. The workflow suite uses
internal data collection and grounding steps, fetching the latest
available provider data before falling back to deterministic demo data in local
or offline test mode. It then exposes repeatable analysis paths such as
fundamental analysis, technical analysis, news digest, risk review, and combined
stock briefs. Workflows provide bounded analysis, validated inputs, evidence
objects, citations, chart artifacts, execution status, and result
reinspection from the UI.

This draft feature will own workflow execution and result inspection. It does not own the
overall app shell (`../001-mvp-ui/`). It owns the async execution and streaming
transport needed by workflows and chat, while production flexible Q&A behavior
remains governed by `../003-agentic-chatflow/`.

## User Scenarios & Testing

### User Story 1 - Run A Supported Stock Workflow From UI (Priority: P1)

An authenticated internal user selects a fixed workflow from the UI, chooses a
supported VN or US stock input, runs bounded analysis, and reviews cited results.

**Independent Test**: Log in, open `Workflows`, run one supported VN stock or US
stock workflow, and verify output sections, citations, chart artifacts, and
execution status.

Acceptance scenarios:

1. Given a configured VN or US stock provider can return current records, when
   the user submits valid workflow inputs, then the workflow completes with
   structured output using latest provider data and visible collection
   timestamps.
2. Given a workflow output includes a material claim, when the user inspects the
   result, then the claim has a citation or is marked unsupported/unavailable.
3. Given the workflow requires a chart, when it completes, then the result includes
   a chart artifact linked to the same data and evidence as the text output.

### User Story 2 - Choose A Workflow Type (Priority: P1)

An authenticated internal user can choose the appropriate trading-support workflow
for their research need, such as fundamental analysis, technical analysis, news
digest, risk review, or a combined stock brief.

**Independent Test**: Open the workflow catalog and verify that each supported
workflow type describes its purpose, required inputs, expected output sections,
evidence/citation expectations, and whether chart artifacts are expected.

Acceptance scenarios:

1. Given the user opens the workflow catalog, when supported workflows are listed,
   then each workflow has a clear title, purpose, supported market scope, required
   inputs, and expected result sections.
2. Given the user selects fundamental analysis, when the workflow runs, then the
   result emphasizes business quality, financial health, valuation signals, and
   relevant cited source material.
3. Given the user selects technical analysis, when the workflow runs, then the
   result emphasizes price trend, momentum, support/resistance, indicators, chart
   artifacts, and cited market records.
4. Given the user selects news digest, when trusted source material is available,
   then the result summarizes relevant recent items with citations (source id,
   timestamp, dataset id), sentiment/impact framing, and provenance; when source
   material is unavailable, the limitation is clearly marked.
5. Given the user selects risk review or combined stock brief, when the workflow
   runs, then the result combines relevant evidence sections without presenting an
   autonomous trading decision.

### User Story 3 - Compose A Stock Brief From Reusable Steps (Priority: P1)

An authenticated internal user can run a combined stock brief that orchestrates
reusable workflow steps instead of duplicating each analysis path.

**Independent Test**: Run `stock-brief` and verify it executes collection,
quality checks, fundamental analysis, technical analysis, news digest, and risk
review as visible stages, with partial/unavailable stages clearly marked.

Acceptance scenarios:

1. Given the user runs `stock-brief`, when the workflow starts, then it first
   collects required data before claim-generating analysis steps run.
2. Given the grounding check blocks a claim category, when downstream analysis
   runs, then affected claims include visible caveats or are marked unavailable.
3. Given a required dataset returned no records, when downstream analysis reaches
   that category, then the affected section is omitted or marked unavailable
   instead of fabricated.
4. Given one downstream step fails or is unavailable, when the composite workflow
   completes, then successful sections remain inspectable and the failed section
   shows a clear status.

### User Story 4 - Reject Unsupported Inputs (Priority: P1)

An authenticated internal user cannot accidentally run unsupported markets,
unsupported symbols, missing data, or unsafe workflow states.

**Independent Test**: Attempt to run workflows with gold, BTC, other assets,
unsupported symbols, missing inputs, and stale/missing data conditions.

Acceptance scenarios:

1. Given an unsupported market or asset is selected or submitted, when workflow
   validation runs, then execution is blocked or clearly marked unavailable.
2. Given required input is missing or invalid, when the user submits the workflow,
   then validation appears near the field and no fabricated result is created.
3. Given cited data is stale, missing, or failed, when a result is shown, then the
   condition is visible to the user.

### User Story 5 - Reopen Workflow Results (Priority: P2)

An authenticated internal user can reopen completed workflow runs from history and
inspect output, citations, artifacts, and execution status.

**Independent Test**: Complete a workflow run, refresh with the same valid session,
select the run from `History` -> `Workflow Runs`, and verify the result is restored.

Acceptance scenarios:

1. Given a workflow run completed, when the page reloads with a valid session, then
   the run remains visible under `Workflow Runs`.
2. Given a completed run is selected, when the result opens, then citations,
   artifacts, and execution status remain inspectable.
3. Given a run ID does not exist, when requested, then the system returns a
   not-found state rather than fabricating a result.

### User Story 6 - Run Workflows Asynchronously With Streaming (Priority: P1)

An authenticated internal user can call one async workflow API and receive an
OpenAI-style event stream on that same HTTP response while the server executes
collection, skill, grounding, citation, artifact, and answer generation. The
stream must serve two user needs at once: immediate visible execution progress
while long steps are still running, and incremental answer text once the final
LLM-backed response is being produced.

**Independent Test**: Submit a workflow through the streaming endpoint, consume
the response event stream directly, and verify `run.started`, `run.stage`,
`answer.delta`, `run.completed`, or `run.failed` events arrive in order while
the final result is persisted for history after the stream completes.

Acceptance scenarios:

1. Given a valid workflow request with streaming enabled, when the user submits
   it, then the server returns a `text/event-stream` response from the same
   request and begins executing the workflow in that request's async coroutine.
2. Given the workflow is executing, when collection, workflow stages, agent
   tool activity, or grounded progress summaries are produced, then the response
   stream emits safe ordered progress events immediately so the user does not
   wait on a blank screen.
3. Given the workflow enters the final answer-generation phase, when the model
   produces answer text, then the response stream emits ordered plain-text
   answer deltas before metadata finalization and before the final stored result
   is complete.
4. Given internal steps such as `collect_data` or `vn-financial-data-auditor`
   execute during the workflow, when they produce intermediate output, then that
   output is kept internal and surfaced only through safe progress events rather
   than user-facing answer deltas or persisted final sections.
5. Given the configured model adapter cannot provide streaming through
   LangChain/LiteLLM, when runtime configuration is validated, then workflow
   execution fails closed before presenting a degraded non-streaming answer.
6. Given a provider, model adapter, or legacy library is synchronous, when it is
   called from async execution, then it is isolated from the event loop through a
   bounded thread/process offload or replaced with an async adapter.
7. Given a workflow-backed assistant response is rendered in the UI, when the
   user scans the answer, then the assistant answer appears without a full white
   message card or repeated role header labels and the user's own prompt remains
   visually distinct.
8. Given workflow progress is still active, when the assistant response renders,
   then the execution-visibility summary shows `Working` and the step list is
   expanded by default.
9. Given workflow progress is complete, when the assistant response renders,
   then the execution-visibility summary shows `Completed N steps`, the step
   list is collapsed by default, and the user can expand it again.
10. Given workflow steps are shown to the user, when they read the list, then
    each step uses a product-facing label with optional input subtext rather
    than exposing internal step ids directly, and the completed list ends with
    `Done`.

### User Story 7 - Chatflow Asynchronously With Streaming (Priority: P2)

An authenticated internal user can send a chatflow message to the server, receive
a streaming progress/answer feed, and keep chatflow output bounded by the same
evidence, citation, safety, and no-raw-reasoning rules as workflows.

**Independent Test**: Submit a chatflow message through the async chatflow
endpoint, consume streamed answer/status events, and verify the persisted
chatflow run can be reopened without exposing raw reasoning. Phase 02 may satisfy
this with deterministic mock chatflow output.

Acceptance scenarios:

1. Given a chatflow message is submitted, when the backend accepts it, then it
   creates a chatflow run and streams safe progress/output events without
   blocking other authenticated users.
2. Given chatflow synthesis produces token or section deltas, when streaming is
   supported by the model adapter, then the UI renders those deltas in order and
   reconciles them with the final stored answer.
3. Given streaming is not supported by a configured adapter, when runtime
   configuration is validated, then chatflow execution fails closed before
   presenting a degraded non-streaming answer.
4. Given a chatflow answer includes material financial claims, when the answer is
   shown, then claims have citations or are marked unsupported/unavailable.

### User Story 8 - Inspect Artifacts And Citations In The Right Panel (Priority: P1)

An authenticated internal user can inspect generated workflow artifacts and cited
sources without losing their place in the transcript. Artifact cards open the
full artifact in the right panel, while inline citation chips open the complete
source list and jump to the selected citation.

**Independent Test**: Complete a workflow run that produces cited answer text and
a chart artifact, click the artifact card, verify the full chart viewer opens in
the right panel with download actions, then click an inline citation chip and
verify the right panel switches to the citation list and scrolls to the selected
source.

Acceptance scenarios:

1. Given a workflow answer includes artifact cards, when the user clicks a file
   or chart artifact card, then the right panel opens a full artifact viewer
   rather than a small preview.
2. Given a chart artifact supports multiple chart views, when the user opens it,
   then the user can switch between supported chart views such as line and
   candlestick without using a separate price table in the main answer.
3. Given an artifact supports download, when the user opens the artifact panel,
   then the user can download the original file or an exported chart format.
4. Given a workflow answer includes inline citation chips, when the user clicks a
   citation, then the right panel opens the complete citation/source list and
   scrolls to the clicked source.
5. Given a source is internal fetched data or an external link, when the citation
   is shown in the panel, then internal data is inspectable in the panel and
   external links are clearly available as outbound links.

## Functional Requirements

- **FR-001**: System MUST provide a workflow catalog of fixed system-defined
  trading-support workflows runnable from the UI.
- **FR-002**: Workflow catalog entries MUST declare supported market scope,
  required inputs, stages, role labels, output sections, citation expectations,
  and structured chart requirements.
- **FR-003**: Current workflow market scope MUST include VN stocks and US stocks
  only.
- **FR-004**: Workflow suite MUST include, at minimum, fundamental analysis,
  technical analysis, and news digest workflows for supported stocks.
- **FR-005**: Workflow suite SHOULD include risk review and combined stock brief
  workflows when their required evidence inputs are available.
- **FR-006**: Workflow suite MUST support reusable workflow steps so a composite
  workflow can run another workflow or internal step as one stage.
- **FR-007**: `data-collector` MUST be an internal step that gathers the latest
  available datasets required by the selected workflow, including market records,
  fundamentals, source documents or news, and peer data when available.
 - **FR-008**: `collect_data` MUST be a deterministic step that reads the raw
  `DATA_REQUIREMENTS.yaml` declared by the workflow's skill steps and collects
  canonical records before any skill step runs.
 - **FR-009**: A grounding check MUST run after each skill step, verifying that
  cited sources are a subset of sources returned by `collect_data` and blocking
  claim categories whose required dataset returned no records.
 - **FR-010**: `stock-brief` MUST be a composite workflow that runs
  `data-collector`, `fundamental-analysis`, `technical-analysis`,
  `news-digest`, and `risk-review` as ordered stages, with the grounding check
  auditing each skill step.
- **FR-011**: Gold, BTC, and other assets MUST NOT be enabled runnable workflow
  choices unless a later spec changes scope.
- **FR-012**: Workflow forms MUST render every required input and submit those
  values rather than defaulting to the first available record.
- **FR-013**: Workflow input validation MUST reject unsupported markets,
  unsupported symbols, missing inputs, and invalid values before successful
  execution.
- **FR-014**: System MUST maintain deterministic seeded/offline canonical records
  for VN and US stock examples with source identity, market time, collection
  time, and unique record keys for tests and provider-failure fallback.
- **FR-015**: News digest workflows MUST use trusted source material with source
  identity and publication or collection timestamps when available; if trusted
  source material is unavailable, the workflow MUST clearly mark the news section
  unavailable rather than fabricating digest content.
- **FR-016**: Fundamental analysis workflows MUST expose business quality,
  financial health, valuation, peer/industry context where available, and key
  risk sections when supporting evidence is available.
- **FR-017**: Technical analysis workflows MUST expose trend, momentum,
  support/resistance or equivalent price-level framing, chart artifacts, and
  cited market records when supporting evidence is available.
- **FR-018**: Risk review workflows MUST highlight material downside, data quality,
  market, bull/bear framing, and evidence limitations without issuing autonomous
  decisions.
 - **FR-019**: System MUST derive source-level citations from collected records,
  linking workflow claims to source identity, timestamps, and dataset ids.
 - **FR-020**: Workflow outputs MUST include grounding checks relevant to the
  market and evidence type, including inconsistent periods, split-adjusted price
  comparisons, changed share counts, and unavailable source fields when
  applicable. Cited sources must be a subset of collected sources.
- **FR-021**: Every user-facing material workflow claim MUST expose citations
  (source id, dataset id, timestamp) or be marked unsupported/unavailable.
- **FR-022**: System MUST generate chart artifacts for workflow outputs requiring
  visual price, indicator, or trend analysis. Workflow definitions MUST declare
  chart requirements as structured chart intents, and the runtime MUST resolve
  those intents through a deterministic chart registry rather than LLM-generated
  chart code. Phase 02 MUST support `price_trend`; additional chart ids MAY be
  added by extending the registry.
- **FR-023**: System MUST record execution runs for workflow submissions,
  generated artifacts, failures, partial results, and user-visible output status.
- **FR-024**: System MUST expose result views where users can inspect completed
  workflow outputs after the original run.
- **FR-025**: User-facing workflow outputs MUST NOT expose raw agent reasoning.
- **FR-026**: Workflow outputs MUST be framed as research support, not trading
  decisions, executable orders, or autonomous financial actions.
- **FR-027**: VN stock collection MUST use a provider adapter backed by `vnstock`
  for Phase 02 latest price and fundamental data where the library supports the
  requested symbol and dataset.
- **FR-028**: US stock collection MUST use provider adapters backed by a
  documented US market data source for prices/news and SEC EDGAR company facts
  for public-company fundamentals where available.
- **FR-029**: The system MUST provide a collection-first `dataflows` module that
  serves workflows now and future chatflow collection without implementing admin
  ingestion, scheduled backfill, or broad realtime data operations.
- **FR-030**: `dataflows` MUST expose a single collection boundary that accepts
  market, symbol, and required dataset groups, then returns canonical market
  records, source documents, provider statuses, collection timestamps, warnings,
  and failure reasons.
- **FR-031**: Workflow code MUST request data through `dataflows` and MUST NOT
  call concrete provider adapters directly.
- **FR-032**: Provider adapters MUST record `source_id`, provider timestamp or
  market timestamp, `collected_at`, dataset coverage, and any provider failure
  reason used by the grounding check.
- **FR-033**: Provider failures, missing API keys, rate limits, license
  restrictions, unavailable symbols, or stale latest data MUST produce a
  warning/partial/unavailable result instead of fabricated claims.
- **FR-034**: Workflow execution APIs MUST support request-scoped async
  streaming: one async HTTP call starts execution and returns a live event stream
  on the same response.
- **FR-035**: Workflow streams MUST expose two user-visible stream layers:
  immediate safe progress events during execution and incremental answer deltas
  during final response generation.
- **FR-036**: Workflow progress events MUST cover response start, workflow stage
  status, agent tool activity or equivalent execution-step visibility, warnings,
  citations, artifacts, completion, and failure states.
- **FR-037**: Workflow answer events MUST stream the final user-visible answer
  text incrementally when the model provider supports streaming, instead of
  waiting to emit the entire answer at once.
- **FR-038**: Streamed progress visibility MAY include normalized summaries of
  agent planning or intermediate work, but MUST NOT expose raw chain-of-thought,
  hidden prompts, provider secrets, raw provider payloads, or unsafe internal
  diagnostics.
- **FR-039**: Streamed workflow events MUST be ordered within the response and
  reconcilable with the persisted final run record after completion.
- **FR-040**: Chatflow submissions MUST use a separate direct async stream API
  from workflow submissions. The API MUST append a user message to a chat
  resource at `POST /api/chatflow/chats/{chat_id}/messages`, stream safe
  progress updates and incremental assistant answer text on the same HTTP
  response, and use a chatflow-specific runtime policy and answer schema. Phase
  02 MAY use deterministic mock chatflow output behind this stream contract.
- **FR-041**: Async API handlers MUST NOT directly call blocking provider,
  database, filesystem, or model operations. Any unavoidable synchronous library
  call MUST be isolated with bounded offload and timeout controls.
- **FR-042**: The system MUST enforce process-local global stream, per-user
  stream, and sync-offload concurrency limits for workflow and chatflow streams
  so one user or blocking sync path does not starve other users. Provider/model
  specific limit buckets are deferred until real usage or multi-worker
  deployment requires them.
- **FR-043**: Streamed responses MUST NOT expose raw agent reasoning, hidden
  prompts, provider secrets, raw provider payloads, or unsafe diagnostics.
- **FR-044**: Workflow-backed assistant responses shown in transcript-style UI
  surfaces MUST render the assistant answer body without a full enclosing white
  message card and MUST NOT repeat `You` or `FinMind` role header labels above
  each message.
- **FR-045**: Workflow execution visibility inside assistant responses MUST
  render as a compact collapsible metadata block above the answer body using the
  summary label `Working` while incomplete and `Completed N steps` when
  complete.
- **FR-046**: The workflow execution-visibility block MUST be expanded by
  default while incomplete, collapsed by default when complete, and
  user-expandable after completion.
- **FR-047**: User-visible workflow steps in transcript-style assistant
  responses MUST use product-facing labels instead of raw internal ids and MAY
  show input context such as the active symbol as lighter secondary subtext
  beneath the main step label.
- **FR-048**: Completed workflow execution-visibility lists in assistant
  responses MUST include a terminal `Done` row after the workflow steps.
- **FR-049**: Transcript-style workflow response presentation MUST keep status
  expansion, collapse, and answer rendering visually stable so the composer
  stays pinned and the latest user message remains aligned to the top of the
  transcript viewport while the answer unfolds below it.
- **FR-050**: Production workflow artifacts MUST use a parent `Artifact` contract
  with `artifact_type` as the top-level discriminator. Phase 02 supported
  artifact types are `file` and `chart`.
- **FR-051**: File artifacts MUST include a product-facing `file_type`, a
  technical `mime_type`, filename, downloadable file location, title, status,
  and linked source refs where applicable.
- **FR-052**: Chart artifacts MUST include a chart intent, title, status,
  renderable chart specification, supported chart views, default chart view,
  download options, and linked source refs. Chart artifacts MUST NOT require a
  price table to be visible in the main answer.
- **FR-053**: Artifact cards MUST appear after the relevant answer content and
  MUST open the full artifact viewer in the right-side panel on desktop or the
  equivalent full-screen artifact surface on mobile.
- **FR-054**: Chart artifact viewers MUST support switching among available
  chart views, including line and candlestick when both are supported by the
  artifact data.
- **FR-055**: Artifact download actions MUST be available from the artifact
  viewer for ready artifacts. File artifacts download the original file; chart
  artifacts download exported chart formats such as image or data export when
  provided.
- **FR-056**: Inline citations MUST render at the cited location in the answer as
  compact chips keyed by source/citation id. Clicking a citation chip MUST open
  the right-side citations panel containing the complete source list for the
  answer or run and jump to the selected source.
- **FR-057**: Citations MUST remain evidence/source references, not artifacts.
  The citations panel MUST show internal fetched data and external web links
  distinctly while preserving source identity, dataset id, and timestamp.

## Key Entities

- Market Instrument
- Canonical Market Data Record
- Workflow Specification
- Workflow Step
- Workflow Composition
- Execution Run
- Stream Event
- Grounding Check
- Citation
- Artifact
- File Artifact
- Chart Artifact
- Source Document
- Workflow Stream Display State
- Right Panel Display State

See `../system/state-model.md` for canonical entity definitions.

## Edge Cases

- Cited source not returned by collection: grounding is marked blocked and the
  claim is omitted or qualified.
- Data collection returns partial coverage: quality check marks unavailable
  coverage and downstream skill steps run on available data, reporting
  `blocked_claims` for unsupported categories.
- A workflow partially completes: completed sections, failed sections, and
  unavailable artifacts are distinguishable.
- Unsupported market or instrument request: execution is blocked or clearly marked
  before user reliance.
- Citation unavailable for a generated claim: claim is omitted, qualified, or
  marked unsupported.
- News source material unavailable for a requested digest: news digest section is
  marked unavailable with the reason.
- Technical chart data unavailable: chart artifact is marked unavailable and the
  text result avoids unsupported technical claims.
- Artifact unavailable or failed: the artifact card and panel show the status
  and reason, and unavailable artifacts do not expose broken download actions.
- Chart artifact lacks candlestick data: the chart viewer shows only supported
  views rather than a disabled or misleading candlestick switch.
- Citation chip references a source absent from the run source list: grounding is
  blocked and the chip is not rendered as a trusted citation.
- External citation link is unavailable or unsafe to open inline: the citation
  panel still shows source metadata and uses a clear outbound-link affordance
  instead of embedding unsafe content.
- Fundamental or valuation inputs are inconsistent across periods: the workflow
  marks the data-quality issue before presenting valuation or peer-comparison
  conclusions.
- Run ID does not exist: return not-found behavior.
- Stream client disconnects mid-run: the request-scoped execution is cancelled
  cooperatively where possible, and any completed partial/final result already
  persisted remains inspectable.
- Server restarts while streams are active: active request-scoped streams end;
  only completed/persisted run results are inspectable after restart.
- Streaming model support unavailable: fail closed before advertising answer
  streaming for that workflow or chatflow request.
- Long-running workflow step with no answer text yet: progress visibility still
  updates the user through safe stage/tool/progress events before answer deltas
  begin.
- Final answer generation starts late: progress stream remains active first, then
  answer deltas begin once the LLM-backed answer phase starts.
- Blocking provider/library call in async path: reject the implementation unless
  it uses a bounded offload wrapper, timeout, and safe failure status.
- Workflow step has no user-facing input context such as symbol or period:
  display only the main step label and omit empty subtext.
- Workflow execution has started but no visible steps are completed yet: keep
  the summary label as `Working` without exposing placeholder internal ids.

## Assumptions

- `../001-mvp-ui/` provides authenticated shell and navigation.
- Latest per-run provider collection is enough for Phase 02; historical
  warehouse ingestion, scheduling, and broad data operations require later
  bounded specs.
- Deterministic seeded/offline VN and US stock records remain necessary to
  validate workflow contracts without network or provider credentials.
- News digest can start from provider news where configured and trusted source
  documents or curated/open-source source material available to the project.
- Workflows provide advice support and evidence framing, not buy/sell decisions.
- `data-collector` is bounded to workflow-run needs and does not implement a
  broad native ingestion platform.
- Phase 02 may define and implement the separate direct async chatflow transport
  and server-side streaming contract, including deterministic mock chatflow
  output; production flexible Q&A behavior, broad dynamic research planning, and
  chat-specific product intelligence remain owned by `../003-agentic-chatflow/`.
- User-facing "reasoning" in Phase 02 means safe execution visibility such as
  workflow stages, tool activity summaries, and progress updates; it does not
  mean raw chain-of-thought or hidden internal reasoning.
- Artifact cards remain the entry point for generated outputs, but artifact
  details now use the shared right-panel viewer model. Citation chips use the
  same right panel in citation-list mode and remain distinct from artifacts.

## Success Criteria

- **SC-001**: A user can complete a supported VN stock workflow and inspect cited
  output, chart artifact, and execution status in under 5 minutes.
- **SC-002**: A user can complete a supported US stock workflow and inspect cited
  output, chart artifact, and execution status in under 5 minutes.
- **SC-003**: A user can choose fundamental analysis, technical analysis, and news
  digest workflows from the UI and understand each workflow's purpose before
  running it.
 - **SC-004**: A user can run `stock-brief` and see collection, grounding,
  fundamental, technical, news, and risk stages with clear completion, partial,
  failed, or unavailable status.
- **SC-005**: 100% of user-facing material workflow claims include at least one
  citation or are explicitly marked unsupported/unavailable.
- **SC-006**: At least 95% of supported workflow result views show a citation
  (source id, dataset id, timestamp) for every referenced dataset.
- **SC-007**: Users can identify missing, failed, or out-of-scope data
  conditions (via blocked_claims and unavailable sections) without reading logs.
- **SC-008**: Completed workflow runs remain visible under `History` ->
  `Workflow Runs` after refresh with a valid session.
- **SC-009**: 100% of workflow outputs avoid autonomous buy/sell/order language
  and keep final trading judgment with the user.
- **SC-010**: A streaming workflow request receives its first safe stream event
  in under 1 second in offline automated tests.
- **SC-011**: A workflow stream emits immediate progress visibility before final
  answer completion for 100% of completed, partial, or failed streamed runs.
- **SC-012**: At least 10 concurrent authenticated local test clients can hold
  workflow or chatflow streams without event-loop blocking from synchronous
  provider, database, or model calls.
- **SC-013**: For long-answer workflows and chatflow requests, streamed answer
  text begins before the final persisted result is emitted in at least 95% of
  successful streaming runs against supported streaming providers.
- **SC-014**: Chatflow streams never expose raw reasoning and reconcile streamed
  output with the persisted final chatflow run.
- **SC-015**: In transcript-style workflow responses, users can distinguish
  their prompt from the assistant answer and scan execution visibility without a
  full assistant message card or repeated role headers.
- **SC-016**: For 100% of completed workflow-backed assistant responses, the
  execution-visibility block auto-expands during active work, auto-collapses
  after completion, and remains re-openable by the user.
- **SC-017**: For 100% of ready workflow artifacts in supported runs, users can
  open the full artifact viewer from the artifact card and access at least one
  valid download action when a download is declared.
- **SC-018**: For 100% of rendered inline citation chips, clicking the chip opens
  the citations panel and positions the selected source within the visible
  source list.

## Out Of Scope

- App shell/login ownership.
- Production flexible Q&A agentic chatflow behavior beyond the separate direct
  async chatflow stream transport and deterministic Phase 02 mock output.
- Broad native realtime market data platform beyond per-run provider fetch.
- Broad native realtime news ingestion beyond provider/source documents required
  by one workflow run.
- Gold, BTC, crypto, commodities, options, futures, broker connectivity, trade
  execution, and autonomous financial actions.
