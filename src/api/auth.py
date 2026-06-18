from datetime import timedelta
import secrets

from api.platform.models import AdminUser, Session, utc_now
from api.settings import Settings


class SessionService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._sessions: dict[str, Session] = {}
        self.admin_user = AdminUser(username=settings.admin_username)

    def authenticate(self, username: str, password: str) -> AdminUser | None:
        if username == self._settings.admin_username and password == self._settings.admin_password:
            return self.admin_user
        return None

    def create_session(self, user: AdminUser) -> Session:
        now = utc_now()
        session = Session(
            session_id=secrets.token_urlsafe(32),
            username=user.username,
            role=user.role,
            created_at=now,
            expires_at=now + timedelta(seconds=self._settings.session_ttl_seconds),
        )
        self._sessions[session.session_id] = session
        return session

    def get_session(self, session_id: str | None) -> Session | None:
        if not session_id:
            return None
        session = self._sessions.get(session_id)
        if session is None:
            return None
        if session.expires_at <= utc_now():
            self._sessions.pop(session_id, None)
            return None
        return session

    def delete_session(self, session_id: str | None) -> None:
        if session_id:
            self._sessions.pop(session_id, None)
