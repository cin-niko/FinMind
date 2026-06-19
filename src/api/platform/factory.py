from dataclasses import dataclass

from api.platform.memory import (
    InMemoryMarketDataRepository,
    InMemoryRunRepository,
    create_workflow_catalog,
)
from api.platform.workflows.service import WorkflowService


@dataclass(frozen=True)
class Platform:
    workflow_service: WorkflowService


def create_demo_platform() -> Platform:
    runs = InMemoryRunRepository()
    return Platform(
        workflow_service=WorkflowService(
            workflows=create_workflow_catalog(),
            market_data=InMemoryMarketDataRepository(),
            runs=runs,
        )
    )
