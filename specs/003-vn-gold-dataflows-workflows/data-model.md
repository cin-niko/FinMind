---
id: SPEC-FEAT-003-DATA
feature: vn-gold-dataflows-workflows
status: draft
owner: solo
created: 2026-07-11
implements: []
validated_by: []
adr_refs: []
---

# Data Model: VN And Gold Dataflows And Workflows

This feature uses canonical entities in `../system/state-model.md` and the
data-record boundary in `../system/data-record-flow.md`. It defines only
Phase 03 usage and extensions.

## MarketInstrument Usage

- Enabled Phase 03 `market` values: `VN_STOCK` and `GOLD`.
- `GOLD` identifies the single supported `XAUUSD` world-gold benchmark, not all
  commodities.
- `XAUUSD` has the user-facing display name `Gold`; it is not labeled as or
  treated as a domestic SJC product.
- The benchmark is quoted in USD per troy ounce.
- Each enabled instrument declares a display name, quote currency or unit, and
  active/unsupported status.

## GoldCollectionRequest

Feature-owned request passed to the common dataflow boundary.

- `instrument_id`: `XAUUSD`.
- `required_datasets`: supported Gold OHLC price history.
- `requested_at`: collection request timestamp.

Rules:

- Requests for unsupported assets or undeclared datasets are rejected before
  collection.
- The Gold technical-analysis workflow binds `instrument_id` to `XAUUSD`; users
  do not submit a market, symbol, or instrument value for that workflow.
- A collection request does not expose provider credentials or raw payloads.
- Gold evidence timestamps are normalized to UTC. Source-specific symbol mapping
  remains inside the connector contract.

## GoldEvidenceRecord

Feature-owned deterministic record produced from normalized gold source data.

- `record_type`: bounded gold market record type declared by the selected source
  contract.
- `instrument_id`, `market`, `period`, `source_record_ids`, and `payload`.
- `context`: deterministic rendered projection for LLM and UI use.
- `allowed_claims` and `blocked_claims`.
- `source_id`, `dataset_id`, `market_time`, `collected_at`, freshness status,
  warnings, and methodology version.

Rules:

- Gold records have the same citation allowlist and rendering rules as other
  records, but never claim stock-only fundamentals.
- Gold technical records use OHLC evidence and may omit volume; a missing volume
  cannot be inferred or presented as zero.
- Stale, delayed, missing, or mismatched benchmark data blocks affected claims.

## WorkflowSpecification Usage

- Each Phase 03 catalog entry declares market scope, enabled inputs, required
  datasets, stages, expected sections, citation policy, chart intent, and
  unsupported categories.
- VN stock brief composes collection, grounding, fundamental, and technical
  steps. Gold workflows exclude stock-only financial-statement sections.
- A workflow may complete as `success`, `partial`, `failed`, or `unavailable`.

## ExecutionRun And Citation Usage

- Workflow runs persist market, instrument, inputs, stage status, final output,
  artifacts, warnings, status, and captured output language through the shared
  run store.
- Citation snapshots retain source id, dataset id, timestamp, rendered evidence,
  and enough structured context for later inspection.
- Reinspection restores final/partial output and limitations without raw agent
  reasoning or provider dumps.
