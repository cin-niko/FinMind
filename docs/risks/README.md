# Risks

Use this directory for known risks, mitigations, and open concerns that affect
product behavior, delivery, operations, data quality, compliance, or user trust.

Link risk records from the owning spec, plan, or ADR when they affect a bounded
feature or shared contract.

Start new risk records from [`template.md`](template.md).

## Index

| Risk | Status | Severity | Summary |
|------|--------|----------|---------|
| [`RISK-001`](RISK-001-workflow-skill-contract-drift.md) | Open | Medium | YAML workflow definitions and Markdown agent skills can drift apart. |
| [`RISK-002`](RISK-002-agent-skill-unsupported-claims.md) | Open | High | Agent skills can produce unsupported financial claims without sufficient evidence or citations. |
| [`RISK-003`](RISK-003-external-agent-integration-portability.md) | Open | Medium | Future Claude/MCP integrations may need contracts that diverge from internal UI/API assumptions. |
| [`RISK-004`](RISK-004-async-stream-resource-saturation.md) | Open | High | Async workflow/chatflow streams can saturate finite provider, model, database, or offload resources. |
