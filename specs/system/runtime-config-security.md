---
id: SPEC-SYSTEM-RUNTIME-SECURITY-FINMIND
status: active
last_review: 2026-07-11
implements:
  - src/finmind_agents/runtime
  - src/finmind_api/settings.py
  - src/finmind_api/auth.py
  - src/finmind_api/dependencies.py
  - src/finmind_api/run_store.py
validated_by:
  - tests/test_app.py
adr_refs: []
---

# Runtime, Config, And Security

## Authentication

All user-facing app and API surfaces require successful login before protected content is displayed. V1 uses one internal admin account bootstrapped from environment variables, with the repository-local `.env` file used as a local-development fallback when a variable is not present in the process environment:

- `FINMIND_ADMIN_USERNAME`
- `FINMIND_ADMIN_PASSWORD`
- `FINMIND_SESSION_SECRET`

The application must fail closed when any required value is missing or invalid. Fail closed means protected content is not available to unauthenticated visitors.

## Sessions

V1 uses cookie-backed web sessions for authenticated browser access. Session cookie values must be signed or otherwise verified using `FINMIND_SESSION_SECRET`; unsigned, malformed, or tampered session cookies must be treated as unauthenticated. Logout and expiration must block protected content again.

## Scope Gates

The active user-facing workflow scope is VN stocks and gold only. Chatflow
remains deferred to Phase 04. Future market coverage is not valid user-facing
scope until a bounded spec defines asset coverage, source eligibility, and
safety behavior.

VN provider selection uses `FINMIND_VN_DATA_PROVIDER` as its sole environment
variable and accepts only `vnstock` in the current workflow foundation.

Gold provider selection uses `FINMIND_GOLD_DATA_PROVIDER` and accepts only
`twelvedata` in Phase 03. `FINMIND_TWELVE_DATA_API_KEY` supplies the connector
credential, and `FINMIND_DATAFLOW_PROVIDER_TIMEOUT_SECONDS` bounds each provider
attempt. Missing or rejected credentials fail the Gold collection without a
fallback source; credentials must never appear in output or logs.

Mock/demo surfaces are still user-facing scope surfaces. Controls must not present
unsupported markets or assets as enabled runnable choices. If roadmap markets are
shown for product preview, they must be disabled or clearly marked future/out-of-scope
before execution rather than allowing the user to submit and discover the limitation
only through backend validation.

V1 excludes:

- Trade execution
- Broker connectivity
- Portfolio order management
- Self-service registration
- External identity providers
- any market, asset, or source coverage not defined by the active feature spec

## Evidence Safety

Generated material claims must show citations (source id, dataset id, timestamp) or be omitted, qualified, or marked unsupported/unavailable. Data age is conveyed by citation timestamps; records must not be silently presented as more current than their citation timestamp.

## Reasoning Safety

The UI may show evidence, citations, workflow stages, role status, tool status, artifact status, and final grounded rationale. It must not expose raw agent reasoning.

## Conversation Store (PostgreSQL)

Workflow-created conversations persist to PostgreSQL so history survives app
restarts. Interrupted queued or running conversations are reconciled to failed
on startup under the shared conversation contract. Configuration:

- `FINMIND_DATABASE_URL`: Postgres DSN. Required for the product conversation store; the application fails closed (protected content is not served) when it is missing or the database is unreachable.
- The persistence implementation is owned by the API layer; the agentic layer declares the corresponding conversation repository contract.
- Development uses the `postgres` service in `docker-compose.yaml`; local `uv run uvicorn` points `FINMIND_DATABASE_URL` at `localhost:5432`.
- Conversations own their messages and execution metadata; assistant messages
  own their citation snapshots and artifacts. Deleting a conversation
  cascade-deletes those children but does not delete shared canonical market
  data. The schema is bootstrapped or migrated safely on startup.
- Database credentials are read only from environment variables and must not be logged, returned in API output, or exposed in the UI.
