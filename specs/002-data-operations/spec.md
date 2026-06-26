---
id: SPEC-FEAT-002
feature: data-operations
status: pending
owner: solo
created: 2026-06-18
implements: []
validated_by:
  - tests/test_platform_services.py
adr_refs:
  - docs/adr/0001-vn-only-v1-market-scope.md
  - docs/adr/0002-daily-canonical-vn-price-data.md
  - docs/adr/0003-vn100-universe-and-lazy-fetch.md
  - docs/adr/0004-dormant-roadmap-market-connectors.md
  - docs/adr/0006-shared-evidence-lineage-tables.md
  - docs/adr/0007-single-timescaledb-store-for-v1.md
---

# Feature Specification: Data Operations

## Summary

**Status update 2026-06-26**: the market data platform scope is parked as
pending. VN100 metadata seeding, canonical table contracts, lazy-fetch
diagnostics, and real-provider wiring remain useful groundwork, but Phase 002 is
not on the critical path until reliable market-data rights/access are secured
or an operator-owned import source is available. Product work now proceeds via
workflow/chatflow using real-time retrieval tools rather than requiring a fully
populated canonical market database.

Deliver admin-controlled data operations for the **Vietnam stock market only**: a
pre-seeded **VN100 universe** in `market_instruments`, ingestion status,
scheduled/manual jobs, idempotent reruns, freshness calculation, market data
inspection, overlap prevention, **lazy on-first-access daily ingestion** for
in-universe tickers, and non-secret diagnostics. Daily bars (`vn_prices_daily`)
are the canonical timeframe; 1h bars (`vn_prices`) remain best-effort within
the free `vnstock` rolling window.

US stocks, XAUUSD, and SJC gold are removed from V1 user-facing scope and held
as roadmap markets behind the existing source connector contracts. Their
adapters, schemas, and FRs are preserved in this spec for history and remain
reachable behind roadmap configuration, but they are not part of V1 ingestion,
freshness output, or market views.

This feature depends on `../001-mvp-workflow-platform/` for authentication, app shell, canonical state contracts, evidence contracts, and result inspection patterns.

## Clarifications

### Session 2026-06-19

- Q: How should overlapping manual ingestion requests for the same dataset and period be handled? → A: Block overlapping manual runs with a visible blocked status/message.
- Q: Which datasets are required for the initial phase 002 implementation? → A: Initial implementation must ingest `vn_prices`, `xauusd_prices`, and `sjc_gold_prices`; indicators, reports, and macro/news remain source-contract extension points unless needed by an approved workflow.
- Q: How should phase 002 calculate dataset freshness? → A: Use dataset-specific freshness: VN stock and XAUUSD by latest expected 1h interval, SJC by latest expected VN business day, missing when no records, failed when latest ingestion failed.
- Q: How should scheduled ingestion be executed in phase 002? → A: Require an external scheduler/worker contract now, even for demo storage.
- Q: What scheduler/worker contract should phase 002 expose? → A: Add a protected scheduler/worker API endpoint that invokes scheduled ingestion for supported datasets.
- Q: What database should phase 002 use and how should tests run it? → A: PostgreSQL is the canonical database; tests and local verification use PostgreSQL via Docker Compose.
- Q: What timeframe should each initial market dataset store? → A: VN stocks and XAUUSD store 1h bars; VN SJC gold stores daily prices.
- Q: How should large 10-year multi-market price history be stored? → A: Use typed PostgreSQL time-series tables for price observations, with shared metadata, ingestion, evidence, citation, and artifact tables.
- Q: What database service should power time-series storage? → A: Use a PostgreSQL-compatible TimescaleDB service, with local/test runtime via Docker Compose.
- Q: How should real provider fetching be configured? → A: Use one provider variable per supported dataset (`FINMIND_VN_PROVIDER`, `FINMIND_XAUUSD_PROVIDER`, and `FINMIND_SJC_PROVIDER`) with `mock` for deterministic local tests and the implemented real provider for live fetches; optional provider API keys are separate (`FINMIND_VNSTOCK_API_KEY`, `FINMIND_ALPHA_VANTAGE_API_KEY`), remain server-side, and never appear in API responses, diagnostics, logs, or tests.
- Q: Which free provider set should phase 002 support first? → A: Use `vnstock` for VN stocks, yfinance/Yahoo Finance for recent XAUUSD 1h bars, Alpha Vantage free gold history as XAUUSD daily fallback, and the official SJC website/chart surfaces for SJC daily quotes.
- Q: How should free-source historical limitations affect retention? → A: Keep VN stocks at 1h where `vnstock` history allows it, store XAUUSD recent rolling 1h bars plus long-history daily fallback, and store SJC as daily quotes only.
- Q: How should fetch operations be modeled? → A: Use one ingestion pipeline for `latest`, `period`, and `historical` modes; historical mode plans inclusive daily fetch periods, latest mode resolves the current expected date, and manual/admin plus worker scheduled calls share the same planner/provider/upsert/job path.

