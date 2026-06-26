from collections.abc import Callable
from datetime import UTC, date, datetime
from typing import Any
from uuid import uuid4

from api.platform.freshness import (
    active_freshness_dataset_ids,
    calculate_dataset_freshness,
)
from api.platform.ingestion.sources import TimeSeriesRecord
from api.platform.ingestion.store_writer import (
    IngestionJobRecord,
    InstrumentMetadata,
)


class PostgresTimeSeriesStore:
    def __init__(
        self,
        database_url: str | None = None,
        connection_factory: Callable[[], Any] | None = None,
        roadmap_markets_enabled: bool = False,
    ) -> None:
        if database_url is None and connection_factory is None:
            raise ValueError("database_url or connection_factory is required")
        self._database_url = database_url
        self._connection_factory = connection_factory
        self._roadmap_markets_enabled = roadmap_markets_enabled

    def upsert_many(self, records: list[TimeSeriesRecord]) -> int:
        connection = self._connect()
        try:
            with connection.cursor() as cursor:
                for record in records:
                    self._upsert_instrument(cursor, record)
                    if record.dataset_id in {"us_prices", "vn_prices"}:
                        cursor.execute(_UPSERT_STOCK_BAR, _stock_params(record))
                    elif record.dataset_id == "us_prices_daily":
                        cursor.execute(_UPSERT_STOCK_DAILY_BAR, _stock_daily_params(record))
                    elif record.dataset_id == "vn_prices_daily":
                        cursor.execute(
                            _UPSERT_VN_PRICES_DAILY,
                            _vn_prices_daily_params(record),
                        )
                    elif record.dataset_id == "xauusd_prices":
                        cursor.execute(_UPSERT_XAUUSD_BAR, _xauusd_params(record))
                    elif record.dataset_id == "xauusd_prices_daily":
                        cursor.execute(
                            _UPSERT_XAUUSD_DAILY_BAR,
                            _xauusd_daily_params(record),
                        )
                    elif record.dataset_id == "sjc_gold_prices":
                        cursor.execute(_UPSERT_SJC_QUOTE, _sjc_params(record))
                    else:
                        raise ValueError(f"Unsupported dataset: {record.dataset_id}")
            connection.commit()
            return len(records)
        finally:
            connection.close()

    def list_dataset(self, dataset_id: str) -> list[TimeSeriesRecord]:
        connection = self._connect()
        try:
            with connection.cursor() as cursor:
                if dataset_id in {"us_prices", "vn_prices"}:
                    cursor.execute(
                        _SELECT_STOCK_BARS,
                        {"market": _stock_market_for_dataset(dataset_id)},
                    )
                    rows = cursor.fetchall()
                    return [_stock_record(row) for row in rows]
                if dataset_id == "us_prices_daily":
                    cursor.execute(_SELECT_STOCK_DAILY_BARS, {"market": "US_STOCK"})
                    rows = cursor.fetchall()
                    return [_stock_daily_record(row) for row in rows]
                if dataset_id == "vn_prices_daily":
                    cursor.execute(_SELECT_VN_PRICES_DAILY, None)
                    rows = cursor.fetchall()
                    return [_vn_prices_daily_record(row) for row in rows]
                if dataset_id == "xauusd_prices":
                    cursor.execute(_SELECT_XAUUSD_BARS, None)
                    rows = cursor.fetchall()
                    return [_xauusd_record(row) for row in rows]
                if dataset_id == "xauusd_prices_daily":
                    cursor.execute(_SELECT_XAUUSD_DAILY_BARS, None)
                    rows = cursor.fetchall()
                    return [_xauusd_daily_record(row) for row in rows]
                if dataset_id == "sjc_gold_prices":
                    cursor.execute(_SELECT_SJC_QUOTES, None)
                    rows = cursor.fetchall()
                    return [_sjc_record(row) for row in rows]
                return []
        finally:
            connection.close()

    def list_dataset_for_instrument(
        self, dataset_id: str, instrument_id: str
    ) -> list[TimeSeriesRecord]:
        sql = _DATASET_ROWS_BY_INSTRUMENT_SQL.get(dataset_id)
        if sql is None:
            return []
        record_factory = _DATASET_ROWS_BY_INSTRUMENT_FACTORY[dataset_id]
        connection = self._connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql, {"instrument_id": instrument_id})
                rows = cursor.fetchall()
                return [record_factory(row) for row in rows]
        finally:
            connection.close()

    def read_instrument(
        self, instrument_id: str
    ) -> InstrumentMetadata | None:
        connection = self._connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    _SELECT_INSTRUMENT,
                    {"instrument_id": instrument_id},
                )
                rows = cursor.fetchall()
                if not rows:
                    return None
                return _instrument_metadata(rows[0])
        finally:
            connection.close()

    def list_instruments(self) -> list[InstrumentMetadata]:
        connection = self._connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute(_SELECT_INSTRUMENTS, None)
                rows = cursor.fetchall()
                return [_instrument_metadata(row) for row in rows]
        finally:
            connection.close()

    def list_collection_instrument_ids(
        self, collection_id: str
    ) -> set[str]:
        connection = self._connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    _SELECT_COLLECTION_INSTRUMENT_IDS,
                    {"collection_id": collection_id},
                )
                rows = cursor.fetchall()
                return {str(row["instrument_id"]) for row in rows}
        finally:
            connection.close()

    def list_jobs(self) -> list[IngestionJobRecord]:
        connection = self._connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute(_SELECT_JOBS, None)
                rows = cursor.fetchall()
                return [_job_record(row) for row in rows]
        finally:
            connection.close()

    def has_dataset_rows(
        self, dataset_id: str, instrument_id: str
    ) -> bool:
        sql = _DATASET_ROW_EXISTS_SQL.get(dataset_id)
        if sql is None:
            return False
        connection = self._connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql, {"instrument_id": instrument_id})
                return bool(cursor.fetchall())
        finally:
            connection.close()

    def is_in_collection(
        self, collection_id: str, instrument_id: str
    ) -> bool:
        connection = self._connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    _SELECT_COLLECTION_MEMBERSHIP,
                    {
                        "collection_id": collection_id,
                        "instrument_id": instrument_id,
                    },
                )
                return bool(cursor.fetchall())
        finally:
            connection.close()

    def has_active_job(self, source_id: str, period: str) -> bool:
        connection = self._connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    _SELECT_ACTIVE_JOB,
                    {"source_id": source_id, "dataset_id": source_id, "period": period},
                )
                return bool(cursor.fetchall())
        finally:
            connection.close()

    def create_running_job(
        self,
        source_id: str,
        period: str,
        trigger: str,
    ) -> IngestionJobRecord:
        job = _new_job(
            source_id=source_id,
            period=period,
            trigger=trigger,
            status="running",
            completed_at=None,
            record_count=0,
            diagnostics={},
        )
        self._insert_job(job)
        return job

    def save_completed_job(
        self,
        source_id: str,
        period: str,
        trigger: str,
        status: str,
        record_count: int,
        diagnostics: dict[str, object],
    ) -> IngestionJobRecord:
        job = _new_job(
            source_id=source_id,
            period=period,
            trigger=trigger,
            status=status,
            completed_at=datetime.now(UTC),
            record_count=record_count,
            diagnostics=diagnostics,
        )
        self._insert_job(job)
        return job

    def freshness(self) -> list[dict[str, object]]:
        return calculate_dataset_freshness(
            dataset_ids=active_freshness_dataset_ids(
                self._roadmap_markets_enabled
            ),
            list_dataset=self.list_dataset,
            list_jobs=self.list_jobs,
        )

    def _connect(self) -> Any:
        if self._connection_factory is not None:
            return self._connection_factory()
        try:
            import psycopg
            from psycopg.rows import dict_row
        except ImportError as exc:
            raise RuntimeError("psycopg is required for PostgreSQL storage") from exc
        return psycopg.connect(self._database_url, row_factory=dict_row)

    def _insert_job(self, job: IngestionJobRecord) -> None:
        connection = self._connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    _INSERT_JOB,
                    {
                        "job_id": job.job_id,
                        "source_id": job.source_id,
                        "dataset_id": job.dataset_id,
                        "trigger": job.trigger,
                        "period": job.period,
                        "status": job.status,
                        "started_at": job.started_at,
                        "completed_at": job.completed_at,
                        "record_count": job.record_count,
                        "diagnostics": _jsonb(job.diagnostics),
                    },
                )
            connection.commit()
        finally:
            connection.close()

    def _upsert_instrument(self, cursor: Any, record: TimeSeriesRecord) -> None:
        payload = record.payload
        cursor.execute(
            _UPSERT_INSTRUMENT,
            {
                "instrument_id": record.instrument_id,
                "symbol": str(payload.get("symbol", record.instrument_id)),
                "market": _market_for_record(record),
                "asset_class": _asset_class_for_record(record),
                "exchange": payload.get("exchange"),
                "display_name": str(
                    payload.get("display_name", payload.get("symbol", record.instrument_id))
                ),
                "currency": str(payload.get("currency", "VND")),
                "sector": payload.get("sector"),
                "industry": payload.get("industry"),
                "sub_industry": payload.get("sub_industry"),
                "status": str(payload.get("status", "active")),
            },
        )


