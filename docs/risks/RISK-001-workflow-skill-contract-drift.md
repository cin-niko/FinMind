---
id: RISK-001
status: open
severity: medium
likelihood: medium
owner: engineering
created: 2026-06-27
last_reviewed: 2026-06-27
related_specs:
  - specs/002-workflow/spec.md
  - specs/002-workflow/plan.md
related_adrs:
  - docs/adr/ADR-001-hybrid-workflow-definitions-and-agent-skills.md
---

# RISK-001: Workflow Definition And Skill Contract Drift

## Summary

YAML workflow definitions and Markdown agent skills can drift apart if a workflow
expects inputs, datasets, output sections, or citation behavior that the
referenced skill does not support.

## Impact

Contract drift can produce broken workflow runs, misleading UI catalog metadata,
incomplete result sections, failed MCP/tool exposure, or unsafe outputs that
appear valid because one artifact changed without the other.

## Triggers

- A workflow definition references a skill id or version that does not exist.
- A skill changes required evidence or output shape without a matching workflow
  definition update.
- UI/API catalog fields diverge from the workflow definition.
- Tests rely on hard-coded workflow assumptions instead of definition fixtures.

## Mitigation

- Add schema validation for workflow YAML.
- Add compatibility checks that every referenced skill exists and declares the
  required datasets, output schema, citation policy, and blocked-claim behavior.
- Treat workflow definitions as the source of truth for catalog/API structure.
- Require spec/task updates when adding, renaming, or changing a workflow step.

## Residual Risk

Some drift can still happen in free-form analysis instructions because Markdown
skills are human-authored. This remains acceptable only if runtime validation
continues to enforce supported markets, input schemas, citations, freshness, and
output status.

## Validation

- Unit tests load every workflow definition and referenced skill.
- Contract tests fail on unknown skill ids, missing required fields, unsupported
  markets, and incompatible output schemas.
- `/speckit-analyze` or an equivalent spec check verifies linked ADR/risk/spec
  references remain valid.
- Phase 02 implementation validates workflow definition loading and skill
  compatibility in `tests/test_platform_services.py`.

## References

- `specs/002-workflow/plan.md`
- `specs/002-workflow/data-model.md`
- `docs/adr/ADR-001-hybrid-workflow-definitions-and-agent-skills.md`