### Session 2026-06-21

- Q: Should pre-production historical backfill and post-launch latest fetching use separate daily/1h mechanisms? → A: Use the same 1h ingestion mechanism for both historical backfill and post-launch latest fetches.
- Q: What happens if the free provider cannot supply full long-range VN stock 1h coverage? → A: Historical 1h backfill is best-effort; missing provider ranges are recorded as coverage diagnostics, and production can launch with partial 1h history.
- Q: Where should long historical backfill execute? → A: Run historical backfill as an independent worker/script process that imports the ingestion service and writes to the DB; the web app must not execute long backfills inline.
- Q: How should a long-range free-source market backfill handle datasets whose providers cannot supply that exact history? → A: The operator backfill plan MUST run VN stock 1h best-effort for the requested range, run XAUUSD daily fallback for the full requested range and recent XAUUSD 1h only inside the free provider window, and skip SJC historical ranges unless a true historical SJC source/archive is configured; it MUST NOT synthesize persisted provider rows to hide missing historical data.
- Q: How should US Markets enter phase 002 given VN/XAU free-source constraints? → A: Add `US` as a supported market view with `us_prices` for recent 1h yfinance/Yahoo Finance data and `us_prices_daily` for daily base history from a no-key daily CSV source. US mini charts may use index/proxy summaries, but the US instrument table and heatmap must contain individual instruments only, not index or ETF proxy rows.
- Q: How should operators run only the US daily base without triggering VN/gold providers? → A: Provide a dedicated `us-daily-history` backfill preset that runs only `us_prices_daily` over the requested range and does not execute the broader `market-history` plan.
- Q: What historical scope should phase 002 fetch first after long ranges proved fragile across free providers? → A: Start production preparation with a 7-day operational baseline for US and Gold while VNStock historical backfill is paused. Longer ranges remain explicit, provider-dependent future work after the 7-day baseline and latest/current fetch loop are stable.
- Q: Which optional focused historical fetch should remain available for US/XAUUSD work? → A: Keep a `us-xauusd-history` preset for focused US Markets and XAUUSD operator runs. The default operational baseline is still `market-history` for US and Gold-capable sources.
- Q: How should focused US/XAUUSD providers behave when free endpoints rate-limit, disconnect, or return empty daily fallback payloads? → A: Provider adapters must retry transient HTTP failures with bounded backoff, record non-secret retry-aware diagnostics when retries are exhausted, and treat empty Alpha Vantage daily fallback responses for historical XAUUSD as failed provider coverage rather than successful zero-row ingestion.
- Q: What is enough for phase 002 launch after free-provider backfill failures? → A: Use the independent `market-history` worker for a 7-day backfill across US and Gold-capable sources, keep VNStock historical backfill paused, and rely on `latest`/`period` scheduled or admin fetches for real-time/current updates. Longer historical windows are future work.
- Q: How should the 7-day backfill proceed while VNStock is noisy or rate-limited? → A: Temporarily exclude `vn_prices` from the default `market-history` preset and backfill only US and Gold-capable datasets (`us_prices_daily`, `xauusd_prices_daily`, recent `xauusd_prices`, and skipped/diagnosed `sjc_gold_prices`). VN latest/manual ingestion remains available separately and VN historical backfill is future work.
- Q: How should operators prioritize current records before retrying history? → A: Provide a `market-latest` independent operator preset that runs latest-mode fetches for current US and Gold-capable datasets before any 7-day historical backfill attempt.

