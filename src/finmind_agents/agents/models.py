from typing import Protocol, Literal

from pydantic import BaseModel, Field

from finmind_agents.dataflows.models import DataRequirement


class AgentRunRequest(BaseModel):
    workflow_id: str
    skill_id: str
    skill_markdown: str
    data_requirements: tuple[DataRequirement, ...]
    context: dict[str, object] = Field(default_factory=dict)
    evidence_ids: tuple[str, ...]


class AgentRunResult(BaseModel):
    status: Literal["success", "partial", "failed"]
    section_title: str
    content: str
    citations: tuple[str, ...] = ()
    allowed_claims: tuple[str, ...] = ()
    blocked_claims: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


class AgentOrchestratorProtocol(Protocol):
    def run_skill(self, request: AgentRunRequest) -> AgentRunResult: ...
