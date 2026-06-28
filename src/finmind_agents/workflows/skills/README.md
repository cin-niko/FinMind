# Workflow Agent Skills

Markdown agent skills describe governed workflow behavior. The current active
runtime skill is `vn-financial-data-collector`; analysis skills will be added
back only after their core logic is specified and reviewed.

Skills are not directly executable API or external-agent tools. The workflow
runtime invokes them only through validated YAML workflow definitions and still
enforces market scope, data-quality gates, citation policy, freshness, and
advice-only safety rules.

## Standard Format

Each workflow skill lives in `src/finmind_agents/workflows/skills/<skill-name>/SKILL.md`
and is referenced by workflow YAML with that full project-relative path. Each
`SKILL.md` uses this document structure:

- YAML frontmatter with `name`, `description`, and `version`.
- Optional `DATA_REQUIREMENTS.yaml` for low-level machine-readable data needs
  consumed by the orchestrator before calling `DataflowService.retrieve(...)`.
- Compatibility fields consumed by the current loader: `Version`, `Purpose`,
  `Blocked Behavior`, `Output Contract`, and `Citation Policy`.
- Agent operating sections: `Role`, `When To Use`, `Required Context`,
  `Agent Prompt`, `Workflow Procedure`, `Output Contract`, `Citation Policy`,
  `Allowed Claims`, `Unavailable Rules`, `Safety Rules`, and `Output Examples`.

The compatibility fields preserve deterministic catalog validation today. The
agent operating sections are the future prompt surface for skill-loaded workflow
execution.
