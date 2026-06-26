from collections.abc import Callable, Mapping
import csv
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from html.parser import HTMLParser
from io import StringIO
import os
from pathlib import Path
import re
import time
from typing import Any

import httpx

from api.platform.ingestion.errors import ProviderFetchError
from api.platform.ingestion.sources import TimeSeriesRecord

FetchJson = Callable[[str], object]


def vn100_seed_symbols() -> tuple[str, ...]:
    seed_path = (
        Path(__file__).resolve().parents[4] / "data" / "seed" / "vn100.csv"
    )
    with seed_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        symbols = tuple(
            str(row["symbol"]).strip().upper()
            for row in reader
            if str(row.get("symbol", "")).strip()
        )
    if len(symbols) != 100 or len(set(symbols)) != 100:
        raise RuntimeError("VN100 seed symbols must contain 100 unique tickers")
    return symbols


@dataclass(frozen=True)
class FreeMarketDataSource:
    source_id: str
    provider: str
    fetch_json: FetchJson

    def fetch(
        self,
        period: str,
        *,
        instrument_id: str | None = None,
    ) -> list[TimeSeriesRecord]:
        raise NotImplementedError


class VnstockVNStockSource(FreeMarketDataSource):
    def __init__(
        self,
        fetch_json: FetchJson | None = None,
        api_key: str | None = None,
        symbols: tuple[str, ...] | None = None,
        timeout_seconds: float = 15.0,
    ) -> None:
        self._symbols = symbols or vn100_seed_symbols()
        self._api_key = api_key
        super().__init__(
            source_id="vn_prices",
            provider="vnstock",
            fetch_json=fetch_json
            or _vnstock_fetcher(
                self._symbols,
                api_key,
                timeout_seconds,
            ),
        )

    def fetch(
        self,
        period: str,
        *,
        instrument_id: str | None = None,
    ) -> list[TimeSeriesRecord]:
        payload = self._load_payload(period, instrument_id)
        rows = _records_from_payload(self.source_id, payload)
        capabilities = _capabilities_from_payload(payload)
        records: list[TimeSeriesRecord] = []
        for row in rows:
            _require_fields(
                self.source_id,
                row,
                (
                    "instrument_id",
                    "symbol",
                    "exchange",
                    "interval_start",
                    "interval_end",
                    "open",
                    "high",
                    "low",
                    "close",
                    "volume",
                    "currency",
                ),
            )
            interval_start = _parse_datetime(str(row["interval_start"]))
            normalized = dict(row)
            normalized["market"] = str(normalized.get("market", "VN_STOCK"))
            normalized["capabilities"] = capabilities
            records.append(
                TimeSeriesRecord(
                    dataset_id=self.source_id,
                    record_key=f"{row['instrument_id']}:{interval_start.isoformat()}",
                    instrument_id=str(row["instrument_id"]),
                    market_time=interval_start,
                    collected_at=_collected_at(row),
                    source_id=self.provider,
                    payload=normalized,
                )
            )
        return records

    def _load_payload(
        self,
        period: str,
        instrument_id: str | None,
    ) -> object:
        if instrument_id is not None:
            symbols = _resolve_vn_symbols(self._symbols, instrument_id)
            return _vnstock_hourly_payload(period, symbols, self._api_key)
        return self.fetch_json(period)


class VnstockVNStockDailySource(FreeMarketDataSource):
    def __init__(
        self,
        fetch_json: FetchJson | None = None,
        api_key: str | None = None,
        symbols: tuple[str, ...] | None = None,
        timeout_seconds: float = 15.0,
    ) -> None:
        self._symbols = symbols or vn100_seed_symbols()
        self._api_key = api_key
        super().__init__(
            source_id="vn_prices_daily",
            provider="vnstock",
            fetch_json=fetch_json
            or _vnstock_daily_fetcher(
                self._symbols,
                api_key,
                timeout_seconds,
            ),
        )

    def fetch(
        self,
        period: str,
        *,
        instrument_id: str | None = None,
    ) -> list[TimeSeriesRecord]:
        payload = self._load_payload(period, instrument_id)
        rows = _records_from_payload(self.source_id, payload)
        capabilities = _capabilities_from_payload(payload)
        records: list[TimeSeriesRecord] = []
        for row in rows:
            _require_fields(
                self.source_id,
                row,
                (
                    "instrument_id",
                    "symbol",
                    "exchange",
                    "trade_date",
                    "open",
                    "high",
                    "low",
                    "close",
                    "volume",
                    "currency",
                ),
            )
            trade_date = str(row["trade_date"])
            market_time = _parse_datetime(
                f"{trade_date}T00:00:00+00:00"
            )
            normalized = dict(row)
            normalized["market"] = str(
                normalized.get("market", "VN_STOCK")
            )
            normalized["capabilities"] = capabilities
            records.append(
                TimeSeriesRecord(
                    dataset_id=self.source_id,
                    record_key=f"{row['instrument_id']}:{trade_date}",
                    instrument_id=str(row["instrument_id"]),
                    market_time=market_time,
                    collected_at=_collected_at(row),
                    source_id=self.provider,
                    payload=normalized,
                )
            )
        return records

    def _load_payload(
        self,
        period: str,
        instrument_id: str | None,
    ) -> object:
        if instrument_id is not None:
            symbols = _resolve_vn_symbols(self._symbols, instrument_id)
            return _vnstock_daily_payload(period, symbols, self._api_key)
        return self.fetch_json(period)


