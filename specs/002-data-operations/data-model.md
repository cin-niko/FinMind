---
id: SPEC-FEAT-002-DATA
feature: data-operations
status: draft
owner: solo
created: 2026-06-18
implements: []
validated_by:
  - tests/test_platform_services.py
adr_refs: []
---

# Data Model: Data Operations

This feature extends use of shared entities from `../system/state-model.md`.

## Storage Decision

PostgreSQL-compatible TimescaleDB is the canonical database service for phase 002. Tests and local verification use TimescaleDB/PostgreSQL provisioned through Docker Compose so idempotent upserts, constraints, hypertables, typed time-series indexes, and concurrent worker/API behavior are validated against the same database family used by the application.

Feature-owned usage:

- `IngestionJob`: scheduled/manual fetch operation with dataset scope, period, trigger, status, timestamps, record count, and diagnostics.
- `CanonicalMarketDataRecord`: logical product contract for ingestion-backed VN stock and gold observations. Phase 002 stores these observations physically in typed time-series tables with uniqueness rules.
- `SourceDocument`: company reports, macro news, market news, and document-like evidence sources.
- `MarketInstrument`: supported VN stock and gold instrument metadata.
- `MarketCollection`: index groups, predefined watchlists, sector groups, and thematic groups used by Market UI filters.
- `MarketCollectionMembership`: effective-dated links between instruments and collections.
- `EvidenceObject` and `Citation`: source material exposed downstream to workflows and chat.

Rules:

- Each typed time-series table defines a dataset-specific uniqueness boundary.
- Manual reruns update or replace matching logical records instead of duplicating them.
- Failed ingestion jobs record non-secret diagnostics.
- Production ingestion selects PostgreSQL persistence when `FINMIND_DATABASE_URL` is
  configured. In-memory persistence is limited to local/demo tests with no database URL.
- Real provider fetching uses one configured adapter per dataset. Provider responses
  are normalized into the typed canonical schemas below before persistence.

## Provider Configuration

The runtime chooses each source independently. `mock` uses deterministic local data
for tests and demos. Real values select the implemented free adapters.

Environment variables:

| Variable | Required | Notes |
|----------|----------|-------|
| `FINMIND_DATABASE_URL` | production yes | PostgreSQL/TimescaleDB connection URL used by the ingestion store. |
| `FINMIND_VN_PROVIDER` | no | `mock` by default; `vnstock` selects the real VN stock adapter. |
| `FINMIND_US_PROVIDER` | no | `mock` by default; `yfinance` selects the real US stock recent 1h adapter; `us_prices_daily` uses a no-key daily CSV source for daily history. |
| `FINMIND_XAUUSD_PROVIDER` | no | `mock` by default; `yfinance` selects the real XAUUSD 1h adapter. |
| `FINMIND_XAUUSD_DAILY_FALLBACK` | no | `alpha_vantage` when enabled by real XAUUSD configuration; used when 1h historical coverage is unavailable. |
| `FINMIND_SJC_PROVIDER` | no | `mock` by default; `sjc_official` selects the real SJC daily quote adapter. |
| `FINMIND_VNSTOCK_API_KEY` | `vnstock` yes | Server-side VNStock API key. Must not appear in diagnostics, logs, fixtures, or API responses. |
| `FINMIND_ALPHA_VANTAGE_API_KEY` | no | Server-side Alpha Vantage key for XAUUSD daily fallback. Must not appear in diagnostics, logs, fixtures, or API responses. |
| `FINMIND_PROVIDER_TIMEOUT_SECONDS` | no | Provider timeout; defaults to a conservative value. |

Real provider set:

