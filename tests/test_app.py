import json
from collections.abc import Iterator
from pathlib import Path
import asyncio

import pytest
from fastapi.testclient import TestClient

from finmind_agents.agents.models import AgentStreamEvent
from finmind_api.app import create_app
from finmind_api.settings import Settings, SettingsError


@pytest.fixture
def admin_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FINMIND_ADMIN_USERNAME", "analyst")
    monkeypatch.setenv("FINMIND_ADMIN_PASSWORD", "secret-pass")
    monkeypatch.setenv("FINMIND_SESSION_SECRET", "session-secret-with-length")


class FakeAgentOrchestrator:
    def _result(self, request: object) -> object:
        from finmind_agents.agents.models import AgentRunResult

        return AgentRunResult(
            status="success",
            section_title="Collected Data",
            content="VCB momentum remains constructive on available data.",
            citations=("citation_vn_prices_VCB-prices",),
            allowed_claims=("data_availability",),
            blocked_claims=(),
            warnings=(),
        )

    async def stream_skill(self, request: object) -> object:
        yield AgentStreamEvent(kind="content_delta", text="VCB momentum remains ")
        yield AgentStreamEvent(kind="content_delta", text="constructive on available data.")
        yield AgentStreamEvent(kind="result", result=self._result(request))


def _collect_sse_events(response: object) -> list[dict[str, object]]:
    events: list[dict[str, object]] = []
    event_name = "message"
    data_lines: list[str] = []
    for raw_line in response.iter_lines():
        line = raw_line if isinstance(raw_line, str) else raw_line.decode("utf-8")
        if not line:
            if data_lines:
                payload = json.loads("\n".join(data_lines))
                payload["_event"] = event_name
                events.append(payload)
            event_name = "message"
            data_lines = []
            continue
        if line.startswith("event:"):
            event_name = line.removeprefix("event:").strip()
        elif line.startswith("data:"):
            data_lines.append(line.removeprefix("data:").strip())
    return events


def _post_workflow_run(
    client: TestClient,
    workflow_id: str,
    payload: dict[str, object],
) -> tuple[object, list[dict[str, object]]]:
    with client.stream(
        "POST",
        f"/api/workflows/{workflow_id}/runs",
        json=payload,
        headers={"Accept": "text/event-stream"},
    ) as response:
        events = _collect_sse_events(response)
    return response, events


def _final_run_from_events(events: list[dict[str, object]]) -> dict[str, object]:
    final_event = next(event for event in events if event["kind"] == "run.completed")
    return final_event["payload"]["run"]


def _failed_event_from_events(events: list[dict[str, object]]) -> dict[str, object]:
    return next(event for event in events if event["kind"] == "run.failed")


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
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("FINMIND_ADMIN_USERNAME", raising=False)
    monkeypatch.delenv("FINMIND_ADMIN_PASSWORD", raising=False)
    monkeypatch.delenv("FINMIND_SESSION_SECRET", raising=False)

    with pytest.raises(SettingsError, match="FINMIND_ADMIN_USERNAME"):
        create_app()


