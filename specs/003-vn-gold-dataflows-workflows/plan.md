---
id: SPEC-FEAT-003-PLAN
feature: vn-gold-dataflows-workflows
status: draft
owner: solo
created: 2026-07-11
implements: []
validated_by: []
adr_refs: []
---

# Implementation Plan: VN And Gold Dataflows And Workflows

**Branch**: `main` | **Date**: 2026-07-12 | **Spec**: [`spec.md`](spec.md)

**Input**: Phase 03 specification and shared system contracts.

## Summary

Implement bounded VN-stock and XAUUSD workflows with deterministic evidence,
language-aware narrative, and a conversation-based persistence model. A workflow
continues to produce a `WorkflowResult`; a new adapter maps that result to the
first assistant message in a newly created conversation. The implementation
replaces persisted workflow runs/history with owner-authorized conversations and
message-owned citations/artifacts, while retaining shared canonical market data.

## Decision Review — Most Likely To Change

These are the product and type decisions to approve before task generation. The
remaining implementation sequence follows them; no unresolved clarification
blocks planning.

### 1. Conversation and message persistence model

```text
Workflow submission
  -> new Conversation (owner, workflow metadata, status)
  -> WorkflowResult (transient execution output)
  -> ConversationAdapter
  -> first assistant Message
  -> message-owned CitationSnapshot and Artifact
```

- Every workflow submission creates a new conversation, even when another
  conversation is open.
- `WorkflowResult` remains an internal workflow boundary; it is neither a
  persisted history root nor a message.
- `Conversation` owns ordered messages and lifecycle state. `Message` owns its
  citations and artifacts. A later Phase 04 chat reply uses the same `Message`
  type.
- A terminal conversation is retained until its owner deletes it. Deletion
  cascades through messages to their citations/artifacts and execution metadata;
  shared canonical price records and source records are retained.
- Delete is rejected while the conversation is `queued` or `running`, because
  Phase 03 deliberately has no cancellation behavior.
- Legacy `runs`/`run_citations` history is not migrated. The Phase 03 database
  migration starts conversation history empty; this is appropriate for the
  current single-user V1/dev data. Changing that decision requires an explicit
  legacy-data migration policy before implementation.

### 2. New Python and TypeScript interfaces

The implementation introduces the following canonical application interfaces;
their wire representations are specified in
[`contracts/conversation-api.md`](contracts/conversation-api.md).

| Boundary | Planned interface | Responsibility |
|---|---|---|
| Workflow | `WorkflowResult` | Transient structured workflow output: status, sections, stage state, citations, artifacts, language, failure summary. |
| Adapter | `ConversationAdapter` | Deterministically maps one `WorkflowResult` into one assistant `Message`, then assigns citations/artifacts to that message. |
| Domain | `Conversation`, `Message`, `ConversationStatus`, `MessageRole`, `MessageSourceKind` | Typed persisted model and user-facing state. |
| Repository | `ConversationRepository` | Create, update lifecycle, append result message, get/list by owner, delete terminal conversation, reconcile interrupted conversations, and persist canonical price series. |
| Service | `ConversationWorkflowService` | Creates a conversation before execution, launches bounded work independent of the SSE connection, publishes safe events, and delegates persistence to the adapter/repository. |
| UI | `ConversationSummary`, `ConversationDetail`, `ConversationMessage`, `ConversationStreamEvent` | Replaces `WorkflowRun` client types, `/runs` calls, and run-history hydration. |
| Preferences | `LanguageSelection`, `LanguagePreference` | Persisted `auto`/`vi`/`en` selection and its authenticated settings API/UI boundary. |

`ExecutionRun`, `RunRepository`, `PostgresRunRepository`, `WorkflowRun`, and
run-oriented stream/API types are removed or renamed as part of the mechanical
migration described later. No compatibility alias is kept: Phase 03 removes the
run product contract rather than supporting two persistence roots.

### 3. User-facing workflow behavior

- Clicking **Run** creates a conversation immediately and opens it in the chat
  work area. The workflow catalog remains the submission surface.
- The conversation shows safe stage progress while its status is `queued` or
  `running`. On completion, its first assistant message renders the result;
  citations and artifacts appear on that message.
- History contains conversations, not a separate workflow-runs list. A terminal
  conversation shows delete; unavailable evidence remains visible in a successful
  conversation and never becomes a `partial` status.
- The UI sends resolved `vi` or `en` at submission. The backend captures it on
  the conversation and injects it into the model system-language instruction.
- Auto-detect remains the saved default selection, resolving the browser's first
  supported `vi-*`/`en-*` language or `en` as fallback.
- Settings opens from the left rail footer. It provides Auto-detect, English,
  and Vietnamese, saves selection immediately through the preference API, and
  updates web copy without changing historical conversation messages.
