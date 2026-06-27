from pathlib import Path

from api.platform.models import AgentSkill


class AgentSkillError(ValueError):
    """Raised when an agent skill document is missing or invalid."""


SKILLS_DIR = Path(__file__).with_name("skills")


def load_agent_skills(skills_dir: Path = SKILLS_DIR) -> dict[str, AgentSkill]:
    skills: dict[str, AgentSkill] = {}
    for path in sorted(skills_dir.glob("*.md")):
        if path.name == "README.md":
            continue
        skill = _skill_from_markdown(path)
        skills[skill.skill_id] = skill
    return skills


def _skill_from_markdown(path: Path) -> AgentSkill:
    content = path.read_text(encoding="utf-8")
    purpose = _extract_field(content, "Purpose")
    required_context = _extract_list(content, "Required Context")
    allowed_claims = _extract_list(content, "Allowed Claims")
    safety_rules = _extract_list(content, "Safety Rules")
    blocked_behavior = _extract_field(content, "Blocked Behavior")
    output_contract = _extract_field(content, "Output Contract")
    citation_policy = _extract_field(content, "Citation Policy")
    return AgentSkill(
        skill_id=path.stem,
        skill_path=f"src/api/platform/workflows/skills/{path.name}",
        version=_extract_field(content, "Version"),
        purpose=purpose,
        required_context=tuple(required_context),
        allowed_claims=tuple(allowed_claims),
        blocked_behavior=blocked_behavior,
        output_contract=output_contract,
        citation_policy=citation_policy,
        safety_rules=tuple(safety_rules),
    )


def _extract_field(content: str, label: str) -> str:
    prefix = f"{label}:"
    for line in content.splitlines():
        if line.startswith(prefix):
            value = line.removeprefix(prefix).strip()
            if value:
                return value
    raise AgentSkillError(f"Missing {label}")


def _extract_list(content: str, label: str) -> list[str]:
    heading = f"## {label}"
    lines = content.splitlines()
    try:
        start = lines.index(heading) + 1
    except ValueError as error:
        raise AgentSkillError(f"Missing {label}") from error

    values: list[str] = []
    for line in lines[start:]:
        if line.startswith("## "):
            break
        if line.startswith("- "):
            values.append(line[2:].strip())
    if not values:
        raise AgentSkillError(f"Empty {label}")
    return values
