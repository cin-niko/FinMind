---
id: SPEC-FEAT-002-TASKS
feature: workflow
status: active
owner: solo
created: 2026-06-28
implements: []
validated_by: []
adr_refs:
  - docs/adr/ADR-001-hybrid-workflow-definitions-and-agent-skills.md
  - docs/adr/ADR-002-direct-async-sse-streaming.md
  - docs/adr/ADR-003-artifact-and-citation-inspection-contract.md
---

# Tasks: Workflow

**Input**: Design documents from `specs/002-workflow/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`,
`contracts/api-contract.md`, `quickstart.md`

**Tests**: Required for backend/API behavior, workflow runtime safety,
dataflows collection, and frontend contract changes per
`.specify/memory/constitution.md`.

**Organization**: Tasks are grouped by independently testable user story and
reflect the remaining work from the current codebase to the target
`src/finmind_agents` / `src/finmind_api` / `src/finmind_ui` architecture.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel after phase dependencies are complete.
- **[Story]**: User story label from `spec.md`.
- Every task includes an exact file path.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish the package layout and dependency surface for the
workflow runtime.

- [x] T001 Update workflow implementation dependencies for LangChain Deep Agents and `langchain-litellm` in `pyproject.toml`
- [x] T002 [P] Add target backend package roots in `src/finmind_agents/__init__.py` and `src/finmind_api/__init__.py`
- [x] T003 [P] Add target frontend package root notes in `src/finmind_ui/README.md`
- [x] T004 [P] Add target package migration notes and runtime env expectations in `specs/002-workflow/quickstart.md`
- [x] T005 Make `src/finmind_api/app.py` the canonical API entrypoint

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Create the shared runtime, dataflow, workflow, and API boundaries
that all workflow stories depend on.

**CRITICAL**: No user story work can begin until this phase is complete.

### Tests for Foundation

- [x] T006 [P] Add package migration import coverage for `finmind_agents` and `finmind_api` in `tests/test_platform_services.py`
- [x] T007 [P] Add runtime policy and fail-closed model configuration tests in `tests/test_platform_services.py`
- [x] T008 [P] Add API contract regression coverage for workflow agent metadata in `tests/test_app.py`

### Implementation for Foundation

- [x] T009 Create shared runtime models and policy types in `src/finmind_agents/runtime/models.py`
- [x] T010 [P] Create LiteLLM-backed model bootstrap and runtime settings loader in `src/finmind_agents/runtime/bootstrap.py`
- [x] T011 [P] Create runtime validators for citations, safety, and no-raw-reasoning rules in `src/finmind_agents/runtime/validators.py`
- [x] T012 [P] Create runtime tool registry for `collect_dataflow`, skill loading, and output validation in `src/finmind_agents/runtime/tools.py`
- [x] T013 Create `FinMindAgentRuntime` orchestration entrypoint in `src/finmind_agents/runtime/service.py`
- [x] T014 [P] Migrate canonical dataflow models and providers into `src/finmind_agents/dataflows/models.py` and `src/finmind_agents/dataflows/providers/base.py`
- [x] T015 [P] Migrate workflow definitions, skill loading, and validation into `src/finmind_agents/workflows/definitions.py`, `src/finmind_agents/workflows/skills.py`, and `src/finmind_agents/workflows/specs.py`
- [x] T016 Create thin API dependency wiring to the new packages in `src/finmind_api/dependencies.py` and `src/finmind_api/app.py`
- [x] T017 Remove the legacy `src/api` boundary and route backend imports through `finmind_agents` and `finmind_api`

**Checkpoint**: The target packages load, the runtime can be constructed, and
the current API surface can call through the new boundaries.

---

## Phase 2A: Data Records, Rendering, And Citation Persistence (Blocking Prerequisites)

**Purpose**: Replace direct collected-record prompting with deterministic
runtime `DataRecord` objects, template-backed `context` rendering, reusable
`price_series` persistence, citation allowlists, and persisted citation
snapshots before LLM analysis.

