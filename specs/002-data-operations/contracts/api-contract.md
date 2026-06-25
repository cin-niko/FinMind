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
- `mode`: `latest` or `period`
- `period` for `period` mode

Response includes job status and record count. Unsafe overlap returns blocked status with a clear message.
`historical` mode is rejected by the web API with a clear message directing operators
to the independent backfill worker/script.
When real providers are configured, failures return a failed job with non-secret
diagnostics; bearer tokens, authorization headers, and raw provider payloads are
never returned.

## `POST /api/worker/ingestion/scheduled`

Protected scheduler/worker endpoint that invokes scheduled ingestion for supported VN stock and gold datasets.

Request includes:

- `source_id`
- optional `mode`; defaults to `latest`
- optional `period` for explicit scheduled reruns

Response includes scheduled job status, dataset scope, and record count. Unsafe overlap returns blocked status with a clear message.
The worker endpoint uses the same configured source connectors and PostgreSQL-backed
persistence as manual ingestion when `FINMIND_DATABASE_URL` is configured.
`historical` mode is rejected by the web API; long historical backfills run through
the independent worker/script:

```bash
uv run python -m api.platform.ingestion.backfill \
  --source-id vn_prices \
  --from-date 2026-06-18 \
  --to-date 2026-06-25
```

## `GET /api/market-data/{dataset_id}`

Returns chart-ready time-series records for supported initial datasets `vn_prices`, `xauusd_prices`, and `sjc_gold_prices`. Responses include freshness metadata and omit provider secrets.

For `vn_prices`, records include chart-ready 1h OHLCV fields: `time`, `open`, `high`, `low`, `close`, `volume`, plus table metadata for symbol, exchange, currency, source, and freshness.

For `xauusd_prices`, records include chart-ready 1h OHLC fields: `time`, `open`, `high`, `low`, `close`, plus unit, currency, source, and freshness.
If no stored 1h bar exists for an hour but a stored `xauusd_prices_daily` record
covers the same date, the response may include synthesized display bars where
`open`, `high`, `low`, and `close` equal the daily close. These records must include
`display_fallback: true`, `source_grain: "1d"`, and a source reference to the daily
fallback record so clients can render a smooth chart without mistaking it for real
intraday data.

For `xauusd_prices_daily`, records include chart-ready daily fallback OHLC fields:
`time`, `open`, `high`, `low`, `close`, plus unit, currency, source, freshness, and
a fallback/capability diagnostic when free 1h historical coverage is unavailable.

For `sjc_gold_prices`, records include chart-ready daily line/spread fields: `time`, `value`, optional `buy_price`, optional `sell_price`, unit, currency, source, and freshness. `value` is the provided `price` or the midpoint of `buy_price` and `sell_price`.

## `GET /api/market/overview`

Returns Market page header and overview data for a selected market.

Query parameters:

- `market`: `VN` or `Commodity`
- `watchlist_id` optional
- `collection_id` optional

Response includes:

- available markets and selected market
- watchlists
- collections for index, sector, and theme filters
- top index mini chart series
- heatmap cells with instrument id, symbol, sector/industry, latest price, percent change, volume/value where available, and freshness
- sortable instrument list rows with symbol, display name, sector/industry, latest price, percent change, volume/value, and freshness

## `GET /api/market/instruments/{instrument_id}/chart`

Returns the full instrument chart opened from a stock list row or heatmap cell.

Query parameters:

- `timeframe`: `1h`, `4h`, `1d`, or `1M`
- `from`
- `to`

Response includes chart-ready OHLC/line records, the selected timeframe, freshness metadata, and a table fallback. For `vn_prices` and `xauusd_prices`, `4h`, `1d`, and `1M` may be derived from stored 1h bars. For `sjc_gold_prices`, daily and monthly views may be derived from daily quotes.
When the yfinance provider cannot supply XAUUSD 1h history for the requested range,
the response must identify that daily fallback records are used when available.
