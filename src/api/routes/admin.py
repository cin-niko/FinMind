from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request

from api.dependencies import require_session
from api.platform.ingestion.planner import IngestionFetchRequest
from api.platform.ingestion.service import _serialize_job
from api.platform.models import Session

router = APIRouter(prefix="/api", tags=["admin"])


@router.get("/admin/ingestion")
def get_ingestion_status(
    request: Request,
    _session: Annotated[Session, Depends(require_session)],
) -> dict[str, object]:
    return request.app.state.platform.ingestion_service.status()


@router.post("/admin/fetch")
def trigger_manual_fetch(
    payload: dict[str, str],
    request: Request,
    _session: Annotated[Session, Depends(require_session)],
) -> dict[str, object]:
    fetch_request = IngestionFetchRequest.from_payload(payload)
    if fetch_request.mode == "historical":
        raise HTTPException(
            status_code=400,
            detail="Historical backfill must run via the independent backfill worker script.",
        )
    job = request.app.state.platform.ingestion_service.run_manual_request(
        fetch_request
    )
    return _serialize_job(job)


@router.post("/worker/ingestion/scheduled")
def trigger_scheduled_fetch(
    payload: dict[str, str],
    request: Request,
    _session: Annotated[Session, Depends(require_session)],
) -> dict[str, object]:
    fetch_request = IngestionFetchRequest.from_payload(payload)
    if fetch_request.mode == "historical":
        raise HTTPException(
            status_code=400,
            detail="Historical backfill must run via the independent backfill worker script.",
        )
    job = request.app.state.platform.ingestion_service.run_scheduled_request(
        fetch_request
    )
    return _serialize_job(job)


@router.get("/market-data/{dataset_id}")
def get_market_data(
    dataset_id: str,
    request: Request,
    _session: Annotated[Session, Depends(require_session)],
) -> dict[str, object]:
    return request.app.state.platform.ingestion_service.market_data(dataset_id)
