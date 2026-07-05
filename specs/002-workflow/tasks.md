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

- [X] T001 Update workflow implementation dependencies for LangChain Deep Agents and `langchain-litellm` in `pyproject.toml`
- [X] T002 [P] Add target backend package roots in `src/finmind_agents/__init__.py` and `src/finmind_api/__init__.py`
- [X] T003 [P] Add target frontend package root notes in `src/finmind_ui/README.md`
- [X] T004 [P] Add target package migration notes and runtime env expectations in `specs/002-workflow/quickstart.md`
- [X] T005 Make `src/finmind_api/app.py` the canonical API entrypoint

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Create the shared runtime, dataflow, workflow, and API boundaries
that all workflow stories depend on.

**CRITICAL**: No user story work can begin until this phase is complete.

### Tests for Foundation

- [X] T006 [P] Add package migration import coverage for `finmind_agents` and `finmind_api` in `tests/test_platform_services.py`
- [X] T007 [P] Add runtime policy and fail-closed model configuration tests in `tests/test_platform_services.py`
- [X] T008 [P] Add API contract regression coverage for workflow agent metadata in `tests/test_app.py`

### Implementation for Foundation

- [X] T009 Create shared runtime models and policy types in `src/finmind_agents/runtime/models.py`
- [X] T010 [P] Create LiteLLM-backed model bootstrap and runtime settings loader in `src/finmind_agents/runtime/bootstrap.py`
- [X] T011 [P] Create runtime validators for citations, safety, and no-raw-reasoning rules in `src/finmind_agents/runtime/validators.py`
- [X] T012 [P] Create runtime tool registry for `collect_dataflow`, skill loading, and output validation in `src/finmind_agents/runtime/tools.py`
- [X] T013 Create `FinMindAgentRuntime` orchestration entrypoint in `src/finmind_agents/runtime/service.py`
- [X] T014 [P] Migrate canonical dataflow models and providers into `src/finmind_agents/dataflows/models.py` and `src/finmind_agents/dataflows/providers/base.py`
- [X] T015 [P] Migrate workflow definitions, skill loading, and validation into `src/finmind_agents/workflows/definitions.py`, `src/finmind_agents/workflows/skills.py`, and `src/finmind_agents/workflows/specs.py`
- [X] T016 Create thin API dependency wiring to the new packages in `src/finmind_api/dependencies.py` and `src/finmind_api/app.py`
- [X] T017 Remove the legacy `src/api` boundary and route backend imports through `finmind_agents` and `finmind_api`

**Checkpoint**: The target packages load, the runtime can be constructed, and
the current API surface can call through the new boundaries.

---

## Phase 3: User Story 1 - Run A Supported Stock Workflow From UI (Priority: P1) MVP

**Goal**: An authenticated internal user runs one supported VN stock or US stock
workflow through the LangChain/LiteLLM-backed runtime and reviews grounded
results in the UI.

**Independent Test**: Log in, open `Workflows`, run one supported VN or US stock
workflow, and verify agent metadata, citations, chart artifacts, and execution
status.

### Tests for User Story 1

- [X] T018 [P] [US1] Add VN workflow runtime test for `technical-analysis` with agent metadata in `tests/test_platform_services.py`
- [X] T019 [P] [US1] Add US workflow runtime test for `technical-analysis` with provider/fallback metadata in `tests/test_platform_services.py`
- [X] T020 [P] [US1] Add fail-closed workflow run test when `FINMIND_AGENT_MODEL` is unset in `tests/test_platform_services.py`

### Implementation for User Story 1

