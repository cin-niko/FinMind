---
id: ADR-0006
title: Use shared evidence lineage tables for workflow and chat outputs
status: accepted
date: 2026-06-25
deciders: [solo]
affects_specs:
  - specs/system/state-model.md
  - specs/system/contracts.md
  - specs/002-data-operations/spec.md
  - specs/003-evidence-backed-chat/spec.md
---

# ADR-0006: Use shared evidence lineage tables for workflow and chat outputs

## Context

FinMind's product promise is evidence-backed finance research: user-facing workflow
and chat outputs must show citations, freshness, chart artifacts, execution status,
and grounded results without exposing raw model reasoning.

Phase 002 defines `evidence_objects`, `citations`, `artifacts`, and
`execution_logs` alongside market data tables. These tables were discussed as the
database layer that preserves what backed a response, what citation the user saw,
what renderable artifact was produced, and what happened during the run.

The alternative would be to let each surface (fixed workflows, chat, future plugins)
store its own evidence payload shape inside run JSON or chat messages. That would be
faster initially but would create trust drift and make reload-restored citation
integrity hard to audit.

## Decision

Use a **shared evidence lineage model** across workflows, chat, and future extension
surfaces:

- `evidence_objects` are internal grounding units linking a claim or artifact to
  source records, source documents, or other artifacts with freshness status.
- `citations` are user-visible source references linked to evidence objects.
- `artifacts` are renderable charts, tables, computed outputs, or inline
  visualizations linked to evidence refs.
- `execution_logs` record the user-visible event timeline for ingestion jobs,
  workflow runs, chat runs, tool calls, artifact creation, failures, and output
  status.

These tables are regular relational PostgreSQL tables. High-volume prices remain in
typed TimescaleDB hypertables; evidence lineage points back to those typed rows by
stable references rather than duplicating the market data.

## Consequences

### Positive

- One evidence/citation/artifact contract across workflow and chat surfaces.
- Reloaded results can prove what data and freshness state supported prior claims.
- Phase 003 chat can reuse Phase 001 workflow grounding behavior instead of creating
  chat-specific evidence storage.
- Future plugin/external outputs can follow the same lineage contract.

### Negative / trade-offs

- More tables and persistence wiring than embedding everything in `ExecutionRun.output`.
- Requires care to avoid storing raw reasoning, provider secrets, or raw scraped
  payloads in diagnostics/details.
- Workflow code that currently builds evidence in memory must eventually persist
  normalized lineage rows before chat relies on cross-run citation integrity.

### Neutral

- Ingestion generally writes price rows and `ingestion_jobs`; evidence objects are
  created when a workflow or chat uses data to make a user-facing claim.
- `execution_logs` may link either `job_id` for ingestion or `run_id` for workflow
  and chat.

## Alternatives considered

### Option A: Store citations and evidence only inside run/chat JSON

- Pros: Fastest implementation; fewer normalized tables.
- Cons: Harder reload integrity, weaker cross-surface reuse, and duplicate evidence
  shapes across workflow/chat/plugin paths.
- **Rejected** because it undermines FinMind's evidence-backed contract.

### Option B: Store only user-visible citations, not evidence objects

- Pros: Smaller schema and simpler UI rendering.
- Cons: Loses the internal proof chain from claim to source rows and freshness.
- **Rejected** because citations without structured evidence cannot support audit
  and artifact traceability.

### Option C: Persist raw provider responses as evidence

- Pros: Maximum source detail.
- Cons: Provider secrets/licensing risk, large payloads, and poor normalized querying.
- **Rejected**; persist normalized typed rows and non-secret summaries/refs instead.

## References

- [`specs/system/state-model.md`](../../specs/system/state-model.md) — `EvidenceObject`, `Citation`, `Artifact`
- [`specs/system/contracts.md`](../../specs/system/contracts.md) — evidence, artifact, execution visibility contracts
- [`specs/002-data-operations/spec.md`](../../specs/002-data-operations/spec.md) — FR-008b, FR-008c, FR-016
- [`specs/003-evidence-backed-chat/spec.md`](../../specs/003-evidence-backed-chat/spec.md) — FR-013, FR-015, FR-016
- [`docs/risks/README.md`](../risks/README.md) — R-003
