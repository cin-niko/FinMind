---
id: SPEC-FEAT-003-TASKS
feature: vn-gold-dataflows-workflows
status: draft
owner: solo
created: 2026-07-12
implements: []
validated_by: []
adr_refs: []
---

# Tasks: VN And Gold Dataflows And Workflows

**Input**: Design documents from `specs/003-vn-gold-dataflows-workflows/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md),
[research.md](research.md), [data-model.md](data-model.md),
[workflow contract](contracts/workflow-contract.md), and
[conversation API contract](contracts/conversation-api.md).

**Tests**: Required. All automated tests use deterministic mocks or fixtures;
they must not call a live market, news, or model provider.

**Organization**: Tasks are grouped by user story after the shared conversation
foundation. A workflow submission always creates a new conversation; workflow
results are mapped to first assistant messages; citations/artifacts belong to
those messages.

## Format: `[ID] [P?] [Story] Description`

- **[P]** marks tasks that can run in parallel after their stated dependencies.
- **[US#]** maps a task to a feature-spec user story.

## Phase 1: Setup And Test Doubles

**Purpose**: Establish deterministic test boundaries and preserve the active
Phase 03 contract before implementation begins.

- [X] T001 Update deterministic provider/model fixture seams in `tests/conftest.py` so all Phase 03 tests block live external calls.
- [ ] T002 [P] Add deterministic XAUUSD, VN-news, valuation, timeout, and language fixtures in `tests/conftest.py` and `tests/fixtures/phase03/`.
- [ ] T003 [P] Update Phase 03 contract references and validation entry points in `specs/003-vn-gold-dataflows-workflows/quickstart.md` and `tests/test_app.py`.

---

## Phase 2: Foundational Conversation Architecture

**Purpose**: Replace the persisted run root with conversation/message ownership.
All user-story work depends on this phase.

**⚠️ CRITICAL**: Complete this phase before implementing any workflow feature.

- [X] T004 Replace `ExecutionRun` and `RunStatus` usage with typed `WorkflowResult`, `Conversation`, `Message`, `ConversationStatus`, `MessageRole`, and `MessageSourceKind` in `src/finmind_agents/models.py`.
- [X] T005 Define `ConversationRepository` and remove the public `RunRepository` protocol in `src/finmind_agents/repositories.py`.
- [X] T006 Implement deterministic `ConversationAdapter` mapping from `WorkflowResult` to a first assistant message with message-owned citations/artifacts in `src/finmind_agents/workflows/conversation_adapter.py`.
- [ ] T007 Implement PostgreSQL conversation, message, message-citation, and message-artifact persistence with owner filtering, terminal-only cascade delete, and retained `price_series_records` in `src/finmind_api/conversation_store.py`.
- [ ] T008 Add legacy `runs`/`run_citations` schema retirement without data migration in `src/finmind_api/conversation_store.py` and `tests/test_app.py`.
- [X] T009 Implement `ConversationWorkflowService` with pre-execution conversation creation, 120-second timeout, detached execution, safe interruption persistence, and startup reconciliation in `src/finmind_agents/workflows/conversation_service.py` and `src/finmind_api/app.py`.
- [X] T010 Replace run-oriented stream event models and serializers with the `conversation.*` and `message.*` event contract in `src/finmind_api/streaming.py` and `src/finmind_agents/workflows/service.py`.
- [X] T011 Replace `/runs` routing with owner-authorized conversation list/detail/delete routes and register them in `src/finmind_api/routes/conversations.py`, `src/finmind_api/routes/workflows.py`, and `src/finmind_api/routes/__init__.py`.
- [X] T012 Replace run client types and calls with `ConversationSummary`, `ConversationDetail`, `ConversationMessage`, and `ConversationStreamEvent` in `src/finmind_ui/src/api/client.ts`.
- [ ] T013 Add foundation unit and API coverage for adapter mapping, owner filtering, terminal-only delete, cascade deletion, timeout, disconnect, and restart reconciliation in `tests/test_platform_services.py` and `tests/test_app.py`.

**Checkpoint**: A deterministic workflow can create a conversation, produce a
message-bound result, survive client disconnect while the process is alive, and
be reopened or terminally deleted without `/runs` APIs.

---

## Phase 3: User Story 1 — Build Gold Evidence Dataflows (Priority: P1) 🎯 MVP

**Goal**: Collect and normalize daily XAUUSD evidence with durable provenance,
deterministic unavailable rendering, and bounded provider retries.

**Independent Test**: With only XAUUSD fixtures, collection returns daily
records with UTC `market_time`/`collected_at`, citation-ready context, and safe
unavailable/failure results without contacting a live provider.

- [X] T014 [P] [US1] Add fixture-driven XAUUSD collection, timestamp-provenance, missing-data, and two-retry failure tests in `tests/test_platform_services.py`.
- [X] T015 [US1] Add configured Gold provider selection and daily-only XAUUSD collection request validation in `src/finmind_agents/dataflows/registry.py` and `src/finmind_agents/dataflows/service.py`.
- [X] T016 [US1] Implement XAUUSD daily OHLC normalization, UTC timestamps, full returned history upsert, and no-cache/no-fallback failure behavior in `src/finmind_agents/dataflows/providers/gold.py` and `src/finmind_api/conversation_store.py`.
- [X] T017 [US1] Add Gold deterministic record rendering, `None` to `Unavailable` conversion, and citation allowlist construction in `src/finmind_agents/evidence/builders.py`, `src/finmind_agents/evidence/rendering.py`, and `src/finmind_agents/workflows/citations.py`.
- [X] T018 [US1] Add Gold dataset/instrument rejection and evidence-contract API coverage in `tests/test_app.py`.

**Checkpoint**: Gold evidence collection is independently safe and testable with
fixtures; no Gold analysis is required yet.

---

## Phase 4: User Story 2 — Mature And Extend VN Stock Workflows (Priority: P1)

**Goal**: Deliver bounded, cited VN technical/fundamental, news, valuation, and
stock-brief results with unavailable fields rendered before the LLM.

**Independent Test**: For a fixture-backed VN symbol, each workflow creates a
conversation whose first assistant message contains only cited claims or
explicit `Unavailable` markers and no trade instruction.

- [ ] T019 [P] [US2] Add deterministic fixture coverage for unavailable fields, mature technical/fundamental output, and VN stock-brief composition in `tests/test_platform_services.py`.
- [ ] T020 [P] [US2] Add fixture coverage for publisher-allowlisted news URL/title/time/content and valuation unavailable/range/sensitivity cases in `tests/test_app.py`.
- [ ] T021 [US2] Refine VN technical and fundamental workflow definitions, data requirements, and safety-only output sections in `src/finmind_agents/workflows/definitions/` and `src/finmind_agents/workflows/skills/`.
- [ ] T022 [US2] Implement configured publisher-allowlist news normalization and bounded source-document context in `src/finmind_agents/dataflows/providers/news.py` and `src/finmind_agents/dataflows/service.py`.
- [ ] T023 [US2] Implement deterministic VN valuation input gates, sector-method selection, median/P25–P75 range, and DCF sensitivity without target/recommendation output in `src/finmind_agents/workflows/valuation.py` and `src/finmind_agents/workflows/definitions.py`.
- [ ] T024 [US2] Implement the composed stock-brief workflow and message-bound citation/artifact aggregation in `src/finmind_agents/workflows/definitions.py` and `src/finmind_agents/workflows/service.py`.
- [ ] T025 [US2] Verify VN workflow API responses preserve `Unavailable`, citations, grounded output, and research-only safety behavior in `tests/test_app.py`.

**Checkpoint**: Every fixed VN workflow is independently runnable against
fixtures and produces one safe conversation result message.

---

## Phase 5: User Story 3 — Run Gold Technical Analysis (Priority: P1)

**Goal**: Render a fixed daily XAUUSD technical-analysis conversation without
stock-only sections or trading signals.

**Independent Test**: A fixture-backed Gold workflow creates a conversation with
an XAUUSD-only assistant result message, cited daily chart, and unavailable
markers where evidence is insufficient.

- [X] T026 [P] [US3] Add deterministic Gold technical workflow and chart/unavailable coverage in `tests/test_platform_services.py` and `tests/test_app.py`.
- [X] T027 [US3] Add the fixed Gold technical workflow definition, daily chart requirement, and XAUUSD-only validation in `src/finmind_agents/workflows/definitions/gold-technical-analysis.yaml` and `src/finmind_agents/workflows/validation.py`.
- [X] T028 [US3] Implement Gold technical skill context, analysis-only output rules, and stock-section exclusion in `src/finmind_agents/workflows/skills/gold-technical-analysis/SKILL.md` and `src/finmind_agents/workflows/service.py`.
- [X] T029 [US3] Render the Gold catalog card, fixed-scope confirmation dialog, and validation state in `src/finmind_ui/src/features/workflows/WorkflowPage.tsx` and `src/finmind_ui/src/features/workflows/workflowCatalog.ts`.

**Checkpoint**: Gold technical analysis can be demonstrated independently from
the catalog through a fixture-backed conversation.

---

## Phase 6: User Story 4 — Receive Language-Appropriate Output (Priority: P1)

**Goal**: Let the authenticated user manage Auto-detect, English, or Vietnamese
from Settings and capture resolved `vi`/`en` on each workflow conversation.

**Independent Test**: Settings changes immediately update UI copy; Auto-detect
uses browser precedence/fallback; a submitted workflow captures only `vi` or
`en` and its narrative follows that captured value.

- [X] T030 [P] [US4] Add deterministic API/service tests for language preference defaulting, validation, update, and conversation capture in `tests/test_app.py` and `tests/test_platform_services.py`.
- [X] T031 [US4] Implement server-side language preference persistence and authenticated `GET`/`PUT /api/preferences/language` endpoints in `src/finmind_api/preferences_store.py`, `src/finmind_api/routes/preferences.py`, and `src/finmind_api/routes/__init__.py`.
- [X] T032 [US4] Thread resolved `vi`/`en` through workflow submission, `WorkflowResult`, and the model system-language instruction in `src/finmind_agents/workflows/conversation_service.py`, `src/finmind_agents/agents/prompts.py`, and `src/finmind_agents/runtime/service.py`.
- [X] T033 [US4] Add the left-rail-footer Settings surface with Auto-detect/English/Vietnamese controls and immediate persisted updates in `src/finmind_ui/src/features/settings/LanguageSettings.tsx`, `src/finmind_ui/src/api/client.ts`, and `src/finmind_ui/src/App.tsx`.
- [X] T034 [US4] Add Settings/browser-language and workflow-language UI coverage in `src/finmind_ui/src/features/settings/i18n.test.ts` and backend language-validation tests.
- [X] T034A [US4] Consolidate FinMind-owned UI, workflow progress, deterministic
  messages, and workflow catalog copy into typed English/Vietnamese locale
  catalogs with English fallback, while leaving canonical record and citation
  content unchanged.

**Checkpoint**: Language is predictable in UI and workflow messages without
altering source evidence or historical conversations.

---

## Phase 7: User Story 5 — Inspect And Delete A Workflow Conversation (Priority: P1)

**Goal**: Let an owner reopen conversation messages/evidence and delete terminal
conversations with message-child cascade behavior.

**Independent Test**: A workflow-created conversation appears in History, shows
its first assistant message and message-owned evidence, rejects cross-owner and
active deletion, and deletes terminal children without deleting shared price data.

- [ ] T035 [P] [US5] Add deterministic conversation history, owner-filtering, terminal-delete, and canonical-price-retention tests in `tests/test_app.py` and `tests/test_platform_services.py`.
- [X] T036 [US5] Implement conversation summary/detail serializers and message-nested citations/artifacts in `src/finmind_api/schemas.py` and `src/finmind_api/routes/conversations.py`.
- [X] T037 [US5] Replace run-history hydration and artifact selection with conversation/message history in `src/finmind_ui/src/App.tsx`, `src/finmind_ui/src/features/chat/`, and `src/finmind_ui/src/api/client.ts`.
- [X] T038 [US5] Implement terminal conversation delete UI, confirmation/error states, and History removal in `src/finmind_ui/src/features/chat/ConversationHistory.tsx` and `src/finmind_ui/src/App.tsx`.
- [X] T039 [US5] Update conversation/message/citation/artifact visual states against `specs/system/ui-ux-guidelines.md` in `src/finmind_ui/src/styles.css` and `src/finmind_ui/src/features/chat/ArtifactPanel.tsx`.

**Checkpoint**: Conversation ownership, reinspection, and deletion work without
any remaining user-facing run-history surface.

---

## Phase 8: Polish And Cross-Cutting Validation

**Purpose**: Retire legacy run implementation, validate safety/performance, and
complete deterministic end-to-end coverage.

- [ ] T040 Remove legacy run persistence, routes, stream names, client types, and tests from `src/finmind_api/run_store.py`, `src/finmind_api/routes/runs.py`, `src/finmind_agents/repositories.py`, and `src/finmind_ui/src/api/client.ts`.
- [ ] T041 [P] Verify no `partial` terminal status, raw reasoning, provider payload, target price, recommendation, or trade instruction remains in `src/finmind_agents/`, `src/finmind_api/`, and `src/finmind_ui/`.
- [ ] T042 [P] Add deterministic regression coverage for 1-second conversation start visibility and 120-second terminal timeout in `tests/test_app.py` and `tests/test_platform_services.py`.
- [ ] T043 Run backend validation with `uv run pytest` and record results in `specs/003-vn-gold-dataflows-workflows/quickstart.md`.
- [ ] T044 Run frontend tests and build from `src/finmind_ui/` using commands in `src/finmind_ui/package.json`, then record results in `specs/003-vn-gold-dataflows-workflows/quickstart.md`.
- [ ] T045 Perform and record the separate live-provider contract check without adding it to automated tests in `specs/003-vn-gold-dataflows-workflows/quickstart.md`.

---

## Dependencies And Execution Order

```text
Setup (T001–T003)
  -> Foundation (T004–T013)
      -> US1 Gold evidence (T014–T018)
          -> US3 Gold technical analysis (T026–T029)
      -> US2 VN workflows (T019–T025)
      -> US4 Language settings and localized presentation (T030–T034A)
      -> US5 Conversation inspection/delete (T035–T039)
  -> Polish (T040–T045)
