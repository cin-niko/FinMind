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
- `ChatMessage`: user and assistant messages with evidence-linked outputs.
- `ExecutionRun`: chatflow execution status, tools, retrieval, and artifacts.
- `EvidenceObject`: grounding units for chat claims.
- `Citation`: user-visible source references.
- `Artifact`: generated report, chart, table, evidence list, or citation bundle.
- `SourceDocument`: trusted company, market, macro, or news source.
- `CanonicalMarketDataRecord`: market data referenced by chat answers.

Final fields and relationships require `/speckit-plan` after source and retrieval
decisions are made.
