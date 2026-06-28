from collections.abc import Callable
from dataclasses import dataclass

from finmind_agents.dataflows.models import DataflowCollectionRequest, DataflowCollectionResult
from finmind_agents.dataflows.service import DataflowService


@dataclass(frozen=True)
class RuntimeToolRegistry:
    dataflows: DataflowService
    skill_loader: Callable[[str], str]

    def collect_dataflow(
        self,
        request: DataflowCollectionRequest,
    ) -> DataflowCollectionResult:
        return self.dataflows.collect(request)

    def load_skill(self, skill_id: str) -> str:
        return self.skill_loader(skill_id)

