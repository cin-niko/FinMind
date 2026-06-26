---
id: SPEC-FEAT-003
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

# Feature Specification: Evidence-Backed Chat

## Summary

Deliver a chat tab where authenticated internal users ask supported VN finance questions. Chat must reuse the same evidence, citations, chart artifacts, freshness metadata, and execution records established by the workflow platform.

Roadmap update 2026-06-26: because `../002-data-operations/` is parked, M1 must not depend on a populated canonical market database. The active path is workflow/chatflow over real-time retrieval tools that return structured evidence payloads with source, retrieval timestamp, normalized fields, and warning/error state.

## User Scenarios & Testing

### User Story 1 - Ask Evidence-Backed Questions (Priority: P1)

An authenticated internal user asks open-ended finance research questions in chat where role-based agents coordinate over shared platform contracts.

**Independent Test**: Ask a supported VN finance question and verify that the answer includes citations, retrieval freshness metadata, role-agent execution status, inline visualization when useful, and no unsupported claims beyond available evidence.

Acceptance scenarios:

1. Given the user is logged in and asks a supported finance question, when chat orchestration completes, then the answer includes cited evidence, freshness metadata, and execution artifacts consistent with the workflow surface.
2. Given the user asks a question outside V1 market scope, when the chat run completes, then the system states the scope limitation and avoids fabricating unsupported analysis.
3. Given a chat answer uses a chart or derived artifact, when the user inspects it, then the artifact is traceable to canonical data and citations.
4. Given a chat task benefits from computed analysis or visualization, when the system produces an inline artifact, then the artifact is linked to its inputs, execution record, and evidence.

## Functional Requirements

- **FR-007**: System MUST provide a chat tab where generic role-based agents answer supported open-ended finance questions using the same evidence, citations, charts, inline visualizations, and execution records as fixed workflows. While Phase 002 is parked, M1 answers MUST use real-time retrieval tool outputs rather than a populated market database.
- **FR-013**: Every user-facing chat answer MUST expose citations and freshness metadata for material claims. M1 freshness is tied to retrieval timestamps.
- **FR-014**: System MUST generate and display chart or table artifacts for chat outputs when retrieval tools return enough structured data to support them.
- **FR-015**: Chat MUST support inline visualization artifacts for complex tasks where a chart, table, or computed result materially improves user understanding.
- **FR-016**: System MUST record execution logs for chat runs, tool calls, generated artifacts, failures, and user-visible output status.
- **FR-017**: System MUST distinguish workflow agents from generic role agents while preserving shared lower-layer contracts for data access, evidence, citations, charts, inline artifacts, and execution records.
- **FR-018**: System MUST expose result views where users can inspect completed chat outputs, citations, charts, freshness, and execution status after the original run.
- **FR-019**: System MUST show clear out-of-scope behavior for unsupported markets, unsupported instruments, missing data, stale data, and unavailable citations.
- **FR-020**: System MUST show users evidence, citations, role-agent stages, and tool or artifact status while retaining raw agent reasoning internally and excluding it from user-facing chat views.
- **FR-030**: Retrieval tools used by workflow/chatflow MUST produce a structured evidence payload containing source name, retrieval timestamp, requested symbol/question, normalized fields used in the answer, and warning/error state.
- **FR-031**: When retrieval tools fail, rate-limit, or cannot return enough structured data, chat/workflow output MUST surface an unavailable-data state and MUST NOT fall back to demo market fixtures.

## Key Entities

- Chat Session
- Role Agent
- Execution Run
- Evidence Object
- Citation
- Inline Visualization Artifact
- Chart Artifact
- Execution Log

See `../system/state-model.md` for canonical entity definitions.

## Edge Cases

- Supported data exists but is stale: chat outputs display freshness warnings.
- Real-time retrieval fails, rate-limits, or returns partial data: chat outputs show the unavailable or partial-data state and avoid unsupported analysis.
- A chat run partially completes: the result distinguishes completed sections, failed sections, and unavailable artifacts.
- Citations are unavailable for a generated claim: the claim is omitted, qualified, or marked unsupported.
- Unsupported US stock, gold, or BTC requests return a clear V1 scope limitation.

## Success Criteria

- **SC-003**: 100% of user-facing material claims in chat outputs include at least one citation or are explicitly marked unsupported or unavailable.
- **SC-006**: At least 95% of supported chat result views show freshness metadata for every referenced dataset.
- **SC-007**: Users can identify stale, missing, failed, or out-of-scope data conditions from the chat UI without reading server logs.
- **SC-009**: At least one approved chat scenario produces an inline visualization or computed artifact that is inspectable and tied to cited inputs.

## Out Of Scope

- Chat-specific data stores that duplicate workflow evidence/freshness logic.
- US stocks and BTC as supported V1 markets.
- External plugin adapter; see `../004-extension-hardening/`.
