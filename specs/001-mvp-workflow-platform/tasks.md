---
id: SPEC-FEAT-001-TASKS
feature: mvp-workflow-platform
status: draft
owner: solo
created: 2026-06-18
implements:
  - src/api
  - src/ui
validated_by:
  - tests/test_app.py
  - tests/test_platform_services.py
adr_refs: []
---

# Tasks: MVP Workflow Platform

## Phase 1: Setup

- [x] T001 Create `src/api/__init__.py` and `src/api/app.py` package entrypoints.
- [x] T002 [P] Create `src/api/settings.py` for `FINMIND_ADMIN_USERNAME`, `FINMIND_ADMIN_PASSWORD`, `FINMIND_SESSION_SECRET`, and V1 runtime settings.
- [x] T003 [P] Create `src/api/platform/__init__.py` for finance platform service assembly.
- [x] T004 [P] Create `src/ui/package.json` with React, Vite, TypeScript, Lucide icons, and Lightweight Charts dependencies.
- [x] T005 [P] Create `src/ui/src/main.tsx`, `src/ui/src/App.tsx`, and `src/ui/index.html` frontend entrypoints following `specs/system/ui-workbench.md`.
- [x] T006 Update `pyproject.toml` package metadata only if needed to include `src/api` and keep `src/agent_core`.

## Phase 2: Foundation

- [x] T007 Define platform domain models for sessions, instruments, seeded data records, documents, workflows, runs, evidence, citations, and artifacts in `src/api/platform/models.py`.
- [x] T008 [P] Define repository interfaces for market data, documents, runs, sessions, and workflow specs in `src/api/platform/repositories.py`.
- [x] T009 [P] Implement in-memory repository adapters with seeded/demo VN stock and gold records in `src/api/platform/memory.py`.
- [x] T010 Implement service container assembly and demo platform factory in `src/api/platform/factory.py`.
- [x] T011 Implement cookie-backed session creation, lookup, expiration, and logout support in `src/api/auth.py`.
- [x] T012 Implement FastAPI dependency guards for authenticated admin access in `src/api/dependencies.py`.
- [x] T013 [P] Define shared API response schemas for citations, freshness, artifacts, visible execution, errors, and workflow runs in `src/api/schemas.py`.
- [x] T014 [P] Create UI API client helpers for session, workflows, and runs in `src/ui/src/api/client.ts`.
- [x] T015 [P] Create shared UI layout primitives for authenticated shell, left rail, top context bar, loading state, empty state, and error state in `src/ui/src/components/layout.tsx`.
- [x] T016 Wire FastAPI route registration for auth, workflows, and runs in `src/api/routes/__init__.py`.

## Phase 3: Authentication And Shell

- [x] T017 [US2] Implement login, logout, and session endpoints in `src/api/routes/auth.py`.
- [x] T018 [US2] Apply session guards to all protected API routes in `src/api/app.py`.
- [x] T019 [P] [US2] Build login view and session bootstrap behavior in `src/ui/src/features/auth/LoginPage.tsx`.
- [x] T020 [P] [US2] Build authenticated analyst shell with workflow and results navigation in `src/ui/src/features/shell/AppShell.tsx`.
- [x] T021 [US2] Implement frontend route protection, logout behavior, and session expiration handling in `src/ui/src/App.tsx`.
- [x] T022 [US2] Ensure startup fails closed when required admin env values are missing or invalid in `src/api/settings.py`.

## Phase 4: Fixed Workflow

- [x] T023 [P] [US1] Define declarative workflow spec structures and catalog loader in `src/api/platform/workflows/specs.py`.
- [x] T024 [P] [US1] Create V1 workflow catalog entries for VN stock daily market brief, VN single-symbol research, and gold brief in `src/api/platform/workflows/catalog.py`.
- [x] T025 [US1] Implement workflow input validation and unsupported market handling in `src/api/platform/workflows/validation.py`.
- [x] T026 [P] [US1] Implement evidence and citation builders for canonical market data and source documents in `src/api/platform/evidence.py`.
- [x] T027 [P] [US1] Implement chart artifact creation from canonical price series in `src/api/platform/artifacts.py`.
- [x] T028 [US1] Implement workflow execution service with stage status, citations, freshness, artifacts, and run persistence in `src/api/platform/workflows/service.py`.
- [x] T029 [US1] Implement workflow catalog and run endpoints matching `contracts/api-contract.md` in `src/api/routes/workflows.py`.
- [x] T030 [P] [US1] Build workflow tab with workflow picker, input form, submit state, validation errors, and run status in `src/ui/src/features/workflows/WorkflowPage.tsx`.
- [x] T031 [P] [US1] Build result section renderer for cited text, freshness, visible execution status, and unsupported claims in `src/ui/src/features/results/ResultView.tsx`.
- [x] T032 [P] [US1] Build Lightweight Charts market chart component with accessible table fallback for workflow artifacts in `src/ui/src/features/charts/MarketChart.tsx`.
- [x] T033 [US1] Connect workflow page to API client and route completed runs to result inspection in `src/ui/src/App.tsx`.

## Phase 5: Validation

- [x] T034 [P] Update `README.md` with Phase 1 local setup, environment variables, API server command, UI command, and validation workflow.
- [ ] T035 Validate UI against `specs/system/ui-workbench.md` for responsive layouts, accessibility states, chart fallbacks, and no raw reasoning exposure.
- [x] T036 Run `uv run pytest` and record any remaining failures in `specs/001-mvp-workflow-platform/quickstart.md`.
- [x] T037 Run UI build and lint commands from `src/ui/package.json` and record any remaining failures in `specs/001-mvp-workflow-platform/quickstart.md`.
- [ ] T038 Validate quickstart scenarios from `specs/001-mvp-workflow-platform/quickstart.md`.

## UI Refinement: Chat-First Shell

- [ ] T039 Update `src/ui/src/App.tsx` view state so `New Chat` is the default authenticated surface and supports chat, Market, workflows, and artifact detail panel state.
- [ ] T040 Update `src/ui/src/features/shell/AppShell.tsx` to render left rail labels `New Chat`, `Market`, `Workflows`, and grouped `History` with chat conversations and workflow runs.
- [ ] T041 Create `src/ui/src/features/chat/ChatPage.tsx` with centered transcript, bottom composer, deterministic mock response handling, first-message chat titles, inline visual blocks, and artifact cards.
- [ ] T042 Create `src/ui/src/features/chat/ArtifactPanel.tsx` for desktop right-side artifact viewing and mobile full-screen artifact viewing.
- [ ] T043 Create `src/ui/src/features/data-hub/DataHubPage.tsx` with hybrid watchlist layout, system predefined VN stock/gold data, selected instrument chart, freshness metadata, news/source feed, and market table.
- [ ] T044 Refactor `src/ui/src/features/workflows/WorkflowPage.tsx` into catalog-card-first workflow selection before workflow-specific inputs.
- [ ] T045 Update `src/ui/src/styles.css` to the light professional design tokens in `specs/system/ui-workbench.md`, including responsive mobile drawer behavior.
- [ ] T046 Add or update UI tests/manual validation notes for chat mock response, artifact panel, Market real-data-only boundary, workflow catalog selection, and mobile chat-first behavior.
- [x] T047 Update the light theme and left rail to the Perplexity-inspired ledger treatment in `specs/system/ui-workbench.md`, including flat icon-and-text nav rows, one neutral selected-row state, and `History` subsections for `Chat` and `Workflow Runs`.
