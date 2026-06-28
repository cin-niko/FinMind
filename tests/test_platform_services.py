from collections.abc import Iterator
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from finmind_agents.models import Market
from finmind_agents.workflows.catalog import build_workflow_catalog
from finmind_api.app import create_app


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
    def run_skill(self, request: object) -> object:
        from finmind_agents.agents.models import AgentRunResult

        return AgentRunResult(
            status="success",
            section_title="Collected Data",
            content="Agent-collected VCB data package with evidence.",
            citations=("citation_vn_prices_VCB-2026-06-18",),
            allowed_claims=("data_availability",),
            blocked_claims=(),
            warnings=(),
        )


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("FINMIND_ADMIN_USERNAME", "analyst")
    monkeypatch.setenv("FINMIND_ADMIN_PASSWORD", "secret-pass")
    monkeypatch.setenv("FINMIND_SESSION_SECRET", "session-secret-with-length")
    monkeypatch.setenv("FINMIND_VN_DATA_PROVIDER", "offline")
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
    assert workflow_ids == {"vn-financial-data-collector"}
    assert "gold-brief" not in workflow_ids
    assert all(workflow["requires_citations"] for workflow in workflows)
    assert all("stages" in workflow for workflow in workflows)
    collector = workflows[0]
    assert collector["workflow_type"] == "atomic"
    assert collector["market_scope"] == ["VN_STOCK"]
    assert collector["output_sections"] == [
        "Data Quality",
        "Collected Data",
    ]


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
            "vn-financial-data-collector",
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
        "src/finmind_agents/workflows/skills/vn-financial-data-collector/DATA_REQUIREMENTS.yaml"
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
        DataflowRetrievalRequest,
        DataRequirement,
        DatasetGroup,
    )

    request = DataflowRetrievalRequest(
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


def test_agent_retrieval_plan_rejects_undeclared_dataset() -> None:
    from finmind_agents.dataflows.models import AgentRetrievalPlan, DataRequirement
    from finmind_agents.dataflows.requirements import (
        RetrievalPlanError,
        validate_agent_retrieval_plan,
    )

    plan = AgentRetrievalPlan(
        skill_id="vn-financial-data-collector",
        market=Market.VN_STOCK,
        symbol="DXG",
        required_requests=(DataRequirement(dataset="ohlcv"),),
        optional_requests=(DataRequirement(dataset="news"),),
        policy_id="workflow_strict",
    )

    with pytest.raises(RetrievalPlanError, match="not declared"):
        validate_agent_retrieval_plan(
            plan,
            declared_requirements=(DataRequirement(dataset="ohlcv"),),
            allow_optional=True,
        )


def test_dataflow_service_passes_effective_groups_to_provider() -> None:
    from finmind_agents.dataflows.models import (
        DataflowProviderResult,
        DataflowRetrievalRequest,
        DataRequirement,
        DatasetGroup,
        RetrievalStatus,
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

        def fetch(self, request: DataflowRetrievalRequest) -> ProviderFetchResult:
            seen_groups.append(request.dataset_groups)
            return ProviderFetchResult(
                provider_result=DataflowProviderResult(
                    provider_id=self.provider_id,
                    dataset_groups=request.dataset_groups,
                    status=RetrievalStatus.FAILED,
                    warnings=("no_data",),
                    failure_reason="test provider has no data",
                )
            )

    DataflowService(
        registry=DataflowProviderRegistry(providers=(RecordingProvider(),))
    ).retrieve(
        DataflowRetrievalRequest(
            market=Market.VN_STOCK,
            symbol="DXG",
            requested_by="test",
            data_requirements=(DataRequirement(dataset="ohlcv"),),
            allow_fallback=False,
        )
    )

    assert seen_groups == [(DatasetGroup.MARKET_PRICE,)]


def test_collector_workflow_uses_skill_data_requirements(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/workflows/vn-financial-data-collector/run",
        json={"market": "VN_STOCK", "symbol": "VCB"},
    )

    assert response.status_code == 200
    result = response.json()
    assert result["output"]["collection"]["requested_dataset_groups"] == [
        "market_price",
        "fundamental",
        "news",
    ]


def test_workflow_uses_agent_skill_output(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/workflows/vn-financial-data-collector/run",
        json={"market": "VN_STOCK", "symbol": "VCB"},
    )

    assert response.status_code == 200
    result = response.json()
    collected = next(
        section
        for section in result["output"]["sections"]
        if section["title"] == "Collected Data"
    )

    assert collected["content"] == "Agent-collected VCB data package with evidence."
    assert collected["citations"] == ["citation_vn_prices_VCB-2026-06-18"]
    assert result["output"]["agent"]["status"] == "success"
    assert result["output"]["agent"]["retrieval_plan_status"] == "executed"


def test_agent_orchestrator_requires_litellm_chat_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from finmind_agents.agents.models import AgentRunRequest
    from finmind_agents.agents.orchestrator import AgentOrchestrator, AgentOrchestratorError

    monkeypatch.delenv("LITELLM_CHAT_MODEL", raising=False)

    orchestrator = AgentOrchestrator()

    with pytest.raises(AgentOrchestratorError, match="LITELLM_CHAT_MODEL"):
        orchestrator.run_skill(
            AgentRunRequest(
                workflow_id="vn-financial-data-collector",
                skill_id="vn-financial-data-collector",
                skill_markdown="# Skill",
                data_requirements=(),
                context={},
                evidence_ids=("citation_vn_prices_VCB-2026-06-18",),
            )
        )


def test_workflow_agent_orchestrator_is_langchain_native() -> None:
    source = Path("src/finmind_agents/runtime/service.py").read_text(encoding="utf-8")
    shim = Path("src/finmind_agents/agents/orchestrator.py").read_text(encoding="utf-8")

    assert "agent_core" not in source
    assert "langchain_openai" not in source
    assert "langchain_cohere" not in source
    assert "create_deep_agent" in source
    assert "langchain.agents" not in source
    assert "Compatibility exports" in shim


def test_agent_orchestrator_accepts_json_chat_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from finmind_agents.agents.models import AgentRunRequest
    from finmind_agents.agents.orchestrator import AgentOrchestrator

    class JsonDeepAgent:
        def invoke(self, input: dict[str, object]) -> dict[str, object]:
            assert input["messages"]
            return {
                "messages": [
                    {
                        "content": (
                            '{"status":"success","section_title":"Collected Data",'
                            '"content":"DXG data was collected with partial provider coverage.",'
                            '"citations":["citation_vn_prices_DXG-2026-06-26"],'
                            '"allowed_claims":["data_availability"],'
                            '"blocked_claims":["valuation_context"],'
                            '"warnings":["vnstock_finance_fetch_failed"]}'
                        )
                    }
                ]
            }

    def fake_agent_factory(
        model: str,
        system_prompt: str,
        skill_loader: object,
        use_tools: bool,
    ) -> JsonDeepAgent:
        assert model == "command-r"
        assert "guarded financial workflow agent" in system_prompt
        assert callable(skill_loader)
        assert skill_loader("vn-financial-data-collector") == "# Skill"
        assert use_tools is False
        return JsonDeepAgent()

    monkeypatch.setenv("LITELLM_CHAT_MODEL", "command-r")

    result = AgentOrchestrator(agent_factory=fake_agent_factory).run_skill(
        AgentRunRequest(
            workflow_id="vn-financial-data-collector",
            skill_id="vn-financial-data-collector",
            skill_markdown="# Skill",
            data_requirements=(),
            context={},
            evidence_ids=("citation_vn_prices_DXG-2026-06-26",),
        )
    )

    assert result.status == "success"
    assert result.section_title == "Collected Data"
    assert result.citations == ("citation_vn_prices_DXG-2026-06-26",)


def test_agent_orchestrator_coerces_structured_content_to_string(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from finmind_agents.agents.models import AgentRunRequest
    from finmind_agents.agents.orchestrator import AgentOrchestrator

    class StructuredContentDeepAgent:
        def invoke(self, input: dict[str, object]) -> dict[str, object]:
            return {
                "messages": [
                    {
                        "content": (
                            '{"status":"partial","section_title":"Collected Data",'
                            '"content":{"market":"VN_STOCK","ticker":"DXG"},'
                            '"citations":["citation_vn_prices_DXG-2026-06-26"],'
                            '"allowed_claims":["data_availability"],'
                            '"blocked_claims":["valuation_context"],'
                            '"warnings":["vnstock_finance_fetch_failed"]}'
                        )
                    }
                ]
            }

    monkeypatch.setenv("LITELLM_CHAT_MODEL", "command-r7b-12-2024")

    result = AgentOrchestrator(
        agent_factory=lambda model, system_prompt, skill_loader, use_tools: (
            StructuredContentDeepAgent()
        )
    ).run_skill(
        AgentRunRequest(
            workflow_id="vn-financial-data-collector",
            skill_id="vn-financial-data-collector",
            skill_markdown="# Skill",
            data_requirements=(),
            context={},
            evidence_ids=("citation_vn_prices_DXG-2026-06-26",),
        )
    )

    assert result.status == "partial"
    assert '"ticker": "DXG"' in result.content


def test_agent_orchestrator_reports_sanitized_provider_error(
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

    with pytest.raises(AgentOrchestratorError) as error:
        AgentOrchestrator(agent_factory=failing_agent_factory).run_skill(
            AgentRunRequest(
                workflow_id="vn-financial-data-collector",
                skill_id="vn-financial-data-collector",
                skill_markdown="# Skill",
                data_requirements=(),
                context={},
                evidence_ids=("citation_vn_prices_DXG-2026-06-26",),
            )
        )

    message = str(error.value)
    assert "RuntimeError" in message
    assert "You have no permission to access this resource" in message
    assert "secret-provider-key" not in message
    assert "api_key=<redacted>" in message


def test_dataflow_models_serialize_safe_provider_statuses() -> None:
    from finmind_agents.dataflows.models import (
        DataflowProviderResult,
        DataflowRetrievalRequest,
        DataflowRetrievalResult,
        DatasetGroup,
        RetrievalStatus,
    )

    request = DataflowRetrievalRequest(
        market=Market.VN_STOCK,
        symbol="VCB",
        dataset_groups=(DatasetGroup.MARKET_PRICE, DatasetGroup.FUNDAMENTAL),
        requested_by="vn-financial-data-collector",
    )
    provider = DataflowProviderResult(
        provider_id="vnstock",
        dataset_groups=(DatasetGroup.MARKET_PRICE,),
        status=RetrievalStatus.SUCCESS,
        source_ids=("vnstock_prices",),
        warnings=(),
    )
    result = DataflowRetrievalResult(
        retrieval_id="retrieval_test",
        market=request.market,
        symbol=request.symbol,
        requested_dataset_groups=request.dataset_groups,
        provider_results=(provider,),
        records=(),
        source_documents=(),
        status=RetrievalStatus.SUCCESS,
        warnings=(),
        failure_reasons=(),
    )

    serialized = result.to_output()

    assert serialized["retrieval_id"] == "retrieval_test"
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
    us_providers = registry.providers_for(
        market=Market.US_STOCK,
        dataset_groups=(DatasetGroup.MARKET_PRICE, DatasetGroup.NEWS),
    )

    assert {provider.provider_id for provider in vn_providers} >= {"vnstock", "offline_fallback"}
    assert {provider.provider_id for provider in us_providers} >= {
        "alpha_vantage",
        "offline_fallback",
    }


def test_vn_data_provider_env_can_disable_vnstock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from finmind_agents.dataflows.models import DatasetGroup
    from finmind_api.platform import create_demo_platform

    monkeypatch.setenv("FINMIND_ADMIN_USERNAME", "analyst")
    monkeypatch.setenv("FINMIND_ADMIN_PASSWORD", "secret-pass")
    monkeypatch.setenv("FINMIND_SESSION_SECRET", "session-secret-with-length")
    monkeypatch.setenv("FINMIND_VN_DATA_PROVIDER", "offline")

    platform = create_demo_platform()
    providers = platform.dataflow_service.registry.providers_for(
        market=Market.VN_STOCK,
        dataset_groups=(DatasetGroup.MARKET_PRICE,),
    )

    assert {provider.provider_id for provider in providers} == {"offline_fallback"}


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


def test_bare_vn_data_provider_env_is_supported(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from finmind_api.settings import Settings

    monkeypatch.setenv("FINMIND_ADMIN_USERNAME", "analyst")
    monkeypatch.setenv("FINMIND_ADMIN_PASSWORD", "secret-pass")
    monkeypatch.setenv("FINMIND_SESSION_SECRET", "session-secret-with-length")
    monkeypatch.delenv("FINMIND_VN_DATA_PROVIDER", raising=False)
    monkeypatch.setenv("VN_DATA_PROVIDER", "offline")

    assert Settings.from_env().vn_data_provider == "offline"


def test_vnstock_api_key_env_is_supported(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from finmind_api.settings import Settings

    monkeypatch.setenv("FINMIND_ADMIN_USERNAME", "analyst")
    monkeypatch.setenv("FINMIND_ADMIN_PASSWORD", "secret-pass")
    monkeypatch.setenv("FINMIND_SESSION_SECRET", "session-secret-with-length")
    monkeypatch.setenv("FINMIND_VNSTOCK_API_KEY", "vnstock-secret")

    assert Settings.from_env().vnstock_api_key == "vnstock-secret"


def test_dataflow_fallback_labels_provider_failure_without_raw_payloads(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from finmind_agents.dataflows.models import DataflowRetrievalRequest, DatasetGroup
    from finmind_api.platform import create_demo_platform

    monkeypatch.setenv("FINMIND_ADMIN_USERNAME", "analyst")
    monkeypatch.setenv("FINMIND_ADMIN_PASSWORD", "secret-pass")
    monkeypatch.setenv("FINMIND_SESSION_SECRET", "session-secret-with-length")
    monkeypatch.delenv("FINMIND_US_ALPHA_VANTAGE_API_KEY", raising=False)
    platform = create_demo_platform()

    result = platform.dataflow_service.retrieve(
        DataflowRetrievalRequest(
            market=Market.US_STOCK,
            symbol="AAPL",
            dataset_groups=(DatasetGroup.NEWS,),
            requested_by="vn-financial-data-collector",
        )
    )
    output = result.to_output()

    assert output["status"] in {"partial", "fallback", "failed"}
    assert "offline_fallback" in output["providers"]
    assert any(
        provider["status"] in {"skipped", "fallback", "failed"}
        for provider in output["provider_results"]
    )
    assert "raw" not in str(output).lower()
    assert "secret" not in str(output).lower()


def test_vnstock_provider_fetches_live_price_and_fundamental_records(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from finmind_agents.dataflows.models import DataflowRetrievalRequest, DatasetGroup
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
        def ratios(self, **kwargs: object) -> list[dict[str, object]]:
            assert kwargs["orient"] == "report"
            return [
                {
                    "item": "EPS",
                    "item_id": "trailing_eps",
                    "2026-Q1": 5400,
                    "2025-Q4": 5100,
                },
                {
                    "item": "BVPS",
                    "item_id": "book_value_per_share_bvps",
                    "2026-Q1": 36200,
                    "2025-Q4": 35100,
                },
                {
                    "item": "ROE",
                    "item_id": "roe",
                    "2026-Q1": 0.214,
                    "2025-Q4": 0.2,
                }
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
        DataflowRetrievalRequest(
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
    assert price.payload["close"] == 61200
    assert fundamentals.payload["eps"] == 5400
    assert result.provider_result.source_ids == (
        "vnstock_fundamentals",
        "vnstock_prices",
    )


def test_vnstock_provider_supports_top_level_vnstock_api(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from finmind_agents.dataflows.models import DataflowRetrievalRequest, DatasetGroup
    from finmind_agents.dataflows.providers.vnstock import VnstockProvider

    class FakeQuote:
        def __init__(self, **kwargs: object) -> None:
            assert kwargs["source"] == "VCI"
            assert kwargs["symbol"] == "DXG"

        def history(self, **kwargs: object) -> list[dict[str, object]]:
            assert kwargs["interval"] == "1D"
            return [
                {
                    "time": "2026-06-27",
                    "close": 14.2,
                    "volume": 1200000,
                }
            ]

    class FakeFinance:
        def __init__(self, **kwargs: object) -> None:
            raise ConnectionError("finance unavailable")

    class FakeCompany:
        def __init__(self, **kwargs: object) -> None:
            assert kwargs["source"] == "KBS"
            assert kwargs["symbol"] == "DXG"

        def overview(self) -> list[dict[str, object]]:
            return [
                {
                    "symbol": "DXG",
                    "exchange": "HOSE",
                    "outstanding_shares": 1268104965,
                    "charter_capital": 12699,
                    "as_of_date": "2025-12-31T00:00:00",
                }
            ]

    fake_vnstock = SimpleNamespace(
        Quote=FakeQuote,
        Finance=FakeFinance,
        Company=FakeCompany,
    )
    monkeypatch.setitem(sys.modules, "vnstock", fake_vnstock)

    result = VnstockProvider().fetch(
        DataflowRetrievalRequest(
            market=Market.VN_STOCK,
            symbol="DXG",
            dataset_groups=(DatasetGroup.MARKET_PRICE, DatasetGroup.FUNDAMENTAL),
            requested_by="vn-financial-data-collector",
        )
    )

    assert result.provider_result.status == "partial"
    assert {record.dataset_id for record in result.records} == {
        "vn_prices",
        "vn_fundamentals",
    }
    fundamentals = next(
        record for record in result.records if record.dataset_id == "vn_fundamentals"
    )
    assert fundamentals.payload["outstanding_shares"] == 1268104965
    assert "vnstock_finance_fetch_failed" in result.provider_result.warnings


def test_vnstock_provider_registers_api_key_before_fetch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from finmind_agents.dataflows.models import DataflowRetrievalRequest, DatasetGroup
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
        DataflowRetrievalRequest(
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
    from finmind_agents.dataflows.models import DataflowRetrievalRequest, DatasetGroup
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
        DataflowRetrievalRequest(
            market=Market.VN_STOCK,
            symbol="VCB",
            dataset_groups=(DatasetGroup.MARKET_PRICE,),
            requested_by="vn-financial-data-collector",
        )
    )

    assert result.provider_result.status == "failed"
    assert result.provider_result.warnings == ("vnstock_registration_failed",)
    assert "vnstock-secret" not in str(result.provider_result)


def test_workflow_run_returns_cited_fresh_chart_result(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/workflows/vn-financial-data-collector/run",
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
        if section["title"] == "Collected Data"
    )
    assert analysis_section["citations"]
    assert result["output"]["citations"][0]["source_type"] == "market_data"
    assert result["output"]["freshness"][0]["status"] == "fresh"
    collection = result["output"]["collection"]
    assert collection["retrieval_id"].startswith("retrieval_")
    assert "market_price" in collection["requested_dataset_groups"]
    assert collection["provider_results"]
    assert "raw" not in str(collection).lower()
    assert "secret" not in str(collection).lower()
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
        "/api/workflows/vn-financial-data-collector/run",
        json={"market": "VN_STOCK", "symbol": "VCB"},
    )

    assert response.status_code == 200
    result = response.json()
    section = next(
        item
        for item in result["output"]["sections"]
        if item["title"] == "Collected Data"
    )
    chart = result["output"]["artifacts"]["chart"]

    assert result["inputs"]["symbol"] == "VCB"
    assert "Agent-collected VCB data package" in section["content"]
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
        "/api/workflows/vn-financial-data-collector/run",
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
    response = client.post("/api/workflows/vn-financial-data-collector/run", json=payload)

    assert response.status_code == 422
    assert expected_detail in response.json()["detail"]


def test_failed_validation_does_not_create_successful_run(
    client: TestClient,
) -> None:
    failed = client.post(
        "/api/workflows/vn-financial-data-collector/run",
        json={"market": "VN_STOCK", "symbol": "ZZZ"},
    )
    runs = client.get("/api/runs")

    assert failed.status_code == 422
    assert runs.status_code == 200
    assert runs.json() == []


def test_workflow_catalog_remains_provider_neutral(client: TestClient) -> None:
    response = client.get("/api/workflows")

    assert response.status_code == 200
    catalog_text = str(response.json()).lower()
    assert "vnstock" not in catalog_text
    assert "alpha_vantage" not in catalog_text
    assert "sec_edgar" not in catalog_text


def test_unsupported_market_validation_stops_before_dataflow_calls(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from finmind_agents.dataflows.service import DataflowService

    def fail_retrieve(self: DataflowService, request: object) -> object:
        raise AssertionError("dataflows should not run for invalid market")

    monkeypatch.setattr(DataflowService, "retrieve", fail_retrieve)

    response = client.post(
        "/api/workflows/vn-financial-data-collector/run",
        json={"market": "GOLD", "symbol": "SJC"},
    )

    assert response.status_code == 422


def test_unknown_run_returns_404(client: TestClient) -> None:
    response = client.get("/api/runs/run_missing")

    assert response.status_code == 404
    assert response.json()["detail"] == "Run not found"


def test_completed_workflow_run_can_be_reopened_from_history(
    client: TestClient,
) -> None:
    run_response = client.post(
        "/api/workflows/vn-financial-data-collector/run",
        json={"market": "VN_STOCK", "symbol": "VCB"},
    )
    result = run_response.json()

    list_response = client.get("/api/runs")
    detail_response = client.get(f"/api/runs/{result['id']}")

    assert run_response.status_code == 200
    assert result["status"] == "success"
    assert result["output"]["collection"]["provider_results"]
    assert list_response.status_code == 200
    assert list_response.json()[0] == result
    assert detail_response.status_code == 200
    assert detail_response.json() == result
