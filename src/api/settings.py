from dataclasses import dataclass
import os


class SettingsError(RuntimeError):
    """Raised when required runtime configuration is missing or invalid."""


@dataclass(frozen=True)
class Settings:
    admin_username: str
    admin_password: str
    session_secret: str
    session_cookie_name: str = "finmind_session"
    session_ttl_seconds: int = 8 * 60 * 60

    @classmethod
    def from_env(cls) -> "Settings":
        required = {
            "FINMIND_ADMIN_USERNAME": os.getenv("FINMIND_ADMIN_USERNAME", "").strip(),
            "FINMIND_ADMIN_PASSWORD": os.getenv("FINMIND_ADMIN_PASSWORD", ""),
            "FINMIND_SESSION_SECRET": os.getenv("FINMIND_SESSION_SECRET", ""),
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise SettingsError(f"Missing required admin configuration: {', '.join(missing)}")
        if len(required["FINMIND_SESSION_SECRET"]) < 16:
            raise SettingsError("FINMIND_SESSION_SECRET must be at least 16 characters")
        return cls(
            admin_username=required["FINMIND_ADMIN_USERNAME"],
            admin_password=required["FINMIND_ADMIN_PASSWORD"],
            session_secret=required["FINMIND_SESSION_SECRET"],
        )
