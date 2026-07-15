---
id: SPEC-FEAT-003-CONVERSATION-API
feature: vn-gold-dataflows-workflows
status: draft
owner: solo
created: 2026-07-12
implements: []
validated_by: []
adr_refs: []
---

# Conversation API Contract

This is the Phase 03 wire contract for workflow-created conversations. Shared
entity semantics live in [`../../system/state-model.md`](../../system/state-model.md);
workflow behavior lives in [`workflow-contract.md`](workflow-contract.md).

## Type Interfaces

```text
ConversationStatus = "queued" | "running" | "success" | "failed"
MessageRole = "user" | "assistant"
MessageSourceKind = "workflow_result" | "chat"
LanguageSelection = "auto" | "vi" | "en"

LanguagePreference {
  selection: LanguageSelection
}

ConversationSummary {
  id, title, workflow_id?, status, output_language?, created_at, updated_at
}

ConversationDetail extends ConversationSummary {
  inputs?, started_at?, completed_at?, stage_status, messages
}

ConversationMessage {
  id, conversation_id, role, source_kind, workflow_id?, status?,
  content, created_at, citations?, artifacts?
}

ConversationStreamEvent {
  event_id, conversation_id, sequence, created_at,
  kind: "conversation.started" | "conversation.stage" |
        "message.delta" | "message.created" | "citation" |
        "artifact" | "conversation.completed" | "conversation.failed",
  payload
}
```

`WorkflowResult` is not a response type. It is mapped by the server-side
conversation adapter to `ConversationMessage` before persistence or delivery.

## Endpoints

### Create a workflow conversation

`POST /api/workflows/{workflow_id}/conversations`

- Requires an authenticated user and valid workflow inputs plus resolved
  `language` (`vi` or `en`).
- Creates a new owned conversation before execution and returns an SSE stream.
- The first event is `conversation.started` and includes the new
  `conversation_id`.
- A successful terminal event includes the adapter-created first assistant
  message. A failed terminal event includes only a product-facing failure
  summary; no raw exception, provider payload, or reasoning is exposed.
- Closing the SSE client does not delete or cancel the conversation.

### List and inspect conversations

`GET /api/conversations`

- Returns only summaries owned by the authenticated user, newest first.

`GET /api/conversations/{conversation_id}`

- Returns a detail record only when the authenticated user owns it; otherwise
  responds as not found.
- Includes messages. Citations and artifacts are nested only on their owning
  assistant message.

### Read and update language preference

`GET /api/preferences/language`

- Returns the authenticated user's saved `LanguagePreference`.
- A user with no saved preference receives and persists `selection: "auto"`.

`PUT /api/preferences/language`

- Accepts exactly one `selection`: `auto`, `vi`, or `en`.
- Updates only the authenticated user's preference and returns the saved value.
- The UI resolves `auto` from the browser at display/submission time; it sends
  only resolved `vi` or `en` with a workflow conversation submission.

### Delete a conversation

`DELETE /api/conversations/{conversation_id}`

- Owner-only.
- Allowed only for `success` or `failed` conversations.
- Cascade-deletes messages, message citations, message artifacts, and execution
  metadata. It retains shared canonical market data.
- A `queued` or `running` conversation is rejected because Phase 03 has no
  cancellation endpoint.

## Compatibility Boundary

Phase 03 removes `POST /api/workflows/{workflow_id}/runs`, `GET /api/runs`,
`GET /api/runs/{run_id}`, and `GET /api/runs/{run_id}/citations`. No API alias
is retained. Existing persisted run history is not migrated.
