from datetime import UTC, datetime, timedelta

from api.platform.ingestion.sources import TimeSeriesRecord


class DemoMarketDataSource:
    def __init__(self, source_id: str) -> None:
        if source_id not in {
            "us_prices",
            "us_prices_daily",
            "vn_prices",
            "xauusd_prices",
            "sjc_gold_prices",
        }:
            raise ValueError(f"Unsupported demo source: {source_id}")
        self.source_id = source_id

    def fetch(
        self,
        period: str,
        *,
        instrument_id: str | None = None,
    ) -> list[TimeSeriesRecord]:
        if self.source_id == "us_prices":
            return _us_price_records(period)
        if self.source_id == "us_prices_daily":
            return _us_daily_records(period)
        if self.source_id == "vn_prices":
            return _vn_price_records(period)
        if self.source_id == "xauusd_prices":
            return _xauusd_records(period)
        return _sjc_gold_records(period)


def create_demo_sources() -> dict[str, DemoMarketDataSource]:
    return {
        source_id: DemoMarketDataSource(source_id)
        for source_id in (
            "us_prices",
            "us_prices_daily",
            "vn_prices",
            "xauusd_prices",
            "sjc_gold_prices",
        )
    }


def _period_date(period: str) -> datetime:
    return datetime.fromisoformat(period.split(":", maxsplit=1)[0]).replace(tzinfo=UTC)


def _vn_price_records(period: str) -> list[TimeSeriesRecord]:
    day = _period_date(period)
    collected_at = day.replace(hour=8, minute=30)
    records: list[TimeSeriesRecord] = []
    rows = (
        ("vn_stock:VCB", "VCB", 57400, [200, 300, 100, 300, 200, 200]),
        ("vn_stock:VPB", "VPB", 21400, [50, -80, 120, 150, 180, 210]),
    )
    for instrument_id, symbol, base, deltas in rows:
        open_price = float(base)
        for index, delta in enumerate(deltas):
            start = day.replace(hour=2 + index)
            close = open_price + delta
            records.append(
                TimeSeriesRecord(
                    dataset_id="vn_prices",
                    record_key=f"{instrument_id}:{start.isoformat()}",
                    instrument_id=instrument_id,
                    market_time=start,
                    collected_at=collected_at,
                    source_id="vn_prices",
                    payload={
                        "symbol": symbol,
                        "exchange": "HOSE",
                        "interval_start": start.isoformat(),
                        "interval_end": (start + timedelta(hours=1)).isoformat(),
                        "open": open_price,
                        "high": max(open_price, close) + 200,
                        "low": min(open_price, close) - 100,
                        "close": close,
                        "volume": 320000 + index * 70000,
                        "value": (320000 + index * 70000) * close,
                        "currency": "VND",
                    },
                )
            )
            open_price = close
    return records[:6]


def _us_price_records(period: str) -> list[TimeSeriesRecord]:
    day = _period_date(period)
    collected_at = day.replace(hour=21, minute=30)
    records: list[TimeSeriesRecord] = []
    rows = _us_demo_rows()
    for instrument_id, symbol, exchange, base, sector, industry in rows:
        open_price = float(base)
        for index, delta in enumerate([1.2, -0.7, 1.8, 0.9, -0.4, 1.1]):
            start = day.replace(hour=14 + index)
            close = open_price + delta
            records.append(
                TimeSeriesRecord(
                    dataset_id="us_prices",
                    record_key=f"{instrument_id}:{start.isoformat()}",
                    instrument_id=instrument_id,
                    market_time=start,
                    collected_at=collected_at,
                    source_id="us_prices",
                    payload={
                        "market": "US_STOCK",
                        "symbol": symbol,
                        "exchange": exchange,
                        "interval_start": start.isoformat(),
                        "interval_end": (start + timedelta(hours=1)).isoformat(),
                        "open": open_price,
                        "high": max(open_price, close) + 0.6,
                        "low": min(open_price, close) - 0.4,
                        "close": close,
                        "volume": 1200000 + index * 80000,
                        "value": (1200000 + index * 80000) * close,
                        "currency": "USD",
                        "sector": sector,
                        "industry": industry,
                    },
                )
            )
            open_price = close
    return records[:6]


def _us_daily_records(period: str) -> list[TimeSeriesRecord]:
    day = _period_date(period)
    collected_at = day.replace(hour=21, minute=30)
    return [
        TimeSeriesRecord(
            dataset_id="us_prices_daily",
            record_key=f"{instrument_id}:{day.date().isoformat()}",
            instrument_id=instrument_id,
            market_time=day,
            collected_at=collected_at,
            source_id="us_prices_daily",
            payload={
                "market": "US_STOCK",
                "symbol": symbol,
                "exchange": exchange,
                "trading_date": day.date().isoformat(),
                "open": base,
                "high": base + 2.4,
                "low": base - 1.8,
                "close": base + 1.1,
                "volume": 52000000,
                "currency": "USD",
                "sector": sector,
                "industry": industry,
            },
        )
        for instrument_id, symbol, exchange, base, sector, industry in _us_demo_rows()
    ]


def _us_demo_rows() -> tuple[tuple[str, str, str, float, str, str], ...]:
    return (
        ("us_stock:AAPL", "AAPL", "NASDAQ", 195.0, "Technology", "Consumer Electronics"),
        ("us_stock:MSFT", "MSFT", "NASDAQ", 432.0, "Technology", "Software"),
        ("us_stock:NVDA", "NVDA", "NASDAQ", 128.0, "Technology", "Semiconductors"),
        ("us_stock:AMZN", "AMZN", "NASDAQ", 186.0, "Consumer Cyclical", "Internet Retail"),
    )


def _xauusd_records(period: str) -> list[TimeSeriesRecord]:
    day = _period_date(period)
    collected_at = day.replace(hour=8, minute=30)
    records: list[TimeSeriesRecord] = []
    open_price = 2320.0
    for index, delta in enumerate([1.5, -0.8, 2.2, 1.1, -1.4, 2.6]):
        start = day.replace(hour=index)
        close = open_price + delta
        records.append(
            TimeSeriesRecord(
                dataset_id="xauusd_prices",
                record_key=f"gold:XAUUSD:{start.isoformat()}",
                instrument_id="gold:XAUUSD",
                market_time=start,
                collected_at=collected_at,
                source_id="xauusd_prices",
                payload={
                    "symbol": "XAUUSD",
                    "interval_start": start.isoformat(),
                    "interval_end": (start + timedelta(hours=1)).isoformat(),
                    "open": open_price,
                    "high": max(open_price, close) + 1.8,
                    "low": min(open_price, close) - 1.1,
                    "close": close,
                    "unit": "oz",
                    "currency": "USD",
                },
            )
        )
        open_price = close
    return records


def _sjc_gold_records(period: str) -> list[TimeSeriesRecord]:
    day = _period_date(period)
    collected_at = day.replace(hour=8, minute=30)
    return [
        TimeSeriesRecord(
            dataset_id="sjc_gold_prices",
            record_key=f"gold:SJC:buy_sell:{day.date().isoformat()}",
            instrument_id="gold:SJC",
            market_time=day,
            collected_at=collected_at,
            source_id="sjc_gold_prices",
            payload={
                "symbol": "SJC",
                "quote_type": "buy_sell",
                "quote_date": day.date().isoformat(),
                "buy_price": 76400000,
                "sell_price": 78600000,
                "unit": "tael",
                "currency": "VND",
                "location": "VN",
            },
        )
    ]
