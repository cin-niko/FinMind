---
id: SPEC-INDEX-FINMIND
status: active
last_review: 2026-06-18
implements: []
validated_by: []
adr_refs: []
---

# Specs Index

This directory separates stable platform-wide specifications from bounded feature specifications managed by Spec Kit.

## Layout

| Path | Purpose |
|------|---------|
| `system/` | Platform-wide specs: state model, contracts, runtime behavior, config, security, and UI foundations. Stable across features. |
| `NNN-slug/` | Per-feature specs, one folder per bounded capability. Created append-only with a zero-padded number and kebab-case slug. Managed by `/speckit-specify`, `/speckit-plan`, `/speckit-tasks`, and `/speckit-implement`. |

## Spec Lifecycle

All spec files use YAML frontmatter for traceability.

System specs:

```yaml
---
id: SPEC-SYSTEM-ID
status: active
last_review: 2026-06-18
implements: []
validated_by: []
adr_refs: []
---
```

Feature specs:

```yaml
---
id: SPEC-FEAT-001
feature: mvp-workflow-platform
status: draft
owner: solo
created: 2026-06-18
implements: []
validated_by:
  - tests/test_app.py
  - tests/test_platform_services.py
adr_refs: []
---
```

`make check-specs` should verify that `implements:` and `validated_by:` paths exist and that `adr_refs:` resolve to files in `docs/adr/`. Draft specs should leave `implements: []` until the referenced code exists.

## Current Spec Map

| Spec | Status | Scope | Depends On |
|------|--------|-------|------------|
| `system/state-model.md` | active | Shared domain entities, lifecycle states, execution records, evidence, citations, artifacts, and ingestion state. | None |
| `system/contracts.md` | active | Stable API and artifact contract rules shared across features. | `system/state-model.md` |
| `system/runtime-config-security.md` | active | Runtime behavior, auth/session rules, admin bootstrap, scope gates, and safety constraints. | `system/state-model.md` |
| `system/ui-workbench.md` | active | Analyst workbench design system and shared UI rules. | `system/contracts.md` |
| `001-mvp-workflow-platform/` | draft | Authenticated app shell, fixed workflow execution, cited results, chart artifacts, result inspection. | `system/*` |
| `002-data-operations/` | draft | Admin ingestion, scheduled/manual jobs, idempotent reruns, freshness, market data inspector. | `001-mvp-workflow-platform/`, `system/*` |
| `003-evidence-backed-chat/` | draft | Chat surface over shared evidence, citations, artifacts, freshness, and execution records. | `001-mvp-workflow-platform/`, `002-data-operations/`, `system/*` |
| `004-extension-hardening/` | draft | Plugin-ready execution artifact and evidence contracts without shipping an external adapter. | `001-mvp-workflow-platform/`, `003-evidence-backed-chat/`, `system/*` |

## Requirement Coverage

| Requirement | Owner Spec | Notes |
|-------------|------------|-------|
| FR-001 | `001-mvp-workflow-platform/spec.md`, `system/runtime-config-security.md` | Login required for all protected surfaces. |
| FR-002 | `001-mvp-workflow-platform/spec.md`, `system/runtime-config-security.md` | Single environment-configured admin. |
| FR-002a | `001-mvp-workflow-platform/spec.md`, `system/runtime-config-security.md` | `FINMIND_ADMIN_USERNAME`, `FINMIND_ADMIN_PASSWORD`, `FINMIND_SESSION_SECRET`; fail closed. |
| FR-003 | `001-mvp-workflow-platform/spec.md`, `system/ui-workbench.md` | Workflow tab, catalog cards, declared workflow inputs, bounded workflow execution, and V1-only enabled market controls. |
| FR-004 | `001-mvp-workflow-platform/spec.md`, `system/state-model.md` | Declarative workflow specifications. |
| FR-005 | `001-mvp-workflow-platform/spec.md`, `system/runtime-config-security.md` | VN stocks and gold in V1; US stocks and BTC roadmap only. |
| FR-006 | `001-mvp-workflow-platform/spec.md` | TradingAgents-inspired roles in fixed workflows. |
| FR-007 | `003-evidence-backed-chat/spec.md` | Chat deferred until shared workflow/evidence contracts exist. |
| FR-008 | `system/state-model.md`, `001-mvp-workflow-platform/spec.md`, `002-data-operations/spec.md` | Seeded/demo storage in Phase 1; ingestion-backed storage in Phase 2. |
| FR-009 | `002-data-operations/spec.md` | Market data, price series, indicators, reports, macro/news material. |
| FR-010 | `002-data-operations/spec.md` | Scheduled and admin-triggered ingestion. |
| FR-011 | `002-data-operations/spec.md` | Idempotent manual ingestion with status and diagnostics. |
| FR-012 | `system/state-model.md`, `001-mvp-workflow-platform/spec.md` | Evidence objects. |
| FR-013 | `system/contracts.md`, `001-mvp-workflow-platform/spec.md`, `003-evidence-backed-chat/spec.md` | Citations and freshness for material claims. |
| FR-014 | `001-mvp-workflow-platform/spec.md`, `003-evidence-backed-chat/spec.md` | Chart artifacts for workflow and chat outputs. |
| FR-015 | `003-evidence-backed-chat/spec.md` | Inline visualization artifacts. |
| FR-016 | `system/state-model.md`, `001-mvp-workflow-platform/spec.md`, `002-data-operations/spec.md`, `003-evidence-backed-chat/spec.md` | Execution logs across runs, tool calls, ingestion, artifacts, failures, output status. |
| FR-017 | `003-evidence-backed-chat/spec.md`, `system/contracts.md` | Workflow agents vs generic role agents with shared contracts. |
| FR-018 | `001-mvp-workflow-platform/spec.md`, `003-evidence-backed-chat/spec.md` | Result views and reload-restored history for completed workflow and chat outputs. |
| FR-019 | `system/runtime-config-security.md`, `001-mvp-workflow-platform/spec.md`, `002-data-operations/spec.md`, `003-evidence-backed-chat/spec.md` | Out-of-scope, unsupported, missing, stale, unavailable citation states; known unsupported workflow choices are blocked or marked before execution. |
| FR-020 | `system/runtime-config-security.md`, `001-mvp-workflow-platform/spec.md`, `003-evidence-backed-chat/spec.md` | Show evidence/status; hide raw reasoning. |
| FR-021 | `system/runtime-config-security.md`, `001-mvp-workflow-platform/spec.md` | Cookie-backed sessions verified with `FINMIND_SESSION_SECRET`. |
| FR-022 | `system/contracts.md`, `002-data-operations/spec.md` | Provider abstraction. |
| FR-023 | `system/contracts.md`, `004-extension-hardening/spec.md` | Separated product layers and reusable agent platform. |
| FR-024 | `004-extension-hardening/spec.md`, `system/contracts.md` | Integration-ready artifacts and execution contracts. |
| FR-025 | `system/runtime-config-security.md`, `001-mvp-workflow-platform/spec.md` | Explicit V1 exclusions, including no enabled US stock or BTC controls in mock/demo V1 surfaces. |

## Migration Notes

- The former monolithic V1 material was split by bounded capability.
- Shared contracts, state, runtime/config/security, and UI guidance moved to `system/`.
- No functional requirement or success criterion was intentionally dropped; use the coverage table above when reviewing future edits.
