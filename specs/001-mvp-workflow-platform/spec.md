---
id: SPEC-FEAT-001
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

# Feature Specification: MVP Workflow Platform

## Summary

Deliver the first independently valuable FinMind slice: an authenticated internal analyst shell where the environment-configured admin can run a bounded finance research workflow for VN stocks or gold and inspect cited, freshness-aware results with chart artifacts and visible execution status.

This feature intentionally does not include live/admin ingestion operations, evidence-backed chat, or production plugin adapters. Those are preserved in later feature specs.

## User Scenarios & Testing

### User Story 1 - Run a Cited Fixed Workflow (Priority: P1)

An authenticated internal user selects a predefined finance research workflow, enters required inputs, runs the workflow, and reviews a structured result with citations, freshness metadata, chart artifacts, and inspectable execution status.

**Independent Test**: Log in as the environment-configured internal admin, run one V1 workflow from the workflow tab using seeded/demo VN stock or gold data, and verify that the completed result includes cited evidence, freshness metadata, at least one chart artifact when relevant, and an execution record.

Acceptance scenarios:

1. Given the admin user is logged in and required seeded/demo data is available, when the user selects a V1 workflow and submits valid inputs, then the system completes bounded analysis and displays structured output sections with citations, freshness metadata, and execution status.
2. Given a workflow requires a market chart, when the workflow completes, then the result includes a chart artifact linked to the same canonical data and evidence used by the textual answer.
3. Given a workflow input is missing or invalid, when the user attempts to run the workflow, then the system prevents execution and shows a clear validation message without creating a successful run record.

### User Story 2 - Access Login-Required Shell (Priority: P1)

An internal admin user accesses the authenticated application shell, while unauthenticated visitors are blocked from all protected content.

**Independent Test**: Attempt to access each Phase 1 surface before login, log in with environment-configured admin credentials, navigate workflow and results, log out, and confirm protected content is blocked again.

Acceptance scenarios:

1. Given no active session exists, when a visitor opens any protected application route, then the system requires login before showing content.
2. Given valid admin credentials from environment variables, when the user logs in, then the system grants access to Phase 1 surfaces.
3. Given the user logs out or the session expires, when the user attempts to access protected content, then the system returns to the login flow.
4. Given required admin environment values are missing or invalid at startup, when the app starts, then protected content remains unavailable.

## Functional Requirements

- **FR-001**: System MUST require successful login before any user can access workflow, result, or future protected surfaces.
- **FR-002**: System MUST bootstrap one internal admin account from environment variables at application startup and grant that account access to all V1 surfaces as they ship.
- **FR-002a**: System MUST read admin bootstrap values from `FINMIND_ADMIN_USERNAME`, `FINMIND_ADMIN_PASSWORD`, and `FINMIND_SESSION_SECRET`, and MUST fail closed when any required value is missing or invalid.
- **FR-003**: System MUST provide a workflow tab where users can choose a predefined V1 workflow, provide validated inputs, run bounded analysis, and inspect completed results.
- **FR-004**: System MUST model each fixed workflow as a declarative specification covering inputs, required datasets, execution stages, output sections, citation expectations, and chart requirements.
- **FR-005**: V1 MUST support VN stocks and gold as the first implementation market scope, while preserving contracts and data modeling that can later add US stocks and BTC without replacing the core platform.
- **FR-006**: V1 MUST ship an initial workflow set that includes TradingAgents-inspired roles such as fundamental analysis, technical analysis, macro analysis, and risk management where relevant to the selected market scope.
- **FR-008**: Phase 1 MUST maintain seeded/demo canonical storage for supported VN stock and gold datasets with source identity, collection time, effective market time, freshness metadata, and uniqueness rules.
- **FR-012**: System MUST construct reusable evidence objects that link generated claims to source data, citations, timestamps, and generated artifacts.
- **FR-013**: Every user-facing workflow result MUST expose citations and freshness metadata for material claims.
- **FR-014**: System MUST generate and display market chart artifacts for workflow outputs that require visual price, indicator, or trend analysis.
- **FR-016**: System MUST record execution logs for workflow runs, generated artifacts, failures, and user-visible output status.
- **FR-018**: System MUST expose result views where users can inspect completed workflow outputs, citations, charts, freshness, and execution status after the original run.
- **FR-019**: System MUST show clear out-of-scope behavior for unsupported markets, unsupported instruments, missing data, stale data, and unavailable citations.
- **FR-020**: System MUST show users evidence, citations, workflow stages, and tool or artifact status while retaining raw agent reasoning internally and excluding it from user-facing result views.
- **FR-021**: System MUST use cookie-backed web sessions for V1 authenticated application access.
- **FR-022**: System MUST keep provider-specific market data details abstract at the product contract level while allowing implementation-time provider validation for technical and licensing suitability.
- **FR-023**: System MUST preserve separated product layers for app experience, API access, agent/core logic, and data workflows.
- **FR-025**: System MUST exclude trade execution, broker connectivity, portfolio order management, self-service registration, external identity providers, US stocks, and BTC from V1 user-facing market coverage.

## Key Entities

- Internal Admin User
- Session
- Market Instrument
- Canonical Market Data Record
- Source Document
- Workflow Specification
- Workflow Run
- Evidence Object
- Citation
- Chart Artifact
- Execution Log

See `../system/state-model.md` for canonical entity definitions.

## Edge Cases

- Supported data exists but is stale: workflow outputs must display freshness warnings.
- A workflow partially completes: the result distinguishes completed sections, failed sections, and unavailable artifacts.
- Citations are unavailable for a generated claim: the claim is omitted, qualified, or marked unsupported.
- Startup admin credentials are missing or invalid: the application fails closed.
- Unsupported US stock or BTC requests return a V1 scope limitation.

## Success Criteria

- **SC-001**: 100% of protected Phase 1 routes require login before displaying workflow or result content.
- **SC-002**: An authenticated admin user can complete a successful fixed workflow run and review cited output, freshness metadata, chart artifact, and execution status in under 5 minutes using available seeded/demo data.
- **SC-002a**: When required admin environment variables are present at startup, the configured admin credentials authenticate successfully without manual database setup.
- **SC-002b**: When any required admin environment variable is missing or invalid at startup, the application prevents unauthenticated access and reports configuration failure.
- **SC-003**: 100% of user-facing material claims in workflow outputs include at least one citation or are explicitly marked unsupported or unavailable.
- **SC-006**: At least 95% of supported workflow result views show freshness metadata for every referenced dataset.
- **SC-007**: Users can identify stale, missing, failed, or out-of-scope data conditions from the UI without reading server logs.
- **SC-008**: V1 supports at least one stock research path and one non-stock market research path across approved initial workflows.

## Out Of Scope

- Admin ingestion operations and market data inspector; see `../002-data-operations/`.
- Evidence-backed chat; see `../003-evidence-backed-chat/`.
- Production plugin adapter; see `../004-extension-hardening/`.
- US stocks and BTC as supported V1 markets.
