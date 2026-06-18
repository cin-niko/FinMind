---
id: SPEC-FEAT-002-CONTRACTS
feature: data-operations
status: draft
owner: solo
created: 2026-06-18
implements: []
validated_by:
  - tests/test_app.py
adr_refs: []
---

# API Contract: Data Operations

All endpoints require an active session.

## `GET /api/admin/ingestion`

Returns ingestion job history and dataset freshness.

Response includes:

- jobs with `job_id`, `source_id`, `trigger`, `status`, `started_at`, `completed_at`, `record_count`, `diagnostics`
- freshness entries with `dataset`, `status`, `as_of`, `record_count`

## `POST /api/admin/fetch`

Triggers a manual ingestion job for a supported VN stock or gold dataset.

Request includes:

- `source_id`
- `period`

Response includes job status and record count. Unsafe overlap returns blocked or queued status with a clear message.

## `GET /api/market-data/{dataset_id}`

Returns chart-ready canonical records for a supported dataset. Responses include freshness metadata and omit provider secrets.
