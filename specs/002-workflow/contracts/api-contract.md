---
id: SPEC-FEAT-002-CONTRACTS
feature: workflow
status: draft
owner: solo
created: 2026-06-26
implements: []
validated_by: []
adr_refs: []
---

# API Contract: Workflow

## Workflows

### `GET /api/workflows`

Returns fixed workflow catalog entries for VN stock and US stock workflows.

### `POST /api/workflows/{workflow_id}/run`

Runs a bounded workflow with validated inputs and returns or links to a workflow
run containing sections, citations, freshness, artifacts, and visible execution
status.

Unsupported markets and assets, including gold and BTC, return clear scope
limitations.

## Results

### `GET /api/runs`

Returns workflow runs visible to the authenticated user for history and result
reinspection.

### `GET /api/runs/{run_id}`

Returns a completed or partial workflow run with sections, citations, freshness,
artifacts, and visible execution status. Raw agent reasoning is excluded.
