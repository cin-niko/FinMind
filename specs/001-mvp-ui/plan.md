---
id: SPEC-FEAT-001-PLAN
feature: mvp-ui
status: active
owner: solo
created: 2026-06-26
implements:
  - src/ui
  - src/api
validated_by:
  - tests/test_app.py
adr_refs: []
---

# Implementation Plan: MVP UI

## Summary

Document the implemented authenticated app shell, login/session behavior, left
rail, chat-first mock UI, history layout, mock artifact detail behavior, and light
ledger visual treatment.

## Technical Context

- Backend: FastAPI session endpoints and auth dependencies.
- Frontend: React/Vite app shell, login, shell navigation, mock chat components,
  artifact detail UI.
- Testing: `tests/test_app.py` plus frontend build/type checks.
- Performance target: login, shell navigation, mock chat rendering, and artifact
  detail interactions remain responsive with small local/demo state.

## Constitution Check

- Code quality: auth/session and UI shell ownership are separated.
- Testing standards: auth/session behavior is covered; UI build remains required.
- Safety guardrails: raw reasoning, secrets, and arbitrary generated HTML are not
  exposed.
- UX consistency: shell follows `../system/ui-ux-guidelines.md`.
- Performance: MVP UI uses bounded local/demo state.
- Traceability: shared rules are in `../system/`; UI behavior is in this feature.

Post-design check: no constitution gate violations are open.

## Documentation Dependencies

- Runtime/security: `../system/runtime-config-security.md`
- UI/UX: `../system/ui-ux-guidelines.md`
- State: `../system/state-model.md`
