---
id: SPEC-FEAT-002-DATA
feature: data-operations
status: draft
owner: solo
created: 2026-06-18
implements: []
validated_by:
  - tests/test_platform_services.py
adr_refs: []
---

# Data Model: Data Operations

This feature extends use of shared entities from `../system/state-model.md`.

Feature-owned usage:

- `IngestionJob`: scheduled/manual fetch operation with dataset scope, period, trigger, status, timestamps, record count, and diagnostics.
- `CanonicalMarketDataRecord`: ingestion-backed VN stock and gold records with uniqueness rules.
- `SourceDocument`: company reports, macro news, market news, and document-like evidence sources.
- `MarketInstrument`: supported VN stock and gold instrument metadata.
- `EvidenceObject` and `Citation`: source material exposed downstream to workflows and chat.

Rules:

- `(dataset_id, record_key)` remains the canonical uniqueness boundary.
- Manual reruns update or replace matching logical records instead of duplicating them.
- Failed ingestion jobs record non-secret diagnostics.
