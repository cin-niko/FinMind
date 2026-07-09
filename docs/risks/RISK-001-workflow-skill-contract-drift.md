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
expects inputs, skill refs, output sections, runtime policy, or citation behavior
that the referenced skill does not support. Detailed data requirements are owned
by the skill's `DATA_REQUIREMENTS.yaml`; workflow YAML drift should not be
resolved by duplicating dataset lists.

## Impact

Contract drift can produce broken workflow runs, misleading UI catalog metadata,
incomplete result sections, failed MCP/tool exposure, or unsafe outputs that
appear valid because one artifact changed without the other.

## Triggers

- A workflow definition references a skill id or version that does not exist.
- A skill changes required evidence or output shape without a matching workflow
  definition update.
- A shared agent runtime or DeepAgent adapter changes skill-loading behavior
  without matching workflow policy or data-requirement updates.
- A workflow definition starts duplicating detailed dataset requirements instead
  of referencing the skill-owned requirements.
- An agent-derived retrieval plan requests datasets outside the loaded skill
  requirements or runtime policy.
- UI/API catalog fields diverge from the workflow definition.
- Tests rely on hard-coded workflow assumptions instead of definition fixtures.

## Mitigation

- Add schema validation for workflow YAML.
- Add compatibility checks that every referenced skill exists and declares the
  required datasets, output schema, citation policy, and blocked-claim behavior.
- Treat workflow definitions as the source of truth for catalog/API structure.
- Treat `DATA_REQUIREMENTS.yaml` as the source of truth for skill-level retrieval
  needs.
- Treat policy envelopes as explicit contracts: workflow policy fixes allowed
  skills, tools, output schema, and failure behavior; skill-owned requirements
  fix retrieval needs; chatflow policy may allow dynamic selection.
- Validate every agent-derived retrieval plan before executing dataflows.
- Require spec/task updates when adding, renaming, or changing a workflow step.

## Residual Risk

Some drift can still happen in free-form analysis instructions because Markdown
skills are human-authored. This remains acceptable only if runtime validation
continues to enforce supported markets, input schemas, citations, freshness, and
output status. Shared DeepAgent-style runtimes increase the need for policy
tests because one substrate can affect both workflow and chatflow behavior.

## Validation

- Unit tests load every workflow definition and referenced skill.
- Contract tests fail on unknown skill ids, missing required fields, unsupported
  markets, and incompatible output schemas.
- `/speckit-analyze` or an equivalent spec check verifies linked ADR/risk/spec
  references remain valid.
- Phase 02 implementation validates workflow definition loading and skill
  compatibility in `tests/test_platform_services.py`.
- Runtime adapter tests must prove workflow mode cannot load skills, tools, or
  data requirements outside the workflow policy envelope.
- Tests must fail if workflow YAML duplicates detailed dataset requirements that
  belong in `DATA_REQUIREMENTS.yaml`.
- Tests must reject agent retrieval plans that request undeclared required or
  optional datasets.

## References

- `specs/002-workflow/plan.md`
- `specs/002-workflow/data-model.md`
- `docs/adr/ADR-001-hybrid-workflow-definitions-and-agent-skills.md`
