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

Build workflow/chatflow as a thin orchestration surface over shared evidence,
citations, artifacts, freshness, execution records, and real-time retrieval
tools. Phase 002 market-data persistence is pending, so M1 must not depend on a
populated canonical price database.

## Architecture

- `src/api/platform/tools/realtime_market.py`: real-time retrieval tool contract returning structured evidence payloads
- `src/api/platform/chat/roles.py`: role-agent contracts for fundamental, technical, macro, and risk roles
- `src/api/platform/chat/service.py`: chat/workflow orchestration service reusing workflow/evidence/artifact services and retrieval tools
- `src/api/platform/chat/scope.py`: unsupported market and instrument response handling
- `src/api/platform/chat/artifacts.py`: inline visualization artifact builder
- `src/api/routes/chat.py`: chat endpoint
- `src/ui/src/features/chat/ChatPage.tsx`: chat UI
- `src/ui/src/features/chat/InlineArtifact.tsx`: inline chart/table/computed-result renderer

## Gates

- Chat cannot invent unsupported claims.
- Chat must use shared evidence and freshness contracts.
- Unsupported US stock and BTC questions must return V1 scope limitations.
- Raw agent reasoning is not displayed.
- Retrieval tool failures/rate limits are surfaced as unavailable-data states.
- Demo market fixtures are not used as fallback evidence.
