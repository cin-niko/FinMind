---
id: SPEC-SYSTEM-STATE-FINMIND
status: active
last_review: 2026-06-18
implements:
  - src/agent_core
validated_by:
  - tests/test_platform_services.py
adr_refs:
  - docs/adr/0001-vn-only-v1-market-scope.md
  - docs/adr/0006-shared-evidence-lineage-tables.md
---

# System State Model

This spec defines stable domain state shared across FinMind features. Feature folders may extend usage, but should not redefine these entities differently.

## Market Scope

V1 supports VN stocks only as user-facing markets, scoped to the pre-seeded VN100 universe. US stocks, gold (XAUUSD/SJC), and BTC remain roadmap markets. Shared identifiers may preserve extension points for future markets, but no V1 user surface may imply roadmap-market coverage.

## Entities

### InternalAdminUser

Represents the single environment-configured internal account initialized at application startup for V1.

- `username`: unique login name
- `password_secret`: validated against configured secret, never exposed
- `role`: `admin`
- `config_source`: environment bootstrap
- `created_at`: bootstrap timestamp
- `last_login_at`: latest successful login timestamp

Rules:

- Exactly one admin account is required for V1.
- The account is bootstrapped from `FINMIND_ADMIN_USERNAME`, `FINMIND_ADMIN_PASSWORD`, and `FINMIND_SESSION_SECRET`.
- Missing or invalid bootstrap environment values fail closed before protected app access is available.

### Session

Represents cookie-backed authenticated web access.

- `session_id`: unique opaque identifier
- `username`: linked admin user
- `role`: current role
- `created_at`: session creation timestamp
- `expires_at`: expiration timestamp

Rules:

- Protected app/API access requires an active session.
- Logout or expiration invalidates protected access.

### MarketInstrument

Represents a supported VN stock or gold instrument.

- `instrument_id`: stable internal identifier
- `symbol`: market symbol or commodity code
- `market`: `VN_STOCK` or `GOLD`
- `display_name`: user-facing name
- `currency`: quote currency
- `asset_class`: stock, commodity, or a later approved class
- `exchange`: exchange, board, or venue label when applicable
- `sector`: sector classification when applicable
- `industry`: industry classification when applicable
- `sub_industry`: optional deeper classification when applicable
- `status`: active, inactive, unsupported

### MarketCollection

Represents a reusable market grouping for indexes, predefined watchlists, sectors, and themes.

- `collection_id`: stable collection identifier
- `market`: supported market scope
- `name`: user-facing label
- `collection_type`: index, watchlist, sector, or theme
- `description`: optional short description
- `sort_order`: optional UI ordering

### MarketCollectionMembership

Represents an effective-dated link between an instrument and a market collection.

- `collection_id`: linked market collection
- `instrument_id`: linked market instrument
- `weight`: optional index/watchlist weight
- `effective_from`: membership start date
- `effective_to`: membership end date when no longer active

### CanonicalMarketDataRecord

Normalized market data item used by workflows, charts, indicators, and evidence.

- `dataset_id`: dataset/source grouping such as VN price series or gold spot
- `record_key`: unique logical key within dataset
- `instrument_id`: linked instrument
- `market_time`: effective market timestamp
- `collected_at`: ingestion collection timestamp
- `source_id`: source connector identifier
- `payload`: normalized data values
- `freshness_status`: fresh, stale, missing, failed

Rules:

- `(dataset_id, record_key)` must be unique.
- Reruns for the same logical record update or replace the canonical record instead of duplicating it.
- Feature implementations may store high-volume observations in typed time-series tables while preserving this logical contract for identity, freshness, evidence, citations, and artifacts.

### SourceDocument

Company report, macro news, market news, or document-like evidence source.

- `document_id`: unique identifier
- `source_id`: source connector identifier
- `title`: source title
- `published_at`: publication timestamp when available
- `collected_at`: collection timestamp
- `url_or_reference`: source reference
- `content_excerpt`: stored excerpt or summary allowed by source constraints
- `market_scope`: related market or instrument scope

### IngestionJob

Scheduled or manual data fetch operation.

- `job_id`: unique identifier
- `source_id`: source connector or dataset
- `trigger`: scheduled or manual
- `period`: requested dataset period
- `status`: queued, running, success, failed, skipped
- `started_at`: start timestamp
- `completed_at`: completion timestamp when available
- `record_count`: canonical records affected
- `diagnostics`: non-secret outcome or error context

Rules:

- Manual reruns for the same dataset and period must be idempotent.
- Unsafe overlapping runs for the same dataset and period must be blocked with visible status.

### WorkflowSpecification

Declarative fixed research workflow definition.

- `workflow_id`: stable identifier
- `title`: user-facing name
- `market_scope`: supported market or instrument type
- `inputs`: validated input schema
- `required_datasets`: dataset dependencies
- `stages`: ordered analysis stages
- `role_agents`: applicable analysis roles such as fundamental, technical, macro, or risk
- `output_sections`: expected result sections
- `citation_policy`: required citation behavior
- `chart_requirements`: required or optional charts

Rules:

- Workflows must remain bounded and independently testable.
- Workflow definitions must not hardcode provider-specific details.

### ExecutionRun

Common record for workflow and chat execution.

- `run_id`: unique identifier
- `kind`: workflow or chat
- `status`: queued, running, success, partial, failed
- `requested_by`: admin user
- `inputs`: user inputs or question
- `started_at`: start timestamp
- `completed_at`: completion timestamp when available
- `output`: linked result output
- `logs`: execution events

Rules:

- Partial runs distinguish completed sections from failures.
- Raw agent reasoning remains internal and is not included in user-facing output.

### EvidenceObject

Grounding unit connecting claims and artifacts to source material.

- `evidence_id`: unique identifier
- `claim_ref`: output section or claim supported
- `source_refs`: market records, source documents, or artifacts
- `observed_at`: timestamp for the evidence
- `freshness_status`: fresh, stale, missing, failed
- `summary`: concise evidence summary

Rules:

- Material user-facing claims require at least one evidence object and citation, or explicit unsupported/unavailable marking.

### Citation

User-visible source reference.

- `citation_id`: unique identifier
- `evidence_id`: linked evidence object
- `label`: user-facing citation label
- `source_type`: market_data, document, artifact
- `source_reference`: URL, document id, dataset key, or artifact id
- `timestamp`: source or collection timestamp

### Artifact

Generated chart, table, computed output, or inline visualization.

- `artifact_id`: unique identifier
- `artifact_type`: chart, table, computed_result, inline_visualization
- `title`: user-facing title
- `inputs`: linked data and run inputs
- `payload`: renderable artifact data
- `evidence_refs`: linked evidence objects

Rules:

- Chart and inline visualization artifacts must be traceable to canonical data and execution context.

### ChatSession

Conversation around open-ended finance research questions.

- `chat_id`: unique identifier
- `messages`: user and assistant messages
- `role_agent_events`: role-agent execution status
- `runs`: linked execution runs
- `artifacts`: inline visualizations or computed outputs

Rules:

- Chat answers use the same evidence, citation, freshness, and artifact contracts as workflows.
- Unsupported market questions produce clear scope limitations.
