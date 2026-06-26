from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from api.dependencies import require_session
from api.platform.freshness import calculate_dataset_freshness
from api.platform.ingestion.sources import TimeSeriesRecord
from api.platform.ingestion.store_writer import (
    InstrumentMetadata,
    TimeSeriesStore,
)
from api.platform.models import Session

router = APIRouter(prefix="/api", tags=["market"])

_VN_DAILY_DATASET = "vn_prices_daily"
_VN100_COLLECTION_ID = "VN100"
_INDEX_SYMBOLS = ("VNINDEX", "VN100", "VN30", "HNXINDEX", "UPCOM")


@router.get("/market/overview")
def get_market_overview(
    request: Request,
    _session: Annotated[Session, Depends(require_session)],
    market: str = Query(default="VN"),
    collection_id: str | None = None,
    watchlist_id: str | None = None,
) -> dict[str, object]:
    try:
        selected_market = _normalize_market(market)
        if selected_market == "VN":
            return _render_vn_overview(
                request.app.state.platform.ingestion_service.store,
                collection_id=collection_id,
            )
        return request.app.state.platform.market_service.overview(
            market=selected_market,
            collection_id=collection_id,
            watchlist_id=watchlist_id,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error


def _normalize_market(market: str) -> str:
    if market != "VN":
        raise ValueError("V1 market overview supports VN only")
    return market


def _render_vn_overview(
    store: TimeSeriesStore,
    collection_id: str | None,
) -> dict[str, object]:
    instruments = [
        instrument
        for instrument in store.list_instruments()
        if instrument.market == "VN_STOCK"
        and instrument.asset_class == "stock"
        and instrument.status == "active"
        and store.is_in_collection(_VN100_COLLECTION_ID, instrument.instrument_id)
    ]
    records = store.list_dataset(_VN_DAILY_DATASET)
    latest_by_instrument = _latest_daily_records_by_instrument(records)
    previous_by_instrument = _previous_daily_records_by_instrument(records)
    overview_rows = [
        _serialize_overview_instrument(
            instrument,
            latest_by_instrument[instrument.instrument_id],
            previous_by_instrument.get(instrument.instrument_id),
        )
        for instrument in instruments
        if instrument.instrument_id in latest_by_instrument
    ]
    heatmap_member_ids = _heatmap_member_ids(
        store=store,
        collection_id=collection_id,
        fallback_ids={instrument.instrument_id for instrument in instruments},
    )
    heatmap_rows = [
        row for row in overview_rows if row["id"] in heatmap_member_ids
    ]
    return {
        "available_markets": ["VN"],
        "selected_market": "VN",
        "watchlists": [
            {
                "id": "watchlist:default-vn",
                "name": "VN Watchlist",
                "type": "watchlist",
            }
        ],
        "collections": _vn_collections(instruments),
        "index_charts": _derived_index_charts(records),
        "heatmap": heatmap_rows,
        "instrument_rows": overview_rows[:10],
        "meta": {"roadmap_markets_enabled": False},
    }


def _latest_daily_records_by_instrument(
    records: list[TimeSeriesRecord],
) -> dict[str, TimeSeriesRecord]:
    latest: dict[str, TimeSeriesRecord] = {}
    for record in records:
        current = latest.get(record.instrument_id)
        if current is None or record.market_time > current.market_time:
            latest[record.instrument_id] = record
    return latest


def _previous_daily_records_by_instrument(
    records: list[TimeSeriesRecord],
) -> dict[str, TimeSeriesRecord]:
    ordered: dict[str, list[TimeSeriesRecord]] = {}
    for record in records:
        ordered.setdefault(record.instrument_id, []).append(record)
    previous: dict[str, TimeSeriesRecord] = {}
    for instrument_id, instrument_records in ordered.items():
        instrument_records.sort(key=lambda item: item.market_time)
        if len(instrument_records) >= 2:
            previous[instrument_id] = instrument_records[-2]
    return previous


def _heatmap_member_ids(
    store: TimeSeriesStore,
    collection_id: str | None,
    fallback_ids: set[str],
) -> set[str]:
    if not collection_id or collection_id in {"all", "vn100"}:
        return fallback_ids
    member_ids = store.list_collection_instrument_ids(collection_id)
    if member_ids:
        return member_ids
    return fallback_ids


def _serialize_overview_instrument(
    instrument: InstrumentMetadata,
    latest_record: TimeSeriesRecord,
    previous_record: TimeSeriesRecord | None,
) -> dict[str, object]:
    latest_close = _coerce_price(latest_record.payload.get("close"))
    previous_close = (
        _coerce_price(previous_record.payload.get("close"))
        if previous_record is not None
        else latest_close
    )
    change_percent = (
        ((latest_close - previous_close) / previous_close) * 100
        if previous_close
        else 0
    )
    volume = _coerce_volume(latest_record.payload.get("volume"))
    return {
        "id": instrument.instrument_id,
        "symbol": instrument.symbol,
        "name": instrument.display_name,
        "market": "VN",
        "asset_class": instrument.asset_class,
        "exchange": instrument.exchange,
        "currency": instrument.currency,
        "sector": instrument.sector,
        "industry": instrument.industry,
        "sub_industry": instrument.sub_industry,
        "last": latest_close,
        "change_percent": round(change_percent, 2),
        "volume": volume,
        "value": float(latest_close) * volume,
        "freshness": str(
            latest_record.payload.get("freshness_status", "fresh")
        ),
        "source_id": latest_record.source_id,
        "as_of": str(latest_record.payload.get("trade_date", "")),
    }


def _vn_collections(
    instruments: list[InstrumentMetadata],
) -> list[dict[str, object]]:
    base_collections = [
        {"id": "all", "name": "All", "type": "index"},
        {"id": "vn30", "name": "VN30", "type": "index"},
        {"id": "vn100", "name": "VN100", "type": "index"},
    ]
    sector_collections = [
        {"id": _sector_collection_id(sector), "name": sector, "type": "sector"}
        for sector in sorted(
            {
                instrument.sector
                for instrument in instruments
                if instrument.sector
            }
        )
    ]
    return [*base_collections, *sector_collections]


def _sector_collection_id(sector: str) -> str:
    return "sector:" + sector.lower().replace("&", "and").replace(" ", "-")


def _derived_index_charts(
    records: list[TimeSeriesRecord],
) -> list[dict[str, object]]:
    by_date: dict[str, list[float]] = {}
    for record in records:
        trade_date = str(record.payload.get("trade_date", ""))
        if not trade_date:
            continue
        by_date.setdefault(trade_date, []).append(
            float(_coerce_price(record.payload.get("close")))
        )
    series = [
        {
            "time": trade_date,
            "value": round(sum(values) / len(values), 2),
        }
        for trade_date, values in sorted(by_date.items())
        if values
    ]
    if not series:
        series = [{"time": "", "value": 0}]
    latest = series[-1]
    previous = series[-2] if len(series) > 1 else latest
    change_percent = (
        round(
            ((latest["value"] - previous["value"]) / previous["value"])
            * 100,
            2,
        )
        if previous["value"]
        else 0
    )
    return [
        {
            "symbol": symbol,
            "name": symbol,
            "last": latest["value"],
            "change_percent": change_percent,
            "series": series,
        }
        for symbol in _INDEX_SYMBOLS
    ]


@router.get("/market/instruments/{instrument_id}/chart")
def get_instrument_chart(
    instrument_id: str,
    request: Request,
    _session: Annotated[Session, Depends(require_session)],
    timeframe: str = Query(default="1h"),
) -> dict[str, object]:
    try:
        selected_timeframe = _normalize_timeframe(timeframe)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error
    platform = request.app.state.platform
    lazy_payload: dict[str, object] | None = None
    if _is_vn_stock_chart(instrument_id):
        lazy_result = platform.ingestion_service.ensure_dataset_rows(
            dataset_id=_VN_DAILY_DATASET,
            instrument_id=instrument_id,
        )
        lazy_payload = lazy_result.to_dict()
        if lazy_result.status == "out_of_scope":
            return {
                "instrument": {"id": instrument_id},
                "timeframe": timeframe,
                "records": [],
                "table": [],
                "lazy_fetch": lazy_payload,
            }
    if _is_vn_stock_chart(instrument_id):
        return _render_vn_chart(
            store=platform.ingestion_service.store,
            instrument_id=instrument_id,
            timeframe=selected_timeframe,
            lazy_payload=lazy_payload,
        )
    try:
        chart = platform.market_service.instrument_chart(
            instrument_id=instrument_id,
            timeframe=selected_timeframe,
        )
    except KeyError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(error)
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error
    if lazy_payload is not None:
        chart["lazy_fetch"] = lazy_payload
    return chart


def _is_vn_stock_chart(instrument_id: str) -> bool:
    return instrument_id.startswith("vn_stock:")


def _render_vn_chart(
    store: TimeSeriesStore,
    instrument_id: str,
    timeframe: str,
    lazy_payload: dict[str, object] | None,
) -> dict[str, object]:
    selected_timeframe = _normalize_timeframe(timeframe)
    dataset_id = _dataset_for_vn_timeframe(selected_timeframe)
    rows = store.list_dataset_for_instrument(dataset_id, instrument_id)
    instrument = store.read_instrument(instrument_id)
    freshness_entries = calculate_dataset_freshness(
        dataset_ids=[dataset_id],
        list_dataset=lambda _dataset_id: rows,
        list_jobs=store.list_jobs,
    )
    freshness_status = str(freshness_entries[0]["status"])
    records = [_serialize_vn_bar(record, dataset_id) for record in rows]
    payload = {
        "instrument": (
            _serialize_instrument_metadata(instrument)
            if instrument is not None
            else {"id": instrument_id}
        ),
        "timeframe": selected_timeframe,
        "freshness": {
            "status": freshness_status,
            "as_of": _latest_as_of(rows, dataset_id),
        },
        "records": records,
        "table": records,
    }
    if lazy_payload is not None:
        payload["lazy_fetch"] = lazy_payload
    return payload


def _normalize_timeframe(timeframe: str) -> str:
    if timeframe not in {"1h", "4h", "1d", "1M"}:
        raise ValueError("Unsupported chart timeframe")
    return timeframe


def _dataset_for_vn_timeframe(timeframe: str) -> str:
    if timeframe == "1h":
        return "vn_prices"
    return _VN_DAILY_DATASET


def _latest_as_of(
    rows: list[TimeSeriesRecord], dataset_id: str
) -> str | None:
    if not rows:
        return None
    if dataset_id == _VN_DAILY_DATASET:
        return str(rows[-1].payload.get("trade_date", ""))
    return rows[-1].market_time.isoformat()


def _serialize_vn_bar(
    record: TimeSeriesRecord,
    dataset_id: str,
) -> dict[str, object]:
    if dataset_id == _VN_DAILY_DATASET:
        return _serialize_canonical_bar(record)
    payload = record.payload
    return {
        "time": str(
            payload.get(
                "interval_start",
                record.market_time.isoformat(),
            )
        ),
        "open": _coerce_price(payload.get("open")),
        "high": _coerce_price(payload.get("high")),
        "low": _coerce_price(payload.get("low")),
        "close": _coerce_price(payload.get("close")),
        "volume": _coerce_volume(payload.get("volume")),
    }


def _serialize_canonical_bar(
    record: TimeSeriesRecord,
) -> dict[str, object]:
    payload = record.payload
    return {
        "time": str(payload.get("trade_date", "")),
        "open": _coerce_price(payload.get("open")),
        "high": _coerce_price(payload.get("high")),
        "low": _coerce_price(payload.get("low")),
        "close": _coerce_price(payload.get("close")),
        "volume": _coerce_volume(payload.get("volume")),
    }


def _coerce_price(value: object) -> float | int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return value if value % 1 else int(value)
    if value is None:
        return 0
    return float(value)  # type: ignore[arg-type]


def _coerce_volume(value: object) -> int:
    if value is None:
        return 0
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    return int(float(value))  # type: ignore[arg-type]


def _serialize_instrument_metadata(
    instrument: InstrumentMetadata,
) -> dict[str, object]:
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