class YFinanceUSStockSource(FreeMarketDataSource):
    def __init__(
        self,
        fetch_json: FetchJson | None = None,
        symbols: tuple[str, ...] = ("AAPL", "MSFT", "NVDA", "AMZN"),
        timeout_seconds: float = 15.0,
    ) -> None:
        super().__init__(
            source_id="us_prices",
            provider="yfinance",
            fetch_json=fetch_json or _yfinance_us_stock_fetcher(symbols, timeout_seconds),
        )

    def fetch(
        self,
        period: str,
        *,
        instrument_id: str | None = None,
    ) -> list[TimeSeriesRecord]:
        payload = self.fetch_json(period)
        rows = _records_from_payload(self.source_id, payload)
        capabilities = _capabilities_from_payload(payload)
        records: list[TimeSeriesRecord] = []
        for row in rows:
            _require_fields(
                self.source_id,
                row,
                (
                    "instrument_id",
                    "symbol",
                    "exchange",
                    "interval_start",
                    "interval_end",
                    "open",
                    "high",
                    "low",
                    "close",
                    "volume",
                    "currency",
                ),
            )
            interval_start = _parse_datetime(str(row["interval_start"]))
            normalized = dict(row)
            normalized["market"] = str(normalized.get("market", "US_STOCK"))
            normalized["capabilities"] = capabilities
            records.append(
                TimeSeriesRecord(
                    dataset_id=self.source_id,
                    record_key=f"{row['instrument_id']}:{interval_start.isoformat()}",
                    instrument_id=str(row["instrument_id"]),
                    market_time=interval_start,
                    collected_at=_collected_at(row),
                    source_id=self.provider,
                    payload=normalized,
                )
            )
        return records


class StooqUSStockDailySource(FreeMarketDataSource):
    def __init__(
        self,
        fetch_json: FetchJson | None = None,
        symbols: tuple[str, ...] = ("AAPL", "MSFT", "NVDA", "AMZN"),
        timeout_seconds: float = 15.0,
    ) -> None:
        super().__init__(
            source_id="us_prices_daily",
            provider="stooq",
            fetch_json=fetch_json
            or _stooq_us_stock_daily_fetcher(symbols, timeout_seconds),
        )

    def fetch(
        self,
        period: str,
        *,
        instrument_id: str | None = None,
    ) -> list[TimeSeriesRecord]:
        payload = self.fetch_json(period)
        rows = _records_from_payload(self.source_id, payload)
        capabilities = _capabilities_from_payload(payload)
        records: list[TimeSeriesRecord] = []
        for row in rows:
            _require_fields(
                self.source_id,
                row,
                (
                    "instrument_id",
                    "symbol",
                    "exchange",
                    "trading_date",
                    "open",
                    "high",
                    "low",
                    "close",
                    "volume",
                    "currency",
                ),
            )
            trading_date = str(row["trading_date"])
            market_time = _parse_datetime(f"{trading_date}T00:00:00+00:00")
            normalized = dict(row)
            normalized["market"] = str(normalized.get("market", "US_STOCK"))
            normalized["capabilities"] = capabilities
            records.append(
                TimeSeriesRecord(
                    dataset_id=self.source_id,
                    record_key=f"{row['instrument_id']}:{trading_date}",
                    instrument_id=str(row["instrument_id"]),
                    market_time=market_time,
                    collected_at=_collected_at(row),
                    source_id=self.provider,
                    payload=normalized,
                )
            )
        return records


class YFinanceXauusdSource(FreeMarketDataSource):
    def __init__(
        self,
        fetch_json: FetchJson | None = None,
        timeout_seconds: float = 15.0,
    ) -> None:
        super().__init__(
            source_id="xauusd_prices",
            provider="yfinance",
            fetch_json=fetch_json or _yfinance_xauusd_fetcher(timeout_seconds),
        )

    def fetch(
        self,
        period: str,
        *,
        instrument_id: str | None = None,
    ) -> list[TimeSeriesRecord]:
        payload = self.fetch_json(period)
        rows = _records_from_payload(self.source_id, payload)
        capabilities = _capabilities_from_payload(payload)
        records: list[TimeSeriesRecord] = []
        for row in rows:
            _require_fields(
                self.source_id,
                row,
                ("interval_start", "interval_end", "open", "high", "low", "close"),
            )
            interval_start = _parse_datetime(str(row["interval_start"]))
            normalized = {
                "symbol": str(row.get("symbol", "XAUUSD")),
                "interval_start": str(row["interval_start"]),
                "interval_end": str(row["interval_end"]),
                "open": row["open"],
                "high": row["high"],
                "low": row["low"],
                "close": row["close"],
                "unit": str(row.get("unit", "oz")),
                "currency": str(row.get("currency", "USD")),
                "capabilities": capabilities,
            }
            records.append(
                TimeSeriesRecord(
                    dataset_id=self.source_id,
                    record_key=f"gold:XAUUSD:{interval_start.isoformat()}",
                    instrument_id="gold:XAUUSD",
                    market_time=interval_start,
                    collected_at=_collected_at(row),
                    source_id=self.provider,
                    payload=normalized,
                )
            )
        return records


