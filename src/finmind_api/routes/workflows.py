from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse

from finmind_agents.models import Session
from finmind_agents.runtime.service import AgentOrchestratorError
from finmind_agents.workflows.validation import WorkflowValidationError
from finmind_api.dependencies import require_session
from finmind_api.streaming import sse_event_stream, with_heartbeats

router = APIRouter(prefix="/api", tags=["workflows"])


@router.get("/workflows")
def list_workflows(
    request: Request,
    _session: Annotated[Session, Depends(require_session)],
) -> list[dict[str, object]]:
    return request.app.state.platform.workflow_service.list_workflows()


@router.post("/workflows/{workflow_id}/runs")
async def run_workflow(
    workflow_id: str,
    payload: dict[str, Any],
    request: Request,
    session: Annotated[Session, Depends(require_session)],
) -> StreamingResponse:
    lease = await request.app.state.stream_limiter.acquire(session.username)
    if lease is None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": {
                    "code": "concurrency_limit_exceeded",
                    "message": (
                        "Too many active workflow or chatflow streams. "
                        "Retry after a short delay."
                    ),
                    "retry_after_seconds": 5,
                }
            },
        )
    try:
        request.app.state.platform.workflow_service.prepare_workflow_run(
            workflow_id=workflow_id,
            inputs=payload,
        )
        event_source = request.app.state.platform.workflow_service.stream_workflow(
            workflow_id=workflow_id,
            inputs=payload,
            requested_by=session.username,
        )
        heartbeat_seconds = float(getattr(request.app.state, "stream_heartbeat_seconds", 5.0))
        response = StreamingResponse(
            _guarded_event_source(
                request,
                event_source,
                request.app.state.stream_limiter,
                lease,
                heartbeat_seconds,
            ),
            media_type="text/event-stream",
        )
        response.headers["Cache-Control"] = "no-cache"
        response.headers["X-Accel-Buffering"] = "no"
        return response
    except KeyError as error:
        await request.app.state.stream_limiter.release(lease)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except WorkflowValidationError as error:
        await request.app.state.stream_limiter.release(lease)
        raise HTTPException(status_code=422, detail=str(error)) from error
    except AgentOrchestratorError as error:
        await request.app.state.stream_limiter.release(lease)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error


async def _guarded_event_source(
    request: Request,
    event_source: object,
    limiter: object,
    lease: object,
    heartbeat_seconds: float = 5.0,
) -> object:
    try:
        async for frame in with_heartbeats(
            sse_event_stream(event_source),
            heartbeat_seconds,
        ):
            if await request.is_disconnected():
                break
            yield frame
    finally:
        await limiter.release(lease)
