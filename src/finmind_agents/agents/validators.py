from finmind_agents.agents.models import AgentRunResult


FORBIDDEN_OUTPUT_TERMS = (
    "chain-of-thought",
    "hidden prompt",
    "raw reasoning",
    "skill_markdown",
    "data_requirements",
    "workflow_id",
    "place an order",
    "execute trade",
)


class AgentValidationError(ValueError):
    """Raised when an agent result violates FinMind output guardrails."""


def validate_agent_result(
    result: AgentRunResult,
    evidence_ids: tuple[str, ...],
) -> None:
    known_evidence = set(evidence_ids)
    unknown_citations = [
        citation for citation in result.citations if citation not in known_evidence
    ]
    if unknown_citations:
        raise AgentValidationError(
            f"Agent result referenced unknown citations: {unknown_citations}"
        )
    normalized_content = result.content.lower()
    forbidden_terms = [
        term for term in FORBIDDEN_OUTPUT_TERMS if term in normalized_content
    ]
    if forbidden_terms:
        raise AgentValidationError(
            f"Agent result contains forbidden output terms: {forbidden_terms}"
        )
