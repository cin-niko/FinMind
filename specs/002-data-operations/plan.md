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

Build ingestion operations above the shared platform contracts: source connectors, idempotent canonical upserts, external scheduler/worker API contract, manual trigger service, freshness calculation, admin endpoints, market data endpoints, and UI pages for admin ingestion and market data inspection.

## Technical Context

- Backend: Python 3.12, FastAPI, Pydantic
- Frontend: TypeScript, React/Vite, Lightweight Charts
- Storage: PostgreSQL-compatible TimescaleDB canonical application database; Docker Compose TimescaleDB/PostgreSQL for tests and local verification
- Dependencies: `../001-mvp-workflow-platform/`, `../system/state-model.md`, `../system/contracts.md`

## Architecture

- `src/api/platform/ingestion/sources.py`: source contracts with initial `vn_prices`, `xauusd_prices`, and `sjc_gold_prices` support plus extension points for indicators, reports, and macro/news
- `src/api/platform/ingestion/demo_sources.py`: deterministic VN stock, XAUUSD, and SJC gold source connectors for `vn_prices`, `xauusd_prices`, and `sjc_gold_prices`
- `src/api/platform/ingestion/free_sources.py`: free provider adapters for `vnstock` VN stocks, yfinance/Yahoo Finance XAUUSD recent 1h bars, Alpha Vantage XAUUSD daily fallback, and official SJC daily quotes
- `src/api/platform/ingestion/store_writer.py`: idempotent time-series record writer
- `src/api/platform/storage/postgres.py`: PostgreSQL/TimescaleDB connection/session management and repository implementations
- `src/api/platform/ingestion/service.py`: shared ingestion orchestration, worker/manual latest/period invocation handling, independent backfill invocation support, and blocked overlap prevention
- `src/api/platform/ingestion/backfill.py`: CLI worker entrypoint for long historical backfills outside the web app process
- `src/api/platform/freshness.py`: dataset freshness calculation
- `src/api/routes/admin.py`: admin ingestion, protected worker ingestion, freshness, and market data endpoints
- `src/ui/src/features/admin/AdminIngestionPage.tsx`: admin ingestion UI
- `src/ui/src/features/market/MarketPage.tsx`: market data inspector

## Gates

- Manual reruns are idempotent for the same dataset and period.
- PostgreSQL constraints enforce time-series uniqueness for stock 1h bars, XAUUSD 1h bars, and SJC daily quotes.
- Time-series price tables are TimescaleDB hypertables or equivalent PostgreSQL time partitions.
- Tests and local verification run against Docker Compose TimescaleDB/PostgreSQL.
- Unsafe overlap is blocked with visible status.
- Scheduled ingestion is invoked through a protected worker API endpoint, not only app startup or demo history.
- Initial implementation ingests `vn_prices`, `xauusd_prices`, and `sjc_gold_prices`; other source types remain connector extension points until required by an approved workflow.
- Dataset provider variables select `mock` or the implemented real adapter:
  `vnstock` for VN stocks, yfinance/Yahoo Finance for recent XAUUSD 1h bars, Alpha
  Vantage for XAUUSD daily fallback, and official SJC pages for SJC daily quotes.
- Real provider adapters must surface historical range/rate/fallback capability
  diagnostics without claiming unavailable 1h history exists.
- VN stock historical backfill and post-launch latest fetches use the same 1h
  ingestion/upsert path; phase 002 starts with a 1-month operational US and Gold baseline while VNStock historical backfill is paused, and incomplete
  longer coverage is a best-effort coverage
  diagnostic, not a daily fallback or launch blocker.
- Long historical backfill is run by an independent worker/script process. The web API
  rejects inline `historical` execution and remains responsible for status/diagnostic
  inspection and short latest/period fetches only.
- Diagnostics never expose secrets.
- Provider-specific details remain behind source connector contracts.
- V1 user-facing data scope remains VN stocks and gold.
