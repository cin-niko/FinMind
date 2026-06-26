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
adr_refs:
  - docs/adr/0001-vn-only-v1-market-scope.md
  - docs/adr/0002-daily-canonical-vn-price-data.md
  - docs/adr/0003-vn100-universe-and-lazy-fetch.md
  - docs/adr/0004-dormant-roadmap-market-connectors.md
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
- [ ] T014 [SUPERSEDED 2026-06-25 — replaced by T049 under VN-only V1 scope] Validate quickstart scenarios from `specs/002-data-operations/quickstart.md` against Docker Compose TimescaleDB/PostgreSQL.
- [x] T015 Add per-dataset runtime provider configuration for mock and real source selection.
- [x] T016 Implement VN stock provider adapter with historical range diagnostics and canonical `vn_prices` 1h OHLCV normalization.
- [x] T017 [SUPERSEDED 2026-06-25 — roadmap; code remains dormant in V1] Implement yfinance/Yahoo Finance XAUUSD adapter for recent rolling `xauusd_prices` 1h OHLC normalization.
- [x] T018 [SUPERSEDED 2026-06-25 — roadmap; code remains dormant in V1] Implement Alpha Vantage free gold daily fallback adapter and `xauusd_prices_daily` persistence/query support.
- [x] T019 [SUPERSEDED 2026-06-25 — roadmap; code remains dormant in V1] Implement official SJC website/chart importer for daily `sjc_gold_prices` buy/sell quotes with source attribution and no raw page dumps in diagnostics.
- [x] T020 Add tests that prove the free provider set has no paid API dependency, handles unavailable 1h history with daily fallback diagnostics, preserves idempotent PostgreSQL writes, and never exposes provider tokens or raw scraped content.
- [x] T021 Add fetch request planning for `latest`, `period`, and inclusive `historical` date ranges in `src/api/platform/ingestion/planner.py`.
- [x] T022 Extend ingestion service and admin/worker APIs so manual admin fetches, historical backfills, and daily latest scheduled fetches share one planner/provider/upsert/job path.
- [x] T023 Update admin ingestion UI and API client to support latest, single period, and historical range fetch modes.
- [x] T024 Add tests for historical range splitting, latest daily fetch resolution, manual admin range fetch, scheduled latest fetch, and overlap blocking by source/date scope.
- [x] T025 Replace the legacy VN stock provider support with `vnstock` and normalize `vn_prices` 1h OHLCV records through the existing canonical schema.
- [x] T026 Simplify provider runtime configuration to per-dataset values: `FINMIND_VN_PROVIDER=mock|vnstock`, `FINMIND_XAUUSD_PROVIDER=mock|yfinance`, `FINMIND_SJC_PROVIDER=mock|sjc_official`, and optional `FINMIND_XAUUSD_DAILY_FALLBACK=alpha_vantage`.
- [x] T027 Update `.env.sample`, Docker Compose, README, and tests to remove `FINMIND_PROVIDER_PROFILE`, `FINMIND_PROVIDER_MODE`, and generic provider URL configuration.
- [x] T028 Split provider credentials into provider-specific secrets: `FINMIND_VNSTOCK_API_KEY` and `FINMIND_ALPHA_VANTAGE_API_KEY`; keep VNStock credentials optional/reserved because the implemented free `vnstock` adapter does not require a key.
- [x] T029 [SUPERSEDED 2026-06-25 — roadmap; XAUUSD removed from V1] Expand `xauusd_prices_daily` records into display-only hourly fallback bars for `xauusd_prices` chart responses when real 1h bars are missing, while preserving daily storage truth and fallback metadata.
- [x] T030 Record best-effort VN long-range 1h historical coverage diagnostics while keeping historical backfill and latest fetches on the same `stock_1h_bars` ingestion path.
- [x] T031 Add an independent historical backfill worker/script entrypoint and reject inline `historical` execution from web API endpoints.
- [x] T032 [SUPERSEDED 2026-06-25 — replaced by `vn-history` plan in T047] Add an operator market-history backfill preset with Docker Compose runner support, free-source historical limits, and non-secret skipped-source diagnostics.
- [x] T033 [SUPERSEDED 2026-06-25 — roadmap; US removed from V1] Add US Markets support with `us_prices` recent 1h ingestion, shared stock storage, market overview selector support, and tests.
- [x] T034 [SUPERSEDED 2026-06-25 — roadmap; US removed from V1] Add US daily base support with `us_prices_daily`, typed daily stock storage, yfinance daily adapter, backfill support, and individual-equity-only US list/heatmap rows.
- [x] T035 [SUPERSEDED 2026-06-25 — heatmap scoping re-specified by FR-018b under VN-only V1] Scope market heatmap filters to the heatmap card only, keeping the instrument table, Watchlist, and Gainers/Losers rail on the selected market overview.
- [x] T036 [SUPERSEDED 2026-06-25 — roadmap; US/Gold removed from V1] Change the initial historical data operation to a 7-day operational backfill for US and Gold-capable sources while VNStock historical backfill is paused, with longer ranges left as future provider-dependent work.
- [x] T037 [SUPERSEDED 2026-06-25 — roadmap; US/XAUUSD removed from V1] Add an optional focused `us-xauusd-history` independent backfill preset for operator troubleshooting, excluding VN and SJC and using range fetches for daily US/XAUUSD sources.
- [x] T038 [SUPERSEDED 2026-06-25 — roadmap; US/XAUUSD removed from V1] Add bounded retry diagnostics for US/XAUUSD provider HTTP failures and fail empty Alpha Vantage daily fallback responses instead of recording successful zero-row history.
- [x] T039 [SUPERSEDED 2026-06-25 — V1 scope is now VN-only daily-canonical] Set phase 002 operational data scope to a 7-day independent market-history backfill for US and Gold plus latest/period fetches for current updates, leaving VN historical and longer history as future work.
- [x] T040 [SUPERSEDED 2026-06-25 — roadmap; US/Gold removed from V1] Add a `market-latest` independent operator preset that runs current US and Gold-capable latest fetches before 7-day historical backfill attempts.

