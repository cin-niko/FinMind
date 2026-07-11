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

- [x] T018 [P] Add deterministic record id, payload, and `context` rendering tests for price summary, indicator, pattern evidence, pattern setup, company profile, and fundamental records in `tests/test_platform_services.py`
- [x] T019 [P] Add regression tests for strict pattern evidence outputs ported from `src/finmind_agents/workflows/skills/vn-technical-analysis/references/pattern_detection.md` in `tests/test_platform_services.py`
- [x] T020 [P] Add regression tests for heuristic setup ranking/status outputs ported from `equity-research-vn/vn-technical-analysis/references/pattern_scoring.md` in `tests/test_platform_services.py`
- [x] T021 [P] Add citation allowlist, rendered citation snippet, and unknown-citation grounding tests in `tests/test_platform_services.py`
- [x] T022 [P] Add audited fundamental gate tests for `fundamental_record.is_audited` in `tests/test_platform_services.py`
- [x] T023 [P] Add API contract coverage for `GET /api/runs/{run_id}/citations` in `tests/test_app.py`
- [x] T024 [P] Add regression coverage that full `price_series_record` and raw provider payloads are excluded from normal LLM payloads in `tests/test_platform_services.py`

### Implementation for Data Records And Citations

- [x] T025 [P] Add shared `DataRecord`, `PriceSeriesRecord`, `DataBundle`, and citation snapshot models in `src/finmind_agents/models.py`
- [x] T026 [P] Add record rendering helpers with template-backed default `context` generation in `src/finmind_agents/evidence/rendering.py`
- [x] T027 [P] Add record rendering templates for price summary, indicators, pattern evidence, pattern setup, company profile, and fundamental context in `src/finmind_agents/templates/records/`
- [x] T028 [P] Add deterministic data record builders for price summary, indicators, pattern evidence, pattern setup, company profile, fundamental records, and stored price series in `src/finmind_agents/evidence/builders.py`
- [x] T029 [P] Port strict technical-pattern detectors from `src/finmind_agents/workflows/skills/vn-technical-analysis/references/pattern_detection.md` into `src/finmind_agents/evidence/patterns.py`
- [x] T030 [P] Port heuristic setup scoring from `equity-research-vn/vn-technical-analysis/references/pattern_scoring.md` into `src/finmind_agents/evidence/patterns.py`
- [x] T031 [P] Add citation allowlist generation and citation snapshot builders in `src/finmind_agents/evidence/citations.py`
- [x] T032 Add data bundle packaging that uses rendered record `context` and excludes full price series from normal LLM context in `src/finmind_agents/evidence/bundles.py`
- [x] T033 Add PostgreSQL and in-memory repositories for persisted `price_series` data and citation rows in `src/finmind_api/run_store.py`
- [x] T034 Add workflow execution wiring to persist reusable `price_series`, build runtime `DataRecord` objects, and persist only cited citation snapshots before `FinMindAgentRuntime` calls in `src/finmind_agents/workflows/service.py`
- [x] T035 Update agent request payload construction to pass `data_bundle` and citation ids instead of raw provider payloads in `src/finmind_agents/agents/prompts.py`
- [x] T036 Update grounding validation to verify model citations against the data bundle citation allowlist in `src/finmind_agents/workflows/grounding.py`
- [x] T037 Add `GET /api/runs/{run_id}/citations` route and response schema in `src/finmind_api/routes/runs.py` and `src/finmind_api/schemas.py`

**Checkpoint**: Workflow runs persist reusable `price_series` data and cited
citation snapshots before LLM analysis; model output can cite only the
allowlist; every record has deterministic `context`; citation inspection can
fetch persisted citation rows without hidden runtime state.

---

## Phase 3: User Story 1 - Run A Supported Stock Workflow From UI (Priority: P1)

**Goal**: An authenticated internal user runs one supported VN stock workflow
through the LangChain/LiteLLM-backed runtime and reviews
grounded results in the UI.

**Independent Test**: Log in, open `Workflows`, run one supported VN stock
workflow, and verify output sections, citations, chart artifacts, and
execution status.

### Tests for User Story 1

- [x] T038 [P] [US1] Add VN workflow runtime test for `technical-analysis` with agent metadata in `tests/test_platform_services.py`
- [x] T039 [P] [US1] Record legacy US workflow runtime coverage as superseded by Phase 03 T020-T021 in `../003-vn-gold-dataflows-workflows/tasks.md`
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

## Phase 5: Moved Scope - Phase 03 VN Stock Brief

**Goal**: Moved to `../003-vn-gold-dataflows-workflows/` as the Phase 03 VN
stock brief scope.

**Independent Test**: Run `stock-brief` and verify visible stages,
quality-gate behavior, partial/unavailable sections, and preserved completed
sections.

### Tests for User Story 3

