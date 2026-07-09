from pathlib import Path

from finmind_agents.models import WorkflowSpecification
from finmind_agents.repositories import WorkflowRepository


class WorkflowCatalogError(ValueError):
    """Raised when workflow definitions and skills are incompatible."""


class WorkflowCatalog(WorkflowRepository):
    def __init__(self, workflows: list[WorkflowSpecification]) -> None:
        self._workflows = {workflow.workflow_id: workflow for workflow in workflows}

    def list(self) -> list[WorkflowSpecification]:
        return list(self._workflows.values())

    def get(self, workflow_id: str) -> WorkflowSpecification | None:
        return self._workflows.get(workflow_id)


def validate_workflow_catalog(
    workflows: list[WorkflowSpecification],
    skill_paths: set[str],
) -> None:
    workflow_ids = {workflow.workflow_id for workflow in workflows}
    skill_ids = {Path(skill_ref).parent.name for skill_ref in skill_paths}
    for workflow in workflows:
        if workflow.step_sequence:
            valid_steps = set(workflow_ids) | set(workflow.stages) | skill_ids
            missing_steps = [
                step for step in workflow.step_sequence if step not in valid_steps
            ]
            if missing_steps:
                raise WorkflowCatalogError(
                    f"{workflow.workflow_id} references unknown steps: {missing_steps}"
                )
        missing_skills = [
            skill_ref
            for skill_ref in workflow.skill_refs
            if skill_ref not in skill_paths
        ]
        if missing_skills:
            raise WorkflowCatalogError(
                f"{workflow.workflow_id} references missing skills: {missing_skills}"
            )
        if workflow.step_sequence:
            skill_ref_ids = {
                Path(skill_ref).parent.name for skill_ref in workflow.skill_refs
            }
            orphan_skill_steps = [
                step
                for step in workflow.step_sequence
                if step != "collect_data"
                and step not in workflow_ids
                and step not in skill_ref_ids
            ]
            if orphan_skill_steps:
                raise WorkflowCatalogError(
                    f"{workflow.workflow_id} skill steps lack a skill_ref: "
                    f"{orphan_skill_steps}"
                )
