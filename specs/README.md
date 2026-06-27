---
id: SPEC-INDEX-FINMIND
status: active
last_review: 2026-06-26
implements: []
validated_by: []
adr_refs: []
---

# Specs Index

This directory is the canonical product and platform specification source for
FinMind. It contains shared system contracts plus bounded feature specs managed
through Spec Kit.

## Current Product Direction

FinMind is an agentic AI platform for financial trading research. The short-term
product goal is advice support, not trading decisions: fixed analysis workflows
and flexible chat-style research surfaces must be data-driven, grounded in trusted
sources, and backed by evidence/citations for material claims.

The long-term direction is a Perplexity Finance-like native financial management
ecosystem with market data, news, and richer data operations in-app. That direction
is intentionally not specified as an active feature until reliable data rights,
source access, and implementation scope are ready.

## Layout

| Path | Purpose |
|------|---------|
| `system/` | Platform-wide specs: state model, contracts, runtime behavior, config, security, safety, and UI foundations. |
| `NNN-slug/` | Per-feature specs, plans, tasks, and supporting artifacts for one bounded capability. Managed by Spec Kit slash commands: `/speckit-specify`, `/speckit-plan`, `/speckit-tasks`, and `/speckit-implement`. |
| `001-mvp-ui/` | Implemented MVP app shell, auth, deterministic mock chat UI, artifact detail, navigation, history layout, and UI foundations. |
| `002-workflow/` | Draft phase 02 workflow suite for UI-runnable fundamental analysis, technical analysis, news digest, risk review, combined stock briefs, VN/US stock scope, evidence/citations, freshness, chart artifacts, and run inspection. |
| `003-agentic-chatflow/` | Draft future evidence-backed flexible Q&A chatflow over trusted sources. |

Future feature folders must be created append-only with Spec Kit only when their
scope is ready to become canonical.

## Spec Kit Conventions

Each bounded feature lives in one `NNN-slug/` folder and should contain only the
artifacts for that capability:

- `spec.md`: user value, scenarios, functional requirements, success criteria,
  assumptions, and out-of-scope boundaries.
- `plan.md`: technical context, constitution checks, design decisions, gates,
  and links to shared system specs.
- `research.md`: planning decisions and rejected alternatives.
- `data-model.md`: feature usage of canonical system entities and any
  feature-owned state.
- `contracts/`: API, UI, artifact, command, or other interface contracts owned
  by the feature.
- `quickstart.md`: runnable validation guide.
- `tasks.md`: implementation task plan grouped by independently testable user
  stories.
- `checklists/`: quality or readiness checklists generated during Spec Kit
  workflow steps.

Shared state, API rules, runtime/security posture, and UI/UX foundations stay in
`system/`. Feature folders may reference or extend shared contracts for their
capability, but must not redefine system entities or cross-feature rules
differently.

## Spec Lifecycle

All spec files use YAML frontmatter for traceability.

System specs:

```yaml
---
id: SPEC-SYSTEM-ID
status: active
last_review: 2026-06-26
implements: []
validated_by: []
adr_refs: []
---
```

Feature specs:

```yaml
---
id: SPEC-FEAT-001
feature: mvp-ui
status: active
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
```

Draft specs should leave `implements: []` until code lands. Referenced paths in
`implements:`, `validated_by:`, and `adr_refs:` must exist.