class AlphaVantageXauusdDailySource(FreeMarketDataSource):
    def __init__(
        self,
        fetch_json: FetchJson | None = None,
        api_key: str | None = None,
        timeout_seconds: float = 15.0,
    ) -> None:
        super().__init__(
            source_id="xauusd_prices_daily",
            provider="alpha_vantage",
            fetch_json=fetch_json
            or _alpha_vantage_xauusd_daily_fetcher(api_key, timeout_seconds),
        )

    def fetch(
        self,
        period: str,
        *,
        instrument_id: str | None = None,
    ) -> list[TimeSeriesRecord]:
        payload = self.fetch_json(period)
        period_start = _period_start(period).date()
        period_end = _period_end(period).date()
        rows = [
            row
            for row in _records_from_payload(self.source_id, payload)
            if period_start
            <= datetime.fromisoformat(str(row.get("trading_date"))).date()
            <= period_end
        ]
        if not rows:
            raise ProviderFetchError(
                "alpha_vantage fetch failed for xauusd_prices_daily: no daily records"
            )
        capabilities = _capabilities_from_payload(payload)
        records: list[TimeSeriesRecord] = []
        for row in rows:
            _require_fields(
                self.source_id,
                row,
                ("trading_date", "open", "high", "low", "close"),
            )
            market_time = _parse_datetime(f"{row['trading_date']}T00:00:00+00:00")
            normalized = {
                "symbol": str(row.get("symbol", "XAUUSD")),
                "trading_date": str(row["trading_date"]),
                "open": row["open"],
                "high": row["high"],
                "low": row["low"],
                "close": row["close"],
                "unit": str(row.get("unit", "oz")),
                "currency": str(row.get("currency", "USD")),
                "fallback": "daily",
                "capabilities": capabilities,
            }
            records.append(
                TimeSeriesRecord(
                    dataset_id=self.source_id,
                    record_key=f"gold:XAUUSD:{row['trading_date']}",
                    instrument_id="gold:XAUUSD",
                    market_time=market_time,
                    collected_at=_collected_at(row),
                    source_id=self.provider,
                    payload=normalized,
                )
            )
        return records


class SJCOfficialGoldSource(FreeMarketDataSource):
    def __init__(
        self,
        fetch_json: FetchJson | None = None,
        url: str | None = None,
        timeout_seconds: float = 15.0,
    ) -> None:
        super().__init__(
            source_id="sjc_gold_prices",
            provider="sjc_official",
            fetch_json=fetch_json
            or _http_text_fetcher(
                provider="sjc_official",
                source_id="sjc_gold_prices",
                url=url or "https://sjc.com.vn/",
                timeout_seconds=timeout_seconds,
            ),
        )

    def fetch(
        self,
        period: str,
        *,
        instrument_id: str | None = None,
    ) -> list[TimeSeriesRecord]:
        payload = self.fetch_json(period)
        rows = _sjc_rows_from_payload(self.source_id, payload, period)
        capabilities = _capabilities_from_payload(payload)
        records: list[TimeSeriesRecord] = []
        for row in rows:
            _require_fields(
                self.source_id,
                row,
                ("quote_date", "buy_price", "sell_price"),
            )
            market_time = _parse_datetime(f"{row['quote_date']}T00:00:00+00:00")
            normalized = {
                "symbol": str(row.get("symbol", "SJC")),
                "quote_type": str(row.get("quote_type", "buy_sell")),
                "quote_date": str(row["quote_date"]),
                "buy_price": row["buy_price"],
                "sell_price": row["sell_price"],
                "unit": str(row.get("unit", "tael")),
                "currency": str(row.get("currency", "VND")),
                "location": str(row.get("location", "VN")),
                "attribution": "SJC official",
                "capabilities": capabilities,
            }
            records.append(
                TimeSeriesRecord(
                    dataset_id=self.source_id,
                    record_key=f"gold:SJC:{normalized['quote_type']}:{row['quote_date']}",
                    instrument_id="gold:SJC",
                    market_time=market_time,
                    collected_at=_collected_at(row),
                    source_id=self.provider,
                    payload=normalized,
                )
            )
        return records


def create_real_sources(
    vnstock_api_key: str | None = None,
    alpha_vantage_api_key: str | None = None,
    timeout_seconds: float = 15.0,
) -> dict[str, FreeMarketDataSource]:
    sources: list[FreeMarketDataSource] = [
        YFinanceUSStockSource(timeout_seconds=timeout_seconds),
        StooqUSStockDailySource(timeout_seconds=timeout_seconds),
        VnstockVNStockSource(
            api_key=vnstock_api_key,
            timeout_seconds=timeout_seconds,
        ),
        VnstockVNStockDailySource(
            api_key=vnstock_api_key,
            timeout_seconds=timeout_seconds,
        ),
        YFinanceXauusdSource(timeout_seconds=timeout_seconds),
        AlphaVantageXauusdDailySource(
            api_key=alpha_vantage_api_key,
            timeout_seconds=timeout_seconds,
        ),
        SJCOfficialGoldSource(timeout_seconds=timeout_seconds),
    ]
    return {source.source_id: source for source in sources}


