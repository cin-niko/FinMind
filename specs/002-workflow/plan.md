---
id: SPEC-FEAT-002-PLAN
feature: workflow
status: active
owner: solo
created: 2026-06-26
implements: []
validated_by:
  - tests/test_app.py
  - tests/test_platform_services.py
  - src/finmind_ui/package.json
adr_refs:
  - docs/adr/ADR-001-hybrid-workflow-definitions-and-agent-skills.md
---

# Implementation Plan: Workflow

## Summary

Implement Phase 02 fixed, UI-runnable financial trading support workflows for VN
stocks and US stocks on top of a shared agent runtime that can later power
Phase 03 chatflow. The target repo split is `src/finmind_agents` for the agentic
and finance orchestration layer, `src/finmind_api` for the FastAPI delivery
layer, and `src/finmind_ui` for the frontend. The workflow contract remains
hybrid: YAML definitions declare inputs, skill refs, stages, output schemas,
runtime policy, and safety gates; Agent Skills own governed analyst procedure
and skill-level data requirements. The MVP runtime should rely on LangChain
Deep Agents via `deepagents.create_deep_agent`, use `langchain-litellm` as the
default multi-provider model adapter, and defer LangGraph until workflow or
chatflow complexity actually requires graph state, checkpointing, or multi-agent
branching. The first active workflow focus is the VN financial data collector
path, with broader workflow catalog contracts retained for Phase 02.

## Technical Context

- Language/version: Python 3.12 backend, TypeScript React/Vite frontend.
- Backend dependencies: FastAPI, Pydantic, LangChain, Deep Agents
  (`deepagents`), `langchain-litellm` as the default multi-provider model
  adapter, `httpx`, retrieval-first dataflow adapters, in-memory fallback
  repositories, pytest. LangGraph is intentionally deferred for the current MVP.
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
  and `npm run build` in `src/finmind_ui`.
- Target platform: internal browser app backed by FastAPI JSON APIs.
- Performance goals: supported offline workflow runs complete under 3 seconds in
  automated tests. Live provider collection should target a 15-second per-run
  timeout budget, with per-provider timeout/failure surfaced to
  `data-quality-check`. Agent skill execution should have a bounded iteration
  and timeout budget per workflow stage.
- Constraints: VN stocks and US stocks only; gold/BTC/other assets blocked or
  roadmap-marked; no broker/order/trade execution; no raw reasoning exposure;
  workflow skill execution requires an explicit LLM configuration and fails
  closed when unavailable.
- Scale/scope: latest provider fetch for one requested symbol per run, small
  canonical in-memory cache/fallback datasets, one authenticated internal admin,
  single-process execution.

## Constitution Check

- Code quality: keep the `src/finmind_agents` split explicit: runtime,
  workflows, skills, and dataflows remain separate; `src/finmind_api` stays a
  delivery layer and does not absorb finance workflow logic.
- Testing standards: add/adjust pytest coverage for catalog, VN/US runs,
  unsupported assets, composite `stock-brief`, data-quality gating, citations,
  chart artifacts, and run reinspection; run frontend build for UI contract
  compatibility.
- Safety guardrails: unsupported assets are blocked, data-quality warnings gate
  claims, material claims require citations or unavailable marking, raw reasoning
  is excluded, LLM/tool failures fail closed or produce partial/unavailable
  output, and outputs remain advice support only.
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

- `src/finmind_agents/runtime/`: own `FinMindAgentRuntime`, model bootstrap,
  `deepagents.create_deep_agent` orchestration, `langchain-litellm` adapter
  wiring, tool registry, runtime policies, and the seam where LangGraph may be
  added later. For the MVP, Deep Agents plus normal Python guardrail code are
  sufficient; do not introduce LangGraph graph state until workflow/chatflow
  needs it.
- `src/finmind_agents/workflows/`: own workflow definitions, catalog loading,
  validation, collection orchestration, quality gates, executor logic, and run
  result assembly.
- `src/finmind_agents/skills/`: own skill loading and skill assets in
  `<skill-name>/SKILL.md` and `DATA_REQUIREMENTS.yaml`.
