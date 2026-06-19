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

Deliver the first independently valuable FinMind slice: an authenticated internal analyst shell with a chat-first default surface, a real-data Market surface for VN stocks and gold, fixed system-defined workflows, and inspectable cited workflow results with freshness-aware chart artifacts and visible execution status.

This feature intentionally does not include live/admin ingestion operations, production evidence-backed chat, arbitrary LLM-generated HTML execution, or production plugin adapters. Those are preserved in later feature specs.

## User Scenarios & Testing

### User Story 1 - Run a Cited Fixed Workflow (Priority: P1)

An authenticated internal user selects a predefined finance research workflow, enters required inputs, runs the workflow, and reviews a structured result with citations, freshness metadata, chart artifacts, and inspectable execution status.

**Independent Test**: Log in as the environment-configured internal admin, run one V1 workflow from the workflow tab using seeded/demo VN stock or gold data, and verify that the completed result includes cited evidence, freshness metadata, at least one chart artifact when relevant, and an execution record.

Acceptance scenarios:

1. Given the admin user is logged in and required seeded/demo data is available, when the user selects a V1 workflow and submits valid inputs, then the system completes bounded analysis and displays structured output sections with citations, freshness metadata, and execution status.
2. Given a workflow requires a market chart, when the workflow completes, then the result includes a chart artifact linked to the same canonical data and evidence used by the textual answer.
3. Given a workflow input is missing or invalid, when the user attempts to run the workflow, then the system prevents execution and shows a clear validation message without creating a successful run record.
4. Given the workflow form is a mock/demo UI, when market or instrument choices are displayed, then only V1-supported VN stock and gold options are enabled for submission; US stock and BTC roadmap options are omitted or shown only as disabled/future preview choices before execution.

### User Story 2 - Access Login-Required Shell (Priority: P1)

An internal admin user accesses the authenticated application shell, while unauthenticated visitors are blocked from all protected content.

**Independent Test**: Attempt to access each Phase 1 surface before login, log in with environment-configured admin credentials, navigate workflow and results, log out, and confirm protected content is blocked again.

Acceptance scenarios:

1. Given no active session exists, when a visitor opens any protected application route, then the system requires login before showing content.
2. Given valid admin credentials from environment variables, when the user logs in, then the system grants access to Phase 1 surfaces.
3. Given the user logs out or the session expires, when the user attempts to access protected content, then the system returns to the login flow.
4. Given required admin environment values are missing or invalid at startup, when the app starts, then protected content remains unavailable.
5. Given a session cookie is unsigned, malformed, or tampered, when the user attempts to access protected content, then the system treats the request as unauthenticated.

### User Story 3 - Use Chat-First Shell With Mock Artifacts (Priority: P1)

An authenticated internal user lands on a new chat surface, asks a finance research question, receives a deterministic mock response, sees inline visual content where relevant, and can open larger mock artifacts in a right-side detail panel.

**Independent Test**: Log in as the environment-configured internal admin, confirm the default surface is `New Chat`, submit a message, verify a mock response appears with inline visual content and artifact cards, click a report/evidence artifact, and verify it opens in the right-side panel on desktop.

Acceptance scenarios:

1. Given the admin user is logged in, when the application shell loads, then the default active surface is `New Chat`.
2. Given the user submits the first chat message, when the deterministic mock response appears, then the chat is added to `History` using the first user message as the chat title.
3. Given the user submits any chat message, including the first message in a new chat, when the transcript updates, then the latest user message is positioned at the top of the chat transcript viewport.
4. Given a mock response includes a small visual, when the answer renders, then the visual appears inline inside the chat message using approved local templates.
5. Given a mock response includes a larger report, table, chart, evidence list, or citation bundle, when the user clicks its artifact card, then the full artifact opens in a right-side panel on desktop and a full-screen artifact view on mobile.

### User Story 4 - Inspect Real-Data Market (Priority: P1)

An authenticated internal user opens `Market` to inspect real VN stock and gold data through a watchlist-style dashboard with market snapshots, chart, news/source feed, freshness state, and market table.

**Independent Test**: Log in, open `Market`, verify only real seeded/demo data is displayed, select a supported instrument from the system predefined watchlist, and verify the selected chart, freshness metadata, source/news feed, and table update without LLM-generated summaries or recommendations.

Acceptance scenarios:

