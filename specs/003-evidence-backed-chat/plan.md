---
id: SPEC-FEAT-003-PLAN
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

# Implementation Plan: Evidence-Backed Chat

## Summary

Build chat as a thin orchestration surface over workflow evidence, citations, artifacts, freshness, and execution records. Because Phase 002 data operations are parked, M1 uses real-time retrieval tools as its market-data source of truth and records their outputs as structured evidence payloads.

## Architecture

- `src/api/platform/chat/roles.py`: role-agent contracts for fundamental, technical, macro, and risk roles
- `src/api/platform/chat/service.py`: chat orchestration service reusing workflow/evidence/artifact services
- `src/api/platform/tools/realtime_market.py`: retrieval tool contract returning structured evidence payloads for M1 market questions
- `src/api/platform/chat/scope.py`: unsupported market and instrument response handling
- `src/api/platform/chat/artifacts.py`: inline visualization artifact builder
- `src/api/routes/chat.py`: chat endpoint
- `src/ui/src/features/chat/ChatPage.tsx`: chat UI
- `src/ui/src/features/chat/InlineArtifact.tsx`: inline chart/table/computed-result renderer

## Gates

- Chat cannot invent unsupported claims.
- Chat must use shared evidence and freshness contracts.
- Retrieval tool failures, rate limits, and insufficient data must surface as unavailable-data states.
- Chat must not use demo market fixtures as fallback evidence.
- Unsupported US stock and BTC questions must return V1 scope limitations.
- Raw agent reasoning is not displayed.
