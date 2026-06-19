from fastapi import APIRouter, HTTPException, Request, Response, status

from api.dependencies import get_session_from_request
from api.schemas import LoginRequest

router = APIRouter(prefix="/api", tags=["auth"])


@router.get("/session")
def get_session(request: Request) -> dict[str, object]:
    session = get_session_from_request(request)
    if session is None:
        return {"authenticated": False}
    return {"authenticated": True, "role": session.role}


@router.post("/login")
def login(payload: LoginRequest, request: Request, response: Response) -> dict[str, object]:
    settings = request.app.state.settings
    session_service = request.app.state.session_service
    user = session_service.authenticate(payload.username, payload.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    session = session_service.create_session(user)
    response.set_cookie(
        key=settings.session_cookie_name,
        value=session.session_id,
        httponly=True,
        samesite="lax",
        max_age=settings.session_ttl_seconds,
    )
    return {"authenticated": True, "role": user.role}


@router.post("/logout")
def logout(request: Request, response: Response) -> dict[str, object]:
    settings = request.app.state.settings
    session_service = request.app.state.session_service
    session_service.delete_session(request.cookies.get(settings.session_cookie_name))
    response.delete_cookie(settings.session_cookie_name)
    return {"authenticated": False}