**CRITICAL**: New claim-generating workflow work must consume a compact data
bundle, not raw provider payloads or full price series.

### Tests for Data Records And Citations

- [ ] T018 [P] Add deterministic record id, payload, and `context` rendering tests for price summary, indicator, pattern evidence, pattern setup, company profile, and fundamental records in `tests/test_platform_services.py`
- [ ] T019 [P] Add regression tests for strict pattern evidence outputs ported from `src/finmind_agents/workflows/skills/vn-technical-analysis/references/pattern_detection.md` in `tests/test_platform_services.py`
- [ ] T020 [P] Add regression tests for heuristic setup ranking/status outputs ported from `equity-research-vn/vn-technical-analysis/references/pattern_scoring.md` in `tests/test_platform_services.py`
- [ ] T021 [P] Add citation allowlist, rendered citation snippet, and unknown-citation grounding tests in `tests/test_platform_services.py`
- [ ] T022 [P] Add audited fundamental gate tests for `fundamental_record.is_audited` in `tests/test_platform_services.py`
- [ ] T023 [P] Add API contract coverage for `GET /api/runs/{run_id}/citations` in `tests/test_app.py`
- [ ] T024 [P] Add regression coverage that full `price_series_record` and raw provider payloads are excluded from normal LLM payloads in `tests/test_platform_services.py`

### Implementation for Data Records And Citations

- [ ] T025 [P] Add shared `DataRecord`, `PriceSeriesRecord`, `DataBundle`, and citation snapshot models in `src/finmind_agents/models.py`
- [ ] T026 [P] Add record rendering helpers with template-backed default `context` generation in `src/finmind_agents/evidence/rendering.py`
- [ ] T027 [P] Add record rendering templates for price summary, indicators, pattern evidence, pattern setup, company profile, and fundamental context in `src/finmind_agents/templates/records/`
- [ ] T028 [P] Add deterministic data record builders for price summary, indicators, pattern evidence, pattern setup, company profile, fundamental records, and stored price series in `src/finmind_agents/evidence/builders.py`
- [ ] T029 [P] Port strict technical-pattern detectors from `src/finmind_agents/workflows/skills/vn-technical-analysis/references/pattern_detection.md` into `src/finmind_agents/evidence/patterns.py`
- [ ] T030 [P] Port heuristic setup scoring from `equity-research-vn/vn-technical-analysis/references/pattern_scoring.md` into `src/finmind_agents/evidence/patterns.py`
- [ ] T031 [P] Add citation allowlist generation and citation snapshot builders in `src/finmind_agents/evidence/citations.py`
- [ ] T032 Add data bundle packaging that uses rendered record `context` and excludes full price series from normal LLM context in `src/finmind_agents/evidence/bundles.py`
- [ ] T033 Add PostgreSQL and in-memory repositories for persisted `price_series` data and citation rows in `src/finmind_api/run_store.py`
- [ ] T034 Add workflow execution wiring to persist reusable `price_series`, build runtime `DataRecord` objects, and persist only cited citation snapshots before `FinMindAgentRuntime` calls in `src/finmind_agents/workflows/service.py`
- [ ] T035 Update agent request payload construction to pass `data_bundle` and citation ids instead of raw provider payloads in `src/finmind_agents/agents/prompts.py`
- [ ] T036 Update grounding validation to verify model citations against the data bundle citation allowlist in `src/finmind_agents/workflows/grounding.py`
- [ ] T037 Add `GET /api/runs/{run_id}/citations` route and response schema in `src/finmind_api/routes/runs.py` and `src/finmind_api/schemas.py`

**Checkpoint**: Workflow runs persist reusable `price_series` data and cited
citation snapshots before LLM analysis; model output can cite only the
allowlist; every record has deterministic `context`; citation inspection can
fetch persisted citation rows without hidden runtime state.

---

## Phase 3: User Story 1 - Run A Supported Stock Workflow From UI (Priority: P1)