def _records_from_payload(source_id: str, payload: object) -> list[Mapping[str, Any]]:
    if isinstance(payload, Mapping):
        records = payload.get("records", [])
    else:
        records = payload
    if not isinstance(records, list):
        raise ProviderFetchError(f"{source_id} provider response is missing records")
    normalized: list[Mapping[str, Any]] = []
    for record in records:
        if not isinstance(record, Mapping):
            raise ProviderFetchError(f"{source_id} provider record is not an object")
        normalized.append(record)
    return normalized


def _sjc_rows_from_payload(
    source_id: str,
    payload: object,
    period: str,
) -> list[Mapping[str, Any]]:
    if isinstance(payload, str):
        rows = _parse_sjc_html_rows(payload, period)
        if rows:
            return rows
        raise ProviderFetchError(f"{source_id} provider response has no SJC quote rows")
    return _records_from_payload(source_id, payload)


def _parse_sjc_html_rows(html: str, period: str) -> list[Mapping[str, Any]]:
    parser = _TableCellParser()
    parser.feed(html)
    rows: list[Mapping[str, Any]] = []
    for cells in parser.rows:
        if len(cells) < 3:
            continue
        normalized_cells = [cell.lower() for cell in cells]
        if not any("sjc" in cell for cell in normalized_cells):
            continue
        buy_price = _parse_price(cells[1])
        sell_price = _parse_price(cells[2])
        if buy_price is None or sell_price is None:
            continue
        rows.append(
            {
                "symbol": "SJC",
                "quote_type": "buy_sell",
                "quote_date": period,
                "buy_price": buy_price,
                "sell_price": sell_price,
                "unit": "tael",
                "currency": "VND",
                "location": "VN",
            }
        )
    return rows


class _TableCellParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.rows: list[list[str]] = []
        self._current_row: list[str] | None = None
        self._current_cell: list[str] | None = None

    def handle_starttag(self, tag: str, _attrs: list[tuple[str, str | None]]) -> None:
        if tag == "tr":
            self._current_row = []
        elif tag in {"td", "th"} and self._current_row is not None:
            self._current_cell = []

    def handle_data(self, data: str) -> None:
        if self._current_cell is not None:
            self._current_cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"td", "th"} and self._current_row is not None:
            cell_text = " ".join(self._current_cell or []).strip()
            self._current_row.append(cell_text)
            self._current_cell = None
        elif tag == "tr" and self._current_row is not None:
            self.rows.append(self._current_row)
            self._current_row = None


def _parse_price(value: str) -> int | None:
    digits = re.sub(r"[^0-9]", "", value)
    if not digits:
        return None
    return int(digits)


def _http_json_fetcher(
    provider: str,
    source_id: str,
    url: str | None,
    token: str | None,
    timeout_seconds: float,
) -> FetchJson:
    if not url:
        return _unconfigured_fetch(provider, source_id)

    def fetch_json(period: str) -> object:
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        def request_payload() -> object:
            with httpx.Client(timeout=timeout_seconds) as client:
                response = client.get(url, params={"period": period}, headers=headers)
                response.raise_for_status()
                return response.json()

        return _fetch_with_provider_retries(provider, source_id, request_payload)

    return fetch_json


def _http_text_fetcher(
    provider: str,
    source_id: str,
    url: str,
    timeout_seconds: float,
) -> FetchJson:
    def fetch_text(_period: str) -> object:
        def request_payload() -> object:
            with httpx.Client(timeout=timeout_seconds) as client:
                response = client.get(url)
                response.raise_for_status()
                return response.text

        return _fetch_with_provider_retries(provider, source_id, request_payload)

    return fetch_text


def _yfinance_xauusd_fetcher(timeout_seconds: float) -> FetchJson:
    def fetch_json(period: str) -> object:
        start = _period_start(period)
        end = start + timedelta(days=1)
        url = "https://query1.finance.yahoo.com/v8/finance/chart/XAUUSD=X"
        params = {
            "period1": str(int(start.timestamp())),
            "period2": str(int(end.timestamp())),
            "interval": "1h",
        }
        def request_payload() -> object:
            with httpx.Client(timeout=timeout_seconds) as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                return response.json()

        payload = _fetch_with_provider_retries("yfinance", "xauusd_prices", request_payload)
        return _normalize_yfinance_payload(payload)

    return fetch_json


def _yfinance_us_stock_fetcher(
    symbols: tuple[str, ...],
    timeout_seconds: float,
) -> FetchJson:
    def fetch_json(period: str) -> object:
        start = _period_start(period)
        end = start + timedelta(days=1)
        records: list[dict[str, object]] = []
        for symbol in symbols:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            params = {
                "period1": str(int(start.timestamp())),
                "period2": str(int(end.timestamp())),
                "interval": "1h",
            }
            def request_payload(
                request_url: str = url,
                request_params: dict[str, str] = params,
            ) -> object:
                with httpx.Client(timeout=timeout_seconds) as client:
                    response = client.get(request_url, params=request_params)
                    response.raise_for_status()
                    return response.json()

            payload = _fetch_with_provider_retries("yfinance", "us_prices", request_payload)
            records.extend(_normalize_yfinance_us_payload(symbol, payload))
        return {
            "capabilities": {
                "interval": "1h",
                "history": "recent",
                "max_intraday_days": 60,
                "provider": "yfinance",
                "coverage": "best_effort",
            },
            "records": records,
        }

    return fetch_json


