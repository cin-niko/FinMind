---
id: SPEC-FEAT-002-TASKS
feature: workflow
status: active
owner: solo
created: 2026-06-26
implements: []
validated_by: []
adr_refs:
  - docs/adr/ADR-001-hybrid-workflow-definitions-and-agent-skills.md
---

# Tasks: Workflow

**Input**: Design documents from `specs/002-workflow/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`,
`contracts/api-contract.md`, `quickstart.md`

**Tests**: Required for changed backend/API behavior and frontend contract
compatibility per `.specify/memory/constitution.md` and `plan.md`.

**Organization**: Tasks are grouped by independently testable user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel after its phase dependencies are complete.
- **[Story]**: User story label from `spec.md`.
- Every task includes the target file path.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare Phase 02 implementation surfaces and verification targets.

- [X] T001 Update Phase 02 implementation references in `AGENTS.md`
- [X] T002 [P] Add workflow definition fixture directory in `src/api/platform/workflows/definitions/README.md`
- [X] T003 [P] Add workflow skill fixture directory in `src/api/platform/workflows/skills/README.md`
- [X] T004 [P] Add workflow runtime module exports in `src/api/platform/workflows/__init__.py`
- [X] T005 [P] Add Phase 02 quickstart command notes in `specs/002-workflow/quickstart.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared runtime, contracts, fixtures, and validation that MUST be in
place before user stories can be implemented.

**CRITICAL**: No user story work can begin until this phase is complete.

### Tests for Foundation

- [X] T006 [P] Add workflow definition loading tests in `tests/test_platform_services.py`
- [X] T007 [P] Add workflow YAML/skill compatibility tests in `tests/test_platform_services.py`
- [X] T008 [P] Add unsupported market and missing symbol API validation tests in `tests/test_app.py`

### Implementation for Foundation

- [X] T009 Add `US_STOCK`, workflow definition, agent skill, workflow step, and quality report models in `src/api/platform/models.py`
- [X] T010 Add seeded VN and US stock instruments, price records, fundamentals, and source documents in `src/api/platform/memory.py`
- [X] T011 Add YAML workflow definition loader in `src/api/platform/workflows/definitions.py`
- [X] T012 Add Markdown agent skill loader in `src/api/platform/workflows/skills.py`
- [X] T013 Add workflow definition schema validation and skill compatibility checks in `src/api/platform/workflows/specs.py`
- [X] T014 Replace hard-coded workflow catalog construction with YAML-backed catalog loading in `src/api/platform/workflows/catalog.py`
- [X] T015 Add market/symbol/workflow compatibility validation for VN_STOCK and US_STOCK only in `src/api/platform/workflows/validation.py`
- [X] T016 Add workflow catalog serialization fields for description, workflow_type, market_scope, required_inputs, stages, requires_citations, chart_requirements, and output_sections in `src/api/platform/workflows/service.py`
- [X] T017 Update API response schemas for expanded workflow catalog and run output contracts in `src/api/schemas.py`
- [X] T018 Update workflow route error mapping for unknown workflow, unsupported input, and missing required input in `src/api/routes/workflows.py`
- [X] T019 Update TypeScript workflow/run API types for quality, stage status, warnings, freshness, artifacts, and catalog fields in `src/ui/src/api/client.ts`

**Checkpoint**: Workflow definitions load, skills are validated, VN/US scope is
enforced, and API/UI types can represent Phase 02 contracts.

---

## Phase 3: User Story 1 - Run A Supported Stock Workflow From UI (Priority: P1) MVP

**Goal**: An authenticated internal user runs one supported VN or US stock
workflow from the UI and reviews cited, fresh, chart-backed output.

**Independent Test**: Log in, open `Workflows`, run one supported VN stock or US
stock workflow, and verify output sections, citations, freshness, chart artifacts,
and execution status.

### Tests for User Story 1

- [X] T020 [P] [US1] Add API test for running `technical-analysis` with `market=VN_STOCK` and `symbol=VCB` in `tests/test_platform_services.py`
- [X] T021 [P] [US1] Add API test for running `technical-analysis` with `market=US_STOCK` and `symbol=AAPL` in `tests/test_platform_services.py`
- [X] T022 [P] [US1] Add run output contract assertions for citations, freshness, chart artifact, visible execution, and no raw reasoning in `tests/test_platform_services.py`

### Implementation for User Story 1

- [X] T023 [P] [US1] Add `technical-analysis.yaml` workflow definition in `src/api/platform/workflows/definitions/technical-analysis.yaml`
- [X] T024 [P] [US1] Add `technical-analysis.md` agent skill in `src/api/platform/workflows/skills/technical-analysis.md`
- [X] T025 [US1] Add bounded data collection for workflow-required price, fundamental, and source document records in `src/api/platform/workflows/collector.py`
- [X] T026 [US1] Add basic dataset quality report generation for fresh/stale/missing records in `src/api/platform/workflows/quality.py`
- [X] T027 [US1] Add technical analysis step execution with cited trend output and chart artifact references in `src/api/platform/workflows/executor.py`
- [X] T028 [US1] Orchestrate validation, collection, quality, execution, persistence, and serialization in `src/api/platform/workflows/service.py`
- [X] T029 [US1] Update workflow run API request handling to submit market and symbol inputs in `src/api/routes/workflows.py`
- [X] T030 [US1] Update workflow form market and symbol handling for VN_STOCK and US_STOCK in `src/ui/src/features/workflows/WorkflowPage.tsx`
- [X] T031 [US1] Update result view to show quality summary, freshness, citations, chart artifact, and stage status for one run in `src/ui/src/features/results/ResultView.tsx`

**Checkpoint**: User Story 1 is independently runnable and testable as the MVP.

---

## Phase 4: User Story 2 - Choose A Workflow Type (Priority: P1)

**Goal**: An authenticated internal user can choose fundamental analysis,
technical analysis, news digest, risk review, or stock brief from the workflow
catalog and understand expected inputs/outputs before running.

**Independent Test**: Open the workflow catalog and verify each supported workflow
type describes purpose, required inputs, output sections, evidence/citation
expectations, and chart artifact expectations.

### Tests for User Story 2

- [X] T032 [P] [US2] Add catalog API test for required workflow ids and catalog metadata in `tests/test_platform_services.py`
- [X] T033 [P] [US2] Add frontend catalog type coverage for workflow metadata mapping in `src/ui/src/features/workflows/workflowCatalog.test.ts`

### Implementation for User Story 2

- [X] T034 [P] [US2] Add `fundamental-analysis.yaml` workflow definition in `src/api/platform/workflows/definitions/fundamental-analysis.yaml`
- [X] T035 [P] [US2] Add `news-digest.yaml` workflow definition in `src/api/platform/workflows/definitions/news-digest.yaml`
- [X] T036 [P] [US2] Add `risk-review.yaml` workflow definition in `src/api/platform/workflows/definitions/risk-review.yaml`
- [X] T037 [P] [US2] Add `fundamental-analysis.md` agent skill in `src/api/platform/workflows/skills/fundamental-analysis.md`
- [X] T038 [P] [US2] Add `news-digest.md` agent skill in `src/api/platform/workflows/skills/news-digest.md`
- [X] T039 [P] [US2] Add `risk-review.md` agent skill in `src/api/platform/workflows/skills/risk-review.md`
- [X] T040 [US2] Add fundamental, news digest, and risk review section executors in `src/api/platform/workflows/executor.py`
- [X] T041 [US2] Update workflow catalog cards to show purpose, supported markets, required inputs, expected sections, citations, and chart requirements in `src/ui/src/features/workflows/WorkflowPage.tsx`
- [X] T042 [US2] Update workflow catalog and form styles for denser metadata display in `src/ui/src/styles.css`

**Checkpoint**: User Story 2 catalog selection works independently of composite
workflow execution.

---

## Phase 5: User Story 3 - Compose A Stock Brief From Reusable Steps (Priority: P1)

**Goal**: An authenticated internal user runs `stock-brief`, which executes
collection, data-quality checks, fundamental analysis, technical analysis, news
digest, and risk review as visible reusable stages.

**Independent Test**: Run `stock-brief` and verify visible stages, quality gate
behavior, partial/unavailable sections, and preserved completed sections.

### Tests for User Story 3

- [X] T043 [P] [US3] Add stock brief composite success API test in `tests/test_platform_services.py`
- [X] T044 [P] [US3] Add stock brief partial/unavailable stage API test with missing news or stale dataset fixture in `tests/test_platform_services.py`
- [X] T045 [P] [US3] Add output validation test that blocked claim categories are omitted or unavailable in `tests/test_platform_services.py`

### Implementation for User Story 3

- [X] T046 [P] [US3] Add `stock-brief.yaml` composite workflow definition in `src/api/platform/workflows/definitions/stock-brief.yaml`
- [X] T047 [P] [US3] Add `stock-brief.md` composition skill note in `src/api/platform/workflows/skills/stock-brief.md`
- [X] T048 [US3] Implement composite step sequencing and stage status propagation in `src/api/platform/workflows/executor.py`
- [X] T049 [US3] Implement quality gate allowed_claims and blocked_claims enforcement in `src/api/platform/workflows/quality.py`
- [X] T050 [US3] Persist partial and failed workflow runs with visible execution details in `src/api/platform/workflows/service.py`
- [X] T051 [US3] Render per-stage success, partial, failed, and unavailable states in `src/ui/src/features/results/ResultView.tsx`
- [X] T052 [US3] Add result view styling for quality warnings and unavailable sections in `src/ui/src/styles.css`

**Checkpoint**: User Story 3 can be demonstrated with success and partial
`stock-brief` runs.

---

## Phase 6: User Story 4 - Reject Unsupported Inputs (Priority: P1)

**Goal**: An authenticated internal user cannot run unsupported markets,
unsupported symbols, missing inputs, or unsafe workflow states.

**Independent Test**: Attempt workflows with gold, BTC, unsupported symbols,
missing inputs, and stale/missing data conditions; verify no fabricated successful
run is created.

### Tests for User Story 4

- [X] T053 [P] [US4] Add API tests rejecting GOLD, BTC, crypto, missing symbol, and unsupported symbol inputs in `tests/test_platform_services.py`
- [X] T054 [P] [US4] Add API test that failed validation does not create a successful run in `tests/test_platform_services.py`
- [X] T055 [P] [US4] Add protected route regression test for workflow validation errors after login in `tests/test_app.py`

### Implementation for User Story 4

- [X] T056 [US4] Harden workflow input validation messages and status codes in `src/api/platform/workflows/validation.py`
- [X] T057 [US4] Prevent unsupported assets from appearing as enabled UI choices in `src/ui/src/features/workflows/WorkflowPage.tsx`
- [X] T058 [US4] Show field-level validation and run error messages near workflow inputs in `src/ui/src/features/workflows/WorkflowPage.tsx`
- [X] T059 [US4] Add no-fabrication guard for failed collection, failed quality, and missing citations in `src/api/platform/workflows/service.py`

**Checkpoint**: User Story 4 safety validation is independently testable through
API calls and UI form behavior.

---

## Phase 7: User Story 5 - Reopen Workflow Results (Priority: P2)

**Goal**: An authenticated internal user can reopen completed, partial, or failed
workflow runs from history and inspect output, citations, freshness, artifacts,
and execution status.

**Independent Test**: Complete a workflow run, refresh with a valid session,
select `History` -> `Workflow Runs`, reopen the run, and verify the saved result
is restored.

### Tests for User Story 5

- [X] T060 [P] [US5] Add run history list and reinspection API test for completed workflow runs in `tests/test_platform_services.py`
- [X] T061 [P] [US5] Add partial or failed run reinspection API test in `tests/test_platform_services.py`
- [X] T062 [P] [US5] Add unknown run not-found regression test for Phase 02 run shape in `tests/test_app.py`

### Implementation for User Story 5

- [X] T063 [US5] Ensure run repository preserves quality, citations, freshness, artifacts, visible execution, and logs in `src/api/platform/repositories.py`
- [X] T064 [US5] Serialize completed, partial, and failed Phase 02 runs consistently in `src/api/schemas.py`
- [X] T065 [US5] Ensure run list and run detail routes expose saved workflow output without raw reasoning in `src/api/routes/runs.py`
- [X] T066 [US5] Update app history selection flow for Phase 02 workflow runs in `src/ui/src/App.tsx`
- [X] T067 [US5] Update shell/history labels for workflow run reinspection in `src/ui/src/features/shell/AppShell.tsx`

**Checkpoint**: User Story 5 is independently testable from stored workflow run
records.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Quality, safety, UX, performance, documentation, and final
verification across completed stories.

- [X] T068 [P] Update implementation traceability in `specs/002-workflow/spec.md`
- [X] T069 [P] Update implementation traceability in `specs/002-workflow/plan.md`
- [X] T070 [P] Update ADR/risk references after implementation in `docs/adr/ADR-001-hybrid-workflow-definitions-and-agent-skills.md`
- [X] T071 [P] Update risk mitigations after implementation in `docs/risks/RISK-001-workflow-skill-contract-drift.md`
- [X] T072 [P] Update risk mitigations after implementation in `docs/risks/RISK-002-agent-skill-unsupported-claims.md`
- [X] T073 [P] Update risk mitigations after implementation in `docs/risks/RISK-003-external-agent-integration-portability.md`
- [X] T074 Run backend verification command `UV_CACHE_DIR=/private/tmp/finmind-uv-cache uv run --group dev python -m pytest tests/test_app.py tests/test_platform_services.py`
- [X] T075 Run frontend verification command `cd src/ui && npm run build`
- [X] T076 Review workflow UI against `specs/system/ui-ux-guidelines.md`
- [X] T077 Review safety guardrails against `.specify/memory/constitution.md`
- [X] T078 Verify quickstart scenarios in `specs/002-workflow/quickstart.md`

---

## Phase 9: Dataflows Retrieval Refactor

**Purpose**: Move provider retrieval out of workflow collector code and into a
shared `src/api/platform/dataflows/` module for Phase 02 workflows and future
Phase 03 chatflow retrieval.

### Tests for Dataflows

- [ ] T079 [P] Add dataflow model serialization tests for retrieval request, retrieval result, and provider result in `tests/test_platform_services.py`
- [ ] T080 [P] Add provider registry dataset-group selection tests for VN_STOCK and US_STOCK in `tests/test_platform_services.py`
- [ ] T081 [P] Add deterministic fallback labeling tests for provider failure in `tests/test_platform_services.py`
- [ ] T082 [P] Add no-secret and no-raw-provider-payload assertions for dataflow results in `tests/test_platform_services.py`
- [ ] T083 [P] Add workflow API test asserting `output.collection.retrieval_id` and `provider_results` for `technical-analysis` in `tests/test_platform_services.py`
- [ ] T084 [P] Add workflow API test asserting fallback collection status is visible and claims remain cited or unavailable in `tests/test_platform_services.py`
- [ ] T085 [P] Add test mapping `fundamental-analysis` required datasets to `market_price`, `fundamental`, and `news` in `tests/test_platform_services.py`
- [ ] T086 [P] Add test mapping `news-digest` required datasets to `news` without requiring price data in `tests/test_platform_services.py`
- [ ] T087 [P] Add frontend catalog regression test that provider internals are not shown on workflow cards in `src/ui/src/features/workflows/workflowCatalog.test.ts`
- [ ] T088 [P] Add stock brief API test asserting a single retrieval result covers `market_price`, `fundamental`, and `news` in `tests/test_platform_services.py`
- [ ] T089 [P] Add stock brief partial-provider test asserting failed news retrieval marks news/risk sections unavailable without blocking technical analysis in `tests/test_platform_services.py`
- [ ] T090 [P] Add API test that unsupported market validation stops before dataflow provider calls in `tests/test_platform_services.py`
- [ ] T091 [P] Add API test that missing Alpha Vantage key creates skipped provider status and fallback warning for US news in `tests/test_platform_services.py`
- [ ] T092 [P] Add API test that SEC EDGAR missing User-Agent creates skipped fundamentals provider status without leaking diagnostics in `tests/test_platform_services.py`
- [ ] T093 [P] Add run reinspection API test asserting collection status persists in saved workflow runs in `tests/test_platform_services.py`
- [ ] T094 [P] Add partial run reinspection API test asserting provider warnings persist without raw diagnostics in `tests/test_platform_services.py`

### Implementation for Dataflows

- [ ] T095 Create dataflows package exports in `src/api/platform/dataflows/__init__.py`
- [ ] T096 [P] Create dataflows provider package exports in `src/api/platform/dataflows/providers/__init__.py`
- [ ] T097 [P] Add dataflow environment settings for Alpha Vantage key, SEC EDGAR User-Agent, provider timeout, and fallback mode in `src/api/settings.py`
- [ ] T098 [P] Add dependency notes for optional `vnstock` and live provider behavior in `specs/002-workflow/quickstart.md`
- [ ] T099 Add dataset group constants and retrieval status enums in `src/api/platform/dataflows/models.py`
- [ ] T100 Add `DataflowRetrievalRequest`, `DataflowProviderResult`, and `DataflowRetrievalResult` models in `src/api/platform/dataflows/models.py`
- [ ] T101 Add provider protocol and provider capability model in `src/api/platform/dataflows/providers/base.py`
- [ ] T102 Add provider registry by market and dataset group in `src/api/platform/dataflows/registry.py`
- [ ] T103 Add provider payload normalizers for price records, fundamental records, and source documents in `src/api/platform/dataflows/normalizers.py`
- [ ] T104 Add deterministic fallback provider and fallback policy in `src/api/platform/dataflows/fallback.py`
- [ ] T105 Add `DataflowService.retrieve(...)` orchestration with timeout, provider status aggregation, fallback, and safe result output in `src/api/platform/dataflows/service.py`
- [ ] T106 Wire `DataflowService` construction into platform factory dependencies in `src/api/platform/factory.py`
- [ ] T107 Refactor workflow collected data model to include `DataflowRetrievalResult` in `src/api/platform/workflows/collector.py`
- [ ] T108 Refactor workflow collector to build `DataflowRetrievalRequest` from workflow required datasets in `src/api/platform/workflows/collector.py`
- [ ] T109 Add workflow-required-dataset to dataflow-dataset-group mapping helper in `src/api/platform/workflows/collector.py`
- [ ] T110 Refactor workflow service to call `DataflowService` through the collector and persist collection output in `src/api/platform/workflows/service.py`
- [ ] T111 Update quality report input mapping from dataflow dataset groups to workflow dataset statuses in `src/api/platform/workflows/quality.py`
- [ ] T112 Serialize workflow collection output without raw provider payloads in `src/api/schemas.py`
- [ ] T113 Update workflow run output TypeScript types for collection result fields in `src/ui/src/api/client.ts`
- [ ] T114 Render collection status and safe provider summaries in result view in `src/ui/src/features/results/ResultView.tsx`
- [ ] T115 Keep provider details out of catalog response serialization in `src/api/platform/workflows/service.py`
- [ ] T116 Update workflow catalog UI copy to remain provider-neutral while result view shows collection status in `src/ui/src/features/workflows/WorkflowPage.tsx`
- [ ] T117 Ensure composite workflow execution reuses one collected dataflow result across sections in `src/api/platform/workflows/service.py`
- [ ] T118 Propagate provider warnings into visible composite stages in `src/api/platform/workflows/executor.py`
- [ ] T119 Render composite collection warnings beside stage statuses in `src/ui/src/features/results/ResultView.tsx`
- [ ] T120 Add graceful unavailable behavior for VN `vnstock` adapter in `src/api/platform/dataflows/providers/vnstock.py`
- [ ] T121 Add graceful unavailable behavior for US Alpha Vantage adapter in `src/api/platform/dataflows/providers/alpha_vantage.py`
- [ ] T122 Add graceful unavailable behavior for US SEC EDGAR adapter in `src/api/platform/dataflows/providers/sec_edgar.py`
- [ ] T123 Add provider failure and skipped-provider mapping into data-quality blocked claims in `src/api/platform/workflows/quality.py`
- [ ] T124 Ensure route error mapping distinguishes validation errors from provider partial/fallback output in `src/api/routes/workflows.py`
- [ ] T125 Ensure run repository preserves collection output in `src/api/platform/repositories.py`
- [ ] T126 Ensure run list and run detail routes serialize collection output consistently in `src/api/routes/runs.py`
- [ ] T127 Ensure result reinspection UI displays saved collection status without rerunning providers in `src/ui/src/App.tsx`

### Verification

- [ ] T128 [P] Update implementation traceability for dataflows in `specs/002-workflow/spec.md`
- [ ] T129 [P] Update implementation traceability for dataflows in `specs/002-workflow/plan.md`
- [ ] T130 [P] Update risk notes for provider failure, fallback labeling, and source licensing in `docs/risks/RISK-002-agent-skill-unsupported-claims.md`
- [ ] T131 [P] Update ADR notes for retrieval module boundaries in `docs/adr/ADR-001-hybrid-workflow-definitions-and-agent-skills.md`
- [ ] T132 Review collection status UI against `specs/system/ui-ux-guidelines.md`
- [ ] T133 Review safety guardrails against `.specify/memory/constitution.md`
- [ ] T134 Run backend verification command `UV_CACHE_DIR=/private/tmp/finmind-uv-cache uv run --group dev python -m pytest tests/test_app.py tests/test_platform_services.py`
- [ ] T135 Run backend lint command `UV_CACHE_DIR=/private/tmp/finmind-uv-cache uv run --with ruff ruff check src tests`
- [ ] T136 Run frontend verification command `cd src/ui && npm run build`
- [ ] T137 Re-run quickstart scenarios in `specs/002-workflow/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Setup and blocks all user stories.
- **User Stories (Phases 3-7)**: Depend on Foundational completion.
- **Polish (Phase 8)**: Depends on all desired user stories.
- **Dataflows Retrieval Refactor (Phase 9)**: Depends on the current workflow
  harness and supersedes direct collector/repository retrieval for future work.