**Goal**: An authenticated internal user runs one supported VN stock or US
stock workflow through the LangChain/LiteLLM-backed runtime and reviews
grounded results in the UI.

**Independent Test**: Log in, open `Workflows`, run one supported VN or US
stock workflow, and verify output sections, citations, chart artifacts, and
execution status.

### Tests for User Story 1

- [x] T038 [P] [US1] Add VN workflow runtime test for `technical-analysis` with agent metadata in `tests/test_platform_services.py`
- [x] T039 [P] [US1] Add US workflow runtime test for `technical-analysis` with provider/fallback metadata in `tests/test_platform_services.py`
- [x] T040 [P] [US1] Add fail-closed workflow run test when `FINMIND_AGENT_MODEL` is unset in `tests/test_platform_services.py`

### Implementation for User Story 1

- [x] T041 [P] [US1] Migrate workflow collection and quality services into `src/finmind_agents/workflows/collector.py` and `src/finmind_agents/workflows/quality.py`
- [x] T042 [US1] Implement runtime-driven workflow execution for atomic workflows in `src/finmind_agents/workflows/service.py`
- [x] T043 [US1] Implement the `collect_dataflow` runtime tool against shared dataflows in `src/finmind_agents/runtime/tools.py`
- [x] T044 [US1] Add workflow API routes that call the new runtime-backed service in `src/finmind_api/routes/workflows.py`
- [x] T045 [US1] Align backend schemas with workflow response envelopes in `src/finmind_api/schemas.py`
- [x] T046 [US1] Migrate workflow page request handling and response typing into `src/finmind_ui/src/api/client.ts` and `src/finmind_ui/src/features/workflows/WorkflowPage.tsx`
- [x] T047 [US1] Migrate result rendering for citations and chart artifacts into `src/finmind_ui/src/features/results/ResultView.tsx`

**Checkpoint**: User Story 1 is a working MVP on the new runtime boundary.

---

## Phase 4: User Story 2 - Choose A Workflow Type (Priority: P1)

**Goal**: An authenticated internal user can choose the right workflow and
understand its bounded behavior before execution.

**Independent Test**: Open the workflow catalog and verify each workflow shows
purpose, markets, required inputs, stages, expected sections, and
chart/citation expectations through the migrated UI.

### Tests for User Story 2

- [x] T048 [P] [US2] Add catalog metadata regression tests for the migrated workflow catalog in `tests/test_platform_services.py`
- [x] T049 [P] [US2] Add frontend catalog mapping coverage for the migrated UI client in `src/finmind_ui/src/features/workflows/workflowCatalog.test.ts`

### Implementation for User Story 2

- [x] T050 [P] [US2] Migrate workflow catalog loading and serialization into `src/finmind_agents/workflows/catalog.py`
- [x] T051 [US2] Add workflow catalog API route and serialization wiring in `src/finmind_api/routes/workflows.py`
- [x] T052 [US2] Migrate catalog display logic and provider-neutral workflow copy into `src/finmind_ui/src/features/workflows/workflowCatalog.ts` and `src/finmind_ui/src/features/workflows/WorkflowPage.tsx`
- [x] T053 [US2] Migrate workflow page styling for dense metadata display into `src/finmind_ui/src/styles.css`

**Checkpoint**: Workflow choice is independently testable through the migrated
catalog path.

---

## Phase 5: User Story 3 - Compose A Stock Brief From Reusable Steps (Priority: P1)

**Goal**: An authenticated internal user runs `stock-brief` as a reusable,
runtime-driven composite workflow with visible stages and guarded partial
behavior.

**Independent Test**: Run `stock-brief` and verify visible stages,
quality-gate behavior, partial/unavailable sections, and preserved completed
sections.

### Tests for User Story 3

