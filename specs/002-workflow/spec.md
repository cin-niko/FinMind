---
id: SPEC-FEAT-002
feature: workflow
status: draft
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

# Feature Specification: Workflow

## Summary

Define phase 02 fixed, system-defined financial trading support workflows for the
current market scope: VN stocks and US stocks only. The workflow suite uses
internal data collection and data-quality gate steps, fetching the latest
available provider data before falling back to deterministic demo data in local
or offline test mode. It then exposes repeatable analysis paths such as
fundamental analysis, technical analysis, news digest, risk review, and combined
stock briefs. Workflows provide bounded analysis, validated inputs, evidence
objects, citations, freshness metadata, chart artifacts, execution status, and
result reinspection from the UI.

This draft feature will own workflow execution and result inspection. It does not own the
overall app shell (`../001-mvp-ui/`) or flexible agentic Q&A chatflow
(`../003-agentic-chatflow/`).

## User Scenarios & Testing

### User Story 1 - Run A Supported Stock Workflow From UI (Priority: P1)

An authenticated internal user selects a fixed workflow from the UI, chooses a
supported VN or US stock input, runs bounded analysis, and reviews cited results.

**Independent Test**: Log in, open `Workflows`, run one supported VN stock or US
stock workflow, and verify output sections, citations, freshness, chart artifacts,
and execution status.

Acceptance scenarios:

1. Given a configured VN or US stock provider can return current records, when
   the user submits valid workflow inputs, then the workflow completes with
   structured output using latest provider data and visible collection
   timestamps.
2. Given a workflow output includes a material claim, when the user inspects the
   result, then the claim has a citation or is marked unsupported/unavailable.
3. Given the workflow requires a chart, when it completes, then the result includes
   a chart artifact linked to the same data and evidence as the text output.

### User Story 2 - Choose A Workflow Type (Priority: P1)

An authenticated internal user can choose the appropriate trading-support workflow
for their research need, such as fundamental analysis, technical analysis, news
digest, risk review, or a combined stock brief.

**Independent Test**: Open the workflow catalog and verify that each supported
workflow type describes its purpose, required inputs, expected output sections,
evidence/citation expectations, and whether chart artifacts are expected.

Acceptance scenarios:

1. Given the user opens the workflow catalog, when supported workflows are listed,
   then each workflow has a clear title, purpose, supported market scope, required
   inputs, and expected result sections.
2. Given the user selects fundamental analysis, when the workflow runs, then the
   result emphasizes business quality, financial health, valuation signals, and
   relevant cited source material.
3. Given the user selects technical analysis, when the workflow runs, then the
   result emphasizes price trend, momentum, support/resistance, indicators, chart
   artifacts, and cited market records.
4. Given the user selects news digest, when trusted source material is available,
   then the result summarizes relevant recent items with citations, timestamps,
   sentiment/impact framing, and source freshness; when source material is
   unavailable, the limitation is clearly marked.
5. Given the user selects risk review or combined stock brief, when the workflow
   runs, then the result combines relevant evidence sections without presenting an
   autonomous trading decision.

### User Story 3 - Compose A Stock Brief From Reusable Steps (Priority: P1)

An authenticated internal user can run a combined stock brief that orchestrates
reusable workflow steps instead of duplicating each analysis path.

**Independent Test**: Run `stock-brief` and verify it executes collection,
quality checks, fundamental analysis, technical analysis, news digest, and risk
review as visible stages, with partial/unavailable stages clearly marked.

Acceptance scenarios:

1. Given the user runs `stock-brief`, when the workflow starts, then it first
   collects required data and runs data-quality checks before claim-generating
   analysis steps.
2. Given `data-quality-check` returns warnings, when downstream analysis runs,
   then affected claims include visible caveats.
3. Given `data-quality-check` blocks a claim category, when downstream analysis
   reaches that category, then the affected section is omitted or marked
   unavailable instead of fabricated.
4. Given one downstream step fails or is unavailable, when the composite workflow
   completes, then successful sections remain inspectable and the failed section
   shows a clear status.

### User Story 4 - Reject Unsupported Inputs (Priority: P1)

An authenticated internal user cannot accidentally run unsupported markets,
unsupported symbols, missing data, or unsafe workflow states.

**Independent Test**: Attempt to run workflows with gold, BTC, other assets,
unsupported symbols, missing inputs, and stale/missing data conditions.

Acceptance scenarios:

1. Given an unsupported market or asset is selected or submitted, when workflow
   validation runs, then execution is blocked or clearly marked unavailable.
2. Given required input is missing or invalid, when the user submits the workflow,
   then validation appears near the field and no fabricated result is created.
