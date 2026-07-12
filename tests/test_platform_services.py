from collections.abc import Iterator
import asyncio
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from finmind_agents.models import Market
from finmind_agents.workflows.catalog import build_workflow_catalog
from finmind_api.app import create_app
from finmind_api.platform import build_run_store as _real_build_run_store


def test_target_packages_are_importable() -> None:
    import finmind_agents
    import finmind_api

    assert finmind_agents.__doc__
    assert finmind_api.__doc__


def test_finmind_agent_runtime_policy_fails_closed_without_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from finmind_agents.runtime.bootstrap import AgentModelSettings
    from finmind_agents.runtime.models import AgentRuntimePolicy, RuntimeMode
    from finmind_agents.runtime.service import FinMindAgentRuntime, RuntimeConfigurationError

    monkeypatch.delenv("LITELLM_CHAT_MODEL", raising=False)

    runtime = FinMindAgentRuntime(
        model_settings=AgentModelSettings.from_env(),
        policy=AgentRuntimePolicy.workflow_strict(),
    )

    with pytest.raises(RuntimeConfigurationError, match="LITELLM_CHAT_MODEL"):
        runtime.ensure_configured(RuntimeMode.WORKFLOW)


class FakeAgentOrchestrator:
    async def stream_skill(self, request: object) -> object:
        from finmind_agents.agents.models import AgentRunResult, AgentStreamEvent

        yield AgentStreamEvent(
            kind="content_delta",
            text="Agent-collected VCB data package with evidence.",
        )
        yield AgentStreamEvent(
            kind="result",
            result=AgentRunResult(
                status="success",
                section_title="Collected Data",
                content="Agent-collected VCB data package with evidence.",
                citations=("citation_vn_prices_VCB-prices",),
                allowed_claims=("data_availability",),
                blocked_claims=(),
                warnings=(),
            ),
        )


class CapturingAgentOrchestrator:
    def __init__(self) -> None:
        self.requests: list[object] = []

    async def stream_skill(self, request: object) -> object:
        from finmind_agents.agents.models import AgentRunResult, AgentStreamEvent

        self.requests.append(request)
        yield AgentStreamEvent(
            kind="result",
            result=AgentRunResult(
                status="success",
                section_title="Collected Data",
                content="Captured request.",
                citations=("citation_vn_prices_VCB-prices",),
                allowed_claims=("data_availability",),
                blocked_claims=(),
                warnings=(),
            ),
        )


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
) -> tuple[object, dict[str, object] | None, list[dict[str, object]]]:
    with client.stream(
        "POST",
        f"/api/workflows/{workflow_id}/runs",
        json=payload,
        headers={"Accept": "text/event-stream"},
    ) as response:
        events = _collect_sse_events(response)
    final_output = next(
        (event for event in events if event["kind"] == "run.completed"),
        None,
    )
    return response, (
        final_output["payload"]["run"] if final_output is not None else None
    ), events


def _failed_event_from_events(events: list[dict[str, object]]) -> dict[str, object]:
    return next(event for event in events if event["kind"] == "run.failed")


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("FINMIND_ADMIN_USERNAME", "analyst")
    monkeypatch.setenv("FINMIND_ADMIN_PASSWORD", "secret-pass")
    monkeypatch.setenv("FINMIND_SESSION_SECRET", "session-secret-with-length")
    monkeypatch.setattr(
        "finmind_api.platform.build_default_agent_orchestrator",
        lambda: FakeAgentOrchestrator(),
    )
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
    assert workflow_ids == {
        "vn-financial-data-collector",
        "vn-fundamental-analysis",
        "vn-technical-analysis",
    }
    assert "gold-brief" not in workflow_ids
    assert all(workflow["requires_citations"] for workflow in workflows)
    assert all("stages" in workflow for workflow in workflows)
    by_id = {workflow["id"]: workflow for workflow in workflows}
    collector = by_id["vn-financial-data-collector"]
    assert collector["workflow_type"] == "atomic"
    assert collector["market_scope"] == ["VN_STOCK"]
    assert collector["output_sections"] == [
        "Collected Data",
    ]
    fundamental = by_id["vn-fundamental-analysis"]
    assert fundamental["workflow_type"] == "composite"
    assert fundamental["output_sections"] == ["Fundamental Analysis"]
    technical = by_id["vn-technical-analysis"]
    assert technical["workflow_type"] == "atomic"
    assert technical["output_sections"] == ["Technical Analysis"]


def test_workflow_catalog_entries_expose_required_metadata(
    client: TestClient,
) -> None:
    response = client.get("/api/workflows")

    assert response.status_code == 200
    for workflow in response.json():
        assert workflow["title"]
        assert workflow["description"]
        assert workflow["market_scope"]
        assert workflow["required_inputs"] == [
            {"name": "market", "type": "string", "required": True},
            {"name": "symbol", "type": "string", "required": True},
        ]
        assert workflow["stages"]
        assert workflow["output_sections"]
        assert workflow["requires_citations"] is True
        assert workflow["chart_requirements"] == [
            {
                "chart_id": "price_trend",
                "chart_type": "line",
                "title": "Price trend",
                "source_types": ["market_price"],
                "required": True,
            }
        ]
        serialized = json.dumps(workflow).lower()
        assert "vnstock" not in serialized


def test_workflow_yaml_definitions_reference_existing_agent_skills() -> None:
    workflows = build_workflow_catalog()

    assert workflows
    for workflow in workflows:
        assert workflow.definition_path.endswith(f"{workflow.workflow_id}.yaml")
        assert workflow.workflow_type in {"atomic", "internal", "composite"}
        assert workflow.skill_refs
        for skill_ref in workflow.skill_refs:
            assert skill_ref.endswith("/SKILL.md")


def test_workflow_yaml_does_not_duplicate_skill_data_requirements() -> None:
    definition = json.loads(
        Path(
            "src/finmind_agents/workflows/definitions/"
            "vn-financial-data-collector.yaml"
        ).read_text(encoding="utf-8")
    )

    assert "required_datasets" not in definition


def test_workflow_agent_skills_use_standard_format() -> None:
    from pathlib import Path

    skills_dir = Path("src/finmind_agents/workflows/skills")
    required_sections = {
        "## Role",
        "## When To Use",
        "## Agent Prompt",
        "## Required Context",
        "## Workflow Procedure",
        "## Output Contract",
        "## Citation Policy",
        "## Allowed Claims",
        "## Unavailable Rules",
        "## Safety Rules",
        "## Output Examples",
    }

    skill_paths = sorted(skills_dir.glob("*/SKILL.md"))

    assert skill_paths
    for path in skill_paths:
        assert path.parent.name in {
            "vn-financial-data-auditor",
            "vn-fundamental-analysis",
            "vn-technical-analysis",
        }
        content = path.read_text(encoding="utf-8")
        assert content.startswith("---\n")
        assert "name:" in content
        assert "description:" in content
        missing_sections = {
            section for section in required_sections if section not in content
        }
        assert not missing_sections, f"{path} missing {sorted(missing_sections)}"
        for line in content.splitlines():
            if line.startswith("- `references/"):
                reference_path = path.parent / line.removeprefix("- `").removesuffix("`")
                assert reference_path.exists(), f"{path} missing {reference_path}"