- [ ] T054 [P] [US3] Add composite workflow runtime test for `stock-brief` success in `tests/test_platform_services.py`
- [ ] T055 [P] [US3] Add composite workflow partial-provider test for unsupported news/catalyst claim categories in `tests/test_platform_services.py`
- [ ] T056 [P] [US3] Add API response coverage for visible stage statuses and blocked claim categories in `tests/test_app.py`

### Implementation for User Story 3

- [ ] T057 [P] [US3] Migrate composite workflow definitions and skill refs into `src/finmind_agents/workflows/definitions.py` and `src/finmind_agents/skills/`
- [ ] T058 [US3] Implement composite sequencing and section assembly in `src/finmind_agents/workflows/executor.py`
- [ ] T059 [US3] Implement runtime policy handling for reusable internal steps in `src/finmind_agents/runtime/service.py`
- [ ] T060 [US3] Persist composite run output, stage status, and tool status via `src/finmind_api/run_store.py`
- [ ] T061 [US3] Render composite stage states and unavailable sections in `src/finmind_ui/src/features/results/ResultView.tsx`

**Checkpoint**: `stock-brief` works as a composed workflow without duplicating
collection or safety logic.

---

## Phase 6: User Story 4 - Reject Unsupported Inputs (Priority: P1)

**Goal**: An authenticated internal user cannot run unsupported markets,
unsupported symbols, undeclared collection plans, or unsafe workflow states.

**Independent Test**: Attempt unsupported assets, missing inputs, invalid
symbols, undeclared dataset collection, and missing model configuration.

### Tests for User Story 4

- [ ] T062 [P] [US4] Add unsupported market, symbol, and missing input validation coverage on the migrated API in `tests/test_app.py`
- [ ] T063 [P] [US4] Add collection-plan rejection tests for undeclared dataset requests in `tests/test_platform_services.py`
- [ ] T064 [P] [US4] Add no-fabrication assertions for failed quality or missing citations in `tests/test_platform_services.py`

### Implementation for User Story 4

- [ ] T065 [US4] Migrate workflow input validation and market scoping into `src/finmind_agents/workflows/validation.py`
- [ ] T066 [US4] Add collection-plan approval and rejection logic in `src/finmind_agents/dataflows/requirements.py`
- [ ] T067 [US4] Add API error mapping for validation, fail-closed runtime errors, and partial provider failures in `src/finmind_api/routes/workflows.py`
- [ ] T068 [US4] Migrate field-level validation and unsupported-state UI handling into `src/finmind_ui/src/features/workflows/WorkflowPage.tsx`

**Checkpoint**: Safety behavior is independently testable through both API and
UI.

---

## Phase 7: User Story 5 - Reopen Workflow Results (Priority: P2)

**Goal**: An authenticated internal user can reopen completed workflow runs
from history and inspect output, citations, artifacts, and execution status.

**Independent Test**: Complete a workflow run, refresh, reopen it from
history, and verify saved output, citations, and artifacts are restored.

### Tests for User Story 5

- [ ] T069 [P] [US5] Add run history API coverage for completed and partial workflow runs in `tests/test_app.py`
- [x] T070 [P] [US5] Add run reinspection persistence coverage for `collection` and `agent` envelopes in `tests/test_platform_services.py`
- [ ] T071 [P] [US5] Add citation reinspection coverage for persisted citation snapshot responses in `tests/test_app.py`

### Implementation for User Story 5

- [x] T072 [US5] Migrate run repository persistence into PostgreSQL via `PostgresRunRepository` in `src/finmind_api/run_store.py`, configured by `FINMIND_DATABASE_URL`
- [x] T073 [US5] Add run list and detail routes in `src/finmind_api/routes/runs.py`
- [ ] T074 [US5] Add citation reinspection query wiring in `src/finmind_api/run_store.py` and `src/finmind_api/routes/runs.py`
- [ ] T075 [US5] Migrate history selection and run reinspection flow into `src/finmind_ui/src/App.tsx` and `src/finmind_ui/src/features/shell/AppShell.tsx`

**Checkpoint**: Stored workflow runs remain inspectable after the architecture
migration.

