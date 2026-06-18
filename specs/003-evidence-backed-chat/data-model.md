---
id: SPEC-FEAT-003-DATA
feature: evidence-backed-chat
status: draft
owner: solo
created: 2026-06-18
implements: []
validated_by:
  - tests/test_platform_services.py
adr_refs: []
---

# Data Model: Evidence-Backed Chat

This feature uses shared entities from `../system/state-model.md`.

Feature-owned usage:

- `ChatSession`: conversation, user/assistant messages, role-agent events, runs, and artifacts.
- `RoleAgent`: generic chat role participating through shared platform contracts.
- `ExecutionRun`: chat run records.
- `Artifact`: inline visualizations, charts, tables, and computed outputs.
- `EvidenceObject` and `Citation`: grounding and references for material chat claims.

Chat does not own separate canonical market data or citation systems.