- [X] T021 [P] [US1] Migrate workflow collection and quality services into `src/finmind_agents/workflows/collector.py` and `src/finmind_agents/workflows/quality.py`
- [X] T022 [US1] Implement runtime-driven workflow execution for atomic workflows in `src/finmind_agents/workflows/service.py`
- [X] T023 [US1] Implement the `collect_dataflow` runtime tool against shared dataflows in `src/finmind_agents/runtime/tools.py`
- [X] T024 [US1] Add workflow API routes that call the new runtime-backed service in `src/finmind_api/routes/workflows.py`
- [X] T025 [US1] Align backend schemas with the `agent` and `collection` response envelopes in `src/finmind_api/schemas.py`
- [X] T026 [US1] Migrate workflow page request handling and response typing into `src/finmind_ui/src/api/client.ts` and `src/finmind_ui/src/features/workflows/WorkflowPage.tsx`
- [X] T027 [US1] Migrate result rendering for agent metadata, citations, and chart artifacts into `src/finmind_ui/src/features/results/ResultView.tsx`

**Checkpoint**: User Story 1 is a working MVP on the new runtime boundary.

---

## Phase 4: User Story 2 - Choose A Workflow Type (Priority: P1)

**Goal**: An authenticated internal user can choose the right workflow and
understand its bounded behavior before execution.

**Independent Test**: Open the workflow catalog and verify each workflow shows
purpose, markets, required inputs, stages, expected sections, and chart/citation
expectations through the migrated UI.

### Tests for User Story 2

- [X] T028 [P] [US2] Add catalog metadata regression tests for the migrated workflow catalog in `tests/test_platform_services.py`
- [X] T029 [P] [US2] Add frontend catalog mapping coverage for the migrated UI client in `src/finmind_ui/src/features/workflows/workflowCatalog.test.ts`

### Implementation for User Story 2

- [X] T030 [P] [US2] Migrate workflow catalog loading and serialization into `src/finmind_agents/workflows/catalog.py`
- [X] T031 [US2] Add workflow catalog API route and serialization wiring in `src/finmind_api/routes/workflows.py`
- [X] T032 [US2] Migrate catalog display logic and provider-neutral workflow copy into `src/finmind_ui/src/features/workflows/workflowCatalog.ts` and `src/finmind_ui/src/features/workflows/WorkflowPage.tsx`
- [X] T033 [US2] Migrate workflow page styling for dense metadata display into `src/finmind_ui/src/styles.css`

**Checkpoint**: Workflow choice is independently testable through the migrated
catalog path.

---

## Phase 5: User Story 3 - Compose A Stock Brief From Reusable Steps (Priority: P1)

**Goal**: An authenticated internal user runs `stock-brief` as a reusable,
runtime-driven composite workflow with visible stages and guarded partial
behavior.

**Independent Test**: Run `stock-brief` and verify visible stages, quality-gate
behavior, partial/unavailable sections, and preserved completed sections.

### Tests for User Story 3

- [ ] T034 [P] [US3] Add composite workflow runtime test for `stock-brief` success in `tests/test_platform_services.py`
- [ ] T035 [P] [US3] Add composite workflow partial-provider test for blocked news or risk sections in `tests/test_platform_services.py`
- [ ] T036 [P] [US3] Add API response coverage for visible stage statuses and blocked claim categories in `tests/test_app.py`

### Implementation for User Story 3

- [ ] T037 [P] [US3] Migrate composite workflow definitions and skill refs into `src/finmind_agents/workflows/definitions.py` and `src/finmind_agents/skills/`
- [ ] T038 [US3] Implement composite sequencing and section assembly in `src/finmind_agents/workflows/executor.py`
- [ ] T039 [US3] Implement runtime policy handling for reusable internal steps in `src/finmind_agents/runtime/service.py`
- [ ] T040 [US3] Persist composite run output, stage status, and tool status via the API-layer run store (`src/finmind_api/run_store.py`)
- [ ] T041 [US3] Render composite stage states and unavailable sections in `src/finmind_ui/src/features/results/ResultView.tsx`

**Checkpoint**: `stock-brief` works as a composed workflow without duplicating
collection or safety logic.

---

## Phase 6: User Story 4 - Reject Unsupported Inputs (Priority: P1)