### Session 2026-06-25

- Q: After repeated free-provider failures on US and Gold, what should V1 actually cover? → A: Scope V1 to VN stocks only. US stocks, XAUUSD, and SJC gold move to roadmap and are removed from enabled V1 surfaces. Provider connector contracts, adapters, and schemas for US/XAUUSD/SJC remain in code as roadmap extension points but are not part of V1 ingestion, freshness, or market views.
- Q: What VN universe should V1 cover? → A: Pre-seed the VN100 constituent list into `market_instruments` from a static CSV checked into the repository and refreshed on a quarterly cadence, plus a `VN100` row in `market_collections` with effective-dated memberships. VN30, sector, and watchlist collections remain supported entities and are populated from the VN100 universe.
- Q: How should tickers outside the pre-seeded universe be handled? → A: V1 covers the VN100 universe only. References to tickers outside VN100 return a clear out-of-scope status. The universe is extended by updating the seed CSV and re-running the seed script; no open on-demand instrument creation in V1.
- Q: How should price data be loaded for VN100 tickers that have no rows yet? → A: Pre-seed metadata only; defer price ingestion. On first chart/workflow access to a VN100 ticker with no `vn_prices_daily` rows, the ingestion service triggers a one-shot inline `latest`+`period` daily fetch through the same idempotent path used by scheduled ingestion. Historical backfill still runs only from the independent worker.
- Q: What is the canonical VN timeframe for V1? → A: `1d` is canonical. `vn_prices_daily` is the primary storage and the default chart timeframe. `vn_prices` 1h remains best-effort over the rolling `vnstock` window; `4h` and `1M` views are derived from daily. The instrument detail chart defaults to `1d`.
- Q: How should phase 002 freshness behave under VN-only scope? → A: Freshness is computed only for `vn_prices_daily` (fresh ≤ 1 VN trading day) and best-effort `vn_prices` (fresh ≤ latest expected 1h bar inside the vnstock window). Missing = no records; failed = latest ingestion job failed.
- Q: What is the final Phase 002 real-data path? → A: Docker Compose defaults VN ingestion to `FINMIND_VN_PROVIDER=vnstock`, seeds the VN100 universe before API/backfill startup, runs the `vn-history` backfill against all VN100 symbols from the seed CSV, and renders Market overview/instrument charts from canonical store rows rather than demo market fixtures.

### Session 2026-06-26

- Q: What happens after VNStock/API limits block practical VN100 backfill? → A: Park the Phase 002 market-data platform as pending. Do not reintroduce demo/mock market data as a substitute for real rows. Continue workflow/chatflow work using real-time retrieval tools, with citations and freshness tied to tool outputs. Resume Phase 002 only when a reliable legal source is available, such as licensed data, official downloads, or operator-supplied Excel/CSV imports.

## User Scenarios & Testing

### User Story 1 - Control And Monitor Ingestion (Priority: P1)

An authenticated internal admin monitors scheduled VN stock market data ingestion, manually triggers safe reruns or backfills, and sees job status, freshness, and failure information for the VN datasets in V1 scope (`vn_prices_daily` canonical, `vn_prices` 1h best-effort).

**Independent Test**: Log in as admin, view ingestion status, trigger manual fetches for `vn_prices_daily` and `vn_prices`, rerun one fetch for the same period, and verify that job status, timestamps, outcome, freshness metadata, and time-series records update without duplicates.

Acceptance scenarios:

1. Given the admin panel is open, when the admin views ingestion status, then the system shows latest scheduled and manual job outcomes, freshness timestamps, and any errors for each supported dataset.
2. Given a manual ingestion job is triggered for an already-ingested period, when the job completes, then typed time-series records are updated idempotently and downstream freshness metadata reflects the completed run.
3. Given an ingestion source fails, when the admin reviews the job, then the system displays failure status and diagnostic context without exposing secrets.
4. Given multiple manual ingestion requests target the same dataset and period, when overlap would be unsafe, then the system blocks the later request with visible status.

### User Story 2 - Inspect Market Data (Priority: P2)

An authenticated internal admin inspects chart-ready VN time-series records and freshness metadata across the VN100 universe.

**Independent Test**: Open the market data view after ingestion, browse VN100 instruments, and verify chart-ready records, freshness state, lazy-fetch behavior on first access, and table fallback.

Acceptance scenarios:

1. Given the Market page is open, then the page shows top index mini charts for `VNINDEX`, `VN100`, `VN30`, `HNXINDEX`, and `UPCOM`, a sortable VN100 instrument list, and a filterable VN100 heatmap. No header market selector is shown in V1.
2. Given the admin filters the heatmap by a collection such as `VN30` or a sector collection, then only the heatmap cells update; the instrument table, Watchlist, and Gainers/Losers rail remain scoped to VN100.
3. Given the admin clicks a VN100 row or heatmap cell with no `vn_prices_daily` rows yet, then the system triggers a lazy daily ingestion through the canonical idempotent path, shows a loading state with a freshness banner, and renders the `1d` chart on completion.
4. Given the admin references a ticker outside the pre-seeded VN100 universe, then the system returns a clear out-of-scope status without creating an instrument record or attempting ingestion.

## Functional Requirements

