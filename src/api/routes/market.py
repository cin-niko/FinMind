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


@router.get("/market/overview")
def get_market_overview(
    request: Request,
    _session: Annotated[Session, Depends(require_session)],
    market: str = Query(default="VN"),
    collection_id: str | None = None,
    watchlist_id: str | None = None,
) -> dict[str, object]:
    try:
        return request.app.state.platform.market_service.overview(
            market=market,
            collection_id=collection_id,
            watchlist_id=watchlist_id,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error


@router.get("/market/instruments/{instrument_id}/chart")
def get_instrument_chart(
    instrument_id: str,
    request: Request,
    _session: Annotated[Session, Depends(require_session)],
    timeframe: str = Query(default="1h"),
) -> dict[str, object]:
    platform = request.app.state.platform
    lazy_payload: dict[str, object] | None = None
    lazy_succeeded = False
    if _should_lazy_fetch(instrument_id, timeframe):
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
        lazy_succeeded = lazy_result.status in {
            "success",
            "already_present",
        }
    if lazy_succeeded and lazy_payload is not None:
        canonical = _render_vn_daily_chart(
            store=platform.ingestion_service.store,
            instrument_id=instrument_id,
            lazy_payload=lazy_payload,
        )
        if canonical is not None:
            return canonical
    try:
        chart = platform.market_service.instrument_chart(
            instrument_id=instrument_id,
            timeframe=timeframe,
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


def _should_lazy_fetch(instrument_id: str, timeframe: str) -> bool:
    return instrument_id.startswith("vn_stock:") and timeframe == "1d"


def _render_vn_daily_chart(
    store: TimeSeriesStore,
    instrument_id: str,
    lazy_payload: dict[str, object],
) -> dict[str, object] | None:
    rows = store.list_dataset_for_instrument(
        _VN_DAILY_DATASET, instrument_id
    )
    if not rows:
        return None
    instrument = store.read_instrument(instrument_id)
    if instrument is None:
        return None
    freshness_entries = calculate_dataset_freshness(
        dataset_ids=[_VN_DAILY_DATASET],
        list_dataset=lambda _dataset_id: rows,
        list_jobs=store.list_jobs,
    )
    freshness_status = str(freshness_entries[0]["status"])
    latest_trade_date = str(rows[-1].payload.get("trade_date", ""))
    records = [_serialize_canonical_bar(record) for record in rows]
    return {
        "instrument": _serialize_instrument_metadata(instrument),
        "timeframe": "1d",
        "freshness": {
            "status": freshness_status,
            "as_of": latest_trade_date,
        },
        "records": records,
        "table": records,
        "lazy_fetch": lazy_payload,
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
