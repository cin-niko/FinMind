from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from finmind_api.app import create_app
from finmind_api.settings import SettingsError


@pytest.fixture
def admin_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FINMIND_ADMIN_USERNAME", "analyst")
    monkeypatch.setenv("FINMIND_ADMIN_PASSWORD", "secret-pass")
    monkeypatch.setenv("FINMIND_SESSION_SECRET", "session-secret-with-length")


class FakeAgentOrchestrator:
    def run_skill(self, request: object) -> object:
        from finmind_agents.agents.models import AgentRunResult

        return AgentRunResult(
            status="success",
            section_title="Collected Data",
            content="Agent-collected VCB data package with evidence.",
            citations=("citation_vn_prices_VCB-prices",),
            allowed_claims=("data_availability",),
            blocked_claims=(),
            warnings=(),
        )


@pytest.fixture
def client(admin_env: None, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("FINMIND_VN_DATA_PROVIDER", "offline")
    monkeypatch.setattr(
        "finmind_api.platform.build_default_agent_orchestrator",
        lambda: FakeAgentOrchestrator(),
    )
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
    run_response = client.post(
        "/api/workflows/vn-financial-data-collector/run",
        json={"market": "VN_STOCK", "symbol": "VCB"},
    )

    assert workflows_response.status_code == 401
    assert workflows_response.json()["detail"] == "Authentication required"
    assert runs_response.status_code == 401
    assert run_response.status_code == 401


def test_workflow_validation_rejects_unsupported_market_and_missing_symbol(
    client: TestClient,
) -> None:
    login_response = client.post(
        "/api/login",
        json={"username": "analyst", "password": "secret-pass"},
    )
    assert login_response.status_code == 200

    unsupported_market = client.post(
        "/api/workflows/vn-financial-data-collector/run",
        json={"market": "BTC", "symbol": "BTC"},
    )
    missing_symbol = client.post(
        "/api/workflows/vn-financial-data-collector/run",
        json={"market": "VN_STOCK"},
    )

    assert unsupported_market.status_code == 422
    assert "supports VN stocks and US stocks only" in unsupported_market.json()["detail"]
    assert missing_symbol.status_code == 422
    assert missing_symbol.json()["detail"] == "symbol is required"


def test_workflow_agent_runtime_error_returns_service_unavailable(
    admin_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("FINMIND_VN_DATA_PROVIDER", "offline")
    monkeypatch.delenv("LITELLM_CHAT_MODEL", raising=False)
    app = create_app()
    with TestClient(app) as test_client:
        login_response = test_client.post(
            "/api/login",
            json={"username": "analyst", "password": "secret-pass"},
        )
        assert login_response.status_code == 200

        response = test_client.post(
            "/api/workflows/vn-financial-data-collector/run",
            json={"market": "VN_STOCK", "symbol": "VCB"},
        )

    assert response.status_code == 503
    assert "LITELLM_CHAT_MODEL is required" in response.json()["detail"]


def test_workflow_run_exposes_safe_agent_metadata(client: TestClient) -> None:
    login_response = client.post(
        "/api/login",
        json={"username": "analyst", "password": "secret-pass"},
    )
    assert login_response.status_code == 200

    response = client.post(
        "/api/workflows/vn-financial-data-collector/run",
        json={"market": "VN_STOCK", "symbol": "VCB"},
    )

    assert response.status_code == 200
    output = response.json()["output"]
    assert output["steps"]
    assert any(step["id"] == "collect_data" for step in output["steps"])
    assert any(step["kind"] == "skill" for step in output["steps"])
    assert "reasoning" not in str(output).lower()
    assert "secret" not in str(output).lower()


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
