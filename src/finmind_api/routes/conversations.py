from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from finmind_agents.models import Session
from finmind_api.dependencies import require_session

router = APIRouter(prefix="/api", tags=["conversations"])


@router.get("/conversations")
def list_conversations(
    request: Request,
    session: Annotated[Session, Depends(require_session)],
) -> list[dict[str, object]]:
    return request.app.state.platform.conversation_service.list(session.username)


@router.get("/conversations/{conversation_id}")
def get_conversation(
    conversation_id: str,
    request: Request,
    session: Annotated[Session, Depends(require_session)],
) -> dict[str, object]:
    conversation = request.app.state.platform.conversation_service.get(conversation_id, session.username)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: str,
    request: Request,
    session: Annotated[Session, Depends(require_session)],
) -> None:
    if not request.app.state.platform.conversation_service.delete(conversation_id, session.username):
        raise HTTPException(
            status_code=409,
            detail="Conversation was not found or is still running",
        )
