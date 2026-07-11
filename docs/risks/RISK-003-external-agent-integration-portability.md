---
id: RISK-003
status: open
severity: medium
likelihood: medium
owner: engineering
created: 2026-06-27
last_reviewed: 2026-06-27
related_specs:
  - specs/002-workflow/spec.md
  - specs/004-agentic-chatflow/spec.md
related_adrs:
  - docs/adr/ADR-001-hybrid-workflow-definitions-and-agent-skills.md
---

# RISK-003: External Agent Integration Portability

## Summary

Future Claude, MCP, or other external agent integrations may require workflow
tool schemas, permission boundaries, streaming behavior, or artifact access
patterns that differ from FinMind's internal UI/API runtime.

## Impact

If Phase 02 overfits to either the internal UI or one external client, workflows
may need expensive redesign before they can be exposed as safe external tools.
If exposed too loosely, external agents may bypass FinMind's data-quality and
citation guardrails.

## Triggers

- Workflow definitions cannot be translated into stable tool schemas.
- External clients need different input/output contracts than FinMind API
  responses.
- External agents call analysis skills directly instead of using the guarded
  workflow runtime.
- A future DeepAgent runtime, LangGraph adapter, or MCP integration uses a
  different tool contract than FinMind's internal runtime.
- Artifact or citation retrieval is not separately addressable from workflow
  execution.

## Mitigation

- Keep workflow definitions client-neutral and machine-readable.
- Expose external integrations through runtime-managed tools such as
  `list_workflows`, `run_workflow`, `get_workflow_run`, `get_citations`, and
  `get_artifact`.
- Do not expose Markdown skills as directly executable external tools.
- Keep citations, artifacts, and run ids stable enough for external clients to
  inspect after execution.
- Keep agent runtime adapters behind a shared `FinMindAgentRuntime` interface so
  workflow mode and chatflow mode can share skills/tools while preserving
  policy-specific limits.
- External integrations must call FinMind-managed tools such as `retrieve_dataflow`
  or `run_workflow`; they must not call providers or skills as unguarded
  standalone operations.

## Residual Risk

External client standards may evolve. The residual risk is acceptable if Phase 02
keeps the core workflow contract portable and defers client-specific adapter
details to a later integration spec. DeepAgent-style runtimes may improve
portability for chatflow, but only if their tool and state contracts are mapped
back to FinMind-owned validation and audit boundaries.

## Validation

- Design review confirms workflow definitions can map to tool schemas without
  duplicating business logic.
- Future integration specs must call the guarded runtime rather than individual
  skills directly.
- API contract tests prove runs, citations, and artifacts are retrievable by id.
- Phase 02 keeps workflow contracts in YAML definitions and exposes runs,
  citations, freshness, and artifacts through the guarded FastAPI runtime.
- Adapter tests must prove the same skill/dataflow contracts can run under
  workflow policy and, later, chatflow policy without bypassing guardrails.

## References

- `specs/002-workflow/spec.md`
- `specs/004-agentic-chatflow/spec.md`
- `docs/adr/ADR-001-hybrid-workflow-definitions-and-agent-skills.md`