| Dataset | Provider | Historical policy | Notes |
|---------|----------|-------------------|-------|
| `vn_prices` | `vnstock` | 1h for both pre-production historical backfill and post-launch latest fetches, where `vnstock` history allows the requested range. | Adapter must record range/rate limitations and missing long-range coverage in diagnostics. |
| `us_prices` | yfinance/Yahoo Finance | Recent rolling 1h history for US individual equities. | Adapter must not imply full long-range 1h coverage. |
| `us_prices_daily` | Stooq/no-key daily CSV | Daily history for US individual equities. | This is the canonical daily base for US market charts and backfill; phase 002 starts with a 1-month operational baseline, and operators should use the `us-daily-history` preset to avoid running VN/gold providers when fetching only US daily bars. |
| `xauusd_prices` | yfinance/Yahoo Finance | Recent rolling 1h history. | The operator backfill plan caps long-range 1h execution to the recent free-provider window and must not imply full long-range 1h coverage. |
| `xauusd_prices_daily` | Alpha Vantage free gold history fallback | Daily long-history fallback. | Used for long-range chart/backfill when free 1h XAUUSD is unavailable. |
| `sjc_gold_prices` | Official SJC website/chart surfaces | Current daily buy/sell quotes unless a true historical archive is configured. | Scraper/importer must attribute SJC and avoid raw page dumps in diagnostics; the operator backfill plan skips multi-day historical SJC ranges rather than duplicating current quotes into past dates. |

Provider response contract:

- Adapters fetch the requested `period=<YYYY-MM-DD>` or planned historical range
  through their provider-specific SDK/API.
- Provider output is normalized into an array of records or an object with a
  `records` array before schema validation.
- Each record must include fields needed by the dataset-specific schema below.
- Connectors generate deterministic `record_key` values from canonical observation keys
  when the provider does not supply one.
- Connector diagnostics may include source id, dataset id, status, and field names, but
  must not include tokens, raw authorization headers, or full provider payload dumps.
- Real-source adapters must expose capability diagnostics such as supported interval,
  date range, rate-limit status, and fallback usage without treating unavailable free
  history as missing provider credentials.
- VN stock historical backfill and latest fetches share the same 1h provider/upsert
  path into `stock_1h_bars`; incomplete long-range 1h coverage is represented as
  coverage diagnostics, not synthetic bars and not a production launch blocker.
- XAUUSD long-range backfill uses `xauusd_prices_daily` for full-range persistence
  and recent-window `xauusd_prices` for true provider 1h bars. Display-only hourly
  fallback bars may be derived from daily records, but they are not persisted as
  provider-sourced 1h observations.
- The optional focused US/XAUUSD run uses the `us-xauusd-history` preset, which fetches
  US daily, recent US 1h, XAUUSD daily fallback, and recent XAUUSD 1h data without
  running VN or SJC providers.
- SJC historical backfill requires a real historical SJC source/archive. The
  currently configured official current quote adapter may populate latest or
  single-day operational quotes, but it is not a historical archive.

## PostgreSQL Tables

Phase 002 stores the following tables in a PostgreSQL-compatible TimescaleDB service:

- `market_instruments`: supported VN stock, XAUUSD, and VN SJC gold instrument metadata.
- `market_collections`: supported index groups, predefined watchlists, sector groups, and thematic groups.
- `market_collection_memberships`: effective-dated membership links from instruments to collections.
- `stock_1h_bars`: typed 1h OHLCV bars for stock datasets, including `vn_prices` and `us_prices`.
- `stock_daily_bars`: typed daily OHLCV bars for stock datasets, including `us_prices_daily`.
- `xauusd_1h_bars`: typed 1h OHLC bars for XAUUSD.
- `xauusd_daily_bars`: typed daily OHLC fallback bars for XAUUSD long history when
  free 1h historical data is unavailable.
- `sjc_gold_daily_quotes`: typed daily VN SJC gold buy/sell/reference quotes.
- `source_documents`: document-like source material for reports, macro/news, and future approved workflow sources, including source identity, publication/collection timestamps, references, excerpts/summaries, and market scope.
- `ingestion_jobs`: scheduled/manual job history with source/dataset scope, period, trigger, status, timestamps, affected record count, and JSONB non-secret diagnostics.
- `execution_logs`: user-visible ingestion/workflow execution events, failures, artifact status, and output status.
- `evidence_objects`: grounding units that reference typed time-series records, source documents, or artifacts and carry freshness status.
- `citations`: user-visible source references linked to evidence objects.
- `artifacts`: generated charts, tables, computed outputs, and future inline visualizations with JSONB renderable payloads and evidence references.