def _stooq_us_stock_daily_fetcher(
    symbols: tuple[str, ...],
    timeout_seconds: float,
) -> FetchJson:
    def fetch_json(period: str) -> object:
        start = _period_start(period)
        end = _period_end(period)
        records: list[dict[str, object]] = []
        for symbol in symbols:
            url = "https://stooq.com/q/d/l/"
            params = {
                "s": f"{symbol.lower()}.us",
                "d1": start.date().strftime("%Y%m%d"),
                "d2": end.date().strftime("%Y%m%d"),
                "i": "d",
            }
            def request_payload(
                request_url: str = url,
                request_params: dict[str, str] = params,
            ) -> object:
                with httpx.Client(timeout=timeout_seconds) as client:
                    response = client.get(request_url, params=request_params)
                    response.raise_for_status()
                    return response.text

            payload = _fetch_with_provider_retries("stooq", "us_prices_daily", request_payload)
            records.extend(_normalize_stooq_us_daily_csv(symbol, payload))
        return {
            "capabilities": {
                "interval": "1d",
                "history": "20y",
                "provider": "stooq",
                "coverage": "best_effort",
            },
            "records": records,
        }

    return fetch_json


def _resolve_vn_symbols(
    default: tuple[str, ...],
    instrument_id: str | None,
) -> tuple[str, ...]:
    if instrument_id and instrument_id.startswith("vn_stock:"):
        return (instrument_id.split(":", 1)[1].upper(),)
    return default


def _vnstock_hourly_payload(
    period: str,
    symbols: tuple[str, ...],
    api_key: str | None,
) -> object:
    if api_key:
        os.environ["VNSTOCK_API_KEY"] = api_key
    start = _period_start(period)
    end = start + timedelta(days=1)
    records: list[dict[str, object]] = []
    symbol_failures: list[dict[str, str]] = []
    for symbol in symbols:
        try:
            raw_history = _fetch_vnstock_symbol_history(
                symbol=symbol,
                start=start.date().isoformat(),
                end=end.date().isoformat(),
            )
        except ProviderFetchError as exc:
            symbol_failures.append(
                {"symbol": symbol, "error": str(exc)}
            )
            continue
        records.extend(_normalize_vnstock_history(symbol, raw_history))
        _throttle_vnstock_symbol_fetch()
    return {
        "capabilities": {
            "interval": "1h",
            "provider": "vnstock",
            "coverage": "best_effort",
            "from": start.date().isoformat(),
            "to": end.date().isoformat(),
            "covered_from": start.date().isoformat(),
            "covered_to": end.date().isoformat(),
            "symbol_failures": symbol_failures,
        },
        "records": records,
    }


def _vnstock_daily_payload(
    period: str,
    symbols: tuple[str, ...],
    api_key: str | None,
) -> object:
    if api_key:
        os.environ["VNSTOCK_API_KEY"] = api_key
    start = _period_start(period)
    end_candidate = (
        _period_end(period)
        if ":" in period
        else start
    )
    end = end_candidate if end_candidate >= start else start
    records: list[dict[str, object]] = []
    symbol_failures: list[dict[str, str]] = []
    for symbol in symbols:
        try:
            raw_history = _fetch_vnstock_symbol_daily_history(
                symbol=symbol,
                start=start.date().isoformat(),
                end=end.date().isoformat(),
            )
        except ProviderFetchError as exc:
            symbol_failures.append(
                {"symbol": symbol, "error": str(exc)}
            )
            continue
        records.extend(
            _normalize_vnstock_daily_history(symbol, raw_history)
        )
        _throttle_vnstock_symbol_fetch()
    return {
        "capabilities": {
            "interval": "1d",
            "provider": "vnstock",
            "coverage": "rolling",
            "from": start.date().isoformat(),
            "to": end.date().isoformat(),
            "covered_from": start.date().isoformat(),
            "covered_to": end.date().isoformat(),
            "symbol_failures": symbol_failures,
        },
        "records": records,
    }


def _throttle_vnstock_symbol_fetch() -> None:
    delay_raw = os.getenv("FINMIND_VNSTOCK_SYMBOL_DELAY_SECONDS", "0.75")
    try:
        delay_seconds = float(delay_raw)
    except ValueError:
        delay_seconds = 0.75
    if delay_seconds > 0:
        time.sleep(delay_seconds)


def _vnstock_fetcher(
    symbols: tuple[str, ...],
    api_key: str | None,
    _timeout_seconds: float,
) -> FetchJson:
    def fetch_json(period: str) -> object:
        return _vnstock_hourly_payload(period, symbols, api_key)

    return fetch_json


def _vnstock_daily_fetcher(
    symbols: tuple[str, ...],
    api_key: str | None,
    _timeout_seconds: float,
) -> FetchJson:
    def fetch_json(period: str) -> object:
        return _vnstock_daily_payload(period, symbols, api_key)

    return fetch_json