- **FR-008**: System MUST maintain ingestion-backed time-series storage for VN stock datasets in V1 scope with source identity, collection time, effective market time, freshness metadata, and uniqueness rules.
- **FR-008a**: Phase 002 MUST use a PostgreSQL-compatible TimescaleDB service as the canonical application database for ingestion-backed storage; tests and local verification MUST use a TimescaleDB/PostgreSQL instance provisioned through Docker Compose rather than SQLite or in-memory-only persistence.
- **FR-008b**: PostgreSQL storage MUST include shared tables for market instruments, source documents, ingestion jobs, execution logs, evidence objects, citations, and artifacts, plus typed time-series tables for VN daily bars (`vn_prices_daily`, required) and VN 1h bars (`vn_prices`, best-effort). JSONB is allowed for diagnostics, source excerpts/summaries, artifact payloads, and execution output fields that remain provider- or artifact-shaped. XAUUSD and SJC gold typed tables defined in `data-model.md` remain as roadmap schemas; they are not part of V1 ingestion output.
- **FR-008c**: Time-series tables MUST enforce dataset-specific uniqueness for their logical observation keys, ingestion jobs MUST support lookup and overlap checks by dataset/source, period, and active status, and traceability tables MUST preserve links from citations/evidence/artifacts back to time-series records, source documents, or execution context.
- **FR-008d**: `vn_prices_daily` records MUST be stored in a typed VN stock daily OHLCV table keyed by market, instrument, and trade date; `vn_prices` records MUST be stored in a typed VN stock 1h bars table keyed by market, instrument, and interval start. XAUUSD 1h, XAUUSD daily, and SJC gold daily schemas remain defined in `data-model.md` for roadmap re-enablement, but V1 ingestion MUST NOT write to them.
- **FR-008e**: `vn_prices_daily` and `vn_prices` tables MUST be created as TimescaleDB hypertables or equivalent PostgreSQL time partitions, while shared metadata/evidence tables remain regular relational tables. Roadmap XAUUSD/SJC tables follow the same partitioning rule when re-enabled.
- **FR-008f**: Market instruments MUST store classification metadata needed for display filters, including asset class, sector, industry, optional sub-industry, exchange, currency, status, and display name.
- **FR-008g**: PostgreSQL storage MUST include market collection tables for index groups, predefined watchlists, sectors, and thematic groups, with membership records linking instruments to collections over effective date ranges. V1 collections are populated from the VN100 universe.
- **FR-008h**: Phase 002 V1 MUST pre-seed `market_instruments` with the VN100 constituent list from a static CSV checked into the repository (refreshed on a quarterly cadence) and MUST create a `VN100` row in `market_collections` with effective-dated memberships before V1 ingestion runs. The seed list is the V1 instrument universe; tickers outside this list MUST return out-of-scope behavior in V1 market and workflow surfaces.
- **FR-009**: System MUST ingest and expose chart-ready `vn_prices_daily` (canonical) and `vn_prices` 1h (best-effort) datasets in V1. Roadmap datasets (`xauusd_prices`, `xauusd_prices_daily`, `sjc_gold_prices`, `us_prices`, `us_prices_daily`) are not part of V1 ingestion output.
- **FR-009b**: Production ingestion MUST select VN source adapters with the per-dataset provider variable `FINMIND_VN_PROVIDER=mock|vnstock`. Roadmap variables (`FINMIND_US_PROVIDER`, `FINMIND_XAUUSD_PROVIDER`, `FINMIND_XAUUSD_DAILY_FALLBACK`, `FINMIND_SJC_PROVIDER`) remain recognized config names; setting them MUST NOT enable V1 surfaces.
- **FR-009f**: Provider credentials MUST be configured with provider-specific variables, not a shared token. `FINMIND_VNSTOCK_API_KEY` is optional/reserved for VN provider profiles that require credentials; the implemented free `vnstock` V1 adapter MUST NOT fail closed solely because the key is absent. `FINMIND_ALPHA_VANTAGE_API_KEY` is a roadmap variable used only when XAUUSD daily fallback is re-enabled outside V1.
- **FR-009c**: Source adapters MUST normalize provider responses into the typed canonical schemas in `data-model.md`; invalid, missing, or unsupported provider fields MUST fail the ingestion job without writing partial corrupt records.
- **FR-009d**: The V1 no-cost real provider set MUST support `vnstock` for VN stock daily history and VN stock 1h rolling-window history. yfinance/Yahoo Finance (XAUUSD/US), Alpha Vantage (XAUUSD daily), and official SJC ingestion remain implemented as roadmap adapters and MUST NOT be wired into V1 schedules or admin controls.
- **FR-009e**: Real-source adapters MUST record provider capability limits in ingestion diagnostics and freshness views; VN 1h coverage gaps inside the `vnstock` rolling window MUST be reported as best-effort coverage diagnostics rather than treated as canonical missing data.
- **FR-009a**: Source contracts MUST preserve extension points for indicators, company reports where applicable, macro news, and other source material required by approved workflows, but those sources are not required to be populated in V1 unless an approved workflow declares them as required datasets.
- **FR-010**: System MUST support both externally scheduled ingestion jobs and admin-triggered manual ingestion jobs for V1 VN datasets (`vn_prices_daily`, `vn_prices`).
- **FR-010c**: Fetch requests MUST support `latest`, `period`, and `historical` modes. `historical` requests MUST include `from_date` and `to_date`; `period` requests MUST include `period`; `latest` requests MUST derive the latest expected date server-side.
- **FR-010d**: Historical fetches MUST run from an independent worker/script process, split inclusive date ranges into provider-safe periods, fetch each period through the selected source adapter, and write all returned records through the same idempotent PostgreSQL upsert path used by latest fetches.
- **FR-010e**: VN stock historical backfill, scheduled latest fetches, and lazy on-first-access fetches MUST share the canonical idempotent ingestion path. `vn_prices_daily` is the canonical V1 timeframe and writes to the typed daily stock storage path; `vn_prices` 1h fetches write to the existing `stock_1h_bars` path and remain best-effort over the `vnstock` rolling window.
- **FR-010f**: VN stock 1h coverage MUST be treated as provider best-effort: ingestion records all returned 1h bars, records missing/unavailable date ranges as non-secret coverage diagnostics, and MUST NOT block V1 launch or freshness when 1h coverage is incomplete. `vn_prices_daily` is the freshness/launch-critical timeframe.
- **FR-010i**: The independent operator backfill runner MUST provide a `vn-history` plan as the V1 default, executing `vn_prices_daily` over the requested range as range-oriented daily-history operations and capping `vn_prices` 1h to the `vnstock` rolling window. The previous `market-history` US+Gold preset is preserved as a roadmap entry behind roadmap configuration and MUST NOT run by default in V1.
- **FR-010j**: Backfill diagnostics and CLI output MUST distinguish executed, failed, and skipped datasets with non-secret reasons; skipped unsupported historical sources MUST NOT be represented as successful ingestion jobs or persisted synthetic observations.
- **FR-010k**: [SUPERSEDED 2026-06-25 — VN-only V1 scope; preserved as roadmap requirement] US market ingestion MUST populate `us_prices` as recent 1h OHLCV bars through the shared stock time-series path with `market=US_STOCK`, and MUST populate `us_prices_daily` as the daily OHLCV base through a typed daily stock storage path; the phase 002 default backfill targets 7 days, while longer daily history is future provider-dependent work. Free-source historical limitations MUST be reported as recent intraday coverage for `us_prices` rather than full long-range 1h coverage.
- **FR-010l**: [SUPERSEDED 2026-06-25 — VN-only V1 scope; preserved as roadmap requirement] The US market overview instrument table and heatmap MUST include individual equities only. Indexes, volatility indexes, futures, and ETF proxy instruments may be used for mini chart/index summaries but MUST NOT appear as instrument rows or heatmap cells.
- **FR-010m**: [SUPERSEDED 2026-06-25 — VN-only V1 scope; preserved as roadmap requirement] The independent backfill CLI MUST provide a `us-daily-history` preset that runs only `us_prices_daily` as one range-oriented daily-history operation for the requested `from_date:to_date` scope; it MUST NOT run VN, XAUUSD, or SJC datasets. The documented first-run scope is 7 days.
- **FR-010n**: [SUPERSEDED 2026-06-25 — VN-only V1 scope; preserved as roadmap requirement] The independent backfill CLI MUST provide a `us-xauusd-history` preset for focused US/XAUUSD operator runs. It MUST run `us_prices_daily` and `xauusd_prices_daily` as range-oriented daily-history operations, run `us_prices` and `xauusd_prices` only over the recent free 1h coverage window, and MUST NOT run VN or SJC datasets.
- **FR-010o**: [SUPERSEDED 2026-06-25 — VN-only V1 scope; preserved as roadmap requirement] Real US/XAUUSD provider adapters MUST retry transient HTTP failures such as timeouts, connection errors, HTTP 429, and HTTP 5xx with bounded backoff before failing the ingestion job. Exhausted retries MUST produce non-secret diagnostics with provider, dataset, and sanitized error class/status. `xauusd_prices_daily` MUST fail when the provider returns no daily records for a historical range.
- **FR-010p**: [SUPERSEDED 2026-06-25 — VN-only V1 scope; preserved as roadmap requirement] The independent operator CLI MUST provide a `market-latest` preset that runs latest-mode current-data fetches for US and Gold-capable sources before historical backfill attempts.
- **FR-010q**: When a chart or workflow requests price data for a VN100 instrument that has no rows in `vn_prices_daily`, the ingestion service MUST trigger a single inline `latest`+`period` daily fetch through the same idempotent upsert path used by scheduled ingestion, subject to overlap blocking and rate guards. Lazy fetches MUST NOT execute `historical` mode; long-range backfill remains the independent worker's responsibility. References to tickers outside the VN100 universe MUST return out-of-scope without triggering ingestion.
- **FR-010r**: `vn_prices_daily` is the canonical VN timeframe for V1. Default instrument chart timeframe MUST be `1d`. `vn_prices` 1h records remain best-effort over the free `vnstock` rolling window and MUST NOT block V1 launch, freshness, or workflow execution when missing.
- **FR-010a**: Scheduled ingestion MUST be invoked through an explicit scheduler/worker contract rather than relying only on in-process app startup or demo history, and scheduled/manual runs MUST write to the canonical PostgreSQL storage.
- **FR-010b**: The scheduler/worker contract MUST be exposed as a protected API endpoint separate from the admin manual fetch endpoint and MUST invoke scheduled ingestion for V1 VN datasets.
- **FR-010g**: Web API endpoints MUST reject `historical` fetch execution with a clear message pointing operators to the independent backfill worker/script; the web app may display status and diagnostics for completed backfill jobs from the shared DB. Lazy on-first-access fetches (FR-010q) are `latest`+`period` and are exempt from this restriction.
- **FR-010h**: Web UI fetch controls MUST expose only `latest` and `period` modes; historical range controls MUST NOT appear in the V1 app UI.
- **FR-011**: Manual ingestion MUST be idempotent for the same dataset and period and MUST expose run status, timestamps, outcome, and diagnostic error context.
- **FR-011b**: In production mode, ingestion jobs, overlap checks, upserts, freshness, and market-data inspection MUST use PostgreSQL-backed persistence selected by `FINMIND_DATABASE_URL`; in-memory storage is allowed only when no database URL is configured for local/demo tests.
- **FR-011a**: Manual ingestion MUST block a request when the same dataset and period is already queued or running, returning a visible blocked status/message instead of starting duplicate work. Lazy on-first-access fetches MUST honor the same overlap guard.
- **FR-016**: System MUST record execution logs for ingestion jobs, generated artifacts, failures, and user-visible output status.
- **FR-018**: System MUST expose views where users can inspect ingestion-backed freshness and data status after the original job.
- **FR-018a**: V1 freshness calculation MUST use dataset-specific rules: `vn_prices_daily` is fresh when records cover the latest expected VN trading day, `vn_prices` is fresh when records cover the latest expected 1h bar inside the `vnstock` rolling coverage window, datasets with no time-series records are `missing`, and datasets whose latest ingestion job failed are `failed`. Roadmap dataset freshness paths (XAUUSD, SJC, US) remain implemented in code but are not part of V1 freshness output.
- **FR-018b**: V1 market data views MUST show a single VN market overview with no header market selector. Top index mini chart cards MUST include `VNINDEX`, `VN100`, `VN30`, `HNXINDEX`, and `UPCOM` in a single horizontal scroll row that fits four cards per desktop row when space allows, with index name, current price, change percent, change value, and line chart. The main view MUST include a sortable VN100 instrument table limited to 10 visible rows with columns Symbol, Sector, Price, Change, and Volume; a collection/sector-filtered VN100 heatmap as the final main-column section; and a right-side rail containing Watchlist first and a tabbed Gainers/Losers card second. Heatmap collection/sector controls MUST affect only the heatmap card. The market view MUST NOT expose a separate watchlist selector or a trailing instrument detail card.
- **FR-018f**: The V1 Market overview API MUST render VN instruments, heatmap rows, freshness metadata, and list prices from canonical `market_instruments`, `market_collection_memberships`, and `vn_prices_daily` rows. It MUST NOT use demo `MarketService` fixtures for VN overview after Phase 002; US/gold roadmap overview paths remain disabled unless a later spec re-enables them.
- **FR-018c**: Instrument detail charts MUST default to `1d` and MUST support `1h`, `4h`, `1d`, and `1M` timeframe selections where source data allows it. `4h` and `1M` MUST be derived from `vn_prices_daily` in V1; `1h` MUST be served from `vn_prices` over the available `vnstock` window with explicit coverage banners when bars are missing. VN instrument chart responses MUST render from canonical ingestion-backed rows only after phase 002; when lazy or scheduled ingestion fails or returns no rows, the API MUST return a missing/failed chart payload with freshness and lazy-fetch diagnostics rather than falling back to demo market fixtures.
- **FR-018d**: [SUPERSEDED 2026-06-25 — VN-only V1 scope; preserved as roadmap requirement] When charting `xauusd_prices` at `1h` and stored 1h bars are missing for dates covered by `xauusd_prices_daily`, the display API MUST synthesize hourly display bars from the daily close price for each hour in that day, mark those records with `display_fallback=true` and `source_grain=1d`, and keep the original daily observations in `xauusd_prices_daily` storage without treating synthesized records as persisted 1h provider data.
- **FR-018e**: V1 market data, admin ingestion, and workflow surfaces MUST be VN-only. Roadmap markets (US stocks, XAUUSD, SJC gold) MUST NOT appear as enabled choices, mini charts, instrument rows, freshness rows, or selectable workflow inputs in V1. If roadmap markets are surfaced for product preview, they MUST be disabled/marked out-of-scope before any submission rather than allowed and discovered only via backend validation error.
- **FR-019**: System MUST show clear behavior for missing data, stale data, failed sources, unsupported instruments, and unavailable citations.
- **FR-022**: System MUST keep provider-specific market data details abstract at the product contract level while allowing implementation-time provider validation for technical and licensing suitability.

