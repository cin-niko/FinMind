---
id: SPEC-FEAT-002-DATA
feature: workflow
status: active
owner: solo
created: 2026-06-26
implements: []
validated_by: []
adr_refs: []
---

# Data Model: Workflow

This feature uses shared entities from `../system/state-model.md` and defines
Phase 02 workflow-specific usage/extensions below.

## MarketInstrument

Represents a supported equity instrument.

Fields:

- `instrument_id`: stable symbol or index id such as `VCB`, `VNINDEX`, `AAPL`.
- `symbol`: user-facing symbol.
- `market`: `VN_STOCK` or `US_STOCK`.
- `display_name`: user-facing label.
- `currency`: quote currency.
- `status`: active, inactive, unsupported.

Validation:

- Phase 02 accepts only `VN_STOCK` and `US_STOCK`.
- Gold, BTC, crypto, commodities, options, and futures are unsupported.

## CanonicalMarketDataRecord

Normalized market data item used by collection, charts, indicators, and evidence.

Fields:

- `dataset_id`: `vn_prices`, `us_prices`, `vn_fundamentals`,
  `us_fundamentals`, `source_documents`, or equivalent bounded demo dataset.
- `record_key`: unique logical key.
- `instrument_id`: linked instrument.
- `market_time`: effective market timestamp.
- `collected_at`: collection timestamp.
- `source_id`: source connector or demo source identity.
- `retrieval_id`: optional id linking records fetched during the same dataflow
  retrieval attempt.
- `payload`: normalized values such as close, change percent, volume, EPS, BVPS,
  revenue, profit, valuation ratios, or peer metrics.
- `freshness_status`: fresh, stale, missing, failed.

Validation:

- `(dataset_id, record_key)` is unique.
- Price records used in technical analysis must include enough points for the
  requested chart/indicator or the chart claim category is blocked.
- Fundamental records used in valuation must include compatible reporting period
  metadata or valuation confidence is blocked/qualified.
- Provider records must preserve market/effective timestamp and collection
  timestamp separately.
- Deterministic fallback records must use source ids that make fallback status
  visible, not pretend to be live provider data.

## DataflowRetrievalRequest

Input contract for retrieving evidence-ready finance data.

Fields:

- `market`: `VN_STOCK` or `US_STOCK`.
- `symbol`
- `dataset_groups`: `market_price`, `fundamental`, `news`.
- `lookback`: optional period/window for price history or news.
- `allow_fallback`: whether deterministic fallback may be used when live
  providers are unavailable.
- `requested_by`: workflow id or future chatflow request id.

Validation:

- Dataset groups must map from workflow `required_datasets` or future chatflow
  retrieval needs.
- Unsupported markets or symbols are rejected before provider calls.
- Fallback use must be explicit and visible in the retrieval result.

## DataflowRetrievalResult

Output contract returned by `DataflowService.retrieve(...)`.

Fields:

- `retrieval_id`
- `market`: `VN_STOCK` or `US_STOCK`.
- `symbol`
- `requested_dataset_groups`: `market_price`, `fundamental`, `news`.
- `provider_results`: provider status records.
- `records`: canonical market data records.
- `source_documents`: source documents/news records.
- `started_at`
- `completed_at`
- `status`: success, partial, failed, fallback.
- `warnings`
- `failure_reasons`
- `records_collected`
- `documents_collected`

Validation:

- Provider failures, missing API keys, timeouts, rate limits, and unsupported
  symbols must be represented in `warnings` or `failure_reasons`.
- A fallback run must not be marked as fresh live provider data.
- Raw provider payloads and secrets must not be returned.

## DataflowProviderResult

Status for one provider attempt within a retrieval.

Fields:

- `provider_id`: e.g. `vnstock`, `alpha_vantage`, `sec_edgar`,
  `offline_fallback`.
- `dataset_groups`
- `status`: success, partial, failed, skipped, fallback.
- `source_ids`
- `started_at`
- `completed_at`
- `warnings`
- `failure_reason`
- `rate_limit_hint` when available.

Validation:

- Provider status is user-visible only as safe source/status metadata.
- Provider diagnostics must not include credentials, raw responses, or unsafe
  internals.

## SourceProvider

Adapter identity and capability metadata.

Fields:

