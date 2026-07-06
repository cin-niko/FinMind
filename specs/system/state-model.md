---
id: SPEC-SYSTEM-STATE-FINMIND
status: active
last_review: 2026-06-18
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

`002-workflow` uses seeded/demo VN stock and US stock records to validate the workflow,
citation, grounding, and chart contracts. Future market scope is not
canonical until a new bounded feature spec defines supported assets, source
eligibility, and safety behavior.

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

Represents a supported VN stock or US stock instrument.

- `instrument_id`: stable internal identifier
- `symbol`: market symbol or commodity code
- `market`: `VN_STOCK` or `US_STOCK`
- `display_name`: user-facing name
- `currency`: quote currency
- `status`: active, inactive, unsupported

### CanonicalMarketDataRecord

Normalized market data item used by workflows, charts, indicators, and evidence.

- `dataset_id`: dataset/source grouping such as VN or US price series
- `record_key`: unique logical key within dataset
- `instrument_id`: linked instrument
- `market_time`: effective market timestamp
- `collected_at`: ingestion collection timestamp
- `source_id`: source connector identifier
- `payload`: normalized data values

Rules:

- `(dataset_id, record_key)` must be unique.
- Reruns for the same logical record update or replace the canonical record instead of duplicating it.

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

User-visible source-level reference derived directly from collected canonical
records. There is no separate `EvidenceObject` layer; grounding is enforced by a
post-skill `GroundingCheck` over citations.

- `citation_id`: unique identifier
- `source_id`: source connector or demo source identity
- `dataset_id`: dataset the claim draws from
- `label`: user-facing citation label
- `timestamp`: source or market timestamp (conveys data age)

Rules:

- Material user-facing claims require at least one citation or explicit unsupported/unavailable marking.
- Cited sources must be a subset of sources returned by collection; otherwise the claim is an `uncited_claim` and grounding is `blocked`.

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
