---
id: SPEC-SYSTEM-CONTRACTS-FINMIND
status: active
last_review: 2026-07-09
implements:
  - src/finmind_agents
  - src/finmind_api
validated_by:
  - tests/test_app.py
  - tests/test_platform_services.py
adr_refs:
  - docs/adr/ADR-003-artifact-and-citation-inspection-contract.md
---

# System Contracts

This spec defines stable contract rules for API responses, generated artifacts, citations, grounding, execution visibility, and provider abstraction.

## API Surface

The authenticated app shell consumes JSON APIs for:

- Session state: `GET /api/session`, `POST /api/login`, `POST /api/logout`
- Workflow catalog and runs: `GET /api/workflows`, `POST /api/workflows/{workflow_id}/run`
- Result inspection: `GET /api/runs`, `GET /api/runs/{run_id}`,
  `GET /api/runs/{run_id}/citations`

All protected APIs require an active cookie-backed session. Raw agent reasoning is never returned.

## Citation And Grounding Contract

Material user-facing claims must be backed by at least one citation or be explicitly marked unsupported or unavailable. A citation must include:

- `citation_id`: unique identifier
- `record_id`: deterministic data record id
- `record_type`: data record type
- `source_id`: source connector or demo source identity
- `dataset_id`: dataset the claim draws from
- User-facing label
- Source or market timestamp (conveys data age)
- Optional cited fields or payload paths

Cited ids must be a subset of the run's citation allowlist. Claims citing ids
not in the returned set are `uncited_claims` and force grounding to `blocked`.
Data age is conveyed by citation timestamps; there is no separate
freshness-status concept.

The product-wide data-record boundary is defined in
[`specs/system/data-record-flow.md`](data-record-flow.md).
That note defines the general fetch -> normalize -> derive -> package -> cite ->
LLM flow used across FinMind surfaces.

## Artifact Contract

Artifacts are reusable outputs linked to inputs, source refs, and execution context.

Supported artifact types:

- `file`
- `chart`

All production artifacts share `artifact_id`, `artifact_type`, title, status,
optional reason, and `source_refs`.

File artifacts represent physical assets and must include `file_type`,
`mime_type`, filename, file location, and download metadata. The product UI uses
`file_type` for labels, icons, and viewer choice; transport, storage, download,
and content validation use `mime_type`.

Workflow chart artifacts are deterministic runtime outputs selected through
structured chart requirements such as `price_trend`, not arbitrary LLM-generated
HTML or JavaScript. Chart artifacts must include chart intent, supported chart
views, default view, renderable chart spec, linked source refs, status, and
download metadata. Chart artifacts should not require a price table in the main
answer; raw chart data access should use downloads or a separate file artifact
when specified.

Citations are evidence/source references, not artifacts. Inline citation chips
open citation inspection and must not be modeled as citation-bundle artifacts.

Inline artifacts in chat must follow the same traceability and safe-rendering
rules as workflow artifacts.

`001-mvp-ui` mock chat artifacts are trusted local-template UI artifacts, not API
execution artifacts. Production chat artifact contracts require a future bounded
feature spec.

## Execution Visibility Contract

User-facing execution status may include:

- Workflow stages
- Role-agent status
- Tool or artifact status
- Run status: queued, running, success, partial, failed
- Failure summaries and unavailable sections

User-facing execution status must not include hidden model reasoning transcripts.

## Provider Abstraction

Product contracts must stay provider-neutral. Source connector implementation may validate provider suitability, licensing, credentials, and schema details, but public feature specs and user-facing contracts should refer to supported datasets and source identities rather than locking the product to one vendor.

## Layering Contract

FinMind keeps separable layers:

- App experience in UI
- FastAPI JSON API
- Finance orchestration and data services
- LangChain-backed agent runtime
- Data contracts and repositories

Feature work should use the LangChain-backed runtime in
`src/finmind_agents/runtime` for workflow and future chatflow agent execution.
Finance-specific workflow semantics, dataflow access, citations, and safety
policy remain above provider model adapters.