_UPSERT_INSTRUMENT = """
INSERT INTO market_instruments (
    instrument_id, symbol, market, asset_class, exchange, display_name, currency,
    sector, industry, sub_industry, status
) VALUES (
    %(instrument_id)s, %(symbol)s, %(market)s, %(asset_class)s, %(exchange)s,
    %(display_name)s, %(currency)s, %(sector)s, %(industry)s, %(sub_industry)s,
    %(status)s
)
ON CONFLICT (instrument_id) DO UPDATE SET
    symbol = EXCLUDED.symbol,
    market = EXCLUDED.market,
    asset_class = EXCLUDED.asset_class,
    exchange = EXCLUDED.exchange,
    display_name = EXCLUDED.display_name,
    currency = EXCLUDED.currency,
    sector = EXCLUDED.sector,
    industry = EXCLUDED.industry,
    sub_industry = EXCLUDED.sub_industry,
    status = EXCLUDED.status
"""

_UPSERT_STOCK_BAR = """
INSERT INTO stock_1h_bars (
    market, instrument_id, symbol, exchange, interval_start, interval_end, open,
    high, low, close, volume, value, currency, adjusted_close,
    corporate_action_flag, collected_at, source_id, freshness_status
) VALUES (
    %(market)s, %(instrument_id)s, %(symbol)s, %(exchange)s, %(interval_start)s,
    %(interval_end)s, %(open)s, %(high)s, %(low)s, %(close)s, %(volume)s,
    %(value)s, %(currency)s, %(adjusted_close)s, %(corporate_action_flag)s,
    %(collected_at)s, %(source_id)s, %(freshness_status)s
)
ON CONFLICT (market, instrument_id, interval_start) DO UPDATE SET
    interval_end = EXCLUDED.interval_end,
    open = EXCLUDED.open,
    high = EXCLUDED.high,
    low = EXCLUDED.low,
    close = EXCLUDED.close,
    volume = EXCLUDED.volume,
    value = EXCLUDED.value,
    currency = EXCLUDED.currency,
    adjusted_close = EXCLUDED.adjusted_close,
    corporate_action_flag = EXCLUDED.corporate_action_flag,
    collected_at = EXCLUDED.collected_at,
    source_id = EXCLUDED.source_id,
    freshness_status = EXCLUDED.freshness_status
"""

