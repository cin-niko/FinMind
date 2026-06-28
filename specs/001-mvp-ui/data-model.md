---
id: SPEC-FEAT-001-DATA
feature: mvp-ui
status: active
owner: solo
created: 2026-06-26
implements:
  - src/finmind_ui
validated_by: []
adr_refs: []
---

# Data Model: MVP UI

This feature uses canonical entities from `../system/state-model.md`.

Feature-owned usage:

- `InternalAdminUser`: environment-configured login identity.
- `Session`: authenticated shell access.
- `MockChatConversation`: deterministic client-side conversation.
- `ChatMessage`: user and deterministic assistant messages.
- `ChatArtifact`: trusted mock report, chart, table, evidence list, or citation
  bundle rendered by local templates.

Workflow execution state belongs to `../002-workflow/`. Production chat execution
state belongs to `../003-agentic-chatflow/`.
