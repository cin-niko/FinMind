---
id: SPEC-FEAT-002-TASKS
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

# Tasks: Data Operations

- [ ] T001 [P] Define ingestion source contracts for VN prices, gold spot, indicators, reports, and macro news in `src/api/platform/ingestion/sources.py`.
- [ ] T002 [P] Implement demo VN stock and gold source connectors with deterministic records in `src/api/platform/ingestion/demo_sources.py`.
- [ ] T003 Implement idempotent canonical record upsert behavior in `src/api/platform/ingestion/store_writer.py`.
- [ ] T004 Implement ingestion scheduler and manual trigger service with overlap prevention in `src/api/platform/ingestion/service.py`.
- [ ] T005 Implement freshness calculation by dataset and instrument in `src/api/platform/freshness.py`.
- [ ] T006 Implement admin ingestion, manual fetch, freshness, and market data endpoints in `src/api/routes/admin.py`.
- [ ] T007 [P] Build admin ingestion page with job history, freshness table, manual fetch controls, and diagnostics in `src/ui/src/features/admin/AdminIngestionPage.tsx`.
- [ ] T008 [P] Build market data inspector for chart-ready canonical records with chart and table views in `src/ui/src/features/market-data/MarketDataPage.tsx`.
- [ ] T009 Connect admin ingestion controls to API client and refresh visible status after manual runs in `src/ui/src/api/client.ts`.
- [ ] T010 Validate quickstart scenarios from `specs/002-data-operations/quickstart.md`.
