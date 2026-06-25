from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal

from api.platform.models import FreshnessStatus

MarketView = Literal["VN", "US", "Commodity"]
ChartTimeframe = Literal["1h", "4h", "1d", "1M"]


@dataclass(frozen=True)
class MarketInstrumentProfile:
    instrument_id: str
    symbol: str
    market: str
    asset_class: str
    exchange: str | None
    display_name: str
    currency: str
    sector: str | None
    industry: str | None
    sub_industry: str | None
    status: str = "active"


@dataclass(frozen=True)
class MarketCollection:
    collection_id: str
    market: str
    name: str
    collection_type: str
    sort_order: int


@dataclass(frozen=True)
class MarketCollectionMembership:
    collection_id: str
    instrument_id: str
    weight: float | None


@dataclass(frozen=True)
class StockBar:
    instrument_id: str
    market: str
    symbol: str
    exchange: str
    interval_start: datetime
    interval_end: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    value: float
    currency: str
    collected_at: datetime
    source_id: str
    freshness_status: FreshnessStatus


@dataclass(frozen=True)
class LinePoint:
    time: datetime
    value: float


@dataclass(frozen=True)
class DemoMarketStore:
    instruments: tuple[MarketInstrumentProfile, ...]
    collections: tuple[MarketCollection, ...]
    memberships: tuple[MarketCollectionMembership, ...]
    stock_bars: tuple[StockBar, ...]
    index_series: dict[str, tuple[LinePoint, ...]]


@dataclass(frozen=True)
class MarketService:
    store: DemoMarketStore

    def overview(
        self,
        market: str,
        collection_id: str | None = None,
        watchlist_id: str | None = None,
    ) -> dict[str, object]:
        selected_market = _normalize_market(market)
        active_collection = collection_id or watchlist_id or _default_collection(selected_market)
        instruments = self._instruments_for_collection(selected_market, active_collection)
        latest_by_instrument = self._latest_stock_bars(instruments)

        return {
            "available_markets": ["VN", "US", "Commodity"],
            "selected_market": selected_market,
            "watchlists": [
                _serialize_collection(collection)
                for collection in self.store.collections
                if (
                    collection.market == selected_market
                    and collection.collection_type == "watchlist"
                )
            ],
            "collections": [
                _serialize_collection(collection)
                for collection in sorted(self.store.collections, key=lambda item: item.sort_order)
                if (
                    collection.market == selected_market
                    and collection.collection_type != "watchlist"
                )
            ],
            "index_charts": self._index_charts(selected_market),
            "heatmap": [
                _serialize_heatmap_cell(instrument, latest_by_instrument[instrument.instrument_id])
                for instrument in instruments
                if instrument.instrument_id in latest_by_instrument
            ],
            "instrument_rows": [
                _serialize_instrument_row(
                    instrument,
                    latest_by_instrument[instrument.instrument_id],
                )
                for instrument in instruments
                if instrument.instrument_id in latest_by_instrument
            ],
        }

    def instrument_chart(
        self,
        instrument_id: str,
        timeframe: str = "1h",
    ) -> dict[str, object]:
        selected_timeframe = _normalize_timeframe(timeframe)
        instrument = self._instrument(instrument_id)
        bars = [
            bar
            for bar in self.store.stock_bars
            if bar.instrument_id == instrument_id
        ]
        if not bars:
            raise KeyError("Instrument chart data not found")
        aggregated = _aggregate_stock_bars(
            sorted(bars, key=lambda item: item.interval_start),
            selected_timeframe,
        )
        records = [_serialize_chart_bar(bar) for bar in aggregated]
        freshness = max(bars, key=lambda item: item.interval_start)
        return {
            "instrument": _serialize_instrument(instrument),
            "timeframe": selected_timeframe,
            "freshness": {
                "status": freshness.freshness_status.value,
                "as_of": freshness.interval_start.isoformat(),
            },
            "records": records,
            "table": records,
        }

    def _instruments_for_collection(
        self,
        market: MarketView,
        collection_id: str,
    ) -> list[MarketInstrumentProfile]:
        member_ids = {
            membership.instrument_id
            for membership in self.store.memberships
            if membership.collection_id == collection_id
        }
        if not member_ids:
            member_ids = {
                instrument.instrument_id
                for instrument in self.store.instruments
                if _instrument_view(instrument) == market
            }
        return sorted(
            [
                instrument
                for instrument in self.store.instruments
                if instrument.instrument_id in member_ids and _instrument_view(instrument) == market
            ],
            key=lambda item: item.symbol,
        )

    def _latest_stock_bars(
        self,
        instruments: list[MarketInstrumentProfile],
    ) -> dict[str, StockBar]:
        requested_ids = {instrument.instrument_id for instrument in instruments}
        latest: dict[str, StockBar] = {}
        for bar in self.store.stock_bars:
            if bar.instrument_id not in requested_ids:
                continue
            current = latest.get(bar.instrument_id)
            if current is None or bar.interval_start > current.interval_start:
                latest[bar.instrument_id] = bar
        return latest

    def _index_charts(self, market: MarketView) -> list[dict[str, object]]:
        index_symbols = {
            "VN": ("VNINDEX", "VN100", "VN30", "HNXINDEX", "UPCOM"),
            "US": ("S&P 500", "NASDAQ 100", "Dow", "Russell 2000", "VIX"),
            "Commodity": (),
        }[market]
        charts: list[dict[str, object]] = []
        for symbol in index_symbols:
            series = self.store.index_series.get(symbol, ())
            if not series:
                continue
            latest = series[-1]
            previous = series[-2] if len(series) > 1 else latest
            change_percent = round(((latest.value - previous.value) / previous.value) * 100, 2)
            charts.append(
                {
                    "symbol": symbol,
                    "name": symbol,
                    "last": latest.value,
                    "change_percent": change_percent,
                    "series": [
                        {"time": point.time.isoformat(), "value": point.value}
                        for point in series
                    ],
                }
            )
        return charts

    def _instrument(self, instrument_id: str) -> MarketInstrumentProfile:
        for instrument in self.store.instruments:
            if instrument.instrument_id == instrument_id:
                return instrument
        raise KeyError("Instrument not found")


