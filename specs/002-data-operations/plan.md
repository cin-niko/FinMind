---
id: SPEC-FEAT-002-PLAN
feature: data-operations
status: draft
owner: solo
created: 2026-06-18
implements: []
validated_by:
  - tests/test_platform_services.py
adr_refs: []
---

# Implementation Plan: Data Operations

## Summary

Build ingestion operations above the shared platform contracts: source connectors, idempotent canonical upserts, scheduler/manual trigger service, freshness calculation, admin endpoints, market data endpoints, and UI pages for admin ingestion and market data inspection.

## Technical Context

- Backend: Python 3.12, FastAPI, Pydantic
- Frontend: TypeScript, React/Vite, Lightweight Charts
- Storage: in-memory/demo repositories initially, preserving repository boundaries for durable storage later
- Dependencies: `../001-mvp-workflow-platform/`, `../system/state-model.md`, `../system/contracts.md`

## Architecture

- `src/api/platform/ingestion/sources.py`: source contracts
- `src/api/platform/ingestion/demo_sources.py`: deterministic VN stock and gold source connectors
- `src/api/platform/ingestion/store_writer.py`: idempotent canonical record writer
- `src/api/platform/ingestion/service.py`: scheduled/manual ingestion orchestration and overlap prevention
- `src/api/platform/freshness.py`: dataset freshness calculation
- `src/api/routes/admin.py`: admin ingestion, freshness, and market data endpoints
- `src/ui/src/features/admin/AdminIngestionPage.tsx`: admin ingestion UI
- `src/ui/src/features/market-data/MarketDataPage.tsx`: market data inspector

## Gates

- Manual reruns are idempotent for the same dataset and period.
- Unsafe overlap is blocked or serialized.
- Diagnostics never expose secrets.
- Provider-specific details remain behind source connector contracts.
- V1 user-facing data scope remains VN stocks and gold.
