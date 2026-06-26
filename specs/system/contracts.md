---
id: SPEC-SYSTEM-CONTRACTS-FINMIND
status: active
last_review: 2026-06-18
implements:
  - src/agent_core
  - src/api
validated_by:
  - tests/test_app.py
  - tests/test_platform_services.py
adr_refs: []
---

# System Contracts

This spec defines stable contract rules for API responses, generated artifacts, evidence, citations, execution visibility, and provider abstraction.

## API Surface

The authenticated app shell consumes JSON APIs for:

- Session state: `GET /api/session`, `POST /api/login`, `POST /api/logout`
- Workflow catalog and runs: `GET /api/workflows`, `POST /api/workflows/{workflow_id}/run`
- Result inspection: `GET /api/runs`, `GET /api/runs/{run_id}`

All protected APIs require an active cookie-backed session. Raw agent reasoning is never returned.

## Evidence And Citation Contract

Material user-facing claims must be backed by at least one citation or be explicitly marked unsupported or unavailable. A citation must include:

- User-facing label
- Source type
- Source reference
- Source or collection timestamp where available
- Link to an evidence object or generated artifact when applicable

Freshness metadata must be visible for referenced datasets. Freshness states are: fresh, stale, missing, failed.

## Artifact Contract

Artifacts are reusable outputs linked to inputs, evidence, and execution context.

Supported artifact types:

- `chart`
- `table`
- `computed_result`
- `inline_visualization`

Chart artifacts must include renderable payload data and an accessible table fallback. Inline artifacts in chat must follow the same traceability rules as workflow chart artifacts.

`001-mvp-ui` mock chat artifacts are trusted local-template UI artifacts, not API
execution artifacts. Production chat artifact contracts require a future bounded
feature spec.

## Execution Visibility Contract

User-facing execution status may include:

- Workflow stages
- Role-agent status
- Tool or artifact status
- Run status: queued, running, success, partial, failed
- Failure summaries and unavailable sections

User-facing execution status must not include hidden model reasoning transcripts.

## Provider Abstraction

Product contracts must stay provider-neutral. Source connector implementation may validate provider suitability, licensing, credentials, and schema details, but public feature specs and user-facing contracts should refer to supported datasets and source identities rather than locking the product to one vendor.

## Layering Contract

FinMind keeps separable layers:

- App experience in UI
- FastAPI JSON API
- Finance orchestration and data services
- Reusable `agent_core`
- Data contracts and repositories

Feature work may reuse `agent_core` primitives for model interaction, tool invocation, streaming, and tool artifacts. Finance-specific workflow semantics live above `agent_core` unless an abstraction is genuinely reusable.
