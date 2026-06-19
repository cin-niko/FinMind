from api.platform.models import WorkflowSpecification
from api.platform.repositories import WorkflowRepository


class WorkflowCatalog(WorkflowRepository):
    def __init__(self, workflows: list[WorkflowSpecification]) -> None:
        self._workflows = {workflow.workflow_id: workflow for workflow in workflows}

    def list(self) -> list[WorkflowSpecification]:
        return list(self._workflows.values())

    def get(self, workflow_id: str) -> WorkflowSpecification | None:
        return self._workflows.get(workflow_id)
