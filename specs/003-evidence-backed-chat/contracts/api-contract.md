---
id: SPEC-FEAT-003-CONTRACTS
feature: evidence-backed-chat
status: draft
owner: solo
created: 2026-06-18
implements: []
validated_by:
  - tests/test_app.py
adr_refs: []
---

# API Contract: Evidence-Backed Chat

All endpoints require an active session.

## `POST /api/chat`

Runs evidence-backed chat orchestration.

Request includes:

- `message`

Response includes:

- `id`
- `kind: chat`
- `status`
- cited answer text or scope-limitation response
- citations
- freshness
- inline artifacts
- visible role-agent/tool status

Unsupported market questions return a successful scoped response or validation error with a clear limitation, not fabricated analysis.
