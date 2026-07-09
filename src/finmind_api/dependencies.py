from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

from finmind_agents.models import Session


def get_session_from_request(request: Request) -> Session | None:
    settings = request.app.state.settings
    session_service = request.app.state.session_service
    session_id = request.cookies.get(settings.session_cookie_name)
    return session_service.get_session(session_id)


def require_session(
    session: Annotated[Session | None, Depends(get_session_from_request)],
) -> Session:
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return session
