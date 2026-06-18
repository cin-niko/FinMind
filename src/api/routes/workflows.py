from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, status

from api.dependencies import require_session
from api.platform.models import Session
from api.platform.workflows.validation import WorkflowValidationError

router = APIRouter(prefix="/api", tags=["workflows"])


@router.get("/workflows")
def list_workflows(
    request: Request,
    _session: Annotated[Session, Depends(require_session)],
) -> list[dict[str, object]]:
    return request.app.state.platform.workflow_service.list_workflows()


@router.post("/workflows/{workflow_id}/run")
def run_workflow(
    workflow_id: str,
    payload: dict[str, Any],
    request: Request,
    session: Annotated[Session, Depends(require_session)],
) -> dict[str, object]:
    try:
        return request.app.state.platform.workflow_service.run_workflow(
            workflow_id=workflow_id,
            inputs=payload,
            requested_by=session.username,
        )
    except KeyError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except WorkflowValidationError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
