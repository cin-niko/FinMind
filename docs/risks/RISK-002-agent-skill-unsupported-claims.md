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

## Mitigation

- Runtime code must enforce data-quality `allowed_claims` and `blocked_claims`
  before accepting section output.
- Output validation must reject or downgrade sections with material claims that
  lack citation ids and freshness metadata.
- Skills must instruct agents to mark unavailable sections instead of inventing
  missing news, fundamentals, or technical claims.
- User-facing output must never expose raw reasoning or autonomous trading
  decisions.

## Residual Risk

Claim detection may miss subtle unsupported phrasing, especially when generated
text is nuanced. This risk remains open until output schemas become structured
enough to validate claim categories and citations more precisely.

## Validation

- Tests simulate stale, missing, and failed datasets and assert blocked claims are
  omitted or marked unavailable.
- Tests assert every material output section carries citations or an unavailable
  status.
- Review checks inspect skill instructions for advice-only framing and evidence
  requirements.

## References

- `specs/002-workflow/spec.md`
- `specs/002-workflow/contracts/api-contract.md`
- `docs/adr/ADR-001-hybrid-workflow-definitions-and-agent-skills.md`
