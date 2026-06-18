---
id: SPEC-FEAT-001-PLAN
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

# Implementation Plan: MVP Workflow Platform

## Summary

Build the first FinMind platform slice with FastAPI JSON APIs, React/Vite UI, cookie-backed sessions, seeded/demo canonical VN stock and gold data, fixed workflow execution, evidence/citation/artifact contracts, chart rendering, and result inspection. Keep admin ingestion, chat, and plugin hardening outside this feature.

## Technical Context

- Backend: Python 3.12, FastAPI, Pydantic, pydantic-settings, uvicorn
- Frontend: TypeScript, React/Vite, Lucide icons, Lightweight Charts
- Existing substrate: `src/agent_core`
- Storage: in-memory/demo repository contracts in this feature, designed for later durable storage
- Testing: pytest for backend/API/service contracts; UI build/lint and targeted browser validation when UI exists

## Architecture

- `src/agent_core`: reusable model, tool, streaming, settings, and artifact substrate
- `src/api`: FastAPI app, auth, schemas, finance platform models, repositories, workflow services, result APIs
- `src/ui`: authenticated analyst shell, login, workflow, result, chart components

## Gates

- Authentication: all protected content requires cookie-backed session.
- Evidence: material claims require citations or unsupported/unavailable marking.
- Scope: VN stocks and gold only; US stocks and BTC are roadmap.
- Reasoning: raw agent reasoning is not user-visible.
- Layering: finance workflow semantics stay above `agent_core` unless genuinely reusable.

## Documentation Dependencies

- System state: `../system/state-model.md`
- Contracts: `../system/contracts.md`
- Runtime/security: `../system/runtime-config-security.md`
- UI: `../system/ui-workbench.md`
