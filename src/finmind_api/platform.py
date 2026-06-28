from dataclasses import dataclass

from finmind_agents.dataflows.registry import build_default_provider_registry
from finmind_agents.dataflows.service import DataflowService
from finmind_agents.memory import (
    InMemoryMarketDataRepository,
    InMemoryRunRepository,
    create_workflow_catalog,
)
from finmind_agents.runtime.service import AgentOrchestrator
from finmind_agents.workflows.service import WorkflowService
from finmind_api.settings import Settings


@dataclass(frozen=True)
class Platform:
    workflow_service: WorkflowService
    dataflow_service: DataflowService


def build_default_agent_orchestrator() -> AgentOrchestrator:
    return AgentOrchestrator()


def create_demo_platform() -> Platform:
    runs = InMemoryRunRepository()
    market_data = InMemoryMarketDataRepository()
    settings = Settings.from_env()
    dataflow_service = DataflowService(
        registry=build_default_provider_registry(
            vn_data_provider=settings.vn_data_provider,
            vnstock_api_key=settings.vnstock_api_key,
            alpha_vantage_api_key=settings.us_alpha_vantage_api_key,
            sec_edgar_user_agent=settings.sec_edgar_user_agent,
            fallback_market_data=market_data,
        )
    )
    return Platform(
        workflow_service=WorkflowService(
            workflows=create_workflow_catalog(),
            dataflows=dataflow_service,
            agent_orchestrator=build_default_agent_orchestrator(),
            runs=runs,
        ),
        dataflow_service=dataflow_service,
    )
