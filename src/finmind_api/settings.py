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
    vn_data_provider: str = "vnstock"
    vnstock_api_key: str = ""
    gold_data_provider: str = "twelvedata"
    twelve_data_api_key: str = ""
    dataflow_provider_timeout_seconds: float = 15.0
    database_url: str = ""
    stream_global_limit: int = 32
    stream_per_user_limit: int = 4
    sync_offload_limit: int = 8
    stream_heartbeat_seconds: float = 5.0

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
        vn_data_provider = _env(
            "FINMIND_VN_DATA_PROVIDER",
            dotenv,
            "vnstock",
        ).strip().lower()
        if vn_data_provider != "vnstock":
            raise SettingsError("FINMIND_VN_DATA_PROVIDER must be vnstock")
        gold_data_provider = _env(
            "FINMIND_GOLD_DATA_PROVIDER",
            dotenv,
            "twelvedata",
        ).strip().lower()
        if gold_data_provider != "twelvedata":
            raise SettingsError("FINMIND_GOLD_DATA_PROVIDER must be twelvedata")
        return cls(
            admin_username=required["FINMIND_ADMIN_USERNAME"],
            admin_password=required["FINMIND_ADMIN_PASSWORD"],
            session_secret=required["FINMIND_SESSION_SECRET"],
            vn_data_provider=vn_data_provider,
            vnstock_api_key=_env("FINMIND_VNSTOCK_API_KEY", dotenv, "").strip(),
            gold_data_provider=gold_data_provider,
            twelve_data_api_key=_env(
                "FINMIND_TWELVE_DATA_API_KEY",
                dotenv,
                "",
            ).strip(),
            dataflow_provider_timeout_seconds=float(
                _env("FINMIND_DATAFLOW_PROVIDER_TIMEOUT_SECONDS", dotenv, "15")
            ),
            database_url=_env("FINMIND_DATABASE_URL", dotenv, "").strip(),
            stream_global_limit=max(
                1,
                int(_env("FINMIND_STREAM_GLOBAL_LIMIT", dotenv, "32")),
            ),
            stream_per_user_limit=max(
                1,
                int(_env("FINMIND_STREAM_PER_USER_LIMIT", dotenv, "4")),
            ),
            sync_offload_limit=max(
                1,
                int(_env("FINMIND_SYNC_OFFLOAD_LIMIT", dotenv, "8")),
            ),
            stream_heartbeat_seconds=max(
                0.0,
                float(_env("FINMIND_STREAM_HEARTBEAT_SECONDS", dotenv, "5")),
            ),
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
