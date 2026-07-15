import json
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from finmind_agents.agents.models import AgentRunResult, AgentStreamEvent
from finmind_api.app import create_app


class FakeAgentOrchestrator:
    async def stream_skill(self, request: object) -> object:
        language = getattr(request, "context", {}).get("language", "en")
        citations = tuple(getattr(request, "citation_ids", ()))[:1]
        content = "Dữ liệu có sẵn." if language == "vi" else "Available evidence is shown."
        yield AgentStreamEvent(kind="content_delta", text=content)
        yield AgentStreamEvent(
            kind="result",
            result=AgentRunResult(
                status="success", section_title="Research", content=content,
                citations=citations,
                allowed_claims=("data_availability",), blocked_claims=(), warnings=(),
            ),
        )


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("FINMIND_ADMIN_USERNAME", "analyst")
    monkeypatch.setenv("FINMIND_ADMIN_PASSWORD", "secret-pass")
    monkeypatch.setenv("FINMIND_SESSION_SECRET", "session-secret-with-length")
    monkeypatch.setattr("finmind_api.platform.build_default_agent_orchestrator", lambda: FakeAgentOrchestrator())
    with TestClient(create_app()) as test_client:
        yield test_client


def _login(client: TestClient) -> None:
    response = client.post("/api/login", json={"username": "analyst", "password": "secret-pass"})
    assert response.status_code == 200


def _events(response: object) -> list[dict[str, object]]:
    events: list[dict[str, object]] = []
    for line in response.iter_lines():
        value = line.decode() if isinstance(line, bytes) else line
        if value.startswith("data:"):
            events.append(json.loads(value.removeprefix("data:").strip()))
    return events


def _start(client: TestClient, workflow_id: str, payload: dict[str, object]) -> list[dict[str, object]]:
    with client.stream("POST", f"/api/workflows/{workflow_id}/conversations", json=payload) as response:
        assert response.status_code == 200
        return _events(response)


def test_workflow_catalog_includes_fixed_gold_workflow(client: TestClient) -> None:
    _login(client)
    workflows = client.get("/api/workflows").json()
    gold = next(item for item in workflows if item["id"] == "gold-technical-analysis")
    assert gold["market_scope"] == ["GOLD"]
    assert gold["required_inputs"] == [{"name": "market", "type": "string", "required": True}]
    workflow_ids = {item["id"] for item in workflows}
    assert {"vn-news-digest", "vn-valuation", "vn-stock-brief"} <= workflow_ids


@pytest.mark.parametrize("workflow_id", ["vn-news-digest", "vn-valuation", "vn-stock-brief"])
def test_extended_vn_workflows_create_cited_conversations(
    client: TestClient,
    workflow_id: str,
) -> None:
    _login(client)
    events = _start(
        client,
        workflow_id,
        {"market": "VN_STOCK", "symbol": "VCB", "language": "en"},
    )
    completed = next(event for event in events if event["kind"] == "conversation.completed")
    message = completed["payload"]["message"]
    assert message["content"]
    assert message["citations"]


def test_workflow_creates_conversation_and_message_owned_evidence(client: TestClient) -> None:
    _login(client)
    events = _start(client, "vn-financial-data-collector", {"market": "VN_STOCK", "symbol": "VCB", "language": "en"})
    assert events[0]["kind"] == "conversation.started"
    completed = next(event for event in events if event["kind"] == "conversation.completed")
    conversation_id = completed["payload"]["conversation"]["id"]
    detail = client.get(f"/api/conversations/{conversation_id}")
    assert detail.status_code == 200
    body = detail.json()
    assert body["status"] == "success"
    assert body["messages"][0]["source_kind"] == "workflow_result"
    assert body["messages"][0]["citations"]
    assert body["messages"][0]["artifacts"]
    assert client.get("/api/runs").status_code == 404


def test_gold_workflow_binds_xauusd_and_rejects_override(client: TestClient) -> None:
    _login(client)
    events = _start(client, "gold-technical-analysis", {"market": "GOLD", "language": "vi"})
    completed = next(event for event in events if event["kind"] == "conversation.completed")
    assert completed["payload"]["conversation"]["inputs"]["symbol"] == "XAUUSD"
    assert completed["payload"]["message"]["workflow_result"]["language"] == "vi"
    rejected = client.post("/api/workflows/gold-technical-analysis/conversations", json={"market": "GOLD", "symbol": "SJC", "language": "en"})
    assert rejected.status_code == 422


def test_language_preference_defaults_and_validates(client: TestClient) -> None:
    _login(client)
    assert client.get("/api/preferences/language").json() == {"selection": "auto"}
    assert client.put("/api/preferences/language", json={"selection": "vi"}).json() == {"selection": "vi"}
    assert client.put("/api/preferences/language", json={"selection": "fr"}).status_code == 422


def test_terminal_conversation_can_be_deleted(client: TestClient) -> None:
    _login(client)
    events = _start(client, "vn-financial-data-collector", {"market": "VN_STOCK", "symbol": "VCB", "language": "en"})
    completed = next(event for event in events if event["kind"] == "conversation.completed")
    conversation_id = completed["payload"]["conversation"]["id"]
    assert client.delete(f"/api/conversations/{conversation_id}").status_code == 204
    assert client.get(f"/api/conversations/{conversation_id}").status_code == 404
