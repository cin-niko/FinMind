---
id: SPEC-SYSTEM-STATE-FINMIND
status: active
last_review: 2026-07-12
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

### UserLanguagePreference

Represents the authenticated user's persisted web-language selection and its
effective output language.

- `username`: linked internal admin user
- `selection`: `auto`, `vi`, or `en`
- `updated_at`: latest preference update timestamp

Rules:

- The preference is owned by the authenticated user and persisted server-side;
  it remains available across browser sessions and devices.
- The initial selection is `auto`. The UI offers exactly `Auto-detect`,
  `English`, and `Vietnamese`.
- With `auto`, the UI resolves the effective language from the browser's ordered
  language list: it normalizes `vi-*` to `vi` and `en-*` to `en`, uses the first
  supported entry, and uses `en` when no supported entry exists. With an
  explicit selection, the effective language is that selection.
- The selection and effective language control web-visible copy. Source
  identifiers, citations, timestamps, numeric values, and market symbols remain
  unchanged.
- At workflow submission the UI sends the resolved effective language (`vi` or
  `en`). The backend validates and captures that value as `output_language` and
  uses it for generated Phase 03 workflow narrative. A later selection change
  does not rewrite saved workflow output.

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
  every workflow-created conversation.
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

### WorkflowResult

The transient, non-conversation output of one fixed workflow execution.

- `workflow_id`: workflow that produced the result
- `status`: success or failed
- `output`: structured result sections or product-facing failure summary
- `stage_status`: safe visible workflow-stage state
- `citations`: cited evidence references
- `artifacts`: generated chart or file outputs
- `output_language`: resolved language used for narrative, when applicable

Rules:

- `WorkflowResult` is an execution boundary, not a persisted user-history root
  and not a message. It does not own citations or artifacts after persistence.
- The conversation adapter maps a `WorkflowResult` to an assistant message and
  assigns its citations and artifacts to that message.

### Conversation

The product-owned root for a user's ordered messages. Starting a fixed workflow
always creates a new conversation. Its workflow result is passed to the
conversation adapter, which creates the first assistant message. Future chat
also creates messages in conversations; Phase 03 does not add arbitrary
follow-up messages or flexible chat routing.

- `conversation_id`: unique identifier
- `owner_username`: authenticated user who owns the conversation
- `workflow_id`: fixed workflow that created the conversation, when applicable
- `inputs`: accepted workflow inputs, when applicable
- `output_language`: resolved `vi` or `en` captured at submission
- `status`: queued, running, success, failed
- `title`: user-facing conversation title
- `created_at`, `started_at`, `completed_at`, `updated_at`: lifecycle timestamps
- `messages`: ordered message ids
- `stage_status`: visible safe workflow-stage state

Rules:

- An unavailable field, claim, chart, or section is output-level evidence state,
  not a conversation terminal status. The rendered response must state the
  affected item is unavailable without changing an otherwise successful
  conversation.
- A conversation is successful only when all planned workflow stages complete
  safely. A timeout, interrupted execution, or failed planned stage makes the
  conversation failed; the shared status contract does not use `partial`.
- A submitted conversation may briefly be `queued` before execution and is
  `running` while executing. If the service restarts, it must mark any persisted
  `queued` or `running` conversation from the interrupted service instance as
  `failed`, record `completed_at`, and retain a product-facing interruption
  summary. It does not resume the interrupted workflow.
- Conversations are owned by `owner_username`. Every conversation read, update,
  and delete operation must authorize that owner; citations and artifacts are
  reached only through an authorized conversation.
- The conversation persists until its owner deletes it; Phase 03 has no
  automatic time-based purge. Deleting a conversation cascade-deletes its
  messages, the citation snapshots and artifacts owned by those messages, and
  execution metadata, but never deletes shared canonical market-data records.
  Deletion is allowed only after the conversation reaches `success` or `failed`;
  deleting `queued` or `running` conversations is rejected because Phase 03 has
  no cancellation.
- Raw agent reasoning remains internal and is not included in user-facing
  messages. The conversation store persists after an app restart; its database
  configuration follows `FINMIND_DATABASE_URL` and fails closed when unavailable.

### Message

An ordered user-facing entry within one conversation.

- `message_id`: unique identifier
- `conversation_id`: owning conversation
- `role`: `user` or `assistant`
- `content`: user text or rendered response content
- `created_at`: creation timestamp
- `source_kind`: `workflow_result` or a future chat-message source
- `workflow_id`: fixed workflow identifier when `source_kind` is
  `workflow_result`
- `status`: optional safe result/failure state for a workflow-result message

Rules:

- A workflow produces a `WorkflowResult`; it does not create a user-facing
  message itself. The conversation adapter maps that result to one assistant
  message in the new conversation, including a product-facing failure summary
  when applicable.
- Chat creates its own user and assistant messages through its future chatflow
  path. Both workflow and chat messages use this same conversation/message
  ownership model.
- Citations and artifacts belong to the assistant message they support, not
  directly to a workflow result or conversation. They are reached through that
  message and its authorized conversation.

### Citation

User-visible source reference generated by the LLM from allowed data records and
validated by runtime grounding rules.

- `citation_id`: unique identifier
- `message_id`: owning assistant message
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
- Cited citation ids must be a subset of the owning message's citation allowlist; otherwise
  the claim is an `uncited_claim` and grounding is `blocked`.
- Citations are not artifacts and must resolve back to allowed data records.
- The persisted citation row must be sufficient for UI inspection even when the
  intermediate derived `DataRecord` is not stored durably.

### Artifact

Parent model for generated outputs that users can open or download.

- `artifact_id`: unique identifier
- `message_id`: owning assistant message
- `artifact_type`: `file` or `chart`
- `title`: user-facing title
- `inputs`: linked data and conversation inputs
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

- File and chart artifacts must be traceable to canonical data and their owning
  assistant message.
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
  the answer or conversation, and jump to the selected source.

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
