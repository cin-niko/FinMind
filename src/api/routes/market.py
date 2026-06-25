from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from api.dependencies import require_session
from api.platform.models import Session

router = APIRouter(prefix="/api", tags=["market"])


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
    if _should_lazy_fetch(instrument_id, timeframe):
        lazy_result = platform.ingestion_service.ensure_dataset_rows(
            dataset_id="vn_prices_daily",
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