### User Story Dependencies

- **US1 Run A Supported Stock Workflow From UI (P1)**: MVP; depends only on Foundation.
- **US2 Choose A Workflow Type (P1)**: Depends on Foundation; can proceed in parallel with US1 after shared catalog contracts exist.
- **US3 Compose A Stock Brief From Reusable Steps (P1)**: Depends on Foundation and benefits from US1/US2 step executors.
- **US4 Reject Unsupported Inputs (P1)**: Depends on Foundation; can proceed in parallel with US1 because it targets validation behavior.
- **US5 Reopen Workflow Results (P2)**: Depends on Foundation and at least one run-producing story, preferably US1.

### Within Each User Story

- Write or update tests before implementation tasks in that story.
- Definition/skill files before catalog/service code that loads them.
- Collector and quality code before executor code that consumes collected data.
- Executor code before route/UI integration.
- Story checkpoint must pass before moving to the next priority story.

---

## Parallel Opportunities

- Setup tasks T002-T005 can run in parallel.
- Foundation tests T006-T008 can run in parallel.
- US1 tests T020-T022 can run in parallel; definition and skill tasks T023-T024 can run in parallel.
- US2 definition and skill tasks T034-T039 can run in parallel.
- US3 tests T043-T045 can run in parallel; definition and skill tasks T046-T047 can run in parallel.
- US4 tests T053-T055 can run in parallel.
- US5 tests T060-T062 can run in parallel.
- Polish documentation tasks T068-T073 can run in parallel.
- Dataflows tests T079-T094 can run in parallel; provider adapter skeletons
  T120-T122 can run in parallel after the base protocol and registry exist.

