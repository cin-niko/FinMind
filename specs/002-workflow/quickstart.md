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
  - docs/adr/ADR-002-direct-async-sse-streaming.md
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
  - VN collection uses the `vnstock` adapter.
- Optional stream concurrency limits:
  - `FINMIND_STREAM_GLOBAL_LIMIT`
  - `FINMIND_STREAM_PER_USER_LIMIT`
  - `FINMIND_SYNC_OFFLOAD_LIMIT`
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

Async/streaming verification should include API tests that use an async HTTP
client or ASGI test client to submit workflow stream requests, consume
SSE events from the same response, and assert no blocking sync work occurs in
request handlers.

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
6. Confirm collected price, fundamentals, and company profile coverage is shown
   with citations (source id, dataset id, timestamp) where
   available.
7. Confirm missing statements, ratios, peer data, or unsupported news/catalyst
   requests cause partial/unavailable sections rather than fabricated analysis.
8. Confirm no raw model reasoning, hidden prompts, provider secrets, or raw
   provider payloads appear in the exported report or API response.

## Scenario 3: Unsupported Market Request

1. Submit a workflow request with an unsupported `market` value.
2. Confirm the request is rejected or clearly marked unsupported before data
   collection or result creation.

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

## Scenario 5A: Data Records And Citation Persistence

1. Run `vn-technical-analysis` or `vn-fundamental-analysis` for a supported
   symbol.
2. Confirm collection returns canonical source records, then runtime builds
   deterministic data records before the LLM call.
3. Confirm the normal LLM bundle includes compact records such as
   `price_summary_record`, `indicator_record`, `pattern_evidence_record`,
   `pattern_setup_record`, `company_profile_record`, or `fundamental_record`,
   and excludes full `price_series_record` data by default.
4. Confirm each record exposes a deterministic rendered `context` used for LLM
   input, while structured fields remain the canonical in-memory representation.
5. Confirm citation ids are created before the LLM call and every model-cited id
   exists in the data bundle allowlist.
6. Confirm `price_series_record` is persisted for charting/reuse, while
   intermediate derived records are not required to be stored durably by
   default.
7. Confirm final run output embeds citation summaries and
   `GET /api/runs/{run_id}/citations` returns the persisted citation records with
   `record_id`, `record_type`, source id, dataset id, timestamp,
   `payload_snapshot`, and `display_content`.
8. Confirm a `fundamental_record` with `is_audited=false` blocks confident
   fundamental claims or marks them unavailable.
9. Confirm no raw provider payload, full price series, hidden prompt, or raw
   reasoning is included in the LLM payload or citation response.

## Scenario 6: Unsupported Asset

1. Attempt to run an unsupported asset.
2. Confirm execution is blocked or clearly marked unavailable.
3. Confirm no successful fabricated run is created.

## Scenario 7: Run Reinspection

1. Complete a workflow run.
2. Refresh with a valid session.
3. Open `History` -> `Workflow Runs`.
4. Reopen the completed run and confirm output, quality, collection status,
   citations, artifacts, and step/grounding status remain visible.

## Scenario 8: Async Workflow Stream

1. Log in through the API or UI shell.
2. Submit `POST /api/workflows/technical-analysis/runs` with
   `market=VN_STOCK` and `symbol=VCB`.
3. Confirm the response is `200 OK` with `Content-Type: text/event-stream`.
4. Confirm the first safe event arrives in under 1 second in offline tests.
5. Confirm the same response stream emits ordered safe events:
   - `response_started`
   - `stage_status`
   - `warning` when applicable
   - `citation` when citations are produced
   - `artifact` when chart artifacts are produced
   - `output_delta`
   - `final_output`
   - `completed` or `failed`
6. Confirm no event contains raw reasoning, hidden prompts, provider secrets, raw
   provider payloads, or unsafe diagnostics.
7. Confirm the final run can be reopened through `GET /api/runs/{run_id}` after
   stream completion without rerunning providers.

## Scenario 8A: Transcript-Style Workflow Response UI

1. Open the authenticated chat/transcript surface that renders workflow-backed
   assistant responses.
2. Submit or reopen a workflow-backed response with visible execution progress.
3. Confirm the user prompt remains a bubble-style message.
4. Confirm the assistant answer renders without a full white message card and
   without repeated `You` or `FinMind` role headers.
5. While the run is still active, confirm the execution-visibility block shows
   the summary label `Working` and is expanded by default.
6. After the run completes, confirm the summary label changes to
   `Completed N steps`, the block collapses by default, and the user can reopen
   it manually.
7. Confirm visible steps use product-facing labels and optional lighter subtext
   such as `DXG` rather than raw workflow or skill ids.
8. Confirm the completed visible step list ends with `Done`.
9. Confirm artifact cards render after the answer content and open the full
   artifact viewer in the right-side panel.
10. Confirm chart artifacts expose only supported view switches, such as `Line`
   and `Candlestick` when both data shapes exist, and do not require a price
   table in the main answer.
11. Confirm ready artifacts expose valid download actions and unavailable
   artifacts show a reason without broken download actions.
12. Click an inline citation chip in the answer and confirm the right-side panel
   switches to the citations list, shows all sources for the answer or run, and
   scrolls to the clicked source.

## Scenario 9: Chatflow Deferred

1. Confirm Phase 02 exposes no runnable `/api/chatflow/...` contract.
2. Confirm production chatflow validation is deferred to
   `../004-agentic-chatflow/`.

## Scenario 10: Multi-User Non-Blocking Execution

1. Start at least 10 authenticated test clients.
2. Submit a mix of direct workflow streaming requests.
3. Hold each client's SSE response stream open until completion or timeout.
4. Confirm each client receives its first safe event promptly and no client is
   delayed by another client's provider/model call.
5. Force one sync-only provider path, such as a VN provider library call, and
   confirm it executes through bounded offload with timeout/failure metadata
   rather than blocking the event loop.
6. Confirm per-user, global, or sync-offload concurrency limits return `429`
   with a safe error when exceeded.
7. Confirm Phase 02 limits are enforced by process-local semaphores; Redis or
   distributed lease behavior is not expected in this phase.

## Scenario 11: Disconnect And Restart Safety

1. Submit a long-running async workflow stream.
2. Close the client connection before completion.
3. Confirm request-scoped execution is cancelled cooperatively where possible.
4. Confirm no raw reasoning or unsafe diagnostics are emitted during disconnect.
5. Simulate server restart while streams are active.
6. Confirm active streams end and only completed/persisted final run results are
   inspectable after restart.