def create_demo_market_service() -> MarketService:
    collected_at = datetime(2026, 6, 18, 8, 30, tzinfo=UTC)
    instruments = (
        MarketInstrumentProfile(
            instrument_id="vn_stock:VCB",
            symbol="VCB",
            market="VN_STOCK",
            asset_class="stock",
            exchange="HOSE",
            display_name="Vietcombank",
            currency="VND",
            sector="Financials",
            industry="Banking",
            sub_industry="Commercial Banking",
        ),
        MarketInstrumentProfile(
            instrument_id="vn_stock:VPB",
            symbol="VPB",
            market="VN_STOCK",
            asset_class="stock",
            exchange="HOSE",
            display_name="VPBank",
            currency="VND",
            sector="Financials",
            industry="Banking",
            sub_industry="Commercial Banking",
        ),
        MarketInstrumentProfile(
            instrument_id="vn_stock:GAS",
            symbol="GAS",
            market="VN_STOCK",
            asset_class="stock",
            exchange="HOSE",
            display_name="PV Gas",
            currency="VND",
            sector="Energy",
            industry="Oil & Gas",
            sub_industry="Gas Utilities",
        ),
        MarketInstrumentProfile(
            instrument_id="us_stock:AAPL",
            symbol="AAPL",
            market="US_STOCK",
            asset_class="stock",
            exchange="NASDAQ",
            display_name="Apple Inc.",
            currency="USD",
            sector="Technology",
            industry="Consumer Electronics",
            sub_industry="Hardware",
        ),
        MarketInstrumentProfile(
            instrument_id="us_stock:MSFT",
            symbol="MSFT",
            market="US_STOCK",
            asset_class="stock",
            exchange="NASDAQ",
            display_name="Microsoft Corporation",
            currency="USD",
            sector="Technology",
            industry="Software",
            sub_industry="Application Software",
        ),
        MarketInstrumentProfile(
            instrument_id="us_stock:NVDA",
            symbol="NVDA",
            market="US_STOCK",
            asset_class="stock",
            exchange="NASDAQ",
            display_name="NVIDIA Corporation",
            currency="USD",
            sector="Technology",
            industry="Semiconductors",
            sub_industry="Graphics Processors",
        ),
        MarketInstrumentProfile(
            instrument_id="us_stock:AMZN",
            symbol="AMZN",
            market="US_STOCK",
            asset_class="stock",
            exchange="NASDAQ",
            display_name="Amazon.com, Inc.",
            currency="USD",
            sector="Consumer Cyclical",
            industry="Internet Retail",
            sub_industry="E-Commerce",
        ),
    )
    collections = (
        MarketCollection("watchlist:default-vn", "VN", "Default VN", "watchlist", 0),
        MarketCollection("all", "VN", "All", "theme", 1),
        MarketCollection("vnindex", "VN", "VNINDEX", "index", 2),
        MarketCollection("vn100", "VN", "VN100", "index", 3),
        MarketCollection("vn30", "VN", "VN30", "index", 4),
        MarketCollection("hnxindex", "VN", "HNXINDEX", "index", 5),
        MarketCollection("upcom", "VN", "UPCOM", "index", 6),
        MarketCollection("vnbanking", "VN", "VN Banking", "sector", 7),
        MarketCollection("vnenergy", "VN", "VN Energy", "sector", 8),
        MarketCollection("watchlist:default-us", "US", "Default US", "watchlist", 0),
        MarketCollection("all", "US", "All", "theme", 1),
        MarketCollection("sp500", "US", "S&P 500", "index", 2),
        MarketCollection("nasdaq100", "US", "NASDAQ 100", "index", 3),
        MarketCollection("dow", "US", "Dow", "index", 4),
        MarketCollection("russell2000", "US", "Russell 2000", "index", 5),
        MarketCollection("us-technology", "US", "Technology", "sector", 6),
        MarketCollection("us-broad-market", "US", "Broad Market", "sector", 7),
    )
    memberships = (
        MarketCollectionMembership("watchlist:default-vn", "vn_stock:VCB", 0.4),
        MarketCollectionMembership("watchlist:default-vn", "vn_stock:VPB", 0.3),
        MarketCollectionMembership("watchlist:default-vn", "vn_stock:GAS", 0.3),
        MarketCollectionMembership("all", "vn_stock:VCB", None),
        MarketCollectionMembership("all", "vn_stock:VPB", None),
        MarketCollectionMembership("all", "vn_stock:GAS", None),
        MarketCollectionMembership("vn30", "vn_stock:VCB", 0.12),
        MarketCollectionMembership("vn30", "vn_stock:VPB", 0.08),
        MarketCollectionMembership("vn100", "vn_stock:VCB", 0.09),
        MarketCollectionMembership("vn100", "vn_stock:VPB", 0.07),
        MarketCollectionMembership("vn100", "vn_stock:GAS", 0.05),
        MarketCollectionMembership("hnxindex", "vn_stock:VPB", 0.04),
        MarketCollectionMembership("upcom", "vn_stock:GAS", 0.03),
        MarketCollectionMembership("vnbanking", "vn_stock:VCB", None),
        MarketCollectionMembership("vnbanking", "vn_stock:VPB", None),
        MarketCollectionMembership("vnenergy", "vn_stock:GAS", None),
        MarketCollectionMembership("watchlist:default-us", "us_stock:AAPL", 0.3),
        MarketCollectionMembership("watchlist:default-us", "us_stock:MSFT", 0.3),
        MarketCollectionMembership("watchlist:default-us", "us_stock:NVDA", 0.25),
        MarketCollectionMembership("watchlist:default-us", "us_stock:AMZN", 0.15),
        MarketCollectionMembership("all", "us_stock:AAPL", None),
        MarketCollectionMembership("all", "us_stock:MSFT", None),
        MarketCollectionMembership("all", "us_stock:NVDA", None),
        MarketCollectionMembership("all", "us_stock:AMZN", None),
        MarketCollectionMembership("sp500", "us_stock:AAPL", 0.07),
        MarketCollectionMembership("sp500", "us_stock:MSFT", 0.06),
        MarketCollectionMembership("sp500", "us_stock:NVDA", 0.05),
        MarketCollectionMembership("sp500", "us_stock:AMZN", 0.04),
        MarketCollectionMembership("nasdaq100", "us_stock:AAPL", 0.09),
        MarketCollectionMembership("nasdaq100", "us_stock:MSFT", 0.08),
        MarketCollectionMembership("nasdaq100", "us_stock:NVDA", 0.07),
        MarketCollectionMembership("nasdaq100", "us_stock:AMZN", 0.05),
        MarketCollectionMembership("dow", "us_stock:MSFT", 0.05),
        MarketCollectionMembership("russell2000", "us_stock:AMZN", 0.01),
        MarketCollectionMembership("us-technology", "us_stock:AAPL", None),
        MarketCollectionMembership("us-technology", "us_stock:MSFT", None),
        MarketCollectionMembership("us-technology", "us_stock:NVDA", None),
        MarketCollectionMembership("us-broad-market", "us_stock:AMZN", None),
    )
    return MarketService(
        DemoMarketStore(
            instruments=instruments,
            collections=collections,
            memberships=memberships,
            stock_bars=(
                *_vcb_stock_bars(collected_at),
                *_stock_bars(
                    "vn_stock:VPB",
                    "VPB",
                    "HOSE",
                    21400,
                    [50, -80, 120, 150, 180, 210],
                    collected_at,
                ),
                *_stock_bars(
                    "vn_stock:GAS",
                    "GAS",
                    "HOSE",
                    84200,
                    [-200, 100, 180, -90, 210, 250],
                    collected_at,
                ),
                *_us_stock_bars(
                    "us_stock:AAPL",
                    "AAPL",
                    "NASDAQ",
                    195.0,
                    [1.2, -0.7, 1.8, 0.9, -0.4, 1.1],
                    collected_at,
                ),
                *_us_stock_bars(
                    "us_stock:MSFT",
                    "MSFT",
                    "NASDAQ",
                    432.0,
                    [2.1, 1.4, -0.6, 2.3, 1.1, 1.6],
                    collected_at,
                ),
                *_us_stock_bars(
                    "us_stock:NVDA",
                    "NVDA",
                    "NASDAQ",
                    128.0,
                    [-0.5, 0.4, 0.8, -0.2, 0.7, 0.9],
                    collected_at,
                ),
                *_us_stock_bars(
                    "us_stock:AMZN",
                    "AMZN",
                    "NASDAQ",
                    186.0,
                    [0.3, -1.1, -0.4, 0.6, 0.9, -0.2],
                    collected_at,
                ),
            ),
            index_series={
                "VNINDEX": _line_series(1281.2, [0, 2.4, -1.2, 4.1, 5.6, 6.8]),
                "VN100": _line_series(1210.8, [0, -0.8, 1.2, 2.8, 3.1, 3.7]),
                "VN30": _line_series(1320.5, [0, 1.7, 2.1, 3.4, 2.9, 4.2]),
                "HNXINDEX": _line_series(242.4, [0, -0.3, 0.4, 0.9, 0.6, 1.1]),
                "UPCOM": _line_series(98.7, [0, 0.2, -0.1, 0.3, 0.5, 0.4]),
                "S&P 500": _line_series(5480.0, [0, 8.4, 4.2, 13.1, 16.6, 19.8]),
                "NASDAQ 100": _line_series(19320.0, [0, 42.0, 55.0, 48.0, 72.0, 81.0]),
                "Dow": _line_series(38820.0, [0, -18.0, 22.0, 45.0, 38.0, 64.0]),
                "Russell 2000": _line_series(2050.0, [0, -6.2, -3.4, 4.1, 8.2, 6.1]),
                "VIX": _line_series(16.8, [0, -0.2, -0.1, -0.4, -0.5, -0.7]),
            },
        )
    )


