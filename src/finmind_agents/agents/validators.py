from finmind_agents.agents.models import AgentMetadataResult, AgentRunResult


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
    citation_ids: tuple[str, ...],
) -> None:
    validate_agent_content(result.content)
    validate_agent_metadata(
        AgentMetadataResult(
            status=result.status,
            citations=result.citations,
            allowed_claims=result.allowed_claims,
            blocked_claims=result.blocked_claims,
            warnings=result.warnings,
        ),
        citation_ids,
    )


def validate_agent_content(content: str) -> None:
    normalized_content = content.lower()
    forbidden_terms = [
        term for term in FORBIDDEN_OUTPUT_TERMS if term in normalized_content
    ]
    if forbidden_terms:
        raise AgentValidationError(
            f"Agent result contains forbidden output terms: {forbidden_terms}"
        )


def validate_agent_metadata(
    metadata: AgentMetadataResult,
    citation_ids: tuple[str, ...],
) -> None:
    known_citations = set(citation_ids)
    unknown_citations = [
        citation for citation in metadata.citations if citation not in known_citations
    ]
    if unknown_citations:
        raise AgentValidationError(
            f"Agent result referenced unknown citations: {unknown_citations}"
        )
