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
- Q: How should real provider fetching be configured? → A: Use one provider variable per supported dataset (`FINMIND_VN_PROVIDER`, `FINMIND_XAUUSD_PROVIDER`, and `FINMIND_SJC_PROVIDER`) with `mock` for deterministic local data and the implemented real provider for live fetches; provider API keys are separate (`FINMIND_VNSTOCK_API_KEY`, `FINMIND_ALPHA_VANTAGE_API_KEY`), remain server-side, and never appear in API responses, diagnostics, logs, or tests.
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

## User Scenarios & Testing

### User Story 1 - Control And Monitor Ingestion (Priority: P1)

An authenticated internal admin monitors scheduled market data ingestion, manually triggers safe reruns or backfills, and sees job status, freshness, and failure information for supported VN stock and gold datasets.

**Independent Test**: Log in as admin, view ingestion status, trigger manual fetches for VN stock and gold datasets, rerun one fetch for the same period, and verify that job status, timestamps, outcome, freshness metadata, and time-series records update without duplicates.

Acceptance scenarios:

1. Given the admin panel is open, when the admin views ingestion status, then the system shows latest scheduled and manual job outcomes, freshness timestamps, and any errors for each supported dataset.
2. Given a manual ingestion job is triggered for an already-ingested period, when the job completes, then typed time-series records are updated idempotently and downstream freshness metadata reflects the completed run.
3. Given an ingestion source fails, when the admin reviews the job, then the system displays failure status and diagnostic context without exposing secrets.
4. Given multiple manual ingestion requests target the same dataset and period, when overlap would be unsafe, then the system blocks the later request with visible status.

### User Story 2 - Inspect Market Data (Priority: P2)

An authenticated internal admin inspects chart-ready time-series records and freshness metadata for supported datasets.

**Independent Test**: Open the market data view after ingestion, select a VN stock or gold dataset, and verify chart-ready records, freshness state, and table fallback.

Acceptance scenarios:

1. Given the Market page is open, when the admin selects `VN`, then the page shows top index mini charts for `VNINDEX`, `VN100`, `VN30`, `HNXINDEX`, and `UPCOM`, a sortable instrument list, and a filterable market heatmap with no trailing instrument detail card.
2. Given the admin filters the heatmap by a collection such as `VN30`, `VN100`, or a sector collection, then only the heatmap cells update to matching instruments while the instrument table, Watchlist, and Gainers/Losers rail remain scoped to the selected market.
3. Given the admin clicks a stock row or heatmap cell, when the selection changes, then the selected state updates without navigating away from the market overview layout.

## Functional Requirements

