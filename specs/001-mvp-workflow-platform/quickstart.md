---
id: SPEC-FEAT-001-QUICKSTART
feature: mvp-workflow-platform
status: draft
owner: solo
created: 2026-06-18
implements:
  - src/api
  - src/ui
validated_by:
  - tests/test_app.py
  - tests/test_platform_services.py
adr_refs: []
---

# Quickstart: MVP Workflow Platform Validation

## Prerequisites

- Python 3.12 environment
- Project dependencies installed with `uv sync --group dev`
- Admin credentials configured:
  - `FINMIND_ADMIN_USERNAME`
  - `FINMIND_ADMIN_PASSWORD`
  - `FINMIND_SESSION_SECRET`

## Commands

```bash
uv run pytest
```

After implementation:

```bash
uv run uvicorn api.app:create_app --factory --reload
```

```bash
cd src/ui
npm install
npm run dev
```

## Scenario 1: Login-Required Shell

1. Start with all admin environment variables set.
2. Open the app without an active session.
3. Confirm protected Phase 1 content is not shown.
4. Log in with the configured admin credentials.
5. Confirm workflow and result navigation is available.
6. Log out and confirm protected content is blocked.
7. Restart without one required admin variable and confirm fail-closed behavior.

## Scenario 2: Fixed Workflow Run

1. Ensure seeded/demo VN stock or gold data is available.
2. Open the workflow tab.
3. Select a V1 workflow such as daily market brief.
4. Submit valid inputs.
5. Inspect the completed result.

Expected result: output includes structured sections, citations, freshness metadata, chart artifacts when relevant, visible stage/tool status, and no raw agent reasoning.

## Scenario 3: Result Inspection

1. Complete one workflow run.
2. Open the run from the result view.
3. Inspect citations, evidence, freshness, artifacts, and visible execution status.

Expected result: completed and partial runs remain inspectable after execution.