def _stock_bars(
    instrument_id: str,
    symbol: str,
    exchange: str,
    base: int,
    deltas: list[int],
    collected_at: datetime,
) -> tuple[StockBar, ...]:
    starts = [
        datetime(2026, 6, 18, 2, 0, tzinfo=UTC),
        datetime(2026, 6, 18, 3, 0, tzinfo=UTC),
        datetime(2026, 6, 18, 4, 0, tzinfo=UTC),
        datetime(2026, 6, 18, 5, 0, tzinfo=UTC),
        datetime(2026, 6, 18, 6, 0, tzinfo=UTC),
        datetime(2026, 6, 18, 7, 0, tzinfo=UTC),
    ]
    bars: list[StockBar] = []
    open_price = float(base)
    for index, start in enumerate(starts):
        close = open_price + deltas[index]
        high = max(open_price, close) + 200
        low = min(open_price, close) - 100
        volume = 320000 + (index * 70000)
        bars.append(
            StockBar(
                instrument_id=instrument_id,
                market="VN_STOCK",
                symbol=symbol,
                exchange=exchange,
                interval_start=start,
                interval_end=start + timedelta(hours=1),
                open=open_price,
                high=high,
                low=low,
                close=close,
                volume=volume,
                value=volume * close,
                currency="VND",
                collected_at=collected_at,
                source_id="demo_vn_prices",
                freshness_status=FreshnessStatus.FRESH,
            )
        )
        open_price = close
    return tuple(bars)


