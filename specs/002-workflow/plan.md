---
id: SPEC-FEAT-002-PLAN
feature: workflow
status: active
owner: solo
created: 2026-06-26
implements:
  - src/api/platform/workflows
  - src/api/platform/models.py
  - src/api/platform/memory.py
  - src/ui/src/features/workflows
  - src/ui/src/features/results/ResultView.tsx
validated_by:
  - tests/test_app.py
  - tests/test_platform_services.py
  - src/ui/package.json
adr_refs:
  - docs/adr/ADR-001-hybrid-workflow-definitions-and-agent-skills.md
---

# Implementation Plan: Workflow

## Summary

Implement Phase 02 fixed, UI-runnable financial trading support workflows for VN
stocks and US stocks. The backend will replace the earlier gold-oriented workflow
scaffold with a guarded runtime that executes YAML workflow definitions and
governed Markdown agent skills for `data-collector`, `data-quality-check`,
`fundamental-analysis`, `technical-analysis`, `news-digest`, `risk-review`, and
the composite `stock-brief`. The data collector will fetch latest available
provider data for supported symbols before using deterministic seeded/offline
fallback records. The UI will show the workflow catalog, required inputs, stage
execution status, quality warnings, citations, freshness, chart artifacts, and
completed run inspection.

## Technical Context

- Language/version: Python 3.12 backend, TypeScript React/Vite frontend.
- Backend dependencies: FastAPI, Pydantic, `httpx`, retrieval-first dataflow
  adapters, in-memory fallback repositories, existing `src/api/platform`
  services, pytest.
- Market-data providers: `vnstock` adapter for VN stock latest price and
  fundamentals; US provider adapter using Alpha Vantage for current/daily
  prices and market news when an API key is configured; SEC EDGAR company facts
  adapter for public-company fundamentals; deterministic offline fallback for
  tests and provider outage paths.
- Frontend dependencies: React/Vite, existing app shell, existing workflow/result
  pages, Lightweight Charts.
- Storage: in-memory canonical record cache/repository for Phase 02 provider
  results plus deterministic offline fallback records; no database migration.
- Testing: `UV_CACHE_DIR=/private/tmp/finmind-uv-cache uv run --group dev python -m pytest`
  and `npm run build` in `src/ui`.
- Target platform: internal browser app backed by FastAPI JSON APIs.
- Performance goals: supported offline workflow runs complete under 3 seconds in
  automated tests. Live provider collection should target a 15-second per-run
  timeout budget, with per-provider timeout/failure surfaced to
  `data-quality-check`.
- Constraints: VN stocks and US stocks only; gold/BTC/other assets blocked or
  roadmap-marked; no broker/order/trade execution; no raw reasoning exposure.
- Scale/scope: latest provider fetch for one requested symbol per run, small
  canonical in-memory cache/fallback datasets, one authenticated internal admin,
  single-process execution.

## Constitution Check

- Code quality: keep YAML workflow definition loading, Markdown skill loading,
  validation, collection, quality gates, step execution, artifacts, and run
  repositories in separate modules under `src/api/platform/workflows` or existing
  platform modules.
- Testing standards: add/adjust pytest coverage for catalog, VN/US runs,
  unsupported assets, composite `stock-brief`, data-quality gating, citations,
  chart artifacts, and run reinspection; run frontend build for UI contract
  compatibility.
- Safety guardrails: unsupported assets are blocked, data-quality warnings gate
  claims, material claims require citations or unavailable marking, raw reasoning
  is excluded, and outputs remain advice support only.
- UX consistency: workflow catalog, forms, run result, stage status, data-quality
  warnings, citations, freshness, and artifacts follow
  `../system/ui-ux-guidelines.md`.
- Performance requirements: offline workflow execution target is under 3 seconds
  in automated tests; live provider collection has a 15-second per-run timeout
  budget and must surface timeout/failure state through `data-quality-check`.
- Spec traceability: feature behavior lives in this folder; shared state,
  contracts, runtime/security, and UI rules remain in `../system/`.

Gate result: pass. No constitution violations require exception.

## Architecture

- `src/api/platform/models.py`: add `US_STOCK`, workflow definition/skill
  metadata fields, workflow step/composition fields, dataset quality report
  structures, and workflow output typing where useful.
- `src/api/platform/memory.py`: keep seeded VN and US stock fallback records,
  fundamental records or source documents, and remove gold from active supported
  records. Phase 02 does not introduce an admin ingestion store.
- `src/api/platform/dataflows/`: add the retrieval layer shared by workflows now
  and future chatflow retrieval. It owns provider selection, latest data fetch,
  normalization, fallback policy, provider status, and canonical retrieval
  results.
- `src/api/platform/dataflows/providers/`: add provider adapters: `vnstock` for
  VN stocks, Alpha Vantage for US prices/news when configured, SEC EDGAR company
  facts for US fundamentals, and deterministic fallback sources.
- `src/api/platform/workflows/definitions/`: store YAML workflow definitions for
  user-facing atomic workflows, internal steps, and composite workflows.
- `src/api/platform/workflows/skills/`: store Markdown agent skills that describe
  governed analysis behavior for each analysis step.
- `src/api/platform/workflows/catalog.py`: load and validate workflow definitions,
  expose catalog metadata, and verify referenced Markdown skills exist.
- `src/api/platform/workflows/validation.py`: validate market/symbol/workflow
  compatibility and reject gold/BTC/unsupported assets.