- `src/finmind_agents/dataflows/`: own provider selection, latest data fetch,
  normalization, fallback policy, provider status, and canonical retrieval
  results. It remains shared by workflows now and chatflow later.
- `src/finmind_agents/domain/`: own shared finance domain models and canonical
  workflow/dataflow entities.
- `src/finmind_api/`: own FastAPI app setup, auth, dependencies, routes,
  schemas, and API-facing error mapping. It should call into `finmind_agents`
  and stay thin.
- `src/finmind_ui/`: own workflow forms, result views, app shell integration,
  and API client bindings for workflow contracts.

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
- Workflow YAML is the executable product contract for inputs, markets, skill
  refs, stages, output sections, citations, chart requirements, runtime policy,
  and safety gates. It must not duplicate detailed skill data requirements.
- Markdown agent skills are governed analysis instructions and cannot bypass
  runtime validation, data-quality gates, citation/freshness enforcement, or
  advice-only safety rules.
- Workflow mode is a constrained agent run: fixed skill selection from YAML,
  skill-owned data requirements, strict output schema, low iteration budget,
  dataflows-only tool access, no provider-direct access, and fail-closed
  behavior.
- Future chatflow mode should reuse the same runtime with a flexible research
  policy: dynamic skill loading, dynamic data requirements, broader approved
  tool access, larger iteration budget, clarification/partial-answer behavior,
  and chat-specific answer schemas.
- Sub-agents may be used per data domain, such as VN market data, fundamentals,
  technical data, news/source documents, and risk review. Their outputs remain
  intermediate and must pass FinMind grounding/citation validators before being
  shown.
- Every claim-generating workflow records `data-collector` and
  `data-quality-check` stages before claim-generating synthesis, even if the UI
  selected an atomic workflow. `data-collector` is implemented as agent-planned,
  FinMind-validated retrieval through the dataflows tool boundary.
- The agent runtime reads the skill before retrieval planning. Required data
  declared by the skill must be attempted; optional data may be attempted when
  allowed by policy and timeout budget.
- Agent-planned retrieval is only a request. FinMind validates market, symbol,
  dataset ids, required/optional status, fallback permission, and tool policy
  before executing the retrieval.
- `data-quality-check` may return `pass`, `warn`, `partial`, or `fail`.
- `warn` allows affected sections to run with visible caveats.
- `partial` runs unaffected sections and marks blocked sections unavailable.
- `fail` blocks claim-generating sections and stores a failed or partial run.
- Composite workflows preserve completed sections even when later stages are
  unavailable.

## Dataflows Retrieval Design

`src/finmind_agents/dataflows/` is a retrieval module, not an admin ingestion or
backfill platform. It serves Phase 02 workflows and is intentionally reusable by
the Phase 03 chatflow.

Module layout:

```text
src/finmind_agents/dataflows/
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
finmind_api route
  -> workflow validation
  -> finmind_agents.workflows loads workflow YAML and allowed skill ref
  -> FinMindAgentRuntime loads SKILL.md and DATA_REQUIREMENTS.yaml
  -> Deep Agents runtime derives required/optional retrieval plan inside policy
  -> FinMind validates retrieval plan
  -> retrieve_dataflow tool calls DataflowService.retrieve(...)
  -> FinMind runs data-quality-check on retrieved data
  -> Deep Agents runtime synthesizes governed draft output
  -> grounding/citation/output validators
  -> finmind_api serializes result output
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
- Use one shared `FinMindAgentRuntime` for workflow now and chatflow later, with
  different policy envelopes.
- Treat Agent Skill `DATA_REQUIREMENTS.yaml` as the canonical source for detailed
  data needs; workflow YAML references skills and constrains runtime policy
  instead of duplicating retrieval requirements.
- Use Deep Agents (`deepagents.create_deep_agent`) for the shared workflow
  runtime core and `langchain-litellm` as the default model adapter so multiple
  providers can run behind one LangChain-facing integration point.
- Defer LangGraph until the runtime truly needs graph state, checkpoints,
  multi-agent branching, or pause/resume orchestration.
- Spend implementation effort on dataflows, grounding, citations, validators,
  and synthesis prompts; do not rebuild planning/delegation primitives unless
  the framework proves too hard to control.
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