**Goal**: An authenticated internal user cannot run unsupported markets,
unsupported symbols, undeclared collection plans, or unsafe workflow states.

**Independent Test**: Attempt unsupported assets, missing inputs, invalid
symbols, undeclared dataset collection, and missing model configuration.

### Tests for User Story 4

- [ ] T042 [P] [US4] Add unsupported market, symbol, and missing input validation coverage on the migrated API in `tests/test_app.py`
- [ ] T043 [P] [US4] Add collection-plan rejection tests for undeclared dataset requests in `tests/test_platform_services.py`
- [ ] T044 [P] [US4] Add no-fabrication assertions for failed quality or missing citations in `tests/test_platform_services.py`

### Implementation for User Story 4

- [ ] T045 [US4] Migrate workflow input validation and market scoping into `src/finmind_agents/workflows/validation.py`
- [ ] T046 [US4] Add collection-plan approval and rejection logic in `src/finmind_agents/dataflows/requirements.py`
- [ ] T047 [US4] Add API error mapping for validation, fail-closed runtime errors, and partial provider failures in `src/finmind_api/routes/workflows.py`
- [ ] T048 [US4] Migrate field-level validation and unsupported-state UI handling into `src/finmind_ui/src/features/workflows/WorkflowPage.tsx`

**Checkpoint**: Safety behavior is independently testable through both API and
UI.

---

## Phase 7: User Story 5 - Reopen Workflow Results (Priority: P2)

**Goal**: An authenticated internal user can reopen completed or partial runs
after the migration without rerunning providers or the agent.

**Independent Test**: Complete a workflow run, refresh, reopen it from history,
and verify saved output, collection status, agent metadata, citations, and
artifacts are restored.

### Tests for User Story 5

- [ ] T049 [P] [US5] Add migrated run history API coverage for completed and partial workflow runs in `tests/test_app.py`
- [x] T050 [P] [US5] Add run reinspection persistence coverage for `collection` and `agent` envelopes in `tests/test_platform_services.py`

### Implementation for User Story 5

- [x] T051 [US5] Migrate run repository persistence into PostgreSQL via `PostgresRunRepository` in the API layer (`src/finmind_api/run_store.py`), configured by `FINMIND_DATABASE_URL`; the agentic layer keeps only the `RunRepository` contract
- [x] T052 [US5] Add run list and detail routes in `src/finmind_api/routes/runs.py`
- [ ] T053 [US5] Migrate history selection and run reinspection flow into `src/finmind_ui/src/App.tsx` and `src/finmind_ui/src/features/shell/AppShell.tsx`

**Checkpoint**: Stored workflow runs remain inspectable after the architecture
migration.

---

## Phase 8: User Story 6 - Direct Async Workflow Streaming With Progress And Answer Separation (Priority: P1)

**Goal**: An authenticated internal user can call one async workflow API and
receive safe SSE stream events on the same HTTP response, with a separate
progress lane for visible working steps and a separate answer lane for streamed
final answer text. The shared event model must stay generic enough for Phase 03
chatflow reuse without implementing chatflow in Phase 02.

**Independent Test**: Submit `POST /api/workflows/{workflow_id}/runs`, consume
`text/event-stream` events from the same response, and verify first event
latency, ordered safe `run.*` progress events, ordered `answer.delta` events,
final output reconciliation, and no event-loop blocking from sync dependencies.

### Tests for User Story 6

- [X] T065 [P] [US6] Add direct workflow SSE stream API tests in `tests/test_app.py` covering `run.started`, `run.stage`, `run.completed`, and terminal events
- [X] T066 [P] [US6] Add workflow stream completion persistence/reinspection coverage in `tests/test_app.py`
- [X] T067 [P] [US6] Add mandatory streaming-adapter validation and non-blocking sync-offload regression coverage for workflow providers or model calls in `tests/test_platform_services.py`
- [X] T068 [P] [US6] Add workflow process-local global and per-user stream limit coverage for safe `429` responses in `tests/test_app.py`
- [X] T069 [P] [US6] Add workflow progress-vs-answer event ordering coverage in `tests/test_app.py` so `run.stage` becomes visible before `answer.delta`
- [X] T070 [P] [US6] Add frontend stream client parsing coverage for `run.*` and `answer.delta` events in `src/finmind_ui/src/api/client.test.ts`

