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
    try:
        return request.app.state.platform.market_service.instrument_chart(
            instrument_id=instrument_id,
            timeframe=timeframe,
        )
    except KeyError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error
