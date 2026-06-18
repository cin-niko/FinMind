---
id: SPEC-FEAT-001-DATA
feature: mvp-workflow-platform
status: draft
owner: solo
created: 2026-06-18
implements: []
validated_by:
  - tests/test_platform_services.py
adr_refs: []
---

# Data Model: MVP Workflow Platform

This feature uses the canonical entities from `../system/state-model.md`.

Feature-owned usage:

- `InternalAdminUser`: bootstrap one admin from environment.
- `Session`: authenticate API and app shell access.
- `MarketInstrument`: represent supported VN stock and gold instruments.
- `CanonicalMarketDataRecord`: seeded/demo records for VN price series and gold spot.
- `WorkflowSpecification`: declarative workflow catalog.
- `ExecutionRun`: workflow run records only in this phase.
- `EvidenceObject`: grounding units for workflow claims.
- `Citation`: visible source references.
- `Artifact`: chart artifacts linked to workflow inputs and evidence.

Phase 1 does not own scheduled ingestion state or chat sessions; those are introduced by later feature specs.