_UPSERT_STOCK_DAILY_BAR = """
INSERT INTO stock_daily_bars (
    market, instrument_id, symbol, exchange, trading_date, open, high, low,
    close, volume, value, currency, adjusted_close, corporate_action_flag,
    collected_at, source_id, freshness_status
) VALUES (
    %(market)s, %(instrument_id)s, %(symbol)s, %(exchange)s, %(trading_date)s,
    %(open)s, %(high)s, %(low)s, %(close)s, %(volume)s, %(value)s, %(currency)s,
    %(adjusted_close)s, %(corporate_action_flag)s, %(collected_at)s,
    %(source_id)s, %(freshness_status)s
)
ON CONFLICT (market, instrument_id, trading_date) DO UPDATE SET
    open = EXCLUDED.open,
    high = EXCLUDED.high,
    low = EXCLUDED.low,
    close = EXCLUDED.close,
    volume = EXCLUDED.volume,
    value = EXCLUDED.value,
    currency = EXCLUDED.currency,
    adjusted_close = EXCLUDED.adjusted_close,
    corporate_action_flag = EXCLUDED.corporate_action_flag,
    collected_at = EXCLUDED.collected_at,
    source_id = EXCLUDED.source_id,
    freshness_status = EXCLUDED.freshness_status
"""

