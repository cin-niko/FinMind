from dataclasses import dataclass

from finmind_agents.dataflows.registry import build_default_provider_registry
from finmind_agents.dataflows.service import DataflowService
from finmind_agents.memory import (
    InMemoryMarketDataRepository,
    create_workflow_catalog,
)
from finmind_agents.repositories import RunRepository
from finmind_agents.runtime.service import AgentOrchestrator
from finmind_agents.workflows.service import WorkflowService
from finmind_api.settings import Settings, SettingsError


@dataclass(frozen=True)
class Platform:
    workflow_service: WorkflowService
    dataflow_service: DataflowService


def build_default_agent_orchestrator() -> AgentOrchestrator:
    return AgentOrchestrator()


def build_run_store(settings: Settings) -> RunRepository:
    """Construct the product run store from settings.

    The product store is PostgreSQL (implemented in the API layer); the
    application fails closed when the DSN is missing or unreachable. Tests
    override this seam to inject an in-memory run repository.
    """
    if not settings.database_url:
        raise SettingsError("FINMIND_DATABASE_URL is required for the run store")
    from finmind_api.run_store import PostgresRunRepository

    return PostgresRunRepository(settings.database_url)


def create_demo_platform() -> Platform:
    settings = Settings.from_env()
    runs = build_run_store(settings)
    market_data = InMemoryMarketDataRepository()
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