---

## Phase 8: User Story 6 - Run Workflows Asynchronously With Streaming (Priority: P1)

**Goal**: An authenticated internal user can call one async workflow API and
receive safe SSE stream events on the same HTTP response, with separate
progress and final-answer lanes.

**Independent Test**: Submit `POST /api/workflows/{workflow_id}/runs`, consume
`text/event-stream` events from the same response, and verify first event
latency, ordered safe progress events, ordered `answer.delta` events, final
output reconciliation, and no event-loop blocking from sync dependencies.

### Tests for User Story 6

- [x] T076 [P] [US6] Add direct workflow SSE stream API tests in `tests/test_app.py` covering `run.started`, `run.stage`, `run.completed`, and terminal events
- [x] T077 [P] [US6] Add workflow stream completion persistence/reinspection coverage in `tests/test_app.py`
- [x] T078 [P] [US6] Add mandatory streaming-adapter validation and non-blocking sync-offload regression coverage for workflow providers or model calls in `tests/test_platform_services.py`
- [x] T079 [P] [US6] Add workflow process-local global and per-user stream limit coverage for safe `429` responses in `tests/test_app.py`
- [x] T080 [P] [US6] Add workflow progress-vs-answer event ordering coverage in `tests/test_app.py`
- [x] T081 [P] [US6] Add frontend stream client parsing coverage for `run.*` and `answer.delta` events in `src/finmind_ui/src/api/client.test.ts`

### Implementation for User Story 6

- [x] T082 [US6] Add shared safe stream event models in `src/finmind_agents/streaming/models.py`
- [x] T083 [US6] Update request-scoped SSE helpers, heartbeat handling, disconnect handling, and process-local concurrency semaphores in `src/finmind_api/streaming.py`
- [x] T084 [US6] Convert workflow service execution to expose async streaming events in `src/finmind_agents/workflows/service.py`
- [x] T085 [US6] Add `POST /api/workflows/{workflow_id}/runs` route in `src/finmind_api/routes/workflows.py`
- [x] T086 [US6] Refactor workflow runtime emission so visible working-step events and final answer text deltas are produced as separate event kinds in `src/finmind_agents/runtime/service.py` and `src/finmind_agents/workflows/service.py`
- [x] T087 [US6] Persist final completed, partial, or failed workflow stream output through `src/finmind_api/run_store.py`
- [x] T088 [US6] Add bounded sync-offload helpers for sync-only provider/model paths in `src/finmind_agents/runtime/offload.py`
- [x] T089 [US6] Update frontend API client to consume shared workflow stream events in `src/finmind_ui/src/api/client.ts`
- [x] T090 [US6] Render a collapsible `Working` / `Completed N steps` progress group from `run.stage` events in `src/finmind_ui/src/App.tsx` and `src/finmind_ui/src/features/chat/ChatPage.tsx`

**Checkpoint**: Workflow run endpoint works through direct request-scoped SSE
and the UI separates visible working steps from final answer text.

---

## Phase 9: User Story 7 - Chatflow Asynchronously With Streaming (Priority: P2)

**Goal**: An authenticated internal user can send a chatflow message, receive
safe streamed progress and answer deltas, and reopen the persisted result
without exposing raw reasoning. Phase 02 may satisfy this with deterministic
mock chatflow output.

**Independent Test**: Submit a chatflow message through the async chatflow
endpoint, consume streamed answer/status events, and verify the persisted
chatflow run can be reopened without exposing raw reasoning.

### Tests for User Story 7

- [ ] T091 [P] [US7] Add chatflow stream API coverage for `POST /api/chatflow/chats/{chat_id}/messages` in `tests/test_app.py`
- [ ] T092 [P] [US7] Add chatflow completion persistence and reinspection coverage in `tests/test_app.py`
- [ ] T093 [P] [US7] Add fail-closed chatflow streaming-adapter validation coverage in `tests/test_platform_services.py`
- [ ] T094 [P] [US7] Add frontend chatflow stream client reconciliation coverage in `src/finmind_ui/src/api/client.test.ts`