def _us_stock_bars(
    instrument_id: str,
    symbol: str,
    exchange: str,
    base: float,
    deltas: list[float],
    collected_at: datetime,
) -> tuple[StockBar, ...]:
    starts = [
        datetime(2026, 6, 18, 14, 0, tzinfo=UTC),
        datetime(2026, 6, 18, 15, 0, tzinfo=UTC),
        datetime(2026, 6, 18, 16, 0, tzinfo=UTC),
        datetime(2026, 6, 18, 17, 0, tzinfo=UTC),
        datetime(2026, 6, 18, 18, 0, tzinfo=UTC),
        datetime(2026, 6, 18, 19, 0, tzinfo=UTC),
    ]
    bars: list[StockBar] = []
    open_price = base
    for index, start in enumerate(starts):
        close = round(open_price + deltas[index], 2)
        high = round(max(open_price, close) + 0.8, 2)
        low = round(min(open_price, close) - 0.5, 2)
        volume = 1200000 + (index * 85000)
        bars.append(
            StockBar(
                instrument_id=instrument_id,
                market="US_STOCK",
                symbol=symbol,
                exchange=exchange,
                interval_start=start,
                interval_end=start + timedelta(hours=1),
                open=open_price,
                high=high,
                low=low,
                close=close,
                volume=volume,
                value=volume * close,
                currency="USD",
                collected_at=collected_at,
                source_id="demo_us_prices",
                freshness_status=FreshnessStatus.FRESH,
            )
        )
        open_price = close
    return tuple(bars)