## Key Entities

- Canonical Market Data Record
- Source Document
- Ingestion Job
- Market Instrument
- Market Collection
- Market Collection Membership
- Evidence Object
- Citation
- Execution Log

See `../system/state-model.md` for canonical entity definitions.

## Edge Cases

- Source data contains duplicate or corrected records: ingestion preserves canonical uniqueness and makes reruns safe.
- Multiple manual ingestion requests target the same dataset and period: the later request is blocked with a visible status/message while the earlier job is queued or running.
- A source fails: diagnostics are visible but secrets are not exposed.
- Data is stale, missing, or failed: freshness views and downstream workflow/chat results show clear warnings using dataset-specific freshness rules.
- Provider schema changes: connector-level handling reports failure without corrupting typed time-series records.
- Free provider limits: ingestion reports limited or unavailable historical coverage instead of filling synthetic data or blocking production launch solely for incomplete long-range 1h VN coverage.
- VN historical and latest fetches diverge in implementation: this is invalid for phase 002; both must use the canonical 1h ingestion mechanism.
- Web app executes long historical backfill inline: this is invalid for phase 002; use the independent backfill worker/script.
- SJC official current quote scraping is requested for a historical range: the independent runner skips that dataset with a clear diagnostic until a historical SJC source/archive is added.
- XAUUSD long-range 1h backfill is requested through free resources: the independent runner uses recent free 1h coverage plus the daily fallback for long-range chart continuity, and display APIs may synthesize hourly display bars from stored daily fallback rows without persisting them as provider-sourced 1h rows.

## Success Criteria

- **SC-004**: 100% of ingestion jobs display trigger type, status, start time, end time or active state, dataset scope, and success or failure outcome.
- **SC-005**: Re-running ingestion for the same dataset and period does not create duplicate time-series records in validation scenarios.
- **SC-007**: Users can identify stale, missing, failed, or out-of-scope data conditions from the UI without reading server logs.

## Out Of Scope

- Evidence-backed chat; see `../003-evidence-backed-chat/`.
- Production plugin adapter; see `../004-extension-hardening/`.
- US stocks and BTC as V1 user-facing datasets (roadmap; US connector code and `us_prices*` schemas remain dormant in V1).
- XAUUSD and SJC gold as V1 user-facing datasets (roadmap; yfinance/Alpha Vantage/SJC connector code and `xauusd_prices*` / `sjc_gold_prices` schemas remain dormant in V1).
- Open on-demand instrument creation outside the pre-seeded VN100 universe.
- Treating demo/mock market fixtures as a Phase 002 completion substitute.