---

## Parallel Example: User Story 1

```bash
Task: "Add API test for running technical-analysis with market=VN_STOCK and symbol=VCB in tests/test_platform_services.py"
Task: "Add API test for running technical-analysis with market=US_STOCK and symbol=AAPL in tests/test_platform_services.py"
Task: "Add technical-analysis.yaml workflow definition in src/api/platform/workflows/definitions/technical-analysis.yaml"
Task: "Add technical-analysis.md agent skill in src/api/platform/workflows/skills/technical-analysis.md"
```

## Parallel Example: User Story 2

```bash
Task: "Add fundamental-analysis.yaml workflow definition in src/api/platform/workflows/definitions/fundamental-analysis.yaml"
Task: "Add news-digest.yaml workflow definition in src/api/platform/workflows/definitions/news-digest.yaml"
Task: "Add risk-review.yaml workflow definition in src/api/platform/workflows/definitions/risk-review.yaml"
Task: "Add fundamental-analysis.md agent skill in src/api/platform/workflows/skills/fundamental-analysis.md"
Task: "Add news-digest.md agent skill in src/api/platform/workflows/skills/news-digest.md"
Task: "Add risk-review.md agent skill in src/api/platform/workflows/skills/risk-review.md"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 setup.
2. Complete Phase 2 foundation.
3. Complete Phase 3 User Story 1.
4. Validate with backend tests for `technical-analysis` VN/US runs and frontend build.
5. Demo one VN or US workflow run with citations, freshness, chart artifact, and visible execution.

### Incremental Delivery

1. Add US1 to prove one runnable workflow end to end.
2. Add US2 to complete the workflow catalog and analysis choices.
3. Add US3 to compose `stock-brief` from reusable steps.
4. Add US4 to harden unsupported input and no-fabrication behavior.
5. Add US5 to complete history/reinspection behavior.
6. Finish Phase 8 verification and traceability updates.
7. Complete Phase 9 before treating workflow outputs as live-provider-backed.

### Notes

- Keep workflow YAML as the executable contract and Markdown skills as governed
  analysis instructions.
- Do not expose Markdown skills as directly executable API or external-agent
  tools.
- Do not add gold, BTC, broker actions, order execution, or flexible chatflow in
  this feature.
- Commit after each completed phase or independently testable story.