1. Given the admin user opens `Market`, when the page renders, then it shows a hybrid dashboard layout with executive summary cards above denser chart/feed/table details.
2. Given the user selects a supported VN stock or gold instrument from the system predefined watchlist, when the selection changes, then the chart, market details, freshness, and news/source feed reflect that instrument.
3. Given the dashboard displays source/news or market data, when the user inspects it, then the content is real seeded/demo data only and contains no LLM summaries, generated recommendations, or chat output.

## Functional Requirements

- **FR-001**: System MUST require successful login before any user can access workflow, result, or future protected surfaces.
- **FR-002**: System MUST bootstrap one internal admin account from environment variables at application startup and grant that account access to all V1 surfaces as they ship.
- **FR-002a**: System MUST read admin bootstrap values from `FINMIND_ADMIN_USERNAME`, `FINMIND_ADMIN_PASSWORD`, and `FINMIND_SESSION_SECRET`, and MUST fail closed when any required value is missing or invalid.
- **FR-003**: System MUST provide a workflow tab where users can choose a predefined V1 workflow, provide validated inputs, run bounded analysis, and inspect completed results.
- **FR-003a**: System MUST present fixed workflows as catalog cards before showing workflow-specific inputs.
- **FR-003b**: Workflow market and instrument controls MUST NOT expose US stocks or BTC as enabled selectable V1 options. If mock/demo UI needs to preview roadmap scope, those options MUST be disabled or clearly marked future/out-of-scope before execution rather than relying on backend validation after the user clicks Run.
- **FR-003c**: Workflow forms MUST render and submit every declared workflow input required by the selected workflow, including symbol inputs for single-instrument research workflows. Execution MUST use those inputs to select the target canonical records rather than defaulting to the first record in a market dataset.
- **FR-004**: System MUST model each fixed workflow as a declarative specification covering inputs, required datasets, execution stages, output sections, citation expectations, and chart requirements.
- **FR-005**: V1 MUST support VN stocks and gold as the first implementation market scope, while preserving contracts and data modeling that can later add US stocks and BTC without replacing the core platform.
- **FR-006**: V1 MUST ship an initial workflow set that includes TradingAgents-inspired roles such as fundamental analysis, technical analysis, macro analysis, and risk management where relevant to the selected market scope.
- **FR-008**: Phase 1 MUST maintain seeded/demo canonical storage for supported VN stock and gold datasets with source identity, collection time, effective market time, freshness metadata, and uniqueness rules.
- **FR-012**: System MUST construct reusable evidence objects that link generated claims to source data, citations, timestamps, and generated artifacts.
- **FR-013**: Every user-facing workflow result MUST expose citations and freshness metadata for material claims.
- **FR-014**: System MUST generate and display market chart artifacts for workflow outputs that require visual price, indicator, or trend analysis.
- **FR-016**: System MUST record execution logs for workflow runs, generated artifacts, failures, and user-visible output status.
- **FR-018**: System MUST expose result views where users can inspect completed workflow outputs, citations, charts, freshness, and execution status after the original run.
- **FR-018a**: System MUST expose one `History` section in the left rail that groups chat conversations and workflow runs under separate `Chat` and `Workflow Runs` subheaders, without date-based grouping in V1.
- **FR-018b**: Completed workflow runs MUST be listable from the protected API and restored into the `Workflow Runs` history after a full page reload while the authenticated session remains valid.
- **FR-019**: System MUST show clear out-of-scope behavior for unsupported markets, unsupported instruments, missing data, stale data, and unavailable citations.
- **FR-020**: System MUST show users evidence, citations, workflow stages, and tool or artifact status while retaining raw agent reasoning internally and excluding it from user-facing result views.
- **FR-021**: System MUST use cookie-backed web sessions for V1 authenticated application access.
- **FR-021a**: Session cookie values MUST be signed or otherwise verified using `FINMIND_SESSION_SECRET`; unsigned, malformed, or tampered session cookies MUST NOT authenticate protected content.
- **FR-022**: System MUST keep provider-specific market data details abstract at the product contract level while allowing implementation-time provider validation for technical and licensing suitability.
- **FR-023**: System MUST preserve separated product layers for app experience, API access, agent/core logic, and data workflows.
- **FR-024**: System MUST provide a chat-first shell with left-rail navigation labels `New Chat`, `Market`, `Workflows`, and `History`.
- **FR-026**: V1 Chat MUST use deterministic mock responses and MUST NOT execute arbitrary LLM-generated HTML.
- **FR-027**: V1 Chat MUST support inline trusted mock visual blocks and artifact cards for reports, charts, tables, evidence lists, and citation bundles.
- **FR-028**: Chat artifact cards MUST open in a right-side detail panel on desktop and full-screen artifact view on mobile.
- **FR-029**: Market MUST show real seeded/demo VN stock and gold data only, using a system predefined watchlist in V1.
- **FR-030**: Market MUST NOT show LLM summaries, generated recommendations, or chat-derived content in V1.
- **FR-031**: The authenticated UI MUST use a Perplexity-inspired light ledger visual theme by default while preserving token boundaries for dark mode later.
- **FR-031a**: The left rail MUST render primary navigation as flat icon-and-text rows where only the active nav row or selected history row receives a subtle neutral selected background; amber/yellow MUST NOT be used as rail selection color.
- **FR-025**: System MUST exclude trade execution, broker connectivity, portfolio order management, self-service registration, external identity providers, US stocks, and BTC from V1 user-facing market coverage.

