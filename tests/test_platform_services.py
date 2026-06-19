from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from api.app import create_app


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("FINMIND_ADMIN_USERNAME", "analyst")
    monkeypatch.setenv("FINMIND_ADMIN_PASSWORD", "secret-pass")
    monkeypatch.setenv("FINMIND_SESSION_SECRET", "session-secret-with-length")
    app = create_app()
    with TestClient(app) as test_client:
        login = test_client.post(
            "/api/login",
            json={"username": "analyst", "password": "secret-pass"},
        )
        assert login.status_code == 200
        yield test_client


def test_workflow_catalog_exposes_vn_stock_and_gold_workflows(
    client: TestClient,
) -> None:
    response = client.get("/api/workflows")

    assert response.status_code == 200
    workflows = response.json()
    workflow_ids = {workflow["id"] for workflow in workflows}
    assert {
        "daily-market-brief",
        "vn-single-symbol-research",
        "gold-brief",
    } <= workflow_ids
    assert all(workflow["requires_citations"] for workflow in workflows)
    assert all("stages" in workflow for workflow in workflows)


def test_workflow_run_returns_cited_fresh_chart_result(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/workflows/daily-market-brief/run",
        json={"market": "VN_STOCK"},
    )

    assert response.status_code == 200
    result = response.json()
    assert result["kind"] == "workflow"
    assert result["status"] == "success"
    assert result["output"]["sections"][0]["citations"]
    assert result["output"]["citations"][0]["source_type"] == "market_data"
    assert result["output"]["freshness"][0]["status"] == "fresh"
    chart = result["output"]["artifacts"]["chart"]
    assert chart["artifact_type"] == "chart"
    assert chart["payload"]["series"]
    assert chart["evidence_refs"]
    assert "reasoning" not in str(result).lower()

    run_response = client.get(f"/api/runs/{result['id']}")

    assert run_response.status_code == 200
    assert run_response.json() == result

    list_response = client.get("/api/runs")

    assert list_response.status_code == 200
    assert list_response.json()[0] == result


def test_single_symbol_workflow_targets_requested_symbol(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/workflows/vn-single-symbol-research/run",
        json={"market": "VN_STOCK", "symbol": "VCB"},
    )

    assert response.status_code == 200
    result = response.json()
    section = result["output"]["sections"][0]
    chart = result["output"]["artifacts"]["chart"]

    assert result["inputs"]["symbol"] == "VCB"
    assert "VCB closed" in section["content"]
    assert "VNINDEX" not in section["content"]
    assert chart["payload"]["table"] == [
        {
            "record_key": "VCB-2026-06-18",
            "market_time": "2026-06-18T07:00:00+00:00",
            "close": 58200,
        }
    ]


def test_invalid_workflow_input_does_not_create_successful_run(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/workflows/daily-market-brief/run",
        json={"market": "US_STOCK"},
    )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert "V1 supports VN stocks and gold" in detail


def test_unknown_run_returns_404(client: TestClient) -> None:
    response = client.get("/api/runs/run_missing")

    assert response.status_code == 404
    assert response.json()["detail"] == "Run not found"
