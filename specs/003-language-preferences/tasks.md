---
id: TASKS-FEAT-003
feature: language-preferences
status: complete
implements:
  - src/finmind_api/routes/preferences.py
  - src/finmind_ui/src/features/settings
  - src/finmind_agents/runtime/service.py
validated_by:
  - tests/test_app.py
  - tests/test_platform_services.py
  - src/finmind_ui/src/features/settings/i18n.test.ts
adr_refs: []
---

# Tasks: Language Preferences

These completed tasks are the focused migration of former combined Phase 03
tasks T030 through T034A.

## User Story 1 — Choose the product language

- [x] T001 Add deterministic API and service tests for preference defaulting,
  accepted updates, rejected values, and user ownership.
- [x] T002 Implement authenticated server-side preference persistence plus
  `GET` and `PUT /api/preferences/language`.
- [x] T003 Add the Settings surface with Auto-detect, English, and Vietnamese,
  immediate save behavior, and browser-language resolution.
- [x] T004 Consolidate FinMind-owned interface, workflow catalog, progress,
  validation, status, and artifact/citation chrome into typed English and
  Vietnamese catalogs with English fallback.

## User Story 2 — Capture workflow output language

- [x] T005 Thread resolved `vi | en` through workflow submission and saved
  output metadata.
- [x] T006 Add explicit model-language instructions and response-language
  validation with safe failure.
- [x] T007 Add backend and frontend coverage for workflow language capture,
  browser precedence, fallback, and explicit-selection precedence.

## User Story 3 — Preserve canonical evidence

- [x] T008 Keep canonical records, source content, citations, identifiers,
  timestamps, numbers, symbols, and historical output outside localization.
- [x] T009 Document the language-only Phase 03 boundary and move VN and Gold
  planning to their separate owners.

## Completion gate

- [x] T010 Run the complete backend suite and record the result during final
  merge-readiness verification.
- [x] T011 Run frontend tests and build and record the result during final
  merge-readiness verification.
- [x] T012 Run spec reference checks and `git diff --check` during final
  merge-readiness verification.
