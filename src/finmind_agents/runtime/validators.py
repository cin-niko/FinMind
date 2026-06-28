from finmind_agents.agents.models import AgentRunResult
from finmind_agents.agents.validators import validate_agent_result


def validate_finmind_agent_output(
    result: AgentRunResult,
    *,
    evidence_ids: tuple[str, ...],
) -> None:
    validate_agent_result(result, evidence_ids)