Relational constraints:

- `stock_1h_bars` has a unique constraint on `(market, instrument_id, interval_start)`.
- `xauusd_1h_bars` has a unique constraint on `(instrument_id, interval_start)`.
- `sjc_gold_daily_quotes` has a unique constraint on `(instrument_id, quote_type, quote_date)`.
- `market_collections` has a unique constraint on `(market, collection_id)`.
- `market_collection_memberships` has a unique constraint on `(collection_id, instrument_id, effective_from)`.
- `market_instruments.instrument_id` is referenced by time-series records.
- `market_collection_memberships.instrument_id` references `market_instruments.instrument_id`.
- `ingestion_jobs` supports overlap checks by dataset/source, period, and active statuses `queued` or `running`.
- `citations.evidence_id` references `evidence_objects.evidence_id`.
- Evidence and artifact reference fields preserve traceability to typed time-series records, source documents, artifacts, or execution context without storing provider secrets.
- `stock_1h_bars`, `xauusd_1h_bars`, `xauusd_daily_bars`, and
  `sjc_gold_daily_quotes` are TimescaleDB hypertables or equivalent PostgreSQL time
  partitions keyed by their time column.

## Market Dataset Schemas

Phase 002 stores one typed time-series row per logical price observation. Shared metadata, ingestion, evidence, citation, and artifact contracts remain common, but price observations use typed relational columns so 10-year multi-market chart queries can use efficient table-specific indexes and later time partitions.

Common columns for all time-series price tables:

| Column | Type | Required | Notes |
|--------|------|----------|-------|
| `instrument_id` | text | yes | References `market_instruments.instrument_id`. |
| `collected_at` | timestamptz | yes | Ingestion collection timestamp. |
| `source_id` | text | yes | Source connector identity, provider-neutral at product-contract level. |
| `freshness_status` | text | yes | `fresh`, `stale`, `missing`, or `failed`. |

## Market Metadata Schemas

### `market_instruments`

Stores instrument identity and classification metadata used by filters, heatmaps, watchlists, and detail pages.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `instrument_id` | text | yes | Stable id such as `vn_stock:VPB`, `gold:XAUUSD`, or `gold:SJC`. |
| `symbol` | text | yes | Display symbol such as `VPB`, `XAUUSD`, or `SJC`. |
| `market` | text | yes | `VN_STOCK` or `GOLD` in V1. |
| `asset_class` | text | yes | `stock`, `commodity`, or future approved classes. |
| `exchange` | text | no | Exchange/board such as `HOSE`, `HNX`, `UPCOM`, or source venue. |
| `display_name` | text | yes | User-facing instrument name. |
| `currency` | text | yes | Quote currency. |
| `sector` | text | no | Sector classification, e.g. `Financials`. |
| `industry` | text | no | Industry classification, e.g. `Banking`. |
| `sub_industry` | text | no | Optional deeper classification. |
| `status` | text | yes | `active`, `inactive`, or `unsupported`. |

### `market_collections`

Stores reusable display groups for index strips, watchlists, heatmap filters, and list filters.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `collection_id` | text | yes | Stable id such as `vnindex`, `vn30`, `vn100`, `vnenergy`, or `watchlist:default-vn`. |
| `market` | text | yes | `VN_STOCK` or `GOLD` in V1. |
| `name` | text | yes | User-facing label. |
| `collection_type` | text | yes | `index`, `watchlist`, `sector`, or `theme`. |
| `description` | text | no | Short non-provider-specific description. |
| `sort_order` | integer | no | Stable UI ordering. |

### `market_collection_memberships`