### Implementation for User Story 7

- [ ] T095 [US7] Add chatflow run and message service contracts in `src/finmind_agents/runtime/service.py` and `src/finmind_agents/streaming/models.py`
- [ ] T096 [US7] Add chatflow chat/message routes in `src/finmind_api/routes/chatflow.py`
- [ ] T097 [US7] Add persisted chatflow run and chat metadata support in `src/finmind_api/run_store.py`
- [ ] T098 [US7] Implement deterministic mock chatflow streaming output under workflow-aligned safety and citation rules in `src/finmind_agents/runtime/service.py`
- [ ] T099 [US7] Add frontend chatflow stream handling and persisted re-open support in `src/finmind_ui/src/api/client.ts` and `src/finmind_ui/src/features/chat/ChatPage.tsx`

**Checkpoint**: Chatflow stream contract exists and remains bounded by the same
evidence, citation, and safety rules as workflows.

---

## Phase 10: User Story 8 - Inspect Artifacts And Citations In The Right Panel (Priority: P1)

**Goal**: An authenticated internal user can click artifact cards to open full
file/chart viewers in the right panel, click inline citation chips to open the
complete source list and jump to the selected source, switch chart views when
available, and download ready artifacts.

**Independent Test**: Complete a cited workflow run with a chart artifact,
click the chart artifact card, verify the right-side panel opens the full chart
viewer with supported view switches and download actions, then click an inline
citation chip and verify the right-side panel switches to the complete citation
list and scrolls to the clicked source.

### Tests for User Story 8

- [x] T100 [P] [US8] Add backend artifact contract regression coverage for `artifact_type=file|chart`, `file_type`, `mime_type`, chart `spec`, downloads, status, and `source_refs` in `tests/test_platform_services.py`
- [x] T101 [P] [US8] Add API stream/run response coverage for `artifact` events and `run.completed` chart artifact payloads in `tests/test_app.py`
- [x] T102 [P] [US8] Add frontend API type/normalization tests for FileArtifact and ChartArtifact payloads in `src/finmind_ui/src/api/client.test.ts`
- [x] T103 [P] [US8] Add chart viewer tests for line/candlestick switching, hidden unsupported views, and no required price table rendering in `src/finmind_ui/src/features/charts/MarketChart.test.tsx`
- [x] T104 [P] [US8] Add right-panel interaction tests for artifact-card open and citation-chip jump behavior in `src/finmind_ui/src/features/chat/ChatPage.test.tsx`

### Implementation for User Story 8

- [x] T105 [US8] Update shared Artifact, FileArtifact, ChartArtifact, and download models in `src/finmind_agents/models.py`
- [x] T106 [US8] Update chart artifact construction to emit `artifact_type=chart`, `chart_intent`, chart `spec.supported_views`, `spec.default_view`, downloads, status, and unique artifact ids in `src/finmind_agents/artifacts.py`
- [x] T107 [US8] Update workflow service artifact and citation serialization for stream events and persisted runs in `src/finmind_agents/workflows/service.py`
- [x] T108 [US8] Update frontend artifact and citation contract types in `src/finmind_ui/src/api/client.ts`
- [x] T109 [US8] Replace legacy chart payload/table rendering with chart `spec` rendering and line/candlestick switching in `src/finmind_ui/src/features/charts/MarketChart.tsx`
- [x] T110 [US8] Add shared right-panel display state for artifact mode and citations mode in `src/finmind_ui/src/App.tsx`
- [x] T111 [US8] Render artifact cards after workflow answers and wire card clicks to artifact mode in `src/finmind_ui/src/features/chat/ChatPage.tsx`
- [x] T112 [US8] Render inline citation chips in workflow answers and wire chip clicks to citations mode with selected-source jump in `src/finmind_ui/src/features/chat/ChatPage.tsx`
- [x] T113 [US8] Add full artifact viewer and citation-list panel content in `src/finmind_ui/src/features/chat/ArtifactPanel.tsx`
- [x] T114 [US8] Remove main-answer price table affordances and route raw chart data access through declared downloads in `src/finmind_ui/src/features/charts/MarketChart.tsx`

