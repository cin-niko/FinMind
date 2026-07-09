---
id: SPEC-FEAT-003-PLAN
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
- Current market scope: VN stocks and US stocks only.

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
