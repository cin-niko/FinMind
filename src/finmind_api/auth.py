from datetime import timedelta
import hashlib
import hmac
import secrets

from finmind_agents.models import AdminUser, Session, utc_now
from finmind_api.settings import Settings


class SessionService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._sessions: dict[str, Session] = {}
        self.admin_user = AdminUser(username=settings.admin_username)

    def authenticate(self, username: str, password: str) -> AdminUser | None:
        if (
            username == self._settings.admin_username
            and password == self._settings.admin_password
        ):
            return self.admin_user
        return None

    def create_session(self, user: AdminUser) -> Session:
        now = utc_now()
        session_id = secrets.token_urlsafe(32)
        session = Session(
            session_id=self._sign_session_id(session_id),
            username=user.username,
            role=user.role,
            created_at=now,
            expires_at=now
            + timedelta(seconds=self._settings.session_ttl_seconds),
        )
        self._sessions[session_id] = session
        return session

    def get_session(self, session_token: str | None) -> Session | None:
        session_id = self._verify_session_token(session_token)
        if session_id is None:
            return None
        session = self._sessions.get(session_id)
        if session is None:
            return None
        if session.expires_at <= utc_now():
            self._sessions.pop(session_id, None)
            return None
        return session

    def delete_session(self, session_token: str | None) -> None:
        session_id = self._verify_session_token(session_token)
        if session_id is not None:
            self._sessions.pop(session_id, None)

    def _sign_session_id(self, session_id: str) -> str:
        signature = hmac.new(
            self._settings.session_secret.encode(),
            session_id.encode(),
            hashlib.sha256,
        ).hexdigest()
        return f"{session_id}.{signature}"

    def _verify_session_token(self, session_token: str | None) -> str | None:
        if not session_token:
            return None
        session_id, separator, signature = session_token.partition(".")
        if not separator or not session_id or not signature:
            return None
        expected_signature = hmac.new(
            self._settings.session_secret.encode(),
            session_id.encode(),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(signature, expected_signature):
            return None
        return session_id
