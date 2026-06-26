from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from api.app import create_app
from api.settings import SettingsError


@pytest.fixture
def admin_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FINMIND_ADMIN_USERNAME", "analyst")
    monkeypatch.setenv("FINMIND_ADMIN_PASSWORD", "secret-pass")
    monkeypatch.setenv("FINMIND_SESSION_SECRET", "session-secret-with-length")


@pytest.fixture
def client(admin_env: None) -> Iterator[TestClient]:
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


def test_app_fails_closed_when_admin_config_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("FINMIND_ADMIN_USERNAME", raising=False)
    monkeypatch.delenv("FINMIND_ADMIN_PASSWORD", raising=False)
    monkeypatch.delenv("FINMIND_SESSION_SECRET", raising=False)

    with pytest.raises(SettingsError, match="FINMIND_ADMIN_USERNAME"):
        create_app()


def test_protected_workflow_routes_require_login(client: TestClient) -> None:
    workflows_response = client.get("/api/workflows")
    runs_response = client.get("/api/runs")
    market_response = client.get("/api/market/overview?market=VN")
    chart_response = client.get(
        "/api/market/instruments/vn_stock:VCB/chart?timeframe=4h",
    )
    run_response = client.post(
        "/api/workflows/daily-market-brief/run",
        json={"market": "VN_STOCK"},
    )

    assert workflows_response.status_code == 401
    assert workflows_response.json()["detail"] == "Authentication required"
    assert runs_response.status_code == 401
    assert market_response.status_code == 401
    assert chart_response.status_code == 401
    assert run_response.status_code == 401


def test_admin_can_login_check_session_and_logout(client: TestClient) -> None:
    assert client.get("/api/session").json() == {"authenticated": False}

    login_response = client.post(
        "/api/login",
        json={"username": "analyst", "password": "secret-pass"},
    )

    assert login_response.status_code == 200
    assert login_response.json() == {"authenticated": True, "role": "admin"}
    assert "finmind_session" in login_response.cookies
    assert client.get("/api/session").json() == {
        "authenticated": True,
        "role": "admin",
    }

    logout_response = client.post("/api/logout")

    assert logout_response.status_code == 200
    assert logout_response.json() == {"authenticated": False}
    assert client.get("/api/session").json() == {"authenticated": False}


def test_unsigned_session_cookie_is_rejected(client: TestClient) -> None:
    client.cookies.set("finmind_session", "unsigned-session-id")

    session_response = client.get("/api/session")
    workflows_response = client.get("/api/workflows")

    assert session_response.json() == {"authenticated": False}
    assert workflows_response.status_code == 401


def test_tampered_session_cookie_is_rejected(client: TestClient) -> None:
    login_response = client.post(
        "/api/login",
        json={"username": "analyst", "password": "secret-pass"},
    )
    session_cookie = login_response.cookies.get("finmind_session")
    assert session_cookie is not None
    assert "." in session_cookie
    client.cookies.set("finmind_session", f"{session_cookie}tampered")

    session_response = client.get("/api/session")
    workflows_response = client.get("/api/workflows")

    assert session_response.json() == {"authenticated": False}
    assert workflows_response.status_code == 401


def test_invalid_credentials_are_rejected(client: TestClient) -> None:
    response = client.post(
        "/api/login",
        json={"username": "analyst", "password": "wrong"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


def test_app_builds_with_dataset_provider_config(
    admin_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("FINMIND_VN_PROVIDER", "vnstock")
    monkeypatch.setenv("FINMIND_VNSTOCK_API_KEY", "vnstock-key")
    monkeypatch.setenv("FINMIND_US_PROVIDER", "yfinance")
    monkeypatch.setenv("FINMIND_XAUUSD_PROVIDER", "yfinance")
    monkeypatch.setenv("FINMIND_XAUUSD_DAILY_FALLBACK", "alpha_vantage")
    monkeypatch.setenv("FINMIND_ALPHA_VANTAGE_API_KEY", "alpha-key")
    monkeypatch.setenv("FINMIND_SJC_PROVIDER", "sjc_official")

    app = create_app()

    sources = app.state.platform.ingestion_service.sources
    assert set(sources) == {"vn_prices", "vn_prices_daily"}
    assert sources["vn_prices"].provider == "vnstock"
    assert sources["vn_prices_daily"].provider == "vnstock"
    assert sources["vn_prices_daily"].source_id == "vn_prices_daily"


def test_app_builds_roadmap_sources_only_when_enabled(
    admin_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("FINMIND_VN_PROVIDER", "vnstock")
    monkeypatch.setenv("FINMIND_US_PROVIDER", "yfinance")
    monkeypatch.setenv("FINMIND_XAUUSD_PROVIDER", "yfinance")
    monkeypatch.setenv("FINMIND_XAUUSD_DAILY_FALLBACK", "alpha_vantage")
    monkeypatch.setenv("FINMIND_ALPHA_VANTAGE_API_KEY", "alpha-key")
    monkeypatch.setenv("FINMIND_SJC_PROVIDER", "sjc_official")
    monkeypatch.setenv("FINMIND_ROADMAP_MARKETS", "true")

    app = create_app()

    sources = app.state.platform.ingestion_service.sources
    assert set(sources) == {
        "us_prices",
        "us_prices_daily",
        "vn_prices",
        "vn_prices_daily",
        "xauusd_prices",
        "xauusd_prices_daily",
        "sjc_gold_prices",
    }
    assert sources["us_prices"].provider == "yfinance"
    assert sources["us_prices_daily"].provider == "stooq"
    assert sources["vn_prices"].provider == "vnstock"
    assert sources["vn_prices_daily"].provider == "vnstock"
    assert sources["vn_prices_daily"].source_id == "vn_prices_daily"


def test_app_defaults_to_mock_dataset_providers(admin_env: None) -> None:
    app = create_app()

    sources = app.state.platform.ingestion_service.sources
    assert set(sources) == {"vn_prices"}
    assert all(source.__class__.__name__ == "DemoMarketDataSource" for source in sources.values())


def test_dataset_provider_config_rejects_unknown_provider(
    admin_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("FINMIND_VN_PROVIDER", "paid-vendor")

    with pytest.raises(SettingsError, match="FINMIND_VN_PROVIDER"):
        create_app()


def test_vnstock_provider_does_not_require_api_key(
    admin_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("FINMIND_VN_PROVIDER", "vnstock")
    monkeypatch.delenv("FINMIND_VNSTOCK_API_KEY", raising=False)
    monkeypatch.setenv("FINMIND_PROVIDER_TOKEN", "legacy-shared-token")

    app = create_app()

    sources = app.state.platform.ingestion_service.sources
    assert sources["vn_prices"].provider == "vnstock"
    assert sources["vn_prices_daily"].provider == "vnstock"