_UPSERT_VN_PRICES_DAILY = """
INSERT INTO vn_prices_daily (
    market, instrument_id, symbol, exchange, trade_date, open, high, low,
    close, volume, value, currency, adjusted_close, corporate_action_flag,
    collected_at, source_id, freshness_status
) VALUES (
    %(market)s, %(instrument_id)s, %(symbol)s, %(exchange)s, %(trade_date)s,
    %(open)s, %(high)s, %(low)s, %(close)s, %(volume)s, %(value)s,
    %(currency)s, %(adjusted_close)s, %(corporate_action_flag)s,
    %(collected_at)s, %(source_id)s, %(freshness_status)s
)
ON CONFLICT (market, instrument_id, trade_date) DO UPDATE SET
    open = EXCLUDED.open,
    high = EXCLUDED.high,
    low = EXCLUDED.low,
    close = EXCLUDED.close,
    volume = EXCLUDED.volume,
    value = EXCLUDED.value,
    currency = EXCLUDED.currency,
    adjusted_close = EXCLUDED.adjusted_close,
    corporate_action_flag = EXCLUDED.corporate_action_flag,
    collected_at = EXCLUDED.collected_at,
    source_id = EXCLUDED.source_id,
    freshness_status = EXCLUDED.freshness_status
"""

_UPSERT_XAUUSD_BAR = """
INSERT INTO xauusd_1h_bars (
    instrument_id, symbol, interval_start, interval_end, open, high, low, close,
    unit, currency, collected_at, source_id, freshness_status
) VALUES (
    %(instrument_id)s, %(symbol)s, %(interval_start)s, %(interval_end)s, %(open)s,
    %(high)s, %(low)s, %(close)s, %(unit)s, %(currency)s, %(collected_at)s,
    %(source_id)s, %(freshness_status)s
)
ON CONFLICT (instrument_id, interval_start) DO UPDATE SET
    interval_end = EXCLUDED.interval_end,
    open = EXCLUDED.open,
    high = EXCLUDED.high,
    low = EXCLUDED.low,
    close = EXCLUDED.close,
    unit = EXCLUDED.unit,
    currency = EXCLUDED.currency,
    collected_at = EXCLUDED.collected_at,
    source_id = EXCLUDED.source_id,
    freshness_status = EXCLUDED.freshness_status
"""

_UPSERT_XAUUSD_DAILY_BAR = """
INSERT INTO xauusd_daily_bars (
    instrument_id, symbol, trading_date, open, high, low, close, unit, currency,
    collected_at, source_id, freshness_status
) VALUES (
    %(instrument_id)s, %(symbol)s, %(trading_date)s, %(open)s, %(high)s, %(low)s,
    %(close)s, %(unit)s, %(currency)s, %(collected_at)s, %(source_id)s,
    %(freshness_status)s
)
ON CONFLICT (instrument_id, trading_date) DO UPDATE SET
    open = EXCLUDED.open,
    high = EXCLUDED.high,
    low = EXCLUDED.low,
    close = EXCLUDED.close,
    unit = EXCLUDED.unit,
    currency = EXCLUDED.currency,
    collected_at = EXCLUDED.collected_at,
    source_id = EXCLUDED.source_id,
    freshness_status = EXCLUDED.freshness_status
"""

_UPSERT_SJC_QUOTE = """
INSERT INTO sjc_gold_daily_quotes (
    instrument_id, symbol, quote_type, quote_date, buy_price, sell_price, price,
    unit, currency, location, collected_at, source_id, freshness_status
) VALUES (
    %(instrument_id)s, %(symbol)s, %(quote_type)s, %(quote_date)s, %(buy_price)s,
    %(sell_price)s, %(price)s, %(unit)s, %(currency)s, %(location)s,
    %(collected_at)s, %(source_id)s, %(freshness_status)s
)
ON CONFLICT (instrument_id, quote_type, quote_date) DO UPDATE SET
    buy_price = EXCLUDED.buy_price,
    sell_price = EXCLUDED.sell_price,
    price = EXCLUDED.price,
    unit = EXCLUDED.unit,
    currency = EXCLUDED.currency,
    location = EXCLUDED.location,
    collected_at = EXCLUDED.collected_at,
    source_id = EXCLUDED.source_id,
    freshness_status = EXCLUDED.freshness_status
"""

_INSERT_JOB = """
INSERT INTO ingestion_jobs (
    job_id, source_id, dataset_id, trigger, period, status, started_at,
    completed_at, record_count, diagnostics
) VALUES (
    %(job_id)s, %(source_id)s, %(dataset_id)s, %(trigger)s, %(period)s,
    %(status)s, %(started_at)s, %(completed_at)s, %(record_count)s,
    %(diagnostics)s
)
"""