def test_vn_collector_skill_declares_low_level_data_requirements() -> None:
    from finmind_agents.dataflows.requirements import load_data_requirements

    requirements = load_data_requirements(
        "src/finmind_agents/workflows/skills/vn-financial-data-auditor/DATA_REQUIREMENTS.yaml"
    )

    assert [requirement.dataset for requirement in requirements] == [
        "ohlcv",
        "financial_statement",
        "valuation_ratios",
        "corporate_events",
        "company_profile",
        "source_documents",
    ]
    assert requirements[0].params["interval"] == "1d"
    assert requirements[0].params["lookback"] == "2y"
    assert requirements[1].params["statements"] == [
        "income_statement",
        "balance_sheet",
        "cash_flow",
    ]


def test_dataflow_request_derives_dataset_groups_from_low_level_requirements() -> None:
    from finmind_agents.dataflows.models import (
        DataflowCollectionRequest,
        DataRequirement,
        DatasetGroup,
    )

    request = DataflowCollectionRequest(
        market=Market.VN_STOCK,
        symbol="DXG",
        requested_by="vn-financial-data-collector",
        data_requirements=(
            DataRequirement(dataset="ohlcv", params={"interval": "1d"}),
            DataRequirement(dataset="financial_statement", params={"lookback": "5y"}),
            DataRequirement(dataset="source_documents", params={"lookback": "90d"}),
        ),
    )

    assert request.effective_dataset_groups() == (
        DatasetGroup.MARKET_PRICE,
        DatasetGroup.FUNDAMENTAL,
        DatasetGroup.NEWS,
    )


def test_agent_collection_plan_rejects_undeclared_dataset() -> None:
    from finmind_agents.dataflows.models import AgentCollectionPlan, DataRequirement
    from finmind_agents.dataflows.requirements import (
        CollectionPlanError,
        validate_agent_collection_plan,
    )

    plan = AgentCollectionPlan(
        skill_id="vn-financial-data-collector",
        market=Market.VN_STOCK,
        symbol="DXG",
        required_requests=(DataRequirement(dataset="ohlcv"),),
        optional_requests=(DataRequirement(dataset="news"),),
        policy_id="workflow_strict",
    )

    with pytest.raises(CollectionPlanError, match="not declared"):
        validate_agent_collection_plan(
            plan,
            declared_requirements=(DataRequirement(dataset="ohlcv"),),
            allow_optional=True,
        )


def test_dataflow_service_passes_effective_groups_to_provider() -> None:
    from finmind_agents.dataflows.models import (
        DataflowProviderResult,
        DataflowCollectionRequest,
        DataRequirement,
        DatasetGroup,
        CollectionStatus,
    )
    from finmind_agents.dataflows.providers.base import (
        ProviderCapability,
        ProviderFetchResult,
    )
    from finmind_agents.dataflows.registry import DataflowProviderRegistry
    from finmind_agents.dataflows.service import DataflowService

    seen_groups: list[tuple[DatasetGroup, ...]] = []

    class RecordingProvider:
        provider_id = "recording"
        capabilities = (
            ProviderCapability(
                market=Market.VN_STOCK,
                dataset_groups=(DatasetGroup.MARKET_PRICE,),
            ),
        )

        def fetch(self, request: DataflowCollectionRequest) -> ProviderFetchResult:
            seen_groups.append(request.dataset_groups)
            return ProviderFetchResult(
                provider_result=DataflowProviderResult(
                    provider_id=self.provider_id,
                    dataset_groups=request.dataset_groups,
                    status=CollectionStatus.FAILED,
                    warnings=("no_data",),
                    failure_reason="test provider has no data",
                )
            )

    DataflowService(
        registry=DataflowProviderRegistry(providers=(RecordingProvider(),))
    ).collect(
        DataflowCollectionRequest(
            market=Market.VN_STOCK,
            symbol="DXG",
            requested_by="test",
            data_requirements=(DataRequirement(dataset="ohlcv"),),
        )
    )

    assert seen_groups == [(DatasetGroup.MARKET_PRICE,)]


def test_collector_workflow_uses_skill_data_requirements(
    client: TestClient,
) -> None:
    response, result, _events = _post_workflow_run(
        client,
        "vn-financial-data-collector",
        {"market": "VN_STOCK", "symbol": "VCB"},
    )

    assert response.status_code == 200
    assert result["output"]["collection"]["requested_dataset_groups"] == [
        "market_price",
        "fundamental",
        "company_profile",
        "news",
    ]


def test_workflow_uses_agent_skill_output(
    client: TestClient,
) -> None:
    response, result, _events = _post_workflow_run(
        client,
        "vn-financial-data-collector",
        {"market": "VN_STOCK", "symbol": "VCB"},
    )

    assert response.status_code == 200
    collected = next(
        section
        for section in result["output"]["sections"]
        if section["title"] == "Collected Data"
    )

    assert collected["content"] == "Agent-collected VCB data package with evidence."
    assert collected["citations"] == ["citation_vn_prices_VCB-prices"]
    assert collected["status"] == "success"
    assert result["output"]["steps"][-1]["kind"] == "skill"
    assert result["output"]["steps"][-1]["status"] == "success"


