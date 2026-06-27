---
id: ADR-001
status: accepted
date: 2026-06-27
deciders:
  - product-owner
  - engineering
related_specs:
  - specs/002-workflow/spec.md
  - specs/002-workflow/plan.md
related_risks:
  - docs/risks/RISK-001-workflow-skill-contract-drift.md
  - docs/risks/RISK-002-agent-skill-unsupported-claims.md
  - docs/risks/RISK-003-external-agent-integration-portability.md
---

# ADR-001: Hybrid Workflow Definitions And Agent Skills

## Status

Accepted

## Context

Phase 02 introduces UI-runnable financial trading support workflows for VN stocks
and US stocks. These workflows must be composable, testable, visible in the UI,
safe for advice-only output, and reusable later by external agent clients such as
Claude or MCP-compatible integrations.

Pure fixed-code workflows are easy to test but make future workflow/plugin
reuse harder. Pure Markdown agent skills are flexible but too weak as the only
source of truth for validation, UI catalog generation, API contracts, execution
state, partial failure behavior, and citation enforcement.

## Decision

FinMind MUST use a hybrid workflow architecture:

- YAML workflow definitions describe machine-readable workflow contracts:
  workflow id, type, supported markets, required inputs, required datasets,
  ordered steps, output sections, citation policy, chart requirements, and
  safety gates.
- Markdown agent skills describe human-readable analysis behavior for individual
  capabilities such as `fundamental-analysis`, `technical-analysis`,
  `news-digest`, and `risk-review`.
- Fixed runtime code enforces validation, market scope, data collection,
  data-quality gates, citation/freshness requirements, no raw reasoning,
  no autonomous trading actions, run persistence, and API/UI response contracts.

The runtime MUST treat workflow YAML as the executable contract and Markdown
skills as governed analysis instructions. Markdown skills MUST NOT be the only
source of truth for input validation, permissions, supported markets, execution
state, or output schemas.

## Alternatives Considered

| Alternative | Reason Not Chosen |
|-------------|-------------------|
| Fixed code only | Strong safety and tests, but workflow behavior becomes harder to expose, version, inspect, or reuse through future Claude/MCP integrations. |
| Markdown agent skills only | Flexible and readable, but weak for deterministic validation, UI/API catalog generation, automated tests, partial execution state, and citation enforcement. |
| YAML definitions only | Strong contracts, but insufficient for domain analysis guidance, prompt iteration, and future agent-facing analyst behavior. |

## Consequences

- Workflow contracts become portable across FinMind UI, API, tests, and later
  MCP/Claude adapters.
- Agent skills can evolve analysis guidance without bypassing runtime guardrails.
- Implementation must include schema validation for workflow definitions and
  compatibility checks between workflow steps and referenced skills.
- The project must manage versioning for both YAML workflow definitions and
  Markdown skills.
- Delivery has more upfront structure than fixed Python functions, but avoids
  locking Phase 02 into one-off workflow code.

## Validation

- Workflow definition schema tests reject missing inputs, unsupported markets,
  unknown step ids, missing skill references, and invalid output contracts.
- Runtime tests prove unsupported assets are blocked before skill execution.
- Runtime tests prove material claims without citations are omitted, qualified,
  or marked unavailable.
- Catalog/API tests are generated from or checked against workflow definitions.
- MCP/Claude adapter design can expose workflow definitions as tool schemas
  without duplicating workflow contracts.

Phase 02 implementation validation:

- `tests/test_app.py`
- `tests/test_platform_services.py`
- `src/ui/package.json` build script

## References

- `specs/002-workflow/spec.md`
- `specs/002-workflow/plan.md`
- `specs/002-workflow/data-model.md`
- `specs/002-workflow/contracts/api-contract.md`
- `docs/risks/RISK-001-workflow-skill-contract-drift.md`
- `docs/risks/RISK-002-agent-skill-unsupported-claims.md`
- `docs/risks/RISK-003-external-agent-integration-portability.md`
