from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from api.app import create_app
from api.platform.workflows.catalog import build_workflow_catalog


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


def test_workflow_definitions_load_phase_02_catalog(
    client: TestClient,
) -> None:
    response = client.get("/api/workflows")

    assert response.status_code == 200
    workflows = response.json()
    workflow_ids = {workflow["id"] for workflow in workflows}
    assert {
        "fundamental-analysis",
        "technical-analysis",
        "news-digest",
        "risk-review",
        "stock-brief",
    } <= workflow_ids
    assert "gold-brief" not in workflow_ids
    assert all(workflow["requires_citations"] for workflow in workflows)
    assert all("stages" in workflow for workflow in workflows)
    stock_brief = next(workflow for workflow in workflows if workflow["id"] == "stock-brief")
    assert stock_brief["workflow_type"] == "composite"
    assert stock_brief["market_scope"] == ["VN_STOCK", "US_STOCK"]
    assert stock_brief["output_sections"] == [
        "Data Quality",
        "Fundamentals",
        "Technical Analysis",
        "News Digest",
        "Risk Review",
    ]


def test_workflow_yaml_definitions_reference_existing_agent_skills() -> None:
    workflows = build_workflow_catalog()

    assert workflows
    for workflow in workflows:
        assert workflow.definition_path.endswith(f"{workflow.workflow_id}.yaml")
        assert workflow.workflow_type in {"atomic", "internal", "composite"}
        assert workflow.skill_refs
        for skill_ref in workflow.skill_refs:
            assert skill_ref.endswith(".md")


def test_workflow_run_returns_cited_fresh_chart_result(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/workflows/technical-analysis/run",
        json={"market": "VN_STOCK", "symbol": "VCB"},
    )

    assert response.status_code == 200
    result = response.json()
    assert result["kind"] == "workflow"
    assert result["status"] == "success"
    assert result["inputs"]["symbol"] == "VCB"
    assert result["output"]["quality"]["quality_status"] in {"pass", "warn"}
    analysis_section = next(
        section
        for section in result["output"]["sections"]
        if section["title"] == "Technical Analysis"
    )
    assert analysis_section["citations"]
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


def test_fundamental_workflow_collects_fundamentals_and_source_documents(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/workflows/fundamental-analysis/run",
        json={"market": "VN_STOCK", "symbol": "VCB"},
    )

    assert response.status_code == 200
    result = response.json()
    quality = result["output"]["quality"]
    section = next(
        item
        for item in result["output"]["sections"]
        if item["title"] == "Fundamentals"
    )

    assert result["status"] == "success"
    assert quality["dataset_statuses"]["fundamentals"] == "fresh"
    assert quality["dataset_statuses"]["source_documents"] == "fresh"
    assert section["status"] == "success"


def test_single_symbol_workflow_targets_requested_symbol(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/workflows/technical-analysis/run",
        json={"market": "VN_STOCK", "symbol": "VCB"},
    )

    assert response.status_code == 200
    result = response.json()
    section = next(
        item
        for item in result["output"]["sections"]
        if item["title"] == "Technical Analysis"
    )
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
        "/api/workflows/technical-analysis/run",
        json={"market": "GOLD", "symbol": "SJC"},
    )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert "supports VN stocks and US stocks only" in detail


@pytest.mark.parametrize(
    ("payload", "expected_detail"),
    [
        ({"market": "GOLD", "symbol": "SJC"}, "supports VN stocks and US stocks only"),
        ({"market": "BTC", "symbol": "BTC"}, "supports VN stocks and US stocks only"),
        ({"market": "CRYPTO", "symbol": "ETH"}, "supports VN stocks and US stocks only"),
        ({"market": "VN_STOCK"}, "symbol is required"),
        ({"market": "VN_STOCK", "symbol": "ZZZ"}, "Required market data is missing"),
    ],
)
def test_unsupported_or_missing_workflow_inputs_are_rejected(
    client: TestClient,
    payload: dict[str, str],
    expected_detail: str,
) -> None:
    response = client.post("/api/workflows/technical-analysis/run", json=payload)

    assert response.status_code == 422
    assert expected_detail in response.json()["detail"]


def test_failed_validation_does_not_create_successful_run(
    client: TestClient,
) -> None:
    failed = client.post(
        "/api/workflows/technical-analysis/run",
        json={"market": "VN_STOCK", "symbol": "ZZZ"},
    )
    runs = client.get("/api/runs")

    assert failed.status_code == 422
    assert runs.status_code == 200
    assert runs.json() == []


def test_stock_brief_composite_run_shows_visible_stages(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/workflows/stock-brief/run",
        json={"market": "VN_STOCK", "symbol": "VCB"},
    )

    assert response.status_code == 200
    result = response.json()
    stage_ids = [
        stage["id"]
        for stage in result["output"]["visible_execution"]["stages"]
    ]
    assert stage_ids == [
        "data-collector",
        "data-quality-check",
        "fundamental-analysis",
        "technical-analysis",
        "news-digest",
        "risk-review",
    ]
    assert result["output"]["sections"]


def test_stock_brief_marks_blocked_claim_categories_unavailable(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/workflows/stock-brief/run",
        json={"market": "US_STOCK", "symbol": "AAPL"},
    )

    assert response.status_code == 200
    result = response.json()
    quality = result["output"]["quality"]
    unavailable_sections = [
        section
        for section in result["output"]["sections"]
        if section["status"] == "unavailable"
    ]
    assert "source_documents" in quality["blocked_claims"]
    assert unavailable_sections


def test_unknown_run_returns_404(client: TestClient) -> None:
    response = client.get("/api/runs/run_missing")

    assert response.status_code == 404
    assert response.json()["detail"] == "Run not found"


def test_completed_workflow_run_can_be_reopened_from_history(
    client: TestClient,
) -> None:
    run_response = client.post(
        "/api/workflows/technical-analysis/run",
        json={"market": "VN_STOCK", "symbol": "VCB"},
    )
    result = run_response.json()

    list_response = client.get("/api/runs")
    detail_response = client.get(f"/api/runs/{result['id']}")

    assert run_response.status_code == 200
    assert result["status"] == "success"
    assert list_response.status_code == 200
    assert list_response.json()[0] == result
    assert detail_response.status_code == 200
    assert detail_response.json() == result


def test_partial_workflow_run_can_be_reopened_from_history(
    client: TestClient,
) -> None:
    run_response = client.post(
        "/api/workflows/stock-brief/run",
        json={"market": "US_STOCK", "symbol": "AAPL"},
    )
    result = run_response.json()

    detail_response = client.get(f"/api/runs/{result['id']}")

    assert run_response.status_code == 200
    assert result["status"] == "partial"
    assert result["output"]["quality"]["quality_status"] == "partial"
    assert detail_response.status_code == 200
    assert detail_response.json() == result