- A typed frontend locale catalog owns FinMind UI copy. Workflow progress maps
  stable stage/status identifiers to localized labels; API and core workflow
  contracts remain language-neutral. The model prompt localizes generated
  narrative while explicitly preserving canonical record fields/content and
  citation evidence in English or its provided source representation.

### 4. Lifecycle and provider behavior

- Every workflow conversation has a 120-second end-to-end timeout; timeout is
  an inspectable `failed` conversation.
- A client disconnect only closes that SSE subscription. Execution continues in
  the application process while it remains alive; the client may inspect the
  conversation afterward.
- On application startup, persisted `queued`/`running` conversations from a
  prior process are marked `failed` with a safe interruption summary. There is
  no resume.
- Collection makes an initial attempt plus at most two retries for transient
  provider failures. Invalid input, missing required evidence, unsupported scope,
  safety failure, and language failure are not retryable. No cache or fallback
  provider is silently substituted.
- No cancellation endpoint, idempotency key, queue limit, or concurrency limit
  is added in Phase 03. Existing request stream limiting is removed from the
  product contract; implementation may retain only infrastructure protection
  that does not change this product behavior.

## Technical Context

**Language/Version**: Python 3.12 backend; TypeScript/React frontend.

**Primary Dependencies**: FastAPI, Pydantic, psycopg/PostgreSQL, LangChain/
LiteLLM runtime, Vite/React, pytest, Node test/build tooling.

**Storage**: PostgreSQL conversation store with messages, message citations,
message artifacts, and shared canonical `price_series_records`.

**Testing**: pytest plus frontend tests/build. All automated tests use
deterministic mocks/fixtures for provider and model behavior; no live network
dependency.

**Target Platform**: Authenticated web workbench served by FastAPI with Vite
frontend.

**Project Type**: Web application with Python API/agent layers and TypeScript UI.

**Performance Goals**:

- Persist and expose the new conversation/progress state within 1 second of a
  valid local workflow submission.
- A workflow reaches a terminal status within 120 seconds.
- Reopening a persisted conversation displays its stored first message, citations,
  and artifacts without refetching provider data.

**Constraints**:

- Scope is VN stocks and XAUUSD Gold only.
- No raw reasoning, secrets, provider dumps, trading actions, target prices, or
  recommendations.
- `partial` is not a terminal status; unavailable is field/section evidence
  state.
- Live provider checks are recorded operational validation, never CI input.

**Scale/Scope**: One authenticated V1 user; ownership filtering is enforced in
the data/query boundary for future multi-user support. Five fixed workflows:
existing VN technical/fundamental plus VN news, valuation, stock brief, and Gold
technical analysis.

## Constitution Check — Pre-Design

- **Code quality — PASS**: Conversation, message, adapter, workflow, repository,
  API, and UI ownership are separated. Shared entities remain in system specs.
- **Testing standards — PASS**: pytest and frontend verification are required;
  deterministic mocks/fixtures are mandatory for automated coverage.
- **Safety guardrails — PASS**: Grounding, citations, unavailable rendering,
  no-raw-reasoning, research-only output, and no-silent-fallback remain required.
- **UX consistency — PASS**: Conversation history, message-bound evidence,
  visible stages, terminal failures, and delete behavior extend the shared UI
  guidelines.
- **Performance requirements — PASS**: 1-second initial progress and 120-second
  terminal timeout are explicit.
- **Spec traceability — PASS**: System state/contracts/data-record flow and the
  Phase 03 artifacts own the behavior. No ADR or risk exception is required.

## Research Decisions

[`research.md`](research.md) is the Phase 0 decision record. Its implementation
decisions are now resolved as follows:

- Daily XAUUSD OHLC only; retain the fullest source history returned and do not
  offer multi-timeframe controls.
- Use the configured Twelve Data connector for the daily XAUUSD series; select
  it explicitly in runtime configuration and fail closed when its credential is
  missing or invalid.
- `market_time` is displayed as evidence time; `collected_at` is provenance only;
  Phase 03 does not label fresh/stale.
- Missing/invalid source or derived fields normalize to `None` and render as
  `Unavailable` before the LLM sees them.
- The static publisher-domain allowlist and provider-delivered article URL,
  title, publication time, and content support the VN news digest. Deterministic
  article deduplication is out of scope.
- VN valuation uses the sector-method matrix and cited, period-consistent inputs
  documented in the feature spec; ranges/sensitivity are research support only.
- One new conversation per workflow, result-to-message adapter, message-owned
  citations/artifacts, owner filtering, terminal-only delete, and no legacy-run
  migration are the chosen persistence design.
- Automated validation is fixture/mock-only. Provider contract checks are
  separately recorded operational work.

