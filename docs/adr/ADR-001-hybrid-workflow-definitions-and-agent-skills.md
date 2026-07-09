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
  workflow id, type, supported markets, required inputs, skill refs, ordered
  steps, output sections, citation policy, chart requirements, runtime policy,
  and safety gates.
- Markdown agent skills describe human-readable analysis behavior for individual
  capabilities such as `fundamental-analysis`, `technical-analysis`,
  `news-digest`, and `risk-review`.
- Fixed runtime code enforces validation, market scope, dataflow tool
  permissions, data-quality gates, citation/freshness requirements, no raw reasoning,
  no autonomous trading actions, run persistence, and API/UI response contracts.
- Provider retrieval lives behind `src/api/platform/dataflows/`, so workflow
  and agent code request canonical dataset groups through FinMind tools and never
  call concrete market-data, fundamentals, or news providers directly.
- Skill data needs MUST be represented as low-level machine-readable data
  requirements, stored beside the skill as `DATA_REQUIREMENTS.yaml` when a skill
  needs provider-backed data. `SKILL.md` explains the analyst procedure and
  verification rules; `DATA_REQUIREMENTS.yaml` declares exact datasets such as
  OHLCV, financial statements, valuation ratios, corporate events, company
  profile, and source documents.
- Skill-owned data requirements are the canonical source of truth for retrieval
  needs. Workflow YAML MUST NOT duplicate detailed dataset requirements; it may
  constrain market scope, inputs, skill refs, allowed tools, runtime mode,
  output schema, and safety gates.
- Workflow skills MUST run through FinMind's shared agent runtime, backed by
  LangChain Deep Agents (`deepagents.create_deep_agent`). LLM configuration is
  required for workflow skill execution; missing model configuration fails
  closed instead of silently falling back to deterministic prose.
- FinMind SHOULD converge workflow and chatflow execution on one shared
  `FinMindAgentRuntime` abstraction. Workflows and chatflow use the same agent
  substrate, skill registry, dataflows tool boundary, validators, citation
  policy, and safety policy, but run under different policy envelopes.
- Workflow execution is a constrained agent run: fixed skills from workflow
  YAML, skill-owned data requirements, strict output schema, low iteration
  budget, dataflows-only tool access, no autonomous tool expansion, and
  fail-closed behavior.
- Chatflow execution is a flexible research agent run: dynamic skill loading,
  dynamic data requirements, broader approved tool access, larger iteration
  budget, clarification/partial-answer behavior, and chat-specific answer
  schemas.

The runtime MUST treat workflow YAML as the executable product contract and
Agent Skills as the canonical source for skill-level data requirements and
governed analysis instructions. Markdown skills MUST NOT be the source of truth
for input validation, permissions, supported markets, execution state, or output
schemas; workflow YAML MUST NOT be the source of truth for detailed data
requirements.

During a workflow run, the agent runtime reads `SKILL.md` and
`DATA_REQUIREMENTS.yaml`, then plans retrieval calls inside the
`workflow_strict` policy. FinMind validates the requested market, symbol,
dataset ids, required/optional status, fallback policy, and tool permissions
before executing any retrieval through `DataflowService.retrieve(...)`.
DeepAgent decides the retrieval plan from the skill; FinMind remains the
authority that validates and executes dataflow calls.

Named high-level packages MAY be added later as convenience macros, but the core
dataflows contract is low-level requirements that compile into provider dataset
groups. This lets fixed workflows and the future chatflow orchestrator request
specific data without depending on provider-specific APIs.

Deep Agents execution is the Phase 02 runtime substrate for the shared runtime.
LangGraph remains a future option when explicit graph state, checkpointing,
pause/resume, or more complex multi-agent branching becomes necessary. When a
model provider does not support tool-planning messages, the orchestrator may
load the skill into the prompt and still validate the result through FinMind
guardrails.

DeepAgent/agent frameworks MUST NOT own FinMind authority boundaries. Provider
access remains behind `dataflows`; market scope, citations, no-trade safety,
output schemas, persistence, audit logs, and UI contracts remain enforced by
FinMind runtime code outside the agent.

## Alternatives Considered

| Alternative | Reason Not Chosen |
|-------------|-------------------|
| Fixed code only | Strong safety and tests, but workflow behavior becomes harder to expose, version, inspect, or reuse through future Claude/MCP integrations. |
| Markdown agent skills only | Flexible and readable, but weak for deterministic validation, UI/API catalog generation, automated tests, partial execution state, and citation enforcement. |
| YAML definitions only | Strong contracts, but insufficient for domain analysis guidance, prompt iteration, and future agent-facing analyst behavior. |
| Duplicating data requirements in workflow YAML and skill files | Appears deterministic, but creates two sources of truth and makes chatflow reuse diverge from workflow runs for accidental reasons. |
| High-level data packages only | Simple workflow prompts, but too rigid for future agentic chatflow and ad hoc analyst questions that need precise datasets, windows, periods, or metrics. |
| LangGraph immediately | Useful for future multi-agent chatflow and graph state, but unnecessary for the current single-skill workflow path and would add framework complexity before branching/tool-loop requirements exist. |
| Hand-rolled LLM call only | Simpler dependency surface, but less representative of the future chatflow agent stack and less useful for testing LangChain skill/tool behavior early. |
| Separate workflow and chatflow agent runtimes | Keeps workflow strictness simple, but creates duplicated skill/tool behavior and makes future chatflow/workflow parity harder to reason about. |
| DeepAgents as immediate unguarded authority | Good fit for future planning and subagents, but unsafe if it bypasses FinMind-controlled dataflows, citation validation, market scope, or no-trade guardrails. |

## Consequences

- Workflow contracts become portable across FinMind UI, API, tests, and later
  MCP/Claude adapters.
- Agent skills can evolve analysis guidance without bypassing runtime guardrails.
- Implementation must include schema validation for workflow definitions and
  compatibility checks between workflow steps, referenced skills, and
  skill-owned data requirements.
- Implementation must include retrieval-plan validation so the agent can plan
  dataflow calls from the skill without calling unsupported datasets, markets,
  providers, or tools.
- Implementation must keep provider status, fallback labeling, and source
  normalization in the dataflows retrieval module rather than duplicating
  provider logic in workflow skills or executors.
- The project must manage versioning for both YAML workflow definitions and
  Markdown skills.
- The project must manage runtime adapter compatibility, especially for models
  with different tool-calling behavior.
- Workflow and chatflow can share one agent substrate while preserving different
  policy envelopes and failure semantics.
- Delivery has more upfront structure than fixed Python functions, but avoids
  locking Phase 02 into one-off workflow code.

## Validation

- Workflow definition schema tests reject missing inputs, unsupported markets,
  unknown step ids, missing skill references, duplicated detailed data
  requirements, and invalid output contracts.
- Skill schema tests validate `DATA_REQUIREMENTS.yaml` and prove required data
  is attempted before claim-generating synthesis.
- Runtime tests prove agent-planned dataflow calls are rejected when they request
  unsupported markets, datasets, providers, or tools.
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