### Implementation for User Story 6

- [X] T071 [US6] Add shared safe stream event models in `src/finmind_agents/streaming/models.py` for `run.started`, `run.stage`, `answer.delta`, `citation`, `artifact`, `run.completed`, and `run.failed`
- [X] T072 [US6] Update request-scoped SSE helpers, heartbeat handling, disconnect handling, and process-local concurrency semaphores in `src/finmind_api/streaming.py`
- [X] T073 [US6] Convert workflow service execution to expose async streaming events in `src/finmind_agents/workflows/service.py`
- [X] T074 [US6] Add `POST /api/workflows/{workflow_id}/runs` route in `src/finmind_api/routes/workflows.py`
- [X] T075 [US6] Refactor workflow runtime emission so visible working-step events and final answer text deltas are produced as separate shared event kinds in `src/finmind_agents/runtime/service.py` and `src/finmind_agents/workflows/service.py`, with plain-text answer streaming and async metadata finalization
- [X] T076 [US6] Persist final completed, partial, or failed workflow stream output through `src/finmind_api/run_store.py`
- [X] T077 [US6] Add bounded sync-offload helpers for sync-only provider/model paths in `src/finmind_agents/runtime/offload.py`
- [X] T078 [US6] Update frontend API client to consume shared workflow stream events in `src/finmind_ui/src/api/client.ts`
- [X] T079 [US6] Render a collapsible `Working` / `Completed N steps` progress group from `run.stage` events and keep `answer.delta` in a separate final-answer area in `src/finmind_ui/src/App.tsx` and `src/finmind_ui/src/features/chat/ChatPage.tsx`
- [X] T080 [US6] Encode the shared event contract extension note for future chatflow reuse without implementing chatflow in Phase 02 in `specs/002-workflow/plan.md` and `specs/002-workflow/contracts/api-contract.md`

**Checkpoint**: Workflow run endpoint works through direct request-scoped SSE
without compatibility wrappers or queue/subscription URLs, and the UI separates
visible working steps from final answer text.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Finish migration edges, documentation, traceability, and final
verification.

