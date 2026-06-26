---
id: SPEC-FEAT-001-RESEARCH
feature: mvp-ui
status: active
owner: solo
created: 2026-06-26
implements: []
validated_by: []
adr_refs: []
---

# Research: MVP UI

## Decision: Keep the first screen as the app shell

The first authenticated screen is `New Chat`, not a landing page.

Rationale: FinMind is an internal financial research platform. Users need the usable research shell
immediately after login.

Alternatives considered: marketing-style landing page. Rejected because it delays
the core application flow.

## Decision: Keep MVP UI chat deterministic

`001-mvp-ui` chat responses and artifacts are deterministic local UI behavior.

Rationale: This validates shell, artifact, and layout behavior before production
agentic chatflow is specified.

Alternatives considered: early production chat orchestration. Rejected because
source access, retrieval, citations, and safety contracts are not ready.
