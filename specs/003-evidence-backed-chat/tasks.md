---
id: SPEC-FEAT-003-TASKS
feature: evidence-backed-chat
status: draft
owner: solo
created: 2026-06-18
implements: []
validated_by:
  - tests/test_app.py
  - tests/test_platform_services.py
adr_refs: []
---

# Tasks: Evidence-Backed Chat

- [ ] T001 [P] Define role-agent orchestration contracts for fundamental, technical, macro, and risk roles in `src/api/platform/chat/roles.py`.
- [ ] T002 Implement chat orchestration service that can reuse workflow/evidence/artifact services in `src/api/platform/chat/service.py`.
- [ ] T003 Implement unsupported market and unsupported instrument response handling in `src/api/platform/chat/scope.py`.
- [ ] T004 [P] Implement inline visualization artifact builder for chat outputs in `src/api/platform/chat/artifacts.py`.
- [ ] T005 Implement chat endpoint matching `contracts/api-contract.md` in `src/api/routes/chat.py`.
- [ ] T006 [P] Build chat page with message composer, answer stream area, citations, freshness, role status, and inline artifacts in `src/ui/src/features/chat/ChatPage.tsx`.
- [ ] T007 [P] Build inline artifact renderer for chart, table, and computed-result payloads in `src/ui/src/features/chat/InlineArtifact.tsx`.
- [ ] T008 Connect chat page to API client and result inspection flow in `src/ui/src/App.tsx`.
- [ ] T009 Validate quickstart scenarios from `specs/003-evidence-backed-chat/quickstart.md`.
