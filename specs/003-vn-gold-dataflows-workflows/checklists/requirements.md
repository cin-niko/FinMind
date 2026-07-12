---
id: SPEC-FEAT-003-CHECKLIST
feature: vn-gold-dataflows-workflows
status: draft
owner: solo
created: 2026-07-11
implements: []
validated_by: []
adr_refs: []
---

# Specification Quality Checklist: VN And Gold Dataflows And Workflows

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-07-12
**Feature**: [`spec.md`](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain
- [ ] Requirements are testable and unambiguous
- [ ] Success criteria are measurable
- [x] Success criteria are technology-agnostic (no implementation details)
- [ ] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded
- [ ] Dependencies and assumptions identified

## Feature Readiness

- [ ] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [ ] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification

## Notes

- Blindspot pass completed on 2026-07-12. The detailed decision gates are in
  [`research.md`](../research.md#blindspot-pass-decisions-required-before-implementation).
- Language selection is canonical: persist `auto`, `vi`, or `en`; resolve
  Auto-detect from the browser list; submit and capture only `vi` or `en`; and
  fail safely if narrative cannot honor the captured language.
  Timestamp provenance is defined: show `market_time` as evidence time, retain
  `collected_at` for inspection, and do not calculate a fresh/stale
  classification. Field-level unavailable values are deterministically rendered
  before LLM analysis and do not change an otherwise successful conversation.
- Conversation ownership/retention is canonical: every workflow starts a new
  owner-filtered conversation; a conversation adapter maps the workflow result
  to its first assistant message; citations and artifacts belong to that
  message; deletion cascades through messages to their children and execution
  metadata but not shared canonical market data.
- Lifecycle is canonical: 120-second timeout fails; provider collection has at
  most two retries; disconnect does not cancel; startup fails interrupted
  conversations;
  cancellation, idempotency, queue/concurrency limits, and resume are deferred.
- Automated acceptance evidence is canonical: tests use deterministic mocks or
  fixtures only; live-provider contract validation is a separately recorded
  operational check and never a suite dependency.
- Acceptance scenarios do not yet cover financial restatements.
- SC-002 and SC-008 need workflow-level latency boundaries and a defined local-
  validation environment. The plan must resolve these before `/speckit-tasks`.
