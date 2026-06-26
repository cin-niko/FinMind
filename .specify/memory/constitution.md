<!--
Sync Impact Report
Version change: 1.0.0 -> 1.1.0
Modified principles:
- IV. Spec-First Traceability -> VI. Spec-First Traceability
Added principles:
- IV. Safety Guardrails And Human Control
- V. Performance Requirements Are Explicit
Added sections: None
Removed sections: None
Templates requiring updates:
- Updated .specify/templates/plan-template.md
- Updated .specify/templates/spec-template.md
- Updated .specify/templates/tasks-template.md
- Checked .specify/templates/commands/*.md (not present)
- Checked README.md
- Updated AGENTS.md
Follow-up TODOs: None
-->
# FinMind Constitution

**Version**: 1.1.0 | **Ratified**: 2026-06-26 | **Last Amended**: 2026-06-26

## Core Principles

### I. Code Quality Is A Contract

All production code MUST be typed, cohesive, and organized around clear ownership
boundaries. Shared behavior MUST live in one canonical module or spec, not in
duplicated implementations. Python code MUST follow `.agents/skills/python-guidelines/SKILL.md`
when that skill applies. Changes MUST prefer established project patterns over new
abstractions unless the new abstraction removes meaningful complexity.

Rationale: FinMind handles evidence-backed financial workflows; unclear ownership,
duplicated schemas, or weak typing make outputs harder to trust and maintain.

### II. Tests Prove Behavior

Every behavior change MUST include verification proportional to its risk. New or
changed Python behavior MUST be covered by `uv run pytest` or a narrower pytest
target documented in the handoff. Frontend changes MUST use the verification
commands defined by `src/ui/package.json`. Tests MAY be omitted only when the
change is documentation-only or when the relevant spec/plan explicitly records
why automated coverage is not practical.

Rationale: Passing tests are the project's minimum evidence that implementation
still matches the spec and existing behavior has not regressed.

### III. User Experience Consistency

User-facing changes MUST follow `specs/system/ui-ux-guidelines.md` and preserve a
consistent workbench experience across navigation, controls, status messaging,
citations, freshness, artifacts, and error states. UI surfaces MUST show grounded
evidence and execution state, not raw agent reasoning. New UX patterns MUST be
specified before implementation and reused when they become shared behavior.

Rationale: Analysts need predictable, evidence-oriented workflows; inconsistent
UI behavior reduces trust in research output and slows repeated use.

### IV. Safety Guardrails And Human Control

FinMind MUST preserve human control over financial interpretation, workflow
execution, and any user-visible recommendation. User-facing surfaces MUST show
evidence, citations, freshness, tool/artifact status, and bounded outputs; they
MUST NOT expose raw agent reasoning, hidden prompts, provider secrets, credentials,
or unsafe internal diagnostics. Unsupported markets, missing evidence, stale data,
failed tools, and unavailable providers MUST be blocked or clearly marked before
the user can rely on the output. Any workflow that could affect trading judgment
MUST keep the analyst in the loop and avoid autonomous execution of trades,
orders, or irreversible financial actions.

Rationale: FinMind supports financial research, not unchecked financial action.
Guardrails and explicit human review preserve user trust and reduce operational,
compliance, and data-quality risk.

### V. Performance Requirements Are Explicit

Each feature plan MUST state performance goals, constraints, or an explicit `N/A`
with rationale. Performance-sensitive paths, including workflow execution, API
responses, chart rendering, data loading, and retrieval/tool calls, MUST define
measurable expectations before implementation. Regressions against documented
performance expectations MUST be treated as defects.

Rationale: Financial research workflows are operational tools; unbounded latency,
memory use, or rendering cost degrades analyst throughput and reliability.

### VI. Spec-First Traceability

Behavior and contracts MUST be specified before implementation. Shared state,
runtime, API, security, and UI contracts MUST live in `specs/system/`; bounded
feature behavior MUST live in `specs/NNN-slug/`; decisions MUST live in
`docs/adr/`; risks MUST live in `docs/risks/`. Implementations and tests MUST be
traceable to the owning spec, and schemas or requirement tables MUST not be
duplicated across files.

Rationale: A single source of truth keeps agent-assisted work auditable and keeps
future feature changes from diverging across docs, code, and tests.

## Engineering Standards

FinMind uses Python 3.12, FastAPI, pytest, and a Vite frontend. Backend code MUST
keep API, platform services, repositories, and reusable agent substrate boundaries
separate. Frontend code MUST preserve the UI foundations in `specs/system/ui-ux-guidelines.md`
and avoid introducing unsupported market scope or provider details into product
contracts. Secrets MUST remain out of docs, logs, UI, tests, telemetry, and
generated artifacts.

All specs MUST use YAML frontmatter with `id`, lifecycle status, `implements`,
`validated_by`, and `adr_refs`. Referenced paths MUST exist unless the spec is
explicitly draft and uses an empty list for not-yet-implemented code.

## Development Workflow

Feature work MUST start by reading `AGENTS.md`, `specs/README.md`, and the owning
system or feature spec. If behavior, safety posture, or contracts change, update
the spec first, then implementation, then tests. Plans MUST complete the
Constitution Check before Phase 0 research and re-check after Phase 1 design.
Tasks MUST be grouped by independently testable user stories and include quality,
testing, safety, UX, and performance work where applicable.

Completion handoffs MUST summarize changed specs, code, and verification results.
If verification cannot be run, the handoff MUST state the exact command skipped
and why.

## Governance

This constitution supersedes conflicting local practices. Amendments MUST update
this file, assign a semantic version bump, update the Last Amended date, and
propagate changes to dependent templates and runtime guidance.

Versioning policy:
- MAJOR: Backward-incompatible governance changes or principle removals.
- MINOR: New principles, sections, or materially expanded requirements.
- PATCH: Clarifications, wording fixes, or non-semantic refinements.

Compliance review is required during planning, implementation review, and final
handoff. Any exception to a MUST-level rule requires a documented rationale in the
owning spec, plan, ADR, or risk record.
