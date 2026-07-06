---
id: SPEC-FEAT-003
feature: agentic-chatflow
status: draft
owner: solo
created: 2026-06-26
implements: []
validated_by: []
adr_refs: []
---

# Feature Specification: Agentic Chatflow

## Summary

Deliver a future flexible Q&A chatflow for financial trading research advice.
The chatflow will answer user questions using trusted source data, citations (with source id,
dataset id, and timestamp), artifacts, and explicit safety guardrails.

This feature is draft. The current deterministic mock chat UI remains owned by
`../001-mvp-ui/`. Fixed workflow execution remains owned by `../002-workflow/`.

## User Scenarios & Testing

### User Story 1 - Ask Evidence-Backed Finance Questions (Priority: P1)

An authenticated internal user asks a finance research question and receives an
answer grounded in trusted sources with citations.

**Independent Test**: Ask a supported VN or US stock research question and verify
that the answer includes cited claims, provenance (source id, dataset id,
timestamp), and unsupported markers where evidence is missing.

Acceptance scenarios:

1. Given trusted source data is available, when the user asks a supported question,
   then the answer cites the evidence used for material claims.
2. Given evidence is missing, stale, failed, or unsupported, when the answer is
   generated, then the output marks the limitation instead of hallucinating.
3. Given the user asks for a trading decision, when the answer is generated, then
   the system frames output as advice support, not an autonomous decision.

### User Story 2 - Inspect Chat Artifacts And Citations (Priority: P1)

An authenticated internal user can inspect generated chat artifacts such as
files, tables, and charts from the answer, while citations remain inline source
inspection controls.

**Independent Test**: Ask a supported question that produces an artifact, open the
artifact detail, and verify the artifact links back to evidence and citations.

Acceptance scenarios:

1. Given the answer contains an artifact, when the user opens it, then
   citations, grounding, and artifact status remain visible.
2. Given an artifact cannot be generated safely, when the answer renders, then the
   artifact status is marked unavailable rather than fabricated.

### User Story 3 - Keep Humans In The Loop (Priority: P1)

An authenticated internal user receives research support without autonomous
orders, broker actions, or irreversible financial actions.

**Independent Test**: Ask for buy/sell execution or order placement and verify the
system refuses autonomous action while providing bounded research guidance if
evidence supports it.

Acceptance scenarios:

1. Given the user asks the system to trade, when the request is processed, then no
   trade, order, or broker action is performed.
2. Given the system provides advice support, when output appears, then the user can
   see evidence, confidence boundaries, and limitations.

## Functional Requirements

- **FR-001**: Chatflow MUST answer supported finance research questions using
  trusted source data and citations.
- **FR-002**: Chatflow MUST support VN stock and US stock questions only until a
  later spec expands market scope.
- **FR-003**: Chatflow MUST mark unsupported markets, unsupported assets, stale
  data, missing evidence, failed tools, and unavailable providers before user
  reliance.
- **FR-004**: Chatflow MUST cite material claims or explicitly mark them
  unsupported/unavailable.
- **FR-005**: Chatflow MUST show citation provenance (source id, dataset id,
  timestamp) for referenced datasets where available.
- **FR-006**: Chatflow MUST produce inspectable artifacts only when they can be
  linked to evidence and execution context.
- **FR-007**: Chatflow MUST NOT expose raw agent reasoning, hidden prompts,
  provider secrets, credentials, or unsafe diagnostics.
- **FR-008**: Chatflow MUST NOT execute trades, place orders, connect to brokers,
  or perform irreversible financial actions.
- **FR-009**: Chatflow MUST distinguish advice support from decisions and must keep
  the user responsible for final judgment.
- **FR-010**: Chatflow MUST record enough execution status for users to understand
  tool, collection, citation, and artifact availability.

## Key Entities

- Chat Conversation
- Chat Message
- Execution Run
- Evidence Object
- Citation
- Artifact
- Source Document
- Canonical Market Data Record

See `../system/state-model.md` for canonical entity definitions. This feature may
require new production chat entities during planning.

## Edge Cases

- User asks about gold, BTC, crypto, commodities, options, or other unsupported
  assets: scope limitation is shown.
- User asks for a decision or order: autonomous action is refused.
- Trusted sources disagree: answer shows disagreement and cites both sides.
- Source is unavailable or uncited: answer marks the claim ungrounded or
  unavailable.
- Artifact generation fails: artifact is marked unavailable.

## Assumptions

- The MVP UI shell exists from `../001-mvp-ui/`.
- Fixed workflow contracts exist from `../002-workflow/`.
- Trusted source access, collection policy, and data rights require planning before
  implementation.

## Success Criteria

- **SC-001**: 100% of material chat claims include citations or are explicitly
  marked unsupported/unavailable.
- **SC-002**: 100% of unsupported markets/assets are blocked or visibly marked
  before user reliance.
- **SC-003**: 100% of trade execution/order placement requests do not trigger
  irreversible financial actions.
- **SC-004**: Users can inspect citations, grounding, and artifact status for
  generated answers without reading logs.
- **SC-005**: Supported answers remain within the current VN stock and US stock
  market scope.

## Out Of Scope

- MVP shell/login ownership.
- Fixed workflow execution ownership.
- Broker connectivity, trade execution, portfolio order management, and autonomous
  decisions.
- Native realtime data/news platform unless specified by a later bounded feature.
- Gold, BTC, crypto, commodities, options, futures, and other non-current assets.