- [X] T081 [P] Update workflow implementation traceability in `specs/002-workflow/spec.md`
- [X] T082 [P] Update workflow plan traceability after package migration in `specs/002-workflow/plan.md`
- [X] T083 [P] Record runtime/package migration and direct async SSE decisions in `docs/adr/ADR-001-hybrid-workflow-definitions-and-agent-skills.md` and `docs/adr/ADR-002-direct-async-sse-streaming.md`
- [ ] T084 [P] Update workflow runtime, provider-risk, and async stream saturation mitigations in `docs/risks/RISK-001-workflow-skill-contract-drift.md`, `docs/risks/RISK-002-agent-skill-unsupported-claims.md`, and `docs/risks/RISK-004-async-stream-resource-saturation.md`
- [ ] T085 [P] Update validated environment configuration, stream limiter defaults, and deprecated env cleanup notes in `.env`
- [ ] T086 [P] Add a manual workflow runtime test script for DXG using `.env` configuration in `test.py`
- [X] T087 Review migrated workflow UI against `specs/system/ui-ux-guidelines.md`
- [ ] T088 Review runtime safety guardrails against `.specify/memory/constitution.md`
- [X] T089 Run backend verification command `UV_CACHE_DIR=/private/tmp/finmind-uv-cache uv run --group dev python -m pytest tests/test_app.py tests/test_platform_services.py`
- [X] T090 Run frontend verification command `cd src/finmind_ui && npm run build`
- [ ] T091 Run the workflow quickstart validation scenarios in `specs/002-workflow/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Setup and blocks all user stories.
- **User Stories (Phases 3-8)**: Depend on Foundational completion.
- **Polish (Phase 9)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **US1 Run A Supported Stock Workflow From UI (P1)**: Starts after Foundation;
  it is the MVP and proves the new runtime boundary end to end.
- **US2 Choose A Workflow Type (P1)**: Starts after Foundation; can proceed in
  parallel with US1 once catalog loading exists.
- **US3 Compose A Stock Brief From Reusable Steps (P1)**: Depends on Foundation
  and benefits from US1 atomic execution and US2 catalog coverage.
- **US4 Reject Unsupported Inputs (P1)**: Starts after Foundation and can run in
  parallel with US1 because it targets validation and safety behavior.
- **US5 Reopen Workflow Results (P2)**: Depends on Foundation and at least one
  run-producing story, preferably US1.
- **US6 Direct Async Workflow Streaming (P1)**: Depends on Foundation and should
  land before UI workflows are considered complete, because stream endpoints are
  the canonical execution APIs for the development branch.

### Within Each User Story

- Tests must be written and fail before implementation tasks in that story.
- Runtime/dataflow contracts must exist before workflow service wiring.
- Workflow service wiring must land before API route integration.
- API integration must land before frontend result or form integration.
- Story checkpoints should pass before moving to the next priority story.

---

## Parallel Opportunities

- Setup tasks T002-T004 can run in parallel.
- Foundation tests T006-T008 can run in parallel.
- Foundation implementation tasks T010-T012 and T014-T015 can run in parallel.
- US1 tests T018-T020 can run in parallel.
- US2 tests T028-T029 can run in parallel.
- US3 tests T034-T036 can run in parallel.
- US4 tests T042-T044 can run in parallel.
- US5 tests T049-T050 can run in parallel.
- US6 tests T065-T070 can run in parallel.
- Polish documentation tasks T081-T086 can run in parallel.

---

## Parallel Example: User Story 1

```bash
Task: "Add VN workflow runtime test for technical-analysis with agent metadata in tests/test_platform_services.py"
Task: "Add US workflow runtime test for technical-analysis with provider/fallback metadata in tests/test_platform_services.py"
Task: "Add fail-closed workflow run test when FINMIND_AGENT_MODEL is unset in tests/test_platform_services.py"
```

## Parallel Example: User Story 3

```bash
Task: "Add composite workflow runtime test for stock-brief success in tests/test_platform_services.py"
Task: "Add composite workflow partial-provider test for blocked news or risk sections in tests/test_platform_services.py"
Task: "Add API response coverage for visible stage statuses and blocked claim categories in tests/test_app.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 setup.
2. Complete Phase 2 foundation.
3. Complete Phase 3 User Story 1.
4. Validate with backend tests and the migrated workflow UI build.
5. Demo one VN or US workflow run with grounded output and safe agent metadata.

### Incremental Delivery

1. Deliver US1 to prove the runtime, dataflows, API, and UI path.
2. Deliver US2 to complete workflow choice on the migrated UI.
3. Deliver US3 to make `stock-brief` reusable and visible.
4. Deliver US4 to lock down validation and collection-plan safety.
5. Deliver US5 to preserve run history and result reinspection.
6. Deliver US6 direct workflow streaming with separate progress and final-answer areas.
7. Finish documentation, verification, and quickstart validation in Phase 9.

### Notes

- Keep workflow YAML as the executable contract and Markdown skills as governed
  analyst instructions.
- Keep detailed collection requirements in `DATA_REQUIREMENTS.yaml`, not in
  workflow YAML.
- Keep provider access behind `collect_dataflow`; agent skills must not call
  provider clients directly.
- Do not add production flexible chatflow behavior, broker actions, gold, BTC,
  or autonomous financial actions in this feature.