```

### User Story Dependencies

- **US1** starts after the foundation and is the suggested MVP. It is required
  before US3.
- **US2**, **US4**, and **US5** start after the foundation and can proceed in
  parallel with US1 if capacity allows.
- **US3** starts after US1.
- **Polish** starts after every selected story is complete.

## Parallel Opportunities

- T002 and T003 can run in parallel after T001.
- T014 and T018 can run in parallel before the US1 implementation tasks.
- T019 and T020 can run in parallel before the US2 implementation tasks.
- T026 can begin after US1; T030 and T035 can run in parallel after the
  foundation.
- T041 and T042 can run in parallel after feature implementation.

## Implementation Strategy

### MVP First

1. Complete Setup and Foundation.
2. Complete US1 and validate deterministic Gold collection independently.
3. Demonstrate a fixture-backed Gold dataflow with provenance and safe failure.

### Incremental Delivery

1. Add US2 for complete VN research workflows.
2. Add US3 for the fixed Gold analysis experience.
3. Add US4 Settings and language capture.
4. Add US5 History/reinspection/deletion.
5. Complete cross-cutting migration, safety, performance, and deterministic
   validation.

## Notes

- Every task uses the required checkbox, ID, optional parallel marker, story
  label where applicable, and exact path format.
- Do not implement the old superseded run-based task list; this file is the
  authoritative Phase 03 execution order.