Stores effective-dated membership for indexes, watchlists, sectors, and themes.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `collection_id` | text | yes | References `market_collections.collection_id`. |
| `instrument_id` | text | yes | References `market_instruments.instrument_id`. |
| `weight` | number | no | Index/watchlist weight when available. |
| `effective_from` | date | yes | Membership start date. |
| `effective_to` | date | no | Membership end date; null means active. |

Initial VN collections include `vnindex`, `vn30`, `vn100`, and sector/theme collections such as `vnenergy` and `vnbanking` when source membership is available.

### Stock Dataset: `stock_1h_bars`

Initial datasets: `vn_prices`, `us_prices`

Supported markets: `VN_STOCK`, `US_STOCK`

Grain: one 1h OHLCV bar per stock instrument and trading interval.

Record identity:

- `instrument_id`: stable stock instrument id, e.g. `vn_stock:VCB` or `us_stock:SPY`.
- Uniqueness: `(market, instrument_id, interval_start)`.

Columns:

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `market` | text | yes | `VN_STOCK` or `US_STOCK`. |
| `symbol` | string | yes | Exchange symbol such as `VCB` or `SPY`. |
| `exchange` | string | yes | Exchange or board label such as `HOSE`, `HNX`, `UPCOM`, `NYSE`, `NASDAQ`, or `NYSEARCA`. |
| `interval_start` | timestamptz | yes | UTC start of the 1h interval. |
| `interval_end` | timestamptz | yes | UTC end of the 1h interval. |
| `open` | number | yes | 1h open price in `currency`. |
| `high` | number | yes | 1h high price in `currency`. |
| `low` | number | yes | 1h low price in `currency`. |
| `close` | number | yes | 1h close price in `currency`. |
| `volume` | integer | yes | Matched volume for the 1h interval. |
| `value` | number | no | Matched traded value when available. |
| `currency` | string | yes | `VND`. |
| `adjusted_close` | number | no | Adjusted close when available. |
| `corporate_action_flag` | boolean | no | Indicates split/dividend/adjustment context when available. |
| `collected_at` | timestamptz | yes | Ingestion collection timestamp. |
| `source_id` | text | yes | Source connector identity. |
| `freshness_status` | text | yes | `fresh`, `stale`, `missing`, or `failed`. |

Chart-ready mapping:

- Candlestick: `time = interval_start`, `open`, `high`, `low`, `close`.
- Volume histogram: `time = interval_start`, `value = volume`.
- Table fallback includes symbol, exchange, interval start/end, OHLC, volume, currency, source, and freshness.

Validation rules:

- `open`, `high`, `low`, and `close` must be non-negative.
- `high` must be greater than or equal to `open`, `low`, and `close`.
- `low` must be less than or equal to `open`, `high`, and `close`.
- `volume` must be greater than or equal to zero.
- TimescaleDB hypertable time column: `interval_start`.
- Recommended indexes: unique `(market, instrument_id, interval_start)` and range index `(market, instrument_id, interval_start)`.

### International Gold Dataset: `xauusd_1h_bars`

Dataset: `xauusd_prices`

Grain: one 1h OHLC bar per XAUUSD instrument and trading interval.

Record identity:

- `instrument_id`: stable gold instrument id, e.g. `gold:XAUUSD`.
- Uniqueness: `(instrument_id, interval_start)`.

Columns:

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `symbol` | string | yes | `XAUUSD`. |
| `interval_start` | timestamptz | yes | UTC start of the 1h interval. |
| `interval_end` | timestamptz | yes | UTC end of the 1h interval. |
| `open` | number | yes | 1h open price in `currency`. |
| `high` | number | yes | 1h high price in `currency`. |
| `low` | number | yes | 1h low price in `currency`. |
| `close` | number | yes | 1h close price in `currency`. |
| `unit` | string | yes | `oz`. |
| `currency` | string | yes | `USD`. |
| `collected_at` | timestamptz | yes | Ingestion collection timestamp. |
| `source_id` | text | yes | Source connector identity. |
| `freshness_status` | text | yes | `fresh`, `stale`, `missing`, or `failed`. |

Chart-ready mapping:

