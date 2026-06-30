from dataclasses import dataclass
import os
from pathlib import Path


class SettingsError(RuntimeError):
    """Raised when required runtime configuration is missing or invalid."""


@dataclass(frozen=True)
class Settings:
    admin_username: str
    admin_password: str
    session_secret: str
    session_cookie_name: str = "finmind_session"
    session_ttl_seconds: int = 8 * 60 * 60
    us_alpha_vantage_api_key: str = ""
    sec_edgar_user_agent: str = ""
    vn_data_provider: str = "vnstock"
    vnstock_api_key: str = ""
    dataflow_provider_timeout_seconds: float = 15.0
    dataflow_allow_fallback: bool = True
    database_url: str = ""

    @classmethod
    def from_env(cls) -> "Settings":
        dotenv = _load_local_dotenv()
        required = {
            "FINMIND_ADMIN_USERNAME": _env(
                "FINMIND_ADMIN_USERNAME",
                dotenv,
            ).strip(),
            "FINMIND_ADMIN_PASSWORD": _env("FINMIND_ADMIN_PASSWORD", dotenv),
            "FINMIND_SESSION_SECRET": _env("FINMIND_SESSION_SECRET", dotenv),
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise SettingsError(f"Missing required admin configuration: {', '.join(missing)}")
        if len(required["FINMIND_SESSION_SECRET"]) < 16:
            raise SettingsError("FINMIND_SESSION_SECRET must be at least 16 characters")
        vn_data_provider = (
            _env("FINMIND_VN_DATA_PROVIDER", dotenv)
            or _env("VN_DATA_PROVIDER", dotenv)
            or "vnstock"
        ).strip().lower()
        if vn_data_provider not in {"vnstock", "offline"}:
            raise SettingsError("FINMIND_VN_DATA_PROVIDER must be one of: offline, vnstock")
        return cls(
            admin_username=required["FINMIND_ADMIN_USERNAME"],
            admin_password=required["FINMIND_ADMIN_PASSWORD"],
            session_secret=required["FINMIND_SESSION_SECRET"],
            us_alpha_vantage_api_key=_env(
                "FINMIND_US_ALPHA_VANTAGE_API_KEY",
                dotenv,
                "",
            ).strip(),
            sec_edgar_user_agent=_env(
                "FINMIND_SEC_EDGAR_USER_AGENT",
                dotenv,
                "",
            ).strip(),
            vn_data_provider=vn_data_provider,
            vnstock_api_key=_env("FINMIND_VNSTOCK_API_KEY", dotenv, "").strip(),
            dataflow_provider_timeout_seconds=float(
                _env("FINMIND_DATAFLOW_PROVIDER_TIMEOUT_SECONDS", dotenv, "15")
            ),
            dataflow_allow_fallback=_env(
                "FINMIND_DATAFLOW_ALLOW_FALLBACK",
                dotenv,
                "true",
            ).lower()
            not in {"0", "false", "no"},
            database_url=_env("FINMIND_DATABASE_URL", dotenv, "").strip(),
        )


def _env(name: str, dotenv: dict[str, str], default: str = "") -> str:
    value = os.getenv(name)
    if value is not None:
        return value
    return dotenv.get(name, default)


def _load_local_dotenv(path: Path = Path(".env")) -> dict[str, str]:
    if not path.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line.removeprefix("export ").lstrip()
        name, value = line.split("=", 1)
        name = name.strip()
        if not name:
            continue
        values[name] = _clean_dotenv_value(value)
    return values


def _clean_dotenv_value(value: str) -> str:
    cleaned = value.strip()
    if len(cleaned) >= 2 and cleaned[0] == cleaned[-1] and cleaned[0] in {"'", '"'}:
        return cleaned[1:-1]
    return cleaned
