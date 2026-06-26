---
id: SPEC-INDEX-FINMIND
status: active
last_review: 2026-06-18
implements: []
validated_by: []
adr_refs:
  - docs/adr/0001-vn-only-v1-market-scope.md
  - docs/adr/0005-phase-003-m1-m2-chat-milestones.md
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
| `002-data-operations/` | pending (parked 2026-06-26) | Market data platform groundwork for VN100 canonical storage remains, but full real-data ingestion is parked until reliable data rights/access or operator import files are available. Demo fixtures must not be used as completion substitute. | `001-mvp-workflow-platform/`, `system/*` |
| `003-evidence-backed-chat/` | draft (pivoted 2026-06-26) | M1: workflow/chatflow over real-time retrieval tools with citations/freshness/tool evidence, not dependent on a populated Phase 002 market DB. M2: fundamentals layer after concrete use cases. | `001-mvp-workflow-platform/`, `system/*`; later resumes `002-data-operations/` when data source is resolved |
| `004-extension-hardening/` | draft | Plugin-ready execution artifact and evidence contracts without shipping an external adapter. | `001-mvp-workflow-platform/`, `003-evidence-backed-chat/`, `system/*` |

## Related Research

Non-normative product and market research. Link here instead of duplicating in
feature specs.

| Document | Relevance |
|----------|-----------|
| [`docs/research/perplexity-finance.md`](../docs/research/perplexity-finance.md) | Perplexity Finance benchmark (surfaces, data providers, Finance Search API, FinMind comparison). Primary input for `003-evidence-backed-chat/` M1/M2 scoping and SC-010 M2 use cases. |

## Requirement Coverage