def test_settings_loads_local_dotenv_fallback_for_admin_login(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dotenv_path = tmp_path / ".env"
    dotenv_path.write_text(
        "\n".join(
            [
                "FINMIND_ADMIN_USERNAME=admin",
                "FINMIND_ADMIN_PASSWORD=admin",
                "FINMIND_SESSION_SECRET=session-secret-with-length",
                "FINMIND_DATABASE_URL=postgresql://example",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("FINMIND_ADMIN_USERNAME", raising=False)
    monkeypatch.delenv("FINMIND_ADMIN_PASSWORD", raising=False)
    monkeypatch.delenv("FINMIND_SESSION_SECRET", raising=False)

    settings = Settings.from_env()

    assert settings.admin_username == "admin"
    assert settings.admin_password == "admin"


def test_process_env_overrides_local_dotenv(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dotenv_path = tmp_path / ".env"
    dotenv_path.write_text(
        "\n".join(
            [
                "FINMIND_ADMIN_USERNAME=admin",
                "FINMIND_ADMIN_PASSWORD=admin",
                "FINMIND_SESSION_SECRET=session-secret-with-length",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("FINMIND_ADMIN_USERNAME", "analyst")
    monkeypatch.setenv("FINMIND_ADMIN_PASSWORD", "secret-pass")
    monkeypatch.setenv("FINMIND_SESSION_SECRET", "process-secret-with-length")

    settings = Settings.from_env()

    assert settings.admin_username == "analyst"
    assert settings.admin_password == "secret-pass"


def test_protected_workflow_routes_require_login(client: TestClient) -> None:
    workflows_response = client.get("/api/workflows")
    runs_response = client.get("/api/runs")
    citations_response = client.get("/api/runs/run_missing/citations")
    run_response = client.post(
        "/api/workflows/vn-financial-data-collector/runs",
        json={"market": "VN_STOCK", "symbol": "VCB"},
    )

    assert workflows_response.status_code == 401
    assert workflows_response.json()["detail"] == "Authentication required"
    assert runs_response.status_code == 401
    assert citations_response.status_code == 401
    assert run_response.status_code == 401


def test_run_citations_endpoint_returns_saved_citation_snapshots(
    client: TestClient,
) -> None:
    login_response = client.post(
        "/api/login",
        json={"username": "analyst", "password": "secret-pass"},
    )
    assert login_response.status_code == 200

    response, events = _post_workflow_run(
        client,
        "vn-financial-data-collector",
        {"market": "VN_STOCK", "symbol": "VCB"},
    )
    assert response.status_code == 200
    run = _final_run_from_events(events)

    citations_response = client.get(f"/api/runs/{run['id']}/citations")

    assert citations_response.status_code == 200
    citations = citations_response.json()
    assert len(citations) == 1
    citation = citations[0]
    assert citation["citation_id"] == "citation_vn_prices_VCB-prices"
    assert citation["record_type"] == "price_summary"
    assert citation["display_content"]
    assert citation["payload_snapshot"]["payload"]["year_end_prices"]


def test_workflow_validation_rejects_unsupported_market_and_missing_symbol(
    client: TestClient,
) -> None:
    login_response = client.post(
        "/api/login",
        json={"username": "analyst", "password": "secret-pass"},
    )
    assert login_response.status_code == 200

    unsupported_market = client.post(
        "/api/workflows/vn-financial-data-collector/runs",
        json={"market": "INVALID_MARKET", "symbol": "INVALID"},
    )
    missing_symbol = client.post(
        "/api/workflows/vn-financial-data-collector/runs",
        json={"market": "VN_STOCK"},
    )

    assert unsupported_market.status_code == 422
    assert "supports VN stocks only" in unsupported_market.json()["detail"]
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

        response, events = _post_workflow_run(
            test_client,
            "vn-financial-data-collector",
            {"market": "VN_STOCK", "symbol": "VCB"},
        )

    assert response.status_code == 200
    assert "LITELLM_CHAT_MODEL is required" in _failed_event_from_events(events)["payload"]["message"]


def test_workflow_run_exposes_safe_agent_metadata(client: TestClient) -> None:
    login_response = client.post(
        "/api/login",
        json={"username": "analyst", "password": "secret-pass"},
    )
    assert login_response.status_code == 200

    response, events = _post_workflow_run(
        client,
        "vn-financial-data-collector",
        {"market": "VN_STOCK", "symbol": "VCB"},
    )
    assert response.status_code == 200
    output = _final_run_from_events(events)["output"]
    assert output["steps"]
    assert any(step["id"] == "collect_data" for step in output["steps"])
    assert any(step["kind"] == "skill" for step in output["steps"])
    assert "reasoning" not in str(output).lower()
    assert "secret" not in str(output).lower()


def test_workflow_run_streams_safe_sse_events_and_persists_final_run(
    client: TestClient,
) -> None:
    login_response = client.post(
        "/api/login",
        json={"username": "analyst", "password": "secret-pass"},
    )
    assert login_response.status_code == 200

    response, events = _post_workflow_run(
        client,
        "vn-financial-data-collector",
        {"market": "VN_STOCK", "symbol": "VCB"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert [event["kind"] for event in events[:3]] == [
        "run.started",
        "run.stage",
        "run.stage",
    ]
    assert any(event["kind"] == "answer.delta" for event in events)
    artifact_event = next(event for event in events if event["kind"] == "artifact")
    assert artifact_event["payload"]["artifact_type"] == "chart"
    assert artifact_event["payload"]["chart_intent"] == "price_trend"
    assert artifact_event["payload"]["spec"]["supported_views"] == [
        "line",
        "candlestick",
    ]
    assert artifact_event["payload"]["downloads"]
    assert "table" not in artifact_event["payload"]
    assert any(event["kind"] == "run.completed" for event in events)
    assert events[-1]["kind"] == "run.completed"

    final_run = _final_run_from_events(events)
    assert final_run["output"]["artifacts"] == [artifact_event["payload"]]
    run_response = client.get(f"/api/runs/{final_run['id']}")

    assert run_response.status_code == 200
    assert run_response.json() == final_run


def test_chart_artifact_downloads_export_csv_and_svg(
    client: TestClient,
) -> None:
    login_response = client.post(
        "/api/login",
        json={"username": "analyst", "password": "secret-pass"},
    )
    assert login_response.status_code == 200

    _response, events = _post_workflow_run(
        client,
        "vn-financial-data-collector",
        {"market": "VN_STOCK", "symbol": "VCB"},
    )
    artifact = _final_run_from_events(events)["output"]["artifacts"][0]

    csv_response = client.get(f"/api/artifacts/{artifact['artifact_id']}/download?format=csv")
    svg_response = client.get(f"/api/artifacts/{artifact['artifact_id']}/download?format=svg")

    assert csv_response.status_code == 200
    assert csv_response.headers["content-type"].startswith("text/csv")
    assert "date,open,high,low,close,volume" in csv_response.text
    assert "2026-06-18,58200,58200,58200,58200,4920000" in csv_response.text
    assert svg_response.status_code == 200
    assert svg_response.headers["content-type"].startswith("image/svg+xml")
    assert "<svg" in svg_response.text


def test_workflow_run_emits_run_stage_before_answer_delta(
    admin_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("FINMIND_VN_DATA_PROVIDER", "offline")
    monkeypatch.setattr(
        "finmind_api.platform.build_default_agent_orchestrator",
        lambda: FakeAgentOrchestrator(),
    )
    app = create_app()
    with TestClient(app) as test_client:
        login_response = test_client.post(
            "/api/login",
            json={"username": "analyst", "password": "secret-pass"},
        )
        assert login_response.status_code == 200

        response, events = _post_workflow_run(
            test_client,
            "vn-financial-data-collector",
            {"market": "VN_STOCK", "symbol": "VCB"},
        )

    answer_delta_indexes = [
        index for index, event in enumerate(events) if event["kind"] == "answer.delta"
    ]
    first_stage_index = next(
        index for index, event in enumerate(events) if event["kind"] == "run.stage"
    )
    assert response.status_code == 200
    assert len(answer_delta_indexes) >= 2
    assert all(first_stage_index < index for index in answer_delta_indexes)
    assert "".join(events[index]["payload"]["text"] for index in answer_delta_indexes)

    skill_running_index = next(
        index
        for index, event in enumerate(events)
        if event["kind"] == "run.stage"
        and event["payload"].get("stage") == "vn-financial-data-auditor"
        and event["payload"].get("status") == "running"
    )
    assert skill_running_index < answer_delta_indexes[0]


def test_workflow_run_returns_429_when_per_user_stream_limit_is_reached(
    admin_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("FINMIND_VN_DATA_PROVIDER", "offline")
    monkeypatch.setenv("FINMIND_STREAM_PER_USER_LIMIT", "1")
    monkeypatch.setattr(
        "finmind_api.platform.build_default_agent_orchestrator",
        lambda: FakeAgentOrchestrator(),
    )
    app = create_app()
    with TestClient(app) as test_client:
        login_response = test_client.post(
            "/api/login",
            json={"username": "analyst", "password": "secret-pass"},
        )
        assert login_response.status_code == 200
        lease = asyncio.run(app.state.stream_limiter.acquire("analyst"))
        assert lease is not None
        response = test_client.post(
            "/api/workflows/vn-financial-data-collector/runs",
            json={"market": "VN_STOCK", "symbol": "VCB"},
            headers={"Accept": "text/event-stream"},
        )
        asyncio.run(app.state.stream_limiter.release(lease))

    assert response.status_code == 429
    assert response.json()["detail"]["error"]["code"] == "concurrency_limit_exceeded"


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