_SELECT_COLLECTION_MEMBERSHIP = """
SELECT 1
FROM market_collection_memberships
WHERE collection_id = %(collection_id)s
  AND instrument_id = %(instrument_id)s
LIMIT 1
"""

_SELECT_INSTRUMENT = """
SELECT instrument_id, symbol, market, asset_class, exchange,
       display_name, currency, sector, industry, sub_industry, status
FROM market_instruments
WHERE instrument_id = %(instrument_id)s
LIMIT 1
"""

_SELECT_INSTRUMENTS = """
SELECT instrument_id, symbol, market, asset_class, exchange,
       display_name, currency, sector, industry, sub_industry, status
FROM market_instruments
WHERE market = 'VN_STOCK'
  AND asset_class = 'stock'
  AND status = 'active'
ORDER BY symbol ASC
"""

_SELECT_COLLECTION_INSTRUMENT_IDS = """
SELECT instrument_id
FROM market_collection_memberships
WHERE collection_id = %(collection_id)s
  AND (effective_to IS NULL OR effective_to >= CURRENT_DATE)
ORDER BY instrument_id ASC
"""

_SELECT_VN_PRICES_DAILY_BY_INSTRUMENT = """
SELECT *
FROM vn_prices_daily
WHERE instrument_id = %(instrument_id)s
ORDER BY trade_date ASC
"""

_SELECT_US_PRICES_DAILY_BY_INSTRUMENT = """
SELECT *
FROM stock_daily_bars
WHERE instrument_id = %(instrument_id)s
ORDER BY trading_date ASC
"""

_DATASET_ROWS_BY_INSTRUMENT_SQL: dict[str, str] = {
    "vn_prices_daily": _SELECT_VN_PRICES_DAILY_BY_INSTRUMENT,
    "us_prices_daily": _SELECT_US_PRICES_DAILY_BY_INSTRUMENT,
}


_DATASET_ROW_EXISTS_SQL = {
    "vn_prices_daily": (
        "SELECT 1 FROM vn_prices_daily "
        "WHERE instrument_id = %(instrument_id)s LIMIT 1"
    ),
}

_SELECT_ACTIVE_JOB = """
SELECT job_id
FROM ingestion_jobs
WHERE source_id = %(source_id)s
  AND dataset_id = %(dataset_id)s
  AND period = %(period)s
  AND status IN ('queued', 'running')
LIMIT 1
"""

_SELECT_JOBS = """
SELECT job_id, source_id, dataset_id, trigger, period, status, started_at,
       completed_at, record_count, diagnostics
FROM ingestion_jobs
ORDER BY started_at DESC
"""

_SELECT_STOCK_BARS = """
SELECT *
FROM stock_1h_bars
WHERE market = %(market)s
ORDER BY interval_start ASC, instrument_id ASC
"""

_SELECT_STOCK_DAILY_BARS = """
SELECT *
FROM stock_daily_bars
WHERE market = %(market)s
ORDER BY trading_date ASC, instrument_id ASC
"""

_SELECT_VN_PRICES_DAILY = """
SELECT *
FROM vn_prices_daily
WHERE market = 'VN_STOCK'
ORDER BY trade_date ASC, instrument_id ASC
"""

_SELECT_XAUUSD_BARS = """
SELECT *
FROM xauusd_1h_bars
ORDER BY interval_start ASC
"""

_SELECT_XAUUSD_DAILY_BARS = """
SELECT *
FROM xauusd_daily_bars
ORDER BY trading_date ASC
"""

_SELECT_SJC_QUOTES = """
SELECT *
FROM sjc_gold_daily_quotes
ORDER BY quote_date ASC, instrument_id ASC
"""


def _stock_params(record: TimeSeriesRecord) -> dict[str, object]:
    payload = record.payload
    return {
        "market": str(payload.get("market", "VN_STOCK")),
        "instrument_id": record.instrument_id,
        "symbol": _required(payload, "symbol"),
        "exchange": _required(payload, "exchange"),
        "interval_start": _parse_datetime(_required(payload, "interval_start")),
        "interval_end": _parse_datetime(_required(payload, "interval_end")),
        "open": _required(payload, "open"),
        "high": _required(payload, "high"),
        "low": _required(payload, "low"),
        "close": _required(payload, "close"),
        "volume": _required(payload, "volume"),
        "value": payload.get("value"),
        "currency": _required(payload, "currency"),
        "adjusted_close": payload.get("adjusted_close"),
        "corporate_action_flag": payload.get("corporate_action_flag"),
        "collected_at": record.collected_at,
        "source_id": record.source_id,
        "freshness_status": str(payload.get("freshness_status", "fresh")),
    }