def _fetch_vnstock_symbol_daily_history(
    symbol: str,
    start: str,
    end: str,
) -> object:
    try:
        quote_class = _vnstock_quote_class()
    except ImportError as exc:
        raise ProviderFetchError(
            "vnstock adapter for vn_prices_daily requires the vnstock"
            " package"
        ) from exc

    try:
        quote = quote_class(
            source="VCI",
            symbol=symbol,
            random_agent=False,
            show_log=False,
        )
        return quote.history(start=start, end=end, interval="1D")
    except SystemExit as exc:  # pragma: no cover - provider boundary
        raise ProviderFetchError(
            _safe_provider_exit("vnstock", "vn_prices_daily", exc)
        ) from exc
    except Exception as exc:  # pragma: no cover - provider boundary
        raise ProviderFetchError(
            "vnstock fetch failed for vn_prices_daily: "
            f"{exc.__class__.__name__}"
        ) from exc


def _normalize_vnstock_daily_history(
    symbol: str,
    raw_history: object,
) -> list[dict[str, object]]:
    rows = _rows_from_tabular(raw_history)
    records: list[dict[str, object]] = []
    for row in rows:
        trade_date = _vnstock_row_date(row)
        if trade_date is None:
            continue
        records.append(
            {
                "instrument_id": f"vn_stock:{symbol}",
                "symbol": symbol,
                "exchange": str(row.get("exchange", "HOSE")),
                "trade_date": trade_date.isoformat(),
                "open": row.get("open"),
                "high": row.get("high"),
                "low": row.get("low"),
                "close": row.get("close"),
                "volume": row.get("volume"),
                "value": row.get("value"),
                "currency": str(row.get("currency", "VND")),
            }
        )
    return records


def _vnstock_row_date(row: Mapping[str, Any]) -> date | None:
    for key in (
        "trade_date",
        "trading_date",
        "date",
        "time",
        "datetime",
        "tradingDate",
    ):
        value = row.get(key)
        if value is None:
            continue
        text = str(value)
        try:
            if "T" in text or " " in text:
                return _parse_datetime(text).date()
            return date.fromisoformat(text[:10])
        except ValueError:
            continue
    return None


def _fetch_vnstock_symbol_history(symbol: str, start: str, end: str) -> object:
    try:
        quote_class = _vnstock_quote_class()
    except ImportError as exc:
        raise ProviderFetchError(
            "vnstock adapter for vn_prices requires the vnstock package"
        ) from exc

    try:
        quote = quote_class(
            source="VCI",
            symbol=symbol,
            random_agent=False,
            show_log=False,
        )
        return quote.history(start=start, end=end, interval="1H")
    except SystemExit as exc:  # pragma: no cover - live provider boundary
        raise ProviderFetchError(_safe_provider_exit("vnstock", "vn_prices", exc)) from exc
    except Exception as exc:  # pragma: no cover - live provider boundary
        raise ProviderFetchError(
            f"vnstock fetch failed for vn_prices: {exc.__class__.__name__}"
        ) from exc


def _vnstock_quote_class() -> type:
    from vnstock.api.quote import Quote  # type: ignore[import-not-found]

    return Quote


def _safe_provider_exit(provider: str, source_id: str, exc: SystemExit) -> str:
    raw_message = str(exc)
    if "rate limit" in raw_message.lower() or "giới hạn" in raw_message.lower():
        return f"{provider} fetch failed for {source_id}: rate limit exceeded"
    return f"{provider} fetch failed for {source_id}: provider terminated request"


def _normalize_vnstock_history(symbol: str, raw_history: object) -> list[dict[str, object]]:
    rows = _rows_from_tabular(raw_history)
    records: list[dict[str, object]] = []
    for row in rows:
        interval_start = _vnstock_row_time(row)
        if interval_start is None:
            continue
        records.append(
            {
                "instrument_id": f"vn_stock:{symbol}",
                "symbol": symbol,
                "exchange": str(row.get("exchange", "HOSE")),
                "interval_start": interval_start.isoformat(),
                "interval_end": (interval_start + timedelta(hours=1)).isoformat(),
                "open": row.get("open"),
                "high": row.get("high"),
                "low": row.get("low"),
                "close": row.get("close"),
                "volume": row.get("volume"),
                "value": row.get("value"),
                "currency": str(row.get("currency", "VND")),
            }
        )
    return records


def _rows_from_tabular(raw_history: object) -> list[Mapping[str, Any]]:
    if hasattr(raw_history, "to_dict"):
        records = raw_history.to_dict(orient="records")
    else:
        records = raw_history
    if not isinstance(records, list):
        raise ProviderFetchError("vnstock response is not tabular")
    rows: list[Mapping[str, Any]] = []
    for record in records:
        if not isinstance(record, Mapping):
            continue
        rows.append(record)
    return rows


def _vnstock_row_time(row: Mapping[str, Any]) -> datetime | None:
    for key in ("interval_start", "time", "datetime", "date", "tradingDate"):
        if row.get(key) is not None:
            return _parse_datetime(str(row[key]))
    return None