def _vcb_stock_bars(collected_at: datetime) -> tuple[StockBar, ...]:
    rows = (
        (datetime(2026, 6, 18, 2, 0, tzinfo=UTC), 57400, 57800, 57300, 57600, 350000),
        (datetime(2026, 6, 18, 3, 0, tzinfo=UTC), 57600, 58100, 57500, 57900, 370000),
        (datetime(2026, 6, 18, 4, 0, tzinfo=UTC), 57900, 58200, 57800, 58000, 390000),
        (datetime(2026, 6, 18, 5, 0, tzinfo=UTC), 58000, 58600, 57900, 58300, 420000),
        (datetime(2026, 6, 18, 6, 0, tzinfo=UTC), 58300, 58900, 58100, 58500, 680000),
        (datetime(2026, 6, 18, 7, 0, tzinfo=UTC), 58500, 58800, 58400, 58700, 710000),
    )
    return tuple(
        StockBar(
            instrument_id="vn_stock:VCB",
            market="VN_STOCK",
            symbol="VCB",
            exchange="HOSE",
            interval_start=start,
            interval_end=start + timedelta(hours=1),
            open=open_price,
            high=high,
            low=low,
            close=close,
            volume=volume,
            value=volume * close,
            currency="VND",
            collected_at=collected_at,
            source_id="demo_vn_prices",
            freshness_status=FreshnessStatus.FRESH,
        )
        for start, open_price, high, low, close, volume in rows
    )


