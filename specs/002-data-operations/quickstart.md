---
id: SPEC-FEAT-002-QUICKSTART
feature: data-operations
status: draft
owner: solo
created: 2026-06-18
implements: []
validated_by:
  - tests/test_app.py
  - tests/test_platform_services.py
adr_refs: []
---

# Quickstart: Data Operations Validation

## Scenario 1: Admin Ingestion Control

1. Log in as admin.
2. Open admin ingestion status.
3. Trigger a manual fetch for `vn_prices`.
4. Trigger a manual fetch for `gold_spot`.
5. Re-run one fetch for the same period.

Expected result: jobs show trigger type, status, timestamps, dataset scope, record counts, and non-secret diagnostics. The rerun does not create duplicate canonical records.

## Scenario 2: Market Data Inspection

1. Open the market data view.
2. Select a supported VN stock or gold dataset.
3. Inspect the chart panel and table fallback.

Expected result: chart-ready records and freshness metadata are visible.
