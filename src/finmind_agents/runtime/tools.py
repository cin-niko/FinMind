from collections.abc import Callable
from dataclasses import dataclass

from finmind_agents.dataflows.models import DataflowRetrievalRequest, DataflowRetrievalResult
from finmind_agents.dataflows.service import DataflowService


@dataclass(frozen=True)
class RuntimeToolRegistry:
    dataflows: DataflowService
    skill_loader: Callable[[str], str]

    def retrieve_dataflow(
        self,
        request: DataflowRetrievalRequest,
    ) -> DataflowRetrievalResult:
        return self.dataflows.retrieve(request)

    def load_skill(self, skill_id: str) -> str:
        return self.skill_loader(skill_id)