- **FR-008**: System MUST maintain ingestion-backed time-series storage for supported VN stock and gold datasets with source identity, collection time, effective market time, freshness metadata, and uniqueness rules.
- **FR-008a**: Phase 002 MUST use a PostgreSQL-compatible TimescaleDB service as the canonical application database for ingestion-backed storage; tests and local verification MUST use a TimescaleDB/PostgreSQL instance provisioned through Docker Compose rather than SQLite or in-memory-only persistence.
- **FR-008b**: PostgreSQL storage MUST include shared tables for market instruments, source documents, ingestion jobs, execution logs, evidence objects, citations, and artifacts, plus typed time-series tables for stock 1h bars, XAUUSD 1h bars, and SJC gold daily quotes; JSONB is allowed for diagnostics, source excerpts/summaries, artifact payloads, and execution output fields that remain provider- or artifact-shaped.
- **FR-008c**: Time-series tables MUST enforce dataset-specific uniqueness for their logical observation keys, ingestion jobs MUST support lookup and overlap checks by dataset/source, period, and active status, and traceability tables MUST preserve links from citations/evidence/artifacts back to time-series records, source documents, or execution context.
- **FR-008d**: `vn_prices` records MUST be stored in a typed stock 1h bars table keyed by market, instrument, and interval start; `xauusd_prices` records MUST be stored in a typed XAUUSD 1h bars table keyed by instrument and interval start; and `sjc_gold_prices` records MUST be stored in a typed SJC gold daily quotes table keyed by instrument, quote type, and quote date, using the schemas in `data-model.md`.
- **FR-008e**: The stock 1h bars, XAUUSD 1h bars, and SJC gold daily quote tables MUST be created as TimescaleDB hypertables or equivalent PostgreSQL time partitions, while shared metadata/evidence tables remain regular relational tables.
- **FR-008f**: Market instruments MUST store classification metadata needed for display filters, including asset class, sector, industry, optional sub-industry, exchange, currency, status, and display name.
- **FR-008g**: PostgreSQL storage MUST include market collection tables for index groups, predefined watchlists, sectors, and thematic groups, with membership records linking instruments to collections over effective date ranges.
- **FR-009**: System MUST ingest and expose chart-ready `vn_prices`, `xauusd_prices`, and `sjc_gold_prices` datasets in the initial implementation.
- **FR-009b**: Production ingestion MUST select source adapters with per-dataset provider variables: `FINMIND_VN_PROVIDER=mock|vnstock`, `FINMIND_US_PROVIDER=mock|yfinance`, `FINMIND_XAUUSD_PROVIDER=mock|yfinance`, `FINMIND_SJC_PROVIDER=mock|sjc_official`, and optional `FINMIND_XAUUSD_DAILY_FALLBACK=alpha_vantage`.
- **FR-009f**: Provider credentials MUST be configured with provider-specific variables, not a shared token. `FINMIND_VNSTOCK_API_KEY` is required when `FINMIND_VN_PROVIDER=vnstock`; `FINMIND_ALPHA_VANTAGE_API_KEY` is used only by the Alpha Vantage XAUUSD daily fallback.
- **FR-009c**: Source adapters MUST normalize provider responses into the typed canonical schemas in `data-model.md`; invalid, missing, or unsupported provider fields MUST fail the ingestion job without writing partial corrupt records.
- **FR-009d**: The initial no-cost real provider set MUST support `vnstock` for VN stock history, yfinance/Yahoo Finance for recent XAUUSD intraday bars, Alpha Vantage free gold history as a daily XAUUSD fallback, and official SJC website/chart ingestion for SJC daily buy/sell quotes.
- **FR-009e**: Real-source adapters MUST record provider capability limits in ingestion diagnostics and freshness views; unavailable 1h historical ranges MUST degrade to daily XAUUSD history rather than pretending 1h coverage exists.
- **FR-009a**: Source contracts MUST preserve extension points for indicators, company reports where applicable, macro news, and other source material required by approved workflows, but those sources are not required to be populated in the initial implementation unless an approved workflow declares them as required datasets.
- **FR-010**: System MUST support both externally scheduled ingestion jobs and admin-triggered manual ingestion jobs for supported VN stock and gold datasets.
- **FR-010c**: Fetch requests MUST support `latest`, `period`, and `historical` modes. `historical` requests MUST include `from_date` and `to_date`; `period` requests MUST include `period`; `latest` requests MUST derive the latest expected date server-side.
- **FR-010d**: Historical fetches MUST run from an independent worker/script process, split inclusive date ranges into provider-safe periods, fetch each period through the selected source adapter, and write all returned records through the same idempotent PostgreSQL upsert path used by latest fetches.
- **FR-010e**: VN stock pre-production historical backfill and post-launch latest fetching MUST use the same canonical 1h ingestion mechanism and write to the same typed `stock_1h_bars` storage path; daily VN stock ingestion MUST NOT be introduced as a separate production mechanism in phase 002 unless a later spec explicitly changes the timeframe policy.
- **FR-010f**: VN stock historical 1h backfill MUST be treated as provider best-effort: ingestion records all returned 1h bars, records missing/unavailable date ranges as non-secret coverage diagnostics, and MUST NOT block production launch solely because the free provider lacks complete long-range 1h coverage.
- **FR-010i**: The independent operator backfill runner MUST support a market-history plan for the initial datasets. The phase 002 default run currently targets a 7-day operational baseline for US and Gold-capable sources while VNStock historical backfill is paused; it MUST execute `us_prices_daily` and `xauusd_prices_daily` over the requested range when configured, cap `xauusd_prices` 1h execution to the recent free-provider coverage window, and skip `sjc_gold_prices` historical ranges when only the current official SJC quote source is configured. VN historical backfill MAY be run separately only when a stable provider path is available.
- **FR-010j**: Backfill diagnostics and CLI output MUST distinguish executed, failed, and skipped datasets with non-secret reasons; skipped unsupported historical sources MUST NOT be represented as successful ingestion jobs or persisted synthetic observations.
- **FR-010k**: US market ingestion MUST populate `us_prices` as recent 1h OHLCV bars through the shared stock time-series path with `market=US_STOCK`, and MUST populate `us_prices_daily` as the daily OHLCV base through a typed daily stock storage path; the phase 002 default backfill targets 7 days, while longer daily history is future provider-dependent work. Free-source historical limitations MUST be reported as recent intraday coverage for `us_prices` rather than full long-range 1h coverage.
- **FR-010l**: The US market overview instrument table and heatmap MUST include individual equities only. Indexes, volatility indexes, futures, and ETF proxy instruments may be used for mini chart/index summaries but MUST NOT appear as instrument rows or heatmap cells.
- **FR-010m**: The independent backfill CLI MUST provide a `us-daily-history` preset that runs only `us_prices_daily` as one range-oriented daily-history operation for the requested `from_date:to_date` scope; it MUST NOT run VN, XAUUSD, or SJC datasets. The documented first-run scope is 7 days.
- **FR-010n**: The independent backfill CLI MUST provide a `us-xauusd-history` preset for focused US/XAUUSD operator runs. It MUST run `us_prices_daily` and `xauusd_prices_daily` as range-oriented daily-history operations, run `us_prices` and `xauusd_prices` only over the recent free 1h coverage window, and MUST NOT run VN or SJC datasets.
- **FR-010o**: Real US/XAUUSD provider adapters MUST retry transient HTTP failures such as timeouts, connection errors, HTTP 429, and HTTP 5xx with bounded backoff before failing the ingestion job. Exhausted retries MUST produce non-secret diagnostics with provider, dataset, and sanitized error class/status. `xauusd_prices_daily` MUST fail when the provider returns no daily records for a historical range.
- **FR-010p**: The independent operator CLI MUST provide a `market-latest` preset that runs latest-mode current-data fetches for US and Gold-capable sources before historical backfill attempts. The preset MUST include `us_prices`, `xauusd_prices`, and `sjc_gold_prices`, MUST NOT call `vn_prices` while VNStock historical/default operations are paused, and MUST write through the same idempotent ingestion service path used by scheduled fetches.
- **FR-010a**: Scheduled ingestion MUST be invoked through an explicit scheduler/worker contract rather than relying only on in-process app startup or demo history, and scheduled/manual runs MUST write to the canonical PostgreSQL storage.
- **FR-010b**: The scheduler/worker contract MUST be exposed as a protected API endpoint separate from the admin manual fetch endpoint and MUST invoke scheduled ingestion for supported datasets.
- **FR-010g**: Web API endpoints MUST reject `historical` fetch execution with a clear message pointing operators to the independent backfill worker/script; the web app may display status and diagnostics for completed backfill jobs from the shared DB.
- **FR-010h**: Web UI fetch controls MUST expose only `latest` and `period` modes; historical range controls MUST NOT appear in the app UI for VN stocks, XAUUSD, or SJC gold.
- **FR-011**: Manual ingestion MUST be idempotent for the same dataset and period and MUST expose run status, timestamps, outcome, and diagnostic error context.
- **FR-011b**: In production mode, ingestion jobs, overlap checks, upserts, freshness, and market-data inspection MUST use PostgreSQL-backed persistence selected by `FINMIND_DATABASE_URL`; in-memory storage is allowed only when no database URL is configured for local/demo tests.
- **FR-011a**: Manual ingestion MUST block a request when the same dataset and period is already queued or running, returning a visible blocked status/message instead of starting duplicate work.
- **FR-016**: System MUST record execution logs for ingestion jobs, generated artifacts, failures, and user-visible output status.
- **FR-018**: System MUST expose views where users can inspect ingestion-backed freshness and data status after the original job.
- **FR-018a**: Freshness calculation MUST use dataset-specific rules: `vn_prices` and `xauusd_prices` are fresh when records cover the latest expected 1h interval for their market calendars, `sjc_gold_prices` is fresh when records cover the latest expected VN business day quote, datasets with no time-series records are `missing`, and datasets whose latest ingestion job failed are `failed`.
- **FR-018b**: Market data views MUST support a header market selector where `VN` is displayed as a VN Markets choice with a flag indicator and `US` is displayed as a US Markets choice with a flag indicator. VN top index mini chart cards MUST include `VNINDEX`, `VN100`, `VN30`, `HNXINDEX`, and `UPCOM`; US top index mini chart cards MUST include S&P 500, NASDAQ 100, Dow, Russell 2000, and VIX using supported index/proxy summaries where direct index data is unavailable. Mini charts appear in a single horizontal scroll row that fits four cards per desktop row when space allows, with index name/current price/change percent/change value/line chart. The main market view MUST include a sortable instrument table limited to 10 visible individual-equity rows with columns Symbol, Sector, Price, Change, and Volume, a collection/sector-filtered heatmap of individual equities as the final main-column section, and a right-side rail containing Watchlist first and a tabbed Gainers/Losers card second. Heatmap collection/sector controls MUST affect only the heatmap card; they MUST NOT refetch or rescope the instrument table, Watchlist, Gainers, or Losers. The market view MUST NOT expose a separate watchlist selector or trailing instrument detail card in phase 002.
- **FR-018c**: Instrument detail charts MUST support `1h`, `4h`, `1d`, and `1M` timeframe selections where source data allows it; `4h`, `1d`, and `1M` stock/XAUUSD bars may be derived from stored 1h bars, XAUUSD long-history views may use daily fallback records when free 1h history is unavailable, and SJC gold supports daily and monthly views derived from daily quotes.
- **FR-018d**: When charting `xauusd_prices` at `1h` and stored 1h bars are missing for dates covered by `xauusd_prices_daily`, the display API MUST synthesize hourly display bars from the daily close price (`open = high = low = close = daily close`) for each hour in that day, mark those records with `display_fallback=true` and `source_grain=1d`, and keep the original daily observations in `xauusd_prices_daily` storage without treating synthesized records as persisted 1h provider data.
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
- US stocks and BTC as user-facing datasets.
