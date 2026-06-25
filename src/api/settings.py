from dataclasses import dataclass
import os


class SettingsError(RuntimeError):
    """Raised when required runtime configuration is missing or invalid."""


@dataclass(frozen=True)
class Settings:
    admin_username: str
    admin_password: str
    session_secret: str
    database_url: str | None = None
    vn_provider: str = "mock"
    us_provider: str = "mock"
    xauusd_provider: str = "mock"
    xauusd_daily_fallback: str = "alpha_vantage"
    sjc_provider: str = "mock"
    vnstock_api_key: str | None = None
    alpha_vantage_api_key: str | None = None
    provider_timeout_seconds: float = 15.0
    session_cookie_name: str = "finmind_session"
    session_ttl_seconds: int = 8 * 60 * 60
    roadmap_markets_enabled: bool = False

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
        provider_config = {
            "FINMIND_VN_PROVIDER": os.getenv("FINMIND_VN_PROVIDER", "mock")
            .strip()
            .lower(),
            "FINMIND_US_PROVIDER": os.getenv("FINMIND_US_PROVIDER", "mock")
            .strip()
            .lower(),
            "FINMIND_XAUUSD_PROVIDER": os.getenv("FINMIND_XAUUSD_PROVIDER", "mock")
            .strip()
            .lower(),
            "FINMIND_XAUUSD_DAILY_FALLBACK": os.getenv(
                "FINMIND_XAUUSD_DAILY_FALLBACK",
                "alpha_vantage",
            )
            .strip()
            .lower(),
            "FINMIND_SJC_PROVIDER": os.getenv("FINMIND_SJC_PROVIDER", "mock")
            .strip()
            .lower(),
        }
        supported_provider_values = {
            "FINMIND_VN_PROVIDER": {"mock", "vnstock"},
            "FINMIND_US_PROVIDER": {"mock", "yfinance"},
            "FINMIND_XAUUSD_PROVIDER": {"mock", "yfinance"},
            "FINMIND_XAUUSD_DAILY_FALLBACK": {"alpha_vantage"},
            "FINMIND_SJC_PROVIDER": {"mock", "sjc_official"},
        }
        unsupported_provider_config = [
            name
            for name, supported_values in supported_provider_values.items()
            if provider_config[name] not in supported_values
        ]
        if unsupported_provider_config:
            raise SettingsError(
                "Unsupported provider configuration: "
                + ", ".join(unsupported_provider_config)
            )
        credentials = {
            "FINMIND_VNSTOCK_API_KEY": os.getenv("FINMIND_VNSTOCK_API_KEY", "").strip(),
            "FINMIND_ALPHA_VANTAGE_API_KEY": os.getenv(
                "FINMIND_ALPHA_VANTAGE_API_KEY",
                "",
            ).strip(),
        }
        if provider_config["FINMIND_VN_PROVIDER"] == "vnstock" and not credentials[
            "FINMIND_VNSTOCK_API_KEY"
        ]:
            raise SettingsError("FINMIND_VNSTOCK_API_KEY is required for vnstock provider")
        timeout_raw = os.getenv("FINMIND_PROVIDER_TIMEOUT_SECONDS", "15").strip()
        try:
            provider_timeout_seconds = float(timeout_raw)
        except ValueError as exc:
            raise SettingsError("FINMIND_PROVIDER_TIMEOUT_SECONDS must be numeric") from exc
        if provider_timeout_seconds <= 0:
            raise SettingsError("FINMIND_PROVIDER_TIMEOUT_SECONDS must be positive")
        roadmap_raw = (
            os.getenv("FINMIND_ROADMAP_MARKETS", "").strip().lower()
        )
        truthy = {"true", "1"}
        falsy = {"", "false", "0"}
        if roadmap_raw in truthy:
            roadmap_markets_enabled = True
        elif roadmap_raw in falsy:
            roadmap_markets_enabled = False
        else:
            raise SettingsError(
                "FINMIND_ROADMAP_MARKETS must be true/false/1/0"
            )
        return cls(
            admin_username=required["FINMIND_ADMIN_USERNAME"],
            admin_password=required["FINMIND_ADMIN_PASSWORD"],
            session_secret=required["FINMIND_SESSION_SECRET"],
            database_url=os.getenv("FINMIND_DATABASE_URL", "").strip() or None,
            vn_provider=provider_config["FINMIND_VN_PROVIDER"],
            us_provider=provider_config["FINMIND_US_PROVIDER"],
            xauusd_provider=provider_config["FINMIND_XAUUSD_PROVIDER"],
            xauusd_daily_fallback=provider_config[
                "FINMIND_XAUUSD_DAILY_FALLBACK"
            ],
            sjc_provider=provider_config["FINMIND_SJC_PROVIDER"],
            vnstock_api_key=credentials["FINMIND_VNSTOCK_API_KEY"] or None,
            alpha_vantage_api_key=credentials["FINMIND_ALPHA_VANTAGE_API_KEY"] or None,
            provider_timeout_seconds=provider_timeout_seconds,
            roadmap_markets_enabled=roadmap_markets_enabled,
        )
