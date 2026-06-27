from api.platform.models import WorkflowSpecification
from api.platform.workflows.definitions import load_workflow_definitions
from api.platform.workflows.skills import load_agent_skills
from api.platform.workflows.specs import validate_workflow_catalog


def build_workflow_catalog() -> list[WorkflowSpecification]:
    workflows = load_workflow_definitions()
    skill_paths = {skill.skill_path for skill in load_agent_skills().values()}
    validate_workflow_catalog(workflows, skill_paths)
    return workflows