| Requirement | Owner Spec | Notes |
|-------------|------------|-------|
| FR-001 | `001-mvp-workflow-platform/spec.md`, `system/runtime-config-security.md` | Login required for all protected surfaces. |
| FR-002 | `001-mvp-workflow-platform/spec.md`, `system/runtime-config-security.md` | Single environment-configured admin. |
| FR-002a | `001-mvp-workflow-platform/spec.md`, `system/runtime-config-security.md` | `FINMIND_ADMIN_USERNAME`, `FINMIND_ADMIN_PASSWORD`, `FINMIND_SESSION_SECRET`; fail closed. |
| FR-003 | `001-mvp-workflow-platform/spec.md`, `system/ui-workbench.md` | Workflow tab, catalog cards, declared workflow inputs, bounded workflow execution, and V1-only enabled market controls. |
| FR-004 | `001-mvp-workflow-platform/spec.md`, `system/state-model.md` | Declarative workflow specifications. |
| FR-005 | `001-mvp-workflow-platform/spec.md`, `system/runtime-config-security.md` | VN stocks only in V1 (VN100 universe); US stocks, BTC, XAUUSD, and SJC gold roadmap only. Superseded prior "VN stocks and gold" V1 scope on 2026-06-25. |
| FR-006 | `001-mvp-workflow-platform/spec.md` | TradingAgents-inspired roles in fixed workflows. |
| FR-007 | `003-evidence-backed-chat/spec.md` | Chat deferred until shared workflow/evidence contracts exist. Phase 003 M1 now uses real-time retrieval tools because Phase 002 market-data population is pending. |
| FR-024 | `001-mvp-workflow-platform/spec.md`, `system/ui-workbench.md` | Active shell navigation exposes New Chat, Workflows, and History; Market and Admin ingestion are hidden while Phase 002 is parked. |
| FR-026 | `003-evidence-backed-chat/spec.md` | M2: fundamentals data layer (companies, financial_facts, earnings) via Phase 002 source connector contract; schema driven by ≥3 concrete chat use cases. |
| FR-027 | `003-evidence-backed-chat/spec.md` | M2: fundamentals ingestion shares the canonical idempotent ingestion path, overlap guard, and lineage with price ingestion. |
| FR-028 | `003-evidence-backed-chat/spec.md` | M2: fundamentals citable via existing evidence/citation contracts with point-in-time semantics. |
| FR-029 | `003-evidence-backed-chat/spec.md` | M2: fiscal-period-aware freshness rule distinct from price freshness. |
| FR-008 | `system/state-model.md`, `001-mvp-workflow-platform/spec.md`, `002-data-operations/spec.md` | Seeded/demo storage in Phase 1; ingestion-backed storage in Phase 2. |
| FR-008a | `002-data-operations/spec.md` | PostgreSQL-compatible TimescaleDB is the canonical phase 002 database service; tests and local verification use Docker Compose TimescaleDB/PostgreSQL. |
| FR-008b | `002-data-operations/spec.md`, `002-data-operations/data-model.md` | V1: PostgreSQL stores shared metadata/evidence tables plus typed time-series tables for `vn_prices_daily` (canonical) and `vn_prices` 1h (best-effort). XAUUSD/SJC/US schemas remain in `data-model.md` as roadmap. |
| FR-008h | `002-data-operations/spec.md` | Pre-seeded VN100 universe from static CSV; instrument creation outside the universe is rejected in V1. |
| FR-010q | `002-data-operations/spec.md` | Lazy on-first-access daily fetch for VN100 tickers with no `vn_prices_daily` rows; out-of-universe tickers return out-of-scope. |
| FR-010r | `002-data-operations/spec.md` | `vn_prices_daily` is the canonical V1 timeframe; default chart timeframe `1d`; `vn_prices` 1h is best-effort. |
| FR-018e | `002-data-operations/spec.md`, `system/ui-workbench.md` | V1 market/admin/workflow surfaces are VN-only; roadmap markets disabled or marked out-of-scope. |
| FR-008c | `002-data-operations/spec.md`, `002-data-operations/data-model.md` | PostgreSQL typed time-series uniqueness, overlap checks, and traceability constraints. |
| FR-008d | `002-data-operations/spec.md`, `002-data-operations/data-model.md` | Market-specific typed schemas for `vn_prices` 1h OHLCV records, `xauusd_prices` 1h OHLC records, and `sjc_gold_prices` daily quote records. |
| FR-008e | `002-data-operations/spec.md`, `002-data-operations/data-model.md` | Price time-series tables are TimescaleDB hypertables or equivalent PostgreSQL time partitions. |
| FR-008f | `002-data-operations/spec.md`, `002-data-operations/data-model.md` | Market instrument classification metadata for asset class, sector, industry, exchange, currency, status, and display name. |
| FR-008g | `002-data-operations/spec.md`, `002-data-operations/data-model.md` | Market collections and effective-dated memberships for indexes, watchlists, sectors, and themes. |
| FR-009 | `002-data-operations/spec.md` | Market data, price series, indicators, reports, macro/news material. |
| FR-009a | `002-data-operations/spec.md` | Initial phase 002 populated datasets are `vn_prices`, `xauusd_prices`, and `sjc_gold_prices`; other source types remain connector extension points until required by approved workflows. |
| FR-010 | `002-data-operations/spec.md` | Scheduled and admin-triggered ingestion. |
| FR-010a | `002-data-operations/spec.md`, `system/contracts.md` | Scheduled ingestion uses an explicit scheduler/worker contract rather than app startup or demo history only. |
| FR-010b | `002-data-operations/spec.md`, `system/contracts.md` | Protected worker API endpoint invokes scheduled ingestion for supported datasets. |
| FR-011 | `002-data-operations/spec.md` | Idempotent manual ingestion with status and diagnostics. |
| FR-011a | `002-data-operations/spec.md`, `system/state-model.md`, `system/runtime-config-security.md` | Overlapping ingestion for the same dataset and period is blocked with visible status. |
| FR-012 | `system/state-model.md`, `001-mvp-workflow-platform/spec.md` | Evidence objects. |
| FR-013 | `system/contracts.md`, `001-mvp-workflow-platform/spec.md`, `003-evidence-backed-chat/spec.md` | Citations and freshness for material claims. |
| FR-014 | `001-mvp-workflow-platform/spec.md`, `003-evidence-backed-chat/spec.md` | Chart artifacts for workflow and chat outputs. |
| FR-015 | `003-evidence-backed-chat/spec.md` | Inline visualization artifacts. |
| FR-016 | `system/state-model.md`, `001-mvp-workflow-platform/spec.md`, `002-data-operations/spec.md`, `003-evidence-backed-chat/spec.md` | Execution logs across runs, tool calls, ingestion, artifacts, failures, output status. |
| FR-017 | `003-evidence-backed-chat/spec.md`, `system/contracts.md` | Workflow agents vs generic role agents with shared contracts. |
| FR-018 | `001-mvp-workflow-platform/spec.md`, `003-evidence-backed-chat/spec.md` | Result views and reload-restored history for completed workflow and chat outputs. |
| FR-018a | `002-data-operations/spec.md` | Dataset-specific freshness calculation for `vn_prices`, `xauusd_prices`, `sjc_gold_prices`, missing records, and failed latest ingestion. |
| FR-018b | `002-data-operations/spec.md`, `system/ui-workbench.md` | Market page with VN Markets selector, required VN index mini charts, sortable 10-row instrument list, and final filterable heatmap. |
| FR-018c | `002-data-operations/spec.md`, `system/ui-workbench.md` | Instrument detail charts support `1h`, `4h`, `1d`, and `1M` timeframe selections where available. |
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
