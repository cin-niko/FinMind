---
id: SPEC-FEAT-004-TASKS
feature: agentic-chatflow
status: draft
owner: solo
created: 2026-06-26
implements: []
validated_by: []
adr_refs: []
---

# Tasks: Agentic Chatflow

**Input**: Draft artifacts in `specs/004-agentic-chatflow/` and the completed
Phase 02/03 workflow evidence foundation.

## Phase 1: Resolve Planning Gates

- [ ] T001 Run clarification for trusted sources, collection behavior, retention, evaluation thresholds, and chat-specific market policy in `specs/004-agentic-chatflow/spec.md`
- [ ] T002 Update source, citation, tool, retention, and performance decisions in `specs/004-agentic-chatflow/research.md`
- [ ] T003 Update production conversation/message/run entities in `specs/004-agentic-chatflow/data-model.md`
- [ ] T004 Update chatflow stream, persistence, and safety contracts in `specs/004-agentic-chatflow/contracts/chatflow-contract.md`
- [ ] T005 Complete implementation planning only after T001-T004 resolve the Phase 04 gates in `specs/004-agentic-chatflow/plan.md`

## Phase 2: Grounded Chatflow Contract And Evaluation

- [ ] T006 [P] Define grounded-answer, unsupported-claim, citation, and safety-refusal evaluation cases in `specs/004-agentic-chatflow/research.md`
- [ ] T007 [P] Add chatflow stream event and fail-closed adapter validation coverage in `tests/test_app.py` and `tests/test_platform_services.py`
- [ ] T008 Define chatflow run/message service boundaries over the shared runtime in `src/finmind_agents/chatflow/service.py`
- [ ] T009 Define conversation/message API routes and response schemas in `src/finmind_api/routes/` and `src/finmind_api/schemas.py`
- [ ] T010 Define persisted conversation, message, and chatflow-run metadata support in `src/finmind_api/run_store.py`

## Phase 3: Streaming Chat Experience And Reinspection

- [ ] T011 Add chat-message stream handling, progress/answer/citation/artifact reconciliation, and fail-closed states in `src/finmind_ui/src/api/client.ts`
- [ ] T012 Add persisted conversation reopening, run-history linkage, and citation/artifact inspection in `src/finmind_ui/src/features/chat/ChatPage.tsx` and `src/finmind_ui/src/features/shell/AppShell.tsx`
- [ ] T013 Decide whether Phase 04 needs a streaming mock distinct from the `001-mvp-ui` deterministic mock and document the outcome in `specs/004-agentic-chatflow/plan.md`

## Phase 4: Implementation Gate

- [ ] T014 Begin production chatflow implementation only after Phase 04 source, safety, evaluation, and performance gates pass in `specs/004-agentic-chatflow/plan.md`

## Migration Notes

- T007 replaces Phase 02 T091-T094.
- T008-T010 replace Phase 02 T095-T097.
- T013 replaces Phase 02 T098.
- T011-T012 replace Phase 02 T099.