## Project Structure

### Documentation

```text
specs/003-vn-gold-dataflows-workflows/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── workflow-contract.md
│   └── conversation-api.md
└── tasks.md                 # regenerated by /speckit-tasks
```

### Source Code

```text
src/
├── finmind_agents/
│   ├── models.py                 # replace ExecutionRun with conversation result types
│   ├── repositories.py           # ConversationRepository protocol
│   ├── dataflows/                # Gold/VN normalized collection and records
│   ├── runtime/                  # language-aware model invocation and bounded timeout
│   └── workflows/
│       ├── service.py            # WorkflowResult production and orchestration
│       ├── conversation_adapter.py
│       ├── catalog.py
│       └── definitions/
├── finmind_api/
│   ├── app.py                    # startup interruption reconciliation
│   ├── conversation_store.py     # PostgreSQL conversation/message persistence
│   ├── routes/workflows.py       # create conversation and SSE subscription
│   ├── routes/conversations.py   # owner-filtered detail/list/delete
│   └── streaming.py
└── finmind_ui/src/
    ├── api/client.ts             # conversation API/types/SSE client
    ├── App.tsx                   # workflow-to-conversation navigation
    └── features/
        ├── chat/                 # shared conversation transcript/message rendering
        ├── settings/             # language selection surface
        └── workflows/            # fixed workflow catalog and validation

tests/
├── conftest.py                   # deterministic provider/model fixtures
├── test_app.py                   # API, ownership, deletion, SSE contracts
└── test_platform_services.py     # workflow, adapter, lifecycle, evidence tests
```

**Structure Decision**: Keep existing `finmind_agents`, `finmind_api`, and
`finmind_ui` boundaries. Add a focused adapter and conversation repository
instead of merging persistence concerns into workflow orchestration.

## Implementation Sequence

### A. Decision-sensitive delivery

1. Implement shared `WorkflowResult`, `Conversation`, `Message`, status/role/
   source enums, and the `ConversationRepository`/`ConversationAdapter`
   protocols. Remove `ExecutionRun` from the new public domain contract.
2. Build PostgreSQL conversation persistence and the conversation/message API
   contract, including owner filtering, terminal-only delete cascade, and
   startup interruption reconciliation.
3. Refactor fixed workflow orchestration so it creates a conversation before
   execution, produces `WorkflowResult`, and lets the adapter persist the first
   assistant message with message-owned citations/artifacts.
4. Change SSE/API/UI from run-oriented behavior to conversation-oriented
   behavior. The new conversation opens immediately; its stream is detachable
   without cancelling execution.
5. Add the authenticated Settings language surface and preference API. Persist
   `auto`/`vi`/`en`, resolve Auto-detect in the browser, and pass only resolved
   `vi`/`en` to workflow submissions.
6. Implement/complete Gold dataflow and fixed VN news, valuation, stock-brief,
   and Gold technical workflows using the existing deterministic evidence
   boundary, language instruction, safety rules, and provider retry policy.
7. Add deterministic mock/fixture tests for dataflow, language settings, adapter,
   ownership, delete cascade, timeout, disconnect, restart, unavailable fields,
   citations, and artifacts. Record live-provider validation outside CI.

### B. Mechanical migration and cleanup

1. Rename/remove `RunRepository`, `PostgresRunRepository`, `/api/runs`,
   `WorkflowRun`, run-specific SSE kinds, run history UI, and old route/tests.
2. Replace the `runs`/`run_citations` schema with conversation/message tables
   and message-owned citation/artifact rows. Preserve `price_series_records`.
3. Remove current request-bound SSE cancellation behavior and move execution to
   a process-scoped task owned by `ConversationWorkflowService`.
4. Regenerate `tasks.md`; it is superseded and must not be implemented as-is.
5. Run `uv run pytest`, frontend tests/build, quickstart deterministic scenarios,
   and a separately recorded live-provider contract check.

## Constitution Check — Post-Design

- **Code quality — PASS**: The adapter prevents workflow execution from owning
  conversation/message persistence; repository and API ownership are explicit.
- **Testing standards — PASS**: The plan requires deterministic test doubles and
  names backend/frontend verification.
- **Safety and UX — PASS**: Evidence remains message-bound and grounded; no raw
  reasoning becomes part of the conversation; terminal failures and unavailable
  content are visible.
- **Performance — PASS**: Submission/progress and terminal bounds are specified.
- **Traceability — PASS**: [system state model](../system/state-model.md),
  [system contracts](../system/contracts.md),
  [data-record flow](../system/data-record-flow.md), and feature contracts own
  all product behavior.

## Complexity Tracking

No constitution exception is required. The conversation adapter is a justified
boundary because the user-facing message model deliberately differs from the
workflow execution result model.
