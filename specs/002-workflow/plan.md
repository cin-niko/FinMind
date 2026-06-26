---
id: SPEC-FEAT-002-PLAN
feature: workflow
status: draft
owner: solo
created: 2026-06-26
implements: []
validated_by: []
adr_refs: []
---

# Implementation Plan: Workflow

## Summary

Plan phase 02 fixed workflow execution for VN stocks and US stocks only:
catalog, input validation, seeded/demo canonical records, evidence objects,
citations, freshness, chart artifacts, run persistence, and result inspection.

## Technical Context

- Backend: FastAPI routes, platform services, in-memory/demo repositories,
  workflow catalog, validation, evidence, citations, artifacts, and run storage.
- Frontend: workflow catalog, workflow input form, result view, chart rendering,
  run history integration through the MVP UI shell.
- Testing: `tests/test_platform_services.py` and API tests that exercise workflow
  routes.
- Implementation state: not treated as complete in this split. Existing code may
  contain earlier workflow experiments, but phase 02 requires a fresh plan against
  this draft spec before implementation alignment.
- Performance target: seeded/demo workflow execution and result inspection remain
  responsive for bounded local/demo datasets.

## Constitution Check

- Code quality: workflow models, validation, repository state, evidence, and UI
  workflow components remain separately owned.
- Testing standards: workflow catalog, validation, artifacts, citations, and run
  inspection require automated coverage.
- Safety guardrails: unsupported markets are blocked, citations/freshness are
  visible, raw reasoning is excluded, and no trading action exists.
- UX consistency: workflow surfaces follow `../system/ui-ux-guidelines.md`.
- Performance: bounded seeded/demo data keeps MVP workflow latency constrained;
  live data targets need a later spec.
- Traceability: shared entities and contracts are linked to `../system/`.

Gate result: draft only. Run `/speckit-plan` for phase 02 before implementation.

## Documentation Dependencies

- System state: `../system/state-model.md`
- Contracts: `../system/contracts.md`
- Runtime/security: `../system/runtime-config-security.md`
- UI/UX: `../system/ui-ux-guidelines.md`
