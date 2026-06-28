---
id: RISK-002
status: open
severity: high
likelihood: medium
owner: engineering
created: 2026-06-27
last_reviewed: 2026-06-27
related_specs:
  - specs/002-workflow/spec.md
  - specs/002-workflow/contracts/api-contract.md
related_adrs:
  - docs/adr/ADR-001-hybrid-workflow-definitions-and-agent-skills.md
---

# RISK-002: Agent Skill Produces Unsupported Claims

## Summary

An LLM-backed or instruction-driven agent skill may generate a material financial
claim that is not supported by collected evidence, citations, or freshness
metadata.

## Impact

Unsupported claims directly damage user trust and violate FinMind's product
principles: advice, not decision; data driven; claims with evidence/citations,
not hallucination. In financial contexts this can also create safety, compliance,
and reputational risk.

## Triggers

- A skill receives partial or stale evidence but still writes confident analysis.
- A skill uses background model knowledge instead of collected workflow context.
- A citation id is missing, invalid, or not linked to the claim evidence.
- Data-quality gates mark a claim category blocked but the skill still emits it.
- Provider retrieval fails, skips due missing credentials, or falls back to
  deterministic data without downstream sections preserving the warning.
- A DeepAgent/chatflow-style runtime performs extra reasoning, skill loading, or
  tool calls beyond the workflow policy envelope and emits unsupported claims.
- The agent derives an incomplete or excessive retrieval plan from the skill and
  then synthesizes claims as if all required evidence was collected.

## Mitigation

- Runtime code must enforce data-quality `allowed_claims` and `blocked_claims`
  before accepting section output.
- Output validation must reject or downgrade sections with material claims that
  lack citation ids and freshness metadata.
- Skills must instruct agents to mark unavailable sections instead of inventing
  missing news, fundamentals, or technical claims.
- Dataflows provider results must preserve skipped, failed, partial, and fallback
  status so workflow quality gates can block or caveat affected claim categories.
- Agent-derived retrieval plans must be validated against skill-owned
  `DATA_REQUIREMENTS.yaml`; missing required retrievals must become quality gate
  warnings or blocking issues before synthesis.
- User-facing output must never expose raw reasoning or autonomous trading
  decisions.
- FinMind validators must run outside the agent framework and remain mandatory
  for every runtime adapter, including LangChain `create_agent`, DeepAgents, or
  future LangGraph adapters.
- Workflow mode must use a strict policy envelope: dataflows-only provider
  access, fixed skill refs, skill-owned data requirements, strict output schema,
  and fail-closed validation.

## Residual Risk

Claim detection may miss subtle unsupported phrasing, especially when generated
text is nuanced. This risk remains open until output schemas become structured
enough to validate claim categories and citations more precisely. DeepAgent-style
planning may add another residual risk because subagent/tool behavior can create
claims from intermediate context unless all outputs are validated by FinMind.

## Validation

- Tests simulate stale, missing, and failed datasets and assert blocked claims are
  omitted or marked unavailable.
- Tests assert every material output section carries citations or an unavailable
  status.
- Review checks inspect skill instructions for advice-only framing and evidence
  requirements.
- Phase 02 implementation tests assert no raw reasoning appears and blocked stock
  brief sections are marked unavailable.
- Dataflows tests assert provider failures and fallback states are visible without
  exposing raw provider payloads, credentials, or unsafe diagnostics.
- Runtime adapter tests assert agent output is rejected when citations are
  unknown, prompt/request payloads are echoed, trading instructions appear, or
  claims rely on unavailable datasets.
- Retrieval-plan tests assert required skill data is attempted and unsupported
  optional data requests are rejected before provider execution.

## References

- `specs/002-workflow/spec.md`
- `specs/002-workflow/contracts/api-contract.md`
- `docs/adr/ADR-001-hybrid-workflow-definitions-and-agent-skills.md`
