---
id: SPEC-FEAT-003-TASKS
feature: vn-gold-dataflows-workflows
status: superseded
owner: solo
created: 2026-07-11
implements: []
validated_by: []
adr_refs: []
---

# Tasks: VN And Gold Dataflows And Workflows

**Input**: Design artifacts in `specs/003-vn-gold-dataflows-workflows/`

> **Superseded task draft**: This task list predates the Phase 03 scope that
> defines XAUUSD/Twelve Data, mature existing VN workflows, new VN news and
> valuation workflows, server-persisted language preference, and Phase 04-only
> chat behavior. Do not implement from this file. Regenerate it with
> `/speckit-tasks` after the detailed Phase 03 planning discussion is complete.
>
> Phase 02 migration references to task identifiers in this file are historical
> traceability only. The regenerated task list replaces those identifiers.

## Phase 1: Gold Scope And Foundation

- [ ] T001 Define the supported gold instrument/benchmark, source eligibility, datasets, freshness target, units, and provider-failure behavior in `specs/003-vn-gold-dataflows-workflows/research.md`
- [x] T002 [P] Define Phase 03 market, record, and workflow usage in `specs/003-vn-gold-dataflows-workflows/data-model.md`
- [x] T003 [P] Define catalog, gold collection, run, inspection, and safety API behavior in `specs/003-vn-gold-dataflows-workflows/contracts/workflow-contract.md`
- [x] T004 Update shared active-market scope and runtime configuration validation in `specs/system/state-model.md` and `specs/system/runtime-config-security.md`

## Phase 2: User Story 1 - Build Gold Dataflows (Priority: P1)

**Goal**: Collect auditable gold evidence before a gold workflow can make claims.

**Independent Test**: A supported gold collection returns normalized fresh cited
records; stale, missing, and undeclared data becomes unavailable or rejected.

- [ ] T005 [P] [US1] Add gold collection and stale/unavailable evidence coverage in `tests/test_platform_services.py`
- [ ] T006 [US1] Add configured gold connector selection, normalization, freshness, and provider-status handling in `src/finmind_agents/dataflows/registry.py`, `src/finmind_agents/dataflows/service.py`, and `src/finmind_agents/dataflows/providers/gold.py`
- [ ] T007 [US1] Add deterministic gold evidence records, rendered context, and citation-allowlist construction in `src/finmind_agents/evidence/builders.py`, `src/finmind_agents/evidence/rendering.py`, and `src/finmind_agents/evidence/citations.py`
- [ ] T008 [US1] Enforce declared gold dataset requirements and unsupported-asset rejection in `src/finmind_agents/dataflows/requirements.py`

## Phase 3: User Story 2 - Run Gold Workflows (Priority: P1)

**Goal**: Run fixed cited gold workflows without exposing stock-only analysis.

**Independent Test**: A gold run shows progress, citations, freshness, artifacts
where supported, and visible unavailable states.

- [ ] T009 [P] [US2] Add gold workflow catalog, run, and citation API coverage in `tests/test_app.py`
- [ ] T010 [US2] Add gold workflow definitions, skills, declared data requirements, and chart intents in `src/finmind_agents/workflows/definitions.py` and `src/finmind_agents/skills/gold-analysis/`
- [ ] T011 [US2] Assemble grounded gold workflow output and artifact status in `src/finmind_agents/workflows/service.py`
- [ ] T012 [US2] Expose Phase 03 gold catalog and workflow validation through `src/finmind_api/routes/workflows.py` and `src/finmind_api/schemas.py`
- [ ] T013 [US2] Render gold workflow selection, freshness, citations, and unavailable output in `src/finmind_ui/src/features/workflows/WorkflowPage.tsx` and `src/finmind_ui/src/features/results/ResultView.tsx`

## Phase 4: User Story 3 - Run New VN Stock Workflows (Priority: P1)

**Goal**: Deliver the composed VN stock brief on the shared evidence foundation.

**Independent Test**: A VN stock brief keeps completed sections visible when a
stage is partial and presents citations for its material claims.

