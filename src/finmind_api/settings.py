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
    us_alpha_vantage_api_key: str = ""
    sec_edgar_user_agent: str = ""
    vn_data_provider: str = "vnstock"
    vnstock_api_key: str = ""
    dataflow_provider_timeout_seconds: float = 15.0
    dataflow_allow_fallback: bool = True
    database_url: str = ""

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
        vn_data_provider = (
            os.getenv("FINMIND_VN_DATA_PROVIDER")
            or os.getenv("VN_DATA_PROVIDER")
            or "vnstock"
        ).strip().lower()
        if vn_data_provider not in {"vnstock", "offline"}:
            raise SettingsError("FINMIND_VN_DATA_PROVIDER must be one of: offline, vnstock")
        return cls(
            admin_username=required["FINMIND_ADMIN_USERNAME"],
            admin_password=required["FINMIND_ADMIN_PASSWORD"],
            session_secret=required["FINMIND_SESSION_SECRET"],
            us_alpha_vantage_api_key=os.getenv(
                "FINMIND_US_ALPHA_VANTAGE_API_KEY",
                "",
            ).strip(),
            sec_edgar_user_agent=os.getenv(
                "FINMIND_SEC_EDGAR_USER_AGENT",
                "",
            ).strip(),
            vn_data_provider=vn_data_provider,
            vnstock_api_key=os.getenv("FINMIND_VNSTOCK_API_KEY", "").strip(),
            dataflow_provider_timeout_seconds=float(
                os.getenv("FINMIND_DATAFLOW_PROVIDER_TIMEOUT_SECONDS", "15")
            ),
            dataflow_allow_fallback=os.getenv(
                "FINMIND_DATAFLOW_ALLOW_FALLBACK",
                "true",
            ).lower()
            not in {"0", "false", "no"},
            database_url=os.getenv("FINMIND_DATABASE_URL", "").strip(),
        )
