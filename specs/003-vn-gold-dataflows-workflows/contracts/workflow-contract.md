---
id: SPEC-FEAT-003-CONTRACTS
feature: vn-gold-dataflows-workflows
status: draft
owner: solo
created: 2026-07-11
implements: []
validated_by: []
adr_refs: []
---

# Workflow Contract: VN And Gold Dataflows And Workflows

This feature extends the shared API and evidence contracts in
`../../system/contracts.md`, `../../system/state-model.md`, and
`../../system/data-record-flow.md`.

## Catalog Contract

Each enabled catalog entry must include:

- stable `workflow_id`, title, and purpose;
- `market_scope` containing only `VN_STOCK` or `GOLD`;
- required input schema and supported instrument selection;
- required dataset groups, ordered stage labels, expected output sections, and
  chart requirements;
- citation/freshness expectations and unsupported claim categories.

Phase 03 must not serialize unsupported workflows as enabled catalog choices.

## Gold Dataflow Contract

A supported gold collection result must return:

- normalized records or source documents with `source_id`, `dataset_id`, market
  time, `collected_at`, and freshness status;
- bounded record context plus citation allowlist identifiers;
- provider/collection status, unavailable datasets, warnings, and failure
  reasons; and
- no raw provider payloads, credentials, or unsupported claim categories in
  user-facing output.

Any stale, unavailable, mismatched, or undeclared gold dataset must mark its
affected claims unavailable or reject the workflow before answer generation.

## Workflow Run Contract

`POST /api/workflows/{workflow_id}/runs` retains the Phase 02 SSE event contract
for valid Phase 03 inputs. Safe progress events, citations, artifacts, terminal
status, and persisted final results must remain reconcilable with run inspection.

The request must reject or visibly mark:

- missing or malformed inputs;
- a market outside `VN_STOCK` or `GOLD`;
- a gold instrument or benchmark outside the configured catalog;
- undeclared dataset requests; and
- unsafe, stale, or unsupported claim categories.

## Run Inspection Contract

`GET /api/runs`, `GET /api/runs/{run_id}`, and
`GET /api/runs/{run_id}/citations` must support completed and partial Phase 03
workflow runs. Responses preserve market, instrument, stage status, output,
artifacts, citation provenance, and limitations without disclosing raw reasoning.

## Safety Contract

- Material claims cite an allowed record or are marked unavailable/unsupported.
- Stock-only financial sections never appear as gold evidence.
- Gold-specific context is not silently mixed into VN stock workflows.
- Outputs provide research support only and refuse broker, order, and trade
  execution actions.
