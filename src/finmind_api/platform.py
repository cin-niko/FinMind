from dataclasses import dataclass

from finmind_agents.dataflows.registry import build_default_provider_registry
from finmind_agents.dataflows.service import DataflowService
from finmind_agents.conversations import ConversationWorkflowService
from finmind_agents.memory import create_workflow_catalog
from finmind_agents.repositories import ConversationRepository
from finmind_agents.runtime.service import AgentOrchestrator
from finmind_agents.workflows.service import WorkflowService
from finmind_api.settings import Settings, SettingsError


@dataclass(frozen=True)
class Platform:
    workflow_service: WorkflowService
    conversation_service: ConversationWorkflowService
    dataflow_service: DataflowService


def build_default_agent_orchestrator() -> AgentOrchestrator:
    return AgentOrchestrator()


def build_conversation_store(settings: Settings) -> ConversationRepository:
    """Construct the product conversation store from settings.

    The product store is PostgreSQL (implemented in the API layer); the
    application fails closed when the DSN is missing or unreachable. Tests
    override this seam to inject an in-memory run repository.
    """
    if not settings.database_url:
        raise SettingsError("FINMIND_DATABASE_URL is required for conversation persistence")
    from finmind_api.conversation_store import PostgresConversationRepository

    return PostgresConversationRepository(settings.database_url)


def create_demo_platform() -> Platform:
    settings = Settings.from_env()
    conversations = build_conversation_store(settings)
    dataflow_service = DataflowService(
        registry=build_default_provider_registry(
            vn_data_provider=settings.vn_data_provider,
            vnstock_api_key=settings.vnstock_api_key,
            gold_data_provider=settings.gold_data_provider,
            twelve_data_api_key=settings.twelve_data_api_key,
            provider_timeout_seconds=settings.dataflow_provider_timeout_seconds,
        )
    )
    workflow_service = WorkflowService(
            workflows=create_workflow_catalog(),
            dataflows=dataflow_service,
            agent_orchestrator=build_default_agent_orchestrator(),
            records=conversations,
        )
    conversations.reconcile_interrupted()
    return Platform(
        workflow_service=workflow_service,
        conversation_service=ConversationWorkflowService(
            workflows=workflow_service,
            conversations=conversations,
        ),
        dataflow_service=dataflow_service,
    )
