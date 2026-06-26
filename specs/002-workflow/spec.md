---
id: SPEC-FEAT-002
feature: workflow
status: draft
owner: solo
created: 2026-06-26
implements: []
validated_by: []
adr_refs: []
---

# Feature Specification: Workflow

## Summary

Define phase 02 fixed, system-defined financial analysis workflows for the current market
scope: VN stocks and US stocks only. Workflows provide bounded analysis, validated
inputs, evidence objects, citations, freshness metadata, chart artifacts, execution
status, and result reinspection.

This draft feature will own workflow execution and result inspection. It does not own the
overall app shell (`../001-mvp-ui/`) or flexible agentic Q&A chatflow
(`../003-agentic-chatflow/`).

## User Scenarios & Testing

### User Story 1 - Run A Supported Stock Workflow (Priority: P1)

An authenticated internal user selects a fixed workflow, chooses a supported VN or
US stock input, runs bounded analysis, and reviews cited results.

**Independent Test**: Log in, open `Workflows`, run one supported VN stock or US
stock workflow, and verify output sections, citations, freshness, chart artifacts,
and execution status.

Acceptance scenarios:

1. Given seeded/demo VN or US stock records are available, when the user submits
   valid workflow inputs, then the workflow completes with structured output.
2. Given a workflow output includes a material claim, when the user inspects the
   result, then the claim has a citation or is marked unsupported/unavailable.
3. Given the workflow requires a chart, when it completes, then the result includes
   a chart artifact linked to the same data and evidence as the text output.

### User Story 2 - Reject Unsupported Inputs (Priority: P1)

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

### User Story 3 - Reopen Workflow Results (Priority: P2)

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
  analysis workflows.
- **FR-002**: Workflow catalog entries MUST declare supported market scope,
  required inputs, stages, role labels, output sections, citation expectations,
  and chart requirements.
- **FR-003**: Current workflow market scope MUST include VN stocks and US stocks
  only.
- **FR-004**: Gold, BTC, and other assets MUST NOT be enabled runnable workflow
  choices unless a later spec changes scope.
- **FR-005**: Workflow forms MUST render every required input and submit those
  values rather than defaulting to the first available record.
- **FR-006**: Workflow input validation MUST reject unsupported markets,
  unsupported symbols, missing inputs, and invalid values before successful
  execution.
- **FR-007**: System MUST maintain seeded/demo canonical records for VN and US
  stock examples with source identity, market time, collection time, freshness,
  and unique record keys.
- **FR-008**: System MUST construct evidence objects linking workflow claims to
  source records, citations, timestamps, and generated artifacts.
- **FR-009**: Every user-facing material workflow claim MUST expose citations and
  freshness metadata or be marked unsupported/unavailable.
- **FR-010**: System MUST generate chart artifacts for workflow outputs requiring
  visual price, indicator, or trend analysis.
- **FR-011**: System MUST record execution runs for workflow submissions,
  generated artifacts, failures, partial results, and user-visible output status.
- **FR-012**: System MUST expose result views where users can inspect completed
  workflow outputs after the original run.
- **FR-013**: User-facing workflow outputs MUST NOT expose raw agent reasoning.
- **FR-014**: Workflow outputs MUST be framed as research support, not trading
  decisions, executable orders, or autonomous financial actions.

## Key Entities

- Market Instrument
- Canonical Market Data Record
- Workflow Specification
- Execution Run
- Evidence Object
- Citation
- Chart Artifact

See `../system/state-model.md` for canonical entity definitions.

## Edge Cases

- Supported data exists but is stale: result displays freshness warnings.
- A workflow partially completes: completed sections, failed sections, and
  unavailable artifacts are distinguishable.
- Unsupported market or instrument request: execution is blocked or clearly marked
  before user reliance.
- Citation unavailable for a generated claim: claim is omitted, qualified, or
  marked unsupported.
- Run ID does not exist: return not-found behavior.

## Assumptions

- `../001-mvp-ui/` provides authenticated shell and navigation.
- Seeded/demo VN and US stock records are enough to validate workflow contracts.
- Production realtime market data and native news require later bounded specs.

## Success Criteria

- **SC-001**: A user can complete a supported VN stock workflow and inspect cited
  output, freshness, chart artifact, and execution status in under 5 minutes.
- **SC-002**: A user can complete a supported US stock workflow and inspect cited
  output, freshness, chart artifact, and execution status in under 5 minutes.
- **SC-003**: 100% of user-facing material workflow claims include at least one
  citation or are explicitly marked unsupported/unavailable.
- **SC-004**: At least 95% of supported workflow result views show freshness
  metadata for every referenced dataset.
- **SC-005**: Users can identify stale, missing, failed, or out-of-scope data
  conditions without reading logs.
- **SC-006**: Completed workflow runs remain visible under `History` ->
  `Workflow Runs` after refresh with a valid session.

## Out Of Scope

- App shell/login ownership.
- Production flexible Q&A agentic chatflow.
- Native realtime market data platform.
- Native news ingestion.
- Gold, BTC, crypto, commodities, options, futures, broker connectivity, trade
  execution, and autonomous financial actions.
