from dataclasses import dataclass


@dataclass(frozen=True)
class GroundingResult:
    grounding_status: str
    blocked_claims: tuple[str, ...]
    uncited_claims: tuple[str, ...]


def uncited_citations(
    cited_ids: tuple[str, ...],
    valid_citation_ids: tuple[str, ...],
) -> tuple[str, ...]:
    valid = set(valid_citation_ids)
    return tuple(citation_id for citation_id in cited_ids if citation_id not in valid)


def citations_within_allowlist(
    cited_ids: tuple[str, ...],
    valid_citation_ids: tuple[str, ...],
) -> bool:
    return not uncited_citations(cited_ids, valid_citation_ids)
