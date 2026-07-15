from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from finmind_agents.models import Session
from finmind_api.dependencies import require_session

router = APIRouter(prefix="/api/preferences", tags=["preferences"])


class LanguagePreferenceRequest(BaseModel):
    selection: str


@router.get("/language")
def get_language_preference(
    request: Request,
    session: Annotated[Session, Depends(require_session)],
) -> dict[str, str]:
    store = request.app.state.platform.workflow_service.records
    selection = store.get_language_preference(session.username)
    if selection is None:
        selection = store.save_language_preference(session.username, "auto")
    return {"selection": selection}


@router.put("/language")
def save_language_preference(
    payload: LanguagePreferenceRequest,
    request: Request,
    session: Annotated[Session, Depends(require_session)],
) -> dict[str, str]:
    if payload.selection not in {"auto", "en", "vi"}:
        raise HTTPException(status_code=422, detail="selection must be auto, en, or vi")
    store = request.app.state.platform.workflow_service.records
    return {"selection": store.save_language_preference(session.username, payload.selection)}