**Checkpoint**: Artifact and citation inspection works from the transcript
without treating citations as artifacts or requiring chart price tables in the
main answer.

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Finish migration edges, documentation, traceability, and final
verification.

- [x] T115 [P] Update workflow implementation traceability in `specs/002-workflow/spec.md`
- [x] T116 [P] Update workflow plan traceability after package migration in `specs/002-workflow/plan.md`
- [x] T117 [P] Record runtime/package migration and direct async SSE decisions in `docs/adr/ADR-001-hybrid-workflow-definitions-and-agent-skills.md` and `docs/adr/ADR-002-direct-async-sse-streaming.md`
- [ ] T118 [P] Update workflow runtime, provider-risk, and async stream saturation mitigations in `docs/risks/RISK-001-workflow-skill-contract-drift.md`, `docs/risks/RISK-002-agent-skill-unsupported-claims.md`, and `docs/risks/RISK-004-async-stream-resource-saturation.md`
- [ ] T119 [P] Update validated environment configuration, stream limiter defaults, and deprecated env cleanup notes in `.env`
- [ ] T120 [P] Add a manual workflow runtime validation script for DXG using `.env` configuration in `test.py`
- [x] T121 Review migrated workflow UI against `specs/system/ui-ux-guidelines.md`
- [ ] T122 Review runtime safety guardrails against `.specify/memory/constitution.md`
- [ ] T123 [P] Regenerate implementation convergence notes after Phase 2A storage/rendering changes in `specs/002-workflow/plan.md` and `specs/002-workflow/quickstart.md`
- [x] T124 Run backend verification command `UV_CACHE_DIR=/private/tmp/finmind-uv-cache uv run --group dev python -m pytest tests/test_app.py tests/test_platform_services.py`
- [x] T125 Run frontend verification command `cd src/finmind_ui && npm run build`
- [ ] T126 Run the workflow quickstart validation scenarios in `specs/002-workflow/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Setup and blocks all user stories.
- **Data Records And Citations (Phase 2A)**: Depends on Foundational and
  blocks new claim-generating workflow work.
- **User Stories (Phases 3-10)**: Depend on Foundational completion; US1, US3,
  US5, US6, and US8 also depend materially on Phase 2A.
- **Polish (Phase 11)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **US1 Run A Supported Stock Workflow From UI (P1)**: Starts after Foundation
  and should be completed only after Phase 2A aligns model-visible context and
  citations.
- **US2 Choose A Workflow Type (P1)**: Starts after Foundation and can proceed
  in parallel with US1 once catalog loading exists.
- **US3 Compose A Stock Brief From Reusable Steps (P1)**: Depends on
  Foundation, benefits from US1 atomic execution, and consumes the Phase 2A
  evidence path.
- **US4 Reject Unsupported Inputs (P1)**: Starts after Foundation and can run
  in parallel with US1 because it targets validation and safety behavior.
- **US5 Reopen Workflow Results (P2)**: Depends on Foundation and at least one
  run-producing story, preferably US1 plus Phase 2A citation persistence.
- **US6 Run Workflows Asynchronously With Streaming (P1)**: Depends on
  Foundation and should land before UI workflows are considered complete,
  because stream endpoints are the canonical execution APIs.
- **US7 Chatflow Asynchronously With Streaming (P2)**: Depends on Foundation,
  the shared stream contract from US6, and the shared runtime policy envelope.
- **US8 Inspect Artifacts And Citations In The Right Panel (P1)**: Depends on
  US1 workflow output, US5 run reinspection persistence, and US6 stream event
  reconciliation.

### Within Each User Story

- Tests must be written and fail before implementation tasks in that story.
- Runtime/dataflow contracts must exist before workflow service wiring.
- Evidence/rendering builders must land before prompt assembly and citation
  persistence wiring.
- Workflow service wiring must land before API route integration.
- API integration must land before frontend result or form integration.
- Story checkpoints should pass before moving to the next priority story.

---

## Parallel Opportunities

- Setup tasks T002-T004 can run in parallel.
- Foundation tests T006-T008 can run in parallel.
- Foundation implementation tasks T010-T012 and T014-T015 can run in parallel.
- Phase 2A tests T018-T024 can run in parallel.
- Phase 2A implementation tasks T025-T031 can run in parallel before bundle
  and service wiring.
- US1 tests T038-T040 can run in parallel.
- US2 tests T048-T049 can run in parallel.
- US3 tests T054-T056 can run in parallel.
- US4 tests T062-T064 can run in parallel.
- US5 tests T069-T071 can run in parallel.
- US6 tests T076-T081 can run in parallel.
- US7 tests T091-T094 can run in parallel.
- US8 tests T100-T104 can run in parallel.
- Polish documentation tasks T118-T123 can run in parallel.

---

## Parallel Example: User Story 1

```bash
Task: "Add VN workflow runtime test for technical-analysis with agent metadata in tests/test_platform_services.py"
Task: "Add US workflow runtime test for technical-analysis with provider/fallback metadata in tests/test_platform_services.py"
Task: "Add fail-closed workflow run test when FINMIND_AGENT_MODEL is unset in tests/test_platform_services.py"
```

## Parallel Example: Phase 2A

```bash
Task: "Add deterministic record id, payload, and context rendering tests in tests/test_platform_services.py"
Task: "Add regression tests for strict pattern evidence outputs in tests/test_platform_services.py"
Task: "Add regression tests for heuristic setup ranking/status outputs in tests/test_platform_services.py"
Task: "Add citation allowlist, rendered citation snippet, and unknown-citation grounding tests in tests/test_platform_services.py"
```

## Parallel Example: User Story 8

```bash
Task: "Add backend artifact contract regression coverage in tests/test_platform_services.py"
Task: "Add frontend API type/normalization tests in src/finmind_ui/src/api/client.test.ts"
Task: "Add chart viewer tests in src/finmind_ui/src/features/charts/MarketChart.test.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 setup.
2. Complete Phase 2 foundation.
3. Complete Phase 2A data records, rendering, and citation persistence.
4. Complete Phase 3 User Story 1.
5. Validate with backend tests and the migrated workflow UI build.
6. Demo one VN or US workflow run with grounded output and safe citation
   inspection.

