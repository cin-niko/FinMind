import json
from pathlib import Path
from typing import Any

from finmind_agents.dataflows.models import (
    AgentCollectionPlan,
    DataRequirement,
    Market,
    CollectionPlanStatus,
)


class DataRequirementError(ValueError):
    """Raised when a skill data requirement contract is invalid."""


class CollectionPlanError(ValueError):
    """Raised when an agent collection plan violates skill or runtime policy."""


def load_data_requirements(path: str | Path) -> tuple[DataRequirement, ...]:
    requirements_path = Path(path)
    data = _load_mapping(requirements_path)
    raw_required = data.get("required", data.get("requirements"))
    raw_optional = data.get("optional", [])
    if not isinstance(raw_required, list) or not raw_required:
        raise DataRequirementError(
            f"{requirements_path.name} must define a non-empty required list"
        )
    if not isinstance(raw_optional, list):
        raise DataRequirementError(f"{requirements_path.name} optional must be a list")
    requirements: list[DataRequirement] = []
    requirements.extend(_requirements_from_items(raw_required, required=True))
    requirements.extend(_requirements_from_items(raw_optional, required=False))
    return tuple(requirements)


def build_agent_collection_plan(
    *,
    skill_id: str,
    market: Market,
    symbol: str,
    data_requirements: tuple[DataRequirement, ...],
    policy_id: str = "workflow_strict",
    allow_optional: bool = True,
) -> AgentCollectionPlan:
    plan = AgentCollectionPlan(
        skill_id=skill_id,
        market=market,
        symbol=symbol,
        required_requests=tuple(
            requirement for requirement in data_requirements if requirement.required
        ),
        optional_requests=tuple(
            requirement
            for requirement in data_requirements
            if not requirement.required and allow_optional
        ),
        policy_id=policy_id,
    )
    validate_agent_collection_plan(
        plan,
        declared_requirements=data_requirements,
        allow_optional=allow_optional,
    )
    return AgentCollectionPlan(
        skill_id=plan.skill_id,
        market=plan.market,
        symbol=plan.symbol,
        required_requests=plan.required_requests,
        optional_requests=plan.optional_requests,
        policy_id=plan.policy_id,
        status=CollectionPlanStatus.APPROVED,
    )


def mark_collection_plan_executed(plan: AgentCollectionPlan) -> AgentCollectionPlan:
    return AgentCollectionPlan(
        skill_id=plan.skill_id,
        market=plan.market,
        symbol=plan.symbol,
        required_requests=plan.required_requests,
        optional_requests=plan.optional_requests,
        policy_id=plan.policy_id,
        status=CollectionPlanStatus.EXECUTED,
    )


def validate_agent_collection_plan(
    plan: AgentCollectionPlan,
    *,
    declared_requirements: tuple[DataRequirement, ...],
    allow_optional: bool,
) -> None:
    declared = {requirement.dataset for requirement in declared_requirements}
    required_declared = {
        requirement.dataset for requirement in declared_requirements if requirement.required
    }
    optional_declared = {
        requirement.dataset for requirement in declared_requirements if not requirement.required
    }
    for requirement in plan.required_requests:
        if requirement.dataset not in declared:
            raise CollectionPlanError(
                f"{requirement.dataset} is not declared by skill data requirements"
            )
    for requirement in plan.optional_requests:
        if not allow_optional:
            raise CollectionPlanError("Optional collection is not allowed by policy")
        if requirement.dataset not in optional_declared:
            raise CollectionPlanError(
                f"{requirement.dataset} is not declared optional by skill data requirements"
            )
    planned_required = {requirement.dataset for requirement in plan.required_requests}
    missing_required = sorted(required_declared - planned_required)
    if missing_required:
        raise CollectionPlanError(
            f"Required skill data was not planned: {', '.join(missing_required)}"
        )


def _requirements_from_items(
    items: list[object],
    *,
    required: bool,
) -> list[DataRequirement]:
    requirements: list[DataRequirement] = []
    for item in items:
        if not isinstance(item, dict):
            raise DataRequirementError("Each data requirement must be an object")
        dataset = item.get("dataset")
        if not isinstance(dataset, str) or not dataset:
            raise DataRequirementError("Each data requirement must include dataset")
        params = {key: value for key, value in item.items() if key != "dataset"}
        requirements.append(
            DataRequirement(dataset=dataset, params=params, required=required)
        )
    return requirements


def _load_mapping(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise DataRequirementError(
            f"{path.name} must use JSON-compatible YAML"
        ) from error
    if not isinstance(data, dict):
        raise DataRequirementError(f"{path.name} must define an object")
    return data
