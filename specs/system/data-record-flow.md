---
id: SPEC-SYSTEM-DATA-RECORD-FINMIND
status: active
last_review: 2026-07-09
implements:
  - src/finmind_agents
  - src/finmind_api
  - src/finmind_ui
validated_by:
  - tests/test_app.py
  - tests/test_platform_services.py
adr_refs: []
---

# Data Record Flow

This spec defines the product-wide boundary between raw source data, deterministic
records, and LLM-visible context. It applies to workflows, chatflow, and any
future FinMind surface that turns fetched data into cited natural-language output.

## Core Rule

FinMind must not pass raw provider output directly to the LLM as the primary
analysis surface. The runtime owns the data-record pipeline:

1. Fetch raw source data.
2. Normalize and validate it.
3. Compute deterministic derived records.
4. Chunk or package those records into a compact data bundle.
5. Assign citation ids to the records that may be surfaced to the LLM.
6. Persist reusable base data and cited citation snapshots.
7. Send only the data bundle and citation allowlist to the LLM.
8. Validate the model output against the allowed citations and grounding rules.

## Boundary Table

| Step | Who does it | Simple rule | Notes |
|---|---|---|---|
| Fetch raw data | Runtime / dataflows | Deterministic | Collect provider payloads, source docs, and market records. |
| Normalize data | Runtime / dataflows | Deterministic | Convert provider output into canonical records. |
| Compute derived records | Runtime | Deterministic | Build indicators, pattern evidence, setup scores, and snapshots. |
| Chunk / package records | Runtime | Deterministic | Select the compact data bundle for the model call. |
| Assign citation ids | Runtime | Deterministic | Citation ids are created before the LLM sees the records. |
| Persist base data and cited snapshots | Runtime / API | Deterministic | Save `price_series_record` for reuse/charting and save the cited evidence snapshots needed for UI inspection. |
| Choose collection flow | Runtime / workflow policy | Deterministic | Workflow definitions and policy decide what to fetch. |
| Interpret records | Skill / LLM | LLM step | The model explains the evidence and labels unsupported claims. |
| Write answer text | Skill / LLM | LLM step | The model narrates from the supplied data bundle. |
| Generate citations | Skill / LLM within allowlist | LLM step | The model may reference only provided citation ids. |
| Validate grounding | Runtime validators | Deterministic | Reject unknown citations and unsupported claims. |

The dividing line is simple: everything before the LLM call is deterministic
runtime work; the LLM only writes from the packaged data bundle.

## Deterministic Record Contract

Deterministic records are product-owned data objects derived from raw source
data. They are the stable interface between collection and language generation.

Examples include:

- `price_series_record`: stored for chart rendering, reuse, and internal data
  workflows; not normally sent to the LLM.
- `price_summary_record`: compact price behavior summary for LLM-visible
  context.
- `indicator_record`: deterministic technical indicators.
- `pattern_evidence_record`: strict detected or invalidated pattern evidence.
- `pattern_setup_record`: forming or potential setup scoring.
- `company_profile_record`: company identity and profile context.
- `fundamental_record`: audited financial/fundamental record with
  `is_audited: boolean`.

Phase 02 does not define `news_record`, `risk_record`, or
`fundamental_flags_record`. News and catalyst claims must be marked unavailable
until a future source-ingestion contract defines deterministic news records. Risk
language may be generated only as interpretation of underlying technical or
fundamental records, cited back to those records.

Rules:

- Given the same raw inputs and methodology version, the same derived data
  records and citation ids should be produced.
- `DataRecord` is the deterministic runtime contract before the LLM call; it is
  not required to be a default persistent storage object for every run.
- `price_series_record` is the default persisted base record because it supports
  charts, reuse, and recalculation.
- Intermediate derived records such as `indicator_record`,
  `pattern_evidence_record`, `pattern_setup_record`, and
  `price_summary_record` may remain runtime-only unless a later audit/debug
  feature explicitly requires durable snapshots.
- Citations are generated from and validated against the provided data records.
  The persisted citation row is the durable user-facing evidence snapshot for a
  cited claim.
- Each record type should define a deterministic human-readable context
  projection from its structured fields. That rendered context may be reused for
  LLM input, citation display, and UI inspection, but the structured fields
  remain the canonical source of truth.
- The default rendering contract is a class-owned `context` property backed by a
  deterministic template. Subclasses may override the default when a record
  needs custom presentation logic.
- Template rendering should stay presentation-only. Calculation, validation,
  filtering, and business logic belong in deterministic Python code before the
  template step.
- Raw provider payloads remain available to the runtime for processing and audit,
  but they are not the default LLM input surface.
- Persisted citation rows must carry enough provenance and payload detail for
  the UI to inspect source, dataset, timestamp, methodology, and the cited fact
  without requiring the full intermediate record to be stored.
- `fundamental_record.is_audited` is the simple boolean gate for confident
  fundamental claims.

## LLM Boundary

The LLM may interpret deterministic records and compose cited language from them.
It must not decide what raw data to fetch or rely on raw provider dumps as its
primary evidence source.

Allowed LLM behavior:

- Summarize the data bundle
- Cite the provided citation ids
- Mark unsupported claims unavailable
- Explain pattern findings or metric guardrails from the supplied records

Disallowed LLM behavior:

- Choosing collection strategy
- Calling providers directly
- Inventing citations
- Treating raw payloads as the user-facing evidence contract

## Application Impact

This boundary applies across the product:

- Workflow orchestration builds the data bundle before analysis.
- Chatflow uses the same record boundary for grounded responses.
- UI inspection surfaces should render citations and, where needed, derived
  record facts, not raw provider dumps. In Phase 02, citation inspection is the
  required durable surface; full intermediate-record inspection is optional
  future debug scope.
- Shared template files may be used to keep record rendering consistent across
  LLM context building and UI display, provided the rendered output stays
  deterministic for the same record fields.
- Tests should assert that deterministic record generation and citations remain
  stable and inspectable without exposing hidden reasoning or provider
  internals.
