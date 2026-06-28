---
id: SPEC-FEAT-003-DATA
feature: agentic-chatflow
status: draft
owner: solo
created: 2026-06-26
implements: []
validated_by: []
adr_refs: []
---

# Data Model: Agentic Chatflow

Draft expected entities:

- `ChatConversation`: production conversation record.
- `ChatMessage`: user and assistant messages with cited outputs.
- `ExecutionRun`: chatflow execution status, tools, collection, and artifacts.
- `Citation`: user-visible source-level references (source id, dataset id, timestamp).
- `GroundingCheck`: post-answer audit that cited sources are a subset of collected sources.
- `Artifact`: generated report, chart, table, or citation bundle with source refs.
- `SourceDocument`: trusted company, market, macro, or news source.
- `CanonicalMarketDataRecord`: market data referenced by chat answers.

Final fields and relationships require `/speckit-plan` after source and collection
decisions are made.
