from dataclasses import dataclass
from pathlib import Path

from finmind_agents.dataflows.models import (
    AgentCollectionPlan,
    DataRequirement,
    DataflowCollectionRequest,
    DataflowCollectionResult,
)
from finmind_agents.dataflows.requirements import (
    build_agent_collection_plan,
    load_data_requirements,
    mark_collection_plan_executed,
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
    collection: DataflowCollectionResult
    collection_plan: AgentCollectionPlan


def collect_workflow_data(
    workflow: WorkflowSpecification,
    dataflows: DataflowService,
    market: Market,
    symbol: str | None,
) -> CollectedWorkflowData:
    if not symbol:
        raise WorkflowValidationError("symbol is required")
    data_requirements = data_requirements_for_workflow(workflow)
    collection_plan = build_agent_collection_plan(
        skill_id=primary_skill_id(workflow),
        market=market,
        symbol=symbol,
        data_requirements=data_requirements,
    )
    collection = dataflows.collect(
        DataflowCollectionRequest(
            market=market,
            symbol=symbol,
            data_requirements=collection_plan.all_requests(),
            requested_by=workflow.workflow_id,
        )
    )
    if not collection.records and not collection.source_documents:
        raise WorkflowValidationError(
            "Market data provider is unavailable. Try again after the provider recovers."
        )
    return CollectedWorkflowData(
        records=collection.records,
        source_documents=collection.source_documents,
        collection=collection,
        collection_plan=mark_collection_plan_executed(collection_plan),
    )


def data_requirements_for_workflow(
    workflow: WorkflowSpecification,
) -> tuple[DataRequirement, ...]:
    requirements: list[DataRequirement] = []
    for skill_ref in workflow.skill_refs:
        requirements.extend(_load_requirements_for_skill_ref(skill_ref))
    return tuple(requirements)


def data_requirements_for_skill(
    workflow: WorkflowSpecification,
    skill_id: str,
) -> tuple[DataRequirement, ...]:
    skill_ref = skill_ref_for_id(workflow, skill_id)
    if skill_ref is None:
        return ()
    return _load_requirements_for_skill_ref(skill_ref)


def skill_ref_for_id(
    workflow: WorkflowSpecification,
    skill_id: str,
) -> str | None:
    for skill_ref in workflow.skill_refs:
        if Path(skill_ref).parent.name == skill_id:
            return skill_ref
    return None


def primary_skill_id(workflow: WorkflowSpecification) -> str:
    if not workflow.skill_refs:
        return ""
    return Path(workflow.skill_refs[0]).parent.name


def _load_requirements_for_skill_ref(skill_ref: str) -> tuple[DataRequirement, ...]:
    requirements_path = Path(skill_ref).with_name("DATA_REQUIREMENTS.yaml")
    if requirements_path.exists():
        return load_data_requirements(requirements_path)
    return ()