def _alpha_vantage_xauusd_daily_fetcher(
    api_key: str | None,
    timeout_seconds: float,
) -> FetchJson:
    if not api_key:
        return _unconfigured_fetch("alpha_vantage", "xauusd_prices_daily")

    def fetch_json(_period: str) -> object:
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": "GLD",
            "outputsize": "compact",
            "apikey": api_key,
        }
        def request_payload() -> object:
            with httpx.Client(timeout=timeout_seconds) as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                return response.json()

        payload = _fetch_with_provider_retries(
            "alpha_vantage",
            "xauusd_prices_daily",
            request_payload,
        )
        return _normalize_alpha_vantage_payload(payload)

    return fetch_json


def _normalize_yfinance_payload(payload: object) -> dict[str, object]:
    if not isinstance(payload, Mapping):
        raise ProviderFetchError("yfinance response is not an object")
    chart = payload.get("chart")
    if not isinstance(chart, Mapping):
        raise ProviderFetchError("yfinance response missing chart")
    results = chart.get("result")
    if not isinstance(results, list) or not results:
        return {
            "capabilities": {
                "interval": "1h",
                "history": "recent",
                "fallback_dataset": "xauusd_prices_daily",
            },
            "records": [],
        }
    result = results[0]
    if not isinstance(result, Mapping):
        raise ProviderFetchError("yfinance result is not an object")
    timestamps = result.get("timestamp", [])
    indicators = result.get("indicators", {})
    quote_list = indicators.get("quote", []) if isinstance(indicators, Mapping) else []
    quote = quote_list[0] if isinstance(quote_list, list) and quote_list else {}
    if not isinstance(timestamps, list) or not isinstance(quote, Mapping):
        raise ProviderFetchError("yfinance response missing quote data")
    records: list[dict[str, object]] = []
    for index, timestamp in enumerate(timestamps):
        start = datetime.fromtimestamp(int(timestamp), tz=UTC)
        open_price = _list_value(quote, "open", index)
        high = _list_value(quote, "high", index)
        low = _list_value(quote, "low", index)
        close = _list_value(quote, "close", index)
        if None in {open_price, high, low, close}:
            continue
        records.append(
            {
                "interval_start": start.isoformat(),
                "interval_end": (start + timedelta(hours=1)).isoformat(),
                "open": open_price,
                "high": high,
                "low": low,
                "close": close,
            }
        )
    return {
        "capabilities": {
            "interval": "1h",
            "history": "recent",
            "max_intraday_days": 60,
            "fallback_dataset": "xauusd_prices_daily",
        },
        "records": records,
    }


def _normalize_yfinance_us_payload(
    symbol: str,
    payload: object,
) -> list[dict[str, object]]:
    if not isinstance(payload, Mapping):
        raise ProviderFetchError("yfinance response is not an object")
    chart = payload.get("chart")
    if not isinstance(chart, Mapping):
        raise ProviderFetchError("yfinance response missing chart")
    results = chart.get("result")
    if not isinstance(results, list) or not results:
        return []
    result = results[0]
    if not isinstance(result, Mapping):
        raise ProviderFetchError("yfinance result is not an object")
    timestamps = result.get("timestamp", [])
    indicators = result.get("indicators", {})
    quote_list = indicators.get("quote", []) if isinstance(indicators, Mapping) else []
    quote = quote_list[0] if isinstance(quote_list, list) and quote_list else {}
    meta = result.get("meta", {})
    if not isinstance(timestamps, list) or not isinstance(quote, Mapping):
        raise ProviderFetchError("yfinance response missing quote data")
    exchange = "NASDAQ" if symbol == "^VIX" else _yfinance_exchange(meta)
    records: list[dict[str, object]] = []
    for index, timestamp in enumerate(timestamps):
        start = datetime.fromtimestamp(int(timestamp), tz=UTC)
        open_price = _list_value(quote, "open", index)
        high = _list_value(quote, "high", index)
        low = _list_value(quote, "low", index)
        close = _list_value(quote, "close", index)
        volume = _list_value(quote, "volume", index) or 0
        if None in {open_price, high, low, close}:
            continue
        records.append(
            {
                "instrument_id": f"us_stock:{symbol}",
                "symbol": symbol,
                "exchange": exchange,
                "interval_start": start.isoformat(),
                "interval_end": (start + timedelta(hours=1)).isoformat(),
                "open": open_price,
                "high": high,
                "low": low,
                "close": close,
                "volume": volume,
                "currency": "USD",
                "sector": _us_proxy_sector(symbol),
                "industry": _us_proxy_industry(symbol),
            }
        )
    return records


def _normalize_stooq_us_daily_csv(
    symbol: str,
    payload: str,
) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    reader = csv.DictReader(StringIO(payload))
    for row in reader:
        trading_date = row.get("Date")
        open_price = row.get("Open")
        high = row.get("High")
        low = row.get("Low")
        close = row.get("Close")
        volume = row.get("Volume")
        if not trading_date or not open_price or not high or not low or not close:
            continue
        records.append(
            {
                "instrument_id": f"us_stock:{symbol}",
                "symbol": symbol,
                "exchange": "NASDAQ",
                "trading_date": trading_date,
                "open": float(open_price),
                "high": float(high),
                "low": float(low),
                "close": float(close),
                "volume": int(float(volume or 0)),
                "currency": "USD",
                "sector": _us_equity_sector(symbol),
                "industry": _us_equity_industry(symbol),
            }
        )
    return records