### Incremental Delivery

1. Land Phase 2A first so model-visible context, rendered record `context`, and
   citation persistence are deterministic.
2. Deliver US1 to prove the runtime, dataflows, API, and UI path.
3. Deliver US2 to complete workflow choice on the migrated UI.
4. Deliver US4 to lock down validation and collection-plan safety.
5. Deliver US3 to make `stock-brief` reusable and visible.
6. Deliver US6 to make stream transport the canonical execution path.
7. Deliver US5 to preserve run history and citation reinspection.
8. Deliver US8 right-panel artifact and citation inspection.
9. Deliver US7 bounded chatflow streaming if Phase 02 scope still includes the
   deterministic mock path.
10. Re-run relevant documentation, verification, and quickstart validation from
   Phase 11.

### Notes

- Keep workflow YAML as the executable contract and Markdown skills as governed
  analyst instructions.
- Keep detailed collection requirements in `DATA_REQUIREMENTS.yaml`, not in
  workflow YAML.
- Keep provider access behind `collect_dataflow`; agent skills must not call
  provider clients directly.
- Treat structured record fields as canonical and rendered `context` as a
  deterministic projection reused by LLM input and UI display.
- Do not add production flexible chatflow behavior, broker actions, gold, BTC,
  or autonomous financial actions in this feature.
