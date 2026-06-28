from dataclasses import dataclass
from pathlib import Path

from finmind_agents.dataflows.models import (
    AgentRetrievalPlan,
    DataRequirement,
    DataflowRetrievalRequest,
    DataflowRetrievalResult,
    DatasetGroup,
)
from finmind_agents.dataflows.requirements import (
    build_agent_retrieval_plan,
    load_data_requirements,
    mark_retrieval_plan_executed,
)
from finmind_agents.dataflows.service import DataflowService
from finmind_agents.models import (
    CanonicalMarketDataRecord,
    Market,
    SourceDocument,
    WorkflowSpecification,
)
from finmind_agents.workflows.validation import WorkflowValidationError


@dataclass(frozen=True)
class CollectedWorkflowData:
    records: tuple[CanonicalMarketDataRecord, ...]
    source_documents: tuple[SourceDocument, ...]
    retrieval: DataflowRetrievalResult
    retrieval_plan: AgentRetrievalPlan


def collect_workflow_data(
    workflow: WorkflowSpecification,
    dataflows: DataflowService,
    market: Market,
    symbol: str | None,
) -> CollectedWorkflowData:
    if not symbol:
        raise WorkflowValidationError("symbol is required")
    data_requirements = data_requirements_for_workflow(workflow)
    retrieval_plan = build_agent_retrieval_plan(
        skill_id=primary_skill_id(workflow),
        market=market,
        symbol=symbol,
        data_requirements=data_requirements,
    )
    retrieval = dataflows.retrieve(
        DataflowRetrievalRequest(
            market=market,
            symbol=symbol,
            data_requirements=retrieval_plan.all_requests(),
            requested_by=workflow.workflow_id,
        )
    )
    if not retrieval.records and not retrieval.source_documents:
        raise WorkflowValidationError("Required market data is missing")
    return CollectedWorkflowData(
        records=retrieval.records,
        source_documents=retrieval.source_documents,
        retrieval=retrieval,
        retrieval_plan=mark_retrieval_plan_executed(retrieval_plan),
    )


def data_requirements_for_workflow(
    workflow: WorkflowSpecification,
) -> tuple[DataRequirement, ...]:
    requirements: list[DataRequirement] = []
    for skill_ref in workflow.skill_refs:
        requirements_path = Path(skill_ref).with_name("DATA_REQUIREMENTS.yaml")
        if requirements_path.exists():
            requirements.extend(load_data_requirements(requirements_path))
    return tuple(requirements)


def primary_skill_id(workflow: WorkflowSpecification) -> str:
    if not workflow.skill_refs:
        return ""
    return Path(workflow.skill_refs[0]).parent.name


def required_dataset_categories_for_requirements(
    data_requirements: tuple[DataRequirement, ...],
) -> tuple[str, ...]:
    categories: list[str] = []
    for requirement in data_requirements:
        if not requirement.required:
            continue
        category = _quality_dataset_for_group(requirement.dataset_group())
        if category not in categories:
            categories.append(category)
    return tuple(categories)


def _quality_dataset_for_group(group: DatasetGroup) -> str:
    if group is DatasetGroup.MARKET_PRICE:
        return "price_series"
    if group is DatasetGroup.FUNDAMENTAL:
        return "fundamentals"
    return "source_documents"
