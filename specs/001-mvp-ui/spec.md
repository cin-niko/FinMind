---
id: SPEC-FEAT-001
feature: mvp-ui
status: active
owner: solo
created: 2026-06-26
implements:
  - src/finmind_ui
  - src/finmind_api
validated_by:
  - tests/test_app.py
adr_refs: []
---

# Feature Specification: MVP UI

## Summary

Deliver the authenticated FinMind application shell: login, session-aware access,
left-rail navigation, chat-first landing surface, grouped history layout, mock
artifact detail behavior, and the shared light ledger UI treatment.

This feature owns the user-facing shell and UI foundations only. Fixed workflow
execution belongs to `../002-workflow/`. Production evidence-backed agentic
chatflow belongs to `../004-agentic-chatflow/`.

## User Scenarios & Testing

### User Story 1 - Access Login-Required Shell (Priority: P1)

An internal admin user accesses the authenticated app shell, while unauthenticated
visitors are blocked from protected content.

**Independent Test**: Attempt to access protected app/session behavior before
login, log in with environment-configured admin credentials, navigate the shell,
log out, and confirm protected content is blocked again.

Acceptance scenarios:

1. Given no active session exists, when a visitor opens protected app content,
   then the system requires login.
2. Given valid admin credentials, when the user logs in, then the app shell opens.
3. Given the user logs out or the session expires, when protected content is
   requested, then the user is treated as unauthenticated.
4. Given required admin environment values are missing or invalid at startup, when
   the app starts, then protected content remains unavailable.

### User Story 2 - Use Chat-First Shell With Mock Artifacts (Priority: P1)

An authenticated internal user lands on a new chat surface, submits a finance
research prompt, receives a deterministic mock response, and can open trusted mock
artifacts in a detail panel.

**Independent Test**: Log in, confirm `New Chat` is the default surface, submit a
message, verify a deterministic mock response with inline visual content or
artifact cards, and open an artifact detail view.

Acceptance scenarios:

1. Given the admin user is logged in, when the shell loads, then the default active
   surface is `New Chat`.
2. Given the user submits the first chat message, when the mock response appears,
   then the conversation is added to grouped `History`.
3. Given a mock artifact card is clicked, when the viewport is desktop-sized, then
   the artifact opens in a right-side detail panel.
4. Given a mock artifact card is clicked on mobile, then the artifact opens in a
   full-screen artifact view.

### User Story 3 - Navigate Workflows And History (Priority: P2)

An authenticated internal user can move between `New Chat`, `Workflows`, and
grouped `History` without layout instability or hidden roadmap surfaces.

**Independent Test**: Log in, switch between shell surfaces, inspect grouped
history sections, and confirm unsupported roadmap surfaces are not active
navigation entries.

Acceptance scenarios:

1. Given the user is authenticated, when they use the left rail, then `New Chat`,
   `Workflows`, and grouped `History` are available.
2. Given roadmap features are not canonical, when the shell renders, then native
   Market, Admin ingestion, production chat orchestration, plugin, and
   other future asset surfaces are not enabled navigation entries.

## Functional Requirements

- **FR-001**: System MUST require successful login before protected app content is
  shown.
- **FR-002**: System MUST bootstrap one internal admin account from environment
  variables and fail closed when required values are missing or invalid.
- **FR-003**: System MUST use signed or otherwise verified cookie-backed sessions.
- **FR-004**: The authenticated shell MUST default to `New Chat`.
- **FR-005**: The shell MUST expose left-rail navigation for `New Chat`,
  `Workflows`, and grouped `History`.
- **FR-006**: History MUST group chat conversations and workflow runs under
  separate `Chat` and `Workflow Runs` subheaders.
- **FR-007**: `001-mvp-ui` chat UI MUST use deterministic mock responses only and
  MUST NOT present itself as production evidence-backed chatflow.
- **FR-008**: Mock artifact cards MUST open in a detail panel on desktop and a
  full-screen artifact view on mobile.
- **FR-009**: Mock artifact detail MUST NOT execute arbitrary generated HTML.
- **FR-010**: UI MUST follow `../system/ui-ux-guidelines.md`.
- **FR-011**: User-facing surfaces MUST show status and errors without raw agent
  reasoning, secrets, or hidden prompts.

## Key Entities

- Internal Admin User
- Session
- Mock Chat Conversation
- Chat Message
- Chat Artifact

See `../system/state-model.md` for canonical entity definitions.

## Edge Cases

- Missing or invalid admin configuration: protected shell fails closed.
- Tampered session cookie: protected content is blocked.
- Artifact too large for inline rendering: show an artifact card and detail view.
- Mobile artifact detail: use full-screen artifact mode.
- Roadmap surface requested directly: show unavailable or not-found behavior
  rather than enabling unsupported navigation.

## Assumptions

- `001-mvp-ui` serves authenticated internal users only.
- The chat surface in this feature is a deterministic UI prototype, not real
  agentic chatflow.
- Workflow-specific result contents are owned by `../002-workflow/`.

## Success Criteria

- **SC-001**: 100% of protected app/session surfaces require login.
- **SC-002**: A configured admin can log in, reach `New Chat`, navigate to
  `Workflows`, inspect grouped `History`, and log out in under 2 minutes.
- **SC-003**: Mock artifact cards open the correct detail surface on desktop and
  mobile without executing generated HTML.
- **SC-004**: Users can identify authentication errors, loading states, and
  unavailable surfaces without reading logs.
- **SC-005**: No user-facing shell surface exposes raw agent reasoning.

## Out Of Scope

- Fixed workflow execution and cited workflow outputs.
- Production evidence-backed agentic chatflow.
- Native market data/news platform.
- Trade execution, broker connectivity, autonomous decisions, and
  other non-current assets.
