---
id: SPEC-FEAT-001-CONTRACTS
feature: mvp-workflow-platform
status: draft
owner: solo
created: 2026-06-18
implements:
  - src/api/routes
validated_by:
  - tests/test_app.py
adr_refs: []
---

# API Contract: MVP Workflow Platform

## Authentication

### `GET /api/session`

Returns the current authentication state.

### `POST /api/login`

Authenticates the environment-configured internal admin user and creates a cookie-backed web session.

### `POST /api/logout`

Invalidates the current session.

## Workflows

### `GET /api/workflows`

Returns declarative workflow catalog entries for VN stock and gold workflows.

### `POST /api/workflows/{workflow_id}/run`

Runs a bounded workflow with validated inputs and returns or links to a workflow run containing sections, citations, freshness, artifacts, and visible execution status.

Unsupported market requests return clear V1 scope limitations.

## Results

### `GET /api/runs/{run_id}`

Returns a completed or partial workflow run with sections, citations, freshness, artifacts, and visible execution status. Raw agent reasoning is excluded.
