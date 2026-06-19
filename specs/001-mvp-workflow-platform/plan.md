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

Build the first FinMind platform slice with FastAPI JSON APIs, React/Vite UI, cookie-backed sessions, a chat-first shell with deterministic mock chat artifacts, a real-data Market surface for seeded/demo VN stock and gold data, fixed workflow execution, evidence/citation/artifact contracts, chart rendering, and result inspection. Keep admin ingestion, production evidence-backed chat, arbitrary LLM-generated HTML, and plugin hardening outside this feature.

## Technical Context

- Backend: Python 3.12, FastAPI, Pydantic, pydantic-settings, uvicorn
- Frontend: TypeScript, React/Vite, Lucide icons, Lightweight Charts
- Existing substrate: `src/agent_core`
- Storage: in-memory/demo repository contracts in this feature, designed for later durable storage
- Testing: pytest for backend/API/service contracts; UI build/lint and targeted browser validation when UI exists

## Architecture

- `src/agent_core`: reusable model, tool, streaming, settings, and artifact substrate
- `src/api`: FastAPI app, auth, schemas, finance platform models, repositories, workflow services, result APIs
- `src/ui`: authenticated analyst shell, login, chat mock surface, Market, workflow catalog, result, chart components

## Gates

- Authentication: all protected content requires cookie-backed session.
- Evidence: material claims require citations or unsupported/unavailable marking.
- Scope: VN stocks and gold only; US stocks and BTC are roadmap.
- Reasoning: raw agent reasoning is not user-visible.
- Chat safety: V1 chat renders deterministic trusted mock artifacts only; no arbitrary LLM HTML execution.
- Market boundary: Market displays real seeded/demo data only and excludes generated prose or recommendations.
- Layering: finance workflow semantics stay above `agent_core` unless genuinely reusable.

## UI/UX Refinement Plan

### Shell

- Replace the current workflow-first shell with a chat-first shell.
- Left rail labels: `New Chat`, `Market`, `Workflows`, `History`.
- `History` groups `Chats` and `Workflow Runs` under one section.
- Default post-login surface: `New Chat`.
- Desktop artifact detail opens in a right-side split panel; mobile artifact detail opens full-screen.

### Chat

- Implement a simple centered chat layout with bottom composer.
- Use deterministic mock responses for V1.
- Use the first user message as the chat history title.
- Render trusted local-template inline visuals inside chat answers.
- Render report, chart, table, evidence list, and citation bundle artifact cards inside chat answers.
- Clicking an artifact card opens the full mock artifact in the right-side panel.
- Do not connect Chat to Market context in V1.
- Do not execute arbitrary LLM-generated HTML in V1.

### Market

- Implement a hybrid watchlist dashboard: summary cards above denser chart/feed/table detail.
- Use system-predefined VN stock and gold instruments in V1.
- Show real seeded/demo data only: market snapshots, selected instrument chart, freshness metadata, source/news feed, and market table.
- Exclude LLM summaries, recommendations, and chat-generated content.

### Workflows

- Present fixed system-defined workflows as catalog cards.
- Clicking a card opens workflow-specific inputs and run action.
- Workflow results may contain generated/cited output and remain separate from Market.

### Visual Theme

- Use the Perplexity-inspired light ledger theme defined in `../system/ui-workbench.md`.
- Use warm off-white surfaces, charcoal text, a quiet neutral rail, restrained teal focus/selection accents, and amber/brass only for workflow actions, warnings, freshness, and coverage states.
- Keep green/red reserved for market direction and success/failure states.
- Avoid decorative gradients, marketing hero sections, and AI-purple visual language.

## Documentation Dependencies

- System state: `../system/state-model.md`
- Contracts: `../system/contracts.md`
- Runtime/security: `../system/runtime-config-security.md`
- UI: `../system/ui-workbench.md`
