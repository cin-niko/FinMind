from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from finmind_api.dependencies import require_session
from finmind_agents.models import Session

router = APIRouter(prefix="/api", tags=["runs"])


@router.get("/runs")
def list_runs(
    request: Request,
    _session: Annotated[Session, Depends(require_session)],
) -> list[dict[str, object]]:
    return request.app.state.platform.workflow_service.list_runs()


@router.get("/runs/{run_id}")
def get_run(
    run_id: str,
    request: Request,
    _session: Annotated[Session, Depends(require_session)],
) -> dict[str, object]:
    run = request.app.state.platform.workflow_service.get_run(run_id)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )
    return run
