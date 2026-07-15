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


@router.post("/workflows/{workflow_id}/conversations")
async def start_workflow_conversation(
    workflow_id: str,
    payload: dict[str, Any],
    request: Request,
    session: Annotated[Session, Depends(require_session)],
) -> StreamingResponse:
    language = payload.pop("language", "en")
    if language not in {"en", "vi"}:
        raise HTTPException(status_code=422, detail="language must be en or vi")
    try:
        conversation = request.app.state.platform.conversation_service.start(
            workflow_id, payload, session.username, language
        )
        heartbeat_seconds = float(getattr(request.app.state, "stream_heartbeat_seconds", 5.0))
        response = StreamingResponse(
            _conversation_event_source(
                request.app.state.platform.conversation_service.events(conversation.conversation_id),
                heartbeat_seconds,
            ),
            media_type="text/event-stream",
        )
        response.headers["Cache-Control"] = "no-cache"
        response.headers["X-Accel-Buffering"] = "no"
        return response
    except KeyError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except WorkflowValidationError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except AgentOrchestratorError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error


async def _conversation_event_source(
    event_source: object,
    heartbeat_seconds: float = 5.0,
) -> object:
    async for frame in with_heartbeats(sse_event_stream(event_source), heartbeat_seconds):
        yield frame
