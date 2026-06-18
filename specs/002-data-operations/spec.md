---
id: SPEC-FEAT-002
feature: data-operations
status: draft
owner: solo
created: 2026-06-18
implements: []
validated_by:
  - tests/test_platform_services.py
adr_refs: []
---

# Feature Specification: Data Operations

## Summary

Deliver admin-controlled data operations for VN stock and gold datasets: ingestion status, scheduled/manual jobs, idempotent reruns, freshness calculation, market data inspection, overlap prevention, and non-secret diagnostics.

This feature depends on `../001-mvp-workflow-platform/` for authentication, app shell, canonical state contracts, evidence contracts, and result inspection patterns.

## User Scenarios & Testing

### User Story 1 - Control And Monitor Ingestion (Priority: P1)

An authenticated internal admin monitors scheduled market data ingestion, manually triggers safe reruns or backfills, and sees job status, freshness, and failure information for supported VN stock and gold datasets.

**Independent Test**: Log in as admin, view ingestion status, trigger manual fetches for VN stock and gold datasets, rerun one fetch for the same period, and verify that job status, timestamps, outcome, freshness metadata, and canonical records update without duplicates.

Acceptance scenarios:

1. Given the admin panel is open, when the admin views ingestion status, then the system shows latest scheduled and manual job outcomes, freshness timestamps, and any errors for each supported dataset.
2. Given a manual ingestion job is triggered for an already-ingested period, when the job completes, then canonical records are updated idempotently and downstream freshness metadata reflects the completed run.
3. Given an ingestion source fails, when the admin reviews the job, then the system displays failure status and diagnostic context without exposing secrets.
4. Given multiple manual ingestion requests target the same dataset and period, when overlap would be unsafe, then the system blocks or serializes work with visible status.

### User Story 2 - Inspect Market Data (Priority: P2)

An authenticated internal admin inspects chart-ready canonical records and freshness metadata for supported datasets.

**Independent Test**: Open the market data view after ingestion, select a VN stock or gold dataset, and verify chart-ready records, freshness state, and table fallback.

## Functional Requirements

- **FR-008**: System MUST maintain ingestion-backed canonical storage for supported VN stock and gold datasets with source identity, collection time, effective market time, freshness metadata, and uniqueness rules.
- **FR-009**: System MUST ingest and expose market data, chart-ready price series, indicators, company reports where applicable, macro news, and other source material required by approved workflows.
- **FR-010**: System MUST support both scheduled ingestion jobs and admin-triggered manual ingestion jobs for supported VN stock and gold datasets.
- **FR-011**: Manual ingestion MUST be idempotent for the same dataset and period and MUST expose run status, timestamps, outcome, and diagnostic error context.
- **FR-016**: System MUST record execution logs for ingestion jobs, generated artifacts, failures, and user-visible output status.
- **FR-018**: System MUST expose views where users can inspect ingestion-backed freshness and data status after the original job.
- **FR-019**: System MUST show clear behavior for missing data, stale data, failed sources, unsupported instruments, and unavailable citations.
- **FR-022**: System MUST keep provider-specific market data details abstract at the product contract level while allowing implementation-time provider validation for technical and licensing suitability.

## Key Entities

- Canonical Market Data Record
- Source Document
- Ingestion Job
- Market Instrument
- Evidence Object
- Citation
- Execution Log

See `../system/state-model.md` for canonical entity definitions.

## Edge Cases

- Source data contains duplicate or corrected records: ingestion preserves canonical uniqueness and makes reruns safe.
- Multiple manual ingestion requests target the same dataset and period: unsafe overlap is prevented or serialized.
- A source fails: diagnostics are visible but secrets are not exposed.
- Data is stale or missing: freshness views and downstream workflow/chat results show clear warnings.
- Provider schema changes: connector-level handling reports failure without corrupting canonical records.

## Success Criteria

- **SC-004**: 100% of ingestion jobs display trigger type, status, start time, end time or active state, dataset scope, and success or failure outcome.
- **SC-005**: Re-running ingestion for the same dataset and period does not create duplicate canonical records in validation scenarios.
- **SC-007**: Users can identify stale, missing, failed, or out-of-scope data conditions from the UI without reading server logs.

## Out Of Scope

- Evidence-backed chat; see `../003-evidence-backed-chat/`.
- Production plugin adapter; see `../004-extension-hardening/`.
- US stocks and BTC as user-facing datasets.
