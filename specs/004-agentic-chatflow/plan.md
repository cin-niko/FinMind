---
id: SPEC-FEAT-004-PLAN
feature: agentic-chatflow
status: draft
owner: solo
created: 2026-06-26
implements: []
validated_by: []
adr_refs: []
---

# Implementation Plan: Agentic Chatflow

## Summary

Draft plan for a future evidence-backed Q&A chatflow over trusted finance sources.
This plan is intentionally not implementation-ready until source access, data
rights, collection strategy, citation policy, safety review, and performance goals
are finalized.

## Technical Context

- Existing foundation: MVP UI shell, artifact detail UI, workflow evidence/citation
  concepts, and LangChain-backed workflow agent runtime in
  `src/finmind_agents/runtime`.
- Unknowns to resolve before implementation: trusted source list, collection
  strategy, provider/data rights, model/tool policy, evaluation set, and latency
  targets.
- Future market scope starts from the mature VN stock and gold workflow scope
  unless a later spec expands it before implementation.
- Inherited foundation: Phase 02 established shared safe SSE event semantics,
  bounded sync offload, citation snapshots, artifact inspection, and persisted
  run foundations. Phase 04 defines chat-specific conversation, message,
  routing, persistence, and frontend behavior on top of those foundations.
- Moved Phase 02 scope: chatflow stream API coverage, completion/reinspection,
  fail-closed adapter validation, client reconciliation, services, routes,
  metadata persistence, mock-stream decision, and persisted reopen behavior are
  owned by this feature's `tasks.md`.

## Constitution Check

- Code quality: production chat entities and contracts must be separated from mock
  UI chat.
- Testing standards: answer grounding, citations, unsupported states, and safety
  refusals require automated and manual evaluation.
- Safety guardrails: no trading execution; human-in-the-loop required.
- UX consistency: chat surfaces follow `../system/ui-ux-guidelines.md`.
- Performance: unresolved; must be defined before implementation.
- Traceability: shared evidence/artifact contracts stay in `../system/`.

Gate result: draft only. Do not implement until open planning decisions are
resolved.
