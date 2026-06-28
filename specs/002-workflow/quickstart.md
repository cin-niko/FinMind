---
id: SPEC-FEAT-002-QUICKSTART
feature: workflow
status: active
owner: solo
created: 2026-06-26
implements: []
validated_by: []
adr_refs:
  - docs/adr/ADR-001-hybrid-workflow-definitions-and-agent-skills.md
---

# Quickstart: Workflow Validation

## Prerequisites

- Admin credentials configured:
  - `FINMIND_ADMIN_USERNAME`
  - `FINMIND_ADMIN_PASSWORD`
  - `FINMIND_SESSION_SECRET`
- Optional live provider credentials/configuration:
  - `LITELLM_CHAT_MODEL` selects the model used by the Deep Agents workflow
    runtime. Model strings should use the LiteLLM-compatible format for the
    target provider.
  - `LITELLM_API_KEY` provides the model credential through the shared LiteLLM
    adapter. Do not add provider-specific model key names to FinMind workflow
    contracts.
  - `LITELLM_API_BASE` is optional and should be set only for OpenAI-compatible
    gateways or provider deployments that require a custom base URL.
  - `FINMIND_VNSTOCK_API_KEY` optionally registers the backend runtime with
    vnstock before VN provider fetches. Leave it empty for guest access.
  - `FINMIND_US_ALPHA_VANTAGE_API_KEY` for US price/news collection.
  - SEC EDGAR requests must use a configured User-Agent/contact setting before
    live US fundamentals collection is enabled.
  - VN collection uses the `vnstock` adapter.
- Dependencies installed.

## Package Migration Notes

Phase 02 targets three package boundaries:

- `src/finmind_agents`: shared agent runtime, workflow definitions, Agent Skills,
  dataflows, validators, and finance-domain services.
- `src/finmind_api`: FastAPI app, dependencies, routes, schemas, auth wiring,
  and API error mapping.
- `src/finmind_ui`: Vite frontend package for workflow forms, result views, and
  app shell integration.

The active implementation uses these package boundaries directly. New workflow
runtime behavior should be implemented in `finmind_agents` first, then exposed
through `finmind_api`.

## Commands

Task execution starts from [`tasks.md`](tasks.md). Phase 02 should be validated
incrementally after each independently testable user story, then with the full
commands below before completion.

Backend/API verification:

```bash
UV_CACHE_DIR=/private/tmp/finmind-uv-cache uv run --group dev python -m pytest tests/test_app.py tests/test_platform_services.py
```

Frontend verification:

```bash
cd src/finmind_ui
npm run build
```

## Scenario 1: Catalog

1. Log in through the MVP UI shell.
2. Open `Workflows`.
3. Confirm catalog includes:
   - `fundamental-analysis`
   - `technical-analysis`
   - `news-digest`
   - `risk-review`
   - `stock-brief`
4. Confirm each catalog card shows purpose, markets, required inputs, stages, and
   chart/citation expectations.

## Scenario 2: VN Stock Brief

1. Run `stock-brief` with `market=VN_STOCK` and a supported symbol such as `VCB`.
2. Confirm the runtime loads the referenced Agent Skill and
   `DATA_REQUIREMENTS.yaml`, derives the collection plan under workflow policy,
   and then requests data through `dataflows`.
3. Confirm `dataflows` attempts latest VN provider collection through the
   `vnstock` adapter before deterministic fallback is used.
4. Confirm stages include:
   - `collect_data`
   - `data-audit`
   - `fundamental-analysis`
   - `technical-analysis`
   - `news-digest`
   - `risk-review`
5. Confirm result includes steps, grounding status, collection status, sections,
   citations, chart artifact, and source refs.

## Scenario 2A: VN Financial Data Auditor Agent Skill

1. Run the VN financial data auditor skill through the workflow runtime with
   `market=VN_STOCK` and `symbol=DXG` (the `vn-financial-data-collector` workflow
   runs `collect_data` then the `vn-financial-data-auditor` skill).
2. Confirm the runtime uses a configured LLM model and records safe agent
   execution metadata such as skill id, step status, warnings, and blocked claim
   categories.
3. Confirm detailed data needs come from the skill's `DATA_REQUIREMENTS.yaml`,
   not duplicated workflow YAML fields.
4. Confirm the agent derives required/optional collection calls from those data
   requirements, and FinMind validates the plan before executing dataflows.
5. Confirm the skill audits already-collected records through `dataflows`
   rather than importing or calling `vnstock` directly from the skill
   instructions; collection is owned by the `collect_data` step.
6. Confirm collected price, fundamentals, company profile, and source-document
   coverage is shown with citations (source id, dataset id, timestamp) where
   available.
7. Confirm missing statements, ratios, peer data, or news documents cause
   partial/unavailable sections rather than fabricated analysis.
8. Confirm no raw model reasoning, hidden prompts, provider secrets, or raw
   provider payloads appear in the exported report or API response.

## Scenario 3: US Stock Workflow

1. Run `technical-analysis` or `stock-brief` with `market=US_STOCK` and a
   supported symbol such as `AAPL`.
2. Confirm `collect_data` requests data through `dataflows`, and `dataflows`
   attempts latest US provider collection through Alpha Vantage for prices/news
   when configured and SEC EDGAR company facts for fundamentals where available.
3. Confirm output uses US stock records, not VN stock defaults.
4. Confirm citations reference US datasets and provider/fallback source identity.

## Scenario 4: Provider Failure Or Fallback

1. Run a workflow with live provider credentials disabled or with a forced
   provider failure in tests.
2. Confirm `collection.status` is `partial`, `failed`, or `fallback`.
3. Confirm `collection.provider_results` identifies the failed/skipped/fallback
   provider without raw provider payloads or secrets.
4. Confirm affected skill steps are `unavailable` and `grounding.grounding_status`
   is `blocked`.
5. Confirm blocked claim categories are omitted or marked unavailable.
6. Confirm fallback data is labeled as fallback and not presented as live data.

## Scenario 5: Grounding Gate

1. Run a workflow where one required dataset is missing or stale.
2. Confirm the affected skill step is `unavailable` and
   `grounding.grounding_status` is `blocked`.
3. Confirm blocked claim categories are omitted or marked unavailable.
4. Confirm unaffected sections remain inspectable for partial results.

## Scenario 6: Unsupported Asset

1. Attempt to run gold, BTC, crypto, or another unsupported asset.
2. Confirm execution is blocked or clearly marked unavailable.
3. Confirm no successful fabricated run is created.

## Scenario 7: Run Reinspection

1. Complete a workflow run.
2. Refresh with a valid session.
3. Open `History` -> `Workflow Runs`.
4. Reopen the completed run and confirm output, quality, collection status,
   citations, artifacts, and step/grounding status remain visible.