def _stock_daily_params(record: TimeSeriesRecord) -> dict[str, object]:
    payload = record.payload
    return {
        "market": str(payload.get("market", "US_STOCK")),
        "instrument_id": record.instrument_id,
        "symbol": _required(payload, "symbol"),
        "exchange": _required(payload, "exchange"),
        "trading_date": _parse_date(_required(payload, "trading_date")),
        "open": _required(payload, "open"),
        "high": _required(payload, "high"),
        "low": _required(payload, "low"),
        "close": _required(payload, "close"),
        "volume": _required(payload, "volume"),
        "value": payload.get("value"),
        "currency": _required(payload, "currency"),
        "adjusted_close": payload.get("adjusted_close"),
        "corporate_action_flag": payload.get("corporate_action_flag"),
        "collected_at": record.collected_at,
        "source_id": record.source_id,
        "freshness_status": str(payload.get("freshness_status", "fresh")),
    }


def _vn_prices_daily_params(record: TimeSeriesRecord) -> dict[str, object]:
    payload = record.payload
    return {
        "market": str(payload.get("market", "VN_STOCK")),
        "instrument_id": record.instrument_id,
        "symbol": _required(payload, "symbol"),
        "exchange": _required(payload, "exchange"),
        "trade_date": _parse_date(_required(payload, "trade_date")),
        "open": _required(payload, "open"),
        "high": _required(payload, "high"),
        "low": _required(payload, "low"),
        "close": _required(payload, "close"),
        "volume": _required(payload, "volume"),
        "value": payload.get("value"),
        "currency": _required(payload, "currency"),
        "adjusted_close": payload.get("adjusted_close"),
        "corporate_action_flag": payload.get("corporate_action_flag"),
        "collected_at": record.collected_at,
        "source_id": record.source_id,
        "freshness_status": str(
            payload.get("freshness_status", "fresh")
        ),
    }


def _xauusd_params(record: TimeSeriesRecord) -> dict[str, object]:
    payload = record.payload
    return {
        "instrument_id": record.instrument_id,
        "symbol": _required(payload, "symbol"),
        "interval_start": _parse_datetime(_required(payload, "interval_start")),
        "interval_end": _parse_datetime(_required(payload, "interval_end")),
        "open": _required(payload, "open"),
        "high": _required(payload, "high"),
        "low": _required(payload, "low"),
        "close": _required(payload, "close"),
        "unit": _required(payload, "unit"),
        "currency": _required(payload, "currency"),
        "collected_at": record.collected_at,
        "source_id": record.source_id,
        "freshness_status": str(payload.get("freshness_status", "fresh")),
    }


def _xauusd_daily_params(record: TimeSeriesRecord) -> dict[str, object]:
    payload = record.payload
    return {
        "instrument_id": record.instrument_id,
        "symbol": _required(payload, "symbol"),
        "trading_date": _parse_date(_required(payload, "trading_date")),
        "open": _required(payload, "open"),
        "high": _required(payload, "high"),
        "low": _required(payload, "low"),
        "close": _required(payload, "close"),
        "unit": _required(payload, "unit"),
        "currency": _required(payload, "currency"),
        "collected_at": record.collected_at,
        "source_id": record.source_id,
        "freshness_status": str(payload.get("freshness_status", "fresh")),
    }


def _sjc_params(record: TimeSeriesRecord) -> dict[str, object]:
    payload = record.payload
    return {
        "instrument_id": record.instrument_id,
        "symbol": _required(payload, "symbol"),
        "quote_type": _required(payload, "quote_type"),
        "quote_date": _parse_date(_required(payload, "quote_date")),
        "buy_price": payload.get("buy_price"),
        "sell_price": payload.get("sell_price"),
        "price": payload.get("price"),
        "unit": _required(payload, "unit"),
        "currency": _required(payload, "currency"),
        "location": payload.get("location"),
        "collected_at": record.collected_at,
        "source_id": record.source_id,
        "freshness_status": str(payload.get("freshness_status", "fresh")),
    }


def _instrument_metadata(row: dict[str, Any]) -> InstrumentMetadata:
    return InstrumentMetadata(
        instrument_id=row["instrument_id"],
        symbol=row["symbol"],
        market=row["market"],
        asset_class=row["asset_class"],
        exchange=row.get("exchange"),
        display_name=row["display_name"],
        currency=row["currency"],
        sector=row.get("sector"),
        industry=row.get("industry"),
        sub_industry=row.get("sub_industry"),
        status=row.get("status", "active"),
    )