- `src/api/platform/workflows/collector.py`: translate workflow-required
  datasets into a dataflow retrieval request, then pass returned canonical
  records/documents and collection status into quality and execution. It must not
  call provider adapters directly.
- `src/api/platform/workflows/quality.py`: produce dataset statuses, warnings,
  blocking issues, allowed/blocked claim categories, freshness summary, and
  evidence refs.
- `src/api/platform/workflows/executor.py`: execute atomic and composite workflow
  steps, propagate partial/unavailable stage status, and assemble outputs.
- `src/api/platform/workflows/service.py`: orchestrate validation, execution, run
  persistence, serialization, and API-facing errors.
- `src/api/platform/artifacts.py` and `evidence.py`: reuse chart/evidence helpers
  and extend only where new workflow output needs require it.
- `src/ui/src/features/workflows/WorkflowPage.tsx`: show workflow purpose,
  workflow type, markets, required inputs, and run action.
- `src/ui/src/features/results/ResultView.tsx`: show data-quality summary,
  per-stage status, partial/unavailable sections, citations, freshness, and chart
  artifacts.
- `src/ui/src/api/client.ts`: align TypeScript types with expanded workflow
  catalog and run output contracts.

## Workflow Execution Design

Atomic user-facing workflows:

- `fundamental-analysis`
- `technical-analysis`
- `news-digest`
- `risk-review`

Internal steps:

- `data-collector`
- `data-quality-check`

Composite workflow:

```text
stock-brief
  -> data-collector
  -> data-quality-check
  -> fundamental-analysis
  -> technical-analysis
  -> news-digest
  -> risk-review
```

Execution rules:

- Every workflow run starts with validation.
- Workflow YAML is the executable contract for inputs, markets, stages, output
  sections, citations, chart requirements, and safety gates.
- Markdown agent skills are governed analysis instructions and cannot bypass
  runtime validation, data-quality gates, citation/freshness enforcement, or
  advice-only safety rules.
- Every claim-generating workflow runs `data-collector` and `data-quality-check`
  first, even if the UI selected an atomic workflow.
- `data-quality-check` may return `pass`, `warn`, `partial`, or `fail`.
- `warn` allows affected sections to run with visible caveats.
- `partial` runs unaffected sections and marks blocked sections unavailable.
- `fail` blocks claim-generating sections and stores a failed or partial run.
- Composite workflows preserve completed sections even when later stages are
  unavailable.

## Dataflows Retrieval Design

`src/api/platform/dataflows/` is a retrieval module, not an admin ingestion or
backfill platform. It serves Phase 02 workflows and is intentionally reusable by
the Phase 03 chatflow.

Module layout:

```text
src/api/platform/dataflows/
  __init__.py
  models.py
  service.py
  registry.py
  fallback.py
  normalizers.py
  providers/
    __init__.py
    base.py
    vnstock.py
    alpha_vantage.py
    sec_edgar.py
```

Responsibilities:

- `models.py`: retrieval requests, retrieval results, provider results,
  provider status, and dataset ids.
- `service.py`: one `DataflowService.retrieve(...)` entry point for workflows
  and future chatflow.
- `registry.py`: provider selection by market and dataset group.
- `fallback.py`: deterministic offline fallback policy and fallback labeling.
- `normalizers.py`: provider payload to canonical records/source documents.
- `providers/`: provider adapters only; no workflow or UI behavior.

Dataset groups:

- `market_price`: latest quote/history/volume for charts and technical analysis.
- `fundamental`: EPS, BVPS, revenue, profit, ratios, and company facts.
- `news`: recent market/company source documents.
- Future groups may include `macro`, `peer`, `filings`, and `events`.

Execution boundary:

```text
WorkflowService
  -> workflow validation
  -> workflows.collector builds RetrievalRequest
  -> DataflowService.retrieve(...)
  -> data-quality-check
  -> analysis sections
  -> result output with collection status and citations
```

Rules:

- Workflows and chatflow do not know provider internals.
- Provider raw responses, API keys, credentials, hidden prompts, and unsafe
  diagnostics never reach user-facing responses.
- Provider failure returns `partial`, `failed`, or `fallback`; it never fabricates
  successful evidence.
- Fallback records are labeled as fallback and remain distinguishable from live
  provider data.

## Phase 0 Research Output

Resolved in `research.md`:

- Use composable fixed workflows before flexible chatflow.
- Use hybrid YAML workflow definitions and Markdown agent skills instead of
  one-off fixed-code workflows or unconstrained skill-only execution.
- Use latest real provider data for VN and US stocks, with deterministic
  seeded/offline fallback for tests and degraded provider paths.
- Keep data collection and quality checks internal but visible through status.
- Incorporate useful TradingAgents and equity-research-vn workflow ideas while
  rejecting autonomous trading/order execution and broad ingestion.

## Phase 1 Design Output

Generated/updated artifacts:

- `data-model.md`
- `contracts/api-contract.md`
- `quickstart.md`

## Post-Design Constitution Check

- Code ownership remains bounded by existing API/platform/UI layers.
- Test targets are explicit.
- Safety and human control are represented in validation, quality gates, and
  output contracts.
- UX surfaces reference the system UI/UX guidelines.
- Performance expectations are documented for offline execution and live
  provider collection.
- No unresolved clarifications remain.
