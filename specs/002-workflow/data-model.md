---
id: SPEC-FEAT-002-DATA
feature: workflow
status: draft
owner: solo
created: 2026-06-26
implements: []
validated_by: []
adr_refs: []
---

# Data Model: Workflow

This feature uses canonical entities from `../system/state-model.md`.

Feature-owned usage:

- `MarketInstrument`: supported VN stock and US stock instruments.
- `CanonicalMarketDataRecord`: seeded/demo VN and US price records.
- `WorkflowSpecification`: fixed workflow catalog and declared workflow behavior.
- `ExecutionRun`: workflow run records.
- `EvidenceObject`: grounding units for material workflow claims.
- `Citation`: visible source references.
- `Artifact`: chart/table/computed outputs linked to workflow inputs and evidence.

This feature does not own UI shell session state or production chat execution
state.