- [ ] T014 [P] [US3] Add composed VN stock brief success and partial-stage coverage in `tests/test_platform_services.py`
- [ ] T015 [P] [US3] Add stage-status and blocked-claim API coverage in `tests/test_app.py`
- [ ] T016 [US3] Add VN stock brief composition and shared skill references in `src/finmind_agents/workflows/definitions.py` and `src/finmind_agents/workflows/executor.py`
- [ ] T017 [US3] Persist composed stage status and partial output in `src/finmind_api/run_store.py`
- [ ] T018 [US3] Render composed VN stage states and unavailable sections in `src/finmind_ui/src/features/results/ResultView.tsx`

## Phase 5: User Story 4 - Compare VN Stock And Gold Scope Boundaries (Priority: P2)

**Goal**: Show only the correct market inputs and workflow expectations.

**Independent Test**: Catalog and request validation permit VN stock or gold only
and identify each workflow's supported sections and limitations.

- [ ] T019 [P] [US4] Add catalog and request coverage for Phase 03 market rejection in `tests/test_app.py`
- [ ] T020 [US4] Extend market and input validation for configured gold instruments in `src/finmind_agents/workflows/validation.py`
- [x] T021 [US4] Remove unsupported catalog/provider configuration in `src/finmind_agents/dataflows/registry.py` and `src/finmind_api/settings.py`
- [ ] T022 [US4] Render field-level validation and market-specific catalog copy in `src/finmind_ui/src/features/workflows/WorkflowPage.tsx`

## Phase 6: User Story 5 - Reinspect Workflow Runs (Priority: P2)

**Goal**: Restore evidence-backed VN stock and gold runs from history.

**Independent Test**: Completed and partial runs reopen with output, citations,
artifacts, stage status, and limitations intact.

- [ ] T023 [P] [US5] Add run-history and citation-reinspection API coverage in `tests/test_app.py`
- [ ] T024 [US5] Complete persisted citation queries and market-aware run detail in `src/finmind_api/run_store.py` and `src/finmind_api/routes/runs.py`
- [ ] T025 [US5] Add workflow history selection and reinspection flow in `src/finmind_ui/src/App.tsx` and `src/finmind_ui/src/features/shell/AppShell.tsx`

## Phase 7: Polish And Verification

- [ ] T026 [P] Update workflow risk and safety mitigations in `docs/risks/RISK-001-workflow-skill-contract-drift.md`, `docs/risks/RISK-002-agent-skill-unsupported-claims.md`, and `docs/risks/RISK-004-async-stream-resource-saturation.md`
- [ ] T027 [P] Update validated Phase 03 environment configuration and manual VN/gold runtime checks in `.env` and `test.py`
- [ ] T028 Review Phase 03 safety guardrails against `.specify/memory/constitution.md` and record outcome in `specs/003-vn-gold-dataflows-workflows/plan.md`
- [ ] T029 Regenerate Phase 03 convergence and quickstart validation notes in `specs/003-vn-gold-dataflows-workflows/plan.md` and `specs/003-vn-gold-dataflows-workflows/quickstart.md`
- [ ] T030 Run backend verification for Phase 03 coverage in `tests/test_app.py` and `tests/test_platform_services.py`
- [ ] T031 Run UI build and the VN/gold validation scenarios in `specs/003-vn-gold-dataflows-workflows/quickstart.md`

## Dependencies

- Gold source definition and shared market scope (T001-T004) block all gold work.
- Gold dataflows (T005-T008) block gold workflows (T009-T013).
- VN brief work (T014-T018) can progress after the shared Phase 02 foundation.
- Scope validation (T019-T022) and reinspection (T023-T025) depend on runnable
  Phase 03 workflow contracts.
- Polish and verification (T026-T031) follow implemented user stories.

## Migration Notes

- T014-T018 replace unfinished Phase 02 T054-T061.
- T019-T022 replace unfinished Phase 02 T062-T068.
- T023-T025 replace unfinished Phase 02 T069, T071, T074-T075.
- T026-T031 replace unfinished Phase 02 T118-T120, T122-T123, and T126.
- Phase 02 chatflow T091-T099 remain Phase 04 work and are tracked in
  `../004-agentic-chatflow/tasks.md`.