def _stock_record(row: dict[str, Any]) -> TimeSeriesRecord:
    interval_start = _as_datetime(row["interval_start"])
    dataset_id = "us_prices" if row["market"] == "US_STOCK" else "vn_prices"
    return TimeSeriesRecord(
        dataset_id=dataset_id,
        record_key=f"{row['instrument_id']}:{interval_start.isoformat()}",
        instrument_id=row["instrument_id"],
        market_time=interval_start,
        collected_at=_as_datetime(row["collected_at"]),
        source_id=row["source_id"],
        payload={
            "market": row["market"],
            "symbol": row["symbol"],
            "exchange": row["exchange"],
            "interval_start": interval_start.isoformat(),
            "interval_end": _as_datetime(row["interval_end"]).isoformat(),
            "open": row["open"],
            "high": row["high"],
            "low": row["low"],
            "close": row["close"],
            "volume": row["volume"],
            "value": row["value"],
            "currency": row["currency"],
            "adjusted_close": row["adjusted_close"],
            "corporate_action_flag": row["corporate_action_flag"],
            "freshness_status": row["freshness_status"],
        },
    )


def _stock_daily_record(row: dict[str, Any]) -> TimeSeriesRecord:
    trading_date = _as_date(row["trading_date"])
    dataset_id = "us_prices_daily" if row["market"] == "US_STOCK" else "stock_daily"
    return TimeSeriesRecord(
        dataset_id=dataset_id,
        record_key=f"{row['instrument_id']}:{trading_date.isoformat()}",
        instrument_id=row["instrument_id"],
        market_time=datetime.combine(trading_date, datetime.min.time(), tzinfo=UTC),
        collected_at=_as_datetime(row["collected_at"]),
        source_id=row["source_id"],
        payload={
            "market": row["market"],
            "symbol": row["symbol"],
            "exchange": row["exchange"],
            "trading_date": trading_date.isoformat(),
            "open": row["open"],
            "high": row["high"],
            "low": row["low"],
            "close": row["close"],
            "volume": row["volume"],
            "value": row["value"],
            "currency": row["currency"],
            "adjusted_close": row["adjusted_close"],
            "corporate_action_flag": row["corporate_action_flag"],
            "freshness_status": row["freshness_status"],
        },
    )


def _vn_prices_daily_record(row: dict[str, Any]) -> TimeSeriesRecord:
    trade_date = _as_date(row["trade_date"])
    return TimeSeriesRecord(
        dataset_id="vn_prices_daily",
        record_key=f"{row['instrument_id']}:{trade_date.isoformat()}",
        instrument_id=row["instrument_id"],
        market_time=datetime.combine(
            trade_date, datetime.min.time(), tzinfo=UTC
        ),
        collected_at=_as_datetime(row["collected_at"]),
        source_id=row["source_id"],
        payload={
            "market": row["market"],
            "symbol": row["symbol"],
            "exchange": row["exchange"],
            "trade_date": trade_date.isoformat(),
            "open": row["open"],
            "high": row["high"],
            "low": row["low"],
            "close": row["close"],
            "volume": row["volume"],
            "value": row["value"],
            "currency": row["currency"],
            "adjusted_close": row["adjusted_close"],
            "corporate_action_flag": row["corporate_action_flag"],
            "freshness_status": row["freshness_status"],
        },
    )


def _xauusd_record(row: dict[str, Any]) -> TimeSeriesRecord:
    interval_start = _as_datetime(row["interval_start"])
    return TimeSeriesRecord(
        dataset_id="xauusd_prices",
        record_key=f"{row['instrument_id']}:{interval_start.isoformat()}",
        instrument_id=row["instrument_id"],
        market_time=interval_start,
        collected_at=_as_datetime(row["collected_at"]),
        source_id=row["source_id"],
        payload={
            "symbol": row["symbol"],
            "interval_start": interval_start.isoformat(),
            "interval_end": _as_datetime(row["interval_end"]).isoformat(),
            "open": row["open"],
            "high": row["high"],
            "low": row["low"],
            "close": row["close"],
            "unit": row["unit"],
            "currency": row["currency"],
            "freshness_status": row["freshness_status"],
        },
    )


