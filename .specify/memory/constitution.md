<!--
Sync Impact Report
Version change: template -> 1.0.0
Modified principles:
- PRINCIPLE_1_NAME -> I. Canonical Specs First
- PRINCIPLE_2_NAME -> II. Bounded Feature Phases
- PRINCIPLE_3_NAME -> III. Evidence-Backed User Surfaces
- PRINCIPLE_4_NAME -> IV. Provider And Data Contract Discipline
- PRINCIPLE_5_NAME -> V. Verification Before Completion
Added sections:
- Platform Scope And Constraints
- Development Workflow And Quality Gates
Removed sections:
- Placeholder SECTION_2_NAME and SECTION_3_NAME
Templates requiring updates:
- ✅ .specify/templates/plan-template.md
- ✅ .specify/templates/spec-template.md
- ✅ .specify/templates/tasks-template.md
- ✅ .specify/templates/commands/*.md not present in this repository
Follow-up TODOs: none
-->
# FinMind Constitution

## Core Principles

### I. Canonical Specs First
All behavior, shared state, API contracts, runtime rules, security constraints, and UI
foundations MUST be specified before implementation. Shared contracts live under
`specs/system/`; bounded feature behavior lives under `specs/NNN-slug/`. Specs MUST
use YAML frontmatter with existing, valid references where references are declared.

Rationale: FinMind has multiple surfaces that depend on the same financial data and
evidence contracts. A single source of truth prevents divergent schemas, APIs, and UI
claims.

### II. Bounded Feature Phases
Work MUST remain inside the owning phase unless a spec explicitly changes scope.
Features MUST use append-only folders such as `001-mvp-workflow-platform/`,
`002-data-operations/`, `003-evidence-backed-chat/`, and
`004-extension-hardening/`. Shared entities MUST NOT be duplicated inside feature
specs when they belong in `specs/system/`.

Rationale: The product is being built incrementally. Keeping phases bounded preserves
reviewability and prevents later roadmap capabilities from destabilizing current work.

### III. Evidence-Backed User Surfaces
User-facing outputs MUST show grounded evidence, citations, freshness, stages, tool or
artifact status, and final results. User-facing surfaces MUST NOT expose raw agent
reasoning, hidden prompts, provider secrets, environment secrets, or unverifiable
claims. Chart and data artifacts MUST include enough metadata for users to inspect the
source and freshness of displayed values.

Rationale: FinMind is a finance research workbench. Trust depends on visible evidence,
not opaque reasoning traces.

### IV. Provider And Data Contract Discipline
Product contracts MUST describe provider-agnostic source connector behavior, canonical
schemas, licensing expectations, credentials, and failure modes. Implementation MAY
validate concrete providers and credentials behind connector contracts, but provider
secrets and vendor-specific details MUST stay out of user-facing contracts, logs, and
tests. Canonical market data MUST use typed schemas and idempotent persistence rather
than ad hoc payloads where the product depends on query performance or chart fidelity.

Rationale: Market providers can change. The platform must preserve stable internal
contracts while allowing implementation-level provider swaps.

### V. Verification Before Completion
Behavior changes MUST include verification proportional to their risk. Python work MUST
use focused pytest coverage and `uv run pytest` or a narrower justified subset before
completion. Frontend work MUST use the commands defined by `src/ui/package.json`.
Database/provider work MUST include tests for idempotency, schema mapping, failure
diagnostics, and no-secret leakage. Completion claims MUST cite fresh verification
results.

Rationale: Financial data operations fail silently without strict verification. Evidence
from tests and builds is required before work can be considered handled.

## Platform Scope And Constraints

V1 user-facing market scope is VN stocks and gold. US stocks, crypto, BTC, and other
markets are roadmap-only until an owning spec changes scope. Product-level specs MUST
keep provider details abstract while implementation specs MAY define connector
configuration, credential names, database services, and operational diagnostics.

Timeseries market data MUST be modeled for the access patterns users need: 1h VN stock
bars, 1h XAUUSD bars, and daily SJC gold quotes for phase 002. Large historical datasets
MUST use a time-series-capable PostgreSQL service or an explicitly justified equivalent.

## Development Workflow And Quality Gates

Feature work MUST follow this order:

1. Identify the owning spec from `specs/README.md`.
2. Update relevant `specs/system/*` and `specs/NNN-slug/*` files before code.
3. Implement the smallest scoped change matching the spec.
4. Add or update tests for changed behavior and contract boundaries.
5. Run relevant verification before reporting completion.

For new bounded capabilities, use the Spec Kit flow: specify, clarify when needed, plan,
tasks, and implement. If a feature changes shared contracts, update `specs/system/*` and
the cross-reference map in `specs/README.md`.

## Governance

This constitution supersedes informal practices and agent-specific shortcuts. Amendments
MUST be made in `.specify/memory/constitution.md`, include a Sync Impact Report, and
propagate any changed rules to Spec Kit templates and runtime guidance. Reviews MUST
check that feature specs, implementation, tests, and documentation comply with the
constitution.

Versioning follows semantic versioning:

- MAJOR: backward-incompatible governance or principle removals/redefinitions.
- MINOR: new principles, new governance sections, or materially expanded guidance.
- PATCH: clarifications, wording fixes, and non-semantic refinements.

**Version**: 1.0.0 | **Ratified**: 2026-06-19 | **Last Amended**: 2026-06-19