- Candlestick: `time = interval_start`, `open`, `high`, `low`, `close`.
- Table fallback includes symbol, interval start/end, OHLC, unit, currency, source, and freshness.

Validation rules:

- `open`, `high`, `low`, and `close` must be non-negative.
- `high` must be greater than or equal to `open`, `low`, and `close`.
- `low` must be less than or equal to `open`, `high`, and `close`.
- TimescaleDB hypertable time column: `interval_start`.
- Recommended indexes: unique `(instrument_id, interval_start)` and range index `(instrument_id, interval_start)`.

### International Gold Daily Fallback: `xauusd_daily_bars`

Dataset: `xauusd_prices_daily`

Real provider fallback source: Alpha Vantage free gold history fallback.

Grain: one daily OHLC bar per XAUUSD/gold instrument and trading date.

Purpose: preserve long-history XAUUSD charts when free 1h intraday history is
unavailable. The system must label this as daily fallback coverage rather than
claiming 1h coverage.

Record identity:

- `instrument_id`: stable gold instrument id, e.g. `gold:XAUUSD`.
- Uniqueness: `(instrument_id, trading_date)`.

Columns:

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `symbol` | string | yes | `XAUUSD` or provider-equivalent gold spot symbol. |
| `trading_date` | date | yes | UTC trading date. |
| `open` | number | yes | Daily open price in `currency`. |
| `high` | number | yes | Daily high price in `currency`. |
| `low` | number | yes | Daily low price in `currency`. |
| `close` | number | yes | Daily close price in `currency`. |
| `unit` | string | yes | `oz`. |
| `currency` | string | yes | `USD`. |
| `collected_at` | timestamptz | yes | Ingestion collection timestamp. |
| `source_id` | text | yes | Source connector identity. |
| `freshness_status` | text | yes | `fresh`, `stale`, `missing`, or `failed`. |

Validation rules:

- `open`, `high`, `low`, and `close` must be non-negative.
- `high` must be greater than or equal to `open`, `low`, and `close`.
- `low` must be less than or equal to `open`, `high`, and `close`.
- TimescaleDB hypertable time column: `trading_date`.
- Recommended indexes: unique `(instrument_id, trading_date)` and range index
  `(instrument_id, trading_date)`.

### VN Gold Dataset: `sjc_gold_daily_quotes`

Dataset: `sjc_gold_prices`

Grain: one daily SJC gold quote per product, quote type, and quote date.

Record identity:

- `instrument_id`: stable VN gold instrument id, e.g. `gold:SJC`.
- Uniqueness: `(instrument_id, quote_type, quote_date)`.

Columns:

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `symbol` | string | yes | Gold product code such as `SJC`. |
| `quote_type` | string | yes | `buy_sell` or `reference`. |
| `quote_date` | date | yes | VN business date. |
| `buy_price` | number | no | Buy price when source provides a spread. |
| `sell_price` | number | no | Sell price when source provides a spread. |
| `price` | number | no | Single reference price when buy/sell are not provided. |
| `unit` | string | yes | Initial value: `tael`. |
| `currency` | string | yes | `VND`. |
| `location` | string | no | VN market/location label when available. |
| `collected_at` | timestamptz | yes | Ingestion collection timestamp. |
| `source_id` | text | yes | Source connector identity. |
| `freshness_status` | text | yes | `fresh`, `stale`, `missing`, or `failed`. |

Chart-ready mapping:

- Line series: `time = quote_date`, `value = price` when present, otherwise midpoint of `buy_price` and `sell_price`.
- Spread table: buy price, sell price, midpoint, unit, currency, location, source, and freshness.

Validation rules:

- At least one of `price` or both `buy_price` and `sell_price` must be present.
- `price`, `buy_price`, and `sell_price` must be non-negative when present.
- `sell_price` must be greater than or equal to `buy_price` when both are present.
- TimescaleDB hypertable time column: `quote_date`.
- Recommended indexes: unique `(instrument_id, quote_type, quote_date)` and range index `(instrument_id, quote_date)`.