- [x] T054 [P] [US3] Moved composite workflow success coverage to Phase 03 T014 in `../003-vn-gold-dataflows-workflows/tasks.md`
- [x] T055 [P] [US3] Moved composite partial-stage coverage to Phase 03 T014 in `../003-vn-gold-dataflows-workflows/tasks.md`
- [x] T056 [P] [US3] Moved stage-status and blocked-claim API coverage to Phase 03 T015 in `../003-vn-gold-dataflows-workflows/tasks.md`

### Implementation for User Story 3

- [x] T057 [P] [US3] Moved composite definitions and skills to Phase 03 T016 in `../003-vn-gold-dataflows-workflows/tasks.md`
- [x] T058 [US3] Moved composite sequencing and section assembly to Phase 03 T016 in `../003-vn-gold-dataflows-workflows/tasks.md`
- [x] T059 [US3] Moved reusable-step runtime policy to Phase 03 T016 in `../003-vn-gold-dataflows-workflows/tasks.md`
- [x] T060 [US3] Moved composite run persistence to Phase 03 T017 in `../003-vn-gold-dataflows-workflows/tasks.md`
- [x] T061 [US3] Moved composite UI stage rendering to Phase 03 T018 in `../003-vn-gold-dataflows-workflows/tasks.md`

**Checkpoint**: `stock-brief` works as a composed workflow without duplicating
collection or safety logic.

---

## Phase 6: Moved Scope - Phase 03 Market Validation

**Goal**: Moved to `../003-vn-gold-dataflows-workflows/` for VN stock and gold
market validation.

**Independent Test**: Attempt unsupported assets, missing inputs, invalid
symbols, undeclared dataset collection, and missing model configuration.

### Tests for User Story 4

- [x] T062 [P] [US4] Moved market and input API coverage to Phase 03 T019 in `../003-vn-gold-dataflows-workflows/tasks.md`
- [x] T063 [P] [US4] Moved undeclared dataset rejection coverage to Phase 03 T005 and T008 in `../003-vn-gold-dataflows-workflows/tasks.md`
- [x] T064 [P] [US4] Moved no-fabrication safety coverage to Phase 03 T005 in `../003-vn-gold-dataflows-workflows/tasks.md`

### Implementation for User Story 4

- [x] T065 [US4] Moved workflow input validation and market scoping to Phase 03 T020 in `../003-vn-gold-dataflows-workflows/tasks.md`
- [x] T066 [US4] Moved collection-plan approval and rejection to Phase 03 T008 in `../003-vn-gold-dataflows-workflows/tasks.md`
- [x] T067 [US4] Moved validation and partial-provider API errors to Phase 03 T021 in `../003-vn-gold-dataflows-workflows/tasks.md`
- [x] T068 [US4] Moved field-level validation UI to Phase 03 T022 in `../003-vn-gold-dataflows-workflows/tasks.md`

**Checkpoint**: Safety behavior is independently testable through both API and
UI.

---

## Phase 7: Moved Scope - Phase 03 Run Reinspection

**Goal**: Remaining reinspection behavior moved to
`../003-vn-gold-dataflows-workflows/` for VN stock and gold runs.

**Independent Test**: Complete a workflow run, refresh, reopen it from
history, and verify saved output, citations, and artifacts are restored.

### Tests for User Story 5

- [x] T069 [P] [US5] Moved run-history API coverage to Phase 03 T023 in `../003-vn-gold-dataflows-workflows/tasks.md`
- [x] T070 [P] [US5] Add run reinspection persistence coverage for `collection` and `agent` envelopes in `tests/test_platform_services.py`
- [x] T071 [P] [US5] Moved citation reinspection API coverage to Phase 03 T023 in `../003-vn-gold-dataflows-workflows/tasks.md`

### Implementation for User Story 5

- [x] T072 [US5] Migrate run repository persistence into PostgreSQL via `PostgresRunRepository` in `src/finmind_api/run_store.py`, configured by `FINMIND_DATABASE_URL`
- [x] T073 [US5] Add run list and detail routes in `src/finmind_api/routes/runs.py`
- [x] T074 [US5] Moved citation reinspection queries to Phase 03 T024 in `../003-vn-gold-dataflows-workflows/tasks.md`
- [x] T075 [US5] Moved history selection and reinspection UI to Phase 03 T025 in `../003-vn-gold-dataflows-workflows/tasks.md`

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

## Phase 9: Moved Scope - Chatflow Asynchronously With Streaming

**Goal**: Moved to `../004-agentic-chatflow/`. Phase 02 no longer owns chatflow
transport, chatflow persistence, or deterministic mock chatflow output.

**Independent Test**: Verify Phase 02 exposes no runnable `/api/chatflow/...`
contract and that Phase 04 owns production chatflow specification work.

### Tests for User Story 7

- [x] T091 [P] [US7] Move chatflow stream API coverage to `../004-agentic-chatflow/tasks.md`
- [x] T092 [P] [US7] Move chatflow completion persistence and reinspection coverage to `../004-agentic-chatflow/tasks.md`
- [x] T093 [P] [US7] Move fail-closed chatflow streaming-adapter validation coverage to `../004-agentic-chatflow/tasks.md`
- [x] T094 [P] [US7] Move frontend chatflow stream client reconciliation coverage to `../004-agentic-chatflow/tasks.md`

