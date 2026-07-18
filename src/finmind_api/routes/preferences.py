from typing import Annotated

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from finmind_agents.models import Session
from finmind_api.dependencies import require_session
from finmind_api.preferences_store import LanguageSelection

router = APIRouter(prefix="/api/preferences", tags=["preferences"])


class LanguagePreferenceRequest(BaseModel):
    selection: LanguageSelection


@router.get("/language")
def get_language_preference(
    request: Request,
    session: Annotated[Session, Depends(require_session)],
) -> dict[str, LanguageSelection]:
    selection = request.app.state.language_preferences.get(session.username)
    return {"selection": selection}


@router.put("/language")
def save_language_preference(
    payload: LanguagePreferenceRequest,
    request: Request,
    session: Annotated[Session, Depends(require_session)],
) -> dict[str, LanguageSelection]:
    selection = request.app.state.language_preferences.save(
        session.username,
        payload.selection,
    )
    return {"selection": selection}