- [x] T041 Add `vn_prices_daily` typed daily OHLCV table, hypertable/partition definition, uniqueness constraint, and migration in `src/api/platform/storage/sql/`.
- [x] T042 Extend the `vnstock` adapter with a daily fetch path and normalize records into `vn_prices_daily`; preserve the existing 1h path for the rolling window in `src/api/platform/ingestion/free_sources.py`.
- [x] T043 Add VN100 universe seed: ship a static CSV at `data/seed/vn100.csv` (refreshed quarterly), and a one-shot script `scripts/seed_vn100.sh` that loads constituents into `market_instruments` and creates the `VN100` collection plus effective-dated memberships.
- [x] T044 Implement lazy daily fetch policy in the ingestion service: trigger inline `latest`+`period` for a VN100 ticker with no `vn_prices_daily` rows, guarded by overlap blocking and rate limits; out-of-universe tickers must return out-of-scope without ingestion.
- [x] T045 Update freshness for VN-only V1: `vn_prices_daily` ≤ 1 VN trading day; `vn_prices` ≤ latest expected 1h within the `vnstock` rolling window; remove US/XAUUSD/SJC paths from active freshness output (keep dormant code).
- [x] T046 UI scope-down: remove the header market selector, default the instrument detail chart to `1d`, surface the lazy-fetch loading + freshness banner, and hide US/XAUUSD/SJC mini charts/tables/heatmap rows in V1.
- [x] T047 Replace the default `market-history` plan with a `vn-history` plan targeting `vn_prices_daily` (required) and `vn_prices` best-effort; keep US/XAUUSD/SJC presets reachable behind a `FINMIND_ROADMAP_MARKETS` guard (off by default).
- [x] T048 Tests: VN100 seed determinism, lazy-fetch trigger + overlap guard, out-of-universe rejection, daily canonical freshness rules, default `1d` chart timeframe, and UI scope-down regression. *(Covered incrementally during T041–T046 — see backend `tests/test_platform_services.py` and UI `*.test.ts` files.)*
- [x] T049 Rewrite `specs/002-data-operations/quickstart.md` for the VN-only flow (VN100 seed → scheduled `vn_prices_daily` latest → admin manual rerun → lazy first-access fetch → freshness inspection) and validate against Docker Compose TimescaleDB/PostgreSQL. (Supersedes T014.)
- [x] T050 Finish Phase 002 real-data wiring: Compose defaults VN ingestion to `vnstock`, VNStock sources read the full VN100 seed symbol list by default, API/backfill startup seeds VN100 metadata, and the V1 Market overview reads canonical `vn_prices_daily` rows instead of demo market fixtures.
- [x] T051 Park Phase 002 market-data platform as pending after provider/rate-limit constraints blocked reliable VN100 backfill; keep contracts/import path groundwork, do not use demo fixtures as completion substitute, and shift active product work to workflow/chatflow real-time retrieval tools.
