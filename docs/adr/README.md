# Architecture Decision Records

Use this directory for durable architecture and product-engineering decisions.

Each ADR should describe the context, decision, alternatives considered, and
consequences. Link ADRs from specs using `adr_refs`.

Start new ADRs from [`template.md`](template.md).

## Index

| ADR | Status | Decision |
|-----|--------|----------|
| [`ADR-001`](ADR-001-hybrid-workflow-definitions-and-agent-skills.md) | Accepted | Use hybrid YAML workflow definitions, Markdown agent skills, and a guarded runtime for Phase 02 workflows and future external agent integrations. |
| [`ADR-002`](ADR-002-direct-async-sse-streaming.md) | Accepted | Use direct request-scoped SSE streaming for workflow and chatflow execution. |
| [`ADR-003`](ADR-003-artifact-and-citation-inspection-contract.md) | Accepted | Use `Artifact -> FileArtifact | ChartArtifact` and keep citations as a separate right-panel evidence surface. |