def _xauusd_daily_record(row: dict[str, Any]) -> TimeSeriesRecord:
    trading_date = _as_date(row["trading_date"])
    return TimeSeriesRecord(
        dataset_id="xauusd_prices_daily",
        record_key=f"{row['instrument_id']}:{trading_date.isoformat()}",
        instrument_id=row["instrument_id"],
        market_time=datetime.combine(trading_date, datetime.min.time(), tzinfo=UTC),
        collected_at=_as_datetime(row["collected_at"]),
        source_id=row["source_id"],
        payload={
            "symbol": row["symbol"],
            "trading_date": trading_date.isoformat(),
            "open": row["open"],
            "high": row["high"],
            "low": row["low"],
            "close": row["close"],
            "unit": row["unit"],
            "currency": row["currency"],
            "freshness_status": row["freshness_status"],
            "fallback": "daily",
        },
    )


def _sjc_record(row: dict[str, Any]) -> TimeSeriesRecord:
    quote_date = _as_date(row["quote_date"])
    return TimeSeriesRecord(
        dataset_id="sjc_gold_prices",
        record_key=f"{row['instrument_id']}:{row['quote_type']}:{quote_date.isoformat()}",
        instrument_id=row["instrument_id"],
        market_time=datetime.combine(quote_date, datetime.min.time(), tzinfo=UTC),
        collected_at=_as_datetime(row["collected_at"]),
        source_id=row["source_id"],
        payload={
            "symbol": row["symbol"],
            "quote_type": row["quote_type"],
            "quote_date": quote_date.isoformat(),
            "buy_price": row["buy_price"],
            "sell_price": row["sell_price"],
            "price": row["price"],
            "unit": row["unit"],
            "currency": row["currency"],
            "location": row["location"],
            "freshness_status": row["freshness_status"],
        },
    )


def _job_record(row: dict[str, Any]) -> IngestionJobRecord:
    return IngestionJobRecord(
        job_id=row["job_id"],
        source_id=row["source_id"],
        dataset_id=row["dataset_id"],
        period=row["period"],
        trigger=row["trigger"],
        status=row["status"],
        started_at=_as_datetime(row["started_at"]),
        completed_at=_as_datetime(row["completed_at"]) if row["completed_at"] else None,
        record_count=row["record_count"],
        diagnostics=row["diagnostics"],
    )


def _new_job(
    source_id: str,
    period: str,
    trigger: str,
    status: str,
    completed_at: datetime | None,
    record_count: int,
    diagnostics: dict[str, object],
) -> IngestionJobRecord:
    return IngestionJobRecord(
        job_id=f"ingest_{uuid4().hex}",
        source_id=source_id,
        dataset_id=source_id,
        period=period,
        trigger=trigger,
        status=status,
        started_at=datetime.now(UTC),
        completed_at=completed_at,
        record_count=record_count,
        diagnostics=diagnostics,
    )


_DATASET_ROWS_BY_INSTRUMENT_FACTORY: dict[
    str, Callable[[dict[str, Any]], TimeSeriesRecord]
] = {
    "vn_prices_daily": _vn_prices_daily_record,
    "us_prices_daily": _stock_daily_record,
}


_STOCK_DATASETS = {
    "us_prices",
    "us_prices_daily",
    "vn_prices",
    "vn_prices_daily",
}


def _market_for_record(record: TimeSeriesRecord) -> str:
    if record.dataset_id in _STOCK_DATASETS:
        return str(record.payload.get("market", "VN_STOCK"))
    return "GOLD"


def _asset_class_for_record(record: TimeSeriesRecord) -> str:
    if record.dataset_id in _STOCK_DATASETS:
        return "stock"
    return "commodity"


def _stock_market_for_dataset(dataset_id: str) -> str:
    if dataset_id == "us_prices":
        return "US_STOCK"
    return "VN_STOCK"


def _required(payload: dict[str, object], key: str) -> Any:
    value = payload.get(key)
    if value is None:
        raise ValueError(f"Missing required payload field: {key}")
    return value


def _parse_datetime(value: object) -> datetime:
    if isinstance(value, datetime):
        return _as_datetime(value)
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return _as_datetime(parsed)


def _parse_date(value: object) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    return date.fromisoformat(str(value))


def _as_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _as_date(value: date | datetime) -> date:
    if isinstance(value, datetime):
        return value.date()
    return value


def _jsonb(value: dict[str, object]) -> object:
    try:
        from psycopg.types.json import Jsonb
    except ImportError:
        return value
    return Jsonb(value)