## Key Entities

- Internal Admin User
- Session
- Market Instrument
- Canonical Market Data Record
- Source Document
- Workflow Specification
- Workflow Run
- Chat Conversation
- Chat Message
- Chat Artifact
- Evidence Object
- Citation
- Chart Artifact
- Execution Log

See `../system/state-model.md` for canonical entity definitions.

## Edge Cases

- Supported data exists but is stale: workflow outputs must display freshness warnings.
- A workflow partially completes: the result distinguishes completed sections, failed sections, and unavailable artifacts.
- Browser page reload after workflow completion: the authenticated UI reloads server-side persisted workflow runs and keeps completed result entries available in `History`.
- Citations are unavailable for a generated claim: the claim is omitted, qualified, or marked unsupported.
- Startup admin credentials are missing or invalid: the application fails closed.
- Unsupported US stock or BTC requests return a V1 scope limitation before execution where possible. Workflow forms must not let users run an unsupported market when the unsupported state is known at selection time.
- Chat mock artifact is too large for inline display: render an artifact card and open the full content in the right-side panel.
- Mobile user opens a chat artifact: use full-screen artifact mode instead of a cramped split panel.
- Market data is stale: show freshness warnings using real data metadata, not generated prose.

## Success Criteria

- **SC-001**: 100% of protected Phase 1 routes require login before displaying workflow or result content.
- **SC-002**: An authenticated admin user can complete a successful fixed workflow run and review cited output, freshness metadata, chart artifact, and execution status in under 5 minutes using available seeded/demo data.
- **SC-002a**: When required admin environment variables are present at startup, the configured admin credentials authenticate successfully without manual database setup.
- **SC-002b**: When any required admin environment variable is missing or invalid at startup, the application prevents unauthenticated access and reports configuration failure.
- **SC-003**: 100% of user-facing material claims in workflow outputs include at least one citation or are explicitly marked unsupported or unavailable.
- **SC-006**: At least 95% of supported workflow result views show freshness metadata for every referenced dataset.
- **SC-007**: Users can identify stale, missing, failed, or out-of-scope data conditions from the UI without reading server logs.
- **SC-007a**: After completing a workflow run and refreshing the page with a valid session, the completed run remains visible under `History` → `Workflow Runs` and can be reopened.
- **SC-008**: V1 supports at least one stock research path and one non-stock market research path across approved initial workflows.
- **SC-008a**: Workflow market controls expose only VN stock and gold as enabled runnable choices in V1; any US stock or BTC mock/roadmap preview is disabled or explicitly out-of-scope before Run.
- **SC-009**: After login, the default surface is `New Chat` and the left rail exposes `New Chat`, `Market`, `Workflows`, and grouped `History`.
- **SC-010**: A user can submit a chat message, receive a deterministic mock response, see an inline visual or artifact card, and open an artifact in the right-side panel without invoking a production LLM.
- **SC-011**: Market displays system predefined VN stock and gold watchlist data with chart, freshness, news/source feed, and market table while containing no LLM-generated content.

## Out Of Scope

- Admin ingestion operations and market data inspector; see `../002-data-operations/`.
- Production evidence-backed chat, arbitrary LLM-generated HTML rendering, and orchestrator-backed chat artifacts; see `../003-evidence-backed-chat/`.
- Production plugin adapter; see `../004-extension-hardening/`.
- US stocks and BTC as supported V1 markets.
