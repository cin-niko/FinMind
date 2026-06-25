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

- [x] T001 [P] Define ingestion source contracts for initial `vn_prices`, `xauusd_prices`, and `sjc_gold_prices` support, with extension points for indicators, reports, and macro news in `src/api/platform/ingestion/sources.py`.
- [x] T002 [P] Implement demo VN stock, XAUUSD, and SJC gold source connectors with deterministic `vn_prices`, `xauusd_prices`, and `sjc_gold_prices` records in `src/api/platform/ingestion/demo_sources.py`.
- [x] T003 Add Docker Compose TimescaleDB/PostgreSQL service and test database configuration for phase 002 verification.
- [x] T004 Define PostgreSQL/TimescaleDB schema/migrations for initial market instruments, market collections, market collection memberships, `stock_1h_bars`, `xauusd_1h_bars`, `sjc_gold_daily_quotes`, source documents, ingestion jobs, execution logs, evidence objects, citations, and artifacts, creating the initial price tables as hypertables or equivalent PostgreSQL time partitions.
- [x] T005 Define and validate typed `vn_prices` 1h OHLCV schema, `xauusd_prices` 1h OHLC schema, `sjc_gold_prices` daily quote schema, and market instrument/collection metadata schemas from `specs/002-data-operations/data-model.md`.
- [x] T006 Implement PostgreSQL/TimescaleDB repository/session layer in `src/api/platform/storage/postgres.py`.
- [x] T007 Implement idempotent time-series upsert behavior in `src/api/platform/storage/postgres.py` using typed table uniqueness constraints.
- [x] T008 Implement ingestion service with manual trigger handling, protected worker invocation handling, and blocked overlap prevention in `src/api/platform/ingestion/service.py`.
- [x] T009 Implement dataset-specific freshness calculation for `vn_prices`, `xauusd_prices`, and `sjc_gold_prices` in `src/api/platform/freshness.py`.
- [x] T010 Implement admin ingestion, protected worker scheduled ingestion, manual fetch, freshness, and market data endpoints in `src/api/routes/admin.py`, with market overview and instrument chart endpoints in `src/api/routes/market.py`.
- [x] T011 [P] Build admin ingestion page with job history, freshness table, manual fetch controls, and diagnostics in `src/ui/src/features/admin/AdminIngestionPage.tsx`.
- [x] T012 [P] Build market data inspector with market selector, watchlist selector, index mini charts, filterable heatmap, sortable instrument list, and full instrument chart detail in `src/ui/src/features/market/MarketPage.tsx`.
- [x] T013 Connect admin ingestion controls to API client and refresh visible status after manual runs in `src/ui/src/api/client.ts`.
- [ ] T014 Validate quickstart scenarios from `specs/002-data-operations/quickstart.md` against Docker Compose TimescaleDB/PostgreSQL.
- [x] T015 Add per-dataset runtime provider configuration for mock and real source selection.
- [x] T016 Implement VN stock provider adapter with historical range diagnostics and canonical `vn_prices` 1h OHLCV normalization.
- [x] T017 Implement yfinance/Yahoo Finance XAUUSD adapter for recent rolling `xauusd_prices` 1h OHLC normalization.
- [x] T018 Implement Alpha Vantage free gold daily fallback adapter and `xauusd_prices_daily` persistence/query support.
- [x] T019 Implement official SJC website/chart importer for daily `sjc_gold_prices` buy/sell quotes with source attribution and no raw page dumps in diagnostics.
- [x] T020 Add tests that prove the free provider set has no paid API dependency, handles unavailable 1h history with daily fallback diagnostics, preserves idempotent PostgreSQL writes, and never exposes provider tokens or raw scraped content.
- [x] T021 Add fetch request planning for `latest`, `period`, and inclusive `historical` date ranges in `src/api/platform/ingestion/planner.py`.
- [x] T022 Extend ingestion service and admin/worker APIs so manual admin fetches, historical backfills, and daily latest scheduled fetches share one planner/provider/upsert/job path.
- [x] T023 Update admin ingestion UI and API client to support latest, single period, and historical range fetch modes.
- [x] T024 Add tests for historical range splitting, latest daily fetch resolution, manual admin range fetch, scheduled latest fetch, and overlap blocking by source/date scope.
- [x] T025 Replace the legacy VN stock provider support with `vnstock` and normalize `vn_prices` 1h OHLCV records through the existing canonical schema.
- [x] T026 Simplify provider runtime configuration to per-dataset values: `FINMIND_VN_PROVIDER=mock|vnstock`, `FINMIND_XAUUSD_PROVIDER=mock|yfinance`, `FINMIND_SJC_PROVIDER=mock|sjc_official`, and optional `FINMIND_XAUUSD_DAILY_FALLBACK=alpha_vantage`.
- [x] T027 Update `.env.sample`, Docker Compose, README, and tests to remove `FINMIND_PROVIDER_PROFILE`, `FINMIND_PROVIDER_MODE`, and generic provider URL configuration.
- [x] T028 Split provider credentials into provider-specific secrets: `FINMIND_VNSTOCK_API_KEY` and `FINMIND_ALPHA_VANTAGE_API_KEY`; reject `vnstock` runtime config when its key is missing.
- [x] T029 Expand `xauusd_prices_daily` records into display-only hourly fallback bars for `xauusd_prices` chart responses when real 1h bars are missing, while preserving daily storage truth and fallback metadata.
- [x] T030 Record best-effort VN long-range 1h historical coverage diagnostics while keeping historical backfill and latest fetches on the same `stock_1h_bars` ingestion path.
- [x] T031 Add an independent historical backfill worker/script entrypoint and reject inline `historical` execution from web API endpoints.
- [x] T032 Add an operator market-history backfill preset with Docker Compose runner support, free-source historical limits, and non-secret skipped-source diagnostics.
- [x] T033 Add US Markets support with `us_prices` recent 1h ingestion, shared stock storage, market overview selector support, and tests.
- [x] T034 Add US daily base support with `us_prices_daily`, typed daily stock storage, yfinance daily adapter, backfill support, and individual-equity-only US list/heatmap rows.
- [x] T035 Scope market heatmap filters to the heatmap card only, keeping the instrument table, Watchlist, and Gainers/Losers rail on the selected market overview.
- [x] T036 Change the initial historical data operation to a 1-month operational backfill for US and Gold-capable sources while VNStock historical backfill is paused, with longer ranges left as future provider-dependent work.
- [x] T037 Add an optional focused `us-xauusd-history` independent backfill preset for operator troubleshooting, excluding VN and SJC and using range fetches for daily US/XAUUSD sources.
- [x] T038 Add bounded retry diagnostics for US/XAUUSD provider HTTP failures and fail empty Alpha Vantage daily fallback responses instead of recording successful zero-row history.
- [x] T039 Set phase 002 operational data scope to a 1-month independent market-history backfill for US and Gold plus latest/period fetches for current updates, leaving VN historical and longer history as future work.