def _yfinance_exchange(meta: object) -> str:
    if isinstance(meta, Mapping) and meta.get("exchangeName"):
        return str(meta["exchangeName"])
    return "US"


def _us_proxy_sector(symbol: str) -> str:
    return {
        "SPY": "Broad Market",
        "QQQ": "Technology",
        "DIA": "Industrials",
        "IWM": "Small Cap",
        "^VIX": "Volatility",
    }.get(symbol, "US Market")


def _us_proxy_industry(symbol: str) -> str:
    return {
        "SPY": "S&P 500 Proxy",
        "QQQ": "NASDAQ 100 Proxy",
        "DIA": "Dow Proxy",
        "IWM": "Russell 2000 Proxy",
        "^VIX": "Volatility Index",
    }.get(symbol, "Equity")


def _us_equity_sector(symbol: str) -> str:
    return {
        "AAPL": "Technology",
        "MSFT": "Technology",
        "NVDA": "Technology",
        "AMZN": "Consumer Cyclical",
    }.get(symbol, "US Equity")


def _us_equity_industry(symbol: str) -> str:
    return {
        "AAPL": "Consumer Electronics",
        "MSFT": "Software",
        "NVDA": "Semiconductors",
        "AMZN": "Internet Retail",
    }.get(symbol, "Equity")


def _normalize_alpha_vantage_payload(payload: object) -> dict[str, object]:
    if not isinstance(payload, Mapping):
        raise ProviderFetchError("alpha_vantage response is not an object")
    series = payload.get("Time Series (Daily)", {})
    if not isinstance(series, Mapping):
        raise ProviderFetchError("alpha_vantage response missing daily series")
    records: list[dict[str, object]] = []
    for trading_date, row in series.items():
        if not isinstance(row, Mapping):
            continue
        records.append(
            {
                "trading_date": str(trading_date),
                "open": row.get("1. open"),
                "high": row.get("2. high"),
                "low": row.get("3. low"),
                "close": row.get("4. close"),
            }
        )
    return {
        "capabilities": {
            "interval": "1d",
            "fallback_for": "xauusd_prices",
            "reason": "free 1h history unavailable",
        },
        "records": records,
    }


def _list_value(
    quote: Mapping[str, object],
    key: str,
    index: int,
) -> object | None:
    values = quote.get(key)
    if not isinstance(values, list) or index >= len(values):
        return None
    return values[index]


def _period_start(period: str) -> datetime:
    value = period.split(":", maxsplit=1)[0]
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _period_end(period: str) -> datetime:
    value = period.split(":", maxsplit=1)[1] if ":" in period else period
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _safe_fetch_error(exc: Exception) -> str:
    if isinstance(exc, httpx.HTTPStatusError):
        return f"HTTP {exc.response.status_code}"
    if isinstance(exc, httpx.TimeoutException):
        return "timeout"
    if isinstance(exc, httpx.RequestError):
        return exc.__class__.__name__
    return exc.__class__.__name__


def _fetch_with_provider_retries(
    provider: str,
    source_id: str,
    request_payload: Callable[[], object],
) -> object:
    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        try:
            return request_payload()
        except (httpx.HTTPError, ValueError) as exc:
            if attempt == max_attempts or not _is_retryable_provider_error(exc):
                raise ProviderFetchError(
                    f"{provider} fetch failed for {source_id}: "
                    f"{_safe_fetch_error(exc)} after {attempt} attempt(s)"
                ) from exc
            _provider_retry_sleep(attempt)
    raise ProviderFetchError(f"{provider} fetch failed for {source_id}: retry exhausted")


def _is_retryable_provider_error(exc: Exception) -> bool:
    if isinstance(exc, httpx.TimeoutException | httpx.ConnectError | httpx.NetworkError):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in {429, 500, 502, 503, 504}
    return False


def _provider_retry_sleep(attempt: int) -> None:
    time.sleep(min(2 ** (attempt - 1), 4))


def _capabilities_from_payload(payload: object) -> dict[str, object]:
    if not isinstance(payload, Mapping):
        return {}
    capabilities = payload.get("capabilities", {})
    if not isinstance(capabilities, Mapping):
        return {}
    return dict(capabilities)


def _require_fields(
    source_id: str,
    row: Mapping[str, Any],
    fields: tuple[str, ...],
) -> None:
    missing = [field for field in fields if row.get(field) is None]
    if missing:
        raise ProviderFetchError(
            f"{source_id} provider response is missing fields: {', '.join(missing)}"
        )


def _parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _collected_at(row: Mapping[str, Any]) -> datetime:
    if row.get("collected_at"):
        return _parse_datetime(str(row["collected_at"]))
    return datetime.now(UTC)


def _unconfigured_fetch(provider: str, source_id: str) -> FetchJson:
    def fetch_json(_period: str) -> object:
        raise ProviderFetchError(
            f"{provider} adapter for {source_id} requires configured fetch transport"
        )

    return fetch_json