3. Given cited data is stale, missing, or failed, when a result is shown, then the
   condition is visible to the user.

### User Story 5 - Reopen Workflow Results (Priority: P2)

An authenticated internal user can reopen completed workflow runs from history and
inspect output, citations, freshness, artifacts, and execution status.

**Independent Test**: Complete a workflow run, refresh with the same valid session,
select the run from `History` -> `Workflow Runs`, and verify the result is restored.

Acceptance scenarios:

1. Given a workflow run completed, when the page reloads with a valid session, then
   the run remains visible under `Workflow Runs`.
2. Given a completed run is selected, when the result opens, then citations,
   freshness, artifacts, and execution status remain inspectable.
3. Given a run ID does not exist, when requested, then the system returns a
   not-found state rather than fabricating a result.

## Functional Requirements

- **FR-001**: System MUST provide a workflow catalog of fixed system-defined
  trading-support workflows runnable from the UI.
- **FR-002**: Workflow catalog entries MUST declare supported market scope,
  required inputs, stages, role labels, output sections, citation expectations,
  and chart requirements.
- **FR-003**: Current workflow market scope MUST include VN stocks and US stocks
  only.
- **FR-004**: Workflow suite MUST include, at minimum, fundamental analysis,
  technical analysis, and news digest workflows for supported stocks.
- **FR-005**: Workflow suite SHOULD include risk review and combined stock brief
  workflows when their required evidence inputs are available.
- **FR-006**: Workflow suite MUST support reusable workflow steps so a composite
  workflow can run another workflow or internal step as one stage.
- **FR-007**: `data-collector` MUST be an internal step that gathers the latest
  available datasets required by the selected workflow, including market records,
  fundamentals, source documents or news, and peer data when available.
- **FR-008**: `data-quality-check` MUST be an internal gate step that evaluates
  collected records before claim-generating analysis steps run.
- **FR-009**: `data-quality-check` MUST output quality status, dataset statuses,
  blocking issues, warnings, allowed claim categories, blocked claim categories,
  freshness summary, and evidence references.
- **FR-010**: `stock-brief` MUST be a composite workflow that runs
  `data-collector`, `data-quality-check`, `fundamental-analysis`,
  `technical-analysis`, `news-digest`, and `risk-review` as ordered stages.
- **FR-011**: Gold, BTC, and other assets MUST NOT be enabled runnable workflow
  choices unless a later spec changes scope.
- **FR-012**: Workflow forms MUST render every required input and submit those
  values rather than defaulting to the first available record.
- **FR-013**: Workflow input validation MUST reject unsupported markets,
  unsupported symbols, missing inputs, and invalid values before successful
  execution.
- **FR-014**: System MUST maintain deterministic seeded/offline canonical records
  for VN and US stock examples with source identity, market time, collection
  time, freshness, and unique record keys for tests and provider-failure
  fallback.
- **FR-015**: News digest workflows MUST use trusted source material with source
  identity and publication or collection timestamps when available; if trusted
  source material is unavailable, the workflow MUST clearly mark the news section
  unavailable rather than fabricating digest content.
- **FR-016**: Fundamental analysis workflows MUST expose business quality,
  financial health, valuation, peer/industry context where available, and key
  risk sections when supporting evidence is available.
- **FR-017**: Technical analysis workflows MUST expose trend, momentum,
  support/resistance or equivalent price-level framing, chart artifacts, and
  cited market records when supporting evidence is available.
- **FR-018**: Risk review workflows MUST highlight material downside, data quality,
  market, bull/bear framing, and evidence limitations without issuing autonomous
  decisions.
- **FR-019**: System MUST construct evidence objects linking workflow claims to
  source records, citations, timestamps, and generated artifacts.
- **FR-020**: Workflow outputs MUST include data-quality checks relevant to the
  market and evidence type, including stale records, inconsistent periods,
  split-adjusted price comparisons, changed share counts, and unavailable source
  fields when applicable.
- **FR-021**: Every user-facing material workflow claim MUST expose citations and
  freshness metadata or be marked unsupported/unavailable.
- **FR-022**: System MUST generate chart artifacts for workflow outputs requiring
  visual price, indicator, or trend analysis.
- **FR-023**: System MUST record execution runs for workflow submissions,
  generated artifacts, failures, partial results, and user-visible output status.
- **FR-024**: System MUST expose result views where users can inspect completed
  workflow outputs after the original run.
- **FR-025**: User-facing workflow outputs MUST NOT expose raw agent reasoning.
- **FR-026**: Workflow outputs MUST be framed as research support, not trading
  decisions, executable orders, or autonomous financial actions.