def _line_series(base: float, deltas: list[float]) -> tuple[LinePoint, ...]:
    return tuple(
        LinePoint(
            time=datetime(2026, 6, 18, 2 + index, 0, tzinfo=UTC),
            value=round(base + delta, 2),
        )
        for index, delta in enumerate(deltas)
    )


def _normalize_market(market: str) -> MarketView:
    if market in {"VN", "US", "Commodity"}:
        return market  # type: ignore[return-value]
    raise ValueError("V1 supports VN, US, and Commodity markets")


def _normalize_timeframe(timeframe: str) -> ChartTimeframe:
    if timeframe in {"1h", "4h", "1d", "1M"}:
        return timeframe  # type: ignore[return-value]
    raise ValueError("Unsupported timeframe")


def _default_collection(market: MarketView) -> str:
    if market == "VN":
        return "watchlist:default-vn"
    if market == "US":
        return "watchlist:default-us"
    return "all"


def _instrument_view(instrument: MarketInstrumentProfile) -> MarketView:
    if instrument.market == "VN_STOCK":
        return "VN"
    if instrument.market == "US_STOCK":
        return "US"
    return "Commodity"


def _serialize_collection(collection: MarketCollection) -> dict[str, object]:
    return {
        "id": collection.collection_id,
        "name": collection.name,
        "type": collection.collection_type,
    }


def _serialize_instrument(instrument: MarketInstrumentProfile) -> dict[str, object]:
    return {
        "id": instrument.instrument_id,
        "symbol": instrument.symbol,
        "name": instrument.display_name,
        "market": instrument.market,
        "asset_class": instrument.asset_class,
        "exchange": instrument.exchange,
        "currency": instrument.currency,
        "sector": instrument.sector,
        "industry": instrument.industry,
        "sub_industry": instrument.sub_industry,
    }


def _serialize_heatmap_cell(
    instrument: MarketInstrumentProfile,
    bar: StockBar,
) -> dict[str, object]:
    return {
        **_serialize_instrument(instrument),
        "last": bar.close,
        "change_percent": _change_percent(bar),
        "volume": bar.volume,
        "value": bar.value,
        "freshness": bar.freshness_status.value,
    }


def _serialize_instrument_row(
    instrument: MarketInstrumentProfile,
    bar: StockBar,
) -> dict[str, object]:
    return {
        **_serialize_heatmap_cell(instrument, bar),
        "source_id": bar.source_id,
        "as_of": bar.interval_start.isoformat(),
    }


def _change_percent(bar: StockBar) -> float:
    if bar.open == 0:
        return 0.0
    return round(((bar.close - bar.open) / bar.open) * 100, 2)


def _aggregate_stock_bars(
    bars: list[StockBar],
    timeframe: ChartTimeframe,
) -> list[StockBar]:
    if timeframe == "1h":
        return bars
    if timeframe == "4h":
        return [_combine_stock_bars(chunk) for chunk in _chunks(bars, 4)]
    return [_combine_stock_bars(bars)]


def _chunks(bars: list[StockBar], size: int) -> list[list[StockBar]]:
    return [bars[index:index + size] for index in range(0, len(bars), size)]


def _combine_stock_bars(bars: list[StockBar]) -> StockBar:
    first = bars[0]
    last = bars[-1]
    return StockBar(
        instrument_id=first.instrument_id,
        market=first.market,
        symbol=first.symbol,
        exchange=first.exchange,
        interval_start=first.interval_start,
        interval_end=last.interval_end,
        open=first.open,
        high=max(bar.high for bar in bars),
        low=min(bar.low for bar in bars),
        close=last.close,
        volume=sum(bar.volume for bar in bars),
        value=sum(bar.value for bar in bars),
        currency=first.currency,
        collected_at=last.collected_at,
        source_id=last.source_id,
        freshness_status=last.freshness_status,
    )


def _serialize_chart_bar(bar: StockBar) -> dict[str, object]:
    return {
        "time": bar.interval_start.isoformat(),
        "open": int(bar.open),
        "high": int(bar.high),
        "low": int(bar.low),
        "close": int(bar.close),
        "volume": bar.volume,
    }
