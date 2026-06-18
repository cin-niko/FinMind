---
id: SPEC-FEAT-002-RESEARCH
feature: data-operations
status: draft
owner: solo
created: 2026-06-18
implements: []
validated_by: []
adr_refs: []
---

# Research: Data Operations

## Decision: Keep provider details behind connector contracts

The product contract should define supported datasets, freshness, source identity, and canonical records. Provider licensing, credentials, schemas, and retry behavior belong in source connector implementations.

## Decision: Use deterministic demo sources first

Deterministic VN stock and gold sources allow validation of idempotency, freshness, and UI behavior before production provider selection is complete.

## Decision: Prevent or serialize unsafe overlap

Multiple jobs for the same dataset and period can corrupt freshness interpretation or duplicate records. The service should either block overlap or serialize it with visible status.
