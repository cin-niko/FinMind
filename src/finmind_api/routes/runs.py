from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from pydantic import BaseModel

from finmind_api.dependencies import require_session
from finmind_agents.models import Session
from finmind_api.schemas import CitationResponse

router = APIRouter(prefix="/api", tags=["runs"])


class RenameRunRequest(BaseModel):
    title: str


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


@router.get("/runs/{run_id}/citations", response_model=list[CitationResponse])
def list_run_citations(
    run_id: str,
    request: Request,
    _session: Annotated[Session, Depends(require_session)],
) -> list[dict[str, object]]:
    run = request.app.state.platform.workflow_service.get_run(run_id)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )
    return request.app.state.platform.workflow_service.list_citations(run_id)


@router.delete("/runs/{run_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_run(
    run_id: str,
    request: Request,
    _session: Annotated[Session, Depends(require_session)],
) -> None:
    deleted = request.app.state.platform.workflow_service.delete_run(run_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )


@router.patch("/runs/{run_id}")
def rename_run(
    run_id: str,
    payload: Annotated[RenameRunRequest, Body()],
    request: Request,
    _session: Annotated[Session, Depends(require_session)],
) -> dict[str, object]:
    title = payload.title.strip()
    if not title:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="title must not be empty",
        )
    run = request.app.state.platform.workflow_service.rename_run(run_id, title)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )
    return run