### Implementation for User Story 7

- [x] T095 [US7] Move chatflow run and message service contracts to `../004-agentic-chatflow/tasks.md`
- [x] T096 [US7] Move chatflow chat/message routes to `../004-agentic-chatflow/tasks.md`
- [x] T097 [US7] Move persisted chatflow run and chat metadata support to `../004-agentic-chatflow/tasks.md`
- [x] T098 [US7] Move deterministic mock chatflow streaming output to `../004-agentic-chatflow/tasks.md`
- [x] T099 [US7] Move frontend chatflow stream handling and persisted re-open support to `../004-agentic-chatflow/tasks.md`

**Checkpoint**: Chatflow work is no longer part of Phase 02 and remains traceable
in Phase 04.

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
- [x] T118 [P] Moved workflow risk mitigation updates to Phase 03 T026 in `../003-vn-gold-dataflows-workflows/tasks.md`
- [x] T119 [P] Moved Phase 03 environment configuration updates to Phase 03 T027 in `../003-vn-gold-dataflows-workflows/tasks.md`
- [x] T120 [P] Moved manual VN/gold workflow validation to Phase 03 T027 in `../003-vn-gold-dataflows-workflows/tasks.md`
- [x] T121 Review migrated workflow UI against `specs/system/ui-ux-guidelines.md`
- [x] T122 Moved runtime safety review to Phase 03 T028 in `../003-vn-gold-dataflows-workflows/tasks.md`
- [x] T123 [P] Moved convergence and quickstart validation notes to Phase 03 T029 in `../003-vn-gold-dataflows-workflows/tasks.md`
- [x] T124 Run backend verification command `UV_CACHE_DIR=/private/tmp/finmind-uv-cache uv run --group dev python -m pytest tests/test_app.py tests/test_platform_services.py`
- [x] T125 Run frontend verification command `cd src/finmind_ui && npm run build`
- [x] T126 Moved VN/gold workflow quickstart validation to Phase 03 T031 in `../003-vn-gold-dataflows-workflows/tasks.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Setup and blocks all user stories.
- **Data Records And Citations (Phase 2A)**: Depends on Foundational and
  blocks new claim-generating workflow work.
- **Completed Phase 02 User Stories (Phases 3-10)**: Depend on Foundational
  completion; Phase 03 owns the moved workflow-maturity work recorded above.
- **Polish (Phase 11)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **US1 Run A Supported Stock Workflow From UI (P1)**: Starts after Foundation
  and should be completed only after Phase 2A aligns model-visible context and
  citations.
- **US2 Choose A Workflow Type (P1)**: Starts after Foundation and can proceed
  in parallel with US1 once catalog loading exists.
- **Moved Phase 03 Workflow Maturity**: Composite VN workflows, active-market
  validation, and run reinspection are planned in
  `../003-vn-gold-dataflows-workflows/tasks.md`.
- **US6 Run Workflows Asynchronously With Streaming (P1)**: Depends on
  Foundation and should land before UI workflows are considered complete,
  because stream endpoints are the canonical execution APIs.
- **Moved Phase 04 Chatflow**: Depends on the shared stream contract from US6
  and is planned in `../004-agentic-chatflow/tasks.md`.
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
- US6 tests T076-T081 can run in parallel.
- US8 tests T100-T104 can run in parallel.
- Phase 03 and Phase 04 task plans define their own parallel work.

---

## Parallel Example: User Story 1

```bash
Task: "Add VN workflow runtime test for technical-analysis with agent metadata in tests/test_platform_services.py"
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
6. Demo one VN workflow run with grounded output and safe citation inspection.

### Incremental Delivery

1. Land Phase 2A first so model-visible context, rendered record `context`, and
   citation persistence are deterministic.
2. Deliver US1 to prove the runtime, dataflows, API, and UI path.
3. Deliver US2 to complete workflow choice on the migrated UI.
4. Deliver US6 to make stream transport the canonical execution path.
5. Deliver US8 right-panel artifact and citation inspection.
6. Continue composite workflows, active-market validation, and reinspection in
   `../003-vn-gold-dataflows-workflows/`.
7. Continue chatflow planning in `../004-agentic-chatflow/`.

### Notes

- Keep workflow YAML as the executable contract and Markdown skills as governed
  analyst instructions.
- Keep detailed collection requirements in `DATA_REQUIREMENTS.yaml`, not in
  workflow YAML.
- Keep provider access behind `collect_dataflow`; agent skills must not call
  provider clients directly.
- Treat structured record fields as canonical and rendered `context` as a
  deterministic projection reused by LLM input and UI display.
- Do not add production flexible chatflow behavior, broker actions, or autonomous
  financial actions in this feature. Gold workflow support is owned
  by `../003-vn-gold-dataflows-workflows/`; chatflow is owned by
  `../004-agentic-chatflow/`.
