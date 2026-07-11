---
id: SPEC-SYSTEM-STATE-FINMIND
status: active
last_review: 2026-07-11
implements:
  - src/finmind_agents
validated_by:
  - tests/test_platform_services.py
adr_refs:
  - docs/adr/ADR-003-artifact-and-citation-inspection-contract.md
---

# System State Model

This spec defines stable domain state shared across FinMind features. Feature folders may extend usage, but should not redefine these entities differently.

## Market Scope

`002-workflow` establishes the workflow, citation, grounding, and chart
contracts. `003-vn-gold-dataflows-workflows` defines the active user-facing
workflow scope as VN stocks and gold. Future market
scope is not canonical until a bounded feature spec defines supported assets,
source eligibility, and safety behavior.

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

Represents a supported workflow instrument: a VN stock or configured gold
benchmark.

- `instrument_id`: stable internal identifier
- `symbol`: market symbol or commodity code
- `market`: `VN_STOCK` or `GOLD`
- `display_name`: user-facing name
- `currency`: quote currency
- `status`: active, inactive, unsupported

### CanonicalMarketDataRecord

Normalized market data item used by workflows, charts, indicators, and evidence.

- `dataset_id`: dataset/source grouping such as VN stock or gold price series
- `record_key`: unique logical key within dataset
- `instrument_id`: linked instrument
- `market_time`: effective market timestamp
- `collected_at`: ingestion collection timestamp
- `source_id`: source connector identifier
- `payload`: normalized data values

Rules:

- `(dataset_id, record_key)` must be unique.
- Reruns for the same logical record update or replace the canonical record instead of duplicating it.

### DataRecord

Deterministic record derived from raw or canonical provider data before any LLM
call. Data records are the model-visible data contract for grounded
workflow and chatflow answers.

- `record_id`: stable deterministic id
- `record_type`: `price_summary_record`, `indicator_record`,
  `pattern_evidence_record`, `pattern_setup_record`, `company_profile_record`,
  or `fundamental_record`
- `symbol`: market symbol
- `market`: `VN_STOCK` or `GOLD`
- `period`: effective period or window represented by the record
- `source_record_ids`: linked canonical/raw record ids used to produce it
- `payload`: compact model-visible facts
- `context`: deterministic rendered content derived from record fields for LLM
  context and human-readable display
- `is_audited`: boolean audit gate for `fundamental_record`; true for records
  whose deterministic audit/refinement has completed
- `allowed_claims`: claim categories this record can support
- `blocked_claims`: claim categories this record cannot support
- `warnings`: data quality or audit warnings
- `methodology_version`: version of the calculation/audit method
- `created_at`: record creation timestamp

Rules:

- Given the same source records and methodology version, the same data record
  ids and payloads should be produced.
- `DataRecord` defines the deterministic pre-LLM interface and may be
  recalculated from persisted base data; it is not required to be persisted for
  every run.
- The structured record fields remain canonical; `context` is a deterministic
  rendered projection of those fields, not the source of truth.
- The default implementation may use a class-owned template and cached
  rendering. Subclasses may override rendering behavior when they need custom
  logic.
- `price_series_record` is the default persisted base record for charting,
  reuse, and recalculation, but is not normally sent to the LLM.
- Phase 02 does not define `news_record`, `risk_record`, or a separate
  `fundamental_flags_record`.
- Fundamental claims should use `fundamental_record` only when `is_audited=true`
  unless the workflow explicitly marks output as preliminary/unavailable.

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
- Completed runs persist to the PostgreSQL run store so they remain inspectable
  from `History` -> `Workflow Runs` (and later chat history) after an app
  restart. One `runs` table serves both `workflow` and `chat` runs via the
  `kind` discriminator. The DSN is configured via `FINMIND_DATABASE_URL`; the app
  fails closed when it is missing or unreachable.

### Citation

User-visible source reference generated by the LLM from allowed data records and
validated by runtime grounding rules.

- `citation_id`: unique identifier
- `run_id`: linked workflow or chatflow run
- `record_id`: linked data record
- `record_type`: data record type
- `source_id`: source connector or demo source identity
- `dataset_id`: dataset the claim draws from
- `label`: user-facing citation label
- `timestamp`: source or market timestamp (conveys data age)
- `cited_fields`: optional record fields or payload paths cited by the answer
- `payload_snapshot`: compact cited evidence snapshot persisted for UI
  inspection
- `display_content`: optional rendered snippet or markdown content used by
  citation inspection surfaces
- `methodology_version`: optional derived-record methodology version when the
  citation comes from calculated evidence

Rules:

- Material user-facing claims require at least one citation or explicit unsupported/unavailable marking.
- Cited citation ids must be a subset of the run's citation allowlist; otherwise
  the claim is an `uncited_claim` and grounding is `blocked`.
- Citations are not artifacts and must resolve back to allowed data records.
- The persisted citation row must be sufficient for UI inspection even when the
  intermediate derived `DataRecord` is not stored durably.

### Artifact

Parent model for generated outputs that users can open or download.

- `artifact_id`: unique identifier
- `artifact_type`: `file` or `chart`
- `title`: user-facing title
- `inputs`: linked data and run inputs
- `source_refs`: linked citation ids
- `status`: ready, unavailable, or failed
- `reason`: optional unavailable or failure reason

### FileArtifact

Physical generated asset such as PDF, PPTX, DOCX, XLSX, CSV, PNG, JPG, or SVG.

- `artifact_type`: `file`
- `file_type`: product-facing file category
- `mime_type`: technical content type for browser, storage, download, and
  validation behavior
- `filename`: user-facing download filename
- `url`: file location controlled by the authenticated app
- `size_bytes`: optional file size
- `downloads`: one or more downloadable representations

### ChartArtifact

Structured chart output rendered by trusted FinMind UI components.

- `artifact_type`: `chart`
- `chart_intent`: product/runtime intent such as `price_trend`
- `spec`: renderable chart specification
- `supported_views`: supported chart views such as line and candlestick
- `default_view`: initial chart view
- `downloads`: exported chart formats such as PNG or CSV

Rules:

- File and chart artifacts must be traceable to canonical data and execution context.
- Chart artifacts must be rendered by trusted UI components and must not execute
  arbitrary generated HTML or JavaScript.
- Citations are not artifacts; source inspection uses citation panel state.

### RightPanelDisplayState

Client-side display state for contextual inspection.

- `mode`: artifact or citations
- `artifact_id`: selected artifact when `mode=artifact`
- `citation_id`: selected citation/source when `mode=citations`

Rules:

- Artifact cards open artifact mode and show the full artifact viewer.
- Inline citation chips open citations mode, show the complete source list for
  the answer or run, and jump to the selected source.

### MockChatConversation

Client-side `001-mvp-ui` conversation around deterministic mock finance research
responses.

- `chat_id`: unique identifier
- `messages`: user and assistant messages
- `title`: derived from the first user message
- `artifacts`: trusted mock report, chart, table, or file-style artifacts
  rendered by local templates

Rules:

- `001-mvp-ui` mock chat must not present itself as production evidence-backed
  orchestration.
- Mock chat must not expose raw agent reasoning or execute arbitrary generated
  HTML.
- Mock citations must render inline or in citation inspection surfaces, not as
  citation-bundle or evidence-list artifact cards.