def test_workflow_passes_rendered_data_records_without_raw_price_series(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    orchestrator = CapturingAgentOrchestrator()
    monkeypatch.setenv("FINMIND_ADMIN_USERNAME", "analyst")
    monkeypatch.setenv("FINMIND_ADMIN_PASSWORD", "secret-pass")
    monkeypatch.setenv("FINMIND_SESSION_SECRET", "session-secret-with-length")
    monkeypatch.setattr(
        "finmind_api.platform.build_default_agent_orchestrator",
        lambda: orchestrator,
    )
    app = create_app()
    with TestClient(app) as test_client:
        login = test_client.post(
            "/api/login",
            json={"username": "analyst", "password": "secret-pass"},
        )
        assert login.status_code == 200
        response, result, _events = _post_workflow_run(
            test_client,
            "vn-financial-data-collector",
            {"market": "VN_STOCK", "symbol": "VCB"},
        )

    assert response.status_code == 200
    assert result is not None
    assert len(orchestrator.requests) == 1
    request = orchestrator.requests[0]
    records = request.context["records"]
    data_bundle = request.context["data_bundle"]
    assert records
    assert all("context" in record for record in records)
    assert any(record["record_type"] == "price_summary" for record in records)
    assert not any(record["record_type"] == "price_series" for record in records)
    assert data_bundle["records"] == records
    assert data_bundle["excluded_record_ids"]
    price_summary = next(
        record for record in records if record["record_type"] == "price_summary"
    )
    assert "year_end_prices" in price_summary["fields"]
    assert "citation_vn_prices_VCB-prices" in data_bundle["citation_ids"]


def test_fundamental_analysis_request_marks_fundamental_record_audited(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    orchestrator = CapturingAgentOrchestrator()
    monkeypatch.setenv("FINMIND_ADMIN_USERNAME", "analyst")
    monkeypatch.setenv("FINMIND_ADMIN_PASSWORD", "secret-pass")
    monkeypatch.setenv("FINMIND_SESSION_SECRET", "session-secret-with-length")
    monkeypatch.setattr(
        "finmind_api.platform.build_default_agent_orchestrator",
        lambda: orchestrator,
    )
    app = create_app()
    with TestClient(app) as test_client:
        login = test_client.post(
            "/api/login",
            json={"username": "analyst", "password": "secret-pass"},
        )
        assert login.status_code == 200
        response, result, _events = _post_workflow_run(
            test_client,
            "vn-fundamental-analysis",
            {"market": "VN_STOCK", "symbol": "VCB"},
        )

    assert response.status_code == 200
    assert result is not None
    assert len(orchestrator.requests) == 2
    request = orchestrator.requests[-1]
    fundamental = next(
        record for record in request.context["data_bundle"]["records"]
        if record["record_type"] == "fundamental"
    )
    assert fundamental["fields"]["is_audited"] is True
    assert "audit_warnings" in fundamental["fields"]


def test_workflow_chart_artifact_uses_structured_price_trend_contract(
    client: TestClient,
) -> None:
    response, result, events = _post_workflow_run(
        client,
        "vn-financial-data-collector",
        {"market": "VN_STOCK", "symbol": "VCB"},
    )

    assert response.status_code == 200
    artifacts = result["output"]["artifacts"]
    assert isinstance(artifacts, list)
    chart = artifacts[0]
    assert chart["artifact_type"] == "chart"
    assert chart["chart_intent"] == "price_trend"
    assert chart["status"] == "ready"
    assert chart["spec"]["supported_views"] == ["line", "candlestick"]
    assert chart["spec"]["default_view"] == "line"
    assert chart["spec"]["x_axis"] == {"field": "date", "type": "time"}
    assert chart["spec"]["series"][0]["name"] == "Close"
    assert chart["spec"]["series"][0]["type"] == "line"
    assert chart["spec"]["series"][0]["data"]
    assert chart["spec"]["candles"]
    assert "table" not in chart
    assert chart["downloads"] == [
        {
            "format": "svg",
            "url": f"/api/artifacts/{chart['artifact_id']}/download?format=svg",
            "filename": "vcb-price-series.svg",
            "mime_type": "image/svg+xml",
        },
        {
            "format": "csv",
            "url": f"/api/artifacts/{chart['artifact_id']}/download?format=csv",
            "filename": "vcb-price-series.csv",
            "mime_type": "text/csv",
        },
    ]
    assert chart["source_refs"]
    artifact_event = next(event for event in events if event["kind"] == "artifact")
    assert artifact_event["payload"] == chart


def test_fundamental_analysis_workflow_runs_collector_audit_and_analysis_steps(
    client: TestClient,
) -> None:
    response, result, _events = _post_workflow_run(
        client,
        "vn-fundamental-analysis",
        {"market": "VN_STOCK", "symbol": "VCB"},
    )

    assert response.status_code == 200
    steps = result["output"]["steps"]
    assert [step["id"] for step in steps] == [
        "collect_data",
        "vn-financial-data-auditor",
        "vn-fundamental-analysis",
    ]
    assert all(step["kind"] == "skill" for step in steps[1:])
    assert all(step["status"] == "success" for step in steps[1:])
    assert result["status"] == "success"
    # upstream-dependent skill has no DATA_REQUIREMENTS, so collect fetches only
    # the auditor's groups
    assert result["output"]["collection"]["requested_dataset_groups"] == [
        "market_price",
        "fundamental",
        "company_profile",
        "news",
    ]
    assert [section["title"] for section in result["output"]["sections"]] == [
        "Fundamental Analysis"
    ]


def test_internal_workflow_steps_do_not_become_user_visible_sections(
    client: TestClient,
) -> None:
    response, result, events = _post_workflow_run(
        client,
        "vn-fundamental-analysis",
        {"market": "VN_STOCK", "symbol": "VCB"},
    )

    assert response.status_code == 200
    assert all(section["title"] != "Collected Data" for section in result["output"]["sections"])
    assert all(
        not (
            event["kind"] == "answer.delta"
            and event["payload"].get("section_title") == "Collected Data"
        )
        for event in events
    )


def test_technical_analysis_workflow_runs_collect_and_analysis_steps(
    client: TestClient,
) -> None:
    response, result, _events = _post_workflow_run(
        client,
        "vn-technical-analysis",
        {"market": "VN_STOCK", "symbol": "VCB"},
    )

    assert response.status_code == 200
    steps = result["output"]["steps"]
    assert [step["id"] for step in steps] == [
        "collect_data",
        "vn-technical-analysis",
    ]
    assert steps[-1]["kind"] == "skill"
    assert steps[-1]["status"] == "success"
    assert result["status"] == "success"
    assert "market_price" in result["output"]["collection"]["requested_dataset_groups"]


def test_agent_orchestrator_stream_skill_requires_litellm_chat_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from finmind_agents.agents.models import AgentRunRequest
    from finmind_agents.agents.orchestrator import AgentOrchestrator, AgentOrchestratorError

    monkeypatch.delenv("LITELLM_CHAT_MODEL", raising=False)

    orchestrator = AgentOrchestrator()

    async def consume() -> None:
        async for _event in orchestrator.stream_skill(
            AgentRunRequest(
                workflow_id="vn-financial-data-collector",
                skill_id="vn-financial-data-collector",
                skill_markdown="# Skill",
                data_requirements=(),
                context={},
                citation_ids=("citation_vn_prices_VCB-2026-06-18",),
            )
        ):
            pass

    with pytest.raises(AgentOrchestratorError, match="LITELLM_CHAT_MODEL"):
        asyncio.run(consume())


def test_workflow_agent_orchestrator_is_langchain_native() -> None:
    source = Path("src/finmind_agents/runtime/service.py").read_text(encoding="utf-8")
    shim = Path("src/finmind_agents/agents/orchestrator.py").read_text(encoding="utf-8")

    assert "agent_core" not in source
    assert "langchain_openai" not in source
    assert "langchain_cohere" not in source
    assert "create_deep_agent" in source
    assert "langchain.agents" not in source
    assert "Compatibility exports" in shim


def test_agent_orchestrator_stream_skill_reports_sanitized_provider_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from finmind_agents.agents.models import AgentRunRequest
    from finmind_agents.agents.orchestrator import AgentOrchestrator, AgentOrchestratorError

    def failing_agent_factory(
        model: str,
        system_prompt: str,
        skill_loader: object,
        use_tools: bool,
    ) -> object:
        raise RuntimeError(
            "OpenAIException - You have no permission to access this resource; "
            "api_key=secret-provider-key"
        )

    monkeypatch.setenv("LITELLM_CHAT_MODEL", "qwen/qwen3.7-plus")

    async def consume() -> None:
        async for _event in AgentOrchestrator(
            agent_factory=failing_agent_factory,
        ).stream_skill(
            AgentRunRequest(
                workflow_id="vn-financial-data-collector",
                skill_id="vn-financial-data-collector",
                skill_markdown="# Skill",
                data_requirements=(),
                context={},
                citation_ids=("citation_vn_prices_DXG-2026-06-26",),
            )
        ):
            pass

    with pytest.raises(AgentOrchestratorError) as error:
        asyncio.run(consume())

    message = str(error.value)
    assert "RuntimeError" in message
    assert "You have no permission to access this resource" in message
    assert "secret-provider-key" not in message
    assert "api_key=<redacted>" in message


def _fake_v3_chat_stream(deltas: tuple[str, ...]) -> object:
    class _TextProjection:
        def __aiter__(self) -> object:
            async def _gen() -> object:
                for delta in deltas:
                    yield delta
            return _gen()

    class _ChatStream:
        @property
        def text(self) -> object:
            return _TextProjection()

    return _ChatStream()


def _fake_v3_run_stream(chat_streams: list[object]) -> object:
    class _RunStream:
        async def __aenter__(self) -> object:
            return self

        async def __aexit__(self, *_exc: object) -> bool:
            return False

        @property
        def messages(self) -> object:
            async def _gen() -> object:
                for chat_stream in chat_streams:
                    yield chat_stream
            return _gen()

    return _RunStream()


def _fake_streaming_agent_factory(chat_streams: list[object]):
    class _StreamingAgent:
        async def astream_events(
            self,
            input: object,
            config: object | None = None,
            *,
            version: str = "v2",
            **_kwargs: object,
        ) -> object:
            assert version == "v3"
            return _fake_v3_run_stream(chat_streams)

    def _factory(
        _model: str,
        _system_prompt: str,
        _skill_loader: object,
        _use_tools: bool,
    ) -> object:
        return _StreamingAgent()

    return _factory


def test_agent_orchestrator_stream_skill_emits_incremental_content_deltas(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from finmind_agents.agents.models import AgentRunRequest
    from finmind_agents.agents.orchestrator import AgentOrchestrator

    class FakeMetadataModel:
        async def ainvoke(self, messages: object) -> object:
            assert messages
            return SimpleNamespace(
                content=(
                    '{"status":"success",'
                    '"citations":["citation_vn_prices_DXG-2026-06-26"],'
                    '"allowed_claims":["data_availability"],'
                    '"blocked_claims":[],"warnings":[]}'
                )
            )

    monkeypatch.setenv("LITELLM_CHAT_MODEL", "gpt-4o-mini")
    monkeypatch.setattr(
        "finmind_agents.runtime.service.build_chat_model",
        lambda settings: FakeMetadataModel(),
    )

    chat_streams = [
        _fake_v3_chat_stream(("VCB momentum ", "remains constructive")),
    ]
    orchestrator = AgentOrchestrator(
        agent_factory=_fake_streaming_agent_factory(chat_streams),
    )

    async def collect_events() -> list[object]:
        events: list[object] = []
        async for event in orchestrator.stream_skill(
            AgentRunRequest(
                workflow_id="vn-financial-data-collector",
                skill_id="vn-financial-data-collector",
                skill_markdown="# Skill",
                data_requirements=(),
                context={},
                citation_ids=("citation_vn_prices_DXG-2026-06-26",),
            )
        ):
            events.append(event)
        return events

    events = asyncio.run(collect_events())
    content_deltas = [event.text for event in events if getattr(event, "kind", "") == "content_delta"]
    result_event = next(event for event in events if getattr(event, "kind", "") == "result")

    assert content_deltas
    assert "".join(content_deltas) == "VCB momentum remains constructive"
    assert result_event.result is not None
    assert result_event.result.content == "VCB momentum remains constructive"


def test_agent_orchestrator_stream_skill_fails_closed_without_async_stream_support(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from finmind_agents.agents.models import AgentRunRequest
    from finmind_agents.agents.orchestrator import AgentOrchestrator
    from finmind_agents.runtime.service import AgentOrchestratorError

    class NonStreamingAgent:
        async def astream_events(
            self,
            input: object,
            config: object | None = None,
            *,
            version: str = "v2",
            **_kwargs: object,
        ) -> object:
            raise NotImplementedError("model does not support event streaming")

    monkeypatch.setenv("LITELLM_CHAT_MODEL", "gpt-4o-mini")

    async def consume() -> None:
        async for _event in AgentOrchestrator(
            agent_factory=lambda *_a, **_k: NonStreamingAgent(),
        ).stream_skill(
            AgentRunRequest(
                workflow_id="vn-financial-data-collector",
                skill_id="vn-financial-data-collector",
                skill_markdown="# Skill",
                data_requirements=(),
                context={},
                citation_ids=("citation_vn_prices_DXG-2026-06-26",),
            )
        ):
            pass

    with pytest.raises(AgentOrchestratorError, match="event streaming"):
        asyncio.run(consume())


def test_run_sync_offloads_work_without_blocking_the_event_loop() -> None:
    from time import sleep

    from finmind_agents.runtime.offload import configure_sync_offload_limit, run_sync

    configure_sync_offload_limit(1)

    async def exercise() -> int:
        ticks = 0

        async def ticker() -> None:
            nonlocal ticks
            for _ in range(3):
                await asyncio.sleep(0.01)
                ticks += 1

        await asyncio.gather(
            run_sync(sleep, 0.05),
            ticker(),
        )
        return ticks

    assert asyncio.run(exercise()) == 3


def test_dataflow_models_serialize_safe_provider_statuses() -> None:
    from finmind_agents.dataflows.models import (
        DataflowProviderResult,
        DataflowCollectionRequest,
        DataflowCollectionResult,
        DatasetGroup,
        CollectionStatus,
    )

    request = DataflowCollectionRequest(
        market=Market.VN_STOCK,
        symbol="VCB",
        dataset_groups=(DatasetGroup.MARKET_PRICE, DatasetGroup.FUNDAMENTAL),
        requested_by="vn-financial-data-collector",
    )
    provider = DataflowProviderResult(
        provider_id="vnstock",
        dataset_groups=(DatasetGroup.MARKET_PRICE,),
        status=CollectionStatus.SUCCESS,
        source_ids=("vnstock_prices",),
        warnings=(),
    )
    result = DataflowCollectionResult(
        collection_id="collection_test",
        market=request.market,
        symbol=request.symbol,
        requested_dataset_groups=request.dataset_groups,
        provider_results=(provider,),
        records=(),
        source_documents=(),
        status=CollectionStatus.SUCCESS,
        warnings=(),
        failure_reasons=(),
    )

    serialized = result.to_output()

    assert serialized["collection_id"] == "collection_test"
    assert serialized["requested_dataset_groups"] == ["market_price", "fundamental"]
    assert serialized["provider_results"][0]["provider_id"] == "vnstock"
    assert "raw" not in str(serialized).lower()
    assert "secret" not in str(serialized).lower()


def test_dataflow_registry_selects_providers_by_market_and_dataset_group() -> None:
    from finmind_agents.dataflows.models import DatasetGroup
    from finmind_agents.dataflows.registry import build_default_provider_registry

    registry = build_default_provider_registry()

    vn_providers = registry.providers_for(
        market=Market.VN_STOCK,
        dataset_groups=(DatasetGroup.MARKET_PRICE, DatasetGroup.FUNDAMENTAL),
    )
    assert {provider.provider_id for provider in vn_providers} == {"vnstock"}


def test_smoke_script_builds_workflow_service_without_removed_provider_kwargs() -> None:
    script_path = Path(__file__).resolve().parents[1] / "test.py"
    spec = importlib.util.spec_from_file_location("finmind_smoke_script", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    workflow_service = module.create_workflow_service_from_env()

    assert workflow_service.list_workflows()


def test_vn_data_provider_env_rejects_offline_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from finmind_api.settings import Settings, SettingsError

    monkeypatch.setenv("FINMIND_ADMIN_USERNAME", "analyst")
    monkeypatch.setenv("FINMIND_ADMIN_PASSWORD", "secret-pass")
    monkeypatch.setenv("FINMIND_SESSION_SECRET", "session-secret-with-length")
    monkeypatch.setenv("FINMIND_VN_DATA_PROVIDER", "offline")

    with pytest.raises(SettingsError, match="must be vnstock"):
        Settings.from_env()


def test_vn_data_provider_env_defaults_to_vnstock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from finmind_api.settings import Settings

    monkeypatch.setenv("FINMIND_ADMIN_USERNAME", "analyst")
    monkeypatch.setenv("FINMIND_ADMIN_PASSWORD", "secret-pass")
    monkeypatch.setenv("FINMIND_SESSION_SECRET", "session-secret-with-length")
    monkeypatch.delenv("FINMIND_VN_DATA_PROVIDER", raising=False)
    monkeypatch.delenv("VN_DATA_PROVIDER", raising=False)

    assert Settings.from_env().vn_data_provider == "vnstock"


def test_bare_vn_data_provider_env_rejects_offline_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from finmind_api.settings import Settings, SettingsError

    monkeypatch.setenv("FINMIND_ADMIN_USERNAME", "analyst")
    monkeypatch.setenv("FINMIND_ADMIN_PASSWORD", "secret-pass")
    monkeypatch.setenv("FINMIND_SESSION_SECRET", "session-secret-with-length")
    monkeypatch.delenv("FINMIND_VN_DATA_PROVIDER", raising=False)
    monkeypatch.setenv("VN_DATA_PROVIDER", "offline")

    with pytest.raises(SettingsError, match="must be vnstock"):
        Settings.from_env()


def test_vnstock_api_key_env_is_supported(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from finmind_api.settings import Settings

    monkeypatch.setenv("FINMIND_ADMIN_USERNAME", "analyst")
    monkeypatch.setenv("FINMIND_ADMIN_PASSWORD", "secret-pass")
    monkeypatch.setenv("FINMIND_SESSION_SECRET", "session-secret-with-length")
    monkeypatch.setenv("FINMIND_VNSTOCK_API_KEY", "vnstock-secret")

    assert Settings.from_env().vnstock_api_key == "vnstock-secret"


def test_vnstock_provider_fetches_live_price_and_fundamental_records(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from finmind_agents.dataflows.models import DataflowCollectionRequest, DatasetGroup
    from finmind_agents.dataflows.providers.vnstock import VnstockProvider

    class FakeEquityMarket:
        def ohlcv(self, **kwargs: object) -> list[dict[str, object]]:
            assert kwargs["resolution"] == "1D"
            return [
                {
                    "time": "2026-06-27",
                    "close": 61200,
                    "change_percent": 1.7,
                    "volume": 5100000,
                }
            ]

    class FakeEquityFundamental:
        def income_statement(self, **kwargs: object) -> list[dict[str, object]]:
            assert kwargs["source"] == "vci"
            assert kwargs["period"] == "year"
            return [
                {"item": "EPS", "item_id": "eps_basic_vnd", "2025": 5400, "2024": 5100},
                {"item": "Net profit", "item_id": "net_profit_loss_after_tax",
                 "2025": 54000, "2024": 48000},
            ]

        def balance_sheet(self, **kwargs: object) -> list[dict[str, object]]:
            assert kwargs["source"] == "vci"
            assert kwargs["period"] == "year"
            return [
                {"item": "Equity", "item_id": "owners_equity", "2025": 270000, "2024": 240000},
                {"item": "Assets", "item_id": "total_assets", "2025": 3000000, "2024": 2800000},
            ]

    fake_vnstock = SimpleNamespace(
        Market=lambda: SimpleNamespace(
            equity=lambda symbol: FakeEquityMarket(),
        ),
        Fundamental=lambda: SimpleNamespace(
            equity=lambda symbol: FakeEquityFundamental(),
        ),
    )
    monkeypatch.setitem(sys.modules, "vnstock", fake_vnstock)

    result = VnstockProvider().fetch(
        DataflowCollectionRequest(
            market=Market.VN_STOCK,
            symbol="VCB",
           dataset_groups=(DatasetGroup.MARKET_PRICE, DatasetGroup.FUNDAMENTAL),
           requested_by="vn-financial-data-collector",
       )
   )

    assert result.provider_result.status == "success"
    assert {record.dataset_id for record in result.records} == {
        "vn_prices",
        "vn_fundamentals",
    }
    price = next(record for record in result.records if record.dataset_id == "vn_prices")
    fundamentals = next(
        record for record in result.records if record.dataset_id == "vn_fundamentals"
    )
    assert price.payload["series"][0]["close"] == 61200
    assert fundamentals.payload["eps"] == 5400
    assert fundamentals.payload["roe_percent"] == 20.0
    assert result.provider_result.source_ids == (
        "vnstock_fundamentals",
        "vnstock_prices",
    )


def test_vnstock_provider_falls_back_to_overview_when_statements_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from finmind_agents.dataflows.models import DataflowCollectionRequest, DatasetGroup
    from finmind_agents.dataflows.providers.vnstock import VnstockProvider

    class FakeEquityMarket:
        def ohlcv(self, **kwargs: object) -> list[dict[str, object]]:
            assert kwargs["source"] == "vci"
            return [{"time": "2026-06-27", "close": 14.2, "volume": 1200000}]

    class FakeEquityFundamental:
        def income_statement(self, **kwargs: object) -> list[dict[str, object]]:
            return []

        def balance_sheet(self, **kwargs: object) -> list[dict[str, object]]:
            return []

    class FakeCompany:
        def __init__(self, **kwargs: object) -> None:
            assert kwargs["source"] == "vci"
            assert kwargs["symbol"] == "DXG"

        def overview(self) -> list[dict[str, object]]:
            return [
                {
                    "symbol": "DXG",
                    "exchange": "HOSE",
                    "issue_share": 1268104965,
                    "market_cap": 18000000000000,
                    "free_float": 0.35,
                    "free_float_percentage": 35.0,
                    "sector": "Real Estate",
                    "as_of_date": "2025-12-31T00:00:00",
                }
            ]

    fake_vnstock = SimpleNamespace(
        Market=lambda: SimpleNamespace(equity=lambda symbol: FakeEquityMarket()),
        Fundamental=lambda: SimpleNamespace(equity=lambda symbol: FakeEquityFundamental()),
        Company=FakeCompany,
    )
    monkeypatch.setitem(sys.modules, "vnstock", fake_vnstock)

    result = VnstockProvider().fetch(
        DataflowCollectionRequest(
            market=Market.VN_STOCK,
            symbol="DXG",
            dataset_groups=(DatasetGroup.MARKET_PRICE, DatasetGroup.FUNDAMENTAL, DatasetGroup.COMPANY_PROFILE),
            requested_by="vn-financial-data-collector",
        )
    )

    assert result.provider_result.status == "partial"
    assert {record.dataset_id for record in result.records} == {
        "vn_prices",
        "vn_fundamentals",
        "vn_company_profile",
    }
    fundamentals = next(
        record for record in result.records if record.dataset_id == "vn_fundamentals"
    )
    assert fundamentals.source_id == "vnstock_company_overview"
    assert fundamentals.payload["outstanding_shares"] == 1268104965
    assert fundamentals.payload["sector"] == "Real Estate"
    profile = next(
        record for record in result.records if record.dataset_id == "vn_company_profile"
    )
    assert profile.payload["company_name"] is None  # fake overview has no organ_name
    assert profile.payload["outstanding_shares"] == 1268104965
    assert profile.payload["market_cap"] == 18000000000000
    assert profile.payload["pe"] is None  # statements unavailable -> no eps
    assert "vnstock_finance_fetch_failed" in result.provider_result.warnings


def test_vnstock_provider_registers_api_key_before_fetch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from finmind_agents.dataflows.models import DataflowCollectionRequest, DatasetGroup
    from finmind_agents.dataflows.providers.vnstock import VnstockProvider

    registered: list[str] = []

    class FakeEquityMarket:
        def ohlcv(self, **kwargs: object) -> list[dict[str, object]]:
            assert registered == ["vnstock-secret"]
            return [{"time": "2026-06-27", "close": 61200}]

    fake_vnstock = SimpleNamespace(
        register_user=lambda api_key: registered.append(api_key),
        Market=lambda: SimpleNamespace(equity=lambda symbol: FakeEquityMarket()),
        Fundamental=lambda: SimpleNamespace(equity=SimpleNamespace()),
    )
    monkeypatch.setitem(sys.modules, "vnstock", fake_vnstock)

    result = VnstockProvider(api_key="vnstock-secret").fetch(
        DataflowCollectionRequest(
            market=Market.VN_STOCK,
            symbol="VCB",
            dataset_groups=(DatasetGroup.MARKET_PRICE,),
            requested_by="vn-financial-data-collector",
        )
    )

    assert result.provider_result.status == "success"
    assert "vnstock-secret" not in str(result.provider_result)


def test_vnstock_provider_registration_failure_does_not_leak_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from finmind_agents.dataflows.models import DataflowCollectionRequest, DatasetGroup
    from finmind_agents.dataflows.providers.vnstock import VnstockProvider

    def fail_register(api_key: str) -> None:
        raise RuntimeError(f"bad key {api_key}")

    fake_vnstock = SimpleNamespace(
        register_user=fail_register,
        Market=lambda: SimpleNamespace(equity=SimpleNamespace()),
        Fundamental=lambda: SimpleNamespace(equity=SimpleNamespace()),
    )
    monkeypatch.setitem(sys.modules, "vnstock", fake_vnstock)

    result = VnstockProvider(api_key="vnstock-secret").fetch(
        DataflowCollectionRequest(
            market=Market.VN_STOCK,
            symbol="VCB",
            dataset_groups=(DatasetGroup.MARKET_PRICE,),
            requested_by="vn-financial-data-collector",
        )
    )

    assert result.provider_result.status == "failed"
    assert result.provider_result.warnings == ("vnstock_registration_failed",)
    assert "vnstock-secret" not in str(result.provider_result)


def test_workflow_run_returns_cited_chart_result(
    client: TestClient,
) -> None:
    response, result, _events = _post_workflow_run(
        client,
        "vn-financial-data-collector",
        {"market": "VN_STOCK", "symbol": "VCB"},
    )

    assert response.status_code == 200
    assert result["kind"] == "workflow"
    assert result["status"] == "success"
    assert result["inputs"]["symbol"] == "VCB"
    assert result["output"]["grounding"]["grounding_status"] == "pass"
    analysis_section = next(
        section
        for section in result["output"]["sections"]
        if section["title"] == "Collected Data"
    )
    assert analysis_section["citations"]
    assert result["output"]["citations"]
    assert result["output"]["citations"][0]["dataset_id"] in {"vn_prices", "vn_fundamentals"}
    assert result["output"]["citations"][0]["source_id"]
    assert result["output"]["citations"][0]["timestamp"]
    collection = result["output"]["collection"]
    assert collection["collection_id"].startswith("collection_")
    assert "market_price" in collection["requested_dataset_groups"]
    assert collection["provider_results"]
    assert "raw" not in str(collection).lower()
    assert "secret" not in str(collection).lower()
    chart = result["output"]["artifacts"][0]
    assert chart["artifact_type"] == "chart"
    assert chart["spec"]["series"]
    assert chart["source_refs"]
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
    response, result, _events = _post_workflow_run(
        client,
        "vn-financial-data-collector",
        {"market": "VN_STOCK", "symbol": "VCB"},
    )

    assert response.status_code == 200
    section = next(
        item
        for item in result["output"]["sections"]
        if item["title"] == "Collected Data"
    )
    chart = result["output"]["artifacts"][0]

    assert result["inputs"]["symbol"] == "VCB"
    assert "Agent-collected VCB data package" in section["content"]
    assert "VNINDEX" not in section["content"]
    assert chart["spec"]["candles"] == [
        {
            "date": "2026-06-18",
            "open": 58200,
            "high": 58200,
            "low": 58200,
            "close": 58200,
            "volume": 4920000,
        },
    ]


def test_invalid_workflow_input_does_not_create_successful_run(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/workflows/vn-financial-data-collector/runs",
        json={"market": "INVALID_MARKET", "symbol": "INVALID"},
    )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert "supports VN stocks only" in detail


@pytest.mark.parametrize(
    ("payload", "expected_detail"),
    [
        ({"market": "INVALID_MARKET", "symbol": "INVALID"}, "supports VN stocks only"),
        ({"market": "VN_STOCK"}, "symbol is required"),
    ],
)
def test_unsupported_or_missing_workflow_inputs_are_rejected(
    client: TestClient,
    payload: dict[str, str],
    expected_detail: str,
) -> None:
    response = client.post("/api/workflows/vn-financial-data-collector/runs", json=payload)

    assert response.status_code == 422
    assert expected_detail in response.json()["detail"]


def test_missing_market_data_emits_failed_stream_event_and_failed_run(
    client: TestClient,
) -> None:
    response, run, events = _post_workflow_run(
        client,
        "vn-financial-data-collector",
        {"market": "VN_STOCK", "symbol": "ZZZ"},
    )
    runs = client.get("/api/runs")

    assert response.status_code == 200
    assert runs.status_code == 200
    assert run is None
    failed = _failed_event_from_events(events)
    assert "Market data provider is unavailable" in failed["payload"]["message"]
    assert runs.json()[0]["status"] == "failed"


def test_workflow_catalog_remains_provider_neutral(client: TestClient) -> None:
    response = client.get("/api/workflows")

    assert response.status_code == 200
    catalog_text = str(response.json()).lower()
    assert "vnstock" not in catalog_text


def test_unsupported_market_validation_stops_before_dataflow_calls(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from finmind_agents.dataflows.service import DataflowService

    def fail_collect(self: DataflowService, request: object) -> object:
        raise AssertionError("dataflows should not run for invalid market")

    monkeypatch.setattr(DataflowService, "collect", fail_collect)

    response = client.post(
        "/api/workflows/vn-financial-data-collector/runs",
        json={"market": "INVALID_MARKET", "symbol": "INVALID"},
    )

    assert response.status_code == 422


def test_unknown_run_returns_404(client: TestClient) -> None:
    response = client.get("/api/runs/run_missing")

    assert response.status_code == 404
    assert response.json()["detail"] == "Run not found"


def test_completed_workflow_run_can_be_reopened_from_history(
    client: TestClient,
) -> None:
    run_response, result, _events = _post_workflow_run(
        client,
        "vn-financial-data-collector",
        {"market": "VN_STOCK", "symbol": "VCB"},
    )

    list_response = client.get("/api/runs")
    detail_response = client.get(f"/api/runs/{result['id']}")

    assert run_response.status_code == 200
    assert result["status"] == "success"
    assert result["output"]["collection"]["provider_results"]
    assert list_response.status_code == 200
    assert list_response.json()[0] == result
    assert detail_response.status_code == 200
    assert detail_response.json() == result



def test_run_can_be_renamed_and_the_title_persists(client: TestClient) -> None:
    run_response, run, _events = _post_workflow_run(
        client,
        "vn-financial-data-collector",
        {"market": "VN_STOCK", "symbol": "VCB"},
    )
    assert run_response.status_code == 200
    run_id = run["id"]
    assert run["title"] is None

    rename_response = client.patch(
        f"/api/runs/{run_id}",
        json={"title": "VCB snapshot Q2"},
    )

    assert rename_response.status_code == 200
    assert rename_response.json()["title"] == "VCB snapshot Q2"

    detail_response = client.get(f"/api/runs/{run_id}")
    assert detail_response.status_code == 200
    assert detail_response.json()["title"] == "VCB snapshot Q2"

    list_response = client.get("/api/runs")
    assert list_response.status_code == 200
    assert list_response.json()[0]["title"] == "VCB snapshot Q2"


def test_rename_run_rejects_empty_title(client: TestClient) -> None:
    _run_response, run, _events = _post_workflow_run(
        client,
        "vn-financial-data-collector",
        {"market": "VN_STOCK", "symbol": "VCB"},
    )
    run_id = run["id"]

    rename_response = client.patch(
        f"/api/runs/{run_id}",
        json={"title": "   "},
    )

    assert rename_response.status_code == 422
    assert rename_response.json()["detail"] == "title must not be empty"


def test_rename_run_returns_404_for_unknown_run(client: TestClient) -> None:
    rename_response = client.patch(
        "/api/runs/run_does_not_exist",
        json={"title": "missing"},
    )

    assert rename_response.status_code == 404
    assert rename_response.json()["detail"] == "Run not found"


def test_run_can_be_deleted_and_disappears_from_history(
    client: TestClient,
) -> None:
    _run_response, run, _events = _post_workflow_run(
        client,
        "vn-financial-data-collector",
        {"market": "VN_STOCK", "symbol": "VCB"},
    )
    run_id = run["id"]

    delete_response = client.delete(f"/api/runs/{run_id}")

    assert delete_response.status_code == 204

    detail_response = client.get(f"/api/runs/{run_id}")
    assert detail_response.status_code == 404

    list_response = client.get("/api/runs")
    assert all(run["id"] != run_id for run in list_response.json())


def test_delete_run_returns_404_for_unknown_run(client: TestClient) -> None:
    delete_response = client.delete("/api/runs/run_does_not_exist")

    assert delete_response.status_code == 404
    assert delete_response.json()["detail"] == "Run not found"


def test_build_run_store_fails_closed_without_database_url(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The product run store is PostgreSQL; the app must fail closed when the
    DSN is missing instead of silently falling back to a non-durable store."""
    from finmind_api.settings import Settings, SettingsError

    monkeypatch.setenv("FINMIND_ADMIN_USERNAME", "analyst")
    monkeypatch.setenv("FINMIND_ADMIN_PASSWORD", "secret-pass")
    monkeypatch.setenv("FINMIND_SESSION_SECRET", "session-secret-with-length")
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("FINMIND_DATABASE_URL", raising=False)
    settings = Settings.from_env()

    with pytest.raises(SettingsError, match="FINMIND_DATABASE_URL"):
        _real_build_run_store(settings)


def test_with_heartbeats_emits_keepalive_when_idle_and_forwards_frames() -> None:
    import asyncio as _asyncio

    from finmind_api.streaming import HEARTBEAT_FRAME, with_heartbeats

    async def frame_source():
        yield b"event: run.stage\ndata: {\"kind\":\"run.stage\"}\n\n"
        await _asyncio.sleep(0.05)
        yield b"event: answer.delta\ndata: {\"kind\":\"answer.delta\"}\n\n"

    async def collect() -> list[bytes]:
        frames: list[bytes] = []
        async for frame in with_heartbeats(frame_source(), interval=0.01):
            frames.append(frame)
        return frames

    frames = _asyncio.run(collect())
    assert frames[0] == b"event: run.stage\ndata: {\"kind\":\"run.stage\"}\n\n"
    assert HEARTBEAT_FRAME in frames
    assert frames[-1] == b"event: answer.delta\ndata: {\"kind\":\"answer.delta\"}\n\n"


def test_with_heartbeats_disabled_when_interval_is_zero() -> None:
    import asyncio as _asyncio

    from finmind_api.streaming import HEARTBEAT_FRAME, with_heartbeats

    async def frame_source():
        yield b"a\n\n"
        yield b"b\n\n"

    async def collect() -> list[bytes]:
        frames: list[bytes] = []
        async for frame in with_heartbeats(frame_source(), interval=0):
            frames.append(frame)
        return frames

    frames = _asyncio.run(collect())
    assert frames == [b"a\n\n", b"b\n\n"]
    assert HEARTBEAT_FRAME not in frames


def _synthetic_pattern_series() -> list[dict[str, object]]:
    closes = [
        120, 118, 116, 114, 112, 110, 108, 106, 104, 102,
        100, 98, 96, 94, 92, 90, 92, 95, 98, 101,
        104, 107, 110, 113, 116, 114, 112, 109, 106, 103,
        100, 97, 94, 91, 89, 90, 93, 97, 101, 105,
        109, 113, 116, 118, 120, 121, 122, 121, 120, 119,
        118, 119, 120, 121, 122, 123, 124, 125, 126, 127,
    ]
    rows: list[dict[str, object]] = []
    for index, close in enumerate(closes, start=1):
        rows.append(
            {
                "date": f"2026-03-{index:02d}",
                "open": close - 1,
                "high": close + 2,
                "low": close - 2,
                "close": close,
                "volume": 1_000_000 + index * 1000,
            }
        )
    return rows


def test_data_record_builders_render_expected_contexts() -> None:
    from datetime import UTC, datetime

    from finmind_agents.evidence.builders import build_data_bundle
    from finmind_agents.models import CanonicalMarketDataRecord

    price_record = CanonicalMarketDataRecord(
        dataset_id="vn_prices",
        record_key="VCB-prices",
        instrument_id="VCB",
        market_time=datetime(2026, 6, 18, 7, 0, tzinfo=UTC),
        collected_at=datetime(2026, 6, 18, 8, 0, tzinfo=UTC),
        source_id="vnstock_prices",
        payload={
            "series": _synthetic_pattern_series(),
            "count": 60,
            "start_date": "2026-03-01",
            "end_date": "2026-03-60",
            "interval": "1D",
        },
    )
    fundamental_record = CanonicalMarketDataRecord(
        dataset_id="vn_fundamentals",
        record_key="VCB-FY2025",
        instrument_id="VCB",
        market_time=datetime(2026, 3, 31, 7, 0, tzinfo=UTC),
        collected_at=datetime(2026, 6, 18, 8, 0, tzinfo=UTC),
        source_id="vnstock_fundamentals",
        payload={"period": "FY2025", "eps": 5200, "roe_percent": 20.3},
    )
    company_profile_record = CanonicalMarketDataRecord(
        dataset_id="vn_company_profile",
        record_key="VCB-profile",
        instrument_id="VCB",
        market_time=datetime(2026, 6, 18, 7, 0, tzinfo=UTC),
        collected_at=datetime(2026, 6, 18, 8, 0, tzinfo=UTC),
        source_id="vnstock_company_profile",
        payload={"company_name": "VCB", "industry": "Banking"},
    )
    indicator_record = CanonicalMarketDataRecord(
        dataset_id="vn_indicators",
        record_key="VCB-indicators",
        instrument_id="VCB",
        market_time=datetime(2026, 6, 18, 7, 0, tzinfo=UTC),
        collected_at=datetime(2026, 6, 18, 8, 0, tzinfo=UTC),
        source_id="computed_indicators",
        payload={"latest_date": "2026-06-18", "latest_close": 127, "trend": "uptrend", "ema10": 120, "sma20": 118, "sma50": 112, "rsi14": 61, "macd_line": 1.2, "macd_signal": 0.8, "macd_histogram": 0.4, "support": 116, "resistance": 128, "volume_ratio": 1.4},
    )
    bundle = build_data_bundle((price_record, fundamental_record, company_profile_record, indicator_record))

    record_types = {record.record_type for record in bundle.records}
    assert "price_series" in record_types
    assert "price_summary" in record_types
    assert "pattern_evidence" in record_types
    assert "pattern_setup" in record_types
    assert "fundamental" in record_types
    assert "company_profile" in record_types
    assert "indicator" in record_types
    for record in bundle.records:
        assert record.record_id
        assert record.context
        assert record.citation_id
    assert bundle.to_prompt_payload()["excluded_record_ids"] == []


def test_pattern_evidence_builder_detects_double_bottom_and_divergence() -> None:
    from finmind_agents.evidence.patterns import detect_pattern_evidence

    payload = detect_pattern_evidence(_synthetic_pattern_series())
    patterns = {pattern["pattern_id"]: pattern for pattern in payload["detected_patterns"]}

    assert "double_bottom" in patterns
    assert patterns["double_bottom"]["verdict"] == "detected"
    assert "rsi_divergence" in patterns or "rsi_bullish_divergence" in patterns


def test_pattern_setup_builder_returns_ranked_candidates() -> None:
    from finmind_agents.evidence.patterns import detect_pattern_setups

    payload = detect_pattern_setups(_synthetic_pattern_series())

    assert payload["setups"]
    assert payload["setups"][0]["completion_score"] >= payload["setups"][-1]["completion_score"]
    assert payload["setups"][0]["setup_status"] in {"near_confirmation", "forming", "not_clean"}


def test_mark_fundamentals_audited_sets_audit_gate() -> None:
    from datetime import UTC, datetime

    from finmind_agents.data_records import FundamentalRecord
    from finmind_agents.evidence.builders import mark_fundamentals_audited

    record = FundamentalRecord(
        record_id="fundamental:VCB",
        record_type="fundamental",
        dataset_id="vn_fundamentals",
        instrument_id="VCB",
        market_time=datetime(2026, 3, 31, 7, 0, tzinfo=UTC),
        collected_at=datetime(2026, 6, 18, 8, 0, tzinfo=UTC),
        source_id="vnstock_fundamentals",
        payload={"period": "FY2025", "eps": 5200, "is_audited": False},
        citation_id="citation_vn_fundamentals_VCB-FY2025",
        label="VCB fundamentals",
    )

    audited = mark_fundamentals_audited((record,))[0]

    assert audited.payload["is_audited"] is True
    assert audited.context


def test_grounding_rejects_unknown_citation_ids() -> None:
    from finmind_agents.workflows.grounding import citations_within_allowlist, uncited_citations

    assert citations_within_allowlist(("cite_1",), ("cite_1", "cite_2")) is True
    assert citations_within_allowlist(("cite_3",), ("cite_1", "cite_2")) is False
    assert uncited_citations(("cite_1", "cite_3"), ("cite_1", "cite_2")) == ("cite_3",)


def test_prompt_payload_uses_data_bundle_and_citation_allowlist() -> None:
    from finmind_agents.agents.models import AgentRunRequest
    from finmind_agents.agents.prompts import build_skill_answer_prompt

    request = AgentRunRequest(
        workflow_id="vn-technical-analysis",
        skill_id="vn-technical-analysis",
        skill_markdown="# Skill",
        data_requirements=(),
        context={
            "data_bundle": {
                "bundle_id": "bundle_1",
                "records": [{"record_id": "r1", "record_type": "indicator", "context": "x"}],
                "citation_ids": ["cite_1"],
                "excluded_record_ids": ["raw_prices"],
                "methodology_versions": ["indicators.v1"],
            }
        },
        citation_ids=("cite_1",),
    )

    prompt = build_skill_answer_prompt(request)

    assert '"data_bundle"' in prompt
    assert '"excluded_record_ids": ["raw_prices"]' in prompt
    assert '"allowed_citation_ids": ["cite_1"]' in prompt
