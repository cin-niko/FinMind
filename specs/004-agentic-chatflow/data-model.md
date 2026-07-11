---
id: SPEC-FEAT-004-DATA
feature: agentic-chatflow
status: draft
owner: solo
created: 2026-06-26
implements: []
validated_by: []
adr_refs: []
---

# Data Model: Agentic Chatflow

This draft extends the shared entities in `../system/state-model.md`. Final
retention, source, and tool choices remain Phase 04 planning gates.

## ChatflowRunRequest

- `run_id`, `conversation_id`, `message_id`, `user_message`, `market_context`,
  `policy_id`, `streaming_requested`, `prior_messages`, and `output_schema`.
- The route identifies the conversation by `chat_id`; authenticated ownership is
  required before accepting a message.
- Prior messages contain safe persisted content only, never raw reasoning.

## ChatConversation

- `chat_id`, `owner_user_id`, `title`, `created_at`, `updated_at`, and `status`
  (`active` or `archived`).
- Ownership is checked before messages or history are returned.

## ChatMessage

- `message_id`, `chat_id`, optional `run_id`, `role`, `content`, optional
  `market_context`, citations, `created_at`, and status.
- Supported roles are `user`, `assistant`, and `system_status`; statuses are
  `submitted`, `streaming`, `completed`, `partial`, and `failed`.
- Assistant output is reconciled from safe stream events and final persisted
  run/message output. Secrets, prompts, raw reasoning, and unsafe diagnostics
  are never persisted as messages.

## ExecutionRun And StreamEvent Usage

- `ExecutionRun` uses the shared run model with `kind: chatflow`, optional
  `conversation_id`, owned status, citations, artifacts, collection metadata,
  and safe final output.
- `StreamEvent` retains monotonic sequence, safe event kind, timestamp, and
  payload rules from the Phase 02 streaming foundation.
- Stream output must reconcile with the persisted run and message; request-
  scoped streams are not assumed replayable after disconnect or restart.

## Evidence And Output Usage

- `Citation`, `GroundingCheck`, `Artifact`, `SourceDocument`, and
  `CanonicalMarketDataRecord` use the shared evidence contract.
- Every material claim cites an allowed collected source or is explicitly marked
  unsupported/unavailable.
- Phase 04 begins with the mature VN stock and gold source boundary from Phase
  03 unless a later approved spec expands it.
