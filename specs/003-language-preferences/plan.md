---
id: PLAN-FEAT-003
feature: language-preferences
status: active
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

# Implementation Plan: Language Preferences

## Summary

Phase 03 adds a server-persisted `auto | vi | en` preference, deterministic
browser resolution to `vi | en`, typed UI catalogs with English fallback, and
immutable capture of effective language at workflow submission. It localizes
FinMind-owned presentation only and preserves canonical evidence.

## Technical context

- Backend: FastAPI preference endpoints backed by the existing authenticated
  record repository.
- Frontend: React/TypeScript language selection, resolver, locale catalogs, and
  Settings UI.
- Workflow runtime: validated `vi | en` request context, explicit system-language
  instruction, and output-language validation.
- Tests: deterministic Python API/service tests plus TypeScript catalog and
  browser-resolution tests.

## Constitution check

- Advice, not decision: language changes presentation, not financial intent.
- Data driven: canonical evidence is never translated or mutated.
- Claims with citations: language does not weaken the shared citation contract.
- Human control: the user explicitly chooses or retains Auto-detect.
- No raw reasoning: neither localized UI nor failures expose model reasoning.
- Specs before code: this focused spec records the behavior already delivered
  during the former combined Phase 03 implementation.

## Design

1. Persist `selection`, not a browser-derived value. This lets Auto-detect
   resolve appropriately on each device while retaining the user's intent.
2. Resolve Auto-detect in ordered browser-language precedence and fall back to
   English deterministically.
3. Send only effective `vi | en` at workflow submission. The server validates
   and captures it independently of presentation labels.
4. Resolve stable UI keys through typed locale catalogs. English is the
   deterministic missing-key fallback.
5. Keep canonical evidence and saved historical output outside localization.

## Ownership boundaries

- Shared entity definitions: `../system/state-model.md`
- Shared API index: `../system/contracts.md`
- Shared UI behavior: `../system/ui-ux-guidelines.md`
- Workflow foundation: `../002-workflow/`
- Future VN and Gold workflow consumers: separately merged bounded feature
  specifications

## Verification gate

Phase 03 is merge-ready only when backend tests, frontend tests, frontend build,
link/reference checks, and `git diff --check` pass. A live provider check is not
required for this language-only feature.
