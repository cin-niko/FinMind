import json
from pathlib import Path
from typing import Any

from api.platform.models import Market, WorkflowSpecification, WorkflowType


class WorkflowDefinitionError(ValueError):
    """Raised when a workflow definition is missing or invalid."""


DEFINITIONS_DIR = Path(__file__).with_name("definitions")


def load_workflow_definitions(
    definitions_dir: Path = DEFINITIONS_DIR,
) -> list[WorkflowSpecification]:
    workflows: list[WorkflowSpecification] = []
    for path in sorted(definitions_dir.glob("*.yaml")):
        workflows.append(_workflow_from_mapping(path, _load_mapping(path)))
    if not workflows:
        raise WorkflowDefinitionError("No workflow definitions found")
    return workflows


def _load_mapping(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise WorkflowDefinitionError(
            f"{path.name} must use JSON-compatible YAML"
        ) from error
    if not isinstance(data, dict):
        raise WorkflowDefinitionError(f"{path.name} must define an object")
    return data


def _workflow_from_mapping(
    path: Path,
    data: dict[str, Any],
) -> WorkflowSpecification:
    workflow_id = _required_str(data, "workflow_id", path)
    return WorkflowSpecification(
        workflow_id=workflow_id,
        definition_path=f"src/api/platform/workflows/definitions/{path.name}",
        version=_required_str(data, "version", path),
        title=_required_str(data, "title", path),
        description=_required_str(data, "description", path),
        workflow_type=WorkflowType(_required_str(data, "workflow_type", path)),
        market_scope=tuple(Market(item) for item in _required_list(data, "market_scope", path)),
        required_inputs=tuple(_required_list(data, "required_inputs", path)),
        required_datasets=tuple(_required_list(data, "required_datasets", path)),
        stages=tuple(_required_list(data, "stages", path)),
        skill_refs=tuple(_required_list(data, "skill_refs", path)),
        output_sections=tuple(_required_list(data, "output_sections", path)),
        citation_policy=_required_str(data, "citation_policy", path),
        chart_requirements=tuple(_optional_list(data, "chart_requirements", path)),
        step_sequence=tuple(_optional_list(data, "step_sequence", path)),
    )


def _required_str(data: dict[str, Any], key: str, path: Path) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise WorkflowDefinitionError(f"{path.name} missing required string {key}")
    return value


def _required_list(data: dict[str, Any], key: str, path: Path) -> list[Any]:
    value = data.get(key)
    if not isinstance(value, list) or not value:
        raise WorkflowDefinitionError(f"{path.name} missing required list {key}")
    return value


def _optional_list(data: dict[str, Any], key: str, path: Path) -> list[Any]:
    value = data.get(key, [])
    if not isinstance(value, list):
        raise WorkflowDefinitionError(f"{path.name} invalid list {key}")
    return value
