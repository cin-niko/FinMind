from dataclasses import dataclass
from enum import StrEnum

from finmind_agents.models import Market


class RuntimeMode(StrEnum):
    WORKFLOW = "workflow"
    CHATFLOW = "chatflow"


class RuntimeFailureBehavior(StrEnum):
    FAIL_CLOSED = "fail_closed"
    PARTIAL_ANSWER = "partial_answer"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class RuntimeTool:
    tool_id: str
    description: str
    side_effect_profile: str = "read_only"


@dataclass(frozen=True)
class AgentRuntimePolicy:
    policy_id: str
    mode: RuntimeMode
    allowed_tools: tuple[str, ...]
    allowed_skills: tuple[str, ...]
    allowed_markets: tuple[Market, ...]
    allowed_dataset_groups: tuple[str, ...]
    allow_optional_collection: bool
    max_iterations: int
    timeout_seconds: float
    output_schema: str
    failure_behavior: RuntimeFailureBehavior
    raw_reasoning_policy: str = "hidden"
    human_control_policy: str = "advice_only"

    @classmethod
    def workflow_strict(
        cls,
        *,
        allowed_skills: tuple[str, ...] = (),
    ) -> "AgentRuntimePolicy":
        return cls(
            policy_id="workflow_strict",
            mode=RuntimeMode.WORKFLOW,
            allowed_tools=("collect_dataflow", "load_skill", "validate_finmind_output"),
            allowed_skills=allowed_skills,
            allowed_markets=(Market.VN_STOCK, Market.US_STOCK),
            allowed_dataset_groups=("market_price", "fundamental", "news"),
            allow_optional_collection=True,
            max_iterations=4,
            timeout_seconds=45.0,
            output_schema="workflow_agent_result",
            failure_behavior=RuntimeFailureBehavior.FAIL_CLOSED,
        )

    def allows_market(self, market: Market) -> bool:
        return market in self.allowed_markets