- **FR-027**: VN stock collection MUST use a provider adapter backed by `vnstock`
  for Phase 02 latest price and fundamental data where the library supports the
  requested symbol and dataset.
- **FR-028**: US stock collection MUST use provider adapters backed by a
  documented US market data source for prices/news and SEC EDGAR company facts
  for public-company fundamentals where available.
- **FR-029**: The system MUST provide a retrieval-first `dataflows` module that
  serves workflows now and future chatflow retrieval without implementing admin
  ingestion, scheduled backfill, or broad realtime data operations.
- **FR-030**: `dataflows` MUST expose a single retrieval boundary that accepts
  market, symbol, and required dataset groups, then returns canonical market
  records, source documents, provider statuses, collection timestamps, warnings,
  and failure reasons.
- **FR-031**: Workflow code MUST request data through `dataflows` and MUST NOT
  call concrete provider adapters directly.
- **FR-032**: Provider adapters MUST record `source_id`, provider timestamp or
  market timestamp, `collected_at`, dataset coverage, and any provider failure
  reason used by `data-quality-check`.
- **FR-033**: Provider failures, missing API keys, rate limits, license
  restrictions, unavailable symbols, or stale latest data MUST produce a
  warning/partial/unavailable result instead of fabricated claims.

## Key Entities

- Market Instrument
- Canonical Market Data Record
- Workflow Specification
- Workflow Step
- Workflow Composition
- Execution Run
- Dataset Quality Report
- Evidence Object
- Citation
- Chart Artifact
- Source Document

See `../system/state-model.md` for canonical entity definitions.

## Edge Cases

- Supported data exists but is stale: result displays freshness warnings.
- Data collection returns partial coverage: quality check marks unavailable
  datasets and downstream steps run only unaffected sections.
- A workflow partially completes: completed sections, failed sections, and
  unavailable artifacts are distinguishable.
- Unsupported market or instrument request: execution is blocked or clearly marked
  before user reliance.
- Citation unavailable for a generated claim: claim is omitted, qualified, or
  marked unsupported.
- News source material unavailable for a requested digest: news digest section is
  marked unavailable with the reason.
- Technical chart data unavailable: chart artifact is marked unavailable and the
  text result avoids unsupported technical claims.
- Fundamental or valuation inputs are inconsistent across periods: the workflow
  marks the data-quality issue before presenting valuation or peer-comparison
  conclusions.
- Run ID does not exist: return not-found behavior.

## Assumptions

- `../001-mvp-ui/` provides authenticated shell and navigation.
- Latest per-run provider collection is enough for Phase 02; historical
  warehouse ingestion, scheduling, and broad data operations require later
  bounded specs.
- Deterministic seeded/offline VN and US stock records remain necessary to
  validate workflow contracts without network or provider credentials.
- News digest can start from provider news where configured and trusted source
  documents or curated/open-source source material available to the project.
- Workflows provide advice support and evidence framing, not buy/sell decisions.
- `data-collector` is bounded to workflow-run needs and does not implement a
  broad native ingestion platform.

## Success Criteria

- **SC-001**: A user can complete a supported VN stock workflow and inspect cited
  output, freshness, chart artifact, and execution status in under 5 minutes.
- **SC-002**: A user can complete a supported US stock workflow and inspect cited
  output, freshness, chart artifact, and execution status in under 5 minutes.
- **SC-003**: A user can choose fundamental analysis, technical analysis, and news
  digest workflows from the UI and understand each workflow's purpose before
  running it.
- **SC-004**: A user can run `stock-brief` and see collection, data-quality,
  fundamental, technical, news, and risk stages with clear completion, partial,
  failed, or unavailable status.
- **SC-005**: 100% of user-facing material workflow claims include at least one
  citation or are explicitly marked unsupported/unavailable.
- **SC-006**: At least 95% of supported workflow result views show freshness
  metadata for every referenced dataset.
- **SC-007**: Users can identify stale, missing, failed, or out-of-scope data
  conditions without reading logs.
- **SC-008**: Completed workflow runs remain visible under `History` ->
  `Workflow Runs` after refresh with a valid session.
- **SC-009**: 100% of workflow outputs avoid autonomous buy/sell/order language
  and keep final trading judgment with the user.

## Out Of Scope

- App shell/login ownership.
- Production flexible Q&A agentic chatflow.
- Broad native realtime market data platform beyond per-run provider fetch.
- Broad native realtime news ingestion beyond provider/source documents required
  by one workflow run.
- Gold, BTC, crypto, commodities, options, futures, broker connectivity, trade
  execution, and autonomous financial actions.
