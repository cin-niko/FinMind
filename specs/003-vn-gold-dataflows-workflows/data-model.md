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
- `required_datasets`: supported daily Gold OHLC price history.
- `requested_at`: collection request timestamp.

Rules:

- Requests for unsupported assets or undeclared datasets are rejected before
  collection.
- The Gold technical-analysis workflow binds `instrument_id` to `XAUUSD`; users
  do not submit a market, symbol, or instrument value for that workflow.
- Each collection fetches the fullest daily history returned within the
  configured source's supported limit and upserts the shared canonical XAUUSD
  price-series record. Phase 03 does not request or retain other intervals.
- A transient configured-provider collection failure makes at most two retries
  after the initial attempt. If all attempts fail, collection fails without
  returning a cached response or using another provider.
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
- `source_id`, `dataset_id`, UTC `market_time`, UTC `collected_at`, warnings,
  and methodology version.

Rules:

- Gold records have the same citation allowlist and rendering rules as other
  records, but never claim stock-only fundamentals.
- Gold technical records use daily OHLC evidence and may omit volume; a missing
  volume cannot be inferred or presented as zero.
- Missing, invalid, or mismatched benchmark data blocks affected claims.
- `market_time` is the evidence time shown to analysts; `collected_at` records
  when FinMind received the evidence for audit and reinspection. Phase 03 does
  not derive a separate fresh/stale classification from either timestamp.

## WorkflowSpecification Usage

- Each Phase 03 catalog entry declares market scope, enabled inputs, required
  datasets, stages, expected sections, citation policy, chart intent, and
  unsupported categories.
- VN stock brief composes collection, grounding, fundamental, and technical
  steps. Gold workflows exclude stock-only financial-statement sections.
- A workflow-created conversation terminates as `success` or `failed`; it may be
  `queued` or `running` before termination. Phase 03 does not use `partial`.
- Unavailable belongs to a field, claim, chart, or section. It is explicitly
  rendered in the deterministic evidence context before the LLM sees the
  record, and it does not change a successful conversation by itself.

## Conversation, Message, And Evidence Usage

- Starting a workflow always creates a new owned conversation before execution.
  The conversation persists workflow metadata, market, instrument, inputs, stage
  status, overall status, and captured effective output language (`vi` or `en`).
  The workflow produces a `WorkflowResult`; a conversation adapter maps it to
  the conversation's first assistant message or product-facing failure summary.
  The user's separately persisted language selection may be `auto`, `vi`, or
  `en`.
- Citation snapshots retain source id, dataset id, timestamp, rendered evidence,
  and enough structured context for later inspection on their owning assistant
  message.
- Conversation inspection restores the assistant message created by the adapter,
  or a failed conversation's product-facing failure summary, and field-level
  limitations without raw agent reasoning or provider dumps.
- A conversation stores its accepted, running, and terminal lifecycle
  timestamps. A timeout or service-restart interruption stores a terminal
  `failed` status and product-facing summary; interrupted conversations are not
  resumed.
- Deleting a conversation cascade-deletes its messages, their citations and
  artifacts, and execution metadata. It does not delete canonical market data
  records, which can be shared by later conversations.
- Phase 03 reuses the shared citation allowlist and persisted citation snapshots;
  it does not persist every intermediate derived record or introduce a separate
  workflow/skill-version history for recomputation.

## News Digest Usage

The news digest uses the shared `SourceDocument` evidence model. Each Phase 03
news source carries provider-delivered URL, title, publication time, and content
for citation and LLM context. The configured web-search provider and the exact
source-document schema are plan decisions; the workflow does not deterministically
deduplicate collected articles.