- `provider_id`
- `market_scope`
- `dataset_capabilities`
- `requires_api_key`
- `license_notes`
- `timeout_seconds`
- `enabled`

Validation:

- Provider adapters must normalize output to shared canonical records/documents.
- Provider secrets and raw responses must not appear in user-facing output.
- Product contracts should cite source identity and data timestamp without
  hardcoding implementation details into UI copy.

## SourceDocument

Trusted source material for news digest and fundamental context.

Fields:

- `document_id`
- `source_id`
- `title`
- `published_at`
- `collected_at`
- `url_or_reference`
- `content_excerpt`
- `market_scope`
- `instrument_ids`
- `sentiment_hint` when available

Validation:

- Missing or stale documents block or qualify news digest claims.
- Source excerpts must respect source constraints.

## WorkflowSpecification

Machine-readable YAML workflow definition.

Fields:

- `workflow_id`: e.g. `fundamental-analysis`, `technical-analysis`,
  `news-digest`, `risk-review`, `stock-brief`.
- `definition_path`: project-relative YAML definition path.
- `version`: workflow contract version.
- `title`
- `description`
- `workflow_type`: atomic, internal, composite.
- `market_scope`
- `required_inputs`
- `required_datasets`
- `stages`
- `skill_refs`: Markdown agent skills referenced by analysis stages.
- `output_sections`
- `citation_policy`
- `chart_requirements`
- `step_sequence`: ordered step ids for composite workflows.

Validation:

- User-facing workflows must be runnable from the UI.
- Internal steps are not primary catalog cards unless diagnostics are later
  specified.
- Composite workflows reference existing workflow or internal step ids.
- Referenced Markdown agent skills must exist and declare compatible evidence and
  output expectations.

## AgentSkill

Governed Markdown instruction document for one analysis capability.

Fields:

- `skill_id`: stable id such as `fundamental-analysis`.
- `skill_path`: project-relative Markdown path.
- `version`
- `purpose`
- `required_context`
- `allowed_claims`
- `blocked_behavior`
- `output_contract`
- `citation_policy`
- `safety_rules`

Validation:

- Skills must not declare supported markets or permissions broader than the
  workflow definition and runtime allow.
- Skills must instruct unavailable or unsupported output when evidence is stale,
  missing, failed, or blocked by `data-quality-check`.
- Skills are not directly executable by external clients; the guarded runtime
  invokes them through workflow definitions.

## WorkflowStep

Runtime stage within a workflow run.

Fields:

- `step_id`
- `title`
- `kind`: collector, quality_gate, analysis, artifact, risk
- `status`: queued, running, success, partial, failed, unavailable
- `started_at`
- `completed_at`
- `blocking_issues`
- `warnings`
- `output_refs`

Validation:

- Failed/unavailable steps must not silently produce claims.
- Partial composite workflows preserve successful step outputs.

## DatasetQualityReport

Output of `data-quality-check`.

Fields:

- `quality_status`: pass, warn, partial, fail.
- `dataset_statuses`: mapping from dataset id to fresh, stale, missing, failed,
  or partial.
- `blocking_issues`: issues preventing claim categories.
- `warnings`: issues requiring caveats.
- `allowed_claims`: claim categories safe to generate.
- `blocked_claims`: claim categories omitted or marked unavailable.
- `freshness_summary`: user-visible freshness note.
- `evidence_refs`: evidence or record references checked.

Validation:

- Claim-generating steps must inspect `allowed_claims` and `blocked_claims`.
- Quality warnings must be visible in result output.

## ExecutionRun

Workflow run record.

Additional Phase 02 output expectations:

- `sections`: generated result sections with citation ids and status.
- `quality`: dataset quality report.
- `citations`: visible citations.
- `freshness`: per-dataset freshness.
- `artifacts`: charts/tables/computed outputs.
- `visible_execution`: stage statuses, tool/artifact status, warnings, and
  unavailable sections.
- `logs`: internal event summaries without raw reasoning.

State transitions:

```text
queued -> running -> success
queued -> running -> partial
queued -> running -> failed
```

## EvidenceObject / Citation / Artifact

Reuse shared contracts:

- Evidence links claims to source records/documents/artifacts.
- Citations are visible source references for material claims.
- Artifacts are traceable chart/table/computed outputs with accessible fallback
  data.
